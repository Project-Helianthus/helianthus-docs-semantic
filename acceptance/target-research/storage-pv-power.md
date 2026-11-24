---
status: "research notes for Matter 1.6.1 power-source clusters; no mapping is decided and no canonical target is written."
---

# Storage, PV and power source

Matter 1.6.1 cluster accounting for Storage, PV and power source. Identifiers, conformance, types and units are read from go-fabric@v0.22.2:parity/schema.json (revision 1.6.1, data model revision 21) and the generated cluster and device files cited below. Catalog elements are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json and semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json. Canonical units are the `canonical_unit` field of docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json. Target rows are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json and docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md. No mapping is chosen. No grade in this note is `exact`. Charge capacity stays `unit.ampere_hour` where the catalog defines it; `storage.capacity.remaining` and `storage.capacity.full_charge` are absent from the pinned catalog. A catalog canonical unit is written beside the Matter unit on each element row that names a catalog field.

Read-only source accounting for the Power Source cluster group (battery storage, solar power, power source). No mapping is decided here.

## 1. Header

- Queue row QQ04: `TARGET-MAT-R` read-only source accounting by cluster; no canonical JSON writer here (the research row).
- docs-semantic frozen SHA: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`. `git rev-parse HEAD` in the pinned files returned that SHA.
- semreg frozen SHA: `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:`. `git rev-parse HEAD` in the pinned files returned that SHA. `fixtures/v1/element-catalog-v1.json` at that SHA has `identification_schemes` `[]` at line 197. Grep of that fixture finds `pv.status.operating` at line 8917, `storage.capacity.charge` at line 9226, `storage.pack.voltage` at line 10229, and `storage.state.soc` at line 11066. The docs-semantic catalog at its frozen SHA has the same line numbers for `storage.pack.voltage` and `storage.state.soc`. A byte-for-byte diff of the two catalogs was not done.
- go-fabric: module path `go-fabric`, directory `v0.22.2` (`go-fabric v0.22.2`). `go.mod` does not state the tag. `go-fabric@v0.22.2:parity/schema.json` key `matter` (lines 2–7): `revision` `1.6.1`, `specificationVersion` `17170688`, `interactionModelRevision` `12`, `dataModelRevision` `21`, `sourceCommit` `a commit id recorded in the cited file`. Each cluster package comment says the file was generated from the matter.js model at `a commit id recorded in the cited file` (Matter 1.6.1).
- The Matter 1.6.1 target pins a different module tag. `api/v1/targets/matter-1.6.1-v1.json` `model_source`: repository `go-fabric`, tag `v0.13.12`, `inspection_grade` `Proven`, `execution_grade` `Unknown`, `standards_equivalence` `Unknown`. Adopted models in that object: Electrical Sensor `device_type_id` 1296 revision 1; Power Topology `cluster_id` 156 revision 1; Electrical Power Measurement `cluster_id` 144 revision 3 attribute id 5 `ActiveCurrent`. PowerSource, PowerSourceConfiguration, BatteryStorage, and SolarPower are not in `model_source.models`. A full diff of tag `v0.13.12` against `v0.22.2` was not done.
- Target contract at that SHA: `helianthus.gateway.matter-projection/v1`, status `adoption_projection_contract_pre_1_0`, `mapping_revision` 1, target `matter.data-model` version `1.6.1`. Pack pins include `pv` `1.0.0` and `storage` `1.1.0`. `non_claims` includes `endpoint_allocation` and `conformance`. `git grep` of `tests/test_matter161_target.py` and `api/v1/targets/matter-1.6.1-v1.md` at that SHA found no `PowerSource`, `BatteryStorage`, `SolarPower`, `0x002F`, or `0x002E`.

### Files read

- Plan: the registry unit rule (opening), `the documentation rules` (opening), `the documentation rules` (opening, including rule 0), the research row (QQ04).
- Pinned files: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`, `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`.
- docs-semantic at the frozen SHA: `api/v1/element-catalog-v1.json` (the cited elements, `identification_schemes` `[]`, no `canonical_unit` key), `api/v1/pack-metadata-v1.json` (canonical units), `api/v1/targets/matter-1.6.1-v1.json` (header and `model_source`).
- semreg at the frozen SHA: `fixtures/v1/element-catalog-v1.json` (the four ids above and `identification_schemes`).
- go-fabric v0.22.2: `go-fabric@v0.22.2:parity/schema.json` (header; device types PowerSource, SolarPower, BatteryStorage; cluster PowerSource types and features); `go-fabric@v0.22.2:device/power_source_gen.go`, `go-fabric@v0.22.2:device/solar_power_gen.go`, `go-fabric@v0.22.2:device/battery_storage_gen.go`; `go-fabric@v0.22.2:cluster/spec/powersource/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/powersourceconfiguration/definition_gen.go`; `go-fabric@v0.22.2:cluster/spec/instance.go` lines 15–23; `go.mod`.
- Prior claims were checked only against a prior accounting (legend lines 1–8; PowerSource lines 93–135; device-type stub lines 1047–1064); `audits/semreg-loss-20261118/a prior accounting` (a prior claim through a prior claim, lines 218–235).

### How to read the tables

Catalog element records have no unit field. Units below are `pack-metadata-v1.json` `fields[].canonical_unit.id` for that field ref. `identification_schemes` is `[]`.

Global attributes are not cluster elements. `go-fabric@v0.22.2:cluster/spec/instance.go` lines 16–22 name six ids every server answers: `AttrGeneratedCommandList` `0xFFF8`, `AttrAcceptedCommandList` `0xFFF9`, `AttrEventList` `0xFFFA`, `AttrAttributeList` `0xFFFB`, `AttrFeatureMap` `0xFFFC`, `AttrClusterRevision` `0xFFFD`. The comment on that block cites Matter Core §7.13. Neither `definition_gen.go` lists them. They are not rows below.

Every attribute in both `Definition` literals has `Access` `RW` `"R"` and `Read` `PrivilegeView`. Event access is the same. No attribute in either literal has a `Default` key. No attribute type name in either cluster is a unit name (`voltage-mV`, `amperage-mA`, and the like do not appear). `go-fabric@v0.22.2:parity/schema.json` gives the same type strings (`uint32`, `uint16`, `uint8`, `bool`, `string`, the enum names, `list`).

