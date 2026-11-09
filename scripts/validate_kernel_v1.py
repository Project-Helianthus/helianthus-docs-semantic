"""Validate structural consistency of the semantic-kernel v1 documents."""

from __future__ import annotations
import copy
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "api/v1/kernel.md"
ACCEPTANCE = ROOT / "api/v1/acceptance.md"
SERIALIZATION = ROOT / "api/v1/serialization.md"
VECTORS = ROOT / "api/v1/acceptance-vectors.json"
TYPE_HEADING = re.compile("^### Type: ([A-Za-z][A-Za-z0-9]*)$", re.MULTILINE)
TYPE_BLOCK = re.compile(
    "^type ([A-Za-z][A-Za-z0-9]*) struct \\{\\n(.*?)^\\}", re.MULTILINE | re.DOTALL
)
JSON_FIELD = re.compile(
    '^\\s+[A-Za-z][A-Za-z0-9]*\\s+.+`json:"([a-z][a-z0-9_]*)(?:,omitempty)?"`$',
    re.MULTILINE,
)
ERROR_HEADING = re.compile("^### Error: `([a-z][a-z0-9_]*)`$", re.MULTILINE)
COVERAGE_HEADING = re.compile("^### Coverage: `([a-z][a-z0-9_]*)`$", re.MULTILINE)
VECTOR_ID = re.compile("^K-(POS|NEG)-[0-9]{3}$")


class DuplicateKey(ValueError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


# Only types live here; maintained expected values live in the JSON rules file.
RULE_SCHEMAS = {
    "required-type-fields": {
        "SourceDescriptor": [
            "set",
            ["str", "str", "str", "str", "str", "str", "str", "str", "str"],
        ],
        "NativeBinding": [
            "set",
            ["str", "str", "str", "str", "str", "str", "str", "str"],
        ],
        "SourcePathRef": ["set", ["str", "str", "str", "str"]],
        "DerivationInput": ["set", ["str", "str", "str"]],
        "EvaluationView": ["set", ["str", "str", "str", "str", "str", "str", "str"]],
        "EvaluatedRetainedObservation": ["set", ["str", "str"]],
        "RetainedObservation": ["set", ["str", "str", "str"]],
        "PackRef": ["set", ["str", "str"]],
        "DefinitionRef": ["set", ["str", "str", "str"]],
        "DefinitionIndex": ["set", ["str", "str", "str", "str", "str", "str"]],
        "CapabilityRequirement": ["set", ["str", "str", "str", "str", "str"]],
        "Precondition": ["set", ["str", "str", "str", "str", "str"]],
        "ExpectedEffect": ["set", ["str", "str", "str", "str"]],
        "Selection": [
            "set",
            [
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
            ],
        ],
        "FactEnvelope": ["set", ["str", "str", "str", "str", "str"]],
        "Conflict": ["set", ["str", "str", "str", "str", "str"]],
        "DispatchEvidence": ["set", ["str", "str", "str", "str", "str", "str"]],
        "Intent": [
            "set",
            [
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
            ],
        ],
        "Readback": [
            "set",
            [
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
            ],
        ],
        "ProjectionDisposition": ["set", ["str", "str", "str", "str", "str", "str"]],
    },
    "factenvelope-must-not-persist-presentation-selection": "str",
    "forbidden-publication-metadata": ["set", ["str", "str", "str"]],
    "required-hooks": ["tuple", ["str", "str", "str", "str", "str"]],
    "selectpresentation-must-receive-complete-immutable-inputs": "str",
    "required-correction-vectors": {
        "K-POS-018": ["tuple", ["str", "str"]],
        "K-POS-019": ["tuple", ["str", "str"]],
        "K-POS-020": ["tuple", ["str", "str"]],
        "K-NEG-034": ["tuple", ["str", "str"]],
        "K-NEG-036": ["tuple", ["str", "str"]],
        "K-NEG-037": ["tuple", ["str", "str"]],
        "K-NEG-038": ["tuple", ["str", "str"]],
        "K-POS-021": ["tuple", ["str", "str"]],
        "K-POS-022": ["tuple", ["str", "str"]],
        "K-NEG-039": ["tuple", ["str", "str"]],
        "K-NEG-040": ["tuple", ["str", "str"]],
        "K-NEG-041": ["tuple", ["str", "str"]],
        "K-NEG-042": ["tuple", ["str", "str"]],
        "K-NEG-043": ["tuple", ["str", "str"]],
        "K-NEG-044": ["tuple", ["str", "str"]],
        "K-POS-023": ["tuple", ["str", "str"]],
        "K-NEG-045": ["tuple", ["str", "str"]],
        "K-NEG-046": ["tuple", ["str", "str"]],
        "K-NEG-047": ["tuple", ["str", "str"]],
        "K-NEG-048": ["tuple", ["str", "str"]],
        "K-NEG-049": ["tuple", ["str", "str"]],
        "K-NEG-050": ["tuple", ["str", "str"]],
        "K-NEG-051": ["tuple", ["str", "str"]],
        "K-POS-024": ["tuple", ["str", "str"]],
        "K-NEG-052": ["tuple", ["str", "str"]],
        "K-NEG-053": ["tuple", ["str", "str"]],
        "K-NEG-054": ["tuple", ["str", "str"]],
        "K-NEG-055": ["tuple", ["str", "str"]],
        "K-POS-025": ["tuple", ["str", "str"]],
        "K-NEG-056": ["tuple", ["str", "str"]],
        "K-NEG-057": ["tuple", ["str", "str"]],
        "K-NEG-058": ["tuple", ["str", "str"]],
        "K-NEG-059": ["tuple", ["str", "str"]],
        "K-NEG-060": ["tuple", ["str", "str"]],
        "K-NEG-061": ["tuple", ["str", "str"]],
        "K-NEG-062": ["tuple", ["str", "str"]],
        "K-NEG-063": ["tuple", ["str", "str"]],
        "K-NEG-064": ["tuple", ["str", "str"]],
        "K-NEG-065": ["tuple", ["str", "str"]],
    },
    "k-pos-019-time-only-evaluation-assertions-are-incomplete": [
        "set",
        ["str", "str", "str"],
    ],
    "k-pos-019-freshness-thresholds-are-incomplete": ["set", ["str", "str", "str"]],
    "required-readback": [
        "set",
        ["str", "str", "str", "str", "str", "str", "str", "str", "str"],
    ],
    "k-pos-016-equal-ids-across-kinds-are-not-exercised": "int",
    "k-pos-020-multi-source-derivation-is-incomplete": "int",
    "require-correction-vectors": ["tuple", ["str", "str"]],
    "exact-precondition-binding-is-missing": ["set", ["str", "str"]],
    "mixed-candidate-evidence-is-incomplete": "int",
    "mixed-candidate-evidence-is-incomplete-requirement-2": "int",
    "equal-revision-negative-control-is-missing": "int",
    "k-neg-039-unqualified-selected-candidate-is-missing": "str",
    "k-neg-039-unqualified-selected-candidate-is-missing-requirement-2": "str",
    "k-neg-040-exact-candidate-negative-control-is-invalid": "str",
    "k-pos-014-typed-expected-effect-is-incomplete": [
        "set",
        ["str", "str", "str", "str"],
    ],
    "k-neg-041-unrelated-readback-is-not-otherwise-eligible": {
        "assertion": "str",
        "qualification": "str",
        "promotion": "str",
        "validity": "str",
        "evaluated_freshness": "str",
        "effective_availability": "str",
        "open_conflict": "bool",
    },
    "k-pos-014-context-is-incomplete": ["set", ["str", "str"]],
    "k-neg-045-retained-pre-dispatch-negative-control-is-invalid": "str",
    "k-neg-046-unverifiable-freshness-control-is-incomplete": ["set", ["str", "str"]],
    "k-neg-046-unverifiable-freshness-control-is-incomplete-requirement-2": "str",
    "k-neg-046-unverifiable-freshness-control-is-incomplete-requirement-3": "str",
    "expected-partition": {
        "K-NEG-047": "str",
        "K-NEG-048": "str",
        "K-NEG-049": "str",
        "K-NEG-050": "str",
    },
    "k-neg-047-empty-identity-basis-control-is-missing": ["list", []],
    "k-neg-048-empty-capability-proof-control-is-missing": ["list", []],
    "expected-states": {
        "created_at_a": ["tuple", [["list", []], "int", ["list", ["str"]], "int"]],
        "b_ingress": [
            "tuple",
            [["list", ["str"]], "int", ["list", ["str", "str"]], "int"],
        ],
        "c_ingress": [
            "tuple",
            [["list", ["str", "str"]], "int", ["list", ["str", "str", "str"]], "int"],
        ],
    },
    "require-correction-vectors-requirement-2": [
        "tuple",
        [
            ["tuple", ["str", ["list", ["str"]], "int"]],
            ["tuple", ["str", ["list", ["str", "str"]], "int"]],
        ],
    ],
    "k-neg-051-c-to-a-reflection-control-is-invalid": "str",
    "k-neg-021-causal-domain-error-partition-is-incomplete": "str",
    "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-2": "bool",
    "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-3": "bool",
    "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-4": "int",
    "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-5": "int",
    "k-neg-052-malformed-causal-time-overlap-is-incomplete": "str",
    "k-neg-052-malformed-causal-time-overlap-is-incomplete-requirement-2": "str",
    "k-neg-052-malformed-causal-time-overlap-is-incomplete-requirement-3": "int",
    "k-neg-053-causal-append-capacity-control-is-incomplete": "str",
    "k-neg-053-causal-append-capacity-control-is-incomplete-requirement-2": "bool",
    "k-pos-024-exact-derived-conflict-is-missing": "int",
    "conflict-source": "str",
    "conflict-source-requirement-2": "str",
    "conflict-source-requirement-3": ["list", ["str", "str"]],
    "k-pos-024-kernel-owned-conflict-derivation-is-incomplete": "bool",
    "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-2": "bool",
    "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-3": [
        "list",
        ["str", "str"],
    ],
    "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-4": [
        "list",
        ["str", "str"],
    ],
    "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-5": "bool",
    "kpos024-selection-binding-valid": "str",
    "kpos024-selection-binding-valid-requirement-2": "str",
    "k-pos-024-snapshot-bound-pure-selection-is-incomplete": "bool",
    "k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-2": "str",
    "k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-3": "str",
    "k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-4": [
        "list",
        [
            {
                "candidate_id": "str",
                "candidate_revision": "str",
                "freshness": "str",
                "effective_availability": "str",
            },
            {
                "candidate_id": "str",
                "candidate_revision": "str",
                "freshness": "str",
                "effective_availability": "str",
            },
        ],
    ],
    "k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-5": "str",
    "k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-6": [
        "set",
        ["str", "str"],
    ],
    "k-pos-024-withdrawal-metadata-cleanup-is-incomplete": ["list", ["str"]],
    "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-2": [
        "list",
        ["str"],
    ],
    "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-3": ["list", []],
    "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-4": "bool",
    "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-5": "bool",
    "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-6": "bool",
    "k-neg-054-derived-conflict-mismatch-control-is-incomplete": "str",
    "k-neg-055-publisher-metadata-rejection-is-incomplete": "str",
    "k-neg-055-publisher-metadata-rejection-is-incomplete-requirement-2": "str",
    "required-snapshot-fields": [
        "set",
        [
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
        ],
    ],
    "required-candidate-fields": [
        "set",
        [
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
            "str",
        ],
    ],
    "k-pos-025-snapshot-candidate-path-is-inconsistent": "str",
    "k-pos-025-snapshot-evaluation-binding-is-incomplete": "int",
    "requested-candidates-complete": ["set", ["str", "str", "str", "str", "str"]],
    "requested-candidates-complete-requirement-2": "str",
    "k-pos-025-exact-envelope-policy-input-is-incomplete": "bool",
    "k-pos-025-deterministic-selection-result-is-incomplete": "bool",
    "k-pos-025-deterministic-selection-result-is-incomplete-requirement-2": "str",
    "k-pos-025-deterministic-selection-result-is-incomplete-requirement-3": "bool",
    "require-correction-vectors-requirement-3": [
        "tuple",
        ["str", "str", "str", "str", "str", "str", "str", "str", "str"],
    ],
    "complete-selection-base-input-is-missing": "str",
    "k-neg-056-wrong-envelope-result-control-is-incomplete": "str",
    "k-neg-056-wrong-envelope-result-control-is-incomplete-requirement-2": "str",
    "k-neg-057-snapshot-id-mismatch-control-is-incomplete": "str",
    "k-neg-057-snapshot-id-mismatch-control-is-incomplete-requirement-2": "str",
    "k-neg-057-snapshot-id-mismatch-control-is-incomplete-requirement-3": "bool",
    "k-neg-058-revision-mismatch-control-is-incomplete": "str",
    "k-neg-058-revision-mismatch-control-is-incomplete-requirement-2": "str",
    "k-neg-058-revision-mismatch-control-is-incomplete-requirement-3": "bool",
    "k-neg-059-evaluation-digest-mismatch-control-is-incomplete": "str",
    "k-neg-059-evaluation-digest-mismatch-control-is-incomplete-requirement-2": "str",
    "k-neg-059-evaluation-digest-mismatch-control-is-incomplete-requirement-3": "bool",
    "k-neg-060-absent-selection-key-control-is-incomplete": "str",
    "k-neg-060-absent-selection-key-control-is-incomplete-requirement-2": "str",
    "k-neg-061-incomplete-evaluation-view-control-is-missing": "str",
    "k-neg-061-incomplete-evaluation-view-control-is-missing-requirement-2": "str",
    "k-neg-061-incomplete-evaluation-view-control-is-missing-requirement-3": "bool",
    "k-neg-062-selection-context-mismatch-is-incomplete": "str",
    "k-neg-062-selection-context-mismatch-is-incomplete-requirement-2": "str",
    "selection-policy-ownership-controls-are-incomplete": "str",
    "selection-policy-ownership-controls-are-incomplete-requirement-2": "bool",
    "selection-policy-ownership-controls-are-incomplete-requirement-3": "str",
    "selection-policy-ownership-controls-are-incomplete-requirement-4": "int",
    "target-candidate-id": "str",
    "k-neg-065-candidate-revision-mismatch-is-incomplete": "str",
    "k-neg-065-candidate-revision-mismatch-is-incomplete-requirement-2": "str",
    "k-neg-065-candidate-revision-mismatch-is-incomplete-requirement-3": "bool",
    "k-pos-018-resolvable-retirement-tombstones-are-incomplete": {
        "source-epoch:after-restart": "str",
        "source-epoch:before-restart": "str",
    },
    "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-2": "str",
    "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-3": [
        "list",
        [],
    ],
    "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-4": "str",
    "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-5": "str",
    "k-pos-021-atomic-supersession-assertions-are-incomplete": [
        "set",
        ["str", "str", "str", "str", "str"],
    ],
    "k-neg-042-omitted-fence-negative-control-is-missing": ["list", []],
    "k-pos-021-resolvable-transition-tombstones-are-incomplete": {
        "binding:evse:01": "str",
        "binding:evse:02": "str",
    },
    "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-2": "str",
    "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-3": "str",
    "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-4": "str",
    "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-5": "str",
    "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-6": "str",
    "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-7": "str",
    "k-pos-022-deterministic-multi-pack-dispatch-is-incomplete": "int",
    "k-pos-022-definition-index-collections-are-incomplete": [
        "set",
        ["str", "str", "str", "str", "str", "str"],
    ],
    "require-correction-vectors-requirement-4": [
        "tuple",
        ["str", "str", "str", "str", "str"],
    ],
    "unexpected-acceptance-vector-contract": "str",
    "unexpected-kernel-contract-reference": "str",
    "class-map": "str",
    "class-map-text": "str",
    "precedence-text": "str",
    "expected-prefix": "str",
    "expected-prefix-requirement-2": "str",
    "input-members": ["tuple", ["str", "str"]],
    "exactly-one-of-input-or-input-json-is-required": "int",
    "positive-expectation-is-invalid": "str",
    "positive-expectation-is-invalid-requirement-2": "str",
    "positive-expectation-is-invalid-requirement-3": "str",
    "negative-expectation-is-invalid": "str",
    "rejection-must-assert-unchanged-state": "bool",
    "incomplete-coverage": ["set", ["str", "str"]],
    "incomplete-coverage-requirement-2": ["set", ["str", "str"]],
}


def decode_rule(value, schema):
    if isinstance(schema, str):
        expected = {"str": str, "int": int, "bool": bool, "NoneType": type(None)}[
            schema
        ]
        if type(value) is not expected:
            raise ValueError("malformed rule value type")
        return value
    if isinstance(schema, dict):
        if not isinstance(value, dict) or set(value) != set(schema):
            raise ValueError("malformed rule object")
        return {key: decode_rule(value[key], child) for key, child in schema.items()}
    kind, children = schema
    if not isinstance(value, list) or len(value) != len(children):
        raise ValueError("malformed rule collection")
    decoded = [decode_rule(item, child) for item, child in zip(value, children)]
    if kind == "set" and len(decoded) != len(set(decoded)):
        raise ValueError("duplicate rule set member")
    return {"list": list, "tuple": tuple, "set": set}[kind](decoded)


def load_rules(path):
    document = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique_object
    )
    if not isinstance(document, dict) or set(document) != {"contract", "rules"}:
        raise ValueError("invalid rules document fields")
    if document["contract"] != "helianthus.semantic.kernel.validation-rules/v1":
        raise ValueError("invalid rules contract")
    records = document["rules"]
    if not isinstance(records, dict) or set(records) != set(RULE_SCHEMAS):
        raise ValueError("missing or unused rules")
    return {
        name: decode_record(record, RULE_SCHEMAS[name])
        for name, record in records.items()
    }


