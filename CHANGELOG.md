---
status: "unreleased change record; implementation and consumer adoption remain pending."
---

# Changelog

## Unreleased

- The [semantic resource graph contract](api/v1/graph.md) of increment 1
  defines resources and their identity, typed relations, planes, lenses, the
  element catalog rules, activation, publication and coherence, and amends the
  kernel, serialization and acceptance pages in place. The five stable graph
  errors join the exhaustive v1 list. The new record members are optional and
  omitted when empty, so records without graph content keep their canonical
  bytes and identifiers, and the kernel vectors run unchanged without the
  catalog. Implementations follow in semreg and the gateway.
- Add the element catalog schema
  [`api/v1/element-catalog-v1.schema.json`](api/v1/element-catalog-v1.schema.json)
  for the contract `helianthus.semantic.element-catalog/v1`, and its
  repository-contained, dependency-free checker
  [`scripts/json_schema_subset_v1.py`](scripts/json_schema_subset_v1.py), which
  supports a fixed keyword subset including the conditionals and refuses every
  other keyword in a schema. Additive: no existing document, schema or
  validator changes. The catalog data and its cross-entry validator follow in
  later changes.
- Until the 0.7 release a breaking change may be made in place in an existing
  versioned directory, and each such change is listed in the new
  [in-place change record](api/README.md#in-place-change-record) of the
  [version rule](api/README.md#version-rule); from the release on a breaking
  change requires a new major directory. The PV, EVSE and infrastructure pack
  pages point to the version rule, the
  [pack metadata](api/v1/pack-metadata-v1.md) states that immutable means
  read-only at run time, the
  [family-catalog](api/v1/family-catalog-v1.md) compatibility rule applies from
  the release on, and the
  [ownership layering](architecture/repository-ownership-v1.md) names the
  semantic resource graph. No contract data, vector, fixture or validator
  changes; consumers need no action.
- Breaking: rename the three thermal value members as recorded in the
  [naming contract](architecture/naming-contract.md). Coordinate consumers in
  one wave; no alias or migration path is provided before 1.0.
- Breaking: rename the wire reason and eeBUS mapping state
  `unknown_pending_std_01` to `unknown_pending_normative_source` in the
  [family-catalog contract](api/v1/family-catalog-v1.md), the pack pages and
  acceptance vectors, their validators, the [API index](api/README.md) and the
  [donor ledger](compatibility/donor-ledger.md). The meaning is unchanged. The
  old spelling survives only as a documentary correspondence; no validator,
  fixture expectation or alias accepts it. Merge together with the matching
  SemReg rename; consumers move in the same wave.
