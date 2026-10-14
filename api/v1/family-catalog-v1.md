# Family catalog contract v1

`helianthus.semreg.family-catalog/v1` is a protocol-neutral, read-only contract
for a catalog that records, for each device or protocol family, the
qualification state its published evidence supports today, why that state is
not stronger, how the family reaches consumers, and where the evidence lives.

Status: accepted contract definition. Owning implementation package:
[`semreg/v1/catalog`](https://github.com/Project-Helianthus/helianthus-semreg)
in `Project-Helianthus/helianthus-semreg`, which also owns the fixture
`fixtures/v1/family-catalog-v1.json`. This page defines the contract only. It
states no family's state, composition or evidence; those live in the fixture
with their evidence references.

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
- `not_composed` rows stay `composition_verified=false`: verification applies
  only to a claimed composition.
- `composition_verified=false` means the composition is **unverified**. It does
  not assert that the family is absent from the gateway, and `not_composed`
  with `composition_verified=false` means only that no composition is claimed.

## Reason

`reason` explains why a row is not stronger than its `state`. It is a closed
vocabulary; each value has one definition, and a value never changes meaning
within v1.

| Value | Definition |
| --- | --- |
| `offline_profile_only` | Evidence is an admitted offline profile only; no live qualification, write authority or support claim exists. |
| `offline_mapping_gate_only` | Evidence is an accepted source-specific mapping gate exercised over offline observations only; it is neither device support nor physical qualification. |
| `family_compatible_offline` | Evidence shows offline family-level compatibility only; no exact build, absolute value, sender or live authority is established. |
| `no_admissible_profile` | The pinned sources establish no exact, admissible profile tuple for the family. |
| `qualification_test_ready_offline` | A native qualification card reports the family ready for a qualification test; no live qualification or support claim exists. |
| `evidence_blocked` | A native qualification card or disposition reports qualification blocked by missing or insufficient evidence. |
| `no_go_missing_evidence` | The native owner decided no-go for typed decoding or acquisition because required evidence is missing. |
| `offline_replay_only` | Evidence is offline replay qualification of received observations only. |
| `semantic_mapping_unknown` | Native receive-side evidence exists, but no semantic mapping of the family is established. |
| `legacy_layer_composition` | The family reaches consumers through a legacy composition layer rather than a SemReg pack. |
| `unknown_pending_std_01` | The family is unknown pending the STD-01 standards-evidence work; no normative mapping or conformance claim exists. |
| `no_producer` | No producer, topology instance or mapping exists for the family. |

## Evidence references

Each `evidence` entry is an object with exactly four non-empty string members.

| Member | Rule |
| --- | --- |
| `owner` | Public repository pinned to an immutable revision, as `Project-Helianthus/<repository>@<revision>`. |
| `kind` | Evidence kind, for example `native_disposition`, `native_evidence`, `native_qualification_card`, `native_registry`, `semantic_contract`, `semreg_fixture`, `issue`, `pull_request` or `gateway_composition`. Kinds are an open, additive vocabulary. |
| `locator` | Path inside the repository at that revision, or issue or pull-request reference. |
| `statement` | What the cited material establishes, stated without copying restricted text and without claiming more than the source. |

A `gateway_composition` entry cites gateway code for a composition claim. Its
`owner` MUST be `Project-Helianthus/helianthus-ebusgateway@` followed by the
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

## Validation and limits

Run `python3 scripts/validate_family_catalog_v1.py`,
`python3 scripts/test_validate_family_catalog_v1.py`, then
`./scripts/check_docs.sh`. These check that this page states the exact
vocabularies and rules of the contract; they do not read the SemReg fixture and
establish no family state, native qualification or live behavior.
