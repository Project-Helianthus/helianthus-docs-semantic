#!/usr/bin/env python3
"""Validate the graph acceptance vectors against the graph contract and the element catalog.

The document is ``api/v1/graph-acceptance-vectors.json``
(``helianthus.semantic.graph.acceptance/v1``). Each rule returns a list of
problems; an empty list from every rule means the document is valid. The
rules check the shape and repeated keys, the identifiers, the coverage areas
and operations against section 19 joined with the part 2 amendment, the stable
errors, the definition references (against the catalog as each prior state
registers it, with its stated catalog mutations), the anchor keys, every
section 19 statement, the section 36 statements and the PUB-3 statements, the
graph cuts and the recorded catalog digest. For a graph cut the rules
recompute every snapshot and cut identifier, check the canonical order of
members, findings and relation coherence, and recompute the plane membership
of every resource a member holds. For a read the rules recompute the served
cut identifier and the canonical order of the result, and require every lens
a vector names to be in the catalog. A list_resources plane filter uses PLN-3
membership. A lens resource carries the lens planes it is in. A scope aggregate
is the aggregate of the requested fact. A frontier above 4096 entries is
bounds_exceeded.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

import json_schema_subset_v1 as subset
from check_snapshot_vector_ids import canonical, digest_without

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "api/v1/graph-acceptance-vectors.json"
GRAPH = ROOT / "api/v1/graph.md"
ACCEPTANCE = ROOT / "api/v1/acceptance.md"
CATALOG_PATH = "api/v1/element-catalog-v1.json"
CATALOG = ROOT / CATALOG_PATH
KERNEL_CONTRACT = "helianthus.semantic.kernel/v1"
CUT_CONTRACT = "helianthus.semantic.graph-cut/v1"
LENS_RESULT_CONTRACT = "helianthus.semantic.lens-result/v1"
MAX_CUT_MEMBERS = 256
FINDING_KINDS = ("anchor_parent_unresolved", "contradicted_absence", "duplicate_identity", "same_unit", "ungraphed")
COHERENCE_STATES = ("coherent", "stale", "dangling", "outside_cut", "excluded", "conflict")

VECTOR_ID = re.compile("^G-(POS|NEG)-[A-Z]+-[0-9]+$")
ERROR_HEADING = re.compile("^### Error: `([a-z][a-z0-9_]*)`$", re.MULTILINE)
SECTION_19 = re.compile(r"^## 19\. Conformance$(.*?)^## 20\.", re.MULTILINE | re.DOTALL)
STATEMENT_ROW = re.compile(
    r"^\| ([^|]+?) \| (G-(?:POS|NEG)-[A-Z]+-[0-9]+) \| ([^|]+?) \| ([^|]+?) \|$", re.MULTILINE
)
IDENTIFIER = re.compile(r"G-(?:POS|NEG)-[A-Z]+-[0-9]+")
LEADING_OPERATION = re.compile(r"^`([a-z_]+)`")
REJECTED_ERROR = re.compile(r"^reject `([a-z_]+)`")
COVERAGE_SENTENCE = re.compile(r"Coverage identifiers of the graph acceptance document:(.*?)\.\s+Each", re.DOTALL)
OPERATIONS_SENTENCE = re.compile(r"Operations\s+are(.*?)\.\s", re.DOTALL)
PART2_JOIN = re.compile(r"Coverage identifiers (.+?) join the list; operations (.+?) join the list")
SECTION_36_HEADING = re.compile(r"^## 36\. ", re.MULTILINE)
SECTION_36_ROW = re.compile(
    r"^\| (G-(?:POS|NEG)-[A-Z]+-[0-9]+) \| ([^|]+?) \| ([^|]+?) \|$", re.MULTILINE
)
CODE = re.compile(r"`([a-z_]+)`")
DIGEST_TEXT = re.compile(r"^sha256:[0-9a-f]{64}$")
READ_OPERATIONS = frozenset({"list_resources", "traverse", "retrieve_lens", "sum_members", "project"})
PAGE_BOUND = 4096
FRONTIER_BOUND = 4096
DEPTH_BOUND = 32
POLARITY = {"POS": "positive", "NEG": "negative"}

DIGEST = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
TEXT = {"type": "string", "minLength": 1}
TEXT_LIST = {"type": "array", "items": TEXT, "uniqueItems": True}
PACK_REF = {
    "type": "object", "required": ["id", "version"], "additionalProperties": False,
    "properties": {"id": TEXT, "version": TEXT},
}
# A registry may register the element catalog with stated mutations, so that a vector can hold an
# element of disposition unknown when the committed catalog has none. Each mutation sets one member
# entry to unknown with a reason and a tracking issue; the entry then has no plane (PLN-7).
SET_DISPOSITION = {
    "type": "object", "required": ["ref", "disposition", "reason", "tracking"], "additionalProperties": False,
    "properties": {
        "ref": {"type": "object"},
        "disposition": {"const": "unknown"},
        "reason": {"type": "string", "pattern": "^catalog\\.reason\\.[a-z0-9]+(?:_[a-z0-9]+)*$"},
        "tracking": {"type": "string",
                     "pattern": "^https://github\\.com/Project-Helianthus/[a-z0-9.-]+/issues/[1-9][0-9]*$"},
    },
}
CATALOG_MUTATION = {
    "type": "object", "required": ["set_disposition"], "additionalProperties": False,
    "properties": {"set_disposition": SET_DISPOSITION},
}
REGISTRY = {
    "type": "object", "required": ["element_catalog", "packs"], "additionalProperties": False,
    "properties": {
        "element_catalog": {"enum": ["registered", "absent"]},
        "catalog_mutations": {"type": "array", "items": CATALOG_MUTATION, "minItems": 1},
        "packs": {"type": "array", "items": PACK_REF},
        "identification_schemes": TEXT_LIST,
    },
}
PRIOR_STATE = {
    "type": "object", "required": ["name", "registry", "batches"], "additionalProperties": False,
    "properties": {
        "name": TEXT,
        "registry": {"anyOf": [{"type": "null"}, REGISTRY]},
        "batches": {"type": "array", "items": {"type": "object"}},
        "admission_context": {"type": "object"},
    },
}
MEMBER = {
    "type": "object", "required": ["asset_id", "snapshot_id"], "additionalProperties": False,
    "properties": {"asset_id": TEXT, "snapshot_id": DIGEST},
}
FINDING = {
    "type": "object", "required": ["kind", "subject"], "additionalProperties": False,
    "properties": {"kind": TEXT, "subject": {"type": "object"}},
}
COHERENCE = {
    "type": "object", "required": ["asset_id", "definition", "from", "to", "state", "coherence"],
    "additionalProperties": False,
    "properties": {
        "asset_id": TEXT, "definition": {"type": "object"}, "from": TEXT, "to": TEXT,
        "state": {"enum": ["candidate", "qualified", "rejected", "conflict"]},
        "coherence": {"enum": list(COHERENCE_STATES)},
    },
}
PLANE_MEMBERSHIP = {
    "type": "object", "required": ["resource_id", "planes"], "additionalProperties": False,
    "properties": {"resource_id": TEXT, "planes": TEXT_LIST},
}
CUT = {
    "type": "object",
    "required": ["cut_id", "completeness", "members", "excluded_members", "findings", "relation_coherence",
                 "plane_membership"],
    "additionalProperties": False,
    "properties": {
        "cut_id": DIGEST,
        "completeness": {"enum": ["complete", "partial"]},
        "members": {"type": "array", "items": MEMBER, "minItems": 1},
        "excluded_members": TEXT_LIST,
        "findings": {"type": "array", "items": FINDING},
        "relation_coherence": {"type": "array", "items": COHERENCE},
        "plane_membership": {"type": "array", "items": PLANE_MEMBERSHIP},
    },
}
CUT_INPUT = {
    "type": "object", "required": ["completeness", "snapshots"], "additionalProperties": False,
    "properties": {
        "completeness": {"enum": ["complete", "partial"]},
        "snapshots": {"type": "array", "items": {"type": "object"}, "minItems": 1},
    },
}
SUBJECT_TEXT = {"type": "string", "minLength": 1}
SUBJECT_KEY = {
    "type": "object", "additionalProperties": False,
    "required": ["asset_id", "definition"],
    "properties": {
        "asset_id": SUBJECT_TEXT, "definition": {"type": "object"}, "resource": SUBJECT_TEXT,
        "side": {"enum": ["from", "to"]}, "from": SUBJECT_TEXT, "to": SUBJECT_TEXT,
    },
}
SUBJECTS = {
    "anchor_parent_unresolved": {
        "type": "object", "required": ["resource_id"], "additionalProperties": False,
        "properties": {"resource_id": SUBJECT_TEXT},
    },
    "contradicted_absence": {
        "type": "object", "required": ["absence", "relation"], "additionalProperties": False,
        "properties": {
            "absence": dict(SUBJECT_KEY, required=["asset_id", "definition", "resource", "side"]),
            "relation": dict(SUBJECT_KEY, required=["asset_id", "definition", "from", "to"]),
        },
    },
    "duplicate_identity": {
        "type": "object", "required": ["resource_id", "asset_ids"], "additionalProperties": False,
        "properties": {"resource_id": SUBJECT_TEXT,
                       "asset_ids": {"type": "array", "items": SUBJECT_TEXT, "minItems": 2, "uniqueItems": True}},
    },
    "same_unit": {
        "type": "object", "required": ["resource_ids"], "additionalProperties": False,
        "properties": {"resource_ids": {"type": "array", "items": SUBJECT_TEXT, "minItems": 2, "uniqueItems": True}},
    },
    "ungraphed": {
        "type": "object", "required": ["asset_id"], "additionalProperties": False,
        "properties": {"asset_id": SUBJECT_TEXT},
    },
}
REJECT = {
    "type": "object", "required": ["result", "error_id", "state_unchanged"], "additionalProperties": False,
    "properties": {"result": {"const": "reject"}, "error_id": TEXT, "state_unchanged": {"const": True}},
}
ACCEPT = {
    "type": "object", "required": ["result", "assertions"], "additionalProperties": False,
    "properties": {
        "result": {"const": "accept"},
        "assertions": dict(TEXT_LIST, minItems=1),
        "relation_states": {"type": "array", "items": {"type": "object"}},
        "cut": CUT,
        "resources": {"type": "array", "items": {"type": "object"}},
        "inadmissible_operations": {"type": "array", "items": {"type": "object"}},
        "multiple_membership": {"type": "array", "items": {"type": "object"}},
        "read": {"type": "object"},
    },
}
DEFINITION = {
    "type": "object", "required": ["ref", "disposition"], "additionalProperties": False,
    "properties": {
        "ref": {"type": "object"},
        "disposition": {"enum": ["member", "unknown", "unsupported"]},
        "planes": dict(TEXT_LIST, minItems=2),
    },
}
ANCHOR_KEY = {
    "type": "object", "required": ["identity", "key"], "additionalProperties": False,
    "properties": {
        "identity": {
            "type": "object", "required": ["scheme", "issuer", "token"], "additionalProperties": False,
            "properties": {"scheme": TEXT, "issuer": {"type": "string"}, "token": TEXT},
        },
        "key": DIGEST,
    },
}
VECTOR = {
    "type": "object",
    "required": ["id", "polarity", "record_type", "operation", "coverage", "prior_state", "input",
                 "expect", "definitions", "criterion"],
    "additionalProperties": False,
    "properties": {
        "id": TEXT,
        "polarity": {"enum": ["positive", "negative"]},
        "record_type": {"enum": ["Registry", "ElementCatalog", "PublicationBatch", "GraphCut", "Intent", "Read"]},
        "operation": {"enum": ["construct_registry", "register_catalog", "apply", "assemble_cut", "admit",
                               "list_resources", "traverse", "retrieve_lens", "sum_members", "project"]},
        "coverage": dict(TEXT_LIST, minItems=1),
        "prior_state": TEXT,
        "input": {"type": "object"},
        "expect": {"anyOf": [ACCEPT, REJECT]},
        "definitions": {"type": "array", "items": DEFINITION},
        "anchor_keys": {"type": "array", "items": ANCHOR_KEY, "minItems": 1},
        "uncovered_packs": {"type": "array", "items": PACK_REF, "minItems": 1},
        "criterion": TEXT,
    },
}
SCHEMA = {
    "type": "object",
    "required": ["contract", "kernel_contract", "element_catalog", "synthetic_identification_schemes",
                 "error_ids", "coverage_ids", "operations", "prior_states", "vectors"],
    "additionalProperties": False,
    "properties": {
        "contract": {"const": "helianthus.semantic.graph.acceptance/v1"},
        "kernel_contract": {"const": KERNEL_CONTRACT},
        "element_catalog": {
            "type": "object", "required": ["path", "contract", "sha256"], "additionalProperties": False,
            "properties": {"path": TEXT, "contract": TEXT, "sha256": DIGEST},
        },
        "synthetic_identification_schemes": TEXT_LIST,
        "error_ids": dict(TEXT_LIST, minItems=1),
        "coverage_ids": dict(TEXT_LIST, minItems=1, items={"enum": [
            "activation", "resource", "relation", "plane_membership", "element_catalog", "graph_cut",
            "authority", "retrieval", "lens_result", "sum", "target_report"]}),
        "operations": dict(TEXT_LIST, minItems=1, items={"enum": [
            "construct_registry", "register_catalog", "apply", "assemble_cut", "admit",
            "list_resources", "traverse", "retrieve_lens", "sum_members", "project"]}),
        "prior_states": {"type": "array", "items": PRIOR_STATE, "minItems": 1},
        "vectors": {"type": "array", "items": VECTOR, "minItems": 1},
    },
}


class Context(NamedTuple):
    catalog: dict[str, Any]
    catalog_bytes: bytes
    graph_text: str
    acceptance_text: str


def parse_document(text: str) -> dict[str, Any]:
    """Parse JSON text, refusing repeated object keys and non-JSON constants."""
    return json.loads(text, object_pairs_hook=subset._unique_object, parse_constant=subset._refuse_constant)


def load_document(path: Path) -> dict[str, Any]:
    return parse_document(path.read_text(encoding="utf-8"))


def load_context() -> Context:
    catalog_bytes = CATALOG.read_bytes()
    return Context(
        catalog=parse_document(catalog_bytes.decode("utf-8")),
        catalog_bytes=catalog_bytes,
        graph_text=GRAPH.read_text(encoding="utf-8"),
        acceptance_text=ACCEPTANCE.read_text(encoding="utf-8"),
    )


def sorted_problems(problems: list[str]) -> list[str]:
    return sorted(set(problems))


def check_shape(document: dict[str, Any], context: Context) -> list[str]:
    problems = subset.errors(document, SCHEMA)
    if problems:
        return problems
    names = [state["name"] for state in document["prior_states"]]
    if len(names) != len(set(names)):
        problems.append("prior_states: duplicate name")
    used = {vector["prior_state"] for vector in document["vectors"]}
    problems += [f"prior_states: {name} is unused" for name in sorted(set(names) - used)]
    for vector in document["vectors"]:
        if vector["prior_state"] not in names:
            problems.append(f"{vector['id']}: prior_state {vector['prior_state']} is not defined")
        if vector["operation"] not in document["operations"]:
            problems.append(f"{vector['id']}: operation {vector['operation']} is not listed in operations")
    return sorted_problems(problems)


def check_identifiers(document: dict[str, Any], context: Context) -> list[str]:
    problems = []
    seen: set[str] = set()
    for vector in document["vectors"]:
        vector_id = vector["id"]
        match = VECTOR_ID.match(vector_id)
        if not match:
            problems.append(f"{vector_id}: identifier does not match G-(POS|NEG)-<AREA>-<n>")
        elif POLARITY[match.group(1)] != vector["polarity"]:
            problems.append(f"{vector_id}: polarity {vector['polarity']} disagrees with the identifier")
        if vector_id in seen:
            problems.append(f"{vector_id}: duplicate identifier")
        seen.add(vector_id)
    return sorted_problems(problems)


def section_19_names(context: Context, sentence: re.Pattern[str]) -> list[str]:
    match = sentence.search(section_19(context.graph_text))
    if match is None:
        raise ValueError("graph.md section 19 does not list its coverage identifiers and operations")
    return sorted(CODE.findall(match.group(1)))


def part2_joined(context: Context) -> dict[str, list[str]]:
    """Coverage identifiers and operations that section 35 adds to the section 19 lists."""
    match = PART2_JOIN.search(context.graph_text)
    if match is None:
        raise ValueError("graph.md does not join the part 2 coverage identifiers and operations")
    return {"coverage": CODE.findall(match.group(1)), "operations": CODE.findall(match.group(2))}


def joined_names(context: Context, sentence: re.Pattern[str], kind: str) -> list[str]:
    return sorted(set(section_19_names(context, sentence)) | set(part2_joined(context)[kind]))


def check_coverage(document: dict[str, Any], context: Context) -> list[str]:
    listed = set(document["coverage_ids"])
    found: dict[str, set[str]] = {area: set() for area in listed}
    problems = []
    areas = joined_names(context, COVERAGE_SENTENCE, "coverage")
    if document["coverage_ids"] != areas:
        problems.append(f"coverage_ids must be the {len(areas)} coverage areas: {areas}")
    operations = joined_names(context, OPERATIONS_SENTENCE, "operations")
    if document["operations"] != operations:
        problems.append(f"operations must be the section 19 operations joined with part 2: {operations}")
    for vector in document["vectors"]:
        for area in vector["coverage"]:
            if area not in listed:
                problems.append(f"{vector['id']}: coverage {area} is not listed in coverage_ids")
            else:
                found[area].add(vector["polarity"])
    for area in sorted(listed):
        for polarity in ("positive", "negative"):
            if polarity not in found[area]:
                problems.append(f"coverage {area} has no {polarity} vector")
    return sorted_problems(problems)


def documented_errors(context: Context) -> tuple[set[str], set[str]]:
    graph = set(ERROR_HEADING.findall(context.graph_text))
    return graph, graph | set(ERROR_HEADING.findall(context.acceptance_text))


def check_errors(document: dict[str, Any], context: Context) -> list[str]:
    graph, documented = documented_errors(context)
    expected = set()
    problems = []
    for vector in document["vectors"]:
        error_id = vector["expect"].get("error_id")
        if error_id is None:
            continue
        expected.add(error_id)
        if error_id not in documented:
            problems.append(f"{vector['id']}: error {error_id} is not a documented error heading")
    wanted = sorted(graph | expected)
    if document["error_ids"] != wanted:
        problems.append(f"error_ids must be the graph errors plus the expected errors: {wanted}")
    return sorted_problems(problems)


def ref_key(ref: dict[str, Any]) -> str:
    return json.dumps(ref, sort_keys=True, separators=(",", ":"))


def catalog_ref(pack: dict[str, Any], element_id: str, version: str) -> dict[str, Any]:
    return {"owner": {"kind": "pack", "pack": dict(pack)}, "id": element_id, "version": version}


def core_ref(element_id: str) -> dict[str, Any]:
    return {"owner": {"kind": "core", "contract": KERNEL_CONTRACT}, "id": element_id, "version": "1.0.0"}


def fact_refs(node: dict[str, Any]) -> list[dict[str, Any]]:
    pack = {"id": node["pack_id"], "version": node["pack_version"]}
    refs = [catalog_ref(pack, node["fact_id"], pack["version"])]
    refs += [catalog_ref(pack, item["id"], pack["version"]) for item in node.get("dimensions", [])]
    return refs


def node_refs(node: dict[str, Any]) -> list[dict[str, Any]]:
    keys = set(node)
    if keys == {"owner", "id", "version"}:
        return [node]
    if keys == {"pack", "id", "version"} and isinstance(node["pack"], dict):
        return [catalog_ref(node["pack"], node["id"], node["version"])]
    if {"pack_id", "pack_version", "fact_id"} <= keys:
        return fact_refs(node)
    if {"resource_id", "kind", "anchor"} <= keys:
        return [core_ref(node["kind"])]
    if {"pack", "definition_id", "versions"} <= keys:
        return [catalog_ref(node["pack"], node["definition_id"], node["versions"]["minimum"])]
    return []


def collect_refs(value: Any, found: dict[str, dict[str, Any]]) -> None:
    if isinstance(value, dict):
        for ref in node_refs(value):
            found[ref_key(ref)] = ref
        for item in value.values():
            collect_refs(item, found)
    elif isinstance(value, list):
        for item in value:
            collect_refs(item, found)


def prior_states(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {state["name"]: state for state in document["prior_states"]}


def used_refs(vector: dict[str, Any], states: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    collect_refs([states.get(vector["prior_state"], {}), vector["input"], vector["expect"]], found)
    return found


def definition_problems(vector: dict[str, Any], entries: dict[str, dict[str, Any]]) -> list[str]:
    problems = []
    for definition in vector["definitions"]:
        entry = entries.get(ref_key(definition["ref"]))
        label = f"{vector['id']}: {definition['ref'].get('id')}"
        if entry is None:
            problems.append(f"{label} is not in the element catalog")
            continue
        if entry["disposition"] != definition["disposition"]:
            problems.append(f"{label} has disposition {entry['disposition']}, not {definition['disposition']}")
        if "planes" in definition and definition["planes"] != entry["planes"]:
            problems.append(f"{label} planes {definition['planes']} differ from the catalog")
    return problems


def declaration_problems(vector: dict[str, Any], used: dict[str, dict[str, Any]]) -> list[str]:
    declared = {ref_key(definition["ref"]) for definition in vector["definitions"]}
    problems = [f"{vector['id']}: {used[key].get('id')} is referenced but not declared in definitions"
                for key in sorted(set(used) - declared)]
    problems += [f"{vector['id']}: a declared definition is not referenced: {key}"
                 for key in sorted(declared - set(used))]
    return problems


def inadmissible_problems(vector: dict[str, Any], entries: dict[str, dict[str, Any]]) -> list[str]:
    listed = vector["expect"].get("inadmissible_operations")
    if listed is None:
        return []
    wanted = sorted(key for key, entry in entries.items()
                    if entry["element_kind"] == "operation" and entry["disposition"] != "member")
    if sorted(ref_key(ref) for ref in listed) != wanted:
        return [f"{vector['id']}: inadmissible_operations differ from the operations without disposition member"]
    return []


def pack_problems(vector: dict[str, Any], states: dict[str, dict[str, Any]], packs: set[str]) -> list[str]:
    registry = (states.get(vector["prior_state"]) or {}).get("registry") or {}
    named = list(registry.get("packs", [])) + list(vector["input"].get("packs", []))
    uncovered = {ref_key(pack) for pack in vector.get("uncovered_packs", [])}
    problems = [f"{vector['id']}: pack {pack['id']} {pack['version']} is not covered by the catalog"
                for pack in named if ref_key(pack) not in packs and ref_key(pack) not in uncovered]
    problems += [f"{vector['id']}: uncovered pack {key} is covered by the catalog" for key in sorted(uncovered & packs)]
    return problems


def catalog_entries(context: Context) -> dict[str, dict[str, Any]]:
    return {ref_key(entry["ref"]): entry for entry in context.catalog["elements"]}


def registered_entries(state: dict[str, Any] | None, entries: dict[str, dict[str, Any]]
                       ) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """The catalog entries as a prior state registers them: its catalog mutations applied to a copy."""
    registry = (state or {}).get("registry") or {}
    mutations = registry.get("catalog_mutations", [])
    if not mutations:
        return entries, []
    label = f"prior state {state['name']}"
    if registry["element_catalog"] != "registered":
        return entries, [f"{label}: catalog mutations need a registered element catalog"]
    result = dict(entries)
    problems = []
    for mutation in mutations:
        change = mutation["set_disposition"]
        key = ref_key(change["ref"])
        entry = result.get(key)
        if entry is None:
            problems.append(f"{label}: catalog mutation names {change['ref'].get('id')}, which is not in the catalog")
        elif entry is not entries.get(key) or entry["disposition"] != "member":
            problems.append(f"{label}: catalog mutation of {change['ref'].get('id')} must change one member entry once")
        else:
            mutated_entry = copy.deepcopy(entry)
            mutated_entry.update(disposition=change["disposition"], planes=[], reason=change["reason"],
                                 tracking=change["tracking"])
            result[key] = mutated_entry
    return result, problems


def state_entries(document: dict[str, Any], context: Context) -> tuple[dict[str, dict[str, dict[str, Any]]], list[str]]:
    """Catalog entries registered by each prior state, keyed by state name, and the mutation problems."""
    entries = catalog_entries(context)
    result, problems = {}, []
    for state in document["prior_states"]:
        result[state["name"]], found = registered_entries(state, entries)
        problems += found
    return result, problems


def check_definitions(document: dict[str, Any], context: Context) -> list[str]:
    entries = catalog_entries(context)
    packs = {ref_key(entry["ref"]["owner"]["pack"]) for entry in context.catalog["elements"]
             if entry["ref"]["owner"]["kind"] == "pack"}
    states = prior_states(document)
    registered, problems = state_entries(document, context)
    for vector in document["vectors"]:
        vector_entries = registered.get(vector["prior_state"], entries)
        problems += definition_problems(vector, vector_entries)
        problems += declaration_problems(vector, used_refs(vector, states))
        problems += inadmissible_problems(vector, vector_entries)
        problems += pack_problems(vector, states, packs)
    return sorted_problems(problems)


def collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        if isinstance(value.get("key"), str) and value["key"].startswith("sha256:"):
            found.add(value["key"])
        for item in value.values():
            collect_keys(item, found)
    elif isinstance(value, list):
        for item in value:
            collect_keys(item, found)


def anchor_key(identity: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical(identity)).hexdigest()


def key_problems(vector: dict[str, Any], state: dict[str, Any], allowed: set[str]) -> list[str]:
    problems = []
    registered = set(((state or {}).get("registry") or {}).get("identification_schemes", []))
    declared = set()
    for entry in vector.get("anchor_keys", []):
        identity = entry["identity"]
        declared.add(entry["key"])
        if anchor_key(identity) != entry["key"]:
            problems.append(f"{vector['id']}: key {entry['key']} is not sha256 over the JCS identity object")
        if identity["scheme"] not in registered or identity["scheme"] not in allowed:
            problems.append(f"{vector['id']}: scheme {identity['scheme']} is not registered for the vector")
    used: set[str] = set()
    collect_keys([state, vector["input"]], used)
    problems += [f"{vector['id']}: key {key} has no declared identity object" for key in sorted(used - declared)]
    problems += [f"{vector['id']}: declared key {key} is not used" for key in sorted(declared - used)]
    return problems


def check_anchor_keys(document: dict[str, Any], context: Context) -> list[str]:
    allowed = {scheme.get("id") for scheme in context.catalog["identification_schemes"]}
    allowed |= set(document["synthetic_identification_schemes"])
    states = prior_states(document)
    problems = []
    for vector in document["vectors"]:
        problems += key_problems(vector, states.get(vector["prior_state"], {}), allowed)
    return sorted_problems(problems)


class Statement(NamedTuple):
    klass: str
    operation: str | None
    error_id: str | None


# PUB-3 states the publication of operator records in prose; section 19 has no row for it, so its
# vectors are required here by identifier. A section 19 row with the same identifier takes precedence.
PUBLICATION_STATEMENTS = {
    "G-POS-PUB-1": Statement("Publication", "apply", None),
    "G-NEG-PUB-1": Statement("Publication", "apply", "relation_not_qualified"),
}


def section_19(graph_text: str) -> str:
    match = SECTION_19.search(graph_text)
    if match is None:
        raise ValueError("graph.md has no section 19")
    return match.group(1)


def section_36_statements(graph_text: str) -> dict[str, Statement]:
    match = SECTION_36_HEADING.search(graph_text)
    if match is None:
        raise ValueError("graph.md has no section 36")
    rows = {}
    for identifier, statement, expected in SECTION_36_ROW.findall(graph_text[match.start():]):
        operation = LEADING_OPERATION.match(statement.strip())
        error = REJECTED_ERROR.match(expected.strip())
        rows[identifier] = Statement("Retrieval", operation.group(1) if operation else None,
                                     error.group(1) if error else None)
    if len(rows) != 21:
        raise ValueError("graph.md section 36 does not list 21 vectors")
    return rows


def statements(graph_text: str) -> tuple[dict[str, Statement], set[str]]:
    text = section_19(graph_text)
    rows = {}
    for klass, identifier, statement, expected in STATEMENT_ROW.findall(text):
        operation = LEADING_OPERATION.match(statement)
        error = REJECTED_ERROR.match(expected)
        rows[identifier] = Statement(klass, operation and operation.group(1), error and error.group(1))
    outside = set(IDENTIFIER.findall(STATEMENT_ROW.sub("", text)))
    rows.update(section_36_statements(graph_text))
    return rows, outside


def required_identifiers(rows: dict[str, Statement], outside: set[str]) -> set[str]:
    return set(rows) | outside


def statement_problems(vector: dict[str, Any], row: Statement, operations: set[str]) -> list[str]:
    problems = []
    if row.operation in operations and vector["operation"] != row.operation:
        problems.append(f"{vector['id']}: operation {vector['operation']} differs from the statement {row.operation}")
    if vector["expect"].get("error_id") != row.error_id:
        problems.append(f"{vector['id']}: expected {vector['expect'].get('error_id')} differs from the statement {row.error_id}")
    return problems


def check_statements(document: dict[str, Any], context: Context) -> list[str]:
    rows, outside = statements(context.graph_text)
    rows = {**PUBLICATION_STATEMENTS, **rows}
    operations = set(document["operations"])
    by_id = {vector["id"]: vector for vector in document["vectors"]}
    problems = [f"{identifier}: section 19 statement has no vector"
                for identifier in sorted(required_identifiers(rows, outside) - set(by_id))]
    for identifier, vector in by_id.items():
        if identifier in rows:
            problems += statement_problems(vector, rows[identifier], operations)
    return sorted_problems(problems)


def snapshot_identifier(snapshot: dict[str, Any]) -> str:
    return digest_without(snapshot, "snapshot_id")


def cut_identifier(members: list[dict[str, Any]]) -> str:
    return "sha256:" + hashlib.sha256(canonical({"contract": CUT_CONTRACT, "members": members})).hexdigest()


def finding_order(finding: dict[str, Any]) -> tuple[bytes, bytes]:
    return finding["kind"].encode("utf-8"), canonical(finding["subject"])


def relation_order(entry: dict[str, Any]) -> tuple[bytes, bytes, bytes]:
    return canonical(entry["definition"]), entry["from"].encode("utf-8"), entry["to"].encode("utf-8")


def snapshot_problems(vector: dict[str, Any]) -> list[str]:
    problems = subset.errors(vector["input"], CUT_INPUT)
    if problems:
        return [f"{vector['id']}: {problem}" for problem in problems]
    for snapshot in vector["input"]["snapshots"]:
        if snapshot.get("snapshot_id") != snapshot_identifier(snapshot):
            problems.append(f"{vector['id']}: snapshot_id of {snapshot.get('asset_id')} is not content-derived")
    return problems


def rejected_cut_problems(vector: dict[str, Any]) -> list[str]:
    snapshots = vector["input"]["snapshots"]
    assets = [snapshot.get("asset_id") for snapshot in snapshots]
    error_id = vector["expect"]["error_id"]
    if error_id == "duplicate_key" and len(assets) == len(set(assets)):
        return [f"{vector['id']}: duplicate_key needs two snapshots of one asset"]
    if error_id == "bounds_exceeded" and (len(snapshots) <= MAX_CUT_MEMBERS or len(assets) != len(set(assets))):
        return [f"{vector['id']}: bounds_exceeded needs more than {MAX_CUT_MEMBERS} snapshots of distinct assets"]
    if error_id not in ("duplicate_key", "bounds_exceeded"):
        return [f"{vector['id']}: assemble_cut rejects only duplicate_key or bounds_exceeded here, not {error_id}"]
    return []


def member_problems(vector: dict[str, Any], cut: dict[str, Any]) -> list[str]:
    snapshots = vector["input"]["snapshots"]
    label = vector["id"]
    problems = []
    if len(snapshots) > MAX_CUT_MEMBERS or len({s["asset_id"] for s in snapshots}) != len(snapshots):
        problems.append(f"{label}: accepted cut input needs at most {MAX_CUT_MEMBERS} snapshots of distinct assets")
    members = cut["members"]
    if members != sorted(members, key=lambda member: member["asset_id"].encode("utf-8")):
        problems.append(f"{label}: members are not in canonical order (by asset identifier)")
    given = sorted((s["asset_id"], s["snapshot_id"]) for s in snapshots)
    if sorted((m["asset_id"], m["snapshot_id"]) for m in members) != given:
        problems.append(f"{label}: members differ from the input snapshots")
    if cut["cut_id"] != cut_identifier(members):
        problems.append(f"{label}: cut_id is not sha256 over the JCS bytes of the contract and the members")
    return problems


def finding_problems(vector: dict[str, Any], cut: dict[str, Any]) -> list[str]:
    label = vector["id"]
    problems = []
    for finding in cut["findings"]:
        schema = SUBJECTS.get(finding["kind"])
        if schema is None:
            problems.append(f"{label}: finding kind {finding['kind']} is not a CutFindingKind")
        elif subset.errors(finding["subject"], schema):
            problems.append(f"{label}: {finding['kind']} subject does not have the shape of its kind")
        elif any(value != sorted(value) for value in finding["subject"].values() if isinstance(value, list)):
            problems.append(f"{label}: {finding['kind']} subject lists are not sorted")
    if cut["findings"] != sorted(cut["findings"], key=finding_order):
        problems.append(f"{label}: findings are not in canonical order (kind, canonical subject)")
    excluded = sorted({asset for finding in cut["findings"] if finding["kind"] == "duplicate_identity"
                       for asset in finding["subject"].get("asset_ids", [])})
    if cut["excluded_members"] != excluded:
        problems.append(f"{label}: excluded_members must be the members named by duplicate_identity: {excluded}")
    wanted = "partial" if excluded else vector["input"]["completeness"]
    if cut["completeness"] != wanted:
        problems.append(f"{label}: completeness must be {wanted}; an excluded member makes the cut partial")
    return problems


def held_relations(snapshots: list[dict[str, Any]], excluded: set[str]) -> dict[tuple[bytes, bytes, bytes], Any]:
    held = {}
    for snapshot in snapshots:
        if snapshot["asset_id"] in excluded:
            continue
        for relation in snapshot.get("relations", []):
            held[relation_order(relation)] = (snapshot["asset_id"], relation["state"])
    return held


def coherence_problems(vector: dict[str, Any], cut: dict[str, Any]) -> list[str]:
    label = vector["id"]
    entries = cut["relation_coherence"]
    problems = []
    if entries != sorted(entries, key=relation_order):
        problems.append(f"{label}: relation_coherence is not in canonical order (definition, from, to)")
    held = held_relations(vector["input"]["snapshots"], set(cut["excluded_members"]))
    given = {relation_order(entry): (entry["asset_id"], entry["state"]) for entry in entries}
    if given != held or len(given) != len(entries):
        problems.append(f"{label}: every relation instance of an included member needs exactly one coherence "
                        "with its holder and state")
    return problems


def subject_resources(snapshot: dict[str, Any], entries: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    planes: dict[str, set[str]] = {}
    for envelope in snapshot.get("facts", []):
        key = envelope["key"]
        entry = entries.get(ref_key(fact_refs(key)[0]))
        if entry is None or entry["disposition"] != "member":
            continue
        dimension = entry.get("attributes", {}).get("subject", {}).get("dimension", {}).get("id")
        for item in key["dimensions"]:
            if item["id"] == dimension:
                planes.setdefault(item["value"].get("text", ""), set()).update(entry["planes"])
    services = {}
    for service in snapshot.get("services", []):
        definition = service["definition"]
        entry = entries.get(ref_key(catalog_ref(definition["pack"], definition["id"], definition["version"])))
        if "resource" in service and entry is not None:
            services[service["instance_id"]] = service["resource"]
            planes.setdefault(service["resource"], set()).update(entry["planes"])
    for capability in snapshot.get("capabilities", []):
        definition = capability["definition"]
        entry = entries.get(ref_key(catalog_ref(definition["pack"], definition["id"], definition["version"])))
        if capability.get("service_instance") in services and entry is not None:
            planes.setdefault(services[capability["service_instance"]], set()).update(entry["planes"])
    return planes


def catalog_planes(entries: dict[str, dict[str, Any]], ref: dict[str, Any]) -> list[str]:
    return entries.get(ref_key(ref), {}).get("planes", [])


def plane_list(resource: dict[str, Any], extra: set[str], order: list[str], entries: dict[str, dict[str, Any]]
               ) -> list[str]:
    """PLN-3 planes of one current resource, in catalog order."""
    if resource["state"] != "current":
        return []
    planes = set(extra)
    if resource["anchor"]["class"] in ("equipment", "component"):
        planes.add("physical")
    admitted = set(catalog_planes(entries, core_ref(resource["kind"])))
    return [plane for plane in order if plane in planes and plane in admitted]


def endpoint_planes(edges: list[dict[str, Any]], entries: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    """Planes of qualified coherent relation instances, by endpoint (PLN-2)."""
    reached: dict[str, set[str]] = {}
    for edge in edges:
        if edge["coherence"] != "coherent" or edge["state"] != "qualified":
            continue
        names = catalog_planes(entries, edge["definition"])
        for end in (edge["from"], edge["to"]):
            reached.setdefault(end, set()).update(names)
    return reached


def resource_planes(cut: dict[str, Any], snapshots: list[dict[str, Any]], entries: dict[str, dict[str, Any]],
                    order: list[str]) -> dict[str, list[str]]:
    excluded = set(cut["excluded_members"])
    edges = [{"coherence": entry["coherence"], "state": entry["state"], "definition": entry["definition"],
              "from": entry["from"], "to": entry["to"]} for entry in cut["relation_coherence"]]
    reached = endpoint_planes(edges, entries)
    result: dict[str, list[str]] = {}
    for snapshot in snapshots:
        subjects = subject_resources(snapshot, entries)
        for resource in snapshot.get("resources", []):
            rid = resource["resource_id"]
            if snapshot["asset_id"] in excluded or resource["state"] != "current":
                result.setdefault(rid, [])
                continue
            extra = reached.get(rid, set()) | subjects.get(rid, set())
            result[rid] = plane_list(resource, extra, order, entries)
    return result


def read_planes(snapshots: list[dict[str, Any]], edges: list[dict[str, Any]], entries: dict[str, dict[str, Any]],
                order: list[str]) -> dict[str, list[str]]:
    """PLN-3 membership of every resource in a read, keyed by resource id."""
    reached = endpoint_planes(edges, entries)
    result: dict[str, list[str]] = {}
    for snapshot in snapshots:
        subjects = subject_resources(snapshot, entries)
        for resource in snapshot.get("resources", []):
            rid = resource["resource_id"]
            if resource["state"] != "current":
                result.setdefault(rid, [])
                continue
            extra = reached.get(rid, set()) | subjects.get(rid, set())
            result[rid] = plane_list(resource, extra, order, entries)
    return result


def plane_order(catalog: dict[str, Any]) -> list[str]:
    return [plane["id"] for plane in catalog["planes"]]


def plane_problems(vector: dict[str, Any], cut: dict[str, Any], context: Context,
                   entries: dict[str, dict[str, Any]]) -> list[str]:
    order = plane_order(context.catalog)
    wanted = resource_planes(cut, vector["input"]["snapshots"], entries, order)
    listed = cut["plane_membership"]
    problems = []
    if [entry["resource_id"] for entry in listed] != sorted(wanted, key=lambda rid: rid.encode("utf-8")):
        problems.append(f"{vector['id']}: plane_membership must list every resource a member holds, "
                        "sorted by resource_id")
    for entry in listed:
        if entry["resource_id"] in wanted and entry["planes"] != wanted[entry["resource_id"]]:
            problems.append(f"{vector['id']}: {entry['resource_id']} planes {entry['planes']} differ from "
                            f"PLN-3 {wanted[entry['resource_id']]}")
    return problems


def check_cuts(document: dict[str, Any], context: Context) -> list[str]:
    problems = []
    kinds: set[str] = set()
    states: set[str] = set()
    registered, _ = state_entries(document, context)
    entries = catalog_entries(context)
    for vector in document["vectors"]:
        if vector["operation"] != "assemble_cut":
            continue
        if vector["record_type"] != "GraphCut":
            problems.append(f"{vector['id']}: assemble_cut takes record_type GraphCut")
        found = snapshot_problems(vector)
        if found:
            problems += found
            continue
        if vector["expect"]["result"] == "reject":
            problems += rejected_cut_problems(vector)
            continue
        cut = vector["expect"].get("cut")
        if cut is None:
            problems.append(f"{vector['id']}: an accepted assemble_cut states its cut")
            continue
        problems += member_problems(vector, cut) + finding_problems(vector, cut)
        problems += coherence_problems(vector, cut)
        problems += plane_problems(vector, cut, context, registered.get(vector["prior_state"], entries))
        kinds |= {finding["kind"] for finding in cut["findings"]}
        states |= {entry["coherence"] for entry in cut["relation_coherence"]}
    problems += [f"no accepted cut vector has finding {kind}" for kind in sorted(set(FINDING_KINDS) - kinds)]
    problems += [f"no accepted cut vector has coherence {state}" for state in sorted(set(COHERENCE_STATES) - states)]
    return sorted_problems(problems)


def check_catalog_digest(document: dict[str, Any], context: Context) -> list[str]:
    recorded = document["element_catalog"]
    problems = []
    if recorded["path"] != CATALOG_PATH:
        problems.append(f"element_catalog path {recorded['path']} is not {CATALOG_PATH}")
    if recorded["contract"] != context.catalog["contract"]:
        problems.append(f"element_catalog contract {recorded['contract']} differs from the catalog")
    actual = "sha256:" + hashlib.sha256(context.catalog_bytes).hexdigest()
    if recorded["sha256"] != actual:
        problems.append(f"element_catalog sha256 {recorded['sha256']} differs from the file ({actual})")
    return problems


def request_digest(request: dict[str, Any]) -> str:
    body = {key: value for key, value in request.items() if key != "page_token"}
    return "sha256:" + hashlib.sha256(canonical(body)).hexdigest()


def catalog_digest(context: Context) -> str:
    return "sha256:" + hashlib.sha256(context.catalog_bytes).hexdigest()


def named_lens(request: dict[str, Any], catalog: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    lens_id = request.get("lens")
    if not isinstance(lens_id, str):
        return None, None
    lens = next((item for item in catalog["lenses"] if item["id"] == lens_id), None)
    if lens is None:
        return None, "membership_missing"
    return lens, None


def token_error(request: dict[str, Any], cut_id: str) -> str | None:
    token = request.get("page_token")
    if token is None:
        return None
    fields = {"cut_id", "request_digest"}
    if not isinstance(token, dict) or set(token) != fields:
        return "invalid_value"
    if not DIGEST_TEXT.match(token["cut_id"]) or not DIGEST_TEXT.match(token["request_digest"]):
        return "invalid_value"
    if token["cut_id"] != cut_id or token["request_digest"] != request_digest(request):
        return "revision_conflict"
    return None


def pin_error(request: dict[str, Any], held: list[str]) -> str | None:
    pin = request.get("cut_id")
    if pin is None:
        return None
    if not isinstance(pin, str) or not DIGEST_TEXT.match(pin):
        return "invalid_value"
    if pin not in held:
        return "revision_conflict"
    return None


def bounds_error(request: dict[str, Any], lens: dict[str, Any] | None) -> str | None:
    page_size = request.get("page_size")
    if page_size is not None and page_size > PAGE_BOUND:
        return "bounds_exceeded"
    cap = lens["max_depth"] if lens is not None else DEPTH_BOUND
    if request.get("depth", cap) > cap or request.get("depth", cap) > DEPTH_BOUND:
        return "bounds_exceeded"
    return None


def cut_ref(snapshots: list[dict[str, Any]], completeness: str, not_included: list[dict[str, Any]]) -> dict[str, Any]:
    members = [{"asset_id": item["asset_id"], "snapshot_id": item["snapshot_id"]} for item in snapshots]
    members.sort(key=lambda member: member["asset_id"].encode())
    listed = sorted(not_included, key=lambda item: item["asset_id"].encode())
    return {
        "completeness": "partial" if listed else completeness,
        "cut_id": cut_identifier(members),
        "members": members,
        "not_included": listed,
    }


def resource_index(snapshots: list[dict[str, Any]], entries: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        for resource in snapshot.get("resources", []):
            if resource["resource_id"] in found:
                continue
            kind = entries.get(ref_key(core_ref(resource["kind"])), {})
            found[resource["resource_id"]] = {
                "asset_id": snapshot["asset_id"],
                "installation_root": bool(kind.get("attributes", {}).get("installation_root")),
                "kind": resource["kind"],
                "planes": list(kind.get("planes", [])),
                "resource_id": resource["resource_id"],
                "state": resource.get("state"),
            }
    return found


def coherence_of(relation: dict[str, Any], resources: dict[str, dict[str, Any]], completeness: str) -> str:
    if relation["state"] == "conflict":
        return "conflict"
    target = resources.get(relation["to"])
    if target is None:
        return "dangling" if completeness == "complete" else "outside_cut"
    if target["state"] in ("withdrawn", "retired"):
        return "stale"
    return "coherent"


def build_edges(snapshots: list[dict[str, Any]], resources: dict[str, dict[str, Any]], completeness: str
                ) -> list[dict[str, Any]]:
    edges = []
    for snapshot in snapshots:
        for relation in snapshot.get("relations", []):
            edges.append({
                "coherence": coherence_of(relation, resources, completeness),
                "definition": relation["definition"],
                "from": relation["from"],
                "state": relation["state"],
                "to": relation["to"],
            })
    return edges


def followed_keys(entries: dict[str, dict[str, Any]], lens: dict[str, Any] | None, request: dict[str, Any]
                  ) -> tuple[set[str], str | None]:
    """Relation definitions a traversal may follow, or membership_missing."""
    planes = set(lens["planes"] if lens is not None else request.get("planes", []))
    named = None if lens is not None else request.get("definitions")
    if named is None:
        return {key for key, entry in entries.items()
                if entry.get("element_kind") == "relation" and entry.get("disposition") == "member"
                and set(entry.get("planes", [])) & planes}, None
    chosen = set()
    for ref in named:
        entry = entries.get(ref_key(ref))
        if entry is None or not (set(entry.get("planes", [])) & planes):
            return set(), "membership_missing"
        chosen.add(ref_key(ref))
    return chosen, None


def annotate_edges(edges: list[dict[str, Any]], entries: dict[str, dict[str, Any]], followed: set[str]) -> None:
    for edge in edges:
        entry = entries.get(ref_key(edge["definition"]), {})
        edge["core_type"] = (entry.get("attributes") or {}).get("core_type")
        edge["follow"] = (ref_key(edge["definition"]) in followed and edge["state"] == "qualified"
                          and edge["coherence"] == "coherent")
        edge["in_plane"] = edge["follow"]


def neighbor_targets(resource_id: str, edges: list[dict[str, Any]], direction: str) -> list[tuple[dict[str, Any], str]]:
    targets = []
    for edge in edges:
        if not edge["follow"]:
            continue
        if direction != "incoming" and edge["from"] == resource_id:
            targets.append((edge, edge["to"]))
        if direction != "outgoing" and edge["to"] == resource_id and edge["from"] != resource_id:
            targets.append((edge, edge["from"]))
    targets.sort(key=lambda item: (relation_order(item[0]), item[1].encode()))
    return targets


def frontier_entry(resource_id: str, reason: str, count: int) -> dict[str, Any]:
    return {"kind": reason, "not_followed": count, "subject": {"resource_id": resource_id}}


def walk_reached(entry_ids: list[str], edges: list[dict[str, Any]], direction: str, depth_limit: int
                 ) -> tuple[dict[str, int], list[dict[str, Any]]]:
    depth = {resource_id: 0 for resource_id in entry_ids}
    frontier: list[dict[str, Any]] = []
    queue = sorted(entry_ids, key=lambda resource_id: resource_id.encode())
    seen = set(queue)
    index = 0
    while index < len(queue):
        resource_id = queue[index]
        index += 1
        targets = neighbor_targets(resource_id, edges, direction)
        if depth[resource_id] >= depth_limit:
            if targets:
                frontier.append(frontier_entry(resource_id, "depth_limit", len(targets)))
            continue
        for _edge, target in targets:
            if target in seen:
                continue
            seen.add(target)
            depth[target] = depth[resource_id] + 1
            queue.append(target)
    frontier.sort(key=finding_order)
    return depth, frontier


def resolve_entry(request: dict[str, Any], lens: dict[str, Any] | None, resources: dict[str, dict[str, Any]]
                  ) -> list[str] | str:
    entry = request.get("entry") or {}
    if entry.get("kind") == "resource":
        resource = resources.get(entry.get("resource_id"))
        if resource is None or resource["state"] != "current":
            return "dangling_reference"
        return [entry["resource_id"]]
    if entry.get("kind") == "sites":
        return sorted((rid for rid, resource in resources.items()
                       if resource["state"] == "current" and resource["installation_root"]),
                      key=lambda rid: rid.encode())
    if lens is None:
        return "dangling_reference"
    root_kinds = set(lens["root_kinds"])
    return sorted((rid for rid, resource in resources.items()
                   if resource["state"] == "current" and resource["kind"] in root_kinds),
                  key=lambda rid: rid.encode())


def result_resources(depth: dict[str, int], resources: dict[str, dict[str, Any]],
                     planes_of: dict[str, list[str]] | None = None) -> list[dict[str, Any]]:
    rows = []
    for rid, level in depth.items():
        row = {"asset_id": resources[rid]["asset_id"], "depth": level, "kind": resources[rid]["kind"],
               "resource_id": rid}
        if planes_of is not None:
            row["planes"] = list(planes_of.get(rid, []))
        rows.append(row)
    rows.sort(key=lambda row: (row["depth"], row["resource_id"].encode()))
    return rows


def result_relations(edges: list[dict[str, Any]], reached: set[str]) -> list[dict[str, Any]]:
    chosen = []
    for edge in edges:
        both = edge["from"] in reached and edge["to"] in reached
        touched = edge["from"] in reached or edge["to"] in reached
        non_member = edge["state"] != "qualified" or edge["coherence"] != "coherent"
        if (edge["follow"] and both) or (touched and non_member and not edge["follow"]):
            chosen.append({
                "coherence": edge["coherence"], "definition": edge["definition"], "from": edge["from"],
                "in_plane": edge["in_plane"], "state": edge["state"], "to": edge["to"],
            })
    chosen.sort(key=relation_order)
    return chosen


def fact_resource(fact: dict[str, Any], entries: dict[str, dict[str, Any]]
                  ) -> tuple[str | None, dict[str, Any] | None]:
    ref = fact_refs(fact["key"])[0]
    entry = entries.get(ref_key(ref))
    if entry is None:
        return None, None
    dimension = (entry.get("attributes") or {}).get("subject", {}).get("dimension", {}).get("id")
    for item in fact["key"].get("dimensions", []):
        if item["id"] == dimension:
            return item["value"].get("text"), entry
    return None, entry


def result_facts(snapshots: list[dict[str, Any]], entries: dict[str, dict[str, Any]], reached: set[str],
                 planes: set[str]) -> list[dict[str, Any]]:
    chosen = []
    for snapshot in snapshots:
        for fact in snapshot.get("facts", []):
            resource_id, entry = fact_resource(fact, entries)
            if resource_id not in reached or entry is None or entry.get("disposition") != "member":
                continue
            if planes and not (set(entry.get("planes", [])) & planes):
                continue
            chosen.append(fact)
    chosen.sort(key=lambda fact: canonical(fact["key"]))
    return chosen


def finding_resources(finding: dict[str, Any]) -> set[str]:
    subject = finding.get("subject") or {}
    found = set(subject.get("resource_ids") or [])
    if "resource_id" in subject:
        found.add(subject["resource_id"])
    return found


def result_findings(findings: list[dict[str, Any]], reached: set[str]) -> list[dict[str, Any]]:
    chosen = [finding for finding in findings if finding_resources(finding) & reached]
    return sorted(chosen, key=finding_order)


def lists_are_sorted(findings: list[dict[str, Any]]) -> bool:
    for finding in findings:
        for value in (finding.get("subject") or {}).values():
            if isinstance(value, list) and value != sorted(value):
                return False
    return True


def relation_page(relation: dict[str, Any], index_of: dict[str, int]) -> int:
    if relation["from"] in index_of:
        return index_of[relation["from"]]
    return index_of.get(relation["to"], 0)


def page_chunks(resources: list[dict[str, Any]], page_size: int) -> list[list[dict[str, Any]]]:
    return [resources[index:index + page_size] for index in range(0, len(resources), page_size)] or [[]]


def paginate(body: dict[str, Any], page_size: int, entries: dict[str, dict[str, Any]], digest: str
             ) -> list[dict[str, Any]]:
    chunks = page_chunks(body["resources"], page_size)
    index_of: dict[str, int] = {}
    for page_index, chunk in enumerate(chunks):
        for row in chunk:
            index_of[row["resource_id"]] = page_index
    pages = []
    for page_index, chunk in enumerate(chunks):
        page = {
            "cut_id": body["cut"]["cut_id"],
            "facts": [],
            "findings": [],
            "frontier": [item for item in body["frontier"]
                         if index_of.get(item["subject"]["resource_id"]) == page_index],
            "relations": [item for item in body["relations"] if relation_page(item, index_of) == page_index],
            "resources": chunk,
        }
        for fact in body["facts"]:
            resource_id, _entry = fact_resource(fact, entries)
            if index_of.get(resource_id) == page_index:
                page["facts"].append(fact)
        if page_index + 1 < len(chunks):
            page["next_page"] = {"cut_id": body["cut"]["cut_id"], "request_digest": digest}
        pages.append(page)
    for finding in body["findings"]:
        page_index = 0
        for resource_id in sorted(finding_resources(finding)):
            if resource_id in index_of:
                page_index = index_of[resource_id]
                break
        pages[page_index]["findings"].append(finding)
    return pages


def list_read(resources: dict[str, dict[str, Any]], request: dict[str, Any], cut: dict[str, Any],
              planes_of: dict[str, list[str]]) -> dict[str, Any]:
    kind = request.get("kind")
    plane = request.get("plane")
    chosen = []
    for resource in resources.values():
        if resource["state"] != "current":
            continue
        if kind is not None and resource["kind"] != kind:
            continue
        # PLN-3 membership, not the kind's catalog planes. Those only bound where an instance may appear.
        if plane is not None and plane not in planes_of.get(resource["resource_id"], []):
            continue
        chosen.append({"asset_id": resource["asset_id"], "kind": resource["kind"], "resource_id": resource["resource_id"]})
    chosen.sort(key=lambda item: item["resource_id"].encode())
    return {"cut": cut, "resources": chosen}


def graph_body(vector: dict[str, Any], entries: dict[str, dict[str, Any]], context: Context, cut: dict[str, Any],
               lens: dict[str, Any] | None, edges: list[dict[str, Any]]) -> dict[str, Any] | str:
    request = vector["input"]["request"]
    entry_ids = resolve_entry(request, lens, resource_index(vector["input"]["snapshots"], entries))
    if isinstance(entry_ids, str):
        return entry_ids
    cap = lens["max_depth"] if lens is not None else DEPTH_BOUND
    depth, frontier = walk_reached(entry_ids, edges, request.get("direction", "outgoing"), request.get("depth", cap))
    if len(frontier) > FRONTIER_BOUND:
        return "bounds_exceeded"
    reached = set(depth)
    planes = set(lens["planes"]) if lens is not None else set(request.get("planes", []))
    indexed = resource_index(vector["input"]["snapshots"], entries)
    membership = None
    if lens is not None:
        allowed = set(lens["planes"])
        full = read_planes(vector["input"]["snapshots"], edges, entries, plane_order(context.catalog))
        membership = {rid: [plane for plane in names if plane in allowed] for rid, names in full.items()}
    resource_rows = result_resources(depth, indexed, membership)
    body = {
        "cut": cut,
        "entry": request.get("entry"),
        "facts": result_facts(vector["input"]["snapshots"], entries, reached, planes) if lens is not None else [],
        "findings": result_findings(vector["input"].get("findings", []), reached),
        "frontier": frontier,
        "relations": result_relations(edges, reached),
        "resources": resource_rows,
    }
    if lens is not None:
        body["catalog"] = catalog_digest(context)
        body["contract"] = LENS_RESULT_CONTRACT
        body["lens"] = lens["id"]
    if request.get("page_size") is not None:
        body["pages"] = paginate(body, request["page_size"], entries, request_digest(request))
    return body


def scope_members(scope: str, edges: list[dict[str, Any]]) -> set[str]:
    seen = {scope}
    queue = [scope]
    index = 0
    while index < len(queue):
        current = queue[index]
        index += 1
        for edge, target in neighbor_targets(current, edges, "outgoing"):
            if edge["core_type"] not in ("groups", "contains") or target in seen:
                continue
            seen.add(target)
            queue.append(target)
    seen.discard(scope)
    return seen


def sum_fact_rows(snapshots: list[dict[str, Any]], entries: dict[str, dict[str, Any]], planes: set[str]
                  ) -> list[dict[str, Any]]:
    rows = []
    for snapshot in snapshots:
        for fact in snapshot.get("facts", []):
            resource_id, entry = fact_resource(fact, entries)
            if resource_id is None or entry is None or entry.get("disposition") != "member":
                continue
            if not (set(entry.get("planes", [])) & planes):
                continue
            rows.append({"asset_id": snapshot["asset_id"], "entry": entry, "fact": fact, "resource_id": resource_id})
    return rows


def quality_reason(fact: dict[str, Any]) -> str | None:
    if fact.get("conflicts"):
        return "member_conflict"
    candidates = fact.get("candidates") or []
    if not candidates:
        return "member_unavailable"
    quality = candidates[0].get("quality") or {}
    if quality.get("freshness") == "conflict" or quality.get("validity") == "conflict":
        return "member_conflict"
    if quality.get("availability") != "available" or quality.get("freshness") != "fresh":
        return "member_unavailable"
    return None


def sign_token(reference: Any) -> str:
    if isinstance(reference, dict):
        return json.dumps(reference, sort_keys=True, separators=(",", ":"))
    return "" if reference is None else str(reference)


def sign_reason(rows: list[dict[str, Any]]) -> str | None:
    """SUM-5. The sign reference is the catalog entry's, never a fact member."""
    signed = []
    for row in rows:
        attributes = row["entry"].get("attributes") or {}
        if attributes.get("direction") == "signed":
            signed.append((row, attributes.get("sign_reference")))
    if not signed:
        return None
    references = {sign_token(reference) for _row, reference in signed}
    if len(references) > 1:
        return "mixed_sign_reference"
    reference = signed[0][1]
    if reference == "native_convention" and len({row["asset_id"] for row, _reference in signed}) > 1:
        return "mixed_sign_reference"
    return None


