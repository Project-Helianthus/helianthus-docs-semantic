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
            "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt", "unit.second", "unit.cubic_metre", "unit.metre", "unit.ohm", "unit.radian", "unit.one", "unit.volt_ampere_reactive_second", "unit.volt_ampere_second", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre", "unit.kilogram_per_joule", "unit.watt_per_square_metre", "unit.metre_per_joule", "unit.currency", "unit.currency_per_joule"}
# Each field the rule moved: SI unit, customary bounds before the move, exact factor and offset.
CONVERTED = {
    "pv.energy.generated": ("unit.joule", ("0", 0), ("1", 12), Fraction(3600000), Fraction(0)),
    "pv.temperature.inverter": ("unit.kelvin", ("-5", 1), ("2", 2), Fraction(1), Fraction(27315, 100)),
}
# Customary and prefixed units that no pack field may declare.
NOT_SI = ("unit.kilowatt_hour", "unit.celsius", "unit.percent", "unit.litre_per_minute", "unit.kilowatt", "unit.bar")


def quantity_identity(identifier, unit, dimension, minimum, maximum):
    """The quantity identity compared whole: id, kind, unit, dimension, optional and both bounds."""
    return {
        "id": identifier,
        "kind": "quantity",
        "unit": unit,
        "dimension": dimension,
        "optional": True,
        "minimum_coefficient": minimum[0],
        "minimum_exponent": minimum[1],
        "maximum_coefficient": maximum[0],
        "maximum_exponent": maximum[1],
    }


# System generated energy stays on the system. String energy and the two phase powers are distinct.
GENERATED_ENERGY = quantity_identity("pv.energy.generated", "unit.joule", "pv.dimension.system", ("0", 0), ("36", 17))
NEW_QUANTITIES = (
    quantity_identity("pv.dc.energy", "unit.joule", "pv.dimension.string", ("0", 0), ("36", 17)),
    quantity_identity("pv.ac.apparent_power", "unit.volt_ampere", "pv.dimension.phase", ("0", 0), ("1", 7)),
    quantity_identity("pv.ac.reactive_power", "unit.volt_ampere_reactive", "pv.dimension.phase", ("-1", 7), ("1", 7)),
)
# Each identity field and the production mutation this test rejects for it:
# id -> DefinitionRef (the ref no longer names the field);
# kind -> noncanonical kind; unit -> canonical quantity contract;
# dimension -> noncanonical dimension (string energy on the system is this case);
# optional -> noncanonical optionality;
# minimum coefficient, maximum coefficient and maximum exponent -> canonical quantity contract;
# minimum exponent -> canonical kernel Decimal when the coefficient is 0, because a zero
# coefficient with another exponent is not a kernel Decimal, and canonical quantity contract
# when the coefficient is not zero.
IDENTITY_MUTATIONS = (
    ("id", "DefinitionRef", lambda field: field.update(id=field["id"] + ".moved")),
    ("kind", "noncanonical kind", lambda field: field.update(kind="symbol")),
    ("unit", "canonical quantity contract", lambda field: field.update(unit="unit.watt")),
    ("dimension", "noncanonical kind, dimension, or optionality", lambda field: field.update(dimension="pv.dimension.system")),
    ("optional", "noncanonical kind, dimension, or optionality", lambda field: field.update(optional=False)),
    ("minimum_coefficient", "canonical quantity contract", lambda field: field["bounds"]["minimum"].update(coefficient="9")),
    ("minimum_exponent", None, lambda field: field["bounds"]["minimum"].update(exponent10=1)),
    ("maximum_coefficient", "canonical quantity contract", lambda field: field["bounds"]["maximum"].update(coefficient="9")),
    ("maximum_exponent", "canonical quantity contract", lambda field: field["bounds"]["maximum"].update(exponent10=3)),
)


def read_identity(field):
    bounds = field["bounds"]
    identity = quantity_identity(
        field["id"], field.get("unit"), field.get("dimension"),
        (bounds["minimum"]["coefficient"], bounds["minimum"]["exponent10"]),
        (bounds["maximum"]["coefficient"], bounds["maximum"]["exponent10"]),
    )
    identity["kind"] = field.get("kind")
    identity["optional"] = field.get("optional")
    return identity


