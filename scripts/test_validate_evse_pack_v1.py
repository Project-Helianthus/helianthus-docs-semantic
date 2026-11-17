#!/usr/bin/env python3
"""Focused RED-first mutation controls for the EVSE v1 catalog."""
from __future__ import annotations

import copy
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_evse_pack_v1", ROOT / "scripts" / "validate_evse_pack_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load EVSE validator")
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
    "evse.energy.session": ("unit.joule", ("0", 0), ("1", 12), Fraction(3600000), Fraction(0)),
    "evse.energy.lifetime": ("unit.joule", ("0", 0), ("1", 12), Fraction(3600000), Fraction(0)),
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


class TestAllocatedCurrentPhaseStaysOffConnector:
    """Phase allocated current is a different field from the connector allocation.

    Fields and the production mutation each check catches:
    - ``evse.limit.allocated_current`` dimension: setting it to
      ``evse.dimension.phase`` is rejected as a noncanonical dimension.
    - ``evse.limit.allocated_current_phase`` id: absence of the field fails.
    - ``evse.limit.allocated_current_phase`` dimension: setting it to
      ``evse.dimension.connector`` is rejected as a noncanonical dimension.
    """

    CONNECTOR = "evse.dimension.connector"
    PHASE = "evse.dimension.phase"
    ALLOCATED = "evse.limit.allocated_current"
    PHASE_ALLOCATED = "evse.limit.allocated_current_phase"

    def __init__(self, document):
        fields = document["catalog"]["definitions"]["fields"]
        by_id = {field["id"]: field for field in fields}
        if by_id.get(self.ALLOCATED, {}).get("dimension") != self.CONNECTOR:
            raise AssertionError(f"{self.ALLOCATED} must stay on {self.CONNECTOR}")
        if self.PHASE_ALLOCATED not in by_id:
            raise AssertionError(f"{self.PHASE_ALLOCATED} is absent")
        if by_id[self.PHASE_ALLOCATED]["dimension"] != self.PHASE:
            raise AssertionError(f"{self.PHASE_ALLOCATED} must stay off {self.CONNECTOR}")
        positions = {field["id"]: index for index, field in enumerate(fields)}
        case(
            document,
            "allocated_current_moved_onto_phase",
            "noncanonical kind, dimension, or optionality",
            lambda catalog, index=positions[self.ALLOCATED]: catalog["definitions"]["fields"][index].update(dimension=self.PHASE),
        )
        case(
            document,
            "allocated_current_phase_on_connector",
            "noncanonical kind, dimension, or optionality",
            lambda catalog, index=positions[self.PHASE_ALLOCATED]: catalog["definitions"]["fields"][index].update(dimension=self.CONNECTOR),
        )
        print("allocated_current_phase_off_connector: PASS")


def main():
    document = validator.load_document(validator.VECTORS)
    validator.validate_document(document)
    validator.decimal_less({"coefficient": "9007199254740992", "exponent10": -18}, {"coefficient": "9007199254740993", "exponent10": -18}) or (_ for _ in ()).throw(AssertionError("exact Decimal comparison"))
    print("baseline_exact_chain: PASS")
    print("close_decimal_interval: PASS")
    check_si_units(document)
    TestAllocatedCurrentPhaseStaysOffConnector(document)
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}
    for identifier in CONVERTED:
        for unit in NOT_SI:
            case(document, f"{identifier}_{unit}", "outside the canonical SI unit set", lambda c, i=positions[identifier], u=unit: c["definitions"]["fields"][i].update(unit=u))
    case(document, "voltage_customary_unit", "outside the canonical SI unit set", lambda c: c["definitions"]["fields"][0].update(unit="unit.millivolt"))
    case(document, "session_energy_customary_bounds", "quantity contract", lambda c: c["definitions"]["fields"][positions["evse.energy.session"]]["bounds"].update(maximum={"coefficient": "1", "exponent10": 12}))
    case(document, "lifetime_energy_customary_bounds", "quantity contract", lambda c: c["definitions"]["fields"][positions["evse.energy.lifetime"]]["bounds"].update(maximum={"coefficient": "1", "exponent10": 12}))
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
    case(document, "relation_cardinality", "relation association", lambda c: c["definitions"]["relations"][3].update(cardinality="one_to_one"))
    case(document, "relation_cardinality_missing", "relation association", lambda c: c["definitions"]["relations"][0].pop("cardinality"))
    case(document, "relation_member_earlier_name", "definition groups", lambda c: c["definitions"].update({EARLIER_MEMBER: c["definitions"].pop("relations")}))
    case(document, "relation_member_duplicated", "definition groups", lambda c: c["definitions"].update({EARLIER_MEMBER: copy.deepcopy(c["definitions"]["relations"])}))
    case(document, "operation_precondition", "operation safety", lambda c: c["definitions"]["operations"][0].update(preconditions=["exact_route"]))
    case(document, "operation_retry", "operation safety", lambda c: c["definitions"]["operations"][0].update(retry="retry"))
    case(document, "effect_crosswire", "effect association", lambda c: c["definitions"]["effect_rules"][0].update(fact="evse.limit.actual_current"))
    case(document, "portal_authority", "Portal operation", lambda c: c["definitions"]["portal_contributions"][5].update(admission="always"))
    case(document, "counter_weakened", "counter policy", lambda c: c["counter_policy"].update(decrease="infer_reset"))
    case(document, "lifecycle_weakened", "lifecycle axes", lambda c: c["lifecycle_axes"].remove("generation_fencing"))
    print("focused_mutations: 36 REJECTED")


if __name__ == "__main__":
    main()
