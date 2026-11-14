#!/usr/bin/env python3
"""Dependency-free checker for a fixed JSON Schema subset.

The module supports exactly these keywords and refuses every other keyword in
a schema, so a keyword can never be silently ignored:

- annotations: ``$schema``, ``$id``, ``$defs`` (root only), ``title``,
  ``description``;
- ``$ref`` to a local ``#/$defs/<name>`` only;
- ``type`` (one of object, array, string, integer, boolean, null), ``const``,
  ``enum``;
- ``pattern``, ``minLength``, ``maxLength``;
- ``minimum``, ``maximum``;
- ``items``, ``minItems``, ``maxItems``, ``uniqueItems``;
- ``properties``, ``required``, ``additionalProperties`` (boolean);
- ``allOf``, ``anyOf``, ``oneOf``, ``not``, ``if``, ``then``, ``else``.

Values compare with JSON equality: a boolean never equals a number, an
integer never accepts a boolean, and objects compare regardless of key order.
A ``pattern`` is an unanchored search; ``$`` matches only at the very end of
the string, and the escapes whose Python meaning differs from ECMA-262
(``\\d``, ``\\w``, ``\\b`` and their negations, ``\\A``, ``\\Z``, ``\\z``) are
refused.

Usage: ``python3 scripts/json_schema_subset_v1.py SCHEMA [INSTANCE]``.
"""
from functools import lru_cache
import json
import math
import re
import sys
from typing import NamedTuple

TYPES = ("object", "array", "string", "integer", "boolean", "null")
ROOT_ONLY = frozenset({"$schema", "$id", "$defs"})
TEXT_KEYWORDS = frozenset({"$schema", "$id", "title", "description"})
COUNT_KEYWORDS = frozenset({"minLength", "maxLength", "minItems", "maxItems"})
BOUND_KEYWORDS = frozenset({"minimum", "maximum"})
FLAG_KEYWORDS = frozenset({"uniqueItems", "additionalProperties"})
SCHEMA_KEYWORDS = ("items", "not", "if", "then", "else")
SCHEMA_LIST_KEYWORDS = ("allOf", "anyOf", "oneOf")
IN_PLACE_KEYWORDS = ("not", "if", "then", "else")
REF_PATTERN = re.compile(r"#/\$defs/([A-Za-z0-9_.-]+)")
REFUSED_ESCAPES = frozenset("dDwWbBAZz")


class SchemaError(ValueError):
    """The schema uses an unsupported keyword or a malformed keyword value."""


def _escape(token):
    return str(token).replace("~", "~0").replace("/", "~1")