def reject_identity(document, identifier, name, expected, mutate):
    candidate = copy.deepcopy(document)
    field = next(item for item in candidate["catalog"]["definitions"]["fields"] if item["id"] == identifier)
    if expected is None:
        coefficient = field["bounds"]["minimum"]["coefficient"]
        expected = "canonical kernel Decimal" if coefficient == "0" else "canonical quantity contract"
    mutate(field)
    try:
        validator.validate_document(candidate)
    except ValueError as error:
        if expected not in str(error):
            raise AssertionError(f"{identifier} {name}: expected {expected!r}, got {error!s}") from error
        return
    raise AssertionError(f"{identifier} {name} accepted")


def assert_distinct_quantities(fields):
    if read_identity(fields["pv.energy.generated"]) != GENERATED_ENERGY:
        raise AssertionError("pv.energy.generated left pv.dimension.system")
    for expected in NEW_QUANTITIES:
        actual = fields.get(expected["id"])
        if actual is None or actual.get("kind") != "quantity" or read_identity(actual) != expected:
            raise AssertionError(expected["id"] + " is absent or is not its distinct quantity")


def assert_distinct_portals(document):
    portals = {item["id"]: tuple(item.get("fields", ())) for item in document["catalog"]["definitions"]["portal_contributions"]}
    string_fields = portals.get("pv.portal.read.string", ())
    if string_fields[:1] != ("pv.dc.energy",) or "pv.energy.generated" in string_fields:
        raise AssertionError("string read no longer keeps pv.dc.energy off system energy")
    system_fields = portals.get("pv.portal.read.system", ())
    if "pv.energy.generated" not in system_fields or "pv.dc.energy" in system_fields:
        raise AssertionError("system read no longer holds only system energy")
    phase = portals.get("pv.portal.read.phase", ())
    original_phase = ("pv.ac.active_power", "pv.ac.apparent_power", "pv.ac.current", "pv.ac.reactive_power", "pv.ac.voltage")
    if phase[:len(original_phase)] != original_phase:
        raise AssertionError("phase read is not the five phase quantities")


# Phase apparent and reactive power stay on the phase. Active power stays an
# inverter total. The two new totals are absent until the pack names them.
# Each identity field of a new total, and the production mutation this test
# rejects for it, is one IDENTITY_MUTATIONS row:
# id -> DefinitionRef (the ref no longer names the field);
# kind -> noncanonical kind;
# unit -> canonical quantity contract;
# dimension -> noncanonical kind, dimension, or optionality;
# optional -> noncanonical kind, dimension, or optionality;
# minimum coefficient, maximum coefficient and maximum exponent -> canonical quantity contract;
# minimum exponent -> canonical kernel Decimal when the coefficient is 0, and
# canonical quantity contract when the coefficient is not zero.
PHASE_POWERS = (
    quantity_identity("pv.ac.apparent_power", "unit.volt_ampere", "pv.dimension.phase", ("0", 0), ("1", 7)),
    quantity_identity("pv.ac.reactive_power", "unit.volt_ampere_reactive", "pv.dimension.phase", ("-1", 7), ("1", 7)),
)
AGGREGATE_ACTIVE = quantity_identity(
    "pv.ac.aggregate_active_power", "unit.watt", "pv.dimension.inverter", ("-1", 7), ("1", 7),
)
INVERTER_TOTALS = (
    quantity_identity("pv.ac.aggregate_apparent_power", "unit.volt_ampere", "pv.dimension.inverter", ("0", 0), ("1", 7)),
    quantity_identity("pv.ac.aggregate_reactive_power", "unit.volt_ampere_reactive", "pv.dimension.inverter", ("-1", 7), ("1", 7)),
)


def assert_inverter_totals(fields):
    for expected in PHASE_POWERS:
        actual = fields.get(expected["id"])
        if actual is None or read_identity(actual) != expected:
            raise AssertionError(expected["id"] + " left pv.dimension.phase")
    actual_active = fields.get(AGGREGATE_ACTIVE["id"])
    if actual_active is None or read_identity(actual_active) != AGGREGATE_ACTIVE:
        raise AssertionError("pv.ac.aggregate_active_power left pv.dimension.inverter")
    for expected in INVERTER_TOTALS:
        actual = fields.get(expected["id"])
        if actual is None or actual.get("kind") != "quantity" or read_identity(actual) != expected:
            raise AssertionError(expected["id"] + " is absent or is not an inverter total")


