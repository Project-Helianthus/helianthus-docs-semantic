# Derived five-pack availability view

Status: proposed read-helper contract for review, normative on merge. This page
specifies derivation rules over accepted v1 inputs; it does not define a new
serialized contract identifier, exported function signature or endpoint. Examples
are conceptual, not executable API fixtures. The helper remains pre-stable;
pack definition versions do not promise a stable consumer API before 1.0.

Evidence basis: the accepted [immutable metadata](pack-metadata-v1.md) and its
[fixture](pack-metadata-v1.json), [kernel types](kernel.md),
[serialization](serialization.md), and [projection dispositions](kernel.md#type-projectiondisposition).
The owning implementation is
[helianthus-semreg](https://github.com/Project-Helianthus/helianthus-semreg).
Its `packs.NewMetadataRegistry` must supply the existing metadata semantics;
this page does not replace that constructor or add methods to it. Implementation
conformance requires comparison with that constructor and the evaluation types.

Compatibility effect: an additive, pure read helper. No pack definition,
[family catalog state or composition](family-catalog-v1.md), native
qualification, operation admission, receipt mechanism or canonical state store
changes. There is no new MCP namespace or stability promise. Existing eBUS MCP
compatibility is preserved; MCP and GraphQL presentations of identical inputs
must preserve the same identity, distinctions, alternatives and loss accounting.
This page does not prescribe either transport's response shape.

## Inputs and exact identity

The helper takes an immutable validated metadata registry, one complete validated
`Snapshot`, and its matching `EvaluationView`. Metadata describes definitions;
the snapshot and evaluation describe this asset at this evaluation context.
Family catalog composition and declared pack support are not availability inputs.
There is no implicit clock, native lookup, discovery, publication, store read or
operation-admission call.

Before returning any result, validate the snapshot and evaluation under the
existing kernel rules, recompute the evaluation digest, and require:

- the exact snapshot ID and **complete** revision vector match;
- every current candidate appears exactly once by candidate ID and revision in
  evaluated facts, with no omissions or extras;
- the complete explicit evaluation context and evaluated retained set satisfy
  the kernel's evaluation and original-deadline rules.

The result carries the asset ID, snapshot ID, complete revision vector,
evaluation context (wall estimate, monotonic point and their existing time-domain
information), and evaluation digest unchanged. Do not substitute the semantic
revision alone, a latest-state pointer, a pack version or equal numeric revisions
from another asset. Preserve exact metadata PackRefs and DefinitionRefs as well.
A later evaluation requires a newly derived result even if snapshot bytes and
publication revisions have not changed. A mismatched or absent input yields no
availability result; it is not an empty successful view. Use existing validation
errors, without adding an error namespace or a receipt/digest for this helper.

## Five-pack scope and ordering

Produce exactly one row for each exact PackRef returned by the accepted metadata
registry, including rows with no instances or facts:

| Pack ID | Version | Definition owner |
| --- | --- | --- |
| `helianthus.pack.evse` | `1.0.0` | [EVSE](packs/evse-v1.md) |
| `helianthus.pack.infrastructure` | `1.0.0` | [Electrical infrastructure](packs/infrastructure-v1.md) |
| `helianthus.pack.pv` | `1.0.0` | [PV/inverter](packs/pv-inverter-v1.md) |
| `helianthus.pack.storage` | `1.1.0` | [Storage/BMS](packs/storage-bms-v1.md) |
| `helianthus.pack.thermal` | `1.0.0` | [Thermal/HVAC](packs/thermal-hvac-v1.md) |

This is canonical UTF-8 byte order by `(pack id, pack version)`, not registration
order or semantic-version precedence. Group by exact typed references, never ID
prefix, display label, family membership or a similar definition. Use existing
`HasDefinition`, `ServiceOwnsCapability` and, where a field/service/capability
relation is presented, `FieldMatches` semantics. Use `OperationMatches` only to
check the exact metadata five-part shape; a match cannot admit an operation.
Unknown or wrong-version references cannot be matched by dropping tuple fields.
Other registered packs remain outside this explicitly five-pack view; their
absence here says nothing about their support or availability.

Within each row, preserve separate collections of:

- service instances, sorted by exact instance ID;
- capability instances, sorted by exact instance ID, with their owning service
  reference, qualification, availability, constraints and activation evidence;
- current fact envelopes, sorted by canonical `FactKey`, with candidates sorted
  by candidate ID and joined to their exact evaluated candidate revision;
- evaluated retained observations, separately sorted by the kernel's complete
  retained-instance identity, only while the original deadline permits them.

Copy the source records or provide exact resolvable references within the supplied
immutable inputs. Retain every alternative and conflict, exact values and units,
source lineage, derivation inputs, evidence, causal context and distinct time
fields. Use canonical ordering from [serialization](serialization.md) for nested
collections. Return detached collections; mutation of a helper result cannot
mutate metadata, snapshot, evaluation or another result. Identical canonical
inputs yield identical logical rows and ordering.

## Availability without promotion

A pack row means only that its definitions are declared. It has no aggregate
`available` flag, inferred capability instance or count of admitted operations.
An empty capability collection cannot become available because metadata lists
capabilities, a family is composed, or one fact exists.

For each current fact, display stored quality axes alongside the matching
`EvaluatedFact.Freshness` and `EffectiveAvailability`. Stored availability alone
cannot describe a current value. Time evaluation can degrade or expire evidence;
it cannot promote, qualify or restore it. Do not overwrite stored quality with
evaluated quality, reset observation/receipt times, choose a winning source or
convert unknown into zero, false or an empty value.

`EvaluationView.Facts` evaluates **facts**, not service or capability instances.
For those instances, preserve the snapshot's availability and qualification,
current binding/source/generation path, owning service and activation evidence.
Their presence, even with `availability=available`, is not an admission result.
The kernel's actionable-capability rules, explicit degraded policy, constraints,
preconditions, exact candidate binding and admission-time re-evaluation remain
mandatory in the existing operation path. This helper creates no route,
authority, intent, sender or control affordance.

Preserve permitted partial last-known-good current candidates with their original
revision, time and evaluated state. Historical retained observations stay visibly
separate and non-actionable; they cannot fill a gap in current facts, satisfy a
capability or confirm readback. New partial publication cannot silently erase a
permitted current value, while fencing/withdrawal and retention expiry cannot be
undone by this read helper.

## Empty, absent, withheld and unknown

| Situation | Read meaning |
| --- | --- |
| Pack row with empty service/capability/fact collections | No matching current records in this supplied snapshot. Definitions remain declared; neither native absence nor unsupported hardware is proved. |
| Expected fact key has no current envelope | No current fact was published for that key. Do not synthesize a candidate, value or quality state. |
| Present candidate with unknown qualification, validity or evaluated freshness | Preserve the particular unknown axis and reasons. Unknown is not unsupported and cannot establish capability availability. |
| Present withdrawn instance or valueless candidate | Preserve the existing tombstone/quality rules. Do not drop it as if it had never existed or reconstruct a forbidden value. |
| Empty evaluated retained collection | No historical record remains visible at this context, even if the immutable snapshot contains expired retained records. |
| Missing snapshot, evaluation or required collection | Invalid/incomplete input, not evidence for an empty pack or unavailable device. |

Withholding is a presentation/projection disposition, not a new kernel
availability or qualification value. If a consumer projects this view, use the
existing `ProjectionReport`: every requested `(kind,item_id)` has exactly one
matching disposition; `withheld`, `unrepresentable`, `unsupported` and `unknown`
retain their reasons; `transformed` retains loss detail and `exact` forbids loss.
Preserve source keys and snapshot/revision binding. A withheld fact is not
absent native evidence, an unsupported family or an unavailable capability.
An omitted request is not an `unknown` disposition. A report alone does not carry
the evaluation context/digest; it cannot replace the matched evaluated inputs or
prove current availability. Any projection that drops alternatives, lineage,
units, precision or time information must account for that loss explicitly.

Proven/Hypothesis/Unknown describes the basis of a claim; it remains separate
from kernel assertion, qualification, promotion, validity, freshness and
availability. Neither those evidence labels nor family catalog states supply a
missing fact. Native claims still require the public native owner's contract
and qualification evidence before a semantic mapping can be used.

## Conceptual examples and falsifiers

These cases describe synthetic evaluated inputs, not complete wire objects:

| Input case | Required result |
| --- | --- |
| All five packs declared; valid evaluated snapshot has no services, capabilities or facts | Five ordered rows, each with empty current collections; no available-capability claim. |
| Storage fact retained as a current last-known-good candidate; evaluated freshness becomes stale | Same candidate/revision and original times; evaluated degraded availability where the kernel requires it; no renewed evidence or control permission. |
| EVSE capability exists but its qualification is unknown | Instance and unknown qualification remain visible; declared metadata cannot upgrade it. |
| A thermal fact has two conflicting current candidates | Both candidates, their evaluated states and conflict survive; no helper-selected winner. |
| Infrastructure fact requested for a target that withholds it | Target report keeps the exact requested tuple and withholding reason; current source evidence is not rewritten. |
| Same snapshot evaluated later, after a retained observation expires | New evaluation identity and no expired retained entry; snapshot and publication revisions unchanged. |
| Equal semantic revision but different snapshot ID, vector component or evaluated candidate revision | Reject mismatched inputs; never combine their rows. |

A helper is falsified by any catalog-only availability assertion, implicit clock
read, cross-version match, mixed snapshot/evaluation identity, missing alternative
or conflict, retained-to-current substitution, unexplained projection omission,
mutation of an input, or operation admitted on the strength of this view.

Unresolved: the SemReg exported helper signature and transport presentation shapes
require implementation review; this page freezes neither. Native mappings and
family qualification stay with their existing owners. This partial INT-05 /
INT-08 slice does not close either parent or establish hardware, interoperability,
release or physical acceptance.
