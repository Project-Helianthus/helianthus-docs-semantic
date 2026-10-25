#!/usr/bin/env python3
"""Mutation controls for the Huawei gateway-meter Infrastructure gate (run with python3 -m pytest)."""
import copy
import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_huawei_gateway_meter_infrastructure_mapping", ROOT / "scripts/validate_huawei_gateway_meter_infrastructure_mapping.py")
v = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v
SPEC.loader.exec_module(v)


def contract():
    return copy.deepcopy(v.load())


def case():
    return copy.deepcopy(v.load()["baselines"]["default"])


def set_path(document, path, value):
    v.mutate(document, {"path": path, "value": value})


def project(document):
    return v.project(document, v.load())


def test_gate_passes_with_its_page():
    document = v.load()
    v.document(document)
    v.check_document(document, v.DOC.read_text(encoding="utf-8"))


def test_no_binary_floating_point():
    with pytest.raises(ValueError, match="binary floating point"):
        v.loads('{"gain": 1000.0}')
    float_case = case()
    float_case["routed_unit"] = 11.0
    with pytest.raises(ValueError):
        project(float_case)
    document = contract()
    set_path(document, "admission.decoded_meter_words", 0.0)
    with pytest.raises(ValueError):
        v.validate_contract(document)


@pytest.mark.parametrize("name,mutation,message", [
    ("pack", lambda d: set_path(d, "pack.id", "helianthus.pack.pv"), "contract"),
    ("pack-version", lambda d: set_path(d, "pack.version", "1.1.0"), "contract"),
    ("status", lambda d: set_path(d, "status", "accepted_source_specific_read_only_mapping_gate"), "contract"),
    ("evidence-amendment", lambda d: set_path(d, "evidence.meter_observation_amendment.issue", 255), "evidence"),
    ("evidence-page", lambda d: d["evidence"]["monitoring_contract"]["pages"].pop(), "evidence"),
    ("class-contract-claimed", lambda d: set_path(d, "admission.meter_class_contract", True), "admission"),
    ("meter-identity-claimed", lambda d: set_path(d, "admission.meter_identity", "PROFILE_SELECTED"), "admission"),
    ("decoded-words", lambda d: set_path(d, "admission.decoded_meter_words", 4), "admission"),
    ("meter-selectable", lambda d: d["admission"]["selection_outcomes_allowed"].append("PROFILE_SELECTED"), "admission"),
    ("precondition-dropped", lambda d: v.mutate(d, {"path": "admission.preconditions_for_any_mapping.3", "remove": True}), "admission"),
    ("role-derived", lambda d: d["role"]["never_derived_from"].remove("sign_or_magnitude_of_a_power_value"), "role"),
    ("role-default", lambda d: set_path(d, "role.undeclared", "assume_grid_connection"), "role"),
    ("role-value-added", lambda d: d["role"]["values"].append("consumption"), "role"),
    ("role-feeder-power", lambda d: set_path(d, "role.dimension_by_role.feeder.power", "infrastructure.dimension.grid_connection"), "role"),
    ("role-energy-dimension", lambda d: set_path(d, "role.dimension_by_role.grid_connection.energy", "infrastructure.dimension.grid_connection"), "role"),
    ("native-item-dropped", lambda d: v.mutate(d, {"path": "field_rules.3", "remove": True}), "native inventory"),
    ("native-item-duplicated", lambda d: d["field_rules"].append(copy.deepcopy(d["field_rules"][0])), "native inventory"),
    ("native-item-added", lambda d: d["field_rules"].append({**copy.deepcopy(d["field_rules"][0]), "native_id": "meter_voltage_group"}), "native inventory"),
    ("native-item-path", lambda d: set_path(d, "field_rules.0.gateway_path", "emma"), "native inventory"),
    ("outcome-mapped", lambda d: set_path(d, "field_rules.0.disposition.outcome", "exact"), "withheld reason"),
    ("withheld-without-reason", lambda d: v.mutate(d, {"path": "field_rules.0.disposition.reason", "remove": True}), "withheld reason"),
    ("withheld-unknown-reason", lambda d: set_path(d, "field_rules.0.disposition.reason", "infrastructure.reason.invented"), "withheld reason"),
    ("grade", lambda d: set_path(d, "field_rules.0.grade", "certain"), "withheld reason"),
    ("prospective-in-force", lambda d: set_path(d, "field_rules.0.prospective.0.in_force", True), "prospective target"),
    ("prospective-target-not-in-pack", lambda d: set_path(d, "field_rules.0.prospective.0.target", "infrastructure.power.net_active"), "prospective target"),
    ("prospective-unit", lambda d: set_path(d, "field_rules.0.prospective.0.unit", "unit.kilowatt_hour"), "prospective target"),
    ("prospective-dimension", lambda d: set_path(d, "field_rules.0.prospective.0.dimension", "infrastructure.dimension.meter"), "prospective target"),
    ("prospective-native-unit", lambda d: set_path(d, "field_rules.0.prospective.0.native.unit", "MW"), "prospective target"),
    ("prospective-role", lambda d: v.mutate(d, {"path": "field_rules.0.prospective.0.role", "remove": True}), "prospective role"),
    ("prospective-role-feeder", lambda d: set_path(d, "field_rules.0.prospective.0.role", "feeder"), "prospective role"),
    ("prospective-sign-assumed", lambda d: set_path(d, "field_rules.0.prospective.0.sign_reference", "positive_export_assumed"), "prospective sign"),
    ("prospective-sign-removed", lambda d: v.mutate(d, {"path": "field_rules.5.prospective.0.sign_reference", "remove": True}), "prospective sign"),
    ("prospective-direction", lambda d: set_path(d, "field_rules.1.prospective.0.direction", "guessed"), "prospective counter"),
    ("prospective-counter", lambda d: set_path(d, "field_rules.1.prospective.0.counter", "delta_published"), "prospective counter"),
    ("requested-added", lambda d: d["projection"]["requested_items"].append({"kind": "fact", "item_id": "infrastructure.status.breaker"}), "requested items"),
    ("requested-dropped", lambda d: v.mutate(d, {"path": "projection.requested_items.0", "remove": True}), "requested items"),
    ("reason-unused", lambda d: d["reasons"].update({"infrastructure.reason.unused": {"loss_kind": "policy", "description": "x", "reversible": True}}), "reason inventory"),
    ("reason-primary-removed", lambda d: d["reasons"].pop("infrastructure.reason.no_meter_class_contract"), "withheld reason"),
    ("identity-asset-allowed", lambda d: set_path(d, "identity.meter_asset_id", "meter-asset-demo"), "identity contract"),
    ("identity-forbidden", lambda d: set_path(d, "identity.source_id.forbidden_derivations.0", "vendor"), "identity contract"),
    ("lifecycle-zero", lambda d: set_path(d, "lifecycle.absent_optional_group", "zero"), "lifecycle contract"),
    ("lifecycle-negation", lambda d: set_path(d, "lifecycle.exception", "negates_the_gateway"), "lifecycle contract"),
    ("outcome-vocabulary", lambda d: set_path(d, "outcome_vocabulary.native_only", "exact"), "outcome vocabulary"),
    ("unsupported-dropped", lambda d: v.mutate(d, {"path": "unsupported.1", "remove": True}), "unsupported"),
    ("primary-reason", lambda d: set_path(d, "projection.primary_reason", "infrastructure.reason.answered_not_decoded"), "projection"),
    ("precedence", lambda d: set_path(d, "projection.error_precedence.3", "lifecycle_missing"), "projection"),
    ("operations", lambda d: set_path(d, "projection.operations", "allowed"), "projection"),
    ("consumer", lambda d: set_path(d, "consumer_cutover.until_implemented", "public_binding"), "consumer cutover"),
])
def test_contract_mutations_are_rejected(name, mutation, message):
    document = contract()
    mutation(document)
    with pytest.raises(ValueError) as error:
        v.validate_contract(document)
    assert message in str(error.value)


