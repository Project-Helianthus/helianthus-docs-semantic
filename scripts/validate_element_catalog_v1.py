#!/usr/bin/env python3
"""Validate the element catalog against the accepted packs and the graph contract.

``python3 scripts/validate_element_catalog_v1.py`` loads
``api/v1/element-catalog-v1.json`` with repeated object keys refused, checks it
against ``api/v1/element-catalog-v1.schema.json`` through
``scripts/json_schema_subset_v1.py`` and then enforces the cross-entry rules
CAT-1 to CAT-9 of graph contract section 10.4 in code. Every expected value is
recomputed from the accepted inputs; nothing is taken from the catalog
generator, which this module never imports:

- ``catalog.definitions`` of the thermal, PV, EVSE and infrastructure
  acceptance vectors and the storage contract tables (CAT-1, CAT-2);
- ``api/v1/pack-metadata-v1.json`` (CAT-2);
- sections 7.1, 8.1 and 10.2 of ``api/v1/graph.md`` for the core relation
  types, the planes and the kernel state types (CAT-1, CAT-4);
- ``scripts/element-catalog-seed-refs.json``, the frozen references that may
  carry the ``accepted_pack`` arm or a ``native_convention`` sign reference
  (CAT-6, CAT-7).

| Rule | What is recomputed | Stable error |
|---|---|---|
| CAT-1 | one entry per pack reference and per kernel state type of section 10.2 | ``membership_missing``, ``definition_owner_missing``, ``duplicate_identity`` |
| CAT-2 | dimensions, services, capabilities, operation shapes, value kinds, relation endpoints and cardinality, dimension roles, subject kinds | ``invalid_value`` |
| CAT-3 | section 10.3 per entry | ``membership_missing`` |
| CAT-4 | the planes and core types of sections 7.1 and 8.1, PLN-5, PLN-6, LNS-1, at most one installation root, resolvable references | ``membership_missing``, ``duplicate_identity``, ``invalid_value`` |
| CAT-5 | pack-owned definitions stay inside their pack; owners per element kind; the ``native.`` namespace | ``definition_owner_conflict`` |
| CAT-6 | the admission arm allowed per plane, core type and element; ``accepted_pack`` only for seed references; a page of this repository is a repository-relative path of a file in the tree | ``invalid_value`` |
| CAT-7 | a signed fact names a ``supplies`` relation, or ``native_convention`` for a seed reference | ``invalid_value``, ``membership_missing`` |
| CAT-8 | canonical entry order | ``noncanonical_order`` |
| CAT-9 | unique scheme identifiers, each with a ``public_registry`` admission record | ``duplicate_identity``, ``invalid_value`` |

Each failure prints the stable error, the rule and the entry. The exit status
is 1 on any failure and 0 with a PASS line otherwise.
"""
import re
import sys
from pathlib import Path
from typing import NamedTuple

import json_schema_subset_v1 as subset

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "api/v1/element-catalog-v1.json"
SCHEMA = ROOT / "api/v1/element-catalog-v1.schema.json"
SEED_REFS = ROOT / "scripts/element-catalog-seed-refs.json"
PACK_METADATA = ROOT / "api/v1/pack-metadata-v1.json"
STORAGE_TABLES = ROOT / "api/v1/packs/storage-bms-contract-tables.json"
GRAPH_PAGE = ROOT / "api/v1/graph.md"
VECTOR_FILES = tuple(ROOT / "api/v1/packs" / name for name in (
    "thermal-hvac-acceptance-vectors.json",
    "pv-inverter-acceptance-vectors.json",
    "evse-acceptance-vectors.json",
    "infrastructure-acceptance-vectors.json",
))

VECTOR_GROUPS = (
    ("fields", "fact"), ("fact_dimensions", "dimension"), ("services", "service"),
    ("relations", "relation"), ("capabilities", "capability"), ("operations", "operation"),
    ("effect_rules", "effect_rule"), ("portal_contributions", "presentation"),
)
STORAGE_GROUPS = (
    ("field_specs", "fact"), ("services", "service"), ("relations", "relation"),
    ("capabilities", "capability"), ("operations", "operation"), ("effects", "effect_rule"),
    ("portal_contributions", "presentation"),
)
STORAGE_INDEX_GROUPS = (
    ("fields", "fact"), ("services", "service"), ("capabilities", "capability"),
    ("operations", "operation"), ("effect_rules", "effect_rule"),
)
KERNEL_KINDS = ("evidence_state", "lifecycle_state", "presentation")
DISPOSITIONS = ("member", "unsupported", "unknown")
OVER_TIME = "_over_time"
NATIVE_PREFIX = "native."

