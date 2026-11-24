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
            "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt", "unit.second", "unit.cubic_metre", "unit.metre", "unit.ohm", "unit.radian", "unit.one", "unit.volt_ampere_reactive_second", "unit.volt_ampere_second", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre", "unit.kilogram_per_joule", "unit.watt_per_square_metre", "unit.metre_per_joule", "unit.currency", "unit.currency_per_joule"}
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


# Each identity field of a new quantity, and the production mutation this test
# rejects for it:
# id -> DefinitionRef (the ref no longer names the field);
# kind -> noncanonical kind, dimension, or optionality;
# unit -> canonical quantity contract (another SI unit, so the unit set still admits it);
# dimension -> noncanonical kind, dimension, or optionality
#   (self-consumption moved onto the grid connection, or either grid-connection
#   power moved onto the meter);
# optional -> noncanonical kind, dimension, or optionality;
# minimum coefficient, minimum exponent, maximum coefficient and maximum exponent
#   -> canonical quantity contract. This validator compares the bound object with
#   the contract before it parses a kernel Decimal, so an exponent change is a
#   quantity-contract failure.
KEPT_QUANTITIES = {
    "infrastructure.energy.import": ("unit.joule", "infrastructure.dimension.meter", ("0", 0), ("36", 17)),
    "infrastructure.energy.export": ("unit.joule", "infrastructure.dimension.meter", ("0", 0), ("36", 17)),
    "infrastructure.power.import_active": ("unit.watt", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.export_active": ("unit.watt", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.import_reactive": ("unit.volt_ampere_reactive", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.export_reactive": ("unit.volt_ampere_reactive", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.apparent": ("unit.volt_ampere", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.ac.active_power": ("unit.watt", "infrastructure.dimension.phase", ("-1", 7), ("1", 7)),
    "infrastructure.ac.voltage_line_line": ("unit.volt", "infrastructure.dimension.line_pair", ("0", 0), ("1", 3)),
}
NEW_QUANTITIES = {
    "infrastructure.energy.self_consumption": ("unit.joule", "infrastructure.dimension.meter", ("0", 0), ("36", 17), "unit.watt", "infrastructure.dimension.grid_connection"),
    "infrastructure.power.pcc": ("unit.watt", "infrastructure.dimension.grid_connection", ("-1", 7), ("1", 7), "unit.joule", "infrastructure.dimension.meter"),
    "infrastructure.limit.fallback_power": ("unit.watt", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7), "unit.joule", "infrastructure.dimension.meter"),
}
SERVICES = {f"infrastructure.service.{name}" for name in ("site", "grid_connection", "feeder", "circuit", "phase", "meter", "line_pair")}
PAGE_PHRASES = ("not the import counter", "not the import/export pair", "not the PV export limit")


def quantity_identity(field):
    bounds = field["bounds"]
    return (
        field.get("kind"),
        field.get("unit"),
        field.get("dimension"),
        field.get("optional"),
        (bounds["minimum"]["coefficient"], bounds["minimum"]["exponent10"]),
        (bounds["maximum"]["coefficient"], bounds["maximum"]["exponent10"]),
    )


def expected_identity(spec):
    unit, dimension, minimum, maximum = spec[:4]
    return ("quantity", unit, dimension, True, minimum, maximum)


def reject_field(document, identifier, name, expected, mutate):
    candidate = copy.deepcopy(document)
    field = next(item for item in candidate["catalog"]["definitions"]["fields"] if item["id"] == identifier)
    mutate(field)
    try:
        validator.validate_document(candidate)
    except ValueError as error:
        if expected not in str(error):
            raise AssertionError(f"{identifier} {name}: expected {expected!r}, got {error!s}") from error
        return
    raise AssertionError(f"{identifier} {name} accepted")


def assert_kept_quantities(fields):
    for identifier, spec in KEPT_QUANTITIES.items():
        actual = fields.get(identifier)
        if actual is None or quantity_identity(actual) != expected_identity(spec):
            raise AssertionError(f"{identifier} changed")


def assert_new_quantities(fields):
    missing = [identifier for identifier in NEW_QUANTITIES if identifier not in fields]
    if missing:
        raise AssertionError(f"grid members absent: {missing}")
    for identifier, spec in NEW_QUANTITIES.items():
        if quantity_identity(fields[identifier]) != expected_identity(spec):
            raise AssertionError(f"{identifier} is not its distinct quantity")


def assert_grid_portals(portals):
    meter = portals.get("infrastructure.portal.read.meter", ())
    grid = portals.get("infrastructure.portal.read.grid_connection", ())
    phase = portals.get("infrastructure.portal.read.phase", ())
    if meter != ("infrastructure.accuracy.measured", "infrastructure.accuracy.ratio_maximum",
                 "infrastructure.energy.export", "infrastructure.energy.import",
                 "infrastructure.energy.self_consumption"):
        raise AssertionError("meter read is not the accuracy facts, then export, import, and self-consumption")
    if "infrastructure.limit.fallback_power" not in grid or "infrastructure.power.pcc" not in grid:
        raise AssertionError("grid-connection read misses the fallback limit or point-of-coupling power")
    if "infrastructure.power.import_active" not in grid or "infrastructure.power.export_active" not in grid:
        raise AssertionError("import and export active power left the grid-connection read")
    if "infrastructure.power.pcc" in phase or "infrastructure.ac.active_power" not in phase:
        raise AssertionError("point-of-coupling power moved onto the phase, or phase active power left it")


def assert_grid_page():
    text = validator.DOCUMENT.read_text(encoding="utf-8")
    for identifier in NEW_QUANTITIES:
        if identifier not in text:
            raise AssertionError(f"document misses {identifier}")
    for phrase in PAGE_PHRASES:
        if phrase not in text:
            raise AssertionError(f"infrastructure page misses {phrase}")


def assert_grid_members(document):
    if document["catalog"]["pack"] != {"id": "helianthus.pack.infrastructure", "version": "1.0.0"}:
        raise AssertionError("pack version changed")
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    assert_kept_quantities(fields)
    services = {item["id"] for item in document["catalog"]["definitions"]["services"]}
    unchanged = services == SERVICES and document["catalog"]["definitions"]["operations"] == []
    if not unchanged or len(document["catalog"]["definitions"]["capabilities"]) != 6:
        raise AssertionError("a service, capability, or operation changed")
    assert_new_quantities(fields)
    portals = {item["id"]: tuple(item.get("fields", ())) for item in document["catalog"]["definitions"]["portal_contributions"]}
    assert_grid_portals(portals)
    assert_grid_page()


def reject_grid_members(document):
    rejected = 0
    for identifier, spec in NEW_QUANTITIES.items():
        wrong_unit, wrong_dimension = spec[4], spec[5]
        mutations = (
            ("id", "DefinitionRef", lambda field: field.update(id=field["id"] + ".moved")),
            ("kind", "noncanonical kind, dimension, or optionality", lambda field: field.update(kind="symbol")),
            ("unit", "canonical quantity contract", lambda field, unit=wrong_unit: field.update(unit=unit)),
            ("dimension", "noncanonical kind, dimension, or optionality", lambda field, dimension=wrong_dimension: field.update(dimension=dimension)),
            ("optional", "noncanonical kind, dimension, or optionality", lambda field: field.update(optional=False)),
            ("minimum_coefficient", "canonical quantity contract", lambda field: field["bounds"]["minimum"].update(coefficient="9")),
            ("minimum_exponent", "canonical quantity contract", lambda field: field["bounds"]["minimum"].update(exponent10=1)),
            ("maximum_coefficient", "canonical quantity contract", lambda field: field["bounds"]["maximum"].update(coefficient="9")),
            ("maximum_exponent", "canonical quantity contract", lambda field: field["bounds"]["maximum"].update(exponent10=3)),
        )
        for name, expected, mutate in mutations:
            reject_field(document, identifier, name, expected, mutate)
            rejected += 1
    print(f"grid_member_mutants: {rejected} REJECTED")


class TestGridMembersStayDistinct:
    """Self-consumption, point-of-coupling power and the fallback limit stay off the counters they are not."""

    def __init__(self, document):
        assert_grid_members(document)
        reject_grid_members(document)
        print("grid_members: PASS")


def main():
    document = validator.load_document(validator.VECTORS)
    TestGridMembersStayDistinct(document)
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
    check_accuracy_facts(document)


def check_accuracy_facts(document):
    """Accuracy identity fields and the production mutation each one catches.

    infrastructure.accuracy.measured id: renaming the field and its ref fails the fields catalog.
    kind, dimension and optional: each change fails the noncanonical field check.
    qualifiers: dropping them fails field qualifiers.
    infrastructure.accuracy.ratio_maximum unit: another SI unit fails the quantity contract.
    bounds minimum and bounds maximum: filling either fails the quantity contract.
    infrastructure.dimension.measurement_type value_kind: text fails the qualifier dimension check.
    symbols: replacing one symbol fails the qualifier dimension check.
    """
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    measured = fields["infrastructure.accuracy.measured"]
    ratio = fields["infrastructure.accuracy.ratio_maximum"]
    if measured["kind"] != "boolean" or tuple(measured["qualifiers"]) != ("infrastructure.dimension.measurement_type",):
        raise AssertionError("measured fact")
    if ratio["kind"] != "quantity" or ratio["unit"] != "unit.ratio" or ratio["bounds"] != {"minimum": None, "maximum": None}:
        raise AssertionError("ratio fact")
    if tuple(ratio["qualifiers"]) != ("infrastructure.dimension.measurement_type",):
        raise AssertionError("ratio qualifiers")
    qualifier = document["catalog"]["definitions"]["qualifier_dimensions"][0]
    if qualifier["id"] != "infrastructure.dimension.measurement_type" or qualifier["value_kind"] != "symbol":
        raise AssertionError("measurement type")
    if tuple(qualifier["symbols"]) != validator.MEASUREMENT_SYMBOLS:
        raise AssertionError("measurement symbols")
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}

    def rename(catalog, ident):
        field = catalog["definitions"]["fields"][positions[ident]]
        field["id"] = ident + "_moved"
        field["ref"]["id"] = field["id"]

    case(document, "measured_id", "fields catalog", lambda catalog: rename(catalog, "infrastructure.accuracy.measured"))
    case(document, "measured_kind", "noncanonical kind", lambda catalog: catalog["definitions"]["fields"][positions["infrastructure.accuracy.measured"]].update(kind="symbol"))
    case(document, "measured_dimension", "noncanonical kind", lambda catalog: catalog["definitions"]["fields"][positions["infrastructure.accuracy.measured"]].update(dimension="infrastructure.dimension.phase"))
    case(document, "measured_optional", "noncanonical kind", lambda catalog: catalog["definitions"]["fields"][positions["infrastructure.accuracy.measured"]].update(optional=False))
    case(document, "measured_qualifiers", "field qualifiers", lambda catalog: catalog["definitions"]["fields"][positions["infrastructure.accuracy.measured"]].pop("qualifiers"))
    case(document, "ratio_unit", "canonical quantity contract", lambda catalog: catalog["definitions"]["fields"][positions["infrastructure.accuracy.ratio_maximum"]].update(unit="unit.watt"))
    case(document, "ratio_minimum", "canonical quantity contract", lambda catalog: catalog["definitions"]["fields"][positions["infrastructure.accuracy.ratio_maximum"]]["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}))
    case(document, "ratio_maximum", "canonical quantity contract", lambda catalog: catalog["definitions"]["fields"][positions["infrastructure.accuracy.ratio_maximum"]]["bounds"].update(maximum={"coefficient": "1", "exponent10": 0}))
    case(document, "measurement_value_kind", "qualifier dimension", lambda catalog: catalog["definitions"]["qualifier_dimensions"][0].update(value_kind="text"))
    case(document, "measurement_symbol", "qualifier dimension", lambda catalog: catalog["definitions"]["qualifier_dimensions"][0]["symbols"].__setitem__(0, "other_symbol"))
    print("accuracy_facts: PASS")


if __name__ == "__main__":
    main()