@pytest.mark.parametrize("field,value", [("loss_kind", "native_enum"), ("description", ""), ("reversible", "yes")])
def test_every_reason_declares_its_loss(field, value):
    document = contract()
    document["reasons"]["infrastructure.reason.profile_withholds_meter"][field] = value
    with pytest.raises(ValueError, match="reason loss"):
        v.validate_contract(document)


def test_every_native_item_has_exactly_one_withheld_disposition_and_nothing_is_published():
    document = v.load()
    assert [rule["native_id"] for rule in document["field_rules"]] == [nid for nid, _ in v.INVENTORY]
    for scenario in document["scenarios"]:
        if scenario["polarity"] != "positive":
            continue
        output = v.run_scenario(scenario, document)
        assert [row["native_id"] for row in output["native_dispositions"]] == [nid for nid, _ in v.INVENTORY]
        assert {row["outcome"] for row in output["native_dispositions"]} == {"withheld"}
        assert output["facts"] == [] and output["relationships"] == [] and output["operations"] == []
        assert [item["outcome"] for item in output["dispositions"]] == ["withheld"] * 8
        assert all(item["source_keys"] == [] and item["reason"] == v.PRIMARY_REASON and item["loss"] for item in output["dispositions"])


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
            broken["native_dispositions"][0]["reason"] = "infrastructure.reason.invented"
        with pytest.raises(ValueError):
            v.assert_complete(broken, document)


