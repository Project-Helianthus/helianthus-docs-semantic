---
status: "accepted pack contract helianthus.pack.energy_management 1.0.0"
---

# Energy management pack v1

`helianthus.pack.energy_management` 1.0.0 publishes the admitted energy-management
subject. `energy.dimension.subject` is a class-level subject for any equipment,
component or function that is controlled, metered or priced. Its anchor classes are
`component`, `equipment` and `function`. `energy.service.subject` uses those subject
classes. Its fact-key dimension is `energy.dimension.subject`.

Facts are on the energy plane, except `energy.heartbeat.status`,
`energy.heartbeat.timeout` and `energy.manager.state`, which are on the diagnostic
plane. Qualifier dimensions are on the energy plane. The subject dimension and
`energy.service.subject` are on the energy, control and diagnostic planes.
Operation capabilities,
operations and effect rules are on the control plane. `energy.capability.read.subject`
is on the energy and diagnostic planes. `energy.portal.read.subject` is an unsupported
presentation and has no plane. It lists every admitted field whose dimension is
`energy.dimension.subject`. `energy.portal.read.tariff` is an unsupported
presentation and has no plane. It lists the fields of `energy.service.tariff`
and no other identifier.

`resource.tariff` is a function on the energy and control planes.
`energy.dimension.tariff` names that kind and uses the same planes.
`energy.service.tariff` uses that kind. Its fact-key dimension is
`energy.dimension.tariff`. Tariff facts are on the energy plane.
`energy.capability.read.tariff` is on the energy plane. Qualifier dimensions, including
`energy.dimension.direct_control_timestamp` and `energy.dimension.job`, are on the
energy plane. The reviewed table records `energy.dimension.job` in no plane. This pack
has no member with an empty plane, so the dimension is a member on the energy plane.
Direct-control and task-management facts are fields of `energy.dimension.subject`.
Operation capabilities, operations and effect rules stay on the control plane.

A price the admitted table records as `unit.currency_per_joule` stays
`unit.currency_per_joule`. The registry does not rewrite it as another unit.
A consumer shows that price per kWh. The registry value stays per joule.

`energy.task.remote_controllable`: absent means true. A false value declines writes on
the features linked through the job relation list. That absence rule is not a catalog
default.

A limit has a power value, an active flag and a duration. Failsafe power and the minimum
failsafe duration apply when the heartbeat is lost. After a restart the controllable
system starts in init with the failsafe limit. The restart fallback is not the previous
active limit.

A series is slot facts keyed by `energy.dimension.series` and `energy.dimension.slot`. A
power sequence is the flexibility offer, keyed by `energy.dimension.sequence`. A power
limit is `unit.watt`, never a current.

`energy.esa.mode` is the uint8 mode identifier in `unit.one`, not a ModeTag.
`energy.esa.mode_supported` keeps the identifier and the ModeTag metadata as text. Tags
are not the mode value. `energy.operation.set_esa_mode` writes that identifier.
`energy.series.slot_power_maximum` writes a limit curve.
`energy.series.slot_power_nominal` writes forecast power.
`energy.operation.modify_series_slot` has no start timestamp and derives neither input
from the other. `energy.operation.set_esa_state`: paused pauses and online resumes.

These quantities are signed in the admitted field table. This pack admits no supplies
relation, and a signed catalog fact names one. Their catalog direction and vector
direction are `not_applicable`: `energy.esa.minimum_power`, `energy.esa.maximum_power`,
`energy.esa.adjustment_minimum_power`, `energy.esa.adjustment_maximum_power`,
`energy.esa.requested_power`, `energy.series.slot_power_nominal`,
`energy.series.slot_power_minimum`, `energy.series.slot_power_maximum`,
`energy.series.slot_energy_nominal`, `energy.series.slot_adjustment_minimum_power`,
`energy.series.slot_adjustment_maximum_power`.

