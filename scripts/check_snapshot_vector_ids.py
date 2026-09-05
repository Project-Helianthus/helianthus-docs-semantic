#!/usr/bin/env python3
"""Independently verify content-derived snapshot/vector identities for v1."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from types import MappingProxyType


ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api" / "v1" / "acceptance-vectors.json"

def freeze(value: Any) -> Any:
    """Make the checked-in mutation contract impossible to alter while replaying."""
    if isinstance(value, dict):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    """Return a JSON-shaped copy of a frozen contract value for comparison/use."""
    if isinstance(value, MappingProxyType):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class CaseSpec:
    """The immutable public meaning of one snapshot-vector negative control."""

    base_vector: str | None
    operation: str
    record_type: str
    mutation_kind: str
    input: Any
    error_id: str
    state_unchanged: bool


# This specification is deliberately independent of acceptance-vectors.json.
# In particular, replay always takes redigest behaviour from this table, never
# from a mutable vector declaration.
EXPECTED_CASES = MappingProxyType({
    "K-NEG-056": CaseSpec(
        "K-POS-025", "select_presentation", "Selection", "policy_return",
        freeze({
            "base_vector": "K-POS-025",
            "expected_requested_envelope_candidate_ids": ["candidate:voltage:b"],
            "policy_return": {"candidate_id": "candidate:power:a"},
            "requested_key_from_base": True,
        }),
        "invalid_value", True,
    ),
    "K-NEG-057": CaseSpec(
        "K-POS-025", "select_presentation", "Selection", "replace",
        freeze({
            "base_vector": "K-POS-025",
            "mutation": {
                "path": "evaluation_view.snapshot_id",
                "replacement": "snapshot:multi:other",
            },
            "recompute_evaluation_digest": True,
        }),
        "revision_conflict", True,
    ),
    "K-NEG-058": CaseSpec(
        "K-POS-025", "select_presentation", "Selection", "replace",
        freeze({
            "base_vector": "K-POS-025",
            "mutation": {
                "path": "evaluation_view.revisions.facts",
                "replacement": "13",
            },
            "recompute_evaluation_digest": True,
        }),
        "revision_conflict", True,
    ),
    "K-NEG-059": CaseSpec(
        "K-POS-025", "select_presentation", "Selection", "replace",
        freeze({
            "base_vector": "K-POS-025",
            "digest_syntax_valid": True,
            "mutation": {
                "path": "evaluation_view.evaluation_digest",
                "replacement": "sha256:" + "0" * 64,
            },
        }),
        "digest_mismatch", True,
    ),
    "K-NEG-060": CaseSpec(
        "K-POS-025", "select_presentation", "Selection", "replace",
        freeze({
            "base_vector": "K-POS-025",
            "mutation": {
                "path": "requested_key",
                "replacement": {
                    "dimensions": [],
                    "fact_id": "helianthus.hvac.temperature",
                    "pack_id": "helianthus.pack.hvac",
                    "pack_version": "1.0.0",
                },
            },
        }),
        "dangling_reference", True,
    ),
    "K-NEG-061": CaseSpec(
        "K-POS-025", "select_presentation", "Selection", "remove_candidate",
        freeze({
            "base_vector": "K-POS-025",
            "mutation": {
                "path": "evaluation_view.facts",
                "remove_candidate_id": "candidate:voltage:b",
            },
            "recompute_evaluation_digest": True,
        }),
        "dangling_reference", True,
    ),
    "K-NEG-062": CaseSpec(
        "K-POS-025", "validate_result", "Selection", "replace_selection",
        freeze({
            "base_vector": "K-POS-025",
            "mutation": {
                "path": "selection.context.evaluate_monotonic.nanoseconds",
                "replacement": "40000000001",
            },
        }),
        "revision_conflict", True,
    ),
    "K-NEG-063": CaseSpec(
        "K-POS-025", "select_presentation", "SelectionPolicy", "policy_id",
        freeze({
            "base_vector": "K-POS-025",
            "exact_registration_absent": True,
            "policy_id": "policy.presentation.missing",
            "policy_version": "1.0.0",
        }),
        "definition_owner_missing", True,
    ),
    # This is intentionally not a replay from K-POS-025: it is the distinct
    # two-registration definition_owner_conflict control.
    "K-NEG-064": CaseSpec(
        None, "register", "SelectionPolicy", "two_registration",
        freeze({
            "policy_id": "policy.presentation.prefer_meter",
            "policy_version": "1.0.0",
            "registration_count": 2,
        }),
        "definition_owner_conflict", True,
    ),
    "K-NEG-065": CaseSpec(
        "K-POS-025", "select_presentation", "Selection", "replace_candidate_revision",
        freeze({
            "base_vector": "K-POS-025",
            "mutation": {
                "path": "evaluation_view.facts[candidate:voltage:b].candidate_revision",
                "replacement": "8",
            },
            "recompute_evaluation_digest": True,
        }),
        "revision_conflict", True,
    ),
})


def reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def canonical(value: Any) -> bytes:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    text.encode("ascii")  # These exact public fixtures intentionally use ASCII only.
    return text.encode("utf-8")


def digest_without(record: dict[str, Any], member: str) -> str:
    payload = {key: value for key, value in record.items() if key != member}
    return "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()


def at_path(root: dict[str, Any], path: str) -> tuple[Any, str]:
    current: Any = root
    parts = path.split(".")
    for part in parts[:-1]:
        current = current[part]
    return current, parts[-1]


def changed_paths(left: Any, right: Any, prefix: str = "") -> list[str]:
    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        paths: list[str] = []
        for key in sorted(set(left) | set(right)):
            child = f"{prefix}.{key}" if prefix else key
            if key not in left or key not in right:
                paths.append(child)
            else:
                paths.extend(changed_paths(left[key], right[key], child))
        return paths
    if isinstance(left, list):
        if len(left) != len(right):
            return [prefix]
        paths: list[str] = []
        for index, (a, b) in enumerate(zip(left, right)):
            paths.extend(changed_paths(a, b, f"{prefix}[{index}]"))
        return paths
    return [] if left == right else [prefix]


def expected_input(spec: CaseSpec) -> dict[str, Any]:
    return thaw(spec.input)


def require_expected_case(vector: dict[str, Any], vector_id: str, spec: CaseSpec) -> None:
    """Reject fixture drift before it can affect mutation replay."""
    if (
        vector.get("operation") != spec.operation
        or vector.get("polarity") != "negative"
        or vector.get("record_type") != spec.record_type
        or vector.get("input") != expected_input(spec)
        or vector.get("expect") != {
            "error_id": spec.error_id,
            "result": "reject",
            "state_unchanged": spec.state_unchanged,
        }
    ):
        raise ValueError(f"{vector_id}: immutable mutation specification differs")
    if spec.base_vector is None:
        if "prior_vector" in vector or "base_vector" in vector["input"]:
            raise ValueError(f"{vector_id}: registration control must not have a positive base")
    elif (
        vector.get("prior_vector") != spec.base_vector
        or vector["input"].get("base_vector") != spec.base_vector
    ):
        raise ValueError(f"{vector_id}: exact positive base is not declared")


def apply_expected_mutation(
    base: dict[str, Any], vector_id: str, spec: CaseSpec
) -> tuple[dict[str, Any], list[str]]:
    case = copy.deepcopy(base)
    inputs = expected_input(spec)
    if spec.mutation_kind == "policy_return":
        return case, []
    if spec.mutation_kind == "policy_id":
        case["policy"]["policy_id"] = inputs["policy_id"]
        return case, ["policy.policy_id"]
    mutation = inputs["mutation"]
    path = mutation["path"]
    if spec.mutation_kind == "remove_candidate":
        facts = case["evaluation_view"]["facts"]
        candidate = mutation["remove_candidate_id"]
        case["evaluation_view"]["facts"] = [fact for fact in facts if fact["candidate_id"] != candidate]
        declared = ["evaluation_view.facts"]
    elif spec.mutation_kind == "replace_candidate_revision":
        candidate = path[path.index("[") + 1:path.index("]")]
        for fact in case["evaluation_view"]["facts"]:
            if fact["candidate_id"] == candidate:
                fact["candidate_revision"] = mutation["replacement"]
                break
        else:
            raise ValueError(f"{vector_id}: mutation candidate is absent")
        declared = [f"evaluation_view.facts[{candidate}].candidate_revision"]
    else:
        parent, member = at_path(case, path)
        parent[member] = copy.deepcopy(mutation["replacement"])
        declared = [path]
    if inputs.get("recompute_evaluation_digest") is True:
        case["evaluation_view"]["evaluation_digest"] = digest_without(
            case["evaluation_view"], "evaluation_digest"
        )
        declared.append("evaluation_view.evaluation_digest")
    return case, declared


def normalized_paths(base: dict[str, Any], mutated: dict[str, Any], vector_id: str) -> list[str]:
    paths = changed_paths(base, mutated)
    if vector_id == "K-NEG-065":
        facts = base["evaluation_view"]["facts"]
        index = next(i for i, fact in enumerate(facts) if fact["candidate_id"] == "candidate:voltage:b")
        paths = [path.replace(f"facts[{index}]", "facts[candidate:voltage:b]") for path in paths]
    return paths


def paths_match(actual: list[str], declared: list[str]) -> bool:
    return all(any(path == root or path.startswith(root + ".") for root in declared) for path in actual) and all(
        any(path == root or path.startswith(root + ".") for path in actual) for root in declared
    )


def main() -> None:
    document = json.loads(VECTORS.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate)
    vectors = document["vectors"]
    by_id = {vector["id"]: vector for vector in vectors}
    if len(by_id) != len(vectors):
        raise ValueError("duplicate vector ID")
    missing = sorted(set(EXPECTED_CASES) - set(by_id))
    if missing:
        raise ValueError(f"missing snapshot negative controls: {missing}")
    for vector_id, spec in EXPECTED_CASES.items():
        require_expected_case(by_id[vector_id], vector_id, spec)

    evaluation = by_id["K-POS-019"]["input"]
    snapshot_019 = evaluation["snapshot"]
    expected_019 = digest_without(snapshot_019, "snapshot_id")
    if snapshot_019["snapshot_id"] != expected_019:
        raise ValueError("K-POS-019: snapshot_id is not content-derived")
    required_snapshot = {
        "contract", "snapshot_id", "asset_id", "revisions", "evaluated_at", "evaluate_monotonic",
        "sources", "bindings", "identity_links", "facts", "services", "capabilities", "fences", "cursors",
    }
    if not required_snapshot.issubset(snapshot_019):
        raise ValueError("K-POS-019: complete typed snapshot is not visible")
    candidates = [candidate for envelope in snapshot_019["facts"] for candidate in envelope["candidates"]]
    candidate = next((item for item in candidates if item["candidate_id"] == evaluation["candidate_id"]), None)
    if candidate is None or len(candidates) != 1 or candidate["revision"] != "4":
        raise ValueError("K-POS-019: exact candidate/revision is incomplete")
    if len(evaluation["contexts"]) != 3 or any("context" not in item for item in evaluation["contexts"]):
        raise ValueError("K-POS-019: deterministic typed contexts are incomplete")
    availability = {"fresh": "available", "stale": "degraded", "expired": "unavailable"}
    for item in evaluation["contexts"]:
        freshness = item["expected_freshness"]
        expected_view = {
            "contract": "helianthus.semantic.evaluation/v1",
            "snapshot_id": expected_019,
            "revisions": snapshot_019["revisions"],
            "context": item["context"],
            "facts": [{
                "candidate_id": candidate["candidate_id"],
                "candidate_revision": candidate["revision"],
                "freshness": freshness,
                "effective_availability": availability[freshness],
            }],
            "evaluation_digest": "",
        }
        if item.get("expected_evaluation_digest") != digest_without(expected_view, "evaluation_digest"):
            raise ValueError(f"K-POS-019: {freshness} evaluation digest differs")

    selection = by_id["K-POS-025"]
    base = selection["input"]
    snapshot_025 = base["snapshot"]
    expected_025 = digest_without(snapshot_025, "snapshot_id")
    if snapshot_025["snapshot_id"] != expected_025:
        raise ValueError("K-POS-025: snapshot_id is not content-derived")
    view = base["evaluation_view"]
    if view["snapshot_id"] != expected_025:
        raise ValueError("K-POS-025: evaluation snapshot reference differs")
    expected_view = digest_without(view, "evaluation_digest")
    if view["evaluation_digest"] != expected_view:
        raise ValueError("K-POS-025: evaluation_digest is not content-derived")
    for name in ("selection", "repeat_selection"):
        result = selection["expect"][name]
        if result["snapshot_id"] != expected_025 or result["evaluation_digest"] != expected_view:
            raise ValueError(f"K-POS-025: {name} identity binding differs")

    for vector_id, spec in EXPECTED_CASES.items():
        if spec.base_vector is None:
            continue
        vector = by_id[vector_id]
        case_base = base
        if spec.mutation_kind == "replace_selection":
            case_base = copy.deepcopy(base)
            case_base["selection"] = copy.deepcopy(selection["expect"]["selection"])
        mutated, declared = apply_expected_mutation(case_base, vector_id, spec)
        actual = normalized_paths(case_base, mutated, vector_id)
        if not paths_match(actual, declared):
            raise ValueError(f"{vector_id}: mutation differs: {actual} != {declared}")
        if spec.mutation_kind == "policy_return":
            inputs = expected_input(spec)
            selected = inputs["policy_return"]["candidate_id"]
            allowed = inputs["expected_requested_envelope_candidate_ids"]
            if selected in allowed or base["requested_key"] != base["policy_input"]["envelope_key"]:
                raise ValueError("K-NEG-056: out-of-envelope mutation is incomplete")

    print("snapshot vector identities: 2 snapshots, 4 evaluation digests, 9 dependent mutations valid")


if __name__ == "__main__":
    main()
