#!/usr/bin/env python3
import copy
import tempfile
import unittest
from pathlib import Path

import json_schema_subset_v1 as subset
import validate_certification_references_v1 as v

SCHEMA = v.load(v.SCHEMA)
DOCUMENT = v.load(v.VECTORS)
BY_ID = {vector["id"]: vector for vector in DOCUMENT["vectors"]}
REFERENCE_MEMBERS = v.CATEGORY_MEMBERS["reference"]


def reference():
    return copy.deepcopy(BY_ID["CR-POS-01"]["document"]["entries"][0])


def gap():
    return copy.deepcopy(BY_ID["CR-POS-01"]["document"]["entries"][1])


def unavailable():
    return copy.deepcopy(BY_ID["CR-POS-01"]["document"]["entries"][2])


def document(*entries):
    return {"contract": v.CONTRACT, "entries": list(entries)}


def finding(*entries):
    return v.check_document(document(*entries), SCHEMA)


def schema_rejects(*entries):
    return bool(subset.errors(document(*entries), SCHEMA))


class VectorFileTest(unittest.TestCase):
    def test_vectors_pass(self):
        self.assertEqual(v.main([str(v.VECTORS)]), 0)

    def test_expected_outcome_must_match(self):
        vectors = copy.deepcopy(DOCUMENT["vectors"])
        vectors[0]["expected"] = {"accepted": False, "reason": "schema"}
        self.assertTrue(v.check_vector_set(vectors, SCHEMA))

    def test_a_reason_without_a_vector_is_reported(self):
        vectors = [vector for vector in DOCUMENT["vectors"] if vector["expected"].get("reason") != "refusal_missing"]
        self.assertIn("reason without a vector: refusal_missing", v.check_vector_set(vectors, SCHEMA))

    def test_a_wrong_coverage_result_is_reported(self):
        vectors = copy.deepcopy(DOCUMENT["vectors"])
        vectors[next(i for i, x in enumerate(vectors) if x["id"] == "CR-COV-01")]["coverage"][0]["result"] = "not_covered"
        self.assertTrue(v.check_vector_set(vectors, SCHEMA))

    def test_repeated_vector_id_is_reported(self):
        vectors = DOCUMENT["vectors"] + [DOCUMENT["vectors"][0]]
        self.assertIn("vector ids are not unique", v.check_vector_set(vectors, SCHEMA))

    def test_schema_rejects_every_negative_vector_the_code_rejects(self):
        code_only = {"category_conflict", "firmware_invalid", "invalid_value"}
        for vector in DOCUMENT["vectors"]:
            reason = vector["expected"].get("reason")
            if reason and reason not in code_only:
                with self.subTest(vector["id"]):
                    self.assertTrue(subset.errors(vector["document"], SCHEMA))

    def test_every_positive_vector_conforms_to_the_schema(self):
        for vector in DOCUMENT["vectors"]:
            if vector["expected"]["accepted"]:
                with self.subTest(vector["id"]):
                    self.assertEqual(subset.errors(vector["document"], SCHEMA), [])


