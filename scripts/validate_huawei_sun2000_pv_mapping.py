#!/usr/bin/env python3
"""Execute the Huawei SUN2000 PV mapping gate: admitted monitoring facts to helianthus.pack.pv@1.0.0."""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "api/v1/mappings/huawei-sun2000-pv-v1.json"
DOC = ROOT / "api/v1/mappings/huawei-sun2000-pv-v1.md"
PACK_CATALOG = ROOT / "api/v1/packs/pv-inverter-acceptance-vectors.json"

PACK = {"id": "helianthus.pack.pv", "version": "1.0.0"}
M3 = "huawei.sun2000.m3.monitoring-readonly@1.0.0"
M1 = "huawei.sun2000.m1.monitoring-readonly@1.0.0"
NATIVE_PREFIX = "native.huawei.sun2000."
LOSS_KINDS = {"unit", "range", "precision", "time", "symbol", "provenance", "identity", "capability", "operation", "policy"}
OUTCOMES = {"exact", "transformed", "withheld", "native_only"}
GRADES = ["unknown", "hypothesis", "proven"]
ERROR_PRECEDENCE = ["profile_not_selected", "native_evidence_invalid", "identity_missing_or_invalid", "lifecycle_missing", "mapping_unqualified", "unsupported_or_withheld"]
OPAQUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")
COEFFICIENT_RE = re.compile(r"^(0|-?[1-9][0-9]*)$")
HEX_RUN_RE = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")
ID_FORBIDDEN_TEXT = ("serial", "esn", "sun2000", "huawei", "luna", "smartlogger", "sdongle", "s-dongle", "emma")
ID_ADDRESS_RE = re.compile(r"(\d{1,3}\.){3}\d{1,3}|:\d{3,5}$")
WORD_TYPES = {"I16": (1, True), "U16": (1, False), "I32": (2, True), "U32": (2, False)}
GAIN_EXPONENT = {1: 0, 10: -1, 100: -2, 1000: -3}
UNIT_SHIFT = {("V", "unit.volt"): 0, ("A", "unit.ampere"): 0, ("kW", "unit.watt"): 3, ("kWh", "unit.kilowatt_hour"): 0}
FORBIDDEN_DERIVATIONS = ["serial_number", "esn", "vendor", "model", "firmware_or_version", "routed_unit_alone", "endpoint_address"]
EDITION = {"title": "SUN2000MC V200R023C00 Modbus Interface Definitions", "issue": "Issue 01", "date": "2023-03-17", "use": "identity_only_inspection_only_never_quoted"}
REGISTRY_FLAGS = {"catalog_registered": False, "automatic_runtime_admission": False, "live_qualified": False, "support_claim": False, "write_authority": False}
QUALIFICATION = {**REGISTRY_FLAGS, "mapping_qualified": True, "outbound_allowed": False}
EVIDENCE = {
    "monitoring_contract": {"repository": "helianthus-docs-modbus", "issue": 242, "pull_request": 253, "pages": ["protocols/huawei/monitoring-readonly-v1.md", "protocols/huawei/read-pacing-v1.md"]},
    "registry_profiles": {"repository": "helianthus-modbusreg", "issue": 348, "pull_request": 357},
    "program_issues": {"repository": "helianthus-modbusreg", "issues": [199, 201]},
    "multi_endpoint_contract": {"repository": "helianthus-docs-ebus", "issue": 746, "pull_request": 748},
    "grades": ["proven", "hypothesis", "unknown"],
}
_COMMON = [("status_group_words", "retained_native"), ("string_group_tail_words", "retained_native")]
PROFILE_FIELDS = {
    M3: [("pv_string_voltage", "admitted"), ("pv_string_current", "admitted"), ("input_power", "refused_group"), ("active_power", "refused_group"), ("device_status", "refused_group"),
         ("energy_accumulated", "admitted"), ("energy_current_hour", "admitted"), ("energy_current_day", "admitted")] + _COMMON
        + [("dc_input_energy_counter", "retained_native"), ("statistics_time_words", "retained_native"), ("battery", "withheld_group"), ("meter", "withheld_group")],
    M1: [("pv_string_voltage", "admitted"), ("pv_string_current", "admitted"), ("input_power", "admitted"), ("active_power", "admitted"), ("device_status", "admitted"),
         ("energy_accumulated", "admitted"), ("energy_current_hour", "admitted"), ("energy_current_day", "admitted")] + _COMMON
        + [("power_group_other_words", "retained_native"), ("dc_input_energy_counter", "retained_native"), ("statistics_time_words", "retained_native"), ("battery", "withheld_group"), ("meter", "withheld_group")],
}
FACT_COUNT = {M3: 19, M1: 22}
READ_PLAN = {
    M3: [(32000, 16, "retained_no_facts"), (32016, 24, "consumed"), (32106, 10, "consumed")],
    M1: [(32000, 16, "retained_no_facts"), (32016, 24, "consumed"), (32064, 32, "consumed"), (32106, 10, "consumed")],
}
REFUSED = {M3: [(32064, 32, 3), (37100, 38, 3)], M1: []}
RUNTIME_REASONS = {"pv.reason.native_fact_unknown", "pv.reason.value_outside_pack_range", "pv.reason.input_presence_unknown", "pv.reason.negative_active_power_sign_unknown", "pv.reason.state_code_not_observed", "pv.reason.power_group_refused"}
UNSUPPORTED = ["per_phase_values", "array_or_string_topology", "tracker_pairing", "plant_or_site_aggregate", "planned_plant_groups", "derived_energy", "active_power_limit", "export_power_limit", "enable_disable", "write_operations", "acknowledgement", "readback", "retry", "control_routes"]
REQUESTED = ["pv.ac.aggregate_active_power", "pv.dc.aggregate_power", "pv.dc.current", "pv.dc.voltage", "pv.energy.generated", "pv.status.operating"]
DIMENSION_TEXT = {"asset_suffix": {"strip_prefix": "pv-asset-"}, "pv.dimension.system": "system:{asset_suffix}", "pv.dimension.inverter": "inverter:{asset_suffix}", "pv.dimension.input": "input:{n}", "pv.dimension.phase": None}
DOC_TOKENS = ("gateway-configured", "no binary floating point", "no derived energy", "unknown is never zero", "outbound_allowed=false", "one atomic cutover", "proven only where the monitoring contract is proven")


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
    return {field["id"]: field for field in catalog["fields"]}, {rel["id"]: rel for rel in catalog["relationships"]}, {dim["id"] for dim in catalog["fact_dimensions"]}