# Graph section 7.1: the planes a supplies medium gives.
MEDIUM_PLANES = {
    "electrical": {"energy"},
    "air": {"energy"},
    "heat_transfer_fluid": {"energy", "hydraulic"},
    "refrigerant": {"energy", "hydraulic"},
}
# Graph section 10.2: owner per element kind; an extension entry is native (section 10.6).
OWNER_KINDS = {
    "resource_kind": {"core"},
    "relation": {"pack", "core"},
    "dimension": {"pack"},
    "service": {"pack"},
    "fact": {"pack"},
    "capability": {"pack"},
    "operation": {"pack"},
    "effect_rule": {"pack"},
    "evidence_state": {"core"},
    "lifecycle_state": {"core"},
    "presentation": {"pack", "core"},
}
# Graph section 10.5: the arms an admission record may use.
FULL_RULE_ARMS = frozenset({"matter_baseline", "eebus", "two_vendors"})
STRUCTURE_ARMS = FULL_RULE_ARMS | {"owner_decision"}
PACK_ARMS = FULL_RULE_ARMS | {"accepted_pack"}
CORE_ARMS = {
    "resource_kind": STRUCTURE_ARMS | {"accepted_pack"},
    "relation": STRUCTURE_ARMS,
    "evidence_state": frozenset({"accepted_kernel", "owner_decision"}),
    "lifecycle_state": frozenset({"accepted_kernel", "owner_decision"}),
    "presentation": frozenset({"accepted_kernel"}),
}
SCHEME_ARM = "public_registry"
# Graph section 10.5: a page of this repository is a repository-relative path.
# A relative reference resolves against the revision that carries the catalog.
THIS_REPO_BLOB = "https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/"
RELATIVE_EVIDENCE_PATH = re.compile(
    r"(?:(?!\.\.)[A-Za-z0-9._-]+/)+(?!\.\.)[A-Za-z0-9._-]+\Z"
)
RELATIVE_EVIDENCE_MISSING = "repository-relative evidence is not a path in this tree"
THIS_REPO_BLOB_EVIDENCE = "this repository is cited by a repository-relative path"
# Graph section 10.2: referenced definitions per element kind and the kind they name.
REFERENCE_ATTRIBUTES = {
    "service": (("fact_key_dimension", "dimension"),),
    "capability": (("service", "service"), ("operation", "operation")),
    "operation": (("capability", "capability"), ("argument", "fact"), ("effect_rule", "effect_rule")),
    "effect_rule": (("operation", "operation"), ("fact", "fact")),
}


class Finding(NamedTuple):
    error: str
    rule: str
    entry: str
    detail: str

    def __str__(self):
        return f"{self.error} {self.rule} {self.entry}: {self.detail}"


class Agreement(NamedTuple):
    key: tuple
    element_kind: str
    label: str
    expected: object
    read: object


class Inputs(NamedTuple):
    pack_kinds: dict
    agreements: list
    kernel_types: dict
    seed: frozenset
    planes: tuple
    core_types: dict
    relation_ends: dict = {}


class Index(NamedTuple):
    by_key: dict
    kinds: dict
    planes: frozenset
    core_types: dict


# ------------------------------------------------------------------ references


def pack_key(pack, ident, version):
    return ("pack", pack["id"], pack["version"], ident, version)


def item_key(ref):
    """Key of a pack-side reference: ``{"pack": ..., "id": ..., "version": ...}``."""
    return pack_key(ref["pack"], ref["id"], ref["version"])


def ref_key(ref):
    """Key of a catalog ``elementRef``."""
    owner = ref["owner"]
    if owner["kind"] == "pack":
        return pack_key(owner["pack"], ref["id"], ref["version"])
    scope = owner.get("contract", owner.get("repository", ""))
    return (owner["kind"], scope, "", ref["id"], ref["version"])


def optional_key(ref):
    return ref_key(ref) if isinstance(ref, dict) else None


def show(key):
    if key is None:
        return "nothing"
    owner = f"{key[1]}@{key[2]}" if key[0] == "pack" else key[0]
    return f"{key[3]}@{key[4]} [{owner}]"


def render(value):
    return show(value) if isinstance(value, tuple) else value


def order_key(entry):
    owner = entry["ref"]["owner"]
    pack = owner.get("pack", {"id": "", "version": ""})
    parts = (owner["kind"], pack["id"], pack["version"], entry["ref"]["id"], entry["ref"]["version"])
    return tuple(part.encode("utf-8") for part in parts)


def value_at(name):
    return lambda attributes: attributes.get(name)


def ref_at(name):
    return lambda attributes: optional_key(attributes.get(name))


def endpoint_at(side):
    return lambda attributes: optional_key(attributes.get("endpoint_dimensions", {}).get(side))


def subject_dimension(attributes):
    subject = attributes.get("subject", {})
    return optional_key(subject.get("dimension", subject.get("qualifier_dimension")))


# ---------------------------------------------------------------- pack inputs


