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
plane. Qualifier dimensions are on the energy plane. The subject dimension and the
service are on the energy, control and diagnostic planes. Operation capabilities,
operations and effect rules are on the control plane. `energy.capability.read.subject`
is on the energy and diagnostic planes. `energy.portal.read.subject` is an unsupported
presentation and has no plane. The read portal lists every admitted field of this pack
and no other identifier.

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

An empty bound stays empty. Stated bounds are only these:
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
empty; `energy.heartbeat.timeout` (unit.second) minimum empty, maximum 60. Every other
quantity bound is empty on both sides.

The six events below are admitted table rows and are not catalog entries. An entered or
left event must name symbols stored on its trigger fact, and a fact has no symbols
attribute. Capability activation in the vectors is `qualified_current_binding`, the
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

### Dimensions

`energy.dimension.subject`
`energy.dimension.slot`
`energy.dimension.series`
`energy.dimension.adjustment_range`
`energy.dimension.sequence`
`energy.dimension.balance`

### Service

`energy.service.subject`

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

### Portal

`energy.portal.read.subject`

### Events

`energy.event.power_adjust_start`
`energy.event.power_adjust_end`
`energy.event.paused`
`energy.event.resumed`
`energy.event.heartbeat_lost`
`energy.event.failsafe_entered`
