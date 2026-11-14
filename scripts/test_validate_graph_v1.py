#!/usr/bin/env python3
"""Mutation tests of the graph acceptance vector validator.

Every test copies the committed vector document, applies one mutation and
expects the rule that the mutation breaks to report it; ``validate`` must
report it as well. Digests are computed here, never written as literals.
"""
import copy
import hashlib
import json
import sys
import unittest

import validate_graph_v1 as validator

CONTEXT = validator.load_context()
DOCUMENT = validator.load_document(validator.VECTORS)


def mutated(change):
    document = copy.deepcopy(DOCUMENT)
    change(document)
    return document


def vector(document, vector_id):
    return next(item for item in document["vectors"] if item["id"] == vector_id)


def first_with_anchor_key(document):
    return next(item for item in document["vectors"] if item.get("anchor_keys"))


class CommittedDocumentTest(unittest.TestCase):
    def test_every_rule_passes(self):
        for name, rule in validator.RULES:
            with self.subTest(rule=name):
                self.assertEqual(rule(DOCUMENT, CONTEXT), [])

    def test_validate_passes(self):
        self.assertEqual(validator.validate(DOCUMENT, CONTEXT), [])


class MutationTest(unittest.TestCase):
    def assert_rule_rejects(self, rule, document, fragment):
        problems = rule(document, CONTEXT)
        self.assertTrue(any(fragment in problem for problem in problems), problems)
        self.assertNotEqual(validator.validate(document, CONTEXT), [])

    def test_repeated_json_key_is_rejected(self):
        text = json.dumps(DOCUMENT)
        repeated = text.replace('"contract": ', '"contract": "x", "contract": ', 1)
        with self.assertRaises(ValueError):
            validator.parse_document(repeated)

    def test_unknown_vector_member_is_rejected(self):
        document = mutated(lambda d: d["vectors"][0].update(plane="energy"))
        self.assert_rule_rejects(validator.check_shape, document, "plane")

    def test_unlisted_operation_is_rejected(self):
        document = mutated(lambda d: d["vectors"][0].update(operation="assemble_cut"))
        self.assert_rule_rejects(validator.check_shape, document, "operation")

    def test_malformed_identifier_is_rejected(self):
        document = mutated(lambda d: d["vectors"][0].update(id="G-POS-act-1"))
        self.assert_rule_rejects(validator.check_identifiers, document, "G-POS-act-1")

    def test_duplicated_identifier_is_rejected(self):
        def change(document):
            document["vectors"][1]["id"] = document["vectors"][0]["id"]
        self.assert_rule_rejects(validator.check_identifiers, mutated(change), "duplicate")

    def test_polarity_must_match_identifier(self):
        def change(document):
            vector(document, "G-NEG-ID-1")["polarity"] = "positive"
        self.assert_rule_rejects(validator.check_identifiers, mutated(change), "G-NEG-ID-1")

    def test_coverage_area_without_negative_is_rejected(self):
        def change(document):
            for item in document["vectors"]:
                if item["polarity"] == "negative" and "authority" in item["coverage"]:
                    item["coverage"] = ["activation"]
        self.assert_rule_rejects(validator.check_coverage, mutated(change), "authority")

    def test_coverage_area_without_positive_is_rejected(self):
        def change(document):
            for item in document["vectors"]:
                if item["polarity"] == "positive" and "element_catalog" in item["coverage"]:
                    item["coverage"] = ["activation"]
        self.assert_rule_rejects(validator.check_coverage, mutated(change), "element_catalog")

    def test_undeclared_coverage_area_is_rejected(self):
        document = mutated(lambda d: d["vectors"][0]["coverage"].append("graph_cut"))
        self.assert_rule_rejects(validator.check_coverage, document, "graph_cut")

    def test_vector_without_documented_error_is_rejected(self):
        def change(document):
            vector(document, "G-NEG-ID-1")["expect"]["error_id"] = "identity_collision"
        self.assert_rule_rejects(validator.check_errors, mutated(change), "identity_collision")

    def test_error_ids_must_equal_graph_and_expected_errors(self):
        def change(document):
            document["error_ids"] = [e for e in document["error_ids"] if e != "stale_relation"]
        self.assert_rule_rejects(validator.check_errors, mutated(change), "error_ids")

    def test_definition_missing_from_catalog_is_rejected(self):
        def change(document):
            item = vector(document, "G-NEG-RES-2")
            text = json.dumps(item).replace("pv.dc.power", "pv.dc.peak_power")
            item.clear()
            item.update(json.loads(text))
        self.assert_rule_rejects(validator.check_definitions, mutated(change), "pv.dc.peak_power")

    def test_assumed_disposition_must_match_catalog(self):
        def change(document):
            item = vector(document, "G-NEG-RES-1")
            for entry in item["definitions"]:
                if entry["disposition"] == "unknown":
                    entry["disposition"] = "member"
        self.assert_rule_rejects(validator.check_definitions, mutated(change), "disposition")

    def test_undeclared_definition_reference_is_rejected(self):
        def change(document):
            item = vector(document, "G-NEG-RES-2")
            item["definitions"] = [
                entry for entry in item["definitions"] if entry["ref"]["id"] != "pv.dc.power"
            ]
        self.assert_rule_rejects(validator.check_definitions, mutated(change), "pv.dc.power")

    def test_declared_planes_must_match_catalog(self):
        def change(document):
            for entry in vector(document, "G-POS-CAT-2")["definitions"]:
                if "planes" in entry:
                    entry["planes"] = entry["planes"][:1]
        self.assert_rule_rejects(validator.check_definitions, mutated(change), "planes")

    def test_wrong_anchor_key_digest_is_rejected_for_every_identity_field(self):
        for field in ("scheme", "issuer", "token"):
            with self.subTest(field=field):
                def change(document, field=field):
                    entry = first_with_anchor_key(document)["anchor_keys"][0]
                    entry["identity"][field] = entry["identity"][field] + "-changed"
                self.assert_rule_rejects(validator.check_anchor_keys, mutated(change), "key")

    def test_anchor_key_value_itself_is_checked(self):
        def change(document):
            entry = first_with_anchor_key(document)["anchor_keys"][0]
            entry["key"] = "sha256:" + hashlib.sha256(b"other").hexdigest()
        self.assert_rule_rejects(validator.check_anchor_keys, mutated(change), "key")

    def test_record_key_without_declared_identity_is_rejected(self):
        def change(document):
            first_with_anchor_key(document)["anchor_keys"].pop(0)
        self.assert_rule_rejects(validator.check_anchor_keys, mutated(change), "key")

    def test_unregistered_identification_scheme_is_rejected(self):
        def change(document):
            name = first_with_anchor_key(document)["prior_state"]
            state = next(s for s in document["prior_states"] if s["name"] == name)
            state["registry"]["identification_schemes"] = []
        self.assert_rule_rejects(validator.check_anchor_keys, mutated(change), "scheme")

    def test_section_19_identifier_without_vector_is_rejected(self):
        def change(document):
            document["vectors"] = [v for v in document["vectors"] if v["id"] != "G-NEG-ID-1"]
        self.assert_rule_rejects(validator.check_statements, mutated(change), "G-NEG-ID-1")

    def test_closing_paragraph_identifier_without_vector_is_rejected(self):
        def change(document):
            document["vectors"] = [v for v in document["vectors"] if v["id"] != "G-POS-ID-1"]
        self.assert_rule_rejects(validator.check_statements, mutated(change), "G-POS-ID-1")

    def test_statement_error_must_match_vector(self):
        def change(document):
            vector(document, "G-NEG-REL-3")["expect"]["error_id"] = "dangling_reference"
        self.assert_rule_rejects(validator.check_statements, mutated(change), "G-NEG-REL-3")

    def test_statement_operation_must_match_vector(self):
        def change(document):
            vector(document, "G-NEG-ACT-2")["operation"] = "apply"
        self.assert_rule_rejects(validator.check_statements, mutated(change), "G-NEG-ACT-2")

    def test_catalog_digest_must_match_file(self):
        def change(document):
            document["element_catalog"]["sha256"] = "sha256:" + hashlib.sha256(b"x").hexdigest()
        self.assert_rule_rejects(validator.check_catalog_digest, mutated(change), "sha256")

    def test_catalog_path_must_be_the_element_catalog(self):
        def change(document):
            document["element_catalog"]["path"] = "api/v1/pack-metadata-v1.json"
        self.assert_rule_rejects(validator.check_catalog_digest, mutated(change), "path")


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
