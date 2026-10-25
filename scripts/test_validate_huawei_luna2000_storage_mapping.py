#!/usr/bin/env python3
"""Mutation controls for the Huawei LUNA2000 storage gate (run with python3 or python3 -m pytest)."""
import copy
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_huawei_luna2000_storage_mapping", ROOT / "scripts/validate_huawei_luna2000_storage_mapping.py")
v = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v
SPEC.loader.exec_module(v)

SUPPORT_SPEC = importlib.util.spec_from_file_location("huawei_mapping_test_support", ROOT / "scripts/huawei_mapping_test_support.py")
support = importlib.util.module_from_spec(SUPPORT_SPEC)
sys.modules[SUPPORT_SPEC.name] = support
SUPPORT_SPEC.loader.exec_module(support)
parametrize, raises = support.parametrize, support.raises


def contract():
    return copy.deepcopy(v.load())


def case():
    return copy.deepcopy(v.load()["baselines"]["default"])


def set_path(document, path, value):
    v.mutate(document, {"path": path, "value": value})


def project(document):
    return v.project(document, v.load())


def rule_index(native_id):
    return [r["native_id"] for r in v.load()["field_rules"]].index(native_id)


def test_gate_passes_with_its_page():
    document = v.load()
    v.document(document)
    v.check_document(document, v.DOC.read_text(encoding="utf-8"))


def test_no_binary_floating_point():
    with raises(ValueError, match="binary floating point"):
        v.loads('{"gain": 100.0}')
    document = contract()
    set_path(document, "admission.registry_disposition.decoder_keys", 0.0)
    with raises(ValueError):
        v.validate_contract(document)
    float_case = case()
    float_case["reads"] = [{"offset": 37066, "quantity": 4, "outcome": "ANSWERED", "words": [1.0, 2, 3, 4]}]
    with raises(ValueError, match="native_evidence_invalid"):
        project(float_case)


