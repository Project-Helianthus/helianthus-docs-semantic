---
status: "research notes for Matter 1.6.1 bridge and identity clusters; no mapping is decided and no canonical target is written."
---

# Bridge identity

Matter 1.6.1 cluster accounting for Bridge identity. Identifiers, conformance, types and units are read from go-fabric@v0.22.2:parity/schema.json (revision 1.6.1, data model revision 21) and the generated cluster and device files cited below. Catalog elements are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json and semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:fixtures/v1/element-catalog-v1.json. Canonical units are the `canonical_unit` field of docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/pack-metadata-v1.json. Target rows are read from docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json and docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.md. No mapping is chosen. No grade in this note is `exact`. Charge capacity stays `unit.ampere_hour` where the catalog defines it; `storage.capacity.remaining` and `storage.capacity.full_charge` are absent from the pinned catalog. A catalog canonical unit is written beside the Matter unit on each element row that names a catalog field.

Read-only source accounting for the bridge-identity cluster group. No mapping decision is made here.

## Header

- Queue row QQ04 in the research row: TARGET-MAT-R read-only source accounting by cluster.
- docs-semantic frozen SHA: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:` (`git -C` that view `rev-parse HEAD` returned this SHA).
- semreg frozen SHA: `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:` (`git rev-parse HEAD` on that view returned this SHA).
- go-fabric: module `go-fabric v0.22.2`. README.md line 29 states `v0.22.2` (2026-11-12). README.md line 17 states the Matter specification currently 1.6.1. `go-fabric@v0.22.2:schema/levels_gen.go` line 17 lists level `"1.6.1"` with the comment `matter.js v0.18.0 (a commit id recorded in the cited file), method model`. `script/surfacecheck/summary.md` line 15 states specification level 1.6.1. Each cluster file named below states generation from the matter.js model at `a commit id recorded in the cited file` (Matter 1.6.1). The sources read here do not equate `a commit id recorded in the cited file` with `a commit id recorded in the cited file`.

Files read:

- `go-fabric@v0.22.2:device/aggregator_gen.go`, `go-fabric@v0.22.2:device/bridged_node_gen.go`, `go-fabric@v0.22.2:device/root_node_gen.go`, `go-fabric@v0.22.2:device/doc.go` lines 31-37, `go-fabric@v0.22.2:device/base.go` lines 18-47 and 149-174, `go-fabric@v0.22.2:docs/reference/device-types.md` sections Aggregator (lines 14-24), BridgedNode (lines 108-120), RootNode (lines 978-1011).
- `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` device types `0x000E`, `0x0013`, `0x0016`, Base at lines 2350-2368, `clusterClassifications` lines 2475-2507, HeatPump `0x0309` lines 2030-2068 (prior-audit check only). `go-fabric@v0.22.2:schema/devicetype_requirements.go` lines 190-198. `go-fabric@v0.22.2:schema/levels_gen.go` lines 9-17. `go-fabric@v0.22.2:schema/devicetypes.go` lines 17-30.
- `go-fabric@v0.22.2:cluster/spec/basicinformation/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/bridgeddevicebasicinformation/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/descriptor/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/fixedlabel/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/userlabel/definition_gen.go`, `go-fabric@v0.22.2:cluster/spec/identify/definition_gen.go`.
- `go-fabric@v0.22.2:cluster/spec/instance.go` lines 15-23, `go-fabric@v0.22.2:cluster/spec/peer_state.go` lines 69-81, `go-fabric@v0.22.2:cluster/spec/conformance.go` lines 110-126 and 203-229, `go-fabric@v0.22.2:cluster/spec/revision_conformance_test.go` lines 12-36, `go-fabric@v0.22.2:cluster/spec/model.go` lines 22-59.
- the registry unit rule items 34 and 49. They add no cluster fact to this accounting.
- docs-semantic at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`, via `git show` / `git grep`: `api/v1/element-catalog-v1.json`, `api/v1/targets/matter-1.6.1-v1.json`. Pinned catalog and target files of those files: `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/element-catalog-v1.json`, `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:api/v1/targets/matter-1.6.1-v1.json`.
- semreg at `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:`, `fixtures/v1/element-catalog-v1.json` (grep for `equipment.identification`, `equipment.label`, `resource.equipment`).
- Prior claims were checked against a prior accounting lines 1-4, 60-91, 137-171, and the Matter headings from line 10 through line 1047. a prior accounting lines 5-7 and 292.

No attribute in the six `Definition` values sets a unit. The type column is the generated type, with the constraint text when the definition declares one.

Catalog outcome, the same for every row of the six clusters unless the SemReg cell names a a prior proposal id: `git grep` of `equipment.identification` and `equipment.label` on docs-semantic `api/v1/element-catalog-v1.json` at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:` returned no matches, and the same two patterns on the semreg fixture at `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:` returned no matches. The Matter target JSON at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:` contains `cluster_id` 144 and 156 only (`git grep` of `"cluster_id"`). None of 3, 29, 40, 41, 56, 57, 64, or 65 (decimal for `0x0003`, `0x001D`, `0x0028`, `0x0029` is not in this group, `0x0039` is 57, `0x0040` is 64, `0x0041` is 65) appears. Decimal check: Identify 3, Descriptor 29, BasicInformation 40, BridgedDeviceBasicInformation 57, FixedLabel 64, UserLabel 65. So every row below has catalog status `absent`, target row `no row`, source status `no source`, loss `no correspondence`. A driver feed is not visible from these sources.

Applicability used for "mandatory for which device types", from `go-fabric@v0.22.2:cluster/spec/conformance.go` and `revision_conformance_test.go` lines 12-17 and 29-35, evaluated at the cluster revision in that cluster's `definition_gen.go`:

- `M` (`ConfMandatory`) is mandatory.
- A bare `Rev >= vN` (`ConfRevision`) is mandatory when the definition revision is at least N (`revisionApplicability`, `conformance.go` lines 110-125).
- `Rev >= vN, O` (`ConfOtherwise` of a revision term then `ConfOptional`) is mandatory when the definition revision is at least N, and optional below N (`revision_conformance_test.go` line 33).
- `[Rev >= vN]` (`ConfOptionalIf`) is optional when the revision is at least N (line 35).
- `O` is optional. `X` (`ConfDisallowed`) is `ApplicabilityNone` (line 215-216). `desc` (`ConfDesc`) is conditional (line 226-227).
- A bare name is mandatory only when that name is a supported feature (`conformance.go` lines 237-241).

An element is listed as mandatory for a device type of this group when that device type requires the cluster and the element's applicability at the definition revision is mandatory. Base device type requirements apply to every endpoint that lists a device type (`go-fabric@v0.22.2:schema/devicetype_requirements.go` lines 190-193; `go-fabric@v0.22.2:device/devicetype_requirements_gen.go` lines 2350-2352).

## Device types

### Aggregator

