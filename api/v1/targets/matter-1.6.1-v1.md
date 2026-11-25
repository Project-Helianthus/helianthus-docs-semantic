---
status: "adoption contract under `helianthus.gateway.matter-projection/v1`,\npre-1.0 and not stable before Helianthus 1.0. The\n[machine-readable descriptor](matter-1.6.1-v1.json) is a separate target in the\nexisting versioned contract. It does not introduce a major or experimental\nnamespace. It does not activate the existing pinned HTTP feed or replace its\nchecker. Those migration edges remain owner-controlled."
---

# Matter 1.6.1 projection contract v1

Status: adoption contract under `helianthus.gateway.matter-projection/v1`,
pre-1.0 and not stable before Helianthus 1.0. The
[machine-readable descriptor](matter-1.6.1-v1.json) is a separate target in the
existing versioned contract. It does not introduce a major or experimental
namespace. It does not activate the existing pinned HTTP feed or replace its
checker. Those migration edges remain owner-controlled.

## Evidence and model identities

The graded report **go-fabric suitability for the Helianthus Matter binding**
provides the source-inspection basis for the adopted Matter 1.6.1 target in
SukramJ/go-fabric v0.13.12. Proven here means verified in the cited source by
that report, not independently executed in this repository. Public versioned
source references are:

