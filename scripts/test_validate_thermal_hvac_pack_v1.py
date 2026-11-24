#!/usr/bin/env python3
"""Mutation tests for the thermal/HVAC pack documentation validator."""

from __future__ import annotations

import copy
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_thermal_hvac_pack_v1",
    ROOT / "scripts" / "validate_thermal_hvac_pack_v1.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load thermal/HVAC pack validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

# The SI unit set of the unit rule in api/README.md; a pack field declares no other unit.
SI_UNITS = {
    "unit.ampere", "unit.ampere_hour", "unit.cubic_metre_per_second", "unit.hertz", "unit.joule",
    "unit.kelvin", "unit.pascal", "unit.ratio", "unit.reciprocal_second", "unit.volt",
    "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt", "unit.second", "unit.cubic_metre", "unit.metre", "unit.ohm", "unit.radian", "unit.one", "unit.volt_ampere_reactive_second", "unit.volt_ampere_second", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre", "unit.kilogram_per_joule", "unit.watt_per_square_metre", "unit.metre_per_joule", "unit.currency", "unit.currency_per_joule",
}
# The seven units of the thermal pack after the accepted placement.
PACK_UNITS = {
    "unit.kelvin", "unit.ratio", "unit.cubic_metre_per_second", "unit.pascal",
    "unit.reciprocal_second", "unit.watt", "unit.joule",
}
SYSTEM = "thermal.dimension.system"
ZONE = "thermal.dimension.zone"
CIRCUIT = "thermal.dimension.circuit"
DHW = "thermal.dimension.dhw"
VENTILATION = "thermal.dimension.ventilation"
GENERATOR = "thermal.dimension.heat_generator"
STORE = "thermal.dimension.thermal_store"
TERMINAL = "thermal.dimension.terminal_unit"
REFRIGERANT = "thermal.dimension.refrigerant_circuit"
COMPRESSOR = "thermal.dimension.compressor"
ROOM = "thermal.dimension.room"
RESOURCE_DIMENSIONS = {SYSTEM, ZONE, CIRCUIT, DHW, VENTILATION, GENERATOR, STORE, TERMINAL, REFRIGERANT, COMPRESSOR, "thermal.dimension.pump", ROOM}
# Temperature bounds of the placement, in kelvin: -100 to 200 and -50 to 150 degrees Celsius plus 273.15.
AIR = (Fraction(-100), Fraction(200))
SETPOINT = (Fraction(-50), Fraction(150))
CELSIUS_OFFSET = Fraction(27315, 100)


def kelvin(bounds):
    return tuple(value + CELSIUS_OFFSET for value in bounds)


