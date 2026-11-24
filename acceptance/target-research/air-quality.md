---
status: "research notes for Matter 1.6.1 air-quality clusters; no mapping is decided and no canonical target is written."
---

# Air quality, concentrations and filter monitoring

Matter 1.6.1 cluster accounting for Air quality, concentrations and filter monitoring. Identifiers, conformance, types and units are read from go-fabric@v0.22.2:parity/schema.json (revision 1.6.1, data model revision 21) and the generated cluster and device files cited below. Catalog elements are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json and semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json. Canonical units are the `canonical_unit` field of docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json. Target rows are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json and docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md. No mapping is chosen. No grade in this note is `exact`. Charge capacity stays `unit.ampere_hour` where the catalog defines it; `storage.capacity.remaining` and `storage.capacity.full_charge` are absent from the pinned catalog. A catalog canonical unit is written beside the Matter unit on each element row that names a catalog field.



Frozen SHAs named by the brief:

- docs-semantic `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`
- semreg `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:`

go-fabric module source: `go-fabric` v0.22.2 at `go-fabric v0.22.2`. Matter revision stated there: 1.6.1 (`go-fabric@v0.22.2:parity/schema.json` line 9; `go-fabric@v0.22.2:docs/reference/spec-levels.md` lines 58–60, where 1.6.1 is the last level and that line says the last level is the pin). Each cluster file header below also says the generated model is matter.js at `a commit id recorded in the cited file` (Matter 1.6.1). `spec-levels.md` line 58 names matter.js tag `v0.18.0` commit `a commit id recorded in the cited file` for level 1.6.1. This accounting does not establish that `a commit id recorded in the cited file` and `a commit id recorded in the cited file` are the same commit (see Uncertainty).

Catalog and target facts are taken from the pinned catalog and target files that name docs-semantic SHA `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`:

- `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`
- `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`

Those views are one row per element. A search of the catalog view for `thermal.air.`, `thermal.filter.`, `thermal.measurement.air_quality`, `resource.air_filter`, and the same stems in the target view, returned no element id. The only catalog hits kept for the domain check are listed in the later sections.

## Files read

- the research row QQ04.
- `go-fabric@v0.22.2:device/air_quality_sensor_gen.go`, `go-fabric@v0.22.2:device/air_purifier_gen.go`.
- `go-fabric@v0.22.2:device/smoke_co_alarm_gen.go` lines 18–61, `go-fabric@v0.22.2:device/refrigerator_gen.go` lines 16–48, `go-fabric@v0.22.2:device/room_air_conditioner_gen.go` lines 23–70, `go-fabric@v0.22.2:device/extractor_hood_gen.go` lines 16–50, for other device types that name a cluster of this group.
- `go-fabric@v0.22.2:cluster/spec/airquality/definition_gen.go` (whole file).
- `go-fabric@v0.22.2:cluster/spec/carbonmonoxideconcentrationmeasurement/definition_gen.go` (whole file).
- `go-fabric@v0.22.2:cluster/spec/hepafiltermonitoring/definition_gen.go` and `go-fabric@v0.22.2:cluster/spec/activatedcarbonfiltermonitoring/definition_gen.go` (whole files).
- go-fabric `cluster/spec/<concentration>/definition_gen.go` line 7 and the attribute-id block for each of the other nine concentration clusters (ids below). `go-fabric@v0.22.2:cluster/spec/pm25concentrationmeasurement/definition_gen.go` lines 1–40 and `go-fabric@v0.22.2:cluster/spec/radonconcentrationmeasurement/definition_gen.go` lines 100–139 were read in full slices.
- `go-fabric@v0.22.2:parity/schema.json` at the device-type and cluster objects cited per section. `go-fabric@v0.22.2:docs/reference/spec-levels.md` lines 49–60. `go-fabric@v0.22.2:parity/schema.json` line 9.
- Prior claims were checked against a prior accounting lines 181–219 and 773–991, and line 1553. a prior accounting lines 172–181 and 347.

`git -C <view> show <sha>:<path>` was not run in this session. The compact views are the frozen-SHA extracts named by the brief. See Uncertainty.

## How a row is filled

- Kind is attribute, command, struct field, or feature. Events are stated per cluster. Schema.json also lists `FeatureMap` id 65532 and `ClusterRevision` id 65533 on these clusters; `definition_gen.go` does not put them in `Attributes`. Both are rows, with the schema locator.
- Conformance text is the generated `Conformance.Text`.
- "Mandatory for which device types" means a device type whose server requirement for this cluster is `M`, and whose element conformance is `M`. An element whose own conformance is `M` on a cluster the device type marks `O` or `[Rev >= v3]` (`optionalIf`) is not treated as mandatory for that device type. The Go device struct sets `Mandatory: true` only for the `M` servers.
- Catalog status `absent` means the element id is not in `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`. Target `no row` means that id is not in `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`.
- Source status `no source` when no catalog element is a feed. Loss `no correspondence` when no catalog element matches. `none` is not used, because no row in this group has an exact catalog match.
- Access and quality letters in the generated id comments: `R` read, `V` view privilege, `X` nullable, `F` fixed, `N` non-volatile, `RW` read and write. Command `ResetCondition` declares `RW: "R"` with read privilege operate and write privilege operate.

a prior proposal and a prior proposal names below are the prior accounting's ticket column for ids that are not in the catalog. They are proposals, not catalog elements.

## Device types of this group

### AirQualitySensor

Locator: `go-fabric@v0.22.2:device/air_quality_sensor_gen.go` lines 26–29 and 42–101.

| | |
|---|---|
| id | `0x002C` (`AirQualitySensorID`) |
| revision | 1 |
| classification | `simple` |
| composition | `schema.CompositionTree` |

Server clusters as that file declares them:

| cluster | id | conformance | mandatory flag in the Go struct |
|---|---|---|---|
| Identify | `0x0003` | `M` | true |
| AirQuality | `0x005B` | `M` | true |
| TemperatureMeasurement | `0x0402` | `O` | not set |
| RelativeHumidityMeasurement | `0x0405` | `O` | not set |
| CarbonMonoxideConcentrationMeasurement | `0x040C` | `O` | not set |
| CarbonDioxideConcentrationMeasurement | `0x040D` | `O` | not set |
| NitrogenDioxideConcentrationMeasurement | `0x0413` | `O` | not set |
| OzoneConcentrationMeasurement | `0x0415` | `O` | not set |
| Pm25ConcentrationMeasurement | `0x042A` | `O` | not set |
| FormaldehydeConcentrationMeasurement | `0x042B` | `O` | not set |
| Pm1ConcentrationMeasurement | `0x042C` | `O` | not set |
| Pm10ConcentrationMeasurement | `0x042D` | `O` | not set |
| TotalVolatileOrganicCompoundsConcentrationMeasurement | `0x042E` | `O` | not set |
| RadonConcentrationMeasurement | `0x042F` | `O` | not set |

`go-fabric@v0.22.2:parity/schema.json` lines 5395–5488 name the same device type id 44, revision 1, and the same server clusters with the same conformance texts. The schema `requirements` array also has Descriptor id 29 with no `conformance` field (lines 5407–5410). The device file's `Servers` slice does not list Descriptor. Identify and TemperatureMeasurement are outside this cluster group; they are listed here because the device file declares them.

### AirPurifier

Locator: `go-fabric@v0.22.2:device/air_purifier_gen.go` lines 18–21 and 34–61.

| | |
|---|---|
| id | `0x002D` (`AirPurifierID`) |
| revision | 3 |
| classification | `simple` |
| composition | `schema.CompositionTree` |

Server clusters as that file declares them:

| cluster | id | conformance | mandatory flag in the Go struct |
|---|---|---|---|
| Identify | `0x0003` | `M` | true |
| FanControl | `0x0202` | `M` | true |
| Groups | `0x0004` | `O` | not set |
| OnOff | `0x0006` | `O` | not set |
| HepaFilterMonitoring | `0x0071` | `O` | not set |
| ActivatedCarbonFilterMonitoring | `0x0072` | `O` | not set |

`go-fabric@v0.22.2:parity/schema.json` lines 5733–5802 name device type id 45, revision 3. Beside the servers above, that `requirements` array also has:

| element | schema id | name | conformance field |
|---|---|---|---|
| serverCluster | 29 | Descriptor | absent |
| deviceType | 44 | AirQualitySensor | `O` |
| deviceType | 769 | Thermostat | `O` |
| deviceType | 770 | TemperatureSensor | `O` |
| deviceType | 775 | HumiditySensor | `O` |

The device file's `Servers` slice does not list those five. The schema `effective.requirements` also include a condition `GroupcastListenerCond`, conformance text `O`, location `Root` (lines 5834–5848). Identify, FanControl, Groups and OnOff are outside this cluster group.

## AirQuality `0x005B` revision 1

Locator: `go-fabric@v0.22.2:cluster/spec/airquality/definition_gen.go` lines 6–7, 19–23, 26–28, 36–41, 48–70, 72–90. Schema cluster object: `go-fabric@v0.22.2:parity/schema.json` lines 56749–56837 (`commands` `[]`, `events` `[]`). No `Base` field. No commands and no events in either source.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AirQuality | attribute | `0x0000` | `AirQualityEnum` enum8 | `M` | AirQualitySensor `0x002C` (cluster `M`, attribute `M`) | none in catalog (`thermal.dimension.substance`, `thermal.measurement.air_quality`) | absent | no row | no source | no correspondence | access `R` `V`; constraint text `desc`. Enum values: 0 `Unknown` `M`, 1 `Good` `M`, 2 `Fair` `FAIR`, 3 `Moderate` `MOD`, 4 `Poor` `M`, 5 `VeryPoor` `VPOOR`, 6 `ExtremelyPoor` `XPOOR` (`definition_gen.go` lines 49–70). a prior accounting lines 185–185. |
| FAIR | feature | bit 0 | bitmap bit, title `Fair` | `O` | none | none in catalog | absent | no row | no source | no correspondence | `definition_gen.go` lines 37 and 76. a prior accounting line 186 calls the bit absent and names a a prior proposal binding rule. That rule is not a catalog element. |
| MOD | feature | bit 1 | bitmap bit, title `Moderate` | `O` | none | none in catalog | absent | no row | no source | no correspondence | `definition_gen.go` lines 38 and 77. a prior accounting line 187. |
| VPOOR | feature | bit 2 | bitmap bit, title `VeryPoor` | `O` | none | none in catalog | absent | no row | no source | no correspondence | `definition_gen.go` lines 39 and 78. a prior accounting line 188. |
| XPOOR | feature | bit 3 | bitmap bit, title `ExtremelyPoor` | `O` | none | none in catalog | absent | no row | no source | no correspondence | `definition_gen.go` lines 40 and 79. a prior accounting line 189. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | AirQualitySensor `0x002C` (cluster `M`, attribute `M`) | none in catalog | absent | no row | no source | no correspondence | schema.json lines 56782–56804. access read `V`; quality fixed. Not in `definition_gen.go` `Attributes`. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | AirQualitySensor `0x002C` (cluster `M`, attribute `M`) | none in catalog | absent | no row | no source | no correspondence | schema.json lines 56805–56833. access read `V`; quality fixed; constraint `min 1`; default 1. Not in `definition_gen.go` `Attributes`. |

Device-type search: the name `AirQuality` as a server requirement occurs on AirQualitySensor (`schema.json` lines 5412–5416 and `go-fabric@v0.22.2:device/air_quality_sensor_gen.go` lines 48–52). No other `*_gen.go` server list names this cluster.

