"""Differential and fail-closed checks for maintained kernel validation rules."""

import ast
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TextInput:
    def __init__(self, text):
        self.text = text

    def read_text(self, encoding):
        return self.text


class KernelRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = module_at(
            "kernel_rules_current", ROOT / "scripts/validate_kernel_v1.py"
        )
        original_path = Path(
            os.environ.get(
                "KERNEL_VALIDATOR_ORIGINAL",
                ROOT / ".tmp/before/tree/scripts/validate_kernel_v1.py",
            )
        )
        cls.original = (
            module_at("kernel_rules_original", original_path)
            if original_path.is_file()
            else None
        )
        cls.inputs = {
            "KERNEL": (ROOT / "api/v1/kernel.md").read_text(),
            "ACCEPTANCE": (ROOT / "api/v1/acceptance.md").read_text(),
            "SERIALIZATION": (ROOT / "api/v1/serialization.md").read_text(),
            "VECTORS": (ROOT / "api/v1/acceptance-vectors.json").read_text(),
        }
        cls.rules_text = (ROOT / "scripts/kernel-validation-rules.json").read_text()
        cls.scenarios = 0

    @classmethod
    def tearDownClass(cls):
        mode = "Differential" if cls.original else "Independent"
        print(f"{mode} scenarios executed: {cls.scenarios}")

    def verdict(self, module, inputs):
        for name, text in inputs.items():
            setattr(module, name, TextInput(text))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                module.main()
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            return type(error).__name__, str(error)
        return "accept", ""

    def compare(self, inputs, category=None, accepted=False):
        original = self.verdict(self.original, inputs) if self.original else None
        current = self.verdict(self.current, inputs)
        type(self).scenarios += 1
        # Identical diagnostics protect failure categories as well as verdicts.
        if self.original:
            self.assertEqual(original, current)
        if accepted:
            self.assertEqual(current[0], "accept")
        else:
            self.assertNotEqual(current[0], "accept")
            self.assertIn(category, current[1])

    def vectors_case(self, mutate, category=None, accepted=False):
        inputs = dict(self.inputs)
        data = json.loads(inputs["VECTORS"])
        mutate(data)
        inputs["VECTORS"] = json.dumps(data)
        self.compare(inputs, category, accepted)

    def test_current_documents(self):
        self.compare(dict(self.inputs), accepted=True)

    def test_missing_type(self):
        inputs = dict(self.inputs)
        start = inputs["KERNEL"].index("type SourceDescriptor struct {")
        end = inputs["KERNEL"].index("\n}", start) + 2
        inputs["KERNEL"] = inputs["KERNEL"][:start] + inputs["KERNEL"][end:]
        self.compare(inputs, "missing required fields")

    def test_every_required_field(self):
        required = self.current.rule("required-type-fields")
        for name, fields in required.items():
            for field in sorted(fields):
                with self.subTest(record=name, field=field):
                    inputs = dict(self.inputs)
                    start = inputs["KERNEL"].index(f"type {name} struct {{")
                    end = inputs["KERNEL"].index("\n}", start)
                    block = inputs["KERNEL"][start:end]
                    changed = block.replace(
                        f'json:"{field}"', f'json:"removed_{field}"'
                    )
                    changed = changed.replace(
                        f'json:"{field},omitempty"', f'json:"removed_{field},omitempty"'
                    )
                    self.assertNotEqual(block, changed)
                    inputs["KERNEL"] = (
                        inputs["KERNEL"][:start] + changed + inputs["KERNEL"][end:]
                    )
                    self.compare(inputs, "missing required fields")

    def test_extra_key_preserves_acceptance(self):
        # Existing acceptance data deliberately permits extension keys.
        self.vectors_case(lambda data: data.update(extension=True), accepted=True)
        self.vectors_case(
            lambda data: data["vectors"][0].update(extension=True), accepted=True
        )

    def test_duplicate_identity(self):
        # Vector identity has one field, id; catches removing the seen-ID guard.
        self.vectors_case(
            lambda data: data["vectors"].append(copy.deepcopy(data["vectors"][0])),
            "duplicate vector id",
        )

    def test_malformed_vector(self):
        self.vectors_case(
            lambda data: data["vectors"].__setitem__(0, "invalid"), "not an object"
        )
        self.vectors_case(
            lambda data: data["vectors"][0].update(id="invalid"), "invalid id"
        )
        self.vectors_case(
            lambda data: data["vectors"][0].update(expect=[]),
            "expect must be an object",
        )

    def test_missing_coverage(self):
        self.vectors_case(
            lambda data: data["vectors"][0].update(coverage=[]), "coverage must be"
        )

        def remove_coverage(data):
            target = data["coverage_ids"][0]
            for vector in data["vectors"]:
                vector["coverage"] = [c for c in vector["coverage"] if c != target]
                if not vector["coverage"]:
                    vector["coverage"] = [data["coverage_ids"][1]]

        self.vectors_case(remove_coverage, "coverage missing polarities")

    def test_changed_formula(self):
        # The semantic calculation recomputes a canonical evaluation digest.
        def mutate(data):
            vector = next(v for v in data["vectors"] if v["id"] == "K-POS-025")
            vector["input"]["evaluation_view"]["evaluation_digest"] = (
                "sha256:" + "0" * 64
            )

        self.vectors_case(mutate, "snapshot/evaluation binding")

    def test_requested_key_absent_from_snapshot(self):
        def mutate(data):
            vector = next(v for v in data["vectors"] if v["id"] == "K-POS-025")
            vector["input"]["requested_key"] = {"kind": "absent"}

        self.vectors_case(mutate, "K-POS-025: snapshot/evaluation binding is incomplete")

    def test_changed_revision_formula(self):
        def mutate(data):
            vector = next(v for v in data["vectors"] if v["id"] == "K-POS-024")
            conflicting = vector["input"]["conflicting_snapshot"]["revisions"]["facts"]
            vector["input"]["initial_snapshot"]["revisions"]["facts"] = conflicting

        self.vectors_case(mutate, "metadata revision sequence")

    def test_broken_reference(self):
        self.vectors_case(
            lambda data: data["vectors"][0].update(prior_vector="K-POS-999"),
            "prior_vector must reference",
        )

    def test_projection_identity_axes(self):
        # Both kind and item_id are identity fields; catches tuple-axis omission.
        for field in ("kind", "item_id"):
            with self.subTest(field=field):

                def mutate(data):
                    vector = next(v for v in data["vectors"] if v["id"] == "K-POS-016")
                    vector["input"]["dispositions"][0][field] = "unmatched"

                self.vectors_case(mutate, "projection tuple accounting")

    def test_duplicate_document_key(self):
        inputs = dict(self.inputs)
        inputs["VECTORS"] = inputs["VECTORS"].replace(
            "{", '{"extension":1,"extension":2,', 1
        )
        self.compare(inputs, "duplicate JSON key")

    def load_text(self, text):
        (ROOT / ".tmp").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "rules.json"
            path.write_text(text)
            return self.current.load_rules(path)

    def reject_rules(self, mutate, category):
        document = json.loads(self.rules_text)
        mutate(document)
        with self.assertRaisesRegex(ValueError, category):
            self.load_text(json.dumps(document))

    def test_duplicate_rule_keys(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.load_text(self.rules_text.replace("{", '{"contract":0,', 1))

    def test_unknown_kind(self):
        self.reject_rules(
            lambda d: d["rules"]["required-type-fields"].update(kind="expression"),
            "unknown rule kind",
        )

    def test_missing_rule(self):
        self.reject_rules(
            lambda d: d["rules"].pop("required-type-fields"), "missing or unused rules"
        )

    def test_unused_rule(self):
        self.reject_rules(
            lambda d: d["rules"].update(
                unused={"kind": "expected-value", "value": True}
            ),
            "missing or unused rules",
        )

    def test_extra_rule_key(self):
        self.reject_rules(
            lambda d: d["rules"]["required-type-fields"].update(extension=True),
            "invalid rule fields",
        )

    def test_malformed_types(self):
        for value in (None, [], True, 4, "not an object"):
            with self.subTest(value=value):
                self.reject_rules(
                    lambda d: d["rules"]["required-type-fields"].update(value=value),
                    "malformed rule object",
                )
        self.reject_rules(
            lambda d: d["rules"]["required-type-fields"]["value"][
                "PackRef"
            ].__setitem__(0, False),
            "malformed rule value type",
        )

    def test_duplicate_set_members(self):
        def duplicate(document):
            fields = document["rules"]["required-type-fields"]["value"]["PackRef"]
            fields[1] = fields[0]

        self.reject_rules(duplicate, "duplicate rule set member")

    def test_each_rule_rejects_malformed_value(self):
        for name in self.current.RULE_SCHEMAS:
            with self.subTest(behavior=name):
                self.reject_rules(
                    lambda d: d["rules"][name].update(value=None), "malformed rule"
                )

    def test_rule_inventory_is_exhaustively_consumed(self):
        tree = ast.parse((ROOT / "scripts/validate_kernel_v1.py").read_text())
        names = {
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "rule"
        }
        self.assertEqual(names, set(self.current.RULE_SCHEMAS))
        self.assertEqual(names, set(json.loads(self.rules_text)["rules"]))

    def test_rules_control_requirements(self):
        before = copy.deepcopy(self.current.RULES)
        try:
            self.current.RULES["required-hooks"] = ("absent synthetic required hook",)
            verdict = self.verdict(self.current, dict(self.inputs))
            self.assertIn("required pack hook is missing", verdict[1])
        finally:
            self.current.RULES = before


if __name__ == "__main__":
    unittest.main(verbosity=2)
