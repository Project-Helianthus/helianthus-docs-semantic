# Semantic kernel v1 serialization

Status: normative companion to
[`helianthus.semantic.kernel/v1`](kernel.md) when merged into `main`

## Encoding profile

Every public v1 record uses UTF-8 JSON and the exact snake-case member names in
the kernel contract. The encoded form MUST:

1. contain one complete JSON value and no byte-order mark or trailing data;
2. reject duplicate object member names before binding to a type;
3. reject members that are not defined for the selected v1 record;
4. reject JSON `null`; an optional field is omitted when absent;
5. reject non-finite numbers and any JSON number where the contract requires a
   decimal string;
6. validate identifiers, enums, ranges, field presence, collection bounds,
   cross-references, and state invariants before publication; and
7. serialize valid records with RFC 8785 JSON Canonicalization Scheme (JCS)
   after applying the v1 array-order rules below.

JCS defines object-key and JSON primitive serialization. This contract encodes
64-bit signed/unsigned integers and exact decimal coefficients as strings before
JCS so JavaScript or intermediate decoders cannot round them. An implementation
MUST validate the original JSON token type: the JSON number `1` is not accepted
for a field whose wire type is the string `"1"`.

## Field presence and unknown data

Required members are always emitted, including required empty arrays. Optional
members use `omitempty` in the Go sketches and are omitted when absent. Empty
string, zero identifier, synthetic time, empty evidence, and JSON `null` do not
stand in for absence.

Unknown semantic object members are `unknown_member`. Forward-compatible native
data remains in the native owner's evidence object and is referenced by
`EvidenceRef`. Unknown native symbols are represented by `Symbol` with
`known=false` and a `native.` namespace. They are preserved byte-for-byte after
valid UTF-8/NFC validation and cannot become known pack symbols merely by
round-trip.

This strict member rule prevents a v1 reader from silently discarding a safety
or authority field. A later contract version may add members with an explicit
migration; v1 does not provide an arbitrary extension map.

## Canonical identifiers and text

Identifiers are ASCII and are never Unicode-normalized, trimmed, case-folded,
or percent-decoded. Equality is exact byte equality within the same named type.
An `AssetID` equal as text to a `SourceID` remains a different typed value.

Human-readable semantic text and `Symbol.token` MUST be valid UTF-8 in Unicode
Normalization Form C. Control characters are rejected except tab, line feed,
and carriage return in `Value.text`. Native text that cannot meet this rule
stays in native evidence; a transformation may publish a semantic text value
only with lineage and any loss recorded.

## Canonical decimal and quantity

`Decimal` is canonical before JSON serialization:

- zero is `{"coefficient":"0","exponent10":0}`;
- a non-zero coefficient has no leading zero and does not end in zero;
- exponent is an integer from -18 through 18;
- `-0`, `00`, `01`, `10` with an unshifted exponent, exponent strings, and JSON
  floating-point coefficients are invalid.

For example, exact 230.0 V is represented as coefficient `23`, exponent `1`,
and the pack-declared voltage unit. Measurement resolution or display precision
is a separate pack property and is not inferred from trailing decimal zeroes.
Unit conversion creates a new derived candidate with derivation/evidence and
does not rewrite the native candidate.

## Canonical time

All `TimePoint.unix_nanoseconds`, `TimePoint.uncertainty_ns`, and monotonic ticks
use decimal strings. `TimePoint` is an estimate under its named clock; it is not
serialized as an RFC 3339 string because that form cannot preserve every signed
nanosecond value and uncertainty without additional rules.

Two wall points are directly comparable only when their `clock_id` is identical
or an admitted transformation supplies a common `clock.utc` estimate and
evidence. Comparison uses uncertainty intervals. Deadline and causal-expiry
checks fail closed: admission proceeds only when the latest plausible current
time is strictly before the earliest plausible deadline/expiry.

Monotonic comparison requires equal `clock_epoch_id`. A restarted process or
reset clock creates a new epoch even if the numeric ticks repeat. Across epochs,
freshness uses the conservative UTC rule in the kernel contract or becomes
`unknown`; it never subtracts the ticks or resets the receipt point.

## Array ordering

The producer MUST sort set-like arrays before validation and serialization. A
decoder MUST reject a non-canonical order rather than silently reorder signed or
digested input.

