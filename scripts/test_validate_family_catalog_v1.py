#!/usr/bin/env python3
import unittest
from pathlib import Path

import validate_family_catalog_v1 as v

TEXT = v.PAGE.read_text(encoding="utf-8")


class FamilyCatalogPageTest(unittest.TestCase):
    def test_page_passes(self):
        self.assertEqual(v.check(TEXT), [])

    def test_missing_reason_rejected(self):
        mutated = TEXT.replace("| `no_producer` |", "| `other_reason` |")
        self.assertTrue(v.check(mutated))

    def test_extra_reason_rejected(self):
        mutated = TEXT.replace("| `no_producer` |", "| `extra_reason` | x |\n| `no_producer` |")
        self.assertTrue(v.check(mutated))

    def test_missing_composition_rejected(self):
        self.assertTrue(v.check(TEXT.replace("| `provider_local` |", "| `x` |")))

    def test_missing_rule_rejected(self):
        self.assertTrue(v.check(TEXT.replace("gateway_composition", "gw")))

    def test_missing_member_rejected(self):
        self.assertTrue(v.check(TEXT.replace("composition_verified", "cv")))


if __name__ == "__main__":
    unittest.main()
