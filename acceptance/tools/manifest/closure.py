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


@dataclass
class PackageFacts:
    moved_decls: dict[str, str]
    outside_decls: dict[str, str]
    symbol_uses: dict[str, list[str]]
    outside_uses: list[str]
    tests: list[TestFunction]


def blank_source(source: str, literal: str = " ") -> str:
    """Replace comments, strings and runes with spaces. Newlines stay.

    ``literal`` marks the first character of each string or rune, so a
    caller that needs to see where a literal stood can keep one token there.
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
            chars[index] = literal
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
            chars[index] = literal
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
    parsed: dict[str, "GoFile"] | None = None,
    struct_types: set[str] | None = None,
    aliases_of: "Callable[[str], dict[str, str]] | None" = None,
    qualified_names: set[str] | None = None,
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
                reached: set[tuple[str, str]] = set()
                uses = source.uses(
                    declaration, package_names, struct_types or set(), aliases, reached
                )
                uses |= _qualified(reached, qualified_names)
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
                    reached = set()
                    assertion_uses = source.uses(
                        declaration, package_names, struct_types or set(), aliases, reached,
                        window=(body_start + start, body_start + end),
                    )
                    assertion_uses |= _qualified(reached, qualified_names)
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
            tests.append(TestFunction(name=name, file=path, uses=uses, assertions=assertions))
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
            while at < end:
                if self.tokens[at][0] == ";":
                    at += 1
                    continue
                stop = self._statement_end(at, end)
                self._spec(kind, at, stop, found, at)
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

    def _spec(self, kind: str, start: int, stop: int, found: list[Declaration], first: int) -> None:
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
        for at in names:
            if self.tokens[at][0] != "_":
                found.append(Declaration(
                    name=self.tokens[at][0],
                    kind=kind,
                    first=first,
                    last=stop,
                    skip=set(names),
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

    def _literal(self, index: int, low: int, stack: list[tuple[int, str, bool]], struct_types: set[str]) -> tuple[str, bool]:
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
                if self._word(opener - 2) == "]":
                    return "collection", True
                return "struct", False
            return "other", False
        if before == "]":
            opener = self.open.get(index - 1, -1)
            named = self._word(opener - 1) if opener > low else ""
            if named and _is_name(named):
                return ("struct" if named in struct_types else "other"), False
            return "other", False
        if before and _is_name(before):
            start = index - 1
            qualified = False
            if start - 2 >= low and self._word(start - 1) == "." and _is_name(self._word(start - 2)):
                start -= 2
                qualified = True
            is_struct = qualified or before in struct_types
            if start > low and self._word(start - 1) == "]":
                return "collection", is_struct
            return ("struct" if is_struct else "other"), False
        return "other", False

    def _scope_end(self, stack: list[tuple[int, str, bool]], limit: int) -> int:
        return self._end_of(stack[-1][0]) + 1 if stack else limit

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

    def _local_declaration(self, index: int, limit: int, stack: list[tuple[int, str, bool]], skip: set[int], add) -> None:
        kind = self._word(index)
        end = self._scope_end(stack, limit)
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
                    kind, element = self._literal(index, low, stack, struct_types)
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
                    lead = self._word(chain[-1] - 1) if chain[-1] - 1 >= low else ""
                    if lead in ("if", "for", "switch"):
                        start, stop = self._header_scope(index, high, chain=lead == "if")
                    elif lead == "case":
                        cursor = index + 1
                        while cursor < high and self._word(cursor) != ":":
                            cursor += 1
                        start, stop = cursor, self._clause_end(cursor + 1, high, stack)
                    else:
                        start = self._statement_end(chain[-1], high)
                        stop = self._scope_end(stack, high)
                    for at in chain:
                        add(self.tokens[at][0], start, stop)
            elif word in ("var", "const", "type") and stack and (
                self._word(index + 1) == "(" or _is_name(self._word(index + 1))
            ):
                self._local_declaration(index, high, stack, skip, add)
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

    def _initializer_type(self, start: int, stop: int) -> str | None:
        """Type name of an initializer that is a struct literal ``T{...}`` or ``&T{...}``."""
        cursor = start
        if cursor < stop and self._word(cursor) == "&":
            cursor += 1
        if cursor + 1 < stop and _is_name(self._word(cursor)) and self._word(cursor + 1) == "{":
            return self._word(cursor)
        return None

    def method_uses(self, declaration: Declaration, keys: set[str]) -> set[str]:
        """Method keys of ``keys`` that the declaration refers to.

        A reference is ``name.Method`` where ``name`` is a parameter, receiver
        or local variable that is declared with a package type ``T`` and
        ``T.Method`` is in ``keys``, or the method expression ``T.Method``. A
        name that is bound more than once to different types, or to a value
        whose type is not spelled, resolves to no type. A field is never a
        method key, so a field selector is not a reference.
        """
        low, high = declaration.first, declaration.last
        types: dict[str, str | None] = {}

        def bind(name: str, kind: str | None) -> None:
            if name in types and types[name] != kind:
                types[name] = None
            else:
                types[name] = kind

        for name, kind in declaration.typed:
            bind(name, kind)
        index = low
        while index < high:
            word = self.tokens[index][0]
            if word == "func" and self._word(index + 1) == "(" and not (
                index == low and declaration.kind in ("func", "method")
            ):
                for name, kind in self._typed_signature(index + 1):
                    bind(name, kind)
            elif word == ":=":
                chain: list[int] = []
                at = index - 1
                while at >= low and _is_name(self.tokens[at][0]):
                    chain.append(at)
                    if at - 1 >= low and self._word(at - 1) == ",":
                        at -= 2
                    else:
                        break
                kind = None
                if len(chain) == 1:
                    kind = self._initializer_type(index + 1, self._statement_end(index + 1, high))
                for at in chain:
                    bind(self.tokens[at][0], kind)
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
                    for name_at in chain:
                        bind(self.tokens[name_at][0], kind)
            index += 1
        found: set[str] = set()
        for index in range(low, high):
            word = self.tokens[index][0]
            if (
                not _is_name(word)
                or (index > low and self._word(index - 1) == ".")
                or self._word(index + 1) != "."
                or not self._word(index + 2)
                or not _is_name(self._word(index + 2))
            ):
                continue
            kind = types.get(word, word)
            if kind is None:
                continue
            key = f"{kind}.{self._word(index + 2)}"
            if key in keys:
                found.add(key)
        return found


_IMPORT_LINE = re.compile(r'^\s*(?:import\s+)?([A-Za-z_][A-Za-z0-9_]*|\.|_)?\s*"([^"\n]+)"\s*(?://.*)?$')
_TOP_LEVEL = re.compile(r"^(?:func|type|var|const)\b")


def _module_path(repo: Path, revision: str) -> str:
    blob = read_blobs(repo, revision, ["go.mod"]).get("go.mod")
    if blob is None:
        return ""
    match = re.search(r"(?m)^\s*module\s+(\S+)", blob.decode(errors="replace"))
    return match.group(1).strip('"') if match else ""


def _import_aliases(
    text: str,
    resolve: "Callable[[str], str | None]",
    clause_of: "Callable[[str], str]",
) -> dict[str, str]:
    """Import names of one file that stand for a donor directory.

    ``resolve`` maps an import path to the donor directory it names, or None.
    An import without a name takes the package clause of that directory.
    """
    aliases: dict[str, str] = {}
    for line in text.splitlines():
        if _TOP_LEVEL.match(line) and not line.startswith("import"):
            break
        found = _IMPORT_LINE.match(line)
        if not found:
            continue
        local, path = found.group(1), found.group(2)
        if local in (".", "_"):
            continue
        directory = resolve(path)
        if directory is None:
            continue
        name = local or clause_of(directory)
        if name:
            aliases[name] = directory
    return aliases


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


def _struct_closure(declarations: list[Declaration]) -> set[str]:
    """Names of types that are structs, aliases and defined types of structs included."""
    struct_types = {item.name for item in declarations if item.kind == "type" and item.struct}
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

    # Any donor directory a moved file imports is read, so that a name it uses
    # there is found even when the input names no symbol of that directory.
    loaded = list(packages)
    for kind, item in entries:
        if kind != "move":
            continue
        for directory in sorted(set(aliases_of(texts[item["package"].rstrip("/")][item["path"]]).values())):
            if directory not in parsed and clause_of(directory):
                load(directory, clause_of(directory))
                loaded.append(directory)
    info: dict[str, dict[str, object]] = {}
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
        info[directory] = {
            "declared": declared,
            "struct_types": _struct_closure(every),
            "methods": methods,
            "lookup": lookup,
            "moved_keys": moved_keys,
            "stay_keys": stay_keys,
            "moved_names": {key for key in moved_keys if "." not in key},
            "stay_names": {key for key in stay_keys if "." not in key},
        }
    if facts.errors:
        return facts
    outside: set[str] = set()
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
                declaration, declared, struct_types, aliases, reached
            )
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
            called = files[moved_keys[key]].method_uses(declaration, {item.key for item in methods})
            called.discard(declaration.key)
            for method_key in called:
                if method_key in moved_keys:
                    carried.add(method_key)
                elif method_key not in stay_keys:
                    outside.add(method_key)
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
    for directory in packages:
        facts.moved_names[directory] |= all_moved
        facts.outside_names[directory] |= all_outside
    moved_pairs = {(item["file"], item["name"]) for item in facts.moved}
    for directory in packages:
        found = _tests(
            texts[directory], set(), facts.moved_names[directory], facts.outside_names[directory],
            parsed[directory], info[directory]["struct_types"], aliases_of,
            all_moved | all_outside,
        )
        facts.tests[directory] = [
            test for test in found if (test.file, test.name) not in moved_pairs
        ]
    # A test file outside the package of its directory (an external test
    # package) and a test file of a donor directory that the input does not
    # name still exercise moved symbols when it imports a package of the move.
    covered = {path for directory in packages for path in texts[directory]}
    hints = [directory + '"' for directory in packages if directory != "."]
    if module and "." in packages:
        hints.append(module + '"')
    candidates = [
        path for path in list_files_recursive(repo, revision)
        if path.endswith("_test.go") and path not in covered
    ]
    grouped: dict[str, dict[str, str]] = {}
    for path, blob in sorted(read_blobs(repo, revision, candidates).items()):
        text = blob.decode(errors="replace")
        if not any(hint in text for hint in hints):
            continue
        if not set(aliases_of(text).values()) & set(packages):
            continue
        grouped.setdefault(str(Path(path).parent), {})[path] = text
    for directory, group in sorted(grouped.items()):
        found = _tests(
            group, set(), set(), set(), {path: GoFile(text) for path, text in group.items()},
            set(), aliases_of, all_moved | all_outside,
        )
        found = [test for test in found if (test.file, test.name) not in moved_pairs]
        if directory in packages:
            facts.tests[directory] += found
        else:
            facts.tests[directory] = found
            facts.moved_names[directory] = set(all_moved)
            facts.outside_names[directory] = set(all_outside)
    return facts
