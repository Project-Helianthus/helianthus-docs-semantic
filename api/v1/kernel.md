# Project Helianthus semantic kernel v1

Contract ID: `helianthus.semantic.kernel/v1`

Owning Go module: `github.com/Project-Helianthus/helianthus-semreg`

Status: normative for the Helianthus v1 kernel when merged into `main`

## Scope

This document defines the implementable protocol-neutral kernel contract for
software 0.7. It fixes the public record types, validation rules, state axes,
snapshot and update semantics, capability matching, operation evidence, causal
loop bounds, projection accounting, and compatibility aliases that INT-05 must
implement.

The contract is normative only for Project Helianthus. It does not define the
thermal, PV, storage, EVSE, or infrastructure capability-pack catalogs; native
protocol mappings; gateway lifecycle interfaces; Portal descriptors; consumer
schemas; or target conformance. Those owners may depend on these records but may
not redefine them.

Canonical kernel packages must not import a transport, protocol, native
registry, gateway, vendor, output, UI, sibling-checkout, or private package.
Native owners retain framing, I/O, protocol lifecycle, qualification, decoding,
native identity, and raw evidence. The gateway retains live composition and the
native adapter retains every live handle. A semantic selection or projection
never grants authority or supplies a route around guarded native admission.

The wire rules in [serialization.md](serialization.md) and the scenarios in
[acceptance.md](acceptance.md) are part of this contract.

Public top-level records use these exact contract IDs:

| Record | Contract ID |
|---|---|
| `PublicationBatch`, `Snapshot` | `helianthus.semantic.kernel/v1` |
| `EvaluationView` | `helianthus.semantic.evaluation/v1` |
| `Selection` | `helianthus.semantic.selection/v1` |
| `Intent`, `ExecutionRecord` | `helianthus.semantic.operation/v1` |
| `ProjectionReport` | `helianthus.semantic.projection/v1` |
| `CompatibilityAlias` | `helianthus.semantic.alias/v1` |
| acceptance-vector document | `helianthus.semantic.kernel.acceptance/v1` |

## Conformance language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, and `MAY` have their usual normative
meaning. A v1 implementation conforms only when every applicable positive and
negative vector in
[acceptance-vectors.json](acceptance-vectors.json) passes without weakening a
validation rule.

An implementation may use different private data structures. Its public Go
types and JSON records MUST preserve the names, distinctions, and behavior in
this contract. Validation is fail-closed and atomic: a rejected record or update
changes no published state.

## Package surface

INT-05 must provide these public packages without cyclic imports:

| Package | Owns |
|---|---|
| `semreg/v1` | identifiers, versions, evidence, bindings, identity, values, facts, predicates, quality, services, capabilities, causal context, publication batches, fences, immutable snapshots, and pure evaluation views |
| `semreg/v1/operation` | intent, preconditions, admitted routes, dispatch/acknowledgement/readback evidence, and outcomes |
| `semreg/v1/projection` | target manifests, requested items, dispositions, loss details, and compatibility aliases |

Each package MUST expose validation for its complete public records. The root
package MUST expose deterministic canonical JSON for any valid v1 record. It
MUST return a stable error identifier from [acceptance.md](acceptance.md) for
every rejection. It MUST NOT accept an untyped `any` or arbitrary property bag
as a public semantic value, constraint, argument, precondition, or extension.

### Type: PackValidator

The root package exposes a typed pack boundary equivalent to:

```go
type PackValidator interface {
    Pack() PackRef
    Definitions() DefinitionIndex
    ValidateFact(FactKey, *Value) error
    ValidateService(ServiceInstance) error
    ValidateCapability(CapabilityInstance) error
    ValidateField(DefinitionRef, TypedField) error
    MatchConstraints(CapabilityInstance, []TypedField) error
    EvaluatePredicate(FactCandidate, PredicateOp, Value) (bool, error)
}
```

The kernel registry is constructed atomically with zero or more validators keyed
by exact `PackRef`. It builds the exact definition-owner index described below
before accepting any semantic record. Registry iteration order is never
observable. Duplicate validator/definition ownership is
`definition_owner_conflict`; a missing validator/index entry is
`definition_owner_missing`. The kernel MUST NOT infer ownership from an ID
prefix, probe validators in registration order, or accept the first validator
that returns success.

A record that needs a pack definition cannot be qualified, promoted, or made
actionable unless its exact owner and validator are registered. The interface
carries only typed kernel records; it does not expose raw protocol values,
native handles, arbitrary JSON, or `any`. Capability-pack catalogs and their
implementations remain separate INT-04/05 work.

## Primitive rules

### Type: ContractVersion

`ContractVersion` is an ASCII string of 1 through 128 bytes matching
`^[a-z][a-z0-9]*(?:[._/-][a-z0-9]+)*(?:[./]v[1-9][0-9]*)$`. The kernel constant is
exactly `helianthus.semantic.kernel/v1`.

### Type: DefinitionID

`DefinitionID` is an ASCII string of 3 through 160 bytes matching
`^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$`. Capability packs own their definition
IDs. The kernel validates syntax and version references but never manufactures a
domain definition.

### Type: OpaqueID

`OpaqueID` is a case-sensitive ASCII string of 1 through 256 bytes matching
`^[A-Za-z0-9][A-Za-z0-9._:/@-]*$`. It is never trimmed or case-folded. The
following are distinct aliases of `OpaqueID` and are never interchangeable:

- `AssetID`
- `SourceID`
- `SourceEpochID`
- `ClockEpochID`
- `NativeBindingID`
- `CandidateID`
- `ConflictID`
- `CapabilityInstanceID`
- `ServiceInstanceID`
- `SnapshotID`
- `BatchID`
- `IntentID`
- `AttemptID`
- `OriginID`
- `CorrelationID`
- `IdempotencyKey`
- `PolicyID`
- `TargetID`

String equality between two different aliases does not make them the same
identity. In particular, a bus address is not an `AssetID`, a source epoch is
not a driver generation, a driver generation is not a semantic revision, and a
lifecycle operation identifier is not an intent or causal correlation.

### Type: Uint64

`Uint64` is represented in JSON as a canonical decimal string matching
`0|[1-9][0-9]*` and ranging from 0 through 18446744073709551615. Sequence,
generation, revision, and monotonic values use this type so JSON decoders cannot
lose integer precision.

### Type: Int64

`Int64` is represented in JSON as a canonical decimal string matching
`0|-?[1-9][0-9]*` and ranging from -9223372036854775808 through
9223372036854775807.

### Type: SemanticVersion

`SemanticVersion` is a SemVer 2.0.0 `MAJOR.MINOR.PATCH` string. V1 definition
versions MUST contain three unsigned components without leading zeroes and MUST
NOT contain prerelease or build metadata. Ordering compares the three numeric
components.

### Type: VersionLabel

`VersionLabel` preserves an externally owned protocol, profile, firmware, or
target version without recoding it as SemVer. It is a case-sensitive ASCII
string of 1 through 128 bytes, has no control character or leading/trailing
whitespace, and is compared only for exact equality. Examples such as native
profile build labels remain native evidence; lexical order does not mean newer.

### Type: VersionRange

```go
type VersionRange struct {
    Minimum         SemanticVersion `json:"minimum"`
    MaximumExclusive SemanticVersion `json:"maximum_exclusive"`
}
```

Both versions are required, `minimum < maximum_exclusive`, and a version matches
only when `minimum <= version < maximum_exclusive`. A requirement for v1 of a
definition normally uses `1.0.0` through `2.0.0`; exact minor/patch ranges MAY
be narrower. Matching never falls back to a different definition ID.

### Type: Digest

`Digest` is exactly `sha256:` followed by 64 lowercase hexadecimal characters.
It identifies bytes under an owning contract. It is not proof that a referenced
object is public, qualified, or trustworthy. Invalid digest syntax inside an
`EvidenceRef` is `invalid_evidence`; invalid syntax on another record is
`invalid_value`; a valid but incorrect computed digest is `digest_mismatch`.

### Type: ErrorID

`ErrorID` is an ASCII string matching `^[a-z][a-z0-9_]*$`. V1 public validation
uses only the stable IDs in [acceptance.md](acceptance.md). Human-readable error
text may add context but cannot replace or change the ID.

## Evidence, source, and identity

### Type: EvidenceRef

```go
type EvidenceRef struct {
    Owner     DefinitionID    `json:"owner"`
    Kind      DefinitionID    `json:"kind"`
    Digest    Digest          `json:"digest"`
    Contract  ContractVersion `json:"contract"`
    Access    EvidenceAccess  `json:"access"`
    Redaction RedactionState  `json:"redaction"`
}
```