def test_an_answering_group_is_neither_a_value_nor_an_identity():
    document = case()
    document["reads"] = [{"native_id": native_id, "outcome": "ANSWERED"} for native_id in v.FEEDABLE]
    output = project(document)
    assert output["facts"] == []
    rows = {row["native_id"]: row["reason"] for row in output["native_dispositions"]}
    assert all(rows[native_id] == "infrastructure.reason.answered_not_decoded" for native_id in v.FEEDABLE)
    assert rows["sun2000_inverter_exposed_meter_group_refused"] == "infrastructure.reason.refused_on_family"
    assert rows["profile_meter_groups"] == "infrastructure.reason.profile_withholds_meter"


@pytest.mark.parametrize("read", [
    {"native_id": "sdongle_plant_grid_power", "outcome": "ANSWERED", "words": [0, 1200]},
    {"native_id": "sdongle_plant_grid_power", "outcome": "ANSWERED", "value": 1200},
    {"native_id": "sdongle_plant_grid_power", "outcome": "EXCEPTION"},
    {"native_id": "sdongle_plant_grid_power", "outcome": "ANSWERED", "exception_code": 3},
    {"native_id": "sdongle_plant_grid_power", "outcome": "TIMEOUT"},
    {"native_id": "sun2000_inverter_exposed_meter_group_refused", "outcome": "ANSWERED"},
    {"native_id": "profile_meter_groups", "outcome": "ANSWERED"},
    {"native_id": "invented_meter_group", "outcome": "ANSWERED"},
    {"outcome": "ANSWERED"},
    None,
])
def test_invalid_reads_are_rejected(read):
    document = case()
    document["reads"] = [read]
    with pytest.raises(ValueError, match="native_evidence_invalid"):
        project(document)


def test_a_duplicate_read_is_rejected():
    document = case()
    read = {"native_id": "emma_built_in_sensor_group", "outcome": "FAILED"}
    document["reads"] = [read, copy.deepcopy(read)]
    with pytest.raises(ValueError, match="native_evidence_invalid"):
        project(document)


def test_an_exception_negates_nothing_and_publishes_no_value():
    document = case()
    document["reads"] = [{"native_id": "emma_built_in_sensor_group", "outcome": "EXCEPTION", "exception_code": 3}, {"native_id": "emma_external_sensor_group", "outcome": "NOT_READ"}]
    rows = {row["native_id"]: row["reason"] for row in project(document)["native_dispositions"]}
    assert rows["emma_built_in_sensor_group"] == "infrastructure.reason.read_exception_no_negation"
    assert rows["emma_external_sensor_group"] == "infrastructure.reason.no_meter_class_contract"


@pytest.mark.parametrize("declared,expected", [
    ("grid_connection", {"power": "infrastructure.dimension.grid_connection", "energy": "infrastructure.dimension.meter", "relationship": "infrastructure.relationship.grid_connection_meter"}),
    ("feeder", {"power": "withheld", "energy": "infrastructure.dimension.meter", "relationship": "none_decided"}),
    ("circuit", {"power": "withheld", "energy": "infrastructure.dimension.meter", "relationship": "none_decided"}),
    (None, "role_unknown_role_dependent_facts_not_published"),
])
def test_the_configured_role_selects_the_dimension_and_publishes_nothing(declared, expected):
    document = case()
    document["role"]["declared"] = declared
    output = project(document)
    assert output["role"]["dimension_if_admitted"] == expected and output["role"]["declared"] == declared
    assert output["role"]["keyed_to"] == {"source_id": "source:gateway-demo-d", "routed_unit": 11}
    assert output["facts"] == []


@pytest.mark.parametrize("role", [
    {"declared": "grid_connection", "source": "derived_from_power_sign"}, {"declared": "grid_connection", "source": "derived_from_registers"},
    {"declared": "grid_connection", "source": "listing_label"}, {"declared": "grid_connection"}, {"declared": "consumption", "source": "operator_configuration"},
    {"declared": "", "source": "operator_configuration"}, {"declared": ["grid_connection"], "source": "operator_configuration"}, None, "grid_connection",
])
def test_a_role_is_configuration_and_never_derived(role):
    document = case()
    document["role"] = role
    with pytest.raises(ValueError, match="role_invalid"):
        project(document)


