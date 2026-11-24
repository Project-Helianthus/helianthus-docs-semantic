---
status: "research notes for Matter 1.6.1 electrical measurement clusters; no mapping is decided and no canonical target is written."
---

# Electrical measurement

Matter 1.6.1 cluster accounting for Electrical measurement. Identifiers, conformance, types and units are read from go-fabric@v0.22.2:parity/schema.json (revision 1.6.1, data model revision 21) and the generated cluster and device files cited below. Catalog elements are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json and semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json. Canonical units are the `canonical_unit` field of docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json. Target rows are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json and docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md. No mapping is chosen. No grade in this note is `exact`. Charge capacity stays `unit.ampere_hour` where the catalog defines it; `storage.capacity.remaining` and `storage.capacity.full_charge` are absent from the pinned catalog. A catalog canonical unit is written beside the Matter unit on each element row that names a catalog field.

Read-only source accounting for the electrical measurement and metering cluster group. No mapping is decided here.

## 1. Header

- Queue row QQ04: `TARGET-MAT-R` read-only source accounting by cluster; no canonical JSON writer here (the research row).
- docs-semantic frozen SHA: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`. `git rev-parse HEAD` in the pinned files returned that SHA, so line numbers below are that commit.
- semreg frozen SHA: `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:`. `git rev-parse HEAD` in the pinned files returned that SHA. `git grep` of `fixtures/v1/element-catalog-v1.json` at that SHA finds `evse.ac.current` and `identification_schemes` at line 197 with value `[]`. A byte-for-byte diff of that fixture against the docs-semantic catalog was not done.
- go-fabric: module path `go-fabric`, directory `v0.22.2` (`go-fabric v0.22.2`). `go.mod` does not state the tag. `go-fabric@v0.22.2:parity/schema.json` key `matter` (lines 2–7): `revision` `1.6.1`, `specificationVersion` `17170688`, `interactionModelRevision` `12`, `dataModelRevision` `21`, `sourceCommit` `a commit id recorded in the cited file`. Each cluster package comment says the file was generated from the matter.js model at `a commit id recorded in the cited file` (Matter 1.6.1).
- The Matter 1.6.1 target pins a different module tag. `api/v1/targets/matter-1.6.1-v1.json` `model_source` (lines 11295–11323): repository `go-fabric`, tag `v0.13.12`, `inspection_grade` `Proven`, `execution_grade` `Unknown`, `standards_equivalence` `Unknown`. Adopted models: Electrical Sensor `device_type_id` 1296 revision 1; Power Topology `cluster_id` 156 revision 1; Electrical Power Measurement `cluster_id` 144 revision 3 `attribute_id` 5 `ActiveCurrent`. Those three identities match the v0.22.2 files cited in section 2 and in the ElectricalPowerMeasurement cluster. A full diff of tag `v0.13.12` against `v0.22.2` was not done.
- Target contract (`matter-1.6.1-v1.json` lines 1–27): `helianthus.gateway.matter-projection/v1`, status `adoption_projection_contract_pre_1_0`, `mapping_revision` 1, target `matter.data-model` version `1.6.1`. Pack pins: evse, infrastructure, pv, thermal `1.0.0`; storage `1.1.0`. 246 rows. Disposition counts from that JSON: 139 facts + 37 capabilities + 7 operations `unknown` / `matter.unmapped.v1` (183); 36 services `unsupported` / `matter.service_not_requested_item.v1`; 21 relations `unknown` / `matter.relation_construct_not_adopted.v1`; 5 relations `withheld` / `matter.power_topology_endpoint_unallocated.v1`; 1 fact `transformed` / `matter.phase_association_by_relation.v1` (`evse.ac.current`). The markdown (line 98) says the other 126 facts/capabilities/operations remain unknown. That 126 matches the pack roster arithmetic in the same markdown (lines 44–46): 88 facts minus the one transformed fact, plus 32 capabilities, plus 7 operations. The JSON's 183 counts every unknown row, including rows outside that pack roster.

### Files read

- Plan: the registry unit rule, `the documentation rules`, `the documentation rules`, the research row (QQ04).
- Pinned files: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`, `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`.
- docs-semantic at the frozen SHA: `api/v1/targets/matter-1.6.1-v1.json`, `api/v1/targets/matter-1.6.1-v1.md`, `api/v1/element-catalog-v1.json` (identification schemes and the absence of a unit key), `api/v1/pack-metadata-v1.json` (canonical units; see the open questions 1).
- semreg at the frozen SHA: `fixtures/v1/element-catalog-v1.json` (`evse.ac.current`, `identification_schemes`).
- go-fabric v0.22.2: `go-fabric@v0.22.2:parity/schema.json` (header and device types 1296–1300); `go-fabric@v0.22.2:device/electrical_sensor_gen.go`, `go-fabric@v0.22.2:device/electrical_meter_gen.go`, `go-fabric@v0.22.2:device/electrical_utility_meter_gen.go`, `go-fabric@v0.22.2:device/meter_reference_point_gen.go`; `go-fabric@v0.22.2:device/type.go`, `go-fabric@v0.22.2:device/base.go`, `go-fabric@v0.22.2:device/device.go` (`composes`); `go-fabric@v0.22.2:cluster/spec/instance.go`; `go-fabric@v0.22.2:cluster/spec/electricalpowermeasurement/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/electricalenergymeasurement/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/powertopology/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/meteridentification/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/commoditymetering/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/electricalgridconditions/definition_gen.go`.
- Prior claims were checked only against a prior accounting (legend line 3; ElectricalPowerMeasurement 280–308; ElectricalEnergyMeasurement 310–327; PowerTopology 468–477; ElectricalGridConditions 515–523; MeterIdentification 1027–1036; CommodityMetering 1038–1045; device-type stub 1047–1064); `audits/semreg-loss-20261118/a prior accounting` (lines 1–27, a prior claim, a prior claim).

### How to read the tables

Catalog element records have no unit field (`element-catalog-v1.json` has no `canonical_unit` key). Units below are `pack-metadata-v1.json` `fields[].canonical_unit.id` for that field ref. `identification_schemes` is `[]` (catalog line 197; semreg fixture line 197).

Global attributes are not cluster elements. `go-fabric@v0.22.2:cluster/spec/instance.go` lines 16–22 name ids every server answers: `AttrGeneratedCommandList` `0xFFF8`, `AttrAcceptedCommandList` `0xFFF9`, `AttrEventList` `0xFFFA`, `AttrAttributeList` `0xFFFB`, `AttrFeatureMap` `0xFFFC`, `AttrClusterRevision` `0xFFFD`. None of the six `definition_gen.go` files lists them. They are not rows below.

Grades: `exact` would require the same meaning, kind, and unit with loss `none`. No row in this group is `exact`. `partial` means the catalog fact is the same quantity family and the losses are named. `candidate` means the quantity is related and a loss keeps it from `partial` (RMS not declared, lifetime versus import, session versus a period, charge versus grid import, generation versus export). An ambiguous match is left out of the feed cell and listed in section 5.

Mandatory column:

- `EM`: the ElectricalMeter device file sets that cluster `Mandatory: true`, and this element's conformance text is `M`.
- `EU`: the same rule for ElectricalUtilityMeter.
- `ES-if`: ElectricalSensor lists the cluster as `O.a+` with `Mandatory` unset; the element text is `M`, so it is mandatory only when that cluster is mounted.
- `—`: not mandatory for a device type of this group under that rule.
- CommodityMetering on ElectricalMeter is the string `P, M` with `Mandatory` unset. Its `M` attributes are not marked `EM`.

`source status` is `defined` when a catalog element is named, and `no source` when none is. Whether a driver constructs the fact is not visible from these sources.

Commands: each cluster's `Definition` literal has no `Commands` field. One row records that.

Enum values are listed in the type cell. Every enum value cited here has conformance text `M` in its `EnumValue`.

## 2. Device types

The device file `Servers` slice is what the generated file declares (`go-fabric@v0.22.2:device/type.go` lines 39–41). `schema.json` `deviceTypes[].requirements` is a second list. They are not the same set. `go-fabric@v0.22.2:device/base.go` lines 18–66 append only the Matter Base device type's plain optional servers whose conformance text is `O` (FixedLabel `0x0040`, UserLabel `0x0041`) when a declaration names them. `go-fabric@v0.22.2:device/device.go` `composes` (lines 658–679) walks `Type.Base` only to test schema `deviceType` requirements. It does not copy a parent type's `Servers` onto the child. Whether a constructed ElectricalMeter therefore mounts ElectricalEnergyTariff's servers is not established beyond those lines.

### ElectricalSensor

- File: `go-fabric@v0.22.2:device/electrical_sensor_gen.go`.
- Id `0x0510` (1296), revision 1, classification `utility`, composition `schema.CompositionTree` (lines 16–18, 28–30). No `Base`. No `Conditions`.
- Servers the file declares (lines 31–44):
  - PowerTopology `0x009C`, conformance `M`, `Mandatory: true`.
  - ElectricalPowerMeasurement `0x0090`, conformance `O.a+`, `Mandatory` unset.
  - ElectricalEnergyMeasurement `0x0091`, conformance `O.a+`, `Mandatory` unset.
- `schema.json` device type id 1296, name `ElectricalSensor`, classification `utility`, revision 1 (lines 18989–19016). Requirements: Descriptor id 29, `serverCluster`, no `conformance` key; ElectricalPowerMeasurement id 144, `O.a+`; ElectricalEnergyMeasurement id 145, `O.a+`; PowerTopology id 156, `M`. `effective.conditions` is empty (line 19020). The file's `Servers` omit Descriptor.

### ElectricalMeter

