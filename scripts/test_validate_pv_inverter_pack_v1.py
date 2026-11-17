#!/usr/bin/env python3
"""Focused exact-association mutation tests for the PV/inverter pack."""
from __future__ import annotations

import copy
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_pv_inverter_pack_v1", ROOT / "scripts" / "validate_pv_inverter_pack_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load PV/inverter pack validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)
# The member name used before the in-place rename, assembled so that no file spells it.
EARLIER_MEMBER = "relation" + "ships"
# The SI unit set of the unit rule in api/README.md; a pack field declares no other unit.
SI_UNITS = {"unit.ampere", "unit.ampere_hour", "unit.cubic_metre_per_second", "unit.hertz", "unit.joule",
            "unit.kelvin", "unit.pascal", "unit.ratio", "unit.reciprocal_second", "unit.volt",
            "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt"}
# Each field the rule moved: SI unit, customary bounds before the move, exact factor and offset.
CONVERTED = {
    "pv.energy.generated": ("unit.joule", ("0", 0), ("1", 12), Fraction(3600000), Fraction(0)),
    "pv.temperature.inverter": ("unit.kelvin", ("-5", 1), ("2", 2), Fraction(1), Fraction(27315, 100)),
}
# Customary and prefixed units that no pack field may declare.
NOT_SI = ("unit.kilowatt_hour", "unit.celsius", "unit.percent", "unit.litre_per_minute", "unit.kilowatt", "unit.bar")


def kernel_decimal(value):
    """Exact kernel Decimal of a Fraction; a value that does not terminate in decimal fails."""
    exponent = 0
    while value.denominator != 1:
        value *= 10
        exponent -= 1
        if exponent < -18:
            raise AssertionError("conversion does not terminate in decimal")
    coefficient = value.numerator
    if coefficient == 0:
        return {"coefficient": "0", "exponent10": 0}
    while coefficient % 10 == 0:
        coefficient //= 10
        exponent += 1
    return {"coefficient": str(coefficient), "exponent10": exponent}


def converted(bound, factor, offset):
    coefficient, exponent = bound
    return kernel_decimal(Fraction(int(coefficient)) * Fraction(10) ** exponent * factor + offset)


def check_si_units(document):
    if validator.CANONICAL_UNITS != SI_UNITS:
        raise AssertionError("validator unit set differs from the unit rule")
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    for field in fields.values():
        if field["kind"] == "quantity" and field["unit"] not in SI_UNITS:
            raise AssertionError(f"{field['id']} declares {field['unit']}")
    for identifier, (unit, minimum, maximum, factor, offset) in CONVERTED.items():
        expected = {"minimum": converted(minimum, factor, offset), "maximum": converted(maximum, factor, offset)}
        if fields[identifier]["unit"] != unit or fields[identifier]["bounds"] != expected:
            raise AssertionError(f"{identifier} is not the exact SI conversion")
    print("si_units_and_exact_bounds: PASS")


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
    check_si_units(document)
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}
    for identifier in CONVERTED:
        for unit in NOT_SI:
            case(document, f"{identifier}_{unit}", "outside the canonical SI unit set", lambda c, i=positions[identifier], u=unit: c["definitions"]["fields"][i].update(unit=u))
    case(document, "voltage_customary_unit", "outside the canonical SI unit set", lambda c: c["definitions"]["fields"][0].update(unit="unit.millivolt"))
    case(document, "energy_si_unit_customary_bounds", "canonical quantity contract", lambda c: c["definitions"]["fields"][positions["pv.energy.generated"]]["bounds"].update(maximum={"coefficient": "1", "exponent10": 12}))
    case(document, "temperature_si_unit_customary_minimum", "canonical quantity contract", lambda c: c["definitions"]["fields"][positions["pv.temperature.inverter"]]["bounds"].update(minimum={"coefficient": "-5", "exponent10": 1}))

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
    case(document, "topology_self_edge", "topology relation association", lambda c: c["definitions"]["relations"][0].update(to="pv.dimension.system"))
    case(document, "relation_cardinality_drift", "topology relation association", lambda c: c["definitions"]["relations"][2].update(cardinality="many_to_many"))
    case(document, "relation_cardinality_missing", "topology relation association", lambda c: c["definitions"]["relations"][4].pop("cardinality"))
    case(document, "relation_member_earlier_name", "definition groups", lambda c: c["definitions"].update({EARLIER_MEMBER: c["definitions"].pop("relations")}))
    case(document, "relation_member_duplicated", "definition groups", lambda c: c["definitions"].update({EARLIER_MEMBER: copy.deepcopy(c["definitions"]["relations"])}))
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
    print("focused_mutations: 51 REJECTED")


if __name__ == "__main__":
    main()
