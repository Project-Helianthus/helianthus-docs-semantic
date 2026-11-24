#!/usr/bin/env python3
"""Check the committed oracle (items 13 and 14).

  check.py --index              every vector payload is in index.json with its sha256, and every file-backed entry exists
  check.py --replay <reference> re-record the reference under .tmp/ and compare every actual with the frozen expectation
  check.py --restart            compare the two lifecycles recorded under acceptance/vectors/current/restart/

Nothing is ever written under acceptance/vectors by --replay, and index.json is never refreshed.
"""

import argparse
import bisect
import collections
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
VECTORS = ROOT / "acceptance" / "vectors"
INDEX = VECTORS / "index.json"
ORIGINS = {"recorded-current", "recorded-released", "recorded-pre-port", "specification", "synthetic"}
ROLES = {"expected-output", "input"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_index():
    return json.loads(INDEX.read_text(encoding="utf-8"))["vectors"]


def references():
    return json.loads((HERE / "references.json").read_text(encoding="utf-8"))["references"]


def verify_index():
    errors = []
    entries = load_index()
    known = references()
    by_path = {}
    for entry in entries:
        if entry["path"] in by_path:
            errors.append(f"{entry['path']}: listed twice")
        by_path[entry["path"]] = entry
        if entry["origin"] not in ORIGINS:
            errors.append(f"{entry['path']}: origin {entry['origin']!r} is not one of the index origins")
        if entry["reference"] not in known:
            errors.append(f"{entry['path']}: reference {entry['reference']!r} is not in references.json")
        if entry["role"] not in ROLES:
            errors.append(f"{entry['path']}: role {entry['role']!r}")
        file = VECTORS / entry["path"]
        if entry.get("digest_only"):
            continue
        if not file.is_file():
            errors.append(f"{entry['path']}: indexed file is missing")
        elif sha256(file) != entry["sha256"]:
            errors.append(f"{entry['path']}: sha256 differs from index.json")
    for file in sorted(p for p in VECTORS.rglob("*") if p.is_file() and p.name != "index.json"):
        relative = file.relative_to(VECTORS).as_posix()
        if relative not in by_path:
            errors.append(f"{relative}: vector payload is not in index.json")
    return errors


def replay(reference):
    errors = []
    entries = [e for e in load_index() if e["reference"] == reference]
    expected = {e["path"]: e for e in entries if e["role"] == "expected-output"}
    for entry in entries:
        if entry["role"] == "input":
            file = VECTORS / entry["path"]
            if not file.is_file():
                errors.append(f"{entry['path']}: indexed input is missing")
            elif sha256(file) != entry["sha256"]:
                errors.append(f"{entry['path']}: indexed input sha256 differs from index.json")
    if errors:
        return errors
    target = ROOT / ".tmp" / "oracle-replay" / reference
    run = subprocess.run([str(HERE / "record.sh"), reference, "--replay", "--no-sessions"])
    if run.returncode != 0:
        return [f"record.sh {reference} --replay exited {run.returncode}"]
    actual_vectors = target / "vectors"
    if reference == "current":
        for entry in entries:
            if entry["role"] == "input" and entry["path"].endswith("/session.json") and "/sessions/" in entry["path"]:
                output_path = entry["path"][: -len("session.json")] + "output.json"
                if output_path not in expected:
                    errors.append(f"{entry['path']}: the session has no expected-output entry {output_path}")
                    continue
                actual = actual_vectors / output_path
                actual.parent.mkdir(parents=True, exist_ok=True)
                run = subprocess.run([sys.executable, "-I", str(HERE / "replay_session.py"), "--reference", reference, "--session", str(VECTORS / entry["path"]), "--output", str(actual),
                                      "--provenance", str(target / "oracle" / "provenance" / (Path(entry["path"]).parent.relative_to("current/sessions").as_posix().replace("/", "-") + ".json"))])
                if run.returncode != 0 or not actual.is_file():
                    errors.append(f"{entry['path']}: the replay process produced no output (exit {run.returncode})")
    for path, entry in sorted(expected.items()):
        actual = actual_vectors / path
        if not actual.is_file():
            errors.append(f"{path}: missing actual output")
            continue
        file = VECTORS / path
        if file.is_file() and not entry.get("digest_only"):
            if actual.read_bytes() != file.read_bytes():
                errors.append(f"{path}: actual output differs from the frozen expectation" + describe(file, actual))
        elif sha256(actual) != entry["sha256"]:
            errors.append(f"{path}: actual digest differs from the initial expected digest")
    if actual_vectors.is_dir():
        for actual in sorted(p for p in actual_vectors.rglob("*") if p.is_file()):
            relative = actual.relative_to(actual_vectors).as_posix()
            if relative not in expected:
                errors.append(f"{relative}: extra actual output with no expected-output entry")
    errors += compare_build(reference, target / "oracle")
    return errors


def describe(expected_file, actual_file):
    try:
        left, right = json.loads(expected_file.read_text(encoding="utf-8")), json.loads(actual_file.read_text(encoding="utf-8"))
    except ValueError:
        return ""
    if isinstance(left, dict) and isinstance(right, dict):
        changed = [key for key in sorted(set(left) | set(right)) if left.get(key) != right.get(key)]
        return " (differing members: " + ", ".join(changed) + ")"
    return ""


UNTRIMMED_FORM = "go install module@version"
# Sections of a Go ELF executable that carry no file system path and no address downstream of one.
HOST_PATH_SYMBOL = "runtime.defaultGOROOT.str"
# Sections that are loaded into memory and hold code or data. Their bytes move with the host paths (the Go root string changes length, the
# path-bearing tables after it change size) and the addresses written into them move with them; they are compared with that shift accounted for.
HOST_PATH_SYMBOLS = (HOST_PATH_SYMBOL, "runtime.defaultGOROOT")
LOADED_SECTIONS = (".text", ".rodata", ".noptrdata", ".data")
PATH_FREE_SECTIONS = (".typelink", ".go.buildinfo", ".debug_abbrev", ".debug_frame", ".debug_loclists", ".debug_rnglists", ".debug_addr", ".strtab", ".shstrtab")


def elf_view(data):
    """Section names and sizes, the path-free sections' digests, the symbol table without addresses, and the build information of a Go ELF64 executable."""
    shoff = struct.unpack_from("<Q", data, 0x28)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 0x3A)
    raw = [struct.unpack_from("<IIQQQQ", data, shoff + index * shentsize) for index in range(shnum)]
    names_at = raw[shstrndx][4]

    def text(offset, base):
        return data[base + offset:data.index(b"\0", base + offset)].decode("utf-8", "replace")

    sections = {text(name, names_at): (kind, offset, size) for name, kind, _flags, _addr, offset, size in raw}
    body = {name: data[offset:offset + size] for name, (kind, offset, size) in sections.items() if kind != 8}
    symbols = []
    if ".symtab" in body and ".strtab" in body:
        table, names = body[".symtab"], body[".strtab"]
        for position in range(0, len(table) - 23, 24):
            name, info, _other, _shndx, _value, size = struct.unpack_from("<IBBHQQ", table, position)
            symbol = names[name:names.index(b"\0", name)].decode("utf-8", "replace")
            # The size of the string that holds the Go root path is the length of that path: the one symbol that records a host path.
            symbols.append((symbol, info, 0 if symbol == HOST_PATH_SYMBOL else size))
    info = body.get(".go.buildinfo", b"")
    version = modinfo = b""
    if info.startswith(b"\xff Go buildinf:") and info[15] & 2:
        cursor = 32
        parts = []
        for _ in range(2):
            length = shift = 0
            while True:
                byte = info[cursor]
                cursor += 1
                length |= (byte & 0x7F) << shift
                shift += 7
                if byte < 0x80:
                    break
            parts.append(info[cursor:cursor + length])
            cursor += length
        version, modinfo = parts
    return {"sections": [(name, kind, size) for name, (kind, _offset, size) in sections.items()], "path_free": {name: hashlib.sha256(body[name]).hexdigest() for name in PATH_FREE_SECTIONS if name in body},
            "symbols": sorted(symbols), "version": version, "modinfo": modinfo}