- File: `go-fabric@v0.22.2:device/electrical_meter_gen.go`.
- Id `0x0514` (1300), revision 1, classification `simple`, composition tree, `Base` `ElectricalEnergyTariff` (lines 16–18, 28–31).
- Servers the file declares (lines 32–46):
  - ElectricalPowerMeasurement `0x0090`, conformance `M`, `Mandatory: true`.
  - ElectricalEnergyMeasurement `0x0091`, conformance `M`, `Mandatory: true`.
  - CommodityMetering `0x0B07`, conformance `P, M`, `Mandatory` unset. The accessor comment says the server is nil until a declaration mounts it (lines 75–77).
- `schema.json` device type id 1300 (lines 19546–19597): `base` in `effective` is `ElectricalEnergyTariff` (line 19601). Requirements: Descriptor 29, no conformance key; ElectricalPowerMeasurement 144 `M`; ElectricalEnergyMeasurement 145 `M`; CommodityPrice 149 `[ActiveTariff].a+`; ElectricalGridConditions 160 `O`; deviceType ElectricalSensor 1296 `M`; CommodityTariff 1792 `O.a+`; CommodityMetering 2823 `P, M`. The file's `Servers` omit Descriptor, CommodityPrice, ElectricalGridConditions, CommodityTariff, and the ElectricalSensor device type.

### ElectricalUtilityMeter

- File: `go-fabric@v0.22.2:device/electrical_utility_meter_gen.go`.
- Id `0x0511` (1297), revision 1, classification `simple`, composition tree, `Base` `MeterReferencePoint` (lines 14–16, 26–29).
- Servers the file declares (lines 30–35): MeterIdentification `0x0B06`, conformance `M`, `Mandatory: true`.
- `schema.json` device type id 1297 (lines 19112–19145): requirements Identify 3 `M`; Descriptor 29, no conformance key; deviceType ElectricalEnergyTariff 1299 `[ElectricalEnergy].a+`; deviceType ElectricalMeter 1300 `[ElectricalEnergy].a+`; serverCluster MeterIdentification 2822 `M`. `effective.base` is `MeterReferencePoint` (line 19149). The file's `Servers` omit Identify, Descriptor, and both device types.

### MeterReferencePoint

- File: `go-fabric@v0.22.2:device/meter_reference_point_gen.go`.
- Id `0x0512` (1298), revision 1, classification `simple`, composition tree, `Conditions` `ElectricalEnergy` (lines 14–16, 26–29). No `Base`.
- Servers the file declares (lines 30–35): Identify `0x0003`, conformance `M`, `Mandatory: true`. Identify is outside this cluster group.
- `schema.json` device type id 1298 (lines 19212–19245): requirements Identify 3 `M`; Descriptor 29, no conformance key; deviceType ElectricalEnergyTariff 1299 `[ElectricalEnergy].a+`; deviceType ElectricalMeter 1300 `[ElectricalEnergy].a+`. `effective.conditions` includes `ElectricalEnergy` (lines 19243–19245). The file's `Servers` omit Descriptor and both device types.

ElectricalGridConditions `0x00A0` is on none of these four `Servers` slices. `schema.json` lists it as `serverCluster` conformance `O` on ElectricalMeter (lines 19574–19578) and on ElectricalEnergyTariff id 1299 (lines 19419–19423). ElectricalEnergyTariff is not a device type of this group; it is the `Base` name on ElectricalMeter.

## 3. Clusters

Locator prefix for a cluster is its `definition_gen.go` unless a cell names another file. Catalog lines are `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`. Target lines are `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json` unless the cell cites the JSON.

### ElectricalPowerMeasurement

Cluster id `0x0090` (144), name `ElectricalPowerMeasurement`, revision 3 (lines 22–26). No `Commands` field. Attribute and event access in `Definition` is Read / View. Feature bits are the cluster FeatureMap bits, separate from global `AttrFeatureMap` `0xFFFC`.

