"""Typed closure over a donor package at one commit.

Declarations come from the package directory. Uses are unqualified
identifiers in the moved files. A test left in the donor is mixed when it
uses both a moved symbol and a symbol that stays, and each of its assertions
is classified the same way.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
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
    # Reserved for names a test package declares and keeps; the symbol-level
    # closure reports those as ordinary uses, so it stays empty there.
    own: set[str] = field(default_factory=set)


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


# Symbol-level closure.
#
# A symbol is a top-level declaration: a function, type, var or const name, or
# a method written ``Receiver.Method``. Which symbol an identifier refers to,
# and which package it belongs to, is read from Go's own name resolution: the
# helper program in ``gotypes/`` type-checks the donor with go/types and
# reports, for every declaration, test function and assertion, the declared
# symbols it uses. A field label, a parameter, a receiver, a local binding, a
# type parameter and a package name never is one. This module classifies what
# the helper reports; it does not read Go syntax to decide what a name means.

HELPER_DIR = Path(__file__).resolve().parent / "gotypes"
HELPER_FILES = ("resolve.go", "flow.go")


class ResolverError(Exception):
    pass


def _module_path(repo: Path, revision: str) -> str:
    blob = read_blobs(repo, revision, ["go.mod"]).get("go.mod")
    if blob is None:
        return ""
    match = re.search(r"(?m)^\s*module\s+(\S+)", blob.decode(errors="replace"))
    return match.group(1).strip('"') if match else ""


def _escape_module_path(path: str) -> str:
    return "".join("!" + char.lower() if char.isupper() else char for char in path)


def _module_cache(go: str) -> Path | None:
    configured = os.environ.get("GOMODCACHE")
    if configured:
        return Path(configured)
    try:
        completed = subprocess.run([go, "env", "GOMODCACHE"], capture_output=True, text=True, check=False)
    except OSError:
        return None
    value = completed.stdout.strip()
    return Path(value) if completed.returncode == 0 and value else None


def _requirements(go_mod: str) -> dict[str, str]:
    """The module versions the donor's go.mod requires, after its replacements."""
    required: dict[str, str] = {}
    replaced: dict[str, tuple[str, str]] = {}
    block = ""
    for raw in go_mod.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if block:
            if line == ")":
                block = ""
                continue
            fields = line.split()
        else:
            fields = line.split()
            if fields[0] in ("require", "replace") and len(fields) > 1 and fields[1] == "(":
                block = fields[0]
                continue
            if fields[0] not in ("require", "replace"):
                continue
            block_kind, fields = fields[0], fields[1:]
        kind = block or block_kind
        if kind == "require" and len(fields) >= 2:
            required[fields[0].strip('"')] = fields[1].strip('"')
        elif kind == "replace" and "=>" in fields:
            arrow = fields.index("=>")
            target = fields[arrow + 1:]
            if len(target) == 2:
                replaced[fields[0].strip('"')] = (target[0].strip('"'), target[1].strip('"'))
            elif len(target) == 1:
                replaced[fields[0].strip('"')] = (target[0].strip('"'), "")
    resolved: dict[str, str] = {}
    for module, version in required.items():
        if module in replaced:
            module_to, version_to = replaced[module]
            if not version_to:
                continue
            resolved[module] = f"{module_to}@{version_to}"
        else:
            resolved[module] = f"{module}@{version}"
    return resolved


def _dependency_directories(repo: Path, revision: str, go: str) -> dict[str, str]:
    """Module directories of the donor's pinned dependencies in the module cache.

    A dependency whose directory is not in the cache is left out, and the
    helper then stands an empty package in for it.
    """
    blob = read_blobs(repo, revision, ["go.mod"]).get("go.mod")
    cache = _module_cache(go)
    if blob is None or cache is None:
        return {}
    found: dict[str, str] = {}
    for module, pinned in _requirements(blob.decode(errors="replace")).items():
        path, _, version = pinned.partition("@")
        directory = cache / (_escape_module_path(path) + "@" + version)
        if directory.is_dir():
            found[module] = str(directory)
    return found


