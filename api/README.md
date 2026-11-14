# Semantic API publication status

## Kernel v1

The versioned kernel contract consists of:

- [typed records and invariants](v1/kernel.md);
- [deterministic JSON serialization](v1/serialization.md);
- [acceptance rules and stable errors](v1/acceptance.md);
- [resource graph, relations, planes, lenses and element catalog
  rules](v1/graph.md);
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
remains `unknown_pending_normative_source`.

The [Growatt BMS RS-485 v2.02 mapping gate](v1/mappings/growatt-bms-rs485-v202-storage-v1.md)
freezes the accepted read-only source-specific field and lifecycle boundary for
later SemReg work. It does not activate consumer publication or control.

The [Tesla Gen3 WC3 24.44.3 EVSE current-limit mapping gate](v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md)
freezes the source-specific read-only mapping of persistent configured current
and an evidence-qualified provisional allocated current. It exposes no sender,
route, authority, consumer binding, or control.

The [Huawei SUN2000 PV mapping gate](v1/mappings/huawei-sun2000-pv-v1.md) maps the
admitted facts of the two offline monitoring profiles to the PV pack, with grades
inherited from the native contract and every other native item withheld or
native-only with a stated loss. The [LUNA2000 storage gate](v1/mappings/huawei-luna2000-storage-v1.md)
and the [gateway-meter Infrastructure gate](v1/mappings/huawei-gateway-meter-infrastructure-v1.md)
publish nothing today: no battery profile is admitted and no meter is decoded. They
record where the existing Storage and Infrastructure packs will take the facts, keep
capacity in energy units withheld, and expose no consumer binding or control.

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
`unknown_pending_normative_source`.

## EVSE pack v1

[`helianthus.pack.evse/v1`](v1/packs/evse-v1.md) is the accepted fourth
INT-04 capability pack. It defines typed connector/phase/session/meter topology,
telemetry, current-limit distinctions, lifecycle, loss, conservative
allocated-current operations, and Portal contributions. Its
[positive and negative vectors](v1/packs/evse-acceptance-vectors.json) are
checked by `scripts/validate_evse_pack_v1.py`. Tesla FBE0/FDE0 is offline
candidate evidence with no sender, control route, or live authority. eeBUS
remains `unknown_pending_normative_source`; the Matter draft is not conformance.

## Electrical infrastructure pack v1

[`helianthus.pack.infrastructure/v1`](v1/packs/infrastructure-v1.md) is the
accepted fifth INT-04 capability pack. It defines protocol-neutral electrical
site, grid-connection, feeder, circuit, phase, and meter topology; typed
telemetry and state; lifecycle and loss boundaries; and Portal read
contributions. Its [positive and negative vectors](v1/packs/infrastructure-acceptance-vectors.json)
are checked by `scripts/validate_infrastructure_pack_v1.py`. It publishes no
operation, breaker actuation, import/export control, sender, control route, or
live authority. eBUS and Modbus are non-universal evidence only, eeBUS remains
`unknown_pending_normative_source`, and Matter is not conformance.

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

## Family catalog v1

The [family catalog contract v1](v1/family-catalog-v1.md) defines the
`helianthus.semreg.family-catalog/v1` document: per-family `state` (the kernel
`Qualification` set), `composition`, `reason` and evidence references. It is
checked by `scripts/validate_family_catalog_v1.py` and states no family's actual
state; states live in the SemReg fixture with their evidence.

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
unresolved questions, and correction criteria. Until the Helianthus 0.7
release, the project owner may require a breaking change to be made in place in
an existing versioned directory; each such change is listed in this page's
in-place change record with its date, scope and the locks it moves. From the
0.7 release on, a breaking change requires a new major contract directory.
Illustrative planning sketches and conceptual examples outside an accepted
directory are not stable or executable API.

## In-place change record

Each in-place change made under the exception of the version rule before the
0.7 release is listed here, oldest first; the record closes at the release.

| Date | Change | Locks moved |
|---|---|---|
| 2026-11-14 | Version rule exception for the 0.7 release cycle; pack metadata "immutable" means read-only at run time; family-catalog compatibility applies from the release on; the ownership layering names the semantic resource graph; the PV, EVSE and infrastructure pack pages point to the version rule. | None: no vector, fixture, schema, digest or validator changes. |
| 2026-11-14 | Graph contract page [graph.md](v1/graph.md) added and the kernel, serialization and acceptance pages amended in place (graph.md section 17). | `scripts/validate_kernel_v1.py` and `scripts/test_validate_kernel_rules.py` take the documented error set as the union of the acceptance.md and graph.md headings; `api/v1/acceptance-vectors.json`, its `error_ids` and every pinned digest unchanged. |

## Matter 1.6.1 target

The [Matter 1.6.1 adoption projection contract](v1/targets/matter-1.6.1-v1.md)
and [accounting ledger](v1/targets/matter-1.6.1-v1.json) retain the five-pack
roster with one phase-qualified current projection and explicit irreversible
loss. Source-model inspection is separate from execution qualification. This
pre-1.0 target does not activate the pinned feed or replace the historical
Matter 1.7 ledger and checker.
