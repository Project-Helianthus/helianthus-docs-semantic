# Tesla Gen3 WC3 24.44.3 EVSE current-limit mapping gate v1

This accepted source-specific, read-only gate maps qualified Tesla Wall Connector
Gen3 `wc3_24_44_3` current-limit evidence into
`helianthus.pack.evse@1.0.0`. The executable contract is
[tesla-gen3-wc3-24443-evse-current-limit-v1.json](tesla-gen3-wc3-24443-evse-current-limit-v1.json).
It is an offline mapping qualification, not a device-support or physical
qualification claim.

## Publishable inputs and evidence boundary

The native current-limit contract is pinned to
[docs-modbus `6611e20`](https://github.com/Project-Helianthus/helianthus-docs-modbus/commit/6611e20ac8b2c3e8b953934757346f8a847b30bf),
the read-only native-projection revision is
[`1127c333`](https://github.com/Project-Helianthus/helianthus-docs-modbus/commit/1127c333de1f1d02305952a58f8745ee05c42e12),
the typed registry is
[`57f7eb84`](https://github.com/Project-Helianthus/helianthus-modbusreg/commit/57f7eb84f7d4e1173621711bf64624726c71bc75),
the semantic package is
[`f3f761bc`](https://github.com/Project-Helianthus/helianthus-semreg/commit/f3f761bc67e10d6a65eba6c13cb4dc51002d6955),
and gateway composition is
[`32244901`](https://github.com/Project-Helianthus/helianthus-ebusgateway/commit/32244901c4c8337266cd348bdad90fb9e8eb0a61).
The accepted generic EVSE input is `helianthus.pack.evse@1.0.0` at this
repository's base `f830ace6c2b9dd1af0e87ce808fa545662578418`.

Only FC100 family-6 evidence for this exact profile is admissible. Persistent
`t7` to `t8` `MaxOutputCurrentAmps` maps exactly, in integer amperes, to
`evse.limit.configured_current`. The correlated provisional `t25` to `t26` and
`t27` to `t28` `LimitCurrentMaxAmps` maps exactly to
`evse.limit.allocated_current` only when `LimitTimeoutSeconds` is finite
`1..86399` and `InhibitCharging` is false. The zero-timeout form is withheld;
timeout and inhibit themselves have no EVSE fact. Persistent and provisional
facts are separate and never substituted for one another.

The four provisional request/ack/readback payloads, persistent request/terminal
payloads, FC100 decoding, and their immutable digests remain native evidence.
The semantic gate accepts their immutable references only. A source path,
receipt timestamp, source epoch, driver generation, qualification, semantic
revision, lifecycle generation, and one immutable evidence ID are required for
one atomic publication. Evidence from observations, epochs, generations, or
revisions cannot be combined. Permitted last-known-good retention remains the
native owner's lifecycle decision.

## Identity, loss, and operations

The gateway must configure stable, non-secret asset, EVSE, and connector IDs.
They must be distinct and cannot be derived from unit ID, firmware text,
observation values, payload bytes, or request order. Missing, blank, invalid,
reused, or ambiguous IDs fail closed. This gate establishes no connector
topology beyond that configured semantic connector identity.

Power, energy, phase, session, readiness, SOC, thermal, fault, interlock,
meter, and all unsupported native facts remain withheld or native-only. There
is no sender, route, authority, acknowledgement/readback authority, retry, or
live control. Every operation is unavailable, including
`evse.operation.set_allocated_current`; `outbound_allowed=false` is not an
operation admission.

## Later consumer cutover

A later gateway change may use one SemReg projection to feed versioned semantic
MCP, mTLS GraphQL and Portal with parity, then applicable Home Assistant
adoption. It must remove fallback, comparator, compatibility adapter, shadow
authority, dual publication, caller-supplied provenance, and write routes.
Until that implementation is accepted, this mapping exposes no consumer binding.

Run `python3 scripts/validate_tesla_gen3_wc3_24443_evse_current_limit_mapping.py`,
`python3 scripts/test_validate_tesla_gen3_wc3_24443_evse_current_limit_mapping.py`,
and `./scripts/check_docs.sh`.
