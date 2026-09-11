# Issue #29 author evidence

## Scope

This change freezes `helianthus.semantic.pack-metadata/v1` as a public machine-readable input for the narrow future SemReg metadata registry issue. It exports exact facts from the five accepted pack contracts only.

## Evidence basis

- `api/v1/packs/*-acceptance-vectors.json` supplies thermal, PV, EVSE and infrastructure facts.
- `api/v1/packs/storage-bms-contract-tables.json` supplies accepted storage 1.1.0 facts.
- Gateway #973's architecture report requires this SemReg-owned frozen view and rejects copied Gateway semantic tables.

## Limits

No SemReg runtime code, Gateway descriptor, Portal label or view, native mapping, operation admission, compatibility alias, deployment, device action or 0.8 work is included. No eeBUS normative mapping is asserted.

## P2 correction evidence

The reference query model compares all four typed DefinitionRef components for
FieldMatches. Focused hostile probes alter pack ID, pack version, definition ID
and definition version for every valid field/service/capability relation and
require rejection. The strict Draft 2020-12 schema defines every published
record shape, and its repository-contained validator runs in the configured
documentation check without an external package. Raw schema probes reject
omitted or malformed references, malformed operations, and extra or incorrect
packs.