def decode_record(record, schema):
    if not isinstance(record, dict) or set(record) != {"kind", "value"}:
        raise ValueError("invalid rule fields")
    if record["kind"] != "expected-value":
        raise ValueError("unknown rule kind")
    return decode_rule(record["value"], schema)


def rule(name):
    return copy.deepcopy(RULES[name])


RULES = load_rules(Path(__file__).with_name("kernel-validation-rules.json"))


def require_unique_sorted(values: Any, label: str) -> list[str]:
    if (
        not isinstance(values, list)
        or not values
        or (not all((isinstance(value, str) for value in values)))
    ):
        raise ValueError(f"{label} must be a non-empty string array")
    if len(values) != len(set(values)):
        raise ValueError(f"{label} contains duplicates")
    if values != sorted(values):
        raise ValueError(f"{label} is not sorted")
    return values


def heading_set(text: str, pattern: re.Pattern[str], label: str) -> set[str]:
    values = pattern.findall(text)
    if not values or len(values) != len(set(values)):
        raise ValueError(f"{label} headings are missing or duplicated")
    return set(values)


def require_type_fields(kernel_text: str) -> None:
    blocks = {
        name: set(JSON_FIELD.findall(body))
        for name, body in TYPE_BLOCK.findall(kernel_text)
    }
    required = rule("required-type-fields")
    for name, fields in required.items():
        missing = fields - blocks.get(name, set())
        if missing:
            raise ValueError(f"{name} is missing required fields: {sorted(missing)}")
    if rule("factenvelope-must-not-persist-presentation-selection") in blocks.get(
        "FactEnvelope", set()
    ):
        raise ValueError("FactEnvelope must not persist presentation selection")
    forbidden_publication_metadata = rule("forbidden-publication-metadata")
    if forbidden_publication_metadata & blocks.get("PublicationBatch", set()):
        raise ValueError("PublicationBatch must not accept envelope metadata input")
    required_hooks = rule("required-hooks")
    for hook in required_hooks:
        if hook not in kernel_text:
            raise ValueError(f"required pack hook is missing: {hook}")
    if not re.search(
        rule("selectpresentation-must-receive-complete-immutable-inputs"), kernel_text
    ):
        raise ValueError("SelectPresentation must receive complete immutable inputs")


