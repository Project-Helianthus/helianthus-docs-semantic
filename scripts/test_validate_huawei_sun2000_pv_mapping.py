#!/usr/bin/env python3
"""Mutation controls for the Huawei SUN2000 PV mapping gate (run with python3 or python3 -m pytest)."""
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_huawei_sun2000_pv_mapping", ROOT / "scripts/validate_huawei_sun2000_pv_mapping.py")
v = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v
SPEC.loader.exec_module(v)

SUPPORT_SPEC = importlib.util.spec_from_file_location("huawei_mapping_test_support", ROOT / "scripts/huawei_mapping_test_support.py")
support = importlib.util.module_from_spec(SUPPORT_SPEC)
sys.modules[SUPPORT_SPEC.name] = support
SUPPORT_SPEC.loader.exec_module(support)
parametrize, raises = support.parametrize, support.raises

M1, M3 = v.M1, v.M3


def contract():
    return copy.deepcopy(v.load())


def case(name="m1"):
    return copy.deepcopy(v.load()["baselines"][name])


def fact_position(document, key, index):
    return next(position for position, fact in enumerate(document["facts"]) if fact["key"] == key and fact["index"] == index)


def set_path(document, path, value):
    v.mutate(document, {"path": path, "value": value})


def assert_rejected(mutation, message):
    document = contract()
    mutation(document)
    with raises(ValueError) as error:
        v.validate_contract(document)
    assert message in str(error.value)


def project(document):
    return v.project(document, v.load())


def by_key(output):
    return {(f["key"]["fact_id"], f["key"]["dimensions"][0]["value"]["text"]): f for f in output["facts"]}


def split_words(raw, count, signed):
    if raw < 0:
        assert signed
        raw += 1 << (16 * count)
    return [(raw >> (16 * (count - 1 - k))) & 0xFFFF for k in range(count)]


def test_gate_passes_with_its_page():
    document = v.load()
    v.document(document)
    v.check_document(document, v.DOC.read_text(encoding="utf-8"))


def test_no_binary_floating_point_anywhere():
    with raises(ValueError, match="binary floating point"):
        v.loads('{"coefficient": 601.2}')
    document = contract()
    set_path(document, "decimal_policy.exponent10_range.0", -18.0)
    with raises(ValueError, match="binary floating point"):
        v.validate_contract(document)
    float_case = case()
    set_path(float_case, "lifecycle.receipt_monotonic", 5.0e9)
    with raises(ValueError, match="native_evidence_invalid"):
        project(float_case)


