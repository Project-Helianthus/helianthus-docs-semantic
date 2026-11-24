---
status: "documentation vocabulary based on the [semantic kernel v1](../api/v1/kernel.md)\nand [repository ownership contract](repository-ownership-v1.md). Existing typed\nand wire contracts retain their narrower meanings and compatibility rules;\nthis page introduces no API, member rename, schema change, or protocol fact.\nA conflicting type-level usage is an open question for its owner, not authority\nto reinterpret it here."
---

# Cross-repository glossary

Status: documentation vocabulary based on the [semantic kernel v1](../api/v1/kernel.md)
and [repository ownership contract](repository-ownership-v1.md). Existing typed
and wire contracts retain their narrower meanings and compatibility rules;
this page introduces no API, member rename, schema change, or protocol fact.
A conflicting type-level usage is an open question for its owner, not authority
to reinterpret it here.

## Epoch

An **epoch** identifies one continuity domain. A source epoch identifies the
continuity of one native source; it is not a counter, driver generation, or
snapshot revision. Under the [kernel contract](../api/v1/kernel.md),
`SourceEpochID` changes when source sequencing may restart, continuity cannot
be proved on restore, another runtime assumes the source, or the native
profile/version changes. `ClockEpochID` instead identifies a monotonic clock
domain; ticks from different clock epochs are not directly comparable.

A driver generation orders lifecycle instances within a source epoch. A fence
irreversibly excludes an old generation; it is a lifecycle transition, not an
epoch synonym. Snapshot revisions order accepted publication changes, not
source identity or reconnect counts. Existing counter-shaped types that use
“epoch” retain their owning contract's meaning; their names do not make them
`SourceEpochID` or establish cross-repository equivalence.

Retired unqualified synonyms: **generation**, **revision**, and **fence** for
source epoch. Use each qualified term for its distinct purpose.

## Driver

A **driver** owns lifecycle at an explicitly named integration boundary. The
[ownership contract](repository-ownership-v1.md) separates native transport and
profile acquisition from gateway orchestration and northbound output binding.
A native driver/provider may own acquisition and a live native handle; the
gateway composes and supervises that lifecycle. An output binding owns one
target/version projection with declared loss, not native qualification.
Always state which boundary a driver serves rather than assigning all roles
to one undocumented component.

Retired unqualified synonyms: **provider**, **adapter**, **runtime**, and
**sidecar** for driver. These remain valid narrower roles when their owner
defines them: an adapter may be a physical interface, a runtime a composition
owner, and a sidecar a process arrangement. None alone proves driver identity,
source continuity, or a northbound mapping.

## Profile

A **profile** is an explicit native interpretation and admission contract for a
defined source/version scope. It is not inferred device identity or proof of a
qualified installation. Native definitions and evidence belong to the
[public native documentation owners](../evidence/native-documentation-owners.md);
the [kernel](../api/v1/kernel.md) carries profile identity/version as native
evidence, not semantic capability proof.

Retired unqualified synonyms: **flavor**, **card**, **catalog**, **catalogue**,
and **pack** for profile. Use **catalog** for an inventory; the
[family catalog contract](../api/v1/family-catalog-v1.md) does not itself admit
an installation. A semantic pack owns versioned capability vocabulary, not a
native mapping. Flavor and card retain only explicitly documented local uses.

Likewise, **qualify**, **admit**, **accept**, and **promote** are not interchangeable:
qualification requires the native owner's evidence for the stated scope;
admission applies an explicit gate; acceptance is relative to a named contract;
promotion exposes a stable consumer contract. Proven/Hypothesis/Unknown evidence
grades do not themselves qualify an installation, admit an operation, or grant
command authority. Unknown evidence remains unknown; admission fails closed.

## Snapshot

A **snapshot** is an immutable, bounded observation or publication view with
provenance and freshness context. It is not evidence of live device readiness.
The [kernel snapshot contract](../api/v1/kernel.md) is narrower: `Snapshot` is
complete for one asset at one semantic revision, preserves alternatives and
conflicts, and contains bounded retained observations. Its revision vector is
separate from source epoch and driver generation.

Retired unqualified synonyms: **capture**, **read**, and **live state** for
snapshot. A native capture handle, a native semantic read, a protocol-neutral
read, and stored semantic state retain their owning contracts; they are not
interchangeable return types. Native capture/read terminology is routed through
the [native owners](../evidence/native-documentation-owners.md). A handle does
not imply an atomic observation, current freshness, or an actionable route.

Kernel current-state consumers need a time-evaluated view of the immutable
snapshot. Freshness can change without rewriting snapshot bytes. Preserve native
evidence and partial last-known-good state where the contract permits retention;
retained observations remain non-actionable. Operation admission re-evaluates
current evidence and fences, and fails closed. This glossary changes neither
existing eBUS MCP behavior nor GraphQL parity or projection loss.

## Resource

