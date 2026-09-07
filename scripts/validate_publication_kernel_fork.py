#!/usr/bin/env python3
"""Validate the machine-significant PublicationKernel fork contract."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "api/v1/kernel.md"
ACCEPTANCE = ROOT / "api/v1/acceptance.md"
FIXTURE = ROOT / "api/v1/kernel-fork-acceptance.json"
EXPECTED = {
    "KF-POS-001": ("positive", "fork", {"point_in_time", "current_and_canonical_byte_identical"}),
    "KF-POS-002": ("positive", "apply_sequence_33_to_fork", {"source_byte_identical", "fork_advances_once", "same_source_epoch_generation"}),
    "KF-NEG-001": ("negative", "apply_malformed_or_conflicting_batch_to_fork", {"reject", "source_and_fork_byte_identical"}),
    "KF-POS-003": ("positive", "replay_accepted_tuple_independently", {"equal_detached_result_bytes", "no_revision_advance"}),
    "KF-POS-004": ("positive", "fork_then_first_publication", {"same_definition_accept_reject_behavior", "empty_current_preserved"}),
    "KF-NEG-002": ("negative", "mutate_all_current_and_fork_return_values", {"no_attached_state_change"}),
    "KF-POS-005": ("positive", "race", {"complete_committed_point_only", "no_mixed_state"}),
}
COPIED_STATE_CLAUSE = (
    "If a current state exists, the fork MUST copy exactly this current-state\n"
    "set: snapshot, canonical bytes, revision vector, sources, bindings, identity\n"
    "links, facts, services, capabilities, publication cursors, generation fences,\n"
    "and accepted current-tuple replay results."
)
NO_SHARED_MUTABLE_STORAGE_CLAUSE = (
    "The source and fork MUST share no mutable snapshot, canonical-byte, replay-result,\n"
    "map, or slice storage."
)

def main() -> None:
    kernel, acceptance = KERNEL.read_text(), ACCEPTANCE.read_text()
    required = (
        "func (k *PublicationKernel) Fork() (*PublicationKernel, error)",
        "stable v1 error identifier `invalid_value`",
        "read lock",
        "The fork MUST retain the same\nasset and registered pack-validation behavior",
        COPIED_STATE_CLAUSE,
        NO_SHARED_MUTABLE_STORAGE_CLAUSE,
        "it creates no restore, import, checkpoint,\npersistence, serialization",
        "same source, source epoch and\ndriver generation",
    )
    for token in required:
        if kernel.count(token) != 1:
            raise ValueError(f"kernel fork contract missing or repeated: {token!r}")
    for token in ("## PublicationKernel fork falsifiers", "KF-POS-001", "KF-POS-005", "nil receiver"):
        if token not in acceptance:
            raise ValueError(f"acceptance fork contract missing: {token!r}")
    data = json.loads(FIXTURE.read_text())
    if data.get("contract") != "helianthus.semantic.kernel.fork.acceptance/v1" or data.get("kernel_contract") != "helianthus.semantic.kernel/v1":
        raise ValueError("fork fixture contract pin differs")
    if data.get("signature") != "func (k *PublicationKernel) Fork() (*PublicationKernel, error)":
        raise ValueError("fork signature differs")
    if data.get("nil_receiver") != {"object": "nil", "error_id": "invalid_value", "subject": "publication kernel"}:
        raise ValueError("nil receiver contract differs")
    if data.get("non_goals") != ["restore", "import", "checkpoint", "persistence", "serialization", "gateway", "lifecycle_replacement"]:
        raise ValueError("fork non-goals differ")
    rows = data.get("scenarios")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise ValueError("fork scenario count differs")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "polarity", "setup", "operation", "expect"}:
            raise ValueError("fork scenario shape differs")
        ident = row["id"]
        if ident in seen or ident not in EXPECTED:
            raise ValueError("fork scenario id differs")
        seen.add(ident)
        polarity, operation, outcome = EXPECTED[ident]
        if row["polarity"] != polarity or row["operation"] != operation or set(row["expect"]) != outcome or len(row["expect"]) != len(outcome):
            raise ValueError(f"fork scenario differs: {ident}")
    print("PublicationKernel fork v1: PASS; 7 normative falsifiers")

if __name__ == "__main__":
    main()