@parametrize("name,mutation,message", [
    ("pack", lambda d: set_path(d, "pack.id", "helianthus.pack.storage"), "contract"),
    ("pack-version", lambda d: set_path(d, "pack.version", "1.1.0"), "contract"),
    ("status", lambda d: set_path(d, "status", "accepted"), "contract"),
    ("evidence-pull-request", lambda d: set_path(d, "evidence.registry_profiles.pull_request", 358), "evidence"),
    ("evidence-contract-issue", lambda d: set_path(d, "evidence.monitoring_contract.issue", 241), "evidence"),
    ("edition-title", lambda d: set_path(d, "native_contract.edition.title", "SUN2000MC V200R023C00 Modbus Interface Definitions (draft)"), "edition"),
    ("edition-issue", lambda d: set_path(d, "native_contract.edition.issue", "Issue 02"), "edition"),
    ("edition-date", lambda d: set_path(d, "native_contract.edition.date", "2023-04-20"), "edition"),
    ("edition-quoted", lambda d: set_path(d, "native_contract.edition.use", "quoted"), "edition"),
    ("registry-flag", lambda d: set_path(d, "native_contract.registry_flags.live_qualified", True), "native contract"),
    ("outbound", lambda d: set_path(d, "native_contract.outbound_allowed", True), "native contract"),
    ("word-order", lambda d: set_path(d, "native_contract.word_order", "least_significant_word_first"), "native contract"),
    ("map0-gains-a-field", lambda d: set_path(d, "native_contract.unmapped_families.0.fields", ["pv_string_voltage"]), "unmapped family"),
    ("map0-outcome", lambda d: set_path(d, "native_contract.unmapped_families.0.outcome", "PROFILE_SELECTED"), "unmapped family"),
    ("profile-removed", lambda d: v.mutate(d, {"path": "native_contract.profiles.1", "remove": True}), "profiles"),
    ("field-dropped-from-profile", lambda d: v.mutate(d, {"path": "native_contract.profiles.1.fields.4", "remove": True}), "profile field inventory"),
    ("field-duplicated-in-profile", lambda d: set_path(d, "native_contract.profiles.1.fields.1.native_id", "pv_string_voltage"), "profile field inventory"),
    ("field-added-to-profile", lambda d: d["native_contract"]["profiles"][0]["fields"].append({"native_id": "battery_power", "state": "admitted"}), "profile field inventory"),
    ("refused-field-admitted", lambda d: set_path(d, "native_contract.profiles.0.fields.2.state", "admitted"), "profile field inventory"),
    ("fact-count", lambda d: set_path(d, "native_contract.profiles.0.fact_count", 20), "profile read plan"),
    ("read-plan-extent", lambda d: set_path(d, "native_contract.profiles.1.read_plan.2.quantity", 31), "profile read plan"),
    ("refusal-dropped", lambda d: v.mutate(d, {"path": "native_contract.profiles.0.refused_groups.0", "remove": True}), "profile read plan"),
    ("rule-removed", lambda d: v.mutate(d, {"path": "field_rules.0", "remove": True}), "missing disposition"),
    ("rule-duplicated", lambda d: d["field_rules"].append(copy.deepcopy(d["field_rules"][0])), "duplicate disposition"),
    ("rule-without-native-field", lambda d: d["field_rules"].append({**copy.deepcopy(d["field_rules"][-1]), "native_id": "battery_power"}), "disposition without native field"),
    ("exact-with-loss", lambda d: set_path(d, "field_rules.0.disposition.loss", [{"kind": "policy"}]), "exact loss"),
    ("transformed-without-loss", lambda d: set_path(d, "field_rules.2.disposition.loss", []), "transformed loss"),
    ("loss-kind", lambda d: set_path(d, "field_rules.5.disposition.loss.0.kind", "native_enum"), "transformed loss"),
    ("loss-not-reversible-flag", lambda d: set_path(d, "field_rules.5.disposition.loss.0.reversible", "no"), "transformed loss"),
    ("loss-wrong-native-item", lambda d: set_path(d, "field_rules.5.disposition.loss.0.source_items", ["native.huawei.sun2000.active_power"]), "transformed loss"),
    ("withheld-without-reason", lambda d: v.mutate(d, {"path": "field_rules.6.disposition.reason", "remove": True}), "withheld reason"),
    ("withheld-unknown-reason", lambda d: set_path(d, "field_rules.6.disposition.reason", "pv.reason.invented"), "withheld reason"),
    ("withheld-with-loss", lambda d: set_path(d, "field_rules.6.disposition.loss", []), "withheld reason"),
    ("target-other-fact", lambda d: set_path(d, "field_rules.0.target", "pv.dc.current"), "target definition"),
    ("target-not-in-pack", lambda d: set_path(d, "field_rules.0.target", "pv.dc.invented"), "target definition"),
    ("unit-other-than-pack", lambda d: set_path(d, "field_rules.0.unit", "unit.watt"), "target definition"),
    ("dimension-other-than-pack", lambda d: set_path(d, "field_rules.0.dimension", "pv.dimension.string"), "target definition"),
    ("dimension-text", lambda d: set_path(d, "field_rules.0.dimension_text", "input:{n}:{asset_suffix}"), "dimension text"),
    ("native-gain", lambda d: set_path(d, "field_rules.0.native.gain", 7), "native form"),
    ("native-words", lambda d: set_path(d, "field_rules.2.native.words", 1), "native form"),
    ("unit-shift", lambda d: set_path(d, "field_rules.2.exponent10_shift", 0), "unit shift"),
    ("silent-unit-conversion", lambda d: set_path(d, "field_rules.2.disposition.loss", [{"kind": "provenance", "source_items": ["native.huawei.sun2000.input_power"], "description": "x", "reversible": True}]), "silent unit conversion"),
    ("sign-convention", lambda d: set_path(d, "field_rules.3.sign.negative_value", "published"), "sign convention"),
    ("sign-provenance-loss", lambda d: set_path(d, "field_rules.3.disposition.loss", [d["field_rules"][3]["disposition"]["loss"][0]]), "sign convention"),
    ("status-symbol", lambda d: set_path(d, "field_rules.4.symbols", {"grid_connected": "idle"}), "status symbols"),
    ("status-extra-code", lambda d: set_path(d, "field_rules.4.symbols", {"grid_connected": "generating", "standby": "standby"}), "status symbols"),
    ("status-symbol-loss", lambda d: set_path(d, "field_rules.4.disposition.loss", [{"kind": "policy", "source_items": ["native.huawei.sun2000.device_status"], "description": "x", "reversible": False}]), "status loss"),
    ("energy-policy-loss", lambda d: set_path(d, "field_rules.5.disposition.loss", [{"kind": "time", "source_items": ["native.huawei.sun2000.energy_accumulated"], "description": "x", "reversible": False}]), "counter policy loss"),
    ("ceiling-grade", lambda d: set_path(d, "field_rules.0.grade_ceiling.m3", "certain"), "disposition"),
    ("ceiling-member", lambda d: v.mutate(d, {"path": "field_rules.0.grade_ceiling.m1", "remove": True}), "disposition"),
    ("reason-unused", lambda d: d["reasons"].update({"pv.reason.unused": {"loss_kind": "policy", "description": "x", "reversible": True}}), "reason inventory"),
    ("identity-forbidden-derivation", lambda d: set_path(d, "identity.asset_id.forbidden_derivations.0", "vendor"), "identity contract"),
    ("identity-source-distinct", lambda d: set_path(d, "identity.source_id.distinct_from", "binding_id"), "identity contract"),
    ("identity-binding-inputs", lambda d: set_path(d, "identity.binding_id.stable_inputs.0", "routed_unit"), "identity contract"),
    ("identity-granularity", lambda d: set_path(d, "identity.asset_id.granularity", "one_asset_per_endpoint"), "identity contract"),
    ("identity-dimension-text", lambda d: d["identity"]["dimension_text"].update({"pv.dimension.system": "system:{n}"}), "identity contract"),
    ("identity-phase-value", lambda d: d["identity"]["dimension_text"].update({"pv.dimension.phase": "phase:L1"}), "identity contract"),
    ("lifecycle-retention", lambda d: set_path(d, "lifecycle.retention_fence", "none"), "lifecycle contract"),
    ("lifecycle-device-time", lambda d: set_path(d, "lifecycle.device_time", "statistics_time_used"), "lifecycle contract"),
    ("decimal-policy", lambda d: set_path(d, "decimal_policy.binary_floating_point", "allowed"), "decimal policy"),
    ("derived-energy", lambda d: set_path(d, "decimal_policy.derived_energy", "allowed"), "decimal policy"),
    ("counter-reset", lambda d: set_path(d, "counter_policy.decrease", "reset"), "counter policy"),
    ("counter-sum", lambda d: set_path(d, "counter_policy.sum_across_inverters", "allowed"), "counter policy"),
    ("unsupported-dropped", lambda d: v.mutate(d, {"path": "unsupported.0", "remove": True}), "unsupported"),
    ("requested-dropped", lambda d: v.mutate(d, {"path": "projection.requested_items.0", "remove": True}), "requested items"),
    ("precedence", lambda d: set_path(d, "projection.error_precedence.0", "native_evidence_invalid"), "projection"),
    ("operations", lambda d: set_path(d, "projection.operations", "allowed"), "projection"),
    ("consumer", lambda d: set_path(d, "consumer_cutover.path", "single_asset_projection"), "consumer cutover"),
])
def test_contract_mutations_are_rejected(name, mutation, message):
    assert_rejected(mutation, message)


