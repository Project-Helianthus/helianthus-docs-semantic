#!/usr/bin/env python3
"""Validate exact typed associations in the EVSE v1 catalog."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/packs/evse-acceptance-vectors.json"
DOCUMENT = ROOT / "api/v1/packs/evse-v1.md"
PACK = {"id": "helianthus.pack.evse", "version": "1.0.0"}
ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
DOMAINS = {"thermal_hvac": ("helianthus.pack.thermal", "accepted"),
           "pv_inverter": ("helianthus.pack.pv", "accepted"),
           "storage_bms": ("helianthus.pack.storage", "accepted"),
           "evse": ("helianthus.pack.evse", "accepted"),
           "infrastructure": ("helianthus.pack.infrastructure", "follow_on")}
PINS = {"semantic_docs": "f81f04b026ccfc0bb4107c5a361e7bee146a166a",
        "semreg": "cc9b324225e945598128eeabe977e7fa0af6dc93",
        "tesla_docs_modbus": "d16ff91ff808803fa31c67a6a10eb2a4faa70937",
        "tesla_modbusreg": "75e4e3988a7682068c02d8ac24f737b7f24a029f",
        "eebus_ledger": "81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1",
        "eebus_m625_donor": "cedf238e34f879815ba773e9cd76b2b31c2822a3",
        "matter_draft": "29b4768a513cf566011ab8cd60df1bc495204953"}
LIFECYCLE = {"source_epoch", "driver_generation", "semantic_revision",
             "capability_qualification", "activation", "generation_fencing",
             "partial_updates", "stale_unknown_evidence", "last_known_good_retention"}
POLICY = {"admission": ["exact_source_epoch", "current_driver_generation",
                          "exact_semantic_revision", "qualified_active_capability"],
          "stale_generation": "reject",
          "partial_publication": "supplied_valid_only_preserve_permitted_last_known_good",
          "withdrawal": "explicit_generation_fenced",
          "evidence": "stale_unknown_never_promote_or_authorize",
          "tombstone": "retained_non_actionable"}
COUNTER = {"session_and_lifetime_energy": "native_reset_or_wrap_evidence_required",
           "decrease": "never_infer_reset_or_wrap",
           "projection": "counter_continuity_or_loss_explicit"}
AVAILABILITY = {"effective_availability": "kernel_observation_and_capability_state_only",
                "native_readiness": "evse.status.readiness",
                "portal": "consume_kernel_availability_separately"}
LOSS = {"native_enum_bitfield", "precision_range", "connector_phase_session_meter_topology",
        "direction_reference", "counter_reset_wrap", "unavailable_fields",
        "conflicting_sources", "vendor_extensions", "unsupported_operations"}
DIMS = {"evse.dimension.asset", "evse.dimension.evse", "evse.dimension.connector",
        "evse.dimension.phase", "evse.dimension.session", "evse.dimension.meter"}
FIELD_CONTRACTS = {
    "evse.ac.voltage": ("quantity", "unit.volt", "evse.dimension.phase", True, None, ("0", 0, "1", 3)),
    "evse.ac.current": ("quantity", "unit.ampere", "evse.dimension.phase", True, None, ("0", 0, "1", 3)),
    "evse.ac.active_power": ("quantity", "unit.watt", "evse.dimension.phase", True, None, ("-1", 7, "1", 7)),
    "evse.ac.frequency": ("quantity", "unit.hertz", "evse.dimension.evse", True, None, ("0", 0, "1", 3)),
    "evse.energy.session": ("quantity", "unit.kilowatt_hour", "evse.dimension.session", True, None, ("0", 0, "1", 12)),
    "evse.energy.lifetime": ("quantity", "unit.kilowatt_hour", "evse.dimension.meter", True, None, ("0", 0, "1", 12)),
    "evse.limit.advertised_current": ("quantity", "unit.ampere", "evse.dimension.connector", True, None, ("0", 0, "1", 3)),
    "evse.limit.configured_current": ("quantity", "unit.ampere", "evse.dimension.evse", True, None, ("0", 0, "1", 3)),
    "evse.limit.allocated_current": ("quantity", "unit.ampere", "evse.dimension.connector", True, None, ("0", 0, "1", 3)),
    "evse.limit.actual_current": ("quantity", "unit.ampere", "evse.dimension.connector", True, None, ("0", 0, "1", 3)),
    "evse.status.connection": ("symbol", None, "evse.dimension.connector", True, ("evse.status.connection.connected", "evse.status.connection.disconnected"), None),
    "evse.status.charging": ("symbol", None, "evse.dimension.connector", True, ("evse.status.charging.charging", "evse.status.charging.complete", "evse.status.charging.idle"), None),
    "evse.status.readiness": ("symbol", None, "evse.dimension.evse", True, ("evse.status.readiness.not_ready", "evse.status.readiness.ready"), None),
    "evse.status.fault": ("symbol", None, "evse.dimension.evse", True, ("evse.status.fault.clear", "evse.status.fault.present"), None),
    "evse.status.interlock": ("symbol", None, "evse.dimension.connector", True, ("evse.status.interlock.active", "evse.status.interlock.clear"), None),
}
SERVICES = {"evse.service.evse": "evse.dimension.evse",
            "evse.service.connector": "evse.dimension.connector",
            "evse.service.phase": "evse.dimension.phase",
            "evse.service.session": "evse.dimension.session",
            "evse.service.meter": "evse.dimension.meter"}
RELATIONSHIPS = {"evse.relationship.asset_evse": ("evse.dimension.asset", "evse.dimension.evse", "one_to_many"),
                 "evse.relationship.evse_connector": ("evse.dimension.evse", "evse.dimension.connector", "one_to_many"),
                 "evse.relationship.connector_phase": ("evse.dimension.connector", "evse.dimension.phase", "one_to_many"),
                 "evse.relationship.connector_session": ("evse.dimension.connector", "evse.dimension.session", "one_to_many_over_time"),
                 "evse.relationship.evse_meter": ("evse.dimension.evse", "evse.dimension.meter", "one_to_many")}
CAPS = {"evse.capability.read.evse": ("evse.service.evse", ()),
        "evse.capability.read.connector": ("evse.service.connector", ()),
        "evse.capability.read.phase": ("evse.service.phase", ()),
        "evse.capability.read.session": ("evse.service.session", ()),
        "evse.capability.read.meter": ("evse.service.meter", ()),
        "evse.capability.set_allocated_current": ("evse.service.connector", ("evse.limit.allocated_current",))}
OP = "evse.operation.set_allocated_current"
EFFECT = "evse.effect.set_allocated_current"
PRECONDITIONS = ["current_source_epoch", "current_driver_generation", "current_semantic_revision", "qualified_active_capability", "exact_route", "authority_admitted"]
STAGES = ["admission", "dispatch", "acknowledgement", "readback", "terminal_outcome"]
OUTCOMES = ["rejected", "failed_no_contact", "acknowledged_unverified", "applied", "no_effect", "conflict", "indeterminate"]
PORTAL_READS = {"evse.portal.read.evse": ("evse.service.evse", ("evse.ac.frequency", "evse.limit.configured_current", "evse.status.fault", "evse.status.readiness")),
                "evse.portal.read.connector": ("evse.service.connector", ("evse.limit.actual_current", "evse.limit.advertised_current", "evse.limit.allocated_current", "evse.status.charging", "evse.status.connection", "evse.status.interlock")),
                "evse.portal.read.phase": ("evse.service.phase", ("evse.ac.active_power", "evse.ac.current", "evse.ac.voltage")),
                "evse.portal.read.session": ("evse.service.session", ("evse.energy.session",)),
                "evse.portal.read.meter": ("evse.service.meter", ("evse.energy.lifetime",))}
MAPPINGS = {
    "evse.mapping.tesla.legacy_fbe0_fde0": {"id":"evse.mapping.tesla.legacy_fbe0_fde0","native_owner":"helianthus-docs-modbus","source_refs":["tesla_docs_modbus","tesla_modbusreg"],"state":"candidate","qualification":"offline_family_compatible_only","provenance":["legacy_fbe0","legacy_fde0"],"allocated_current":"native_candidate","actual_current":"native_candidate_separate","relative_or_unknown_state":"native_only_no_absolute_allocation","sender":"none","control_route":"none","live_authority":False,"loss":"unknown"},
    "evse.mapping.eebus": {"id":"evse.mapping.eebus","native_owner":"helianthus-docs-eebus","source_refs":["eebus_ledger","eebus_m625_donor"],"state":"unknown_pending_std_01","qualification":"unresolved","loss":"unknown"},
    "evse.mapping.matter": {"id":"evse.mapping.matter","native_owner":"matter_draft","source_refs":["matter_draft"],"state":"candidate_design_input_only","qualification":"not_conformance","loss":"unknown"},
}


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_document(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source, object_pairs_hook=pairs)


def exact(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label} differs")


def refs(items, label, expected):
    if not isinstance(items, list) or not items:
        raise ValueError(f"{label} must be non-empty")
    ids, orders = [], []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"]):
            raise ValueError(f"{label} invalid ID")
        if item.get("ref") != {"pack": PACK, "id": item["id"], "version": "1.0.0"}:
            raise ValueError(f"{label} missing exact DefinitionRef owner/version")
        ids.append(item["id"])
        orders.append(item.get("order"))
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate definition ID in {label}")
    if not all(type(order) is int and order > 0 for order in orders) or orders != sorted(orders) or len(orders) != len(set(orders)):
        raise ValueError(f"{label} noncanonical order")
    exact(set(ids), set(expected), f"{label} catalog")
    return {item["id"]: item for item in items}


def decimal(value):
    if not isinstance(value, dict) or set(value) != {"coefficient", "exponent10"}:
        raise ValueError("bounds must use canonical kernel Decimal")
    coefficient, exponent = value["coefficient"], value["exponent10"]
    if not isinstance(coefficient, str) or not re.fullmatch(r"0|-?[1-9][0-9]*", coefficient) or type(exponent) is not int or not -18 <= exponent <= 18 or (coefficient == "0" and exponent != 0) or (coefficient != "0" and coefficient.endswith("0")):
        raise ValueError("bounds must use canonical kernel Decimal")
    return int(coefficient), exponent


def decimal_less(left, right):
    lc, le = decimal(left)
    rc, rexp = decimal(right)
    shared = min(le, rexp)
    return lc * 10 ** (le - shared) < rc * 10 ** (rexp - shared)


def validate_fields(fields):
    records = refs(fields, "fields", FIELD_CONTRACTS)
    for identifier, field in records.items():
        kind, unit, dimension, optional, symbols, bounds = FIELD_CONTRACTS[identifier]
        base = {"id", "ref", "kind", "dimension", "optional", "order"}
        if field.get("kind") != kind or field.get("dimension") != dimension or type(field.get("optional")) is not bool or field["optional"] != optional:
            raise ValueError("field has noncanonical kind, dimension, or optionality")
        if kind == "quantity":
            minimum = {"coefficient": bounds[0], "exponent10": bounds[1]}
            maximum = {"coefficient": bounds[2], "exponent10": bounds[3]}
            if set(field) != base | {"unit", "bounds"} or field.get("unit") != unit or not decimal_less(field.get("bounds", {}).get("minimum"), field.get("bounds", {}).get("maximum")) or field.get("bounds") != {"minimum": minimum, "maximum": maximum}:
                raise ValueError("field has invalid canonical quantity contract")
        elif set(field) != base | {"symbols"} or tuple(field.get("symbols", ())) != symbols or field.get("symbols") != sorted(field.get("symbols", [])) or any(not isinstance(value, str) or not ID.fullmatch(value) for value in field["symbols"]):
            raise ValueError("field has invalid canonical symbol contract")
    return records


def validate_defs(catalog):
    definitions = catalog.get("definitions", {})
    fields = validate_fields(definitions.get("fields"))
    dimensions = refs(definitions.get("fact_dimensions"), "fact dimensions", DIMS)
    if any(item.get("value_kind") != "text" or set(item) != {"id", "ref", "value_kind", "order"} for item in dimensions.values()):
        raise ValueError("dimension association")
    services = refs(definitions.get("services"), "services", SERVICES)
    if any(item.get("fact_key_dimension") != SERVICES[key] or set(item) != {"id", "ref", "fact_key_dimension", "order"} for key, item in services.items()):
        raise ValueError("service association")
    relationships = refs(definitions.get("relationships"), "relationships", RELATIONSHIPS)
    if any((item.get("from"), item.get("to"), item.get("cardinality")) != RELATIONSHIPS[key] or set(item) != {"id", "ref", "from", "to", "cardinality", "order"} for key, item in relationships.items()):
        raise ValueError("relationship association")
    capabilities = refs(definitions.get("capabilities"), "capabilities", CAPS)
    for key, item in capabilities.items():
        service, constraints = CAPS[key]
        expected = {"id", "ref", "service", "activation", "order"} | ({"constraints"} if constraints else set())
        if item.get("service") != service or tuple(item.get("constraints", ())) != constraints or item.get("activation") != "qualified_current_binding" or set(item) != expected:
            raise ValueError("capability association")
    operations = refs(definitions.get("operations"), "operations", {OP})
    operation = operations[OP]
    if set(operation) != {"id", "ref", "capability", "arguments", "argument_constraints", "effect_rule", "preconditions", "stages", "terminal_outcomes", "readback", "retry", "order"} or (operation.get("capability"), tuple(operation.get("arguments", ())), tuple(operation.get("argument_constraints", ())), operation.get("effect_rule")) != ("evse.capability.set_allocated_current", ("evse.limit.allocated_current",), ("evse.limit.allocated_current",), EFFECT) or operation.get("preconditions") != PRECONDITIONS or operation.get("stages") != STAGES or operation.get("terminal_outcomes") != OUTCOMES or operation.get("readback") != "current_generation_exact_effect" or operation.get("retry") != "forbidden_after_indeterminate":
        raise ValueError("operation safety")
    effects = refs(definitions.get("effect_rules"), "effect rules", {EFFECT})
    effect = effects[EFFECT]
    if set(effect) != {"id", "ref", "operation", "fact", "operator", "order"} or (effect.get("operation"), effect.get("fact"), effect.get("operator")) != (OP, "evse.limit.allocated_current", "equal"):
        raise ValueError("effect association")
    portal = refs(definitions.get("portal_contributions"), "Portal contributions", set(PORTAL_READS) | {"evse.portal.operation.set_allocated_current"})
    coverage = set()
    for key, item in portal.items():
        if key in PORTAL_READS:
            service, facts = PORTAL_READS[key]
            if item.get("kind") != "read" or item.get("service") != service or tuple(item.get("fields", ())) != facts or set(item) != {"id", "ref", "kind", "service", "fields", "order"}:
                raise ValueError("Portal read association")
            coverage.update(facts)
        elif item.get("kind") != "operation" or item.get("operation") != OP or item.get("admission") != "current_only" or set(item) != {"id", "ref", "kind", "operation", "admission", "order"}:
            raise ValueError("Portal operation association")
    exact(coverage, set(fields), "Portal read field coverage")


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get("pack") != PACK or catalog.get("kernel_contract") != "helianthus.semantic.kernel/v1" or catalog.get("status") != "accepted":
        raise ValueError("catalog lacks exact PackRef")
    exact({item.get("id"): (item.get("pack"), item.get("state")) for item in catalog.get("domain_catalog", []) if isinstance(item, dict)}, DOMAINS, "five-domain catalog")
    exact({item.get("id"): item.get("revision") for item in catalog.get("inputs", []) if isinstance(item, dict)}, PINS, "pinned public inputs")
    if set(catalog.get("lifecycle_axes", [])) != LIFECYCLE:
        raise ValueError("lifecycle axes")
    exact(catalog.get("publication_withdrawal_policy"), POLICY, "publication/withdrawal policy")
    exact(catalog.get("counter_policy"), COUNTER, "counter policy")
    exact(catalog.get("availability_policy"), AVAILABILITY, "availability policy")
    if set(catalog.get("loss_dispositions", [])) != LOSS:
        raise ValueError("projection-loss coverage")
    rows = catalog.get("candidate_mappings")
    if not isinstance(rows, list) or len({row.get("id") for row in rows if isinstance(row, dict)}) != len(rows):
        raise ValueError("native mapping IDs")
    exact({row.get("id"): row for row in rows if isinstance(row, dict)}, MAPPINGS, "native mapping boundary")
    validate_defs(catalog)


def resolve(document, path):
    current = document
    for part in path.split(".")[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    final = path.split(".")[-1]
    return current, int(final) if isinstance(current, list) else final


def mutate(catalog, mutation):
    parent, key = resolve(catalog, mutation["path"])
    if mutation["op"] == "set":
        parent[key] = mutation.get("value")
    else:
        raise ValueError("unknown vector mutation")


def validate_document(document):
    if document.get("contract") != "helianthus.semantic.pack.evse.acceptance/v1" or document.get("pack_contract") != "helianthus.pack.evse/v1":
        raise ValueError("contract ID")
    validate_catalog(document.get("catalog"))
    vectors = document.get("vectors", [])
    if not any(vector.get("polarity") == "positive" for vector in vectors) or not any(vector.get("polarity") == "negative" for vector in vectors):
        raise ValueError("positive and negative vectors")
    for vector in vectors:
        candidate = copy.deepcopy(document["catalog"])
        for mutation in vector.get("input", {}).get("mutations", []):
            mutate(candidate, mutation)
        if vector.get("polarity") == "positive":
            validate_catalog(candidate)
        else:
            try:
                validate_catalog(candidate)
            except ValueError as error:
                if vector.get("expect", {}).get("error") not in str(error):
                    raise ValueError(f"{vector.get('id')}: {error}") from error
            else:
                raise ValueError(f"{vector.get('id')}: accepted")


def main():
    document = load_document(VECTORS)
    validate_document(document)
    text = DOCUMENT.read_text(encoding="utf-8")
    for collection in document["catalog"]["definitions"].values():
        for definition in collection:
            if definition["id"] not in text:
                raise ValueError(f"document misses {definition['id']}")
    print("EVSE pack v1: PASS")


if __name__ == "__main__":
    main()
