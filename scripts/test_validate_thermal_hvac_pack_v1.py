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
# The ten units of the thermal pack after the admitted hydraulic rows.
PACK_UNITS = {
    "unit.kelvin", "unit.ratio", "unit.cubic_metre_per_second", "unit.pascal",
    "unit.reciprocal_second", "unit.watt", "unit.joule", "unit.one", "unit.second",
    "unit.cubic_metre", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre",
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
FUNCTION = "thermal.dimension.function"
SENSOR = "thermal.dimension.sensor"
RESOURCE_DIMENSIONS = {SYSTEM, ZONE, CIRCUIT, DHW, VENTILATION, GENERATOR, STORE, TERMINAL, REFRIGERANT, COMPRESSOR, "thermal.dimension.pump", ROOM, FUNCTION, SENSOR, "thermal.dimension.valve", "thermal.dimension.solar_circuit", "thermal.dimension.solar_collector", "thermal.dimension.detector", "thermal.dimension.water_tank", "thermal.dimension.fan", "thermal.dimension.air_filter"}
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
    "thermal.action.zone_state": (ZONE, None, None),
    "thermal.calibration.temperature_offset": (ZONE, 'unit.kelvin', None),
    "thermal.configuration.control_sequence": (ZONE, None, None),
    "thermal.configuration.display_unit": (SYSTEM, None, None),
    "thermal.configuration.emergency_heat_delta": (ZONE, 'unit.kelvin', None),
    "thermal.configuration.keypad_lockout": (SYSTEM, None, None),
    "thermal.configuration.remote_sensing": (ZONE, None, None),
    "thermal.configuration.schedule_programming": (SYSTEM, None, None),
    "thermal.demand.cooling": (ZONE, 'unit.ratio', (Fraction(0, 1), Fraction(1, 1))),
    "thermal.demand.heating": (ZONE, 'unit.ratio', (Fraction(0, 1), Fraction(1, 1))),
    "thermal.hold.duration": (ZONE, 'unit.second', None),
    "thermal.hold.expiry": (ZONE, None, None),
    "thermal.hold.setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.hold.state": (ZONE, None, None),
    "thermal.limit.absolute_maximum_cooling_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.absolute_maximum_heating_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.absolute_minimum_cooling_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.absolute_minimum_heating_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.maximum_cooling_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.maximum_heating_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.minimum_cooling_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.minimum_heating_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.limit.minimum_setpoint_deadband": (ZONE, 'unit.kelvin', (Fraction(0, 1), Fraction(127, 10))),
    "thermal.limit.setpoint_step": (ZONE, 'unit.kelvin', None),
    "thermal.measurement.sensor_humidity": (SENSOR, 'unit.ratio', None),
    "thermal.measurement.sensor_temperature": (SENSOR, 'unit.kelvin', None),
    "thermal.mode.zone_cooling": (ZONE, None, None),
    "thermal.preset.active_handle": (ZONE, None, None),
    "thermal.preset.built_in": (ZONE, None, None),
    "thermal.preset.cooling_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.preset.heating_setpoint": (ZONE, 'unit.kelvin', None),
    "thermal.preset.maximum_count": (ZONE, 'unit.one', (Fraction(1, 1), None)),
    "thermal.preset.name": (ZONE, None, None),
    "thermal.preset.scenario": (ZONE, None, None),
    "thermal.preset.supported_scenarios": (ZONE, None, None),
    "thermal.program.active_handle": (FUNCTION, None, None),
    "thermal.program.built_in": (FUNCTION, None, None),
    "thermal.program.entry_cooling_setpoint": (FUNCTION, 'unit.kelvin', None),
    "thermal.program.entry_days": (FUNCTION, None, None),
    "thermal.program.entry_end": (FUNCTION, 'unit.second', None),
    "thermal.program.entry_heating_setpoint": (FUNCTION, 'unit.kelvin', None),
    "thermal.program.entry_preset": (FUNCTION, None, None),
    "thermal.program.entry_start": (FUNCTION, 'unit.second', None),
    "thermal.program.entry_state": (FUNCTION, None, None),
    "thermal.program.entry_system_mode": (FUNCTION, None, None),
    "thermal.program.maximum_count": (FUNCTION, 'unit.one', (Fraction(1, 1), None)),
    "thermal.program.maximum_entries": (FUNCTION, 'unit.one', (Fraction(1, 1), None)),
    "thermal.program.maximum_entries_per_day": (FUNCTION, 'unit.one', (Fraction(1, 1), None)),
    "thermal.program.name": (FUNCTION, None, None),
    "thermal.program.preset": (FUNCTION, None, None),
    "thermal.program.supported_types": (FUNCTION, None, None),
    "thermal.program.system_mode": (FUNCTION, None, None),
    "thermal.setpoint.change_amount": (ZONE, 'unit.kelvin', None),
    "thermal.setpoint.change_source": (ZONE, None, None),
    "thermal.setpoint.change_time": (ZONE, None, None),
    "thermal.status.occupancy": (ZONE, None, None),
    "thermal.status.window": (ZONE, None, None),
    "thermal.status.zone_running_state": (ZONE, None, None),
    "thermal.suggestion.active": (ZONE, None, None),
    "thermal.suggestion.current": (ZONE, 'unit.one', None),
    "thermal.suggestion.effective_time": (ZONE, None, None),
    "thermal.suggestion.expiration": (ZONE, None, None),
    "thermal.suggestion.maximum_count": (ZONE, 'unit.one', (Fraction(5, 1), None)),
    "thermal.suggestion.not_following_reason": (ZONE, None, None),
    "thermal.suggestion.preset": (ZONE, None, None),
    "thermal.mode.dhw": ("thermal.dimension.dhw", None, None),
    "thermal.mode.dhw_supported": ("thermal.dimension.dhw", None, None),
    "thermal.dhw.heater_types": ("thermal.dimension.dhw", None, None),
    "thermal.dhw.heat_demand": ("thermal.dimension.dhw", None, None),
    "thermal.dhw.estimated_heat_required": ("thermal.dimension.dhw", 'unit.joule', (Fraction(0), None)),
    "thermal.dhw.charge_ratio": ("thermal.dimension.dhw", 'unit.ratio', (None, Fraction(1))),
    "thermal.dhw.boost_state": ("thermal.dimension.dhw", None, None),
    "thermal.dhw.boost_duration": ("thermal.dimension.dhw", 'unit.second', (Fraction(1), None)),
    "thermal.dhw.boost_one_shot": ("thermal.dimension.dhw", None, None),
    "thermal.dhw.boost_emergency": ("thermal.dimension.dhw", None, None),
    "thermal.dhw.boost_temporary_setpoint": ("thermal.dimension.dhw", 'unit.kelvin', None),
    "thermal.dhw.boost_target_ratio": ("thermal.dimension.dhw", 'unit.ratio', (None, Fraction(1))),
    "thermal.dhw.boost_target_reheat_ratio": ("thermal.dimension.dhw", 'unit.ratio', None),
    "thermal.measurement.dhw_flow_rate": ("thermal.dimension.dhw", 'unit.cubic_metre_per_second', None),
    "thermal.measurement.dhw_circuit_flow_temperature": ("thermal.dimension.dhw", 'unit.kelvin', None),
    "thermal.measurement.dhw_circuit_return_temperature": ("thermal.dimension.dhw", 'unit.kelvin', None),
    "thermal.nameplate.store_volume": ("thermal.dimension.thermal_store", 'unit.cubic_metre', None),
    "thermal.measurement.store_top_temperature": ("thermal.dimension.thermal_store", 'unit.kelvin', None),
    "thermal.measurement.store_bottom_temperature": ("thermal.dimension.thermal_store", 'unit.kelvin', None),
    "thermal.status.pump_running": ("thermal.dimension.pump", None, None),
    "thermal.status.pump": ("thermal.dimension.pump", None, None),
    "thermal.status.pump_alarms": ("thermal.dimension.pump", None, None),
    "thermal.mode.pump_operation": ("thermal.dimension.pump", None, None),
    "thermal.mode.pump_effective_operation": ("thermal.dimension.pump", None, None),
    "thermal.mode.pump_control": ("thermal.dimension.pump", None, None),
    "thermal.mode.pump_effective_control": ("thermal.dimension.pump", None, None),
    "thermal.measurement.pump_capacity": ("thermal.dimension.pump", 'unit.ratio', None),
    "thermal.setpoint.pump_level": ("thermal.dimension.pump", 'unit.ratio', None),
    "thermal.measurement.pump_running_time": ("thermal.dimension.pump", 'unit.second', None),
    "thermal.measurement.pump_power": ("thermal.dimension.pump", 'unit.watt', None),
    "thermal.energy.pump_consumed": ("thermal.dimension.pump", 'unit.joule', None),
    "thermal.measurement.pump_flow_rate": ("thermal.dimension.pump", 'unit.cubic_metre_per_second', None),
    "thermal.measurement.pump_pressure": ("thermal.dimension.pump", 'unit.pascal', None),
    "thermal.measurement.pump_medium_temperature": ("thermal.dimension.pump", 'unit.kelvin', None),
    "thermal.nameplate.pump_maximum_pressure": ("thermal.dimension.pump", 'unit.pascal', None),
    "thermal.nameplate.pump_maximum_speed": ("thermal.dimension.pump", 'unit.reciprocal_second', None),
    "thermal.nameplate.pump_maximum_flow": ("thermal.dimension.pump", 'unit.cubic_metre_per_second', None),
    "thermal.nameplate.pump_minimum_constant_pressure": ("thermal.dimension.pump", 'unit.pascal', None),
    "thermal.nameplate.pump_maximum_constant_pressure": ("thermal.dimension.pump", 'unit.pascal', None),
    "thermal.nameplate.pump_minimum_compensated_pressure": ("thermal.dimension.pump", 'unit.pascal', None),
    "thermal.nameplate.pump_maximum_compensated_pressure": ("thermal.dimension.pump", 'unit.pascal', None),
    "thermal.nameplate.pump_minimum_constant_speed": ("thermal.dimension.pump", 'unit.reciprocal_second', None),
    "thermal.nameplate.pump_maximum_constant_speed": ("thermal.dimension.pump", 'unit.reciprocal_second', None),
    "thermal.nameplate.pump_minimum_constant_flow": ("thermal.dimension.pump", 'unit.cubic_metre_per_second', None),
    "thermal.nameplate.pump_maximum_constant_flow": ("thermal.dimension.pump", 'unit.cubic_metre_per_second', None),
    "thermal.nameplate.pump_minimum_constant_temperature": ("thermal.dimension.pump", 'unit.kelvin', None),
    "thermal.nameplate.pump_maximum_constant_temperature": ("thermal.dimension.pump", 'unit.kelvin', None),
    "thermal.status.valve_state": ("thermal.dimension.valve", None, None),
    "thermal.setpoint.valve_target_state": ("thermal.dimension.valve", None, None),
    "thermal.measurement.valve_level": ("thermal.dimension.valve", 'unit.ratio', (None, Fraction(1))),
    "thermal.setpoint.valve_target_level": ("thermal.dimension.valve", 'unit.ratio', (None, Fraction(1))),
    "thermal.configuration.valve_default_open_level": ("thermal.dimension.valve", 'unit.ratio', (Fraction(1, 100), Fraction(1))),
    "thermal.configuration.valve_level_step": ("thermal.dimension.valve", 'unit.ratio', None),
    "thermal.valve.open_duration": ("thermal.dimension.valve", 'unit.second', (Fraction(1), None)),
    "thermal.configuration.valve_default_open_duration": ("thermal.dimension.valve", 'unit.second', (Fraction(1), None)),
    "thermal.valve.auto_close_time": ("thermal.dimension.valve", None, None),
    "thermal.valve.remaining_duration": ("thermal.dimension.valve", 'unit.second', None),
    "thermal.status.valve_faults": ("thermal.dimension.valve", None, None),
    "thermal.measurement.valve_flow_rate": ("thermal.dimension.valve", 'unit.cubic_metre_per_second', None),
    "thermal.measurement.system_water_pressure": ("thermal.dimension.system", 'unit.pascal', None),
    "thermal.measurement.circuit_water_pressure": ("thermal.dimension.circuit", 'unit.pascal', None),
    "thermal.measurement.heat_generator_flow_rate": ("thermal.dimension.heat_generator", 'unit.cubic_metre_per_second', None),
    "thermal.measurement.circuit_return_temperature": ("thermal.dimension.circuit", 'unit.kelvin', None),
    "thermal.measurement.dew_point": ("thermal.dimension.circuit", 'unit.kelvin', None),
    "thermal.measurement.circuit_humidity": ("thermal.dimension.circuit", 'unit.ratio', None),
    "thermal.measurement.collector_temperature": ("thermal.dimension.solar_collector", 'unit.kelvin', None),
    "thermal.measurement.solar_flow_temperature": ("thermal.dimension.solar_circuit", 'unit.kelvin', None),
    "thermal.measurement.solar_return_temperature": ("thermal.dimension.solar_circuit", 'unit.kelvin', None),
    "thermal.measurement.solar_power": ("thermal.dimension.solar_circuit", 'unit.watt', None),
    "thermal.status.leak": ("thermal.dimension.detector", None, None),
    "thermal.status.freeze": ("thermal.dimension.detector", None, None),
    "thermal.detector.sensitivity_level": ("thermal.dimension.detector", 'unit.one', None),
    "thermal.detector.supported_sensitivity_levels": ("thermal.dimension.detector", 'unit.one', None),
    "thermal.detector.default_sensitivity_level": ("thermal.dimension.detector", 'unit.one', None),
    "thermal.detector.alarms_active": ("thermal.dimension.detector", None, None),
    "thermal.detector.alarms_suppressed": ("thermal.dimension.detector", None, None),
    "thermal.detector.alarms_enabled": ("thermal.dimension.detector", None, None),
    "thermal.detector.alarms_supported": ("thermal.dimension.detector", None, None),
    "thermal.detector.sensor_fault": ("thermal.dimension.detector", None, None),
    "thermal.water_tank.condition": ("thermal.dimension.water_tank", 'unit.ratio', (None, Fraction(1))),
    "thermal.water_tank.degradation_direction": ("thermal.dimension.water_tank", None, None),
    "thermal.water_tank.change_indication": ("thermal.dimension.water_tank", None, None),
    "thermal.water_tank.in_place": ("thermal.dimension.water_tank", None, None),
    "thermal.water_tank.last_changed": ("thermal.dimension.water_tank", None, None),
    "thermal.water_tank.replacement_product_identifier": ("thermal.dimension.water_tank", None, None),
    "thermal.measurement.electrical_power": (GENERATOR, 'unit.watt', None),
    "thermal.energy.electrical_consumed": (GENERATOR, 'unit.joule', None),
    "thermal.energy.solar_yield": ("thermal.dimension.solar_circuit", 'unit.joule', None),
    "thermal.setpoint.heat_generator_flow_temperature": (GENERATOR, 'unit.kelvin', None),
    "thermal.setpoint.circuit_flow_temperature": (CIRCUIT, 'unit.kelvin', None),
    "thermal.setpoint.circuit_fixed_flow_temperature": (CIRCUIT, 'unit.kelvin', None),
    "thermal.limit.circuit_flow_temperature_minimum": (CIRCUIT, 'unit.kelvin', None),
    "thermal.limit.circuit_flow_temperature_maximum": (CIRCUIT, 'unit.kelvin', None),
    "thermal.measurement.outdoor_air_temperature_average": (SYSTEM, 'unit.kelvin', None),
    "thermal.status.terminal_unit_power": (TERMINAL, None, None),
    "thermal.measurement.terminal_unit_air_temperature": (TERMINAL, 'unit.kelvin', None),
    "thermal.measurement.terminal_unit_humidity": (TERMINAL, 'unit.ratio', None),
    "thermal.setpoint.terminal_unit_heating": (TERMINAL, 'unit.kelvin', None),
    "thermal.setpoint.terminal_unit_cooling": (TERMINAL, 'unit.kelvin', None),
    "thermal.measurement.coil_temperature": (TERMINAL, 'unit.kelvin', None),
    "thermal.configuration.ac_type": (TERMINAL, None, None),
    "thermal.nameplate.cooling_capacity": (TERMINAL, 'unit.watt', None),
    "thermal.configuration.refrigerant_type": (TERMINAL, None, None),
    "thermal.configuration.compressor_type": (TERMINAL, None, None),
    "thermal.status.terminal_unit_errors": (TERMINAL, None, None),
    "thermal.measurement.louver_position": (TERMINAL, None, None),
    "thermal.fan.mode": ("thermal.dimension.fan", None, None),
    "thermal.fan.mode_sequence": ("thermal.dimension.fan", None, None),
    "thermal.fan.speed_setting": ("thermal.dimension.fan", 'unit.ratio', (None, Fraction(1))),
    "thermal.fan.speed_ratio": ("thermal.dimension.fan", 'unit.ratio', (None, Fraction(1))),
    "thermal.fan.speed_step_maximum": ("thermal.dimension.fan", 'unit.one', (Fraction(1), Fraction(100))),
    "thermal.fan.speed_step_setting": ("thermal.dimension.fan", 'unit.one', None),
    "thermal.fan.speed_step": ("thermal.dimension.fan", 'unit.one', None),
    "thermal.fan.rock_support": ("thermal.dimension.fan", None, None),
    "thermal.fan.rock_setting": ("thermal.dimension.fan", None, None),
    "thermal.fan.wind_support": ("thermal.dimension.fan", None, None),
    "thermal.fan.wind_setting": ("thermal.dimension.fan", None, None),
    "thermal.fan.airflow_direction": ("thermal.dimension.fan", None, None),
    "thermal.mode.ventilation": (VENTILATION, None, None),
    "thermal.measurement.supply_air_flow": (VENTILATION, 'unit.cubic_metre_per_second', None),
    "thermal.measurement.extract_air_flow": (VENTILATION, 'unit.cubic_metre_per_second', None),
    "thermal.measurement.supply_air_temperature": (VENTILATION, 'unit.kelvin', None),
    "thermal.measurement.extract_air_temperature": (VENTILATION, 'unit.kelvin', None),
    "thermal.measurement.outdoor_intake_air_temperature": (VENTILATION, 'unit.kelvin', None),
    "thermal.measurement.exhaust_air_temperature": (VENTILATION, 'unit.kelvin', None),
    "thermal.filter.kind": ("thermal.dimension.air_filter", None, None),
    "thermal.filter.condition": ("thermal.dimension.air_filter", 'unit.ratio', (None, Fraction(1))),
    "thermal.filter.degradation_direction": ("thermal.dimension.air_filter", None, None),
    "thermal.filter.change_indication": ("thermal.dimension.air_filter", None, None),
    "thermal.filter.in_place": ("thermal.dimension.air_filter", None, None),
    "thermal.filter.last_changed": ("thermal.dimension.air_filter", None, None),
    "thermal.filter.replacement_product_kind": ("thermal.dimension.air_filter", None, None),
    "thermal.filter.replacement_product_identifier": ("thermal.dimension.air_filter", None, None),
    "thermal.measurement.air_quality": (ZONE, None, None),
    "thermal.air.volume_fraction": (ZONE, 'unit.ratio', None),
    "thermal.air.mass_concentration": (ZONE, 'unit.kilogram_per_cubic_metre', None),
    "thermal.air.radon_concentration": (ZONE, 'unit.becquerel_per_cubic_metre', None),
    "thermal.air.statistic_window": (ZONE, 'unit.second', (None, Fraction(604800))),
    "thermal.air.level": (ZONE, None, None),
    "thermal.air.uncertainty": (ZONE, 'unit.ratio', None),
    "thermal.air.measurement_medium": (ZONE, None, None),
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


def assert_field_bounds(identifier, field, bounds):
    if bounds is None:
        if "bounds" in field:
            raise AssertionError(f"{identifier} is a symbol with bounds")
        return
    expected_keys = set()
    if bounds[0] is not None:
        expected_keys.add("minimum")
    if bounds[1] is not None:
        expected_keys.add("maximum")
    if set(field.get("bounds", {})) != expected_keys:
        raise AssertionError(f"{identifier} bounds differ from the placement")
    for side, expected in (("minimum", bounds[0]), ("maximum", bounds[1])):
        if expected is None:
            continue
        if exact_value(field["bounds"][side]) != expected:
            raise AssertionError(f"{identifier} bounds differ from {bounds}")


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
        assert_field_bounds(identifier, field, bounds)
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


def removed_present(text: str, identifier: str) -> bool:
    """True when the removed id is its own token.

    thermal.configuration.display_unit.celsius is an admitted symbol. It
    contains the removed unit name only as part of that longer identifier.
    """
    if identifier.startswith('"'):
        return identifier in text
    start = 0
    while True:
        found = text.find(identifier, start)
        if found < 0:
            return False
        before = text[found - 1] if found else " "
        end = found + len(identifier)
        after = text[end] if end < len(text) else " "
        if (before not in "abcdefghijklmnopqrstuvwxyz0123456789_"
                and after not in "abcdefghijklmnopqrstuvwxyz0123456789_"):
            return True
        start = found + 1


def check_removed() -> None:
    for path in (validator.VECTORS, validator.DOCUMENT, Path(validator.__file__)):
        text = path.read_text(encoding="utf-8")
        found = [identifier for identifier in REMOVED if removed_present(text, identifier)]
        if found:
            raise AssertionError(f"{path.name} still names {found}")
    print("removed_identifiers_absent: PASS")


def absent_side_decimal(present: dict | None, side: str) -> dict:
    """Canonical decimal that stays strictly ordered against the present side."""
    if present is None:
        return {"coefficient": "9", "exponent10": 0}
    step = -1 if side == "minimum" else 1
    coefficient = int(present["coefficient"]) + step
    if coefficient == 0 or str(coefficient).endswith("0"):
        coefficient += step
    exponent = 0 if coefficient == 0 else present["exponent10"]
    return {"coefficient": str(coefficient), "exponent10": exponent}


def reject_one_sided(document, index, bounds):
    """Shift the present side and insert the absent side."""
    count = 0
    for side, expected in (("minimum", bounds[0]), ("maximum", bounds[1])):
        if expected is None:
            inserted = copy.deepcopy(document)
            field_bounds = definitions(inserted)["fields"][index].setdefault("bounds", {})
            other = "maximum" if side == "minimum" else "minimum"
            field_bounds[side] = absent_side_decimal(field_bounds.get(other), side)
            reject(inserted, "field bounds differ")
            count += 1
            continue
        shifted = copy.deepcopy(document)
        _shift_bound(definitions(shifted)["fields"][index]["bounds"][side], side)
        reject(shifted, "field bounds differ")
        count += 1
    return count


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
        if bounds[0] is None or bounds[1] is None:
            count += reject_one_sided(document, index, bounds)
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
    extra["order"] = max(item["order"] for item in definitions(document)["fields"]) + 1
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


ADMITTED_PUMP_ACTUATION = {
    "thermal.capability.set_pump_control_mode",
    "thermal.capability.set_pump_level",
    "thermal.capability.set_pump_operation_mode",
    "thermal.capability.set_pump_running",
    "thermal.operation.set_pump_control_mode",
    "thermal.operation.set_pump_level",
    "thermal.operation.set_pump_operation_mode",
    "thermal.operation.set_pump_running",
}


def assert_admitted_pump_actuation(services: dict, capabilities: set, document: dict) -> None:
    service = services[PUMP_SERVICE]
    if service.get("fact_key_dimension") != PUMP:
        raise AssertionError("pump service is not keyed on the pump dimension")
    operations = {item["id"] for item in definitions(document)["operations"]}
    actuation = {item for item in capabilities | operations if "pump" in item}
    if actuation != ADMITTED_PUMP_ACTUATION or "thermal.capability.read.pump" in capabilities:
        raise AssertionError("pump actuation is not the admitted set")
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
    assert_admitted_pump_actuation(services, capabilities, document)
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


PE04_FIELDS = ('thermal.action.zone_state', 'thermal.calibration.temperature_offset', 'thermal.configuration.control_sequence', 'thermal.configuration.display_unit', 'thermal.configuration.emergency_heat_delta', 'thermal.configuration.keypad_lockout', 'thermal.configuration.remote_sensing', 'thermal.configuration.schedule_programming', 'thermal.demand.cooling', 'thermal.demand.heating', 'thermal.hold.duration', 'thermal.hold.expiry', 'thermal.hold.setpoint', 'thermal.hold.state', 'thermal.limit.absolute_maximum_cooling_setpoint', 'thermal.limit.absolute_maximum_heating_setpoint', 'thermal.limit.absolute_minimum_cooling_setpoint', 'thermal.limit.absolute_minimum_heating_setpoint', 'thermal.limit.maximum_cooling_setpoint', 'thermal.limit.maximum_heating_setpoint', 'thermal.limit.minimum_cooling_setpoint', 'thermal.limit.minimum_heating_setpoint', 'thermal.limit.minimum_setpoint_deadband', 'thermal.limit.setpoint_step', 'thermal.measurement.sensor_humidity', 'thermal.measurement.sensor_temperature', 'thermal.mode.zone_cooling', 'thermal.preset.active_handle', 'thermal.preset.built_in', 'thermal.preset.cooling_setpoint', 'thermal.preset.heating_setpoint', 'thermal.preset.maximum_count', 'thermal.preset.name', 'thermal.preset.scenario', 'thermal.preset.supported_scenarios', 'thermal.program.active_handle', 'thermal.program.built_in', 'thermal.program.entry_cooling_setpoint', 'thermal.program.entry_days', 'thermal.program.entry_end', 'thermal.program.entry_heating_setpoint', 'thermal.program.entry_preset', 'thermal.program.entry_start', 'thermal.program.entry_state', 'thermal.program.entry_system_mode', 'thermal.program.maximum_count', 'thermal.program.maximum_entries', 'thermal.program.maximum_entries_per_day', 'thermal.program.name', 'thermal.program.preset', 'thermal.program.supported_types', 'thermal.program.system_mode', 'thermal.setpoint.change_amount', 'thermal.setpoint.change_source', 'thermal.setpoint.change_time', 'thermal.status.occupancy', 'thermal.status.window', 'thermal.status.zone_running_state', 'thermal.suggestion.active', 'thermal.suggestion.current', 'thermal.suggestion.effective_time', 'thermal.suggestion.expiration', 'thermal.suggestion.maximum_count', 'thermal.suggestion.not_following_reason', 'thermal.suggestion.preset')
PE04_SYMBOLS = {'thermal.mode.zone': ('auto', 'comfort', 'eco', 'off', 'on'), 'thermal.action.zone_state': ('cooling', 'dehumidifying', 'heating', 'idle', 'ventilating'), 'thermal.configuration.control_sequence': ('cooling_and_heating', 'cooling_and_heating_with_reheat', 'cooling_only', 'cooling_with_reheat', 'heating_only', 'heating_with_reheat'), 'thermal.configuration.display_unit': ('celsius', 'fahrenheit'), 'thermal.configuration.keypad_lockout': ('level_1', 'level_2', 'level_3', 'level_4', 'level_5', 'none'), 'thermal.configuration.remote_sensing': ('local_temperature', 'occupancy', 'outdoor_temperature'), 'thermal.configuration.schedule_programming': ('denied', 'permitted'), 'thermal.hold.state': ('off', 'on'), 'thermal.mode.zone_cooling': ('auto', 'eco', 'off', 'on'), 'thermal.preset.scenario': ('going_to_sleep', 'occupied', 'sleep', 'unoccupied', 'user_defined', 'vacation', 'wake'), 'thermal.preset.supported_scenarios': ('going_to_sleep', 'occupied', 'sleep', 'unoccupied', 'user_defined', 'vacation', 'wake'), 'thermal.program.entry_days': ('away', 'friday', 'monday', 'saturday', 'sunday', 'thursday', 'tuesday', 'wednesday'), 'thermal.program.entry_state': ('off', 'on'), 'thermal.program.entry_system_mode': ('auto', 'cool', 'heat', 'off'), 'thermal.program.supported_types': ('names', 'off', 'presets', 'setpoints'), 'thermal.program.system_mode': ('auto', 'cool', 'heat', 'off'), 'thermal.setpoint.change_source': ('external', 'manual', 'schedule'), 'thermal.status.occupancy': ('occupied', 'unoccupied'), 'thermal.status.window': ('closed', 'open'), 'thermal.status.zone_running_state': ('cool', 'cool_stage_2', 'fan', 'fan_stage_2', 'fan_stage_3', 'heat', 'heat_stage_2'), 'thermal.suggestion.not_following_reason': ('conflicting_suggestions', 'demand_response_event', 'occupancy', 'ongoing_hold', 'preconditioning_mode', 'schedule', 'time_of_use_cost_savings', 'vacation_mode')}
PE04_QUALIFIERS = {'thermal.preset.built_in': ('thermal.dimension.preset',), 'thermal.preset.cooling_setpoint': ('thermal.dimension.preset',), 'thermal.preset.heating_setpoint': ('thermal.dimension.preset',), 'thermal.preset.name': ('thermal.dimension.preset',), 'thermal.preset.scenario': ('thermal.dimension.preset',), 'thermal.program.built_in': ('thermal.dimension.time_program',), 'thermal.program.entry_cooling_setpoint': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_days': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_end': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_heating_setpoint': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_preset': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_start': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_state': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.entry_system_mode': ('thermal.dimension.program_entry', 'thermal.dimension.time_program'), 'thermal.program.name': ('thermal.dimension.time_program',), 'thermal.program.preset': ('thermal.dimension.time_program',), 'thermal.program.system_mode': ('thermal.dimension.time_program',), 'thermal.suggestion.active': ('thermal.dimension.suggestion',), 'thermal.suggestion.effective_time': ('thermal.dimension.suggestion',), 'thermal.suggestion.expiration': ('thermal.dimension.suggestion',), 'thermal.suggestion.preset': ('thermal.dimension.suggestion',)}
PE04_OPERATIONS = {'thermal.operation.set_active_preset': ('thermal.capability.set_active_preset', 'thermal.preset.active_handle', 'thermal.effect.set_active_preset', ()), 'thermal.operation.set_active_program': ('thermal.capability.set_active_program', 'thermal.program.active_handle', 'thermal.effect.set_active_program', ()), 'thermal.operation.set_control_sequence': ('thermal.capability.set_control_sequence', 'thermal.configuration.control_sequence', 'thermal.effect.set_control_sequence', ()), 'thermal.operation.set_display_unit': ('thermal.capability.set_display_unit', 'thermal.configuration.display_unit', 'thermal.effect.set_display_unit', ()), 'thermal.operation.set_emergency_heat_delta': ('thermal.capability.set_emergency_heat_delta', 'thermal.configuration.emergency_heat_delta', 'thermal.effect.set_emergency_heat_delta', ()), 'thermal.operation.set_hold': ('thermal.capability.set_hold', 'thermal.hold.state', 'thermal.effect.set_hold', ('thermal.hold.duration', 'thermal.hold.setpoint')), 'thermal.operation.set_keypad_lockout': ('thermal.capability.set_keypad_lockout', 'thermal.configuration.keypad_lockout', 'thermal.effect.set_keypad_lockout', ()), 'thermal.operation.set_maximum_cooling_setpoint': ('thermal.capability.set_maximum_cooling_setpoint', 'thermal.limit.maximum_cooling_setpoint', 'thermal.effect.set_maximum_cooling_setpoint', ()), 'thermal.operation.set_maximum_heating_setpoint': ('thermal.capability.set_maximum_heating_setpoint', 'thermal.limit.maximum_heating_setpoint', 'thermal.effect.set_maximum_heating_setpoint', ()), 'thermal.operation.set_minimum_cooling_setpoint': ('thermal.capability.set_minimum_cooling_setpoint', 'thermal.limit.minimum_cooling_setpoint', 'thermal.effect.set_minimum_cooling_setpoint', ()), 'thermal.operation.set_minimum_heating_setpoint': ('thermal.capability.set_minimum_heating_setpoint', 'thermal.limit.minimum_heating_setpoint', 'thermal.effect.set_minimum_heating_setpoint', ()), 'thermal.operation.set_occupied_cooling': ('thermal.capability.set_occupied_cooling', 'thermal.setpoint.occupied_cooling', 'thermal.effect.set_occupied_cooling', ()), 'thermal.operation.set_occupied_heating': ('thermal.capability.set_occupied_heating', 'thermal.setpoint.occupied_heating', 'thermal.effect.set_occupied_heating', ()), 'thermal.operation.set_preset': ('thermal.capability.set_preset', 'thermal.preset.heating_setpoint', 'thermal.effect.set_preset', ('thermal.preset.cooling_setpoint', 'thermal.preset.name', 'thermal.preset.scenario')), 'thermal.operation.set_program_entry': ('thermal.capability.set_program_entry', 'thermal.program.entry_start', 'thermal.effect.set_program_entry', ('thermal.program.entry_cooling_setpoint', 'thermal.program.entry_days', 'thermal.program.entry_end', 'thermal.program.entry_heating_setpoint', 'thermal.program.entry_preset', 'thermal.program.entry_state', 'thermal.program.entry_system_mode')), 'thermal.operation.set_remote_sensing': ('thermal.capability.set_remote_sensing', 'thermal.configuration.remote_sensing', 'thermal.effect.set_remote_sensing', ()), 'thermal.operation.set_schedule_programming': ('thermal.capability.set_schedule_programming', 'thermal.configuration.schedule_programming', 'thermal.effect.set_schedule_programming', ()), 'thermal.operation.set_suggestion': ('thermal.capability.set_suggestion', 'thermal.suggestion.active', 'thermal.effect.set_suggestion', ('thermal.suggestion.effective_time', 'thermal.suggestion.expiration', 'thermal.suggestion.preset')), 'thermal.operation.set_temperature_calibration': ('thermal.capability.set_temperature_calibration', 'thermal.calibration.temperature_offset', 'thermal.effect.set_temperature_calibration', ()), 'thermal.operation.set_unoccupied_cooling': ('thermal.capability.set_unoccupied_cooling', 'thermal.setpoint.unoccupied_cooling', 'thermal.effect.set_unoccupied_cooling', ()), 'thermal.operation.set_unoccupied_heating': ('thermal.capability.set_unoccupied_heating', 'thermal.setpoint.unoccupied_heating', 'thermal.effect.set_unoccupied_heating', ()), 'thermal.operation.set_zone_cooling_mode': ('thermal.capability.set_zone_cooling_mode', 'thermal.mode.zone_cooling', 'thermal.effect.set_zone_cooling_mode', ()), 'thermal.operation.set_zone_mode': ('thermal.capability.set_zone_mode', 'thermal.mode.zone', 'thermal.effect.set_zone_mode', ())}
PE04_EVENTS = {'thermal.event.active_preset_changed': ('thermal.service.zone', 'thermal.preset.active_handle', ()), 'thermal.event.active_program_changed': ('thermal.service.function', 'thermal.program.active_handle', ()), 'thermal.event.local_temperature_changed': ('thermal.service.zone', 'thermal.measurement.air_temperature', ()), 'thermal.event.occupancy_changed': ('thermal.service.zone', 'thermal.status.occupancy', ()), 'thermal.event.running_mode_changed': ('thermal.service.zone', 'thermal.action.zone_state', ()), 'thermal.event.running_state_changed': ('thermal.service.zone', 'thermal.status.zone_running_state', ()), 'thermal.event.setpoint_changed': ('thermal.service.zone', 'thermal.setpoint.occupied_heating', ('thermal.setpoint.change_amount', 'thermal.setpoint.change_source')), 'thermal.event.system_mode_changed': ('thermal.service.system', 'thermal.mode.system', ())}
PE04_QUALIFIER_DIMENSIONS = {'thermal.dimension.preset': ('text', None), 'thermal.dimension.program_entry': ('quantity', 'unit.one'), 'thermal.dimension.suggestion': ('quantity', 'unit.one'), 'thermal.dimension.time_program': ('text', None)}

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


def check_pe04_symbols(fields: dict) -> None:
    for ident, tokens in PE04_SYMBOLS.items():
        expected = [f"{ident}.{token}" for token in tokens]
        if fields[ident].get("symbols") != expected:
            raise AssertionError(f"{ident} symbols differ")


def check_pe04_qualifiers(fields: dict) -> None:
    for ident, quals in PE04_QUALIFIERS.items():
        if list(fields[ident].get("qualifiers", ())) != list(quals):
            raise AssertionError(f"{ident} qualifiers differ")


def check_pe04_operations(document: dict) -> None:
    operations = {item["id"]: item for item in definitions(document)["operations"]}
    for ident, (cap, arg, effect, params) in PE04_OPERATIONS.items():
        item = operations[ident]
        observed = (
            item["capability"], item["arguments"], item["effect_rule"],
            tuple(item.get("parameters", ())),
        )
        if observed != (cap, [arg], effect, params):
            raise AssertionError(f"{ident} operation identity differs")


def check_pe04_events(document: dict) -> None:
    events = {item["id"]: item for item in definitions(document)["events"]}
    for ident, (service, trigger, payload) in PE04_EVENTS.items():
        item = events[ident]
        if (item["service"], item["trigger"], tuple(item["payload"])) != (service, trigger, payload):
            raise AssertionError(f"{ident} event identity differs")


def check_pe04(document: dict) -> None:
    """Admitted zone, function and sensor rows stay, and the two excluded rows do not."""
    fields = {field["id"]: field for field in definitions(document)["fields"]}
    if "thermal.limit.humidity_maximum" in fields:
        raise AssertionError("humidity maximum is a member")
    relations = {item["id"] for item in definitions(document)["relations"]}
    if "thermal.relation.sensor_zone" in relations:
        raise AssertionError("sensor zone relation is a member")
    missing = [ident for ident in PE04_FIELDS if ident not in fields]
    if missing:
        raise AssertionError(f"admitted fields absent: {missing}")
    check_pe04_symbols(fields)
    check_pe04_qualifiers(fields)
    check_pe04_operations(document)
    check_pe04_events(document)
    for ident in ROOM_QUANTITIES + ROOM_MODES:
        if ident not in fields:
            raise AssertionError(f"room id left the pack: {ident}")
    print("pe04_identity: PASS")


def pe04_field_mutants(document: dict) -> int:
    count = 0
    for ident in PE04_FIELDS:
        index = field_index(document, ident)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        count += 1
        if definitions(document)["fields"][index]["kind"] in {"symbol", "symbols", "quantity"}:
            continue
        extra = copy.deepcopy(document)
        definitions(extra)["fields"][index]["unit"] = "unit.kelvin"
        reject(extra, "non-quantity field has quantity-only data")
        count += 1
    return count


def pe04_symbol_mutants(document: dict) -> int:
    count = 0
    for ident, tokens in PE04_SYMBOLS.items():
        index = field_index(document, ident)
        for token in tokens:
            renamed = copy.deepcopy(document)
            symbols = definitions(renamed)["fields"][index]["symbols"]
            symbols[symbols.index(f"{ident}.{token}")] = f"{ident}.paused"
            reject(renamed, "field has invalid semantic symbols")
            count += 1
    return count


def pe04_qualifier_mutants(document: dict) -> int:
    count = 0
    for ident, quals in PE04_QUALIFIERS.items():
        index = field_index(document, ident)
        cleared = copy.deepcopy(document)
        definitions(cleared)["fields"][index].pop("qualifiers")
        reject(cleared, "field qualifiers differ")
        added = copy.deepcopy(document)
        extra = "thermal.dimension.preset" if quals == ("thermal.dimension.suggestion",) else "thermal.dimension.suggestion"
        definitions(added)["fields"][index]["qualifiers"] = list(quals) + [extra]
        reject(added, "field qualifiers differ")
        count += 2
        if len(quals) < 2:
            continue
        swapped = copy.deepcopy(document)
        definitions(swapped)["fields"][index]["qualifiers"] = list(reversed(quals))
        reject(swapped, "field qualifiers differ")
        count += 1
    return count


def pe04_operation_index(document: dict, ident: str) -> int:
    operations = definitions(document)["operations"]
    return next(i for i, item in enumerate(operations) if item["id"] == ident)


def pe04_operation_identity_mutants(document: dict) -> int:
    count = 0
    ids = list(PE04_OPERATIONS)
    for ident in ids:
        index = pe04_operation_index(document, ident)
        other = ids[0] if ident != ids[0] else ids[1]
        _cap, other_arg, other_effect, _params = PE04_OPERATIONS[other]
        other_cap = PE04_OPERATIONS[other][0]
        renamed = copy.deepcopy(document)
        item = definitions(renamed)["operations"][index]
        item["id"] += "_other"
        item["ref"]["id"] += "_other"
        reject(renamed, "operation catalog")
        changed = copy.deepcopy(document)
        definitions(changed)["operations"][index]["capability"] = other_cap
        reject(changed, "operation capability differs")
        argued = copy.deepcopy(document)
        definitions(argued)["operations"][index]["arguments"] = [other_arg]
        definitions(argued)["operations"][index]["argument_constraints"] = [other_arg]
        reject(argued, "operation argument differs")
        effected = copy.deepcopy(document)
        definitions(effected)["operations"][index]["effect_rule"] = other_effect
        reject(effected, "operation effect differs")
        count += 4
    return count


def pe04_parameter_mutants(document: dict) -> int:
    count = 0
    for ident, (_cap, _arg, _effect, params) in PE04_OPERATIONS.items():
        index = pe04_operation_index(document, ident)
        extra = copy.deepcopy(document)
        item = definitions(extra)["operations"][index]
        item["parameters"] = list(params) + ["thermal.hold.expiry"]
        reject(extra, "operation parameters differ")
        count += 1
        for parameter in params:
            replaced = copy.deepcopy(document)
            current = list(definitions(replaced)["operations"][index]["parameters"])
            current[current.index(parameter)] = "thermal.hold.expiry"
            definitions(replaced)["operations"][index]["parameters"] = current
            reject(replaced, "operation parameters differ")
            count += 1
    return count


def pe04_event_index(document: dict, ident: str) -> int:
    events = definitions(document)["events"]
    return next(i for i, item in enumerate(events) if item["id"] == ident)


def pe04_event_mutants(document: dict) -> int:
    count = 0
    for ident, (service, trigger, payload) in PE04_EVENTS.items():
        index = pe04_event_index(document, ident)
        removed = copy.deepcopy(document)
        del definitions(removed)["events"][index]
        reject(removed, "event catalog")
        other_service = "thermal.service.system" if service != "thermal.service.system" else "thermal.service.zone"
        moved = copy.deepcopy(document)
        definitions(moved)["events"][index]["service"] = other_service
        reject(moved, "event service differs")
        other_trigger = "thermal.mode.zone" if trigger != "thermal.mode.zone" else "thermal.mode.system"
        trig = copy.deepcopy(document)
        definitions(trig)["events"][index]["trigger"] = other_trigger
        reject(trig, "event trigger differs")
        pay = copy.deepcopy(document)
        definitions(pay)["events"][index]["payload"] = list(payload) + ["thermal.mode.zone"]
        reject(pay, "event payload differs")
        count += 4
    return count


def pe04_rename(document: dict, group: str, ident: str) -> dict:
    mutated = copy.deepcopy(document)
    for item in definitions(mutated)[group]:
        if item["id"] == ident:
            item["id"] += "_other"
            item["ref"]["id"] += "_other"
            return mutated
    raise AssertionError(ident)


def pe04_group_mutants(document: dict) -> int:
    count = 0
    cases = [(ident, "qualifier_dimensions", "qualifier catalog") for ident in PE04_QUALIFIER_DIMENSIONS]
    cases += [
        ("thermal.dimension.function", "fact_dimensions", "fact-key dimension contracts"),
        ("thermal.dimension.sensor", "fact_dimensions", "fact-key dimension contracts"),
        ("thermal.service.function", "services", "service catalog"),
        ("thermal.service.sensor", "services", "service catalog"),
        ("thermal.capability.read.function", "capabilities", "capability catalog"),
        ("thermal.capability.read.sensor", "capabilities", "capability catalog"),
        ("thermal.portal.read.function", "portal_contributions", "Portal catalog"),
        ("thermal.portal.read.sensor", "portal_contributions", "Portal catalog"),
    ]
    for _ident, (cap, _arg, effect, _params) in PE04_OPERATIONS.items():
        cases.append((cap, "capabilities", "capability catalog"))
        cases.append((effect, "effect_rules", "effect catalog"))
    for ident, group, message in cases:
        reject(pe04_rename(document, group, ident), message)
        count += 1
    for portal_id in ("thermal.portal.read.function", "thermal.portal.read.sensor"):
        dropped = copy.deepcopy(document)
        portal = next(item for item in definitions(dropped)["portal_contributions"] if item["id"] == portal_id)
        portal["fields"].pop()
        reject(dropped, "read descriptor field coverage")
        count += 1
    return count


def pe04_qualifier_dimension_mutants(document: dict) -> int:
    count = 0
    items = definitions(document)["qualifier_dimensions"]
    for ident, (kind, unit) in PE04_QUALIFIER_DIMENSIONS.items():
        index = next(i for i, item in enumerate(items) if item["id"] == ident)
        changed = copy.deepcopy(document)
        definitions(changed)["qualifier_dimensions"][index]["value_kind"] = "symbol" if kind != "symbol" else "text"
        reject(changed, "qualifier dimension differs")
        unit_change = copy.deepcopy(document)
        item = definitions(unit_change)["qualifier_dimensions"][index]
        if unit is None:
            item["unit"] = "unit.one"
        else:
            item.pop("unit")
        reject(unit_change, "qualifier dimension differs")
        count += 2
    return count


def pe04_mutants(document: dict) -> int:
    """Identity fields and the production mutation each case catches.

    field id: removing the field is rejected as a field catalog mismatch.
    non-quantity unit: inserting unit.kelvin is rejected as quantity-only data.
    each symbol token, including thermal.mode.zone on: replacing that token is
    rejected as invalid semantic symbols.
    qualifier list: removing it, appending one, or reversing two is rejected
    as field qualifiers differ.
    operation id: renaming it is rejected as an operation catalog mismatch.
    capability, argument and effect: replacing each is rejected as operation
    capability differs, operation argument differs, or operation effect differs.
    each parameter, and one added parameter: replacing or adding it is rejected
    as operation parameters differ.
    event id: removing it is rejected as an event catalog mismatch.
    event service, trigger and payload: replacing each is rejected as event
    service differs, event trigger differs, or event payload differs.
    qualifier-dimension id: renaming it is rejected as a qualifier catalog mismatch.
    qualifier value kind and unit: replacing each is rejected as qualifier
    dimension differs.
    function and sensor fact-dimension ids: renaming each is rejected as
    fact-key dimension contracts differ.
    function and sensor service ids: renaming each is rejected as a service
    catalog mismatch.
    each new capability id: renaming it is rejected as a capability catalog mismatch.
    each new effect id: renaming it is rejected as an effect catalog mismatch.
    each new portal id: renaming it is rejected as a Portal catalog mismatch.
    one field of each new read portal: removing it is rejected as read
    descriptor field coverage.
    Subject, unit and each present bound of every new field are varied by
    field_axis_mutants: a moved dimension is rejected as field subject differs,
    a replaced unit is rejected as field unit, a shifted present bound and an
    inserted absent bound are rejected as field bounds differ.
    """
    return (
        pe04_field_mutants(document) + pe04_symbol_mutants(document)
        + pe04_qualifier_mutants(document) + pe04_operation_identity_mutants(document)
        + pe04_parameter_mutants(document) + pe04_event_mutants(document)
        + pe04_group_mutants(document) + pe04_qualifier_dimension_mutants(document)
    )




PE05_FIELDS = ('thermal.mode.dhw', 'thermal.mode.dhw_supported', 'thermal.dhw.heater_types', 'thermal.dhw.heat_demand', 'thermal.dhw.estimated_heat_required', 'thermal.dhw.charge_ratio', 'thermal.dhw.boost_state', 'thermal.dhw.boost_duration', 'thermal.dhw.boost_one_shot', 'thermal.dhw.boost_emergency', 'thermal.dhw.boost_temporary_setpoint', 'thermal.dhw.boost_target_ratio', 'thermal.dhw.boost_target_reheat_ratio', 'thermal.measurement.dhw_flow_rate', 'thermal.measurement.dhw_circuit_flow_temperature', 'thermal.measurement.dhw_circuit_return_temperature', 'thermal.nameplate.store_volume', 'thermal.measurement.store_top_temperature', 'thermal.measurement.store_bottom_temperature', 'thermal.status.pump_running', 'thermal.status.pump', 'thermal.status.pump_alarms', 'thermal.mode.pump_operation', 'thermal.mode.pump_effective_operation', 'thermal.mode.pump_control', 'thermal.mode.pump_effective_control', 'thermal.measurement.pump_capacity', 'thermal.setpoint.pump_level', 'thermal.measurement.pump_running_time', 'thermal.measurement.pump_power', 'thermal.energy.pump_consumed', 'thermal.measurement.pump_flow_rate', 'thermal.measurement.pump_pressure', 'thermal.measurement.pump_medium_temperature', 'thermal.nameplate.pump_maximum_pressure', 'thermal.nameplate.pump_maximum_speed', 'thermal.nameplate.pump_maximum_flow', 'thermal.nameplate.pump_minimum_constant_pressure', 'thermal.nameplate.pump_maximum_constant_pressure', 'thermal.nameplate.pump_minimum_compensated_pressure', 'thermal.nameplate.pump_maximum_compensated_pressure', 'thermal.nameplate.pump_minimum_constant_speed', 'thermal.nameplate.pump_maximum_constant_speed', 'thermal.nameplate.pump_minimum_constant_flow', 'thermal.nameplate.pump_maximum_constant_flow', 'thermal.nameplate.pump_minimum_constant_temperature', 'thermal.nameplate.pump_maximum_constant_temperature', 'thermal.status.valve_state', 'thermal.setpoint.valve_target_state', 'thermal.measurement.valve_level', 'thermal.setpoint.valve_target_level', 'thermal.configuration.valve_default_open_level', 'thermal.configuration.valve_level_step', 'thermal.valve.open_duration', 'thermal.configuration.valve_default_open_duration', 'thermal.valve.auto_close_time', 'thermal.valve.remaining_duration', 'thermal.status.valve_faults', 'thermal.measurement.valve_flow_rate', 'thermal.measurement.system_water_pressure', 'thermal.measurement.circuit_water_pressure', 'thermal.measurement.heat_generator_flow_rate', 'thermal.measurement.circuit_return_temperature', 'thermal.measurement.dew_point', 'thermal.measurement.circuit_humidity', 'thermal.measurement.collector_temperature', 'thermal.measurement.solar_flow_temperature', 'thermal.measurement.solar_return_temperature', 'thermal.measurement.solar_power', 'thermal.status.leak', 'thermal.status.freeze', 'thermal.detector.sensitivity_level', 'thermal.detector.supported_sensitivity_levels', 'thermal.detector.default_sensitivity_level', 'thermal.detector.alarms_active', 'thermal.detector.alarms_suppressed', 'thermal.detector.alarms_enabled', 'thermal.detector.alarms_supported', 'thermal.detector.sensor_fault', 'thermal.water_tank.condition', 'thermal.water_tank.degradation_direction', 'thermal.water_tank.change_indication', 'thermal.water_tank.in_place', 'thermal.water_tank.last_changed', 'thermal.water_tank.replacement_product_identifier')
PE05_SYMBOLS = {'thermal.mode.dhw': ('auto', 'eco', 'manual', 'off', 'on', 'timed', 'vacation'), 'thermal.mode.dhw_supported': ('auto', 'eco', 'manual', 'off', 'on', 'timed', 'vacation'), 'thermal.dhw.heater_types': ('boiler', 'heat_pump', 'immersion_element_1', 'immersion_element_2', 'other'), 'thermal.dhw.heat_demand': ('boiler', 'heat_pump', 'immersion_element_1', 'immersion_element_2', 'other'), 'thermal.dhw.boost_state': ('active', 'inactive'), 'thermal.status.pump_running': ('off', 'on'), 'thermal.status.pump': ('device_fault', 'local_override', 'remote_flow', 'remote_pressure', 'remote_temperature', 'running', 'speed_high', 'speed_low', 'supply_fault'), 'thermal.status.pump_alarms': ('air_detection', 'dry_running', 'electronic_fatal_failure', 'electronic_non_fatal_failure', 'electronic_temperature_high', 'general_fault', 'leakage', 'motor_fatal_failure', 'motor_temperature_high', 'power_missing_phase', 'pump_blocked', 'sensor_failure', 'supply_voltage_high', 'supply_voltage_low', 'system_pressure_high', 'system_pressure_low', 'turbine_operation'), 'thermal.mode.pump_operation': ('local', 'maximum', 'minimum', 'normal'), 'thermal.mode.pump_effective_operation': ('local', 'maximum', 'minimum', 'normal'), 'thermal.mode.pump_control': ('automatic', 'constant_flow', 'constant_pressure', 'constant_speed', 'constant_temperature', 'proportional_pressure'), 'thermal.mode.pump_effective_control': ('automatic', 'constant_flow', 'constant_pressure', 'constant_speed', 'constant_temperature', 'proportional_pressure'), 'thermal.status.valve_state': ('closed', 'open', 'transitioning'), 'thermal.setpoint.valve_target_state': ('closed', 'open'), 'thermal.status.valve_faults': ('blocked', 'current_exceeded', 'general_fault', 'leaking', 'not_connected', 'short_circuit'), 'thermal.status.leak': ('clear', 'detected'), 'thermal.status.freeze': ('clear', 'detected'), 'thermal.detector.alarms_active': ('audible', 'visual'), 'thermal.detector.alarms_suppressed': ('audible', 'visual'), 'thermal.detector.alarms_enabled': ('audible', 'visual'), 'thermal.detector.alarms_supported': ('audible', 'visual'), 'thermal.detector.sensor_fault': ('general_fault',), 'thermal.water_tank.degradation_direction': ('down', 'up'), 'thermal.water_tank.change_indication': ('critical', 'ok', 'warning')}
PE05_QUALIFIERS = {'thermal.water_tank.replacement_product_identifier': ('thermal.dimension.replacement_product',)}
PE05_OPERATIONS = {'thermal.operation.set_dhw_mode': ('thermal.capability.set_dhw_mode', 'thermal.mode.dhw', 'thermal.effect.set_dhw_mode', ()), 'thermal.operation.set_dhw_temperature': ('thermal.capability.set_dhw_temperature', 'thermal.setpoint.dhw_temperature_setpoint', 'thermal.effect.set_dhw_temperature', ()), 'thermal.operation.set_dhw_boost': ('thermal.capability.set_dhw_boost', 'thermal.dhw.boost_state', 'thermal.effect.set_dhw_boost', ('thermal.dhw.boost_duration', 'thermal.dhw.boost_one_shot', 'thermal.dhw.boost_emergency', 'thermal.dhw.boost_temporary_setpoint', 'thermal.dhw.boost_target_ratio', 'thermal.dhw.boost_target_reheat_ratio')), 'thermal.operation.set_pump_running': ('thermal.capability.set_pump_running', 'thermal.status.pump_running', 'thermal.effect.set_pump_running', ()), 'thermal.operation.set_pump_operation_mode': ('thermal.capability.set_pump_operation_mode', 'thermal.mode.pump_operation', 'thermal.effect.set_pump_operation_mode', ()), 'thermal.operation.set_pump_control_mode': ('thermal.capability.set_pump_control_mode', 'thermal.mode.pump_control', 'thermal.effect.set_pump_control_mode', ()), 'thermal.operation.set_pump_level': ('thermal.capability.set_pump_level', 'thermal.setpoint.pump_level', 'thermal.effect.set_pump_level', ()), 'thermal.operation.set_valve_state': ('thermal.capability.set_valve_state', 'thermal.setpoint.valve_target_state', 'thermal.effect.set_valve_state', ('thermal.valve.open_duration', 'thermal.setpoint.valve_target_level')), 'thermal.operation.set_valve_level': ('thermal.capability.set_valve_level', 'thermal.setpoint.valve_target_level', 'thermal.effect.set_valve_level', ()), 'thermal.operation.set_valve_default_open_duration': ('thermal.capability.set_valve_default_open_duration', 'thermal.configuration.valve_default_open_duration', 'thermal.effect.set_valve_default_open_duration', ()), 'thermal.operation.set_valve_default_open_level': ('thermal.capability.set_valve_default_open_level', 'thermal.configuration.valve_default_open_level', 'thermal.effect.set_valve_default_open_level', ()), 'thermal.operation.suppress_detector_alarm': ('thermal.capability.suppress_detector_alarm', 'thermal.detector.alarms_suppressed', 'thermal.effect.suppress_detector_alarm', ()), 'thermal.operation.enable_detector_alarm': ('thermal.capability.enable_detector_alarm', 'thermal.detector.alarms_enabled', 'thermal.effect.enable_detector_alarm', ()), 'thermal.operation.set_detector_sensitivity': ('thermal.capability.set_detector_sensitivity', 'thermal.detector.sensitivity_level', 'thermal.effect.set_detector_sensitivity', ()), 'thermal.operation.reset_water_tank': ('thermal.capability.reset_water_tank', 'thermal.water_tank.change_indication', 'thermal.effect.reset_water_tank', ())}
PE05_EVENTS = {'thermal.event.valve_state_changed': ('thermal.service.valve', 'thermal.status.valve_state', ('thermal.measurement.valve_level',)), 'thermal.event.valve_fault': ('thermal.service.valve', 'thermal.status.valve_faults', ()), 'thermal.event.leak_changed': ('thermal.service.detector', 'thermal.status.leak', ()), 'thermal.event.freeze_changed': ('thermal.service.detector', 'thermal.status.freeze', ()), 'thermal.event.detector_alarms_changed': ('thermal.service.detector', 'thermal.detector.alarms_active', ('thermal.detector.alarms_suppressed',)), 'thermal.event.detector_sensor_fault': ('thermal.service.detector', 'thermal.detector.sensor_fault', ())}
PE05_EXCLUDED = ('thermal.status.legionella_protection', 'thermal.configuration.legionella_days', 'thermal.configuration.legionella_time', 'thermal.setpoint.store_charge_temperature', 'thermal.configuration.store_charge_hysteresis', 'thermal.configuration.dew_point_offset', 'thermal.measurement.pump_start_count', 'thermal.valve.role', 'thermal.status.frost_protection')
PE05_RELATIONS = ('thermal.relation.valve_member', 'thermal.relation.pump_member', 'thermal.relation.solar_circuit_collector', 'thermal.relation.solar_supply', 'thermal.relation.detector_member', 'thermal.relation.water_tank_member')
PE05_WITHHELD_EVENTS = ('thermal.event.dhw_boost_started', 'thermal.event.dhw_boost_ended', 'thermal.event.pump_supply_voltage_low', 'thermal.event.pump_supply_voltage_high', 'thermal.event.pump_power_missing_phase', 'thermal.event.pump_system_pressure_low', 'thermal.event.pump_system_pressure_high', 'thermal.event.pump_dry_running', 'thermal.event.pump_motor_temperature_high', 'thermal.event.pump_motor_fatal_failure', 'thermal.event.pump_electronic_temperature_high', 'thermal.event.pump_pump_blocked', 'thermal.event.pump_sensor_failure', 'thermal.event.pump_electronic_non_fatal_failure', 'thermal.event.pump_electronic_fatal_failure', 'thermal.event.pump_general_fault', 'thermal.event.pump_leakage', 'thermal.event.pump_air_detection', 'thermal.event.pump_turbine_operation')
PE05_DIMENSIONS = ('thermal.dimension.valve', 'thermal.dimension.solar_circuit', 'thermal.dimension.solar_collector', 'thermal.dimension.detector', 'thermal.dimension.water_tank')
PE05_SERVICES = ('thermal.service.valve', 'thermal.service.solar_circuit', 'thermal.service.solar_collector', 'thermal.service.detector', 'thermal.service.water_tank')
PE05_PORTALS = (
    "thermal.portal.read.valve", "thermal.portal.read.solar_circuit", "thermal.portal.read.solar_collector",
    "thermal.portal.read.detector", "thermal.portal.read.water_tank",
)


def check_pe05_withheld(fields: dict, relations: set, events: set, operations: dict) -> None:
    present = [ident for ident in PE05_EXCLUDED if ident in fields]
    if present:
        raise AssertionError(f"two-vendor fields admitted: {present}")
    present = [ident for ident in PE05_RELATIONS if ident in relations]
    if present:
        raise AssertionError(f"relations admitted: {present}")
    present = [ident for ident in PE05_WITHHELD_EVENTS if ident in events]
    if present:
        raise AssertionError(f"withheld events admitted: {present}")
    for ident in ("thermal.relation.zone_room", "thermal.relation.circuit_room"):
        if ident not in relations:
            raise AssertionError(f"room containment left the pack: {ident}")
    if "thermal.operation.set_zone_mode" not in operations:
        raise AssertionError("zone mode operation left the pack")


def check_pe05_fields(fields: dict) -> None:
    missing = [ident for ident in PE05_FIELDS if ident not in fields]
    if missing:
        raise AssertionError(f"admitted fields absent: {missing}")
    for ident, tokens in PE05_SYMBOLS.items():
        if fields[ident].get("symbols") != [f"{ident}.{token}" for token in tokens]:
            raise AssertionError(f"{ident} symbols differ")
    for ident, quals in PE05_QUALIFIERS.items():
        if tuple(fields[ident].get("qualifiers", ())) != quals:
            raise AssertionError(f"{ident} qualifiers differ")


def check_pe05_operations(operations: dict) -> None:
    for ident, (cap, arg, effect, params) in PE05_OPERATIONS.items():
        item = operations[ident]
        observed = (item["capability"], item["arguments"], item["effect_rule"], tuple(item.get("parameters", ())))
        if observed != (cap, [arg], effect, params):
            raise AssertionError(f"{ident} operation identity differs")


def check_pe05_events(document: dict) -> None:
    event_items = {item["id"]: item for item in definitions(document)["events"]}
    for ident, (service, trigger, payload) in PE05_EVENTS.items():
        item = event_items[ident]
        if (item["service"], item["trigger"], tuple(item["payload"])) != (service, trigger, payload):
            raise AssertionError(f"{ident} event identity differs")
    qualifiers = {item["id"]: item for item in definitions(document)["qualifier_dimensions"]}
    replacement = qualifiers["thermal.dimension.replacement_product"]
    if (replacement.get("value_kind"), replacement.get("unit")) != ("quantity", "unit.one"):
        raise AssertionError("replacement product qualifier differs")


def check_pe05(document: dict) -> None:
    """Admitted hydraulic rows are present and the withheld rows are absent.

    Subject, unit and each present or absent bound of every admitted field are
    compared by check_field_table. field_axis_mutants varies those three for
    every field, including these.
    """
    fields = {field["id"]: field for field in definitions(document)["fields"]}
    relations = {item["id"] for item in definitions(document)["relations"]}
    events = {item["id"] for item in definitions(document)["events"]}
    operations = {item["id"]: item for item in definitions(document)["operations"]}
    check_pe05_withheld(fields, relations, events, operations)
    check_pe05_fields(fields)
    check_pe05_operations(operations)
    check_pe05_events(document)
    print("pe05_identity: PASS")


def pe05_field_mutants(document: dict) -> int:
    count = 0
    for ident in PE05_FIELDS:
        index = field_index(document, ident)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        count += 1
        if definitions(document)["fields"][index]["kind"] in {"symbol", "symbols", "quantity"}:
            continue
        extra = copy.deepcopy(document)
        definitions(extra)["fields"][index]["unit"] = "unit.kelvin"
        reject(extra, "non-quantity field has quantity-only data")
        count += 1
    return count


def pe05_symbol_mutants(document: dict) -> int:
    count = 0
    for ident, tokens in PE05_SYMBOLS.items():
        index = field_index(document, ident)
        for token in tokens:
            renamed = copy.deepcopy(document)
            symbols = definitions(renamed)["fields"][index]["symbols"]
            symbols[symbols.index(f"{ident}.{token}")] = f"{ident}.paused"
            reject(renamed, "field has invalid semantic symbols")
            count += 1
    return count


def pe05_qualifier_mutants(document: dict) -> int:
    count = 0
    for ident in PE05_QUALIFIERS:
        index = field_index(document, ident)
        cleared = copy.deepcopy(document)
        definitions(cleared)["fields"][index].pop("qualifiers")
        reject(cleared, "field qualifiers differ")
        added = copy.deepcopy(document)
        definitions(added)["fields"][index]["qualifiers"].append("thermal.dimension.suggestion")
        reject(added, "field qualifiers differ")
        count += 2
    return count


def pe05_operation_index(document: dict, ident: str) -> int:
    return next(i for i, item in enumerate(definitions(document)["operations"]) if item["id"] == ident)


def pe05_operation_mutants(document: dict) -> int:
    count = 0
    ids = list(PE05_OPERATIONS)
    for ident in ids:
        index = pe05_operation_index(document, ident)
        other = ids[0] if ident != ids[0] else ids[1]
        other_cap, other_arg, other_effect, _params = PE05_OPERATIONS[other]
        renamed = copy.deepcopy(document)
        item = definitions(renamed)["operations"][index]
        item["id"] += "_other"
        item["ref"]["id"] += "_other"
        reject(renamed, "operation catalog")
        changed = copy.deepcopy(document)
        definitions(changed)["operations"][index]["capability"] = other_cap
        reject(changed, "operation capability differs")
        argued = copy.deepcopy(document)
        definitions(argued)["operations"][index]["arguments"] = [other_arg]
        definitions(argued)["operations"][index]["argument_constraints"] = [other_arg]
        reject(argued, "operation argument differs")
        effected = copy.deepcopy(document)
        definitions(effected)["operations"][index]["effect_rule"] = other_effect
        reject(effected, "operation effect differs")
        count += 4
        capability_id = PE05_OPERATIONS[ident][0]
        moved = copy.deepcopy(document)
        capability = next(item for item in definitions(moved)["capabilities"] if item["id"] == capability_id)
        capability["service"] = "thermal.service.zone"
        reject(moved, "operation capability differs")
        count += 1
    return count


def pe05_parameter_mutants(document: dict) -> int:
    count = 0
    for ident, (_cap, _arg, _effect, params) in PE05_OPERATIONS.items():
        index = pe05_operation_index(document, ident)
        extra = copy.deepcopy(document)
        item = definitions(extra)["operations"][index]
        item["parameters"] = list(params) + ["thermal.hold.expiry"]
        reject(extra, "operation parameters differ")
        count += 1
        for parameter in params:
            replaced = copy.deepcopy(document)
            current = list(definitions(replaced)["operations"][index]["parameters"])
            current[current.index(parameter)] = "thermal.hold.expiry"
            definitions(replaced)["operations"][index]["parameters"] = current
            reject(replaced, "operation parameters differ")
            count += 1
    return count


def pe05_event_mutants(document: dict) -> int:
    count = 0
    for ident, (service, trigger, payload) in PE05_EVENTS.items():
        index = next(i for i, item in enumerate(definitions(document)["events"]) if item["id"] == ident)
        removed = copy.deepcopy(document)
        del definitions(removed)["events"][index]
        reject(removed, "event catalog")
        moved = copy.deepcopy(document)
        definitions(moved)["events"][index]["service"] = (
            "thermal.service.system" if service != "thermal.service.system" else "thermal.service.zone")
        reject(moved, "event service differs")
        trig = copy.deepcopy(document)
        definitions(trig)["events"][index]["trigger"] = (
            "thermal.mode.zone" if trigger != "thermal.mode.zone" else "thermal.mode.system")
        reject(trig, "event trigger differs")
        pay = copy.deepcopy(document)
        definitions(pay)["events"][index]["payload"] = list(payload) + ["thermal.mode.zone"]
        reject(pay, "event payload differs")
        entered = copy.deepcopy(document)
        definitions(entered)["events"][index]["condition"] = "entered"
        reject(entered, "event payload differs")
        derived = copy.deepcopy(document)
        definitions(derived)["events"][index]["origin"] = "derived"
        reject(derived, "event payload differs")
        count += 6
    return count


def pe05_rename(document: dict, group: str, ident: str) -> dict:
    mutated = copy.deepcopy(document)
    for item in definitions(mutated)[group]:
        if item["id"] == ident:
            item["id"] += "_other"
            item["ref"]["id"] += "_other"
            return mutated
    raise AssertionError(ident)


def pe05_group_mutants(document: dict) -> int:
    count = 0
    cases = [("thermal.dimension.replacement_product", "qualifier_dimensions", "qualifier catalog")]
    cases += [(ident, "fact_dimensions", "fact-key dimension contracts") for ident in PE05_DIMENSIONS]
    cases += [(ident, "services", "service catalog") for ident in PE05_SERVICES]
    for cap, _arg, effect, _params in PE05_OPERATIONS.values():
        cases.append((cap, "capabilities", "capability catalog"))
        cases.append((effect, "effect_rules", "effect catalog"))
    cases += [(ident, "portal_contributions", "Portal catalog") for ident in PE05_PORTALS]
    for ident, group, message in cases:
        reject(pe05_rename(document, group, ident), message)
        count += 1
    qualifiers = definitions(document)["qualifier_dimensions"]
    index = next(i for i, item in enumerate(qualifiers) if item["id"] == "thermal.dimension.replacement_product")
    changed = copy.deepcopy(document)
    definitions(changed)["qualifier_dimensions"][index]["value_kind"] = "text"
    reject(changed, "qualifier dimension differs")
    cleared = copy.deepcopy(document)
    definitions(cleared)["qualifier_dimensions"][index].pop("unit")
    reject(cleared, "qualifier dimension differs")
    count += 2
    for portal_id in PE05_PORTALS:
        dropped = copy.deepcopy(document)
        portal = next(item for item in definitions(dropped)["portal_contributions"] if item["id"] == portal_id)
        portal["fields"].pop()
        reject(dropped, "read descriptor field coverage")
        count += 1
    return count


def pe05_mutants(document: dict) -> int:
    """Identity fields and the production mutation each case catches.

    field id: removing the field is rejected as a field catalog mismatch.
    non-quantity unit: inserting unit.kelvin on a boolean, text or time field
    is rejected as quantity-only data.
    each symbol token: replacing that token is rejected as invalid semantic symbols.
    qualifier list: removing it or appending one is rejected as field qualifiers differ.
    operation id: renaming it is rejected as an operation catalog mismatch.
    capability, argument and effect: replacing each is rejected as operation
    capability differs, operation argument differs, or operation effect differs.
    capability service: moving it to thermal.service.zone is rejected as
    operation capability differs.
    each parameter, and one added parameter: replacing or adding it is rejected
    as operation parameters differ.
    event id: removing it is rejected as an event catalog mismatch.
    event service, trigger and payload: replacing each is rejected as event
    service differs, event trigger differs, or event payload differs.
    event condition and origin: replacing each is rejected as event payload differs.
    qualifier-dimension id: renaming it is rejected as a qualifier catalog mismatch.
    qualifier value kind and unit: replacing each is rejected as qualifier dimension differs.
    each new fact-dimension id: renaming it is rejected as fact-key dimension contracts.
    each new service id: renaming it is rejected as a service catalog mismatch.
    each new capability id: renaming it is rejected as a capability catalog mismatch.
    each new effect id: renaming it is rejected as an effect catalog mismatch.
    each new portal id: renaming it is rejected as a Portal catalog mismatch.
    one field of each new read portal: removing it is rejected as read descriptor
    field coverage.
    Subject, unit and each present or absent bound of every new field are varied
    by field_axis_mutants.
    """
    return (
        pe05_field_mutants(document) + pe05_symbol_mutants(document) + pe05_qualifier_mutants(document)
        + pe05_operation_mutants(document) + pe05_parameter_mutants(document) + pe05_event_mutants(document)
        + pe05_group_mutants(document)
    )


QU11_FIELDS = ('thermal.measurement.electrical_power', 'thermal.energy.electrical_consumed', 'thermal.energy.solar_yield', 'thermal.setpoint.heat_generator_flow_temperature', 'thermal.setpoint.circuit_flow_temperature', 'thermal.setpoint.circuit_fixed_flow_temperature', 'thermal.limit.circuit_flow_temperature_minimum', 'thermal.limit.circuit_flow_temperature_maximum', 'thermal.measurement.outdoor_air_temperature_average', 'thermal.status.terminal_unit_power', 'thermal.measurement.terminal_unit_air_temperature', 'thermal.measurement.terminal_unit_humidity', 'thermal.setpoint.terminal_unit_heating', 'thermal.setpoint.terminal_unit_cooling', 'thermal.measurement.coil_temperature', 'thermal.configuration.ac_type', 'thermal.nameplate.cooling_capacity', 'thermal.configuration.refrigerant_type', 'thermal.configuration.compressor_type', 'thermal.status.terminal_unit_errors', 'thermal.measurement.louver_position', 'thermal.fan.mode', 'thermal.fan.mode_sequence', 'thermal.fan.speed_setting', 'thermal.fan.speed_ratio', 'thermal.fan.speed_step_maximum', 'thermal.fan.speed_step_setting', 'thermal.fan.speed_step', 'thermal.fan.rock_support', 'thermal.fan.rock_setting', 'thermal.fan.wind_support', 'thermal.fan.wind_setting', 'thermal.fan.airflow_direction', 'thermal.mode.ventilation', 'thermal.measurement.supply_air_flow', 'thermal.measurement.extract_air_flow', 'thermal.measurement.supply_air_temperature', 'thermal.measurement.extract_air_temperature', 'thermal.measurement.outdoor_intake_air_temperature', 'thermal.measurement.exhaust_air_temperature', 'thermal.filter.kind', 'thermal.filter.condition', 'thermal.filter.degradation_direction', 'thermal.filter.change_indication', 'thermal.filter.in_place', 'thermal.filter.last_changed', 'thermal.filter.replacement_product_kind', 'thermal.filter.replacement_product_identifier', 'thermal.measurement.air_quality', 'thermal.air.volume_fraction', 'thermal.air.mass_concentration', 'thermal.air.radon_concentration', 'thermal.air.statistic_window', 'thermal.air.level', 'thermal.air.uncertainty', 'thermal.air.measurement_medium')
QU11_SYMBOLS = {'thermal.status.terminal_unit_power': ('off', 'on'), 'thermal.configuration.ac_type': ('cooling_fixed', 'cooling_inverter', 'heat_pump_fixed', 'heat_pump_inverter', 'unknown'), 'thermal.configuration.refrigerant_type': ('r22', 'r407c', 'r410a', 'unknown'), 'thermal.configuration.compressor_type': ('t1', 't2', 't3', 'unknown'), 'thermal.status.terminal_unit_errors': ('coil_sensor_fail', 'compressor_fail', 'fan_fail', 'outdoor_sensor_fail', 'room_sensor_fail'), 'thermal.measurement.louver_position': ('closed', 'half', 'open', 'quarter', 'three_quarters'), 'thermal.fan.mode': ('auto', 'high', 'low', 'medium', 'off', 'on', 'smart'), 'thermal.fan.mode_sequence': ('off_high', 'off_high_auto', 'off_low_high', 'off_low_high_auto', 'off_low_medium_high', 'off_low_medium_high_auto'), 'thermal.fan.rock_support': ('left_right', 'round', 'up_down'), 'thermal.fan.rock_setting': ('left_right', 'round', 'up_down'), 'thermal.fan.wind_support': ('natural', 'sleep'), 'thermal.fan.wind_setting': ('natural', 'sleep'), 'thermal.fan.airflow_direction': ('forward', 'reverse'), 'thermal.mode.ventilation': ('auto', 'eco', 'off', 'on'), 'thermal.filter.kind': ('activated_carbon', 'hepa', 'other'), 'thermal.filter.degradation_direction': ('down', 'up'), 'thermal.filter.change_indication': ('critical', 'ok', 'warning'), 'thermal.filter.replacement_product_kind': ('ean', 'gtin14', 'gtin8', 'oem', 'upc'), 'thermal.measurement.air_quality': ('extremely_poor', 'fair', 'good', 'moderate', 'poor', 'unknown', 'very_poor'), 'thermal.air.level': ('critical', 'high', 'low', 'medium', 'unknown'), 'thermal.air.measurement_medium': ('air', 'soil', 'water')}
QU11_QUALIFIERS = {'thermal.energy.electrical_consumed': ('thermal.dimension.period', 'thermal.dimension.period_offset'), 'thermal.energy.solar_yield': ('thermal.dimension.period', 'thermal.dimension.period_offset'), 'thermal.filter.replacement_product_kind': ('thermal.dimension.replacement_product',), 'thermal.filter.replacement_product_identifier': ('thermal.dimension.replacement_product',), 'thermal.air.volume_fraction': ('thermal.dimension.statistic', 'thermal.dimension.substance'), 'thermal.air.mass_concentration': ('thermal.dimension.statistic', 'thermal.dimension.substance'), 'thermal.air.radon_concentration': ('thermal.dimension.statistic',), 'thermal.air.statistic_window': ('thermal.dimension.statistic', 'thermal.dimension.substance'), 'thermal.air.level': ('thermal.dimension.substance',), 'thermal.air.uncertainty': ('thermal.dimension.substance',), 'thermal.air.measurement_medium': ('thermal.dimension.substance',)}
QU11_OPERATIONS = {'thermal.operation.set_heat_generator_flow_temperature': ('thermal.capability.set_heat_generator_flow_temperature', 'thermal.setpoint.heat_generator_flow_temperature', 'thermal.effect.set_heat_generator_flow_temperature', 'thermal.service.heat_generator'), 'thermal.operation.set_circuit_fixed_flow_temperature': ('thermal.capability.set_circuit_fixed_flow_temperature', 'thermal.setpoint.circuit_fixed_flow_temperature', 'thermal.effect.set_circuit_fixed_flow_temperature', 'thermal.service.circuit'), 'thermal.operation.set_circuit_flow_temperature_minimum': ('thermal.capability.set_circuit_flow_temperature_minimum', 'thermal.limit.circuit_flow_temperature_minimum', 'thermal.effect.set_circuit_flow_temperature_minimum', 'thermal.service.circuit'), 'thermal.operation.set_circuit_flow_temperature_maximum': ('thermal.capability.set_circuit_flow_temperature_maximum', 'thermal.limit.circuit_flow_temperature_maximum', 'thermal.effect.set_circuit_flow_temperature_maximum', 'thermal.service.circuit'), 'thermal.operation.set_overrun_hvac_system_off': ('thermal.capability.set_overrun_hvac_system_off', 'thermal.overrun.hvac_system_off', 'thermal.effect.set_overrun_hvac_system_off', 'thermal.service.system'), 'thermal.operation.set_overrun_one_day_at_home': ('thermal.capability.set_overrun_one_day_at_home', 'thermal.overrun.one_day_at_home', 'thermal.effect.set_overrun_one_day_at_home', 'thermal.service.system'), 'thermal.operation.set_overrun_one_day_away': ('thermal.capability.set_overrun_one_day_away', 'thermal.overrun.one_day_away', 'thermal.effect.set_overrun_one_day_away', 'thermal.service.system'), 'thermal.operation.set_overrun_one_time_dhw': ('thermal.capability.set_overrun_one_time_dhw', 'thermal.overrun.one_time_dhw', 'thermal.effect.set_overrun_one_time_dhw', 'thermal.service.system'), 'thermal.operation.set_overrun_one_time_ventilation': ('thermal.capability.set_overrun_one_time_ventilation', 'thermal.overrun.one_time_ventilation', 'thermal.effect.set_overrun_one_time_ventilation', 'thermal.service.system'), 'thermal.operation.set_overrun_party': ('thermal.capability.set_overrun_party', 'thermal.overrun.party', 'thermal.effect.set_overrun_party', 'thermal.service.system'), 'thermal.operation.set_overrun_sg_ready_condition_1': ('thermal.capability.set_overrun_sg_ready_condition_1', 'thermal.overrun.sg_ready_condition_1', 'thermal.effect.set_overrun_sg_ready_condition_1', 'thermal.service.system'), 'thermal.operation.set_overrun_sg_ready_condition_3': ('thermal.capability.set_overrun_sg_ready_condition_3', 'thermal.overrun.sg_ready_condition_3', 'thermal.effect.set_overrun_sg_ready_condition_3', 'thermal.service.system'), 'thermal.operation.set_overrun_sg_ready_condition_4': ('thermal.capability.set_overrun_sg_ready_condition_4', 'thermal.overrun.sg_ready_condition_4', 'thermal.effect.set_overrun_sg_ready_condition_4', 'thermal.service.system'), 'thermal.operation.set_overrun_valve_kick': ('thermal.capability.set_overrun_valve_kick', 'thermal.overrun.valve_kick', 'thermal.effect.set_overrun_valve_kick', 'thermal.service.system'), 'thermal.operation.set_terminal_unit_power': ('thermal.capability.set_terminal_unit_power', 'thermal.status.terminal_unit_power', 'thermal.effect.set_terminal_unit_power', 'thermal.service.terminal_unit'), 'thermal.operation.set_terminal_unit_mode': ('thermal.capability.set_terminal_unit_mode', 'thermal.mode.terminal_unit', 'thermal.effect.set_terminal_unit_mode', 'thermal.service.terminal_unit'), 'thermal.operation.set_terminal_unit_heating': ('thermal.capability.set_terminal_unit_heating', 'thermal.setpoint.terminal_unit_heating', 'thermal.effect.set_terminal_unit_heating', 'thermal.service.terminal_unit'), 'thermal.operation.set_terminal_unit_cooling': ('thermal.capability.set_terminal_unit_cooling', 'thermal.setpoint.terminal_unit_cooling', 'thermal.effect.set_terminal_unit_cooling', 'thermal.service.terminal_unit'), 'thermal.operation.set_louver_position': ('thermal.capability.set_louver_position', 'thermal.measurement.louver_position', 'thermal.effect.set_louver_position', 'thermal.service.terminal_unit'), 'thermal.operation.set_fan_mode': ('thermal.capability.set_fan_mode', 'thermal.fan.mode', 'thermal.effect.set_fan_mode', 'thermal.service.fan'), 'thermal.operation.set_fan_speed': ('thermal.capability.set_fan_speed', 'thermal.fan.speed_setting', 'thermal.effect.set_fan_speed', 'thermal.service.fan'), 'thermal.operation.set_fan_step': ('thermal.capability.set_fan_step', 'thermal.fan.speed_step_setting', 'thermal.effect.set_fan_step', 'thermal.service.fan'), 'thermal.operation.set_fan_rock': ('thermal.capability.set_fan_rock', 'thermal.fan.rock_setting', 'thermal.effect.set_fan_rock', 'thermal.service.fan'), 'thermal.operation.set_fan_wind': ('thermal.capability.set_fan_wind', 'thermal.fan.wind_setting', 'thermal.effect.set_fan_wind', 'thermal.service.fan'), 'thermal.operation.set_fan_airflow_direction': ('thermal.capability.set_fan_airflow_direction', 'thermal.fan.airflow_direction', 'thermal.effect.set_fan_airflow_direction', 'thermal.service.fan'), 'thermal.operation.set_ventilation_mode': ('thermal.capability.set_ventilation_mode', 'thermal.mode.ventilation', 'thermal.effect.set_ventilation_mode', 'thermal.service.ventilation'), 'thermal.operation.set_ventilation_level': ('thermal.capability.set_ventilation_level', 'thermal.demand.level', 'thermal.effect.set_ventilation_level', 'thermal.service.ventilation'), 'thermal.operation.reset_filter': ('thermal.capability.reset_filter', 'thermal.filter.change_indication', 'thermal.effect.reset_filter', 'thermal.service.air_filter'), 'thermal.operation.set_filter_last_changed': ('thermal.capability.set_filter_last_changed', 'thermal.filter.last_changed', 'thermal.effect.set_filter_last_changed', 'thermal.service.air_filter')}
QU11_EXCLUDED = ('thermal.energy.fuel_consumed', 'thermal.energy.heat_delivered', 'thermal.energy.environmental_yield', 'thermal.measurement.modulation', 'thermal.setpoint.modulation', 'thermal.status.flame', 'thermal.status.backup_heater', 'thermal.measurement.burner_starts', 'thermal.measurement.burner_operating_time', 'thermal.measurement.compressor_starts', 'thermal.measurement.compressor_operating_time', 'thermal.nameplate.heat_output', 'thermal.configuration.partial_load_power', 'thermal.configuration.heating_curve_slope', 'thermal.configuration.heating_curve_offset', 'thermal.configuration.circuit_kind', 'thermal.status.screed_drying', 'thermal.program.screed_drying_day', 'thermal.setpoint.screed_drying_temperature', 'thermal.configuration.bivalence_heating_temperature', 'thermal.configuration.bivalence_dhw_temperature', 'thermal.maintenance.next_due', 'thermal.absence.start', 'thermal.absence.end', 'thermal.absence.setpoint', 'thermal.measurement.fan_speed', 'thermal.measurement.heat_recovery_efficiency', 'thermal.status.bypass', 'thermal.operation.set_screed_drying', 'thermal.operation.set_absence', 'thermal.operation.set_heating_curve', 'thermal.operation.set_bivalence_temperatures', 'thermal.dimension.purpose', 'thermal.dimension.louver_axis')
QU11_RELATIONS = ('thermal.relation.fan_member', 'thermal.relation.filter_member')
QU11_DIMENSIONS = ("thermal.dimension.fan", "thermal.dimension.air_filter")
QU11_QUALIFIER_DIMENSIONS = {'thermal.dimension.period': ('symbol', None, ('day', 'month', 'year')), 'thermal.dimension.period_offset': ('quantity', 'unit.one', None), 'thermal.dimension.substance': ('symbol', None, ('carbon_dioxide', 'carbon_monoxide', 'formaldehyde', 'nitrogen_dioxide', 'ozone', 'pm1', 'pm10', 'pm2_5', 'radon', 'volatile_organic_compounds')), 'thermal.dimension.statistic': ('symbol', None, ('average', 'measured', 'peak'))}
QU11_SERVICES = ("thermal.service.fan", "thermal.service.air_filter")
QU11_PORTALS = ("thermal.portal.read.fan", "thermal.portal.read.air_filter")
FORBIDDEN_USE_CASES = (
    "flexibleStartForWhiteGoods",
    "monitoringAndControlOfSmartGridReadyConditions",
)


def check_qu11_fields(fields: dict) -> None:
    missing = [ident for ident in QU11_FIELDS if ident not in fields]
    if missing:
        raise AssertionError(f"admitted fields absent: {missing}")
    for ident, tokens in QU11_SYMBOLS.items():
        if fields[ident].get("symbols") != [f"{ident}.{token}" for token in tokens]:
            raise AssertionError(f"{ident} symbols differ")
    for ident, quals in QU11_QUALIFIERS.items():
        if tuple(fields[ident].get("qualifiers", ())) != quals:
            raise AssertionError(f"{ident} qualifiers differ")
    if "qualifiers" in fields["thermal.measurement.louver_position"]:
        raise AssertionError("louver position keeps an axis qualifier")


def check_qu11_withheld(fields: dict, operations: dict, qualifier_ids: set, relations: set) -> None:
    admitted = fields.keys() | operations.keys() | qualifier_ids
    present = [ident for ident in QU11_EXCLUDED if ident in admitted]
    if present:
        raise AssertionError(f"withheld ids admitted: {present}")
    present = [ident for ident in QU11_RELATIONS if ident in relations]
    if present:
        raise AssertionError(f"relations admitted: {present}")


def check_qu11_operations(document: dict, operations: dict) -> None:
    capabilities = {item["id"]: item for item in definitions(document)["capabilities"]}
    for ident, (capability, argument, effect, service) in QU11_OPERATIONS.items():
        item = operations[ident]
        observed = (item["capability"], item["arguments"], item["effect_rule"], item.get("parameters"))
        if observed != (capability, [argument], effect, None):
            raise AssertionError(f"{ident} operation identity differs")
        owner = capabilities[capability]
        if owner["service"] != service or owner["constraints"] != [argument]:
            raise AssertionError(f"{ident} capability identity differs")


def check_qu11_event(events: dict) -> None:
    event = events["thermal.event.maintenance_due"]
    observed = (
        event["service"], event["trigger"], event["condition"], tuple(event["payload"]),
        event["origin"], event.get("symbols"),
    )
    expected = (
        "thermal.service.system", "thermal.status.maintenance", "entered", (), "derived",
        ["thermal.status.maintenance.due"],
    )
    if observed != expected:
        raise AssertionError("maintenance event identity differs")


def check_qu11_qualifier_dimensions(document: dict) -> None:
    qualifiers = {item["id"]: item for item in definitions(document)["qualifier_dimensions"]}
    for ident, (value_kind, unit, symbols) in QU11_QUALIFIER_DIMENSIONS.items():
        item = qualifiers[ident]
        expected_symbols = None if symbols is None else list(symbols)
        if (item.get("value_kind"), item.get("unit"), item.get("symbols")) != (value_kind, unit, expected_symbols):
            raise AssertionError(f"{ident} qualifier dimension differs")


def check_qu11_pages() -> None:
    for path in (validator.VECTORS, validator.DOCUMENT, ROOT / "api/v1/element-catalog-v1.json"):
        found = [name for name in FORBIDDEN_USE_CASES if name in path.read_text(encoding="utf-8")]
        if found:
            raise AssertionError(f"{path.name} cites {found}")


def check_qu11(document: dict) -> None:
    """Admitted generator and ventilation rows are present and the withheld rows are absent."""
    fields = {field["id"]: field for field in definitions(document)["fields"]}
    operations = {item["id"]: item for item in definitions(document)["operations"]}
    events = {item["id"]: item for item in definitions(document)["events"]}
    qualifier_ids = {item["id"] for item in definitions(document)["qualifier_dimensions"]}
    relations = {item["id"] for item in definitions(document)["relations"]}
    check_qu11_fields(fields)
    check_qu11_withheld(fields, operations, qualifier_ids, relations)
    check_qu11_operations(document, operations)
    check_qu11_event(events)
    check_qu11_qualifier_dimensions(document)
    check_qu11_pages()
    print("qu11_identity: PASS")


def qu11_rename(document: dict, group: str, ident: str) -> dict:
    mutated = copy.deepcopy(document)
    for item in definitions(mutated)[group]:
        if item["id"] == ident:
            item["id"] += "_other"
            item["ref"]["id"] += "_other"
            return mutated
    raise AssertionError(ident)


def qu11_field_mutants(document: dict) -> int:
    count = 0
    for ident in QU11_FIELDS:
        index = field_index(document, ident)
        removed = copy.deepcopy(document)
        del definitions(removed)["fields"][index]
        reject(removed, "field catalog")
        count += 1
        if definitions(document)["fields"][index]["kind"] in {"symbol", "symbols", "quantity"}:
            continue
        extra = copy.deepcopy(document)
        definitions(extra)["fields"][index]["unit"] = "unit.kelvin"
        reject(extra, "non-quantity field has quantity-only data")
        count += 1
    return count


def qu11_symbol_mutants(document: dict) -> int:
    count = 0
    for ident, tokens in QU11_SYMBOLS.items():
        index = field_index(document, ident)
        for token in tokens:
            renamed = copy.deepcopy(document)
            symbols = definitions(renamed)["fields"][index]["symbols"]
            symbols[symbols.index(f"{ident}.{token}")] = f"{ident}.paused"
            reject(renamed, "field has invalid semantic symbols")
            count += 1
        smuggled = copy.deepcopy(document)
        definitions(smuggled)["fields"][index]["symbols"].append(f"{ident}.withheld")
        reject(smuggled, "field has invalid semantic symbols")
        count += 1
    return count


def qu11_qualifier_mutants(document: dict) -> int:
    count = 0
    for ident in QU11_QUALIFIERS:
        index = field_index(document, ident)
        cleared = copy.deepcopy(document)
        definitions(cleared)["fields"][index].pop("qualifiers")
        reject(cleared, "field qualifiers differ")
        added = copy.deepcopy(document)
        definitions(added)["fields"][index]["qualifiers"].append("thermal.dimension.suggestion")
        reject(added, "field qualifiers differ")
        count += 2
    return count


def qu11_operation_index(document: dict, ident: str) -> int:
    return next(i for i, item in enumerate(definitions(document)["operations"]) if item["id"] == ident)


def qu11_one_operation_mutants(document: dict, ident: str, ids: list) -> int:
    index = qu11_operation_index(document, ident)
    other = ids[0] if ident != ids[0] else ids[1]
    other_cap, other_arg, other_effect, _service = QU11_OPERATIONS[other]
    reject(qu11_rename(document, "operations", ident), "operation catalog")
    changed = copy.deepcopy(document)
    definitions(changed)["operations"][index]["capability"] = other_cap
    reject(changed, "operation capability differs")
    argued = copy.deepcopy(document)
    item = definitions(argued)["operations"][index]
    item["arguments"] = [other_arg]
    item["argument_constraints"] = [other_arg]
    reject(argued, "operation argument differs")
    effected = copy.deepcopy(document)
    definitions(effected)["operations"][index]["effect_rule"] = other_effect
    reject(effected, "operation effect differs")
    extra = copy.deepcopy(document)
    definitions(extra)["operations"][index]["parameters"] = ["thermal.hold.expiry"]
    reject(extra, "operation parameters differ")
    moved = copy.deepcopy(document)
    capability_id = QU11_OPERATIONS[ident][0]
    for capability in definitions(moved)["capabilities"]:
        if capability["id"] == capability_id:
            capability["service"] = "thermal.service.zone"
    reject(moved, "operation capability differs")
    return 6


def qu11_operation_mutants(document: dict) -> int:
    ids = list(QU11_OPERATIONS)
    return sum(qu11_one_operation_mutants(document, ident, ids) for ident in ids)


def qu11_event_mutants(document: dict) -> int:
    count = 0
    index = next(
        i for i, item in enumerate(definitions(document)["events"]) if item["id"] == "thermal.event.maintenance_due")
    removed = copy.deepcopy(document)
    del definitions(removed)["events"][index]
    reject(removed, "event catalog")
    replacements = (
        ("service", "thermal.service.zone", "event service differs"),
        ("trigger", "thermal.mode.system", "event trigger differs"),
        ("condition", "changed", "event payload differs"),
        ("origin", "emitted", "event payload differs"),
        ("payload", ["thermal.mode.zone"], "event payload differs"),
        ("symbols", ["thermal.status.maintenance.clear"], "event payload differs"),
    )
    for key, value, message in replacements:
        mutated = copy.deepcopy(document)
        definitions(mutated)["events"][index][key] = value
        reject(mutated, message)
        count += 1
    return count + 1


def qu11_qualifier_symbol_mutants(document: dict, slot: int, symbols: tuple) -> int:
    count = 0
    for token in symbols:
        replaced = copy.deepcopy(document)
        current = definitions(replaced)["qualifier_dimensions"][slot]["symbols"]
        current[current.index(token)] = "paused"
        reject(replaced, "qualifier dimension differs")
        count += 1
    return count


def qu11_one_qualifier_dimension_mutants(document: dict, ident: str, value_kind: str, unit, symbols) -> int:
    count = 1
    reject(qu11_rename(document, "qualifier_dimensions", ident), "qualifier catalog")
    slot = next(i for i, item in enumerate(definitions(document)["qualifier_dimensions"]) if item["id"] == ident)
    changed = copy.deepcopy(document)
    replacement = "quantity" if value_kind == "text" else "text"
    definitions(changed)["qualifier_dimensions"][slot]["value_kind"] = replacement
    reject(changed, "qualifier dimension differs")
    count += 1
    if unit is not None:
        cleared = copy.deepcopy(document)
        definitions(cleared)["qualifier_dimensions"][slot].pop("unit")
        reject(cleared, "qualifier dimension differs")
        count += 1
    if symbols is not None:
        count += qu11_qualifier_symbol_mutants(document, slot, symbols)
    return count


def qu11_qualifier_dimension_mutants(document: dict) -> int:
    return sum(
        qu11_one_qualifier_dimension_mutants(document, ident, value_kind, unit, symbols)
        for ident, (value_kind, unit, symbols) in QU11_QUALIFIER_DIMENSIONS.items()
    )


def qu11_group_cases() -> list:
    cases = [(ident, "fact_dimensions", "fact-key dimension contracts") for ident in QU11_DIMENSIONS]
    cases += [(ident, "services", "service catalog") for ident in QU11_SERVICES]
    for capability, _argument, effect, _service in QU11_OPERATIONS.values():
        cases.append((capability, "capabilities", "capability catalog"))
        cases.append((effect, "effect_rules", "effect catalog"))
    cases += [(ident, "portal_contributions", "Portal catalog") for ident in QU11_PORTALS]
    return cases


def qu11_group_mutants(document: dict) -> int:
    count = 0
    for ident, group, message in qu11_group_cases():
        reject(qu11_rename(document, group, ident), message)
        count += 1
    for portal_id in QU11_PORTALS:
        dropped = copy.deepcopy(document)
        for portal in definitions(dropped)["portal_contributions"]:
            if portal["id"] == portal_id:
                portal["fields"].pop()
        reject(dropped, "read descriptor field coverage")
        count += 1
    return count


def qu11_mutants(document: dict) -> int:
    """Identity fields and the production mutation each case catches.

    field id: removing the field is rejected as a field catalog mismatch.
    non-quantity unit: inserting unit.kelvin on a boolean, text or time field
    is rejected as quantity-only data.
    each symbol token: replacing that token is rejected as invalid semantic symbols.
    qualifier list: removing it or appending one is rejected as field qualifiers differ.
    operation id: renaming it is rejected as an operation catalog mismatch.
    capability, argument and effect: replacing each is rejected as operation
    capability differs, operation argument differs, or operation effect differs.
    capability service: moving it to thermal.service.zone is rejected as
    operation capability differs.
    one added parameter: adding it is rejected as operation parameters differ.
    event id: removing it is rejected as an event catalog mismatch.
    event service, trigger, payload, condition, origin and symbol: replacing
    each is rejected as event service differs, event trigger differs, or event
    payload differs.
    qualifier-dimension id: renaming it is rejected as a qualifier catalog mismatch.
    qualifier value kind, unit and each symbol: replacing each is rejected as
    qualifier dimension differs.
    each new fact-dimension id: renaming it is rejected as fact-key dimension contracts.
    each new service id: renaming it is rejected as a service catalog mismatch.
    each new capability id: renaming it is rejected as a capability catalog mismatch.
    each new effect id: renaming it is rejected as an effect catalog mismatch.
    each new portal id: renaming it is rejected as a Portal catalog mismatch.
    one field of each new read portal: removing it is rejected as read descriptor
    field coverage.
    Subject, unit and each present or absent bound of every new field are varied
    by field_axis_mutants.
    A symbol token listed by the field contract may contain unknown. A symbol
    containing unknown or withheld that the contract does not list is rejected.
    """
    return (
        qu11_field_mutants(document) + qu11_symbol_mutants(document) + qu11_qualifier_mutants(document)
        + qu11_operation_mutants(document) + qu11_event_mutants(document)
        + qu11_qualifier_dimension_mutants(document) + qu11_group_mutants(document)
    )


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
    check_pe04(document)
    print(f"room_mutants: {room_mutants(document)} REJECTED")
    print(f"pe04_mutants: {pe04_mutants(document)} REJECTED")
    check_pe05(document)
    print(f"pe05_mutants: {pe05_mutants(document)} REJECTED")
    check_qu11(document)
    print(f"qu11_mutants: {qu11_mutants(document)} REJECTED")


if __name__ == "__main__":
    main()
