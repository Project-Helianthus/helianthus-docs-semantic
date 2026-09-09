#!/usr/bin/env python3
"""Validate the machine-significant retained-observation v1 contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "api/v1/kernel.md"
ACCEPTANCE = ROOT / "api/v1/acceptance.md"
SERIALIZATION = ROOT / "api/v1/serialization.md"
FIXTURE = ROOT / "api/v1/retained-observation-acceptance.json"

AXES = ["candidate_id", "candidate_revision", "jcs_key", "binding_id", "source_epoch_id", "driver_generation"]
EXPECTED = {
    "RO-POS-001": ("positive", "generation_fence", {"current_removed", "original_candidate_byte_identical", "retained_visible_before_original_deadline", "fenced_non_actionable", "matching_fenced_binding_and_fence_path"}),
    "RO-POS-002": ("positive", "source_retirement", {"current_removed", "original_candidate_byte_identical", "retained_visible_before_original_deadline", "retired_non_actionable", "matching_retired_binding_and_source_path"}),
    "RO-POS-003": ("positive", "same_id_replacement", {"current_replacement_visible", "retained_prior_visible", "identity_axes_distinguish_instances", "canonical_tuple_order"}),
    "RO-POS-004": ("positive", "withdraw_retained_id", {"all_matching_retained_id_instances_removed", "no_dangling_current_lookup", "current_unrelated_unchanged"}),
    "RO-POS-005": ("positive", "evaluate_after_original_deadline", {"retained_absent_from_current_view", "retained_absent_from_readback_view", "snapshot_bytes_unchanged", "no_publication_required"}),
    "RO-POS-006": ("positive", "successive_fences", {"multiple_revisions_retained", "bounded_at_32", "canonical_tuple_order", "individual_original_deadlines"}),
    "RO-NEG-001": ("negative", "validate_retained_copy", {"reject", "error_id:invalid_value", "state_unchanged"}),
    "RO-NEG-002": ("negative", "select_retained", {"reject", "error_id:route_selection_forbidden", "state_unchanged"}),
    "RO-NEG-003": ("negative", "admit_or_confirm_from_retained", {"reject", "error_id:precondition_failed", "state_unchanged"}),
    "RO-NEG-004": ("negative", "incomplete_fence_transition", {"reject", "error_id:generation_transition_incomplete", "current_and_retained_state_unchanged"}),
    "RO-NEG-005": ("negative", "validate_retained_tombstone_path", {"reject", "error_id:dangling_reference", "current_and_retained_state_unchanged"}),
    "RO-NEG-006": ("negative", "validate_retained_tombstone_path", {"reject", "error_id:dangling_reference", "current_and_retained_state_unchanged"}),
}

CLAUSES = (
    "`retained` is separately sorted by retained-instance identity.",
    "an expired record is absent even when no later publication\noccurred.",
    "MUST NOT expose an unevaluated\n`Snapshot` as current state.",
    "`(candidate_id,candidate_revision,JCS(key),binding_id,source_epoch_id,driver_generation)`",
    "At most\n32 retained instances exist per asset; an excess rejects atomically with\n`bounds_exceeded`.",
    "it removes the current candidate and every matching retained\ninstance.",
    "Retained-path validation is separate from current-fact validation.",
    "MUST exist. For `removal=source_retirement`, that binding MUST be `retired` and\nthe matching source descriptor MUST be `retired` for its source ID and source\nepoch ID.",
)

def main() -> None:
    kernel, acceptance, serialization = (path.read_text(encoding="utf-8") for path in (KERNEL, ACCEPTANCE, SERIALIZATION))
    for clause in CLAUSES:
        if kernel.count(clause) != 1:
            raise ValueError(f"retained contract clause missing or repeated: {clause!r}")
    for token in ("## Retained-observation falsifiers", "retained-observation-acceptance.json"):
        if token not in acceptance:
            raise ValueError(f"retained acceptance reference missing: {token!r}")
    if "EvaluationView.retained" not in serialization:
        raise ValueError("retained serialization order is missing")
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if data.get("contract") != "helianthus.semantic.retained-observation.acceptance/v1" or data.get("kernel_contract") != "helianthus.semantic.kernel/v1" or data.get("retained_contract") != "helianthus.semantic.retained-observation/v1":
        raise ValueError("retained fixture contract pin differs")
    if data.get("identity_axes") != AXES:
        raise ValueError("retained fixture identity axes differ")
    rows = data.get("scenarios")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise ValueError("retained scenario count differs")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not {"id", "polarity", "operation", "expect"}.issubset(row):
            raise ValueError("retained scenario shape differs")
        ident = row["id"]
        if ident in seen or ident not in EXPECTED:
            raise ValueError(f"retained scenario id differs: {ident!r}")
        seen.add(ident)
        polarity, operation, outcome = EXPECTED[ident]
        if row["polarity"] != polarity or row["operation"] != operation or set(row["expect"]) != outcome or len(row["expect"]) != len(outcome):
            raise ValueError(f"retained scenario differs: {ident}")
    tombstone = next(row for row in rows if row["id"] == "RO-NEG-005")
    retirement_tombstone = next(row for row in rows if row["id"] == "RO-NEG-006")
    if tombstone.get("mutation") != "replace_matching_fenced_binding_or_fence_axis":
        raise ValueError("retained tombstone-path mutation differs")
    if retirement_tombstone.get("mutation") != "replace_matching_retired_source_descriptor_axis":
        raise ValueError("retained retirement-tombstone mutation differs")
    fence = next(row for row in rows if row["id"] == "RO-POS-001")["input"]
    retired = next(row for row in rows if row["id"] == "RO-POS-002")["input"]
    mismatch = tombstone["input"]
    for label, scenario, state, tombstone_key in (("fence", fence, "fenced", "fence"), ("retirement", retired, "retired", "source")):
        path, binding, marker = scenario.get("candidate_path", {}), scenario.get("binding", {}), scenario.get(tombstone_key, {})
        axes = ("source_id", "source_epoch_id") + (("driver_generation",) if tombstone_key == "fence" else ())
        if binding.get("state") != state or any(path.get(axis) != binding.get(axis) or path.get(axis) != marker.get(axis) for axis in axes) or path.get("binding_id") != binding.get("binding_id"):
            raise ValueError(f"retained {label} tombstone path differs")
    if mismatch.get("candidate_path", {}).get("driver_generation") == mismatch.get("binding", {}).get("driver_generation"):
        raise ValueError("retained mismatch control is not mismatched")
    retirement_mismatch = retirement_tombstone["input"]
    if retirement_mismatch.get("retained_removal") != "source_retirement" or retirement_mismatch.get("binding", {}).get("state") != "retired" or retirement_mismatch.get("source", {}).get("state") != "retired" or retirement_mismatch.get("candidate_path", {}).get("source_epoch_id") == retirement_mismatch.get("source", {}).get("source_epoch_id"):
        raise ValueError("retained retirement mismatch control is not concrete")
    print("Retained observation v1: PASS; 12 normative falsifiers")

if __name__ == "__main__":
    main()