class ReferenceMemberTest(unittest.TestCase):
    def test_reference_entry_is_accepted(self):
        self.assertIsNone(finding(reference()))

    def test_a_reference_lacking_any_one_member_fails(self):
        for name in ("source", "driver", "vendor", "flavor", "model", "firmware", "issuer",
                     "certificate_number", "issue_date", "stated_value", "url", "retrieved_on"):
            with self.subTest(name):
                entry = reference()
                del entry[name]
                self.assertEqual(finding(entry), v.Finding("missing_member", 0, name))
                self.assertTrue(schema_rejects(entry))

    def test_the_twelve_members_are_the_reference_members(self):
        self.assertEqual(set(REFERENCE_MEMBERS) - {"category"}, {
            "source", "driver", "vendor", "flavor", "model", "firmware", "issuer",
            "certificate_number", "issue_date", "stated_value", "url", "retrieved_on"})

    def test_a_missing_category_fails(self):
        entry = reference()
        del entry["category"]
        self.assertEqual(finding(entry), v.Finding("missing_member", 0, "category"))

    def test_an_unknown_category_fails(self):
        for category in ("other", ["reference"], 1):
            with self.subTest(category):
                entry = reference()
                entry["category"] = category
                self.assertEqual(finding(entry).reason, "invalid_value")

    def test_an_entry_that_is_not_an_object_fails(self):
        self.assertEqual(finding("entry"), v.Finding("schema", 0))

    def test_an_empty_text_member_fails(self):
        for name in v.TEXT_MEMBERS:
            with self.subTest(name):
                entry = reference()
                entry[name] = ""
                self.assertEqual(finding(entry), v.Finding("invalid_value", 0, name))

    def test_a_date_must_be_a_calendar_date(self):
        for name in v.DATE_MEMBERS:
            for text in ("2000-02-30", "20000201", "2000-2-1", 20000201):
                with self.subTest((name, text)):
                    entry = reference()
                    entry[name] = text
                    self.assertEqual(finding(entry), v.Finding("invalid_value", 0, name))

    def test_url_must_be_https(self):
        entry = reference()
        entry["url"] = "ftp://example.invalid/registry"
        self.assertEqual(finding(entry).reason, "invalid_value")


class SourceCategoryTest(unittest.TestCase):
    def test_a_source_other_than_certification_fails_in_every_category(self):
        for make in (reference, gap, unavailable):
            for source in ("device", "Certification", "", None, ["certification"]):
                with self.subTest((make.__name__, source)):
                    entry = make()
                    entry["source"] = source
                    self.assertEqual(finding(entry), v.Finding("source_not_certification", 0, "source"))
                    self.assertTrue(schema_rejects(entry))

    def test_a_member_naming_a_device_published_value_fails(self):
        for make in (reference, gap, unavailable):
            for name in ("device_value", "published_value", "measured_value", "reading", "device_published_accuracy"):
                with self.subTest((make.__name__, name)):
                    entry = make()
                    entry[name] = {"coefficient": "1", "exponent10": 0}
                    self.assertEqual(finding(entry), v.Finding("unknown_member", 0, name))
                    self.assertTrue(schema_rejects(entry))


class CategoryConflictTest(unittest.TestCase):
    def pair(self, **change):
        first = reference()
        second = gap()
        for name in v.IDENTITY:
            second[name] = copy.deepcopy(first[name])
        second.update(change)
        return first, second

    def test_equal_identity_with_two_categories_fails(self):
        first, second = self.pair()
        self.assertEqual(finding(first, second), v.Finding("category_conflict", 1))
        third = unavailable()
        for name in v.IDENTITY:
            third[name] = copy.deepcopy(first[name])
        self.assertEqual(finding(first, third), v.Finding("category_conflict", 1))
        self.assertEqual(finding(second, third), v.Finding("category_conflict", 1))

    def test_each_identity_field_alone_separates_two_categories(self):
        changes = {
            "driver": "other-driver",
            "vendor": "Other Vendor",
            "flavor": "other-profile",
            "model": "EX-9999",
            "firmware": {"form": "release", "release": "9.0.0"},
        }
        self.assertEqual(set(changes), set(v.IDENTITY))
        for name, value in changes.items():
            with self.subTest(name):
                first, second = self.pair(**{name: value})
                self.assertIsNone(finding(first, second))

    def test_two_entries_of_one_category_for_one_identity_are_accepted(self):
        first = reference()
        second = reference()
        second["certificate_number"] = "EX-CERT-0002"
        self.assertIsNone(finding(first, second))

    def test_the_identity_compares_the_whole_firmware_record(self):
        first, second = self.pair()
        first["firmware"] = {"form": "range", "from": "1.0", "to": "2.0", "upper_bound_stated_by": "certificate"}
        second["firmware"] = {"form": "range", "from": "1.0", "to": "2.0", "upper_bound_stated_by": "vendor_document"}
        self.assertIsNone(finding(first, second))


