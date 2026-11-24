---
status: "research notes for Matter 1.6.1 EVSE and device-energy-management clusters; no mapping is decided and no canonical target is written."
---

# EVSE and device energy management

Matter 1.6.1 cluster accounting for EVSE and device energy management. Identifiers, conformance, types and units are read from go-fabric@v0.22.2:parity/schema.json (revision 1.6.1, data model revision 21) and the generated cluster and device files cited below. Catalog elements are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json and semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json. Canonical units are the `canonical_unit` field of docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json. Target rows are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json and docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md. No mapping is chosen. No grade in this note is `exact`. Charge capacity stays `unit.ampere_hour` where the catalog defines it; `storage.capacity.remaining` and `storage.capacity.full_charge` are absent from the pinned catalog. A catalog canonical unit is written beside the Matter unit on each element row that names a catalog field.

Read-only source accounting for the Energy EVSE, Energy EVSE Mode, Device Energy Management, Device Energy Management Mode, and Energy Preference clusters. No mapping is decided here.

## 1. Header

- Queue row QQ04: `TARGET-MAT-R` read-only source accounting by cluster; no canonical JSON writer here (the research row).
- docs-semantic frozen SHA: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`. `git rev-parse HEAD` in that view returned the same SHA.
- semreg frozen SHA: `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:`. `git rev-parse HEAD` in that view returned the same SHA. `git grep -c` of `evse.limit.configured_current` in `fixtures/v1/element-catalog-v1.json` at that SHA returns 1. A byte-for-byte diff of that fixture against the docs-semantic catalog was not done.
- go-fabric: module path `go-fabric`, directory `v0.22.2` (`go-fabric v0.22.2`). `go.mod` states the module path and `go 1.27.4`; it does not state the tag. `go-fabric@v0.22.2:parity/schema.json` key `matter` (lines 2–7): `revision` `1.6.1`, `specificationVersion` `17170688`, `interactionModelRevision` `12`, `dataModelRevision` `21`, `sourceCommit` `a commit id recorded in the cited file`. Each cluster package comment says the file was generated from the matter.js model at `a commit id recorded in the cited file` (Matter 1.6.1). `go-fabric@v0.22.2:cluster/doc.go` lines 28–29 say the cluster implementations target Matter Core Specification 1.6.1.
- The Matter 1.6.1 target pins a different module tag. `api/v1/targets/matter-1.6.1-v1.json` `model_source` (lines 11295–11325): repository `go-fabric`, tag `v0.13.12`, `inspection_grade` `Proven`, `execution_grade` `Unknown`, `standards_equivalence` `Unknown`. Adopted models in that object: Electrical Sensor device type 1296 revision 1; Power Topology cluster 156 revision 1; Electrical Power Measurement cluster 144 revision 3 attribute 5 `ActiveCurrent`. None of those three is a cluster or device type of this group. A diff of tag `v0.13.12` against `v0.22.2` was not done.

### Files read

- Plan: the registry unit rule, `the documentation rules`, `the documentation rules`, the research row (QQ04).
- Pinned files: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`, `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`.
- docs-semantic at the frozen SHA: `api/v1/element-catalog-v1.json` (394 `elements`; `identification_schemes` is `[]` at line 197; no `canonical_unit` key), `api/v1/pack-metadata-v1.json` (canonical units; see the open questions 1), `api/v1/targets/matter-1.6.1-v1.json`, `api/v1/targets/matter-1.6.1-v1.md` (line 18, tag `v0.13.12`), `api/v1/packs/evse-acceptance-vectors.json` (symbol lists), `tests/test_matter161_target.py` (positive ref is `evse.ac.current`, lines 37–38).
- semreg at the frozen SHA: `fixtures/v1/element-catalog-v1.json` (one grep hit for `evse.limit.configured_current`); `semreg/v1/packs/evse/definitions.go` (field table, symbol lists, decimal bounds); `semreg/v1/packs/thermal/definitions.go` lines 102–104 and 123–125 (SG-Ready symbol shape).
- go-fabric v0.22.2: `go-fabric@v0.22.2:parity/schema.json` (header; device types 1292 and 1293; cluster ids 152, 153, 155, 157, 159); `go-fabric@v0.22.2:device/energy_evse_gen.go`; `go-fabric@v0.22.2:device/device_energy_management_gen.go`; `go-fabric@v0.22.2:cluster/spec/instance.go` lines 16–22; `go-fabric@v0.22.2:cluster/doc.go` lines 28–29; `go-fabric@v0.22.2:cluster/spec/energyevse/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/energyevsemode/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/deviceenergymanagement/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/deviceenergymanagementmode/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/energypreference/definition_gen.go`.
- Prior claims were checked only against a prior accounting (legend line 3; DeviceEnergyManagement 377–407; EnergyEvse 409–454; EnergyPreference 456–466; EnergyEvseMode 479–489; DeviceEnergyManagementMode 503–513; device-type stub 1053); `audits/semreg-loss-20261118/a prior accounting` (a prior claim through a prior claim, a prior claim).

### How to read the tables

Locator prefix for a cluster is its `definition_gen.go` unless a cell names another file. Catalog lines are `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`. Target lines are `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json` unless the cell cites the JSON.

Catalog element records have no unit field. Units below are `pack-metadata-v1.json` `fields[].canonical_unit.id`. Symbol literals are not on the catalog record. They are the `symbols` arrays in `evse-acceptance-vectors.json` lines 42–46 and the same lists in `semreg/v1/packs/evse/definitions.go` lines 47–51. Those two lists match for the five status facts.

Global attributes are not cluster elements. `go-fabric@v0.22.2:cluster/spec/instance.go` lines 16–22 names ids every server answers: `0xFFF8` through `0xFFFD`. None of the five `definition_gen.go` files lists them. They are not rows below.

Grades: `exact` would require the same meaning, kind, and unit with loss `none`. No row in this group is `exact`. `partial` means the catalog fact is the same quantity family and the losses are named. `candidate` means the quantity is related and a loss keeps it from `partial`. An id is left out of the feed cell when its subject or name is a different quantity (measured phase current, lifetime meter energy, per-phase allocation, actual current). Those ids are in section 5.

Mandatory column, from the device file `Servers` slice only:

- `EE`: EnergyEvse sets that cluster `Mandatory: true`, and this element's conformance text is `M`.
- `DEM`: DeviceEnergyManagement sets that cluster `Mandatory: true`, and this element's conformance text is `M`.
- `EE-in` / `DEM-in`: the element's own text is `M`, and it sits inside a parent whose text is not `M`. It is mandatory inside that parent. The parent names the condition.
- `if-mounted`: DeviceEnergyManagementMode is listed with conformance `ControllableEsa, O` and `Mandatory` unset. The element's own text is `M`.
- `—`: none of the above.

`source status` is `defined` when the feed cell names a catalog id, and `no source` when it does not. Whether a driver constructs the fact is not visible from these sources.

`loss` is `none` only for `exact`. A `no source` row's loss is that no catalog element exists.

Where a list constraint text is only `max N` and the decoder is `DecodeListIn(..., 0, N)`, the decoder's minimum 0 is not in the constraint text. Cited on the rows where it shows up.

Enum values are in the type cell. A value is listed with its conformance text. ModeTag and ModeChangeStatus `EnumValue` entries have no `Conformance` field.

## 2. Device types

The device file `Servers` and `Clients` slices are what the generated file declares. `schema.json` `deviceTypes[].requirements` is a second list. For these two types the server-cluster names in the file match the server clusters in `schema.json`. The schema list also has device-type requirements and a Descriptor server that the file's `Servers` slice does not contain.

### EnergyEvse

- File: `go-fabric@v0.22.2:device/energy_evse_gen.go`.
- Id `0x050C` (1292), revision 2, classification `simple`, composition `schema.CompositionTree` (lines 16–19, 29–31). No `Base`. No `Conditions`.
- Servers the file declares (lines 32–51):
  - EnergyEvse `0x0099`, conformance `M`, `Mandatory: true`.
  - EnergyEvseMode `0x009D`, conformance `M`, `Mandatory: true`.
  - Identify `0x0003`, conformance `O`, `Mandatory` unset. Outside this cluster group.
  - TemperatureMeasurement `0x0402`, conformance `O`, `Mandatory` unset. Outside this cluster group.
- `schema.json` device type id 1292, name `EnergyEvse`, classification `simple`, revision 2 (lines 18176–18179). Requirements (lines 18180–18227): Identify 3 `O`; deviceType PowerSource 17 `M`; Descriptor 29 with no conformance key; EnergyEvse 153 `M`; EnergyEvseMode 157 `M`; TemperatureMeasurement 1026 `O`; deviceType DeviceEnergyManagement 1293 `M`; deviceType ElectricalSensor 1296 `M`.
- `effective.requirements` (lines 18229–18447) keeps those and adds constraints `min 1` on the three device types. On the composed DeviceEnergyManagement server it sets feature `PFR` conformance text `M` (lines 18365–18377) and feature `PA` conformance text `desc` (lines 18379–18391). On the composed ElectricalSensor it sets ElectricalPowerMeasurement 144 and ElectricalEnergyMeasurement 145 conformance text `M` (lines 18415–18445). `effective.conditions` is empty (line 18231). The file's `Servers` omit Descriptor and do not declare the three device types or those feature overrides.

### DeviceEnergyManagement

- File: `go-fabric@v0.22.2:device/device_energy_management_gen.go`.
- Id `0x050D` (1293), revision 3, classification `utility`, composition tree, `Conditions` `ControllableEsa` (lines 14–17, 27–30). No `Base`.
- Servers the file declares (lines 31–41):
  - DeviceEnergyManagement `0x0098`, conformance `M`, `Mandatory: true`.
  - DeviceEnergyManagementMode `0x009F`, conformance `ControllableEsa, O`, `Mandatory` unset. The accessor comment says the server is nil until a declaration mounts it (lines 69–70).
- Clients the file declares (lines 42–46): ElectricalGridConditions `0x00A0`, conformance `O`. Outside this cluster group.
- `schema.json` device type id 1293 (lines 18452–18479): Descriptor 29, no conformance key; DeviceEnergyManagement 152 `M`; DeviceEnergyManagementMode 159 `ControllableEsa, O`; clientCluster ElectricalGridConditions 160 `O`. `effective.conditions` is `ControllableEsa` (lines 18483–18485). `effective` conformance of DeviceEnergyManagementMode is `otherwise` of the name `ControllableEsa` and `O` (python read of the same object; the requirements text is line 18472). `effective` also narrows features `PA`, `STA`, `PAU`, `FA`, and `CON` to conformance text `[ControllableEsa].a+` (choice `a`, num 1, `orMore` true) on this device type's DeviceEnergyManagement server (lines 18526–18545 and the following feature objects). The cluster definition's own feature texts are in section 3 and are not this device-type override. The file's `Servers` omit Descriptor and do not restate the feature overrides.