def check_vector_id_required_correction_vector_is_missing(vectors):
    by_id = {vector.get("id"): vector for vector in vectors}
    required = rule("required-correction-vectors")
    for vector_id, (record_type, polarity) in required.items():
        vector = by_id.get(vector_id)
        if not vector or vector.get("record_type") != record_type:
            raise ValueError(f"{vector_id}: required correction vector is missing")
        if vector.get("polarity") != polarity:
            raise ValueError(f"{vector_id}: correction-vector polarity is invalid")
    evaluation_assertions = set(by_id["K-POS-019"]["expect"].get("assertions", []))
    if not rule("k-pos-019-time-only-evaluation-assertions-are-incomplete").issubset(
        evaluation_assertions
    ):
        raise ValueError("K-POS-019: time-only evaluation assertions are incomplete")
    contexts = by_id["K-POS-019"].get("input", {}).get("contexts", [])
    if {context.get("expected_freshness") for context in contexts} != rule(
        "k-pos-019-freshness-thresholds-are-incomplete"
    ):
        raise ValueError("K-POS-019: freshness thresholds are incomplete")
    required_readback = rule("required-readback")
    return (by_id, required_readback)


def check_vector_id_readback_binding_scenario_is_incomplete(by_id, required_readback):
    for vector_id, readback in (
        ("K-POS-014", by_id["K-POS-014"].get("input", {}).get("readback", {})),
        ("K-NEG-036", by_id["K-NEG-036"].get("input", {})),
        ("K-NEG-041", by_id["K-NEG-041"].get("input", {}).get("readback", {})),
    ):
        if not required_readback.issubset(readback):
            raise ValueError(f"{vector_id}: readback binding scenario is incomplete")
    projection = by_id["K-POS-016"].get("input", {})
    requested = {
        (item.get("kind"), item.get("item_id"))
        for item in projection.get("requested", [])
    }
    dispositions = {
        (item.get("kind"), item.get("item_id"))
        for item in projection.get("dispositions", [])
    }
    if requested != dispositions or len(requested) != len(
        projection.get("requested", [])
    ):
        raise ValueError("K-POS-016: projection tuple accounting is incomplete")
    ids_by_kind = defaultdict(set)
    for kind, item_id in requested:
        ids_by_kind[item_id].add(kind)
    if not any(
        (
            len(kinds) > rule("k-pos-016-equal-ids-across-kinds-are-not-exercised")
            for kinds in ids_by_kind.values()
        )
    ):
        raise ValueError("K-POS-016: equal IDs across kinds are not exercised")
    derivation = by_id["K-POS-020"].get("input", {}).get("derived_candidate", {})
    sources = {
        path.get("source_id")
        for item in derivation.get("inputs", [])
        for path in item.get("source_paths", [])
    }
    return (derivation, sources)


def check_k_pos_020_multi_source_derivation_is_incomplete(derivation, sources):
    if len(sources) < rule(
        "k-pos-020-multi-source-derivation-is-incomplete"
    ) or not derivation.get("binding_id_omitted"):
        raise ValueError("K-POS-020: multi-source derivation is incomplete")
    derivation_ids = [item.get("candidate_id") for item in derivation.get("inputs", [])]
    if derivation_ids != sorted(derivation_ids):
        raise ValueError("K-POS-020: derivation inputs are not canonical")


def check_vector_id_exact_precondition_binding_is_missing(by_id):
    for vector_id in rule("require-correction-vectors"):
        scenario = by_id[vector_id].get("input", {})
        precondition = scenario.get("precondition", {})
        candidates = scenario.get("envelope_candidates", [])
        if not rule("exact-precondition-binding-is-missing").issubset(precondition):
            raise ValueError(f"{vector_id}: exact precondition binding is missing")
        values = {json.dumps(item.get("value"), sort_keys=True) for item in candidates}
        if len(candidates) < rule("mixed-candidate-evidence-is-incomplete") or len(
            values
        ) < rule("mixed-candidate-evidence-is-incomplete-requirement-2"):
            raise ValueError(f"{vector_id}: mixed candidate evidence is incomplete")
        if len({item.get("revision") for item in candidates}) != rule(
            "equal-revision-negative-control-is-missing"
        ):
            raise ValueError(f"{vector_id}: equal revision negative control is missing")
        selected = next(
            (
                item
                for item in candidates
                if item.get("candidate_id") == precondition.get("candidate_id")
            ),
            None,
        )
        if not selected:
            raise ValueError(f"{vector_id}: selected candidate is absent")
        if vector_id == rule(
            "k-neg-039-unqualified-selected-candidate-is-missing"
        ) and selected.get("qualification") == rule(
            "k-neg-039-unqualified-selected-candidate-is-missing-requirement-2"
        ):
            raise ValueError("K-NEG-039: unqualified selected candidate is missing")
        if vector_id == rule("k-neg-040-exact-candidate-negative-control-is-invalid"):
            expected = json.dumps(precondition.get("expected"), sort_keys=True)
            selected_value = json.dumps(selected.get("value"), sort_keys=True)
            other_values = {
                json.dumps(item.get("value"), sort_keys=True)
                for item in candidates
                if item is not selected
            }
            if selected_value == expected or expected not in other_values:
                raise ValueError(
                    "K-NEG-040: exact-candidate negative control is invalid"
                )


def check_k_pos_014_typed_expected_effect_is_incomplete(by_id):
    effect = by_id["K-POS-014"].get("input", {}).get("expected_effect", {})
    if not rule("k-pos-014-typed-expected-effect-is-incomplete").issubset(effect):
        raise ValueError("K-POS-014: typed expected effect is incomplete")
    unrelated = by_id["K-NEG-041"].get("input", {})
    if unrelated.get("expected_effect", {}).get("fact") == unrelated.get(
        "resolved_candidate", {}
    ).get("fact"):
        raise ValueError("K-NEG-041: unrelated same-route readback is missing")
    resolved = unrelated.get("resolved_candidate", {})
    if any(
        (
            resolved.get(key) != value
            for key, value in rule(
                "k-neg-041-unrelated-readback-is-not-otherwise-eligible"
            ).items()
        )
    ):
        raise ValueError("K-NEG-041: unrelated readback is not otherwise eligible")
    applied = by_id["K-POS-014"].get("input", {})
    dispatch_completed = applied.get("dispatch", {}).get("completed", {})
    readback_evaluation = applied.get("readback", {}).get("evaluation", {})
    candidate = applied.get("resolved_candidate", {})
    candidate_times = candidate.get("times", {})
    for label, context in (
        ("dispatch completion", dispatch_completed),
        ("readback evaluation", readback_evaluation),
    ):
        if not rule("k-pos-014-context-is-incomplete").issubset(context):
            raise ValueError(f"K-POS-014: {label} context is incomplete")
    completed_mono = dispatch_completed["evaluate_monotonic"]
    receipt_mono = candidate_times.get("receipt_monotonic", {})
    return (applied, candidate, completed_mono, receipt_mono)


def check_k_pos_014_post_dispatch_monotonic_receipt_proof_is_missing(
    applied, by_id, candidate, completed_mono, receipt_mono
):
    if completed_mono.get("clock_epoch_id") != receipt_mono.get(
        "clock_epoch_id"
    ) or int(receipt_mono.get("nanoseconds", "-1")) <= int(
        completed_mono.get("nanoseconds", "-1")
    ):
        raise ValueError("K-POS-014: post-dispatch monotonic receipt proof is missing")
    if candidate.get("candidate_revision") == applied.get(
        "admitted_candidate_revision"
    ):
        raise ValueError("K-POS-014: post-dispatch candidate revision is unchanged")
    retained = by_id["K-NEG-045"].get("input", {})
    retained_candidate = retained.get("resolved_candidate", {})
    retained_completed = retained.get("dispatch", {}).get("completed", {})
    retained_receipt = retained_candidate.get("times", {}).get("receipt_monotonic", {})
    if (
        retained_candidate.get("candidate_revision")
        != retained.get("admitted_candidate_revision")
        or retained_receipt.get("clock_epoch_id")
        != retained_completed.get("evaluate_monotonic", {}).get("clock_epoch_id")
        or int(retained_receipt.get("nanoseconds", "0"))
        >= int(retained_completed.get("evaluate_monotonic", {}).get("nanoseconds", "0"))
        or (
            by_id["K-NEG-045"]["expect"].get("error_id")
            != rule("k-neg-045-retained-pre-dispatch-negative-control-is-invalid")
        )
    ):
        raise ValueError("K-NEG-045: retained pre-dispatch negative control is invalid")
    uncertain = by_id["K-NEG-046"].get("input", {})
    uncertain_candidate = uncertain.get("resolved_candidate", {})
    uncertain_receipt = uncertain_candidate.get("times", {}).get(
        "receipt_monotonic", {}
    )
    uncertain_evaluation = uncertain.get("readback", {}).get("evaluation", {})
    uncertainty = int(
        uncertain_evaluation.get("evaluated_at", {}).get("uncertainty_ns", "0")
    )
    max_uncertainty = int(
        uncertain_candidate.get("freshness_policy", {}).get(
            "max_wall_uncertainty_ns", "0"
        )
    )
    if (
        not rule("k-neg-046-unverifiable-freshness-control-is-incomplete").issubset(
            uncertain_evaluation
        )
        or uncertain_receipt.get("clock_epoch_id")
        == uncertain_evaluation.get("evaluate_monotonic", {}).get("clock_epoch_id")
        or uncertainty <= max_uncertainty
        or (
            uncertain.get("evaluated_freshness")
            != rule(
                "k-neg-046-unverifiable-freshness-control-is-incomplete-requirement-2"
            )
        )
        or (
            by_id["K-NEG-046"]["expect"].get("error_id")
            != rule(
                "k-neg-046-unverifiable-freshness-control-is-incomplete-requirement-3"
            )
        )
    ):
        raise ValueError("K-NEG-046: unverifiable freshness control is incomplete")
    expected_partition = rule("expected-partition")
    return (expected_partition,)


