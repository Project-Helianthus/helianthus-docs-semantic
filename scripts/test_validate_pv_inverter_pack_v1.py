#!/usr/bin/env python3
"""Focused exact-association mutation tests for the PV/inverter pack."""
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


def case(document, name, expected, mutate):
    candidate = copy.deepcopy(document)
    mutate(candidate["catalog"])
    reject(candidate, expected)
    print(f"{name}: REJECTED")


def main():
    document = validator.load_document(validator.VECTORS)
    validator.validate_document(document)
    validator.decimal_less({"coefficient": "9007199254740992", "exponent10": -18}, {"coefficient": "9007199254740993", "exponent10": -18}) or (_ for _ in ()).throw(AssertionError("exact close Decimal comparison"))
    print("baseline_exact_chain: PASS")
    print("close_decimal_interval: PASS")

    case(document, "wrong_pack", "exact PackRef", lambda c: c["pack"].update(id="helianthus.pack.thermal"))
    case(document, "missing_follow_on", "five-domain catalog", lambda c: c["domain_catalog"].pop())
    case(document, "storage_bms_downgrade", "five-domain catalog", lambda c: c["domain_catalog"][2].update(state="follow_on"))
    case(document, "retyped_voltage", "field has noncanonical kind", lambda c: c["definitions"]["fields"][0].update(kind="symbol", symbols=["pv.status.operating.idle"]))
    case(document, "voltage_wrong_optional", "field has noncanonical kind", lambda c: c["definitions"]["fields"][0].update(optional=False))
    case(document, "boolean_decimal_exponent", "canonical kernel Decimal", lambda c: c["definitions"]["fields"][0]["bounds"]["maximum"].update(exponent10=True))
    case(document, "dc_voltage_exact_minimum", "canonical quantity contract", lambda c: c["definitions"]["fields"][0]["bounds"].update(minimum={"coefficient":"-99","exponent10":0}))
    case(document, "ac_frequency_exact_maximum", "canonical quantity contract", lambda c: c["definitions"]["fields"][6]["bounds"].update(maximum={"coefficient":"999","exponent10":0}))
    case(document, "retained_limit_exact_maximum", "canonical quantity contract", lambda c: c["definitions"]["fields"][10]["bounds"].update(maximum={"coefficient":"2","exponent10":7}))
    case(document, "wrong_canonical_unit", "canonical quantity contract", lambda c: c["definitions"]["fields"][0].update(unit="unit.watt"))
    case(document, "duplicate_field_order", "fields noncanonical order", lambda c: c["definitions"]["fields"][1].update(order=10))
    case(document, "duplicate_symbol", "canonical symbol contract", lambda c: c["definitions"]["fields"][12].update(symbols=["pv.status.operating.idle", "pv.status.operating.idle"]))
    case(document, "nul_symbol", "canonical symbol contract", lambda c: c["definitions"]["fields"][12].update(symbols=["pv.status.operating.generating\u0000", "pv.status.operating.idle", "pv.status.operating.standby"]))
    case(document, "availability_symbol_reintroduced", "fields catalog", lambda c: c["definitions"]["fields"].append({"id":"pv.status.availability","ref":{"pack":validator.PACK,"id":"pv.status.availability","version":"1.0.0"},"kind":"symbol","dimension":"pv.dimension.inverter","symbols":["pv.status.availability.available"],"optional":True,"order":230}))
    case(document, "readiness_conflates_unavailable", "canonical symbol contract", lambda c: c["definitions"]["fields"][12].update(symbols=["pv.status.operating.generating", "pv.status.operating.idle", "pv.status.operating.unavailable"]))
    case(document, "availability_policy_conflated", "availability policy", lambda c: c["availability_policy"].update(effective_availability="pv.status.operating"))
    case(document, "topology_self_edge", "topology relationship association", lambda c: c["definitions"]["relationships"][0].update(to="pv.dimension.system"))
    case(document, "phase_service_system_dimension", "service dimension association", lambda c: c["definitions"]["services"][5].update(fact_key_dimension="pv.dimension.system"))
    case(document, "capability_cross_service", "capability association", lambda c: c["definitions"]["capabilities"][6].update(service="pv.service.system"))
    case(document, "operation_cross_capability", "operation association", lambda c: c["definitions"]["operations"][0].update(capability="pv.capability.set_export_limit"))
    case(document, "operation_wrong_argument", "operation association", lambda c: c["definitions"]["operations"][0].update(arguments=["pv.limit.export_power"], argument_constraints=["pv.limit.export_power"]))
    case(document, "cross_operation_effect", "operation association", lambda c: c["definitions"]["operations"][0].update(effect_rule="pv.effect.set_export_limit"))
    case(document, "wrong_effect_fact", "effect association", lambda c: c["definitions"]["effect_rules"][0].update(fact="pv.status.fault"))
    case(document, "effect_cross_operation", "effect association", lambda c: c["definitions"]["effect_rules"][0].update(operation="pv.operation.set_export_limit"))
    case(document, "wrong_portal_operation", "Portal operation association", lambda c: c["definitions"]["portal_contributions"][6].update(operation="pv.operation.set_export_limit"))
    case(document, "missing_portal_field", "Portal read association", lambda c: c["definitions"]["portal_contributions"][1]["fields"].remove("pv.status.fault"))
    case(document, "wrong_portal_read_service", "Portal read association", lambda c: c["definitions"]["portal_contributions"][1].update(service="pv.service.system"))
    case(document, "growatt_wrong_owner", "native mapping boundary", lambda c: c["candidate_mappings"][0].update(native_owner="helianthus-semreg"))
    case(document, "mapping_missing_loss", "native mapping boundary", lambda c: c["candidate_mappings"][0].pop("loss"))
    case(document, "mapping_wrong_source_ref", "native mapping boundary", lambda c: c["candidate_mappings"][1].update(source_refs=["growatt_docs_modbus"]))
    case(document, "extra_normative_mapping", "native mapping boundary", lambda c: c["candidate_mappings"].append({"id":"pv.mapping.extra","native_owner":"helianthus-semreg","source_refs":[],"state":"normative","qualification":"qualified","loss":"none"}))
    case(document, "tesla_provenance_reintroduced", "pinned public inputs", lambda c: c["inputs"][4].update(id="tesla_docs_modbus", revision="d16ff91ff808803fa31c67a6a10eb2a4faa70937"))
    print("focused_mutations: 32 REJECTED")


if __name__ == "__main__":
    main()