MeasurementTypeEnum (enum16, lines 172–212), every value conformance `M`: `Unspecified` 0, `Voltage` 1, `ActiveCurrent` 2, `ReactiveCurrent` 3, `ApparentCurrent` 4, `ActivePower` 5, `ReactivePower` 6, `ApparentPower` 7, `RmsVoltage` 8, `RmsCurrent` 9, `RmsPower` 10, `Frequency` 11, `PowerFactor` 12, `NeutralCurrent` 13, `ElectricalEnergy` 14, `ReactiveEnergy` 15, `ApparentEnergy` 16.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PowerMode | attribute | 0x0000 | PowerModeEnum enum8: Unknown 0, Dc 1, Ac 2, each M | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog element; ac/dc fact prefixes are not a declared PowerMode value | lines 393–397; enum lines 221–233 |
| NumberOfMeasurementTypes | attribute | 0x0001 | uint8; Fixed; constraint `max 32` | M | EM, ES-if | none in catalog ( `infrastructure.accuracy.measured`, `pv.accuracy.measured`) | absent | no row | no source | no catalog count of measurement types | lines 399–405 |
| Accuracy | attribute | 0x0002 | list of MeasurementAccuracyStruct; Fixed; constraint `1 to numberOfMeasurementTypes`; decoder list bound 1..2147483647 | M | EM, ES-if | none in catalog ( `infrastructure.accuracy.*`, `pv.accuracy.*`, `*.dimension.measurement_type`) | absent | no row | no source | no accuracy element; list length is tied to NumberOfMeasurementTypes; decoder max is not the constraint ref | lines 407–414; decode lines 355–357 |
| Accuracy.MeasurementType | field | 0 | MeasurementTypeEnum (values above) | M | EM, ES-if | none in catalog | absent | no row | no source | enum has no catalog element | struct lines 270–271 |
| Accuracy.Measured | field | 1 | bool | M | EM, ES-if | none in catalog | absent | no row | no source | none of the cited accuracy ids exist | line 272 |
| Accuracy.MinMeasuredValue | field | 2 | int64; constraint `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | range is on the field; no catalog range | line 273 |
| Accuracy.MaxMeasuredValue | field | 3 | int64; constraint `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | same as MinMeasuredValue | line 274 |
| Accuracy.AccuracyRanges | field | 4 | list of MeasurementAccuracyRangeStruct; constraint `min 1`; decoder 1..2147483647 | M | EM, ES-if | none in catalog | absent | no row | no source | nested range has no catalog element | line 275; decode line 263 |
| AccuracyRanges.RangeMin | field | 0 | int64; `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog range | line 322 |
| AccuracyRanges.RangeMax | field | 1 | int64; `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog range | line 323 |
| AccuracyRanges.PercentMax | field | 2 | percent100ths uint16; constraint `max 10000`; decoder accepts 0..10000 | O.a+ (Choice name `a`, Num 1, OrMore true, OrLess false) | — | none in catalog | absent | no row | no source | constraint text has no minimum; decoder minimum is 0 | lines 324 and 309 |
| AccuracyRanges.PercentMin | field | 3 | percent100ths; constraint `max percentTypical`; decoder 0..10000 | `[PercentMax]` | — | none in catalog | absent | no row | no source | same decoder versus constraint gap | lines 325 and 310 |
| AccuracyRanges.PercentTypical | field | 4 | percent100ths; constraint `percentMin to percentMax`; decoder 0..10000 | `[PercentMin]` | — | none in catalog | absent | no row | no source | same decoder versus constraint gap | lines 326 and 311 |
| AccuracyRanges.FixedMax | field | 5 | uint64; constraint `max (2^62) - 1` | O.a+ (same Choice `a` as PercentMax) | — | none in catalog | absent | no row | no source | no catalog fixed-error element | line 327 |
| AccuracyRanges.FixedMin | field | 6 | uint64; constraint `max fixedMax` | `[FixedMax]` | — | none in catalog | absent | no row | no source | no catalog element | line 328 |
| AccuracyRanges.FixedTypical | field | 7 | uint64; constraint `fixedMin to fixedMax` | `[FixedMin]` | — | none in catalog | absent | no row | no source | no catalog element | line 329 |
| Ranges | attribute | 0x0003 | list of MeasurementRangeStruct; Quieter; EmptyListDefault; constraint `0 to numberOfMeasurementTypes` | O | — | none in catalog | absent | no row | no source | no retained-revision element in the catalog | lines 416–424 |
| Ranges.MeasurementType | field | 0 | MeasurementTypeEnum | M | — | none in catalog | absent | no row | no source | M only inside the struct | line 153 |
| Ranges.Min | field | 1 | int64; `-2^62 to 2^62` | M | — | none in catalog | absent | no row | no source | no catalog period range | line 154 |
| Ranges.Max | field | 2 | int64; `-2^62 to 2^62` | M | — | none in catalog | absent | no row | no source | no catalog period range | line 155 |
| Ranges.StartTimestamp | field | 3 | epoch-s uint32 | `EndTimestamp` | — | none in catalog | absent | no row | no source | no catalog period bound | line 156 |
| Ranges.EndTimestamp | field | 4 | epoch-s; conformance text `desc`; constraint `min startTimestamp + 1` | `desc` | — | none in catalog | absent | no row | no source | no catalog period bound | line 157 |
| Ranges.MinTimestamp | field | 5 | epoch-s | `EndTimestamp` | — | none in catalog | absent | no row | no source | no catalog period bound | line 158 |
| Ranges.MaxTimestamp | field | 6 | epoch-s; constraint `min minTimestamp + 1` | `EndTimestamp` | — | none in catalog | absent | no row | no source | no catalog period bound | line 159 |
| Ranges.StartSystime | field | 7 | systime-ms uint64 | `EndSystime` | — | none in catalog | absent | no row | no source | no catalog systime | line 160 |
| Ranges.EndSystime | field | 8 | systime-ms; conformance text `desc`; constraint `min startSystime + 1` | `desc` | — | none in catalog | absent | no row | no source | no catalog systime | line 161 |
| Ranges.MinSystime | field | 9 | systime-ms | `EndSystime` | — | none in catalog | absent | no row | no source | no catalog systime | line 162 |
| Ranges.MaxSystime | field | 10 | systime-ms; constraint `min minSystime + 1` | `EndSystime` | — | none in catalog | absent | no row | no source | no catalog systime | line 163 |
| Voltage | attribute | 0x0004 | voltage-mV int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62`; catalog canonical unit `evse.ac.voltage` `unit.volt`, `infrastructure.ac.voltage` `unit.volt`, `pv.ac.voltage` `unit.volt`, `pv.ac.aggregate_voltage` `unit.volt`, `pv.dc.voltage` `unit.volt`, `pv.dc.aggregate_voltage` `unit.volt`, `storage.pack.voltage` `unit.volt` | O | — | `evse.ac.voltage` partial; `infrastructure.ac.voltage` partial; `pv.ac.voltage` partial; `pv.ac.aggregate_voltage` partial; `pv.dc.voltage` partial; `pv.dc.aggregate_voltage` partial; `storage.pack.voltage` partial | present | unknown / `matter.unmapped.v1` for each (target lines 6, 42, 88, 82, 103, 99, 148) | defined | unit.volt versus voltage-mV and no conversion row; one cluster value versus phase member, inverter aggregate, dc_input, or battery_pack; nullable and range versus no numeric range on the catalog element; pack-metadata does not say RMS, so these are not RmsVoltage feeds | lines 426–433; catalog lines 71, 120, 180, 174, 195, 191, 265; units `unit.volt` |
| ActiveCurrent | attribute | 0x0005 | amperage-mA int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62`; catalog canonical unit `evse.ac.current` `unit.ampere`, `infrastructure.ac.current` `unit.ampere`, `pv.ac.current` `unit.ampere`, `pv.ac.aggregate_current` `unit.ampere`, `pv.dc.current` `unit.ampere`, `pv.dc.aggregate_current` `unit.ampere`, `storage.pack.current` `unit.ampere` | O | — | `evse.ac.current` partial; `infrastructure.ac.current` partial; `pv.ac.current` partial; `pv.ac.aggregate_current` partial; `pv.dc.current` partial; `pv.dc.aggregate_current` partial; `storage.pack.current` partial | present | `evse.ac.current` transformed / `matter.phase_association_by_relation.v1` (JSON lines 109–159; target line 4). The other six unknown / `matter.unmapped.v1` (target lines 38, 84, 80, 100, 97, 146) | defined | `evse.ac.current`: exact_multiply factor 1000 from `unit.ampere` to `amperage-mA`, `require_integral_result` true, loss kind `unit`, `reversible` false; representation signed_integer minimum -4611686018427387904 maximum 4611686018427387904 nullable true; emission `value_must_be_non_null` true, `eligible_source_keys` 1, `required_dimension` `evse.dimension.phase`, `on_nonrepresentable` `whole_document_no_payload`. Relations member cites `evse.relation.connector_phase`, whose own row is unknown / `matter.relation_construct_not_adopted.v1` (target line 22). Other currents: `unit.ampere` versus amperage-mA with no conversion row; phase, inverter aggregate, dc_input, or battery_pack versus one value; `non_negative` except `storage.pack.current` which is `signed`; nullable and range | lines 435–442; catalog lines 69, 116, 176, 172, 192, 189, 263 |
| ReactiveCurrent | attribute | 0x0006 | amperage-mA int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62` | `[ALTC]` | — | none in catalog ( `infrastructure.ac.reactive_current`) | absent | no row | no source | no reactive-current element | lines 444–451 |
| ApparentCurrent | attribute | 0x0007 | amperage-mA int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62` | `[ALTC]` | — | none in catalog ( `infrastructure.ac.apparent_current`) | absent | no row | no source | no apparent-current element | lines 453–460 |
| ActivePower | attribute | 0x0008 | power-mW int64; Nullable; Quieter; no Default key; `-2^62 to 2^62`; catalog canonical unit `evse.ac.active_power` `unit.watt`, `infrastructure.ac.active_power` `unit.watt`, `pv.ac.active_power` `unit.watt`, `pv.ac.aggregate_active_power` `unit.watt`, `pv.dc.aggregate_power` `unit.watt`, `pv.dc.power` `unit.watt`, `storage.pack.power` `unit.watt`, `infrastructure.power.pcc` `unit.watt`, `infrastructure.power.import_active` `unit.watt`, `infrastructure.power.export_active` `unit.watt` | M | EM, ES-if | `evse.ac.active_power` partial; `infrastructure.ac.active_power` partial; `pv.ac.active_power` partial; `pv.ac.aggregate_active_power` partial; `pv.dc.aggregate_power` partial; `pv.dc.power` partial; `storage.pack.power` partial; `infrastructure.power.pcc` partial; `infrastructure.power.import_active` partial; `infrastructure.power.export_active` partial | present | unknown / `matter.unmapped.v1` for each (target lines 3, 36, 77, 78, 98, 102, 147, 59, 57, 55) | defined | `unit.watt` versus power-mW, no conversion row; signed phase or pack or pcc versus one nullable cluster value; aggregates are `aggregate`; `pv.dc.power` and the import/export pair are `non_negative` (sign split on the directional pair); subjects are phase, inverter, dc_input, battery_pack, or grid_connection; nullable and range. Absent names, not feeds: `evse.ac.total_active_power` (a prior proposal/a prior proposal), `thermal.measurement.electrical_power` (a prior proposal) | lines 462–468; catalog lines 68, 114, 169, 170, 190, 194, 264, 151, 149, 147; units `unit.watt` |
| ReactivePower | attribute | 0x0009 | power-mVAR int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62`; catalog canonical unit `infrastructure.ac.reactive_power` `unit.volt_ampere_reactive`, `pv.ac.reactive_power` `unit.volt_ampere_reactive`, `pv.ac.aggregate_reactive_power` `unit.volt_ampere_reactive`, `infrastructure.power.import_reactive` `unit.volt_ampere_reactive`, `infrastructure.power.export_reactive` `unit.volt_ampere_reactive` | `[ALTC]` | — | `infrastructure.ac.reactive_power` partial; `pv.ac.reactive_power` partial; `pv.ac.aggregate_reactive_power` partial; `infrastructure.power.import_reactive` partial; `infrastructure.power.export_reactive` partial | present | unknown / `matter.unmapped.v1` (target lines 41, 87, 81, 58, 56) | defined | `unit.volt_ampere_reactive` versus power-mVAR, no conversion row; phase member or inverter aggregate or grid_connection; import/export are `non_negative` splits of a signed attribute; nullable and range | lines 470–477; catalog lines 119, 179, 173, 150, 148 |
| ApparentPower | attribute | 0x000A | power-mVA int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62`; catalog canonical unit `infrastructure.ac.apparent_power` `unit.volt_ampere`, `pv.ac.apparent_power` `unit.volt_ampere`, `pv.ac.aggregate_apparent_power` `unit.volt_ampere`, `infrastructure.power.apparent` `unit.volt_ampere` | `[ALTC]` | — | `infrastructure.ac.apparent_power` partial; `pv.ac.apparent_power` partial; `pv.ac.aggregate_apparent_power` partial; `infrastructure.power.apparent` partial | present | unknown / `matter.unmapped.v1` (target lines 37, 83, 79, 54) | defined | `unit.volt_ampere` versus power-mVA, no conversion row; catalog direction `non_negative` versus a signed nullable attribute; phase, inverter aggregate, or grid_connection; range | lines 479–486; catalog lines 115, 175, 171, 146 |
| RmsVoltage | attribute | 0x000B | voltage-mV int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62`; catalog canonical unit `evse.ac.voltage` `unit.volt`, `infrastructure.ac.voltage` `unit.volt`, `pv.ac.voltage` `unit.volt`, `pv.ac.aggregate_voltage` `unit.volt` | `[ALTC]` | — | `evse.ac.voltage` candidate; `infrastructure.ac.voltage` candidate; `pv.ac.voltage` candidate; `pv.ac.aggregate_voltage` candidate | present | unknown / `matter.unmapped.v1` (target lines 6, 42, 88, 82) | defined | catalog and pack-metadata do not declare RMS; same unit, subject, null, and range losses as Voltage; DC voltage facts are not listed here | lines 488–495 |
| RmsCurrent | attribute | 0x000C | amperage-mA int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62`; catalog canonical unit `evse.ac.current` `unit.ampere`, `infrastructure.ac.current` `unit.ampere`, `pv.ac.current` `unit.ampere`, `pv.ac.aggregate_current` `unit.ampere` | `[ALTC]` | — | `evse.ac.current` candidate; `infrastructure.ac.current` candidate; `pv.ac.current` candidate; `pv.ac.aggregate_current` candidate | present | `evse.ac.current` transformed onto ActiveCurrent, not onto this attribute (JSON lines 135–138 name attribute_id 5). The other three unknown / `matter.unmapped.v1` | defined | RMS not declared; the one conversion row targets ActiveCurrent | lines 497–504 |
| RmsPower | attribute | 0x000D | power-mW int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62`; catalog canonical unit `evse.ac.active_power` `unit.watt`, `infrastructure.ac.active_power` `unit.watt`, `pv.ac.active_power` `unit.watt`, `pv.ac.aggregate_active_power` `unit.watt` | `[ALTC]` | — | `evse.ac.active_power` candidate; `infrastructure.ac.active_power` candidate; `pv.ac.active_power` candidate; `pv.ac.aggregate_active_power` candidate | present | unknown / `matter.unmapped.v1` (target lines 3, 36, 77, 78) | defined | RMS not declared; unit.watt versus power-mW; subject and sign losses as ActivePower | lines 506–513 |
| Frequency | attribute | 0x000E | int64 (type name has no unit); Nullable; Quieter; NullDefault; constraint `0 to 1000000`; catalog canonical unit `evse.ac.frequency` `unit.hertz`, `infrastructure.ac.frequency` `unit.hertz`, `pv.ac.frequency` `unit.hertz` | `[ALTC]` | — | `evse.ac.frequency` partial; `infrastructure.ac.frequency` partial; `pv.ac.frequency` partial | present | unknown / `matter.unmapped.v1` (target lines 5, 39, 85) | defined | `unit.hertz` versus an unnamed int64; no scale in the type name or the target; range; nullable; subjects are evse, grid_connection, and inverter | lines 515–522; catalog lines 70, 117, 177; units `unit.hertz` |
| HarmonicCurrents | attribute | 0x000F | list of HarmonicMeasurementStruct; Nullable; Quieter; constraint `max 25`; decoder 0..25, null TLV returns nil | `HARM` | — | none in catalog ( `infrastructure.ac.harmonic_current`, `infrastructure.dimension.harmonic_order`) | absent | no row | no source | no harmonic element | lines 524–531; decode lines 365–370 |
| HarmonicPhases | attribute | 0x0010 | list of HarmonicMeasurementStruct; Nullable; Quieter; `max 25` | `PWRQ` | — | none in catalog ( `infrastructure.ac.harmonic_phase`) | absent | no row | no source | no harmonic-phase element | lines 533–540 |
| HarmonicMeasurement.Order | field | 0 | uint8; constraint text `min 1`; decoder `DecodeUintIn` 1..255 | M | — | none in catalog | absent | no row | no source | constraint text has no maximum; decoder maximum is 255 | lines 96 and 87 |
| HarmonicMeasurement.Measurement | field | 1 | int64; Nullable; `-2^62 to 2^62` | M | — | none in catalog | absent | no row | no source | no unit on the field | line 97 |
| PowerFactor | attribute | 0x0011 | int64 (type name has no unit); Nullable; Quieter; NullDefault; constraint `-10000 to 10000`; catalog canonical unit `infrastructure.ac.power_factor` `unit.ratio`, `pv.ac.power_factor` `unit.ratio` | `[ALTC]` | — | `infrastructure.ac.power_factor` partial; `pv.ac.power_factor` partial | present | unknown / `matter.unmapped.v1` (target lines 40, 86) | defined | `unit.ratio` versus unnamed int64; scale not declared (the type is not `percent100ths`); range; nullable; subjects are grid_connection and inverter, not a phase. Absent: `infrastructure.ac.phase_power_factor`, `pv.ac.phase_power_factor` (a prior proposal, a prior proposal) | lines 542–549; catalog lines 118, 178; units `unit.ratio` |
| NeutralCurrent | attribute | 0x0012 | amperage-mA int64; Nullable; Quieter; NullDefault; `-2^62 to 2^62` | `[POLY]` | — | none in catalog ( `infrastructure.ac.neutral_current`) | absent | no row | no source | no neutral-current element | lines 551–558 |
| DIRC | feature | bit 0 | FeatureMap bit `1 << 0`, title DirectCurrent | `O.a+` (Choice name `a`, Num 1, OrMore true, OrLess false, Args optional) | — | none in catalog | absent | no row | no source | dc.* facts are not a feature-bit element | lines 385 and 63 |
| ALTC | feature | bit 1 | title AlternatingCurrent | `O.a+` (same Choice `a`) | — | none in catalog ( `infrastructure.ac.reactive_current`, which is absent) | absent | no row | no source | AC facts are not a feature-bit element | lines 386 and 64 |
| POLY | feature | bit 2 | title PolyphasePower | `[ALTC]` | — | none in catalog ( `infrastructure.ac.neutral_current`, which is absent) | absent | no row | no source | no feature element | lines 387 and 65 |
| HARM | feature | bit 3 | title Harmonics | `[ALTC]` | — | none in catalog ( `infrastructure.ac.harmonic_current`, which is absent) | absent | no row | no source | no feature element | lines 388 and 66 |
| PWRQ | feature | bit 4 | title PowerQuality | `[ALTC]` | — | none in catalog ( `infrastructure.ac.harmonic_phase`, which is absent) | absent | no row | no source | no feature element | lines 389 and 67 |
| MeasurementPeriodRanges | event | 0x00 | priority info; field below | `Ranges` | — | none in catalog | absent | no row | no source | no catalog event for period ranges | lines 561–564 |
| MeasurementPeriodRanges.Ranges | event field | 0 | list of MeasurementRangeStruct; constraint `1 to numberOfMeasurementTypes`; decoder 1..2147483647 | M | — | none in catalog | absent | no row | no source | struct fields are the Ranges.* rows above | line 566; decode line 347 |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Commands` field (lines 381–571) |

