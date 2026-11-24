---
status: "research notes for Matter 1.6.1 water and hydraulics clusters; no mapping is decided and no canonical target is written."
---

# Water and hydraulics

Matter 1.6.1 cluster accounting for Water and hydraulics. Identifiers, conformance, types and units are read from go-fabric@v0.22.2:parity/schema.json (revision 1.6.1, data model revision 21) and the generated cluster and device files cited below. Catalog elements are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json and semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json. Canonical units are the `canonical_unit` field of docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json. Target rows are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json and docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md. No mapping is chosen. No grade in this note is `exact`. Charge capacity stays `unit.ampere_hour` where the catalog defines it; `storage.capacity.remaining` and `storage.capacity.full_charge` are absent from the pinned catalog. A catalog canonical unit is written beside the Matter unit on each element row that names a catalog field.

Read-only source accounting for WaterHeaterManagement, WaterHeaterMode, PumpConfigurationAndControl, ValveConfigurationAndControl, BooleanState, BooleanStateConfiguration, WaterTankLevelMonitoring, OnOff and LevelControl. No mapping is decided here.

## Header

- Queue row QQ04: the research row, text `TARGET-MAT-R read-only source accounting by cluster; no canonical JSON writer here`.
- docs-semantic frozen SHA `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:` (checked with `git rev-parse HEAD` on that view).
- semreg frozen SHA `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:` (checked the same way).
- go-fabric v0.22.2. `README.md` line 17 states that this module implements Matter, currently 1.6.1. Each `definition_gen.go` header in this group states the matter.js model at `a commit id recorded in the cited file` (Matter 1.6.1). `go-fabric@v0.22.2:parity/schema.json` `matter.revision` is `1.6.1` and `matter.sourceCommit` is `a commit id recorded in the cited file`.
- The Matter 1.6.1 target JSON `model_source.tag` is `v0.13.12` (`api/v1/targets/matter-1.6.1-v1.json` at the docs-semantic SHA). `model_source.inspection_basis` says the upstream source was not independently replayed. This accounting reads cluster definitions from go-fabric v0.22.2. The two tags were not diffed.

### Files read