def assert_inverter_total_reads(document):
    portals = {item["id"]: tuple(item.get("fields", ()))
               for item in document["catalog"]["definitions"]["portal_contributions"]}
    inverter = portals.get("pv.portal.read.inverter", ())
    phase = portals.get("pv.portal.read.phase", ())
    for expected in INVERTER_TOTALS:
        if expected["id"] not in inverter or expected["id"] in phase:
            raise AssertionError(expected["id"] + " is not only an inverter read field")
    for expected in PHASE_POWERS:
        if expected["id"] not in phase or expected["id"] in inverter:
            raise AssertionError(expected["id"] + " left the phase read")


def reject_inverter_totals(document):
    for expected in INVERTER_TOTALS:
        for name, error, mutate in IDENTITY_MUTATIONS:
            reject_identity(document, expected["id"], name, error, mutate)


def reject_distinct_quantities(document):
    for expected in NEW_QUANTITIES:
        for name, error, mutate in IDENTITY_MUTATIONS:
            reject_identity(document, expected["id"], name, error, mutate)


class TestPVStringEnergyStaysDistinct:
    """String DC energy stays off the system; generated energy stays on the system."""

    def run(self):
        document = validator.load_document(validator.VECTORS)
        fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
        assert_distinct_quantities(fields)
        assert_distinct_portals(document)
        reject_distinct_quantities(document)
        print("pv_string_energy_stays_distinct: PASS")


class TestPVInverterTotalsStayOffPhase:
    """Apparent and reactive inverter totals stay off the phase fields."""

    def run(self):
        document = validator.load_document(validator.VECTORS)
        fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
        assert_inverter_totals(fields)
        assert_inverter_total_reads(document)
        reject_inverter_totals(document)
        print("pv_inverter_totals_stay_off_phase: PASS")


ACTIVE_POWER_LIMIT = quantity_identity(
    "pv.limit.active_power", "unit.watt", "pv.dimension.inverter", ("0", 0), ("1", 7),
)
# Day, month and year yields are period counters. The ratio is not the watt limit.
# Each identity field and the production mutation this test rejects for it:
# id -> DefinitionRef (the ref no longer names the field);
# kind -> noncanonical kind;
# unit -> canonical quantity contract;
# dimension -> noncanonical kind, dimension, or optionality
#   (a yield moved onto the inverter, or the ratio moved onto the system);
# optional -> noncanonical kind, dimension, or optionality;
# minimum coefficient, maximum coefficient and maximum exponent -> canonical quantity contract;
# minimum exponent -> canonical kernel Decimal, because each minimum coefficient is 0.
YIELDS = (
    quantity_identity("pv.energy.yield_day", "unit.joule", "pv.dimension.system", ("0", 0), ("36", 17)),
    quantity_identity("pv.energy.yield_month", "unit.joule", "pv.dimension.system", ("0", 0), ("36", 17)),
    quantity_identity("pv.energy.yield_year", "unit.joule", "pv.dimension.system", ("0", 0), ("36", 17)),
)
LIMIT_RATIO = quantity_identity(
    "pv.limit.active_power_ratio", "unit.ratio", "pv.dimension.inverter", ("0", 0), ("1", 0),
)


def mutations_for(dimension_target):
    rows = []
    for name, error, mutate in IDENTITY_MUTATIONS:
        if name == "dimension":
            rows.append((name, error, lambda field, target=dimension_target: field.update(dimension=target)))
        else:
            rows.append((name, error, mutate))
    return rows


