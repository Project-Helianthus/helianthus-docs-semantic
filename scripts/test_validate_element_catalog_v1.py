#!/usr/bin/env python3
"""Mutation tests of the element catalog validator against the committed catalog.

Every test copies the real catalog, applies one mutation and expects the
stable error of the rule that the mutation breaks. Cross-entry rules are
tested through ``check_rules`` so that a rejection proves the rule code, not
the schema; ``validate`` must reject every mutation as well.
"""
import contextlib
import copy
import io
import sys
import unittest

import json_schema_subset_v1 as subset
import validate_element_catalog_v1 as validator

CATALOG = subset.load_json(validator.CATALOG)
SCHEMA = subset.load_json(validator.SCHEMA)
INPUTS = validator.load_inputs()

FIELD = "evse.ac.voltage"
SIGNED_FIELD = "evse.ac.active_power"
SERVICE = "evse.service.connector"
OTHER_DIMENSION = "evse.dimension.evse"
CONTAINS_RELATION = "evse.relation.connector_phase"
PHYSICAL_ONLY_RELATION = "pv.relation.array_string"
REQUIRED_PLANE_RELATION = "evse.relation.asset_evse"
CROSSING_RELATION = "pv.relation.inverter_array"
FOREIGN_DIMENSION = "storage.dimension.battery"
CORE_KIND = "resource.equipment"
KERNEL_TYPE = "kernel.ack_state"
LENS_ROOT = "resource.pv_system"
# Section 29 seeds. Relation definitions stay unnamed. lens.energy_flow omits
# resource.storage_system: that kind admits physical only, so it admits no
# energy plane (LNS-1). Provenance roots are the equipment endpoints of
# relation.relays, the six equipment kinds.
SEEDED_LENSES = (
    {
        "id": "lens.installation_hierarchy",
        "question": "What is installed here, what is part of what, and what is grouped or controlled together?",
        "planes": ["physical", "control"],
        "root_kinds": [
            "resource.site", "resource.pv_system", "resource.storage_system", "resource.thermal_system",
            "resource.charging_station", "resource.equipment",
        ],
        "max_depth": 16,
    },
    {
        "id": "lens.energy_flow",
        "question": "Where does electrical energy flow and where is it measured?",
        "planes": ["energy"],
        "root_kinds": [
            "resource.site", "resource.grid_connection", "resource.pv_system", "resource.charging_station",
        ],
        "max_depth": 16,
    },
    {
        "id": "lens.equipment_composition",
        "question": "What is this piece of equipment made of, and how healthy are its parts?",
        "planes": ["physical", "diagnostic"],
        "root_kinds": [
            "resource.inverter", "resource.battery", "resource.battery_pack", "resource.charging_station",
            "resource.meter", "resource.equipment",
        ],
        "max_depth": 8,
    },
    {
        "id": "lens.provenance",
        "question": "Through which equipment does this information arrive?",
        "planes": ["provenance"],
        "root_kinds": [
            "resource.battery", "resource.battery_pack", "resource.charging_station", "resource.equipment",
            "resource.inverter", "resource.meter",
        ],
        "max_depth": 8,
    },
)
# One member kind per lens that admits none of that lens's planes.
OUTSIDE_LENS_PLANE = {
    "lens.installation_hierarchy": "resource.feeder",
    "lens.energy_flow": "resource.storage_system",
    "lens.equipment_composition": "resource.feeder",
    "lens.provenance": "resource.heat_generator",
}
SCHEME_ADMISSION = {"arm": "public_registry", "evidence": ["https://example.org/registries/synthetic"]}
THERMAL_PAGE = "api/v1/packs/thermal-hvac-v1.md"
THIS_REPO_PAGES = {
    "api/v1/kernel.md",
    "api/v1/packs/evse-v1.md",
    "api/v1/packs/infrastructure-v1.md",
    "api/v1/packs/pv-inverter-v1.md",
    "api/v1/packs/storage-bms-v1.md",
    "api/v1/packs/thermal-hvac-v1.md",
}
OVERRUN_FACTS = (
    "thermal.overrun.hvac_system_off",
    "thermal.overrun.one_day_at_home",
    "thermal.overrun.one_day_away",
    "thermal.overrun.one_time_dhw",
    "thermal.overrun.one_time_ventilation",
    "thermal.overrun.party",
    "thermal.overrun.sg_ready_condition_1",
    "thermal.overrun.sg_ready_condition_3",
    "thermal.overrun.sg_ready_condition_4",
    "thermal.overrun.valve_kick",
)
OCCUPANCY_SETPOINTS = (
    "thermal.setpoint.occupied_cooling",
    "thermal.setpoint.occupied_heating",
    "thermal.setpoint.unoccupied_cooling",
    "thermal.setpoint.unoccupied_heating",
)
HYDRAULIC_MEMBERS = (
    "resource.pump",
    "thermal.dimension.pump",
    "thermal.service.pump",
    "thermal.measurement.pump_speed",
    "thermal.measurement.valve_position",
    "thermal.portal.read.pump",
)
# One relation definition of each pack that declares relations.
PACK_RELATIONS = ("pv.relation.inverter_array", "evse.relation.evse_connector",
                  "infrastructure.relation.feeder_circuit", "storage.relation.pack_module",
                  "thermal.relation.generator_compressor")
