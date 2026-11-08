"""Offline glossary navigation contract; prose remains editorial."""

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY = Path("architecture/glossary.md")
TERMS = ("epoch", "driver", "profile", "snapshot")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def sections(text):
    matches = list(re.finditer(r"^## (Epoch|Driver|Profile|Snapshot)$", text, re.M))
    return [(m.group(1).lower(), text[m.end():matches[i + 1].start()]
             if i + 1 < len(matches) else text[m.end():])
            for i, m in enumerate(matches)]


def link_errors(text, document):
    errors = []
    for raw in LINK.findall(text):
        target = urlsplit(raw)
        if target.scheme or target.netloc:
            errors.append("expected repository-local contract link: " + raw)
            continue
        path = (ROOT / document).parent / unquote(target.path)
        resolved = path.resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.is_file():
            errors.append("missing or escaping target: " + raw)
        elif target.fragment:
            headings = re.findall(r"^#+ (.+)$", resolved.read_text(), re.M)
            anchors = {re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-")
                       for h in headings}
            if unquote(target.fragment) not in anchors:
                errors.append("missing anchor: " + raw)
    return errors


class GlossaryContract(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / GLOSSARY).read_text()

    def test_four_unique_navigation_anchors(self):
        self.assertCountEqual([name for name, _ in sections(self.text)], TERMS)

    def test_each_entry_links_its_existing_contract(self):
        required = {
            "epoch": "../api/v1/kernel.md",
            "driver": "repository-ownership-v1.md",
            "profile": "../evidence/native-documentation-owners.md",
            "snapshot": "../api/v1/kernel.md",
        }
        for name, body in sections(self.text):
            with self.subTest(term=name):
                self.assertIn(required[name], LINK.findall(body))

    def test_glossary_contract_links_resolve(self):
        self.assertTrue(LINK.findall(self.text))
        self.assertEqual(link_errors(self.text, GLOSSARY), [])

    def test_readme_links_glossary(self):
        self.assertIn(GLOSSARY.as_posix(), LINK.findall((ROOT / "README.md").read_text()))

    def test_every_anchor_removal_is_detected(self):
        for term in TERMS:
            with self.subTest(term=term):
                changed = self.text.replace("## " + term.title(), "## Other", 1)
                self.assertNotIn(term, [name for name, _ in sections(changed)])

    def test_each_local_target_mutation_is_detected(self):
        for target in set(LINK.findall(self.text)):
            with self.subTest(target=target):
                changed = self.text.replace("](" + target + ")", "](missing-contract.md)", 1)
                self.assertTrue(link_errors(changed, GLOSSARY))

    def test_invalid_link_forms_are_detected(self):
        for target in ("../api/v1/kernel.md#missing-anchor", "../../outside.md",
                       "https://example.invalid/contract"):
            with self.subTest(target=target):
                self.assertTrue(link_errors("[contract](" + target + ")", GLOSSARY))


if __name__ == "__main__":
    unittest.main()