TEMPERATURE = kelvin(AIR)
SET_TEMPERATURE = kelvin(SETPOINT)
RATIO = (Fraction(0), Fraction(1))
# Field -> (subject dimension, unit, (minimum, maximum)); symbols carry no unit and no bounds.
FIELD_TABLE = {
    "thermal.measurement.air_temperature": (ZONE, "unit.kelvin", TEMPERATURE),
    "thermal.measurement.humidity": (ZONE, "unit.ratio", RATIO),
    "thermal.setpoint.temperature_setpoint": (ZONE, "unit.kelvin", SET_TEMPERATURE),
    "thermal.setpoint.occupied_cooling": (ZONE, "unit.kelvin", SET_TEMPERATURE),
    "thermal.setpoint.occupied_heating": (ZONE, "unit.kelvin", SET_TEMPERATURE),
    "thermal.setpoint.unoccupied_cooling": (ZONE, "unit.kelvin", SET_TEMPERATURE),
    "thermal.setpoint.unoccupied_heating": (ZONE, "unit.kelvin", SET_TEMPERATURE),
    "thermal.mode.zone": (ZONE, None, None),
    "thermal.measurement.circuit_flow_temperature": (CIRCUIT, "unit.kelvin", TEMPERATURE),
    "thermal.measurement.flow_rate": (CIRCUIT, "unit.cubic_metre_per_second", (Fraction(0), Fraction(2, 10))),
    "thermal.measurement.dhw_temperature": (DHW, "unit.kelvin", TEMPERATURE),
    "thermal.setpoint.dhw_temperature_setpoint": (DHW, "unit.kelvin", SET_TEMPERATURE),
    "thermal.demand.level": (VENTILATION, "unit.ratio", RATIO),
    "thermal.measurement.outdoor_air_temperature": (SYSTEM, "unit.kelvin", TEMPERATURE),
    "thermal.measurement.system_flow_temperature": (SYSTEM, "unit.kelvin", TEMPERATURE),
    "thermal.mode.system": (SYSTEM, None, None),
    "thermal.action.state": (SYSTEM, None, None),
    "thermal.status.operation": (SYSTEM, None, None),
    "thermal.status.fault": (SYSTEM, None, None),
    "thermal.status.maintenance": (SYSTEM, None, None),
    "thermal.measurement.heat_generator_flow_temperature": (GENERATOR, "unit.kelvin", TEMPERATURE),
    "thermal.measurement.heat_generator_return_temperature": (GENERATOR, "unit.kelvin", TEMPERATURE),
    "thermal.measurement.thermal_power": (GENERATOR, "unit.watt", (Fraction(-1000000), Fraction(1000000))),
    "thermal.energy.heat_output": (GENERATOR, "unit.joule", (Fraction(0), Fraction(36) * 10 ** 17)),
    "thermal.measurement.water_pressure": (GENERATOR, "unit.pascal", (Fraction(-101325), Fraction(10000000))),
    "thermal.status.heat_generator_fault": (GENERATOR, None, None),
    "thermal.status.heat_generator_operation": (GENERATOR, None, None),
    "thermal.measurement.store_temperature": (STORE, "unit.kelvin", TEMPERATURE),
    "thermal.mode.terminal_unit": (TERMINAL, None, None),
    "thermal.status.terminal_unit_fault": (TERMINAL, None, None),
    "thermal.status.terminal_unit_operation": (TERMINAL, None, None),
    "thermal.measurement.refrigerant_high_side_pressure": (REFRIGERANT, "unit.pascal", (Fraction(0), Fraction(10) ** 8)),
    "thermal.measurement.refrigerant_low_side_pressure": (REFRIGERANT, "unit.pascal", (Fraction(0), Fraction(10) ** 8)),
    "thermal.measurement.refrigerant_condensing_temperature": (REFRIGERANT, "unit.kelvin", TEMPERATURE),
    "thermal.measurement.refrigerant_evaporating_temperature": (REFRIGERANT, "unit.kelvin", TEMPERATURE),
    "thermal.measurement.compressor_speed": (COMPRESSOR, "unit.reciprocal_second", (Fraction(0), Fraction(1000))),
    "thermal.measurement.pump_speed": ("thermal.dimension.pump", "unit.reciprocal_second", (Fraction(0), Fraction(1000))),
    "thermal.measurement.valve_position": (TERMINAL, "unit.ratio", RATIO),
    "thermal.overrun.one_time_dhw": (SYSTEM, None, None),
    "thermal.overrun.party": (SYSTEM, None, None),
    "thermal.overrun.sg_ready_condition_1": (SYSTEM, None, None),
    "thermal.overrun.sg_ready_condition_3": (SYSTEM, None, None),
    "thermal.overrun.sg_ready_condition_4": (SYSTEM, None, None),
    "thermal.overrun.one_day_away": (SYSTEM, None, None),
    "thermal.overrun.one_day_at_home": (SYSTEM, None, None),
    "thermal.overrun.one_time_ventilation": (SYSTEM, None, None),
    "thermal.overrun.hvac_system_off": (SYSTEM, None, None),
    "thermal.overrun.valve_kick": (SYSTEM, None, None),
    "thermal.room.limit_absolute_maximum_cooling_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_absolute_maximum_heating_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_absolute_minimum_cooling_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_absolute_minimum_heating_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_maximum_cooling_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_maximum_heating_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_minimum_cooling_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_minimum_heating_setpoint": (ROOM, "unit.kelvin", None),
    "thermal.room.limit_setpoint_step": (ROOM, "unit.kelvin", None),
    "thermal.room.measurement_air_temperature": (ROOM, "unit.kelvin", None),
    "thermal.room.mode_zone": (ROOM, None, None),
    "thermal.room.mode_zone_cooling": (ROOM, None, None),
    "thermal.room.setpoint_occupied_cooling": (ROOM, "unit.kelvin", None),
    "thermal.room.setpoint_occupied_heating": (ROOM, "unit.kelvin", None),
    "thermal.room.setpoint_temperature_setpoint": (ROOM, "unit.kelvin", None),
}
# Overrun identity: field id, system dimension, and the four status symbols.
# Symbol lists stay in canonical sorted order, the same rule as thermal.mode.system.
OVERRUN_IDS = (
    "thermal.overrun.one_time_dhw",
    "thermal.overrun.party",
    "thermal.overrun.sg_ready_condition_1",
    "thermal.overrun.sg_ready_condition_3",
    "thermal.overrun.sg_ready_condition_4",
    "thermal.overrun.one_day_away",
    "thermal.overrun.one_day_at_home",
    "thermal.overrun.one_time_ventilation",
    "thermal.overrun.hvac_system_off",
    "thermal.overrun.valve_kick",
)
OVERRUN_STATUSES = ("active", "finished", "inactive", "running")
# Four zone setpoints, distinct from the single zone setpoint, in canonical id order.
OCCUPANCY_SETPOINTS = (
    "thermal.setpoint.occupied_cooling",
    "thermal.setpoint.occupied_heating",
    "thermal.setpoint.unoccupied_cooling",
    "thermal.setpoint.unoccupied_heating",
)
# System mode keeps auto, cool, heat and off, and adds the five symbols, sorted.
SYSTEM_MODE_SYMBOLS = (
    "auto", "cool", "dry", "emergency_heat", "fan_only", "heat", "off", "precooling", "sleep",
)
# Relation -> (from dimensions, to dimensions, cardinality).
RELATION_TABLE = {
    "thermal.relation.system_member": (
        [SYSTEM], [ZONE, CIRCUIT, DHW, VENTILATION, GENERATOR, STORE, TERMINAL, REFRIGERANT], "one_to_many"),
    "thermal.relation.fluid_supply": (
        [GENERATOR, STORE, CIRCUIT], [CIRCUIT, STORE, ZONE, DHW, TERMINAL], "many_to_many"),
    "thermal.relation.air_supply": ([TERMINAL, VENTILATION], [ZONE], "many_to_many"),
    "thermal.relation.refrigerant_circuit_member": ([REFRIGERANT], [GENERATOR, TERMINAL], "one_to_many"),
    "thermal.relation.generator_compressor": ([GENERATOR], [COMPRESSOR], "one_to_many"),
    "thermal.relation.circuit_room": ([CIRCUIT], [ROOM], "one_to_many"),
    "thermal.relation.circuit_zone": ([CIRCUIT], [ZONE], "one_to_many"),
    "thermal.relation.zone_room": ([ZONE], [ROOM], "one_to_many"),
}
# Identifiers the placement removes; none may remain in the pack vectors, the page or the validator.
REMOVED = (
    "thermal.dimension.temperature", "thermal.dimension.ratio", "thermal.dimension.power",
    "thermal.dimension.volumetric_flow", "thermal.measurement.water_temperature", '"thermal.measurement.power"',
    "unit.celsius", "unit.percent", "unit.litre_per_minute",
)


def exact_value(decimal):
    return Fraction(int(decimal["coefficient"])) * Fraction(10) ** decimal["exponent10"]