### ElectricalEnergyMeasurement

Cluster id `0x0091` (145), name `ElectricalEnergyMeasurement`, revision 2 (lines 22–26). No `Commands` field. Attribute and event access is Read / View. This package declares its own MeasurementTypeEnum, MeasurementAccuracyStruct, and MeasurementAccuracyRangeStruct (lines 147–290). Field names, ids, types, and conformance texts match the ElectricalPowerMeasurement copies. MeasurementTypeEnum values are the same 0..16 list, each `M` (lines 153–194).

EnergyMeasurementStruct (lines 137–145): `Energy` energy-mWh int64, `M`, constraint `0 to 2^62`, decoder `DecodeIntIn` maximum 9223372036854775807 (line 124). `StartTimestamp` / `EndTimestamp` epoch-s, conformance text `desc`, end constraint `min startTimestamp + 1`. `StartSystime` / `EndSystime` systime-ms, conformance text `desc`, end constraint `min startSystime + 1`. `ApparentEnergy` energy-mVAh, conformance `P, APPE` with Op `ConfOtherwise` (provisional, else feature APPE), constraint `0 to 2^62`, same decoder maximum. `ReactiveEnergy` energy-mVARh, conformance `P, REAE`, same constraint and decoder maximum.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Accuracy | attribute | 0x0000 | MeasurementAccuracyStruct (one struct, not a list); Fixed | M | EM, ES-if | none in catalog ( `infrastructure.accuracy.*`, `pv.accuracy.*`) | absent | no row | no source | no accuracy element; unlike EPM this attribute is a single struct | lines 396–402 |
| Accuracy.MeasurementType | field | 0 | MeasurementTypeEnum 0..16 as in EPM | M | EM, ES-if | none in catalog | absent | no row | no source | duplicate struct, same gap | line 231 |
| Accuracy.Measured | field | 1 | bool | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog element | line 232 |
| Accuracy.MinMeasuredValue | field | 2 | int64; `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog range | line 233 |
| Accuracy.MaxMeasuredValue | field | 3 | int64; `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog range | line 234 |
| Accuracy.AccuracyRanges | field | 4 | list; `min 1` | M | EM, ES-if | none in catalog | absent | no row | no source | nested fields below | line 235 |
| AccuracyRanges.RangeMin | field | 0 | int64; `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog element | line 282 |
| AccuracyRanges.RangeMax | field | 1 | int64; `-2^62 to 2^62` | M | EM, ES-if | none in catalog | absent | no row | no source | no catalog element | line 283 |
| AccuracyRanges.PercentMax | field | 2 | percent100ths; `max 10000`; decoder 0..10000 | O.a+ (Choice `a`, Num 1, OrMore true, OrLess false) | — | none in catalog | absent | no row | no source | constraint text has no minimum | lines 284 and 269 |
| AccuracyRanges.PercentMin | field | 3 | percent100ths; `max percentTypical`; decoder 0..10000 | `[PercentMax]` | — | none in catalog | absent | no row | no source | same decoder gap | line 285 |
| AccuracyRanges.PercentTypical | field | 4 | percent100ths; `percentMin to percentMax` | `[PercentMin]` | — | none in catalog | absent | no row | no source | same decoder gap | line 286 |
| AccuracyRanges.FixedMax | field | 5 | uint64; `max (2^62) - 1` | O.a+ (same Choice `a`) | — | none in catalog | absent | no row | no source | no catalog element | line 287 |
| AccuracyRanges.FixedMin | field | 6 | uint64; `max fixedMax` | `[FixedMax]` | — | none in catalog | absent | no row | no source | no catalog element | line 288 |
| AccuracyRanges.FixedTypical | field | 7 | uint64; `fixedMin to fixedMax` | `[FixedMin]` | — | none in catalog | absent | no row | no source | no catalog element | line 289 |
| CumulativeEnergyImported | attribute | 0x0001 | EnergyMeasurementStruct; Nullable; Quieter; catalog canonical unit `infrastructure.energy.import` `unit.joule`, `evse.energy.lifetime` `unit.joule`, `storage.energy.charged` `unit.joule` | `IMPE & CUME` | — | on `Energy`: `infrastructure.energy.import` partial; `evse.energy.lifetime` candidate; `storage.energy.charged` candidate | present | unknown / `matter.unmapped.v1` (target lines 51, 13, 137) | defined | `unit.joule` versus energy-mWh, no conversion row; `non_negative` versus the struct's signed energy-mWh field; meter versus battery_pack; `evse.energy.lifetime` is a lifetime meter counter, not an imported counter; `storage.energy.charged` is charge on a battery_pack, not grid import; no start/end on the catalog facts; nullable. Absent proposals: `infrastructure.energy.phase_import`, `pv.ac.phase_energy_imported`, `pv.energy.consumed`, `thermal.energy.electrical_consumed` | lines 404–410; catalog lines 136, 85, 254; units `unit.joule` |
| CumulativeEnergyImported.Energy | field | 0 | energy-mWh; `0 to 2^62`; decoder max 9223372036854775807 | M | — | same three facts as the attribute | present | same three rows | defined | the joule versus energy-mWh loss sits on this field; decoder maximum is not the constraint text | lines 138 and 124 |
| CumulativeEnergyImported.StartTimestamp | field | 1 | epoch-s | `desc` | — | none in catalog | absent | no row | no source | catalog energy facts have no period start | line 139 |
| CumulativeEnergyImported.EndTimestamp | field | 2 | epoch-s; `min startTimestamp + 1` | `desc` | — | none in catalog | absent | no row | no source | no period end | line 140 |
| CumulativeEnergyImported.StartSystime | field | 3 | systime-ms | `desc` | — | none in catalog | absent | no row | no source | no systime | line 141 |
| CumulativeEnergyImported.EndSystime | field | 4 | systime-ms; `min startSystime + 1` | `desc` | — | none in catalog | absent | no row | no source | no systime | line 142 |
| CumulativeEnergyImported.ApparentEnergy | field | 5 | energy-mVAh; `0 to 2^62`; decoder max 9223372036854775807 | `P, APPE` (ConfOtherwise: provisional, else APPE) | — | none in catalog ( `infrastructure.energy.apparent_import`, `pv.energy.apparent_imported`) | absent | no row | no source | no apparent-energy element | lines 143 and 129 |
| CumulativeEnergyImported.ReactiveEnergy | field | 6 | energy-mVARh; `0 to 2^62`; same decoder max | `P, REAE` (ConfOtherwise: provisional, else REAE) | — | none in catalog ( `infrastructure.energy.reactive_import`, `pv.energy.reactive_imported`) | absent | no row | no source | no reactive-energy element | lines 144 and 130 |
| CumulativeEnergyExported | attribute | 0x0002 | EnergyMeasurementStruct; Nullable; Quieter; catalog canonical unit `infrastructure.energy.export` `unit.joule`, `pv.energy.generated` `unit.joule`, `storage.energy.discharged` `unit.joule`, `pv.dc.energy` `unit.joule` | `EXPE & CUME` | — | on `Energy`: `infrastructure.energy.export` partial; `pv.energy.generated` candidate; `storage.energy.discharged` candidate; `pv.dc.energy` candidate | present | unknown / `matter.unmapped.v1` (target lines 50, 104, 138, 101) | defined | `unit.joule` versus energy-mWh, no conversion row; `non_negative`; `pv.energy.generated` is a pv_system aggregate, not an export counter; `storage.energy.discharged` is a battery_pack; `pv.dc.energy` is a pv_string quantity (catalog plane `physical`); no period bounds; nullable. Absent: `evse.energy.lifetime_exported`, `infrastructure.energy.phase_export`, `pv.ac.phase_energy_exported`, `pv.dc.aggregate_energy` | lines 412–418; catalog lines 135, 204, 255, 193 |
| CumulativeEnergyExported.Energy | field | 0 | energy-mWh; same constraint and decoder as imported Energy | M | — | same four facts as the attribute | present | same four rows | defined | same joule versus energy-mWh loss | line 138 |
| CumulativeEnergyExported.StartTimestamp | field | 1 | epoch-s | `desc` | — | none in catalog | absent | no row | no source | no period start | line 139 |
| CumulativeEnergyExported.EndTimestamp | field | 2 | epoch-s | `desc` | — | none in catalog | absent | no row | no source | no period end | line 140 |
| CumulativeEnergyExported.StartSystime | field | 3 | systime-ms | `desc` | — | none in catalog | absent | no row | no source | no systime | line 141 |
| CumulativeEnergyExported.EndSystime | field | 4 | systime-ms | `desc` | — | none in catalog | absent | no row | no source | no systime | line 142 |
| CumulativeEnergyExported.ApparentEnergy | field | 5 | energy-mVAh; `P, APPE` | `P, APPE` | — | none in catalog ( `infrastructure.energy.apparent_export`, `pv.energy.apparent_exported`) | absent | no row | no source | no apparent-energy element | line 143 |
| CumulativeEnergyExported.ReactiveEnergy | field | 6 | energy-mVARh; `P, REAE` | `P, REAE` | — | none in catalog ( `infrastructure.energy.reactive_export`, `pv.energy.reactive_exported`) | absent | no row | no source | no reactive-energy element | line 144 |
| PeriodicEnergyImported | attribute | 0x0003 | EnergyMeasurementStruct; Nullable; Quieter; catalog canonical unit `evse.energy.session` `unit.joule` | `IMPE & PERE` | — | `evse.energy.session` candidate | present | unknown / `matter.unmapped.v1` (target line 14) | defined | session subject `resource.charging_session`, `unit.joule`, `non_negative`, and no start/end, versus a period import struct in energy-mWh. Yield facts are export-shaped and are not listed here. Absent proposals: `thermal.dimension.period`, `thermal.energy.electrical_consumed` | lines 420–426; catalog line 86 |
| PeriodicEnergyImported.Energy | field | 0 | energy-mWh; catalog canonical unit `evse.energy.session` `unit.joule` | M | — | `evse.energy.session` candidate | present | unknown / `matter.unmapped.v1` | defined | joule versus energy-mWh; session versus import period | line 138 |
| PeriodicEnergyImported.StartTimestamp | field | 1 | epoch-s | `desc` | — | none in catalog | absent | no row | no source | session fact has no start | line 139 |
| PeriodicEnergyImported.EndTimestamp | field | 2 | epoch-s | `desc` | — | none in catalog | absent | no row | no source | no end | line 140 |
| PeriodicEnergyImported.StartSystime | field | 3 | systime-ms | `desc` | — | none in catalog | absent | no row | no source | no systime | line 141 |
| PeriodicEnergyImported.EndSystime | field | 4 | systime-ms | `desc` | — | none in catalog | absent | no row | no source | no systime | line 142 |
| PeriodicEnergyImported.ApparentEnergy | field | 5 | energy-mVAh | `P, APPE` | — | none in catalog | absent | no row | no source | no apparent-energy element | line 143 |
| PeriodicEnergyImported.ReactiveEnergy | field | 6 | energy-mVARh | `P, REAE` | — | none in catalog | absent | no row | no source | no reactive-energy element | line 144 |
| PeriodicEnergyExported | attribute | 0x0004 | EnergyMeasurementStruct; Nullable; Quieter; catalog canonical unit `pv.energy.yield_day` `unit.joule`, `pv.energy.yield_month` `unit.joule`, `pv.energy.yield_year` `unit.joule` | `EXPE & PERE` | — | `pv.energy.yield_day` candidate; `pv.energy.yield_month` candidate; `pv.energy.yield_year` candidate | present | unknown / `matter.unmapped.v1` (target lines 105, 106, 107) | defined | `unit.joule` versus energy-mWh; pv_system `aggregate`; no start, end, or systime on the facts; day/month/year is in the id, not a declared epoch bound; nullable | lines 428–434; catalog lines 205–207 |
| PeriodicEnergyExported.Energy | field | 0 | energy-mWh | M | — | the three yield facts, candidate | present | unknown / `matter.unmapped.v1` | defined | same joule and period losses | line 138 |
| PeriodicEnergyExported.StartTimestamp | field | 1 | epoch-s | `desc` | — | none in catalog | absent | no row | no source | yield facts have no start field | line 139 |
| PeriodicEnergyExported.EndTimestamp | field | 2 | epoch-s | `desc` | — | none in catalog | absent | no row | no source | no end | line 140 |
| PeriodicEnergyExported.StartSystime | field | 3 | systime-ms | `desc` | — | none in catalog | absent | no row | no source | no systime | line 141 |
| PeriodicEnergyExported.EndSystime | field | 4 | systime-ms | `desc` | — | none in catalog | absent | no row | no source | no systime | line 142 |
| PeriodicEnergyExported.ApparentEnergy | field | 5 | energy-mVAh | `P, APPE` | — | none in catalog | absent | no row | no source | no apparent-energy element | line 143 |
| PeriodicEnergyExported.ReactiveEnergy | field | 6 | energy-mVARh | `P, REAE` | — | none in catalog | absent | no row | no source | no reactive-energy element | line 144 |
| CumulativeEnergyReset | attribute | 0x0005 | CumulativeEnergyResetStruct; Nullable; NullDefault | `[CUME]` | — | none in catalog | absent | no row | no source | no reset element | lines 436–443 |
| CumulativeEnergyReset.ImportedResetTimestamp | field | 0 | epoch-s; Nullable; NullDefault | `[IMPE]` | — | none in catalog | absent | no row | no source | no reset timestamp | line 91 |
| CumulativeEnergyReset.ExportedResetTimestamp | field | 1 | epoch-s; Nullable; NullDefault | `[EXPE]` | — | none in catalog | absent | no row | no source | no reset timestamp | line 92 |
| CumulativeEnergyReset.ImportedResetSystime | field | 2 | systime-ms; Nullable; NullDefault | `[IMPE]` | — | none in catalog | absent | no row | no source | no reset systime | line 93 |
| CumulativeEnergyReset.ExportedResetSystime | field | 3 | systime-ms; Nullable; NullDefault | `[EXPE]` | — | none in catalog | absent | no row | no source | no reset systime | line 94 |
| IMPE | feature | bit 0 | title ImportedEnergy | `O.a+` (Choice `a`, Num 1, OrMore true, OrLess false) | — | none in catalog | absent | no row | no source | import facts are not a feature bit | lines 387 and 51 |
| EXPE | feature | bit 1 | title ExportedEnergy | `O.a+` (same Choice `a`) | — | none in catalog | absent | no row | no source | export facts are not a feature bit | lines 388 and 52 |
| CUME | feature | bit 2 | title CumulativeEnergy | `O.b+` (Choice `b`, Num 1, OrMore true, OrLess false) | — | none in catalog | absent | no row | no source | cumulative facts are not a feature bit | lines 389 and 53 |
| PERE | feature | bit 3 | title PeriodicEnergy | `O.b+` (same Choice `b`) | — | none in catalog | absent | no row | no source | yield facts are not a feature bit | lines 390 and 54 |
| APPE | feature | bit 4 | title ApparentEnergy | `P, O` (ConfOtherwise: provisional, else optional) | — | none in catalog ( apparent energy ids, all absent) | absent | no row | no source | no feature element | lines 391 and 55 |
| REAE | feature | bit 5 | title ReactiveEnergy | `P, O` (ConfOtherwise: provisional, else optional) | — | none in catalog ( reactive energy ids, all absent) | absent | no row | no source | no feature element | lines 392 and 56 |
| CumulativeEnergyMeasured | event | 0x00 | priority info | `CUME` | — | none in catalog ( `infrastructure.event.energy_measured`) | absent | no row | no source | no catalog event | lines 447–449 |
| CumulativeEnergyMeasured.EnergyImported | event field | 0 | EnergyMeasurementStruct | `CUME & IMPE` | — | same candidates as CumulativeEnergyImported, on the Energy field only | present for those facts | unknown / `matter.unmapped.v1` for those facts | defined | same losses as CumulativeEnergyImported; the event itself has no catalog element | line 451 |
| CumulativeEnergyMeasured.EnergyExported | event field | 1 | EnergyMeasurementStruct | `CUME & EXPE` | — | same candidates as CumulativeEnergyExported, on the Energy field only | present for those facts | unknown / `matter.unmapped.v1` | defined | same losses as CumulativeEnergyExported | line 452 |
| PeriodicEnergyMeasured | event | 0x01 | priority info | `PERE` | — | none in catalog ( `infrastructure.event.energy_measured`) | absent | no row | no source | no catalog event | lines 457–459 |
| PeriodicEnergyMeasured.EnergyImported | event field | 0 | EnergyMeasurementStruct; catalog canonical unit `evse.energy.session` `unit.joule` | `PERE & IMPE` | — | `evse.energy.session` candidate | present | unknown / `matter.unmapped.v1` | defined | same session losses | line 461 |
| PeriodicEnergyMeasured.EnergyExported | event field | 1 | EnergyMeasurementStruct | `PERE & EXPE` | — | the three yield facts, candidate | present | unknown / `matter.unmapped.v1` | defined | same yield losses | line 462 |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Commands` field (lines 384–467) |