def add_quantities(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    total = 0
    unit = None
    for row in sorted(rows, key=lambda item: item["resource_id"].encode()):
        quantity = row["fact"]["candidates"][0]["value"]["quantity"]
        number = quantity["number"]
        if number.get("exponent10") != 0 or (unit is not None and quantity["unit"] != unit):
            return None
        total += int(number["coefficient"])
        unit = quantity["unit"]
    if unit is None:
        return None
    return {"coefficient": str(total), "exponent10": 0, "unit": unit}


def aggregation_of(row: dict[str, Any]) -> str | None:
    return (row["entry"].get("attributes") or {}).get("aggregation")


def sum_decision(rows: list[dict[str, Any]], members: set[str], fact_ref: dict[str, Any], scope: str,
                 findings: list[dict[str, Any]], cut: dict[str, Any], entries: dict[str, dict[str, Any]]
                 ) -> dict[str, Any]:
    """The withheld reason, or the member sum with aggregates left beside it."""
    if not members:
        return {"withheld": "no_coverage"}
    if same_unit_members(findings, members):
        return {"withheld": "same_unit"}
    if cut["completeness"] == "partial" and cut["not_included"]:
        return {"withheld": "partial_cut"}
    wanted = ref_key(fact_ref)
    relevant = [row for row in rows if row["resource_id"] in members
                and ref_key(fact_refs(row["fact"]["key"])[0]) == wanted and aggregation_of(row) == "member"]
    if {row["resource_id"] for row in relevant} != set(members):
        return {"withheld": "member_unavailable"}
    blocked = next((quality_reason(row["fact"]) for row in relevant if quality_reason(row["fact"])), None)
    if blocked:
        return {"withheld": blocked}
    signed = sign_reason(relevant)
    if signed:
        return {"withheld": signed}
    value = add_quantities(relevant)
    if value is None:
        return {"withheld": "member_unavailable"}
    body: dict[str, Any] = {"not_added": not_added_ids(rows, members, scope), "value": value}
    observed = scope_aggregate(rows, scope, fact_ref)
    if observed is not None:
        body["observed_aggregate"] = observed
    return body


def same_unit_members(findings: list[dict[str, Any]], members: set[str]) -> bool:
    for finding in findings:
        if finding.get("kind") != "same_unit":
            continue
        if len(set(finding.get("subject", {}).get("resource_ids", [])) & set(members)) >= 2:
            return True
    return False


def not_added_ids(rows: list[dict[str, Any]], members: set[str], scope: str) -> list[str]:
    scope_or_member = members | {scope}
    found = {row["fact"]["key"]["fact_id"] for row in rows
             if row["resource_id"] in scope_or_member and aggregation_of(row) != "member"}
    return sorted(found)


def aggregate_fact_id(member_id: str) -> str:
    """Catalog id of the aggregate fact paired with a member fact definition."""
    head, separator, tail = member_id.rpartition(".")
    if not separator:
        return ""
    return f"{head}.aggregate_{tail}"


def scope_aggregate(rows: list[dict[str, Any]], scope: str | None, fact_ref: dict[str, Any]) -> dict[str, Any] | None:
    """The scope's aggregate of the requested fact definition, not any aggregate on the scope."""
    wanted = aggregate_fact_id(fact_ref["id"])
    found = [row["fact"] for row in rows
             if row["resource_id"] == scope and aggregation_of(row) == "aggregate"
             and row["fact"]["key"]["fact_id"] == wanted]
    found.sort(key=lambda fact: canonical(fact["key"]))
    return found[0] if found else None


def sum_read(vector: dict[str, Any], entries: dict[str, dict[str, Any]], context: Context, cut: dict[str, Any],
             lens: dict[str, Any], edges: list[dict[str, Any]]) -> dict[str, Any] | str:
    request = vector["input"]["request"]
    body = graph_body(vector, entries, context, cut, lens, edges)
    if isinstance(body, str):
        return body
    reached = {row["resource_id"] for row in body["resources"]}
    scope = request["scope"]
    members = scope_members(scope, edges) if scope in reached else set()
    decision = sum_decision(sum_fact_rows(vector["input"]["snapshots"], entries, set(lens["planes"])),
                            members, request["fact"], scope, vector["input"].get("findings", []), cut, entries)
    decision.update(cut=cut, fact=request["fact"]["id"], scope=scope)
    return decision


def cited_ok(report: dict[str, Any], edges: list[dict[str, Any]], resources: dict[str, dict[str, Any]]) -> bool:
    for disposition in report.get("dispositions", []):
        for resource_id in disposition.get("resources", []):
            resource = resources.get(resource_id)
            if resource is None or resource["state"] != "current":
                return False
        for key in disposition.get("relations", []):
            if not any(edge["definition"] == key.get("definition") and edge["from"] == key.get("from")
                       and edge["to"] == key.get("to") and edge["state"] == "qualified"
                       and edge["coherence"] == "coherent" for edge in edges):
                return False
    return True


def project_read(request: dict[str, Any], edges: list[dict[str, Any]], resources: dict[str, dict[str, Any]],
                 cut: dict[str, Any]) -> dict[str, Any] | str:
    report = request.get("report")
    if not isinstance(report, dict) or report.get("lens") != request.get("lens"):
        return "invalid_value"
    if not cited_ok(report, edges, resources):
        return "projection_incomplete"
    return {"cut": cut, "lens": request["lens"], "report": report}


def prepare_read(vector: dict[str, Any], context: Context) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    payload = vector["input"]
    request = payload["request"]
    not_included = list(payload.get("not_included") or [])
    cut = cut_ref(payload["snapshots"], payload.get("completeness", "complete"), not_included)
    lens, lens_error = named_lens(request, context.catalog)
    if lens_error:
        return cut, None, lens_error
    held = payload.get("held_cuts", [cut["cut_id"]])
    error = token_error(request, cut["cut_id"]) or pin_error(request, held) or bounds_error(request, lens)
    return cut, lens, error


def evaluate_read(vector: dict[str, Any], entries: dict[str, dict[str, Any]], context: Context
                  ) -> tuple[str | None, dict[str, Any] | None]:
    """Recompute a read: an error identifier, or the canonical result body."""
    cut, lens, error = prepare_read(vector, context)
    if error:
        return error, None
    request = vector["input"]["request"]
    resources = resource_index(vector["input"]["snapshots"], entries)
    if vector["operation"] == "list_resources":
        edges = build_edges(vector["input"]["snapshots"], resources, cut["completeness"])
        planes_of = read_planes(vector["input"]["snapshots"], edges, entries, plane_order(context.catalog))
        return None, list_read(resources, request, cut, planes_of)
    edges = build_edges(vector["input"]["snapshots"], resources, cut["completeness"])
    followed, follow_error = followed_keys(entries, lens, request)
    if follow_error:
        return follow_error, None
    annotate_edges(edges, entries, followed)
    if vector["operation"] == "project":
        projected = project_read(request, edges, resources, cut)
        if isinstance(projected, str):
            return projected, None
        return None, projected
    if vector["operation"] == "sum_members":
        if lens is None:
            return "membership_missing", None
        summed = sum_read(vector, entries, context, cut, lens, edges)
        if isinstance(summed, str):
            return summed, None
        return None, summed
    walked = graph_body(vector, entries, context, cut, lens, edges)
    if isinstance(walked, str):
        return walked, None
    return None, walked


def read_snapshot_problems(vector: dict[str, Any]) -> list[str]:
    problems = []
    payload = vector.get("input")
    if not isinstance(payload, dict) or not isinstance(payload.get("request"), dict) or not payload.get("snapshots"):
        return [f"{vector['id']}: a read input is member snapshots plus a request"]
    if payload.get("not_included") and payload.get("completeness") != "partial":
        problems.append(f"{vector['id']}: completeness must be partial when an asset is not included")
    for snapshot in payload["snapshots"]:
        if snapshot.get("snapshot_id") != snapshot_identifier(snapshot):
            problems.append(f"{vector['id']}: snapshot_id of {snapshot.get('asset_id')} is not content-derived")
    return problems


def lens_strings(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        lens_id = value.get("lens")
        if isinstance(lens_id, str):
            found.add(lens_id)
        for item in value.values():
            lens_strings(item, found)
    elif isinstance(value, list):
        for item in value:
            lens_strings(item, found)


def first_diff(left: Any, right: Any, prefix: str = "") -> str:
    if type(left) is not type(right) or not isinstance(left, (dict, list)):
        return prefix or "value"
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{prefix}.length" if prefix else "length"
        for index, (item, other) in enumerate(zip(left, right)):
            if item != other:
                return first_diff(item, other, f"{prefix}[{index}]")
        return prefix or "value"
    for key in sorted(set(left) | set(right)):
        child = f"{prefix}.{key}" if prefix else str(key)
        if key not in left or key not in right or left[key] != right[key]:
            return first_diff(left.get(key), right.get(key), child)
    return prefix or "value"


def known_lenses(context: Context) -> set[str]:
    return {lens["id"] for lens in context.catalog["lenses"]}


def mismatched_read(vector: dict[str, Any], error: str | None, body: dict[str, Any] | None, context: Context
                    ) -> list[str]:
    label = vector["id"]
    expect = vector["expect"]
    if error:
        if expect.get("result") == "reject" and expect.get("error_id") == error:
            return []
        problems = [f"{label}: expected {expect.get('error_id')} differs from {error}"]
        lens_id = vector["input"]["request"].get("lens")
        if error == "membership_missing" and isinstance(lens_id, str) and lens_id not in known_lenses(context):
            problems.append(f"{label}: lens {lens_id} is not in the catalog")
        return problems
    problems = []
    if expect.get("result") != "accept":
        problems.append(f"{label}: recomputed read is accepted")
    read = expect.get("read")
    if not isinstance(read, dict) or read != body:
        problems.append(f"{label}: read result differs at {first_diff(read, body)}")
    if isinstance(read, dict) and "path" in read or (isinstance(body, dict) and "path" in body):
        problems.append(f"{label}: result has a path member")
    named: set[str] = set()
    lens_strings(vector["input"], named)
    for lens_id in sorted(named):
        if lens_id not in known_lenses(context):
            problems.append(f"{label}: lens {lens_id} is not in the catalog")
    return problems


def check_one_read(vector: dict[str, Any], entries: dict[str, dict[str, Any]], context: Context) -> list[str]:
    if vector["record_type"] != "Read":
        return [f"{vector['id']}: {vector['operation']} takes record_type Read"]
    problems = read_snapshot_problems(vector)
    if problems:
        return problems
    if not lists_are_sorted(vector["input"].get("findings", [])):
        return [f"{vector['id']}: subject lists are not sorted"]
    error, body = evaluate_read(vector, entries, context)
    return mismatched_read(vector, error, body, context)


def check_reads(document: dict[str, Any], context: Context) -> list[str]:
    registered, _found = state_entries(document, context)
    entries = catalog_entries(context)
    problems = []
    for vector in document["vectors"]:
        if vector["operation"] not in READ_OPERATIONS:
            continue
        problems += check_one_read(vector, registered.get(vector["prior_state"], entries), context)
    return sorted_problems(problems)


RULES = (
    ("shape", check_shape),
    ("identifiers", check_identifiers),
    ("coverage", check_coverage),
    ("errors", check_errors),
    ("definitions", check_definitions),
    ("anchor_keys", check_anchor_keys),
    ("statements", check_statements),
    ("cuts", check_cuts),
    ("reads", check_reads),
    ("catalog_digest", check_catalog_digest),
)


def validate(document: dict[str, Any], context: Context) -> list[str]:
    problems = check_shape(document, context)
    if problems:
        return problems
    for _, rule in RULES[1:]:
        problems += rule(document, context)
    return problems


def main() -> int:
    try:
        document = load_document(VECTORS)
        problems = validate(document, load_context())
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"graph acceptance vectors: {len(document['vectors'])} vectors valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
