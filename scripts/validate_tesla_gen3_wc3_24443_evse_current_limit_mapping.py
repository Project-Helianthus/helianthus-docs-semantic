#!/usr/bin/env python3
"""Execute the source-specific Tesla Gen3 WC3 current-limit mapping gate."""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "api/v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.json"
DOC = ROOT / "api/v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md"
PACK = {"id": "helianthus.pack.evse", "version": "1.0.0"}
PINS = {"docs_semantic_base": "f830ace6c2b9dd1af0e87ce808fa545662578418", "semreg": "f3f761bc67e10d6a65eba6c13cb4dc51002d6955", "docs_modbus_current_limit": "6611e20ac8b2c3e8b953934757346f8a847b30bf", "docs_modbus_native_projection": "1127c333de1f1d02305952a58f8745ee05c42e12", "modbusreg": "57f7eb84f7d4e1173621711bf64624726c71bc75", "gateway_main": "32244901c4c8337266cd348bdad90fb9e8eb0a61"}
ERRORS = ["profile_or_version_invalid", "identity_invalid", "source_path_invalid", "evidence_binding_invalid", "lifecycle_invalid", "unsupported_fact_or_operation"]
OPAQUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
PERSISTENT_REFS = ["persistent_request", "persistent_terminal"]
PROVISIONAL_REFS = ["provisional_set", "provisional_ack", "provisional_readback_request", "provisional_readback_terminal"]


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def fail(code):
    raise ValueError(code)


def mutate(value, mutation):
    parts = mutation["path"].split(".")
    current = value
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current.setdefault(part, {})
    key = int(parts[-1]) if isinstance(current, list) else parts[-1]
    if mutation.get("op") == "delete":
        current.pop(key)
    else:
        current[key] = mutation["value"]


def validate_contract(contract):
    if contract.get("contract") != "helianthus.semantic.mapping.tesla-gen3-wc3-24443.evse-current-limit/v1" or contract.get("pack") != PACK or contract.get("pins") != PINS:
        fail("contract")
    native = contract.get("native_contract")
    if native != {"profile": "wc3_24_44_3", "source_path": "modbus.v1.tesla.gen3.evse.current_limit.get", "function": "FC100", "read_only": True, "outbound_allowed": False, "persistent": {"request_response": "family_6.t7_to_t8", "field": "MaxOutputCurrentAmps", "unit": "unit.ampere"}, "provisional": {"set_ack": "family_6.t25_to_t26", "readback": "family_6.t27_to_t28", "field": "LimitCurrentMaxAmps", "timeout": "LimitTimeoutSeconds", "inhibit": "InhibitCharging", "unit": "unit.ampere"}}:
        fail("native_contract")
    identity = contract.get("identity", {})
    if set(identity) != {"asset_id", "evse_id", "connector_id", "forbidden_derivations", "failure"} or identity.get("forbidden_derivations") != ["unit_id", "firmware_text", "observation_values", "payload_bytes", "request_order"] or identity.get("failure") != "missing_blank_invalid_reused_or_ambiguous_identity_fails_closed" or any(identity.get(k) != {"source": f"gateway_configured_semantic_{k}", "required": True, "non_secret": True} for k in ("asset_id", "evse_id", "connector_id")):
        fail("identity_contract")
    lifecycle = contract.get("lifecycle", {})
    if lifecycle != {"required": ["receipt_timestamp", "source_epoch", "driver_generation", "qualification", "semantic_revision", "lifecycle_generation"], "per_fact_evidence": {"persistent": ["immutable_evidence_id", "payload_digest", "persistent_request", "persistent_terminal"], "provisional": ["immutable_evidence_id", "payload_digest", "correlation_id", "provisional_set", "provisional_ack", "provisional_readback_request", "provisional_readback_terminal"]}, "atomicity": "persistent_and_provisional_each_have_one_evidence_id_one_source_epoch_one_driver_generation_one_semantic_revision", "withdrawal": "explicit_generation_fenced", "retention": "native_owner_only_permitted_last_known_good", "physical_qualified": False, "mapping_qualified": True}:
        fail("lifecycle_contract")
    if contract.get("field_rules") != [{"source": "persistent.MaxOutputCurrentAmps", "target": "evse.limit.configured_current", "dimension": "evse", "unit": "unit.ampere", "disposition": "exact"}, {"source": "provisional.LimitCurrentMaxAmps", "target": "evse.limit.allocated_current", "dimension": "connector", "unit": "unit.ampere", "disposition": "exact_when_finite_timeout_and_not_inhibited"}]:
        fail("field_rules")
    if len(contract.get("withheld", [])) != 3 or contract.get("unsupported") != ["power", "energy", "phase", "session", "readiness", "connector_topology", "state_of_charge", "thermal", "fault", "interlock", "meter", "set_allocated_current", "sender", "route", "authority", "acknowledgement_authority", "readback_authority", "retry", "live_control"]:
        fail("withheld_or_unsupported")
    projection = contract.get("projection", {})
    if projection.get("source_path") != "modbus.v1.tesla.gen3.evse.current_limit.get" or projection.get("error_precedence") != ERRORS or projection.get("operations") != "all_unavailable_no_authority" or projection.get("missing_native") != "withheld_unavailable_never_zero":
        fail("projection")
    cutover = contract.get("consumer_cutover", {})
    if cutover != {"sequence": ["one_semreg_projection", "versioned_semantic_mcp", "mtls_graphql_and_portal_parity", "home_assistant_adoption"], "forbidden": ["fallback", "comparator", "compatibility_adapter", "shadow_authority", "dual_publication", "caller_supplied_provenance", "write_route"], "until_implemented": "no_consumer_binding"}:
        fail("consumer_cutover")


