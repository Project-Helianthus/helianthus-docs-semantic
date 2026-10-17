# Gateway-local runtime and Infrastructure pack boundary

Status: proposed application-mapping assessment for issue #36; no executable
mapping or stable API is established. This is a partial INT-04 / INT-05 / INT-08
slice. The evidence basis is the accepted
[Infrastructure pack v1](../../api/v1/packs/infrastructure-v1.md), its
[typed catalog](../../api/v1/packs/infrastructure-acceptance-vectors.json), and the
[ownership contract](../../architecture/repository-ownership-v1.md).

The exact target PackRef is `{id: "helianthus.pack.infrastructure", version:
"1.0.0"}`. All DefinitionRefs listed below use that PackRef and definition
version `1.0.0`; the catalog remains authoritative for types, units, dimensions,
symbols, bounds, and associations. No semantic IDs are introduced here.

## Mapping decision and evidence

The pack describes electrical infrastructure, explicitly excluding host,
network, and deployment infrastructure. Gateway-local runtime observations alone
have no supported mapping to this pack. The following are semantic exclusions,
not assertions that particular gateway fields or diagnostics are implemented.
No public gateway-local source contract was supplied with this assessment, so
exact source paths, field names, enum domains, acquisition behavior, and available
local diagnostic facts remain Unknown. A positive source-to-target mapping is
blocked pending that contract; no protocol-native fact is inferred.

| Local source concept to assess | Existing target considered | Disposition and reason |
|---|---|---|
| Driver observed connection state | `infrastructure.status.connection` | Unsupported: a driver connection does not prove electrical grid connection. Source implementation Unknown. |
| Runtime ready or healthy state | `infrastructure.status.readiness` | Unsupported: runtime readiness does not prove electrical grid readiness. Source implementation Unknown. |
| Acquisition success, failure, or missing observation | `infrastructure.status.fault` | Unsupported: acquisition failure does not prove an electrical site fault; success does not prove clear. Source implementation Unknown. |
| Local error, retry, latency, or resource diagnostics | No target definition | Unsupported: local diagnostic quantities are outside this electrical pack. Their availability, units, and time domains are Unknown. |
| Driver instance or source attachment | Electrical dimensions and relationships below | Unsupported: runtime composition does not prove electrical topology or asset identity. Source implementation Unknown. |

Proven: the cited pack defines electrical semantics and excludes host/network/
deployment semantics. Hypothesis: a future supplied gateway source may expose
separately qualified electrical observations; this is not evidence that it does.
Unknown: the concrete runtime source contract and any implemented electrical
binding. These evidence grades are explanatory labels, separate from native
qualification and kernel quality; they do not set qualification to qualified or
promotion to promoted.

## Individual catalog dispositions

Each row is unsupported **for gateway-local runtime facts alone**. The electrical
value or binding is Unknown, not an assertion that an electrical device lacks the
capability. Missing values remain absent with explicit kernel quality/availability
where applicable; do not encode Unknown or unsupported as a pack symbol, numeric
zero, or a healthy state. No implemented Infrastructure field is verified here.

