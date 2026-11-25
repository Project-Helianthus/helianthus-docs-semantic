#!/usr/bin/env python3
"""Mutation checks for the energy-management pack validator.

Each rejection names the production comparison it trips:
- field id: the id leaves FIELD_CONTRACTS, so the field set is no longer the PE07 set
- field kind, unit, dimension, qualifiers, symbols, direction: that contract comparison
- bounds.minimum and bounds.maximum: the two sides of check_bounds
- operation id: the id leaves OPERATION_CONTRACTS
- operation capability, arguments, effect_rule, parameters: that contract comparison
- pack id and pack version: the catalog pack comparison
- energy.price.current unit: the unit comparison; unit.kilowatt_hour is rejected
- energy.price.forecast_price unit, dimension, qualifiers, symbols, direction,
  bounds.minimum and bounds.maximum: that contract comparison
- energy.tariff.unit_basis kind, unit, dimension and symbols: that contract comparison
- energy.operation.write_incentive_slot capability, arguments, effect_rule and
  parameters: that contract comparison
"""
from __future__ import annotations

import ast
import copy
import csv
import json
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_energy_management_pack_v1",
    ROOT / "scripts" / "validate_energy_management_pack_v1.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load energy-management validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

BOUNDED = "energy.limit.consumption_failsafe_duration_minimum"
EMPTY = "energy.limit.consumption_duration"
QUALIFIED = "energy.series.slot_power_nominal"
SYMBOL = "energy.limit.state"
OPERATION = "energy.operation.modify_series_slot"


def document():
    return validator.load(validator.VECTORS)


def page():
    return validator.PAGE.read_text(encoding="utf-8")


def field(body, ident):
    for item in body["catalog"]["definitions"]["fields"]:
        if item["id"] == ident:
            return item
    raise AssertionError(ident)