`EvidenceAccess` is `public`, `authorized`, or `restricted`.
`RedactionState` is `none`, `redacted`, or `metadata_only`. The record carries no
payload or locator. `access=public` MAY use any redaction state;
`access=restricted` MUST NOT use `redaction=none` in a public snapshot. A digest
does not grant access. The native owner remains responsible for the object,
authorization, retention, and redaction contract.

### Type: SourceDescriptor

```go
type SourceDescriptor struct {
    SourceID         SourceID       `json:"source_id"`
    SourceEpochID    SourceEpochID  `json:"source_epoch_id"`
    ProtocolID       DefinitionID   `json:"protocol_id"`
    ProfileID        DefinitionID   `json:"profile_id"`
    ProfileVersion   VersionLabel   `json:"profile_version"`
    RegistryEvidence EvidenceRef    `json:"registry_evidence"`
    StartedAt        TimePoint      `json:"started_at"`
    State            SourceState    `json:"state"`
    Revision         Uint64         `json:"revision"`
}
```

The native owner allocates `source_id`. It MUST allocate a new unpredictable
`source_epoch_id` whenever source sequencing can restart, state is restored
without a proved sequence continuation, or a new process/runtime assumes the
source. Profile identity and version are native evidence, not semantic
capability proof. A profile/version change creates a new source epoch. Revision
is greater than zero and orders metadata changes within one epoch. One snapshot
contains at most one `current` epoch for a given `source_id`; retired descriptors
remain resolvable and non-current.

### Type: SourceState

`SourceState` is `current` or `retired`. A publisher may upsert only `current`;
`retired` is an irreversible kernel-produced tombstone created by an accepted
source retirement. A publisher-supplied retired upsert is
`stale_source_epoch`.

### Type: OriginRef

```go
type OriginRef struct {
    OriginID      OriginID         `json:"origin_id"`
    Kind          OriginKind       `json:"kind"`
    SourceID      *SourceID        `json:"source_id,omitempty"`
    SourceEpochID *SourceEpochID   `json:"source_epoch_id,omitempty"`
    BindingID     *NativeBindingID `json:"binding_id,omitempty"`
    Evidence      []EvidenceRef    `json:"evidence"`
}
```

`OriginKind` is `native_observation`, `derived`, `operator`, `automation`, or
`projection`. Native observations require source, epoch, and binding. Derived
origins require a `Derivation` on the candidate. Operator and automation origins
omit native source fields and require authority/audit evidence. Projection
origins omit native source fields, retain the prior causal context, and require
projection evidence. Evidence contains 1 through 32 unique references. An
origin describes lineage; it never grants operation authority.

### Type: NativeBinding

```go
type NativeBinding struct {
    BindingID        NativeBindingID `json:"binding_id"`
    AssetID          AssetID         `json:"asset_id"`
    SourceID         SourceID        `json:"source_id"`
    SourceEpochID    SourceEpochID   `json:"source_epoch_id"`
    DriverGeneration Uint64          `json:"driver_generation"`
    NativeResource   EvidenceRef     `json:"native_resource"`
    State            BindingState    `json:"state"`
    Revision         Uint64          `json:"revision"`
}
```

`driver_generation` MUST be greater than zero. The native adapter allocates the
binding ID and remains the only owner of a live native handle. A binding is an
opaque route reference, never a decoded bus address. Reusing a binding ID with a
different source, source epoch, asset, or native resource is
`identity_not_qualified`. `current` resolves through a current source epoch and
an unfenced generation. `fenced` resolves through its retained generation fence;
`retired` resolves through its retained retired source descriptor. Neither
tombstone is a route or live handle.

### Type: BindingState

`BindingState` is `current`, `fenced`, or `retired`. A publisher may upsert only
`current`; `fenced` and `retired` are irreversible kernel-produced tombstones.
A publisher-supplied fenced upsert is `stale_driver_generation`; a
publisher-supplied retired upsert is `stale_source_epoch`.

### Type: IdentityLink

```go
type IdentityLink struct {
    AssetID   AssetID        `json:"asset_id"`
    BindingID NativeBindingID `json:"binding_id"`
    State     LinkState      `json:"state"`
    Basis     []EvidenceRef  `json:"basis"`
    Revision  Uint64         `json:"revision"`
}
```

`LinkState` is `candidate`, `qualified`, `rejected`, `conflict`, or `withdrawn`.
`basis` contains 1 through 32 unique evidence references. Candidate/qualified
basis proves the link; rejected/conflict basis proves that state. Automatic
withdrawal retains the prior basis and adds available transition evidence,
including generation-fence evidence. Similar values, model strings, addresses,
or topology positions cannot qualify a link. Contradictory qualified links
become `conflict`; the kernel does not choose one silently. A non-withdrawn link
must resolve a current binding. A withdrawn link must resolve a retained fenced
or retired binding tombstone, or a retained current binding when withdrawal is
an explicit identity decision. It is never identity or route authority.

### Type: SourcePathRef

```go
type SourcePathRef struct {
    BindingID        NativeBindingID `json:"binding_id"`
    SourceID         SourceID        `json:"source_id"`
    SourceEpochID    SourceEpochID   `json:"source_epoch_id"`
    DriverGeneration Uint64          `json:"driver_generation"`
}
```

A source path names one exact native dependency without carrying a live handle.
Every member must resolve to the same current `NativeBinding`. Source paths are
sorted by `(source_id,source_epoch_id,driver_generation,binding_id)` and are
unique.

### Type: DerivationInput

```go
type DerivationInput struct {
    CandidateID       CandidateID     `json:"candidate_id"`
    CandidateRevision Uint64          `json:"candidate_revision"`
    SourcePaths       []SourcePathRef `json:"source_paths"`
}
```

An input binds one exact candidate revision and every transitive native source
path on which that revision depends. An observed input has exactly one path. An
inferred input repeats the sorted union of its own derivation inputs' paths.
`source_paths` contains 1 through 32 entries. The kernel rejects an input whose
candidate revision or resolved path set differs from the referenced candidate.

### Type: Derivation

```go
type Derivation struct {
    Algorithm DefinitionID      `json:"algorithm"`
    Version   SemanticVersion   `json:"version"`
    Inputs    []DerivationInput `json:"inputs"`
    Evidence  []EvidenceRef     `json:"evidence"`
}
```

An inferred fact requires a derivation with 1 through 32 inputs, sorted by
`candidate_id`, with no duplicate candidate. The graph of candidate inputs in
one snapshot MUST be acyclic, contain at most 4096 nodes, and have maximum depth
32. Missing inputs, a revision/path mismatch, self-reference, or a cycle is
`dangling_reference` or `derivation_cycle` according to the stable error table.
An observed fact MUST omit `derivation`.

## Exact values and dimensions

### Type: Decimal

```go
type Decimal struct {
    Coefficient string `json:"coefficient"`
    Exponent10  int32  `json:"exponent10"`
}
```

`coefficient` is `0` or `-?[1-9][0-9]*`. `-0` and leading zeroes are invalid.
`exponent10` is from -18 through 18. Zero MUST use exponent 0. A non-zero
coefficient MUST NOT end in `0`; trailing decimal zeroes move into the exponent.
The represented value is `coefficient × 10^exponent10`. IEEE floating point is
never authoritative.

### Type: Symbol

```go
type Symbol struct {
    Namespace DefinitionID `json:"namespace"`
    Token     string       `json:"token"`
    Known     bool         `json:"known"`
}
```

`token` is valid NFC UTF-8, 1 through 256 bytes, with no control character.
Known symbols use a capability-pack namespace and MUST be declared by that
exact pack version. Unknown native symbols use a namespace beginning
`native.` and `known=false`; they round-trip without becoming a supported
semantic symbol or capability. `known=true` is invalid for a `native.`
namespace.

### Type: Value

```go
type Value struct {
    Kind      ValueKind  `json:"kind"`
    Quantity  *Quantity  `json:"quantity,omitempty"`
    Boolean   *bool      `json:"boolean,omitempty"`
    Text      *string    `json:"text,omitempty"`
    Symbol    *Symbol    `json:"symbol,omitempty"`
    Symbols   []Symbol   `json:"symbols,omitempty"`
    Time      *TimePoint `json:"time,omitempty"`
}

type Quantity struct {
    Number Decimal      `json:"number"`
    Unit   DefinitionID `json:"unit"`
}
```