EnergyPreference `0x009B` is on neither device file and on neither of these two `schema.json` requirement lists.

## 3. Clusters

### EnergyEvse

Cluster id `0x0099` (153), name `EnergyEvse`, revision 4 (`definition_gen.go` lines 22–26; `schema.json` lines 75904–75906). Feature bits are the cluster FeatureMap bits, separate from global `AttrFeatureMap` `0xFFFC`.

StateEnum (enum8, lines 274–282): `NotPluggedIn` 0 M, `PluggedInNoDemand` 1 M, `PluggedInDemand` 2 M, `PluggedInCharging` 3 M, `PluggedInDischarging` 4 `V2X`, `SessionEnding` 5 M, `Fault` 6 M.

SupplyStateEnum (enum8, lines 302–309): `Disabled` 0 M, `ChargingEnabled` 1 M, `DischargingEnabled` 2 `[V2X]`, `DisabledError` 3 M, `DisabledDiagnostics` 4 M, `Enabled` 5 `[V2X]`.

FaultStateEnum (enum8, lines 235–253), every value M: `NoError` 0, `MeterFailure` 1, `OverVoltage` 2, `UnderVoltage` 3, `OverCurrent` 4, `ContactWetFailure` 5, `ContactDryFailure` 6, `GroundFault` 7, `PowerLoss` 8, `PowerQuality` 9, `PilotShortCircuit` 10, `EmergencyStop` 11, `EvDisconnected` 12, `WrongPowerSupply` 13, `LiveNeutralSwap` 14, `OverTemperature` 15, `Other` 255.

EnergyTransferStoppedReasonEnum (enum8, lines 200–204), every value M: `EvStopped` 0, `EvseStopped` 1, `Other` 2.

TargetDayOfWeekBitmap (map8, lines 141–149), every member M, width 1: `Sunday` bit 0 through `Saturday` bit 6.