def elf_layout(data):
    """Sections (name -> kind, address, file offset, size) and symbols (name, info, value, size) of a Go ELF64 executable."""
    shoff = struct.unpack_from("<Q", data, 0x28)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 0x3A)
    raw = [struct.unpack_from("<IIQQQQ", data, shoff + index * shentsize) for index in range(shnum)]
    names_at = raw[shstrndx][4]
    sections = {data[names_at + name:data.index(b"\0", names_at + name)].decode("utf-8", "replace"): (kind, addr, offset, size) for name, kind, _flags, addr, offset, size in raw}
    symbols = []
    if ".symtab" in sections and ".strtab" in sections:
        _kind, _addr, table_at, table_size = sections[".symtab"]
        _kind, _addr, names_base, _size = sections[".strtab"]
        for position in range(table_at, table_at + table_size - 23, 24):
            name, info, _other, _shndx, value, size = struct.unpack_from("<IBBHQQ", data, position)
            symbols.append((data[names_base + name:data.index(b"\0", names_base + name)].decode("utf-8", "replace"), info, value, size))
    return sections, symbols


def signed(value, width):
    return value - (1 << (8 * width)) if value >> (8 * width - 1) else value


def loaded_differences(delivered, rebuilt):
    """Names of the loaded code and data sections whose bytes differ once the host-dependent shift is set aside.

    A symbol that both executables have (same name, kind and size) is an anchor: from its address up to the next anchor the rebuild
    holds the same bytes shifted by the distance between the two addresses. The Go root string and the variable that points at it are
    set aside. Every other byte must be equal, or lie in a 4 or 8 byte word (an absolute address or an offset relative to the next
    instruction) that changed by exactly the shift of the symbol it points at."""
    left_sections, left_symbols = elf_layout(delivered)
    right_sections, right_symbols = elf_layout(rebuilt)
    by_key = collections.defaultdict(list)
    for name, info, value, size in right_symbols:
        by_key[(name, info, size)].append(value)
    used = collections.Counter()
    shifts = {}
    for name, info, value, size in left_symbols:
        if name == HOST_PATH_SYMBOL or not value:
            continue
        key = (name, info, size)
        position = used[key]
        used[key] += 1
        if position < len(by_key[key]):
            shifts.setdefault(value, by_key[key][position] - value)
    for name, (_kind, addr, _offset, _size) in left_sections.items():
        if addr and name in right_sections:
            shifts.setdefault(addr, right_sections[name][1] - addr)
    anchors = sorted(shifts)

    def shift_at(address):
        found = bisect.bisect_right(anchors, address) - 1
        return shifts[anchors[found]] if found >= 0 else 0

    skipped = [(value, value + size) for name, _info, value, size in left_symbols if name in HOST_PATH_SYMBOLS]
    different = []
    for name in LOADED_SECTIONS:
        if name not in left_sections or name not in right_sections:
            different.append(name)
            continue
        _kind, addr, offset, size = left_sections[name]
        _kind, right_addr, right_offset, right_size = right_sections[name]
        cuts = {addr + size} | {anchor for anchor in anchors if addr <= anchor < addr + size} | {edge for span in skipped for edge in span if addr < edge < addr + size}
        bounds = sorted(cuts | {addr})
        widths = (4,) if name == ".text" else (8, 4)
        for start, end in zip(bounds, bounds[1:]):
            shift = shift_at(start)
            old = delivered[offset + start - addr:offset + end - addr]
            at = start + shift - right_addr
            new = rebuilt[right_offset + at:right_offset + at + (end - start)] if 0 <= at and at + (end - start) <= right_size else None
            if new is None:
                different.append(name)
                break
            if old == new:
                continue
            changed = [index for index in range(len(old)) if old[index] != new[index] and not any(low <= start + index < high for low, high in skipped)]
            cursor = 0
            explained = True
            while cursor < len(changed):
                first = changed[cursor]
                found = False
                for width in widths:
                    for word in range(max(first - width + 1, 0), min(first, len(old) - width) + 1):
                        before = int.from_bytes(old[word:word + width], "little")
                        after = int.from_bytes(new[word:word + width], "little")
                        moved = signed(after, width) - signed(before, width)
                        place = start + word
                        targets = [(before, shift_at(before))]
                        if width == 4:
                            targets += [(place + 4 + extra + signed(before, 4), shift_at(place + 4 + extra + signed(before, 4)) - shift_at(place)) for extra in range(9)]
                        if any(moved == expected for _target, expected in targets):
                            found = True
                            while cursor < len(changed) and changed[cursor] < word + width:
                                cursor += 1
                            break
                    if found:
                        break
                if not found:
                    explained = False
                    break
            if not explained:
                different.append(name)
                break
    return different