Grades: `exact` would require the same meaning, kind, and unit with loss `none`. No row in this group is `exact`. `partial` means the catalog fact is the same quantity family and the losses are named. `candidate` means a symbol fact sits in the same status or fault family and the element record does not contain symbol literals, so the enum mapping is not established. A quantity is also `candidate` when it is a cumulative lifetime counter and the attribute is a fixed capacity, and no derivation from the counter to that capacity is in the sources. One fact is named on one attribute. `source status` is `defined` when a catalog element is named, and `no source` when none is. Whether a driver constructs the fact is not visible from these sources.

Mandatory column, for device types of this group only:

- `PS`: `go-fabric@v0.22.2:device/power_source_gen.go` sets the PowerSource cluster `Mandatory: true`, and this element's conformance text is `M`.
- `BS-el`: `go-fabric@v0.22.2:parity/schema.json` BatteryStorage `effective.requirements` sets this element's own conformance text to `M` on a composed PowerSource. The device file's `Servers` do not include that cluster.
- `SP-el`: the same for SolarPower, which sets feature `WIRED` to `M` on the composed PowerSource.
- `—`: not mandatory under those declarations.

A feature set to `M` by a device type is not treated as making every `ConfName` element of that feature mandatory. The generated files state both texts and do not evaluate that implication. See Uncertainty.

Catalog lines are `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`. Target lines are `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`. Every catalog fact named below has disposition `unknown` and reason `matter.unmapped.v1` with an empty target object, unless a cell says otherwise.

## 2. Device types

The device file `Servers` slice is what that file declares. `schema.json` `deviceTypes[].requirements` and `effective.requirements` are a second list. For these three types the two lists are not the same set. Decimal ids in `schema.json` match the hex ids in the device files (`17` = `0x0011`, `23` = `0x0017`, `24` = `0x0018`).

Clusters other than PowerSource `0x002F` and PowerSourceConfiguration `0x002E` are named here when a device type requires them. Their elements are not rows in section 3.

### PowerSource

- File: `go-fabric@v0.22.2:device/power_source_gen.go` lines 13–35.
- Id `0x0011`, revision 1, classification `utility`, composition `schema.CompositionTree`. The `Type` literal has no `Base` field and no `Conditions` field.
- Servers the file declares:
  - PowerSource `0x002F`, conformance `M`, `Mandatory: true`.
- `schema.json` device type id 17, name `PowerSource`, classification `utility`, revision 1 (lines 521–584). Requirements: Descriptor id 29, `serverCluster`, no `conformance` key; PowerSource id 47, `serverCluster`, `M`. `effective.conditions` is empty. `effective` does not add a feature or attribute conformance on the PowerSource cluster. The file's `Servers` omit Descriptor.

### SolarPower

- File: `go-fabric@v0.22.2:device/solar_power_gen.go` lines 13–34.
- Id `0x0017`, revision 1, classification `simple`, composition tree. No `Base`. No `Conditions`.
- Servers the file declares:
  - Identify `0x0003`, conformance `O`, `Mandatory` unset. Identify is outside this cluster group.
- `schema.json` device type id 23, name `SolarPower`, classification `simple`, revision 1 (lines 2182–2536). Requirements:
  - Identify id 3, `serverCluster`, `O`.
  - PowerSource id 17, `deviceType`, `M`.
  - Descriptor id 29, `serverCluster`, no `conformance` key.
  - TemperatureSensor id 770, `deviceType`, `O`.
  - DeviceEnergyManagement id 1293, `deviceType`, `desc`.
  - ElectricalSensor id 1296, `deviceType`, `M`.
- `effective` (same object): PowerSource constraint `min 1`, and on its PowerSource cluster (id 47) feature `WIRED` bit 0 conformance `M` (lines 2286–2309). ElectricalSensor constraint `min 1`; on ElectricalPowerMeasurement, attributes `Voltage` and `ActiveCurrent` conformance `M`; on ElectricalEnergyMeasurement, feature `EXPE` bit 1 conformance `M` (lines 2458–2531). DeviceEnergyManagement cluster feature `PA` bit 0 conformance `M` (lines 2396–2419). Those clusters are outside this group. The file's `Servers` omit Descriptor and every device type.

### BatteryStorage

- File: `go-fabric@v0.22.2:device/battery_storage_gen.go` lines 13–34.
- Id `0x0018`, revision 2, classification `simple`, composition tree. No `Base`. No `Conditions`.
- Servers the file declares:
  - Identify `0x0003`, conformance `O`, `Mandatory` unset. Identify is outside this cluster group.
- `schema.json` device type id 24, name `BatteryStorage`, classification `simple`, revision 2 (lines 2538–3260). Requirements:
  - Identify id 3, `serverCluster`, `O`.
  - PowerSource id 17, `deviceType`, `M`.
  - SolarPower id 23, `deviceType`, `O`.
  - Descriptor id 29, `serverCluster`, no `conformance` key.
  - TemperatureSensor id 770, `deviceType`, `O`.
  - DeviceEnergyManagement id 1293, `deviceType`, `M`.
  - ElectricalSensor id 1296, `deviceType`, `M`.
- `effective` splits the mandatory device types into instances:
  - ElectricalSensor instance 1, constraint text `min 2`: ElectricalPowerMeasurement feature `ALTC` bit 1 `M`, attributes `Voltage` and `ActiveCurrent` `M`; ElectricalEnergyMeasurement feature `EXPE` bit 1 `M` (lines 2631–2738).
  - ElectricalSensor instance 2, same `min 2`: ElectricalPowerMeasurement feature `DIRC` bit 0 `M`, attributes `Voltage` and `ActiveCurrent` `M`; ElectricalEnergyMeasurement feature `EXPE` `M` (lines 2768–2875).
  - PowerSource instance 1, constraint text `min 2`: PowerSource cluster feature `WIRED` bit 0 conformance `M` (lines 2904–2972). No wired attribute is restated.
  - PowerSource instance 2, same `min 2`: feature `BAT` bit 1 `M`; attributes `BatVoltage` id 11, `BatPercentRemaining` id 12, `BatTimeRemaining` id 13, `ActiveBatFaults` id 18, `BatCapacity` id 24, `BatTimeToFullCharge` id 27, `BatChargingCurrent` id 29, `ActiveBatChargeFaults` id 30, each conformance `M` (lines 2976–3155). Feature `RECHG` is not in that list.
  - DeviceEnergyManagement cluster feature `PA` bit 0 `M` (lines 3231–3256).
  - SolarPower conformance `O` with no nested requirements in this object (lines 3160–3173).
- The file's `Servers` omit Descriptor and every device type.

