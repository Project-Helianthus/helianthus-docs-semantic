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


def cut(document, vector_id):
    return vector(document, vector_id)["expect"]["cut"]


def jcs(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def cut_identifier(members, contract="helianthus.semantic.graph-cut/v1"):
    return "sha256:" + hashlib.sha256(jcs({"contract": contract, "members": members})).hexdigest()


def snapshot_identifier(snapshot):
    return "sha256:" + hashlib.sha256(jcs({k: v for k, v in snapshot.items() if k != "snapshot_id"})).hexdigest()


class CommittedDocumentTest(unittest.TestCase):
    def test_every_rule_passes(self):
        for name, rule in validator.RULES:
            with self.subTest(rule=name):
                self.assertEqual(rule(DOCUMENT, CONTEXT), [])

    def test_validate_passes(self):
        self.assertEqual(validator.validate(DOCUMENT, CONTEXT), [])


SCHEME_VECTORS = ("G-NEG-ID-8", "G-NEG-ID-9")


def anchors(value, found):
    if isinstance(value, dict):
        if "class" in value and "basis" in value:
            found.append(value)
        for item in value.values():
            anchors(item, found)
    elif isinstance(value, list):
        for item in value:
            anchors(item, found)
    return found


def registered_schemes(document, state_name):
    state = next(s for s in document["prior_states"] if s["name"] == state_name)
    return set((state.get("registry") or {}).get("identification_schemes", []))


def declared_identities(document):
    return {entry["key"]: entry["identity"] for item in document["vectors"] for entry in item.get("anchor_keys", [])}


def anchor_scheme_problems(document):
    """RES-2 on the committed vectors outside the two scheme vectors: a native_identity anchor
    carries a registered scheme equal to the scheme its key digests; any other anchor carries none."""
    identities = declared_identities(document)
    problems = []
    places = [(s["name"], s) for s in document["prior_states"]]
    places += [(item["prior_state"], item["input"]) for item in document["vectors"] if item["id"] not in SCHEME_VECTORS]
    for state_name, value in places:
        registered = registered_schemes(document, state_name)
        for anchor in anchors(value, []):
            if anchor["basis"] != "native_identity":
                if "scheme" in anchor:
                    problems.append(f"{state_name}: {anchor['basis']} anchor carries a scheme")
                continue
            scheme = anchor.get("scheme")
            if scheme is None:
                problems.append(f"{state_name}: native_identity anchor without scheme")
                continue
            if scheme not in registered:
                problems.append(f"{state_name}: scheme {scheme} is not registered")
            identity = identities.get(anchor.get("key"))
            if identity is None or identity["scheme"] != scheme:
                problems.append(f"{state_name}: scheme {scheme} differs from the digested identity")
    return problems


def scheme_vector_anchor(document, vector_id):
    return vector(document, vector_id)["input"]["resource_upserts"][0]["anchor"]


class AnchorSchemeTest(unittest.TestCase):
    def test_committed_anchors_carry_the_digested_scheme(self):
        self.assertEqual(anchor_scheme_problems(DOCUMENT), [])
        self.assertTrue(any(a["basis"] == "native_identity" for a in anchors(DOCUMENT, [])))

    def test_each_scheme_member_mutation_is_caught(self):
        def native(document):
            return next(a for a in anchors(document["vectors"], []) if a["basis"] == "native_identity"
                        and a.get("scheme") == "synthetic.serial")

        def other(document):
            return next(a for a in anchors(document["vectors"], []) if a["basis"] != "native_identity")

        def renamed_identity(document):
            for item in document["vectors"]:
                for entry in item.get("anchor_keys", []):
                    entry["identity"] = dict(entry["identity"], scheme="synthetic.other")

        mutations = {
            "presence": lambda d: native(d).pop("scheme"),
            "listed": lambda d: native(d).update(scheme="synthetic.unlisted"),
            "digested": renamed_identity,
            "absence": lambda d: other(d).update(scheme="synthetic.serial"),
        }
        for name, change in mutations.items():
            with self.subTest(field=name):
                self.assertNotEqual(anchor_scheme_problems(mutated(change)), [])

    def test_unlisted_scheme_vector_has_only_that_fault(self):
        item = vector(DOCUMENT, "G-NEG-ID-8")
        anchor = scheme_vector_anchor(DOCUMENT, "G-NEG-ID-8")
        self.assertEqual(item["expect"]["error_id"], "invalid_value")
        self.assertEqual(anchor["basis"], "native_identity")
        self.assertNotIn(anchor["scheme"], registered_schemes(DOCUMENT, item["prior_state"]))
        self.assertIn(anchor["key"], declared_identities(DOCUMENT))

    def test_scheme_on_another_basis_vector_has_only_that_fault(self):
        item = vector(DOCUMENT, "G-NEG-ID-9")
        anchor = scheme_vector_anchor(DOCUMENT, "G-NEG-ID-9")
        self.assertEqual(item["expect"]["error_id"], "invalid_value")
        self.assertEqual(anchor["basis"], "operator_slot")
        self.assertNotIn("key", anchor)
        self.assertIn(anchor["scheme"], registered_schemes(DOCUMENT, item["prior_state"]))

    def test_scheme_vectors_are_required_by_section_19(self):
        for vector_id in SCHEME_VECTORS:
            def change(document, vector_id=vector_id):
                document["vectors"] = [v for v in document["vectors"] if v["id"] != vector_id]
            with self.subTest(vector=vector_id):
                problems = validator.check_statements(mutated(change), CONTEXT)
                self.assertTrue(any(vector_id in problem for problem in problems), problems)


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
        def change(document):
            document["operations"] = [o for o in document["operations"] if o != "assemble_cut"]
        self.assert_rule_rejects(validator.check_shape, mutated(change), "assemble_cut")

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
        document = mutated(lambda d: d["vectors"][0]["coverage"].append("spatial"))
        self.assert_rule_rejects(validator.check_coverage, document, "spatial")

    def test_coverage_list_shorter_than_seven_is_rejected(self):
        def change(document):
            document["coverage_ids"].remove("plane_membership")
            for item in document["vectors"]:
                item["coverage"] = [a for a in item["coverage"] if a != "plane_membership"] or ["graph_cut"]
        self.assert_rule_rejects(validator.check_coverage, mutated(change), "coverage_ids")

    def test_operations_must_be_the_section_19_operations(self):
        def change(document):
            document["operations"] = [o for o in document["operations"] if o != "assemble_cut"]
            for item in document["vectors"]:
                if item["operation"] == "assemble_cut":
                    item["operation"] = "apply"
        self.assert_rule_rejects(validator.check_coverage, mutated(change), "operations")

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

    def test_section_19_cut_identifier_without_vector_is_rejected(self):
        for identifier in ("G-POS-CUT-3", "G-POS-CUT-11", "G-POS-PLN-1"):
            with self.subTest(identifier=identifier):
                def change(document, identifier=identifier):
                    document["vectors"] = [v for v in document["vectors"] if v["id"] != identifier]
                self.assert_rule_rejects(validator.check_statements, mutated(change), identifier)

    def test_publication_identifier_without_vector_is_rejected(self):
        for identifier in ("G-POS-PUB-1", "G-NEG-PUB-1"):
            with self.subTest(identifier=identifier):
                def change(document, identifier=identifier):
                    document["vectors"] = [v for v in document["vectors"] if v["id"] != identifier]
                self.assert_rule_rejects(validator.check_statements, mutated(change), identifier)

    def test_publication_statement_must_match_vector_for_every_field(self):
        # operation: the contributor's batch is applied, never assembled; error_id: the positive
        # accepts and the negative rejects with relation_not_qualified, never another error.
        cases = (
            ("G-POS-PUB-1", "operation", "assemble_cut"),
            ("G-NEG-PUB-1", "operation", "admit"),
            ("G-POS-PUB-1", "error_id", "relation_not_qualified"),
            ("G-NEG-PUB-1", "error_id", "invalid_value"),
        )
        for identifier, field, value in cases:
            with self.subTest(identifier=identifier, field=field):
                def change(document, identifier=identifier, field=field, value=value):
                    item = vector(document, identifier)
                    if field == "operation":
                        item["operation"] = value
                    else:
                        item["expect"] = {"result": "reject", "error_id": value, "state_unchanged": True}
                self.assert_rule_rejects(validator.check_statements, mutated(change), identifier)

    def test_cut_statement_must_be_assembled(self):
        def change(document):
            vector(document, "G-POS-CUT-6")["operation"] = "apply"
        self.assert_rule_rejects(validator.check_statements, mutated(change), "G-POS-CUT-6")

    def test_wrong_cut_identifier_is_rejected_for_every_field(self):
        # contract: a cut identifier over another contract string; asset_id and snapshot_id: an
        # identifier over a member list with that field changed; order: an identifier over the
        # members in reverse order. Each is the identifier a faulty AssembleCut would produce.
        def wrong(members, field):
            members = copy.deepcopy(members)
            if field == "contract":
                return cut_identifier(members, "helianthus.semantic.graph-cut/v2")
            if field == "order":
                return cut_identifier(list(reversed(members)))
            members[0][field] = members[0][field] + "-changed"
            return cut_identifier(members)
        for field in ("contract", "asset_id", "snapshot_id", "order"):
            with self.subTest(field=field):
                def change(document, field=field):
                    expected = cut(document, "G-POS-CUT-12")
                    expected["cut_id"] = wrong(expected["members"], field)
                self.assert_rule_rejects(validator.check_cuts, mutated(change), "cut_id")

    def test_committed_cut_identifier_is_the_contract_digest(self):
        for item in DOCUMENT["vectors"]:
            expected = item["expect"].get("cut")
            if expected is not None:
                with self.subTest(vector=item["id"]):
                    self.assertEqual(expected["cut_id"], cut_identifier(expected["members"]))

    def test_snapshot_identifier_must_be_content_derived(self):
        def change(document):
            vector(document, "G-POS-CUT-12")["input"]["snapshots"][0]["revisions"]["semantic"] = "99"
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "snapshot_id")

    def test_committed_snapshot_identifiers_are_content_derived(self):
        for item in DOCUMENT["vectors"]:
            if item["operation"] == "assemble_cut":
                for snapshot in item["input"]["snapshots"]:
                    self.assertEqual(snapshot["snapshot_id"], snapshot_identifier(snapshot))

    def test_members_must_be_the_input_snapshots(self):
        for field in ("asset_id", "snapshot_id"):
            with self.subTest(field=field):
                def change(document, field=field):
                    expected = cut(document, "G-POS-CUT-12")
                    expected["members"][0][field] = expected["members"][0][field] + "-changed"
                    expected["cut_id"] = cut_identifier(expected["members"])
                self.assert_rule_rejects(validator.check_cuts, mutated(change), "members")

    def test_members_out_of_canonical_order_are_rejected(self):
        def change(document):
            expected = cut(document, "G-POS-CUT-12")
            expected["members"].reverse()
            expected["cut_id"] = cut_identifier(expected["members"])
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "order")

    def test_finding_out_of_canonical_order_is_rejected_for_every_key_field(self):
        # subject: two same_unit findings swapped; kind: a finding moved behind one of a later kind.
        def by_subject(document):
            cut(document, "G-POS-CUT-4")["findings"].reverse()

        def by_kind(document):
            findings = cut(document, "G-POS-CUT-4")["findings"]
            findings[0] = {"kind": "ungraphed", "subject": findings[0]["subject"]}
        for name, change in (("subject", by_subject), ("kind", by_kind)):
            with self.subTest(field=name):
                self.assert_rule_rejects(validator.check_cuts, mutated(change), "order")

    def test_finding_subject_lists_must_be_sorted(self):
        def change(document):
            cut(document, "G-POS-CUT-8")["findings"][0]["subject"]["resource_ids"].reverse()
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "sorted")

    def test_relation_coherence_out_of_canonical_order_is_rejected(self):
        def change(document):
            cut(document, "G-POS-CUT-4")["relation_coherence"].reverse()
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "order")

    def test_every_relation_instance_needs_a_coherence(self):
        def change(document):
            cut(document, "G-POS-CUT-6")["relation_coherence"].pop()
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "coherence")

    def test_unknown_finding_kind_is_rejected(self):
        def change(document):
            cut(document, "G-POS-CUT-7")["findings"][0]["kind"] = "possibly_same"
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "possibly_same")

    def test_finding_subject_must_have_the_shape_of_its_kind(self):
        def change(document):
            cut(document, "G-POS-CUT-5")["findings"][0]["subject"] = {"resource_id": "resource:pv:01"}
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "subject")

    def test_exclusion_makes_the_cut_partial(self):
        def change(document):
            cut(document, "G-POS-CUT-1")["completeness"] = "complete"
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "partial")

    def test_excluded_members_follow_duplicate_identity_findings(self):
        def change(document):
            cut(document, "G-POS-CUT-9")["excluded_members"].pop()
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "excluded")

    def test_plane_membership_follows_the_catalog_and_coherence(self):
        def dropped(document):
            entry = cut(document, "G-POS-PLN-1")["plane_membership"][0]
            entry["planes"] = [p for p in entry["planes"] if p != "provenance"]

        def added(document):
            entry = cut(document, "G-POS-PLN-1")["plane_membership"][0]
            entry["planes"] = sorted(set(entry["planes"]) | {"energy"})
        for name, change in (("dropped", dropped), ("added", added)):
            with self.subTest(change=name):
                self.assert_rule_rejects(validator.check_cuts, mutated(change), "planes")

    def test_every_finding_kind_and_coherence_state_is_exercised(self):
        def change(document):
            document["vectors"] = [v for v in document["vectors"] if v["id"] != "G-POS-CUT-13"]
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "outside_cut")

    def test_rejected_cut_keeps_the_stable_error(self):
        def change(document):
            vector(document, "G-NEG-CUT-2")["input"]["snapshots"].pop()
        self.assert_rule_rejects(validator.check_cuts, mutated(change), "G-NEG-CUT-2")

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