`go-fabric@v0.22.2:device/aggregator_gen.go` lines 15-45. Id `0x000E`, revision 2, classification `simple`, composition `schema.CompositionFullFamily`, condition `FabricSynchronization`. The same id, revision, classification, composition, and condition are in `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 50-53. `go-fabric@v0.22.2:docs/reference/device-types.md` lines 14-24 match the server table below.

| Server cluster | ID | Conformance | Mandatory in the device file | Locator |
| --- | --- | --- | --- | --- |
| Actions | `0x0025` | `O` | no (`Mandatory` field absent) | `go-fabric@v0.22.2:device/aggregator_gen.go` lines 33-36 |
| Identify | `0x0003` | `O` | no | lines 37-40 |
| CommissionerControl | `0x0751` | `FabricSynchronization` | no | lines 41-44 |

No client clusters in this file.

`go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 55-59 also list server cluster Descriptor `0x001D` with no `Conformance` field, and under it attribute `DeviceTypeList` with no `Conformance` field. `go-fabric@v0.22.2:device/aggregator_gen.go` has no Descriptor entry. Base lists Descriptor server conformance `M` (see below).

### BridgedNode

`go-fabric@v0.22.2:device/bridged_node_gen.go` lines 17-56. Id `0x0013`, revision 3, classification `utility`, composition `schema.CompositionFullFamily`, condition `FabricSynchronizedNode`. The same identity is in `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 103-105. `go-fabric@v0.22.2:docs/reference/device-types.md` lines 108-120 match the server table below.

| Server cluster | ID | Conformance | Mandatory in the device file | Locator |
| --- | --- | --- | --- | --- |
| BridgedDeviceBasicInformation | `0x0039` | `M` | `Mandatory: true` | `go-fabric@v0.22.2:device/bridged_node_gen.go` lines 35-39 |
| PowerSourceConfiguration | `0x002E` | `BridgedPowerSourceInfo, D` | no | lines 40-43 |
| PowerSource | `0x002F` | `BridgedPowerSourceInfo` | no | lines 44-47 |
| AdministratorCommissioning | `0x003C` | `FabricSynchronizedNode` | no | lines 48-51 |
| EcosystemInformation | `0x0750` | `FabricSynchronizedNode, O` | no | lines 52-55 |

No client clusters in this file.

`go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 107-111 list Descriptor `0x001D` with no `Conformance` field and nested attribute `DeviceTypeList` with no `Conformance` field. Line 115 sets `BridgedDeviceBasicInformation` conformance `M`. Line 118 lists device type `PowerSource` `0x0011` conformance `O`. `go-fabric@v0.22.2:device/bridged_node_gen.go` has no Descriptor entry and no device-type requirement.

### RootNode

`go-fabric@v0.22.2:device/root_node_gen.go` lines 31-147. Id `0x0016`, revision 5, classification `node`, composition `schema.CompositionFullFamily`. Conditions: `CustomNetworkConfig`, `ManagedAclAllowed`, `TimeSyncCond`, `TimeSyncWithClientCond`, `TimeSyncWithNtpcCond`, `TimeSyncWithTzCond`, `TlsCertificatesCond`, `TlsClientCond`, `PowerSourceCond`, `AclExtensionCond`, `GroupcastListenerCond`, `GroupcastSenderCond` (lines 47). The same identity and conditions are in `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 148-150. `go-fabric@v0.22.2:docs/reference/device-types.md` lines 978-1011 match the tables below.

Server clusters in `go-fabric@v0.22.2:device/root_node_gen.go` lines 48-141:

| Server cluster | ID | Conformance | Mandatory in the device file |
| --- | --- | --- | --- |
| AccessControl | `0x001F` | `M` | `Mandatory: true` (no `Definition` field on this entry) |
| BasicInformation | `0x0028` | `M` | `Mandatory: true` |
| GeneralCommissioning | `0x0030` | `M` | `Mandatory: true` |
| GeneralDiagnostics | `0x0033` | `M` | `Mandatory: true` |
| AdministratorCommissioning | `0x003C` | `M` | `Mandatory: true` |
| OperationalCredentials | `0x003E` | `M` | `Mandatory: true` (no `Definition` field) |
| GroupKeyManagement | `0x003F` | `M` | `Mandatory: true` (no `Definition` field) |
| LocalizationConfiguration | `0x002B` | `LanguageLocale` | no |
| TimeFormatLocalization | `0x002C` | `TimeLocale` | no |
| UnitLocalization | `0x002D` | `UnitLocale` | no |
| PowerSourceConfiguration | `0x002E` | `O, D` | no |
| NetworkCommissioning | `0x0031` | `!CustomNetworkConfig` | no |
| DiagnosticLogs | `0x0032` | `O` | no |
| SoftwareDiagnostics | `0x0034` | `O` | no |
| ThreadNetworkDiagnostics | `0x0035` | `[Thread]` | no |
| WiFiNetworkDiagnostics | `0x0036` | `[WiFi]` | no |
| EthernetNetworkDiagnostics | `0x0037` | `[Ethernet]` | no |
| TimeSynchronization | `0x0038` | `TimeSyncCond, TimeSyncWithClientCond, TimeSyncWithNtpcCond, TimeSyncWithTzCond, TlsClientCond, TlsCertificatesCond, O` | no |
| IcdManagement | `0x0046` | `Sit \| Lit` | no |
| Groupcast | `0x0065` | `GroupcastListenerCond, GroupcastSenderCond, O` | no |
| TlsCertificateManagement | `0x0801` | `TlsCertificatesCond, O` | no |
| TlsClientManagement | `0x0802` | `TlsClientCond, O` | no |

Client cluster in lines 142-146: TimeSynchronization `0x0038`, conformance `TimeSyncWithClientCond, O`, no `Mandatory` field.

`go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` line 166 sets BasicInformation `Singleton: true` as well as conformance `M`. The device file has `Mandatory: true` and no singleton field. Lines 152-156 list Descriptor `0x001D` with no `Conformance` field and nested attribute `DeviceTypeList` with no `Conformance` field. Line 218 lists device type `PowerSource` `0x0011` conformance `PowerSourceCond, O`. `go-fabric@v0.22.2:device/root_node_gen.go` has no Descriptor entry and no device-type requirement. The schema block also nests feature and attribute requirements on AccessControl, TimeSynchronization, GroupKeyManagement, IcdManagement, and Groupcast (lines 158-214); those clusters are outside this group and are not expanded here.

### Base device type (applies to all three)

`go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 2353-2368. Name `Base`, classification `base`, revision 3, composition `tree`, id not set (the Go struct comment at `devicetype_requirements.go` lines 162-163 says the Base device type has none). Server clusters:

| Server cluster | ID | Conformance |
| --- | --- | --- |
| Descriptor | `0x001D` | `M` |
| Binding | `0x001E` | `Simple & Client` |
| FixedLabel | `0x0040` | `O` |
| UserLabel | `0x0041` | `O` |

