#!/usr/bin/env python3
"""Execute the exact Growatt BMS RS-485 v2.02 storage mapping gate."""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "api/v1/mappings/growatt-bms-rs485-v202-storage-v1.json"
DOC = ROOT / "api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md"
PACK = {"id": "helianthus.pack.storage", "version": "1.1.0"}
REVISION = {"family": "1xSxxP ESS", "file_revision": "Rev2.01", "header_version": "V2.0", "cumulative_revision": "2.02"}
SLICES = [
    {"function": "FC03", "offset": "0x0001", "quantity": 7},
    {"function": "FC03", "offset": "0x000D", "quantity": 29},
    {"function": "FC03", "offset": "0x0100", "quantity": 12},
    {"function": "FC03", "offset": "0x010D", "quantity": 2},
]
PINS = {
    "docs_semantic_base": "ed33276cddb2dd86757efcf335c95936bdf4efe2",
    "semreg": "f3f761bc67e10d6a65eba6c13cb4dc51002d6955",
    "storage_docs": "c20fdef000fe95df95fca60c55d651a0614c4efd",
    "storage_runtime": "6556bf4b3fffd645b6c14ebfd194d8570b7c5207",
    "docs_modbus_lifecycle": "35151979c8561d5dc4215030899277aec36d2f9f",
    "modbusreg": "7853d903970a4fdded35abaef01fe30f7e93be6a",
    "native_source": "6c08d4d2acf70bea622da333f6d75e26d2d92621",
    "gateway_main": "32244901c4c8337266cd348bdad90fb9e8eb0a61",
    "gateway_tree": "0a850d5646d46f5782b1396d72a3d93bffa6974e",
    "gateway_reviewed_source": "15ab7f0f4197485c83c04f8fe24000ebe058cb7a",
}
LOSS_KINDS = {"unit", "range", "precision", "time", "symbol", "provenance", "identity", "capability", "operation", "policy"}
ERROR_PRECEDENCE = ["native_evidence_missing", "revision_or_unit_or_slice_invalid", "identity_missing_or_invalid", "lifecycle_missing", "mapping_unqualified", "unsupported_or_withheld"]
OPAQUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")
UNSUPPORTED = ["pack_power", "state_of_health", "cell_temperature_meaning", "cell_voltage_extrema", "pack_module_cell_string_topology", "repeated_pack_identity", "warning_error_company_status", "extension_words", "calibration_control_adjacent_fields", "writable_ranges", "charge_discharge_limits", "interlock", "authority", "write_operations", "acknowledgement", "readback", "retry", "control_routes"]


def load():
    return json.loads(PATH.read_text())


def fail(code):
    raise ValueError(code)