PowerSourceConfiguration `0x002E` is on none of these three `Servers` slices and on none of these three `schema.json` requirement lists. Device type BridgedNode id 19, outside this group, lists it as `serverCluster` conformance `BridgedPowerSourceInfo, D` (schema lines 689–693 and 751–773).

## 3. Clusters

Locator prefix for a cluster is its `definition_gen.go` unless a cell names another file.

### PowerSource

Cluster id `0x002F` (47), name `PowerSource`, revision 3 (lines 22–26). `Definition` (lines 609–878) has `Features`, `Attributes`, and `Events`. It has no `Commands` key.

Feature bits (lines 611–616), separate from global `AttrFeatureMap` `0xFFFC`:

- `WIRED`, title `Wired`, bit 0, text `O.a`, op `ConfChoice`, `Choice` name `a`, `Num` 1, `OrMore` false, `OrLess` false, `Args` one `ConfOptional`.
- `BAT`, title `Battery`, bit 1, the same `Choice` `a`.
- `RECHG`, title `Rechargeable`, bit 2, text `[BAT]`, op `ConfOptionalIf`, arg `ConfName` `BAT`.
- `REPLC`, title `Replaceable`, bit 3, text `[BAT]`, same op and arg.

`schema.json` feature `WIRED` (lines 31722–31741) has conformance text `O.a` and ast `choice` with `name` `a`, `expr` type `O`, `num` 1. The ast object in that snippet has no `orMore` key. `BAT` is the same shape at bit 1 (lines 31743–31762). `RECHG` and `REPLC` texts are `[BAT]` (lines 31765–31789).

Enum values below are the `EnumValue` `Name` and `Value`. Every one of them has conformance text `M`.

PowerSourceStatusEnum (enum8, lines 483–488): `Unspecified` 0, `Active` 1, `Standby` 2, `Unavailable` 3.

WiredCurrentTypeEnum (enum8, lines 504–507): `Ac` 0, `Dc` 1.

WiredFaultEnum (enum8, lines 524–528): `Unspecified` 0, `OverVoltage` 1, `UnderVoltage` 2.

BatChargeLevelEnum (enum8, lines 217–221): `Ok` 0, `Warning` 1, `Critical` 2.

BatReplaceabilityEnum (enum8, lines 460–465): `Unspecified` 0, `NotReplaceable` 1, `UserReplaceable` 2, `FactoryReplaceable` 3.

BatFaultEnum (enum8, lines 438–442): `Unspecified` 0, `OverTemp` 1, `UnderTemp` 2.

BatChargeStateEnum (enum8, lines 239–244): `Unknown` 0, `IsCharging` 1, `IsAtFullCharge` 2, `IsNotCharging` 3.

BatChargeFaultEnum (enum8, lines 188–199): `Unspecified` 0, `AmbientTooHot` 1, `AmbientTooCold` 2, `BatteryTooHot` 3, `BatteryTooCold` 4, `BatteryAbsent` 5, `BatteryOverVoltage` 6, `BatteryUnderVoltage` 7, `ChargerOverVoltage` 8, `ChargerUnderVoltage` 9, `SafetyTimeout` 10.

BatApprovedChemistryEnum (enum16, lines 129–163): `Unspecified` 0, `Alkaline` 1, `LithiumCarbonFluoride` 2, `LithiumChromiumOxide` 3, `LithiumCopperOxide` 4, `LithiumIronDisulfide` 5, `LithiumManganeseDioxide` 6, `LithiumThionylChloride` 7, `Magnesium` 8, `MercuryOxide` 9, `NickelOxyhydride` 10, `SilverOxide` 11, `ZincAir` 12, `ZincCarbon` 13, `ZincChloride` 14, `ZincManganeseDioxide` 15, `LeadAcid` 16, `LithiumCobaltOxide` 17, `LithiumIon` 18, `LithiumIonPolymer` 19, `LithiumIronPhosphate` 20, `LithiumSulfur` 21, `LithiumTitanate` 22, `NickelCadmium` 23, `NickelHydrogen` 24, `NickelIron` 25, `NickelMetalHydride` 26, `NickelZinc` 27, `SilverZinc` 28, `SodiumIon` 29, `SodiumSulfur` 30, `ZincBromide` 31, `ZincCerium` 32.

