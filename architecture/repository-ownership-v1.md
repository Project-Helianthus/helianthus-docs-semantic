# Protocol-neutral semantic repository ownership v1

Status: accepted bootstrap ownership boundary. This document does not define a
complete semantic schema, freeze an executable API, complete INT-04, implement
INT-05, or establish normative, conformance, release, or hardware acceptance.

## Purpose

Project Helianthus uses a protocol-neutral semantic layer so native energy
protocols can retain their full evidence and capabilities while consumers use
stable cross-protocol contracts. The public code owner is
[`helianthus-semreg`](https://github.com/Project-Helianthus/helianthus-semreg).
This repository owns the reusable architecture and API documentation.

The intended layering is:

```text
protocol-native transport and evidence
  -> protocol/profile registry and qualification
  -> protocol-neutral semantic facts and capabilities
  -> target-specific projection with declared loss
  -> consumers and output bindings
```

No protocol is the universal semantic source. Existing eBUS and PV contracts
are migration donors and compatibility comparators, not authority over other
protocols.

## Ownership split

| Owner | Responsibilities | Exclusions |
|---|---|---|
| Native transport | Framing, sessions, bounded I/O, retries, and native protocol mechanics | Vendor meaning, cross-protocol semantics, consumer policy |
| Native protocol/profile registry | Native identity, version/profile qualification, decoding, evidence, and native capabilities | Universal semantic ownership and target projection policy |
| `helianthus-semreg` | Protocol-neutral kernel, versioned capability packages, semantic validation, interfaces, and compatibility fixtures | Native framing/I/O, vendor scanning, gateway orchestration, UI implementation |
| Gateway/runtime | Driver lifecycle, composition, source attachment, operation dispatch, and public runtime availability | Redefining native evidence or semantic meaning |
| Output binding | One target/version mapping with explicit transformation, withholding, and loss | Upstream qualification or command authority |
| Consumer | Stable promoted facts and supported operations | Native decoding, hidden mapping, or upstream semantic definition |

The semantic kernel must build without transport, protocol, registry, gateway,
vendor, output, UI, sibling-checkout, or private dependencies. A device may
expose several independently versioned capability packages; packages do not own
native mappings.

## Evidence and state boundary

Raw frames, registers, protocol objects, captures, and native identities remain
available under the native owner's public evidence and access contract. A
semantic fact references that evidence and transformation lineage without
claiming that the semantic repository captured or qualified it.

The contract must preserve distinct states for observed, inferred, qualified,
promoted, unsupported, and unknown information. Runtime availability,
freshness, validity, and capability withdrawal are separate from qualification.
A missing value is not numeric zero, an unknown symbol is not a supported known
symbol, and a catalog entry is not a device capability.

When several sources describe an asset, their candidates and evidence remain
visible. Similar values, names, addresses, or topology do not prove identity.
Selection for presentation does not destroy alternatives, hide conflicts, or
grant command authority. Partial source failure must not erase unrelated
last-known good fields when the owning contract permits retention.

## Lifecycle and operations boundary

Native providers and the gateway own live driver lifecycle. Semantic capability
publication must retain the source and provider generation that justified it.
Withdrawal or replacement fences the old generation; late observations and
operations from that generation cannot silently reactivate it.

The future typed operation contract must distinguish intent admission, exact
route selection, native dispatch, acknowledgement, confirming readback, and
outcome. Timeout is not proof that no side effect occurred. Observation and
projection never create command authority. The exact types, serialization,
admission rules, and recovery behavior remain future reviewed API work.

## Projection boundary

Every output binding owns a mapping for one target and target version. The
mapping must account for requested facts, relations, capabilities, and
operations as exact, transformed, withheld, unrepresentable, unsupported, or
unknown. Transformations record material unit, range, precision, time, symbol,
or provenance loss. Similar concepts across Matter, eeBUS, GraphQL, MCP, Home
Assistant, Prometheus, or Portal do not prove equivalent behavior or
conformance.

## Version and delivery boundary

Software 0.7 owns typed semantic contracts and their compatible product
integration. Descriptive language, IR, generation, and measured code reduction
belong to later 0.8 work after the typed contracts are accepted and must preserve
their behavior.

This bootstrap activates no API version. A later reviewed document must define
the complete typed kernel and capability-package contracts, validation,
compatibility fixtures, and unresolved normative dispositions before dependent
implementation is accepted. See [API publication status](../api/README.md).