These further quantities are signed in the admitted field table. This pack admits no
supplies relation, and a signed catalog fact names one. Their catalog direction and
vector direction are `not_applicable`: `energy.tariff.randomization_offset`,
`energy.price.current`, `energy.price.forecast_price`,
`energy.incentive.incentive_value`, `energy.tariff.day_entry_randomization_offset`,
`energy.tariff.component_price`.

An empty bound stays empty. Stated bounds are these:
`energy.limit.consumption_active_power` (unit.watt) minimum 0, maximum empty;
`energy.limit.consumption_failsafe_power` (unit.watt) minimum 0, maximum empty;
`energy.limit.consumption_failsafe_duration_minimum` (unit.second) minimum 7200, maximum
86400; `energy.nameplate.consumption_nominal_maximum` (unit.watt) minimum 0, maximum
empty; `energy.nameplate.consumption_contractual_maximum` (unit.watt) minimum 0, maximum
empty; `energy.limit.production_active_power` (unit.watt) minimum 0, maximum empty;
`energy.limit.production_failsafe_power` (unit.watt) minimum 0, maximum empty;
`energy.limit.production_failsafe_duration_minimum` (unit.second) minimum 7200, maximum
86400; `energy.nameplate.production_nominal_maximum` (unit.watt) minimum 0, maximum
empty; `energy.nameplate.production_contractual_maximum` (unit.watt) minimum 0, maximum
empty; `energy.heartbeat.timeout` (unit.second) minimum empty, maximum 60.

Further stated bounds are `energy.price.current_level` (unit.one) minimum -32768,
maximum 32767; `energy.price.forecast_level` (unit.one) minimum -32768, maximum 32767;
`energy.incentive.renewable_ratio` (unit.ratio) minimum 0, maximum 1;
`energy.incentive.maximum_tiers` (unit.one) minimum 3, maximum empty.

These quantities name no unit, and the registry does not invent one:
`energy.tariff.component_threshold`, `energy.grid.carbon_intensity`,
`energy.grid.local_carbon_intensity`.

These quantities have an empty direction in the admitted table. Their catalog direction
and vector direction are `not_applicable`: `energy.grid.carbon_intensity`,
`energy.grid.local_carbon_intensity`, `energy.direct_control.power`,
`energy.direct_control.energy`, `energy.task.elapsed_time`,
`energy.task.remaining_time`.

Every other
quantity bound is empty on both sides.

The six events below are admitted table rows and are not catalog entries. An entered or
left event must name symbols stored on its trigger fact, and a fact has no symbols
attribute.

`energy.event.price_changed` and `energy.event.grid_conditions_changed` are `changed`
events. A changed event stores no symbols, so both are catalog entries.

Capability activation in the vectors is `qualified_current_binding`, the
token used by the other packs. A verification level of specification is recorded on
these rows and blocks nothing. No element is marked sensitive or hidden. Each entry is
admitted on `matter_baseline` or `eebus` as the admitted table records. Evidence is this
page and the filed issue. No entry uses `accepted_pack`. No pack version is raised: this
pack is 1.0.0.

## Parameter order

`energy.operation.adjust_power` stores parameters `energy.esa.request_cause`,
`energy.esa.requested_duration`. The reviewed table lists
`energy.esa.requested_duration`, `energy.esa.request_cause`.

`energy.operation.set_esa_state` stores parameters `energy.esa.request_cause`,
`energy.esa.requested_duration`. The reviewed table lists
`energy.esa.requested_duration`, `energy.esa.request_cause`.

`energy.operation.modify_series_slot` stores parameters `energy.esa.request_cause`,
`energy.series.identifier`, `energy.series.slot_duration`,
`energy.series.slot_power_maximum`. The reviewed table lists
`energy.series.slot_duration`, `energy.series.identifier`, `energy.esa.request_cause`,
`energy.series.slot_power_maximum`.

`energy.operation.write_incentive_slot` stores parameters
`energy.incentive.boundary_lower`, `energy.incentive.boundary_upper`,
`energy.incentive.incentive_kind`, `energy.incentive.slot_end`,
`energy.incentive.slot_start`, `energy.incentive.tier_kind`. The reviewed table lists
`energy.incentive.slot_start`, `energy.incentive.slot_end`,
`energy.incentive.boundary_lower`, `energy.incentive.boundary_upper`,
`energy.incentive.tier_kind`, `energy.incentive.incentive_kind`.