Attribute access in `Definition` is Read / View unless the row says otherwise. Current attributes with conformance `M` use `amperage-mA` int64, quality nonvolatile, constraint `min 0`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PREF ChargingPreferences | feature | bit 0 | FeatureMap bit | M | EE | none in catalog ( `evse.target.added_energy`, `evse.target.state_of_charge`, `evse.target.time_of_day`) | absent | no row | no source | no catalog element for the feature bit | lines 84, 661 |
| SOC SoCReporting | feature | bit 1 | FeatureMap bit | O | — | none in catalog ( `evse.vehicle.state_of_charge`) | absent | no row | no source | no catalog element | lines 85, 662 |
| PNC PlugAndCharge | feature | bit 2 | FeatureMap bit | O | — | none in catalog ( `evse.vehicle.identifier`) | absent | no row | no source | no catalog element | lines 86, 663 |
| RFID Rfid | feature | bit 3 | FeatureMap bit | O | — | none in catalog ( `evse.session.rfid_token`) | absent | no row | no source | no catalog element | lines 87, 664 |
| V2X | feature | bit 4 | FeatureMap bit | O | — | none in catalog ( `evse.limit.discharging_enabled_until`) | absent | no row | no source | no catalog element | lines 88, 665 |
| State | attribute | 0x0000 | StateEnum enum8; nullable; catalog canonical unit `evse.status.connection` none, `evse.status.charging` none | M | EE | `evse.status.connection` candidate; `evse.status.charging` candidate | present (lines 110, 109) | unknown / `matter.unmapped.v1` (rows 32, 31) | defined | enumeration: connection symbols `evse.status.connection.connected`, `evse.status.connection.disconnected`; charging symbols `evse.status.charging.charging`, `evse.status.charging.complete`, `evse.status.charging.idle`; StateEnum has seven values; subject `resource.connector` on both facts; the attribute carries no connector id | lines 669–673; acceptance vectors lines 42–43; `definitions.go` lines 47–48 |
| SupplyState | attribute | 0x0001 | SupplyStateEnum enum8; catalog canonical unit `evse.status.readiness` none, `evse.status.interlock` none | M | EE | `evse.status.readiness` candidate; `evse.status.interlock` candidate | present (lines 113, 112) | unknown / `matter.unmapped.v1` (rows 35, 34) | defined | enumeration: readiness symbols `evse.status.readiness.not_ready`, `evse.status.readiness.ready` on `resource.evse`; interlock symbols `evse.status.interlock.active`, `evse.status.interlock.clear` on `resource.connector`; SupplyStateEnum is Disabled, ChargingEnabled, DischargingEnabled, DisabledError, DisabledDiagnostics, Enabled | lines 676–679; acceptance lines 44 and 46; `definitions.go` lines 50–51 |
| FaultState | attribute | 0x0002 | FaultStateEnum enum8; catalog canonical unit `evse.status.fault` none | M | EE | `evse.status.fault` candidate | present (line 111) | unknown / `matter.unmapped.v1` (row 33) | defined | enumeration: symbols `evse.status.fault.clear`, `evse.status.fault.present` versus 17 cause values; subject `resource.evse` | lines 682–685; acceptance line 45; `definitions.go` line 49 |
| ChargingEnabledUntil | attribute | 0x0003 | epoch-s uint32; nullable; nonvolatile | M | EE | none in catalog ( `evse.limit.allocated_current_expiry`, `evse.limit.charging_enabled_until`) | absent | no row | no source | no catalog timestamp | lines 688–692 |
| DischargingEnabledUntil | attribute | 0x0004 | epoch-s uint32; nullable; nonvolatile | V2X | — | none in catalog ( `evse.limit.discharging_enabled_until`) | absent | no row | no source | no catalog timestamp | lines 695–699 |
| CircuitCapacity | attribute | 0x0005 | amperage-mA int64; nonvolatile; constraint `min 0`; catalog canonical unit `evse.limit.configured_current` `unit.ampere`, `evse.ac.current` `unit.ampere` | M | EE | `evse.limit.configured_current` partial | present (line 91) | unknown / `matter.unmapped.v1` (row 19) | defined | unit `unit.ampere` (pack-metadata lines 595–603) versus `amperage-mA`; the declared `exact_multiply` factor 1000 is on `evse.ac.current` only (target JSON lines 135–146) and is not on this row; catalog range coefficient `0` exponent 0 through coefficient `1` exponent 3 (`definitions.go` line 46); subject `resource.evse`; attribute carries no endpoint id | lines 702–707 |
| MinimumChargeCurrent | attribute | 0x0006 | amperage-mA int64; nonvolatile; `min 0` | M | EE | none in catalog ( `evse.limit.minimum_charge_current`) | absent | no row | no source | no catalog minimum-current element | lines 710–715 |
| MaximumChargeCurrent | attribute | 0x0007 | amperage-mA int64; nonvolatile; `min 0`; catalog canonical unit `evse.limit.advertised_current` `unit.ampere`, `evse.limit.allocated_current` `unit.ampere` | M | EE | `evse.limit.advertised_current` candidate; `evse.limit.allocated_current` candidate | present (lines 88, 89) | unknown / `matter.unmapped.v1` (rows 16, 17) | defined | two connector-scoped ampere facts, and the sources do not choose between them; unit `unit.ampere` (lines 519–525 and 546–551) versus `amperage-mA`, with no conversion on these rows; catalog range 0 through coefficient `1` exponent 3 (`definitions.go` lines 43–44); subject `resource.connector` | lines 718–723 |
| MaximumDischargeCurrent | attribute | 0x0008 | amperage-mA int64; nonvolatile; `min 0` | V2X | — | none in catalog ( `evse.limit.maximum_discharge_current`) | absent | no row | no source | no catalog discharge-current element | lines 726–731 |
| UserMaximumChargeCurrent | attribute | 0x0009 | amperage-mA int64; nonvolatile; constraint `desc`; default `float64(0)` | O | — | none in catalog ( `evse.limit.user_maximum_charge_current`, `evse.operation.set_user_maximum_charge_current`) | absent | no row | no source | no catalog element; access RW, read View, write Manage | lines 734–740 |
| RandomizationDelayWindow | attribute | 0x000A | elapsed-s uint32; nonvolatile; constraint `max 86400`; default `float64(600)` | O | — | none in catalog ( `evse.configuration.randomization_delay_window`, `evse.operation.set_randomization_delay_window`) | absent | no row | no source | no catalog duration; access RW, read View, write Manage | lines 743–749 |
| NextChargeStartTime | attribute | 0x0023 | epoch-s uint32; nullable | PREF | — | none in catalog ( `evse.target.next_start`) | absent | no row | no source | no catalog timestamp; feature PREF text is M | lines 752–756, 661 |
| NextChargeTargetTime | attribute | 0x0024 | epoch-s uint32; nullable | PREF | — | none in catalog ( `evse.target.next_target_time`) | absent | no row | no source | same as NextChargeStartTime | lines 759–763 |
| NextChargeRequiredEnergy | attribute | 0x0025 | energy-mWh int64; nullable; `min 0`; catalog canonical unit `evse.energy.session` `unit.joule` | PREF | — | none in catalog ( `evse.target.next_required_energy`) | absent | no row | no source | no catalog target energy; `evse.energy.session` is session energy, not a target | lines 766–771 |
| NextChargeTargetSoC | attribute | 0x0026 | percent uint8; nullable; `max 100`; catalog canonical unit `storage.state.soc` `unit.ratio` | PREF | — | none in catalog ( `evse.target.next_state_of_charge`) | absent | no row | no source | no catalog percent; `storage.state.soc` is a storage-pack fact and is not named here | lines 774–779 |
| ApproximateEvEfficiency | attribute | 0x0027 | uint16; nullable; nonvolatile; constraint `desc`; default `spec.NullDefault{}` | [PREF] | — | none in catalog ( `evse.operation.set_vehicle_efficiency`, `evse.vehicle.approximate_efficiency`) | absent | no row | no source | no unit on the attribute and no catalog element; access RW, read View, write Manage | lines 782–788 |
| StateOfCharge | attribute | 0x0030 | percent uint8; nullable; `max 100` | SOC | — | none in catalog ( `evse.vehicle.state_of_charge`, `evse.service.vehicle`, `resource.vehicle`) | absent | no row | no source | `resource.vehicle` is absent from the catalog (`git grep` of `"id": "resource.vehicle"` found no line) | lines 791–796 |
| BatteryCapacity | attribute | 0x0031 | energy-mWh int64; nullable; `min 0` | SOC | — | none in catalog ( `evse.vehicle.battery_capacity`) | absent | no row | no source | no catalog capacity | lines 799–804 |
| VehicleId | attribute | 0x0032 | string; nullable; `max 32` | PNC | — | none in catalog ( `evse.vehicle.identifier`, `evse.dimension.vehicle`, `resource.vehicle`) | absent | no row | no source | no catalog vehicle id | lines 807–812 |
| SessionId | attribute | 0x0040 | uint32; nullable; nonvolatile | M | EE | none in catalog ( `evse.session.identifier`) | absent | no row | no source | `evse.dimension.session` is a dimension whose semreg value kind is `ValueText` (`definitions.go` line 53), not a uint32 | lines 815–819 |
| SessionDuration | attribute | 0x0041 | elapsed-s uint32; nullable; nonvolatile; quieter | M | EE | none in catalog ( `evse.session.duration`, `evse.session.start`) | absent | no row | no source | no catalog duration | lines 822–826 |
| SessionEnergyCharged | attribute | 0x0042 | energy-mWh int64; nullable; nonvolatile; quieter; `min 0`; catalog canonical unit `evse.energy.session` `unit.joule` | M | EE | `evse.energy.session` partial | present (line 86) | unknown / `matter.unmapped.v1` (row 14); JSON lines 577–581, loss kind `policy` | defined | unit `unit.joule` (pack-metadata lines 465–474) versus `energy-mWh`, and this row declares no scale; catalog range coefficient `0` exponent 0 through coefficient `36` exponent 17 (`definitions.go` line 41); direction `non_negative`, aggregation `member`, subject `resource.charging_session`; the fact does not split charge from discharge; attribute is nullable | lines 829–834 |
| SessionEnergyDischarged | attribute | 0x0043 | energy-mWh int64; nullable; nonvolatile; quieter; `min 0`; catalog canonical unit `evse.energy.session` `unit.joule` | V2X | — | none in catalog ( `evse.energy.session_discharged`) | absent | no row | no source | `evse.energy.session` is one non-negative session quantity and is not named as the discharge split | lines 837–842 |
| GetTargetsResponse | command | 0x00 | response; access RW, read View, write Operate | PREF | — | none in catalog | absent | no row | no source | response payload; a prior accounting marks the response absent and names no id for it | lines 847–849 |
| GetTargetsResponse.ChargingTargetSchedules | field | 0 | list of ChargingTargetScheduleStruct; constraint `max 7`; decoder `DecodeListIn` 0..7 | M | EE-in | none in catalog ( on SetTargets as `evse.dimension.target_schedule`) | absent | no row | no source | M inside GetTargetsResponse, whose text is PREF; decoder minimum 0 is not in the constraint text | lines 851, 326 |
| ChargingTargetSchedules.DayOfWeekForSequence | field | 0 | TargetDayOfWeekBitmap map8 | M | EE-in | none in catalog ( `evse.target.days`) | absent | no row | no source | bitmap members Sunday..Saturday, each M | lines 118, 141–148 |
| ChargingTargetSchedules.ChargingTargets | field | 1 | list of ChargingTargetStruct; constraint `max 10` | M | EE-in | none in catalog ( `evse.dimension.target`) | absent | no row | no source | line 110 calls `DecodeList` with no upper argument; constraint text `max 10` is on the field (line 119); the comment at line 109 leaves that bound out of this decoder | lines 119, 109–110 |
| ChargingTargets.TargetTimeMinutesPastMidnight | field | 0 | uint16; constraint `max 1439`; decoder 0..1439 | M | EE-in | none in catalog ( `evse.target.time_of_day`) | absent | no row | no source | decoder minimum 0 is not in the constraint text | lines 180, 170 |
| ChargingTargets.TargetSoC | field | 1 | percent uint8; constraint `max 100`; default `float64(0)`; decoder optional 0..100 | SOC, O.a+ | — | none in catalog ( `evse.target.state_of_charge`) | absent | no row | no source | choice `a`, num 1, OrMore true, OrLess false, beside the name SOC | line 181 |
| ChargingTargets.AddedEnergy | field | 2 | energy-mWh int64; constraint `min 0`; default `float64(0)`; decoder optional 0..max int64 | [SOC], O.a+ | — | none in catalog ( `evse.target.added_energy`) | absent | no row | no source | same choice `a` as TargetSoC, under optional-if SOC | line 182 |
| Disable | command | 0x01 | request, response `status`; timed; read Operate, write Operate; payload struct empty; catalog canonical unit `evse.limit.allocated_current` `unit.ampere` | M | EE | none in catalog ( `evse.operation.set_supply`) | absent | no row | no source | `evse.operation.set_allocated_current` takes `evse.limit.allocated_current` and is named on EnableCharging, not here | lines 856–860, 336 |
| EnableCharging | command | 0x02 | request, response `status`; timed; Operate / Operate; catalog canonical unit `evse.limit.allocated_current` `unit.ampere` | M | EE | `evse.operation.set_allocated_current` candidate | present (line 92) | unknown / `matter.unmapped.v1` (row 20) | defined | the operation's argument is one current fact; the command has an until-timestamp, a minimum, and a maximum; effect rule writes `evse.limit.allocated_current` (catalog line 84) | lines 863–866; operation attributes in the catalog record |
| EnableCharging.ChargingEnabledUntil | field | 0 | epoch-s uint32; nullable | M | EE-in | none in catalog ( `evse.limit.charging_enabled_until`) | absent | no row | no source | M inside EnableCharging | line 868 |
| EnableCharging.MinimumChargeCurrent | field | 1 | amperage-mA int64; `min 0`; decoder 0..max int64 | M | EE-in | none in catalog ( `evse.limit.minimum_charge_current`) | absent | no row | no source | no catalog minimum | lines 869, 367 |
| EnableCharging.MaximumChargeCurrent | field | 2 | amperage-mA int64; `min 0`; decoder 0..max int64; catalog canonical unit `evse.limit.advertised_current` `unit.ampere`, `evse.limit.allocated_current` `unit.ampere` | M | EE-in | `evse.limit.advertised_current` candidate; `evse.limit.allocated_current` candidate | present (lines 88, 89) | unknown / `matter.unmapped.v1` (rows 16, 17) | defined | same pair and the same unit loss as attribute MaximumChargeCurrent; the operation argument is the allocated fact only | lines 870, 368 |
| EnableDischarging | command | 0x03 | request, response `status`; timed; Operate / Operate | V2X | — | none in catalog ( `evse.operation.set_supply`) | absent | no row | no source | no discharge operation in the catalog | lines 875–878 |
| EnableDischarging.DischargingEnabledUntil | field | 0 | epoch-s uint32; nullable | M | EE-in | none in catalog ( `evse.limit.discharging_enabled_until`) | absent | no row | no source | M inside a V2X command | line 880 |
| EnableDischarging.MaximumDischargeCurrent | field | 1 | amperage-mA int64; `min 0`; decoder 0..max int64 | M | EE-in | none in catalog ( `evse.limit.maximum_discharge_current`) | absent | no row | no source | no catalog discharge current | lines 881, 390 |
| StartDiagnostics | command | 0x04 | request, response `status`; timed; Operate / Operate; payload empty | O | — | none in catalog ( `evse.operation.set_supply`) | absent | no row | no source | empty payload | lines 886–889, 395 |
| SetTargets | command | 0x05 | request, response `status`; timed; Operate / Operate | PREF | — | none in catalog ( `evse.operation.set_target`, `evse.dimension.target`, `evse.dimension.target_schedule`, `evse.target.added_energy`, `evse.target.days`, `evse.target.state_of_charge`, `evse.target.time_of_day`) | absent | no row | no source | one field, tabulated on the next row; nested schedule fields are the rows above | lines 893–900 |
| SetTargets.ChargingTargetSchedules | field | 0 | list of ChargingTargetScheduleStruct; constraint `max 7`; decoder `DecodeListIn` 0..7 | M | EE-in | none in catalog ( `evse.dimension.target_schedule`) | absent | no row | no source | M inside SetTargets, whose text is PREF; same struct as GetTargetsResponse field 0; decoder at line 423 | line 898 |
| GetTargets | command | 0x06 | request, response `GetTargetsResponse`; timed; Operate / Operate; payload empty | PREF | — | none in catalog ( `evse.target.schedule_count`) | absent | no row | no source | empty request | lines 903–907, 428 |
| ClearTargets | command | 0x07 | request, response `status`; timed; Operate / Operate; payload empty | PREF | — | none in catalog ( `evse.operation.clear_targets`, `evse.target.schedule_count`) | absent | no row | no source | empty request | lines 910–914, 440 |
| EvConnected | event | 0x00 | info; Read / View | M | EE | none in catalog ( `evse.event.ev_connected`) | absent | no row | no source | one field | lines 919–921 |
| EvConnected.SessionId | field | 0 | uint32 | M | EE-in | none in catalog ( `evse.session.identifier`) | absent | no row | no source | M inside the event | line 923 |
| EvNotDetected | event | 0x01 | info; Read / View | M | EE | none in catalog ( `evse.event.ev_not_detected`) | absent | no row | no source | five fields | lines 928–930 |
| EvNotDetected.SessionId | field | 0 | uint32 | M | EE-in | none in catalog ( `evse.session.identifier`) | absent | no row | no source | no uint32 session id in the catalog | line 932 |
| EvNotDetected.State | field | 1 | StateEnum; catalog canonical unit `evse.status.connection` none, `evse.status.charging` none | M | EE-in | `evse.status.connection` candidate; `evse.status.charging` candidate | present (lines 110, 109) | unknown / `matter.unmapped.v1` (rows 32, 31) | defined | same enumeration loss as attribute State; this field is the value carried on the event | line 933 |
| EvNotDetected.SessionDuration | field | 2 | elapsed-s uint32 | M | EE-in | none in catalog ( `evse.session.duration`) | absent | no row | no source | no catalog duration | line 934 |
| EvNotDetected.SessionEnergyCharged | field | 3 | energy-mWh int64; `min 0`; decoder 0..max int64; catalog canonical unit `evse.energy.session` `unit.joule` | M | EE-in | `evse.energy.session` candidate | present (line 86) | unknown / `matter.unmapped.v1` (row 14) | defined | same unit and session-scope loss as the attribute; the field is one sample on the event | lines 935, 498 |
| EvNotDetected.SessionEnergyDischarged | field | 4 | energy-mWh int64; `min 0`; optional in the decoder | V2X | — | none in catalog ( `evse.energy.session_discharged`) | absent | no row | no source | discharge split has no catalog element | lines 936, 499 |
| EnergyTransferStarted | event | 0x02 | info; Read / View | M | EE | none in catalog ( `evse.event.energy_transfer_started`) | absent | no row | no source | four fields | lines 941–943 |
| EnergyTransferStarted.SessionId | field | 0 | uint32 | M | EE-in | none in catalog ( `evse.session.identifier`) | absent | no row | no source | no uint32 session id | line 945 |
| EnergyTransferStarted.State | field | 1 | StateEnum; catalog canonical unit `evse.status.connection` none, `evse.status.charging` none | M | EE-in | `evse.status.connection` candidate; `evse.status.charging` candidate | present (lines 110, 109) | unknown / `matter.unmapped.v1` (rows 32, 31) | defined | same enumeration loss as attribute State | line 946 |
| EnergyTransferStarted.MaximumCurrent | field | 2 | amperage-mA int64; `min 0`; decoder 0..max int64; catalog canonical unit `evse.limit.advertised_current` `unit.ampere`, `evse.limit.allocated_current` `unit.ampere` | M | EE-in | `evse.limit.advertised_current` candidate; `evse.limit.allocated_current` candidate | present (lines 88, 89) | unknown / `matter.unmapped.v1` (rows 16, 17) | defined | same pair and unit loss as attribute MaximumChargeCurrent; the field is the current carried on the event | lines 947, 526 |
| EnergyTransferStarted.MaximumDischargeCurrent | field | 3 | amperage-mA int64; `min 0`; optional in the decoder | V2X | — | none in catalog ( `evse.limit.maximum_discharge_current`) | absent | no row | no source | no catalog discharge current | lines 948, 527 |
| EnergyTransferStopped | event | 0x03 | info; Read / View | M | EE | none in catalog ( `evse.event.energy_transfer_stopped`) | absent | no row | no source | field ids 0, 1, 2, 4, 5; no field 3 | lines 953–955 |
| EnergyTransferStopped.SessionId | field | 0 | uint32 | M | EE-in | none in catalog ( `evse.session.identifier`) | absent | no row | no source | no uint32 session id | line 957 |
| EnergyTransferStopped.State | field | 1 | StateEnum; catalog canonical unit `evse.status.connection` none, `evse.status.charging` none | M | EE-in | `evse.status.connection` candidate; `evse.status.charging` candidate | present (lines 110, 109) | unknown / `matter.unmapped.v1` (rows 32, 31) | defined | same enumeration loss as attribute State | line 958 |
| EnergyTransferStopped.Reason | field | 2 | EnergyTransferStoppedReasonEnum | M | EE-in | none in catalog | absent | no row | no source | three reason values, each M; no catalog reason element | line 959 |
| EnergyTransferStopped.EnergyTransferred | field | 4 | energy-mWh int64; `min 0`; decoder 0..max int64; catalog canonical unit `evse.energy.session` `unit.joule` | M | EE-in | `evse.energy.session` candidate | present (line 86) | unknown / `matter.unmapped.v1` (row 14) | defined | unit `unit.joule` versus `energy-mWh` with no scale on the row; the fact does not say transferred versus charged | lines 960, 557 |
| EnergyTransferStopped.EnergyDischarged | field | 5 | energy-mWh int64; `min 0`; optional in the decoder | V2X | — | none in catalog ( `evse.energy.session_discharged`) | absent | no row | no source | no catalog discharge energy | lines 961, 558 |
| Fault | event | 0x04 | critical; Read / View | M | EE | none in catalog ( `evse.event.fault`) | absent | no row | no source | field ids 0, 1, 2, 4; no field 3 | lines 966–968 |
| Fault.SessionId | field | 0 | uint32; nullable | M | EE-in | none in catalog ( `evse.session.identifier`) | absent | no row | no source | nullable uint32; catalog session dimension is text | line 970 |
| Fault.State | field | 1 | StateEnum; catalog canonical unit `evse.status.connection` none, `evse.status.charging` none | M | EE-in | `evse.status.connection` candidate; `evse.status.charging` candidate | present (lines 110, 109) | unknown / `matter.unmapped.v1` (rows 32, 31) | defined | same enumeration loss as attribute State | line 971 |
| Fault.FaultStatePreviousState | field | 2 | FaultStateEnum; catalog canonical unit `evse.status.fault` none | M | EE-in | `evse.status.fault` candidate | present (line 111) | unknown / `matter.unmapped.v1` (row 33) | defined | symbols `evse.status.fault.clear`, `evse.status.fault.present` versus the cause enum; the field is the previous value | line 972 |
| Fault.FaultStateCurrentState | field | 4 | FaultStateEnum; catalog canonical unit `evse.status.fault` none | M | EE-in | `evse.status.fault` candidate | present (line 111) | unknown / `matter.unmapped.v1` (row 33) | defined | same symbol loss; the field is the current value | line 973 |
| Rfid | event | 0x05 | info; Read / View | [RFID] | — | none in catalog ( `evse.event.rfid`, `evse.session.rfid_token`) | absent | no row | no source | optional-if the name RFID | lines 978–980 |
| Rfid.Uid | field | 0 | octstr; constraint `max 10`; decoder 0..10 | M | EE-in | none in catalog ( `evse.session.rfid_token`) | absent | no row | no source | M inside an event whose text is `[RFID]`; decoder minimum 0 is not in the constraint text | lines 982, 605 |

