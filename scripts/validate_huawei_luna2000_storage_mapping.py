#!/usr/bin/env python3
"""Execute the Huawei LUNA2000 storage gate: what helianthus.pack.storage@1.1.0 takes once a battery profile is admitted, and nothing before."""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "api/v1/mappings/huawei-luna2000-storage-v1.json"
DOC = ROOT / "api/v1/mappings/huawei-luna2000-storage-v1.md"
PACK_TABLES = ROOT / "api/v1/packs/storage-bms-contract-tables.json"

PACK = {"id": "helianthus.pack.storage", "version": "1.1.0"}
NATIVE_PREFIX = "native.huawei.luna2000."
LOSS_KINDS = {"unit", "range", "precision", "time", "symbol", "provenance", "identity", "capability", "operation", "policy"}
GRADES = ["unknown", "hypothesis", "proven"]
ERROR_PRECEDENCE = ["gate_revision_required", "native_evidence_invalid", "identity_missing_or_invalid", "lifecycle_missing", "mapping_unqualified", "unsupported_or_withheld"]
OPAQUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")
HEX_RUN_RE = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")
ID_FORBIDDEN_TEXT = ("serial", "esn", "sun2000", "huawei", "luna", "smartlogger", "sdongle", "s-dongle", "emma")
ID_ADDRESS_RE = re.compile(r"(\d{1,3}\.){3}\d{1,3}|:\d{3,5}$")
UNIT_SHIFT = {("%", "unit.percent"): 0, ("kW", "unit.watt"): 3, ("kWh", "unit.kilowatt_hour"): 0}
FORBIDDEN_DERIVATIONS = ["serial_number", "esn", "vendor", "model", "firmware_or_version", "routed_unit_alone", "endpoint_address"]
REGISTRY_FLAGS = {"catalog_registered": False, "automatic_runtime_admission": False, "live_qualified": False, "support_claim": False, "write_authority": False}
QUALIFICATION = {**REGISTRY_FLAGS, "mapping_qualified": True, "outbound_allowed": False}
EVIDENCE = {
    "monitoring_contract": {"repository": "helianthus-docs-modbus", "issue": 242, "pull_request": 253, "pages": ["protocols/huawei/monitoring-readonly-v1.md", "protocols/huawei/read-pacing-v1.md"]},
    "registry_profiles": {"repository": "helianthus-modbusreg", "issue": 348, "pull_request": 357},
    "program_issues": {"repository": "helianthus-modbusreg", "issues": [199, 201]},
    "multi_endpoint_contract": {"repository": "helianthus-docs-ebus", "issue": 746, "pull_request": 748},
    "sibling_gates": ["huawei-sun2000-pv-v1", "huawei-gateway-meter-infrastructure-v1"],
    "grades": ["proven", "hypothesis", "unknown"],
}
ADMISSION = {
    "registry_disposition": {"profile": "huawei.luna2000", "outcome": "NO_ADMISSIBLE_PROFILE", "battery_groups": "PRESENT_NOT_ADMITTED", "facts_admitted": False, "decoder_keys": 0},
    "selection_outcomes_allowed": ["INSUFFICIENT_EVIDENCE", "NO_ADMISSIBLE_PROFILE", "AMBIGUOUS"],
    "selected_profile": "fails_closed_until_this_gate_is_revised",
    "registry_flags": REGISTRY_FLAGS,
    "preconditions_for_any_mapping": [
        "a_battery_profile_for_the_exact_family_is_admitted_with_a_consulted_edition",
        "type_word_order_gain_unit_and_sign_of_each_consumed_word_are_stated",
        "a_sign_is_graded_before_any_power_is_published",
        "the_aggregation_basis_is_recorded_as_provenance",
        "the_storage_asset_granularity_is_settled",
        "this_gate_is_revised_with_executable_vectors",
    ],
}
# native item -> (source, read group or None). Registry items come from the LUNA2000 disposition; planned items from the monitoring contract.
INVENTORY = [
    ("battery_group_37000_30", "registry_disposition", (37000, 30)), ("battery_single_read_37000_1", "registry_disposition", (37000, 1)),
    ("battery_group_37066_4", "registry_disposition", (37066, 4)), ("battery_group_47000_1", "registry_disposition", (47000, 1)),
    ("site_battery_soc", "monitoring_contract_planned", None), ("site_battery_power", "monitoring_contract_planned", None), ("plant_battery_power", "monitoring_contract_planned", None),
    ("site_battery_energy_charged_total", "monitoring_contract_planned", None), ("site_battery_energy_discharged_total", "monitoring_contract_planned", None),
    ("site_battery_energy_charged_day", "monitoring_contract_planned", None), ("site_battery_energy_discharged_day", "monitoring_contract_planned", None),
    ("site_rated_storage_capacity", "monitoring_contract_planned", None),
]
READS = {read: nid for nid, source, read in INVENTORY if read}
RUNTIME_REASONS = {"storage.reason.battery_group_not_read", "storage.reason.zero_word_is_not_a_battery_value", "storage.reason.battery_group_exception_no_negation"}
PRIMARY_REASON = "storage.reason.no_admitted_battery_profile"
REQUESTED = ["storage.energy.charged", "storage.energy.discharged", "storage.pack.power", "storage.state.soc", "storage.status.operating"]
NEVER_REQUESTED = ["storage.limit.charge_power", "storage.limit.discharge_power", "storage.status.interlock", "storage.operation.set_charge_limit", "storage.operation.set_discharge_limit"]
UNSUPPORTED = ["rated_capacity_in_energy_units", "state_of_health", "cell_and_module_values", "charge_and_discharge_power_limits", "interlock", "working_mode_or_schedule", "remote_dispatch", "authority", "write_operations", "acknowledgement", "readback", "retry", "control_routes"]
SIGNS = {"unknown_no_value_without_a_graded_sign", "positive_while_charging_negative_while_discharging"}
COUNTERS = {"reset_wrap_and_continuity_never_inferred"}
DOC_TOKENS = ("gateway-configured", "unknown, never zero", "no binary floating point", "capacity in energy units is withheld", "outbound_allowed=false", "one atomic cutover", "never converted")


