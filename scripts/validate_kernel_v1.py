#!/usr/bin/env python3
"""Validate structural consistency of the semantic-kernel v1 documents."""

from __future__ import annotations

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

TYPE_HEADING = re.compile(r"^### Type: ([A-Za-z][A-Za-z0-9]*)$", re.MULTILINE)
TYPE_BLOCK = re.compile(
    r"^type ([A-Za-z][A-Za-z0-9]*) struct \{\n(.*?)^\}",
    re.MULTILINE | re.DOTALL,
)
JSON_FIELD = re.compile(
    r'^\s+[A-Za-z][A-Za-z0-9]*\s+.+`json:"([a-z][a-z0-9_]*)(?:,omitempty)?"`$',
    re.MULTILINE,
)
ERROR_HEADING = re.compile(r"^### Error: `([a-z][a-z0-9_]*)`$", re.MULTILINE)
COVERAGE_HEADING = re.compile(r"^### Coverage: `([a-z][a-z0-9_]*)`$", re.MULTILINE)
VECTOR_ID = re.compile(r"^K-(POS|NEG)-[0-9]{3}$")


class DuplicateKey(ValueError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def require_unique_sorted(values: Any, label: str) -> list[str]:
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(value, str) for value in values)
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
    required = {
        "SourcePathRef": {
            "binding_id",
            "source_id",
            "source_epoch_id",
            "driver_generation",
        },
        "DerivationInput": {
            "candidate_id",
            "candidate_revision",
            "source_paths",
        },
        "EvaluationView": {
            "contract",
            "snapshot_id",
            "revisions",
            "context",
            "facts",
            "evaluation_digest",
        },
        "PackRef": {"id", "version"},
        "DefinitionRef": {"pack", "id", "version"},
        "DefinitionIndex": {
            "pack",
            "fields",
            "services",
            "capabilities",
            "operations",
            "effect_rules",
        },
        "CapabilityRequirement": {
            "pack",
            "definition_id",
            "versions",
            "instance_id",
            "allow_degraded",
        },
        "Precondition": {
            "fact",
            "candidate_id",
            "candidate_revision",
            "operator",
            "expected",
        },
        "ExpectedEffect": {"rule", "fact", "operator", "expected"},
        "Intent": {
            "contract",
            "intent_id",
            "kind",
            "expected_effect",
            "asset_id",
            "arguments",
            "required_capability",
            "authority",
            "causal",
            "expected_semantic_revision",
            "expected_capability_revision",
            "expected_capability_instance_revision",
            "expected_source_epoch_id",
            "expected_driver_generation",
            "preconditions",
            "idempotency_key",
            "deadline",
        },
        "Readback": {
            "snapshot_id",
            "revisions",
            "candidate_id",
            "candidate_revision",
            "binding_id",
            "source_id",
            "source_epoch_id",
            "driver_generation",
            "relation",
            "at",
            "evidence",
        },
        "ProjectionDisposition": {
            "kind",
            "item_id",
            "outcome",
            "source_keys",
            "loss",
            "reason",
        },
    }
    for name, fields in required.items():
        missing = fields - blocks.get(name, set())
        if missing:
            raise ValueError(f"{name} is missing required fields: {sorted(missing)}")

    required_hooks = (
        "Definitions() DefinitionIndex",
        "EvaluatePredicate(FactCandidate, PredicateOp, Value) (bool, error)",
        "ValidateIntent(Intent) error",
        "EvaluateReadback(Intent, v1.FactCandidate) (ReadbackRelation, error)",
    )
    for hook in required_hooks:
        if hook not in kernel_text:
            raise ValueError(f"required pack hook is missing: {hook}")