## Operation notes

`energy.operation.set_consumption_limit`: RR05 converts a charging-station consumption
limit from watt to ampere in eebusreg; the gateway does not convert it; measured voltage
when SemReg has one, else the specification nominal voltage marked declared

`energy.operation.set_esa_state`: paused pauses, online resumes

`energy.operation.modify_series_slot`: writes limit curves and forecast changes;
slot_power_maximum writes a limit curve and is a separate input from slot_power_nominal

`energy.operation.set_esa_mode`: ChangeToMode.NewMode writes the uint8 mode identifier
carried by energy.esa.mode, not a ModeTag

`energy.operation.set_sequence_state`: pause, resume, stop

`energy.operation.write_incentive_slot`: energy manager writes the incentive table to
the device

`energy.operation.set_direct_control_activity_state`: Table 50 transitions among
running, paused and inactive; sequenceId rule; isActivityStateChangeable

`energy.operation.set_direct_control_energy_mode`: isEnergyModeChangeable; timestamp
duration zero for a current-value adjustment

`energy.operation.set_direct_control_power`: isPowerChangeable; timestamp duration zero
for a current-value adjustment

`energy.operation.set_direct_control_energy`: isEnergyChangeable; timestamp duration
zero for a current-value adjustment

## Events

`energy.event.power_adjust_start` is `entered` on `energy.esa.state` for symbol
`power_adjust_active`, origin `emitted`.

`energy.event.power_adjust_end` is `left` on `energy.esa.state` for symbol
`power_adjust_active`, payload `energy.esa.adjustment_end_cause`, origin `emitted`.

`energy.event.paused` is `entered` on `energy.esa.state` for symbol `paused`, origin
`emitted`.

`energy.event.resumed` is `left` on `energy.esa.state` for symbol `paused`, payload
`energy.esa.adjustment_end_cause`, origin `emitted`.

`energy.event.heartbeat_lost` is `entered` on `energy.heartbeat.status` for symbol
`timeout`, origin `derived`.

`energy.event.failsafe_entered` is `entered` on `energy.limit.state` for symbol
`failsafe`, origin `derived`.

## Admitted identifiers

### Fields

`energy.limit.consumption_active_power`
`energy.limit.consumption_active`
`energy.limit.consumption_duration`
`energy.limit.consumption_failsafe_power`
`energy.limit.consumption_failsafe_duration_minimum`
`energy.nameplate.consumption_nominal_maximum`
`energy.nameplate.consumption_contractual_maximum`
`energy.limit.production_active_power`
`energy.limit.production_active`
`energy.limit.production_duration`
`energy.limit.production_failsafe_power`
`energy.limit.production_failsafe_duration_minimum`
`energy.nameplate.production_nominal_maximum`
`energy.nameplate.production_contractual_maximum`
`energy.limit.state`
`energy.heartbeat.status`
`energy.heartbeat.timeout`
`energy.manager.state`
`energy.esa.type`
`energy.esa.can_generate`
`energy.esa.state`
`energy.esa.minimum_power`
`energy.esa.maximum_power`
`energy.esa.adjustment_minimum_power`
`energy.esa.adjustment_maximum_power`
`energy.esa.adjustment_minimum_duration`
`energy.esa.adjustment_maximum_duration`
`energy.esa.adjustment_cause`
`energy.esa.opt_out`
`energy.esa.mode`
`energy.esa.mode_supported`
`energy.esa.requested_power`
`energy.esa.requested_duration`
`energy.esa.request_cause`
`energy.esa.adjustment_end_cause`
`energy.series.identifier`
`energy.series.start`
`energy.series.end`
`energy.series.earliest_start`
`energy.series.latest_end`
`energy.series.update_reason`
`energy.series.pausable`
`energy.series.slot_start`
`energy.series.slot_duration`
`energy.series.slot_minimum_duration`
`energy.series.slot_maximum_duration`
`energy.series.slot_default_duration`
`energy.series.slot_elapsed`
`energy.series.slot_remaining`
`energy.series.slot_power_nominal`
`energy.series.slot_power_minimum`
`energy.series.slot_power_maximum`
`energy.series.slot_energy_nominal`
`energy.series.slot_pausable`
`energy.series.slot_minimum_pause`
`energy.series.slot_maximum_pause`
`energy.series.slot_adjustment_minimum_power`
`energy.series.slot_adjustment_maximum_power`
`energy.series.slot_adjustment_minimum_duration`
`energy.series.slot_adjustment_maximum_duration`
`energy.series.slot_state`
`energy.series.constraint_minimum_slot_duration`
`energy.series.constraint_maximum_slots`
`energy.series.constraint_slot_value_step`
`energy.sequence.state`
`energy.sequence.earliest_start`
`energy.sequence.latest_end`
`energy.sequence.scheduled_start`
`energy.sequence.pausable`
`energy.sequence.stoppable`
`energy.sequence.active_duration_minimum`
`energy.sequence.active_duration_maximum`
`energy.sequence.pause_duration_minimum`
`energy.sequence.pause_duration_maximum`
`energy.sequence.slot_duration`
`energy.sequence.slot_power_expected`
`energy.sequence.slot_power_minimum`
`energy.sequence.slot_power_maximum`
`energy.preference.balance_step`
`energy.preference.balance_label`
`energy.preference.current_balance`
`energy.preference.priorities`
`energy.preference.low_power_sensitivity`

