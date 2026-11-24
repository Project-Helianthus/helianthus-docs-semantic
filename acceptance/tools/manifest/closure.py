"""Typed closure over a donor package at one commit.

Declarations come from the package directory. Uses are unqualified
identifiers in the moved files. A test left in the donor is mixed when it
uses both a moved symbol and a symbol that stays, and each of its assertions
is classified the same way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from gitstore import list_dir, read_blobs


_KEYWORDS = {
    "break", "case", "chan", "const", "continue", "default", "defer", "else",
    "fallthrough", "for", "func", "go", "goto", "if", "import", "interface",
    "map", "package", "range", "return", "select", "struct", "switch", "type",
    "var",
}
_BUILTINS = {
    "any", "append", "bool", "byte", "cap", "close", "comparable", "complex",
    "complex64", "complex128", "copy", "delete", "error", "false", "float32",
    "float64", "imag", "int", "int8", "int16", "int32", "int64", "iota", "len",
    "make", "new", "nil", "panic", "print", "println", "real", "recover",
    "rune", "string", "true", "uint", "uint8", "uint16", "uint32", "uint64",
    "uintptr",
}
_FUNC_NAME = re.compile(r"\bfunc\s*(?:\([^)]*\))?\s*([A-Za-z_][A-Za-z0-9_]*)")
_TYPE_NAME = re.compile(r"\btype\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_VAR_NAME = re.compile(r"\b(?:var|const)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_IMPORT_QUOTED = re.compile(r'import\s+(?:([A-Za-z_][A-Za-z0-9_]*)\s+)?"([^"]+)"')
_IMPORT_GROUP = re.compile(r"import\s*\((.*?)\)", re.S)
_IMPORT_SPEC = re.compile(r'(?:([A-Za-z_][A-Za-z0-9_]*)|\.|_)\s+"([^"]+)"|"([^"]+)"')
_ASSERTION_NAME = re.compile(r"assertion=([A-Za-z0-9_.-]+)")
_FAILURE = {"Error", "Errorf", "Fatal", "Fatalf", "Fail", "FailNow"}


@dataclass
class Assertion:
    name: str
    function: str
    file: str
    uses: set[str] = field(default_factory=set)
    helpers: list[str] = field(default_factory=list)


@dataclass
class TestFunction:
    name: str
    file: str
    uses: set[str] = field(default_factory=set)
    assertions: list[Assertion] = field(default_factory=list)


@dataclass
class PackageFacts:
    moved_decls: dict[str, str]
    outside_decls: dict[str, str]
    symbol_uses: dict[str, list[str]]
    outside_uses: list[str]
    tests: list[TestFunction]


def blank_source(source: str) -> str:
    """Replace comments, strings and runes with spaces. Newlines stay."""
    chars = list(source)
    index = 0
    length = len(chars)
    while index < length:
        character = chars[index]
        nxt = chars[index + 1] if index + 1 < length else ""
        if character == "/" and nxt == "/":
            while index < length and chars[index] != "\n":
                chars[index] = " "
                index += 1
            continue
        if character == "/" and nxt == "*":
            chars[index] = " "
            chars[index + 1] = " "
            index += 2
            while index < length - 1 and not (chars[index] == "*" and chars[index + 1] == "/"):
                if chars[index] != "\n":
                    chars[index] = " "
                index += 1
            if index < length:
                chars[index] = " "
            if index + 1 < length:
                chars[index + 1] = " "
            index += 2
            continue
        if character == "`":
            chars[index] = " "
            index += 1
            while index < length and chars[index] != "`":
                if chars[index] != "\n":
                    chars[index] = " "
                index += 1
            if index < length:
                chars[index] = " "
                index += 1
            continue
        if character == '"' or character == "'":
            quote = character
            chars[index] = " "
            index += 1
            while index < length and chars[index] != quote:
                if chars[index] == "\\" and index + 1 < length:
                    chars[index] = " "
                    index += 1
                    if chars[index] != "\n":
                        chars[index] = " "
                    index += 1
                    continue
                if chars[index] != "\n":
                    chars[index] = " "
                index += 1
            if index < length:
                chars[index] = " "
                index += 1
            continue
        index += 1
    return "".join(chars)


def _import_names(blanked: str) -> set[str]:
    names: set[str] = set()
    for match in _IMPORT_QUOTED.finditer(blanked):
        alias, path = match.group(1), match.group(2)
        names.add(alias or path.rsplit("/", 1)[-1])
    for group in _IMPORT_GROUP.finditer(blanked):
        for spec in _IMPORT_SPEC.finditer(group.group(1)):
            alias, path, bare = spec.group(1), spec.group(2), spec.group(3)
            if alias == "_" or spec.group(0).startswith("."):
                continue
            if alias:
                names.add(alias)
            elif path:
                names.add(path.rsplit("/", 1)[-1])
            elif bare:
                names.add(bare.rsplit("/", 1)[-1])
    return names


def _group_names(blanked: str, keyword: str) -> set[str]:
    names: set[str] = set()
    token = keyword + " ("
    start = 0
    while True:
        at = blanked.find(token, start)
        if at < 0:
            break
        depth = 0
        index = at + len(keyword)
        end = index
        while end < len(blanked):
            if blanked[end] == "(":
                depth += 1
            elif blanked[end] == ")":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1
        block = blanked[at:end]
        for line in block.splitlines()[1:]:
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", line)
            if not match:
                continue
            name = match.group(1)
            if name not in _KEYWORDS and name not in _BUILTINS:
                names.add(name)
        start = end
    return names


def declarations(source: str) -> set[str]:
    blanked = blank_source(source)
    names: set[str] = set()
    for expression in (_FUNC_NAME, _TYPE_NAME, _VAR_NAME):
        names.update(expression.findall(blanked))
    names.update(_group_names(blanked, "const"))
    names.update(_group_names(blanked, "var"))
    names.update(_group_names(blanked, "type"))
    return {name for name in names if name not in _KEYWORDS and name not in _BUILTINS}


def package_name(source: str) -> str:
    match = re.search(r"(?m)^\s*package\s+([A-Za-z_][A-Za-z0-9_]*)", blank_source(source))
    if not match:
        raise ValueError("missing package clause")
    return match.group(1)


def _tokenize(blanked: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*|:=|[{}()]|\.", blanked):
        tokens.append((match.group(0), match.group(0)))
    return tokens


def _uses_in_text(blanked: str, interesting: set[str], imports: set[str]) -> set[str]:
    used: set[str] = set()
    previous = ""
    for token, _value in _tokenize(blanked):
        if token == ".":
            previous = "."
            continue
        if previous != "." and token in interesting and token not in imports and token not in _BUILTINS:
            used.add(token)
        previous = token
    return used


def _function_spans(blanked: str) -> list[tuple[str, int, int]]:
    """Return (name, body_start, body_end) for functions that have a body."""
    spans: list[tuple[str, int, int]] = []
    for match in _FUNC_NAME.finditer(blanked):
        name = match.group(1)
        index = match.end()
        paren = bracket = brace = 0
        started = False
        body_at = None
        while index < len(blanked):
            character = blanked[index]
            if character == "(":
                paren += 1
            elif character == ")":
                paren -= 1
            elif character == "[":
                bracket += 1
            elif character == "]":
                bracket -= 1
            elif character == "{":
                if paren == 0 and bracket == 0 and brace == 0:
                    body_at = index
                    started = True
                    brace = 1
                    index += 1
                    break
                brace += 1
            elif character == "}" and brace:
                brace -= 1
            index += 1
        if not started or body_at is None:
            continue
        depth = 1
        index = body_at + 1
        while index < len(blanked) and depth:
            if blanked[index] == "{":
                depth += 1
            elif blanked[index] == "}":
                depth -= 1
            index += 1
        spans.append((name, body_at, index))
    return spans


def _skip_balanced(text: str, index: int, open_char: str, close_char: str) -> int:
    depth = 0
    while index < len(text):
        if text[index] == open_char:
            depth += 1
        elif text[index] == close_char:
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return index


def _if_spans(body: str, base: int) -> list[tuple[int, int]]:
    """Top-level if statements inside a function body, as absolute offsets."""
    spans: list[tuple[int, int]] = []
    depth = 0
    index = 0
    while index < len(body):
        character = body[index]
        if character == "{":
            depth += 1
            index += 1
            continue
        if character == "}":
            depth -= 1
            index += 1
            continue
        if depth == 1 and body.startswith("if", index) and _boundary(body, index, 2):
            start = index
            cursor = index + 2
            paren = bracket = brace = 0
            while cursor < len(body):
                char = body[cursor]
                if char == "(":
                    paren += 1
                elif char == ")":
                    paren -= 1
                elif char == "[":
                    bracket += 1
                elif char == "]":
                    bracket -= 1
                elif char == "{" and paren == 0 and bracket == 0 and brace == 0:
                    cursor = _skip_balanced(body, cursor, "{", "}")
                    break
                elif char == "{":
                    brace += 1
                elif char == "}":
                    brace -= 1
                cursor += 1
            while cursor < len(body) and body[cursor].isspace():
                cursor += 1
            if body.startswith("else", cursor) and _boundary(body, cursor, 4):
                cursor += 4
                while cursor < len(body) and body[cursor].isspace():
                    cursor += 1
                if body.startswith("if", cursor) and _boundary(body, cursor, 2):
                    # else-if stays inside this assertion; consume one more if.
                    nested, _end = _consume_if(body, cursor)
                    cursor = nested
                elif cursor < len(body) and body[cursor] == "{":
                    cursor = _skip_balanced(body, cursor, "{", "}")
            spans.append((base + start, base + cursor))
            index = cursor
            continue
        index += 1
    return spans


def _boundary(text: str, index: int, size: int) -> bool:
    before = text[index - 1] if index else " "
    after_at = index + size
    after = text[after_at] if after_at < len(text) else " "
    return not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_")


def _consume_if(body: str, index: int) -> tuple[int, int]:
    cursor = index + 2
    paren = bracket = brace = 0
    while cursor < len(body):
        char = body[cursor]
        if char == "(":
            paren += 1
        elif char == ")":
            paren -= 1
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket -= 1
        elif char == "{" and paren == 0 and bracket == 0 and brace == 0:
            return _skip_balanced(body, cursor, "{", "}"), 0
        cursor += 1
    return cursor, 0


def _failure_call(segment: str) -> bool:
    return re.search(r"\.\s*(?:Error|Errorf|Fatal|Fatalf|Fail|FailNow)\b", segment) is not None


def _assertion_name(raw_segment: str, function: str, ordinal: int) -> str:
    match = _ASSERTION_NAME.search(raw_segment)
    if match:
        return match.group(1)
    literal = re.search(r'"([^"]+)"', raw_segment)
    if literal:
        text = literal.group(1).split("=", 1)[0].strip()
        if text:
            return re.sub(r"\s+", "-", text)[:80]
    return f"{function}#{ordinal}"


def _helpers(blanked_segment: str, moved: set[str]) -> list[str]:
    found: list[str] = []
    previous = ""
    for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*|\(", blanked_segment):
        token = match.group(0)
        if token == "(" and previous in moved and previous not in found:
            found.append(previous)
        previous = token
    return sorted(found)


def analyze(repo: Path, revision: str, moved_paths: list[str]) -> PackageFacts:
    if not moved_paths:
        return PackageFacts({}, {}, {}, [], [])
    blobs = read_blobs(repo, revision, moved_paths)
    missing = [path for path in moved_paths if path not in blobs]
    if missing:
        raise ValueError("missing moved paths: " + ", ".join(missing))
    texts = {path: blobs[path].decode(errors="replace") for path in moved_paths}
    packages = {package_name(texts[path]) for path in moved_paths}
    if len(packages) != 1:
        raise ValueError("moved files span more than one package")
    package = next(iter(packages))
    directory = str(Path(moved_paths[0]).parent)
    if any(str(Path(path).parent) != directory for path in moved_paths):
        raise ValueError("moved files span more than one directory")
    siblings = [
        path for path in list_dir(repo, revision, directory)
        if path.endswith(".go")
    ]
    sibling_blobs = read_blobs(repo, revision, siblings)
    moved_set = set(moved_paths)
    moved_decls: dict[str, str] = {}
    outside_decls: dict[str, str] = {}
    decoded: dict[str, str] = {}
    for path, blob in sibling_blobs.items():
        text = blob.decode(errors="replace")
        try:
            if package_name(text) != package:
                continue
        except ValueError:
            continue
        decoded[path] = text
        for name in declarations(text):
            target = moved_decls if path in moved_set else outside_decls
            target.setdefault(name, path)
    # A name defined in the moved set is moved even if another file repeats it.
    for name in list(outside_decls):
        if name in moved_decls:
            del outside_decls[name]
    for path in moved_paths:
        if path in decoded:
            continue
        decoded[path] = texts[path]
        for name in declarations(texts[path]):
            moved_decls[name] = path
            outside_decls.pop(name, None)
    outside_names = set(outside_decls)
    moved_names = set(moved_decls)
    package_names = moved_names | outside_names
    symbol_uses: dict[str, list[str]] = {name: [] for name in moved_names}
    outside_uses: set[str] = set()
    for path in moved_paths:
        blanked = blank_source(decoded[path])
        imports = _import_names(blanked)
        for name, body_start, body_end in _function_spans(blanked):
            if name not in moved_names:
                continue
            segment = blanked[body_start:body_end]
            used = _uses_in_text(segment, package_names, imports)
            used.discard(name)
            symbol_uses[name] = sorted(item for item in used if item in moved_names)
            outside_uses.update(item for item in used if item in outside_names)
        # Signature and composite-literal uses sit outside the brace body.
        file_uses = _uses_in_text(blanked, outside_names, imports)
        outside_uses.update(file_uses)
    tests = [] if outside_uses else _tests(decoded, moved_set, moved_names, outside_names)
    return PackageFacts(
        moved_decls=moved_decls,
        outside_decls=outside_decls,
        symbol_uses=symbol_uses,
        outside_uses=sorted(outside_uses),
        tests=tests,
    )


def _tests(
    decoded: dict[str, str],
    moved_set: set[str],
    moved_names: set[str],
    outside_names: set[str],
) -> list[TestFunction]:
    package_names = moved_names | outside_names
    tests: list[TestFunction] = []
    for path, text in sorted(decoded.items()):
        if path in moved_set or not path.endswith("_test.go"):
            continue
        raw_blank_pairs = text
        blanked = blank_source(text)
        imports = _import_names(blanked)
        for name, body_start, body_end in _function_spans(blanked):
            if not name.startswith("Test"):
                continue
            body = blanked[body_start:body_end]
            raw_body = raw_blank_pairs[body_start:body_end]
            uses = _uses_in_text(body, package_names, imports)
            assertions: list[Assertion] = []
            ordinal = 0
            for start, end in _if_spans(body, 0):
                segment = body[start:end]
                raw_segment = raw_body[start:end]
                if not _failure_call(segment):
                    continue
                ordinal += 1
                assertion_uses = _uses_in_text(segment, package_names, imports)
                assertions.append(Assertion(
                    name=_assertion_name(raw_segment, name, ordinal),
                    function=name,
                    file=path,
                    uses=assertion_uses,
                    helpers=_helpers(segment, moved_names),
                ))
            tests.append(TestFunction(name=name, file=path, uses=uses, assertions=assertions))
    return tests


def classify_test(test: TestFunction, moved_names: set[str], outside_names: set[str]) -> str:
    moved = bool(test.uses & moved_names)
    staying = bool(test.uses & outside_names)
    if moved and not staying:
        return "only-moved"
    if moved and staying:
        return "mixed"
    return "unrelated"