def decimal_of(number):
    with localcontext() as context:
        context.prec = 60
        return Decimal(int(number["coefficient"])).scaleb(number["exponent10"])


def decode(words, native_type):
    count, signed = WORD_TYPES[native_type]
    if not isinstance(words, list) or len(words) != count or any(type(word) is not int or not 0 <= word <= 0xFFFF for word in words):
        fail("native_evidence_invalid")
    raw = 0
    for word in words:
        raw = (raw << 16) | word
    if signed and raw >= 1 << (16 * count - 1):
        raw -= 1 << (16 * count)
    return raw


def canonical(coefficient, exponent):
    if coefficient == 0:
        return {"coefficient": "0", "exponent10": 0}
    while coefficient % 10 == 0:
        coefficient //= 10
        exponent += 1
    if not -18 <= exponent <= 18:
        fail("native_evidence_invalid")
    return {"coefficient": str(coefficient), "exponent10": exponent}


def grade_min(left, right):
    return GRADES[min(GRADES.index(left), GRADES.index(right))]


def validate_contract(document):
    fields, relationships, dimensions = pack_catalog()
    if document.get("contract") != "helianthus.semantic.mapping.huawei-sun2000.pv/v1" or document.get("mapping_id") != "pv.mapping.huawei.sun2000.monitoring" or document.get("pack") != PACK or document.get("status") != "accepted_source_specific_read_only_mapping_gate":
        fail("contract")
    if document.get("evidence") != EVIDENCE:
        fail("evidence")
    native = document.get("native_contract", {})
    if native.get("function") != "FC03" or native.get("read_only") is not True or native.get("outbound_allowed") is not False or native.get("word_order") != "big_endian_most_significant_word_first" or native.get("value") != "twos_complement_integer_over_gain" or native.get("registry_flags") != REGISTRY_FLAGS or native.get("selection_outcomes") != ["PROFILE_SELECTED", "INSUFFICIENT_EVIDENCE", "NO_ADMISSIBLE_PROFILE", "AMBIGUOUS"]:
        fail("native contract")
    if native.get("edition") != EDITION:
        fail("edition")
    if native.get("unmapped_families") != [{"family": "SUN2000 MAP0 series", "gateway_path": "EMMA", "outcome": "NO_ADMISSIBLE_PROFILE", "reason": "no_consulted_edition", "fields": []}]:
        fail("unmapped family")
    profiles = native.get("profiles", [])
    if [profile.get("profile_id") for profile in profiles] != [M3, M1]:
        fail("profiles")
    rules = document.get("field_rules", [])
    rule_ids = [rule.get("native_id") for rule in rules]
    if len(rule_ids) != len(set(rule_ids)):
        fail("duplicate disposition")
    for profile in profiles:
        pid = profile["profile_id"]
        listed = [(row.get("native_id"), row.get("state")) for row in profile.get("fields", [])]
        if listed != PROFILE_FIELDS[pid]:
            fail("profile field inventory")
        if profile.get("fact_count") != FACT_COUNT[pid] or [(g.get("offset"), g.get("quantity"), g.get("use")) for g in profile.get("read_plan", [])] != READ_PLAN[pid] or [(g.get("offset"), g.get("quantity"), g.get("exception")) for g in profile.get("refused_groups", [])] != REFUSED[pid]:
            fail("profile read plan")
        for nid, state in PROFILE_FIELDS[pid]:
            if nid not in rule_ids:
                fail("missing disposition")
        counts = {rule["native_id"]: (rule.get("native") or {}).get("count") for rule in rules}
        if sum(counts[nid] or 0 for nid, state in PROFILE_FIELDS[pid] if state == "admitted") != FACT_COUNT[pid]:
            fail("profile fact count")
    if set(rule_ids) != {nid for fields_ in PROFILE_FIELDS.values() for nid, _ in fields_}:
        fail("disposition without native field")
    reasons = document.get("reasons", {})
    for name, spec in reasons.items():
        if not name.startswith("pv.reason.") or spec.get("loss_kind") not in LOSS_KINDS or not spec.get("description") or type(spec.get("reversible")) is not bool:
            fail("reason loss")
    used = set()
    targets = []
    for rule in rules:
        disposition = rule.get("disposition", {})
        outcome = disposition.get("outcome")
        if outcome not in OUTCOMES or set(rule.get("grade_ceiling", {})) != {"m3", "m1"} or any(value not in GRADES for value in rule["grade_ceiling"].values()):
            fail("disposition")
        if outcome in ("withheld", "native_only"):
            if disposition.get("reason") not in reasons or "loss" in disposition or rule.get("target"):
                fail("withheld reason")
            used.add(disposition["reason"])
            for target in rule.get("prospective_targets", []):
                if target not in fields:
                    fail("prospective target")
            continue
        target = rule.get("target")
        pack_field = fields.get(target)
        losses = disposition.get("loss")
        if pack_field is None or rule.get("requested") != {"kind": "fact", "item_id": target} or rule.get("dimension") != pack_field["dimension"] or rule.get("unit") != pack_field.get("unit"):
            fail("target definition")
        if rule.get("dimension_text") != DIMENSION_TEXT[rule["dimension"]]:
            fail("dimension text")
        spec = rule.get("native", {})
        words, signed = WORD_TYPES.get(spec.get("type"), (None, None))
        if spec.get("words") != words or spec.get("gain") not in GAIN_EXPONENT or type(spec.get("count")) is not int or spec.get("group_offset") not in (32016, 32064, 32106):
            fail("native form")
        if outcome == "exact" and losses != []:
            fail("exact loss")
        if outcome == "transformed":
            if not losses or any(loss.get("kind") not in LOSS_KINDS or loss.get("source_items") != [NATIVE_PREFIX + rule["native_id"]] or not loss.get("description") or type(loss.get("reversible")) is not bool for loss in losses):
                fail("transformed loss")
        shift = rule.get("exponent10_shift")
        if target == "pv.status.operating":
            if rule.get("symbols") != {"grid_connected": "generating"} or "pv.status.operating." + rule["symbols"]["grid_connected"] not in fields[target]["symbols"] or spec.get("unit") != "" or rule.get("unit") is not None:
                fail("status symbols")
            if "symbol" not in [loss["kind"] for loss in losses]:
                fail("status loss")
        else:
            if UNIT_SHIFT.get((spec.get("unit"), rule.get("unit"))) != shift:
                fail("unit shift")
            if shift and "unit" not in [loss["kind"] for loss in losses]:
                fail("silent unit conversion")
        if rule["native_id"] == "active_power" and (rule.get("sign") != {"native_reference": "positive_while_producing", "negative_value": "withheld"} or "provenance" not in [loss["kind"] for loss in losses]):
            fail("sign convention")
        if rule["native_id"] == "energy_accumulated" and "policy" not in [loss["kind"] for loss in losses]:
            fail("counter policy loss")
        targets.append(target)
    if sorted(targets) != REQUESTED or document.get("projection", {}).get("requested_items") != [{"kind": "fact", "item_id": item} for item in REQUESTED]:
        fail("requested items")
    if set(reasons) != used | RUNTIME_REASONS:
        fail("reason inventory")
    for rule in rules:
        if rule.get("native_id") in ("pv_string_voltage", "pv_string_current") and rule["grade_ceiling"]["m1"] != "proven":
            fail("grade ceiling")
    identity = document.get("identity", {})
    for key, granularity in (("asset_id", "one_asset_per_admitted_inverter_child_within_an_endpoint_instance"), ("source_id", "one_source_per_endpoint_instance")):
        entry = identity.get(key, {})
        if entry.get("required") is not True or entry.get("non_secret") is not True or entry.get("granularity") != granularity or entry.get("forbidden_derivations") != FORBIDDEN_DERIVATIONS:
            fail("identity contract")
    if identity.get("source_id", {}).get("distinct_from") != "asset_id" or identity.get("failure") != "missing_or_invalid_asset_or_source_identity_fails_closed":
        fail("identity contract")
    if identity.get("binding_id") != {"source": "gateway_domain_separated_asset_source_profile_binding", "required": True, "non_secret": True, "stable_inputs": ["asset_id", "source_id", "profile_id"]}:
        fail("identity contract")
    if identity.get("dimension_text") != DIMENSION_TEXT or identity.get("relationships") != ["pv.relationship.system_inverter", "pv.relationship.inverter_input"] or any(name not in relationships for name in identity["relationships"]):
        fail("identity contract")
    if document.get("lifecycle") != {
        "required_observation_evidence": ["observation_id", "observation_revision", "receipt_wall", "receipt_monotonic", "clock_epoch", "source_epoch", "driver_generation", "connection_generation", "profile_selection", "groups", "facts"],
        "freshness": "native_receipt_axes_preserved", "device_time": "statistics_time_words_never_used",
        "retention": "last_complete_group_reading_keeps_its_original_observation", "retention_fence": "never_across_profile_unit_or_connection_identity",
        "withdrawal": "explicit_generation_fenced", "qualification": "mapping_qualified_offline_profile_and_live_unqualified"}:
        fail("lifecycle contract")
    if document.get("decimal_policy") != {"form": "kernel_decimal_coefficient_exponent10", "exponent10_range": [-18, 18], "zero": "coefficient_0_exponent10_0", "trailing_zero": "moves_to_exponent10", "binary_floating_point": "forbidden", "derived_energy": "forbidden"}:
        fail("decimal policy")
    if document.get("counter_policy") != {"fact": "pv.energy.generated", "source": "energy_accumulated", "decrease": "never_inferred_as_reset_or_wrap", "continuity": "native_evidence_required", "delta_or_period_energy": "not_published", "sum_across_inverters": "forbidden"}:
        fail("counter policy")
    if document.get("outcome_vocabulary") != {"exact": "exact", "transformed": "transformed", "withheld": "withheld", "native_only": "unrepresentable"}:
        fail("outcome vocabulary")
    if document.get("unsupported") != UNSUPPORTED:
        fail("unsupported")
    projection = document.get("projection", {})
    if projection.get("error_precedence") != ERROR_PRECEDENCE or projection.get("operations") != "unsupported_no_authority" or projection.get("missing_native") != "unavailable_withheld_never_zero" or projection.get("target") != "SemReg_pv_projection":
        fail("projection")
    if document.get("consumer_cutover") != {"consumers": ["semantic_mcp", "graphql", "portal", "home_assistant"], "path": "shared_semantic_snapshot_only", "until_implemented": "no_public_consumer_binding"}:
        fail("consumer cutover")
    if contains_float(document):
        fail("binary floating point")