# Thermal relations with one endpoint kind on each side, and with several on one side.
SINGLE_ENDPOINT_RELATION = "thermal.relation.generator_compressor"
MULTI_ENDPOINT_RELATION = "thermal.relation.fluid_supply"
VECTOR_FILES = tuple(validator.ROOT / path for path in validator.ACCEPTED_PACK_SOURCES
                     if path != validator.STORAGE_SOURCE)
THERMAL_VECTORS = VECTOR_FILES[0]
# The member name used before the in-place rename, assembled so that no file spells it.
EARLIER_MEMBER = "relation" + "ships"


def evidence_links(catalog):
    records = list(catalog["planes"]) + list(catalog["core_relation_types"])
    records += list(catalog["identification_schemes"]) + list(catalog["elements"])
    for record in records:
        yield from record["admission"]["evidence"]


def entry_of(catalog, ident):
    matches = [entry for entry in catalog["elements"] if entry["ref"]["id"] == ident]
    if len(matches) != 1:
        raise AssertionError(f"{ident}: expected one entry, found {len(matches)}")
    return matches[0]


def ref_of(catalog, ident):
    return copy.deepcopy(entry_of(catalog, ident)["ref"])


def resort(catalog):
    catalog["elements"].sort(key=validator.order_key)


def mutate_copy(mutate):
    catalog = copy.deepcopy(CATALOG)
    mutate(catalog)
    return catalog


def remove(catalog, ident):
    catalog["elements"].remove(entry_of(catalog, ident))


def add_copy(catalog, ident, new_ident):
    clone = copy.deepcopy(entry_of(catalog, ident))
    clone["ref"]["id"] = new_ident
    catalog["elements"].append(clone)
    resort(catalog)
    return clone


def scheme(ident):
    return {"id": ident, "issuer_registry": "none", "token_form": "synthetic token",
            "admission": copy.deepcopy(SCHEME_ADMISSION)}