@pytest.mark.parametrize("unit", [0, 248, -1, True, "11", 11.5])
def test_the_routed_unit_that_keys_the_role_is_bounded(unit):
    document = case()
    document["routed_unit"] = unit
    with pytest.raises(ValueError):
        project(document)


@pytest.mark.parametrize("outcome,message", [("PROFILE_SELECTED", "gate_revision_required"), ("INSUFFICIENT_EVIDENCE", None), ("NO_ADMISSIBLE_PROFILE", None), ("AMBIGUOUS", None), ("", "native_evidence_invalid"), (None, "native_evidence_invalid")])
def test_a_selected_meter_fails_closed(outcome, message):
    document = case()
    document["selection"]["outcome"] = outcome
    if message is None:
        project(document)
        return
    with pytest.raises(ValueError, match=message):
        project(document)


def test_a_meter_identity_is_never_claimed():
    for identity in ({"asset_id": "meter-asset-demo-delta"}, {"asset_id": ""}, {"asset_id": None}):
        document = case()
        document["identity"] = identity
        with pytest.raises(ValueError, match="gate_revision_required"):
            project(document)


@pytest.mark.parametrize("source", ["", None, "source gateway", "source:serial-1", "source:ESN-1", "source:10.1.2.3", "source:host:502", "11", "source:meter-huawei", "source:emma-a"])
def test_source_identifier_never_comes_from_forbidden_inputs(source):
    document = case()
    document["source"]["source_id"] = source
    with pytest.raises(ValueError, match="identity_missing_or_invalid"):
        project(document)


@pytest.mark.parametrize("path,value", [("lifecycle.observation_id", ""), ("lifecycle.observation_revision", 0), ("lifecycle.receipt_wall", "2026-01-01T00:00:00"), ("lifecycle.receipt_monotonic", None), ("lifecycle.clock_epoch", "bad epoch"), ("lifecycle.source_epoch", None), ("lifecycle.driver_generation", True), ("lifecycle.connection_generation", 0)])
def test_every_lifecycle_axis_is_required(path, value):
    document = case()
    set_path(document, path, value)
    with pytest.raises(ValueError, match="lifecycle_missing"):
        project(document)


@pytest.mark.parametrize("flag", sorted(v.REGISTRY_FLAGS) + ["mapping_qualified", "outbound_allowed"])
def test_every_qualification_flag_is_pinned(flag):
    document = case()
    document["qualification"][flag] = not document["qualification"][flag]
    with pytest.raises(ValueError, match="mapping_unqualified"):
        project(document)


@pytest.mark.parametrize("member,value", [("request_operation", "any"), ("request_direction_split", "signed_power_to_import_export"), ("request_mixed_sign_references", True)])
def test_no_operation_split_or_mixed_sign_is_available(member, value):
    document = case()
    document[member] = value
    with pytest.raises(ValueError, match="unsupported_or_withheld"):
        project(document)


def test_first_error_of_the_precedence_list_wins():
    document = case()
    document["selection"]["outcome"] = "PROFILE_SELECTED"
    document["source"]["source_id"] = ""
    document["role"] = {"declared": "x", "source": "y"}
    document["request_operation"] = "any"
    with pytest.raises(ValueError, match="gate_revision_required"):
        project(document)
    document["selection"]["outcome"] = "AMBIGUOUS"
    document["reads"] = [{"native_id": "invented", "outcome": "ANSWERED"}]
    with pytest.raises(ValueError, match="native_evidence_invalid"):
        project(document)
    document["reads"] = []
    with pytest.raises(ValueError, match="identity_missing_or_invalid"):
        project(document)
    document["source"]["source_id"] = "source:gateway-demo-d"
    with pytest.raises(ValueError, match="role_invalid"):
        project(document)