def expected_facts(profile, rules):
    expected = []
    for nid, state in PROFILE_FIELDS[profile["profile_id"]]:
        if state == "admitted":
            count = rules[nid]["native"]["count"]
            expected += [(nid, n) for n in (range(1, count + 1) if count > 1 else [0])]
    return expected


def validate_case(case, contract):
    if not isinstance(case, dict):
        fail("native_evidence_invalid")
    profiles = {profile["profile_id"]: profile for profile in contract["native_contract"]["profiles"]}
    selection = case.get("selection")
    unit = selection.get("routed_unit") if isinstance(selection, dict) else None
    if not isinstance(selection, dict) or selection.get("outcome") != "PROFILE_SELECTED" or selection.get("profile_id") not in profiles or type(unit) is not int or not 1 <= unit <= 247:
        fail("profile_not_selected")
    profile = profiles[selection["profile_id"]]
    rules = {rule["native_id"]: rule for rule in contract["field_rules"]}
    life = case.get("lifecycle") if isinstance(case.get("lifecycle"), dict) else {}
    errors = set()
    if contains_float(case):
        errors.add("native_evidence_invalid")
    groups = {}
    plan = {(g["offset"], g["quantity"]) for g in profile["read_plan"]}
    refused = {(g["offset"], g["quantity"]) for g in profile["refused_groups"]}
    for group in case.get("groups") if isinstance(case.get("groups"), list) else [None]:
        key = (group.get("offset"), group.get("quantity")) if isinstance(group, dict) else None
        if key not in plan | refused or key in groups or group.get("outcome") not in ("ANSWERED", "EXCEPTION", "FAILED", "NOT_READ"):
            errors.add("native_evidence_invalid")
            continue
        code = group.get("exception_code")
        if (group["outcome"] == "EXCEPTION") != (type(code) is int and code >= 1) or (key in refused and (group["outcome"] != "EXCEPTION" or code != 3)):
            errors.add("native_evidence_invalid")
        groups[key] = group["outcome"]
    if not plan <= set(groups):
        errors.add("native_evidence_invalid")
    facts = {}
    listed = case.get("facts") if isinstance(case.get("facts"), list) else []
    for fact in listed:
        if not isinstance(fact, dict) or (fact.get("key"), fact.get("index")) in facts:
            errors.add("native_evidence_invalid")
            continue
        facts[(fact.get("key"), fact.get("index"))] = fact
    wanted = expected_facts(profile, rules)
    if sorted(facts, key=str) != sorted(wanted, key=str) or len(listed) != FACT_COUNT[profile["profile_id"]]:
        errors.add("native_evidence_invalid")
    for (nid, index), fact in facts.items():
        if (nid, index) not in wanted:
            continue
        try:
            check_fact(fact, rules[nid], groups, life, selection)
        except ValueError:
            errors.add("native_evidence_invalid")
    identity, source = case.get("identity"), case.get("source")
    asset = identity.get("asset_id") if isinstance(identity, dict) else None
    binding = identity.get("binding_id") if isinstance(identity, dict) else None
    source_id = source.get("source_id") if isinstance(source, dict) else None
    values = (asset, binding, source_id)
    if any(not isinstance(item, str) or not OPAQUE_RE.fullmatch(item) or any(token in item.lower() for token in ID_FORBIDDEN_TEXT) or ID_ADDRESS_RE.search(item) or item == str(unit) for item in values) or len(set(values)) != 3:
        errors.add("identity_missing_or_invalid")
    for fact in case.get("facts") or []:
        origin = fact.get("retained") and fact.get("origin") if isinstance(fact, dict) else None
        if isinstance(origin, dict) and (origin.get("asset_id"), origin.get("binding_id"), origin.get("source_id")) != values:
            errors.add("native_evidence_invalid")
    opaque, numeric = ("observation_id", "clock_epoch", "source_epoch"), ("observation_revision", "driver_generation", "connection_generation")
    if any(not isinstance(life.get(key), str) or not OPAQUE_RE.fullmatch(life[key]) for key in opaque) or any(type(life.get(key)) is not int or life[key] < 1 for key in numeric) or type(life.get("receipt_monotonic")) is not int or life.get("receipt_monotonic", 0) < 1:
        errors.add("lifecycle_missing")
    try:
        if datetime.fromisoformat(life.get("receipt_wall", "").replace("Z", "+00:00")).tzinfo is None:
            raise ValueError
    except (AttributeError, ValueError):
        errors.add("lifecycle_missing")
    if case.get("qualification") != QUALIFICATION:
        errors.add("mapping_unqualified")
    if case.get("request_operation") or case.get("derive_energy"):
        errors.add("unsupported_or_withheld")
    for code in ERROR_PRECEDENCE:
        if code in errors:
            fail(code)
    return profile, rules, facts, groups, asset, binding, source_id, life


