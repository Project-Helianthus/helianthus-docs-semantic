# helianthus-docs-semantic

`helianthus-docs-semantic` is the public Project Helianthus home for reusable,
cross-protocol semantic architecture and API documentation.

## Bootstrap status

This repository currently establishes documentation ownership and reviewed
conceptual boundaries. It does not publish a complete or frozen semantic API,
complete INT-04, implement INT-05, settle unresolved normative versions, or
establish conformance, release, or hardware acceptance.

The first complete typed architecture/API contract will be added through a
separate scoped issue and independent review. Until that contract is accepted,
the [API directory](api/README.md) contains no active version.

## Documentation map

- [Repository ownership and boundaries](architecture/repository-ownership-v1.md)
  records the accepted owner split without publishing an executable schema.
- [API publication status](api/README.md) defines how a future version becomes
  active.
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

The check verifies required bootstrap files, whitespace, and repository-local
Markdown links. No protocol, transport, conformance, deployment, or physical
smoke gate applies to this ownership-only bootstrap.

## License

This repository is licensed under the GNU Affero General Public License v3.0.
See [LICENSE](LICENSE).
