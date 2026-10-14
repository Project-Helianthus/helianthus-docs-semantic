# Family catalog contract v1

`helianthus.semreg.family-catalog/v1` is a protocol-neutral, read-only contract
for a catalog that records, for each device or protocol family, the
qualification state its published evidence supports today, why that state is
not stronger, how the family reaches consumers, and where the evidence lives.

Status: accepted contract definition, compared against SemReg revision
`455d902aa231ec4baef741dbfe9a719455c28362`. Owning implementation package:
[`semreg/v1/catalog`](https://github.com/Project-Helianthus/helianthus-semreg/blob/455d902aa231ec4baef741dbfe9a719455c28362/semreg/v1/catalog/catalog.go)
in `Project-Helianthus/helianthus-semreg`, which also owns the fixture
[`fixtures/v1/family-catalog-v1.json`](https://github.com/Project-Helianthus/helianthus-semreg/blob/455d902aa231ec4baef741dbfe9a719455c28362/fixtures/v1/family-catalog-v1.json)
and its [`fixtures/README.md`](https://github.com/Project-Helianthus/helianthus-semreg/blob/455d902aa231ec4baef741dbfe9a719455c28362/fixtures/README.md).
The `Qualification` vocabulary it reuses is defined in this repository at
[`api/v1/kernel.md`](kernel.md#type-quality). This page defines the contract
only. It states no family's state, composition or evidence; those live in the
fixture with their evidence references.

Evidence basis: the SemReg decoder and validator, the fixture README, and the
fixture's own reason statements at the revision above, which agree on every
vocabulary and rule stated here. Compatibility effect: new contract; no
existing contract changes.

A catalog row never creates a native mapping, route, authority, consumer
binding or live operation. It records a state and points at evidence owned
elsewhere.

## Document

The catalog is one JSON object with exactly these members. Every member below
is required; no other member is allowed at any object level, and a repeated
member name in any object is rejected rather than resolved to the last value.
Trailing data after the document is rejected.

| Member | Type | Rule |
| --- | --- | --- |
| `contract` | string | Exactly `helianthus.semreg.family-catalog/v1`. |
| `semantic_docs_pin` | string | `Project-Helianthus/helianthus-docs-semantic@` followed by a full 40-character commit SHA of the semantic documentation the vocabulary was taken from. |
| `states` | array of string | The declared state vocabulary. It MUST equal the `Qualification` set below exactly: every value present once, no other value. |
| `families` | array of family | One row per family; `family_id` values are unique. |

### Family row

All members are required. `native_owner` and `semantic_pack` MAY be empty
strings when no native owner or capability pack exists; every other string MUST
be non-empty.

| Member | Type | Rule |
| --- | --- | --- |
| `family_id` | string | Stable identifier, unique within the catalog. |
| `name` | string | Human-readable family name. |
| `native_owner` | string | Public registry repository that owns the family's native evidence, or empty. |
| `semantic_pack` | string | Exact `PackRef` of the accepted capability pack the family maps to, or empty. |
| `state` | string | One `Qualification` value; see [State](#state). |
| `composition` | string | One composition value; see [Composition](#composition). |
| `composition_verified` | boolean | See [Composition](#composition). |
| `reason` | string | One reason value; see [Reason](#reason). |
| `evidence` | array of evidence | At least one entry; see [Evidence](#evidence-references). |

A catalog is complete only against a family list that its consumer pins (for
INT-05, the family list of the INT-07 draft). Completeness is a consumer check:
a missing or unlisted family is rejected, but this contract does not itself
enumerate families.

## State

`state` reuses the existing kernel `Qualification` vocabulary and adds nothing
to it. The definition lives in the
[kernel v1 `Quality` type](kernel.md#type-quality): `candidate`,
`qualified`, `unsupported`, `unknown`, `rejected`, with the semantics stated
there (for example that `unsupported` and `rejected` forbid a value and
promotion, and that `unknown` cannot be promoted or satisfy a capability). This
contract does not redefine them.

The catalog has no value for conditions such as "evidence blocked", "no
admissible profile" or "no-go". Those conditions stay `unknown` or `candidate`
and are named by `reason`. A catalog MUST NOT invent a state value, and a
`qualified` row requires evidence that satisfies the owning native
qualification and the semantic contract; a catalog entry, similar concept,
address or model string alone is not such evidence.

## Composition

`composition` records how the family reaches consumers at a pinned gateway
revision.

| Value | Meaning |
| --- | --- |
| `composed` | The family is composed through SemReg. |
| `composed_legacy` | The family is composed on a legacy layer, not through a SemReg pack. |
| `provider_local` | The native provider emits the family and no gateway composition is claimed. |
| `not_composed` | No composition is claimed. |

`composition_verified` is a flag, not a state:

- Any `composition` other than `not_composed` requires
  `composition_verified=true` and at least one `gateway_composition` evidence
  entry pinned to a full gateway commit.
- `composition_verified=true` requires such a `gateway_composition` entry.
- A `not_composed` row MUST have `composition_verified=false` and MUST NOT carry
  any `gateway_composition` evidence entry: verification and gateway-composition
  evidence apply only to a claimed composition.
- `composition_verified=false` means the composition is **unverified**. It does
  not assert that the family is absent from the gateway, and `not_composed`
  with `composition_verified=false` means only that no composition is claimed.

## Reason

`reason` explains why a row is not stronger than its `state`. It is a closed
vocabulary; each value has one definition, and a value never changes meaning
within v1.

| Value | Definition |
| --- | --- |
| `offline_profile_only` | The cited native disposition admits an offline profile only. Source wording: "outcome OFFLINE_PROFILE_ADMITTED; live_qualified=false, write_authority=false, support_claim=false". |
| `offline_mapping_gate_only` | The cited evidence is an accepted source-specific read-only mapping gate over offline observations. Source wording: "neither device support nor physical qualification". |
| `family_compatible_offline` | The cited native evidence is offline and family-compatible only. Source wording: "offline family-compatible native evidence only"; "no sender, control route or live authority". Any narrower restriction, such as absolute allocation being withheld for a relative or unknown state while allocated and actual current stay separate native candidates, is the conditional rule of the owning pack or mapping and is not implied by this reason. |
| `no_admissible_profile` | The pinned native sources establish no admissible exact profile tuple. Source wording: "establishes no admissible exact device-type/model-build/protocol tuple". |
| `qualification_test_ready_offline` | A native qualification card reports the qualification as test-ready. Source wording: "QUALIFICATION_TEST_READY; HardwareTestReady, LiveQualified, CatalogRegistered, SupportClaim, WriteAuthority all false". |
| `evidence_blocked` | A native qualification card or disposition reports the qualification as blocked on evidence. Source wording: "QUALIFICATION_EVIDENCE_BLOCKED". |
| `no_go_missing_evidence` | The native owner recorded a no-go for lack of evidence. Source wording: "NO_GO / missing evidence; typed decoding, discovery and acquisition removed". |
| `offline_replay_only` | The cited evidence is offline replay qualification of receive-only observations. Source wording: "replay-qualified offline; receive-only". |
| `semantic_mapping_unknown` | Native receive-side evidence exists but the family's semantic mapping is not established. Source wording: "state cells remain native and opaque"; "no mapping is normative". |
| `legacy_layer_composition` | The cited gateway composition evidence shows the family reaching consumers through the legacy semantic layer, not a SemReg pack publication. Source wording: "the legacy semantic layer, not a SemReg thermal pack publication". |
| `unknown_pending_std_01` | The family stays unknown while the dependency named `unknown_pending_std_01` in the accepted packs is unresolved. Source wording: "remains unknown_pending_std_01 in every pack; no normative mapping or conformance claim". |
| `no_producer` | No producer, topology instance or mapping is established for the family. Source wording: "no producer, topology instance or mapping exists". |

## Evidence references

Each `evidence` entry is an object with exactly four non-empty string members.

| Member | Rule |
| --- | --- |
| `owner` | Public repository reference in one of two forms. `Project-Helianthus/<repository>@<revision>` pins an immutable revision, so the `locator` path at that revision is reproducible. `Project-Helianthus/<repository>#<number>` names an issue or pull request thread; it pins no revision and its content can change, so it is used only for kinds `issue` and `pull_request`, and the `statement` records what the thread established when cited. |
| `kind` | Evidence kind, for example `native_disposition`, `native_evidence`, `native_qualification_card`, `native_registry`, `semantic_contract`, `semreg_fixture`, `issue`, `pull_request` or `gateway_composition`. Kinds are an open, additive vocabulary. |
| `locator` | Path inside the repository at the pinned revision (`@` form), or the URL of the issue or pull request (`#` form). |
| `statement` | What the cited material establishes, stated without copying restricted text and without claiming more than the source. |

A `gateway_composition` entry cites gateway code for a composition claim. It
MUST use the `@` form and its `owner` MUST be `Project-Helianthus/helianthus-ebusgateway@` followed by the
full 40-character commit SHA; an abbreviated revision is rejected. Evidence
MUST be publishable: no private material, device capture, serial, network
coordinate or credential.

## Compatibility

Within v1 only additive vocabulary values are allowed: new families, new
`reason` values, new `composition` values and new evidence kinds. The following
require a new contract version (`v2`):

- a new `state` value, since `state` is the kernel `Qualification` set;
- removing or renaming any member or vocabulary value;
- adding a member to the document, a family row or an evidence entry;
- changing the meaning of an existing value or flag.

A v1 reader rejects an unknown member and an out-of-vocabulary value; a v1
reader that does not know an additively added value fails closed rather than
mapping it to a known one.

## Relation to packs and INT-05

The accepted capability packs
([thermal/HVAC](packs/thermal-hvac-v1.md), [storage/BMS](packs/storage-bms-v1.md),
[PV/inverter](packs/pv-inverter-v1.md), [EVSE](packs/evse-v1.md),
[infrastructure](packs/infrastructure-v1.md)) define typed vocabulary. A
family's `semantic_pack` names a pack; it does not turn a candidate native row
into a normative mapping, and the pack specifications keep ownership of what a
row may expose.

INT-05 acceptance requires that every existing family has a catalog row and a
correct state: insufficient evidence remains `unknown` or `candidate`, is not
excluded from scope, and is not fabricated. Accordingly a row is never silently
dropped for lack of evidence, and a state is never raised above what its
evidence references support.

## Unresolved questions

- The `reason` definitions quote the evidence statements in the fixture; the
  SemReg README lists the values without definitions, so the definitions here
  are the contract's own wording over those sources.
- The `unknown_pending_std_01` dependency is defined by the accepted packs, not
  by this contract; this page does not restate it.
- Completeness against a family list is checked by the consumer against a list it
  pins; this contract names no list.
- The SemReg validator checks only that `owner` is non-empty, apart from the
  `gateway_composition` pin; the two `owner` forms above are a documentation
  rule that the validator does not yet enforce.

## Falsifiers

This contract is wrong, and a correction is required, if any of the following is
shown at a pinned revision:

- a fixture or decoder accepts a `state` outside the kernel `Qualification` set,
  or a document whose `states` member differs from it;
- a row with a claimed composition is accepted without `composition_verified=true`
  and a full-SHA `gateway_composition` entry;
- a `not_composed` row is accepted with `composition_verified=true` or with a
  `gateway_composition` entry;
- a document with an unknown or repeated member, or trailing data, is accepted;
- a `reason` value is used with a meaning that contradicts its definition above,
  or a row's `state` is `qualified` without the owning native qualification;
- a family is dropped, or given a fabricated state, because its evidence is
  insufficient.

## Validation and limits

Run `python3 scripts/validate_family_catalog_v1.py`,
`python3 scripts/test_validate_family_catalog_v1.py`, then
`./scripts/check_docs.sh`. These check that this page states the exact
vocabularies and rules of the contract; they do not read the SemReg fixture and
establish no family state, native qualification or live behavior.
