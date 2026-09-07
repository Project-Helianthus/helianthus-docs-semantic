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

def execute(document: dict, kernel_text: str | None = None) -> bool:
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "fork.json"
        fixture.write_text(json.dumps(document), encoding="utf-8")
        original_fixture, original_kernel = validator.FIXTURE, validator.KERNEL
        validator.FIXTURE = fixture
        if kernel_text is not None:
            candidate_kernel = Path(directory) / "kernel.md"
            candidate_kernel.write_text(kernel_text, encoding="utf-8")
            validator.KERNEL = candidate_kernel
        try:
            validator.main()
        except ValueError:
            return False
        finally:
            validator.FIXTURE, validator.KERNEL = original_fixture, original_kernel
    return True


def weaken_kernel(kernel: str, original: str, replacement: str) -> str:
    if kernel.count(original) != 1:
        raise AssertionError(f"expected exactly one stable clause: {original!r}")
    return kernel.replace(original, replacement, 1)

def main() -> None:
    baseline = json.loads(validator.FIXTURE.read_text())
    kernel = validator.KERNEL.read_text(encoding="utf-8")
    cases = [("baseline", baseline, None, True)]
    signature = copy.deepcopy(baseline)
    signature["signature"] = "func (k *PublicationKernel) Clone() (*PublicationKernel, error)"
    cases.append(("signature", signature, None, False))
    nil = copy.deepcopy(baseline)
    nil["nil_receiver"]["error_id"] = "sequence_conflict"
    cases.append(("nil_error", nil, None, False))
    lifecycle = copy.deepcopy(baseline)
    lifecycle["non_goals"].remove("lifecycle_replacement")
    cases.append(("lifecycle_non_goal", lifecycle, None, False))
    cursor = copy.deepcopy(baseline)
    cursor["scenarios"][1]["expect"].remove("same_source_epoch_generation")
    cases.append(("cursor_continuation", cursor, None, False))
    cases.extend((
        ("cursor_preservation", baseline, weaken_kernel(
            kernel,
            validator.COPIED_STATE_CLAUSE,
            validator.COPIED_STATE_CLAUSE.replace("publication cursors, ", ""),
        ), False),
        ("fence_preservation", baseline, weaken_kernel(
            kernel,
            validator.COPIED_STATE_CLAUSE,
            validator.COPIED_STATE_CLAUSE.replace("generation fences,\n", ""),
        ), False),
        ("map_slice_isolation", baseline, weaken_kernel(
            kernel,
            validator.NO_SHARED_MUTABLE_STORAGE_CLAUSE,
            "The source and fork MUST share no mutable snapshot, canonical-byte, or replay-result storage.",
        ), False),
    ))
    for name, document, kernel_text, expected in cases:
        actual = execute(document, kernel_text)
        if actual != expected:
            raise AssertionError(f"{name}: expected {expected}, got {actual}")
        print(f"{name}: {'PASS' if actual else 'REJECTED'}")


if __name__ == "__main__":
    main()