def reject(document: dict, expected: str) -> None:
    try:
        validator.validate_document(document)
    except ValueError as error:
        if expected not in str(error):
            raise AssertionError(f"expected {expected!r}, got {error!s}") from error
        return
    raise AssertionError(f"expected rejection containing {expected!r}")


def field_index(document: dict, identifier: str) -> int:
    fields = document["catalog"]["definitions"]["fields"]
    return next(i for i, field in enumerate(fields) if field["id"] == identifier)


def check_field_table(document: dict) -> None:
    fields = {field["id"]: field for field in document["catalog"]["definitions"]["fields"]}
    if set(fields) != set(FIELD_TABLE):
        raise AssertionError(f"field set differs: {sorted(set(fields) ^ set(FIELD_TABLE))}")
    for identifier, (dimension, unit, bounds) in FIELD_TABLE.items():
        field = fields[identifier]
        if field["dimension"] != dimension or dimension not in RESOURCE_DIMENSIONS:
            raise AssertionError(f"{identifier} is not keyed on its subject {dimension}")
        if field.get("unit") != unit:
            raise AssertionError(f"{identifier} declares {field.get('unit')}, not {unit}")
        if bounds is None:
            if "bounds" in field:
                raise AssertionError(f"{identifier} is a symbol with bounds")
            continue
        actual = (exact_value(field["bounds"]["minimum"]), exact_value(field["bounds"]["maximum"]))
        if actual != bounds:
            raise AssertionError(f"{identifier} bounds {actual} differ from {bounds}")
    print("field_subject_unit_bounds_table: PASS")


def check_units(document: dict) -> None:
    if validator.CANONICAL_UNITS != SI_UNITS:
        raise AssertionError("validator unit set differs from the unit rule")
    used = {field["unit"] for field in document["catalog"]["definitions"]["fields"] if field["kind"] == "quantity"}
    if used != PACK_UNITS:
        raise AssertionError(f"pack units {sorted(used)} differ from {sorted(PACK_UNITS)}")
    print("pack_unit_set: PASS")


def check_dimensions(document: dict) -> None:
    dimensions = {item["id"] for item in document["catalog"]["definitions"]["fact_dimensions"]}
    services = {item["fact_key_dimension"] for item in document["catalog"]["definitions"]["services"]}
    if dimensions != RESOURCE_DIMENSIONS or services != RESOURCE_DIMENSIONS:
        raise AssertionError("every dimension is a resource dimension bound by one service")
    print("resource_dimensions_only: PASS")


def check_relations(document: dict) -> None:
    relations = {item["id"]: item for item in document["catalog"]["definitions"]["relations"]}
    if set(relations) != set(RELATION_TABLE):
        raise AssertionError("relation definitions differ")
    for identifier, (ends_from, ends_to, cardinality) in RELATION_TABLE.items():
        item = relations[identifier]
        if (item["from"], item["to"], item["cardinality"]) != (ends_from, ends_to, cardinality):
            raise AssertionError(f"{identifier} endpoints or cardinality differ")
    print("relation_table: PASS")


def check_removed() -> None:
    for path in (validator.VECTORS, validator.DOCUMENT, Path(validator.__file__)):
        text = path.read_text(encoding="utf-8")
        found = [identifier for identifier in REMOVED if identifier in text]
        if found:
            raise AssertionError(f"{path.name} still names {found}")
    print("removed_identifiers_absent: PASS")


def field_axis_mutants(document: dict) -> int:
    """Vary the subject, the unit and each bound of every field; each change must be rejected."""
    count = 0
    for identifier, (dimension, unit, bounds) in FIELD_TABLE.items():
        index = field_index(document, identifier)
        other = ZONE if dimension != ZONE else CIRCUIT
        moved = copy.deepcopy(document)
        moved["catalog"]["definitions"]["fields"][index]["dimension"] = other
        reject(moved, "field subject differs")
        count += 1
        if unit is None:
            continue
        for wrong_unit in ("unit.celsius", sorted(PACK_UNITS - {unit})[0]):
            wrong = copy.deepcopy(document)
            wrong["catalog"]["definitions"]["fields"][index]["unit"] = wrong_unit
            reject(wrong, "field unit")
            count += 1
        if bounds is None:
            inserted = copy.deepcopy(document)
            definitions(inserted)["fields"][index]["bounds"] = {
                "minimum": {"coefficient": "0", "exponent10": 0},
                "maximum": {"coefficient": "1", "exponent10": 0},
            }
            reject(inserted, "field bounds differ")
            count += 1
            continue
        for side in ("minimum", "maximum"):
            shifted = copy.deepcopy(document)
            bound = shifted["catalog"]["definitions"]["fields"][index]["bounds"][side]
            bound["coefficient"] = str(int(bound["coefficient"]) + (-1 if side == "minimum" else 1))
            if bound["coefficient"] == "0":
                bound["exponent10"] = 0
            elif bound["coefficient"].endswith("0"):
                bound["coefficient"] = str(int(bound["coefficient"]) + 1)
            reject(shifted, "field bounds differ")
            count += 1
    return count


def relation_axis_mutants(document: dict) -> int:
    """Vary the identifier, each endpoint list and the cardinality of every relation definition."""
    count = 0
    relations = document["catalog"]["definitions"]["relations"]
    for index, item in enumerate(relations):
        for path, value in (
            (("from",), [CIRCUIT] if item["from"] != [CIRCUIT] else [ZONE]),
            (("to",), item["to"][:-1] or [SYSTEM]),
            (("cardinality",), "one_to_one"),
        ):
            mutated = copy.deepcopy(document)
            mutated["catalog"]["definitions"]["relations"][index][path[0]] = value
            reject(mutated, "relation endpoints or cardinality differ")
            count += 1
        dangling = copy.deepcopy(document)
        dangling["catalog"]["definitions"]["relations"][index]["to"] = ["thermal.dimension.missing"]
        reject(dangling, "relation dangling dimension")
        renamed = copy.deepcopy(document)
        renamed["catalog"]["definitions"]["relations"][index]["id"] += "_other"
        renamed["catalog"]["definitions"]["relations"][index]["ref"]["id"] += "_other"
        reject(renamed, "relation catalog")
        count += 2
    return count