@parametrize("reason,field,value", [
    ("loss kind", "loss_kind", "native_enum"), ("description", "description", ""), ("reversible flag", "reversible", "yes"),
])
def test_every_reason_declares_its_loss(reason, field, value):
    document = contract()
    document["reasons"]["pv.reason.value_outside_pack_range"][field] = value
    with raises(ValueError, match="reason loss"):
        v.validate_contract(document)


def test_every_native_field_of_each_profile_has_exactly_one_disposition():
    document = v.load()
    rules = {rule["native_id"]: rule for rule in document["field_rules"]}
    for profile in document["native_contract"]["profiles"]:
        expected = [nid for nid, _ in v.PROFILE_FIELDS[profile["profile_id"]]]
        assert [row["native_id"] for row in profile["fields"]] == expected
        for nid in expected:
            assert len([rule for rule in document["field_rules"] if rule["native_id"] == nid]) == 1
            assert rules[nid]["disposition"]["outcome"] in v.OUTCOMES
    for scenario in document["scenarios"]:
        if scenario["polarity"] != "positive":
            continue
        output = v.run_scenario(scenario, document)
        profile = next(p for p in document["native_contract"]["profiles"] if p["profile_id"] == document["baselines"][scenario["baseline"]]["selection"]["profile_id"])
        v.assert_complete(output, profile, rules)
        rows = [(row["native_id"], row.get("index")) for row in output["native_dispositions"]]
        assert len(rows) == len(set(rows))
        assert len(output["native_dispositions"]) == len(profile["fields"]) - 2 + 16  # eight string rows for voltage and for current, one row for every other field


