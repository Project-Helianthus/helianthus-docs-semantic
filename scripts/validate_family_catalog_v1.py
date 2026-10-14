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
RULES = [
    "`candidate`, `qualified`, `unsupported`, `unknown`, `rejected`, with the semantics",
    "no other member is allowed at any object level",
    "a repeated member name in any object is rejected",
    "Trailing data after the document is rejected",
    "It MUST equal the `Qualification` set below exactly",
    "MUST have `composition_verified=false` and MUST NOT carry any `gateway_composition` evidence entry",
    "Any `composition` other than `not_composed` requires `composition_verified=true`",
    "`composition_verified=true` requires such a `gateway_composition` entry",
    "MUST be `Project-Helianthus/helianthus-ebusgateway@` followed by the full 40-character commit SHA",
    "`Project-Helianthus/<repository>@<revision>` pins an immutable revision",
    "`Project-Helianthus/<repository>#<number>` names an issue or pull request thread",
    "new contract version",
    "insufficient evidence remains `unknown` or `candidate`",
    "is not excluded from scope",
    "is not fabricated",
]
SECTIONS = ["Unresolved questions", "Falsifiers"]


def section(text: str, heading: str) -> str:
    match = re.search(rf"^#+ {re.escape(heading)}\n(.*?)(?=^#+ |\Z)", text, flags=re.M | re.S)
    return match.group(1) if match else ""


def table_values(text: str, heading: str) -> list[str]:
    """Return the first-column code values of the table under a heading."""
    return re.findall(r"^\| `([^`]+)` \|", section(text, heading), flags=re.M)


def check(text: str) -> list[str]:
    errors: list[str] = []
    if CONTRACT not in text:
        errors.append("contract identifier missing")
    tables = {
        "Document": MEMBERS,
        "Family row": FAMILY_MEMBERS,
        "Composition": COMPOSITIONS,
        "Reason": REASONS,
    }
    for heading, expected in tables.items():
        if table_values(text, heading) != expected:
            errors.append(f"{heading} table differs from the contract")
    evidence = [v for v in table_values(text, "Evidence references") if v in EVIDENCE_MEMBERS]
    if evidence != EVIDENCE_MEMBERS:
        errors.append("evidence table differs from the contract")
    for state in STATES:
        if f"`{state}`" not in text:
            errors.append(f"state not named: {state}")
    flat = " ".join(text.split())
    for rule in RULES:
        if rule not in flat:
            errors.append(f"required statement missing: {rule}")
    for heading in SECTIONS:
        if not section(text, heading).strip():
            errors.append(f"section missing or empty: {heading}")
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
