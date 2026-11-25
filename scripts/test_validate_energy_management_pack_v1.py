#!/usr/bin/env python3
"""Mutation checks for the energy-management pack validator.

Each rejection names the production comparison it trips:
- field id: the id leaves FIELD_CONTRACTS, so the field set is no longer the PE07 set
- field kind, unit, dimension, qualifiers, symbols, direction: that contract comparison
- bounds.minimum and bounds.maximum: the two sides of check_bounds
- operation id: the id leaves OPERATION_CONTRACTS
- operation capability, arguments, effect_rule, parameters: that contract comparison
- pack id and pack version: the catalog pack comparison
"""
from __future__ import annotations

import copy
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


def main():
    body = document()
    text = page()
    validator.validate(body, text)
    positive_contracts(body)
    reject_field_identity(body, text)
    reject_empty_and_extra(body, text)
    reject_operation_identity(body, text)
    reject_pack_identity(body, text)
    print("energy management pack tests: PASS")


if __name__ == "__main__":
    main()