`ValueKind` is `quantity`, `boolean`, `text`, `symbol`, `symbols`, or `time`.
Exactly one matching payload is present; every other payload is omitted. JSON
`null` is invalid. `text` is NFC UTF-8 of at most 4096 bytes without control
characters other than tab, line feed, and carriage return. A `symbols` value
contains 1 through 64 unique symbols sorted by namespace then token. A pack
defines the allowed kind, dimension, unit, range, resolution, and symbol set for
each fact or argument.

### Type: Dimension

```go
type Dimension struct {
    ID    DefinitionID `json:"id"`
    Value Value        `json:"value"`
}
```

A dimension value is restricted to `boolean`, `text`, `symbol`, or `quantity`.
One fact key contains at most 16 dimensions, sorted by `id`, with no duplicate
ID. The owning pack defines which dimensions are required and their value
contracts.

### Type: FactKey

```go
type FactKey struct {
    PackID      DefinitionID    `json:"pack_id"`
    PackVersion SemanticVersion `json:"pack_version"`
    FactID      DefinitionID    `json:"fact_id"`
    Dimensions  []Dimension     `json:"dimensions"`
}
```

The tuple of all four fields is the key. A key from one pack version is not
silently equal to the same text in another version. Packs, not the kernel,
define fact meaning.

## Time and quality axes

### Type: TimePoint

```go
type TimePoint struct {
    UnixNanoseconds Int64        `json:"unix_nanoseconds"`
    ClockID         DefinitionID `json:"clock_id"`
    UncertaintyNS   Uint64       `json:"uncertainty_ns"`
}
```

`clock_id` identifies the wall-clock realization. `clock.utc` means a UTC
estimate. Source-specific clocks use a namespaced ID and require transformation
evidence before comparison with UTC. An uncertainty of zero asserts exactness
under the owning clock contract; it is not the default for an unknown clock.

### Type: MonotonicPoint

```go
type MonotonicPoint struct {
    ClockEpochID ClockEpochID `json:"clock_epoch_id"`
    Nanoseconds  Uint64       `json:"nanoseconds"`
}
```

Monotonic points are comparable only when `clock_epoch_id` is identical.
Restarting or resetting the monotonic clock MUST allocate a new epoch. Numeric
ticks from different epochs MUST NOT be ordered or subtracted.

### Type: Times

```go
type Times struct {
    PhenomenonAt      *TimePoint      `json:"phenomenon_at,omitempty"`
    SourceAt          *TimePoint      `json:"source_at,omitempty"`
    ReceivedAt        TimePoint       `json:"received_at"`
    ReceiptMonotonic  MonotonicPoint  `json:"receipt_monotonic"`
    EvaluatedAt       TimePoint       `json:"evaluated_at"`
    EvaluateMonotonic MonotonicPoint  `json:"evaluate_monotonic"`
}
```

Missing source or phenomenon time is omitted, not synthesized. Receipt and
evaluation are required. If the monotonic epochs match, evaluation ticks MUST
be greater than or equal to receipt ticks. Wall time does not override a
backward monotonic result.

### Type: FreshnessPolicy

```go
type FreshnessPolicy struct {
    PolicyID             PolicyID       `json:"policy_id"`
    Version              SemanticVersion `json:"version"`
    FreshForNS           Uint64         `json:"fresh_for_ns"`
    RetainForNS          Uint64         `json:"retain_for_ns"`
    MaxWallUncertaintyNS Uint64         `json:"max_wall_uncertainty_ns"`
}
```

`fresh_for_ns > 0` and `retain_for_ns > fresh_for_ns`. A pack supplies the
policy; the kernel evaluates it. Within one monotonic epoch, elapsed time is the
tick difference. Across epochs, the kernel may use `clock.utc` wall points only
when the sum of receipt and evaluation uncertainty is no greater than
`max_wall_uncertainty_ns`.

For cross-epoch wall evaluation, let `d` be the wall-time difference and `u` the
sum of uncertainties. The conservative elapsed interval is
`[max(0,d-u), d+u]`:

- `fresh` only when its upper bound is less than `fresh_for_ns`;
- `stale` only when its lower bound is at least `fresh_for_ns` and its upper
  bound is less than `retain_for_ns`;
- `expired` only when its lower bound is at least `retain_for_ns`;
- otherwise `unknown`.

All duration arithmetic is checked. Signed/unsigned overflow, a negative wall
delta outside the stated uncertainty, or an interval beyond the supported
integer range is `invalid_time`; it never wraps.

When wall clocks are not comparable or uncertainty exceeds the policy, restart
restoration yields `freshness=unknown` and at most `availability=degraded` until
a new observation arrives. It never resets a retained fact to `fresh` merely
because a new monotonic epoch started.

### Type: EvaluationContext

```go
type EvaluationContext struct {
    EvaluatedAt       TimePoint     `json:"evaluated_at"`
    EvaluateMonotonic MonotonicPoint `json:"evaluate_monotonic"`
}
```

The root package exposes a pure operation equivalent to
`EvaluateSnapshot(Snapshot, EvaluationContext) (EvaluationView, error)`. The
caller supplies a trusted current wall estimate and monotonic point. Evaluation
fails with `invalid_time` when the context is earlier than the snapshot under a
comparable clock, and uses the `FreshnessPolicy` rules above for every retained
candidate. It never reads a process clock implicitly.

### Type: EvaluatedFact

```go
type EvaluatedFact struct {
    CandidateID          CandidateID   `json:"candidate_id"`
    CandidateRevision    Uint64        `json:"candidate_revision"`
    Freshness            Freshness     `json:"freshness"`
    EffectiveAvailability Availability `json:"effective_availability"`
}
```

For an observed candidate, `freshness` is evaluated from its receipt time to the
supplied context. For an inferred candidate, the kernel evaluates the candidate
and every transitive `DerivationInput`, then combines them deterministically:
`expired` wins; otherwise `unknown` wins; otherwise `stale` wins; otherwise the
result is `fresh`. This preserves all source paths while preventing a fresh
derived view from outliving an input.

Effective availability starts with the candidate's stored availability.
`withdrawn` stays `withdrawn`; `expired` caps every other state at `unavailable`;
`stale` or `unknown` changes `available` to `degraded`; and an already degraded
or unavailable state never improves. Evaluation cannot promote, qualify, or
restore a candidate.

### Type: EvaluationView

```go
type EvaluationView struct {
    Contract         ContractVersion `json:"contract"`
    SnapshotID       SnapshotID      `json:"snapshot_id"`
    Revisions        RevisionVector  `json:"revisions"`
    Context          EvaluationContext `json:"context"`
    Facts            []EvaluatedFact `json:"facts"`
    EvaluationDigest Digest          `json:"evaluation_digest"`
}
```

`contract` is exactly `helianthus.semantic.evaluation/v1`. Facts are sorted by
candidate ID and cover every candidate in the snapshot exactly once. The digest
is SHA-256 over canonical view JSON with `evaluation_digest` omitted. Evaluation
creates no publication: the source snapshot ID, revision vector, candidates,
stored quality, and canonical snapshot bytes remain byte-identical. Repeating
evaluation with the same snapshot and context produces identical view bytes.

Operation admission MUST evaluate the admitted snapshot with a trusted current
context immediately before checking preconditions and selecting a route. It then
applies the exact candidate binding and all six eligibility axes defined by
`Precondition`; it cannot search for a different candidate that makes a predicate
true. This re-evaluation does not relax the intent's expected snapshot revisions.

### Type: Quality

```go
type Quality struct {
    Assertion     AssertionKind `json:"assertion"`
    Qualification Qualification `json:"qualification"`
    Promotion     Promotion     `json:"promotion"`
    Validity      Validity      `json:"validity"`
    Availability Availability  `json:"availability"`
    Freshness     Freshness     `json:"freshness"`
    Reasons       []DefinitionID `json:"reasons"`
}
```

The axes are independent and are never collapsed into one status:

- `AssertionKind`: `observed` or `inferred`;
- `Qualification`: `candidate`, `qualified`, `unsupported`, `unknown`, or
  `rejected`;
- `Promotion`: `unpromoted` or `promoted`;
- `Validity`: `good`, `suspect`, `bad`, or `unknown`;
- `Availability`: `available`, `degraded`, `unavailable`, or `withdrawn`;
- `Freshness`: `fresh`, `stale`, `expired`, or `unknown`.