## Concentration clusters (shared shape)

Ten clusters, each revision 5, `Base: "ConcentrationMeasurement"`, matter.js `a commit id recorded in the cited file` in the file header. Each `definition_gen.go` attribute-id comment block matches `go-fabric@v0.22.2:cluster/spec/carbonmonoxideconcentrationmeasurement/definition_gen.go` lines 26–37. The full definition read for carbon monoxide (lines 132–225) is the row source for types, conformance, access, quality and constraints. Radon features at `go-fabric@v0.22.2:cluster/spec/radonconcentrationmeasurement/definition_gen.go` lines 132–139 match the carbon monoxide feature block. Schema objects are 724 lines apart and each has `"commands": []` then `"events": []`:

| cluster | id | schema cluster line | schema `commands` line |
|---|---|---|---|
| CarbonMonoxideConcentrationMeasurement | `0x040C` | 108681 | 109085 |
| CarbonDioxideConcentrationMeasurement | `0x040D` | 109405 | 109809 |
| NitrogenDioxideConcentrationMeasurement | `0x0413` | 110129 | 110533 |
| OzoneConcentrationMeasurement | `0x0415` | 110853 | 111257 |
| Pm25ConcentrationMeasurement | `0x042A` | 111577 | 111981 |
| FormaldehydeConcentrationMeasurement | `0x042B` | 112301 | 112705 |
| Pm1ConcentrationMeasurement | `0x042C` | 113025 | 113429 |
| Pm10ConcentrationMeasurement | `0x042D` | 113749 | 114153 |
| TotalVolatileOrganicCompoundsConcentrationMeasurement | `0x042E` | 114473 | 114877 |
| RadonConcentrationMeasurement | `0x042F` | 115197 | 115601 |

`events` is the next line in each of those objects (read at 109086, 109810, 111982, 115602). No command fields. No events.

Shared type facts, from `go-fabric@v0.22.2:cluster/spec/carbonmonoxideconcentrationmeasurement/definition_gen.go`:

- `single` is `spec.KindFloat32` (lines 147, 155, 163, 170, 185, 200).
- `elapsed-s` is uint, 32 bits (lines 178 and 193). Constraint text `max 604800` on both window attributes.
- Measured, peak and average values: nullable; constraint text `minMeasuredValue to maxMeasuredValue`.
- Min and max measured values: nullable and fixed. Max has constraint text `min minMeasuredValue`. Min has no constraint struct.
- Uncertainty: conformance text `[MEA]`, fixed, not nullable.
- `MeasurementUnit` and `MeasurementMedium`: fixed.
- `LevelValue`: no nullable and no fixed flag on the attribute (lines 219–224).
- `MeasurementUnitEnum` values, all conformance `MEA`: 0 `Ppm`, 1 `Ppb`, 2 `Ppt`, 3 `Mgm3`, 4 `Ugm3`, 5 `Ngm3`, 6 `Pm3`, 7 `Bqm3` (lines 107–129). The same eight values are in the carbon monoxide schema datatype (schema.json lines 109345–109397) and in `go-fabric@v0.22.2:cluster/spec/radonconcentrationmeasurement/definition_gen.go` lines 107–129. No per-cluster subset of this enum appears in these files.
- `MeasurementMediumEnum`: 0 `Air` `M`, 1 `Water` `M`, 2 `Soil` `M` (lines 86–98).
- `LevelValueEnum`: 0 `Unknown` `M`, 1 `Low` `M`, 2 `Medium` `MED`, 3 `High` `M`, 4 `Critical` `CRI` (lines 61–77).
- Features: `MEA` bit 0 `O.a+` (choice `a`, num 1, or-more); `LEV` bit 1 `O.a+` (same choice); `MED` bit 2 `[LEV]`; `CRI` bit 3 `[LEV]`; `PEA` bit 4 `[MEA]`; `AVG` bit 5 `[MEA]` (lines 136–142).
- Schema `ClusterRevision` default on the carbon monoxide object is 5 (schema.json line 109081). `FeatureMap` is id 65532, conformance `M`, the same shape as AirQuality.

Device types that name a concentration cluster:

- All ten: AirQualitySensor, conformance `O` (`go-fabric@v0.22.2:device/air_quality_sensor_gen.go` lines 61–100).
- Carbon monoxide only, also SmokeCoAlarm `0x0076` revision 2, conformance `O` (`go-fabric@v0.22.2:device/smoke_co_alarm_gen.go` lines 18–21 and 57–60; schema.json lines 8332–8384).

No device file marks any of these ten clusters `M`. `MeasurementMedium`, `FeatureMap` and `ClusterRevision` are conformance `M` inside the cluster and are not mandatory for a device type.

Catalog proposals below are the a prior accounting SemReg column (lines 773–991). Every one of those ids is absent from the catalog view.

### CarbonMonoxideConcentrationMeasurement `0x040C`

a prior accounting lines 773–793. Also optional on SmokeCoAlarm, as above.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | nullable; constraint `minMeasuredValue to maxMeasuredValue`; access `R` `V`. `definition_gen.go` lines 145–152. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | nullable, fixed. a prior accounting line 784 says absent, reason a binding derived from field bounds. No catalog element holds those bounds. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | nullable, fixed; constraint `min minMeasuredValue`. a prior accounting line 780, same derivation sentence. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | nullable; same range constraint as MeasuredValue. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | constraint `max 604800`. Not nullable in the attribute struct. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | nullable; same range constraint as MeasuredValue. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | constraint `max 604800`. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | fixed; not nullable. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | fixed. Enum 0–7 all conformance `MEA`, listed in the shared section. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | fixed. Enum `Air`/`Water`/`Soil`, each `M`. Cluster is `O` on AirQualitySensor and on SmokeCoAlarm, so the attribute is not device-mandatory. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | Enum values in the shared section. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | choice `a`, at least one, with `LEV`. a prior accounting line 791. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | same choice `a`. a prior accounting line 790. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 792. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 789. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 793. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 788. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema.json on this cluster, same ids as AirQuality lines 56782–56804. Cluster is not `M` on a device type. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | default 5 on this schema object (line 109081); constraint `min 1`; quality fixed. |

