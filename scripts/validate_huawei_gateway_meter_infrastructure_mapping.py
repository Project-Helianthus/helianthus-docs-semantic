#!/usr/bin/env python3
"""Execute the Huawei gateway-meter gate: what helianthus.pack.infrastructure@1.0.0 will take from a meter once one is decoded, and nothing before."""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "api/v1/mappings/huawei-gateway-meter-infrastructure-v1.json"
DOC = ROOT / "api/v1/mappings/huawei-gateway-meter-infrastructure-v1.md"
PACK_CATALOG = ROOT / "api/v1/packs/infrastructure-acceptance-vectors.json"
LOCAL_ASSESSMENT = ROOT / "mappings/infrastructure/gateway-runtime.md"

PACK = {"id": "helianthus.pack.infrastructure", "version": "1.0.0"}
NATIVE_PREFIX = "native.huawei.gateway_meter."
LOSS_KINDS = {"unit", "range", "precision", "time", "symbol", "provenance", "identity", "capability", "operation", "policy"}
GRADES = ["unknown", "hypothesis", "proven"]
ERROR_PRECEDENCE = ["gate_revision_required", "native_evidence_invalid", "identity_missing_or_invalid", "role_invalid", "lifecycle_missing", "mapping_unqualified", "unsupported_or_withheld"]
OPAQUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")
HEX_RUN_RE = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")
ID_FORBIDDEN_TEXT = ("serial", "esn", "sun2000", "huawei", "luna", "smartlogger", "sdongle", "s-dongle", "emma")
ID_ADDRESS_RE = re.compile(r"(\d{1,3}\.){3}\d{1,3}|:\d{3,5}$")
UNIT_SHIFT = {("kW", "unit.watt"): 3, ("W", "unit.watt"): 0, ("kWh", "unit.kilowatt_hour"): 0, ("ratio", "unit.ratio"): 0}
FORBIDDEN_DERIVATIONS = ["serial_number", "esn", "vendor", "model", "firmware_or_version", "routed_unit_alone", "endpoint_address"]
REGISTRY_FLAGS = {"catalog_registered": False, "automatic_runtime_admission": False, "live_qualified": False, "support_claim": False, "write_authority": False}
QUALIFICATION = {**REGISTRY_FLAGS, "mapping_qualified": True, "outbound_allowed": False}
EVIDENCE = {
    "monitoring_contract": {"repository": "helianthus-docs-modbus", "issue": 242, "pull_request": 253, "pages": ["protocols/huawei/monitoring-readonly-v1.md", "protocols/huawei/read-pacing-v1.md", "protocols/huawei/gateway-power-meter-v1.md"]},
    "meter_observation_amendment": {"repository": "helianthus-docs-modbus", "issue": 254},
    "registry_profiles": {"repository": "helianthus-modbusreg", "issue": 348, "pull_request": 357},
    "program_issues": {"repository": "helianthus-modbusreg", "issues": [199, 201]},
    "multi_endpoint_contract": {"repository": "helianthus-docs-ebus", "issue": 746, "pull_request": 748},
    "gateway_local_assessment": "mappings/infrastructure/gateway-runtime.md",
    "sibling_gates": ["huawei-sun2000-pv-v1", "huawei-luna2000-storage-v1"],
    "grades": ["proven", "hypothesis", "unknown"],
}
ADMISSION = {
    "meter_class_contract": False, "meter_identity": "INSUFFICIENT_EVIDENCE", "decoded_meter_words": 0,
    "selection_outcomes_allowed": ["INSUFFICIENT_EVIDENCE", "NO_ADMISSIBLE_PROFILE", "AMBIGUOUS"],
    "selected_meter": "fails_closed_until_this_gate_is_revised", "registry_flags": REGISTRY_FLAGS,
    "preconditions_for_any_mapping": [
        "a_meter_class_contract_exists_with_an_identity_read", "the_exposure_path_is_observed",
        "type_word_order_gain_unit_and_sign_of_each_consumed_word_are_stated", "a_sign_reference_is_graded_per_source_and_never_mixed",
        "the_role_is_declared_in_configuration", "this_gate_is_revised_with_executable_vectors"],
}
ROLE = {
    "source": "operator_configuration_keyed_to_endpoint_and_routed_unit",
    "values": ["grid_connection", "feeder", "circuit"],
    "undeclared": "role_unknown_and_role_dependent_facts_not_published",
    "never_derived_from": ["registers", "sign_or_magnitude_of_a_power_value", "label", "unit_number", "listing_order", "model", "presence_of_another_meter"],
    "dimension_by_role": {
        "grid_connection": {"power": "infrastructure.dimension.grid_connection", "energy": "infrastructure.dimension.meter", "relationship": "infrastructure.relationship.grid_connection_meter"},
        "feeder": {"power": "withheld", "energy": "infrastructure.dimension.meter", "relationship": "none_decided"},
        "circuit": {"power": "withheld", "energy": "infrastructure.dimension.meter", "relationship": "none_decided"},
    },
}
INVENTORY = [
    ("smartlogger_meter_electrical_group", "smartlogger"), ("smartlogger_meter_energy_totals", "smartlogger"), ("emma_built_in_sensor_group", "emma"), ("emma_external_sensor_group", "emma"),
    ("sdongle_inverter_exposed_meter_group", "sdongle"), ("sdongle_plant_grid_power", "sdongle"), ("sun2000_inverter_exposed_meter_group_refused", "sun2000_m3"), ("profile_meter_groups", "sun2000_profiles"),
]
FEEDABLE = [nid for nid, path in INVENTORY[:6]]
PRIMARY_REASON = "infrastructure.reason.no_meter_class_contract"
RUNTIME_REASONS = {"infrastructure.reason.answered_not_decoded", "infrastructure.reason.read_exception_no_negation"}
REQUESTED = ["infrastructure.ac.active_power", "infrastructure.ac.current", "infrastructure.ac.power_factor", "infrastructure.ac.voltage", "infrastructure.energy.export", "infrastructure.energy.import", "infrastructure.power.export_active", "infrastructure.power.import_active"]
UNSUPPORTED = ["role_inference", "direction_split_without_a_stated_sign", "mixed_sign_references", "meter_identity", "connection_readiness_breaker_fault_interlock_state", "gateway_runtime_state_as_electrical_state", "write_operations", "acknowledgement", "readback", "retry", "control_routes"]
SIGN_REFERENCES = {"positive_export", "positive_import", "not_stated"}
DOC_TOKENS = ("gateway-configured", "unknown, never zero", "no binary floating point", "outbound_allowed=false", "one atomic cutover", "role is configuration", "no meter register is decoded")


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


