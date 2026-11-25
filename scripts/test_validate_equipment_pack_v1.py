#!/usr/bin/env python3
"""Mutation checks for the equipment pack validator.

Each rejection names the production comparison it trips:
- field id: the id leaves FIELD_CONTRACTS, so the field set is no longer the admitted PE02 set
- field kind, unit, dimension, qualifiers, symbols, direction: that contract comparison
- bounds.minimum and bounds.maximum: the two sides of check_bounds
- empty bounds.minimum: filling a null minimum is the same minimum comparison
- operation id: the id leaves OPERATION_CONTRACTS
- operation capability, arguments, effect_rule, parameters: that contract comparison
- effect fact and operator: that effect comparison
- event id: the id leaves EVENT_CONTRACTS
- event service, trigger, condition, payload, origin: that contract comparison
- qualifier unit: the message qualifier unit comparison
- fact-dimension value_kind: the dimension value_kind comparison
- service fact_key_dimension: that service comparison
- capability service and activation: that capability comparison
- portal fields: the portal field-list comparison
- pack id and pack version: the catalog pack comparison
- sensitive: forbid_marks
- an excluded field id: the field-set comparison against FIELD_CONTRACTS
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_equipment_pack_v1",
    ROOT / "scripts" / "validate_equipment_pack_v1.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load equipment validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

BOUNDED = "equipment.identification.software_version"
EMPTY = "equipment.power.battery_capacity"
QUALIFIED = "equipment.message.text"
SYMBOL = "equipment.power.wired_faults"
OPERATION = "equipment.operation.set_label"
EVENT = "equipment.event.reachable_changed"
PORTAL = "equipment.portal.read.unit"


def document():
    return validator.load(validator.VECTORS)


def page():
    return validator.PAGE.read_text(encoding="utf-8")


def field(body, ident):
    for item in body["catalog"]["definitions"]["fields"]:
        if item["id"] == ident:
            return item
    raise AssertionError(ident)


def by_id(items, ident):
    for item in items:
        if item["id"] == ident:
            return item
    raise AssertionError(ident)


def expect_reject(body, text, mutate, token):
    candidate = copy.deepcopy(body)
    mutate(candidate)
    try:
        validator.validate(candidate, text)
    except ValueError as error:
        if token not in str(error):
            raise AssertionError(f"{token} not in {error}") from error
        print(f"{token}: REJECTED")
        return
    raise AssertionError(f"accepted mutation {token}")


def reject_field_identity(body, text):
    # id: production field-set comparison against FIELD_CONTRACTS.
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(id="equipment.extra.field"), "outside PE02")
    # kind: production kind comparison.
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(kind="text"), f"{BOUNDED} kind")
    # unit: production unit comparison.
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(unit="unit.volt"), f"{BOUNDED} unit")
    # dimension: production dimension comparison.
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(dimension="equipment.dimension.resource"), f"{BOUNDED} dimension")
    # qualifiers: production qualifier comparison. message.text names the message dimension.
    expect_reject(body, text, lambda item: field(item, QUALIFIED).update(qualifiers=[]), f"{QUALIFIED} qualifiers")
    # symbols: production symbol comparison. wired_faults names the fault tokens.
    expect_reject(body, text, lambda item: field(item, SYMBOL).update(symbols=["unspecified"]), f"{SYMBOL} symbols")
    # direction: production direction comparison.
    expect_reject(body, text, lambda item: field(item, EMPTY).update(direction="signed"), f"{EMPTY} direction")
    # bounds.minimum: production minimum comparison. The committed minimum is 0.
    expect_reject(
        body, text,
        lambda item: field(item, BOUNDED)["bounds"].update(minimum={"coefficient": "1", "exponent10": 0}),
        f"{BOUNDED} bounds.minimum",
    )
    # bounds.maximum: production maximum comparison. The committed maximum is 4294967295.
    expect_reject(
        body, text,
        lambda item: field(item, BOUNDED)["bounds"].update(maximum=None),
        f"{BOUNDED} bounds.maximum",
    )


def reject_empty_and_extra(body, text):
    # Filling an empty bound is a minimum mutation. Battery capacity has neither side.
    expect_reject(
        body, text,
        lambda item: field(item, EMPTY)["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}),
        f"{EMPTY} bounds.minimum",
    )
    expect_reject(body, text, lambda item: item["catalog"]["definitions"]["fields"].pop(0), "fields missing")

    def mark(item):
        field(item, BOUNDED)["sensitive"] = True

    expect_reject(body, text, mark, "marked sensitive")
    expect_reject(
        body, text,
        lambda item: item["catalog"]["definitions"]["fields"].append({"id": validator.EXCLUDED_FIELDS[0]}),
        "outside PE02",
    )


def reject_operation_identity(body, text):
    def operation(item):
        return by_id(item["catalog"]["definitions"]["operations"], OPERATION)

    # id: production operation-set comparison.
    expect_reject(body, text, lambda item: operation(item).update(id="equipment.operation.extra"), "outside PE02")
    # capability: production capability comparison.
    expect_reject(body, text, lambda item: operation(item).update(capability=validator.READ_RESOURCE), f"{OPERATION} capability")
    # arguments: production arguments comparison.
    expect_reject(body, text, lambda item: operation(item).update(arguments=["equipment.label.description"]), f"{OPERATION} arguments")
    # effect_rule: production effect_rule comparison.
    expect_reject(body, text, lambda item: operation(item).update(effect_rule="equipment.effect.extra"), f"{OPERATION} effect_rule")
    # parameters: production parameters comparison. Drops the stored parameter.
    expect_reject(body, text, lambda item: operation(item).update(parameters=[]), f"{OPERATION} parameters")


def reject_effect_and_event(body, text):
    effect = "equipment.effect.set_label"
    # fact: production effect fact comparison. The fact is the operation argument.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["effect_rules"], effect).update(fact="equipment.label.description"),
        f"{effect} fact",
    )
    # operator: production operator comparison.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["effect_rules"], effect).update(operator="set"),
        f"{effect} operator",
    )
    def event(item):
        return by_id(item["catalog"]["definitions"]["events"], EVENT)

    # id: production event-set comparison.
    expect_reject(body, text, lambda item: event(item).update(id="equipment.event.extra"), "outside PE02")
    # service: production service comparison.
    expect_reject(body, text, lambda item: event(item).update(service=validator.SERVICE_RESOURCE), f"{EVENT} service")
    # trigger: production trigger comparison.
    expect_reject(body, text, lambda item: event(item).update(trigger="equipment.label.name"), f"{EVENT} trigger")
    # condition: production condition comparison.
    expect_reject(body, text, lambda item: event(item).update(condition="entered"), f"{EVENT} condition")
    # payload: production payload comparison. The committed payload is the trigger fact.
    expect_reject(body, text, lambda item: event(item).update(payload=[]), f"{EVENT} payload")
    # origin: production origin comparison.
    expect_reject(body, text, lambda item: event(item).update(origin="derived"), f"{EVENT} origin")


def reject_pack_and_groups(body, text):
    # pack id: production pack comparison.
    expect_reject(body, text, lambda item: item["catalog"]["pack"].update(id="helianthus.pack.other"), "pack id")
    # pack version: production pack comparison.
    expect_reject(body, text, lambda item: item["catalog"]["pack"].update(version="1.1.0"), "pack id")
    # value_kind: production qualifier unit comparison. The table names quantity and no other unit.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["qualifier_dimensions"], validator.MESSAGE).update(unit="unit.second"),
        f"{validator.MESSAGE} unit",
    )
    # value_kind: production fact-dimension value_kind comparison.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["fact_dimensions"], validator.UNIT).update(value_kind="quantity"),
        f"{validator.UNIT} value_kind",
    )
    # fact_key_dimension: production service comparison.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["services"], validator.SERVICE_UNIT).update(fact_key_dimension=validator.RESOURCE),
        f"{validator.SERVICE_UNIT} fact_key_dimension",
    )
    # service: production capability comparison.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["capabilities"], validator.READ_UNIT).update(service=validator.SERVICE_RESOURCE),
        f"{validator.READ_UNIT} service",
    )
    # activation: production activation comparison.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["capabilities"], validator.READ_UNIT).update(activation="other"),
        f"{validator.READ_UNIT} activation",
    )
    # fields: production portal field-list comparison.
    expect_reject(
        body, text,
        lambda item: by_id(item["catalog"]["definitions"]["portal_contributions"], PORTAL).update(fields=["equipment.label.name"]),
        f"{PORTAL} fields",
    )


def positive_contracts(body):
    capacity = field(body, EMPTY)
    if capacity["bounds"] != {"minimum": None, "maximum": None}:
        raise AssertionError("empty bounds were filled")
    if capacity["unit"] != "unit.ampere_hour":
        raise AssertionError("battery capacity unit")
    if capacity["direction"] != "non_negative":
        raise AssertionError("battery capacity direction")
    version = field(body, BOUNDED)
    if version["bounds"]["minimum"] != {"coefficient": "0", "exponent10": 0}:
        raise AssertionError("software_version minimum")
    if version["bounds"]["maximum"] != {"coefficient": "4294967295", "exponent10": 0}:
        raise AssertionError("software_version maximum")
    if "sensitive" in version or "hidden" in version:
        raise AssertionError("field is marked")
    print("committed field contracts: PASS")


def positive_absent(body):
    encoded = json.dumps(body)
    for ident in validator.ABSENT_IDS:
        if f'"{ident}"' in encoded:
            raise AssertionError(ident)
    print("absent ids: PASS")


def equipment_entries():
    catalog = json.loads((ROOT / "api/v1/element-catalog-v1.json").read_text(encoding="utf-8"))
    return {
        entry["ref"]["id"]: entry
        for entry in catalog["elements"]
        if entry["ref"]["owner"]["kind"] == "pack"
        and entry["ref"]["owner"]["pack"]["id"] == "helianthus.pack.equipment"
    }


def check_catalog_identity():
    entries = equipment_entries()
    if set(entries) != set(validator.ADMISSION):
        raise AssertionError("catalog membership")
    for ident, entry in entries.items():
        if entry["planes"] != validator.PLANES[ident]:
            raise AssertionError(f"{ident} planes")
        if entry["admission"]["arm"] != validator.ADMISSION[ident]:
            raise AssertionError(f"{ident} admission")
    print("catalog identity: PASS")


def check_catalog_facts():
    entries = equipment_entries()
    for ident, contract in validator.FIELD_CONTRACTS.items():
        attributes = entries[ident]["attributes"]
        if attributes["direction"] != contract["direction"]:
            raise AssertionError(f"{ident} direction")
        if attributes["value_kind"] != contract["kind"]:
            raise AssertionError(f"{ident} kind")
        if contract["kind"] in {"symbol", "symbols"} and attributes.get("symbols") != list(contract["symbols"]):
            raise AssertionError(f"{ident} symbols")
        if contract["kind"] not in {"symbol", "symbols"} and "symbols" in attributes:
            raise AssertionError(f"{ident} symbols")
    print("catalog facts: PASS")


def check_catalog_shapes():
    entries = equipment_entries()
    unit = entries[validator.UNIT]["attributes"]
    if unit.get("anchor_classes") != ["component", "equipment"] or "resource_kind" in unit:
        raise AssertionError("unit anchors")
    resource = entries[validator.RESOURCE]["attributes"]
    if resource.get("anchor_classes") != ["component", "episode", "equipment", "function"]:
        raise AssertionError("resource anchors")
    service = entries[validator.SERVICE_UNIT]["attributes"]
    if service.get("subject_classes") != ["component", "equipment"] or "subject_kind" in service:
        raise AssertionError("unit service classes")
    message = entries[validator.MESSAGE]["attributes"]
    if message.get("unit") != "unit.one" or message.get("value_kind") != "quantity" or "symbols" in message:
        raise AssertionError("message qualifier")
    operation = entries[OPERATION]["attributes"]
    if [item["id"] for item in operation.get("parameters", [])] != ["equipment.label.description"]:
        raise AssertionError("set_label parameters")
    event = entries[EVENT]["attributes"]
    if event.get("payload", [{}])[0].get("id") != "equipment.status.reachable" or "symbols" in event:
        raise AssertionError("reachable payload")
    portal = entries[PORTAL]
    if portal["disposition"] != "unsupported" or portal["planes"] != []:
        raise AssertionError("portal disposition")
    print("catalog shapes: PASS")


def main():
    body = document()
    text = page()
    validator.validate(body, text)
    positive_contracts(body)
    positive_absent(body)
    reject_field_identity(body, text)
    reject_empty_and_extra(body, text)
    reject_operation_identity(body, text)
    reject_effect_and_event(body, text)
    reject_pack_and_groups(body, text)
    check_catalog_identity()
    check_catalog_facts()
    check_catalog_shapes()
    print("equipment pack tests: PASS")


if __name__ == "__main__":
    main()