def definitions(document: dict) -> dict:
    return document["catalog"]["definitions"]


def append_field(document: dict, identifier: str) -> None:
    extra = copy.deepcopy(definitions(document)["fields"][0])
    extra["id"] = identifier
    extra["ref"]["id"] = identifier
    extra["order"] = 1000
    definitions(document)["fields"].append(extra)


def overrun_symbols(identifier: str) -> list[str]:
    return [f"{identifier}.{status}" for status in OVERRUN_STATUSES]


def check_overrun_identity(document: dict) -> None:
    """Each overrun id is one system symbol with the four statuses.

    Identity fields and the production mutation each case catches:
    field id: removing the field is rejected as a field catalog mismatch;
    dimension: moving it off thermal.dimension.system is rejected as a subject mismatch;
    each status token active, finished, inactive and running: replacing that token
    is rejected as invalid semantic symbols;
    symbol prefix: a status that is not prefixed by its field id is rejected as
    invalid semantic symbols.
    """
    fields = {field["id"]: field for field in definitions(document)["fields"]}
    missing = [identifier for identifier in OVERRUN_IDS if identifier not in fields]
    if missing:
        raise AssertionError(f"overrun ids absent: {missing}")
    for identifier in OVERRUN_IDS:
        field = fields[identifier]
        if field["dimension"] != SYSTEM or field["kind"] != "symbol":
            raise AssertionError(f"{identifier} is not a system symbol")
        if field.get("symbols") != overrun_symbols(identifier):
            raise AssertionError(f"{identifier} symbols differ from the four overrun statuses")
        if "unit" in field or "bounds" in field:
            raise AssertionError(f"{identifier} carries quantity data")
    text = validator.DOCUMENT.read_text(encoding="utf-8")
    if "independently inactive, active, running or finished" not in text:
        raise AssertionError("thermal page does not state the four independent overrun statuses")
    for identifier in OVERRUN_IDS:
        if identifier not in text:
            raise AssertionError(f"thermal page misses {identifier}")
    print("overrun_identity: PASS")


def overrun_identity_mutants(document: dict) -> int:
    count = 0
    for identifier in OVERRUN_IDS:
        index = field_index(document, identifier)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        count += 1
        moved = copy.deepcopy(document)
        definitions(moved)["fields"][index]["dimension"] = ZONE
        reject(moved, "field subject differs")
        count += 1
        for status in OVERRUN_STATUSES:
            renamed = copy.deepcopy(document)
            symbols = definitions(renamed)["fields"][index]["symbols"]
            symbols[symbols.index(f"{identifier}.{status}")] = f"{identifier}.paused"
            reject(renamed, "field has invalid semantic symbols")
            count += 1
        prefixed = copy.deepcopy(document)
        symbols = definitions(prefixed)["fields"][index]["symbols"]
        symbols[0] = f"thermal.overrun.other.{OVERRUN_STATUSES[0]}"
        reject(prefixed, "field has invalid semantic symbols")
        count += 1
    return count


def system_mode_symbols() -> list[str]:
    return [f"thermal.mode.system.{name}" for name in SYSTEM_MODE_SYMBOLS]


def check_occupancy_setpoints(document: dict) -> None:
    """Four zone kelvin setpoints, distinct from the single zone setpoint.

    Identity fields and the production mutation each case catches:
    field id: removing the field is rejected as a field catalog mismatch;
    dimension: moving it off thermal.dimension.zone is rejected as a subject mismatch;
    unit: replacing unit.kelvin is rejected as a field unit mismatch;
    minimum bound: shifting the minimum is rejected as bounds differ;
    maximum bound: shifting the maximum is rejected as bounds differ;
    each system-mode symbol auto, cool, dry, emergency_heat, fan_only, heat, off,
    precooling and sleep: replacing that token is rejected as invalid semantic symbols.
    """
    fields = {field["id"]: field for field in definitions(document)["fields"]}
    missing = [identifier for identifier in OCCUPANCY_SETPOINTS if identifier not in fields]
    mode = fields["thermal.mode.system"].get("symbols", [])
    missing_symbols = [name for name in SYSTEM_MODE_SYMBOLS if f"thermal.mode.system.{name}" not in mode]
    if missing or missing_symbols:
        raise AssertionError(
            f"occupancy setpoints absent: {missing}; system mode symbols absent: {missing_symbols}")
    for identifier in OCCUPANCY_SETPOINTS:
        field = fields[identifier]
        if field["dimension"] != ZONE or field.get("unit") != "unit.kelvin":
            raise AssertionError(f"{identifier} is not a zone kelvin quantity")
        actual = (exact_value(field["bounds"]["minimum"]), exact_value(field["bounds"]["maximum"]))
        zone = fields["thermal.setpoint.temperature_setpoint"]
        same = (exact_value(zone["bounds"]["minimum"]), exact_value(zone["bounds"]["maximum"]))
        if actual != SET_TEMPERATURE or actual != same:
            raise AssertionError(f"{identifier} bounds differ from the zone setpoint")
    if mode != system_mode_symbols():
        raise AssertionError("thermal.mode.system symbols differ")
    operation = next(item for item in definitions(document)["operations"]
                     if item["id"] == "thermal.operation.set_temperature")
    if operation["arguments"] != ["thermal.setpoint.temperature_setpoint"]:
        raise AssertionError("set-temperature operation no longer takes the single zone setpoint")
    text = validator.DOCUMENT.read_text(encoding="utf-8")
    if "distinct from the single zone setpoint" not in text:
        raise AssertionError("thermal page does not distinguish the occupancy setpoints")
    for identifier in OCCUPANCY_SETPOINTS:
        if identifier not in text:
            raise AssertionError(f"thermal page misses {identifier}")
    print("occupancy_setpoints: PASS")


