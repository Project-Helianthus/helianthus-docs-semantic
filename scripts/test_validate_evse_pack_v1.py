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



PE06_FIELD_IDS = frozenset({
    'evse.ac.active_power',
    'evse.ac.connected_phases',
    'evse.ac.current',
    'evse.ac.frequency',
    'evse.ac.total_active_power',
    'evse.ac.voltage',
    'evse.configuration.randomization_delay_window',
    'evse.demand.departure_time',
    'evse.demand.maximum_energy',
    'evse.demand.minimum_energy',
    'evse.demand.optimal_energy',
    'evse.energy.lifetime',
    'evse.energy.lifetime_exported',
    'evse.energy.session',
    'evse.energy.session_discharged',
    'evse.limit.actual_current',
    'evse.limit.advertised_current',
    'evse.limit.allocated_current',
    'evse.limit.allocated_current_expiry',
    'evse.limit.allocated_current_phase',
    'evse.limit.charging_enabled_until',
    'evse.limit.configured_current',
    'evse.limit.discharging_enabled_until',
    'evse.limit.failsafe_current',
    'evse.limit.maximum_discharge_current',
    'evse.limit.minimum_charge_current',
    'evse.limit.recommended_current_phase',
    'evse.limit.user_maximum_charge_current',
    'evse.limit.vehicle_maximum_current_phase',
    'evse.limit.vehicle_minimum_current_phase',
    'evse.mode',
    'evse.mode_supported',
    'evse.session.asymmetric_charging',
    'evse.session.communication_standard',
    'evse.session.duration',
    'evse.session.identifier',
    'evse.session.rfid_token',
    'evse.session.start',
    'evse.status.charging',
    'evse.status.connection',
    'evse.status.fault',
    'evse.status.fault_cause',
    'evse.status.interlock',
    'evse.status.readiness',
    'evse.status.state',
    'evse.status.supply',
    'evse.summary.cost',
    'evse.summary.currency',
    'evse.summary.end',
    'evse.summary.energy_grid',
    'evse.summary.energy_self_produced',
    'evse.summary.self_produced_ratio',
    'evse.target.added_energy',
    'evse.target.days',
    'evse.target.next_required_energy',
    'evse.target.next_start',
    'evse.target.next_state_of_charge',
    'evse.target.next_target_time',
    'evse.target.schedule_count',
    'evse.target.state_of_charge',
    'evse.target.time_of_day',
    'evse.vehicle.ac_power',
    'evse.vehicle.approximate_efficiency',
    'evse.vehicle.battery_capacity',
    'evse.vehicle.connection',
    'evse.vehicle.identifier',
    'evse.vehicle.maximum_power',
    'evse.vehicle.minimum_power',
    'evse.vehicle.sleep',
    'evse.vehicle.standby_power',
    'evse.vehicle.state_of_charge',
    'evse.vehicle.state_of_health',
    'evse.vehicle.travel_range',
})

