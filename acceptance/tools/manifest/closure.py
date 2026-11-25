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

from gitstore import list_dir, list_files_recursive, read_blobs


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
    # Names declared by the package of this test when that package is not one
    # the input names (an external test package); they stay in the donor.
    own: set[str] = field(default_factory=set)


@dataclass
class PackageFacts:
    moved_decls: dict[str, str]
    outside_decls: dict[str, str]
    symbol_uses: dict[str, list[str]]
    outside_uses: list[str]
    tests: list[TestFunction]


def blank_source(source: str, literal: str = " ", strings: bool = True) -> str:
    """Replace comments, strings and runes with spaces. Newlines stay.

    ``literal`` marks the first character of each string or rune, so a
    caller that needs to see where a literal stood can keep one token there.
    With ``strings`` false only comments are blanked and every literal stays.
    """
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
            if strings:
                chars[index] = literal
            index += 1
            while index < length and chars[index] != "`":
                if strings and chars[index] != "\n":
                    chars[index] = " "
                index += 1
            if index < length:
                if strings:
                    chars[index] = " "
                index += 1
            continue
        if character == '"' or character == "'":
            quote = character
            if strings:
                chars[index] = literal
            index += 1
            while index < length and chars[index] != quote:
                if chars[index] == "\\" and index + 1 < length:
                    if strings:
                        chars[index] = " "
                    index += 1
                    if strings and chars[index] != "\n":
                        chars[index] = " "
                    index += 1
                    continue
                if strings and chars[index] != "\n":
                    chars[index] = " "
                index += 1
            if index < length:
                if strings:
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
    parsed: dict[str, "GoFile"] | None = None,
    struct_types: set[str] | None = None,
    aliases_of: "Callable[[str], dict[str, str]] | None" = None,
    qualified_names: set[str] | None = None,
    method_keys: set[str] | None = None,
    foreign: dict[str, set[str]] | None = None,
    own: set[str] | None = None,
    foreign_methods: dict[str, set[str]] | None = None,
    dots_of: "Callable[[str], list[str]] | None" = None,
    dot_names: dict[str, tuple[set[str], set[str]]] | None = None,
) -> list[TestFunction]:
    """Test functions with the donor symbols each one and each assertion uses.

    With ``parsed`` a use is a reference that resolves to a declaration of the
    package: a local name that is spelled like one is not a use. With
    ``aliases_of`` (the import names of a test file) a reference
    ``alias.Name`` that is spelled ``directory.Name`` in ``qualified_names``
    is a use of that name of another donor package.
    """
    package_names = moved_names | outside_names
    tests: list[TestFunction] = []
    for path, text in sorted(decoded.items()):
        if path in moved_set or not path.endswith("_test.go"):
            continue
        raw_blank_pairs = text
        blanked = blank_source(text)
        imports = _import_names(blanked)
        source = parsed.get(path) if parsed else None
        aliases = aliases_of(text) if aliases_of else None
        dot_dirs = dots_of(text) if dots_of else []

        def reach(declaration: Declaration, window: tuple[int, int] | None) -> set[str]:
            """Donor names the declaration uses in the window and in the statements that give its locals their values."""
            found = reach_in(declaration, window)
            if window is not None:
                for origin in source.origins(declaration, window):
                    found |= reach_in(declaration, origin)
            return found

        def reach_in(declaration: Declaration, window: tuple[int, int] | None) -> set[str]:
            """Donor names the declaration uses, qualified ones spelled ``directory.Name``."""
            reached: set[tuple[str, str]] = set()
            found = source.uses(
                declaration, package_names, struct_types or set(), aliases, reached,
                window=window, foreign=foreign,
            )
            found |= _qualified(reached, qualified_names)
            if method_keys or foreign_methods:
                reached_methods: set[tuple[str, str]] = set()
                found |= source.method_uses(
                    declaration, method_keys or set(), window=window, aliases=aliases,
                    qualified=reached_methods, dots=dot_dirs, foreign_methods=foreign_methods,
                )
                found |= _qualified(reached_methods, qualified_names)
            # A name a dot import makes available is a use of that directory.
            for other in dot_dirs:
                names, structs = (dot_names or {}).get(other, (set(), set()))
                used = source.uses(declaration, names, structs, foreign=foreign, window=window)
                found |= {f"{other}.{name}" for name in used if not qualified_names or f"{other}.{name}" in qualified_names}
            return found

        resolved = (
            {item.name: item for item in source.declarations if item.kind == "func"}
            if source else {}
        )
        for name, body_start, body_end in _function_spans(blanked):
            if not name.startswith("Test"):
                continue
            body = blanked[body_start:body_end]
            raw_body = raw_blank_pairs[body_start:body_end]
            declaration = resolved.get(name)
            if source is not None and declaration is not None:
                uses = reach(declaration, None)
            else:
                uses = _uses_in_text(body, package_names, imports)
            assertions: list[Assertion] = []
            ordinal = 0
            for start, end in _if_spans(body, 0):
                segment = body[start:end]
                raw_segment = raw_body[start:end]
                if not _failure_call(segment):
                    continue
                ordinal += 1
                helpers = _helpers(segment, moved_names)
                if source is not None and declaration is not None:
                    assertion_uses = reach(declaration, (body_start + start, body_start + end))
                    helpers = [item for item in helpers if item in assertion_uses]
                else:
                    assertion_uses = _uses_in_text(segment, package_names, imports)
                assertions.append(Assertion(
                    name=_assertion_name(raw_segment, name, ordinal),
                    function=name,
                    file=path,
                    uses=assertion_uses,
                    helpers=helpers,
                ))
            tests.append(TestFunction(
                name=name, file=path, uses=uses, assertions=assertions, own=set(own or ()),
            ))
    return tests


def _qualified(reached: set[tuple[str, str]], names: set[str] | None) -> set[str]:
    if not names:
        return set()
    return {f"{directory}.{name}" for directory, name in reached if f"{directory}.{name}" in names}


def classify_test(test: TestFunction, moved_names: set[str], outside_names: set[str]) -> str:
    moved = bool(test.uses & moved_names)
    staying = bool(test.uses & outside_names)
    if moved and not staying:
        return "only-moved"
    if moved and staying:
        return "mixed"
    return "unrelated"


# Symbol-level closure.
#
# A symbol is a top-level declaration: a function, type, var or const name, or
# a method written ``Receiver.Method``. Only those names count. A field name,
# a parameter or receiver name, a local binding and a package name are not
# declarations and never make a use.

_SYMBOL_TOKEN = re.compile(r"[^\W\d]\w*|\d[\w.]*|:=|\.\.\.|[{}()\[\],;.:]|\S")
_OPENERS = {"(", "[", "{"}
_CLOSERS = {")", "]", "}"}
_LINE_KEYWORDS = {"break", "continue", "fallthrough", "return"}
_CLOSE_SIGNATURE = {",", ")", "]", "}", ";", "=", ":", ":="}


def _is_name(text: str) -> bool:
    return (text[0].isalpha() or text[0] == "_") and text not in _KEYWORDS


@dataclass
class Declaration:
    name: str
    kind: str
    first: int
    last: int
    receiver: str = ""
    struct: bool = False
    base: str = ""
    body: int = -1
    skip: set[int] = field(default_factory=set)
    masks: list[tuple[str, int, int]] = field(default_factory=list)
    typed: list[tuple[str, str | None]] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.receiver}.{self.name}" if self.kind == "method" else self.name


