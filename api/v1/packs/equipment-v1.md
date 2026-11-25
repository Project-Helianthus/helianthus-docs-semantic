---
status: "accepted pack contract helianthus.pack.equipment 1.0.0"
---

# Equipment pack v1

`helianthus.pack.equipment` 1.0.0 publishes the admitted equipment subject.
`equipment.dimension.unit` is a class-level subject for any equipment or component. Its
anchor classes are `component` and `equipment`. `equipment.service.unit` uses those
subject classes. Its fact-key dimension is `equipment.dimension.unit`.

`equipment.dimension.resource` is a class-level subject for any equipment, component,
function or episode. Its anchor classes are `component`, `episode`, `equipment` and
`function`. `equipment.service.resource` uses those subject classes. Its fact-key
dimension is `equipment.dimension.resource`.

The admitted field table assigns no plane. Class-level dimensions and their services are
members of the energy, control and diagnostic planes. `equipment.dimension.message` is
on the diagnostic plane. Energy quantities and the wired-current type are on the energy
plane. Status, diagnosis, source state, presence, fault and message facts are on the
diagnostic plane. Identification, labels, designations, cell count and the clock are on
the provenance plane: identification is not an energy quantity, a setpoint or a
diagnostic status, and a class-level dimension does not carry the physical or provenance
plane. `equipment.capability.read.unit` is on the energy, diagnostic and provenance
planes. `equipment.capability.read.resource` is on the provenance plane.
`equipment.capability.set_label`, `equipment.operation.set_label` and
`equipment.effect.set_label` are on the control plane. Each changed event uses the
planes of its trigger. The two read portals are unsupported presentations and have no
plane.

`equipment.dimension.message` is the qualifier of `equipment.message.text`,
`equipment.message.kind` and `equipment.message.time`. The admitted table names its
value kind as quantity and names no unit. A quantity qualifier is admitted only as
`unit.one`, so this dimension uses `unit.one`.

`equipment.power.battery_capacity` stays `unit.ampere_hour`. No joule value is derived
from it. The table states no voltage for that derivation. Both bounds stay empty.

Stated bounds are these: `equipment.identification.software_version` (unit.one) minimum
0, maximum 4294967295; `equipment.identification.hardware_version` (unit.one) minimum 0,
maximum 65535; `equipment.power.source_order` (unit.one) minimum 0, maximum 255;
`equipment.power.battery_quantity` (unit.one) minimum 0, maximum 255.

Every other quantity bound is empty on both sides.
`equipment.power.battery_charge_ratio` is `unit.ratio` with both bounds empty. A maximum
of 200 on an integer representation is not an SI range.
`equipment.identification.manufacturing_date` stays text. A length of 8 to 16 is not a
catalog bound. `equipment.time.timezone` stays text. The reviewed spec element is an
offset duration, not a timezone name, and this pack invents no duration unit.

`equipment.identification.software_revision` is text and
`equipment.identification.software_version` is a quantity in `unit.one`.
`equipment.identification.hardware_revision` is text and
`equipment.identification.hardware_version` is a quantity in `unit.one`. The pairs are
distinct.

Symbol tokens are the admitted table tokens. For `equipment.power.wired_faults`,
`equipment.power.battery_faults` and `equipment.power.battery_charge_faults`, and for
`equipment.event.wired_fault_change`, `equipment.event.battery_fault_change` and
`equipment.event.battery_charge_fault_change`: source enum Unspecified converts to
`unspecified`; `unspecified` is a source enum member; an empty source list converts to
the symbol set `no_fault`; `no_fault` is not a source enum member; `no_fault` is absent
from a non-empty source list.

`equipment.identification.power_source_kind`: `unknown`, `mains_single_phase`,
`mains_three_phase`, `battery`, `dc`.

`equipment.diagnosis.operating_state`: `normal_operation`, `standby`, `failure`,
`service_needed`, `override_detected`, `in_alarm`, `not_reachable`, `finished`,
`temporarily_not_ready`, `off`.

`equipment.power.source_status`: `unspecified`, `active`, `standby`, `unavailable`.

`equipment.power.wired_current_type`: `ac`, `dc`.

`equipment.power.wired_faults`: `unspecified`, `over_voltage`, `under_voltage`,
`no_fault`.

`equipment.power.battery_charge_level`: `ok`, `warning`, `critical`.

