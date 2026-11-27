#!/usr/bin/env python3
"""Validate exact typed associations in the EVSE v1 catalog."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/packs/evse-acceptance-vectors.json"
DOCUMENT = ROOT / "api/v1/packs/evse-v1.md"
PACK = {"id": "helianthus.pack.evse", "version": "1.0.0"}
ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
# The SI unit set of the unit rule in api/README.md (a working reading): a pack field declares no customary or prefixed unit.
CANONICAL_UNITS = frozenset({"unit.ampere", "unit.ampere_hour", "unit.cubic_metre_per_second", "unit.hertz", "unit.joule",
                             "unit.kelvin", "unit.pascal", "unit.ratio", "unit.reciprocal_second", "unit.volt",
                             "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt", "unit.second", "unit.cubic_metre", "unit.metre", "unit.ohm", "unit.radian", "unit.one", "unit.volt_ampere_reactive_second", "unit.volt_ampere_second", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre", "unit.kilogram_per_joule", "unit.watt_per_square_metre", "unit.metre_per_joule", "unit.currency", "unit.currency_per_joule"})
DOMAINS = {"thermal_hvac": ("helianthus.pack.thermal", "accepted"),
           "pv_inverter": ("helianthus.pack.pv", "accepted"),
           "storage_bms": ("helianthus.pack.storage", "accepted"),
           "evse": ("helianthus.pack.evse", "accepted"),
           "infrastructure": ("helianthus.pack.infrastructure", "follow_on")}
PINS = {"semantic_docs": "f81f04b026ccfc0bb4107c5a361e7bee146a166a",
        "semreg": "cc9b324225e945598128eeabe977e7fa0af6dc93",
        "tesla_docs_modbus": "d16ff91ff808803fa31c67a6a10eb2a4faa70937",
        "tesla_modbusreg": "75e4e3988a7682068c02d8ac24f737b7f24a029f",
        "eebus_ledger": "81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1",
        "eebus_m625_donor": "cedf238e34f879815ba773e9cd76b2b31c2822a3",
        "matter_draft": "29b4768a513cf566011ab8cd60df1bc495204953"}
LIFECYCLE = {"source_epoch", "driver_generation", "semantic_revision",
             "capability_qualification", "activation", "generation_fencing",
             "partial_updates", "stale_unknown_evidence", "last_known_good_retention"}
POLICY = {"admission": ["exact_source_epoch", "current_driver_generation",
                          "exact_semantic_revision", "qualified_active_capability"],
          "stale_generation": "reject",
          "partial_publication": "supplied_valid_only_preserve_permitted_last_known_good",
          "withdrawal": "explicit_generation_fenced",
          "evidence": "stale_unknown_never_promote_or_authorize",
          "tombstone": "retained_non_actionable"}
COUNTER = {"session_and_lifetime_energy": "native_reset_or_wrap_evidence_required",
           "decrease": "never_infer_reset_or_wrap",
           "projection": "counter_continuity_or_loss_explicit"}
AVAILABILITY = {"effective_availability": "kernel_observation_and_capability_state_only",
                "native_readiness": "evse.status.readiness",
                "portal": "consume_kernel_availability_separately"}
LOSS = {"native_enum_bitfield", "precision_range", "connector_phase_session_meter_topology",
        "direction_reference", "counter_reset_wrap", "unavailable_fields",
        "conflicting_sources", "vendor_extensions", "unsupported_operations"}
DIMS = {"evse.dimension.asset", "evse.dimension.evse", "evse.dimension.connector",
        "evse.dimension.phase", "evse.dimension.session", "evse.dimension.meter", "evse.dimension.vehicle"}
FIELD_CONTRACTS = {
    "evse.ac.voltage": ("quantity", "unit.volt", "evse.dimension.phase", True, None, ("0", 0, "1", 3)),
    "evse.ac.current": ("quantity", "unit.ampere", "evse.dimension.phase", True, None, ("0", 0, "1", 3)),
    "evse.ac.active_power": ("quantity", "unit.watt", "evse.dimension.phase", True, None, ("-1", 7, "1", 7)),
    "evse.ac.frequency": ("quantity", "unit.hertz", "evse.dimension.evse", True, None, ("0", 0, "1", 3)),
    "evse.energy.session": ("quantity", "unit.joule", "evse.dimension.session", True, None, ("0", 0, "36", 17)),
    "evse.energy.lifetime": ("quantity", "unit.joule", "evse.dimension.meter", True, None, ("0", 0, "36", 17)),
    "evse.limit.advertised_current": ("quantity", "unit.ampere", "evse.dimension.connector", True, None, ("0", 0, "1", 3)),
    "evse.limit.configured_current": ("quantity", "unit.ampere", "evse.dimension.evse", True, None, ("0", 0, "1", 3)),
    "evse.limit.allocated_current": ("quantity", "unit.ampere", "evse.dimension.connector", True, None, ("0", 0, "1", 3)),
    "evse.limit.allocated_current_phase": ("quantity", "unit.ampere", "evse.dimension.phase", True, None, ("0", 0, "1", 3)),
    "evse.limit.actual_current": ("quantity", "unit.ampere", "evse.dimension.connector", True, None, ("0", 0, "1", 3)),
    "evse.status.connection": ("symbol", None, "evse.dimension.connector", True, ("evse.status.connection.connected", "evse.status.connection.disconnected"), None),
    "evse.status.charging": ("symbol", None, "evse.dimension.connector", True, ("evse.status.charging.charging", "evse.status.charging.complete", "evse.status.charging.idle"), None),
    "evse.status.readiness": ("symbol", None, "evse.dimension.evse", True, ("evse.status.readiness.not_ready", "evse.status.readiness.ready"), None),
    "evse.status.fault": ("symbol", None, "evse.dimension.evse", True, ("evse.status.fault.clear", "evse.status.fault.present"), None),
    "evse.status.interlock": ("symbol", None, "evse.dimension.connector", True, ("evse.status.interlock.active", "evse.status.interlock.clear"), None),

    'evse.status.state': ('symbol', None, 'evse.dimension.connector', True, ('evse.status.state.fault', 'evse.status.state.not_plugged_in', 'evse.status.state.plugged_in_charging', 'evse.status.state.plugged_in_demand', 'evse.status.state.plugged_in_discharging', 'evse.status.state.plugged_in_no_demand', 'evse.status.state.session_ending'), None),
    'evse.status.supply': ('symbol', None, 'evse.dimension.evse', True, ('evse.status.supply.charging_enabled', 'evse.status.supply.disabled', 'evse.status.supply.disabled_diagnostics', 'evse.status.supply.disabled_error', 'evse.status.supply.discharging_enabled', 'evse.status.supply.enabled'), None),
    'evse.status.fault_cause': ('symbol', None, 'evse.dimension.evse', True, ('evse.status.fault_cause.contact_dry_failure', 'evse.status.fault_cause.contact_wet_failure', 'evse.status.fault_cause.emergency_stop', 'evse.status.fault_cause.ev_disconnected', 'evse.status.fault_cause.ground_fault', 'evse.status.fault_cause.live_neutral_swap', 'evse.status.fault_cause.meter_failure', 'evse.status.fault_cause.no_error', 'evse.status.fault_cause.other', 'evse.status.fault_cause.over_current', 'evse.status.fault_cause.over_temperature', 'evse.status.fault_cause.over_voltage', 'evse.status.fault_cause.pilot_short_circuit', 'evse.status.fault_cause.power_loss', 'evse.status.fault_cause.power_quality', 'evse.status.fault_cause.under_voltage', 'evse.status.fault_cause.wrong_power_supply'), None),
    'evse.limit.charging_enabled_until': ('time', None, 'evse.dimension.evse', True, None, None),
    'evse.limit.allocated_current_expiry': ('time', None, 'evse.dimension.connector', True, None, None),
    'evse.limit.discharging_enabled_until': ('time', None, 'evse.dimension.evse', True, None, None),
    'evse.limit.minimum_charge_current': ('quantity', 'unit.ampere', 'evse.dimension.connector', True, None, None),
    'evse.limit.maximum_discharge_current': ('quantity', 'unit.ampere', 'evse.dimension.connector', True, None, None),
    'evse.limit.user_maximum_charge_current': ('quantity', 'unit.ampere', 'evse.dimension.evse', True, None, None),
    'evse.limit.failsafe_current': ('quantity', 'unit.ampere', 'evse.dimension.evse', True, None, None),
    'evse.limit.recommended_current_phase': ('quantity', 'unit.ampere', 'evse.dimension.phase', True, None, None),
    'evse.limit.vehicle_minimum_current_phase': ('quantity', 'unit.ampere', 'evse.dimension.phase', True, None, None),
    'evse.limit.vehicle_maximum_current_phase': ('quantity', 'unit.ampere', 'evse.dimension.phase', True, None, None),
    'evse.configuration.randomization_delay_window': ('quantity', 'unit.second', 'evse.dimension.evse', True, None, None),
    'evse.mode': ('quantity', 'unit.one', 'evse.dimension.evse', True, None, None),
    'evse.mode_supported': ('text', None, 'evse.dimension.evse', True, None, None),
    'evse.ac.total_active_power': ('quantity', 'unit.watt', 'evse.dimension.evse', True, None, None),
    'evse.ac.connected_phases': ('quantity', 'unit.one', 'evse.dimension.connector', True, None, None),
    'evse.energy.lifetime_exported': ('quantity', 'unit.joule', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.measured': ('boolean', None, 'evse.dimension.meter', True, None, None),
    'evse.accuracy.ratio_maximum': ('quantity', 'unit.ratio', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.measured_minimum_active_current': ('quantity', 'unit.ampere', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.measured_maximum_active_current': ('quantity', 'unit.ampere', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.range_minimum_active_current': ('quantity', 'unit.ampere', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.range_maximum_active_current': ('quantity', 'unit.ampere', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.measured_minimum_active_power': ('quantity', 'unit.watt', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.measured_maximum_active_power': ('quantity', 'unit.watt', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.range_minimum_active_power': ('quantity', 'unit.watt', 'evse.dimension.meter', True, None, None),
    'evse.accuracy.range_maximum_active_power': ('quantity', 'unit.watt', 'evse.dimension.meter', True, None, None),
    'evse.session.identifier': ('text', None, 'evse.dimension.session', True, None, None),
    'evse.session.start': ('time', None, 'evse.dimension.session', True, None, None),
    'evse.session.duration': ('quantity', 'unit.second', 'evse.dimension.session', True, None, None),
    'evse.energy.session_discharged': ('quantity', 'unit.joule', 'evse.dimension.session', True, None, None),
    'evse.session.rfid_token': ('text', None, 'evse.dimension.session', True, None, None),
    'evse.session.communication_standard': ('symbol', None, 'evse.dimension.session', True, ('evse.session.communication_standard.iec_61851', 'evse.session.communication_standard.iso_15118_2', 'evse.session.communication_standard.iso_15118_20'), None),
    'evse.session.asymmetric_charging': ('boolean', None, 'evse.dimension.session', True, None, None),
    'evse.demand.minimum_energy': ('quantity', 'unit.joule', 'evse.dimension.session', True, None, None),
    'evse.demand.optimal_energy': ('quantity', 'unit.joule', 'evse.dimension.session', True, None, None),
    'evse.demand.maximum_energy': ('quantity', 'unit.joule', 'evse.dimension.session', True, None, None),
    'evse.demand.departure_time': ('time', None, 'evse.dimension.session', True, None, None),
    'evse.summary.energy_grid': ('quantity', 'unit.joule', 'evse.dimension.session', True, None, None),
    'evse.summary.energy_self_produced': ('quantity', 'unit.joule', 'evse.dimension.session', True, None, None),
    'evse.summary.self_produced_ratio': ('quantity', 'unit.ratio', 'evse.dimension.session', True, None, None),
    'evse.summary.cost': ('quantity', 'unit.currency', 'evse.dimension.session', True, None, None),
    'evse.summary.currency': ('text', None, 'evse.dimension.session', True, None, None),
    'evse.summary.end': ('time', None, 'evse.dimension.session', True, None, None),
    'evse.target.schedule_count': ('quantity', 'unit.one', 'evse.dimension.evse', True, None, None),
    'evse.target.days': ('symbols', None, 'evse.dimension.evse', True, ('evse.target.days.friday', 'evse.target.days.monday', 'evse.target.days.saturday', 'evse.target.days.sunday', 'evse.target.days.thursday', 'evse.target.days.tuesday', 'evse.target.days.wednesday'), None),
    'evse.target.time_of_day': ('quantity', 'unit.second', 'evse.dimension.evse', True, None, None),
    'evse.target.state_of_charge': ('quantity', 'unit.ratio', 'evse.dimension.evse', True, None, None),
    'evse.target.added_energy': ('quantity', 'unit.joule', 'evse.dimension.evse', True, None, None),
    'evse.target.next_start': ('time', None, 'evse.dimension.evse', True, None, None),
    'evse.target.next_target_time': ('time', None, 'evse.dimension.evse', True, None, None),
    'evse.target.next_required_energy': ('quantity', 'unit.joule', 'evse.dimension.evse', True, None, None),
    'evse.target.next_state_of_charge': ('quantity', 'unit.ratio', 'evse.dimension.evse', True, None, None),
    'evse.vehicle.approximate_efficiency': ('quantity', None, 'evse.dimension.evse', True, None, None),
    'evse.vehicle.state_of_charge': ('quantity', 'unit.ratio', 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.battery_capacity': ('quantity', 'unit.joule', 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.state_of_health': ('quantity', 'unit.ratio', 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.travel_range': ('quantity', 'unit.metre', 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.identifier': ('text', None, 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.minimum_power': ('quantity', 'unit.watt', 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.maximum_power': ('quantity', 'unit.watt', 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.standby_power': ('quantity', 'unit.watt', 'evse.dimension.vehicle', True, None, None),
    'evse.vehicle.sleep': ('symbol', None, 'evse.dimension.vehicle', True, ('evse.vehicle.sleep.awake', 'evse.vehicle.sleep.sleeping'), None),
    'evse.vehicle.connection': ('symbol', None, 'evse.dimension.vehicle', True, ('evse.vehicle.connection.connected', 'evse.vehicle.connection.disconnected'), None),
    'evse.vehicle.ac_power': ('quantity', 'unit.watt', 'evse.dimension.vehicle', True, None, None),

    'evse.cevc.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.cevc_001': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.cevc_007': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.cevc_012': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.cevc_015': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.cevc_023': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.cevc_028': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.cevc_054': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.earliest_time_series_start_time': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.heartbeat_counter': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.heartbeat_timeout': ('quantity', 'unit.second', 'evse.dimension.connector', True, None, (None, None, '6', 1)),
    'evse.cevc.heartbeat_timestamp': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.incentive_slot': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.incentive_slot_constraints': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.incentive_table': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.incentive_table_constraints': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.incentive_table_description': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.measurement_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.operating_state': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.slot_count_max': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.slot_count_min': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.slot_duration_min': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.slot_value_max': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.slot_value_min': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.slot_value_step_size': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.tariff_constraints': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.tariff_description': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.tier': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.time_period': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.time_series_constraints_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.time_series_description_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.time_series_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.time_series_slot': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.time_series_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.time_series_writeable': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.unit': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.cevc.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.device_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.evcc_006': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.evcc_007': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.evcc_017': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.evcc_018': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.evcc_019': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.identification_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.identification_value': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.iso15118': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.key_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.key_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.manufacturer_description': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.measurement_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.one': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.operating_state': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.parameter_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.value_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcc.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.ac_measured_phases': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.ac_measurement_variant': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.current': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.measurement_constraints_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.measurement_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.measurement_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.parameter_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.timestamp': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.value_range_min': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.value_source': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcem.voltage_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.bill_constraints_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.bill_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.bill_description_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.bill_writeable': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.evcs_009': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.position': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.position_count_max': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.position_count_min': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.supported_bill_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.total': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evcs.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.device_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.operating_state': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsecc.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.characteristic_context': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.commodity_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.current': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.evsoc_002': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.measurement_constraints_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.measurement_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.measurement_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.timestamp': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.value_range_min': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.value_source': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.value_state': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.evsoc.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.heartbeat_counter': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.heartbeat_timeout': ('quantity', 'unit.second', 'evse.dimension.connector', True, None, (None, None, '4', 0)),
    'evse.opev.heartbeat_timestamp': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.is_limit_changeable': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.last_error_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.limit_category': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.limit_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.load_control_limit_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.load_control_limit_description_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.measurement_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.opev_004': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.parameter_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.scale': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.unit': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.opev.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.actor': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.brand_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.device_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.electrical_connection_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.hardware_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.heartbeat_counter': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.heartbeat_timeout': ('quantity', 'unit.second', 'evse.dimension.connector', True, None, (None, None, '4', 0)),
    'evse.oscev.heartbeat_timestamp': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.is_limit_changeable': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.limit_category': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.limit_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.load_control_limit_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.load_control_limit_description_data': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.manufacturer_label': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.measurement_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.operating_state': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.parameter_id': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.permitted_value_set': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.scale': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.scope_type': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.serial_number': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.software_revision': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.unit': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.use_case_name': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.use_case_version': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.vendor_code': ('text', None, 'evse.dimension.connector', True, None, None),
    'evse.oscev.vendor_name': ('text', None, 'evse.dimension.connector', True, None, None),
}
SERVICES = {"evse.service.evse": "evse.dimension.evse",
            "evse.service.connector": "evse.dimension.connector",
            "evse.service.phase": "evse.dimension.phase",
            "evse.service.session": "evse.dimension.session",
            "evse.service.meter": "evse.dimension.meter",
            "evse.service.vehicle": "evse.dimension.vehicle"}
RELATIONS = {"evse.relation.asset_evse": ("evse.dimension.asset", "evse.dimension.evse", "one_to_many"),
             "evse.relation.evse_connector": ("evse.dimension.evse", "evse.dimension.connector", "one_to_many"),
             "evse.relation.connector_phase": ("evse.dimension.connector", "evse.dimension.phase", "one_to_many"),
             "evse.relation.connector_session": ("evse.dimension.connector", "evse.dimension.session", "one_to_many_over_time"),
             "evse.relation.evse_meter": ("evse.dimension.evse", "evse.dimension.meter", "one_to_many"),
             "evse.relation.connector_vehicle": ("evse.dimension.connector", "evse.dimension.vehicle", "one_to_one")}
DEFINITION_GROUPS = {"fields", "fact_dimensions", "services", "relations", "capabilities", "operations",
                     "effect_rules", "portal_contributions", "qualifier_dimensions", "events"}
CAPS = {"evse.capability.read.evse": ("evse.service.evse", ()),
        "evse.capability.read.connector": ("evse.service.connector", ()),
        "evse.capability.read.phase": ("evse.service.phase", ()),
        "evse.capability.read.session": ("evse.service.session", ()),
        "evse.capability.read.meter": ("evse.service.meter", ()),
        "evse.capability.set_allocated_current": ("evse.service.connector", ("evse.limit.allocated_current",)),
    "evse.capability.read.vehicle": ("evse.service.vehicle", ()),
    'evse.capability.set_supply': ('evse.service.evse', ('evse.status.supply',)),
    'evse.capability.set_allocated_current_with_expiry': ('evse.service.connector', ('evse.limit.allocated_current',)),
    'evse.capability.set_user_maximum_charge_current': ('evse.service.evse', ('evse.limit.user_maximum_charge_current',)),
    'evse.capability.set_randomization_delay_window': ('evse.service.evse', ('evse.configuration.randomization_delay_window',)),
    'evse.capability.set_vehicle_efficiency': ('evse.service.evse', ('evse.vehicle.approximate_efficiency',)),
    'evse.capability.set_target': ('evse.service.evse', ('evse.target.time_of_day',)),
    'evse.capability.clear_targets': ('evse.service.evse', ('evse.target.schedule_count',)),
    'evse.capability.set_evse_mode': ('evse.service.evse', ('evse.mode',)),
    'evse.capability.set_allocated_current_phase': ('evse.service.phase', ('evse.limit.allocated_current_phase',)),
    'evse.capability.set_recommended_current_phase': ('evse.service.phase', ('evse.limit.recommended_current_phase',)),
    'evse.capability.set_failsafe_current': ('evse.service.evse', ('evse.limit.failsafe_current',)),}
OP = "evse.operation.set_allocated_current"
EFFECT = "evse.effect.set_allocated_current"
PRECONDITIONS = ["current_source_epoch", "current_driver_generation", "current_semantic_revision", "qualified_active_capability", "exact_route", "authority_admitted"]
STAGES = ["admission", "dispatch", "acknowledgement", "readback", "terminal_outcome"]
OUTCOMES = ["rejected", "failed_no_contact", "acknowledged_unverified", "applied", "no_effect", "conflict", "indeterminate"]
PORTAL_READS = {"evse.portal.read.evse": ("evse.service.evse", ("evse.ac.frequency", "evse.limit.configured_current", "evse.status.fault", "evse.status.readiness", "evse.status.supply", "evse.status.fault_cause", "evse.limit.charging_enabled_until", "evse.limit.discharging_enabled_until", "evse.limit.user_maximum_charge_current", "evse.limit.failsafe_current", "evse.configuration.randomization_delay_window", "evse.mode", "evse.mode_supported", "evse.ac.total_active_power", "evse.target.schedule_count", "evse.target.days", "evse.target.time_of_day", "evse.target.state_of_charge", "evse.target.added_energy", "evse.target.next_start", "evse.target.next_target_time", "evse.target.next_required_energy", "evse.target.next_state_of_charge", "evse.vehicle.approximate_efficiency")),
                "evse.portal.read.connector": ("evse.service.connector", ("evse.limit.actual_current", "evse.limit.advertised_current", "evse.limit.allocated_current", "evse.status.charging", "evse.status.connection", "evse.status.interlock", "evse.status.state", "evse.limit.allocated_current_expiry", "evse.limit.minimum_charge_current", "evse.limit.maximum_discharge_current", "evse.ac.connected_phases", "evse.cevc.actor", "evse.cevc.brand_name", "evse.cevc.cevc_001", "evse.cevc.cevc_007", "evse.cevc.cevc_012", "evse.cevc.cevc_015", "evse.cevc.cevc_023", "evse.cevc.cevc_028", "evse.cevc.cevc_054", "evse.cevc.device_code", "evse.cevc.earliest_time_series_start_time", "evse.cevc.electrical_connection_id", "evse.cevc.hardware_revision", "evse.cevc.heartbeat_counter", "evse.cevc.heartbeat_timeout", "evse.cevc.heartbeat_timestamp", "evse.cevc.incentive_slot", "evse.cevc.incentive_slot_constraints", "evse.cevc.incentive_table", "evse.cevc.incentive_table_constraints", "evse.cevc.incentive_table_description", "evse.cevc.manufacturer_label", "evse.cevc.measurement_id", "evse.cevc.operating_state", "evse.cevc.permitted_value_set", "evse.cevc.scope_type", "evse.cevc.serial_number", "evse.cevc.slot_count_max", "evse.cevc.slot_count_min", "evse.cevc.slot_duration_min", "evse.cevc.slot_value_max", "evse.cevc.slot_value_min", "evse.cevc.slot_value_step_size", "evse.cevc.software_revision", "evse.cevc.tariff_constraints", "evse.cevc.tariff_description", "evse.cevc.tier", "evse.cevc.time_period", "evse.cevc.time_series_constraints_data", "evse.cevc.time_series_description_data", "evse.cevc.time_series_id", "evse.cevc.time_series_slot", "evse.cevc.time_series_type", "evse.cevc.time_series_writeable", "evse.cevc.unit", "evse.cevc.use_case_name", "evse.cevc.use_case_version", "evse.cevc.vendor_code", "evse.cevc.vendor_name", "evse.evcc.actor", "evse.evcc.brand_name", "evse.evcc.device_code", "evse.evcc.device_name", "evse.evcc.electrical_connection_id", "evse.evcc.evcc_006", "evse.evcc.evcc_007", "evse.evcc.evcc_017", "evse.evcc.evcc_018", "evse.evcc.evcc_019", "evse.evcc.hardware_revision", "evse.evcc.identification_id", "evse.evcc.identification_value", "evse.evcc.iso15118", "evse.evcc.key_id", "evse.evcc.key_name", "evse.evcc.manufacturer_description", "evse.evcc.manufacturer_label", "evse.evcc.measurement_id", "evse.evcc.one", "evse.evcc.operating_state", "evse.evcc.parameter_id", "evse.evcc.permitted_value_set", "evse.evcc.scope_type", "evse.evcc.serial_number", "evse.evcc.software_revision", "evse.evcc.use_case_name", "evse.evcc.use_case_version", "evse.evcc.value_type", "evse.evcc.vendor_code", "evse.evcc.vendor_name", "evse.evcem.ac_measured_phases", "evse.evcem.ac_measurement_variant", "evse.evcem.actor", "evse.evcem.brand_name", "evse.evcem.current", "evse.evcem.device_code", "evse.evcem.electrical_connection_id", "evse.evcem.hardware_revision", "evse.evcem.manufacturer_label", "evse.evcem.measurement_constraints_data", "evse.evcem.measurement_id", "evse.evcem.measurement_type", "evse.evcem.parameter_id", "evse.evcem.permitted_value_set", "evse.evcem.scope_type", "evse.evcem.serial_number", "evse.evcem.software_revision", "evse.evcem.timestamp", "evse.evcem.use_case_name", "evse.evcem.use_case_version", "evse.evcem.value_range_min", "evse.evcem.value_source", "evse.evcem.vendor_code", "evse.evcem.vendor_name", "evse.evcem.voltage_type", "evse.evcs.actor", "evse.evcs.bill_constraints_data", "evse.evcs.bill_data", "evse.evcs.bill_description_data", "evse.evcs.bill_writeable", "evse.evcs.brand_name", "evse.evcs.device_code", "evse.evcs.electrical_connection_id", "evse.evcs.evcs_009", "evse.evcs.hardware_revision", "evse.evcs.manufacturer_label", "evse.evcs.permitted_value_set", "evse.evcs.position", "evse.evcs.position_count_max", "evse.evcs.position_count_min", "evse.evcs.scope_type", "evse.evcs.serial_number", "evse.evcs.software_revision", "evse.evcs.supported_bill_type", "evse.evcs.total", "evse.evcs.use_case_name", "evse.evcs.use_case_version", "evse.evcs.vendor_code", "evse.evcs.vendor_name", "evse.evsecc.actor", "evse.evsecc.brand_name", "evse.evsecc.device_code", "evse.evsecc.device_name", "evse.evsecc.electrical_connection_id", "evse.evsecc.hardware_revision", "evse.evsecc.manufacturer_label", "evse.evsecc.operating_state", "evse.evsecc.permitted_value_set", "evse.evsecc.scope_type", "evse.evsecc.serial_number", "evse.evsecc.software_revision", "evse.evsecc.use_case_name", "evse.evsecc.use_case_version", "evse.evsecc.vendor_code", "evse.evsecc.vendor_name", "evse.evsoc.actor", "evse.evsoc.brand_name", "evse.evsoc.characteristic_context", "evse.evsoc.commodity_type", "evse.evsoc.current", "evse.evsoc.device_code", "evse.evsoc.electrical_connection_id", "evse.evsoc.evsoc_002", "evse.evsoc.hardware_revision", "evse.evsoc.manufacturer_label", "evse.evsoc.measurement_constraints_data", "evse.evsoc.measurement_id", "evse.evsoc.measurement_type", "evse.evsoc.permitted_value_set", "evse.evsoc.scope_type", "evse.evsoc.serial_number", "evse.evsoc.software_revision", "evse.evsoc.timestamp", "evse.evsoc.use_case_name", "evse.evsoc.use_case_version", "evse.evsoc.value_range_min", "evse.evsoc.value_source", "evse.evsoc.value_state", "evse.evsoc.vendor_code", "evse.evsoc.vendor_name", "evse.opev.actor", "evse.opev.brand_name", "evse.opev.device_code", "evse.opev.electrical_connection_id", "evse.opev.hardware_revision", "evse.opev.heartbeat_counter", "evse.opev.heartbeat_timeout", "evse.opev.heartbeat_timestamp", "evse.opev.is_limit_changeable", "evse.opev.last_error_code", "evse.opev.limit_category", "evse.opev.limit_type", "evse.opev.load_control_limit_data", "evse.opev.load_control_limit_description_data", "evse.opev.manufacturer_label", "evse.opev.measurement_id", "evse.opev.opev_004", "evse.opev.parameter_id", "evse.opev.permitted_value_set", "evse.opev.scale", "evse.opev.scope_type", "evse.opev.serial_number", "evse.opev.software_revision", "evse.opev.unit", "evse.opev.use_case_name", "evse.opev.use_case_version", "evse.opev.vendor_code", "evse.opev.vendor_name", "evse.oscev.actor", "evse.oscev.brand_name", "evse.oscev.device_code", "evse.oscev.electrical_connection_id", "evse.oscev.hardware_revision", "evse.oscev.heartbeat_counter", "evse.oscev.heartbeat_timeout", "evse.oscev.heartbeat_timestamp", "evse.oscev.is_limit_changeable", "evse.oscev.limit_category", "evse.oscev.limit_type", "evse.oscev.load_control_limit_data", "evse.oscev.load_control_limit_description_data", "evse.oscev.manufacturer_label", "evse.oscev.measurement_id", "evse.oscev.operating_state", "evse.oscev.parameter_id", "evse.oscev.permitted_value_set", "evse.oscev.scale", "evse.oscev.scope_type", "evse.oscev.serial_number", "evse.oscev.software_revision", "evse.oscev.unit", "evse.oscev.use_case_name", "evse.oscev.use_case_version", "evse.oscev.vendor_code", "evse.oscev.vendor_name")),
                "evse.portal.read.phase": ("evse.service.phase", ("evse.ac.active_power", "evse.ac.current", "evse.ac.voltage", "evse.limit.allocated_current_phase", "evse.limit.recommended_current_phase", "evse.limit.vehicle_minimum_current_phase", "evse.limit.vehicle_maximum_current_phase")),
                "evse.portal.read.session": ("evse.service.session", ("evse.energy.session", "evse.session.identifier", "evse.session.start", "evse.session.duration", "evse.energy.session_discharged", "evse.session.rfid_token", "evse.session.communication_standard", "evse.session.asymmetric_charging", "evse.demand.minimum_energy", "evse.demand.optimal_energy", "evse.demand.maximum_energy", "evse.demand.departure_time", "evse.summary.energy_grid", "evse.summary.energy_self_produced", "evse.summary.self_produced_ratio", "evse.summary.cost", "evse.summary.currency", "evse.summary.end")),
                "evse.portal.read.meter": ("evse.service.meter", ("evse.energy.lifetime", "evse.energy.lifetime_exported", "evse.accuracy.measured", "evse.accuracy.ratio_maximum", "evse.accuracy.measured_minimum_active_current", "evse.accuracy.measured_maximum_active_current", "evse.accuracy.range_minimum_active_current", "evse.accuracy.range_maximum_active_current", "evse.accuracy.measured_minimum_active_power", "evse.accuracy.measured_maximum_active_power", "evse.accuracy.range_minimum_active_power", "evse.accuracy.range_maximum_active_power")),
                "evse.portal.read.vehicle": ("evse.service.vehicle", ("evse.vehicle.state_of_charge", "evse.vehicle.battery_capacity", "evse.vehicle.state_of_health", "evse.vehicle.travel_range", "evse.vehicle.identifier", "evse.vehicle.minimum_power", "evse.vehicle.maximum_power", "evse.vehicle.standby_power", "evse.vehicle.sleep", "evse.vehicle.connection", "evse.vehicle.ac_power"))}
QUALIFIED = {
    'evse.target.days': ('evse.dimension.target_schedule',),
    'evse.target.time_of_day': ('evse.dimension.target', 'evse.dimension.target_schedule'),
    'evse.target.state_of_charge': ('evse.dimension.target', 'evse.dimension.target_schedule'),
    'evse.target.added_energy': ('evse.dimension.target', 'evse.dimension.target_schedule'),
    'evse.accuracy.measured': ('evse.dimension.measurement_type',),
    'evse.accuracy.ratio_maximum': ('evse.dimension.measurement_type',),
    'evse.accuracy.measured_minimum_active_current': ('evse.dimension.measurement_type',),
    'evse.accuracy.measured_maximum_active_current': ('evse.dimension.measurement_type',),
    'evse.accuracy.range_minimum_active_current': ('evse.dimension.measurement_type',),
    'evse.accuracy.range_maximum_active_current': ('evse.dimension.measurement_type',),
    'evse.accuracy.measured_minimum_active_power': ('evse.dimension.measurement_type',),
    'evse.accuracy.measured_maximum_active_power': ('evse.dimension.measurement_type',),
    'evse.accuracy.range_minimum_active_power': ('evse.dimension.measurement_type',),
    'evse.accuracy.range_maximum_active_power': ('evse.dimension.measurement_type',),
}
MEASUREMENT_SYMBOLS = ("active_current", "active_power", "apparent_current", "apparent_energy", "apparent_power", "electrical_energy", "frequency", "neutral_current", "power_factor", "reactive_current", "reactive_energy", "reactive_power", "rms_current", "rms_power", "rms_voltage", "unspecified", "voltage",)
QUALIFIER_DIMS = {
    "evse.dimension.target_schedule": ("quantity", "unit.one"),
    "evse.dimension.target": ("quantity", "unit.one"),
    "evse.dimension.measurement_type": ("symbol", None),
}
NEW_OPERATIONS = {
    'evse.operation.set_supply': ('evse.capability.set_supply', 'evse.status.supply', 'evse.effect.set_supply', ('evse.limit.allocated_current', 'evse.limit.charging_enabled_until', 'evse.limit.discharging_enabled_until', 'evse.limit.maximum_discharge_current', 'evse.limit.minimum_charge_current')),
    'evse.operation.set_allocated_current_with_expiry': ('evse.capability.set_allocated_current_with_expiry', 'evse.limit.allocated_current', 'evse.effect.set_allocated_current_with_expiry', ('evse.limit.allocated_current_expiry',)),
    'evse.operation.set_user_maximum_charge_current': ('evse.capability.set_user_maximum_charge_current', 'evse.limit.user_maximum_charge_current', 'evse.effect.set_user_maximum_charge_current', ()),
    'evse.operation.set_randomization_delay_window': ('evse.capability.set_randomization_delay_window', 'evse.configuration.randomization_delay_window', 'evse.effect.set_randomization_delay_window', ()),
    'evse.operation.set_vehicle_efficiency': ('evse.capability.set_vehicle_efficiency', 'evse.vehicle.approximate_efficiency', 'evse.effect.set_vehicle_efficiency', ()),
    'evse.operation.set_target': ('evse.capability.set_target', 'evse.target.time_of_day', 'evse.effect.set_target', ('evse.target.added_energy', 'evse.target.days', 'evse.target.state_of_charge')),
    'evse.operation.clear_targets': ('evse.capability.clear_targets', 'evse.target.schedule_count', 'evse.effect.clear_targets', ()),
    'evse.operation.set_evse_mode': ('evse.capability.set_evse_mode', 'evse.mode', 'evse.effect.set_evse_mode', ()),
    'evse.operation.set_allocated_current_phase': ('evse.capability.set_allocated_current_phase', 'evse.limit.allocated_current_phase', 'evse.effect.set_allocated_current_phase', ()),
    'evse.operation.set_recommended_current_phase': ('evse.capability.set_recommended_current_phase', 'evse.limit.recommended_current_phase', 'evse.effect.set_recommended_current_phase', ()),
    'evse.operation.set_failsafe_current': ('evse.capability.set_failsafe_current', 'evse.limit.failsafe_current', 'evse.effect.set_failsafe_current', ()),
}
NEW_EFFECTS = {
    'evse.effect.set_supply': ('evse.operation.set_supply', 'evse.status.supply'),
    'evse.effect.set_allocated_current_with_expiry': ('evse.operation.set_allocated_current_with_expiry', 'evse.limit.allocated_current'),
    'evse.effect.set_user_maximum_charge_current': ('evse.operation.set_user_maximum_charge_current', 'evse.limit.user_maximum_charge_current'),
    'evse.effect.set_randomization_delay_window': ('evse.operation.set_randomization_delay_window', 'evse.configuration.randomization_delay_window'),
    'evse.effect.set_vehicle_efficiency': ('evse.operation.set_vehicle_efficiency', 'evse.vehicle.approximate_efficiency'),
    'evse.effect.set_target': ('evse.operation.set_target', 'evse.target.time_of_day'),
    'evse.effect.clear_targets': ('evse.operation.clear_targets', 'evse.target.schedule_count'),
    'evse.effect.set_evse_mode': ('evse.operation.set_evse_mode', 'evse.mode'),
    'evse.effect.set_allocated_current_phase': ('evse.operation.set_allocated_current_phase', 'evse.limit.allocated_current_phase'),
    'evse.effect.set_recommended_current_phase': ('evse.operation.set_recommended_current_phase', 'evse.limit.recommended_current_phase'),
    'evse.effect.set_failsafe_current': ('evse.operation.set_failsafe_current', 'evse.limit.failsafe_current'),
}
EVENTS = {
    'evse.event.fault': {'service': 'evse.service.evse', 'trigger': 'evse.status.fault_cause', 'condition': 'changed', 'payload': (), 'origin': 'emitted'},
    'evse.event.rfid': {'service': 'evse.service.session', 'trigger': 'evse.session.rfid_token', 'condition': 'changed', 'payload': (), 'origin': 'emitted'},
}

MAPPINGS = {
    "evse.mapping.tesla.legacy_fbe0_fde0": {"id":"evse.mapping.tesla.legacy_fbe0_fde0","native_owner":"helianthus-docs-modbus","source_refs":["tesla_docs_modbus","tesla_modbusreg"],"state":"candidate","qualification":"offline_family_compatible_only","provenance":["legacy_fbe0","legacy_fde0"],"allocated_current":"native_candidate","actual_current":"native_candidate_separate","relative_or_unknown_state":"native_only_no_absolute_allocation","sender":"none","control_route":"none","live_authority":False,"loss":"unknown"},
    "evse.mapping.eebus": {"id":"evse.mapping.eebus","native_owner":"helianthus-docs-eebus","source_refs":["eebus_ledger","eebus_m625_donor"],"state":"unknown_pending_normative_source","qualification":"unresolved","loss":"unknown"},
    "evse.mapping.matter": {"id":"evse.mapping.matter","native_owner":"matter_draft","source_refs":["matter_draft"],"state":"candidate_design_input_only","qualification":"not_conformance","loss":"unknown"},
}


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_document(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source, object_pairs_hook=pairs)


def exact(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label} differs")


def refs(items, label, expected):
    if not isinstance(items, list) or not items:
        raise ValueError(f"{label} must be non-empty")
    ids, orders = [], []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"]):
            raise ValueError(f"{label} invalid ID")
        if item.get("ref") != {"pack": PACK, "id": item["id"], "version": "1.0.0"}:
            raise ValueError(f"{label} missing exact DefinitionRef owner/version")
        ids.append(item["id"])
        orders.append(item.get("order"))
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate definition ID in {label}")
    if not all(type(order) is int and order > 0 for order in orders) or orders != sorted(orders) or len(orders) != len(set(orders)):
        raise ValueError(f"{label} noncanonical order")
    exact(set(ids), set(expected), f"{label} catalog")
    return {item["id"]: item for item in items}


def decimal(value):
    if not isinstance(value, dict) or set(value) != {"coefficient", "exponent10"}:
        raise ValueError("bounds must use canonical kernel Decimal")
    coefficient, exponent = value["coefficient"], value["exponent10"]
    if not isinstance(coefficient, str) or not re.fullmatch(r"0|-?[1-9][0-9]*", coefficient) or type(exponent) is not int or not -18 <= exponent <= 18 or (coefficient == "0" and exponent != 0) or (coefficient != "0" and coefficient.endswith("0")):
        raise ValueError("bounds must use canonical kernel Decimal")
    return int(coefficient), exponent

def require_canonical_unit(unit):
    if unit not in CANONICAL_UNITS:
        raise ValueError("field unit is outside the canonical SI unit set")


def decimal_less(left, right):
    lc, le = decimal(left)
    rc, rexp = decimal(right)
    shared = min(le, rexp)
    return lc * 10 ** (le - shared) < rc * 10 ** (rexp - shared)


def check_qualifiers(identifier, field, base):
    qualifiers = QUALIFIED.get(identifier)
    if qualifiers is not None:
        if tuple(field.get("qualifiers", ())) != qualifiers:
            raise ValueError("field qualifiers")
        return base | {"qualifiers"}
    if "qualifiers" in field:
        raise ValueError("field qualifiers")
    return base


def validate_fields(fields):
    records = refs(fields, "fields", FIELD_CONTRACTS)
    for identifier, field in records.items():
        kind, unit, dimension, optional, symbols, bounds = FIELD_CONTRACTS[identifier]
        base = {"id", "ref", "kind", "dimension", "optional", "order"}
        if field.get("kind") != kind or field.get("dimension") != dimension or type(field.get("optional")) is not bool or field["optional"] != optional:
            raise ValueError("field has noncanonical kind, dimension, or optionality")
        base = check_qualifiers(identifier, field, base)
        if kind == "quantity":
            check_quantity(field, unit, bounds, base)
        elif kind in ("symbol", "symbols"):
            if set(field) != base | {"symbols"} or tuple(field.get("symbols", ())) != symbols or field.get("symbols") != sorted(field.get("symbols", [])) or any(not isinstance(value, str) or not ID.fullmatch(value) for value in field["symbols"]):
                raise ValueError("field has invalid canonical symbol contract")
        elif kind in ("boolean", "text", "time"):
            if set(field) != base:
                raise ValueError("field has invalid canonical text contract")
        else:
            raise ValueError("field has invalid canonical symbol contract")
    return records


def bound_side(coefficient, exponent):
    # An empty side stays null.
    if coefficient is None:
        return None
    return {"coefficient": coefficient, "exponent10": exponent}


def contract_bounds(bounds):
    if bounds is None:
        return None, None
    return bound_side(bounds[0], bounds[1]), bound_side(bounds[2], bounds[3])


def bounds_match(field, unit, minimum, maximum, base):
    if set(field) != base | {"unit", "bounds"} or field.get("unit") != unit:
        return False
    ordered = minimum is None or maximum is None or decimal_less(field.get("bounds", {}).get("minimum"), field.get("bounds", {}).get("maximum"))
    if not ordered:
        return False
    return field.get("bounds") == {"minimum": minimum, "maximum": maximum}


def check_quantity(field, unit, bounds, base):
    if unit is None:
        if "unit" in field or bounds is not None or set(field) != base | {"bounds"} or field.get("bounds") != {"minimum": None, "maximum": None}:
            raise ValueError("field has invalid canonical quantity contract")
        return
    require_canonical_unit(field.get("unit"))
    minimum, maximum = contract_bounds(bounds)
    if not bounds_match(field, unit, minimum, maximum, base):
        raise ValueError("field has invalid canonical quantity contract")


def check_qualifier_dimensions(definitions):
    items = refs(definitions.get("qualifier_dimensions"), "qualifier dimensions", QUALIFIER_DIMS)
    for ident, item in items.items():
        value_kind, unit = QUALIFIER_DIMS[ident]
        if value_kind == "symbol":
            if set(item) != {"id", "ref", "value_kind", "symbols", "order"} or item.get("value_kind") != "symbol" or tuple(item.get("symbols", ())) != MEASUREMENT_SYMBOLS:
                raise ValueError("qualifier dimension")
            continue
        if set(item) != {"id", "ref", "value_kind", "unit", "order"} or item.get("value_kind") != value_kind or item.get("unit") != unit:
            raise ValueError("qualifier dimension")


def check_new_operations(operations):
    for ident, item in operations.items():
        if ident == OP:
            continue
        capability, argument, effect, parameters = NEW_OPERATIONS[ident]
        expected = {"id", "ref", "capability", "arguments", "effect_rule", "order"}
        if parameters:
            expected.add("parameters")
        if set(item) != expected or item.get("capability") != capability or tuple(item.get("arguments", ())) != (argument,) or item.get("effect_rule") != effect or tuple(item.get("parameters", ())) != parameters:
            raise ValueError("operation association")


def check_new_effects(effects):
    for ident, item in effects.items():
        if ident == EFFECT:
            continue
        operation, fact = NEW_EFFECTS[ident]
        if set(item) != {"id", "ref", "operation", "fact", "operator", "order"} or item.get("operation") != operation or item.get("fact") != fact or item.get("operator") != "equal":
            raise ValueError("effect association")


def check_events(definitions):
    events = refs(definitions.get("events"), "events", EVENTS)
    for ident, item in events.items():
        spec = EVENTS[ident]
        if set(item) != {"id", "ref", "service", "trigger", "condition", "payload", "origin", "order"} or item.get("service") != spec["service"] or item.get("trigger") != spec["trigger"] or item.get("condition") != spec["condition"] or tuple(item.get("payload", ())) != tuple(spec["payload"]) or item.get("origin") != spec["origin"]:
            raise ValueError("event association")


def definition_groups(catalog):
    definitions = catalog.get("definitions", {})
    if not isinstance(definitions, dict) or set(definitions) != DEFINITION_GROUPS:
        raise ValueError("definition groups must be exactly " + ", ".join(sorted(DEFINITION_GROUPS)))
    return definitions


def validate_defs(catalog):
    definitions = definition_groups(catalog)
    fields = validate_fields(definitions.get("fields"))
    dimensions = refs(definitions.get("fact_dimensions"), "fact dimensions", DIMS)
    if any(item.get("value_kind") != "text" or set(item) != {"id", "ref", "value_kind", "order"} for item in dimensions.values()):
        raise ValueError("dimension association")
    services = refs(definitions.get("services"), "services", SERVICES)
    if any(item.get("fact_key_dimension") != SERVICES[key] or set(item) != {"id", "ref", "fact_key_dimension", "order"} for key, item in services.items()):
        raise ValueError("service association")
    relations = refs(definitions.get("relations"), "relations", RELATIONS)
    if any((item.get("from"), item.get("to"), item.get("cardinality")) != RELATIONS[key] or set(item) != {"id", "ref", "from", "to", "cardinality", "order"} for key, item in relations.items()):
        raise ValueError("relation association")
    capabilities = refs(definitions.get("capabilities"), "capabilities", CAPS)
    for key, item in capabilities.items():
        service, constraints = CAPS[key]
        expected = {"id", "ref", "service", "activation", "order"} | ({"constraints"} if constraints else set())
        if item.get("service") != service or tuple(item.get("constraints", ())) != constraints or item.get("activation") != "qualified_current_binding" or set(item) != expected:
            raise ValueError("capability association")
    operations = refs(definitions.get("operations"), "operations", {OP} | set(NEW_OPERATIONS))
    operation = operations[OP]
    if set(operation) != {"id", "ref", "capability", "arguments", "argument_constraints", "effect_rule", "preconditions", "stages", "terminal_outcomes", "readback", "retry", "order"} or (operation.get("capability"), tuple(operation.get("arguments", ())), tuple(operation.get("argument_constraints", ())), operation.get("effect_rule")) != ("evse.capability.set_allocated_current", ("evse.limit.allocated_current",), ("evse.limit.allocated_current",), EFFECT) or operation.get("preconditions") != PRECONDITIONS or operation.get("stages") != STAGES or operation.get("terminal_outcomes") != OUTCOMES or operation.get("readback") != "current_generation_exact_effect" or operation.get("retry") != "forbidden_after_indeterminate":
        raise ValueError("operation safety")
    check_new_operations(operations)
    effects = refs(definitions.get("effect_rules"), "effect rules", {EFFECT} | set(NEW_EFFECTS))
    effect = effects[EFFECT]
    if set(effect) != {"id", "ref", "operation", "fact", "operator", "order"} or (effect.get("operation"), effect.get("fact"), effect.get("operator")) != (OP, "evse.limit.allocated_current", "equal"):
        raise ValueError("effect association")
    check_new_effects(effects)
    check_qualifier_dimensions(definitions)
    check_events(definitions)
    portal = refs(definitions.get("portal_contributions"), "Portal contributions", set(PORTAL_READS) | {"evse.portal.operation.set_allocated_current"})
    coverage = set()
    for key, item in portal.items():
        if key in PORTAL_READS:
            service, facts = PORTAL_READS[key]
            if item.get("kind") != "read" or item.get("service") != service or tuple(item.get("fields", ())) != facts or set(item) != {"id", "ref", "kind", "service", "fields", "order"}:
                raise ValueError("Portal read association")
            coverage.update(facts)
        elif item.get("kind") != "operation" or item.get("operation") != OP or item.get("admission") != "current_only" or set(item) != {"id", "ref", "kind", "operation", "admission", "order"}:
            raise ValueError("Portal operation association")
    exact(coverage, set(fields), "Portal read field coverage")


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get("pack") != PACK or catalog.get("kernel_contract") != "helianthus.semantic.kernel/v1" or catalog.get("status") != "accepted":
        raise ValueError("catalog lacks exact PackRef")
    exact({item.get("id"): (item.get("pack"), item.get("state")) for item in catalog.get("domain_catalog", []) if isinstance(item, dict)}, DOMAINS, "five-domain catalog")
    exact({item.get("id"): item.get("revision") for item in catalog.get("inputs", []) if isinstance(item, dict)}, PINS, "pinned public inputs")
    if set(catalog.get("lifecycle_axes", [])) != LIFECYCLE:
        raise ValueError("lifecycle axes")
    exact(catalog.get("publication_withdrawal_policy"), POLICY, "publication/withdrawal policy")
    exact(catalog.get("counter_policy"), COUNTER, "counter policy")
    exact(catalog.get("availability_policy"), AVAILABILITY, "availability policy")
    if set(catalog.get("loss_dispositions", [])) != LOSS:
        raise ValueError("projection-loss coverage")
    rows = catalog.get("candidate_mappings")
    if not isinstance(rows, list) or len({row.get("id") for row in rows if isinstance(row, dict)}) != len(rows):
        raise ValueError("native mapping IDs")
    exact({row.get("id"): row for row in rows if isinstance(row, dict)}, MAPPINGS, "native mapping boundary")
    validate_defs(catalog)


def resolve(document, path):
    current = document
    for part in path.split(".")[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    final = path.split(".")[-1]
    return current, int(final) if isinstance(current, list) else final


def mutate(catalog, mutation):
    parent, key = resolve(catalog, mutation["path"])
    if mutation["op"] == "set":
        parent[key] = mutation.get("value")
    else:
        raise ValueError("unknown vector mutation")


def validate_document(document):
    if document.get("contract") != "helianthus.semantic.pack.evse.acceptance/v1" or document.get("pack_contract") != "helianthus.pack.evse/v1":
        raise ValueError("contract ID")
    validate_catalog(document.get("catalog"))
    vectors = document.get("vectors", [])
    if not any(vector.get("polarity") == "positive" for vector in vectors) or not any(vector.get("polarity") == "negative" for vector in vectors):
        raise ValueError("positive and negative vectors")
    for vector in vectors:
        candidate = copy.deepcopy(document["catalog"])
        for mutation in vector.get("input", {}).get("mutations", []):
            mutate(candidate, mutation)
        if vector.get("polarity") == "positive":
            validate_catalog(candidate)
        else:
            try:
                validate_catalog(candidate)
            except ValueError as error:
                if vector.get("expect", {}).get("error") not in str(error):
                    raise ValueError(f"{vector.get('id')}: {error}") from error
            else:
                raise ValueError(f"{vector.get('id')}: accepted")


def main():
    document = load_document(VECTORS)
    validate_document(document)
    text = DOCUMENT.read_text(encoding="utf-8")
    for collection in document["catalog"]["definitions"].values():
        for definition in collection:
            if definition["id"] not in text:
                raise ValueError(f"document misses {definition['id']}")
    print("EVSE pack v1: PASS")


if __name__ == "__main__":
    main()