BatCommonDesignationEnum (enum16, lines 339–421): `Unspecified` 0, `Aaa` 1, `Aa` 2, `C` 3, `D` 4, `4V5` 5, `6V0` 6, `9V0` 7, `12Aa` 8, `Aaaa` 9, `A` 10, `B` 11, `F` 12, `N` 13, `No6` 14, `SubC` 15, `A23` 16, `A27` 17, `Ba5800` 18, `Duplex` 19, `4Sr44` 20, `523` 21, `531` 22, `15V0` 23, `22V5` 24, `30V0` 25, `45V0` 26, `67V5` 27, `J` 28, `Cr123A` 29, `Cr2` 30, `2Cr5` 31, `CrP2` 32, `CrV3` 33, `Sr41` 34, `Sr43` 35, `Sr44` 36, `Sr45` 37, `Sr48` 38, `Sr54` 39, `Sr55` 40, `Sr57` 41, `Sr58` 42, `Sr59` 43, `Sr60` 44, `Sr63` 45, `Sr64` 46, `Sr65` 47, `Sr66` 48, `Sr67` 49, `Sr68` 50, `Sr69` 51, `Sr516` 52, `Sr731` 53, `Sr712` 54, `Lr932` 55, `A5` 56, `A10` 57, `A13` 58, `A312` 59, `A675` 60, `Ac41E` 61, `10180` 62, `10280` 63, `10440` 64, `14250` 65, `14430` 66, `14500` 67, `14650` 68, `15270` 69, `16340` 70, `Rcr123A` 71, `17500` 72, `17670` 73, `18350` 74, `18500` 75, `18650` 76, `19670` 77, `25500` 78, `26650` 79, `32600` 80.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Status | attribute | 0x0000 | PowerSourceStatusEnum enum8 (values above); constraint text `desc`; catalog canonical unit `storage.status.operating` none, `pv.status.operating` none, `pv.status.fault` none, `pv.status.derating` none | M | PS | `storage.status.operating` candidate; `pv.status.operating` candidate | present | unknown / `matter.unmapped.v1` (target lines 166, 126) | defined | symbol versus enum; literals of either symbol are not in the element record or the pack-metadata field; subjects are `resource.battery_pack` and `resource.inverter`; no unit on either side | lines 618–624; catalog lines 288, 234. Also required on each composed PowerSource: BatteryStorage and SolarPower schema set that device type to `M` (BatteryStorage `min 2`, SolarPower `min 1`). prior accounting also names absent `equipment.power.source_status` (a prior proposal) and present `pv.status.fault`, `pv.status.derating`, which are not feeds in this table |
| Order | attribute | 0x0001 | uint8; NonVolatile; no constraint key | M | PS | none in catalog ( `equipment.power.source_order`) | absent | no row | no source | no catalog element; no range on the attribute | lines 625–631. Same composed-PowerSource note as Status |
| Description | attribute | 0x0002 | string; Fixed; constraint `max 60` | M | PS | none in catalog ( `equipment.power.source_description`) | absent | no row | no source | no catalog element; length max 60 | lines 632–639. Same composed-PowerSource note as Status |
| WiredAssessedInputVoltage | attribute | 0x0003 | uint32; no unit in the type name; Nullable; ChangesOmitted; no constraint key | `[WIRED]` | — | none in catalog ( `equipment.power.wired_input_voltage`) | absent | no row | no source | no catalog element; nullable; unit not declared | lines 640–646. SolarPower and BatteryStorage instance 1 set feature `WIRED` to `M` and do not restate this attribute |
| WiredAssessedInputFrequency | attribute | 0x0004 | uint16; no unit in the type name; Nullable; ChangesOmitted; no constraint key | `[WIRED]` | — | none in catalog ( `equipment.power.wired_input_frequency`) | absent | no row | no source | no catalog element; nullable; unit not declared | lines 647–653 |
| WiredCurrentType | attribute | 0x0005 | WiredCurrentTypeEnum enum8: `Ac` 0, `Dc` 1; Fixed; constraint `desc` | `WIRED` (`ConfName`, not optional-if) | — | none in catalog ( `equipment.power.wired_current_type`) | absent | no row | no source | no catalog element; ac/dc enum versus no catalog current-type fact | lines 654–661 |
| WiredAssessedCurrent | attribute | 0x0006 | uint32; no unit in the type name; Nullable; ChangesOmitted; no constraint key; catalog canonical unit `storage.pack.current` `unit.ampere` | `[WIRED]` | — | none in catalog ( `equipment.power.wired_current`) | absent | no row | no source | no catalog element; nullable; unit not declared | lines 662–668. `storage.pack.current` is named on BatChargingCurrent, not here |
| WiredNominalVoltage | attribute | 0x0007 | uint32; no unit in the type name; Fixed; no constraint key | `[WIRED]` | — | none in catalog ( `equipment.power.wired_nominal_voltage`) | absent | no row | no source | no catalog element; unit not declared | lines 669–675 |
| WiredMaximumCurrent | attribute | 0x0008 | uint32; no unit in the type name; Fixed; no constraint key | `[WIRED]` | — | none in catalog ( `equipment.power.wired_maximum_current`) | absent | no row | no source | no catalog element; unit not declared | lines 676–682 |
| WiredPresent | attribute | 0x0009 | bool; no quality key | `[WIRED]` | — | none in catalog ( `equipment.power.wired_present`) | absent | no row | no source | no catalog element | lines 683–688 |
| ActiveWiredFaults | attribute | 0x000A | list of WiredFaultEnum; constraint `max 8`; no quality key; catalog canonical unit `pv.status.fault` none | `[WIRED]` | — | none in catalog ( `equipment.power.wired_faults`) | absent | no row | no source | no catalog element; list versus a single symbol; enum is Unspecified, OverVoltage, UnderVoltage | lines 689–695. `pv.status.fault` is not a feed; see section 5 |
| BatVoltage | attribute | 0x000B | uint32; no unit in the type name; Nullable; ChangesOmitted; no constraint key; catalog canonical unit `storage.pack.voltage` `unit.volt` | `[BAT]` | BS-el | `storage.pack.voltage` partial | present | unknown / `matter.unmapped.v1` (target line 148) | defined | `unit.volt` versus uint32 with no unit and no conversion row; nullable and no range versus no numeric range on the catalog element; subject `resource.battery_pack` versus one cluster value; cell voltage facts are not this feed | lines 696–702; catalog line 265. prior accounting also names absent `equipment.power.battery_voltage` (a prior proposal) |
| BatPercentRemaining | attribute | 0x000C | uint8; no unit in the type name; Nullable; Quieter; constraint `max 200` (no minimum in the constraint); catalog canonical unit `storage.state.soc` `unit.ratio`, `storage.state.soh` `unit.ratio` | `[BAT]` | BS-el | `storage.state.soc` partial | present | unknown / `matter.unmapped.v1` (target line 162) | defined | `unit.ratio` versus uint8 `max 200` with no scale declared; nullable; no minimum in the constraint text; subject `resource.battery_pack` | lines 703–710; catalog line 284. prior accounting also names absent `equipment.power.battery_charge_ratio` (a prior proposal). `storage.state.soh` is not this feed |
| BatTimeRemaining | attribute | 0x000D | uint32; no unit in the type name; Nullable; Quieter; no constraint key | `[BAT]` | BS-el | none in catalog ( `equipment.power.battery_time_remaining`, `storage.state.time_remaining`) | absent | no row | no source | no catalog element; nullable; unit not declared | lines 711–717 |
| BatChargeLevel | attribute | 0x000E | BatChargeLevelEnum enum8: `Ok` 0, `Warning` 1, `Critical` 2; constraint `desc`; catalog canonical unit `storage.status.warning` none, `storage.status.alarm` none | `BAT` (`ConfName`) | — | `storage.status.warning` candidate; `storage.status.alarm` candidate | present | unknown / `matter.unmapped.v1` (target lines 168, 164) | defined | one symbol each versus an enum; symbol literals are not in the element records; subjects are `resource.battery_pack` | lines 718–724; catalog lines 290, 286. Not `BS-el`: the BatteryStorage element list does not restate this attribute. prior accounting names absent `equipment.power.battery_charge_level` and `storage.status.charge_level` (a prior proposal, a prior proposal) |
| BatReplacementNeeded | attribute | 0x000F | bool; no quality key | `BAT` (`ConfName`) | — | none in catalog ( `equipment.power.battery_replacement_needed`, `storage.status.replacement_needed`) | absent | no row | no source | no catalog element | lines 725–730 |
| BatReplaceability | attribute | 0x0010 | BatReplaceabilityEnum enum8 (values above); Fixed; no constraint key | `BAT` (`ConfName`) | — | none in catalog ( `equipment.power.battery_replaceability`) | absent | no row | no source | no catalog element | lines 731–737 |
| BatPresent | attribute | 0x0011 | bool; no quality key | `[BAT]` | — | none in catalog ( `equipment.power.battery_present`) | absent | no row | no source | no catalog element | lines 738–743 |
| ActiveBatFaults | attribute | 0x0012 | list of BatFaultEnum; constraint `max 8`; catalog canonical unit `storage.status.protection` none | `[BAT]` | BS-el | `storage.status.protection` candidate | present | unknown / `matter.unmapped.v1` (target line 167) | defined | one symbol versus a list of BatFaultEnum (`Unspecified`, `OverTemp`, `UnderTemp`); symbol literals are not in the element record; subject `resource.battery_pack` | lines 744–750; catalog line 289. prior accounting names absent `equipment.power.battery_faults` and `storage.status.faults` (a prior proposal, a prior proposal) |
| BatReplacementDescription | attribute | 0x0013 | string; Fixed; constraint `max 60` | `REPLC` (`ConfName`) | — | none in catalog ( `equipment.power.battery_replacement_description`) | absent | no row | no source | no catalog element; length max 60 | lines 751–758 |
| BatCommonDesignation | attribute | 0x0014 | BatCommonDesignationEnum enum16 (81 values above); Fixed; constraint `desc` | `[REPLC]` | — | none in catalog ( `equipment.power.battery_common_designation`) | absent | no row | no source | no catalog element; enum of 81 designation literals | lines 759–766 |
| BatAnsiDesignation | attribute | 0x0015 | string; Fixed; constraint `max 20` | `[REPLC]` | — | none in catalog ( `equipment.power.battery_ansi_designation`) | absent | no row | no source | no catalog element; length max 20 | lines 767–774 |
| BatIecDesignation | attribute | 0x0016 | string; Fixed; constraint `max 20` | `[REPLC]` | — | none in catalog ( `equipment.power.battery_iec_designation`) | absent | no row | no source | no catalog element; length max 20 | lines 775–782 |
| BatApprovedChemistry | attribute | 0x0017 | BatApprovedChemistryEnum enum16 (33 values above); Fixed; constraint `desc` | `[REPLC]` | — | none in catalog ( `equipment.power.battery_chemistry`) | absent | no row | no source | no catalog element; chemistry enum versus no catalog chemistry fact | lines 783–790 |
| BatCapacity | attribute | 0x0018 | uint32; no unit in the type name; Fixed; no constraint key; catalog canonical unit `storage.capacity.charge` `unit.ampere_hour`, `storage.capacity.discharge` `unit.ampere_hour` | `[REPLC \| RECHG]` (op `ConfOptionalIf` of `ConfOr` of names `REPLC` and `RECHG`) | BS-el | `storage.capacity.charge` candidate; `storage.capacity.discharge` candidate | present | unknown / `matter.unmapped.v1` (target lines 133, 134) | defined | `unit.ampere_hour` versus uint32 with no unit and no conversion row; the two facts are cumulative lifetime counters, measurement point `pack_terminals_lifetime_counter`, in `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/mappings/growatt-bms-rs485-v202-storage-v1.json` (sources `cumulative_charge_amp_hours` and `cumulative_discharge_amp_hours`; counter continuity, reset and wrap stay native evidence) and `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/mappings/huawei-luna2000-storage-v1.md` states they are cumulative throughput and not a rated capacity; BatCapacity is Fixed and does not rise across cycles; no derivation from those counters to a fixed capacity is in the sources; two `non_negative` pack facts versus one attribute; no range; which of the two facts would be the attribute is not declared | lines 791–797; catalog lines 241, 242. Joule energy facts are not feeds. prior accounting names absent `equipment.power.battery_capacity`, `storage.capacity.full_charge`, `storage.capacity.remaining` (a prior proposal, a prior proposal) and does not name the two present capacity ids |
| BatQuantity | attribute | 0x0019 | uint8; Fixed; no constraint key | `REPLC` (`ConfName`) | — | none in catalog ( `equipment.power.battery_quantity`) | absent | no row | no source | no catalog element | lines 798–804 |
| BatChargeState | attribute | 0x001A | BatChargeStateEnum enum8 (values above); constraint `desc`; catalog canonical unit `storage.status.operating` none, `storage.status.alarm` none, `storage.status.protection` none, `storage.status.warning` none | `RECHG` (`ConfName`) | — | none in catalog ( `equipment.power.battery_charge_state`, `storage.status.charge_direction`) | absent | no row | no source | no catalog element for charge state; `storage.status.operating` is named on Status, not here | lines 805–811. Not `BS-el`. The prior accounting also names `storage.status.alarm`, `storage.status.operating`, `storage.status.protection`, `storage.status.warning` on this attribute; those four are present and are named on other rows or in section 5 |
| BatTimeToFullCharge | attribute | 0x001B | uint32; no unit in the type name; Nullable; Quieter; no constraint key | `[RECHG]` | BS-el | none in catalog ( `equipment.power.battery_time_to_full`, `storage.state.time_to_full`) | absent | no row | no source | no catalog element; nullable; unit not declared | lines 812–818. BatteryStorage sets this attribute to `M` and does not set feature `RECHG` to `M` |
| BatFunctionalWhileCharging | attribute | 0x001C | bool; no quality key | `RECHG` (`ConfName`) | — | none in catalog ( `equipment.power.battery_functional_while_charging`) | absent | no row | no source | no catalog element | lines 819–824 |
| BatChargingCurrent | attribute | 0x001D | uint32; no unit in the type name; Nullable; ChangesOmitted; no constraint key; catalog canonical unit `storage.pack.current` `unit.ampere` | `[RECHG]` | BS-el | `storage.pack.current` partial | present | unknown / `matter.unmapped.v1` (target line 146) | defined | `unit.ampere` versus uint32 with no unit and no conversion row; catalog direction `signed` with `sign_reference` `native_convention` versus an unsigned type; nullable; no range; subject `resource.battery_pack`; the attribute name is charging current and the fact is pack current | lines 825–831; catalog line 263. prior accounting also names absent `equipment.power.battery_charging_current` (a prior proposal) |
| ActiveBatChargeFaults | attribute | 0x001E | list of BatChargeFaultEnum; constraint `max 16`; catalog canonical unit `storage.status.protection` none | `[RECHG]` | BS-el | none in catalog ( `equipment.power.battery_charge_faults`, `storage.status.charge_faults`) | absent | no row | no source | no catalog element; list of 11 charge-fault literals; `storage.status.protection` is named on ActiveBatFaults | lines 832–838 |
| EndpointList | attribute | 0x001F | list of `endpoint-no` uint16; no constraint key; no quality key | M | PS | none in catalog | absent | no row | no source | no catalog element whose record is an endpoint number; relation records are not this list (section 5) | lines 839–844. Same composed-PowerSource note as Status. Target `non_claims` includes `endpoint_allocation`. prior accounting status for this attribute is absent, reason text about derivation from relations, no SemReg id |
| WIRED | feature | bit 0 | FeatureMap bit `1 << 0`, title `Wired` | `O.a` (Choice `a`, Num 1, OrMore false, OrLess false) | SP-el, BS-el | none in catalog | absent | no row | no source | no feature element. SolarPower sets it `M` on the composed PowerSource. BatteryStorage instance 1 sets the same bit `M` | lines 612 and 77–78; schema lines 2296–2309 and 2957–2972 |
| BAT | feature | bit 1 | title `Battery` | `O.a` (same Choice `a`) | BS-el | none in catalog | absent | no row | no source | no feature element | lines 613 and 79; schema lines 3027–3043 |
| RECHG | feature | bit 2 | title `Rechargeable` | `[BAT]` | — | none in catalog | absent | no row | no source | no feature element; BatteryStorage sets several `[RECHG]` attributes to `M` and does not set this bit | lines 614 and 80 |
| REPLC | feature | bit 3 | title `Replaceable` | `[BAT]` | — | none in catalog | absent | no row | no source | no feature element | lines 615 and 81 |
| WiredFaultChange | event | 0x00 | priority info | `[WIRED]` | — | none in catalog ( `equipment.event.wired_fault_change`) | absent | no row | no source | no catalog event | lines 846–856 |
| WiredFaultChange.Current | event field | 0 | list of WiredFaultEnum; constraint `max 8`; `EmptyListDefault`; decoder `DecodeListIn` 0..8 | M | — | none in catalog | absent | no row | no source | field conformance `M` is inside the event; decoder minimum 0 is not in the constraint text, which is `max 8` | lines 852 and 546–547 |
| WiredFaultChange.Previous | event field | 1 | list of WiredFaultEnum; constraint `max 8`; `EmptyListDefault`; decoder 0..8 | M | — | none in catalog | absent | no row | no source | same decoder versus constraint gap | lines 853 and 548 |
| BatFaultChange | event | 0x01 | priority info | `[BAT]` | — | none in catalog ( `equipment.event.battery_fault_change`, `storage.event.fault_change`) | absent | no row | no source | no catalog event | lines 857–866 |
| BatFaultChange.Current | event field | 0 | list of BatFaultEnum; constraint `max 8`; `EmptyListDefault`; decoder 0..8 | M | — | none in catalog | absent | no row | no source | same shape as WiredFaultChange.Current | lines 862 and 569 |
| BatFaultChange.Previous | event field | 1 | list of BatFaultEnum; constraint `max 8`; `EmptyListDefault`; decoder 0..8 | M | — | none in catalog | absent | no row | no source | same decoder versus constraint gap | lines 863 and 570 |
| BatChargeFaultChange | event | 0x02 | priority info | `[RECHG]` | — | none in catalog ( `equipment.event.battery_charge_fault_change`, `storage.event.charge_fault_change`) | absent | no row | no source | no catalog event | lines 867–876 |
| BatChargeFaultChange.Current | event field | 0 | list of BatChargeFaultEnum; constraint `max 16`; `EmptyListDefault`; decoder 0..16 | M | — | none in catalog | absent | no row | no source | decoder minimum 0 is not in the constraint text `max 16` | lines 872 and 591 |
| BatChargeFaultChange.Previous | event field | 1 | list of BatChargeFaultEnum; constraint `max 16`; `EmptyListDefault`; decoder 0..16 | M | — | none in catalog | absent | no row | no source | same decoder versus constraint gap | lines 873 and 592 |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | `Definition` has no `Commands` key (lines 609–878) |