- go-fabric v0.22.2: `README.md` lines 14-19; `go-fabric@v0.22.2:device/water_heater_gen.go`, `go-fabric@v0.22.2:device/pump_gen.go`, `go-fabric@v0.22.2:device/pump_controller_gen.go`, `go-fabric@v0.22.2:device/water_valve_gen.go`, `go-fabric@v0.22.2:device/water_freeze_detector_gen.go`, `go-fabric@v0.22.2:device/water_leak_detector_gen.go`; a scan of every `device/*_gen.go` for these nine cluster ids; `cluster/spec/{waterheatermanagement,waterheatermode,pumpconfigurationandcontrol,valveconfigurationandcontrol,booleanstate,booleanstateconfiguration,watertanklevelmonitoring,onoff,levelcontrol}/definition_gen.go`; `go-fabric@v0.22.2:parity/schema.json` cluster objects for those nine names (attribute, command, event and feature counts, type strings, and the `FeatureMap` / `ClusterRevision` effective conformance).
- docs-semantic at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`: `api/v1/element-catalog-v1.json` (394 elements); `api/v1/targets/matter-1.6.1-v1.json` (246 rows). `tests/test_matter161_target.py` and `api/v1/targets/matter-1.6.1-v1.md` do not name these clusters.
- semreg at `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:`: `fixtures/v1/element-catalog-v1.json` (394 elements, same ids). Element bodies differ from the docs-semantic catalog in 20 elements, and only in `admission.evidence`. Attributes, kind and disposition match. The docs-semantic evidence path uses an unpinned evidence path; the semreg evidence path pins blob `a commit id recorded in the cited file`. Eight ids cited below are in that set: `resource.pump`, `thermal.dimension.pump`, `thermal.measurement.pump_speed`, `thermal.measurement.valve_position`, `thermal.overrun.one_time_dhw`, `thermal.overrun.valve_kick`, `thermal.portal.read.pump`, `thermal.service.pump`. The other twelve are `thermal.overrun.hvac_system_off`, `thermal.overrun.one_day_at_home`, `thermal.overrun.one_day_away`, `thermal.overrun.one_time_ventilation`, `thermal.overrun.party`, `thermal.overrun.sg_ready_condition_1`, `thermal.overrun.sg_ready_condition_3`, `thermal.overrun.sg_ready_condition_4`, `thermal.setpoint.occupied_cooling`, `thermal.setpoint.occupied_heating`, `thermal.setpoint.unoccupied_cooling`, `thermal.setpoint.unoccupied_heating`.
- Rows were located in `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`, `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`. Dispositions below are from the target JSON. The target TSV is a comment line, a header, and 246 data rows with the same element ids as the JSON.
- Prior claims were checked against a prior accounting (Matter sections for these nine clusters, lines 10-58, 173-179, 221-278, 329-344, 491-501, 525-576); a prior accounting lines 124-181 and 300-309.

### How a row was filled

- Cluster tables follow `Definition` in each `definition_gen.go`. `go-fabric@v0.22.2:parity/schema.json` lists the same attributes plus `FeatureMap` id 65532 and `ClusterRevision` id 65533 on all nine clusters. On each of the nine, `effective.conformance.text` for both is `M`, and the `ClusterRevision` default equals that cluster's revision. Those two are not in `Definition.Attributes` and are not rows below.
- Conformance text is the generated `Conformance.Text`.
- `mandatory for which device types` uses the six device types of this group. A row is mandatory when that device file requires the cluster (server or client) and the element's conformance text is `M`, or the device file forces the feature or sets `PresenceMandatory`, or the device file sets no OnOff features and the conformance text is `!OFFONLY` (On and Toggle). `none` means no device type in this group requires it. Optional clusters keep `none` even where the element's own conformance is `M`. Other device files that also require BooleanState, OnOff or LevelControl are outside this column; see Uncertainty.
- A SemReg id is cited only from `api/v1/element-catalog-v1.json` at the docs-semantic SHA. `exact` would require meaning, kind and unit to correspond. No row in this group is `exact`: every catalog fact's attribute object has `value_kind`, `subject`, `aggregation` and `direction` (some also `sign_reference`) and no unit field, and none of the 39 symbol facts has a `values` list. `partial` is a quantity whose subject is the same device family, with the gaps in `loss`. `candidate` is name proximity only. An id that appears only in the a prior accounting is `none in catalog (proposed by <ticket>)`.
- Catalog status `present` / `absent` is membership of that id at the docs-semantic SHA. Target disposition is that element's row in `matter-1.6.1-v1.json`, or `no row`.
- `source status` is `defined` when at least one cited id is in the catalog, and `no source` when none is. Whether a driver feeds an element is not in these sources.
- `loss` is `no correspondence` when source status is `no source`. `none` is unused in this group because no correspondence is exact.

## Device types

All six are `Classification: simple`, `Composition: schema.CompositionTree`. Clusters named here that are outside the nine are listed so the device file is complete, and they are not given element tables.

### WaterHeater

- Id `0x050F`, revision 1. `go-fabric@v0.22.2:device/water_heater_gen.go` lines 16-18 and 29-31.
- Server `WaterHeaterManagement` `0x0094`, conformance `M`, `Mandatory: true` (lines 33-37).
- Server `WaterHeaterMode` `0x009E`, conformance `M`, `Mandatory: true` (lines 38-42).
- Server `Thermostat` `0x0201`, conformance `M`, `Mandatory: true`, `Features: 0x1`, `FeatureNames: HEAT` (lines 43-48). Outside this group.
- Server `Identify` `0x0003`, conformance `O` (lines 49-52). Outside this group.
- No client clusters in this file.

### Pump

- Id `0x0303`, revision 4. `go-fabric@v0.22.2:device/pump_gen.go` lines 21-24 and 34-36.
- Servers: `Identify` `0x0003` `M` (lines 38-42); `OnOff` `0x0006` `M` (lines 43-47); `PumpConfigurationAndControl` `0x0200` `M` (lines 48-52); `Groups` `0x0004` `O` (lines 53-56); `LevelControl` `0x0008` `O` (lines 57-60); `ScenesManagement` `0x0062` `O` (lines 61-64); `TemperatureMeasurement` `0x0402` `O` (lines 65-68); `PressureMeasurement` `0x0403` `O` (lines 69-72); `FlowMeasurement` `0x0404` `O` (lines 73-76).
- Clients, all conformance `O`: `TemperatureMeasurement` `0x0402`, `PressureMeasurement` `0x0403`, `FlowMeasurement` `0x0404`, `OccupancySensing` `0x0406` (lines 78-91).

### PumpController

- Id `0x0304`, revision 5. `go-fabric@v0.22.2:device/pump_controller_gen.go` lines 14-17 and 27-29.
- Servers: `Identify` `0x0003` `M` (lines 31-35); `Binding` `0x001E`, conformance `Simple & Client`, `Mandatory: true`, `BaseMandated: true` (lines 36-41). Both outside this group.
- Clients: `OnOff` `0x0006` `M` (lines 43-47); `PumpConfigurationAndControl` `0x0200` `M` (lines 48-51); `Identify` `0x0003` `O`; `Groups` `0x0004` `O`; `LevelControl` `0x0008` `O`; `ScenesManagement` `0x0062` `O`; `TemperatureMeasurement` `0x0402` `O`; `PressureMeasurement` `0x0403` `O`; `FlowMeasurement` `0x0404` `O` (lines 52-73).
- The file does not repeat element requirements on the client clusters. Mandatory client rows below use the cluster element's own conformance.

### WaterValve

- Id `0x0042`, revision 1. `go-fabric@v0.22.2:device/water_valve_gen.go` lines 15-18 and 28-30.
- Servers: `Identify` `0x0003` `M` (lines 32-36); `ValveConfigurationAndControl` `0x0081` `M` (lines 37-41); `FlowMeasurement` `0x0404` `O` (lines 42-45).
- Client: `FlowMeasurement` `0x0404` `O` (lines 47-51).

### WaterFreezeDetector

- Id `0x0041`, revision 2. `go-fabric@v0.22.2:device/water_freeze_detector_gen.go` lines 15-18 and 28-30.
- Servers: `Identify` `0x0003` `M` (lines 32-36); `BooleanState` `0x0045` `M`, `Features: 0x1`, `FeatureNames: CHGEVENT`, element event `StateChange` id `0x0000` `PresenceMandatory` (lines 37-45); `BooleanStateConfiguration` `0x0080` `O` (lines 46-49).

### WaterLeakDetector

- Id `0x0043`, revision 2. `go-fabric@v0.22.2:device/water_leak_detector_gen.go` lines 15-18 and 28-30.
- Servers match WaterFreezeDetector: `Identify` `M` (lines 32-36); `BooleanState` `M` with `CHGEVENT` and `StateChange` `PresenceMandatory` (lines 37-45); `BooleanStateConfiguration` `O` (lines 46-49).

WaterTankLevelMonitoring is not declared on any of these six device files.

## Clusters

### WaterHeaterManagement

Cluster id `0x0094`, name `WaterHeaterManagement`, revision 2. `go-fabric@v0.22.2:cluster/spec/waterheatermanagement/definition_gen.go` lines 22-26. `Definition` at line 226. No base cluster. Mandatory for WaterHeater server.

Bitmap `WaterHeaterHeatSourceBitmap` map8, all members conformance `M`: `ImmersionElement1` bit 0, `ImmersionElement2` bit 1, `HeatPump` bit 2, `Boiler` bit 3, `Other` bit 4 (lines 132-148).

`BoostStateEnum` enum8: `Inactive` 0 `M`, `Active` 1 `M` (lines 67-77).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EM | feature | bit 0 | feature bit, title EnergyManagement | O | none | none in catalog: thermal.dhw.estimated_heat_required | absent: thermal.dhw.estimated_heat_required | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/waterheatermanagement/definition_gen.go:229 |
| TP | feature | bit 1 | feature bit, title TankPercent | O | none | none in catalog: thermal.dhw.charge_ratio | absent: thermal.dhw.charge_ratio | no row | no source | no correspondence | definition_gen.go:230 |
| HeaterTypes | attribute | 0x0000 | WaterHeaterHeatSourceBitmap map8; fixed | M | WaterHeater server | none in catalog: thermal.dhw.heater_types | absent: thermal.dhw.heater_types | no row | no source | no correspondence | access R view; definition_gen.go:233-239 |
| HeatDemand | attribute | 0x0001 | WaterHeaterHeatSourceBitmap map8 | M | WaterHeater server | none in catalog: thermal.dhw.heat_demand | absent: thermal.dhw.heat_demand | no row | no source | no correspondence | access R view; definition_gen.go:240-245 |
| TankVolume | attribute | 0x0002 | uint16; no unit token in the type name | EM | none | none in catalog: thermal.nameplate.store_volume | absent: thermal.nameplate.store_volume | no row | no source | no correspondence | access R view; definition_gen.go:246-251; schema.json type string uint16 |
| EstimatedHeatRequired | attribute | 0x0003 | energy-mWh, int64, min 0 | EM | none | none in catalog: thermal.dhw.estimated_heat_required | absent: thermal.dhw.estimated_heat_required | no row | no source | no correspondence | access R view; definition_gen.go:252-258. thermal.energy.heat_output is a catalog quantity on resource.heat_generator and is not cited as a feed |
| TankPercentage | attribute | 0x0004 | percent, uint8, max 100 | TP | none | none in catalog: thermal.dhw.charge_ratio | absent: thermal.dhw.charge_ratio | no row | no source | no correspondence | access R view; definition_gen.go:259-265 |
| BoostState | attribute | 0x0005 | BoostStateEnum enum8: Inactive 0 M, Active 1 M | M | WaterHeater server | thermal.overrun.one_time_dhw (candidate); none in catalog: thermal.dhw.boost_state | present: thermal.overrun.one_time_dhw; absent: thermal.dhw.boost_state | thermal.overrun.one_time_dhw: unknown / matter.unmapped.v1; thermal.dhw.boost_state: no row | defined | catalog fact is value_kind symbol, subject resource.thermal_system, and has no values list; Matter type is BoostStateEnum Inactive 0 / Active 1, both conformance M; enumeration mapping is not established; subject is the thermal system | access R view; definition_gen.go:266-271. Candidate because the catalog id names a one-time DHW overrun and does not define symbol values |
| Boost | command | 0x00 | request, response status | M | WaterHeater server | none in catalog: thermal.operation.set_dhw_boost | absent: thermal.operation.set_dhw_boost | no row | no source | no correspondence | access R manage, write manage; definition_gen.go:273-283. Field rows follow |
| Boost.BoostInfo | command field | 0 | WaterHeaterBoostInfoStruct | M | WaterHeater server | none in catalog: thermal.dhw.boost_duration, thermal.dhw.boost_emergency, thermal.dhw.boost_one_shot, thermal.dhw.boost_target_ratio, thermal.dhw.boost_target_reheat_ratio, thermal.dhw.boost_temporary_setpoint | absent: thermal.dhw.boost_duration, thermal.dhw.boost_one_shot, thermal.dhw.boost_emergency, thermal.dhw.boost_temporary_setpoint, thermal.dhw.boost_target_ratio, thermal.dhw.boost_target_reheat_ratio | no row | no source | no correspondence | definition_gen.go:280. Struct fields lines 117-123 |
| Boost.BoostInfo.Duration | command field | 0 | elapsed-s, uint32, min 1 | M | WaterHeater server | none in catalog: thermal.dhw.boost_duration | absent: thermal.dhw.boost_duration | no row | no source | no correspondence | definition_gen.go:118 |
| Boost.BoostInfo.OneShot | command field | 1 | bool; default false | [!TP], [TP].a- | none | none in catalog: thermal.dhw.boost_one_shot | absent: thermal.dhw.boost_one_shot | no row | no source | no correspondence | optional if not TP, else choice a at most one with TargetReheat; definition_gen.go:119 |
| Boost.BoostInfo.EmergencyBoost | command field | 2 | bool; default false | O | none | none in catalog: thermal.dhw.boost_emergency | absent: thermal.dhw.boost_emergency | no row | no source | no correspondence | definition_gen.go:120 |
| Boost.BoostInfo.TemporarySetpoint | command field | 3 | temperature, int16, constraint desc | O | none | none in catalog: thermal.dhw.boost_temporary_setpoint | absent: thermal.dhw.boost_temporary_setpoint | no row | no source | no correspondence | definition_gen.go:121. Catalog fact thermal.setpoint.dhw_temperature_setpoint is a standing DHW setpoint quantity with no unit and is not cited as this field's feed |
| Boost.BoostInfo.TargetPercentage | command field | 4 | percent, uint8, max 100 | TargetReheat, [TP] | none | none in catalog: thermal.dhw.boost_target_ratio | absent: thermal.dhw.boost_target_ratio | no row | no source | no correspondence | definition_gen.go:122 |
| Boost.BoostInfo.TargetReheat | command field | 5 | percent, uint8, max targetPercentage | [TP].a- | none | none in catalog: thermal.dhw.boost_target_reheat_ratio | absent: thermal.dhw.boost_target_reheat_ratio | no row | no source | no correspondence | choice a, at most one, optional if TP; definition_gen.go:123 |
| CancelBoost | command | 0x01 | request, response status; empty payload | M | WaterHeater server | none in catalog: thermal.operation.set_dhw_boost | absent: thermal.operation.set_dhw_boost | no row | no source | no correspondence | access R manage, write manage; definition_gen.go:284-290 |
| BoostStarted | event | 0x00 | priority info | M | WaterHeater server | none in catalog: thermal.event.dhw_boost_started | absent: thermal.event.dhw_boost_started | no row | no source | no correspondence | access R view; definition_gen.go:292-301 |
| BoostStarted.BoostInfo | event field | 0 | WaterHeaterBoostInfoStruct | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | same struct as Boost.BoostInfo; definition_gen.go:298 |
| BoostStarted.BoostInfo.Duration | event field | 0 | elapsed-s, uint32, min 1 | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:118 |
| BoostStarted.BoostInfo.OneShot | event field | 1 | bool; default false | [!TP], [TP].a- | none | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:119 |
| BoostStarted.BoostInfo.EmergencyBoost | event field | 2 | bool; default false | O | none | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:120 |
| BoostStarted.BoostInfo.TemporarySetpoint | event field | 3 | temperature, int16, constraint desc | O | none | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:121 |
| BoostStarted.BoostInfo.TargetPercentage | event field | 4 | percent, uint8, max 100 | TargetReheat, [TP] | none | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:122 |
| BoostStarted.BoostInfo.TargetReheat | event field | 5 | percent, uint8, max targetPercentage | [TP].a- | none | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:123 |
| BoostEnded | event | 0x01 | priority info; empty payload | M | WaterHeater server | none in catalog: thermal.event.dhw_boost_ended | absent: thermal.event.dhw_boost_ended | no row | no source | no correspondence | access R view; definition_gen.go:302-306 |

### WaterHeaterMode

Cluster id `0x009E`, name `WaterHeaterMode`, revision 1, base `ModeBase`. `go-fabric@v0.22.2:cluster/spec/waterheatermode/definition_gen.go` lines 22-26 and 244-246. Mandatory for WaterHeater server.

`ModeTag` enum16 values, with no conformance on the values: `Auto` 0, `Quick` 1, `Quiet` 2, `LowNoise` 3, `LowEnergy` 4, `Vacation` 5, `Min` 6, `Max` 7, `Night` 8, `Day` 9, `Off` 16384, `Manual` 16385, `Timed` 16386. Range `MfgTags` 32768-49151 (lines 147-181).

`ModeChangeStatus` enum8 values, with no conformance on the values: `Success` 0, `UnsupportedMode` 1, `GenericFailure` 2, `InvalidInMode` 3. Range `MfgCodes` 128-191 (lines 59-75).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEPONOFF | feature | bit 0 | feature bit, title OnOff | X | none | none in catalog | absent | no row | no source | no correspondence | disallowed; definition_gen.go:248. prior accounting line 500 also status absent |
| SupportedModes | attribute | 0x0000 | list of ModeOptionStruct, fixed, length 2 to 255 | M | WaterHeater server | none in catalog: thermal.mode.dhw_supported | absent: thermal.mode.dhw_supported | no row | no source | no correspondence | access R view; definition_gen.go:251-259 |
| SupportedModes.Label | attribute field | 0 | string, fixed, max 64 | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | ModeOptionStruct; definition_gen.go:106 |
| SupportedModes.Mode | attribute field | 1 | uint8, fixed | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:107 |
| SupportedModes.ModeTags | attribute field | 2 | list of ModeTagStruct, fixed, length 1 to 8 | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:108 |
| SupportedModes.ModeTags.MfgCode | attribute field | 0 | vendor-id, uint16, constraint desc | O | none | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:137 |
| SupportedModes.ModeTags.Value | attribute field | 1 | ModeTag enum16 | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:138 |
| CurrentMode | attribute | 0x0001 | uint8, nonvolatile, constraint desc | M | WaterHeater server | none in catalog: thermal.mode.dhw | absent: thermal.mode.dhw | no row | no source | no correspondence | access R view; definition_gen.go:260-267. thermal.mode.system, thermal.mode.zone and thermal.mode.terminal_unit are symbol facts on other subjects and are not cited as feeds |
| StartUpMode | attribute | 0x0002 | uint8, nullable, nonvolatile, constraint desc | X | none | none in catalog | absent | no row | no source | no correspondence | disallowed; access RW view/operate; definition_gen.go:268-275 |
| OnMode | attribute | 0x0003 | uint8, nullable, nonvolatile, constraint desc | X | none | none in catalog | absent | no row | no source | no correspondence | disallowed; access RW view/operate; definition_gen.go:276-283 |
| ChangeToMode | command | 0x00 | request, response ChangeToModeResponse | M | WaterHeater server | none in catalog: thermal.operation.set_dhw_mode | absent: thermal.operation.set_dhw_mode | no row | no source | no correspondence | access R operate, write operate; definition_gen.go:286-295 |
| ChangeToMode.NewMode | command field | 0 | uint8, constraint desc | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:292 |
| ChangeToModeResponse | command | 0x01 | response | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; definition_gen.go:296-305. prior accounting line 501 marks the response absent as an operation outcome |
| ChangeToModeResponse.Status | command field | 0 | ModeChangeStatus enum8, constraint desc | M | WaterHeater server | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:301 |
| ChangeToModeResponse.StatusText | command field | 1 | string, max 64 | [Status == Success], M | none | none in catalog | absent | no row | no source | no correspondence | definition_gen.go:302 |

### PumpConfigurationAndControl

Cluster id `0x0200`, name `PumpConfigurationAndControl`, revision 5. `go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go` lines 22-26. `Definition` at line 467. No commands. Mandatory server on Pump and mandatory client on PumpController.

`OperationModeEnum` enum8: `Normal` 0 `M`, `Minimum` 1 `SPD`, `Maximum` 2 `SPD`, `Local` 3 `LOCAL` (lines 126-140).

`ControlModeEnum` enum8: `ConstantSpeed` 0 `SPD`, `ConstantPressure` 1 `PRSCONST`, `ProportionalPressure` 2 `PRSCOMP`, `ConstantFlow` 3 `FLW`, `ConstantTemperature` 5 `TEMP`, `Automatic` 7 `AUTO` (lines 99-117). Value 4 and value 6 are not in the enum.

`PumpStatusBitmap` map16, every member conformance `M`: `DeviceFault` bit 0, `SupplyFault` bit 1, `SpeedLow` bit 2, `SpeedHigh` bit 3, `LocalOverride` bit 4, `Running` bit 5, `RemotePressure` bit 6, `RemoteFlow` bit 7, `RemoteTemperature` bit 8 (lines 149-173).

Pressure, speed, flow, temperature, capacity, power and energy attributes in this cluster use integer type names. `schema.json` type strings for them are `int16`, `uint16`, `uint24` or `uint32`, with no unit token. `MinConstTemp` and `MaxConstTemp` add constraint `min -27315`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PRSCONST | feature | bit 0 | feature bit, title ConstantPressure | O.a+ | none | none in catalog: thermal.mode.pump_control | absent: thermal.mode.pump_control | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:470; choice a is one or more for the five O.a+ bits |
| PRSCOMP | feature | bit 1 | feature bit, title CompensatedPressure | O.a+ | none | none in catalog: thermal.mode.pump_control | absent: thermal.mode.pump_control | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:471; choice a is one or more for the five O.a+ bits |
| FLW | feature | bit 2 | feature bit, title ConstantFlow | O.a+ | none | none in catalog: thermal.mode.pump_control | absent: thermal.mode.pump_control | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:472; choice a is one or more for the five O.a+ bits |
| SPD | feature | bit 3 | feature bit, title ConstantSpeed | O.a+ | none | none in catalog: thermal.mode.pump_control | absent: thermal.mode.pump_control | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:473; choice a is one or more for the five O.a+ bits |
| TEMP | feature | bit 4 | feature bit, title ConstantTemperature | O.a+ | none | none in catalog: thermal.mode.pump_control | absent: thermal.mode.pump_control | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:474; choice a is one or more for the five O.a+ bits |
| AUTO | feature | bit 5 | feature bit, title Automatic | O | none | none in catalog: thermal.mode.pump_control | absent: thermal.mode.pump_control | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:475 |
| LOCAL | feature | bit 6 | feature bit, title LocalOperation | O | none | none in catalog: thermal.mode.pump_control | absent: thermal.mode.pump_control | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:476 |
| MaxPressure | attribute | 0x0000 | int16; nullable; fixed; default null | M | Pump server; PumpController client | none in catalog: thermal.nameplate.pump_maximum_pressure | absent: thermal.nameplate.pump_maximum_pressure | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:480 |
| MaxSpeed | attribute | 0x0001 | uint16; nullable; fixed; default null | M | Pump server; PumpController client | none in catalog: thermal.nameplate.pump_maximum_speed | absent: thermal.nameplate.pump_maximum_speed | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:488 |
| MaxFlow | attribute | 0x0002 | uint16; nullable; fixed; default null | M | Pump server; PumpController client | none in catalog: thermal.nameplate.pump_maximum_flow | absent: thermal.nameplate.pump_maximum_flow | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:496 |
| MinConstPressure | attribute | 0x0003 | int16; nullable; fixed; default null | PRSCONST, [AUTO] | none | none in catalog: thermal.nameplate.pump_minimum_constant_pressure | absent: thermal.nameplate.pump_minimum_constant_pressure | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:504 |
| MaxConstPressure | attribute | 0x0004 | int16; nullable; fixed; default null | PRSCONST, [AUTO] | none | none in catalog: thermal.nameplate.pump_maximum_constant_pressure | absent: thermal.nameplate.pump_maximum_constant_pressure | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:512 |
| MinCompPressure | attribute | 0x0005 | int16; nullable; fixed; default null | PRSCOMP, [AUTO] | none | none in catalog: thermal.nameplate.pump_minimum_compensated_pressure | absent: thermal.nameplate.pump_minimum_compensated_pressure | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:520 |
| MaxCompPressure | attribute | 0x0006 | int16; nullable; fixed; default null | PRSCOMP, [AUTO] | none | none in catalog: thermal.nameplate.pump_maximum_compensated_pressure | absent: thermal.nameplate.pump_maximum_compensated_pressure | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:528 |
| MinConstSpeed | attribute | 0x0007 | uint16; nullable; fixed; default null | SPD, [AUTO] | none | none in catalog: thermal.nameplate.pump_minimum_constant_speed | absent: thermal.nameplate.pump_minimum_constant_speed | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:536 |
| MaxConstSpeed | attribute | 0x0008 | uint16; nullable; fixed; default null | SPD, [AUTO] | none | none in catalog: thermal.nameplate.pump_maximum_constant_speed | absent: thermal.nameplate.pump_maximum_constant_speed | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:544 |
| MinConstFlow | attribute | 0x0009 | uint16; nullable; fixed; default null | FLW, [AUTO] | none | none in catalog: thermal.nameplate.pump_minimum_constant_flow | absent: thermal.nameplate.pump_minimum_constant_flow | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:552 |
| MaxConstFlow | attribute | 0x000A | uint16; nullable; fixed; default null | FLW, [AUTO] | none | none in catalog: thermal.nameplate.pump_maximum_constant_flow | absent: thermal.nameplate.pump_maximum_constant_flow | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:560 |
| MinConstTemp | attribute | 0x000B | int16; nullable; fixed; min -27315; default null | TEMP, [AUTO] | none | none in catalog: thermal.nameplate.pump_minimum_constant_temperature | absent: thermal.nameplate.pump_minimum_constant_temperature | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:568 |
| MaxConstTemp | attribute | 0x000C | int16; nullable; fixed; min -27315; default null | TEMP, [AUTO] | none | none in catalog: thermal.nameplate.pump_maximum_constant_temperature | absent: thermal.nameplate.pump_maximum_constant_temperature | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:577 |
| PumpStatus | attribute | 0x0010 | PumpStatusBitmap map16; constraint desc; default 0 | O | none | none in catalog: thermal.status.pump | absent: thermal.status.pump | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:586-592 |
| EffectiveOperationMode | attribute | 0x0011 | OperationModeEnum enum8; nonvolatile; constraint desc | M | Pump server; PumpController client | none in catalog: thermal.mode.pump_effective_operation | absent: thermal.mode.pump_effective_operation | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:594-600 |
| EffectiveControlMode | attribute | 0x0012 | ControlModeEnum enum8; nonvolatile; constraint desc | M | Pump server; PumpController client | none in catalog: thermal.mode.pump_effective_control | absent: thermal.mode.pump_effective_control | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:602-608 |
| Capacity | attribute | 0x0013 | int16; nullable; default null; no unit token | M | Pump server; PumpController client | none in catalog: thermal.measurement.pump_capacity | absent: thermal.measurement.pump_capacity | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:610-616 |
| Speed | attribute | 0x0014 | uint16; nullable; default null; no unit token | O | none | thermal.measurement.pump_speed (partial) | present: thermal.measurement.pump_speed | thermal.measurement.pump_speed: unknown / matter.unmapped.v1 | defined | catalog fact is value_kind quantity, subject resource.pump, aggregation member, direction non_negative, and has no unit attribute; Matter type name is uint16 with no unit token, nullable, no constraint on the attribute; enumeration not applicable | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:618-624. Partial: both name a pump speed quantity. prior accounting line 552 marks this attribute present |
| LifetimeRunningHours | attribute | 0x0015 | uint24; nullable; nonvolatile; default 0; no unit token | O | none | none in catalog: thermal.measurement.pump_running_time | absent: thermal.measurement.pump_running_time | no row | no source | no correspondence | access RW view/manage; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:626-632 |
| Power | attribute | 0x0016 | uint24; nullable; default null; no unit token | O | none | none in catalog: thermal.measurement.pump_power | absent: thermal.measurement.pump_power | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:634-640. thermal.measurement.thermal_power is a signed quantity on resource.heat_generator and is not cited as a feed |
| LifetimeEnergyConsumed | attribute | 0x0017 | uint32; nullable; nonvolatile; default 0; no unit token | O | none | none in catalog: thermal.energy.pump_consumed | absent: thermal.energy.pump_consumed | no row | no source | no correspondence | access RW view/manage; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:642-648 |
| OperationMode | attribute | 0x0020 | OperationModeEnum enum8; nonvolatile; constraint desc; default 0 | M | Pump server; PumpController client | none in catalog: thermal.mode.pump_operation, thermal.operation.set_pump_operation_mode | absent: thermal.mode.pump_operation, thermal.operation.set_pump_operation_mode | no row | no source | no correspondence | access RW view/manage; default 0 is OperationModeNormal; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:650-657 |
| ControlMode | attribute | 0x0021 | ControlModeEnum enum8; nonvolatile; constraint desc; default 0 | O | none | none in catalog: thermal.mode.pump_control, thermal.operation.set_pump_control_mode | absent: thermal.mode.pump_control, thermal.operation.set_pump_control_mode | no row | no source | no correspondence | access RW view/manage; default 0 is ConstantSpeed; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:659-666 |
| AlarmMask | attribute | 0x0022 | uint16 | D | none | none in catalog | absent | no row | no source | no correspondence | deprecated; access RW view/operate; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:668-672. prior accounting line 529 status absent |
| SupplyVoltageLow | event | 0x00 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_supply_voltage_low, thermal.status.pump_alarms | absent: thermal.event.pump_supply_voltage_low, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:676 |
| SupplyVoltageHigh | event | 0x01 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_supply_voltage_high, thermal.status.pump_alarms | absent: thermal.event.pump_supply_voltage_high, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:682 |
| PowerMissingPhase | event | 0x02 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_power_missing_phase, thermal.status.pump_alarms | absent: thermal.event.pump_power_missing_phase, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:688 |
| SystemPressureLow | event | 0x03 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_system_pressure_low, thermal.status.pump_alarms | absent: thermal.event.pump_system_pressure_low, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:694 |
| SystemPressureHigh | event | 0x04 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_system_pressure_high, thermal.status.pump_alarms | absent: thermal.event.pump_system_pressure_high, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:700 |
| DryRunning | event | 0x05 | priority critical; empty payload | O | none | none in catalog: thermal.event.pump_dry_running, thermal.status.pump_alarms | absent: thermal.event.pump_dry_running, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:706 |
| MotorTemperatureHigh | event | 0x06 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_motor_temperature_high, thermal.status.pump_alarms | absent: thermal.event.pump_motor_temperature_high, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:712 |
| PumpMotorFatalFailure | event | 0x07 | priority critical; empty payload | O | none | none in catalog: thermal.event.pump_motor_fatal_failure, thermal.status.pump_alarms | absent: thermal.event.pump_motor_fatal_failure, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:718 |
| ElectronicTemperatureHigh | event | 0x08 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_electronic_temperature_high, thermal.status.pump_alarms | absent: thermal.event.pump_electronic_temperature_high, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:724 |
| PumpBlocked | event | 0x09 | priority critical; empty payload | O | none | none in catalog: thermal.event.pump_pump_blocked, thermal.status.pump_alarms | absent: thermal.event.pump_pump_blocked, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:730 |
| SensorFailure | event | 0x0A | priority info; empty payload | O | none | none in catalog: thermal.event.pump_sensor_failure, thermal.status.pump_alarms | absent: thermal.event.pump_sensor_failure, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:736 |
| ElectronicNonFatalFailure | event | 0x0B | priority info; empty payload | O | none | none in catalog: thermal.event.pump_electronic_non_fatal_failure, thermal.status.pump_alarms | absent: thermal.event.pump_electronic_non_fatal_failure, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:742 |
| ElectronicFatalFailure | event | 0x0C | priority critical; empty payload | O | none | none in catalog: thermal.event.pump_electronic_fatal_failure, thermal.status.pump_alarms | absent: thermal.event.pump_electronic_fatal_failure, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:748 |
| GeneralFault | event | 0x0D | priority info; empty payload | O | none | none in catalog: thermal.event.pump_general_fault, thermal.status.pump_alarms | absent: thermal.event.pump_general_fault, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:754 |
| Leakage | event | 0x0E | priority info; empty payload | O | none | none in catalog: thermal.event.pump_leakage, thermal.status.pump_alarms | absent: thermal.event.pump_leakage, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:760 |
| AirDetection | event | 0x0F | priority info; empty payload | O | none | none in catalog: thermal.event.pump_air_detection, thermal.status.pump_alarms | absent: thermal.event.pump_air_detection, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:766 |
| TurbineOperation | event | 0x10 | priority info; empty payload | O | none | none in catalog: thermal.event.pump_turbine_operation, thermal.status.pump_alarms | absent: thermal.event.pump_turbine_operation, thermal.status.pump_alarms | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:772 |

### ValveConfigurationAndControl

Cluster id `0x0081`, name `ValveConfigurationAndControl`, revision 1. `go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go` lines 22-26. `Definition` at line 217. Mandatory server on WaterValve.

`ValveStateEnum` enum8: `Closed` 0 `M`, `Open` 1 `M`, `Transitioning` 2 `M` (lines 116-128).

`ValveFaultBitmap` map16, every member conformance `M`: `GeneralFault` bit 0, `Blocked` bit 1, `Leaking` bit 2, `NotConnected` bit 3, `ShortCircuit` bit 4, `CurrentExceeded` bit 5 (lines 89-107).

`StatusCodeEnum` enum8 value `FailureDueToFault` 2 `M` is declared at lines 66-80 and is not referenced by `Definition`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TS | feature | bit 0 | feature bit, title TimeSync | desc | none | none in catalog: thermal.valve.auto_close_time | absent: thermal.valve.auto_close_time | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:220 |
| LVL | feature | bit 1 | feature bit, title Level | O | none | none in catalog: thermal.measurement.valve_level | absent: thermal.measurement.valve_level | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:221. Catalog fact thermal.measurement.valve_position is cited on CurrentLevel, not on this bit |
| OpenDuration | attribute | 0x0000 | elapsed-s, uint32, min 1, nullable | M | WaterValve server | none in catalog: thermal.valve.open_duration | absent: thermal.valve.open_duration | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:224-231 |
| DefaultOpenDuration | attribute | 0x0001 | elapsed-s, uint32, min 1, nullable, nonvolatile | M | WaterValve server | none in catalog: thermal.configuration.valve_default_open_duration, thermal.operation.set_valve_default_open_duration | absent: thermal.configuration.valve_default_open_duration, thermal.operation.set_valve_default_open_duration | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:232-239 |
| AutoCloseTime | attribute | 0x0002 | epoch-us, uint64, nullable | TS | none | none in catalog: thermal.valve.auto_close_time | absent: thermal.valve.auto_close_time | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:240-246 |
| RemainingDuration | attribute | 0x0003 | elapsed-s, uint32, nullable, quieter reporting | M | WaterValve server | none in catalog: thermal.valve.remaining_duration | absent: thermal.valve.remaining_duration | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:247-253 |
| CurrentState | attribute | 0x0004 | ValveStateEnum enum8, nullable | M | WaterValve server | none in catalog: resource.valve, thermal.status.valve_state | absent: resource.valve, thermal.status.valve_state | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:254-260 |
| TargetState | attribute | 0x0005 | ValveStateEnum enum8, nullable | M | WaterValve server | none in catalog: thermal.setpoint.valve_target_state | absent: thermal.setpoint.valve_target_state | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:261-267 |
| CurrentLevel | attribute | 0x0006 | percent, uint8, max 100, nullable | LVL | none | thermal.measurement.valve_position (partial); none in catalog: thermal.measurement.valve_level | present: thermal.measurement.valve_position; absent: thermal.measurement.valve_level | thermal.measurement.valve_position: unknown / matter.unmapped.v1; thermal.measurement.valve_level: no row | defined | catalog fact is value_kind quantity, subject resource.terminal_unit, aggregation member, direction non_negative, and has no unit attribute; Matter type name is percent, uint8, max 100, nullable, conformance LVL; subject kind is terminal_unit and the catalog has no resource.valve | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:268-275 |
| TargetLevel | attribute | 0x0007 | percent, uint8, max 100, nullable | LVL | none | none in catalog: thermal.operation.set_valve_level, thermal.setpoint.valve_target_level | absent: thermal.operation.set_valve_level, thermal.setpoint.valve_target_level | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:276-283. valve_position is an observed quantity and is not cited as this target |
| DefaultOpenLevel | attribute | 0x0008 | percent, uint8, 1 to 100, nonvolatile, default 100 | [LVL] | none | none in catalog: thermal.configuration.valve_default_open_level, thermal.operation.set_valve_default_open_level | absent: thermal.configuration.valve_default_open_level, thermal.operation.set_valve_default_open_level | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:284-292 |
| ValveFault | attribute | 0x0009 | ValveFaultBitmap map16, default 0 | O | none | none in catalog: thermal.status.valve_faults | absent: thermal.status.valve_faults | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:293-299 |
| LevelStep | attribute | 0x000A | uint8, 1 to 50, fixed, default 1 | [LVL] | none | none in catalog: thermal.configuration.valve_level_step | absent: thermal.configuration.valve_level_step | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:300-308 |
| Open | command | 0x00 | request, response status | M | WaterValve server | none in catalog: thermal.operation.set_valve_state | absent: thermal.operation.set_valve_state | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:310-320 |
| Open.OpenDuration | command field | 0 | elapsed-s, uint32, min 1, nullable | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:317 |
| Open.TargetLevel | command field | 1 | percent, uint8, 1 to 100 | [LVL] | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:318 |
| Close | command | 0x01 | request, response status; empty payload | M | WaterValve server | none in catalog: thermal.operation.set_valve_state | absent: thermal.operation.set_valve_state | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:321-328 |
| ValveStateChanged | event | 0x00 | priority info | O | none | none in catalog: thermal.event.valve_state_changed | absent: thermal.event.valve_state_changed | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:331-340 |
| ValveStateChanged.ValveState | event field | 0 | ValveStateEnum enum8 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:336 |
| ValveStateChanged.ValveLevel | event field | 1 | percent, uint8, max 100 | LVL | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:337 |
| ValveFault | event | 0x01 | priority info | O | none | none in catalog: thermal.event.valve_fault | absent: thermal.event.valve_fault | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:341-349. Same name as attribute 0x0009; this row is the event |
| ValveFault.ValveFault | event field | 0 | ValveFaultBitmap map16 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/valveconfigurationandcontrol/definition_gen.go:346 |

### BooleanState

Cluster id `0x0045`, name `BooleanState`, revision 3. `go-fabric@v0.22.2:cluster/spec/booleanstate/definition_gen.go` lines 22-26. `Definition` at line 70. Mandatory server on WaterFreezeDetector and WaterLeakDetector, both with feature `CHGEVENT` and event `StateChange` `PresenceMandatory`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CHGEVENT | feature | bit 0 | feature bit, title ChangeEvent | [Rev >= v3] | WaterFreezeDetector server; WaterLeakDetector server (device file Features 0x1 CHGEVENT and StateChange PresenceMandatory) | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstate/definition_gen.go:73. Device files set Features 0x1 |
| StateValue | attribute | 0x0000 | bool | M | WaterFreezeDetector server; WaterLeakDetector server | none in catalog: thermal.status.freeze, thermal.status.leak | absent: thermal.status.freeze, thermal.status.leak | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstate/definition_gen.go:76-81. The two proposals are one prior accounting row for both device types |
| StateChange | event | 0x00 | priority info | CHGEVENT, O | WaterFreezeDetector server; WaterLeakDetector server (device file Features 0x1 CHGEVENT and StateChange PresenceMandatory) | none in catalog: thermal.event.freeze_changed, thermal.event.leak_changed | absent: thermal.event.freeze_changed, thermal.event.leak_changed | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstate/definition_gen.go:83-92 |
| StateChange.StateValue | event field | 0 | bool | M | WaterFreezeDetector server; WaterLeakDetector server (device file Features 0x1 CHGEVENT and StateChange PresenceMandatory) | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstate/definition_gen.go:89 |

### BooleanStateConfiguration

Cluster id `0x0080`, name `BooleanStateConfiguration`, revision 2. `go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go` lines 22-26. `Definition` at line 196. Optional server on WaterFreezeDetector and WaterLeakDetector. No element below is mandatory for those device types.

`AlarmModeBitmap` map8: `Visual` bit 0 conformance `VIS`, `Audible` bit 1 conformance `AUD` (lines 72-82).

`SensorFaultBitmap` map16: `GeneralFault` bit 0 conformance `M` (lines 91-99).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| VIS | feature | bit 0 | feature bit, title Visual | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:199 |
| AUD | feature | bit 1 | feature bit, title Audible | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:200 |
| SPRS | feature | bit 2 | feature bit, title AlarmSuppress | [VIS \| AUD] | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:201 |
| SENSLVL | feature | bit 3 | feature bit, title SensitivityLevel | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:202 |
| FAULTEV | feature | bit 4 | feature bit, title FaultEvents | [Rev >= v2] | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:203 |
| CurrentSensitivityLevel | attribute | 0x0000 | uint8, nonvolatile, max supportedSensitivityLevels - 1 | SENSLVL | none | none in catalog: thermal.detector.sensitivity_level, thermal.operation.set_detector_sensitivity | absent: thermal.detector.sensitivity_level, thermal.operation.set_detector_sensitivity | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:206-213 |
| SupportedSensitivityLevels | attribute | 0x0001 | uint8, fixed, 2 to 10 | SENSLVL | none | none in catalog: thermal.detector.supported_sensitivity_levels | absent: thermal.detector.supported_sensitivity_levels | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:214-221 |
| DefaultSensitivityLevel | attribute | 0x0002 | uint8, fixed, max supportedSensitivityLevels - 1 | [SENSLVL] | none | none in catalog: thermal.detector.default_sensitivity_level | absent: thermal.detector.default_sensitivity_level | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:222-229 |
| AlarmsActive | attribute | 0x0003 | AlarmModeBitmap map8 | VIS \| AUD | none | none in catalog: thermal.detector.alarms_active | absent: thermal.detector.alarms_active | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:230-235 |
| AlarmsSuppressed | attribute | 0x0004 | AlarmModeBitmap map8 | SPRS | none | none in catalog: thermal.detector.alarms_suppressed | absent: thermal.detector.alarms_suppressed | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:236-241 |
| AlarmsEnabled | attribute | 0x0005 | AlarmModeBitmap map8, nonvolatile | [VIS \| AUD] | none | none in catalog: thermal.detector.alarms_enabled | absent: thermal.detector.alarms_enabled | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:242-248 |
| AlarmsSupported | attribute | 0x0006 | AlarmModeBitmap map8, fixed | VIS \| AUD | none | none in catalog: thermal.detector.alarms_supported | absent: thermal.detector.alarms_supported | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:249-255 |
| SensorFault | attribute | 0x0007 | SensorFaultBitmap map16, default 0 | O | none | none in catalog: thermal.detector.sensor_fault | absent: thermal.detector.sensor_fault | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:256-262 |
| SuppressAlarm | command | 0x00 | request, response status | SPRS | none | none in catalog: thermal.operation.suppress_detector_alarm | absent: thermal.operation.suppress_detector_alarm | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:265-272 |
| SuppressAlarm.AlarmsToSuppress | command field | 0 | AlarmModeBitmap map8 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:271 |
| EnableDisableAlarm | command | 0x01 | request, response status | VIS \| AUD | none | none in catalog: thermal.operation.enable_detector_alarm | absent: thermal.operation.enable_detector_alarm | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:273-284 |
| EnableDisableAlarm.AlarmsToEnableDisable | command field | 0 | AlarmModeBitmap map8 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:280 |
| AlarmsStateChanged | event | 0x00 | priority info | VIS \| AUD | none | none in catalog: thermal.event.detector_alarms_changed | absent: thermal.event.detector_alarms_changed | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:286-296 |
| AlarmsStateChanged.AlarmsActive | event field | 0 | AlarmModeBitmap map8 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:292 |
| AlarmsStateChanged.AlarmsSuppressed | event field | 1 | AlarmModeBitmap map8 | SPRS | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:293 |
| SensorFault | event | 0x01 | priority info | FAULTEV, O | none | none in catalog: thermal.event.detector_sensor_fault | absent: thermal.event.detector_sensor_fault | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:297-305. Same name as attribute 0x0007; this row is the event |
| SensorFault.SensorFault | event field | 0 | SensorFaultBitmap map16 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/booleanstateconfiguration/definition_gen.go:302 |

### WaterTankLevelMonitoring

Cluster id `0x0079`, name `WaterTankLevelMonitoring`, revision 1, base `ResourceMonitoring`. `go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go` lines 22-26 and 174-176. No device type in this group declares it, so every row is `none` in the mandatory column. `ChangeIndication` conformance is `M` on the cluster itself.

`ChangeIndicationEnum` enum8: `Ok` 0 `M`, `Warning` 1 `WRN`, `Critical` 2 `M` (lines 61-73).

`DegradationDirectionEnum` enum8: `Up` 0 `M`, `Down` 1 `M` (lines 82-92).

`ProductIdentifierTypeEnum` enum8, every value conformance `M`: `Upc` 0, `Gtin8` 1, `Ean` 2, `Gtin14` 3, `Oem` 4 (lines 101-117).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CON | feature | bit 0 | feature bit, title Condition | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:178. prior accounting line 232 status absent; line 226 puts the water-tank ids on attribute Condition, not on this bit |
| WRN | feature | bit 1 | feature bit, title Warning | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:179 |
| REP | feature | bit 2 | feature bit, title ReplacementProductList | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:180 |
| Condition | attribute | 0x0000 | percent, uint8, max 100 | CON | none | none in catalog: resource.water_tank, thermal.dimension.water_tank, thermal.relation.water_tank_member, thermal.service.water_tank, thermal.water_tank.condition | absent: resource.water_tank, thermal.dimension.water_tank, thermal.relation.water_tank_member, thermal.service.water_tank, thermal.water_tank.condition | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:183-189 |
| DegradationDirection | attribute | 0x0001 | DegradationDirectionEnum enum8, fixed, constraint desc | CON | none | none in catalog: thermal.water_tank.degradation_direction | absent: thermal.water_tank.degradation_direction | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:190-197 |
| ChangeIndication | attribute | 0x0002 | ChangeIndicationEnum enum8 | M | none | none in catalog: thermal.water_tank.change_indication | absent: thermal.water_tank.change_indication | no row | no source | no correspondence | access R view; cluster conformance M; no group device type requires the cluster; go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:198-203 |
| InPlaceIndicator | attribute | 0x0003 | bool | O | none | none in catalog: thermal.water_tank.in_place | absent: thermal.water_tank.in_place | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:204-209 |
| LastChangedTime | attribute | 0x0004 | epoch-s, uint32, nullable, nonvolatile, default null | O | none | none in catalog: thermal.water_tank.last_changed | absent: thermal.water_tank.last_changed | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:210-217 |
| ReplacementProductList | attribute | 0x0005 | list of ReplacementProductStruct, fixed, max 5 | REP | none | none in catalog: thermal.dimension.replacement_product, thermal.water_tank.replacement_product_identifier | absent: thermal.dimension.replacement_product, thermal.water_tank.replacement_product_identifier | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:218-226 |
| ReplacementProductList.ProductIdentifierType | attribute field | 0 | ProductIdentifierTypeEnum enum8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:146 |
| ReplacementProductList.ProductIdentifierValue | attribute field | 1 | string, max 20 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:147 |
| ResetCondition | command | 0x00 | request, response status; empty payload | O | none | none in catalog: thermal.operation.reset_water_tank | absent: thermal.operation.reset_water_tank | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/watertanklevelmonitoring/definition_gen.go:228-235 |

### OnOff

Cluster id `0x0006`, name `OnOff`, revision 6. `go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go` lines 22-26. `Definition` at line 270. Mandatory server on Pump and mandatory client on PumpController. Neither device file sets an OnOff feature.

`StartUpOnOffEnum` enum8: `Off` 0 `M`, `On` 1 `M`, `Toggle` 2 `M` (lines 140-151).

`EffectIdentifierEnum` enum8: `DelayedAllOff` 0 `M`, `DyingLight` 1 `M` (lines 103-113). `DelayedAllOffEffectVariantEnum`: `DelayedOffFastFade` 0 `M`, `NoFade` 1 `M`, `DelayedOffSlowFade` 2 `M` (lines 65-77). `DyingLightEffectVariantEnum`: `DyingLightFadeOff` 0 `M` (lines 87-94). The command field `EffectVariant` is typed `enum8`, not one of those enums (`definition_gen.go:341`).

`OnOffControlBitmap` map8: `AcceptOnlyWhenOn` bit 0 conformance `M` (lines 122-130).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LT | feature | bit 0 | feature bit, title Lighting | [!OFFONLY] | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:273 |
| DF | feature | bit 1 | feature bit, title DeadFrontBehavior | [!OFFONLY] | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:274 |
| OFFONLY | feature | bit 2 | feature bit, title OffOnly | [!(LT \| DF)] | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:275 |
| OnOff | attribute | 0x0000 | bool, nonvolatile, scene | M | Pump server; PumpController client | none in catalog: thermal.status.pump_running; none in catalog: thermal.status.terminal_unit_power | absent: thermal.status.pump_running, thermal.status.terminal_unit_power | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:278-284. prior accounting line 16 |
| GlobalSceneControl | attribute | 0x4000 | bool | LT | none | none in catalog | absent | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:285-290 |
| OnTime | attribute | 0x4001 | uint16 | LT | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:291-296 |
| OffWaitTime | attribute | 0x4002 | uint16 | LT | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:297-302 |
| StartUpOnOff | attribute | 0x4003 | StartUpOnOffEnum enum8, nullable, nonvolatile, constraint desc | LT | none | none in catalog | absent | no row | no source | no correspondence | access RW view/manage; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:303-310 |
| Off | command | 0x00 | request, response status; empty payload | M | Pump server; PumpController client | none in catalog: thermal.operation.set_pump_running; none in catalog: thermal.operation.set_terminal_unit_power | absent: thermal.operation.set_pump_running, thermal.operation.set_terminal_unit_power | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:313-319 |
| On | command | 0x01 | request, response status; empty payload | !OFFONLY | Pump server; PumpController client (conformance !OFFONLY; go-fabric@v0.22.2:device/pump_gen.go:43-47 and go-fabric@v0.22.2:device/pump_controller_gen.go:43-47 set no OnOff features) | none in catalog: thermal.operation.set_pump_running; none in catalog: thermal.operation.set_terminal_unit_power | absent: thermal.operation.set_pump_running, thermal.operation.set_terminal_unit_power | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:320-326 |
| Toggle | command | 0x02 | request, response status; empty payload | !OFFONLY | Pump server; PumpController client (conformance !OFFONLY; go-fabric@v0.22.2:device/pump_gen.go:43-47 and go-fabric@v0.22.2:device/pump_controller_gen.go:43-47 set no OnOff features) | none in catalog: thermal.operation.set_pump_running; none in catalog: thermal.operation.set_terminal_unit_power | absent: thermal.operation.set_pump_running, thermal.operation.set_terminal_unit_power | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:327-333 |
| OffWithEffect | command | 0x40 | request, response status | LT | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:334-344 |
| OffWithEffect.EffectIdentifier | command field | 0 | EffectIdentifierEnum enum8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:340 |
| OffWithEffect.EffectVariant | command field | 1 | enum8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:341 |
| OnWithRecallGlobalScene | command | 0x41 | request, response status; empty payload | LT | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:345-351 |
| OnWithTimedOff | command | 0x42 | request, response status | LT | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:352-363 |
| OnWithTimedOff.OnOffControl | command field | 0 | OnOffControlBitmap map8, 0 to 1 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:358 |
| OnWithTimedOff.OnTime | command field | 1 | uint16, max 65534 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:359 |
| OnWithTimedOff.OffWaitTime | command field | 2 | uint16, max 65534 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/onoff/definition_gen.go:360 |

### LevelControl

Cluster id `0x0008`, name `LevelControl`, revision 7. `go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go` lines 22-26. `Definition` at line 396. Optional server on Pump and optional client on PumpController. No row is mandatory for a device type in this group.

`MoveModeEnum` and `StepModeEnum` enum8: `Up` 0 `M`, `Down` 1 `M` (lines 77-87 and 115-124).

`OptionsBitmap` map8: `ExecuteIfOff` bit 0 conformance `LT | OO`, `CoupleColorTempToLevel` bit 1 conformance `LT` (lines 96-106).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OO | feature | bit 0 | feature bit, title OnOff | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:399 |
| LT | feature | bit 1 | feature bit, title Lighting | O | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:400 |
| FQ | feature | bit 2 | feature bit, title Frequency | P | none | none in catalog | absent | no row | no source | no correspondence | provisional; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:401 |
| CurrentLevel | attribute | 0x0000 | uint8, nullable, nonvolatile, scene, quieter reporting, minLevel to maxLevel | M | none | none in catalog: thermal.setpoint.pump_level | absent: thermal.setpoint.pump_level | no row | no source | no correspondence | access R view; cluster is optional on Pump and PumpController; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:404-411 |
| RemainingTime | attribute | 0x0001 | uint16, quieter reporting | LT | none | none in catalog | absent | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:412-418 |
| MinLevel | attribute | 0x0002 | uint8, fixed, max 254, default 1 | Rev >= v7, O | none | none in catalog | absent | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:419-427 |
| MaxLevel | attribute | 0x0003 | uint8, fixed, minLevel to 254, default 254 | Rev >= v7, O | none | none in catalog | absent | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:428-436 |
| CurrentFrequency | attribute | 0x0004 | uint16, scene, quieter reporting, minFrequency to maxFrequency | FQ | none | none in catalog | absent | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:437-444 |
| MinFrequency | attribute | 0x0005 | uint16 | FQ | none | none in catalog | absent | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:445-450 |
| MaxFrequency | attribute | 0x0006 | uint16, min minFrequency | FQ | none | none in catalog | absent | no row | no source | no correspondence | access R view; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:451-457 |
| Options | attribute | 0x000F | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:458-464 |
| OnOffTransitionTime | attribute | 0x0010 | uint16, default 0 | O | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:465-471 |
| OnLevel | attribute | 0x0011 | uint8, nullable, minLevel to maxLevel | M | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:472-479 |
| OnTransitionTime | attribute | 0x0012 | uint16, nullable, default null | O | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:480-487 |
| OffTransitionTime | attribute | 0x0013 | uint16, nullable, default null | O | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:488-495 |
| DefaultMoveRate | attribute | 0x0014 | uint8, nullable, min 1 | O | none | none in catalog | absent | no row | no source | no correspondence | access RW view/operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:496-503 |
| StartUpCurrentLevel | attribute | 0x4000 | uint8, nullable, nonvolatile, constraint desc | LT | none | none in catalog | absent | no row | no source | no correspondence | access RW view/manage; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:504-511 |
| MoveToLevel | command | 0x00 | request, response status | M | none | none in catalog: thermal.operation.set_pump_level | absent: thermal.operation.set_pump_level | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:515 |
| MoveToLevel.Level | command field | 0 | uint8, max 254 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:520 |
| MoveToLevel.TransitionTime | command field | 1 | uint16, nullable | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:521 |
| MoveToLevel.OptionsMask | command field | 2 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:522 |
| MoveToLevel.OptionsOverride | command field | 3 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:523 |
| Move | command | 0x01 | request, response status | M | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:528 |
| Move.MoveMode | command field | 0 | MoveModeEnum enum8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:533 |
| Move.Rate | command field | 1 | uint8, nullable | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:534 |
| Move.OptionsMask | command field | 2 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:535 |
| Move.OptionsOverride | command field | 3 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:536 |
| Step | command | 0x02 | request, response status | M | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:541 |
| Step.StepMode | command field | 0 | StepModeEnum enum8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:546 |
| Step.StepSize | command field | 1 | uint8 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:547 |
| Step.TransitionTime | command field | 2 | uint16, nullable | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:548 |
| Step.OptionsMask | command field | 3 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:549 |
| Step.OptionsOverride | command field | 4 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:550 |
| Stop | command | 0x03 | request, response status | M | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:555 |
| Stop.OptionsMask | command field | 0 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:560 |
| Stop.OptionsOverride | command field | 1 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:561 |
| MoveToLevelWithOnOff | command | 0x04 | request, response status | M | none | none in catalog: thermal.operation.set_pump_level | absent: thermal.operation.set_pump_level | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:566 |
| MoveToLevelWithOnOff.Level | command field | 0 | uint8, max 254 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:571 |
| MoveToLevelWithOnOff.TransitionTime | command field | 1 | uint16, nullable | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:572 |
| MoveToLevelWithOnOff.OptionsMask | command field | 2 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:573 |
| MoveToLevelWithOnOff.OptionsOverride | command field | 3 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:574 |
| MoveWithOnOff | command | 0x05 | request, response status | M | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:579 |
| MoveWithOnOff.MoveMode | command field | 0 | MoveModeEnum enum8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:584 |
| MoveWithOnOff.Rate | command field | 1 | uint8, nullable | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:585 |
| MoveWithOnOff.OptionsMask | command field | 2 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:586 |
| MoveWithOnOff.OptionsOverride | command field | 3 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:587 |
| StepWithOnOff | command | 0x06 | request, response status | M | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:592 |
| StepWithOnOff.StepMode | command field | 0 | StepModeEnum enum8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:597 |
| StepWithOnOff.StepSize | command field | 1 | uint8 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:598 |
| StepWithOnOff.TransitionTime | command field | 2 | uint16, nullable | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:599 |
| StepWithOnOff.OptionsMask | command field | 3 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:600 |
| StepWithOnOff.OptionsOverride | command field | 4 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:601 |
| StopWithOnOff | command | 0x07 | request, response status | M | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:606 |
| StopWithOnOff.OptionsMask | command field | 0 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:611 |
| StopWithOnOff.OptionsOverride | command field | 1 | OptionsBitmap map8, constraint desc | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:612 |
| MoveToClosestFrequency | command | 0x08 | request, response status | FQ | none | none in catalog | absent | no row | no source | no correspondence | access R operate, write operate; go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:617 |
| MoveToClosestFrequency.Frequency | command field | 0 | uint16 | M | none | none in catalog | absent | no row | no source | no correspondence | go-fabric@v0.22.2:cluster/spec/levelcontrol/definition_gen.go:622 |

## Mandatory elements without a source

An element is listed here when a device type in this group requires it and no catalog element is cited for it. `BoostState` is mandatory on WaterHeater and is omitted here because `thermal.overrun.one_time_dhw` is a candidate (`defined`), with the gaps in that row's loss cell. Clusters outside this group that these device types require (Identify, Thermostat with feature HEAT, Binding) are not expanded.

| cluster | element | kind | id | conformance (as declared) | mandatory for which device types |
|---|---|---|---|---|---|
| WaterHeaterManagement | HeaterTypes | attribute | 0x0000 | M | WaterHeater server |
| WaterHeaterManagement | HeatDemand | attribute | 0x0001 | M | WaterHeater server |
| WaterHeaterManagement | Boost | command | 0x00 | M | WaterHeater server |
| WaterHeaterManagement | Boost.BoostInfo | command field | 0 | M | WaterHeater server |
| WaterHeaterManagement | Boost.BoostInfo.Duration | command field | 0 | M | WaterHeater server |
| WaterHeaterManagement | CancelBoost | command | 0x01 | M | WaterHeater server |
| WaterHeaterManagement | BoostStarted | event | 0x00 | M | WaterHeater server |
| WaterHeaterManagement | BoostStarted.BoostInfo | event field | 0 | M | WaterHeater server |
| WaterHeaterManagement | BoostStarted.BoostInfo.Duration | event field | 0 | M | WaterHeater server |
| WaterHeaterManagement | BoostEnded | event | 0x01 | M | WaterHeater server |
| WaterHeaterMode | SupportedModes | attribute | 0x0000 | M | WaterHeater server |
| WaterHeaterMode | SupportedModes.Label | attribute field | 0 | M | WaterHeater server |
| WaterHeaterMode | SupportedModes.Mode | attribute field | 1 | M | WaterHeater server |
| WaterHeaterMode | SupportedModes.ModeTags | attribute field | 2 | M | WaterHeater server |
| WaterHeaterMode | SupportedModes.ModeTags.Value | attribute field | 1 | M | WaterHeater server |
| WaterHeaterMode | CurrentMode | attribute | 0x0001 | M | WaterHeater server |
| WaterHeaterMode | ChangeToMode | command | 0x00 | M | WaterHeater server |
| WaterHeaterMode | ChangeToMode.NewMode | command field | 0 | M | WaterHeater server |
| WaterHeaterMode | ChangeToModeResponse | command | 0x01 | M | WaterHeater server |
| WaterHeaterMode | ChangeToModeResponse.Status | command field | 0 | M | WaterHeater server |
| PumpConfigurationAndControl | MaxPressure | attribute | 0x0000 | M | Pump server; PumpController client |
| PumpConfigurationAndControl | MaxSpeed | attribute | 0x0001 | M | Pump server; PumpController client |
| PumpConfigurationAndControl | MaxFlow | attribute | 0x0002 | M | Pump server; PumpController client |
| PumpConfigurationAndControl | EffectiveOperationMode | attribute | 0x0011 | M | Pump server; PumpController client |
| PumpConfigurationAndControl | EffectiveControlMode | attribute | 0x0012 | M | Pump server; PumpController client |
| PumpConfigurationAndControl | Capacity | attribute | 0x0013 | M | Pump server; PumpController client |
| PumpConfigurationAndControl | OperationMode | attribute | 0x0020 | M | Pump server; PumpController client |
| ValveConfigurationAndControl | OpenDuration | attribute | 0x0000 | M | WaterValve server |
| ValveConfigurationAndControl | DefaultOpenDuration | attribute | 0x0001 | M | WaterValve server |
| ValveConfigurationAndControl | RemainingDuration | attribute | 0x0003 | M | WaterValve server |
| ValveConfigurationAndControl | CurrentState | attribute | 0x0004 | M | WaterValve server |
| ValveConfigurationAndControl | TargetState | attribute | 0x0005 | M | WaterValve server |
| ValveConfigurationAndControl | Open | command | 0x00 | M | WaterValve server |
| ValveConfigurationAndControl | Close | command | 0x01 | M | WaterValve server |
| BooleanState | CHGEVENT | feature | bit 0 | [Rev >= v3] | WaterFreezeDetector server; WaterLeakDetector server (device file Features 0x1 CHGEVENT and StateChange PresenceMandatory) |
| BooleanState | StateValue | attribute | 0x0000 | M | WaterFreezeDetector server; WaterLeakDetector server |
| BooleanState | StateChange | event | 0x00 | CHGEVENT, O | WaterFreezeDetector server; WaterLeakDetector server (device file Features 0x1 CHGEVENT and StateChange PresenceMandatory) |
| BooleanState | StateChange.StateValue | event field | 0 | M | WaterFreezeDetector server; WaterLeakDetector server (device file Features 0x1 CHGEVENT and StateChange PresenceMandatory) |
| OnOff | OnOff | attribute | 0x0000 | M | Pump server; PumpController client |
| OnOff | Off | command | 0x00 | M | Pump server; PumpController client |
| OnOff | On | command | 0x01 | !OFFONLY | Pump server; PumpController client (conformance !OFFONLY; go-fabric@v0.22.2:device/pump_gen.go:43-47 and go-fabric@v0.22.2:device/pump_controller_gen.go:43-47 set no OnOff features) |
| OnOff | Toggle | command | 0x02 | !OFFONLY | Pump server; PumpController client (conformance !OFFONLY; go-fabric@v0.22.2:device/pump_gen.go:43-47 and go-fabric@v0.22.2:device/pump_controller_gen.go:43-47 set no OnOff features) |

Count: 42.

## Catalog elements of this domain without a Matter element

Included when the id, subject kind or resource kind is `resource.pump`, `resource.domestic_hot_water` or `resource.thermal_store`, or the id contains `pump`, `dhw`, `valve`, `water` or `store`, and the element is not cited as a feed in the cluster tables. Three relations are added because a `to_kinds` entry is `resource.domestic_hot_water` or `resource.thermal_store`: `thermal.relation.fluid_supply`, `thermal.relation.system_member`, `relation.thermal_control`. Three facts are added because a cluster attribute in this group is the nearest name and the subjects differ: `thermal.measurement.flow_rate` (MaxFlow), `thermal.energy.heat_output` (EstimatedHeatRequired), `thermal.measurement.thermal_power` (pump Power). Refrigerant, compressor, circuit, zone and terminal-unit elements other than `thermal.measurement.valve_position` are outside this rule and are not listed. `thermal.measurement.pump_speed`, `thermal.measurement.valve_position` and `thermal.overrun.one_time_dhw` are cited above and are not repeated.

Catalog facts below have no unit attribute. Target dispositions are from `api/v1/targets/matter-1.6.1-v1.json` at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`.

