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


TYPED_ROOTS = ("zones", "dhw", "circuits", "radioDevices", "solar", "cylinders", "energyTotals", "boilerStatus", "system", "schedules", "adapterHardwareInfo")
MCP_TOOL_OF_ROOT = {
    "zones": "ebus.v1.semantic.zones.get", "dhw": "ebus.v1.semantic.dhw.get", "circuits": "ebus.v1.semantic.circuits.get",
    "radioDevices": "ebus.v1.semantic.radio_devices.get", "solar": "ebus.v1.semantic.solar.get", "cylinders": "ebus.v1.semantic.cylinders.get",
    "energyTotals": "ebus.v1.semantic.energy_totals.get", "boilerStatus": "ebus.v1.semantic.boiler_status.get", "system": "ebus.v1.semantic.system.get",
    "schedules": "ebus.v1.semantic.schedules.get", "adapterHardwareInfo": "ebus.v1.semantic.adapter_info.get",
}
TYPED_DIRECTORY = "acceptance/vectors/pre-port/gateway/typed/"


def unwrap(reference):
    """Name, kind and whether a list sits in the wrapper chain of an introspection type reference."""
    is_list = False
    while reference.get("ofType"):
        is_list = is_list or reference["kind"] == "LIST"
        reference = reference["ofType"]
    return reference["name"], reference["kind"], is_list


def paths_to_fields(types):
    """Breadth-first walk from each typed root query: type name -> (root, [(field, is_list), ...]) of its shortest path."""
    by_name = {entry["name"]: entry for entry in types}
    found = {}
    for root in TYPED_ROOTS:
        field = next((f for f in by_name["Query"]["fields"] if f["name"] == root), None)
        if field is None:
            continue
        name, _kind, is_list = unwrap(field["type"])
        queue = [(name, [(root, is_list)])]
        while queue:
            current, path = queue.pop(0)
            if current in found:
                continue
            found[current] = (root, path)
            for child in by_name[current].get("fields") or []:
                child_name, child_kind, child_list = unwrap(child["type"])
                if child_kind == "OBJECT" and "_" not in child["name"]:
                    queue.append((child_name, path + [(child["name"], child_list)]))
    return found


def resolve(document, pointer):
    node = document
    for part in pointer.lstrip("/").split("/"):
        if isinstance(node, list):
            node = node[int(part)] if int(part) < len(node) else None
        elif isinstance(node, dict):
            node = node.get(part)
        else:
            return None
        if node is None:
            return None
    return node


def value_links(types, typed, mcp, loss_names):
    """For each loss (Type.field): the pointer into the typed GraphQL vector and into the MCP vector at which a non-null value is shown."""
    where = paths_to_fields(types)
    out = {}
    for type_name, field_name in loss_names:
        if type_name not in where:
            raise SystemExit(f"{type_name}.{field_name}: no typed root query reaches the type")
        root, path = where[type_name]
        steps = []
        for name, is_list in path:
            steps.append(name)
            if is_list:
                steps.append("0")
        link = {}
        for group in ("complete", "pin_cases"):
            for index, record in enumerate(typed[group]):
                if record["name"].split("/")[0] != root:
                    continue
                pointer = "/".join(["", group, str(index), "response", "data", *steps, field_name])
                value = resolve(typed, pointer)
                if value is None:
                    continue
                key = "pre_port_value_vector" if group == "complete" else "pre_port_pin_fixture_vector"
                link.setdefault(key, {"vector": TYPED_DIRECTORY + "graphql-typed-queries.json" + "#" + pointer, "value": value})
        if "pre_port_value_vector" not in link:
            raise SystemExit(f"{type_name}.{field_name}: the typed GraphQL vector shows no value")
        tool = MCP_TOOL_OF_ROOT[root]
        for index, record in enumerate(mcp["complete"]):
            if record["tool"] != tool or record["name"] != tool:
                continue
            # the MCP tag of a field is its snake-case name, with a unit suffix where the GraphQL name carries none
            for suffix in ("", "_c", "_h"):
                pointer = "/".join(["", "complete", str(index), "envelope", "data", *[snake(step) if step != "0" else step for step in steps[1:]], snake(field_name) + suffix])
                value = resolve(mcp, pointer)
                if value is not None:
                    link["pre_port_mcp_value_vector"] = {"vector": TYPED_DIRECTORY + "mcp-typed-tools.json" + "#" + pointer, "value": value}
                    break
        for index, record in enumerate(mcp["pin_cases"]):
            if record["tool"] != tool:
                continue
            for suffix in ("", "_c", "_h"):
                pointer = "/".join(["", "pin_cases", str(index), "envelope", "data", *[snake(step) if step != "0" else step for step in steps[1:]], snake(field_name) + suffix])
                value = resolve(mcp, pointer)
                if value is not None:
                    link.setdefault("pre_port_mcp_pin_fixture_vector", {"vector": TYPED_DIRECTORY + "mcp-typed-tools.json" + "#" + pointer, "value": value})
                    break
        out[(type_name, field_name)] = link
    return out


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