def pack_catalog():
    catalog = json.loads(PACK_CATALOG.read_text(encoding="utf-8"))["catalog"]["definitions"]
    return {field["id"]: field for field in catalog["fields"]}, {dimension["id"] for dimension in catalog["fact_dimensions"]}, {rel["id"] for rel in catalog["relationships"]}


def validate_contract(document):
    fields, dimensions, relationships = pack_catalog()
    if document.get("contract") != "helianthus.semantic.mapping.huawei-gateway-meter.infrastructure/v1" or document.get("mapping_id") != "infrastructure.mapping.huawei.gateway_meter" or document.get("pack") != PACK or document.get("status") != "accepted_withheld_mapping_gate_no_meter_decoded":
        fail("contract")
    if document.get("evidence") != EVIDENCE or not LOCAL_ASSESSMENT.is_file():
        fail("evidence")
    if document.get("admission") != ADMISSION:
        fail("admission")
    role = document.get("role")
    if role != ROLE:
        fail("role")
    for entry in ROLE["dimension_by_role"].values():
        if entry["power"] != "withheld" and entry["power"] not in dimensions or entry["energy"] not in dimensions or (entry["relationship"] != "none_decided" and entry["relationship"] not in relationships):
            fail("role dimensions")
    rules = document.get("field_rules", [])
    if [(rule.get("native_id"), rule.get("gateway_path")) for rule in rules] != INVENTORY:
        fail("native inventory")
    reasons = document.get("reasons", {})
    for name, spec in reasons.items():
        if not name.startswith("infrastructure.reason.") or spec.get("loss_kind") not in LOSS_KINDS or not spec.get("description") or type(spec.get("reversible")) is not bool:
            fail("reason loss")
    used, targets = set(), set()
    for rule in rules:
        disposition = rule.get("disposition", {})
        if set(disposition) != {"outcome", "reason"} or disposition["outcome"] != "withheld" or disposition["reason"] not in reasons or rule.get("grade") not in GRADES:
            fail("withheld reason")
        used.add(disposition["reason"])
        for row in rule.get("prospective", []):
            pack_field = fields.get(row.get("target"))
            native = row.get("native")
            if row.get("in_force") is not False or pack_field is None or row.get("dimension") != pack_field["dimension"] or row.get("unit") != pack_field.get("unit") or UNIT_SHIFT.get(((native or {}).get("unit"), row.get("unit"))) is None:
                fail("prospective target")
            if row["dimension"] == "infrastructure.dimension.grid_connection" and row.get("role") != "grid_connection":
                fail("prospective role")
            if row["target"].startswith("infrastructure.power.") and row.get("sign_reference") not in SIGN_REFERENCES:
                fail("prospective sign")
            if row["target"].startswith("infrastructure.energy.") and (row.get("direction") not in ("stated", "not_stated") or row.get("counter") != "reset_wrap_and_continuity_never_inferred"):
                fail("prospective counter")
            targets.add(row["target"])
    if not targets <= set(REQUESTED) or document.get("projection", {}).get("requested_items") != [{"kind": "fact", "item_id": item} for item in REQUESTED] or any(item not in fields for item in REQUESTED):
        fail("requested items")
    if set(reasons) != used | RUNTIME_REASONS | {PRIMARY_REASON}:
        fail("reason inventory")
    identity = document.get("identity", {})
    if identity != {"source_id": {"source": "gateway_configured_semantic_source_id", "required": True, "non_secret": True, "forbidden_derivations": FORBIDDEN_DERIVATIONS},
                    "meter_asset_id": "none_exists_until_a_meter_class_contract_gives_an_identity", "failure": "missing_or_invalid_source_identity_fails_closed"}:
        fail("identity contract")
    if document.get("lifecycle") != {
        "required_observation_evidence": ["observation_id", "observation_revision", "receipt_wall", "receipt_monotonic", "clock_epoch", "source_epoch", "driver_generation", "connection_generation", "selection", "role", "reads"],
        "absent_optional_group": "unknown_never_zero", "exception": "no_negation_of_the_gateway_or_an_identified_inverter", "withdrawal": "explicit_generation_fenced"}:
        fail("lifecycle contract")
    if document.get("outcome_vocabulary") != {"exact": "exact", "transformed": "transformed", "withheld": "withheld", "native_only": "unrepresentable"}:
        fail("outcome vocabulary")
    if document.get("unsupported") != UNSUPPORTED:
        fail("unsupported")
    projection = document.get("projection", {})
    if projection.get("primary_reason") != PRIMARY_REASON or projection.get("error_precedence") != ERROR_PRECEDENCE or projection.get("operations") != "unsupported_no_authority" or projection.get("missing_native") != "unavailable_withheld_never_zero" or projection.get("target") != "SemReg_infrastructure_projection":
        fail("projection")
    if document.get("consumer_cutover") != {"consumers": ["semantic_mcp", "graphql", "portal", "home_assistant"], "path": "shared_semantic_snapshot_only", "until_implemented": "no_public_consumer_binding"}:
        fail("consumer cutover")
    if contains_float(document):
        fail("binary floating point")