`reasons` contains at most 16 unique sorted namespaced codes. An inferred value
requires `Derivation`; an observed value forbids it. `promotion=promoted`
requires `qualification=qualified`, `validity` of `good` or `suspect`, and
`availability` of `available` or `degraded`. `unsupported` and `rejected`
forbid a value and promotion. `withdrawn` forbids a value. `unknown` may retain
an observed opaque native symbol but cannot be promoted or satisfy a capability.

## Facts, alternatives, and conflicts

### Type: FactCandidate

```go
type FactCandidate struct {
    CandidateID      CandidateID      `json:"candidate_id"`
    Key              FactKey         `json:"key"`
    Value            *Value          `json:"value,omitempty"`
    Quality          Quality         `json:"quality"`
    Times            Times           `json:"times"`
    FreshnessPolicy  FreshnessPolicy `json:"freshness_policy"`
    BindingID        *NativeBindingID `json:"binding_id,omitempty"`
    SourceEpochID    *SourceEpochID    `json:"source_epoch_id,omitempty"`
    DriverGeneration *Uint64           `json:"driver_generation,omitempty"`
    Origin           OriginRef        `json:"origin"`
    Causal           *CausalContext   `json:"causal,omitempty"`
    Evidence         []EvidenceRef    `json:"evidence"`
    Derivation       *Derivation      `json:"derivation,omitempty"`
    Revision         Uint64           `json:"revision"`
}
```

Evidence contains 1 through 32 unique references and `revision` is greater than
zero. An observed candidate requires binding, source epoch, and driver
generation; the generation is greater than zero and all three fields resolve to
one current binding. It omits `derivation`. An inferred candidate omits those
three single-path fields and requires a `Derivation`; its typed inputs preserve
every native source path, so it never invents or arbitrarily selects a synthetic
binding. A candidate value is required except where `Quality` forbids it. Origin
and causal context survive projection and derived facts; they do not grant
command authority.

`revision` increments whenever the key, value, quality, times, binding path,
origin, causal context, evidence, or derivation changes. Retaining a candidate in
a later snapshot preserves both its revision and observation times. A producer
cannot rewrite receipt/evidence as post-dispatch without a new candidate revision
and new native evidence.

### Type: Selection

```go
type Selection struct {
    Contract           ContractVersion `json:"contract"`
    SnapshotID         SnapshotID      `json:"snapshot_id"`
    Revisions          RevisionVector  `json:"revisions"`
    EvaluationDigest   Digest          `json:"evaluation_digest"`
    Context            EvaluationContext `json:"context"`
    Key                FactKey         `json:"key"`
    PolicyID           PolicyID        `json:"policy_id"`
    PolicyVersion      SemanticVersion `json:"policy_version"`
    SelectedCandidate  CandidateID    `json:"selected_candidate"`
    CandidateRevision  Uint64          `json:"candidate_revision"`
    PresentationOnly   bool           `json:"presentation_only"`
}
```

`Selection` is not stored in `Snapshot` or `FactEnvelope`. The root package
exposes a pure operation equivalent to
`SelectPresentation(Snapshot, EvaluationView, FactKey, PolicyID,
SemanticVersion) (Selection, error)`. It validates both immutable inputs before
policy dispatch: the view digest is recomputed; snapshot IDs and complete
revision vectors match; every evaluated candidate ID/revision corresponds
exactly once to a snapshot candidate; and no snapshot candidate is omitted. It
then resolves exactly one envelope by canonical `FactKey` equality and passes
that envelope plus only its matching evaluated facts to the policy hook.

`contract` is exactly `helianthus.semantic.selection/v1` and
`presentation_only` MUST be true. The result repeats the matched snapshot ID,
revision vector, complete evaluation context and digest. The selected candidate
and revision must belong to the requested envelope and its evaluated subset.
Native publication cannot register or choose the cross-source policy. A
selection is valid only for its named snapshot and evaluation; any later
publication or evaluation requires a new result. Selection does not remove
alternatives, resolve identity, choose an operation route, or retain capability
authority.

### Type: SelectionPolicy

```go
type SelectionPolicy interface {
    PolicyID() PolicyID
    Version() SemanticVersion
    Select(FactEnvelope, []EvaluatedFact) (CandidateID, error)
}
```

The kernel registers each `(policy_id,version)` exactly once and invokes one
exact match. Duplicate registration is `definition_owner_conflict`; absence is
`definition_owner_missing`. The hook receives the full immutable candidates,
values, stored quality, provenance, derivation and derived conflicts through the
envelope, plus the matching sorted freshness/availability results. It is pure:
no process clock, mutable snapshot store, registration-order probing, native
lookup or external I/O. Repeating identical canonical inputs MUST select the
same candidate. A returned candidate outside the supplied envelope/evaluated
subset is `invalid_value`. The kernel, not the policy, constructs every other
`Selection` field from the validated inputs. A policy that cannot select one
candidate returns `invalid_value`; omission or multiple results are not a valid
selection.

A malformed evaluation digest is `invalid_value`; a valid digest that does not
match the evaluation bytes is `digest_mismatch`. A snapshot ID, revision vector,
evaluation context or evaluated candidate revision mismatch is
`revision_conflict`. A missing requested key or candidate reference is
`dangling_reference`.

### Type: Conflict

```go
type Conflict struct {
    ConflictID ConflictID    `json:"conflict_id"`
    Kind       ConflictKind  `json:"kind"`
    Candidates []CandidateID `json:"candidates"`
    Evidence   []EvidenceRef `json:"evidence"`
    State      ConflictState `json:"state"`
}
```

`ConflictKind` is exactly `value` and `ConflictState` is exactly `open` in v1.
A conflict contains 2 through 32 unique sorted candidate IDs. `evidence`
contains the sorted, deduplicated union of their candidate evidence and therefore
has 1 through 1024 references.

Identity disagreement remains explicit in `IdentityLink.state=conflict`;
source differences remain in candidate lineage; pack-version differences remain
in `FactKey`; and operation ambiguity is rejected during route admission. Those
axes do not create underspecified publisher-authored `FactEnvelope` conflicts.

After applying all explicit fact changes and lifecycle/derivation cascades, the
kernel reconciles each affected envelope. It takes candidates with a value,
`qualification=qualified`, and `promotion=promoted`. When their canonical value
bytes contain at least two distinct values, it emits one open value conflict
containing every candidate in that set. Its `conflict_id` is the `sha256:` digest
of JCS bytes for `{contract,asset_id,key,kind,candidates}`, with `contract`
exactly `helianthus.semantic.conflict-id/v1`. Otherwise the current envelope
contains no conflict. Native publishers never submit, resolve, or select
cross-source conflict metadata.

Withdrawal, fencing, dependency cascade, or candidate revision change reruns
this rule against the complete resulting candidate set. A conflict whose
condition no longer holds is absent from the new current snapshot; it is not
rewritten as `resolved` and no resolution evidence is fabricated. The immutable
prior snapshot remains the history of the former conflict.

### Type: FactEnvelope

```go
type FactEnvelope struct {
    AssetID   AssetID        `json:"asset_id"`
    Key       FactKey        `json:"key"`
    Candidates []FactCandidate `json:"candidates"`
    Conflicts []Conflict     `json:"conflicts"`
    Revision  Uint64         `json:"revision"`
}
```

One envelope holds 1 through 32 candidates with unique IDs, sorted by
`candidate_id`. Candidates for the same key coexist. `conflicts` is exactly the
kernel-derived result above and is never a publisher input. The kernel cannot
silently choose one. `revision` increments exactly once in a batch whenever its
candidate set/revision/content or derived conflict changes; otherwise it is
retained unchanged. A decoded snapshot whose conflict IDs, candidate set,
evidence union, state, or order differs from the derived result is
`invalid_value`.

## Services and capabilities

### Type: PackRef

```go
type PackRef struct {
    ID      DefinitionID    `json:"id"`
    Version SemanticVersion `json:"version"`
}
```

A pack reference is the exact registry key. Pack IDs and versions are explicit;
they are never parsed from a definition ID.

### Type: DefinitionRef

```go
type DefinitionRef struct {
    Pack    PackRef         `json:"pack"`
    ID      DefinitionID    `json:"id"`
    Version SemanticVersion `json:"version"`
}
```

Every service, capability, operation, effect rule, and typed field definition
uses this record. The definition's pack must match its one registered owner.

### Type: DefinitionIndex