@parametrize("name,mutation,message", [
    ("pack", lambda d: set_path(d, "pack.id", "helianthus.pack.pv"), "contract"),
    ("pack-version", lambda d: set_path(d, "pack.version", "1.0.0"), "contract"),
    ("status", lambda d: set_path(d, "status", "accepted_source_specific_read_only_mapping_gate"), "contract"),
    ("evidence-issue", lambda d: set_path(d, "evidence.registry_profiles.issue", 349), "evidence"),
    ("battery-profile-selectable", lambda d: d["admission"]["selection_outcomes_allowed"].append("PROFILE_SELECTED"), "admission"),
    ("facts-admitted", lambda d: set_path(d, "admission.registry_disposition.facts_admitted", True), "admission"),
    ("decoder-keys", lambda d: set_path(d, "admission.registry_disposition.decoder_keys", 3), "admission"),
    ("registry-flag", lambda d: set_path(d, "admission.registry_flags.write_authority", True), "admission"),
    ("precondition-dropped", lambda d: v.mutate(d, {"path": "admission.preconditions_for_any_mapping.2", "remove": True}), "admission"),
    ("native-item-dropped", lambda d: v.mutate(d, {"path": "field_rules.4", "remove": True}), "native inventory"),
    ("native-item-duplicated", lambda d: d["field_rules"].append(copy.deepcopy(d["field_rules"][0])), "native inventory"),
    ("native-item-added", lambda d: d["field_rules"].append({**copy.deepcopy(d["field_rules"][0]), "native_id": "battery_cell_voltage"}), "native inventory"),
    ("native-item-source", lambda d: set_path(d, "field_rules.4.source", "registry_disposition"), "native inventory"),
    ("native-item-read", lambda d: set_path(d, "field_rules.0.read.quantity", 31), "native inventory"),
    ("outcome-mapped", lambda d: set_path(d, "field_rules.4.disposition.outcome", "exact"), "withheld reason"),
    ("withheld-without-reason", lambda d: v.mutate(d, {"path": "field_rules.4.disposition.reason", "remove": True}), "withheld reason"),
    ("withheld-unknown-reason", lambda d: set_path(d, "field_rules.4.disposition.reason", "storage.reason.invented"), "withheld reason"),
    ("grade", lambda d: set_path(d, "field_rules.4.grade", "certain"), "withheld reason"),
    ("prospective-in-force", lambda d: set_path(d, "field_rules.4.prospective.in_force", True), "prospective target"),
    ("prospective-target-not-in-pack", lambda d: set_path(d, "field_rules.4.prospective.target", "storage.capacity.rated_energy"), "prospective target"),
    ("prospective-other-fact", lambda d: set_path(d, "field_rules.4.prospective.target", "storage.state.soh"), "requested items"),
    ("prospective-unit", lambda d: set_path(d, "field_rules.4.prospective.unit", "unit.ampere_hour"), "prospective target"),
    ("prospective-dimension", lambda d: set_path(d, "field_rules.4.prospective.dimension", "storage.dimension.cell"), "prospective target"),
    ("prospective-native-form", lambda d: set_path(d, "field_rules.4.prospective.native.gain", 1000), "prospective native form"),
    ("prospective-kilowatt-hour-as-ampere-hour", lambda d: set_path(d, "field_rules.7.prospective.unit", "unit.ampere_hour"), "prospective target"),
    ("prospective-sign-removed", lambda d: v.mutate(d, {"path": "field_rules.5.prospective.sign", "remove": True}), "prospective sign"),
    ("prospective-sign-assumed", lambda d: set_path(d, "field_rules.5.prospective.sign", "positive_while_charging_negative_while_discharging_assumed"), "prospective sign"),
    ("prospective-counter-removed", lambda d: v.mutate(d, {"path": "field_rules.7.prospective.counter", "remove": True}), "prospective counter"),
    ("prospective-symbols", lambda d: set_path(d, "field_rules.0.prospective.symbols", ["storage.status.operating.active"]), "prospective symbols"),
    ("reason-unused", lambda d: d["reasons"].update({"storage.reason.unused": {"loss_kind": "policy", "description": "x", "reversible": True}}), "reason inventory"),
    ("reason-primary-removed", lambda d: d["reasons"].pop("storage.reason.no_admitted_battery_profile"), "reason inventory"),
    ("capacity-converted", lambda d: set_path(d, "capacity.conversion", "allowed"), "capacity"),
    ("capacity-published", lambda d: set_path(d, "capacity.energy_units", "published"), "capacity"),
    ("unsupported-dropped", lambda d: v.mutate(d, {"path": "unsupported.0", "remove": True}), "unsupported"),
    ("limit-item-requested", lambda d: set_path(d, "pack_items_never_requested.0", "storage.limit.discharge_power"), "control-adjacent items"),
    ("operation-item-not-in-pack", lambda d: set_path(d, "pack_items_never_requested.4", "storage.operation.set_dispatch"), "control-adjacent items"),
    ("requested-added", lambda d: d["projection"]["requested_items"].append({"kind": "fact", "item_id": "storage.limit.charge_power"}), "requested items"),
    ("requested-dropped", lambda d: v.mutate(d, {"path": "projection.requested_items.0", "remove": True}), "requested items"),
    ("primary-reason", lambda d: set_path(d, "projection.primary_reason", "storage.reason.battery_group_not_read"), "projection"),
    ("precedence", lambda d: set_path(d, "projection.error_precedence.0", "native_evidence_invalid"), "projection"),
    ("operations", lambda d: set_path(d, "projection.operations", "allowed"), "projection"),
    ("identity-forbidden", lambda d: set_path(d, "identity.asset_id.forbidden_derivations.0", "vendor"), "identity contract"),
    ("identity-distinct", lambda d: set_path(d, "identity.source_id.distinct_from", "binding_id"), "identity contract"),
    ("identity-binding", lambda d: set_path(d, "identity.binding_id.stable_inputs.1", "routed_unit"), "identity contract"),
    ("identity-granularity", lambda d: set_path(d, "identity.storage_asset_granularity", "one_asset_per_battery"), "identity contract"),
    ("lifecycle-zero", lambda d: set_path(d, "lifecycle.absent_optional_group", "zero"), "lifecycle contract"),
    ("lifecycle-negation", lambda d: set_path(d, "lifecycle.exception", "negates_the_parent"), "lifecycle contract"),
    ("outcome-vocabulary", lambda d: set_path(d, "outcome_vocabulary.native_only", "exact"), "outcome vocabulary"),
    ("consumer", lambda d: set_path(d, "consumer_cutover.path", "growatt_single_asset_projection"), "consumer cutover"),
])
def test_contract_mutations_are_rejected(name, mutation, message):
    document = contract()
    mutation(document)
    with raises(ValueError) as error:
        v.validate_contract(document)
    assert message in str(error.value)


