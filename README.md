# helianthus-docs-semantic

`helianthus-docs-semantic` is the public Project Helianthus home for reusable,
cross-protocol semantic architecture and API documentation.

## Contract status

The [semantic kernel v1 contract](api/v1/kernel.md) defines the protocol-neutral
types, serialization, validation, and acceptance vectors required for its own
dependent implementation in `helianthus-semreg`. It becomes normative for that
Helianthus implementation when merged into `main`.

This kernel contract does not complete all INT-04 capability packs or native
mappings, implement INT-05 product code, settle unresolved normative versions,
or establish target conformance, release, or hardware acceptance.

## Documentation map

- [Repository ownership and boundaries](architecture/repository-ownership-v1.md)
  records the accepted owner split without publishing an executable schema.
- [API publication status](api/README.md) defines how a future version becomes
  active and links the current kernel contract.
- [Kernel v1 acceptance](api/v1/acceptance.md) defines the concrete positive and
  negative vectors required of later code.
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
