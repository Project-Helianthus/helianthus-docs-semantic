---
status: "research index for Matter 1.6.1 source accounting by cluster; no mapping is decided and no canonical target is written."
---

# Matter 1.6.1 source accounting by cluster

## Scope

These notes account Matter 1.6.1 device types cluster by cluster. Identifiers, conformance, types and units are the Matter 1.6.1 model generated in go-fabric v0.22.2, `go-fabric@v0.22.2:parity/schema.json` (revision `1.6.1`, data model revision 21), and the generated device and cluster files the group notes cite. The catalog is `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`. The same element ids are in `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json`. Canonical units are `canonical_unit` on each field of `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json` (a definition reference such as `unit.volt`, or null). The array `units` is the pack's unit-id list. Target rows are `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json` and `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md`. The JSON `rows` array has 246 entries and one disposition `transformed`. The markdown states 177 rows and that only `evse.ac.current` is `transformed`. These notes keep both counts and do not resolve them. No canonical target file is written here. No Matter code is edited and the go-fabric pin is not moved.

The canonical unit is SI. Charge capacity, including charge and discharge counters and remaining and full-charge capacity, stays ampere-hour. At the pinned catalog, `storage.capacity.charge` and `storage.capacity.discharge` carry `unit.ampere_hour`. `storage.capacity.remaining` and `storage.capacity.full_charge` are absent. These notes keep those gaps and do not state coulombs.

Group notes: [air quality](air-quality.md), [bridge identity](bridge-identity.md), [electrical](electrical.md), [EVSE and device energy management](evse-dem.md), [sensing](sensing.md), [storage, PV and power source](storage-pv-power.md), [tariff](tariff.md), [thermostat](thermostat.md), [water and hydraulics](water-hydraulics.md).

## Grade legend

A row's grade is one of `exact`, `partial`, `candidate` or none.

- `exact`: the same meaning, the same kind and the same unit, and the loss is `none`. No row in these notes is `exact`.
- `partial`: the catalog fact is the same quantity family, and the losses are named.
- `candidate`: the quantity is related, and a named loss keeps it from `partial`.
- none: no catalog element is a feed. The row says no source.

The Matter unit of the element is written beside the catalog `canonical_unit` of each named field, so the conversion the row needs is visible. Where the element record has no unit field, the canonical unit is still the pack-metadata field, or none when that field is null.

## Device types

A cluster is required here when that group note sets it mandatory on the device file (`Mandatory: true` or conformance `M` on a server the note treats as required). Schema device-type requirements the same note records, and that the device file omits, are listed under the device type and are not folded into the device-file set. Element coverage uses the note that accounted the cluster. Clusters no note expands are marked `not in the sources`.

Global attributes: air-quality and sensing include `FeatureMap` / `ClusterRevision` where `schema.json` effective conformance is `M`. The bridge-identity note includes six global attributes because `go-fabric@v0.22.2:cluster/spec/instance.go` lines 15–22 name ids every server answers. Electrical, thermostat and storage-pv-power leave those ids out of cluster element rows. That split is under Disagreements between drafts. Lists below follow the note that owned the cluster.

### Air quality

Group note: [air-quality note](air-quality.md).

**AirQualitySensor** `0x002C` revision 1.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| Identify `0x0003` `M` | no. That note does not expand Identify. [bridge-identity note](bridge-identity.md): `IdentifyTime` `0x0000` `M`, `IdentifyType` `0x0001` `M`, command `Identify` `0x00` `M`, field `Identify.IdentifyTime` `M`, each with no catalog element. |
| AirQuality `0x005B` `M` | no: attribute `AirQuality` `0x0000`, `FeatureMap` 65532, `ClusterRevision` 65533. |

Concentration clusters on this device type are `O`. Descriptor appears in `go-fabric@v0.22.2:parity/schema.json` with no conformance field (lines 75–76). Mandatoriness of that empty field is not stated.