@parametrize("field,value", [("loss_kind", "native_enum"), ("description", ""), ("reversible", "yes")])
def test_every_reason_declares_its_loss(field, value):
    document = contract()
    document["reasons"]["storage.reason.no_energy_capacity_fact_in_pack"][field] = value
    with raises(ValueError, match="reason loss"):
        v.validate_contract(document)


def test_every_native_item_has_exactly_one_withheld_disposition_and_nothing_is_published():
    document = v.load()
    assert [rule["native_id"] for rule in document["field_rules"]] == [nid for nid, _, _ in v.INVENTORY]
    for scenario in document["scenarios"]:
        if scenario["polarity"] != "positive":
            continue
        output = v.run_scenario(scenario, document)
        assert [row["native_id"] for row in output["native_dispositions"]] == [nid for nid, _, _ in v.INVENTORY]
        assert {row["outcome"] for row in output["native_dispositions"]} == {"withheld"}
        assert output["facts"] == [] and output["relationships"] == [] and output["operations"] == []
        assert [item["outcome"] for item in output["dispositions"]] == ["withheld"] * 5
        assert all(item["source_keys"] == [] and item["reason"] and item["loss"] for item in output["dispositions"])


def test_completeness_check_catches_damage():
    document = v.load()
    output = v.run_scenario(document["scenarios"][0], document)
    for damage in ("drop", "duplicate", "fact", "outcome", "reason"):
        broken = copy.deepcopy(output)
        if damage == "drop":
            del broken["native_dispositions"][-1]
        elif damage == "duplicate":
            broken["native_dispositions"].append(copy.deepcopy(broken["native_dispositions"][-1]))
        elif damage == "fact":
            broken["facts"].append({"key": {}})
        elif damage == "outcome":
            broken["native_dispositions"][0]["outcome"] = "exact"
        else:
            broken["native_dispositions"][0]["reason"] = "storage.reason.invented"
        with raises(ValueError):
            v.assert_complete(broken, document)


@parametrize("reads,expected", [
    ([], {"battery_group_37000_30": "battery_group_not_read", "battery_single_read_37000_1": "battery_group_not_read", "battery_group_37066_4": "battery_group_not_read", "battery_group_47000_1": "battery_group_not_read"}),
    ([{"offset": 37000, "quantity": 1, "outcome": "ANSWERED", "words": [0]}, {"offset": 47000, "quantity": 1, "outcome": "ANSWERED", "words": [0]}],
     {"battery_group_37000_30": "battery_group_not_read", "battery_single_read_37000_1": "zero_word_is_not_a_battery_value", "battery_group_37066_4": "battery_group_not_read", "battery_group_47000_1": "zero_word_is_not_a_battery_value"}),
    ([{"offset": 37066, "quantity": 4, "outcome": "ANSWERED", "words": [0, 0, 0, 0]}], {"battery_group_37066_4": "zero_word_is_not_a_battery_value"}),
    ([{"offset": 37066, "quantity": 4, "outcome": "ANSWERED", "words": [0, 0, 0, 1]}], {"battery_group_37066_4": "no_admitted_battery_profile"}),
    ([{"offset": 37000, "quantity": 30, "outcome": "EXCEPTION", "exception_code": 3}], {"battery_group_37000_30": "battery_group_exception_no_negation"}),
    ([{"offset": 47000, "quantity": 1, "outcome": "FAILED"}, {"offset": 37000, "quantity": 1, "outcome": "NOT_READ"}], {"battery_group_47000_1": "battery_group_not_read", "battery_single_read_37000_1": "battery_group_not_read"}),
])
def test_reads_select_the_reason_and_never_a_value(reads, expected):
    document = case()
    document["reads"] = reads
    output = project(document)
    rows = {row["native_id"]: row["reason"] for row in output["native_dispositions"]}
    for native_id, reason in expected.items():
        assert rows[native_id] == "storage.reason." + reason
    assert output["facts"] == []
    assert not any("quantity" in str(item) for item in output["facts"])


