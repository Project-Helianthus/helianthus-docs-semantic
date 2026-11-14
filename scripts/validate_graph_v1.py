#!/usr/bin/env python3
"""Validate the graph acceptance vectors against the graph contract and the element catalog.

The document is ``api/v1/graph-acceptance-vectors.json``
(``helianthus.semantic.graph.acceptance/v1``). Each rule returns a list of
problems; an empty list from every rule means the document is valid. The
rules check the shape and repeated keys, the identifiers, the coverage areas,
the stable errors, the definition references, the anchor keys, the section 19
statements of the covered classes and the recorded catalog digest.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

import json_schema_subset_v1 as subset
from check_snapshot_vector_ids import canonical

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "api/v1/graph-acceptance-vectors.json"
GRAPH = ROOT / "api/v1/graph.md"
ACCEPTANCE = ROOT / "api/v1/acceptance.md"
CATALOG_PATH = "api/v1/element-catalog-v1.json"
CATALOG = ROOT / CATALOG_PATH
KERNEL_CONTRACT = "helianthus.semantic.kernel/v1"

VECTOR_ID = re.compile("^G-(POS|NEG)-[A-Z]+-[0-9]+$")
ERROR_HEADING = re.compile("^### Error: `([a-z][a-z0-9_]*)`$", re.MULTILINE)
SECTION_19 = re.compile(r"^## 19\. Conformance$(.*?)^## 20\.", re.MULTILINE | re.DOTALL)
STATEMENT_ROW = re.compile(
    r"^\| ([^|]+?) \| (G-(?:POS|NEG)-[A-Z]+-[0-9]+) \| ([^|]+?) \| ([^|]+?) \|$", re.MULTILINE
)
IDENTIFIER = re.compile(r"G-(?:POS|NEG)-[A-Z]+-[0-9]+")
LEADING_OPERATION = re.compile(r"^`([a-z_]+)`")
REJECTED_ERROR = re.compile(r"^reject `([a-z_]+)`")
POLARITY = {"POS": "positive", "NEG": "negative"}

# Section 19 classes whose statements this document covers; the cut and plane classes follow later.
SLICE_CLASSES = frozenset({
    "Activation", "Duplicate identity", "Identity drift", "False join", "Missing membership",
    "Stale relation", "Dangling endpoint", "Conflict in one asset", "Identity", "Unauthorized control",
})

DIGEST = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
TEXT = {"type": "string", "minLength": 1}
TEXT_LIST = {"type": "array", "items": TEXT, "uniqueItems": True}
PACK_REF = {
    "type": "object", "required": ["id", "version"], "additionalProperties": False,
    "properties": {"id": TEXT, "version": TEXT},
}
REGISTRY = {
    "type": "object", "required": ["element_catalog", "packs"], "additionalProperties": False,
    "properties": {
        "element_catalog": {"enum": ["registered", "absent"]},
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
        "resources": {"type": "array", "items": {"type": "object"}},
        "inadmissible_operations": {"type": "array", "items": {"type": "object"}},
        "multiple_membership": {"type": "array", "items": {"type": "object"}},
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
        "record_type": {"enum": ["Registry", "ElementCatalog", "PublicationBatch", "Intent"]},
        "operation": {"enum": ["construct_registry", "register_catalog", "apply", "assemble_cut", "admit"]},
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
            "authority"]}),
        "operations": dict(TEXT_LIST, minItems=1, items={"enum": [
            "construct_registry", "register_catalog", "apply", "assemble_cut", "admit"]}),
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


def check_coverage(document: dict[str, Any], context: Context) -> list[str]:
    listed = set(document["coverage_ids"])
    found: dict[str, set[str]] = {area: set() for area in listed}
    problems = []
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


def check_definitions(document: dict[str, Any], context: Context) -> list[str]:
    entries = {ref_key(entry["ref"]): entry for entry in context.catalog["elements"]}
    packs = {ref_key(entry["ref"]["owner"]["pack"]) for entry in context.catalog["elements"]
             if entry["ref"]["owner"]["kind"] == "pack"}
    states = prior_states(document)
    problems = []
    for vector in document["vectors"]:
        problems += definition_problems(vector, entries)
        problems += declaration_problems(vector, used_refs(vector, states))
        problems += inadmissible_problems(vector, entries)
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


def section_19(graph_text: str) -> str:
    match = SECTION_19.search(graph_text)
    if match is None:
        raise ValueError("graph.md has no section 19")
    return match.group(1)


def statements(graph_text: str) -> tuple[dict[str, Statement], set[str]]:
    text = section_19(graph_text)
    rows = {}
    for klass, identifier, statement, expected in STATEMENT_ROW.findall(text):
        operation = LEADING_OPERATION.match(statement)
        error = REJECTED_ERROR.match(expected)
        rows[identifier] = Statement(klass, operation and operation.group(1), error and error.group(1))
    outside = set(IDENTIFIER.findall(STATEMENT_ROW.sub("", text)))
    return rows, outside


def required_identifiers(rows: dict[str, Statement], outside: set[str], operations: set[str]) -> set[str]:
    required = {identifier for identifier, row in rows.items()
                if row.klass in SLICE_CLASSES and row.operation in operations}
    return required | (outside - set(rows))


def statement_problems(vector: dict[str, Any], row: Statement, operations: set[str]) -> list[str]:
    problems = []
    if row.operation in operations and vector["operation"] != row.operation:
        problems.append(f"{vector['id']}: operation {vector['operation']} differs from the statement {row.operation}")
    if vector["expect"].get("error_id") != row.error_id:
        problems.append(f"{vector['id']}: expected {vector['expect'].get('error_id')} differs from the statement {row.error_id}")
    return problems


def check_statements(document: dict[str, Any], context: Context) -> list[str]:
    rows, outside = statements(context.graph_text)
    operations = set(document["operations"])
    by_id = {vector["id"]: vector for vector in document["vectors"]}
    problems = [f"{identifier}: section 19 statement has no vector"
                for identifier in sorted(required_identifiers(rows, outside, operations) - set(by_id))]
    for identifier, vector in by_id.items():
        if identifier in rows:
            problems += statement_problems(vector, rows[identifier], operations)
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


RULES = (
    ("shape", check_shape),
    ("identifiers", check_identifiers),
    ("coverage", check_coverage),
    ("errors", check_errors),
    ("definitions", check_definitions),
    ("anchor_keys", check_anchor_keys),
    ("statements", check_statements),
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
