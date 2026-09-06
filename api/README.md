# Semantic API publication status

## Kernel v1

The versioned kernel contract consists of:

- [typed records and invariants](v1/kernel.md);
- [deterministic JSON serialization](v1/serialization.md);
- [acceptance rules and stable errors](v1/acceptance.md); and
- [positive and negative acceptance vectors](v1/acceptance-vectors.json).

## Thermal/HVAC pack v1

The first accepted INT-04 capability pack is
[`helianthus.pack.thermal/v1`](v1/packs/thermal-hvac-v1.md). It supplies the
typed thermal/HVAC field, service, capability, operation, effect, lifecycle,
projection-loss, and Portal-contribution contract over the kernel. Its
[positive and negative vectors](v1/packs/thermal-hvac-acceptance-vectors.json)
are mechanically checked with `scripts/validate_thermal_hvac_pack_v1.py`.
Native eBUS and GREE rows remain candidate evidence owned by their native
documentation repositories. Affected eeBUS rows remain unknown pending STD-01.

## Storage/BMS pack v1

[`helianthus.pack.storage/v1`](v1/packs/storage-bms-v1.md) is the accepted
second typed capability pack. Its vectors are checked by
`scripts/validate_storage_bms_pack_v1.py`. CAN V1.04 and RS-485 1xSxxP rows are
offline candidate evidence only; eeBUS remains `unknown_pending_std_01`.

Primary contract ID: `helianthus.semantic.kernel/v1`; the pure time-evaluation
view uses `helianthus.semantic.evaluation/v1`, and pure presentation results use
`helianthus.semantic.selection/v1`. Selection receives the complete matching
immutable snapshot and evaluation view; it has no hidden store or native lookup.
The contract becomes normative for the Project Helianthus kernel implementation
when merged into `main`. The owning Go module is
[`Project-Helianthus/helianthus-semreg`](https://github.com/Project-Helianthus/helianthus-semreg).

The contract is complete for its kernel scope: identity/source/evidence,
protocol-neutral values and quality, facts and conflicts, services and
capabilities, immutable publication/snapshots, pure freshness evaluation,
multi-source derived dependencies, self-contained deterministic presentation
selection, exact precondition evidence, pack-owned
readback effects and definition dispatch, mandatory generation supersession,
operation evidence, causal budgets, projection loss, and compatibility aliases.
It deliberately contains no protocol/vendor/gateway import or arbitrary public
value bag.

## Remaining contracts

This publication does not complete all INT-04. Separately versioned and reviewed
contracts are still required for the PV/inverter, EVSE, and infrastructure
capability-pack catalogs; exact native mappings and normative dispositions;
gateway composition; and target bindings. The accepted thermal and storage packs
do not close those three follow-ons or turn candidate native rows into
normative mappings.

Matter draft and eeBUS source gaps stay explicit. Affected mappings cannot
become normative merely because the kernel v1 types can represent them.

## Version rule

An accepted API lives in an explicit versioned directory and states its status,
compatibility policy, owning implementation package, validation commands,
unresolved questions, and correction criteria. A breaking change requires a new
major contract directory. Illustrative planning sketches and conceptual examples
outside an accepted directory are not stable or executable API.