### CarbonDioxideConcentrationMeasurement `0x040D`

Header: `go-fabric@v0.22.2:cluster/spec/carbondioxideconcentrationmeasurement/definition_gen.go` line 7. Attribute-id comments lines 27–37 match carbon monoxide. Schema `commands`/`events` empty at lines 109809–109810. a prior accounting lines 795–815. Device type: AirQualitySensor `O` only.

Rows match the carbon monoxide table except the SemReg proposals on two attributes:

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 803. Shared type row. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 806, derivation sentence, no catalog bounds element. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 802. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.volume_fraction`, `thermal.dimension.statistic`) | absent | no row | no source | no correspondence | a prior accounting line 807. Both ids absent. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 808. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.volume_fraction`, `thermal.dimension.statistic`) | absent | no row | no source | no correspondence | a prior accounting line 799. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 800. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 809. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 805. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 804. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 801. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 813. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 812. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 814. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 811. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 815. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 810. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema feature map on this cluster object; cluster not `M` on a device type. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | same global shape; carbon monoxide sibling default is 5. This object's default was not read as its own line. See Uncertainty. |

### NitrogenDioxideConcentrationMeasurement `0x0413`

Header line 7 of `go-fabric@v0.22.2:cluster/spec/nitrogendioxideconcentrationmeasurement/definition_gen.go`. Schema `commands`/`events` empty at 110533. a prior accounting lines 817–837. Proposals match carbon monoxide (`thermal.air.volume_fraction` on measured, peak, average and unit). Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 825. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 828. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 824. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 829. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 830. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 821. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 822. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 831. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 827. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 826. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 823. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 835. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 834. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 836. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 833. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 837. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 832. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

### OzoneConcentrationMeasurement `0x0415`

Header line 7 of `go-fabric@v0.22.2:cluster/spec/ozoneconcentrationmeasurement/definition_gen.go`. Schema `commands`/`events` empty at 111257. a prior accounting lines 839–859. Proposals match carbon monoxide. Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 847. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 850. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 846. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 851. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 852. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 843. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 844. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 853. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 849. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 848. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 845. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 857. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 856. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 858. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 855. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 859. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 854. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

### Pm25ConcentrationMeasurement `0x042A`

Header: `go-fabric@v0.22.2:cluster/spec/pm25concentrationmeasurement/definition_gen.go` lines 6–7 and 19–37. Schema `commands`/`events` empty at 111981–111982. a prior accounting lines 861–881. Value proposals use `thermal.air.mass_concentration`. Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | id comment line 27: `single, MEA, R V, X`. a prior accounting line 869. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | id comment line 28: `X F`. a prior accounting line 872. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | id comment line 29. a prior accounting line 868. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 873. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 874. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 865. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 866. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 875. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 871. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 870. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 867. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 879. `Base` line 135. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 878. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 880. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 877. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 881. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 876. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

### FormaldehydeConcentrationMeasurement `0x042B`

Header line 7 of `go-fabric@v0.22.2:cluster/spec/formaldehydeconcentrationmeasurement/definition_gen.go`. Schema `commands`/`events` empty at 112705. a prior accounting lines 883–903. Proposals match PM2.5 (`thermal.air.mass_concentration`). Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 891. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 894. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 890. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 895. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 896. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 887. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 888. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 897. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 893. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 892. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 889. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 901. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 900. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 902. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 899. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 903. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 898. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

### Pm1ConcentrationMeasurement `0x042C`

Header line 7 of `go-fabric@v0.22.2:cluster/spec/pm1concentrationmeasurement/definition_gen.go`. Schema `commands`/`events` empty at 113429. a prior accounting lines 905–925. Proposals match PM2.5. Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 913. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 916. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 912. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 917. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 918. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 909. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 910. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 919. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 915. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 914. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 911. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 923. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 922. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 924. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 921. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 925. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 920. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

### Pm10ConcentrationMeasurement `0x042D`

Header line 7 of `go-fabric@v0.22.2:cluster/spec/pm10concentrationmeasurement/definition_gen.go`. Schema `commands`/`events` empty at 114153. a prior accounting lines 927–947. Proposals match PM2.5. Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 935. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 938. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 934. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 939. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 940. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 931. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 932. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 941. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.mass_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 937. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 936. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 933. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 945. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 944. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 946. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 943. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 947. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 942. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

### TotalVolatileOrganicCompoundsConcentrationMeasurement `0x042E`

