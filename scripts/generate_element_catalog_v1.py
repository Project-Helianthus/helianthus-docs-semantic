#!/usr/bin/env python3
"""Generate the element catalog seed from the accepted packs.

``python3 scripts/generate_element_catalog_v1.py`` writes
``api/v1/element-catalog-v1.json`` and ``scripts/element-catalog-seed-refs.json``.
``--check`` writes nothing and exits 1 when either committed file differs from
a fresh generation. The generator reads repository inputs only and uses the
standard library only. It runs once to produce the seed; after the seed is
reviewed, entries change only by reviewed edits and the generator is not
re-run over reviewed decisions.

Inputs: ``catalog.definitions`` of the thermal, PV, EVSE and infrastructure
acceptance vectors; the storage contract tables; the kernel state types and
their values in ``api/v1/kernel.md``; the six state types that
``api/v1/graph.md`` adds, the core relation types (section 7.1), the plane
questions (section 8.1) and the element-kind lists (section 10.2) of
``api/v1/graph.md``.

Rules of the catalog seed outline and the attributes they produce:

| Rule | Attribute it produces |
|---|---|
| D1 | one core resource kind per resource dimension; the kind's anchor class; ``resource_kind`` of a resource dimension |
| D2 | admission of the 27 derived kinds (``accepted_pack``, the accepting pack pages) |
| D3 | role ``qualifier`` for a dimension that fields reference but the pack does not declare; ``unknown`` when it qualifies only unresolved facts |
| F1 | fact ``subject``: resolved to the kind of a resource dimension, else unresolved with its qualifier dimension and disposition ``unknown`` |
| F2 | fact ``planes`` from the second segment of the field identifier |
| F3 | fact ``aggregation`` |
| F4 | fact ``direction`` and ``sign_reference`` (``native_convention``) |
| S1 | service ``fact_key_dimension``, ``subject_kind`` and the kind's planes |
| C1 | capability ``service``, ``operation`` and planes (service planes, plus control when an operation uses it) |
| O1 | operation ``capability``, ``argument``, ``effect_rule`` and planes (control plus the argument's planes); effect rule ``operation``, ``fact`` and the operation's planes; ``unknown`` when the argument is ``unknown`` |
| R1 | pack relation ``core_type``, ``orientation``, ``from_kinds``, ``to_kinds``, ``cardinality``, ``over_time``, ``medium``, ``basis_classes``, ``endpoint_dimensions`` and derived planes |
| R2 | core relation ``relation.relays`` between the six equipment kinds, plane provenance |
| Kind planes (7) | physical for equipment and component, the planes of the kind's facts and of every relation touching it; ``unknown`` when none |
| Kernel vocabulary (8) | evidence and lifecycle states with ``kernel_type``, ``values`` and planes |
| Presentation (8) | Portal descriptors and target vocabulary, ``unsupported`` with a final reason |
| Tracking (9) | ``reason`` and ``tracking`` of every ``unknown`` entry |

Plane lists follow the plane order of graph section 8.1. Entries follow the
canonical order CAT-8. The admission records of the seven core relation types,
``resource.equipment`` and ``relation.relays`` are copied into
``CITED_ADMISSIONS``.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = "api/v1/element-catalog-v1.json"
SEED_REFS_PATH = "scripts/element-catalog-seed-refs.json"
KERNEL_PAGE = "api/v1/kernel.md"
GRAPH_PAGE = "api/v1/graph.md"
STORAGE_TABLES = "api/v1/packs/storage-bms-contract-tables.json"
STORAGE_PAGE = "storage-bms-v1.md"
VECTOR_PACKS = (
    ("api/v1/packs/thermal-hvac-acceptance-vectors.json", "thermal-hvac-v1.md"),
    ("api/v1/packs/pv-inverter-acceptance-vectors.json", "pv-inverter-v1.md"),
    ("api/v1/packs/evse-acceptance-vectors.json", "evse-v1.md"),
    ("api/v1/packs/infrastructure-acceptance-vectors.json", "infrastructure-v1.md"),
)

DOCS_BLOB = "https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/f4f62ce20ce4b643f8f7d75d97063a1b0d346cee/"
CONTRACT_ISSUE = "https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/67"
TRACKING_ISSUE = "https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/68"
KERNEL_CONTRACT = "helianthus.semantic.kernel/v1"
CORE_VERSION = "1.0.0"
CORE_OWNER = {"kind": "core", "contract": KERNEL_CONTRACT}
CATALOG_ORDER = "owner kind, pack id, pack version, element id, element version as canonical UTF-8 byte sequence"
SEED_REFS_CONTRACT = "helianthus.semantic.element-catalog-seed-refs/v1"

PLANES = ("physical", "energy", "hydraulic", "control", "diagnostic", "provenance")
BASIS_ORDER = ("native_observation", "configuration", "gate_rule")
LOCATED_CLASSES = ("equipment", "component")

REASON_SUBJECT = "catalog.reason.subject_unresolved"
REASON_QUALIFIER = "catalog.reason.qualifier_of_unresolved_facts"
REASON_NO_PLACE = "catalog.reason.no_fact_or_relation"
REASON_ARGUMENT = "catalog.reason.argument_unresolved"
REASON_PRESENTATION = "catalog.reason.target_presentation"

MATTER_BLOB = "https://github.com/AryaHassanli/connectedhomeip/blob/29b4768a513cf566011ab8cd60df1bc495204953/data_model/1.7/"
CITED_ADMISSIONS = {
    "contains": ("matter_baseline", ("clusters/Descriptor-Cluster.xml",)),
    "groups": ("matter_baseline", ("clusters/Groups.xml", "clusters/Descriptor-Cluster.xml")),
    "supplies": ("matter_baseline", ("clusters/PowerTopology.xml",)),
    "measures": ("matter_baseline", ("device_types/ElectricalSensor.xml", "clusters/PowerTopology.xml")),
    "controls": ("matter_baseline", ("clusters/Binding-Cluster.xml",)),
    "hosts": ("matter_baseline", ("clusters/EnergyEVSE.xml",)),
    "relays": ("matter_baseline", (
        "device_types/Aggregator.xml",
        "device_types/BridgedNode.xml",
        "clusters/BridgedDeviceBasicInformationCluster.xml",
    )),
    "resource.equipment": ("matter_baseline", (
        "device_types/BridgedNode.xml",
        "device_types/RootNodeDeviceType.xml",
    )),
    "relation.relays": ("matter_baseline", (
        "device_types/Aggregator.xml",
        "device_types/BridgedNode.xml",
    )),
}

# Rule D1: core kind -> (anchor class, pack dimensions mapped to it).
KIND_RULES = {
    "resource.thermal_system": ("function", ("thermal.dimension.system",)),
    "resource.zone": ("function", ("thermal.dimension.zone",)),
    "resource.thermal_circuit": ("function", ("thermal.dimension.circuit",)),
    "resource.domestic_hot_water": ("function", ("thermal.dimension.dhw",)),
    "resource.ventilation_system": ("function", ("thermal.dimension.ventilation",)),
    "resource.pv_system": ("function", ("pv.dimension.system",)),
    "resource.inverter": ("equipment", ("pv.dimension.inverter",)),
    "resource.pv_array": ("function", ("pv.dimension.array",)),
    "resource.pv_string": ("component", ("pv.dimension.string",)),
    "resource.dc_input": ("component", ("pv.dimension.input",)),
    "resource.phase": ("component", (
        "pv.dimension.phase", "evse.dimension.phase", "infrastructure.dimension.phase",
    )),
    "resource.storage_system": ("function", ("storage.dimension.system",)),
    "resource.battery": ("equipment", ("storage.dimension.battery",)),
    "resource.battery_pack": ("equipment", ("storage.dimension.pack",)),
    "resource.battery_module": ("component", ("storage.dimension.module",)),
    "resource.battery_cell": ("component", ("storage.dimension.cell",)),
    "resource.battery_string": ("component", ("storage.dimension.string",)),
    "resource.storage_interface": ("component", ("storage.dimension.interface",)),
    "resource.charging_station": ("equipment", ("evse.dimension.asset",)),
    "resource.evse": ("component", ("evse.dimension.evse",)),
    "resource.connector": ("component", ("evse.dimension.connector",)),
    "resource.charging_session": ("episode", ("evse.dimension.session",)),
    "resource.meter": ("equipment", ("evse.dimension.meter", "infrastructure.dimension.meter")),
    "resource.site": ("function", ("infrastructure.dimension.site",)),
    "resource.grid_connection": ("function", ("infrastructure.dimension.grid_connection",)),
    "resource.feeder": ("function", ("infrastructure.dimension.feeder",)),
    "resource.electrical_circuit": ("function", ("infrastructure.dimension.circuit",)),
    "resource.equipment": ("equipment", ()),
}

# Rule R1: pack relation -> (core type, orientation, basis classes).
RELATION_RULES = {
    "pv.relationship.system_inverter": ("groups", "as_core", ("gate_rule", "configuration")),
    "pv.relationship.inverter_array": ("supplies", "inverse", ("configuration",)),
    "pv.relationship.array_string": ("contains", "as_core", ("configuration",)),
    "pv.relationship.inverter_input": ("contains", "as_core", ("gate_rule",)),
    "pv.relationship.inverter_phase": ("contains", "as_core", ("gate_rule",)),
    "infrastructure.relationship.site_grid_connection": ("contains", "as_core", ("configuration",)),
    "infrastructure.relationship.grid_connection_feeder": ("supplies", "as_core", ("configuration",)),
    "infrastructure.relationship.feeder_circuit": ("supplies", "as_core", ("configuration",)),
    "infrastructure.relationship.circuit_phase": ("contains", "as_core", ("configuration",)),
    "infrastructure.relationship.grid_connection_meter": ("measures", "inverse", ("configuration",)),
    "evse.relationship.asset_evse": ("contains", "as_core", ("configuration",)),
    "evse.relationship.evse_connector": ("contains", "as_core", ("configuration",)),
    "evse.relationship.connector_phase": ("contains", "as_core", ("gate_rule",)),
    "evse.relationship.connector_session": ("hosts", "as_core", ("gate_rule",)),
    "evse.relationship.evse_meter": ("measures", "inverse", ("configuration",)),
    "storage.relationship.system_battery": ("groups", "as_core", ("configuration",)),
    "storage.relationship.battery_pack": ("contains", "as_core", ("gate_rule",)),
    "storage.relationship.pack_module": ("contains", "as_core", ("gate_rule",)),
    "storage.relationship.module_cell": ("contains", "as_core", ("gate_rule",)),
    "storage.relationship.pack_string": ("contains", "as_core", ("gate_rule",)),
    "storage.relationship.pack_interface": ("contains", "as_core", ("gate_rule",)),
}
SUPPLIES_MEDIUM = "electrical"
MEDIUM_PLANES = {
    "electrical": ("energy",),
    "air": ("energy",),
    "heat_transfer_fluid": ("energy", "hydraulic"),
    "refrigerant": ("energy", "hydraulic"),
}
DEFAULT_CARDINALITY = "one_to_many"

# Rule F2: second segment of the field identifier -> planes.
FIELD_CLASS_PLANES = {
    "dc": ("energy",), "ac": ("energy",), "power": ("energy",), "pack": ("energy",),
    "cell": ("energy",), "energy": ("energy",), "capacity": ("energy",), "state": ("energy",),
    "limit": ("energy", "control"),
    "mode": ("control",), "action": ("control",),
    "temperature": ("diagnostic",),
    "status": ("diagnostic",),
}
INTERLOCK_CLASS = "status.interlock"
# Rule F3.
MEMBER_CLASSES = frozenset({
    "dc", "ac", "power", "pack", "cell", "energy", "capacity", "state", "measurement", "temperature",
})
GROUPING_KINDS = frozenset({"resource.pv_system", "resource.storage_system", "resource.site"})
# Rule F4.
FLOW_UNITS = frozenset({
    "unit.watt", "unit.ampere", "unit.kilowatt_hour", "unit.volt_ampere",
    "unit.volt_ampere_reactive", "unit.ampere_hour",
})
POWER_FACTOR_SUFFIX = ".power_factor"

# Kernel vocabulary (section 8 of the outline).
GRAPH_ADDED_TYPES = frozenset({
    "AnchorClass", "AnchorBasis", "RelationBasis", "ResourceState", "RelationCoherence", "CutFindingKind",
})
VALUE_LABELS = {"RetainedRemoval": "Removal"}
VALUE_TABLES = {
    "Outcome": "`Outcome` is one of:",
    "RelationBasis": "Basis classes (`RelationBasis`):",
    "RelationCoherence": "Every relation instance gets one `RelationCoherence`:",
    "CutFindingKind": "(`CutFindingKind`):",
}
STATE_PLANES = {
    "Validity": ("diagnostic", "provenance"),
    "Freshness": ("diagnostic", "provenance"),
    "SourceState": ("provenance",),
    "BindingState": ("provenance",),
    "LinkState": ("provenance",),
    "ResourceState": ("provenance",),
    "RetainedRemoval": ("provenance",),
    "Availability": ("diagnostic",),
    "ConflictState": ("diagnostic",),
    "RelationCoherence": ("diagnostic",),
    "CutFindingKind": ("diagnostic",),
    "Outcome": ("control",),
    "DeliveryState": ("control",),
    "AckState": ("control",),
    "ReadbackRelation": ("control",),
}
EVIDENCE_STATE_PLANES = ("provenance",)


class SeedError(ValueError):
    """An input does not satisfy a seed rule; nothing is written."""


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def ordered_planes(planes):
    unknown = set(planes) - set(PLANES)
    if unknown:
        raise SeedError(f"unknown planes: {sorted(unknown)}")
    return [plane for plane in PLANES if plane in planes]


def pack_ref(pack, element_id, version):
    return {"owner": {"kind": "pack", "pack": dict(pack)}, "id": element_id, "version": version}


def core_ref(element_id):
    return {"owner": dict(CORE_OWNER), "id": element_id, "version": CORE_VERSION}


def page_url(page):
    return DOCS_BLOB + "api/v1/packs/" + page


def cited(key):
    arm, paths = CITED_ADMISSIONS[key]
    return {"arm": arm, "evidence": [MATTER_BLOB + path for path in paths]}


def owner_decision():
    return {"arm": "owner_decision", "evidence": [CONTRACT_ISSUE]}


def accepted_kernel():
    return {"arm": "accepted_kernel", "evidence": [DOCS_BLOB + KERNEL_PAGE]}


def accepted_pack(pages):
    return {"arm": "accepted_pack", "evidence": sorted({page_url(page) for page in pages})}


# ---------------------------------------------------------------- pack inputs


def vector_relation(item):
    cardinality = item.get("cardinality", DEFAULT_CARDINALITY)
    over_time = cardinality.endswith("_over_time")
    return {
        "id": item["id"], "version": item["ref"]["version"],
        "from": item["from"], "to": item["to"],
        "cardinality": cardinality.removesuffix("_over_time"), "over_time": over_time,
    }


def vector_field(item):
    bounds = item.get("bounds")
    return {
        "id": item["id"], "version": item["ref"]["version"], "kind": item["kind"],
        "unit": item.get("unit"), "dimension": item["dimension"],
        "minimum": None if bounds is None else bounds.get("minimum"),
    }


def load_vector_pack(path, page):
    catalog = read_json(path)["catalog"]
    defs = catalog["definitions"]
    for group in defs.values():
        for item in group:
            if item["ref"]["pack"] != catalog["pack"] or item["ref"]["id"] != item["id"]:
                raise SeedError(f"{item['id']}: reference does not name its own pack")
    return {
        "pack": catalog["pack"], "page": page,
        "dimensions": [(item["id"], item["ref"]["version"]) for item in defs["fact_dimensions"]],
        "fields": [vector_field(item) for item in defs["fields"]],
        "services": [{"id": item["id"], "version": item["ref"]["version"],
                      "dimension": item["fact_key_dimension"]} for item in defs["services"]],
        "relations": [vector_relation(item) for item in defs.get("relationships", [])],
        "capabilities": [{"id": item["id"], "version": item["ref"]["version"],
                          "service": item["service"]} for item in defs["capabilities"]],
        "operations": [{"id": item["id"], "version": item["ref"]["version"],
                        "capability": item["capability"], "arguments": item["arguments"],
                        "effect": item["effect_rule"]} for item in defs["operations"]],
        "effects": [{"id": item["id"], "version": item["ref"]["version"],
                     "operation": item["operation"], "fact": item["fact"]} for item in defs["effect_rules"]],
        "portals": [(item["id"], item["ref"]["version"]) for item in defs["portal_contributions"]],
    }


def storage_versions(tables):
    index = tables["definition_index"]
    versions = {}
    for group in ("fields", "services", "capabilities", "operations", "effect_rules"):
        for item in index[group]:
            if item["pack"] != index["pack"]:
                raise SeedError(f"{item['id']}: storage index names another pack")
            versions[item["id"]] = item["version"]
    return versions


def storage_field(item, versions):
    bounds = item.get("bounds")
    return {
        "id": item["id"], "version": versions[item["id"]], "kind": item["kind"],
        "unit": item.get("unit"), "dimension": item["dimension"],
        "minimum": None if bounds is None else bounds.get("minimum"),
    }


def load_storage_pack():
    tables = read_json(STORAGE_TABLES)
    pack = tables["definition_index"]["pack"]
    versions = storage_versions(tables)
    service_dimension = {item["id"]: item["dimension"] for item in tables["services"]}
    dimensions = []
    for item in sorted(tables["services"], key=lambda entry: entry["order"]):
        if item["dimension"] not in dimensions:
            dimensions.append(item["dimension"])
    return {
        "pack": pack, "page": STORAGE_PAGE,
        "dimensions": [(dimension, pack["version"]) for dimension in dimensions],
        "fields": [storage_field(item, versions) for item in tables["field_specs"]],
        "services": [{"id": item["id"], "version": versions[item["id"]],
                      "dimension": item["dimension"]} for item in tables["services"]],
        "relations": [{"id": item["id"], "version": pack["version"],
                       "from": service_dimension[item["source"]], "to": service_dimension[item["target"]],
                       "cardinality": item["cardinality"], "over_time": False} for item in tables["relationships"]],
        "capabilities": [{"id": item["id"], "version": versions[item["id"]],
                          "service": item["service"]} for item in tables["capabilities"]],
        "operations": [{"id": item["id"], "version": versions[item["id"]], "capability": item["capability"],
                        "arguments": [item["input"]], "effect": item["effect"]} for item in tables["operations"]],
        "effects": [{"id": item["id"], "version": versions[item["id"]], "operation": item["operation"],
                     "fact": item["field"]} for item in tables["effects"]],
        "portals": [(item["id"], pack["version"]) for item in tables["portal_contributions"]],
    }


def load_packs():
    packs = [load_vector_pack(path, page) for path, page in VECTOR_PACKS]
    packs.append(load_storage_pack())
    return packs


# ------------------------------------------------------------ markdown inputs


def section(text, heading):
    start = text.find("\n" + heading + "\n")
    if start < 0:
        raise SeedError(f"missing section: {heading}")
    level = heading.split(" ", 1)[0]
    rest = text[start + len(heading) + 2:]
    stop = re.search(r"\n#{1,%d} " % len(level), rest)
    return rest if stop is None else rest[:stop.start()]


def table_after(text, marker):
    start = text.find(marker)
    if start < 0 or text.find(marker, start + 1) >= 0:
        raise SeedError(f"marker must occur exactly once: {marker}")
    if marker.startswith("|"):
        start = text.rfind("\n", 0, start) + 1
    else:
        start += len(marker)
    lines = text[start:].lstrip("\n").splitlines()
    rows = []
    for line in lines:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    if len(rows) < 3 or set(rows[1][0]) - set("-: "):
        raise SeedError(f"no table after: {marker}")
    return rows[2:]


def ticked(cell):
    names = re.findall(r"`([^`]+)`", cell)
    if not names:
        raise SeedError(f"no code value in: {cell}")
    return names


def inline_values(text, name):
    pattern = re.compile(
        r"`%s`(?::| is(?: exactly)?)\s+(`[a-z_]+`(?:,?\s+(?:or\s+)?`[a-z_]+`)*)" % re.escape(name)
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise SeedError(f"value sentence of {name} must occur exactly once, found {len(matches)}")
    return re.findall(r"`([a-z_]+)`", matches[0])


def kernel_values(name, kernel_text, graph_text):
    text = graph_text if name in GRAPH_ADDED_TYPES else kernel_text
    if name in VALUE_TABLES:
        return [ticked(row[0])[0] for row in table_after(text, VALUE_TABLES[name])]
    return inline_values(text, VALUE_LABELS.get(name, name))


def element_kind_lists(graph_text):
    block = section(graph_text, "### 10.2 Element kinds")
    lists = {}
    for kind in ("evidence_state", "lifecycle_state", "presentation"):
        match = re.search(r"^- `%s`[^:]*:(.*?)(?=^- `|\n\n)" % kind, block, re.M | re.S)
        if match is None:
            raise SeedError(f"graph section 10.2 lists no {kind} types")
        lists[kind] = [name for name in re.findall(r"`([A-Za-z]+)`", match.group(1)) if name[0].isupper()]
    return lists


def planes_table(graph_text):
    rows = table_after(section(graph_text, "### 8.1 The planes"), "| Plane |")
    return [{"id": ticked(row[0])[0], "question": row[1], "admission": owner_decision()} for row in rows]


def plane_names(cell):
    if cell == "none":
        return []
    return ordered_planes([name.strip() for name in cell.split(",")])


def core_types_table(graph_text):
    rows = table_after(section(graph_text, "### 7.1 Core relation types"), "| Type |")
    result = []
    for row in rows:
        type_id = ticked(row[0])[0]
        result.append({
            "id": type_id, "reads": row[1], "structure": row[2],
            "allowed_planes": plane_names(row[3]), "required_planes": plane_names(row[4]),
            "admission": cited(type_id),
        })
    return result


# ------------------------------------------------------------------ the model


class Model:
    """Pack definitions indexed for the seed rules."""

    def __init__(self, packs):
        self.packs = packs
        self.kind_of = {}
        self.anchor = {}
        for kind, (anchor, dimensions) in KIND_RULES.items():
            self.anchor[kind] = anchor
            for dimension in dimensions:
                self.kind_of[dimension] = kind
        self.dimension_ref = {}
        self.resource_dims = set()
        self.fields = {}
        self.owner_pack = {}
        for pack in packs:
            self._index(pack)
        missing = sorted(set(self.kind_of) - self.resource_dims)
        if missing:
            raise SeedError(f"rule D1 names dimensions no pack declares: {missing}")
        self.fact_planes = {field_id: field_planes(field, self) for field_id, field in self.fields.items()}
        self.kind_fact_planes = self._kind_fact_planes()

    def _index(self, pack):
        for dimension, version in pack["dimensions"]:
            if dimension not in self.kind_of:
                raise SeedError(f"rule D1 maps no kind to {dimension}")
            self.dimension_ref[dimension] = pack_ref(pack["pack"], dimension, version)
            self.resource_dims.add(dimension)
            self.owner_pack[dimension] = pack
        for field in pack["fields"]:
            self.fields[field["id"]] = field
            self.owner_pack[field["id"]] = pack
            if field["dimension"] not in self.dimension_ref:
                self.dimension_ref[field["dimension"]] = pack_ref(pack["pack"], field["dimension"], pack["pack"]["version"])
                self.owner_pack[field["dimension"]] = pack

    def _kind_fact_planes(self):
        result = {kind: set() for kind in KIND_RULES}
        for field_id, field in self.fields.items():
            if field["dimension"] in self.resource_dims:
                result[self.kind_of[field["dimension"]]].update(self.fact_planes[field_id])
        return result

    def is_resolved(self, field_id):
        return self.fields[field_id]["dimension"] in self.resource_dims


def field_class(field_id):
    return field_id.split(".")[1]


def field_planes(field, model):
    if field["dimension"] not in model.resource_dims:
        return set()
    name = field_class(field["id"])
    if name not in FIELD_CLASS_PLANES:
        raise SeedError(f"rule F2 has no planes for {field['id']}")
    planes = set(FIELD_CLASS_PLANES[name])
    if field["id"].split(".", 1)[1].startswith(INTERLOCK_CLASS):
        planes.add("control")
    return planes


# ------------------------------------------------------------------ relations


def core_endpoints(relation):
    rule = RELATION_RULES[relation["id"]]
    if rule[1] == "as_core":
        return relation["from"], relation["to"]
    return relation["to"], relation["from"]


def relation_planes(relation, model):
    core_type = RELATION_RULES[relation["id"]][0]
    to_kind = model.kind_of[core_endpoints(relation)[1]]
    to_planes = model.kind_fact_planes[to_kind]
    if core_type == "contains":
        return {"physical"} | (to_planes & {"energy", "hydraulic", "diagnostic"})
    if core_type == "groups":
        located = {"physical"} if model.anchor[to_kind] in LOCATED_CLASSES else set()
        return located | (to_planes & {"energy", "hydraulic", "control"})
    if core_type == "supplies":
        return set(MEDIUM_PLANES[SUPPLIES_MEDIUM])
    if core_type == "measures":
        return to_planes & {"energy"}
    if core_type == "hosts":
        return to_planes & {"energy", "control", "diagnostic"}
    raise SeedError(f"rule R1 derives no planes for {relation['id']}")


def relation_entry(pack, relation, model):
    if relation["id"] not in RELATION_RULES:
        raise SeedError(f"rule R1 has no core type for {relation['id']}")
    core_type, orientation, basis = RELATION_RULES[relation["id"]]
    planes = relation_planes(relation, model)
    if not planes:
        raise SeedError(f"rule R1 derives an empty plane set for {relation['id']}")
    attributes = {
        "core_type": core_type, "orientation": orientation,
        "from_kinds": [model.kind_of[relation["from"]]], "to_kinds": [model.kind_of[relation["to"]]],
        "cardinality": relation["cardinality"], "over_time": relation["over_time"],
    }
    if core_type == "supplies":
        attributes["medium"] = SUPPLIES_MEDIUM
    attributes["basis_classes"] = [name for name in BASIS_ORDER if name in basis]
    attributes["endpoint_dimensions"] = {
        "from": model.dimension_ref[relation["from"]], "to": model.dimension_ref[relation["to"]],
    }
    return member(pack_ref(pack["pack"], relation["id"], relation["version"]), "relation", planes,
                  accepted_pack([pack["page"]]), attributes)


def relays_kinds():
    return sorted(kind for kind, (anchor, _) in KIND_RULES.items() if anchor == "equipment")


def relays_entry():
    kinds = relays_kinds()
    attributes = {
        "core_type": "relays", "orientation": "as_core", "from_kinds": kinds, "to_kinds": kinds,
        "cardinality": "many_to_many", "over_time": False,
        "basis_classes": ["native_observation", "configuration"],
    }
    return member(core_ref("relation.relays"), "relation", {"provenance"}, cited("relation.relays"), attributes)


# -------------------------------------------------------------------- entries


def member(ref, element_kind, planes, admission, attributes):
    return {
        "ref": ref, "element_kind": element_kind, "disposition": "member",
        "planes": ordered_planes(planes), "admission": admission, "attributes": attributes,
    }


def unknown(ref, element_kind, reason, admission, attributes):
    return {
        "ref": ref, "element_kind": element_kind, "disposition": "unknown", "planes": [],
        "reason": reason, "tracking": TRACKING_ISSUE, "admission": admission, "attributes": attributes,
    }


def unsupported(ref, admission, target):
    return {
        "ref": ref, "element_kind": "presentation", "disposition": "unsupported", "planes": [],
        "reason": REASON_PRESENTATION, "admission": admission, "attributes": {"target": target},
    }


def placed(ref, element_kind, planes, admission, attributes, reason):
    if planes:
        return member(ref, element_kind, planes, admission, attributes)
    return unknown(ref, element_kind, reason, admission, attributes)


def kind_planes(model, relations):
    result = {}
    for kind, (anchor, _) in KIND_RULES.items():
        planes = set(model.kind_fact_planes[kind])
        if anchor in LOCATED_CLASSES:
            planes.add("physical")
        result[kind] = planes
    for entry in relations:
        for kind in entry["attributes"]["from_kinds"] + entry["attributes"]["to_kinds"]:
            result[kind].update(entry["planes"])
    return result


def kind_entries(model, planes_of_kind):
    entries = []
    for kind, (anchor, dimensions) in KIND_RULES.items():
        if dimensions:
            admission = accepted_pack([model.owner_pack[dimension]["page"] for dimension in dimensions])
        else:
            admission = cited(kind)
        entries.append(placed(core_ref(kind), "resource_kind", planes_of_kind[kind], admission,
                              {"anchor_class": anchor}, REASON_NO_PLACE))
    return entries


def dimension_entries(model, planes_of_kind):
    entries = []
    for dimension, ref in model.dimension_ref.items():
        pack = model.owner_pack[dimension]
        admission = accepted_pack([pack["page"]])
        if dimension in model.resource_dims:
            kind = model.kind_of[dimension]
            attributes = {"role": "resource", "resource_kind": kind}
            entries.append(placed(ref, "dimension", planes_of_kind[kind], admission, attributes, REASON_NO_PLACE))
            continue
        users = [field for field in model.fields.values() if field["dimension"] == dimension]
        planes = set().union(*(model.fact_planes[field["id"]] for field in users))
        entries.append(placed(ref, "dimension", planes, admission, {"role": "qualifier"}, REASON_QUALIFIER))
    return entries


def fact_aggregation(field, kind):
    name = field_class(field["id"])
    if field["kind"] != "quantity" or name not in MEMBER_CLASSES:
        return "not_applicable"
    if "aggregate" in field["id"] or kind in GROUPING_KINDS:
        return "aggregate"
    return "member"


def allows_negative(field):
    minimum = field["minimum"]
    return minimum is None or minimum["coefficient"].startswith("-")


def fact_direction(field):
    is_flow = field["unit"] in FLOW_UNITS or field["id"].endswith(POWER_FACTOR_SUFFIX)
    if field["kind"] != "quantity" or not is_flow:
        return "not_applicable"
    return "signed" if allows_negative(field) else "non_negative"


def fact_entry(field, model):
    pack = model.owner_pack[field["id"]]
    ref = pack_ref(pack["pack"], field["id"], field["version"])
    dimension_ref = model.dimension_ref[field["dimension"]]
    kind = model.kind_of.get(field["dimension"]) if model.is_resolved(field["id"]) else None
    if kind is None:
        subject = {"status": "unresolved", "qualifier_dimension": dimension_ref}
    else:
        subject = {"status": "resolved", "dimension": dimension_ref, "kind": kind}
    attributes = {"value_kind": field["kind"], "subject": subject,
                  "aggregation": fact_aggregation(field, kind), "direction": fact_direction(field)}
    if attributes["direction"] == "signed":
        attributes["sign_reference"] = "native_convention"
    return placed(ref, "fact", model.fact_planes[field["id"]], accepted_pack([pack["page"]]), attributes,
                  REASON_SUBJECT)


def service_entries(pack, model, planes_of_kind, refs):
    entries = []
    for service in pack["services"]:
        ref = pack_ref(pack["pack"], service["id"], service["version"])
        refs[service["id"]] = ref
        kind = model.kind_of[service["dimension"]]
        attributes = {"fact_key_dimension": model.dimension_ref[service["dimension"]], "subject_kind": kind}
        entries.append(placed(ref, "service", planes_of_kind[kind], accepted_pack([pack["page"]]), attributes,
                              REASON_NO_PLACE))
    return entries


def operation_index(pack):
    by_capability = {}
    for operation in pack["operations"]:
        if operation["capability"] in by_capability:
            raise SeedError(f"two operations use {operation['capability']}")
        by_capability[operation["capability"]] = operation
    return by_capability


def capability_entries(pack, planes_of, refs):
    entries = []
    by_capability = operation_index(pack)
    for capability in pack["capabilities"]:
        ref = pack_ref(pack["pack"], capability["id"], capability["version"])
        refs[capability["id"]] = ref
        attributes = {"service": refs[capability["service"]]}
        planes = set(planes_of[capability["service"]])
        operation = by_capability.get(capability["id"])
        if operation is not None:
            attributes["operation"] = pack_ref(pack["pack"], operation["id"], operation["version"])
            if planes:
                planes.add("control")
        entries.append(placed(ref, "capability", planes, accepted_pack([pack["page"]]), attributes,
                              REASON_NO_PLACE))
    return entries


def operation_entries(pack, model, refs):
    entries = []
    effects = {effect["id"]: effect for effect in pack["effects"]}
    for operation in pack["operations"]:
        if len(operation["arguments"]) != 1:
            raise SeedError(f"{operation['id']}: rule O1 expects one argument field")
        argument = operation["arguments"][0]
        effect = effects[operation["effect"]]
        if effect["operation"] != operation["id"] or effect["fact"] != argument:
            raise SeedError(f"{effect['id']}: effect rule does not match its operation")
        planes = set(model.fact_planes[argument])
        if planes:
            planes.add("control")
        operation_ref = pack_ref(pack["pack"], operation["id"], operation["version"])
        effect_ref = pack_ref(pack["pack"], effect["id"], effect["version"])
        fact_ref = refs[argument]
        admission = accepted_pack([pack["page"]])
        entries.append(placed(operation_ref, "operation", planes, admission, {
            "capability": refs[operation["capability"]], "argument": fact_ref, "effect_rule": effect_ref,
        }, REASON_ARGUMENT))
        entries.append(placed(effect_ref, "effect_rule", planes, admission, {
            "operation": operation_ref, "fact": fact_ref,
        }, REASON_ARGUMENT))
    return entries


def pack_entries(pack, model, planes_of_kind):
    refs = {}
    entries = []
    for field in pack["fields"]:
        entry = fact_entry(field, model)
        refs[field["id"]] = entry["ref"]
        entries.append(entry)
    services = service_entries(pack, model, planes_of_kind, refs)
    planes_of = {entry["ref"]["id"]: set(entry["planes"]) for entry in services}
    entries.extend(services)
    entries.extend(capability_entries(pack, planes_of, refs))
    entries.extend(operation_entries(pack, model, refs))
    for portal_id, version in pack["portals"]:
        entries.append(unsupported(pack_ref(pack["pack"], portal_id, version), accepted_pack([pack["page"]]),
                                   "portal"))
    return entries


def snake_case(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def kernel_entries(graph_text, kernel_text):
    lists = element_kind_lists(graph_text)
    entries = []
    for element_kind in ("evidence_state", "lifecycle_state"):
        for name in lists[element_kind]:
            admission = owner_decision() if name in GRAPH_ADDED_TYPES else accepted_kernel()
            planes = STATE_PLANES.get(name, EVIDENCE_STATE_PLANES if element_kind == "evidence_state" else ())
            if not planes:
                raise SeedError(f"the kernel vocabulary rule places no plane for {name}")
            attributes = {"kernel_type": name, "values": kernel_values(name, kernel_text, graph_text)}
            entries.append(member(core_ref("kernel." + snake_case(name)), element_kind, set(planes), admission,
                                  attributes))
    for name in lists["presentation"]:
        kernel_values(name, kernel_text, graph_text)
        entries.append(unsupported(core_ref("kernel." + snake_case(name)), accepted_kernel(),
                                   "projection_vocabulary"))
    return entries


# --------------------------------------------------------------- the document


def catalog_key(entry):
    ref = entry["ref"]
    owner = ref["owner"]
    pack = owner.get("pack", {"id": "", "version": ""})
    parts = (owner["kind"], pack["id"], pack["version"], ref["id"], ref["version"])
    return tuple(part.encode("utf-8") for part in parts)


def check_closure(entries, core_types):
    planes_of_kind = {entry["ref"]["id"]: set(entry["planes"])
                      for entry in entries if entry["element_kind"] == "resource_kind"}
    limits = {core_type["id"]: core_type for core_type in core_types}
    for entry in entries:
        attributes = entry["attributes"]
        planes = set(entry["planes"])
        if entry["element_kind"] == "relation":
            limit = limits[attributes["core_type"]]
            if not planes <= set(limit["allowed_planes"]) or not set(limit["required_planes"]) <= planes:
                raise SeedError(f"{entry['ref']['id']}: planes outside its core type limits")
            for kind in attributes["from_kinds"] + attributes["to_kinds"]:
                if not planes <= planes_of_kind[kind]:
                    raise SeedError(f"{entry['ref']['id']}: endpoint kind {kind} does not admit its planes")
        kind = attributes.get("subject_kind") or attributes.get("resource_kind")
        if kind is None and entry["element_kind"] == "fact" and attributes["subject"]["status"] == "resolved":
            kind = attributes["subject"]["kind"]
        if kind is not None and not planes <= planes_of_kind[kind]:
            raise SeedError(f"{entry['ref']['id']}: subject kind {kind} does not admit its planes")


def build_entries(packs, graph_text, kernel_text):
    model = Model(packs)
    relations = [relation_entry(pack, relation, model) for pack in packs for relation in pack["relations"]]
    relations.append(relays_entry())
    planes_of_kind = kind_planes(model, relations)
    entries = kind_entries(model, planes_of_kind) + relations + dimension_entries(model, planes_of_kind)
    for pack in packs:
        entries.extend(pack_entries(pack, model, planes_of_kind))
    entries.extend(kernel_entries(graph_text, kernel_text))
    entries.sort(key=catalog_key)
    keys = [catalog_key(entry) for entry in entries]
    if len(set(keys)) != len(keys):
        raise SeedError("duplicate catalog entry")
    return entries


def build():
    graph_text = read_text(GRAPH_PAGE)
    kernel_text = read_text(KERNEL_PAGE)
    core_types = core_types_table(graph_text)
    entries = build_entries(load_packs(), graph_text, kernel_text)
    check_closure(entries, core_types)
    catalog = {
        "contract": "helianthus.semantic.element-catalog/v1",
        "kernel_contract": KERNEL_CONTRACT,
        "status": "accepted",
        "catalog_order": CATALOG_ORDER,
        "planes": planes_table(graph_text),
        "core_relation_types": core_types,
        "identification_schemes": [],
        "elements": entries,
        "lenses": [],
    }
    seed_refs = {
        "contract": SEED_REFS_CONTRACT,
        "refs": [entry["ref"] for entry in entries if entry["admission"]["arm"] == "accepted_pack"],
    }
    return {CATALOG_PATH: render(catalog), SEED_REFS_PATH: render(seed_refs)}


def render(document):
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the element catalog seed.")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 when the committed files differ from a fresh generation")
    args = parser.parse_args(argv)
    try:
        outputs = build()
    except (OSError, KeyError, ValueError) as error:
        print(f"element catalog seed: {error}", file=sys.stderr)
        return 2
    if args.check:
        stale = [path for path, text in outputs.items()
                 if not (ROOT / path).is_file() or (ROOT / path).read_text(encoding="utf-8") != text]
        for path in stale:
            print(f"{path} differs from a fresh generation", file=sys.stderr)
        return 1 if stale else 0
    for path, text in outputs.items():
        (ROOT / path).write_text(text, encoding="utf-8")
    print(f"wrote {CATALOG_PATH} and {SEED_REFS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