| element | kind | catalog disposition | attributes used for this judgment | target row disposition (+reason) | why it has no counterpart in these clusters |
|---|---|---|---|---|---|
| resource.domestic_hot_water | resource_kind | member | anchor_class function; planes physical, energy, hydraulic, control | no row | WaterHeater device type 0x050F is not a cluster element |
| resource.pump | resource_kind | member | anchor_class component; planes physical, hydraulic, diagnostic | no row | Pump device type 0x0303 is not a cluster element |
| resource.thermal_store | resource_kind | member | anchor_class equipment; planes physical, energy, hydraulic, control | no row | no store resource element in these clusters |
| thermal.dimension.dhw | dimension | member | role resource, resource_kind resource.domestic_hot_water | no row | dimension, not a cluster element |
| thermal.dimension.pump | dimension | member | role resource, resource_kind resource.pump | no row | dimension, not a cluster element |
| thermal.dimension.thermal_store | dimension | member | role resource, resource_kind resource.thermal_store | no row | dimension, not a cluster element |
| thermal.service.dhw | service | member | subject_kind resource.domestic_hot_water | unsupported / matter.service_not_requested_item.v1 | service, not a cluster element |
| thermal.service.pump | service | member | subject_kind resource.pump | unsupported / matter.service_not_requested_item.v1 | service, not a cluster element |
| thermal.service.thermal_store | service | member | subject_kind resource.thermal_store | unsupported / matter.service_not_requested_item.v1 | service, not a cluster element |
| thermal.capability.read.dhw | capability | member | service thermal.service.dhw | unknown / matter.unmapped.v1 | no read-capability element in these clusters |
| thermal.capability.read.thermal_store | capability | member | service thermal.service.thermal_store | unknown / matter.unmapped.v1 | no read-capability element in these clusters |
| thermal.measurement.dhw_temperature | fact | member | quantity, subject resource.domestic_hot_water, aggregation member, direction not_applicable | unknown / matter.unmapped.v1 | no temperature attribute in these nine clusters; WaterHeater's Thermostat cluster is outside this group |
| thermal.measurement.store_temperature | fact | member | quantity, subject resource.thermal_store, aggregation member, direction not_applicable | unknown / matter.unmapped.v1 | TankPercentage is percent and TankVolume is uint16; neither is this temperature |
| thermal.measurement.flow_rate | fact | member | quantity, subject resource.thermal_circuit, aggregation member, direction non_negative | unknown / matter.unmapped.v1 | MaxFlow is a uint16 nameplate attribute; FlowMeasurement is outside this group |
| thermal.measurement.water_pressure | fact | member | quantity, subject resource.heat_generator, aggregation member, direction not_applicable | unknown / matter.unmapped.v1 | pump pressure attributes are int16 nameplate limits; PressureMeasurement is outside this group |
| thermal.setpoint.dhw_temperature_setpoint | fact | member | quantity, subject resource.domestic_hot_water, aggregation not_applicable, direction not_applicable | unknown / matter.unmapped.v1 | standing DHW setpoint; Boost.TemporarySetpoint is an optional boost field of type temperature |
| thermal.energy.heat_output | fact | member | quantity, subject resource.heat_generator, aggregation member, direction non_negative | unknown / matter.unmapped.v1 | EstimatedHeatRequired is energy-mWh on feature EM; subjects differ and the catalog fact has no unit |
| thermal.measurement.thermal_power | fact | member | quantity, subject resource.heat_generator, aggregation member, direction signed, sign_reference thermal.relation.fluid_supply | unknown / matter.unmapped.v1 | pump Power is uint24 with no unit token, on a pump; this fact is heat-generator thermal power |
| thermal.overrun.valve_kick | fact | member | symbol, subject resource.thermal_system, no values list | unknown / matter.unmapped.v1 | symbol fact; Open and Close are commands |
| thermal.portal.read.dhw | presentation | unsupported | target portal | no row | presentation |
| thermal.portal.read.pump | presentation | unsupported | target portal | no row | presentation |
| thermal.portal.read.thermal_store | presentation | unsupported | target portal | no row | presentation |
| thermal.relation.fluid_supply | relation | member | core_type supplies, orientation as_core, medium heat_transfer_fluid, from heat_generator / thermal_circuit / thermal_store, to domestic_hot_water / terminal_unit / thermal_circuit / thermal_store / zone, cardinality many_to_many, over_time false, basis_classes configuration | unknown / matter.relation_construct_not_adopted.v1 | relation; HeaterTypes is a bitmap, not this relation |
| thermal.relation.system_member | relation | member | core_type groups, from thermal_system, to domestic_hot_water / heat_generator / refrigerant_circuit / terminal_unit / thermal_circuit / thermal_store / ventilation_system / zone, cardinality one_to_many, over_time false, basis_classes configuration and gate_rule | unknown / matter.relation_construct_not_adopted.v1 | grouping relation; no cluster element in this group is that relation |
| relation.thermal_control | relation | member | core_type controls, from equipment, to domestic_hot_water / heat_generator / terminal_unit / thermal_circuit / thermal_system / ventilation_system / zone, cardinality many_to_many, over_time false, basis_classes configuration and gate_rule | no row | control relation; no cluster element in this group is that relation |

