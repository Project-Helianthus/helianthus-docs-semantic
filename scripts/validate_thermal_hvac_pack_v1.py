#!/usr/bin/env python3
"""Validate the kernel-compatible thermal/HVAC v1 catalog.

Every field declares exactly one fact dimension. A resource dimension names
the resource the fact is about. thermal.dimension.function is class-level:
anchor class function and no resource kind. A qualifier dimension qualifies a
fact and is not its subject. Quantity fields use the SI units of the unit
rule in api/README.md with the exact bounds of the accepted placement, and the
pack relation definitions name their endpoint dimensions and cardinality.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/packs/thermal-hvac-acceptance-vectors.json"
DOCUMENT = ROOT / "api/v1/packs/thermal-hvac-v1.md"
PACK = {"id": "helianthus.pack.thermal", "version": "1.0.0"}
ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
KINDS = {"quantity", "symbol", "text", "symbols", "boolean", "time"}
# The SI unit set of the unit rule in api/README.md; a pack field declares no other unit.
CANONICAL_UNITS = frozenset({
    "unit.ampere", "unit.ampere_hour", "unit.cubic_metre_per_second", "unit.hertz", "unit.joule",
    "unit.kelvin", "unit.pascal", "unit.ratio", "unit.reciprocal_second", "unit.volt",
    "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt", "unit.second", "unit.cubic_metre", "unit.metre", "unit.ohm", "unit.radian", "unit.one", "unit.volt_ampere_reactive_second", "unit.volt_ampere_second", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre", "unit.kilogram_per_joule", "unit.watt_per_square_metre", "unit.metre_per_joule", "unit.currency", "unit.currency_per_joule",
})
SUBJECTS = ("system", "zone", "circuit", "dhw", "ventilation", "heat_generator", "thermal_store",
            "terminal_unit", "refrigerant_circuit", "compressor", "room", "function", "sensor")
# Pump is a resource subject with a service and a read descriptor, and with no capability.
RESOURCE_SUBJECTS = (*SUBJECTS, "pump", "valve", "solar_circuit", "solar_collector", "detector", "water_tank")
DIMS = {f"thermal.dimension.{name}" for name in RESOURCE_SUBJECTS}
SERVICE_DIMENSION = {f"thermal.service.{name}": f"thermal.dimension.{name}" for name in RESOURCE_SUBJECTS}
SERVICES = set(SERVICE_DIMENSION)
CAPS = {f"thermal.capability.read.{name}" for name in SUBJECTS} | {
    "thermal.capability.set_temperature", "thermal.capability.set_mode",
    "thermal.room.capability_set_occupied_cooling", "thermal.room.capability_set_occupied_heating",
    "thermal.room.capability_set_temperature", "thermal.room.capability_set_zone_cooling_mode",
    "thermal.room.capability_set_zone_mode",
    'thermal.capability.set_active_preset', 'thermal.capability.set_active_program', 'thermal.capability.set_control_sequence', 'thermal.capability.set_display_unit', 'thermal.capability.set_emergency_heat_delta', 'thermal.capability.set_hold', 'thermal.capability.set_keypad_lockout', 'thermal.capability.set_maximum_cooling_setpoint', 'thermal.capability.set_maximum_heating_setpoint', 'thermal.capability.set_minimum_cooling_setpoint', 'thermal.capability.set_minimum_heating_setpoint', 'thermal.capability.set_occupied_cooling', 'thermal.capability.set_occupied_heating', 'thermal.capability.set_preset', 'thermal.capability.set_program_entry', 'thermal.capability.set_remote_sensing', 'thermal.capability.set_schedule_programming', 'thermal.capability.set_suggestion', 'thermal.capability.set_temperature_calibration', 'thermal.capability.set_unoccupied_cooling', 'thermal.capability.set_unoccupied_heating', 'thermal.capability.set_zone_cooling_mode', 'thermal.capability.set_zone_mode', 'thermal.capability.set_dhw_mode', 'thermal.capability.set_dhw_temperature', 'thermal.capability.set_dhw_boost', 'thermal.capability.set_pump_running', 'thermal.capability.set_pump_operation_mode', 'thermal.capability.set_pump_control_mode', 'thermal.capability.set_pump_level', 'thermal.capability.set_valve_state', 'thermal.capability.set_valve_level', 'thermal.capability.set_valve_default_open_duration', 'thermal.capability.set_valve_default_open_level', 'thermal.capability.suppress_detector_alarm', 'thermal.capability.enable_detector_alarm', 'thermal.capability.set_detector_sensitivity', 'thermal.capability.reset_water_tank'}
OPS = {"thermal.operation.set_temperature", "thermal.operation.set_mode",
       "thermal.room.operation_set_occupied_cooling", "thermal.room.operation_set_occupied_heating",
       "thermal.room.operation_set_temperature", "thermal.room.operation_set_zone_cooling_mode",
       "thermal.room.operation_set_zone_mode",
    'thermal.operation.set_active_preset', 'thermal.operation.set_active_program', 'thermal.operation.set_control_sequence', 'thermal.operation.set_display_unit', 'thermal.operation.set_emergency_heat_delta', 'thermal.operation.set_hold', 'thermal.operation.set_keypad_lockout', 'thermal.operation.set_maximum_cooling_setpoint', 'thermal.operation.set_maximum_heating_setpoint', 'thermal.operation.set_minimum_cooling_setpoint', 'thermal.operation.set_minimum_heating_setpoint', 'thermal.operation.set_occupied_cooling', 'thermal.operation.set_occupied_heating', 'thermal.operation.set_preset', 'thermal.operation.set_program_entry', 'thermal.operation.set_remote_sensing', 'thermal.operation.set_schedule_programming', 'thermal.operation.set_suggestion', 'thermal.operation.set_temperature_calibration', 'thermal.operation.set_unoccupied_cooling', 'thermal.operation.set_unoccupied_heating', 'thermal.operation.set_zone_cooling_mode', 'thermal.operation.set_zone_mode', 'thermal.operation.set_dhw_mode', 'thermal.operation.set_dhw_temperature', 'thermal.operation.set_dhw_boost', 'thermal.operation.set_pump_running', 'thermal.operation.set_pump_operation_mode', 'thermal.operation.set_pump_control_mode', 'thermal.operation.set_pump_level', 'thermal.operation.set_valve_state', 'thermal.operation.set_valve_level', 'thermal.operation.set_valve_default_open_duration', 'thermal.operation.set_valve_default_open_level', 'thermal.operation.suppress_detector_alarm', 'thermal.operation.enable_detector_alarm', 'thermal.operation.set_detector_sensitivity', 'thermal.operation.reset_water_tank'}
EFFECTS = {"thermal.effect.set_temperature", "thermal.effect.set_mode",
           "thermal.room.effect_set_occupied_cooling", "thermal.room.effect_set_occupied_heating",
           "thermal.room.effect_set_temperature", "thermal.room.effect_set_zone_cooling_mode",
           "thermal.room.effect_set_zone_mode",
    'thermal.effect.set_active_preset', 'thermal.effect.set_active_program', 'thermal.effect.set_control_sequence', 'thermal.effect.set_display_unit', 'thermal.effect.set_emergency_heat_delta', 'thermal.effect.set_hold', 'thermal.effect.set_keypad_lockout', 'thermal.effect.set_maximum_cooling_setpoint', 'thermal.effect.set_maximum_heating_setpoint', 'thermal.effect.set_minimum_cooling_setpoint', 'thermal.effect.set_minimum_heating_setpoint', 'thermal.effect.set_occupied_cooling', 'thermal.effect.set_occupied_heating', 'thermal.effect.set_preset', 'thermal.effect.set_program_entry', 'thermal.effect.set_remote_sensing', 'thermal.effect.set_schedule_programming', 'thermal.effect.set_suggestion', 'thermal.effect.set_temperature_calibration', 'thermal.effect.set_unoccupied_cooling', 'thermal.effect.set_unoccupied_heating', 'thermal.effect.set_zone_cooling_mode', 'thermal.effect.set_zone_mode', 'thermal.effect.set_dhw_mode', 'thermal.effect.set_dhw_temperature', 'thermal.effect.set_dhw_boost', 'thermal.effect.set_pump_running', 'thermal.effect.set_pump_operation_mode', 'thermal.effect.set_pump_control_mode', 'thermal.effect.set_pump_level', 'thermal.effect.set_valve_state', 'thermal.effect.set_valve_level', 'thermal.effect.set_valve_default_open_duration', 'thermal.effect.set_valve_default_open_level', 'thermal.effect.suppress_detector_alarm', 'thermal.effect.enable_detector_alarm', 'thermal.effect.set_detector_sensitivity', 'thermal.effect.reset_water_tank'}
# Room operation -> (capability, room fact, effect). The argument is that fact, not a zone fact.
ROOM_OPERATIONS = {
    "thermal.room.operation_set_occupied_cooling": (
        "thermal.room.capability_set_occupied_cooling", "thermal.room.setpoint_occupied_cooling",
        "thermal.room.effect_set_occupied_cooling"),
    "thermal.room.operation_set_occupied_heating": (
        "thermal.room.capability_set_occupied_heating", "thermal.room.setpoint_occupied_heating",
        "thermal.room.effect_set_occupied_heating"),
    "thermal.room.operation_set_temperature": (
        "thermal.room.capability_set_temperature", "thermal.room.setpoint_temperature_setpoint",
        "thermal.room.effect_set_temperature"),
    "thermal.room.operation_set_zone_cooling_mode": (
        "thermal.room.capability_set_zone_cooling_mode", "thermal.room.mode_zone_cooling",
        "thermal.room.effect_set_zone_cooling_mode"),
    "thermal.room.operation_set_zone_mode": (
        "thermal.room.capability_set_zone_mode", "thermal.room.mode_zone",
        "thermal.room.effect_set_zone_mode"),
}
PORTAL = {f"thermal.portal.read.{name}" for name in RESOURCE_SUBJECTS} | {
    "thermal.portal.operation.set_temperature", "thermal.portal.operation.set_mode"}
KELVIN = ("unit.kelvin", ("17315", -2), ("47315", -2))
KELVIN_SETPOINT = ("unit.kelvin", ("22315", -2), ("42315", -2))
RATIO = ("unit.ratio", ("0", 0), ("1", 0))
# Field -> (subject dimension, (unit, minimum, maximum) or symbols), tables A3 of the accepted placement.
FIELD_CONTRACT = {
    "thermal.measurement.air_temperature": ("zone", KELVIN),
    "thermal.measurement.humidity": ("zone", RATIO),
    "thermal.setpoint.temperature_setpoint": ("zone", KELVIN_SETPOINT),
    "thermal.setpoint.occupied_cooling": ("zone", KELVIN_SETPOINT),
    "thermal.setpoint.occupied_heating": ("zone", KELVIN_SETPOINT),
    "thermal.setpoint.unoccupied_cooling": ("zone", KELVIN_SETPOINT),
    "thermal.setpoint.unoccupied_heating": ("zone", KELVIN_SETPOINT),
    "thermal.mode.zone": ("zone", ("auto", "comfort", "eco", "off", "on")),
    "thermal.measurement.circuit_flow_temperature": ("circuit", KELVIN),
    "thermal.measurement.flow_rate": ("circuit", ("unit.cubic_metre_per_second", ("0", 0), ("2", -1))),
    "thermal.measurement.dhw_temperature": ("dhw", KELVIN),
    "thermal.setpoint.dhw_temperature_setpoint": ("dhw", KELVIN_SETPOINT),
    "thermal.demand.level": ("ventilation", RATIO),
    "thermal.measurement.outdoor_air_temperature": ("system", KELVIN),
    "thermal.measurement.system_flow_temperature": ("system", KELVIN),
    "thermal.mode.system": ("system", (
        "auto", "cool", "dry", "emergency_heat", "fan_only", "heat", "off", "precooling", "sleep")),
    "thermal.action.state": ("system", ("cooling", "dhw", "heating", "idle", "ventilating")),
    "thermal.status.operation": ("system", ("active", "idle")),
    "thermal.status.fault": ("system", ("clear", "present")),
    "thermal.status.maintenance": ("system", ("clear", "due")),
    "thermal.measurement.heat_generator_flow_temperature": ("heat_generator", KELVIN),
    "thermal.measurement.heat_generator_return_temperature": ("heat_generator", KELVIN),
    "thermal.measurement.thermal_power": ("heat_generator", ("unit.watt", ("-1", 6), ("1", 6))),
    "thermal.energy.heat_output": ("heat_generator", ("unit.joule", ("0", 0), ("36", 17))),
    "thermal.measurement.water_pressure": ("heat_generator", ("unit.pascal", ("-101325", 0), ("1", 7))),
    "thermal.status.heat_generator_fault": ("heat_generator", ("clear", "present")),
    "thermal.status.heat_generator_operation": ("heat_generator", ("active", "idle")),
    "thermal.measurement.store_temperature": ("thermal_store", KELVIN),
    "thermal.mode.terminal_unit": ("terminal_unit", ("auto", "cool", "dry", "fan_only", "heat", "off")),
    "thermal.status.terminal_unit_fault": ("terminal_unit", ("clear", "present")),
    "thermal.status.terminal_unit_operation": ("terminal_unit", ("active", "idle")),
    "thermal.measurement.refrigerant_high_side_pressure": ("refrigerant_circuit", ("unit.pascal", ("0", 0), ("1", 8))),
    "thermal.measurement.refrigerant_low_side_pressure": ("refrigerant_circuit", ("unit.pascal", ("0", 0), ("1", 8))),
    "thermal.measurement.refrigerant_condensing_temperature": ("refrigerant_circuit", KELVIN),
    "thermal.measurement.refrigerant_evaporating_temperature": ("refrigerant_circuit", KELVIN),
    "thermal.measurement.compressor_speed": ("compressor", ("unit.reciprocal_second", ("0", 0), ("1", 3))),
    "thermal.measurement.pump_speed": ("pump", ("unit.reciprocal_second", ("0", 0), ("1", 3))),
    "thermal.measurement.valve_position": ("terminal_unit", RATIO),
    "thermal.overrun.one_time_dhw": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.party": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.sg_ready_condition_1": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.sg_ready_condition_3": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.sg_ready_condition_4": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.one_day_away": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.one_day_at_home": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.one_time_ventilation": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.hvac_system_off": ("system", ("active", "finished", "inactive", "running")),
    "thermal.overrun.valve_kick": ("system", ("active", "finished", "inactive", "running")),
    "thermal.room.limit_absolute_maximum_cooling_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_absolute_maximum_heating_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_absolute_minimum_cooling_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_absolute_minimum_heating_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_maximum_cooling_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_maximum_heating_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_minimum_cooling_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_minimum_heating_setpoint": ("room", ("unit.kelvin",)),
    "thermal.room.limit_setpoint_step": ("room", ("unit.kelvin",)),
    "thermal.room.measurement_air_temperature": ("room", ("unit.kelvin",)),
    "thermal.room.mode_zone": ("room", ("auto", "eco", "off", "on")),
    "thermal.room.mode_zone_cooling": ("room", ("auto", "eco", "off", "on")),
    "thermal.room.setpoint_occupied_cooling": ("room", ("unit.kelvin",)),
    "thermal.room.setpoint_occupied_heating": ("room", ("unit.kelvin",)),
    "thermal.room.setpoint_temperature_setpoint": ("room", ("unit.kelvin",)),
    "thermal.action.zone_state": ("zone", ('cooling', 'dehumidifying', 'heating', 'idle', 'ventilating')),
    "thermal.calibration.temperature_offset": ("zone", ('unit.kelvin',)),
    "thermal.configuration.control_sequence": ("zone", ('cooling_and_heating', 'cooling_and_heating_with_reheat', 'cooling_only', 'cooling_with_reheat', 'heating_only', 'heating_with_reheat')),
    "thermal.configuration.display_unit": ("system", ('celsius', 'fahrenheit')),
    "thermal.configuration.emergency_heat_delta": ("zone", ('unit.kelvin',)),
    "thermal.configuration.keypad_lockout": ("system", ('level_1', 'level_2', 'level_3', 'level_4', 'level_5', 'none')),
    "thermal.configuration.remote_sensing": ("zone", ('local_temperature', 'occupancy', 'outdoor_temperature')),
    "thermal.configuration.schedule_programming": ("system", ('denied', 'permitted')),
    "thermal.demand.cooling": ("zone", ('unit.ratio', ('0', 0), ('1', 0))),
    "thermal.demand.heating": ("zone", ('unit.ratio', ('0', 0), ('1', 0))),
    "thermal.hold.duration": ("zone", ('unit.second',)),
    "thermal.hold.expiry": ("zone", ()),
    "thermal.hold.setpoint": ("zone", ('unit.kelvin',)),
    "thermal.hold.state": ("zone", ('off', 'on')),
    "thermal.limit.absolute_maximum_cooling_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.absolute_maximum_heating_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.absolute_minimum_cooling_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.absolute_minimum_heating_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.maximum_cooling_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.maximum_heating_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.minimum_cooling_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.minimum_heating_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.limit.minimum_setpoint_deadband": ("zone", ('unit.kelvin', ('0', 0), ('127', -1))),
    "thermal.limit.setpoint_step": ("zone", ('unit.kelvin',)),
    "thermal.measurement.sensor_humidity": ("sensor", ('unit.ratio',)),
    "thermal.measurement.sensor_temperature": ("sensor", ('unit.kelvin',)),
    "thermal.mode.zone_cooling": ("zone", ('auto', 'eco', 'off', 'on')),
    "thermal.preset.active_handle": ("zone", ()),
    "thermal.preset.built_in": ("zone", ()),
    "thermal.preset.cooling_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.preset.heating_setpoint": ("zone", ('unit.kelvin',)),
    "thermal.preset.maximum_count": ("zone", ('unit.one', ('1', 0), None)),
    "thermal.preset.name": ("zone", ()),
    "thermal.preset.scenario": ("zone", ('going_to_sleep', 'occupied', 'sleep', 'unoccupied', 'user_defined', 'vacation', 'wake')),
    "thermal.preset.supported_scenarios": ("zone", ('going_to_sleep', 'occupied', 'sleep', 'unoccupied', 'user_defined', 'vacation', 'wake')),
    "thermal.program.active_handle": ("function", ()),
    "thermal.program.built_in": ("function", ()),
    "thermal.program.entry_cooling_setpoint": ("function", ('unit.kelvin',)),
    "thermal.program.entry_days": ("function", ('away', 'friday', 'monday', 'saturday', 'sunday', 'thursday', 'tuesday', 'wednesday')),
    "thermal.program.entry_end": ("function", ('unit.second',)),
    "thermal.program.entry_heating_setpoint": ("function", ('unit.kelvin',)),
    "thermal.program.entry_preset": ("function", ()),
    "thermal.program.entry_start": ("function", ('unit.second',)),
    "thermal.program.entry_state": ("function", ('off', 'on')),
    "thermal.program.entry_system_mode": ("function", ('auto', 'cool', 'heat', 'off')),
    "thermal.program.maximum_count": ("function", ('unit.one', ('1', 0), None)),
    "thermal.program.maximum_entries": ("function", ('unit.one', ('1', 0), None)),
    "thermal.program.maximum_entries_per_day": ("function", ('unit.one', ('1', 0), None)),
    "thermal.program.name": ("function", ()),
    "thermal.program.preset": ("function", ()),
    "thermal.program.supported_types": ("function", ('names', 'off', 'presets', 'setpoints')),
    "thermal.program.system_mode": ("function", ('auto', 'cool', 'heat', 'off')),
    "thermal.setpoint.change_amount": ("zone", ('unit.kelvin',)),
    "thermal.setpoint.change_source": ("zone", ('external', 'manual', 'schedule')),
    "thermal.setpoint.change_time": ("zone", ()),
    "thermal.status.occupancy": ("zone", ('occupied', 'unoccupied')),
    "thermal.status.window": ("zone", ('closed', 'open')),
    "thermal.status.zone_running_state": ("zone", ('cool', 'cool_stage_2', 'fan', 'fan_stage_2', 'fan_stage_3', 'heat', 'heat_stage_2')),
    "thermal.suggestion.active": ("zone", ()),
    "thermal.suggestion.current": ("zone", ('unit.one',)),
    "thermal.suggestion.effective_time": ("zone", ()),
    "thermal.suggestion.expiration": ("zone", ()),
    "thermal.suggestion.maximum_count": ("zone", ('unit.one', ('5', 0), None)),
    "thermal.suggestion.not_following_reason": ("zone", ('conflicting_suggestions', 'demand_response_event', 'occupancy', 'ongoing_hold', 'preconditioning_mode', 'schedule', 'time_of_use_cost_savings', 'vacation_mode')),
    "thermal.suggestion.preset": ("zone", ()),
    "thermal.mode.dhw": ("dhw", ('auto', 'eco', 'manual', 'off', 'on', 'timed', 'vacation')),
    "thermal.mode.dhw_supported": ("dhw", ('auto', 'eco', 'manual', 'off', 'on', 'timed', 'vacation')),
    "thermal.dhw.heater_types": ("dhw", ('boiler', 'heat_pump', 'immersion_element_1', 'immersion_element_2', 'other')),
    "thermal.dhw.heat_demand": ("dhw", ('boiler', 'heat_pump', 'immersion_element_1', 'immersion_element_2', 'other')),
    "thermal.dhw.estimated_heat_required": ("dhw", ("unit.joule", ('0', 0), None)),
    "thermal.dhw.charge_ratio": ("dhw", ("unit.ratio", None, ('1', 0))),
    "thermal.dhw.boost_state": ("dhw", ('active', 'inactive')),
    "thermal.dhw.boost_duration": ("dhw", ("unit.second", ('1', 0), None)),
    "thermal.dhw.boost_one_shot": ("dhw", ()),
    "thermal.dhw.boost_emergency": ("dhw", ()),
    "thermal.dhw.boost_temporary_setpoint": ("dhw", ("unit.kelvin",)),
    "thermal.dhw.boost_target_ratio": ("dhw", ("unit.ratio", None, ('1', 0))),
    "thermal.dhw.boost_target_reheat_ratio": ("dhw", ("unit.ratio",)),
    "thermal.measurement.dhw_flow_rate": ("dhw", ("unit.cubic_metre_per_second",)),
    "thermal.measurement.dhw_circuit_flow_temperature": ("dhw", ("unit.kelvin",)),
    "thermal.measurement.dhw_circuit_return_temperature": ("dhw", ("unit.kelvin",)),
    "thermal.nameplate.store_volume": ("thermal_store", ("unit.cubic_metre",)),
    "thermal.measurement.store_top_temperature": ("thermal_store", ("unit.kelvin",)),
    "thermal.measurement.store_bottom_temperature": ("thermal_store", ("unit.kelvin",)),
    "thermal.status.pump_running": ("pump", ('off', 'on')),
    "thermal.status.pump": ("pump", ('device_fault', 'local_override', 'remote_flow', 'remote_pressure', 'remote_temperature', 'running', 'speed_high', 'speed_low', 'supply_fault')),
    "thermal.status.pump_alarms": ("pump", ('air_detection', 'dry_running', 'electronic_fatal_failure', 'electronic_non_fatal_failure', 'electronic_temperature_high', 'general_fault', 'leakage', 'motor_fatal_failure', 'motor_temperature_high', 'power_missing_phase', 'pump_blocked', 'sensor_failure', 'supply_voltage_high', 'supply_voltage_low', 'system_pressure_high', 'system_pressure_low', 'turbine_operation')),
    "thermal.mode.pump_operation": ("pump", ('local', 'maximum', 'minimum', 'normal')),
    "thermal.mode.pump_effective_operation": ("pump", ('local', 'maximum', 'minimum', 'normal')),
    "thermal.mode.pump_control": ("pump", ('automatic', 'constant_flow', 'constant_pressure', 'constant_speed', 'constant_temperature', 'proportional_pressure')),
    "thermal.mode.pump_effective_control": ("pump", ('automatic', 'constant_flow', 'constant_pressure', 'constant_speed', 'constant_temperature', 'proportional_pressure')),
    "thermal.measurement.pump_capacity": ("pump", ("unit.ratio",)),
    "thermal.setpoint.pump_level": ("pump", ("unit.ratio",)),
    "thermal.measurement.pump_running_time": ("pump", ("unit.second",)),
    "thermal.measurement.pump_power": ("pump", ("unit.watt",)),
    "thermal.energy.pump_consumed": ("pump", ("unit.joule",)),
    "thermal.measurement.pump_flow_rate": ("pump", ("unit.cubic_metre_per_second",)),
    "thermal.measurement.pump_pressure": ("pump", ("unit.pascal",)),
    "thermal.measurement.pump_medium_temperature": ("pump", ("unit.kelvin",)),
    "thermal.nameplate.pump_maximum_pressure": ("pump", ("unit.pascal",)),
    "thermal.nameplate.pump_maximum_speed": ("pump", ("unit.reciprocal_second",)),
    "thermal.nameplate.pump_maximum_flow": ("pump", ("unit.cubic_metre_per_second",)),
    "thermal.nameplate.pump_minimum_constant_pressure": ("pump", ("unit.pascal",)),
    "thermal.nameplate.pump_maximum_constant_pressure": ("pump", ("unit.pascal",)),
    "thermal.nameplate.pump_minimum_compensated_pressure": ("pump", ("unit.pascal",)),
    "thermal.nameplate.pump_maximum_compensated_pressure": ("pump", ("unit.pascal",)),
    "thermal.nameplate.pump_minimum_constant_speed": ("pump", ("unit.reciprocal_second",)),
    "thermal.nameplate.pump_maximum_constant_speed": ("pump", ("unit.reciprocal_second",)),
    "thermal.nameplate.pump_minimum_constant_flow": ("pump", ("unit.cubic_metre_per_second",)),
    "thermal.nameplate.pump_maximum_constant_flow": ("pump", ("unit.cubic_metre_per_second",)),
    "thermal.nameplate.pump_minimum_constant_temperature": ("pump", ("unit.kelvin",)),
    "thermal.nameplate.pump_maximum_constant_temperature": ("pump", ("unit.kelvin",)),
    "thermal.status.valve_state": ("valve", ('closed', 'open', 'transitioning')),
    "thermal.setpoint.valve_target_state": ("valve", ('closed', 'open')),
    "thermal.measurement.valve_level": ("valve", ("unit.ratio", None, ('1', 0))),
    "thermal.setpoint.valve_target_level": ("valve", ("unit.ratio", None, ('1', 0))),
    "thermal.configuration.valve_default_open_level": ("valve", ("unit.ratio", ('1', -2), ('1', 0))),
    "thermal.configuration.valve_level_step": ("valve", ("unit.ratio",)),
    "thermal.valve.open_duration": ("valve", ("unit.second", ('1', 0), None)),
    "thermal.configuration.valve_default_open_duration": ("valve", ("unit.second", ('1', 0), None)),
    "thermal.valve.auto_close_time": ("valve", ()),
    "thermal.valve.remaining_duration": ("valve", ("unit.second",)),
    "thermal.status.valve_faults": ("valve", ('blocked', 'current_exceeded', 'general_fault', 'leaking', 'not_connected', 'short_circuit')),
    "thermal.measurement.valve_flow_rate": ("valve", ("unit.cubic_metre_per_second",)),
    "thermal.measurement.system_water_pressure": ("system", ("unit.pascal",)),
    "thermal.measurement.circuit_water_pressure": ("circuit", ("unit.pascal",)),
    "thermal.measurement.heat_generator_flow_rate": ("heat_generator", ("unit.cubic_metre_per_second",)),
    "thermal.measurement.circuit_return_temperature": ("circuit", ("unit.kelvin",)),
    "thermal.measurement.dew_point": ("circuit", ("unit.kelvin",)),
    "thermal.measurement.circuit_humidity": ("circuit", ("unit.ratio",)),
    "thermal.measurement.collector_temperature": ("solar_collector", ("unit.kelvin",)),
    "thermal.measurement.solar_flow_temperature": ("solar_circuit", ("unit.kelvin",)),
    "thermal.measurement.solar_return_temperature": ("solar_circuit", ("unit.kelvin",)),
    "thermal.measurement.solar_power": ("solar_circuit", ("unit.watt",)),
    "thermal.status.leak": ("detector", ('clear', 'detected')),
    "thermal.status.freeze": ("detector", ('clear', 'detected')),
    "thermal.detector.sensitivity_level": ("detector", ("unit.one",)),
    "thermal.detector.supported_sensitivity_levels": ("detector", ("unit.one",)),
    "thermal.detector.default_sensitivity_level": ("detector", ("unit.one",)),
    "thermal.detector.alarms_active": ("detector", ('audible', 'visual')),
    "thermal.detector.alarms_suppressed": ("detector", ('audible', 'visual')),
    "thermal.detector.alarms_enabled": ("detector", ('audible', 'visual')),
    "thermal.detector.alarms_supported": ("detector", ('audible', 'visual')),
    "thermal.detector.sensor_fault": ("detector", ('general_fault',)),
    "thermal.water_tank.condition": ("water_tank", ("unit.ratio", None, ('1', 0))),
    "thermal.water_tank.degradation_direction": ("water_tank", ('down', 'up')),
    "thermal.water_tank.change_indication": ("water_tank", ('critical', 'ok', 'warning')),
    "thermal.water_tank.in_place": ("water_tank", ()),
    "thermal.water_tank.last_changed": ("water_tank", ()),
    "thermal.water_tank.replacement_product_identifier": ("water_tank", ()),
}
FIELDS = set(FIELD_CONTRACT)
QUALIFIERS = {'thermal.preset.built_in': ('thermal.dimension.preset',), 'thermal.preset.cooling_setpoint': ('thermal.dimension.preset',), 'thermal.preset.heating_setpoint': ('thermal.dimension.preset',), 'thermal.preset.name': ('thermal.dimension.preset',), 'thermal.preset.scenario': ('thermal.dimension.preset',), 'thermal.program.built_in': ('thermal.dimension.time_program',), 'thermal.program.entry_cooling_setpoint': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_days': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_end': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_heating_setpoint': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_preset': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_start': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_state': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_system_mode': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.name': ('thermal.dimension.time_program',), 'thermal.program.preset': ('thermal.dimension.time_program',), 'thermal.program.system_mode': ('thermal.dimension.time_program',), 'thermal.suggestion.active': ('thermal.dimension.suggestion',), 'thermal.suggestion.effective_time': ('thermal.dimension.suggestion',), 'thermal.suggestion.expiration': ('thermal.dimension.suggestion',), 'thermal.suggestion.preset': ('thermal.dimension.suggestion',), 'thermal.water_tank.replacement_product_identifier': ('thermal.dimension.replacement_product',)}
OPERATION_CONTRACT = {'thermal.operation.set_active_preset': ('thermal.capability.set_active_preset', 'thermal.preset.active_handle', 'thermal.effect.set_active_preset', (), 'thermal.service.zone'), 'thermal.operation.set_active_program': ('thermal.capability.set_active_program', 'thermal.program.active_handle', 'thermal.effect.set_active_program', (), 'thermal.service.function'), 'thermal.operation.set_control_sequence': ('thermal.capability.set_control_sequence', 'thermal.configuration.control_sequence', 'thermal.effect.set_control_sequence', (), 'thermal.service.zone'), 'thermal.operation.set_display_unit': ('thermal.capability.set_display_unit', 'thermal.configuration.display_unit', 'thermal.effect.set_display_unit', (), 'thermal.service.system'), 'thermal.operation.set_emergency_heat_delta': ('thermal.capability.set_emergency_heat_delta', 'thermal.configuration.emergency_heat_delta', 'thermal.effect.set_emergency_heat_delta', (), 'thermal.service.zone'), 'thermal.operation.set_hold': ('thermal.capability.set_hold', 'thermal.hold.state', 'thermal.effect.set_hold', ('thermal.hold.duration', 'thermal.hold.setpoint'), 'thermal.service.zone'), 'thermal.operation.set_keypad_lockout': ('thermal.capability.set_keypad_lockout', 'thermal.configuration.keypad_lockout', 'thermal.effect.set_keypad_lockout', (), 'thermal.service.system'), 'thermal.operation.set_maximum_cooling_setpoint': ('thermal.capability.set_maximum_cooling_setpoint', 'thermal.limit.maximum_cooling_setpoint', 'thermal.effect.set_maximum_cooling_setpoint', (), 'thermal.service.zone'), 'thermal.operation.set_maximum_heating_setpoint': ('thermal.capability.set_maximum_heating_setpoint', 'thermal.limit.maximum_heating_setpoint', 'thermal.effect.set_maximum_heating_setpoint', (), 'thermal.service.zone'), 'thermal.operation.set_minimum_cooling_setpoint': ('thermal.capability.set_minimum_cooling_setpoint', 'thermal.limit.minimum_cooling_setpoint', 'thermal.effect.set_minimum_cooling_setpoint', (), 'thermal.service.zone'), 'thermal.operation.set_minimum_heating_setpoint': ('thermal.capability.set_minimum_heating_setpoint', 'thermal.limit.minimum_heating_setpoint', 'thermal.effect.set_minimum_heating_setpoint', (), 'thermal.service.zone'), 'thermal.operation.set_occupied_cooling': ('thermal.capability.set_occupied_cooling', 'thermal.setpoint.occupied_cooling', 'thermal.effect.set_occupied_cooling', (), 'thermal.service.zone'), 'thermal.operation.set_occupied_heating': ('thermal.capability.set_occupied_heating', 'thermal.setpoint.occupied_heating', 'thermal.effect.set_occupied_heating', (), 'thermal.service.zone'), 'thermal.operation.set_preset': ('thermal.capability.set_preset', 'thermal.preset.heating_setpoint', 'thermal.effect.set_preset', ('thermal.preset.cooling_setpoint', 'thermal.preset.name', 'thermal.preset.scenario'), 'thermal.service.zone'), 'thermal.operation.set_program_entry': ('thermal.capability.set_program_entry', 'thermal.program.entry_start', 'thermal.effect.set_program_entry', ('thermal.program.entry_cooling_setpoint', 'thermal.program.entry_days', 'thermal.program.entry_end', 'thermal.program.entry_heating_setpoint', 'thermal.program.entry_preset', 'thermal.program.entry_state', 'thermal.program.entry_system_mode'), 'thermal.service.function'), 'thermal.operation.set_remote_sensing': ('thermal.capability.set_remote_sensing', 'thermal.configuration.remote_sensing', 'thermal.effect.set_remote_sensing', (), 'thermal.service.zone'), 'thermal.operation.set_schedule_programming': ('thermal.capability.set_schedule_programming', 'thermal.configuration.schedule_programming', 'thermal.effect.set_schedule_programming', (), 'thermal.service.system'), 'thermal.operation.set_suggestion': ('thermal.capability.set_suggestion', 'thermal.suggestion.active', 'thermal.effect.set_suggestion', ('thermal.suggestion.effective_time', 'thermal.suggestion.expiration', 'thermal.suggestion.preset'), 'thermal.service.zone'), 'thermal.operation.set_temperature_calibration': ('thermal.capability.set_temperature_calibration', 'thermal.calibration.temperature_offset', 'thermal.effect.set_temperature_calibration', (), 'thermal.service.zone'), 'thermal.operation.set_unoccupied_cooling': ('thermal.capability.set_unoccupied_cooling', 'thermal.setpoint.unoccupied_cooling', 'thermal.effect.set_unoccupied_cooling', (), 'thermal.service.zone'), 'thermal.operation.set_unoccupied_heating': ('thermal.capability.set_unoccupied_heating', 'thermal.setpoint.unoccupied_heating', 'thermal.effect.set_unoccupied_heating', (), 'thermal.service.zone'), 'thermal.operation.set_zone_cooling_mode': ('thermal.capability.set_zone_cooling_mode', 'thermal.mode.zone_cooling', 'thermal.effect.set_zone_cooling_mode', (), 'thermal.service.zone'), 'thermal.operation.set_zone_mode': ('thermal.capability.set_zone_mode', 'thermal.mode.zone', 'thermal.effect.set_zone_mode', (), 'thermal.service.zone'), 'thermal.operation.set_dhw_mode': ('thermal.capability.set_dhw_mode', 'thermal.mode.dhw', 'thermal.effect.set_dhw_mode', (), 'thermal.service.dhw'), 'thermal.operation.set_dhw_temperature': ('thermal.capability.set_dhw_temperature', 'thermal.setpoint.dhw_temperature_setpoint', 'thermal.effect.set_dhw_temperature', (), 'thermal.service.dhw'), 'thermal.operation.set_dhw_boost': ('thermal.capability.set_dhw_boost', 'thermal.dhw.boost_state', 'thermal.effect.set_dhw_boost', ('thermal.dhw.boost_duration', 'thermal.dhw.boost_one_shot', 'thermal.dhw.boost_emergency', 'thermal.dhw.boost_temporary_setpoint', 'thermal.dhw.boost_target_ratio', 'thermal.dhw.boost_target_reheat_ratio'), 'thermal.service.dhw'), 'thermal.operation.set_pump_running': ('thermal.capability.set_pump_running', 'thermal.status.pump_running', 'thermal.effect.set_pump_running', (), 'thermal.service.pump'), 'thermal.operation.set_pump_operation_mode': ('thermal.capability.set_pump_operation_mode', 'thermal.mode.pump_operation', 'thermal.effect.set_pump_operation_mode', (), 'thermal.service.pump'), 'thermal.operation.set_pump_control_mode': ('thermal.capability.set_pump_control_mode', 'thermal.mode.pump_control', 'thermal.effect.set_pump_control_mode', (), 'thermal.service.pump'), 'thermal.operation.set_pump_level': ('thermal.capability.set_pump_level', 'thermal.setpoint.pump_level', 'thermal.effect.set_pump_level', (), 'thermal.service.pump'), 'thermal.operation.set_valve_state': ('thermal.capability.set_valve_state', 'thermal.setpoint.valve_target_state', 'thermal.effect.set_valve_state', ('thermal.valve.open_duration', 'thermal.setpoint.valve_target_level'), 'thermal.service.valve'), 'thermal.operation.set_valve_level': ('thermal.capability.set_valve_level', 'thermal.setpoint.valve_target_level', 'thermal.effect.set_valve_level', (), 'thermal.service.valve'), 'thermal.operation.set_valve_default_open_duration': ('thermal.capability.set_valve_default_open_duration', 'thermal.configuration.valve_default_open_duration', 'thermal.effect.set_valve_default_open_duration', (), 'thermal.service.valve'), 'thermal.operation.set_valve_default_open_level': ('thermal.capability.set_valve_default_open_level', 'thermal.configuration.valve_default_open_level', 'thermal.effect.set_valve_default_open_level', (), 'thermal.service.valve'), 'thermal.operation.suppress_detector_alarm': ('thermal.capability.suppress_detector_alarm', 'thermal.detector.alarms_suppressed', 'thermal.effect.suppress_detector_alarm', (), 'thermal.service.detector'), 'thermal.operation.enable_detector_alarm': ('thermal.capability.enable_detector_alarm', 'thermal.detector.alarms_enabled', 'thermal.effect.enable_detector_alarm', (), 'thermal.service.detector'), 'thermal.operation.set_detector_sensitivity': ('thermal.capability.set_detector_sensitivity', 'thermal.detector.sensitivity_level', 'thermal.effect.set_detector_sensitivity', (), 'thermal.service.detector'), 'thermal.operation.reset_water_tank': ('thermal.capability.reset_water_tank', 'thermal.water_tank.change_indication', 'thermal.effect.reset_water_tank', (), 'thermal.service.water_tank')}
EVENT_CONTRACT = {'thermal.event.active_preset_changed': ('thermal.service.zone', 'thermal.preset.active_handle', ()), 'thermal.event.active_program_changed': ('thermal.service.function', 'thermal.program.active_handle', ()), 'thermal.event.local_temperature_changed': ('thermal.service.zone', 'thermal.measurement.air_temperature', ()), 'thermal.event.occupancy_changed': ('thermal.service.zone', 'thermal.status.occupancy', ()), 'thermal.event.running_mode_changed': ('thermal.service.zone', 'thermal.action.zone_state', ()), 'thermal.event.running_state_changed': ('thermal.service.zone', 'thermal.status.zone_running_state', ()), 'thermal.event.setpoint_changed': ('thermal.service.zone', 'thermal.setpoint.occupied_heating', ('thermal.setpoint.change_amount', 'thermal.setpoint.change_source')), 'thermal.event.system_mode_changed': ('thermal.service.system', 'thermal.mode.system', ()), 'thermal.event.valve_state_changed': ('thermal.service.valve', 'thermal.status.valve_state', ('thermal.measurement.valve_level',)), 'thermal.event.valve_fault': ('thermal.service.valve', 'thermal.status.valve_faults', ()), 'thermal.event.leak_changed': ('thermal.service.detector', 'thermal.status.leak', ()), 'thermal.event.freeze_changed': ('thermal.service.detector', 'thermal.status.freeze', ()), 'thermal.event.detector_alarms_changed': ('thermal.service.detector', 'thermal.detector.alarms_active', ('thermal.detector.alarms_suppressed',)), 'thermal.event.detector_sensor_fault': ('thermal.service.detector', 'thermal.detector.sensor_fault', ())}
QUALIFIER_CONTRACT = {'thermal.dimension.preset': ('text', None), 'thermal.dimension.program_entry': ('quantity', 'unit.one'), 'thermal.dimension.suggestion': ('quantity', 'unit.one'), 'thermal.dimension.time_program': ('text', None), 'thermal.dimension.replacement_product': ('quantity', 'unit.one')}
# Relation -> (from subjects, to subjects, cardinality), table A4 of the accepted placement.
RELATION_CONTRACT = {
    "thermal.relation.system_member": (
        ("system",),
        ("zone", "circuit", "dhw", "ventilation", "heat_generator", "thermal_store", "terminal_unit",
         "refrigerant_circuit"),
        "one_to_many"),
    "thermal.relation.fluid_supply": (
        ("heat_generator", "thermal_store", "circuit"), ("circuit", "thermal_store", "zone", "dhw", "terminal_unit"),
        "many_to_many"),
    "thermal.relation.air_supply": (("terminal_unit", "ventilation"), ("zone",), "many_to_many"),
    "thermal.relation.refrigerant_circuit_member": (("refrigerant_circuit",), ("heat_generator", "terminal_unit"),
                                                    "one_to_many"),
    "thermal.relation.generator_compressor": (("heat_generator",), ("compressor",), "one_to_many"),
    "thermal.relation.circuit_room": (("circuit",), ("room",), "one_to_many"),
    "thermal.relation.circuit_zone": (("circuit",), ("zone",), "one_to_many"),
    "thermal.relation.zone_room": (("zone",), ("room",), "one_to_many"),
}
CARDINALITIES = {"one_to_one", "one_to_many", "many_to_many"}
DOMAINS = {
    "thermal_hvac": ("helianthus.pack.thermal", "accepted"),
    "pv_inverter": ("helianthus.pack.pv", "follow_on"),
    "storage_bms": ("helianthus.pack.storage", "follow_on"),
    "evse": ("helianthus.pack.evse", "follow_on"),
    "infrastructure": ("helianthus.pack.infrastructure", "follow_on"),
}
LIFECYCLE = {"source_epoch", "driver_generation", "semantic_revision", "capability_qualification", "activation",
             "generation_fencing", "partial_updates", "stale_unknown_evidence", "last_known_good_retention"}
LOSS = {"native_enum", "precision_range", "multiple_zones_faces", "schedules", "vendor_extensions",
        "unavailable_fields", "conflicting_sources", "unsupported_operations"}
PUBLICATION_POLICY = {
    "admission": ["exact_source_epoch", "current_driver_generation", "exact_semantic_revision",
                  "qualified_active_capability"],
    "stale_generation": "reject",
    "partial_publication": "supplied_valid_only_preserve_permitted_last_known_good",
    "withdrawal": "explicit_generation_fenced",
    "evidence": "stale_unknown_never_promote_or_authorize",
    "tombstone": "retained_non_actionable",
}
PRECONDITIONS = ["current_generation", "qualified_active_capability", "exact_route", "authority_admitted"]
OPERATION_STAGES = ["admission", "dispatch", "acknowledgement", "readback", "terminal_outcome"]
OUTCOMES = ["rejected", "failed_no_contact", "acknowledged_unverified", "applied", "no_effect", "conflict",
            "indeterminate"]
PINS = {
    "semantic_kernel": "da5ab4415d3bec73f9572aec1c495a6cdcbcba47",
    "ebus": "ef076cb03e6cd5612f5dcbe7839e00ab4ee666c9",
    "gree_can": "665a5f22f78c349b5e3063bda158af250a3f44b6",
    "eebus_ledger": "81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1",
    "eebus_m625_donor": "cedf238e34f879815ba773e9cd76b2b31c2822a3",
    "matter_draft": "29b4768a513cf566011ab8cd60df1bc495204953",
}


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_document(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=pairs)


def exact(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label} differs")


def refs(items, label):
    if not isinstance(items, list) or not items:
        raise ValueError(f"{label} must be non-empty")
    got, order = [], []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"]):
            raise ValueError(f"{label} invalid ID")
        if item.get("ref") != {"pack": PACK, "id": item["id"], "version": "1.0.0"}:
            raise ValueError(f"{label} missing exact DefinitionRef owner/version")
        got.append(item["id"])
        order.append(item.get("order"))
    if len(got) != len(set(got)):
        raise ValueError(f"duplicate definition ID in {label}")
    if not all(isinstance(x, int) and x > 0 for x in order) or order != sorted(order) or len(order) != len(set(order)):
        raise ValueError(f"{label} noncanonical order")
    return set(got)


def decimal_pair(value):
    canonical = (
        isinstance(value, dict) and set(value) == {"coefficient", "exponent10"}
        and isinstance(value["coefficient"], str) and re.fullmatch(r"0|-?[1-9][0-9]*", value["coefficient"])
        and isinstance(value["exponent10"], int) and -18 <= value["exponent10"] <= 18
        and (value["coefficient"] != "0" or value["exponent10"] == 0)
        and (value["coefficient"] == "0" or not value["coefficient"].endswith("0"))
    )
    if not canonical:
        raise ValueError("bounds must use canonical kernel Decimal")
    return value["coefficient"], value["exponent10"]


def magnitude(pair):
    coefficient, exponent = pair
    return int(coefficient) * 10 ** exponent if exponent >= 0 else int(coefficient) / 10 ** -exponent



def bound_side(bounds, name, expected):
    if expected is None:
        if name in bounds:
            raise ValueError("field bounds differ from the placement")
        return None
    if name not in bounds:
        raise ValueError("field bounds differ from the placement")
    got = decimal_pair(bounds[name])
    if got != expected:
        raise ValueError("field bounds differ from the placement")
    return got


def reject_unordered(bounds):
    if "minimum" not in bounds or "maximum" not in bounds:
        return
    minimum = decimal_pair(bounds["minimum"])
    maximum = decimal_pair(bounds["maximum"])
    if magnitude(minimum) >= magnitude(maximum):
        raise ValueError("field unordered numeric bounds")


def validate_quantity(field, contract):
    unit = field.get("unit")
    if not isinstance(unit, str) or not ID.fullmatch(unit):
        raise ValueError("field has invalid unit ID")
    if unit not in CANONICAL_UNITS:
        raise ValueError("field unit is outside the canonical SI unit set")
    if not isinstance(contract, tuple) or not contract or not str(contract[0]).startswith("unit."):
        raise ValueError("field kind differs from the placement")
    if unit != contract[0]:
        raise ValueError("field unit differs from the placement")
    if len(contract) == 1:
        if "bounds" in field:
            raise ValueError("field bounds differ from the placement")
        return
    bounds = field.get("bounds", {})
    reject_unordered(bounds)
    bound_side(bounds, "minimum", contract[1])
    bound_side(bounds, "maximum", contract[2])


def check_field_qualifiers(field):
    expected = QUALIFIERS.get(field["id"], ())
    if expected:
        if list(field.get("qualifiers", ())) != list(expected):
            raise ValueError("field qualifiers differ")
        return
    if "qualifiers" in field:
        raise ValueError("field qualifiers differ")


def check_operation_contract(item, caps):
    contract = OPERATION_CONTRACT.get(item["id"])
    if contract is None:
        if "parameters" in item:
            raise ValueError("operation parameters differ")
        return
    capability_id, argument, effect_id, parameters, service = contract
    if item.get("capability") != capability_id:
        raise ValueError("operation capability differs")
    capability = next(cap for cap in caps if cap["id"] == item["capability"])
    same_service = capability.get("service") == service
    if not same_service or capability.get("constraints") != [argument]:
        raise ValueError("operation capability differs")
    same_argument = item.get("arguments") == [argument]
    if not same_argument or item.get("argument_constraints") != [argument]:
        raise ValueError("operation argument differs")
    if item.get("effect_rule") != effect_id:
        raise ValueError("operation effect differs")
    if tuple(item.get("parameters", ())) != tuple(parameters):
        raise ValueError("operation parameters differ")


def validate_qualifier_dimensions(items):
    for item in items:
        value_kind, unit = QUALIFIER_CONTRACT[item["id"]]
        if item.get("value_kind") != value_kind or item.get("unit") != unit:
            raise ValueError("qualifier dimension differs")


def validate_events(items):
    for item in items:
        service, trigger, payload = EVENT_CONTRACT[item["id"]]
        if item.get("service") != service:
            raise ValueError("event service differs")
        if item.get("trigger") != trigger:
            raise ValueError("event trigger differs")
        if tuple(item.get("payload", ())) != tuple(payload):
            raise ValueError("event payload differs")
        if item.get("condition") != "changed" or item.get("origin") != "emitted":
            raise ValueError("event payload differs")




def validate_symbols(field, contract):
    if "unit" in field or "bounds" in field:
        raise ValueError("non-quantity field has quantity-only data")
    if field["kind"] not in {"symbol", "symbols"}:
        return
    symbols = field.get("symbols", [])
    if (not isinstance(symbols, list) or not symbols or symbols != sorted(symbols)
            or any("unknown" in s or "withheld" in s for s in symbols)):
        raise ValueError("field has invalid semantic symbols")
    if symbols != [f"{field['id']}.{name}" for name in contract]:
        raise ValueError("field has invalid semantic symbols")


def validate_field(field):
    if field.get("kind") not in KINDS:
        raise ValueError("field has non-kernel ValueKind")
    dimension = field.get("dimension")
    if not isinstance(dimension, str) or not ID.fullmatch(dimension):
        raise ValueError("field has invalid dimension ID")
    if dimension not in DIMS:
        raise ValueError("field has no resource dimension")
    if not isinstance(field.get("optional"), bool):
        raise ValueError("field lacks optionality")
    subject, contract = FIELD_CONTRACT[field["id"]]
    if field["id"].startswith("thermal.room.mode_") and any(
            isinstance(symbol, str) and symbol.endswith(".comfort") for symbol in field.get("symbols", [])):
        raise ValueError("room mode includes zone comfort")
    if field["kind"] == "quantity":
        validate_quantity(field, contract)
    else:
        validate_symbols(field, contract)
    check_field_qualifiers(field)
    if dimension != f"thermal.dimension.{subject}":
        raise ValueError("field subject differs from the placement")


def validate_relations(relations):
    exact(refs(relations, "relations"), set(RELATION_CONTRACT), "relation catalog")
    for item in relations:
        ends = (item.get("from"), item.get("to"))
        if not all(isinstance(end, list) and end and all(isinstance(x, str) for x in end) for end in ends):
            raise ValueError("relation endpoints must be non-empty dimension lists")
        if any(x not in DIMS for end in ends for x in end) or item.get("cardinality") not in CARDINALITIES:
            raise ValueError("relation dangling dimension or cardinality")
        source, target, cardinality = RELATION_CONTRACT[item["id"]]
        expected = ([f"thermal.dimension.{x}" for x in source], [f"thermal.dimension.{x}" for x in target])
        if ends != expected or item["cardinality"] != cardinality:
            raise ValueError("relation endpoints or cardinality differ from the placement")


def validate_capabilities(caps, services):
    for item in caps:
        if item.get("service") not in services or item.get("activation") != "qualified_current_binding":
            raise ValueError("capability dangling service or activation")
        if item["id"].startswith("thermal.capability.set_") and not isinstance(item.get("constraints"), list):
            raise ValueError("capability lacks exact argument constraint")


def validate_operations(ops, caps, effects, fields):
    capability_ids = {item["id"] for item in caps}
    dimension_of = {field["id"]: field["dimension"] for field in fields}
    for item in ops:
        check_operation_contract(item, caps)
        if (item.get("capability") not in capability_ids or not set(item.get("arguments", [])) <= FIELDS
                or item.get("effect_rule") not in effects):
            raise ValueError("operation dangling reference")
        capability = next(cap for cap in caps if cap["id"] == item["capability"])
        if capability.get("constraints") != item.get("arguments") or item.get("argument_constraints") != item.get(
                "arguments"):
            raise ValueError("operation/capability constraint mismatch")
        if (item.get("preconditions") != PRECONDITIONS or item.get("readback") != "current_generation_exact_effect"
                or item.get("retry") != "forbidden_after_indeterminate"):
            raise ValueError("operation lacks admission/readback")
        if item.get("stages") != OPERATION_STAGES or item.get("terminal_outcomes") != OUTCOMES:
            raise ValueError("operation stages/outcomes are incomplete")
        if item["id"] in ROOM_OPERATIONS:
            capability_id, argument, effect_id = ROOM_OPERATIONS[item["id"]]
            if (item.get("capability") != capability_id or item.get("arguments") != [argument]
                    or item.get("effect_rule") != effect_id or capability.get("service") != "thermal.service.room"
                    or dimension_of.get(argument) != "thermal.dimension.room"):
                raise ValueError("room operation argument is not the room fact")


def validate_portal(portal, services, operations, fields):
    dimension_of = {field["id"]: field["dimension"] for field in fields}
    for item in portal:
        if item.get("kind") == "read":
            if item.get("service") not in services or not set(item.get("fields", [])) <= FIELDS:
                raise ValueError("Portal dangling reference")
            if any(dimension_of.get(x) != SERVICE_DIMENSION[item["service"]] for x in item["fields"]):
                raise ValueError("read descriptor reads another subject than its service")
        if item.get("kind") == "operation" and item.get("operation") not in operations:
            raise ValueError("Portal dangling reference")
    read_fields = {field for item in portal if item.get("kind") == "read" for field in item.get("fields", [])}
    exact(read_fields, FIELDS, "read descriptor field coverage")


def validate_defs(catalog):
    definitions = catalog.get("definitions", {})
    fields = definitions.get("fields")
    exact(refs(fields, "fields"), FIELDS, "field catalog")
    for field in fields:
        validate_field(field)
    exact(refs(definitions.get("fact_dimensions"), "fact dimensions"), DIMS, "fact-key dimension contracts")
    qualifiers = definitions.get("qualifier_dimensions")
    exact(refs(qualifiers, "qualifier dimensions"), set(QUALIFIER_CONTRACT), "qualifier catalog")
    validate_qualifier_dimensions(qualifiers)
    services, caps = definitions.get("services"), definitions.get("capabilities")
    ops, effects, portal = definitions.get("operations"), definitions.get("effect_rules"), definitions.get(
        "portal_contributions")
    exact(refs(services, "services"), SERVICES, "service catalog")
    exact(refs(caps, "capabilities"), CAPS, "capability catalog")
    exact(refs(ops, "operations"), OPS, "operation catalog")
    exact(refs(effects, "effect rules"), EFFECTS, "effect catalog")
    exact(refs(portal, "Portal contributions"), PORTAL, "Portal catalog")
    if any(item.get("fact_key_dimension") != SERVICE_DIMENSION[item["id"]] for item in services):
        raise ValueError("service missing dimension contract")
    validate_relations(definitions.get("relations"))
    validate_capabilities(caps, SERVICES)
    validate_operations(ops, caps, EFFECTS, fields)
    for item in effects:
        if item.get("operation") not in OPS or item.get("fact") not in FIELDS or item.get("operator") != "equal":
            raise ValueError("effect dangling reference")
    events = definitions.get("events")
    exact(refs(events, "events"), set(EVENT_CONTRACT), "event catalog")
    validate_events(events)
    validate_portal(portal, SERVICES, OPS, fields)


def validate_catalog(catalog):
    if (not isinstance(catalog, dict) or catalog.get("pack") != PACK
            or catalog.get("kernel_contract") != "helianthus.semantic.kernel/v1"):
        raise ValueError("catalog lacks exact PackRef")
    domains = {x.get("id"): (x.get("pack"), x.get("state")) for x in catalog.get("domain_catalog", [])
               if isinstance(x, dict)}
    if domains != DOMAINS:
        raise ValueError("five-domain catalog")
    if {x.get("id"): x.get("revision") for x in catalog.get("inputs", []) if isinstance(x, dict)} != PINS:
        raise ValueError("pinned public inputs")
    if set(catalog.get("lifecycle_axes", [])) != LIFECYCLE:
        raise ValueError("lifecycle axes")
    if catalog.get("publication_withdrawal_policy") != PUBLICATION_POLICY:
        raise ValueError("publication/withdrawal policy")
    if set(catalog.get("loss_dispositions", [])) != LOSS:
        raise ValueError("projection-loss coverage")
    mappings = {x.get("native_owner"): x for x in catalog.get("candidate_mappings", []) if isinstance(x, dict)}
    for owner in ("helianthus-docs-ebus", "helianthus-docs-canbus"):
        row = mappings.get(owner, {})
        if row.get("state") != "candidate" or row.get("qualification") != "native_owner_required":
            raise ValueError("native mapping boundary")
    if mappings.get("helianthus-docs-eebus", {}).get("state") != "unknown_pending_normative_source":
        raise ValueError("eeBUS mapping")
    validate_defs(catalog)


def resolve(catalog, path):
    node, parts = catalog, path.split(".")
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node, int(parts[-1]) if isinstance(node, list) else parts[-1]


def mutate(catalog, mutation):
    parent, key = resolve(catalog, mutation["path"])
    if mutation["op"] == "set":
        parent[key] = mutation.get("value")
    elif mutation["op"] == "delete":
        del parent[key]
    elif mutation["op"] == "append_copy":
        parent[key].append(copy.deepcopy(parent[key][mutation["index"]]))
    elif mutation["op"] == "remove_id":
        parent[key][:] = [x for x in parent[key] if (x.get("id") if isinstance(x, dict) else x) != mutation["id"]]
    else:
        raise ValueError("unknown vector mutation")


def check_vector(document, vector):
    candidate = copy.deepcopy(document["catalog"])
    for mutation in vector.get("input", {}).get("mutations", []):
        mutate(candidate, mutation)
    if vector.get("polarity") == "positive":
        validate_catalog(candidate)
        return
    try:
        validate_catalog(candidate)
    except ValueError as error:
        if vector.get("expect", {}).get("error") not in str(error):
            raise ValueError(f"{vector.get('id')}: {error}") from error
    else:
        raise ValueError(f"{vector.get('id')}: accepted")


def validate_document(document):
    if (document.get("contract") != "helianthus.semantic.pack.thermal.acceptance/v1"
            or document.get("pack_contract") != "helianthus.pack.thermal/v1"):
        raise ValueError("contract ID")
    validate_catalog(document.get("catalog"))
    vectors = document.get("vectors", [])
    polarities = {vector.get("polarity") for vector in vectors}
    if not {"positive", "negative"} <= polarities:
        raise ValueError("positive and negative vectors")
    for vector in vectors:
        check_vector(document, vector)


def main():
    document = load_document(VECTORS)
    validate_document(document)
    text = DOCUMENT.read_text(encoding="utf-8")
    for group in document["catalog"]["definitions"].values():
        for item in group:
            if item["id"] not in text:
                raise ValueError(f"document misses {item['id']}")
    print("thermal/HVAC pack v1: PASS")


if __name__ == "__main__":
    main()
