---
status: "unreleased change record; implementation and consumer adoption remain pending."
---

# Changelog

## Unreleased

- The thermal pack stays `helianthus.pack.thermal` 1.0.0 and publishes the
  admitted generator and ventilation facts, `thermal.event.maintenance_due`,
  29 operations with one capability and one effect rule each, four qualifier
  dimensions, `resource.fan`, `resource.air_filter`, their dimensions and
  services, and the two read descriptors. `thermal.dimension.period` keeps
  day, month and year. `lifetime` is not a symbol. `thermal.dimension.purpose`
  and `thermal.dimension.louver_axis` stay out.
  `thermal.measurement.electrical_power` uses direction `not_applicable`
  because the pack admits no electrical supplies relation. Empty bounds stay
  empty. Overrun operations keep the status symbols active, finished, inactive
  and running, with no default-deny rule. `thermal.relation.fan_member` and
  `thermal.relation.filter_member` are not added. Two-vendor-only rows stay
  out. A fact may store symbols so the entered derived maintenance event can
  name `due`. New Matter 1.6.1 rows are unknown with `matter.unmapped.v1`. The
  two new services are unsupported with
  `matter.service_not_requested_item.v1`. `evse.ac.current` stays the only
  transformed row. The historical Matter 1.7 roster stays at 184 items. No
  pack version is raised.
- The thermal pack stays `helianthus.pack.thermal` 1.0.0 and publishes the
  admitted hydraulic, circuit and store facts, one qualifier dimension, five
  resource dimensions, five resource kinds, five services, and fifteen
  operations with one capability and one effect rule each. `resource.pump`,
  `thermal.dimension.pump` and `thermal.service.pump` keep physical,
  hydraulic and diagnostic and also carry energy and control.
  `thermal.measurement.pump_speed` stays hydraulic and diagnostic. Six
  changed events are catalog entries. Two domestic-hot-water boost events
  and seventeen pump alarm events stay out. Nine two-vendor-only fields
  stay out. Six hydraulic relations are not added. Empty bounds stay empty.
  New Matter 1.6.1 rows are unknown with `matter.unmapped.v1`. The five new
  services are unsupported with `matter.service_not_requested_item.v1`.
  `evse.ac.current` stays the only transformed row. The historical Matter
  1.7 roster stays at 184 items. No pack version is raised.
- The thermal pack stays `helianthus.pack.thermal` 1.0.0 and publishes the
  admitted zone, function and sensor facts, `resource.sensor`,
  `thermal.dimension.function`, `thermal.dimension.sensor`, four qualifier
  dimensions, `thermal.service.function`, `thermal.service.sensor`, two read
  capabilities, and twenty-three operations with one capability and one effect
  rule each. `thermal.mode.zone` gains `on` and keeps `comfort`. Five
  quantities the table marks signed use direction `not_applicable` because no
  supplies relation is named. The deadband stays 0 to 12.7. Three durations
  stay non-negative. Empty bounds stay empty. The maximum humidity fact stays
  out because the second vendor is unconfirmed. The sensor-to-zone relation is
  not added. Occupied and unoccupied heating and cooling setpoints keep their
  bytes. Eight changed events are catalog entries. New Matter 1.6.1 rows are
  unknown with `matter.unmapped.v1`. The two new services are unsupported with
  `matter.service_not_requested_item.v1`. `evse.ac.current` stays the only
  transformed row. The historical Matter 1.7 roster stays at 184 items. No
  pack version is raised.
- The energy-management pack stays `helianthus.pack.energy_management` 1.0.0
  and publishes the admitted tariff, price, incentive, grid and metering facts,
  `resource.tariff`, `energy.dimension.tariff`, twelve qualifier dimensions,
  `energy.service.tariff`, the direct-control and task-management fields, and
  six operations with one capability and one effect rule each. Prices recorded
  as `unit.currency_per_joule` stay that unit. Six quantities the table marks
  signed use direction `not_applicable` because this pack admits no supplies
  relation. Three quantities name no unit. Two changed events are catalog
  entries. No supplies relation is added. Empty bounds stay empty. New Matter
  1.6.1 rows are unknown with `matter.unmapped.v1`. The historical Matter 1.7
  roster stays at 184 items. No pack version is raised.
- The energy-management pack `helianthus.pack.energy_management` 1.0.0
  publishes the admitted subject facts, `energy.dimension.subject`, five
  qualifier dimensions, `energy.service.subject`, one read capability, and
  thirteen operations with one capability and one effect rule each. Six
  entered or left events stay out of the catalog because a fact stores no
  symbols. Eleven signed quantities use direction `not_applicable` until a
  supplies relation is admitted. Empty bounds stay empty. No element is
  marked sensitive or hidden. New Matter 1.6.1 rows are unknown with
  `matter.unmapped.v1`. The historical Matter 1.7 roster stays at 184
  items. No other pack is added and no pack version is raised.
- The EVSE pack publishes the 225 admitted use-case, actor, and scenario facts
  on `evse.dimension.connector`. Text facts are on the physical plane.
  `evse.cevc.heartbeat_timeout` is `unit.second` on the diagnostic plane with
  an empty minimum and a maximum of 60 s. `evse.opev.heartbeat_timeout` and
  `evse.oscev.heartbeat_timeout` are `unit.second` on the diagnostic plane
  with an empty minimum and a maximum of 4 s. No operation is added. The
  earlier rows stay. New Matter 1.6.1 rows are unknown with
  `matter.unmapped.v1`. The historical Matter 1.7 roster stays at 184 items.
  No pack version is raised.