def check_vector_id_context_specific_error_is_incorrect(by_id, expected_partition):
    for vector_id, error_id in expected_partition.items():
        if by_id[vector_id]["expect"].get("error_id") != error_id:
            raise ValueError(f"{vector_id}: context-specific error is incorrect")
    if by_id["K-NEG-047"].get("input", {}).get("basis") != rule(
        "k-neg-047-empty-identity-basis-control-is-missing"
    ):
        raise ValueError("K-NEG-047: empty identity basis control is missing")
    if by_id["K-NEG-048"].get("input", {}).get("activation_evidence") != rule(
        "k-neg-048-empty-capability-proof-control-is-missing"
    ):
        raise ValueError("K-NEG-048: empty capability proof control is missing")
    if by_id["K-NEG-049"].get("input", {}).get("candidate_id") in by_id[
        "K-NEG-049"
    ].get("input", {}).get("snapshot_candidates", []):
        raise ValueError("K-NEG-049: missing precondition target control is invalid")
    revision_case = by_id["K-NEG-050"].get("input", {})
    return (revision_case,)


def check_k_neg_050_revision_changed_precondition_control_is_invalid(
    by_id, revision_case
):
    if revision_case.get("candidate_revision") == revision_case.get(
        "resolved_candidate_revision"
    ):
        raise ValueError("K-NEG-050: revision-changed precondition control is invalid")
    causal = by_id["K-POS-023"].get("input", {})
    states = {state.get("event"): state for state in causal.get("states", [])}
    expected_states = rule("expected-states")
    for event, (
        incoming_path,
        incoming_hops,
        accepted_path,
        accepted_hops,
    ) in expected_states.items():
        state = states.get(event, {})
        if (
            state.get("incoming_path") != incoming_path
            or state.get("incoming_hop_count") != incoming_hops
            or state.get("accepted_path") != accepted_path
            or (state.get("accepted_hop_count") != accepted_hops)
        ):
            raise ValueError(f"K-POS-023: {event} causal transition is invalid")
    for event, path, hops in rule("require-correction-vectors-requirement-2"):
        state = states.get(event, {})
        if state.get("emitted_path") != path or state.get("emitted_hop_count") != hops:
            raise ValueError(f"K-POS-023: {event} mutates causal context")
    reflection = by_id["K-NEG-051"].get("input", {})
    return (reflection,)


def check_k_neg_051_c_to_a_reflection_control_is_invalid(by_id, reflection):
    if (
        reflection.get("receiver") not in reflection.get("incoming_path", [])
        or reflection.get("attempted_path_after_rejection")
        != reflection.get("incoming_path")
        or by_id["K-NEG-051"]["expect"].get("error_id")
        != rule("k-neg-051-c-to-a-reflection-control-is-invalid")
    ):
        raise ValueError("K-NEG-051: C-to-A reflection control is invalid")
    hard_bound = by_id["K-NEG-021"]
    hard_input = hard_bound.get("input", {})
    if (
        hard_bound["expect"].get("error_id")
        != rule("k-neg-021-causal-domain-error-partition-is-incomplete")
        or hard_input.get("all_wire_fields_syntactically_valid")
        is not rule(
            "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-2"
        )
        or hard_input.get("causal_domain_limits_are_only_failure")
        is not rule(
            "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-3"
        )
        or (
            hard_input.get("max_hops", 0)
            <= rule(
                "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-4"
            )
        )
        or (
            int(hard_input.get("lifetime_ns", "0"))
            <= rule(
                "k-neg-021-causal-domain-error-partition-is-incomplete-requirement-5"
            )
        )
    ):
        raise ValueError("K-NEG-021: causal-domain error partition is incomplete")
    malformed_causal = by_id["K-NEG-052"]
    malformed_input = malformed_causal.get("input", {})
    if (
        malformed_causal["expect"].get("error_id")
        != rule("k-neg-052-malformed-causal-time-overlap-is-incomplete")
        or malformed_input.get("first_seen_at", {}).get("uncertainty_ns")
        != rule("k-neg-052-malformed-causal-time-overlap-is-incomplete-requirement-2")
        or malformed_input.get("max_hops", 0)
        <= rule("k-neg-052-malformed-causal-time-overlap-is-incomplete-requirement-3")
    ):
        raise ValueError("K-NEG-052: malformed causal-time overlap is incomplete")
    exhausted = by_id["K-NEG-053"]
    exhausted_input = exhausted.get("input", {})
    if (
        exhausted["expect"].get("error_id")
        != rule("k-neg-053-causal-append-capacity-control-is-incomplete")
        or exhausted_input.get("all_wire_fields_syntactically_valid")
        is not rule(
            "k-neg-053-causal-append-capacity-control-is-incomplete-requirement-2"
        )
        or exhausted_input.get("incoming_hop_count") != exhausted_input.get("max_hops")
        or (
            len(exhausted_input.get("incoming_path", []))
            != exhausted_input.get("incoming_hop_count")
        )
        or (exhausted_input.get("receiver") in exhausted_input.get("incoming_path", []))
    ):
        raise ValueError("K-NEG-053: causal append-capacity control is incomplete")
    metadata = by_id["K-POS-024"].get("input", {})
    create = metadata.get("create_conflict_batch", {})
    conflicting = metadata.get("conflicting_snapshot", {}).get("envelope", {})
    selection_view = metadata.get("presentation_evaluation_view", {})
    selection = metadata.get("presentation_selection", {})
    withdrawal = metadata.get("withdraw_one_batch", {})
    resulting = metadata.get("resulting_snapshot", {})
    result_envelope = resulting.get("envelope", {})
    prior = metadata.get("prior_snapshot_after_withdrawal", {})
    conflicts = conflicting.get("conflicts", [])
    return (
        conflicting,
        conflicts,
        create,
        metadata,
        prior,
        result_envelope,
        resulting,
        selection,
        selection_view,
        withdrawal,
    )


