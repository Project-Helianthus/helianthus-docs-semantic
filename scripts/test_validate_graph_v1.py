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


# Prior states that register the catalog with one element set to unknown.
UNKNOWN_STATES = ("thermal-zone-with-qualified-setpoint-capability", "thermal-system-without-circuits",
                  "catalog-registered-with-an-unknown-fact-for-cut-assembly")


def state(document, name):
    return next(item for item in document["prior_states"] if item["name"] == name)


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

    def test_vectors_need_their_registered_catalog_mutation(self):
        # Without the mutation of its prior state, each of the three vectors over an
        # unknown element declares a disposition the committed catalog does not hold.
        for name in UNKNOWN_STATES:
            with self.subTest(state=name):
                def change(document, name=name):
                    state(document, name)["registry"].pop("catalog_mutations")
                self.assert_rule_rejects(validator.check_definitions, mutated(change), "disposition")

    def test_registered_catalog_mutation_fields_are_checked(self):
        # Fields of a catalog mutation and the production check that catches each:
        # ref (outside the catalog: registered_entries lookup; a second mutation of the
        # same entry: the once check), disposition, reason and tracking (shape schema).
        other_ref = {"owner": {"kind": "core", "contract": "helianthus.semantic.kernel/v1"},
                     "id": "resource.not_a_catalog_kind", "version": "1.0.0"}
        cases = (
            ("ref", lambda change: change.update(ref=other_ref), validator.check_definitions, "not in the catalog"),
            ("ref_twice", None, validator.check_definitions, "once"),
            ("disposition", lambda change: change.update(disposition="unsupported"), validator.check_shape,
             "/disposition"),
            ("reason", lambda change: change.update(reason="no reason"), validator.check_shape, "/reason"),
            ("tracking", lambda change: change.update(tracking="https://example.org/issues/1"),
             validator.check_shape, "/tracking"),
        )
        for field, edit, rule, fragment in cases:
            with self.subTest(field=field):
                def change(document, edit=edit):
                    mutations = state(document, UNKNOWN_STATES[0])["registry"]["catalog_mutations"]
                    if edit is None:
                        mutations.append(copy.deepcopy(mutations[0]))
                    else:
                        edit(mutations[0]["set_disposition"])
                document = mutated(change)
                if rule is validator.check_shape:
                    # The registry is null or an object, so the shape rule reports the registry;
                    # the registry schema names the field.
                    self.assert_rule_rejects(rule, document, "/registry")
                    registry = state(document, UNKNOWN_STATES[0])["registry"]
                    self.assertTrue(any(fragment in problem for problem in
                                        validator.subset.errors(registry, validator.REGISTRY)))
                else:
                    self.assert_rule_rejects(rule, document, fragment)

    def test_registered_catalog_mutation_of_a_non_member_is_rejected(self):
        unsupported = next(entry for entry in CONTEXT.catalog["elements"] if entry["disposition"] == "unsupported")
        def change(document):
            mutation = state(document, UNKNOWN_STATES[0])["registry"]["catalog_mutations"][0]
            mutation["set_disposition"]["ref"] = copy.deepcopy(unsupported["ref"])
        self.assert_rule_rejects(validator.check_definitions, mutated(change), "one member entry")

    def test_catalog_mutation_without_registered_catalog_is_rejected(self):
        def change(document):
            state(document, UNKNOWN_STATES[0])["registry"]["element_catalog"] = "absent"
        self.assert_rule_rejects(validator.check_definitions, mutated(change), "registered element catalog")

    def test_cut_planes_read_the_registered_catalog(self):
        # The cut vector over an unknown fact runs on the catalog its prior state registers:
        # on the committed catalog the fact is a member and its subject would be in a plane.
        state_name = vector(DOCUMENT, "G-POS-CUT-10")["prior_state"]
        registered, problems = validator.state_entries(DOCUMENT, CONTEXT)
        self.assertEqual(problems, [])
        entry = registered[state_name][next(key for key in registered[state_name]
                                            if '"thermal.demand.level"' in key)]
        self.assertEqual((entry["disposition"], entry["planes"]), ("unknown", []))
        snapshot = vector(DOCUMENT, "G-POS-CUT-10")["input"]["snapshots"][0]
        self.assertEqual(validator.subject_resources(snapshot, registered[state_name]), {})
        self.assertTrue(validator.subject_resources(snapshot, validator.catalog_entries(CONTEXT)))

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


