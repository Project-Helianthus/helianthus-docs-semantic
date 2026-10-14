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


if __name__ == "__main__":
    unittest.main()