def untrimmed_differences(delivered, rebuilt):
    """Why a rebuild of an untrimmed build (no -trimpath) is not the delivered binary once the host-dependent build paths are set aside.

    The executable embeds the Go root and module cache paths of the host that built it, in .rodata, .gopclntab and the debug sections,
    and every section laid out after them moves with their lengths. What is compared instead is everything those paths do not touch:
    toolchain version, module graph with its hashes and build settings, section names, the symbol table (names, kinds, sizes), the
    byte content of the path-free sections and the code and data sections (.text, .rodata, .noptrdata, .data) with the shift of the
    host-dependent layout set aside (loaded_differences)."""
    left, right = elf_view(delivered), elf_view(rebuilt)
    problems = []
    if not left["version"] or not left["modinfo"]:
        problems.append("the delivered binary carries no readable build information")
    if left["version"] != right["version"]:
        problems.append("toolchain version differs")
    if left["modinfo"] != right["modinfo"]:
        problems.append("module graph, hashes or build settings differ")
    if [name for name, _kind, _size in left["sections"]] != [name for name, _kind, _size in right["sections"]]:
        problems.append("section list differs")
    if left["symbols"] != right["symbols"]:
        problems.append("symbol table differs")
    for name in PATH_FREE_SECTIONS:
        if left["path_free"].get(name) != right["path_free"].get(name):
            problems.append(f"path-free section {name} differs")
    for name in loaded_differences(delivered, rebuilt):
        problems.append(f"code or data section {name} differs")
    return problems