class GoFile:
    """Tokens and top-level declarations of one Go source file."""

    def __init__(self, text: str) -> None:
        self.blanked = blank_source(text, "0")
        self.tokens = [
            (match.group(0), match.start(), match.end())
            for match in _SYMBOL_TOKEN.finditer(self.blanked)
        ]
        self.close: dict[int, int] = {}
        self.open: dict[int, int] = {}
        stack: list[int] = []
        for index, (word, _start, _end) in enumerate(self.tokens):
            if word in _OPENERS:
                stack.append(index)
            elif word in _CLOSERS and stack:
                opener = stack.pop()
                self.close[opener] = index
                self.open[index] = opener
        self.declarations = self._scan()

    def _word(self, index: int) -> str:
        return self.tokens[index][0] if 0 <= index < len(self.tokens) else ""

    def _end_of(self, opener: int) -> int:
        return self.close.get(opener, opener)

    def _break_between(self, before: int, after: int) -> bool:
        return "\n" in self.blanked[self.tokens[before][2]:self.tokens[after][1]]

    def _ends_line(self, index: int) -> bool:
        word = self._word(index)
        if word in _CLOSERS or word[:1].isdigit():
            return True
        if word[:1].isalpha() or word[:1] == "_":
            return word not in _KEYWORDS or word in _LINE_KEYWORDS
        return False

    def _statement_end(self, index: int, limit: int) -> int:
        depth = 0
        cursor = index
        while cursor < limit:
            word = self.tokens[cursor][0]
            if word in _OPENERS:
                depth += 1
            elif word in _CLOSERS:
                if depth == 0:
                    return cursor
                depth -= 1
            elif word == ";" and depth == 0:
                return cursor + 1
            cursor += 1
            if depth == 0 and cursor < limit and self._break_between(cursor - 1, cursor) and self._ends_line(cursor - 1):
                return cursor
        return limit

    def _entries(self, opener: int) -> list[tuple[int, int]]:
        """Token ranges of the comma separated entries of a bracketed list."""
        end = self._end_of(opener)
        entries: list[tuple[int, int]] = []
        start = opener + 1
        depth = 0
        for cursor in range(opener + 1, end):
            word = self.tokens[cursor][0]
            if word in _OPENERS:
                depth += 1
            elif word in _CLOSERS:
                depth -= 1
            elif word == "," and depth == 0:
                entries.append((start, cursor))
                start = cursor + 1
        entries.append((start, end))
        return [entry for entry in entries if entry[0] < entry[1]]

    def _named(self, opener: int, force: bool = False) -> list[int]:
        """Token indexes of the names bound by a parameter or type-parameter list."""
        entries = self._entries(opener)

        def is_named(first: int, last: int) -> bool:
            if last - first < 2 or not _is_name(self.tokens[first][0]):
                return False
            second = self.tokens[first + 1][0]
            if second == ".":
                return False
            if second == "[":
                return self._end_of(first + 1) + 1 < last
            return True

        if not force and not any(is_named(first, last) for first, last in entries):
            return []
        return [first for first, _last in entries if _is_name(self.tokens[first][0])]

    def _type_name(self, first: int, last: int) -> str | None:
        """Name of the package type spelled by the tokens, or None for any other type."""
        cursor = first
        if cursor < last and self._word(cursor) == "*":
            cursor += 1
        if cursor >= last or not _is_name(self._word(cursor)):
            return None
        if (
            cursor + 2 < last
            and self._word(cursor + 1) == "."
            and _is_name(self._word(cursor + 2))
            and (cursor + 3 >= last or self._word(cursor + 3) == "[")
        ):
            # A type of another package, spelled ``alias.Name``.
            return f"{self._word(cursor)}.{self._word(cursor + 2)}"
        if cursor + 1 < last and self._word(cursor + 1) != "[":
            return None
        return self._word(cursor)

    def _typed(self, opener: int) -> list[tuple[str, str | None]]:
        """Names bound by a parameter list with the type each one is declared as."""
        named = set(self._named(opener))
        found: list[tuple[str, str | None]] = []
        pending: list[int] = []
        for first, last in self._entries(opener):
            if first not in named:
                continue
            if last - first < 2:
                pending.append(first)
                continue
            kind = self._type_name(first + 1, last)
            for at in [*pending, first]:
                found.append((self.tokens[at][0], kind))
            pending = []
        for at in pending:
            found.append((self.tokens[at][0], None))
        return found

    def _typed_signature(self, cursor: int) -> list[tuple[str, str | None]]:
        """Typed names of the parameter and result lists of a signature."""
        found: list[tuple[str, str | None]] = []
        for _ in range(2):
            if cursor < len(self.tokens) and self.tokens[cursor][0] == "(":
                found += self._typed(cursor)
                cursor = self._end_of(cursor) + 1
        return found

    def _receiver_type(self, first: int, last: int) -> str:
        found = ""
        cursor = first
        while cursor < last:
            word = self.tokens[cursor][0]
            if word == "[":
                cursor = self._end_of(cursor) + 1
                continue
            if _is_name(word):
                found = word
            cursor += 1
        return found

    def _signature(self, cursor: int) -> tuple[list[int], int, int | None]:
        """Names bound by a signature that starts at its parameter list.

        Returns the name tokens, the index after the signature and the index
        of the body brace, or None for a signature that has no body.
        """
        count = len(self.tokens)
        names: list[int] = []
        for _ in range(2):
            if cursor < count and self.tokens[cursor][0] == "(":
                names += self._named(cursor)
                cursor = self._end_of(cursor) + 1
        while cursor < count:
            word = self.tokens[cursor][0]
            if word == "{" and self._word(cursor - 1) not in ("struct", "interface"):
                return names, cursor, cursor
            if word in _CLOSE_SIGNATURE:
                break
            if word in _OPENERS:
                cursor = self._end_of(cursor) + 1
                continue
            if self._break_between(cursor - 1, cursor) and self._ends_line(cursor - 1):
                break
            cursor += 1
        return names, cursor, None

    def _scan(self) -> list[Declaration]:
        found: list[Declaration] = []
        count = len(self.tokens)
        index = 0
        while index < count:
            word = self.tokens[index][0]
            if word == "func":
                index = self._function(index, found)
            elif word in ("type", "var", "const"):
                index = self._general(index, found)
            else:
                index = max(self._statement_end(index, count), index + 1)
        return found

    def _function(self, index: int, found: list[Declaration]) -> int:
        count = len(self.tokens)
        cursor = index + 1
        names: list[int] = []
        type_names: list[int] = []
        receiver = ""
        method = self._word(cursor) == "("
        typed: list[tuple[str, str | None]] = []
        if method:
            closing = self._end_of(cursor)
            names += self._named(cursor)
            typed += self._typed(cursor)
            receiver = self._receiver_type(cursor + 1, closing)
            # The names in the brackets of a generic receiver type are type
            # parameters bound by the receiver, not package symbols.
            for at in range(cursor + 1, closing):
                if self.tokens[at][0] == "[":
                    type_names += [
                        first for first, _last in self._entries(at)
                        if _is_name(self.tokens[first][0])
                    ]
                    break
            cursor = closing + 1
        if cursor >= count or not _is_name(self.tokens[cursor][0]):
            return max(cursor, index + 1)
        name_at = cursor
        cursor += 1
        if self._word(cursor) == "[":
            type_names = self._named(cursor, force=True)
            cursor = self._end_of(cursor) + 1
        typed += self._typed_signature(cursor)
        parameter_names, cursor, body = self._signature(cursor)
        names += parameter_names
        end = self._end_of(body) + 1 if body is not None else cursor
        name = self.tokens[name_at][0]
        if name not in ("_", "init"):
            found.append(Declaration(
                name=name,
                kind="method" if method else "func",
                first=index,
                last=end,
                receiver=receiver,
                body=-1 if body is None else body,
                typed=typed,
                skip={name_at, *names, *type_names},
                # A type parameter is in scope in the whole declaration. A
                # receiver, parameter or result name only binds in the body, so
                # a type of the same spelling in the signature is still a use.
                masks=[(self.tokens[at][0], index, end) for at in type_names]
                + (
                    [(self.tokens[at][0], body, end) for at in names]
                    if body is not None else []
                ),
            ))
        return max(end, index + 1)

    def _general(self, index: int, found: list[Declaration]) -> int:
        count = len(self.tokens)
        kind = self.tokens[index][0]
        cursor = index + 1
        if cursor >= count:
            return count
        if self.tokens[cursor][0] == "(":
            end = self._end_of(cursor)
            at = cursor + 1
            # A constant specification without a type and an initializer
            # repeats the previous one, so it uses what that one uses.
            inherit: dict[str, object] | None = (
                {"start": None, "skip": set()} if kind == "const" else None
            )
            while at < end:
                if self.tokens[at][0] == ";":
                    at += 1
                    continue
                stop = self._statement_end(at, end)
                self._spec(kind, at, stop, found, at, inherit)
                at = max(stop, at + 1)
            return end + 1
        stop = self._statement_end(cursor, count)
        self._spec(kind, cursor, stop, found, index)
        return max(stop, cursor + 1)

    def _type_parameters(self, opener: int) -> bool:
        """True when the bracket after a type name lists type parameters.

        ``type A [N]int`` and ``type A [N + 1]int`` give an array length that
        uses the constant ``N``. A list starts with a name that is followed by
        a comma, a constraint or a type.
        """
        first = self._word(opener + 1)
        if not first or not _is_name(first):
            return False
        second = self._word(opener + 2)
        if second in (",", "~", "interface", "func", "map", "chan", "struct"):
            return True
        if second == "[":
            return self._word(self._end_of(opener + 2) + 1) not in ("]", "")
        return bool(second) and _is_name(second)

    def _spec(
        self,
        kind: str,
        start: int,
        stop: int,
        found: list[Declaration],
        first: int,
        inherit: dict[str, object] | None = None,
    ) -> None:
        if start >= stop or not _is_name(self.tokens[start][0]):
            return
        if kind == "type":
            cursor = start + 1
            masks: list[tuple[str, int, int]] = []
            if cursor < stop and self._word(cursor) == "[" and self._type_parameters(cursor):
                masks = [
                    (self.tokens[at][0], first, stop)
                    for at in self._named(cursor, force=True)
                ]
                cursor = self._end_of(cursor) + 1
            if cursor < stop and self._word(cursor) == "=":
                cursor += 1
            # A type spelled as another package type name (an alias or a
            # defined type) has that type's underlying kind.
            base = ""
            if (
                cursor < stop
                and _is_name(self._word(cursor))
                and (cursor + 1 >= stop or self._word(cursor + 1) != ".")
            ):
                base = self._word(cursor)
            elif (
                cursor + 2 < stop
                and _is_name(self._word(cursor))
                and self._word(cursor + 1) == "."
                and _is_name(self._word(cursor + 2))
                and (cursor + 3 >= stop or self._word(cursor + 3) == "[")
            ):
                # A type of another package, spelled ``alias.Name``.
                base = f"{self._word(cursor)}.{self._word(cursor + 2)}"
            found.append(Declaration(
                name=self.tokens[start][0],
                kind="type",
                first=first,
                last=stop,
                struct=cursor < stop and self._word(cursor) == "struct",
                base=base,
                skip={start},
                masks=masks,
            ))
            return
        names: list[int] = []
        cursor = start
        while cursor < stop and _is_name(self.tokens[cursor][0]):
            names.append(cursor)
            if cursor + 1 < stop and self._word(cursor + 1) == ",":
                cursor += 2
            else:
                break
        skipped = set(names)
        if inherit is not None:
            if names[-1] + 1 >= stop and inherit["start"] is not None:
                first = inherit["start"]
                skipped = set(inherit["skip"]) | skipped
            else:
                inherit["start"] = first
            inherit["skip"] = set(skipped)
        # Names that have a value each are initialized independently, so the
        # name of one counts only its own value and not that of a sibling.
        own_values: list[tuple[int, int]] = []
        if len(names) > 1:
            at = names[-1] + 1
            while at < stop and self._word(at) != "=":
                at = self._end_of(at) + 1 if self._word(at) in _OPENERS else at + 1
            if at < stop:
                own_values = self._split(at + 1, stop)
        for position, at in enumerate(names):
            if self.tokens[at][0] != "_":
                apart = set(skipped)
                if len(own_values) == len(names):
                    for other, (begin, end) in enumerate(own_values):
                        if other != position:
                            apart.update(range(begin, end))
                found.append(Declaration(
                    name=self.tokens[at][0],
                    kind=kind,
                    first=first,
                    last=stop,
                    skip=apart,
                ))

    def _fields(self, opener: int, interface: bool, skip: set[int], add) -> None:
        end = self._end_of(opener)
        at = opener + 1
        while at < end:
            if self._word(at) == ";":
                at += 1
                continue
            stop = self._statement_end(at, end)
            self._field(at, stop, interface, skip, add)
            at = max(stop, at + 1)

    def _field(self, first: int, stop: int, interface: bool, skip: set[int], add) -> None:
        if not _is_name(self.tokens[first][0]):
            return
        second = self._word(first + 1) if first + 1 < stop else ""
        if interface:
            if second == "(":
                skip.add(first)
                after = self._end_of(first + 1) + 1
                bound = self._named(first + 1)
                if self._word(after) == "(":
                    bound += self._named(after)
                skip.update(bound)
            return
        if second == ",":
            cursor = first
            while cursor < stop and _is_name(self.tokens[cursor][0]):
                skip.add(cursor)
                if cursor + 1 < stop and self._word(cursor + 1) == ",":
                    cursor += 2
                else:
                    break
            return
        if not second or second in (".", "0"):
            return
        if second == "[":
            closing = self._end_of(first + 1)
            if closing + 1 >= stop or self._word(closing + 1) == "0":
                return
        skip.add(first)

    def _past_pointers(self, index: int) -> int:
        """Index of the first ``*`` of the pointer stars that end just before ``index``."""
        while index > 0 and self._word(index - 1) == "*":
            index -= 1
        return index

    def _literal(
        self,
        index: int,
        low: int,
        stack: list[tuple[int, str, bool]],
        struct_types: set[str],
        qualified_struct: "Callable[[str, str], bool] | None" = None,
    ) -> tuple[str, bool]:
        """Kind of the composite literal opened at ``index``.

        ``struct`` means the keys of its elements are field names.
        ``collection`` means its elements may omit their type and
        ``True`` says that element type is a struct.
        """
        before = self._word(index - 1) if index > low else ""
        if before in ("{", ",", ":"):
            parent = stack[-1] if stack else None
            if parent is not None and parent[1] == "collection":
                return ("struct", False) if parent[2] else ("other", False)
            return "other", False
        if before == "}":
            opener = self.open.get(index - 1, -1)
            if opener > low and self._word(opener - 1) == "struct":
                if self._word(self._past_pointers(opener - 1) - 1) == "]":
                    return "collection", True
                return "struct", False
            return "other", False
        if before == "]":
            opener = self.open.get(index - 1, -1)
            named = self._word(opener - 1) if opener > low else ""
            if named and _is_name(named):
                start = opener - 1
                if opener - 3 >= low and self._word(opener - 2) == "." and _is_name(self._word(opener - 3)):
                    # A generic type of another package, spelled ``alias.Name[...]``.
                    start = opener - 3
                    is_struct = (
                        qualified_struct(self._word(start), named) if qualified_struct else True
                    )
                else:
                    is_struct = named in struct_types
                if self._word(self._past_pointers(start) - 1) == "]":
                    return "collection", is_struct
                return ("struct" if is_struct else "other"), False
            return "other", False
        if before and _is_name(before):
            start = index - 1
            qualified = False
            if start - 2 >= low and self._word(start - 1) == "." and _is_name(self._word(start - 2)):
                start -= 2
                qualified = True
            if qualified:
                # A type of another package is a struct unless that package is a
                # donor directory that declares it as some other kind of type.
                is_struct = qualified_struct(self._word(start), before) if qualified_struct else True
            else:
                is_struct = before in struct_types
            if start > low and self._word(self._past_pointers(start) - 1) == "]":
                return "collection", is_struct
            return ("struct" if is_struct else "other"), False
        return "other", False

    def _scope_end(self, stack: list[tuple[int, str, bool]], limit: int, at: int | None = None) -> int:
        """End of the scope a binding made at token ``at`` is visible in.

        A binding in the body of a ``case`` or ``default`` clause ends with
        that clause, not with the select or switch that holds it.
        """
        if not stack:
            return limit
        opener = stack[-1][0]
        if at is not None:
            depth = 0
            clause = False
            for cursor in range(opener + 1, at):
                word = self.tokens[cursor][0]
                if word in _OPENERS:
                    depth += 1
                elif word in _CLOSERS:
                    depth -= 1
                elif depth == 0 and word in ("case", "default"):
                    clause = True
            if clause:
                return self._clause_end(at, limit, stack)
        return self._end_of(opener) + 1

    def _header(self, index: int, limit: int) -> tuple[int, int]:
        """Body brace and first top-level semicolon of a header from ``index`` on.

        A brace that opens a composite literal of a slice, array, map or struct
        type is a part of the header, so a range over ``[]int{1, 2}`` still
        finds the loop body after it. Both results are -1 when absent.
        """
        depth = 0
        semicolon = -1
        literal = False
        cursor = index + 1
        while cursor < limit:
            word = self.tokens[cursor][0]
            if depth == 0:
                if word == "{":
                    if self._word(cursor - 1) in ("struct", "interface"):
                        cursor = self._end_of(cursor) + 1
                        continue
                    if literal:
                        literal = False
                        cursor = self._end_of(cursor) + 1
                        continue
                    return cursor, semicolon
                if word in ("map", "struct"):
                    literal = True
                elif word == "[":
                    before = self._word(cursor - 1)
                    if not (before and _is_name(before)) and before not in ("]", ")"):
                        literal = True
                elif word == ";" and semicolon < 0:
                    semicolon = cursor
            if word in _OPENERS:
                depth += 1
            elif word in _CLOSERS:
                depth -= 1
            cursor += 1
        return -1, semicolon

    def _header_scope(self, index: int, limit: int, chain: bool = False) -> tuple[int, int]:
        """Token range a binding of an if, for or switch header is visible in.

        With ``chain`` the range of an ``if`` runs through every ``else``
        branch that follows its block.
        """
        body, semicolon = self._header(index, limit)
        if body < 0:
            return limit, limit
        start = semicolon + 1 if semicolon >= 0 else body
        stop = self._end_of(body) + 1
        while chain and stop < limit and self._word(stop) == "else":
            nxt = stop + 1
            if self._word(nxt) == "if":
                nxt, _semicolon = self._header(nxt, limit)
                if nxt < 0:
                    break
            if self._word(nxt) != "{":
                break
            stop = self._end_of(nxt) + 1
        return start, stop

    def _clause_end(self, cursor: int, limit: int, stack: list[tuple[int, str, bool]]) -> int:
        """End of a ``case`` clause of a select or switch that starts at ``cursor``."""
        depth = 0
        while cursor < limit:
            word = self.tokens[cursor][0]
            if word in _OPENERS:
                depth += 1
            elif word in _CLOSERS:
                if depth == 0:
                    return cursor
                depth -= 1
            elif depth == 0 and word in ("case", "default"):
                return cursor
            cursor += 1
        return self._scope_end(stack, limit)

    def _short_scope(
        self, index: int, chain: list[int], low: int, high: int, stack: list[tuple[int, str, bool]]
    ) -> tuple[int, int]:
        """Token range a name bound by the ``:=`` at ``index`` is visible in."""
        lead = self._word(chain[-1] - 1) if chain[-1] - 1 >= low else ""
        if lead in ("if", "for", "switch"):
            return self._header_scope(index, high, chain=lead == "if")
        if lead == "case":
            cursor = index + 1
            while cursor < high and self._word(cursor) != ":":
                cursor += 1
            return cursor, self._clause_end(cursor + 1, high, stack)
        return self._statement_end(chain[-1], high), self._scope_end(stack, high, index)

    def _local_declaration(
        self, index: int, limit: int, stack: list[tuple[int, str, bool]], skip: set[int], add,
        types: "list[tuple[str, int, int, bool]] | None" = None,
        struct_types: set[str] | None = None,
        qualified_struct: "Callable[[str, str], bool] | None" = None,
    ) -> None:
        kind = self._word(index)
        end = self._scope_end(stack, limit, index)
        names: list[tuple[list[int], int]] = []
        if self._word(index + 1) == "(":
            closing = self._end_of(index + 1)
            at = index + 2
            while at < closing:
                if self._word(at) == ";":
                    at += 1
                    continue
                stop = self._statement_end(at, closing)
                names.append((self._chain(at, stop, kind == "type"), stop))
                at = max(stop, at + 1)
        else:
            stop = self._statement_end(index + 1, limit)
            names.append((self._chain(index + 1, stop, kind == "type"), stop))
        for chain, stop in names:
            for at in chain:
                skip.add(at)
                add(self.tokens[at][0], stop, end)
                if kind == "type" and types is not None:
                    types.append((
                        self.tokens[at][0], stop, end,
                        self._struct_spec(at + 1, stop, struct_types or set(), qualified_struct),
                    ))

    def _struct_spec(
        self,
        start: int,
        stop: int,
        struct_types: set[str],
        qualified_struct: "Callable[[str, str], bool] | None" = None,
    ) -> bool:
        """True when the type specification tokens from ``start`` spell a struct."""
        cursor = start
        if cursor < stop and self._word(cursor) == "=":
            cursor += 1
        if cursor >= stop:
            return False
        word = self._word(cursor)
        if word == "struct":
            return True
        if (
            _is_name(word)
            and cursor + 2 < stop
            and self._word(cursor + 1) == "."
            and _is_name(self._word(cursor + 2))
        ):
            # A type of another package, spelled ``alias.Name``.
            return qualified_struct(word, self._word(cursor + 2)) if qualified_struct else True
        return _is_name(word) and word in struct_types and (cursor + 1 >= stop or self._word(cursor + 1) != ".")

    def _chain(self, start: int, stop: int, single: bool) -> list[int]:
        chain: list[int] = []
        cursor = start
        while cursor < stop and _is_name(self.tokens[cursor][0]):
            chain.append(cursor)
            if not single and cursor + 1 < stop and self._word(cursor + 1) == ",":
                cursor += 2
            else:
                break
        return chain

    def uses(
        self,
        declaration: Declaration,
        candidates: set[str],
        struct_types: set[str],
        aliases: dict[str, str] | None = None,
        qualified: set[tuple[str, str]] | None = None,
        window: tuple[int, int] | None = None,
        foreign: dict[str, set[str]] | None = None,
    ) -> set[str]:
        """Candidate names the declaration uses.

        ``aliases`` maps an import name to the donor directory it imports. A
        use of ``alias.Name`` that is not shadowed by a local binding is added
        to ``qualified`` as ``(directory, Name)``; the alias is never a use.
        ``window`` limits the result to tokens at those source offsets.

        A name after a dot, a field or method name in a type body, the key of
        a struct literal element, and a name bound by a parameter, a receiver,
        a type parameter or a local declaration inside its scope are not uses.
        """
        low, high = declaration.first, declaration.last
        skip = set(declaration.skip)
        masks: dict[str, list[tuple[int, int]]] = {}

        def add(name: str, start: int, stop: int) -> None:
            masks.setdefault(name, []).append((start, stop))

        for name, start, stop in declaration.masks:
            add(name, start, stop)
        blocks = {declaration.body} if declaration.body >= 0 else set()
        stack: list[tuple[int, str, bool]] = []
        local_types: list[tuple[str, int, int, bool]] = []

        def qualified_struct(alias: str, name: str) -> bool:
            if aliases and foreign and alias in aliases and aliases[alias] in foreign:
                return name in foreign[aliases[alias]]
            return True

        seen: list[tuple[str, int]] = []
        quals: list[tuple[str, str, int]] = []
        index = low
        while index < high:
            word = self.tokens[index][0]
            if word == "func" and self._word(index + 1) == "(" and not (index == low and declaration.kind in ("func", "method")):
                names, after, body = self._signature(index + 1)
                stop = self._end_of(body) + 1 if body is not None else after
                skip.update(names)
                if body is not None:
                    for at in names:
                        add(self.tokens[at][0], body, stop)
                    blocks.add(body)
            elif word in ("if", "for", "switch", "select", "else"):
                body, _semicolon = self._header(index, high)
                if body >= 0:
                    blocks.add(body)
            elif word == "{":
                before = self._word(index - 1) if index > low else ""
                element = False
                if index in blocks:
                    kind = "block"
                elif before in ("struct", "interface"):
                    kind = "body"
                    self._fields(index, before == "interface", skip, add)
                else:
                    known = struct_types
                    active = [item for item in local_types if item[1] <= index < item[2]]
                    if active:
                        known = set(struct_types)
                        for name, _first, _last, is_struct in active:
                            if is_struct:
                                known.add(name)
                            else:
                                known.discard(name)
                    kind, element = self._literal(index, low, stack, known, qualified_struct)
                stack.append((index, kind, element))
            elif word == "}":
                if stack:
                    stack.pop()
            elif word == ":=":
                chain: list[int] = []
                at = index - 1
                while at >= low and _is_name(self.tokens[at][0]):
                    chain.append(at)
                    if at - 1 >= low and self._word(at - 1) == ",":
                        at -= 2
                    else:
                        break
                if chain:
                    skip.update(chain)
                    start, stop = self._short_scope(index, chain, low, high, stack)
                    for at in chain:
                        add(self.tokens[at][0], start, stop)
            elif word in ("var", "const", "type") and stack and (
                self._word(index + 1) == "(" or _is_name(self._word(index + 1))
            ):
                self._local_declaration(index, high, stack, skip, add, local_types, struct_types, qualified_struct)
            elif _is_name(word):
                before = self._word(index - 1) if index > low else ""
                if (
                    aliases
                    and word in aliases
                    and before != "."
                    and self._word(index + 1) == "."
                    and _is_name(self._word(index + 2))
                ):
                    quals.append((word, self.tokens[index + 2][0], index))
                if (
                    word in candidates
                    and before != "."
                    and not (
                        stack
                        and stack[-1][1] == "struct"
                        and before in ("{", ",")
                        and self._word(index + 1) == ":"
                    )
                ):
                    seen.append((word, index))
            index += 1
        def visible(word: str, at: int) -> bool:
            if at in skip or any(start <= at < stop for start, stop in masks.get(word, ())):
                return False
            return window is None or window[0] <= self.tokens[at][1] < window[1]

        if qualified is not None:
            qualified.update((aliases[alias], name) for alias, name, at in quals if visible(alias, at))
        return {word for word, at in seen if visible(word, at)}

    def _plain_assignment(self, index: int) -> bool:
        """True when the ``=`` token at ``index`` is an assignment, not part of ``==``, ``<=`` and the like."""
        start = self.tokens[index][1]
        before = self.blanked[start - 1] if start > 0 else ""
        after = self.blanked[start + 1] if start + 1 < len(self.blanked) else ""
        return before not in "=!<>:+-*/%&|^" and after != "="

    def origins(self, declaration: Declaration, window: tuple[int, int]) -> list[tuple[int, int]]:
        """Source ranges of the statements that give the locals read in ``window`` their values.

        A local that the window reads is followed to the nearest earlier
        ``:=`` or ``=`` that assigns it, and the locals that statement reads
        are followed the same way. An assertion that checks ``got`` after
        ``got := Moved()`` therefore uses what that statement uses.
        """
        low, high = declaration.first, declaration.last
        # Each definition lists the names it assigns with the binding each name
        # is: the ``:=`` that declared it, found by scope, or None for a name
        # declared outside the function body (a parameter, a package name).
        definitions: list[tuple[dict[str, int | None], int, int]] = []
        scopes: dict[str, list[tuple[int, int, int]]] = {}
        stack: list[tuple[int, str, bool]] = []

        def binding(name: str, at: int) -> int | None:
            covering = [item for item in scopes.get(name, ()) if item[0] <= at < item[1]]
            return max(covering, key=lambda item: item[0])[2] if covering else None

        for index in range(low, high):
            word = self.tokens[index][0]
            if word == "{":
                stack.append((index, "", False))
                continue
            if word == "}":
                if stack:
                    stack.pop()
                continue
            if word != ":=" and not (word == "=" and self._plain_assignment(index)):
                continue
            chain: list[int] = []
            at = index - 1
            while at >= low and _is_name(self.tokens[at][0]):
                chain.append(at)
                if at - 1 >= low and self._word(at - 1) == ",":
                    at -= 2
                else:
                    break
            stop = self._statement_end(index + 1, high)
            if not chain or stop <= index + 1:
                continue
            bound: dict[str, int | None] = {}
            if word == ":=":
                start, end = self._short_scope(index, chain, low, high, stack)
                for at in chain:
                    scopes.setdefault(self.tokens[at][0], []).append((start, end, index))
                    bound[self.tokens[at][0]] = index
            else:
                for at in chain:
                    bound[self.tokens[at][0]] = binding(self.tokens[at][0], index)
            definitions.append((bound, index, stop))

        def read(first: int, last: int) -> list[tuple[str, int]]:
            return [
                (self.tokens[at][0], at)
                for at in range(first, last)
                if _is_name(self.tokens[at][0]) and self._word(at - 1) != "."
            ]

        pending = [
            (name, window[0], at)
            for name, at in read(
                next((at for at in range(low, high) if self.tokens[at][1] >= window[0]), high),
                next((at for at in range(low, high) if self.tokens[at][1] >= window[1]), high),
            )
        ]
        windows: list[tuple[int, int]] = []
        done: set[int] = set()
        while pending:
            name, limit, at = pending.pop()
            # The binding the read refers to, not any earlier variable of the
            # same spelling that a nested scope declared.
            wanted = binding(name, at)
            earlier = [
                item for item in definitions
                if name in item[0] and item[0][name] == wanted and self.tokens[item[1]][1] < limit
            ]
            if not earlier:
                continue
            _bound, equals, stop = max(earlier, key=lambda item: item[1])
            if equals in done:
                continue
            done.add(equals)
            windows.append((self.tokens[equals + 1][1], self.tokens[stop - 1][2]))
            pending += [(item, self.tokens[equals][1], where) for item, where in read(equals + 1, stop)]
        return windows

    def _initializer_type(self, start: int, stop: int) -> str | None:
        """Type name of an initializer that is a struct literal ``T{...}`` or ``&T{...}``."""
        cursor = start
        if cursor < stop and self._word(cursor) == "&":
            cursor += 1
        if cursor + 1 < stop and _is_name(self._word(cursor)) and self._word(cursor + 1) == "{":
            return self._word(cursor)
        return None

    def method_uses(
        self,
        declaration: Declaration,
        keys: set[str],
        window: tuple[int, int] | None = None,
        aliases: dict[str, str] | None = None,
        qualified: set[tuple[str, str]] | None = None,
        dots: list[str] | None = None,
        foreign_methods: dict[str, set[str]] | None = None,
    ) -> set[str]:
        """Method keys of ``keys`` that the declaration refers to.

        A reference is ``name.Method`` where ``name`` is a parameter, receiver
        or local variable that is declared with a package type ``T`` and
        ``T.Method`` is in ``keys``, or the method expression ``T.Method``. The
        binding in scope at the reference gives the type; a name bound to a
        value whose type is not spelled resolves to no type. A field is never a
        method key, so a field selector is not a reference. ``window`` limits
        the result to references at those source offsets.

        A reference to a method of a type of another donor package, through a
        type spelled ``alias.T`` (or ``T`` of a dot import) or the method
        expression ``alias.T.Method``, is added to ``qualified`` as
        ``(directory, T.Method)`` when ``foreign_methods`` lists it for that
        directory.
        """
        low, high = declaration.first, declaration.last
        foreign_methods = foreign_methods or {}
        # Each binding is visible from where it takes effect to the end of its
        # scope, and the innermost one that covers a reference gives its type.
        bindings: dict[str, list[tuple[int, int, str | None]]] = {}

        def bind(name: str, start: int, stop: int, kind: str | None) -> None:
            bindings.setdefault(name, []).append((start, stop, kind))

        def kind_at(name: str, at: int) -> str | None:
            covering = [item for item in bindings.get(name, ()) if item[0] <= at < item[1]]
            return max(covering, key=lambda item: item[0])[2] if covering else None

        for name, kind in declaration.typed:
            bind(name, low, high, kind)
        stack: list[tuple[int, str, bool]] = []
        index = low
        while index < high:
            word = self.tokens[index][0]
            if word == "func" and self._word(index + 1) == "(" and not (
                index == low and declaration.kind in ("func", "method")
            ):
                _names, _after, body = self._signature(index + 1)
                if body is not None:
                    for name, kind in self._typed_signature(index + 1):
                        bind(name, body, self._end_of(body) + 1, kind)
            elif word == "{":
                stack.append((index, "", False))
            elif word == "}":
                if stack:
                    stack.pop()
            elif word == ":=":
                chain: list[int] = []
                at = index - 1
                while at >= low and _is_name(self.tokens[at][0]):
                    chain.append(at)
                    if at - 1 >= low and self._word(at - 1) == ",":
                        at -= 2
                    else:
                        break
                if chain:
                    ordered = chain[::-1]
                    stop_at = self._statement_end(index + 1, high)
                    values = [
                        (first, last) for first, last in self._split(index + 1, stop_at)
                    ]
                    kinds: list[str | None] = []
                    for position, at in enumerate(ordered):
                        kind = None
                        if len(chain) == 1:
                            kind = self._initializer_type(index + 1, stop_at)
                        if (
                            kind is None
                            and len(values) == len(ordered)
                            and values[position][1] - values[position][0] == 1
                            and _is_name(self._word(values[position][0]))
                        ):
                            # ``x, ok := x, true`` binds a new ``x`` of the type of the old one.
                            kind = kind_at(self._word(values[position][0]), index)
                        kinds.append(kind)
                    start, stop = self._short_scope(index, chain, low, high, stack)
                    plain = self._word(chain[-1] - 1) not in ("if", "for", "switch", "case")
                    scope_end = self._scope_end(stack, high, index)
                    for at, kind in zip(ordered, kinds):
                        name = self.tokens[at][0]
                        # A name that is already bound in this very scope is
                        # assigned by a redeclaring ``:=`` and keeps its type.
                        if len(chain) > 1 and plain and any(
                            item[1] == scope_end and item[0] <= index
                            for item in bindings.get(name, ())
                        ):
                            continue
                        bind(name, start, stop, kind)
            elif word == "var" and index > low:
                specs: list[tuple[int, int]] = []
                if self._word(index + 1) == "(":
                    closing = self._end_of(index + 1)
                    at = index + 2
                    while at < closing:
                        if self._word(at) == ";":
                            at += 1
                            continue
                        stop = self._statement_end(at, closing)
                        specs.append((at, stop))
                        at = max(stop, at + 1)
                else:
                    specs.append((index + 1, self._statement_end(index + 1, high)))
                for at, stop in specs:
                    chain = self._chain(at, stop, False)
                    if not chain:
                        continue
                    after = chain[-1] + 1
                    if after < stop and self._word(after) == "=":
                        kind = self._initializer_type(after + 1, stop) if len(chain) == 1 else None
                    else:
                        kind = self._type_name(after, stop)
                    scope_end = self._scope_end(stack, high, index)
                    for name_at in chain:
                        bind(self.tokens[name_at][0], stop, scope_end, kind)
            index += 1
        found: set[str] = set()

        def record(kind: str, method: str) -> None:
            key = f"{kind}.{method}"
            if key in keys:
                found.add(key)
            elif qualified is not None:
                if "." in kind:
                    alias, _dot, type_name = kind.partition(".")
                    directory = (aliases or {}).get(alias)
                    if directory and f"{type_name}.{method}" in foreign_methods.get(directory, ()):
                        qualified.add((directory, f"{type_name}.{method}"))
                else:
                    for directory in dots or ():
                        if key in foreign_methods.get(directory, ()):
                            qualified.add((directory, key))

        for index in range(low, high):
            word = self.tokens[index][0]
            if word == "." and index > low and self._word(index - 1) == ")" and _is_name(self._word(index + 1)):
                # The method expression ``(*T).Method`` or ``(*alias.T).Method``.
                opener = self.open.get(index - 1, -1)
                before = self._word(opener - 1) if opener > low else ""
                if opener < low or (before and (_is_name(before) or before in _CLOSERS)):
                    continue
                inner = opener + 1
                if self._word(inner) == "*":
                    inner += 1
                if not _is_name(self._word(inner)):
                    continue
                head = inner
                tail = inner + 1
                spelled = self._word(inner)
                if (
                    self._word(inner + 1) == "."
                    and _is_name(self._word(inner + 2))
                    and self._word(inner) in (aliases or {})
                ):
                    spelled = f"{self._word(inner)}.{self._word(inner + 2)}"
                    tail = inner + 3
                if tail < index - 1 and self._word(tail) == "[" and self._end_of(tail) + 1 == index - 1:
                    # An explicit instantiation, ``(*T[int]).Method``.
                    tail = index - 1
                if tail != index - 1:
                    continue
                if window is not None and not window[0] <= self.tokens[head][1] < window[1]:
                    continue
                if any(item[0] <= head < item[1] for item in bindings.get(self._word(head), ())):
                    continue
                record(spelled, self._word(index + 1))
                continue
            dot = index + 1
            if (
                _is_name(word)
                and self._word(dot) == "["
                and not any(item[0] <= index < item[1] for item in bindings.get(word, ()))
            ):
                # An instantiated type before a selector, ``T[int].Method``.
                dot = self._end_of(dot) + 1
            if (
                not _is_name(word)
                or (index > low and self._word(index - 1) == ".")
                or self._word(dot) != "."
                or not self._word(dot + 1)
                or not _is_name(self._word(dot + 1))
            ):
                continue
            if window is not None and not window[0] <= self.tokens[index][1] < window[1]:
                continue
            covering = [item for item in bindings.get(word, ()) if item[0] <= index < item[1]]
            kind = max(covering, key=lambda item: item[0])[2] if covering else word
            if kind is None:
                continue
            if (
                not covering
                and aliases
                and word in aliases
                and self._word(index + 3) == "."
                and _is_name(self._word(index + 4))
            ):
                # The method expression ``alias.T.Method``.
                kind = f"{word}.{self._word(index + 2)}"
                method = self._word(index + 4)
            else:
                method = self._word(dot + 1)
            record(kind, method)
        return found

    def _split(self, start: int, stop: int) -> list[tuple[int, int]]:
        """Token ranges of the comma separated parts of tokens ``start`` to ``stop``."""
        parts: list[tuple[int, int]] = []
        depth = 0
        first = start
        for cursor in range(start, stop):
            word = self.tokens[cursor][0]
            if word in _OPENERS:
                depth += 1
            elif word in _CLOSERS:
                depth -= 1
            elif word == "," and depth == 0:
                parts.append((first, cursor))
                first = cursor + 1
        parts.append((first, stop))
        return [part for part in parts if part[0] < part[1]]


