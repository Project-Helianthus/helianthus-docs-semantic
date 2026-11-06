#!/usr/bin/env python3
"""Mutation tests for the retained-observation v1 contract validator."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("retained_validator", ROOT / "scripts" / "validate_retained_observation_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load retained validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

def execute(document: dict, kernel_text: str | None = None) -> bool:
    # Keep artifacts for review: no automatic removal under worker constraints.
    retained_root = ROOT / ".tmp" / "retained-validator"
    retained_root.mkdir(parents=True, exist_ok=True)
    directory = tempfile.mkdtemp(dir=retained_root)
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
    def scenario(document: dict, ident: str) -> dict:
        return next(item for item in document["scenarios"] if item["id"] == ident)
    for ident in ('RO-CAP-invalid_fence_restore', 'RO-CAP-invalid_empty_fence_restore'):
        row = scenario(baseline, ident)
        assert row['operation'] == 'structural_restore'
        assert row['input']['fences'] + row['input']['current_unfenced_tuples'] == 129
        assert row['expect']['result'] == 'bounds_exceeded'
        assert row['expect']['H'] == row['expect']['C'] == 0
        assert row['expect']['recovery_blocked'] is False
        assert 'empty_state' in row['expect']['unchanged']
    excess = scenario(baseline, 'RO-CAP-fence_excess')
    assert excess['input']['fences'] + excess['input']['current_unfenced_tuples'] == 128
    assert excess['input']['upserts'] == 20 and excess['expect']['recovery_blocked'] is False
    mutated_axes = copy.deepcopy(baseline)
    mutated_axes["identity_axes"] = mutated_axes["identity_axes"][:-1]
    missing_expiry = kernel.replace("an expired record is absent even when no later publication\noccurred.", "an expired record may remain visible.", 1)
    missing_withdrawal = kernel.replace("it removes the current candidate and every matching retained\ninstance.", "it removes only the current candidate.", 1)
    selection = copy.deepcopy(baseline)
    scenario(selection, "RO-NEG-002")["expect"][1] = "error_id:invalid_value"
    tombstone = copy.deepcopy(baseline)
    scenario(tombstone, "RO-NEG-006")["expect"][1] = "error_id:invalid_value"
    tombstone_mutation = copy.deepcopy(baseline)
    scenario(tombstone_mutation, "RO-NEG-005")["mutation"] = "omit_tombstone_check"
    retirement_tombstone = copy.deepcopy(baseline)
    scenario(retirement_tombstone, "RO-NEG-006")["input"]["source"]["source_epoch_id"] = "epoch:meter:2"
    sequential = copy.deepcopy(baseline)
    scenario(sequential, "RO-POS-007")["input"]["binding"]["state"] = "fenced"
    cross_source = copy.deepcopy(baseline)
    scenario(cross_source, "RO-NEG-007")["input"]["retirement_source_id"] = "source:meter"
    count_drift = copy.deepcopy(baseline)
    count_drift["scenario_counts"]["total"] += 1
    omitted_vector = copy.deepcopy(baseline)
    omitted_vector["scenarios"] = [item for item in omitted_vector["scenarios"] if item["id"] != "RO-POS-008"]
    missing_path = kernel.replace("Retained-path validation is separate from current-fact validation.", "Retained-path validation is unspecified.", 1)
    # Vary every declared identity axis independently. These catch omission,
    # reordering or aliasing of candidate ID, revision, JCS key, binding, epoch,
    # and generation in the contract identity declaration, not runtime identity.
    for axis in validator.AXES:
        document = copy.deepcopy(baseline)
        document["identity_axes"][validator.AXES.index(axis)] = "omitted:" + axis
        if execute(document):
            raise AssertionError(f"identity axis accepted: {axis}")
        print(f"identity axis {axis}: REJECTED")
    # Mutate every input/output member: counts catch off-by-one, refresh debt,
    # inferred debt, pruning/clock, fence headroom and restore/replay precedence
    # contract drift. Every unchanged-state axis must survive refusal and replay.
    for ident in validator.CAPACITY_CASES:
        for section in ("input", "expect"):
            for field, value in scenario(baseline, ident)[section].items():
                document = copy.deepcopy(baseline)
                replacement = (not value if isinstance(value, bool) else
                               value + 1 if isinstance(value, int) else
                               value + ["unexpected"] if isinstance(value, list) else
                               value + ":mutant")
                scenario(document, ident)[section][field] = replacement
                if execute(document):
                    raise AssertionError(f"capacity mutant accepted: {ident}.{section}.{field}")
        for index, group in enumerate(scenario(baseline, ident)["input"].get("path_groups", [])):
            for field, value in group.items():
                document = copy.deepcopy(baseline)
                scenario(document, ident)["input"]["path_groups"][index][field] = value + 1 if isinstance(value, int) else value + ":mutant"
                if execute(document):
                    raise AssertionError(f"mixed path accepted: {index}.{field}")
        unchanged = scenario(baseline, ident)["expect"]["unchanged"]
        for field in unchanged:
            document = copy.deepcopy(baseline)
            scenario(document, ident)["expect"]["unchanged"].remove(field)
            if execute(document):
                raise AssertionError(f"non-advance mutant accepted: {ident}.{field}")
        print(f"{ident}: all input/output and non-advance mutants REJECTED")
    for clause in validator.CLAUSES:
        if execute(baseline, kernel.replace(clause, "omitted normative clause", 1)):
            raise AssertionError(f"contract clause mutant accepted: {clause}")
    for name, document, kernel_text, expected in (
        ("baseline", baseline, None, True),
        ("identity_axes", mutated_axes, None, False),
        ("expiry", baseline, missing_expiry, False),
        ("withdrawal", baseline, missing_withdrawal, False),
        ("selection_error", selection, None, False),
        ("tombstone_error", tombstone, None, False),
        ("tombstone_mutation", tombstone_mutation, None, False),
        ("retirement_tombstone", retirement_tombstone, None, False),
        ("sequential_retirement", sequential, None, False),
        ("cross_source_retirement", cross_source, None, False),
        ("declared_count_drift", count_drift, None, False),
        ("omitted_sequential_vector", omitted_vector, None, False),
        ("tombstone_path", baseline, missing_path, False),
    ):
        actual = execute(document, kernel_text)
        if actual != expected:
            raise AssertionError(f"{name}: expected {expected}, got {actual}")
        print(f"{name}: {'PASS' if actual else 'REJECTED'}")

if __name__ == "__main__":
    main()