def test_planned_items_keep_their_reason_whatever_is_read():
    document = case()
    document["reads"] = [{"offset": 37000, "quantity": 30, "outcome": "ANSWERED", "words": [1] * 30}]
    rows = {row["native_id"]: row["reason"] for row in project(document)["native_dispositions"]}
    assert rows["site_battery_soc"] == "storage.reason.planned_group_not_observed"
    assert rows["site_rated_storage_capacity"] == "storage.reason.no_energy_capacity_fact_in_pack"
    assert rows["site_battery_energy_charged_day"] == "storage.reason.period_counter_time_domain_not_represented"


@parametrize("read", [
    {"offset": 30368, "quantity": 1, "outcome": "ANSWERED", "words": [7550]},
    {"offset": 37000, "quantity": 29, "outcome": "ANSWERED", "words": [0] * 29},
    {"offset": 37066, "quantity": 4, "outcome": "ANSWERED", "words": [1, 2]},
    {"offset": 37066, "quantity": 4, "outcome": "ANSWERED", "words": [1, 2, 3, 70000]},
    {"offset": 37066, "quantity": 4, "outcome": "ANSWERED", "words": [1, 2, 3, True]},
    {"offset": 37066, "quantity": 4, "outcome": "ANSWERED"},
    {"offset": 37066, "quantity": 4, "outcome": "EXCEPTION"},
    {"offset": 37066, "quantity": 4, "outcome": "FAILED", "words": [1, 2, 3, 4]},
    {"offset": 37066, "quantity": 4, "outcome": "ANSWERED", "words": [1, 2, 3, 4], "exception_code": 3},
    {"offset": 37066, "quantity": 4, "outcome": "TIMEOUT"},
    None,
])
def test_invalid_or_planned_reads_are_rejected(read):
    document = case()
    document["reads"] = [read]
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)


def test_a_duplicate_read_is_rejected():
    document = case()
    read = {"offset": 37066, "quantity": 4, "outcome": "FAILED"}
    document["reads"] = [read, copy.deepcopy(read)]
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)


@parametrize("outcome,message", [("PROFILE_SELECTED", "gate_revision_required"), ("INSUFFICIENT_EVIDENCE", None), ("NO_ADMISSIBLE_PROFILE", None), ("AMBIGUOUS", None), ("", "native_evidence_invalid"), (None, "native_evidence_invalid"), ("OFFLINE_PROFILE_ADMITTED", "native_evidence_invalid")])
def test_a_selected_battery_profile_fails_closed(outcome, message):
    document = case()
    document["luna_selection"]["outcome"] = outcome
    if message is None:
        project(document)
        return
    with raises(ValueError, match=message):
        project(document)


def test_capacity_is_never_converted_to_energy_units_or_published():
    for member, value in (("request_conversion", "ampere_hour_to_kilowatt_hour"), ("request_conversion", "voltage_times_ampere_hour"), ("request_item", "storage.capacity.charge")):
        document = case()
        document[member] = value
        with raises(ValueError, match="unsupported_or_withheld"):
            project(document)
    output = project(case())
    assert not [item for item in output["requested"] if "capacity" in item["item_id"]]
    assert {row["native_id"]: row["reason"] for row in output["native_dispositions"]}["site_rated_storage_capacity"] == "storage.reason.no_energy_capacity_fact_in_pack"