class PackModel:
    """Reference set and repeated facts derived from the accepted pack documents."""

    def __init__(self):
        self.kinds = {}
        self.roles = {}
        self.agreements = []
        self.relation_ends = {}

    def expect(self, key, element_kind):
        self.kinds[key] = element_kind

    def agree(self, key, element_kind, label, expected, read):
        self.agreements.append(Agreement(key, element_kind, label, expected, read))

    def resource_dimension(self, key):
        self.expect(key, "dimension")
        self.roles[key] = "resource"

    def field(self, key, value_kind, dimension):
        self.expect(key, "fact")
        self.expect(dimension, "dimension")
        self.roles.setdefault(dimension, "qualifier")
        self.agree(key, "fact", "value_kind", value_kind, value_at("value_kind"))
        self.agree(key, "fact", "subject dimension", dimension, subject_dimension)

    def relation(self, key, ends, cardinality):
        """Record a relation; ``ends`` holds the tuple of endpoint dimensions of each side.

        A catalog entry names its endpoint dimensions only when each side has exactly one;
        a side with several endpoint kinds leaves both endpoint dimensions out.
        """
        self.expect(key, "relation")
        self.relation_ends[key] = ends
        single = all(len(side) == 1 for side in ends)
        for side, dimensions in zip(("from", "to"), ends):
            for dimension in dimensions:
                self.expect(dimension, "dimension")
            self.agree(key, "relation", f"endpoint {side}", dimensions[0] if single else None, endpoint_at(side))
        self.agree(key, "relation", "cardinality", cardinality.removesuffix(OVER_TIME), value_at("cardinality"))
        self.agree(key, "relation", "over_time", cardinality.endswith(OVER_TIME), value_at("over_time"))

    def role_agreements(self):
        for key, role in self.roles.items():
            self.agree(key, "dimension", "role", role, value_at("role"))


def endpoint_ids(path, value):
    """One endpoint dimension identifier, or a non-empty list of distinct ones, as a tuple."""
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list) or not value \
            or not all(isinstance(ident, str) for ident in value) or len(set(value)) != len(value):
        raise ValueError(f"{path.name}: relation endpoint is neither a dimension nor a list of distinct ones")
    return tuple(value)


def load_vector_pack(path, model):
    catalog = subset.load_json(path)["catalog"]
    pack, defs = catalog["pack"], catalog["definitions"]
    unknown = sorted(set(defs) - {group for group, _ in VECTOR_GROUPS})
    if unknown:
        raise ValueError(f"{path.name}: definition groups outside the catalog inputs: {unknown}")
    for group, element_kind in VECTOR_GROUPS:
        for item in defs.get(group, []):
            model.expect(item_key(item["ref"]), element_kind)
    declared = {item["id"]: item["ref"]["version"] for item in defs.get("fact_dimensions", [])}

    def dimension(ident):
        return pack_key(pack, ident, declared.get(ident, pack["version"]))

    for ident in declared:
        model.resource_dimension(dimension(ident))
    for item in defs.get("services", []):
        model.resource_dimension(dimension(item["fact_key_dimension"]))
    for item in defs.get("fields", []):
        model.field(item_key(item["ref"]), item["kind"], dimension(item["dimension"]))
    for item in defs.get("relations", []):
        ends = tuple(tuple(dimension(ident) for ident in endpoint_ids(path, item[side])) for side in ("from", "to"))
        model.relation(item_key(item["ref"]), ends, item["cardinality"])


def load_storage_pack(path, model):
    tables = subset.load_json(path)
    index = tables["definition_index"]
    pack = index["pack"]
    versions = {}
    for group, element_kind in STORAGE_INDEX_GROUPS:
        for item in index[group]:
            versions[item["id"]] = item_key(item)
            model.expect(item_key(item), element_kind)

    def key(ident):
        return versions.get(ident, pack_key(pack, ident, pack["version"]))

    def dimension(ident):
        return pack_key(pack, ident, pack["version"])

    for group, element_kind in STORAGE_GROUPS:
        for item in tables[group]:
            model.expect(key(item["id"]), element_kind)
    service_dimension = {item["id"]: dimension(item["dimension"]) for item in tables["services"]}
    for value in service_dimension.values():
        model.resource_dimension(value)
    for item in tables["field_specs"]:
        model.field(key(item["id"]), item["kind"], dimension(item["dimension"]))
    for item in tables["relations"]:
        ends = ((service_dimension[item["from"]],), (service_dimension[item["to"]],))
        model.relation(key(item["id"]), ends, item["cardinality"])


def metadata_agreements(metadata):
    """Facts that the catalog repeats from pack metadata, as (key, kind, label, expected, reader)."""
    result = []
    for pack in metadata["packs"]:
        for item in pack["fields"]:
            result.append((item["ref"], "fact", "subject dimension", item["dimension"], subject_dimension))
        for item in pack["services"]:
            result.append((item["ref"], "service", "fact_key_dimension", item["fact_key_dimension"],
                           ref_at("fact_key_dimension")))
        for item in pack["capabilities"]:
            result.append((item["ref"], "capability", "service", item["service"], ref_at("service")))
        for item in pack["operations"]:
            result.extend(operation_agreements(item))
    return [Agreement(item_key(ref), kind, "pack metadata " + label, item_key(expected), read)
            for ref, kind, label, expected, read in result]


def operation_agreements(item):
    return [
        (item["ref"], "operation", "capability", item["capability"], ref_at("capability")),
        (item["ref"], "operation", "argument", item["argument"], ref_at("argument")),
        (item["ref"], "operation", "effect_rule", item["effect"], ref_at("effect_rule")),
        (item["capability"], "capability", "operation", item["ref"], ref_at("operation")),
        (item["capability"], "capability", "service", item["service"], ref_at("service")),
        (item["effect"], "effect_rule", "operation", item["ref"], ref_at("operation")),
        (item["effect"], "effect_rule", "fact", item["argument"], ref_at("fact")),
    ]


# -------------------------------------------------------------- graph inputs