`equipment.power.battery_replaceability`: `unspecified`, `not_replaceable`,
`user_replaceable`, `factory_replaceable`.

`equipment.power.battery_faults`: `unspecified`, `over_temperature`,
`under_temperature`, `no_fault`.

`equipment.power.battery_charge_state`: `unknown`, `charging`, `full`, `not_charging`.

`equipment.power.battery_charge_faults`: `unspecified`, `ambient_too_hot`,
`ambient_too_cold`, `battery_too_hot`, `battery_too_cold`, `battery_absent`,
`battery_over_voltage`, `battery_under_voltage`, `charger_over_voltage`,
`charger_under_voltage`, `safety_timeout`, `no_fault`.

`equipment.message.kind`: `logging`, `information`, `warning`, `alarm`, `emergency`,
`obsolete`.

`equipment.operation.set_label` writes `equipment.label.name`. Its parameter is
`equipment.label.description`. `equipment.effect.set_label` matches that argument on the
operation's resource dimension. The read portals list every admitted field of their
dimension. The history fields are not listed.

The five events are `changed` events, origin `emitted`, on `equipment.service.unit`.
Each payload is its trigger fact. A changed event stores no symbols.

Where the admitted table names a cluster element, the Matter 1.6.1 row stays `unknown`
with reason `matter.unmapped.v1`. The table does not state the factor, offset, rounding
and representation bounds, and this roster admits one transformed row,
`evse.ac.current`. `equipment.service.unit` and `equipment.service.resource` are
`unsupported` with reason `matter.service_not_requested_item.v1`. Dimensions, the effect
rule, events and the read portals have no roster row.

Capability activation in the vectors is `qualified_current_binding`. A verification
level of specification is recorded on these rows and blocks nothing. No element is
marked sensitive or hidden. Each entry is admitted on `matter_baseline` or `eebus` as
the admitted table records. Evidence is this page and the filed issue. No entry uses
`accepted_pack`. No pack version is raised: this pack is 1.0.0.

## Identifiers

`equipment.capability.read.resource`, `equipment.capability.read.unit`
`equipment.capability.set_label`, `equipment.diagnosis.last_error_code`
`equipment.diagnosis.operating_state`, `equipment.diagnosis.operating_time`
`equipment.diagnosis.vendor_state_code`, `equipment.dimension.message`
`equipment.dimension.resource`, `equipment.dimension.unit`, `equipment.effect.set_label`
`equipment.event.battery_charge_fault_change`, `equipment.event.battery_fault_change`
`equipment.event.message_queued`, `equipment.event.reachable_changed`
`equipment.event.wired_fault_change`, `equipment.identification.brand_name`
`equipment.identification.hardware_revision`
`equipment.identification.hardware_version`
`equipment.identification.manufacturing_date`, `equipment.identification.part_number`
`equipment.identification.power_source_kind`, `equipment.identification.product_code`
`equipment.identification.product_description`, `equipment.identification.product_label`
`equipment.identification.product_name`, `equipment.identification.product_url`
`equipment.identification.serial_number`, `equipment.identification.software_revision`
`equipment.identification.software_version`, `equipment.identification.vendor_code`
`equipment.identification.vendor_name`, `equipment.label.description`
`equipment.label.name`, `equipment.message.kind`, `equipment.message.text`
`equipment.message.time`, `equipment.operation.set_label`
`equipment.portal.read.resource`, `equipment.portal.read.unit`
`equipment.power.battery_ansi_designation`, `equipment.power.battery_capacity`
`equipment.power.battery_charge_faults`, `equipment.power.battery_charge_level`
`equipment.power.battery_charge_ratio`, `equipment.power.battery_charge_state`
`equipment.power.battery_charging_current`, `equipment.power.battery_chemistry`
`equipment.power.battery_common_designation`, `equipment.power.battery_faults`
`equipment.power.battery_functional_while_charging`
`equipment.power.battery_iec_designation`, `equipment.power.battery_present`
`equipment.power.battery_quantity`, `equipment.power.battery_replaceability`
`equipment.power.battery_replacement_description`
`equipment.power.battery_replacement_needed`, `equipment.power.battery_time_remaining`
`equipment.power.battery_time_to_full`, `equipment.power.battery_voltage`
`equipment.power.source_description`, `equipment.power.source_order`
`equipment.power.source_status`, `equipment.power.wired_current`
`equipment.power.wired_current_type`, `equipment.power.wired_faults`
`equipment.power.wired_input_frequency`, `equipment.power.wired_input_voltage`
`equipment.power.wired_maximum_current`, `equipment.power.wired_nominal_voltage`
`equipment.power.wired_present`, `equipment.service.resource`, `equipment.service.unit`
`equipment.status.reachable`, `equipment.time.current`, `equipment.time.timezone`