```go
type DefinitionIndex struct {
    Pack         PackRef         `json:"pack"`
    Fields       []DefinitionRef `json:"fields"`
    Services     []DefinitionRef `json:"services"`
    Capabilities []DefinitionRef `json:"capabilities"`
    Operations   []DefinitionRef `json:"operations"`
    EffectRules  []DefinitionRef `json:"effect_rules"`
}
```

Each collection is sorted by `(id,version)`, has no duplicate, and every member's
`pack` equals `DefinitionIndex.pack`. Across the complete registry, the tuple
`(definition kind,id,version)` has exactly one owner. A duplicate tuple, a
validator whose `Pack()` differs from its index, or a definition listed under the
wrong kind is `definition_owner_conflict`. A referenced tuple absent from its
declared pack/index or a pack without its validator is
`definition_owner_missing`. Registration order and identifier spelling never
alter lookup.

### Type: TypedField

```go
type TypedField struct {
    ID    DefinitionID `json:"id"`
    Value Value        `json:"value"`
}
```

`TypedField` is used only where an accepted capability pack declares the field,
its value kind, unit, range, and required presence. Collections contain at most
64 fields, sorted by ID, with no duplicates.

### Type: PredicateOp

`PredicateOp` is the root-package string enum `equal`, `not_equal`, `less`,
`less_equal`, `greater`, `greater_equal`, or `contains`. A pack validator must
reject operators or value/unit combinations that its exact fact definition does
not support.

### Type: ServiceInstance

```go
type ServiceInstance struct {
    InstanceID       ServiceInstanceID `json:"instance_id"`
    AssetID          AssetID           `json:"asset_id"`
    Definition       DefinitionRef      `json:"definition"`
    BindingID        NativeBindingID   `json:"binding_id"`
    SourceEpochID    SourceEpochID      `json:"source_epoch_id"`
    DriverGeneration Uint64             `json:"driver_generation"`
    Qualification    Qualification      `json:"qualification"`
    Availability     Availability       `json:"availability"`
    Revision         Uint64             `json:"revision"`
}
```

### Type: CapabilityInstance

```go
type CapabilityInstance struct {
    InstanceID       CapabilityInstanceID `json:"instance_id"`
    AssetID          AssetID              `json:"asset_id"`
    ServiceInstance  ServiceInstanceID    `json:"service_instance"`
    Definition       DefinitionRef         `json:"definition"`
    BindingID        NativeBindingID      `json:"binding_id"`
    SourceEpochID    SourceEpochID         `json:"source_epoch_id"`
    DriverGeneration Uint64                `json:"driver_generation"`
    Qualification    Qualification         `json:"qualification"`
    Availability     Availability          `json:"availability"`
    Constraints      []TypedField          `json:"constraints"`
    ActivationEvidence []EvidenceRef       `json:"activation_evidence"`
    Revision         Uint64                `json:"revision"`
}
```

Service and capability `driver_generation` and `revision` are greater than zero.
When availability is not `withdrawn`, their asset, binding, source epoch,
generation, and service references must all resolve to the same `current` source
path in one snapshot. A withdrawn service/capability instead resolves to the
same retained binding, which may be `current`, `fenced`, or `retired`; a
withdrawn capability's service must remain resolvable, and must itself be
withdrawn when the binding is not current. Constraints are unique and sorted.
Each definition resolves through its explicit `DefinitionRef.pack` and the
matching service/capability definition index. Activation evidence contains 1
through 32 unique references and remains historical evidence on a tombstone.

An actionable capability is exactly one instance whose definition pack, ID, and
version match the request, `qualification=qualified`, availability is
`available` or explicitly permitted `degraded`, binding/source/generation are
current, activation evidence is non-empty, and every constraint admits the
arguments. Catalog completeness cannot create an instance. A pack or native
mapping decides which degraded capabilities remain actionable; absence of that
decision means unavailable.

## Publication, fencing, and immutable snapshots

### Type: GenerationFence

```go
type GenerationFence struct {
    SourceID         SourceID       `json:"source_id"`
    SourceEpochID    SourceEpochID  `json:"source_epoch_id"`
    DriverGeneration Uint64         `json:"driver_generation"`
    Reason           DefinitionID   `json:"reason"`
    Evidence         []EvidenceRef  `json:"evidence"`
    Revision         Uint64         `json:"revision"`
}
```

A fence is monotonic and irreversible for its source epoch and generation.
Accepting a fence happens before publication of the resulting snapshot. Every
binding from that generation is retained as `state=fenced`; its identity links
are retained as `state=withdrawn`; its services and capabilities are retained as
`availability=withdrawn`. Their object revisions increment exactly once. Their
references resolve through the retained binding and fence but are non-actionable.
Observed candidates and the transitive derived-dependency closure are removed
from the new current snapshot, affected envelope metadata is reconciled, and
empty fact envelopes are removed. Historical snapshots retain every pre-fence
record.

Late batches, readbacks, and operation admission for that generation fail. The
native owner must reject every guarded callback at the same boundary, including
one already selected but not yet invoked. The semantic changes, derived closure,
and callback fence are one publication-versus-admission happens-before boundary.
The kernel never closes the native handle itself.

### Type: PublicationBatch

```go
type PublicationBatch struct {
    Contract                 ContractVersion       `json:"contract"`
    BatchID                  BatchID               `json:"batch_id"`
    BatchDigest              Digest                `json:"batch_digest"`
    AssetID                  AssetID               `json:"asset_id"`
    SourceID                 SourceID              `json:"source_id"`
    SourceEpochID            SourceEpochID         `json:"source_epoch_id"`
    DriverGeneration         Uint64                `json:"driver_generation"`
    Sequence                 Uint64                `json:"sequence"`
    ExpectedSemanticRevision Uint64                `json:"expected_semantic_revision"`
    ObservedAt               TimePoint             `json:"observed_at"`
    SourceUpserts            []SourceDescriptor    `json:"source_upserts"`
    SourceRetirements        []SourceEpochID        `json:"source_retirements"`
    BindingUpserts           []NativeBinding       `json:"binding_upserts"`
    IdentityLinkUpserts      []IdentityLink        `json:"identity_link_upserts"`
    FactUpserts              []FactCandidate       `json:"fact_upserts"`
    FactWithdrawals          []CandidateID         `json:"fact_withdrawals"`
    ServiceUpserts           []ServiceInstance     `json:"service_upserts"`
    ServiceWithdrawals       []ServiceInstanceID   `json:"service_withdrawals"`
    CapabilityUpserts        []CapabilityInstance  `json:"capability_upserts"`
    CapabilityWithdrawals    []CapabilityInstanceID `json:"capability_withdrawals"`
    GenerationFences         []GenerationFence     `json:"generation_fences"`
}
```

The batch is one atomic change for one asset/source/epoch/generation. Collection
members are unique and canonically sorted. `batch_digest` is the digest of the
canonical JSON record with the `batch_digest` member omitted. Sequence is
strictly increasing for `(source_id, source_epoch_id, driver_generation)`.
Replaying an identical sequence and digest returns the prior result without a
new revision. Reusing a sequence with different bytes is `sequence_conflict`.

Every observed upsert and withdrawal belongs to the header asset, source, epoch,
and generation, except an explicit source retirement or a fence of an older
generation under the same source. An inferred fact upsert belongs to the header
asset but derives lifecycle from its typed input paths; the batch header orders
the publishing attempt and does not become a synthetic native dependency.
Cross-asset changes require a separate batch and cannot be partially committed
together.

`expected_semantic_revision` must equal the current asset revision. Any invalid
member, stale source epoch, fenced generation, revision mismatch, or withdrawal
of an unknown ID rejects the complete batch without mutation. Fields absent from
the batch remain unchanged. Partial reads therefore upsert only evidenced
candidates; they do not erase unrelated facts. Withdrawal is explicit except for
the source-retirement, generation-fence, and derived-dependency cascades defined
here.

Source upserts and retirements refer only to the batch `source_id`. A new source
epoch is added before its bindings or facts. Retiring the current epoch retains
its descriptor as `state=retired`, retains its bindings as `state=retired`, and
retains its identity links/services/capabilities as withdrawn tombstones while
atomically removing its observed candidates and derived closure. Every changed
object revision and affected component revision increments once. A retired epoch
cannot be reactivated. Historical immutable snapshots retain its earlier active
state. Replacing an active epoch requires its retirement and the new current
descriptor in the same batch.