### PowerSourceConfiguration

Cluster id `0x002E` (46), name `PowerSourceConfiguration`, revision 1 (`definition_gen.go` lines 19–23). `Definition` (lines 36–48) has one attribute. It has no `Features` key, no `Events` key, and no `Commands` key. The package comment states revision 1 from the matter.js model at `a commit id recorded in the cited file` (Matter 1.6.1).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sources | attribute | 0x0000 | list of `endpoint-no` uint16; NonVolatile; constraint `max 6` | M | — | none in catalog | absent | no row | no source | no catalog element; list max 6 of endpoint numbers; not mounted by a device type of this group | lines 39–46. Cluster conformance `M` would apply on a server that mounts the cluster. BridgedNode, outside this group, is the schema device type that lists it |
| (features) | feature | — | none declared | — | — | — | — | — | — | — | no `Features` key |
| (events) | event | — | none declared | — | — | — | — | — | — | — | no `Events` key |
| (commands) | command | — | none declared | — | — | — | — | — | — | — | no `Commands` key |

## 4. Mandatory elements without a source

Included: `PS`, `BS-el`, and `SP-el` from the column rule, where the feed cell names no catalog element. `BatCapacity` is `BS-el` and is included: its feed cell names `storage.capacity.charge` and `storage.capacity.discharge` only as candidates, and those facts are cumulative lifetime counters, not a fixed capacity. `Status`, `BatVoltage`, `BatPercentRemaining`, `BatChargeLevel`, `ActiveBatFaults`, and `BatChargingCurrent` have a catalog element and are not in this list. `BatChargeLevel` is not in the mandatory column.