These identifiers are not catalog entries. The two history facts and
`equipment.dimension.history_index` are two-vendor-only and the second vendor is
unconfirmed, so they stay outside the accepted catalog, pack, metadata and target.
`equipment.diagnosis.link_state`, `equipment.diagnosis.degraded_reason` and
`equipment.diagnosis.controller_capability` have an empty admission and are not given an
arm. The remaining events have an empty trigger or condition. An event needs both. The
remaining operations have an empty capability, effect or argument. An operation needs a
capability, an argument and an effect. None of those rows is added.

## Not published

`equipment.diagnosis.error_history_code`, `equipment.diagnosis.error_history_time`
`equipment.dimension.history_index`, `equipment.diagnosis.link_state`
`equipment.diagnosis.degraded_reason`, `equipment.diagnosis.controller_capability`
`equipment.event.general_diagnostics_hardware_fault_change`
`equipment.event.general_diagnostics_radio_fault_change`
`equipment.event.general_diagnostics_network_fault_change`
`equipment.event.general_diagnostics_boot_reason`
`equipment.event.software_diagnostics_software_fault`
`equipment.event.time_synchronization_dst_table_empty`
`equipment.event.time_synchronization_dst_status`
`equipment.event.time_synchronization_time_zone_status`
`equipment.event.time_synchronization_time_failure`
`equipment.event.time_synchronization_missing_trusted_time_source`
`equipment.event.basic_information_start_up`
`equipment.event.basic_information_shut_down`, `equipment.event.basic_information_leave`
`equipment.event.bridged_device_basic_information_start_up`
`equipment.event.bridged_device_basic_information_shut_down`
`equipment.event.bridged_device_basic_information_leave`
`equipment.event.bridged_device_basic_information_active_changed`
`equipment.event.electrical_power_measurement_measurement_period_ranges`
`equipment.event.electrical_energy_measurement_cumulative_energy_measured`
`equipment.event.electrical_energy_measurement_periodic_energy_measured`
`equipment.event.messages_message_presented`
`equipment.event.messages_message_complete`
`equipment.event.pump_configuration_and_control_supply_voltage_low`
`equipment.event.pump_configuration_and_control_supply_voltage_high`
`equipment.event.pump_configuration_and_control_power_missing_phase`
`equipment.event.pump_configuration_and_control_system_pressure_low`
`equipment.event.pump_configuration_and_control_system_pressure_high`
`equipment.event.pump_configuration_and_control_dry_running`
`equipment.event.pump_configuration_and_control_motor_temperature_high`
`equipment.event.pump_configuration_and_control_pump_motor_fatal_failure`
`equipment.event.pump_configuration_and_control_electronic_temperature_high`
`equipment.event.pump_configuration_and_control_pump_blocked`
`equipment.event.pump_configuration_and_control_sensor_failure`
`equipment.event.pump_configuration_and_control_electronic_non_fatal_failure`
`equipment.event.pump_configuration_and_control_electronic_fatal_failure`
`equipment.event.pump_configuration_and_control_general_fault`
`equipment.event.pump_configuration_and_control_leakage`
`equipment.event.pump_configuration_and_control_air_detection`
`equipment.event.pump_configuration_and_control_turbine_operation`
`equipment.event.device_energy_management_power_adjust_start`
`equipment.event.device_energy_management_power_adjust_end`
`equipment.event.device_energy_management_paused`
`equipment.event.device_energy_management_resumed`
`equipment.operation.general_diagnostics_test_event_trigger`
`equipment.operation.general_diagnostics_time_snapshot`
`equipment.operation.general_diagnostics_payload_test_request`
`equipment.operation.software_diagnostics_reset_watermarks`
`equipment.operation.time_synchronization_set_utc_time`
`equipment.operation.time_synchronization_set_trusted_time_source`
`equipment.operation.time_synchronization_set_time_zone`
`equipment.operation.time_synchronization_set_dst_offset`
`equipment.operation.time_synchronization_set_default_ntp`