class CommittedCatalog(unittest.TestCase):
    def test_committed_catalog_passes(self):
        self.assertEqual(validator.validate(copy.deepcopy(CATALOG), INPUTS, SCHEMA), [])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(validator.main(), 0)
        self.assertTrue(output.getvalue().startswith("PASS: element catalog CAT-1..CAT-9: 998 entries"))

    def test_same_repository_pages_are_relative_paths(self):
        relative = []
        issues = []
        other = []
        for link in evidence_links(CATALOG):
            self.assertIsNone(validator.repository_evidence_problem(link), link)
            if link.startswith("https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/"):
                issues.append(link)
            elif link.startswith("https://"):
                self.assertNotIn("helianthus-docs-semantic", link)
                other.append(link)
            else:
                path = link.split("#", 1)[0]
                self.assertEqual(link, path)
                self.assertTrue((validator.ROOT / path).is_file(), link)
                relative.append(link)
        self.assertEqual(set(relative), THIS_REPO_PAGES)
        self.assertTrue(issues)
        self.assertTrue(any("connectedhomeip" in link for link in other))
        contract = validator.GRAPH_PAGE.read_text(encoding="utf-8")
        self.assertIn(
            "A relative reference resolves against the repository revision that carries the catalog.",
            contract,
        )

    def test_overrun_evidence_is_a_document_link(self):
        for ident in OVERRUN_FACTS:
            evidence = entry_of(CATALOG, ident)["admission"]["evidence"]
            self.assertEqual(evidence, [THERMAL_PAGE], ident)

    def test_occupancy_setpoint_evidence_is_a_document_link(self):
        for ident in OCCUPANCY_SETPOINTS:
            evidence = entry_of(CATALOG, ident)["admission"]["evidence"]
            self.assertEqual(evidence, [THERMAL_PAGE], ident)

    def test_pump_and_valve_evidence_is_a_document_link(self):
        for ident in HYDRAULIC_MEMBERS:
            evidence = entry_of(CATALOG, ident)["admission"]["evidence"]
            self.assertEqual(evidence, [THERMAL_PAGE], ident)

    def test_yield_and_ratio_evidence_matches_the_sibling(self):
        generated = entry_of(CATALOG, "pv.energy.generated")["admission"]["evidence"]
        watt_limit = entry_of(CATALOG, "pv.limit.active_power")["admission"]["evidence"]
        for ident in ("pv.energy.yield_day", "pv.energy.yield_month", "pv.energy.yield_year"):
            self.assertEqual(entry_of(CATALOG, ident)["admission"]["evidence"], generated, ident)
        self.assertEqual(entry_of(CATALOG, "pv.limit.active_power_ratio")["admission"]["evidence"], watt_limit)

    def test_grid_member_evidence_matches_the_sibling(self):
        imported = entry_of(CATALOG, "infrastructure.energy.import")["admission"]["evidence"]
        import_active = entry_of(CATALOG, "infrastructure.power.import_active")["admission"]["evidence"]
        self.assertEqual(entry_of(CATALOG, "infrastructure.energy.self_consumption")["admission"]["evidence"], imported)
        for ident in ("infrastructure.power.pcc", "infrastructure.limit.fallback_power"):
            self.assertEqual(entry_of(CATALOG, ident)["admission"]["evidence"], import_active, ident)
        coupled = entry_of(CATALOG, "infrastructure.power.pcc")["attributes"]
        self.assertEqual(coupled["direction"], "signed")
        self.assertEqual(coupled["sign_reference"], "native_convention")
        self.assertEqual(coupled["subject"]["dimension"]["id"], "infrastructure.dimension.grid_connection")
        fallback = entry_of(CATALOG, "infrastructure.limit.fallback_power")["attributes"]
        self.assertEqual(fallback["direction"], "non_negative")
        self.assertNotIn("sign_reference", fallback)
        consumed = entry_of(CATALOG, "infrastructure.energy.self_consumption")["attributes"]
        self.assertEqual(consumed["direction"], "non_negative")
        self.assertEqual(consumed["subject"]["dimension"]["id"], "infrastructure.dimension.meter")

    def test_pilot_facts_schemes_and_absent_chemistry(self):
        present = {entry["ref"]["id"] for entry in CATALOG["elements"]}
        self.assertNotIn("storage.attribute.chemistry", present)
        battery_type = entry_of(CATALOG, "storage.configuration.battery_type")
        self.assertEqual(battery_type["element_kind"], "fact")
        self.assertEqual(battery_type["admission"]["arm"], "eebus")
        self.assertEqual(battery_type["attributes"]["value_kind"], "symbol")
        self.assertEqual(battery_type["attributes"]["subject"]["dimension"]["id"], "storage.dimension.pack")
        self.assertEqual(battery_type["attributes"]["direction"], "not_applicable")
        for ident in ("storage.limit.charge_current", "storage.limit.discharge_current"):
            entry = entry_of(CATALOG, ident)
            self.assertEqual(entry["element_kind"], "fact")
            self.assertEqual(entry["planes"], ["energy"])
            self.assertEqual(entry["admission"]["arm"], "two_vendors")
            subject = entry["attributes"]["subject"]
            self.assertEqual(subject["dimension"]["id"], "storage.dimension.pack")
            self.assertEqual(subject["kind"], "resource.battery_pack")
            self.assertNotIn("qualifiers", entry["attributes"])
            self.assertEqual(entry["attributes"]["value_kind"], "quantity")
            self.assertEqual(entry["attributes"]["direction"], "non_negative")
        for ident in ("pv.accuracy.measured", "infrastructure.accuracy.measured"):
            attributes = entry_of(CATALOG, ident)["attributes"]
            self.assertEqual(attributes["value_kind"], "boolean")
            self.assertEqual([item["id"] for item in attributes["qualifiers"]],
                             [ident.split(".", 1)[0] + ".dimension.measurement_type"])
        for ident in ("pv.accuracy.ratio_maximum", "infrastructure.accuracy.ratio_maximum"):
            attributes = entry_of(CATALOG, ident)["attributes"]
            self.assertEqual(attributes["value_kind"], "quantity")
            self.assertEqual([item["id"] for item in attributes["qualifiers"]],
                             [ident.split(".", 1)[0] + ".dimension.measurement_type"])
        for ident in ("pv.dimension.measurement_type", "infrastructure.dimension.measurement_type"):
            attributes = entry_of(CATALOG, ident)["attributes"]
            self.assertEqual(attributes["role"], "qualifier")
            self.assertEqual(attributes["value_kind"], "symbol")
            self.assertGreater(len(attributes["symbols"]), 1)
        schemes = CATALOG["identification_schemes"]
        self.assertEqual([item["id"] for item in schemes], ["scheme.ieee.eui48", "scheme.ieee.eui64"])
        self.assertTrue(all(item["admission"]["arm"] == "public_registry" for item in schemes))

    def test_reference_set_counts(self):
        kinds = list(INPUTS.pack_kinds.values())
        self.assertEqual(len(kinds), 930)
        self.assertEqual(kinds.count("relation"), 30)
        self.assertEqual(kinds.count("presentation"), 42)
        self.assertEqual(kinds.count("dimension"), 47)
        self.assertEqual(len(INPUTS.kernel_types), 28)

    def test_room_planes_and_containment(self):
        planes = ["physical", "energy", "control"]
        self.assertEqual(entry_of(CATALOG, "resource.room")["planes"], planes)
        self.assertEqual(entry_of(CATALOG, "thermal.dimension.room")["planes"], planes)
        self.assertEqual(entry_of(CATALOG, "resource.room")["attributes"]["anchor_class"], "function")
        for ident in (
            "thermal.relation.circuit_room",
            "thermal.relation.circuit_zone",
            "thermal.relation.zone_room",
        ):
            entry = entry_of(CATALOG, ident)
            self.assertEqual(entry["planes"], ["physical"])
            self.assertEqual(entry["attributes"]["core_type"], "contains")
            self.assertNotIn("medium", entry["attributes"])
        fluid = entry_of(CATALOG, "thermal.relation.fluid_supply")
        self.assertEqual(fluid["attributes"]["core_type"], "supplies")
        self.assertEqual(fluid["attributes"]["medium"], "heat_transfer_fluid")
        self.assertEqual(fluid["planes"], ["energy", "hydraulic"])
        self.assertNotIn("physical", fluid["planes"])

    def test_generator_is_not_imported(self):
        self.assertNotIn("generate_element_catalog_v1", sys.modules)
        source = validator.Path(validator.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import generate_element_catalog_v1", source)

    def test_finding_prints_error_rule_and_entry(self):
        finding = validator.Finding("membership_missing", "CAT-1", "x@1.0.0 [core]", "detail")
        self.assertEqual(str(finding), "membership_missing CAT-1 x@1.0.0 [core]: detail")


class Mutations(unittest.TestCase):
    def rejects(self, mutate, error, rule, entry=None, detail=None):
        catalog = copy.deepcopy(CATALOG)
        mutate(catalog)
        findings = validator.check_rules(catalog, INPUTS)
        matching = [finding for finding in findings if (finding.error, finding.rule) == (error, rule)
                    and (entry is None or entry in finding.entry)
                    and (detail is None or detail in finding.detail)]
        self.assertTrue(matching, f"no {error} {rule} finding among {[str(item) for item in findings]}")
        self.assertTrue(validator.validate(catalog, INPUTS, SCHEMA), "validate accepted the mutation")
        return findings

    def test_missing_repository_path_is_rejected(self):
        self.rejects(
            lambda c: entry_of(c, "pv.energy.generated")["admission"].__setitem__(
                "evidence", ["api/v1/packs/missing-page.md"]),
            "invalid_value", "CAT-6", "pv.energy.generated", validator.RELATIVE_EVIDENCE_MISSING)

    def test_branch_link_to_this_repository_is_rejected(self):
        branch = validator.THIS_REPO_BLOB + "api/v1/packs/pv-inverter-v1.md"
        self.rejects(
            lambda c: entry_of(c, "pv.energy.generated")["admission"].__setitem__("evidence", [branch]),
            "invalid_value", "CAT-6", "pv.energy.generated", validator.THIS_REPO_BLOB_EVIDENCE)

    def test_fragment_on_an_existing_page_is_kept(self):
        catalog = mutate_copy(lambda c: entry_of(c, "pv.energy.generated")["admission"].__setitem__(
            "evidence", ["api/v1/packs/pv-inverter-v1.md#limit"]))
        self.assertEqual(validator.validate(catalog, INPUTS, SCHEMA), [])

    # CAT-1
    def test_missing_pack_field(self):
        self.rejects(lambda c: remove(c, FIELD), "membership_missing", "CAT-1", FIELD)

    def test_room_relation_requires_physical(self):
        for ident in (
            "thermal.relation.circuit_room",
            "thermal.relation.circuit_zone",
            "thermal.relation.zone_room",
        ):
            self.rejects(
                lambda catalog, ident=ident: entry_of(catalog, ident).__setitem__("planes", ["energy"]),
                "membership_missing", "CAT-4", ident, "PLN-6")

    def test_room_dimension_follows_kind_planes(self):
        self.rejects(
            lambda catalog: entry_of(catalog, "resource.room").__setitem__("planes", ["energy", "control"]),
            "membership_missing", "CAT-4", "thermal.dimension.room", "PLN-5")

    def test_extra_pack_reference(self):
        self.rejects(lambda c: add_copy(c, FIELD, "evse.ac.synthetic_extra"),
                     "definition_owner_missing", "CAT-1", "evse.ac.synthetic_extra")

    def test_missing_kernel_state_type(self):
        self.rejects(lambda c: remove(c, KERNEL_TYPE), "membership_missing", "CAT-1", KERNEL_TYPE)

    def test_duplicate_entry(self):
        def mutate(catalog):
            catalog["elements"].append(copy.deepcopy(entry_of(catalog, FIELD)))
            resort(catalog)
        self.rejects(mutate, "duplicate_identity", "CAT-1", FIELD)

    def test_every_reference_key_field_counts(self):
        # Fields of the reference key and the production mutation each case catches:
        # pack id, pack version, id, version: a key that ignores the field still
        # matches the original reference, so no membership_missing is reported;
        # owner kind: a key that ignores it files the core-owned entry as an extra
        # pack reference (definition_owner_missing), which must not happen.
        def vary(path, value):
            def mutate(catalog):
                target = entry_of(catalog, FIELD)["ref"]
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = value
                resort(catalog)
            return mutate
        cases = (
            (("owner", "pack", "id"), "helianthus.pack.synthetic", "definition_owner_missing", "CAT-1"),
            (("owner", "pack", "version"), "9.9.9", "definition_owner_missing", "CAT-1"),
            (("id",), "evse.ac.synthetic_voltage", "definition_owner_missing", "CAT-1"),
            (("version",), "9.9.9", "definition_owner_missing", "CAT-1"),
            (("owner",), {"kind": "core", "contract": "helianthus.semantic.kernel/v1"},
             "definition_owner_conflict", "CAT-5"),
        )
        for path, value, error, rule in cases:
            with self.subTest(field="/".join(path)):
                findings = self.rejects(vary(path, value), "membership_missing", "CAT-1", FIELD)
                self.assertIn((error, rule), {(item.error, item.rule) for item in findings})
                self.assertIn(("invalid_value", "CAT-6"), {(item.error, item.rule) for item in findings})
                if path == ("owner",):
                    self.assertNotIn("definition_owner_missing", {item.error for item in findings})

    # CAT-2
    def test_service_dimension_disagrees_with_pack_metadata(self):
        def mutate(catalog):
            entry_of(catalog, SERVICE)["attributes"]["fact_key_dimension"] = ref_of(catalog, OTHER_DIMENSION)
        self.rejects(mutate, "invalid_value", "CAT-2", SERVICE, "pack metadata fact_key_dimension")

    def test_relation_cardinality_disagrees_with_its_pack(self):
        # The cardinality of every pack is read from the pack: the PV pack declares it too.
        for ident in PACK_RELATIONS:
            with self.subTest(relation=ident):
                def mutate(catalog, ident=ident):
                    entry_of(catalog, ident)["attributes"]["cardinality"] = "many_to_many"
                self.rejects(mutate, "invalid_value", "CAT-2", ident, "cardinality")

    def test_relation_over_time_disagrees_with_its_pack(self):
        def mutate(catalog):
            entry_of(catalog, "evse.relation.connector_session")["attributes"]["over_time"] = False
        self.rejects(mutate, "invalid_value", "CAT-2", "evse.relation.connector_session", "over_time")

    def test_single_endpoint_dimension_disagrees_with_its_pack(self):
        # Each side is read from the pack's one-item endpoint list; a reader that
        # ignored a side, or that took a list for no endpoint at all, misses the change.
        for side in ("from", "to"):
            with self.subTest(side=side):
                def mutate(catalog, side=side):
                    entry_of(catalog, SINGLE_ENDPOINT_RELATION)["attributes"]["endpoint_dimensions"][side] = \
                        ref_of(catalog, "thermal.dimension.zone")
                self.rejects(mutate, "invalid_value", "CAT-2", SINGLE_ENDPOINT_RELATION, f"endpoint {side}")

    def test_single_endpoint_relation_without_endpoint_dimensions(self):
        def mutate(catalog):
            del entry_of(catalog, SINGLE_ENDPOINT_RELATION)["attributes"]["endpoint_dimensions"]
        self.rejects(mutate, "invalid_value", "CAT-2", SINGLE_ENDPOINT_RELATION, "endpoint from")

    def test_multi_endpoint_relation_with_endpoint_dimensions(self):
        # A side with several endpoint kinds has no single endpoint dimension to name.
        def mutate(catalog):
            entry_of(catalog, MULTI_ENDPOINT_RELATION)["attributes"]["endpoint_dimensions"] = {
                "from": ref_of(catalog, "thermal.dimension.heat_generator"),
                "to": ref_of(catalog, "thermal.dimension.circuit"),
            }
        self.rejects(mutate, "invalid_value", "CAT-2", MULTI_ENDPOINT_RELATION, "endpoint to")

    def test_endpoint_kinds_disagree_with_the_pack_endpoints(self):
        # Fields varied: from_kinds and to_kinds of a relation with several endpoint
        # kinds (no endpoint_dimensions to fall back on): a kind dropped, a kind
        # replaced by another kind of the same pack, and a kind repeated. A validator
        # that read no kinds from the pack endpoints accepts each mutation.
        for side in ("from", "to"):
            for name, change in (
                ("dropped", lambda kinds: kinds[1:]),
                ("replaced", lambda kinds: ["resource.compressor"] + kinds[1:]),
                ("repeated", lambda kinds: kinds + kinds[:1]),
            ):
                with self.subTest(side=side, case=name):
                    def mutate(catalog, side=side, change=change):
                        attributes = entry_of(catalog, MULTI_ENDPOINT_RELATION)["attributes"]
                        attributes[f"{side}_kinds"] = change(list(attributes[f"{side}_kinds"]))
                    findings = validator.check_rules(mutate_copy(mutate), INPUTS)
                    self.assertIn(f"{side}_kinds is", " ".join(item.detail for item in findings
                                                                 if MULTI_ENDPOINT_RELATION in item.entry))

    # CAT-3
    def test_member_with_empty_planes(self):
        self.rejects(lambda c: entry_of(c, FIELD).update(planes=[]), "membership_missing", "CAT-3", FIELD)

    # CAT-4
    def test_relation_plane_not_admitted_by_endpoint_kind(self):
        def mutate(catalog):
            entry_of(catalog, PHYSICAL_ONLY_RELATION)["planes"] = ["physical", "energy"]
        self.rejects(mutate, "membership_missing", "CAT-4", PHYSICAL_ONLY_RELATION, "(PLN-5)")

    def test_relation_misses_required_plane(self):
        def mutate(catalog):
            entry_of(catalog, REQUIRED_PLANE_RELATION)["planes"] = ["energy", "diagnostic"]
        self.rejects(mutate, "membership_missing", "CAT-4", REQUIRED_PLANE_RELATION, "required planes")

    def test_duplicated_plane_identifier(self):
        def mutate(catalog):
            twin = copy.deepcopy(catalog["planes"][0])
            twin["question"] = "Synthetic second question?"
            catalog["planes"].append(twin)
        self.rejects(mutate, "duplicate_identity", "CAT-4", "plane physical")

    def test_lens_relation_outside_its_planes(self):
        def mutate(catalog):
            catalog["lenses"].append({
                "id": "lens.synthetic_control", "question": "Which synthetic control path exists?",
                "planes": ["control"], "root_kinds": [LENS_ROOT],
                "relations": [ref_of(catalog, PHYSICAL_ONLY_RELATION)], "max_depth": 2,
            })
        self.rejects(mutate, "membership_missing", "CAT-4", "lens.synthetic_control", "member of no lens plane")

    def test_four_lenses_match_section_29(self):
        self.assertEqual(CATALOG["lenses"], [dict(item) for item in SEEDED_LENSES])
        for lens in CATALOG["lenses"]:
            self.assertNotIn("relations", lens)

    def test_provenance_roots_are_the_relay_equipment(self):
        relays = entry_of(CATALOG, "relation.relays")["attributes"]
        lens = next(item for item in CATALOG["lenses"] if item["id"] == "lens.provenance")
        self.assertEqual(lens["root_kinds"], relays["from_kinds"])
        self.assertEqual(lens["root_kinds"], relays["to_kinds"])

    def test_each_seeded_lens_rejects_a_root_outside_its_planes(self):
        # Field varied: root_kinds of each seeded lens. The production mutation
        # is one member kind whose planes miss every plane of that lens. A
        # check that ignored root_kinds would accept the catalog.
        for ident, kind in OUTSIDE_LENS_PLANE.items():
            with self.subTest(lens=ident, root=kind):
                def mutate(catalog, ident=ident, kind=kind):
                    lens = next(item for item in catalog["lenses"] if item["id"] == ident)
                    lens["root_kinds"] = [kind]
                self.rejects(mutate, "membership_missing", "CAT-4", ident, "(LNS-1)")

    def test_exactly_one_installation_root(self):
        roots = [entry["ref"]["id"] for entry in CATALOG["elements"]
                 if entry["element_kind"] == "resource_kind" and entry["attributes"].get("installation_root") is True]
        self.assertEqual(roots, ["resource.site"])

    def test_second_installation_root_is_rejected(self):
        # Field varied: installation_root on a second resource kind. The
        # production mutation is a second true flag. A check that ignored the
        # flag would accept the catalog. False is not a root.
        def mutate(catalog):
            entry_of(catalog, "resource.equipment")["attributes"]["installation_root"] = True
        self.rejects(mutate, "duplicate_identity", "CAT-4", "resource.equipment", "installation root")

    def test_false_installation_root_is_not_a_second_root(self):
        def mutate(catalog):
            entry_of(catalog, "resource.equipment")["attributes"]["installation_root"] = False
        self.assertEqual(validator.check_rules(mutate_copy(mutate), INPUTS), [])

    # CAT-5
    def test_pack_relation_crossing_packs(self):
        def mutate(catalog):
            attributes = entry_of(catalog, CROSSING_RELATION)["attributes"]
            attributes["to_kinds"] = ["resource.battery"]
            attributes["endpoint_dimensions"]["to"] = ref_of(catalog, FOREIGN_DIMENSION)
        self.rejects(mutate, "definition_owner_conflict", "CAT-5", CROSSING_RELATION, "resource.battery")

    # CAT-6
    def test_accepted_pack_outside_seed_refs(self):
        def mutate(catalog):
            entry_of(catalog, CORE_KIND)["admission"]["arm"] = "accepted_pack"
        self.rejects(mutate, "invalid_value", "CAT-6", CORE_KIND, "seed")

    # CAT-7
    def test_sign_reference_names_non_supplies_relation(self):
        def mutate(catalog):
            entry_of(catalog, SIGNED_FIELD)["attributes"]["sign_reference"] = ref_of(catalog, CONTAINS_RELATION)
        self.rejects(mutate, "invalid_value", "CAT-7", SIGNED_FIELD, "not a supplies relation")

    def test_new_signed_entry_with_native_convention(self):
        new_ident = SIGNED_FIELD + "_synthetic"
        self.rejects(lambda c: add_copy(c, SIGNED_FIELD, new_ident), "invalid_value", "CAT-7", new_ident,
                     "native_convention")

    # CAT-8
    def test_two_swapped_entries(self):
        def mutate(catalog):
            elements = catalog["elements"]
            elements[10], elements[11] = elements[11], elements[10]
        self.rejects(mutate, "noncanonical_order", "CAT-8")

    # CAT-9
    def test_duplicated_scheme_identifier(self):
        def mutate(catalog):
            catalog["identification_schemes"] = [scheme("scheme.synthetic"), scheme("scheme.synthetic")]
        self.rejects(mutate, "duplicate_identity", "CAT-9", "scheme.synthetic")

    def test_scheme_record_fields_are_the_two_ieee_schemes(self):
        # id: swapping the two records changes the ordered scheme list.
        # issuer_registry and token_form: each field of the first record is replaced.
        def swap(catalog):
            schemes = catalog["identification_schemes"]
            schemes[0], schemes[1] = schemes[1], schemes[0]

        def issuer(catalog):
            catalog["identification_schemes"][0]["issuer_registry"] = "other"

        def token(catalog):
            catalog["identification_schemes"][0]["token_form"] = "synthetic token"

        for mutate in (swap, issuer, token):
            with self.subTest(mutate=mutate.__name__):
                self.rejects(mutate, "invalid_value", "CAT-9", "identification schemes",
                             "scheme.ieee.eui48 then scheme.ieee.eui64")

    def test_qualifier_that_is_not_a_qualifier_dimension(self):
        def mutate(catalog):
            entry_of(catalog, "pv.accuracy.measured")["attributes"]["qualifiers"] = [
                ref_of(catalog, "pv.dimension.inverter")]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.accuracy.measured",
                     "qualifier is not a qualifier dimension")

    def test_qualifier_from_another_pack(self):
        def mutate(catalog):
            entry_of(catalog, "pv.accuracy.measured")["attributes"]["qualifiers"] = [
                ref_of(catalog, "infrastructure.dimension.measurement_type")]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.accuracy.measured",
                     "qualifier is not a dimension of the same pack")

    def test_qualifiers_out_of_order(self):
        def mutate(catalog):
            entry_of(catalog, "pv.accuracy.measured")["attributes"]["qualifiers"] = [
                ref_of(catalog, "pv.dimension.phase"), ref_of(catalog, "pv.dimension.measurement_type")]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.accuracy.measured",
                     "qualifiers are not a sorted unique list")

    def test_unsorted_anchor_classes(self):
        def mutate(catalog):
            attributes = entry_of(catalog, "pv.dimension.inverter")["attributes"]
            del attributes["resource_kind"]
            attributes["anchor_classes"] = ["equipment", "component"]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.dimension.inverter",
                     "anchor classes are not sorted unique")

    def test_class_level_fact_carries_a_resource_kind(self):
        def mutate(catalog):
            attributes = entry_of(catalog, "pv.dimension.inverter")["attributes"]
            del attributes["resource_kind"]
            attributes["anchor_classes"] = ["equipment"]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.accuracy.measured",
                     "class-level fact carries a resource kind")

    def test_parameter_equal_to_the_argument(self):
        def mutate(catalog):
            attributes = entry_of(catalog, "pv.operation.set_active_power_limit")["attributes"]
            attributes["parameters"] = [copy.deepcopy(attributes["argument"])]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.operation.set_active_power_limit",
                     "parameter equals the argument")

    def test_parameter_from_another_pack(self):
        def mutate(catalog):
            entry_of(catalog, "pv.operation.set_active_power_limit")["attributes"]["parameters"] = [
                ref_of(catalog, "storage.limit.charge_current")]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.operation.set_active_power_limit",
                     "parameter is not a field of the same pack")

    def test_parameters_out_of_order(self):
        def mutate(catalog):
            entry_of(catalog, "pv.operation.set_active_power_limit")["attributes"]["parameters"] = [
                ref_of(catalog, "pv.limit.export_power"), ref_of(catalog, "pv.limit.active_power_ratio")]
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.operation.set_active_power_limit",
                     "parameters are not a sorted unique list")

    def test_event_trigger_from_another_pack(self):
        def mutate(catalog):
            trigger = entry_of(catalog, "infrastructure.energy.import")
            event = copy.deepcopy(entry_of(catalog, "pv.accuracy.measured"))
            event["ref"]["id"] = "pv.event.synthetic"
            event["element_kind"] = "event"
            event["planes"] = list(trigger["planes"])
            event["attributes"] = {
                "service": ref_of(catalog, "pv.service.inverter"),
                "trigger": ref_of(catalog, "infrastructure.energy.import"),
                "condition": "changed",
                "payload": [],
                "origin": "derived",
            }
            catalog["elements"].append(event)
            resort(catalog)
        self.rejects(mutate, "invalid_value", "CAT-2", "pv.event.synthetic",
                     "trigger is not a fact of the same pack")