`Order`, `Description`, and `EndpointList` are `PS`. BatteryStorage and SolarPower require device type PowerSource with conformance `M` (BatteryStorage effective constraint `min 2`, SolarPower `min 1`), and the cluster text of these three attributes is `M`, so the same three are mandatory on those composed PowerSource endpoints. The device files do not list the cluster.

| element | cluster | why it is mandatory here | catalog |
|---|---|---|---|
| Order | PowerSource 0x0001 | `PS`; also each composed PowerSource required by BatteryStorage and SolarPower | none (`equipment.power.source_order` absent) |
| Description | PowerSource 0x0002 | `PS`; same composed endpoints | none (`equipment.power.source_description` absent) |
| EndpointList | PowerSource 0x001F | `PS`; same composed endpoints | none |
| BatTimeRemaining | PowerSource 0x000D | `BS-el` (BatteryStorage PowerSource instance 2) | none (`storage.state.time_remaining` absent) |
| BatTimeToFullCharge | PowerSource 0x001B | `BS-el` (same instance) | none (`storage.state.time_to_full` absent) |
| ActiveBatChargeFaults | PowerSource 0x001E | `BS-el` (same instance) | none (`storage.status.charge_faults` absent) |
| BatCapacity | PowerSource 0x0018 | `BS-el` (BatteryStorage PowerSource instance 2). The named facts are cumulative lifetime counters and do not fill this Fixed attribute | `storage.capacity.charge` and `storage.capacity.discharge` are present and are not a fixed capacity |
| WIRED | PowerSource feature bit 0 | `SP-el` (SolarPower) and `BS-el` (BatteryStorage instance 1) | none |
| BAT | PowerSource feature bit 1 | `BS-el` (BatteryStorage instance 2) | none |