def _shift_bound(bound: dict, side: str) -> None:
    bound["coefficient"] = str(int(bound["coefficient"]) + (-1 if side == "minimum" else 1))
    if bound["coefficient"] != "0" and bound["coefficient"].endswith("0"):
        bound["coefficient"] = str(int(bound["coefficient"]) + 1)


def occupancy_identity_mutants(document: dict) -> int:
    count = 0
    for identifier in OCCUPANCY_SETPOINTS:
        index = field_index(document, identifier)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        count += 1
        moved = copy.deepcopy(document)
        definitions(moved)["fields"][index]["dimension"] = CIRCUIT
        reject(moved, "field subject differs")
        count += 1
        wrong = copy.deepcopy(document)
        definitions(wrong)["fields"][index]["unit"] = "unit.watt"
        reject(wrong, "field unit")
        count += 1
        for side in ("minimum", "maximum"):
            shifted = copy.deepcopy(document)
            _shift_bound(definitions(shifted)["fields"][index]["bounds"][side], side)
            reject(shifted, "field bounds differ")
            count += 1
    mode_index = field_index(document, "thermal.mode.system")
    for name in SYSTEM_MODE_SYMBOLS:
        renamed = copy.deepcopy(document)
        symbols = definitions(renamed)["fields"][mode_index]["symbols"]
        symbols[symbols.index(f"thermal.mode.system.{name}")] = "thermal.mode.system.paused"
        reject(renamed, "field has invalid semantic symbols")
        count += 1
    return count


PUMP = "thermal.dimension.pump"
PUMP_SERVICE = "thermal.service.pump"
PUMP_SPEED = "thermal.measurement.pump_speed"
VALVE_POSITION = "thermal.measurement.valve_position"
# (field id, subject dimension, unit, (minimum, maximum))
HYDRAULIC = (
    (PUMP_SPEED, PUMP, "unit.reciprocal_second", (Fraction(0), Fraction(1000))),
    (VALVE_POSITION, TERMINAL, "unit.ratio", RATIO),
)


def hydraulic_missing(fields: dict, dimensions: set, services: dict) -> list:
    missing = [identifier for identifier, *_rest in HYDRAULIC if identifier not in fields]
    if PUMP not in dimensions:
        missing.append(PUMP)
    if PUMP_SERVICE not in services:
        missing.append(PUMP_SERVICE)
    return missing


def assert_kept_compressor_and_kick(fields: dict) -> None:
    speed = fields["thermal.measurement.compressor_speed"]
    if speed["dimension"] != COMPRESSOR or speed.get("unit") != "unit.reciprocal_second":
        raise AssertionError("compressor speed changed")
    kick = fields["thermal.overrun.valve_kick"]
    if kick["dimension"] != SYSTEM or kick["kind"] != "symbol":
        raise AssertionError("valve kick changed")
    if fields[PUMP_SPEED]["dimension"] == COMPRESSOR:
        raise AssertionError("pump speed is compressor speed")


def assert_hydraulic_quantities(fields: dict) -> None:
    for identifier, dimension, unit, bounds in HYDRAULIC:
        field = fields[identifier]
        actual = (exact_value(field["bounds"]["minimum"]), exact_value(field["bounds"]["maximum"]))
        if field["dimension"] != dimension or field.get("unit") != unit or actual != bounds:
            raise AssertionError(f"{identifier} is not the hydraulic quantity")


def assert_pump_has_no_actuation(services: dict, capabilities: set, document: dict) -> None:
    service = services[PUMP_SERVICE]
    if service.get("fact_key_dimension") != PUMP:
        raise AssertionError("pump service is not keyed on the pump dimension")
    operations = {item["id"] for item in definitions(document)["operations"]}
    if any("pump" in item for item in capabilities | operations):
        raise AssertionError("pump gained a capability or an operation")
    text = validator.DOCUMENT.read_text(encoding="utf-8")
    if "pump speed is not compressor speed" not in text:
        raise AssertionError("thermal page does not separate pump speed from compressor speed")
    if "valve position is not an overrun" not in text:
        raise AssertionError("thermal page does not separate valve position from an overrun")


def check_pump_and_valve(document: dict) -> None:
    """Pump speed is a pump quantity. Valve position is a terminal-unit ratio.

    Identity fields and the production mutation each case catches:
    field id: removing the field is rejected as a field catalog mismatch;
    dimension: moving pump speed off thermal.dimension.pump, or valve position
    off thermal.dimension.terminal_unit, is rejected as a subject mismatch;
    unit: replacing the unit is rejected as a field unit mismatch;
    minimum bound: shifting the minimum is rejected as bounds differ;
    maximum bound: shifting the maximum is rejected as bounds differ.
    """
    fields = {field["id"]: field for field in definitions(document)["fields"]}
    dimensions = {item["id"] for item in definitions(document)["fact_dimensions"]}
    services = {item["id"]: item for item in definitions(document)["services"]}
    capabilities = {item["id"] for item in definitions(document)["capabilities"]}
    missing = hydraulic_missing(fields, dimensions, services)
    if missing:
        raise AssertionError(f"hydraulic members absent: {missing}")
    assert_kept_compressor_and_kick(fields)
    assert_hydraulic_quantities(fields)
    assert_pump_has_no_actuation(services, capabilities, document)
    print("pump_and_valve: PASS")


