# Semantic kernel v1 acceptance contract

Status: normative companion to [kernel.md](kernel.md) when merged into `main`

## Publication and implementation boundary

This document specifies the tests that a later `helianthus-semreg`
implementation must pass. The documentation PR is accepted through complete
reviewed specifications, structurally consistent vectors, source/link checks,
and this repository's document validation. It does not require the nonexistent
implementation to run.

INT-05 must copy or consume the published
[acceptance vectors](acceptance-vectors.json), execute each scenario against the
public implementation, and retain exact vector IDs in test output. Target,
gateway, Portal, consumer, normative-protocol, and physical tests remain with
their owners.

## Vector format

Each JSON vector contains:

- a unique ID `K-POS-nnn` or `K-NEG-nnn`;
- `polarity` (`positive` or `negative`);
- one kernel `record_type` defined in [kernel.md](kernel.md);
- one named `operation` such as `validate`, `apply`, `admit`, `project`, or
  `restore`;
- one or more coverage IDs from this document;
- concrete harness `input` and optional `prior_state`;
- an expected `accept` result and observable postcondition, or a `reject`
  result with one stable error ID; and
- a short `criterion` that states the behavior under test.

An `input` is the complete fixture-harness scenario for the property being
exercised. It is direct wire JSON when it contains all members of the named
record. Scenario fields such as `eligible_routes`, `evidence_count`, or
`earlier_projection_same_value` are setup or observations, not extra members of
the public record. INT-05 must expand scenario shorthand into separately visible,
valid typed fixture records before invoking the API named by `operation`; no
unstated fixture default may alter the listed input, expected result, or
criterion. A vector may reference a prior positive vector by ID when its full
accepted setup would otherwise repeat the same record. The implementation
fixture loader resolves that reference by using the earlier vector's canonical
accepted result, then applies the stated mutation. Referenced positive vectors
must precede the dependent vector.

Every rejection is atomic. The implementation must assert that state and all
revisions are byte-identical before and after the rejected operation.

## Required coverage

### Coverage: `serialization`

Canonical JSON, exact integer/decimal tokens, required/optional fields,
duplicate keys, unknown members, array order, and stable digest input.

### Coverage: `identity`

Typed opaque IDs, evidence-qualified links, false-link rejection, conflicts,
and non-routable compatibility aliases.

### Coverage: `lineage`

Native evidence references, observed versus inferred facts, derivation inputs,
exact transitive source paths, multi-source lifecycle invalidation, bounded
acyclic graphs, origins, and correlation preservation.

### Coverage: `time`

Wall-clock uncertainty, distinct phenomenon/source/receipt/evaluation times,
monotonic clock epochs, reset behavior, and fail-closed comparison.

### Coverage: `freshness`

Fresh/stale/expired/unknown evaluation, conservative cross-epoch wall fallback,
retention after restart, time-only evaluation views with unchanged snapshot
bytes/revisions, admission-time re-evaluation, and no false fresh reset.

### Coverage: `qualification`

Assertion, qualification, promotion, validity, availability, and freshness as
independent axes; unknown and unsupported remain distinct.

### Coverage: `conflict`

Multiple candidates coexist, qualified disagreement remains visible, and
kernel-derived conflict metadata is atomically reconciled when candidates
change. Pure presentation selection receives matching immutable snapshot and
evaluation inputs, resolves the exact requested envelope, and does not destroy
or resolve alternatives.

### Coverage: `capability`

Exact pack/definition/version matching, activation evidence, constraints,
qualification, availability, degraded admission policy, and deterministic exact
pack-owner dispatch.

### Coverage: `snapshot`

Immutable deep copies, complete revision vectors, canonical collections,
resolved references, collection bounds, atomic derived-dependency cascades, and
reader visibility.

### Coverage: `partial_update`

Expected revisions, explicit upserts/withdrawals, retained unrelated facts,
idempotent replay, conflicting sequence reuse, and all-or-nothing changes.

### Coverage: `generation`

Distinct source epoch, driver generation, object/semantic revisions, lifecycle
operation, and intent correlation; activation publication, mandatory explicit
generation supersession, resolvable non-actionable fenced/retired tombstones,
complete post-transition snapshot validation, and fencing order.

### Coverage: `retained_observation`