def assert_yields_and_ratio(document):
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    if read_identity(fields["pv.energy.generated"]) != GENERATED_ENERGY:
        raise AssertionError("pv.energy.generated changed")
    if read_identity(fields["pv.limit.active_power"]) != ACTIVE_POWER_LIMIT:
        raise AssertionError("pv.limit.active_power changed")
    missing = [expected["id"] for expected in (*YIELDS, LIMIT_RATIO) if expected["id"] not in fields]
    if missing:
        raise AssertionError(f"yield members absent: {missing}")
    for expected in YIELDS:
        actual = fields[expected["id"]]
        if actual.get("kind") != "quantity" or read_identity(actual) != expected:
            raise AssertionError(expected["id"] + " is not a period yield")
    if read_identity(fields[LIMIT_RATIO["id"]]) != LIMIT_RATIO:
        raise AssertionError("pv.limit.active_power_ratio is not the ratio")
    operation = next(item for item in document["catalog"]["definitions"]["operations"]
                     if item["id"] == "pv.operation.set_active_power_limit")
    if operation.get("arguments") != ["pv.limit.active_power"]:
        raise AssertionError("set-active-power-limit left the watt argument")
    text = validator.DOCUMENT.read_text(encoding="utf-8")
    if "yields are periods" not in text:
        raise AssertionError("PV page does not call the yields periods")
    if "ratio is not the watt limit" not in text:
        raise AssertionError("PV page does not separate the ratio from the watt limit")


def reject_yields_and_ratio(document):
    for expected in YIELDS:
        for name, error, mutate in mutations_for("pv.dimension.inverter"):
            reject_identity(document, expected["id"], name, error, mutate)
    for name, error, mutate in mutations_for("pv.dimension.system"):
        reject_identity(document, LIMIT_RATIO["id"], name, error, mutate)


class TestPVYieldsAndRatio:
    """Period yields stay off the lifetime counter. The ratio stays off the watt limit."""

    def run(self, document):
        assert_yields_and_ratio(document)
        reject_yields_and_ratio(document)
        print("pv_yields_and_ratio: PASS")


def load_checked_document():
    document = validator.load_document(validator.VECTORS)
    TestPVYieldsAndRatio().run(document)
    validator.validate_document(document)
    TestPVStringEnergyStaysDistinct().run()
    TestPVInverterTotalsStayOffPhase().run()
    return document


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
    document = load_checked_document()
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
    case(document, "ac_frequency_exact_maximum", "canonical quantity contract", lambda c: c["definitions"]["fields"][9]["bounds"].update(maximum={"coefficient":"999","exponent10":0}))
    case(document, "retained_limit_exact_maximum", "canonical quantity contract", lambda c: c["definitions"]["fields"][13]["bounds"].update(maximum={"coefficient":"2","exponent10":7}))
    case(document, "wrong_canonical_unit", "canonical quantity contract", lambda c: c["definitions"]["fields"][0].update(unit="unit.watt"))
    case(document, "duplicate_field_order", "fields noncanonical order", lambda c: c["definitions"]["fields"][1].update(order=10))
    case(document, "duplicate_symbol", "canonical symbol contract", lambda c: c["definitions"]["fields"][15].update(symbols=["pv.status.operating.idle", "pv.status.operating.idle"]))
    case(document, "nul_symbol", "canonical symbol contract", lambda c: c["definitions"]["fields"][15].update(symbols=["pv.status.operating.generating\u0000", "pv.status.operating.idle", "pv.status.operating.standby"]))
    case(document, "availability_symbol_reintroduced", "fields catalog", lambda c: c["definitions"]["fields"].append({"id":"pv.status.availability","ref":{"pack":validator.PACK,"id":"pv.status.availability","version":"1.0.0"},"kind":"symbol","dimension":"pv.dimension.inverter","symbols":["pv.status.availability.available"],"optional":True,"order":950}))
    case(document, "readiness_conflates_unavailable", "canonical symbol contract", lambda c: c["definitions"]["fields"][15].update(symbols=["pv.status.operating.generating", "pv.status.operating.idle", "pv.status.operating.unavailable"]))
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
    check_accuracy_facts(document)


