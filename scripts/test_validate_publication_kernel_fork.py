#!/usr/bin/env python3
"""Mutation tests for the PublicationKernel fork contract validator."""
from __future__ import annotations
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fork_validator", ROOT / "scripts" / "validate_publication_kernel_fork.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load fork validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

def execute(document: dict) -> bool:
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "fork.json"
        fixture.write_text(json.dumps(document), encoding="utf-8")
        original = validator.FIXTURE
        validator.FIXTURE = fixture
        try:
            validator.main()
        except ValueError:
            return False
        finally:
            validator.FIXTURE = original
    return True

def main() -> None:
    baseline = json.loads(validator.FIXTURE.read_text())
    cases = [("baseline", baseline, True)]
    signature = copy.deepcopy(baseline)
    signature["signature"] = "func (k *PublicationKernel) Clone() (*PublicationKernel, error)"
    cases.append(("signature", signature, False))
    nil = copy.deepcopy(baseline)
    nil["nil_receiver"]["error_id"] = "sequence_conflict"
    cases.append(("nil_error", nil, False))
    lifecycle = copy.deepcopy(baseline)
    lifecycle["non_goals"].remove("lifecycle_replacement")
    cases.append(("lifecycle_non_goal", lifecycle, False))
    cursor = copy.deepcopy(baseline)
    cursor["scenarios"][1]["expect"].remove("same_source_epoch_generation")
    cases.append(("cursor_continuation", cursor, False))
    for name, document, expected in cases:
        actual = execute(document)
        if actual != expected:
            raise AssertionError(f"{name}: expected {expected}, got {actual}")
        print(f"{name}: {'PASS' if actual else 'REJECTED'}")

if __name__ == "__main__":
    main()