### EnergyEvseMode

Cluster id `0x009D` (157), name `EnergyEvseMode`, revision 2, `Base` `ModeBase` (lines 22–26, 248; `schema.json` cluster id 157). No events. Feature bit is separate from global `AttrFeatureMap`.

ModeTag (enum16, lines 167–184) has no `Conformance` on each `EnumValue`. Values: `Auto` 0, `Quick` 1, `Quiet` 2, `LowNoise` 3, `LowEnergy` 4, `Vacation` 5, `Min` 6, `Max` 7, `Night` 8, `Day` 9, `Manual` 16384, `TimeOfUse` 16385, `SolarCharging` 16386, `V2X` 16387. Range `MfgTags` 32768..49151.

ModeChangeStatus (enum8, lines 68–75) has no `Conformance` on each value: `Success` 0, `UnsupportedMode` 1, `GenericFailure` 2, `InvalidInMode` 3. Range `MfgCodes` 128..191.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEPONOFF OnOff | feature | bit 0 | FeatureMap bit | X | — | none in catalog | absent | no row | no source | `Op` is `ConfDisallowed` | lines 49, 250 |
| SupportedModes | attribute | 0x0000 | list of ModeOptionStruct; fixed; constraint `2 to 255`; decoder 2..255 | M | EE | none in catalog ( `evse.mode_supported`) | absent | no row | no source | access Read / View | lines 254–260 |
| SupportedModes.Label | field | 0 | string; fixed; `max 64`; decoder 0..64 | M | EE-in | none in catalog | absent | no row | no source | M inside SupportedModes | lines 106, 96 |
| SupportedModes.Mode | field | 1 | uint8; fixed | M | EE-in | none in catalog | absent | no row | no source | mode index, not a ModeTag | line 107 |
| SupportedModes.ModeTags | field | 2 | list of ModeTagStruct; fixed; `1 to 8`; decoder 1..8 | M | EE-in | none in catalog | absent | no row | no source | M inside SupportedModes | lines 108, 98 |
| ModeTags.MfgCode | field | 0 | vendor-id uint16; constraint `desc` | O | — | none in catalog | absent | no row | no source | optional manufacturer code | line 137 |
| ModeTags.Value | field | 1 | ModeTag enum16 | M | EE-in | none in catalog ( `evse.mode`) | absent | no row | no source | device-specific values Manual, TimeOfUse, SolarCharging, V2X plus the shared 0..9 values; no Conformance on the values | lines 138, 167–184 |
| CurrentMode | attribute | 0x0001 | uint8; nonvolatile; constraint `desc` | M | EE | none in catalog ( `evse.mode`) | absent | no row | no source | index into SupportedModes, not the ModeTag value itself | lines 263–268 |
| StartUpMode | attribute | 0x0002 | uint8; nullable; nonvolatile; constraint `desc` | X | — | none in catalog | absent | no row | no source | `Op` `ConfDisallowed`; access RW, read View, write Operate | lines 271–276 |
| OnMode | attribute | 0x0003 | uint8; nullable; nonvolatile; constraint `desc` | X | — | none in catalog | absent | no row | no source | same access and `ConfDisallowed` as StartUpMode | lines 279–284 |
| ChangeToMode | command | 0x00 | request, response `ChangeToModeResponse`; read Operate, write Operate | M | EE | none in catalog ( `evse.operation.set_evse_mode`) | absent | no row | no source | not marked timed | lines 289–292 |
| ChangeToMode.NewMode | field | 0 | uint8; constraint `desc` | M | EE-in | none in catalog | absent | no row | no source | decoder is `DecodeUint` with no numeric bound (line 201) | line 294 |
| ChangeToModeResponse | command | 0x01 | response; access RW, read View, write Operate | M | EE | none in catalog | absent | no row | no source | a prior accounting marks the response absent and names no id | lines 299–301 |
| ChangeToModeResponse.Status | field | 0 | ModeChangeStatus enum8; constraint `desc` | M | EE-in | none in catalog | absent | no row | no source | values have no Conformance field; range MfgCodes 128..191 | lines 303, 68–75 |
| ChangeToModeResponse.StatusText | field | 1 | string; constraint `max 64`; decoder 0..64 | [Status == Success], M | EE-in | none in catalog | absent | no row | no source | otherwise of optional-if `Status == Success`, then mandatory | lines 304, 223 |

### DeviceEnergyManagement

Cluster id `0x0098` (152), name `DeviceEnergyManagement`, revision 4 (lines 22–26; `schema.json` lines 73611–73613). No command in this cluster sets `Timed`. Attribute access is Read / View. Command access is Read Operate, write Operate, response `status`, except where a row says the payload is empty.

ESATypeEnum (enum8, lines 275–291), every value `O`: `Evse` 0, `SpaceHeating` 1, `WaterHeating` 2, `SpaceCooling` 3, `SpaceHeatingCooling` 4, `BatteryStorage` 5, `SolarPv` 6, `FridgeFreezer` 7, `WashingMachine` 8, `Dishwasher` 9, `Cooking` 10, `HomeWaterPump` 11, `IrrigationWaterPump` 12, `PoolPump` 13, `Other` 255.

ESAStateEnum (enum8, lines 240–246): `Offline` 0 M, `Online` 1 M, `Fault` 2 M, `PowerAdjustActive` 3 `PA`, `Paused` 4 `PAU`.

OptOutStateEnum (enum8, lines 482–487), every value M: `NoOptOut` 0, `LocalOptOut` 1, `GridOptOut` 2, `OptOut` 3.

AdjustmentCauseEnum (enum8, lines 90–93), every value M: `LocalOptimization` 0, `GridOptimization` 1.

CauseEnum (enum8, lines 112–118), every value M: `NormalCompletion` 0, `Offline` 1, `Fault` 2, `UserOptOut` 3, `Cancelled` 4.

PowerAdjustReasonEnum (enum8, lines 572–576), every value M: `NoAdjustment` 0, `LocalOptimizationAdjustment` 1, `GridOptimizationAdjustment` 2.

ForecastUpdateReasonEnum (enum8, lines 460–464), every value M: `InternalOptimization` 0, `LocalOptimization` 1, `GridOptimization` 2.