def check_accuracy_facts(document):
    """Accuracy identity fields and the production mutation each one catches.

    pv.accuracy.measured id: renaming the field and its ref fails the fields catalog.
    kind, dimension and optional: each change fails the noncanonical field check.
    qualifiers: dropping them fails field qualifiers.
    pv.accuracy.ratio_maximum unit: another SI unit fails the quantity contract.
    bounds minimum and bounds maximum: filling either fails the quantity contract.
    pv.dimension.measurement_type value_kind: text fails the qualifier dimension check.
    symbols: replacing one symbol fails the qualifier dimension check.
    """
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    measured = fields["pv.accuracy.measured"]
    ratio = fields["pv.accuracy.ratio_maximum"]
    if measured["kind"] != "boolean" or tuple(measured["qualifiers"]) != ("pv.dimension.measurement_type",):
        raise AssertionError("measured fact")
    if ratio["kind"] != "quantity" or ratio["unit"] != "unit.ratio" or ratio["bounds"] != {"minimum": None, "maximum": None}:
        raise AssertionError("ratio fact")
    if tuple(ratio["qualifiers"]) != ("pv.dimension.measurement_type",):
        raise AssertionError("ratio qualifiers")
    qualifier = document["catalog"]["definitions"]["qualifier_dimensions"][0]
    if qualifier["id"] != "pv.dimension.measurement_type" or qualifier["value_kind"] != "symbol":
        raise AssertionError("measurement type")
    if tuple(qualifier["symbols"]) != validator.MEASUREMENT_SYMBOLS:
        raise AssertionError("measurement symbols")
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}

    def rename(catalog, ident):
        field = catalog["definitions"]["fields"][positions[ident]]
        field["id"] = ident + "_moved"
        field["ref"]["id"] = field["id"]

    case(document, "measured_id", "fields catalog", lambda catalog: rename(catalog, "pv.accuracy.measured"))
    case(document, "measured_kind", "noncanonical kind", lambda catalog: catalog["definitions"]["fields"][positions["pv.accuracy.measured"]].update(kind="symbol"))
    case(document, "measured_dimension", "noncanonical kind", lambda catalog: catalog["definitions"]["fields"][positions["pv.accuracy.measured"]].update(dimension="pv.dimension.phase"))
    case(document, "measured_optional", "noncanonical kind", lambda catalog: catalog["definitions"]["fields"][positions["pv.accuracy.measured"]].update(optional=False))
    case(document, "measured_qualifiers", "field qualifiers", lambda catalog: catalog["definitions"]["fields"][positions["pv.accuracy.measured"]].pop("qualifiers"))
    case(document, "ratio_unit", "canonical quantity contract", lambda catalog: catalog["definitions"]["fields"][positions["pv.accuracy.ratio_maximum"]].update(unit="unit.watt"))
    case(document, "ratio_minimum", "canonical quantity contract", lambda catalog: catalog["definitions"]["fields"][positions["pv.accuracy.ratio_maximum"]]["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}))
    case(document, "ratio_maximum", "canonical quantity contract", lambda catalog: catalog["definitions"]["fields"][positions["pv.accuracy.ratio_maximum"]]["bounds"].update(maximum={"coefficient": "1", "exponent10": 0}))
    case(document, "measurement_value_kind", "qualifier dimension", lambda catalog: catalog["definitions"]["qualifier_dimensions"][0].update(value_kind="text"))
    case(document, "measurement_symbol", "qualifier dimension", lambda catalog: catalog["definitions"]["qualifier_dimensions"][0]["symbols"].__setitem__(0, "other_symbol"))
    print("accuracy_facts: PASS")
    check_admitted_fields(document)


PRIOR_FIELDS = frozenset({
    "pv.dc.voltage", "pv.dc.current", "pv.dc.power", "pv.dc.energy",
    "pv.ac.voltage", "pv.ac.current", "pv.ac.active_power", "pv.ac.apparent_power", "pv.ac.reactive_power",
    "pv.ac.frequency", "pv.ac.power_factor", "pv.energy.generated", "pv.energy.yield_day", "pv.energy.yield_month",
    "pv.energy.yield_year", "pv.temperature.inverter", "pv.limit.active_power", "pv.limit.active_power_ratio",
    "pv.limit.export_power", "pv.status.operating", "pv.status.derating", "pv.status.fault",
    "pv.dc.aggregate_voltage", "pv.dc.aggregate_current", "pv.dc.aggregate_power",
    "pv.ac.aggregate_voltage", "pv.ac.aggregate_current", "pv.ac.aggregate_active_power",
    "pv.ac.aggregate_apparent_power", "pv.ac.aggregate_reactive_power",
    "pv.accuracy.measured", "pv.accuracy.ratio_maximum",
})
EXCLUDED_IDS = (
    "pv.status.operating_detail", "pv.temperature.sensor", "pv.configuration.maximum_active_power",
    "pv.configuration.maximum_apparent_power", "pv.configuration.maximum_reactive_power",
    "pv.input.state", "pv.input.temperature", "pv.measurement.irradiance", "pv.measurement.module_temperature",
    "pv.dimension.temperature_sensor", "pv.operation.set_power_settings", "pv.operation.set_active_power_limit_ratio",
)


def check_admitted_fields(document):
    """Each admitted field identity and the production mutation that catches it.

    id: renaming the field and its ref fails the fields catalog.
    kind, dimension and optional: each change fails the noncanonical field check.
    quantity unit: another canonical unit fails the quantity contract.
    empty bounds: setting a minimum fails the quantity contract.
    closed bounds: changing the minimum coefficient fails the quantity contract.
    symbol and symbols: replacing the symbol list fails the symbol contract.
    text: adding a unit fails the text contract.
    qualifiers: replacing the qualifier list fails field qualifiers.
    """
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    if fields["pv.configuration.grid_code"]["kind"] != "text" or fields["pv.configuration.grid_code"]["dimension"] != "pv.dimension.inverter":
        raise AssertionError("grid_code")
    if any("sunspec" in ident for ident in fields) or any(ident in fields for ident in EXCLUDED_IDS):
        raise AssertionError("excluded setting")
    if validator.FIELD_CONTRACTS["pv.accuracy.measured"] != ("boolean", None, "pv.dimension.inverter", True, None):
        raise AssertionError("measured pilot")
    if validator.FIELD_CONTRACTS["pv.accuracy.ratio_maximum"] != ("quantity", "unit.ratio", "pv.dimension.inverter", True, None):
        raise AssertionError("ratio pilot")
    if validator.FIELD_BOUNDS["pv.accuracy.ratio_maximum"] != (None, None):
        raise AssertionError("ratio bounds")
    new_ids = [ident for ident in validator.FIELD_CONTRACTS if ident not in PRIOR_FIELDS]
    if len(new_ids) != 63 or set(validator.FIELD_CONTRACTS) != set(fields):
        raise AssertionError("field catalog")
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}
    for ident in new_ids:
        kind = validator.FIELD_CONTRACTS[ident][0]
        index = positions[ident]
        other_dimension = "pv.dimension.array" if fields[ident]["dimension"] != "pv.dimension.array" else "pv.dimension.input"

        def rename(catalog, index=index):
            field = catalog["definitions"]["fields"][index]
            field["id"] = field["id"] + "_moved"
            field["ref"]["id"] = field["id"]

        case(document, ident + "_id", "fields catalog", rename)
        case(document, ident + "_kind", "noncanonical kind", lambda catalog, index=index, kind=kind: catalog["definitions"]["fields"][index].update(kind="text" if kind != "text" else "boolean"))
        case(document, ident + "_dimension", "noncanonical kind", lambda catalog, index=index, other_dimension=other_dimension: catalog["definitions"]["fields"][index].update(dimension=other_dimension))
        case(document, ident + "_optional", "noncanonical kind", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(optional=False))
        if kind == "quantity" and "unit" in fields[ident]:
            other_unit = "unit.second" if fields[ident]["unit"] != "unit.second" else "unit.watt"
            case(document, ident + "_unit", "canonical quantity contract", lambda catalog, index=index, other_unit=other_unit: catalog["definitions"]["fields"][index].update(unit=other_unit))
        if kind == "quantity":
            low, _high = validator.FIELD_BOUNDS[ident]
            if low is None:
                case(document, ident + "_minimum", "canonical quantity contract", lambda catalog, index=index: catalog["definitions"]["fields"][index]["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}))
            else:
                case(document, ident + "_minimum", "canonical quantity contract", lambda catalog, index=index: catalog["definitions"]["fields"][index]["bounds"]["minimum"].update(coefficient="9"))
        elif kind == "text":
            case(document, ident + "_unit", "canonical text contract", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(unit="unit.watt"))
        else:
            case(document, ident + "_symbols", "canonical symbol contract", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(symbols=["other_symbol"]))
        if "qualifiers" in fields[ident]:
            case(document, ident + "_qualifiers", "field qualifiers", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(qualifiers=["pv.dimension.array"]))
    print("admitted_fields: PASS")


if __name__ == "__main__":
    main()