Count: 25. The catalog has no `thermal.capability.read.pump`.

## Disagreements with the prior accounting

### a prior accounting

prior accounting header, line 3: status `present` means the row is on main and that ticket's target row is complete; `planned` means the ticket adds the element. SemReg ids in the nine cluster sections were checked against the catalog at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`.

1. Pump `Speed` (`a prior accounting` line 552) is status `present` with SemReg `thermal.measurement.pump_speed`. That id is in the catalog, disposition `member`. Its target row is disposition `unknown`, reason `matter.unmapped.v1`. The frozen target does not record a completed mapping.

2. Valve `CurrentLevel` (line 263) is status `planned` and names both `thermal.measurement.valve_position`, which is in the catalog, and `thermal.measurement.valve_level`, which is absent.

3. WaterHeaterManagement `BoostState` (line 333) is status `planned` and names both `thermal.overrun.one_time_dhw`, which is in the catalog, and `thermal.dhw.boost_state`, which is absent.

Other `planned` ids in these nine sections are absent from the catalog, which matches the prior accounting's own meaning of `planned`. Cluster ids, revisions and the conformance texts in those sections match `definition_gen.go` `Conformance.Text` for the elements compared, including `AlarmMask` `D`, WaterHeaterMode `StartUpMode` and `OnMode` `X`, feature `DEPONOFF` `X`, LevelControl `FQ` `P`, and BooleanState event `CHGEVENT, O`.