CostTypeEnum (enum8, lines 216–221), every value M: `Financial` 0, `GhgEmissions` 1, `Comfort` 2, `Temperature` 3.

On device type EnergyEvse, `schema.json` effective requirements set feature PFR conformance text to `M` and feature PA conformance text to `desc` (lines 18365–18391). That override is not in `go-fabric@v0.22.2:device/energy_evse_gen.go` and is not the cluster definition's own feature text. The mandatory column uses the cluster text and the device file.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PA PowerAdjustment | feature | bit 0 | FeatureMap bit | O | — | none in catalog ( `energy.esa.adjustment_maximum_duration`, `energy.esa.adjustment_maximum_power`, `energy.esa.adjustment_minimum_duration`, `energy.esa.adjustment_minimum_power`) | absent | no row | no source | device-type effective text on 1293 is `[ControllableEsa].a+`; on EnergyEvse's composed DEM the effective text is `desc` | lines 67, 902; schema lines 18529–18545 and 18379–18386 |
| PFR PowerForecastReporting | feature | bit 1 | FeatureMap bit | [!PA].a, STA \| PAU \| FA \| CON, O | — | none in catalog ( the `energy.series.slot_*` ids listed on this feature in a prior accounting) | absent | no row | no source | choice `a` num 1, OrMore false, OrLess false, of optional-if not PA; then the or of STA, PAU, FA, CON; then optional. On EnergyEvse's composed DEM the effective text is `M` | line 903; schema lines 18367–18372 |
| SFR StateForecastReporting | feature | bit 2 | FeatureMap bit | [!PA].a | — | none in catalog ( the same `energy.series.slot_*` group) | absent | no row | no source | same choice `a` as PFR: num 1, OrMore false, optional-if not PA | line 904 |
| STA StartTimeAdjustment | feature | bit 3 | FeatureMap bit | O | — | none in catalog ( `energy.series.earliest_start`) | absent | no row | no source | device-type 1293 effective text is `[ControllableEsa].a+` | lines 70, 905 |
| PAU Pausable | feature | bit 4 | FeatureMap bit | O | — | none in catalog ( `energy.series.pausable`) | absent | no row | no source | device-type 1293 effective text is `[ControllableEsa].a+` | lines 71, 906 |
| FA ForecastAdjustment | feature | bit 5 | FeatureMap bit | O | — | none in catalog | absent | no row | no source | device-type 1293 effective text is `[ControllableEsa].a+`; a prior accounting names no separate id beyond the slot-adjustment group on PFR | lines 72, 907 |
| CON ConstraintBasedAdjustment | feature | bit 6 | FeatureMap bit | O | — | none in catalog | absent | no row | no source | device-type 1293 effective text is `[ControllableEsa].a+` | lines 73, 908 |
| EsaType | attribute | 0x0000 | ESATypeEnum enum8; fixed | M | DEM | none in catalog ( `energy.dimension.subject`, `energy.esa.type`) | absent | no row | no source | every enum value text is O | lines 912–916 |
| EsaCanGenerate | attribute | 0x0001 | bool; fixed | M | DEM | none in catalog ( `energy.esa.can_generate`) | absent | no row | no source | no catalog bool | lines 919–923 |
| EsaState | attribute | 0x0002 | ESAStateEnum enum8; constraint `desc` | M | DEM | none in catalog ( `energy.esa.state`, `energy.service.subject`) | absent | no row | no source | values PowerAdjustActive and Paused are feature-conditioned | lines 926–930 |
| AbsMinPower | attribute | 0x0003 | power-mW int64 | M | DEM | none in catalog ( `energy.esa.minimum_power`) | absent | no row | no source | no catalog power bound for this attribute; no constraint text on the attribute | lines 933–936 |
| AbsMaxPower | attribute | 0x0004 | power-mW int64; constraint `min absMinPower` | M | DEM | none in catalog ( `energy.esa.maximum_power`) | absent | no row | no source | minimum is a reference to AbsMinPower | lines 939–943 |
| PowerAdjustmentCapability | attribute | 0x0005 | PowerAdjustCapabilityStruct; nullable; quieter | PA | — | none in catalog ( `energy.dimension.adjustment_range`, `energy.esa.adjustment_cause`, and the four `energy.esa.adjustment_*` ids) | absent | no row | no source | decoder returns nil on TLV null (the decode func above line 899) | lines 946–951 |
| PowerAdjustmentCapability.PowerAdjustCapability | field | 0 | list of PowerAdjustStruct; nullable; constraint `max 8`; decoder 0..8 | M | DEM-in | none in catalog ( `energy.dimension.adjustment_range`) | absent | no row | no source | M inside an attribute whose text is PA; decoder minimum 0 is not in the constraint text | lines 515, 506 |
| PowerAdjustmentCapability.Cause | field | 1 | PowerAdjustReasonEnum | M | DEM-in | none in catalog ( `energy.esa.adjustment_cause`) | absent | no row | no source | three reason values, each M | line 516 |
| PowerAdjustStruct.MinPower | field | 0 | power-mW int64 | M | DEM-in | none in catalog ( `energy.esa.adjustment_minimum_power`) | absent | no row | no source | no constraint text | line 551 |
| PowerAdjustStruct.MaxPower | field | 1 | power-mW int64; constraint `min minPower` | M | DEM-in | none in catalog ( `energy.esa.adjustment_maximum_power`) | absent | no row | no source | minimum references MinPower | line 552 |
| PowerAdjustStruct.MinDuration | field | 2 | elapsed-s uint32 | M | DEM-in | none in catalog ( `energy.esa.adjustment_minimum_duration`) | absent | no row | no source | no constraint text | line 553 |
| PowerAdjustStruct.MaxDuration | field | 3 | elapsed-s uint32; constraint `min minDuration` | M | DEM-in | none in catalog ( `energy.esa.adjustment_maximum_duration`) | absent | no row | no source | minimum references MinDuration | line 554 |
| Forecast | attribute | 0x0006 | ForecastStruct; nullable; quieter | PFR \| SFR | — | none in catalog ( `energy.dimension.series`, `energy.dimension.slot`, and the `energy.series.*` ids in the a prior accounting Forecast cell) | absent | no row | no source | `git grep` of `energy.series.` and `energy.esa.` in the catalog found no line; decoder returns nil on TLV null (lines 891–895) | lines 954–959 |
| Forecast.ForecastId | field | 0 | uint32 | M | DEM-in | none in catalog ( `energy.series.identifier`) | absent | no row | no source | M inside Forecast | line 340 |
| Forecast.ActiveSlotNumber | field | 1 | uint16; nullable | M | DEM-in | none in catalog | absent | no row | no source | a prior accounting's slot list has no separate id that this note assigns to this field | line 341 |
| Forecast.StartTime | field | 2 | epoch-s uint32 | M | DEM-in | none in catalog ( `energy.series.start`) | absent | no row | no source | M inside Forecast | line 342 |
| Forecast.EndTime | field | 3 | epoch-s uint32 | M | DEM-in | none in catalog ( `energy.series.end`) | absent | no row | no source | M inside Forecast | line 343 |
| Forecast.EarliestStartTime | field | 4 | epoch-s uint32; nullable; decoder optional nullable | STA | — | none in catalog ( `energy.series.earliest_start`) | absent | no row | no source | optional in the Go struct (`*spec.Nullable`) | lines 344, 328 |
| Forecast.LatestEndTime | field | 5 | epoch-s uint32 | STA | — | none in catalog ( `energy.series.latest_end`) | absent | no row | no source | optional in the Go struct | line 345 |
| Forecast.IsPausable | field | 6 | bool | M | DEM-in | none in catalog ( `energy.series.pausable`) | absent | no row | no source | M inside Forecast | line 346 |
| Forecast.Slots | field | 7 | list of SlotStruct; constraint `max 10`; decoder 0..10 | M | DEM-in | none in catalog ( `energy.dimension.slot`) | absent | no row | no source | decoder minimum 0 is not in the constraint text | lines 347, 331 |
| Forecast.ForecastUpdateReason | field | 8 | ForecastUpdateReasonEnum | M | DEM-in | none in catalog ( `energy.series.update_reason`) | absent | no row | no source | three values, each M | line 348 |
| Slot.MinDuration | field | 0 | elapsed-s uint32 | M | DEM-in | none in catalog ( `energy.series.slot_minimum_duration`) | absent | no row | no source | M inside SlotStruct | line 425 |
| Slot.MaxDuration | field | 1 | elapsed-s uint32 | M | DEM-in | none in catalog ( `energy.series.slot_maximum_duration`) | absent | no row | no source | M inside SlotStruct | line 426 |
| Slot.DefaultDuration | field | 2 | elapsed-s uint32 | M | DEM-in | none in catalog ( `energy.series.slot_default_duration`) | absent | no row | no source | M inside SlotStruct | line 427 |
| Slot.ElapsedSlotTime | field | 3 | elapsed-s uint32 | M | DEM-in | none in catalog ( `energy.series.slot_elapsed`) | absent | no row | no source | M inside SlotStruct | line 428 |
| Slot.RemainingSlotTime | field | 4 | elapsed-s uint32 | M | DEM-in | none in catalog ( `energy.series.slot_remaining`) | absent | no row | no source | M inside SlotStruct | line 429 |
| Slot.SlotIsPausable | field | 5 | bool | PAU | — | none in catalog ( `energy.series.slot_pausable`) | absent | no row | no source | optional in the Go struct | line 430 |
| Slot.MinPauseDuration | field | 6 | elapsed-s uint32 | PAU | — | none in catalog ( `energy.series.slot_minimum_pause`) | absent | no row | no source | optional in the Go struct | line 431 |
| Slot.MaxPauseDuration | field | 7 | elapsed-s uint32 | PAU | — | none in catalog ( `energy.series.slot_maximum_pause`) | absent | no row | no source | optional in the Go struct | line 432 |
| Slot.ManufacturerEsaState | field | 8 | uint16 | SFR | — | none in catalog ( `energy.series.slot_state`) | absent | no row | no source | the proposed id is one cell in the a prior accounting group; this note does not treat that name as a proven field match | line 433 |
| Slot.NominalPower | field | 9 | power-mW int64 | PFR | — | none in catalog ( `energy.series.slot_power_nominal`) | absent | no row | no source | no catalog power | line 434 |
| Slot.MinPower | field | 10 | power-mW int64 | PFR | — | none in catalog ( `energy.series.slot_power_minimum`) | absent | no row | no source | no catalog power | line 435 |
| Slot.MaxPower | field | 11 | power-mW int64 | PFR | — | none in catalog ( `energy.series.slot_power_maximum`) | absent | no row | no source | no catalog power | line 436 |
| Slot.NominalEnergy | field | 12 | energy-mWh int64 | PFR | — | none in catalog ( `energy.series.slot_energy_nominal`) | absent | no row | no source | no catalog energy | line 437 |
| Slot.Costs | field | 13 | list of CostStruct; constraint `max 5`; decoder 0..5 | O | — | none in catalog | absent | no row | no source | a prior accounting Forecast cell does not name a cost id; decoder minimum 0 is not in the constraint text | lines 438, 413 |
| Slot.MinPowerAdjustment | field | 14 | power-mW int64 | FA & PFR | — | none in catalog ( `energy.series.slot_adjustment_minimum_power`) | absent | no row | no source | both feature names | line 439 |
| Slot.MaxPowerAdjustment | field | 15 | power-mW int64 | FA & PFR | — | none in catalog ( `energy.series.slot_adjustment_maximum_power`) | absent | no row | no source | both feature names | line 440 |
| Slot.MinDurationAdjustment | field | 16 | elapsed-s uint32 | FA | — | none in catalog ( `energy.series.slot_adjustment_minimum_duration`) | absent | no row | no source | feature FA | line 441 |
| Slot.MaxDurationAdjustment | field | 17 | elapsed-s uint32 | FA | — | none in catalog ( `energy.series.slot_adjustment_maximum_duration`) | absent | no row | no source | feature FA | line 442 |
| Cost.CostType | field | 0 | CostTypeEnum | M | DEM-in | none in catalog | absent | no row | no source | M inside an optional Costs list | line 194 |
| Cost.Value | field | 1 | int32 | M | DEM-in | none in catalog | absent | no row | no source | no unit on the field | line 195 |
| Cost.DecimalPoints | field | 2 | uint8 | M | DEM-in | none in catalog | absent | no row | no source | scale digits for Value | line 196 |
| Cost.Currency | field | 3 | uint16; constraint `max 999`; default `float64(0)`; decoder optional 0..999 | O | — | none in catalog | absent | no row | no source | no currency element | lines 197, 186 |
| OptOutState | attribute | 0x0007 | OptOutStateEnum enum8; constraint `desc` | PA \| STA \| PAU \| FA \| CON | — | none in catalog ( `energy.esa.opt_out`) | absent | no row | no source | four values, each M | lines 962–966 |
| PowerAdjustRequest | command | 0x00 | request, response `status`; catalog canonical unit `pv.limit.active_power` `unit.watt` | PA | — | none in catalog ( `energy.operation.adjust_power`, `energy.esa.request_cause`, `energy.esa.requested_duration`, `energy.esa.requested_power`; a prior proposal names `pv.limit.active_power`, `pv.operation.set_active_power_limit`) | absent | no row | no source | `pv.limit.active_power` is a PV-pack fact and is not named as a feed of this command | lines 971–974 |
| PowerAdjustRequest.Power | field | 0 | power-mW int64; constraint `desc` | M | DEM-in | none in catalog ( `energy.esa.requested_power`) | absent | no row | no source | M inside a PA command | line 976 |
| PowerAdjustRequest.Duration | field | 1 | elapsed-s uint32; constraint `desc` | M | DEM-in | none in catalog ( `energy.esa.requested_duration`) | absent | no row | no source | M inside a PA command | line 977 |
| PowerAdjustRequest.Cause | field | 2 | AdjustmentCauseEnum; constraint `desc` | M | DEM-in | none in catalog ( `energy.esa.request_cause`) | absent | no row | no source | two cause values, each M | line 978 |
| CancelPowerAdjustRequest | command | 0x01 | request, response `status`; payload empty | PA | — | none in catalog ( `energy.operation.adjust_power`) | absent | no row | no source | empty struct, lines 638–648 | lines 983–987 |
| StartTimeAdjustRequest | command | 0x02 | request, response `status` | STA | — | none in catalog ( `energy.operation.adjust_start_time`) | absent | no row | no source | two fields | lines 990–993 |
| StartTimeAdjustRequest.RequestedStartTime | field | 0 | epoch-s uint32; constraint `desc` | M | DEM-in | none in catalog ( `energy.series.earliest_start`) | absent | no row | no source | a requested time, not the forecast's earliest start; the proposed id is the one a prior accounting puts on the feature | line 995 |
| StartTimeAdjustRequest.Cause | field | 1 | AdjustmentCauseEnum | M | DEM-in | none in catalog ( `energy.esa.request_cause`) | absent | no row | no source | no constraint text on this field | line 996 |
| PauseRequest | command | 0x03 | request, response `status` | PAU | — | none in catalog ( `energy.operation.set_esa_state`, `energy.esa.requested_duration`) | absent | no row | no source | two fields | lines 1001–1004 |
| PauseRequest.Duration | field | 0 | elapsed-s uint32; constraint `desc` | M | DEM-in | none in catalog ( `energy.esa.requested_duration`) | absent | no row | no source | M inside a PAU command | line 1006 |
| PauseRequest.Cause | field | 1 | AdjustmentCauseEnum | M | DEM-in | none in catalog ( `energy.esa.request_cause`) | absent | no row | no source | no constraint text | line 1007 |
| ResumeRequest | command | 0x04 | request, response `status`; payload empty | PAU | — | none in catalog ( `energy.operation.set_esa_state`) | absent | no row | no source | empty payload | lines 1012–1016 |
| ModifyForecastRequest | command | 0x05 | request, response `status` | FA | — | none in catalog ( `energy.operation.modify_series_slot`) | absent | no row | no source | three fields | lines 1019–1022 |
| ModifyForecastRequest.ForecastId | field | 0 | uint32 | M | DEM-in | none in catalog ( `energy.series.identifier`) | absent | no row | no source | no constraint text | line 1024 |
| ModifyForecastRequest.SlotAdjustments | field | 1 | list of SlotAdjustmentStruct; constraint `max 10` | M | DEM-in | none in catalog ( `energy.operation.modify_series_slot`) | absent | no row | no source | the proposed id is an operation, not a list element | line 1025 |
| ModifyForecastRequest.Cause | field | 2 | AdjustmentCauseEnum | M | DEM-in | none in catalog ( `energy.esa.request_cause`) | absent | no row | no source | no constraint text | line 1026 |
| SlotAdjustment.SlotIndex | field | 0 | uint8; constraint `desc` | M | DEM-in | none in catalog | absent | no row | no source | a prior accounting does not name a slot-index id | line 607 |
| SlotAdjustment.NominalPower | field | 1 | power-mW int64; constraint `desc` | PFR | — | none in catalog ( `energy.series.slot_power_nominal`) | absent | no row | no source | optional in the Go struct | line 608 |
| SlotAdjustment.Duration | field | 2 | elapsed-s uint32; constraint `desc` | M | DEM-in | none in catalog ( `energy.series.slot_duration`) | absent | no row | no source | M inside the adjustment struct | line 609 |
| RequestConstraintBasedForecast | command | 0x06 | request, response `status` | CON | — | none in catalog ( `energy.operation.modify_series_slot`) | absent | no row | no source | two fields | lines 1031–1034 |
| RequestConstraintBasedForecast.Constraints | field | 0 | list of ConstraintsStruct; constraint `max 10` | M | DEM-in | none in catalog | absent | no row | no source | no separate proposed id for the list | line 1036 |
| RequestConstraintBasedForecast.Cause | field | 1 | AdjustmentCauseEnum | M | DEM-in | none in catalog ( `energy.esa.request_cause`) | absent | no row | no source | no constraint text | line 1037 |
| Constraints.StartTime | field | 0 | epoch-s uint32; constraint `desc` | M | DEM-in | none in catalog | absent | no row | no source | no proposed id that names this field alone | line 155 |
| Constraints.Duration | field | 1 | elapsed-s uint32; constraint `max 86400`; decoder 0..86400 | M | DEM-in | none in catalog | absent | no row | no source | decoder minimum 0 is not in the constraint text | lines 156, 144 |
| Constraints.NominalPower | field | 2 | power-mW int64; constraint `desc` | PFR | — | none in catalog | absent | no row | no source | optional in the Go struct | line 157 |
| Constraints.MaximumEnergy | field | 3 | energy-mWh int64 | PFR | — | none in catalog | absent | no row | no source | no constraint text; optional in the Go struct | line 158 |
| Constraints.LoadControl | field | 4 | int8 | SFR | — | none in catalog | absent | no row | no source | optional in the Go struct; no unit | line 159 |
| CancelRequest | command | 0x07 | request, response `status`; payload empty | STA \| FA \| CON | — | none in catalog ( `energy.operation.modify_series_slot`) | absent | no row | no source | empty payload | lines 1042–1046 |
| PowerAdjustStart | event | 0x00 | info; Read / View; no fields | PA | — | none in catalog ( `energy.event.power_adjust_start`) | absent | no row | no source | decode is registered; the `Fields` slice is absent | lines 1051–1054 |
| PowerAdjustEnd | event | 0x01 | info; Read / View | PA | — | none in catalog ( `energy.event.power_adjust_end`, `energy.esa.adjustment_end_cause`) | absent | no row | no source | three fields | lines 1057–1059 |
| PowerAdjustEnd.Cause | field | 0 | CauseEnum | M | DEM-in | none in catalog ( `energy.esa.adjustment_end_cause`) | absent | no row | no source | five cause values, each M | line 1061 |
| PowerAdjustEnd.Duration | field | 1 | elapsed-s uint32 | M | DEM-in | none in catalog | absent | no row | no source | no proposed duration id on this event | line 1062 |
| PowerAdjustEnd.EnergyUse | field | 2 | energy-mWh int64 | M | DEM-in | none in catalog | absent | no row | no source | no unit conversion and no catalog energy element for this field | line 1063 |
| Paused | event | 0x02 | info; Read / View; no fields | PAU | — | none in catalog ( `energy.event.paused`) | absent | no row | no source | no `Fields` slice | lines 1068–1071 |
| Resumed | event | 0x03 | info; Read / View | PAU | — | none in catalog ( `energy.event.resumed`, `energy.esa.adjustment_end_cause`) | absent | no row | no source | one field | lines 1074–1076 |
| Resumed.Cause | field | 0 | CauseEnum | M | DEM-in | none in catalog ( `energy.esa.adjustment_end_cause`) | absent | no row | no source | same CauseEnum as PowerAdjustEnd.Cause | line 1078 |