class GapAndUnavailableTest(unittest.TestCase):
    STATED = {"measurement_type": "active_power", "measured": True}

    def test_gap_and_unavailable_entries_are_accepted(self):
        self.assertIsNone(finding(gap()))
        self.assertIsNone(finding(unavailable()))

    def test_a_gap_carrying_a_stated_value_fails(self):
        entry = gap()
        entry["stated_value"] = self.STATED
        self.assertEqual(finding(entry), v.Finding("stated_value_not_allowed", 0, "stated_value"))
        self.assertTrue(schema_rejects(entry))

    def test_an_unavailable_entry_carrying_a_stated_value_fails(self):
        entry = unavailable()
        entry["stated_value"] = self.STATED
        self.assertEqual(finding(entry), v.Finding("stated_value_not_allowed", 0, "stated_value"))
        self.assertTrue(schema_rejects(entry))

    def test_an_unavailable_entry_without_refusal_text_fails(self):
        for text in ("MISSING", "", None, 3):
            with self.subTest(text):
                entry = unavailable()
                if text == "MISSING":
                    del entry["refusal"]
                else:
                    entry["refusal"] = text
                self.assertEqual(finding(entry), v.Finding("refusal_missing", 0, "refusal"))
                self.assertTrue(schema_rejects(entry))

    def test_refusal_text_is_not_allowed_on_other_categories(self):
        for make in (reference, gap):
            entry = make()
            entry["refusal"] = "refused"
            self.assertEqual(finding(entry), v.Finding("unknown_member", 0, "refusal"))

    def test_certificate_members_are_not_allowed_on_a_gap(self):
        for name in ("certificate_number", "issue_date"):
            entry = gap()
            entry[name] = "2000-01-01" if name == "issue_date" else "EX"
            self.assertEqual(finding(entry), v.Finding("unknown_member", 0, name))

    def test_a_gap_or_unavailable_entry_lacking_a_member_fails(self):
        for make in (gap, unavailable):
            for name in v.CATEGORY_MEMBERS[make()["category"]]:
                if name == "refusal":
                    continue
                with self.subTest((make.__name__, name)):
                    entry = make()
                    del entry[name]
                    self.assertEqual(finding(entry), v.Finding("missing_member", 0, name))


