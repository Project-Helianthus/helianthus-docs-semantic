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
fixture's own reason statements at the revision above. They agree on the
vocabularies, the state set and the composition rules of that revision. The
`verification`, `module` and `version` members, the reason and evidence-kind
vocabularies, the unbounded pack list and the consumer rule below were revised
in place after it; the SemReg decoder and fixture adopt them separately.
Contract requirements are broader than validator coverage in two places: the
`@`/`#` evidence-owner forms are not enforced (the validator checks only a
non-empty `owner` and the gateway pin), and member presence is not enforced for
every member (an omitted `native_owner` or `semantic_pack` decodes to an empty
string, which the contract also permits, but the decoder cannot distinguish
omission from an explicit empty value). Compatibility effect: new contract; no
existing contract changes. The optional row member `further_semantic_packs` was
added after that revision: the SemReg decoder there rejects it as an unknown
member until the SemReg fixture, decoder and mapping-gate cross-check adopt it.

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

Every member except `further_semantic_packs`, `module` and `version` is
required; see [Packs of a row](#packs-of-a-row) and
[Composition](#composition). `native_owner` and `semantic_pack` MAY be
empty strings when no native owner or capability pack exists; every other string
MUST be non-empty.

| Member | Type | Rule |
| --- | --- | --- |
| `family_id` | string | Stable identifier, unique within the catalog. |
| `name` | string | Human-readable family name. |
| `native_owner` | string | Public registry repository that owns the family's native evidence, or empty. |
| `semantic_pack` | string | Exact `PackRef` of the accepted capability pack the family maps to, or empty. |
| `further_semantic_packs` | array of string | Optional. Further exact `PackRef` values of the accepted capability packs the family maps to; see [Packs of a row](#packs-of-a-row). |
| `state` | string | One `Qualification` value; see [State](#state). |
| `composition` | string | One composition value; see [Composition](#composition). |
| `composition_verified` | boolean | See [Composition](#composition). |
| `verification` | string | One verification value; see [Verification](#verification). |
| `module` | string | Optional. The driver module that registers the family; see [Composition](#composition). |
| `version` | string | Optional. The version of that module; see [Composition](#composition). |
| `reason` | string | One reason value; see [Reason](#reason). |
| `evidence` | array of evidence | At least one entry; see [Evidence](#evidence-references). |

A catalog is complete only against a family list that its consumer pins (for
INT-05, the family list of the INT-07 draft). Completeness is a consumer check:
a missing required family is rejected, and a valid additional family that the
list does not name is admitted. That differs from an unknown member of a Family
object, which stays rejected. The family list is every family the registered
drivers declare, with no fixed count, and this contract does not itself
enumerate families.

## Packs of a row

A family whose elements belong to more than one accepted capability pack names
every such pack in its row. `semantic_pack` holds the first of them and the
optional `further_semantic_packs` holds the others:

- `further_semantic_packs` is an array of exact `PackRef` strings, in the same
  form as `semantic_pack`, with no fixed count: a row names every accepted pack
  it maps to. Its entries are unique, and
  no entry equals `semantic_pack`.
- It is allowed only when `semantic_pack` is non-empty.
- It is omitted when the family has no further pack.
  A present empty array is rejected, so a row that names one pack or none
  keeps its bytes.
- Canonical order is ascending byte order of the `PackRef` strings. The
  entries are sorted in canonical order and
  `semantic_pack` sorts before every entry. A row in any other order is
  rejected, not reordered.
- No pack is primary: `semantic_pack` is the first in canonical order. It
  carries no precedence, default or ownership over the further packs.
- Cross-check: for every accepted mapping gate of a family, the row's packs
  (`semantic_pack` and every entry of `further_semantic_packs`)
  include the gate's pack. A row that leaves out the pack of an accepted
  mapping gate of its family is rejected.

## State

`state` reuses the existing kernel `Qualification` vocabulary and adds nothing
to it. The definition lives in the
[kernel v1 `Quality` type](kernel.md#type-quality): `candidate`,
`qualified`, `unsupported`, `unknown`, `rejected`, with the semantics stated
there. A state value keeps its meaning: `unsupported` and `rejected` forbid a
value, and `unknown` stays distinct from a known capability. An already promoted
element retains its actual candidate state, `unknown` included. A candidate
state, `unsupported` and `rejected` included, is never by itself a promotion
veto: a known SemReg element whose candidate becomes `unsupported` with no value
validates as promoted when its value-presence requirements hold, and the
separate capability and projection rules stay. This contract does not redefine
the states.

The catalog has no value for conditions such as "evidence blocked", "no
admissible profile" or "no-go". Those conditions stay `unknown` or `candidate`
and are named by `reason`. A catalog MUST NOT invent a state value. A
`qualified` row has the reason `declared_by_specification` and at least one
evidence entry of kind `specification` from the pinned native specification or
public documentation, with the declaration bound at runtime; a catalog entry,
similar concept, address or model string alone is not such evidence.

## Composition

`composition` records how the family reaches consumers through the driver that
registers it.

| Value | Meaning |
| --- | --- |
| `composed` | The family is composed through SemReg. |
| `composed_legacy` | The family is composed on a legacy layer, not through a SemReg pack. |
| `provider_local` | The native provider emits the family and no composition through SemReg is claimed. |
| `not_composed` | No composition is claimed. |

`composition_verified` is a flag, not a state:

- `module` and `version` are the composition evidence of the driver's own
  registration. Each is a string and is omitted when empty.
- Any `composition` other than `not_composed` requires
  `composition_verified=true` and both `module` and `version`.
- `composition_verified=true` requires both `module` and `version`.
- A `not_composed` row MUST have `composition_verified=false` and MUST NOT carry
  `module` or `version`: verification and composition evidence apply only to a
  claimed composition.
- `composition_verified=false` means the composition is **unverified**. It does
  not assert that the family is absent from the gateway, and `not_composed`
  with `composition_verified=false` means only that no composition is claimed.

## Verification

`verification` records the hardware-test level of the row. It is a recorded
level beside `state`; it never raises or lowers qualification, promotion or an
operation.

| Value | Meaning |
| --- | --- |
| `tested_on_hardware` | A public hardware test record exists. The row carries at least one `hardware_test_record` evidence entry. |
| `not_tested_on_hardware` | No hardware test is recorded. This holds no row below `qualified`. |

## Reason

`reason` states the basis of a row's `state`. It is a closed
vocabulary; each value has one definition, and a value never changes meaning
within v1.

| Value | Definition |
| --- | --- |
| `declared_by_specification` | The pinned native specification or public documentation declares the family's mapping, and the declaration is bound at runtime. A `qualified` row has this reason and a `specification` evidence entry. |
| `specification_conflict` | Two public sources state conflicting facts. Both are recorded as evidence. |
| `semantic_mapping_unknown` | Native receive-side evidence exists but the family's semantic mapping is not established. Source wording: "state cells remain native and opaque"; "no mapping is normative". |
| `unknown_pending_normative_source` | The family stays unknown while the dependency named `unknown_pending_normative_source` in the accepted packs is unresolved. Source wording: "remains unknown_pending_normative_source in every pack; no normative mapping or conformance claim". |
| `no_producer` | No producer, topology instance or mapping is established for the family. Source wording: "no producer, topology instance or mapping exists". |

Name correspondence (documentary only): `unknown_pending_normative_source` was
formerly spelled `unknown_pending_std_01`. The rename keeps the definition; the
old spelling is not a v1 value, and a document carrying it is rejected like any
other value outside this table.

## Evidence references

Each `evidence` entry is an object with exactly four non-empty string members.

| Member | Rule |
| --- | --- |
| `owner` | Public repository reference in one of two forms. `Project-Helianthus/<repository>@<revision>` pins an immutable revision, so the `locator` path at that revision is reproducible. `Project-Helianthus/<repository>#<number>` names an issue or pull request thread; it pins no revision and its content can change, so it is used only for kinds `issue` and `pull_request`, and the `statement` records what the thread established when cited. |
| `kind` | Evidence kind, for example `native_disposition`, `native_evidence`, `native_qualification_card`, `native_registry`, `semantic_contract`, `semreg_fixture`, `specification`, `hardware_test_record`, `certification`, `issue` or `pull_request`. Kinds are an open, additive vocabulary. |
| `locator` | Path inside the repository at the pinned revision (`@` form), or the URL of the issue or pull request (`#` form). |
| `statement` | What the cited material establishes, stated without copying restricted text and without claiming more than the source. |

A `specification` entry cites the pinned native specification or public
documentation that declares the mapping. A `hardware_test_record` entry cites a
public hardware test record in a project repository. A `certification` entry
cites a record of [certification references](certification-references-v1.md),
that is, a value a certificate states about a device. Evidence
MUST be publishable: no private material, device capture, serial, network
coordinate or credential.

## Compatibility

Within v1 only additive vocabulary values are allowed: new families, new
`reason` values, new `composition` values and new evidence kinds. From the 0.7
release on, the following require a new contract version (`v2`); until then the
in-place rule of [api/README.md](../README.md#version-rule) applies:

- a new `state` value, since `state` is the kernel `Qualification` set;
- removing or renaming any member or vocabulary value;
- adding a member to the document, a family row or an evidence entry;
- changing the meaning of an existing value or flag.

A v1 reader rejects an unknown member and an out-of-vocabulary value; a v1
reader that does not know an additively added value fails closed rather than
mapping it to a known one.

The row members `verification`, `module` and `version` and the revised `reason`
and evidence-kind vocabularies were set in place before the 0.7 release,
replacing the `gateway_composition` evidence kind and its gateway pin; no alias
and no revision bump carries the earlier form.

The family-row member `further_semantic_packs` was added in place before the
0.7 release; the [in-place change record](../README.md#in-place-change-record)
lists it. It is optional and omitted when empty, so every existing row keeps its
bytes; a reader that does not know the member rejects a row that carries it.

## Relation to packs and INT-05

The accepted capability packs
([thermal/HVAC](packs/thermal-hvac-v1.md), [storage/BMS](packs/storage-bms-v1.md),
[PV/inverter](packs/pv-inverter-v1.md), [EVSE](packs/evse-v1.md),
[infrastructure](packs/infrastructure-v1.md)) define typed vocabulary. A
family's `semantic_pack` and `further_semantic_packs` name packs; they do not
turn a candidate native row into a normative mapping, and the pack
specifications keep ownership of what a row may expose.

INT-05 acceptance requires that every existing family has a catalog row and a
correct state: insufficient evidence remains `unknown` or `candidate`, is not
excluded from scope, and is not fabricated. Accordingly a row is never silently
dropped for lack of evidence, and a state is never raised above what its
evidence references support.

## Unresolved questions

- The `reason` definitions quote the evidence statements in the fixture; the
  SemReg README lists the values without definitions, so the definitions here
  are the contract's own wording over those sources.
- The `unknown_pending_normative_source` dependency is defined by the accepted
  packs, not by this contract; this page does not restate it.
- Completeness against a family list is checked by the consumer against a list it
  pins; this contract names no list.
- The SemReg validator checks only that `owner` is non-empty; the two `owner`
  forms above are a documentation rule that the validator does not yet enforce.
- The SemReg decoder and fixture adopt the members and vocabularies revised in
  place above, the unlisted valid family and the unbounded pack list in a
  separate change.
- An accepted mapping gate names its pack but no `family_id`. How the
  cross-check of [Packs of a row](#packs-of-a-row) associates a gate with a
  family row is for the SemReg cross-check to state; this page does not decide
  it.

## Falsifiers

This contract is wrong, and a correction is required, if any of the following is
shown at a pinned revision:

- a fixture or decoder accepts a `state` outside the kernel `Qualification` set,
  or a document whose `states` member differs from it;
- a row with a claimed composition is accepted without `composition_verified=true`
  and both `module` and `version`;
- a `not_composed` row is accepted with `composition_verified=true` or with a
  `module` or `version`;
- a row is accepted whose `verification` is outside its two values, or whose
  `tested_on_hardware` has no `hardware_test_record` evidence entry;
- a `qualified` row is accepted without the reason `declared_by_specification`
  and a `specification` evidence entry, or a row is held below `qualified` for
  lack of a hardware test;
- a document with an unknown or repeated member, or trailing data, is accepted;
- a valid additional family that the consumer's list does not name is rejected,
  a missing required family is accepted, or an unknown member of a family
  object is accepted;
- a candidate state is treated as a veto of promotion, or an already promoted
  element is shown with a state other than its actual candidate state;
- a `reason` value is used with a meaning that contradicts its definition above,
  or a row's `state` is `qualified` without the owning native qualification;
- a family is dropped, or given a fabricated state, because its evidence is
  insufficient;
- a row is accepted whose `further_semantic_packs` is present but empty, repeats
  an entry, holds `semantic_pack`, is not in canonical order or follows an empty
  `semantic_pack`, or a row naming six accepted packs is rejected for its count;
- a row is accepted whose packs leave out the pack of an accepted mapping gate
  of its family.

## Validation and limits

Run `python3 scripts/validate_family_catalog_v1.py`,
`python3 scripts/test_validate_family_catalog_v1.py`, then
`./scripts/check_docs.sh`. These check that this page states the exact
vocabularies and rules of the contract; they do not read the SemReg fixture and
establish no family state, native qualification or live behavior. The
cross-check of a row's packs against accepted mapping gates is not run here; it
belongs to the SemReg validator, which reads the fixture.