def pump_and_valve_mutants(document: dict) -> int:
    count = 0
    for identifier, dimension, _unit, _bounds in HYDRAULIC:
        index = field_index(document, identifier)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        count += 1
        moved = copy.deepcopy(document)
        definitions(moved)["fields"][index]["dimension"] = ZONE if dimension != ZONE else CIRCUIT
        reject(moved, "field subject differs")
        count += 1
        wrong = copy.deepcopy(document)
        definitions(wrong)["fields"][index]["unit"] = "unit.watt"
        reject(wrong, "field unit")
        count += 1
        for side in ("minimum", "maximum"):
            shifted = copy.deepcopy(document)
            _shift_bound(definitions(shifted)["fields"][index]["bounds"][side], side)
            reject(shifted, "field bounds differ")
            count += 1
    return count


def append_qualifier(document: dict) -> None:
    extra = copy.deepcopy(definitions(document)["fact_dimensions"][0])
    extra["id"] = "thermal.dimension.quantity"
    extra["ref"]["id"] = "thermal.dimension.quantity"
    extra["order"] = 1000
    definitions(document)["fact_dimensions"].append(extra)


def set_bounds(document: dict) -> None:
    definitions(document)["fields"][0]["bounds"] = {
        "minimum": {"coefficient": "3", "exponent10": 1},
        "maximum": {"coefficient": "1", "exponent10": 1},
    }


ROOM_QUANTITIES = (
    "thermal.room.limit_absolute_maximum_cooling_setpoint",
    "thermal.room.limit_absolute_maximum_heating_setpoint",
    "thermal.room.limit_absolute_minimum_cooling_setpoint",
    "thermal.room.limit_absolute_minimum_heating_setpoint",
    "thermal.room.limit_maximum_cooling_setpoint",
    "thermal.room.limit_maximum_heating_setpoint",
    "thermal.room.limit_minimum_cooling_setpoint",
    "thermal.room.limit_minimum_heating_setpoint",
    "thermal.room.limit_setpoint_step",
    "thermal.room.measurement_air_temperature",
    "thermal.room.setpoint_occupied_cooling",
    "thermal.room.setpoint_occupied_heating",
    "thermal.room.setpoint_temperature_setpoint",
)
ROOM_MODES = ("thermal.room.mode_zone", "thermal.room.mode_zone_cooling")
ROOM_TOKENS = ("auto", "eco", "off", "on")
# operation, capability, argument fact, effect
ROOM_OPERATIONS = (
    ("thermal.room.operation_set_occupied_cooling", "thermal.room.capability_set_occupied_cooling",
     "thermal.room.setpoint_occupied_cooling", "thermal.room.effect_set_occupied_cooling"),
    ("thermal.room.operation_set_occupied_heating", "thermal.room.capability_set_occupied_heating",
     "thermal.room.setpoint_occupied_heating", "thermal.room.effect_set_occupied_heating"),
    ("thermal.room.operation_set_temperature", "thermal.room.capability_set_temperature",
     "thermal.room.setpoint_temperature_setpoint", "thermal.room.effect_set_temperature"),
    ("thermal.room.operation_set_zone_cooling_mode", "thermal.room.capability_set_zone_cooling_mode",
     "thermal.room.mode_zone_cooling", "thermal.room.effect_set_zone_cooling_mode"),
    ("thermal.room.operation_set_zone_mode", "thermal.room.capability_set_zone_mode",
     "thermal.room.mode_zone", "thermal.room.effect_set_zone_mode"),
)
ROOM_RELATIONS = (
    "thermal.relation.circuit_room",
    "thermal.relation.circuit_zone",
    "thermal.relation.zone_room",
)
ZONE_ARGUMENT = {
    "thermal.room.operation_set_occupied_cooling": "thermal.setpoint.temperature_setpoint",
    "thermal.room.operation_set_occupied_heating": "thermal.setpoint.temperature_setpoint",
    "thermal.room.operation_set_temperature": "thermal.setpoint.temperature_setpoint",
    "thermal.room.operation_set_zone_cooling_mode": "thermal.mode.zone",
    "thermal.room.operation_set_zone_mode": "thermal.mode.zone",
}


def room_symbols(identifier: str) -> list[str]:
    return [f"{identifier}.{token}" for token in ROOM_TOKENS]


def check_room_quantities(fields: dict) -> None:
    for identifier in ROOM_QUANTITIES:
        field = fields[identifier]
        if field["dimension"] != ROOM or field.get("unit") != "unit.kelvin" or "bounds" in field:
            raise AssertionError(f"{identifier} is not an unbounded room kelvin quantity")


def check_room_modes(fields: dict) -> None:
    for identifier in ROOM_MODES:
        symbols = fields[identifier].get("symbols")
        if symbols != room_symbols(identifier):
            raise AssertionError(f"{identifier} symbols differ")
        if any(symbol.endswith(".comfort") for symbol in symbols):
            raise AssertionError(f"{identifier} includes zone comfort")
    zone_symbols = fields["thermal.mode.zone"].get("symbols", [])
    if "thermal.mode.zone.comfort" not in zone_symbols:
        raise AssertionError("zone mode lost comfort")


def check_room_operations(document: dict) -> None:
    operations = {item["id"]: item for item in definitions(document)["operations"]}
    capabilities = {item["id"]: item for item in definitions(document)["capabilities"]}
    for operation_id, capability_id, argument, effect_id in ROOM_OPERATIONS:
        operation = operations[operation_id]
        names_room = operation["capability"] == capability_id
        names_room = names_room and operation["arguments"] == [argument]
        names_room = names_room and operation["effect_rule"] == effect_id
        if not names_room:
            raise AssertionError(f"{operation_id} does not name its room fact")
        if capabilities[capability_id]["service"] != "thermal.service.room":
            raise AssertionError(f"{capability_id} is not on the room service")


