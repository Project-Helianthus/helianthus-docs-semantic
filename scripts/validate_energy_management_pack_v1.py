#!/usr/bin/env python3
"""Validate helianthus.pack.energy_management 1.0.0 against the admitted PE07 fields."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/packs/energy-management-acceptance-vectors.json"
PAGE = ROOT / "api/v1/packs/energy-management-v1.md"
PACK = {"id": "helianthus.pack.energy_management", "version": "1.0.0"}
SUBJECT = "energy.dimension.subject"
SERVICE = "energy.service.subject"
READ_CAPABILITY = "energy.capability.read.subject"
READ_PORTAL = "energy.portal.read.subject"
GROUPS = ('fields', 'fact_dimensions', 'qualifier_dimensions', 'services', 'capabilities', 'operations', 'effect_rules', 'portal_contributions')
PAGE_IDS = ('energy.limit.consumption_active_power', 'energy.limit.consumption_active', 'energy.limit.consumption_duration', 'energy.limit.consumption_failsafe_power', 'energy.limit.consumption_failsafe_duration_minimum', 'energy.nameplate.consumption_nominal_maximum', 'energy.nameplate.consumption_contractual_maximum', 'energy.limit.production_active_power', 'energy.limit.production_active', 'energy.limit.production_duration', 'energy.limit.production_failsafe_power', 'energy.limit.production_failsafe_duration_minimum', 'energy.nameplate.production_nominal_maximum', 'energy.nameplate.production_contractual_maximum', 'energy.limit.state', 'energy.heartbeat.status', 'energy.heartbeat.timeout', 'energy.manager.state', 'energy.esa.type', 'energy.esa.can_generate', 'energy.esa.state', 'energy.esa.minimum_power', 'energy.esa.maximum_power', 'energy.esa.adjustment_minimum_power', 'energy.esa.adjustment_maximum_power', 'energy.esa.adjustment_minimum_duration', 'energy.esa.adjustment_maximum_duration', 'energy.esa.adjustment_cause', 'energy.esa.opt_out', 'energy.esa.mode', 'energy.esa.mode_supported', 'energy.esa.requested_power', 'energy.esa.requested_duration', 'energy.esa.request_cause', 'energy.esa.adjustment_end_cause', 'energy.series.identifier', 'energy.series.start', 'energy.series.end', 'energy.series.earliest_start', 'energy.series.latest_end', 'energy.series.update_reason', 'energy.series.pausable', 'energy.series.slot_start', 'energy.series.slot_duration', 'energy.series.slot_minimum_duration', 'energy.series.slot_maximum_duration', 'energy.series.slot_default_duration', 'energy.series.slot_elapsed', 'energy.series.slot_remaining', 'energy.series.slot_power_nominal', 'energy.series.slot_power_minimum', 'energy.series.slot_power_maximum', 'energy.series.slot_energy_nominal', 'energy.series.slot_pausable', 'energy.series.slot_minimum_pause', 'energy.series.slot_maximum_pause', 'energy.series.slot_adjustment_minimum_power', 'energy.series.slot_adjustment_maximum_power', 'energy.series.slot_adjustment_minimum_duration', 'energy.series.slot_adjustment_maximum_duration', 'energy.series.slot_state', 'energy.series.constraint_minimum_slot_duration', 'energy.series.constraint_maximum_slots', 'energy.series.constraint_slot_value_step', 'energy.sequence.state', 'energy.sequence.earliest_start', 'energy.sequence.latest_end', 'energy.sequence.scheduled_start', 'energy.sequence.pausable', 'energy.sequence.stoppable', 'energy.sequence.active_duration_minimum', 'energy.sequence.active_duration_maximum', 'energy.sequence.pause_duration_minimum', 'energy.sequence.pause_duration_maximum', 'energy.sequence.slot_duration', 'energy.sequence.slot_power_expected', 'energy.sequence.slot_power_minimum', 'energy.sequence.slot_power_maximum', 'energy.preference.balance_step', 'energy.preference.balance_label', 'energy.preference.current_balance', 'energy.preference.priorities', 'energy.preference.low_power_sensitivity', 'energy.dimension.subject', 'energy.dimension.slot', 'energy.dimension.series', 'energy.dimension.adjustment_range', 'energy.dimension.sequence', 'energy.dimension.balance', 'energy.service.subject', 'energy.capability.read.subject', 'energy.capability.set_consumption_limit', 'energy.capability.set_production_limit', 'energy.capability.set_consumption_failsafe', 'energy.capability.set_production_failsafe', 'energy.capability.adjust_power', 'energy.capability.set_esa_state', 'energy.capability.adjust_start_time', 'energy.capability.modify_series_slot', 'energy.capability.set_esa_mode', 'energy.capability.schedule_sequence', 'energy.capability.set_sequence_state', 'energy.capability.set_energy_balance', 'energy.capability.set_low_power_sensitivity', 'energy.operation.set_consumption_limit', 'energy.operation.set_production_limit', 'energy.operation.set_consumption_failsafe', 'energy.operation.set_production_failsafe', 'energy.operation.adjust_power', 'energy.operation.set_esa_state', 'energy.operation.adjust_start_time', 'energy.operation.modify_series_slot', 'energy.operation.set_esa_mode', 'energy.operation.schedule_sequence', 'energy.operation.set_sequence_state', 'energy.operation.set_energy_balance', 'energy.operation.set_low_power_sensitivity', 'energy.effect.set_consumption_limit', 'energy.effect.set_production_limit', 'energy.effect.set_consumption_failsafe', 'energy.effect.set_production_failsafe', 'energy.effect.adjust_power', 'energy.effect.set_esa_state', 'energy.effect.adjust_start_time', 'energy.effect.modify_series_slot', 'energy.effect.set_esa_mode', 'energy.effect.schedule_sequence', 'energy.effect.set_sequence_state', 'energy.effect.set_energy_balance', 'energy.effect.set_low_power_sensitivity', 'energy.portal.read.subject', 'energy.event.power_adjust_start', 'energy.event.power_adjust_end', 'energy.event.paused', 'energy.event.resumed', 'energy.event.heartbeat_lost', 'energy.event.failsafe_entered')
SIGNED_FIELDS = ('energy.esa.minimum_power', 'energy.esa.maximum_power', 'energy.esa.adjustment_minimum_power', 'energy.esa.adjustment_maximum_power', 'energy.esa.requested_power', 'energy.series.slot_power_nominal', 'energy.series.slot_power_minimum', 'energy.series.slot_power_maximum', 'energy.series.slot_energy_nominal', 'energy.series.slot_adjustment_minimum_power', 'energy.series.slot_adjustment_maximum_power')
TOKEN = re.compile(r"(?<![A-Za-z0-9_])(?:%s)(?![A-Za-z0-9_])")

FIELD_CONTRACTS = {
    'energy.limit.consumption_active_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.consumption_active': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.limit.consumption_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.consumption_failsafe_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.consumption_failsafe_duration_minimum': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "72", "exponent10": 2}, "maximum": {"coefficient": "864", "exponent10": 2}}, "direction": 'non_negative'},
    'energy.nameplate.consumption_nominal_maximum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.nameplate.consumption_contractual_maximum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.production_active_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.production_active': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.limit.production_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.production_failsafe_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.production_failsafe_duration_minimum': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "72", "exponent10": 2}, "maximum": {"coefficient": "864", "exponent10": 2}}, "direction": 'non_negative'},
    'energy.nameplate.production_nominal_maximum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.nameplate.production_contractual_maximum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": None}, "direction": 'non_negative'},
    'energy.limit.state': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.limit.state.failsafe', 'energy.limit.state.init', 'energy.limit.state.limited', 'energy.limit.state.unlimited_autonomous', 'energy.limit.state.unlimited_controlled'), "bounds": None, "direction": 'not_applicable'},
    'energy.heartbeat.status': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.heartbeat.status.ok', 'energy.heartbeat.status.timeout', 'energy.heartbeat.status.unknown'), "bounds": None, "direction": 'not_applicable'},
    'energy.heartbeat.timeout': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": {"coefficient": "6", "exponent10": 1}}, "direction": 'non_negative'},
    'energy.manager.state': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.manager.state.failure', 'energy.manager.state.normal_operation', 'energy.manager.state.not_reachable'), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.type': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.esa.type.battery_storage', 'energy.esa.type.cooking', 'energy.esa.type.dishwasher', 'energy.esa.type.evse', 'energy.esa.type.fridge_freezer', 'energy.esa.type.home_water_pump', 'energy.esa.type.irrigation_water_pump', 'energy.esa.type.other', 'energy.esa.type.pool_pump', 'energy.esa.type.solar_pv', 'energy.esa.type.space_cooling', 'energy.esa.type.space_heating', 'energy.esa.type.space_heating_cooling', 'energy.esa.type.washing_machine', 'energy.esa.type.water_heating'), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.can_generate': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.state': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.esa.state.fault', 'energy.esa.state.offline', 'energy.esa.state.online', 'energy.esa.state.paused', 'energy.esa.state.power_adjust_active'), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.minimum_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.esa.maximum_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.esa.adjustment_minimum_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.adjustment_range',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.esa.adjustment_maximum_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.adjustment_range',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.esa.adjustment_minimum_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.adjustment_range',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.esa.adjustment_maximum_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.adjustment_range',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.esa.adjustment_cause': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.esa.adjustment_cause.grid_optimization', 'energy.esa.adjustment_cause.local_optimization', 'energy.esa.adjustment_cause.no_adjustment'), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.opt_out': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.esa.opt_out.grid_opt_out', 'energy.esa.opt_out.local_opt_out', 'energy.esa.opt_out.no_opt_out', 'energy.esa.opt_out.opt_out'), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.mode': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.esa.mode_supported': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.requested_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.esa.requested_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.esa.request_cause': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.esa.request_cause.grid_optimization', 'energy.esa.request_cause.local_optimization'), "bounds": None, "direction": 'not_applicable'},
    'energy.esa.adjustment_end_cause': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.esa.adjustment_end_cause.cancelled', 'energy.esa.adjustment_end_cause.fault', 'energy.esa.adjustment_end_cause.normal_completion', 'energy.esa.adjustment_end_cause.offline', 'energy.esa.adjustment_end_cause.user_opt_out'), "bounds": None, "direction": 'not_applicable'},
    'energy.series.identifier': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.end': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.earliest_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.latest_end': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.update_reason': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": ('energy.series.update_reason.grid_optimization', 'energy.series.update_reason.internal_optimization', 'energy.series.update_reason.local_optimization'), "bounds": None, "direction": 'not_applicable'},
    'energy.series.pausable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.slot_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.slot_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_minimum_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_maximum_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_default_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_elapsed': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_remaining': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_power_nominal': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.series.slot_power_minimum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.series.slot_power_maximum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.series.slot_energy_nominal': {"kind": 'quantity', "unit": 'unit.joule', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.series.slot_pausable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.slot_minimum_pause': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_maximum_pause': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_adjustment_minimum_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.series.slot_adjustment_maximum_power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.series.slot_adjustment_minimum_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_adjustment_maximum_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.slot_state': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series', 'energy.dimension.slot'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.series.constraint_minimum_slot_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.series.constraint_maximum_slots': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.series.constraint_slot_value_step': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.series',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.state': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": ('energy.sequence.state.completed', 'energy.sequence.state.inactive', 'energy.sequence.state.invalid', 'energy.sequence.state.paused', 'energy.sequence.state.pending', 'energy.sequence.state.running', 'energy.sequence.state.scheduled', 'energy.sequence.state.scheduled_paused'), "bounds": None, "direction": 'not_applicable'},
    'energy.sequence.earliest_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.sequence.latest_end': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.sequence.scheduled_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.sequence.pausable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.sequence.stoppable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.sequence.active_duration_minimum': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.active_duration_maximum': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.pause_duration_minimum': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.pause_duration_maximum': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.slot_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.slot_power_expected': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.slot_power_minimum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.sequence.slot_power_maximum': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.sequence', 'energy.dimension.slot'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.preference.balance_step': {"kind": 'quantity', "unit": 'unit.ratio', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.balance',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.preference.balance_label': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.balance',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.preference.current_balance': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.preference.priorities': {"kind": 'symbols', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": ('energy.preference.priorities.comfort', 'energy.preference.priorities.efficiency', 'energy.preference.priorities.speed', 'energy.preference.priorities.water_consumption'), "bounds": None, "direction": 'not_applicable'},
    'energy.preference.low_power_sensitivity': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
}

OPERATION_CONTRACTS = {
    'energy.operation.set_consumption_limit': {"capability": 'energy.capability.set_consumption_limit', "effect_rule": 'energy.effect.set_consumption_limit', "service": 'energy.service.subject', "arguments": ('energy.limit.consumption_active_power',), "parameters": ('energy.limit.consumption_active', 'energy.limit.consumption_duration'), "admission": 'eebus'},
    'energy.operation.set_production_limit': {"capability": 'energy.capability.set_production_limit', "effect_rule": 'energy.effect.set_production_limit', "service": 'energy.service.subject', "arguments": ('energy.limit.production_active_power',), "parameters": ('energy.limit.production_active', 'energy.limit.production_duration'), "admission": 'eebus'},
    'energy.operation.set_consumption_failsafe': {"capability": 'energy.capability.set_consumption_failsafe', "effect_rule": 'energy.effect.set_consumption_failsafe', "service": 'energy.service.subject', "arguments": ('energy.limit.consumption_failsafe_power',), "parameters": ('energy.limit.consumption_failsafe_duration_minimum',), "admission": 'eebus'},
    'energy.operation.set_production_failsafe': {"capability": 'energy.capability.set_production_failsafe', "effect_rule": 'energy.effect.set_production_failsafe', "service": 'energy.service.subject', "arguments": ('energy.limit.production_failsafe_power',), "parameters": ('energy.limit.production_failsafe_duration_minimum',), "admission": 'eebus'},
    'energy.operation.adjust_power': {"capability": 'energy.capability.adjust_power', "effect_rule": 'energy.effect.adjust_power', "service": 'energy.service.subject', "arguments": ('energy.esa.requested_power',), "parameters": ('energy.esa.request_cause', 'energy.esa.requested_duration'), "admission": 'matter_baseline'},
    'energy.operation.set_esa_state': {"capability": 'energy.capability.set_esa_state', "effect_rule": 'energy.effect.set_esa_state', "service": 'energy.service.subject', "arguments": ('energy.esa.state',), "parameters": ('energy.esa.request_cause', 'energy.esa.requested_duration'), "admission": 'matter_baseline'},
    'energy.operation.adjust_start_time': {"capability": 'energy.capability.adjust_start_time', "effect_rule": 'energy.effect.adjust_start_time', "service": 'energy.service.subject', "arguments": ('energy.series.start',), "parameters": ('energy.esa.request_cause',), "admission": 'matter_baseline'},
    'energy.operation.modify_series_slot': {"capability": 'energy.capability.modify_series_slot', "effect_rule": 'energy.effect.modify_series_slot', "service": 'energy.service.subject', "arguments": ('energy.series.slot_power_nominal',), "parameters": ('energy.esa.request_cause', 'energy.series.identifier', 'energy.series.slot_duration', 'energy.series.slot_power_maximum'), "admission": 'matter_baseline'},
    'energy.operation.set_esa_mode': {"capability": 'energy.capability.set_esa_mode', "effect_rule": 'energy.effect.set_esa_mode', "service": 'energy.service.subject', "arguments": ('energy.esa.mode',), "parameters": (), "admission": 'matter_baseline'},
    'energy.operation.schedule_sequence': {"capability": 'energy.capability.schedule_sequence', "effect_rule": 'energy.effect.schedule_sequence', "service": 'energy.service.subject', "arguments": ('energy.sequence.scheduled_start',), "parameters": (), "admission": 'eebus'},
    'energy.operation.set_sequence_state': {"capability": 'energy.capability.set_sequence_state', "effect_rule": 'energy.effect.set_sequence_state', "service": 'energy.service.subject', "arguments": ('energy.sequence.state',), "parameters": (), "admission": 'eebus'},
    'energy.operation.set_energy_balance': {"capability": 'energy.capability.set_energy_balance', "effect_rule": 'energy.effect.set_energy_balance', "service": 'energy.service.subject', "arguments": ('energy.preference.current_balance',), "parameters": (), "admission": 'matter_baseline'},
    'energy.operation.set_low_power_sensitivity': {"capability": 'energy.capability.set_low_power_sensitivity', "effect_rule": 'energy.effect.set_low_power_sensitivity', "service": 'energy.service.subject', "arguments": ('energy.preference.low_power_sensitivity',), "parameters": (), "admission": 'matter_baseline'},
}

QUALIFIER_CONTRACTS = {
    'energy.dimension.slot': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.series': {"value_kind": 'symbol', "unit": None, "symbols": ('charging_plan', 'charging_power_limit_curve', 'committed_power_plan', 'consumption_limit_curve', 'fallback_consumption_limit_curve', 'fallback_production_limit_curve', 'forecast', 'power_demand_forecast', 'preliminary_power_plan', 'production_limit_curve'), "admission": 'matter_baseline'},
    'energy.dimension.adjustment_range': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.sequence': {"value_kind": 'text', "unit": None, "symbols": (), "admission": 'eebus'},
    'energy.dimension.balance': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
}


def require(condition, label):
    if not condition:
        raise ValueError(label)


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    with path.open(encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=pairs)


def ref_of(ident):
    return {"pack": PACK, "id": ident, "version": "1.0.0"}


def forbid_marks(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(key not in {"sensitive", "hidden"}, f"marked {key}")
            forbid_marks(item)
    elif isinstance(value, list):
        for item in value:
            forbid_marks(item)


def check_orders(items, label):
    orders = [item.get("order") for item in items]
    require(all(isinstance(order, int) and order > 0 for order in orders), f"{label} order")
    require(orders == sorted(orders) and len(set(orders)) == len(orders), f"{label} order")


def check_refs(items, label):
    for item in items:
        require(item.get("ref") == ref_of(item["id"]), f"{label} {item['id']} ref")


def check_bounds(ident, item, expected):
    actual = item.get("bounds")
    if expected is None:
        require(actual is None, f"{ident} bounds")
        return
    require(isinstance(actual, dict), f"{ident} bounds")
    require(set(actual) == {"minimum", "maximum"}, f"{ident} bounds")
    require(actual.get("minimum") == expected["minimum"], f"{ident} bounds.minimum")
    require(actual.get("maximum") == expected["maximum"], f"{ident} bounds.maximum")


def check_field(item):
    ident = item["id"]
    contract = FIELD_CONTRACTS[ident]
    require(item.get("kind") == contract["kind"], f"{ident} kind")
    require(item.get("unit") == contract["unit"], f"{ident} unit")
    require(item.get("dimension") == contract["dimension"], f"{ident} dimension")
    require(tuple(item.get("qualifiers", ())) == contract["qualifiers"], f"{ident} qualifiers")
    require(tuple(item.get("symbols", ())) == contract["symbols"], f"{ident} symbols")
    require(item.get("direction") == contract["direction"], f"{ident} direction")
    require(item.get("optional") is True, f"{ident} optional")
    check_bounds(ident, item, contract["bounds"])
    if ident in SIGNED_FIELDS:
        require(item.get("direction") != "signed", f"{ident} direction")


def check_fields(items):
    require(isinstance(items, list), "fields")
    found = [item["id"] for item in items]
    unknown = sorted(set(found) - set(FIELD_CONTRACTS))
    missing = sorted(set(FIELD_CONTRACTS) - set(found))
    require(not unknown, f"fields outside PE07: {unknown}")
    require(not missing, f"fields missing: {missing}")
    require(len(found) == len(set(found)), "duplicate field")
    check_orders(items, "fields")
    check_refs(items, "field")
    for item in items:
        check_field(item)


def check_subject(items):
    require(len(items) == 1, "fact dimensions")
    item = items[0]
    require(item["id"] == SUBJECT, "fact dimension id")
    require(item.get("value_kind") == "text", "fact dimension value_kind")
    check_refs(items, "fact dimension")
    check_orders(items, "fact dimensions")


def check_qualifiers(items):
    found = [item["id"] for item in items]
    require(set(found) == set(QUALIFIER_CONTRACTS), "qualifier dimensions")
    check_orders(items, "qualifier dimensions")
    check_refs(items, "qualifier")
    for item in items:
        contract = QUALIFIER_CONTRACTS[item["id"]]
        require(item.get("value_kind") == contract["value_kind"], f"{item['id']} value_kind")
        require(item.get("unit") == contract["unit"], f"{item['id']} unit")
        require(tuple(item.get("symbols", ())) == contract["symbols"], f"{item['id']} symbols")


def check_service(items):
    require(len(items) == 1 and items[0]["id"] == SERVICE, "service")
    require(items[0].get("fact_key_dimension") == SUBJECT, "service fact_key_dimension")
    check_refs(items, "service")
    check_orders(items, "services")


def check_capabilities(items, operations):
    expected = {READ_CAPABILITY, *(contract["capability"] for contract in OPERATION_CONTRACTS.values())}
    found = [item["id"] for item in items]
    require(set(found) == expected, "capabilities")
    check_orders(items, "capabilities")
    check_refs(items, "capability")
    for item in items:
        require(item.get("service") == SERVICE, f"{item['id']} service")
        require(item.get("activation") == "qualified_current_binding", f"{item['id']} activation")


def check_operation(item):
    ident = item["id"]
    contract = OPERATION_CONTRACTS[ident]
    require(item.get("capability") == contract["capability"], f"{ident} capability")
    require(tuple(item.get("arguments", ())) == contract["arguments"], f"{ident} arguments")
    require(tuple(item.get("parameters", ())) == contract["parameters"], f"{ident} parameters")
    require(item.get("effect_rule") == contract["effect_rule"], f"{ident} effect_rule")
    require("preconditions" not in item, f"{ident} preconditions")


def check_operations(items):
    found = [item["id"] for item in items]
    unknown = sorted(set(found) - set(OPERATION_CONTRACTS))
    missing = sorted(set(OPERATION_CONTRACTS) - set(found))
    require(not unknown, f"operations outside PE07: {unknown}")
    require(not missing, f"operations missing: {missing}")
    check_orders(items, "operations")
    check_refs(items, "operation")
    for item in items:
        check_operation(item)


def check_effects(items, operations):
    expected = {item["effect_rule"]: item for item in operations}
    found = [item["id"] for item in items]
    require(set(found) == set(expected), "effect rules")
    check_orders(items, "effect rules")
    check_refs(items, "effect")
    for item in items:
        contract = expected[item["id"]]
        require(item.get("operation") == contract["id"], f"{item['id']} operation")
        require(item.get("fact") == contract["arguments"][0], f"{item['id']} fact")
        require(item.get("operator") == "equal", f"{item['id']} operator")


def check_portal(items, field_ids):
    require(len(items) == 1 and items[0]["id"] == READ_PORTAL, "portal")
    item = items[0]
    require(item.get("kind") == "read", "portal kind")
    require(item.get("service") == SERVICE, "portal service")
    require(item.get("fields") == sorted(field_ids), "portal fields")
    check_refs(items, "portal")
    check_orders(items, "portals")


def check_page(text):
    for ident in PAGE_IDS:
        require(TOKEN.pattern and re.search(TOKEN.pattern % re.escape(ident), text), f"document misses {ident}")


def check_pack(document):
    catalog = document["catalog"]
    require(document.get("contract") == "helianthus.semantic.pack.energy_management.acceptance/v1", "contract")
    require(document.get("pack_contract") == "helianthus.pack.energy_management/v1", "pack contract")
    require(catalog.get("pack") == PACK, "pack id")
    definitions = catalog["definitions"]
    require(set(definitions) == set(GROUPS), f"definition groups {sorted(set(definitions) - set(GROUPS))}")


def validate(document, page):
    forbid_marks(document)
    check_pack(document)
    definitions = document["catalog"]["definitions"]
    check_fields(definitions["fields"])
    check_subject(definitions["fact_dimensions"])
    check_qualifiers(definitions["qualifier_dimensions"])
    check_service(definitions["services"])
    check_capabilities(definitions["capabilities"], definitions["operations"])
    check_operations(definitions["operations"])
    check_effects(definitions["effect_rules"], definitions["operations"])
    check_portal(definitions["portal_contributions"], list(FIELD_CONTRACTS))
    check_page(page)


def main():
    validate(load(VECTORS), PAGE.read_text(encoding="utf-8"))
    print(f"energy management pack v1: PASS ({len(FIELD_CONTRACTS)} fields)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