class PackInputs(unittest.TestCase):
    """The validator reads the relation definitions only in their one encoding."""

    def load_with(self, path, mutate):
        original = subset.load_json

        def patched(target):
            document = original(target)
            if validator.Path(target) == path:
                mutate(document)
            return document

        validator.subset.load_json = patched
        try:
            return validator.load_inputs()
        finally:
            validator.subset.load_json = original

    def test_vector_pack_with_the_earlier_member_name(self):
        def mutate(document):
            definitions = document["catalog"]["definitions"]
            definitions[EARLIER_MEMBER] = definitions.pop("relations")
        for path in VECTOR_FILES:
            with self.subTest(pack=path.name), self.assertRaisesRegex(ValueError, "definition groups outside"):
                self.load_with(path, mutate)

    def test_vector_pack_with_both_member_names(self):
        def mutate(document):
            definitions = document["catalog"]["definitions"]
            definitions[EARLIER_MEMBER] = copy.deepcopy(definitions["relations"])
        with self.assertRaisesRegex(ValueError, "definition groups outside"):
            self.load_with(THERMAL_VECTORS, mutate)

    def test_vector_relation_without_cardinality(self):
        for path in VECTOR_FILES:
            with self.subTest(pack=path.name), self.assertRaises(KeyError):
                self.load_with(path, lambda d: d["catalog"]["definitions"]["relations"][0].pop("cardinality"))

    def test_vector_relation_endpoint_list_malformed(self):
        cases = (
            ("empty", []),
            ("duplicated", ["thermal.dimension.zone", "thermal.dimension.zone"]),
            ("not_text", [{"id": "thermal.dimension.zone"}]),
            ("not_a_list", {"id": "thermal.dimension.zone"}),
        )
        for side in ("from", "to"):
            for name, value in cases:
                with self.subTest(side=side, case=name), self.assertRaisesRegex(ValueError, "relation endpoint"):
                    self.load_with(THERMAL_VECTORS,
                                   lambda d, side=side, value=value:
                                   d["catalog"]["definitions"]["relations"][0].update({side: value}))

    def test_storage_relation_with_the_earlier_endpoint_names(self):
        def mutate(document):
            relation = document["relations"][0]
            relation["source"], relation["target"] = relation.pop("from"), relation.pop("to")
        with self.assertRaises(KeyError):
            self.load_with(validator.STORAGE_TABLES, mutate)

    def test_storage_tables_with_the_earlier_member_name(self):
        with self.assertRaises(KeyError):
            self.load_with(validator.STORAGE_TABLES, lambda d: d.update({EARLIER_MEMBER: d.pop("relations")}))

    def test_storage_relation_without_cardinality(self):
        with self.assertRaises(KeyError):
            self.load_with(validator.STORAGE_TABLES, lambda d: d["relations"][0].pop("cardinality"))


if __name__ == "__main__":
    unittest.main()
