# PV and inverter capability pack v1

`helianthus.pack.pv/v1` has exact PackRef `{id: "helianthus.pack.pv",
version: "1.0.0"}`. It is the accepted software-0.7 typed input over
`helianthus.semantic.kernel/v1`; its machine-significant catalog is
[pv-inverter-acceptance-vectors.json](pv-inverter-acceptance-vectors.json).
Every item is an exact versioned `DefinitionRef` under this PackRef.

## Fields and topology

The catalog defines canonical quantity fields for aggregate and per-input DC
voltage, current, and power; per-string DC energy; aggregate and per-phase AC
voltage, current and active power; per-phase apparent power and reactive
power; AC frequency; power factor; generated energy; inverter
temperature; and active-power and export-limit settings. The inverter totals
`pv.ac.aggregate_apparent_power` and `pv.ac.aggregate_reactive_power` are on
`pv.dimension.inverter`. They are distinct from the phase fields
`pv.ac.apparent_power` and `pv.ac.reactive_power`. Canonical units are
volt, ampere, watt, volt-ampere, volt-ampere reactive, hertz, joule, kelvin,
and ratio, under the
[unit rule](../../README.md#unit-rule): generated energy and string DC energy
are in joule, inverter temperature is in kelvin, and the bounds of generated
energy and inverter temperature are the exact conversions of their earlier
customary bounds. String DC energy uses the same joule bounds as generated
energy. Neither total is derived from the other. A customary unit appears only at display, in a
consumer. Operating,
derating, and fault fields use declared symbols only. Effective observation and
capability availability stays exclusively in kernel availability state; it is
not a PV symbol. `pv.status.operating` is a distinct native operating-readiness
fact and never encodes unavailable, withdrawn, stale, or unknown. Portal
consumes that kernel availability separately from promoted PV facts. Unknown,
withheld, unavailable, and operation outcomes remain kernel quality,
availability, and operation records, never symbols.

Fact-key dimensions are `pv.dimension.system`, `pv.dimension.inverter`,
`pv.dimension.array`, `pv.dimension.string`, `pv.dimension.input`, and
`pv.dimension.phase`. `pv.dimension.measurement_type` is a qualifier
dimension, not a fact-key dimension. `pv.accuracy.measured` is a boolean and
`pv.accuracy.ratio_maximum` is `unit.ratio` on `pv.dimension.inverter`. Both
are qualified by `pv.dimension.measurement_type`. The ratio bounds are empty.
This pack does not publish an Accuracy struct.

The corresponding services and explicit relation
definitions preserve system-to-inverter, inverter-to-array, array-to-string,
inverter-to-input, and inverter-to-phase records. Each of the five relation
definitions declares the cardinality `one_to_many` of
[graph section 7.2](../graph.md#72-relation-definitions), with `from`, `to`,
`cardinality` and `order` as in the other packs. A publisher MUST NOT flatten
per-string, per-input, per-phase, or richer native topology into an aggregate
record. Missing topology is unavailable evidence, not guessed membership.

The accepted catalog IDs are:

```text
pv.dc.voltage                     pv.dc.current
pv.dc.power                       pv.ac.voltage
pv.ac.current                     pv.ac.active_power
pv.dc.energy                      pv.ac.apparent_power
pv.ac.reactive_power
pv.dc.aggregate_voltage           pv.dc.aggregate_current
pv.dc.aggregate_power             pv.ac.aggregate_voltage
pv.ac.aggregate_current           pv.ac.aggregate_active_power
pv.ac.aggregate_apparent_power    pv.ac.aggregate_reactive_power
pv.ac.frequency                   pv.ac.power_factor
pv.energy.generated               pv.temperature.inverter
pv.energy.yield_day               pv.energy.yield_month
pv.energy.yield_year              pv.limit.active_power
pv.limit.active_power_ratio       pv.limit.export_power
pv.status.operating               pv.status.derating
pv.status.fault
pv.accuracy.measured              pv.accuracy.ratio_maximum
pv.dimension.measurement_type
pv.service.system                 pv.service.inverter
pv.service.array                  pv.service.string
pv.service.input                  pv.service.phase
pv.relation.system_inverter       pv.relation.inverter_array
pv.relation.array_string          pv.relation.inverter_input
pv.relation.inverter_phase
pv.capability.read.system         pv.capability.read.inverter
pv.capability.read.array          pv.capability.read.string
pv.capability.read.input          pv.capability.read.phase
pv.capability.set_active_power_limit
pv.capability.set_export_limit
pv.effect.set_active_power_limit  pv.effect.set_export_limit
pv.portal.read.system             pv.portal.read.inverter
pv.portal.read.array              pv.portal.read.string
pv.portal.read.input              pv.portal.read.phase
pv.portal.operation.set_active_power_limit
pv.portal.operation.set_export_limit
```

## Capability and operation boundary

A quantity carries closed minimum and maximum kernel `Decimal`
`{coefficient, exponent10}` bounds only when its fact table states both.
Empty bounds stay empty. `pv.accuracy.ratio_maximum` has both bounds empty.
`pv.ac.phase_power_factor` is closed from -1 to 1.
`pv.configuration.grid_code` is the eeBUS grid-code fact.
SunSpec grid-code settings have no element.
A new signed quantity names `pv.relation.inverter_array`.
Seed signed rows keep `native_convention`.
Those per-field values are part of this PackRef and cannot be broadened,
narrowed, or re-encoded under the same version.

Read capabilities require a qualified current binding. The only operations are
`pv.operation.set_active_power_limit` and `pv.operation.set_export_limit`.
The three yields are periods. The ratio is not the watt limit.
`pv.operation.set_active_power_limit` still takes `pv.limit.active_power`.
No release case is added. A verification level recorded beside an element
blocks nothing. No element is marked sensitive or hidden.
Each requires its exact field, capability, qualified active binding, current
generation, exact native route, and authority admission. An exact qualified
native owner may expose one of these routes; lack of such a route publishes no
operation. This contract supplies neither generic inverter enable/disable nor a
native write recipe.

Admission, dispatch, acknowledgement, readback, and terminal outcome are
separate. `applied` needs current-generation confirming readback using the
pack-owned exact effect rule. After possible dispatch or an indeterminate
handoff, blind retry is forbidden. Terminal outcomes are `rejected`,
`failed_no_contact`, `acknowledged_unverified`, `applied`, `no_effect`,
`conflict`, and `indeterminate`.

## Lifecycle, publication, and loss

Source epoch, driver generation, semantic revision, qualification, activation,
generation fencing, partial updates, stale/unknown evidence, and permitted
last-known-good retention remain independent. Publication requires exact source
epoch, current driver generation, exact semantic revision, and qualified active
capability. Partial publication changes only supplied valid fields; withdrawal
is explicit and generation-fenced. Stale or unknown evidence cannot promote,
authorize, or operate. Generated-energy counter reset or wrap requires native
evidence and is reported as loss or counter continuity evidence; it is never
inferred from a decreasing value.

Projection loss records native enums, precision/range, signed direction,
per-string/per-input/per-phase topology, counter reset/wrap, curtailment
reason, vendor extensions, unavailable fields, conflicts, and unsupported
operations. Projection cannot create a route, authority, capability, or fact.

## Measurement reference and aggregation boundary

The canonical unit does not establish an electrical reference, aggregation, or
sign convention. A qualified native mapping must identify the voltage/current
reference and phase basis it actually observes. Aggregate AC/DC fields retain a
native aggregation record; this pack does not assume scalar, vector, arithmetic
sum, average, or nameplate aggregation. Signed active power and power factor
retain the native direction/reference convention in evidence and expose any
unprojectable convention as explicit loss. Per-phase apparent power is
non-negative. Per-phase reactive power is signed under the native convention.
Neither is derived from active power. The inverter totals
`pv.ac.aggregate_apparent_power` (non-negative) and
`pv.ac.aggregate_reactive_power` (signed under the native convention) are
distinct from those phase fields, and neither total is derived from a phase
field. Candidate and unknown rows therefore
cannot be used to infer import/export direction or normalize phase measurements.

## Portal contribution descriptors

Read descriptors consume promoted fields for system, inverter, input, phase,
array, and string services. Operation descriptors expose an admitted current
operation affordance only. Portal consumes promoted definitions and current
admission; it does not define semantic truth, native routes, authority, or
lifecycle.

## Native mapping boundary

Inputs are semantic documentation `346cda9b675a03a7d1a8c886a3467eab84ce8fb2`,
semantic implementation `cc9b324225e945598128eeabe977e7fa0af6dc93`, Growatt
documentation `7ba9c333539c4381c06584cab0dc86c7e9280767`, Growatt registry
`7853d903970a4fdded35abaef01fe30f7e93be6a`, Fronius documentation
`f0292b6dee164b78c2ec06849e214839f55abd18`, Fronius registry
`1e2cea375f415847fb70cb8a181cdd1285543eca`, eeBUS ledger
`81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1`, eeBUS raw donor
`cedf238e34f879815ba773e9cd76b2b31c2822a3`, and Matter draft
`29b4768a513cf566011ab8cd60df1bc495204953`.

Growatt and Fronius rows are candidates only. The Fronius sources are offline
readiness candidates with `live_qualified=false` and no write authority.
Growatt TL3-X applicability and offsets 59--124 remain blocked by docs-modbus
#143 and modbusreg #196. Affected eeBUS mapping is `unknown_pending_normative_source`;
the Matter draft is not conformance. No mapping in this pack is normative or an
operation authority.

## Compatibility and validation

The full five-domain catalog has thermal/HVAC, PV/inverter, and storage/BMS
accepted, with EVSE and infrastructure as required follow-ons. This is typed
0.7 documentation only: it introduces no 0.8 IR, HWIR, code generation,
runtime, native driver, gateway, consumer, Portal UI, deployment, or live
action. The version rule of [api/README.md](../../README.md#version-rule)
applies, including its rule for in-place changes until the 0.7 release.

Run `python3 scripts/validate_pv_inverter_pack_v1.py`,
`python3 scripts/test_validate_pv_inverter_pack_v1.py`, and
`./scripts/check_docs.sh`. Corrections must reject a wrong PackRef or owner,
missing five-domain catalog, invalid canonical field/topology, unqualified
mapping, absent lifecycle/loss/counter coverage, generic enable/disable,
unadmitted operation, missing Portal coverage, or an invalid bound/order.

## Admitted identifiers

`pv.configuration.grid_code` is a catalog element on `pv.dimension.inverter`.
SunSpec grid-code settings have no element.
`pv.dimension.period` is day, month, year.
`pv.dimension.period_offset` is `unit.one` and stores no bound.

```text
pv.configuration.grid_code
pv.status.functional_states
pv.status.failure_states
pv.status.string_availability
pv.status.battery_availability
pv.status.grid_connection
pv.nameplate.production_nominal_maximum
pv.nameplate.consumption_nominal_maximum
pv.nameplate.apparent_production_nominal_maximum
pv.nameplate.apparent_consumption_nominal_maximum
pv.nameplate.peak_power
pv.string.power
pv.string.current
pv.string.voltage
pv.string.insulation_resistance
pv.string.tilt
pv.string.azimuth
pv.string.temperature
pv.energy.yield_history
pv.system.active_power
pv.energy.consumed
pv.energy.reactive_exported
pv.energy.reactive_imported
pv.energy.apparent_exported
pv.energy.apparent_imported
pv.ac.phase_power_factor
pv.ac.phase_energy_exported
pv.ac.phase_energy_imported
pv.dc.aggregate_energy
pv.moi.use_case_name
pv.mps.use_case_name
pv.vapd.use_case_name
pv.moi.actor
pv.mps.actor
pv.vapd.actor
pv.moi.use_case_version
pv.mps.use_case_version
pv.vapd.use_case_version
pv.moi.device_name
pv.moi.device_code
pv.moi.serial_number
pv.moi.software_revision
pv.moi.hardware_revision
pv.moi.vendor_name
pv.moi.vendor_code
pv.moi.moi_016b
pv.moi.manufacturer_label
pv.moi.moi_018
pv.moi.timestamp
pv.moi.moi_022
pv.moi.ec1
pv.mps.ec1
pv.vapd.ec1
pv.vapd.vapd_004
pv.moi.ac_yield_total
pv.moi.ac_yield_day
pv.moi.ac_yield_day_historical
pv.moi.ac_yield_month
pv.moi.ac_yield_month_historical
pv.moi.ac_yield_year
pv.moi.ac_yield_year_historical
pv.vapd.ac_power_total
pv.vapd.ac_yield_total
pv.dimension.period
pv.dimension.period_offset
```