- The EVSE pack publishes the admitted vehicle, session, limit, target and mode
  facts, the changed events `evse.event.fault` and `evse.event.rfid`, and eleven
  operations with their capabilities and effect rules. `resource.vehicle` and
  `evse.service.vehicle` are added. `evse.operation.set_allocated_current` and its
  set case stay. No release case is added. Four entered or left events stay out
  because a fact stores no symbols. Three signed quantities use direction
  `not_applicable` until an EVSE supplies relation is admitted.
  `evse.vehicle.approximate_efficiency` has no unit. Empty bounds stay empty.
  New Matter 1.6.1 rows are unknown with `matter.unmapped.v1`. The historical
  Matter 1.7 roster stays at 184 items. No pack version is raised.
- The storage pack publishes the admitted pack, interface and system facts,
  two fault events, and fifteen interface operations with their capabilities
  and effect rules. `storage.operation.set_ac_power`,
  `storage.operation.set_dc_power` and `storage.operation.set_pcc_power` keep
  the power argument and the ordered parameters `storage.setpoint.active` and
  `storage.setpoint.duration`. An eeBUS scenario may omit validity duration,
  a supplied duration starts counting at receipt, and explicit zero deactivates
  the setpoint. Omitted duration and explicit zero are distinct, and neither
  is a command execution deadline. Charge and discharge capacity stay
  `unit.ampere_hour`, as do the remaining and full-charge capacities. The two
  current limits and the interlock field stay as they are. Two-vendor-only
  rows stay out. The low-voltage CAN storage gate emits pack
  `storage.state.cycle_count` and does not emit the module-sourced count as
  that pack fact. The historical Matter 1.7 roster stays at 184 items. No pack
  version is raised.
- The PV pack and the infrastructure pack publish the remaining admitted
  `pv` and `infrastructure` rows. `pv.configuration.grid_code` is the eeBUS
  grid-code fact. SunSpec grid-code settings have no element. Two-vendor-only
  rows, the source-not-found power-settings operation, and the two load
  relations stay out. `infrastructure.portal.read.load` reads the load fields.
  `infrastructure.capability.read.load` is not added. Empty bounds stay empty.
  New signed quantities name `pv.relation.inverter_array` or
  `infrastructure.relation.feeder_circuit`. The eight pilot ids are unchanged.
  Each new fact is an unknown Matter 1.6.1 row with reason
  `matter.unmapped.v1`. `infrastructure.service.load` has one roster row,
  disposition `unsupported` and reason `matter.service_not_requested_item.v1`.
  The historical Matter 1.7 roster stays at 184 items. No pack version is raised.
- The thermal pack publishes `resource.room` and `thermal.dimension.room` on
  the physical, energy and control planes, with `thermal.service.room`,
  fifteen `thermal.room` facts, five room operations and their capabilities
  and effect rules, and the containment relations
  `thermal.relation.circuit_room`, `thermal.relation.circuit_zone` and
  `thermal.relation.zone_room`. Room quantities are `unit.kelvin` with no
  bounds. `thermal.relation.fluid_supply` stays a separate supplies relation
  and is not a physical parent. The Matter 1.6.1 roster gains the room facts,
  the read capability, the five write capabilities, the five operations, the
  service and the three relations. The historical Matter 1.7 roster stays at
  184 items. No pack version is raised.
