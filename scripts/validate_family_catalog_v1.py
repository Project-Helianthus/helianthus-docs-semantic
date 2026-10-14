#!/usr/bin/env python3
"""Check that the family-catalog/v1 contract page states its exact vocabularies."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "api/v1/family-catalog-v1.md"

CONTRACT = "helianthus.semreg.family-catalog/v1"
MEMBERS = ["contract", "semantic_docs_pin", "states", "families"]
FAMILY_MEMBERS = [
    "family_id", "name", "native_owner", "semantic_pack", "state",
    "composition", "composition_verified", "reason", "evidence",
]
EVIDENCE_MEMBERS = ["owner", "kind", "locator", "statement"]
STATES = ["candidate", "qualified", "unsupported", "unknown", "rejected"]
COMPOSITIONS = ["composed", "composed_legacy", "provider_local", "not_composed"]
REASONS = [
    "offline_profile_only", "offline_mapping_gate_only", "family_compatible_offline",
    "no_admissible_profile", "qualification_test_ready_offline", "evidence_blocked",
    "no_go_missing_evidence", "offline_replay_only", "semantic_mapping_unknown",
    "legacy_layer_composition", "unknown_pending_std_01", "no_producer",
]
PHRASES = [
    "gateway_composition",
    "full 40-character commit SHA",
    "composition_verified=true",
    "unverified",
    "new contract version",
    "insufficient evidence remains `unknown` or `candidate`",
    "is not excluded from scope",
    "is not fabricated",
]


def table_values(text: str, heading: str) -> list[str]:
    """Return the first-column code values of the table under a heading."""
    section = text.split(f"## {heading}", 1)[1].split("\n## ", 1)[0]
    return re.findall(r"^\| `([a-z0-9_]+)` \|", section, flags=re.M)


def check(text: str) -> list[str]:
    errors: list[str] = []
    if CONTRACT not in text:
        errors.append("contract identifier missing")
    for name in MEMBERS + FAMILY_MEMBERS + EVIDENCE_MEMBERS:
        if f"`{name}`" not in text:
            errors.append(f"member not documented: {name}")
    for state in STATES:
        if f"`{state}`" not in text:
            errors.append(f"state not named: {state}")
    if table_values(text, "Reason") != REASONS:
        errors.append("reason table differs from the contract vocabulary")
    if [v for v in table_values(text, "Composition") if v in COMPOSITIONS] != COMPOSITIONS:
        errors.append("composition table differs from the contract vocabulary")
    flat = " ".join(text.split())
    for phrase in PHRASES:
        if phrase not in flat:
            errors.append(f"required statement missing: {phrase}")
    return errors


def main() -> int:
    errors = check(PAGE.read_text(encoding="utf-8"))
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("family catalog v1 contract page ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