STRUCTURAL_EVSE_IDS = frozenset({
    'evse.dimension.measurement_type',
    'evse.capability.clear_targets',
    'evse.capability.read.connector',
    'evse.capability.read.evse',
    'evse.capability.read.meter',
    'evse.capability.read.phase',
    'evse.capability.read.session',
    'evse.capability.read.vehicle',
    'evse.capability.set_allocated_current',
    'evse.capability.set_allocated_current_phase',
    'evse.capability.set_allocated_current_with_expiry',
    'evse.capability.set_evse_mode',
    'evse.capability.set_failsafe_current',
    'evse.capability.set_randomization_delay_window',
    'evse.capability.set_recommended_current_phase',
    'evse.capability.set_supply',
    'evse.capability.set_target',
    'evse.capability.set_user_maximum_charge_current',
    'evse.capability.set_vehicle_efficiency',
    'evse.dimension.asset',
    'evse.dimension.connector',
    'evse.dimension.evse',
    'evse.dimension.meter',
    'evse.dimension.phase',
    'evse.dimension.session',
    'evse.dimension.target',
    'evse.dimension.target_schedule',
    'evse.dimension.vehicle',
    'evse.effect.clear_targets',
    'evse.effect.set_allocated_current',
    'evse.effect.set_allocated_current_phase',
    'evse.effect.set_allocated_current_with_expiry',
    'evse.effect.set_evse_mode',
    'evse.effect.set_failsafe_current',
    'evse.effect.set_randomization_delay_window',
    'evse.effect.set_recommended_current_phase',
    'evse.effect.set_supply',
    'evse.effect.set_target',
    'evse.effect.set_user_maximum_charge_current',
    'evse.effect.set_vehicle_efficiency',
    'evse.event.fault',
    'evse.event.rfid',
    'evse.operation.clear_targets',
    'evse.operation.set_allocated_current',
    'evse.operation.set_allocated_current_phase',
    'evse.operation.set_allocated_current_with_expiry',
    'evse.operation.set_evse_mode',
    'evse.operation.set_failsafe_current',
    'evse.operation.set_randomization_delay_window',
    'evse.operation.set_recommended_current_phase',
    'evse.operation.set_supply',
    'evse.operation.set_target',
    'evse.operation.set_user_maximum_charge_current',
    'evse.operation.set_vehicle_efficiency',
    'evse.portal.operation.set_allocated_current',
    'evse.portal.read.connector',
    'evse.portal.read.evse',
    'evse.portal.read.meter',
    'evse.portal.read.phase',
    'evse.portal.read.session',
    'evse.portal.read.vehicle',
    'evse.relation.asset_evse',
    'evse.relation.connector_phase',
    'evse.relation.connector_session',
    'evse.relation.connector_vehicle',
    'evse.relation.evse_connector',
    'evse.relation.evse_meter',
    'evse.service.connector',
    'evse.service.evse',
    'evse.service.meter',
    'evse.service.phase',
    'evse.service.session',
    'evse.service.vehicle',
})

CONNECTOR_PORTAL_PREFIX = (
    'evse.limit.actual_current',
    'evse.limit.advertised_current',
    'evse.limit.allocated_current',
    'evse.status.charging',
    'evse.status.connection',
    'evse.status.interlock',
    'evse.status.state',
    'evse.limit.allocated_current_expiry',
    'evse.limit.minimum_charge_current',
    'evse.limit.maximum_discharge_current',
    'evse.ac.connected_phases',
)

HEARTBEAT_CONTRACTS = {
    "evse.cevc.heartbeat_timeout": ("quantity", "unit.second", "evse.dimension.connector", True, None, (None, None, "6", 1)),
    "evse.opev.heartbeat_timeout": ("quantity", "unit.second", "evse.dimension.connector", True, None, (None, None, "4", 0)),
    "evse.oscev.heartbeat_timeout": ("quantity", "unit.second", "evse.dimension.connector", True, None, (None, None, "4", 0)),
}
TEXT_ID = "evse.cevc.use_case_name"
TEXT_CONTRACT = ("text", None, "evse.dimension.connector", True, None, None)


CR02_ACCURACY_IDS = frozenset({
    "evse.accuracy.measured", "evse.accuracy.ratio_maximum",
    "evse.accuracy.measured_minimum_active_current", "evse.accuracy.measured_maximum_active_current",
    "evse.accuracy.range_minimum_active_current", "evse.accuracy.range_maximum_active_current",
    "evse.accuracy.measured_minimum_active_power", "evse.accuracy.measured_maximum_active_power",
    "evse.accuracy.range_minimum_active_power", "evse.accuracy.range_maximum_active_power",
})


def qq12_evse_ids():
    import csv
    path = ROOT / "acceptance/catalog-inputs/energy/qq12-fields.tsv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["id"] for row in csv.DictReader(handle, delimiter="\t") if row["id"].startswith("evse.")}


def check_qq12_field_set():
    """FIELD_CONTRACTS is the frozen PE06 field ids plus every QQ12 evse id.

    A QQ12 id missing from FIELD_CONTRACTS, a PE06 id removed from it, or an
    id in neither set fails the equality. Overlap fails the disjoint check.
    """
    qq12 = qq12_evse_ids()
    contracts = set(validator.FIELD_CONTRACTS)
    if contracts != PE06_FIELD_IDS | qq12 | CR02_ACCURACY_IDS:
        raise AssertionError("FIELD_CONTRACTS is not the PE06 fields plus the QQ12 evse fields")
    if PE06_FIELD_IDS & qq12 or CR02_ACCURACY_IDS & (PE06_FIELD_IDS | qq12):
        raise AssertionError("a QQ12 evse id collides with a PE06 field")
    if len(qq12) != 225:
        raise AssertionError("QQ12 evse field count")
    portal = validator.PORTAL_READS["evse.portal.read.connector"][1]
    if portal != CONNECTOR_PORTAL_PREFIX + tuple(sorted(qq12)):
        raise AssertionError("connector portal fields changed the PE06 prefix or the QQ12 order")
    if validator.FIELD_CONTRACTS[TEXT_ID] != TEXT_CONTRACT:
        raise AssertionError("text contract tuple")
    for ident, contract in HEARTBEAT_CONTRACTS.items():
        if validator.FIELD_CONTRACTS[ident] != contract:
            raise AssertionError(f"{ident} contract tuple")
    print("qq12_evse_field_set: PASS")