Descriptor's nested requirement: feature `TAGLIST`, conformance `Duplicate` (line 2361). `go-fabric@v0.22.2:device/base.go` lines 18-30 read FixedLabel and UserLabel where conformance text is `O`, and state that Descriptor (mandatory, the assembler's) stays out of that optional list. `go-fabric@v0.22.2:device/doc.go` lines 33-35 state that the assembler mounts Descriptor, Identify, BridgedDeviceBasicInformation, Groups, and ScenesManagement on every endpoint, and that the device package does not mount them. The device files above still declare BridgedDeviceBasicInformation and Identify where the device type names them.

Cluster classification in `go-fabric@v0.22.2:device/devicetype_requirements_gen.go` lines 2476-2507: Identify `endpoint`, Descriptor `endpoint`, BasicInformation `node`, BridgedDeviceBasicInformation `endpoint`, FixedLabel `endpoint`, UserLabel `endpoint`.

## Shared global attributes

`go-fabric@v0.22.2:cluster/spec/instance.go` lines 15-22: ids every server answers. Types in `go-fabric@v0.22.2:cluster/spec/peer_state.go` lines 69-81. They are absent from each cluster's `Definition.Attributes`. Conformance text: none in those two files. No unit.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GeneratedCommandList | attribute | `0xFFF8` | list of uint32 | none declared; every server answers | on each mandatory server of this group: Descriptor for Aggregator, BridgedNode, and RootNode; BasicInformation for RootNode; BridgedDeviceBasicInformation for BridgedNode | none in catalog | absent | no row | no source | no correspondence | `go-fabric@v0.22.2:cluster/spec/instance.go:17`; `peer_state.go:79-80` |
| AcceptedCommandList | attribute | `0xFFF9` | list of uint32 | none declared; every server answers | same as GeneratedCommandList | none in catalog | absent | no row | no source | no correspondence | `go-fabric@v0.22.2:cluster/spec/instance.go:18` |
| EventList | attribute | `0xFFFA` | list of uint32 | none declared; every server answers | same as GeneratedCommandList | none in catalog | absent | no row | no source | no correspondence | `go-fabric@v0.22.2:cluster/spec/instance.go:19` |
| AttributeList | attribute | `0xFFFB` | list of uint32 | none declared; every server answers | same as GeneratedCommandList | none in catalog | absent | no row | no source | no correspondence | `go-fabric@v0.22.2:cluster/spec/instance.go:20` |
| FeatureMap | attribute | `0xFFFC` | bitmap, 32 bits | none declared; every server answers | same as GeneratedCommandList | none in catalog | absent | no row | no source | no correspondence | `go-fabric@v0.22.2:cluster/spec/instance.go:21`; `peer_state.go:77` |
| ClusterRevision | attribute | `0xFFFD` | uint16 | none declared; every server answers | same as GeneratedCommandList | none in catalog | absent | no row | no source | no correspondence | `go-fabric@v0.22.2:cluster/spec/instance.go:22`; `peer_state.go:75-76`. Each cluster file also has its own `Revision` constant, cited in that cluster's section |

These six rows are the global attributes of all six clusters. They are not repeated in the cluster tables.

## BasicInformation `0x0028` revision 6

`go-fabric@v0.22.2:cluster/spec/basicinformation/definition_gen.go` lines 21-26 and 317-318. Classification `node` (`go-fabric@v0.22.2:device/devicetype_requirements_gen.go` line 2484). No `Features` slice and no feature-bit constants. No commands. Attribute ids jump from `0x0016` to `0x0018`; the file declares no attribute `0x0017`.