# An import path is an interpreted ("...") or a raw (`...`) string literal.
_IMPORT_SPEC_NAME = re.compile(r'(?:([A-Za-z_][A-Za-z0-9_]*|\.)\s*)?(?:"([^"\n]+)"|`([^`\n]+)`)')
_IMPORT_SINGLE = re.compile(r'\bimport\s+(?:([A-Za-z_][A-Za-z0-9_]*|\.)\s*)?(?:"([^"\n]+)"|`([^`\n]+)`)')
_TOP_LEVEL = re.compile(r"^(?:func|type|var|const)\b")


def _module_path(repo: Path, revision: str) -> str:
    blob = read_blobs(repo, revision, ["go.mod"]).get("go.mod")
    if blob is None:
        return ""
    match = re.search(r"(?m)^\s*module\s+(\S+)", blob.decode(errors="replace"))
    return match.group(1).strip('"') if match else ""


def _import_bindings(
    text: str,
    resolve: "Callable[[str], str | None]",
    clause_of: "Callable[[str], str]",
) -> tuple[dict[str, str], list[str]]:
    """Import names of one file that stand for a donor directory.

    ``resolve`` maps an import path to the donor directory it names, or None.
    An import without a name takes the package clause of that directory. Only
    the import declarations of the code count, never a comment. The second
    result lists the donor directories a dot import makes available by their
    bare names.
    """
    aliases: dict[str, str] = {}
    dots: list[str] = []
    head: list[str] = []
    for line in blank_source(text, strings=False).splitlines():
        if _TOP_LEVEL.match(line) and not line.startswith("import"):
            break
        head.append(line)
    # A grouped import may stand on one line, with its specs separated by
    # semicolons, so the specs are read from the declarations and not by line.
    declared = "\n".join(head)
    specs: list[tuple[str, str]] = []
    for group in _IMPORT_GROUP.finditer(declared):
        specs += [
            (found.group(1) or "", found.group(2) or found.group(3))
            for found in _IMPORT_SPEC_NAME.finditer(group.group(1))
        ]
    specs += [
        (found.group(1) or "", found.group(2) or found.group(3))
        for found in _IMPORT_SINGLE.finditer(_IMPORT_GROUP.sub(" ", declared))
    ]
    for local, path in specs:
        if local == "_":
            continue
        directory = resolve(path)
        if directory is None:
            continue
        if local == ".":
            if directory not in dots:
                dots.append(directory)
            continue
        name = local or clause_of(directory)
        if name:
            aliases[name] = directory
    return aliases, dots