def check_origin(fact, life, selection):
    """A retained reading carries the receipt coordinates and lineage of the observation that produced it."""
    origin = fact.get("origin")
    keys = {"receipt_wall", "receipt_monotonic", "clock_epoch", "source_epoch", "driver_generation", "connection_generation", "profile_id", "routed_unit", "asset_id", "binding_id", "source_id"}
    if not isinstance(origin, dict) or set(origin) != keys:
        fail("retained origin")
    try:
        if datetime.fromisoformat(origin["receipt_wall"].replace("Z", "+00:00")).tzinfo is None:
            raise ValueError
    except (AttributeError, ValueError):
        fail("retained origin")
    if type(origin["receipt_monotonic"]) is not int or origin["receipt_monotonic"] < 1 or not isinstance(origin["clock_epoch"], str) or not OPAQUE_RE.fullmatch(origin["clock_epoch"]):
        fail("retained origin")
    if origin["clock_epoch"] == life.get("clock_epoch") and origin["receipt_monotonic"] >= life.get("receipt_monotonic", 0):
        fail("retained origin")
    if origin["source_epoch"] != life.get("source_epoch") or origin["driver_generation"] != life.get("driver_generation"):
        fail("retained reading crosses a source epoch or driver generation")
    if origin["connection_generation"] != life.get("connection_generation") or origin["profile_id"] != selection.get("profile_id") or origin["routed_unit"] != selection.get("routed_unit"):
        fail("retained reading crosses a connection, profile or unit identity")


