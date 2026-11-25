# Thermal and HVAC capability pack v1

`helianthus.pack.thermal/v1` has exact PackRef
`{id: "helianthus.pack.thermal", version: "1.0.0"}` and is the accepted
software-0.7 typed input over `helianthus.semantic.kernel/v1`. The complete
machine-significant catalog is [thermal-hvac-acceptance-vectors.json](thermal-hvac-acceptance-vectors.json).
Every listed item expands to an exact versioned `DefinitionRef` under this PackRef.

## Field catalog

Kernel ValueKind is used exclusively: quantities use canonical DefinitionID
units and kernel Decimal bounds; symbols carry declared semantic symbols.

Every field declares exactly one fact dimension. A resource dimension names
the resource the fact is about, its subject (section 6.2 of the
[graph contract](../graph.md)). `thermal.dimension.function` is class-level:
it names anchor class function and no resource kind. The qualifier dimensions
`thermal.dimension.preset`, `thermal.dimension.time_program`,
`thermal.dimension.program_entry` and `thermal.dimension.suggestion` qualify
a fact and are not its subject.

| Field | Kind | Subject | Unit | Bounds | Direction |
|---|---|---|---|---|---|
| `thermal.measurement.air_temperature` | quantity | zone | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.measurement.humidity` | quantity | zone | `unit.ratio` | 0 to 1 | not applicable |
| `thermal.setpoint.temperature_setpoint` | quantity | zone | `unit.kelvin` | 223.15 to 423.15 | not applicable |
| `thermal.setpoint.occupied_cooling` | quantity | zone | `unit.kelvin` | 223.15 to 423.15 | not applicable |
| `thermal.setpoint.occupied_heating` | quantity | zone | `unit.kelvin` | 223.15 to 423.15 | not applicable |
| `thermal.setpoint.unoccupied_cooling` | quantity | zone | `unit.kelvin` | 223.15 to 423.15 | not applicable |
| `thermal.setpoint.unoccupied_heating` | quantity | zone | `unit.kelvin` | 223.15 to 423.15 | not applicable |
| `thermal.mode.zone` | symbol | zone | | | |
| `thermal.measurement.circuit_flow_temperature` | quantity | thermal circuit | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.measurement.flow_rate` | quantity | thermal circuit | `unit.cubic_metre_per_second` | 0 to 0.2 | non-negative |
| `thermal.measurement.dhw_temperature` | quantity | domestic hot water | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.setpoint.dhw_temperature_setpoint` | quantity | domestic hot water | `unit.kelvin` | 223.15 to 423.15 | not applicable |
| `thermal.demand.level` | quantity | ventilation system | `unit.ratio` | 0 to 1 | not applicable |
| `thermal.measurement.outdoor_air_temperature` | quantity | thermal system | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.measurement.system_flow_temperature` | quantity | thermal system | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.mode.system` | symbol | thermal system | | | |
| `thermal.action.state` | symbol | thermal system | | | |
| `thermal.status.operation` | symbol | thermal system | | | |
| `thermal.status.fault` | symbol | thermal system | | | |
| `thermal.status.maintenance` | symbol | thermal system | | | |
| `thermal.overrun.one_time_dhw` | symbol | thermal system | | | |
| `thermal.overrun.party` | symbol | thermal system | | | |
| `thermal.overrun.sg_ready_condition_1` | symbol | thermal system | | | |
| `thermal.overrun.sg_ready_condition_3` | symbol | thermal system | | | |
| `thermal.overrun.sg_ready_condition_4` | symbol | thermal system | | | |
| `thermal.overrun.one_day_away` | symbol | thermal system | | | |
| `thermal.overrun.one_day_at_home` | symbol | thermal system | | | |
| `thermal.overrun.one_time_ventilation` | symbol | thermal system | | | |
| `thermal.overrun.hvac_system_off` | symbol | thermal system | | | |
| `thermal.overrun.valve_kick` | symbol | thermal system | | | |
| `thermal.measurement.heat_generator_flow_temperature` | quantity | heat generator | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.measurement.heat_generator_return_temperature` | quantity | heat generator | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.measurement.thermal_power` | quantity | heat generator | `unit.watt` | -1 000 000 to 1 000 000 | signed |
| `thermal.energy.heat_output` | quantity | heat generator | `unit.joule` | 0 to 3.6 x 10^18 | non-negative |
| `thermal.measurement.water_pressure` | quantity | heat generator | `unit.pascal` | -101 325 to 10 000 000 | not applicable |
| `thermal.status.heat_generator_fault` | symbol | heat generator | | | |
| `thermal.status.heat_generator_operation` | symbol | heat generator | | | |
| `thermal.measurement.store_temperature` | quantity | thermal store | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.mode.terminal_unit` | symbol | terminal unit | | | |
| `thermal.status.terminal_unit_fault` | symbol | terminal unit | | | |
| `thermal.status.terminal_unit_operation` | symbol | terminal unit | | | |
| `thermal.measurement.refrigerant_high_side_pressure` | quantity | refrigerant circuit | `unit.pascal` | 0 to 100 000 000 | not applicable |
| `thermal.measurement.refrigerant_low_side_pressure` | quantity | refrigerant circuit | `unit.pascal` | 0 to 100 000 000 | not applicable |
| `thermal.measurement.refrigerant_condensing_temperature` | quantity | refrigerant circuit | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.measurement.refrigerant_evaporating_temperature` | quantity | refrigerant circuit | `unit.kelvin` | 173.15 to 473.15 | not applicable |
| `thermal.measurement.compressor_speed` | quantity | compressor | `unit.reciprocal_second` | 0 to 1 000 | non-negative |
| `thermal.measurement.pump_speed` | quantity | pump | `unit.reciprocal_second` | 0 to 1 000 | non-negative |
| `thermal.measurement.valve_position` | quantity | terminal unit | `unit.ratio` | 0 to 1 | non-negative |

The subject column names the resource kind of the field's dimension:
thermal system `thermal.dimension.system`, zone `thermal.dimension.zone`,
thermal circuit `thermal.dimension.circuit`, domestic hot water
`thermal.dimension.dhw`, ventilation system `thermal.dimension.ventilation`,
heat generator `thermal.dimension.heat_generator`, thermal store
`thermal.dimension.thermal_store`, terminal unit
`thermal.dimension.terminal_unit`, refrigerant circuit
`thermal.dimension.refrigerant_circuit`, compressor
`thermal.dimension.compressor` and pump `thermal.dimension.pump`.

The temperatures of a circuit and of the domestic hot water are two facts,
each on its own subject. Thermal power is the thermal output of the heat
generator; its sign reference is the nominal direction of
`thermal.relation.fluid_supply`, so a positive value is heat the generator
delivers to the fluid it supplies. The demand level is a ratio of the
subject's rated maximum. Water pressure is a gauge pressure; the refrigerant
pressures are absolute pressures. Compressor speed is a rotational speed.
The pump speed is not compressor speed. The valve position is not an overrun.

Symbols: system mode is auto, cool, dry, emergency_heat, fan_only, heat, off,
precooling or sleep; zone mode is auto, comfort,
eco or off; terminal-unit mode is auto, cool, dry, fan_only, heat or off;
action is heating, cooling, DHW, ventilating or idle; each operation status is
active or idle; each fault status is clear or present; maintenance is clear or
due. Each of `thermal.overrun.one_time_dhw`, `thermal.overrun.party`,
`thermal.overrun.sg_ready_condition_1`, `thermal.overrun.sg_ready_condition_3`,
`thermal.overrun.sg_ready_condition_4`, `thermal.overrun.one_day_away`,
`thermal.overrun.one_day_at_home`, `thermal.overrun.one_time_ventilation`,
`thermal.overrun.hvac_system_off` and `thermal.overrun.valve_kick` is
independently inactive, active, running or finished. Several of those statuses
can be active together. A one-time domestic-hot-water overrun is a status of
its own; the domestic-hot-water setpoint stays a separate fact. The occupied
heating setpoint `thermal.setpoint.occupied_heating`, the occupied cooling
setpoint `thermal.setpoint.occupied_cooling`, the unoccupied heating setpoint
`thermal.setpoint.unoccupied_heating` and the unoccupied cooling setpoint
`thermal.setpoint.unoccupied_cooling` are four zone quantities
distinct from the single zone setpoint `thermal.setpoint.temperature_setpoint`. The
set-temperature operation still takes only that single zone setpoint. Unknown,
withheld, unsupported, and operation outcome stay in kernel quality,
availability, and operation records. They are never semantic symbols.
Schedules and vendor extensions remain native evidence and projection loss
until separately typed.

The air, circuit, hot-water, outdoor, flow, setpoint, humidity, demand,
operation, fault, action and mode fields carry the 0.7 values. The
return-temperature, water-pressure, store, terminal-unit, maintenance,
heat-generator status, refrigerant, compressor-speed and heat-output fields
are defined in the same edit and are published only with native evidence.
The electrical power and energy that a thermal appliance draws are not
thermal facts: a mapping gate publishes them on the appliance's electrical
circuit and meter with the [infrastructure pack](infrastructure-v1.md).

## Units

Canonical units follow the [unit rule](../../README.md#unit-rule): canonical
units in the semantic registry are SI, and a customary unit appears only at
display, in a consumer. The pack's reading of the rule is the working reading
stated there, not yet confirmed by the project owner. The pack uses seven
units: `unit.kelvin`, `unit.ratio` (0 to 1), `unit.cubic_metre_per_second`,
`unit.pascal`, `unit.reciprocal_second`, `unit.watt` and `unit.joule`.

The bounds of the fields that existed before this edit are their earlier
bounds converted: kelvin is degree Celsius plus 273.15, a ratio is percent
divided by 100, and the flow bound is restated as 0.2 cubic metre per second.
A mapping gate converts each native value with an exact factor and offset
(kilowatt-hour times 3 600 000 to joule, bar times 100 000 to pascal). Where a
factor does not terminate in decimal (litre per minute divided by 60 000, or
revolutions per minute divided by 60), the gate rounds half to even to a
declared number of decimal places, chosen so that converting back and
rounding to the native step returns the native value. The native value and
unit stay in the evidence.

## Services, capabilities, and relations

The FactKey dimension contracts are `thermal.dimension.system`,
`thermal.dimension.zone`, `thermal.dimension.circuit`, `thermal.dimension.dhw`,
`thermal.dimension.ventilation`, `thermal.dimension.heat_generator`,
`thermal.dimension.thermal_store`, `thermal.dimension.terminal_unit`,
`thermal.dimension.refrigerant_circuit`, `thermal.dimension.compressor`,
`thermal.dimension.pump`, `thermal.dimension.room`,
`thermal.dimension.sensor`, `thermal.dimension.valve`,
`thermal.dimension.solar_circuit`, `thermal.dimension.solar_collector`,
`thermal.dimension.detector`, and `thermal.dimension.water_tank`; each of these is typed text and names one
resource. `thermal.dimension.function` is typed text, names anchor class
function, and names no resource. They preserve separate instances
without a guessed canonical face.

| Resource kind | Anchor class | Dimension | Service | Read capability |
|---|---|---|---|---|
| thermal system | function | `thermal.dimension.system` | `thermal.service.system` | `thermal.capability.read.system` |
| zone | function | `thermal.dimension.zone` | `thermal.service.zone` | `thermal.capability.read.zone` |
| room | function | `thermal.dimension.room` | `thermal.service.room` | `thermal.capability.read.room` |
| sensor | equipment | `thermal.dimension.sensor` | `thermal.service.sensor` | `thermal.capability.read.sensor` |
| thermal circuit | function | `thermal.dimension.circuit` | `thermal.service.circuit` | `thermal.capability.read.circuit` |
| domestic hot water | function | `thermal.dimension.dhw` | `thermal.service.dhw` | `thermal.capability.read.dhw` |
| ventilation system | function | `thermal.dimension.ventilation` | `thermal.service.ventilation` | `thermal.capability.read.ventilation` |
| heat generator | equipment | `thermal.dimension.heat_generator` | `thermal.service.heat_generator` | `thermal.capability.read.heat_generator` |
| thermal store | equipment | `thermal.dimension.thermal_store` | `thermal.service.thermal_store` | `thermal.capability.read.thermal_store` |
| terminal unit | equipment | `thermal.dimension.terminal_unit` | `thermal.service.terminal_unit` | `thermal.capability.read.terminal_unit` |
| refrigerant circuit | function | `thermal.dimension.refrigerant_circuit` | `thermal.service.refrigerant_circuit` | `thermal.capability.read.refrigerant_circuit` |
| compressor | component | `thermal.dimension.compressor` | `thermal.service.compressor` | `thermal.capability.read.compressor` |
| pump | component | `thermal.dimension.pump` | `thermal.service.pump` | none |
| valve | component | `thermal.dimension.valve` | `thermal.service.valve` | none |
| solar thermal circuit | function | `thermal.dimension.solar_circuit` | `thermal.service.solar_circuit` | none |
| solar collector | equipment | `thermal.dimension.solar_collector` | `thermal.service.solar_collector` | none |
| detector | equipment | `thermal.dimension.detector` | `thermal.service.detector` | none |
| water tank | component | `thermal.dimension.water_tank` | `thermal.service.water_tank` | none |

The pump service has a read descriptor and no read capability. `resource.pump`, `thermal.dimension.pump` and `thermal.service.pump` keep physical, hydraulic and diagnostic and also carry energy and control. `thermal.measurement.pump_speed` stays hydraulic and diagnostic. The valve, solar-circuit, solar-collector, detector and water-tank services have a read descriptor and no read capability. `thermal.service.function` binds `thermal.dimension.function` and `thermal.capability.read.function` reads it. Each service
binds the matching dimension. Operations require qualified
current binding: `thermal.capability.set_temperature` on the zone service and
`thermal.capability.set_mode` on the system service. Indoor and outdoor units
are not kinds.

The pack declares fifteen relation definitions. Each names the dimensions of its
`from` and `to` ends as lists and its cardinality; the
[element catalog](../element-catalog-v1.json) states the core type,
orientation, endpoint kinds, medium, admitted basis classes and planes:

| Definition | Core type | From | To | Cardinality | Basis classes | Planes |
|---|---|---|---|---|---|---|
| `thermal.relation.system_member` | `groups` | thermal system | zone, thermal circuit, domestic hot water, ventilation system, heat generator, thermal store, terminal unit, refrigerant circuit | one to many | configuration, gate rule | physical, control |
| `thermal.relation.fluid_supply` | `supplies`, heat-transfer fluid | heat generator, thermal store, thermal circuit | thermal circuit, thermal store, zone, domestic hot water, terminal unit | many to many | configuration, gate rule | energy, hydraulic |
| `thermal.relation.air_supply` | `supplies`, air | terminal unit, ventilation system | zone | many to many | configuration | energy |
| `thermal.relation.refrigerant_circuit_member` | `groups` | refrigerant circuit | heat generator, terminal unit | one to many | configuration, gate rule | physical, hydraulic |
| `thermal.relation.generator_compressor` | `contains` | heat generator | compressor | one to many | gate rule | physical, hydraulic, diagnostic |
| `thermal.relation.circuit_room` | `contains` | thermal circuit | room | one to many | configuration | physical |
| `thermal.relation.circuit_zone` | `contains` | thermal circuit | zone | one to many | configuration | physical |
| `thermal.relation.zone_room` | `contains` | zone | room | one to many | configuration | physical |
| `thermal.relation.pump_member` | `contains` | thermal circuit, domestic hot water, heat generator, solar thermal circuit | pump | one to many | configuration, gate rule | physical, hydraulic |
| `thermal.relation.valve_member` | `contains` | thermal circuit, zone, domestic hot water, heat generator, terminal unit | valve | one to many | configuration, gate rule | physical, hydraulic |
| `thermal.relation.solar_circuit_collector` | `contains` | solar thermal circuit | solar collector | one to many | configuration, gate rule | physical, hydraulic |
| `thermal.relation.detector_member` | `contains` | thermal system, pump, zone | detector | one to many | configuration, gate rule | physical |
| `thermal.relation.water_tank_member` | `contains` | ventilation system, terminal unit, heat generator | water tank | one to many | configuration, gate rule | physical |
| `thermal.relation.fan_member` | `contains` | terminal unit, ventilation system, heat generator | fan | one to many | configuration, gate rule | physical |
| `thermal.relation.filter_member` | `contains` | ventilation system, terminal unit | air filter | one to many | configuration, gate rule | physical |

The core-owned definition `relation.thermal_control` (`controls`) runs from
generic equipment to the thermal system, zone, thermal circuit, domestic hot
water, ventilation system, heat generator and terminal unit, many to many,
with basis classes configuration and gate rule, in the control plane. It is
listed in the element catalog because one of its ends is not reached through
a dimension of this pack.

A relation instance is published only with the basis class its native owner
documents; without it the relation is unknown and no absence statement is
made. `thermal.relation.fluid_supply` admits configuration and gate rule. The
reviewed row names no public path for the controller assignment.
`thermal.relation.fluid_supply` is a separate
supplies relation and is not a physical parent. Refrigerant pressures are
published only when the native owner proves the pressure reference; compressor
speed only when
it proves the mechanical meaning and the unit.

Through the fluid facts, the fluid kinds and `thermal.relation.fluid_supply`
the hydraulic plane is no longer empty.

## Admission records

The five kinds added by this edit enter by the first branch of the admission
rule (graph contract section 10.5): the heat generator on the adopted Matter
baseline (eeBUS represents it as well), the terminal unit on the Matter
baseline, and the thermal store, the refrigerant circuit and the compressor on
eeBUS. Their dimensions, services, read capabilities and read descriptors take
the record of their kind. Each record cites the
[research report on thermal resources and relations](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/68#issuecomment-6878639940),
which names the public data-model element for each kind, under the
[decision on kinds, relations and plane membership](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/68#issuecomment-6878639475).

The second branch (common to two or more vendors, with a deep-research report
in the admitting issue) admits:

- `thermal.relation.fluid_supply`, `thermal.relation.air_supply` and
  `thermal.relation.refrigerant_circuit_member`: the
  [research note on fluid and air supply and refrigerant-circuit membership](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/68#issuecomment-6878640316);
- the two refrigerant pressures and the two refrigerant saturation
  temperatures: the
  [research note on refrigerant pressures and saturation temperatures](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/65#issuecomment-6878641751);
- `thermal.measurement.compressor_speed`: the
  [research note on compressor speed](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/65#issuecomment-6878642109);
- `thermal.measurement.thermal_power` and `thermal.energy.heat_output`: the
  [research note on thermal power and heat energy](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/65#issuecomment-6878642474).

The placement and the unit rule are recorded in the
[decision record](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/67#issuecomment-6878639152)
and the [decision on thermal fields and units](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/65#issuecomment-6878640674),
with the [research report on thermal quantities and units](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/65#issuecomment-6878641100)
and the [research note on the canonical temperature unit](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/65#issuecomment-6878641365).
Identifiers recorded before the room kind stay provisional under the
[naming contract](../../../architecture/naming-contract.md).
Room identifiers are admitted there with the historical name equal to the
canonical name and with no confirmation question.

## Operations, effects, and readback

`thermal.operation.set_temperature` takes `thermal.setpoint.temperature_setpoint` with
`thermal.effect.set_temperature`; `thermal.operation.set_mode` takes
`thermal.mode.system` with `thermal.effect.set_mode`. Both are admitted under
graph enforcement: the setpoint is a fact of the zone, and the operation and
its effect rule are in the control plane. `thermal.operation.set_zone_mode` takes `thermal.mode.zone` and
`thermal.operation.set_zone_cooling_mode` takes `thermal.mode.zone_cooling`.
Both are published on `thermal.service.zone` and their Matter rows stay
unknown with `matter.unmapped.v1`. The temperature and mode operations require
current generation, qualified active capability, exact route, and authority
admission. Dispatch, ACK, readback, and result remain separate; applied needs
current-generation confirming readback and indeterminate handoff forbids retry.

`resource.room` is the SPINE 1.3.0 section 4.2.33 entity type HVACRoom.
HeatingZone remains `resource.zone`. A room is not folded into a zone.
`thermal.dimension.room`, `thermal.service.room` and
`thermal.capability.read.room` are members of the physical, energy and control
planes. The read descriptor is `thermal.portal.read.room`.

Room quantities are `unit.kelvin` and carry no bounds:
`thermal.room.limit_absolute_minimum_heating_setpoint`,
`thermal.room.limit_absolute_maximum_heating_setpoint`,
`thermal.room.limit_absolute_minimum_cooling_setpoint`,
`thermal.room.limit_absolute_maximum_cooling_setpoint`,
`thermal.room.limit_minimum_heating_setpoint`,
`thermal.room.limit_maximum_heating_setpoint`,
`thermal.room.limit_minimum_cooling_setpoint`,
`thermal.room.limit_maximum_cooling_setpoint`,
`thermal.room.limit_setpoint_step`,
`thermal.room.measurement_air_temperature`,
`thermal.room.setpoint_occupied_cooling`,
`thermal.room.setpoint_occupied_heating`, and
`thermal.room.setpoint_temperature_setpoint`.
`thermal.room.measurement_air_temperature` is an aggregation member on the
energy and control planes (MRT 1.0.0 scenario 1). The other room quantities
are control facts. Heating limits and the occupied heating setpoint cite
CRHT 1.0.0 scenario 1. Cooling limits and the occupied cooling setpoint cite
CRCT 1.0.0 scenario 1. The temperature setpoint cites CRHT 1.0.0 scenario 1.
The reviewed table calls `thermal.room.limit_setpoint_step` signed. No
supplies relation is named for that fact, so the catalog records direction
`not_applicable` and infers no sign.

`thermal.room.mode_zone` symbols are `auto`, `eco`, `off` and `on`
(MRHSF 1.0.0 scenario 1). `thermal.room.mode_zone_cooling` uses the same four
symbols (MRCSF 1.0.0 scenario 1). Comfort stays a symbol of `thermal.mode.zone`
and is not a room mode.

`thermal.relation.circuit_zone` and `thermal.relation.zone_room` are the
circuit-to-zone-to-room containment of CRHSF/MRHSF 1.0.0 section 3.2.2.1
Figure 5 option 2. `thermal.relation.circuit_room` is Figure 5 option 1.
Each containment row is `contains`, one to many, basis class configuration,
and the physical plane only.

Room writes are control operations on `thermal.service.room`. Each argument
is a fact of `thermal.dimension.room`:

- `thermal.room.operation_set_zone_mode` takes `thermal.room.mode_zone`
  through `thermal.room.capability_set_zone_mode` and
  `thermal.room.effect_set_zone_mode` (CRHSF 1.0.0 scenario 1).
- `thermal.room.operation_set_zone_cooling_mode` takes
  `thermal.room.mode_zone_cooling` through
  `thermal.room.capability_set_zone_cooling_mode` and
  `thermal.room.effect_set_zone_cooling_mode` (CRCSF 1.0.0 scenario 1).
- `thermal.room.operation_set_occupied_heating` takes
  `thermal.room.setpoint_occupied_heating` through
  `thermal.room.capability_set_occupied_heating` and
  `thermal.room.effect_set_occupied_heating` (CRHT 1.0.0 scenario 1).
- `thermal.room.operation_set_occupied_cooling` takes
  `thermal.room.setpoint_occupied_cooling` through
  `thermal.room.capability_set_occupied_cooling` and
  `thermal.room.effect_set_occupied_cooling` (CRCT 1.0.0 scenario 1).
- `thermal.room.operation_set_temperature` takes
  `thermal.room.setpoint_temperature_setpoint` through
  `thermal.room.capability_set_temperature` and
  `thermal.room.effect_set_temperature` (CRHT 1.0.0 scenario 1).

A room control does not take a zone argument.

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
`thermal.portal.read.circuit`, `thermal.portal.read.dhw`,
`thermal.portal.read.ventilation`, `thermal.portal.read.heat_generator`,
`thermal.portal.read.thermal_store`, `thermal.portal.read.terminal_unit`,
`thermal.portal.read.refrigerant_circuit`,
`thermal.portal.read.compressor`, `thermal.portal.read.pump`,
`thermal.portal.read.room`, `thermal.portal.read.function`, and
`thermal.portal.read.sensor`. Operation descriptors are
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
The fields, dimensions, services, capabilities, relation definitions and
Portal descriptors of this page changed in place under the version rule of
[api/README.md](../../README.md#version-rule); the PackRef and every
definition version stay 1.0.0. No alias, compatibility shim or dual
acceptance is provided for a removed identifier.

## Validation and correction criteria

Run `python3 scripts/validate_thermal_hvac_pack_v1.py`,
`python3 scripts/test_validate_thermal_hvac_pack_v1.py`, and
`./scripts/check_docs.sh`. Correct invalid ValueKind/unit/dimension/Decimal,
a field without a resource dimension or on another subject, a unit outside
the SI unit set or bounds other than the placement's, a relation definition
with a dangling dimension or other endpoints or cardinality, missing
owner/version, arbitrary public extension, outcome symbol, missing dimension
contract, dangling reference, or mapping-promotion defect.

## Concrete acceptance policy

The typed read descriptors consume every declared field exactly, and each
reads only fields of its own service's subject: the system descriptor reads
action, system mode, operation, fault, outdoor air temperature, system flow
temperature, maintenance, each overrun status, keypad lockout, display unit
and schedule programming; the zone descriptor air
temperature, humidity, the single zone setpoint, the occupied and unoccupied
heating and cooling setpoints, zone mode, and the other admitted zone facts;
`thermal.portal.read.function` reads the function facts and
`thermal.portal.read.sensor` reads the sensor facts; the circuit
descriptor flow rate and circuit flow temperature; the hot-water descriptor
hot-water temperature and setpoint; the ventilation descriptor demand level;
and the descriptor of each
added kind the facts of that kind. The validator rejects an orphaned,
undeclared or foreign read field.

Publication requires exact source epoch, current driver generation, exact
semantic revision, and qualified activation; stale generation is rejected.
Partial publication changes only supplied valid fields while preserving permitted
last-known-good. Withdrawal is explicit and generation-fenced. Stale/unknown
evidence cannot promote or authorize; retained tombstone evidence is
non-actionable.

`thermal.capability.set_temperature` constrains exactly
`thermal.setpoint.temperature_setpoint`; `thermal.capability.set_mode` constrains exactly
`thermal.mode.system`. Stages are admission, dispatch, acknowledgement,
readback, and terminal outcome. Outcomes are `rejected`,
`failed_no_contact`, `acknowledged_unverified`, `applied`, `no_effect`,
`conflict`, and `indeterminate`. `applied` needs post-dispatch current-generation
confirming readback; blind retry is forbidden after possible dispatch or
indeterminate handoff.

## Zone, function and sensor rows

`resource.sensor` is equipment on the physical, energy and control planes.
`thermal.dimension.sensor` names that kind. `thermal.dimension.function` names
anchor class function and no resource kind, on the energy, control and
diagnostic planes. Time programs apply to any function resource. The four
qualifier dimensions are control members. A hold is the quick veto: its
argument is `thermal.hold.state` and its parameters are `thermal.hold.duration`
and `thermal.hold.setpoint`. A setpoint limit is not the validator bound.
`thermal.configuration.display_unit` names `celsius` or `fahrenheit` and
changes no value's unit.

`thermal.mode.zone` gains `thermal.mode.zone.on` and comfort stays. Five
quantities the reviewed table marks signed are direction `not_applicable`
because no supplies relation is named: `thermal.limit.minimum_setpoint_deadband`,
`thermal.limit.setpoint_step`, `thermal.calibration.temperature_offset`,
`thermal.setpoint.change_amount` and `thermal.configuration.emergency_heat_delta`.
The deadband stays 0 to 12.7. `thermal.hold.duration`,
`thermal.program.entry_start` and `thermal.program.entry_end` stay
non-negative. Empty bounds stay empty. `thermal.event.active_program_changed`
is on `thermal.service.function` because its trigger is a function fact.
`thermal.event.setpoint_changed` matches occupied heating only, and its
payload is `thermal.setpoint.change_amount` then `thermal.setpoint.change_source`.
Each admitted operation has one capability and one effect, and a declared
parameter stays a parameter.

Zone status facts are control members because `resource.zone` does not admit
the diagnostic plane. `thermal.limit.humidity_maximum` is not a member: the
second vendor is unconfirmed. `thermal.relation.sensor_zone` is not a member.
A Matter octet handle is text: each octet is two lowercase hexadecimal digits,
high nibble first, with no prefix and no separator. Empty octets are empty
text. A null handle is omitted. A handle of at most 16 octets stays at most
16 octets. Round-trip example octets encode as `00017f80ff0a`. An eeBUS
TimeTable identifier stays a native unsigned integer (SPINE 1.3.0) and does
not use that hexadecimal rule.

New Matter 1.6.1 rows are unknown with `matter.unmapped.v1`.
`thermal.service.function` and `thermal.service.sensor` are unsupported with
`matter.service_not_requested_item.v1`. `evse.ac.current` remains the only
transformed row. The historical Matter 1.7 roster stays at 184 items. Names
are admitted with the historical name equal to the canonical name. The pack
version stays 1.0.0.

- `resource.sensor`
- `thermal.action.zone_state`
- `thermal.calibration.temperature_offset`
- `thermal.capability.read.function`
- `thermal.capability.read.sensor`
- `thermal.capability.set_active_preset`
- `thermal.capability.set_active_program`
- `thermal.capability.set_control_sequence`
- `thermal.capability.set_display_unit`
- `thermal.capability.set_emergency_heat_delta`
- `thermal.capability.set_hold`
- `thermal.capability.set_keypad_lockout`
- `thermal.capability.set_maximum_cooling_setpoint`
- `thermal.capability.set_maximum_heating_setpoint`
- `thermal.capability.set_minimum_cooling_setpoint`
- `thermal.capability.set_minimum_heating_setpoint`
- `thermal.capability.set_occupied_cooling`
- `thermal.capability.set_occupied_heating`
- `thermal.capability.set_preset`
- `thermal.capability.set_program_entry`
- `thermal.capability.set_remote_sensing`
- `thermal.capability.set_schedule_programming`
- `thermal.capability.set_suggestion`
- `thermal.capability.set_temperature_calibration`
- `thermal.capability.set_unoccupied_cooling`
- `thermal.capability.set_unoccupied_heating`
- `thermal.capability.set_zone_cooling_mode`
- `thermal.capability.set_zone_mode`
- `thermal.configuration.control_sequence`
- `thermal.configuration.display_unit`
- `thermal.configuration.emergency_heat_delta`
- `thermal.configuration.keypad_lockout`
- `thermal.configuration.remote_sensing`
- `thermal.configuration.schedule_programming`
- `thermal.demand.cooling`
- `thermal.demand.heating`
- `thermal.dimension.function`
- `thermal.dimension.preset`
- `thermal.dimension.program_entry`
- `thermal.dimension.sensor`
- `thermal.dimension.suggestion`
- `thermal.dimension.time_program`
- `thermal.effect.set_active_preset`
- `thermal.effect.set_active_program`
- `thermal.effect.set_control_sequence`
- `thermal.effect.set_display_unit`
- `thermal.effect.set_emergency_heat_delta`
- `thermal.effect.set_hold`
- `thermal.effect.set_keypad_lockout`
- `thermal.effect.set_maximum_cooling_setpoint`
- `thermal.effect.set_maximum_heating_setpoint`
- `thermal.effect.set_minimum_cooling_setpoint`
- `thermal.effect.set_minimum_heating_setpoint`
- `thermal.effect.set_occupied_cooling`
- `thermal.effect.set_occupied_heating`
- `thermal.effect.set_preset`
- `thermal.effect.set_program_entry`
- `thermal.effect.set_remote_sensing`
- `thermal.effect.set_schedule_programming`
- `thermal.effect.set_suggestion`
- `thermal.effect.set_temperature_calibration`
- `thermal.effect.set_unoccupied_cooling`
- `thermal.effect.set_unoccupied_heating`
- `thermal.effect.set_zone_cooling_mode`
- `thermal.effect.set_zone_mode`
- `thermal.event.active_preset_changed`
- `thermal.event.active_program_changed`
- `thermal.event.local_temperature_changed`
- `thermal.event.occupancy_changed`
- `thermal.event.running_mode_changed`
- `thermal.event.running_state_changed`
- `thermal.event.setpoint_changed`
- `thermal.event.system_mode_changed`
- `thermal.hold.duration`
- `thermal.hold.expiry`
- `thermal.hold.setpoint`
- `thermal.hold.state`
- `thermal.limit.absolute_maximum_cooling_setpoint`
- `thermal.limit.absolute_maximum_heating_setpoint`
- `thermal.limit.absolute_minimum_cooling_setpoint`
- `thermal.limit.absolute_minimum_heating_setpoint`
- `thermal.limit.maximum_cooling_setpoint`
- `thermal.limit.maximum_heating_setpoint`
- `thermal.limit.minimum_cooling_setpoint`
- `thermal.limit.minimum_heating_setpoint`
- `thermal.limit.minimum_setpoint_deadband`
- `thermal.limit.setpoint_step`
- `thermal.measurement.sensor_humidity`
- `thermal.measurement.sensor_temperature`
- `thermal.mode.zone_cooling`
- `thermal.operation.set_active_preset`
- `thermal.operation.set_active_program`
- `thermal.operation.set_control_sequence`
- `thermal.operation.set_display_unit`
- `thermal.operation.set_emergency_heat_delta`
- `thermal.operation.set_hold`
- `thermal.operation.set_keypad_lockout`
- `thermal.operation.set_maximum_cooling_setpoint`
- `thermal.operation.set_maximum_heating_setpoint`
- `thermal.operation.set_minimum_cooling_setpoint`
- `thermal.operation.set_minimum_heating_setpoint`
- `thermal.operation.set_occupied_cooling`
- `thermal.operation.set_occupied_heating`
- `thermal.operation.set_preset`
- `thermal.operation.set_program_entry`
- `thermal.operation.set_remote_sensing`
- `thermal.operation.set_schedule_programming`
- `thermal.operation.set_suggestion`
- `thermal.operation.set_temperature_calibration`
- `thermal.operation.set_unoccupied_cooling`
- `thermal.operation.set_unoccupied_heating`
- `thermal.operation.set_zone_cooling_mode`
- `thermal.operation.set_zone_mode`
- `thermal.portal.read.function`
- `thermal.portal.read.sensor`
- `thermal.preset.active_handle`
- `thermal.preset.built_in`
- `thermal.preset.cooling_setpoint`
- `thermal.preset.heating_setpoint`
- `thermal.preset.maximum_count`
- `thermal.preset.name`
- `thermal.preset.scenario`
- `thermal.preset.supported_scenarios`
- `thermal.program.active_handle`
- `thermal.program.built_in`
- `thermal.program.entry_cooling_setpoint`
- `thermal.program.entry_days`
- `thermal.program.entry_end`
- `thermal.program.entry_heating_setpoint`
- `thermal.program.entry_preset`
- `thermal.program.entry_start`
- `thermal.program.entry_state`
- `thermal.program.entry_system_mode`
- `thermal.program.maximum_count`
- `thermal.program.maximum_entries`
- `thermal.program.maximum_entries_per_day`
- `thermal.program.name`
- `thermal.program.preset`
- `thermal.program.supported_types`
- `thermal.program.system_mode`
- `thermal.service.function`
- `thermal.service.sensor`
- `thermal.setpoint.change_amount`
- `thermal.setpoint.change_source`
- `thermal.setpoint.change_time`
- `thermal.status.occupancy`
- `thermal.status.window`
- `thermal.status.zone_running_state`
- `thermal.suggestion.active`
- `thermal.suggestion.current`
- `thermal.suggestion.effective_time`
- `thermal.suggestion.expiration`
- `thermal.suggestion.maximum_count`
- `thermal.suggestion.not_following_reason`
- `thermal.suggestion.preset`

## Hydraulic, circuit and store rows

`resource.valve` is a component. `resource.solar_thermal_circuit` is a function. `resource.solar_collector` and `resource.detector` are equipment. `resource.water_tank` is a component. `thermal.dimension.replacement_product` qualifies `thermal.water_tank.replacement_product_identifier` and is `unit.one` on the physical plane. Empty bounds stay empty. Two-vendor-only rows stay out: `thermal.status.legionella_protection`, `thermal.configuration.legionella_days`, `thermal.configuration.legionella_time`, `thermal.setpoint.store_charge_temperature`, `thermal.configuration.store_charge_hysteresis`, `thermal.configuration.dew_point_offset`, `thermal.measurement.pump_start_count`, `thermal.valve.role`, `thermal.status.frost_protection`. `thermal.relation.valve_member`, `thermal.relation.pump_member`, `thermal.relation.solar_circuit_collector`, `thermal.relation.detector_member` and `thermal.relation.water_tank_member` are members. `thermal.relation.solar_supply` is not added. These events stay out: `thermal.event.dhw_boost_started`, `thermal.event.dhw_boost_ended`, `thermal.event.pump_supply_voltage_low`, `thermal.event.pump_supply_voltage_high`, `thermal.event.pump_power_missing_phase`, `thermal.event.pump_system_pressure_low`, `thermal.event.pump_system_pressure_high`, `thermal.event.pump_dry_running`, `thermal.event.pump_motor_temperature_high`, `thermal.event.pump_motor_fatal_failure`, `thermal.event.pump_electronic_temperature_high`, `thermal.event.pump_pump_blocked`, `thermal.event.pump_sensor_failure`, `thermal.event.pump_electronic_non_fatal_failure`, `thermal.event.pump_electronic_fatal_failure`, `thermal.event.pump_general_fault`, `thermal.event.pump_leakage`, `thermal.event.pump_air_detection`, `thermal.event.pump_turbine_operation`. `thermal.relation.zone_room`, `thermal.relation.circuit_room` and `thermal.operation.set_zone_mode` stay.

- `resource.valve`
- `resource.solar_thermal_circuit`
- `resource.solar_collector`
- `resource.detector`
- `resource.water_tank`
- `thermal.dimension.replacement_product`
- `thermal.dimension.valve`
- `thermal.dimension.solar_circuit`
- `thermal.dimension.solar_collector`
- `thermal.dimension.detector`
- `thermal.dimension.water_tank`
- `thermal.service.valve`
- `thermal.service.solar_circuit`
- `thermal.service.solar_collector`
- `thermal.service.detector`
- `thermal.service.water_tank`
- `thermal.mode.dhw`
- `thermal.mode.dhw_supported`
- `thermal.dhw.heater_types`
- `thermal.dhw.heat_demand`
- `thermal.dhw.estimated_heat_required`
- `thermal.dhw.charge_ratio`
- `thermal.dhw.boost_state`
- `thermal.dhw.boost_duration`
- `thermal.dhw.boost_one_shot`
- `thermal.dhw.boost_emergency`
- `thermal.dhw.boost_temporary_setpoint`
- `thermal.dhw.boost_target_ratio`
- `thermal.dhw.boost_target_reheat_ratio`
- `thermal.measurement.dhw_flow_rate`
- `thermal.measurement.dhw_circuit_flow_temperature`
- `thermal.measurement.dhw_circuit_return_temperature`
- `thermal.nameplate.store_volume`
- `thermal.measurement.store_top_temperature`
- `thermal.measurement.store_bottom_temperature`
- `thermal.status.pump_running`
- `thermal.status.pump`
- `thermal.status.pump_alarms`
- `thermal.mode.pump_operation`
- `thermal.mode.pump_effective_operation`
- `thermal.mode.pump_control`
- `thermal.mode.pump_effective_control`
- `thermal.measurement.pump_capacity`
- `thermal.setpoint.pump_level`
- `thermal.measurement.pump_running_time`
- `thermal.measurement.pump_power`
- `thermal.energy.pump_consumed`
- `thermal.measurement.pump_flow_rate`
- `thermal.measurement.pump_pressure`
- `thermal.measurement.pump_medium_temperature`
- `thermal.nameplate.pump_maximum_pressure`
- `thermal.nameplate.pump_maximum_speed`
- `thermal.nameplate.pump_maximum_flow`
- `thermal.nameplate.pump_minimum_constant_pressure`
- `thermal.nameplate.pump_maximum_constant_pressure`
- `thermal.nameplate.pump_minimum_compensated_pressure`
- `thermal.nameplate.pump_maximum_compensated_pressure`
- `thermal.nameplate.pump_minimum_constant_speed`
- `thermal.nameplate.pump_maximum_constant_speed`
- `thermal.nameplate.pump_minimum_constant_flow`
- `thermal.nameplate.pump_maximum_constant_flow`
- `thermal.nameplate.pump_minimum_constant_temperature`
- `thermal.nameplate.pump_maximum_constant_temperature`
- `thermal.status.valve_state`
- `thermal.setpoint.valve_target_state`
- `thermal.measurement.valve_level`
- `thermal.setpoint.valve_target_level`
- `thermal.configuration.valve_default_open_level`
- `thermal.configuration.valve_level_step`
- `thermal.valve.open_duration`
- `thermal.configuration.valve_default_open_duration`
- `thermal.valve.auto_close_time`
- `thermal.valve.remaining_duration`
- `thermal.status.valve_faults`
- `thermal.measurement.valve_flow_rate`
- `thermal.measurement.system_water_pressure`
- `thermal.measurement.circuit_water_pressure`
- `thermal.measurement.heat_generator_flow_rate`
- `thermal.measurement.circuit_return_temperature`
- `thermal.measurement.dew_point`
- `thermal.measurement.circuit_humidity`
- `thermal.measurement.collector_temperature`
- `thermal.measurement.solar_flow_temperature`
- `thermal.measurement.solar_return_temperature`
- `thermal.measurement.solar_power`
- `thermal.status.leak`
- `thermal.status.freeze`
- `thermal.detector.sensitivity_level`
- `thermal.detector.supported_sensitivity_levels`
- `thermal.detector.default_sensitivity_level`
- `thermal.detector.alarms_active`
- `thermal.detector.alarms_suppressed`
- `thermal.detector.alarms_enabled`
- `thermal.detector.alarms_supported`
- `thermal.detector.sensor_fault`
- `thermal.water_tank.condition`
- `thermal.water_tank.degradation_direction`
- `thermal.water_tank.change_indication`
- `thermal.water_tank.in_place`
- `thermal.water_tank.last_changed`
- `thermal.water_tank.replacement_product_identifier`
- `thermal.capability.set_dhw_mode`
- `thermal.operation.set_dhw_mode`
- `thermal.effect.set_dhw_mode`
- `thermal.capability.set_dhw_temperature`
- `thermal.operation.set_dhw_temperature`
- `thermal.effect.set_dhw_temperature`
- `thermal.capability.set_dhw_boost`
- `thermal.operation.set_dhw_boost`
- `thermal.effect.set_dhw_boost`
- `thermal.capability.set_pump_running`
- `thermal.operation.set_pump_running`
- `thermal.effect.set_pump_running`
- `thermal.capability.set_pump_operation_mode`
- `thermal.operation.set_pump_operation_mode`
- `thermal.effect.set_pump_operation_mode`
- `thermal.capability.set_pump_control_mode`
- `thermal.operation.set_pump_control_mode`
- `thermal.effect.set_pump_control_mode`
- `thermal.capability.set_pump_level`
- `thermal.operation.set_pump_level`
- `thermal.effect.set_pump_level`
- `thermal.capability.set_valve_state`
- `thermal.operation.set_valve_state`
- `thermal.effect.set_valve_state`
- `thermal.capability.set_valve_level`
- `thermal.operation.set_valve_level`
- `thermal.effect.set_valve_level`
- `thermal.capability.set_valve_default_open_duration`
- `thermal.operation.set_valve_default_open_duration`
- `thermal.effect.set_valve_default_open_duration`
- `thermal.capability.set_valve_default_open_level`
- `thermal.operation.set_valve_default_open_level`
- `thermal.effect.set_valve_default_open_level`
- `thermal.capability.suppress_detector_alarm`
- `thermal.operation.suppress_detector_alarm`
- `thermal.effect.suppress_detector_alarm`
- `thermal.capability.enable_detector_alarm`
- `thermal.operation.enable_detector_alarm`
- `thermal.effect.enable_detector_alarm`
- `thermal.capability.set_detector_sensitivity`
- `thermal.operation.set_detector_sensitivity`
- `thermal.effect.set_detector_sensitivity`
- `thermal.capability.reset_water_tank`
- `thermal.operation.reset_water_tank`
- `thermal.effect.reset_water_tank`
- `thermal.event.valve_state_changed`
- `thermal.event.valve_fault`
- `thermal.event.leak_changed`
- `thermal.event.freeze_changed`
- `thermal.event.detector_alarms_changed`
- `thermal.event.detector_sensor_fault`
- `thermal.portal.read.valve`
- `thermal.portal.read.solar_circuit`
- `thermal.portal.read.solar_collector`
- `thermal.portal.read.detector`
- `thermal.portal.read.water_tank`

## Generator and ventilation rows

`resource.fan` is a component on the physical and control planes. `resource.air_filter` is a component on the physical, control and diagnostic planes. `thermal.dimension.fan` and `thermal.service.fan` carry the fan planes. `thermal.dimension.air_filter` and `thermal.service.air_filter` carry the filter planes. `thermal.portal.read.fan` and `thermal.portal.read.air_filter` read those subjects. No read capability is added for them.

`thermal.dimension.period` is a symbol qualifier with `day`, `month` and `year` on the energy plane. `lifetime` is not a symbol. `thermal.dimension.period_offset` is `unit.one` on the energy plane. `thermal.dimension.substance` and `thermal.dimension.statistic` are symbol qualifiers on the energy and control planes. `thermal.dimension.purpose` and `thermal.dimension.louver_axis` stay out. `thermal.measurement.louver_position` has no axis qualifier. `thermal.energy.electrical_consumed` and `thermal.energy.solar_yield` are qualified by `thermal.dimension.period` and `thermal.dimension.period_offset`.

`thermal.measurement.electrical_power` is `unit.watt` on the energy plane with direction `not_applicable`. The quantity is signed in the fact table, and this pack admits no electrical supplies relation for it. Empty bounds stay empty. `thermal.event.maintenance_due` is entered and derived from `thermal.status.maintenance` when the status is `due`. The overrun operations take the existing overrun status. The symbols stay `active`, `finished`, `inactive` and `running`. An argument of `active` starts the overrun and `inactive` stops it. Readback `running` confirms active and `finished` confirms inactive. There is no default-deny rule. `thermal.relation.fan_member` and `thermal.relation.filter_member` are members. Two-vendor-only rows stay out: `thermal.energy.fuel_consumed`, `thermal.energy.heat_delivered`, `thermal.energy.environmental_yield`, `thermal.measurement.modulation`, `thermal.setpoint.modulation`, `thermal.status.flame`, `thermal.status.backup_heater`, `thermal.measurement.burner_starts`, `thermal.measurement.burner_operating_time`, `thermal.measurement.compressor_starts`, `thermal.measurement.compressor_operating_time`, `thermal.nameplate.heat_output`, `thermal.configuration.partial_load_power`, `thermal.configuration.heating_curve_slope`, `thermal.configuration.heating_curve_offset`, `thermal.configuration.circuit_kind`, `thermal.status.screed_drying`, `thermal.program.screed_drying_day`, `thermal.setpoint.screed_drying_temperature`, `thermal.configuration.bivalence_heating_temperature`, `thermal.configuration.bivalence_dhw_temperature`, `thermal.maintenance.next_due`, `thermal.absence.start`, `thermal.absence.end`, `thermal.absence.setpoint`, `thermal.measurement.fan_speed`, `thermal.measurement.heat_recovery_efficiency`, `thermal.status.bypass`, `thermal.operation.set_screed_drying`, `thermal.operation.set_absence`, `thermal.operation.set_heating_curve`, `thermal.operation.set_bivalence_temperatures`, `thermal.dimension.purpose`, `thermal.dimension.louver_axis`.

- `resource.fan`
- `resource.air_filter`
- `thermal.dimension.fan`
- `thermal.dimension.air_filter`
- `thermal.dimension.period`
- `thermal.dimension.period_offset`
- `thermal.dimension.substance`
- `thermal.dimension.statistic`
- `thermal.service.fan`
- `thermal.service.air_filter`
- `thermal.portal.read.fan`
- `thermal.portal.read.air_filter`
- `thermal.measurement.electrical_power`
- `thermal.energy.electrical_consumed`
- `thermal.energy.solar_yield`
- `thermal.setpoint.heat_generator_flow_temperature`
- `thermal.setpoint.circuit_flow_temperature`
- `thermal.setpoint.circuit_fixed_flow_temperature`
- `thermal.limit.circuit_flow_temperature_minimum`
- `thermal.limit.circuit_flow_temperature_maximum`
- `thermal.measurement.outdoor_air_temperature_average`
- `thermal.status.terminal_unit_power`
- `thermal.measurement.terminal_unit_air_temperature`
- `thermal.measurement.terminal_unit_humidity`
- `thermal.setpoint.terminal_unit_heating`
- `thermal.setpoint.terminal_unit_cooling`
- `thermal.measurement.coil_temperature`
- `thermal.configuration.ac_type`
- `thermal.nameplate.cooling_capacity`
- `thermal.configuration.refrigerant_type`
- `thermal.configuration.compressor_type`
- `thermal.status.terminal_unit_errors`
- `thermal.measurement.louver_position`
- `thermal.fan.mode`
- `thermal.fan.mode_sequence`
- `thermal.fan.speed_setting`
- `thermal.fan.speed_ratio`
- `thermal.fan.speed_step_maximum`
- `thermal.fan.speed_step_setting`
- `thermal.fan.speed_step`
- `thermal.fan.rock_support`
- `thermal.fan.rock_setting`
- `thermal.fan.wind_support`
- `thermal.fan.wind_setting`
- `thermal.fan.airflow_direction`
- `thermal.mode.ventilation`
- `thermal.measurement.supply_air_flow`
- `thermal.measurement.extract_air_flow`
- `thermal.measurement.supply_air_temperature`
- `thermal.measurement.extract_air_temperature`
- `thermal.measurement.outdoor_intake_air_temperature`
- `thermal.measurement.exhaust_air_temperature`
- `thermal.filter.kind`
- `thermal.filter.condition`
- `thermal.filter.degradation_direction`
- `thermal.filter.change_indication`
- `thermal.filter.in_place`
- `thermal.filter.last_changed`
- `thermal.filter.replacement_product_kind`
- `thermal.filter.replacement_product_identifier`
- `thermal.measurement.air_quality`
- `thermal.air.volume_fraction`
- `thermal.air.mass_concentration`
- `thermal.air.radon_concentration`
- `thermal.air.statistic_window`
- `thermal.air.level`
- `thermal.air.uncertainty`
- `thermal.air.measurement_medium`
- `thermal.capability.set_heat_generator_flow_temperature`
- `thermal.operation.set_heat_generator_flow_temperature`
- `thermal.effect.set_heat_generator_flow_temperature`
- `thermal.capability.set_circuit_fixed_flow_temperature`
- `thermal.operation.set_circuit_fixed_flow_temperature`
- `thermal.effect.set_circuit_fixed_flow_temperature`
- `thermal.capability.set_circuit_flow_temperature_minimum`
- `thermal.operation.set_circuit_flow_temperature_minimum`
- `thermal.effect.set_circuit_flow_temperature_minimum`
- `thermal.capability.set_circuit_flow_temperature_maximum`
- `thermal.operation.set_circuit_flow_temperature_maximum`
- `thermal.effect.set_circuit_flow_temperature_maximum`
- `thermal.capability.set_overrun_hvac_system_off`
- `thermal.operation.set_overrun_hvac_system_off`
- `thermal.effect.set_overrun_hvac_system_off`
- `thermal.capability.set_overrun_one_day_at_home`
- `thermal.operation.set_overrun_one_day_at_home`
- `thermal.effect.set_overrun_one_day_at_home`
- `thermal.capability.set_overrun_one_day_away`
- `thermal.operation.set_overrun_one_day_away`
- `thermal.effect.set_overrun_one_day_away`
- `thermal.capability.set_overrun_one_time_dhw`
- `thermal.operation.set_overrun_one_time_dhw`
- `thermal.effect.set_overrun_one_time_dhw`
- `thermal.capability.set_overrun_one_time_ventilation`
- `thermal.operation.set_overrun_one_time_ventilation`
- `thermal.effect.set_overrun_one_time_ventilation`
- `thermal.capability.set_overrun_party`
- `thermal.operation.set_overrun_party`
- `thermal.effect.set_overrun_party`
- `thermal.capability.set_overrun_sg_ready_condition_1`
- `thermal.operation.set_overrun_sg_ready_condition_1`
- `thermal.effect.set_overrun_sg_ready_condition_1`
- `thermal.capability.set_overrun_sg_ready_condition_3`
- `thermal.operation.set_overrun_sg_ready_condition_3`
- `thermal.effect.set_overrun_sg_ready_condition_3`
- `thermal.capability.set_overrun_sg_ready_condition_4`
- `thermal.operation.set_overrun_sg_ready_condition_4`
- `thermal.effect.set_overrun_sg_ready_condition_4`
- `thermal.capability.set_overrun_valve_kick`
- `thermal.operation.set_overrun_valve_kick`
- `thermal.effect.set_overrun_valve_kick`
- `thermal.capability.set_terminal_unit_power`
- `thermal.operation.set_terminal_unit_power`
- `thermal.effect.set_terminal_unit_power`
- `thermal.capability.set_terminal_unit_mode`
- `thermal.operation.set_terminal_unit_mode`
- `thermal.effect.set_terminal_unit_mode`
- `thermal.capability.set_terminal_unit_heating`
- `thermal.operation.set_terminal_unit_heating`
- `thermal.effect.set_terminal_unit_heating`
- `thermal.capability.set_terminal_unit_cooling`
- `thermal.operation.set_terminal_unit_cooling`
- `thermal.effect.set_terminal_unit_cooling`
- `thermal.capability.set_louver_position`
- `thermal.operation.set_louver_position`
- `thermal.effect.set_louver_position`
- `thermal.capability.set_fan_mode`
- `thermal.operation.set_fan_mode`
- `thermal.effect.set_fan_mode`
- `thermal.capability.set_fan_speed`
- `thermal.operation.set_fan_speed`
- `thermal.effect.set_fan_speed`
- `thermal.capability.set_fan_step`
- `thermal.operation.set_fan_step`
- `thermal.effect.set_fan_step`
- `thermal.capability.set_fan_rock`
- `thermal.operation.set_fan_rock`
- `thermal.effect.set_fan_rock`
- `thermal.capability.set_fan_wind`
- `thermal.operation.set_fan_wind`
- `thermal.effect.set_fan_wind`
- `thermal.capability.set_fan_airflow_direction`
- `thermal.operation.set_fan_airflow_direction`
- `thermal.effect.set_fan_airflow_direction`
- `thermal.capability.set_ventilation_mode`
- `thermal.operation.set_ventilation_mode`
- `thermal.effect.set_ventilation_mode`
- `thermal.capability.set_ventilation_level`
- `thermal.operation.set_ventilation_level`
- `thermal.effect.set_ventilation_level`
- `thermal.capability.reset_filter`
- `thermal.operation.reset_filter`
- `thermal.effect.reset_filter`
- `thermal.capability.set_filter_last_changed`
- `thermal.operation.set_filter_last_changed`
- `thermal.effect.set_filter_last_changed`
- `thermal.event.maintenance_due`