`energy.tariff.label`
`energy.tariff.provider`
`energy.tariff.currency`
`energy.tariff.unit_basis`
`energy.tariff.block_mode`
`energy.tariff.start`
`energy.tariff.direction`
`energy.tariff.status`
`energy.tariff.price_kind`
`energy.tariff.randomization_offset`
`energy.tariff.randomization_kind`
`energy.price.current`
`energy.price.current_level`
`energy.price.current_start`
`energy.price.current_end`
`energy.price.current_description`
`energy.price.forecast_start`
`energy.price.forecast_end`
`energy.price.forecast_price`
`energy.price.forecast_level`
`energy.incentive.slot_start`
`energy.incentive.slot_end`
`energy.incentive.tier_kind`
`energy.incentive.boundary_lower`
`energy.incentive.boundary_upper`
`energy.incentive.incentive_value`
`energy.incentive.incentive_kind`
`energy.incentive.renewable_ratio`
`energy.incentive.co2_intensity`
`energy.incentive.maximum_tiers`
`energy.incentive.maximum_slots`
`energy.negotiation.simulation_cycles_maximum`
`energy.negotiation.simulation_concurrent`
`energy.negotiation.request_timeout`
`energy.negotiation.writeable_wait`
`energy.tariff.day_entry_start`
`energy.tariff.day_entry_duration`
`energy.tariff.day_entry_randomization_offset`
`energy.tariff.day_pattern_days`
`energy.tariff.day_pattern_entry`
`energy.tariff.calendar_period_start`
`energy.tariff.calendar_period_pattern`
`energy.tariff.individual_day_date`
`energy.tariff.individual_day_kind`
`energy.tariff.individual_day_entry`
`energy.tariff.component_price`
`energy.tariff.component_price_kind`
`energy.tariff.component_friendly_credit`
`energy.tariff.component_auxiliary_load`
`energy.tariff.component_peak_period`
`energy.tariff.component_power_threshold`
`energy.tariff.component_apparent_power_threshold`
`energy.tariff.component_threshold`
`energy.tariff.component_label`
`energy.tariff.component_predicted`
`energy.tariff.period_label`
`energy.tariff.period_entry`
`energy.tariff.period_component`
`energy.tariff.current_day_entry`
`energy.tariff.current_day_entry_date`
`energy.tariff.next_day_entry`
`energy.tariff.next_day_entry_date`
`energy.tariff.current_day`
`energy.tariff.next_day`
`energy.tariff.current_components`
`energy.tariff.next_components`
`energy.metering.quantity`
`energy.metering.timestamp`
`energy.metering.maximum_quantities`
`energy.grid.local_generation_available`
`energy.grid.start`
`energy.grid.end`
`energy.grid.carbon_intensity`
`energy.grid.carbon_level`
`energy.grid.local_carbon_intensity`
`energy.grid.local_carbon_level`
`energy.direct_control.timestamp`
`energy.direct_control.activity_state`
`energy.direct_control.is_activity_state_changeable`
`energy.direct_control.energy_mode`
`energy.direct_control.is_energy_mode_changeable`
`energy.direct_control.power`
`energy.direct_control.is_power_changeable`
`energy.direct_control.energy`
`energy.direct_control.is_energy_changeable`
`energy.direct_control.sequence_id`
`energy.direct_control.positive_energy_direction`
`energy.direct_control.power_unit`
`energy.direct_control.energy_unit`
`energy.task.job_id`
`energy.task.timestamp`
`energy.task.job_state`
`energy.task.elapsed_time`
`energy.task.remaining_time`
`energy.task.direct_control_related`
`energy.task.hvac_related`
`energy.task.hvac_related_overrun_id`
`energy.task.load_control_releated`
`energy.task.load_control_releated_event_id`
`energy.task.power_sequences_related`
`energy.task.power_sequences_related_sequence_id`
`energy.task.smart_energy_management_ps_related`
`energy.task.smart_energy_management_ps_related_sequence_id`
`energy.task.job_source`
`energy.task.label`
`energy.task.description`
`energy.task.remote_controllable`
`energy.task.jobs_active`
`energy.lpc.use_case_name`
`energy.lpp.use_case_name`
`energy.poen.use_case_name`
`energy.podf.use_case_name`
`energy.tout.use_case_name`
`energy.itpcm.use_case_name`
`energy.ohpcf.use_case_name`
`energy.lpc.actor`
`energy.lpp.actor`
`energy.poen.actor`
`energy.podf.actor`
`energy.tout.actor`
`energy.itpcm.actor`
`energy.ohpcf.actor`
`energy.lpc.use_case_version`
`energy.lpp.use_case_version`
`energy.poen.use_case_version`
`energy.podf.use_case_version`
`energy.tout.use_case_version`
`energy.itpcm.use_case_version`
`energy.ohpcf.use_case_version`
`energy.lpc.heartbeat_timestamp`
`energy.lpp.heartbeat_timestamp`
`energy.lpc.heartbeat_counter`
`energy.lpp.heartbeat_counter`
`energy.itpcm.itpcm_031`
`energy.lpc.value_range_min`
`energy.lpp.value_range_min`
`energy.poen.value_range_min`
`energy.podf.value_range_min`
`energy.tout.value_range_min`
`energy.itpcm.value_range_min`
`energy.ohpcf.value_range_min`
`energy.lpc.per`
`energy.lpp.per`
`energy.poen.per`
`energy.podf.per`
`energy.tout.per`
`energy.itpcm.per`
`energy.ohpcf.per`
`energy.lpc.slots`
`energy.lpp.slots`
`energy.poen.slots`
`energy.podf.slots`
`energy.tout.slots`
`energy.itpcm.slots`
`energy.ohpcf.slots`
`energy.itpcm.simple_committed_incentive_table`
`energy.lpc.committed_power_plan`
`energy.lpp.committed_power_plan`
`energy.poen.committed_power_plan`
`energy.podf.committed_power_plan`
`energy.tout.committed_power_plan`
`energy.itpcm.committed_power_plan`
`energy.ohpcf.committed_power_plan`
`energy.ohpcf.flexibility`
`energy.ohpcf.alternatives`
`energy.ohpcf.is_pausable`
`energy.ohpcf.is_stoppable`
`energy.ohpcf.alternatives_count`
`energy.ohpcf.total_sequences_count_max`
`energy.ohpcf.supports_reselection`
`energy.ohpcf.sequence_id`
`energy.ohpcf.earliest_start_time`
`energy.ohpcf.latest_end_time`
`energy.ohpcf.default_duration`
`energy.ohpcf.active_duration_min`
`energy.ohpcf.pause_duration_min`
`energy.ohpcf.elapsed_slot_time`
`energy.ohpcf.remaining_slot_time`

