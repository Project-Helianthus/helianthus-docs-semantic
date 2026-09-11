# Immutable pack metadata v1

`helianthus.semantic.pack-metadata/v1` is an accepted, protocol-neutral read-only contract for the five accepted capability packs. Its machine-readable fixture is [pack-metadata-v1.json](pack-metadata-v1.json), constrained by the [JSON Schema](pack-metadata-v1.schema.json) and validated against the exact accepted source contracts by `scripts/validate_pack_metadata_v1.py`.

This contract provides SemReg's future external descriptor validator with already accepted pack facts. It does not define Portal descriptors, labels or views; native membership; protocol mappings; operation admission; runtime composition; compatibility aliases; or control behavior. eeBUS normative mappings remain unresolved where their owning contract says so.

## Data and ordering

Each record is an exact `PackRef` or `DefinitionRef`. The fixture contains thermal/HVAC 1.0.0, PV/inverter 1.0.0, storage/BMS 1.1.0, EVSE 1.0.0, and electrical infrastructure 1.0.0. Its source paths are accepted vectors, with storage field and operation detail from accepted storage contract tables.

`units` and `definitions` are bytewise sorted by `(pack id, pack version, definition id, definition version)`. Fields include their exact canonical unit (or `null` for a non-quantity) and dimension. Services include their exact fact-key dimension. Capabilities include their owning service. Operations use the exact five-part `{operation, capability, service, argument, effect}` shape. `storage.state.soc` has canonical `unit.percent`; neither `storage.state_of_charge` nor `storage.unit.percent` is a definition.

The constructor required of the owning SemReg implementation rejects duplicate, ambiguous, cross-pack, wrong-version, missing-definition, wrong-unit or malformed relations that differ from the accepted source. It deep-copies inputs and returns deep copies of every collection. This repository does not implement the SemReg runtime API.

## Required queries

| Query | Required result |
| --- | --- |
| `Packs()` | Canonically ordered deep copy of the five `PackRef`s. |
| `HasDefinition(ref)` | True only for an exact exported definition, including quantity units. |
| `CanonicalUnit(field)` | Exact unit for an exact quantity field; no result otherwise. |
| `ServiceOwnsCapability(service, capability)` | True only for exact same-pack ownership. |
| `FieldMatches(field, service, capability)` | True only when ownership holds and field/service dimensions are equal. |
| `OperationMatches(operation, capability, service, argument, effect)` | True only for one exact pack-owned five-part shape. |

Every unknown, wrong-version, cross-pack, wrong-unit, service, capability, operation, argument, or effect query fails closed. Lookup keys are typed tuples, not concatenated strings.

## Validation and limits

Run `python3 scripts/validate_pack_metadata_schema_v1.py`, `python3 scripts/validate_pack_metadata_v1.py`, `python3 scripts/test_validate_pack_metadata_v1.py`, then `./scripts/check_docs.sh`. The repository-contained validator executes the Draft 2020-12 features used by this strict schema without a third-party dependency and separately enforces the exact five accepted PackRefs. The focused tests include raw-schema missing/malformed references, malformed operations, extra/incorrect packs, source drift mutations, canonical-order rejection, complete FieldMatches typed-reference probes, and deep-copy query isolation. They do not establish implementation, native qualification, Portal acceptance, interoperability or physical-device behavior.
