# Kernel v1 compatibility donor ledger

Status: pinned public inputs and migration comparators for the v1 kernel
contract. Each source was reconciled again while preparing the contract.
Inclusion does not promote the donor into a universal model, prove current
normative completeness, or accept a migration.

| Donor | Required kernel comparator | Boundary |
|---|---|---|
| [`helianthus-ebusreg/pv@738142f`](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/738142f97519b3d5566f6d75d9c3975d7ffe2e96/pv/types.go) | Exact string decimals, units, typed dimensions, quality/availability/freshness, monotonic receipt/retention, counter evidence, provenance digests, partial fact retention, generation, capability outcome, and complete requested-output accounting | eBUS/PV-specific and mainly single-source; v1 preserves it as a migration comparator while adding multiple candidates, source epochs, wall uncertainty, distinct quality axes, and operation evidence |
| [`helianthus-ebusreg projection@738142f`](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/738142f97519b3d5566f6d75d9c3975d7ffe2e96/registry/projection.go) | Stable public service-plane identities and explicit per-plane paths | Path identity becomes a tested compatibility alias/view; it is not adopted as physical asset or native route identity |
| [`gateway DriverManager@e31106c`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/e31106c9c726fbb8df7546901763e19b93659e72/internal/drivermanager/manager.go) | Current generation/revision, activation before running capability publication, effective-capability admission under lock, generation-bound callback/release, safety quarantine, and bounded non-reentrant withdrawal | Gateway/runtime remains the owner. Kernel source epoch, driver generation, semantic revision, lifecycle operation, intent, idempotency, and causal correlation stay distinct; v1 additionally requires an explicit semantic transition fence before a higher generation is published, without importing the manager |
| [`gateway Modbus adapter@e31106c`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/e31106c9c726fbb8df7546901763e19b93659e72/internal/modbusadapter/canonical_pv.go) | Profile-qualified exact native-to-PV candidate translation and source evidence | A producer seam only; it does not justify semreg importing gateway/Modbus code or treating existing PV as universal |
| [`eeBUS native snapshot@ede40b9`](https://github.com/Project-Helianthus/helianthus-eebusreg/blob/ede40b929e9c2d9cbf0de20c4844e737d5e6af68/native_snapshot_v2.go) | Separate observation/capture/data timestamps, protocol version, topology/services/sessions/use cases, typed native unknowns, bounds, validation, and deep-clone immutability | Native eeBUS identity and values remain native evidence; their presence does not create semantic qualification or capability |
| [`eeBUS evidence envelope@ede40b9`](https://github.com/Project-Helianthus/helianthus-eebusreg/blob/ede40b929e9c2d9cbf0de20c4844e737d5e6af68/eebusevidence/envelope_v1.go) | Lowercase SHA-256 digests, authorization scope, redaction, data/capture timestamps, unknown preservation, canonical object order, and public-safe formatting | Evidence remains under the native owner's access/redaction contract; a digest neither discloses payload nor grants authority |
| [`eeBUS raw operation outcomes@ede40b9`](https://github.com/Project-Helianthus/helianthus-eebusreg/blob/ede40b929e9c2d9cbf0de20c4844e737d5e6af68/eebusraw/raw_mutation_v1.go) | Dispatch, reply, verify, applied/no-contact/rejected/no-effect/conflict/unknown outcomes, possible-side-effect evidence, and retry restrictions | Native mutation remains native; kernel v1 preserves the evidence distinctions without claiming eeBUS mapping or conformance |
| [`eeBUS normative ledger@81cd647`](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1/protocols/eebus-normative-source-ledger.md) | Public record of accessible eeBUS source/version evidence and unresolved exact revisions | It does not authorize inventing one current eeBUS version, copying restricted standards, or freezing a mapping |
| [`Matter draft 1.7 ballot 0.9@29b4768`](https://github.com/AryaHassanli/connectedhomeip/commit/29b4768a513cf566011ab8cd60df1bc495204953) | Provisional energy-range and electrical-topology concepts used to test kernel expressiveness | Upstream PR #73842 remained open and draft when reconciled; this pin is not final Matter publication or conformance |
| [`software guide@ec6050f`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/ec6050fb31738f201c96203c52be0702671df343/software-stabilization-07-08.implementing/00-canonical.md) | Public ownership, dependency, and 0.7/0.8 delivery boundary | Planning guide only; repository issues, contracts, tests, and reviews provide acceptance |
| [`semantic reconciliation@ec6050f`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/ec6050fb31738f201c96203c52be0702671df343/software-stabilization-07-08.implementing/93-semantic-draft-reconciliation.md) | Retained semantic requirements and planned owner split | Does not complete INT-04 or create an executable schema |

INT-05 must freeze the exact donor fixtures, externally consumed identities, and
persisted forms used by its implementation issue. It must compare value, unit,
dimensions, quality, availability, freshness, counter continuity, provenance,
identity, capability outcome, and projection accounting. Every accepted
difference receives a reviewed migration disposition and rollback behavior.

A newer donor revision is not accepted merely because it is newer. Removing an
old public identity or eBUS-owned universal type waits until every known consumer
and persisted identifier is migrated and the exact integrated release verifies
forward state, restart continuity, and rollback.