- [Electrical Sensor](https://github.com/SukramJ/go-fabric/blob/v0.13.12/device/electrical_sensor_gen.go): device type `0x0510`, revision 1.
- [Power Topology](https://github.com/SukramJ/go-fabric/blob/v0.13.12/cluster/spec/powertopology/definition_gen.go): cluster `0x009C`, revision 1.
- [Electrical Power Measurement](https://github.com/SukramJ/go-fabric/blob/v0.13.12/cluster/spec/electricalpowermeasurement/definition_gen.go): cluster `0x0090`, revision 3, optional nullable `ActiveCurrent` attribute `0x0005`, mA.

The report's model-source inspection is **Proven**; execution, complete
standards equivalence, feature/composition closure, conformance, certification,
controller interoperability, Linux arm64, Pi performance and latency remain
**Unknown**. No upstream source or SDK execution is retained by this descriptor.
Any proposed equivalence beyond those identities is a **Hypothesis** requiring
separate evidence. Optional current does not supply mandatory EPM attributes or
qualify an Electrical Sensor endpoint. Nothing here allocates an endpoint.

The [historical Matter 1.7 ledger](matter-1.7-ballot-0.9-v1.json) is the
accounting input for the fact, capability and operation rows, not a source pin
for this target. Electrical Sensor and Power Topology revisions change from 2 to
1; EPM remains revision 3. This deliberately defers the 1.7-only elements and
does not claim that changing revision constants makes a complete 1.7
implementation equivalent to 1.6.1.

## Accounting and admission

The roster is derived from the [element catalog](../element-catalog-v1.json):
one row for every fact, capability, operation, service and relation definition
owned by the five accepted packs, 252 rows in all (146 facts, 37 capabilities,
7 operations, 36 services and 26 relation definitions). Pack versions are
Energy management, EVSE, Infrastructure, PV and Thermal `1.0.0`, and Storage
`1.1.0`, as the catalog keys them. Core-owned elements, dimensions, effect rules and presentations are
not requested; the rows that cite them account for them. Rows sort by exact
pack ID, pack version, item ID and item version; kind is also part of row
identity. Each fact, capability, operation and relation row preserves its typed
kernel-v1 request and exact snapshot/revision binding. Fact rows keep their
canonical runtime FactKey dimensions, read from the catalog subject. These are
runtime bindings, not synthetic values supplied by the descriptor.

`helianthus.pack.energy_management` 1.0.0 adds one unknown row, reason
`matter.unmapped.v1`, for each of its facts, capabilities and operations.
`energy.service.subject` is unsupported, reason
`matter.service_not_requested_item.v1`. Dimensions, effect rules, events and
the read portal have no roster row. Where a reviewed column names a cluster
element, the row stays unknown: this roster admits one transformed row,
`evse.ac.current`, and the conversion for those columns is not established
here.

`helianthus.pack.equipment` 1.0.0 adds one unknown row, reason
`matter.unmapped.v1`, for each of its facts, capabilities and operations.
`equipment.service.unit` and `equipment.service.resource` are unsupported,
reason `matter.service_not_requested_item.v1`. Dimensions, effect rules,
events and the read portals have no roster row. Where a reviewed column
names a cluster element, the row stays unknown: the conversion factor,
offset, rounding and representation bounds are not stated, and this roster
admits one transformed row, `evse.ac.current`.

Measurement-type association, unverified. The Matter column recorded for the
measurement-type dimension is `ElectricalPowerMeasurement.Accuracy`. For the
measured boolean the recorded columns are `ElectricalPowerMeasurement.Accuracy`,
`ElectricalPowerMeasurement.NumberOfMeasurementTypes` and
`ElectricalEnergyMeasurement.Accuracy`; for the maximum ratio they are
`ElectricalPowerMeasurement.Accuracy` and `ElectricalEnergyMeasurement.Accuracy`.
No versioned public source is cited for these associations yet, so they are
unverified. They are Matter columns, not one device type, cluster, attribute or
conversion, and not a `MeasurementAccuracyStruct`. No row is `transformed` on
this basis, and no struct is published. `pv.dimension.measurement_type` and
`infrastructure.dimension.measurement_type` have no roster row.

The fed subject is the PV inverter. The catalog members are
`pv.accuracy.measured`, `pv.accuracy.ratio_maximum`,
`pv.dimension.measurement_type`, `infrastructure.accuracy.measured`,
`infrastructure.accuracy.ratio_maximum` and
`infrastructure.dimension.measurement_type`. The two measured facts are
booleans and the two ratio facts are `unit.ratio`, each qualified by its
measurement-type dimension. `storage.attribute.chemistry` and
`storage.configuration.battery_type` are not added, and neither id substitutes
for the other. `storage.limit.charge_current` and
`storage.limit.discharge_current` are catalog members, `unit.ampere` on
`storage.dimension.pack`, with both bounds empty. The six facts are the two
measured facts, the two ratio facts and the two current limits. Each of the
six facts has one `unknown` row, reason `matter.unmapped.v1`, and no target
member.

Electrical Power Measurement is not complete: `PowerMode`,
`MinMeasuredValue`, `MaxMeasuredValue`, `AccuracyRanges`, `RangeMin` and
`RangeMax` have no catalog element and no source in the cited tables. The
mandatory `NumberOfMeasurementTypes` has no catalog count, and `ActivePower` has
several partial sources and no single element id. Electrical Sensor `0x0510` is
therefore not a complete endpoint, and this row does not deliver it.

Only `evse.ac.current` is `transformed`, with reason
`matter.phase_association_by_relation.v1`, to device/cluster/attribute
`0x0510 / 0x0090 / 0x0005`. Multiply exact amperes by 1000; emit only an integral,
non-null signed `amperage-mA` value within the inclusive bounds
`-4611686018427387904..4611686018427387904`. The attribute is nullable, but this
positive projection never emits null. No rounding, truncation, saturation or
floating-point approximation is permitted: `1.234 A` is `1234 mA`, whereas
`0.0001 A` is nonrepresentable. Signed values and exact bounds are preserved.

Require exactly one eligible, pack-validated, phase-qualified source FactKey;
its pack ID/version, fact ID and exact canonical runtime dimensions must match.
Missing, multiple or ambiguous phase keys refuse the whole document. Stale,
unavailable, conflicted, invalid or revision-mismatched input and
any nonrepresentable value likewise produce **no target payload for the whole
document**, never partial success. Native evidence, source lineage, conflicts,
time domains and partial last-known-good state remain upstream; retained state
cannot substitute for current admission or invent a qualified value.

The positive row's member `relations` cites `evse.relation.connector_phase`,
the one catalog relation of its pack whose far endpoint is the phase dimension
of the source key. The association of the phase-qualified source with its
endpoint is accounted by that relation's own row, not declared as an identity
loss of the scalar value.

Each relation row carries the member `relation` with the catalog core type, and
the medium where the catalog states one. Every `measures` definition and every
`supplies` definition with medium `electrical` (five rows) is `withheld` with
reason `matter.power_topology_endpoint_unallocated.v1`. Its `target_construct`
names the Power Topology cluster `0x009C` with equivalence **Hypothesis**. That
construct carries an electrical association only between allocated endpoints.
This descriptor allocates none, so no association is emitted. The other 21
relation definitions (`contains`, `groups` and `hosts`) remain `unknown` with
`matter.relation_construct_not_adopted.v1`. Their target constructs lie outside
the three adopted model identities. No relation row is `unrepresentable`: the
catalog's admission record of every core type used here names a construct of
the target data model.

Kernel-v1 `ItemKind` names facts, relations, capabilities and operations only,
so a service is never a requested item. Each of the 36 services is
`unsupported` with `matter.service_not_requested_item.v1`, a null `requested`
member and no FactKey. Its subject has no allocated endpoint in this target.

All other 189 facts/capabilities/operations remain kernel-v1 `unknown` with
`matter.unmapped.v1` and irreversible policy loss. They create no target lookup,
inferred fallback, intent, authority, route, operation or control. A similar
name or model identity cannot promote them. Protocol-native facts still require
the public native documentation owner's contract before a semantic mapping.

## Explicit losses and compatibility

The transformed row retains the historical unit-loss declaration: only exact
integral mA are representable. It declares no separate identity loss; the
cited relation row carries the association and its loss. The projection
cannot reconstruct a phase or an endpoint, collapse multiple phases into a
total, or manufacture an endpoint correspondence. Preserve the original native
and semantic evidence outside the projection. Every service and relation row
declares one irreversible identity loss: no association or endpoint
correspondence is emitted or inferred. Unknown fact, capability and operation
rows retain their explicit irreversible policy loss. Absence of a target is not
an unsupported-device qualification.

This target adds an adoption descriptor; it does not silently retarget existing
consumers. The historical ledger, feed, dependency lock and gates remain separate
migration work. The roster bytes and their digest change in place before the
0.7 release; no contract, mapping or pack version is raised. The gateway's
Matter projection pins this descriptor's path and digest; that pin moves in the
same in-place wave as
[helianthus-matterreg#116](https://github.com/Project-Helianthus/helianthus-matterreg/issues/116).
The semantic owner is this repository; kernel, packs and typed
implementation inputs belong to
[helianthus-semreg](https://github.com/Project-Helianthus/helianthus-semreg).
The Matter SDK/runtime boundary belongs to
[helianthus-matterreg](https://github.com/Project-Helianthus/helianthus-matterreg).
This publication changes no eBUS MCP or GraphQL behavior or parity.

## Validation and falsifiers

Run `python3 -m unittest discover -s tests -p 'test_matter161_target.py' -v`.
The standard-library checks validate publication/accounting rules and disposable
JSON contract mutants. They do not test a production converter or SDK runtime.
The expected roster is computed from the element catalog, never from pinned
counts. Model version/revision drift, a second positive row, a missing
requested item of any pack and kind, a requested service, weakened phase
admission, rounding permission, a dropped or wrong relation citation, a
promoted relation or service, or erased loss must independently fail. Row
identity, source binding and cited relation axes are varied independently with
valid sibling values; all other fields remain unchanged in each mutant.

Unresolved: complete model/feature closure, endpoint allocation, reproducible
retained SDK inputs, real binding execution and platform/physical
qualification. Correct this contract if public versioned evidence contradicts
an identity, the element catalog changes, or a loss/guard is shown
insufficient. Such evidence requires reviewed contract correction, not
automatic admission. Full repository publication gates, committed-change
independent review and feed activation are outside this focused offline
evidence.
