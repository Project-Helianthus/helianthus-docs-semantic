#!/usr/bin/env python3
"""Mutation tests for the thermal/HVAC pack documentation validator."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_thermal_hvac_pack_v1",
    ROOT / "scripts" / "validate_thermal_hvac_pack_v1.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load thermal/HVAC pack validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def reject(document: dict, expected: str) -> None:
    try:
        validator.validate_document(document)
    except ValueError as error:
        if expected not in str(error):
            raise AssertionError(f"expected {expected!r}, got {error!s}") from error
        return
    raise AssertionError(f"expected rejection containing {expected!r}")


def main() -> None:
    document = validator.load_document(validator.VECTORS)
    validator.validate_document(document)
    catalog = document["catalog"]

    duplicate = copy.deepcopy(document)
    duplicate["catalog"]["definitions"]["fields"].append(
        copy.deepcopy(catalog["definitions"]["fields"][0])
    )
    reject(duplicate, "duplicate definition ID")

    wrong_pack = copy.deepcopy(document)
    wrong_pack["catalog"]["pack"]["id"] = "helianthus.pack.pv"
    reject(wrong_pack, "exact PackRef")

    missing_follow_on = copy.deepcopy(document)
    missing_follow_on["catalog"]["domain_catalog"] = missing_follow_on["catalog"][
        "domain_catalog"
    ][:-1]
    reject(missing_follow_on, "five-domain catalog")

    missing_effect = copy.deepcopy(document)
    missing_effect["catalog"]["definitions"]["effect_rules"] = []
    reject(missing_effect, "effect rule")

    invalid_bounds = copy.deepcopy(document)
    invalid_bounds["catalog"]["definitions"]["fields"][0]["bounds"] = {
        "minimum": {"coefficient": "3", "exponent10": 1},
        "maximum": {"coefficient": "1", "exponent10": 1},
    }
    reject(invalid_bounds, "unordered numeric bounds")

    eebus_normative = copy.deepcopy(document)
    eebus_normative["catalog"]["candidate_mappings"][2]["state"] = "qualified"
    reject(eebus_normative, "eeBUS mapping")

    non_kernel_kind = copy.deepcopy(document)
    non_kernel_kind["catalog"]["definitions"]["fields"][0]["kind"] = "decimal"
    reject(non_kernel_kind, "non-kernel ValueKind")

    missing_owner = copy.deepcopy(document)
    del missing_owner["catalog"]["definitions"]["services"][0]["ref"]
    reject(missing_owner, "DefinitionRef owner/version")

    arbitrary_extension = copy.deepcopy(document)
    extension = copy.deepcopy(arbitrary_extension["catalog"]["definitions"]["fields"][0])
    extension["id"] = "thermal.vendor.extension"
    extension["ref"]["id"] = "thermal.vendor.extension"
    extension["order"] = 140
    arbitrary_extension["catalog"]["definitions"]["fields"].append(extension)
    reject(arbitrary_extension, "field catalog")

    arbitrary_schedule = copy.deepcopy(document)
    schedule = copy.deepcopy(arbitrary_schedule["catalog"]["definitions"]["fields"][0])
    schedule["id"] = "thermal.schedule.summary"
    schedule["ref"]["id"] = "thermal.schedule.summary"
    schedule["order"] = 140
    arbitrary_schedule["catalog"]["definitions"]["fields"].append(schedule)
    reject(arbitrary_schedule, "field catalog")

    missing_policy = copy.deepcopy(document)
    del missing_policy["catalog"]["publication_withdrawal_policy"]
    reject(missing_policy, "publication/withdrawal policy")

    missing_read_field = copy.deepcopy(document)
    missing_read_field["catalog"]["definitions"]["portal_contributions"][0]["fields"].remove(
        "thermal.measurement.power"
    )
    reject(missing_read_field, "read descriptor field coverage")

    missing_stage = copy.deepcopy(document)
    missing_stage["catalog"]["definitions"]["operations"][0]["stages"].pop()
    reject(missing_stage, "operation stages/outcomes")

    bad_constraint = copy.deepcopy(document)
    bad_constraint["catalog"]["definitions"]["capabilities"][5]["constraints"] = []
    reject(bad_constraint, "operation/capability constraint mismatch")

    print("baseline: PASS")
    print("duplicate_definition: REJECTED")
    print("wrong_pack: REJECTED")
    print("missing_follow_on: REJECTED")
    print("missing_effect: REJECTED")
    print("invalid_bounds: REJECTED")
    print("eebus_normative: REJECTED")
    print("non_kernel_kind: REJECTED")
    print("missing_owner: REJECTED")
    print("arbitrary_extension: REJECTED")
    print("arbitrary_schedule: REJECTED")
    print("missing_policy: REJECTED")
    print("missing_read_field: REJECTED")
    print("missing_stage: REJECTED")
    print("bad_constraint: REJECTED")


if __name__ == "__main__":
    main()
