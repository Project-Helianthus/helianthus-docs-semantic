#!/usr/bin/env python3
"""Validate helianthus.pack.equipment 1.0.0 against the admitted PE02 rows.

QQ13 events and operations stay out of the vectors. Their trigger, condition,
capability, argument and effect cells are empty. The three QQ13 fields with an
empty admission are not given an arm. Two-vendor-only PE02 rows stay out.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/packs/equipment-acceptance-vectors.json"
PAGE = ROOT / "api/v1/packs/equipment-v1.md"
TABLES = ROOT / "acceptance/catalog-inputs/equipment"
PACK = {"id": "helianthus.pack.equipment", "version": "1.0.0"}
ADMITTED_ARMS = frozenset({"matter_baseline", "eebus"})
CLASS_PLANES = ["energy", "control", "diagnostic"]
GROUPS = (
    "fields", "fact_dimensions", "qualifier_dimensions", "services", "capabilities",
    "operations", "effect_rules", "portal_contributions", "events",
)
TOKEN = re.compile(r"(?<![A-Za-z0-9_])(?:%s)(?![A-Za-z0-9_])")
EXCLUDED_FIELDS = (
    "equipment.diagnosis.error_history_code",
    "equipment.diagnosis.error_history_time",
)
EXCLUDED_QUALIFIER = "equipment.dimension.history_index"
EMPTY_ADMISSION_FIELDS = (
    "equipment.diagnosis.link_state",
    "equipment.diagnosis.degraded_reason",
    "equipment.diagnosis.controller_capability",
)
MESSAGE = "equipment.dimension.message"
UNIT = "equipment.dimension.unit"
RESOURCE = "equipment.dimension.resource"
SERVICE_UNIT = "equipment.service.unit"
SERVICE_RESOURCE = "equipment.service.resource"
READ_UNIT = "equipment.capability.read.unit"
READ_RESOURCE = "equipment.capability.read.resource"
PORTAL_UNIT = "equipment.portal.read.unit"
PORTAL_RESOURCE = "equipment.portal.read.resource"
SET_LABEL = "equipment.operation.set_label"
ENERGY_FACTS = frozenset({
    "equipment.power.wired_input_voltage",
    "equipment.power.wired_input_frequency",
    "equipment.power.wired_current_type",
    "equipment.power.wired_current",
    "equipment.power.wired_nominal_voltage",
    "equipment.power.wired_maximum_current",
    "equipment.power.battery_voltage",
    "equipment.power.battery_charge_ratio",
    "equipment.power.battery_time_remaining",
    "equipment.power.battery_capacity",
    "equipment.power.battery_time_to_full",
    "equipment.power.battery_charging_current",
})
DIAGNOSTIC_FACTS = frozenset({
    "equipment.status.reachable",
    "equipment.diagnosis.operating_state",
    "equipment.diagnosis.vendor_state_code",
    "equipment.diagnosis.last_error_code",
    "equipment.diagnosis.operating_time",
    "equipment.power.source_status",
    "equipment.power.source_order",
    "equipment.power.source_description",
    "equipment.power.wired_present",
    "equipment.power.wired_faults",
    "equipment.power.battery_charge_level",
    "equipment.power.battery_replacement_needed",
    "equipment.power.battery_replaceability",
    "equipment.power.battery_present",
    "equipment.power.battery_faults",
    "equipment.power.battery_charge_state",
    "equipment.power.battery_functional_while_charging",
    "equipment.power.battery_charge_faults",
    "equipment.message.text",
    "equipment.message.kind",
    "equipment.message.time",
})
PROVENANCE_TEXTS = frozenset({
    "equipment.power.battery_replacement_description",
    "equipment.power.battery_common_designation",
    "equipment.power.battery_ansi_designation",
    "equipment.power.battery_iec_designation",
    "equipment.power.battery_chemistry",
    "equipment.power.battery_quantity",
})


def require(condition, label):
    if not condition:
        raise ValueError(label)


def table(name):
    with (TABLES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def comma_list(cell):
    return tuple(part.strip() for part in cell.split(",") if part.strip())


def stated_bound(cell):
    if cell == "":
        return None
    return {"coefficient": cell, "exponent10": 0}


def stored_direction(kind, cell):
    if kind != "quantity" or cell == "":
        return "not_applicable"
    require(cell in {"non_negative", "not_applicable"}, f"direction {cell}")
    return cell


def field_contract(row):
    kind = row["value_kind"]
    quantity = kind == "quantity"
    unit = row["unit"] or None
    if quantity:
        require(unit is not None, f"{row['id']} unit")
    return {
        "kind": kind,
        "unit": unit if quantity else None,
        "dimension": row["subject_dimension"],
        "qualifiers": comma_list(row["qualifiers"]),
        "symbols": comma_list(row["symbols"]),
        "bounds": None if not quantity else {
            "minimum": stated_bound(row["minimum"]),
            "maximum": stated_bound(row["maximum"]),
        },
        "direction": stored_direction(kind, row["direction"]),
        "admission": row["admission"],
    }


def load_fields():
    contracts = {}
    excluded = []
    for row in table("pe02-fields.tsv"):
        if row["admission"] in ADMITTED_ARMS:
            contracts[row["id"]] = field_contract(row)
        else:
            excluded.append(row["id"])
    require(tuple(excluded) == EXCLUDED_FIELDS, "PE02 excluded fields")
    return contracts


def load_empty_admission():
    found = tuple(row["id"] for row in table("qq13-fields.tsv"))
    require(found == EMPTY_ADMISSION_FIELDS, "QQ13 empty-admission fields")
    require(all(row["admission"] == "" for row in table("qq13-fields.tsv")), "QQ13 admission")
    return found


def anchor_classes(cell):
    prefix = "anchor classes "
    require(cell.startswith(prefix), "anchor classes")
    return tuple(sorted(comma_list(cell[len(prefix):])))


def load_dimensions():
    found = {}
    for row in table("pe02-resource-dimensions.tsv"):
        require(row["admission"] in ADMITTED_ARMS, row["id"])
        found[row["id"]] = {"anchors": anchor_classes(row["attributes"]), "admission": row["admission"]}
    require(set(found) == {UNIT, RESOURCE}, "fact dimensions")
    require(found[UNIT]["anchors"] == ("component", "equipment"), "unit anchors")
    require(found[RESOURCE]["anchors"] == ("component", "episode", "equipment", "function"), "resource anchors")
    return found


def load_qualifier():
    rows = table("pe02-qualifier-dimensions.tsv")
    excluded = tuple(row["id"] for row in rows if row["admission"] not in ADMITTED_ARMS)
    require(excluded == (EXCLUDED_QUALIFIER,), "excluded qualifier")
    admitted = [row for row in rows if row["admission"] in ADMITTED_ARMS]
    require(len(admitted) == 1 and admitted[0]["id"] == MESSAGE, "message qualifier")
    require(admitted[0]["attributes"] == "value kind quantity", "message value kind")
    return {MESSAGE: {"value_kind": "quantity", "unit": "unit.one", "symbols": (), "admission": admitted[0]["admission"]}}


def fact_key(cell):
    prefix = "fact-key dimension "
    require(cell.startswith(prefix), "fact-key dimension")
    return cell[len(prefix):]


def load_services():
    services = {}
    lists = {}
    for row in table("pe02-services.tsv"):
        require(row["admission"] in ADMITTED_ARMS, row["id"])
        if row["id"].startswith("equipment.service."):
            services[row["id"]] = {"fact_key_dimension": fact_key(row["attributes"]), "admission": row["admission"]}
        else:
            lists[row["id"]] = {"fields": comma_list(row["attributes"]), "admission": row["admission"]}
    require(set(services) == {SERVICE_UNIT, SERVICE_RESOURCE}, "services")
    require(services[SERVICE_UNIT]["fact_key_dimension"] == UNIT, "unit service")
    require(services[SERVICE_RESOURCE]["fact_key_dimension"] == RESOURCE, "resource service")
    return services, lists


def load_operation():
    rows = [row for row in table("pe02-operations.tsv") if row["admission"] in ADMITTED_ARMS]
    require(len(rows) == 1 and rows[0]["operation"] == SET_LABEL, "set_label")
    row = rows[0]
    return {
        SET_LABEL: {
            "capability": row["capability"],
            "arguments": (row["argument"],),
            "parameters": comma_list(row["parameters"]),
            "effect_rule": row["effect_rule"],
            "service": row["service"],
            "admission": row["admission"],
        }
    }


def load_events():
    contracts = {}
    for row in table("pe02-events.tsv"):
        require(row["admission"] in ADMITTED_ARMS, row["event"])
        require(row["trigger_fact"] and row["condition"] and row["payload"], row["event"])
        contracts[row["event"]] = {
            "service": row["service"],
            "trigger": row["trigger_fact"],
            "condition": row["condition"],
            "payload": comma_list(row["payload"]),
            "origin": row["origin"],
            "admission": row["admission"],
        }
    return contracts


def absent_events():
    found = []
    for row in table("qq13-events.tsv"):
        require(row["trigger_fact"] == "" or row["condition"] == "", row["event"])
        found.append(row["event"])
    return tuple(found)


def absent_operations():
    found = []
    for row in table("qq13-operations.tsv"):
        complete = row["capability"] and row["effect_rule"] and row["argument"]
        require(not complete, row["operation"])
        found.append(row["operation"])
    return tuple(found)


def provenance_fact(ident):
    return (
        ident.startswith("equipment.identification.")
        or ident.startswith("equipment.label.")
        or ident.startswith("equipment.time.")
        or ident in PROVENANCE_TEXTS
    )


def fact_planes(ident):
    if ident in ENERGY_FACTS:
        return ["energy"]
    if ident in DIAGNOSTIC_FACTS:
        return ["diagnostic"]
    require(provenance_fact(ident), f"{ident} plane")
    return ["provenance"]


def union_planes(idents):
    present = {plane for ident in idents for plane in fact_planes(ident)}
    return [plane for plane in ("energy", "diagnostic", "provenance") if plane in present]


def plane_map(fields, events):
    planes = {ident: fact_planes(ident) for ident in fields}
    for ident in (UNIT, RESOURCE, SERVICE_UNIT, SERVICE_RESOURCE):
        planes[ident] = list(CLASS_PLANES)
    planes[MESSAGE] = ["diagnostic"]
    unit_fields = [ident for ident, contract in fields.items() if contract["dimension"] == UNIT]
    planes[READ_UNIT] = union_planes(unit_fields)
    planes[READ_RESOURCE] = ["provenance"]
    planes["equipment.capability.set_label"] = ["control"]
    planes[SET_LABEL] = ["control"]
    planes["equipment.effect.set_label"] = ["control"]
    planes[PORTAL_UNIT] = []
    planes[PORTAL_RESOURCE] = []
    for ident, contract in events.items():
        planes[ident] = list(fact_planes(contract["trigger"]))
    require(planes[READ_UNIT] == ["energy", "diagnostic", "provenance"], "read.unit planes")
    return planes


def admission_map(fields, dimensions, qualifier, services, lists, operation, events):
    found = {ident: contract["admission"] for ident, contract in fields.items()}
    found.update({ident: item["admission"] for ident, item in dimensions.items()})
    found.update({ident: item["admission"] for ident, item in qualifier.items()})
    found.update({ident: item["admission"] for ident, item in services.items()})
    found.update({ident: item["admission"] for ident, item in lists.items()})
    for ident, contract in operation.items():
        found[ident] = contract["admission"]
        found[contract["capability"]] = contract["admission"]
        found[contract["effect_rule"]] = contract["admission"]
    found.update({ident: contract["admission"] for ident, contract in events.items()})
    return found


def portal_fields(fields, dimension):
    return sorted(ident for ident, contract in fields.items() if contract["dimension"] == dimension)


def check_published_lists(fields, lists):
    expected = {
        READ_UNIT: portal_fields(fields, UNIT),
        PORTAL_UNIT: portal_fields(fields, UNIT),
        READ_RESOURCE: portal_fields(fields, RESOURCE),
        PORTAL_RESOURCE: portal_fields(fields, RESOURCE),
    }
    require(set(lists) == set(expected), "service field lists")
    for ident, wanted in expected.items():
        published = tuple(item for item in lists[ident]["fields"] if item not in EXCLUDED_FIELDS)
        require(sorted(published) == wanted, f"{ident} fields")


FIELD_CONTRACTS = load_fields()
EMPTY_ADMISSION = load_empty_admission()
FACT_DIMENSIONS = load_dimensions()
QUALIFIER_CONTRACTS = load_qualifier()
SERVICES, SERVICE_LISTS = load_services()
OPERATION_CONTRACTS = load_operation()
EVENT_CONTRACTS = load_events()
ABSENT_EVENTS = absent_events()
ABSENT_OPERATIONS = absent_operations()
PLANES = plane_map(FIELD_CONTRACTS, EVENT_CONTRACTS)
ADMISSION = admission_map(
    FIELD_CONTRACTS, FACT_DIMENSIONS, QUALIFIER_CONTRACTS, SERVICES, SERVICE_LISTS,
    OPERATION_CONTRACTS, EVENT_CONTRACTS,
)
UNIT_PORTAL_FIELDS = portal_fields(FIELD_CONTRACTS, UNIT)
RESOURCE_PORTAL_FIELDS = portal_fields(FIELD_CONTRACTS, RESOURCE)
check_published_lists(FIELD_CONTRACTS, SERVICE_LISTS)
ABSENT_IDS = EXCLUDED_FIELDS + (EXCLUDED_QUALIFIER,) + EMPTY_ADMISSION + ABSENT_EVENTS + ABSENT_OPERATIONS
PAGE_IDS = tuple(sorted(set(ADMISSION) | set(ABSENT_IDS)))
require(set(ENERGY_FACTS).isdisjoint(DIAGNOSTIC_FACTS), "plane overlap")
require(ENERGY_FACTS | DIAGNOSTIC_FACTS <= set(FIELD_CONTRACTS), "plane facts")
require(all(provenance_fact(ident) for ident in set(FIELD_CONTRACTS) - ENERGY_FACTS - DIAGNOSTIC_FACTS), "provenance")


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    with path.open(encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=pairs)


def ref_of(ident):
    return {"pack": PACK, "id": ident, "version": "1.0.0"}


def forbid_marks(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(key not in {"sensitive", "hidden"}, f"marked {key}")
            forbid_marks(item)
    elif isinstance(value, list):
        for item in value:
            forbid_marks(item)


def check_orders(items, label):
    orders = [item.get("order") for item in items]
    require(all(isinstance(order, int) and order > 0 for order in orders), f"{label} order")
    require(orders == sorted(orders) and len(set(orders)) == len(orders), f"{label} order")


def check_refs(items, label):
    for item in items:
        require(item.get("ref") == ref_of(item["id"]), f"{label} {item['id']} ref")


def check_bounds(ident, item, expected):
    actual = item.get("bounds")
    if expected is None:
        require(actual is None, f"{ident} bounds")
        return
    require(isinstance(actual, dict), f"{ident} bounds")
    require(set(actual) == {"minimum", "maximum"}, f"{ident} bounds")
    require(actual.get("minimum") == expected["minimum"], f"{ident} bounds.minimum")
    require(actual.get("maximum") == expected["maximum"], f"{ident} bounds.maximum")


def check_field(item):
    ident = item["id"]
    contract = FIELD_CONTRACTS[ident]
    require(item.get("kind") == contract["kind"], f"{ident} kind")
    require(item.get("unit") == contract["unit"], f"{ident} unit")
    require(item.get("dimension") == contract["dimension"], f"{ident} dimension")
    require(tuple(item.get("qualifiers", ())) == contract["qualifiers"], f"{ident} qualifiers")
    require(tuple(item.get("symbols", ())) == contract["symbols"], f"{ident} symbols")
    require(item.get("direction") == contract["direction"], f"{ident} direction")
    require(item.get("optional") is True, f"{ident} optional")
    check_bounds(ident, item, contract["bounds"])


def member_set(items, expected, label):
    found = [item["id"] for item in items]
    unknown = sorted(set(found) - set(expected))
    missing = sorted(set(expected) - set(found))
    require(not unknown, f"{label} outside PE02: {unknown}")
    require(not missing, f"{label} missing: {missing}")
    require(len(found) == len(set(found)), f"duplicate {label}")


def check_fields(items):
    require(isinstance(items, list), "fields")
    member_set(items, FIELD_CONTRACTS, "fields")
    check_orders(items, "fields")
    check_refs(items, "field")
    for item in items:
        check_field(item)


def check_subject(items):
    found = {item["id"]: item for item in items}
    require(set(found) == set(FACT_DIMENSIONS), "fact dimensions")
    for ident, item in found.items():
        require(item.get("value_kind") == "text", f"{ident} value_kind")
    check_refs(items, "fact dimension")
    check_orders(items, "fact dimensions")


def check_qualifiers(items):
    found = {item["id"]: item for item in items}
    require(set(found) == set(QUALIFIER_CONTRACTS), "qualifier dimensions")
    check_orders(items, "qualifier dimensions")
    check_refs(items, "qualifier")
    for ident, item in found.items():
        contract = QUALIFIER_CONTRACTS[ident]
        require(item.get("value_kind") == contract["value_kind"], f"{ident} value_kind")
        require(item.get("unit") == contract["unit"], f"{ident} unit")
        require(tuple(item.get("symbols", ())) == contract["symbols"], f"{ident} symbols")


def check_service(items):
    found = {item["id"]: item for item in items}
    require(set(found) == set(SERVICES), "service")
    for ident, item in found.items():
        require(item.get("fact_key_dimension") == SERVICES[ident]["fact_key_dimension"], f"{ident} fact_key_dimension")
    check_refs(items, "service")
    check_orders(items, "services")


def check_capabilities(items):
    expected = {READ_UNIT: SERVICE_UNIT, READ_RESOURCE: SERVICE_RESOURCE}
    for contract in OPERATION_CONTRACTS.values():
        expected[contract["capability"]] = contract["service"]
    found = [item["id"] for item in items]
    require(set(found) == set(expected), "capabilities")
    check_orders(items, "capabilities")
    check_refs(items, "capability")
    for item in items:
        require(item.get("service") == expected[item["id"]], f"{item['id']} service")
        require(item.get("activation") == "qualified_current_binding", f"{item['id']} activation")
        require("operation" not in item, f"{item['id']} operation")


def check_operation(item):
    ident = item["id"]
    contract = OPERATION_CONTRACTS[ident]
    require(item.get("capability") == contract["capability"], f"{ident} capability")
    require(tuple(item.get("arguments", ())) == contract["arguments"], f"{ident} arguments")
    require(tuple(item.get("parameters", ())) == contract["parameters"], f"{ident} parameters")
    require(item.get("effect_rule") == contract["effect_rule"], f"{ident} effect_rule")
    require("preconditions" not in item, f"{ident} preconditions")


def check_operations(items):
    member_set(items, OPERATION_CONTRACTS, "operations")
    check_orders(items, "operations")
    check_refs(items, "operation")
    for item in items:
        check_operation(item)


def check_effects(items, operations):
    expected = {item["effect_rule"]: item for item in operations}
    found = [item["id"] for item in items]
    require(set(found) == set(expected), "effect rules")
    check_orders(items, "effect rules")
    check_refs(items, "effect")
    for item in items:
        contract = expected[item["id"]]
        require(item.get("operation") == contract["id"], f"{item['id']} operation")
        require(item.get("fact") == contract["arguments"][0], f"{item['id']} fact")
        require(item.get("operator") == "equal", f"{item['id']} operator")


def check_portal(items):
    found = {item["id"]: item for item in items}
    expected = {PORTAL_UNIT: (SERVICE_UNIT, UNIT_PORTAL_FIELDS), PORTAL_RESOURCE: (SERVICE_RESOURCE, RESOURCE_PORTAL_FIELDS)}
    require(set(found) == set(expected), "portal")
    check_refs(items, "portal")
    check_orders(items, "portals")
    for ident, (service, fields) in expected.items():
        item = found[ident]
        require(item.get("kind") == "read", f"{ident} kind")
        require(item.get("service") == service, f"{ident} service")
        require(item.get("fields") == fields, f"{ident} fields")


def check_events(items):
    member_set(items, EVENT_CONTRACTS, "events")
    check_orders(items, "events")
    check_refs(items, "event")
    for item in items:
        ident = item["id"]
        contract = EVENT_CONTRACTS[ident]
        require(item.get("service") == contract["service"], f"{ident} service")
        require(item.get("trigger") == contract["trigger"], f"{ident} trigger")
        require(item.get("condition") == contract["condition"], f"{ident} condition")
        require(tuple(item.get("payload", ())) == contract["payload"], f"{ident} payload")
        require(item.get("origin") == contract["origin"], f"{ident} origin")
        require("symbols" not in item, f"{ident} symbols")


def nested_ids(document):
    found = []
    for group in GROUPS:
        for item in document["catalog"]["definitions"][group]:
            found.append(item["id"])
            for key in ("fields", "arguments", "parameters", "qualifiers", "payload", "symbols"):
                for value in item.get(key, ()):
                    if isinstance(value, str):
                        found.append(value)
    return found


def check_absent(document):
    present = set(nested_ids(document))
    leaked = sorted(set(ABSENT_IDS) & present)
    require(not leaked, f"absent ids published: {leaked}")


def check_page(text):
    for ident in PAGE_IDS:
        require(TOKEN.pattern and re.search(TOKEN.pattern % re.escape(ident), text), f"document misses {ident}")


def check_pack(document):
    catalog = document["catalog"]
    require(document.get("contract") == "helianthus.semantic.pack.equipment.acceptance/v1", "contract")
    require(document.get("pack_contract") == "helianthus.pack.equipment/v1", "pack contract")
    require(catalog.get("pack") == PACK, "pack id")
    definitions = catalog["definitions"]
    require(set(definitions) == set(GROUPS), f"definition groups {sorted(set(definitions) - set(GROUPS))}")


def validate(document, page):
    forbid_marks(document)
    check_pack(document)
    definitions = document["catalog"]["definitions"]
    check_fields(definitions["fields"])
    check_subject(definitions["fact_dimensions"])
    check_qualifiers(definitions["qualifier_dimensions"])
    check_service(definitions["services"])
    check_capabilities(definitions["capabilities"])
    check_operations(definitions["operations"])
    check_effects(definitions["effect_rules"], definitions["operations"])
    check_portal(definitions["portal_contributions"])
    check_events(definitions["events"])
    check_absent(document)
    check_page(page)


def main():
    validate(load(VECTORS), PAGE.read_text(encoding="utf-8"))
    print(f"equipment pack v1: PASS ({len(FIELD_CONTRACTS)} fields)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