PART2_VECTORS = (
    "G-POS-RET-1", "G-POS-RET-2", "G-POS-RET-3", "G-POS-RET-4", "G-POS-RET-5",
    "G-NEG-RET-1", "G-NEG-RET-2", "G-NEG-RET-3", "G-NEG-RET-4", "G-NEG-RET-5", "G-NEG-RET-6",
    "G-POS-LNS-1", "G-POS-LNS-2", "G-POS-LNS-3",
    "G-POS-SUM-1", "G-NEG-SUM-1", "G-NEG-SUM-2", "G-NEG-SUM-3", "G-NEG-SUM-4",
    "G-POS-TGT-1", "G-NEG-TGT-1",
)
PART2_COVERAGE = ("lens_result", "retrieval", "sum", "target_report")
PART2_OPERATIONS = ("list_resources", "project", "retrieve_lens", "sum_members", "traverse")


class Part2VectorTest(unittest.TestCase):
    def test_section_36_identifiers_are_required(self):
        for vector_id in PART2_VECTORS:
            def change(document, vector_id=vector_id):
                document["vectors"] = [item for item in document["vectors"] if item["id"] != vector_id]
            with self.subTest(vector=vector_id):
                problems = validator.check_statements(mutated(change), CONTEXT)
                self.assertTrue(any(vector_id in problem for problem in problems), problems)

    def test_part2_coverage_and_operations_join_the_list(self):
        self.assertEqual(len(DOCUMENT["coverage_ids"]), 11)
        for area in PART2_COVERAGE:
            self.assertIn(area, DOCUMENT["coverage_ids"])
        for operation in PART2_OPERATIONS:
            self.assertIn(operation, DOCUMENT["operations"])
        self.assertEqual(validator.check_coverage(DOCUMENT, CONTEXT), [])


def read_of(document, vector_id):
    return vector(document, vector_id)["expect"]["read"]


def digest_of(label):
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