A **resource** is an identifiable thing of the installation with its own
lifecycle that facts, services, capabilities and relations can be about: a
piece of equipment, a component, a function of the installation, or a bounded
episode. The gateway allocates its `ResourceID`, which keeps one identity in
every pack, plane, lens and target; an `AssetID` is not a `ResourceID`. The
[graph contract](../api/v1/graph.md#6-resources-and-identity) defines its
anchor, home asset and lifecycle.

## Relation

A **relation** is a published, typed, directed link between two resources
under one relation definition, with state, evidence and provenance. Each
relation definition specializes one of seven core relation types. When neither
a relation instance nor an absence statement exists, the relation is unknown,
never "none". See the [graph contract](../api/v1/graph.md#7-relations).

## Plane

A **plane** is a view over the one semantic resource graph, defined by the
relation definitions and elements the element catalog makes members of it. A
plane owns no second truth and no command authority, and no plane is primary.
See the [graph contract](../api/v1/graph.md#8-planes).

## Lens

A **lens** is a named, bounded combination of planes, root kinds and relation
definitions that answers one question. It creates no identity, fact, relation
or membership; it selects from the graph. See the
[graph contract](../api/v1/graph.md#9-lenses).

## Element catalog

The **element catalog** is the machine-checked inventory of ownership,
admission, plane membership and catalog disposition (`member`, `unsupported`
or `unknown`) of every semantic element. Plane membership is declared there
once per definition; a catalog disposition is not a target projection outcome.
See the [graph contract](../api/v1/graph.md#10-element-catalog).

## Graph cut

A **graph cut** is a set of per-asset snapshots read together, at most one per
asset, in which relation coherence is evaluated. Its coherent revision is the
vector of member snapshot identifiers; there is no global revision. See the
[graph contract](../api/v1/graph.md#113-graph-cut-and-coherence).

## Served cut

A **served cut** is the one graph cut a read is answered from. It is identified
by its cut identifier and member vector, and the read carries that identifier,
the cut's completeness and its member vector. One answer does not combine two
cuts. See the [graph contract](../api/v1/graph.md#25-coherence-unit).

## Traversal

A **traversal** is a breadth-first walk over `coherent`, `qualified` relation
instances of a stated set of relation definitions, from one entry point, to a
stated depth. See the
[graph contract](../api/v1/graph.md#27-traversal-and-bounds).

## Frontier

A **frontier** is the set of resources at which a traversal stopped because of
a bound, each with the bound that stopped it. A bound never drops a resource
silently. See the
[graph contract](../api/v1/graph.md#27-traversal-and-bounds).

## Lens result

A **lens result** is the canonical document a lens retrieval returns
(`helianthus.semantic.lens-result/v1`). It holds the resources reached, the
relation instances among them, and the facts, services and capabilities whose
subject they are. It is not a target report and it grants no authority. See
the [graph contract](../api/v1/graph.md#28-lens-retrieval).

## Consumer identity

A **consumer identity** is the key under which a consumer stores something it
made from the graph. One consumer object maps to one resource. A value key is
the resource, the fact definition and the qualifier dimension values. A
traversal path, a cut identifier and a plane are not identity. See the
[graph contract](../api/v1/graph.md#33-consumer-identity).

## Qualified exceptions

Within the semantic API the words resource, relation, plane, lens, element
catalog, graph cut, served cut, traversal, frontier, lens result and consumer
identity have only the meanings above. These existing terms keep
their word with a qualifier, as listed in the
[graph contract](../api/v1/graph.md#3-definitions): **readback relation** (the
kernel's `Readback.relation` and `ReadbackRelation`); **native resource** (the
kernel's `NativeBinding.native_resource`); **Portal resource key** (the Portal
catalog's `resource_id`; this exception ends with PTL-3); **registry plane**
and **registry projection** (the native eBUS registry terms of its registry
tools, device GraphQL types and Portal registry routes); and **SPINE topology**
(the eeBUS `TopologyV1` record). No alias is created.

## Event

An **event** is an occurrence the kernel records. Origin `emitted` keeps an
event record of an occurrence the source protocol emits. Origin `derived`
marks a record derived from consecutive retained revisions of the trigger
fact. The event names its service, that trigger, a condition of `entered`,
`left` or `changed`, its symbols and payload, and that origin. See the
[kernel contract](../api/v1/kernel.md#event-record).

## Qualifier dimension

A **qualifier dimension** is a dimension of role `qualifier`. Its value kind
is a quantity of `unit.one`, text, or a symbol list. A fact key carries
exactly the qualifiers that fact declares, as a sorted unique list of
qualifier dimensions of the same pack. An undeclared qualifier is rejected
and is never guessed. See the
[kernel contract](../api/v1/kernel.md#qualifier-dimension).

## Class-level subject

A **class-level subject** is a resource dimension that names anchor classes
instead of one resource kind. The classes are a non-empty sorted unique
subset of `component`, `equipment`, `episode` and `function`. A fact on that
dimension is about any current resource whose kind has one of those classes.
See the [kernel contract](../api/v1/kernel.md#class-level-subject).
