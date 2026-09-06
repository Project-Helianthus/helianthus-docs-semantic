#!/usr/bin/env python3
"""Focused RED-first mutation controls for infrastructure v1."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_infrastructure_pack_v1", ROOT / "scripts" / "validate_infrastructure_pack_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load infrastructure validator")
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
    validator.less({"coefficient": "9007199254740992", "exponent10": -18}, {"coefficient": "9007199254740993", "exponent10": -18}) or (_ for _ in ()).throw(AssertionError("exact Decimal comparison"))
    print("baseline_exact_chain: PASS")
    print("close_decimal_interval: PASS")
    case(document, "wrong_pack", "exact PackRef", lambda c: c["pack"].update(id="helianthus.pack.evse"))
    case(document, "evse_downgraded", "five-domain catalog", lambda c: c["domain_catalog"][3].update(state="follow_on"))
    case(document, "bound_drift", "quantity contract", lambda c: c["definitions"]["fields"][0]["bounds"].update(maximum={"coefficient":"9", "exponent10":2}))
    case(document, "dimension_drift", "noncanonical kind", lambda c: c["definitions"]["fields"][0].update(dimension="infrastructure.dimension.site"))
    case(document, "topology_drift", "relationship association", lambda c: c["definitions"]["relationships"][2].update(cardinality="one_to_one"))
    case(document, "capability_drift", "capability association", lambda c: c["definitions"]["capabilities"][0].update(service="infrastructure.service.meter"))
    case(document, "operation_published", "read-only operation boundary", lambda c: c["definitions"].update(operations=[{"id":"infrastructure.operation.open_breaker"}]))
    case(document, "breaker_actuation_published", "read-only operation boundary", lambda c: c["read_only_operation_boundary"].update(breaker_actuation="published"))
    case(document, "portal_authority", "Portal read association", lambda c: c["definitions"]["portal_contributions"][0].update(kind="operation"))
    case(document, "ebus_live", "native mapping boundary", lambda c: c["candidate_mappings"][0].update(live_authority=True))
    case(document, "modbus_promoted", "native mapping boundary", lambda c: c["candidate_mappings"][1].update(state="qualified"))
    case(document, "modbus_generic_candidate", "native mapping boundary", lambda c: c["candidate_mappings"][1].update(state="candidate"))
    case(document, "eebus_conformance", "native mapping boundary", lambda c: c["candidate_mappings"][2].update(state="qualified"))
    case(document, "matter_conformance", "native mapping boundary", lambda c: c["candidate_mappings"][3].update(qualification="conformant"))
    case(document, "counter_weakened", "counter policy", lambda c: c["counter_policy"].update(decrease="infer_reset"))
    case(document, "lifecycle_weakened", "lifecycle axes", lambda c: c["lifecycle_axes"].remove("generation_fencing"))
    case(document, "loss_omitted", "projection-loss coverage", lambda c: c["loss_dispositions"].remove("aggregation"))
    print("focused_mutations: 17 REJECTED")


if __name__ == "__main__":
    main()
