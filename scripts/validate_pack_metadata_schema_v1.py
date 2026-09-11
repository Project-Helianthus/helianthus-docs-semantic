#!/usr/bin/env python3
"""Repository-contained Draft 2020-12 subset validator for metadata v1."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "api/v1/pack-metadata-v1.schema.json"
FIXTURE = ROOT / "api/v1/pack-metadata-v1.json"

def load(path): return json.loads(path.read_text(encoding="utf-8"))
def validate(value, schema, root, path="$"):
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"): raise ValueError(f"{path}: external schema ref")
        target = root
        for part in ref[2:].split("/"): target = target[part]
        return validate(value, target, root, path)
    if "oneOf" in schema:
        matches = []
        for option in schema["oneOf"]:
            try: validate(value, option, root, path); matches.append(option)
            except ValueError: pass
        if len(matches) != 1: raise ValueError(f"{path}: oneOf")
        return
    expected = schema.get("type")
    mapping = {"object": dict, "array": list, "string": str, "null": type(None)}
    if expected:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(isinstance(value, mapping[name]) for name in choices): raise ValueError(f"{path}: type")
    if "const" in schema and value != schema["const"]: raise ValueError(f"{path}: const")
    if "enum" in schema and value not in schema["enum"]: raise ValueError(f"{path}: enum")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0): raise ValueError(f"{path}: minLength")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value): raise ValueError(f"{path}: pattern")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)): raise ValueError(f"{path}: item count")
        if "items" in schema:
            for index, item in enumerate(value): validate(item, schema["items"], root, f"{path}[{index}]")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - set(value)
        if missing: raise ValueError(f"{path}: required")
        if schema.get("additionalProperties") is False and set(value) - set(properties): raise ValueError(f"{path}: additionalProperties")
        for name, item in value.items():
            if name in properties: validate(item, properties[name], root, f"{path}.{name}")

def exact_five_packs(document):
    actual = {(item["pack"]["id"], item["pack"]["version"]) for item in document["packs"]}
    expected = {("helianthus.pack.thermal", "1.0.0"), ("helianthus.pack.pv", "1.0.0"), ("helianthus.pack.storage", "1.1.0"), ("helianthus.pack.evse", "1.0.0"), ("helianthus.pack.infrastructure", "1.0.0")}
    if actual != expected: raise ValueError("exact accepted five-pack set")

def validate_document(document):
    schema = load(SCHEMA); validate(document, schema, schema); exact_five_packs(document)
def main():
    validate_document(load(FIXTURE)); print("pack metadata v1 Draft 2020-12 schema: PASS")
if __name__ == "__main__": main()