### DeviceEnergyManagementMode

Cluster id `0x009F` (159), name `DeviceEnergyManagementMode`, revision 2, `Base` `ModeBase` (lines 22–26, 248). No events. The struct, command, and feature shape matches EnergyEvseMode. ModeTag values differ.

ModeTag (enum16, lines 167–184) has no `Conformance` on each value: `Auto` 0, `Quick` 1, `Quiet` 2, `LowNoise` 3, `LowEnergy` 4, `Vacation` 5, `Min` 6, `Max` 7, `Night` 8, `Day` 9, `NoOptimization` 16384, `DeviceOptimization` 16385, `LocalOptimization` 16386, `GridOptimization` 16387. Range `MfgTags` 32768..49151.

ModeChangeStatus matches EnergyEvseMode: `Success` 0, `UnsupportedMode` 1, `GenericFailure` 2, `InvalidInMode` 3, no per-value Conformance, range `MfgCodes` 128..191 (lines 68–75).

The device file does not set `Mandatory` on this cluster. Rows with conformance text `M` use `if-mounted`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEPONOFF OnOff | feature | bit 0 | FeatureMap bit | X | — | none in catalog | absent | no row | no source | `Op` `ConfDisallowed` | lines 49, 250 |
| SupportedModes | attribute | 0x0000 | list of ModeOptionStruct; fixed; `2 to 255`; decoder 2..255 | M | if-mounted | none in catalog ( `energy.esa.mode_supported`) | absent | no row | no source | Read / View | lines 254–260 |
| SupportedModes.Label | field | 0 | string; fixed; `max 64` | M | if-mounted | none in catalog | absent | no row | no source | M inside SupportedModes | line 106 |
| SupportedModes.Mode | field | 1 | uint8; fixed | M | if-mounted | none in catalog | absent | no row | no source | mode index | line 107 |
| SupportedModes.ModeTags | field | 2 | list of ModeTagStruct; fixed; `1 to 8` | M | if-mounted | none in catalog | absent | no row | no source | M inside SupportedModes | line 108 |
| ModeTags.MfgCode | field | 0 | vendor-id uint16; constraint `desc` | O | — | none in catalog | absent | no row | no source | optional | line 137 |
| ModeTags.Value | field | 1 | ModeTag enum16 | M | if-mounted | none in catalog | absent | no row | no source | device-specific values NoOptimization, DeviceOptimization, LocalOptimization, GridOptimization; shared values Auto..Day; no Conformance on the values | lines 138, 167–184 |
| CurrentMode | attribute | 0x0001 | uint8; nonvolatile; constraint `desc`; catalog canonical unit `thermal.overrun.sg_ready_condition_1` none | M | if-mounted | none in catalog ( `energy.esa.mode`) | absent | no row | no source | a prior accounting also names `thermal.overrun.sg_ready_condition_1`, `_3`, `_4`. Those three ids are present (catalog lines 351–353). Each symbol list is that id plus `.active`, `.finished`, `.inactive`, `.running` (`thermal/definitions.go` lines 102–104 and 125). They are not placed in the feed cell. CurrentMode is a uint8 index | lines 263–268 |
| StartUpMode | attribute | 0x0002 | uint8; nullable; nonvolatile; constraint `desc` | X | — | none in catalog | absent | no row | no source | `ConfDisallowed`; access RW View / Operate | lines 271–276 |
| OnMode | attribute | 0x0003 | uint8; nullable; nonvolatile; constraint `desc` | X | — | none in catalog | absent | no row | no source | same as StartUpMode | lines 279–284 |
| ChangeToMode | command | 0x00 | request, response `ChangeToModeResponse`; Operate / Operate | M | if-mounted | none in catalog ( `energy.operation.set_esa_mode`) | absent | no row | no source | not marked timed | lines 289–292 |
| ChangeToMode.NewMode | field | 0 | uint8; constraint `desc` | M | if-mounted | none in catalog | absent | no row | no source | decoder has no numeric bound (line 201) | line 294 |
| ChangeToModeResponse | command | 0x01 | response; RW View / Operate | M | if-mounted | none in catalog | absent | no row | no source | a prior accounting marks the response absent | lines 299–301 |
| ChangeToModeResponse.Status | field | 0 | ModeChangeStatus; constraint `desc` | M | if-mounted | none in catalog | absent | no row | no source | range MfgCodes 128..191 | line 303 |
| ChangeToModeResponse.StatusText | field | 1 | string; `max 64` | [Status == Success], M | if-mounted | none in catalog | absent | no row | no source | otherwise of optional-if success, then mandatory | line 304 |