def check_fact(fact, rule, groups, life, selection):
    spec = rule["native"]
    required = {"key", "index", "unit", "availability", "grade", "retained", "observation_id", "observation_revision"}
    if not required <= set(fact) or fact["unit"] != spec["unit"] or type(fact["retained"]) is not bool or fact["grade"] not in GRADES or type(fact["observation_revision"]) is not int or not isinstance(fact["observation_id"], str):
        fail("fact shape")
    group = groups.get(next((g for g in groups if g[0] == spec["group_offset"]), None))
    if fact["availability"] == "UNKNOWN":
        if set(fact) & {"value", "words", "state", "origin"} or fact["grade"] != "unknown" or fact["retained"]:
            fail("unknown fact carries a value")
        return
    if fact["availability"] != "VALUE" or fact["grade"] == "unknown":
        fail("fact availability")
    if fact["retained"]:
        if group == "ANSWERED" or fact["observation_revision"] >= life.get("observation_revision", 0) or fact["observation_id"] == life.get("observation_id"):
            fail("retained fact")
        check_origin(fact, life, selection)
    elif group != "ANSWERED" or fact["observation_id"] != life.get("observation_id") or fact["observation_revision"] != life.get("observation_revision"):
        fail("fact without an answered group")
    if rule["native_id"] == "device_status":
        if fact.get("state") not in rule.get("symbols", {}) or set(fact) & {"value", "words"}:
            fail("status state")
        return
    value = fact.get("value")
    if not isinstance(value, dict) or not isinstance(value.get("coefficient"), str) or not COEFFICIENT_RE.fullmatch(value["coefficient"]) or value.get("exponent10") != GAIN_EXPONENT[spec["gain"]]:
        fail("fact value")
    if decode(fact.get("words"), spec["type"]) != int(value["coefficient"]):
        fail("words do not equal the value")


