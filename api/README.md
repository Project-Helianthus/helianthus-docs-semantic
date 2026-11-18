# Semantic API publication status

## Kernel v1

The versioned kernel contract consists of:

- [typed records and invariants](v1/kernel.md);
- [deterministic JSON serialization](v1/serialization.md);
- [acceptance rules and stable errors](v1/acceptance.md);
- [resource graph, relations, planes, lenses and element catalog
  rules](v1/graph.md);
- [graph acceptance vectors](v1/graph-acceptance-vectors.json), checked by
  `scripts/validate_graph_v1.py`;
- [positive and negative acceptance vectors](v1/acceptance-vectors.json); and
- [detached PublicationKernel fork falsifiers](v1/kernel-fork-acceptance.json).

## Thermal/HVAC pack v1

The first accepted INT-04 capability pack is
[`helianthus.pack.thermal/v1`](v1/packs/thermal-hvac-v1.md). It supplies the
typed thermal/HVAC field, service, capability, operation, effect, lifecycle,
projection-loss, and Portal-contribution contract over the kernel. Its
[positive and negative vectors](v1/packs/thermal-hvac-acceptance-vectors.json)
are mechanically checked with `scripts/validate_thermal_hvac_pack_v1.py`.
Every thermal field names exactly one resource dimension, its subject, in an
SI unit of the [unit rule](#unit-rule), and the pack declares five relation
definitions; the accepted thermal placement of
[docs-semantic#68](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/68)
is applied in place.
Native eBUS and GREE rows remain candidate evidence owned by their native
documentation repositories. Affected eeBUS rows remain unknown pending STD-01.

## Storage/BMS pack v1

[`helianthus.pack.storage/v1`](v1/packs/storage-bms-v1.md) is the accepted
second typed capability pack at exact PackRef `1.1.0`. Its vectors are checked
by `scripts/validate_storage_bms_pack_v1.py`. Version 1.0.0 is superseded and
non-implementable for operations because its interlock was not machine-identifiable.
CAN V1.04 and RS-485 1xSxxP rows are offline candidate evidence only; eeBUS
remains `unknown_pending_normative_source`.

The [Growatt BMS RS-485 v2.02 mapping gate](v1/mappings/growatt-bms-rs485-v202-storage-v1.md)
freezes the accepted read-only source-specific field and lifecycle boundary for
later SemReg work. It does not activate consumer publication or control.

The [Tesla Gen3 WC3 24.44.3 EVSE current-limit mapping gate](v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md)
freezes the source-specific read-only mapping of persistent configured current
and an evidence-qualified provisional allocated current. It exposes no sender,
route, authority, consumer binding, or control.

The [Huawei SUN2000 PV mapping gate](v1/mappings/huawei-sun2000-pv-v1.md) maps the
admitted facts of the two offline monitoring profiles to the PV pack, with grades
inherited from the native contract and every other native item withheld or
native-only with a stated loss. The [LUNA2000 storage gate](v1/mappings/huawei-luna2000-storage-v1.md)
and the [gateway-meter Infrastructure gate](v1/mappings/huawei-gateway-meter-infrastructure-v1.md)
publish nothing today: no battery profile is admitted and no meter is decoded. They
record where the existing Storage and Infrastructure packs will take the facts, keep
capacity in energy units withheld, and expose no consumer binding or control.

Every mapping gate shares one set of graph rules, checked by
`scripts/mapping_gate_graph_rules.py` against the
[element catalog](v1/element-catalog-v1.json) under section 15 of the
[graph contract](v1/graph.md). A gate's `graph` member states its resource
kinds with anchor class, basis, source, identification scheme and parent kind;
its relation definitions with basis class, endpoint kinds, evidence, validity
scope and absence sides; its relayed units, joins, aggregates and native
interpretation selectors. The checker rejects an anchor source other than a
native token, native position or operator label (section 6.3), a kind or
relation definition that is not a catalog member or disagrees with it (RES-1,
RES-2, REL-1, REL-3), an endpoint kind the gate does not publish, a join of
observations whose native tokens differ or that rests on a label, ordinal or
address (section 6.4, RES-7), an aggregate without its catalog subject kind
(EN-1, EN-5), and any `planes` or `plane` member anywhere in the gate (PLN-1).
Each failure carries a stable error identifier and the offending path. A gate
without a `graph` member is reported as `graph_not_stated` and is not rejected
until its own change adds the member; no accepted gate states one yet.

## PV/inverter pack v1

[`helianthus.pack.pv/v1`](v1/packs/pv-inverter-v1.md) is the accepted third
INT-04 capability pack. It defines typed generation, electrical, energy,
state, topology, lifecycle, projection-loss, conservative power-limit operation,
and Portal-contribution contracts. Its [positive and negative
vectors](v1/packs/pv-inverter-acceptance-vectors.json) are checked by
`scripts/validate_pv_inverter_pack_v1.py`. Growatt and Fronius rows remain
candidate-only native-owner evidence; Fronius is offline-only with no write
authority. Growatt TL3-X applicability is blocked by docs-modbus #143 and
modbusreg #196. Affected eeBUS rows remain
`unknown_pending_normative_source`.

## EVSE pack v1

[`helianthus.pack.evse/v1`](v1/packs/evse-v1.md) is the accepted fourth
INT-04 capability pack. It defines typed connector/phase/session/meter topology,
telemetry, current-limit distinctions, lifecycle, loss, conservative
allocated-current operations, and Portal contributions. Its
[positive and negative vectors](v1/packs/evse-acceptance-vectors.json) are
checked by `scripts/validate_evse_pack_v1.py`. Tesla FBE0/FDE0 is offline
candidate evidence with no sender, control route, or live authority. eeBUS
remains `unknown_pending_normative_source`; the Matter draft is not conformance.

## Electrical infrastructure pack v1

[`helianthus.pack.infrastructure/v1`](v1/packs/infrastructure-v1.md) is the
accepted fifth INT-04 capability pack. It defines protocol-neutral electrical
site, grid-connection, feeder, circuit, phase, and meter topology; typed
telemetry and state; lifecycle and loss boundaries; and Portal read
contributions. Its [positive and negative vectors](v1/packs/infrastructure-acceptance-vectors.json)
are checked by `scripts/validate_infrastructure_pack_v1.py`. It publishes no
operation, breaker actuation, import/export control, sender, control route, or
live authority. eBUS and Modbus are non-universal evidence only, eeBUS remains
`unknown_pending_normative_source`, and Matter is not conformance.

Primary contract ID: `helianthus.semantic.kernel/v1`; the pure time-evaluation
view uses `helianthus.semantic.evaluation/v1`, and pure presentation results use
`helianthus.semantic.selection/v1`. Selection receives the complete matching
immutable snapshot and evaluation view; it has no hidden store or native lookup.
The contract becomes normative for the Project Helianthus kernel implementation
when merged into `main`. The owning Go module is
[`Project-Helianthus/helianthus-semreg`](https://github.com/Project-Helianthus/helianthus-semreg).

The kernel's retained-observation lifecycle contract is
[`api/v1/retained-observation-acceptance.json`](v1/retained-observation-acceptance.json).
It keeps pre-fence or retired-source observed evidence separately from current
facts through the original deadline, never as selection or operation authority.
A later source retirement advances a fenced binding tombstone to `retired` while
preserving the original retained candidate and its removal event.

The contract is complete for its kernel scope: identity/source/evidence,
protocol-neutral values and quality, facts and conflicts, services and
capabilities, immutable publication/snapshots, pure freshness evaluation,
multi-source derived dependencies, self-contained deterministic presentation
selection, exact precondition evidence, pack-owned
readback effects and definition dispatch, mandatory generation supersession,
operation evidence, causal budgets, projection loss, and compatibility aliases.
It deliberately contains no protocol/vendor/gateway import or arbitrary public
value bag.

## Family catalog v1

The [family catalog contract v1](v1/family-catalog-v1.md) defines the
`helianthus.semreg.family-catalog/v1` document: per-family `state` (the kernel
`Qualification` set), `composition`, `reason`, the capability packs of the
family (`semantic_pack` and the optional `further_semantic_packs`) and evidence
references. It is checked by `scripts/validate_family_catalog_v1.py` and states
no family's actual state; states live in the SemReg fixture with their evidence.

## Element catalog v1

The [element catalog](v1/element-catalog-v1.json) is the
`helianthus.semantic.element-catalog/v1` document of the
[graph contract](v1/graph.md) section 10. It lists every accepted element of
the five packs and of the kernel vocabulary with its plane membership or an
explicit `unknown` or `unsupported` disposition, and is checked against its
[schema](v1/element-catalog-v1.schema.json) by
`scripts/json_schema_subset_v1.py`. It was generated once from the accepted
packs by `scripts/generate_element_catalog_v1.py`, which also wrote the frozen
list of references that may carry the `accepted_pack` admission arm,
[`scripts/element-catalog-seed-refs.json`](../scripts/element-catalog-seed-refs.json).
From now on its entries change only by reviewed edits; the generator is not
re-run over reviewed decisions.
`scripts/validate_element_catalog_v1.py` checks the catalog independently of
the generator: it recomputes completeness, agreement with pack metadata,
dispositions, plane closure, ownership, admission arms, sign references,
canonical order and the identification-scheme rules (CAT-1 to CAT-9) from the
accepted pack documents, the seed reference list and the graph contract.
CAT-4 also rejects a second installation root.

No entry is `unknown`. The accepted thermal placement of
[docs-semantic#68](https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/68)
gives every thermal fact one subject, removes the four thermal qualifier
dimensions with their entries, adds the heat generator, thermal store,
terminal unit, refrigerant circuit and compressor kinds, the five thermal pack
relation definitions and the core definition `relation.thermal_control`, and
makes the circuit, hot-water and ventilation kinds with their dimensions,
services and read capabilities, and the set-temperature operation and its
effect rule, members. The hydraulic plane holds the fluid facts, the fluid
kinds and `thermal.relation.fluid_supply`. Relation identifiers use the pack
spelling `<pack>.relation.<name>`. The identification-scheme list is empty.
The lens list holds the four lenses of section 29, with relation definitions
left unnamed, and `resource.site` carries `installation_root`. The energy-flow
lens does not name `resource.storage_system`: that kind admits the physical
plane only, so it admits no energy plane (LNS-1).

## Graph acceptance vectors v1

The [graph acceptance vectors](v1/graph-acceptance-vectors.json) are the
`helianthus.semantic.graph.acceptance/v1` document of the
[graph contract](v1/graph.md) section 19. They record the path and SHA-256 of
the element catalog they were written against and cover the seven coverage
areas of section 19 through the operations `construct_registry`,
`register_catalog`, `apply`, `assemble_cut` and `admit`. Each vector names one
prior state, defined once in the document, one operation and one expectation:
the accepted result or the exact stable error. `scripts/validate_graph_v1.py`
checks the shape and repeated keys, the identifiers, a positive and a negative
vector per coverage area,
that every expected error is a documented heading, that every definition
reference resolves in the element catalog with the disposition the vector
assumes, that every anchor key is `sha256:` over the JCS bytes of its
`{scheme, issuer, token}` object, that every section 19 identifier has a
vector, and that the recorded catalog digest equals the file's. For a graph
cut it also recomputes every snapshot and cut identifier, checks the canonical
order of members, findings and relation coherence, and recomputes the plane
membership of every resource a member holds. The seed catalog lists no
identification scheme, so the vectors that need a native anchor key register
the synthetic scheme the document declares.
Coverage is complete: SemReg executes every graph vector by identifier with
the element catalog and every kernel vector without it.

## Remaining contracts

The accepted [immutable pack metadata v1](v1/pack-metadata-v1.md) exports exact
units, dimensions, ownership and operation shapes from the five accepted packs
for a future SemReg query API. It neither implements that API nor creates a
Gateway semantic table.

This publication completes the five typed INT-04 catalogs. Separately versioned
and reviewed contracts are still required for exact native mappings and
normative dispositions;
gateway composition; and target bindings. The accepted thermal, storage/BMS,
PV/inverter, EVSE, and infrastructure packs do not turn candidate native rows
into normative mappings.

Matter draft and eeBUS source gaps stay explicit. Affected mappings cannot
become normative merely because the kernel v1 types can represent them.

## Unit rule

Canonical units in the semantic registry are SI. A customary unit appears only
at display, in a consumer, and display conversion belongs to each consumer.
This rule is decided by the project owner. A pack field never declares a
customary or prefixed unit, and each pack validator checks the units of its
fields against the list below.

The strict reading of the rule is a working reading, not yet confirmed by the
project owner:

- kelvin (`unit.kelvin`) for temperature points and temperature differences;
- a ratio from 0 to 1 (`unit.ratio`) for a dimensionless quantity;
- cubic metre per second (`unit.cubic_metre_per_second`) for volume flow,
  pascal (`unit.pascal`) for pressure, reciprocal second
  (`unit.reciprocal_second`) for rotational speed, watt (`unit.watt`) for power
  and joule (`unit.joule`) for energy;
- hertz, volt, ampere, volt-ampere and var (`unit.hertz`, `unit.volt`,
  `unit.ampere`, `unit.volt_ampere`, `unit.volt_ampere_reactive`) unchanged.

Two parts are decided by the project owner: ampere-hour (`unit.ampere_hour`)
is kept as it is, and percent becomes a ratio from 0 to 1.

These conversions are exact: kelvin is degree Celsius plus 273.15 (a
temperature difference takes the factor 1 and no offset), a ratio is percent
divided by 100, joule is kilowatt-hour times 3 600 000, and pascal is bar
times 100 000. A mapping gate states each conversion as an exact factor and
offset for its pair of native unit and canonical unit, so that the canonical
value is the native value times the factor plus the offset. A conversion whose
factor is not 1 or whose offset is not 0 declares a `unit` loss, and the native
value and unit stay in the evidence. Where a factor does not terminate in
decimal (litre per minute divided by 60 000 to cubic metre per second, or
revolutions per minute divided by 60 to reciprocal second), the mapping gate
rounds half to even to a declared number of decimal places. The number of
places is chosen so that converting back and rounding to the native step
returns the native value.

The PV, EVSE and infrastructure packs and the
[PV](v1/mappings/huawei-sun2000-pv-v1.md) and
[gateway-meter](v1/mappings/huawei-gateway-meter-infrastructure-v1.md) gates
follow the rule, and so does the [thermal pack](v1/packs/thermal-hvac-v1.md),
which states the working reading as its own. The
[storage pack](v1/packs/storage-bms-v1.md) and the
[LUNA2000 storage](v1/mappings/huawei-luna2000-storage-v1.md) and
[Growatt storage](v1/mappings/growatt-bms-rs485-v202-storage-v1.md) gates follow
it too, with both capacities kept in ampere-hours. The element catalog has no
unit member.

## Version rule

An accepted API lives in an explicit versioned directory and states its status,
compatibility policy, owning implementation package, validation commands,
unresolved questions, and correction criteria. Until the Helianthus 0.7
release, the project owner may require a breaking change to be made in place in
an existing versioned directory; each such change is listed in this page's
in-place change record with its date, scope and the locks it moves. From the
0.7 release on, a breaking change requires a new major contract directory.
Illustrative planning sketches and conceptual examples outside an accepted
directory are not stable or executable API.

## In-place change record

Each in-place change made under the exception of the version rule before the
0.7 release is listed here, oldest first; the record closes at the release.

| Date | Change | Locks moved |
|---|---|---|
| 2026-11-14 | Version rule exception for the 0.7 release cycle; pack metadata "immutable" means read-only at run time; family-catalog compatibility applies from the release on; the ownership layering names the semantic resource graph; the PV, EVSE and infrastructure pack pages point to the version rule. | None: no vector, fixture, schema, digest or validator changes. |
| 2026-11-14 | Graph contract page [graph.md](v1/graph.md) added and the kernel, serialization and acceptance pages amended in place (graph.md section 17). | `scripts/validate_kernel_v1.py` and `scripts/test_validate_kernel_rules.py` take the documented error set as the union of the acceptance.md and graph.md headings; `api/v1/acceptance-vectors.json`, its `error_ids` and every pinned digest unchanged. |
| 2026-11-14 | The 21 pack relation definitions renamed in place to `<pack>.relation.<name>` under the member `relations` in the PV, EVSE and infrastructure pack vectors, the storage vectors and contract tables; the PV, hybrid-family storage and gateway-meter gates (the gateway-meter role member is `relation`), the pack and gate pages, the storage cell-voltage contract wording, the element catalog and its seed references follow. Every relation definition uses one encoding (`id`, `ref` where the pack vectors carry one, `from`, `to`, `cardinality`, `order`): the storage tables name their endpoints `from` and `to`, and the five PV definitions declare `one_to_many`. The thermal pack page states that it declares no relation definition. No alias of the earlier spelling remains. | The pack vectors of PV, EVSE, infrastructure and storage and the storage contract tables; `TABLE_SHA256` and the `COUNTS` key `relations` in `scripts/validate_storage_bms_pack_v1.py`; the four pack validators and the catalog validator and generator read `relations` and reject any other definition member, and the PV, hybrid-family storage and gateway-meter gate validators read `relations` (gateway-meter roles: `relation`) and reject the earlier members through their exact identity, role and output comparisons; the bytes of `api/v1/element-catalog-v1.json` and `scripts/element-catalog-seed-refs.json`; the PV, hybrid-family storage and gateway-meter gate JSON files. |
| 2026-11-14 | The family row of [family-catalog-v1.md](v1/family-catalog-v1.md) gains the optional member `further_semantic_packs`: 1 through 4 unique exact `PackRef` strings, none equal to `semantic_pack`, in canonical order after it, allowed only with a non-empty `semantic_pack` and omitted when empty, so every existing row keeps its bytes. No pack of a row is primary, and the row's packs include the pack of every accepted mapping gate of the family. `semantic_pack`, the state, composition and reason vocabularies and the evidence entry are unchanged. | The family-row member list pinned by `scripts/validate_family_catalog_v1.py` (from `family_id`, `name`, `native_owner`, `semantic_pack`, `state`, `composition`, `composition_verified`, `reason`, `evidence` to the same list with `further_semantic_packs` after `semantic_pack`), its pinned `semantic_pack` row and its packs-of-a-row statements, and `scripts/test_validate_family_catalog_v1.py`. The SemReg family-catalog fixture, decoder and mapping-gate cross-check follow in SemReg. |
| 2026-11-15 | The anchor of a native identity carries its scheme: a resource anchor with basis `native_identity` carries the member `scheme`, the identifier of a listed identification scheme equal to the `scheme` of the identity object its key digests, while issuer and token stay inside the digest; an anchor of another basis carries none. Rule RES-2 checks it ([graph.md](v1/graph.md), resource and identity sections; RES-2). | The bytes of `api/v1/graph-acceptance-vectors.json` (every `native_identity` anchor gains `scheme`; vectors G-NEG-ID-8 and G-NEG-ID-9 added). Its copies and digests in the typed kernel follow in the kernel's vector slice. |
| 2026-11-17 | The EVSE current-limit gate [tesla-gen3-wc3-24443-evse-current-limit-v1.json](v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.json) states its resources and relations in place under section 15 of [graph.md](v1/graph.md): a `graph` member names the charging station, EVSE and connector, each anchored by an operator label, and the station-to-EVSE and EVSE-to-connector relations with basis class `configuration`; `unstated_relations` records the connector-to-phase, connector-to-session and EVSE-to-meter relations as unknown, not absent. The identity values become gateway-allocated resource identifiers that name their pack dimension, and each field rule names its subject kind and measurement point (EN-1). No version is raised. | The gate JSON: `identity` (sources, the member `dimension`, three more forbidden derivations), `field_rules` (members `subject_kind` and `measurement_point`; source, target, dimension, unit and disposition unchanged), and the new members `graph` and `unstated_relations`; its page. In `scripts/validate_tesla_gen3_wc3_24443_evse_current_limit_mapping.py` the identity and field-rule constants move in place (subject kind and dimension are looked up in the element catalog) and graph constants are added; `scripts/test_validate_tesla_gen3_wc3_24443_evse_current_limit_mapping.py` gains the graph, identity and subject negatives. The gateway's mapping-gate check for this family pins this repository and follows in the family's gateway publication slice. |
| 2026-11-17 | The [Matter 1.6.1 roster](v1/targets/matter-1.6.1-v1.json) is derived in place from the [element catalog](v1/element-catalog-v1.json): it gains one row for each of the 29 services and 21 relation definitions of the five packs (177 rows in all), and the scope names the five requested kinds. The 127 existing rows keep their dispositions. The five electrical `measures` and `supplies` definitions are `withheld` against the Power Topology construct (equivalence Hypothesis; no endpoint is allocated), the other relation definitions are `unknown`, and services are `unsupported` because a service is not a kernel-v1 requested item; each declares an irreversible identity loss. The positive phase-qualified current row cites `evse.relation.connector_phase` in the member `relations` with reason `matter.phase_association_by_relation.v1` instead of declaring an identity loss. No version is raised. | The bytes and digest of `api/v1/targets/matter-1.6.1-v1.json` (`scope`, the new rows, the positive row's reason, loss and `relations`); `tests/test_matter161_target.py` derives its expected rows from the element catalog instead of pinned counts. The gateway's Matter projection pins the descriptor path and digest; that pin moves in the same in-place wave as helianthus-matter-binding#116. The historical Matter 1.7 ledger and its validator are unchanged. |
| 2026-11-17 | The [unit rule](#unit-rule) is stated: canonical units are SI, a customary unit appears only at display in a consumer, and its strict reading is a working reading. The PV, EVSE and infrastructure packs move to it in place: `pv.energy.generated`, `evse.energy.session`, `evse.energy.lifetime`, `infrastructure.energy.import` and `infrastructure.energy.export` in `unit.joule`, and `pv.temperature.inverter` in `unit.kelvin`, with bounds converted exactly. The PV and gateway-meter gates state each conversion as an exact factor and offset with a `unit` loss when it is not the identity. No version is raised; `unit.volt_ampere`, `unit.volt_ampere_reactive`, the thermal and storage packs and their gates, the EVSE current-limit gate, the relation definitions, the element catalog and both Matter rosters are unchanged. | The PV, EVSE and infrastructure pack vectors: each energy field from `unit.kilowatt_hour` with bounds 0 to 10^12 to `unit.joule` with bounds 0 to 3.6 x 10^18, and the PV inverter temperature from `unit.celsius` with bounds -50 to 200 to `unit.kelvin` with bounds 223.15 to 473.15; the field contracts of their three validators, which gain the SI unit set `CANONICAL_UNITS` and reject any other field unit; SemReg's byte copies and pins of these vectors follow. The PV, EVSE and infrastructure records of `api/v1/pack-metadata-v1.json` (SemReg's metadata registry test follows) and the matching unit names of `architecture/naming-contract.json`. The PV gate JSON: every quantity rule replaces its decimal shift member by `conversion` (factor and offset), the status rule carries none, the energy rule names `unit.joule` with factor 3 600 000 and a `unit` loss before its `policy` loss, and the expected outputs publish joule. The gateway-meter gate JSON: every prospective row gains `conversion` and `loss`, and the energy rows name `unit.joule`. In both gate validators the decimal-shift table becomes `UNIT_CONVERSION` from (native unit, canonical unit) to factor and offset; their pages gain the SI unit and conversion column. The documentation revision that the gateway's gate scripts pin follows in the gateway. |
| 2026-11-17 | The PV gate [huawei-sun2000-pv-v1.json](v1/mappings/huawei-sun2000-pv-v1.json) states its resources and relations in place under section 15 of [graph.md](v1/graph.md): a `graph` member names the gateway path as generic equipment, the inverter and the PV system anchored by an operator label, and the DC input and phase anchored by their native position; the relay of each inverter by its gateway path (basis class `native_observation`) and the system-to-inverter and inverter-to-input relations (`gate_rule`); one inverter seen through two paths joined only by an operator declaration; the inverter's power aggregates without coverage and the generated-energy aggregate covering the one system-to-inverter relation; and the profile identifier and the pack class token as provenance selectors. `unstated_relations` records the array, string, phase, battery and meter relations as unknown, not absent. The class token leaves identity: the home asset is gateway-allocated, and every fact-key dimension value and relation endpoint is a gateway-allocated resource identifier instead of dimension text. Each mapped field rule names its subject kind and measurement point (EN-1). No version is raised. | The gate JSON: `identity` (the asset source becomes `gateway_allocated_asset_id` without a derivation, its forbidden derivations gain `class_token` and `profile_id`, the member `resources` replaces `dimension_text` and `relations`, and the failure statement names reuse and ambiguity), `field_rules` (`dimension_text` gives way to `subject_kind` and `measurement_point`; target, dimension, unit, conversion, disposition and grade ceilings unchanged), the new members `graph` and `unstated_relations`, the baselines (synthetic asset identifiers without a class prefix and allocated resource identifiers), the expected outputs (fact keys and relation endpoints carry resource identifiers, relation records carry `definition` and `basis_class`, and the relay record and the `resources` list are added) and the vectors PV-NEG-022 and PV-NEG-023; its page. In `scripts/validate_huawei_sun2000_pv_mapping.py` the identity constants `ASSET_DERIVATION`, `DIMENSION_TEXT` and `IDENTITY_MEMBERS` give way to `IDENTITY_CONTRACT` and `RESOURCE_ROLES`, graph constants are added, and subject kinds, dimensions, kinds, parents, relation definitions and aggregations are looked up in the element catalog; `scripts/test_validate_huawei_sun2000_pv_mapping.py` gains the graph, identity and subject negatives. The gateway's mapping-gate check for this family reads the gate's `identity` member and pins this repository; it follows in the family's gateway publication slice. |
| 2026-11-17 | The accepted thermal placement is applied in place to the [thermal pack](v1/packs/thermal-hvac-v1.md): every thermal field declares exactly one resource dimension, its subject, and no qualifier dimension remains. `thermal.dimension.temperature`, `thermal.dimension.ratio`, `thermal.dimension.power` and `thermal.dimension.volumetric_flow` are removed; `thermal.measurement.water_temperature` is replaced by `thermal.measurement.circuit_flow_temperature` (thermal circuit) and `thermal.measurement.dhw_temperature` (domestic hot water); the power field is replaced by `thermal.measurement.thermal_power` (heat generator, signed, sign reference `thermal.relation.fluid_supply`); humidity moves to the zone. The heat generator, thermal store, terminal unit, refrigerant circuit and compressor kinds are added with their dimension, service, read capability and read descriptor, and with them the system, heat-generator, store, terminal-unit, refrigerant and compressor fields of the placement (32 fields, 10 services, 12 capabilities, 12 descriptors). Five pack relation definitions name their endpoint dimensions as lists; the core definition `relation.thermal_control` is added to the element catalog. Every quantity is in an SI unit of the [unit rule](#unit-rule): `unit.kelvin`, `unit.ratio`, `unit.cubic_metre_per_second`, `unit.pascal`, `unit.reciprocal_second`, `unit.watt` and `unit.joule`; `unit.celsius`, `unit.percent` and `unit.litre_per_minute` leave the pack. No version is raised and no alias is kept. | The thermal pack vectors (SemReg's byte copy and pin follow): the field, dimension, service, capability, relation and descriptor lists, the bounds converted to kelvin, ratio and cubic metre per second, the two index-based negative vectors re-pointed and five negative vectors added; the validator `scripts/validate_thermal_hvac_pack_v1.py` gains the field, unit, bound, relation and SI-unit contracts. The thermal record of `api/v1/pack-metadata-v1.json` (7 units, 65 definitions; SemReg's metadata registry test follows). The element catalog from 307 to 353 entries and from 26 `unknown` entries to none (SemReg's copy, pin and digest follow), with `resource.equipment` admitting the control plane; the graph vectors' recorded catalog digest, `G-POS-ACT-1` with no inadmissible operation, the vectors `G-POS-REL-6` and `G-NEG-RES-3` with their prior state, and `G-POS-CUT-10` keyed by the ventilation dimension in `unit.ratio` with its snapshot and cut identifiers recomputed (SemReg's copy and pin follow). Because the catalog has no `unknown` entry left, the prior states of `G-NEG-ACT-3`, `G-NEG-RES-1` and `G-POS-CUT-10` (the last in its own new state) register the catalog with one `catalog_mutations` entry that sets `thermal.operation.set_temperature`, `resource.thermal_circuit` or `thermal.demand.level` to `unknown` with a reason and tracking issue, and `scripts/validate_graph_v1.py` checks each vector's definitions, inadmissible operations and cut planes against the catalog as its prior state registers it (SemReg's graph runner follows by applying the mutation). `scripts/validate_element_catalog_v1.py` reads a pack relation endpoint as one dimension or a list of distinct dimensions, repeats `endpoint_dimensions` only when each side has one, and checks each side's endpoint kinds against the pack's endpoint dimensions; the fixed counts of its test and of `scripts/test_validate_pack_metadata_v1.py` (typed-reference probes 104 to 136) are recounted, and the 25 resolved readability baseline records of the two thermal scripts are removed. The Matter 1.6.1 roster from 177 to 211 rows and the Matter 1.7 roster from 127 to 151 rows by their derivation (the gateway's contract digest follows). The thermal rows of `architecture/naming-contract.json` from 61 to 110 and the count in `scripts/check_naming_contract.py`. The docs-ebus thermal map fixtures follow with their dispositions and units. |
| 2026-11-17 | The storage pack moves to the [unit rule](#unit-rule) in place: `storage.state.soc` and `storage.state.soh` in `unit.ratio` with bounds 0 to 1, `storage.energy.charged` and `storage.energy.discharged` in `unit.joule`, and `storage.temperature.pack` and `storage.temperature.cell` in `unit.kelvin` with a lower bound of 0; `storage.capacity.charge` and `storage.capacity.discharge` stay in `unit.ampere_hour`, as decided by the project owner. The storage validator rejects a field unit outside the SI set. The [LUNA2000 storage gate](v1/mappings/huawei-luna2000-storage-v1.md) and the [Growatt storage gate](v1/mappings/growatt-bms-rs485-v202-storage-v1.md) state each conversion as an exact factor and offset with a `unit` loss when it is not the identity. No version is raised; the cell-voltage contract, the other packs, the relation definitions and the element catalog are unchanged, and the field counts of the storage tables stay. | The storage pack vectors and contract tables (SemReg's byte copies and pins follow): the six moved fields from `unit.percent` with bounds 0 to 100, `unit.kilowatt_hour` with bounds 0 to unbounded and `unit.celsius` unbounded on both sides to `unit.ratio` with bounds 0 to 1, `unit.joule` with bounds 0 to unbounded and `unit.kelvin` with bounds 0 to unbounded. The contract-table digest `TABLE_SHA256` of `scripts/validate_storage_bms_pack_v1.py` moves, and the validator gains the SI unit set `CANONICAL_UNITS`. The storage record of `api/v1/pack-metadata-v1.json` (SemReg's metadata registry test follows) and the three storage unit names of `architecture/naming-contract.json`, which become `unit.ratio`, `unit.joule` and `unit.kelvin` with the row count unchanged. The LUNA2000 gate JSON: every quantity prospective row gains `conversion` and `loss`, state of charge names `unit.ratio` with factor 0.01 and the energy rows `unit.joule` with factor 3 600 000; its validator's decimal-shift table becomes `UNIT_CONVERSION`, and its page gains the SI unit, conversion and loss columns. The Growatt gate JSON: every quantity rule gains `native_unit` and `conversion`, state of charge names `unit.ratio` with factor 0.01 and the pack temperature `unit.kelvin` with offset 273.15, both now transformed with a `unit` loss, and the expected outputs publish 0.75 and 298.15; its validator gains `UNIT_CONVERSION` and checks each rule's unit against the storage contract tables. The documentation revision that the gateway's gate scripts pin follows in the gateway. |
| 2026-11-17 | The hybrid-family storage gate [huawei-luna2000-storage-v1.json](v1/mappings/huawei-luna2000-storage-v1.json) states its resources and relations in place under section 15 of [graph.md](v1/graph.md): a `graph` member names the inverter, the battery and the battery pack, each anchored by an operator label; the inverter's relay of the battery with basis class `configuration`, because no native owner documents the attachment as observable, and the battery-to-pack relation (`gate_rule`); the battery relayed by the inverter with no anchor key source for a direct view, so a second view of it joins only by an operator declaration; no aggregate; and the profile identifier and the pack class token as provenance selectors. `unstated_relations` records the module, cell, string, interface and storage-system relations as unknown, not absent. The class token and the profile identifier leave identity: the home asset is gateway-allocated, and the battery and its packs are gateway-allocated resource identifiers. Each prospective row names its subject kind and measurement point (EN-1). Nothing is published, and no version is raised. | The gate JSON: `identity` (the asset and source become gateway-allocated and managed with a stated granularity, the asset's forbidden derivations gain `class_token` and `profile_id`, the member `resources` replaces `storage_asset_granularity`, and the failure statement names reuse and ambiguity), the prospective rows of `field_rules` (members `subject_kind` and `measurement_point`; target, dimension, unit, conversion, loss, sign and counter unchanged), and the new members `graph` and `unstated_relations`; baselines and scenarios unchanged; its page. In `scripts/validate_huawei_luna2000_storage_mapping.py` the identity checks give way to `IDENTITY_CONTRACT` and `RESOURCE_ROLES`, the row member sets gain the two subject members, graph constants are added, the shared graph rules run first, and dimensions, subject kinds, kinds, relation definitions, directions, sign references and aggregations are looked up in the element catalog instead of the pack tables or the target name; `scripts/test_validate_huawei_luna2000_storage_mapping.py` gains the graph, false-join, dangling-endpoint, identity, subject and catalog-lookup negatives. No gateway publisher exists for this gate; the gateway's mapping-gate check for this family pins this repository and follows in the storage publication slice. |
| 2026-11-17 | The gateway-meter gate [huawei-gateway-meter-infrastructure-v1.json](v1/mappings/huawei-gateway-meter-infrastructure-v1.json) of the hybrid inverter family states its resources and relations in place under section 15 of [graph.md](v1/graph.md): a `graph` member names the site and the grid connection as functions and the meter as equipment, each anchored by an operator label; the site-to-grid-connection relation and the meter role as an instance of `infrastructure.relation.grid_connection_meter`, both with basis class `configuration` and held by the grid connection's home asset for the role (EN-8); no relay while the exposure path is unobserved; one meter seen through two paths joined only by an operator declaration; no aggregate; and the gateway path and the profile identifier as provenance selectors. A feeder or circuit role has neither an instance nor an absence statement, because the catalog has no `measures` definition for it, so its relation is unknown instead of `none_decided`. `unstated_relations` records the circuit-to-phase, feeder-to-circuit and grid-connection-to-feeder relations as unknown, not absent. Each prospective row names its subject kind and measurement point (EN-1), so power stays on the resource it is measured at and never moves to the device that reports it. Nothing is published, and no version is raised. | The gate JSON: in `role` the member `relation_by_role` replaces `dimension_by_role`, the prospective rows of `field_rules` gain `subject_kind` and `measurement_point` (target, dimension, unit, conversion, loss, sign, direction, counter and role unchanged), the new members `graph` and `unstated_relations`, and the expected role relation of the feeder vector from `none_decided` to `unknown`; its page. In `scripts/validate_huawei_gateway_meter_infrastructure_mapping.py` the constant `ROLE` loses `dimension_by_role` and the role check `role dimensions` and the grid-connection role rule give way to a lookup in the element catalog (each role's `measures` definition, each row's subject kind and dimension, the role placement in the outputs), graph constants are added and the shared graph rules run first; `scripts/test_validate_huawei_gateway_meter_infrastructure_mapping.py` gains the role-relation, subject, graph, false-join, dangling-endpoint and catalog-lookup negatives, and its role pins move from `none_decided` to `unknown`. No gateway publisher exists for this gate; the gateway's mapping-gate check for this family pins this repository and follows in the family's publication slice. |
| 2026-11-17 | The [storage gate](v1/mappings/growatt-bms-rs485-v202-storage-v1.json) of the low-voltage BMS family over RS-485 states its resource in place under section 15 of [graph.md](v1/graph.md): a `graph` member names the battery pack, anchored by an operator label, with no relation, no relayed unit and no aggregate, a join of a second view by operator declaration only, and the profile, native revision and routed unit number as provenance selectors; `unstated_relations` records every Storage relation as unknown, not absent. The value of the pack dimension in every fact key becomes the gateway-allocated resource identifier of the pack instead of the asset identifier, and each field rule names its subject kind and measurement point (EN-1). No version is raised. | The gate JSON: `identity` (the member `resources` with the pack role; `native_identity_evidence` loses `revision` and `unit_id`), `field_rules` (members `subject_kind` and `measurement_point`; source, target, unit, conversion and disposition unchanged), the new members `graph` and `unstated_relations`, the positive scenario's identity and the pack dimension value of its expected keys and those of the soft-start scenario, and one new negative scenario; its page. In `scripts/validate_growatt_bms_rs485_v202_storage_mapping.py` the field-rule member sets and the identity contract move in place, the pack dimension of a fact key and each rule's subject kind are looked up in the element catalog, graph constants are added and the shared graph rules run first; `scripts/test_validate_growatt_bms_rs485_v202_storage_mapping.py` gains the graph, identity, subject, fact-key and dangling-endpoint negatives. The gateway's mapping-gate check for this family pins this repository and follows in the family's publication slice. |
| 2026-11-17 | The storage pack gains the joule capacities `storage.energy.remaining`, `storage.energy.usable_capacity` and `storage.energy.nominal_capacity` on `storage.dimension.pack`, each optional, with minimum 0 and an unbounded maximum, aggregation member and direction non-negative. They sit with the joule counters `storage.energy.charged` and `storage.energy.discharged`. `storage.capacity.charge` and `storage.capacity.discharge` stay in `unit.ampere_hour`. No joule capacity is derived from an ampere-hour capacity. No service, capability or operation is added, and no version is raised. | The storage contract tables and acceptance vectors: three field specs, the three ids on `storage.portal.read.pack` immediately after `storage.energy.discharged`, and the interlock vector index. `scripts/validate_storage_bms_pack_v1.py` moves `field_specs` from 20 to 23 and the contract-table digest. The element catalog from 353 to 356 entries, its seed references, and the catalog digest recorded by the graph vectors. The storage record of `api/v1/pack-metadata-v1.json`. The Matter 1.7 pass line from 151 kernel-v1 rows (1 transformed, 150 unknown) to 154 kernel-v1 rows (1 transformed, 153 unknown), and three unknown fact rows on each Matter roster. The storage naming rows from 63 to 66. SemReg re-copies these bytes and does not invent the elements. |
| 2026-11-17 | The PV pack gains per-string DC energy `pv.dc.energy` in `unit.joule` on `pv.dimension.string`, minimum 0 and maximum the same coefficients as `pv.energy.generated`, aggregation member and direction non-negative, as the only field of `pv.portal.read.string`. It gains per-phase `pv.ac.apparent_power` in `unit.volt_ampere`, minimum 0 and maximum coefficient 1 exponent 7, direction non-negative, and `pv.ac.reactive_power` in `unit.volt_ampere_reactive` with the infrastructure reactive-power bounds, direction signed and sign reference `native_convention`. `pv.portal.read.phase` lists active power, apparent power, current, reactive power and voltage. `pv.energy.generated` stays on `pv.dimension.system`. Nothing derives string energy from system energy, or system energy from string energy. No service, capability or operation is added, and no version is raised. | The PV acceptance vectors: three fields, so the field count moves from 21 to 24, and the string and phase portal field lists. The PV validator field contracts and bounds. The element catalog from 356 to 359 entries, its seed references, and the catalog digest recorded by the graph vectors. The PV record of `api/v1/pack-metadata-v1.json`, including `unit.volt_ampere` and `unit.volt_ampere_reactive`. The Matter 1.7 pass line from 154 kernel-v1 rows (1 transformed, 153 unknown) to 157 kernel-v1 rows (1 transformed, 156 unknown), and three unknown fact rows on each Matter roster. The PV naming rows from 61 to 64. The pack-metadata typed-reference probe count from 136 to 140. SemReg re-copies these bytes and does not invent the elements. |
| 2026-11-17 | The infrastructure pack gains line-to-line voltage `infrastructure.ac.voltage_line_line` in `unit.volt` on `infrastructure.dimension.line_pair`, with the same bounds as `infrastructure.ac.voltage`, aggregation member and direction not applicable. The core kind `resource.line_pair`, the dimension and the service `infrastructure.service.line_pair` carry planes physical and energy. The read descriptor `infrastructure.portal.read.line_pair` lists only that field. `infrastructure.ac.voltage` stays on `infrastructure.dimension.phase`. No capability is added, and no version is raised. | The infrastructure acceptance vectors: one field, one dimension, one service and one read descriptor. `scripts/validate_infrastructure_pack_v1.py` gains the field contract and the line-pair dimension and service, and does not extend the capability set. The element catalog from 359 to 364 entries, its seed references, and the catalog digest recorded by the graph vectors. The infrastructure record of `api/v1/pack-metadata-v1.json`. The Matter 1.7 pass line from 157 kernel-v1 rows (1 transformed, 156 unknown) to 158 kernel-v1 rows (1 transformed, 157 unknown), one unknown fact row on that roster, and the service and fact rows on the Matter 1.6.1 roster. The infrastructure naming rows from 57 to 60. SemReg re-copies these bytes and does not invent the elements. |
| 2026-11-17 | The EVSE pack gains phase allocated current `evse.limit.allocated_current_phase` in `unit.ampere` on `evse.dimension.phase`, with the same bounds as `evse.limit.allocated_current`. The connector allocation stays on `evse.dimension.connector`. `evse.portal.read.phase` lists active power, current, voltage and the new field. `evse.operation.set_allocated_current`, its capability, its effect and its operation portal continue to name the connector field only. No service, capability or operation is added, and no version is raised. | The EVSE acceptance vectors: one field, so the field count moves from 15 to 16, field order 95 among the limits, and the phase portal field list. `scripts/validate_evse_pack_v1.py` gains the field contract and does not extend the operation. The element catalog from 364 to 365 entries, its seed references, and the catalog digest recorded by the graph vectors. The EVSE record of `api/v1/pack-metadata-v1.json`. The Matter 1.7 pass line from 158 kernel-v1 rows (1 transformed, 157 unknown) to 159 kernel-v1 rows (1 transformed, 158 unknown), and one unknown fact row on each Matter roster. The EVSE naming rows from 52 to 53. SemReg re-copies these bytes and does not invent the elements. |
| 2026-11-17 | Part 2 of the [graph contract](v1/graph.md), sections 23 to 36, defines retrieval and consumption in place on the same page: the served cut (CUT), entry points (ENT), bounded traversal (TRV), the lens result and sums (LRS, SUM), the four lens seeds, the generic read surfaces (API), Portal consumption (PTL), target reports over a named lens (TGT), consumer identity (CID) and native typed surfaces (NTV). `ProjectionManifest` gains the optional member `lens`. `ProjectionDisposition` gains the optional members `resources` and `relations`, both omitted when empty. `semreg/v1/graph` also owns traversal, lens retrieval and sums; `semreg/v1/projection` holds target records only and imports no pack. Serialization states the lens-result array orders. The acceptance class map names the retrieval refusals under the existing identifiers. The derived pack availability view is retired. The glossary defines served cut, traversal, frontier, lens result and consumer identity. No thermal quantity is placed, no thermal relation is defined and no hydraulic lens is seeded. No stable error is added and no version is raised. | `api/v1/graph.md`; `api/v1/kernel.md` (the member `lens` on `ProjectionManifest`, the members `resources` and `relations` on `ProjectionDisposition`, and the package surface); `api/v1/serialization.md` (the lens-result array orders); the class map of `api/v1/acceptance.md`, in place, with no new error heading; `api/v1/pack-availability-view.md`, retired. Kept unchanged: `api/v1/acceptance-vectors.json` and its four SHA-256 pins, the five stable graph errors, and every content-derived identifier. The element catalog, its schema and `api/v1/graph-acceptance-vectors.json` follow in the next slices. |
| 2026-11-17 | The [element catalog](v1/element-catalog-v1.json) seeds the four lenses of [graph.md](v1/graph.md) section 29 in place: `lens.installation_hierarchy`, `lens.energy_flow`, `lens.equipment_composition` and `lens.provenance`, each with the question, planes and depth of that section, and with relation definitions left unnamed. Root kinds are those of that section, except `resource.storage_system` is not a root of `lens.energy_flow`: it admits the physical plane only, so it admits no energy plane (LNS-1), and no kind's planes were changed. `resource.site` is the installation root. The [schema](v1/element-catalog-v1.schema.json) adds the optional boolean `installation_root` on a resource kind. The catalog validator rejects more than one installation root. No version is raised. | The bytes of `api/v1/element-catalog-v1.json` and `api/v1/element-catalog-v1.schema.json`. `scripts/validate_element_catalog_v1.py` gains the installation-root check. The `element_catalog` digest recorded by `api/v1/graph-acceptance-vectors.json` moves with the catalog bytes. SemReg follow-up: re-copy the catalog bytes and move its SHA-256 pin and catalog digest constant. |
| 2026-11-18 | The PV pack gains inverter-total apparent power `pv.ac.aggregate_apparent_power` in `unit.volt_ampere` on `pv.dimension.inverter`, minimum 0 and maximum the same bound as `pv.ac.aggregate_active_power`, aggregation aggregate and direction non-negative, and inverter-total reactive power `pv.ac.aggregate_reactive_power` in `unit.volt_ampere_reactive` on `pv.dimension.inverter`, signed, with the same bounds as `pv.ac.active_power`, aggregation aggregate, direction signed and sign reference `native_convention`. Both are fields of `pv.portal.read.inverter`. The phase fields `pv.ac.apparent_power` and `pv.ac.reactive_power` stay on `pv.dimension.phase`. No service, capability or operation is added, and no version is raised. | The PV acceptance vectors: two fields, so the field count moves from 24 to 26, and the inverter portal field list. The PV validator field contracts and bounds. The element catalog from 365 to 367 entries and its pack-reference count from 301 to 303, its seed references, and the catalog digest recorded by the graph vectors. The PV record of `api/v1/pack-metadata-v1.json`. The Matter 1.7 pass line from 159 kernel-v1 rows (1 transformed, 158 unknown) to 161 kernel-v1 rows (1 transformed, 160 unknown), and two unknown fact rows on each Matter roster. The PV naming rows from 64 to 66. SemReg re-copies these bytes and does not invent the elements. |

## Matter 1.6.1 target

The [Matter 1.6.1 adoption projection contract](v1/targets/matter-1.6.1-v1.md)
and [accounting ledger](v1/targets/matter-1.6.1-v1.json) derive the five-pack
roster from the element catalog, including services and relation definitions,
with one phase-qualified current projection and explicit irreversible loss. Source-model inspection is separate from execution qualification. This
pre-1.0 target does not activate the pinned feed or replace the historical
Matter 1.7 ledger and checker.