def section_text(text, heading):
    marker = "\n" + heading + "\n"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"graph contract has no section {heading!r}")
    body = text[start + len(marker):]
    end = re.search(r"\n#{1,3} ", body)
    return body if end is None else body[:end.start()]


def table_rows(block, header):
    lines = block.splitlines()
    starts = [number for number, line in enumerate(lines) if line.startswith(header)]
    if len(starts) != 1:
        raise ValueError(f"graph contract must hold one table headed {header!r}")
    rows = []
    for line in lines[starts[0] + 2:]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def ticked(cell):
    names = re.findall(r"`([^`]+)`", cell)
    if not names:
        raise ValueError(f"graph contract table cell names no identifier: {cell!r}")
    return names[0]


def plane_cell(cell):
    return () if cell == "none" else tuple(name.strip() for name in cell.split(","))


def graph_planes(text):
    return tuple(ticked(row[0]) for row in table_rows(section_text(text, "### 8.1 The planes"), "| Plane |"))


def graph_core_types(text):
    rows = table_rows(section_text(text, "### 7.1 Core relation types"), "| Type |")
    return {ticked(row[0]): (frozenset(plane_cell(row[3])), frozenset(plane_cell(row[4]))) for row in rows}


def snake_case(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def graph_kernel_types(text):
    """Kernel state types of section 10.2, keyed by their core element identifier."""
    block = section_text(text, "### 10.2 Element kinds")
    pattern = r"^- `(%s)`[^:]*:(.*?)(?=^- `|\n\n)" % "|".join(KERNEL_KINDS)
    result = {}
    for match in re.finditer(pattern, block, re.M | re.S):
        for name in re.findall(r"`([A-Z][A-Za-z]+)`", match.group(2)):
            result["kernel." + snake_case(name)] = (match.group(1), name)
    if {kind for kind, _ in result.values()} != set(KERNEL_KINDS):
        raise ValueError("graph contract section 10.2 does not list every kernel state kind")
    return result


def load_inputs():
    model = PackModel()
    for path in VECTOR_FILES:
        load_vector_pack(path, model)
    load_storage_pack(STORAGE_TABLES, model)
    model.role_agreements()
    graph = GRAPH_PAGE.read_text(encoding="utf-8")
    seed = subset.load_json(SEED_REFS)
    return Inputs(
        pack_kinds=dict(model.kinds),
        agreements=model.agreements + metadata_agreements(subset.load_json(PACK_METADATA)),
        kernel_types=graph_kernel_types(graph),
        seed=frozenset(ref_key(ref) for ref in seed["refs"]),
        planes=graph_planes(graph),
        core_types=graph_core_types(graph),
        relation_ends=dict(model.relation_ends),
    )


# ------------------------------------------------------------------ the index


def build_index(catalog):
    by_key = {}
    for entry in catalog["elements"]:
        by_key.setdefault(ref_key(entry["ref"]), entry)
    kinds = {entry["ref"]["id"]: entry for entry in catalog["elements"]
             if entry["element_kind"] == "resource_kind"}
    core_types = {}
    for core_type in catalog["core_relation_types"]:
        core_types.setdefault(core_type["id"], core_type)
    planes = frozenset(plane["id"] for plane in catalog["planes"])
    return Index(by_key, kinds, planes, core_types)


def entry_name(entry):
    return show(ref_key(entry["ref"]))


def kind_planes(index, kind):
    entry = index.kinds.get(kind)
    return set() if entry is None else set(entry["planes"])


def entry_refs(entry):
    """(label, reference, element kind it must name) of an entry's attributes, sign reference excluded."""
    attributes = entry["attributes"]
    element_kind = entry["element_kind"]
    for name, target in REFERENCE_ATTRIBUTES.get(element_kind, ()):
        if isinstance(attributes.get(name), dict):
            yield name, attributes[name], target
    if element_kind == "fact":
        subject = attributes["subject"]
        for name in ("dimension", "qualifier_dimension"):
            if name in subject:
                yield "subject " + name, subject[name], "dimension"
    for side, ref in attributes.get("endpoint_dimensions", {}).items():
        yield "endpoint " + side, ref, "dimension"


def entry_kinds(entry):
    """Resource kind identifiers that an entry's attributes name."""
    attributes = entry["attributes"]
    kinds = list(attributes.get("from_kinds", [])) + list(attributes.get("to_kinds", []))
    for name in ("resource_kind", "subject_kind"):
        if name in attributes:
            kinds.append(attributes[name])
    subject = attributes.get("subject", {})
    if "kind" in subject:
        kinds.append(subject["kind"])
    return kinds


def subject_kind(entry, index):
    attributes = entry["attributes"]
    if entry["element_kind"] == "fact":
        return attributes["subject"].get("kind")
    if entry["element_kind"] == "service":
        return attributes.get("subject_kind")
    if entry["element_kind"] == "capability":
        service = index.by_key.get(optional_key(attributes.get("service")))
        return None if service is None else service["attributes"].get("subject_kind")
    return None


def dimension_kind(index, ref):
    entry = index.by_key.get(optional_key(ref))
    return None if entry is None else entry["attributes"].get("resource_kind")


# ---------------------------------------------------------------- CAT-1


def duplicate_entries(catalog):
    seen = set()
    for entry in catalog["elements"]:
        key = ref_key(entry["ref"])
        if key in seen:
            yield Finding("duplicate_identity", "CAT-1", show(key), "more than one entry")
        seen.add(key)


def missing_pack_refs(index, inputs):
    for key, element_kind in sorted(inputs.pack_kinds.items()):
        entry = index.by_key.get(key)
        if entry is None:
            yield Finding("membership_missing", "CAT-1", show(key), f"pack {element_kind} has no catalog entry")
        elif entry["element_kind"] != element_kind:
            yield Finding("invalid_value", "CAT-1", show(key),
                          f"element kind {entry['element_kind']}, the pack declares a {element_kind}")


def extra_pack_refs(index, inputs):
    for key in index.by_key:
        if key[0] == "pack" and key not in inputs.pack_kinds:
            yield Finding("definition_owner_missing", "CAT-1", show(key), "no accepted pack declares it")


def kernel_type_findings(index, inputs):
    core = {key[3]: entry for key, entry in index.by_key.items() if key[0] == "core"}
    for ident, (element_kind, name) in sorted(inputs.kernel_types.items()):
        entry = core.get(ident)
        if entry is None:
            yield Finding("membership_missing", "CAT-1", ident, f"kernel {element_kind} {name} has no entry")
        elif entry["element_kind"] != element_kind or entry["attributes"].get("kernel_type", name) != name:
            yield Finding("invalid_value", "CAT-1", ident, f"entry does not list kernel {element_kind} {name}")
    for ident, entry in sorted(core.items()):
        if entry["element_kind"] in KERNEL_KINDS and ident not in inputs.kernel_types:
            yield Finding("definition_owner_missing", "CAT-1", ident, "graph section 10.2 lists no such kernel type")


def check_completeness(catalog, index, inputs):
    return [*duplicate_entries(catalog), *missing_pack_refs(index, inputs), *extra_pack_refs(index, inputs),
            *kernel_type_findings(index, inputs)]


# ---------------------------------------------------------------- CAT-2


def agreement_findings(index, inputs):
    for agreement in inputs.agreements:
        entry = index.by_key.get(agreement.key)
        if entry is None or entry["element_kind"] != agreement.element_kind:
            continue
        actual = agreement.read(entry["attributes"])
        if actual != agreement.expected:
            yield Finding("invalid_value", "CAT-2", show(agreement.key),
                          f"{agreement.label} is {render(actual)}, the accepted packs say {render(agreement.expected)}")


def subject_kind_findings(catalog, index):
    for entry in catalog["elements"]:
        attributes = entry["attributes"]
        if entry["element_kind"] == "service":
            pairs = [(attributes["subject_kind"], attributes["fact_key_dimension"])]
        elif entry["element_kind"] == "fact" and attributes["subject"].get("status") == "resolved":
            pairs = [(attributes["subject"]["kind"], attributes["subject"]["dimension"])]
        elif entry["element_kind"] == "relation" and "endpoint_dimensions" in attributes:
            ends = attributes["endpoint_dimensions"]
            pairs = [(kind, ends["from"]) for kind in attributes["from_kinds"]]
            pairs += [(kind, ends["to"]) for kind in attributes["to_kinds"]]
        else:
            continue
        for kind, dimension in pairs:
            if kind != dimension_kind(index, dimension):
                yield Finding("invalid_value", "CAT-2", entry_name(entry),
                              f"kind {kind} is not the resource kind of dimension {show(optional_key(dimension))}")


def relation_kind_findings(index, inputs):
    """Each side's endpoint kinds equal the resource kinds of the dimensions its pack names there."""
    for key, ends in inputs.relation_ends.items():
        entry = index.by_key.get(key)
        if entry is None or entry["element_kind"] != "relation":
            continue
        for side, dimensions in zip(("from", "to"), ends):
            expected = sorted(str((index.by_key.get(dimension) or {"attributes": {}})["attributes"]
                                  .get("resource_kind")) for dimension in dimensions)
            actual = list(entry["attributes"].get(f"{side}_kinds", []))
            if sorted(actual) != expected or len(set(actual)) != len(actual):
                yield Finding("invalid_value", "CAT-2", show(key),
                              f"{side}_kinds is {actual}, the kinds of the accepted pack endpoints are {expected}")


def check_agreement(catalog, index, inputs):
    return [*agreement_findings(index, inputs), *relation_kind_findings(index, inputs),
            *subject_kind_findings(catalog, index)]


# ---------------------------------------------------------------- CAT-3


def disposition_problems(entry):
    disposition, planes = entry["disposition"], entry["planes"]
    if disposition not in DISPOSITIONS:
        return [f"disposition {disposition} is not a catalog disposition"]
    if disposition == "member":
        return [] if planes else ["member with no plane"]
    problems = [f"{disposition} entry is in planes {planes}"] if planes else []
    if not entry.get("reason"):
        problems.append(f"{disposition} entry has no reason")
    if disposition == "unknown" and not entry.get("tracking"):
        problems.append("unknown entry has no tracking issue")
    if disposition == "unsupported" and "tracking" in entry:
        problems.append("unsupported entry carries a tracking issue; its reason is final")
    return problems


def check_dispositions(catalog, index, inputs):
    return [Finding("membership_missing", "CAT-3", entry_name(entry), problem)
            for entry in catalog["elements"] for problem in disposition_problems(entry)]


# ---------------------------------------------------------------- CAT-4


def duplicate_ids(items, what):
    seen = set()
    for item in items:
        if item["id"] in seen:
            yield Finding("duplicate_identity", "CAT-4", f"{what} {item['id']}", "identifier is not unique")
        seen.add(item["id"])


def structure_findings(catalog, index, inputs):
    yield from duplicate_ids(catalog["planes"], "plane")
    yield from duplicate_ids(catalog["core_relation_types"], "core type")
    yield from duplicate_ids(catalog["lenses"], "lens")
    for plane in inputs.planes:
        if plane not in index.planes:
            yield Finding("membership_missing", "CAT-4", f"plane {plane}", "graph section 8.1 plane is not listed")
    for plane in sorted(index.planes - set(inputs.planes)):
        yield Finding("invalid_value", "CAT-4", f"plane {plane}", "graph section 8.1 defines no such plane")
    for type_id, (allowed, required) in sorted(inputs.core_types.items()):
        core_type = index.core_types.get(type_id)
        if core_type is None:
            yield Finding("membership_missing", "CAT-4", f"core type {type_id}", "graph section 7.1 type is not listed")
        elif (set(core_type["allowed_planes"]), set(core_type["required_planes"])) != (allowed, required):
            yield Finding("invalid_value", "CAT-4", f"core type {type_id}", "planes differ from graph section 7.1")
    for type_id in sorted(set(index.core_types) - set(inputs.core_types)):
        yield Finding("invalid_value", "CAT-4", f"core type {type_id}", "graph section 7.1 defines no such type")


def unknown_planes(index, owner, planes):
    for plane in planes:
        if plane not in index.planes:
            yield Finding("membership_missing", "CAT-4", owner, f"plane {plane} is not in the catalog")


def plane_name_findings(catalog, index):
    for entry in catalog["elements"]:
        yield from unknown_planes(index, entry_name(entry), entry["planes"])
    for core_type in catalog["core_relation_types"]:
        yield from unknown_planes(index, f"core type {core_type['id']}",
                                  core_type["allowed_planes"] + core_type["required_planes"])
    for lens in catalog["lenses"]:
        yield from unknown_planes(index, f"lens {lens['id']}", lens["planes"])


def reference_findings(catalog, index):
    for entry in catalog["elements"]:
        for label, ref, target in entry_refs(entry):
            named = index.by_key.get(ref_key(ref))
            if named is None or named["element_kind"] != target:
                yield Finding("membership_missing", "CAT-4", entry_name(entry),
                              f"{label} {show(ref_key(ref))} is not a {target} entry")
        for kind in entry_kinds(entry):
            if kind not in index.kinds:
                yield Finding("membership_missing", "CAT-4", entry_name(entry), f"kind {kind} is not a resource kind")


def closure_targets(entry, index):
    """(planes the entry needs, planes that bound it, what bounds it, exact) under PLN-5."""
    attributes = entry["attributes"]
    element_kind = entry["element_kind"]
    if element_kind == "relation":
        return [(kind, kind_planes(index, kind), False)
                for kind in attributes["from_kinds"] + attributes["to_kinds"]]
    if element_kind == "effect_rule":
        operation = index.by_key.get(optional_key(attributes.get("operation")))
        return [] if operation is None else [("its operation", set(operation["planes"]), True)]
    if element_kind == "dimension" and attributes.get("role") == "resource":
        kind = attributes.get("resource_kind")
        return [(f"its kind {kind}", kind_planes(index, kind), True)]
    kind = subject_kind(entry, index)
    return [] if kind is None else [(f"subject kind {kind}", kind_planes(index, kind), False)]


def pln5_findings(catalog, index):
    for entry in catalog["elements"]:
        planes = set(entry["planes"])
        for what, bound, exact in closure_targets(entry, index):
            if (planes != bound) if exact else not planes <= bound:
                relation = "differ from" if exact else "are not admitted by"
                yield Finding("membership_missing", "CAT-4", entry_name(entry),
                              f"planes {sorted(planes)} {relation} {what} {sorted(bound)} (PLN-5)")


def pln6_problems(entry, index):
    attributes = entry["attributes"]
    planes = set(entry["planes"])
    core_type = index.core_types.get(attributes["core_type"])
    if core_type is None:
        return [f"core type {attributes['core_type']} is not in the catalog"]
    problems = []
    if not planes <= set(core_type["allowed_planes"]):
        problems.append(f"planes {sorted(planes)} exceed the allowed planes of {core_type['id']}")
    if not set(core_type["required_planes"]) <= planes:
        problems.append(f"planes {sorted(planes)} miss the required planes of {core_type['id']}")
    medium = attributes.get("medium")
    if medium is not None and not planes <= MEDIUM_PLANES.get(medium, set()):
        problems.append(f"planes {sorted(planes)} are not given by medium {medium}")
    return problems


def pln6_findings(catalog, index):
    for entry in catalog["elements"]:
        if entry["element_kind"] == "relation" and entry["disposition"] == "member":
            for problem in pln6_problems(entry, index):
                yield Finding("membership_missing", "CAT-4", entry_name(entry), problem + " (PLN-6)")


def lens_problems(lens, index):
    planes = set(lens["planes"])
    problems = []
    for kind in lens["root_kinds"]:
        entry = index.kinds.get(kind)
        if entry is None or entry["disposition"] != "member" or not planes & set(entry["planes"]):
            problems.append(f"root kind {kind} is not a member kind admitting a lens plane")
    for ref in lens.get("relations", []):
        entry = index.by_key.get(ref_key(ref))
        if entry is None or entry["element_kind"] != "relation" or entry["disposition"] != "member":
            problems.append(f"relation {show(ref_key(ref))} is not a member relation entry")
        elif not planes & set(entry["planes"]):
            problems.append(f"relation {show(ref_key(ref))} is a member of no lens plane")
    return problems


def lns1_findings(catalog, index):
    for lens in catalog["lenses"]:
        for problem in lens_problems(lens, index):
            yield Finding("membership_missing", "CAT-4", f"lens {lens['id']}", problem + " (LNS-1)")


def installation_root_findings(catalog):
    """At most one resource kind carries installation_root true."""
    roots = [entry for entry in catalog["elements"]
             if entry["element_kind"] == "resource_kind" and entry["attributes"].get("installation_root") is True]
    if len(roots) < 2:
        return
    claimed = ", ".join(sorted(entry["ref"]["id"] for entry in roots))
    for entry in roots:
        yield Finding("duplicate_identity", "CAT-4", entry_name(entry),
                      f"installation root is claimed by {claimed}")


def check_closure(catalog, index, inputs):
    return [*structure_findings(catalog, index, inputs), *plane_name_findings(catalog, index),
            *reference_findings(catalog, index), *pln5_findings(catalog, index), *pln6_findings(catalog, index),
            *lns1_findings(catalog, index), *installation_root_findings(catalog)]


# ---------------------------------------------------------------- CAT-5


def pack_kinds(catalog):
    """Resource kinds reached through the resource dimensions of each pack."""
    result = {}
    for entry in catalog["elements"]:
        attributes = entry["attributes"]
        if entry["element_kind"] == "dimension" and attributes.get("role") == "resource":
            owner = entry["ref"]["owner"]
            if owner["kind"] == "pack":
                result.setdefault(ref_key(entry["ref"])[1:3], set()).add(attributes.get("resource_kind"))
    return result


def owner_problems(entry):
    owner_kind = entry["ref"]["owner"]["kind"]
    native_id = entry["ref"]["id"].startswith(NATIVE_PREFIX)
    problems = []
    if owner_kind != "native" and owner_kind not in OWNER_KINDS[entry["element_kind"]]:
        problems.append(f"a {entry['element_kind']} is never {owner_kind}-owned")
    if native_id != (owner_kind == "native"):
        problems.append(f"only a native-owned entry uses the {NATIVE_PREFIX} namespace")
    if owner_kind == "native" and entry["disposition"] != "unknown":
        problems.append("an extension entry is always unknown")
    return problems


def pack_scope_problems(entry, kinds_by_pack):
    pack = ref_key(entry["ref"])[1:3]
    problems = [f"{label} {show(ref_key(ref))} belongs to another owner"
                for label, ref, _ in entry_refs(entry) if ref_key(ref)[:3] != ("pack", *pack)]
    if entry["element_kind"] == "relation":
        attributes = entry["attributes"]
        outside = sorted(set(attributes["from_kinds"] + attributes["to_kinds"]) - kinds_by_pack.get(pack, set()))
        problems.extend(f"endpoint kind {kind} is not reached through a dimension of its pack" for kind in outside)
    return problems


def check_ownership(catalog, index, inputs):
    kinds_by_pack = pack_kinds(catalog)
    findings = []
    for entry in catalog["elements"]:
        problems = owner_problems(entry)
        if entry["ref"]["owner"]["kind"] == "pack":
            problems += pack_scope_problems(entry, kinds_by_pack)
        findings.extend(Finding("definition_owner_conflict", "CAT-5", entry_name(entry), problem)
                        for problem in problems)
    return findings


# ---------------------------------------------------------------- CAT-6


def allowed_arms(entry):
    owner_kind = entry["ref"]["owner"]["kind"]
    if owner_kind == "pack":
        return PACK_ARMS
    if owner_kind == "native":
        return STRUCTURE_ARMS
    return CORE_ARMS.get(entry["element_kind"], frozenset())


def repository_evidence_problem(link):
    """A page of this repository must be a file path in the tree that carries the catalog."""
    if link.startswith(THIS_REPO_BLOB):
        return THIS_REPO_BLOB_EVIDENCE
    if link.startswith(("https://", "http://")):
        return None
    path = link.split("#", 1)[0]
    if RELATIVE_EVIDENCE_PATH.fullmatch(path) is None:
        return RELATIVE_EVIDENCE_MISSING
    target = (ROOT / path).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return RELATIVE_EVIDENCE_MISSING
    if not target.is_file():
        return RELATIVE_EVIDENCE_MISSING
    return None


def repository_evidence_findings(catalog):
    records = [(f"plane {item['id']}", item["admission"]) for item in catalog["planes"]]
    records += [(f"core type {item['id']}", item["admission"]) for item in catalog["core_relation_types"]]
    records += [(f"scheme {item['id']}", item["admission"]) for item in catalog["identification_schemes"]]
    records += [(entry_name(entry), entry["admission"]) for entry in catalog["elements"]]
    findings = []
    for name, admission in records:
        for link in admission["evidence"]:
            problem = repository_evidence_problem(link)
            if problem is not None:
                findings.append(Finding("invalid_value", "CAT-6", name, problem))
    return findings


def check_admission(catalog, index, inputs):
    findings = []
    structures = [("plane", item) for item in catalog["planes"]]
    structures += [("core type", item) for item in catalog["core_relation_types"]]
    for what, item in structures:
        if item["admission"]["arm"] not in STRUCTURE_ARMS:
            findings.append(Finding("invalid_value", "CAT-6", f"{what} {item['id']}",
                                    f"arm {item['admission']['arm']} is not allowed"))
    for entry in catalog["elements"]:
        arm = entry["admission"]["arm"]
        if arm not in allowed_arms(entry):
            findings.append(Finding("invalid_value", "CAT-6", entry_name(entry),
                                    f"arm {arm} is not allowed for this {entry['element_kind']}"))
        elif arm == "accepted_pack" and ref_key(entry["ref"]) not in inputs.seed:
            findings.append(Finding("invalid_value", "CAT-6", entry_name(entry),
                                    "arm accepted_pack outside the frozen seed references"))
    findings.extend(repository_evidence_findings(catalog))
    return findings


# ---------------------------------------------------------------- CAT-7


def sign_problem(entry, index, inputs):
    attributes = entry["attributes"]
    reference = attributes.get("sign_reference")
    if attributes.get("direction") != "signed":
        return None if reference is None else ("invalid_value", "sign reference on a fact that is not signed")
    if reference == "native_convention":
        if ref_key(entry["ref"]) in inputs.seed:
            return None
        return "invalid_value", "native_convention is allowed only for a seed entry"
    if not isinstance(reference, dict):
        return "invalid_value", "signed fact names no sign reference"
    named = index.by_key.get(ref_key(reference))
    if named is None:
        return "membership_missing", f"sign reference {show(ref_key(reference))} has no entry"
    if named["element_kind"] != "relation" or named["attributes"].get("core_type") != "supplies":
        return "invalid_value", f"sign reference {show(ref_key(reference))} is not a supplies relation definition"
    return None


def check_sign_reference(catalog, index, inputs):
    findings = []
    for entry in catalog["elements"]:
        if entry["element_kind"] != "fact":
            continue
        problem = sign_problem(entry, index, inputs)
        if problem is not None:
            findings.append(Finding(problem[0], "CAT-7", entry_name(entry), problem[1]))
    return findings


# ---------------------------------------------------------------- CAT-8 and CAT-9


def check_order(catalog, index, inputs):
    entries = catalog["elements"]
    return [Finding("noncanonical_order", "CAT-8", entry_name(later), f"sorts before {entry_name(earlier)}")
            for earlier, later in zip(entries, entries[1:]) if order_key(later) < order_key(earlier)]


def check_schemes(catalog, index, inputs):
    findings = []
    seen = set()
    for scheme in catalog["identification_schemes"]:
        name = f"scheme {scheme['id']}"
        if scheme["id"] in seen:
            findings.append(Finding("duplicate_identity", "CAT-9", name, "identifier is not unique"))
        seen.add(scheme["id"])
        admission = scheme.get("admission") or {}
        if admission.get("arm") != SCHEME_ARM or not admission.get("evidence"):
            findings.append(Finding("invalid_value", "CAT-9", name, f"needs a {SCHEME_ARM} admission record"))
    return findings


RULES = (
    check_completeness, check_agreement, check_dispositions, check_closure, check_ownership,
    check_admission, check_sign_reference, check_order, check_schemes,
)


def check_rules(catalog, inputs):
    """Findings of CAT-1 to CAT-9 for a schema-valid catalog."""
    index = build_index(catalog)
    findings = []
    for rule in RULES:
        findings.extend(rule(catalog, index, inputs))
    return findings


def validate(catalog, inputs, schema=None):
    """Schema findings, or the cross-entry findings when the schema holds."""
    problems = subset.errors(catalog, subset.load_json(SCHEMA) if schema is None else schema)
    if problems:
        return [Finding("invalid_value", "schema", "catalog", problem) for problem in problems]
    return check_rules(catalog, inputs)


def main():
    try:
        inputs = load_inputs()
        catalog = subset.load_json(CATALOG)
        findings = validate(catalog, inputs)
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(f"FAIL: element catalog inputs: {error!r}", file=sys.stderr)
        return 1
    for finding in findings:
        print(finding, file=sys.stderr)
    if findings:
        print(f"FAIL: {len(findings)} element catalog finding(s)", file=sys.stderr)
        return 1
    print(f"PASS: element catalog CAT-1..CAT-9: {len(catalog['elements'])} entries, "
          f"{len(inputs.pack_kinds)} pack references, {len(inputs.kernel_types)} kernel types, "
          f"{len(catalog['planes'])} planes, {len(catalog['core_relation_types'])} core types, "
          f"{len(catalog['identification_schemes'])} schemes, {len(catalog['lenses'])} lenses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