def test_completeness_check_catches_a_dropped_duplicated_or_unexplained_row():
    document = v.load()
    rules = {rule["native_id"]: rule for rule in document["field_rules"]}
    scenario = document["scenarios"][0]
    profile = document["native_contract"]["profiles"][1]
    output = v.run_scenario(scenario, document)
    for damage in ("drop", "duplicate", "reason", "target"):
        broken = copy.deepcopy(output)
        rows = broken["native_dispositions"]
        if damage == "drop":
            del rows[-1]
        elif damage == "duplicate":
            rows.append(copy.deepcopy(rows[-1]))
        elif damage == "reason":
            del next(row for row in rows if row["outcome"] == "withheld")["reason"]
        else:
            next(row for row in rows if row["outcome"] == "withheld")["target"] = "pv.dc.voltage"
        with raises(ValueError):
            v.assert_complete(broken, profile, rules)


def test_quantities_are_canonical_decimals():
    assert v.canonical(6000, -1) == {"coefficient": "6", "exponent10": 2}
    assert v.canonical(750, -2) == {"coefficient": "75", "exponent10": -1}
    assert v.canonical(0, -3) == {"coefficient": "0", "exponent10": 0}
    assert v.canonical(-300, 0) == {"coefficient": "-3", "exponent10": 2}
    assert v.canonical(1234567, -2) == {"coefficient": "1234567", "exponent10": -2}
    with raises(ValueError):
        v.canonical(1, 19)


def test_words_decode_with_the_contract_word_form():
    assert v.decode([0xFFFF], "I16") == -1
    assert v.decode([0x7FFF], "I16") == 32767
    assert v.decode([0xFFFF], "U16") == 65535
    assert v.decode([0x0012, 0xD687], "U32") == 1234567
    assert v.decode([0xFFFF, 0xFED4], "I32") == -300
    assert v.decode([0xD687, 0x0012], "U32") != 1234567
    for bad in ([], [1, 2], [0x10000], [-1], [True]):
        with raises(ValueError):
            v.decode(bad, "I16")


ADMITTED = [("pv_string_voltage", 1), ("pv_string_voltage", 2), ("pv_string_current", 1), ("pv_string_current", 2),
            ("input_power", 0), ("active_power", 0), ("energy_accumulated", 0), ("energy_current_hour", 0), ("energy_current_day", 0)]
OWN_FACT = {("pv_string_voltage", 1): ("pv.dc.voltage", "input:1"), ("pv_string_voltage", 2): ("pv.dc.voltage", "input:2"),
            ("pv_string_current", 1): ("pv.dc.current", "input:1"), ("pv_string_current", 2): ("pv.dc.current", "input:2"),
            ("input_power", 0): ("pv.dc.aggregate_power", "inverter:demo-alpha"), ("active_power", 0): ("pv.ac.aggregate_active_power", "inverter:demo-alpha"),
            ("energy_accumulated", 0): ("pv.energy.generated", "system:demo-alpha"), ("energy_current_hour", 0): None, ("energy_current_day", 0): None}


@parametrize("key,index", ADMITTED)
def test_each_consumed_word_changes_exactly_its_own_fact(key, index):
    base = case()
    before = by_key(project(base))
    position = fact_position(base, key, index)
    fact = base["facts"][position]
    spec = next(rule for rule in v.load()["field_rules"] if rule["native_id"] == key)["native"]
    raw = int(fact["value"]["coefficient"]) + 1
    fact["value"]["coefficient"] = str(raw)
    fact["words"] = split_words(raw, spec["words"], spec["type"].startswith("I"))
    after = by_key(project(base))
    changed = {name for name in set(before) | set(after) if before.get(name) != after.get(name)}
    expected = OWN_FACT[(key, index)]
    assert changed == (set() if expected is None else {expected})


def test_scale_gain_and_unit_conversion_for_each_form():
    out = by_key(project(case()))
    assert out[("pv.dc.voltage", "input:1")]["value"]["quantity"] == {"number": {"coefficient": "6012", "exponent10": -1}, "unit": "unit.volt"}
    assert out[("pv.dc.current", "input:1")]["value"]["quantity"] == {"number": {"coefficient": "75", "exponent10": -1}, "unit": "unit.ampere"}
    assert out[("pv.dc.aggregate_power", "inverter:demo-alpha")]["value"]["quantity"] == {"number": {"coefficient": "9", "exponent10": 3}, "unit": "unit.watt"}
    assert out[("pv.ac.aggregate_active_power", "inverter:demo-alpha")]["value"]["quantity"] == {"number": {"coefficient": "864", "exponent10": 1}, "unit": "unit.watt"}
    assert out[("pv.energy.generated", "system:demo-alpha")]["value"]["quantity"] == {"number": {"coefficient": "1234567", "exponent10": -2}, "unit": "unit.kilowatt_hour"}