The four energy attributes share one struct definition. The field rows are repeated so each attribute's feed stays on that attribute. Start, end, systime, apparent, and reactive fields are the same declarations (lines 139–144) under every attribute.

### PowerTopology

Cluster id `0x009C` (156), name `PowerTopology`, revision 1 (lines 19–23). No commands. No events. Attribute access is Read / View.

Cluster-level candidates, not rows: no attribute, command, event, or feature has a relation as its value. The target withholds five relations with `target_construct` cluster_id 156 and equivalence `Hypothesis` (target lines 25, 61, 62, 63, 114):

- `evse.relation.evse_meter` (catalog line 103): `core_type` `measures`, from `resource.evse` to `resource.meter`.
- `infrastructure.relation.feeder_circuit` (catalog line 153): `core_type` `supplies`, medium `electrical`, feeder to electrical_circuit.
- `infrastructure.relation.grid_connection_feeder` (catalog line 154): `core_type` `supplies`, medium `electrical`, grid_connection to feeder.
- `infrastructure.relation.grid_connection_meter` (catalog line 155): `core_type` `measures`, grid_connection to meter.
- `pv.relation.inverter_array` (catalog line 222): `core_type` `supplies`, medium `electrical`, inverter to pv_array.

Loss for each: the target loss kind on those rows is identity and irreversible in the markdown account (matter-1.6.1-v1.md lines 80–86); equivalence is `Hypothesis`; the cluster attributes are lists of `endpoint-no`, and this target allocates no endpoint (`non_claims` includes `endpoint_allocation`, JSON line 37). They are repeated in section 5 because they are not the value of an element.

