# Growatt 1xSxxP RS-485 v2.02 storage mapping gate v1

This accepted, source-specific gate maps a bounded native read-only observation
to `helianthus.pack.storage@1.1.0`. It is neither a device support claim nor a
physical qualification. Its machine-readable companion is
[the mapping vectors](growatt-bms-rs485-v202-storage-v1.json).

The executable vectors use offline synthetic RTU observations with valid frame
shape and CRC. They are deterministic mapping evidence, not observations from
hardware and not a device-compatibility claim.

## Publishable evidence pins

The native source is [Growatt RS-485 v2.02 documentation at substantive revision
`6c08d4d`](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/6c08d4d2acf70bea622da333f6d75e26d2d92621/protocols/growatt/bms-rs485-1xsxxp-v202.md).
The [lifecycle gate](https://github.com/Project-Helianthus/helianthus-docs-modbus/commit/35151979c8561d5dc4215030899277aec36d2f9f),
[registry input](https://github.com/Project-Helianthus/helianthus-modbusreg/commit/7853d903970a4fdded35abaef01fe30f7e93be6a),
and [SemReg input](https://github.com/Project-Helianthus/helianthus-semreg/commit/f3f761bc67e10d6a65eba6c13cb4dc51002d6955)
are pinned. Storage docs/runtime inputs are `c20fdef000fe95df95fca60c55d651a0614c4efd`
and `6556bf4b3fffd645b6c14ebfd194d8570b7c5207`.

Gateway composition is accepted only at [main
`32244901c4c8337266cd348bdad90fb9e8eb0a61`](https://github.com/Project-Helianthus/helianthus-ebusgateway/commit/32244901c4c8337266cd348bdad90fb9e8eb0a61), tree
`0a850d5646d46f5782b1396d72a3d93bffa6974e`, from reviewed source
[`15ab7f0f4197485c83c04f8fe24000ebe058cb7a`](https://github.com/Project-Helianthus/helianthus-ebusgateway/commit/15ab7f0f4197485c83c04f8fe24000ebe058cb7a).
These pins are evidence, not a
runtime dependency on a sibling checkout.

## Native admission and preservation

Admission requires the combined revision tuple `1xSxxP ESS`, `Rev2.01`,
`V2.0`, and `2.02`; one caller-selected unicast unit from 1 through 247; and
the four FC03 slices at `0x0001/7`, `0x000D/29`, `0x0100/12`, and `0x010D/2`.
Broadcast unit zero is `NO_SEND`. The immutable native path retains the request
and response ADUs with valid Modbus CRC, per-slice request IDs and exact word
counts, offsets, function, unit, tuple, observation ID and revision, wall and
monotonic receipt axes, opaque clock/source epochs, driver and transport
generations, and qualification. The four slices share the same unit and
transport generation, and request IDs are distinct. Missing or contradictory
evidence rejects the observation before mapping; missing semantic fields are
withheld or unavailable, never zero.

A gateway-configured, non-secret semantic `asset_id` and distinct `source_id`
are required for projection. Neither may be derived from unit, vendor, version,
company, or generation. A stable native binding ID is derived with a
domain-separated function over only the asset ID, source ID, and exact profile;
it never selects or changes the asset identity. Missing or invalid identity
fails closed. The revision,
selected unit, version/gauge evidence, BMS and pack company/generation,
topology, and cell-series evidence remain coherent native provenance. This
mapping may qualify its offline projection while physical qualification remains
false; it grants no device support claim or operation.

## Mapping and loss

The JSON contract fixes every exact, transformed, native-only, and withheld
field. It preserves volts, amperes, percent, Celsius, seconds, counts, and
ampere-hours exactly as native units specify. Capacity is never converted to
kWh and energy is never derived from voltage, current, time, SOC, or a decoded
combination. `charging` and `discharging` become only the semantic `active`
state with a SemReg `symbol` loss; `soft_starting` withholds only the operating
state while the six independently valid facts remain available. Current and
counter continuity use transformed `provenance` and `policy` loss details;
an exact disposition has empty loss. Exact quantity vectors use SemReg's
canonical `{coefficient, exponent10}` decimal form derived from the admitted
fixed-scale words, rather than binary floating-point serialization.

Pack power, SOH, cell-temperature meaning, cell extrema, topology, repeated
pack identity, warning/error/company status, extension words, writable ranges,
and all control-adjacent data are unsupported or opaque. Counters retain the
reset/wrap loss and never infer a reset.

There is no charge/discharge limit, interlock, authority, write, acknowledgement,
readback, retry, or control route. `outbound_allowed=false` grants no operation.

## Later consumer cutover

A later implementation may bind semantic MCP, GraphQL, Portal, and Home
Assistant only through one atomic SemReg cutover. It must replace the selected
legacy semantic path and remove fallback, comparator, compatibility-only, and
dual-publication paths. Until then this gate publishes no consumer binding.

Run `python3 scripts/validate_growatt_bms_rs485_v202_storage_mapping.py`,
`python3 scripts/test_validate_growatt_bms_rs485_v202_storage_mapping.py`, and
`./scripts/check_docs.sh`.