def _import_aliases(
    text: str,
    resolve: "Callable[[str], str | None]",
    clause_of: "Callable[[str], str]",
) -> dict[str, str]:
    return _import_bindings(text, resolve, clause_of)[0]


def _directory_resolver(repo: Path, revision: str, module: str) -> "Callable[[str], str | None]":
    """Map an import path to the donor directory that holds its Go files.

    The directory is found under the module path of the donor, or by the
    longest trailing part of the path that is a donor directory when the donor
    has no go.mod. Any donor directory counts, not only those the input names.
    """
    cache: dict[str, str | None] = {}

    def has_go(directory: str) -> bool:
        return any(name.endswith(".go") for name in list_dir(repo, revision, directory))

    def resolve(path: str) -> str | None:
        if path in cache:
            return cache[path]
        found: str | None = None
        if module:
            if path == module and has_go("."):
                found = "."
            elif path.startswith(module + "/") and has_go(path[len(module) + 1:]):
                found = path[len(module) + 1:]
        else:
            parts = path.split("/")
            for index in range(len(parts)):
                candidate = "/".join(parts[index:])
                if has_go(candidate):
                    found = candidate
                    break
        cache[path] = found
        return found

    return resolve


def _struct_closure(declarations: list[Declaration], extra: set[str] | None = None) -> set[str]:
    """Names of types that are structs, aliases and defined types of structs included.

    ``extra`` names types that are known to be structs because they are
    spelled as a struct type of another package.
    """
    struct_types = {item.name for item in declarations if item.kind == "type" and item.struct}
    struct_types |= extra or set()
    changed = True
    while changed:
        changed = False
        for item in declarations:
            if item.kind == "type" and item.base in struct_types and item.name not in struct_types:
                struct_types.add(item.name)
                changed = True
    return struct_types


