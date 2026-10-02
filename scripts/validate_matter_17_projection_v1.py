#!/usr/bin/env python3
"""Validate the pinned, fail-closed Matter 1.7 projection ledger."""

from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "api/v1/targets/matter-1.7-ballot-0.9-v1.json"
EVIDENCE = ROOT / "api/v1/targets/matter-1.7-ballot-0.9-source-evidence-v1.json"
METADATA = ROOT / "api/v1/pack-metadata-v1.json"
CONTRACT = "helianthus.gateway.matter-projection/v1"
KERNEL = "helianthus.semantic.kernel/v1"
TARGET = {
    "name": "matter.data-model",
    "version": "1.7-draft-ballot-0.9+29b4768a513cf566011ab8cd60df1bc495204953",
}
PINS = {
    "connectedhomeip": {
        "branch": "dm-0.9-1.7",
        "commit": "29b4768a513cf566011ab8cd60df1bc495204953",
    },
    "data_model": {
        "path": "data_model/1.7",
        "spec_sha": "214e40c9d51cfe89050eae68ca5b76238fcfa332",
        "spec_tag": "0.9-1.7-winter2027",
        "scraper": "alchemy v1.7.10+dirty",
    },
    "semreg": "089ed6ae9004",
    "docs_semantic_base": "2b3ca78",
    "packs": {
        "evse": "1.0.0",
        "infrastructure": "1.0.0",
        "pv": "1.0.0",
        "storage": "1.1.0",
        "thermal": "1.0.0",
    },
}
OUTCOMES = {
    "exact",
    "transformed",
    "withheld",
    "unrepresentable",
    "unsupported",
    "unknown",
}
KIND = {"field": "fact", "capability": "capability", "operation": "operation"}
POSITIVE_REF = {
    "pack": {"id": "helianthus.pack.evse", "version": "1.0.0"},
    "id": "evse.ac.current",
    "version": "1.0.0",
}
GUARDS = [
    "stale",
    "unavailable",
    "unqualified",
    "conflicted",
    "invalid",
    "revision_mismatch",
    "nonrepresentable_value",
    "multiple_or_ambiguous_source_keys",
]
OWNERSHIP = {
    "projection_contract": "Project-Helianthus/helianthus-docs-semantic",
    "kernel_and_packs": "Project-Helianthus/helianthus-semreg",
    "runtime_implementation": "Project-Helianthus/helianthus-ebusgateway",
}
NON_CLAIMS = [
    "matter_sdk_dependency",
    "matter_node",
    "endpoint_allocation",
    "commissioning",
    "fabric",
    "transport",
    "subscription",
    "command_dispatch",
    "access_control",
    "certification",
    "conformance",
    "live_device",
    "physical_result",
]
DEFINITION_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
UNKNOWN_REASON = "matter.unmapped.v1"
POSITIVE_REASON = "matter.phase_endpoint_identity_loss.v1"


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def key(ref):
    return (ref["pack"]["id"], ref["pack"]["version"], ref["id"], ref["version"])


def expected_items(metadata):
    items = []
    for pack in metadata["packs"]:
        for source_kind, group in (
            ("field", "fields"),
            ("capability", "capabilities"),
            ("operation", "operations"),
        ):
            for item in pack[group]:
                items.append(
                    {"ref": item["ref"], "kind": KIND[source_kind], "definition": item}
                )
    return sorted(items, key=lambda item: key(item["ref"]))


def expected_source(item):
    ref = item["ref"]
    source = {
        "kernel_contract": KERNEL,
        "requested": {
            "kind": item["kind"],
            "item_id": ref["id"],
            "item_version": ref["version"],
        },
        "revision_binding": {
            "snapshot_id": "exact_input_snapshot",
            "revisions": "exact_input_revisions",
        },
        "fact_keys": [],
    }
    if item["kind"] == "fact":
        source["fact_keys"] = [
            {
                "pack_id": ref["pack"]["id"],
                "pack_version": ref["pack"]["version"],
                "fact_id": ref["id"],
                "dimensions": {
                    "mode": "exact_runtime_fact_key",
                    "definition": item["definition"]["dimension"],
                },
            }
        ]
    return source


