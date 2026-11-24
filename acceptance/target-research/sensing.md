---
status: "research notes for Matter 1.6.1 temperature, pressure, flow and humidity clusters; no mapping is decided and no canonical target is written."
---

# Temperature, pressure, flow and humidity

Matter 1.6.1 cluster accounting for Temperature, pressure, flow and humidity. Identifiers, conformance, types and units are read from go-fabric@v0.22.2:parity/schema.json (revision 1.6.1, data model revision 21) and the generated cluster and device files cited below. Catalog elements are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json and semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json. Canonical units are the `canonical_unit` field of docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json. Target rows are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json and docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md. No mapping is chosen. No grade in this note is `exact`. Charge capacity stays `unit.ampere_hour` where the catalog defines it; `storage.capacity.remaining` and `storage.capacity.full_charge` are absent from the pinned catalog. A catalog canonical unit is written beside the Matter unit on each element row that names a catalog field.

Read-only source accounting for the Matter clusters TemperatureMeasurement, PressureMeasurement, FlowMeasurement and RelativeHumidityMeasurement, and for the device types TemperatureSensor, PressureSensor, FlowSensor and HumiditySensor. No mapping is decided here.

## Header

- docs-semantic frozen SHA `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:` (view the docs-semantic pin). `HEAD` at read time was that SHA.
- semreg frozen SHA `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:` (view the semreg pin). `HEAD` at read time was that SHA.
- go-fabric module path `go-fabric`, directory `go-fabric v0.22.2`. `CHANGELOG.md` heading `[0.22.2]` is dated 2026-11-12. `go-fabric@v0.22.2:parity/schema.json` `matter.revision` is `"1.6.1"` (line 3), `specificationVersion` 17170688 (line 4), `interactionModelRevision` 12 (line 5), `dataModelRevision` 21 (line 6), `sourceCommit` `a commit id recorded in the cited file` (line 7). Each cluster file header names that same Matter revision and the matter.js commit prefix `a commit id recorded in the cited file`.
- The Matter 1.6.1 target's own `model_source.tag` is `v0.13.12`, not v0.22.2 (`api/v1/targets/matter-1.6.1-v1.json`, `model_source.tag`). Its `model_source.models` names Electrical Sensor, Power Topology and Electrical Power Measurement only. This note uses v0.22.2 for the cluster facts below.

Files read:

- `go-fabric@v0.22.2:cluster/spec/temperaturemeasurement/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/pressuremeasurement/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/flowmeasurement/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/relativehumiditymeasurement/definition_gen.go`.
- `go-fabric@v0.22.2:device/temperature_sensor_gen.go`, `go-fabric@v0.22.2:device/pressure_sensor_gen.go`, `go-fabric@v0.22.2:device/flow_sensor_gen.go`, `go-fabric@v0.22.2:device/humidity_sensor_gen.go`.
- `go-fabric@v0.22.2:parity/schema.json` (the four cluster objects, the four device-type objects, and device-type requirements whose cluster id is 1026, 1027, 1028 or 1029). `schema.json` has no `"unit"` key.
- `go-fabric@v0.22.2:schema/element_names_gen.go` lines 1118–1150; `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` for the four sensor device types (around lines 1925–2028).
- `go-fabric@v0.22.2:cluster/measurement/measurement.go` (temperature, humidity and pressure server comments and read paths), `go-fabric@v0.22.2:cluster/measurement/flow.go`, `go-fabric@v0.22.2:cluster/spec/thermostat/values.go` lines 11–36. These are hand-written servers and a value helper. They are not the generated cluster definition. Wire scales below are cited as statements of those files.
- docs-semantic at the frozen SHA: `api/v1/element-catalog-v1.json` (contract `helianthus.semantic.element-catalog/v1`, status `accepted`, 394 elements), `api/v1/targets/matter-1.6.1-v1.json` (contract `helianthus.gateway.matter-projection/v1`, status `adoption_projection_contract_pre_1_0`, `mapping_revision` 1, 246 rows), `api/v1/targets/matter-1.6.1-v1.md` (front matter and the evidence section), `tests/test_matter161_target.py` lines 35–55.
- semreg at the frozen SHA: `fixtures/v1/element-catalog-v1.json`. Normalized JSON of the 18 measurement facts named in the cluster tables is the same in both catalogs. The two catalog files are not byte-identical: 20 other elements differ. None of those 20 ids is one of the 18 facts.
- Same content as the pinned JSON, one row per element. Sources: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`, `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`.
- Prior claims were checked only against a prior accounting lines 1–8, 702–742, 1047–1064; a prior accounting lines 98–122 and 304.
- Plan: the registry unit rule item 3 (SI units in the registry) and item 49 (do not invent). the research row QQ04 was identified as the queue authority for this read-only accounting.

How a row is filled:

- Conformance text is the generated `Conformance.Text`, unless the only declaration is `schema.json` `effective.conformance.text`.
- "Mandatory for which device types" means a device type in `go-fabric@v0.22.2:parity/schema.json` `deviceTypes` whose requirement for this cluster is server conformance `M`, and whose attribute or feature conformance is `M`. Optional (`O`), choice (`O.a+`), feature-name (`EXT`) and optional-if (`[EXT]`) are not treated as mandatory. Client requirements are not server mandates.
- A catalog element is `partial` when `element_kind` is `fact`, `attributes.value_kind` is `quantity`, and the element id names the same quantity class as the Matter attribute (temperature, pressure, flow rate, or humidity). It is not `exact`: the catalog record has no unit; the subject is one resource kind and one dimension; aggregation is on the record; the Matter value is one nullable cluster attribute. No row is `exact`. `candidate` is not used for these 18 facts.
- Ids that appear only on the a prior accounting, and are absent from both catalogs, are written `none in catalog (proposed by <tickets on that prior accounting row>)`. The prior accounting does not assign a ticket per id. The tickets are the row's ticket cell.
- Catalog status is present or absent at docs-semantic SHA `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`.
- Target disposition is the row in `matter-1.6.1-v1.json` for that element id. Every present fact, capability and operation named below is `unknown` / `matter.unmapped.v1`. The test names that pair `UNMAPPED` (`tests/test_matter161_target.py:41`). The row's `loss` entry has `kind` `policy`. Absent ids have `no row`.
- Source status is `defined` when a catalog element is named, and `no source` when none is. Whether a driver feeds an element is not in these sources.
- Loss is `none` only for an exact correspondence. There is no exact correspondence in this group.

`schema.json` cluster objects (the `"id"` line of each object): TemperatureMeasurement line 106252 (id 1026, revision 6), PressureMeasurement line 106437 (id 1027, revision 5), FlowMeasurement line 106842 (id 1028, revision 5), RelativeHumidityMeasurement line 107026 (id 1029, revision 5). Classification of each is `application`. Each has `commands` `[]` and `events` `[]`.

Wire scale, only where a go-fabric file states one. `schema.json` and `definition_gen.go` do not carry a unit field.

| Cluster | Generated type | What the hand-written file states | Locator |
|---|---|---|---|
| TemperatureMeasurement | `temperature`, int16 | Celsius model value, int16 wire step of 0.01, citing Matter §2.3.5.1. `CelsiusToInt16` multiplies by 100 and clamps to [-27315, 32766]. | `go-fabric@v0.22.2:cluster/measurement/measurement.go:274-275`; `go-fabric@v0.22.2:cluster/spec/thermostat/values.go:11-36` |
| PressureMeasurement | int16 | Model unit the file uses is hPa. It says one wire step is 0.1 kPa and cites Matter §2.4.5.1. | `go-fabric@v0.22.2:cluster/measurement/measurement.go:535-538` |
| FlowMeasurement | uint16 | Model unit the file uses is m³/h. It says one wire step is 0.1 m³/h. The citation is a matter.js resource path, not a Matter clause number. | `go-fabric@v0.22.2:cluster/measurement/flow.go:34-36` |
| RelativeHumidityMeasurement | uint16 | Model unit the file uses is percent on a 0–100 span. It says the wire step is 0.01 percent and cites Matter §2.6.5.1. | `go-fabric@v0.22.2:cluster/measurement/measurement.go:367-368` |

Those clause numbers are citations written in the go-fabric files. The licensed clause text is not in the local sources, and it is not restated here.

Catalog facts used below have attributes `value_kind`, `subject`, `aggregation` and `direction` only. Example locator: `thermal.measurement.air_temperature` at `api/v1/element-catalog-v1.json:12537`.

## Device types

Lists follow the device file's `Servers` slice. `go-fabric@v0.22.2:parity/schema.json` requirements for the same device type also include a Descriptor server cluster (`id` 29, `0x001D`) with no `conformance` field. The device files do not. That difference is recorded under each device type and is not resolved.

### TemperatureSensor

- Locator: `go-fabric@v0.22.2:device/temperature_sensor_gen.go:15-49`. Schema device object: `go-fabric@v0.22.2:parity/schema.json:16608` (id 770, name TemperatureSensor, classification `simple`, revision 3).
- Id `0x0302` (770). Revision 3. Classification `simple`. Composition `schema.CompositionTree` (`go-fabric@v0.22.2:device/temperature_sensor_gen.go:28-30`).
- Required server clusters in the device file: TemperatureMeasurement `0x0402`, conformance `M`, `Mandatory: true` (lines 32–36); Identify `0x0003`, conformance `M`, `Mandatory: true` (lines 37–41).
- Optional server clusters in the device file: ThermostatUserInterfaceConfiguration `0x0204`, conformance `O`, no `Mandatory: true` (lines 42–48). Nested element: attribute KeypadLockout `0x0001`, `PresenceOptional` (line 45).
- Schema requirements order (`go-fabric@v0.22.2:parity/schema.json` device object, requirements array): Identify `M`, Descriptor with no conformance field, ThermostatUserInterfaceConfiguration `O`, TemperatureMeasurement `M`. The device file order is TemperatureMeasurement, Identify, ThermostatUserInterfaceConfiguration, and it omits Descriptor.
- Schema `effective.requirements` nests attribute DeviceTypeList under Descriptor (no conformance text on that attribute in the dump) and attribute KeypadLockout under ThermostatUserInterfaceConfiguration with conformance text `O`.

### PressureSensor

- Locator: `go-fabric@v0.22.2:device/pressure_sensor_gen.go:14-41`. Schema device object: `go-fabric@v0.22.2:parity/schema.json:17334` (id 773, revision 3, classification `simple`).
- Id `0x0305` (773). Revision 3. Classification `simple`. Composition tree (lines 27–30).
- Required server clusters in the device file: Identify `0x0003`, conformance `M`, `Mandatory: true` (lines 31–35); PressureMeasurement `0x0403`, conformance `M`, `Mandatory: true` (lines 36–40).
- Optional server clusters in the device file: none.
- Schema requirements also include Descriptor `0x001D` with no conformance field. The device file omits it.

### FlowSensor

- Locator: `go-fabric@v0.22.2:device/flow_sensor_gen.go:14-41`. Schema device object: `go-fabric@v0.22.2:parity/schema.json:17420` (id 774, revision 3, classification `simple`).
- Id `0x0306` (774). Revision 3. Classification `simple`. Composition tree (lines 27–30).
- Required server clusters in the device file: Identify `0x0003`, conformance `M`, `Mandatory: true` (lines 31–35); FlowMeasurement `0x0404`, conformance `M`, `Mandatory: true` (lines 36–40).
- Optional server clusters in the device file: none.
- Schema requirements also include Descriptor `0x001D` with no conformance field. The device file omits it.

### HumiditySensor

- Locator: `go-fabric@v0.22.2:device/humidity_sensor_gen.go:14-41`. Schema device object: `go-fabric@v0.22.2:parity/schema.json:17506` (id 775, revision 3, classification `simple`).
- Id `0x0307` (775). Revision 3. Classification `simple`. Composition tree (lines 27–30).
- Required server clusters in the device file: Identify `0x0003`, conformance `M`, `Mandatory: true` (lines 31–35); RelativeHumidityMeasurement `0x0405`, conformance `M`, `Mandatory: true` (lines 36–40).
- Optional server clusters in the device file: none.
- Schema requirements also include Descriptor `0x001D` with no conformance field. The device file omits it.

Identify (`0x0003`) is mandatory on all four device files. Its attributes, commands, events and features are outside this cluster group and are not expanded.

## TemperatureMeasurement `0x0402`

Revision 6. `definition_gen.go:19-22` and `schema.json:106252`. Commands: none (`schema.json` `commands` `[]`; `definition_gen.go` has no command ids). Events: none (`events` `[]`). Feature bits: none (`schema.json` `features` `[]`). `definition_gen.go:33-36` declares `type Feature uint32` and no bit constants. `Definition.Attributes` does not include ClusterRevision. `schema.json` does, as does `go-fabric@v0.22.2:schema/element_names_gen.go:1118-1123` (no FeatureMap entry for `0x0402`).

Server conformance `M` on device type TemperatureSensor only (`0x0302`). Other requirements of this cluster id, not mandatory:

| Device type | Id | Revision | Side | Conformance |
|---|---|---|---|---|
| AirQualitySensor | `0x002C` | 1 | server | `O` |
| SoilSensor | `0x0045` | 1 | server | `O` |
| TemperatureControlledCabinet | `0x0071` | 6 | server | `O` |
| RoomAirConditioner | `0x0072` | 4 | server | `O` |
| SmokeCoAlarm | `0x0076` | 2 | server | `O` |
| CookSurface | `0x0077` | 2 | server | `O.a+` |
| Pump | `0x0303` | 4 | server and client | `O` |
| Thermostat | `0x0301` | 7 | client | `O` |
| PumpController | `0x0304` | 5 | client | `O` |
| EnergyEvse | `0x050C` | 2 | server | `O` |

SolarPower `0x0017` revision 1 and BatteryStorage `0x0018` revision 2 include device type TemperatureSensor (`id` 770) with conformance `O`. They do not name cluster `0x0402` on the parent requirement list. See Uncertainty.

Generated attributes are read, privilege view (`Access.RW` `"R"`, `Read: spec.PrivilegeView`). Constraint text is the generated `Constraint.Text`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `temperature`, int16. Unit field: not in the generated definition. Hand-written scale: 0.01 °C (see header). | `M` | TemperatureSensor `0x0302` only | partial: the 13 quantity facts in the list under this table. Also none in catalog: `pv.temperature.sensor`, `thermal.measurement.circuit_return_temperature`, `thermal.measurement.collector_temperature`, `thermal.measurement.dew_point`, `thermal.measurement.exhaust_air_temperature`, `thermal.measurement.extract_air_temperature`, `thermal.measurement.outdoor_air_temperature_average`, `thermal.measurement.outdoor_intake_air_temperature`, `thermal.measurement.pump_medium_temperature`, `thermal.measurement.sensor_temperature`, `thermal.measurement.solar_flow_temperature`, `thermal.measurement.solar_return_temperature`, `thermal.measurement.store_bottom_temperature`, `thermal.measurement.store_top_temperature`, `thermal.measurement.supply_air_temperature` | present for the 13; absent for the 15 proposed ids | each of the 13: `unknown` / `matter.unmapped.v1`; proposed ids: `no row` | defined for the 13; no source for the 15 | unit not on the catalog element; subject is one resource and one dimension, not an unbound sensor; aggregation `member`; direction `not_applicable`; catalog has no nullability or range; Matter value is nullable int16 with constraint `minMeasuredValue to maxMeasuredValue`. Not exact | Nullable (`X`), not fixed. `definition_gen.go:42-48`. No default. |
| MinMeasuredValue | attribute | `0x0001` | `temperature`, int16. Same unit situation as MeasuredValue. | `M` | TemperatureSensor `0x0302` only | none in catalog | absent | `no row` | no source | no catalog range element; Matter value is nullable and fixed; constraint `-27315 to 32766` | `definition_gen.go:50-56`. Quality `X F`. |
| MaxMeasuredValue | attribute | `0x0002` | `temperature`, int16. Same unit situation as MeasuredValue. | `M` | TemperatureSensor `0x0302` only | none in catalog | absent | `no row` | no source | no catalog range element; nullable and fixed; constraint `min minMeasuredValue + 1` (no numeric max in the generated constraint) | `definition_gen.go:58-64`. Quality `X F`. |
| Tolerance | attribute | `0x0003` | uint16. No unit field. | `O` | none (conformance `O`) | none in catalog | absent | `no row` | no source | no catalog tolerance element; fixed uint16; constraint `max 2048`; default 0 | `definition_gen.go:66-73`. Quality `F`. Not nullable. |
| ClusterRevision | attribute | `0xFFFD` (65533) | `ClusterRevision`, uint16. No unit. | `M` on `effective.conformance` only. The attribute object has no conformance key. | TemperatureSensor `0x0302` only, because the cluster is `M` there and the effective attribute conformance is `M` | none in catalog | absent | `no row` | no source | revision counter has no catalog element | In `schema.json`, not in `Definition.Attributes`. Effective access read / view, fixed, constraint `min 1`, default 6. `go-fabric@v0.22.2:device/element_names_gen.go:1123`. |

Partial facts for MeasuredValue. Each is `element_kind` `fact`, catalog disposition `member`, `value_kind` `quantity`, aggregation `member`, direction `not_applicable`. Pack versions: pv `1.0.0`, storage `1.1.0`, thermal `1.0.0`.

| element id | version | subject kind | dimension id |
|---|---|---|---|
| `pv.temperature.inverter` | 1.0.0 | `resource.inverter` | `pv.dimension.inverter`; catalog canonical unit `pv.temperature.inverter` `unit.kelvin` |
| `storage.temperature.cell` | 1.1.0 | `resource.battery_cell` | `storage.dimension.cell`; catalog canonical unit `storage.temperature.cell` `unit.kelvin` |
| `storage.temperature.pack` | 1.1.0 | `resource.battery_pack` | `storage.dimension.pack`; catalog canonical unit `storage.temperature.pack` `unit.kelvin` |
| `thermal.measurement.air_temperature` | 1.0.0 | `resource.zone` | `thermal.dimension.zone`; catalog canonical unit `thermal.measurement.air_temperature` `unit.kelvin` |
| `thermal.measurement.circuit_flow_temperature` | 1.0.0 | `resource.thermal_circuit` | `thermal.dimension.circuit`; catalog canonical unit `thermal.measurement.circuit_flow_temperature` `unit.kelvin` |
| `thermal.measurement.dhw_temperature` | 1.0.0 | `resource.domestic_hot_water` | `thermal.dimension.dhw`; catalog canonical unit `thermal.measurement.dhw_temperature` `unit.kelvin` |
| `thermal.measurement.heat_generator_flow_temperature` | 1.0.0 | `resource.heat_generator` | `thermal.dimension.heat_generator`; catalog canonical unit `thermal.measurement.heat_generator_flow_temperature` `unit.kelvin` |
| `thermal.measurement.heat_generator_return_temperature` | 1.0.0 | `resource.heat_generator` | `thermal.dimension.heat_generator`; catalog canonical unit `thermal.measurement.heat_generator_return_temperature` `unit.kelvin` |
| `thermal.measurement.outdoor_air_temperature` | 1.0.0 | `resource.thermal_system` | `thermal.dimension.system`; catalog canonical unit `thermal.measurement.outdoor_air_temperature` `unit.kelvin` |
| `thermal.measurement.refrigerant_condensing_temperature` | 1.0.0 | `resource.refrigerant_circuit` | `thermal.dimension.refrigerant_circuit`; catalog canonical unit `thermal.measurement.refrigerant_condensing_temperature` `unit.kelvin` |
| `thermal.measurement.refrigerant_evaporating_temperature` | 1.0.0 | `resource.refrigerant_circuit` | `thermal.dimension.refrigerant_circuit`; catalog canonical unit `thermal.measurement.refrigerant_evaporating_temperature` `unit.kelvin` |
| `thermal.measurement.store_temperature` | 1.0.0 | `resource.thermal_store` | `thermal.dimension.thermal_store`; catalog canonical unit `thermal.measurement.store_temperature` `unit.kelvin` |
| `thermal.measurement.system_flow_temperature` | 1.0.0 | `resource.thermal_system` | `thermal.dimension.system`; catalog canonical unit `thermal.measurement.system_flow_temperature` `unit.kelvin` |

`storage.temperature.cell` is in the catalog and is not in the a prior accounting MeasuredValue list. See Disagreements.

Setpoint facts are not listed as feeders. A setpoint is not a measured value. They are in the section "Catalog elements of this domain without a Matter element".

## PressureMeasurement `0x0403`

Revision 5. `definition_gen.go:19-22` and `schema.json:106437`. Commands: none. Events: none. One feature bit.

Server conformance `M` on device type PressureSensor only (`0x0305`). Other requirements, not mandatory:

| Device type | Id | Revision | Side | Conformance |
|---|---|---|---|---|
| Pump | `0x0303` | 4 | server and client | `O` |
| PumpController | `0x0304` | 5 | client | `O` |

Generated attributes are read, privilege view, except where a row says the declaration is effective-only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | int16. Unit field: not in the generated definition. Hand-written scale: 0.1 kPa step, model unit the file uses is hPa (see header).; catalog canonical unit `thermal.measurement.refrigerant_high_side_pressure` `unit.pascal`, `thermal.measurement.refrigerant_low_side_pressure` `unit.pascal`, `thermal.measurement.water_pressure` `unit.pascal` | `M` | PressureSensor `0x0305` only | partial: `thermal.measurement.refrigerant_high_side_pressure` 1.0.0, `thermal.measurement.refrigerant_low_side_pressure` 1.0.0, `thermal.measurement.water_pressure` 1.0.0. Also none in catalog: `thermal.measurement.circuit_water_pressure`, `thermal.measurement.pump_pressure`, `thermal.measurement.system_water_pressure` | present for the 3; absent for the 3 proposed ids | each of the 3: `unknown` / `matter.unmapped.v1`; proposed ids: `no row` | defined for the 3; no source for the 3 | same gaps as temperature MeasuredValue (no unit on the element, subject-bound, aggregation `member`, direction `not_applicable`, nullable int16). Constraint `minMeasuredValue to maxMeasuredValue` | `definition_gen.go:55-61`. Quality nullable. Subjects under this table. |
| MinMeasuredValue | attribute | `0x0001` | int16. Same unit situation as MeasuredValue. | `M` | PressureSensor `0x0305` only | none in catalog | absent | `no row` | no source | no catalog range element; nullable and fixed; constraint `max 32766` | `definition_gen.go:63-69`. Quality `X F`. |
| MaxMeasuredValue | attribute | `0x0002` | int16. Same unit situation as MeasuredValue. | `M` | PressureSensor `0x0305` only | none in catalog | absent | `no row` | no source | no catalog range element; nullable and fixed; constraint `minMeasuredValue + 1 to 32767` | `definition_gen.go:71-77`. Quality `X F`. |
| Tolerance | attribute | `0x0003` | uint16. No unit field. | `O` | none | none in catalog | absent | `no row` | no source | no catalog tolerance element; fixed; constraint `max 2048`; default 0 | `definition_gen.go:79-86`. Quality `F`. |
| ScaledValue | attribute | `0x0010` | int16. No unit field. | `EXT` | none (feature conformance, and feature `EXT` is `O`; PressureSensor does not require the feature) | none in catalog | absent | `no row` | no source | no catalog element; nullable int16; constraint `minScaledValue to maxScaledValue` | `definition_gen.go:88-94`. `PressureServer.MatterRead` has no case for this id (`measurement.go:569-597`). |
| MinScaledValue | attribute | `0x0011` | int16. No unit field. | `EXT` | none | none in catalog | absent | `no row` | no source | no catalog element; nullable and fixed; constraint `max 32766` | `definition_gen.go:96-102`. Quality `X F`. Not read by `PressureServer.MatterRead`. |
| MaxScaledValue | attribute | `0x0012` | int16. No unit field. | `EXT` | none | none in catalog | absent | `no row` | no source | no catalog element; nullable and fixed; constraint `minScaledValue + 1 to 32767` | `definition_gen.go:104-110`. Quality `X F`. Not read by `PressureServer.MatterRead`. |
| ScaledTolerance | attribute | `0x0013` | uint16. No unit field. | `[EXT]` | none | none in catalog | absent | `no row` | no source | no catalog element; fixed; constraint `max 2048`; default 0 | `definition_gen.go:112-119`. `ConfOptionalIf` of name `EXT`. Not read by `PressureServer.MatterRead`. |
| Scale | attribute | `0x0014` | int8. No unit field. | `EXT` | none | none in catalog | absent | `no row` | no source | no catalog element; fixed int8; constraint `min -127`; no default in the definition | `definition_gen.go:121-127`. Not read by `PressureServer.MatterRead`. |
| EXT | feature | bit 0 | bitmap bit. Code constant `FeatureExtended = 1 << 0`. Title `Extended`. | `O` | none | none in catalog | absent | `no row` | no source | feature bit has no catalog element | `definition_gen.go:44-46` and `51-53`. Cluster `featureMap` value in `schema.json` is 0. |
| FeatureMap | attribute | `0xFFFC` (65532) | `FeatureMap`, uint32. No unit. | `M` on `effective.conformance` only. The attribute object has no conformance key. | PressureSensor `0x0305` only | none in catalog | absent | `no row` | no source | bitmap has no catalog element | In `schema.json` and `go-fabric@v0.22.2:device/element_names_gen.go:1135`. Not in `Definition.Attributes`. Effective access read / view, fixed. No default on the attribute. |
| ClusterRevision | attribute | `0xFFFD` (65533) | `ClusterRevision`, uint16. No unit. | `M` on `effective.conformance` only | PressureSensor `0x0305` only | none in catalog | absent | `no row` | no source | revision counter has no catalog element | Effective access read / view, fixed, constraint `min 1`, default 5. `go-fabric@v0.22.2:device/element_names_gen.go:1136`. |

Partial pressure facts. Each is a member quantity fact, aggregation `member`, direction `not_applicable`, pack `helianthus.pack.thermal` `1.0.0`.

| element id | subject kind | dimension id |
|---|---|---|
| `thermal.measurement.refrigerant_high_side_pressure` | `resource.refrigerant_circuit` | `thermal.dimension.refrigerant_circuit`; catalog canonical unit `thermal.measurement.refrigerant_high_side_pressure` `unit.pascal` |
| `thermal.measurement.refrigerant_low_side_pressure` | `resource.refrigerant_circuit` | `thermal.dimension.refrigerant_circuit`; catalog canonical unit `thermal.measurement.refrigerant_low_side_pressure` `unit.pascal` |
| `thermal.measurement.water_pressure` | `resource.heat_generator` | `thermal.dimension.heat_generator`; catalog canonical unit `thermal.measurement.water_pressure` `unit.pascal` |

`thermal.measurement.water_pressure` locator: `api/v1/element-catalog-v1.json:13360`. The record does not state a medium and does not state pascal.

## FlowMeasurement `0x0404`

Revision 5. `definition_gen.go:19-22` and `schema.json:106842`. Commands: none. Events: none. Feature bits: none (`features` `[]`; `type Feature uint32` with no bit constants, `definition_gen.go:33-36`). `Definition.Attributes` omits ClusterRevision. `go-fabric@v0.22.2:device/element_names_gen.go:1138-1143` lists ClusterRevision and no FeatureMap.

Server conformance `M` on device type FlowSensor only (`0x0306`). Other requirements, not mandatory:

| Device type | Id | Revision | Side | Conformance |
|---|---|---|---|---|
| IrrigationSystem | `0x0040` | 1 | server and client | `O` |
| WaterValve | `0x0042` | 1 | server and client | `O` |
| Pump | `0x0303` | 4 | server and client | `O` |
| PumpController | `0x0304` | 5 | client | `O` |

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | uint16. Unit field: not in the generated definition. Hand-written scale: 0.1 m³/h step (see header).; catalog canonical unit `thermal.measurement.flow_rate` `unit.cubic_metre_per_second` | `M` | FlowSensor `0x0306` only | partial: `thermal.measurement.flow_rate` 1.0.0. Also none in catalog: `thermal.measurement.dhw_flow_rate`, `thermal.measurement.extract_air_flow`, `thermal.measurement.heat_generator_flow_rate`, `thermal.measurement.pump_flow_rate`, `thermal.measurement.supply_air_flow`, `thermal.measurement.valve_flow_rate` | present for `thermal.measurement.flow_rate`; absent for the 6 proposed ids | `unknown` / `matter.unmapped.v1` for the present fact; proposed ids: `no row` | defined for the present fact; no source for the 6 | unit not on the catalog element; subject `resource.thermal_circuit` / `thermal.dimension.circuit`; aggregation `member`; direction `non_negative` (the Matter type is uint16); nullable; constraint `minMeasuredValue to maxMeasuredValue`. Not exact | `definition_gen.go:42-48`. Quality nullable. Catalog line `api/v1/element-catalog-v1.json:12718`. The catalog record does not name a fluid. |
| MinMeasuredValue | attribute | `0x0001` | uint16. Same unit situation as MeasuredValue. | `M` | FlowSensor `0x0306` only | none in catalog | absent | `no row` | no source | no catalog range element; nullable and fixed; constraint `max 65533` | `definition_gen.go:50-56`. Quality `X F`. |
| MaxMeasuredValue | attribute | `0x0002` | uint16. Same unit situation as MeasuredValue. | `M` | FlowSensor `0x0306` only | none in catalog | absent | `no row` | no source | no catalog range element; nullable and fixed; constraint `min minMeasuredValue + 1` (no numeric max in the generated constraint) | `definition_gen.go:58-64`. Quality `X F`. |
| Tolerance | attribute | `0x0003` | uint16. No unit field. | `O` | none | none in catalog | absent | `no row` | no source | no catalog tolerance element; fixed; constraint `max 2048`; default 0 | `definition_gen.go:66-73`. Quality `F`. |
| ClusterRevision | attribute | `0xFFFD` (65533) | `ClusterRevision`, uint16. No unit. | `M` on `effective.conformance` only | FlowSensor `0x0306` only | none in catalog | absent | `no row` | no source | revision counter has no catalog element | Effective access read / view, fixed, constraint `min 1`, default 5. `go-fabric@v0.22.2:device/element_names_gen.go:1143`. |

## RelativeHumidityMeasurement `0x0405`

Revision 5. `definition_gen.go:19-22` and `schema.json:107026`. Commands: none. Events: none. Feature bits: none (`features` `[]`; `type Feature uint32` with no bit constants). `Definition.Attributes` omits ClusterRevision. `go-fabric@v0.22.2:device/element_names_gen.go:1145-1150` lists ClusterRevision and no FeatureMap.

Server conformance `M` on device type HumiditySensor only (`0x0307`). Other requirements, not mandatory:

| Device type | Id | Revision | Side | Conformance |
|---|---|---|---|---|
| AirQualitySensor | `0x002C` | 1 | server | `O` |
| RoomAirConditioner | `0x0072` | 4 | server | `O` |
| SmokeCoAlarm | `0x0076` | 2 | server | `O` |
| Thermostat | `0x0301` | 7 | client | `O` |

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | uint16. Unit field: not in the generated definition. Hand-written scale: 0.01 percent step (see header).; catalog canonical unit `thermal.measurement.humidity` `unit.ratio` | `M` | HumiditySensor `0x0307` only | partial: `thermal.measurement.humidity` 1.0.0. Also none in catalog: `thermal.measurement.circuit_humidity`, `thermal.measurement.sensor_humidity`, `thermal.measurement.terminal_unit_humidity` | present for `thermal.measurement.humidity`; absent for the 3 proposed ids | `unknown` / `matter.unmapped.v1` for the present fact; proposed ids: `no row` | defined for the present fact; no source for the 3 | unit not on the catalog element; subject `resource.zone` / `thermal.dimension.zone`; aggregation `member`; direction `not_applicable`; nullable uint16; constraint `minMeasuredValue to maxMeasuredValue`. Not exact | `definition_gen.go:42-48`. Catalog line `api/v1/element-catalog-v1.json:12853`. |
| MinMeasuredValue | attribute | `0x0001` | uint16. Same unit situation as MeasuredValue. | `M` | HumiditySensor `0x0307` only | none in catalog | absent | `no row` | no source | no catalog range element; nullable and fixed; constraint `max 9999` | `definition_gen.go:50-56`. Quality `X F`. |
| MaxMeasuredValue | attribute | `0x0002` | uint16. Same unit situation as MeasuredValue. | `M` | HumiditySensor `0x0307` only | none in catalog | absent | `no row` | no source | no catalog range element; nullable and fixed; constraint `minMeasuredValue + 1 to 10000` | `definition_gen.go:58-64`. Quality `X F`. |
| Tolerance | attribute | `0x0003` | uint16. No unit field. | `O` | none | none in catalog | absent | `no row` | no source | no catalog tolerance element; fixed; constraint `max 2048`; no default key in `schema.json` or `definition_gen.go` | `definition_gen.go:66-72`. The other three clusters in this group set Tolerance default 0. This one does not. |
| ClusterRevision | attribute | `0xFFFD` (65533) | `ClusterRevision`, uint16. No unit. | `M` on `effective.conformance` only | HumiditySensor `0x0307` only | none in catalog | absent | `no row` | no source | revision counter has no catalog element | Effective access read / view, fixed, constraint `min 1`, default 5. `go-fabric@v0.22.2:device/element_names_gen.go:1150`. |

## Mandatory elements without a source

Scope: elements of these four clusters whose conformance makes them mandatory on a device type of this group, and whose source status is `no source`. MeasuredValue on each cluster has at least one partial catalog fact, so it is `defined` and is not listed. Tolerance and the pressure `EXT` / `[EXT]` elements are not mandatory. Identify is mandatory on the device files and is outside this cluster group.

| Cluster | Element | Id | Device type | Why there is no source |
|---|---|---|---|---|
| TemperatureMeasurement | MinMeasuredValue | `0x0001` | TemperatureSensor `0x0302` | no catalog element |
| TemperatureMeasurement | MaxMeasuredValue | `0x0002` | TemperatureSensor `0x0302` | no catalog element |
| TemperatureMeasurement | ClusterRevision | `0xFFFD` | TemperatureSensor `0x0302` | no catalog element; declared in `schema.json` effective conformance `M`, not in `Definition.Attributes` |
| PressureMeasurement | MinMeasuredValue | `0x0001` | PressureSensor `0x0305` | no catalog element |
| PressureMeasurement | MaxMeasuredValue | `0x0002` | PressureSensor `0x0305` | no catalog element |
| PressureMeasurement | FeatureMap | `0xFFFC` | PressureSensor `0x0305` | no catalog element; effective conformance `M` |
| PressureMeasurement | ClusterRevision | `0xFFFD` | PressureSensor `0x0305` | no catalog element; effective conformance `M` |
| FlowMeasurement | MinMeasuredValue | `0x0001` | FlowSensor `0x0306` | no catalog element |
| FlowMeasurement | MaxMeasuredValue | `0x0002` | FlowSensor `0x0306` | no catalog element |
| FlowMeasurement | ClusterRevision | `0xFFFD` | FlowSensor `0x0306` | no catalog element; effective conformance `M` |
| RelativeHumidityMeasurement | MinMeasuredValue | `0x0001` | HumiditySensor `0x0307` | no catalog element |
| RelativeHumidityMeasurement | MaxMeasuredValue | `0x0002` | HumiditySensor `0x0307` | no catalog element |
| RelativeHumidityMeasurement | ClusterRevision | `0xFFFD` | HumiditySensor `0x0307` | no catalog element; effective conformance `M` |

Count: 13.

## Catalog elements of this domain without a Matter element

These catalog elements name a temperature measurement quantity class only through a setpoint, a set operation, or a presentation of that operation. None of the four clusters declares a setpoint attribute or any command (`commands` `[]` on each). They are not feeders of MeasuredValue.

| element id | version | kind | catalog disposition | subject | target row | locator note |
|---|---|---|---|---|---|---|
| `thermal.setpoint.temperature_setpoint` | 1.0.0 | fact, `value_kind` quantity, aggregation `not_applicable`, direction `not_applicable` | member | `resource.zone` / `thermal.dimension.zone` | `unknown` / `matter.unmapped.v1` | no unit field; catalog canonical unit `thermal.setpoint.temperature_setpoint` `unit.kelvin` |
| `thermal.setpoint.dhw_temperature_setpoint` | 1.0.0 | fact, `value_kind` quantity, aggregation `not_applicable`, direction `not_applicable` | member | `resource.domestic_hot_water` / `thermal.dimension.dhw` | `unknown` / `matter.unmapped.v1` | no unit field; catalog canonical unit `thermal.setpoint.dhw_temperature_setpoint` `unit.kelvin` |
| `thermal.capability.set_temperature` | 1.0.0 | capability | member | service `thermal.service.zone` 1.0.0; operation `thermal.operation.set_temperature` 1.0.0 | `unknown` / `matter.unmapped.v1` | planes physical, energy, hydraulic, control |
| `thermal.operation.set_temperature` | 1.0.0 | operation | member | argument `thermal.setpoint.temperature_setpoint`; effect `thermal.effect.set_temperature` | `unknown` / `matter.unmapped.v1` | these clusters have no commands; catalog canonical unit `thermal.setpoint.temperature_setpoint` `unit.kelvin` |
| `thermal.effect.set_temperature` | 1.0.0 | effect_rule | member | operation and fact as the capability/operation pair above | `no row` | target `scope.not_requested` includes effect rules (`matter-1.6.1-v1.json:27`) |
| `thermal.portal.operation.set_temperature` | 1.0.0 | presentation | unsupported | attribute `target` `portal` | `no row` | presentations are in `scope.not_requested` |

The 18 measurement facts in the cluster tables are partial feeders of a MeasuredValue, so they are not repeated here.

`resource.sensor`, `thermal.dimension.sensor` and `thermal.service.sensor` are not catalog elements. The a prior accounting device-type rows propose them (below). They are not listed here because this section is catalog elements.

## Disagreements with the prior accounting

a prior accounting: `a prior accounting` line 3 says the Matter tables cover each attribute, command, event and feature, from go-fabric v0.22.2. Checked against `definition_gen.go` and `go-fabric@v0.22.2:parity/schema.json` at that module.

Claims that match those sources, so they are not disagreements: cluster ids and revisions (`0x0402` rev 6, `0x0403` rev 5, `0x0404` rev 5, `0x0405` rev 5); the attribute ids and conformance texts the tables do list (`M`, `O`, `EXT`, `[EXT]`); feature `EXT` bit 0 conformance `O`; empty command and event sets; access `R` in the prior accounting's own legend (line 3: R means read) against generated access `"R"` / view.

Disagreements:

1. The four cluster tables do not list ClusterRevision `0xFFFD`. The pressure table does not list FeatureMap `0xFFFC`. `schema.json` includes both, with effective conformance `M`, and `go-fabric@v0.22.2:device/element_names_gen.go:1118-1150` names them. `definition_gen.go` `Attributes` omits both. The prior accounting matches the generated `Attributes` slice and does not match the schema attribute list. Line 3's claim to list every attribute is not met by the schema attribute list.
2. Temperature MeasuredValue (`a prior accounting:707`) names 15 ids that are absent from the catalog at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:` and from the semreg fixture catalog. They are proposals of tickets a prior proposal, a prior proposal, a prior proposal, a prior proposal, a prior proposal and a prior proposal, not catalog elements. The same row also names ids that are in the catalog. One row status, `planned`, covers both. For the ids that exist, the target row is `unknown` / `matter.unmapped.v1`, which is not a completed target row. The prior accounting's `present` status (line 3: already on main, with the target row finished by the ticket) is not met either.
3. `storage.temperature.cell` 1.1.0 is a catalog quantity fact (`api/v1/element-catalog-v1.json:11375`) and is not in the prior accounting MeasuredValue list. `a prior accounting` a prior claim (line 114) names it. The a prior accounting omits it.
4. MinMeasuredValue and MaxMeasuredValue on all four clusters are `absent` in the prior accounting, with the reason that the binding derives them from field bounds of the mapped fact (lines 706, 708, 715, 718, 730, 732, 739, 741). The catalog facts in this domain have no bounds, min, max, or range field. These sources do not show field bounds to derive.
5. Pressure ScaledValue (`a prior accounting:722`) says SemReg decimals in pascal carry any scale. The three pressure facts in the catalog have no unit field and do not say pascal or a decimal scale. `a prior accounting` a prior claim (line 120) says the same. The catalog does not support that sentence.
6. `a prior accounting` a prior claim (line 121) calls `thermal.measurement.flow_rate` water on the circuit dimension. The catalog record is subject `resource.thermal_circuit`, dimension `thermal.dimension.circuit`, direction `non_negative`. It does not say water. The circuit dimension and the element id match the audit; the medium does not appear in the record.

