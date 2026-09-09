#!/usr/bin/env python3
"""Mutation tests for the retained-observation v1 contract validator."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("retained_validator", ROOT / "scripts" / "validate_retained_observation_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load retained validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

def execute(document: dict, kernel_text: str | None = None) -> bool:
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "retained.json"
        fixture.write_text(json.dumps(document), encoding="utf-8")
        original_fixture, original_kernel = validator.FIXTURE, validator.KERNEL
        validator.FIXTURE = fixture
        if kernel_text is not None:
            candidate = Path(directory) / "kernel.md"
            candidate.write_text(kernel_text, encoding="utf-8")
            validator.KERNEL = candidate
        try:
            validator.main()
        except ValueError:
            return False
        finally:
            validator.FIXTURE, validator.KERNEL = original_fixture, original_kernel
    return True

def main() -> None:
    baseline = json.loads(validator.FIXTURE.read_text(encoding="utf-8"))
    kernel = validator.KERNEL.read_text(encoding="utf-8")
    mutated_axes = copy.deepcopy(baseline)
    mutated_axes["identity_axes"] = mutated_axes["identity_axes"][:-1]
    missing_expiry = kernel.replace("an expired record is absent even when no later publication\noccurred.", "an expired record may remain visible.", 1)
    missing_withdrawal = kernel.replace("it removes the current candidate and every matching retained\ninstance.", "it removes only the current candidate.", 1)
    selection = copy.deepcopy(baseline)
    selection["scenarios"][7]["expect"][1] = "error_id:invalid_value"
    tombstone = copy.deepcopy(baseline)
    tombstone["scenarios"][-1]["expect"][1] = "error_id:invalid_value"
    tombstone_mutation = copy.deepcopy(baseline)
    tombstone_mutation["scenarios"][-2]["mutation"] = "omit_tombstone_check"
    retirement_tombstone = copy.deepcopy(baseline)
    retirement_tombstone["scenarios"][-1]["input"]["source"]["source_epoch_id"] = "epoch:meter:2"
    missing_path = kernel.replace("Retained-path validation is separate from current-fact validation.", "Retained-path validation is unspecified.", 1)
    for name, document, kernel_text, expected in (
        ("baseline", baseline, None, True),
        ("identity_axes", mutated_axes, None, False),
        ("expiry", baseline, missing_expiry, False),
        ("withdrawal", baseline, missing_withdrawal, False),
        ("selection_error", selection, None, False),
        ("tombstone_error", tombstone, None, False),
        ("tombstone_mutation", tombstone_mutation, None, False),
        ("retirement_tombstone", retirement_tombstone, None, False),
        ("tombstone_path", baseline, missing_path, False),
    ):
        actual = execute(document, kernel_text)
        if actual != expected:
            raise AssertionError(f"{name}: expected {expected}, got {actual}")
        print(f"{name}: {'PASS' if actual else 'REJECTED'}")

if __name__ == "__main__":
    main()