def validate_case(case, contract):
    if not isinstance(case, dict):
        fail("native_evidence_invalid")
    selection = case.get("selection")
    outcome = selection.get("outcome") if isinstance(selection, dict) else None
    if outcome == "PROFILE_SELECTED" or "asset_id" in (case.get("identity") if isinstance(case.get("identity"), dict) else {}):
        fail("gate_revision_required")
    errors = set()
    if outcome not in ADMISSION["selection_outcomes_allowed"] or contains_float(case):
        errors.add("native_evidence_invalid")
    reads = {}
    for read in case.get("reads") if isinstance(case.get("reads"), list) else [None]:
        key = read.get("native_id") if isinstance(read, dict) else None
        if key not in FEEDABLE or key in reads or read.get("outcome") not in ("ANSWERED", "EXCEPTION", "FAILED", "NOT_READ") or set(read) - {"native_id", "outcome", "exception_code"}:
            errors.add("native_evidence_invalid")
            continue
        code = read.get("exception_code")
        if (read["outcome"] == "EXCEPTION") != (type(code) is int and code >= 1):
            errors.add("native_evidence_invalid")
        reads[key] = read
    source = case.get("source")
    source_id = source.get("source_id") if isinstance(source, dict) else None
    unit = case.get("routed_unit")
    if not isinstance(source_id, str) or not OPAQUE_RE.fullmatch(source_id) or any(token in source_id.lower() for token in ID_FORBIDDEN_TEXT) or ID_ADDRESS_RE.search(source_id) or (unit is not None and (type(unit) is not int or not 1 <= unit <= 247)) or source_id == str(unit):
        errors.add("identity_missing_or_invalid")
    role = case.get("role")
    declared = role.get("declared") if isinstance(role, dict) else None
    if not isinstance(role, dict) or role.get("source") != "operator_configuration" or (declared is not None and declared not in ROLE["values"]):
        errors.add("role_invalid")
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
    if case.get("request_operation") or case.get("request_direction_split") or case.get("request_mixed_sign_references"):
        errors.add("unsupported_or_withheld")
    for code in ERROR_PRECEDENCE:
        if code in errors:
            fail(code)
    return reads, source_id, unit, declared