Before committing a batch, the kernel computes the transitive closure of inferred
candidates whose `DerivationInput` no longer resolves exactly after the proposed
change. Withdrawal of an input, source retirement, generation fence, binding
invalidation caused by either transition, or candidate revision change
automatically withdraws every affected derived candidate and its dependents in
the same snapshot. A same-batch inferred upsert survives only when all of its
revised inputs and exact source paths resolve after the complete batch. Empty
fact envelopes are removed.

After that closure, the kernel derives current conflict metadata for every
affected non-empty envelope using the exact rule above. This reconciliation is
part of batch application rather than a publisher field. A candidate removal or
revision therefore cannot leave a current conflict pointing at a missing or old
revision, and native publishers cannot acquire cross-source selection or
resolution authority.

This dependency cascade is part of the one atomic batch. Each changed envelope
revision and the fact component revision increments once, while the semantic
revision increments once for the batch regardless of cascade size. No separate
native batch, invented binding, or later cleanup window is permitted. Time-only
aging does not run this publication cascade; `EvaluationView` computes effective
freshness and availability without changing the immutable snapshot.

An available capability upsert is valid only after native activation has
completed for the referenced current generation. Publication of that upsert
happens before a snapshot exposes it as actionable. A fence happens before all
withdrawals for its generation in the same atomic commit. New publication after
a restart uses a new source epoch unless sequence continuity is proved.

Every fence in a batch uses the same source and epoch as its owning descriptor
and contains 1 through 32 unique evidence references. A batch that fences its
own header generation cannot upsert a binding, fact, service, or capability for
that generation.

At most one generation for a `(source_id,source_epoch_id)` is unfenced and
current. A first generation needs no supersession fence. A batch whose header
generation is greater than the current generation MUST include a
`GenerationFence` for every older unfenced generation. Omitting any required
fence is `generation_transition_incomplete`; the batch changes no state. The
transition fence performs all automatic withdrawals and callback rejection
before the same atomic snapshot exposes activated records for the new generation.
Explicit per-record withdrawals MAY repeat the same transition intent but cannot
replace the required fence. A generation below the current one is
`stale_driver_generation` and a fenced generation can never become current again.
The old source descriptor remains current, its old bindings are retained as
fenced tombstones, and the withdrawn link/service/capability records remain
resolvable through those tombstones. The semantic revision increments once;
every identity/fact/service/capability component changed by supersession
increments its component revision once.

### Type: RevisionVector

```go
type RevisionVector struct {
    Semantic   Uint64 `json:"semantic"`
    Identity   Uint64 `json:"identity"`
    Facts      Uint64 `json:"facts"`
    Services   Uint64 `json:"services"`
    Capabilities Uint64 `json:"capabilities"`
}
```

Each value is monotonic per asset and greater than zero in a published snapshot.
`semantic` increments once for every accepted non-idempotent batch. Component
revisions increment only when that component changes.

### Type: PublicationCursor

```go
type PublicationCursor struct {
    SourceID         SourceID      `json:"source_id"`
    SourceEpochID    SourceEpochID `json:"source_epoch_id"`
    DriverGeneration Uint64        `json:"driver_generation"`
    LastSequence     Uint64        `json:"last_sequence"`
    LastBatchDigest  Digest        `json:"last_batch_digest"`
    Fenced           bool          `json:"fenced"`
}
```

One cursor exists for each retained source/epoch/generation. Sequence begins at
1. An identical replay is accepted only for the cursor's `last_sequence` and
`last_batch_digest`; any smaller sequence is `sequence_conflict`. Driver
generation strictly increases within one source epoch and never resets.
`fenced=true` is irreversible. A new source epoch starts a new sequence and
generation domain; the prior epoch remains stale even if its numbers are larger.

### Type: Snapshot

```go
type Snapshot struct {
    Contract       ContractVersion      `json:"contract"`
    SnapshotID     SnapshotID           `json:"snapshot_id"`
    AssetID        AssetID              `json:"asset_id"`
    Revisions      RevisionVector       `json:"revisions"`
    EvaluatedAt    TimePoint            `json:"evaluated_at"`
    EvaluateMonotonic MonotonicPoint    `json:"evaluate_monotonic"`
    Sources        []SourceDescriptor   `json:"sources"`
    Bindings       []NativeBinding      `json:"bindings"`
    IdentityLinks  []IdentityLink       `json:"identity_links"`
    Facts          []FactEnvelope       `json:"facts"`
    Services       []ServiceInstance    `json:"services"`
    Capabilities   []CapabilityInstance `json:"capabilities"`
    Fences         []GenerationFence    `json:"fences"`
    Cursors        []PublicationCursor  `json:"cursors"`
}
```

A snapshot is immutable, self-consistent, and complete for one asset at one
semantic revision. It contains all alternatives and current open conflicts.
Every reference resolves inside the snapshot or to an `EvidenceRef`. Current
facts and actionable identity/service/capability records resolve only through
current source/binding paths. Withdrawn identity/service/capability records
remain non-actionable and resolve through a retained binding; a non-current
binding must resolve through its fence or retired source descriptor. Collections
are sorted by their primary ID/key and contain no duplicate. A `CandidateID` is
unique across all fact envelopes in one snapshot. Limits are 32 sources, 128
bindings, 128 identity links, 4096 fact
envelopes, 1024 services, 2048 capabilities, and 128 retained fences per asset.
Exceeding a limit rejects the batch; it never truncates a snapshot. Up to 128
publication cursors are retained while their source epochs remain relevant to
replay/fence validation.

The snapshot ID is unique for the exact canonical bytes. A reader either sees
the complete prior snapshot or complete new snapshot. It never observes mixed
identity, fact, service, capability, or fence revisions.

`evaluated_at` and `evaluate_monotonic` record the publication-time evaluation
stored in these immutable bytes. Passage of time never mutates this snapshot or
increments a revision. A caller obtains current freshness through
`EvaluateSnapshot`; an operation cannot rely on the stored publication-time
freshness without that admission-time evaluation.

## Operations and guarded admission

### Type: CausalContext

```go
type CausalContext struct {
    Origin              OriginRef      `json:"origin"`
    CorrelationID       CorrelationID  `json:"correlation_id"`
    ParentCorrelationID *CorrelationID `json:"parent_correlation_id,omitempty"`
    HopCount            uint16         `json:"hop_count"`
    MaxHops             uint16         `json:"max_hops"`
    FirstSeenAt         TimePoint      `json:"first_seen_at"`
    ExpiresAt           TimePoint      `json:"expires_at"`
    Path                []TargetID     `json:"path"`
}
```

`max_hops` is from 1 through 16; `hop_count <= max_hops`; path length equals
`hop_count` and has no repeated target. `first_seen_at` and `expires_at` use
`clock.utc`, and expiry is no more than 300 seconds after first seen. `path`
contains the target processors that have successfully entered the causal chain,
in entry order. A context created inside target A starts as `path=[A]` and
`hop_count=1`; an external context before its first target starts empty at zero.

Egress never changes path or hop count. On ingress at receiver R, the receiver
performs this exact order atomically: validate the incoming count/path/expiry;
reject `echo_suppressed` when R is already in path; reject
`causal_budget_exceeded` when appending R would exceed `max_hops`; then append R,
increment `hop_count`, and process or later emit the updated context. Thus A emits
`[A]/1` to B, B accepts and holds `[A,B]/2`, B emits that unchanged context to C,
and C accepts and holds `[A,B,C]/3`. A reflection from C to A is rejected because
A is already present; no path member is appended on rejection.

A reflected observation cannot create an intent or authority. An independent
authorized intent with a new intent ID, idempotency key, and correlation ID
remains admissible even when it requests the same value.

### Type: CapabilityRequirement

```go
type CapabilityRequirement struct {
    Pack         PackRef              `json:"pack"`
    DefinitionID DefinitionID          `json:"definition_id"`
    Versions     VersionRange          `json:"versions"`
    InstanceID   *CapabilityInstanceID `json:"instance_id,omitempty"`
    AllowDegraded bool                 `json:"allow_degraded"`
}
```

The requirement matches only capability definitions owned by the exact pack.
Neither the definition ID nor version range can select another pack.

### Type: Precondition

```go
type Precondition struct {
    Fact              FactKey     `json:"fact"`
    CandidateID       CandidateID `json:"candidate_id"`
    CandidateRevision Uint64      `json:"candidate_revision"`
    Operator          PredicateOp `json:"operator"`
    Expected          Value       `json:"expected"`
}
```

The fact key, candidate ID, and candidate revision select exactly one candidate
in one envelope of the admitted snapshot. Equal numeric revisions on another
candidate never match this reference.