def mutate(value, mutation):
    path = mutation["path"]
    aliases = {
        "native.request_adu": "observation.slices.0.request_adu_hex",
        "native.words": "observation.slices.0.words",
        "native.revision": "observation.revision",
        "native.unit_id": "observation.slices.0.unit_id",
        "native.slices": "observation.slices",
        "native.typed": "observation.typed",
    }
    for old, new in aliases.items():
        if path == old or path.startswith(old + "."):
            path = new + path[len(old):]
            break
    if "source" in value and (path == "identity.source_id" or path.startswith("identity.source_id.")):
        path = "source.source_id" + path[len("identity.source_id"):]
    cursor = value
    parts = path.split(".")
    for part in parts[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    last = parts[-1]
    cursor[int(last) if isinstance(cursor, list) else last] = mutation["value"]


def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def decode_adu(text):
    if not isinstance(text, str) or len(text) % 2:
        return None
    try:
        return bytes.fromhex(text)
    except ValueError:
        return None


def valid_request_adu(raw, unit, offset, quantity):
    return raw is not None and len(raw) == 8 and raw[0] == unit and raw[1] == 3 and int.from_bytes(raw[2:4], "big") == offset and int.from_bytes(raw[4:6], "big") == quantity and int.from_bytes(raw[-2:], "little") == crc16(raw[:-2])


def valid_response_adu(raw, unit, words):
    payload = b"".join(word.to_bytes(2, "big") for word in words)
    return raw is not None and len(raw) == 5 + len(payload) and raw[0] == unit and raw[1] == 3 and raw[2] == len(payload) and raw[3:-2] == payload and int.from_bytes(raw[-2:], "little") == crc16(raw[:-2])


def decimal(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        fail("native_evidence_missing")
    if not number.is_finite():
        fail("native_evidence_missing")
    if not number:
        return {"coefficient": "0", "exponent10": 0}
    sign, digits, exponent = number.normalize().as_tuple()
    coefficient = "".join(str(digit) for digit in digits)
    if sign:
        coefficient = "-" + coefficient
    return {"coefficient": coefficient, "exponent10": exponent}


def signed16(word):
    return word - 0x10000 if word & 0x8000 else word


def fact_key(item_id, asset_id):
    return {"pack_id": PACK["id"], "pack_version": PACK["version"], "fact_id": item_id, "dimensions": [{"id": "storage.dimension.pack", "value": {"kind": "text", "text": asset_id}}]}


def quantity(value, unit):
    return {"kind": "quantity", "quantity": {"number": decimal(value), "unit": unit}}


def symbol(token):
    return {"kind": "symbol", "symbol": {"namespace": "storage.status.operating", "token": token, "known": True}}


def validate_contract(document):
    if document.get("contract") != "helianthus.semantic.mapping.growatt-bms-rs485-v202.storage/v1" or document.get("mapping_id") != "storage.mapping.growatt.rs485.1xsxxp.v202" or document.get("pack") != PACK or document.get("status") != "accepted_source_specific_read_only_mapping_gate" or document.get("pins") != PINS:
        fail("contract")
    native = document.get("native_contract", {})
    if native.get("revision") != REVISION or native.get("unit") != {"selection": "explicit_unicast", "allowed": "1..247", "broadcast_zero": "no_send"} or native.get("slices") != SLICES or native.get("typed_source") != "GrowattBMSTypedReadOnlyStatus" or native.get("qualification") != {"physical_qualified": False, "mapping_qualified": True, "outbound_allowed": False}:
        fail("native contract")
    identity = document.get("identity", {})
    for key in ("asset_id", "source_id"):
        value = identity.get(key, {})
        if value.get("required") is not True or value.get("non_secret") is not True or value.get("forbidden_derivations") != ["unit_id", "vendor", "version", "company", "generation"]:
            fail("identity contract")
    if identity.get("source_id", {}).get("distinct_from") != "asset_id" or identity.get("failure") != "missing_or_invalid_asset_or_source_identity_fails_closed":
        fail("identity contract")
    if identity.get("binding_id") != {"source": "gateway_domain_separated_asset_source_profile_binding", "required": True, "non_secret": True, "stable_inputs": ["asset_id", "source_id", "profile"]}:
        fail("identity contract")
    lifecycle = document.get("lifecycle", {})
    required = ["observation_id", "observation_revision", "receipt_wall", "receipt_monotonic", "clock_epoch", "source_epoch", "driver_generation", "transport_generation", "unit_id", "revision", "slices", "request_id", "request_adu", "response_adu", "words"]
    if lifecycle.get("required_observation_evidence") != required or lifecycle.get("qualification") != "mapping_qualified_and_physical_unqualified":
        fail("lifecycle contract")
    rules = document.get("field_rules", [])
    requested = sorted((rule.get("requested") for rule in rules), key=lambda item: item.get("item_id", ""))
    if len(rules) != 7 or document.get("projection", {}).get("requested_items") != requested:
        fail("requested items")
    for rule in rules:
        disposition = rule.get("disposition", {})
        losses = disposition.get("loss")
        if disposition.get("outcome") == "exact" and losses != []:
            fail("exact loss")
        if disposition.get("outcome") == "transformed" and (not losses or any(loss.get("kind") not in LOSS_KINDS or not loss.get("source_items") or not loss.get("description") or type(loss.get("reversible")) is not bool for loss in losses)):
            fail("transformed loss")
    if len(document.get("withheld", [])) != 7 or any(not row.get("reason") for row in document["withheld"]) or document.get("unsupported") != UNSUPPORTED:
        fail("withheld unsupported")
    projection = document.get("projection", {})
    if projection.get("error_precedence") != ERROR_PRECEDENCE or projection.get("operations") != "unsupported_no_authority" or projection.get("missing_native") != "unavailable_withheld_never_zero":
        fail("projection")
    cutover = document.get("consumer_cutover", {})
    if cutover != {"consumers": ["semantic_mcp", "graphql", "portal", "home_assistant"], "implementation_requirement": "one_atomic_cutover", "required_removals": ["legacy_semantic_path", "fallback", "comparator", "compatibility_only_path", "dual_publication"], "until_implemented": "no_public_consumer_binding"}:
        fail("consumer cutover")


def validate_observation(case):
    errors = set()
    observation, lifecycle = case.get("observation"), case.get("lifecycle")
    identity, source = case.get("identity"), case.get("source")
    if not isinstance(observation, dict) or not isinstance(lifecycle, dict):
        fail("native_evidence_missing")
    slices = observation.get("slices")
    if not isinstance(slices, list) or len(slices) != 4:
        errors.add("native_evidence_missing")
        slices = []
    request_ids, units = [], []
    for index, row in enumerate(slices):
        if not isinstance(row, dict):
            errors.add("native_evidence_missing")
            continue
        words, request_id, unit = row.get("words"), row.get("request_id"), row.get("unit_id")
        words_valid = isinstance(words, list) and all(isinstance(word, int) and not isinstance(word, bool) and 0 <= word <= 0xFFFF for word in words)
        if not isinstance(request_id, int) or isinstance(request_id, bool) or request_id < 1 or not words_valid:
            errors.add("native_evidence_missing")
        else:
            request_ids.append(request_id)
        required = SLICES[index] if index < len(SLICES) else {}
        try:
            offset = int(str(row.get("offset")), 16)
        except (TypeError, ValueError):
            offset = -1
        if {key: row.get(key) for key in ("function", "offset", "quantity")} != required or not isinstance(unit, int) or isinstance(unit, bool) or not 1 <= unit <= 247 or row.get("transport_generation") != lifecycle.get("transport_generation"):
            errors.add("revision_or_unit_or_slice_invalid")
        elif words_valid:
            request = decode_adu(row.get("request_adu_hex"))
            response = decode_adu(row.get("response_adu_hex"))
            if len(words) != row.get("quantity") or not valid_request_adu(request, unit, offset, row["quantity"]) or not valid_response_adu(response, unit, words):
                errors.add("native_evidence_missing")
        units.append(unit)
    if len(request_ids) != len(set(request_ids)) or len({repr(unit) for unit in units}) > 1:
        errors.add("native_evidence_missing")
    if observation.get("revision") != REVISION:
        errors.add("revision_or_unit_or_slice_invalid")
    asset_id = identity.get("asset_id") if isinstance(identity, dict) else None
    binding_id = identity.get("binding_id") if isinstance(identity, dict) else None
    source_id = source.get("source_id") if isinstance(source, dict) else None
    if not isinstance(asset_id, str) or not OPAQUE_RE.fullmatch(asset_id) or not isinstance(binding_id, str) or not OPAQUE_RE.fullmatch(binding_id) or not isinstance(source_id, str) or not OPAQUE_RE.fullmatch(source_id) or asset_id == source_id:
        errors.add("identity_missing_or_invalid")
    opaque_lifecycle = ("observation_id", "clock_epoch", "source_epoch")
    numeric_lifecycle = ("observation_revision", "driver_generation", "transport_generation")
    if any(not isinstance(lifecycle.get(key), str) or not OPAQUE_RE.fullmatch(lifecycle[key]) for key in opaque_lifecycle) or any(not isinstance(lifecycle.get(key), int) or isinstance(lifecycle[key], bool) or lifecycle[key] < 1 for key in numeric_lifecycle) or not isinstance(lifecycle.get("receipt_monotonic"), int) or isinstance(lifecycle.get("receipt_monotonic"), bool) or lifecycle.get("receipt_monotonic", 0) < 1:
        errors.add("lifecycle_missing")
    try:
        received = datetime.fromisoformat(lifecycle.get("receipt_wall", "").replace("Z", "+00:00"))
        if received.tzinfo is None:
            raise ValueError
    except (AttributeError, ValueError):
        errors.add("lifecycle_missing")
    if case.get("qualification") != {"physical_qualified": False, "mapping_qualified": True, "outbound_allowed": False}:
        errors.add("mapping_unqualified")
    if case.get("request_operation"):
        errors.add("unsupported_or_withheld")
    for code in ERROR_PRECEDENCE:
        if code in errors:
            fail(code)
    return observation, lifecycle, asset_id, source_id, binding_id


def project(case, contract):
    observation, lifecycle, asset_id, source_id, binding_id = validate_observation(case)
    typed = observation.get("typed")
    if not isinstance(typed, dict):
        fail("native_evidence_missing")
    words = [row["words"] for row in observation["slices"]]
    native_state = {1: "soft_starting", 2: "charging", 4: "discharging", 8: "standby"}.get(words[1][6])
    raw_values = {"soc_percent": Decimal(words[1][8]), "pack_voltage_volts": Decimal(words[1][9]) / 100, "pack_current_amps": Decimal(signed16(words[1][10])) / 100, "temperature_celsius": Decimal(signed16(words[1][11])), "cumulative_charge_amp_hours": Decimal(words[2][5]) / 10, "cumulative_discharge_amp_hours": Decimal(words[2][6]) / 10}
    if native_state is None or typed.get("operating_state") != native_state:
        fail("native_evidence_missing")
    for name, raw_value in raw_values.items():
        try:
            if Decimal(str(typed.get(name))) != raw_value:
                fail("native_evidence_missing")
        except InvalidOperation:
            fail("native_evidence_missing")
    if not 0 <= raw_values["soc_percent"] <= 100 or raw_values["pack_voltage_volts"] < 0 or raw_values["cumulative_charge_amp_hours"] < 0 or raw_values["cumulative_discharge_amp_hours"] < 0:
        fail("native_evidence_missing")
    requested = contract["projection"]["requested_items"]
    rules = {rule["target"]: rule for rule in contract["field_rules"]}
    native_values = {"storage.capacity.charge": quantity(raw_values["cumulative_charge_amp_hours"], "unit.ampere_hour"), "storage.capacity.discharge": quantity(raw_values["cumulative_discharge_amp_hours"], "unit.ampere_hour"), "storage.pack.current": quantity(raw_values["pack_current_amps"], "unit.ampere"), "storage.pack.voltage": quantity(raw_values["pack_voltage_volts"], "unit.volt"), "storage.state.soc": quantity(raw_values["soc_percent"], "unit.percent"), "storage.temperature.pack": quantity(raw_values["temperature_celsius"], "unit.celsius")}
    operating_token = {"charging": "active", "discharging": "active", "standby": "standby"}.get(native_state)
    facts, dispositions = [], []
    for requested_item in requested:
        item_id = requested_item["item_id"]
        key = fact_key(item_id, asset_id)
        if item_id == "storage.status.operating" and operating_token is None:
            dispositions.append({"kind": "fact", "item_id": item_id, "outcome": "withheld", "source_keys": [], "loss": [], "reason": "storage.reason.soft_starting_not_representable"})
            continue
        value = symbol(operating_token) if item_id == "storage.status.operating" else native_values[item_id]
        facts.append({"key": key, "value": value, "source_path": {"binding_id": binding_id, "source_id": source_id, "source_epoch_id": lifecycle["source_epoch"], "driver_generation": lifecycle["driver_generation"]}, "observation_id": lifecycle["observation_id"], "observation_revision": lifecycle["observation_revision"]})
        rule = rules[item_id]
        dispositions.append({"kind": "fact", "item_id": item_id, "outcome": rule["disposition"]["outcome"], "source_keys": [key], "loss": copy.deepcopy(rule["disposition"]["loss"])})
    return {"facts": facts, "requested": copy.deepcopy(requested), "dispositions": dispositions, "withheld_native": copy.deepcopy(contract["withheld"]), "operations": []}


def document(contract):
    validate_contract(contract)
    scenarios = contract.get("scenarios", [])
    if not scenarios or scenarios[0].get("polarity") != "positive":
        fail("scenario coverage")
    baseline = scenarios[0]
    for scenario in scenarios:
        case = copy.deepcopy(baseline)
        for key in ("expect", "id", "polarity"):
            case.pop(key, None)
        for mutation in scenario.get("mutations", []):
            mutate(case, mutation)
        expected = scenario.get("expect", {})
        if "output" in expected:
            if project(case, contract) != expected["output"]:
                fail("scenario output")
            continue
        try:
            project(case, contract)
        except ValueError as error:
            if str(error) != expected.get("error"):
                raise
        else:
            fail(scenario.get("id", "scenario") + " accepted")


def main():
    contract = load()
    document(contract)
    text = DOC.read_text()
    for token in ("gateway-configured", "physical qualification", "ampere-hours", "one atomic SemReg cutover", "outbound_allowed=false", "offline synthetic"):
        if token not in text:
            fail("document boundary")
    outputs = sum("output" in scenario.get("expect", {}) for scenario in contract["scenarios"])
    print(f"Growatt BMS RS-485 v2.02 storage mapping: PASS; {outputs} executable outputs and {len(contract['scenarios']) - outputs} rejected scenarios")


if __name__ == "__main__":
    main()
