# Issue #25 Growatt BMS RS-485 v2.02 storage mapping — author evidence

## Candidate identity

- Repository: `Project-Helianthus/helianthus-docs-semantic`
- Issue: [#25](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/25)
- Branch: `issue/25-growatt-bms-storage-mapping`
- Base: `ed33276cddb2dd86757efcf335c95936bdf4efe2`
- Mapping candidate head: `3fa3800c9c91f0222940a69fb52acaeb6cb56afa`
- Mapping candidate tree: `3acf21cc36febe1431f3f2f5920fb26b37c0041c`

The candidate adds a public, source-specific mapping gate from the exact
Growatt 1xSxxP RS-485 v2.02 native tuple into
`helianthus.pack.storage@1.1.0`. It pins the accepted gateway main/tree and
reviewed source, docs-semantic/SemReg/storage/docs-modbus/modbusreg/native
inputs, four FC03 slices, selected unicast unit, provenance, lifecycle, and
qualification boundary.

## Files and validation

- `api/v1/mappings/growatt-bms-rs485-v202-storage-v1.{md,json}`: publishable
  evidence, exact/transform/withhold dispositions, unsupported fields, and
  atomic consumer-cutover requirement.
- `scripts/validate_growatt_bms_rs485_v202_storage_mapping.py`: one accepted
  vector and seven negative vectors.
- `scripts/test_validate_growatt_bms_rs485_v202_storage_mapping.py`: nine
  focused mutations rejected: source revision, gateway tree, unit, identity,
  lifecycle promotion, Ah-to-kWh retyping, loss omission, operation grant, and
  consumer fallback.
- `./scripts/check_docs.sh`: PASS. It includes the new validator and mutation
  coverage, plus all existing repository checks.

Focused RED-first evidence: the mapping-gate JSON was absent before this
candidate; the newly added validators then passed the positive vector and
rejected all declared negative and focused mutations.

## Residual boundaries

Physical and semantic qualification are false. No device access, serial I/O,
runtime admission, support claim, deployment, write, operation, authority,
acknowledgement, readback, retry, or consumer publication is authorized.
Ampere-hour capacity is retained as Ah and is never derived or converted to
kWh. Fields without an exact storage definition remain native provenance,
opaque, unsupported, or withheld. A later semantic MCP/GraphQL/Portal/Home
Assistant implementation must perform one atomic SemReg cutover and remove the
legacy semantic path, fallback, comparator, compatibility-only path, and
dual publication.
