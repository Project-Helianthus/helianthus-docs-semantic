---
status: "normative companion to [kernel.md](kernel.md) for `helianthus.semantic.kernel/v1` when merged into `main`"
---

# Semantic resource graph, planes and lenses

Status: normative companion to [kernel.md](kernel.md) for
`helianthus.semantic.kernel/v1` when merged into `main`

The graph acceptance vectors (`api/v1/graph-acceptance-vectors.json`) and the
element catalog files named in sections 1, 10 and 19 are added in place by
later changes of the same release cycle.

Contract: part of `helianthus.semantic.kernel/v1`, published as the companion
page `api/v1/graph.md`. The element catalog document is
`helianthus.semantic.element-catalog/v1`; the graph acceptance document is
`helianthus.semantic.graph.acceptance/v1`.

Owning Go module: `github.com/Project-Helianthus/helianthus-semreg`. The new
kernel records live in `semreg/v1`; the element catalog, planes, lenses and
graph cuts live in a new package `semreg/v1/graph`.

Increment boundary. This page is increment 1: resource identity, relations,
plane membership, lens definitions, the element catalog, activation,
publication and coherence. Increment 2 adds bounded retrieval and traversal,
lens retrieval, target reports over a named lens, consumer identity and API
and Portal consumption. A sentence marked *Increment 2* names a decision this
page deliberately leaves open.

## 1. Conformance language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD` and `MAY` have the meaning given in
the [kernel contract](kernel.md). An implementation conforms to this page only
when every positive and negative vector of `graph-acceptance-vectors.json`
passes with
the element catalog registered, and every kernel vector of
`acceptance-vectors.json` passes without it (section 5). Validation is
fail-closed and atomic: a rejected batch, catalog or registry changes no
published state.

Every rule carries a **Check** line that names the validator, test or vector
that decides it, and who runs it: the kernel (semreg), the catalog validator
(docs-semantic), a gate validator, or the gateway's conformance tests.

## 2. Problem, constraints and current behaviour

**Problem.** The kernel publishes one snapshot per asset. Zones, circuits,
inverter inputs, phases, meters, connectors and cells exist only as text in a
fact-key dimension. The 21 accepted pack relationship definitions have no
instance record. No plane, lens or element catalog exists. Drivers, the gateway
and consumers therefore build their own groupings, identity tables and joins,
and a target projection report is mistaken for an internal view.

**Constraints.**

1. From the scope of docs-semantic#67: a protocol-neutral resource graph with
   canonical identity and typed relation instances; a plane is a view over that
   one graph and a lens a bounded combination of views; the same resource and
   element keep their identity across views; a plane owns no second truth and
   no command authority.
2. Capability pack, plane and lens membership, and target projection are three
   separate concepts with three owners (section 4).
3. No contract or pack revision is raised before the 0.7 release; every change
   is an in-place edit of v1 (section 17).
4. Every mappable capability goes through SemReg, with no compatibility-only
   path. The gateway owns stable opaque asset, source and binding identifiers
   and the native registries own qualification; section 6.3 extends this to
   resources.
5. The admission rule (docs-semantic#68) applies in full to every new concept
   (section 10.5).
6. Native evidence stays native. Appearing in a plane neither promotes a fact
   nor authorizes an operation. The core contract names no vendor, and
   family-specific questions stay with their native owners (section 15).

**Current behaviour kept.** Per-asset atomic publication, immutable snapshots
with content-derived identifiers, the quality axes, identity links with
evidence, generation fences, tombstones, the derivation graph, pure evaluation
and selection, and the operation admission chain.

## 3. Definitions

- **Resource**: an identifiable thing of the installation with its own
  lifecycle that facts, services, capabilities and relations can be about:
  a piece of equipment, a component, a function of the installation, or a
  bounded episode. Identified by a `ResourceID`.
- **Resource kind**: the catalog element that says what a resource is (for
  example `resource.inverter`, `resource.zone`). Owned by the core contract,
  never by a pack.
- **Home asset**: the one asset whose snapshots hold a resource record and
  everything published about that resource (section 11.1).
- **Anchor** and **anchor key**: the declared basis of a resource's identity,
  and the part of it that two records are compared on (section 6.3).
- **Subject**: the resource a fact, service or capability is about.
- **Resource dimension**: a fact-key dimension whose value is the `ResourceID`
  of the subject. **Qualifier dimension**: any other dimension (a role, a
  period, a quantity kind).
- **Core relation type**: one of the seven typed meanings of section 7.1. Not
  instantiable by itself.
- **Relation definition**: a catalog element that specializes one core
  relation type between declared resource kinds. Owned by a pack or by the
  core. Its **starting end** is its own `from`, whatever the core type's
  reading.
- **Relation instance**: a published, typed, directed link between two
  resources under one relation definition, with state, evidence and provenance.
- **Absence statement**: a published, evidenced statement that a resource has
  no relation of a given definition on a given side.
- **Plane**: a view over the one graph, defined by the relation definitions and
  elements the catalog makes members of it.
- **Plane membership**: the planes a catalog element belongs to, declared once
  per definition in the element catalog.
- **Lens**: a named, bounded combination of planes, root kinds and relation
  definitions that answers one question.
- **Element** and **element catalog**: an entry of, and the machine-checked
  inventory of, ownership, admission, plane membership and catalog disposition.
- **Catalog disposition**: `member`, `unsupported` or `unknown` (section 10.3).
  It is not a target projection outcome.
- **Graph-enforced registry**: a kernel registry constructed with the element
  catalog (section 5).
- **Graph cut**: a set of per-asset snapshots read together, at most one per
  asset, in which relation coherence is evaluated (section 11.3).

Reserved terms. Within the semantic API (docs-semantic, semreg, semantic MCP
and GraphQL types, Portal core navigation) *resource*, *relation*, *plane*,
*lens*, *element catalog* and *graph cut* have only the meanings above. Named
exceptions that keep their word with a qualifier: the kernel's `Readback.relation`
and `ReadbackRelation` ("readback relation"); the kernel's
`NativeBinding.native_resource` ("native resource"); the Portal catalog's
`resource_id` until the Portal is re-based on `ResourceID` (*Increment 2*;
"Portal resource key"); the native eBUS registry terms of the
`ebus_v1_registry_*` tools, the eBUS device GraphQL types and the Portal
registry routes ("registry plane", "registry projection"); the eeBUS
`TopologyV1` record ("SPINE topology"). Each exception is listed in the
glossary. No alias is created.

## 4. Three distinct concepts

| | Capability pack | Plane and lens membership | Target projection |
|---|---|---|---|
| Question | What does this fact, service, capability or operation mean? | In which view is this element visible and navigable? | How does one target represent it, and what is lost? |
| Owner | The pack contract (docs-semantic, semreg) | The element catalog (docs-semantic, semreg) | The output binding of one target and version |
| Record | `DefinitionRef` in the pack index | Catalog entry `planes` | `ProjectionReport` |
| Loss | None | None | Declared per item |
| Instance | Facts, services, capabilities, operations | Derived; never published | Target objects |

A pack never declares plane membership. A catalog entry never redefines a pack
definition. A target report never decides membership and never serves as an
internal disposition.

## 5. Activation and transition

The graph rules are a property of the kernel registry, so that they cannot be
skipped by accident or on purpose without it being visible.

- **ACT-1** A kernel registry constructed with the element catalog is
  graph-enforced. It accepts only the catalog whose SHA-256 equals the digest
  pinned in semreg's fixture, and exposes that digest for the release BOM. At
  construction it requires that the catalog covers every registered `PackRef`
  completely (CAT-1 for that pack). The root package receives the catalog
  through an interface it defines itself and never imports `semreg/v1/graph`,
  so no import cycle arises. Check: construction with a registered pack the
  catalog does not cover, or with another catalog, fails with
  `membership_missing` (vectors).
- **ACT-2** A registry constructed without the catalog behaves exactly as
  before, and rejects every graph member: resources, relation instances,
  absence statements, the `resource` and `key` members of identity links, and
  the `resource` member of service instances. Graph records therefore exist
  only under enforcement. Check: a batch with a resource upsert to a
  non-enforced kernel is rejected with `membership_missing` (vector).
- **ACT-3** Under enforcement every rule of sections 6 to 13 applies to every
  batch of that kernel's asset. Check: graph vectors.
- **ACT-4** At construction of a graph-enforced registry, every operation and
  effect rule whose catalog disposition is not `member` is registered as
  inadmissible. Admission reads only the registry's own index: an intent for an
  inadmissible operation is rejected with `membership_missing`. Admission
  never reads a graph record (AUT-1). Check: vector; neither the operation
  package nor any package it imports, directly or indirectly, imports
  `semreg/v1/graph`.
- **ACT-5** Cut assembly (section 11.3) reports as `ungraphed` an asset whose
  snapshot holds a fact of a definition with catalog disposition `member` but
  no graph record; it contributes nothing to any plane. Facts of `unknown`
  definitions do not count, so an enforced asset that publishes only such
  facts is not reported. Check: cut vectors G-POS-CUT-5 and G-POS-CUT-10.

Transition, in this order:

1. The kernel vectors run without the catalog and do not change. Some use
   synthetic definitions under a real `PackRef`; the catalog does not list
   them, so they could not run graph-enforced, and they need not.
2. The graph vectors run with the catalog.
3. The gateway keeps constructing its kernels without the catalog after the
   semreg dependency update, so today's publishers and their text dimension
   values keep working.
4. ebusgateway#1539 switches enforcement on per device family as it migrates
   that family's publishers. Until then the family's assets are reported
   `ungraphed`.
5. Whether every composed family must be graph-enforced at INT-16, and whether
   a family may be switched on while publishing less, is the project owner's
   release decision. This contract only makes the state of each family visible.

Switching a family on changes what it may publish. Services, capabilities and
resources of `unknown` disposition are refused. For the thermal family as
seeded, that means the circuit, hot-water and ventilation services and their
read capabilities, which the gateway already maps today. Its
qualifier-keyed facts stay publishable but are in no plane.

## 6. Resources and identity

### Type: ResourceID

`ResourceID` is a new distinct alias of `OpaqueID`. String equality with an
`AssetID`, `ServiceInstanceID` or dimension text never makes them the same
identity.

### Type: Resource

```go
type Resource struct {
    ResourceID ResourceID          `json:"resource_id"`
    Kind       DefinitionID        `json:"kind"`
    Anchor     ResourceAnchor      `json:"anchor"`
    Supersedes *AnchorSupersession `json:"supersedes,omitempty"`
    State      ResourceState       `json:"state"`
    Origin     OriginRef           `json:"origin"`
    Revision   Uint64              `json:"revision"`
}

type ResourceAnchor struct {
    Class    AnchorClass   `json:"class"`
    Basis    AnchorBasis   `json:"basis"`
    Key      *Digest       `json:"key,omitempty"`
    Parent   *ResourceID   `json:"parent,omitempty"`
    Slot     *string       `json:"slot,omitempty"`
    Evidence []EvidenceRef `json:"evidence"`
}

type AnchorSupersession struct {
    Previous ResourceAnchor `json:"previous"`
    Evidence []EvidenceRef  `json:"evidence"`
}
```

`ResourceState` is `current`, `withdrawn` or `retired`. `AnchorClass` is
`equipment`, `component`, `function` or `episode`. `AnchorBasis` is
`native_identity`, `native_slot` or `operator_slot`. `Slot` is NFC text of 1
through 128 bytes without control characters. `Evidence` holds 1 through 32
unique references. `Revision` is greater than zero and increments whenever any
other member changes.

`Key` is present exactly when the basis is `native_identity`. It is
`sha256:` over the JCS bytes of the identity object
`{scheme, issuer, token}`:

- `scheme` names an identification scheme from the catalog's list (section
  6.3). It names who assigns the token, never the protocol that carries it.