| Record/member | Sort key |
|---|---|
| `EvidenceRef` collections | `(owner, kind, contract, digest)` |
| `Derivation.inputs` | `candidate_id` |
| `DerivationInput.source_paths` | `(source_id, source_epoch_id, driver_generation, binding_id)` |
| `Value.symbols` | `(namespace, token)` |
| `FactKey.dimensions` | `Dimension.id`, then canonical value bytes |
| `Quality.reasons` | `DefinitionID` |
| `FactEnvelope.candidates` | `CandidateID` |
| `FactEnvelope.conflicts` | `ConflictID` |
| `Conflict.candidates` | `CandidateID` |
| `TypedField` collections | `DefinitionID` |
| `DefinitionIndex` collections | `(id, version)` |
| registered pack validators and projection pack versions | `(pack id, pack version)` |
| registered selection policies | `(policy_id, policy_version)` |
| `Intent.preconditions` | `(canonical FactKey bytes, candidate_id, candidate_revision)` |
| sources | `(source_id, source_epoch_id)` |
| source retirements | `SourceEpochID` |
| bindings, identity links, services, capabilities | primary instance/binding ID |
| fact envelopes | canonical `FactKey` bytes |
| `EvaluationView.facts` | `candidate_id` |
| `EvaluationView.retained`, `Snapshot.retained_observations` | `(candidate_id,candidate_revision,JCS(key),binding_id,source_epoch_id,driver_generation)` |
| fences and publication cursors | `(source_id, source_epoch_id, driver_generation)` |
| publication upserts/withdrawals | primary ID or canonical fact key |
| projection requested/dispositions | `(kind, item_id)` |
| loss details | `(kind, canonical source_items, description)` |
| causal path | sequence order; never sorted |
| acknowledgement, dispatch, readback history | sequence order; never sorted |

Every set-like collection rejects duplicates after canonical comparison. Sequence
collections retain their stated event order and may contain the same value only
when the record contract explicitly allows it.

## Canonical record digests

`PublicationBatch.batch_digest` is calculated as follows:

1. validate every field other than `batch_digest` and establish canonical array
   order;
2. omit the `batch_digest` member entirely;
3. serialize the remaining object with JCS;
4. calculate SHA-256 over those UTF-8 bytes; and
5. prefix the lowercase hexadecimal digest with `sha256:`.

The digest binds the batch bytes, not acceptance. A repeated
`(source_id, source_epoch_id, driver_generation, sequence)` is idempotent only
when the digest is identical to the accepted batch. A different digest is
`sequence_conflict` and changes no state. For a sequence not already accepted,
a syntactically valid digest that differs from the computed digest is
`digest_mismatch`.

Only the current `last_sequence`/`last_batch_digest` pair is idempotently
replayable. A smaller sequence is rejected even if its old bytes are available;
the bounded kernel state does not resurrect an earlier snapshot.

Evidence digests are calculated by their native owner under the contract named
in `EvidenceRef`; semreg validates their form and reference rules but does not
recalculate inaccessible evidence.

## Snapshot serialization and immutability

An accepted non-idempotent publication batch creates a new complete snapshot.
The implementation MUST deep-copy mutable caller inputs or otherwise prove that
later caller mutation cannot change published bytes. Snapshot canonical bytes,
revision vector, and references remain immutable.

Snapshot encoding includes required empty arrays so two complete empty
components do not hash differently because one producer omitted a required
member. Readers reject duplicate IDs, dangling references, revision mismatch,
non-canonical order, and collections beyond the kernel limits. They do not
truncate, merge, or choose a first duplicate.

Time-only evaluation serializes an `EvaluationView`; it never serializes updated
freshness back into `Snapshot`. The view repeats the snapshot ID and revision
vector, records its explicit evaluation context, and has its own canonical
digest. Thus fresh-to-stale-to-expired transitions can produce distinct view
bytes while the source snapshot canonical bytes and every publication revision
remain unchanged.

Retained observations serialize the copied original `FactCandidate` without
changing value, time, quality, origin, evidence, binding, source epoch, or
generation. The canonical retained tuple is compared component-wise in the order
stated in `RetainedObservation`; `JCS(key)` supplies the fact-key axis.
`Snapshot.retained_observations` is stored audit state, whereas
`EvaluationView.retained` contains only records before their original deadline.
No serializer may revive an expired retained record or put it in
`EvaluationView.facts`, a fact envelope, selection input, route, or readback.

The retained tuple and copied `Removal` event are immutable across a later
`fenced -> retired` binding-state advance. Canonical snapshot serialization
contains the one current binding tombstone in its normal binding collection plus
the original retained observation; it creates no second retained store or
replacement observation. An identical source-retirement batch replays the prior
canonical snapshot. A later distinct retirement, or one that names a different
source, epoch, or generation, has no canonical output because it rejects before
publication.

