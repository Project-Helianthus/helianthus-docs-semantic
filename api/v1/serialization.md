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
| `Derivation.inputs` | `CandidateID` |
| `Value.symbols` | `(namespace, token)` |
| `FactKey.dimensions` | `Dimension.id`, then canonical value bytes |
| `Quality.reasons` | `DefinitionID` |
| `FactEnvelope.candidates` | `CandidateID` |
| `Conflict.candidates` | `CandidateID` |
| `TypedField` collections | `DefinitionID` |
| sources | `(source_id, source_epoch_id)` |
| source retirements | `SourceEpochID` |
| bindings, identity links, services, capabilities | primary instance/binding ID |
| fact envelopes | canonical `FactKey` bytes |
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
`sequence_conflict` and changes no state.

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

## Partial updates

A publication batch is a patch with explicit operations, not a replacement
snapshot:

- an upsert changes only its named object;
- an explicit withdrawal changes only its named current object;
- an absent object retains its previous value and continues to age under its
  freshness policy;
- a rejected batch changes neither state nor revisions;
- an accepted batch publishes all component changes together; and
- an idempotent replay returns the previously created snapshot and does not
  increment a revision.

When a partial read omits a fact because its native field failed, the adapter
MUST leave the prior fact absent from both upserts and withdrawals unless its
own contract supplies evidence for withdrawal. The retained fact may become
stale, expired, bad, degraded, or unavailable according to its own policy; the
failed sibling does not erase it.

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

## Operation record ordering

Operation records are append-only evidence. Admission binds the exact snapshot
revision and route before dispatch. Dispatch, acknowledgement, and readback keep
their individual timestamps and evidence. A later reconciliation appends a new
record referring to the original attempt; it never changes `unknown` delivery
into `not_sent` or rewrites an original `indeterminate` outcome.

The same `IdempotencyKey` with different canonical intent bytes is
`sequence_conflict`. The same validated intent may return its recorded outcome.
No serializer or cache may convert that deduplication into permission to replay
the native operation.

## Causal serialization

Origin references and correlation IDs persist through facts and projections. A bridge
increments the hop count and appends itself exactly once before emission. It
MUST NOT shorten expiry or hop history in a way that hides a loop, extend the
expiry beyond the original 300-second maximum, or mint authority from an
observation.

A receiving target rejects the record when its ID is already in the path, the
hop count would exceed `max_hops`, or the conservative expiry check fails. An
independent operator or automation request uses a new intent, idempotency, and
correlation ID and undergoes normal authority/admission checks; equality of the
requested semantic value with an earlier projection is not itself suppression.

## Error determinism

Validation MUST return the most specific stable error ID before any state
change. When several independent errors exist, implementations use this order:

1. JSON syntax, duplicate keys, and unknown members;
2. contract, required member, primitive, enum, and bound validation;
3. internal reference, ordering, digest, and derivation validation;
4. source epoch, generation, sequence, and revision validation;
5. identity, qualification, capability, authority, deadline, and precondition
   validation;
6. route ambiguity and guarded admission;
7. operation outcome, causal, projection, and compatibility invariants.

This order makes negative fixtures portable. It does not allow a validator to
skip additional diagnostics in logs, provided the public error ID is stable and
no rejected input changes state.
