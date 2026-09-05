#!/usr/bin/env python3
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
        "SourceDescriptor": {
            "source_id",
            "source_epoch_id",
            "protocol_id",
            "profile_id",
            "profile_version",
            "registry_evidence",
            "started_at",
            "state",
            "revision",
        },
        "NativeBinding": {
            "binding_id",
            "asset_id",
            "source_id",
            "source_epoch_id",
            "driver_generation",
            "native_resource",
            "state",
            "revision",
        },
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
        "Selection": {
            "contract",
            "snapshot_id",
            "revisions",
            "evaluation_digest",
            "context",
            "key",
            "policy_id",
            "policy_version",
            "selected_candidate",
            "candidate_revision",
            "presentation_only",
        },
        "FactEnvelope": {
            "asset_id",
            "key",
            "candidates",
            "conflicts",
            "revision",
        },
        "Conflict": {"conflict_id", "kind", "candidates", "evidence", "state"},
        "DispatchEvidence": {
            "attempt_id",
            "started",
            "completed",
            "delivery",
            "possible_side_effect",
            "evidence",
        },
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
            "evaluation",
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
    if "selection" in blocks.get("FactEnvelope", set()):
        raise ValueError("FactEnvelope must not persist presentation selection")
    forbidden_publication_metadata = {"selection", "selections", "conflicts"}
    if forbidden_publication_metadata & blocks.get("PublicationBatch", set()):
        raise ValueError("PublicationBatch must not accept envelope metadata input")

    required_hooks = (
        "Definitions() DefinitionIndex",
        "EvaluatePredicate(FactCandidate, PredicateOp, Value) (bool, error)",
        "ValidateIntent(Intent) error",
        "EvaluateReadback(Intent, v1.FactCandidate) (ReadbackRelation, error)",
        "Select(FactEnvelope, []EvaluatedFact) (CandidateID, error)",
    )
    for hook in required_hooks:
        if hook not in kernel_text:
            raise ValueError(f"required pack hook is missing: {hook}")
    if not re.search(
        r"SelectPresentation\(Snapshot, EvaluationView, FactKey, PolicyID,\s+"
        r"SemanticVersion\) \(Selection, error\)",
        kernel_text,
    ):
        raise ValueError("SelectPresentation must receive complete immutable inputs")