### EnergyPreference

Cluster id `0x009B` (155), name `EnergyPreference`, revision 1 (lines 22–26; `schema.json` cluster id 155 at line 78116). No commands. No events. Neither device type of this group lists the cluster, so the mandatory column is `—` on every row.

EnergyPriorityEnum (enum8, lines 94–99), every value M: `Comfort` 0, `Speed` 1, `Efficiency` 2, `WaterConsumption` 3.

Both features use choice `a`, num 1, OrMore true, OrLess false (lines 115–116).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BALA EnergyBalance | feature | bit 0 | FeatureMap bit | O.a+ | — | none in catalog | absent | no row | no source | at least one of the choice with LPMS | lines 44, 115 |
| LPMS LowPowerModeSensitivity | feature | bit 1 | FeatureMap bit | O.a+ | — | none in catalog | absent | no row | no source | same choice `a` | lines 45, 116 |
| EnergyBalances | attribute | 0x0000 | list of BalanceStruct; fixed; constraint `2 to 10`; decoder 2..10 | BALA | — | none in catalog ( `energy.dimension.balance`, `energy.preference.balance_label`, `energy.preference.balance_step`) | absent | no row | no source | Read / View; `git grep` of `energy.preference` in the catalog found no line | lines 120–126 |
| EnergyBalances.Step | field | 0 | percent uint8; fixed; constraint `max 100`; decoder 0..100 | M | — | none in catalog ( `energy.preference.balance_step`) | absent | no row | no source | M inside an attribute whose text is BALA; the attribute is not on a device type of this group | lines 74, 65 |
| EnergyBalances.Label | field | 1 | string; fixed; constraint `max 64`; decoder optional 0..64 | O | — | none in catalog ( `energy.preference.balance_label`) | absent | no row | no source | optional label | lines 75, 66 |
| CurrentEnergyBalance | attribute | 0x0001 | uint8; nonvolatile | BALA | — | none in catalog ( `energy.preference.current_balance`, `energy.operation.set_energy_balance`) | absent | no row | no source | access RW, read View, write Operate; no constraint text | lines 129–133 |
| EnergyPriorities | attribute | 0x0002 | list of EnergyPriorityEnum; fixed; constraint text `2` with `Value` bound 2 | BALA | — | none in catalog ( `energy.preference.priorities`) | absent | no row | no source | four enum values, each M | lines 136–141 |
| LowPowerModeSensitivities | attribute | 0x0003 | list of BalanceStruct; fixed; `2 to 10`; decoder 2..10 | LPMS | — | none in catalog ( `energy.preference.low_power_sensitivity`) | absent | no row | no source | same BalanceStruct as EnergyBalances (lines 73–76) | lines 144–149 |
| CurrentLowPowerModeSensitivity | attribute | 0x0004 | uint8; nonvolatile | LPMS | — | none in catalog ( `energy.preference.low_power_sensitivity`, `energy.operation.set_low_power_sensitivity`) | absent | no row | no source | access RW, read View, write Operate; no constraint text | lines 153–157 |

## 4. Mandatory elements without a source

Included here: an element whose conformance text is `M`, on a cluster the device file marks `Mandatory: true`, and whose feed cell names no catalog id. Feature PREF is included because its own text is `M`. Elements whose text is the name `PREF` are listed separately: the feature text is `M`, and their own text is not `M`.

Field rows marked `EE-in` or `DEM-in` under a parent in these lists also name no catalog id, except where the table cites `evse.status.*`, `evse.limit.advertised_current`, `evse.limit.allocated_current`, or `evse.energy.session`. Those field rows stay in the tables.

### EnergyEvse server, device type EnergyEvse

Attributes: `ChargingEnabledUntil`, `MinimumChargeCurrent`, `SessionId`, `SessionDuration`.

Command: `Disable`. Command fields `EnableCharging.ChargingEnabledUntil` and `EnableCharging.MinimumChargeCurrent` (the command itself has a candidate operation; these two fields do not).

Events: `EvConnected`, `EvNotDetected`, `EnergyTransferStarted`, `EnergyTransferStopped`, `Fault`.

Event fields whose text is `M` and whose feed cell names no catalog id: `EvConnected.SessionId`, `EvNotDetected.SessionId`, `EvNotDetected.SessionDuration`, `EnergyTransferStarted.SessionId`, `EnergyTransferStopped.SessionId`, `EnergyTransferStopped.Reason`, `Fault.SessionId`.

Feature: `PREF`.

`State`, `SupplyState`, `FaultState`, `CircuitCapacity`, `MaximumChargeCurrent`, `SessionEnergyCharged`, and `EnableCharging` are conformance `M` and are not in this list because the table names a catalog id.

### Texts `PREF` on that server

Feature PREF conformance text is `M` (line 661). These elements' own text is `PREF`, not `M`, and they name no catalog id: `NextChargeStartTime`, `NextChargeTargetTime`, `NextChargeRequiredEnergy`, `NextChargeTargetSoC`, `SetTargets`, `GetTargets`, `ClearTargets`, `GetTargetsResponse`. `ApproximateEvEfficiency` text is `[PREF]` (optional-if) and is not in this list.

Fields whose own text is `M` inside those `PREF` commands, and whose feed cell names no catalog id: `GetTargetsResponse.ChargingTargetSchedules`, `ChargingTargetSchedules.DayOfWeekForSequence`, `ChargingTargetSchedules.ChargingTargets`, `ChargingTargets.TargetTimeMinutesPastMidnight`, `SetTargets.ChargingTargetSchedules`.

### EnergyEvseMode server, device type EnergyEvse

`SupportedModes`, `CurrentMode`, `ChangeToMode`, `ChangeToModeResponse`. Their `M` fields in the table (`Label`, `Mode`, `ModeTags`, `ModeTags.Value`, `NewMode`, `Status`, `StatusText`) name no catalog id.

### DeviceEnergyManagement server, device type DeviceEnergyManagement

`EsaType`, `EsaCanGenerate`, `EsaState`, `AbsMinPower`, `AbsMaxPower`.

No command, event, or feature of this cluster has conformance text `M`. `M` fields inside `Forecast`, `PowerAdjustCapability`, commands, and events are `DEM-in`: the parent text is a feature name, not `M`. They name no catalog id. They are the field rows in that table.

### Not in the device-file mandatory set

DeviceEnergyManagementMode conformance on the device file is `ControllableEsa, O` with `Mandatory` unset. Its `M` elements are the `if-mounted` rows. They name no catalog id. They are not listed above.

`schema.json` effective requirements of device type 1292 set feature `PFR` conformance text `M` on the composed DeviceEnergyManagement server (lines 18365–18377) and feature `PA` text `desc` (lines 18379–18386). `go-fabric@v0.22.2:device/energy_evse_gen.go` does not declare that server. `Forecast` conformance text on the cluster is `PFR | SFR`. This section does not move `Forecast` into the device-file list.

## 5. Catalog elements of this domain without a Matter element

