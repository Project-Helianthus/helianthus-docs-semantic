# Semantic API publication status

## Kernel v1

The versioned kernel contract consists of:

- [typed records and invariants](v1/kernel.md);
- [deterministic JSON serialization](v1/serialization.md);
- [acceptance rules and stable errors](v1/acceptance.md);
- [positive and negative acceptance vectors](v1/acceptance-vectors.json); and
- [detached PublicationKernel fork falsifiers](v1/kernel-fork-acceptance.json).

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
second typed capability pack at exact PackRef `1.1.0`. Its vectors are checked
by `scripts/validate_storage_bms_pack_v1.py`. Version 1.0.0 is superseded and
non-implementable for operations because its interlock was not machine-identifiable.
CAN V1.04 and RS-485 1xSxxP rows are offline candidate evidence only; eeBUS
remains `unknown_pending_std_01`.

The [Growatt BMS RS-485 v2.02 mapping gate](v1/mappings/growatt-bms-rs485-v202-storage-v1.md)
freezes the accepted read-only source-specific field and lifecycle boundary for
later SemReg work. It does not activate consumer publication or control.

The [Tesla Gen3 WC3 24.44.3 EVSE current-limit mapping gate](v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md)
freezes the source-specific read-only mapping of persistent configured current
and an evidence-qualified provisional allocated current. It exposes no sender,
route, authority, consumer binding, or control.

## PV/inverter pack v1

[`helianthus.pack.pv/v1`](v1/packs/pv-inverter-v1.md) is the accepted third
INT-04 capability pack. It defines typed generation, electrical, energy,
state, topology, lifecycle, projection-loss, conservative power-limit operation,
and Portal-contribution contracts. Its [positive and negative
vectors](v1/packs/pv-inverter-acceptance-vectors.json) are checked by
`scripts/validate_pv_inverter_pack_v1.py`. Growatt and Fronius rows remain
candidate-only native-owner evidence; Fronius is offline-only with no write
authority. Growatt TL3-X applicability is blocked by docs-modbus #143 and
modbusreg #196. Affected eeBUS rows remain
`unknown_pending_std_01`.

## EVSE pack v1

[`helianthus.pack.evse/v1`](v1/packs/evse-v1.md) is the accepted fourth
INT-04 capability pack. It defines typed connector/phase/session/meter topology,
telemetry, current-limit distinctions, lifecycle, loss, conservative
allocated-current operations, and Portal contributions. Its
[positive and negative vectors](v1/packs/evse-acceptance-vectors.json) are
checked by `scripts/validate_evse_pack_v1.py`. Tesla FBE0/FDE0 is offline
candidate evidence with no sender, control route, or live authority. eeBUS
remains `unknown_pending_std_01`; the Matter draft is not conformance.

## Electrical infrastructure pack v1

[`helianthus.pack.infrastructure/v1`](v1/packs/infrastructure-v1.md) is the
accepted fifth INT-04 capability pack. It defines protocol-neutral electrical
site, grid-connection, feeder, circuit, phase, and meter topology; typed
telemetry and state; lifecycle and loss boundaries; and Portal read
contributions. Its [positive and negative vectors](v1/packs/infrastructure-acceptance-vectors.json)
are checked by `scripts/validate_infrastructure_pack_v1.py`. It publishes no
operation, breaker actuation, import/export control, sender, control route, or
live authority. eBUS and Modbus are non-universal evidence only, eeBUS remains
`unknown_pending_std_01`, and Matter is not conformance.

Primary contract ID: `helianthus.semantic.kernel/v1`; the pure time-evaluation
view uses `helianthus.semantic.evaluation/v1`, and pure presentation results use
`helianthus.semantic.selection/v1`. Selection receives the complete matching
immutable snapshot and evaluation view; it has no hidden store or native lookup.
The contract becomes normative for the Project Helianthus kernel implementation
when merged into `main`. The owning Go module is
[`Project-Helianthus/helianthus-semreg`](https://github.com/Project-Helianthus/helianthus-semreg).

The kernel's retained-observation lifecycle contract is
[`api/v1/retained-observation-acceptance.json`](v1/retained-observation-acceptance.json).
It keeps pre-fence or retired-source observed evidence separately from current
facts through the original deadline, never as selection or operation authority.
A later source retirement advances a fenced binding tombstone to `retired` while
preserving the original retained candidate and its removal event.

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

The accepted [immutable pack metadata v1](v1/pack-metadata-v1.md) exports exact
units, dimensions, ownership and operation shapes from the five accepted packs
for a future SemReg query API. It neither implements that API nor creates a
Gateway semantic table.

This publication completes the five typed INT-04 catalogs. Separately versioned
and reviewed contracts are still required for exact native mappings and
normative dispositions;
gateway composition; and target bindings. The accepted thermal, storage/BMS,
PV/inverter, EVSE, and infrastructure packs do not turn candidate native rows
into normative mappings.

Matter draft and eeBUS source gaps stay explicit. Affected mappings cannot
become normative merely because the kernel v1 types can represent them.

## Version rule

An accepted API lives in an explicit versioned directory and states its status,
compatibility policy, owning implementation package, validation commands,
unresolved questions, and correction criteria. A breaking change requires a new
major contract directory. Illustrative planning sketches and conceptual examples
outside an accepted directory are not stable or executable API.
