#!/usr/bin/env python3
"""Focused mutation controls for the Matter 1.7 projection ledger."""

from __future__ import annotations
import copy, importlib.util, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "matter_17_projection", ROOT / "scripts/validate_matter_17_projection_v1.py"
)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def rejects(document, label, mutate):
    candidate = copy.deepcopy(document)
    mutate(candidate)
    try:
        validator.validate(candidate)
    except ValueError:
        print(f"{label}: REJECTED")
        return
    raise AssertionError(f"{label}: accepted")


def main():
    document = validator.load(validator.LEDGER)
    validator.validate(document)
    print("baseline_exact_ledger: PASS")
    positive = next(
        i
        for i, row in enumerate(document["rows"])
        if row["ref"] == validator.POSITIVE_REF
    )
    rejects(
        document,
        "field_kind_not_kernel_fact",
        lambda d: d["rows"][0].update(kind="field"),
    )
    rejects(
        document,
        "non_kernel_outcome",
        lambda d: d["rows"][0].update(disposition="unknown_fail_closed"),
    )
    rejects(
        document,
        "invalid_reason_definition_id",
        lambda d: d["rows"][0].update(reason="not a Definition ID"),
    )
    rejects(
        document,
        "missing_fact_key_binding",
        lambda d: d["rows"][positive]["source"]["fact_keys"][0].pop("dimensions"),
    )
    rejects(
        document,
        "revision_binding_drift",
        lambda d: d["rows"][positive]["source"]["revision_binding"].update(
            revisions="best_effort"
        ),
    )
    rejects(
        document,
        "fractional_milliamperes_allowed",
        lambda d: d["rows"][positive]["target"]["value"]["conversion"].update(
            require_integral_result=False
        ),
    )
    rejects(
        document,
        "target_nullability_drift",
        lambda d: d["rows"][positive]["target"]["value"]["representation"].update(
            nullable=False
        ),
    )
    rejects(
        document,
        "partial_payload_on_range_error",
        lambda d: d["rows"][positive]["target"]["value"].update(
            on_nonrepresentable="omit_attribute"
        ),
    )
    rejects(
        document,
        "guard_removed",
        lambda d: d["input_guards"]["whole_document_no_payload"].pop(),
    )
    rejects(document, "ownership_removed", lambda d: d.pop("ownership"))
    rejects(document, "non_claim_removed", lambda d: d["non_claims"].pop())
    rejects(
        document,
        "ambiguous_source_allowed",
        lambda d: d["rows"][positive]["target"]["value"]["emission"].update(
            eligible_source_keys=2
        ),
    )
    rejects(
        document,
        "old_grouped_order",
        lambda d: d["rows"].__setitem__(
            0,
            d["rows"].pop(
                next(
                    i for i, row in enumerate(d["rows"]) if row["kind"] == "capability"
                )
            ),
        ),
    )
    try:
        validator.validate_evidence({**validator.load(validator.EVIDENCE), "xml": []})
    except ValueError:
        print("public_blob_drift: REJECTED")
    else:
        raise AssertionError("public_blob_drift: accepted")
    print("focused_mutations: 14 REJECTED")


if __name__ == "__main__":
    main()
