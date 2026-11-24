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
    "family_id", "name", "native_owner", "semantic_pack", "further_semantic_packs",
    "state", "composition", "composition_verified", "verification", "module",
    "version", "reason", "evidence",
]
OPTIONAL_MEMBERS = {"further_semantic_packs", "module", "version"}
SEMANTIC_PACK_ROW = (
    "| `semantic_pack` | string | Exact `PackRef` of the accepted capability pack"
    " the family maps to, or empty. |"
)
FAMILY_ROW_RULES = [
    "Every member except `further_semantic_packs`, `module` and `version` is required",
]
PACKS_SECTION = "Packs of a row"
PACK_RULES = [
    "`further_semantic_packs` is an array of exact `PackRef` strings, in the same form as"
    " `semantic_pack`, with no fixed count: a row names every accepted pack it maps to",
    "Its entries are unique, and no entry equals `semantic_pack`",
    "It is allowed only when `semantic_pack` is non-empty",
    "It is omitted when the family has no further pack",
    "A present empty array is rejected",
    "Canonical order is ascending byte order of the `PackRef` strings",
    "The entries are sorted in canonical order and `semantic_pack` sorts before every entry",
    "No pack is primary: `semantic_pack` is the first in canonical order",
    "for every accepted mapping gate of a family, the row's packs (`semantic_pack`"
    " and every entry of `further_semantic_packs`) include the gate's pack",
]
PACK_FORBIDDEN = [
    "1 through 4",
    "The bound follows from the five accepted capability packs",
]
STATE_SECTION = "State"
STATE_RULES = [
    "A state value keeps its meaning: `unsupported` and `rejected` forbid a value,"
    " and `unknown` stays distinct from a known capability",
    "An already promoted element retains its actual candidate state, `unknown` included",
    "A candidate state, `unsupported` and `rejected` included, is never by itself a promotion veto",
    "a known SemReg element whose candidate becomes `unsupported` with no value validates as"
    " promoted when its value-presence requirements hold",
    "the separate capability and projection rules stay",
    "A `qualified` row has the reason `declared_by_specification` and at least one evidence"
    " entry of kind `specification`",
]
STATE_FORBIDDEN = [
    "forbid a value and promotion",
    "cannot be promoted or satisfy a capability",
]
CONSUMER_RULES = [
    "a missing required family is rejected, and a valid additional family that the list does"
    " not name is admitted",
    "an unknown member of a Family object, which stays rejected",
    "with no fixed count",
]
EVIDENCE_MEMBERS = ["owner", "kind", "locator", "statement"]
STATES = ["candidate", "qualified", "unsupported", "unknown", "rejected"]
COMPOSITIONS = ["composed", "composed_legacy", "provider_local", "not_composed"]
VERIFICATIONS = ["tested_on_hardware", "not_tested_on_hardware"]
REASONS = [
    "declared_by_specification", "specification_conflict", "semantic_mapping_unknown",
    "unknown_pending_normative_source", "no_producer",
]
RULES = [
    "`candidate`, `qualified`, `unsupported`, `unknown`, `rejected`, with the semantics",
    "no other member is allowed at any object level",
    "a repeated member name in any object is rejected",
    "Trailing data after the document is rejected",
    "It MUST equal the `Qualification` set below exactly",
    "MUST have `composition_verified=false` and MUST NOT carry `module` or `version`",
    "Any `composition` other than `not_composed` requires `composition_verified=true`"
    " and both `module` and `version`",
    "`composition_verified=true` requires both `module` and `version`",
    "A `hardware_test_record` entry cites a public hardware test record in a project repository",
    "it never raises or lowers qualification, promotion or an operation",
    "The row carries at least one `hardware_test_record` evidence entry",
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


def missing(text: str, rules: list[str]) -> list[str]:
    """Return the rules not stated in the whitespace-normalized text."""
    flat = " ".join(text.split())
    return [rule for rule in rules if rule not in flat]


def check_packs(text: str) -> list[str]:
    """Check the semantic_pack row and the rules for further_semantic_packs."""
    family_row = section(text, "Family row")
    errors = [] if SEMANTIC_PACK_ROW in family_row.splitlines() else ["semantic_pack row differs from the contract"]
    errors += [f"family row statement missing: {rule}" for rule in missing(family_row, FAMILY_ROW_RULES)]
    packs = section(text, PACKS_SECTION)
    errors += [f"packs-of-a-row statement missing: {rule}" for rule in missing(packs, PACK_RULES)]
    errors += [f"packs-of-a-row statement restored: {rule}" for rule in present(packs, PACK_FORBIDDEN)]
    return errors


def present(text: str, statements: list[str]) -> list[str]:
    """Return the statements found in the whitespace-normalized text."""
    flat = " ".join(text.split())
    return [statement for statement in statements if statement in flat]


def check_state(text: str) -> list[str]:
    """Check the State section and the consumer rule against the old bans."""
    state = section(text, STATE_SECTION)
    errors = [f"state statement missing: {rule}" for rule in missing(state, STATE_RULES)]
    errors += [f"state statement restored: {rule}" for rule in present(state, STATE_FORBIDDEN)]
    errors += [f"consumer rule missing: {rule}" for rule in missing(section(text, "Family row"), CONSUMER_RULES)]
    return errors


def check_row_packs(row: dict, accepted: set[str]) -> list[str]:
    """Apply the pack rules of a Family row to one synthetic row."""
    primary = row.get("semantic_pack", "")
    packs = [primary] + list(row.get("further_semantic_packs", []))
    errors = [f"pack not accepted: {pack}" for pack in packs if pack and pack not in accepted]
    if "further_semantic_packs" in row:
        if not primary:
            errors.append("further packs follow an empty semantic_pack")
        if not row["further_semantic_packs"]:
            errors.append("further packs present but empty")
        if len(set(packs)) != len(packs):
            errors.append("pack repeated or equal to semantic_pack")
        if packs != sorted(packs):
            errors.append("packs not in canonical order")
    return errors


def check_row_state(row: dict) -> list[str]:
    """Apply the verification, qualification and composition rules to one row."""
    kinds = {entry.get("kind") for entry in row.get("evidence", [])}
    errors = []
    if row.get("verification") not in VERIFICATIONS:
        errors.append("verification outside its values")
    if row.get("verification") == "tested_on_hardware" and "hardware_test_record" not in kinds:
        errors.append("tested_on_hardware without hardware_test_record evidence")
    if row.get("state") == "qualified" and (
        row.get("reason") != "declared_by_specification" or "specification" not in kinds
    ):
        errors.append("qualified without declared_by_specification and specification evidence")
    claimed = row.get("composition") != "not_composed"
    both = bool(row.get("module")) and bool(row.get("version"))
    if claimed and not (row.get("composition_verified") is True and both):
        errors.append("claimed composition without verification, module and version")
    if not claimed and (row.get("composition_verified") is not False or row.get("module") or row.get("version")):
        errors.append("not_composed with verification, module or version")
    return errors


def check_catalog(document: dict, pinned: list[str]) -> list[str]:
    """Apply the consumer rule: pinned families required, additional valid families admitted."""
    rows = document.get("families", [])
    errors = [f"missing required family: {name}" for name in pinned if name not in [r.get("family_id") for r in rows]]
    for row in rows:
        required = set(FAMILY_MEMBERS) - OPTIONAL_MEMBERS
        errors += [f"unknown family member: {name}" for name in sorted(set(row) - set(FAMILY_MEMBERS))]
        errors += [f"missing family member: {name}" for name in sorted(required - set(row))]
    return errors


def check(text: str) -> list[str]:
    errors: list[str] = []
    if CONTRACT not in text:
        errors.append("contract identifier missing")
    tables = {
        "Document": MEMBERS,
        "Family row": FAMILY_MEMBERS,
        "Composition": COMPOSITIONS,
        "Verification": VERIFICATIONS,
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
    errors.extend(check_packs(text))
    errors.extend(check_state(text))
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