def project(case, contract):
    profile, rules, facts, groups, asset, binding, source_id, life = validate_case(case, contract)
    catalog, _, _ = pack_catalog()
    key_of = profile["key"]
    suffix = asset[len(DIMENSION_TEXT["asset_suffix"]["strip_prefix"]):] if asset.startswith(DIMENSION_TEXT["asset_suffix"]["strip_prefix"]) else asset
    texts = {"pv.dimension.system": "system:" + suffix, "pv.dimension.inverter": "inverter:" + suffix}
    published, native_rows, sources, item_reasons = [], [], {}, {}

    def hold(rule, index, reason):
        row = {"native_id": rule["native_id"]}
        if index is not None:
            row["index"] = index
        native_rows.append({**row, "outcome": "withheld", "reason": reason})
        if rule.get("target"):
            item_reasons.setdefault(rule["target"], []).append(reason)

    for nid, state in PROFILE_FIELDS[profile["profile_id"]]:
        rule = rules[nid]
        if state == "refused_group":
            hold(rule, None, "pv.reason.power_group_refused")
            continue
        if state != "admitted" or not rule.get("target"):
            native_rows.append({"native_id": nid, "outcome": rule["disposition"]["outcome"], "reason": rule["disposition"]["reason"]})
            continue
        count = rule["native"]["count"]
        for n in range(1, count + 1) if count > 1 else [0]:
            index = n if count > 1 else None
            fact = facts[(nid, n)]
            reason, value = None, None
            if fact["availability"] != "VALUE":
                answered = groups.get((32064, 32)) == "ANSWERED"
                reason = "pv.reason.state_code_not_observed" if nid == "device_status" and answered else "pv.reason.native_fact_unknown"
            elif nid == "device_status":
                value = {"kind": "symbol", "symbol": {"namespace": rule["target"], "token": rule["symbols"][fact["state"]], "known": True}}
            else:
                raw = int(fact["value"]["coefficient"])
                if nid in ("pv_string_voltage", "pv_string_current"):
                    pair = [facts[("pv_string_voltage", n)], facts[("pv_string_current", n)]]
                    if not any(int(item["value"]["coefficient"]) for item in pair if item["availability"] == "VALUE"):
                        reason = "pv.reason.input_presence_unknown"
                if reason is None and nid == "active_power" and raw < 0:
                    reason = "pv.reason.negative_active_power_sign_unknown"
                if reason is None:
                    number = canonical(raw, fact["value"]["exponent10"] + rule["exponent10_shift"])
                    bounds = catalog[rule["target"]]["bounds"]
                    if decimal_of(bounds["minimum"]) <= decimal_of(number) <= decimal_of(bounds["maximum"]):
                        value = {"kind": "quantity", "quantity": {"number": number, "unit": rule["unit"]}}
                    else:
                        reason = "pv.reason.value_outside_pack_range"
            if reason:
                hold(rule, index, reason)
                continue
            text = "input:%d" % n if rule["dimension"] == "pv.dimension.input" else texts[rule["dimension"]]
            key = {"pack_id": PACK["id"], "pack_version": PACK["version"], "fact_id": rule["target"], "dimensions": [{"id": rule["dimension"], "value": {"kind": "text", "text": text}}]}
            origin = fact["origin"] if fact["retained"] else life
            published.append({"key": key, "value": value, "receipt_wall": origin["receipt_wall"], "receipt_monotonic": origin["receipt_monotonic"], "clock_epoch": origin["clock_epoch"],
                              "connection_generation": origin.get("connection_generation"), "source_path": {"binding_id": binding, "source_id": source_id, "source_epoch_id": origin["source_epoch"], "driver_generation": origin["driver_generation"]},
                              "observation_id": fact["observation_id"], "observation_revision": fact["observation_revision"],
                              "evidence_grade": grade_min(fact["grade"], rule["grade_ceiling"][key_of]), "retained": fact["retained"]})
            sources.setdefault(rule["target"], []).append(key)
            row = {"native_id": nid}
            if index is not None:
                row["index"] = index
            native_rows.append({**row, "outcome": rule["disposition"]["outcome"], "target": rule["target"]})
    relationships = []
    if any(item["key"]["dimensions"][0]["id"] in texts for item in published):
        relationships.append({"id": "pv.relationship.system_inverter", "from": {"id": "pv.dimension.system", "text": texts["pv.dimension.system"]}, "to": {"id": "pv.dimension.inverter", "text": texts["pv.dimension.inverter"]}})
    for n in range(1, 9):
        if any(item["key"]["dimensions"][0]["value"]["text"] == "input:%d" % n for item in published):
            relationships.append({"id": "pv.relationship.inverter_input", "from": {"id": "pv.dimension.inverter", "text": texts["pv.dimension.inverter"]}, "to": {"id": "pv.dimension.input", "text": "input:%d" % n}})
    published.sort(key=lambda item: (item["key"]["fact_id"], item["key"]["dimensions"][0]["value"]["text"]))
    dispositions = []
    for requested in contract["projection"]["requested_items"]:
        item_id = requested["item_id"]
        rule = next(r for r in contract["field_rules"] if r.get("target") == item_id)
        keys = sorted(sources.get(item_id, []), key=lambda k: k["dimensions"][0]["value"]["text"])
        if keys:
            dispositions.append({"kind": "fact", "item_id": item_id, "outcome": rule["disposition"]["outcome"], "source_keys": keys, "loss": copy.deepcopy(rule["disposition"]["loss"])})
            continue
        reason = item_reasons[item_id][0]
        spec = contract["reasons"][reason]
        dispositions.append({"kind": "fact", "item_id": item_id, "outcome": "withheld", "source_keys": [], "reason": reason,
                             "loss": [{"kind": spec["loss_kind"], "source_items": [NATIVE_PREFIX + rule["native_id"]], "description": spec["description"], "reversible": spec["reversible"]}]})
    output = {"facts": published, "relationships": relationships, "requested": copy.deepcopy(contract["projection"]["requested_items"]), "dispositions": dispositions, "native_dispositions": native_rows, "operations": []}
    assert_complete(output, profile, rules)
    return output