def require_correction_vectors(vectors: list[dict[str, Any]]) -> None:
    by_id = {vector.get("id"): vector for vector in vectors}
    required = {
        "K-POS-019": ("EvaluationView", "positive"),
        "K-POS-020": ("PublicationBatch", "positive"),
        "K-NEG-034": ("PublicationBatch", "negative"),
        "K-NEG-036": ("Readback", "negative"),
        "K-NEG-037": ("ProjectionReport", "negative"),
        "K-NEG-038": ("Intent", "negative"),
        "K-POS-021": ("PublicationBatch", "positive"),
        "K-POS-022": ("DefinitionIndex", "positive"),
        "K-NEG-039": ("Intent", "negative"),
        "K-NEG-040": ("Intent", "negative"),
        "K-NEG-041": ("ExecutionRecord", "negative"),
        "K-NEG-042": ("PublicationBatch", "negative"),
        "K-NEG-043": ("DefinitionIndex", "negative"),
        "K-NEG-044": ("Intent", "negative"),
    }
    for vector_id, (record_type, polarity) in required.items():
        vector = by_id.get(vector_id)
        if not vector or vector.get("record_type") != record_type:
            raise ValueError(f"{vector_id}: required correction vector is missing")
        if vector.get("polarity") != polarity:
            raise ValueError(f"{vector_id}: correction-vector polarity is invalid")

    evaluation_assertions = set(by_id["K-POS-019"]["expect"].get("assertions", []))
    if not {
        "fresh_stale_expired_thresholds_exact",
        "snapshot_canonical_bytes_unchanged",
        "revision_vector_unchanged",
    }.issubset(evaluation_assertions):
        raise ValueError("K-POS-019: time-only evaluation assertions are incomplete")
    contexts = by_id["K-POS-019"].get("input", {}).get("contexts", [])
    if {context.get("expected_freshness") for context in contexts} != {
        "fresh",
        "stale",
        "expired",
    }:
        raise ValueError("K-POS-019: freshness thresholds are incomplete")

    required_readback = {
        "snapshot_id",
        "revisions",
        "candidate_id",
        "candidate_revision",
        "binding_id",
        "source_id",
        "source_epoch_id",
        "driver_generation",
    }
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
    if not any(len(kinds) > 1 for kinds in ids_by_kind.values()):
        raise ValueError("K-POS-016: equal IDs across kinds are not exercised")

    derivation = by_id["K-POS-020"].get("input", {}).get("derived_candidate", {})
    sources = {
        path.get("source_id")
        for item in derivation.get("inputs", [])
        for path in item.get("source_paths", [])
    }
    if len(sources) < 2 or not derivation.get("binding_id_omitted"):
        raise ValueError("K-POS-020: multi-source derivation is incomplete")

    for vector_id in ("K-NEG-039", "K-NEG-040"):
        scenario = by_id[vector_id].get("input", {})
        precondition = scenario.get("precondition", {})
        candidates = scenario.get("envelope_candidates", [])
        if not {"candidate_id", "candidate_revision"}.issubset(precondition):
            raise ValueError(f"{vector_id}: exact precondition binding is missing")
        values = {
            json.dumps(item.get("value"), sort_keys=True) for item in candidates
        }
        if len(candidates) < 2 or len(values) < 2:
            raise ValueError(f"{vector_id}: mixed candidate evidence is incomplete")
        if len({item.get("revision") for item in candidates}) != 1:
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
        if vector_id == "K-NEG-039" and selected.get("qualification") == "qualified":
            raise ValueError("K-NEG-039: unqualified selected candidate is missing")
        if vector_id == "K-NEG-040":
            expected = json.dumps(precondition.get("expected"), sort_keys=True)
            selected_value = json.dumps(selected.get("value"), sort_keys=True)
            other_values = {
                json.dumps(item.get("value"), sort_keys=True)
                for item in candidates
                if item is not selected
            }
            if selected_value == expected or expected not in other_values:
                raise ValueError("K-NEG-040: exact-candidate negative control is invalid")

    effect = by_id["K-POS-014"].get("input", {}).get("expected_effect", {})
    if not {"rule", "fact", "operator", "expected"}.issubset(effect):
        raise ValueError("K-POS-014: typed expected effect is incomplete")
    unrelated = by_id["K-NEG-041"].get("input", {})
    if unrelated.get("expected_effect", {}).get("fact") == unrelated.get(
        "resolved_candidate", {}
    ).get("fact"):
        raise ValueError("K-NEG-041: unrelated same-route readback is missing")
    resolved = unrelated.get("resolved_candidate", {})
    if any(
        resolved.get(key) != value
        for key, value in {
            "assertion": "observed",
            "qualification": "qualified",
            "promotion": "promoted",
            "validity": "good",
            "evaluated_freshness": "fresh",
            "effective_availability": "available",
            "open_conflict": False,
        }.items()
    ):
        raise ValueError("K-NEG-041: unrelated readback is not otherwise eligible")

    transition = by_id["K-POS-021"].get("input", {})
    if not transition.get("generation_fences") or transition.get(
        "driver_generation"
    ) == transition["generation_fences"][0].get("driver_generation"):
        raise ValueError("K-POS-021: explicit higher-generation fence is missing")
    transition_assertions = set(by_id["K-POS-021"]["expect"].get("assertions", []))
    if not {
        "derived_dependents_withdrawn",
        "generation_7_callback_rejected",
        "generation_8_only_actionable",
    }.issubset(transition_assertions):
        raise ValueError("K-POS-021: atomic supersession assertions are incomplete")
    if by_id["K-NEG-042"].get("input", {}).get("generation_fences") != []:
        raise ValueError("K-NEG-042: omitted-fence negative control is missing")

    pack_dispatch = by_id["K-POS-022"].get("input", {})
    if len(pack_dispatch.get("validators_in_registration_order", [])) < 2 or not pack_dispatch.get(
        "repeat_with_registration_order_reversed"
    ):
        raise ValueError("K-POS-022: deterministic multi-pack dispatch is incomplete")
    for validator in pack_dispatch["validators_in_registration_order"]:
        if not {"pack", "fields", "services", "capabilities", "operations", "effect_rules"}.issubset(
            validator
        ):
            raise ValueError("K-POS-022: definition index collections are incomplete")
        for kind in ("fields", "services", "capabilities", "operations", "effect_rules"):
            if any(item.get("pack") != validator["pack"] for item in validator[kind]):
                raise ValueError("K-POS-022: definition owner differs from index pack")