The domain used here is the `helianthus.pack.evse` elements plus the core resource kinds those dimensions name. Device Energy Management and Energy Preference have no catalog elements (`git grep` of `energy.esa.`, `energy.series.`, `energy.preference.`, and `evse.mode` in `element-catalog-v1.json` found no line).

Ten evse ids are named in section 3 feed cells: `evse.status.connection`, `evse.status.charging`, `evse.status.readiness`, `evse.status.interlock`, `evse.status.fault`, `evse.limit.configured_current`, `evse.limit.advertised_current`, `evse.limit.allocated_current`, `evse.energy.session`, `evse.operation.set_allocated_current`. The other 36 evse catalog ids have no feed cell in these five clusters.

Facts, each `unknown` / `matter.unmapped.v1` unless noted:

- `evse.ac.active_power` (catalog line 68, target row 3). Unit `unit.watt`. Subject `resource.phase`. No power attribute in these five clusters.
- `evse.ac.current` (line 69, target row 4). Disposition `transformed`, reason `matter.phase_association_by_relation.v1`. Target JSON lines 135–138: device type 1296, cluster 144, attribute 5, `unit.ampere` to `amperage-mA` by `exact_multiply` factor 1000. That cluster is Electrical Power Measurement, outside this group. `tests/test_matter161_target.py` lines 37–38 use this id as the positive ref.
- `evse.ac.frequency` (line 70, row 5). Unit `unit.hertz`. Subject `resource.evse`.
- `evse.ac.voltage` (line 71, row 6). Unit `unit.volt`. Subject `resource.phase`.
- `evse.energy.lifetime` (line 85, row 13). Unit `unit.joule` (pack-metadata lines 439–447). Subject `resource.meter`. `SessionEnergyCharged` is the session fact, not this one.
- `evse.limit.actual_current` (line 87, row 15). Unit `unit.ampere`, subject `resource.connector`. The id says actual. It is not named on `MaximumChargeCurrent`.
- `evse.limit.allocated_current_phase` (line 90, row 18). Unit `unit.ampere`, subject `resource.phase` (pack-metadata lines 569–586). No attribute in these clusters carries a phase.

Capabilities, each `unknown` / `matter.unmapped.v1`: `evse.capability.read.connector`, `read.evse`, `read.meter`, `read.phase`, `read.session` (catalog lines 72–76, target rows 7–11), and `evse.capability.set_allocated_current` (line 77, row 12). The operation that names that capability is a candidate on `EnableCharging`. The capability kind is not a command.

Dimensions, no target row: `evse.dimension.asset`, `connector`, `evse`, `meter`, `phase`, `session` (catalog lines 78–83). `evse.dimension.session` value kind in semreg is `ValueText` (`definitions.go` line 53).

Effect rule, no target row: `evse.effect.set_allocated_current` (catalog line 84). It names the operation and `evse.limit.allocated_current`.

Relations: `evse.relation.asset_evse`, `connector_phase`, `connector_session`, `evse_connector` are `unknown` / `matter.relation_construct_not_adopted.v1` (target rows 21–24). `evse.relation.evse_meter` is `withheld` / `matter.power_topology_endpoint_unallocated.v1` with `cluster_id` 156 (target row 25). Cluster 156 is Power Topology, outside this group. None of these five clusters has a relation element.

Services, each `unsupported` / `matter.service_not_requested_item.v1`: `evse.service.connector`, `evse`, `meter`, `phase`, `session` (catalog lines 104–108, target rows 26–30).

Presentations, catalog disposition `unsupported`, no target row: `evse.portal.operation.set_allocated_current`, `portal.read.connector`, `portal.read.evse`, `portal.read.meter`, `portal.read.phase`, `portal.read.session` (catalog lines 93–98).

Resource kinds, no target row: `resource.charging_station` (line 39), `resource.charging_session` (line 38), `resource.connector` (line 41), `resource.evse` (line 46). `resource.meter` (line 52) and `resource.phase` (line 53) are the kinds named by `evse.dimension.meter` and `evse.dimension.phase`. They are core kinds. No element in these five clusters is that kind.

`storage.state.soc` is in the catalog and is not an element of this domain's feed cells. `thermal.overrun.sg_ready_condition_1`, `_3`, and `_4` are present and are discussed on `CurrentMode` and in section 6. They are thermal-pack facts.

## 6. Disagreements with the prior accounting

Ids, revisions, and conformance texts in the five a prior accounting cluster sections match the `Definition` literals read here: DeviceEnergyManagement revision 4, EnergyEvse revision 4, EnergyPreference revision 1, EnergyEvseMode revision 2, DeviceEnergyManagementMode revision 2, and the attribute, command, event, and feature ids and conformance strings in those sections. The rows below are the claims those sources do not support.

1. a prior accounting legend line 3: status `present` means on main, and the parenthetical says the ticket completes its target row. The `present` rows in this group are CircuitCapacity (`evse.limit.configured_current`), MaximumChargeCurrent (`evse.limit.advertised_current`, `evse.limit.allocated_current`), and SessionEnergyCharged (`evse.energy.session`) (a prior accounting lines 416, 419, 428). Those ids are in the catalog. Their target rows are `unknown` / `matter.unmapped.v1` with an empty target object (rows 19, 16, 17, 14). The one transformed evse fact in the target is `evse.ac.current`, aimed at cluster 144 attribute 5 (JSON lines 135–138), which is not one of these three attributes.

2. a prior accounting line 1053, device type EnergyEvse, id cell empty, SemReg `evse.ac.total_active_power`, ticket a prior proposal, status planned. `schema.json` device type id is 1292, revision 2 (lines 18176–18179). `git grep` of `evse.ac.total_active_power` in the catalog found no line. The catalog id is `evse.ac.active_power`. The requirements list at lines 18180–18227 does not name that fact.

3. a prior accounting OnMode and StartUpMode (EnergyEvseMode lines 484–485; DeviceEnergyManagementMode lines 508–509) use a reason that begins with the words deprecated or disallowed. The generated `Op` is `ConfDisallowed` and the text is `X` (EnergyEvseMode lines 273 and 281). The generated files do not contain the word deprecated. The conformance text `X` matches. Feature DEPONOFF is also text `X` and `ConfDisallowed` (line 250). Its a prior accounting reason (lines 488 and 512) is a derived-binding note, not that deprecated sentence.

4. a prior accounting DeviceEnergyManagementMode `CurrentMode` (line 507) names `energy.esa.mode` and `thermal.overrun.sg_ready_condition_1`, `_3`, `_4`, status planned. `energy.esa.mode` is absent. The three thermal ids are present (catalog lines 351–353). Each symbol list is that id plus `.active`, `.finished`, `.inactive`, `.running` (`thermal/definitions.go` lines 102–104 and 125). ModeTag on this cluster is `NoOptimization`, `DeviceOptimization`, `LocalOptimization`, `GridOptimization`, plus Auto..Day (lines 158–161, 167–181). `CurrentMode` is a uint8 (line 265).

5. `a prior accounting` a prior claim says Energy EVSE `0x050C` revision 2 requires Energy EVSE, Energy EVSE Mode, Power Source, Device Energy Management, and Electrical Sensor. That list matches `schema.json` requirements lines 18188–18227 (Power Source, Device Energy Management, and Electrical Sensor are `deviceType` elements with conformance `M`). `go-fabric@v0.22.2:device/energy_evse_gen.go` `Servers` (lines 32–51) lists EnergyEvse, EnergyEvseMode, Identify, and TemperatureMeasurement, and does not list those three device types.

6. `a prior accounting` a prior claim (line 263) marks `evse.limit.allocated_current` fed-not-published and marks `evse.limit.advertised_current`, `evse.limit.actual_current`, and `evse.limit.allocated_current_phase` defined-not-fed, all on MaximumChargeCurrent. This note names advertised and allocated as candidates. `actual_current` and `allocated_current_phase` are in section 5. No target row equates any of the four to attribute `0x0007`. A driver feed is not visible from the catalog, the target, or the go-fabric files read here, so the fed-not-published half is unchecked.

7. `a prior accounting` a prior claim calls `evse.limit.configured_current` fed and unpublished for CircuitCapacity. The id is in the catalog and the target row is `unknown` / `matter.unmapped.v1`. A driver feed is not in the sources read here, so the fed half of that claim is unchecked. The unpublished half agrees with the target row.

8. `a prior accounting` line 361 records that cluster fields and enum members, FaultStateEnum among the examples, stayed at attribute granularity in that audit. This note opens them. The enum values and struct fields are in section 3. The audit's attribute-level rows are not a field list.

## 7. Uncertainty

- `go-fabric@v0.22.2:device/energy_evse_gen.go` does not copy `schema.json` device-type requirements onto `Servers`. Whether a constructed EnergyEvse endpoint therefore includes Power Source, Device Energy Management, and Electrical Sensor is not settled by the device file. The same holds for Descriptor on both device types. See the open questions 2.
- `schema.json` sets feature PFR to conformance `M` on the DeviceEnergyManagement server composed into EnergyEvse, and sets PA, STA, PAU, FA, and CON to `[ControllableEsa].a+` on device type 1293. The cluster `Definition` features keep the texts in section 3. Which text a running server uses is not established here.
- DeviceEnergyManagementMode conformance `ControllableEsa, O` is stored as that string on the device file, with `Mandatory` unset. The schema effective AST is `otherwise` of the name `ControllableEsa` and `O`. This note does not reduce that expression to a boolean. `ControllableEsa` is a condition name on the device type (line 30 of the device file; schema line 18484), not a value.
- The target `model_source.tag` is go-fabric `v0.13.12`. The cluster files read here are `v0.22.2`. No diff of the two tags was made for these five clusters.
- Symbol lists and decimal bounds used above come from `semreg/v1/packs/evse/definitions.go` and, for the five status facts, from `evse-acceptance-vectors.json`. The catalog element record does not carry them. Pack-metadata carries the unit id and not the bound.
- No scale between `unit.joule` and `energy-mWh`, or between `unit.watt` and `power-mW`, is declared on a target row in this group. The only declared ampere-to-milliampere conversion found is on `evse.ac.current`. It was not applied to the current-limit facts.
- `a prior accounting` calls some evse facts fed. These sources do not show a driver. Those claims stay open.
- Whether `evse.limit.configured_current` is the same quantity as CircuitCapacity, and which of advertised or allocated current is MaximumChargeCurrent, is not declared by a target row. The grades in section 3 are correspondences of kind, unit, and subject, not a mapping.
- The semreg fixture catalog was not byte-compared with the docs-semantic catalog. One id was grepped.
- EnergyPreference is absent from both device types of this group. Other device types in `schema.json` were not searched for a requirement on cluster 155.
- Heat Pump and Battery Storage device types are outside this group. a prior claim's claim that AbsMinPower and AbsMaxPower are mandatory on those types was not checked.
