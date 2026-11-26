# Electrical infrastructure capability pack v1

`helianthus.pack.infrastructure/v1` has exact PackRef `{id:
"helianthus.pack.infrastructure", version: "1.0.0"}`. It is the accepted
software-0.7 typed input over `helianthus.semantic.kernel/v1`; its
machine-significant catalog is
[infrastructure-acceptance-vectors.json](infrastructure-acceptance-vectors.json).
Every indexed item is an exact `DefinitionRef` owned by this PackRef.

The accepted catalog IDs are:

```text
infrastructure.ac.voltage                 infrastructure.ac.voltage_line_line
infrastructure.ac.current                 infrastructure.ac.active_power
infrastructure.ac.reactive_power          infrastructure.ac.apparent_power
infrastructure.ac.frequency               infrastructure.ac.power_factor
infrastructure.power.import_active        infrastructure.power.export_active
infrastructure.power.import_reactive      infrastructure.power.export_reactive
infrastructure.power.apparent             infrastructure.power.pcc
infrastructure.energy.import              infrastructure.energy.export
infrastructure.energy.self_consumption    infrastructure.limit.fallback_power
infrastructure.accuracy.measured          infrastructure.accuracy.ratio_maximum
infrastructure.status.connection          infrastructure.status.readiness
infrastructure.status.breaker             infrastructure.status.fault
infrastructure.status.interlock
infrastructure.dimension.site
infrastructure.dimension.grid_connection  infrastructure.dimension.feeder
infrastructure.dimension.circuit          infrastructure.dimension.phase
infrastructure.dimension.meter            infrastructure.dimension.line_pair
infrastructure.dimension.measurement_type
infrastructure.service.site               infrastructure.service.line_pair
infrastructure.service.grid_connection    infrastructure.service.feeder
infrastructure.service.circuit            infrastructure.service.phase
infrastructure.service.meter
infrastructure.relation.site_grid_connection
infrastructure.relation.grid_connection_feeder
infrastructure.relation.feeder_circuit
infrastructure.relation.circuit_phase
infrastructure.relation.grid_connection_meter
infrastructure.relation.site_load
infrastructure.relation.load_meter
infrastructure.capability.read.site
infrastructure.capability.read.grid_connection
infrastructure.capability.read.feeder
infrastructure.capability.read.circuit
infrastructure.capability.read.phase
infrastructure.capability.read.meter
infrastructure.portal.read.site           infrastructure.portal.read.grid_connection
infrastructure.portal.read.feeder         infrastructure.portal.read.circuit
infrastructure.portal.read.phase          infrastructure.portal.read.meter
infrastructure.portal.read.line_pair
```

## Electrical topology and fields

Infrastructure means electrical site, grid-connection, feeder, circuit, phase,
line-pair, and meter semantics. It does not mean host, network, deployment, or
building automation infrastructure. The catalog records site-to-grid-connection,
grid-connection-to-feeder, feeder-to-circuit, circuit-to-phase,
grid-connection-to-meter, site-to-load, and meter-to-load membership as
explicit one-to-many relations. It never
invents a site member, phase, meter, circuit, topology, or aggregation. It
declares no relation that places a line pair in that topology.

