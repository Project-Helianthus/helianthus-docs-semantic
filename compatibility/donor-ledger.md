# Bootstrap compatibility donor ledger

Status: starting inventory for future contract work. Each entry is an immutable
public source inspected for the reviewed conceptual direction. Inclusion does
not promote the donor into a universal model, prove current normative
completeness, or accept a migration.

| Donor | Candidate compatibility surface | Bootstrap limit |
|---|---|---|
| [`helianthus-ebusreg@738142f`](https://github.com/Project-Helianthus/helianthus-ebusreg/tree/738142f97519b3d5566f6d75d9c3975d7ffe2e96) | eBUS/PV values, units, lifecycle, registry, counter, and projection behavior | eBUS-specific; complete current consumer and persistence inventory remains future work |
| [`helianthus-ebusgateway@e31106c`](https://github.com/Project-Helianthus/helianthus-ebusgateway/tree/e31106c9c726fbb8df7546901763e19b93659e72) | DriverManager generation/lifecycle and native-to-canonical adapter seams | Gateway runtime remains the owner; bootstrap does not migrate or duplicate it |
| [`helianthus-eebusreg@ede40b9`](https://github.com/Project-Helianthus/helianthus-eebusreg/tree/ede40b929e9c2d9cbf0de20c4844e737d5e6af68) | Native snapshots, typed native values, evidence envelopes, and raw operation outcomes | Native eeBUS contracts remain native; exact normative revisions are unresolved |
| [`helianthus-docs-eebus@81cd647`](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1/protocols/eebus-normative-source-ledger.md) | Public ledger of accessible eeBUS source/version evidence and gaps | It does not authorize inventing one current eeBUS revision or a frozen mapping |
| [`software guide@ec6050f`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/ec6050fb31738f201c96203c52be0702671df343/software-stabilization-07-08.implementing/00-canonical.md) | Public ownership, dependency, and 0.7/0.8 delivery boundary | Planning guide only; repository issues, contracts, tests, and reviews provide acceptance |
| [`semantic reconciliation@ec6050f`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/ec6050fb31738f201c96203c52be0702671df343/software-stabilization-07-08.implementing/93-semantic-draft-reconciliation.md) | Retained semantic requirements and planned owner split | Does not complete INT-04 or create an executable schema |

Future implementation issues must refresh the donor inventory against live
public state, pin the exact inputs used for fixtures, and record every migration
difference. A newer revision is not accepted merely because it is newer.