@dataclass
class SymbolFacts:
    moved: list[dict[str, object]] = field(default_factory=list)
    stays: list[dict[str, str]] = field(default_factory=list)
    outside_uses: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tests: dict[str, list[TestFunction]] = field(default_factory=dict)
    moved_names: dict[str, set[str]] = field(default_factory=dict)
    outside_names: dict[str, set[str]] = field(default_factory=dict)


def analyze_symbols(
    repo: Path,
    revision: str,
    moves: list[dict[str, str]],
    stays: list[dict[str, str]],
) -> SymbolFacts:
    """Closure of a symbol-level move over each donor package it names.

    ``moves`` and ``stays`` hold ``package`` (the donor directory), ``path``
    and ``symbol``. A moved symbol may use only moved symbols and symbols the
    input declares as staying. The methods of a moved type are siblings and
    follow the same rule. A name qualified by an import of any other donor
    directory is a use of that directory, whether or not the input names it.
    """
    facts = SymbolFacts()
    entries = [("move", item) for item in moves] + [("stay", item) for item in stays]
    packages = sorted({item["package"].rstrip("/") for _kind, item in entries})
    parsed: dict[str, dict[str, GoFile]] = {}
    texts: dict[str, dict[str, str]] = {}
    clause_cache: dict[str, str] = {}

    def load(directory: str, clause: str) -> None:
        parsed[directory] = {}
        texts[directory] = {}
        siblings = [path for path in list_dir(repo, revision, directory) if path.endswith(".go")]
        for path, blob in read_blobs(repo, revision, siblings).items():
            text = blob.decode(errors="replace")
            try:
                if package_name(text) != clause:
                    continue
            except ValueError:
                continue
            texts[directory][path] = text
            parsed[directory][path] = GoFile(text)

    for directory in packages:
        listed = sorted({
            item["path"] for _kind, item in entries
            if item["package"].rstrip("/") == directory
        })
        blobs = read_blobs(repo, revision, listed)
        for path in listed:
            if path not in blobs:
                facts.errors.append(f"absent: {path}")
            elif str(Path(path).parent) != directory:
                facts.errors.append(f"package-mismatch: {path}")
        if any(path not in blobs for path in listed):
            continue
        try:
            clauses = {package_name(blobs[path].decode(errors="replace")) for path in listed}
        except ValueError as error:
            facts.errors.append(str(error))
            continue
        if len(clauses) != 1:
            facts.errors.append(f"package-mismatch: {directory}")
            continue
        clause_cache[directory] = next(iter(clauses))
        load(directory, clause_cache[directory])
    if facts.errors:
        return facts
    module = _module_path(repo, revision)
    resolve = _directory_resolver(repo, revision, module)

    def clause_of(directory: str) -> str:
        if directory not in clause_cache:
            clause_cache[directory] = ""
            names = [path for path in list_dir(repo, revision, directory) if path.endswith(".go")]
            blobs = read_blobs(repo, revision, names)
            for path in sorted(blobs, key=lambda item: (item.endswith("_test.go"), item)):
                try:
                    clause_cache[directory] = package_name(blobs[path].decode(errors="replace"))
                except ValueError:
                    continue
                break
        return clause_cache[directory]

    def aliases_of(text: str) -> dict[str, str]:
        return _import_aliases(text, resolve, clause_of)

    def dots_of(text: str) -> list[str]:
        return _import_bindings(text, resolve, clause_of)[1]

    # Any donor directory a moved file imports is read, so that a name it uses
    # there is found even when the input names no symbol of that directory.
    loaded = list(packages)
    for kind, item in entries:
        if kind != "move":
            continue
        source_text = texts[item["package"].rstrip("/")][item["path"]]
        for directory in sorted({*aliases_of(source_text).values(), *dots_of(source_text)}):
            if directory not in parsed and clause_of(directory):
                load(directory, clause_of(directory))
                loaded.append(directory)
    info: dict[str, dict[str, object]] = {}
    qualified_bases: list[tuple[str, str, str | None, str]] = []
    for directory in loaded:
        files = parsed[directory]
        declared: set[str] = set()
        methods: list[Declaration] = []
        lookup: dict[tuple[str, str], Declaration] = {}
        every: list[Declaration] = []
        for path, source in files.items():
            for declaration in source.declarations:
                lookup.setdefault((path, declaration.key), declaration)
                every.append(declaration)
                if declaration.kind == "method":
                    methods.append(declaration)
                else:
                    declared.add(declaration.name)
        moved_keys: dict[str, str] = {}
        stay_keys: dict[str, str] = {}
        for kind, item in entries:
            if item["package"].rstrip("/") != directory:
                continue
            target = moved_keys if kind == "move" else stay_keys
            if (item["path"], item["symbol"]) not in lookup:
                facts.errors.append(f"absent-symbol: {item['path']} {item['symbol']}")
            elif item["symbol"] in target:
                facts.errors.append(f"duplicate-symbol: {item['path']} {item['symbol']}")
            else:
                target[item["symbol"]] = item["path"]
        for key in moved_keys:
            if key in stay_keys:
                facts.errors.append(f"moved-and-stays: {moved_keys[key]} {key}")
        for path, source in files.items():
            file_aliases = aliases_of(texts[directory][path])
            for declaration in source.declarations:
                if declaration.kind != "type" or "." not in declaration.base:
                    continue
                alias, _dot, type_name = declaration.base.partition(".")
                target = file_aliases.get(alias)
                if target is not None and target not in parsed and clause_of(target):
                    load(target, clause_of(target))
                    loaded.append(target)
                qualified_bases.append((directory, declaration.name, target, type_name))
        info[directory] = {
            "declared": declared,
            "every": every,
            "struct_types": _struct_closure(every),
            "methods": methods,
            "lookup": lookup,
            "moved_keys": moved_keys,
            "stay_keys": stay_keys,
            "moved_names": {key for key in moved_keys if "." not in key},
            "stay_names": {key for key in stay_keys if "." not in key},
            "method_keys": {item.key for item in methods},
        }
    if facts.errors:
        return facts
    # An alias or defined type spelled ``alias.Name`` is a struct when that
    # donor type is one (or when its package is not a donor directory, like
    # any other qualified type); its literals then key fields, not values.
    resolved: dict[str, set[str]] = {}
    changed = True
    while changed:
        changed = False
        for directory, name, target, type_name in qualified_bases:
            if name in resolved.get(directory, ()):
                continue
            if target is None or (target in info and type_name in info[target]["struct_types"]):
                resolved.setdefault(directory, set()).add(name)
                info[directory]["struct_types"].update(
                    _struct_closure(info[directory]["every"], resolved[directory])
                )
                changed = True
    outside: set[str] = set()
    foreign = {other: info[other]["struct_types"] for other in info}
    for directory in packages:
        files = parsed[directory]
        declared = info[directory]["declared"]
        struct_types = info[directory]["struct_types"]
        methods = info[directory]["methods"]
        lookup = info[directory]["lookup"]
        moved_keys = info[directory]["moved_keys"]
        stay_keys = info[directory]["stay_keys"]
        moved_names = info[directory]["moved_names"]
        stay_names = info[directory]["stay_names"]
        for key in sorted(moved_keys):
            declaration = lookup[(moved_keys[key], key)]
            aliases = aliases_of(texts[directory][moved_keys[key]])
            reached: set[tuple[str, str]] = set()
            used = files[moved_keys[key]].uses(
                declaration, declared, struct_types, aliases, reached, foreign=foreign
            )
            if declaration.kind != "method":
                # A method and a package function of one name are different
                # symbols; only a function, type or value may name itself.
                used.discard(declaration.name)
            outside.update(used - moved_names - stay_names)
            carried = set(used & moved_names)
            for other, name in sorted(reached):
                if other == directory or other not in info or name not in info[other]["declared"]:
                    continue
                if name in info[other]["moved_names"]:
                    carried.add(f"{other}.{name}")
                elif name not in info[other]["stay_names"]:
                    outside.add(f"{other}.{name}")
            dots = [other for other in dots_of(texts[directory][moved_keys[key]]) if other in info]
            # A name a dot import makes available is a use of that directory.
            for other in dots:
                for name in files[moved_keys[key]].uses(
                    declaration, info[other]["declared"], info[other]["struct_types"], foreign=foreign
                ):
                    if name in info[other]["moved_names"]:
                        carried.add(f"{other}.{name}")
                    elif name not in info[other]["stay_names"]:
                        outside.add(f"{other}.{name}")
            reached_methods: set[tuple[str, str]] = set()
            called = files[moved_keys[key]].method_uses(
                declaration, {item.key for item in methods},
                aliases=aliases, qualified=reached_methods, dots=dots,
                foreign_methods={other: info[other]["method_keys"] for other in info},
            )
            called.discard(declaration.key)
            for method_key in called:
                if method_key in moved_keys:
                    carried.add(method_key)
                elif method_key not in stay_keys:
                    outside.add(method_key)
            # A method of a type of another donor directory is accounted for
            # there, whether or not its receiver type is declared staying.
            for other, method_key in sorted(reached_methods):
                if other == directory:
                    continue
                if method_key in info[other]["moved_keys"]:
                    carried.add(f"{other}.{method_key}")
                elif method_key not in info[other]["stay_keys"]:
                    outside.add(f"{other}.{method_key}")
            facts.moved.append({
                "package": directory,
                "file": moved_keys[key],
                "name": key,
                "uses": sorted(carried),
            })
            if declaration.kind == "type":
                for method in methods:
                    if method.receiver == declaration.name and method.key not in moved_keys and method.key not in stay_keys:
                        outside.add(method.key)
        for key in sorted(stay_keys):
            facts.stays.append({"package": directory, "file": stay_keys[key], "name": key})
        facts.moved_names[directory] = set(moved_names)
        facts.outside_names[directory] = declared - moved_names
    facts.outside_uses = sorted(outside)
    facts.moved.sort(key=lambda item: (item["package"], item["file"], item["name"]))
    facts.stays.sort(key=lambda item: (item["package"], item["file"], item["name"]))
    if facts.errors or facts.outside_uses:
        return facts
    # A donor test names a symbol of a donor package of the move as
    # ``alias.Name``; that spelling is the name it uses there.
    all_moved = {f"{other}.{name}" for other in packages for name in info[other]["moved_names"]}
    all_outside = {
        f"{other}.{name}"
        for other in packages
        for name in info[other]["declared"] - info[other]["moved_names"]
    }
    # A method of a donor package is named ``directory.Type.Method`` where a
    # test of another package calls it through a value of ``alias.Type``.
    for other in packages:
        for key in info[other]["method_keys"]:
            (all_moved if key in info[other]["moved_keys"] else all_outside).add(f"{other}.{key}")
    foreign_methods = {other: info[other]["method_keys"] for other in info}
    dot_names = {other: (info[other]["declared"], info[other]["struct_types"]) for other in info}
    for directory in packages:
        facts.moved_names[directory] |= all_moved
        facts.outside_names[directory] |= all_outside
        # A call of a method is a use of that method: a moved one is moved, any
        # other one of the package stays.
        methods_here = info[directory]["method_keys"]
        facts.moved_names[directory] |= {key for key in methods_here if key in info[directory]["moved_keys"]}
        facts.outside_names[directory] |= {key for key in methods_here if key not in info[directory]["moved_keys"]}
    moved_pairs = {(item["file"], item["name"]) for item in facts.moved}
    for directory in packages:
        found = _tests(
            texts[directory], set(), facts.moved_names[directory], facts.outside_names[directory],
            parsed[directory], info[directory]["struct_types"], aliases_of,
            all_moved | all_outside,
            method_keys=info[directory]["method_keys"], foreign=foreign,
            foreign_methods=foreign_methods, dots_of=dots_of, dot_names=dot_names,
        )
        facts.tests[directory] = [
            test for test in found if (test.file, test.name) not in moved_pairs
        ]
    # A test file outside the package of its directory (an external test
    # package) and a test file of a donor directory that the input does not
    # name still exercise moved symbols when it imports a package of the move.
    covered = {path for directory in packages for path in texts[directory]}
    # An import path is an interpreted or a raw string literal.
    quotes = ('"', "`")
    hints = [directory + quote for directory in packages if directory != "." for quote in quotes]
    if module and "." in packages:
        hints += [module + quote for quote in quotes]
    candidates = [
        path for path in list_files_recursive(repo, revision)
        if path.endswith("_test.go") and path not in covered
    ]
    grouped: dict[tuple[str, str], dict[str, str]] = {}
    for path, blob in sorted(read_blobs(repo, revision, candidates).items()):
        text = blob.decode(errors="replace")
        if not any(hint in text for hint in hints):
            continue
        if not (set(aliases_of(text).values()) | set(dots_of(text))) & set(packages):
            continue
        try:
            clause = package_name(text)
        except ValueError:
            continue
        grouped.setdefault((str(Path(path).parent), clause), {})[path] = text
    for (directory, clause), group in sorted(grouped.items()):
        # What the package of these tests declares stays in the donor, so a
        # test that also uses one of those names is a mixed test.
        own: set[str] = set()
        siblings = [path for path in list_dir(repo, revision, directory) if path.endswith(".go")]
        for blob in read_blobs(repo, revision, siblings).values():
            text = blob.decode(errors="replace")
            try:
                if package_name(text) != clause:
                    continue
            except ValueError:
                continue
            own.update(item.name for item in GoFile(text).declarations if item.kind != "method")
        found = _tests(
            group, set(), set(all_moved), all_outside | own,
            {path: GoFile(text) for path, text in group.items()},
            set(), aliases_of, all_moved | all_outside,
            foreign=foreign, own=own,
            foreign_methods=foreign_methods, dots_of=dots_of, dot_names=dot_names,
        )
        found = [test for test in found if (test.file, test.name) not in moved_pairs]
        if directory in packages:
            facts.tests[directory] += found
        else:
            facts.tests.setdefault(directory, []).extend(found)
            facts.moved_names.setdefault(directory, set(all_moved))
            facts.outside_names.setdefault(directory, set(all_outside))
    return facts