def test_a_gain_or_word_order_mistake_is_rejected():
    for path, value in (("value.exponent10", -2), ("value.coefficient", "90000"), ("words", [9000, 0])):
        document = case()
        set_path(document, "facts.%d.%s" % (fact_position(document, "input_power", 0), path), value)
        with raises(ValueError, match="native_evidence_invalid"):
            project(document)


def test_negative_active_power_is_withheld_and_never_assumed():
    document = case()
    position = fact_position(document, "active_power", 0)
    document["facts"][position]["value"] = {"coefficient": "-300", "exponent10": -3}
    document["facts"][position]["words"] = [0xFFFF, 0xFED4]
    output = project(document)
    assert ("pv.ac.aggregate_active_power", "inverter:demo-alpha") not in by_key(output)
    row = next(row for row in output["native_dispositions"] if row["native_id"] == "active_power")
    assert row == {"native_id": "active_power", "outcome": "withheld", "reason": "pv.reason.negative_active_power_sign_unknown"}
    assert len(output["facts"]) == 7


def test_zero_pair_never_creates_an_input_and_a_single_nonzero_word_does():
    document = case()
    for key, raw in (("pv_string_voltage", 0), ("pv_string_current", 0)):
        position = fact_position(document, key, 3)
        assert int(document["facts"][position]["value"]["coefficient"]) == raw
    assert not any(text == "input:3" for _, text in by_key(project(document)))
    position = fact_position(document, "pv_string_current", 3)
    document["facts"][position]["value"]["coefficient"] = "1"
    document["facts"][position]["words"] = [1]
    out = by_key(project(document))
    assert out[("pv.dc.current", "input:3")]["value"]["quantity"]["number"] == {"coefficient": "1", "exponent10": -2}
    assert out[("pv.dc.voltage", "input:3")]["value"]["quantity"]["number"] == {"coefficient": "0", "exponent10": 0}


def test_unknown_is_absence_and_never_zero():
    document = case()
    for key in ("input_power", "active_power"):
        position = fact_position(document, key, 0)
        for member in ("value", "words"):
            del document["facts"][position][member]
        document["facts"][position].update({"availability": "UNKNOWN", "grade": "unknown"})
    out = by_key(project(document))
    assert ("pv.dc.aggregate_power", "inverter:demo-alpha") not in out and ("pv.ac.aggregate_active_power", "inverter:demo-alpha") not in out
    reasons = {row["native_id"]: row["reason"] for row in project(document)["native_dispositions"] if row["native_id"] in ("input_power", "active_power")}
    assert reasons == {"input_power": "pv.reason.native_fact_unknown", "active_power": "pv.reason.native_fact_unknown"}


def test_unknown_fact_that_carries_a_value_is_rejected():
    document = case()
    position = fact_position(document, "input_power", 0)
    document["facts"][position].update({"availability": "UNKNOWN", "grade": "unknown"})
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)


def test_status_publishes_only_the_observed_state():
    out = by_key(project(case()))
    symbol = out[("pv.status.operating", "inverter:demo-alpha")]["value"]["symbol"]
    assert symbol == {"namespace": "pv.status.operating", "token": "generating", "known": True}
    document = case()
    document["facts"][fact_position(document, "device_status", 0)]["state"] = "standby"
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)


def test_energy_counter_policy_publishes_one_counter_and_no_derivation():
    out = project(case())
    energy = [f for f in out["facts"] if f["key"]["fact_id"] == "pv.energy.generated"]
    assert len(energy) == 1
    assert {row["native_id"]: row["reason"] for row in out["native_dispositions"] if row["native_id"] in ("energy_current_hour", "energy_current_day")} == {
        "energy_current_hour": "pv.reason.period_counter_time_domain_not_represented", "energy_current_day": "pv.reason.period_counter_time_domain_not_represented"}
    disposition = next(item for item in out["dispositions"] if item["item_id"] == "pv.energy.generated")
    assert [loss["kind"] for loss in disposition["loss"]] == ["policy"] and disposition["loss"][0]["reversible"] is False
    document = case()
    document["derive_energy"] = "difference_of_counters"
    with raises(ValueError, match="unsupported_or_withheld"):
        project(document)