def check_k_pos_024_exact_derived_conflict_is_missing(
    by_id,
    conflicting,
    conflicts,
    create,
    metadata,
    prior,
    result_envelope,
    resulting,
    selection,
    selection_view,
    withdrawal,
):
    if len(conflicts) != rule("k-pos-024-exact-derived-conflict-is-missing"):
        raise ValueError("K-POS-024: exact derived conflict is missing")
    conflict = conflicts[0]
    conflict_source = {
        "contract": rule("conflict-source"),
        "asset_id": metadata.get("initial_snapshot", {}).get("asset_id"),
        "key": conflicting.get("key"),
        "kind": rule("conflict-source-requirement-2"),
        "candidates": rule("conflict-source-requirement-3"),
    }
    conflict_bytes = json.dumps(
        conflict_source, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    expected_conflict_id = "sha256:" + hashlib.sha256(conflict_bytes).hexdigest()
    selection_view_unsigned = {
        key: value
        for key, value in selection_view.items()
        if key != "evaluation_digest"
    }
    selection_view_bytes = json.dumps(
        selection_view_unsigned,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    expected_selection_digest = (
        "sha256:" + hashlib.sha256(selection_view_bytes).hexdigest()
    )
    if (
        create.get("publisher_metadata_members_present")
        is not rule("k-pos-024-kernel-owned-conflict-derivation-is-incomplete")
        or withdrawal.get("publisher_metadata_members_present")
        is not rule(
            "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-2"
        )
        or conflict.get("conflict_id") != expected_conflict_id
        or (
            conflict.get("candidates")
            != rule(
                "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-3"
            )
        )
        or (
            conflict.get("evidence")
            != rule(
                "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-4"
            )
        )
        or (
            conflicting.get("selection_member_absent")
            is not rule(
                "k-pos-024-kernel-owned-conflict-derivation-is-incomplete-requirement-5"
            )
        )
    ):
        raise ValueError("K-POS-024: kernel-owned conflict derivation is incomplete")

    def kpos024_selection_binding_valid(candidate_selection: dict[str, Any]) -> bool:
        return (
            candidate_selection.get("snapshot_id")
            == metadata.get("conflicting_snapshot", {}).get("snapshot_id")
            and candidate_selection.get("revisions")
            == metadata.get("conflicting_snapshot", {}).get("revisions")
            and (
                candidate_selection.get("evaluation_digest")
                == expected_selection_digest
            )
            and (candidate_selection.get("context") == selection_view.get("context"))
            and (
                candidate_selection.get("selected_candidate")
                == rule("kpos024-selection-binding-valid")
            )
            and (
                candidate_selection.get("candidate_revision")
                == rule("kpos024-selection-binding-valid-requirement-2")
            )
        )

    if (
        selection.get("stored_in_snapshot")
        is not rule("k-pos-024-snapshot-bound-pure-selection-is-incomplete")
        or selection.get("contract")
        != rule("k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-2")
        or selection_view.get("contract")
        != rule("k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-3")
        or (selection_view.get("snapshot_id") != selection.get("snapshot_id"))
        or (selection_view.get("revisions") != selection.get("revisions"))
        or (selection_view.get("context") != selection.get("context"))
        or (
            selection_view.get("facts")
            != rule(
                "k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-4"
            )
        )
        or (selection_view.get("evaluation_digest") != expected_selection_digest)
        or (
            rule("k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-5")
            not in by_id["K-POS-024"].get("expect", {}).get("assertions", [])
        )
        or (
            not rule(
                "k-pos-024-snapshot-bound-pure-selection-is-incomplete-requirement-6"
            ).issubset(selection.get("context", {}))
        )
        or (not kpos024_selection_binding_valid(selection))
    ):
        raise ValueError("K-POS-024: snapshot-bound pure selection is incomplete")
    mutated_selection = copy.deepcopy(selection)
    mutated_selection["evaluation_digest"] = "sha256:" + "0" * 64
    if kpos024_selection_binding_valid(mutated_selection):
        raise ValueError("K-POS-024: changed selection digest was not rejected")
    if (
        withdrawal.get("fact_withdrawals")
        != rule("k-pos-024-withdrawal-metadata-cleanup-is-incomplete")
        or result_envelope.get("candidates")
        != rule("k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-2")
        or result_envelope.get("conflicts")
        != rule("k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-3")
        or (
            result_envelope.get("selection_member_absent")
            is not rule(
                "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-4"
            )
        )
        or (
            resulting.get("old_selection_valid_for_resulting_snapshot")
            is not rule(
                "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-5"
            )
        )
        or (
            prior.get("unchanged")
            is not rule(
                "k-pos-024-withdrawal-metadata-cleanup-is-incomplete-requirement-6"
            )
        )
        or (prior.get("conflict_id") != expected_conflict_id)
    ):
        raise ValueError("K-POS-024: withdrawal metadata cleanup is incomplete")
    mismatch = by_id["K-NEG-054"]
    return (mismatch,)


def check_k_neg_054_derived_conflict_mismatch_control_is_incomplete(
    by_id, conflicting, metadata, mismatch, result_envelope, resulting
):
    if mismatch["expect"].get("error_id") != rule(
        "k-neg-054-derived-conflict-mismatch-control-is-incomplete"
    ) or mismatch.get("input", {}).get("supplied_conflict", {}).get(
        "evidence"
    ) == mismatch.get("input", {}).get("derived_evidence"):
        raise ValueError("K-NEG-054: derived conflict mismatch control is incomplete")
    publisher_metadata = by_id["K-NEG-055"]
    if publisher_metadata["expect"].get("error_id") != rule(
        "k-neg-055-publisher-metadata-rejection-is-incomplete"
    ) or rule(
        "k-neg-055-publisher-metadata-rejection-is-incomplete-requirement-2"
    ) not in publisher_metadata.get("input", {}):
        raise ValueError("K-NEG-055: publisher metadata rejection is incomplete")
    initial_revisions = metadata.get("initial_snapshot", {}).get("revisions", {})
    conflict_revisions = metadata.get("conflicting_snapshot", {}).get("revisions", {})
    result_revisions = resulting.get("revisions", {})
    if (
        int(conflict_revisions.get("semantic", "0"))
        != int(initial_revisions.get("semantic", "0")) + 1
        or int(result_revisions.get("semantic", "0"))
        != int(conflict_revisions.get("semantic", "0")) + 1
        or int(conflict_revisions.get("facts", "0"))
        != int(initial_revisions.get("facts", "0")) + 1
        or (
            int(result_revisions.get("facts", "0"))
            != int(conflict_revisions.get("facts", "0")) + 1
        )
        or (
            int(result_envelope.get("revision", "0"))
            != int(conflicting.get("revision", "0")) + 1
        )
    ):
        raise ValueError("K-POS-024: metadata revision sequence is incomplete")
    selection_case = by_id["K-POS-025"]
    selection_input = selection_case.get("input", {})
    snapshot = selection_input.get("snapshot", {})
    view = selection_input.get("evaluation_view", {})
    requested_key = selection_input.get("requested_key")
    required_snapshot_fields = rule("required-snapshot-fields")
    required_candidate_fields = rule("required-candidate-fields")
    view_without_digest = {
        key: value for key, value in view.items() if key != "evaluation_digest"
    }
    view_bytes = json.dumps(
        view_without_digest, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    expected_view_digest = "sha256:" + hashlib.sha256(view_bytes).hexdigest()
    snapshot_candidates: dict[str, tuple[str, Any]] = {}
    requested_envelope: dict[str, Any] | None = None
    bindings = {item.get("binding_id"): item for item in snapshot.get("bindings", [])}
    return (
        bindings,
        expected_view_digest,
        requested_envelope,
        requested_key,
        required_candidate_fields,
        required_snapshot_fields,
        selection_case,
        selection_input,
        snapshot,
        snapshot_candidates,
        view,
    )


def check_k_pos_025_snapshot_candidate_input_is_incomplete(
    bindings, requested_key, required_candidate_fields, snapshot, snapshot_candidates
):
    for envelope in snapshot.get("facts", []):
        key_bytes = json.dumps(envelope.get("key"), sort_keys=True)
        if envelope.get("key") == requested_key:
            requested_envelope = envelope
        for item in envelope.get("candidates", []):
            if not required_candidate_fields.issubset(item):
                raise ValueError("K-POS-025: snapshot candidate input is incomplete")
            if item.get("key") != envelope.get("key"):
                raise ValueError("K-POS-025: candidate/envelope key mismatch")
            binding = bindings.get(item.get("binding_id"), {})
            origin = item.get("origin", {})
            if (
                binding.get("state")
                != rule("k-pos-025-snapshot-candidate-path-is-inconsistent")
                or binding.get("source_epoch_id") != item.get("source_epoch_id")
                or binding.get("driver_generation") != item.get("driver_generation")
                or (origin.get("binding_id") != item.get("binding_id"))
                or (origin.get("source_epoch_id") != item.get("source_epoch_id"))
                or (origin.get("source_id") != binding.get("source_id"))
            ):
                raise ValueError("K-POS-025: snapshot candidate path is inconsistent")
            snapshot_candidates[item.get("candidate_id")] = (
                item.get("revision"),
                key_bytes,
            )
    return (requested_envelope,)


def check_k_pos_025_snapshot_evaluation_binding_is_incomplete(
    by_id,
    expected_view_digest,
    requested_envelope,
    requested_key,
    required_snapshot_fields,
    selection_case,
    selection_input,
    snapshot,
    snapshot_candidates,
    view,
):
    evaluated_candidates = {
        item.get("candidate_id"): item.get("candidate_revision")
        for item in view.get("facts", [])
    }
    evaluated_ids = [item.get("candidate_id") for item in view.get("facts", [])]
    candidate_sets_match = set(snapshot_candidates) == set(evaluated_candidates)
    candidate_revisions_match = candidate_sets_match and all(
        (
            snapshot_candidates[candidate_id][0] == revision
            for candidate_id, revision in evaluated_candidates.items()
        )
    )
    result = selection_case.get("expect", {}).get("selection", {})
    repeat_result = selection_case.get("expect", {}).get("repeat_selection", {})
    envelope_keys = [
        json.dumps(envelope.get("key"), sort_keys=True, separators=(",", ":"))
        for envelope in snapshot.get("facts", [])
    ]
    if (
        not required_snapshot_fields.issubset(snapshot)
        or snapshot.get("snapshot_id") != view.get("snapshot_id")
        or snapshot.get("revisions") != view.get("revisions")
        or (view.get("evaluation_digest") != expected_view_digest)
        or (not candidate_revisions_match)
        or (
            len(snapshot_candidates)
            != sum(
                (
                    len(envelope.get("candidates", []))
                    for envelope in snapshot.get("facts", [])
                )
            )
        )
        or (envelope_keys != sorted(envelope_keys))
        or (evaluated_ids != sorted(evaluated_ids))
        or (len(evaluated_ids) != len(set(evaluated_ids)))
        or (requested_envelope is None)
        or (
            len(snapshot.get("facts", []))
            < rule("k-pos-025-snapshot-evaluation-binding-is-incomplete")
        )
    ):
        raise ValueError("K-POS-025: snapshot/evaluation binding is incomplete")
    requested_ids = [
        item.get("candidate_id") for item in requested_envelope.get("candidates", [])
    ]
    requested_candidates_complete = (
        all(
            (
                rule("requested-candidates-complete").issubset(item)
                for item in requested_envelope.get("candidates", [])
            )
        )
        and rule("requested-candidates-complete-requirement-2") in requested_envelope
    )
    policy_input = selection_input.get("policy_input", {})
    if (
        policy_input.get("envelope_key") != requested_key
        or policy_input.get("candidate_ids") != requested_ids
        or policy_input.get("evaluated_fact_ids") != requested_ids
        or (
            selection_input.get("policy", {}).get("registered_once")
            is not rule("k-pos-025-exact-envelope-policy-input-is-incomplete")
        )
        or (not requested_candidates_complete)
    ):
        raise ValueError("K-POS-025: exact envelope policy input is incomplete")
    if (
        result != repeat_result
        or selection_input.get("repeat_identical_call")
        is not rule("k-pos-025-deterministic-selection-result-is-incomplete")
        or result.get("contract")
        != rule("k-pos-025-deterministic-selection-result-is-incomplete-requirement-2")
        or (result.get("snapshot_id") != snapshot.get("snapshot_id"))
        or (result.get("revisions") != snapshot.get("revisions"))
        or (result.get("evaluation_digest") != view.get("evaluation_digest"))
        or (result.get("context") != view.get("context"))
        or (result.get("key") != requested_key)
        or (
            result.get("policy_id")
            != selection_input.get("policy", {}).get("policy_id")
        )
        or (
            result.get("policy_version")
            != selection_input.get("policy", {}).get("policy_version")
        )
        or (result.get("selected_candidate") not in requested_ids)
        or (
            result.get("candidate_revision")
            != evaluated_candidates.get(result.get("selected_candidate"))
        )
        or (
            result.get("presentation_only")
            is not rule(
                "k-pos-025-deterministic-selection-result-is-incomplete-requirement-3"
            )
        )
    ):
        raise ValueError("K-POS-025: deterministic selection result is incomplete")
    for vector_id in rule("require-correction-vectors-requirement-3"):
        if by_id[vector_id].get("input", {}).get("base_vector") != rule(
            "complete-selection-base-input-is-missing"
        ):
            raise ValueError(f"{vector_id}: complete selection base input is missing")
    wrong_envelope = by_id["K-NEG-056"]
    wrong_input = wrong_envelope.get("input", {})
    return (requested_ids, result, wrong_envelope, wrong_input)


def check_k_neg_056_wrong_envelope_result_control_is_incomplete(
    by_id, requested_ids, selection_input, wrong_envelope, wrong_input
):
    if (
        wrong_envelope["expect"].get("error_id")
        != rule("k-neg-056-wrong-envelope-result-control-is-incomplete")
        or wrong_input.get("base_vector")
        != rule("k-neg-056-wrong-envelope-result-control-is-incomplete-requirement-2")
        or wrong_input.get("policy_return", {}).get("candidate_id")
        in wrong_input.get("expected_requested_envelope_candidate_ids", [])
        or (
            wrong_input.get("expected_requested_envelope_candidate_ids")
            != requested_ids
        )
    ):
        raise ValueError("K-NEG-056: wrong-envelope result control is incomplete")

    def recompute_view_digest(candidate_view: dict[str, Any]) -> str:
        unsigned = {
            key: value
            for key, value in candidate_view.items()
            if key != "evaluation_digest"
        }
        encoded = json.dumps(
            unsigned, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    mismatch_ids = by_id["K-NEG-057"]
    mismatch_ids_input = mismatch_ids.get("input", {})
    mismatch_ids_case = copy.deepcopy(selection_input)
    mismatch_ids_case["evaluation_view"]["snapshot_id"] = mismatch_ids_input[
        "mutation"
    ]["replacement"]
    mismatch_ids_case["evaluation_view"]["evaluation_digest"] = recompute_view_digest(
        mismatch_ids_case["evaluation_view"]
    )
    if (
        mismatch_ids["expect"].get("error_id")
        != rule("k-neg-057-snapshot-id-mismatch-control-is-incomplete")
        or mismatch_ids_input.get("mutation", {}).get("path")
        != rule("k-neg-057-snapshot-id-mismatch-control-is-incomplete-requirement-2")
        or mismatch_ids_input.get("recompute_evaluation_digest")
        is not rule(
            "k-neg-057-snapshot-id-mismatch-control-is-incomplete-requirement-3"
        )
        or (
            mismatch_ids_case["snapshot"]["snapshot_id"]
            == mismatch_ids_case["evaluation_view"]["snapshot_id"]
        )
        or (
            mismatch_ids_case["evaluation_view"]["evaluation_digest"]
            != recompute_view_digest(mismatch_ids_case["evaluation_view"])
        )
    ):
        raise ValueError("K-NEG-057: snapshot ID mismatch control is incomplete")
    mismatch_revisions = by_id["K-NEG-058"]
    mismatch_revisions_input = mismatch_revisions.get("input", {})
    mismatch_revisions_case = copy.deepcopy(selection_input)
    mismatch_revisions_case["evaluation_view"]["revisions"]["facts"] = (
        mismatch_revisions_input["mutation"]["replacement"]
    )
    mismatch_revisions_case["evaluation_view"]["evaluation_digest"] = (
        recompute_view_digest(mismatch_revisions_case["evaluation_view"])
    )
    if (
        mismatch_revisions["expect"].get("error_id")
        != rule("k-neg-058-revision-mismatch-control-is-incomplete")
        or mismatch_revisions_input.get("mutation", {}).get("path")
        != rule("k-neg-058-revision-mismatch-control-is-incomplete-requirement-2")
        or mismatch_revisions_input.get("recompute_evaluation_digest")
        is not rule("k-neg-058-revision-mismatch-control-is-incomplete-requirement-3")
        or (
            mismatch_revisions_case["snapshot"]["revisions"]
            == mismatch_revisions_case["evaluation_view"]["revisions"]
        )
        or (
            mismatch_revisions_case["evaluation_view"]["evaluation_digest"]
            != recompute_view_digest(mismatch_revisions_case["evaluation_view"])
        )
    ):
        raise ValueError("K-NEG-058: revision mismatch control is incomplete")
    bad_digest = by_id["K-NEG-059"]
    bad_digest_input = bad_digest.get("input", {})
    bad_digest_case = copy.deepcopy(selection_input)
    bad_digest_case["evaluation_view"]["evaluation_digest"] = bad_digest_input[
        "mutation"
    ]["replacement"]
    return (bad_digest, bad_digest_case, bad_digest_input, recompute_view_digest)


def check_k_neg_059_evaluation_digest_mismatch_control_is_incomplete(
    bad_digest,
    bad_digest_case,
    bad_digest_input,
    by_id,
    recompute_view_digest,
    result,
    selection_input,
    snapshot,
    snapshot_candidates,
    view,
):
    if (
        bad_digest["expect"].get("error_id")
        != rule("k-neg-059-evaluation-digest-mismatch-control-is-incomplete")
        or bad_digest_input.get("mutation", {}).get("path")
        != rule(
            "k-neg-059-evaluation-digest-mismatch-control-is-incomplete-requirement-2"
        )
        or bad_digest_input.get("digest_syntax_valid")
        is not rule(
            "k-neg-059-evaluation-digest-mismatch-control-is-incomplete-requirement-3"
        )
        or (
            bad_digest_case["evaluation_view"]["evaluation_digest"]
            == recompute_view_digest(bad_digest_case["evaluation_view"])
        )
    ):
        raise ValueError("K-NEG-059: evaluation digest mismatch control is incomplete")
    missing_key = by_id["K-NEG-060"]
    missing_key_input = missing_key.get("input", {})
    missing_key_case = copy.deepcopy(selection_input)
    missing_key_case["requested_key"] = missing_key_input["mutation"]["replacement"]
    if (
        missing_key["expect"].get("error_id")
        != rule("k-neg-060-absent-selection-key-control-is-incomplete")
        or missing_key_input.get("mutation", {}).get("path")
        != rule("k-neg-060-absent-selection-key-control-is-incomplete-requirement-2")
        or missing_key_case["requested_key"]
        in [envelope.get("key") for envelope in snapshot.get("facts", [])]
    ):
        raise ValueError("K-NEG-060: absent selection key control is incomplete")
    missing_candidate = by_id["K-NEG-061"]
    missing_candidate_input = missing_candidate.get("input", {})
    missing_candidate_case = copy.deepcopy(selection_input)
    removed_candidate_id = missing_candidate_input.get("mutation", {}).get(
        "remove_candidate_id"
    )
    missing_candidate_case["evaluation_view"]["facts"] = [
        item
        for item in missing_candidate_case["evaluation_view"]["facts"]
        if item.get("candidate_id") != removed_candidate_id
    ]
    missing_candidate_case["evaluation_view"]["evaluation_digest"] = (
        recompute_view_digest(missing_candidate_case["evaluation_view"])
    )
    if (
        missing_candidate["expect"].get("error_id")
        != rule("k-neg-061-incomplete-evaluation-view-control-is-missing")
        or missing_candidate_input.get("mutation", {}).get("path")
        != rule("k-neg-061-incomplete-evaluation-view-control-is-missing-requirement-2")
        or missing_candidate_input.get("recompute_evaluation_digest")
        is not rule(
            "k-neg-061-incomplete-evaluation-view-control-is-missing-requirement-3"
        )
        or (removed_candidate_id not in snapshot_candidates)
        or (
            removed_candidate_id
            in {
                item.get("candidate_id")
                for item in missing_candidate_case["evaluation_view"]["facts"]
            }
        )
        or (
            missing_candidate_case["evaluation_view"]["evaluation_digest"]
            != recompute_view_digest(missing_candidate_case["evaluation_view"])
        )
    ):
        raise ValueError("K-NEG-061: incomplete evaluation view control is missing")
    mismatch_context = by_id["K-NEG-062"]
    mismatch_context_input = mismatch_context.get("input", {})
    mismatch_context_result = copy.deepcopy(result)
    mismatch_context_result["context"]["evaluate_monotonic"]["nanoseconds"] = (
        mismatch_context_input["mutation"]["replacement"]
    )
    if (
        mismatch_context["expect"].get("error_id")
        != rule("k-neg-062-selection-context-mismatch-is-incomplete")
        or mismatch_context_input.get("mutation", {}).get("path")
        != rule("k-neg-062-selection-context-mismatch-is-incomplete-requirement-2")
        or mismatch_context_result.get("context") == view.get("context")
    ):
        raise ValueError("K-NEG-062: selection context mismatch is incomplete")
    missing_policy = by_id["K-NEG-063"]
    duplicate_policy = by_id["K-NEG-064"]
    return (duplicate_policy, missing_policy)


def check_selection_policy_ownership_controls_are_incomplete(
    by_id,
    duplicate_policy,
    missing_policy,
    recompute_view_digest,
    selection_input,
    snapshot_candidates,
):
    if (
        missing_policy["expect"].get("error_id")
        != rule("selection-policy-ownership-controls-are-incomplete")
        or missing_policy.get("input", {}).get("exact_registration_absent")
        is not rule("selection-policy-ownership-controls-are-incomplete-requirement-2")
        or duplicate_policy["expect"].get("error_id")
        != rule("selection-policy-ownership-controls-are-incomplete-requirement-3")
        or (
            duplicate_policy.get("input", {}).get("registration_count")
            != rule("selection-policy-ownership-controls-are-incomplete-requirement-4")
        )
    ):
        raise ValueError("selection-policy ownership controls are incomplete")
    mismatched_candidate_revision = by_id["K-NEG-065"]
    mismatched_candidate_input = mismatched_candidate_revision.get("input", {})
    mismatched_candidate_case = copy.deepcopy(selection_input)
    target_candidate_id = rule("target-candidate-id")
    target_fact = next(
        (
            item
            for item in mismatched_candidate_case["evaluation_view"]["facts"]
            if item.get("candidate_id") == target_candidate_id
        )
    )
    target_fact["candidate_revision"] = mismatched_candidate_input["mutation"][
        "replacement"
    ]
    mismatched_candidate_case["evaluation_view"]["evaluation_digest"] = (
        recompute_view_digest(mismatched_candidate_case["evaluation_view"])
    )
    if (
        mismatched_candidate_revision["expect"].get("error_id")
        != rule("k-neg-065-candidate-revision-mismatch-is-incomplete")
        or mismatched_candidate_input.get("mutation", {}).get("path")
        != rule("k-neg-065-candidate-revision-mismatch-is-incomplete-requirement-2")
        or mismatched_candidate_input.get("recompute_evaluation_digest")
        is not rule("k-neg-065-candidate-revision-mismatch-is-incomplete-requirement-3")
        or (
            target_fact.get("candidate_revision")
            == snapshot_candidates[target_candidate_id][0]
        )
        or (
            mismatched_candidate_case["evaluation_view"]["evaluation_digest"]
            != recompute_view_digest(mismatched_candidate_case["evaluation_view"])
        )
    ):
        raise ValueError("K-NEG-065: candidate revision mismatch is incomplete")
    restart_snapshot = by_id["K-POS-018"].get("input", {}).get("resulting_snapshot", {})
    source_states = {
        item.get("source_epoch_id"): item.get("state")
        for item in restart_snapshot.get("sources", [])
    }
    retired_binding_states = {
        item.get("binding_id"): item.get("state")
        for item in restart_snapshot.get("bindings", [])
    }
    if (
        source_states
        != rule("k-pos-018-resolvable-retirement-tombstones-are-incomplete")
        or retired_binding_states.get("binding:pv:old")
        != rule(
            "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-2"
        )
        or restart_snapshot.get("old_epoch_candidates")
        != rule(
            "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-3"
        )
        or (
            restart_snapshot.get("full_snapshot_validation")
            != rule(
                "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-4"
            )
        )
        or (
            restart_snapshot.get("canonical_serialization")
            != rule(
                "k-pos-018-resolvable-retirement-tombstones-are-incomplete-requirement-5"
            )
        )
    ):
        raise ValueError("K-POS-018: resolvable retirement tombstones are incomplete")
    transition = by_id["K-POS-021"].get("input", {})
    if not transition.get("generation_fences") or transition.get(
        "driver_generation"
    ) == transition["generation_fences"][0].get("driver_generation"):
        raise ValueError("K-POS-021: explicit higher-generation fence is missing")
    transition_assertions = set(by_id["K-POS-021"]["expect"].get("assertions", []))
    if not rule("k-pos-021-atomic-supersession-assertions-are-incomplete").issubset(
        transition_assertions
    ):
        raise ValueError("K-POS-021: atomic supersession assertions are incomplete")
    return (transition,)


def check_k_neg_042_omitted_fence_negative_control_is_missing(by_id, transition):
    if by_id["K-NEG-042"].get("input", {}).get("generation_fences") != rule(
        "k-neg-042-omitted-fence-negative-control-is-missing"
    ):
        raise ValueError("K-NEG-042: omitted-fence negative control is missing")
    resulting_snapshot = transition.get("resulting_snapshot", {})
    binding_states = {
        item.get("binding_id"): item.get("state")
        for item in resulting_snapshot.get("bindings", [])
    }
    service_states = {
        item.get("instance_id"): item.get("availability")
        for item in resulting_snapshot.get("services", [])
    }
    capability_states = {
        item.get("instance_id"): item.get("availability")
        for item in resulting_snapshot.get("capabilities", [])
    }
    if (
        binding_states
        != rule("k-pos-021-resolvable-transition-tombstones-are-incomplete")
        or service_states.get("service:evse:01")
        != rule(
            "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-2"
        )
        or capability_states.get("capability:limit:01")
        != rule(
            "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-3"
        )
        or (
            service_states.get("service:evse:02")
            != rule(
                "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-4"
            )
        )
        or (
            capability_states.get("capability:limit:02")
            != rule(
                "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-5"
            )
        )
        or (
            resulting_snapshot.get("full_snapshot_validation")
            != rule(
                "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-6"
            )
        )
        or (
            resulting_snapshot.get("canonical_serialization")
            != rule(
                "k-pos-021-resolvable-transition-tombstones-are-incomplete-requirement-7"
            )
        )
    ):
        raise ValueError("K-POS-021: resolvable transition tombstones are incomplete")
    pack_dispatch = by_id["K-POS-022"].get("input", {})
    if len(pack_dispatch.get("validators_in_registration_order", [])) < rule(
        "k-pos-022-deterministic-multi-pack-dispatch-is-incomplete"
    ) or not pack_dispatch.get("repeat_with_registration_order_reversed"):
        raise ValueError("K-POS-022: deterministic multi-pack dispatch is incomplete")
    return (pack_dispatch,)


def check_k_pos_022_definition_index_collections_are_incomplete(pack_dispatch):
    for validator in pack_dispatch["validators_in_registration_order"]:
        if not rule("k-pos-022-definition-index-collections-are-incomplete").issubset(
            validator
        ):
            raise ValueError("K-POS-022: definition index collections are incomplete")
        for kind in rule("require-correction-vectors-requirement-4"):
            if any((item.get("pack") != validator["pack"] for item in validator[kind])):
                raise ValueError("K-POS-022: definition owner differs from index pack")


def require_correction_vectors(vectors: list[dict[str, Any]]) -> None:
    by_id, required_readback = check_vector_id_required_correction_vector_is_missing(
        vectors
    )
    derivation, sources = check_vector_id_readback_binding_scenario_is_incomplete(
        by_id, required_readback
    )
    check_k_pos_020_multi_source_derivation_is_incomplete(derivation, sources)
    check_vector_id_exact_precondition_binding_is_missing(by_id)
    applied, candidate, completed_mono, receipt_mono = (
        check_k_pos_014_typed_expected_effect_is_incomplete(by_id)
    )
    (expected_partition,) = (
        check_k_pos_014_post_dispatch_monotonic_receipt_proof_is_missing(
            applied, by_id, candidate, completed_mono, receipt_mono
        )
    )
    (revision_case,) = check_vector_id_context_specific_error_is_incorrect(
        by_id, expected_partition
    )
    (reflection,) = check_k_neg_050_revision_changed_precondition_control_is_invalid(
        by_id, revision_case
    )
    (
        conflicting,
        conflicts,
        create,
        metadata,
        prior,
        result_envelope,
        resulting,
        selection,
        selection_view,
        withdrawal,
    ) = check_k_neg_051_c_to_a_reflection_control_is_invalid(by_id, reflection)
    (mismatch,) = check_k_pos_024_exact_derived_conflict_is_missing(
        by_id,
        conflicting,
        conflicts,
        create,
        metadata,
        prior,
        result_envelope,
        resulting,
        selection,
        selection_view,
        withdrawal,
    )
    (
        bindings,
        expected_view_digest,
        requested_envelope,
        requested_key,
        required_candidate_fields,
        required_snapshot_fields,
        selection_case,
        selection_input,
        snapshot,
        snapshot_candidates,
        view,
    ) = check_k_neg_054_derived_conflict_mismatch_control_is_incomplete(
        by_id, conflicting, metadata, mismatch, result_envelope, resulting
    )
    (requested_envelope,) = check_k_pos_025_snapshot_candidate_input_is_incomplete(
        bindings,
        requested_key,
        required_candidate_fields,
        snapshot,
        snapshot_candidates,
    )
    requested_ids, result, wrong_envelope, wrong_input = (
        check_k_pos_025_snapshot_evaluation_binding_is_incomplete(
            by_id,
            expected_view_digest,
            requested_envelope,
            requested_key,
            required_snapshot_fields,
            selection_case,
            selection_input,
            snapshot,
            snapshot_candidates,
            view,
        )
    )
    bad_digest, bad_digest_case, bad_digest_input, recompute_view_digest = (
        check_k_neg_056_wrong_envelope_result_control_is_incomplete(
            by_id, requested_ids, selection_input, wrong_envelope, wrong_input
        )
    )
    duplicate_policy, missing_policy = (
        check_k_neg_059_evaluation_digest_mismatch_control_is_incomplete(
            bad_digest,
            bad_digest_case,
            bad_digest_input,
            by_id,
            recompute_view_digest,
            result,
            selection_input,
            snapshot,
            snapshot_candidates,
            view,
        )
    )
    (transition,) = check_selection_policy_ownership_controls_are_incomplete(
        by_id,
        duplicate_policy,
        missing_policy,
        recompute_view_digest,
        selection_input,
        snapshot_candidates,
    )
    (pack_dispatch,) = check_k_neg_042_omitted_fence_negative_control_is_missing(
        by_id, transition
    )
    check_k_pos_022_definition_index_collections_are_incomplete(pack_dispatch)


def check_unexpected_acceptance_vector_contract():
    kernel_text = KERNEL.read_text(encoding="utf-8")
    acceptance_text = ACCEPTANCE.read_text(encoding="utf-8")
    serialization_text = SERIALIZATION.read_text(encoding="utf-8")
    data = json.loads(
        VECTORS.read_text(encoding="utf-8"), object_pairs_hook=unique_object
    )
    if data.get("contract") != rule("unexpected-acceptance-vector-contract"):
        raise ValueError("unexpected acceptance-vector contract")
    if data.get("kernel_contract") != rule("unexpected-kernel-contract-reference"):
        raise ValueError("unexpected kernel contract reference")
    error_ids = require_unique_sorted(data.get("error_ids"), "error_ids")
    coverage_ids = require_unique_sorted(data.get("coverage_ids"), "coverage_ids")
    types = heading_set(kernel_text, TYPE_HEADING, "type")
    require_type_fields(kernel_text)
    documented_errors = heading_set(acceptance_text, ERROR_HEADING, "error")
    documented_coverage = heading_set(acceptance_text, COVERAGE_HEADING, "coverage")
    if set(error_ids) != documented_errors:
        raise ValueError("vector error_ids do not match documented error headings")
    if set(coverage_ids) != documented_coverage:
        raise ValueError(
            "vector coverage_ids do not match documented coverage headings"
        )
    class_map = acceptance_text.split(rule("class-map"), 1)
    if len(class_map) != 2:
        raise ValueError("normative rejection class map is missing")
    class_map_text = class_map[1].split(rule("class-map-text"), 1)[0]
    mapped_errors = re.findall("\\| `([a-z][a-z0-9_]*)` \\|", class_map_text)
    return (
        coverage_ids,
        data,
        documented_errors,
        error_ids,
        mapped_errors,
        serialization_text,
        types,
    )


def check_rejection_class_map_does_not_cover_every_stable_error_once(
    data, documented_errors, mapped_errors, serialization_text
):
    if set(mapped_errors) != documented_errors or len(mapped_errors) != len(
        documented_errors
    ):
        raise ValueError("rejection class map does not cover every stable error once")
    precedence_text = serialization_text.split(rule("precedence-text"), 1)
    if len(precedence_text) != 2:
        raise ValueError("serialization error precedence section is missing")
    precedence_values = re.findall("`([a-z][a-z0-9_]*)`", precedence_text[1])
    precedence_ids = set(precedence_values)
    if precedence_ids != documented_errors or len(precedence_values) != len(
        precedence_ids
    ):
        raise ValueError("error precedence does not list every stable error exactly")
    vectors = data.get("vectors")
    if not isinstance(vectors, list) or not vectors:
        raise ValueError("vectors must be a non-empty array")
    seen: set[str] = set()
    positive_seen: set[str] = set()
    used_errors: Counter[str] = Counter()
    coverage_polarities: dict[str, set[str]] = defaultdict(set)
    return (coverage_polarities, positive_seen, seen, used_errors, vectors)


def check_vector_index_is_not_an_object(
    coverage_ids,
    coverage_polarities,
    error_ids,
    positive_seen,
    seen,
    types,
    used_errors,
    vectors,
):
    for index, vector in enumerate(vectors):
        polarity, vector_id = check_vector_identity(index, seen, types, vector)
        check_vector_input(vector, vector_id)
        check_vector_coverage(
            coverage_ids, coverage_polarities, polarity, vector, vector_id
        )
        check_vector_prior(positive_seen, vector, vector_id)
        check_vector_expectation(
            error_ids, polarity, positive_seen, used_errors, vector, vector_id
        )


def check_errors_without_a_negative_vector_sorted_unused_errors(
    coverage_ids, coverage_polarities, error_ids, types, used_errors, vectors
):
    unused_errors = set(error_ids) - set(used_errors)
    if unused_errors:
        raise ValueError(f"errors without a negative vector: {sorted(unused_errors)}")
    incomplete_coverage = {
        key: sorted(rule("incomplete-coverage") - polarities)
        for key, polarities in coverage_polarities.items()
        if polarities != rule("incomplete-coverage-requirement-2")
    }
    missing_coverage = set(coverage_ids) - set(coverage_polarities)
    if missing_coverage or incomplete_coverage:
        raise ValueError(
            f"coverage missing polarities: missing={sorted(missing_coverage)} incomplete={incomplete_coverage}"
        )
    require_correction_vectors(vectors)
    print(
        f"kernel v1 documents consistent: {len(types)} types, {len(error_ids)} errors, {len(coverage_ids)} coverage areas, {len(vectors)} vectors"
    )


def main() -> None:
    (
        coverage_ids,
        data,
        documented_errors,
        error_ids,
        mapped_errors,
        serialization_text,
        types,
    ) = check_unexpected_acceptance_vector_contract()
    coverage_polarities, positive_seen, seen, used_errors, vectors = (
        check_rejection_class_map_does_not_cover_every_stable_error_once(
            data, documented_errors, mapped_errors, serialization_text
        )
    )
    check_vector_index_is_not_an_object(
        coverage_ids,
        coverage_polarities,
        error_ids,
        positive_seen,
        seen,
        types,
        used_errors,
        vectors,
    )
    check_errors_without_a_negative_vector_sorted_unused_errors(
        coverage_ids, coverage_polarities, error_ids, types, used_errors, vectors
    )


def check_vector_identity(index, seen, types, vector):
    if not isinstance(vector, dict):
        raise ValueError(f"vector {index} is not an object")
    vector_id = vector.get("id")
    if not isinstance(vector_id, str) or not VECTOR_ID.fullmatch(vector_id):
        raise ValueError(f"vector {index} has invalid id")
    if vector_id in seen:
        raise ValueError(f"duplicate vector id: {vector_id}")
    seen.add(vector_id)
    polarity = vector.get("polarity")
    expected_prefix = (
        "POS"
        if polarity == rule("expected-prefix")
        else "NEG"
        if polarity == rule("expected-prefix-requirement-2")
        else ""
    )
    if not expected_prefix or not vector_id.startswith(f"K-{expected_prefix}-"):
        raise ValueError(f"{vector_id}: polarity does not match id")
    record_type = vector.get("record_type")
    if record_type not in types:
        raise ValueError(f"{vector_id}: unknown record_type {record_type!r}")
    if not isinstance(vector.get("operation"), str) or not vector["operation"]:
        raise ValueError(f"{vector_id}: operation is required")
    if not isinstance(vector.get("criterion"), str) or not vector["criterion"].strip():
        raise ValueError(f"{vector_id}: criterion is required")
    return (polarity, vector_id)


def check_vector_input(vector, vector_id):
    input_members = [name for name in rule("input-members") if name in vector]
    if len(input_members) != rule("exactly-one-of-input-or-input-json-is-required"):
        raise ValueError(f"{vector_id}: exactly one of input or input_json is required")
    if "input_json" in vector:
        if not isinstance(vector["input_json"], str):
            raise ValueError(f"{vector_id}: input_json must be a string")
        try:
            json.loads(vector["input_json"], object_pairs_hook=unique_object)
        except (json.JSONDecodeError, DuplicateKey):
            pass
        else:
            raise ValueError(
                f"{vector_id}: input_json must demonstrate invalid JSON structure"
            )


def check_vector_coverage(
    coverage_ids, coverage_polarities, polarity, vector, vector_id
):
    coverage = vector.get("coverage")
    if (
        not isinstance(coverage, list)
        or not coverage
        or len(coverage) != len(set(coverage))
    ):
        raise ValueError(f"{vector_id}: coverage must be a unique non-empty array")
    unknown_coverage = set(coverage) - set(coverage_ids)
    if unknown_coverage:
        raise ValueError(f"{vector_id}: unknown coverage {sorted(unknown_coverage)}")
    for coverage_id in coverage:
        coverage_polarities[coverage_id].add(polarity)


def check_vector_prior(positive_seen, vector, vector_id):
    prior = vector.get("prior_vector")
    if prior is not None and prior not in positive_seen:
        raise ValueError(
            f"{vector_id}: prior_vector must reference an earlier positive vector"
        )


def check_vector_expectation(
    error_ids, polarity, positive_seen, used_errors, vector, vector_id
):
    expect = vector.get("expect")
    if not isinstance(expect, dict):
        raise ValueError(f"{vector_id}: expect must be an object")
    if polarity == rule("positive-expectation-is-invalid"):
        if (
            expect.get("result")
            != rule("positive-expectation-is-invalid-requirement-2")
            or rule("positive-expectation-is-invalid-requirement-3") in expect
        ):
            raise ValueError(f"{vector_id}: positive expectation is invalid")
        positive_seen.add(vector_id)
    else:
        error_id = expect.get("error_id")
        if (
            expect.get("result") != rule("negative-expectation-is-invalid")
            or error_id not in error_ids
        ):
            raise ValueError(f"{vector_id}: negative expectation is invalid")
        if expect.get("state_unchanged") is not rule(
            "rejection-must-assert-unchanged-state"
        ):
            raise ValueError(f"{vector_id}: rejection must assert unchanged state")
        used_errors[error_id] += 1


if __name__ == "__main__":
    main()