def resolve_donor(repo: Path, revision: str, packages: list[str]) -> dict[str, object]:
    """Run the Go helper over the donor at ``revision``.

    The helper takes the text of every Go file of the donor and the donor
    directories the move names. There is no other reading of Go source: a
    missing Go toolchain or a helper that fails is an error, not a fallback.
    """
    go = shutil.which("go")
    if go is None:
        raise ResolverError("the go toolchain is required to resolve donor symbols and was not found")
    sources = [str(HELPER_DIR / name) for name in HELPER_FILES]
    missing = [path for path in sources if not Path(path).is_file()]
    if missing:
        raise ResolverError("helper source is missing: " + ", ".join(missing))
    names = [path for path in list_files_recursive(repo, revision) if path.endswith(".go")]
    files = {
        path: blob.decode(errors="replace")
        for path, blob in read_blobs(repo, revision, names).items()
    }
    payload = json.dumps({
        "module": _module_path(repo, revision),
        "files": files,
        "packages": packages,
        "deps": _dependency_directories(repo, revision, go),
    })
    with tempfile.TemporaryDirectory(prefix="manifest-resolve-") as scratch:
        try:
            completed = subprocess.run(
                [go, "run", *sources],
                input=payload,
                capture_output=True,
                text=True,
                check=False,
                cwd=scratch,
            )
        except OSError as error:
            raise ResolverError(f"cannot run the go helper: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        raise ResolverError("go helper failed: " + (detail[-1] if detail else f"exit {completed.returncode}"))
    try:
        return json.loads(completed.stdout)
    except ValueError as error:
        raise ResolverError(f"go helper wrote no JSON: {error}") from error


@dataclass
class SymbolFacts:
    moved: list[dict[str, object]] = field(default_factory=list)
    stays: list[dict[str, str]] = field(default_factory=list)
    outside_uses: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tests: dict[str, list[TestFunction]] = field(default_factory=dict)
    moved_names: dict[str, set[str]] = field(default_factory=dict)
    outside_names: dict[str, set[str]] = field(default_factory=dict)


def _spelled(reference: tuple[str, str], here: str) -> str:
    """A symbol as the manifest names it: bare in its own package, else ``directory.Name``."""
    directory, key = reference
    return key if directory == here else f"{directory}.{key}"


def _canonical(reference: tuple[str, str]) -> str:
    return f"{reference[0]}:{reference[1]}"


def _refs(items: list[list[str]]) -> set[tuple[str, str]]:
    return {(item[0], item[1]) for item in items}


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
    follow the same rule. Which symbol a name stands for comes from the type
    checker, whether or not the package it belongs to is named in the input.
    """
    facts = SymbolFacts()
    entries = [("move", item) for item in moves] + [("stay", item) for item in stays]
    packages = sorted({item["package"].rstrip("/") for _kind, item in entries})
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
    if facts.errors:
        return facts
    try:
        resolved = resolve_donor(repo, revision, packages)
    except ResolverError as error:
        facts.errors.append(f"go-resolver: {error}")
        return facts
    if resolved.get("errors"):
        facts.errors.extend(str(line) for line in resolved["errors"])
        return facts
    records = {
        (item["dir"], bool(item["xtest"])): item for item in resolved["packages"]
    }
    label = lambda item: item["dir"] + ("#xtest" if item["xtest"] else "")
    # A declaration belongs to the package its file is in: the package of a
    # directory or its external test package. The two may declare one name.
    lookup: dict[str, dict[tuple[str, str], tuple[dict, str]]] = {}
    methods: dict[str, list[dict]] = {}
    for directory in packages:
        lookup[directory] = {}
        for item in (records.get((directory, False)), records.get((directory, True))):
            if item is None:
                continue
            methods[label(item)] = []
            for declaration in item["decls"]:
                lookup[directory].setdefault((declaration["file"], declaration["key"]), (declaration, label(item)))
                if declaration["kind"] == "method":
                    methods[label(item)].append(declaration)
    moved_keys: dict[str, dict[str, str]] = {directory: {} for directory in packages}
    stay_keys: dict[str, dict[str, str]] = {directory: {} for directory in packages}
    for kind, item in entries:
        directory = item["package"].rstrip("/")
        target = moved_keys[directory] if kind == "move" else stay_keys[directory]
        if (item["path"], item["symbol"]) not in lookup[directory]:
            facts.errors.append(f"absent-symbol: {item['path']} {item['symbol']}")
        elif item["symbol"] in target:
            facts.errors.append(f"duplicate-symbol: {item['path']} {item['symbol']}")
        else:
            target[item["symbol"]] = item["path"]
    for directory in packages:
        for key in moved_keys[directory]:
            if key in stay_keys[directory]:
                facts.errors.append(f"moved-and-stays: {moved_keys[directory][key]} {key}")
    if facts.errors:
        return facts

    def identity(directory: str, key: str, path: str) -> tuple[str, str]:
        return (lookup[directory][(path, key)][1], key)

    moved_refs = {
        identity(directory, key, path)
        for directory in packages for key, path in moved_keys[directory].items()
    }
    stay_refs = {
        identity(directory, key, path)
        for directory in packages for key, path in stay_keys[directory].items()
    }
    outside: set[str] = set()
    for directory in packages:
        for key in sorted(moved_keys[directory]):
            declaration, here = lookup[directory][(moved_keys[directory][key], key)]
            for selector in sorted(set(declaration.get("unresolved", []))):
                facts.errors.append(f"unresolved-selector: {declaration['file']} {key}.{selector}")
            used = _refs(declaration["uses"])
            # A function, type or value may name itself.
            used.discard((here, key))
            carried = set()
            for reference in used:
                if reference in moved_refs:
                    carried.add(_spelled(reference, here))
                elif reference not in stay_refs:
                    outside.add(_spelled(reference, here))
            facts.moved.append({
                "package": directory,
                "file": moved_keys[directory][key],
                "name": key,
                "uses": sorted(carried),
            })
            if declaration["kind"] == "type":
                for method in methods.get(here, []):
                    if (
                        method["receiver"] == declaration["name"]
                        and (here, method["key"]) not in moved_refs
                        and (here, method["key"]) not in stay_refs
                    ):
                        outside.add(_spelled((here, method["key"]), directory))
        for key in sorted(stay_keys[directory]):
            facts.stays.append({"package": directory, "file": stay_keys[directory][key], "name": key})
    facts.outside_uses = sorted(outside)
    facts.moved.sort(key=lambda item: (item["package"], item["file"], item["name"]))
    facts.stays.sort(key=lambda item: (item["package"], item["file"], item["name"]))
    if facts.outside_uses:
        return facts
    # A test reaches a moved symbol through a helper that its package declares
    # in a test file just as it reaches it directly.
    helper_uses: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for item in resolved["packages"]:
        for declaration in item["decls"]:
            if declaration["test"]:
                # Helpers that share a name in files under different build
                # constraints each keep their reach: the closure is their union.
                helper_uses.setdefault((label(item), declaration["key"]), set()).update(_refs(declaration["uses"]))

    def expand(direct: set[tuple[str, str]]) -> set[tuple[str, str]]:
        reached = set(direct)
        pending = list(direct)
        while pending:
            for found in helper_uses.get(pending.pop(), ()):
                if found not in reached:
                    reached.add(found)
                    pending.append(found)
        return reached

    moved_pairs = {(item["file"], item["name"]) for item in facts.moved}
    seen: set[str] = set()
    for item in sorted(resolved["packages"], key=lambda entry: (entry["dir"], entry["xtest"])):
        directory = item["dir"]
        found: list[TestFunction] = []
        for test in item["tests"]:
            if (test["file"], test["name"]) in moved_pairs:
                continue
            assertions = []
            for ordinal, check in enumerate(test["assertions"], start=1):
                reached = expand(_refs(check["uses"]))
                called = sorted(
                    _spelled(reference, directory)
                    for reference in _refs(check["calls"])
                    if reference in moved_refs and reference in reached
                )
                assertions.append(Assertion(
                    name=_assertion_name(check["text"], test["name"], ordinal),
                    function=test["name"],
                    file=test["file"],
                    uses={_canonical(reference) for reference in reached},
                    helpers=called,
                ))
            found.append(TestFunction(
                name=test["name"],
                file=test["file"],
                uses={_canonical(reference) for reference in expand(_refs(test["uses"]))},
                assertions=assertions,
            ))
        facts.tests.setdefault(directory, []).extend(found)
        for test in found:
            seen |= test.uses
            for check in test.assertions:
                seen |= check.uses
    moved_canon = {_canonical(reference) for reference in moved_refs}
    # Every symbol a test uses that does not move stays in the donor: one the
    # input declares, one of a package the input does not name, and one a
    # test package declares for itself.
    outside_canon = seen - moved_canon
    for directory in packages:
        facts.tests.setdefault(directory, [])
    for directory in facts.tests:
        facts.moved_names[directory] = set(moved_canon)
        facts.outside_names[directory] = set(outside_canon)
    return facts