The typed fields cover per-phase voltage, current, active/reactive/apparent
power; line-to-line voltage on the line-pair dimension; grid frequency and
power factor; direction-separated import/export active/reactive power plus
non-directional apparent power; import/export energy counters; and connection,
readiness, breaker, fault, and interlock state. Line-to-line voltage is
`infrastructure.ac.voltage_line_line` on `infrastructure.dimension.line_pair`.
It is not the phase voltage `infrastructure.ac.voltage`, and it is not stored
on `infrastructure.dimension.phase`. The line-pair service has a read
descriptor and no read capability. Self-consumption is
`infrastructure.energy.self_consumption`. It is not the import counter.
`infrastructure.accuracy.measured` is a boolean and
`infrastructure.accuracy.ratio_maximum` is `unit.ratio` on
`infrastructure.dimension.meter`. Both are qualified by
`infrastructure.dimension.measurement_type`. The ratio bounds are empty.
This pack does not publish an Accuracy struct.
Point-of-coupling power is `infrastructure.power.pcc`.
It is not the import/export pair. The fallback grid limit is
`infrastructure.limit.fallback_power`. It is not the PV export limit.
Quantities use canonical volt,
ampere, watt, volt-ampere-reactive, volt-ampere, hertz, ratio, and joule units
under the [unit rule](../../README.md#unit-rule): the import and export energy
counters are in joule, and their bounds are the exact conversions of their
earlier customary bounds. A customary unit appears only at display, in a
consumer. Published Decimal bounds are pack validation bounds, never a site
capacity or a device nameplate claim.

Unknown, unavailable, unsupported, stale, withdrawn, and conflicting values use
kernel quality, availability, and conflict records. They are not symbols. Native
values which mix import/export, phases, topology, aggregation, state, or units
remain native evidence until a separately qualified mapping accounts for loss.

## Capability and operation boundary

The catalog supplies read capabilities for the site, grid connection, feeder,
circuit, phase, and meter services. They require a qualified current binding.
It deliberately indexes no operations, effect rules, or Portal operation
descriptor: no qualified native route proves an infrastructure control action.

Consequently this pack does not publish generic import/export limit control,
enable/disable, breaker actuation, reset, or a live recipe. A future operation
requires a new reviewed pack version with an exact argument and effect rule,
current source/generation/revision admission, qualified active capability, exact
route, action-time authority, dispatch/acknowledgement/readback evidence,
terminal outcomes, and no blind retry after an indeterminate handoff. A Portal
may consume only currently promoted read facts; it cannot create topology,
semantic truth, authority, or a route.

## Lifecycle, counters, and loss

Source epoch, driver generation, semantic revision, qualification, activation,
generation fencing, partial updates, stale/unknown evidence, and permitted
last-known-good retention remain independent. Publication requires a current
source/generation/revision and qualified active capability. Partial publication
changes supplied valid fields only; withdrawal is explicit and generation-fenced.
Stale or unknown evidence cannot promote, authorize, or operate. A
verification level recorded beside an element blocks nothing. No element is
marked sensitive or hidden.

Import/export counter decrease does not prove reset or wrap. Native evidence is
required; the result is counter-continuity evidence or explicit loss. Projection
loss records native enums/bitfields, precision/range, phase/grid/feeder/circuit/
meter topology, direction/reference, aggregation, counter continuity,
unavailable fields, conflicts, vendor extensions, and unsupported operations.

## Native evidence boundary

Inputs are semantic documentation `e22451c8ca3d3f7275635216450f8fb2d216801e`,
semreg `cc9b324225e945598128eeabe977e7fa0af6dc93`, eBUS documentation
`5d66c66ef15e6bb2d473a341dae17dc9f9e25e05`, Modbus documentation/registry
`7ba9c333539c4381c06584cab0dc86c7e9280767` /
`7853d903970a4fdded35abaef01fe30f7e93be6a`, eeBUS ledger/M6.25 donor
`81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1` /
`cedf238e34f879815ba773e9cd76b2b31c2822a3`, and Matter draft
`29b4768a513cf566011ab8cd60df1bc495204953`.

No donor proves a universal electrical-infrastructure mapping. eBUS remains
identity/provenance-only unknown evidence. Modbus evidence catalogs
profile-specific candidates, but this infrastructure row remains unknown until
an exact relevant profile is selected; neither gains projection, promotion,
control route, or live authority. eeBUS is
`unknown_pending_normative_source`; Matter is a design input, not conformance. No mapping
in this pack is normative or operation authority.

## Compatibility and validation

The five-domain catalog has thermal/HVAC, PV/inverter, storage/BMS, EVSE, and
infrastructure accepted. This is typed 0.7 documentation only. It creates no
semreg runtime, native driver, gateway, Portal UI, Home Assistant entity,
deployment, hardware qualification, live action, 0.8 IR, or code generation.
The version rule of [api/README.md](../../README.md#version-rule) applies,
including its rule for in-place changes until the 0.7 release.

Run `python3 scripts/validate_infrastructure_pack_v1.py`,
`python3 scripts/test_validate_infrastructure_pack_v1.py`, and
`./scripts/check_docs.sh`.

## Load, events, and further fields

`resource.load` is a function on the physical and energy planes.
`infrastructure.dimension.load` and `infrastructure.service.load` use those planes.
`infrastructure.portal.read.load` reads every load-dimension field.
`infrastructure.capability.read.load` is not a member.
`infrastructure.dimension.harmonic_order` is `unit.one` and stores no minimum.
`infrastructure.ac.phase_power_factor` is a signed quantity in `unit.ratio` on `infrastructure.dimension.phase` with empty bounds.
`infrastructure.ac.harmonic_current` and `infrastructure.ac.harmonic_phase` withhold the unit.
`infrastructure.limit.pv_curtailment_factor` is closed from 0 to 1.
Empty bounds stay empty.
A new signed quantity names `infrastructure.relation.feeder_circuit`.
`pv.configuration.grid_code` is not an infrastructure element.
`infrastructure.event.supply_condition_changed` is derived from `infrastructure.status.supply_condition`.
`infrastructure.event.energy_measured` is emitted from `infrastructure.energy.import` with payload `infrastructure.energy.export`.

```text
infrastructure.load.active_power
infrastructure.load.phase_active_power
infrastructure.load.energy_consumed
infrastructure.load.energy_produced
infrastructure.energy.reactive_import
infrastructure.energy.reactive_export
infrastructure.energy.apparent_import
infrastructure.energy.apparent_export
infrastructure.energy.phase_import
infrastructure.energy.phase_export
infrastructure.ac.phase_power_factor
infrastructure.ac.reactive_current
infrastructure.ac.apparent_current
infrastructure.ac.neutral_current
infrastructure.ac.harmonic_current
infrastructure.ac.harmonic_phase
infrastructure.limit.pv_curtailment_factor
infrastructure.meter.kind
infrastructure.meter.point_of_delivery
infrastructure.meter.protocol_version
infrastructure.meter.power_threshold
infrastructure.meter.apparent_power_threshold
infrastructure.meter.power_threshold_source
infrastructure.status.supply_condition
infrastructure.mgcp.use_case_name
infrastructure.mpc.use_case_name
infrastructure.mgcp.actor
infrastructure.mpc.actor
infrastructure.mgcp.use_case_version
infrastructure.mpc.use_case_version
infrastructure.mpc.ac_power
infrastructure.mgcp.ac_current
infrastructure.mpc.ac_voltage
infrastructure.mpc.value_state
infrastructure.mgcp.value_source
infrastructure.mgcp.value_range_min
infrastructure.mpc.value_range_min
infrastructure.mpc.one
infrastructure.mgcp.per
infrastructure.mpc.per
infrastructure.mgcp.slots
infrastructure.mpc.slots
infrastructure.mgcp.committed_power_plan
infrastructure.dimension.harmonic_order
infrastructure.dimension.load
infrastructure.service.load
infrastructure.portal.read.load
infrastructure.event.supply_condition_changed
infrastructure.event.energy_measured
```