The cluster is `Mandatory: true` on ElectricalSensor. No element below has conformance text `M`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AvailableEndpoints | attribute | 0x0000 | list of endpoint-no uint16; Fixed; constraint `max 20` | `SET` | — | none in catalog (no element is an endpoint-no list) | absent | no row | no source | the five withheld relations are cluster-level hypotheses, not this list | lines 55–61 |
| ActiveEndpoints | attribute | 0x0001 | list of endpoint-no uint16; NonVolatile; constraint `max 20` | `DYPF` | — | none in catalog | absent | no row | no source | declared in this revision; see section 6 | lines 63–69 and const line 28 |
| NODE | feature | bit 0 | title NodeTopology | `O.a` (Choice name `a`, Num 1, OrMore false, OrLess false) | — | none in catalog | absent | no row | no source | no feature element | lines 48 and 38 |
| TREE | feature | bit 1 | title TreeTopology | `O.a` (same Choice `a`) | — | none in catalog | absent | no row | no source | no feature element | lines 49 and 39 |
| SET | feature | bit 2 | title SetTopology | `O.a` (same Choice `a`) | — | none in catalog | absent | no row | no source | no feature element | lines 50 and 40 |
| DYPF | feature | bit 3 | title DynamicPowerFlow | `[SET]` | — | none in catalog | absent | no row | no source | no feature element | lines 51 and 41 |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Commands` field (lines 45–71) |

### MeterIdentification

Cluster id `0x0B06` (2822), name `MeterIdentification`, revision 1 (lines 22–26). No commands. No events. Mandatory on ElectricalUtilityMeter. Attribute access is Read / View.

MeterTypeEnum (lines 53–66): `Utility` 0, `Private` 1, `Generic` 2, each `M`. PowerThresholdSourceEnum (lines 108–121): `Contract` 0, `Regulator` 1, `Equipment` 2, each `M`.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeterType | attribute | 0x0000 | MeterTypeEnum; Nullable | M | EU | none in catalog ( `infrastructure.meter.kind`) | absent | no row | no source | `resource.meter` is a resource_kind, not this enum | lines 138–143; enum lines 62–66 |
| PointOfDelivery | attribute | 0x0001 | string; Nullable; constraint `max 64` | M | EU | none in catalog ( `infrastructure.meter.point_of_delivery`) | absent | no row | no source | no delivery-point element; `identification_schemes` is `[]` | lines 145–151; catalog line 197 |
| MeterSerialNumber | attribute | 0x0002 | string; Nullable; constraint `max 64` | M | EU | none in catalog ( `equipment.identification.serial_number`; no `equipment.*` element in the compact catalog) | absent | no row | no source | no serial-number element. This row names the attribute only | lines 153–159 |
| ProtocolVersion | attribute | 0x0003 | string; Nullable; constraint `max 64` | O | — | none in catalog ( `infrastructure.meter.protocol_version`) | absent | no row | no source | optional string | lines 161–167 |
| PowerThreshold | attribute | 0x0004 | PowerThresholdStruct; Nullable; catalog canonical unit `infrastructure.limit.fallback_power` `unit.watt` | `PWRTHLD` | — | none in catalog ( `infrastructure.meter.power_threshold`, `infrastructure.meter.apparent_power_threshold`, `infrastructure.meter.power_threshold_source`) | absent | no row | no source | `infrastructure.limit.fallback_power` is not a feed: it is a grid_connection limit, `non_negative`, `unit.watt`, and it has no PowerThresholdSource value. Refused as ambiguous. Listed in section 5 | lines 169–175; catalog line 138 |
| PowerThreshold.PowerThreshold | field | 0 | power-mW int64 | `O.b` (Choice name `b`, Num 1, OrMore false, OrLess false) | — | none in catalog | absent | no row | no source | no threshold element | line 97 |
| PowerThreshold.ApparentPowerThreshold | field | 1 | power-mVA int64 | `O.b` (same Choice `b`) | — | none in catalog | absent | no row | no source | no threshold element | line 98 |
| PowerThreshold.PowerThresholdSource | field | 2 | PowerThresholdSourceEnum; Nullable | M | — | none in catalog | absent | no row | no source | M inside the struct; the struct's attribute conformance is `PWRTHLD` | line 99 |
| PWRTHLD | feature | bit 0 | title PowerThreshold | O | — | none in catalog ( `infrastructure.meter.power_threshold`, which is absent) | absent | no row | no source | no feature element | lines 134 and 44 |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Commands` field (lines 131–176) |

### CommodityMetering

Cluster id `0x0B07` (2823), name `CommodityMetering`, revision 1 (lines 22–26). No commands. No events. No feature constants. The file declares `type Feature uint32` (line 39) and the `Definition` literal has no `Features` field. On ElectricalMeter the cluster conformance string is `P, M` and `Mandatory` is unset, so `M` here is not `EM`.

TariffUnitEnum (lines 77–88): `KWh` 0, `KVAh` 1, each `M`.

`infrastructure.energy.import` and `infrastructure.energy.export` are feeds of ElectricalEnergyMeasurement cumulative energy, not of these attributes. They have no tariff-component dimension (catalog lines 135–136). They are not listed again as CommodityMetering feeds.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeteredQuantity | attribute | 0x0000 | list of MeteredQuantityStruct; Nullable; constraint `max maximumMeteredQuantities` | M | — (cluster `P, M`, Mandatory unset) | none in catalog ( `energy.metering.quantity`) | absent | no row | no source | joule counters are not tariff-component quantities | lines 103–110 |
| MeteredQuantity.TariffComponentIds | field | 0 | list of uint32; constraint `max 128`; decoder 0..128 | M | — | none in catalog | absent | no row | no source | no tariff-component id element | line 67 |
| MeteredQuantity.Quantity | field | 1 | int64; the field type name has no unit | M | — | none in catalog | absent | no row | no source | unit is the TariffUnit enum on the cluster, not a unit on this field | line 68 |
| MeteredQuantityTimestamp | attribute | 0x0001 | epoch-s uint32; Nullable | M | — (cluster `P, M`, Mandatory unset) | none in catalog ( `energy.metering.timestamp`) | absent | no row | no source | no metering timestamp | lines 112–117 |
| TariffUnit | attribute | 0x0002 | TariffUnitEnum; Nullable | M | — (cluster `P, M`, Mandatory unset) | none in catalog ( `energy.tariff.unit_basis`) | absent | no row | no source | KWh and KVAh are not `unit.joule` | lines 119–124; enum lines 85–88 |
| MaximumMeteredQuantities | attribute | 0x0003 | uint16; Nullable; constraint `min 1` | M | — (cluster `P, M`, Mandatory unset) | none in catalog ( `energy.metering.maximum_quantities`) | absent | no row | no source | no cardinality element | lines 126–132 |
| (features) | feature | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Features` field (lines 99–133) |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Commands` field |

