# Issue #22 author evidence: sequential retained lifecycle fix-forward

## Scope and status

This fix-forward starts from `main` commit
`c626e2a4a4364f5b94c4562dde9f7d01b88a5976`, which contains the earlier
retained-observation contract. It corrects the sequential lifecycle contradiction
reported publicly on issue #22: a retained observation created by a generation
fence must remain valid when later source retirement advances its binding from
`fenced` to `retired`.

The change is protocol-neutral documentation, fixtures, and validators only. It
does not implement SemReg or gateway code, create a cache or parallel store,
change a native mapping, persist state, or perform a live action.

## Contract evidence

`RetainedObservation.Candidate` and its original `Removal` event remain
byte-identical. A `generation_fence` retained record always resolves through its
original matching `GenerationFence`; its binding is `fenced` while the source
epoch is current and later becomes `retired` with the matching retired source
descriptor. Source retirement advances every binding in its exact source epoch,
including prior fenced bindings, atomically. It does not rebind evidence, rewrite
`Removal`, create a second retained record, or make retained evidence actionable.

The acceptance fixture covers fence then retirement, multiple fenced generations
then retirement, exact batch replay, and rejection without advance for a later
distinct duplicate retirement or foreign source, epoch, or generation. Existing
expiry and explicit withdrawal vectors remain applicable.

## Validation

- `python3 scripts/validate_retained_observation_v1.py` — PASS: 19 normative
  falsifiers (9 positive, 10 negative); fixture-count drift is rejected.
- `python3 scripts/test_validate_retained_observation_v1.py` — PASS: baseline
  plus twelve rejecting mutations, including declared-count drift and omission of
  the multiple-fence sequential-retirement vector.
- `python3 -m py_compile scripts/validate_retained_observation_v1.py
  scripts/test_validate_retained_observation_v1.py` — PASS.
- `git diff --check` and local-link validation — PASS.
- `./scripts/check_docs.sh` — PASS. Complete log SHA-256:
  `b99d3628d4acdd79463724fb8a3f4fe57699707637da3fc0efac55278f391428`.

## Residual risk and stop

SemReg must implement these public vectors and publish a corrected revision
before gateway #951 resumes its cutover. This author evidence stops before PR
review or merge.
