#!/usr/bin/env python3
"""Validate the kernel-compatible PV/inverter v1 catalog."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/packs/pv-inverter-acceptance-vectors.json"
DOCUMENT = ROOT / "api/v1/packs/pv-inverter-v1.md"
PACK = {"id": "helianthus.pack.pv", "version": "1.0.0"}
ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
FIELDS = {
    "pv.dc.voltage", "pv.dc.current", "pv.dc.power", "pv.ac.voltage",
    "pv.ac.current", "pv.ac.active_power", "pv.ac.frequency",
    "pv.ac.power_factor", "pv.energy.generated", "pv.temperature.inverter",
    "pv.limit.active_power", "pv.limit.export_power", "pv.status.operating",
    "pv.status.derating", "pv.status.fault", "pv.status.availability",
    "pv.dc.aggregate_voltage", "pv.dc.aggregate_current", "pv.dc.aggregate_power",
    "pv.ac.aggregate_voltage", "pv.ac.aggregate_current", "pv.ac.aggregate_active_power",
}
DIMS = {"pv.dimension.system", "pv.dimension.inverter", "pv.dimension.array",
        "pv.dimension.string", "pv.dimension.input", "pv.dimension.phase"}
SERVICES = {"pv.service.system", "pv.service.inverter", "pv.service.array",
            "pv.service.string", "pv.service.input", "pv.service.phase"}
RELATIONSHIPS = {"pv.relationship.system_inverter", "pv.relationship.inverter_array",
                 "pv.relationship.array_string", "pv.relationship.inverter_input",
                 "pv.relationship.inverter_phase"}
CAPS = {"pv.capability.read.system", "pv.capability.read.inverter",
        "pv.capability.read.array", "pv.capability.read.string",
        "pv.capability.read.input", "pv.capability.read.phase",
        "pv.capability.set_active_power_limit", "pv.capability.set_export_limit"}
OPS = {"pv.operation.set_active_power_limit", "pv.operation.set_export_limit"}
EFFECTS = {"pv.effect.set_active_power_limit", "pv.effect.set_export_limit"}
PORTAL = {"pv.portal.read.system", "pv.portal.read.inverter", "pv.portal.read.array",
          "pv.portal.read.string", "pv.portal.read.input", "pv.portal.read.phase",
          "pv.portal.operation.set_active_power_limit", "pv.portal.operation.set_export_limit"}
DOMAINS = {"thermal_hvac": ("helianthus.pack.thermal", "accepted"),
           "pv_inverter": ("helianthus.pack.pv", "accepted"),
           "storage_bms": ("helianthus.pack.storage", "follow_on"),
           "evse": ("helianthus.pack.evse", "follow_on"),
           "infrastructure": ("helianthus.pack.infrastructure", "follow_on")}
LIFECYCLE = {"source_epoch", "driver_generation", "semantic_revision",
             "capability_qualification", "activation", "generation_fencing",
             "partial_updates", "stale_unknown_evidence", "last_known_good_retention"}
LOSS = {"native_enum", "precision_range", "signed_direction",
        "per_string_input_phase_topology", "counter_reset_wrap", "curtailment_reason",
        "vendor_extensions", "unavailable_fields", "conflicting_sources",
        "unsupported_operations"}
POLICY = {"admission": ["exact_source_epoch", "current_driver_generation",
                          "exact_semantic_revision", "qualified_active_capability"],
          "stale_generation": "reject",
          "partial_publication": "supplied_valid_only_preserve_permitted_last_known_good",
          "withdrawal": "explicit_generation_fenced",
          "evidence": "stale_unknown_never_promote_or_authorize",
          "tombstone": "retained_non_actionable"}
COUNTER = {"generated_energy": "native_reset_or_wrap_evidence_required",
           "decrease": "never_infer_reset_or_wrap",
           "projection": "counter_continuity_or_loss_explicit"}
PINS = {
    "semantic_docs": "346cda9b675a03a7d1a8c886a3467eab84ce8fb2",
    "semreg": "cc9b324225e945598128eeabe977e7fa0af6dc93",
    "growatt_docs_modbus": "7ba9c333539c4381c06584cab0dc86c7e9280767",
    "growatt_modbusreg": "7853d903970a4fdded35abaef01fe30f7e93be6a",
    "tesla_docs_modbus": "d16ff91ff808803fa31c67a6a10eb2a4faa70937",
    "tesla_modbusreg": "75e4e3988a7682068c02d8ac24f737b7f24a029f",
    "eebus_ledger": "81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1",
    "eebus_m625_donor": "cedf238e34f879815ba773e9cd76b2b31c2822a3",
    "matter_draft": "29b4768a513cf566011ab8cd60df1bc495204953",
}
STAGES = ["admission", "dispatch", "acknowledgement", "readback", "terminal_outcome"]
OUTCOMES = ["rejected", "failed_no_contact", "acknowledged_unverified", "applied",
            "no_effect", "conflict", "indeterminate"]
FIELD_CONTRACTS = {
    "pv.dc.voltage": ("unit.volt", "pv.dimension.input"),
    "pv.dc.current": ("unit.ampere", "pv.dimension.input"),
    "pv.dc.power": ("unit.watt", "pv.dimension.input"),
    "pv.ac.voltage": ("unit.volt", "pv.dimension.phase"),
    "pv.ac.current": ("unit.ampere", "pv.dimension.phase"),
    "pv.ac.active_power": ("unit.watt", "pv.dimension.phase"),
    "pv.ac.frequency": ("unit.hertz", "pv.dimension.inverter"),
    "pv.ac.power_factor": ("unit.ratio", "pv.dimension.inverter"),
    "pv.energy.generated": ("unit.kilowatt_hour", "pv.dimension.system"),
    "pv.temperature.inverter": ("unit.celsius", "pv.dimension.inverter"),
    "pv.limit.active_power": ("unit.watt", "pv.dimension.inverter"),
    "pv.limit.export_power": ("unit.watt", "pv.dimension.system"),
    "pv.dc.aggregate_voltage": ("unit.volt", "pv.dimension.inverter"),
    "pv.dc.aggregate_current": ("unit.ampere", "pv.dimension.inverter"),
    "pv.dc.aggregate_power": ("unit.watt", "pv.dimension.inverter"),
    "pv.ac.aggregate_voltage": ("unit.volt", "pv.dimension.inverter"),
    "pv.ac.aggregate_current": ("unit.ampere", "pv.dimension.inverter"),
    "pv.ac.aggregate_active_power": ("unit.watt", "pv.dimension.inverter"),
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


def refs(items, label):
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
    if not all(isinstance(order, int) and order > 0 for order in orders) or orders != sorted(orders) or len(orders) != len(set(orders)):
        raise ValueError(f"{label} noncanonical order")
    return set(ids)


def decimal(value):
    if not isinstance(value, dict) or set(value) != {"coefficient", "exponent10"}:
        raise ValueError("bounds must use canonical kernel Decimal")
    coefficient, exponent = value["coefficient"], value["exponent10"]
    if not isinstance(coefficient, str) or not re.fullmatch(r"0|-?[1-9][0-9]*", coefficient) or not isinstance(exponent, int) or not -18 <= exponent <= 18 or (coefficient == "0" and exponent != 0) or (coefficient != "0" and coefficient.endswith("0")):
        raise ValueError("bounds must use canonical kernel Decimal")
    return int(coefficient) * 10 ** exponent


def validate_defs(catalog):
    definitions = catalog.get("definitions", {})
    fields = definitions.get("fields")
    exact(refs(fields, "fields"), FIELDS, "field catalog")
    for field in fields:
        if field.get("kind") not in {"quantity", "symbol"}:
            raise ValueError("field has non-kernel ValueKind")
        if field.get("dimension") not in DIMS or not isinstance(field.get("optional"), bool):
            raise ValueError("field lacks canonical dimension or optionality")
        if field["kind"] == "quantity":
            if not isinstance(field.get("unit"), str) or not ID.fullmatch(field["unit"]):
                raise ValueError("invalid unit ID")
            if (field.get("unit"), field.get("dimension")) != FIELD_CONTRACTS.get(field["id"]):
                raise ValueError("field has noncanonical unit or dimension")
            if decimal(field.get("bounds", {}).get("minimum")) >= decimal(field.get("bounds", {}).get("maximum")):
                raise ValueError("unordered numeric bounds")
        elif "unit" in field or "bounds" in field or field.get("symbols") != sorted(field.get("symbols", [])) or not field.get("symbols") or any("unknown" in symbol or "withheld" in symbol for symbol in field["symbols"]):
            raise ValueError("invalid semantic symbols")
    exact(refs(definitions.get("fact_dimensions"), "fact dimensions"), DIMS, "dimension catalog")
    for dimension in definitions["fact_dimensions"]:
        if dimension.get("value_kind") != "text":
            raise ValueError("dimension has invalid value kind")
    services = definitions.get("services")
    relationships = definitions.get("relationships")
    capabilities = definitions.get("capabilities")
    operations = definitions.get("operations")
    effects = definitions.get("effect_rules")
    portal = definitions.get("portal_contributions")
    service_ids = refs(services, "services")
    exact(service_ids, SERVICES, "service catalog")
    exact(refs(relationships, "relationships"), RELATIONSHIPS, "topology relationship catalog")
    exact(refs(capabilities, "capabilities"), CAPS, "capability catalog")
    exact(refs(operations, "operations"), OPS, "operation catalog")
    exact(refs(effects, "effect rules"), EFFECTS, "effect catalog")
    exact(refs(portal, "Portal contributions"), PORTAL, "Portal catalog")
    for service in services:
        if service.get("fact_key_dimension") not in DIMS:
            raise ValueError("service missing dimension contract")
    for relation in relationships:
        if relation.get("from") not in DIMS or relation.get("to") not in DIMS:
            raise ValueError("topology relationship is dangling")
    capability_by_id = {capability["id"]: capability for capability in capabilities}
    for capability in capabilities:
        if capability.get("service") not in service_ids or capability.get("activation") != "qualified_current_binding":
            raise ValueError("capability dangling service or activation")
        if capability["id"].startswith("pv.capability.set_") and capability.get("constraints") not in (["pv.limit.active_power"], ["pv.limit.export_power"]):
            raise ValueError("capability lacks exact argument constraint")
    for operation in operations:
        capability = capability_by_id.get(operation.get("capability"))
        if capability is None or operation.get("effect_rule") not in EFFECTS:
            raise ValueError("operation dangling reference")
        if operation.get("arguments") != capability.get("constraints") or operation.get("argument_constraints") != operation.get("arguments"):
            raise ValueError("operation/capability constraint mismatch")
        if operation.get("preconditions") != ["current_generation", "qualified_active_capability", "exact_route", "authority_admitted"] or operation.get("stages") != STAGES or operation.get("terminal_outcomes") != OUTCOMES or operation.get("readback") != "current_generation_exact_effect" or operation.get("retry") != "forbidden_after_indeterminate":
            raise ValueError("operation lacks admission/readback")
    for effect in effects:
        if effect.get("operation") not in OPS or effect.get("fact") not in FIELDS or effect.get("operator") != "equal":
            raise ValueError("effect dangling reference")
    read_fields = set()
    for contribution in portal:
        if contribution.get("kind") == "read":
            if contribution.get("service") not in service_ids or not isinstance(contribution.get("fields"), list) or not set(contribution["fields"]) <= FIELDS:
                raise ValueError("Portal dangling reference")
            read_fields.update(contribution["fields"])
        elif contribution.get("kind") == "operation":
            if contribution.get("operation") not in OPS or contribution.get("admission") != "current_only":
                raise ValueError("Portal operation not admitted")
        else:
            raise ValueError("Portal contribution kind")
    exact(read_fields, FIELDS, "read descriptor field coverage")


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get("pack") != PACK or catalog.get("kernel_contract") != "helianthus.semantic.kernel/v1":
        raise ValueError("catalog lacks exact PackRef")
    actual_domains = {item.get("id"): (item.get("pack"), item.get("state")) for item in catalog.get("domain_catalog", []) if isinstance(item, dict)}
    exact(actual_domains, DOMAINS, "five-domain catalog")
    exact({item.get("id"): item.get("revision") for item in catalog.get("inputs", []) if isinstance(item, dict)}, PINS, "pinned public inputs")
    if set(catalog.get("lifecycle_axes", [])) != LIFECYCLE:
        raise ValueError("lifecycle axes")
    exact(catalog.get("publication_withdrawal_policy"), POLICY, "publication/withdrawal policy")
    exact(catalog.get("counter_policy"), COUNTER, "counter policy")
    if set(catalog.get("loss_dispositions", [])) != LOSS:
        raise ValueError("projection-loss coverage")
    mappings = {mapping.get("id"): mapping for mapping in catalog.get("candidate_mappings", []) if isinstance(mapping, dict)}
    growatt = mappings.get("pv.mapping.growatt.protocol_ii", {})
    if growatt.get("state") != "candidate" or growatt.get("qualification") != "blocked_docs_modbus_143_modbusreg_196" or growatt.get("applicability") != "tl3_x_offsets_59_124_unresolved":
        raise ValueError("Growatt mapping")
    tesla = mappings.get("pv.mapping.tesla.inverter", {})
    if tesla.get("state") != "candidate" or tesla.get("qualification") != "native_owner_required":
        raise ValueError("Tesla mapping")
    eebus = mappings.get("pv.mapping.eebus", {})
    if eebus.get("state") != "unknown_pending_std_01" or eebus.get("qualification") != "unresolved":
        raise ValueError("eeBUS mapping")
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
    elif mutation["op"] == "delete":
        del parent[key]
    elif mutation["op"] == "remove_id":
        parent[key][:] = [item for item in parent[key] if (item.get("id") if isinstance(item, dict) else item) != mutation["id"]]
    else:
        raise ValueError("unknown vector mutation")


def validate_document(document):
    if document.get("contract") != "helianthus.semantic.pack.pv.acceptance/v1" or document.get("pack_contract") != "helianthus.pack.pv/v1":
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
    for definitions in document["catalog"]["definitions"].values():
        for definition in definitions:
            if definition["id"] not in text:
                raise ValueError(f"document misses {definition['id']}")
    print("PV/inverter pack v1: PASS")


if __name__ == "__main__":
    main()