Presentation selection serializes a separate
`helianthus.semantic.selection/v1` result bound to the exact snapshot ID,
complete revision vector, evaluation digest and context, fact
key, candidate ID/revision, and policy ID/version. It is never a `Snapshot` or
`FactEnvelope` member. Selection receives both complete canonical `Snapshot` and
`EvaluationView` bytes. The view digest is verified before snapshot/revision/
candidate correspondence; the requested key is resolved in the snapshot before
one exact policy dispatch. The policy receives the matching envelope and its
sorted evaluated facts only. A later snapshot or evaluation cannot retain or
rewrite the result; callers request a new pure selection.

The same canonical snapshot, evaluation view, requested key and policy version
MUST produce identical selection bytes. Selection reads no implicit store or
clock. A valid-but-wrong evaluation digest is `digest_mismatch`; mismatched
snapshot/revision/context/candidate revision is `revision_conflict`; a missing
requested key/candidate is `dangling_reference`; and an out-of-envelope policy
result is `invalid_value`.

`FactEnvelope.conflicts` is canonical kernel output. After the complete candidate
change and dependency cascade, the kernel sorts eligible candidate IDs, derives
the conflict ID from the specified JCS object, and sorts the unioned candidate
evidence before snapshot serialization. A publication batch never serializes
selection/conflict input. Removing or revising a referenced candidate recomputes
the complete current conflict array before the new snapshot ID is calculated.

## Partial updates

A publication batch is a patch with explicit operations, not a replacement
snapshot:

- an upsert changes only its named object;
- an explicit withdrawal changes only its named current object;
- an absent object retains its previous value and continues to age under its
  freshness policy;
- fact conflict metadata is deterministically reconciled after explicit and
  lifecycle-derived candidate changes;
- a rejected batch changes neither state nor revisions;
- an accepted batch publishes all component changes together; and
- an idempotent replay returns the previously created snapshot and does not
  increment a revision.

When a partial read omits a fact because its native field failed, the adapter
MUST leave the prior fact absent from both upserts and withdrawals unless its
own contract supplies evidence for withdrawal. The retained fact may become
stale, expired, bad, degraded, or unavailable according to its own policy; the
failed sibling does not erase it.

An inferred candidate serializes every exact input candidate revision and the
sorted transitive union of native source paths. A publication that removes or
changes an input path atomically removes affected derived candidates through the
kernel's dependency closure. The cascade is part of the same snapshot and
revision update; no temporary snapshot may retain a derived candidate with a
dangling or fenced dependency.

An affected non-empty envelope is serialized only after its derived conflict
array is recomputed. If withdrawal leaves one qualifying value, the new envelope
contains that candidate and an empty conflict array; its revision and the facts
component revision increment once. The prior snapshot remains the immutable
record of the earlier candidates/conflict. No `resolved` conflict or resolution
evidence is synthesized.

## Generation and restart ordering

The serialization fields express four separate orders:

1. `(source_id, source_epoch_id, driver_generation, sequence)` orders native
   publication attempts;
2. `RevisionVector.semantic` orders accepted semantic snapshots per asset;
3. candidate/service/capability `revision` orders one semantic object; and
4. intent/correlation/idempotency identifiers relate operation evidence without
   defining any of the first three orders.

A runtime lifecycle operation identifier, including a stable value such as zero,
is not serialized into any of these fields unless an owning evidence contract
references it as opaque evidence. It cannot be substituted for generation or
correlation.

After source restart, a new source epoch is required unless the producer proves
continued durable sequence state. After driver replacement, the generation
changes even when the profile and semantic definitions remain the same. A
capability becomes visible as actionable only after activation evidence exists
for the current generation. A fence and all withdrawals for the fenced
generation publish atomically before the new snapshot becomes visible.

A higher generation is not an ordinary partial update. Its first batch includes
an explicit fence for every older unfenced generation under the same source
epoch. The canonical fence array therefore binds the supersession evidence into
`batch_digest`. Missing a required fence is
`generation_transition_incomplete`; serializers and decoders never infer or add
one. The accepted batch atomically serializes the old binding as `fenced`, its
identity link as `withdrawn`, its service/capability as `withdrawn`, removes its
observed and derived candidates, reconciles envelope conflicts, and rejects its
guarded callback before exposing the new generation. These tombstones remain
resolvable through the retained fence/source records and cannot be selected as
current routes. Source retirement uses the corresponding `retired` source and
binding tombstones.

## Operation record ordering