### ElectricalGridConditions

Cluster id `0x00A0` (160), name `ElectricalGridConditions`, revision 1 (lines 22–26). No commands. Not on any of the four device files' `Servers`. Schema conformance on ElectricalMeter and ElectricalEnergyTariff is `O` (schema lines 19574–19578 and 19419–19423). Attribute access is Read / View except LocalGenerationAvailable.

ThreeLevelEnum (lines 102–115): `Low` 0, `Medium` 1, `High` 2, each `M`.

ElectricalGridConditionsStruct fields are all conformance `M` (lines 87–93): `PeriodStart` epoch-s uint32; `PeriodEnd` epoch-s Nullable, constraint `min periodStart + 1`; `GridCarbonIntensity` int16, no unit name; `GridCarbonLevel` ThreeLevelEnum; `LocalCarbonIntensity` int16, no unit name; `LocalCarbonLevel` ThreeLevelEnum.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LocalGenerationAvailable | attribute | 0x0000 | bool; Nullable; access RW, Read View, Write Operate | M | — | none in catalog ( `energy.grid.local_generation_available`, `energy.operation.set_local_generation_available`) | absent | no row | no source | cluster is optional in schema and absent from the four device files | lines 160–165 |
| CurrentConditions | attribute | 0x0001 | ElectricalGridConditionsStruct; Nullable | M | — | none in catalog ( `energy.grid.carbon_intensity`, `energy.grid.carbon_level`, `energy.grid.local_carbon_intensity`, `energy.grid.local_carbon_level`, `energy.grid.start`, `energy.grid.end`) | absent | no row | no source | no grid-condition element | lines 167–173 |
| CurrentConditions.PeriodStart | field | 0 | epoch-s | M | — | none in catalog | absent | no row | no source | M inside the struct | line 88 |
| CurrentConditions.PeriodEnd | field | 1 | epoch-s; Nullable; `min periodStart + 1` | M | — | none in catalog | absent | no row | no source | no period element | line 89 |
| CurrentConditions.GridCarbonIntensity | field | 2 | int16; no unit name in the type | M | — | none in catalog | absent | no row | no source | unit unknown | line 90 |
| CurrentConditions.GridCarbonLevel | field | 3 | ThreeLevelEnum | M | — | none in catalog | absent | no row | no source | no level element | line 91 |
| CurrentConditions.LocalCarbonIntensity | field | 4 | int16; no unit name | M | — | none in catalog | absent | no row | no source | unit unknown | line 92 |
| CurrentConditions.LocalCarbonLevel | field | 5 | ThreeLevelEnum | M | — | none in catalog | absent | no row | no source | no level element | line 93 |
| ForecastConditions | attribute | 0x0002 | list of ElectricalGridConditionsStruct; constraint `max 56`; decoder 0..56 | `FORE` | — | none in catalog (same a prior proposal `energy.grid.*` ids, absent) | absent | no row | no source | same struct as CurrentConditions | lines 175–181; decode line 148 |
| FORE | feature | bit 0 | title Forecasting | O | — | none in catalog (same absent a prior proposal ids) | absent | no row | no source | no feature element | lines 156 and 47 |
| CurrentConditionsChanged | event | 0x00 | priority info | O | — | none in catalog ( `energy.event.grid_conditions_changed`) | absent | no row | no source | no catalog event | lines 184–187 |
| CurrentConditionsChanged.CurrentConditions | event field | 0 | ElectricalGridConditionsStruct; Nullable | M | — | none in catalog | absent | no row | no source | same struct fields | line 189 |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Commands` field (lines 153–194) |

## 4. Mandatory elements without a source

Rule used: a device file sets the cluster `Mandatory: true`, and the element's conformance text is `M`, and the catalog has no element. Feature-gated elements are not in this list. CommodityMetering is not in this list because its device-file `Mandatory` is unset.

ElectricalMeter, and ElectricalSensor only when that optional cluster is mounted (`ES-if`):

- ElectricalPowerMeasurement `PowerMode` `0x0000`.
- ElectricalPowerMeasurement `NumberOfMeasurementTypes` `0x0001`.
- ElectricalPowerMeasurement `Accuracy` `0x0002`, and its `M` fields `MeasurementType`, `Measured`, `MinMeasuredValue`, `MaxMeasuredValue`, `AccuracyRanges` (and the `M` fields of MeasurementAccuracyRangeStruct: `RangeMin`, `RangeMax`). No catalog element for any of them.
- ElectricalEnergyMeasurement `Accuracy` `0x0000`, and the same `M` field set in that package's copy of the structs.

`ActivePower` `0x0008` is `M` on that cluster and has catalog elements, so it is not in this list.

ElectricalUtilityMeter:

- MeterIdentification `MeterType` `0x0000`.
- MeterIdentification `PointOfDelivery` `0x0001`.
- MeterIdentification `MeterSerialNumber` `0x0002`.

PowerTopology is `Mandatory: true` on ElectricalSensor. No attribute, command, event, or feature in it has conformance text `M`.

CommodityMetering attributes `MeteredQuantity`, `MeteredQuantityTimestamp`, `TariffUnit`, and `MaximumMeteredQuantities` have conformance text `M`, and their struct fields `TariffComponentIds` and `Quantity` do too. The ElectricalMeter file sets the cluster conformance to `P, M` and does not set `Mandatory`. They are not in the list above. Schema conformance for that requirement is also `P, M` (schema.json line 19596). This accounting does not parse that string into `ConfOtherwise`.

ElectricalGridConditions attributes `LocalGenerationAvailable` and `CurrentConditions` have conformance text `M`. The cluster is not a `Mandatory: true` server of any device type in this group.

## 5. Catalog elements of this domain without a Matter element

Domain here means electrical measurement, energy counters, topology, meter identity, commodity quantity, and grid conditions, as far as these six clusters. An element already named as `partial` or `candidate` in section 3 is not repeated.

No Matter attribute, command, event, or feature in this group is the counterpart:

- `infrastructure.ac.voltage_line_line` (catalog line 121, `unit.volt`, subject `resource.line_pair`, direction `not_applicable`). Target line 43: unknown / `matter.unmapped.v1`. ElectricalPowerMeasurement has no line-pair attribute.
- `infrastructure.energy.self_consumption` (catalog line 137, `unit.joule`, meter, `non_negative`). Target line 52: unknown / `matter.unmapped.v1`. No self-consumption attribute.
- `storage.energy.nominal_capacity`, `storage.energy.remaining`, `storage.energy.usable_capacity` (catalog lines 256–258, `unit.joule`, battery_pack). Target lines 139–141: unknown / `matter.unmapped.v1`. No capacity attribute in these clusters.
- `storage.capacity.charge`, `storage.capacity.discharge` (catalog lines 241–242, `unit.ampere_hour`). Target lines 133–134: unknown / `matter.unmapped.v1`. No ampere-hour attribute.
- `storage.cell.voltage_minimum`, `storage.cell.voltage_maximum` (catalog lines 244 and 243, `unit.volt`, subject `resource.battery_cell`). Target lines 136 and 135: unknown / `matter.unmapped.v1`. Not ElectricalPowerMeasurement `Voltage`.
- Limit facts, not measured attributes of these clusters: `infrastructure.limit.fallback_power` (catalog line 138, `unit.watt`, grid_connection, `non_negative`; target line 53); `pv.limit.active_power`, `pv.limit.active_power_ratio`, `pv.limit.export_power` (catalog lines 208–210; target lines 108–110); `storage.limit.charge_power`, `storage.limit.discharge_power` (catalog lines 259–260; target lines 142–143); `evse.limit.actual_current`, `evse.limit.advertised_current`, `evse.limit.allocated_current`, `evse.limit.allocated_current_phase`, `evse.limit.configured_current` (catalog lines 87–91, `unit.ampere`; target lines 15–19). All of those target rows are unknown / `matter.unmapped.v1`. `fallback_power` is not MeterIdentification `PowerThreshold`.
- Resource kinds with no attribute value: `resource.meter` (catalog line 52), `resource.phase` (53), `resource.grid_connection` (48), `resource.line_pair` (51), `resource.electrical_circuit` (44), `resource.feeder` (47). Core rows are outside the pack roster the target markdown describes (lines 48–49). `resource.meter` is not `MeterSerialNumber`.
- Symbol facts, `value_kind` `symbol`, with no attribute in these clusters: `infrastructure.status.breaker`, `infrastructure.status.connection`, `infrastructure.status.fault`, `infrastructure.status.interlock`, `infrastructure.status.readiness` (catalog lines 164–168); `evse.status.charging`, `evse.status.connection`, `evse.status.fault`, `evse.status.interlock`, `evse.status.readiness` (catalog lines 109–113).
- The five withheld topology relations in the PowerTopology preamble. Target disposition withheld / `matter.power_topology_endpoint_unallocated.v1`, cluster_id 156, equivalence `Hypothesis`. They have no element whose value is the relation.
- Other electrical relations whose target row is unknown / `matter.relation_construct_not_adopted.v1`: `evse.relation.connector_phase` (catalog line 100, target line 22; cited by the `evse.ac.current` projection and not adopted on its own row), `infrastructure.relation.circuit_phase` (catalog line 152, target line 60), `infrastructure.relation.site_grid_connection` (catalog line 156, target line 64), `evse.relation.asset_evse`, `evse.relation.connector_session`, `evse.relation.evse_connector` (catalog lines 99, 101, 102), `pv.relation.array_string`, `pv.relation.inverter_input`, `pv.relation.inverter_phase`, `pv.relation.system_inverter` (catalog lines 221, 223–225; target lines 113, 115–117), and `storage.relation.battery_pack`, `module_cell`, `pack_interface`, `pack_module`, `pack_string`, `system_battery` (catalog lines 271–276, core types `contains` or `groups`; target lines 149–154, all `relation_construct_not_adopted`).
- Services and the read capabilities that point at them, unsupported / `matter.service_not_requested_item.v1` where a target row was read: `evse.service.meter`, `evse.service.phase` (catalog lines 106–107; `evse.service.meter` target line 28); `infrastructure.service.meter`, `infrastructure.service.phase`, `infrastructure.service.grid_connection`, `infrastructure.service.line_pair`, `infrastructure.service.circuit`, `infrastructure.service.feeder` (catalog lines 157–162; meter and grid_connection target lines 69 and 67). Capabilities: `evse.capability.read.meter`, `evse.capability.read.phase` (catalog lines 74–75); `infrastructure.capability.read.meter`, `infrastructure.capability.read.phase`, `infrastructure.capability.read.grid_connection`, `infrastructure.capability.read.circuit`, `infrastructure.capability.read.feeder` (catalog lines 122–126). No command in these six clusters carries those services.

## 6. Disagreements with the prior accounting

a prior accounting status legend, line 3: `present` means on main and the ticket completes its target row; `planned` means added by the ticket; `absent` means a reason is given. Planned ids that the compact catalog does not contain are recorded in section 3 as `none in catalog (proposed by …)`. That matches the job's rule for a prior proposal–a prior proposal and is not a disagreement.

1. PowerTopology `ActiveEndpoints`. a prior accounting line 472: status `absent`, reason text says deprecated or disallowed in Matter 1.6.1, and no element. go-fabric v0.22.2 `go-fabric@v0.22.2:cluster/spec/powertopology/definition_gen.go` lines 28 and 63–68 declare `ActiveEndpoints` id `0x0001`, conformance `DYPF`, NonVolatile, constraint `max 20`. `a prior accounting` a prior claim (line 222) lists `ActiveEndpoints` `0x0001` as an element and does not state that deprecation.
2. Rows marked `present` whose target rows are not a completed projection, except `evse.ac.current`. Legend line 3 defines `present` as the ticket completing the target row. The target has one transformed row in this group.
   - ActiveCurrent, a prior accounting line 285, six ids. `evse.ac.current` is transformed (target line 4). `infrastructure.ac.current`, `pv.ac.current`, `pv.dc.current`, `pv.dc.aggregate_current`, `storage.pack.current` are unknown / `matter.unmapped.v1` (target lines 38, 84, 100, 97, 146).
   - ApparentPower, line 288: `infrastructure.ac.apparent_power`, `infrastructure.power.apparent`, `pv.ac.aggregate_apparent_power`, `pv.ac.apparent_power`, all unknown / `matter.unmapped.v1` (target lines 37, 54, 79, 83).
   - Frequency, line 289: `evse.ac.frequency`, `infrastructure.ac.frequency`, `pv.ac.frequency`, all unknown / `matter.unmapped.v1` (target lines 5, 39, 85).
   - ReactivePower, line 298: `infrastructure.ac.reactive_power`, `infrastructure.power.export_reactive`, `infrastructure.power.import_reactive`, `pv.ac.aggregate_reactive_power`, `pv.ac.reactive_power`, all unknown / `matter.unmapped.v1` (target lines 41, 56, 58, 81, 87).
   - Voltage, line 302: `evse.ac.voltage`, `infrastructure.ac.voltage`, `pv.ac.voltage`, `pv.dc.aggregate_voltage`, `pv.dc.voltage`, `storage.pack.voltage`, all unknown / `matter.unmapped.v1` (target lines 6, 42, 88, 99, 103, 148).
   - PeriodicEnergyExported, line 318: `pv.energy.yield_day`, `pv.energy.yield_month`, `pv.energy.yield_year`, all unknown / `matter.unmapped.v1` (target lines 105–107).
3. Rows marked `planned` that name ids already in the catalog at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`. Legend line 3 defines `planned` as added by the ticket.
   - ActivePower, line 286, already present: `evse.ac.active_power` (catalog 68), `infrastructure.ac.active_power` (114), `infrastructure.power.pcc` (151), `pv.ac.active_power` (169), `pv.ac.aggregate_active_power` (170), `pv.dc.aggregate_power` (190), `pv.dc.power` (194), `storage.pack.power` (264). Not in the catalog: `evse.ac.total_active_power`, `thermal.measurement.electrical_power`.
   - PowerFactor, line 294, already present: `infrastructure.ac.power_factor` (118), `pv.ac.power_factor` (178). Not in the catalog: `infrastructure.ac.phase_power_factor`, `pv.ac.phase_power_factor`.
   - CumulativeEnergyExported, line 315, already present: `infrastructure.energy.export` (135), `pv.energy.generated` (204), `storage.energy.discharged` (255). Not in the catalog: `evse.energy.lifetime_exported`, `infrastructure.energy.phase_export`, `pv.ac.phase_energy_exported`, `pv.dc.aggregate_energy`. The catalog does contain `pv.dc.energy` (193), which that a prior accounting cell does not name.
   - CumulativeEnergyImported, line 316, already present: `evse.energy.lifetime` (85), `infrastructure.energy.import` (136), `storage.energy.charged` (254). Not in the catalog: `infrastructure.energy.phase_import`, `pv.ac.phase_energy_imported`, `pv.energy.consumed`, `thermal.energy.electrical_consumed`.
