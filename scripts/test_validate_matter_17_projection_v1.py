#!/usr/bin/env python3
"""Focused mutation controls for the Matter 1.7 projection ledger."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("matter_17_projection", ROOT / "scripts/validate_matter_17_projection_v1.py")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def rejects(document, label, mutate):
    candidate = copy.deepcopy(document)
    mutate(candidate)
    try:
        validator.validate(candidate)
    except ValueError:
        print(f"{label}: REJECTED")
        return
    raise AssertionError(f"{label}: accepted")


def main():
    document = validator.load(validator.LEDGER)
    validator.validate(document)
    print("baseline_exact_ledger: PASS")
    rejects(document, "missing_row", lambda d: d["rows"].pop())
    rejects(document, "service_as_projection_item", lambda d: d["rows"][0]["ref"].update(id="evse.service.evse"))
    rejects(document, "duplicate_row", lambda d: d["rows"].__setitem__(1, copy.deepcopy(d["rows"][0])))
    rejects(document, "unknown_reason_removed", lambda d: d["rows"][0].pop("reason"))
    position = next(index for index, row in enumerate(document["rows"]) if row["ref"] == validator.POSITIVE_REF)
    rejects(document, "pinned_device_type_drift", lambda d: d["rows"][position]["target"].update(device_type_id=1297))
    rejects(document, "target_version_drift", lambda d: d["target"].update(version="unversioned"))
    rejects(document, "operation_promoted", lambda d: d["rows"][-1].update(disposition="candidate_read_only_transformed_observation"))
    print("focused_mutations: 7 REJECTED")


if __name__ == "__main__":
    main()