def check_room_containment(document: dict) -> None:
    relations = definitions(document)["relations"]
    fluid = next(item for item in relations if item["id"] == "thermal.relation.fluid_supply")
    observed = (fluid["from"], fluid["to"], fluid["cardinality"])
    if observed != RELATION_TABLE["thermal.relation.fluid_supply"]:
        raise AssertionError("fluid supply changed")
    text = validator.DOCUMENT.read_text(encoding="utf-8")
    if "not a physical parent" not in text:
        raise AssertionError("thermal page does not keep fluid supply separate from containment")
    if "distinct from the single zone setpoint" not in text:
        raise AssertionError("thermal page does not distinguish the occupancy setpoints")


def check_room(document: dict) -> None:
    """Room facts, operations and the three containment rows.

    Identity fields and the production mutation each case catches:
    each room quantity id: removing the field is rejected as a field catalog mismatch;
    dimension: moving it off thermal.dimension.room is rejected as a subject mismatch;
    unit: replacing unit.kelvin is rejected as a field unit mismatch;
    bounds: inserting a bounds pair is rejected as bounds differ;
    each room mode id: removing the field is rejected as a field catalog mismatch;
    each mode token auto, eco, off and on: replacing that token is rejected as
    invalid semantic symbols;
    comfort: inserting a comfort symbol is rejected as room mode includes zone comfort;
    each room operation id: renaming the operation is rejected as an operation catalog mismatch;
    capability: pointing the operation at another room capability, and aligning
    its arguments with that capability's constraints, is rejected as
    room operation argument is not the room fact;
    argument fact: swapping in the zone fact, with the capability constraints updated
    to the same fact, is rejected as room operation argument is not the room fact;
    effect: pointing the operation at another room effect is rejected as
    room operation argument is not the room fact;
    service: moving the capability onto thermal.service.zone is rejected as
    room operation argument is not the room fact;
    each containment id thermal.relation.circuit_room, thermal.relation.circuit_zone
    and thermal.relation.zone_room: renaming it is rejected as a relation catalog mismatch;
    from: replacing the from list is rejected as endpoints or cardinality differ;
    to: replacing the to list is rejected as endpoints or cardinality differ;
    cardinality: setting one_to_one is rejected as endpoints or cardinality differ.
    """
    fields = {field["id"]: field for field in definitions(document)["fields"]}
    check_room_quantities(fields)
    check_room_modes(fields)
    check_room_operations(document)
    check_room_containment(document)
    print("room_identity: PASS")


def room_operation_index(document: dict, operation_id: str) -> int:
    operations = definitions(document)["operations"]
    return next(i for i, item in enumerate(operations) if item["id"] == operation_id)


def room_relation_index(document: dict, identifier: str) -> int:
    relations = definitions(document)["relations"]
    return next(i for i, item in enumerate(relations) if item["id"] == identifier)


def room_quantity_mutants(document: dict) -> int:
    count = 0
    for identifier in ROOM_QUANTITIES:
        index = field_index(document, identifier)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        moved = copy.deepcopy(document)
        definitions(moved)["fields"][index]["dimension"] = ZONE
        reject(moved, "field subject differs")
        wrong = copy.deepcopy(document)
        definitions(wrong)["fields"][index]["unit"] = "unit.watt"
        reject(wrong, "field unit")
        inserted = copy.deepcopy(document)
        definitions(inserted)["fields"][index]["bounds"] = {
            "minimum": {"coefficient": "0", "exponent10": 0},
            "maximum": {"coefficient": "1", "exponent10": 0},
        }
        reject(inserted, "field bounds differ")
        count += 4
    return count


def room_mode_mutants(document: dict) -> int:
    count = 0
    for identifier in ROOM_MODES:
        index = field_index(document, identifier)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        count += 1
        for token in ROOM_TOKENS:
            renamed = copy.deepcopy(document)
            symbols = definitions(renamed)["fields"][index]["symbols"]
            symbols[symbols.index(f"{identifier}.{token}")] = f"{identifier}.paused"
            reject(renamed, "field has invalid semantic symbols")
            count += 1
        comfort = copy.deepcopy(document)
        symbols = definitions(comfort)["fields"][index]["symbols"]
        symbols.append(f"{identifier}.comfort")
        symbols.sort()
        reject(comfort, "room mode includes zone comfort")
        count += 1
    return count


def room_operation_rename_mutants(document: dict) -> int:
    count = 0
    for operation_id, _capability_id, _argument, _effect_id in ROOM_OPERATIONS:
        index = room_operation_index(document, operation_id)
        renamed = copy.deepcopy(document)
        item = definitions(renamed)["operations"][index]
        item["id"] += "_other"
        item["ref"]["id"] += "_other"
        reject(renamed, "operation catalog")
        count += 1
    return count


def room_capability_mutants(document: dict) -> int:
    count = 0
    for operation_id, capability_id, _argument, _effect_id in ROOM_OPERATIONS:
        index = room_operation_index(document, operation_id)
        other_capability = "thermal.room.capability_set_temperature"
        if capability_id == other_capability:
            other_capability = "thermal.room.capability_set_zone_mode"
        swapped = copy.deepcopy(document)
        item = definitions(swapped)["operations"][index]
        other = next(capability for capability in definitions(swapped)["capabilities"]
                     if capability["id"] == other_capability)
        item["capability"] = other_capability
        item["arguments"] = list(other["constraints"])
        item["argument_constraints"] = list(other["constraints"])
        reject(swapped, "room operation argument is not the room fact")
        count += 1
    return count


def room_zone_argument_mutants(document: dict) -> int:
    count = 0
    for operation_id, capability_id, _argument, _effect_id in ROOM_OPERATIONS:
        index = room_operation_index(document, operation_id)
        zone_fact = ZONE_ARGUMENT[operation_id]
        swapped = copy.deepcopy(document)
        item = definitions(swapped)["operations"][index]
        item["arguments"] = [zone_fact]
        item["argument_constraints"] = [zone_fact]
        for capability in definitions(swapped)["capabilities"]:
            if capability["id"] == capability_id:
                capability["constraints"] = [zone_fact]
        reject(swapped, "room operation argument is not the room fact")
        count += 1
    return count


