"""Offline Ruff ratchet keyed by relative path, lexical symbol and rule."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUFF_VERSION = "0.15.10"


def read_json(text):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(text, object_pairs_hook=unique_pairs)


def record_key(record):
    if not isinstance(record, dict) or set(record) != {"path", "symbol", "rule", "count"}:
        raise ValueError("invalid baseline record fields")
    path = record["path"]
    if not isinstance(path, str) or not re.fullmatch(r"(?:scripts|tests)/[^\\]+\.py", path):
        raise ValueError("baseline path must be a relative Python source path")
    if any(part in {"", ".", ".."} for part in path.split("/")):
        raise ValueError("invalid baseline path")
    for field in ("symbol", "rule"):
        if not isinstance(record[field], str) or not record[field]:
            raise ValueError(f"invalid {field}")
    if not re.fullmatch(r"[A-Z]+[0-9]+", record["rule"]):
        raise ValueError("invalid rule")
    if type(record["count"]) is not int or record["count"] < 1:
        raise ValueError("count must be a positive integer")
    return path, record["symbol"], record["rule"]


def baseline_records(document):
    if not isinstance(document, dict) or set(document) != {"ruff_version", "generation", "records"}:
        raise ValueError("invalid baseline document")
    if document["ruff_version"] != RUFF_VERSION or not isinstance(document["generation"], str) or not document["generation"]:
        raise ValueError("baseline version or generation method missing")
    if not isinstance(document["records"], list):
        raise ValueError("baseline records must be an array")
    result = {}
    for record in document["records"]:
        key = record_key(record)
        if key in result:
            raise ValueError(f"duplicate baseline record: {key}")
        result[key] = record["count"]
    return result


def compare_records(current, baseline):
    errors = []
    for key, count in sorted(current.items()):
        if key not in baseline:
            errors.append(f"new finding: {key} count={count}")
        elif count > baseline[key]:
            errors.append(f"increased finding: {key} {baseline[key]} -> {count}")
    for key in sorted(baseline.keys() - current.keys()):
        errors.append(f"unused baseline entry; remove resolved debt: {key}")
    return errors


def lexical_symbol(source, row):
    tree = ast.parse(source)

    def walk_scope(node, parents):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if child.lineno <= row <= child.end_lineno:
                    return walk_scope(child, parents + [child.name])
        return ".".join(parents) or "<module>"

    return walk_scope(tree, [])


def findings_from_json(text, root):
    findings = read_json(text)
    if not isinstance(findings, list):
        raise ValueError("Ruff JSON must be an array")
    counts = Counter()
    for finding in findings:
        path = Path(finding["filename"]).resolve().relative_to(root.resolve()).as_posix()
        rule, message = finding["code"], finding["message"]
        row = finding["location"]["row"]
        if type(row) is not int or row < 1 or not isinstance(message, str):
            raise ValueError("invalid Ruff location or message")
        source = (root / path).read_text()
        if row > len(source.splitlines()):
            raise ValueError("Ruff row outside source")
        symbol = lexical_symbol(source, row)
        if rule in {"C901", "PLR0915"}:
            measured = re.search(r"\((\d+) > \d+\)", message)
            if measured is None:
                raise ValueError("missing measured complexity or statement count")
            count = int(measured.group(1))
        else:
            # Include the binding/message to distinguish separate naming violations.
            symbol += ":" + message
            count = 1
        key = record_key(dict(path=path, symbol=symbol, rule=rule, count=count))
        if rule in {"C901", "PLR0915"} and key in counts:
            raise ValueError("ambiguous duplicate lexical symbol")
        counts[key] += count
    return dict(counts)


def run_ruff(root, runner=subprocess.run):
    version = runner(["ruff", "--version"], capture_output=True, text=True, timeout=180)
    if version.returncode != 0 or version.stdout.strip() != f"ruff {RUFF_VERSION}":
        raise ValueError(f"cached Ruff {RUFF_VERSION} required")
    result = runner(
        ["ruff", "check", "--no-cache", "--config", str(root / "ruff.toml"),
         "--output-format", "json", "scripts", "tests"],
        cwd=root, capture_output=True, text=True, timeout=180,
    )
    if result.returncode not in {0, 1}:
        raise ValueError(f"Ruff tool failure (exit {result.returncode}): {result.stderr.strip()}")
    records = findings_from_json(result.stdout, root)
    if bool(records) != (result.returncode == 1):
        raise ValueError("Ruff exit status contradicts JSON findings")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_readability_gate.py")
        if suite.countTestCases() == 0:
            print("no readability tests discovered", file=sys.stderr)
            return 1
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        baseline = baseline_records(read_json((ROOT / "scripts/readability-baseline.json").read_text()))
        current = run_ruff(ROOT)
        errors = compare_records(current, baseline)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, subprocess.TimeoutExpired) as error:
        print(f"readability unavailable: {error}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"readability checked: {len(current)} baseline records; no new or increased findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
