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
VECTORS = ROOT / "api/v1/acceptance-vectors.json"

TYPE_HEADING = re.compile(r"^### Type: ([A-Za-z][A-Za-z0-9]*)$", re.MULTILINE)
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


def main() -> None:
    kernel_text = KERNEL.read_text(encoding="utf-8")
    acceptance_text = ACCEPTANCE.read_text(encoding="utf-8")
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
    documented_errors = heading_set(acceptance_text, ERROR_HEADING, "error")
    documented_coverage = heading_set(
        acceptance_text, COVERAGE_HEADING, "coverage"
    )

    if set(error_ids) != documented_errors:
        raise ValueError("vector error_ids do not match documented error headings")
    if set(coverage_ids) != documented_coverage:
        raise ValueError("vector coverage_ids do not match documented coverage headings")

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

    print(
        f"kernel v1 documents consistent: {len(types)} types, "
        f"{len(error_ids)} errors, {len(coverage_ids)} coverage areas, "
        f"{len(vectors)} vectors"
    )


if __name__ == "__main__":
    main()