4. RMS. a prior accounting lines 299–301 mark `RmsCurrent`, `RmsPower`, and `RmsVoltage` absent and state that the AC current, power, and voltage fields are RMS. `pack-metadata-v1.json` field records for those AC facts contain no RMS marker. The compact catalog attribute JSON for those facts does not contain an RMS key. `a prior accounting` a prior claim (line 198) says that RMS reading is inferred and is not stated in the pack. The pack records also do not state the opposite.
5. The `present` lists are not the full set of same-quantity catalog facts used in section 3. ActiveCurrent's list omits `pv.ac.aggregate_current` (catalog line 172, target line 80, unknown / `matter.unmapped.v1`). Voltage's list omits `pv.ac.aggregate_voltage` (catalog line 174, target line 82, unknown / `matter.unmapped.v1`).

`a prior accounting` line 26 says the projection maps `evse.ac.current` and gives disposition counts that match the JSON counts in section 1. That headline is not contradicted by the target JSON. Its "fed" column is a driver search (lines 11–13) and is not used here; see section 7.

a prior accounting PowerTopology `AvailableEndpoints` (line 473) is `absent` with a derivation reason. The Matter attribute exists (definition lines 55–61). The legend's `absent` is about a SemReg element, and no catalog element is an endpoint list, so that status is not contradicted. a prior accounting device-type rows (lines 1047–1064) do not name these four device types. CommodityMetering in the prior accounting has no feature rows; the cluster defines no feature bits.

## 7. Uncertainty

- Whether `Type.Base` causes a constructed ElectricalMeter to mount ElectricalEnergyTariff servers, or ElectricalUtilityMeter to mount MeterReferencePoint servers, is not settled by `go-fabric@v0.22.2:device/type.go`, `go-fabric@v0.22.2:device/base.go`, or `go-fabric@v0.22.2:device/device.go` `composes`. Both the device-file `Servers` list and the schema `requirements` list are reported in section 2.
- Schema Descriptor requirements on these device types have no `conformance` key (ElectricalSensor line 18994, ElectricalMeter line 19552, ElectricalUtilityMeter line 19124, MeterReferencePoint line 19224). No conformance is inferred from that absence.
- The device-file string `P, M` on CommodityMetering is not parsed. The generated cluster features `APPE` and `REAE` do parse `P, O` as `ConfOtherwise`. Those are different literals.
- Choice records are copied as `Text`, `Op`, and `Choice` fields (`Name`, `Num`, `OrMore`, `OrLess`). No further English reading of `O.a+` or `O.a` is added.
- Frequency's int64 and PowerFactor's int64 have no unit in the type name. No milli-hertz or hundredths factor is declared. `unit.hertz` and `unit.ratio` are the catalog units. Whether they match at a scale is unknown.
- `unit.joule` versus `energy-mWh`, and `unit.watt` versus `power-mW`, have no conversion row except the ampere row for `evse.ac.current`. No factor is computed here.
- Whether the AC catalog facts are RMS is not stated in pack-metadata or in the catalog attributes. Section 3 keeps them as candidates on the Rms* attributes.
- ElectricalGridConditions intensity fields are `int16` with no unit name (definition lines 90 and 92). The unit is unknown.
- Commodity `Quantity` is `int64` with no unit on the field (line 68). `TariffUnit` is the enum `KWh` or `KVAh`. A mapping onto `unit.joule` is not declared.
- Global attribute ids are in `go-fabric@v0.22.2:cluster/spec/instance.go` and are not cluster elements. Behaviour beyond those constants was not read.
- Driver feeding is not a fact of this job. `a prior accounting` lines 11–13 define "fed" by a string search on other working trees, including semreg main rather than SHA `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:`. Those feed claims are not checked here.
- The semreg fixture and the docs-semantic catalog both have `identification_schemes` `[]` and `evse.ac.current`. A full byte diff was not done.
- Acceptance-vector bounds were not used. They are not the catalog element's declared range.
- The target markdown's 126 and the JSON's 183 unknown rows are both accounted in section 1 from the files' own counts. No further row-class split was required for these clusters.
- Decoder bounds and constraint text differ where section 3 says so (energy maximum, harmonic `Order`, percent minimum). Both are declared in the generated file. Neither is selected as the specification over the other.
- Tag `v0.13.12` versus directory `v0.22.2`: only the three adopted identities were compared, and they match. Everything else about the two tags is unknown.