def validate_evidence(evidence):
    expected = {
        "contract": "helianthus.gateway.matter-source-evidence/v1",
        "target": TARGET,
        "public_source": {
            "repository": "AryaHassanli/connectedhomeip",
            "commit": PINS["connectedhomeip"]["commit"],
        },
        "xml": [
            {
                "path": "data_model/1.7/device_types/ElectricalSensor.xml",
                "blob_sha": "b6235fc64f44d4db2c42d05dc1e9b1f6f51dedfd",
            },
            {
                "path": "data_model/1.7/clusters/ElectricalPowerMeasurement.xml",
                "blob_sha": "3349108215d56ad61a950a3ad874ea9773499cb5",
            },
        ],
        "positive_tuple": {
            "device_type_id": 1296,
            "cluster_id": 144,
            "attribute_id": 5,
            "target_unit": "amperage-mA",
        },
        "boundary": "public path and blob identity only; no standard prose, conformance, runtime, or certification claim",
    }
    if evidence != expected:
        raise ValueError("public XML source evidence")


def validate(document):
    if set(document) != {
        "contract",
        "status",
        "mapping_revision",
        "target",
        "pins",
        "scope",
        "input_guards",
        "ownership",
        "non_claims",
        "rows",
    }:
        raise ValueError("document shape")
    if (
        document["contract"] != CONTRACT
        or document["status"] != "accepted_pinned_draft_projection_contract"
        or document["mapping_revision"] != 1
    ):
        raise ValueError("contract identity")
    if document["target"] != TARGET or document["pins"] != PINS:
        raise ValueError("target or pins")
    if document["scope"] != {
        "projection_items": ["fact", "capability", "operation"],
        "excluded": "service",
    }:
        raise ValueError("scope")
    if document["input_guards"] != {
        "whole_document_no_payload": GUARDS,
        "rule": "all guards and every transformed-value representability rule must pass before any target payload exists",
    }:
        raise ValueError("whole-document input guards")
    if document["ownership"] != OWNERSHIP or document["non_claims"] != NON_CLAIMS:
        raise ValueError("ownership or non-claims")
    expected, rows = expected_items(load(METADATA)), document["rows"]
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("projection coverage")
    if [(row.get("ref"), row.get("kind")) for row in rows] != [
        (item["ref"], item["kind"]) for item in expected
    ]:
        raise ValueError("canonical metadata key order or coverage")
    for row, item in zip(rows, expected):
        if row.get("source") != expected_source(item):
            raise ValueError("typed source and revision binding")
        if (
            row.get("disposition") not in OUTCOMES
            or not isinstance(row.get("reason"), str)
            or not 3 <= len(row["reason"]) <= 160
            or DEFINITION_ID.fullmatch(row["reason"]) is None
        ):
            raise ValueError("kernel v1 outcome or reason DefinitionID")
        loss = row.get("loss")
        valid_loss = (
            isinstance(loss, list)
            and bool(loss)
            and all(
                set(entry) == {"kind", "source_items", "description", "reversible"}
                and entry["kind"]
                in {
                    "unit",
                    "range",
                    "precision",
                    "time",
                    "symbol",
                    "provenance",
                    "identity",
                    "capability",
                    "operation",
                    "policy",
                }
                and entry["source_items"] == [item["ref"]["id"]]
                and isinstance(entry["description"], str)
                and isinstance(entry["reversible"], bool)
                for entry in loss
            )
        )
        if not valid_loss:
            raise ValueError("typed loss accounting")
        if item["ref"] == POSITIVE_REF:
            target = {
                "device_type_id": 1296,
                "cluster_id": 144,
                "attribute_id": 5,
                "value": {
                    "from_unit": "unit.ampere",
                    "to_unit": "amperage-mA",
                    "conversion": {
                        "algorithm": "exact_multiply",
                        "factor": 1000,
                        "require_integral_result": True,
                    },
                    "representation": {
                        "kind": "signed_integer",
                        "minimum": -4611686018427387904,
                        "maximum": 4611686018427387904,
                        "nullable": True,
                    },
                    "emission": {
                        "value_must_be_non_null": True,
                        "eligible_source_keys": 1,
                        "required_dimension": "evse.dimension.phase",
                    },
                    "on_nonrepresentable": "whole_document_no_payload",
                },
            }
            if (
                set(row)
                != {"ref", "kind", "disposition", "reason", "loss", "source", "target"}
                or row["disposition"] != "transformed"
                or row["reason"] != POSITIVE_REASON
                or row["target"] != target
            ):
                raise ValueError("pinned transformed EVSE observation")
        elif (
            set(row) != {"ref", "kind", "disposition", "reason", "loss", "source"}
            or row["disposition"] != "unknown"
            or row["reason"] != UNKNOWN_REASON
        ):
            raise ValueError("fail-closed nonpositive disposition")
    validate_evidence(load(EVIDENCE))


def main():
    validate(load(LEDGER))
    print(
        "Matter 1.7 projection v1: PASS; 127 kernel-v1 rows (1 transformed, 126 unknown)"
    )


if __name__ == "__main__":
    main()