Fence and source-epoch retirement retain a complete immutable observed-candidate
copy until its original deadline while removing it from current facts. Retained
instances use all identity/revision/path axes, are canonically ordered and
bounded, evaluate separately, disappear from current/readback views on expiry
without publication, and never satisfy selection, capability, route, operation,
or confirming-readback authority. Explicit withdrawal removes retained stable-ID
instances deterministically; rejected transitions leave both current and retained
state unchanged.

### Coverage: `operation`

Authority, deadline, preconditions, exactly-one route, guarded native admission,
exact eligible candidate binding, pack-owned expected effects,
dispatch/ACK/readback distinctions, provably post-dispatch observations with
explicit evaluation contexts, terminal outcomes, and retry boundaries.

### Coverage: `causal`

Preserved origin/correlation, bounded 16-hop and 300-second budgets, echo
re-entry rejection, exact receiver-ingress path mutation with unchanged egress,
and admission of an independent authorized intent.

### Coverage: `projection`

Complete requested-item accounting, exact/transformed/withheld/
unrepresentable/unsupported/unknown dispositions, source keys, and explicit
loss.

### Coverage: `compatibility`

Pinned donor comparison, versioned aliases, migration differences, and the rule
that compatibility does not create a native identity or operation route.

The vector set contains at least one positive and one negative scenario for
every coverage ID. A code implementation may add cases but cannot delete,
weaken, or reinterpret these vectors under the same contract version.

## Stable error identifiers

