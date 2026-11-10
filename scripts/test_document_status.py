#!/usr/bin/env python3
"""Exercise status parsing and path-specific baseline behavior."""
import json
import tempfile
import unittest
from pathlib import Path
from check_document_status import BASELINE, ROOT, check, status


class StatusTests(unittest.TestCase):
    def test_repository_baseline(self):
        baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
        self.assertEqual(check(ROOT, baseline), [])

    def test_preserves_free_text(self):
        for value in ('candidate, proposed and not accepted', 'accepted without qualification'):
            self.assertEqual(status('---\nstatus: "' + value + '"\n---\n'), value)

    def test_rejects_unsupported_headers(self):
        for header in ('status: candidate', 'status: ""', 'status: "x"\nstatus: "y"', 'title: "x"', 'status: "x"\nother: "x"', 'status: "bad\\q"'):
            with self.subTest(header=header), self.assertRaises(ValueError):
                status('---\n' + header + '\n---\n')
        with self.assertRaises(ValueError):
            status('---\nstatus: "x"\n')
        with self.assertRaises(ValueError):
            status('---\nstatus: "x"\n---\n---\n')

    def test_ratchet_paths_and_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'old.md').write_text('old')
            (root / 'AGENTS.md').write_text('tooling')
            baseline = {'missing_status': ['old.md'], 'excluded': ['AGENTS.md']}
            self.assertEqual(check(root, baseline, {'old.md'}), [])
            self.assertTrue(check(root, {'missing_status': ['old.md', 'new.md'], 'excluded': ['AGENTS.md']}, {'old.md'}))
            (root / 'new.md').write_text('new')
            self.assertTrue(any('new.md: missing' in e for e in check(root, baseline, {'old.md'})))
            (root / 'new.md').write_text('---\nstatus: "candidate"\n---\n')
            self.assertEqual(check(root, baseline, {'old.md'}), [])
            (root / 'old.md').rename(root / 'renamed.md')
            errors = check(root, baseline, {'old.md'})
            self.assertTrue(any('old.md: stale' in e for e in errors))
            self.assertTrue(any('renamed.md: missing' in e for e in errors))
            (root / 'renamed.md').rename(root / 'old.md')
            (root / 'old.md').write_text('---\nstatus: "accepted"\n---\n')
            self.assertTrue(any('stale missing-status' in e for e in check(root, baseline, {'old.md'})))


if __name__ == '__main__':
    unittest.main()
