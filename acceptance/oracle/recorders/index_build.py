#!/usr/bin/env python3
"""Write acceptance/vectors/index.json once, at initial recording (item 11).

Recorded outputs come from the entry files of record.sh; every other file under acceptance/vectors is a hand-authored or
session input. The index is the frozen manifest: later rows and replays read it and never regenerate it."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

KINDS = {"native", "new-binding"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(vectors, entry_files):
    vectors = Path(vectors)
    outputs = {}
    for entry_file in entry_files:
        for entry in json.loads(Path(entry_file).read_text(encoding="utf-8")):
            outputs[entry["path"]] = entry
    index = []
    for path in sorted(p for p in vectors.rglob("*") if p.is_file() and p.name != "index.json"):
        relative = path.relative_to(vectors).as_posix()
        if relative in outputs:
            entry = dict(outputs[relative])
        else:
            document = json.loads(path.read_text(encoding="utf-8"))
            origin = "specification" if relative.startswith(("spec/", "specification/")) else "synthetic"
            entry = {"path": relative, "origin": origin, "reference": "current", "role": "input", "recorder": "hand-authored"}
            if isinstance(document, dict) and document.get("kind") in KINDS | {"specification", "native-only", "specification-operand"} and "case" in document:
                entry["case"] = document["case"]
                if document["kind"] in KINDS:
                    entry["kind"] = document["kind"]
        entry["sha256"] = sha256(path)
        index.append({key: entry[key] for key in ("path", "sha256", "origin", "reference", "role", "recorder", "case", "kind", "defect") if key in entry})
    common.write(vectors / "index.json", common.canonical({"format": "helianthus-oracle-vector-index/1", "vectors": index}))
    return index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vectors", required=True)
    parser.add_argument("--entries", nargs="+", required=True)
    args = parser.parse_args()
    print(len(build(args.vectors, args.entries)), "entries")


if __name__ == "__main__":
    main()