### Resource kind

`resource.tariff`

### Dimensions

`energy.dimension.subject`
`energy.dimension.slot`
`energy.dimension.series`
`energy.dimension.adjustment_range`
`energy.dimension.sequence`
`energy.dimension.balance`

`energy.dimension.tariff`
`energy.dimension.tier`
`energy.dimension.boundary`
`energy.dimension.incentive`
`energy.dimension.component`
`energy.dimension.day_entry`
`energy.dimension.day_pattern`
`energy.dimension.calendar_period`
`energy.dimension.tariff_period`
`energy.dimension.individual_day`
`energy.dimension.forecast_slot`
`energy.dimension.direct_control_timestamp`
`energy.dimension.job`

### Service

`energy.service.subject`

`energy.service.tariff`

### Capabilities

`energy.capability.read.subject`
`energy.capability.set_consumption_limit`
`energy.capability.set_production_limit`
`energy.capability.set_consumption_failsafe`
`energy.capability.set_production_failsafe`
`energy.capability.adjust_power`
`energy.capability.set_esa_state`
`energy.capability.adjust_start_time`
`energy.capability.modify_series_slot`
`energy.capability.set_esa_mode`
`energy.capability.schedule_sequence`
`energy.capability.set_sequence_state`
`energy.capability.set_energy_balance`
`energy.capability.set_low_power_sensitivity`