`FactKey.pack_id` and `pack_version` dispatch predicate validation to exactly one
registered `PackRef` and its `EvaluatePredicate` hook; prefix inference and
validator probing are forbidden. A missing exact fact-pack validator is
`definition_owner_missing`.

The selected candidate MUST be `qualification=qualified`,
`promotion=promoted`, `validity=good`, evaluated `fresh`, effectively
`availability=available`, and absent from every open conflict. The predicate is
applied only to that candidate. Candidate/unpromoted/suspect/bad/unknown,
stale/expired/degraded/unavailable/withdrawn, missing/revision-changed, or
open-conflict evidence is `precondition_failed`; the kernel MUST NOT search
another same-key candidate or use a presentation selection as fallback.

### Type: ExpectedEffect

```go
type ExpectedEffect struct {
    Rule     DefinitionRef `json:"rule"`
    Fact     FactKey       `json:"fact"`
    Operator PredicateOp   `json:"operator"`
    Expected Value         `json:"expected"`
}
```

`ExpectedEffect` is a required part of the intent's canonical bytes. The
operation pack owns the rule that translates the exact operation and arguments
into this typed fact predicate. `ValidateIntent` MUST derive the expected rule,
fact, operator, and value and require byte-identical fields; caller assertion is
insufficient, and a mismatch is `invalid_value`. `rule.pack` MUST equal
`Intent.kind.pack` and the rule MUST be
present in that pack's `effect_rules` index. The fact may belong to another
explicit pack; this does not transfer ownership of its meaning.

### Type: OperationPackValidator

The operation package exposes this extension of the root pack boundary:

```go
type OperationPackValidator interface {
    v1.PackValidator
    ValidateIntent(Intent) error
    EvaluateReadback(Intent, v1.FactCandidate) (ReadbackRelation, error)
}
```

Any pack that indexes an operation or effect rule MUST implement this interface.
Admission dispatches directly through `Intent.kind.pack`, verifies the indexed
operation and effect rule, then calls `ValidateIntent`. It never probes another
validator. `EvaluateReadback` receives the unchanged admitted intent and the
exact resolved observed candidate named by `Readback`; it MUST reject a candidate
whose `FactKey` differs from `Intent.expected_effect.fact`, then apply the
pack-owned rule/operator/value and return the computed relation. The serialized
`Readback.relation` must equal that result. Missing hooks or index entries are
`definition_owner_missing`; a caller-provided `confirms` token is never evidence
by itself.

These are ordinary typed software 0.7 interfaces. They do not introduce a
descriptive language, IR, generated validator, or code-generation dependency;
those remain 0.8 work.

### Type: Intent

```go
type Intent struct {
    Contract                   ContractVersion       `json:"contract"`
    IntentID                   IntentID              `json:"intent_id"`
    Kind                       DefinitionRef          `json:"kind"`
    ExpectedEffect             ExpectedEffect         `json:"expected_effect"`
    AssetID                    AssetID               `json:"asset_id"`
    Arguments                  []TypedField           `json:"arguments"`
    RequiredCapability         CapabilityRequirement `json:"required_capability"`
    Authority                  EvidenceRef            `json:"authority"`
    Causal                     CausalContext           `json:"causal"`
    ExpectedSemanticRevision   Uint64                 `json:"expected_semantic_revision"`
    ExpectedCapabilityRevision Uint64                 `json:"expected_capability_revision"`
    ExpectedCapabilityInstanceRevision Uint64         `json:"expected_capability_instance_revision"`
    ExpectedSourceEpochID      SourceEpochID          `json:"expected_source_epoch_id"`
    ExpectedDriverGeneration   Uint64                 `json:"expected_driver_generation"`
    Preconditions              []Precondition         `json:"preconditions"`
    IdempotencyKey             IdempotencyKey         `json:"idempotency_key"`
    Deadline                   TimePoint               `json:"deadline"`
}
```

Authority is an opaque evidence reference resolved by the runtime's authority
owner; presence alone never grants permission. The deadline uses `clock.utc`.
Arguments and preconditions contain at most 64 entries. Arguments are sorted by
field ID. Preconditions are sorted by `(canonical fact key,candidate_id,
candidate_revision)` and contain no duplicate tuple. An idempotency key
deduplicates the same validated intent and outcome; it does not make a native
operation replay-safe.

`expected_capability_revision` binds `RevisionVector.capabilities`.
`expected_capability_instance_revision` binds the one matched instance. Both
must still match immediately before guarded dispatch.

### Type: Route

```go
type Route struct {
    CapabilityInstance CapabilityInstanceID `json:"capability_instance"`
    ServiceInstance    ServiceInstanceID    `json:"service_instance"`
    BindingID           NativeBindingID      `json:"binding_id"`
    SourceID            SourceID             `json:"source_id"`
    SourceEpochID       SourceEpochID        `json:"source_epoch_id"`
    DriverGeneration    Uint64                `json:"driver_generation"`
}
```

Admission revalidates authority, deadline, causal budget, preconditions,
expected revisions, exact source epoch/generation, capability qualification and
availability, version range, and constraints against one immutable snapshot. It
also resolves the operation, expected effect, required capability, fields, and
fact predicates through their one exact pack/index/hook. It must produce exactly
one route or fail before dispatch. Every route field resolves through a
`current` source descriptor and `current` binding; fenced/retired tombstones and
withdrawn records can never form a route. Presentation `Selection`,
compatibility aliases, projections, or caller-supplied native IDs cannot select
the route.

The runtime owns the admitted, generation-bound guarded callback. It MUST
revalidate the current generation and fence under its lifecycle lock immediately
before invoking the native adapter, return a release function, and keep the
native adapter as sole handle owner. These runtime mechanics are specified in
INT-06; no gateway type is imported into this kernel.

### Type: DispatchEvidence

```go
type DispatchEvidence struct {
    AttemptID          AttemptID         `json:"attempt_id"`
    Started            EvaluationContext `json:"started"`
    Completed          *EvaluationContext `json:"completed,omitempty"`
    Delivery           DeliveryState     `json:"delivery"`
    PossibleSideEffect bool              `json:"possible_side_effect"`
    Evidence           []EvidenceRef     `json:"evidence"`
}
```

`DeliveryState` is `not_sent`, `sent`, or `unknown`. `not_sent` requires
`possible_side_effect=false`; `sent` or `unknown` may require true unless native
evidence proves no effect. `started` and optional `completed` carry explicit wall
and monotonic contexts; completion cannot precede start under the same-epoch or
uncertainty-aware cross-epoch ordering used for readback. Dispatch completion is
not protocol acknowledgement.

### Type: Acknowledgement

```go
type Acknowledgement struct {
    State    AckState      `json:"state"`
    At       TimePoint     `json:"at"`
    Evidence []EvidenceRef `json:"evidence"`
}
```

`AckState` is `accepted`, `rejected`, or `provisional`. An acknowledgement is
native protocol evidence; it is not confirming readback.

### Type: Readback

```go
type Readback struct {
    SnapshotID        SnapshotID       `json:"snapshot_id"`
    Revisions         RevisionVector   `json:"revisions"`
    CandidateID       CandidateID      `json:"candidate_id"`
    CandidateRevision Uint64           `json:"candidate_revision"`
    BindingID         NativeBindingID  `json:"binding_id"`
    SourceID          SourceID         `json:"source_id"`
    SourceEpochID     SourceEpochID    `json:"source_epoch_id"`
    DriverGeneration  Uint64           `json:"driver_generation"`
    Relation          ReadbackRelation  `json:"relation"`
    Evaluation        EvaluationContext `json:"evaluation"`
    Evidence          []EvidenceRef     `json:"evidence"`
}
```

`ReadbackRelation` is `confirms`, `contradicts`, or `inconclusive`. The exact
snapshot must still be retrievable, its semantic revision must be greater than
the admitted semantic revision, and it must contain the named observed candidate
at exactly `candidate_revision`. The candidate's binding, source, source epoch,
and driver generation must equal these fields, resolve within that snapshot, and
equal the admitted `Route`.

For `applied`, dispatch must be `sent` and include `Dispatch.completed`. The
resolved candidate's `Times.received_at`/`receipt_monotonic` must prove a new
observation strictly after that completed dispatch boundary. When monotonic
epochs match, receipt ticks MUST be greater than completed ticks. Across epochs,
both wall points must use `clock.utc` and the earliest plausible receipt
(`received_at - uncertainty`) MUST be greater than the latest plausible dispatch
completion (`completed_at + uncertainty`). Equality, overlapping uncertainty,
incomparable clocks, missing completion, or a retained pre-dispatch observation
is `invalid_outcome`.