Checked and not a contradiction of the prior accounting's `planned` status: device-type rows TemperatureSensor (`a prior accounting:1060`) proposes `resource.sensor`, `thermal.dimension.sensor`, `thermal.service.sensor` (a prior proposal); HumiditySensor (`a prior accounting:1056`) proposes `resource.sensor` (a prior proposal). All three ids are absent from both catalogs. `a prior accounting` a prior claim's statement that Temperature Sensor is optional on Solar Power and Battery Storage matches schema device-type requirements: SolarPower `0x0017` and BatteryStorage `0x0018` include device type TemperatureSensor with conformance `O`.

`a prior accounting` lines 102–121 split several of these facts into fed-not-published and defined-not-fed. Driver feed is not visible in the sources of this job, so that split is not confirmed and not contradicted here. Source status in the tables is `defined` or `no source` only.

## Uncertainty

1. Unit of each catalog quantity fact. The element record has no unit field. the registry unit rule item 3 says the registry uses SI units. That sentence does not name the unit of these facts. This note does not convert a fact to kelvin, pascal, or any other unit from that sentence. The go-fabric wire scales are statements of the hand-written servers, and the Matter clause numbers they cite were not read as specification text.
2. Whether Descriptor `0x001D` with no conformance field is mandatory on the four sensor device types. The device `Servers` slices omit it. `schema.json` requirements include it. `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` also includes it, with a nested DeviceTypeList attribute. Which list a device must implement is not decided here.
3. SolarPower and BatteryStorage optional TemperatureSensor. The parent `effective.requirements` under that device type list Descriptor and feature `TAGLIST`, and do not repeat TemperatureMeasurement. The TemperatureSensor device type's own requirements include TemperatureMeasurement conformance `M`. This note does not decide whether the optional device-type requirement composes that cluster.
4. Tolerance on RelativeHumidityMeasurement has no default. The other three Tolerance attributes default to 0. No source here says whether the missing default is intentional.
5. `PressureServer.MatterRead` (`measurement.go:569-597`) does not handle ScaledValue, MinScaledValue, MaxScaledValue, ScaledTolerance, or Scale. The generated definition does declare them. The server's silence is not a statement that the attributes are absent from the cluster.
6. Min/Max numeric ends that the hand-written servers return (temperature -27315 and 32766, pressure 0 and 32766, flow 0 and 65534, humidity 0 and 10000) are server choices. The generated constraints are the wider texts in the tables. Those server constants are not catalog elements and are not recorded as Matter mandates beyond the constraint texts.
7. Heating and cooling setpoint ids `thermal.setpoint.occupied_heating`, `thermal.setpoint.occupied_cooling`, `thermal.setpoint.unoccupied_heating`, `thermal.setpoint.unoccupied_cooling` (each 1.0.0, quantity, subject `resource.zone` / `thermal.dimension.zone`) have no unit field. The ids do not say temperature. They have target rows `unknown` / `matter.unmapped.v1`. Whether they belong to this measurement domain is not stated by the catalog. The docs-semantic and semreg copies of `thermal.setpoint.occupied_heating` differ in `admission.evidence` (a blob URL versus a pinned SHA URL). The other three of this set were not field-compared.
8. Kernel measurement-tolerance primitive. `a prior accounting` a prior claim says tolerance is partial via kernel uncertainty primitives and marks that as not verified. The catalog facts in this domain have no uncertainty attribute. semreg `README.md:208` at the frozen SHA uses "uncertainty" for restart-time evaluation of a snapshot, which is not a sensor tolerance. A measurement-tolerance type in the semreg kernel was not established.
9. Target document row count, unresolved. `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json` `rows` has 246 entries and one disposition `transformed`. `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md` states 177 rows and that only `evse.ac.current` is `transformed`. This note keeps both counts and does not resolve them.
10. Identify, Descriptor, and ThermostatUserInterfaceConfiguration on these device types were not given cluster tables. Their mandatory elements, if any, are outside the named clusters.
