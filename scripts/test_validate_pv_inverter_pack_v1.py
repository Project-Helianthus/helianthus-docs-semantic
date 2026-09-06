#!/usr/bin/env python3
"""Focused mutation tests for the PV/inverter pack documentation validator."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_pv_inverter_pack_v1", ROOT / "scripts" / "validate_pv_inverter_pack_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load PV/inverter pack validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def reject(document, expected):
    try:
        validator.validate_document(document)
    except ValueError as error:
        if expected not in str(error):
            raise AssertionError(f"expected {expected!r}, got {error!s}") from error
        return
    raise AssertionError(f"expected rejection containing {expected!r}")


def main():
    document = validator.load_document(validator.VECTORS)
    validator.validate_document(document)
    cases = []

    wrong_pack = copy.deepcopy(document)
    wrong_pack["catalog"]["pack"]["id"] = "helianthus.pack.thermal"
    cases.append(("wrong_pack", wrong_pack, "exact PackRef"))

    no_follow_on = copy.deepcopy(document)
    no_follow_on["catalog"]["domain_catalog"] = no_follow_on["catalog"]["domain_catalog"][:-1]
    cases.append(("missing_follow_on", no_follow_on, "five-domain catalog"))

    no_phase_relation = copy.deepcopy(document)
    no_phase_relation["catalog"]["definitions"]["relationships"] = no_phase_relation["catalog"]["definitions"]["relationships"][:-1]
    cases.append(("missing_phase_relation", no_phase_relation, "topology relationship catalog"))

    generic_enable = copy.deepcopy(document)
    generic_enable["catalog"]["definitions"]["operations"][0]["id"] = "pv.operation.enable"
    generic_enable["catalog"]["definitions"]["operations"][0]["ref"]["id"] = "pv.operation.enable"
    cases.append(("generic_enable", generic_enable, "operation catalog"))

    unadmitted = copy.deepcopy(document)
    unadmitted["catalog"]["definitions"]["operations"][0]["preconditions"][-1] = "optional_authority"
    cases.append(("unadmitted_operation", unadmitted, "operation lacks admission/readback"))

    growatt_qualified = copy.deepcopy(document)
    growatt_qualified["catalog"]["candidate_mappings"][0]["state"] = "qualified"
    cases.append(("growatt_qualified", growatt_qualified, "Growatt mapping"))

    tesla_qualified = copy.deepcopy(document)
    tesla_qualified["catalog"]["candidate_mappings"][1]["state"] = "qualified"
    cases.append(("tesla_qualified", tesla_qualified, "Tesla mapping"))

    eebus_normative = copy.deepcopy(document)
    eebus_normative["catalog"]["candidate_mappings"][2]["state"] = "candidate"
    cases.append(("eebus_normative", eebus_normative, "eeBUS mapping"))

    no_counter = copy.deepcopy(document)
    del no_counter["catalog"]["counter_policy"]
    cases.append(("missing_counter_policy", no_counter, "counter policy"))

    no_portal_field = copy.deepcopy(document)
    no_portal_field["catalog"]["definitions"]["portal_contributions"][1]["fields"].remove("pv.status.fault")
    cases.append(("missing_portal_field", no_portal_field, "read descriptor field coverage"))

    for name, candidate, expected in cases:
        reject(candidate, expected)
        print(f"{name}: REJECTED")
    print("baseline: PASS")


if __name__ == "__main__":
    main()