def assert_complete(output, profile, rules):
    """Every native field of the profile, per string index, carries exactly one disposition."""
    expected = []
    for nid, _ in PROFILE_FIELDS[profile["profile_id"]]:
        count = rules[nid]["native"]["count"] if rules[nid].get("native") else 1
        expected += [(nid, n) for n in range(1, count + 1)] if count > 1 else [(nid, None)]
    seen = [(row["native_id"], row.get("index")) for row in output["native_dispositions"]]
    if seen != expected or any(row["outcome"] not in OUTCOMES for row in output["native_dispositions"]):
        fail("native disposition completeness")
    for row in output["native_dispositions"]:
        if row["outcome"] in ("withheld", "native_only") and ("reason" not in row or "target" in row):
            fail("withheld without reason")


def summarize(output):
    facts = [{"fact_id": item["key"]["fact_id"], "dimension": item["key"]["dimensions"][0]["value"]["text"], "value": item["value"], "evidence_grade": item["evidence_grade"], "retained": item["retained"], "observation_revision": item["observation_revision"]} for item in output["facts"]]
    relationships = [{"id": item["id"], "from": item["from"]["text"], "to": item["to"]["text"]} for item in output["relationships"]]
    dispositions = []
    for item in output["dispositions"]:
        row = {"item_id": item["item_id"], "outcome": item["outcome"], "published": len(item["source_keys"]), "loss": [loss["kind"] for loss in item["loss"]]}
        if "reason" in item:
            row["reason"] = item["reason"]
        dispositions.append(row)
    return {"facts": facts, "relationships": relationships, "dispositions": dispositions, "native_dispositions": output["native_dispositions"], "operations": output["operations"]}


