# helianthus-docs-semantic

`helianthus-docs-semantic` is the public Project Helianthus home for reusable,
cross-protocol semantic architecture and API documentation.

## Contract status

The [semantic kernel v1 contract](api/v1/kernel.md) defines the protocol-neutral
types, serialization, time-only evaluation views, multi-source dependency
lifecycle, exact pack ownership and operation evidence, validation, and
acceptance vectors required for its own dependent implementation in
`helianthus-semreg`. It becomes normative for that Helianthus implementation
when merged into `main`.

This kernel contract does not complete all INT-04 capability packs or native
mappings, implement INT-05 product code, settle unresolved normative versions,
or establish target conformance, release, or hardware acceptance.

The accepted [thermal/HVAC pack v1](api/v1/packs/thermal-hvac-v1.md),
[storage/BMS pack v1](api/v1/packs/storage-bms-v1.md),
[PV/inverter pack v1](api/v1/packs/pv-inverter-v1.md),
[EVSE pack v1](api/v1/packs/evse-v1.md), and [electrical infrastructure pack
v1](api/v1/packs/infrastructure-v1.md) provide all five typed INT-04
vocabularies and machine-checked acceptance vectors. Infrastructure is
electrical site/grid/feeder/circuit semantics, not deployment infrastructure;
it is read-only until a separately qualified native route and action-time
authority exist. Affected eeBUS rows remain unknown pending STD-01.

## Documentation map

- [Repository ownership and boundaries](architecture/repository-ownership-v1.md)
  records the accepted owner split without publishing an executable schema.
- [API publication status](api/README.md) defines how a future version becomes
  active and links the current kernel contract.
- [Kernel v1 acceptance](api/v1/acceptance.md) defines the concrete positive and
  negative vectors required of later code.
- [Immutable pack metadata v1](api/v1/pack-metadata-v1.md) freezes the exact
  five-pack read-only facts required by the future SemReg descriptor validator.
- [Thermal/HVAC pack v1](api/v1/packs/thermal-hvac-v1.md) defines the accepted
  first capability pack and its native-evidence boundary.
- [Storage/BMS pack v1.1](api/v1/packs/storage-bms-v1.md) defines accepted typed
  storage vocabulary, a qualified-current interface interlock predicate, and
  offline candidate boundaries.
- [Growatt BMS RS-485 v2.02 mapping gate](api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md)
  freezes a read-only source-specific projection and its withheld/unsupported
  boundary; it does not qualify a device or publish a consumer binding.
- [Tesla Gen3 WC3 24.44.3 EVSE current-limit mapping gate](api/v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md)
  freezes read-only configured and evidence-qualified provisional-current facts;
  it has no sender, control route, authority, consumer binding, or live action.
- [PV/inverter pack v1](api/v1/packs/pv-inverter-v1.md) defines accepted
  electrical and topology vocabulary with conservative admitted limit actions.
- [EVSE pack v1](api/v1/packs/evse-v1.md) defines accepted charging topology,
  telemetry, and a conservative admitted allocated-current action.
- [Electrical infrastructure pack v1](api/v1/packs/infrastructure-v1.md)
  defines accepted site/grid/feeder/circuit/phase/meter topology, telemetry,
  lifecycle, loss, and a read-only operation boundary.
- [Compatibility donor ledger](compatibility/donor-ledger.md) links immutable
  public migration inputs and states their limits.
- [Native documentation owners](evidence/native-documentation-owners.md) routes
  protocol facts and raw evidence to their source owners.

## Core boundary

The semantic layer preserves the richest qualified facts from each native
source. It retains provenance, exact values and units, time, quality,
alternatives, conflicts, capability lifecycle, and explicit projection loss.
Candidate, unknown, unsupported, unavailable, invalid, stale, and withdrawn are
not interchangeable states.

Native transports and registries retain framing, I/O, protocol lifecycle,
qualification, decoding, native identity, and raw evidence. The gateway retains
runtime composition and driver lifecycle orchestration. Consumers use stable,
promoted contracts and do not define upstream meaning.

## Validation

Run the complete document check from a standalone clone:

```sh
./scripts/check_docs.sh
```

The check verifies required files, whitespace, repository-local Markdown links,
and structural consistency among the kernel contract, stable errors, coverage
areas, and acceptance vectors. It does not implement semantic behavior.

## License

This repository is licensed under the GNU Affero General Public License v3.0.
See [LICENSE](LICENSE).
