# Issue #25 Growatt BMS RS-485 v2.02 storage mapping — author evidence

## Candidate identity

- Repository: `Project-Helianthus/helianthus-docs-semantic`
- Issue: [#25](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/25)
- Branch: `issue/25-growatt-bms-storage-mapping`
- Base: `ed33276cddb2dd86757efcf335c95936bdf4efe2`
- Original mapping candidate head: `3fa3800c9c91f0222940a69fb52acaeb6cb56afa`
- Final mapping candidate head: `7caa360ce5d46ca1a9fe9a9c5cb440f08eaaddaa`
- Final mapping candidate tree: `b8a189d610a6a8a11b46ae3baed73817e0e0152e`

The candidate adds a public, source-specific mapping gate from the exact
Growatt 1xSxxP RS-485 v2.02 native tuple into
`helianthus.pack.storage@1.1.0`. It pins the accepted gateway main/tree and
reviewed source, docs-semantic/SemReg/storage/docs-modbus/modbusreg/native
inputs, four FC03 slices, selected unicast unit, configured semantic asset and
source identities, stable binding identity, provenance, lifecycle, and
qualification boundary.

## Files and validation

- `api/v1/mappings/growatt-bms-rs485-v202-storage-v1.{md,json}`: publishable
  evidence, exact/transform/withhold dispositions, unsupported fields, and
  atomic consumer-cutover requirement.
- `scripts/validate_growatt_bms_rs485_v202_storage_mapping.py`: executes a
  complete positive native-to-SemReg output, the partial soft-start output, and
  thirteen rejected scenarios, including combined-error precedence.
- `scripts/test_validate_growatt_bms_rs485_v202_storage_mapping.py`: eighteen
  focused contract mutations reject pins, native tuple/unit/slices, physical
  qualification, configured identity, all lifecycle evidence, exact/loss
  semantics, withheld and unsupported boundaries, requested items, precedence,
  operations, and consumer cutover.

The final offline synthetic scenario uses four
`GrowattBMSRS485ObservationEvidence`-shaped FC03 slice records, with individual
numeric request IDs, CRC-valid request/response ADUs, exact uint16 word counts,
and a shared unit and transport generation. It validates opaque asset, source,
binding and lifecycle IDs, exact receipt axes, typed/raw equality, and storage
bounds before producing canonical SemReg decimals, symbols, FactKeys,
source paths, requested items, dispositions, losses, reasons, and zero
operations. Soft-start withholds only operating state and retains six valid
independent facts.
- Standalone-clone `./scripts/check_docs.sh`: PASS at exact source
  `7caa360ce5d46ca1a9fe9a9c5cb440f08eaaddaa`; log SHA-256
  `e67737b22e58f714cba2d396a6619f836999567fa040d2767c94186895803e57`.

Focused RED-first evidence: the mapping-gate JSON was absent before this
candidate; the newly added validators then passed the positive vector and
rejected all declared negative and focused mutations.

## Residual boundaries

Physical qualification is false; offline mapping qualification needs configured
non-secret asset/source identities and complete native/lifecycle evidence. No
device access, serial I/O, runtime admission, support claim, deployment, write, operation, authority,
acknowledgement, readback, retry, or consumer publication is authorized.
Ampere-hour capacity is retained as Ah and is never derived or converted to
kWh. Fields without an exact storage definition remain native provenance,
opaque, unsupported, or withheld. A later semantic MCP/GraphQL/Portal/Home
Assistant implementation must perform one atomic SemReg cutover and remove the
legacy semantic path, fallback, comparator, compatibility-only path, and
dual publication.