- Active gateway-composition owner references use
  `Project-Helianthus/helianthus-gateway@<gateway-commit>`, and Matter
  registry references use `Project-Helianthus/helianthus-matterreg`
  (docs-semantic #154, issue #139).
- The [CAN storage mapping gate](api/v1/mappings/growatt-bms-can-storage-v1.md)
  of the low-voltage BMS family states, for each profile and native field, the
  storage element, dimension and conversion, or the package E element the
  field waits for. Profiles are the revision-labelled V1.04 contract, PCS
  standard, PCS extended, PCS gauge, PCS parallel and LINK. Percent becomes a
  ratio by division by 100, degree Celsius becomes kelvin by adding 273.15,
  a kilowatt-hour becomes joule by multiplication by 3 600 000, and an
  ampere-hour stays an ampere-hour. Voltage limits, cycle count, per-cell
  voltage, chemistry and insulation resistance wait for named elements the
  pack does not define yet. The charge-current and discharge-current ids are
  defined on `storage.dimension.pack`; the interface rows that name them stay
  waiting and are not emitted. No pack version is raised. No transmission is
  granted and no consumer binding is published.
- Breaking, in place before the 0.7 release: the
  [low-voltage BMS storage gate](api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md)
  maps the cell voltage extremes on one allocated cell. Remaining capacity
  and full-charge capacity stay withheld and name
  `storage.energy.remaining` and `storage.energy.usable_capacity`. The
  [PV monitoring gate](api/v1/mappings/huawei-sun2000-pv-v1.md) maps the
  current-day yield and publishes signed active power. Month and year yields
  stay prospective because the monitoring contract has no word for them. The
  [current-limit gate](api/v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md)
  takes configured current and allocated current from the provisional
  readback. No pack or contract version is raised.
- Breaking, in place before the 0.7 release: the
  [infrastructure pack](api/v1/packs/infrastructure-v1.md) adds
  self-consumption `infrastructure.energy.self_consumption` in `unit.joule`
  on `infrastructure.dimension.meter`, with the same bounds as
  `infrastructure.energy.import`. It adds point-of-coupling power
  `infrastructure.power.pcc` in `unit.watt` on
  `infrastructure.dimension.grid_connection`, signed, with the same bounds
  as `infrastructure.ac.active_power`. It adds the fallback grid limit
  `infrastructure.limit.fallback_power` in `unit.watt` on
  `infrastructure.dimension.grid_connection`, with the same bounds as
  `infrastructure.power.import_active`. Self-consumption is not the import
  counter. Point-of-coupling power is not the import/export pair. The
  fallback grid limit is not the PV export limit. No service, capability
  or operation is added. Pack metadata, the element catalog, both Matter
  rosters and the naming contract follow. SemReg follow-up: re-copy the
  pack bytes and do not invent the elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [PV pack](api/v1/packs/pv-inverter-v1.md) adds day, month and year yield
  `pv.energy.yield_day`, `pv.energy.yield_month` and `pv.energy.yield_year`
  in `unit.joule` on `pv.dimension.system`, with the same bounds as
  `pv.energy.generated`. The three yields are periods. It also adds
  `pv.limit.active_power_ratio` in `unit.ratio` on `pv.dimension.inverter`,
  from 0 to 1. The ratio is not the watt limit. `pv.energy.generated` and
  `pv.limit.active_power` stay, and `pv.operation.set_active_power_limit`
  still takes the watt argument. No service, capability or operation is
  added. Pack metadata, the element catalog, both Matter rosters and the
  naming contract follow. SemReg follow-up: re-copy the pack bytes and do
  not invent the elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [thermal pack](api/v1/packs/thermal-hvac-v1.md) adds pump speed
  `thermal.measurement.pump_speed` in `unit.reciprocal_second` on
  `thermal.dimension.pump`, with the same bounds as compressor speed, and
  valve position `thermal.measurement.valve_position` in `unit.ratio` on
  `thermal.dimension.terminal_unit`, from 0 to 1. Pump speed is not
  compressor speed. Valve position is not an overrun. The pump service has
  a read descriptor and no read capability. No capability or operation is
  added. Pack metadata, the element catalog, both Matter rosters and the
  naming contract follow. SemReg follow-up: re-copy the pack bytes and do
  not invent the elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [thermal pack](api/v1/packs/thermal-hvac-v1.md) adds four zone setpoints
  in `unit.kelvin`, `thermal.setpoint.occupied_heating`,
  `thermal.setpoint.occupied_cooling`, `thermal.setpoint.unoccupied_heating`
  and `thermal.setpoint.unoccupied_cooling`, with the same bounds as the
  single zone setpoint and distinct from it. System mode gains
  emergency_heat, precooling, fan_only, dry and sleep, and keeps auto, cool,
  heat and off. The set-temperature operation still takes only the single
  zone setpoint. No service, capability or operation is added. Pack metadata,
  the element catalog, both Matter rosters and the naming contract follow.
  SemReg follow-up: re-copy the pack bytes and do not invent the elements.
  No version is raised.
- Breaking, in place before the 0.7 release: the
  [thermal pack](api/v1/packs/thermal-hvac-v1.md) adds ten overrun statuses
  on the system dimension: `thermal.overrun.one_time_dhw`,
  `thermal.overrun.party`, `thermal.overrun.sg_ready_condition_1`,
  `thermal.overrun.sg_ready_condition_3`, `thermal.overrun.sg_ready_condition_4`,
  `thermal.overrun.one_day_away`, `thermal.overrun.one_day_at_home`,
  `thermal.overrun.one_time_ventilation`, `thermal.overrun.hvac_system_off`
  and `thermal.overrun.valve_kick`. Each is independently inactive, active,
  running or finished, and several can be active together. System mode, the
  zone setpoint and the domestic-hot-water setpoint stay. A one-time
  domestic-hot-water overrun is its own status. No service, capability or
  operation is added. Pack metadata, the element catalog, both Matter rosters
  and the naming contract follow. SemReg follow-up: re-copy the pack bytes and
  do not invent the elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [PV pack](api/v1/packs/pv-inverter-v1.md) adds inverter-total apparent
  power `pv.ac.aggregate_apparent_power` in volt-amperes and inverter-total
  reactive power `pv.ac.aggregate_reactive_power` in volt-amperes reactive,
  both on the inverter dimension. The apparent total is non-negative. The
  reactive total is signed. The phase fields `pv.ac.apparent_power` and
  `pv.ac.reactive_power` stay on the phase dimension. No service, capability
  or operation is added. Pack metadata, the element catalog, both Matter
  rosters and the naming contract follow. SemReg follow-up: re-copy the
  pack bytes and do not invent the elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [graph acceptance vectors](api/v1/graph-acceptance-vectors.json) add the
  twenty-one retrieval, lens-result, sum and target-report vectors of
  [graph contract](api/v1/graph.md) section 36. Coverage identifiers
  `retrieval`, `lens_result`, `sum` and `target_report` join the document, and
  operations `list_resources`, `traverse`, `retrieve_lens`, `sum_members` and
  `project` join it. A read is member snapshots plus a request. The validator
  recomputes the served cut identifier and the canonical order, and rejects a
  lens that is not in the catalog. A `list_resources` plane filter uses PLN-3
  membership: a current resource is listed only when PLN-3 places it in the
  requested plane. A lens resource carries the lens planes it is in. A lens
  result omits empty relations, facts, findings and frontier. A page token is
  a string bound to the cut identifier and to the digest of the request, and
  each recorded page is a lens result. A member sum over three inverters
  grouped by a system adds `pv.dc.power` and returns that scope's aggregate
  beside the sum. `G-NEG-RET-5` is the frontier bound: 4097 entries split
  across two assets, so each asset stays within the per-asset resource bound.
  Two further vectors
  cover the other branch of the two section 36 rows that state two cases:
  `G-NEG-RET-7` is a relation definition outside the requested planes, and
  `G-NEG-RET-8` is a page size above 4096. A projection report is the kernel
  report: the lens is `manifest.lens`, and each disposition carries its kind,
  item, outcome, source keys and loss. No stable error is added. No
  thermal quantity is placed. No version is raised. SemReg follow-up: re-copy
  this vector document and move its SHA-256 pin.
- Breaking, in place before the 0.7 release: the
  [element catalog](api/v1/element-catalog-v1.json) seeds the four lenses of
  [graph contract](api/v1/graph.md) section 29. Each lens carries that
  section's question, planes and depth, and names no relation definition, so
  it follows every member relation of its planes. Root kinds are those of
  that section, except `lens.energy_flow` does not name
  `resource.storage_system`: that kind admits the physical plane only, so it
  admits no energy plane (LNS-1). `resource.site` is the installation root.
  No kind's planes were changed to make a lens fit. The catalog schema adds the optional boolean `installation_root`
  on a resource kind, and the catalog validator rejects a second installation
  root. No version is raised. The graph acceptance vectors record the catalog
  digest of this seed. SemReg follow-up: re-copy the catalog bytes and move
  its SHA-256 pin and catalog digest constant.
- Breaking, in place before the 0.7 release: part 2 of the
  [graph contract](api/v1/graph.md) (sections 23 to 36) defines retrieval and
  consumption on the same page. A read is answered from one served cut. A
  traversal is bounded and records its frontier. A lens result is the canonical
  document of a lens retrieval, and sums of its member facts are withheld
  instead of presented as a total when coverage, identity, freshness or the
  cut is incomplete. Four lenses are named for later catalog admission. The
  generic read surfaces keep one answer on GraphQL and the semantic MCP
  namespace. Portal navigation comes from the catalog and from lens results.
  A target report may name the lens it accounts for and may cite the resources
  and relation instances it used. A consumer keys an object by resource, not
  by a path or a cut. No stable error is added. The derived pack availability
  view is retired: an asset outside the graph is `ungraphed`, and availability
  per element comes from the lens result. No thermal quantity is placed, no
  thermal relation is defined and no hydraulic lens is seeded. No version is
  raised. The element catalog and the graph acceptance vectors follow in the
  next slices.
- Breaking, in place before the 0.7 release: the
  [EVSE pack](api/v1/packs/evse-v1.md) adds phase allocated current
  `evse.limit.allocated_current_phase` in ampere on the phase dimension,
  with the same bounds as the connector allocation
  `evse.limit.allocated_current`. The connector allocation stays on the
  connector dimension. The phase read descriptor lists active power,
  current, voltage and the new field. No service, capability or operation
  is added, and `evse.operation.set_allocated_current` continues to name
  the connector field only. Pack metadata, the element catalog, both
  Matter rosters and the naming contract follow. SemReg follow-up:
  re-copy the pack bytes and do not invent the elements. No version is
  raised.
- Breaking, in place before the 0.7 release: the
  [infrastructure pack](api/v1/packs/infrastructure-v1.md) adds line-to-line
  voltage `infrastructure.ac.voltage_line_line` in volt on its own line-pair
  dimension. Phase voltage `infrastructure.ac.voltage` stays on the phase
  dimension. The line-pair kind, dimension and service are physical and
  energy. The line-pair read descriptor lists only the new field. No
  capability is added. Pack metadata, the element catalog, both Matter
  rosters and the naming contract follow. SemReg follow-up: re-copy the
  pack bytes and do not invent the elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [PV pack](api/v1/packs/pv-inverter-v1.md) adds per-string DC energy
  `pv.dc.energy` in joule on the string dimension, and per-phase apparent
  power `pv.ac.apparent_power` and reactive power `pv.ac.reactive_power`.
  System generated energy stays on the system dimension. Nothing derives
  one energy total from the other. No service, capability or operation is
  added. Pack metadata, the element catalog, both Matter rosters and the
  naming contract follow. The typed-reference probe count moves from 136
  to 140. SemReg follow-up: re-copy the pack bytes and do not invent the
  elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [storage pack](api/v1/packs/storage-bms-v1.md) adds the joule capacities
  `storage.energy.remaining`, `storage.energy.usable_capacity` and
  `storage.energy.nominal_capacity` on the pack dimension, beside the joule
  counters `storage.energy.charged` and `storage.energy.discharged`. Each is
  optional, with a minimum of 0 and an unbounded maximum. The charge and
  discharge capacities stay in `unit.ampere_hour`. No joule capacity is
  derived from an ampere-hour capacity. No service, capability or operation
  is added. Pack metadata, the element catalog, both Matter rosters and the
  naming contract follow. SemReg follow-up: re-copy the pack bytes and do
  not invent the elements. No version is raised.
- Breaking, in place before the 0.7 release: the
  [storage gate](api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md) of the
  low-voltage BMS family over RS-485 states its resource, join and selectors
  under section 15 of the [graph contract](api/v1/graph.md) and passes the
  shared graph rules. The battery pack is its only resource, anchored by an
  operator label. Every fact key carries the gateway-allocated resource
  identifier of the pack as the value of the pack dimension (RES-5), no longer
  the asset identifier. A key that carries the asset, source or binding
  identifier fails closed. The gate's evidence supports no relation, so it
  states none, and every Storage relation stays unknown, not absent. A
  module-to-cell relation keyed by a cell index without a published module is
  rejected as a dangling endpoint. The profile, the native revision and the
  routed unit number are selectors classed as provenance, and the routed unit
  number is no longer listed as identity evidence. Each field rule names its
  subject kind, looked up in the element catalog, and its measurement point
  (EN-1). Conversions, dispositions, policies and outcomes are unchanged.
  Gateway follow-up: the gateway's mapping-gate check for this family pins
  this repository and must allocate a resource identifier for the pack; it
  moves with the family's publication slice. No version is raised.
- Breaking, in place before the 0.7 release: the
  [gateway-meter gate](api/v1/mappings/huawei-gateway-meter-infrastructure-v1.md)
  of the hybrid inverter family states its resources, relations, join and
  selectors under section 15 of the [graph contract](api/v1/graph.md) and
  passes the shared graph rules. The site and the grid connection are
  functions and the meter is equipment, each anchored by an operator label. A
  meter's role is an instance of the grid-connection-to-meter `measures`
  relation with basis class `configuration`, held by the grid connection's
  home asset (EN-8), and the validator takes each role's relation from the
  element catalog instead of its own constants. A role stated without its
  instance, a role relation with a native-observation basis, a feeder relation
  whose endpoint the gate does not publish and a join over differing tokens are
  rejected. A feeder or circuit role has neither an instance nor an absence
  statement, so its relation is unknown, not absent. Each prospective row
  names its subject kind and measurement point (EN-1): power stays on the grid
  connection it is measured at, never on the device that reports it, and the
  energy counters stay on the meter. Nothing is published. Gateway follow-up:
  the gateway's mapping-gate check for this family pins this repository; it
  moves with the family's publication slice. No version is raised.
- Breaking, in place before the 0.7 release: the
  [LUNA2000 storage gate](api/v1/mappings/huawei-luna2000-storage-v1.md) of
  the hybrid inverter family states its resources, relations, relayed unit,
  join and selectors under section 15 of the
  [graph contract](api/v1/graph.md) and passes the shared graph rules. The
  battery and its pack are resources of their own, anchored by an operator
  label, instead of registers keyed through the inverter's asset. The inverter
  relays the battery, and its attachment is configuration because no native
  owner documents it as observable. The relaying path exposes no anchor key
  source for the battery, so a second view of it joins only by an operator
  declaration; a join by name or position and a module or cell relation are
  rejected. The module, cell, string, interface and storage-system relations
  stay unknown, not absent, and each prospective row names its subject kind and
  measurement point. Nothing is published. Gateway follow-up: the gateway's
  mapping-gate check for this family pins this repository; it moves with the
  family's storage publication slice. No version is raised.
- Breaking, in place before the 0.7 release: the
  [storage pack](api/v1/packs/storage-bms-v1.md) moves to the
  [unit rule](api/README.md#unit-rule), whose strict reading stays a working
  reading. State of charge and state of health are in `unit.ratio` with bounds
  0 to 1, charged and discharged energy in `unit.joule`, and the pack and cell
  temperatures in `unit.kelvin` with a lower bound of 0; the charge and
  discharge capacities stay in `unit.ampere_hour`, as decided by the project
  owner. The contract tables and vectors are converted exactly, the table digest
  of the storage validator moves, the field counts stay, and the validator
  rejects a field unit outside the SI set. The
  [LUNA2000 storage gate](api/v1/mappings/huawei-luna2000-storage-v1.md) and
  the [Growatt storage gate](api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md)
  state each conversion as an exact factor and offset per native and canonical
  unit pair, with a `unit` loss whenever the conversion is not the identity:
  percent to ratio by the factor 0.01, kilowatt to watt by the factor 1000,
  kilowatt-hour to joule by the factor 3 600 000 and degree Celsius to kelvin
  by the offset 273.15. The Growatt gate publishes state of charge and pack
  temperature as transformed facts. [Pack metadata](api/v1/pack-metadata-v1.json)
  and the [naming contract](architecture/naming-contract.json) follow. SemReg
  follow-up: its byte copies and pins of the storage vectors and contract
  tables and its metadata registry test move; gateway follow-up: the
  documentation revision pinned by its gate scripts moves. The cell-voltage
  contract, the other packs, the relation definitions and the element catalog
  are unchanged. No version is raised.
- Breaking, in place before the 0.7 release: the
  [thermal pack](api/v1/packs/thermal-hvac-v1.md) applies the accepted thermal
  placement. Every thermal field declares exactly one resource dimension, the
  subject of the fact, and the four quantity dimensions are removed. The water
  temperature is split into the circuit flow temperature of a thermal circuit
  and the hot-water temperature of the domestic hot water; thermal power is the
  signed thermal output of a heat generator, with the fluid-supply relation as
  its sign reference; humidity is a fact of the zone. The heat generator,
  thermal store, terminal unit, refrigerant circuit and compressor kinds are
  added with their services, read capabilities and read descriptors, and the
  pack declares five relation definitions; the element catalog adds the core
  thermal-control relation, has no `unknown` entry left, and the hydraulic
  plane is no longer empty. Every quantity is in an SI unit of the
  [unit rule](api/README.md#unit-rule), whose strict reading stays a working
  reading. Pack metadata, the graph vectors, both Matter rosters and the
  [naming contract](architecture/naming-contract.md) follow. SemReg and the
  gateway follow-ups: re-copy and re-pin the pack vectors, the element catalog
  and the graph vectors, and the Matter contract digest. The shared mapping-gate
  graph rules and their tests now take a kind that is outside the catalog by
  construction as their example of a non-member kind, since the thermal circuit
  kind is a member; the rule itself is unchanged. The element catalog
  validator reads a pack relation endpoint as one dimension or a list of
  distinct dimensions and checks each side's endpoint kinds against them. With
  no `unknown` entry left in the catalog, the three graph vectors over an
  `unknown` element (`G-NEG-ACT-3`, `G-NEG-RES-1`, `G-POS-CUT-10`) register the
  catalog with one stated `set_disposition` mutation in their prior state, and
  the graph validator checks them against the catalog as registered. No version
  is raised and no alias is kept.
- Breaking, in place before the 0.7 release: the
  [PV gate](api/v1/mappings/huawei-sun2000-pv-v1.md) states its resources,
  relations, relayed unit, join, aggregates and selectors under section 15 of
  the [graph contract](api/v1/graph.md) and passes the shared graph rules. Its
  fact keys and relation records carry gateway-allocated resource identifiers
  instead of dimension text, and each relation record names its definition and
  basis class. The pack class token and the profile identifier are provenance
  selectors and leave identity, so a hybrid inverter stays one inverter and one
  home asset. The array, string, phase, battery and meter relations stay
  unknown, not absent, and each mapped field rule names its subject kind and
  measurement point. Gateway follow-up: the gateway's mapping-gate check for
  this family reads the gate's `identity` member and pins this repository; it
  moves with the family's gateway publication slice. No version is raised.
- Breaking, in place before the 0.7 release: the [unit rule](api/README.md#unit-rule)
  states that canonical units in the semantic registry are SI and that a
  customary unit appears only at display, in a consumer; its strict reading is
  a working reading until the project owner confirms it. The
  [PV](api/v1/packs/pv-inverter-v1.md), [EVSE](api/v1/packs/evse-v1.md) and
  [infrastructure](api/v1/packs/infrastructure-v1.md) packs move to it:
  generated, session, lifetime, import and export energy are in `unit.joule`
  with bounds 0 to 3.6 x 10^18, and the inverter temperature is in
  `unit.kelvin` with bounds 223.15 to 473.15, each the exact conversion of the
  earlier bounds. Each pack validator rejects a field unit outside the SI set.
  The [PV gate](api/v1/mappings/huawei-sun2000-pv-v1.md) and the
  [gateway-meter gate](api/v1/mappings/huawei-gateway-meter-infrastructure-v1.md)
  state every conversion as an exact factor and offset per native and
  canonical unit pair instead of a decimal shift, with a `unit` loss whenever
  the conversion is not the identity; the PV gate publishes joule by the factor
  3 600 000. [Pack metadata](api/v1/pack-metadata-v1.json) and the
  [naming contract](architecture/naming-contract.json) follow. SemReg follow-up:
  its byte copies and pins of the three pack vectors and its metadata registry
  test move; gateway follow-up: the documentation revision pinned by its gate
  scripts moves. The thermal and storage packs and their gates, the EVSE
  current-limit gate, the relation definitions, the element catalog and both
  Matter rosters are unchanged. No version is raised.
- Breaking, in place before the 0.7 release: the
  [Matter 1.6.1 roster](api/v1/targets/matter-1.6.1-v1.json) is derived from
  the [element catalog](api/v1/element-catalog-v1.json). It gains one row for
  each of the 29 services and 21 relation definitions of the five packs, 177
  rows in all; the 127 existing rows keep their dispositions. The five
  electrical `measures` and `supplies` definitions are `withheld` against the
  Power Topology construct, whose equivalence stays a Hypothesis because no
  endpoint is allocated; the other relation definitions are `unknown`, and
  services are `unsupported` because a service is not a kernel-v1 requested
  item. Each new row declares an irreversible identity loss. The positive
  phase-qualified current row cites `evse.relation.connector_phase` instead of
  declaring an identity loss, with reason
  `matter.phase_association_by_relation.v1`. The
  [roster test](tests/test_matter161_target.py) computes its expected rows from
  the catalog instead of pinned counts. Gateway follow-up: the gateway's Matter
  projection pins this descriptor's path and digest, and that pin moves in the
  same in-place wave as helianthus-matter-binding#116. The historical Matter
  1.7 ledger is unchanged. No version is raised.
- Breaking, in place before the 0.7 release: the
  [EVSE current-limit gate](api/v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md)
  states its resources and relations under section 15 of the
  [graph contract](api/v1/graph.md). Its new `graph` member names the charging
  station, EVSE and connector, each anchored by an operator label because the
  native current-limit evidence carries no listed scheme, token or position,
  and the station-to-EVSE and EVSE-to-connector relations with basis class
  `configuration`; no session is published without a native session token.
  `unstated_relations` keeps the connector-to-phase, connector-to-session and
  EVSE-to-meter relations unknown, not absent. The asset, EVSE and connector
  identity values are gateway-allocated resource identifiers naming their pack
  dimension, never dimension text repeating the asset identifier, an address
  or a sorted ordinal. Each field rule names its subject kind and measurement
  point (EN-1); the validator runs the
  [shared checker](scripts/mapping_gate_graph_rules.py), looks subject kinds,
  dimensions and relation definitions up in the
  [element catalog](api/v1/element-catalog-v1.json), and its test rejects a
  connector numbered by sort order, an ordinal join, a station keyed by an
  address, a false join and a dangling endpoint. Gateway follow-up for this
  family: the gateway's mapping-gate check, which pins this repository, moves
  to these members in the family's gateway publication slice. No version is
  raised.
- Breaking, in place before the 0.7 release: the scheme of a native identity
  is carried on the anchor. A resource anchor with basis `native_identity` in
  the [graph contract](api/v1/graph.md) carries `scheme`, the identifier of an
  identification scheme of the element catalog's list, equal to the `scheme`
  of the identity object its key digests; issuer and token stay inside the
  digest, and the gateway answers for the consistency of the two. RES-2 now
  checks that the scheme is listed and that an anchor of another basis carries
  none (`invalid_value`).
  [`api/v1/graph-acceptance-vectors.json`](api/v1/graph-acceptance-vectors.json)
  adds the member to every `native_identity` anchor and gains G-NEG-ID-8 and
  G-NEG-ID-9. No version is raised.
- Add one shared checker for the resource, relation and identity statements
  every mapping gate makes under section 15 of the
  [graph contract](api/v1/graph.md).
  [`scripts/mapping_gate_graph_rules.py`](scripts/mapping_gate_graph_rules.py)
  reads the [element catalog](api/v1/element-catalog-v1.json) and checks a
  gate's `graph` member: anchor source, class, basis, scheme and parent kind of
  each published resource kind; definition, admitted basis class and published
  endpoint kinds of each relation; relayed units; joins, rejecting a false join
  and a join by label; aggregates and their catalog subject kind; interpretation
  selectors; and no plane member anywhere in the gate. It returns a stable error
  identifier and path per failure and has a `--self-test` mode.
  [`scripts/test_mapping_gate_graph_rules.py`](scripts/test_mapping_gate_graph_rules.py)
  covers a valid synthetic member and each rejection, and both run in
  `scripts/check_docs.sh`. A gate without a `graph` member is reported, not
  rejected; every gate file and validator, the element catalog and the pack
  documents are unchanged, and no lock moves.
- Breaking, in place before the 0.7 release: a family row of the
  [family catalog contract](api/v1/family-catalog-v1.md) may name every
  accepted capability pack its elements belong to. The optional member
  `further_semantic_packs` holds 1 through 4 unique exact `PackRef` strings,
  none equal to `semantic_pack`, sorted in canonical order after it. It is
  allowed only with a non-empty `semantic_pack` and omitted when empty, so every
  existing row keeps its bytes. No pack of a row is primary, and a row's packs
  must include the pack of every accepted mapping gate of its family.
  [`scripts/validate_family_catalog_v1.py`](scripts/validate_family_catalog_v1.py)
  pins the new member list, the unchanged `semantic_pack` row and these rules,
  and its test rejects each of them removed or weakened. `semantic_pack` and
  the state, composition and reason vocabularies are unchanged. A SemReg
  follow-up adds the member to the family-catalog fixture and decoder and adds
  the cross-check of rows against the accepted mapping gates.
- Add the publication vectors of PUB-3 in [`api/v1/graph.md`](api/v1/graph.md)
  to the [graph acceptance vectors](api/v1/graph-acceptance-vectors.json), in
  place: one prior state where the configuration provider publishes into a
  driver's asset as a second source, and three vectors. `G-POS-PUB-1`: a fence
  of the driver's generation removes the driver's gate-rule relation instance
  and keeps the provider's configured instance, whose starting end the driver
  observes (REL-5). `G-NEG-PUB-1`: a configured instance under a
  native-observation origin is `relation_not_qualified`. `G-NEG-PUB-2`: an
  identity link for the driver's binding published by the provider is refused
  with `invalid_value` by the kernel's batch ownership rule.
  [`scripts/validate_graph_v1.py`](scripts/validate_graph_v1.py) requires
  `G-POS-PUB-1` and `G-NEG-PUB-1` by identifier with their operation and
  expected error, and its mutation test covers both. The contract pages, the
  element catalog and the kernel vectors are unchanged.
- Complete the [graph acceptance vectors](api/v1/graph-acceptance-vectors.json)
  in place with 18 graph-cut and plane-membership vectors, so all seven
  coverage areas and every section 19 identifier are covered and SemReg
  executes every graph vector by identifier with the element catalog and every
  kernel vector without it.
- Add the graph acceptance vectors
  [`api/v1/graph-acceptance-vectors.json`](api/v1/graph-acceptance-vectors.json)
  (`helianthus.semantic.graph.acceptance/v1`) with their validator
  [`scripts/validate_graph_v1.py`](scripts/validate_graph_v1.py) and its
  mutation test. The 37 vectors cover activation, resources, relations, the
  element catalog and authority: every section 19 statement of those classes
  that uses `construct_registry`, `register_catalog`, `apply` or `admit`, the
  decode statement for an extra plane-scoped member, and the listed positives
  that need no graph cut. The document records the element catalog's path and
  SHA-256. `scripts/check_docs.sh` runs both new commands. Additive: the
  contract pages, the element catalog and the kernel vectors are unchanged.
  The graph-cut and plane-membership vectors follow in a later change.
- Breaking, in place before the 0.7 release: the 21 pack relation definitions
  are spelled `<pack>.relation.<name>` and listed under the member `relations`
  in the PV, EVSE, infrastructure and storage pack vectors and the
  [storage contract tables](api/v1/packs/storage-bms-contract-tables.json).
  Every relation definition uses one encoding (`id`, `ref` where the pack
  vectors carry one, `from`, `to`, `cardinality`, `order`): the storage tables
  name their endpoints `from` and `to` with unchanged values, and the five PV
  definitions declare `one_to_many`. The PV, hybrid-family storage and
  gateway-meter gates, the pack and gate pages, the storage cell-voltage
  contract, the [element catalog](api/v1/element-catalog-v1.json) and its seed
  references follow; the [thermal pack](api/v1/packs/thermal-hvac-v1.md) states
  that it declares no relation definition. The validators read only the new
  members and reject any other definition member, so no alias or migration
  path exists. The storage `TABLE_SHA256` and `COUNTS` key move; the change is
  listed in the [in-place change record](api/README.md#in-place-change-record).
  Consumers that copy the pack vectors or the storage tables re-copy them.
- Add the element catalog seed
  [`api/v1/element-catalog-v1.json`](api/v1/element-catalog-v1.json): 307
  entries generated once from the accepted packs and the kernel vocabulary by
  [`scripts/generate_element_catalog_v1.py`](scripts/generate_element_catalog_v1.py),
  with the frozen list of the 277 references that may carry the
  `accepted_pack` admission arm in
  [`scripts/element-catalog-seed-refs.json`](scripts/element-catalog-seed-refs.json).
  246 entries are members of at least one plane, 35 presentation entries are
  `unsupported`, and 26 thermal entries are `unknown`, in no plane, pending
  the thermal placement work of docs-semantic#68. The identification-scheme
  and lens lists are empty. `scripts/check_docs.sh` checks the catalog against
  its schema. Additive: no pack, vector, table, metadata or kernel change.
  Later entries change by reviewed edits; the cross-entry validator follows in
  a later change.
- The [semantic resource graph contract](api/v1/graph.md) of increment 1
  defines resources and their identity, typed relations, planes, lenses, the
  element catalog rules, activation, publication and coherence, and amends the
  kernel, serialization and acceptance pages in place. The five stable graph
  errors join the exhaustive v1 list. The new record members are optional and
  omitted when empty, so records without graph content keep their canonical
  bytes and identifiers, and the kernel vectors run unchanged without the
  catalog. Implementations follow in semreg and the gateway.
- Add the element catalog schema
  [`api/v1/element-catalog-v1.schema.json`](api/v1/element-catalog-v1.schema.json)
  for the contract `helianthus.semantic.element-catalog/v1`, and its
  repository-contained, dependency-free checker
  [`scripts/json_schema_subset_v1.py`](scripts/json_schema_subset_v1.py), which
  supports a fixed keyword subset including the conditionals and refuses every
  other keyword in a schema. Additive: no existing document, schema or
  validator changes. The catalog data and its cross-entry validator follow in
  later changes.
- Until the 0.7 release a breaking change may be made in place in an existing
  versioned directory, and each such change is listed in the new
  [in-place change record](api/README.md#in-place-change-record) of the
  [version rule](api/README.md#version-rule); from the release on a breaking
  change requires a new major directory. The PV, EVSE and infrastructure pack
  pages point to the version rule, the
  [pack metadata](api/v1/pack-metadata-v1.md) states that immutable means
  read-only at run time, the
  [family-catalog](api/v1/family-catalog-v1.md) compatibility rule applies from
  the release on, and the
  [ownership layering](architecture/repository-ownership-v1.md) names the
  semantic resource graph. No contract data, vector, fixture or validator
  changes; consumers need no action.
- Breaking: rename the three thermal value members as recorded in the
  [naming contract](architecture/naming-contract.md). Coordinate consumers in
  one wave; no alias or migration path is provided before 1.0.
- Breaking: rename the wire reason and eeBUS mapping state
  `unknown_pending_std_01` to `unknown_pending_normative_source` in the
  [family-catalog contract](api/v1/family-catalog-v1.md), the pack pages and
  acceptance vectors, their validators, the [API index](api/README.md) and the
  [donor ledger](compatibility/donor-ledger.md). The meaning is unchanged. The
  old spelling survives only as a documentary correspondence; no validator,
  fixture expectation or alias accepts it. Merge together with the matching
  SemReg rename; consumers move in the same wave.
