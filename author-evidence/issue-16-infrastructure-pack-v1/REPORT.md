# Issue #16 author evidence: electrical infrastructure pack v1

## Scope and status

This candidate change adds the accepted typed
`helianthus.pack.infrastructure/v1` documentation input over exact base
`e22451c8ca3d3f7275635216450f8fb2d216801e`. It completes the five-domain
catalog without modifying any earlier pack. It is documentation and validation
only; no runtime, native driver, gateway, consumer, deployment, live action, or
hardware qualification is added.

## Files

- `api/v1/packs/infrastructure-v1.md`
- `api/v1/packs/infrastructure-acceptance-vectors.json`
- `scripts/validate_infrastructure_pack_v1.py`
- `scripts/test_validate_infrastructure_pack_v1.py`
- `scripts/check_docs.sh`
- `README.md`, `api/README.md`, and `compatibility/donor-ledger.md`

## Evidence boundary

The catalog pins the issue's exact public revisions: semantic docs `e22451c`,
semreg `cc9b324`, eBUS docs `5d66c66`, Modbus docs/registry `7ba9c333` /
`7853d903`, eeBUS ledger/M6.25 donor `81cd647` / `cedf238`, and Matter draft
`29b4768`. They establish no universal electrical-infrastructure mapping.
eBUS is identity/provenance-only unknown evidence. Modbus donors contain
profile-specific candidates, but this generic infrastructure row stays unknown
without an exact selected profile or projection. eeBUS remains
`unknown_pending_std_01`, and Matter is a
design input rather than conformance.

The pack indexes no operation or effect rule and has no Portal operation
descriptor. Its machine-checked read-only boundary forbids published
import/export control, breaker actuation, generic enable/disable, and any native
route or live authority until a separately qualified contract exists.

Integration review aligned power factor with canonical `unit.ratio`, kept
apparent power non-directional, and kept the generic Modbus row unknown until
an exact relevant profile is selected. The focused suite rejects an attempted
generic Modbus candidate state.

## Validation

- `python3 scripts/validate_infrastructure_pack_v1.py` — PASS.
- `python3 scripts/test_validate_infrastructure_pack_v1.py` — PASS: 2 positive
  controls and 17 rejecting mutations.
- `python3 -m py_compile scripts/validate_infrastructure_pack_v1.py scripts/test_validate_infrastructure_pack_v1.py` — PASS.
- `git diff --check` — PASS.
- `./scripts/check_docs.sh` — PASS. It includes existing kernel, snapshot,
  thermal, storage, PV, EVSE, and the new infrastructure validation suites.
  Complete log: `ci-full.log`, SHA-256
  `5e82da068eb9e4bc410ee6cb8534b9d868bf64b26d0ad07bce715575eff59661`.

## Residual risk and stop

The electrical bounds are semantic validation ranges, not equipment ratings.
Exact provider mappings, a control route, implementation, deployed behavior,
and physical verification remain separate work. This evidence stops before
commit, push, PR review, or merge.