def room_effect_mutants(document: dict) -> int:
    count = 0
    for operation_id, _capability_id, _argument, effect_id in ROOM_OPERATIONS:
        index = room_operation_index(document, operation_id)
        other_effect = "thermal.room.effect_set_temperature"
        if effect_id == other_effect:
            other_effect = "thermal.room.effect_set_zone_mode"
        swapped = copy.deepcopy(document)
        definitions(swapped)["operations"][index]["effect_rule"] = other_effect
        reject(swapped, "room operation argument is not the room fact")
        count += 1
    return count


def room_service_mutants(document: dict) -> int:
    count = 0
    for _operation_id, capability_id, _argument, _effect_id in ROOM_OPERATIONS:
        moved = copy.deepcopy(document)
        for capability in definitions(moved)["capabilities"]:
            if capability["id"] == capability_id:
                capability["service"] = "thermal.service.zone"
        reject(moved, "room operation argument is not the room fact")
        count += 1
    return count


def room_relation_mutants(document: dict) -> int:
    count = 0
    for identifier in ROOM_RELATIONS:
        index = room_relation_index(document, identifier)
        renamed = copy.deepcopy(document)
        item = definitions(renamed)["relations"][index]
        item["id"] += "_other"
        item["ref"]["id"] += "_other"
        reject(renamed, "relation catalog")
        moved_from = copy.deepcopy(document)
        definitions(moved_from)["relations"][index]["from"] = [STORE]
        reject(moved_from, "relation endpoints or cardinality differ")
        moved_to = copy.deepcopy(document)
        definitions(moved_to)["relations"][index]["to"] = [STORE]
        reject(moved_to, "relation endpoints or cardinality differ")
        changed = copy.deepcopy(document)
        definitions(changed)["relations"][index]["cardinality"] = "one_to_one"
        reject(changed, "relation endpoints or cardinality differ")
        count += 4
    return count


def room_mutants(document: dict) -> int:
    return (room_quantity_mutants(document) + room_mode_mutants(document)
            + room_operation_rename_mutants(document) + room_capability_mutants(document)
            + room_zone_argument_mutants(document) + room_effect_mutants(document)
            + room_service_mutants(document) + room_relation_mutants(document))


# name -> (mutation of a copy of the document, expected rejection)
CASES = {
    "duplicate_definition": (
        lambda d: definitions(d)["fields"].append(copy.deepcopy(definitions(d)["fields"][0])),
        "duplicate definition ID"),
    "wrong_pack": (lambda d: d["catalog"]["pack"].update(id="helianthus.pack.pv"), "exact PackRef"),
    "missing_follow_on": (lambda d: d["catalog"]["domain_catalog"].pop(), "five-domain catalog"),
    "missing_effect": (lambda d: definitions(d).update(effect_rules=[]), "effect rule"),
    "invalid_bounds": (set_bounds, "unordered numeric bounds"),
    "eebus_normative": (lambda d: d["catalog"]["candidate_mappings"][2].update(state="qualified"), "eeBUS mapping"),
    "non_kernel_kind": (lambda d: definitions(d)["fields"][0].update(kind="decimal"), "non-kernel ValueKind"),
    "missing_owner": (lambda d: definitions(d)["services"][0].pop("ref"), "DefinitionRef owner/version"),
    "arbitrary_extension": (lambda d: append_field(d, "thermal.vendor.extension"), "field catalog"),
    "arbitrary_schedule": (lambda d: append_field(d, "thermal.schedule.summary"), "field catalog"),
    "missing_policy": (lambda d: d["catalog"].pop("publication_withdrawal_policy"), "publication/withdrawal policy"),
    "missing_read_field": (
        lambda d: definitions(d)["portal_contributions"][0]["fields"].remove(
            "thermal.measurement.outdoor_air_temperature"),
        "read descriptor field coverage"),
    "foreign_read_field": (
        lambda d: definitions(d)["portal_contributions"][0]["fields"].append("thermal.measurement.air_temperature"),
        "read descriptor reads another subject"),
    "missing_stage": (lambda d: definitions(d)["operations"][0]["stages"].pop(), "operation stages/outcomes"),
    "bad_constraint": (
        lambda d: definitions(d)["capabilities"][5].update(constraints=[]), "operation/capability constraint mismatch"),
    "invented_outcome": (
        lambda d: definitions(d)["operations"][0]["terminal_outcomes"].__setitem__(1, "dispatched_unacknowledged"),
        "operation stages/outcomes"),
    "qualifier_dimension": (append_qualifier, "fact-key dimension contracts"),
    "customary_unit": (lambda d: definitions(d)["fields"][0].update(unit="unit.percent"),
                       "outside the canonical SI unit set"),
}


def main() -> None:
    document = validator.load_document(validator.VECTORS)
    validator.validate_document(document)
    print("baseline: PASS")
    check_overrun_identity(document)
    check_occupancy_setpoints(document)
    check_pump_and_valve(document)
    check_field_table(document)
    check_units(document)
    check_dimensions(document)
    check_relations(document)
    check_removed()
    for name, (change, expected) in CASES.items():
        candidate = copy.deepcopy(document)
        change(candidate)
        reject(candidate, expected)
        print(f"{name}: REJECTED")
    print(f"field_subject_unit_bound_mutants: {field_axis_mutants(document)} REJECTED")
    print(f"relation_axis_mutants: {relation_axis_mutants(document)} REJECTED")
    print(f"overrun_identity_mutants: {overrun_identity_mutants(document)} REJECTED")
    print(f"occupancy_identity_mutants: {occupancy_identity_mutants(document)} REJECTED")
    print(f"pump_and_valve_mutants: {pump_and_valve_mutants(document)} REJECTED")
    check_room(document)
    print(f"room_mutants: {room_mutants(document)} REJECTED")


if __name__ == "__main__":
    main()
