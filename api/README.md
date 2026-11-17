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
spelling `<pack>.relation.<name>`. The identification-scheme and lens lists
are empty.

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

## Matter 1.6.1 target

The [Matter 1.6.1 adoption projection contract](v1/targets/matter-1.6.1-v1.md)
and [accounting ledger](v1/targets/matter-1.6.1-v1.json) derive the five-pack
roster from the element catalog, including services and relation definitions,
with one phase-qualified current projection and explicit irreversible loss. Source-model inspection is separate from execution qualification. This
pre-1.0 target does not activate the pinned feed or replace the historical
Matter 1.7 ledger and checker.