### a prior accounting

4. a prior claim Matter column says litres for TankVolume. `go-fabric@v0.22.2:cluster/spec/waterheatermanagement/definition_gen.go:247-250` and `schema.json` type string are `uint16`, with no unit token.

5. a prior claim Matter column says percent of capacity for Capacity. `go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:610` and `schema.json` type string are `int16`, with no unit token.

6. a prior claim's id cell says RPM for Speed, and its SemReg cell attaches reciprocal second to `thermal.measurement.pump_speed`. `go-fabric@v0.22.2:cluster/spec/pumpconfigurationandcontrol/definition_gen.go:618` and `schema.json` type string are `uint16`, with no unit token. That catalog element's attributes have no unit field.

7. a prior claim Matter column says hours for LifetimeRunningHours. The generated type is `uint24` (`definition_gen.go:626`), with no unit token.

8. a prior claim Matter column says W and kWh for Power and LifetimeEnergyConsumed. The generated types are `uint24` (`definition_gen.go:634`) and `uint32` (`definition_gen.go:642`), with no unit token.

9. a prior claim lists symbol values active, finished, inactive and running on `thermal.overrun.one_time_dhw`. The catalog element is `value_kind` `symbol` and has no `values` list. No symbol fact in the catalog (39 symbol facts) has a `values` list.

