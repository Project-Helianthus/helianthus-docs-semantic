#!/usr/bin/env python3
"""Independently verify content-derived snapshot/vector identities for v1."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api" / "v1" / "acceptance-vectors.json"
DEPENDENT = tuple(f"K-NEG-{number:03d}" for number in range(56, 64)) + ("K-NEG-065",)


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


def apply_declared_mutation(base: dict[str, Any], vector: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    case = copy.deepcopy(base)
    vector_id = vector["id"]
    inputs = vector["input"]
    if vector_id == "K-NEG-056":
        return case, []
    if vector_id == "K-NEG-063":
        case["policy"]["policy_id"] = inputs["policy_id"]
        return case, ["policy.policy_id"]
    mutation = inputs["mutation"]
    path = mutation["path"]
    if vector_id == "K-NEG-061":
        facts = case["evaluation_view"]["facts"]
        candidate = mutation["remove_candidate_id"]
        case["evaluation_view"]["facts"] = [fact for fact in facts if fact["candidate_id"] != candidate]
        declared = ["evaluation_view.facts"]
    elif vector_id == "K-NEG-065":
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
    if inputs.get("recompute_evaluation_digest"):
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

    for vector_id in DEPENDENT:
        vector = by_id[vector_id]
        if vector.get("prior_vector") != "K-POS-025" or vector["input"].get("base_vector") != "K-POS-025":
            raise ValueError(f"{vector_id}: exact positive base is not declared")
        case_base = base
        if vector_id == "K-NEG-062":
            case_base = copy.deepcopy(base)
            case_base["selection"] = copy.deepcopy(selection["expect"]["selection"])
        mutated, declared = apply_declared_mutation(case_base, vector)
        actual = normalized_paths(case_base, mutated, vector_id)
        if not paths_match(actual, declared):
            raise ValueError(f"{vector_id}: mutation differs: {actual} != {declared}")
        if vector_id == "K-NEG-056":
            selected = vector["input"]["policy_return"]["candidate_id"]
            allowed = vector["input"]["expected_requested_envelope_candidate_ids"]
            if selected in allowed or base["requested_key"] != base["policy_input"]["envelope_key"]:
                raise ValueError("K-NEG-056: out-of-envelope mutation is incomplete")

    print("snapshot vector identities: 2 snapshots, 4 evaluation digests, 9 dependent mutations valid")


if __name__ == "__main__":
    main()
