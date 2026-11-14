#!/usr/bin/env python3
import unittest

import validate_family_catalog_v1 as v

TEXT = v.PAGE.read_text(encoding="utf-8")


def mutate(old, new):
    assert old in TEXT, old
    return TEXT.replace(old, new, 1)


class FamilyCatalogPageTest(unittest.TestCase):
    def rejected(self, text):
        self.assertTrue(v.check(text))

    def test_page_passes(self):
        self.assertEqual(v.check(TEXT), [])

    def test_reason_removed_or_added(self):
        self.rejected(mutate("| `no_producer` |", "| `other_reason` |"))
        self.rejected(mutate("| `no_producer` |", "| `extra_reason` | x |\n| `no_producer` |"))

    def test_invented_composition_rejected(self):
        self.rejected(mutate("| `not_composed` | No", "| `invented` | x |\n| `not_composed` | No"))

    def test_composition_removed(self):
        self.rejected(mutate("| `provider_local` |", "| `x` |"))

    def test_document_member_added_or_removed(self):
        self.rejected(mutate("| `families` |", "| `extra_member` | string | x |\n| `families` |"))
        self.rejected(mutate("| `contract` |", "| `contract_x` |"))

    def test_family_id_row_deleted(self):
        lines = [l for l in TEXT.splitlines(keepends=True) if not l.startswith("| `family_id` |")]
        self.assertNotEqual("".join(lines), TEXT)
        self.rejected("".join(lines))

    def test_evidence_member_deleted(self):
        lines = [l for l in TEXT.splitlines(keepends=True) if not l.startswith("| `locator` |")]
        self.rejected("".join(lines))

    def test_not_composed_rule_reversed(self):
        self.rejected(mutate("MUST have `composition_verified=false`", "MAY have `composition_verified=true`"))

    def test_not_composed_evidence_prohibition_deleted(self):
        self.rejected(mutate("MUST NOT carry\n  any `gateway_composition` evidence entry", "MAY carry\n  any `gateway_composition` evidence entry"))

    def test_gateway_pin_rule_deleted(self):
        self.rejected(mutate("followed by the\nfull 40-character commit SHA", "followed by a revision"))

    def test_owner_forms_deleted(self):
        self.rejected(mutate("names an issue or pull request thread", "names a thread"))

    def test_trailing_data_rule_deleted(self):
        self.rejected(mutate("Trailing data after the document is rejected", "Trailing data is fine"))

    def test_unknown_member_rule_deleted(self):
        self.rejected(mutate("no other member is allowed at any object level", "other members are fine"))

    def test_sections_required(self):
        self.rejected(mutate("## Falsifiers", "## Other"))
        self.rejected(mutate("## Unresolved questions", "## Other"))

    def test_state_and_intake_rules(self):
        self.rejected(mutate("`unknown`, `rejected`, with", "`unknown`, with"))
        self.rejected(mutate("is not fabricated", "is fine"))


def mutate_once(old, new):
    assert TEXT.count(old) == 1, old
    return TEXT.replace(old, new, 1)


class FurtherSemanticPacksTest(unittest.TestCase):
    def rejected(self, text):
        self.assertTrue(v.check(text))

    def test_member_list_names_further_packs_after_semantic_pack(self):
        self.assertEqual(v.FAMILY_MEMBERS, [
            "family_id", "name", "native_owner", "semantic_pack",
            "further_semantic_packs", "state", "composition",
            "composition_verified", "reason", "evidence",
        ])

    def test_further_packs_row_deleted_renamed_or_moved(self):
        row = next(line for line in TEXT.splitlines(keepends=True) if line.startswith("| `further_semantic_packs` |"))
        self.rejected(mutate_once(row, ""))
        self.rejected(mutate_once("| `further_semantic_packs` |", "| `further_semantic_pack` |"))
        self.rejected(mutate_once(row, "").replace("| `semantic_pack` |", row + "| `semantic_pack` |", 1))

    def test_semantic_pack_row_kept(self):
        self.rejected(mutate_once(
            "Exact `PackRef` of the accepted capability pack the family maps to, or empty.",
            "The primary pack of the family.",
        ))

    def test_optional_member_rule(self):
        self.rejected(mutate_once("Every member except `further_semantic_packs` is required", "All members are required"))

    def test_list_bound(self):
        self.rejected(mutate_once("1 through 4", "1 through 5"))
        self.rejected(mutate_once("1 through 4", "0 through 4"))

    def test_uniqueness_and_semantic_pack_exclusion(self):
        self.rejected(mutate_once("Its entries are unique", "Its entries may repeat"))
        self.rejected(mutate_once("no entry equals `semantic_pack`", "an entry may equal `semantic_pack`"))

    def test_requires_non_empty_semantic_pack(self):
        self.rejected(mutate_once("allowed only when `semantic_pack` is non-empty", "allowed with an empty `semantic_pack`"))

    def test_omitted_when_empty(self):
        self.rejected(mutate_once("It is omitted when the family has no further pack", "It may be empty"))
        self.rejected(mutate_once("A present empty array is rejected", "A present empty array is accepted"))

    def test_canonical_order(self):
        self.rejected(mutate_once("ascending byte order", "any order"))
        self.rejected(mutate_once("`semantic_pack` sorts before every entry", "`semantic_pack` may sort anywhere"))

    def test_no_primary_pack(self):
        self.rejected(mutate_once("No pack is primary", "`semantic_pack` is primary"))

    def test_mapping_gate_cross_check(self):
        self.rejected(mutate_once("include the gate's pack", "may omit the gate's pack"))
        self.rejected(mutate_once("for every accepted mapping gate", "for some accepted mapping gate"))

    def test_rules_bound_to_their_section(self):
        self.rejected(mutate_once("## Packs of a row", "## Other"))


if __name__ == "__main__":
    unittest.main()
