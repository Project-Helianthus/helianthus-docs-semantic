#!/usr/bin/env python3
"""Validate exact typed associations in the infrastructure v1 catalog."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/packs/infrastructure-acceptance-vectors.json"
DOCUMENT = ROOT / "api/v1/packs/infrastructure-v1.md"
PACK = {"id": "helianthus.pack.infrastructure", "version": "1.0.0"}
ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
SYMBOL = re.compile(r"^[a-z][a-z0-9._]*$")
# The SI unit set of the unit rule in api/README.md (a working reading): a pack field declares no customary or prefixed unit.
CANONICAL_UNITS = frozenset({"unit.ampere", "unit.ampere_hour", "unit.cubic_metre_per_second", "unit.hertz", "unit.joule",
                             "unit.kelvin", "unit.pascal", "unit.ratio", "unit.reciprocal_second", "unit.volt",
                             "unit.volt_ampere", "unit.volt_ampere_reactive", "unit.watt", "unit.second", "unit.cubic_metre", "unit.metre", "unit.ohm", "unit.radian", "unit.one", "unit.volt_ampere_reactive_second", "unit.volt_ampere_second", "unit.kilogram_per_cubic_metre", "unit.becquerel_per_cubic_metre", "unit.kilogram_per_joule", "unit.watt_per_square_metre", "unit.metre_per_joule", "unit.currency", "unit.currency_per_joule"})
DOMAINS = {
    "thermal_hvac": ("helianthus.pack.thermal", "accepted"),
    "pv_inverter": ("helianthus.pack.pv", "accepted"),
    "storage_bms": ("helianthus.pack.storage", "accepted"),
    "evse": ("helianthus.pack.evse", "accepted"),
    "infrastructure": ("helianthus.pack.infrastructure", "accepted"),
}
PINS = {
    "semantic_docs": "e22451c8ca3d3f7275635216450f8fb2d216801e",
    "semreg": "cc9b324225e945598128eeabe977e7fa0af6dc93",
    "ebus_docs": "5d66c66ef15e6bb2d473a341dae17dc9f9e25e05",
    "modbus_docs": "7ba9c333539c4381c06584cab0dc86c7e9280767",
    "modbusreg": "7853d903970a4fdded35abaef01fe30f7e93be6a",
    "eebus_ledger": "81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1",
    "eebus_m625_donor": "cedf238e34f879815ba773e9cd76b2b31c2822a3",
    "matter_draft": "29b4768a513cf566011ab8cd60df1bc495204953",
}
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
COUNTER = {"import_export_energy": "native_reset_or_wrap_evidence_required",
           "decrease": "never_infer_reset_or_wrap",
           "projection": "counter_continuity_or_loss_explicit"}
AVAILABILITY = {"effective_availability": "kernel_observation_and_capability_state_only",
                "native_readiness": "infrastructure.status.readiness",
                "portal": "consume_kernel_availability_separately"}
LOSS = {"native_enum_bitfield", "precision_range", "phase_grid_feeder_circuit_meter_topology",
        "direction_reference", "aggregation", "counter_reset_wrap", "unavailable_fields",
        "conflicting_sources", "vendor_extensions", "unsupported_operations"}
READ_ONLY = {"operations": "none_without_qualified_native_route_and_action_time_authority",
             "import_export_limit": "not_published", "breaker_actuation": "not_published",
             "generic_enable_disable": "not_published", "portal_operations": "not_published"}


def quantity(unit, dimension, minimum, maximum):
    return ("quantity", unit, dimension, True, None, minimum, maximum)


def symbol(dimension, symbols):
    return ("symbol", None, dimension, True, tuple(symbols), None, None)


def boolean(dimension):
    return ("boolean", None, dimension, True, None, None, None)


def empty_quantity(unit, dimension):
    return ("quantity", unit, dimension, True, None, None, None)


def text_field(dimension):
    return ("text", None, dimension, True, None, None, None)


def symbols_field(dimension, names):
    return ("symbols", None, dimension, True, tuple(names), None, None)


def unitless_quantity(dimension):
    return ("quantity", None, dimension, True, None, None, None)


MEASUREMENT_SYMBOLS = (
    "active_current", "active_power", "apparent_current", "apparent_energy", "apparent_power",
    "electrical_energy", "frequency", "neutral_current", "power_factor", "reactive_current",
    "reactive_energy", "reactive_power", "rms_current", "rms_power", "rms_voltage", "unspecified", "voltage",
)
QUALIFIED = {
    "infrastructure.accuracy.measured": ("infrastructure.dimension.measurement_type",),
    "infrastructure.accuracy.ratio_maximum": ("infrastructure.dimension.measurement_type",),
    "infrastructure.ac.harmonic_current": ("infrastructure.dimension.harmonic_order",),
    "infrastructure.ac.harmonic_phase": ("infrastructure.dimension.harmonic_order",),
}
QUALIFIER_DIMS = {"infrastructure.dimension.measurement_type", "infrastructure.dimension.harmonic_order"}


FIELD_CONTRACTS = {
    "infrastructure.ac.voltage": quantity("unit.volt", "infrastructure.dimension.phase", ("0", 0), ("1", 3)),
    "infrastructure.ac.voltage_line_line": quantity("unit.volt", "infrastructure.dimension.line_pair", ("0", 0), ("1", 3)),
    "infrastructure.ac.current": quantity("unit.ampere", "infrastructure.dimension.phase", ("0", 0), ("1", 3)),
    "infrastructure.ac.active_power": quantity("unit.watt", "infrastructure.dimension.phase", ("-1", 7), ("1", 7)),
    "infrastructure.ac.reactive_power": quantity("unit.volt_ampere_reactive", "infrastructure.dimension.phase", ("-1", 7), ("1", 7)),
    "infrastructure.ac.apparent_power": quantity("unit.volt_ampere", "infrastructure.dimension.phase", ("0", 0), ("1", 7)),
    "infrastructure.ac.frequency": quantity("unit.hertz", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 3)),
    "infrastructure.ac.power_factor": quantity("unit.ratio", "infrastructure.dimension.grid_connection", ("-1", 0), ("1", 0)),
    "infrastructure.power.import_active": quantity("unit.watt", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.pcc": quantity("unit.watt", "infrastructure.dimension.grid_connection", ("-1", 7), ("1", 7)),
    "infrastructure.limit.fallback_power": quantity("unit.watt", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.export_active": quantity("unit.watt", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.import_reactive": quantity("unit.volt_ampere_reactive", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.export_reactive": quantity("unit.volt_ampere_reactive", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.power.apparent": quantity("unit.volt_ampere", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 7)),
    "infrastructure.energy.import": quantity("unit.joule", "infrastructure.dimension.meter", ("0", 0), ("36", 17)),
    "infrastructure.energy.export": quantity("unit.joule", "infrastructure.dimension.meter", ("0", 0), ("36", 17)),
    "infrastructure.energy.self_consumption": quantity("unit.joule", "infrastructure.dimension.meter", ("0", 0), ("36", 17)),
    "infrastructure.status.connection": symbol("infrastructure.dimension.grid_connection", ["infrastructure.status.connection.connected", "infrastructure.status.connection.disconnected"]),
    "infrastructure.status.readiness": symbol("infrastructure.dimension.grid_connection", ["infrastructure.status.readiness.not_ready", "infrastructure.status.readiness.ready"]),
    "infrastructure.status.breaker": symbol("infrastructure.dimension.circuit", ["infrastructure.status.breaker.closed", "infrastructure.status.breaker.open"]),
    "infrastructure.status.fault": symbol("infrastructure.dimension.site", ["infrastructure.status.fault.clear", "infrastructure.status.fault.present"]),
    "infrastructure.status.interlock": symbol("infrastructure.dimension.circuit", ["infrastructure.status.interlock.active", "infrastructure.status.interlock.clear"]),
    "infrastructure.accuracy.measured": boolean("infrastructure.dimension.meter"),
    "infrastructure.accuracy.ratio_maximum": empty_quantity("unit.ratio", "infrastructure.dimension.meter"),
    "infrastructure.load.active_power": empty_quantity("unit.watt", "infrastructure.dimension.load"),
    "infrastructure.load.phase_active_power": empty_quantity("unit.watt", "infrastructure.dimension.phase"),
    "infrastructure.load.energy_consumed": empty_quantity("unit.joule", "infrastructure.dimension.load"),
    "infrastructure.load.energy_produced": empty_quantity("unit.joule", "infrastructure.dimension.load"),
    "infrastructure.energy.reactive_import": empty_quantity("unit.volt_ampere_reactive_second", "infrastructure.dimension.meter"),
    "infrastructure.energy.reactive_export": empty_quantity("unit.volt_ampere_reactive_second", "infrastructure.dimension.meter"),
    "infrastructure.energy.apparent_import": empty_quantity("unit.volt_ampere_second", "infrastructure.dimension.meter"),
    "infrastructure.energy.apparent_export": empty_quantity("unit.volt_ampere_second", "infrastructure.dimension.meter"),
    "infrastructure.energy.phase_import": empty_quantity("unit.joule", "infrastructure.dimension.phase"),
    "infrastructure.energy.phase_export": empty_quantity("unit.joule", "infrastructure.dimension.phase"),
    "infrastructure.ac.phase_power_factor": quantity("unit.ratio", "infrastructure.dimension.phase", None, None),
    "infrastructure.ac.reactive_current": empty_quantity("unit.ampere", "infrastructure.dimension.phase"),
    "infrastructure.ac.apparent_current": empty_quantity("unit.ampere", "infrastructure.dimension.phase"),
    "infrastructure.ac.neutral_current": empty_quantity("unit.ampere", "infrastructure.dimension.circuit"),
    "infrastructure.ac.harmonic_current": unitless_quantity("infrastructure.dimension.phase"),
    "infrastructure.ac.harmonic_phase": unitless_quantity("infrastructure.dimension.phase"),
    "infrastructure.limit.pv_curtailment_factor": quantity("unit.ratio", "infrastructure.dimension.grid_connection", ("0", 0), ("1", 0)),
    "infrastructure.meter.kind": symbol("infrastructure.dimension.meter", ["utility", "private", "generic"]),
    "infrastructure.meter.point_of_delivery": text_field("infrastructure.dimension.meter"),
    "infrastructure.meter.protocol_version": text_field("infrastructure.dimension.meter"),
    "infrastructure.meter.power_threshold": empty_quantity("unit.watt", "infrastructure.dimension.meter"),
    "infrastructure.meter.apparent_power_threshold": empty_quantity("unit.volt_ampere", "infrastructure.dimension.meter"),
    "infrastructure.meter.power_threshold_source": symbol("infrastructure.dimension.meter", ["contract", "regulator", "equipment"]),
    "infrastructure.status.supply_condition": symbol("infrastructure.dimension.grid_connection", ["normal", "over_voltage", "under_voltage", "over_frequency", "under_frequency", "outage"]),
    "infrastructure.mgcp.use_case_name": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mpc.use_case_name": text_field("infrastructure.dimension.load"),
    "infrastructure.mgcp.actor": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mpc.actor": text_field("infrastructure.dimension.load"),
    "infrastructure.mgcp.use_case_version": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mpc.use_case_version": text_field("infrastructure.dimension.load"),
    "infrastructure.mpc.ac_power": empty_quantity("unit.watt", "infrastructure.dimension.load"),
    "infrastructure.mgcp.ac_current": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mpc.ac_voltage": text_field("infrastructure.dimension.load"),
    "infrastructure.mpc.value_state": text_field("infrastructure.dimension.load"),
    "infrastructure.mgcp.value_source": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mgcp.value_range_min": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mpc.value_range_min": text_field("infrastructure.dimension.load"),
    "infrastructure.mpc.one": text_field("infrastructure.dimension.load"),
    "infrastructure.mgcp.per": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mpc.per": text_field("infrastructure.dimension.load"),
    "infrastructure.mgcp.slots": text_field("infrastructure.dimension.grid_connection"),
    "infrastructure.mpc.slots": text_field("infrastructure.dimension.load"),
    "infrastructure.mgcp.committed_power_plan": text_field("infrastructure.dimension.grid_connection"),
}
DIMS = {f"infrastructure.dimension.{name}" for name in ("site", "grid_connection", "feeder", "circuit", "phase", "meter", "line_pair", "load")}
SERVICES = {f"infrastructure.service.{name}": f"infrastructure.dimension.{name}" for name in ("site", "grid_connection", "feeder", "circuit", "phase", "meter", "line_pair", "load")}
RELATIONS = {
    "infrastructure.relation.site_grid_connection": ("infrastructure.dimension.site", "infrastructure.dimension.grid_connection", "one_to_many"),
    "infrastructure.relation.grid_connection_feeder": ("infrastructure.dimension.grid_connection", "infrastructure.dimension.feeder", "one_to_many"),
    "infrastructure.relation.feeder_circuit": ("infrastructure.dimension.feeder", "infrastructure.dimension.circuit", "one_to_many"),
    "infrastructure.relation.circuit_phase": ("infrastructure.dimension.circuit", "infrastructure.dimension.phase", "one_to_many"),
    "infrastructure.relation.grid_connection_meter": ("infrastructure.dimension.grid_connection", "infrastructure.dimension.meter", "one_to_many"),
    "infrastructure.relation.site_load": ("infrastructure.dimension.site", "infrastructure.dimension.load", "one_to_many"),
    "infrastructure.relation.load_meter": ("infrastructure.dimension.meter", "infrastructure.dimension.load", "one_to_many"),
}
DEFINITION_GROUPS = {"fields", "fact_dimensions", "qualifier_dimensions", "services", "relations", "capabilities",
                     "operations", "effect_rules", "portal_contributions", "events"}
EVENTS = {
    "infrastructure.event.supply_condition_changed": {"service": "infrastructure.service.grid_connection", "trigger": "infrastructure.status.supply_condition", "condition": "changed", "payload": (), "origin": "derived"},
    "infrastructure.event.energy_measured": {"service": "infrastructure.service.meter", "trigger": "infrastructure.energy.import", "condition": "changed", "payload": ("infrastructure.energy.export",), "origin": "emitted"},
}
CAPS = {f"infrastructure.capability.read.{name}": f"infrastructure.service.{name}" for name in ("site", "grid_connection", "feeder", "circuit", "phase", "meter")}
PORTAL = {
    "infrastructure.portal.read.site": ("infrastructure.service.site", ("infrastructure.status.fault",)),
    "infrastructure.portal.read.grid_connection": ("infrastructure.service.grid_connection", ("infrastructure.ac.frequency", "infrastructure.ac.power_factor", "infrastructure.limit.fallback_power", "infrastructure.limit.pv_curtailment_factor", "infrastructure.mgcp.ac_current", "infrastructure.mgcp.actor", "infrastructure.mgcp.committed_power_plan", "infrastructure.mgcp.per", "infrastructure.mgcp.slots", "infrastructure.mgcp.use_case_name", "infrastructure.mgcp.use_case_version", "infrastructure.mgcp.value_range_min", "infrastructure.mgcp.value_source", "infrastructure.power.apparent", "infrastructure.power.export_active", "infrastructure.power.export_reactive", "infrastructure.power.import_active", "infrastructure.power.import_reactive", "infrastructure.power.pcc", "infrastructure.status.connection", "infrastructure.status.readiness", "infrastructure.status.supply_condition")),
    "infrastructure.portal.read.feeder": ("infrastructure.service.feeder", ()),
    "infrastructure.portal.read.circuit": ("infrastructure.service.circuit", ("infrastructure.ac.neutral_current", "infrastructure.status.breaker", "infrastructure.status.interlock")),
    "infrastructure.portal.read.phase": ("infrastructure.service.phase", ("infrastructure.ac.active_power", "infrastructure.ac.apparent_current", "infrastructure.ac.apparent_power", "infrastructure.ac.current", "infrastructure.ac.harmonic_current", "infrastructure.ac.harmonic_phase", "infrastructure.ac.phase_power_factor", "infrastructure.ac.reactive_current", "infrastructure.ac.reactive_power", "infrastructure.ac.voltage", "infrastructure.energy.phase_export", "infrastructure.energy.phase_import", "infrastructure.load.phase_active_power")),
    "infrastructure.portal.read.meter": ("infrastructure.service.meter", ("infrastructure.accuracy.measured", "infrastructure.accuracy.ratio_maximum", "infrastructure.energy.apparent_export", "infrastructure.energy.apparent_import", "infrastructure.energy.export", "infrastructure.energy.import", "infrastructure.energy.reactive_export", "infrastructure.energy.reactive_import", "infrastructure.energy.self_consumption", "infrastructure.meter.apparent_power_threshold", "infrastructure.meter.kind", "infrastructure.meter.point_of_delivery", "infrastructure.meter.power_threshold", "infrastructure.meter.power_threshold_source", "infrastructure.meter.protocol_version")),
    "infrastructure.portal.read.line_pair": ("infrastructure.service.line_pair", ("infrastructure.ac.voltage_line_line",)),
    "infrastructure.portal.read.load": ("infrastructure.service.load", ("infrastructure.load.active_power", "infrastructure.load.energy_consumed", "infrastructure.load.energy_produced", "infrastructure.mpc.ac_power", "infrastructure.mpc.ac_voltage", "infrastructure.mpc.actor", "infrastructure.mpc.one", "infrastructure.mpc.per", "infrastructure.mpc.slots", "infrastructure.mpc.use_case_name", "infrastructure.mpc.use_case_version", "infrastructure.mpc.value_range_min", "infrastructure.mpc.value_state")),
}
MAPPINGS = {
    "infrastructure.mapping.ebus": {"id":"infrastructure.mapping.ebus","native_owner":"helianthus-docs-ebus","source_refs":["ebus_docs"],"state":"unknown_profile_specific","qualification":"identity_provenance_only","control_route":"none","live_authority":False,"loss":"unknown"},
    "infrastructure.mapping.modbus": {"id":"infrastructure.mapping.modbus","native_owner":"helianthus-docs-modbus","source_refs":["modbus_docs","modbusreg"],"state":"unknown_profile_specific","qualification":"no_profile_selected_no_projection","control_route":"none","live_authority":False,"loss":"unknown"},
    "infrastructure.mapping.eebus": {"id":"infrastructure.mapping.eebus","native_owner":"helianthus-docs-eebus","source_refs":["eebus_ledger","eebus_m625_donor"],"state":"unknown_pending_normative_source","qualification":"unresolved","control_route":"none","live_authority":False,"loss":"unknown"},
    "infrastructure.mapping.matter": {"id":"infrastructure.mapping.matter","native_owner":"matter_draft","source_refs":["matter_draft"],"state":"candidate_design_input_only","qualification":"not_conformance","control_route":"none","live_authority":False,"loss":"unknown"},
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
    found, orders = {}, []
    for item in items:
        identifier = item.get("id") if isinstance(item, dict) else None
        if not isinstance(identifier, str) or not ID.fullmatch(identifier):
            raise ValueError(f"{label} invalid ID")
        if item.get("ref") != {"pack": PACK, "id": identifier, "version": "1.0.0"}:
            raise ValueError(f"{label} missing exact DefinitionRef owner/version")
        if identifier in found:
            raise ValueError(f"duplicate definition ID in {label}")
        found[identifier] = item
        orders.append(item.get("order"))
    if not all(type(order) is int and order > 0 for order in orders) or orders != sorted(orders) or len(orders) != len(set(orders)):
        raise ValueError(f"{label} noncanonical order")
    exact(set(found), set(expected), f"{label} catalog")
    return found


def decimal(value):
    if not isinstance(value, dict) or set(value) != {"coefficient", "exponent10"}:
        raise ValueError("bounds must use canonical kernel Decimal")
    coefficient, exponent = value["coefficient"], value["exponent10"]
    if not isinstance(coefficient, str) or not re.fullmatch(r"0|-?[1-9][0-9]*", coefficient) or type(exponent) is not int or not -18 <= exponent <= 18 or (coefficient == "0" and exponent != 0) or (coefficient != "0" and coefficient.endswith("0")):
        raise ValueError("bounds must use canonical kernel Decimal")
    return int(coefficient), exponent

def require_canonical_unit(unit):
    if unit not in CANONICAL_UNITS:
        raise ValueError("field unit is outside the canonical SI unit set")


def less(left, right):
    lc, le = decimal(left)
    rc, rexp = decimal(right)
    shared = min(le, rexp)
    return lc * 10 ** (le - shared) < rc * 10 ** (rexp - shared)


def definition_groups(catalog):
    definitions = catalog.get("definitions", {})
    if not isinstance(definitions, dict) or set(definitions) != DEFINITION_GROUPS:
        raise ValueError("definition groups must be exactly " + ", ".join(sorted(DEFINITION_GROUPS)))
    return definitions


def validate_defs(catalog):
    definitions = definition_groups(catalog)
    fields = refs(definitions.get("fields"), "fields", FIELD_CONTRACTS)
    for identifier, item in fields.items():
        kind, unit, dimension, optional, symbols, minimum, maximum = FIELD_CONTRACTS[identifier]
        base = {"id", "ref", "kind", "dimension", "optional", "order"}
        if (item.get("kind"), item.get("dimension"), item.get("optional")) != (kind, dimension, optional):
            raise ValueError("field has noncanonical kind, dimension, or optionality")
        if identifier in QUALIFIED:
            check_qualified_field(identifier, item, kind, unit, base)
            continue
        if kind == "quantity":
            check_plain_quantity(item, unit, minimum, maximum, base)
        else:
            check_text_or_symbol(item, kind, symbols, base)
    dimensions = refs(definitions.get("fact_dimensions"), "fact dimensions", DIMS)
    if any(set(item) != {"id", "ref", "value_kind", "order"} or item.get("value_kind") != "text" for item in dimensions.values()):
        raise ValueError("dimension association")
    check_qualifier_dimensions(definitions)
    services = refs(definitions.get("services"), "services", SERVICES)
    if any(set(item) != {"id", "ref", "fact_key_dimension", "order"} or item.get("fact_key_dimension") != SERVICES[key] for key, item in services.items()):
        raise ValueError("service association")
    relations = refs(definitions.get("relations"), "relations", RELATIONS)
    if any(set(item) != {"id", "ref", "from", "to", "cardinality", "order"} or (item.get("from"), item.get("to"), item.get("cardinality")) != RELATIONS[key] for key, item in relations.items()):
        raise ValueError("relation association")
    capabilities = refs(definitions.get("capabilities"), "capabilities", CAPS)
    if any(set(item) != {"id", "ref", "service", "activation", "order"} or item.get("service") != CAPS[key] or item.get("activation") != "qualified_current_binding" for key, item in capabilities.items()):
        raise ValueError("capability association")
    check_read_only(definitions)
    portal = refs(definitions.get("portal_contributions"), "Portal contributions", PORTAL)
    coverage = set()
    for key, item in portal.items():
        service, members = PORTAL[key]
        if set(item) != {"id", "ref", "kind", "service", "fields", "order"} or item.get("kind") != "read" or item.get("service") != service or tuple(item.get("fields", ())) != members:
            raise ValueError("Portal read association")
        coverage.update(members)
    exact(coverage, set(fields), "Portal read field coverage")
    if "events" in DEFINITION_GROUPS:
        check_events(definitions)


def check_read_only(definitions):
    if definitions.get("operations") != [] or definitions.get("effect_rules") != []:
        raise ValueError("read-only operation boundary")


def check_plain_quantity(item, unit, minimum, maximum, base):
    if unit is None:
        if "unit" in item or minimum is not None or maximum is not None or set(item) != base | {"bounds"} or item.get("bounds") != {"minimum": None, "maximum": None}:
            raise ValueError("field has invalid canonical quantity contract")
        return
    require_canonical_unit(item.get("unit"))
    if minimum is None and maximum is None:
        if set(item) != base | {"unit", "bounds"} or item.get("unit") != unit or item.get("bounds") != {"minimum": None, "maximum": None}:
            raise ValueError("field has invalid canonical quantity contract")
        return
    bounds = {"minimum": {"coefficient": minimum[0], "exponent10": minimum[1]}, "maximum": {"coefficient": maximum[0], "exponent10": maximum[1]}}
    if set(item) != base | {"unit", "bounds"} or item.get("unit") != unit or item.get("bounds") != bounds or not less(bounds["minimum"], bounds["maximum"]):
        raise ValueError("field has invalid canonical quantity contract")


def check_text_or_symbol(item, kind, symbols, base):
    if kind == "text":
        if set(item) != base:
            raise ValueError("field has invalid canonical text contract")
        return
    if set(item) != base | {"symbols"} or tuple(item.get("symbols", ())) != tuple(symbols) or any(SYMBOL.fullmatch(symbol) is None for symbol in item.get("symbols", ())):
        raise ValueError("field has invalid canonical symbol contract")


def check_qualified_field(identifier, item, kind, unit, base):
    if tuple(item.get("qualifiers", ())) != QUALIFIED[identifier]:
        raise ValueError("field qualifiers")
    if kind == "boolean":
        if set(item) != base | {"qualifiers"}:
            raise ValueError("field qualifiers")
        return
    members = base | {"bounds", "qualifiers"}
    if unit is None:
        if "unit" in item or set(item) != members or item.get("bounds") != {"minimum": None, "maximum": None}:
            raise ValueError("field has invalid canonical quantity contract")
        return
    require_canonical_unit(item.get("unit"))
    if set(item) != members | {"unit"} or item.get("unit") != unit or item.get("bounds") != {"minimum": None, "maximum": None}:
        raise ValueError("field has invalid canonical quantity contract")


def check_qualifier_dimensions(definitions):
    qualifiers = refs(definitions.get("qualifier_dimensions"), "qualifier dimensions", QUALIFIER_DIMS)
    for ident, item in qualifiers.items():
        if ident == "infrastructure.dimension.harmonic_order":
            if set(item) != {"id", "ref", "value_kind", "unit", "order"} or item.get("value_kind") != "quantity" or item.get("unit") != "unit.one":
                raise ValueError("qualifier dimension")
            continue
        if set(item) != {"id", "ref", "value_kind", "symbols", "order"} or item.get("value_kind") != "symbol" or tuple(item.get("symbols", ())) != MEASUREMENT_SYMBOLS:
            raise ValueError("qualifier dimension")


def check_events(definitions):
    events = refs(definitions.get("events"), "events", EVENTS)
    for ident, item in events.items():
        spec = EVENTS[ident]
        if set(item) != {"id", "ref", "service", "trigger", "condition", "payload", "origin", "order"} or item.get("service") != spec["service"] or item.get("trigger") != spec["trigger"] or item.get("condition") != spec["condition"] or tuple(item.get("payload", ())) != tuple(spec["payload"]) or item.get("origin") != spec["origin"]:
            raise ValueError("event association")


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
    exact(catalog.get("read_only_operation_boundary"), READ_ONLY, "read-only operation boundary")
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


def validate_document(document):
    if document.get("contract") != "helianthus.semantic.pack.infrastructure.acceptance/v1" or document.get("pack_contract") != "helianthus.pack.infrastructure/v1":
        raise ValueError("contract ID")
    validate_catalog(document.get("catalog"))
    vectors = document.get("vectors", [])
    if not any(vector.get("polarity") == "positive" for vector in vectors) or not any(vector.get("polarity") == "negative" for vector in vectors):
        raise ValueError("positive and negative vectors")
    for vector in vectors:
        candidate = copy.deepcopy(document["catalog"])
        for mutation in vector.get("input", {}).get("mutations", []):
            parent, key = resolve(candidate, mutation["path"])
            if mutation.get("op") != "set":
                raise ValueError("unknown vector mutation")
            parent[key] = mutation.get("value")
        if vector.get("polarity") == "positive":
            validate_catalog(candidate)
            continue
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
    print("infrastructure pack v1: PASS")


if __name__ == "__main__":
    main()
