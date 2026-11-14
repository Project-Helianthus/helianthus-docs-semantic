#!/usr/bin/env python3
"""Tests of the dependency-free JSON Schema subset checker."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import json_schema_subset_v1 as subset

# keyword, schema, a valid instance, an invalid instance
CASES = [
    ("$ref", {"$defs": {"text": {"type": "string"}}, "$ref": "#/$defs/text"}, "a", 1),
    ("type object", {"type": "object"}, {}, []),
    ("type array", {"type": "array"}, [], {}),
    ("type string", {"type": "string"}, "a", None),
    ("type integer", {"type": "integer"}, 3, 1.5),
    ("type boolean", {"type": "boolean"}, False, 0),
    ("type null", {"type": "null"}, None, False),
    ("const", {"const": {"a": [1, True]}}, {"a": [1, True]}, {"a": [1, 1]}),
    ("enum", {"enum": ["x", None]}, None, "y"),
    ("pattern", {"pattern": "b+"}, "abbc", "ac"),
    ("pattern end anchor", {"pattern": "^a$"}, "a", "a\n"),
    ("minLength", {"minLength": 2}, "éé", "é"),
    ("maxLength", {"maxLength": 2}, "\U0001f600\U0001f600", "abc"),
    ("minimum", {"minimum": 1}, 1, 0),
    ("maximum", {"maximum": 1}, 1, 1.5),
    ("minItems", {"minItems": 1}, [0], []),
    ("maxItems", {"maxItems": 1}, [0], [0, 0]),
    ("uniqueItems", {"uniqueItems": True}, [1, "1"], [1, 1]),
    ("items", {"items": {"type": "string"}}, ["a"], ["a", 1]),
    ("required", {"required": ["a"]}, {"a": 1}, {}),
    ("properties", {"properties": {"a": {"type": "string"}}}, {"a": "x"}, {"a": 1}),
    ("additionalProperties", {"properties": {"a": {}}, "additionalProperties": False}, {"a": 1}, {"b": 1}),
    ("allOf", {"allOf": [{"minimum": 1}, {"maximum": 2}]}, 2, 3),
    ("anyOf", {"anyOf": [{"type": "string"}, {"type": "null"}]}, None, 1),
    ("oneOf", {"oneOf": [{"type": "integer"}, {"minimum": 0}]}, -1, 1),
    ("not", {"not": {"type": "string"}}, 1, "a"),
    ("if then", {"if": {"type": "integer"}, "then": {"minimum": 0}}, 1, -1),
    ("if else", {"if": {"type": "integer"}, "else": {"type": "string"}}, "a", None),
]

ANNOTATED = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.org/synthetic.schema.json",
    "$defs": {"unused": {"title": "t", "description": "d"}},
    "title": "synthetic",
    "description": "synthetic",
    "type": "object",
}

MALFORMED = {
    "$schema": {"$schema": 1},
    "$id": {"$id": None},
    "$defs": {"$defs": []},
    "nested $defs": {"properties": {"a": {"$defs": {}}}},
    "nested $id": {"properties": {"a": {"$id": "x"}}},
    "title": {"title": 1},
    "description": {"description": []},
    "type list": {"type": ["string"]},
    "type number": {"type": "number"},
    "required string": {"required": "a"},
    "required repeated": {"required": ["a", "a"]},
    "minItems text": {"minItems": "1"},
    "minItems boolean": {"minItems": True},
    "minLength negative": {"minLength": -1},
    "minimum boolean": {"minimum": False},
    "uniqueItems number": {"uniqueItems": 1},
    "additionalProperties schema": {"additionalProperties": {"type": "string"}},
    "enum empty": {"enum": []},
    "allOf empty": {"allOf": []},
    "anyOf object": {"anyOf": {}},
    "boolean subschema": {"items": True},
    "pattern does not compile": {"pattern": "("},
    "pattern digit escape": {"pattern": "\\d"},
    "pattern end escape": {"pattern": "a\\Z"},
    "properties list": {"properties": []},
    "schema not an object": [],
}

UNSUPPORTED = [
    "format", "dependentRequired", "prefixItems", "patternProperties", "contains",
    "exclusiveMinimum", "multipleOf", "minProperties", "unevaluatedProperties", "$anchor",
    "$dynamicRef", "additionalItems", "definitions", "propertyNames",
]

BAD_REFS = [
    "https://example.org/remote.schema.json#/$defs/text",
    "other.schema.json#/$defs/text",
    "#/definitions/text",
    "#",
    "#/$defs/missing",
    "#/$defs/text/properties",
]


class KeywordTest(unittest.TestCase):
    def test_each_keyword_accepts_and_rejects(self):
        for name, schema, good, bad in CASES:
            with self.subTest(keyword=name):
                subset.check_schema(schema)
                self.assertEqual(subset.errors(good, schema), [])
                self.assertTrue(subset.errors(bad, schema))

    def test_annotations_accepted(self):
        subset.check_schema(ANNOTATED)
        self.assertEqual(subset.errors({}, ANNOTATED), [])
        self.assertTrue(subset.errors([], ANNOTATED))

    def test_malformed_values_refused(self):
        for name, schema in MALFORMED.items():
            with self.subTest(case=name), self.assertRaises(subset.SchemaError):
                subset.check_schema(schema)

    def test_keyword_checks_ignore_other_types(self):
        schema = {"minLength": 1, "minItems": 1, "minimum": 1, "required": ["a"], "pattern": "x"}
        for instance in (None, True, 1.5, "x", [0], {"a": 1}):
            with self.subTest(instance=instance):
                self.assertEqual(subset.errors(instance, schema), [])


class RefusalTest(unittest.TestCase):
    def test_unsupported_keywords_refused(self):
        for keyword in UNSUPPORTED:
            for schema in ({keyword: {}}, {"properties": {"a": {keyword: 1}}}):
                with self.subTest(keyword=keyword, schema=schema), self.assertRaises(subset.SchemaError):
                    subset.check_schema(schema)

    def test_unsupported_keyword_refused_by_errors(self):
        with self.assertRaises(subset.SchemaError):
            subset.errors("a", {"format": "date"})

    def test_non_local_or_unresolved_ref_refused(self):
        for ref in BAD_REFS:
            schema = {"$defs": {"text": {"type": "string"}}, "$ref": ref}
            with self.subTest(ref=ref), self.assertRaises(subset.SchemaError):
                subset.check_schema(schema)

    def test_then_or_else_without_if_refused(self):
        for schema in ({"then": {}}, {"else": {}}, {"properties": {"a": {"then": {"type": "string"}}}}):
            with self.subTest(schema=schema), self.assertRaises(subset.SchemaError):
                subset.check_schema(schema)

    def test_ref_cycle_without_instance_step_refused(self):
        schema = {"$defs": {"a": {"$ref": "#/$defs/b"}, "b": {"allOf": [{"not": {"$ref": "#/$defs/a"}}]}}}
        with self.assertRaises(subset.SchemaError):
            subset.check_schema(schema)

    def test_ref_recursion_through_items_accepted(self):
        schema = {"$defs": {"tree": {"type": "array", "items": {"$ref": "#/$defs/tree"}}}, "$ref": "#/$defs/tree"}
        self.assertEqual(subset.errors([[[]], []], schema), [])
        self.assertTrue(subset.errors([[1]], schema))


class EqualityTest(unittest.TestCase):
    def test_true_never_equals_one(self):
        self.assertTrue(subset.errors(1, {"const": True}))
        self.assertTrue(subset.errors(True, {"const": 1}))
        self.assertTrue(subset.errors(0, {"const": False}))
        self.assertTrue(subset.errors(True, {"enum": [1, 0]}))
        self.assertTrue(subset.errors(1, {"enum": [True, False]}))
        self.assertEqual(subset.errors([1, True], {"uniqueItems": True}), [])
        self.assertEqual(subset.errors([0, False], {"uniqueItems": True}), [])

    def test_integer_never_accepts_boolean(self):
        self.assertTrue(subset.errors(True, {"type": "integer"}))
        self.assertTrue(subset.errors(False, {"type": "integer"}))
        self.assertEqual(subset.errors(2.0, {"type": "integer"}), [])
        self.assertEqual(subset.errors(True, {"minimum": 5}), [])

    def test_numbers_compare_by_value(self):
        self.assertEqual(subset.errors(1.0, {"const": 1}), [])
        self.assertTrue(subset.errors([1, 1.0], {"uniqueItems": True}))

    def test_unique_items_over_reordered_objects(self):
        repeated = [{"a": 1, "b": [True]}, {"b": [True], "a": 1}]
        self.assertTrue(subset.errors(repeated, {"uniqueItems": True}))
        self.assertEqual(subset.errors([{"a": 1}, {"a": True}], {"uniqueItems": True}), [])

    def test_const_over_reordered_objects(self):
        self.assertEqual(subset.errors({"b": 2, "a": 1}, {"const": {"a": 1, "b": 2}}), [])
        self.assertTrue(subset.errors({"a": 1}, {"const": {"a": 1, "b": 2}}))


class MessageTest(unittest.TestCase):
    SCHEMA = {
        "type": "object",
        "required": ["z", "a"],
        "additionalProperties": False,
        "properties": {"m/n": {"type": "string"}, "list": {"items": {"type": "integer"}}},
    }

    def test_messages_are_sorted_and_deterministic(self):
        instance = {"m/n": 1, "list": [1, "x", True], "extra": None}
        first = subset.errors(instance, self.SCHEMA)
        self.assertEqual(first, sorted(first))
        self.assertEqual(first, subset.errors(dict(reversed(list(instance.items()))), self.SCHEMA))
        self.assertEqual(first, [
            "at '': member extra is not allowed (schema #/additionalProperties)",
            "at '': required member a is missing (schema #/required)",
            "at '': required member z is missing (schema #/required)",
            "at '/list/1': expected type integer (schema #/properties/list/items/type)",
            "at '/list/2': expected type integer (schema #/properties/list/items/type)",
            "at '/m~1n': expected type string (schema #/properties/m~1n/type)",
        ])

    def test_conditional_messages_name_the_branch(self):
        schema = {"if": {"type": "integer"}, "then": {"minimum": 0}, "else": {"type": "string"}}
        self.assertEqual(subset.errors(-1, schema), ["at '': minimum 0 not satisfied (schema #/then/minimum)"])
        self.assertEqual(subset.errors(None, schema), ["at '': expected type string (schema #/else/type)"])


class CommandLineTest(unittest.TestCase):
    def run_main(self, *texts):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, text in enumerate(texts):
                path = Path(directory) / f"document-{index}.json"
                path.write_text(text, encoding="utf-8")
                paths.append(str(path))
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = subset.main(paths)
        return status, out.getvalue(), err.getvalue()

    def test_schema_and_instance_pass(self):
        status, out, _ = self.run_main('{"type": "object"}', '{"a": 1}')
        self.assertEqual(status, 0)
        self.assertEqual(len(out.splitlines()), 1)
        self.assertTrue(out.startswith("PASS"))

    def test_invalid_instance_fails(self):
        status, out, err = self.run_main('{"required": ["a"]}', "{}")
        self.assertEqual((status, out), (1, ""))
        self.assertIn("required member a is missing", err)

    def test_repeated_keys_and_constants_refused(self):
        self.assertEqual(self.run_main('{"type": "object"}', '{"a": 1, "a": 2}')[0], 1)
        self.assertEqual(self.run_main('{"type": "object", "type": "array"}')[0], 1)
        self.assertEqual(self.run_main('{"maximum": NaN}')[0], 1)

    def test_unsupported_schema_and_usage_fail(self):
        self.assertEqual(self.run_main('{"format": "date"}')[0], 1)
        self.assertEqual(self.run_main()[0], 1)


if __name__ == "__main__":
    unittest.main()