def run_scenario(scenario, contract):
    case = copy.deepcopy(contract["baselines"][scenario["baseline"]])
    for mutation in scenario.get("mutations", []):
        mutate(case, mutation)
    return project(case, contract)


def validate_scenarios(contract):
    scenarios = contract.get("scenarios", [])
    if set(contract.get("baselines", {})) != {"m1", "m3"} or [s.get("baseline") for s in scenarios[:2]] != ["m1", "m3"] or any(s.get("mutations") for s in scenarios[:2]):
        fail("scenario baselines")
    ids = [s.get("id") for s in scenarios]
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
        seen_reasons |= {row["reason"] for row in output["native_dispositions"] if "reason" in row}
    if seen_errors != set(ERROR_PRECEDENCE):
        fail("negative scenarios do not cover every error code")
    if seen_reasons != set(contract["reasons"]):
        fail("scenarios do not cover every reason")


def document(contract):
    validate_contract(contract)
    validate_scenarios(contract)


def table(text, heading):
    """Rows of the first Markdown table under `heading`, without the header and separator, cells stripped of backticks."""
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


def native_form(spec):
    return "%s, %s, gain %d" % (spec["type"], spec["unit"], spec["gain"]) if spec["unit"] else "%s, code" % spec["type"]


def expected_tables(contract):
    mapped, held = [], []
    for rule in contract["field_rules"]:
        outcome = rule["disposition"]["outcome"]
        if outcome in ("exact", "transformed"):
            kinds = "+".join(loss["kind"] for loss in rule["disposition"]["loss"]) or "none"
            ceiling = rule["grade_ceiling"]
            mapped.append([rule["native_id"], native_form(rule["native"]), rule["target"], rule["dimension"], outcome, kinds, ceiling["m3"].capitalize(), ceiling["m1"].capitalize()])
        else:
            reason = rule["disposition"]["reason"]
            held.append([rule["native_id"], outcome, reason, contract["reasons"][reason]["loss_kind"], contract["outcome_vocabulary"][outcome]])
    return mapped, held


def check_document(contract, text):
    mapped, held = expected_tables(contract)
    if table(text, "## Field mapping") != mapped or table(text, "## Withheld and native-only") != held:
        fail("document tables")
    if [row[0] for row in table(text, "## Acceptance vectors")] != [scenario["id"] for scenario in contract["scenarios"]]:
        fail("document vectors")
    flat = " ".join(text.split()).lower()
    for token in DOC_TOKENS:
        if token not in flat:
            fail("document boundary")
    if HEX_RUN_RE.search(text) or HEX_RUN_RE.search(json.dumps(contract)):
        fail("publication: digest or revision literal")
    for profile in contract["native_contract"]["profiles"]:
        if "`%s`" % profile["profile_id"] not in text:
            fail("document profile")


def main():
    contract = load()
    document(contract)
    check_document(contract, DOC.read_text(encoding="utf-8"))
    positives = sum(scenario["polarity"] == "positive" for scenario in contract["scenarios"])
    print(f"Huawei SUN2000 PV mapping: PASS; {positives} executable outputs and {len(contract['scenarios']) - positives} rejected scenarios")


if __name__ == "__main__":
    main()