- `issuer` is a code from the public registry that scheme names (for example a
  manufacturer code), or empty when the scheme is globally unique. It is a
  code, never a name.
- `token` is the token in the scheme's canonical form.

The gateway computes the key; the token itself stays native evidence.

The **anchor key** of a resource is `(kind, key)` for `native_identity` and
`(kind, parent, slot)` otherwise.

### 6.1 Granularity

A resource is created for every value of a resource dimension and for every
piece of equipment a relation needs as an endpoint, even when no pack fact is
about it (a logger, a controller, a hub). A qualifier dimension never creates
a resource.

| Anchor class | What it is | Identity follows | Examples (kinds) |
|---|---|---|---|
| `equipment` | A replaceable physical unit | the hardware | inverter, battery pack, meter, charging station, generic equipment |
| `component` | A fixed part of a parent (equipment or function) | the parent and a position | inverter input, phase, connector, battery cell, PV string |
| `function` | A role of the installation | a configuration slot | zone, thermal circuit, PV system, site, grid connection |
| `episode` | A bounded activity | a native episode token in its parent | charging session |

One kind is not one resource. A phase is a component of its container (an
inverter output, an electrical circuit, a connector); the phases of different
containers are different resources, linked where evidence allows by an
electrical `supplies` instance. Equipment whose kind is not yet admitted uses
the core kind `resource.equipment`.

### 6.2 Subject of facts, services and capabilities

Every fact definition of a catalog-covered pack declares exactly one resource
dimension. In a graph-enforced kernel, the value of that dimension in a
`FactKey` is the `ResourceID` of the subject. Other dimensions of the key are
qualifier dimensions declared by the field. A fact definition whose only
dimension is a qualifier has an unresolved subject and catalog disposition
`unknown` until its pack declares the resource dimension in place.

`ServiceInstance` gains an optional member `resource`. In a graph-enforced
kernel a service instance of a catalog-covered pack carries it, naming a
current resource of the kind the catalog declares for the service. A capability
instance's subject is the subject of its service instance.

### 6.3 Allocation, identification schemes and what can be detected

The gateway allocates every `ResourceID`, as it allocates asset, source and
binding identifiers. Until now a publisher or a gate chose sub-asset identity
as dimension text in five different grammars; that text now carries a
gateway-allocated `ResourceID`, so one thing has one identifier in every pack,
plane, lens and target.

Identification schemes are listed in the element catalog
(`identification_schemes`). docs-semantic owns the list. A native owner
proposes an entry with public evidence of the scheme and its issuer registry,
and documents how its native tokens map to a listed scheme and canonical form.
Two native owners that observe one unit through two protocols map its token to
the same scheme, issuer and token, so the keys match. Two units of different
manufacturers with the same serial text differ by issuer, so they do not
collide. Until a scheme is listed for a family, its equipment uses an
`operator_slot` anchor, and section 6.5 later upgrades it without a new
identifier.

Never an anchor, and never a resource dimension: a bus or network address, a
routed unit number, an entity address path, a credential or certificate
fingerprint, a pack class, a profile identifier or other native interpretation
selector, a display name, or an index that is not local to the parent. A
native interpretation selector is provenance. Its native owner decides whether
a given selector is identity evidence, provenance or a resource attribute.

Each identity event, with who checks it:

| Event | Expected identifier | Check | Vector |
|---|---|---|---|
| Driver restart, new source epoch or generation | same | kernel: a binding change never rewrites a resource (RES-3) | G-POS-ID-1, GW-ID-1 |
| Re-addressing on the bus or network | same | gate validator: the anchor source is `native_token`, `native_position` or `operator_label`, never an address | GW-ID-2 |
| Credential or certificate rotation | same | gate validator: a credential is never an anchor source | GW-ID-3 |
| Equipment replaced by another unit | new for the equipment and its components; same for functions; an episode ends | kernel: a different anchor key never reuses a `ResourceID` except by supersession (RES-3, RES-4) | G-NEG-ID-2, GW-ID-4 |
| Operator renames a configuration slot | new for the function unless the operator maps the old slot by supersession | gateway allocator; kernel RES-9 | GW-ID-5 |
| Anchor upgraded: operator label or native slot replaced by a qualified native token | same | kernel RES-9; gateway allocator | G-POS-ID-2, G-NEG-ID-6, G-NEG-ID-7, GW-ID-7 |
| Native owner revises the canonical token form | same | kernel RES-9; the native owner's documented mapping is the evidence | G-POS-ID-2, GW-ID-7 |
| Two units of different manufacturers with equal serial text | different | kernel: the keys differ by issuer | G-POS-ID-3 |
| One unit observed through two paths | one resource when its home asset holds both paths; otherwise two resources flagged `same_unit` when they share an anchor key | kernel within an asset (RES-4); cut assembly across assets (section 11.3) | G-NEG-ID-1, G-POS-CUT-4, G-POS-CUT-8, GW-ID-6 |

The GW-ID vectors belong to the gateway's conformance tests for
ebusgateway#1539 and run again at INT-17.

What can be detected:

- The kernel detects, in one asset: a changed kind; an anchor change without
  valid supersession; a reused retired `ResourceID`; and two current resources
  with one anchor key.
- Cut assembly detects, across assets: one `ResourceID` current in two
  members, and two current resources with one anchor key in two members,
  whether native or slot.

What cannot be detected: two observations whose anchors share no key, such as
a battery relayed by an inverter that exposes no battery token next to the
same battery's own feed, or two protocol views of one zone hung under
different parents. Such pairs stay two unflagged resources, and their facts
can be added up twice, unless an operator declaration gives them a common key
(section 6.4) or one asset holds both paths. Nor can anything detect a token
that is not truly stable; its native owner answers that in its documentation,
and the gate validator checks that the gate states it.

### 6.4 One unit seen through two paths

A unit seen directly and also relayed by another unit (a controller, a logger,
an inverter, a hub) is one resource when both observations carry the same
anchor key, or when an operator declaration says so (section 6.6). Its home
asset then holds both source paths, each a binding with an identity link that
names the resource.

`IdentityLink` gains two optional members. `resource` states that the link's
binding observes that resource; a link without it keeps its present
asset-level meaning. `key` is the identity-object digest of the unit's native
token as seen through this binding, computed as for an anchor; it is present
when the binding's source exposes such a token.

An asset may hold several sources: the kernel allows it. The gateway
publication hub refuses a second source for one asset today. When the two
paths belong to sources homed in two different assets, the observations stay
two resources. Cut assembly flags the pair `same_unit` when they share an
anchor key, native or slot. A reader MUST NOT add up facts of a `same_unit`
pair. Merging them needs an asset that accepts several sources. The gateway
adds assets with several sources in the 0.7 release cycle; this contract is
the same either way.

An operator declares a cross-asset pair by giving both resources one anchor
key: the same `operator_slot` (for equipment), or the same declared parent and
slot (for components and functions; for example, both protocol views of one
zone parented to one operator-declared thermal system with the same slot).
Cut assembly then flags the pair. Without a shared key the pair is not
detectable (section 6.3).

### 6.5 Anchor supersession

A resource keeps its `ResourceID` when its anchor is upgraded. The publishing
upsert carries `supersedes`, which holds the exact previous anchor and the
continuity evidence. Allowed upgrades:

- `operator_slot` → `native_slot` or `native_identity`;
- `native_slot` → `native_identity`;
- `native_identity` → `native_identity` with the same scheme and issuer, when
  the native owner revises the canonical token form.

The gateway allocator asserts a supersession. Continuity evidence is one of:

- a current binding of the home asset that observes the unit under both
  anchors;
