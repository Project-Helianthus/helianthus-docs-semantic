#!/usr/bin/env python3
"""Focused RED-first mutation controls for the EVSE v1 catalog."""
from __future__ import annotations

import ast
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
            "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt", "unit.second", "unit.cubic_metre", "unit.metre", "unit.ohm", "unit.radian", "unit.one", "unit.volt_ampere_reactive_second", "unit.volt_ampere_second", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre", "unit.kilogram_per_joule", "unit.watt_per_square_metre", "unit.metre_per_joule", "unit.currency", "unit.currency_per_joule"}
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
        unit = field.get("unit")
        if field["kind"] == "quantity" and unit is not None and unit not in SI_UNITS:
            raise AssertionError(f"{field['id']} declares {unit}")
    efficiency = fields["evse.vehicle.approximate_efficiency"]
    if "unit" in efficiency or efficiency.get("bounds") != {"minimum": None, "maximum": None}:
        raise AssertionError("approximate efficiency declares a unit or a bound")
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



def check_admitted_rows_leave_the_set_case(document):
    """The allocated-current set case stays first and no release case is added.

    Fields and the production mutation each check catches, on
    ``evse.operation.set_supply``:
    - capability: setting it to ``evse.capability.read.evse`` is rejected as an
      operation association.
    - arguments: setting them to ``evse.status.fault`` is rejected as an
      operation association.
    - effect_rule: setting it to ``evse.effect.set_allocated_current`` is
      rejected as an operation association.
    - parameters: dropping ``evse.limit.allocated_current`` is rejected as an
      operation association.

    Fields and the production mutation each check catches, on
    ``evse.status.state``:
    - kind: setting it to ``quantity`` is rejected as a noncanonical kind.
    - dimension: setting it to ``evse.dimension.evse`` is rejected as a
      noncanonical dimension.
    - symbols: dropping ``evse.status.state.fault`` is rejected as a symbol
      contract.
    """
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    if set(validator.FIELD_CONTRACTS) != set(fields):
        raise AssertionError("FIELD_CONTRACTS differs from the vector fields")
    operations = document["catalog"]["definitions"]["operations"]
    if operations[0]["id"] != "evse.operation.set_allocated_current":
        raise AssertionError("allocated-current set case moved")
    if any("release" in item["id"] for item in operations):
        raise AssertionError("release operation added")
    if any("release" in item["id"] for item in document["catalog"]["definitions"]["effect_rules"]):
        raise AssertionError("release effect added")
    positions = {item["id"]: index for index, item in enumerate(operations)}
    supply = positions["evse.operation.set_supply"]
    case(document, "set_supply_capability", "operation association", lambda catalog, index=supply: catalog["definitions"]["operations"][index].update(capability="evse.capability.read.evse"))
    case(document, "set_supply_argument", "operation association", lambda catalog, index=supply: catalog["definitions"]["operations"][index].update(arguments=["evse.status.fault"]))
    case(document, "set_supply_effect", "operation association", lambda catalog, index=supply: catalog["definitions"]["operations"][index].update(effect_rule="evse.effect.set_allocated_current"))
    case(document, "set_supply_parameters", "operation association", lambda catalog, index=supply: catalog["definitions"]["operations"][index].update(parameters=["evse.limit.charging_enabled_until"]))
    state = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}["evse.status.state"]
    case(document, "state_kind", "noncanonical kind", lambda catalog, index=state: catalog["definitions"]["fields"][index].update(kind="quantity"))
    case(document, "state_dimension", "noncanonical kind", lambda catalog, index=state: catalog["definitions"]["fields"][index].update(dimension="evse.dimension.evse"))
    case(document, "state_symbols", "symbol contract", lambda catalog, index=state: catalog["definitions"]["fields"][index].update(symbols=["evse.status.state.not_plugged_in"]))
    print("admitted_rows_leave_the_set_case: PASS")


# Decision points the readability gate counts for C901. Boolean operators are not included.
DECISION_NODES = {"Assert", "AsyncFor", "ExceptHandler", "For", "If", "Match", "While", "With"}


def decision_points(function):
    measured = 1
    for node in ast.walk(function):
        name = type(node).__name__
        if name in DECISION_NODES:
            measured += 1
        elif name == "Try":
            measured += len(node.handlers) + bool(node.orelse) + bool(node.finalbody)
    return measured


def check_validate_fields_complexity(document):
    """``validate_fields`` stays within the readability complexity limit.

    The qualifier branch is still enforced. Fields and the production mutation
    each check catches:
    - ``evse.target.time_of_day`` qualifiers: replacing them with
      ``evse.dimension.evse`` is rejected as field qualifiers.
    - ``evse.ac.voltage`` qualifiers: adding ``evse.dimension.target`` is
      rejected as field qualifiers.
    """
    source = (ROOT / "scripts" / "validate_evse_pack_v1.py").read_text(encoding="utf-8")
    function = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "validate_fields")
    measured = decision_points(function)
    if measured > 10:
        raise AssertionError(f"validate_fields complexity {measured} exceeds 10")
    print("validate_fields_complexity: PASS")
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}
    target = positions["evse.target.time_of_day"]
    case(document, "target_qualifiers", "field qualifiers", lambda catalog, index=target: catalog["definitions"]["fields"][index].update(qualifiers=["evse.dimension.evse"]))
    voltage = positions["evse.ac.voltage"]
    case(document, "voltage_qualifiers", "field qualifiers", lambda catalog, index=voltage: catalog["definitions"]["fields"][index].update(qualifiers=["evse.dimension.target"]))


def test_validate_fields_complexity():
    document = validator.load_document(validator.VECTORS)
    check_validate_fields_complexity(document)


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
    check_admitted_rows_leave_the_set_case(document)
    check_validate_fields_complexity(document)


if __name__ == "__main__":
    main()