Header line 7 of `go-fabric@v0.22.2:cluster/spec/totalvolatileorganiccompoundsconcentrationmeasurement/definition_gen.go`. Schema `commands`/`events` empty at 114877. a prior accounting lines 949–969. Proposals match carbon monoxide (`thermal.air.volume_fraction`). Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 957. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 960. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 956. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 961. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 962. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 953. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 954. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 963. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.volume_fraction`) | absent | no row | no source | no correspondence | a prior accounting line 959. |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 958. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 955. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 967. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 966. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 968. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 965. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 969. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 964. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

### RadonConcentrationMeasurement `0x042F`

Header: `go-fabric@v0.22.2:cluster/spec/radonconcentrationmeasurement/definition_gen.go` line 7. Enum block lines 107–129 matches carbon monoxide. Features lines 132–139 match. Schema `commands`/`events` empty at 115601–115602. a prior accounting lines 971–991. Value proposals use `thermal.air.radon_concentration`. Device type: AirQualitySensor `O` only.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MeasuredValue | attribute | `0x0000` | `single` float32 | `MEA` | none | none in catalog (`thermal.air.radon_concentration`) | absent | no row | no source | no correspondence | schema MeasuredValue at line 115204, type `single`, conformance `MEA`, quality `X`. a prior accounting line 979. |
| MinMeasuredValue | attribute | `0x0001` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 982. |
| MaxMeasuredValue | attribute | `0x0002` | `single` float32 | `MEA` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 978. |
| PeakMeasuredValue | attribute | `0x0003` | `single` float32 | `PEA` | none | none in catalog (`thermal.air.radon_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 983. |
| PeakMeasuredValueWindow | attribute | `0x0004` | `elapsed-s` uint32 | `PEA` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 984. |
| AverageMeasuredValue | attribute | `0x0005` | `single` float32 | `AVG` | none | none in catalog (`thermal.air.radon_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 975. |
| AverageMeasuredValueWindow | attribute | `0x0006` | `elapsed-s` uint32 | `AVG` | none | none in catalog (`thermal.air.statistic_window`) | absent | no row | no source | no correspondence | a prior accounting line 976. |
| Uncertainty | attribute | `0x0007` | `single` float32 | `[MEA]` | none | none in catalog (`thermal.air.uncertainty`) | absent | no row | no source | no correspondence | a prior accounting line 985. |
| MeasurementUnit | attribute | `0x0008` | `MeasurementUnitEnum` enum8 | `MEA` | none | none in catalog (`thermal.air.radon_concentration`) | absent | no row | no source | no correspondence | a prior accounting line 981. Enum includes `Bqm3` value 7, conformance `MEA`, same as the other nine clusters (`definition_gen.go` lines 115 and 129). |
| MeasurementMedium | attribute | `0x0009` | `MeasurementMediumEnum` enum8 | `M` | none | none in catalog (`thermal.air.measurement_medium`) | absent | no row | no source | no correspondence | a prior accounting line 980. |
| LevelValue | attribute | `0x000A` | `LevelValueEnum` enum8 | `LEV` | none | none in catalog (`thermal.air.level`) | absent | no row | no source | no correspondence | a prior accounting line 977. |
| MEA | feature | bit 0 | title `NumericMeasurement` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | `definition_gen.go` line 137. a prior accounting line 989. |
| LEV | feature | bit 1 | title `LevelIndication` | `O.a+` | none | none in catalog | absent | no row | no source | no correspondence | `definition_gen.go` line 138. a prior accounting line 988. |
| MED | feature | bit 2 | title `MediumLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 990. |
| CRI | feature | bit 3 | title `CriticalLevel` | `[LEV]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 987. |
| PEA | feature | bit 4 | title `PeakMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 991. |
| AVG | feature | bit 5 | title `AverageMeasurement` | `[MEA]` | none | none in catalog | absent | no row | no source | no correspondence | a prior accounting line 986. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global on this cluster. |

## HepaFilterMonitoring `0x0071` revision 1

Locator: `go-fabric@v0.22.2:cluster/spec/hepafiltermonitoring/definition_gen.go` (whole file). `Base: "ResourceMonitoring"` line 176. Schema cluster object starts line 65877. `commands` at 66583 is one command; `events` `[]` at 66608; command `fields` `[]` at 66604.

Device types that list the cluster, all conformance `O`, none with `Mandatory: true`:

| device type | id | revision | locator |
|---|---|---|---|
| AirPurifier | `0x002D` | 3 | `go-fabric@v0.22.2:device/air_purifier_gen.go` lines 53–56 |
| RoomAirConditioner | `0x0072` | 4 | `go-fabric@v0.22.2:device/room_air_conditioner_gen.go` lines 23–26 and 64–67 |
| ExtractorHood | `0x007A` | 1 | `go-fabric@v0.22.2:device/extractor_hood_gen.go` lines 16–19 and 42–45 |

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Condition | attribute | `0x0000` | `percent` uint8 | `CON` | none | none in catalog (`resource.air_filter`, `thermal.dimension.air_filter`, `thermal.filter.condition`, `thermal.filter.kind`, `thermal.service.air_filter`) | absent | no row | no source | no correspondence | access `R` `V`; constraint `max 100`. `definition_gen.go` lines 183–188. a prior accounting line 196. |
| DegradationDirection | attribute | `0x0001` | `DegradationDirectionEnum` enum8 | `CON` | none | none in catalog (`thermal.filter.degradation_direction`) | absent | no row | no source | no correspondence | fixed; constraint `desc`. Enum: 0 `Up` `M`, 1 `Down` `M` (lines 82–92). a prior accounting line 197. |
| ChangeIndication | attribute | `0x0002` | `ChangeIndicationEnum` enum8; catalog canonical unit `thermal.status.maintenance` none | `M` | none | none in catalog ( and a prior proposal: `thermal.filter.change_indication`, `thermal.status.maintenance`) | absent for both proposed ids. `thermal.status.maintenance` is a different catalog fact; see notes | no row for the proposed ids. `thermal.status.maintenance` `1.0.0` disposition `unknown`, reason `matter.unmapped.v1` (target rows line 245) | no source | no correspondence | access `R` `V`. Enum: 0 `Ok` `M`, 1 `Warning` `WRN`, 2 `Critical` `M` (lines 61–73). Cluster is `O` on the three device types, so attribute `M` is not device-mandatory. `thermal.status.maintenance` `1.0.0` is in the catalog (compact line 393): fact, symbol, subject `resource.thermal_system` via `thermal.dimension.system`. The catalog attributes in that row do not name a filter, a percent, or `Ok`/`Warning`/`Critical`. It is not marked as a feed. a prior accounting line 195. |
| InPlaceIndicator | attribute | `0x0003` | `bool` | `O` | none | none in catalog (`thermal.filter.in_place`) | absent | no row | no source | no correspondence | access `R` `V`. `definition_gen.go` lines 205–208. a prior accounting line 198. |
| LastChangedTime | attribute | `0x0004` | `epoch-s` uint32 | `O` | none | none in catalog (`thermal.filter.last_changed`, `thermal.operation.set_filter_last_changed`) | absent | no row | no source | no correspondence | access `RW`, read `V`, write operate; nullable; non-volatile; default `spec.NullDefault{}` (lines 211–216). a prior accounting line 199 records access `W`. |
| ReplacementProductList | attribute | `0x0005` | list of `ReplacementProductStruct` | `REP` | none | none in catalog ( and a prior proposal: `thermal.dimension.replacement_product`, `thermal.filter.replacement_product_identifier`, `thermal.filter.replacement_product_kind`) | absent | no row | no source | no correspondence | fixed; constraint `max 5`. `definition_gen.go` lines 219–225. a prior accounting line 200. |
| ProductIdentifierType | struct field | 0 | `ProductIdentifierTypeEnum` enum8 | `M` | none | none in catalog | absent | no row | no source | no correspondence | field of `ReplacementProductStruct`. constraint `desc`. Enum: 0 `Upc` `M`, 1 `Gtin8` `M`, 2 `Ean` `M`, 3 `Gtin14` `M`, 4 `Oem` `M` (lines 101–117 and 145–146). |
| ProductIdentifierValue | struct field | 1 | `string` | `M` | none | none in catalog | absent | no row | no source | no correspondence | constraint `max 20` (line 147). |
| ResetCondition | command | `0x00` | request, response `status`, payload struct with no fields | `O` | none | none in catalog (`thermal.operation.reset_filter`) | absent | no row | no source | no correspondence | `definition_gen.go` lines 150–162 and 228–235. Access struct `RW` `"R"`, read privilege operate, write privilege operate. schema.json lines 66583–66604 `fields` `[]`. a prior accounting line 201 records access `W`. |
| CON | feature | bit 0 | title `Condition` | `O` | none | none in catalog | absent | no row | no source | no correspondence | `definition_gen.go` line 178. a prior accounting line 202. |
| WRN | feature | bit 1 | title `Warning` | `O` | none | none in catalog | absent | no row | no source | no correspondence | line 179. a prior accounting line 204. |
| REP | feature | bit 2 | title `ReplacementProductList` | `O` | none | none in catalog | absent | no row | no source | no correspondence | line 180. a prior accounting line 203. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema.json lines 66530–66551. quality fixed; access read `V`. Cluster not `M` on a device type. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema.json lines 66553–66579. default 1; constraint `min 1`; quality fixed. |

No events (`schema.json` line 66608). `definition_gen.go` has a `Commands` slice and no `Events` slice.

## ActivatedCarbonFilterMonitoring `0x0072` revision 1

Locator: `go-fabric@v0.22.2:cluster/spec/activatedcarbonfiltermonitoring/definition_gen.go`. The file matches the HEPA file with cluster id `0x0072`, name `ActivatedCarbonFilterMonitoring`, and `Base: "ResourceMonitoring"` (lines 6–7, 22–25, 174–176). Attribute, command, enum and feature blocks are the same texts (lines 29–53, 61–117, 145–147, 182–236). Schema cluster object starts line 66352. Command `ResetCondition` id 0, `fields` `[]`, `events` `[]` at lines 66108–66133.

Device types:

| device type | id | revision | conformance | locator |
|---|---|---|---|---|
| AirPurifier | `0x002D` | 3 | `O` | `go-fabric@v0.22.2:device/air_purifier_gen.go` lines 57–60 |
| RoomAirConditioner | `0x0072` | 4 | `O` | `go-fabric@v0.22.2:device/room_air_conditioner_gen.go` lines 68–71 |
| ExtractorHood | `0x007A` | 1 | `O` | `go-fabric@v0.22.2:device/extractor_hood_gen.go` lines 46–49 |
| Refrigerator | `0x0070` | 3 | `[Rev >= v3]` | `go-fabric@v0.22.2:device/refrigerator_gen.go` lines 16–19 and 45–48. Schema effective ast type `optionalIf`, revision param 3 (`schema.json` lines 6971–6982). Go struct does not set `Mandatory: true`. The accessor comment says the server is nil until a declaration mounts it (line 77). |

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Condition | attribute | `0x0000` | `percent` uint8 | `CON` | none | none in catalog (`resource.air_filter`, `thermal.filter.condition`, `thermal.filter.kind`) | absent | no row | no source | no correspondence | constraint `max 100`. a prior accounting line 211. The HEPA row also names `thermal.dimension.air_filter` and `thermal.service.air_filter`; this prior accounting row does not. |
| DegradationDirection | attribute | `0x0001` | `DegradationDirectionEnum` enum8 | `CON` | none | none in catalog (`thermal.filter.degradation_direction`) | absent | no row | no source | no correspondence | fixed. Enum `Up`/`Down` as HEPA. a prior accounting line 212. |
| ChangeIndication | attribute | `0x0002` | `ChangeIndicationEnum` enum8; catalog canonical unit `thermal.status.maintenance` none | `M` | none | none in catalog (`thermal.filter.change_indication`) | absent | no row | no source | no correspondence | Enum `Ok`/`Warning`/`Critical` as HEPA. a prior accounting line 210 does not list `thermal.status.maintenance`. That catalog fact is still not a feed: symbol on `resource.thermal_system` (catalog compact line 393). |
| InPlaceIndicator | attribute | `0x0003` | `bool` | `O` | none | none in catalog (`thermal.filter.in_place`) | absent | no row | no source | no correspondence | a prior accounting line 213. |
| LastChangedTime | attribute | `0x0004` | `epoch-s` uint32 | `O` | none | none in catalog (`thermal.filter.last_changed`) | absent | no row | no source | no correspondence | access `RW`, read `V`, write operate; nullable; non-volatile; null default (`definition_gen.go` lines 211–216). a prior accounting line 214 records access `W` and does not list `thermal.operation.set_filter_last_changed` (that id is on the HEPA row only). |
| ReplacementProductList | attribute | `0x0005` | list of `ReplacementProductStruct` | `REP` | none | none in catalog (`thermal.filter.replacement_product_identifier`) | absent | no row | no source | no correspondence | fixed; max 5. a prior accounting line 215. HEPA also proposes `thermal.dimension.replacement_product` and `thermal.filter.replacement_product_kind`. |
| ProductIdentifierType | struct field | 0 | `ProductIdentifierTypeEnum` enum8 | `M` | none | none in catalog | absent | no row | no source | no correspondence | same struct as HEPA, `definition_gen.go` lines 145–146. |
| ProductIdentifierValue | struct field | 1 | `string` | `M` | none | none in catalog | absent | no row | no source | no correspondence | max 20, line 147. |
| ResetCondition | command | `0x00` | request, response `status`, no fields | `O` | none | none in catalog (`thermal.operation.reset_filter`) | absent | no row | no source | no correspondence | lines 228–235. schema.json line 66129 `fields` `[]`. a prior accounting line 216 records access `W`. |
| CON | feature | bit 0 | title `Condition` | `O` | none | none in catalog | absent | no row | no source | no correspondence | line 178. a prior accounting line 217. |
| WRN | feature | bit 1 | title `Warning` | `O` | none | none in catalog | absent | no row | no source | no correspondence | line 179. a prior accounting line 219. |
| REP | feature | bit 2 | title `ReplacementProductList` | `O` | none | none in catalog | absent | no row | no source | no correspondence | line 180. a prior accounting line 218. |
| FeatureMap | attribute | 65532 | `FeatureMap` bitmap uint32 | `M` | none | none in catalog | absent | no row | no source | no correspondence | schema global. HEPA sibling lines 66530–66551. This cluster's feature-map object was not re-read line by line; the attribute list starts with Condition at schema line 66359, same as HEPA. |
| ClusterRevision | attribute | 65533 | `ClusterRevision` uint16 | `M` | none | none in catalog | absent | no row | no source | no correspondence | HEPA default 1 was read. This cluster's default line was not read. See Uncertainty. |

No events (schema.json line 66133).

## Mandatory elements without a source

Scope: elements of the listed clusters whose cluster is `M` on AirQualitySensor or AirPurifier and whose own conformance is `M`. Identify (`M` on both device types) and FanControl (`M` on AirPurifier) are outside the listed clusters. Their elements are not in the tables above. See the open questions.

| element | cluster | why it is mandatory | catalog |
|---|---|---|---|
| AirQuality `0x0000` | AirQuality `0x005B` | cluster `M` on AirQualitySensor and attribute `M` | absent. Proposed ids `thermal.dimension.substance`, `thermal.measurement.air_quality` are absent |
| FeatureMap 65532 | AirQuality | cluster `M` on AirQualitySensor and schema conformance `M` | absent |
| ClusterRevision 65533 | AirQuality | cluster `M` on AirQualitySensor and schema conformance `M` | absent |

Enum members `Unknown`, `Good` and `Poor` of `AirQualityEnum` are conformance `M` (definition lines 63–67). They are values of the mandatory attribute, not separate catalog feeds.

No concentration element and no filter element is mandatory for AirQualitySensor or AirPurifier. Those clusters are `O` on the device files of this group. `MeasurementMedium` and `ChangeIndication` are `M` only inside an optional cluster. Refrigerator's activated-carbon conformance is `[Rev >= v3]` / `optionalIf`, and the Go struct does not set `Mandatory: true`.

## Catalog elements of this domain without a Matter element

No catalog row is an air-quality index, a gas or particulate concentration, or a filter condition. The a prior proposal ids in the prior accounting (`thermal.air.*`, `thermal.filter.*`, `thermal.measurement.air_quality`, `resource.air_filter`, and the other ids named in the tables) are absent.

Nearest catalog rows whose ids or subjects use air, ventilation, or maintenance, and why each has no counterpart among the elements of these clusters:

| catalog id | catalog record (compact view) | target row | why it is not a counterpart in these clusters |
|---|---|---|---|
| `thermal.status.maintenance` `1.0.0` | fact, symbol, subject `resource.thermal_system`, dimension `thermal.dimension.system` (line 393). No symbol list and no unit in that attributes JSON | disposition `unknown`, reason `matter.unmapped.v1` (target line 245) | Subject is the thermal system. These clusters' change indication is `ChangeIndicationEnum` (`Ok`, `Warning`, `Critical`) on a filter cluster. The catalog row does not state those values.; catalog canonical unit `thermal.status.maintenance` none |
| `thermal.demand.level` `1.0.0` | fact, quantity, subject `resource.ventilation_system`, dimension `thermal.dimension.ventilation` (line 306). No unit in that attributes JSON | disposition `unknown`, reason `matter.unmapped.v1` (target line 184) | A ventilation demand quantity. No element in these clusters is a demand level. FanControl is outside this group.; catalog canonical unit `thermal.demand.level` `unit.ratio` |
| `thermal.relation.air_supply` `1.0.0` | relation, `core_type` `supplies`, `medium` `air`, from `resource.terminal_unit` and `resource.ventilation_system` to `resource.zone` (line 368) | not retrieved as its own line in this pass | A supply relation. No element in these clusters is a relation. |
| `resource.ventilation_system` `1.0.0` | resource kind, anchor class `function` (line 66) | not a target fact row in the searches above | A resource kind. These clusters do not declare a ventilation resource. |
| `thermal.dimension.ventilation` `1.0.0` | dimension, resource kind `resource.ventilation_system` (line 316) | — | Dimension of that resource kind. |
| `thermal.service.ventilation` `1.0.0` | service, subject kind `resource.ventilation_system` (line 382) | — | Service for that dimension. |
| `thermal.capability.read.ventilation` `1.0.0` | capability, service `thermal.service.ventilation` (line 302) | — | Read capability for that service. |
| `thermal.measurement.humidity` `1.0.0` | fact, quantity, subject `resource.zone` (line 328). No unit in that attributes JSON | not opened in this pass | Zone humidity. The Matter cluster on AirQualitySensor for humidity is RelativeHumidityMeasurement `0x0405`, which is outside this group.; catalog canonical unit `thermal.measurement.humidity` `unit.ratio` |

`thermal.measurement.air_temperature` and `thermal.measurement.outdoor_air_temperature` are temperature facts (catalog lines 321 and 329). They are outside this cluster group's domain.

## Disagreements with the prior accounting

1. a prior accounting lines 199 and 214 record `LastChangedTime` access `W`. Both filter `definition_gen.go` files lines 211–215 declare access `RW`, read privilege view, write privilege operate, nullable, non-volatile.
2. a prior accounting lines 201 and 216 record `ResetCondition` access `W`. Both filter definitions lines 230–233 declare `RW` `"R"` with read privilege operate and write privilege operate. schema.json lines 66599–66603 and the activated-carbon command block agree (`readPriv` `O`, `writePriv` `O`).
3. a prior accounting records attribute access as `R` and does not record the view privilege. The generated attributes of this group use read privilege view (`Access.Read: spec.PrivilegeView` on the attribute structs read in full).
4. a prior accounting, for every concentration cluster, marks `MinMeasuredValue` and `MaxMeasuredValue` absent with the reason that a binding derives them from field bounds (first pair at lines 780 and 784). The attributes are present in the Matter model (ids `0x0001` and `0x0002`, conformance `MEA`). The catalog view has no element for them and no bounds element. The target view has no row. The derivation is not in those sources.
5. `a prior accounting` a prior claim (line 177) calls both filter clusters a partial match to `thermal.status.maintenance`, described there as clear/due, system dimension, defined-not-fed. The catalog row (compact line 393) is a symbol on `resource.thermal_system`. It does not name a filter and does not list symbol values. The target row is disposition `unknown`, reason `matter.unmapped.v1` (line 245). Feed state is not in the catalog or the target row. a prior accounting line 195 puts `thermal.status.maintenance` on HEPA `ChangeIndication` together with `thermal.filter.change_indication`. Line 210 puts only `thermal.filter.change_indication` on the activated-carbon attribute. Neither proposed filter id is in the catalog.
6. a prior accounting assigns `thermal.air.volume_fraction`, `thermal.air.mass_concentration`, or `thermal.air.radon_concentration` by substance. The ten generated clusters share one `MeasurementUnitEnum` (values 0–7, each conformance `MEA`) and do not declare a per-cluster subset. Those three catalog ids are absent. The prior accounting status for the value attributes is `planned`, which matches absence, and the unit split is not a constraint of the generated cluster.
7. `a prior accounting` line 347 says the ten concentration clusters were not opened. The go-fabric definitions and `go-fabric@v0.22.2:parity/schema.json` contain them, revision 5, with the elements in the tables above. a prior claim (line 181) says the group is absent in SemReg. That absence matches the catalog view. The line does not record the per-attribute model.

a prior accounting cluster ids, revisions, attribute ids and conformance texts for this group match the generated definitions, including feature bits and the choice text `O.a+`.

## Uncertainty

1. `git show` at the two frozen SHAs was not run. Catalog and target statements use the pinned catalog and target files, which name docs-semantic SHA `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`. The semreg fixture at SHA `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:` was not read with `git show`. The brief says that fixture is a copy of the catalog.
2. Cluster headers name matter.js `a commit id recorded in the cited file`. `spec-levels.md` line 58 names `a commit id recorded in the cited file` for level 1.6.1. Whether those commits are the same snapshot is unknown.
3. `ClusterRevision` default 5 was read on the carbon monoxide schema object (line 109081) and default 1 on AirQuality (line 56832) and HEPA (line 66579). The other concentration clusters and activated carbon were checked for empty `commands` and `events`, and for cluster id, name and revision. Their `ClusterRevision` default lines were not each read. The generated `Revision` constant is 5 for every concentration cluster and 1 for activated carbon.
4. Activated carbon's `FeatureMap` and `ClusterRevision` schema objects were not read line by line. HEPA's were (lines 66530–66579). The activated-carbon attribute list begins at the same shape (Condition at line 66359).
5. Nine concentration `definition_gen.go` files were not read in full. Their line-7 identity, and for PM2.5 and carbon dioxide the attribute-id comments, match carbon monoxide. Radon's unit enum and the start of its feature list were read and match. Schema object length is 724 lines for each of the ten, with `commands`/`events` empty at the offsets above. A byte-level diff of the ten Go files was not made.
6. Catalog element attributes in the compact view do not include a unit or a symbol vocabulary for `thermal.status.maintenance`, `thermal.demand.level`, or `thermal.measurement.humidity`. Where a unit would be stored beyond that JSON is not established from the sources read at the frozen SHA.
7. Whether any driver feeds a catalog element is not visible from these sources.
8. `go-fabric@v0.22.2:parity/schema.json` Descriptor requirements on both device types have no conformance field. What that absence means for mandatoriness is not stated in the lines read.
9. AirPurifier schema lists optional device types AirQualitySensor, Thermostat, TemperatureSensor and HumiditySensor. The device Go file does not. How devicegen drops them was not determined. This accounting follows the device file for the server list and records the schema list beside it.