PowerSourceConfiguration `Sources` is cluster conformance `M` and is not mandatory for a device type of this group.

Attributes whose cluster text is `M` only inside an event (`Current`, `Previous`) are not in this list. The events themselves are not `M` for a device type of this group.

## 5. Catalog elements of this domain without a Matter element

Domain used here: power-source status, wired-supply assessment, battery charge, replacement, chemistry, and designation on PowerSource, and the endpoint list on PowerSource and PowerSourceConfiguration. Electrical measurement, electrical energy, and device energy management are required by SolarPower and BatteryStorage in `schema.json` and are outside these two clusters. Facts whose quantity family is voltage, current, power, or energy of a phase, inverter, or dc input are not listed as "without a Matter element". Their clusters are not this group. `storage.pack.power` (`unit.watt`, catalog line 264, target line 147), `storage.limit.charge_power` and `storage.limit.discharge_power` (`unit.watt`, catalog lines 259–260, target lines 142–143), and `pv.energy.generated`, `pv.energy.yield_day`, `pv.energy.yield_month`, `pv.energy.yield_year` (`pv.energy.generated` is `unit.joule`; target lines 104–107) are in that excluded set. `pv.energy.consumed` is not in the catalog.

These catalog elements are in the battery and source domain and have no attribute in these two clusters:

| element | kind and unit | why it is not a feed above | catalog line | target line |
|---|---|---|---|---|
| `storage.state.soh` | quantity, `unit.ratio`, subject `resource.battery_pack` | no state-of-health attribute; not BatPercentRemaining | 285 | 163 |
| `storage.energy.nominal_capacity` | quantity, `unit.joule`, `non_negative` | joule versus BatCapacity, which is uint32 with no unit; the ampere-hour pair is named on BatCapacity only as a candidate lifetime counter, not as a fixed-capacity derivation | 256 | 139 |
| `storage.energy.usable_capacity` | quantity, `unit.joule`, `non_negative` | same | 258 | 141 |
| `storage.energy.remaining` | quantity, `unit.joule`, `non_negative` | remaining energy is not BatPercentRemaining (`unit.ratio`) and not BatTimeRemaining (no catalog time fact) | 257 | 140 |
| `storage.energy.charged` | quantity, `unit.joule`, `non_negative` | no energy-total attribute on these clusters | 254 | 137 |
| `storage.energy.discharged` | quantity, `unit.joule`, `non_negative` | same | 255 | 138 |
| `storage.cell.voltage_minimum` | quantity, `unit.volt`, subject `resource.battery_cell` | BatVoltage is one uint32; the cell fact is a different subject | 244 | 136 |
| `storage.cell.voltage_maximum` | quantity, `unit.volt`, subject `resource.battery_cell` | same | 243 | 135 |
| `storage.temperature.cell` | quantity, `unit.kelvin`, subject `resource.battery_cell` | no temperature attribute on these clusters | 291 | 169 |
| `storage.temperature.pack` | quantity, `unit.kelvin`, subject `resource.battery_pack` | same | 292 | 170 |
| `storage.status.interlock` | symbol, no canonical unit, subject `resource.storage_interface` | no interlock attribute; not named as a feed | 287 | 165; catalog canonical unit `storage.status.interlock` none |
| `pv.status.fault` | symbol, no canonical unit, subject `resource.inverter` | enum literals of WiredFaultEnum and BatFaultEnum are not in this record; not named as a feed | 233 | 125; catalog canonical unit `pv.status.fault` none |
| `pv.status.derating` | symbol, no canonical unit, subject `resource.inverter` | PowerSourceStatusEnum literals are not in this record; not named on Status | 232 | 124; catalog canonical unit `pv.status.derating` none |

Relation elements do not carry an endpoint number in the compact attributes, so they are not feeds of `EndpointList` or `Sources`. Storage relations, each `unknown` / `matter.relation_construct_not_adopted.v1`: `storage.relation.battery_pack`, `storage.relation.module_cell`, `storage.relation.pack_interface`, `storage.relation.pack_module`, `storage.relation.pack_string`, `storage.relation.system_battery` (catalog lines 271–276, target lines 149–154). PV relations with that same reason: `pv.relation.array_string`, `pv.relation.inverter_input`, `pv.relation.inverter_phase`, `pv.relation.system_inverter` (target lines 113, 115–117). `pv.relation.inverter_array` is `withheld` / `matter.power_topology_endpoint_unallocated.v1` with `cluster_id` 156 (target line 114), which is Power Topology, not cluster 47 or 46.

`storage.status.operating`, `storage.status.warning`, `storage.status.alarm`, and `storage.status.protection` are named as candidates in section 3 and are not repeated here.

## 6. Disagreements with the prior accounting

PowerSource in `a prior accounting` lines 93–135: the 32 attribute ids, the 3 event ids, the 4 feature bits, and the conformance texts match `definition_gen.go`. The `Definition` literal has no commands, and that section has no command rows. Feature rows there are `absent` with no SemReg id; the catalog has no feature element for these bits.

Claims the sources contradict, or that the sources do not contain:

- The prior accounting file has no `PowerSourceConfiguration` and no `0x002E` (search of the file). The cluster is `go-fabric@v0.22.2:cluster/spec/powersourceconfiguration/definition_gen.go`, id `0x002E`, revision 1, attribute `Sources`. The Matter intro (lines 7–8) describes a cluster-by-cluster read of every attribute, command, event, and feature. The file does not say whether the missing cluster was left out on purpose.
- Device-type stub lines 1047–1064: the SolarPower row's SemReg id is `pv.energy.consumed`, status `planned`, ticket a prior proposal. That id is absent from the catalog. The SolarPower device file declares Identify `O` only. `schema.json` declares PowerSource device type `M`, ElectricalSensor `M`, DeviceEnergyManagement `desc`, TemperatureSensor `O`, Descriptor, and Identify `O`. The stub has no BatteryStorage row and no PowerSource device-type row. Both device files and both schema device types exist (section 2).
- BatCapacity (prior accounting line 102) names `storage.capacity.full_charge` and `storage.capacity.remaining`. Both are absent. The catalog has `storage.capacity.charge` and `storage.capacity.discharge`, both `unit.ampere_hour`. The prior accounting row does not name those two ids. Its status is `planned`, which the legend (line 3) defines as added by the ticket, so the row does not say the absent ids are already in the catalog.
- Planned ids in that PowerSource table that were checked and are absent from the catalog: every `equipment.power.*` id on lines 97–128, every `equipment.event.*` id on lines 129–131, `storage.status.charge_faults`, `storage.status.faults`, `storage.status.charge_level`, `storage.status.charge_direction`, `storage.status.replacement_needed`, `storage.state.time_remaining`, `storage.state.time_to_full`, `storage.event.charge_fault_change`, `storage.event.fault_change`. That absence agrees with the job's rule for `planned` ids. It is recorded so the table in section 3 can be checked against the prior accounting. Present ids that the same table also names: `storage.pack.voltage`, `storage.pack.current`, `storage.state.soc`, `storage.status.alarm`, `storage.status.operating`, `storage.status.protection`, `storage.status.warning`, `pv.status.derating`, `pv.status.fault`, `pv.status.operating`. Their target rows are `unknown` / `matter.unmapped.v1`, so a finished target row is not in the ledger.

`a prior accounting` lines 218–235, claims the generated model or the catalog do not state:

- a prior claim calls BatTimeRemaining and BatTimeToFullCharge "seconds". Both types in `definition_gen.go` and in `schema.json` are `uint32` with no unit.
- a prior claim calls BatCapacity "mAh". The type in both files is `uint32` with no unit. The same row's catalog units match pack-metadata: `storage.capacity.charge` and `storage.capacity.discharge` are `unit.ampere_hour`; `storage.energy.nominal_capacity`, `storage.energy.usable_capacity`, and `storage.energy.remaining` are `unit.joule`.
- a prior claim says `storage.status.protection` and `storage.status.alarm` are boolean only. Both catalog attributes are `value_kind` `symbol` with no values and no boolean field. Pack-metadata fields for both have no `canonical_unit` and no value list.
- a prior claim gives `storage.status.operating` the literals active, idle, and standby. Those literals are not in the catalog element and not in the pack-metadata field.
- a prior claim puts BatChargeLevel, BatReplacementNeeded, and BatPresent on one row fed by `storage.status.warning` and `storage.status.alarm`. The two symbol facts exist. BatReplacementNeeded and BatPresent have no catalog element. The symbol records do not state replacement or presence.
- a prior claim says Status, Order, and Description are absent in SemReg. Order and Description have no catalog element. `storage.status.operating` and `pv.status.operating` are in the catalog. They are symbol facts, not a PowerSourceStatusEnum element.
- a prior claim says EndpointList is partial via relations. The relation elements in section 5 do not contain an endpoint number in the compact attributes, and no target row names cluster 47 or attribute `EndpointList`.
- a prior claim says state of health, cell voltage, and cell temperature have no Matter attribute, marked inferred. These two clusters have no such attribute. `schema.json` lists TemperatureSensor as an optional device type on BatteryStorage and on SolarPower. That device type's cluster was not read, so the claim for the whole data model is not established here.
- a prior claim (line 296) says Battery Storage revision 2 requires two Electrical Sensors, Power Source, and Device Energy Management. `schema.json` effective requirements match that: ElectricalSensor `min 2`, PowerSource `min 2`, DeviceEnergyManagement `M`. `go-fabric@v0.22.2:device/battery_storage_gen.go` declares only Identify `O`.

`a prior accounting` section 2.11 does not mention PowerSourceConfiguration.

## 7. Uncertainty

- Whether a mandatory feature forces attributes whose conformance op is `ConfName` of that feature. SolarPower and BatteryStorage instance 1 set `WIRED` to `M`. `WiredCurrentType` text is `WIRED`. BatteryStorage instance 2 sets `BAT` to `M`. `BatChargeLevel`, `BatReplacementNeeded`, and `BatReplaceability` texts are `BAT`. The element requirements do not restate those attributes. They are not marked `BS-el` or `SP-el`.
- BatteryStorage sets `BatCapacity`, `BatTimeToFullCharge`, `BatChargingCurrent`, and `ActiveBatChargeFaults` to `M` and does not set feature `RECHG` to `M`. What a server does with that combination is not in the device file or in the cluster `Definition`.
- `schema.json` choice ast for `WIRED` and `BAT` has `num` 1 and expr type `O`, and no `orMore` key in the object at lines 31730–31738. The Go `Choice` sets `OrMore` false and `OrLess` false. This accounting reports both and does not decide a third reading.
- Symbol literals for `storage.status.*` and `pv.status.*` are not in the catalog element and not in the pack-metadata field. Candidate rows are name-and-kind correspondences. The mapping onto PowerSourceStatusEnum, BatChargeLevelEnum, and BatFaultEnum is not established.
- No unit is declared for the uint32 and uint16 measure attributes. Scale, and whether a value is assessed, nominal, or instantaneous, is not in these types.
- The device-file `Servers` slices and the schema requirement lists differ for all three device types (section 2). This accounting does not establish which list a constructed endpoint mounts. `go-fabric@v0.22.2:device/device.go` was not read.
- Tag `v0.13.12`, the target `model_source` tag, was not diffed against v0.22.2. The adopted models do not include this group.
- TemperatureSensor, ElectricalPowerMeasurement, ElectricalEnergyMeasurement, and DeviceEnergyManagement were not accounted. They appear only as device-type requirements in section 2.
- Driver publication of the catalog facts is not visible from these sources.
- A byte-for-byte diff of the semreg fixture catalog against the docs-semantic catalog was not done. The grepped ids sit at the same line numbers.
