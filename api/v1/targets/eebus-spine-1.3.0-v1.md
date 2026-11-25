---
status: "adoption contract under `helianthus.gateway.eebus-projection/v1`,\npre-1.0 and not stable before Helianthus 1.0. The\n[machine-readable descriptor](eebus-spine-1.3.0-v1.json) is the eeBUS SPINE\n1.3.0 target. It records fact-table citations and does not emit a datagram\nor allocate an entity."
---

# eeBUS SPINE 1.3.0 projection contract v1

Status: adoption contract under `helianthus.gateway.eebus-projection/v1`,
pre-1.0 and not stable before Helianthus 1.0. The
[machine-readable descriptor](eebus-spine-1.3.0-v1.json) is the eeBUS SPINE
1.3.0 target. It records fact-table citations and does not emit a datagram
or allocate an entity.

## Evidence and model identities

The target is `eebus.spine` revision 1.3.0. The contract is
`helianthus.gateway.eebus-projection/v1`, status
`adoption_projection_contract_pre_1_0`, mapping revision 1.

Source-model inspection is **Hypothesis**. The inspection basis is the
fact-table scenario, feature, function and conversion cells. Requirement
text is not copied. Execution is **Unknown**. Standards equivalence is
**Unknown**. A cited row records target equivalence **Hypothesis**.

A public document is cited by name and revision. A restricted use case is
cited by its name, its revision and its scenario identifier, as the fact
tables record them. Requirement prose is not copied. SPINE is cited by the
name SPINE and revision 1.3.0, together with the clause numbers the source
states, only when that source names this revision. The file-level target
version stays 1.3.0.

The descriptor does not ship a node, pair devices, emit a datagram,
allocate an entity, certify a product, claim conformance, claim a live
device, or claim a physical result. It does not copy use-case requirement
text. The two draft use cases excluded by the publication rule are not
cited.

The projection contract is owned by
Project-Helianthus/helianthus-docs-semantic. Kernel and packs are owned by
Project-Helianthus/helianthus-semreg. The runtime implementation is owned
by Project-Helianthus/helianthus-eebusreg.

## Accounting and admission

The roster is derived from the [element catalog](../element-catalog-v1.json):
one row for every fact, capability, operation, service, relation definition
and event owned by an accepted pack. Core-owned elements, dimensions,
effect rules and presentations are not requested. Rows sort by exact pack
ID, pack version, item ID and item version. Kind is part of row identity.

Each fact, capability, operation and relation row preserves its typed
kernel-v1 request and exact snapshot and revision binding. Fact rows keep
their canonical runtime FactKey dimensions, read from the catalog subject.
A service or an event is not a kernel-v1 requested item, so its `requested`
member is null. A relation row keeps the catalog core type and, when the
catalog states one, the medium.

A row whose fact-table eeBUS cell is empty is `unknown` with reason
`eebus.unmapped.v1` and has no target. A catalog element with no fact-table
eeBUS cell is unknown the same way. A cell that names only a Matter device
type or cluster element is unknown the same way. A cited row uses reason
`eebus.cited.v1`.

A citation may name use cases, scenario identifiers, SPINE features,
functions, keys, one stated parameter, entity types, scopes and a unit
conversion. A unit conversion is recorded only when the source states the
native unit, the power-of-ten scale, the scale used when the scale is
absent, and the canonical unit. The algorithm is
`number_times_ten_to_scale`. A factor is recorded only when the source
states a whole number of joules per watt-hour and the canonical unit is
`unit.joule`. A source that leaves the conversion or the scale undeclared
omits the conversion. No factor, offset or rounding is invented.

Each row has one irreversible policy loss. A cited row records that the
citation does not emit a SPINE datagram or allocate an entity. An unknown
row records that no SPINE feature, function, entity, scenario or datagram
is created.

The Matter 1.6.1 target and the historical Matter 1.7 ledger are unchanged.
No pack version is raised.

`python3 tests/test_eebus_target.py` checks the roster, the citations, the
empty-cell rule and this page.