def _pointer(base, *tokens):
    return base + "".join("/" + _escape(token) for token in tokens)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def json_equal(left, right):
    """Return True when two JSON values are equal under JSON Schema rules."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if _is_number(left) and _is_number(right):
        return left == right
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(map(json_equal, left, right))
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(json_equal(left[key], right[key]) for key in left)
    return type(left) is type(right) and left == right


def type_matches(value, name):
    """Return True when the value has the named JSON type."""
    if name == "integer":
        if isinstance(value, float):
            return math.isfinite(value) and value.is_integer()
        return _is_number(value)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "null":
        return value is None
    expected = {"object": dict, "array": list, "string": str}[name]
    return isinstance(value, expected)


def _translate_pattern(pattern):
    """Return the Python form of an ECMA-262 pattern, refusing divergent escapes."""
    out = []
    in_class = False
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\":
            escaped = pattern[index + 1:index + 2]
            if not escaped or escaped in REFUSED_ESCAPES:
                raise SchemaError(f"pattern escape \\{escaped} is not supported")
            out.append(char + escaped)
            index += 2
            continue
        if char == "[" and not in_class:
            in_class = True
        elif char == "]" and in_class:
            in_class = False
        out.append(r"\Z" if char == "$" and not in_class else char)
        index += 1
    return "".join(out)


@lru_cache(maxsize=256)
def _compiled(pattern):
    try:
        return re.compile(_translate_pattern(pattern))
    except re.error as error:
        raise SchemaError(f"pattern {pattern!r} does not compile: {error}") from error


def _ref_name(value, root):
    match = REF_PATTERN.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise SchemaError(f"$ref {value!r} is not a local #/$defs/<name> reference")
    defs = root.get("$defs", {})
    if match.group(1) not in defs:
        raise SchemaError(f"$ref {value!r} does not resolve")
    return match.group(1)


def _check_value(key, value, pointer, root):
    """Check the form of one keyword value; walk nested schemas."""
    if key in TEXT_KEYWORDS:
        valid = isinstance(value, str)
    elif key in COUNT_KEYWORDS:
        valid = _is_count(value)
    elif key in BOUND_KEYWORDS:
        valid = isinstance(value, int) and not isinstance(value, bool) or isinstance(value, float) and math.isfinite(value)
    elif key in FLAG_KEYWORDS:
        valid = isinstance(value, bool)
    else:
        valid = _CHECKERS[key](value, pointer, root)
    if not valid:
        raise SchemaError(f"{pointer}: malformed {key} value")


def _check_schema_value(value, pointer, root):
    _walk(value, pointer, root)
    return True


def _check_schema_list(value, pointer, root):
    if not isinstance(value, list) or not value:
        return False
    for index, item in enumerate(value):
        _walk(item, _pointer(pointer, index), root)
    return True


def _check_schema_map(value, pointer, root):
    if not isinstance(value, dict):
        return False
    for name in sorted(value):
        _walk(value[name], _pointer(pointer, name), root)
    return True


def _check_required(value, _pointer_text, _root):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return False
    return len(set(value)) == len(value)


def _check_enum(value, _pointer_text, _root):
    return isinstance(value, list) and bool(value)


def _check_type(value, _pointer_text, _root):
    return isinstance(value, str) and value in TYPES


def _check_pattern(value, _pointer_text, _root):
    if not isinstance(value, str):
        return False
    _compiled(value)
    return True


def _check_ref(value, _pointer_text, root):
    _ref_name(value, root)
    return True


_CHECKERS = {
    "$defs": _check_schema_map,
    "properties": _check_schema_map,
    "required": _check_required,
    "enum": _check_enum,
    "const": lambda _value, _pointer_text, _root: True,
    "type": _check_type,
    "pattern": _check_pattern,
    "$ref": _check_ref,
    **{key: _check_schema_value for key in SCHEMA_KEYWORDS},
    **{key: _check_schema_list for key in SCHEMA_LIST_KEYWORDS},
}
SUPPORTED = frozenset(_CHECKERS) | TEXT_KEYWORDS | COUNT_KEYWORDS | BOUND_KEYWORDS | FLAG_KEYWORDS


def _walk(node, pointer, root):
    if not isinstance(node, dict):
        raise SchemaError(f"{pointer}: a schema must be a JSON object")
    for key in sorted(node):
        if key not in SUPPORTED:
            raise SchemaError(f"{pointer}: unsupported keyword {key}")
        if key in ROOT_ONLY and node is not root:
            raise SchemaError(f"{pointer}: {key} is allowed only at the schema root")
    if ("then" in node or "else" in node) and "if" not in node:
        raise SchemaError(f"{pointer}: then or else without if")
    for key in sorted(node):
        _check_value(key, node[key], _pointer(pointer, key), root)


def _in_place_refs(node, root):
    """Return the definitions a schema reaches without consuming the instance."""
    names = []
    stack = [node]
    while stack:
        current = stack.pop()
        if "$ref" in current:
            names.append(_ref_name(current["$ref"], root))
        stack.extend(current[key] for key in IN_PLACE_KEYWORDS if key in current)
        for key in SCHEMA_LIST_KEYWORDS:
            stack.extend(current.get(key, []))
    return sorted(set(names))


def _check_ref_cycles(root):
    defs = root.get("$defs", {})
    edges = {name: _in_place_refs(defs[name], root) for name in defs}
    done = set()
    for start in sorted(edges):
        _visit(start, edges, (), done)


def _visit(name, edges, trail, done):
    if name in trail:
        raise SchemaError(f"$ref cycle without an instance step: {' -> '.join(trail + (name,))}")
    if name in done:
        return
    for target in edges[name]:
        _visit(target, edges, trail + (name,), done)
    done.add(name)


def check_schema(schema):
    """Raise SchemaError unless the whole schema uses only the supported subset."""
    if not isinstance(schema, dict):
        raise SchemaError("#: the schema root must be a JSON object")
    _walk(schema, "#", schema)
    _check_ref_cycles(schema)


class Location(NamedTuple):
    """Instance pointer, schema pointer and root schema of one evaluation."""

    instance: str
    schema: str
    root: dict

    def keyword(self, *tokens):
        return self._replace(schema=_pointer(self.schema, *tokens))

    def child(self, token, *schema_tokens):
        return self._replace(instance=_pointer(self.instance, token), schema=_pointer(self.schema, *schema_tokens))

    def message(self, text):
        return f"at '{self.instance}': {text} (schema {self.schema})"


def _validate(instance, node, loc):
    found = []
    for key in sorted(node):
        handler = _VALIDATORS.get(key)
        if handler is not None:
            found.extend(handler(instance, node, loc.keyword(key)))
    return found


def _valid(instance, node, loc):
    return not _validate(instance, node, loc)


def _v_ref(instance, node, loc):
    name = _ref_name(node["$ref"], loc.root)
    return _validate(instance, loc.root["$defs"][name], loc._replace(schema=f"#/$defs/{name}"))


def _v_type(instance, node, loc):
    if type_matches(instance, node["type"]):
        return []
    return [loc.message(f"expected type {node['type']}")]


def _v_const(instance, node, loc):
    return [] if json_equal(instance, node["const"]) else [loc.message("value differs from const")]


def _v_enum(instance, node, loc):
    if any(json_equal(instance, option) for option in node["enum"]):
        return []
    return [loc.message("value is not one of enum")]


def _v_pattern(instance, node, loc):
    if not isinstance(instance, str) or _compiled(node["pattern"]).search(instance):
        return []
    return [loc.message(f"string does not match pattern {node['pattern']}")]


def _v_bound(instance, node, loc, key, ok):
    if ok(instance, node[key]):
        return []
    return [loc.message(f"{key} {node[key]} not satisfied")]


def _string_size(instance, limit, smaller):
    if not isinstance(instance, str):
        return True
    return len(instance) >= limit if smaller else len(instance) <= limit


def _array_size(instance, limit, smaller):
    if not isinstance(instance, list):
        return True
    return len(instance) >= limit if smaller else len(instance) <= limit


def _number_bound(instance, limit, smaller):
    if not _is_number(instance):
        return True
    return instance >= limit if smaller else instance <= limit


def _bounded(key, size, smaller):
    def handler(instance, node, loc):
        return _v_bound(instance, node, loc, key, lambda value, limit: size(value, limit, smaller))

    return handler


def _v_unique(instance, node, loc):
    if not node["uniqueItems"] or not isinstance(instance, list):
        return []
    for index, item in enumerate(instance):
        if any(json_equal(item, other) for other in instance[:index]):
            return [loc.message(f"item {index} repeats an earlier item")]
    return []


def _v_items(instance, node, loc):
    if not isinstance(instance, list):
        return []
    found = []
    for index, item in enumerate(instance):
        found.extend(_validate(item, node["items"], loc.child(index)))
    return found


def _v_required(instance, node, loc):
    if not isinstance(instance, dict):
        return []
    return [loc.message(f"required member {name} is missing") for name in node["required"] if name not in instance]


def _v_properties(instance, node, loc):
    if not isinstance(instance, dict):
        return []
    found = []
    for name in sorted(set(instance) & set(node["properties"])):
        found.extend(_validate(instance[name], node["properties"][name], loc.child(name, name)))
    return found


def _v_additional(instance, node, loc):
    if node["additionalProperties"] or not isinstance(instance, dict):
        return []
    extra = sorted(set(instance) - set(node.get("properties", {})))
    return [loc.message(f"member {name} is not allowed") for name in extra]


def _v_all_of(instance, node, loc):
    found = []
    for index, branch in enumerate(node["allOf"]):
        found.extend(_validate(instance, branch, loc.keyword(index)))
    return found


def _v_any_of(instance, node, loc):
    if any(_valid(instance, branch, loc.keyword(index)) for index, branch in enumerate(node["anyOf"])):
        return []
    return [loc.message("value matches no anyOf branch")]


def _v_one_of(instance, node, loc):
    matched = sum(_valid(instance, branch, loc.keyword(index)) for index, branch in enumerate(node["oneOf"]))
    if matched == 1:
        return []
    return [loc.message(f"value matches {matched} oneOf branches, expected exactly 1")]


def _v_not(instance, node, loc):
    return [loc.message("value matches the not schema")] if _valid(instance, node["not"], loc) else []


def _v_if(instance, node, loc):
    branch = "then" if _valid(instance, node["if"], loc) else "else"
    if branch not in node:
        return []
    return _validate(instance, node[branch], loc._replace(schema=loc.schema[:-len("/if")] + "/" + branch))


_VALIDATORS = {
    "$ref": _v_ref,
    "type": _v_type,
    "const": _v_const,
    "enum": _v_enum,
    "pattern": _v_pattern,
    "minLength": _bounded("minLength", _string_size, True),
    "maxLength": _bounded("maxLength", _string_size, False),
    "minItems": _bounded("minItems", _array_size, True),
    "maxItems": _bounded("maxItems", _array_size, False),
    "minimum": _bounded("minimum", _number_bound, True),
    "maximum": _bounded("maximum", _number_bound, False),
    "uniqueItems": _v_unique,
    "items": _v_items,
    "required": _v_required,
    "properties": _v_properties,
    "additionalProperties": _v_additional,
    "allOf": _v_all_of,
    "anyOf": _v_any_of,
    "oneOf": _v_one_of,
    "not": _v_not,
    "if": _v_if,
}


def errors(instance, schema):
    """Return the sorted error messages of an instance; empty when it is valid."""
    check_schema(schema)
    return sorted(set(_validate(instance, schema, Location("", "#", schema))))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"repeated object key {key!r}")
        result[key] = value
    return result


def _refuse_constant(name):
    raise ValueError(f"non-JSON constant {name}")


def load_json(path):
    """Load a JSON document, refusing repeated object keys and NaN or Infinity."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_unique_object, parse_constant=_refuse_constant)


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) not in (1, 2):
        print("usage: json_schema_subset_v1.py SCHEMA [INSTANCE]", file=sys.stderr)
        return 1
    try:
        schema = load_json(args[0])
        check_schema(schema)
        problems = errors(load_json(args[1]), schema) if len(args) == 2 else []
    except (OSError, ValueError, RecursionError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    subject = f"{args[1]} conforms to {args[0]}" if len(args) == 2 else f"{args[0]} uses only the supported subset"
    print(f"PASS: {subject}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
