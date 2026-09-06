# EVSE capability pack v1

`helianthus.pack.evse/v1` has exact PackRef `{id: "helianthus.pack.evse",
version: "1.0.0"}`. It is the accepted software-0.7 typed input over
`helianthus.semantic.kernel/v1`; its machine-significant catalog is
[evse-acceptance-vectors.json](evse-acceptance-vectors.json). Every indexed item
is an exact `DefinitionRef` owned by this PackRef.

## Fields and topology

The catalog declares electrical phase measurements, session and lifetime energy
counters, advertised/configured/allocated/actual current limits, and connection,
charging, readiness, fault, and interlock facts. Quantities use canonical volt,
ampere, watt, hertz, and kilowatt-hour units. Published Decimal bounds are pack
validation bounds, never a claim about a device's nameplate capability.

Fact keys distinguish asset, EVSE, connector, phase, session, and meter. The
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
evse.status.connection             evse.status.charging
evse.status.readiness              evse.status.fault
evse.status.interlock
evse.dimension.asset               evse.dimension.evse
evse.dimension.connector           evse.dimension.phase
evse.dimension.session             evse.dimension.meter
evse.service.evse                  evse.service.connector
evse.service.phase                 evse.service.session
evse.service.meter
evse.relationship.asset_evse       evse.relationship.evse_connector
evse.relationship.connector_phase  evse.relationship.connector_session
evse.relationship.evse_meter
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

## Capability and operation boundary

Read capabilities require a qualified current binding. The sole generic
operation is `evse.operation.set_allocated_current`; it requires the exact
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
`unknown_pending_std_01`; Matter is a design input, not conformance. No mapping
in this pack is normative or an operation authority.

## Compatibility and validation

The five-domain catalog has thermal/HVAC, PV/inverter, storage/BMS, and EVSE
accepted; infrastructure remains the required follow-on. This is typed 0.7
documentation only. It creates no semreg runtime, native driver, gateway,
Portal UI, Home Assistant entity, deployment, hardware qualification, live
action, 0.8 IR, or code generation. Breaking change requires a new major pack
directory.

Run `python3 scripts/validate_evse_pack_v1.py`,
`python3 scripts/test_validate_evse_pack_v1.py`, and `./scripts/check_docs.sh`.