def test_no_limit_interlock_or_operation_is_requested_or_available():
    for operation in ("storage.operation.set_charge_limit", "storage.operation.set_discharge_limit"):
        document = case()
        document["request_operation"] = operation
        with raises(ValueError, match="unsupported_or_withheld"):
            project(document)
    requested = {item["item_id"] for item in project(case())["requested"]}
    assert requested == set(v.REQUESTED) and not requested & set(v.NEVER_REQUESTED)
    for item in v.NEVER_REQUESTED:
        document = case()
        document["request_item"] = item
        with raises(ValueError, match="unsupported_or_withheld"):
            project(document)


def test_prospective_rows_are_not_in_force_and_match_the_pack():
    fields, operations = v.pack_tables()
    document = v.load()
    seen = set()
    for rule in document["field_rules"]:
        plan = rule.get("prospective")
        if not plan:
            continue
        assert plan["in_force"] is False
        assert plan["dimension"] == fields[plan["target"]]["dimension"] == "storage.dimension.pack"
        assert plan.get("unit") == fields[plan["target"]].get("unit")
        seen.add(plan["target"])
    assert seen == set(v.REQUESTED)
    assert "storage.pack.power" in seen and "storage.capacity.charge" not in seen and "storage.capacity.discharge" not in seen
    assert not any(token in str(document["field_rules"]) for token in ("storage.limit.", "storage.status.interlock", "storage.operation."))


@parametrize("asset", ["", None, "storage asset", "storage-asset-serial-1", "storage-asset-ESN-1", "storage-asset-10.2.3.4", "storage-asset-host:502", "source:gateway-demo-c", "binding:semantic-storage:demo-gamma", "storage-asset-luna", "storage-asset-huawei"])
def test_asset_identifier_never_comes_from_forbidden_inputs(asset):
    document = case()
    document["identity"]["asset_id"] = asset
    with raises(ValueError, match="identity_missing_or_invalid"):
        project(document)


@parametrize("path,value", [("source.source_id", ""), ("source.source_id", "source:192.168.0.1"), ("identity.binding_id", None), ("identity.binding_id", "storage-asset-demo-gamma"), ("source", None)])
def test_source_and_binding_identifiers_fail_closed(path, value):
    document = case()
    set_path(document, path, value)
    with raises(ValueError, match="identity_missing_or_invalid"):
        project(document)


@parametrize("path,value", [("lifecycle.observation_id", ""), ("lifecycle.observation_revision", 0), ("lifecycle.receipt_wall", "2026-01-01T00:00:00"), ("lifecycle.receipt_wall", None), ("lifecycle.receipt_monotonic", 0), ("lifecycle.clock_epoch", "bad epoch"), ("lifecycle.source_epoch", None), ("lifecycle.driver_generation", True), ("lifecycle.connection_generation", 0)])
def test_every_lifecycle_axis_is_required(path, value):
    document = case()
    set_path(document, path, value)
    with raises(ValueError, match="lifecycle_missing"):
        project(document)


@parametrize("flag", sorted(v.REGISTRY_FLAGS) + ["mapping_qualified", "outbound_allowed"])
def test_every_qualification_flag_is_pinned(flag):
    document = case()
    document["qualification"][flag] = not document["qualification"][flag]
    with raises(ValueError, match="mapping_unqualified"):
        project(document)


def test_first_error_of_the_precedence_list_wins():
    document = case()
    document["luna_selection"]["outcome"] = "PROFILE_SELECTED"
    document["identity"]["asset_id"] = ""
    document["request_operation"] = "storage.operation.set_charge_limit"
    with raises(ValueError, match="gate_revision_required"):
        project(document)
    document["luna_selection"]["outcome"] = "AMBIGUOUS"
    document["reads"] = [{"offset": 1, "quantity": 1, "outcome": "ANSWERED", "words": [0]}]
    with raises(ValueError, match="native_evidence_invalid"):
        project(document)
    document["reads"] = []
    with raises(ValueError, match="identity_missing_or_invalid"):
        project(document)


