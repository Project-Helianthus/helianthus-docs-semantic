#!/usr/bin/env python3
"""Validate exact typed associations in the PV/inverter v1 catalog."""
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
DOMAINS = {"thermal_hvac": ("helianthus.pack.thermal", "accepted"),
           "pv_inverter": ("helianthus.pack.pv", "accepted"),
           "storage_bms": ("helianthus.pack.storage", "accepted"),
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
AVAILABILITY = {"effective_availability": "kernel_observation_and_capability_state_only",
                "native_operating_readiness": "pv.status.operating",
                "portal": "consume_kernel_availability_separately"}
PINS = {
    "semantic_docs": "346cda9b675a03a7d1a8c886a3467eab84ce8fb2",
    "semreg": "cc9b324225e945598128eeabe977e7fa0af6dc93",
    "growatt_docs_modbus": "7ba9c333539c4381c06584cab0dc86c7e9280767",
    "growatt_modbusreg": "7853d903970a4fdded35abaef01fe30f7e93be6a",
    "fronius_docs_modbus": "f0292b6dee164b78c2ec06849e214839f55abd18",
    "fronius_modbusreg": "1e2cea375f415847fb70cb8a181cdd1285543eca",
    "eebus_ledger": "81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1",
    "eebus_m625_donor": "cedf238e34f879815ba773e9cd76b2b31c2822a3",
    "matter_draft": "29b4768a513cf566011ab8cd60df1bc495204953",
}
STAGES = ["admission", "dispatch", "acknowledgement", "readback", "terminal_outcome"]
OUTCOMES = ["rejected", "failed_no_contact", "acknowledged_unverified", "applied",
            "no_effect", "conflict", "indeterminate"]
FIELD_CONTRACTS = {
    "pv.dc.voltage": ("quantity", "unit.volt", "pv.dimension.input", True, None),
    "pv.dc.current": ("quantity", "unit.ampere", "pv.dimension.input", True, None),
    "pv.dc.power": ("quantity", "unit.watt", "pv.dimension.input", True, None),
    "pv.ac.voltage": ("quantity", "unit.volt", "pv.dimension.phase", True, None),
    "pv.ac.current": ("quantity", "unit.ampere", "pv.dimension.phase", True, None),
    "pv.ac.active_power": ("quantity", "unit.watt", "pv.dimension.phase", True, None),
    "pv.ac.frequency": ("quantity", "unit.hertz", "pv.dimension.inverter", True, None),
    "pv.ac.power_factor": ("quantity", "unit.ratio", "pv.dimension.inverter", True, None),
    "pv.energy.generated": ("quantity", "unit.kilowatt_hour", "pv.dimension.system", True, None),
    "pv.temperature.inverter": ("quantity", "unit.celsius", "pv.dimension.inverter", True, None),
    "pv.limit.active_power": ("quantity", "unit.watt", "pv.dimension.inverter", True, None),
    "pv.limit.export_power": ("quantity", "unit.watt", "pv.dimension.system", True, None),
    "pv.status.operating": ("symbol", None, "pv.dimension.inverter", True,
                              ("pv.status.operating.generating", "pv.status.operating.idle", "pv.status.operating.standby")),
    "pv.status.derating": ("symbol", None, "pv.dimension.inverter", True,
                             ("pv.status.derating.active", "pv.status.derating.clear")),
    "pv.status.fault": ("symbol", None, "pv.dimension.inverter", True,
                          ("pv.status.fault.clear", "pv.status.fault.present")),
    "pv.dc.aggregate_voltage": ("quantity", "unit.volt", "pv.dimension.inverter", True, None),
    "pv.dc.aggregate_current": ("quantity", "unit.ampere", "pv.dimension.inverter", True, None),
    "pv.dc.aggregate_power": ("quantity", "unit.watt", "pv.dimension.inverter", True, None),
    "pv.ac.aggregate_voltage": ("quantity", "unit.volt", "pv.dimension.inverter", True, None),
    "pv.ac.aggregate_current": ("quantity", "unit.ampere", "pv.dimension.inverter", True, None),
    "pv.ac.aggregate_active_power": ("quantity", "unit.watt", "pv.dimension.inverter", True, None),
}
FIELD_BOUNDS = {
    "pv.dc.voltage": ({"coefficient":"0","exponent10":0},{"coefficient":"2","exponent10":3}),
    "pv.dc.current": ({"coefficient":"0","exponent10":0},{"coefficient":"2","exponent10":3}),
    "pv.dc.power": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":7}),
    "pv.ac.voltage": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":3}),
    "pv.ac.current": ({"coefficient":"0","exponent10":0},{"coefficient":"2","exponent10":3}),
    "pv.ac.active_power": ({"coefficient":"-1","exponent10":7},{"coefficient":"1","exponent10":7}),
    "pv.ac.frequency": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":3}),
    "pv.ac.power_factor": ({"coefficient":"-1","exponent10":0},{"coefficient":"1","exponent10":0}),
    "pv.energy.generated": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":12}),
    "pv.temperature.inverter": ({"coefficient":"-5","exponent10":1},{"coefficient":"2","exponent10":2}),
    "pv.limit.active_power": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":7}),
    "pv.limit.export_power": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":7}),
    "pv.dc.aggregate_voltage": ({"coefficient":"0","exponent10":0},{"coefficient":"2","exponent10":3}),
    "pv.dc.aggregate_current": ({"coefficient":"0","exponent10":0},{"coefficient":"2","exponent10":3}),
    "pv.dc.aggregate_power": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":7}),
    "pv.ac.aggregate_voltage": ({"coefficient":"0","exponent10":0},{"coefficient":"1","exponent10":3}),
    "pv.ac.aggregate_current": ({"coefficient":"0","exponent10":0},{"coefficient":"2","exponent10":3}),
    "pv.ac.aggregate_active_power": ({"coefficient":"-1","exponent10":7},{"coefficient":"1","exponent10":7}),
}
DIMS = {"pv.dimension.system", "pv.dimension.inverter", "pv.dimension.array",
        "pv.dimension.string", "pv.dimension.input", "pv.dimension.phase"}
SERVICE_DIMENSIONS = {"pv.service.system": "pv.dimension.system",
                      "pv.service.inverter": "pv.dimension.inverter",
                      "pv.service.array": "pv.dimension.array",
                      "pv.service.string": "pv.dimension.string",
                      "pv.service.input": "pv.dimension.input",
                      "pv.service.phase": "pv.dimension.phase"}
RELATIONSHIPS = {"pv.relationship.system_inverter": ("pv.dimension.system", "pv.dimension.inverter"),
                 "pv.relationship.inverter_array": ("pv.dimension.inverter", "pv.dimension.array"),
                 "pv.relationship.array_string": ("pv.dimension.array", "pv.dimension.string"),
                 "pv.relationship.inverter_input": ("pv.dimension.inverter", "pv.dimension.input"),
                 "pv.relationship.inverter_phase": ("pv.dimension.inverter", "pv.dimension.phase")}
CAPS = {"pv.capability.read.system": ("pv.service.system", None),
        "pv.capability.read.inverter": ("pv.service.inverter", None),
        "pv.capability.read.array": ("pv.service.array", None),
        "pv.capability.read.string": ("pv.service.string", None),
        "pv.capability.read.input": ("pv.service.input", None),
        "pv.capability.read.phase": ("pv.service.phase", None),
        "pv.capability.set_active_power_limit": ("pv.service.inverter", ("pv.limit.active_power",)),
        "pv.capability.set_export_limit": ("pv.service.system", ("pv.limit.export_power",))}
OPS = {"pv.operation.set_active_power_limit": ("pv.capability.set_active_power_limit", ("pv.limit.active_power",), "pv.effect.set_active_power_limit"),
       "pv.operation.set_export_limit": ("pv.capability.set_export_limit", ("pv.limit.export_power",), "pv.effect.set_export_limit")}
EFFECTS = {"pv.effect.set_active_power_limit": ("pv.operation.set_active_power_limit", "pv.limit.active_power"),
           "pv.effect.set_export_limit": ("pv.operation.set_export_limit", "pv.limit.export_power")}
PORTAL_READS = {"pv.portal.read.system": ("pv.service.system", ("pv.energy.generated", "pv.limit.export_power")),
                "pv.portal.read.inverter": ("pv.service.inverter", ("pv.ac.aggregate_active_power", "pv.ac.aggregate_current", "pv.ac.aggregate_voltage", "pv.ac.frequency", "pv.ac.power_factor", "pv.dc.aggregate_current", "pv.dc.aggregate_power", "pv.dc.aggregate_voltage", "pv.limit.active_power", "pv.status.derating", "pv.status.fault", "pv.status.operating", "pv.temperature.inverter")),
                "pv.portal.read.array": ("pv.service.array", ()),
                "pv.portal.read.string": ("pv.service.string", ()),
                "pv.portal.read.input": ("pv.service.input", ("pv.dc.current", "pv.dc.power", "pv.dc.voltage")),
                "pv.portal.read.phase": ("pv.service.phase", ("pv.ac.active_power", "pv.ac.current", "pv.ac.voltage"))}
PORTAL_OPS = {"pv.portal.operation.set_active_power_limit": "pv.operation.set_active_power_limit",
              "pv.portal.operation.set_export_limit": "pv.operation.set_export_limit"}
MAPPINGS = {
    "pv.mapping.growatt.protocol_ii": {"id": "pv.mapping.growatt.protocol_ii", "native_owner": "helianthus-docs-modbus", "source_refs": ["growatt_docs_modbus", "growatt_modbusreg"], "state": "candidate", "qualification": "blocked_docs_modbus_143_modbusreg_196", "applicability": "tl3_x_offsets_59_124_unresolved", "loss": "unknown"},
    "pv.mapping.fronius.readiness": {"id": "pv.mapping.fronius.readiness", "native_owner": "helianthus-docs-modbus", "source_refs": ["fronius_docs_modbus", "fronius_modbusreg"], "state": "candidate", "qualification": "offline_candidate_live_qualified_false", "live_qualified": False, "write_authority": False, "loss": "unknown"},
    "pv.mapping.eebus": {"id": "pv.mapping.eebus", "native_owner": "helianthus-docs-eebus", "source_refs": ["eebus_ledger", "eebus_m625_donor"], "state": "unknown_pending_std_01", "qualification": "unresolved", "loss": "unknown"},
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
    left_coefficient, left_exponent = decimal(left)
    right_coefficient, right_exponent = decimal(right)
    shared_exponent = min(left_exponent, right_exponent)
    return left_coefficient * 10 ** (left_exponent - shared_exponent) < right_coefficient * 10 ** (right_exponent - shared_exponent)


def validate_field(field):
    contract = FIELD_CONTRACTS.get(field.get("id"))
    if contract is None:
        raise ValueError("field catalog differs")
    kind, unit, dimension, optional, symbols = contract
    if field.get("kind") != kind or field.get("dimension") != dimension or type(field.get("optional")) is not bool or field["optional"] != optional:
        raise ValueError("field has noncanonical kind, dimension, or optionality")
    required = {"id", "ref", "kind", "dimension", "optional", "order"}
    if kind == "quantity":
        if not isinstance(field.get("unit"), str) or not ID.fullmatch(field["unit"]):
            raise ValueError("invalid unit ID")
        bounds = field.get("bounds", {})
        expected_bounds = {"minimum": FIELD_BOUNDS[field["id"]][0], "maximum": FIELD_BOUNDS[field["id"]][1]}
        if set(field) != required | {"unit", "bounds"} or field.get("unit") != unit or not decimal_less(bounds.get("minimum"), bounds.get("maximum")) or bounds != expected_bounds:
            raise ValueError("field has invalid canonical quantity contract")
        return
    actual_symbols = field.get("symbols")
    if set(field) != required | {"symbols"} or not isinstance(actual_symbols, list) or tuple(actual_symbols) != symbols or actual_symbols != sorted(actual_symbols) or len(actual_symbols) != len(set(actual_symbols)) or any(not isinstance(symbol, str) or not ID.fullmatch(symbol) for symbol in actual_symbols):
        raise ValueError("field has invalid canonical symbol contract")


def validate_defs(catalog):
    definitions = catalog.get("definitions", {})
    fields = refs(definitions.get("fields"), "fields", FIELD_CONTRACTS)
    for field in fields.values():
        validate_field(field)
    dimensions = refs(definitions.get("fact_dimensions"), "fact dimensions", DIMS)
    if any(dimension.get("value_kind") != "text" or set(dimension) != {"id", "ref", "value_kind", "order"} for dimension in dimensions.values()):
        raise ValueError("dimension has invalid value kind")
    services = refs(definitions.get("services"), "services", SERVICE_DIMENSIONS)
    for identifier, service in services.items():
        if service.get("fact_key_dimension") != SERVICE_DIMENSIONS[identifier] or set(service) != {"id", "ref", "fact_key_dimension", "order"}:
            raise ValueError("service dimension association")
    relationships = refs(definitions.get("relationships"), "relationships", RELATIONSHIPS)
    for identifier, relation in relationships.items():
        if (relation.get("from"), relation.get("to")) != RELATIONSHIPS[identifier] or set(relation) != {"id", "ref", "from", "to", "order"}:
            raise ValueError("topology relationship association")
    capabilities = refs(definitions.get("capabilities"), "capabilities", CAPS)
    for identifier, capability in capabilities.items():
        service, constraints = CAPS[identifier]
        expected_keys = {"id", "ref", "service", "activation", "order"}
        if constraints is not None:
            expected_keys.add("constraints")
        if capability.get("service") != service or capability.get("activation") != "qualified_current_binding" or tuple(capability.get("constraints", ())) != (() if constraints is None else constraints) or set(capability) != expected_keys:
            raise ValueError("capability association")
    operations = refs(definitions.get("operations"), "operations", OPS)
    for identifier, operation in operations.items():
        capability, arguments, effect = OPS[identifier]
        if (operation.get("capability"), tuple(operation.get("arguments", ())), tuple(operation.get("argument_constraints", ())), operation.get("effect_rule")) != (capability, arguments, arguments, effect):
            raise ValueError("operation association")
        if operation.get("preconditions") != ["current_generation", "qualified_active_capability", "exact_route", "authority_admitted"] or operation.get("stages") != STAGES or operation.get("terminal_outcomes") != OUTCOMES or operation.get("readback") != "current_generation_exact_effect" or operation.get("retry") != "forbidden_after_indeterminate":
            raise ValueError("operation lacks admission/readback")
    effects = refs(definitions.get("effect_rules"), "effect rules", EFFECTS)
    for identifier, effect in effects.items():
        operation, fact = EFFECTS[identifier]
        if (effect.get("operation"), effect.get("fact"), effect.get("operator")) != (operation, fact, "equal") or FIELD_CONTRACTS[fact][0] != "quantity":
            raise ValueError("effect association")
    portal = refs(definitions.get("portal_contributions"), "Portal contributions", set(PORTAL_READS) | set(PORTAL_OPS))
    read_fields = set()
    for identifier, contribution in portal.items():
        if identifier in PORTAL_READS:
            service, expected_fields = PORTAL_READS[identifier]
            if contribution.get("kind") != "read" or contribution.get("service") != service or tuple(contribution.get("fields", ())) != expected_fields or set(contribution) != {"id", "ref", "kind", "service", "fields", "order"}:
                raise ValueError("Portal read association")
            read_fields.update(expected_fields)
        elif contribution.get("kind") != "operation" or contribution.get("operation") != PORTAL_OPS[identifier] or contribution.get("admission") != "current_only" or set(contribution) != {"id", "ref", "kind", "operation", "admission", "order"}:
            raise ValueError("Portal operation association")
    exact(read_fields, set(FIELD_CONTRACTS), "read descriptor field coverage")


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get("pack") != PACK or catalog.get("kernel_contract") != "helianthus.semantic.kernel/v1":
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
    mapping_rows = catalog.get("candidate_mappings")
    if not isinstance(mapping_rows, list) or len({row.get("id") for row in mapping_rows if isinstance(row, dict)}) != len(mapping_rows):
        raise ValueError("mapping row IDs")
    exact({row.get("id"): row for row in mapping_rows if isinstance(row, dict)}, MAPPINGS, "native mapping boundary")
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