def operation(body):
    for item in body["catalog"]["definitions"]["operations"]:
        if item["id"] == OPERATION:
            return item
    raise AssertionError(OPERATION)


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
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(id="energy.extra.field"), "outside PE07")
    # kind: production kind comparison.
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(kind="text"), f"{BOUNDED} kind")
    # unit: production unit comparison.
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(unit="unit.watt"), f"{BOUNDED} unit")
    # dimension: production dimension comparison.
    expect_reject(body, text, lambda item: field(item, BOUNDED).update(dimension="energy.dimension.slot"), f"{BOUNDED} dimension")
    # qualifiers: production qualifier comparison on a qualified field.
    expect_reject(body, text, lambda item: field(item, QUALIFIED).update(qualifiers=["energy.dimension.slot"]), f"{QUALIFIED} qualifiers")
    # symbols: production symbol comparison.
    expect_reject(body, text, lambda item: field(item, SYMBOL).update(symbols=["energy.limit.state.init"]), f"{SYMBOL} symbols")
    # direction: production direction comparison, including a signed-table field.
    expect_reject(body, text, lambda item: field(item, QUALIFIED).update(direction="signed"), f"{QUALIFIED} direction")
    # bounds.minimum: production minimum comparison. The committed minimum is 7200 s.
    expect_reject(
        body, text,
        lambda item: field(item, BOUNDED)["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}),
        f"{BOUNDED} bounds.minimum",
    )
    # bounds.maximum: production maximum comparison. The committed maximum is 86400 s.
    expect_reject(
        body, text,
        lambda item: field(item, BOUNDED)["bounds"].update(maximum=None),
        f"{BOUNDED} bounds.maximum",
    )


def reject_empty_and_extra(body, text):
    # Filling an empty bound is a minimum mutation. consumption duration has neither side.
    expect_reject(
        body, text,
        lambda item: field(item, EMPTY)["bounds"].update(minimum={"coefficient": "0", "exponent10": 0}),
        f"{EMPTY} bounds.minimum",
    )
    expect_reject(body, text, lambda item: item["catalog"]["definitions"]["fields"].pop(0), "fields missing")

    def mark(item):
        field(item, BOUNDED)["sensitive"] = True

    expect_reject(body, text, mark, "marked sensitive")


def reject_operation_identity(body, text):
    # id: production operation-set comparison.
    expect_reject(body, text, lambda item: operation(item).update(id="energy.operation.extra"), "outside PE07")
    # capability: production capability comparison.
    expect_reject(body, text, lambda item: operation(item).update(capability="energy.capability.read.subject"), f"{OPERATION} capability")
    # arguments: production arguments comparison.
    expect_reject(body, text, lambda item: operation(item).update(arguments=["energy.series.slot_power_maximum"]), f"{OPERATION} arguments")
    # effect_rule: production effect_rule comparison.
    expect_reject(body, text, lambda item: operation(item).update(effect_rule="energy.effect.extra"), f"{OPERATION} effect_rule")
    # parameters: production parameters comparison. Drops one stored parameter.
    expect_reject(body, text, lambda item: operation(item).update(parameters=["energy.esa.request_cause"]), f"{OPERATION} parameters")


def reject_pack_identity(body, text):
    # pack id: production pack comparison.
    expect_reject(body, text, lambda item: item["catalog"]["pack"].update(id="helianthus.pack.other"), "pack id")
    # pack version: production pack comparison.
    expect_reject(body, text, lambda item: item["catalog"]["pack"].update(version="1.1.0"), "pack id")


def positive_contracts(body):
    duration = field(body, EMPTY)
    if duration["bounds"] != {"minimum": None, "maximum": None}:
        raise AssertionError("empty bounds were filled")
    if duration["direction"] != "non_negative":
        raise AssertionError("duration direction")
    signed = field(body, QUALIFIED)
    if signed["direction"] != "not_applicable":
        raise AssertionError("signed table field stored signed")
    if "sensitive" in signed or "hidden" in signed:
        raise AssertionError("field is marked")
    heartbeat = field(body, "energy.heartbeat.timeout")
    if heartbeat["bounds"]["minimum"] is not None:
        raise AssertionError("heartbeat minimum was filled")
    if heartbeat["bounds"]["maximum"] != {"coefficient": "6", "exponent10": 1}:
        raise AssertionError("heartbeat maximum")
    print("committed field contracts: PASS")


def added_operation(body):
    for item in body["catalog"]["definitions"]["operations"]:
        if item["id"] == "energy.operation.write_incentive_slot":
            return item
    raise AssertionError("energy.operation.write_incentive_slot")


def reject_added_identity(body, text):
    price = "energy.price.current"
    forecast = "energy.price.forecast_price"
    basis = "energy.tariff.unit_basis"
    slot = "energy.operation.write_incentive_slot"
    # unit: production unit comparison. A per-kWh registry unit is rejected.
    expect_reject(body, text, lambda item: field(item, price).update(unit="unit.kilowatt_hour"), f"{price} unit")
    # unit: production unit comparison.
    expect_reject(body, text, lambda item: field(item, forecast).update(unit="unit.joule"), f"{forecast} unit")
    # dimension: production dimension comparison.
    expect_reject(body, text, lambda item: field(item, forecast).update(dimension="energy.dimension.subject"), f"{forecast} dimension")
    # qualifiers: production qualifier comparison.
    expect_reject(body, text, lambda item: field(item, forecast).update(qualifiers=["energy.dimension.slot"]), f"{forecast} qualifiers")
    # symbols: production symbol comparison.
    expect_reject(body, text, lambda item: field(item, forecast).update(symbols=["energy.price.forecast_price.other"]), f"{forecast} symbols")
    # direction: production direction comparison. The table says signed; the stored direction is not_applicable.
    expect_reject(body, text, lambda item: field(item, forecast).update(direction="signed"), f"{forecast} direction")
    # bounds.minimum: production minimum comparison.
    expect_reject(
        body, text,
        lambda item: field(item, forecast)["bounds"].update(minimum={"coefficient": "1", "exponent10": 0}),
        f"{forecast} bounds.minimum",
    )
    # bounds.maximum: production maximum comparison.
    expect_reject(
        body, text,
        lambda item: field(item, forecast)["bounds"].update(maximum={"coefficient": "1", "exponent10": 0}),
        f"{forecast} bounds.maximum",
    )
    # kind: production kind comparison.
    expect_reject(body, text, lambda item: field(item, basis).update(kind="text"), f"{basis} kind")
    # unit: production unit comparison.
    expect_reject(body, text, lambda item: field(item, basis).update(unit="unit.one"), f"{basis} unit")
    # dimension: production dimension comparison.
    expect_reject(body, text, lambda item: field(item, basis).update(dimension="energy.dimension.subject"), f"{basis} dimension")
    # symbols: production symbol comparison.
    expect_reject(body, text, lambda item: field(item, basis).update(symbols=["energy.tariff.unit_basis.missing"]), f"{basis} symbols")
    # capability: production capability comparison.
    expect_reject(body, text, lambda item: added_operation(item).update(capability="energy.capability.read.tariff"), f"{slot} capability")
    # arguments: production arguments comparison.
    expect_reject(body, text, lambda item: added_operation(item).update(arguments=["energy.incentive.tier_kind"]), f"{slot} arguments")
    # effect_rule: production effect_rule comparison.
    expect_reject(body, text, lambda item: added_operation(item).update(effect_rule="energy.effect.extra"), f"{slot} effect_rule")
    # parameters: production parameters comparison. Drops every stored parameter but one.
    expect_reject(body, text, lambda item: added_operation(item).update(parameters=["energy.incentive.slot_start"]), f"{slot} parameters")


# Decision points the readability gate counts for C901. Boolean operators are not included.
DECISION_NODES = {"Assert", "AsyncFor", "ExceptHandler", "For", "If", "Match", "While", "With"}


def decision_points(function):
    measured = 1
    for node in ast.walk(function):
        name = type(node).__name__
        if name in DECISION_NODES:
            measured += 1
        elif name == "Try":
            measured += len(node.handlers) + bool(node.orelse) + bool(node.finalbody)
    return measured


def catalog_input_rows(name):
    folder = ROOT / "acceptance" / "catalog-inputs" / "energy"
    with (folder / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def check_added_members_complexity():
    """``added_members`` stays within the readability complexity limit.

    The member comparisons stay in ``added_members``: the field set, stored
    units, signed directions, operation set, qualifier set, catalog membership,
    pack version, and the currency-per-joule price unit.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    function = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "added_members")
    measured = decision_points(function)
    if measured > 10:
        raise AssertionError(f"added_members complexity {measured} exceeds 10")
    print("added_members_complexity: PASS")


def test_added_members_complexity():
    check_added_members_complexity()


def added_members(body):
    pe07 = {row["id"] for row in catalog_input_rows("pe07-fields.tsv")}
    pe12 = catalog_input_rows("pe12-fields.tsv")
    qq = [row for row in catalog_input_rows("qq12-fields.tsv") if row["id"].startswith("energy.")]
    if set(validator.FIELD_CONTRACTS) != pe07 | {row["id"] for row in pe12} | {row["id"] for row in qq}:
        raise AssertionError("field set")
    for row in pe12 + qq:
        contract = validator.FIELD_CONTRACTS[row["id"]]
        expected = row["unit"] or None
        if contract["unit"] != expected:
            raise AssertionError(f"{row['id']} unit rewritten")
        if row["direction"] == "signed" and contract["direction"] != "not_applicable":
            raise AssertionError(f"{row['id']} direction")
    operations = {row["operation"] for row in catalog_input_rows("pe12-operations.tsv")}
    operations |= {row["operation"] for row in catalog_input_rows("qq12-operations.tsv") if row["operation"].startswith("energy.")}
    if set(validator.OPERATION_CONTRACTS) - pe07_operation_ids() != operations:
        raise AssertionError("operation set")
    qualifiers = {row["id"] for row in catalog_input_rows("pe12-qualifier-dimensions.tsv")}
    qualifiers |= {row["id"] for row in catalog_input_rows("qq12-qualifier-dimensions.tsv")}
    if set(validator.QUALIFIER_CONTRACTS) - pe07_qualifier_ids() != qualifiers:
        raise AssertionError("qualifier set")
    catalog = json.loads((ROOT / "api/v1/element-catalog-v1.json").read_text(encoding="utf-8"))
    members = {entry["ref"]["id"] for entry in catalog["elements"]}
    required = qualifiers | {row["id"] for row in pe12} | {row["id"] for row in qq}
    required |= operations
    required |= {row["capability"] for row in catalog_input_rows("pe12-operations.tsv")}
    required |= {row["capability"] for row in catalog_input_rows("qq12-operations.tsv") if row["operation"].startswith("energy.")}
    required |= {row["event"] for row in catalog_input_rows("pe12-events.tsv")}
    required |= {"resource.tariff", "energy.dimension.tariff", "energy.service.tariff", "energy.capability.read.tariff", "energy.portal.read.tariff"}
    if not required <= members or "relation.tariff_applies" in members:
        raise AssertionError("catalog membership")
    if body["catalog"]["pack"]["version"] != "1.0.0":
        raise AssertionError("pack version")
    if field(body, "energy.price.current")["unit"] != "unit.currency_per_joule":
        raise AssertionError("price unit")
    print("added member set: PASS")


def pe07_operation_ids():
    return {
        "energy.operation.set_consumption_limit", "energy.operation.set_production_limit",
        "energy.operation.set_consumption_failsafe", "energy.operation.set_production_failsafe",
        "energy.operation.adjust_power", "energy.operation.set_esa_state",
        "energy.operation.adjust_start_time", "energy.operation.modify_series_slot",
        "energy.operation.set_esa_mode", "energy.operation.schedule_sequence",
        "energy.operation.set_sequence_state", "energy.operation.set_energy_balance",
        "energy.operation.set_low_power_sensitivity",
    }


def pe07_qualifier_ids():
    return {
        "energy.dimension.slot", "energy.dimension.series", "energy.dimension.adjustment_range",
        "energy.dimension.sequence", "energy.dimension.balance",
    }


def main():
    body = document()
    text = page()
    validator.validate(body, text)
    positive_contracts(body)
    reject_field_identity(body, text)
    reject_empty_and_extra(body, text)
    reject_operation_identity(body, text)
    reject_pack_identity(body, text)
    check_added_members_complexity()
    added_members(body)
    reject_added_identity(body, text)
    print("energy management pack tests: PASS")


if __name__ == "__main__":
    main()
