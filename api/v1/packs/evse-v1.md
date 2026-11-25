# EVSE capability pack v1

`helianthus.pack.evse/v1` has exact PackRef `{id: "helianthus.pack.evse",
version: "1.0.0"}`. It is the accepted software-0.7 typed input over
`helianthus.semantic.kernel/v1`; its machine-significant catalog is
[evse-acceptance-vectors.json](evse-acceptance-vectors.json). Every indexed item
is an exact `DefinitionRef` owned by this PackRef.

## Fields and topology

The catalog declares electrical phase measurements, session and lifetime energy
counters, advertised/configured/allocated/actual current limits, and connection,
charging, readiness, fault, and interlock facts.
`evse.limit.allocated_current_phase` is in ampere on the phase dimension, with
the same bounds as `evse.limit.allocated_current`. The two facts stay
distinct: the connector allocation remains on the connector dimension, and
`evse.operation.set_allocated_current` continues to name that field only.
Quantities use canonical volt,
ampere, watt, hertz, and joule units under the
[unit rule](../../README.md#unit-rule): the session and lifetime energy
counters are in joule, and their bounds are the exact conversions of their
earlier customary bounds. A customary unit appears only at display, in a
consumer. Published Decimal bounds are pack validation bounds, never a claim
about a device's nameplate capability.

Fact keys distinguish asset, EVSE, connector, phase, session, meter, and vehicle. The
declared asset-to-EVSE, EVSE-to-connector, connector-to-phase,
connector-to-session, and EVSE-to-meter cardinalities preserve records without
inventing a connector, phase, meter, membership, or simultaneous-session claim.
Native records richer than these relations remain native evidence.

Unknown, unavailable, unsupported, stale, withdrawn, and conflicting states use
kernel quality, availability, and conflict records. They are never substituted
into EVSE symbols. The `relative_or_unknown` Tesla state remains native-only and
does not yield an absolute allocation.

The accepted catalog IDs are:

```text
evse.ac.voltage                    evse.ac.current
evse.ac.active_power               evse.ac.frequency
evse.energy.session                evse.energy.lifetime
evse.limit.advertised_current      evse.limit.configured_current
evse.limit.allocated_current       evse.limit.actual_current
evse.limit.allocated_current_phase
evse.status.connection             evse.status.charging
evse.status.readiness              evse.status.fault
evse.status.interlock
evse.dimension.asset               evse.dimension.evse
evse.dimension.connector           evse.dimension.phase
evse.dimension.session             evse.dimension.meter
evse.service.evse                  evse.service.connector
evse.service.phase                 evse.service.session
evse.service.meter
evse.relation.asset_evse           evse.relation.evse_connector
evse.relation.connector_phase      evse.relation.connector_session
evse.relation.evse_meter
evse.capability.read.evse          evse.capability.read.connector
evse.capability.read.phase         evse.capability.read.session
evse.capability.read.meter         evse.capability.set_allocated_current
evse.operation.set_allocated_current
evse.effect.set_allocated_current
evse.portal.read.evse              evse.portal.read.connector
evse.portal.read.phase             evse.portal.read.session
evse.portal.read.meter
evse.portal.operation.set_allocated_current
```


`resource.vehicle` is equipment on the physical, energy and diagnostic planes.
`evse.dimension.vehicle` uses that kind. `evse.service.vehicle` reads it through
`evse.capability.read.vehicle` and `evse.portal.read.vehicle`. Qualifier
dimensions `evse.dimension.target_schedule` and `evse.dimension.target` are
quantity indexes in `unit.one`. Each admitted operation has one capability and
one effect rule. `evse.operation.set_allocated_current` and its set case stay.
No release case is added. `evse.relation.connector_vehicle` is not added.

New quantities use `unit.ampere`, `unit.watt`, `unit.joule`, `unit.second`,
`unit.one`, `unit.ratio`, `unit.metre` or `unit.currency`. A new quantity bound
is empty. `evse.vehicle.approximate_efficiency` is a quantity with no unit:
ApproximateEvEfficiency is a uint16 with no unit name and no scale, so a
metres-per-joule qualification is withheld.

`evse.ac.total_active_power`, `evse.summary.cost` and `evse.vehicle.ac_power`
are signed in the admitted field table. This pack has no supplies relation, and
a signed catalog fact names one. Their catalog direction is `not_applicable`
until an EVSE supplies relation is admitted.

`evse.mode` is the uint8 mode identifier. `evse.mode_supported` keeps that
identifier and the ModeTag metadata as text. A ModeTag is not the mode value.
`evse.operation.set_evse_mode` writes the identifier.
`evse.operation.set_allocated_current_with_expiry` is the provisional limit
with expiry. It does not replace `evse.operation.set_allocated_current` and it
does not supply a minimum charge current. `evse.operation.set_supply` keeps
enable, disable and diagnostics. Pause below the minimum current is supply
disabled, never a 0 A write of the allocated current.

`evse.event.fault` and `evse.event.rfid` are emitted with an empty payload.
`evse.event.ev_connected`, `evse.event.ev_not_detected`,
`evse.event.energy_transfer_started` and `evse.event.energy_transfer_stopped`
are not catalog entries. An entered or left event must name symbols stored on
its trigger fact, and a fact has no symbols attribute. The specification level
on these rows blocks nothing.

Public citations are Matter 1.6.1 Energy EVSE, Energy EVSE Mode, Electrical
Power Measurement and Electrical Energy Measurement; EV Commissioning and
Configuration V1.0.1 scenarios EVCC-sc1, EVCC-sc2, EVCC-sc3, EVCC-sc4, EVCC-sc6,
EVCC-sc7 and EVCC-sc8; Overload Protection by EV Charging Current Curtailment
V1.0.1b scenarios OPEV-sc1 and OPEV-sc3; Optimization of Self-Consumption During
EV Charging V1.0.1b scenario OSCEV-sc1; EV Charging Electricity Measurement
V1.0.1 scenarios EVCEM-sc1 and EVCEM-sc2; EV Charging Summary V1.0.1 scenario
EVCS-sc1; Coordinated EV Charging V1.0.1 scenario CEVC-sc1; EV State of Charge
V1.0.0 RC1 scenarios EVSOC-sc1, EVSOC-sc2, EVSOC-sc3 and EVSOC-sc4; Monitoring
of Power Consumption V1.0.0 requirement MPC-011.

The additional catalog IDs are `evse.status.state`, `evse.status.supply`,
`evse.status.fault_cause`, `evse.limit.charging_enabled_until`,
`evse.limit.allocated_current_expiry`, `evse.limit.discharging_enabled_until`,
`evse.limit.minimum_charge_current`, `evse.limit.maximum_discharge_current`,
`evse.limit.user_maximum_charge_current`, `evse.limit.failsafe_current`,
`evse.limit.recommended_current_phase`, `evse.limit.vehicle_minimum_current_phase`,
`evse.limit.vehicle_maximum_current_phase`,
`evse.configuration.randomization_delay_window`, `evse.mode`,
`evse.mode_supported`, `evse.ac.total_active_power`, `evse.ac.connected_phases`,
`evse.energy.lifetime_exported`, `evse.session.identifier`, `evse.session.start`,
`evse.session.duration`, `evse.energy.session_discharged`,
`evse.session.rfid_token`, `evse.session.communication_standard`,
`evse.session.asymmetric_charging`, `evse.demand.minimum_energy`,
`evse.demand.optimal_energy`, `evse.demand.maximum_energy`,
`evse.demand.departure_time`, `evse.summary.energy_grid`,
`evse.summary.energy_self_produced`, `evse.summary.self_produced_ratio`,
`evse.summary.cost`, `evse.summary.currency`, `evse.summary.end`,
`evse.target.schedule_count`, `evse.target.days`, `evse.target.time_of_day`,
`evse.target.state_of_charge`, `evse.target.added_energy`,
`evse.target.next_start`, `evse.target.next_target_time`,
`evse.target.next_required_energy`, `evse.target.next_state_of_charge`,
`evse.vehicle.approximate_efficiency`, `evse.vehicle.state_of_charge`,
`evse.vehicle.battery_capacity`, `evse.vehicle.state_of_health`,
`evse.vehicle.travel_range`, `evse.vehicle.identifier`,
`evse.vehicle.minimum_power`, `evse.vehicle.maximum_power`,
`evse.vehicle.standby_power`, `evse.vehicle.sleep`, `evse.vehicle.connection`,
`evse.vehicle.ac_power`, `evse.dimension.vehicle`,
`evse.dimension.target_schedule`, `evse.dimension.target`,
`evse.service.vehicle`, `evse.capability.read.vehicle`,
`evse.capability.set_supply`, `evse.capability.set_allocated_current_with_expiry`,
`evse.capability.set_user_maximum_charge_current`,
`evse.capability.set_randomization_delay_window`,
`evse.capability.set_vehicle_efficiency`, `evse.capability.set_target`,
`evse.capability.clear_targets`, `evse.capability.set_evse_mode`,
`evse.capability.set_allocated_current_phase`,
`evse.capability.set_recommended_current_phase`,
`evse.capability.set_failsafe_current`, `evse.operation.set_supply`,
`evse.operation.set_allocated_current_with_expiry`,
`evse.operation.set_user_maximum_charge_current`,
`evse.operation.set_randomization_delay_window`,
`evse.operation.set_vehicle_efficiency`, `evse.operation.set_target`,
`evse.operation.clear_targets`, `evse.operation.set_evse_mode`,
`evse.operation.set_allocated_current_phase`,
`evse.operation.set_recommended_current_phase`,
`evse.operation.set_failsafe_current`, `evse.effect.set_supply`,
`evse.effect.set_allocated_current_with_expiry`,
`evse.effect.set_user_maximum_charge_current`,
`evse.effect.set_randomization_delay_window`,
`evse.effect.set_vehicle_efficiency`, `evse.effect.set_target`,
`evse.effect.clear_targets`, `evse.effect.set_evse_mode`,
`evse.effect.set_allocated_current_phase`,
`evse.effect.set_recommended_current_phase`, `evse.effect.set_failsafe_current`,
`evse.portal.read.vehicle`, `evse.event.fault` and `evse.event.rfid`.


## Capability and operation boundary

Read capabilities require a qualified current binding. `evse.operation.set_allocated_current`
keeps the generic set case; it requires the exact
`evse.limit.allocated_current` argument, current source epoch, driver
generation, semantic revision, qualified active capability, exact native route,
and authority admission. Dispatch, acknowledgement, readback, and terminal
outcome remain distinct. `applied` requires current-generation confirming
readback under the exact pack-owned effect rule; blind retry after an
indeterminate handoff is forbidden.

This is not an EVSE enable/disable, start/stop, reset, or native write recipe.
The Tesla candidate contributes no sender, control route, or live authority, so
it cannot admit this operation. Another exact qualified native owner may expose
the generic shape only when its own route and action-time authority contract
permit it.

## Lifecycle, counters, and projection loss

Source epoch, driver generation, semantic revision, qualification, activation,
generation fencing, partial updates, stale/unknown evidence, and permitted
last-known-good retention remain separate. Publication requires current source,
generation, revision, and qualified active capability. Partial publication
changes only supplied valid fields. Withdrawal is explicit and generation-fenced.
Stale or unknown evidence cannot promote, authorize, or operate.

Session/lifetime counter decrease does not prove reset or wrap. Native evidence
is required and the result is counter-continuity evidence or explicit loss.
Projection loss records native enums/bitfields, precision/range, connector,
phase, session, and meter topology, direction/reference, counter continuity,
unavailable fields, conflicts, vendor extensions, and unsupported operations.

## Portal contribution descriptors

Read descriptors consume promoted EVSE, connector, phase, session, and meter
facts. The operation descriptor exposes only a currently admitted operation
affordance. Portal consumes promoted definitions and admission; it cannot define
semantic truth, native routes, authority, lifecycle, or an unavailable Tesla
sender.

## Native mapping boundary

Inputs are semantic documentation `f81f04b026ccfc0bb4107c5a361e7bee146a166a`,
semreg `cc9b324225e945598128eeabe977e7fa0af6dc93`, Tesla Modbus documentation
`d16ff91ff808803fa31c67a6a10eb2a4faa70937`, Tesla registry
`75e4e3988a7682068c02d8ac24f737b7f24a029f`, eeBUS ledger
`81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1`, M6.25 donor
`cedf238e34f879815ba773e9cd76b2b31c2822a3`, and Matter draft
`29b4768a513cf566011ab8cd60df1bc495204953`.

The Tesla FBE0/FDE0 row is an offline `family_compatible` native candidate.
It retains allocated and actual current separately, preserves the state byte,
and maps relative/unknown state to no absolute semantic allocation. It has no
sender, control route, or live authority. eeBUS remains
`unknown_pending_normative_source`; Matter is a design input, not conformance. No mapping
in this pack is normative or an operation authority.

## Compatibility and validation

The five-domain catalog has thermal/HVAC, PV/inverter, storage/BMS, and EVSE
accepted; infrastructure remains the required follow-on. This is typed 0.7
documentation only. It creates no semreg runtime, native driver, gateway,
Portal UI, Home Assistant entity, deployment, hardware qualification, live
action, 0.8 IR, or code generation. The version rule of
[api/README.md](../../README.md#version-rule) applies, including its rule for
in-place changes until the 0.7 release.

Run `python3 scripts/validate_evse_pack_v1.py`,
`python3 scripts/test_validate_evse_pack_v1.py`, and `./scripts/check_docs.sh`.