class FirmwareTest(unittest.TestCase):
    def with_firmware(self, firmware):
        entry = reference()
        entry["firmware"] = firmware
        return finding(entry)

    def test_forms_are_accepted(self):
        self.assertIsNone(self.with_firmware({"form": "not_stated"}))
        self.assertIsNone(self.with_firmware({"form": "release", "release": "1.4.0"}))
        self.assertIsNone(self.with_firmware(
            {"form": "range", "from": "1.0", "to": "2.0", "upper_bound_stated_by": "certificate"}))
        self.assertIsNone(self.with_firmware(
            {"form": "range", "from": "1.0", "to": "2.0", "upper_bound_stated_by": "vendor_document"}))

    def test_range_upper_bound_must_be_stated_by_a_certificate_or_vendor_document(self):
        for stated_by in ("MISSING", "driver", "", None, "Certificate"):
            with self.subTest(stated_by):
                firmware = {"form": "range", "from": "1.0", "to": "2.0", "upper_bound_stated_by": stated_by}
                if stated_by == "MISSING":
                    del firmware["upper_bound_stated_by"]
                self.assertEqual(self.with_firmware(firmware), v.Finding("firmware_upper_bound_unstated", 0, "firmware"))

    def test_range_without_an_upper_bound_fails(self):
        firmware = {"form": "range", "from": "1.0", "upper_bound_stated_by": "certificate"}
        self.assertEqual(self.with_firmware(firmware).reason, "firmware_invalid")

    def test_malformed_firmware_fails(self):
        for firmware in (
            "1.0", {}, {"form": "floor"}, {"form": ["release"]}, {"form": "not_stated", "release": "1.0"},
            {"form": "release"}, {"form": "release", "release": "V1.4"}, {"form": "release", "release": ""},
            {"form": "release", "release": 1}, {"form": "release", "release": "1.4", "to": "2.0"},
            {"form": "range", "from": "2.0", "to": "1.0", "upper_bound_stated_by": "certificate"},
        ):
            with self.subTest(firmware):
                self.assertEqual(self.with_firmware(firmware), v.Finding("firmware_invalid", 0, "firmware"))

    def test_a_certified_release_is_a_floor(self):
        firmware = {"form": "release", "release": "1.4.0"}
        self.assertEqual(v.coverage(firmware, "1.4.0"), "covered")
        self.assertEqual(v.coverage(firmware, "1.4.1"), "covered")
        self.assertEqual(v.coverage(firmware, "1.10.0"), "covered")
        self.assertEqual(v.coverage(firmware, "2"), "covered")
        self.assertEqual(v.coverage(firmware, "1.3.9"), "not_covered")
        self.assertEqual(v.coverage(firmware, "1.4"), "covered")
        self.assertEqual(v.coverage(firmware, "0.99.99"), "not_covered")

    def test_a_range_covers_its_bounds_and_nothing_outside(self):
        firmware = {"form": "range", "from": "1.0", "to": "2.0", "upper_bound_stated_by": "certificate"}
        self.assertEqual(v.coverage(firmware, "1.0"), "covered")
        self.assertEqual(v.coverage(firmware, "2.0.0"), "covered")
        self.assertEqual(v.coverage(firmware, "2.0.1"), "not_covered")
        self.assertEqual(v.coverage(firmware, "0.9"), "not_covered")

    def test_not_stated_covers_no_release_by_itself(self):
        self.assertEqual(v.coverage({"form": "not_stated"}, "1.0"), "not_stated")


class StatedValueTest(unittest.TestCase):
    def with_value(self, stated):
        entry = reference()
        entry["stated_value"] = stated
        return finding(entry)

    def test_each_member_alone_is_accepted(self):
        decimal = {"coefficient": "25", "exponent10": -1}
        for name in v.DECIMAL_MEMBERS:
            with self.subTest(name):
                self.assertIsNone(self.with_value({"measurement_type": "active_power", name: decimal}))
        self.assertIsNone(self.with_value({"measurement_type": "voltage", "measured": False}))

    def test_a_stated_value_that_is_not_an_object_fails(self):
        for stated in (None, [], "x", 1):
            with self.subTest(stated):
                self.assertEqual(self.with_value(stated), v.Finding("stated_value_invalid", 0, "stated_value"))

    def test_a_null_or_defaulted_member_fails(self):
        for name in STATED_NAMES:
            with self.subTest(name):
                stated = {"measurement_type": "active_power", "measured": True, name: None}
                self.assertEqual(self.with_value(stated).reason, "stated_value_invalid")

    def test_a_member_outside_the_accuracy_values_fails(self):
        for name in ("power_mode", "number_of_measurement_types", "feature_map", "percent_maximum"):
            with self.subTest(name):
                stated = {"measurement_type": "active_power", name: 1}
                self.assertEqual(self.with_value(stated).reason, "stated_value_invalid")

    def test_the_measurement_type_is_required_and_a_token(self):
        for stated in ({"measured": True}, {"measurement_type": "Active Power", "measured": True},
                       {"measurement_type": "", "measured": True}, {"measurement_type": 1, "measured": True}):
            with self.subTest(stated):
                self.assertEqual(self.with_value(stated).reason, "stated_value_invalid")

    def test_a_statement_with_no_value_fails(self):
        self.assertEqual(self.with_value({"measurement_type": "active_power"}).reason, "stated_value_invalid")

    def test_measured_must_be_a_boolean(self):
        for value in (1, "true", None):
            with self.subTest(value):
                self.assertEqual(
                    self.with_value({"measurement_type": "active_power", "measured": value}).reason,
                    "stated_value_invalid")

    def test_decimals_must_be_canonical(self):
        for decimal in (
            {"coefficient": "10", "exponent10": 0}, {"coefficient": "01", "exponent10": 0},
            {"coefficient": "0", "exponent10": 1}, {"coefficient": "-0", "exponent10": 0},
            {"coefficient": 1, "exponent10": 0}, {"coefficient": "1", "exponent10": 19},
            {"coefficient": "1", "exponent10": -19}, {"coefficient": "1", "exponent10": True},
            {"coefficient": "1", "exponent10": 1.0}, {"coefficient": "1"}, {"coefficient": "1", "exponent10": 0, "unit": "x"},
            1.5, "1.5",
        ):
            with self.subTest(decimal):
                stated = {"measurement_type": "active_power", "ratio_maximum": decimal}
                self.assertEqual(self.with_value(stated).reason, "stated_value_invalid")

    def test_canonical_decimals_are_accepted(self):
        for decimal in (
            {"coefficient": "0", "exponent10": 0}, {"coefficient": "-15", "exponent10": -3},
            {"coefficient": "1", "exponent10": 18}, {"coefficient": "1", "exponent10": -18},
        ):
            with self.subTest(decimal):
                stated = {"measurement_type": "active_power", "ratio_maximum": decimal}
                self.assertIsNone(self.with_value(stated))


