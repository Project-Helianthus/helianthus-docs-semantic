#!/usr/bin/env python3
"""Validate helianthus.pack.energy_management 1.0.0 against the admitted PE07 fields plus the admitted PE12 and QQ12 energy fields."""
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
GROUPS = ('fields', 'fact_dimensions', 'qualifier_dimensions', 'services', 'capabilities', 'operations', 'effect_rules', 'portal_contributions', 'events')
PAGE_IDS = ('energy.limit.consumption_active_power', 'energy.limit.consumption_active', 'energy.limit.consumption_duration', 'energy.limit.consumption_failsafe_power', 'energy.limit.consumption_failsafe_duration_minimum', 'energy.nameplate.consumption_nominal_maximum', 'energy.nameplate.consumption_contractual_maximum', 'energy.limit.production_active_power', 'energy.limit.production_active', 'energy.limit.production_duration', 'energy.limit.production_failsafe_power', 'energy.limit.production_failsafe_duration_minimum', 'energy.nameplate.production_nominal_maximum', 'energy.nameplate.production_contractual_maximum', 'energy.limit.state', 'energy.heartbeat.status', 'energy.heartbeat.timeout', 'energy.manager.state', 'energy.esa.type', 'energy.esa.can_generate', 'energy.esa.state', 'energy.esa.minimum_power', 'energy.esa.maximum_power', 'energy.esa.adjustment_minimum_power', 'energy.esa.adjustment_maximum_power', 'energy.esa.adjustment_minimum_duration', 'energy.esa.adjustment_maximum_duration', 'energy.esa.adjustment_cause', 'energy.esa.opt_out', 'energy.esa.mode', 'energy.esa.mode_supported', 'energy.esa.requested_power', 'energy.esa.requested_duration', 'energy.esa.request_cause', 'energy.esa.adjustment_end_cause', 'energy.series.identifier', 'energy.series.start', 'energy.series.end', 'energy.series.earliest_start', 'energy.series.latest_end', 'energy.series.update_reason', 'energy.series.pausable', 'energy.series.slot_start', 'energy.series.slot_duration', 'energy.series.slot_minimum_duration', 'energy.series.slot_maximum_duration', 'energy.series.slot_default_duration', 'energy.series.slot_elapsed', 'energy.series.slot_remaining', 'energy.series.slot_power_nominal', 'energy.series.slot_power_minimum', 'energy.series.slot_power_maximum', 'energy.series.slot_energy_nominal', 'energy.series.slot_pausable', 'energy.series.slot_minimum_pause', 'energy.series.slot_maximum_pause', 'energy.series.slot_adjustment_minimum_power', 'energy.series.slot_adjustment_maximum_power', 'energy.series.slot_adjustment_minimum_duration', 'energy.series.slot_adjustment_maximum_duration', 'energy.series.slot_state', 'energy.series.constraint_minimum_slot_duration', 'energy.series.constraint_maximum_slots', 'energy.series.constraint_slot_value_step', 'energy.sequence.state', 'energy.sequence.earliest_start', 'energy.sequence.latest_end', 'energy.sequence.scheduled_start', 'energy.sequence.pausable', 'energy.sequence.stoppable', 'energy.sequence.active_duration_minimum', 'energy.sequence.active_duration_maximum', 'energy.sequence.pause_duration_minimum', 'energy.sequence.pause_duration_maximum', 'energy.sequence.slot_duration', 'energy.sequence.slot_power_expected', 'energy.sequence.slot_power_minimum', 'energy.sequence.slot_power_maximum', 'energy.preference.balance_step', 'energy.preference.balance_label', 'energy.preference.current_balance', 'energy.preference.priorities', 'energy.preference.low_power_sensitivity', 'energy.dimension.subject', 'energy.dimension.slot', 'energy.dimension.series', 'energy.dimension.adjustment_range', 'energy.dimension.sequence', 'energy.dimension.balance', 'energy.service.subject', 'energy.capability.read.subject', 'energy.capability.set_consumption_limit', 'energy.capability.set_production_limit', 'energy.capability.set_consumption_failsafe', 'energy.capability.set_production_failsafe', 'energy.capability.adjust_power', 'energy.capability.set_esa_state', 'energy.capability.adjust_start_time', 'energy.capability.modify_series_slot', 'energy.capability.set_esa_mode', 'energy.capability.schedule_sequence', 'energy.capability.set_sequence_state', 'energy.capability.set_energy_balance', 'energy.capability.set_low_power_sensitivity', 'energy.operation.set_consumption_limit', 'energy.operation.set_production_limit', 'energy.operation.set_consumption_failsafe', 'energy.operation.set_production_failsafe', 'energy.operation.adjust_power', 'energy.operation.set_esa_state', 'energy.operation.adjust_start_time', 'energy.operation.modify_series_slot', 'energy.operation.set_esa_mode', 'energy.operation.schedule_sequence', 'energy.operation.set_sequence_state', 'energy.operation.set_energy_balance', 'energy.operation.set_low_power_sensitivity', 'energy.effect.set_consumption_limit', 'energy.effect.set_production_limit', 'energy.effect.set_consumption_failsafe', 'energy.effect.set_production_failsafe', 'energy.effect.adjust_power', 'energy.effect.set_esa_state', 'energy.effect.adjust_start_time', 'energy.effect.modify_series_slot', 'energy.effect.set_esa_mode', 'energy.effect.schedule_sequence', 'energy.effect.set_sequence_state', 'energy.effect.set_energy_balance', 'energy.effect.set_low_power_sensitivity', 'energy.portal.read.subject', 'energy.event.power_adjust_start', 'energy.event.power_adjust_end', 'energy.event.paused', 'energy.event.resumed', 'energy.event.heartbeat_lost', 'energy.event.failsafe_entered', 'resource.tariff', 'energy.dimension.tariff', 'energy.service.tariff', 'energy.capability.read.tariff', 'energy.portal.read.tariff', 'energy.dimension.tier', 'energy.dimension.boundary', 'energy.dimension.incentive', 'energy.dimension.component', 'energy.dimension.day_entry', 'energy.dimension.day_pattern', 'energy.dimension.calendar_period', 'energy.dimension.tariff_period', 'energy.dimension.individual_day', 'energy.dimension.forecast_slot', 'energy.dimension.direct_control_timestamp', 'energy.dimension.job', 'energy.tariff.label', 'energy.tariff.provider', 'energy.tariff.currency', 'energy.tariff.unit_basis', 'energy.tariff.block_mode', 'energy.tariff.start', 'energy.tariff.direction', 'energy.tariff.status', 'energy.tariff.price_kind', 'energy.tariff.randomization_offset', 'energy.tariff.randomization_kind', 'energy.price.current', 'energy.price.current_level', 'energy.price.current_start', 'energy.price.current_end', 'energy.price.current_description', 'energy.price.forecast_start', 'energy.price.forecast_end', 'energy.price.forecast_price', 'energy.price.forecast_level', 'energy.incentive.slot_start', 'energy.incentive.slot_end', 'energy.incentive.tier_kind', 'energy.incentive.boundary_lower', 'energy.incentive.boundary_upper', 'energy.incentive.incentive_value', 'energy.incentive.incentive_kind', 'energy.incentive.renewable_ratio', 'energy.incentive.co2_intensity', 'energy.incentive.maximum_tiers', 'energy.incentive.maximum_slots', 'energy.negotiation.simulation_cycles_maximum', 'energy.negotiation.simulation_concurrent', 'energy.negotiation.request_timeout', 'energy.negotiation.writeable_wait', 'energy.tariff.day_entry_start', 'energy.tariff.day_entry_duration', 'energy.tariff.day_entry_randomization_offset', 'energy.tariff.day_pattern_days', 'energy.tariff.day_pattern_entry', 'energy.tariff.calendar_period_start', 'energy.tariff.calendar_period_pattern', 'energy.tariff.individual_day_date', 'energy.tariff.individual_day_kind', 'energy.tariff.individual_day_entry', 'energy.tariff.component_price', 'energy.tariff.component_price_kind', 'energy.tariff.component_friendly_credit', 'energy.tariff.component_auxiliary_load', 'energy.tariff.component_peak_period', 'energy.tariff.component_power_threshold', 'energy.tariff.component_apparent_power_threshold', 'energy.tariff.component_threshold', 'energy.tariff.component_label', 'energy.tariff.component_predicted', 'energy.tariff.period_label', 'energy.tariff.period_entry', 'energy.tariff.period_component', 'energy.tariff.current_day_entry', 'energy.tariff.current_day_entry_date', 'energy.tariff.next_day_entry', 'energy.tariff.next_day_entry_date', 'energy.tariff.current_day', 'energy.tariff.next_day', 'energy.tariff.current_components', 'energy.tariff.next_components', 'energy.metering.quantity', 'energy.metering.timestamp', 'energy.metering.maximum_quantities', 'energy.grid.local_generation_available', 'energy.grid.start', 'energy.grid.end', 'energy.grid.carbon_intensity', 'energy.grid.carbon_level', 'energy.grid.local_carbon_intensity', 'energy.grid.local_carbon_level', 'energy.direct_control.timestamp', 'energy.direct_control.activity_state', 'energy.direct_control.is_activity_state_changeable', 'energy.direct_control.energy_mode', 'energy.direct_control.is_energy_mode_changeable', 'energy.direct_control.power', 'energy.direct_control.is_power_changeable', 'energy.direct_control.energy', 'energy.direct_control.is_energy_changeable', 'energy.direct_control.sequence_id', 'energy.direct_control.positive_energy_direction', 'energy.direct_control.power_unit', 'energy.direct_control.energy_unit', 'energy.task.job_id', 'energy.task.timestamp', 'energy.task.job_state', 'energy.task.elapsed_time', 'energy.task.remaining_time', 'energy.task.direct_control_related', 'energy.task.hvac_related', 'energy.task.hvac_related_overrun_id', 'energy.task.load_control_releated', 'energy.task.load_control_releated_event_id', 'energy.task.power_sequences_related', 'energy.task.power_sequences_related_sequence_id', 'energy.task.smart_energy_management_ps_related', 'energy.task.smart_energy_management_ps_related_sequence_id', 'energy.task.job_source', 'energy.task.label', 'energy.task.description', 'energy.task.remote_controllable', 'energy.task.jobs_active', 'energy.lpc.use_case_name', 'energy.lpp.use_case_name', 'energy.poen.use_case_name', 'energy.podf.use_case_name', 'energy.tout.use_case_name', 'energy.itpcm.use_case_name', 'energy.ohpcf.use_case_name', 'energy.lpc.actor', 'energy.lpp.actor', 'energy.poen.actor', 'energy.podf.actor', 'energy.tout.actor', 'energy.itpcm.actor', 'energy.ohpcf.actor', 'energy.lpc.use_case_version', 'energy.lpp.use_case_version', 'energy.poen.use_case_version', 'energy.podf.use_case_version', 'energy.tout.use_case_version', 'energy.itpcm.use_case_version', 'energy.ohpcf.use_case_version', 'energy.lpc.heartbeat_timestamp', 'energy.lpp.heartbeat_timestamp', 'energy.lpc.heartbeat_counter', 'energy.lpp.heartbeat_counter', 'energy.itpcm.itpcm_031', 'energy.lpc.value_range_min', 'energy.lpp.value_range_min', 'energy.poen.value_range_min', 'energy.podf.value_range_min', 'energy.tout.value_range_min', 'energy.itpcm.value_range_min', 'energy.ohpcf.value_range_min', 'energy.lpc.per', 'energy.lpp.per', 'energy.poen.per', 'energy.podf.per', 'energy.tout.per', 'energy.itpcm.per', 'energy.ohpcf.per', 'energy.lpc.slots', 'energy.lpp.slots', 'energy.poen.slots', 'energy.podf.slots', 'energy.tout.slots', 'energy.itpcm.slots', 'energy.ohpcf.slots', 'energy.itpcm.simple_committed_incentive_table', 'energy.lpc.committed_power_plan', 'energy.lpp.committed_power_plan', 'energy.poen.committed_power_plan', 'energy.podf.committed_power_plan', 'energy.tout.committed_power_plan', 'energy.itpcm.committed_power_plan', 'energy.ohpcf.committed_power_plan', 'energy.ohpcf.flexibility', 'energy.ohpcf.alternatives', 'energy.ohpcf.is_pausable', 'energy.ohpcf.is_stoppable', 'energy.ohpcf.alternatives_count', 'energy.ohpcf.total_sequences_count_max', 'energy.ohpcf.supports_reselection', 'energy.ohpcf.sequence_id', 'energy.ohpcf.earliest_start_time', 'energy.ohpcf.latest_end_time', 'energy.ohpcf.default_duration', 'energy.ohpcf.active_duration_min', 'energy.ohpcf.pause_duration_min', 'energy.ohpcf.elapsed_slot_time', 'energy.ohpcf.remaining_slot_time', 'energy.capability.write_incentive_slot', 'energy.capability.set_local_generation_available', 'energy.capability.set_direct_control_activity_state', 'energy.capability.set_direct_control_energy_mode', 'energy.capability.set_direct_control_power', 'energy.capability.set_direct_control_energy', 'energy.operation.write_incentive_slot', 'energy.operation.set_local_generation_available', 'energy.operation.set_direct_control_activity_state', 'energy.operation.set_direct_control_energy_mode', 'energy.operation.set_direct_control_power', 'energy.operation.set_direct_control_energy', 'energy.effect.write_incentive_slot', 'energy.effect.set_local_generation_available', 'energy.effect.set_direct_control_activity_state', 'energy.effect.set_direct_control_energy_mode', 'energy.effect.set_direct_control_power', 'energy.effect.set_direct_control_energy', 'energy.event.price_changed', 'energy.event.grid_conditions_changed')
SIGNED_FIELDS = ('energy.esa.minimum_power', 'energy.esa.maximum_power', 'energy.esa.adjustment_minimum_power', 'energy.esa.adjustment_maximum_power', 'energy.esa.requested_power', 'energy.series.slot_power_nominal', 'energy.series.slot_power_minimum', 'energy.series.slot_power_maximum', 'energy.series.slot_energy_nominal', 'energy.series.slot_adjustment_minimum_power', 'energy.series.slot_adjustment_maximum_power', 'energy.tariff.randomization_offset', 'energy.price.current', 'energy.price.forecast_price', 'energy.incentive.incentive_value', 'energy.tariff.day_entry_randomization_offset', 'energy.tariff.component_price')
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
    'energy.tariff.label': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.provider': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.currency': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.unit_basis': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": ('energy.tariff.unit_basis.apparent_energy', 'energy.tariff.unit_basis.energy'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.block_mode': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": ('energy.tariff.block_mode.combined', 'energy.tariff.block_mode.individual', 'energy.tariff.block_mode.no_block'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.direction': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": ('energy.tariff.direction.consumption', 'energy.tariff.direction.production'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.status': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": ('energy.tariff.status.committed', 'energy.tariff.status.preliminary'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.price_kind': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": ('energy.tariff.price_kind.energy', 'energy.tariff.price_kind.energy_and_transmission', 'energy.tariff.price_kind.transmission'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.randomization_offset': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.tariff.randomization_kind': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": ('energy.tariff.randomization_kind.fixed', 'energy.tariff.randomization_kind.none', 'energy.tariff.randomization_kind.random', 'energy.tariff.randomization_kind.random_negative', 'energy.tariff.randomization_kind.random_positive'), "bounds": None, "direction": 'not_applicable'},
    'energy.price.current': {"kind": 'quantity', "unit": 'unit.currency_per_joule', "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.price.current_level': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "-32768", "exponent10": 0}, "maximum": {"coefficient": "32767", "exponent10": 0}}, "direction": 'not_applicable'},
    'energy.price.current_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.price.current_end': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.price.current_description': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.price.forecast_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.price.forecast_end': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.price.forecast_price': {"kind": 'quantity', "unit": 'unit.currency_per_joule', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.price.forecast_level': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": {"minimum": {"coefficient": "-32768", "exponent10": 0}, "maximum": {"coefficient": "32767", "exponent10": 0}}, "direction": 'not_applicable'},
    'energy.incentive.slot_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.slot',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.incentive.slot_end': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.slot',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.incentive.tier_kind': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.slot', 'energy.dimension.tier'), "symbols": ('energy.incentive.tier_kind.dynamic_cost', 'energy.incentive.tier_kind.fixed_cost'), "bounds": None, "direction": 'not_applicable'},
    'energy.incentive.boundary_lower': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.boundary', 'energy.dimension.slot', 'energy.dimension.tier'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.incentive.boundary_upper': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.boundary', 'energy.dimension.slot', 'energy.dimension.tier'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.incentive.incentive_value': {"kind": 'quantity', "unit": 'unit.currency_per_joule', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.incentive', 'energy.dimension.slot', 'energy.dimension.tier'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.incentive.incentive_kind': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.incentive', 'energy.dimension.slot', 'energy.dimension.tier'), "symbols": ('energy.incentive.incentive_kind.absolute_cost', 'energy.incentive.incentive_kind.co2_emission', 'energy.incentive.incentive_kind.relative_cost', 'energy.incentive.incentive_kind.renewable_energy_percentage'), "bounds": None, "direction": 'not_applicable'},
    'energy.incentive.renewable_ratio': {"kind": 'quantity', "unit": 'unit.ratio', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.incentive', 'energy.dimension.slot', 'energy.dimension.tier'), "symbols": (), "bounds": {"minimum": {"coefficient": "0", "exponent10": 0}, "maximum": {"coefficient": "1", "exponent10": 0}}, "direction": 'not_applicable'},
    'energy.incentive.co2_intensity': {"kind": 'quantity', "unit": 'unit.kilogram_per_joule', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.incentive', 'energy.dimension.slot', 'energy.dimension.tier'), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.incentive.maximum_tiers': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": {"minimum": {"coefficient": "3", "exponent10": 0}, "maximum": None}, "direction": 'not_applicable'},
    'energy.incentive.maximum_slots': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.negotiation.simulation_cycles_maximum': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.negotiation.simulation_concurrent': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.negotiation.request_timeout': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.negotiation.writeable_wait': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.tariff.day_entry_start': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.day_entry',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.tariff.day_entry_duration': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.day_entry',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.tariff.day_entry_randomization_offset': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.day_entry',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.tariff.day_pattern_days': {"kind": 'symbols', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.day_pattern',), "symbols": ('energy.tariff.day_pattern_days.friday', 'energy.tariff.day_pattern_days.monday', 'energy.tariff.day_pattern_days.saturday', 'energy.tariff.day_pattern_days.sunday', 'energy.tariff.day_pattern_days.thursday', 'energy.tariff.day_pattern_days.tuesday', 'energy.tariff.day_pattern_days.wednesday'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.day_pattern_entry': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.day_entry', 'energy.dimension.day_pattern'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.calendar_period_start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.calendar_period',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.calendar_period_pattern': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.calendar_period', 'energy.dimension.day_pattern'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.individual_day_date': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.individual_day',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.individual_day_kind': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.individual_day',), "symbols": ('energy.tariff.individual_day_kind.dynamic', 'energy.tariff.individual_day_kind.event', 'energy.tariff.individual_day_kind.holiday', 'energy.tariff.individual_day_kind.standard'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.individual_day_entry': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.day_entry', 'energy.dimension.individual_day'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.component_price': {"kind": 'quantity', "unit": 'unit.currency_per_joule', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.tariff.component_price_kind': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": ('energy.tariff.component_price_kind.critical', 'energy.tariff.component_price_kind.incentive', 'energy.tariff.component_price_kind.incentive_signal', 'energy.tariff.component_price_kind.standard', 'energy.tariff.component_price_kind.virtual'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.component_friendly_credit': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.component_auxiliary_load': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": ('energy.tariff.component_auxiliary_load.none', 'energy.tariff.component_auxiliary_load.off', 'energy.tariff.component_auxiliary_load.on'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.component_peak_period': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": ('energy.tariff.component_peak_period.high', 'energy.tariff.component_peak_period.low', 'energy.tariff.component_peak_period.medium', 'energy.tariff.component_peak_period.unused'), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.component_power_threshold': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.tariff.component_apparent_power_threshold': {"kind": 'quantity', "unit": 'unit.volt_ampere', "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.tariff.component_threshold': {"kind": 'quantity', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.tariff.component_label': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.component_predicted': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.period_label': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.tariff_period',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.period_entry': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.day_entry', 'energy.dimension.tariff_period'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.period_component': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": ('energy.dimension.component', 'energy.dimension.tariff_period'), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.current_day_entry': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.current_day_entry_date': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.next_day_entry': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.next_day_entry_date': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.current_day': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.next_day': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.current_components': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tariff.next_components': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.tariff', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.metering.quantity': {"kind": 'quantity', "unit": 'unit.joule', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.component',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'non_negative'},
    'energy.metering.timestamp': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.metering.maximum_quantities': {"kind": 'quantity', "unit": 'unit.one', "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.grid.local_generation_available': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.grid.start': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.grid.end': {"kind": 'time', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.grid.carbon_intensity': {"kind": 'quantity', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.grid.carbon_level': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": ('energy.grid.carbon_level.high', 'energy.grid.carbon_level.low', 'energy.grid.carbon_level.medium'), "bounds": None, "direction": 'not_applicable'},
    'energy.grid.local_carbon_intensity': {"kind": 'quantity', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.grid.local_carbon_level': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.forecast_slot',), "symbols": ('energy.grid.local_carbon_level.high', 'energy.grid.local_carbon_level.low', 'energy.grid.local_carbon_level.medium'), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.timestamp': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.activity_state': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": ('energy.direct_control.activity_state.inactive', 'energy.direct_control.activity_state.paused', 'energy.direct_control.activity_state.running'), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.is_activity_state_changeable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.energy_mode': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.is_energy_mode_changeable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.power': {"kind": 'quantity', "unit": 'unit.watt', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.direct_control.is_power_changeable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.energy': {"kind": 'quantity', "unit": 'unit.joule', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.direct_control.is_energy_changeable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.sequence_id': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.direct_control_timestamp',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.positive_energy_direction': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.power_unit': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.direct_control.energy_unit': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.job_id': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.timestamp': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.job_state': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.elapsed_time': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.task.remaining_time': {"kind": 'quantity', "unit": 'unit.second', "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": {"minimum": None, "maximum": None}, "direction": 'not_applicable'},
    'energy.task.direct_control_related': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.hvac_related': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.hvac_related_overrun_id': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.load_control_releated': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.load_control_releated_event_id': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.power_sequences_related': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.power_sequences_related_sequence_id': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.smart_energy_management_ps_related': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.smart_energy_management_ps_related_sequence_id': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.job_source': {"kind": 'symbol', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": ('energy.task.job_source.external_configuration', 'energy.task.job_source.internal_mechanism', 'energy.task.job_source.user_interaction'), "bounds": None, "direction": 'not_applicable'},
    'energy.task.label': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.description': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": ('energy.dimension.job',), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.remote_controllable': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.task.jobs_active': {"kind": 'boolean', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.use_case_name': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.use_case_name': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.poen.use_case_name': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.podf.use_case_name': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tout.use_case_name': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.use_case_name': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.use_case_name': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.actor': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.actor': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.poen.actor': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.podf.actor': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tout.actor': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.actor': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.actor': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.use_case_version': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.use_case_version': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.poen.use_case_version': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.podf.use_case_version': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tout.use_case_version': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.use_case_version': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.use_case_version': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.heartbeat_timestamp': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.heartbeat_timestamp': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.heartbeat_counter': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.heartbeat_counter': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.itpcm_031': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.value_range_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.value_range_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.poen.value_range_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.podf.value_range_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tout.value_range_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.value_range_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.value_range_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.per': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.per': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.poen.per': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.podf.per': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tout.per': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.per': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.per': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.slots': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.slots': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.poen.slots': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.podf.slots': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tout.slots': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.slots': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.slots': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.simple_committed_incentive_table': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpc.committed_power_plan': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.lpp.committed_power_plan': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.poen.committed_power_plan': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.podf.committed_power_plan': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.tout.committed_power_plan': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.itpcm.committed_power_plan': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.committed_power_plan': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.flexibility': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.alternatives': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.is_pausable': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.is_stoppable': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.alternatives_count': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.total_sequences_count_max': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.supports_reselection': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.sequence_id': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.earliest_start_time': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.latest_end_time': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.default_duration': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.active_duration_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.pause_duration_min': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.elapsed_slot_time': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
    'energy.ohpcf.remaining_slot_time': {"kind": 'text', "unit": None, "dimension": 'energy.dimension.subject', "qualifiers": (), "symbols": (), "bounds": None, "direction": 'not_applicable'},
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
    'energy.operation.write_incentive_slot': {"capability": 'energy.capability.write_incentive_slot', "effect_rule": 'energy.effect.write_incentive_slot', "service": 'energy.service.tariff', "arguments": ('energy.incentive.incentive_value',), "parameters": ('energy.incentive.boundary_lower', 'energy.incentive.boundary_upper', 'energy.incentive.incentive_kind', 'energy.incentive.slot_end', 'energy.incentive.slot_start', 'energy.incentive.tier_kind'), "admission": 'eebus'},
    'energy.operation.set_local_generation_available': {"capability": 'energy.capability.set_local_generation_available', "effect_rule": 'energy.effect.set_local_generation_available', "service": 'energy.service.subject', "arguments": ('energy.grid.local_generation_available',), "parameters": (), "admission": 'matter_baseline'},
    'energy.operation.set_direct_control_activity_state': {"capability": 'energy.capability.set_direct_control_activity_state', "effect_rule": 'energy.effect.set_direct_control_activity_state', "service": 'energy.service.subject', "arguments": ('energy.direct_control.activity_state',), "parameters": (), "admission": 'eebus'},
    'energy.operation.set_direct_control_energy_mode': {"capability": 'energy.capability.set_direct_control_energy_mode', "effect_rule": 'energy.effect.set_direct_control_energy_mode', "service": 'energy.service.subject', "arguments": ('energy.direct_control.energy_mode',), "parameters": (), "admission": 'eebus'},
    'energy.operation.set_direct_control_power': {"capability": 'energy.capability.set_direct_control_power', "effect_rule": 'energy.effect.set_direct_control_power', "service": 'energy.service.subject', "arguments": ('energy.direct_control.power',), "parameters": (), "admission": 'eebus'},
    'energy.operation.set_direct_control_energy': {"capability": 'energy.capability.set_direct_control_energy', "effect_rule": 'energy.effect.set_direct_control_energy', "service": 'energy.service.subject', "arguments": ('energy.direct_control.energy',), "parameters": (), "admission": 'eebus'},
}

QUALIFIER_CONTRACTS = {
    'energy.dimension.slot': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.series': {"value_kind": 'symbol', "unit": None, "symbols": ('charging_plan', 'charging_power_limit_curve', 'committed_power_plan', 'consumption_limit_curve', 'fallback_consumption_limit_curve', 'fallback_production_limit_curve', 'forecast', 'power_demand_forecast', 'preliminary_power_plan', 'production_limit_curve'), "admission": 'matter_baseline'},
    'energy.dimension.adjustment_range': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.sequence': {"value_kind": 'text', "unit": None, "symbols": (), "admission": 'eebus'},
    'energy.dimension.balance': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.tier': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.boundary': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.incentive': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.component': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.day_entry': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.day_pattern': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.calendar_period': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.tariff_period': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.individual_day': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.forecast_slot': {"value_kind": 'quantity', "unit": 'unit.one', "symbols": (), "admission": 'matter_baseline'},
    'energy.dimension.direct_control_timestamp': {"value_kind": 'text', "unit": None, "symbols": (), "admission": 'eebus'},
    'energy.dimension.job': {"value_kind": 'text', "unit": None, "symbols": (), "admission": 'eebus'},
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


FACT_DIMENSIONS = {
    'energy.dimension.subject': 'text',
    'energy.dimension.tariff': 'text',
}
SERVICES = {
    'energy.service.subject': 'energy.dimension.subject',
    'energy.service.tariff': 'energy.dimension.tariff',
}
READ_CAPABILITIES = {
    'energy.capability.read.subject': 'energy.service.subject',
    'energy.capability.read.tariff': 'energy.service.tariff',
}
TARIFF_PORTAL = 'energy.portal.read.tariff'
TARIFF_PORTAL_FIELDS = ('energy.incentive.boundary_lower', 'energy.incentive.boundary_upper', 'energy.incentive.co2_intensity', 'energy.incentive.incentive_kind', 'energy.incentive.incentive_value', 'energy.incentive.maximum_slots', 'energy.incentive.maximum_tiers', 'energy.incentive.renewable_ratio', 'energy.incentive.slot_end', 'energy.incentive.slot_start', 'energy.incentive.tier_kind', 'energy.price.current', 'energy.price.current_description', 'energy.price.current_end', 'energy.price.current_level', 'energy.price.current_start', 'energy.price.forecast_end', 'energy.price.forecast_level', 'energy.price.forecast_price', 'energy.price.forecast_start', 'energy.tariff.block_mode', 'energy.tariff.calendar_period_pattern', 'energy.tariff.calendar_period_start', 'energy.tariff.component_apparent_power_threshold', 'energy.tariff.component_auxiliary_load', 'energy.tariff.component_friendly_credit', 'energy.tariff.component_label', 'energy.tariff.component_peak_period', 'energy.tariff.component_power_threshold', 'energy.tariff.component_predicted', 'energy.tariff.component_price', 'energy.tariff.component_price_kind', 'energy.tariff.component_threshold', 'energy.tariff.currency', 'energy.tariff.current_components', 'energy.tariff.current_day', 'energy.tariff.current_day_entry', 'energy.tariff.current_day_entry_date', 'energy.tariff.day_entry_duration', 'energy.tariff.day_entry_randomization_offset', 'energy.tariff.day_entry_start', 'energy.tariff.day_pattern_days', 'energy.tariff.day_pattern_entry', 'energy.tariff.direction', 'energy.tariff.individual_day_date', 'energy.tariff.individual_day_entry', 'energy.tariff.individual_day_kind', 'energy.tariff.label', 'energy.tariff.next_components', 'energy.tariff.next_day', 'energy.tariff.next_day_entry', 'energy.tariff.next_day_entry_date', 'energy.tariff.period_component', 'energy.tariff.period_entry', 'energy.tariff.period_label', 'energy.tariff.price_kind', 'energy.tariff.provider', 'energy.tariff.randomization_kind', 'energy.tariff.randomization_offset', 'energy.tariff.start', 'energy.tariff.status', 'energy.tariff.unit_basis')
EVENT_CONTRACTS = {
    'energy.event.price_changed': {"service": 'energy.service.tariff', "trigger": 'energy.price.current', "condition": 'changed', "origin": 'emitted'},
    'energy.event.grid_conditions_changed': {"service": 'energy.service.subject', "trigger": 'energy.grid.carbon_level', "condition": 'changed', "origin": 'emitted'},
}


def check_subject(items):
    found = {item["id"]: item for item in items}
    require(set(found) == set(FACT_DIMENSIONS), "fact dimensions")
    for ident, item in found.items():
        require(item.get("value_kind") == FACT_DIMENSIONS[ident], "fact dimension value_kind")
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
    found = {item["id"]: item for item in items}
    require(set(found) == set(SERVICES), "service")
    for ident, item in found.items():
        require(item.get("fact_key_dimension") == SERVICES[ident], "service fact_key_dimension")
    check_refs(items, "service")
    check_orders(items, "services")


def check_capabilities(items, operations):
    expected = dict(READ_CAPABILITIES)
    for contract in OPERATION_CONTRACTS.values():
        expected[contract["capability"]] = contract["service"]
    found = [item["id"] for item in items]
    require(set(found) == set(expected), "capabilities")
    check_orders(items, "capabilities")
    check_refs(items, "capability")
    for item in items:
        require(item.get("service") == expected[item["id"]], f"{item['id']} service")
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
    found = {item["id"]: item for item in items}
    require(set(found) == {READ_PORTAL, TARIFF_PORTAL}, "portal")
    subject_fields = sorted(ident for ident, contract in FIELD_CONTRACTS.items() if contract["dimension"] == SUBJECT)
    subject = found[READ_PORTAL]
    tariff = found[TARIFF_PORTAL]
    require(subject.get("kind") == "read" and tariff.get("kind") == "read", "portal kind")
    require(subject.get("service") == SERVICE and tariff.get("service") == "energy.service.tariff", "portal service")
    require(subject.get("fields") == subject_fields, "portal fields")
    require(tariff.get("fields") == list(TARIFF_PORTAL_FIELDS), "portal fields")
    require(set(subject_fields).isdisjoint(TARIFF_PORTAL_FIELDS), "portal fields")
    check_refs(items, "portal")
    check_orders(items, "portals")


def check_events(items):
    found = {item["id"]: item for item in items}
    require(set(found) == set(EVENT_CONTRACTS), "events")
    check_orders(items, "events")
    check_refs(items, "event")
    for ident, item in found.items():
        contract = EVENT_CONTRACTS[ident]
        require(item.get("service") == contract["service"], f"{ident} service")
        require(item.get("trigger") == contract["trigger"], f"{ident} trigger")
        require(item.get("condition") == contract["condition"], f"{ident} condition")
        require(item.get("origin") == contract["origin"], f"{ident} origin")
        require(item.get("payload") == [], f"{ident} payload")
        require("symbols" not in item, f"{ident} symbols")


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
    check_events(definitions["events"])
    check_page(page)


def main():
    validate(load(VECTORS), PAGE.read_text(encoding="utf-8"))
    print(f"energy management pack v1: PASS ({len(FIELD_CONTRACTS)} fields)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