def record(introspection, typed_queries, mcp_tools, output):
    item = common.entry("current", "gateway")
    source = common.unpack(item)
    current = json.loads((source / "graphql/testdata/query_schema_introspection.golden.json").read_text(encoding="utf-8"))["response"]["__schema"]["types"]
    names = json.loads((source / "graphql/testdata/register_derived_names.json").read_text(encoding="utf-8"))
    renamed = {(row["surfaces"]["graphql"], row["previous_name"]) for row in names["rows"] if row.get("previous_name") and "graphql" in row.get("surfaces", {})}
    previous = json.loads(Path(introspection).read_text(encoding="utf-8"))["data"]["__schema"]["types"]
    before, after = fields(previous), fields(current)
    typed = json.loads(Path(typed_queries).read_text(encoding="utf-8"))
    mcp = json.loads(Path(mcp_tools).read_text(encoding="utf-8"))
    losses = []
    for key in sorted(before):
        type_name, field_name = key.split(".")
        if key in after or (type_name, field_name) in renamed:
            continue
        losses.append({"surface": "graphql", "published_at_pre_port": f"{before[key]['type']}.{before[key]['field']}", "normalized": key, "pre_port_vector": "acceptance/vectors/pre-port/gateway/graphql-schema-introspection.json" + "#" + before[key]["pointer"]})
    links = value_links(previous, typed, mcp, [tuple(loss["published_at_pre_port"].split(".")) for loss in losses])
    for loss in losses:
        loss.update(links[tuple(loss["published_at_pre_port"].split("."))])
    document = {
        "format": "helianthus-oracle-pre-port-losses/1",
        "derived": True,
        "derivation": "pre-port introspection fields, snake-case normalized, not present in the current pin's introspection golden and not a previous_name row of its register_derived_names.json",
        "value_derivation": "pre_port_vector points at the introspection entry of the field; pre_port_value_vector points at the typed GraphQL answer of the complete synthetic fixture that shows a value for it, pre_port_pin_fixture_vector at a GraphQL answer on a fixture the pin's own tests use where one shows a value, pre_port_mcp_value_vector at the semantic MCP tool answer of the complete fixture and pre_port_mcp_pin_fixture_vector at an MCP answer on a fixture the pin's own tests use where one shows a value; the value of a complete-fixture answer is synthetic, except BoilerState.flowTemperatureC, which carries the flow value of the pin's MCP boiler fixture",
        "current_pin": {"repository": item["slug_at_pin"], "commit": item["commit"]},
        "losses": losses,
    }
    common.write(output, common.canonical(document))
    return losses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--introspection", required=True)
    parser.add_argument("--typed-queries", required=True)
    parser.add_argument("--mcp-tools", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(len(record(args.introspection, args.typed_queries, args.mcp_tools, args.output)), "losses")


if __name__ == "__main__":
    main()
