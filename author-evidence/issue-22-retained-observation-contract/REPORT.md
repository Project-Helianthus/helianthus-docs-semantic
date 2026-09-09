# Issue #22 author evidence: retained-observation contract v1

## Scope and status

This candidate change extends the versioned semantic-kernel contract from exact
base `a435dba83f227c3d0ae83ca13611388132efd2e5`. It defines protocol-neutral,
read-only retained observations for pre-fence and source-retired observed facts.
It changes documentation, acceptance fixtures, and local validators only. It
does not implement SemReg, gateway lifecycle, persistence/restart restoration,
native mappings, routes, deployment, live action, or hardware qualification.

## Contract evidence

`RetainedObservation` copies the complete accepted original `FactCandidate` and
uses the canonical six-axis tuple `(candidate_id,candidate_revision,JCS(key),
binding_id,source_epoch_id,driver_generation)`. Thus a stable CandidateID can
be reused by a current revision without colliding with an old retained instance.
Fence and epoch retirement remove candidates from current facts while retaining
the original evidence through its original deadline. `EvaluationView.retained`
is separate from current facts; expiry removes it from current and readback views
without a publication. Retained evidence cannot select, route, admit, satisfy a
precondition, or confirm a readback.

Current observed candidates resolve through current bindings only. A retained
copy has its own validation: the copied native path must match a fenced binding
and matching generation fence, or a retired binding and matching retired source
descriptor. A mismatched or missing tombstone rejects atomically as
`dangling_reference`; the path is verified without changing any copied byte.

An explicit withdrawal removes all retained instances with its stable CandidateID
atomically, including distinct revisions and paths, and never fails because no
current candidate remains. The 32-record bound, canonical ordering, immutable
copy rule, and atomic rejected-transition non-advance are machine checked.

## Files

- `api/v1/kernel.md`, `api/v1/serialization.md`, and `api/v1/acceptance.md`
- `api/v1/retained-observation-acceptance.json`
- `api/v1/acceptance-vectors.json`
- `scripts/validate_retained_observation_v1.py`
- `scripts/test_validate_retained_observation_v1.py`
- `scripts/validate_kernel_v1.py` and `scripts/check_docs.sh`
- `api/README.md`

## Validation

- `python3 scripts/validate_retained_observation_v1.py` — PASS: 11 normative
  falsifiers.
- `python3 scripts/test_validate_retained_observation_v1.py` — PASS: baseline
  plus six rejecting mutations, including tombstone-path mismatch.
- `python3 -m py_compile scripts/validate_retained_observation_v1.py
  scripts/test_validate_retained_observation_v1.py` — PASS.
- `git diff --check` and local-link validation — PASS.
- `./scripts/check_docs.sh` — PASS: kernel consistency (70 types, 38 errors,
  16 coverage areas, 90 vectors), retained validators, and every existing pack
  validator/self-test. Captured log SHA-256:
  `5c9c5a95833b3a3a95de134add8f26b7cf54f05370b013de4497d6d1a88c7bc7`.

## Residual risk and stop

The next SemReg implementation must consume these vectors and demonstrate the
runtime behavior. The contract intentionally excludes retained-store persistence
and restoration. This author evidence stops before review and merge.
