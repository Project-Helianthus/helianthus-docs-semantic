"""Synthetic ratchet and cached-tool boundary checks."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "readability", Path(__file__).resolve().parents[1] / "scripts/check_readability.py"
)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class ReadabilityGateTests(unittest.TestCase):
    def setUp(self):
        self.record = dict(path="scripts/sample.py", symbol="evaluate", rule="C901", count=12)
        self.key = GATE.record_key(self.record)

    def document(self, records):
        return dict(ruff_version=GATE.RUFF_VERSION, generation="synthetic measurement", records=records)

    def test_clean_and_existing_debt_are_accepted(self):
        self.assertEqual(GATE.compare_records({}, {}), [])
        self.assertEqual(GATE.compare_records({self.key: 12}, {self.key: 12}), [])

    def test_each_identity_field_distinguishes_new_debt(self):
        # Each mutation defeats a comparison that omits this identity field.
        for field, value in [("path", "tests/sample.py"), ("symbol", "other"), ("rule", "PLR0915")]:
            with self.subTest(field=field):
                changed = GATE.record_key(dict(self.record, **{field: value}))
                errors = GATE.compare_records({self.key: 12, changed: 12}, {self.key: 12})
                self.assertTrue(any("new finding" in error for error in errors))

    def test_increased_counts_fail_and_reductions_pass(self):
        self.assertTrue(GATE.compare_records({self.key: 13}, {self.key: 12}))
        self.assertEqual(GATE.compare_records({self.key: 11}, {self.key: 12}), [])

    def test_deleted_debt_requires_removing_unused_entry(self):
        self.assertIn("unused baseline", GATE.compare_records({}, {self.key: 12})[0])
        self.assertEqual(GATE.compare_records({}, {}), [])

    def test_duplicate_and_malformed_baselines_fail(self):
        with self.assertRaises(ValueError):
            GATE.baseline_records(self.document([self.record, self.record]))
        for field, value in [("count", True), ("count", 0), ("path", "../sample.py"),
                             ("symbol", ""), ("rule", "bad")]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                GATE.baseline_records(self.document([dict(self.record, **{field: value})]))
        for document in [{}, self.document({}), dict(self.document([]), ruff_version="unknown")]:
            with self.assertRaises(ValueError):
                GATE.baseline_records(document)
        with self.assertRaises(ValueError):
            GATE.read_json('{"records": [], "records": []}')

    def test_nested_and_moved_symbols_keep_lexical_identity(self):
        source = "class Parser:\n    def evaluate(self):\n        return 1\n"
        self.assertEqual(GATE.lexical_symbol(source, 2), "Parser.evaluate")
        self.assertEqual(GATE.lexical_symbol("\n\n" + source, 4), "Parser.evaluate")
        self.assertNotEqual(GATE.lexical_symbol(source.replace("Parser", "Reader"), 2), "Parser.evaluate")

    def test_scopes_nested_in_conditionals_keep_lexical_identity(self):
        source = (
            "import sys\n"
            "if sys.platform:\n"
            "    def first():\n"
            "        return 1\n"
            "else:\n"
            "    class Box:\n"
            "        def second(self):\n"
            "            return 2\n"
            "try:\n"
            "    pass\n"
            "except ImportError:\n"
            "    for item in []:\n"
            "        def third():\n"
            "            return 3\n"
        )
        self.assertEqual(GATE.lexical_symbol(source, 4), "first")
        self.assertEqual(GATE.lexical_symbol(source, 8), "Box.second")
        self.assertEqual(GATE.lexical_symbol(source, 14), "third")
        self.assertEqual(GATE.lexical_symbol(source, 10), "<module>")
        renamed = source.replace("first", "other")
        self.assertNotEqual(GATE.lexical_symbol(renamed, 4), GATE.lexical_symbol(source, 4))

    def test_tool_failures_and_malformed_json_fail_closed(self):
        version = subprocess.CompletedProcess([], 0, f"ruff {GATE.RUFF_VERSION}\n", "")
        for code, output in [(2, "[]"), (0, "broken"), (0, "{}"), (1, "[]"), (0, "[{}]")]:
            responses = iter([version, subprocess.CompletedProcess([], code, output, "failure")])
            with self.subTest(code=code, output=output), self.assertRaises((ValueError, KeyError)):
                GATE.run_ruff(Path.cwd(), runner=lambda *args, **kwargs: next(responses))
        for result in [subprocess.CompletedProcess([], 0, "ruff unknown", ""),
                       subprocess.CompletedProcess([], 2, "", "failure")]:
            with self.assertRaises(ValueError):
                GATE.run_ruff(Path.cwd(), runner=lambda *args, **kwargs: result)
        for error in [FileNotFoundError("missing tool"), subprocess.TimeoutExpired("ruff", 180)]:
            def fail(*args, **kwargs):
                raise error
            with self.assertRaises(type(error)):
                GATE.run_ruff(Path.cwd(), runner=fail)

    def test_real_ruff_rejects_new_function_in_baselined_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "tests").mkdir()
            (root / "ruff.toml").write_text((GATE.ROOT / "ruff.toml").read_text())
            source = "def evaluate(value):\n" + "".join(
                f"    if value == {index}:\n        return {index}\n" for index in range(11)
            ) + "    return None\n"
            path = root / "scripts/sample.py"
            path.write_text(source)
            before = GATE.run_ruff(root)
            self.assertEqual(before[("scripts/sample.py", "evaluate", "C901")], 12)
            path.write_text("\n\n" + source)
            self.assertEqual(GATE.run_ruff(root), before)
            path.write_text(source + source.replace("evaluate", "another"))
            self.assertTrue(any("new finding" in error for error in GATE.compare_records(GATE.run_ruff(root), before)))
            path.write_text(source.replace("    return None\n", "    if value == 99:\n        return 99\n    return None\n"))
            self.assertTrue(any("increased finding" in error for error in GATE.compare_records(GATE.run_ruff(root), before)))
            path.write_text(source.replace("    if value == 10:\n        return 10\n", ""))
            self.assertEqual(GATE.compare_records(GATE.run_ruff(root), before), [])
            path.write_text("def evaluate(value):\n    return value\n")
            self.assertTrue(any("unused baseline" in error for error in GATE.compare_records(GATE.run_ruff(root), before)))

    def test_statement_and_naming_measurements_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "tests").mkdir()
            (root / "ruff.toml").write_text((GATE.ROOT / "ruff.toml").read_text())
            (root / "scripts/sample.py").write_text(
                "def evaluate(value):\n" + "    value += 1\n" * 51 + "    return value\n"
                + "\ndef BadName(OtherName):\n    return OtherName\n"
            )
            current = GATE.run_ruff(root)
            self.assertEqual(current[("scripts/sample.py", "evaluate", "PLR0915")], 51)
            self.assertEqual({key[2] for key in current}, {"PLR0915", "N802", "N803"})


if __name__ == "__main__":
    unittest.main()