def project(case, contract):
    reads, source_id, unit, declared = validate_case(case, contract)
    rows = []
    for rule in contract["field_rules"]:
        reason = rule["disposition"]["reason"]
        read = reads.get(rule["native_id"])
        if read is not None and read["outcome"] == "ANSWERED":
            reason = "infrastructure.reason.answered_not_decoded"
        elif read is not None and read["outcome"] == "EXCEPTION":
            reason = "infrastructure.reason.read_exception_no_negation"
        rows.append({"native_id": rule["native_id"], "outcome": "withheld", "reason": reason})
    spec = contract["reasons"][PRIMARY_REASON]
    dispositions = [{"kind": "fact", "item_id": item["item_id"], "outcome": "withheld", "source_keys": [], "reason": PRIMARY_REASON,
                     "loss": [{"kind": spec["loss_kind"], "source_items": [NATIVE_PREFIX + "meter"], "description": spec["description"], "reversible": spec["reversible"]}]} for item in contract["projection"]["requested_items"]]
    dimensions = contract["role"]["dimension_by_role"].get(declared) if declared else None
    role = {"declared": declared, "keyed_to": {"source_id": source_id, "routed_unit": unit}, "dimension_if_admitted": copy.deepcopy(dimensions) if dimensions else "role_unknown_role_dependent_facts_not_published"}
    output = {"facts": [], "relationships": [], "requested": copy.deepcopy(contract["projection"]["requested_items"]), "dispositions": dispositions, "native_dispositions": rows, "role": role, "operations": []}
    assert_complete(output, contract)
    return output


def assert_complete(output, contract):
    """Every native item carries exactly one disposition, a reason, and no value."""
    if [row["native_id"] for row in output["native_dispositions"]] != [nid for nid, _ in INVENTORY] or output["facts"] or output["relationships"]:
        fail("native disposition completeness")
    if any(row["outcome"] != "withheld" or row["reason"] not in contract["reasons"] for row in output["native_dispositions"]):
        fail("withheld without reason")


def summarize(output):
    return {"facts": output["facts"], "dispositions": [{"item_id": item["item_id"], "outcome": item["outcome"], "published": len(item["source_keys"]), "reason": item["reason"], "loss": [loss["kind"] for loss in item["loss"]]} for item in output["dispositions"]],
            "native_dispositions": output["native_dispositions"], "role": output["role"], "operations": output["operations"]}


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
    return "%s, %s, gain %d" % (native["type"], native["unit"], native["gain"])


def expected_tables(contract):
    withheld, prospective = [], []
    for rule in contract["field_rules"]:
        reason = rule["disposition"]["reason"]
        withheld.append([rule["native_id"], rule["gateway_path"], rule["grade"].capitalize(), reason, contract["reasons"][reason]["loss_kind"]])
        for row in rule.get("prospective", []):
            rule_text = row.get("sign_reference") or ("direction %s; %s" % (row["direction"], row["counter"]) if "direction" in row else "none")
            prospective.append([row["target"], row["dimension"], rule["native_id"], native_form(row["native"]), rule_text, row.get("role", "any role")])
    return withheld, prospective


def check_document(contract, text):
    withheld, prospective = expected_tables(contract)
    roles = [[role, entry["power"], entry["energy"], entry["relationship"].replace("none_decided", "none decided")] for role, entry in contract["role"]["dimension_by_role"].items()] + [["undeclared", "withheld", "withheld", "none"]]
    if table(text, "## Withheld items") != withheld or table(text, "## Prospective intake") != prospective or table(text, "## Role and dimension") != roles:
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
    print(f"Huawei gateway-meter infrastructure mapping: PASS; {positives} executable outputs and {len(contract['scenarios']) - positives} rejected scenarios")


if __name__ == "__main__":
    main()