10. a prior claim names Pump mandatory OnOff and PumpConfigurationAndControl, and optional Level Control plus temperature, pressure and flow measurement. `go-fabric@v0.22.2:device/pump_gen.go` also declares mandatory Identify (lines 38-42), optional Groups and ScenesManagement (lines 53-64), and optional clients TemperatureMeasurement, PressureMeasurement, FlowMeasurement and OccupancySensing (lines 78-91).

11. a prior claim names Water Valve mandatory ValveConfigurationAndControl and optional Flow Measurement. `go-fabric@v0.22.2:device/water_valve_gen.go` also declares mandatory Identify (lines 32-36) and an optional FlowMeasurement client (lines 47-51).

12. a prior claim names the two detector device types. Both device files also declare mandatory Identify, BooleanState with feature CHGEVENT and event StateChange PresenceMandatory, and optional BooleanStateConfiguration.

13. a prior claim calls Pump Controller a client role. `go-fabric@v0.22.2:device/pump_controller_gen.go` declares servers Identify (`M`) and Binding (conformance `Simple & Client`, `Mandatory: true`, `BaseMandated: true`) as well as the clients.

14. a prior claim says OnOff is partial via `thermal.overrun.hvac_system_off` and `thermal.mode.*.off` symbols. The catalog has `thermal.overrun.hvac_system_off` as a symbol fact on `resource.thermal_system` with no values list. That id ends in `_off`. The catalog has `thermal.mode.system`, `thermal.mode.zone` and `thermal.mode.terminal_unit` as symbol facts with no values list. It has no id ending in `.off`, and no id `thermal.mode.system.off`, `thermal.mode.zone.off` or `thermal.mode.terminal_unit.off`.