Mandatory cluster for RootNode (`go-fabric@v0.22.2:device/root_node_gen.go` lines 54-57; schema line 166 also `Singleton: true`). Aggregator and BridgedNode device files do not list it.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DataModelRevision | attribute | `0x0000` | uint16, constraint `desc` | `M` | RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 321-327 |
| VendorName | attribute | `0x0001` | string, max 32 | `M` | RootNode | none in catalog (`equipment.dimension.unit`, `equipment.identification.vendor_name`, `equipment.service.unit`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 329-335. a prior accounting line 87 |
| VendorId | attribute | `0x0002` | vendor-id, uint16 | `M` | RootNode | none in catalog (`equipment.identification.vendor_code`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 337-342. a prior accounting line 86 |
| ProductName | attribute | `0x0003` | string, max 32 | `M` | RootNode | none in catalog (`equipment.identification.product_name`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 344-350. a prior accounting line 78 |
| ProductId | attribute | `0x0004` | uint16 | `M` | RootNode | none in catalog (`equipment.identification.product_code`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 352-357. a prior accounting line 76 |
| NodeLabel | attribute | `0x0005` | string, max 32 | `M` | RootNode | none in catalog (`equipment.label.name`) | absent | no row | no source | no correspondence | access RW, read View, write Manage; quality NonVolatile. Lines 359-365. a prior accounting line 73 |
| Location | attribute | `0x0006` | string, constraint `2` | `M` | RootNode | none in catalog | absent | no row | no source | no correspondence | access RW, read View, write Administer; quality NonVolatile; default `"XX"`. Lines 367-374. a prior accounting line 70 |
| HardwareVersion | attribute | `0x0007` | uint16 | `M` | RootNode | none in catalog (`equipment.identification.hardware_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed; default 0. Lines 376-382. a prior accounting line 67 |
| HardwareVersionString | attribute | `0x0008` | string, 1 to 64 | `M` | RootNode | none in catalog (`equipment.identification.hardware_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 384-390. a prior accounting line 68 |
| SoftwareVersion | attribute | `0x0009` | uint32, constraint `desc` | `M` | RootNode | none in catalog (`equipment.identification.software_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed; default 0. Lines 392-399. a prior accounting line 82 |
| SoftwareVersionString | attribute | `0x000A` | string, 1 to 64 | `M` | RootNode | none in catalog (`equipment.identification.software_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 401-407. a prior accounting line 83 |
| ManufacturingDate | attribute | `0x000B` | string, 8 to 16 | `O` | none of this group | none in catalog (`equipment.identification.manufacturing_date`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 409-415. a prior accounting line 71 |
| PartNumber | attribute | `0x000C` | string, max 32 | `O` | none of this group | none in catalog (`equipment.identification.product_code`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 417-423. a prior accounting line 74 |
| ProductUrl | attribute | `0x000D` | string, max 256 | `O` | none of this group | none in catalog (`equipment.identification.product_url`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 425-431. a prior accounting line 79 |
| ProductLabel | attribute | `0x000E` | string, max 64 | `O` | none of this group | none in catalog (`equipment.identification.product_label`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 433-439. a prior accounting line 77 |
| SerialNumber | attribute | `0x000F` | string, max 32 | `O` | none of this group | none in catalog (`equipment.identification.serial_number`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 441-447. a prior accounting line 81 |
| LocalConfigDisabled | attribute | `0x0010` | bool | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access RW, read View, write Manage; quality NonVolatile; default false. Lines 449-455. a prior accounting line 69 |
| Reachable | attribute | `0x0011` | bool | `O` | none of this group | none in catalog (`equipment.status.reachable`) | absent | no row | no source | no correspondence | access R View; default true. Lines 457-462. a prior accounting line 80 |
| UniqueId | attribute | `0x0012` | string, max 32 | `Rev >= v4, O` | RootNode (definition revision 6; `revision_conformance_test.go` line 33) | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 464-470. a prior accounting line 85 |
| CapabilityMinima | attribute | `0x0013` | CapabilityMinimaStruct | `M` | RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 472-478. a prior accounting line 64. Fields below |
| CapabilityMinima.CaseSessionsPerFabric | field | 0 | uint16, 3 to 10000 | `M` | RootNode | none in catalog | absent | no row | no source | no correspondence | default 3. Lines 106-107 |
| CapabilityMinima.SubscriptionsPerFabric | field | 1 | uint16, 3 to 10000 | `M` | RootNode | none in catalog | absent | no row | no source | no correspondence | default 3. Line 108 |
| CapabilityMinima.SimultaneousInvocationsSupported | field | 2 | uint16, 1 to 10000 | `Rev >= v6` | RootNode | none in catalog | absent | no row | no source | no correspondence | Go field is `*uint16`. Line 109 |
| CapabilityMinima.SimultaneousWritesSupported | field | 3 | uint16, 1 to 10000 | `Rev >= v6` | RootNode | none in catalog | absent | no row | no source | no correspondence | Go field is `*uint16`. Line 110 |
| CapabilityMinima.ReadPathsSupported | field | 4 | uint16, 9 to 10000 | `Rev >= v6` | RootNode | none in catalog | absent | no row | no source | no correspondence | Go field is `*uint16`. Line 111 |
| CapabilityMinima.SubscribePathsSupported | field | 5 | uint16, 3 to 10000 | `Rev >= v6` | RootNode | none in catalog | absent | no row | no source | no correspondence | Go field is `*uint16`. Line 112 |
| ProductAppearance | attribute | `0x0014` | ProductAppearanceStruct | `[Rev >= v2]` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Optional at revision 6. Lines 480-486. a prior accounting line 75 |
| ProductAppearance.Finish | field | 0 | ProductFinishEnum, 8 bits | `M` | none of this group (parent attribute is optional) | none in catalog | absent | no row | no source | no correspondence | values, each conformance `M`: Other 0, Matte 1, Satin 2, Polished 3, Rugged 4, Fabric 5. Lines 208-226 |
| ProductAppearance.PrimaryColor | field | 1 | ColorEnum, 8 bits, nullable | `M` | none of this group (parent attribute is optional) | none in catalog | absent | no row | no source | no correspondence | quality Nullable. Values, each conformance `M`: Black 0, Navy 1, Green 2, Teal 3, Maroon 4, Purple 5, Olive 6, Gray 7, Blue 8, Lime 9, Aqua 10, Red 11, Fuchsia 12, Yellow 13, White 14, Nickel 15, Chrome 16, Brass 17, Copper 18, Silver 19, Gold 20. Lines 121-169 and 197-199 |
| SpecificationVersion | attribute | `0x0015` | uint32, constraint `desc` | `Rev >= v3` | RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed; default 0. Lines 488-495. a prior accounting line 84 |
| MaxPathsPerInvoke | attribute | `0x0016` | uint16, min 1 | `Rev >= v3` | RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed; default 1. Lines 497-504. a prior accounting line 72 |
| ConfigurationVersion | attribute | `0x0018` | uint32, min 1 | `Rev >= v6` | RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality NonVolatile; default 1. Lines 506-513. a prior accounting line 65 |
| StartUp | event | `0x00` | priority critical | `M` | RootNode | none in catalog | absent | no row | no source | no correspondence | access R View. Lines 516-524. a prior accounting line 91 |
| StartUp.SoftwareVersion | field | 0 | uint32 | `M` | RootNode | none in catalog | absent | no row | no source | no correspondence | lines 229-231 and 521 |
| ShutDown | event | `0x01` | priority critical; no fields | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View. Lines 525-530. a prior accounting line 90 |
| Leave | event | `0x02` | priority info | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View. Lines 531-539. a prior accounting line 88 |
| Leave.FabricIndex | field | 0 | fabric-idx, uint8, 1 to 254 | `M` | none of this group (parent event is optional) | none in catalog | absent | no row | no source | no correspondence | lines 260-262 and 536 |
| ReachableChanged | event | `0x03` | priority info | `Reachable` | none of this group | none in catalog (`equipment.event.reachable_changed`) | absent | no row | no source | no correspondence | access R View. Name `Reachable` is the optional attribute, and the cluster defines no feature of that name, so applicability is conditional (`conformance.go` lines 237-245). Lines 541-548. a prior accounting line 89 |
| ReachableChanged.ReachableNewValue | field | 0 | bool | `M` | none of this group (parent event is conditional) | none in catalog | absent | no row | no source | no correspondence | lines 279-281 and 545 |

## BridgedDeviceBasicInformation `0x0039` revision 6

`go-fabric@v0.22.2:cluster/spec/bridgeddevicebasicinformation/definition_gen.go` lines 21-26 and 377-379. `Base: "BasicInformation"`. Classification `endpoint` (`go-fabric@v0.22.2:device/devicetype_requirements_gen.go` line 2501).

Mandatory cluster for BridgedNode (`go-fabric@v0.22.2:device/bridged_node_gen.go` lines 35-39). Aggregator and RootNode device files do not list it.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BIS | feature | bit 20 | bitmap bit; title BridgedIcdSupport | `[Rev >= v4]` | none of this group | none in catalog | absent | no row | no source | no correspondence | optional at revision 6. Constant `FeatureBridgedIcdSupport = 1 << 20`. Lines 76-78 and 380-382. a prior accounting line 171 |
| DataModelRevision | attribute | `0x0000` | uint16, constraint `desc` | `X` | none of this group | none in catalog | absent | no row | no source | no correspondence | `ConfDisallowed`. Access R View; quality Fixed. Lines 385-391. a prior accounting line 143 |
| VendorName | attribute | `0x0001` | string, max 32 | `desc` | none of this group | none in catalog (`equipment.dimension.unit`, `equipment.identification.vendor_name`) | absent | no row | no source | no correspondence | `ConfDesc`, applicability conditional. Access R View; quality Fixed. Lines 393-399. a prior accounting line 164. The BasicInformation row's a prior proposal list also names `equipment.service.unit`; this prior accounting row does not |
| VendorId | attribute | `0x0002` | vendor-id, uint16 | `desc` | none of this group | none in catalog (`equipment.identification.vendor_code`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 401-406. a prior accounting line 163 |
| ProductName | attribute | `0x0003` | string, max 32 | `O` | none of this group | none in catalog (`equipment.identification.product_name`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 408-414. a prior accounting line 155 |
| ProductId | attribute | `0x0004` | uint16 | `desc` | none of this group | none in catalog (`equipment.identification.product_code`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 416-421. a prior accounting line 153 |
| NodeLabel | attribute | `0x0005` | string, max 32 | `O` | none of this group | none in catalog (`equipment.dimension.resource`, `equipment.label.name`, `equipment.operation.set_label`, `equipment.service.resource`) | absent | no row | no source | no correspondence | access RW, read View, write Manage; quality NonVolatile. Lines 423-429. a prior accounting line 150 |
| Location | attribute | `0x0006` | string, constraint `2` | `X` | none of this group | none in catalog | absent | no row | no source | no correspondence | access RW, read View, write Administer; quality NonVolatile; default `"XX"`. Lines 431-438. a prior accounting line 147 |
| HardwareVersion | attribute | `0x0007` | uint16 | `O` | none of this group | none in catalog (`equipment.identification.hardware_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed; default 0. Lines 440-446. a prior accounting line 144 |
| HardwareVersionString | attribute | `0x0008` | string, 1 to 64 | `O` | none of this group | none in catalog (`equipment.identification.hardware_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 448-454. a prior accounting line 145 |
| SoftwareVersion | attribute | `0x0009` | uint32, constraint `desc` | `O` | none of this group | none in catalog (`equipment.identification.software_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed; default 0. Lines 456-463. a prior accounting line 159 |
| SoftwareVersionString | attribute | `0x000A` | string, 1 to 64 | `O` | none of this group | none in catalog (`equipment.identification.software_revision`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 465-471. a prior accounting line 160 |
| ManufacturingDate | attribute | `0x000B` | string, 8 to 16 | `O` | none of this group | none in catalog (`equipment.identification.manufacturing_date`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 473-479. a prior accounting line 148 |
| PartNumber | attribute | `0x000C` | string, max 32 | `O` | none of this group | none in catalog (`equipment.identification.product_code`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 481-487. a prior accounting line 151 |
| ProductUrl | attribute | `0x000D` | string, max 256 | `O` | none of this group | none in catalog (`equipment.identification.product_url`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 489-495. a prior accounting line 156 |
| ProductLabel | attribute | `0x000E` | string, max 64 | `O` | none of this group | none in catalog (`equipment.identification.product_label`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 497-503. a prior accounting line 154 |
| SerialNumber | attribute | `0x000F` | string, max 32 | `O` | none of this group | none in catalog (`equipment.identification.serial_number`) | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 505-511. a prior accounting line 158 |
| LocalConfigDisabled | attribute | `0x0010` | bool | `X` | none of this group | none in catalog | absent | no row | no source | no correspondence | access RW, read View, write Manage; quality NonVolatile; default false. Lines 513-519. a prior accounting line 146 |
| Reachable | attribute | `0x0011` | bool | `M` | BridgedNode | none in catalog (`equipment.status.reachable`) | absent | no row | no source | no correspondence | access R View; default true. Lines 521-526. a prior accounting line 157 |
| UniqueId | attribute | `0x0012` | string, max 32 | `Rev >= v4, O` | BridgedNode (definition revision 6) | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 528-534. a prior accounting line 162 |
| CapabilityMinima | attribute | `0x0013` | CapabilityMinimaStruct | `X` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 536-542. a prior accounting line 141. The struct is still declared at lines 80-124, with the same fields as BasicInformation |
| CapabilityMinima.CaseSessionsPerFabric | field | 0 | uint16, 3 to 10000 | `M` | none of this group (parent attribute conformance `X`) | none in catalog | absent | no row | no source | no correspondence | default 3. Lines 117-118 |
| CapabilityMinima.SubscriptionsPerFabric | field | 1 | uint16, 3 to 10000 | `M` | none of this group (parent attribute conformance `X`) | none in catalog | absent | no row | no source | no correspondence | default 3. Line 119 |
| CapabilityMinima.SimultaneousInvocationsSupported | field | 2 | uint16, 1 to 10000 | `Rev >= v6` | none of this group (parent attribute conformance `X`) | none in catalog | absent | no row | no source | no correspondence | line 120 |
| CapabilityMinima.SimultaneousWritesSupported | field | 3 | uint16, 1 to 10000 | `Rev >= v6` | none of this group (parent attribute conformance `X`) | none in catalog | absent | no row | no source | no correspondence | line 121 |
| CapabilityMinima.ReadPathsSupported | field | 4 | uint16, 9 to 10000 | `Rev >= v6` | none of this group (parent attribute conformance `X`) | none in catalog | absent | no row | no source | no correspondence | line 122 |
| CapabilityMinima.SubscribePathsSupported | field | 5 | uint16, 3 to 10000 | `Rev >= v6` | none of this group (parent attribute conformance `X`) | none in catalog | absent | no row | no source | no correspondence | line 123 |
| ProductAppearance | attribute | `0x0014` | ProductAppearanceStruct | `[Rev >= v2]` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 544-550. a prior accounting line 152 |
| ProductAppearance.Finish | field | 0 | ProductFinishEnum, 8 bits | `M` | none of this group (parent attribute is optional) | none in catalog | absent | no row | no source | no correspondence | same value names and `M` conformance as BasicInformation. Lines 219-237 |
| ProductAppearance.PrimaryColor | field | 1 | ColorEnum, 8 bits, nullable | `M` | none of this group (parent attribute is optional) | none in catalog | absent | no row | no source | no correspondence | quality Nullable. Same 0-20 color names, each `M`, as BasicInformation. Lines 132-180 and 208-210 |
| SpecificationVersion | attribute | `0x0015` | uint32, constraint `desc` | `X` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed; default 0. Lines 552-559. a prior accounting line 161 |
| MaxPathsPerInvoke | attribute | `0x0016` | uint16, min 1 | `X` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed; default 1. Lines 561-568. a prior accounting line 149 |
| ConfigurationVersion | attribute | `0x0018` | uint32, min 1 | `[Rev >= v6]` | none of this group | none in catalog | absent | no row | no source | no correspondence | optional at revision 6. Access R View; quality NonVolatile; default 1. Lines 570-577. a prior accounting line 142 |
| KeepActive | command | `0x80` | request, response `status` | `BIS` | none of this group | none in catalog | absent | no row | no source | no correspondence | access struct `RW: "R"`, read Operate, write Operate. Lines 579-590. a prior accounting line 165 |
| KeepActive.StayActiveDuration | field | 0 | uint32 | `M` | none of this group (parent command conformance `BIS`) | none in catalog | absent | no row | no source | no correspondence | lines 241-243 and 586 |
| KeepActive.TimeoutMs | field | 1 | uint32, 30000 to 3600000 | `M` | none of this group (parent command conformance `BIS`) | none in catalog | absent | no row | no source | no correspondence | lines 243 and 587 |
| StartUp | event | `0x00` | priority critical | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View. Lines 593-601. a prior accounting line 170 |
| StartUp.SoftwareVersion | field | 0 | uint32 | `M` | none of this group (parent event is optional) | none in catalog | absent | no row | no source | no correspondence | lines 262-264 and 598 |
| ShutDown | event | `0x01` | priority critical; no fields | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View. Lines 602-607. a prior accounting line 169 |
| Leave | event | `0x02` | priority info | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View. Lines 608-616. a prior accounting line 167 |
| Leave.FabricIndex | field | 0 | fabric-idx, uint8, 1 to 254 | `X` | none of this group | none in catalog | absent | no row | no source | no correspondence | Definition field conformance `X`. The Go struct holds `*uint8` and the decoder binds it optional (`definition_gen.go` lines 294-308). Lines 612-613 |
| ReachableChanged | event | `0x03` | priority info | `M` | BridgedNode | none in catalog (`equipment.event.reachable_changed`) | absent | no row | no source | no correspondence | access R View. Lines 617-625. a prior accounting line 168 |
| ReachableChanged.ReachableNewValue | field | 0 | bool | `M` | BridgedNode | none in catalog | absent | no row | no source | no correspondence | lines 312-314 and 622 |
| ActiveChanged | event | `0x80` | priority info | `BIS` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View. Lines 626-634. a prior accounting line 166 |
| ActiveChanged.PromisedActiveDuration | field | 0 | uint32, constraint `desc` | `M` | none of this group (parent event conformance `BIS`) | none in catalog | absent | no row | no source | no correspondence | lines 331-333 and 631 |

## Descriptor `0x001D` revision 3

`go-fabric@v0.22.2:cluster/spec/descriptor/definition_gen.go` lines 21-26 and 197-199. Classification `endpoint`. No commands and no events in `Definition`.

Base server conformance `M` (`go-fabric@v0.22.2:device/devicetype_requirements_gen.go` line 2359), so the cluster is mandatory for Aggregator, BridgedNode, and RootNode. Each of those three schema entries also lists Descriptor with no `Conformance` field and nested attribute `DeviceTypeList` with no `Conformance` field (Aggregator lines 55-59, BridgedNode lines 107-111, RootNode lines 152-156). The three `*_gen.go` device files do not list Descriptor. Base's nested feature requirement for `TAGLIST` is conformance `Duplicate` (line 2361), and none of the three device types lists `Duplicate` among its own conditions.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TAGLIST | feature | bit 0 | bitmap bit; title TagList | `desc` | none of this group | none in catalog | absent | no row | no source | no correspondence | constant `FeatureTagList = 1 << 0`. Cluster feature conformance `desc` (line 201). Base device-type requirement conformance `Duplicate` (schema line 2361). Lines 44-46 and 200-202 |
| DeviceTypeList | attribute | `0x0000` | list of DeviceTypeStruct, min 1 | `M` | Aggregator, BridgedNode, RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Decode length 1 to 2147483647 (line 188). Lines 204-212 |
| DeviceTypeList.DeviceType | field | 0 | devtype-id, uint32 | `M` | Aggregator, BridgedNode, RootNode | none in catalog | absent | no row | no source | no correspondence | lines 49-51 and 74 |
| DeviceTypeList.Revision | field | 1 | uint16, min 1 | `M` | Aggregator, BridgedNode, RootNode | none in catalog | absent | no row | no source | no correspondence | lines 51 and 75 |
| ServerList | attribute | `0x0001` | list of cluster-id (uint32) | `M` | Aggregator, BridgedNode, RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed; default empty list. Lines 213-220 |
| ClientList | attribute | `0x0002` | list of cluster-id (uint32) | `M` | Aggregator, BridgedNode, RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed; default empty list. Lines 221-228 |
| PartsList | attribute | `0x0003` | list of endpoint-no (uint16) | `M` | Aggregator, BridgedNode, RootNode | none in catalog | absent | no row | no source | no correspondence | access R View; default empty list. No Fixed quality on this attribute. Lines 229-235 |
| TagList | attribute | `0x0004` | list of semtag, 1 to 6 | `TAGLIST` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Decode length 1 to 6 (line 193). Lines 236-244 |
| TagList.MfgCode | field | 0 | vendor-id, uint16, nullable | `M` | none of this group (parent attribute conformance `TAGLIST`) | none in catalog | absent | no row | no source | no correspondence | quality Nullable; default null. Lines 80 and 110 |
| TagList.NamespaceId | field | 1 | namespace, enum 8 bits | `M` | none of this group (parent attribute conformance `TAGLIST`) | none in catalog | absent | no row | no source | no correspondence | values have no conformance text in `NamespaceDef` (lines 156-185): CommonClosure 1, CommonCompassDirection 2, CommonCompassLocation 3, CommonDirection 4, CommonLevel 5, CommonLocation 6, CommonNumber 7, CommonPosition 8, ElectricalMeasurement 10, CommodityTariffChronology 11, CommodityTariffCommodity 13, Laundry 14, PowerSource 15, CommonAreaNamespace 16, CommonLandmarkNamespace 17, CommonRelativePosition 18, CommodityTariffFlow 19, Refrigerator 65, RoomAirConditioner 66, Switches 67, Closure 68, ClosurePanel 69, ClosureCovering 70, ClosureWindow 71, ClosureCabinet 72, IdentifiedObject 73, IdentifiedSound 74, IdentifiedHumanActivity 75. Constants at lines 122-150 |
| TagList.Tag | field | 2 | tag, uint8 | `M` | none of this group (parent attribute conformance `TAGLIST`) | none in catalog | absent | no row | no source | no correspondence | line 112 |
| TagList.Label | field | 3 | string, max 64, nullable | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | quality Nullable; default null. Go field is `*Nullable[string]`. Lines 83 and 113 |
| EndpointUniqueId | attribute | `0x0005` | string, max 32 | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View; quality Fixed. Lines 245-252 |

## FixedLabel `0x0040` revision 1

`go-fabric@v0.22.2:cluster/spec/fixedlabel/definition_gen.go` lines 21-26 and 73-76. `Base: "Label"`. Classification `endpoint`. No commands, events, or feature bits. `Feature` is declared as a type (lines 33-36) and no bit constants follow. Base server conformance `O` (schema line 2365). None of the three device files lists FixedLabel. `go-fabric@v0.22.2:device/base.go` lines 149-155: mounted when a declaration names it.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LabelList | attribute | `0x0000` | list of LabelStruct | `M` | none of this group (cluster conformance on Base is `O`) | none in catalog | absent | no row | no source | no correspondence | access R View; quality NonVolatile; default empty list. Decode uses `DecodeList` with no length bounds in this file (lines 68-70). Lines 77-86 |
| LabelList.Label | field | 0 | string, max 16 | `M` | none of this group (cluster is optional on Base) | none in catalog | absent | no row | no source | no correspondence | lines 39-41 and 64 |
| LabelList.Value | field | 1 | string, max 16 | `M` | none of this group (cluster is optional on Base) | none in catalog | absent | no row | no source | no correspondence | lines 41 and 65 |

## UserLabel `0x0041` revision 1

`go-fabric@v0.22.2:cluster/spec/userlabel/definition_gen.go` lines 21-26 and 73-76. `Base: "Label"`. Classification `endpoint`. No commands, events, or feature bits. `Feature` is declared as a type (lines 33-36) and no bit constants follow. Base server conformance `O` (schema line 2366). None of the three device files lists UserLabel. `go-fabric@v0.22.2:device/base.go` lines 168-174: mounted when a declaration names it.

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LabelList | attribute | `0x0000` | list of LabelStruct, min 0 | `M` | none of this group (cluster conformance on Base is `O`) | none in catalog | absent | no row | no source | no correspondence | access RW, read View, write Manage; quality NonVolatile; default empty list. Decode length 0 to 2147483647 (lines 68-70). Lines 77-87 |
| LabelList.Label | field | 0 | string, max 16 | `M` | none of this group (cluster is optional on Base) | none in catalog | absent | no row | no source | no correspondence | lines 39-41 and 64 |
| LabelList.Value | field | 1 | string, max 16 | `M` | none of this group (cluster is optional on Base) | none in catalog | absent | no row | no source | no correspondence | lines 41 and 65 |

## Identify `0x0003` revision 6

`go-fabric@v0.22.2:cluster/spec/identify/definition_gen.go` lines 21-26 and 163-165. Classification `endpoint`. No events. `Feature` is declared as a type (lines 40-43) and `Definition` has no `Features` slice.

Aggregator lists the cluster conformance `O` (`go-fabric@v0.22.2:device/aggregator_gen.go` lines 37-40). BridgedNode and RootNode device files do not list it. Schema requirements for those two device types do not list it either (BridgedNode lines 106-119, RootNode lines 151-218).

| element | kind | id | type / unit | conformance (as declared) | mandatory for which device types | SemReg element(s) that would feed it | catalog status at docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76: | target row disposition (+reason) | source status | loss | notes / locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IdentifyTime | attribute | `0x0000` | uint16 | `M` | none of this group (Aggregator conformance `O`; BridgedNode and RootNode do not list the cluster) | none in catalog | absent | no row | no source | no correspondence | access RW, read View, write Operate; quality Quieter. Lines 168-173 |
| IdentifyType | attribute | `0x0001` | IdentifyTypeEnum, 8 bits, constraint `desc` | `M` | none of this group | none in catalog | absent | no row | no source | no correspondence | access R View. Values, each conformance `M`: None 0, LightOutput 1, VisibleIndicator 2, AudibleBeep 3, Display 4, Actuator 5. Lines 95-113 and 175-180 |
| Identify | command | `0x00` | request, response `status` | `M` | none of this group | none in catalog | absent | no row | no source | no correspondence | access struct `RW: "R"`, read Manage, write Manage. Lines 183-192 |
| Identify.IdentifyTime | field | 0 | uint16 | `M` | none of this group (cluster is not mandatory for this group) | none in catalog | absent | no row | no source | no correspondence | lines 117-118 and 189 |
| TriggerEffect | command | `0x40` | request, response `status` | `O` | none of this group | none in catalog | absent | no row | no source | no correspondence | access struct `RW: "R"`, read Manage, write Manage. Lines 193-203 |
| TriggerEffect.EffectIdentifier | field | 0 | EffectIdentifierEnum, 8 bits, constraint `desc` | `M` | none of this group (parent command is optional, and the cluster is not mandatory here) | none in catalog | absent | no row | no source | no correspondence | values, each conformance `M`: Blink 0, Breathe 1, Okay 2, ChannelChange 11, FinishEffect 254, StopEffect 255. Lines 51-69 and 199 |
| TriggerEffect.EffectVariant | field | 1 | EffectVariantEnum, 8 bits, constraint `desc` | `M` | none of this group (parent command is optional, and the cluster is not mandatory here) | none in catalog | absent | no row | no source | no correspondence | one value, conformance `M`: Default 0. Lines 78-86 and 200 |

## Mandatory elements without a source

Every row below is mandatory for at least one device type of this group, under the applicability rule in the header, and has no catalog element at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:`. Globals are included because `go-fabric@v0.22.2:cluster/spec/instance.go` lines 15-22 say every server answers them, and the server is mandatory for the named device types. Their conformance text is not `M`.

Descriptor, mandatory for Aggregator, BridgedNode, and RootNode via Base conformance `M`:

- DeviceTypeList `0x0000`, and fields DeviceType and Revision.
- ServerList `0x0001`.
- ClientList `0x0002`.
- PartsList `0x0003`.
- GeneratedCommandList, AcceptedCommandList, EventList, AttributeList, FeatureMap, ClusterRevision.

BasicInformation, mandatory for RootNode. Definition revision 6:

- DataModelRevision, VendorName, VendorId, ProductName, ProductId, NodeLabel, Location, HardwareVersion, HardwareVersionString, SoftwareVersion, SoftwareVersionString, CapabilityMinima.
- CapabilityMinima fields CaseSessionsPerFabric, SubscriptionsPerFabric, and, because revision is 6, SimultaneousInvocationsSupported, SimultaneousWritesSupported, ReadPathsSupported, SubscribePathsSupported.
- UniqueId (`Rev >= v4, O` at revision 6).
- SpecificationVersion (`Rev >= v3`).
- MaxPathsPerInvoke (`Rev >= v3`).
- ConfigurationVersion (`Rev >= v6`).
- Event StartUp `0x00` and field SoftwareVersion.
- The six global attributes.

BridgedDeviceBasicInformation, mandatory for BridgedNode. Definition revision 6:

- Reachable.
- UniqueId (`Rev >= v4, O` at revision 6).
- Event ReachableChanged `0x03` and field ReachableNewValue.
- The six global attributes.

Identify, FixedLabel, and UserLabel contribute no element that is mandatory for Aggregator, BridgedNode, or RootNode. Identify is `O` on Aggregator. FixedLabel and UserLabel are `O` on Base.

Elements whose conformance is `O`, `X`, `desc`, `[Rev >= vN]`, or a feature name that these device types do not require are outside this list even when the cluster itself is mandatory. That includes BasicInformation Reachable, ProductAppearance, and the optional identity strings, and BridgedDeviceBasicInformation VendorName, VendorId, ProductId, ProductName, ConfigurationVersion, KeepActive, BIS, and ActiveChanged.

## Catalog elements of this domain without a Matter element

Searched the docs-semantic catalog at `docs-semantic@de3a0b49535582ad51a0ec23011d3aebf9c04c76:` for identity and label ids (`equipment.identification`, `equipment.label`) and read `resource.equipment` plus the `lenses` array. The compact TSV row for `resource.equipment` is line 45 and keeps `anchor_class` only. The admission object below is from `git show` of `api/v1/element-catalog-v1.json` lines 1416-1432. The semreg fixture at `semreg@69a9143a16a0e0b3d9d2c12e358b2aae5042ec89:` has `"id": "resource.equipment"` at the same line number and no `equipment.identification` or `equipment.label` match.

`resource.equipment` version 1.0.0, element kind `resource_kind`, disposition `member`, planes `physical`, `control`, `provenance`, attribute `anchor_class` `equipment`. Admission arm `matter_baseline`, evidence two URLs whose paths are `data_model/1.7/device_types/BridgedNode.xml` and `data_model/1.7/device_types/RootNodeDeviceType.xml` at commit `a commit id recorded in the cited file` of `AryaHassanli/connectedhomeip` (catalog lines 1424-1429). No target row (`git grep` of `resource.equipment` on the Matter target JSON returned no match). The element has no vendor, product, label, serial, or endpoint field. None of the six clusters has an element of kind `resource_kind`. BridgedNode `0x0013` and RootNode `0x0016` are device types in this group; the catalog element is not those device types.

Lenses at catalog lines 15693-15755, each with no target row:

| id | question in the catalog | planes | root kinds that include `resource.equipment` | max_depth |
| --- | --- | --- | --- | --- |
| `lens.installation_hierarchy` | What is installed here, what is part of what, and what is grouped or controlled together? | physical, control | yes, among six root kinds | 16 |
| `lens.equipment_composition` | What is this piece of equipment made of, and how healthy are its parts? | physical, diagnostic | yes, among six root kinds | 8 |
| `lens.provenance` | Through which equipment does this information arrive? | provenance | yes, among six root kinds | 8 |

No element in the six clusters is a lens. Descriptor PartsList is a list of endpoint numbers (`definition_gen.go` lines 229-235) and does not carry a question, root kinds, or `max_depth`.

`kernel.anchor_basis` (compact TSV line 4) values are `native_identity`, `native_slot`, `operator_slot`. `kernel.availability` (line 7) values are `available`, `degraded`, `unavailable`, `withdrawn`. Both are kernel lifecycle or evidence states. They are not listed here as domain elements: the value sets are those enums, and no cluster element in this group is that enum.

The a prior proposal ids named in the cluster tables are absent from the catalog, so they are not entries in this section.

## Disagreements with the prior accounting

a prior accounting, BasicInformation lines 64-91 and BridgedDeviceBasicInformation lines 141-170: each element's kind, id, and conformance text matches `definition_gen.go` for that cluster. Revisions in the headings (6 and 6) match the `Revision` constants. Feature BIS bit 20 and command KeepActive `0x80` and event ActiveChanged `0x80` match. No contradicted id or conformance text was found for those two clusters.

The prior accounting Reason cells for BridgedDeviceBasicInformation DataModelRevision, CapabilityMinima, LocalConfigDisabled, Location, MaxPathsPerInvoke, and SpecificationVersion (lines 141, 143, 146, 147, 149, 161) say "deprecated or disallowed". The generated conformance op on those attributes is `ConfDisallowed` with text `X` (`go-fabric@v0.22.2:cluster/spec/bridgeddevicebasicinformation/definition_gen.go` lines 387, 433, 515, 538, 554, 563). The file does not set `ConfDeprecated` on them.

The prior accounting Matter headings from line 10 through line 1047 include BasicInformation and BridgedDeviceBasicInformation and include no heading for Descriptor `0x001D`, FixedLabel `0x0040`, UserLabel `0x0041`, or Identify `0x0003`. Those four clusters are in go-fabric at the revisions cited above. The prior accounting has no element claim for them to contradict.

`a prior accounting` lines 5-7 limit that audit to HVAC, Energy, and Hydraulics. The row that names a cluster of this group is a prior claim (line 292): Heat Pump `0x0309` revision 1 has mandatory UserLabel. `go-fabric@v0.22.2:schema/devicetype_requirements_gen.go` lines 2030-2068: HeatPump revision 1 lists Identify conformance `O` directly. UserLabel conformance `M` is nested under device type Thermostat `0x0301`, whose own conformance is `O` (lines 2058-2061). The HeatPump requirements do not list UserLabel as a direct server cluster with conformance `M`.

## Uncertainty

- `a commit id recorded in the cited file` (cluster file headers) and `a commit id recorded in the cited file` (`go-fabric@v0.22.2:schema/levels_gen.go` line 17) are both stated beside Matter 1.6.1. No file read here says they are the same matter.js commit.
- Descriptor appears three ways: Base conformance `M`; a per-device-type requirement with no `Conformance` field; absent from `go-fabric@v0.22.2:device/aggregator_gen.go`, `go-fabric@v0.22.2:device/bridged_node_gen.go`, and `go-fabric@v0.22.2:device/root_node_gen.go`. `conformance.go` lines 208-209 map an empty conformance op to optional. This accounting did not find a validator call that applies that function to the empty per-device-type Descriptor requirement, so which record the device-type validator enforces is open. The mandatory column uses the Base text `M`, which `BaseDeviceTypes` documents as applying to every endpoint that lists a device type.
- `go-fabric@v0.22.2:device/doc.go` lines 33-35 say the assembler mounts Identify on every endpoint. The device-type requirements for BridgedNode and RootNode do not list Identify, and Aggregator lists it as `O`. This accounting treats device-type and Base requirements as the mandatory column, and leaves the assembler sentence as a mounting fact.
- `desc` is `ApplicabilityConditional` (`conformance.go` lines 226-227). What satisfies it for VendorName, VendorId, and ProductId on BridgedDeviceBasicInformation, for DataModelRevision's constraint, and for IdentifyType's constraint is not stated in the definition files.
- Identify, TriggerEffect, and KeepActive set `RW` to `R` and also set the Write privilege (Manage, Manage, and Operate). Locators: `go-fabric@v0.22.2:cluster/spec/identify/definition_gen.go` lines 187 and 197; `go-fabric@v0.22.2:cluster/spec/bridgeddevicebasicinformation/definition_gen.go` line 584. `go-fabric@v0.22.2:cluster/spec/model.go` lines 27-28: `RW` is `R`, `W`, `RW`, or `R[W]`, or empty. Lines 41-42: `Writable()` is false when `RW` is `R`. Lines 29 and 53-55: the Write field is the privilege required to write or to invoke. a prior accounting line 3 defines its access column as R read, W write, E event. KeepActive is W there (line 165). Identify and TriggerEffect have no prior accounting row (no Identify heading). The column legend does not say whether W copies the `RW` string or the Write field.
- Whether any driver feeds a future identity element is not visible from the catalog, the target, or go-fabric. Source status stays `no source`.
- `resource.equipment` admission evidence points at Matter 1.7 XML paths. How that 1.7 file relates to the go-fabric 1.6.1 device types `0x0013` and `0x0016` is not in the sources read here.