def require_correction_vectors(vectors: list[dict[str, Any]]) -> None:
    by_id = {vector.get("id"): vector for vector in vectors}
    required = {
        "K-POS-018": ("PublicationBatch", "positive"),
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
        "K-POS-023": ("CausalContext", "positive"),
        "K-NEG-045": ("ExecutionRecord", "negative"),
        "K-NEG-046": ("ExecutionRecord", "negative"),
        "K-NEG-047": ("IdentityLink", "negative"),
        "K-NEG-048": ("CapabilityInstance", "negative"),
        "K-NEG-049": ("Precondition", "negative"),
        "K-NEG-050": ("Precondition", "negative"),
        "K-NEG-051": ("CausalContext", "negative"),
        "K-POS-024": ("PublicationBatch", "positive"),
        "K-NEG-052": ("CausalContext", "negative"),
        "K-NEG-053": ("CausalContext", "negative"),
        "K-NEG-054": ("FactEnvelope", "negative"),
        "K-NEG-055": ("PublicationBatch", "negative"),
        "K-POS-025": ("Selection", "positive"),
        "K-NEG-056": ("Selection", "negative"),
        "K-NEG-057": ("Selection", "negative"),
        "K-NEG-058": ("Selection", "negative"),
        "K-NEG-059": ("Selection", "negative"),
        "K-NEG-060": ("Selection", "negative"),
        "K-NEG-061": ("Selection", "negative"),
        "K-NEG-062": ("Selection", "negative"),
        "K-NEG-063": ("SelectionPolicy", "negative"),
        "K-NEG-064": ("SelectionPolicy", "negative"),
        "K-NEG-065": ("Selection", "negative"),
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
        "evaluation",
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
    derivation_ids = [item.get("candidate_id") for item in derivation.get("inputs", [])]
    if derivation_ids != sorted(derivation_ids):
        raise ValueError("K-POS-020: derivation inputs are not canonical")

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

    applied = by_id["K-POS-014"].get("input", {})
    dispatch_completed = applied.get("dispatch", {}).get("completed", {})
    readback_evaluation = applied.get("readback", {}).get("evaluation", {})
    candidate = applied.get("resolved_candidate", {})
    candidate_times = candidate.get("times", {})
    for label, context in (
        ("dispatch completion", dispatch_completed),
        ("readback evaluation", readback_evaluation),
    ):
        if not {"evaluated_at", "evaluate_monotonic"}.issubset(context):
            raise ValueError(f"K-POS-014: {label} context is incomplete")
    completed_mono = dispatch_completed["evaluate_monotonic"]
    receipt_mono = candidate_times.get("receipt_monotonic", {})
    if (
        completed_mono.get("clock_epoch_id") != receipt_mono.get("clock_epoch_id")
        or int(receipt_mono.get("nanoseconds", "-1"))
        <= int(completed_mono.get("nanoseconds", "-1"))
    ):
        raise ValueError("K-POS-014: post-dispatch monotonic receipt proof is missing")
    if candidate.get("candidate_revision") == applied.get(
        "admitted_candidate_revision"
    ):
        raise ValueError("K-POS-014: post-dispatch candidate revision is unchanged")

    retained = by_id["K-NEG-045"].get("input", {})
    retained_candidate = retained.get("resolved_candidate", {})
    retained_completed = retained.get("dispatch", {}).get("completed", {})
    retained_receipt = retained_candidate.get("times", {}).get(
        "receipt_monotonic", {}
    )
    if (
        retained_candidate.get("candidate_revision")
        != retained.get("admitted_candidate_revision")
        or retained_receipt.get("clock_epoch_id")
        != retained_completed.get("evaluate_monotonic", {}).get("clock_epoch_id")
        or int(retained_receipt.get("nanoseconds", "0"))
        >= int(
            retained_completed.get("evaluate_monotonic", {}).get(
                "nanoseconds", "0"
            )
        )
        or by_id["K-NEG-045"]["expect"].get("error_id") != "invalid_outcome"
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
        not {"evaluated_at", "evaluate_monotonic"}.issubset(
            uncertain_evaluation
        )
        or uncertain_receipt.get("clock_epoch_id")
        == uncertain_evaluation.get("evaluate_monotonic", {}).get(
            "clock_epoch_id"
        )
        or uncertainty <= max_uncertainty
        or uncertain.get("evaluated_freshness") != "unknown"
        or by_id["K-NEG-046"]["expect"].get("error_id") != "invalid_outcome"
    ):
        raise ValueError("K-NEG-046: unverifiable freshness control is incomplete")

    expected_partition = {
        "K-NEG-047": "identity_not_qualified",
        "K-NEG-048": "capability_not_qualified",
        "K-NEG-049": "precondition_failed",
        "K-NEG-050": "precondition_failed",
    }
    for vector_id, error_id in expected_partition.items():
        if by_id[vector_id]["expect"].get("error_id") != error_id:
            raise ValueError(f"{vector_id}: context-specific error is incorrect")
    if by_id["K-NEG-047"].get("input", {}).get("basis") != []:
        raise ValueError("K-NEG-047: empty identity basis control is missing")
    if by_id["K-NEG-048"].get("input", {}).get("activation_evidence") != []:
        raise ValueError("K-NEG-048: empty capability proof control is missing")
    if by_id["K-NEG-049"].get("input", {}).get("candidate_id") in by_id[
        "K-NEG-049"
    ].get("input", {}).get("snapshot_candidates", []):
        raise ValueError("K-NEG-049: missing precondition target control is invalid")
    revision_case = by_id["K-NEG-050"].get("input", {})
    if revision_case.get("candidate_revision") == revision_case.get(
        "resolved_candidate_revision"
    ):
        raise ValueError("K-NEG-050: revision-changed precondition control is invalid")

    causal = by_id["K-POS-023"].get("input", {})
    states = {state.get("event"): state for state in causal.get("states", [])}
    expected_states = {
        "created_at_a": ([], 0, ["target:a"], 1),
        "b_ingress": (["target:a"], 1, ["target:a", "target:b"], 2),
        "c_ingress": (
            ["target:a", "target:b"],
            2,
            ["target:a", "target:b", "target:c"],
            3,
        ),
    }
    for event, (incoming_path, incoming_hops, accepted_path, accepted_hops) in expected_states.items():
        state = states.get(event, {})
        if (
            state.get("incoming_path") != incoming_path
            or state.get("incoming_hop_count") != incoming_hops
            or state.get("accepted_path") != accepted_path
            or state.get("accepted_hop_count") != accepted_hops
        ):
            raise ValueError(f"K-POS-023: {event} causal transition is invalid")
    for event, path, hops in (
        ("a_emits_to_b", ["target:a"], 1),
        ("b_emits_to_c", ["target:a", "target:b"], 2),
    ):
        state = states.get(event, {})
        if state.get("emitted_path") != path or state.get("emitted_hop_count") != hops:
            raise ValueError(f"K-POS-023: {event} mutates causal context")
    reflection = by_id["K-NEG-051"].get("input", {})
    if (
        reflection.get("receiver") not in reflection.get("incoming_path", [])
        or reflection.get("attempted_path_after_rejection")
        != reflection.get("incoming_path")
        or by_id["K-NEG-051"]["expect"].get("error_id") != "echo_suppressed"
    ):
        raise ValueError("K-NEG-051: C-to-A reflection control is invalid")

    hard_bound = by_id["K-NEG-021"]
    hard_input = hard_bound.get("input", {})
    if (
        hard_bound["expect"].get("error_id") != "causal_budget_exceeded"
        or hard_input.get("all_wire_fields_syntactically_valid") is not True
        or hard_input.get("causal_domain_limits_are_only_failure") is not True
        or hard_input.get("max_hops", 0) <= 16
        or int(hard_input.get("lifetime_ns", "0")) <= 300000000000
    ):
        raise ValueError("K-NEG-021: causal-domain error partition is incomplete")
    malformed_causal = by_id["K-NEG-052"]
    malformed_input = malformed_causal.get("input", {})
    if (
        malformed_causal["expect"].get("error_id") != "invalid_time"
        or malformed_input.get("first_seen_at", {}).get("uncertainty_ns")
        != "-1"
        or malformed_input.get("max_hops", 0) <= 16
    ):
        raise ValueError("K-NEG-052: malformed causal-time overlap is incomplete")
    exhausted = by_id["K-NEG-053"]
    exhausted_input = exhausted.get("input", {})
    if (
        exhausted["expect"].get("error_id") != "causal_budget_exceeded"
        or exhausted_input.get("all_wire_fields_syntactically_valid") is not True
        or exhausted_input.get("incoming_hop_count")
        != exhausted_input.get("max_hops")
        or len(exhausted_input.get("incoming_path", []))
        != exhausted_input.get("incoming_hop_count")
        or exhausted_input.get("receiver") in exhausted_input.get(
            "incoming_path", []
        )
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
    if len(conflicts) != 1:
        raise ValueError("K-POS-024: exact derived conflict is missing")
    conflict = conflicts[0]
    conflict_source = {
        "contract": "helianthus.semantic.conflict-id/v1",
        "asset_id": metadata.get("initial_snapshot", {}).get("asset_id"),
        "key": conflicting.get("key"),
        "kind": "value",
        "candidates": ["candidate:source:a", "candidate:source:b"],
    }
    conflict_bytes = json.dumps(
        conflict_source,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
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
        create.get("publisher_metadata_members_present") is not False
        or withdrawal.get("publisher_metadata_members_present") is not False
        or conflict.get("conflict_id") != expected_conflict_id
        or conflict.get("candidates")
        != ["candidate:source:a", "candidate:source:b"]
        or conflict.get("evidence") != ["evidence:source:a", "evidence:source:b"]
        or conflicting.get("selection_member_absent") is not True
    ):
        raise ValueError("K-POS-024: kernel-owned conflict derivation is incomplete")

    def kpos024_selection_binding_valid(candidate_selection: dict[str, Any]) -> bool:
        return (
            candidate_selection.get("snapshot_id")
            == metadata.get("conflicting_snapshot", {}).get("snapshot_id")
            and candidate_selection.get("revisions")
            == metadata.get("conflicting_snapshot", {}).get("revisions")
            and candidate_selection.get("evaluation_digest")
            == expected_selection_digest
            and candidate_selection.get("context") == selection_view.get("context")
            and candidate_selection.get("selected_candidate")
            == "candidate:source:a"
            and candidate_selection.get("candidate_revision") == "4"
        )

    if (
        selection.get("stored_in_snapshot") is not False
        or selection.get("contract") != "helianthus.semantic.selection/v1"
        or selection_view.get("contract")
        != "helianthus.semantic.evaluation/v1"
        or selection_view.get("snapshot_id") != selection.get("snapshot_id")
        or selection_view.get("revisions") != selection.get("revisions")
        or selection_view.get("context") != selection.get("context")
        or selection_view.get("facts")
        != [
            {
                "candidate_id": "candidate:source:a",
                "candidate_revision": "4",
                "freshness": "fresh",
                "effective_availability": "available",
            },
            {
                "candidate_id": "candidate:source:b",
                "candidate_revision": "2",
                "freshness": "fresh",
                "effective_availability": "available",
            },
        ]
        or selection_view.get("evaluation_digest") != expected_selection_digest
        or "presentation_evaluation_digest_recomputed"
        not in by_id["K-POS-024"].get("expect", {}).get("assertions", [])
        or not {"evaluated_at", "evaluate_monotonic"}.issubset(
            selection.get("context", {})
        )
        or not kpos024_selection_binding_valid(selection)
    ):
        raise ValueError("K-POS-024: snapshot-bound pure selection is incomplete")
    mutated_selection = copy.deepcopy(selection)
    mutated_selection["evaluation_digest"] = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )
    if kpos024_selection_binding_valid(mutated_selection):
        raise ValueError("K-POS-024: changed selection digest was not rejected")
    if (
        withdrawal.get("fact_withdrawals") != ["candidate:source:a"]
        or result_envelope.get("candidates") != ["candidate:source:b@2"]
        or result_envelope.get("conflicts") != []
        or result_envelope.get("selection_member_absent") is not True
        or resulting.get("old_selection_valid_for_resulting_snapshot") is not False
        or prior.get("unchanged") is not True
        or prior.get("conflict_id") != expected_conflict_id
    ):
        raise ValueError("K-POS-024: withdrawal metadata cleanup is incomplete")
    mismatch = by_id["K-NEG-054"]
    if (
        mismatch["expect"].get("error_id") != "invalid_value"
        or mismatch.get("input", {}).get("supplied_conflict", {}).get("evidence")
        == mismatch.get("input", {}).get("derived_evidence")
    ):
        raise ValueError("K-NEG-054: derived conflict mismatch control is incomplete")
    publisher_metadata = by_id["K-NEG-055"]
    if (
        publisher_metadata["expect"].get("error_id") != "unknown_member"
        or "conflicts" not in publisher_metadata.get("input", {})
    ):
        raise ValueError("K-NEG-055: publisher metadata rejection is incomplete")
    initial_revisions = metadata.get("initial_snapshot", {}).get("revisions", {})
    conflict_revisions = metadata.get("conflicting_snapshot", {}).get(
        "revisions", {}
    )
    result_revisions = resulting.get("revisions", {})
    if (
        int(conflict_revisions.get("semantic", "0"))
        != int(initial_revisions.get("semantic", "0")) + 1
        or int(result_revisions.get("semantic", "0"))
        != int(conflict_revisions.get("semantic", "0")) + 1
        or int(conflict_revisions.get("facts", "0"))
        != int(initial_revisions.get("facts", "0")) + 1
        or int(result_revisions.get("facts", "0"))
        != int(conflict_revisions.get("facts", "0")) + 1
        or int(result_envelope.get("revision", "0"))
        != int(conflicting.get("revision", "0")) + 1
    ):
        raise ValueError("K-POS-024: metadata revision sequence is incomplete")

    selection_case = by_id["K-POS-025"]
    selection_input = selection_case.get("input", {})
    snapshot = selection_input.get("snapshot", {})
    view = selection_input.get("evaluation_view", {})
    requested_key = selection_input.get("requested_key")
    required_snapshot_fields = {
        "contract",
        "snapshot_id",
        "asset_id",
        "revisions",
        "evaluated_at",
        "evaluate_monotonic",
        "sources",
        "bindings",
        "identity_links",
        "facts",
        "services",
        "capabilities",
        "fences",
        "cursors",
    }
    required_candidate_fields = {
        "candidate_id",
        "key",
        "value",
        "quality",
        "times",
        "freshness_policy",
        "binding_id",
        "source_epoch_id",
        "driver_generation",
        "origin",
        "evidence",
        "revision",
    }
    view_without_digest = {
        key: value for key, value in view.items() if key != "evaluation_digest"
    }
    view_bytes = json.dumps(
        view_without_digest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    expected_view_digest = "sha256:" + hashlib.sha256(view_bytes).hexdigest()
    snapshot_candidates: dict[str, tuple[str, Any]] = {}
    requested_envelope: dict[str, Any] | None = None
    bindings = {
        item.get("binding_id"): item for item in snapshot.get("bindings", [])
    }
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
                binding.get("state") != "current"
                or binding.get("source_epoch_id") != item.get("source_epoch_id")
                or binding.get("driver_generation")
                != item.get("driver_generation")
                or origin.get("binding_id") != item.get("binding_id")
                or origin.get("source_epoch_id") != item.get("source_epoch_id")
                or origin.get("source_id") != binding.get("source_id")
            ):
                raise ValueError("K-POS-025: snapshot candidate path is inconsistent")
            snapshot_candidates[item.get("candidate_id")] = (
                item.get("revision"),
                key_bytes,
            )
    evaluated_candidates = {
        item.get("candidate_id"): item.get("candidate_revision")
        for item in view.get("facts", [])
    }
    evaluated_ids = [item.get("candidate_id") for item in view.get("facts", [])]
    candidate_sets_match = set(snapshot_candidates) == set(evaluated_candidates)
    candidate_revisions_match = candidate_sets_match and all(
        snapshot_candidates[candidate_id][0] == revision
        for candidate_id, revision in evaluated_candidates.items()
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
        or view.get("evaluation_digest") != expected_view_digest
        or not candidate_revisions_match
        or len(snapshot_candidates) != sum(
            len(envelope.get("candidates", []))
            for envelope in snapshot.get("facts", [])
        )
        or envelope_keys != sorted(envelope_keys)
        or evaluated_ids != sorted(evaluated_ids)
        or len(evaluated_ids) != len(set(evaluated_ids))
        or requested_envelope is None
        or len(snapshot.get("facts", [])) < 2
    ):
        raise ValueError("K-POS-025: snapshot/evaluation binding is incomplete")
    requested_ids = [
        item.get("candidate_id")
        for item in requested_envelope.get("candidates", [])
    ]
    requested_candidates_complete = all(
        {
            "candidate_id",
            "revision",
            "value",
            "quality",
            "origin",
        }.issubset(item)
        for item in requested_envelope.get("candidates", [])
    ) and "conflicts" in requested_envelope
    policy_input = selection_input.get("policy_input", {})
    if (
        policy_input.get("envelope_key") != requested_key
        or policy_input.get("candidate_ids") != requested_ids
        or policy_input.get("evaluated_fact_ids") != requested_ids
        or selection_input.get("policy", {}).get("registered_once") is not True
        or not requested_candidates_complete
    ):
        raise ValueError("K-POS-025: exact envelope policy input is incomplete")
    if (
        result != repeat_result
        or selection_input.get("repeat_identical_call") is not True
        or result.get("contract") != "helianthus.semantic.selection/v1"
        or result.get("snapshot_id") != snapshot.get("snapshot_id")
        or result.get("revisions") != snapshot.get("revisions")
        or result.get("evaluation_digest") != view.get("evaluation_digest")
        or result.get("context") != view.get("context")
        or result.get("key") != requested_key
        or result.get("policy_id")
        != selection_input.get("policy", {}).get("policy_id")
        or result.get("policy_version")
        != selection_input.get("policy", {}).get("policy_version")
        or result.get("selected_candidate") not in requested_ids
        or result.get("candidate_revision")
        != evaluated_candidates.get(result.get("selected_candidate"))
        or result.get("presentation_only") is not True
    ):
        raise ValueError("K-POS-025: deterministic selection result is incomplete")

    for vector_id in (
        "K-NEG-056",
        "K-NEG-057",
        "K-NEG-058",
        "K-NEG-059",
        "K-NEG-060",
        "K-NEG-061",
        "K-NEG-062",
        "K-NEG-063",
        "K-NEG-065",
    ):
        if by_id[vector_id].get("input", {}).get("base_vector") != "K-POS-025":
            raise ValueError(f"{vector_id}: complete selection base input is missing")

    wrong_envelope = by_id["K-NEG-056"]
    wrong_input = wrong_envelope.get("input", {})
    if (
        wrong_envelope["expect"].get("error_id") != "invalid_value"
        or wrong_input.get("base_vector") != "K-POS-025"
        or wrong_input.get("policy_return", {}).get("candidate_id")
        in wrong_input.get("expected_requested_envelope_candidate_ids", [])
        or wrong_input.get("expected_requested_envelope_candidate_ids")
        != requested_ids
    ):
        raise ValueError("K-NEG-056: wrong-envelope result control is incomplete")

    def recompute_view_digest(candidate_view: dict[str, Any]) -> str:
        unsigned = {
            key: value
            for key, value in candidate_view.items()
            if key != "evaluation_digest"
        }
        encoded = json.dumps(
            unsigned,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    mismatch_ids = by_id["K-NEG-057"]
    mismatch_ids_input = mismatch_ids.get("input", {})
    mismatch_ids_case = copy.deepcopy(selection_input)
    mismatch_ids_case["evaluation_view"]["snapshot_id"] = mismatch_ids_input[
        "mutation"
    ]["replacement"]
    mismatch_ids_case["evaluation_view"][
        "evaluation_digest"
    ] = recompute_view_digest(mismatch_ids_case["evaluation_view"])
    if (
        mismatch_ids["expect"].get("error_id") != "revision_conflict"
        or mismatch_ids_input.get("mutation", {}).get("path")
        != "evaluation_view.snapshot_id"
        or mismatch_ids_input.get("recompute_evaluation_digest") is not True
        or mismatch_ids_case["snapshot"]["snapshot_id"]
        == mismatch_ids_case["evaluation_view"]["snapshot_id"]
        or mismatch_ids_case["evaluation_view"]["evaluation_digest"]
        != recompute_view_digest(mismatch_ids_case["evaluation_view"])
    ):
        raise ValueError("K-NEG-057: snapshot ID mismatch control is incomplete")
    mismatch_revisions = by_id["K-NEG-058"]
    mismatch_revisions_input = mismatch_revisions.get("input", {})
    mismatch_revisions_case = copy.deepcopy(selection_input)
    mismatch_revisions_case["evaluation_view"]["revisions"][
        "facts"
    ] = mismatch_revisions_input["mutation"]["replacement"]
    mismatch_revisions_case["evaluation_view"][
        "evaluation_digest"
    ] = recompute_view_digest(mismatch_revisions_case["evaluation_view"])
    if (
        mismatch_revisions["expect"].get("error_id") != "revision_conflict"
        or mismatch_revisions_input.get("mutation", {}).get("path")
        != "evaluation_view.revisions.facts"
        or mismatch_revisions_input.get("recompute_evaluation_digest") is not True
        or mismatch_revisions_case["snapshot"]["revisions"]
        == mismatch_revisions_case["evaluation_view"]["revisions"]
        or mismatch_revisions_case["evaluation_view"]["evaluation_digest"]
        != recompute_view_digest(mismatch_revisions_case["evaluation_view"])
    ):
        raise ValueError("K-NEG-058: revision mismatch control is incomplete")
    bad_digest = by_id["K-NEG-059"]
    bad_digest_input = bad_digest.get("input", {})
    bad_digest_case = copy.deepcopy(selection_input)
    bad_digest_case["evaluation_view"]["evaluation_digest"] = bad_digest_input[
        "mutation"
    ]["replacement"]
    if (
        bad_digest["expect"].get("error_id") != "digest_mismatch"
        or bad_digest_input.get("mutation", {}).get("path")
        != "evaluation_view.evaluation_digest"
        or bad_digest_input.get("digest_syntax_valid") is not True
        or bad_digest_case["evaluation_view"]["evaluation_digest"]
        == recompute_view_digest(bad_digest_case["evaluation_view"])
    ):
        raise ValueError("K-NEG-059: evaluation digest mismatch control is incomplete")
    missing_key = by_id["K-NEG-060"]
    missing_key_input = missing_key.get("input", {})
    missing_key_case = copy.deepcopy(selection_input)
    missing_key_case["requested_key"] = missing_key_input["mutation"][
        "replacement"
    ]
    if (
        missing_key["expect"].get("error_id") != "dangling_reference"
        or missing_key_input.get("mutation", {}).get("path") != "requested_key"
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
    missing_candidate_case["evaluation_view"][
        "evaluation_digest"
    ] = recompute_view_digest(missing_candidate_case["evaluation_view"])
    if (
        missing_candidate["expect"].get("error_id") != "dangling_reference"
        or missing_candidate_input.get("mutation", {}).get("path")
        != "evaluation_view.facts"
        or missing_candidate_input.get("recompute_evaluation_digest") is not True
        or removed_candidate_id not in snapshot_candidates
        or removed_candidate_id
        in {
            item.get("candidate_id")
            for item in missing_candidate_case["evaluation_view"]["facts"]
        }
        or missing_candidate_case["evaluation_view"]["evaluation_digest"]
        != recompute_view_digest(missing_candidate_case["evaluation_view"])
    ):
        raise ValueError("K-NEG-061: incomplete evaluation view control is missing")
    mismatch_context = by_id["K-NEG-062"]
    mismatch_context_input = mismatch_context.get("input", {})
    mismatch_context_result = copy.deepcopy(result)
    mismatch_context_result["context"]["evaluate_monotonic"][
        "nanoseconds"
    ] = mismatch_context_input["mutation"]["replacement"]
    if (
        mismatch_context["expect"].get("error_id") != "revision_conflict"
        or mismatch_context_input.get("mutation", {}).get("path")
        != "selection.context.evaluate_monotonic.nanoseconds"
        or mismatch_context_result.get("context") == view.get("context")
    ):
        raise ValueError("K-NEG-062: selection context mismatch is incomplete")
    missing_policy = by_id["K-NEG-063"]
    duplicate_policy = by_id["K-NEG-064"]
    if (
        missing_policy["expect"].get("error_id") != "definition_owner_missing"
        or missing_policy.get("input", {}).get("exact_registration_absent")
        is not True
        or duplicate_policy["expect"].get("error_id")
        != "definition_owner_conflict"
        or duplicate_policy.get("input", {}).get("registration_count") != 2
    ):
        raise ValueError("selection-policy ownership controls are incomplete")
    mismatched_candidate_revision = by_id["K-NEG-065"]
    mismatched_candidate_input = mismatched_candidate_revision.get("input", {})
    mismatched_candidate_case = copy.deepcopy(selection_input)
    target_candidate_id = "candidate:voltage:b"
    target_fact = next(
        item
        for item in mismatched_candidate_case["evaluation_view"]["facts"]
        if item.get("candidate_id") == target_candidate_id
    )
    target_fact["candidate_revision"] = mismatched_candidate_input["mutation"][
        "replacement"
    ]
    mismatched_candidate_case["evaluation_view"][
        "evaluation_digest"
    ] = recompute_view_digest(mismatched_candidate_case["evaluation_view"])
    if (
        mismatched_candidate_revision["expect"].get("error_id")
        != "revision_conflict"
        or mismatched_candidate_input.get("mutation", {}).get("path")
        != "evaluation_view.facts[candidate:voltage:b].candidate_revision"
        or mismatched_candidate_input.get("recompute_evaluation_digest") is not True
        or target_fact.get("candidate_revision")
        == snapshot_candidates[target_candidate_id][0]
        or mismatched_candidate_case["evaluation_view"]["evaluation_digest"]
        != recompute_view_digest(mismatched_candidate_case["evaluation_view"])
    ):
        raise ValueError("K-NEG-065: candidate revision mismatch is incomplete")

    restart_snapshot = by_id["K-POS-018"].get("input", {}).get(
        "resulting_snapshot", {}
    )
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
        != {
            "source-epoch:after-restart": "current",
            "source-epoch:before-restart": "retired",
        }
        or retired_binding_states.get("binding:pv:old") != "retired"
        or restart_snapshot.get("old_epoch_candidates") != []
        or restart_snapshot.get("full_snapshot_validation") != "accept"
        or restart_snapshot.get("canonical_serialization") != "accept"
    ):
        raise ValueError("K-POS-018: resolvable retirement tombstones are incomplete")

    transition = by_id["K-POS-021"].get("input", {})
    if not transition.get("generation_fences") or transition.get(
        "driver_generation"
    ) == transition["generation_fences"][0].get("driver_generation"):
        raise ValueError("K-POS-021: explicit higher-generation fence is missing")
    transition_assertions = set(by_id["K-POS-021"]["expect"].get("assertions", []))
    if not {
        "old_observed_and_derived_candidates_removed",
        "all_tombstone_references_resolve",
        "full_post_transition_snapshot_valid_and_canonical",
        "generation_7_callback_rejected",
        "generation_8_only_actionable",
    }.issubset(transition_assertions):
        raise ValueError("K-POS-021: atomic supersession assertions are incomplete")
    if by_id["K-NEG-042"].get("input", {}).get("generation_fences") != []:
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
        != {"binding:evse:01": "fenced", "binding:evse:02": "current"}
        or service_states.get("service:evse:01") != "withdrawn"
        or capability_states.get("capability:limit:01") != "withdrawn"
        or service_states.get("service:evse:02") != "available"
        or capability_states.get("capability:limit:02") != "available"
        or resulting_snapshot.get("full_snapshot_validation") != "accept"
        or resulting_snapshot.get("canonical_serialization") != "accept"
    ):
        raise ValueError("K-POS-021: resolvable transition tombstones are incomplete")

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
