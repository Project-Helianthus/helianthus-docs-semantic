#!/usr/bin/env python3
"""Focused RED-first mutation controls for the EVSE v1 catalog."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_evse_pack_v1", ROOT / "scripts" / "validate_evse_pack_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load EVSE validator")
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


def case(document, name, expected, mutate):
    candidate = copy.deepcopy(document)
    mutate(candidate["catalog"])
    reject(candidate, expected)
    print(f"{name}: REJECTED")


def main():
    document = validator.load_document(validator.VECTORS)
    validator.validate_document(document)
    validator.decimal_less({"coefficient": "9007199254740992", "exponent10": -18}, {"coefficient": "9007199254740993", "exponent10": -18}) or (_ for _ in ()).throw(AssertionError("exact Decimal comparison"))
    print("baseline_exact_chain: PASS")
    print("close_decimal_interval: PASS")
    case(document, "wrong_pack", "exact PackRef", lambda c: c["pack"].update(id="helianthus.pack.pv"))
    case(document, "infrastructure_accepted", "five-domain catalog", lambda c: c["domain_catalog"][4].update(state="accepted"))
    case(document, "field_bound_drift", "quantity contract", lambda c: c["definitions"]["fields"][0]["bounds"].update(maximum={"coefficient":"9","exponent10":2}))
    case(document, "field_dimension_drift", "noncanonical kind", lambda c: c["definitions"]["fields"][0].update(dimension="evse.dimension.evse"))
    case(document, "relative_state_promoted", "native mapping boundary", lambda c: c["candidate_mappings"][0].update(relative_or_unknown_state="absolute_allocation"))
    case(document, "allocated_actual_collapsed", "native mapping boundary", lambda c: c["candidate_mappings"][0].update(actual_current="native_candidate"))
    case(document, "tesla_live_authority", "native mapping boundary", lambda c: c["candidate_mappings"][0].update(live_authority=True))
    case(document, "tesla_sender", "native mapping boundary", lambda c: c["candidate_mappings"][0].update(sender="native"))
    case(document, "tesla_control_route", "native mapping boundary", lambda c: c["candidate_mappings"][0].update(control_route="fbe0"))
    case(document, "eebus_conformance", "native mapping boundary", lambda c: c["candidate_mappings"][1].update(state="qualified"))
    case(document, "matter_conformance", "native mapping boundary", lambda c: c["candidate_mappings"][2].update(qualification="conformant"))
    case(document, "relationship_cardinality", "relationship association", lambda c: c["definitions"]["relationships"][3].update(cardinality="one_to_one"))
    case(document, "operation_precondition", "operation safety", lambda c: c["definitions"]["operations"][0].update(preconditions=["exact_route"]))
    case(document, "operation_retry", "operation safety", lambda c: c["definitions"]["operations"][0].update(retry="retry"))
    case(document, "effect_crosswire", "effect association", lambda c: c["definitions"]["effect_rules"][0].update(fact="evse.limit.actual_current"))
    case(document, "portal_authority", "Portal operation", lambda c: c["definitions"]["portal_contributions"][5].update(admission="always"))
    case(document, "counter_weakened", "counter policy", lambda c: c["counter_policy"].update(decrease="infer_reset"))
    case(document, "lifecycle_weakened", "lifecycle axes", lambda c: c["lifecycle_axes"].remove("generation_fencing"))
    print("focused_mutations: 18 REJECTED")


if __name__ == "__main__":
    main()