def fail(code):
    raise ValueError(code)


def _no_float(text):
    raise ValueError("binary floating point literal in JSON: " + text)


def _no_duplicates(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate JSON member")
    return dict(pairs)


def loads(text):
    return json.loads(text, parse_float=_no_float, object_pairs_hook=_no_duplicates)


def load():
    return loads(PATH.read_text(encoding="utf-8"))


def contains_float(value):
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_float(item) for item in value)
    return False


def mutate(value, mutation):
    cursor, parts = value, mutation["path"].split(".")
    for part in parts[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    last = parts[-1]
    key = int(last) if isinstance(cursor, list) else last
    if mutation.get("remove"):
        del cursor[key]
    else:
        cursor[key] = mutation["value"]


def pack_tables():
    tables = json.loads(PACK_TABLES.read_text(encoding="utf-8"))
    return {field["id"]: field for field in tables["field_specs"]}, {operation["id"] for operation in tables["operations"]}


def validate_contract(document):
    fields, operations = pack_tables()
    if document.get("contract") != "helianthus.semantic.mapping.huawei-luna2000.storage/v1" or document.get("mapping_id") != "storage.mapping.huawei.luna2000.battery" or document.get("pack") != PACK or document.get("status") != "accepted_withheld_mapping_gate_no_battery_profile":
        fail("contract")
    if document.get("evidence") != EVIDENCE:
        fail("evidence")
    if document.get("admission") != ADMISSION:
        fail("admission")
    rules = document.get("field_rules", [])
    listed = [(rule.get("native_id"), rule.get("source"), (rule["read"]["offset"], rule["read"]["quantity"]) if rule.get("read") else None) for rule in rules]
    if listed != INVENTORY:
        fail("native inventory")
    reasons = document.get("reasons", {})
    for name, spec in reasons.items():
        if not name.startswith("storage.reason.") or spec.get("loss_kind") not in LOSS_KINDS or not spec.get("description") or type(spec.get("reversible")) is not bool:
            fail("reason loss")
    used, targets = set(), set()
    for rule in rules:
        disposition = rule.get("disposition", {})
        if set(disposition) != {"outcome", "reason"} or disposition["outcome"] != "withheld" or disposition["reason"] not in reasons or rule.get("grade") not in GRADES:
            fail("withheld reason")
        used.add(disposition["reason"])
        prospective = rule.get("prospective")
        if prospective is None:
            continue
        target = prospective.get("target")
        pack_field = fields.get(target)
        if prospective.get("in_force") is not False or pack_field is None or prospective.get("dimension") != pack_field["dimension"] or prospective.get("unit") != pack_field.get("unit"):
            fail("prospective target")
        native = prospective.get("native")
        if pack_field["kind"] == "symbol":
            if prospective.get("symbols") != [] or native is not None:
                fail("prospective symbols")
        else:
            if native != rule.get("native") or UNIT_SHIFT.get((native.get("unit"), prospective["unit"])) is None:
                fail("prospective native form")
        if target == "storage.pack.power" and prospective.get("sign") not in SIGNS:
            fail("prospective sign")
        if target in ("storage.energy.charged", "storage.energy.discharged") and prospective.get("counter") not in COUNTERS:
            fail("prospective counter")
        targets.add(target)
    if sorted(targets) != REQUESTED or document.get("projection", {}).get("requested_items") != [{"kind": "fact", "item_id": item} for item in REQUESTED]:
        fail("requested items")
    if set(reasons) != used | RUNTIME_REASONS | {PRIMARY_REASON}:
        fail("reason inventory")
    identity = document.get("identity", {})
    for key in ("asset_id", "source_id"):
        entry = identity.get(key, {})
        if entry.get("required") is not True or entry.get("non_secret") is not True or entry.get("forbidden_derivations") != FORBIDDEN_DERIVATIONS:
            fail("identity contract")
    if identity.get("source_id", {}).get("distinct_from") != "asset_id" or identity.get("failure") != "missing_or_invalid_asset_or_source_identity_fails_closed" or identity.get("storage_asset_granularity") != "unresolved_batteries_are_registers_of_the_inverter_units_not_units_of_their_own":
        fail("identity contract")
    if identity.get("binding_id") != {"source": "gateway_domain_separated_asset_source_profile_binding", "required": True, "non_secret": True, "stable_inputs": ["asset_id", "source_id", "profile_id"]}:
        fail("identity contract")
    if document.get("lifecycle") != {
        "required_observation_evidence": ["observation_id", "observation_revision", "receipt_wall", "receipt_monotonic", "clock_epoch", "source_epoch", "driver_generation", "connection_generation", "luna_selection", "reads"],
        "absent_optional_group": "unknown_never_zero", "exception": "no_negation_of_the_identified_parent",
        "last_known_good": "retained_with_its_original_age_when_a_battery_value_exists", "withdrawal": "explicit_generation_fenced"}:
        fail("lifecycle contract")
    if document.get("outcome_vocabulary") != {"exact": "exact", "transformed": "transformed", "withheld": "withheld", "native_only": "unrepresentable"}:
        fail("outcome vocabulary")
    if document.get("capacity") != {"energy_units": "withheld", "pack_carries": "ampere_hours_only", "conversion": "forbidden", "needs": "separate_semreg_and_pack_revision"}:
        fail("capacity")
    if document.get("unsupported") != UNSUPPORTED:
        fail("unsupported")
    never = document.get("pack_items_never_requested")
    if never != NEVER_REQUESTED or any(item not in fields and item not in operations for item in never) or set(never) & set(REQUESTED):
        fail("control-adjacent items")
    projection = document.get("projection", {})
    if projection.get("primary_reason") != PRIMARY_REASON or projection.get("error_precedence") != ERROR_PRECEDENCE or projection.get("operations") != "unsupported_no_authority" or projection.get("missing_native") != "unavailable_withheld_never_zero" or projection.get("target") != "SemReg_storage_projection":
        fail("projection")
    if document.get("consumer_cutover") != {"consumers": ["semantic_mcp", "graphql", "portal", "home_assistant"], "path": "shared_semantic_snapshot_only", "until_implemented": "no_public_consumer_binding"}:
        fail("consumer cutover")
    if contains_float(document):
        fail("binary floating point")


def validate_case(case, contract):
    if not isinstance(case, dict):
        fail("native_evidence_invalid")
    errors = set()
    selection = case.get("luna_selection")
    outcome = selection.get("outcome") if isinstance(selection, dict) else None
    if outcome == "PROFILE_SELECTED":
        fail("gate_revision_required")
    if outcome not in ADMISSION["selection_outcomes_allowed"] or contains_float(case):
        errors.add("native_evidence_invalid")
    reads = {}
    for read in case.get("reads") if isinstance(case.get("reads"), list) else [None]:
        key = (read.get("offset"), read.get("quantity")) if isinstance(read, dict) else None
        if key not in READS or key in reads or read.get("outcome") not in ("ANSWERED", "EXCEPTION", "FAILED", "NOT_READ"):
            errors.add("native_evidence_invalid")
            continue
        words, code = read.get("words"), read.get("exception_code")
        if read["outcome"] == "ANSWERED":
            valid = isinstance(words, list) and len(words) == key[1] and all(type(word) is int and 0 <= word <= 0xFFFF for word in words) and code is None
        elif read["outcome"] == "EXCEPTION":
            valid = words is None and type(code) is int and code >= 1
        else:
            valid = words is None and code is None
        if not valid:
            errors.add("native_evidence_invalid")
        reads[key] = read
    identity, source = case.get("identity"), case.get("source")
    values = (identity.get("asset_id") if isinstance(identity, dict) else None, identity.get("binding_id") if isinstance(identity, dict) else None, source.get("source_id") if isinstance(source, dict) else None)
    if any(not isinstance(item, str) or not OPAQUE_RE.fullmatch(item) or any(token in item.lower() for token in ID_FORBIDDEN_TEXT) or ID_ADDRESS_RE.search(item) for item in values) or len(set(values)) != 3:
        errors.add("identity_missing_or_invalid")
    life = case.get("lifecycle") if isinstance(case.get("lifecycle"), dict) else {}
    if any(not isinstance(life.get(key), str) or not OPAQUE_RE.fullmatch(life[key]) for key in ("observation_id", "clock_epoch", "source_epoch")) or any(type(life.get(key)) is not int or life[key] < 1 for key in ("observation_revision", "driver_generation", "connection_generation")) or type(life.get("receipt_monotonic")) is not int or life.get("receipt_monotonic", 0) < 1:
        errors.add("lifecycle_missing")
    try:
        if datetime.fromisoformat(life.get("receipt_wall", "").replace("Z", "+00:00")).tzinfo is None:
            raise ValueError
    except (AttributeError, ValueError):
        errors.add("lifecycle_missing")
    if case.get("qualification") != QUALIFICATION:
        errors.add("mapping_unqualified")
    if case.get("request_operation") or case.get("request_conversion") or case.get("request_item"):
        errors.add("unsupported_or_withheld")
    for code in ERROR_PRECEDENCE:
        if code in errors:
            fail(code)
    return reads


def project(case, contract):
    reads = validate_case(case, contract)
    rows = []
    for rule in contract["field_rules"]:
        reason = rule["disposition"]["reason"]
        if rule["source"] == "registry_disposition":
            read = reads.get((rule["read"]["offset"], rule["read"]["quantity"]))
            if read is None or read["outcome"] in ("FAILED", "NOT_READ"):
                reason = "storage.reason.battery_group_not_read"
            elif read["outcome"] == "EXCEPTION":
                reason = "storage.reason.battery_group_exception_no_negation"
            elif all(word == 0 for word in read["words"]):
                reason = "storage.reason.zero_word_is_not_a_battery_value"
            else:
                reason = PRIMARY_REASON
        rows.append({"native_id": rule["native_id"], "outcome": "withheld", "reason": reason})
    spec = contract["reasons"][PRIMARY_REASON]
    dispositions = [{"kind": "fact", "item_id": item["item_id"], "outcome": "withheld", "source_keys": [], "reason": PRIMARY_REASON,
                     "loss": [{"kind": spec["loss_kind"], "source_items": [NATIVE_PREFIX + "battery"], "description": spec["description"], "reversible": spec["reversible"]}]} for item in contract["projection"]["requested_items"]]
    output = {"facts": [], "relationships": [], "requested": copy.deepcopy(contract["projection"]["requested_items"]), "dispositions": dispositions, "native_dispositions": rows, "operations": []}
    assert_complete(output, contract)
    return output


def assert_complete(output, contract):
    """Every native item carries exactly one disposition, a reason, and no value."""
    if [row["native_id"] for row in output["native_dispositions"]] != [nid for nid, _, _ in INVENTORY] or output["facts"] or output["relationships"]:
        fail("native disposition completeness")
    if any(row["outcome"] != "withheld" or row["reason"] not in contract["reasons"] for row in output["native_dispositions"]):
        fail("withheld without reason")


def summarize(output):
    return {"facts": output["facts"], "dispositions": [{"item_id": item["item_id"], "outcome": item["outcome"], "published": len(item["source_keys"]), "reason": item["reason"], "loss": [loss["kind"] for loss in item["loss"]]} for item in output["dispositions"]],
            "native_dispositions": output["native_dispositions"], "operations": output["operations"]}


def run_scenario(scenario, contract):
    case = copy.deepcopy(contract["baselines"][scenario["baseline"]])
    for mutation in scenario.get("mutations", []):
        mutate(case, mutation)
    return project(case, contract)


def validate_scenarios(contract):
    scenarios = contract.get("scenarios", [])
    if set(contract.get("baselines", {})) != {"default"} or not scenarios or scenarios[0].get("mutations") or scenarios[0].get("polarity") != "positive":
        fail("scenario baselines")
    ids = [scenario.get("id") for scenario in scenarios]
    if len(ids) != len(set(ids)):
        fail("scenario ids")
    seen_reasons, seen_errors = set(), set()
    for scenario in scenarios:
        expected = scenario.get("expect", {})
        if scenario.get("polarity") == "negative":
            if set(expected) != {"error"} or expected["error"] not in ERROR_PRECEDENCE:
                fail("negative scenario shape")
            try:
                run_scenario(scenario, contract)
            except ValueError as error:
                if str(error) != expected["error"]:
                    raise
                seen_errors.add(expected["error"])
            else:
                fail(scenario["id"] + " accepted")
            continue
        output = run_scenario(scenario, contract)
        if "output" in expected:
            if output != expected["output"]:
                fail("scenario output " + scenario["id"])
        elif summarize(output) != expected.get("summary"):
            fail("scenario summary " + scenario["id"])
        seen_reasons |= {row["reason"] for row in output["native_dispositions"]} | {item["reason"] for item in output["dispositions"]}
    if seen_errors != set(ERROR_PRECEDENCE):
        fail("negative scenarios do not cover every error code")
    if seen_reasons != set(contract["reasons"]):
        fail("scenarios do not cover every reason")


def document(contract):
    validate_contract(contract)
    validate_scenarios(contract)


def table(text, heading):
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        fail("document heading " + heading)
    rows = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.startswith("|"):
            rows.append([cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")])
    return rows[2:]


def native_form(native):
    return "%s, %s, gain %d" % (native["type"], native["unit"], native["gain"]) if native else "none decoded"


def expected_tables(contract):
    withheld, prospective = [], []
    for rule in contract["field_rules"]:
        reason = rule["disposition"]["reason"]
        withheld.append([rule["native_id"], rule["source"], rule["grade"].capitalize(), reason, contract["reasons"][reason]["loss_kind"]])
        plan = rule.get("prospective")
        if plan:
            rule_text = plan.get("sign") or plan.get("counter") or ("empty table, observed states only" if plan.get("symbols") == [] else "none")
            prospective.append([plan["target"], plan["dimension"], rule["native_id"], native_form(plan.get("native") or rule.get("native")), rule_text, rule["grade"].capitalize()])
    return withheld, prospective


def check_document(contract, text):
    withheld, prospective = expected_tables(contract)
    if table(text, "## Withheld items") != withheld or table(text, "## Prospective intake") != prospective:
        fail("document tables")
    if [row[0] for row in table(text, "## Acceptance vectors")] != [scenario["id"] for scenario in contract["scenarios"]]:
        fail("document vectors")
    flat = " ".join(text.split()).lower()
    for token in DOC_TOKENS:
        if token not in flat:
            fail("document boundary")
    if HEX_RUN_RE.search(text) or HEX_RUN_RE.search(json.dumps(contract)):
        fail("publication: digest or revision literal")


def main():
    contract = load()
    document(contract)
    check_document(contract, DOC.read_text(encoding="utf-8"))
    positives = sum(scenario["polarity"] == "positive" for scenario in contract["scenarios"])
    print(f"Huawei LUNA2000 storage mapping: PASS; {positives} executable outputs and {len(contract['scenarios']) - positives} rejected scenarios")


if __name__ == "__main__":
    main()