## Uncertainty

1. go-fabric v0.22.2 is the local model (README line 17, definition headers, matter.js `a commit id recorded in the cited file`). The target JSON `model_source.tag` is `v0.13.12`, with `inspection_basis` that the upstream source was not independently replayed. These clusters were not diffed between the two tags.

2. Pump integer attributes and TankVolume carry no unit token in `definition_gen.go` or in the `schema.json` type string. A scale is not established from these sources. `MinConstTemp` and `MaxConstTemp` constrain `min -27315` and still use type name `int16`.

3. Catalog quantity facts have no unit attribute, and symbol facts have no values list, so an exact unit or enumeration correspondence cannot be read out of the catalog.

4. A scan of `device/*_gen.go` for these nine cluster ids found requirements outside the six device types. BooleanState is `M` on `go-fabric@v0.22.2:device/contact_sensor_gen.go` and `go-fabric@v0.22.2:device/rain_sensor_gen.go` as well as the two water detectors. OnOff is `M` on 20 device files besides `go-fabric@v0.22.2:device/pump_gen.go` and `go-fabric@v0.22.2:device/pump_controller_gen.go`. LevelControl is `M` on nine device files (lighting, plug, speaker, switch and control bridge); on Pump and PumpController it is `O`, so LevelControl rows stay `none` in the mandatory column. BooleanStateConfiguration is not `M` on any device file. WaterTankLevelMonitoring is declared on none. `go-fabric@v0.22.2:device/heat_pump_gen.go` declares none of these nine cluster ids. The mandatory column does not list device types outside the six.

5. Semreg and docs-semantic catalogs match on element id, kind, disposition and attributes for the compared bodies. They differ on `admission.evidence` for 20 elements. This accounting uses the docs-semantic catalog for status.

6. WaterHeater requires Thermostat with feature HEAT, and several device types in this group require Identify, Binding or a measurement cluster. Those clusters are outside this group's element tables.

7. `StatusCodeEnum` on ValveConfigurationAndControl is declared and unused by `Definition`. Whether a command response uses it is not stated in `Definition`.