`Readback.evaluation` is the complete explicit wall and monotonic context used
to call `EvaluateSnapshot` on the later snapshot. When the receipt and
evaluation monotonic epochs match, evaluation ticks MUST be greater than or
equal to receipt ticks. Across epochs, `EvaluateSnapshot` applies the exact UTC
uncertainty algorithm in `FreshnessPolicy`. The candidate must be qualified,
promoted, good, evaluated fresh and available, and absent from an open conflict.
An incomparable/invalid evaluation or effective stale, expired, unknown,
degraded, unavailable, or withdrawn result is `invalid_outcome`.

A value already satisfied before dispatch never proves `applied`. If an
operation pack supports an already-satisfied preflight decision, it must expose a
separate typed pack contract that skips native dispatch and records no `applied`
`ExecutionRecord`; v1 defines no automatic fallback or additional terminal
outcome for that case.

A missing snapshot/candidate or revision mismatch is `dangling_reference`; a
different or retired route epoch is `stale_source_epoch`; a different or fenced
route generation is `stale_driver_generation`; and a different binding/source or
an inferred candidate is `invalid_outcome`. Even when all route fields match, a
candidate with a different fact key or a pack-evaluated relation other than
`confirms` is `invalid_outcome`. None can support `applied`.

### Type: ExecutionRecord

```go
type ExecutionRecord struct {
    Contract        ContractVersion  `json:"contract"`
    Intent          Intent           `json:"intent"`
    AdmittedAt      *TimePoint       `json:"admitted_at,omitempty"`
    AdmittedRevision *RevisionVector `json:"admitted_revision,omitempty"`
    Route           *Route           `json:"route,omitempty"`
    Dispatch        *DispatchEvidence `json:"dispatch,omitempty"`
    Acknowledgement *Acknowledgement `json:"acknowledgement,omitempty"`
    Readback        *Readback        `json:"readback,omitempty"`
    Outcome         Outcome          `json:"outcome"`
    ErrorID         *ErrorID         `json:"error_id,omitempty"`
    OutcomeEvidence []EvidenceRef    `json:"outcome_evidence"`
}
```

`Outcome` is one of:

| Outcome | Required evidence and meaning |
|---|---|
| `rejected` | No route or dispatch. `error_id` is required and records the stable admission error. |
| `failed_no_contact` | Dispatch evidence proves `not_sent` and no possible side effect. Retry still requires the owning replay policy. |
| `acknowledged_unverified` | A request was sent and accepted/provisionally acknowledged, but no confirming readback exists. |
| `applied` | Dispatch occurred and exact current-generation readback was evaluated as `confirms` by the intent's exact operation-pack effect rule. An ACK is retained when the protocol supplies one. |
| `no_effect` | Dispatch occurred and current-generation evidence proves the requested effect did not occur. |
| `conflict` | Post-dispatch evidence contradicts the requested effect or another current result. |
| `indeterminate` | Dispatch may have occurred and evidence cannot prove applied or no effect. Blind retry and fallback to another route are forbidden. |

After dispatch may have occurred, the execution remains bound to its route.
Timeout is an event, not `failed_no_contact`. An owner-specific recovery contract
may later append reconciliation evidence; it never rewrites the original
immutable execution record.

Only `rejected` carries `error_id`; every other outcome omits it and requires
non-empty outcome evidence. `rejected` MUST omit admitted revision, route,
dispatch, acknowledgement, and readback.

## Projection and compatibility

### Type: ProjectionManifest

```go
type ProjectionManifest struct {
    TargetID        TargetID        `json:"target_id"`
    TargetVersion   VersionLabel    `json:"target_version"`
    KernelVersion   ContractVersion `json:"kernel_version"`
    PackVersions    []PackRef       `json:"pack_versions"`
    MappingRevision Uint64          `json:"mapping_revision"`
}
```

### Type: RequestedItem

```go
type RequestedItem struct {
    ItemID DefinitionID `json:"item_id"`
    Kind   ItemKind     `json:"kind"`
}
```

`ItemKind` is `fact`, `relation`, `capability`, or `operation`.

### Type: LossDetail

```go
type LossDetail struct {
    Kind         LossKind       `json:"kind"`
    SourceItems  []DefinitionID `json:"source_items"`
    Description  string         `json:"description"`
    Reversible   bool           `json:"reversible"`
}
```

`LossKind` is `unit`, `range`, `precision`, `time`, `symbol`, `provenance`,
`identity`, `capability`, `operation`, or `policy`. Description is public NFC
text, not native payload.

### Type: ProjectionDisposition

```go
type ProjectionDisposition struct {
    Kind       ItemKind       `json:"kind"`
    ItemID     DefinitionID   `json:"item_id"`
    Outcome    ProjectionOutcome `json:"outcome"`
    SourceKeys []FactKey      `json:"source_keys"`
    Loss       []LossDetail   `json:"loss"`
    Reason     *DefinitionID  `json:"reason,omitempty"`
}
```

`ProjectionOutcome` is `exact`, `transformed`, `withheld`,
`unrepresentable`, `unsupported`, or `unknown`. Every requested `(kind,item_id)`
tuple has exactly one disposition with the identical tuple. Tuples are unique;
the same item ID MAY occur under different kinds and remains two independent
requests. `exact` forbids loss; `transformed` requires at least one loss detail;
`withheld`, `unrepresentable`, `unsupported`, and `unknown` require a reason.
Only a separately tested same-native mapping may claim lossless round trip.

### Type: ProjectionReport

```go
type ProjectionReport struct {
    Contract      ContractVersion        `json:"contract"`
    Manifest      ProjectionManifest     `json:"manifest"`
    SnapshotID    SnapshotID             `json:"snapshot_id"`
    Revisions     RevisionVector         `json:"revisions"`
    Requested     []RequestedItem        `json:"requested"`
    Dispositions  []ProjectionDisposition `json:"dispositions"`
    Causal        *CausalContext         `json:"causal,omitempty"`
}
```

Requested items and dispositions are sorted by `(kind,item_id)`. Projection
preserves snapshot and causal revisions. It cannot create facts, capability
instances, authority, intents, or routes.

### Type: CompatibilityAlias

```go
type CompatibilityAlias struct {
    AliasContract ContractVersion `json:"alias_contract"`
    LegacyID     OpaqueID        `json:"legacy_id"`
    AssetID      AssetID         `json:"asset_id"`
    ValidFrom    SemanticVersion `json:"valid_from"`
    ValidUntil   *SemanticVersion `json:"valid_until,omitempty"`
    Routable     bool            `json:"routable"`
    Evidence     []EvidenceRef   `json:"evidence"`
}
```

`routable` MUST be false. Aliases preserve public identity during migration but
cannot select a binding, capability, native endpoint, or operation route.
Evidence contains 1 through 32 unique references. `valid_until`, when present,
is greater than `valid_from`. Expiry does not delete historical snapshots.

## External normative boundary

This kernel contract is internally normative for Helianthus. It deliberately
contains no frozen Matter or eeBUS mapping.

The Matter comparison remains the draft 1.7 ballot 0.9 source at
[`29b4768a513cf566011ab8cd60df1bc495204953`](https://github.com/AryaHassanli/connectedhomeip/commit/29b4768a513cf566011ab8cd60df1bc495204953),
with upstream PR #73842 still open and draft when this contract was prepared.
Its provisional energy additions are design inputs, not final Matter
conformance.

The eeBUS
[`normative source ledger@81cd647`](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1/protocols/eebus-normative-source-ledger.md)
leaves exact current SHIP, SPINE, and use-case revisions unresolved. Affected
mappings remain candidate until an authorized exact revision and publishable
compatibility decision exist. Similar concepts do not establish equivalent
choreography, lifecycle, failsafe behavior, or conformance.

## Remaining INT-04 boundary

This v1 contract unblocks implementation of its own kernel records,
serialization, validation, and acceptance vectors in `helianthus-semreg` after
merge. It does not complete all INT-04. Separate reviewed work must still define
the thermal/HVAC, PV/inverter, storage/BMS, EVSE, and infrastructure capability
pack catalogs; exact native mappings and normative dispositions; Portal
contributions; and target contracts. INT-06 owns gateway/runtime composition.
INT-05 owns product code and executable fixtures. The 0.8 descriptive language,
IR, generation, and code reduction remain outside this typed 0.7 contract.