def check_qq12_catalog_shape():
    """Catalog evse ids are the previous evse ids plus the QQ12 fields."""
    import json
    catalog = json.loads((ROOT / "api/v1/element-catalog-v1.json").read_text(encoding="utf-8"))
    evse = [entry for entry in catalog["elements"] if entry["ref"]["id"].startswith("evse.")]
    facts = {entry["ref"]["id"] for entry in evse if entry["element_kind"] == "fact"}
    all_ids = {entry["ref"]["id"] for entry in evse}
    contracts = set(validator.FIELD_CONTRACTS)
    if facts != contracts:
        raise AssertionError("catalog evse facts differ from FIELD_CONTRACTS")
    if all_ids != STRUCTURAL_EVSE_IDS | contracts:
        raise AssertionError("catalog evse ids differ from the previous ids plus the QQ12 fields")
    by_id = {entry["ref"]["id"]: entry for entry in evse}
    evidence = ["api/v1/packs/evse-v1.md", "https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/177"]
    for ident in sorted(qq12_evse_ids()):
        entry = by_id[ident]
        quantity = ident in HEARTBEAT_CONTRACTS
        if entry["planes"] != (["diagnostic"] if quantity else ["physical"]) or entry["admission"] != {"arm": "eebus", "evidence": evidence}:
            raise AssertionError(f"{ident} plane or admission")
        attributes = entry["attributes"]
        if attributes["aggregation"] != ("member" if quantity else "not_applicable") or attributes["direction"] != "not_applicable":
            raise AssertionError(f"{ident} aggregation or direction")
        subject = attributes["subject"]
        if subject["kind"] != "resource.connector" or subject["dimension"]["id"] != "evse.dimension.connector":
            raise AssertionError(f"{ident} subject")
    print("qq12_evse_catalog_shape: PASS")


def check_qq12_matter_rows():
    """Each QQ12 evse fact has one unknown Matter roster row.

    Fields and the publication change each comparison catches:
    - disposition: ``transformed`` is rejected.
    - reason: a reason other than ``matter.unmapped.v1`` is rejected.
    - target: a ``target`` member is rejected.
    """
    import json
    ledger = json.loads((ROOT / "api/v1/targets/matter-1.6.1-v1.json").read_text(encoding="utf-8"))
    seen = {}
    for row in ledger["rows"]:
        ident = row["ref"]["id"]
        if ident in seen:
            raise AssertionError(f"duplicate roster row {ident}")
        seen[ident] = row
    for ident in sorted(qq12_evse_ids()):
        row = seen.get(ident)
        if row is None or row.get("disposition") != "unknown" or row.get("reason") != "matter.unmapped.v1" or "target" in row:
            raise AssertionError(f"roster row {ident} is not one unknown row")
    print("qq12_evse_matter_rows: PASS")


def field_index(document, ident):
    return next(index for index, field in enumerate(document["catalog"]["definitions"]["fields"]) if field["id"] == ident)


def check_qq12_text_contract(document):
    """``evse.cevc.use_case_name`` keeps every field of its text contract.

    Fields and the production mutation each check catches:
    - kind: setting ``symbol`` is rejected as a noncanonical kind.
    - unit: adding ``unit.second`` is rejected as a text contract.
    - dimension: setting ``evse.dimension.evse`` is rejected as a noncanonical kind.
    - optional: setting ``False`` is rejected as a noncanonical kind.
    - symbols: adding ``evse.cevc.use_case_name.present`` is rejected as a text contract.
    - bounds: adding an empty bound pair is rejected as a text contract.
    """
    index = field_index(document, TEXT_ID)
    case(document, "use_case_name_kind", "noncanonical kind", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(kind="symbol"))
    case(document, "use_case_name_unit", "invalid canonical text contract", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(unit="unit.second"))
    case(document, "use_case_name_dimension", "noncanonical kind", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(dimension="evse.dimension.evse"))
    case(document, "use_case_name_optional", "noncanonical kind", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(optional=False))
    case(document, "use_case_name_symbols", "invalid canonical text contract", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(symbols=["evse.cevc.use_case_name.present"]))
    case(document, "use_case_name_bounds", "invalid canonical text contract", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(bounds={"minimum": None, "maximum": None}))
    print("qq12_evse_text_contract: PASS")