- the native owner's documented mapping from the old token form to the new;
- for an `operator_slot` previous anchor only, an operator declaration with
  audit evidence.

A downgrade (native to operator or slot), a change of kind or class, or an
upgrade whose new anchor key is already held by another current resource is
never a supersession. `supersedes` stays in the record until the next anchor
change; prior snapshots keep the history.

### 6.6 Operator declarations

An operator declaration is an accepted identity basis in three forms: an
`operator_slot` anchor (including one shared by two resources to declare a
cross-asset pair, section 6.4), an identity link whose basis is operator
configuration, or the continuity evidence of a supersession from an
`operator_slot`. Each carries the authority and audit evidence the kernel
requires for operator origins. It differs from the operator-typed shared asset
identifier that the audit flagged in five ways:

1. It is recorded as a typed basis that every consumer sees.
2. It names one resource, not a whole asset.
3. It carries audit evidence.
4. It is never counted as native qualification; a later native token replaces
   it only through supersession (section 6.5).
5. It cannot override native evidence: a declaration that joins two
   observations whose native anchor keys differ is rejected.

### 6.7 Resource lifecycle

A resource is an identity record, not an observation. Generation fences and
source retirements do not change it. A publisher withdraws a resource
explicitly (`withdrawn`, reversible to `current` with a new revision) or
retires it (`retired`, irreversible). Whether a current resource is presently
observed is computed by evaluation from its current bindings.

### 6.8 Rules

- **RES-1** Every published resource has a kind whose catalog entry is a
  `resource_kind` with disposition `member`. Check: `membership_missing`.
- **RES-2** The anchor class equals the class the catalog declares for the
  kind. `component` and `episode` anchors carry `parent` and `slot`.
  `function` anchors carry `slot` and, unless the function is a root of the
  installation, `parent`. `equipment` anchors carry `key` when the basis is
  `native_identity` and `slot` when it is `operator_slot`. Basis
  `native_identity` or `native_slot` requires origin kind `native_observation`;
  `operator_slot` requires origin kind `operator`. A `key` names a scheme listed
  in the catalog. Check: `invalid_value`.
- **RES-3** The kind of a `ResourceID` never changes, and its anchor key
  changes only by a supersession that satisfies RES-9. Check: `identity_drift`
  (G-NEG-ID-2).
- **RES-4** In one snapshot, two current resources never share an anchor key,
  and a retired `ResourceID` is never current again. Check:
  `duplicate_identity` (G-NEG-ID-1, G-NEG-ID-3).
- **RES-5** A resource dimension value resolves to a current resource of the
  dimension's declared kind in the same snapshot. Check: absent is
  `dangling_reference`; another kind is `identity_drift`.
- **RES-6** An observed fact whose subject is resource R comes from a binding
  with a non-withdrawn identity link naming R, or naming R's anchor parent
  chain up to an `equipment` or `function` resource. A promoted fact requires
  that link to be `qualified`. Check: `identity_not_qualified`.
- **RES-7** An identity link that names a resource anchored on
  `native_identity` and carries `key` must carry that resource's anchor key.
  An operator declaration therefore cannot join a binding whose native token
  differs. Check: `identity_not_qualified` (G-NEG-ID-4).
- **RES-8** Withdrawing or retiring a resource requires that no current fact,
  service, capability, relation instance or absence statement in the snapshot
  still names it. Check: `dangling_reference`.
- **RES-9** A supersession names exactly the anchor of the previous revision,
  is one of the allowed upgrades of section 6.5, carries non-empty continuity
  evidence of an allowed kind, and leads to an anchor key no other current
  resource of the snapshot holds. Check: a missing or wrong `previous`, a
  downgrade or an empty evidence list is `identity_drift` (G-NEG-ID-6,
  G-NEG-ID-7); a new key already held is `duplicate_identity`.

## 7. Relations

### 7.1 Core relation types

| Type | `from` → `to` reads | Structure | Allowed planes | Required plane |
|---|---|---|---|---|
| `contains` | whole contains part | forest | physical, energy, hydraulic, diagnostic | physical |
| `groups` | group has member | acyclic | physical, energy, hydraulic, control | none |
| `supplies` | upstream delivers a medium to downstream; the nominal direction is the sign reference | graph | energy, hydraulic | none |
| `measures` | measuring resource measures the measured resource | graph | energy, hydraulic, diagnostic | none |
| `controls` | controlling resource regulates or commands the controlled resource | graph | control | control |
| `hosts` | resource hosts an episode | forest | energy, control, diagnostic | none |
| `relays` | resource relays the data of another resource | acyclic | provenance, diagnostic | provenance |

"Forest" means each resource is the `to` of at most one instance of that core
type, across all its definitions, and no cycle exists. "Acyclic" forbids
cycles across all definitions of that core type. A `supplies` definition
declares its medium: `electrical` and `air` give energy; `heat_transfer_fluid`
and `refrigerant` give hydraulic and energy.

### 7.2 Relation definitions

A relation definition declares its core type, its orientation (`as_core`, or
`inverse` when its `from` and `to` read the core type backwards), its `from`
and `to` kinds, cardinality (`one_to_one`, `one_to_many`, `many_to_many`,
optionally over time), the medium for `supplies`, the basis classes it admits,
and its plane membership.

- A definition whose two endpoint kinds are both reached through the
  dimensions of one pack is owned by that pack. This covers the 21 accepted
  definitions.
- A definition that connects kinds of different packs, or uses
  `resource.equipment`, is owned by the core catalog. A pack never owns a
  relation that crosses packs, so the `cross_pack_relation` negative of
  [pack metadata](pack-metadata-v1.md) stays valid.

Basis classes (`RelationBasis`):

| Class | Meaning | Origin kind |
|---|---|---|
| `native_observation` | A native owner documents the relation as observable for a stated scope, and a current binding observed it. | `native_observation` |
| `configuration` | The operator or installer declared it. | `operator` |
| `gate_rule` | A reviewed mapping gate derives it from observed native structure. | `native_observation` |

Which classes a definition admits follows the native owners' evidence, not
this contract. `native_observation` is admitted only when a native owner
documents the relation as observable. `configuration` is admitted when no
native owner does. The question each native owner answers is in section 15.
Similarity of values or names, ordinal position and address arithmetic are
never a basis.

### Type: RelationInstance

```go
type RelationInstance struct {
    Definition DefinitionRef `json:"definition"`
    From       ResourceID    `json:"from"`
    To         ResourceID    `json:"to"`
    State      LinkState     `json:"state"`
    BasisClass RelationBasis `json:"basis_class"`
    Basis      []EvidenceRef `json:"basis"`
    Origin     OriginRef     `json:"origin"`
    Revision   Uint64        `json:"revision"`
}

type RelationKey struct {
    Definition DefinitionRef `json:"definition"`
    From       ResourceID    `json:"from"`
    To         ResourceID    `json:"to"`
}
```

The key is `(definition, from, to)`; one key has at most one instance. A
publisher upserts `candidate`, `qualified` or `rejected`. `rejected` records
evidence that this pair is not related. `conflict` is derived by the kernel
(REL-6); a publisher-supplied `conflict` is `invalid_value`. Withdrawal removes
the instance from the current snapshot; prior snapshots keep its history.
`Basis` holds 1 through 32 unique references.

### Type: RelationAbsence

```go
type RelationAbsence struct {
    Definition DefinitionRef `json:"definition"`
    Resource   ResourceID    `json:"resource"`
    Side       AbsenceSide   `json:"side"`
    State      LinkState     `json:"state"`
    BasisClass RelationBasis `json:"basis_class"`
    Basis      []EvidenceRef `json:"basis"`
    Origin     OriginRef     `json:"origin"`
    Revision   Uint64        `json:"revision"`
}
```

`AbsenceSide` is `from` or `to`. The key is `(definition, resource, side)`.
`State` is `candidate` or `qualified`. The statement means "this resource has
no relation of this definition on this side". When neither an instance nor an
absence statement exists, the relation is unknown, never "none".

### 7.3 Rules

- **REL-1** Every published instance and absence statement names a relation
  definition whose catalog disposition is `member`. Check:
  `membership_missing`.
- **REL-2** The instance's `from` (the definition's starting end) is a current
  resource homed in the publishing asset and of an admitted kind. For an
  absence statement the same holds for `resource`. Check: absent is
  `dangling_reference`; wrong kind is `identity_drift`.
- **REL-3** `basis_class` is admitted by the definition and agrees with the
  origin kind; `basis` is non-empty. Check: `relation_not_qualified`.
- **REL-4** An instance whose `to` is homed in the same asset requires that
  resource to be current and of an admitted kind. Check: withdrawn or retired
  is `stale_relation`; absent is `dangling_reference`; wrong kind is
  `identity_drift`.
- **REL-5** An instance or absence statement with a `native_observation` or
  `gate_rule` basis dies with its binding generation: an accepted fence or
  source retirement removes it in the same atomic snapshot. A `configuration`
  instance is removed only by explicit withdrawal. Check: vector.
- **REL-6** Within one snapshot, after every batch, the kernel sets to
  `conflict` every qualified instance that takes part in:
  - a cardinality violation of its definition;
  - a forest violation of its core type across definitions;
  - a cycle of `contains`, `groups`, `hosts` or `relays` across definitions.
  It never chooses one instance. Check: vectors G-POS-REL-2 (two `contains`
  definitions claiming one part) and G-POS-REL-3 (a `relays` cycle).
- **REL-7** An instance and an absence statement for the same definition,
  resource and side are never both current in one snapshot. Check:
  `invalid_value`.
- **REL-8** Endpoints are typed `ResourceID` values; a dimension text, an
  asset identifier or a plane-scoped identifier can never be an endpoint.
  Check: any other member is `unknown_member`.

## 8. Planes

### 8.1 The planes