**AirPurifier** `0x002D` revision 3.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| Identify `0x0003` `M` | no. Same unexpanded Identify elements as AirQualitySensor (line 498; [bridge-identity note](bridge-identity.md)). |
| FanControl `0x0202` `M` | no. That note does not expand FanControl. [thermostat note](thermostat.md), mandatory for a FanControl server with no feature constraint (line 260, which also cites AirPurifier in `go-fabric@v0.22.2:docs/reference/device-types.md` and leaves it out of that note's own mandatory column): `FanMode` `0x0000`, `FanModeSequence` `0x0001`, `PercentCurrent` `0x0003` have no catalog element. `PercentSetting` `0x0002` has `thermal.demand.level` partial. |

HepaFilterMonitoring and ActivatedCarbonFilterMonitoring are `O`. No concentration or filter element is mandatory for either device type.

### Bridge identity

Group note: [bridge-identity note](bridge-identity.md). Base device type `Descriptor` conformance `M` is applied to Aggregator, BridgedNode and RootNode. The device files do not list Descriptor.

**Aggregator** `0x000E` revision 2. No server in the device file is `M`. Required cluster from Base: Descriptor `0x001D`. Mandatory elements have no catalog source: `DeviceTypeList` `0x0000` and fields `DeviceType` and `Revision`, `ServerList` `0x0001`, `ClientList` `0x0002`, `PartsList` `0x0003`, and the six global attributes. Identify on this device type is `O`.

**BridgedNode** `0x0013` revision 3.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| BridgedDeviceBasicInformation `0x0039` `M` | no: `Reachable` `0x0011` `M`; `UniqueId` `0x0012` (`Rev >= v4, O` at revision 6); event `ReachableChanged` `0x03` `M` and field `ReachableNewValue`; six global attributes. |
| Descriptor `0x001D` (Base `M`) | no: the Descriptor list under Aggregator. |

**RootNode** `0x0016` revision 5.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| BasicInformation `0x0028` `M` | no: `DataModelRevision`, `VendorName`, `VendorId`, `ProductName`, `ProductId`, `NodeLabel`, `Location`, `HardwareVersion`, `HardwareVersionString`, `SoftwareVersion`, `SoftwareVersionString`, `CapabilityMinima` and the six fields named at lines 309–310, `UniqueId`, `SpecificationVersion`, `MaxPathsPerInvoke`, `ConfigurationVersion`, event `StartUp` `0x00` and field `SoftwareVersion`, six global attributes. |
| Descriptor `0x001D` (Base `M`) | no: the Descriptor list under Aggregator. |
| AccessControl `0x001F` `M` | not in the sources. The note does not expand this cluster. |
| GeneralCommissioning `0x0030` `M` | not in the sources. |
| GeneralDiagnostics `0x0033` `M` | not in the sources. |
| AdministratorCommissioning `0x003C` `M` | not in the sources. |
| OperationalCredentials `0x003E` `M` | not in the sources. |
| GroupKeyManagement `0x003F` `M` | not in the sources. |

FixedLabel and UserLabel are `O` on Base and contribute no mandatory element for these three device types.

### Sensing

Group note: [sensing note](sensing.md). Identify is `M` on all four device files and is not expanded. Descriptor is in `go-fabric@v0.22.2:parity/schema.json` with no conformance field; the note does not decide mandatoriness (lines 54, 285).

| Device type | Id | Revision | Required clusters | Catalog source for every mandatory element |
| --- | --- | --- | --- | --- |
| TemperatureSensor | `0x0302` | 3 | TemperatureMeasurement `0x0402` `M`; Identify `0x0003` `M` | TemperatureMeasurement: no. `MeasuredValue` has partial catalog facts. `MinMeasuredValue`, `MaxMeasuredValue`, `ClusterRevision` have none. Identify: no, [bridge-identity note](bridge-identity.md). |
| PressureSensor | `0x0305` | 3 | PressureMeasurement `0x0403` `M`; Identify `M` | PressureMeasurement: no. `MeasuredValue` has partial facts. `MinMeasuredValue`, `MaxMeasuredValue`, `FeatureMap`, `ClusterRevision` have none. Identify: no, same bridge lines. |
| FlowSensor | `0x0306` | 3 | FlowMeasurement `0x0404` `M`; Identify `M` | FlowMeasurement: no. `MeasuredValue` has `thermal.measurement.flow_rate` partial. `MinMeasuredValue`, `MaxMeasuredValue`, `ClusterRevision` have none. Identify: no, same bridge lines. |
| HumiditySensor | `0x0307` | 3 | RelativeHumidityMeasurement `0x0405` `M`; Identify `M` | RelativeHumidityMeasurement: no. `MeasuredValue` has `thermal.measurement.humidity` partial. `MinMeasuredValue`, `MaxMeasuredValue`, `ClusterRevision` have none. Identify: no, same bridge lines. |

### Electrical

Group note: [electrical note](electrical.md).

**ElectricalSensor** `0x0510` revision 1. Device-file required cluster: PowerTopology `0x009C` `M`. No attribute, command, event or feature in it has conformance `M`. ElectricalPowerMeasurement and ElectricalEnergyMeasurement are `O.a+` with `Mandatory` unset. Their conformance-`M` elements are mandatory only when the cluster is mounted (`ES-if`, lines 35 and 318–323) and those elements have no catalog source (the list under ElectricalMeter below, except `ActivePower`). Descriptor in schema has no conformance key.

**ElectricalMeter** `0x0514` revision 1.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| ElectricalPowerMeasurement `0x0090` `M` | no: `PowerMode`, `NumberOfMeasurementTypes`, `Accuracy` and its `M` fields `MeasurementType`, `Measured`, `MinMeasuredValue`, `MaxMeasuredValue`, `AccuracyRanges`, and range fields `RangeMin`, `RangeMax`. `ActivePower` `0x0008` is `M` and has catalog elements. |
| ElectricalEnergyMeasurement `0x0091` `M` | no: `Accuracy` and the same `M` field set in that package's struct copy. |

CommodityMetering conformance `P, M` has `Mandatory` unset. Its `M` attributes are not in the note's mandatory list. Schema also requires device type ElectricalSensor `M`. The note does not add that device type's servers to this mandatory list. `Base` is `ElectricalEnergyTariff`; whether that mounts tariff servers is not settled.

**ElectricalUtilityMeter** `0x0511` revision 1. Device-file required cluster: MeterIdentification `0x0B06` `M`. No: `MeterType` `0x0000`, `PointOfDelivery` `0x0001`, `MeterSerialNumber` `0x0002`. Schema also lists Identify `M`. The device file omits it. Identify's `M` elements have no catalog source ([bridge-identity note](bridge-identity.md)).

**MeterReferencePoint** `0x0512` revision 1. Device-file required cluster: Identify `0x0003` `M`. Elements are outside that note. [bridge-identity note](bridge-identity.md): the `M` elements have no catalog source.

### EVSE and device energy management

Group note: [evse-dem note](evse-dem.md).

**EnergyEvse** `0x050C` revision 2.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| EnergyEvse `0x0099` `M` | no. Elements with a catalog id, so not in the gap list: `State`, `SupplyState`, `FaultState`, `CircuitCapacity`, `MaximumChargeCurrent`, `SessionEnergyCharged`, `EnableCharging`. Elements with no catalog id: lines 366–374 and 378–382 (table in the next section). |
| EnergyEvseMode `0x009D` `M` | no: `SupportedModes`, `CurrentMode`, `ChangeToMode`, `ChangeToModeResponse` and the `M` fields named at line 386. |

Identify and TemperatureMeasurement are `O`. Schema requires device types PowerSource, DeviceEnergyManagement and ElectricalSensor, each `M`, and the device file does not declare them. The note does not move those into the device-file mandatory set.

**DeviceEnergyManagement** `0x050D` revision 3.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| DeviceEnergyManagement `0x0098` `M` | no: `EsaType`, `EsaCanGenerate`, `EsaState`, `AbsMinPower`, `AbsMaxPower`. |

DeviceEnergyManagementMode is `ControllableEsa, O` with `Mandatory` unset and is not in the device-file mandatory set.

### Storage, PV, power source

Group note: [storage-pv-power note](storage-pv-power.md).

**PowerSource** `0x0011` revision 1. Required cluster: PowerSource `0x002F` `M`. No: `Order` `0x0001`, `Description` `0x0002`, `EndpointList` `0x001F`. `Status` `0x0000` has candidate catalog elements and is not in the gap list.

**SolarPower** `0x0017` revision 1. Device-file servers: Identify `O` only. Schema requires device type PowerSource `M` (`min 1`) and ElectricalSensor `M` (`min 1`), and sets feature `WIRED` `M` on the composed PowerSource. The note's gap list for that composed PowerSource: `Order`, `Description`, `EndpointList`, feature `WIRED`. `Status` has candidate catalog elements. TemperatureSensor on the schema is `O`. DeviceEnergyManagement on the schema is `desc`.

**BatteryStorage** `0x0018` revision 2. Device-file servers: Identify `O` only. Schema requires PowerSource `M` (`min 2`), ElectricalSensor `M` (`min 2`), DeviceEnergyManagement `M`. The note's gap list adds, on PowerSource instance 2, `BatTimeRemaining`, `BatTimeToFullCharge`, `ActiveBatChargeFaults`, `BatCapacity` and feature `BAT`, and on instance 1 feature `WIRED`. `BatCapacity` is on that list because `storage.capacity.charge` and `storage.capacity.discharge` are candidate lifetime counters and do not fill the Fixed attribute. `BatVoltage`, `BatPercentRemaining`, `ActiveBatFaults` and `BatChargingCurrent` have catalog elements and are not in the gap list. `BatChargeLevel` has catalog elements and is not in the mandatory column.

PowerSourceConfiguration is on none of these three device files.

### Thermostat, fan, occupancy

Group note: [thermostat note](thermostat.md).

**Thermostat** `0x0301` revision 7.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| Identify `0x0003` `M` | no. Not expanded in that note. [bridge-identity note](bridge-identity.md). |
| Thermostat `0x0201` `M` | no: `ControlSequenceOfOperation` `0x001B`; command `SetpointRaiseLower` `0x00` fields `Mode` and `Amount`. `LocalTemperature`, `SystemMode` and `SetpointRaiseLower` have partial catalog elements. |

Groups conformance `Active` has `Mandatory` unset.

**HeatPump** `0x0309` revision 1. Device file: Identify server `O`, Thermostat client `O`. No cluster of this group is a mandatory server or client in that file. Schema requirements in go-fabric are in section 5. They are not a device-file required cluster in that note.

**RoomAirConditioner** `0x0072` revision 4.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| Identify `0x0003` `M` | no. [bridge-identity note](bridge-identity.md). |
| OnOff `0x0006` `M`, feature `DF` | no for the OnOff elements the water note accounts. That note does not expand OnOff. [water-hydraulics note](water-hydraulics.md): attribute `OnOff` `M`, command `Off` `M`, commands `On` and `Toggle` conformance `!OFFONLY`, no catalog element, on a device file that sets no OnOff features. What feature `DF` adds is not in the sources. |
| Thermostat `0x0201` `M` | no: the same three gaps as Thermostat. |

**Fan** `0x002B` revision 5.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| Identify `0x0003` `M` | no. [bridge-identity note](bridge-identity.md). |
| Groups `0x0004` `M` | not in the sources. No note expands Groups. |
| FanControl `0x0202` `M` | no: `FanMode`, `FanModeSequence`, `PercentCurrent`. `PercentSetting` has `thermal.demand.level` partial. |

**ThermostatController** `0x030A` revision 2. Required server: Binding `0x001E`, conformance `Simple & Client`, `Mandatory` true. Binding's elements are not in the sources. Required client: Thermostat `0x0201` `M`. That note does not score that client's attributes as mandatory server elements.

OccupancySensing and ThermostatUserInterfaceConfiguration are not mandatory servers for this group.

### Tariff

Group note: [tariff note](tariff.md).

**ElectricalEnergyTariff** `0x0513` revision 1. Device-file `Mandatory: true` is set only on Descriptor `0x001D`. CommodityPrice is `[ActiveTariff].a+` and CommodityTariff is `O.a+`, `Mandatory` unset. That note does not expand Descriptor. [bridge-identity note](bridge-identity.md): Descriptor's `M` elements have no catalog source. No element of CommodityPrice, CommodityTariff or Messages is mandatory for this device type.

### Water and hydraulics

Group note: [water-hydraulics note](water-hydraulics.md). That note includes mandatory client clusters. [sensing note](sensing.md) and [thermostat note](thermostat.md) do not score client requirements as server mandates. See section 5.

**WaterHeater** `0x050F` revision 1.

| Required cluster | Every mandatory element has a catalog source |
| --- | --- |
| WaterHeaterManagement `0x0094` `M` | no: WaterHeaterManagement gap rows ([water-hydraulics note](water-hydraulics.md)). `BoostState` is `M` and has candidate `thermal.overrun.one_time_dhw`, so it is omitted from that gap list. |
| WaterHeaterMode `0x009E` `M` | no: lines 423–432. |
| Thermostat `0x0201` `M`, feature `HEAT` | not fully in the sources. That note does not expand Thermostat. The thermostat note lists unconditional `M` gaps `ControlSequenceOfOperation` and the two `SetpointRaiseLower` fields for a Thermostat server and records WaterHeater's `HEAT` requirement as outside its mandatory column (uncertainty, [thermostat note](thermostat.md)). |

Identify on this device type is `O`.

**Pump** `0x0303` revision 4. Required: Identify `M` ([bridge-identity note](bridge-identity.md), no catalog source); OnOff `M` (gap rows lines 451–454); PumpConfigurationAndControl `M` (gap rows lines 433–439). `Speed` is `O` and has a partial catalog element. It is not a mandatory element.

**PumpController** `0x0304` revision 5. Required servers: Identify `M` (same Identify gaps); Binding `M`, elements not in the sources. Required clients, included by that note: OnOff `M` and PumpConfigurationAndControl `M`, same gap rows as Pump.

**WaterValve** `0x0042` revision 1. Required: Identify `M` (same Identify gaps); ValveConfigurationAndControl `M` (gap rows lines 440–446). `CurrentLevel` is conformance `LVL` and is not in the mandatory gap list.

**WaterFreezeDetector** `0x0041` revision 2. Required: Identify `M`; BooleanState `M` with feature `CHGEVENT` and event `StateChange` `PresenceMandatory`. Gap rows lines 447–450. BooleanStateConfiguration is `O`.

**WaterLeakDetector** `0x0043` revision 2. Same required clusters and same gap rows as WaterFreezeDetector.

## Composition of the named device types

No device type is chosen for a resource kind here. The rows below are the device types a later composition can read. They record required clusters, the static attributes the data model requires, and, for each dynamic attribute that a group note grades, the catalog element and grade. Every other dynamic element of those clusters is no source. An endpoint is composed for an admitted resource of a supported kind whose device type's mandatory elements each have a transformed row or a source-declared value. Existing admission admits at least one live element. A complete profile with no admitted live element does not by itself yield an endpoint. An admitted resource lacking a mandatory element is not allocated, and the report names the missing row. That allocation is not made in these notes.

Phases, DC inputs and connectors fold into the parent endpoint as declared losses. Their values stay available in SemReg, in MCP and in GraphQL. No endpoint is denied because a profile is unset.

The Matter 1.6.1 model in go-fabric v0.22.2 has no device type named for a boiler. The identifier `Boiler` is bit 3 of `WaterHeaterHeatSourceBitmap` on WaterHeaterManagement, conformance `M` (`go-fabric@v0.22.2:cluster/spec/waterheatermanagement/definition_gen.go`). Heat Pump `0x0309` is the device type these notes have for a heat generator. A boiler is not given a second device type here.

| Device type | Required clusters | Static attributes | Dynamic attributes, catalog element and grade | Mandatory elements without a source |
| --- | --- | --- | --- | --- |
| Solar Power `0x0017` revision 1, with an Electrical Sensor part | Device file: Identify `O` only. Schema: device type PowerSource `M` (min 1) and Electrical Sensor `M` (min 1), feature `WIRED` `M` on the composed PowerSource. Electrical Sensor device file: PowerTopology `0x009C` `M`. ElectricalPowerMeasurement `0x0090` and ElectricalEnergyMeasurement `0x0091` are `O.a+` on that sensor. | PowerSource `Order` `0x0001`, `Description` `0x0002`, `EndpointList` `0x001F`; feature `WIRED`. PowerTopology has no conformance-`M` element. When a measurement cluster is mounted: `PowerMode` `0x0000`, `NumberOfMeasurementTypes` `0x0001`, `Accuracy` and the `M` fields `MeasurementType`, `Measured`, `MinMeasuredValue`, `MaxMeasuredValue`, `AccuracyRanges`, `RangeMin`, `RangeMax`. | `Status` `0x0000`: `pv.status.operating` candidate. Graded electrical feeds, partial unless noted: Voltage `evse.ac.voltage`, `infrastructure.ac.voltage`, `pv.ac.voltage`, `pv.ac.aggregate_voltage`, `pv.dc.voltage`, `pv.dc.aggregate_voltage`, `storage.pack.voltage`; ActiveCurrent the same current ids, and `evse.ac.current` is the one target row `transformed`; ReactiveCurrent no source; ApparentCurrent no source; ActivePower the active-power ids in the [electrical note](electrical.md); ReactivePower and ApparentPower the reactive and apparent ids there; Frequency `evse.ac.frequency`, `infrastructure.ac.frequency`, `pv.ac.frequency` partial; PowerFactor `infrastructure.ac.power_factor`, `pv.ac.power_factor` partial. RMS attributes are candidate for the AC ids only. Energy cumulative and periodic attributes are partial or candidate as the electrical note grades them. Every other dynamic element: no source. | `Order`, `Description`, `EndpointList`, feature `WIRED`. Mounted measurement clusters: the Accuracy and PowerMode elements above. |
| Battery Storage `0x0018` revision 2 | Device file: Identify `O` only. Schema: PowerSource `M` (min 2), Electrical Sensor `M` (min 2), DeviceEnergyManagement `M`. | Same PowerSource static attributes as Solar Power, plus on PowerSource instance 2 feature `BAT` and the battery attributes whose conformance is feature-gated. Power mode, measurement types and accuracy ranges are the same static measurement elements when ElectricalPowerMeasurement or ElectricalEnergyMeasurement is mounted. | `Status`: `storage.status.operating` candidate. `BatVoltage`: `storage.pack.voltage` partial, catalog `unit.volt`. `BatPercentRemaining`: `storage.state.soc` partial, catalog `unit.ratio`. `BatChargeLevel`: `storage.status.warning` and `storage.status.alarm` candidate. `ActiveBatFaults`: `storage.status.protection` candidate. `BatCapacity`: `storage.capacity.charge` and `storage.capacity.discharge` candidate, catalog `unit.ampere_hour` (not coulomb); cumulative lifetime counters against Fixed uint32, and no derivation to a fixed capacity is in the sources. `BatChargingCurrent`: `storage.pack.current` partial, catalog `unit.ampere`. `BatTimeRemaining`, `BatTimeToFullCharge`, `ActiveBatChargeFaults`: no source. Electrical dynamic attributes: the same grades as Solar Power where the element is in the electrical note. DeviceEnergyManagement `EsaType`, `EsaCanGenerate`, `EsaState`, `AbsMinPower`, `AbsMaxPower`: no source. Every other dynamic element: no source. | `Order`, `Description`, `EndpointList`; feature `WIRED` on instance 1; feature `BAT`, `BatTimeRemaining`, `BatTimeToFullCharge`, `ActiveBatChargeFaults`, `BatCapacity` on instance 2. DeviceEnergyManagement's five `M` attributes. Mounted measurement Accuracy and PowerMode elements. |
| EVSE `0x050C` revision 2 | Device file: EnergyEvse `0x0099` `M`, EnergyEvseMode `0x009D` `M`. Identify and TemperatureMeasurement are `O`. Schema also requires PowerSource, DeviceEnergyManagement and ElectricalSensor, each `M`; the device file does not declare them. | EnergyEvseMode `SupportedModes`, `CurrentMode`, and the `M` fields of `ChangeToMode` and `ChangeToModeResponse`. Feature `PREF` is `M` on the device type these notes read. | `State`: `evse.status.connection`, `evse.status.charging` candidate. `SupplyState`: `evse.status.readiness`, `evse.status.interlock` candidate. `FaultState`: `evse.status.fault` candidate. `CircuitCapacity`: `evse.limit.configured_current` partial, catalog `unit.ampere`. `MaximumChargeCurrent`: `evse.limit.advertised_current`, `evse.limit.allocated_current` candidate, catalog `unit.ampere`. `SessionEnergyCharged`: `evse.energy.session` partial, catalog `unit.joule`. `EnableCharging`: `evse.operation.set_allocated_current` candidate. Elements with no catalog id in the [evse-dem note](evse-dem.md), including `ChargingEnabledUntil`, `MinimumChargeCurrent`, `SessionId`, `SessionDuration`, `Disable`, the `M` events, and the `PREF` schedule commands: no source. Every other dynamic element: no source. | The EnergyEvse and EnergyEvseMode gap rows in the [evse-dem note](evse-dem.md). |
| Electrical Sensor `0x0510` revision 1 | Device file: PowerTopology `0x009C` `M`. ElectricalPowerMeasurement and ElectricalEnergyMeasurement are `O.a+`. | No attribute, command, event or feature of PowerTopology has conformance `M`. When a measurement cluster is mounted: `PowerMode`, `NumberOfMeasurementTypes`, `Accuracy` and the `M` accuracy fields named for Solar Power. | PowerTopology list attributes are endpoint numbers, not catalog element values. The five withheld relations on target cluster 156 stay withheld. Graded measurement attributes are the electrical note's partial and candidate rows. `ActivePower` has partial catalog elements and does not by itself fill the cluster. Every other dynamic element: no source. | None inside PowerTopology's conformance-`M` set. When a measurement cluster is mounted: the Accuracy and PowerMode elements. |
| Thermostat `0x0301` revision 7 | Identify `0x0003` `M`; Thermostat `0x0201` `M`. | `ControlSequenceOfOperation` `0x001B`. Command `SetpointRaiseLower` `0x00` fields `Mode` and `Amount`. | `LocalTemperature` `0x0000`: `thermal.measurement.air_temperature` partial, catalog `unit.kelvin`. `OutdoorTemperature` `0x0001`: `thermal.measurement.outdoor_air_temperature` partial, catalog `unit.kelvin`. Occupied and unoccupied heating and cooling setpoints: the four `thermal.setpoint.occupied_*` and `thermal.setpoint.unoccupied_*` facts, partial, catalog `unit.kelvin`. `SystemMode`: `thermal.mode.system` partial, `thermal.mode.terminal_unit` candidate, `thermal.operation.set_mode` partial. `ThermostatRunningMode`: `thermal.action.state` partial. `SetpointRaiseLower`: `thermal.operation.set_temperature` partial. `AcErrorCode`: `thermal.status.terminal_unit_fault` candidate. Every other dynamic element: no source. | `ControlSequenceOfOperation` and both `SetpointRaiseLower` fields. Identify's `M` elements, in the [bridge-identity note](bridge-identity.md): `IdentifyTime`, `IdentifyType`, command `Identify`. |
| Water Heater `0x050F` revision 1 | WaterHeaterManagement `0x0094` `M`; WaterHeaterMode `0x009E` `M`; Thermostat `0x0201` `M` with feature `HEAT`. Identify is `O`. | WaterHeaterMode `SupportedModes` and its `M` fields, `CurrentMode`, `ChangeToMode` field `NewMode`, `ChangeToModeResponse` field `Status`. Thermostat static gaps are the same three as Thermostat, and feature `HEAT` is outside that unconditional list. | `BoostState`: `thermal.overrun.one_time_dhw` candidate. `HeaterTypes`, `HeatDemand`, `Boost`, `CancelBoost`, `BoostStarted`, `BoostEnded`: no source. Thermostat dynamic attributes: the grades in the Thermostat row. Every other dynamic element: no source. | The WaterHeaterManagement and WaterHeaterMode gap rows in the [water-hydraulics note](water-hydraulics.md). Thermostat's three gaps are not expanded in that note. |
| Heat Pump `0x0309` revision 1 | Device file: Identify server `O`, Thermostat client `O`. No cluster of the thermostat note is a mandatory server in that file. | None on the device-file list. Schema device-type requirements name PowerSource `M`, DeviceEnergyManagement `M` and ElectricalSensor `M`. These notes do not treat that schema list as the device-file list. | No dynamic attribute is mandatory on the device-file list. Schema-composed clusters, if a later row mounts them, use the grades in the Solar Power, Battery Storage and DeviceEnergyManagement rows. | None on the device-file list. The schema list is unsettled. No boiler device type, as stated above. |
| Pump `0x0303` revision 4 | Identify `M`; OnOff `M`; PumpConfigurationAndControl `M`. | `MaxPressure`, `MaxSpeed`, `MaxFlow`, `EffectiveOperationMode`, `EffectiveControlMode`, `Capacity`, `OperationMode`. OnOff `OnOff`, `Off`, and `On` and `Toggle` at conformance `!OFFONLY`. | `Speed` `0x0014` is `O`, not mandatory: `thermal.measurement.pump_speed` partial, catalog `unit.reciprocal_second`. The Matter type is uint16 with no unit token. Every mandatory dynamic element of this device type: no source. | The seven PumpConfigurationAndControl attributes, the four OnOff rows, and Identify's `M` elements. See the [water-hydraulics note](water-hydraulics.md) and the [bridge-identity note](bridge-identity.md). |
| Aggregator `0x000E` revision 2, with Bridged Node `0x0013` revision 3 parts | Aggregator device file: no server is `M`. Base Descriptor `0x001D` is the bridge-identity reading, and the device file omits Descriptor. Bridged Node: BridgedDeviceBasicInformation `0x0039` `M`, plus the same Descriptor reading. | Descriptor `DeviceTypeList` `0x0000` and fields `DeviceType` and `Revision`, `ServerList`, `ClientList`, `PartsList`, and the six global attributes, on the bridge-identity reading. BridgedDeviceBasicInformation `Reachable` `0x0011`; event `ReachableChanged` and field `ReachableNewValue`. | No catalog element feeds those mandatory elements. `UniqueId` is not `M` at revision 6. Every dynamic element: no source. | The Descriptor list and the BridgedDeviceBasicInformation gaps in the [bridge-identity note](bridge-identity.md). |

## Mandatory elements without a source

Rows are the gap lists the notes wrote. Conformance is the text that note gives. A row is omitted where the note says the element has a catalog id. Clusters a note says are outside its tables and that another note expands are in the device-type section above and are not copied again here, except Identify is not given a second table: [bridge-identity note](bridge-identity.md) already state `IdentifyTime`, `IdentifyType` and command `Identify` have no catalog element, and that note does not call them mandatory for Aggregator, BridgedNode or RootNode.

| Device type | Cluster | Element | Conformance | Draft and line |
| --- | --- | --- | --- | --- |
| AirQualitySensor | AirQuality `0x005B` | AirQuality `0x0000` | `M` | [air-quality note](air-quality.md) |
| AirQualitySensor | AirQuality | FeatureMap 65532 | `M` | [air-quality note](air-quality.md) |
| AirQualitySensor | AirQuality | ClusterRevision 65533 | `M` | [air-quality note](air-quality.md) |
| TemperatureSensor | TemperatureMeasurement | MinMeasuredValue `0x0001` | `M` | [sensing note](sensing.md) |
| TemperatureSensor | TemperatureMeasurement | MaxMeasuredValue `0x0002` | `M` | [sensing note](sensing.md) |
| TemperatureSensor | TemperatureMeasurement | ClusterRevision `0xFFFD` | `M` on effective conformance | [sensing note](sensing.md) |
| PressureSensor | PressureMeasurement | MinMeasuredValue `0x0001` | `M` | [sensing note](sensing.md) |
| PressureSensor | PressureMeasurement | MaxMeasuredValue `0x0002` | `M` | [sensing note](sensing.md) |
| PressureSensor | PressureMeasurement | FeatureMap `0xFFFC` | `M` on effective conformance | [sensing note](sensing.md) |
| PressureSensor | PressureMeasurement | ClusterRevision `0xFFFD` | `M` on effective conformance | [sensing note](sensing.md) |
| FlowSensor | FlowMeasurement | MinMeasuredValue `0x0001` | `M` | [sensing note](sensing.md) |
| FlowSensor | FlowMeasurement | MaxMeasuredValue `0x0002` | `M` | [sensing note](sensing.md) |
| FlowSensor | FlowMeasurement | ClusterRevision `0xFFFD` | `M` on effective conformance | [sensing note](sensing.md) |
| HumiditySensor | RelativeHumidityMeasurement | MinMeasuredValue `0x0001` | `M` | [sensing note](sensing.md) |
| HumiditySensor | RelativeHumidityMeasurement | MaxMeasuredValue `0x0002` | `M` | [sensing note](sensing.md) |
| HumiditySensor | RelativeHumidityMeasurement | ClusterRevision `0xFFFD` | `M` on effective conformance | [sensing note](sensing.md) |
| Aggregator, BridgedNode, RootNode | Descriptor | DeviceTypeList `0x0000` | `M` | [bridge-identity note](bridge-identity.md) |
| Aggregator, BridgedNode, RootNode | Descriptor | DeviceTypeList.DeviceType | `M` | [bridge-identity note](bridge-identity.md) |
| Aggregator, BridgedNode, RootNode | Descriptor | DeviceTypeList.Revision | `M` | [bridge-identity note](bridge-identity.md) |
| Aggregator, BridgedNode, RootNode | Descriptor | ServerList `0x0001` | `M` | [bridge-identity note](bridge-identity.md) |
| Aggregator, BridgedNode, RootNode | Descriptor | ClientList `0x0002` | `M` | [bridge-identity note](bridge-identity.md) |
| Aggregator, BridgedNode, RootNode | Descriptor | PartsList `0x0003` | `M` | [bridge-identity note](bridge-identity.md) |
| Aggregator, BridgedNode, RootNode | Descriptor | GeneratedCommandList, AcceptedCommandList, EventList, AttributeList, FeatureMap, ClusterRevision | none declared; every server answers | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | DataModelRevision, VendorName, VendorId, ProductName, ProductId, NodeLabel, Location, HardwareVersion, HardwareVersionString, SoftwareVersion, SoftwareVersionString, CapabilityMinima | `M` | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | CapabilityMinima.CaseSessionsPerFabric, SubscriptionsPerFabric | `M` | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | CapabilityMinima.SimultaneousInvocationsSupported, SimultaneousWritesSupported, ReadPathsSupported, SubscribePathsSupported | `Rev >= v6` | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | UniqueId | `Rev >= v4, O` at revision 6 | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | SpecificationVersion, MaxPathsPerInvoke | `Rev >= v3` | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | ConfigurationVersion | `Rev >= v6` | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | StartUp `0x00`, field SoftwareVersion | `M` | [bridge-identity note](bridge-identity.md) |
| RootNode | BasicInformation | six global attributes | none declared | [bridge-identity note](bridge-identity.md) |
| BridgedNode | BridgedDeviceBasicInformation | Reachable | `M` | [bridge-identity note](bridge-identity.md) |
| BridgedNode | BridgedDeviceBasicInformation | UniqueId | `Rev >= v4, O` at revision 6 | [bridge-identity note](bridge-identity.md) |
| BridgedNode | BridgedDeviceBasicInformation | ReachableChanged `0x03`, field ReachableNewValue | `M` | [bridge-identity note](bridge-identity.md) |
| BridgedNode | BridgedDeviceBasicInformation | six global attributes | none declared | [bridge-identity note](bridge-identity.md) |
| ElectricalMeter; ElectricalSensor when the cluster is mounted | ElectricalPowerMeasurement | PowerMode `0x0000` | `M` | [electrical note](electrical.md) |
| ElectricalMeter; ElectricalSensor when mounted | ElectricalPowerMeasurement | NumberOfMeasurementTypes `0x0001` | `M` | [electrical note](electrical.md) |
| ElectricalMeter; ElectricalSensor when mounted | ElectricalPowerMeasurement | Accuracy `0x0002` and fields MeasurementType, Measured, MinMeasuredValue, MaxMeasuredValue, AccuracyRanges, RangeMin, RangeMax | `M` | [electrical note](electrical.md) |
| ElectricalMeter; ElectricalSensor when mounted | ElectricalEnergyMeasurement | Accuracy `0x0000` and the same `M` field set | `M` | [electrical note](electrical.md) |
| ElectricalUtilityMeter | MeterIdentification | MeterType `0x0000` | `M` | [electrical note](electrical.md) |
| ElectricalUtilityMeter | MeterIdentification | PointOfDelivery `0x0001` | `M` | [electrical note](electrical.md) |
| ElectricalUtilityMeter | MeterIdentification | MeterSerialNumber `0x0002` | `M` | [electrical note](electrical.md) |
| EnergyEvse | EnergyEvse | ChargingEnabledUntil, MinimumChargeCurrent, SessionId, SessionDuration | `M` | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvse | Disable | `M` | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvse | EnableCharging.ChargingEnabledUntil, EnableCharging.MinimumChargeCurrent | `M` | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvse | EvConnected, EvNotDetected, EnergyTransferStarted, EnergyTransferStopped, Fault | `M` | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvse | EvConnected.SessionId, EvNotDetected.SessionId, EvNotDetected.SessionDuration, EnergyTransferStarted.SessionId, EnergyTransferStopped.SessionId, EnergyTransferStopped.Reason, Fault.SessionId | `M` | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvse | feature PREF | `M` | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvse | NextChargeStartTime, NextChargeTargetTime, NextChargeRequiredEnergy, NextChargeTargetSoC, SetTargets, GetTargets, ClearTargets, GetTargetsResponse | `PREF` (feature text is `M`) | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvse | GetTargetsResponse.ChargingTargetSchedules, ChargingTargetSchedules.DayOfWeekForSequence, ChargingTargetSchedules.ChargingTargets, ChargingTargets.TargetTimeMinutesPastMidnight, SetTargets.ChargingTargetSchedules | `M` inside those `PREF` commands | [evse-dem note](evse-dem.md) |
| EnergyEvse | EnergyEvseMode | SupportedModes, CurrentMode, ChangeToMode, ChangeToModeResponse and fields Label, Mode, ModeTags, ModeTags.Value, NewMode, Status, StatusText | `M` | [evse-dem note](evse-dem.md) |
| DeviceEnergyManagement | DeviceEnergyManagement | EsaType, EsaCanGenerate, EsaState, AbsMinPower, AbsMaxPower | `M` | [evse-dem note](evse-dem.md) |
| PowerSource; composed PowerSource on BatteryStorage and SolarPower | PowerSource | Order `0x0001` | `M` | [storage-pv-power note](storage-pv-power.md) |
| PowerSource; composed PowerSource on BatteryStorage and SolarPower | PowerSource | Description `0x0002` | `M` | [storage-pv-power note](storage-pv-power.md) |
| PowerSource; composed PowerSource on BatteryStorage and SolarPower | PowerSource | EndpointList `0x001F` | `M` | [storage-pv-power note](storage-pv-power.md) |
| BatteryStorage PowerSource instance 2 | PowerSource | BatTimeRemaining `0x000D` | `[BAT]` | [storage-pv-power note](storage-pv-power.md) |
| BatteryStorage PowerSource instance 2 | PowerSource | BatTimeToFullCharge `0x001B` | `[RECHG]` | [storage-pv-power note](storage-pv-power.md) |
| BatteryStorage PowerSource instance 2 | PowerSource | ActiveBatChargeFaults `0x001E` | `[RECHG]` | [storage-pv-power note](storage-pv-power.md) |
| BatteryStorage PowerSource instance 2 | PowerSource | BatCapacity `0x0018` | `[REPLC \| RECHG]` | [storage-pv-power note](storage-pv-power.md) |
| SolarPower; BatteryStorage PowerSource instance 1 | PowerSource | feature WIRED bit 0 | `O.a` | [storage-pv-power note](storage-pv-power.md) |
| BatteryStorage PowerSource instance 2 | PowerSource | feature BAT bit 1 | `O.a` | [storage-pv-power note](storage-pv-power.md) |
| Thermostat; RoomAirConditioner | Thermostat | ControlSequenceOfOperation `0x001B` | `M` | [thermostat note](thermostat.md) |
| Thermostat; RoomAirConditioner | Thermostat | SetpointRaiseLower.Mode | `M` | [thermostat note](thermostat.md) |
| Thermostat; RoomAirConditioner | Thermostat | SetpointRaiseLower.Amount | `M` | [thermostat note](thermostat.md) |
| Fan | FanControl | FanMode `0x0000` | `M` | [thermostat note](thermostat.md) |
| Fan | FanControl | FanModeSequence `0x0001` | `M` | [thermostat note](thermostat.md) |
| Fan | FanControl | PercentCurrent `0x0003` | `M` | [thermostat note](thermostat.md) |
| WaterHeater | WaterHeaterManagement | HeaterTypes `0x0000` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | HeatDemand `0x0001` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | Boost `0x00` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | Boost.BoostInfo | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | Boost.BoostInfo.Duration | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | CancelBoost `0x01` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | BoostStarted `0x00` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | BoostStarted.BoostInfo | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | BoostStarted.BoostInfo.Duration | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterManagement | BoostEnded `0x01` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterMode | SupportedModes `0x0000` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterMode | SupportedModes.Label, Mode, ModeTags, ModeTags.Value | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterMode | CurrentMode `0x0001` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterMode | ChangeToMode `0x00`, field NewMode | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterHeater | WaterHeaterMode | ChangeToModeResponse `0x01`, field Status | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | PumpConfigurationAndControl | MaxPressure `0x0000` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | PumpConfigurationAndControl | MaxSpeed `0x0001` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | PumpConfigurationAndControl | MaxFlow `0x0002` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | PumpConfigurationAndControl | EffectiveOperationMode `0x0011` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | PumpConfigurationAndControl | EffectiveControlMode `0x0012` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | PumpConfigurationAndControl | Capacity `0x0013` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | PumpConfigurationAndControl | OperationMode `0x0020` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterValve | ValveConfigurationAndControl | OpenDuration `0x0000` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterValve | ValveConfigurationAndControl | DefaultOpenDuration `0x0001` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterValve | ValveConfigurationAndControl | RemainingDuration `0x0003` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterValve | ValveConfigurationAndControl | CurrentState `0x0004` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterValve | ValveConfigurationAndControl | TargetState `0x0005` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterValve | ValveConfigurationAndControl | Open `0x00` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterValve | ValveConfigurationAndControl | Close `0x01` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterFreezeDetector; WaterLeakDetector | BooleanState | CHGEVENT bit 0 | `[Rev >= v3]` | [water-hydraulics note](water-hydraulics.md) |
| WaterFreezeDetector; WaterLeakDetector | BooleanState | StateValue `0x0000` | `M` | [water-hydraulics note](water-hydraulics.md) |
| WaterFreezeDetector; WaterLeakDetector | BooleanState | StateChange `0x00` | `CHGEVENT, O` | [water-hydraulics note](water-hydraulics.md) |
| WaterFreezeDetector; WaterLeakDetector | BooleanState | StateChange.StateValue | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | OnOff | OnOff `0x0000` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | OnOff | Off `0x00` | `M` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | OnOff | On `0x01` | `!OFFONLY` | [water-hydraulics note](water-hydraulics.md) |
| Pump server; PumpController client | OnOff | Toggle `0x02` | `!OFFONLY` | [water-hydraulics note](water-hydraulics.md) |

[tariff note](tariff.md): no element of its three clusters is mandatory for ElectricalEnergyTariff. DeviceEnergyManagement `M` fields whose parent conformance is a feature name are `DEM-in` and are not in the device-file list ([evse-dem note](evse-dem.md)). DeviceEnergyManagementMode is not in that list.

## Catalog elements and their Matter targets

Target disposition is `unknown` / `matter.unmapped.v1` unless a row says otherwise. Loss text is the note's loss cell, shortened to the gaps it names.

### One measured-value attribute, many facts

TemperatureMeasurement `MeasuredValue` `0x0000`, partial, [sensing note](sensing.md). Loss: no unit on the catalog element; subject is one resource and one dimension; aggregation `member`; direction `not_applicable`; no nullability or range on the catalog element; Matter value is nullable int16 with constraint `minMeasuredValue to maxMeasuredValue`.

| Catalog element | Also named by another note |
| --- | --- |
| `pv.temperature.inverter` | —; catalog canonical unit `pv.temperature.inverter` `unit.kelvin` |
| `storage.temperature.cell` | [storage-pv-power note](storage-pv-power.md): no temperature attribute on PowerSource; catalog canonical unit `storage.temperature.cell` `unit.kelvin` |
| `storage.temperature.pack` | [storage-pv-power note](storage-pv-power.md): same; catalog canonical unit `storage.temperature.pack` `unit.kelvin` |
| `thermal.measurement.air_temperature` | [thermostat note](thermostat.md): partial to Thermostat `LocalTemperature` `0x0000`. Loss there: T-meas, nullability, aggregation `member` (pack `unit.kelvin`, 173.15 to 473.15, subject zone; Matter `temperature` int16). |
| `thermal.measurement.circuit_flow_temperature` | —; catalog canonical unit `thermal.measurement.circuit_flow_temperature` `unit.kelvin` |
| `thermal.measurement.dhw_temperature` | [water-hydraulics note](water-hydraulics.md): no temperature attribute in the water clusters. [thermostat note](thermostat.md): not counted as `LocalTemperature`.; catalog canonical unit `thermal.measurement.dhw_temperature` `unit.kelvin` |
| `thermal.measurement.heat_generator_flow_temperature` | —; catalog canonical unit `thermal.measurement.heat_generator_flow_temperature` `unit.kelvin` |
| `thermal.measurement.heat_generator_return_temperature` | —; catalog canonical unit `thermal.measurement.heat_generator_return_temperature` `unit.kelvin` |
| `thermal.measurement.outdoor_air_temperature` | [thermostat note](thermostat.md): partial to `OutdoorTemperature` `0x0001`. Loss: T-meas, nullability, subject thermal system.; catalog canonical unit `thermal.measurement.outdoor_air_temperature` `unit.kelvin` |
| `thermal.measurement.refrigerant_condensing_temperature` | —; catalog canonical unit `thermal.measurement.refrigerant_condensing_temperature` `unit.kelvin` |
| `thermal.measurement.refrigerant_evaporating_temperature` | —; catalog canonical unit `thermal.measurement.refrigerant_evaporating_temperature` `unit.kelvin` |
| `thermal.measurement.store_temperature` | [water-hydraulics note](water-hydraulics.md): TankPercentage and TankVolume are not this temperature.; catalog canonical unit `thermal.measurement.store_temperature` `unit.kelvin` |
| `thermal.measurement.system_flow_temperature` | —; catalog canonical unit `thermal.measurement.system_flow_temperature` `unit.kelvin` |

PressureMeasurement `MeasuredValue`, partial, [sensing note](sensing.md). Loss: the same gaps as temperature `MeasuredValue`. Elements: `thermal.measurement.refrigerant_high_side_pressure`, `thermal.measurement.refrigerant_low_side_pressure`, `thermal.measurement.water_pressure`. [water-hydraulics note](water-hydraulics.md): pump pressure attributes are int16 nameplate limits and are not `thermal.measurement.water_pressure`.

FlowMeasurement `MeasuredValue`, partial, [sensing note](sensing.md): `thermal.measurement.flow_rate`. Loss: no unit on the element; subject `resource.thermal_circuit`; aggregation `member`; direction `non_negative`; nullable; constraint `minMeasuredValue to maxMeasuredValue`. [water-hydraulics note](water-hydraulics.md): `MaxFlow` is a uint16 nameplate and is not this fact.

RelativeHumidityMeasurement `MeasuredValue`, partial, [sensing note](sensing.md): `thermal.measurement.humidity`. Loss: no unit on the element; subject `resource.zone`; aggregation `member`; direction `not_applicable`; nullable uint16; same min/max constraint. [air-quality note](air-quality.md) and [thermostat note](thermostat.md) place this fact outside those notes' clusters.

### Thermostat, fan

| Catalog element | Grade | Matter element | Loss | Draft line |
| --- | --- | --- | --- | --- |
| `thermal.setpoint.occupied_cooling` | partial | OccupiedCoolingSetpoint `0x0011` | T-set: pack `unit.kelvin` 223.15 to 423.15, subject zone; Matter `temperature` int16; `values.go` encodes setpoints as int16 times 0.01 °C | [thermostat note](thermostat.md) |
| `thermal.setpoint.occupied_heating` | partial | OccupiedHeatingSetpoint `0x0012` | T-set | [thermostat note](thermostat.md); catalog canonical unit `thermal.setpoint.occupied_heating` `unit.kelvin` |
| `thermal.setpoint.unoccupied_cooling` | partial | UnoccupiedCoolingSetpoint `0x0013` | T-set | [thermostat note](thermostat.md); catalog canonical unit `thermal.setpoint.unoccupied_cooling` `unit.kelvin` |
| `thermal.setpoint.unoccupied_heating` | partial | UnoccupiedHeatingSetpoint `0x0014` | T-set | [thermostat note](thermostat.md); catalog canonical unit `thermal.setpoint.unoccupied_heating` `unit.kelvin` |
| `thermal.mode.system` | partial | SystemMode `0x001C` | enumeration; subject; feature gates not in the catalog | [thermostat note](thermostat.md); catalog canonical unit `thermal.mode.system` none |
| `thermal.mode.terminal_unit` | candidate | SystemMode `0x001C` | same | [thermostat note](thermostat.md); catalog canonical unit `thermal.mode.terminal_unit` none |
| `thermal.operation.set_mode` | partial | SystemMode `0x001C` | same | [thermostat note](thermostat.md) |
| `thermal.action.state` | partial | ThermostatRunningMode `0x001E` | enumeration; subject; conformance gates | [thermostat note](thermostat.md); catalog canonical unit `thermal.action.state` none |
| `thermal.status.terminal_unit_fault` | candidate | AcErrorCode `0x0044` | enumeration | [thermostat note](thermostat.md); catalog canonical unit `thermal.status.terminal_unit_fault` none |
| `thermal.operation.set_temperature` | partial | SetpointRaiseLower `0x00` | command shape; enumeration. [sensing note](sensing.md): the four measurement clusters have no command, so this operation is not a MeasuredValue feeder. | [thermostat note](thermostat.md) |
| `thermal.demand.level` | partial | FanControl PercentSetting `0x0002` | unit; resolution; nullability; subject. Pack quantity on the ventilation system, `unit.ratio`, 0 to 1. [air-quality note](air-quality.md): no demand element in the air-quality clusters. | [thermostat note](thermostat.md) |

`thermal.measurement.air_temperature` and `thermal.measurement.outdoor_air_temperature` are in the temperature table above.

### Water

| Catalog element | Grade | Matter element | Loss | Draft line |
| --- | --- | --- | --- | --- |
| `thermal.overrun.one_time_dhw` | candidate | BoostState `0x0005` | symbol fact, no values list; BoostStateEnum Inactive 0 / Active 1; subject `resource.thermal_system` | [water-hydraulics note](water-hydraulics.md); catalog canonical unit `thermal.overrun.one_time_dhw` none |
| `thermal.measurement.pump_speed` | partial | Pump Speed `0x0014` | quantity, subject `resource.pump`, no unit attribute; Matter uint16, no unit token, nullable | [water-hydraulics note](water-hydraulics.md); catalog canonical unit `thermal.measurement.pump_speed` `unit.reciprocal_second` |
| `thermal.measurement.valve_position` | partial | Valve CurrentLevel `0x0006` | quantity, subject `resource.terminal_unit`, no unit; Matter percent uint8 max 100, nullable, conformance `LVL`; catalog has no `resource.valve` | [water-hydraulics note](water-hydraulics.md); catalog canonical unit `thermal.measurement.valve_position` `unit.ratio` |

### Electrical measurement and energy

ElectricalPowerMeasurement and ElectricalEnergyMeasurement, [electrical note](electrical.md). Shared loss themes that note names: catalog `unit.volt` / `unit.ampere` / `unit.watt` / `unit.joule` / `unit.hertz` / `unit.ratio` against Matter `voltage-mV`, `amperage-mA`, `power-mW`, `power-mVAR`, `power-mVA`, `energy-mWh`, or an int64 whose type name has no unit; no conversion row except the one on `evse.ac.current`; one cluster value against a phase member, an aggregate, a pack, or a grid connection; nullable and range against no numeric range on the catalog element.

| Catalog element | Grade | Matter element | Draft line |
| --- | --- | --- | --- |
| `evse.ac.voltage`, `infrastructure.ac.voltage`, `pv.ac.voltage`, `pv.ac.aggregate_voltage`, `pv.dc.voltage`, `pv.dc.aggregate_voltage`, `storage.pack.voltage` | partial | Voltage `0x0004` | 125; catalog canonical unit `evse.ac.voltage` `unit.volt`, `infrastructure.ac.voltage` `unit.volt`, `pv.ac.voltage` `unit.volt`, `pv.ac.aggregate_voltage` `unit.volt`, `pv.dc.voltage` `unit.volt`, `pv.dc.aggregate_voltage` `unit.volt`, `storage.pack.voltage` `unit.volt` |
| `evse.ac.voltage`, `infrastructure.ac.voltage`, `pv.ac.voltage`, `pv.ac.aggregate_voltage` | candidate | RmsVoltage `0x000B`. Loss adds: RMS is not declared. DC voltage facts are not listed on this attribute. | 132; catalog canonical unit `evse.ac.voltage` `unit.volt`, `infrastructure.ac.voltage` `unit.volt`, `pv.ac.voltage` `unit.volt`, `pv.ac.aggregate_voltage` `unit.volt` |
| `evse.ac.current`, `infrastructure.ac.current`, `pv.ac.current`, `pv.ac.aggregate_current`, `pv.dc.current`, `pv.dc.aggregate_current`, `storage.pack.current` | partial | ActiveCurrent `0x0005` | 126; catalog canonical unit `evse.ac.current` `unit.ampere`, `infrastructure.ac.current` `unit.ampere`, `pv.ac.current` `unit.ampere`, `pv.ac.aggregate_current` `unit.ampere`, `pv.dc.current` `unit.ampere`, `pv.dc.aggregate_current` `unit.ampere`, `storage.pack.current` `unit.ampere` |
| `evse.ac.current` | partial, and the target row is `transformed` / `matter.phase_association_by_relation.v1` | ActiveCurrent. Loss the note records on that row: `exact_multiply` factor 1000 from `unit.ampere` to `amperage-mA`, `require_integral_result` true, loss kind `unit`, `reversible` false; signed integer minimum -4611686018427387904 maximum 4611686018427387904, nullable; emission requires a non-null value, one eligible source key, required dimension `evse.dimension.phase`. | 126 |
| `evse.ac.current`, `infrastructure.ac.current`, `pv.ac.current`, `pv.ac.aggregate_current` | candidate | RmsCurrent `0x000C`. The conversion row targets ActiveCurrent. | 133; catalog canonical unit `evse.ac.current` `unit.ampere`, `infrastructure.ac.current` `unit.ampere`, `pv.ac.current` `unit.ampere`, `pv.ac.aggregate_current` `unit.ampere` |
| `evse.ac.active_power`, `infrastructure.ac.active_power`, `pv.ac.active_power`, `pv.ac.aggregate_active_power`, `pv.dc.aggregate_power`, `pv.dc.power`, `storage.pack.power`, `infrastructure.power.pcc`, `infrastructure.power.import_active`, `infrastructure.power.export_active` | partial | ActivePower `0x0008` | 129; catalog canonical unit `evse.ac.active_power` `unit.watt`, `infrastructure.ac.active_power` `unit.watt`, `pv.ac.active_power` `unit.watt`, `pv.ac.aggregate_active_power` `unit.watt`, `pv.dc.aggregate_power` `unit.watt`, `pv.dc.power` `unit.watt`, `storage.pack.power` `unit.watt`, `infrastructure.power.pcc` `unit.watt`, `infrastructure.power.import_active` `unit.watt`, `infrastructure.power.export_active` `unit.watt` |
| `evse.ac.active_power`, `infrastructure.ac.active_power`, `pv.ac.active_power`, `pv.ac.aggregate_active_power` | candidate | RmsPower `0x000D` | 134; catalog canonical unit `evse.ac.active_power` `unit.watt`, `infrastructure.ac.active_power` `unit.watt`, `pv.ac.active_power` `unit.watt`, `pv.ac.aggregate_active_power` `unit.watt` |
| `infrastructure.ac.reactive_power`, `pv.ac.reactive_power`, `pv.ac.aggregate_reactive_power`, `infrastructure.power.import_reactive`, `infrastructure.power.export_reactive` | partial | ReactivePower `0x0009` | 130; catalog canonical unit `infrastructure.ac.reactive_power` `unit.volt_ampere_reactive`, `pv.ac.reactive_power` `unit.volt_ampere_reactive`, `pv.ac.aggregate_reactive_power` `unit.volt_ampere_reactive`, `infrastructure.power.import_reactive` `unit.volt_ampere_reactive`, `infrastructure.power.export_reactive` `unit.volt_ampere_reactive` |
| `infrastructure.ac.apparent_power`, `pv.ac.apparent_power`, `pv.ac.aggregate_apparent_power`, `infrastructure.power.apparent` | partial | ApparentPower `0x000A` | 131; catalog canonical unit `infrastructure.ac.apparent_power` `unit.volt_ampere`, `pv.ac.apparent_power` `unit.volt_ampere`, `pv.ac.aggregate_apparent_power` `unit.volt_ampere`, `infrastructure.power.apparent` `unit.volt_ampere` |
| `evse.ac.frequency`, `infrastructure.ac.frequency`, `pv.ac.frequency` | partial | Frequency `0x000E` | 135; catalog canonical unit `evse.ac.frequency` `unit.hertz`, `infrastructure.ac.frequency` `unit.hertz`, `pv.ac.frequency` `unit.hertz` |
| `infrastructure.ac.power_factor`, `pv.ac.power_factor` | partial | PowerFactor `0x0011` | 140; catalog canonical unit `infrastructure.ac.power_factor` `unit.ratio`, `pv.ac.power_factor` `unit.ratio` |
| `infrastructure.energy.import` | partial | CumulativeEnergyImported `0x0001` and field Energy, and event field CumulativeEnergyMeasured.EnergyImported | 173, 217; catalog canonical unit `infrastructure.energy.import` `unit.joule` |
| `evse.energy.lifetime` | candidate | same imported cumulative elements | 173, 217; catalog canonical unit `evse.energy.lifetime` `unit.joule` |
| `storage.energy.charged` | candidate | same imported cumulative elements | 173, 217; catalog canonical unit `storage.energy.charged` `unit.joule` |
| `infrastructure.energy.export` | partial | CumulativeEnergyExported `0x0002` and field Energy, and CumulativeEnergyMeasured.EnergyExported | 181, 218; catalog canonical unit `infrastructure.energy.export` `unit.joule` |
| `pv.energy.generated`, `storage.energy.discharged`, `pv.dc.energy` | candidate | same exported cumulative elements | 181, 218; catalog canonical unit `pv.energy.generated` `unit.joule`, `storage.energy.discharged` `unit.joule`, `pv.dc.energy` `unit.joule` |
| `evse.energy.session` | candidate | PeriodicEnergyImported `0x0003` and field Energy, and PeriodicEnergyMeasured.EnergyImported | 189, 220; catalog canonical unit `evse.energy.session` `unit.joule` |
| `pv.energy.yield_day`, `pv.energy.yield_month`, `pv.energy.yield_year` | candidate | PeriodicEnergyExported `0x0004` and field Energy, and PeriodicEnergyMeasured.EnergyExported | 197, 221; catalog canonical unit `pv.energy.yield_day` `unit.joule`, `pv.energy.yield_month` `unit.joule`, `pv.energy.yield_year` `unit.joule` |

`storage.pack.voltage` is also partial to PowerSource `BatVoltage` ([storage-pv-power note](storage-pv-power.md)): `unit.volt` against uint32 with no unit and no conversion row; nullable; subject `resource.battery_pack`. `storage.pack.current` is also partial to `BatChargingCurrent`: `unit.ampere` against uint32 with no unit; catalog direction `signed` against an unsigned type.

Five relations are withheld on target cluster_id 156 and are not the value of a PowerTopology element ([electrical note](electrical.md)): `evse.relation.evse_meter`, `infrastructure.relation.feeder_circuit`, `infrastructure.relation.grid_connection_feeder`, `infrastructure.relation.grid_connection_meter`, `pv.relation.inverter_array`. Loss stated there: loss kind identity and irreversible in the markdown account; equivalence `Hypothesis`; attributes are lists of `endpoint-no`; the target allocates no endpoint.

### EVSE

| Catalog element | Grade | Matter element | Loss | Draft line |
| --- | --- | --- | --- | --- |
| `evse.status.connection`, `evse.status.charging` | candidate | State `0x0000` and the State fields on events EvNotDetected, EnergyTransferStarted, EnergyTransferStopped, Fault | connection symbols connected/disconnected and charging symbols charging/complete/idle against StateEnum of seven values; subject `resource.connector`; attribute carries no connector id | [evse-dem note](evse-dem.md); catalog canonical unit `evse.status.connection` none, `evse.status.charging` none |
| `evse.status.readiness`, `evse.status.interlock` | candidate | SupplyState `0x0001` | readiness not_ready/ready and interlock active/clear against SupplyStateEnum Disabled, ChargingEnabled, DischargingEnabled, DisabledError, DisabledDiagnostics, Enabled | [evse-dem note](evse-dem.md); catalog canonical unit `evse.status.readiness` none, `evse.status.interlock` none |
| `evse.status.fault` | candidate | FaultState `0x0002` and Fault event fields FaultStatePreviousState, FaultStateCurrentState | symbols clear/present against 17 cause values | [evse-dem note](evse-dem.md); catalog canonical unit `evse.status.fault` none |
| `evse.limit.configured_current` | partial | CircuitCapacity `0x0005` | `unit.ampere` against `amperage-mA`; the factor-1000 conversion is on `evse.ac.current` only; catalog range coefficient 0 exponent 0 through coefficient 1 exponent 3; subject `resource.evse` | [evse-dem note](evse-dem.md) |
| `evse.limit.advertised_current`, `evse.limit.allocated_current` | candidate | MaximumChargeCurrent `0x0007`, EnableCharging.MaximumChargeCurrent, EnergyTransferStarted.MaximumCurrent | two connector-scoped ampere facts and the sources do not choose; `unit.ampere` against `amperage-mA`; no conversion on these rows | [evse-dem note](evse-dem.md) |
| `evse.energy.session` | partial | SessionEnergyCharged `0x0042` | `unit.joule` against `energy-mWh`; no scale on the row; subject `resource.charging_session`; the fact does not split charge from discharge; attribute nullable | [evse-dem note](evse-dem.md) |
| `evse.energy.session` | candidate | EvNotDetected.SessionEnergyCharged, EnergyTransferStopped.EnergyTransferred | same unit and session-scope loss | [evse-dem note](evse-dem.md); catalog canonical unit `evse.energy.session` `unit.joule` |
| `evse.operation.set_allocated_current` | candidate | EnableCharging `0x02` | the operation argument is one current fact; the command has an until-timestamp, a minimum and a maximum | [evse-dem note](evse-dem.md) |

The same `evse.energy.session` is a candidate on PeriodicEnergyImported in the electrical table.

### Power source

| Catalog element | Grade | Matter element | Loss | Draft line |
| --- | --- | --- | --- | --- |
| `storage.status.operating`, `pv.status.operating` | candidate | Status `0x0000` | symbol against PowerSourceStatusEnum; literals are not in the element record or the pack-metadata field; subjects `resource.battery_pack` and `resource.inverter` | [storage-pv-power note](storage-pv-power.md); catalog canonical unit `storage.status.operating` none, `pv.status.operating` none |
| `storage.state.soc` | partial | BatPercentRemaining `0x000C` | `unit.ratio` against uint8 `max 200`; no scale; nullable; no minimum in the constraint | [storage-pv-power note](storage-pv-power.md) |
| `storage.status.warning`, `storage.status.alarm` | candidate | BatChargeLevel `0x000E` | one symbol each against BatChargeLevelEnum; literals not in the records | [storage-pv-power note](storage-pv-power.md); catalog canonical unit `storage.status.warning` none, `storage.status.alarm` none |
| `storage.status.protection` | candidate | ActiveBatFaults `0x0012` | one symbol against a list of BatFaultEnum | [storage-pv-power note](storage-pv-power.md); catalog canonical unit `storage.status.protection` none |
| `storage.capacity.charge`, `storage.capacity.discharge` | candidate | BatCapacity `0x0018` | cumulative lifetime counters (`pack_terminals_lifetime_counter`) against a Fixed uint32; no derivation to a fixed capacity; `unit.ampere_hour` against uint32 with no unit; two facts against one attribute; which fact is the attribute is not declared | [storage-pv-power note](storage-pv-power.md) |

`storage.pack.voltage` and `storage.pack.current` are in the electrical section above.

Air-quality, bridge-identity and tariff name no catalog element as `exact`, `partial` or `candidate`. Their catalog hits are in the next section or are absent proposed ids.

## Catalog elements with no Matter counterpart

Union of the nine "without a Matter element" sections. An id that another note grades as a feed is in the overlap list, with that feed, and is not described here as having no Matter element.

### No feed in any of the nine notes

[air-quality note](air-quality.md): `thermal.status.maintenance`, `thermal.relation.air_supply`, `resource.ventilation_system`, `thermal.dimension.ventilation`, `thermal.service.ventilation`, `thermal.capability.read.ventilation`. (`thermal.demand.level` and `thermal.measurement.humidity` are overlaps.)

[bridge-identity note](bridge-identity.md): `resource.equipment`; lenses `lens.installation_hierarchy`, `lens.equipment_composition`, `lens.provenance`.

[sensing note](sensing.md), for the four measurement clusters: `thermal.setpoint.temperature_setpoint`, `thermal.setpoint.dhw_temperature_setpoint`, `thermal.capability.set_temperature`, `thermal.effect.set_temperature`, `thermal.portal.operation.set_temperature`. (`thermal.operation.set_temperature` is an overlap.)

[thermostat note](thermostat.md), for thermostat, fan and occupancy clusters: `thermal.setpoint.temperature_setpoint`, `thermal.setpoint.dhw_temperature_setpoint`, `thermal.capability.set_temperature`, `thermal.capability.set_mode`, `thermal.effect.set_temperature`, `thermal.effect.set_mode`, `thermal.capability.read.zone`, `thermal.capability.read.ventilation`, `thermal.capability.read.terminal_unit`, `thermal.capability.read.system`, `thermal.status.operation`, `thermal.status.fault`, `thermal.status.maintenance`, `thermal.status.heat_generator_operation`, `thermal.status.heat_generator_fault`, `thermal.status.terminal_unit_operation`, `thermal.overrun.one_day_away`, `thermal.overrun.one_day_at_home`, `thermal.overrun.party`, and the other seven `thermal.overrun.*` ids that line 357 does not name, `thermal.relation.air_supply`, `resource.zone`, `resource.ventilation_system`, `resource.terminal_unit`.

[water-hydraulics note](water-hydraulics.md) (25 ids; the three measurement overlaps are excluded here): `resource.domestic_hot_water`, `resource.pump`, `resource.thermal_store`, `thermal.dimension.dhw`, `thermal.dimension.pump`, `thermal.dimension.thermal_store`, `thermal.service.dhw`, `thermal.service.pump`, `thermal.service.thermal_store`, `thermal.capability.read.dhw`, `thermal.capability.read.thermal_store`, `thermal.setpoint.dhw_temperature_setpoint`, `thermal.energy.heat_output`, `thermal.measurement.thermal_power`, `thermal.overrun.valve_kick`, `thermal.portal.read.dhw`, `thermal.portal.read.pump`, `thermal.portal.read.thermal_store`, `thermal.relation.fluid_supply`, `thermal.relation.system_member`, `relation.thermal_control`. The note says the catalog has no `thermal.capability.read.pump`.

[electrical note](electrical.md), excluding ids that are feeds in this note: `infrastructure.ac.voltage_line_line`, `infrastructure.energy.self_consumption`, `storage.energy.nominal_capacity`, `storage.energy.remaining`, `storage.energy.usable_capacity`, `storage.cell.voltage_minimum`, `storage.cell.voltage_maximum`, `infrastructure.limit.fallback_power`, `pv.limit.active_power`, `pv.limit.active_power_ratio`, `pv.limit.export_power`, `storage.limit.charge_power`, `storage.limit.discharge_power`, `evse.limit.actual_current`, `evse.limit.allocated_current_phase`, `resource.meter`, `resource.phase`, `resource.grid_connection`, `resource.line_pair`, `resource.electrical_circuit`, `resource.feeder`, `infrastructure.status.breaker`, `infrastructure.status.connection`, `infrastructure.status.fault`, `infrastructure.status.interlock`, `infrastructure.status.readiness`. Relations with target reason `matter.relation_construct_not_adopted.v1`: `evse.relation.connector_phase`, `infrastructure.relation.circuit_phase`, `infrastructure.relation.site_grid_connection`, `evse.relation.asset_evse`, `evse.relation.connector_session`, `evse.relation.evse_connector`, `pv.relation.array_string`, `pv.relation.inverter_input`, `pv.relation.inverter_phase`, `pv.relation.system_inverter`, `storage.relation.battery_pack`, `storage.relation.module_cell`, `storage.relation.pack_interface`, `storage.relation.pack_module`, `storage.relation.pack_string`, `storage.relation.system_battery`. Services: `evse.service.meter`, `evse.service.phase`, `infrastructure.service.meter`, `infrastructure.service.phase`, `infrastructure.service.grid_connection`, `infrastructure.service.line_pair`, `infrastructure.service.circuit`, `infrastructure.service.feeder`. Capabilities: `evse.capability.read.meter`, `evse.capability.read.phase`, `infrastructure.capability.read.meter`, `infrastructure.capability.read.phase`, `infrastructure.capability.read.grid_connection`, `infrastructure.capability.read.circuit`, `infrastructure.capability.read.feeder`. The five withheld topology relations are in the previous section; the electrical note also lists them here because no element value is the relation.

EVSE lines 406–428, the ids with no feed cell in those five clusters and no feed in another note: `evse.limit.actual_current`, `evse.limit.allocated_current_phase`, capabilities `evse.capability.read.connector`, `read.evse`, `read.meter`, `read.phase`, `read.session`, `evse.capability.set_allocated_current`, dimensions `evse.dimension.asset`, `connector`, `evse`, `meter`, `phase`, `session`, `evse.effect.set_allocated_current`, relations `evse.relation.asset_evse`, `connector_phase`, `connector_session`, `evse_connector`, `evse.relation.evse_meter` (withheld, cluster_id 156), services `evse.service.connector`, `evse`, `meter`, `phase`, `session`, presentations `evse.portal.operation.set_allocated_current`, `portal.read.connector`, `portal.read.evse`, `portal.read.meter`, `portal.read.phase`, `portal.read.session`, resource kinds `resource.charging_station`, `resource.charging_session`, `resource.connector`, `resource.evse`.

[storage-pv-power note](storage-pv-power.md), excluding temperature facts that sensing feeds and energy facts that electrical feeds: `storage.state.soh`, `storage.energy.nominal_capacity`, `storage.energy.usable_capacity`, `storage.energy.remaining`, `storage.cell.voltage_minimum`, `storage.cell.voltage_maximum`, `storage.status.interlock`, `pv.status.fault`, `pv.status.derating`. The same storage and PV relations as the electrical list, plus `pv.relation.inverter_array` withheld on cluster 156.

[tariff note](tariff.md): that note's domain list is empty.

### On one note's without-list, and a feed in another

| Id | Without-list | Feed |
| --- | --- | --- |
| `thermal.demand.level` | [air-quality note](air-quality.md) | FanControl PercentSetting, [thermostat note](thermostat.md); catalog canonical unit `thermal.demand.level` `unit.ratio` |
| `thermal.measurement.humidity` | [air-quality note](air-quality.md); [thermostat note](thermostat.md) | RelativeHumidity MeasuredValue, [sensing note](sensing.md); catalog canonical unit `thermal.measurement.humidity` `unit.ratio` |
| `thermal.measurement.flow_rate` | [water-hydraulics note](water-hydraulics.md) | Flow MeasuredValue, [sensing note](sensing.md); catalog canonical unit `thermal.measurement.flow_rate` `unit.cubic_metre_per_second` |
| `thermal.measurement.water_pressure` | [water-hydraulics note](water-hydraulics.md) | Pressure MeasuredValue, [sensing note](sensing.md); catalog canonical unit `thermal.measurement.water_pressure` `unit.pascal` |
| `thermal.measurement.dhw_temperature` | [water-hydraulics note](water-hydraulics.md); [thermostat note](thermostat.md) | Temperature MeasuredValue, [sensing note](sensing.md); catalog canonical unit `thermal.measurement.dhw_temperature` `unit.kelvin` |
| `thermal.measurement.store_temperature` | [water-hydraulics note](water-hydraulics.md) | Temperature MeasuredValue, [sensing note](sensing.md); catalog canonical unit `thermal.measurement.store_temperature` `unit.kelvin` |
| `thermal.operation.set_temperature` | [sensing note](sensing.md) (not a MeasuredValue feeder) | SetpointRaiseLower, [thermostat note](thermostat.md) |
| `storage.temperature.cell`, `storage.temperature.pack` | [storage-pv-power note](storage-pv-power.md) | Temperature MeasuredValue, [sensing note](sensing.md); catalog canonical unit `storage.temperature.cell` `unit.kelvin`, `storage.temperature.pack` `unit.kelvin` |
| `storage.capacity.charge`, `storage.capacity.discharge` | [electrical note](electrical.md) (no ampere-hour attribute in the electrical clusters) | BatCapacity candidate, not a fixed-capacity derivation, [storage-pv-power note](storage-pv-power.md); catalog canonical unit `storage.capacity.charge` `unit.ampere_hour`, `storage.capacity.discharge` `unit.ampere_hour` |
| `storage.energy.charged` | [storage-pv-power note](storage-pv-power.md) (no energy-total on PowerSource) | CumulativeEnergyImported, [electrical note](electrical.md); catalog canonical unit `storage.energy.charged` `unit.joule` |
| `storage.energy.discharged` | [storage-pv-power note](storage-pv-power.md) | CumulativeEnergyExported, [electrical note](electrical.md); catalog canonical unit `storage.energy.discharged` `unit.joule` |
| `evse.ac.active_power`, `evse.ac.current`, `evse.ac.frequency`, `evse.ac.voltage` | [evse-dem note](evse-dem.md) (no matching attribute in the five EVSE clusters) | ActivePower, ActiveCurrent, Frequency, Voltage, [electrical note](electrical.md); catalog canonical unit `evse.ac.active_power` `unit.watt`, `evse.ac.current` `unit.ampere`, `evse.ac.frequency` `unit.hertz`, `evse.ac.voltage` `unit.volt` |
| `evse.energy.lifetime` | [evse-dem note](evse-dem.md) | CumulativeEnergyImported candidate, [electrical note](electrical.md); catalog canonical unit `evse.energy.lifetime` `unit.joule` |
| `evse.limit.configured_current`, `evse.limit.advertised_current`, `evse.limit.allocated_current` | [electrical note](electrical.md) (not measured attributes of the electrical clusters) | CircuitCapacity, MaximumChargeCurrent, [evse-dem note](evse-dem.md); catalog canonical unit `evse.limit.configured_current` `unit.ampere`, `evse.limit.advertised_current` `unit.ampere`, `evse.limit.allocated_current` `unit.ampere` |
| `evse.status.charging`, `evse.status.connection`, `evse.status.fault`, `evse.status.interlock`, `evse.status.readiness` | [electrical note](electrical.md) (no attribute in the electrical clusters) | State, SupplyState, FaultState, [evse-dem note](evse-dem.md); catalog canonical unit `evse.status.charging` none, `evse.status.connection` none, `evse.status.fault` none, `evse.status.interlock` none, `evse.status.readiness` none |
| `evse.energy.session` | electrical lists it as a candidate, not as a without-row | SessionEnergyCharged and PeriodicEnergyImported, above; catalog canonical unit `evse.energy.session` `unit.joule` |

## Disagreements between drafts and with the prior accounting

### Between notes, checked in go-fabric v0.22.2

1. HeatPump. [thermostat note](thermostat.md): `go-fabric@v0.22.2:device/heat_pump_gen.go` lines 29–39 and `go-fabric@v0.22.2:docs/reference/device-types.md` lines 594–598 declare one optional server, Identify `O`, and one optional client, Thermostat `O`, and the note treats `a prior accounting` a prior claim's mandatory Power Source, electrical measurement clusters, Device Energy Management and UserLabel as contradicted by those two files. [bridge-identity note](bridge-identity.md), citing `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 2030–2068: Identify conformance `O` is direct; UserLabel conformance `M` is nested under device type Thermostat `0x0301` whose conformance is `O`; UserLabel is not a direct server with conformance `M`. go-fabric v0.22.2: `go-fabric@v0.22.2:device/heat_pump_gen.go` lines 29–39 and `go-fabric@v0.22.2:docs/reference/device-types.md` lines 592–598 match the thermostat note. `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 2030–2106 also require device type PowerSource conformance `M` (line 2042, inside the bridge note's cited range, not named in that note's disagreement sentence), device type DeviceEnergyManagement conformance `M` with feature `PA` `M`, and device type ElectricalSensor conformance `M` constraint `min 1` with ElectricalPowerMeasurement conformance `M` (feature `ALTC`, attributes `Voltage` and `ActiveCurrent`) and ElectricalEnergyMeasurement conformance `M`. Optional device types in that block: Thermostat (UserLabel `M` nested, lines 2058–2061), TemperatureSensor, WaterHeater. `go-fabric@v0.22.2:device/device.go` `composes` lines 658–678 reports whether a schema device-type requirement names another device type. It does not copy servers onto the child. The electrical note already records that function's limit ([electrical note](electrical.md)). Which list a constructed HeatPump mounts is not settled by these lines.

2. Descriptor. [bridge-identity note](bridge-identity.md) treat Base Descriptor conformance `M` as mandatory for Aggregator, BridgedNode and RootNode. [sensing note](sensing.md), [electrical note](electrical.md), [air-quality note](air-quality.md) and [storage-pv-power note](storage-pv-power.md) record a schema Descriptor row with no conformance key and do not call it mandatory. [tariff note](tariff.md): the ElectricalEnergyTariff device file sets `Mandatory: true` on Descriptor. `go-fabric@v0.22.2:schema/devicetype_requirements.go` lines 190–193: `BaseDeviceTypes` returns the Base device type, whose requirements apply to every endpoint that lists a device type. `go-fabric@v0.22.2:cluster/spec/conformance.go` lines 208–209: `ConfEmpty` is `ApplicabilityOptional`. `go-fabric@v0.22.2:device/doc.go` lines 33–35: the assembler mounts Descriptor, Identify, BridgedDeviceBasicInformation, Groups and ScenesManagement on every endpoint, and the device package does not mount them. The bridge note's uncertainty already says it did not find a validator call that applies the empty-op rule to the per-device Descriptor row. Both texts are in go-fabric. This note does not pick one.

3. Global attributes. [air-quality note](air-quality.md) and [sensing note](sensing.md) include `FeatureMap` and `ClusterRevision` from schema effective conformance `M` in the mandatory gap list. [bridge-identity note](bridge-identity.md) include six globals whose conformance text is not `M`, citing `go-fabric@v0.22.2:cluster/spec/instance.go` lines 15–22. [electrical note](electrical.md), [thermostat note](thermostat.md), and [storage-pv-power note](storage-pv-power.md) leave those ids out of cluster element rows. `go-fabric@v0.22.2:cluster/spec/instance.go` lines 15–22 names the six ids and the comment says every server answers them. The cluster `Definition.Attributes` slices the notes cite omit them. `schema.json` effective conformance `M` is what air-quality and sensing cite. The three readings match three places in the module. This note keeps each note's own list.

4. Mandatory clients. [water-hydraulics note](water-hydraulics.md) scores PumpController's mandatory clients with the cluster element's conformance, and the gap table includes those rows. [sensing note](sensing.md): client requirements are not server mandates. [thermostat note](thermostat.md): ThermostatController's mandatory Thermostat client is not scored as mandatory server elements. go-fabric shows the client requirements on the device files the notes cite. It does not, in the lines read for this disagreement, say which of those scoring rules a complete endpoint uses.

5. Domain scope of "no Matter element". The overlap table in the previous section is the list. Each note's sentence is about its own clusters. The sentences disagree only if read as a claim about the whole Matter model.

### With the prior accounting, as each note states it

Prior claims were checked against the go-fabric texts and the pinned catalog named with each item. The items below are the notes' disagreement sections, not a new reading of those audits.

[air-quality note](air-quality.md): filter `LastChangedTime` and `ResetCondition` access in the prior accounting is `W`; the generated definitions say `RW` with the privileges that note names. prior accounting attribute access omits the view privilege. prior accounting marks concentration `MinMeasuredValue` and `MaxMeasuredValue` absent by derivation from field bounds; the attributes exist, conformance `MEA`, and the catalog has no bounds element. `a prior accounting` a prior claim calls both filter clusters a partial match to `thermal.status.maintenance`; the catalog row is a symbol on `resource.thermal_system` with no symbol values, target `unknown` / `matter.unmapped.v1`. The shared `MeasurementUnitEnum` has no per-cluster subset. a prior claim says the group is absent in SemReg, which matches the catalog, and `a prior accounting` line 347 says the ten concentration clusters were not opened.

[sensing note](sensing.md): the prior accounting omits `ClusterRevision` and pressure `FeatureMap` that `schema.json` includes. Temperature MeasuredValue's prior accounting status does not match a finished target row for the ids that exist, and names ids that are absent. `storage.temperature.cell` is in the catalog and not in the prior accounting MeasuredValue list. Min and Max are `absent` in the prior accounting for a bounds derivation the catalog facts do not support. Pressure scale-in-pascal and flow-as-water are not in the catalog records.

[electrical note](electrical.md): PowerTopology `ActiveEndpoints` is declared, conformance `DYPF`, and the prior accounting calls it absent as deprecated or disallowed. Rows marked `present` have target disposition `unknown` / `matter.unmapped.v1` except `evse.ac.current`. Rows marked `planned` name ids already in the catalog. RMS is not a marker on the pack-metadata fields. The prior accounting's present-lists omit `pv.ac.aggregate_current` and `pv.ac.aggregate_voltage`.

[bridge-identity note](bridge-identity.md): BridgedDeviceBasicInformation attributes whose prior accounting reason says deprecated or disallowed have generated conformance `X` / `ConfDisallowed`, and the file does not set `ConfDeprecated` on them. The prior accounting headings that note read include no Descriptor, FixedLabel, UserLabel or Identify. a prior claim's mandatory UserLabel on HeatPump is the nested optional case in item 1 above.

EVSE lines 436–450: prior accounting `present` rows for CircuitCapacity, MaximumChargeCurrent and SessionEnergyCharged have target `unknown` / `matter.unmapped.v1`. The EnergyEvse device-type prior accounting row has an empty id cell. OnMode and StartUpMode reasons say deprecated or disallowed; generated op is `ConfDisallowed`, text `X`. `CurrentMode` names three `thermal.overrun.sg_ready_condition_*` ids that are in the catalog; the note does not place them in the feed cell. a prior claim's required Power Source, Device Energy Management and Electrical Sensor match `schema.json` and are absent from `go-fabric@v0.22.2:device/energy_evse_gen.go` `Servers`. Fed-not-published claims are unchecked because a driver feed is not in the sources.

[storage-pv-power note](storage-pv-power.md): the prior accounting has no PowerSourceConfiguration. The SolarPower device-type stub's SemReg id `pv.energy.consumed` is absent; the stub has no BatteryStorage or PowerSource device-type row. BatCapacity's prior accounting ids are absent; `storage.capacity.charge` and `storage.capacity.discharge` are present and unnamed there, and this index grades them candidate because they are cumulative lifetime counters rather than a fixed capacity. `a prior accounting` calls BatTimeRemaining and BatTimeToFullCharge seconds and BatCapacity mAh; both generated types are uint32 with no unit. Symbol literals it names are not in the catalog element or the pack-metadata field. a prior claim matches the schema effective requirements and does not match `go-fabric@v0.22.2:device/battery_storage_gen.go`, which declares only Identify `O`.

[thermostat note](thermostat.md): besides HeatPump (item 1), a prior claim omits Fan's mandatory Identify and Groups. a prior claim omits RoomAirConditioner's mandatory Identify. `AtomicResponse` conformance is empty in `definition_gen.go` and `O` in the id comment; the prior accounting says `M`. Deprecated thermostat and occupancy elements remain in the generated definitions. `thermal.event.occupancy_changed` is not in the catalog. `OutdoorTemperature` and `SetpointRaiseLower` are prior accounting `present` with target rows `unknown` / `matter.unmapped.v1`. MinSetpointDeadBand and HvacSystemTypeConfiguration access in the prior accounting is `R`; the generated `RW` string is `R[W]`.

[tariff note](tariff.md): `GetDetailedPriceRequest` and `GetDetailedForecastRequest` each have one field, `Details`, a bitmap. The prior accounting assigns price and description ids to those requests and to feature `FORE`. The value fields sit on the price structs. The device-type prior accounting row leaves the id cell empty; the device file states `0x0513` revision 1.

[water-hydraulics note](water-hydraulics.md): Pump `Speed` is prior accounting `present` and the target row is `unknown` / `matter.unmapped.v1`. Valve `CurrentLevel` and `BoostState` are `planned` and each name one id that is in the catalog and one id that is absent. `a prior accounting` states units (litres, percent, RPM, reciprocal second, hours, W, kWh) on attributes whose generated type has no unit token. It lists symbol values on `thermal.overrun.one_time_dhw`; the catalog symbol fact has no `values` list. a prior claim, a prior claim, a prior claim and a prior claim omit Identify, and a prior claim omits PumpController's servers. a prior claim's `thermal.mode.*.off` ids are not in the catalog.

## The first complete endpoint

QQ10 and XX03 ask for a first complete Matter endpoint, in XX03's words not one optional attribute. This section states, per device type, what the catalog lacks for every mandatory element on the notes' own lists. It does not choose a device type. Schema composition that a note left unsettled stays unsettled. Unexpanded clusters stay `not in the sources`.

No device type below has every mandatory element of every required cluster filled from the catalog, on the union of the device-file requirements and the clusters a note actually expanded. ElectricalSensor is the one whose only device-file `Mandatory: true` cluster, PowerTopology, has no conformance-`M` element ([electrical note](electrical.md)). The same note's `O.a+` measurement clusters, when mounted, lack the Accuracy and PowerMode elements in the gap table, and Descriptor's empty schema conformance is unresolved. That is not a completed endpoint in these sources.

| Device type | What the catalog lacks |
| --- | --- |
| AirQualitySensor | AirQuality attribute, FeatureMap, ClusterRevision ([air-quality note](air-quality.md)). Identify's `M` elements ([bridge-identity note](bridge-identity.md)). |
| AirPurifier | Identify's `M` elements. FanControl `FanMode`, `FanModeSequence`, `PercentCurrent` ([thermostat note](thermostat.md)). `PercentSetting` has a partial fact and does not by itself fill the cluster. |
| Aggregator | Descriptor `M` elements and six globals ([bridge-identity note](bridge-identity.md)). No other device-file mandatory cluster. |
| BridgedNode | BridgedDeviceBasicInformation gaps ([bridge-identity note](bridge-identity.md)) and the Descriptor gaps. |
| RootNode | BasicInformation gaps ([bridge-identity note](bridge-identity.md)) and the Descriptor gaps. Six further `M` servers are not expanded ([bridge-identity note](bridge-identity.md)). |
| TemperatureSensor | MinMeasuredValue, MaxMeasuredValue, ClusterRevision ([sensing note](sensing.md)). MeasuredValue is partial, not exact ([sensing note](sensing.md)). Identify's `M` elements. |
| PressureSensor | MinMeasuredValue, MaxMeasuredValue, FeatureMap, ClusterRevision ([sensing note](sensing.md)). MeasuredValue partial. Identify's `M` elements. |
| FlowSensor | MinMeasuredValue, MaxMeasuredValue, ClusterRevision ([sensing note](sensing.md)). MeasuredValue partial. Identify's `M` elements. |
| HumiditySensor | MinMeasuredValue, MaxMeasuredValue, ClusterRevision ([sensing note](sensing.md)). MeasuredValue partial. Identify's `M` elements. |
| ElectricalSensor | Device-file PowerTopology: no conformance-`M` element ([electrical note](electrical.md)). When a measurement cluster is mounted: the ElectricalPowerMeasurement and ElectricalEnergyMeasurement gap rows ([electrical note](electrical.md)). |
| ElectricalMeter | Those same measurement gap rows ([electrical note](electrical.md)). ActivePower has partial facts and does not fill ElectricalPowerMeasurement. Schema ElectricalSensor `M` and ElectricalEnergyTariff base are not settled as mounted servers ([electrical note](electrical.md)). |
| ElectricalUtilityMeter | MeterType, PointOfDelivery, MeterSerialNumber ([electrical note](electrical.md)). Schema Identify `M` is on the schema list and omitted from the device file ([electrical note](electrical.md)); Identify's `M` elements have no catalog source. |
| MeterReferencePoint | Identify's `M` elements only, inside the device file ([electrical note](electrical.md); [bridge-identity note](bridge-identity.md)). |
| EnergyEvse | The EnergyEvse and EnergyEvseMode gap rows ([evse-dem note](evse-dem.md)). Elements that have only a candidate or a partial fact do not fill those attributes. Schema PowerSource, DeviceEnergyManagement and ElectricalSensor `M` are not in the device file ([evse-dem note](evse-dem.md)). |
| DeviceEnergyManagement | EsaType, EsaCanGenerate, EsaState, AbsMinPower, AbsMaxPower ([evse-dem note](evse-dem.md)). |
| PowerSource | Order, Description, EndpointList ([storage-pv-power note](storage-pv-power.md)). Status is candidate only. |
| SolarPower | Device file: no mandatory server ([storage-pv-power note](storage-pv-power.md)). Schema composed PowerSource: Order, Description, EndpointList, feature WIRED. Schema ElectricalSensor `M` is outside that note's cluster tables. |
| BatteryStorage | Device file: Identify `O` only ([storage-pv-power note](storage-pv-power.md)). Schema composed PowerSource adds BatTimeRemaining, BatTimeToFullCharge, ActiveBatChargeFaults, features WIRED and BAT, plus Order, Description, EndpointList. Partial facts on BatVoltage, BatPercentRemaining and BatChargingCurrent do not remove those gaps. BatCapacity stays on the gap list: `storage.capacity.charge` and `storage.capacity.discharge` are candidate lifetime counters and do not fill the Fixed attribute. |
| Thermostat | ControlSequenceOfOperation and both SetpointRaiseLower fields ([thermostat note](thermostat.md)). LocalTemperature, SystemMode and the command have partial facts. Identify's `M` elements. |
| HeatPump | Device file and `go-fabric@v0.22.2:docs/reference/device-types.md`: no mandatory cluster ([thermostat note](thermostat.md); go-fabric `go-fabric@v0.22.2:device/heat_pump_gen.go` lines 29–39). Schema device-type requirements PowerSource `M`, DeviceEnergyManagement `M` and ElectricalSensor `M` are in go-fabric `go-fabric@v0.22.2:device/devicetype_requirements_gen.go` lines 2042, 2082 and 2094. This note does not treat that schema list as the device-file list. |
| RoomAirConditioner | Thermostat gaps ([thermostat note](thermostat.md)), Identify's `M` elements, and OnOff elements with no catalog source in the water note ([water-hydraulics note](water-hydraulics.md)). Feature `DF` on OnOff is not expanded. |
| Fan | FanMode, FanModeSequence, PercentCurrent ([thermostat note](thermostat.md)). PercentSetting is partial. Identify's `M` elements. Groups is `M` and not expanded. |
| ThermostatController | Binding is `M` and not expanded ([thermostat note](thermostat.md)). The mandatory Thermostat client is not scored by that note. |
| ElectricalEnergyTariff | Descriptor is the only `Mandatory: true` cluster ([tariff note](tariff.md)) and its `M` elements have no catalog source ([bridge-identity note](bridge-identity.md)). CommodityPrice and CommodityTariff are not device-file mandatory. |
| WaterHeater | WaterHeaterManagement and WaterHeaterMode gap rows ([water-hydraulics note](water-hydraulics.md)). BoostState is a candidate and stays short of exact. Thermostat with feature `HEAT` is required and not expanded in that note. |
| Pump | PumpConfigurationAndControl's seven `M` attributes ([water-hydraulics note](water-hydraulics.md)), OnOff's four rows, Identify's `M` elements. |
| PumpController | The same OnOff and PumpConfigurationAndControl gaps, as clients ([water-hydraulics note](water-hydraulics.md)). Identify's `M` elements. Binding is `M` and not expanded. |
| WaterValve | Seven ValveConfigurationAndControl rows ([water-hydraulics note](water-hydraulics.md)) and Identify's `M` elements. |
| WaterFreezeDetector | BooleanState rows ([water-hydraulics note](water-hydraulics.md)) and Identify's `M` elements. |
| WaterLeakDetector | The same BooleanState rows and Identify's `M` elements ([water-hydraulics note](water-hydraulics.md)). |

## Open counting questions

None of these is answered here.

1. Groups `0x0004` and Binding `0x001E` are required servers on device types in these notes (Fan; PumpController; ThermostatController), and no note accounts their elements. One reading: those clusters, and RootNode's further required servers AccessControl, GeneralCommissioning, GeneralDiagnostics, AdministratorCommissioning, OperationalCredentials and GroupKeyManagement, stay `not in the sources` until a later accounting. The other reading: a device type is not closed while a required server is unexpanded. Files: `go-fabric@v0.22.2:device/fan_gen.go`, `go-fabric@v0.22.2:device/pump_controller_gen.go`, `go-fabric@v0.22.2:device/thermostat_controller_gen.go`, `go-fabric@v0.22.2:device/root_node_gen.go`.

2. A schema device-type requirement with conformance `M` may or may not count when the device file omits it. One reading: the device file's `Servers` list is the requirement. The other reading: `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` is the requirement. Both lists exist for HeatPump (`go-fabric@v0.22.2:device/heat_pump_gen.go` lines 29–39 against `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 2042, 2082 and 2094). The [electrical note](electrical.md), the [evse-dem note](evse-dem.md) and the [storage-pv-power note](storage-pv-power.md) record the same split for ElectricalMeter, EnergyEvse, SolarPower and BatteryStorage.

3. A mandatory client cluster's elements may or may not count as server elements. One reading, in the [water-hydraulics note](water-hydraulics.md): PumpController's mandatory clients are scored with the cluster element's conformance. The other reading, in the [sensing note](sensing.md): client requirements are not server mandates. The [thermostat note](thermostat.md) does not score ThermostatController's mandatory Thermostat client as server elements. Files: the device files those notes cite.

4. `FeatureMap`, `ClusterRevision` and the other four global attribute ids may or may not count as mandatory elements. One reading: schema effective conformance `M` includes `FeatureMap` and `ClusterRevision` (the [air-quality note](air-quality.md) and the [sensing note](sensing.md)). Another reading: six global attributes count because `go-fabric@v0.22.2:cluster/spec/instance.go` lines 15–22 name ids every server answers (the [bridge-identity note](bridge-identity.md)). A third reading: those ids stay out of cluster element rows (the [electrical note](electrical.md), the [thermostat note](thermostat.md) and the [storage-pv-power note](storage-pv-power.md)). All three match a go-fabric text.

5. Base Descriptor conformance `M` may apply to every device type, or an empty conformance on a per-device Descriptor row may stay optional. One reading: `go-fabric@v0.22.2:schema/devicetype_requirements.go` lines 190–193, used by the [bridge-identity note](bridge-identity.md) for Aggregator, Bridged Node and Root Node. The other reading: `go-fabric@v0.22.2:cluster/spec/conformance.go` lines 208–209 map an empty op to optional, which is how the other notes treat an empty schema row. ElectricalEnergyTariff is the exception those notes record: its device file sets `Mandatory: true` on Descriptor (`go-fabric@v0.22.2:device/electrical_energy_tariff_gen.go`).