`energy.capability.read.tariff`
`energy.capability.write_incentive_slot`
`energy.capability.set_local_generation_available`
`energy.capability.set_direct_control_activity_state`
`energy.capability.set_direct_control_energy_mode`
`energy.capability.set_direct_control_power`
`energy.capability.set_direct_control_energy`

### Operations

`energy.operation.set_consumption_limit`
`energy.operation.set_production_limit`
`energy.operation.set_consumption_failsafe`
`energy.operation.set_production_failsafe`
`energy.operation.adjust_power`
`energy.operation.set_esa_state`
`energy.operation.adjust_start_time`
`energy.operation.modify_series_slot`
`energy.operation.set_esa_mode`
`energy.operation.schedule_sequence`
`energy.operation.set_sequence_state`
`energy.operation.set_energy_balance`
`energy.operation.set_low_power_sensitivity`

`energy.operation.write_incentive_slot`
`energy.operation.set_local_generation_available`
`energy.operation.set_direct_control_activity_state`
`energy.operation.set_direct_control_energy_mode`
`energy.operation.set_direct_control_power`
`energy.operation.set_direct_control_energy`

### Effect rules

`energy.effect.set_consumption_limit`
`energy.effect.set_production_limit`
`energy.effect.set_consumption_failsafe`
`energy.effect.set_production_failsafe`
`energy.effect.adjust_power`
`energy.effect.set_esa_state`
`energy.effect.adjust_start_time`
`energy.effect.modify_series_slot`
`energy.effect.set_esa_mode`
`energy.effect.schedule_sequence`
`energy.effect.set_sequence_state`
`energy.effect.set_energy_balance`
`energy.effect.set_low_power_sensitivity`

`energy.effect.write_incentive_slot`
`energy.effect.set_local_generation_available`
`energy.effect.set_direct_control_activity_state`
`energy.effect.set_direct_control_energy_mode`
`energy.effect.set_direct_control_power`
`energy.effect.set_direct_control_energy`

### Portal

`energy.portal.read.subject`

`energy.portal.read.tariff`

### Events

`energy.event.power_adjust_start`
`energy.event.power_adjust_end`
`energy.event.paused`
`energy.event.resumed`
`energy.event.heartbeat_lost`
`energy.event.failsafe_entered`
`energy.event.price_changed`
`energy.event.grid_conditions_changed`