def valid_id(value):
    return isinstance(value, str) and bool(OPAQUE.fullmatch(value))


def valid_evidence(evidence, refs, correlation=False):
    if not isinstance(evidence, dict) or not valid_id(evidence.get("immutable_evidence_id")) or not DIGEST.fullmatch(str(evidence.get("payload_digest"))) or any(not DIGEST.fullmatch(str(evidence.get(key))) for key in refs):
        return False
    return not correlation or evidence.get("correlation_id") == evidence["immutable_evidence_id"]


def project(case, contract):
    errors = set()
    if case.get("profile") != "wc3_24_44_3": errors.add(ERRORS[0])
    identity = case.get("identity", {})
    values = [identity.get(k) for k in ("asset_id", "evse_id", "connector_id")]
    if not all(valid_id(v) for v in values) or len(set(values)) != 3: errors.add(ERRORS[1])
    if case.get("source_path") != contract["projection"]["source_path"]: errors.add(ERRORS[2])
    evidence = case.get("evidence", {})
    if not valid_evidence(evidence.get("persistent"), PERSISTENT_REFS): errors.add(ERRORS[3])
    lifecycle = case.get("lifecycle", {})
    try:
        receipt = datetime.fromisoformat(str(lifecycle.get("receipt_timestamp")).replace("Z", "+00:00"))
        receipt_ok = receipt.tzinfo is not None
    except ValueError:
        receipt_ok = False
    if not receipt_ok or not valid_id(lifecycle.get("source_epoch")) or lifecycle.get("qualification") != "qualified" or lifecycle.get("semantic_revision") != "1.0.0" or any(not isinstance(lifecycle.get(k), int) or isinstance(lifecycle.get(k), bool) or lifecycle[k] < 1 for k in ("driver_generation", "lifecycle_generation")): errors.add(ERRORS[4])
    if case.get("unsupported_fact") or case.get("operation"): errors.add(ERRORS[5])
    for error in ERRORS:
        if error in errors: fail(error)
    persistent, provisional = case.get("persistent"), case.get("provisional")
    if not isinstance(persistent, dict) or not isinstance(persistent.get("MaxOutputCurrentAmps"), int) or isinstance(persistent["MaxOutputCurrentAmps"], bool) or persistent["MaxOutputCurrentAmps"] < 0: fail(ERRORS[3])
    facts = [{"id": "evse.limit.configured_current", "dimension": "evse", "value": {"coefficient": str(persistent["MaxOutputCurrentAmps"]), "exponent10": 0}, "unit": "unit.ampere"}]
    withheld = []
    if not isinstance(provisional, dict):
        withheld.append({"id": "evse.limit.allocated_current", "reason": "provisional_record_absent"})
    elif not valid_evidence(evidence.get("provisional"), PROVISIONAL_REFS, correlation=True):
        withheld.append({"id": "evse.limit.allocated_current", "reason": "provisional_evidence_invalid"})
    elif provisional.get("LimitTimeoutSeconds") == 0:
        withheld.append({"id": "evse.limit.allocated_current", "reason": "zero_timeout_unresolved"})
    elif provisional.get("InhibitCharging") is not False:
        withheld.append({"id": "evse.limit.allocated_current", "reason": "inhibit_state_not_semantically_representable"})
    elif not isinstance(provisional.get("LimitCurrentMaxAmps"), int) or isinstance(provisional["LimitCurrentMaxAmps"], bool) or not 6 <= provisional["LimitCurrentMaxAmps"] <= 1000 or not isinstance(provisional.get("LimitTimeoutSeconds"), int) or not 1 <= provisional["LimitTimeoutSeconds"] <= 86399:
        withheld.append({"id": "evse.limit.allocated_current", "reason": "provisional_record_malformed"})
    else:
        facts.append({"id": "evse.limit.allocated_current", "dimension": "connector", "value": {"coefficient": str(provisional["LimitCurrentMaxAmps"]), "exponent10": 0}, "unit": "unit.ampere"})
    return {"facts": facts, "withheld": withheld, "operations": []}


def document(contract):
    validate_contract(contract)
    scenarios = contract.get("scenarios", [])
    if not scenarios or scenarios[0].get("polarity") != "positive": fail("scenario_coverage")
    baseline = scenarios[0]["input"]
    for scenario in scenarios:
        case = copy.deepcopy(baseline)
        for mutation in scenario.get("mutations", []): mutate(case, mutation)
        if scenario["polarity"] == "positive":
            if project(case, contract) != scenario["expect"]: fail("scenario_output")
        else:
            try: project(case, contract)
            except ValueError as error:
                if str(error) != scenario.get("expect_error"): raise
            else: fail("scenario_accepted")


def main():
    contract = load(); document(contract)
    text = DOC.read_text(encoding="utf-8")
    for token in ("FC100", "outbound_allowed=false", "field-scoped immutable evidence", "Every operation is unavailable", "mTLS GraphQL"):
        if token not in text: fail("document_boundary")
    positive = sum(s["polarity"] == "positive" for s in contract["scenarios"])
    print(f"Tesla Gen3 WC3 24.44.3 EVSE current-limit mapping: PASS; {positive} executable outputs and {len(contract['scenarios']) - positive} rejected scenarios")


if __name__ == "__main__": main()
