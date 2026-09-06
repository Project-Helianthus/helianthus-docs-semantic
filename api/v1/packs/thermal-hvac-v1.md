# Thermal and HVAC capability pack v1

`helianthus.pack.thermal/v1` has exact PackRef
`{id: "helianthus.pack.thermal", version: "1.0.0"}` and is the accepted
software-0.7 typed input over `helianthus.semantic.kernel/v1`. The complete
machine-significant catalog is [thermal-hvac-acceptance-vectors.json](thermal-hvac-acceptance-vectors.json).
Every listed item expands to an exact versioned `DefinitionRef` under this PackRef.

## Field catalog

Kernel ValueKind is used exclusively: quantities use canonical DefinitionID
units and kernel Decimal bounds; symbols carry declared semantic symbols.

| Field | Kind | Unit/dimension |
|---|---|---|
| `thermal.measurement.air_temperature` | quantity | `unit.celsius`, `thermal.dimension.temperature` |
| `thermal.measurement.water_temperature` | quantity | `unit.celsius`, `thermal.dimension.temperature` |
| `thermal.measurement.humidity_relative` | quantity | `unit.percent`, `thermal.dimension.ratio` |
| `thermal.measurement.flow_rate` | quantity | `unit.litre_per_minute`, `thermal.dimension.volumetric_flow` |
| `thermal.measurement.power` | quantity | `unit.watt`, `thermal.dimension.power` |
| `thermal.setpoint.temperature` | quantity | `unit.celsius`, `thermal.dimension.temperature` |
| `thermal.setpoint.dhw_temperature` | quantity | `unit.celsius`, `thermal.dimension.temperature` |
| `thermal.mode.system` | symbol | `thermal.dimension.system` |
| `thermal.mode.zone` | symbol | `thermal.dimension.zone` |
| `thermal.demand.level` | quantity | `unit.percent`, `thermal.dimension.ratio` |
| `thermal.status.operation` | symbol | `thermal.dimension.system` |
| `thermal.status.fault` | symbol | `thermal.dimension.system` |
| `thermal.action.state` | symbol | `thermal.dimension.system` |

Unknown, withheld, unsupported, and operation outcome stay in kernel quality,
availability, and operation records. They are never semantic symbols. Action is
heating, cooling, DHW, ventilating, or idle. Schedules and vendor extensions
remain native evidence and projection loss until separately typed.

## Services, capabilities, and relationships

The FactKey dimension contracts are `thermal.dimension.system`,
`thermal.dimension.zone`, `thermal.dimension.circuit`, `thermal.dimension.dhw`,
and `thermal.dimension.ventilation`; each is typed text. They preserve separate
instances without a guessed canonical face.

`thermal.service.system`, `thermal.service.zone`, `thermal.service.circuit`,
`thermal.service.dhw`, and `thermal.service.ventilation` each bind the matching
dimension. Read coverage is `thermal.capability.read.system`,
`thermal.capability.read.zone`, `thermal.capability.read.circuit`,
`thermal.capability.read.dhw`, and `thermal.capability.read.ventilation`.
Operations require qualified current binding: `thermal.capability.set_temperature`
and `thermal.capability.set_mode`.

## Operations, effects, and readback

`thermal.operation.set_temperature` takes `thermal.setpoint.temperature` with
`thermal.effect.set_temperature`; `thermal.operation.set_mode` takes
`thermal.mode.system` with `thermal.effect.set_mode`. A zone-mode operation is
not published because the catalog cannot imply a native route. Both require
current generation, qualified active capability, exact route, and authority
admission. Dispatch, ACK, readback, and result remain separate; applied needs
current-generation confirming readback and indeterminate handoff forbids retry.

## Lifecycle and qualification

Source epoch, driver generation, semantic revision, qualification, activation,
generation fencing, partial updates, stale/unknown evidence, and last-known-good
retention remain independent. Candidate mappings never qualify or activate.

## Projection loss

Native enum, precision/range, multiple zones/faces, schedules, vendor extensions,
unavailable fields, conflicts, and unsupported operations receive an explicit
kernel projection disposition and loss detail. Projection cannot create routes,
authority, intents, or capability instances.

## Portal contribution descriptors

Read descriptors are `thermal.portal.read.system`, `thermal.portal.read.zone`,
`thermal.portal.read.circuit`, `thermal.portal.read.dhw`, and
`thermal.portal.read.ventilation`. Operation descriptors are
`thermal.portal.operation.set_temperature` and `thermal.portal.operation.set_mode`.
Portal consumes promoted definitions and admission; it cannot define truth,
authority, lifecycle, or native routes.

## Native mapping boundary

Inputs are semantic `da5ab4415d3bec73f9572aec1c495a6cdcbcba47`, eBUS
`ef076cb03e6cd5612f5dcbe7839e00ab4ee666c9`, GREE/CAN
`665a5f22f78c349b5e3063bda158af250a3f44b6`, eeBUS ledger
`81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1`, raw donor
`cedf238e34f879815ba773e9cd76b2b31c2822a3`, and Matter draft
`29b4768a513cf566011ab8cd60df1bc495204953`. `thermal.mapping.ebus.companion`
and `thermal.mapping.gree.vrf` are native-owner candidate rows;
`thermal.mapping.eebus` is unknown pending STD-01. No mapping is normative.

## Compatibility and follow-ons

PV/inverter, storage/BMS, EVSE, and infrastructure remain explicit follow-on
packs. This is 0.7 typed design only; it introduces no 0.8 IR, HWIR, codegen,
runtime, native driver, gateway, consumer, deployment, or hardware action.

## Validation and correction criteria

Run `python3 scripts/validate_thermal_hvac_pack_v1.py`,
`python3 scripts/test_validate_thermal_hvac_pack_v1.py`, and
`./scripts/check_docs.sh`. Correct invalid ValueKind/unit/dimension/Decimal,
missing owner/version, arbitrary public extension, outcome symbol, missing
dimension contract, dangling reference, or mapping-promotion defect.

## Concrete acceptance policy

The typed read descriptors consume every declared field exactly: the system
descriptor includes `thermal.measurement.power` and `thermal.action.state` as
well as system mode/status; zone, circuit, DHW, and ventilation consume their
listed facts. The validator rejects an orphaned or undeclared read field.

Publication requires exact source epoch, current driver generation, exact
semantic revision, and qualified activation; stale generation is rejected.
Partial publication changes only supplied valid fields while preserving permitted
last-known-good. Withdrawal is explicit and generation-fenced. Stale/unknown
evidence cannot promote or authorize; retained tombstone evidence is
non-actionable.

`thermal.capability.set_temperature` constrains exactly
`thermal.setpoint.temperature`; `thermal.capability.set_mode` constrains exactly
`thermal.mode.system`. Stages are admission, dispatch, acknowledgement,
readback, and terminal outcome. Outcomes are `rejected`,
`dispatched_unacknowledged`, `acknowledged_unverified`, `applied`, `no_effect`,
`conflict`, and `indeterminate`. `applied` needs post-dispatch current-generation
confirming readback; blind retry is forbidden after possible dispatch or
indeterminate handoff.
