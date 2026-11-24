#!/usr/bin/env python3
"""Sealed move manifests: generate, check, compare, receipt, deletion.

The commands and the acquisition recipe are specified in README.md.
check and compare do not write manifests or sealed lists.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import manifestlib


def _move(value: str) -> dict[str, str]:
    path, separator, destination = value.partition("=")
    repository, colon, destination_path = destination.partition(":")
    if not separator or not colon or not path or not repository or not destination_path:
        raise argparse.ArgumentTypeError(
            "move must be <donor-path>=<destination-repository>:<destination-path>"
        )
    return {
        "path": path,
        "destination_repository": repository,
        "destination_path": destination_path,
    }


def _spec_from_flags(args: argparse.Namespace) -> dict:
    if args.input:
        spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        if not args.row or not args.donor_repository or not args.donor_sha:
            raise SystemExit(
                "generate requires --input or --row, --donor-repository and --donor-sha"
            )
        spec = {
            "row": args.row,
            "donor_repository": args.donor_repository,
            "donor_sha": args.donor_sha,
            "moves": [_move(item) for item in args.move or []],
            "new_files": [],
            "shared": [],
            "specimens": list(args.specimen or []),
            "assertions": [],
            "mapping_rows": [],
            "expectations": [],
            "expected_differences": [],
        }
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="acceptance/tools/manifest/main.py")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate")
    generate.add_argument("--input")
    generate.add_argument("--donor", required=True)
    generate.add_argument("--row")
    generate.add_argument("--donor-repository")
    generate.add_argument("--donor-sha")
    generate.add_argument("--move", action="append")
    generate.add_argument("--specimen", action="append")

    check = commands.add_parser("check")
    check.add_argument("--manifest", required=True)
    check.add_argument("--donor", required=True)

    compare = commands.add_parser("compare")
    compare.add_argument("--manifest", required=True)
    compare.add_argument("--destination", required=True)

    receipt = commands.add_parser("receipt")
    receipt.add_argument("--manifest", required=True)
    receipt.add_argument("--input", required=True)
    receipt.add_argument("--repository-checkout", action="append", default=[])

    deletion = commands.add_parser("deletion")
    deletion.add_argument("--input", required=True)
    deletion.add_argument("--gateway", required=True)

    args = parser.parse_args(argv)
    if args.command == "generate":
        return manifestlib.generate(_spec_from_flags(args), Path(args.donor))
    if args.command == "check":
        return manifestlib.check(Path(args.manifest), Path(args.donor))
    if args.command == "compare":
        return manifestlib.compare(Path(args.manifest), Path(args.destination))
    if args.command == "receipt":
        result = json.loads(Path(args.input).read_text(encoding="utf-8"))
        checkouts = {}
        for item in args.repository_checkout:
            repository, separator, path = item.partition("=")
            if not separator:
                raise SystemExit("repository checkout must be <repository>=<path>")
            checkouts[repository] = Path(path)
        return manifestlib.receipt(Path(args.manifest), result, checkouts)
    if args.command == "deletion":
        spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
        return manifestlib.deletion(spec, Path(args.gateway))
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
