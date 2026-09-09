# Issue #27 Tesla Gen3 WC3 EVSE mapping — author evidence

## Candidate identity

- Repository: `Project-Helianthus/helianthus-docs-semantic`
- Issue: [#27](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/27)
- Branch: `issue/27-tesla-wc3-evse-mapping`
- Base: `f830ace6c2b9dd1af0e87ce808fa545662578418`
- Mapping implementation head: `18164a84a6e28ed44ed99f9169a4cb300464c4c1`
- Mapping implementation tree: `a4a8d7d30243d4cc207f596542603a9066386967`

The source-specific gate maps only the documented integer-ampere persistent
`MaxOutputCurrentAmps` to `evse.limit.configured_current`, and the distinct,
correlated provisional `LimitCurrentMaxAmps` to
`evse.limit.allocated_current` when its timeout is finite (`1..86399`) and
`InhibitCharging` is false. It retains a zero timeout as explicitly withheld.
Both emitted values use canonical exact decimal coefficient/exponent values and
`unit.ampere`; no power, energy, phase, session, topology, readiness, SOC,
thermal, fault, interlock, or meter fact is invented.

## Public evidence pins

- Generic semantic input: `api/v1/packs/evse-v1.md` at base
  `f830ace6c2b9dd1af0e87ce808fa545662578418`.
- SemReg EVSE package:
  [`f3f761bc`](https://github.com/Project-Helianthus/helianthus-semreg/commit/f3f761bc67e10d6a65eba6c13cb4dc51002d6955).
- Tesla native current-limit documentation, accepted docs-modbus issue #127:
  [`6611e20a`](https://github.com/Project-Helianthus/helianthus-docs-modbus/commit/6611e20ac8b2c3e8b953934757346f8a847b30bf).
- Native read-only MCP projection, accepted docs-modbus issue #129:
  [`1127c333`](https://github.com/Project-Helianthus/helianthus-docs-modbus/commit/1127c333de1f1d02305952a58f8745ee05c42e12).
- Typed native retention, accepted modbusreg issue #184:
  [`57f7eb84`](https://github.com/Project-Helianthus/helianthus-modbusreg/commit/57f7eb84f7d4e1173621711bf64624726c71bc75).
- Gateway current main and native-only MCP source:
  [`32244901`](https://github.com/Project-Helianthus/helianthus-ebusgateway/commit/32244901c4c8337266cd348bdad90fb9e8eb0a61).

## Contract, vectors, and validation

`api/v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.{md,json}` fixes
the qualified profile, FC100 source path, configured non-secret asset/EVSE/
connector identity, immutable payload evidence references, receipt/source epoch,
driver generation, qualification, semantic revision, lifecycle generation, and
atomicity. It rejects missing, blank, invalid, reused, or ambiguous identity;
evidence from distinct observations or generations cannot combine.

The mapping validator executes two exact positive outputs and nine hostile
vectors: profile/version, identity, source path, evidence reference, missing
receipt time, unsupported fact, operation attempt, identity ambiguity, and a
combined-error precedence case. Its focused test rejects 17 independently
mutated contract and runtime boundaries, including a changed persistent target,
weakened provisional disposition, outbound enablement, identity derivation,
consumer-cutover escape, and `set_allocated_current` attempt.

Validation passed:

- `python3 scripts/validate_tesla_gen3_wc3_24443_evse_current_limit_mapping.py`
- `python3 scripts/test_validate_tesla_gen3_wc3_24443_evse_current_limit_mapping.py`
- `./scripts/check_docs.sh`
- in an ephemeral public clone pinned to `f3f761bc67e10d6a65eba6c13cb4dc51002d6955`:
  `go test ./semreg/v1/packs/evse`

## Boundaries

This is an offline documentation and fixture gate. Physical qualification is
false. The payloads and FC100 validation remain native evidence, and the MCP
envelope is not semantic authority. All operations remain unavailable: there is
no sender, route, authority, acknowledgement/readback authority, retry, or live
control. No credential, device, private network, deployment, installation, or
live action was accessed.

A later implementation must perform the declared one-SemReg-projection cutover
to versioned semantic MCP, mTLS GraphQL/Portal parity, then applicable Home
Assistant adoption; it must remove fallback, comparator, compatibility adapter,
shadow authority, dual publication, caller-provided provenance, and write
routes.
