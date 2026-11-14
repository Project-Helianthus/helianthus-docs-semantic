---
status: "unreleased change record; implementation and consumer adoption remain pending."
---

# Changelog

## Unreleased

- Add the element catalog schema
  [`api/v1/element-catalog-v1.schema.json`](api/v1/element-catalog-v1.schema.json)
  for the contract `helianthus.semantic.element-catalog/v1`, and its
  repository-contained, dependency-free checker
  [`scripts/json_schema_subset_v1.py`](scripts/json_schema_subset_v1.py), which
  supports a fixed keyword subset including the conditionals and refuses every
  other keyword in a schema. Additive: no existing document, schema or
  validator changes. The catalog data and its cross-entry validator follow in
  later changes.
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