class ReadMutationTest(unittest.TestCase):
    def assert_rule_rejects(self, rule, document, fragment):
        problems = rule(document, CONTEXT)
        self.assertTrue(any(fragment in problem for problem in problems), problems)
        self.assertNotEqual(validator.validate(document, CONTEXT), [])

    def test_read_cut_identifier_is_rejected_for_every_field(self):
        # contract: a cut identifier over another contract string. asset_id and snapshot_id: an
        # identifier over a member list with that field changed. order: an identifier over the
        # members in reverse order. Each is the identifier a faulty read would record.
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
                    served = read_of(document, "G-NEG-SUM-4")["cut"]
                    served["cut_id"] = wrong(served["members"], field)
                self.assert_rule_rejects(validator.check_reads, mutated(change), "cut_id")

    def test_committed_read_cut_identifiers_match_members(self):
        for item in DOCUMENT["vectors"]:
            served = (item["expect"].get("read") or {}).get("cut")
            if served is None:
                continue
            with self.subTest(vector=item["id"]):
                self.assertEqual(served["cut_id"], cut_identifier(served["members"]))

    def test_relation_key_is_rejected_for_every_field(self):
        # owner, id and version: that field of the recorded definition changed. from and to: the
        # recorded endpoint changed. order: the relation list reversed. The recomputed result keeps
        # the canonical relation key and order.
        def owner(relation):
            relation["definition"]["owner"]["pack"]["id"] += "-changed"

        def ident(relation):
            relation["definition"]["id"] += "-changed"

        def version(relation):
            relation["definition"]["version"] += "-changed"

        def source(relation):
            relation["from"] += "-changed"

        def target(relation):
            relation["to"] += "-changed"

        cases = (
            ("owner", "owner", owner),
            ("id", ".id", ident),
            ("version", "version", version),
            ("from", "from", source),
            ("to", "to", target),
        )
        for field, fragment, mutate in cases:
            with self.subTest(field=field):
                def change(document, mutate=mutate):
                    mutate(read_of(document, "G-POS-LNS-1")["relations"][0])
                self.assert_rule_rejects(validator.check_reads, mutated(change), fragment)

        def change_order(document):
            read_of(document, "G-POS-LNS-1")["relations"].reverse()
        self.assert_rule_rejects(validator.check_reads, mutated(change_order), "relations")

    def test_page_token_is_bound_to_the_cut_and_the_request(self):
        # NextPage is a string. Empty lens-result arrays are omitted. Both pages carry one cut.
        item = vector(DOCUMENT, "G-POS-RET-1")
        read = item["expect"]["read"]
        for key in ("facts", "findings", "frontier"):
            self.assertNotIn(key, read)
        pages = read["pages"]
        token = json.loads(pages[0]["next_page"])
        self.assertIsInstance(pages[0]["next_page"], str)
        self.assertEqual(token["cut_id"], read["cut"]["cut_id"])
        self.assertEqual(token["request_digest"], validator.request_digest(item["input"]["request"]))
        self.assertNotIn("next_page", pages[-1])
        self.assertEqual({page["cut"]["cut_id"] for page in pages}, {read["cut"]["cut_id"]})
        union = [row["resource_id"] for page in pages for row in page["resources"]]
        self.assertEqual(union, [row["resource_id"] for row in read["resources"]])

    def test_page_token_fields_are_recomputed(self):
        # cut_id: the token names another cut. request_digest: the token names another request.
        def rewrite(document, field, value):
            page = read_of(document, "G-POS-RET-1")["pages"][0]
            parsed = json.loads(page["next_page"])
            parsed[field] = value
            page["next_page"] = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

        def cut_field(document):
            rewrite(document, "cut_id", digest_of("other-cut"))

        def digest_field(document):
            rewrite(document, "request_digest", digest_of("other-request"))

        for field, change in (("cut_id", cut_field), ("request_digest", digest_field)):
            with self.subTest(field=field):
                self.assert_rule_rejects(validator.check_reads, mutated(change), "next_page")

    def test_object_page_token_is_invalid_value(self):
        # page_token: an object is not the string NextPage, so the token is malformed.
        def change(document):
            item = vector(document, "G-NEG-RET-6")
            item["input"]["request"]["page_token"] = {
                "cut_id": digest_of("other-cut"), "request_digest": digest_of("other-request"),
            }
            item["expect"]["error_id"] = "revision_conflict"

        self.assert_rule_rejects(validator.check_reads, mutated(change), "invalid_value")

    def test_lens_result_omits_empty_members(self):
        # facts: an empty array is not the omitted member the lens result declares.
        def change(document):
            read_of(document, "G-POS-RET-1")["facts"] = []

        self.assert_rule_rejects(validator.check_reads, mutated(change), "facts")

    def test_resource_order_fields_are_recomputed(self):
        # depth: the recorded depth changed. resource_id: the recorded resource changed.
        # order: the resource list reversed. The recomputed walk keeps depth and ResourceID order.
        def depth(document):
            read_of(document, "G-POS-RET-4")["resources"][0]["depth"] += 1

        def resource_id(document):
            row = read_of(document, "G-POS-RET-4")["resources"][0]
            row["resource_id"] += "-changed"

        def order(document):
            read_of(document, "G-POS-RET-4")["resources"].reverse()

        for field, change, fragment in (
            ("depth", depth, "depth"),
            ("resource_id", resource_id, "resource_id"),
            ("order", order, "resources"),
        ):
            with self.subTest(field=field):
                self.assert_rule_rejects(validator.check_reads, mutated(change), fragment)

    def test_fact_key_is_rejected_for_every_field(self):
        # pack_id, pack_version, fact_id, dimensions[0].id and dimensions[0].value.text: that
        # recorded fact-key field changed. The recomputed fact keeps the input key.
        def pack_id(key):
            key["pack_id"] += "-changed"

        def pack_version(key):
            key["pack_version"] += "-changed"

        def fact_id(key):
            key["fact_id"] += "-changed"

        def dimension_id(key):
            key["dimensions"][0]["id"] += "-changed"

        def text(key):
            key["dimensions"][0]["value"]["text"] += "-changed"

        cases = (
            ("pack_id", "pack_id", pack_id),
            ("pack_version", "pack_version", pack_version),
            ("fact_id", "fact_id", fact_id),
            ("dimensions.id", "dimensions[0].id", dimension_id),
            ("dimensions.value.text", "text", text),
        )
        for field, fragment, mutate in cases:
            with self.subTest(field=field):
                def change(document, mutate=mutate):
                    mutate(read_of(document, "G-POS-LNS-1")["facts"][0]["key"])
                self.assert_rule_rejects(validator.check_reads, mutated(change), fragment)

    def test_sum_withheld_reason_is_recomputed(self):
        # withheld: the recorded reason is no longer same_unit. The recomputed sum keeps that reason.
        def change(document):
            read_of(document, "G-NEG-SUM-2")["withheld"] = "no_coverage"
        self.assert_rule_rejects(validator.check_reads, mutated(change), "withheld")

    def test_sum_coefficient_excludes_the_scope_aggregate(self):
        # coefficient: the recorded value adds the scope aggregate. The recomputed sum leaves it out.
        def change(document):
            value = read_of(document, "G-NEG-SUM-1")["value"]
            value["coefficient"] = str(int(value["coefficient"]) + 1000)
        self.assert_rule_rejects(validator.check_reads, mutated(change), "coefficient")

    def test_lens_must_be_in_the_catalog(self):
        # lens: the request names a lens the catalog does not hold.
        def change(document):
            vector(document, "G-POS-LNS-1")["input"]["request"]["lens"] = "lens.not_in_catalog"
        self.assert_rule_rejects(validator.check_reads, mutated(change), "not in the catalog")

    def test_definition_outside_requested_planes_is_membership_missing(self):
        # planes: the request plane set no longer meets the named definition. definitions: the
        # named relation is outside those planes. The read is membership_missing.
        def change(document):
            item = vector(document, "G-POS-RET-5")
            request = item["input"]["request"]
            request["planes"] = ["diagnostic"]
            request["definitions"] = [copy.deepcopy(item["input"]["snapshots"][0]["relations"][0]["definition"])]
        self.assert_rule_rejects(validator.check_reads, mutated(change), "membership_missing")

    def test_project_relation_key_is_rejected_for_every_field(self):
        # definition, from and to: the cited relation key no longer matches a coherent qualified
        # instance. The read is projection_incomplete.
        def cited(document):
            report = vector(document, "G-POS-TGT-1")["input"]["request"]["report"]
            return report["dispositions"][0]["relations"][0]

        def definition(document):
            cited(document)["definition"]["id"] += "-changed"

        def source(document):
            cited(document)["from"] += "-changed"

        def target(document):
            cited(document)["to"] += "-changed"

        for field, change in (("definition", definition), ("from", source), ("to", target)):
            with self.subTest(field=field):
                self.assert_rule_rejects(validator.check_reads, mutated(change), "projection_incomplete")

    def test_list_plane_filter_excludes_a_resource_outside_the_plane(self):
        # resources: the recorded list adds the current inverter that PLN-3 leaves out of energy.
        # The recomputed list_resources filter keeps only the resources the plane contains.
        item = vector(DOCUMENT, "G-POS-RET-3")
        listed = [row["resource_id"] for row in item["expect"]["read"]["resources"]]
        self.assertEqual(listed, ["resource:inverter:01", "resource:inverter:02"])
        present = [resource["resource_id"] for resource in item["input"]["snapshots"][0]["resources"]]
        self.assertIn("resource:inverter:04", present)

        def change(document):
            rows = read_of(document, "G-POS-RET-3")["resources"]
            extra = copy.deepcopy(rows[0])
            extra["resource_id"] = "resource:inverter:04"
            rows.append(extra)

        self.assert_rule_rejects(validator.check_reads, mutated(change), "resources")

    def test_list_plane_filter_uses_pln3_membership(self):
        # facts: the energy facts that place the inverters in the plane are removed, and the cut
        # identifier is recomputed for that snapshot. The plane filter then lists no inverter.
        def change(document):
            item = vector(document, "G-POS-RET-3")
            snapshot = item["input"]["snapshots"][0]
            snapshot["facts"] = []
            snapshot["snapshot_id"] = validator.snapshot_identifier(snapshot)
            served = item["expect"]["read"]["cut"]
            for member in served["members"]:
                if member["asset_id"] == snapshot["asset_id"]:
                    member["snapshot_id"] = snapshot["snapshot_id"]
            served["cut_id"] = validator.cut_identifier(served["members"])

        self.assert_rule_rejects(validator.check_reads, mutated(change), "resources")

    def test_lens_resource_rows_carry_lens_planes(self):
        # planes: the recorded lens resources drop the planes PLN-3 places them in. The recomputed
        # lens result keeps those planes, and a paged lens result carries the same rows.
        rows = {row["resource_id"]: row["planes"] for row in read_of(DOCUMENT, "G-POS-LNS-1")["resources"]}
        self.assertEqual(rows["resource:inverter:01"], ["physical", "diagnostic"])
        self.assertEqual(rows["resource:input:01"], ["physical"])
        self.assertEqual(rows["resource:input:02"], ["physical"])
        self.assertNotEqual(rows["resource:inverter:01"], rows["resource:input:01"])
        for page in read_of(DOCUMENT, "G-POS-RET-1")["pages"]:
            for row in page["resources"]:
                self.assertIn("planes", row)

        def change(document):
            for row in read_of(document, "G-POS-LNS-1")["resources"]:
                del row["planes"]

        self.assert_rule_rejects(validator.check_reads, mutated(change), "planes")

    def test_scope_aggregate_matches_the_requested_fact(self):
        # observed_aggregate: the recorded aggregate is the other aggregate on the scope. The
        # recomputed sum returns the aggregate of the requested member fact.
        positive = vector(DOCUMENT, "G-POS-SUM-1")
        self.assertEqual(positive["input"]["request"]["scope"], "resource:pv-system:01")
        grouped = [rel["to"] for rel in positive["input"]["snapshots"][0]["relations"]
                   if rel["definition"]["id"] == "pv.relation.system_inverter"]
        self.assertEqual(grouped, ["resource:inverter:01", "resource:inverter:02", "resource:inverter:03"])
        subjects = [fact["key"]["dimensions"][0]["value"]["text"] for fact in positive["input"]["snapshots"][0]["facts"]
                    if fact["key"]["fact_id"] == "pv.dc.power"]
        self.assertEqual(sorted(subjects), ["resource:inverter:01", "resource:inverter:02", "resource:inverter:03"])
        self.assertEqual(positive["input"]["request"]["fact"]["id"], "pv.dc.power")
        self.assertEqual(positive["expect"]["read"]["value"]["coefficient"], "60")
        self.assertEqual(positive["expect"]["read"]["value"]["unit"], "unit.watt")
        self.assertEqual(positive["expect"]["read"]["observed_aggregate"]["key"]["fact_id"], "pv.dc.aggregate_power")
        negative = read_of(DOCUMENT, "G-NEG-SUM-1")
        self.assertEqual(negative["value"]["coefficient"], "30")
        self.assertEqual(negative["observed_aggregate"]["key"]["fact_id"], "pv.dc.aggregate_power")

        def change(document):
            item = vector(document, "G-POS-SUM-1")
            decoy = next(fact for fact in item["input"]["snapshots"][0]["facts"]
                         if fact["key"]["fact_id"] == "pv.ac.aggregate_active_power")
            item["expect"]["read"]["observed_aggregate"] = copy.deepcopy(decoy)

        self.assert_rule_rejects(validator.check_reads, mutated(change), "observed_aggregate")

    def test_distinct_catalog_sign_references_withhold(self):
        # sign_reference: the catalog references differ and the fact members agree. SUM-5 withholds.
        rows = [
            {"asset_id": "asset:pv:01",
             "entry": {"attributes": {"direction": "signed", "sign_reference": "native_convention"}},
             "fact": {"sign_reference": "native_convention"}},
            {"asset_id": "asset:pv:01",
             "entry": {"attributes": {"direction": "signed", "sign_reference": "other"}},
             "fact": {"sign_reference": "native_convention"}},
        ]
        self.assertEqual(validator.sign_reason(rows), "mixed_sign_reference")

    def test_injected_fact_sign_reference_does_not_withhold_a_one_asset_sum(self):
        # sign_reference: both member facts carry a different undeclared sign_reference, on one
        # asset. The catalog reference is native_convention, so the recomputed sum has a value.
        self.assertEqual(read_of(DOCUMENT, "G-NEG-SUM-4")["withheld"], "mixed_sign_reference")
        self.assertEqual(len(vector(DOCUMENT, "G-NEG-SUM-4")["input"]["snapshots"]), 2)
        item = copy.deepcopy(vector(DOCUMENT, "G-NEG-SUM-4"))
        primary, other = item["input"]["snapshots"]
        primary["resources"].extend(other["resources"])
        primary["facts"].extend(other["facts"])
        item["input"]["snapshots"] = [primary]
        primary["facts"][0]["sign_reference"] = "native_convention"
        primary["facts"][1]["sign_reference"] = "other"
        registered, _found = validator.state_entries(DOCUMENT, CONTEXT)
        error, body = validator.evaluate_read(item, registered[item["prior_state"]], CONTEXT)
        self.assertIsNone(error)
        self.assertEqual(body["value"]["coefficient"], "185")
        self.assertNotIn("withheld", body)

    def test_unknown_lens_and_outside_planes_are_both_membership_missing(self):
        # planes: the outside-planes vector's planes are widened to admit the named definition.
        # The recomputed traverse is then accepted, so that vector no longer records the branch.
        unknown = vector(DOCUMENT, "G-NEG-RET-4")
        self.assertEqual(unknown["input"]["request"]["lens"], "lens.not_in_catalog")
        self.assertEqual(unknown["expect"]["error_id"], "membership_missing")
        outside = vector(DOCUMENT, "G-NEG-RET-7")
        self.assertEqual(outside["expect"]["error_id"], "membership_missing")
        self.assertEqual(outside["input"]["request"]["planes"], ["diagnostic"])
        self.assertTrue(outside["input"]["request"]["definitions"])

        def change(document):
            vector(document, "G-NEG-RET-7")["input"]["request"]["planes"] = ["energy"]

        self.assert_rule_rejects(validator.check_reads, mutated(change), "recomputed read is accepted")

    def test_project_report_lens_is_in_the_manifest(self):
        # lens: the report lens moves to the top level, which is not a projection report.
        item = vector(DOCUMENT, "G-POS-TGT-1")
        report = item["input"]["request"]["report"]
        self.assertNotIn("lens", report)
        self.assertEqual(report["manifest"]["lens"], item["input"]["request"]["lens"])
        self.assertEqual(report["contract"], "helianthus.semantic.kernel/v1")
        disposition = report["dispositions"][0]
        for key in ("kind", "item_id", "outcome", "source_keys", "loss"):
            self.assertIn(key, disposition)
        self.assertEqual(len(disposition["resources"]), 2)
        self.assertEqual(len(disposition["relations"]), 1)

        def change(document):
            recorded = vector(document, "G-POS-TGT-1")["input"]["request"]["report"]
            recorded["lens"] = recorded["manifest"].pop("lens")

        self.assert_rule_rejects(validator.check_reads, mutated(change), "invalid_value")

    def test_project_disposition_requires_the_report_fields(self):
        # kind: the disposition no longer carries the projection disposition fields.
        def change(document):
            del vector(document, "G-POS-TGT-1")["input"]["request"]["report"]["dispositions"][0]["kind"]

        self.assert_rule_rejects(validator.check_reads, mutated(change), "invalid_value")

    def test_page_size_and_frontier_bound_are_both_bounds_exceeded(self):
        # frontier: G-NEG-RET-5 has no page size and its frontier is above 4096 entries.
        # The page-size branch is the other vector. Each snapshot stays within the per-asset bound.
        item = vector(DOCUMENT, "G-NEG-RET-5")
        self.assertEqual(item["expect"]["error_id"], "bounds_exceeded")
        self.assertIsNone(item["input"]["request"].get("page_size"))
        counts = [len(snap["resources"]) for snap in item["input"]["snapshots"]]
        self.assertTrue(all(count <= 4096 for count in counts))
        self.assertGreater(sum(counts), 4096)
        page = vector(DOCUMENT, "G-NEG-RET-8")
        self.assertEqual(page["input"]["request"]["page_size"], 4097)
        self.assertEqual(page["expect"]["error_id"], "bounds_exceeded")
        registered, _found = validator.state_entries(DOCUMENT, CONTEXT)
        error, body = validator.evaluate_read(item, registered[item["prior_state"]], CONTEXT)
        self.assertEqual(error, "bounds_exceeded")
        self.assertIsNone(body)

    def test_frontier_bound_accepts_4096_entries(self):
        # resources: one stopping resource is removed, so the frontier is within the bound.
        def change(document):
            item = vector(document, "G-NEG-RET-5")
            snap = max(item["input"]["snapshots"], key=lambda candidate: len(candidate["resources"]))
            removed = snap["resources"].pop()["resource_id"]
            snap["relations"] = [rel for rel in snap["relations"] if rel["from"] != removed]
            snap["snapshot_id"] = validator.snapshot_identifier(snap)

        self.assert_rule_rejects(validator.check_reads, mutated(change), "recomputed read is accepted")


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
