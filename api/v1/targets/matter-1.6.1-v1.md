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
accounting input, not a source pin for this target. Electrical Sensor and Power
Topology revisions change from 2 to 1; EPM remains revision 3. This deliberately
defers the 1.7-only elements and does not claim that changing revision constants
makes a complete 1.7 implementation equivalent to 1.6.1.

## Accounting and admission

Exactly 127 requested items from the accepted five-pack
[metadata](../pack-metadata-v1.json) are retained: 88 facts, 32 capabilities and
7 operations. Pack versions are EVSE, Infrastructure, PV and Thermal `1.0.0`,
and Storage `1.1.0`. Services remain excluded. Rows sort by exact pack ID,
pack version, item ID and item version; kind is also part of row identity.
Each row preserves its typed kernel-v1 request, exact snapshot/revision binding,
and canonical runtime FactKey dimensions. These are runtime bindings, not
synthetic values supplied by the descriptor.

Only `evse.ac.current` is `transformed`, with reason
`matter.phase_endpoint_identity_loss.v1`, to device/cluster/attribute
`0x0510 / 0x0090 / 0x0005`. Multiply exact amperes by 1000; emit only an integral,
non-null signed `amperage-mA` value within the inclusive bounds
`-4611686018427387904..4611686018427387904`. The attribute is nullable, but this
positive projection never emits null. No rounding, truncation, saturation or
floating-point approximation is permitted: `1.234 A` is `1234 mA`, whereas
`0.0001 A` is nonrepresentable. Signed values and exact bounds are preserved.

Require exactly one eligible, pack-validated, phase-qualified source FactKey;
its pack ID/version, fact ID and exact canonical runtime dimensions must match.
Missing, multiple or ambiguous phase keys refuse the whole document. Stale,
unavailable, unqualified, conflicted, invalid or revision-mismatched input and
any nonrepresentable value likewise produce **no target payload for the whole
document**, never partial success. Native evidence, source lineage, conflicts,
time domains and partial last-known-good state remain upstream; retained state
cannot substitute for current admission or invent a qualified value.

All other 126 facts/capabilities/operations remain kernel-v1 `unknown` with
`matter.unmapped.v1` and irreversible policy loss. They create no target lookup,
inferred fallback, intent, authority, route, operation or control. A similar
name or model identity cannot promote them. Protocol-native facts still require
the public native documentation owner's contract before a semantic mapping.

## Explicit losses and compatibility

The transformed row retains the historical unit-loss declaration: only exact
integral mA are representable. Its separate irreversible identity loss states
that the scalar target loses phase identity and endpoint association. It cannot
reconstruct either, collapse multiple phases into a total, or manufacture an
endpoint correspondence. Preserve the original native and semantic evidence
outside the projection. Unknown rows retain their explicit irreversible policy
loss; absence of a target is not an unsupported-device qualification.

This target adds an adoption descriptor; it does not silently retarget existing
consumers. The historical ledger, feed, dependency lock and gates remain separate
migration work. The semantic owner is this repository; kernel, packs and typed
implementation inputs belong to
[helianthus-semreg](https://github.com/Project-Helianthus/helianthus-semreg).
The Matter SDK/runtime boundary belongs to
[helianthus-matter-binding](https://github.com/Project-Helianthus/helianthus-matter-binding).
This publication changes no eBUS MCP or GraphQL behavior or parity.

## Validation and falsifiers

Run `python3 -m unittest discover -s tests -p 'test_matter161_target.py' -v`.
The standard-library checks validate publication/accounting rules and disposable
JSON contract mutants. They do not test a production converter or SDK runtime.
Model version/revision drift, a second positive row, missing requested item,
weakened phase admission, rounding permission, or erased loss must independently
fail. Row identity and source binding axes are varied independently with valid
sibling values; all other fields remain unchanged in each mutant.

Unresolved: complete model/feature closure, reproducible retained SDK inputs,
real binding execution and platform/physical qualification. Correct this
contract if public versioned evidence contradicts an identity, the pack roster
changes, or a loss/guard is shown insufficient. Such evidence requires reviewed
contract correction, not automatic admission. Full repository publication gates,
committed-change independent review and feed activation are outside this focused
offline evidence.