| Plane | Question it answers | Relation core types | Element members |
|---|---|---|---|
| `physical` | What exists and what is part of what? | `contains`, `groups` | equipment and component kinds |
| `energy` | How does electrical and thermal energy flow, and where is it measured? | `supplies` (energy media), `measures`, `contains`, `groups`, `hosts` | energy quantities, counters, limits |
| `hydraulic` | How do heat-transfer fluids, including refrigerant, circulate? | `supplies` (fluid media), `contains`, `groups`, `measures` | fluid quantities and fluid-circuit kinds |
| `control` | Who regulates or commands what, and which operations exist? | `controls`, `groups`, `hosts` | modes, setpoints, limits, capabilities, operations, operation states |
| `diagnostic` | Where are faults, alarms and health reported and localized? | `contains`, `measures`, `relays`, `hosts` | status, fault and alarm facts, quality and coherence states |
| `provenance` | Where does information come from? | `relays`, and the kernel lineage records (source, binding, identity link, derivation) | evidence and lifecycle states |

These are the six views docs-semantic#67 names. Reconciliation:

- **Electrical** is the energy plane restricted to the electrical medium; a
  lens expresses it.
- **Refrigerant** is part of the hydraulic plane with medium `refrigerant`;
  refrigerant resource kinds still need admission.
- **Communication** (data paths of loggers, controllers and hubs) is the
  `relays` part of the provenance plane.
- **Spatial** (rooms, areas) has no basis in the accepted public contract and
  is not defined.

A seventh plane needs the admission rule and relation definitions whose
navigation no lens over the existing planes can express.

### 8.2 Membership rules

- **PLN-1** Membership is declared per definition, once, in the element
  catalog. No driver, gateway, API, Portal or consumer assigns membership, and
  no published record carries a plane member. Check: the records have no plane
  member; any is `unknown_member`.
- **PLN-2** An instance of a fact, service or capability is in plane P when its
  definition is a member of P and its subject is current. A relation instance
  is in P when its definition is a member of P, its state is `qualified` and it
  is `coherent` in the cut. Candidate, rejected and conflicting instances are
  visible with their state but are in no plane. Check: cut vectors.
- **PLN-3** A resource instance is in plane P exactly when P is one of its
  kind's catalog planes and one of these holds:
  - P is physical and its anchor class is `equipment` or `component`;
  - it is the subject of a current fact, service or capability instance in P;
  - it is an endpoint of a relation instance in P.

  The kind's catalog planes only bound where its instances may appear. A
  generic equipment resource that only relays data is therefore not in energy
  just because another equipment resource is. Check: G-POS-PLN-1.
- **PLN-4** An element may be a member of several planes. No plane is primary,
  and identity is not anchored in any plane. Check: catalog vectors with
  multiple membership.
- **PLN-5** Closure: a relation definition in P requires both endpoint kinds to
  admit P; a fact, service or capability in P requires its subject kind to
  admit P; an effect rule has exactly the planes of its operation; a resource
  dimension has exactly the planes of its kind. Check: catalog validator,
  `membership_missing`.
- **PLN-6** A relation definition's planes are a non-empty subset of the
  allowed planes of its core type and include the required plane. Check:
  catalog validator, `membership_missing`.
- **PLN-7** An element with disposition `unknown` or `unsupported` is in no
  plane. Instances of an `unsupported` element MUST NOT be published. Facts of
  an `unknown` fact definition MAY be published as kernel records but are in no
  plane. A resource kind, relation definition, service or capability with
  disposition `unknown` cannot be instantiated in a graph-enforced kernel; an
  operation with such a disposition is inadmissible (ACT-4). Check:
  `membership_missing`.

## 9. Lenses

A lens is a catalog object with: a `DefinitionID`; a one-sentence question;
one through six planes; one or more root kinds that admit at least one of its
planes; an optional subset of the relation definitions of those planes; and a
maximum traversal depth from 1 through 32. A lens creates no identity, fact,
relation or membership; it selects from the graph. Increment 1 defines the
shape and seeds no lens; *Increment 2* defines lens retrieval and seeds.

- **LNS-1** Every plane, root kind and relation definition a lens names exists
  in the catalog with disposition `member`, and each named relation definition
  is a member of at least one lens plane. Check: catalog validator,
  `membership_missing`.

## 10. Element catalog

### 10.1 Document and its checks

The catalog is `api/v1/element-catalog-v1.json`, constrained by
`api/v1/element-catalog-v1.schema.json` and validated by
`scripts/validate_element_catalog_v1.py`. The schema uses conditionals
(`if`/`then`/`else`, `allOf`, `anyOf`, `not`), `uniqueItems`, `maxLength`,
`integer` and `boolean`. The repository's dependency-free schema checker does
not support these, so the wave adds a schema checker module that does, with
one negative test per conditional. The catalog validator runs the schema
through that module and enforces the cross-entry rules in code. semreg copies
the catalog byte for byte into `fixtures/v1/`, pins its SHA-256 (ACT-1) and
loads it into the `semreg/v1/graph` registry.

Besides planes, core relation types, elements and lenses, the catalog holds
the list of identification schemes (section 6.3). Each scheme has:

- an identifier;
- the public registry that issues its `issuer` codes, or none when the scheme
  is globally unique;
- the canonical token form;
- an admission record with public evidence of the scheme.

docs-semantic owns the list; native owners propose entries. A scheme names an
issuing registry, never a manufacturer. The seed list is empty: schemes enter
with the native hand-offs, and until then equipment anchors on
`operator_slot`.

### 10.2 Element kinds

| Element kind | Owner | Kind-specific attributes |
|---|---|---|
| `resource_kind` | core | anchor class |
| `relation` | pack or core | core type, orientation, endpoint kinds, cardinality, medium, basis classes |
| `dimension` | pack | role (`resource` or `qualifier`), resource kind |
| `service` | pack | fact-key dimension, subject kind |
| `fact` | pack | subject, aggregation, value kind, direction and sign reference |
| `capability` | pack | service, operation |
| `operation` | pack | capability, argument, effect rule |
| `effect_rule` | pack | operation, fact |
| `evidence_state` | core (kernel) | kernel type and values |
| `lifecycle_state` | core (kernel) | kernel type and values |
| `presentation` | pack or core | target |

Every entry, every plane and every core relation type carries an admission
record (section 10.5). Units and symbols are the value vocabulary of their
field and are accounted through the field's entry.

Kernel state types:

- `evidence_state`: `OriginKind`, `AssertionKind`, `Qualification`,
  `Promotion`, `Validity`, `Freshness`, `EvidenceAccess`, `RedactionState`,
  `ConflictKind`, `AnchorClass`, `AnchorBasis`, `RelationBasis`.
- `lifecycle_state`: `SourceState`, `BindingState`, `LinkState`,
  `Availability`, `RetainedRemoval`, `ConflictState`, `ResourceState`,
  `RelationCoherence`, `CutFindingKind`, `Outcome`, `DeliveryState`,
  `AckState`, `ReadbackRelation`.
- `presentation`, disposition `unsupported`, as target vocabulary: `ItemKind`,
  `LossKind`, `ProjectionOutcome`.