def test_grade_is_inherited_and_never_raised():
    m3 = case("m3")
    for position, fact in enumerate(m3["facts"]):
        if fact["key"] == "pv_string_current":
            fact["grade"] = "proven"
    out = project(m3)
    grades = {(f["key"]["fact_id"]): f["evidence_grade"] for f in out["facts"]}
    assert grades["pv.dc.current"] == "hypothesis" and grades["pv.dc.voltage"] == "proven" and grades["pv.energy.generated"] == "proven"
    m1 = project(case())
    grades = {f["key"]["fact_id"]: f["evidence_grade"] for f in m1["facts"]}
    assert grades["pv.energy.generated"] == "hypothesis" and grades["pv.status.operating"] == "hypothesis" and grades["pv.dc.aggregate_power"] == "proven"
    lowered = case()
    lowered["facts"][fact_position(lowered, "input_power", 0)]["grade"] = "hypothesis"
    assert {f["key"]["fact_id"]: f["evidence_grade"] for f in project(lowered)["facts"]}["pv.dc.aggregate_power"] == "hypothesis"


def test_refused_power_group_withholds_power_and_status_on_the_m3_profile():
    out = project(case("m3"))
    reasons = {row["native_id"]: row["reason"] for row in out["native_dispositions"] if row["native_id"] in ("input_power", "active_power", "device_status")}
    assert set(reasons.values()) == {"pv.reason.power_group_refused"}
    withheld = {item["item_id"]: item for item in out["dispositions"] if item["outcome"] == "withheld"}
    assert set(withheld) == {"pv.dc.aggregate_power", "pv.ac.aggregate_active_power", "pv.status.operating"}
    assert all(item["loss"] and item["reason"] == "pv.reason.power_group_refused" for item in withheld.values())
    document = case("m3")
    document["facts"].append(copy.deepcopy(case()["facts"][fact_position(case(), "input_power", 0)]))
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)


def test_retained_reading_keeps_its_original_observation():
    document = case()
    document["groups"][3]["outcome"] = "FAILED"
    for key in ("energy_accumulated", "energy_current_hour", "energy_current_day"):
        fact = document["facts"][fact_position(document, key, 0)]
        fact.update({"retained": True, "observation_id": "observation:demo-0003", "observation_revision": 3})
    energy = next(f for f in project(document)["facts"] if f["key"]["fact_id"] == "pv.energy.generated")
    assert energy["retained"] is True and energy["observation_id"] == "observation:demo-0003" and energy["observation_revision"] == 3
    for member, value in (("observation_revision", 5), ("observation_id", "observation:demo-0005")):
        broken = copy.deepcopy(document)
        broken["facts"][fact_position(broken, "energy_accumulated", 0)][member] = value
        with raises(ValueError, match="native_evidence_invalid"):
            project(broken)


def test_fact_keys_follow_the_pack_dimensions_and_relationships():
    out = project(case())
    pack = v.pack_catalog()[0]
    for fact in out["facts"]:
        key = fact["key"]
        assert key["pack_id"] == "helianthus.pack.pv" and key["pack_version"] == "1.0.0"
        assert [dimension["id"] for dimension in key["dimensions"]] == [pack[key["fact_id"]]["dimension"]]
        assert not any(dimension["id"] == "pv.dimension.phase" for dimension in key["dimensions"])
    assert {(r["id"], r["from"]["text"], r["to"]["text"]) for r in out["relationships"]} == {
        ("pv.relationship.system_inverter", "system:demo-alpha", "inverter:demo-alpha"),
        ("pv.relationship.inverter_input", "inverter:demo-alpha", "input:1"), ("pv.relationship.inverter_input", "inverter:demo-alpha", "input:2")}


# Identity and key coverage. Each row varies one field and names the production mutation the assertion catches.
@parametrize("path,value,check", [
    ("identity.asset_id", "pv-asset-demo-omega", lambda a, b: a["key"]["dimensions"][0]["value"]["text"] != b["key"]["dimensions"][0]["value"]["text"]),  # system/inverter text must follow the asset
    ("identity.binding_id", "binding:semantic-pv:demo-omega", lambda a, b: a["source_path"]["binding_id"] != b["source_path"]["binding_id"]),  # binding dropped from the source path
    ("source.source_id", "source:gateway-demo-z", lambda a, b: a["source_path"]["source_id"] != b["source_path"]["source_id"]),  # source taken from the asset
    ("lifecycle.source_epoch", "source-epoch:9", lambda a, b: a["source_path"]["source_epoch_id"] != b["source_path"]["source_epoch_id"]),  # epoch not carried
    ("lifecycle.driver_generation", 7, lambda a, b: a["source_path"]["driver_generation"] != b["source_path"]["driver_generation"]),  # generation not carried
])
def test_identity_and_lifecycle_fields_reach_the_published_fact(path, value, check):
    base = case()
    varied = copy.deepcopy(base)
    set_path(varied, path, value)
    first = next(f for f in project(base)["facts"] if f["key"]["fact_id"] == "pv.energy.generated")
    second = next(f for f in project(varied)["facts"] if f["key"]["fact_id"] == "pv.energy.generated")
    assert check(first, second)


