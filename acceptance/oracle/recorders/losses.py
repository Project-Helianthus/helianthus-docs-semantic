#!/usr/bin/env python3
"""Derive pre-port/losses.json: pre-port GraphQL fields that the current introspection does not publish (item 9).

The list is a derived comparison of two recorded documents, marked as such. A field that the current pin's
register_derived_names.json lists as renamed (previous_name to published_name) is a rename, not a loss, and is left out.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def snake(text):
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    return text.lower()


def fields(types):
    out = {}
    for type_index, entry in enumerate(types):
        if entry["name"].startswith("__"):
            continue
        for kind in ("fields", "inputFields"):
            for field_index, field in enumerate(entry.get(kind) or []):
                key = snake(entry["name"]) + "." + snake(field["name"])
                out.setdefault(key, {"type": entry["name"], "field": field["name"], "pointer": f"/data/__schema/types/{type_index}/{kind}/{field_index}"})
    return out


def record(introspection, output):
    item = common.entry("current", "gateway")
    source = common.unpack(item)
    current = json.loads((source / "graphql/testdata/query_schema_introspection.golden.json").read_text(encoding="utf-8"))["response"]["__schema"]["types"]
    names = json.loads((source / "graphql/testdata/register_derived_names.json").read_text(encoding="utf-8"))
    renamed = {(row["surfaces"]["graphql"], row["previous_name"]) for row in names["rows"] if row.get("previous_name") and "graphql" in row.get("surfaces", {})}
    previous = json.loads(Path(introspection).read_text(encoding="utf-8"))["data"]["__schema"]["types"]
    before, after = fields(previous), fields(current)
    losses = []
    for key in sorted(before):
        type_name, field_name = key.split(".")
        if key in after or (type_name, field_name) in renamed:
            continue
        losses.append({"surface": "graphql", "published_at_pre_port": f"{before[key]['type']}.{before[key]['field']}", "normalized": key, "pre_port_vector": "acceptance/vectors/pre-port/gateway/graphql-schema-introspection.json" + "#" + before[key]["pointer"]})
    document = {
        "format": "helianthus-oracle-pre-port-losses/1",
        "derived": True,
        "derivation": "pre-port introspection fields, snake-case normalized, not present in the current pin's introspection golden and not a previous_name row of its register_derived_names.json",
        "current_pin": {"repository": item["slug_at_pin"], "commit": item["commit"]},
        "losses": losses,
    }
    common.write(output, common.canonical(document))
    return losses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--introspection", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(len(record(args.introspection, args.output)), "losses")


if __name__ == "__main__":
    main()