An entry is keyed by its exact `DefinitionRef` (pack-owned; a pack qualifier
dimension takes its pack's version) or by its core `DefinitionID` with the
kernel contract version (core-owned). Native extension entries are keyed in a
`native.` namespace (section 10.6).

### 10.3 Catalog dispositions

| Disposition | Meaning | Required |
|---|---|---|
| `member` | The element is in one or more planes. | non-empty `planes` |
| `unsupported` | The element is outside the semantic graph by definition. | final `reason`, empty `planes` |
| `unknown` | Membership or subject is not yet established. | `reason`, `tracking` issue, empty `planes` |

These values are separate from `ProjectionOutcome`; `withheld` or
`unrepresentable` is never a catalog disposition.

### 10.4 Mechanical validation

- **CAT-1 Completeness.** Every `DefinitionRef` in the accepted pack vectors and
  the storage contract tables has exactly one entry. That covers fields,
  dimensions referenced by fields, services, relation definitions,
  capabilities, operations, effect rules and Portal contributions. The catalog
  also lists every kernel state type of section 10.2, and no pack reference is
  extra. Check: the validator derives the reference set from the pack vectors;
  a missing entry is `membership_missing`, an extra one
  `definition_owner_missing`.
- **CAT-2 Agreement.** Where the catalog repeats a fact of pack metadata or of a
  `DefinitionIndex`, it is equal. Check: cross-validation against
  `pack-metadata-v1.json`; `invalid_value`.
- **CAT-3 Dispositions.** Section 10.3 holds for every entry. Check: schema
  module plus validator; `membership_missing`.
- **CAT-4 Closure and core types.** PLN-5, PLN-6 and LNS-1 hold, and plane and
  core-type identifiers are unique. Check: validator.
- **CAT-5 Ownership.** A pack-owned relation definition stays inside its pack;
  a crossing definition is core-owned. Check: `definition_owner_conflict`.
- **CAT-6 Admission.** Every entry, plane and core relation type carries an
  admission record whose arm is allowed for it (section 10.5). The arm
  `accepted_pack` is allowed only for references listed in the frozen seed
  reference file `scripts/element-catalog-seed-refs.json`. Check: schema
  module plus validator.
- **CAT-7 Sign reference.** A fact with direction `signed` names a `supplies`
  relation definition as its sign reference. `native_convention` is allowed
  only for seed entries whose pack keeps the native sign convention. Check:
  validator.
- **CAT-8 Canonical order.** Entries are sorted by owner, pack identifier,
  pack version, element identifier and element version. Check:
  `noncanonical_order`.
- **CAT-9 Identification schemes.** Scheme identifiers are unique, each scheme
  carries an admission record, and every scheme that a gate references is
  listed. Check: validator; RES-2 in the kernel.

### 10.5 Change rule and admission

Before the 0.7 release a catalog change is an in-place pull request to
docs-semantic that passes CAT-1 to CAT-9 and lists every added, removed or
changed entry. An element leaves the catalog only when its pack definition is
removed in the same reviewed change; otherwise its disposition changes. From
the 0.7 release on, a change follows the version rule of
[`api/README.md`](../README.md).

The admission rule (docs-semantic#68) applies in full: a concept enters the
common model
if the adopted Matter baseline or eeBUS can represent it; beyond that only
when it is common to two or more vendors, and its issue then holds a
deep-research report that looks at other vendors and neutral northbound
standards to choose the representation. Normalization to the
highest-precision industry-standard unit is acceptable.

| Element | Status | Admission | Representability check | Deep-research report |
|---|---|---|---|---|
| Six planes | new; named in docs-semantic#67 | arm `owner_decision`, evidence the issue; the acceptance of this contract on docs-semantic#67 is the admission act | not applicable: a plane holds no data of its own | no |
| Seven core relation types, including the `relays` meaning | new data concepts | arm `matter_baseline` or `eebus`, with the citation per type, recorded before the catalog merges | yes, per type | only for a type whose check fails; or the project owner admits it under `owner_decision` |
| `resource.equipment` | new | `matter_baseline` or `eebus`, cited | yes | if the check fails |
| Core relation definition `relation.relays` | new | follows its core type | as `relays` | as `relays` |
| 27 kinds derived from accepted pack dimensions; the 21 accepted relation definitions; all other seed pack entries | already in the accepted common model | arm `accepted_pack`, evidence the pack contract; allowed only for the frozen seed references | no | no |
| Existing kernel state types and target vocabulary | already in the accepted kernel | arm `accepted_kernel` | no | no |
| The six state types this contract adds (anchor class and basis, relation basis, resource state, relation coherence, cut findings) | contract structure, no data concept | arm `owner_decision` | not applicable | no |
| Any later resource kind, core type, plane, core or pack relation definition, or fact definition | new | the full rule | yes | when not representable |
| Identification scheme | new per entry; an identity convention, not a concept of the common model | arm `public_registry`: docs-semantic review on public evidence of the scheme and its issuing registry | no | no |

Evidence for an admission record is a public link pinned to a revision: a
repository file at a full commit, an issue, or a published specification.

### 10.6 Source-specific extension

The core and pack sections of the catalog name no vendor and no product. A
source-specific concept that is not admitted is an extension entry: identifier
in the `native.` namespace, owner the public native documentation repository,
disposition `unknown`, and a tracking issue. It is never in a plane. It
becomes a core or pack element only through the admission rule, under a
neutral name. Check: the validator rejects an extension entry with another
disposition and a core or pack entry owned by a native repository. Screening
of free text for vendor names stays a review duty.

### 10.7 Bringing in the accepted packs

The seed is generated from the accepted pack vectors by fixed rules and
reviewed as data; rules and counts are in the catalog seed outline
(docs-semantic#68). Every resource dimension maps to one core kind: the three
phase and two meter dimensions share one kind each, while the thermal and the
electrical circuit become two kinds. The 21 relationship definitions become
relation definitions with an explicit core type, orientation and kinds. Every
element whose subject or membership cannot be decided from accepted text
receives `unknown` with a tracking issue instead of being dropped.

## 11. Publication and coherence

### 11.1 Home asset

- **PUB-1** Every current resource has exactly one home asset. All facts,
  services and capabilities whose subject it is, every relation instance whose
  starting end it is, and every absence statement about it are published only
  in its home asset. Check: RES-5 and REL-2 resolve inside the snapshot; cut
  assembly reports a resource current in two assets (section 11.3).
- **PUB-2** The gateway chooses the home asset. Moving a resource to another
  home is a withdrawal in the old home followed by an upsert in the new one.
  Asset granularity is a publication decision, not a resource-model decision.
- **PUB-3** A resource's origin resolves in its home snapshot: a current or
  tombstoned binding of that asset, or an operator origin. Operator-origin
  records are published as follows:
  - A resource that only configuration knows is homed in an asset whose
    single source is the gateway's configuration provider; it needs no second
    source.
  - An operator record whose starting end is homed in a driver's asset (a
    configured meter role, a battery attachment on an inverter) is published
    by the gateway's configuration provider as a contributor source of that
    home asset (section 6.4), under the provider's own source, epoch and
    generation. It is therefore not blocked while the driver's generation is
    fenced, and its withdrawal does not depend on the driver. One exception:
    an operator identity declaration in the form of an `IdentityLink` names
    the driver's binding, and only that binding's source may publish it, so it
    travels in the driver's own batch.
  The contributor path in the gateway belongs to ebusgateway#1539.
  Check: `dangling_reference`.

The batch rule "one atomic change for one asset/source/epoch/generation" is
unchanged. A relation instance whose `to` is homed elsewhere is a change of the
holding asset only; it references `to` by `ResourceID`.

### 11.2 Records in batches and snapshots

`PublicationBatch` gains the optional members `resource_upserts`,
`relation_upserts`, `relation_withdrawals` (a list of `RelationKey`),
`absence_upserts` and `absence_withdrawals` (a list of `(definition, resource,
side)` keys). `Snapshot` gains the optional members `resources`, `relations`
and `relation_absences`. `RevisionVector` gains the optional component
`structure`, which counts changes to these three collections.

Each optional collection is omitted when empty; a present empty collection is
`invalid_value`. `structure` is omitted until the asset's first accepted
structural change and is present and monotonic afterwards. A snapshot that
carries no graph record therefore keeps its exact earlier canonical bytes and
content-derived identifier, and persisted state written before this change
still decodes. This serialization choice is what keeps every existing snapshot
identifier and test pin unchanged.

### 11.3 Graph cut and coherence

A graph cut is assembled by the pure function `AssembleCut(snapshots, catalog,
completeness)` from snapshots with distinct asset identifiers. `completeness`
is `complete` when the caller asserts the set holds every current asset of the
installation, otherwise `partial`. The cut identifier is `sha256:` over the
JCS bytes of `{contract:"helianthus.semantic.graph-cut/v1", members}`, where
`members` lists `(asset_id, snapshot_id)` sorted by asset identifier. There is
no global revision: the coherent revision of a graph read is this vector of
per-asset snapshot identifiers.

Assembly rejects only invalid input: a malformed snapshot, two snapshots of
one asset (`duplicate_key`), or more than 256 snapshots (`bounds_exceeded`).
Problems inside members never block the read; they are reported as findings
(`CutFindingKind`):

| Finding | Condition | Effect |
|---|---|---|
| `duplicate_identity` | one `ResourceID` current in two members, or retired in one and current in another | both members are excluded from the cut, which becomes `partial`; neither is chosen |
| `same_unit` | two current resources of one kind with an equal anchor key in two members: the same native key, or the same parent and slot | both kept; their facts MUST NOT be added together. Pairs that share no key are not detectable (section 6.3) |
| `contradicted_absence` | an absence statement in one member contradicts a qualified instance held by another | the instance becomes `conflict`; the absence statement is reported, not removed |
| `anchor_parent_unresolved` | a resource's anchor parent is not the `from` of a coherent `contains`, `groups` or `hosts` instance to it | the resource keeps its identity but MUST NOT be presented under any parent |
| `ungraphed` | a member holds facts of a catalog-covered pack but no graph record (ACT-5) | it contributes to no plane |

Every relation instance gets one `RelationCoherence`:

| Coherence | Condition |
|---|---|
| `coherent` | `from` current in the holder; `to` current in a member and of an admitted kind; no conflict |
| `stale` | `to` is present in a member but `withdrawn` or `retired` |
| `dangling` | `to` is in no member and the cut is `complete` |
| `outside_cut` | `to` is in no member, the cut is `partial`, and no member was excluded for holding `to` |
| `excluded` | `to` is held by a member that this cut excluded (`duplicate_identity`) |
| `conflict` | the instance is `conflict` in its snapshot (REL-6); or qualified instances held by different members together violate cardinality, the forest rule or acyclicity; or an absence statement elsewhere contradicts it; or `to` has a kind the definition does not admit |

- **COH-1** Only `coherent` instances in state `qualified` are plane members
  (PLN-2). A reader MUST NOT present any other instance as a current edge.
  Check: cut vectors.
- **COH-2** Findings and coherence states are part of the cut's canonical
  output; assembly is deterministic, so identical inputs give identical bytes.
  Check: vectors compare canonical output.

*Increment 2* decides which cut a retrieval serves, how a lens result carries
it, and its bounds.

### 11.4 Derived facts across resources

The kernel rule that derivation inputs resolve inside one snapshot is
unchanged. A fact derived from facts about several resources is published only
when all inputs are in one home asset. In increment 1 no fact is derived from
facts of two different assets: no site balance and no multi-inverter total is
computed across assets. A total that a source itself reports, such as a
logger's or a controller's, is published as an observed aggregate under
section 12. Facts of sources homed in one asset can feed a derivation only when
that asset holds those sources, which needs the multi-source capability of
section 6.4.

### 11.5 Bounds

Per asset: 4096 resources, 8192 relation instances, 1024 absence statements,
and 1024 identity links that carry `resource`. The existing bound of 128
identity links applies to links without `resource` and does not change. Per
cut: 256 member snapshots. Exceeding a bound rejects with `bounds_exceeded` and
never truncates.

## 12. Power and energy: the subject rule

These rules decide where a quantity goes. They place no specific quantity.

- **EN-1 Subject.** A quantity fact's subject is the resource at whose
  boundary or terminal it is measured or defined, not the device that reports
  it, the pack that defines it, or a plane. Check: the gate row names the
  subject kind and the measurement point; review rejects a subject chosen
  because a device reports the value.
- **EN-2 Pack.** The fact uses the definition that already has its meaning, in
  whichever pack owns it. The domain of the subject never chooses the pack; a
  second pack never redefines a meaning. Check: CAT-1 and review.
- **EN-3 Planes.** Membership comes from the fact definition's catalog entry.
  Check: PLN-1.
- **EN-4 Direction.** Each quantity's catalog entry states its direction:
  `not_applicable` (not a flow), `non_negative` (a flow whose definition
  states its direction relative to the subject, or that it is a magnitude), or
  `signed`. A signed quantity names the
  `supplies` relation definition whose nominal direction is its positive
  reference. Seed entries whose pack keeps the native convention carry
  `native_convention` instead. A gate converts a native sign convention with
  evidence or withholds the value; a sign is never inferred from values.
  Check: CAT-7 and gate validators.
- **EN-5 Aggregates.** An aggregate's subject is the resource whose scope it
  covers (a system, a site, a group); its coverage is that resource's `groups`
  or `contains` instances. If that scope cannot be named as a resource, the
  aggregate stays on the reporting equipment with aggregation `aggregate` and
  no coverage. An aggregate and its members are never added together, and an
  aggregate is never attached to a control device because that device reports
  it. Check: catalog `aggregation`; lens enforcement is *Increment 2*.
- **EN-6 Usage.** A usage the source distinguishes is published per usage; a
  merged total is a separate aggregate definition. Check: gate review.
- **EN-7 Units.** Normalization to the highest-precision industry-standard
  unit is done by the gate with evidence and declared precision. Check: pack
  bounds and gate validators.
- **EN-8 Meter roles.** A meter's role is an instance of a `measures` relation
  definition between the meter and the measured resource. It is held by the
  home asset of that definition's starting end; for the accepted infrastructure
  grid-connection-to-meter definition, that is the grid connection. The
  definition admits the basis classes that the native owner's evidence
  supports. The role never changes a fact definition; whether a meter
  quantity's subject is the meter or the measured resource follows EN-1. Check:
  gate validators and the existing role negatives.

Example (informative). A logger with three inverters reports a plant power
total. Under EN-1 and EN-5 its subject is the resource that groups the three
inverters, with aggregation `aggregate`; each inverter's own power has its
inverter as subject. If the logger cannot state which inverters its total
covers, the total stays on the logger resource as an aggregate without
coverage.

## 13. Authority

- **AUT-1** Visibility grants no control. Admission reads no graph record: no
  plane membership, lens result, relation instance or absence statement. The
  catalog affects admission only through the inadmissible flag set at registry
  construction (ACT-4). Check: the operation package does not import
  `semreg/v1/graph`. A vector in which the only path from a capability to the
  target resource is a relation instance finds zero eligible routes and is
  rejected with `ambiguous_route`.
- **AUT-2** The capability-to-resource link is capability instance → service
  instance → service `resource`. The subject of the expected-effect fact
  equals that resource. Check: the pack effect rule derives the expected fact
  key with that subject; a caller-asserted different subject fails the
  existing derivation with `invalid_value`.
- **AUT-3** A `controls` instance describes regulation; it never authorizes an
  operation. An operation on a controlled resource needs that resource's own
  qualified capability instance, whose route may use the controller's binding.
  Check: as AUT-1.
- **AUT-4** Commanded, effective and reported values are separate fact
  definitions; plane membership never merges them. Check: CAT-1 and review.

## 14. Separation from the target projection report

- **PRJ-1** `ProjectionReport` stays the accounting of one target and version,
  never the internal view, the plane contract or a catalog disposition. Check:
  the catalog schema has no projection outcome value.
- **PRJ-2** A `RequestedItem` of kind `relation` names a catalog relation
  definition. Check: projection validation resolves it through the catalog.
- **PRJ-3** A gate, hand-off or internal read never records a target outcome as
  an internal disposition. Check: gate validators.

*Increment 2* decides whether reports may cite relation instances and resources
as sources, and what the present read target becomes.

## 15. Hand-off from native owners

Beyond pack and field, a mapping gate MUST state, and its validator MUST check:

1. for each resource kind it publishes: anchor class and basis, the anchor
   source (`native_token`, `native_position` or `operator_label`; never an
   address or a credential), the listed identification scheme and issuer
   registry its tokens map to, and the parent kind;
2. for each relation it supports: the relation definition, basis class,
   evidence, validity scope (profile, version, scope of the rule) and the
   absence statements it can make;
3. for relayed values: the relaying resource and, when the same unit is also
   observed directly, its anchor key source or a statement that none exists;
4. for aggregates: coverage, aggregation and subject under section 12;
5. which native interpretation selectors it uses and how its native owner
   classifies them;
6. no plane membership.

Questions each native owner answers in its own repository, with evidence; the
contract decides none of them:

- Is a relation of my family observable natively, and for which scope, or is it
  configuration? Examples of such relations: which unit conditions which zone,
  a meter's role, a battery's attachment.
- Is a native unit one resource with a function resource (for example an
  indoor unit and a zone), or two resources with a relation between them?
- Which token identifies my units stably, and in which canonical form?
- Which of my identifiers are interpretation selectors?

Until a native owner answers, the default is two resources, no relation, and
the relation unknown. Native items not proposed for promotion stay native and
need no catalog entry; each native item a gate covers keeps one native
disposition, as today.

## 16. Worked examples (informative)

**A heating controller with two zones and one mixed circuit.** Resources: the
controller (`equipment`), the thermal system (`function`), two zones and one
thermal circuit (`function`, slots under the thermal system). Relations, under
definitions that the thermal pack still has to add through the admission rule:
the thermal system groups the zones and the circuit; the circuit supplies a
heat-transfer fluid to both zones; the controller controls the thermal system.
When the controller is replaced, it gets a new identifier and the new
controller's `controls` instance is published; the zones and the circuit keep
theirs. In the seed this example is not yet expressible: the circuit kind is
`unknown` and no thermal relation definition exists.

**A logger with three inverters and one battery behind an inverter.**
Resources: the logger (`resource.equipment`), three inverters (`equipment`),
the system that groups them (`function`), and the battery (`equipment`). The
logger relays the three inverters and the second inverter relays the battery,
under the core `relays` definition. With one home asset per inverter, the
logger's asset holds the three `relays` instances, whose `to` endpoints are
checked in the cut. If the battery also has its own source homed in another
asset and both paths carry the same anchor key, the cut flags the pair
`same_unit` until one asset holds both sources. If the inverter exposes no
battery token, the two battery resources share no key and are not flagged,
unless the operator declares the pair with one shared operator slot.

**An air-conditioning system with one outdoor and three indoor units.**
Resources: one outdoor and three indoor units (`resource.equipment` until
specific kinds are admitted). A unit address is a destination coordinate and
never an anchor. Whether an indoor unit and a zone are one resource or two, and
whether the unit-to-zone relation is observable or configured, are questions
for the native owner under section 15; until they are answered, no such
relation exists in the graph. A refrigerant circuit enters the hydraulic plane
with medium `refrigerant` once its kind is admitted.

## 17. Amended kernel rules

Each row is an in-place edit of v1 in the 0.7 release cycle. "Kept" means the
present sentence stays and the amendment follows it.

| File, heading | Present sentence | Amendment |
|---|---|---|
| `api/README.md`, Version rule | "A breaking change requires a new major contract directory." | Replaced by: "Until the Helianthus 0.7 release, the project owner may require a breaking change to be made in place in an existing versioned directory; each such change is listed in this page's in-place change record with its date, scope and the locks it moves. From the 0.7 release on, a breaking change requires a new major contract directory." |
| `api/v1/kernel.md`, Scope | "The wire rules in [serialization.md](serialization.md) and the scenarios in [acceptance.md](acceptance.md) are part of this contract." | Replaced by: "The wire rules in serialization.md, the scenarios in acceptance.md and the resource graph, plane, lens, element-catalog and activation rules, errors and vectors in graph.md are part of this contract." |
| same | "It does not define the thermal, PV, storage, EVSE, or infrastructure capability-pack catalogs; native protocol mappings; gateway lifecycle interfaces; Portal descriptors; consumer schemas; or target conformance." | Kept; adds that graph.md defines resources, relations, planes, lenses and the element catalog. |
| `api/v1/kernel.md`, Package surface | `semreg/v1` row | Adds "resources, relation instances and absence statements"; a new row `semreg/v1/graph` owns the element catalog, planes, lenses and graph-cut assembly. |
| `api/v1/kernel.md`, Type: PackValidator | registry construction text | Adds: "A registry constructed with the element catalog is graph-enforced; graph.md section 5 defines its construction checks and the inadmissible-operation flag." |
| `api/v1/kernel.md`, Type: OpaqueID | "In particular, a bus address is not an `AssetID`, a source epoch is not a driver generation, a driver generation is not a semantic revision, and a lifecycle operation identifier is not an intent or causal correlation." | Kept; `ResourceID` joins the alias list, and the sentence adds "and an `AssetID` is not a `ResourceID`". |
| `api/v1/kernel.md`, Type: IdentityLink | struct sketch | Adds the optional members `resource` and `key` (section 6.4). |
| `api/v1/kernel.md`, Type: ServiceInstance | struct sketch | Adds the optional member `resource` (section 6.2). |
| `api/v1/kernel.md`, Type: CapabilityInstance | "Catalog completeness cannot create an instance." | Kept; adds "Plane membership, lens inclusion and relation instances cannot create, select or authorize an instance." |
| `api/v1/kernel.md`, Type: GenerationFence | "Every binding from that generation is retained as `state=fenced`; its identity links are retained as `state=withdrawn`; its services and capabilities are retained as `availability=withdrawn`." | Kept; adds "Its relation instances and absence statements with a native basis are removed from the current snapshot; resources are not affected." |
| `api/v1/kernel.md`, Type: PublicationBatch | "Cross-asset changes require a separate batch and cannot be partially committed together." | Kept; adds "A relation instance whose `to` endpoint is homed in another asset is a change of the holding asset only; graph.md defines its coherence." The struct gains the optional members of section 11.2. |
| `api/v1/kernel.md`, Type: RevisionVector | "Each value is monotonic per asset and greater than zero in a published snapshot." | Replaced by: "Each present value is monotonic per asset and greater than zero in a published snapshot. `structure` is omitted until the asset's first accepted change to resources, relation instances or absence statements and is present in every later snapshot of that asset." |
| `api/v1/kernel.md`, Type: Snapshot | "A snapshot is immutable, self-consistent, and complete for one asset at one semantic revision." | Kept; adds "It holds the resources homed in that asset and every relation instance and absence statement the asset holds." |
| same | "Every reference resolves inside the snapshot or to an `EvidenceRef`." | Replaced by: "Every reference resolves inside the snapshot or to an `EvidenceRef`, except the `to` endpoint of a relation instance homed in another asset, which resolves in a graph cut." |
| same | "Limits are 32 sources, 128 bindings, 128 identity links, 4096 fact envelopes, 40 retained observations, 1024 services, 2048 capabilities, and 128 retained fences per asset." | Kept; adds the bounds of section 11.5, and that the 128 identity links are those without `resource`. |
| same | "It never observes mixed identity, fact, service, capability, or fence revisions." | Replaced by: "It never observes mixed identity, fact, service, capability, structure or fence revisions." |
| `api/v1/kernel.md`, Type: Route | "Presentation `Selection`, compatibility aliases, projections, or caller-supplied native IDs cannot select the route." | Replaced by: "Presentation `Selection`, compatibility aliases, projections, plane membership, lens results, relation instances, or caller-supplied native IDs cannot select the route." |
| `api/v1/kernel.md`, Type: RequestedItem | "`ItemKind` is `fact`, `relation`, `capability`, or `operation`." | Kept; adds "A `relation` item names a relation definition of the element catalog." |
| `api/v1/serialization.md`, Field presence and unknown data | "A later contract version may add members with an explicit migration; v1 does not provide an arbitrary extension map." | Replaced by: "Members are added only by an explicit contract change with a stated migration. The graph members of graph.md were added in place to v1 as optional members that are omitted when empty, so a record without graph content keeps its earlier canonical bytes. v1 provides no arbitrary extension map." |
| `api/v1/serialization.md`, Array ordering | table | Adds: resources by `resource_id`; relation instances and withdrawals by `(canonical definition, from, to)`; absence statements and withdrawals by `(canonical definition, resource, side)`; cut members by asset identifier; findings by `(kind, canonical subject)`. |
| `api/v1/serialization.md`, Error determinism | precedence list | `stale_relation` joins group 5 after `stale_driver_generation`; `membership_missing` joins group 6 after `definition_owner_missing`; `duplicate_identity`, `identity_drift` and `relation_not_qualified` join group 6 after `identity_not_qualified`. |
| `api/v1/acceptance.md`, Stable error identifiers | "This list is exhaustive for v1 public validation. A conforming implementation MUST NOT mint an additional public rejection ID under the same contract version." | Replaced by: "This list and the list of stable graph errors in graph.md are together exhaustive for v1 public validation. A conforming implementation MUST NOT mint any other public rejection ID under the same contract version." |
| `api/v1/acceptance.md`, Normative rejection class map | table | Adds five rows: "two current resources with one `ResourceID` or anchor key, or a reused retired `ResourceID`" → `duplicate_identity`; "changed kind or anchor of a `ResourceID`, or an endpoint or subject of a non-admitted kind" → `identity_drift`; "graph record without a member catalog entry, graph member in a non-enforced kernel, uncovered pack in a graph-enforced registry, inadmissible operation, or invalid catalog membership" → `membership_missing`; "relation instance or absence statement with an empty, non-admitted or origin-inconsistent basis" → `relation_not_qualified`; "relation upsert to a withdrawn or retired same-asset resource" → `stale_relation`. The row "route selected from presentation/projection/alias/caller native ID" adds "plane membership/lens result/relation instance". |
| `api/v1/acceptance.md`, Error: `route_selection_forbidden` | "A caller, presentation selection, projection, compatibility alias, or native address attempts to choose/bypass the guarded route." | Replaced by: "A caller, presentation selection, projection, compatibility alias, plane membership, lens result, relation instance, or native address attempts to choose/bypass the guarded route." |
| `api/v1/pack-metadata-v1.md`, title and first paragraph | "Immutable pack metadata v1" | Adds: "Immutable means read-only at run time. Until the 0.7 release the metadata changes in place whenever an accepted pack changes in place (api/README.md)." The thermal re-keying needs this. |
| `api/v1/family-catalog-v1.md`, Compatibility | "The following require a new contract version (`v2`):" | Replaced by: "From the 0.7 release on, the following require a new contract version (`v2`); until then the in-place rule of api/README.md applies:". A multi-pack family row needs this. |
| `architecture/repository-ownership-v1.md`, Purpose | layering block | Inserts "-> semantic resource graph with planes and lenses" between "protocol-neutral semantic facts and capabilities" and "target-specific projection with declared loss". |
| same, Ownership split | "A device may expose several independently versioned capability packages; packages do not own native mappings." | Kept; adds "The device stays one resource of the semantic graph; packages own neither its identity, its relations nor its plane membership." |
| `api/v1/packs/pv-inverter-v1.md`, `api/v1/packs/evse-v1.md`, `api/v1/packs/infrastructure-v1.md`, Compatibility and validation | "Breaking change requires a new major pack directory." | Replaced by: "The version rule of api/README.md applies, including its rule for in-place changes until the 0.7 release." |
| `architecture/glossary.md` | (no entry) | Adds entries for resource, relation, plane, lens, element catalog and graph cut, and the qualified exceptions of section 3. |
| Pack vectors and pages, storage contract tables, the PV, storage and gateway-meter gates | identifiers `<pack>.relationship.<name>`, the member `relationships` and the word "relationship" | Renamed to `<pack>.relation.<name>`, `relations` and "relation", with one shared encoding (`from`, `to`, `cardinality`, `order`). The rename is decided (docs-semantic#67) and is made in place by a later change of this wave with no alias; it is listed in the in-place change record of [`api/README.md`](../README.md) when it lands. Until then the pack documents keep the `relationship` spelling. |

Not amended in increment 1: `DefinitionIndex` (relation definitions are
indexed by the catalog registry), `pack-availability-view.md` (*Increment 2*),
and the kernel `acceptance-vectors.json`. Because the precedence list and the
class map now name errors whose headings live in graph.md, the kernel
validator `scripts/validate_kernel_v1.py` and its test take the documented
error set as the union of the acceptance.md and graph.md headings. The vector
file's `error_ids` stay equal to the acceptance.md headings.

## 18. Stable graph errors

These identifiers extend the exhaustive v1 list (section 17). Precedence is in
[serialization.md](serialization.md#error-determinism); the class map is in
[acceptance.md](acceptance.md#normative-rejection-class-map).

### Error: `duplicate_identity`

Two current resources in one snapshot share an anchor key, or a retired
`ResourceID` is upserted as current.

### Error: `identity_drift`

A `ResourceID` changes kind or anchor key, or a resource dimension value or
relation endpoint resolves to a resource of a kind its definition does not
admit.

### Error: `membership_missing`

A published record names an element without a catalog entry with disposition
`member` where one is required; a non-enforced kernel receives a graph member;
a graph-enforced registry is constructed with an uncovered pack; an intent
names an inadmissible operation; or the catalog violates completeness,
disposition, closure or core-type plane rules.

### Error: `relation_not_qualified`

A relation instance or absence statement has an empty basis, a basis class its
definition does not admit, or a basis class that disagrees with its origin.

### Error: `stale_relation`

A relation instance is upserted with a same-asset `to` endpoint that is
withdrawn or retired.

## 19. Conformance

Coverage identifiers of the graph acceptance document: `activation`,
`resource`, `relation`, `plane_membership`, `element_catalog`, `graph_cut`,
`authority`. Each has at least one positive and one negative vector. Operations
are `construct_registry`, `register_catalog`, `apply`, `assemble_cut` and
`admit`.

Negative vectors and cut outcomes, as testable statements:

| Class | Identifier | Statement | Expected |
|---|---|---|---|
| Activation | G-NEG-ACT-1 | `apply` a resource upsert to a kernel without the catalog | reject `membership_missing` |
| Activation | G-NEG-ACT-2 | `construct_registry` with the catalog and a pack it does not cover | reject `membership_missing` |
| Activation | G-NEG-ACT-3 | `admit` an intent for an operation whose catalog disposition is `unknown` | reject `membership_missing` |
| Duplicate identity | G-NEG-ID-1 | `apply` two current resources of one kind with one anchor key | reject `duplicate_identity` |
| Duplicate identity | G-NEG-ID-3 | `apply` an upsert making a retired `ResourceID` current | reject `duplicate_identity` |
| Duplicate identity | G-POS-CUT-1 | `assemble_cut` over two members that both hold resource X current | accept; finding `duplicate_identity`; both members excluded; cut `partial` |
| Identity drift | G-NEG-ID-2 | `apply` an upsert changing the kind or anchor key of a `ResourceID` | reject `identity_drift` |
| Identity drift | G-POS-CUT-2 | `assemble_cut` where a relation's `to` has a kind its definition does not admit | accept; coherence `conflict` |
| Identity drift | G-NEG-REL-4 | decode a relation instance with an extra plane-scoped identifier member | reject `unknown_member` |
| False join | G-NEG-ID-4 | `apply` an identity link naming a natively anchored resource with a different `key` | reject `identity_not_qualified` |
| False join | G-NEG-ID-5 | `apply` a qualified identity link naming resource X with an empty basis | reject `identity_not_qualified` |
| False join | G-NEG-REL-1 | `apply` a relation instance with basis class `configuration` and a native-observation origin | reject `relation_not_qualified` |
| False join | G-NEG-REL-2 | `apply` a relation instance whose basis class the definition does not admit | reject `relation_not_qualified` |
| Missing membership | G-NEG-CAT-1 | `register_catalog` with one pack field absent | reject `membership_missing` |
| Missing membership | G-NEG-CAT-2 | `register_catalog` with a relation definition in a plane one endpoint kind does not admit | reject `membership_missing` |
| Missing membership | G-NEG-RES-1 | `apply` a resource whose kind has disposition `unknown` | reject `membership_missing` |
| Missing membership | G-POS-CUT-5 | `assemble_cut` with a member that holds facts of member definitions but no graph record | accept; finding `ungraphed` |
| Missing membership | G-POS-CUT-10 | `assemble_cut` with an enforced member that publishes only facts of `unknown` definitions | accept; no `ungraphed` finding |
| Stale relation | G-NEG-REL-3 | `apply` a relation instance whose same-asset `to` is withdrawn | reject `stale_relation` |
| Stale relation | G-POS-CUT-3 | `assemble_cut` where the `to` resource is retired in its home | accept; coherence `stale`; in no plane |
| Dangling endpoint | G-NEG-REL-5 | `apply` a relation instance whose `from` is not a current resource of the asset | reject `dangling_reference` |
| Dangling endpoint | G-NEG-RES-2 | `apply` a fact whose resource dimension names no current resource | reject `dangling_reference` |
| Dangling endpoint | G-POS-CUT-6 | `assemble_cut` (complete) where `to` is in no member | accept; coherence `dangling` |
| Contradiction | G-POS-CUT-7 | `assemble_cut` where member B's absence statement denies a qualified instance held by member A | accept; instance `conflict`; finding `contradicted_absence` |
| Conflict in one asset | G-POS-REL-2 | `apply` two qualified `contains` instances of different definitions to one part | accept; both `conflict` |
| Conflict in one asset | G-POS-REL-3 | `apply` qualified `relays` instances forming a cycle | accept; all `conflict` |
| Same unit | G-POS-CUT-4 | `assemble_cut` with two resources of one kind and one anchor key in two members, once native and once parent and slot | accept; finding `same_unit` in both cases |
| Same unit | G-POS-CUT-8 | `assemble_cut` with one unit seen through two protocols whose native owners map its token to the same scheme, issuer and token | accept; finding `same_unit` |
| Same unit | G-POS-CUT-11 | `assemble_cut` with two resources of one unit whose anchors share no key | accept; no finding (not detectable, stated) |
| Excluded endpoint | G-POS-CUT-9 | `assemble_cut` where a relation's `to` is held by an excluded member | accept; coherence `excluded` |
| Identity | G-POS-ID-2 | `apply` an anchor supersession from `operator_slot` to `native_identity` with binding continuity evidence | accept; same `ResourceID`, new anchor, `supersedes` recorded |
| Identity | G-NEG-ID-6 | `apply` an anchor change without `supersedes`, or with a `previous` that differs from the prior anchor | reject `identity_drift` |
| Identity | G-NEG-ID-7 | `apply` a supersession from `native_identity` to `operator_slot` | reject `identity_drift` |
| Identity | G-POS-ID-3 | `apply` two resources of one kind whose tokens are equal but whose issuers differ | accept; two resources, no duplicate |
| Plane membership | G-POS-PLN-1 | an equipment resource that only relays, beside another equipment resource with an energy relation | the first is in physical and provenance only |
| Unauthorized control | G-NEG-AUT-1 | `admit` a zone-effect intent when only the controller has a capability and a `controls` instance links them | reject `ambiguous_route`; the graph is not searched |
| Unauthorized control | G-NEG-AUT-2 | `admit` an intent asserting an expected-effect subject other than its capability's service resource | reject `invalid_value` |
| Unauthorized control | G-NEG-AUT-3 | `admit` an intent naming a capability instance visible in the control plane but not qualified | reject `capability_not_qualified` |

The false-join vectors test the kernel's share. Real joins by ordinal, name or
address are caught where they are made, by the gate validators
(docs-semantic#69). The gateway's identity vectors GW-ID-1 to GW-ID-6 (section
6.3) belong to the gateway conformance tests.

Positive vectors also cover: publishing resources of every anchor class; an
in-asset relation; a cross-asset relation `coherent` in a cut; a fence that
removes a native-basis instance and keeps a configured one; an absence
statement; registration of the generated seed; multiple plane membership; one
resource observed through two bindings of one asset; a derived fact over two
resources of one home asset; an unchanged resource across a new source epoch
(G-POS-ID-1); and an operation admitted through a controlled resource's own
capability while a `controls` instance exists, with the same result as without
it.

## 20. Relation to the IOKit registry (informative)

| IOKit | This contract | Borrowed or not, and why |
|---|---|---|
| One registry of entries, each with one entry ID, visible in several planes | One graph of resources, one `ResourceID` in every plane | Borrowed: one identity across views. |
| Entry ID unique for one boot only | `ResourceID` stable across restart, re-addressing and rotation | Not borrowed: integrators need identity that outlives a restart. |
| A plane is the set of parent-child attachments made in that plane | A plane is the catalog's set of relation definitions and elements; one relation instance can be in several planes | Changed: no duplicated attachment per plane; non-tree relations stay typed. |
| Power plane connections are entries of their own | Relation instances are records with state, evidence and lifecycle | Borrowed in spirit. |
| Paths are plane-specific and name the entry | Paths are traversal results (*Increment 2*), never identity | Not borrowed: plane-anchored paths cause identity drift. |
| Matching and probe scores choose drivers automatically | Qualification is native and explicit; selection is presentation-only | Not borrowed. |
| Untyped property tables | Typed facts with pack-owned definitions | Not borrowed: the kernel forbids property bags. |
| Live, mutable registry; iterators may need reset | Immutable per-asset snapshots and graph cuts with explicit coherence | Not borrowed: consumers need identified reads. |
| Registering and terminating entries in phases | Explicit resource states; relation lifecycle tied to generation fences | Borrowed. |
| Seeing an entry does not open it; user clients gate access | Visibility grants no control; admission ignores the graph | Borrowed. |

The IOKit terms *service*, *provider*, *registry entry*, *matching* and
*personality* are not used: they collide with the kernel's services, the
gateway's providers and the native registries.

## 21. Alternatives and why this architecture

| Criterion (integrator's view) | Simplest viable: tags plus a relation record per asset | Registry entries: own identity per entry, attachment per plane, publication above the asset | This contract |
|---|---|---|---|
| One identity across views and targets | No: endpoints stay dimension text | Yes | Yes |
| Navigation without consumer-invented joins | Within one asset only | Yes | Yes, across assets through cuts |
| Coherent read across devices | Per asset only | One graph revision | A vector of per-asset snapshots with explicit coherence and findings |
| Atomic change across devices | No | Yes | No |
| Derived facts across devices | No | Yes | No in increment 1 |
| One unit seen by two sources | Not expressible | One entry | One resource when one asset holds both sources; otherwise flagged `same_unit` when the two share an anchor key, and not detectable when they share none |
| Bookkeeping | None | None | Home assets, moves between homes |
| Kernel publication unit and existing pins | Unchanged | Replaced and re-derived | Unchanged |
| Later move of publication above the asset | Needs re-keying | Already there | Possible without re-keying consumers |

The simplest alternative fails the acceptance: without resource identity a
resource cannot keep one identity across views. The registry-entry direction
meets the model and gives more: one graph revision, atomic and derived changes
across devices, no home-asset bookkeeping. Its cost is replacing the unit of
publication that every gateway publisher and every pinned kernel vector
depends on. Per-plane attachment and publication above the asset could be
separated; this contract takes neither for 0.7. It takes from the registry
direction what integrators store (identity, typed relations, explicit
lifecycle, planes over one graph). It keeps from the simplest one what the 0.7
implementation depends on (per-asset publication and existing bytes). The
price is the cross-device limits in the table. A later release can lift
publication above the asset without changing any identifier a consumer
stores.

## 22. Left out, falsifiers and validation

Left out of increment 1, with reasons:

- retrieval, traversal, lens seeds, consumer identity, target reports over a
  lens, the read target, Portal descriptors and native typed surfaces: they are
  increment 2 and need this identity first;
- specific equipment kinds (controller, communication gateway, outdoor and
  indoor unit, refrigerant circuit, heat generator, pump, valve, cylinder):
  each needs the admission rule and native evidence;
- thermal relation definitions and the thermal subject re-keying: pack
  decisions that need the project owner's placement answers;
- a spatial plane: no public basis;
- atomic and derived changes across assets: the registry-entry direction's
  benefits, not taken for 0.7.

Falsifiers. This contract is wrong if:

- a 0.7 consumer requirement needs an atomic commit or a derived fact across
  assets;
- a native owner shows a stable identity that none of the four anchor classes
  can express;
- a needed relation fits none of the seven core types;
- a view needs navigation that no plane or lens gives.

Validation commands:

- `python3 scripts/validate_graph_v1.py`;
- `python3 scripts/validate_element_catalog_v1.py`;
- `python3 scripts/validate_kernel_v1.py`, with its union of documented errors;
- their tests;
- `./scripts/check_docs.sh`.

semreg executes every graph vector by identifier with the catalog and every
kernel vector without it.
