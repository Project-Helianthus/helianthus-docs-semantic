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
bounded acyclic graphs, origins, and correlation preservation.

### Coverage: `time`

Wall-clock uncertainty, distinct phenomenon/source/receipt/evaluation times,
monotonic clock epochs, reset behavior, and fail-closed comparison.

### Coverage: `freshness`

Fresh/stale/expired/unknown evaluation, conservative cross-epoch wall fallback,
retention after restart, and no false fresh reset.

### Coverage: `qualification`

Assertion, qualification, promotion, validity, availability, and freshness as
independent axes; unknown and unsupported remain distinct.

### Coverage: `conflict`

Multiple candidates coexist, qualified disagreement remains visible, and
presentation selection does not destroy or resolve alternatives.

### Coverage: `capability`

Exact definition/version matching, activation evidence, constraints,
qualification, availability, and degraded admission policy.

### Coverage: `snapshot`

Immutable deep copies, complete revision vectors, canonical collections,
resolved references, collection bounds, and atomic reader visibility.

### Coverage: `partial_update`

Expected revisions, explicit upserts/withdrawals, retained unrelated facts,
idempotent replay, conflicting sequence reuse, and all-or-nothing changes.

### Coverage: `generation`

Distinct source epoch, driver generation, object/semantic revisions, lifecycle
operation, and intent correlation; activation publication and fencing order.

### Coverage: `operation`

Authority, deadline, preconditions, exactly-one route, guarded native admission,
dispatch/ACK/readback distinctions, terminal outcomes, and retry boundaries.

### Coverage: `causal`

Preserved origin/correlation, bounded 16-hop and 300-second budgets, echo
re-entry rejection, and admission of an independent authorized intent.

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

### Error: `invalid_contract`

The record contract ID is missing, malformed, or not the required v1 contract.

### Error: `invalid_identifier`

An identifier is empty, malformed, too long, non-ASCII where ASCII is required,
or supplied under the wrong typed identity.

### Error: `invalid_decimal`

A decimal coefficient/exponent is out of range or not in canonical exact form.

### Error: `invalid_value`

A tagged value selects zero/multiple payloads, uses a forbidden kind, contains
invalid text/symbol data, or violates its pack-declared type/unit/range.

### Error: `invalid_time`

A wall or monotonic point, uncertainty interval, ordering, deadline, expiry, or
freshness policy is malformed or impossible.

### Error: `incomparable_clock_epoch`

An operation tries to subtract/order monotonic points from different clock
epochs without the permitted conservative wall-time evaluation.

### Error: `invalid_evidence`

Evidence is missing, malformed, duplicated, inaccessible for the claimed public
state, or does not satisfy the owning reference contract.

### Error: `derivation_cycle`

An inferred candidate has missing/duplicate inputs, self-reference, a cycle, or
exceeds the derivation node/depth bound.

### Error: `identity_not_qualified`

A binding/link/alias is reused inconsistently or a claimed qualified identity
lacks its native-owner rule and evidence.

### Error: `revision_conflict`

An expected semantic/object/component revision does not match the current
immutable state.

### Error: `sequence_conflict`

The same publication sequence or idempotency key is reused with different
canonical bytes, or sequence order regresses.

### Error: `stale_source_epoch`

A publication or operation refers to a source epoch that is no longer current.

### Error: `stale_driver_generation`

A publication, capability, route, callback, or readback refers to a fenced or
superseded driver generation.

### Error: `capability_not_qualified`

The required service/capability is candidate, unknown, unsupported, rejected,
or lacks activation evidence/current binding qualification.

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

A typed precondition is false, stale, conflicted, unavailable, or cannot be
evaluated under its pack contract.

### Error: `authority_missing`

The authority reference is missing, unresolved, expired, outside scope, or does
not authorize this exact intent and route.

### Error: `route_selection_forbidden`

A caller, presentation selection, projection, compatibility alias, or native
address attempts to choose/bypass the guarded route.

### Error: `causal_budget_exceeded`

The causal context is expired, exceeds 16 hops, exceeds its declared hop count,
has inconsistent path length, repeats a target, or exceeds 300 seconds.

### Error: `echo_suppressed`

A reflected observation/projection attempts to re-enter operation admission
under the same causal path/correlation or tries to create authority.

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
outcome combination is contradictory or incomplete.

### Error: `duplicate_key`

The input JSON repeats an object member or a set-like collection repeats its
canonical key.

### Error: `unknown_member`

A v1 semantic record contains an undeclared member or arbitrary extension bag.

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