def test_input_dimension_does_not_depend_on_the_asset():
    base, varied = case(), case()
    set_path(varied, "identity.asset_id", "pv-asset-demo-omega")
    left = {f["key"]["dimensions"][0]["value"]["text"] for f in project(base)["facts"] if f["key"]["fact_id"] == "pv.dc.voltage"}
    right = {f["key"]["dimensions"][0]["value"]["text"] for f in project(varied)["facts"] if f["key"]["fact_id"] == "pv.dc.voltage"}
    assert left == right == {"input:1", "input:2"}


@parametrize("asset", ["", None, "pv asset", "pv-asset-serial-0001", "pv-asset-ESN-1", "pv-asset-10.0.0.7", "pv-asset-host:502", "1", "source:gateway-demo-a", "binding:semantic-pv:demo-alpha", "pv-asset-sun2000-a", "pv-asset-huawei", "pv-asset-smartlogger-a"])
def test_asset_identifier_never_comes_from_forbidden_inputs(asset):
    document = case()
    document["identity"]["asset_id"] = asset
    with raises(ValueError, match="identity_missing_or_invalid"):
        project(document)


@parametrize("path,value", [("source.source_id", ""), ("source.source_id", "source:10.1.1.1"), ("identity.binding_id", None), ("identity.binding_id", "pv-asset-demo-alpha"), ("source", None), ("identity", {})])
def test_source_and_binding_identifiers_fail_closed(path, value):
    document = case()
    set_path(document, path, value)
    with raises(ValueError, match="identity_missing_or_invalid"):
        project(document)


@parametrize("flag", sorted(v.REGISTRY_FLAGS) + ["mapping_qualified", "outbound_allowed"])
def test_every_qualification_flag_is_pinned(flag):
    document = case()
    document["qualification"][flag] = not document["qualification"][flag]
    with raises(ValueError, match="mapping_unqualified"):
        project(document)


@parametrize("outcome", ["INSUFFICIENT_EVIDENCE", "NO_ADMISSIBLE_PROFILE", "AMBIGUOUS", "", None])
def test_only_a_selected_exact_profile_maps(outcome):
    document = case()
    document["selection"]["outcome"] = outcome
    with raises(ValueError, match="profile_not_selected"):
        project(document)


@parametrize("profile_id", ["huawei.sun2000.map0.monitoring-readonly@1.0.0", "huawei.sun2000.m1.monitoring-readonly@1.0.1", "huawei.sun2000.m1.monitoring-readonly", "huawei.sun2000.m1", ""])
def test_profile_identifier_must_be_exact(profile_id):
    document = case()
    document["selection"]["profile_id"] = profile_id
    with raises(ValueError, match="profile_not_selected"):
        project(document)


def test_a_group_outside_the_plan_or_a_refused_group_that_answered_is_rejected():
    document = case("m3")
    document["groups"][2]["outcome"] = "ANSWERED"
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)
    document = case()
    document["groups"].append({"offset": 37000, "quantity": 30, "outcome": "ANSWERED"})
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)


@parametrize("group,member,value", [(0, "outcome", "EXCEPTION"), (0, "exception_code", 3), (0, "outcome", "TIMEOUT"), (3, "exception_code", 3)])
def test_group_outcomes_and_exception_codes_must_agree(group, member, value):
    document = case()
    document["groups"][group][member] = value
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)


def test_operations_are_never_available():
    for member, value in (("request_operation", "pv.operation.set_export_limit"), ("request_operation", "pv.operation.set_active_power_limit")):
        document = case()
        document[member] = value
        with raises(ValueError, match="unsupported_or_withheld"):
            project(document)
    assert project(case())["operations"] == []