def test_prospective_rows_are_not_in_force_and_match_the_pack():
    fields, dimensions, relationships = v.pack_catalog()
    document = v.load()
    for rule in document["field_rules"]:
        for row in rule.get("prospective", []):
            assert row["in_force"] is False
            assert row["dimension"] == fields[row["target"]]["dimension"] and row["unit"] == fields[row["target"]]["unit"]
            if row["dimension"] == "infrastructure.dimension.grid_connection":
                assert row["role"] == "grid_connection"
    refs = {rule["native_id"]: {row["sign_reference"] for row in rule.get("prospective", []) if "sign_reference" in row} for rule in document["field_rules"]}
    assert refs["sdongle_plant_grid_power"] == {"positive_import"} and refs["sdongle_inverter_exposed_meter_group"] == {"positive_export"} and refs["smartlogger_meter_electrical_group"] == {"not_stated"}
    assert not any(token in str(document["field_rules"]) for token in ("infrastructure.status.", "operation"))


def test_scenario_expectations_are_executed_not_trusted():
    for damage, message in (
        (lambda d: d["scenarios"][0]["expect"]["output"]["role"].update({"declared": "feeder"}), "scenario output"),
        (lambda d: d["scenarios"][3]["expect"]["summary"]["native_dispositions"].pop(), "scenario summary"),
        (lambda d: d["scenarios"][-1]["expect"].update({"error": "lifecycle_missing"}), "gate_revision_required"),
    ):
        document = contract()
        damage(document)
        with pytest.raises(ValueError) as error:
            v.validate_scenarios(document)
        assert message in str(error.value)


def test_scenario_coverage_is_enforced():
    for dropped, message in ((("MTR-POS-004-groups-answer-nothing-decoded",), "cover every reason"), (("MTR-POS-005-meter-read-exception",), "cover every reason"), (("MTR-NEG-007-role-derived-from-sign", "MTR-NEG-008-role-outside-set"), "cover every error")):
        document = contract()
        document["scenarios"] = [s for s in document["scenarios"] if s["id"] not in dropped]
        with pytest.raises(ValueError, match=message):
            v.validate_scenarios(document)


def test_a_negative_scenario_that_is_accepted_fails():
    document = contract()
    next(s for s in document["scenarios"] if s["id"] == "MTR-NEG-006-source-missing")["mutations"] = []
    with pytest.raises(ValueError, match="accepted"):
        v.validate_scenarios(document)


def page():
    return v.DOC.read_text(encoding="utf-8")


@pytest.mark.parametrize("old,new", [
    ("| `emma_external_sensor_group` | emma | Unknown | `infrastructure.reason.no_meter_class_contract` | policy |", "| `emma_external_sensor_group` | emma | Proven | `infrastructure.reason.no_meter_class_contract` | policy |"),
    ("| `infrastructure.power.import_active` | `infrastructure.dimension.grid_connection` | `sdongle_plant_grid_power` | I32, kW, gain 1000 | `positive_import` | `grid_connection` |", "| `infrastructure.power.import_active` | `infrastructure.dimension.grid_connection` | `sdongle_plant_grid_power` | I32, kW, gain 1000 | `positive_export` | `grid_connection` |"),
    ("| `feeder` | withheld | `infrastructure.dimension.meter` | none decided |", "| `feeder` | `infrastructure.dimension.grid_connection` | `infrastructure.dimension.meter` | none decided |"),
    ("| `MTR-NEG-014-error-precedence` |", "| `MTR-NEG-099-other` |"),
    ("role is configuration", "role is derived"),
    ("no meter register is decoded", "a meter register is decoded"),
    ("outbound_allowed=false", "outbound allowed"),
])
def test_page_must_match_the_contract(old, new):
    pattern = re.escape(old).replace(r"\ ", r"\s+")
    mutated, count = re.subn(pattern, lambda _: new, page())
    assert count >= 1
    with pytest.raises(ValueError):
        v.check_document(v.load(), mutated)


def test_a_dropped_table_row_is_rejected():
    for prefix in ("| `profile_meter_groups` |", "| `circuit` |"):
        lines = [line for line in page().splitlines(keepends=True) if not line.startswith(prefix)]
        with pytest.raises(ValueError, match="document tables"):
            v.check_document(v.load(), "".join(lines))


@pytest.mark.parametrize("literal", ["c" * 40, "0123456789abcdef" * 4, "E1" * 20])
def test_publication_rule_rejects_revision_and_digest_literals(literal):
    with pytest.raises(ValueError, match="publication"):
        v.check_document(v.load(), page() + "\n" + literal + "\n")


def test_published_files_cite_no_revision_link_or_endpoint():
    for path in (v.PATH, v.DOC):
        text = path.read_text(encoding="utf-8")
        assert not v.HEX_RUN_RE.search(text)
        assert "/blob/" not in text and "/commit/" not in text and "#L" not in text and "tcp://" not in text