STATED_NAMES = v.STATED_MEMBERS[1:]


class DocumentTest(unittest.TestCase):
    def test_an_empty_or_malformed_document_fails(self):
        for doc in (document(), {"contract": v.CONTRACT}, {"contract": "other", "entries": [reference()]},
                    {"contract": v.CONTRACT, "entries": [reference()], "extra": 1}, [], "x"):
            with self.subTest(doc):
                self.assertEqual(v.check_document(doc, SCHEMA).reason, "schema")

    def test_the_schema_uses_only_the_supported_subset(self):
        subset.check_schema(SCHEMA)

    def test_load_refuses_a_repeated_member(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repeated.json"
            path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
            with self.assertRaises(ValueError):
                v.load(path)


class StatementTest(unittest.TestCase):
    PAGES = (*v.STATEMENTS, "api/v1/certification-references-v1.md")

    def copy_pages(self, folder, edit=None):
        root = Path(folder)
        for name in self.PAGES:
            text = (v.ROOT / name).read_text(encoding="utf-8")
            if edit and edit[0] == name:
                self.assertIn(edit[1], text)
                text = text.replace(edit[1], edit[2], 1)
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return root

    def test_pages_hold_the_statements(self):
        self.assertEqual(v.check_statements(), [])

    def test_a_removed_origin_kind_or_evidence_kind_is_reported(self):
        for name, old, new in (
            ("api/v1/kernel.md", "`derived`, `declared`, `operator`", "`derived`, `operator`"),
            ("api/v1/family-catalog-v1.md", "`hardware_test_record`, `certification`, `issue`", "`hardware_test_record`, `issue`"),
            ("api/v1/driver-contract.md", "lower priority than every device source", "priority"),
            ("api/v1/certification-references-v1.md", "| `category_conflict` |", "| `conflict` |"),
        ):
            with self.subTest(name), tempfile.TemporaryDirectory() as folder:
                root = self.copy_pages(folder, (name, old, new))
                self.assertTrue(v.check_statements(root))

    def test_the_kernel_states_the_declared_origin_rules(self):
        flat = " ".join((v.ROOT / "api/v1/kernel.md").read_text(encoding="utf-8").split())
        self.assertIn("omits native source fields and carries 1 through 32 unique evidence references", flat)


if __name__ == "__main__":
    unittest.main()
