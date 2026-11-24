#!/usr/bin/env python3
"""Check the committed oracle (items 13 and 14).

  check.py --index              every vector payload is in index.json with its sha256, and every file-backed entry exists
  check.py --replay <reference> re-record the reference under .tmp/ and compare every actual with the frozen expectation
  check.py --restart            compare the two lifecycles recorded under acceptance/vectors/current/restart/

Nothing is ever written under acceptance/vectors by --replay, and index.json is never refreshed.
"""

import argparse
import hashlib
import json
import shutil
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
                run = subprocess.run([sys.executable, "-I", str(HERE / "replay_session.py"), "--reference", reference, "--session", str(VECTORS / entry["path"]), "--output", str(actual)])
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
