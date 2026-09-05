# AGENTS

## Purpose and ownership

`helianthus-docs-semantic` owns reusable, cross-protocol Project Helianthus
semantic architecture, public API contracts, semantic versioning rules,
projection contracts, and migration documentation.

It does not own transport framing or I/O, protocol lifecycle, vendor/profile
qualification, native decoding or identity, raw protocol evidence, gateway
runtime composition, output implementation, consumer behavior, release plans,
or private product material. Route protocol-native facts to their public native
documentation owner and link them as evidence rather than copying them into a
universal claim.

Preserve exact values and units, time domains, source lineage, alternatives and
conflicts, capability lifecycle, observed/inferred/qualified/promoted/
unsupported/unknown distinctions, and explicit projection loss. Do not turn a
catalog entry, similar concept, address, model string, or UI observation into a
qualified semantic mapping.

## Workflow

1. Reconcile `origin/main`, the working tree, related issues, branches, pull
   requests, reviews, and checks before editing.
2. Use one scoped issue and an `issue/<number>-<slug>` branch created from the
   current `origin/main`. Keep unrelated work out of the branch.
3. Put accepted API contracts in explicit versioned paths. State the status,
   evidence basis, compatibility effect, unresolved questions, and falsifiers.
   Conceptual examples are not executable or stable API unless the document
   explicitly says they are accepted.
4. Make durable factual claims traceable to publishable, versioned evidence.
   Mark hypotheses and unknowns. Copy no restricted standards text.
5. Run `./scripts/check_docs.sh` from a standalone clone before pushing and add
   focused validation when a document introduces machine-significant rules.
6. Open a linked pull request with scope, evidence, validation, documentation
   dependencies, and residual risk. Resolve valid P0-P2 findings, then obtain a
   fresh exact-HEAD `NO_BLOCKING_FINDINGS` review.
7. Squash merge only after applicable checks are green. Verify remote `main`,
   issue, pull request, and branch state, then stop at the requested boundary.

## Documentation routing

Protocol-neutral semantic contracts belong here. Their code, types, and
compatibility fixtures belong in
[`Project-Helianthus/helianthus-semreg`](https://github.com/Project-Helianthus/helianthus-semreg).
Protocol-native behavior and evidence remain in the corresponding public docs
repository, including `helianthus-docs-ebus`, `helianthus-docs-eebus`,
`helianthus-docs-modbus`, and `helianthus-docs-canbus`. GREE VRF CAN/UART
material is currently canonical under `helianthus-docs-canbus/protocols/gree`.

Typed semantic contracts needed by the software product are versioned
implementation inputs. A future descriptive language, IR, generation, or code
reduction design must be documented separately and must preserve accepted typed
behavior; it cannot silently redefine the typed API.

## Safety and publication boundaries

Public documentation and validation must not depend on private repositories,
private artifacts, local network access, personal laboratory equipment, or
credentials. Never publish personal data, serials, network coordinates, device
fingerprints, private captures, or unsafe write recipes.

Any credential handling, real installation, destructive or irreversible action,
safety-relevant control, or live-device write requires explicit operator
confirmation at action time. Documentation of native reads and qualification
must keep them bounded, version-aware, and fail-closed.
