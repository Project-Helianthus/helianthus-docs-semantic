#!/usr/bin/env python3
"""Validate the pinned, fail-closed Matter 1.7 projection ledger."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "api/v1/targets/matter-1.7-ballot-0.9-v1.json"
METADATA = ROOT / "api/v1/pack-metadata-v1.json"
CONTRACT = "helianthus.gateway.matter-projection/v1"
TARGET = {"name": "matter.data-model", "version": "1.7-draft-ballot-0.9+29b4768a513cf566011ab8cd60df1bc495204953"}
PINS = {
    "connectedhomeip": {"branch": "dm-0.9-1.7", "commit": "29b4768a513cf566011ab8cd60df1bc495204953"},
    "data_model": {"path": "data_model/1.7", "spec_sha": "214e40c9d51cfe89050eae68ca5b76238fcfa332", "spec_tag": "0.9-1.7-winter2027", "scraper": "alchemy v1.7.10+dirty"},
    "semreg": "089ed6ae9004",
    "docs_semantic_base": "2b3ca78",
    "packs": {"evse": "1.0.0", "infrastructure": "1.0.0", "pv": "1.0.0", "storage": "1.1.0", "thermal": "1.0.0"},
}
UNKNOWN_REASON = "no accepted exact pinned Matter mapping for this semantic item"
UNKNOWN_LOSS = ["no target lookup", "no inferred fallback", "no operation or control authority"]
POSITIVE_REF = {"pack": {"id": "helianthus.pack.evse", "version": "1.0.0"}, "id": "evse.ac.current", "version": "1.0.0"}
POSITIVE_TARGET = {"device_type_id": 1296, "cluster_id": 144, "attribute_id": 5, "transform": {"from_unit": "unit.ampere", "to_unit": "milliamperes", "factor": 1000}}


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def expected_items(metadata):
    items = []
    for pack in metadata["packs"]:
        for kind, group in (("field", "fields"), ("capability", "capabilities"), ("operation", "operations")):
            for item in pack[group]:
                items.append({"ref": item["ref"], "kind": kind})
    return items


def validate(document):
    if set(document) != {"contract", "status", "mapping_revision", "target", "pins", "scope", "rows"}:
        raise ValueError("document shape")
    if document["contract"] != CONTRACT or document["status"] != "accepted_pinned_draft_projection_contract" or document["mapping_revision"] != 1:
        raise ValueError("contract identity")
    if document["target"] != TARGET or document["pins"] != PINS:
        raise ValueError("target or pins")
    if document["scope"] != {"projection_items": ["field", "capability", "operation"], "excluded": "service"}:
        raise ValueError("scope")
    expected = expected_items(load(METADATA))
    rows = document["rows"]
    if not isinstance(rows, list) or [{"ref": row.get("ref"), "kind": row.get("kind")} for row in rows] != expected:
        raise ValueError("each accepted field capability and operation exactly once")
    positive_count = 0
    for row in rows:
        if row["ref"] == POSITIVE_REF:
            positive_count += 1
            if set(row) != {"ref", "kind", "disposition", "reason", "loss", "target"} or row["kind"] != "field" or row["disposition"] != "candidate_read_only_transformed_observation" or row["target"] != POSITIVE_TARGET:
                raise ValueError("pinned EVSE transformed observation")
            if not isinstance(row["reason"], str) or not row["reason"] or not isinstance(row["loss"], list) or not row["loss"]:
                raise ValueError("positive observation boundary")
        elif set(row) != {"ref", "kind", "disposition", "reason", "loss"} or row["disposition"] != "unknown_fail_closed" or row["reason"] != UNKNOWN_REASON or row["loss"] != UNKNOWN_LOSS:
            raise ValueError("unknown fail-closed disposition")
    if positive_count != 1 or len(rows) != 127:
        raise ValueError("projection coverage")


def main():
    validate(load(LEDGER))
    print("Matter 1.7 projection v1: PASS; 127 rows (1 transformed candidate, 126 unknown fail-closed)")


if __name__ == "__main__":
    main()