def test_scenario_expectations_are_executed_not_trusted():
    for damage, message in (
        (lambda d: d["scenarios"][0]["expect"]["output"]["native_dispositions"][0].update({"reason": "storage.reason.zero_word_is_not_a_battery_value"}), "scenario output"),
        (lambda d: d["scenarios"][1]["expect"]["summary"]["native_dispositions"].pop(), "scenario summary"),
        (lambda d: d["scenarios"][-1]["expect"].update({"error": "lifecycle_missing"}), "gate_revision_required"),
    ):
        document = contract()
        damage(document)
        with raises(ValueError) as error:
            v.validate_scenarios(document)
        assert message in str(error.value)


def test_scenario_coverage_is_enforced():
    for dropped, message in (("STG-POS-002-zero-words-without-battery", "cover every reason"), ("STG-POS-004-battery-read-exception", "cover every reason"), ("STG-NEG-005-lifecycle-missing", "cover every error")):
        document = contract()
        document["scenarios"] = [s for s in document["scenarios"] if s["id"] != dropped]
        with raises(ValueError, match=message):
            v.validate_scenarios(document)


def test_a_negative_scenario_that_is_accepted_fails():
    document = contract()
    next(s for s in document["scenarios"] if s["id"] == "STG-NEG-004-asset-missing")["mutations"] = []
    with raises(ValueError, match="accepted"):
        v.validate_scenarios(document)


def page():
    return v.DOC.read_text(encoding="utf-8")


@parametrize("old,new", [
    ("| `site_rated_storage_capacity` | monitoring_contract_planned | Hypothesis | `storage.reason.no_energy_capacity_fact_in_pack` | capability |", "| `site_rated_storage_capacity` | monitoring_contract_planned | Hypothesis | `storage.reason.planned_group_not_observed` | provenance |"),
    ("| `storage.state.soc` | `storage.dimension.pack` | `site_battery_soc` | U16, %, gain 100 | none | Hypothesis |", "| `storage.state.soc` | `storage.dimension.pack` | `site_battery_soc` | U16, %, gain 10 | none | Hypothesis |"),
    ("| `storage.pack.power` | `storage.dimension.pack` | `site_battery_power` | I32, kW, gain 1000 | `unknown_no_value_without_a_graded_sign` | Hypothesis |", "| `storage.pack.power` | `storage.dimension.pack` | `site_battery_power` | I32, kW, gain 1000 | `positive_while_charging_negative_while_discharging` | Hypothesis |"),
    ("| `STG-NEG-010-error-precedence` |", "| `STG-NEG-099-other` |"),
    ("Capacity in energy units is withheld", "Capacity in energy units is published"),
    ("never converted", "converted"),
    ("outbound_allowed=false", "outbound allowed"),
])
def test_page_must_match_the_contract(old, new):
    pattern = re.escape(old).replace(r"\ ", r"\s+")
    mutated, count = re.subn(pattern, lambda _: new, page())
    assert count >= 1
    with raises(ValueError):
        v.check_document(v.load(), mutated)


def test_a_dropped_table_row_is_rejected():
    for prefix in ("| `battery_group_37066_4` |", "| `storage.energy.discharged` |"):
        lines = [line for line in page().splitlines(keepends=True) if not line.startswith(prefix)]
        with raises(ValueError, match="document tables"):
            v.check_document(v.load(), "".join(lines))


@parametrize("literal", ["b" * 40, "0123456789abcdef" * 4, "F0" * 20])
def test_publication_rule_rejects_revision_and_digest_literals(literal):
    with raises(ValueError, match="publication"):
        v.check_document(v.load(), page() + "\n" + literal + "\n")


def test_published_files_cite_no_revision_link_or_endpoint():
    for path in (v.PATH, v.DOC):
        text = path.read_text(encoding="utf-8")
        assert not v.HEX_RUN_RE.search(text)
        assert "/blob/" not in text and "/commit/" not in text and "#L" not in text and "tcp://" not in text


if __name__ == "__main__":
    raise SystemExit(support.run(globals()))