def test_scenario_expectations_are_executed_not_trusted():
    for damage, message in (
        (lambda d: d["scenarios"][0]["expect"]["output"]["facts"][0]["value"]["quantity"]["number"].update({"coefficient": "999"}), "scenario output"),
        (lambda d: d["scenarios"][4]["expect"]["summary"]["facts"].pop(), "scenario summary"),
        (lambda d: d["scenarios"][2]["expect"]["summary"]["native_dispositions"][0].update({"outcome": "withheld"}), "scenario summary"),
        (lambda d: d["scenarios"][-1]["expect"].update({"error": "lifecycle_missing"}), "profile_not_selected"),
    ):
        document = contract()
        damage(document)
        with raises(ValueError) as error:
            v.validate_scenarios(document)
        assert message in str(error.value)


def test_scenario_coverage_is_enforced():
    document = contract()
    document["scenarios"] = [s for s in document["scenarios"] if s["id"] != "PV-POS-005-unobserved-status-code"]
    with raises(ValueError, match="cover every reason"):
        v.validate_scenarios(document)
    document = contract()
    document["scenarios"] = [s for s in document["scenarios"] if s["id"] != "PV-NEG-014-lifecycle-missing"]
    with raises(ValueError, match="cover every error"):
        v.validate_scenarios(document)
    document = contract()
    document["scenarios"][1]["mutations"] = [{"path": "identity.asset_id", "value": "pv-asset-demo-omega"}]
    with raises(ValueError, match="scenario baselines"):
        v.validate_scenarios(document)


def test_a_negative_scenario_that_is_accepted_fails():
    document = contract()
    negative = next(s for s in document["scenarios"] if s["id"] == "PV-NEG-010-asset-missing")
    negative["mutations"] = []
    with raises(ValueError, match="accepted"):
        v.validate_scenarios(document)


def page():
    return v.DOC.read_text(encoding="utf-8")


@parametrize("old,new", [
    ("| `pv_string_voltage` | I16, V, gain 10 | `pv.dc.voltage` | `pv.dimension.input` | exact |", "| `pv_string_voltage` | I16, V, gain 10 | `pv.dc.voltage` | `pv.dimension.input` | transformed |"),
    ("| `input_power` | I32, kW, gain 1000 | `pv.dc.aggregate_power` |", "| `input_power` | I32, kW, gain 1000 | `pv.dc.power` |"),
    ("| `pv_string_current` | I16, A, gain 100 | `pv.dc.current` | `pv.dimension.input` | exact | none | Hypothesis | Proven |", "| `pv_string_current` | I16, A, gain 100 | `pv.dc.current` | `pv.dimension.input` | exact | none | Proven | Proven |"),
    ("| `battery` | withheld | `pv.reason.battery_outside_pv_family` | capability | withheld |", "| `battery` | withheld | `pv.reason.battery_outside_pv_family` | capability | unrepresentable |"),
    ("| `PV-NEG-018-error-precedence` |", "| `PV-NEG-099-other` |"),
    ("Proven only where the monitoring contract is Proven", "Proven where a document says so"),
    ("outbound_allowed=false", "outbound allowed"),
])
def test_page_must_match_the_contract(old, new):
    pattern = re.escape(old).replace(r"\ ", r"\s+")
    mutated, count = re.subn(pattern, lambda _: new, page())
    assert count >= 1
    with raises(ValueError):
        v.check_document(v.load(), mutated)


def test_a_dropped_table_row_is_rejected():
    lines = [line for line in page().splitlines(keepends=True) if not line.startswith("| `energy_current_day` |")]
    with raises(ValueError, match="document tables"):
        v.check_document(v.load(), "".join(lines))


@parametrize("literal", ["a" * 40, "0123456789abcdef" * 4, "A1" * 20])
def test_publication_rule_rejects_revision_and_digest_literals(literal):
    with raises(ValueError, match="publication"):
        v.check_document(v.load(), page() + "\n" + literal + "\n")


def test_published_files_cite_no_revision_link_or_endpoint():
    for path in (v.PATH, v.DOC):
        text = path.read_text(encoding="utf-8")
        assert not v.HEX_RUN_RE.search(text)
        assert "/blob/" not in text and "/commit/" not in text and "/tree/" not in text
        assert "#L" not in text
    forbidden = ("serial_number:", "esn:", "tcp://")
    assert not any(token in v.PATH.read_text(encoding="utf-8") for token in forbidden)


def test_baselines_are_synthetic():
    text = v.PATH.read_text(encoding="utf-8")
    document = json.loads(text)
    for baseline in document["baselines"].values():
        assert baseline["lifecycle"]["receipt_wall"] == "2026-01-01T00:00:00Z"
        assert baseline["identity"]["asset_id"].startswith("pv-asset-demo-")
        assert baseline["source"]["source_id"].startswith("source:gateway-demo-")


if __name__ == "__main__":
    raise SystemExit(support.run(globals()))