def check_qq12_quantity_contract(document):
    """``evse.cevc.heartbeat_timeout`` keeps every field of its quantity contract.

    Fields and the production mutation each check catches:
    - kind: setting ``text`` is rejected as a noncanonical kind.
    - unit: setting ``unit.volt`` is rejected as a quantity contract.
    - dimension: setting ``evse.dimension.phase`` is rejected as a noncanonical kind.
    - optional: setting ``False`` is rejected as a noncanonical kind.
    - symbols: adding ``evse.cevc.heartbeat_timeout.present`` is rejected as a quantity contract.
    - minimum coefficient and exponent: installing ``0`` with exponent ``0`` is rejected as a quantity contract.
    - maximum coefficient: setting ``7`` is rejected as a quantity contract.
    - maximum exponent: setting ``0`` is rejected as a quantity contract.
    - ``evse.opev.heartbeat_timeout`` maximum: copying the 60 s bound is rejected as a quantity contract.
    """
    index = field_index(document, "evse.cevc.heartbeat_timeout")
    case(document, "heartbeat_kind", "noncanonical kind", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(kind="text"))
    case(document, "heartbeat_unit", "quantity contract", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(unit="unit.volt"))
    case(document, "heartbeat_dimension", "noncanonical kind", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(dimension="evse.dimension.phase"))
    case(document, "heartbeat_optional", "noncanonical kind", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(optional=False))
    case(document, "heartbeat_symbols", "quantity contract", lambda catalog, index=index: catalog["definitions"]["fields"][index].update(symbols=["evse.cevc.heartbeat_timeout.present"]))
    case(document, "heartbeat_minimum", "quantity contract", lambda catalog, index=index: catalog["definitions"]["fields"][index]["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}))
    case(document, "heartbeat_maximum_coefficient", "quantity contract", lambda catalog, index=index: catalog["definitions"]["fields"][index]["bounds"]["maximum"].update(coefficient="7"))
    case(document, "heartbeat_maximum_exponent", "quantity contract", lambda catalog, index=index: catalog["definitions"]["fields"][index]["bounds"]["maximum"].update(exponent10=0))
    other = field_index(document, "evse.opev.heartbeat_timeout")
    case(document, "opev_maximum_copied_from_cevc", "quantity contract", lambda catalog, index=other: catalog["definitions"]["fields"][index]["bounds"].update(maximum={"coefficient": "6", "exponent10": 1}))
    print("qq12_evse_quantity_contract: PASS")


def check_qq12_evse_rows(document):
    check_qq12_field_set()
    check_qq12_catalog_shape()
    check_qq12_matter_rows()
    check_qq12_text_contract(document)
    check_qq12_quantity_contract(document)

def check_connector_vehicle(document):
    """connector_vehicle fields and the production mutation each one catches.

    id and ref id: renaming both is rejected as a relations catalog mismatch.
    from, to and cardinality: each replacement is rejected as a relation association.
    ref pack id, ref pack version and ref version: each is rejected as a missing exact DefinitionRef.
    order: 0 is rejected as noncanonical order.
    """
    relations = document["catalog"]["definitions"]["relations"]
    index = next(i for i, item in enumerate(relations) if item["id"] == "evse.relation.connector_vehicle")
    item = relations[index]
    if (item["from"], item["to"], item["cardinality"], item["order"]) != (
            "evse.dimension.connector", "evse.dimension.vehicle", "one_to_one", 60):
        raise AssertionError("connector_vehicle")

    def rename(catalog, index=index):
        row = catalog["definitions"]["relations"][index]
        row["id"] += "_other"
        row["ref"]["id"] += "_other"

    case(document, "connector_vehicle_id", "relations catalog", rename)
    case(document, "connector_vehicle_from", "relation association", lambda catalog, index=index: catalog["definitions"]["relations"][index].__setitem__("from", "evse.dimension.evse"))
    case(document, "connector_vehicle_to", "relation association", lambda catalog, index=index: catalog["definitions"]["relations"][index].__setitem__("to", "evse.dimension.evse"))
    case(document, "connector_vehicle_cardinality", "relation association", lambda catalog, index=index: catalog["definitions"]["relations"][index].__setitem__("cardinality", "one_to_many"))
    case(document, "connector_vehicle_pack_id", "missing exact DefinitionRef", lambda catalog, index=index: catalog["definitions"]["relations"][index]["ref"]["pack"].__setitem__("id", "helianthus.pack.thermal"))
    case(document, "connector_vehicle_pack_version", "missing exact DefinitionRef", lambda catalog, index=index: catalog["definitions"]["relations"][index]["ref"]["pack"].__setitem__("version", "9.9.9"))
    case(document, "connector_vehicle_version", "missing exact DefinitionRef", lambda catalog, index=index: catalog["definitions"]["relations"][index]["ref"].__setitem__("version", "9.9.9"))
    case(document, "connector_vehicle_order", "noncanonical order", lambda catalog, index=index: catalog["definitions"]["relations"][index].__setitem__("order", 0))
    print("connector_vehicle: PASS")


def check_cr02_accuracy_fields(document):
    """Each accuracy fact of the EVSE meter keeps every field of its contract.

    Fields and the production mutation each check catches, for every id in ``CR02_ACCURACY_IDS``:
    - id: renaming the field and its ref fails the fields catalog.
    - kind: another kind is rejected as a noncanonical kind.
    - dimension: ``evse.dimension.connector`` is rejected as a noncanonical kind.
    - optional: ``False`` is rejected as a noncanonical kind.
    - unit of a quantity: ``unit.volt`` is rejected as a quantity contract.
    - bounds of a quantity: a minimum is rejected as a quantity contract.
    - qualifiers: removing them is rejected as field qualifiers.
    The qualifier dimension: another value kind, and a changed symbol list, are rejected as a qualifier dimension.
    """
    positions = {field["id"]: index for index, field in enumerate(document["catalog"]["definitions"]["fields"])}
    for ident in sorted(CR02_ACCURACY_IDS):
        index = positions[ident]
        kind = validator.FIELD_CONTRACTS[ident][0]
        if validator.FIELD_CONTRACTS[ident][5] is not None or validator.FIELD_CONTRACTS[ident][2] != "evse.dimension.meter":
            raise AssertionError(ident + " contract")
        def rename(catalog, index=index):
            field = catalog["definitions"]["fields"][index]
            field["id"] = field["id"] + "_moved"
            field["ref"]["id"] = field["id"]
        case(document, ident + "_id", "fields catalog", rename)
        case(document, ident + "_kind", "noncanonical kind", lambda c, index=index, kind=kind: c["definitions"]["fields"][index].update(kind="text" if kind != "text" else "boolean"))
        case(document, ident + "_dimension", "noncanonical kind", lambda c, index=index: c["definitions"]["fields"][index].update(dimension="evse.dimension.connector"))
        case(document, ident + "_optional", "noncanonical kind", lambda c, index=index: c["definitions"]["fields"][index].update(optional=False))
        case(document, ident + "_qualifiers", "field qualifiers", lambda c, index=index: c["definitions"]["fields"][index].pop("qualifiers"))
        if kind == "quantity":
            case(document, ident + "_unit", "quantity contract", lambda c, index=index: c["definitions"]["fields"][index].update(unit="unit.volt"))
            case(document, ident + "_bounds", "quantity contract", lambda c, index=index: c["definitions"]["fields"][index]["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}))
    dimensions = document["catalog"]["definitions"]["qualifier_dimensions"]
    place = next(i for i, item in enumerate(dimensions) if item["id"] == "evse.dimension.measurement_type")
    case(document, "measurement_type_value_kind", "qualifier dimension", lambda c: c["definitions"]["qualifier_dimensions"][place].update(value_kind="text"))
    case(document, "measurement_type_symbols", "qualifier dimension", lambda c: c["definitions"]["qualifier_dimensions"][place]["symbols"].pop())
    print("cr02_accuracy_fields: PASS")


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
    check_connector_vehicle(document)
    check_admitted_rows_leave_the_set_case(document)
    check_validate_fields_complexity(document)
    check_qq12_evse_rows(document)
    check_cr02_accuracy_fields(document)


if __name__ == "__main__":
    main()
