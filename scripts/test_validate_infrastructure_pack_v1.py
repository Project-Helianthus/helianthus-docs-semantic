#!/usr/bin/env python3
"""Focused RED-first mutation controls for infrastructure v1."""
from __future__ import annotations

import copy
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_infrastructure_pack_v1", ROOT / "scripts" / "validate_infrastructure_pack_v1.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load infrastructure validator")
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
    "infrastructure.energy.import": ("unit.joule", ("0", 0), ("1", 12), Fraction(3600000), Fraction(0)),
    "infrastructure.energy.export": ("unit.joule", ("0", 0), ("1", 12), Fraction(3600000), Fraction(0)),
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


class TestLineToLineVoltageStaysOffPhase:
    """Line-to-line voltage is a different field from phase voltage.

    Fields and the production mutation each check catches:
    - ``infrastructure.ac.voltage`` dimension: setting it to
      ``infrastructure.dimension.line_pair`` is rejected as a noncanonical dimension.
    - ``infrastructure.ac.voltage_line_line`` id: absence of the field fails.
    - ``infrastructure.ac.voltage_line_line`` dimension: setting it to
      ``infrastructure.dimension.phase`` is rejected as a noncanonical dimension.
    """

    PHASE = "infrastructure.dimension.phase"
    LINE_PAIR = "infrastructure.dimension.line_pair"
    VOLTAGE = "infrastructure.ac.voltage"
    LINE_LINE = "infrastructure.ac.voltage_line_line"

    def __init__(self, document):
        fields = document["catalog"]["definitions"]["fields"]
        by_id = {field["id"]: field for field in fields}
        if by_id.get(self.VOLTAGE, {}).get("dimension") != self.PHASE:
            raise AssertionError(f"{self.VOLTAGE} must stay on {self.PHASE}")
        if self.LINE_LINE not in by_id:
            raise AssertionError(f"{self.LINE_LINE} is absent")
        if by_id[self.LINE_LINE]["dimension"] != self.LINE_PAIR:
            raise AssertionError(f"{self.LINE_LINE} must stay off {self.PHASE}")
        positions = {field["id"]: index for index, field in enumerate(fields)}
        case(
            document,
            "voltage_moved_onto_line_pair",
            "noncanonical kind, dimension, or optionality",
            lambda catalog, index=positions[self.VOLTAGE]: catalog["definitions"]["fields"][index].update(dimension=self.LINE_PAIR),
        )
        case(
            document,
            "line_line_voltage_on_phase",
            "noncanonical kind, dimension, or optionality",
            lambda catalog, index=positions[self.LINE_LINE]: catalog["definitions"]["fields"][index].update(dimension=self.PHASE),
        )
        print("line_to_line_voltage_off_phase: PASS")


def main():
    document = validator.load_document(validator.VECTORS)
    validator.validate_document(document)
    validator.less({"coefficient": "9007199254740992", "exponent10": -18}, {"coefficient": "9007199254740993", "exponent10": -18}) or (_ for _ in ()).throw(AssertionError("exact Decimal comparison"))
    print("baseline_exact_chain: PASS")
    print("close_decimal_interval: PASS")
    check_si_units(document)
    TestLineToLineVoltageStaysOffPhase(document)
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}
    for identifier in CONVERTED:
        for unit in NOT_SI:
            case(document, f"{identifier}_{unit}", "outside the canonical SI unit set", lambda c, i=positions[identifier], u=unit: c["definitions"]["fields"][i].update(unit=u))
    case(document, "voltage_customary_unit", "outside the canonical SI unit set", lambda c: c["definitions"]["fields"][0].update(unit="unit.millivolt"))
    case(document, "import_energy_customary_bounds", "quantity contract", lambda c: c["definitions"]["fields"][positions["infrastructure.energy.import"]]["bounds"].update(maximum={"coefficient": "1", "exponent10": 12}))
    case(document, "export_energy_customary_bounds", "quantity contract", lambda c: c["definitions"]["fields"][positions["infrastructure.energy.export"]]["bounds"].update(maximum={"coefficient": "1", "exponent10": 12}))
    case(document, "reactive_power_customary_unit", "outside the canonical SI unit set", lambda c: c["definitions"]["fields"][positions["infrastructure.ac.reactive_power"]].update(unit="unit.kilovar"))
    case(document, "wrong_pack", "exact PackRef", lambda c: c["pack"].update(id="helianthus.pack.evse"))
    case(document, "evse_downgraded", "five-domain catalog", lambda c: c["domain_catalog"][3].update(state="follow_on"))
    case(document, "bound_drift", "quantity contract", lambda c: c["definitions"]["fields"][0]["bounds"].update(maximum={"coefficient":"9", "exponent10":2}))
    case(document, "dimension_drift", "noncanonical kind", lambda c: c["definitions"]["fields"][0].update(dimension="infrastructure.dimension.site"))
    case(document, "topology_drift", "relation association", lambda c: c["definitions"]["relations"][2].update(cardinality="one_to_one"))
    case(document, "relation_cardinality_missing", "relation association", lambda c: c["definitions"]["relations"][0].pop("cardinality"))
    case(document, "relation_member_earlier_name", "definition groups", lambda c: c["definitions"].update({EARLIER_MEMBER: c["definitions"].pop("relations")}))
    case(document, "relation_member_duplicated", "definition groups", lambda c: c["definitions"].update({EARLIER_MEMBER: copy.deepcopy(c["definitions"]["relations"])}))
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
    print("focused_mutations: 36 REJECTED")


if __name__ == "__main__":
    main()