This list is exhaustive for v1 public validation. A conforming implementation
MUST NOT mint an additional public rejection ID under the same contract version.
The exact overlap precedence is defined in
[serialization.md](serialization.md#error-determinism).

### Error: `invalid_json`

The input is not exactly one valid UTF-8 JSON value, has a byte-order mark,
contains trailing data, or uses a JSON token that cannot be decoded.

### Error: `invalid_contract`

The record contract ID is missing, malformed, or not the required v1 contract.

### Error: `missing_member`

A required member other than the top-level contract is absent. An omitted
optional member is not an error; `null` cannot substitute for either a required
value or valid omission. An absent top-level contract is `invalid_contract`.

### Error: `invalid_identifier`

An identifier is empty, malformed, too long, non-ASCII where ASCII is required,
or supplied under the wrong typed identity.

### Error: `invalid_decimal`

A decimal coefficient/exponent is out of range or not in canonical exact form.

### Error: `invalid_value`

A tagged value selects zero/multiple payloads, uses a forbidden kind, contains
invalid text/symbol data, violates its pack-declared type/unit/range, or a
snapshot's kernel-derived conflict metadata differs from its candidate set. It
also covers a presentation policy that returns a candidate outside its supplied
envelope/evaluated subset or returns zero/multiple candidates.

### Error: `invalid_enum`

An enum field contains a token outside the exact values declared by its v1 type.

### Error: `bounds_exceeded`

A collection, text value, graph depth/node count, or other explicitly bounded
record exceeds its v1 maximum. Arithmetic overflow remains `invalid_time` or
`invalid_decimal` when that more specific class applies. `CausalContext` path,
hop, declared-hop, and lifetime maxima are the causal-domain exception below and
use `causal_budget_exceeded`.

### Error: `invalid_time`

A wall or monotonic point, uncertainty interval, ordering, deadline, expiry, or
freshness policy is malformed or impossible. A syntactically valid causal
interval whose lifetime exceeds the v1 300-second limit is
`causal_budget_exceeded`; malformed causal time points remain `invalid_time`.

### Error: `incomparable_clock_epoch`

An operation tries to subtract/order monotonic points from different clock
epochs without the permitted conservative wall-time evaluation.

### Error: `invalid_evidence`

A supplied `EvidenceRef` is malformed, inaccessible for the claimed public
state, or violates its owning reference contract. Duplicate canonical references
are `duplicate_key`. An empty/unqualifying `IdentityLink.basis` is
`identity_not_qualified`; empty/unqualifying capability activation evidence is
`capability_not_qualified`.

### Error: `noncanonical_order`

A set-like array is not in its required canonical order. A duplicate canonical
key is `duplicate_key` by higher precedence.

### Error: `digest_mismatch`

A syntactically valid digest on a previously unseen record does not equal the
digest of its required canonical input. Reuse of an accepted sequence or
idempotency key with different bytes is `sequence_conflict`.

### Error: `dangling_reference`

A snapshot or update reference does not resolve to the exact required object,
candidate revision, source path, or later readback snapshot. A resolved but stale
source epoch or generation uses the more specific lifecycle error. This class
does not apply to a precondition's exact candidate lookup or revision check;
those are `precondition_failed`. In selection, an absent requested fact key or
candidate correspondence uses this class.

### Error: `derivation_cycle`

An inferred candidate has missing/duplicate inputs, self-reference, a cycle, or
exceeds the derivation node/depth bound.

### Error: `identity_not_qualified`

A binding/link/alias is reused inconsistently or a claimed qualified identity
lacks its native-owner rule or has empty/unqualifying `IdentityLink.basis`.

### Error: `revision_conflict`

An expected semantic/object/component revision does not match the current
immutable state. It also covers a selection snapshot-ID, complete revision-vector,
evaluation-context, or evaluated-candidate-revision mismatch. A precondition's
candidate-revision mismatch is `precondition_failed` instead.

### Error: `sequence_conflict`

The same publication sequence or idempotency key is reused with different
canonical bytes, or sequence order regresses.

### Error: `stale_source_epoch`

A publication or operation refers to a source epoch that is no longer current.

### Error: `stale_driver_generation`

A publication, capability, route, callback, or readback refers to a fenced or
superseded driver generation.

### Error: `generation_transition_incomplete`

A higher-generation publication omits the explicit fence for an older unfenced
current generation or fails to include its atomic supersession boundary.

### Error: `definition_owner_conflict`

Registration contains duplicate pack validators, duplicate definition ownership,
a validator/index pack mismatch, a definition listed under the wrong kind, or a
duplicate kernel selection-policy ID/version.

### Error: `definition_owner_missing`

An explicit pack or field/service/capability/operation/effect definition has no
exact registered validator and matching definition-index entry, or an operation
pack lacks its required validation hook, or an exact kernel selection policy is
not registered.

### Error: `capability_not_qualified`

The required service/capability is candidate, unknown, unsupported, rejected,
or has empty/unqualifying activation evidence or current binding qualification.

### Error: `capability_unavailable`

The required capability is unavailable, withdrawn, or degraded without an
explicit pack/native mapping that permits degraded operation.

### Error: `ambiguous_route`

Admission finds zero or more than one eligible route after all exact filters and
constraints. Zero eligible route may use a more specific qualification or
availability error when one is uniquely applicable.

### Error: `deadline_expired`

The latest plausible current time is not strictly before the earliest plausible
intent deadline.

### Error: `precondition_failed`

A typed precondition is false; selects no exact candidate; selects candidate,
unpromoted, suspect/bad/unknown, stale/expired, degraded/unavailable/withdrawn,
revision-changed, or open-conflict evidence; or cannot be evaluated under its
exact pack contract. Another same-key candidate is never substituted.

### Error: `authority_missing`

The authority reference is missing, unresolved, expired, outside scope, or does
not authorize this exact intent and route.

### Error: `route_selection_forbidden`

A caller, presentation selection, projection, compatibility alias, or native
address attempts to choose/bypass the guarded route.

### Error: `causal_budget_exceeded`

The causal context is expired, exceeds 16 hops, exceeds its declared hop count,
has inconsistent path length or duplicate historical entries, cannot append a
new receiver within `max_hops`, or exceeds 300 seconds.

### Error: `echo_suppressed`

A receiver already present in the incoming causal path is re-entered under the
same correlation, or a reflected observation/projection tries to create
authority. Rejection does not append the receiver or increment the hop count.

### Error: `retry_forbidden`

An execution with possible side effect, indeterminate outcome, or non-replay-safe
native operation attempts blind retry or fallback to another route.

### Error: `projection_incomplete`

A requested projection item has zero/multiple dispositions, or the disposition
lacks its required reason, loss, source, revision, or causal accounting.

### Error: `alias_not_routable`

A compatibility alias is marked routable or is used as a binding, capability,
endpoint, or operation route.

### Error: `invalid_outcome`

The supplied dispatch, acknowledgement, readback, side-effect flag, and terminal
outcome combination is contradictory or incomplete. This includes a same-route
candidate that does not satisfy the intent's pack-owned expected effect.

### Error: `duplicate_key`

The input JSON repeats an object member or a set-like collection repeats its
canonical key.

### Error: `unknown_member`

A v1 semantic record contains an undeclared member or arbitrary extension bag.

## Context-specific error partition

These rules partition overlaps before applying the general precedence list:

- a syntactically present but empty/unqualifying `IdentityLink.basis` is
  `identity_not_qualified`; malformed supplied references inside a non-empty
  basis remain `invalid_evidence`;
- a syntactically present but empty/unqualifying
  `CapabilityInstance.activation_evidence` is `capability_not_qualified`;
  malformed supplied references inside a non-empty collection remain
  `invalid_evidence`;
- an absent `Precondition.candidate_id` or `candidate_revision` wire member is
  `missing_member`; after the precondition record decodes, an unresolved exact
  candidate ID or unequal candidate revision is `precondition_failed`, never
  `dangling_reference` or `revision_conflict`;
- missing/unresolvable readback snapshot/candidate references remain
  `dangling_reference`, while a resolved but pre-dispatch/unrelated/unverifiable
  candidate used for `applied` is `invalid_outcome`; and
- selection input uses `invalid_value` for malformed digest syntax or a policy
  result outside its supplied envelope, `digest_mismatch` for a valid but wrong
  computed evaluation digest, `revision_conflict` for snapshot/revision/context/
  candidate-revision mismatch, `dangling_reference` for an absent requested key
  or candidate, and the definition-owner errors for missing/duplicate exact
  selection-policy registration; and
- after a `CausalContext` has syntactically valid fields, its path length,
  `hop_count`, `max_hops`, path/count consistency, append capacity, and
  300-second lifetime use `causal_budget_exceeded`, even though generic arrays,
  integers, and time intervals have earlier precedence. Malformed JSON/member/
  identifier/time tokens retain their earlier parser-class error.

## Normative rejection class map

Every `MUST reject`, invalid-state rule, and failed public operation in v1 maps
through this table. The stable error descriptions refine the classes; the
serialization precedence list chooses one when an input violates several rows.

| Rejection class | Stable error ID |
|---|---|
| malformed UTF-8/JSON, byte-order mark, trailing data, invalid JSON token | `invalid_json` |
| repeated object member or duplicate canonical collection key | `duplicate_key` |
| absent, wrong, or malformed top-level contract | `invalid_contract` |
| absent required member other than the top-level contract, or `null` in its place | `missing_member` |
| undeclared member or extension bag | `unknown_member` |
| malformed, empty, overlength, non-ASCII, or wrong typed identifier | `invalid_identifier` |
| noncanonical/out-of-range decimal coefficient or exponent | `invalid_decimal` |
| wrong primitive token type, invalid tagged payload/text/symbol/unit/range, malformed non-evidence digest, mismatched kernel-derived conflict metadata, or zero/multiple/out-of-envelope selection result | `invalid_value` |
| invalid wall/monotonic time, duration, uncertainty, policy, ordering, or arithmetic overflow outside a well-formed over-limit causal lifetime | `invalid_time` |
| malformed or inaccessible supplied `EvidenceRef` outside the identity/capability proof cases below | `invalid_evidence` |
| enum token outside its exact declared set | `invalid_enum` |
| collection/text/graph maximum exceeded outside causal path/hop/lifetime limits | `bounds_exceeded` |
| valid set members presented outside canonical order | `noncanonical_order` |
| previously unseen record digest differs from its computed canonical digest | `digest_mismatch` |
| unresolved candidate/object/revision/source-path/readback-snapshot/selection-key reference outside precondition lookup | `dangling_reference` |
| derivation self-reference, cycle, or graph-shape violation | `derivation_cycle` |
| incomparable monotonic epochs without permitted wall evaluation | `incomparable_clock_epoch` |
| stale expected object/component/semantic revision or mismatched selection snapshot/revision/context/candidate revision outside precondition binding | `revision_conflict` |
| regressed/reused publication sequence or idempotency key with different bytes | `sequence_conflict` |
| retired or non-current source epoch | `stale_source_epoch` |
| fenced/superseded generation or readback/route generation mismatch | `stale_driver_generation` |
| higher generation without every required explicit supersession fence/withdrawal boundary | `generation_transition_incomplete` |
| duplicate validator/definition/selection-policy ownership, pack mismatch, or wrong indexed definition kind | `definition_owner_conflict` |
| missing exact pack validator, field/service/capability/operation/effect entry, operation-pack hook, or selection policy | `definition_owner_missing` |
| unproved/reused/conflicting identity link/binding, including empty or unqualifying link basis | `identity_not_qualified` |
| candidate/unknown/unsupported/rejected capability or empty/unqualifying activation/pack proof | `capability_not_qualified` |
| withdrawn/unavailable or non-permitted degraded capability | `capability_unavailable` |
| zero/multiple eligible routes after otherwise successful filtering | `ambiguous_route` |
| expired or uncertainty-failed deadline | `deadline_expired` |
| false or non-exact candidate/unqualified/unpromoted/suspect/bad/unknown/stale/expired/conflicted/degraded/unavailable/revision-changed precondition | `precondition_failed` |
| missing/unresolved/expired/out-of-scope authority | `authority_missing` |
| route selected from presentation/projection/alias/caller native ID | `route_selection_forbidden` |
| expired/inconsistent/duplicate-history causal context or no capacity to append a new receiver | `causal_budget_exceeded` |
| ingress receiver already in path or attempted authority minting from reflection | `echo_suppressed` |
| unsafe blind retry or route fallback after possible side effect | `retry_forbidden` |
| missing/duplicate/mismatched requested `(kind,item_id)` disposition or required accounting | `projection_incomplete` |
| compatibility alias marked or used as routable | `alias_not_routable` |
| contradictory/incomplete dispatch, ACK, readback, side-effect, and outcome combination | `invalid_outcome` |

## Acceptance procedure for INT-05

1. Pin this documentation repository to the exact reviewed commit consumed by
   the implementation issue.
2. Load the vector JSON with a duplicate-key-rejecting decoder.
3. Resolve `prior_vector` only to an earlier accepted positive vector.
4. Execute the named public validator/update/admission/projection operation.
5. For positive vectors, compare canonical output and stated postconditions.
6. For negative vectors, compare the stable error ID and prove state/revisions
   did not change.
7. Run the complete vector set with race detection and independent clean-clone
   module validation.
8. Record any donor migration difference in the owning compatibility ledger;
   do not modify expected results under v1 merely to match existing behavior.

Documentation acceptance does not claim these code tests passed. It makes the
test obligation concrete so the next code issue can implement it without a new
design cycle.

## Retained-observation falsifiers

The companion [retained-observation fixture](retained-observation-acceptance.json)
is normative for the lifecycle behavior introduced by issue #22. Its eleven vectors
cover generation fence, source retirement, same-ID current replacement, explicit
withdrawal, deadline-only expiry, multiple retained revisions, tampering,
selection/operation rejection, rejected-transition non-advance, and mismatched
fenced/retired tombstone-path rejection. An INT-05
implementation must execute each vector and preserve the stated canonical tuple,
original candidate bytes, and result. The fixture is checked by
`scripts/validate_retained_observation_v1.py` and mutation-tested by
`scripts/test_validate_retained_observation_v1.py`.

## PublicationKernel fork falsifiers

The companion [fork acceptance fixture](kernel-fork-acceptance.json) is
normative for `PublicationKernel.Fork`. Every scenario below is a falsifier:
any result other than its stated postcondition rejects the implementation.

1. `KF-POS-001` builds through sequence 32, forks, and requires byte-identical
   current snapshot and canonical bytes before another apply.
2. `KF-POS-002` applies sequence 33 only to the fork and requires the source to
   remain byte-identical while the fork advances once in the same source, epoch
   and generation.
3. `KF-NEG-001` applies a malformed or conflicting batch only to a fork and
   requires both source and fork to remain unchanged.
4. `KF-POS-003` replays the accepted current tuple independently on source and
   fork and requires equal detached result bytes with no revision advance.
5. `KF-POS-004` forks an empty kernel and requires the same pack validator to
   accept and reject the same definitions after its first publication.
6. `KF-NEG-002` mutates every value returned by `Current` and `Fork` and
   requires no attached state change.
7. `KF-POS-005` races `Current`, `Fork`, and `Apply` and requires each fork to
   contain one complete committed point, never a mixed state.

The fixture also rejects a nil receiver unless `Fork` returns no object and
`invalid_value`. It does not authorize restore, import, checkpoint,
persistence, gateway composition, lifecycle replacement, or a source restart.
