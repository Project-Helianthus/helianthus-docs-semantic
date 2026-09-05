#!/usr/bin/env python3
"""Mutation harness for the independent snapshot-vector identity checker."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_snapshot_vector_ids", ROOT / "scripts" / "check_snapshot_vector_ids.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load snapshot-vector checker")
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def vector(document: dict, vector_id: str) -> dict:
    return next(item for item in document["vectors"] if item["id"] == vector_id)


def encode(document: dict) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def execute(raw: str) -> str:
    with tempfile.TemporaryDirectory() as directory:
        candidate = Path(directory) / "acceptance-vectors.json"
        candidate.write_text(raw, encoding="utf-8")
        original = checker.VECTORS
        checker.VECTORS = candidate
        try:
            checker.main()
        except Exception as error:  # A checker rejection is the expected mutant result.
            return f"FAIL {type(error).__name__}: {error}"
        finally:
            checker.VECTORS = original
    return "PASS"


def main() -> None:
    raw = checker.VECTORS.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    cases: list[tuple[str, str, bool]] = [("baseline", raw, True)]

    placeholder = copy.deepcopy(parsed)
    vector(placeholder, "K-POS-019")["input"]["snapshot"]["snapshot_id"] = "snapshot:meter:10"
    cases.append(("placeholder_snapshot_id", encode(placeholder), False))

    wrong_digest = copy.deepcopy(parsed)
    vector(wrong_digest, "K-POS-025")["input"]["evaluation_view"]["evaluation_digest"] = "sha256:" + "0" * 64
    cases.append(("wrong_evaluation_digest", encode(wrong_digest), False))

    duplicate = raw.replace('"snapshot_id":', '"snapshot_id": "duplicate",\n        "snapshot_id":', 1)
    cases.append(("duplicate_json_member", duplicate, False))

    detached = copy.deepcopy(parsed)
    vector(detached, "K-NEG-057")["input"]["base_vector"] = "K-POS-024"
    cases.append(("detached_positive_base", encode(detached), False))

    false_redigest = copy.deepcopy(parsed)
    vector(false_redigest, "K-NEG-058")["input"]["recompute_evaluation_digest"] = False
    cases.append(("false_redigest", encode(false_redigest), False))

    altered_path = copy.deepcopy(parsed)
    vector(altered_path, "K-NEG-058")["input"]["mutation"]["path"] = "evaluation_view.revisions.identity"
    cases.append(("altered_mutation_path", encode(altered_path), False))

    altered_error = copy.deepcopy(parsed)
    vector(altered_error, "K-NEG-058")["expect"]["error_id"] = "digest_mismatch"
    cases.append(("altered_expected_error", encode(altered_error), False))

    unexpected: list[str] = []
    for name, candidate, expected_pass in cases:
        result = execute(candidate)
        observed_pass = result == "PASS"
        if observed_pass != expected_pass:
            unexpected.append(f"{name}: {result}")
        else:
            print(f"{name}: {'PASS' if observed_pass else 'REJECTED'}")
    if unexpected:
        raise AssertionError("; ".join(unexpected))


if __name__ == "__main__":
    main()
