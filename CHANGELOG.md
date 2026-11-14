---
status: "unreleased change record; implementation and consumer adoption remain pending."
---

# Changelog

## Unreleased

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