def host_independent(entry):
    """A manifest entry without what depends on the host: the digest and size of an untrimmed build, and the host platform of the toolchain."""
    return {key: (" ".join(value.split()[:3]) if key == "toolchain" else value) for key, value in entry.items() if key not in ("sha256", "size")}


def compare_build(reference, actual_oracle):
    errors = []
    committed_bom = {p.name: p for p in (HERE / "bom").glob(f"{reference}-*.json")}
    actual_bom = {p.name: p for p in (actual_oracle / "bom").glob("*.json")} if (actual_oracle / "bom").is_dir() else {}
    for name in sorted(set(committed_bom) | set(actual_bom)):
        if name not in actual_bom:
            errors.append(f"bom/{name}: missing actual bill of materials")
        elif name not in committed_bom:
            errors.append(f"bom/{name}: extra actual bill of materials")
        elif committed_bom[name].read_bytes() != actual_bom[name].read_bytes():
            errors.append(f"bom/{name}: actual bill of materials differs from the committed one")
    manifest = json.loads((HERE / "binaries.json").read_text(encoding="utf-8"))["binaries"]
    rebuilt = {e["id"]: e for e in json.loads((actual_oracle / "binaries.json").read_text(encoding="utf-8"))["binaries"]} if (actual_oracle / "binaries.json").is_file() else {}
    for entry in manifest:
        if entry["reference"] != reference:
            continue
        delivered = HERE / entry["file"]
        if not delivered.is_file():
            errors.append(f"binary {entry['id']}: delivered file {entry['file']} is missing")
        elif sha256(delivered) != entry["sha256"]:
            errors.append(f"binary {entry['id']}: delivered file {entry['file']} does not have the recorded sha256")
        scratch = actual_oracle / entry["file"]
        if entry["id"] not in rebuilt or not scratch.is_file():
            errors.append(f"binary {entry['id']}: not rebuilt")
        elif entry["build_form"] == UNTRIMMED_FORM and sha256(scratch) != entry["sha256"]:
            # No -trimpath: the delivered bytes hold the paths of the host that built them (README, binaries).
            problems = untrimmed_differences(delivered.read_bytes(), scratch.read_bytes())
            if problems:
                errors.append(f"binary {entry['id']}: independent rebuild is not the delivered binary apart from host-dependent build paths: " + "; ".join(problems))
            elif host_independent(rebuilt[entry["id"]]) != host_independent(entry):
                errors.append(f"binary {entry['id']}: rebuilt manifest entry differs from binaries.json")
        elif sha256(scratch) != entry["sha256"]:
            errors.append(f"binary {entry['id']}: independent rebuild does not have the recorded sha256")
        elif rebuilt[entry["id"]] != entry:
            errors.append(f"binary {entry['id']}: rebuilt manifest entry differs from binaries.json")
    return errors


def restart():
    directory = VECTORS / "current" / "restart"
    if not directory.is_dir():
        return ["no restart vectors are recorded under acceptance/vectors/current/restart/"]
    first, second = (json.loads((directory / name).read_text(encoding="utf-8")) for name in ("cut-first.json", "cut-second.json"))
    differences = [key for key in sorted(set(first) | set(second)) if first.get(key) != second.get(key)]
    return [f"lifecycle difference in {key}" for key in differences]


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--index", action="store_true")
    group.add_argument("--replay", metavar="REFERENCE")
    group.add_argument("--restart", action="store_true")
    args = parser.parse_args()
    if args.index:
        errors = verify_index()
    elif args.restart:
        errors = restart()
    else:
        errors = replay(args.replay)
    for error in errors:
        print("FAIL:", error)
    print("FAILED" if errors else "OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