| Existing definition | Disposition | Reason |
|---|---|---|
| `infrastructure.ac.voltage` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.ac.current` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.ac.active_power` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.ac.reactive_power` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.ac.apparent_power` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.ac.frequency` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.ac.power_factor` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.power.import_active` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.power.export_active` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.power.import_reactive` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.power.export_reactive` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.power.apparent` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.energy.import` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.energy.export` | Unknown / unsupported | No qualified electrical measurement with the required unit, dimension, direction, and lineage. |
| `infrastructure.status.connection` | Unknown / unsupported | No qualified electrical state observation; runtime state is not electrical state. |
| `infrastructure.status.readiness` | Unknown / unsupported | No qualified electrical state observation; runtime state is not electrical state. |
| `infrastructure.status.breaker` | Unknown / unsupported | No qualified electrical state observation; runtime state is not electrical state. |
| `infrastructure.status.fault` | Unknown / unsupported | No qualified electrical state observation; runtime state is not electrical state. |
| `infrastructure.status.interlock` | Unknown / unsupported | No qualified electrical state observation; runtime state is not electrical state. |
| `infrastructure.dimension.site` | Unknown / unsupported | No evidenced electrical asset identity or dimension binding. |
| `infrastructure.dimension.grid_connection` | Unknown / unsupported | No evidenced electrical asset identity or dimension binding. |
| `infrastructure.dimension.feeder` | Unknown / unsupported | No evidenced electrical asset identity or dimension binding. |
| `infrastructure.dimension.circuit` | Unknown / unsupported | No evidenced electrical asset identity or dimension binding. |
| `infrastructure.dimension.phase` | Unknown / unsupported | No evidenced electrical asset identity or dimension binding. |
| `infrastructure.dimension.meter` | Unknown / unsupported | No evidenced electrical asset identity or dimension binding. |
| `infrastructure.service.site` | Unknown / unsupported | No qualified electrical asset/service binding. |
| `infrastructure.service.grid_connection` | Unknown / unsupported | No qualified electrical asset/service binding. |
| `infrastructure.service.feeder` | Unknown / unsupported | No qualified electrical asset/service binding. |
| `infrastructure.service.circuit` | Unknown / unsupported | No qualified electrical asset/service binding. |
| `infrastructure.service.phase` | Unknown / unsupported | No qualified electrical asset/service binding. |
| `infrastructure.service.meter` | Unknown / unsupported | No qualified electrical asset/service binding. |
| `infrastructure.relationship.site_grid_connection` | Unknown / unsupported | No evidenced electrical membership; runtime attachment is not topology. |
| `infrastructure.relationship.grid_connection_feeder` | Unknown / unsupported | No evidenced electrical membership; runtime attachment is not topology. |
| `infrastructure.relationship.feeder_circuit` | Unknown / unsupported | No evidenced electrical membership; runtime attachment is not topology. |
| `infrastructure.relationship.circuit_phase` | Unknown / unsupported | No evidenced electrical membership; runtime attachment is not topology. |
| `infrastructure.relationship.grid_connection_meter` | Unknown / unsupported | No evidenced electrical membership; runtime attachment is not topology. |
| `infrastructure.capability.read.site` | Unknown / unsupported | No current qualified active electrical read capability is established. |
| `infrastructure.capability.read.grid_connection` | Unknown / unsupported | No current qualified active electrical read capability is established. |
| `infrastructure.capability.read.feeder` | Unknown / unsupported | No current qualified active electrical read capability is established. |
| `infrastructure.capability.read.circuit` | Unknown / unsupported | No current qualified active electrical read capability is established. |
| `infrastructure.capability.read.phase` | Unknown / unsupported | No current qualified active electrical read capability is established. |
| `infrastructure.capability.read.meter` | Unknown / unsupported | No current qualified active electrical read capability is established. |
| `infrastructure.portal.read.site` | Unknown / unsupported | No promoted electrical facts and qualified binding support this read descriptor. |
| `infrastructure.portal.read.grid_connection` | Unknown / unsupported | No promoted electrical facts and qualified binding support this read descriptor. |
| `infrastructure.portal.read.feeder` | Unknown / unsupported | No promoted electrical facts and qualified binding support this read descriptor. |
| `infrastructure.portal.read.circuit` | Unknown / unsupported | No promoted electrical facts and qualified binding support this read descriptor. |
| `infrastructure.portal.read.phase` | Unknown / unsupported | No promoted electrical facts and qualified binding support this read descriptor. |
| `infrastructure.portal.read.meter` | Unknown / unsupported | No promoted electrical facts and qualified binding support this read descriptor. |

## State separation, retention, and admission

Apply the [kernel contract](../../api/v1/kernel.md) independently of electrical
field values. Runtime state describes the driver; acquisition state describes
whether an observation was obtained. Native qualification describes whether the
specific source/profile/mapping is qualified. Evidence grade describes the basis
for a claim. Kernel validity, freshness, availability, promotion, and capability
activation remain distinct. Neither a running driver nor a successful read
qualifies or promotes an electrical fact.

Keep original native evidence, exact values and units, source lineage, source
epoch, driver generation, semantic revision, alternatives, conflicts, and time
domains. Do not substitute a runtime observation time for an electrical sample
time, or derive electrical aggregation from diagnostics. An unavailable local
source does not erase unrelated valid fields: partial publication changes only
supplied valid fields and preserves permitted last-known-good state. Retained
stale or fenced evidence stays non-actionable; it is not a current fact and
cannot reactivate a withdrawn capability. Withdrawal is explicit and generation
fenced. Current publication requires the pack's current source/generation/
revision and qualified active capability; Unknown never supplies admission.

This assessment adds no operation, control route, authorization gate, MCP
namespace, or GraphQL field. Existing eBUS MCP compatibility and GraphQL parity
remain requirements; neither consumer may manufacture an electrical mapping
from diagnostics. Runtime projection compatibility is unverified here.

## Unresolved evidence and falsifiers

To complete a positive application mapping, supply a public gateway-local source
contract with repository-relative source paths, versioned field/enum definitions,
units, time domains, lifecycle behavior, and synthetic/public fixtures. Establish
which fields actually exist before claiming a mapping. Any protocol-native
meaning first requires its [public native documentation owner](../../evidence/native-documentation-owners.md)
contract, then an exact qualified binding and explicit projection loss.

A source contract demonstrating a qualified electrical observation could falsify
an individual Unknown disposition; a UI label, driver health flag, catalog entry,
or similar name cannot. A pack revision explicitly accepting runtime semantics
would require a separate reviewed contract change, not reinterpretation here.
Local diagnostic-to-pack coverage remains blocked until the source is supplied;
no host metric is silently added to the electrical pack. Full CI, independent
review, output compatibility, transport, and hardware acceptance are not claimed.
