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
CONTAINS_RELATION = "evse.relationship.connector_phase"
PHYSICAL_ONLY_RELATION = "pv.relationship.array_string"
REQUIRED_PLANE_RELATION = "evse.relationship.asset_evse"
CROSSING_RELATION = "pv.relationship.inverter_array"
FOREIGN_DIMENSION = "storage.dimension.battery"
CORE_KIND = "resource.equipment"
KERNEL_TYPE = "kernel.ack_state"
LENS_ROOT = "resource.pv_system"
SCHEME_ADMISSION = {"arm": "public_registry", "evidence": ["https://example.org/registries/synthetic"]}


def entry_of(catalog, ident):
    matches = [entry for entry in catalog["elements"] if entry["ref"]["id"] == ident]
    if len(matches) != 1:
        raise AssertionError(f"{ident}: expected one entry, found {len(matches)}")
    return matches[0]


def ref_of(catalog, ident):
    return copy.deepcopy(entry_of(catalog, ident)["ref"])


def resort(catalog):
    catalog["elements"].sort(key=validator.order_key)


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
        self.assertTrue(output.getvalue().startswith("PASS: element catalog CAT-1..CAT-9: 307 entries"))

    def test_reference_set_counts(self):
        kinds = list(INPUTS.pack_kinds.values())
        self.assertEqual(len(kinds), 250)
        self.assertEqual(kinds.count("relation"), 21)
        self.assertEqual(kinds.count("presentation"), 32)
        self.assertEqual(kinds.count("dimension"), 34)
        self.assertEqual(len(INPUTS.kernel_types), 28)

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

    # CAT-1
    def test_missing_pack_field(self):
        self.rejects(lambda c: remove(c, FIELD), "membership_missing", "CAT-1", FIELD)

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


if __name__ == "__main__":
    unittest.main()
