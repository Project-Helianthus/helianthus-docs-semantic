#!/usr/bin/env python3
"""Run harness-only Go recorders inside a scratch unpack of a pinned tree; the pin's own sources are never edited."""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

GO_SOURCES = Path(__file__).resolve().parent / "go"


def run(reference, entry_id, package, sources, test, output, extra_env=None):
    """Copy GO_SOURCES/<sources>/*.go into <unpack>/<package>/ and run the named recorder test there."""
    item = common.entry(reference, entry_id)
    scratch = common.scratch_root() / "rec" / f"{reference}-{item['id']}-{item['commit'][:12]}"
    tree = common.unpack(item, scratch)
    destination = tree / package
    for stale in destination.glob("zz_oracle_*"):
        stale.unlink()
    for source in sorted((GO_SOURCES / sources).glob("*.go")):
        shutil.copyfile(source, destination / source.name)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = common.go_env({"ORACLE_OUT": str(output), **(extra_env or {})})
    result = common.go_run(["test", "-count=1", "-run", test, f"./{package}/"], tree, env)
    if result.returncode != 0:
        sys.exit(f"recorder {test} failed in {entry_id}: {(result.stdout + result.stderr)[-3000:]}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--test", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.reference, args.entry, args.package, args.sources, args.test, args.output)


if __name__ == "__main__":
    main()
