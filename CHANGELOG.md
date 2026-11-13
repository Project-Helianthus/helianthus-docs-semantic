---
status: "unreleased change record; implementation and consumer adoption remain pending."
---

# Changelog

## Unreleased

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