Operation records are append-only evidence. Admission binds the exact snapshot
revision and route before dispatch. Dispatch, acknowledgement, and readback keep
their individual timestamps and evidence. A later reconciliation appends a new
record referring to the original attempt; it never changes `unknown` delivery
into `not_sent` or rewrites an original `indeterminate` outcome.

Each precondition serializes its fact key, candidate ID, and candidate revision.
Admission resolves only that tuple and requires qualified, promoted, good, fresh,
available, unconflicted evidence. Equal revisions on another same-key candidate
do not match, and neither canonical ordering nor a presentation selection can
change the selected evidence.

A readback serializes the exact later snapshot ID/revisions, candidate revision,
binding, source, source epoch, driver generation, and complete wall-plus-monotonic
`EvaluationContext`. These members are audit evidence and MUST match the
admitted route; a fixture-only generation assertion cannot substitute for them.
For `applied`, the resolved candidate's receipt must be strictly after the
serialized dispatch completion. Equal monotonic epochs compare ticks; different
epochs compare UTC uncertainty intervals, requiring the earliest plausible
receipt to be later than the latest plausible completion. A retained
pre-dispatch candidate, missing completion, overlapping interval, incomparable
clock, or evaluation whose freshness is not reproducible rejects
`invalid_outcome`. The containing intent serializes an exact pack-owned
`ExpectedEffect`. The operation pack validator recomputes the relation from the
unchanged intent and resolved candidate; serialized `relation=confirms` cannot
substitute for that evaluation.

Definition dispatch reads the explicit `PackRef` carried by each
`DefinitionRef` or capability requirement, then performs one exact lookup in the
prebuilt definition index. Registration order, name prefixes, and fallback
probing do not affect canonical bytes or validation results.

The same `IdempotencyKey` with different canonical intent bytes is
`sequence_conflict`. The same validated intent may return its recorded outcome.
No serializer or cache may convert that deduplication into permission to replay
the native operation.

## Causal serialization

Origin references and correlation IDs persist through facts and projections.
The path serializes targets that have already accepted ingress, in their entry
order. A context created inside A is `[A]/1`; A emits `[A]/1` unchanged. Receiver
R validates the incoming context, rejects an existing R, checks capacity, then
appends R and increments the count before processing. Thus B accepts `[A,B]/2`,
emits `[A,B]/2` unchanged, and C accepts `[A,B,C]/3`; a C-to-A reflection is
rejected before mutation because A is already present. Rejection never mutates
the context. A processor
MUST NOT shorten expiry or path history, extend the expiry beyond the original
300-second maximum, or mint authority from an observation.

An independent operator or automation request uses a new intent, idempotency,
and correlation ID and undergoes normal authority/admission checks; equality of
the requested semantic value with an earlier projection is not itself
suppression.

## Error determinism

Validation MUST return the most specific stable error ID before any state
change. Every normative rejection maps to the stable class table in
[acceptance.md](acceptance.md). When several errors exist, implementations use
this exact precedence, from first to last:

1. `invalid_json`, `duplicate_key`;
2. `invalid_contract`, `missing_member`, `unknown_member`;
3. `invalid_identifier`, `invalid_decimal`, `invalid_value`, `invalid_time`,
   `invalid_evidence`, `invalid_enum`, `bounds_exceeded`;
4. `noncanonical_order`, `digest_mismatch`, `dangling_reference`,
   `derivation_cycle`;
5. `stale_source_epoch`, `stale_driver_generation`, `sequence_conflict`,
   `revision_conflict`, `incomparable_clock_epoch`,
   `generation_transition_incomplete`;
6. `definition_owner_conflict`, `definition_owner_missing`,
   `identity_not_qualified`, `capability_not_qualified`,
   `capability_unavailable`, `authority_missing`, `deadline_expired`,
   `precondition_failed`;
7. `route_selection_forbidden`, `ambiguous_route`, `retry_forbidden`;
8. `invalid_outcome`, `echo_suppressed`, `causal_budget_exceeded`,
   `projection_incomplete`, `alias_not_routable`.

The context partitions in acceptance.md classify a decoded record before this
list orders independent failures. In particular, syntactically valid
CausalContext path length, hop values, path/count consistency, append capacity,
and lifetime limits use the causal-budget error; they are excluded from generic
bounds and time errors. Malformed JSON tokens, missing members, invalid
identifiers, or malformed time points retain their earlier classes.

This order makes negative fixtures portable. It does not allow a validator to
skip additional diagnostics in logs, provided the public error ID is stable and
no rejected input changes state.
