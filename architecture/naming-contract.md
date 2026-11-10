# SemReg value-member naming contract

This bounded contract records the implementation-name change required before the
library and consumers can adopt it. The [complete correspondence](naming-contract.json)
contains every inventory row for the five pack definition files, including unchanged
provisional identities and their open questions. Dot-separated DefinitionID
namespaces are identity structure; the terminal value member follows the
[register and field vocabulary](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/naming.md).
Historical names in the correspondence are documentary only, never runtime fallback keys.

| Historical DefinitionID | Canonical DefinitionID | Proof |
|---|---|---|
| `thermal.measurement.humidity_relative` | `thermal.measurement.humidity` | Humidity denotes relative humidity; quantity, percent, ratio and bounds remain. |
| `thermal.setpoint.temperature` | `thermal.setpoint.temperature_setpoint` | Setpoint denotes the regulated value; quantity, Celsius, temperature dimension and bounds remain. |
| `thermal.setpoint.dhw_temperature` | `thermal.setpoint.dhw_temperature_setpoint` | The same setpoint rule applies to the domestic hot water value; quantity, Celsius, temperature dimension and bounds remain. |

The field definitions and operation references are evidenced by the public
[thermal definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go).
The existing [humidity cutover](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/humidity-semreg-cutover.md) describes the relative-humidity quantity.
These names do not establish native meaning or qualification. Proven refers only
to this naming correspondence; native qualification remains independent.
Unresolved vocabulary and native identity remain provisional or unknown, with
questions recorded per row. Go types, pack identities and versions, kernel reason
strings, retention and admission ownership do not change. Structural JSON
envelope tags are outside the value grammar.

Consumers must coordinate the change across gateway projections, GraphQL, MCP,
Home Assistant, virtual device, Matter binding and explorer schema passthrough.
No alias, duplicate field, compatibility shim or migration step is provided.
Native identity, raw evidence, value class, units, scale, polarity, access and
qualification remain intact; admission stays fail closed and partial updates
retain permitted last-known-good fields. The retained-capacity ownership question
remains open and implementation is held until it is resolved. No release or
hardware evidence follows from this contract.

The correspondence data lists direct textual consumer references by old ID; it
is not proof that generic consumers need no work. The
[Home Assistant architecture](https://github.com/Project-Helianthus/helianthus-ha-integration/blob/main/ARCHITECTURE.md)
consumes the semantic GraphQL layer, the
[virtual-device documentation](https://github.com/Project-Helianthus/helianthus-ebus-vdev/blob/main/README.md)
describes a GraphQL client, and the
[explorer schema](https://github.com/Project-Helianthus/helianthus-vrc-explorer/blob/main/src/helianthus_vrc_explorer/artifact_schema.py)
describes its artifact boundary. Their indirect use must be checked during the
consumer wave. GraphQL and MCP must preserve parity and eBUS MCP compatibility.
