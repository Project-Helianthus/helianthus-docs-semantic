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
`thermal.dimension.pump`, `thermal.dimension.room`, and
`thermal.dimension.sensor`; each of these is typed text and names one
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

The pump service has a read descriptor and no read capability. `thermal.service.function` binds `thermal.dimension.function` and `thermal.capability.read.function` reads it. Each service
binds the matching dimension. Operations require qualified
current binding: `thermal.capability.set_temperature` on the zone service and
`thermal.capability.set_mode` on the system service. Indoor and outdoor units
are not kinds.

The pack declares eight relation definitions. Each names the dimensions of its
`from` and `to` ends as lists and its cardinality; the
[element catalog](../element-catalog-v1.json) states the core type,
orientation, endpoint kinds, medium, admitted basis classes and planes:

| Definition | Core type | From | To | Cardinality | Basis classes | Planes |
|---|---|---|---|---|---|---|
| `thermal.relation.system_member` | `groups` | thermal system | zone, thermal circuit, domestic hot water, ventilation system, heat generator, thermal store, terminal unit, refrigerant circuit | one to many | configuration, gate rule | physical, control |
| `thermal.relation.fluid_supply` | `supplies`, heat-transfer fluid | heat generator, thermal store, thermal circuit | thermal circuit, thermal store, zone, domestic hot water, terminal unit | many to many | configuration | energy, hydraulic |
| `thermal.relation.air_supply` | `supplies`, air | terminal unit, ventilation system | zone | many to many | configuration | energy |
| `thermal.relation.refrigerant_circuit_member` | `groups` | refrigerant circuit | heat generator, terminal unit | one to many | configuration, gate rule | physical, hydraulic |
| `thermal.relation.generator_compressor` | `contains` | heat generator | compressor | one to many | gate rule | physical, hydraulic, diagnostic |
| `thermal.relation.circuit_room` | `contains` | thermal circuit | room | one to many | configuration | physical |
| `thermal.relation.circuit_zone` | `contains` | thermal circuit | zone | one to many | configuration | physical |
| `thermal.relation.zone_room` | `contains` | zone | room | one to many | configuration | physical |

The core-owned definition `relation.thermal_control` (`controls`) runs from
generic equipment to the thermal system, zone, thermal circuit, domestic hot
water, ventilation system, heat generator and terminal unit, many to many,
with basis classes configuration and gate rule, in the control plane. It is
listed in the element catalog because one of its ends is not reached through
a dimension of this pack.

A relation instance is published only with the basis class its native owner
documents; without it the relation is unknown and no absence statement is
made. `thermal.relation.fluid_supply` admits configuration until a native
owner documents another class. `thermal.relation.fluid_supply` is a separate
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