def main() -> None:
    kernel_text = KERNEL.read_text(encoding="utf-8")
    acceptance_text = ACCEPTANCE.read_text(encoding="utf-8")
    serialization_text = SERIALIZATION.read_text(encoding="utf-8")
    data = json.loads(
        VECTORS.read_text(encoding="utf-8"), object_pairs_hook=unique_object
    )

    if data.get("contract") != "helianthus.semantic.kernel.acceptance/v1":
        raise ValueError("unexpected acceptance-vector contract")
    if data.get("kernel_contract") != "helianthus.semantic.kernel/v1":
        raise ValueError("unexpected kernel contract reference")

    error_ids = require_unique_sorted(data.get("error_ids"), "error_ids")
    coverage_ids = require_unique_sorted(data.get("coverage_ids"), "coverage_ids")
    types = heading_set(kernel_text, TYPE_HEADING, "type")
    require_type_fields(kernel_text)
    documented_errors = heading_set(acceptance_text, ERROR_HEADING, "error")
    documented_coverage = heading_set(
        acceptance_text, COVERAGE_HEADING, "coverage"
    )

    if set(error_ids) != documented_errors:
        raise ValueError("vector error_ids do not match documented error headings")
    if set(coverage_ids) != documented_coverage:
        raise ValueError("vector coverage_ids do not match documented coverage headings")

    class_map = acceptance_text.split("## Normative rejection class map", 1)
    if len(class_map) != 2:
        raise ValueError("normative rejection class map is missing")
    class_map_text = class_map[1].split("## Acceptance procedure", 1)[0]
    mapped_errors = re.findall(r"\| `([a-z][a-z0-9_]*)` \|", class_map_text)
    if set(mapped_errors) != documented_errors or len(mapped_errors) != len(
        documented_errors
    ):
        raise ValueError("rejection class map does not cover every stable error once")

    precedence_text = serialization_text.split("## Error determinism", 1)
    if len(precedence_text) != 2:
        raise ValueError("serialization error precedence section is missing")
    precedence_values = re.findall(
        r"`([a-z][a-z0-9_]*)`", precedence_text[1]
    )
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

    for index, vector in enumerate(vectors):
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
            if polarity == "positive"
            else "NEG"
            if polarity == "negative"
            else ""
        )
        if not expected_prefix or not vector_id.startswith(f"K-{expected_prefix}-"):
            raise ValueError(f"{vector_id}: polarity does not match id")

        record_type = vector.get("record_type")
        if record_type not in types:
            raise ValueError(f"{vector_id}: unknown record_type {record_type!r}")
        if not isinstance(vector.get("operation"), str) or not vector["operation"]:
            raise ValueError(f"{vector_id}: operation is required")
        if not isinstance(vector.get("criterion"), str) or not vector[
            "criterion"
        ].strip():
            raise ValueError(f"{vector_id}: criterion is required")

        input_members = [name for name in ("input", "input_json") if name in vector]
        if len(input_members) != 1:
            raise ValueError(
                f"{vector_id}: exactly one of input or input_json is required"
            )
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

        coverage = vector.get("coverage")
        if (
            not isinstance(coverage, list)
            or not coverage
            or len(coverage) != len(set(coverage))
        ):
            raise ValueError(
                f"{vector_id}: coverage must be a unique non-empty array"
            )
        unknown_coverage = set(coverage) - set(coverage_ids)
        if unknown_coverage:
            raise ValueError(
                f"{vector_id}: unknown coverage {sorted(unknown_coverage)}"
            )
        for coverage_id in coverage:
            coverage_polarities[coverage_id].add(polarity)

        prior = vector.get("prior_vector")
        if prior is not None and prior not in positive_seen:
            raise ValueError(
                f"{vector_id}: prior_vector must reference an earlier positive vector"
            )

        expect = vector.get("expect")
        if not isinstance(expect, dict):
            raise ValueError(f"{vector_id}: expect must be an object")
        if polarity == "positive":
            if expect.get("result") != "accept" or "error_id" in expect:
                raise ValueError(f"{vector_id}: positive expectation is invalid")
            positive_seen.add(vector_id)
        else:
            error_id = expect.get("error_id")
            if expect.get("result") != "reject" or error_id not in error_ids:
                raise ValueError(f"{vector_id}: negative expectation is invalid")
            if expect.get("state_unchanged") is not True:
                raise ValueError(
                    f"{vector_id}: rejection must assert unchanged state"
                )
            used_errors[error_id] += 1

    unused_errors = set(error_ids) - set(used_errors)
    if unused_errors:
        raise ValueError(
            f"errors without a negative vector: {sorted(unused_errors)}"
        )

    incomplete_coverage = {
        key: sorted({"positive", "negative"} - polarities)
        for key, polarities in coverage_polarities.items()
        if polarities != {"positive", "negative"}
    }
    missing_coverage = set(coverage_ids) - set(coverage_polarities)
    if missing_coverage or incomplete_coverage:
        raise ValueError(
            "coverage missing polarities: "
            f"missing={sorted(missing_coverage)} incomplete={incomplete_coverage}"
        )

    require_correction_vectors(vectors)

    print(
        f"kernel v1 documents consistent: {len(types)} types, "
        f"{len(error_ids)} errors, {len(coverage_ids)} coverage areas, "
        f"{len(vectors)} vectors"
    )


if __name__ == "__main__":
    main()
