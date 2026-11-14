#!/usr/bin/env python3
"""Tests of the element catalog schema against a synthetic catalog.

The catalog data does not exist yet, so every identifier below is synthetic.
"""
import copy
from pathlib import Path
import unittest

import json_schema_subset_v1 as subset

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = subset.load_json(ROOT / "api/v1/element-catalog-v1.schema.json")

SPEC = "https://example.org/specifications/synthetic-1"
ISSUE = "https://github.com/Project-Helianthus/helianthus-docs-semantic/issues/67"
PINNED = "https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/" + "0" * 40 + "/api/v1/kernel.md"
UNPINNED = "https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/kernel.md"
PACK = {"kind": "pack", "pack": {"id": "synthetic.pack", "version": "1.0.0"}}
CORE = {"kind": "core", "contract": "helianthus.semantic.kernel/v1"}
NATIVE = {"kind": "native", "repository": "https://github.com/Project-Helianthus/helianthus-docs-example"}

KIND = "resource.synthetic_equipment"
RELAYS = "relation.relays"
SUPPLIES = "synthetic.relation.supplies_load"
RESOURCE_DIM = "synthetic.dimension.load"
QUALIFIER_DIM = "synthetic.dimension.phase"
SERVICE = "synthetic.service.load"
SIGNED = "synthetic.field.power"
TWO_VENDORS = "synthetic.field.energy"
UNKNOWN = "synthetic.field.mode"
NATIVE_EXT = "native.synthetic.extension"
CAPABILITY = "synthetic.capability.limit"
OPERATION = "synthetic.operation.set_limit"
EFFECT = "synthetic.effect.limit"
EVIDENCE = "kernel.synthetic_evidence"
LIFECYCLE = "kernel.synthetic_lifecycle"
PRESENTATION = "synthetic.portal.load"
SCHEME = "scheme.synthetic_registry"
LENS = "lens.synthetic_energy"
PLANES = ("physical", "energy", "hydraulic", "control", "diagnostic", "provenance")
CORE_TYPES = ("contains", "groups", "supplies", "measures", "controls", "hosts", "relays")


def ref(owner, ident):
    return {"owner": owner, "id": ident, "version": "1.0.0"}


def admission(arm, *evidence):
    return {"arm": arm, "evidence": list(evidence) or [ISSUE if arm == "owner_decision" else SPEC]}


def entry(kind, owner, ident, attributes, arm="accepted_pack", planes=("energy",)):
    return {
        "ref": ref(owner, ident), "element_kind": kind, "disposition": "member",
        "planes": list(planes), "admission": admission(arm), "attributes": attributes,
    }


def outside(item, reason, tracking=None):
    item.update(disposition="unknown" if tracking else "unsupported", planes=[], reason=reason)
    if tracking:
        item["tracking"] = tracking
    return item


def relation_attributes(core_type, **extra):
    return {
        "core_type": core_type, "orientation": "as_core", "from_kinds": [KIND], "to_kinds": [KIND],
        "cardinality": "many_to_many", "over_time": False, "basis_classes": ["configuration"], **extra,
    }


def fact_attributes(value_kind, subject, direction, **extra):
    aggregation = "member" if value_kind == "quantity" else "not_applicable"
    return {"value_kind": value_kind, "subject": subject, "aggregation": aggregation, "direction": direction, **extra}


def structure_elements():
    endpoints = {"from": ref(PACK, RESOURCE_DIM), "to": ref(PACK, RESOURCE_DIM)}
    return [
        entry("resource_kind", CORE, KIND, {"anchor_class": "equipment"}, "matter_baseline", PLANES[:2]),
        entry("relation", CORE, RELAYS, relation_attributes("relays"), "eebus", ["provenance"]),
        entry("relation", PACK, SUPPLIES,
              relation_attributes("supplies", medium="electrical", endpoint_dimensions=endpoints)),
        entry("dimension", PACK, RESOURCE_DIM, {"role": "resource", "resource_kind": KIND}),
        entry("dimension", PACK, QUALIFIER_DIM, {"role": "qualifier"}),
        entry("service", PACK, SERVICE, {"fact_key_dimension": ref(PACK, RESOURCE_DIM), "subject_kind": KIND}),
    ]


def fact_elements():
    resolved = {"status": "resolved", "dimension": ref(PACK, RESOURCE_DIM), "kind": KIND}
    unresolved = {"status": "unresolved", "qualifier_dimension": ref(PACK, QUALIFIER_DIM)}
    two_vendors = entry("fact", PACK, TWO_VENDORS, fact_attributes("quantity", resolved, "non_negative"),
                        "two_vendors")
    two_vendors["admission"]["research_report"] = ISSUE
    native = entry("fact", NATIVE, NATIVE_EXT, fact_attributes("text", {"status": "unresolved"}, "not_applicable"),
                   "eebus")
    return [
        entry("fact", PACK, SIGNED,
              fact_attributes("quantity", resolved, "signed", sign_reference="native_convention")),
        two_vendors,
        outside(entry("fact", PACK, UNKNOWN, fact_attributes("symbol", unresolved, "not_applicable")),
                "subject_not_established", ISSUE),
        outside(native, "not_admitted", ISSUE),
    ]


def control_elements():
    pinned = entry("effect_rule", PACK, EFFECT, {"operation": ref(PACK, OPERATION), "fact": ref(PACK, SIGNED)})
    pinned["admission"]["evidence"] = [PINNED, SPEC]
    return [
        entry("capability", PACK, CAPABILITY, {"service": ref(PACK, SERVICE), "operation": ref(PACK, OPERATION)},
              planes=["control"]),
        entry("operation", PACK, OPERATION, {
            "capability": ref(PACK, CAPABILITY), "argument": ref(PACK, SIGNED), "effect_rule": ref(PACK, EFFECT),
        }, planes=["control"]),
        pinned,
        entry("evidence_state", CORE, EVIDENCE, {"kernel_type": "SyntheticEvidence", "values": ["fresh", "stale"]},
              "accepted_kernel", ["provenance"]),
        entry("lifecycle_state", CORE, LIFECYCLE, {"kernel_type": "SyntheticLifecycle", "values": ["current"]},
              "owner_decision", ["diagnostic", "provenance"]),
        outside(entry("presentation", PACK, PRESENTATION, {"target": "portal"}), "target_vocabulary_only"),
    ]


def catalog():
    """Return a synthetic catalog that covers every kind, disposition and record."""
    return {
        "contract": "helianthus.semantic.element-catalog/v1",
        "kernel_contract": "helianthus.semantic.kernel/v1",
        "status": "draft",
        "catalog_order": "owner kind, pack id, pack version, element id, element version as canonical UTF-8 byte sequence",
        "planes": [{"id": plane, "question": f"Synthetic {plane} question?", "admission": admission("owner_decision")}
                   for plane in PLANES],
        "core_relation_types": [{
            "id": core_type, "reads": f"synthetic {core_type}", "structure": "graph", "allowed_planes": list(PLANES),
            "required_planes": [], "admission": admission("matter_baseline"),
        } for core_type in CORE_TYPES],
        "identification_schemes": [{
            "id": SCHEME, "issuer_registry": "registry.synthetic", "token_form": "synthetic token",
            "admission": admission("public_registry"),
        }],
        "elements": structure_elements() + fact_elements() + control_elements(),
        "lenses": [{
            "id": LENS, "question": "Synthetic lens?", "planes": ["energy"], "root_kinds": [KIND],
            "relations": [ref(PACK, SUPPLIES)], "max_depth": 4,
        }],
    }


def _item(items, token):
    for item in items:
        if token in (item.get("id"), item.get("ref", {}).get("id")):
            return item
    raise KeyError(token)


def mutated(*operations):
    """Apply (path, value) operations to a fresh catalog; a value of DROP deletes."""
    document = catalog()
    for path, value in operations:
        node = document
        for token in path[:-1]:
            node = _item(node, token) if isinstance(node, list) else node[token]
        if value is DROP:
            del node[path[-1]]
        else:
            node[path[-1]] = copy.deepcopy(value)
    return document


DROP = object()


def at(*path):
    return ("elements",) + path


# probe name -> (operations, schema pointer that must appear in an error)
PROBES = {
    "member without planes": ([(at(SIGNED, "planes"), [])], "element/allOf/0/then/properties/planes/minItems"),
    "unknown without tracking": ([(at(UNKNOWN, "tracking"), DROP)], "element/allOf/2/then/required"),
    "unsupported with planes": ([(at(PRESENTATION, "planes"), ["control"])], "element/allOf/1/then/properties/planes"),
    "member with a reason": ([(at(SIGNED, "reason"), "synthetic_reason")], "element/allOf/0/then/not"),
    "supplies without medium": ([(at(SUPPLIES, "attributes", "medium"), DROP)], "relationAttributes/then/required"),
    "contains with medium": ([(at(SUPPLIES, "attributes", "core_type"), "contains")], "relationAttributes/else/not"),
    "qualifier dimension with a resource kind": (
        [(at(QUALIFIER_DIM, "attributes", "resource_kind"), KIND)], "dimensionAttributes/else/not"),
    "plane member on a record": ([(at(SIGNED, "attributes", "planes"), ["energy"])],
                                 "factAttributes/additionalProperties"),
    "resource kind owned by a pack": ([(at(KIND, "ref", "owner"), PACK)], "element/allOf/7/then/properties/ref"),
    "presentation as member": ([(at(PRESENTATION, "disposition"), "member"), (at(PRESENTATION, "reason"), DROP),
                                (at(PRESENTATION, "planes"), ["control"])], "element/allOf/16/then"),
    "native extension as member": ([(at(NATIVE_EXT, "disposition"), "member"), (at(NATIVE_EXT, "reason"), DROP),
                                    (at(NATIVE_EXT, "tracking"), DROP), (at(NATIVE_EXT, "planes"), ["diagnostic"])],
                                   "element/allOf/3/then"),
    "projection outcome as disposition": ([(at(SIGNED, "disposition"), "withheld")],
                                          "element/properties/disposition/enum"),
    "two_vendors without report": ([(at(TWO_VENDORS, "admission", "research_report"), DROP)],
                                   "admission/allOf/0/then/required"),
    "element without admission": ([(at(SIGNED, "admission"), DROP)], "#/$defs/element/required"),
    "core relation type without admission": ([(("core_relation_types", "relays", "admission"), DROP)],
                                             "#/$defs/coreRelationType/required"),
    "kernel state on the accepted_pack arm": ([(at(EVIDENCE, "admission"), admission("accepted_pack"))],
                                              "element/allOf/4/then"),
    "core relation on the accepted_pack arm": ([(at(RELAYS, "admission", "arm"), "accepted_pack")],
                                               "element/allOf/5/then"),
    "pack element on the owner_decision arm": ([(at(SIGNED, "admission"), admission("owner_decision"))],
                                               "element/allOf/6/then"),
    "plane on the accepted_pack arm": ([(("planes", "energy", "admission"), admission("accepted_pack"))],
                                       "plane/properties/admission/allOf/1"),
    "signed without sign reference": ([(at(SIGNED, "attributes", "sign_reference"), DROP)],
                                      "factAttributes/allOf/0/then/required"),
    "unsigned with sign reference": ([(at(TWO_VENDORS, "attributes", "sign_reference"), "native_convention")],
                                     "factAttributes/allOf/0/else/not"),
    "symbol fact with a direction": ([(at(UNKNOWN, "attributes", "direction"), "non_negative")],
                                     "factAttributes/allOf/1/then/properties/direction/const"),
    "research report on a non-two_vendors arm": ([(at(SIGNED, "admission", "research_report"), ISSUE)],
                                                 "admission/allOf/0/else/not"),
    "unpinned evidence": ([(at(SIGNED, "admission", "evidence"), [UNPINNED])], "publicUrl/pattern"),
    "scheme on the owner_decision arm": ([(("identification_schemes", SCHEME, "admission"),
                                           admission("owner_decision"))],
                                         "identificationScheme/properties/admission/allOf/1"),
    "element on the public_registry arm": ([(at(SIGNED, "admission", "arm"), "public_registry")],
                                           "element/allOf/17"),
    "catalog without the scheme list": ([(("identification_schemes",), DROP)], "#/required"),
    "lens with depth 0": ([(("lenses", LENS, "max_depth"), 0)], "lens/properties/max_depth/minimum"),
}

# JSON pointer of every if node -> operations of a probe that only that conditional rejects
CONDITIONAL_PROBES = {
    "#/$defs/admission/allOf/0/if": PROBES["two_vendors without report"][0],
    "#/$defs/admission/allOf/1/if": [(("planes", "energy", "admission", "evidence"), [PINNED])],
    "#/$defs/relationAttributes/if": PROBES["supplies without medium"][0],
    "#/$defs/dimensionAttributes/if": PROBES["qualifier dimension with a resource kind"][0],
    "#/$defs/factAttributes/allOf/0/if": PROBES["signed without sign reference"][0],
    "#/$defs/factAttributes/allOf/1/if": PROBES["symbol fact with a direction"][0],
    "#/$defs/element/allOf/0/if": PROBES["member without planes"][0],
    "#/$defs/element/allOf/1/if": PROBES["unsupported with planes"][0],
    "#/$defs/element/allOf/2/if": PROBES["unknown without tracking"][0],
    "#/$defs/element/allOf/3/if": PROBES["native extension as member"][0],
    "#/$defs/element/allOf/4/if": PROBES["kernel state on the accepted_pack arm"][0],
    "#/$defs/element/allOf/5/if": PROBES["core relation on the accepted_pack arm"][0],
    "#/$defs/element/allOf/6/if": PROBES["pack element on the owner_decision arm"][0],
    "#/$defs/element/allOf/7/if": PROBES["resource kind owned by a pack"][0],
    "#/$defs/element/allOf/8/if": [(at(SUPPLIES, "attributes", "orientation"), DROP)],
    "#/$defs/element/allOf/9/if": [(at(RESOURCE_DIM, "attributes", "role"), DROP)],
    "#/$defs/element/allOf/10/if": [(at(SERVICE, "attributes", "subject_kind"), DROP)],
    "#/$defs/element/allOf/11/if": [(at(SIGNED, "attributes", "subject"), DROP)],
    "#/$defs/element/allOf/12/if": [(at(CAPABILITY, "attributes", "service"), DROP)],
    "#/$defs/element/allOf/13/if": [(at(OPERATION, "attributes", "effect_rule"), DROP)],
    "#/$defs/element/allOf/14/if": [(at(EFFECT, "attributes", "fact"), DROP)],
    "#/$defs/element/allOf/15/if": [(at(EVIDENCE, "attributes", "kernel_type"), "synthetic_evidence")],
    "#/$defs/element/allOf/16/if": PROBES["presentation as member"][0],
}


def if_pointers(node, pointer="#"):
    """Return the JSON pointer of every if node in a schema."""
    found = []
    if isinstance(node, dict):
        found.extend([pointer + "/if"] if "if" in node else [])
        for key in sorted(node):
            found.extend(if_pointers(node[key], f"{pointer}/{key}"))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            found.extend(if_pointers(item, f"{pointer}/{index}"))
    return found


def without_conditional(pointer):
    """Return a copy of the schema with the if/then/else of one node removed."""
    schema = copy.deepcopy(SCHEMA)
    node = schema
    for token in pointer.split("/")[1:-1]:
        node = node[int(token)] if isinstance(node, list) else node[token]
    for key in ("if", "then", "else"):
        node.pop(key, None)
    return schema


class PublishedSchemaTest(unittest.TestCase):
    def test_schema_uses_only_the_supported_subset(self):
        subset.check_schema(SCHEMA)

    def test_schema_identity(self):
        self.assertEqual(SCHEMA["title"], "Helianthus element catalog v1")
        self.assertEqual(SCHEMA["properties"]["contract"]["const"], "helianthus.semantic.element-catalog/v1")
        self.assertTrue(SCHEMA["$id"].endswith("/blob/main/api/v1/element-catalog-v1.schema.json"))

    def test_synthetic_catalog_is_valid(self):
        self.assertEqual(subset.errors(catalog(), SCHEMA), [])

    def test_synthetic_catalog_covers_the_shape(self):
        document = catalog()
        elements = document["elements"]
        kinds = SCHEMA["$defs"]["element"]["properties"]["element_kind"]["enum"]
        self.assertEqual(sorted({item["element_kind"] for item in elements}), sorted(kinds))
        self.assertEqual({item["disposition"] for item in elements}, {"member", "unsupported", "unknown"})
        facts = [item["attributes"] for item in elements if item["element_kind"] == "fact"]
        self.assertEqual({fact["subject"]["status"] for fact in facts}, {"resolved", "unresolved"})
        self.assertIn("native_convention", [fact.get("sign_reference") for fact in facts])
        self.assertEqual(_item(elements, RELAYS)["attributes"]["core_type"], "relays")
        self.assertTrue(document["identification_schemes"] and document["lenses"])


class NegativeProbeTest(unittest.TestCase):
    def test_probe_count(self):
        self.assertEqual(len(PROBES), 28)

    def test_each_probe_rejected_for_its_rule(self):
        for name, (operations, location) in PROBES.items():
            with self.subTest(probe=name):
                found = subset.errors(mutated(*operations), SCHEMA)
                self.assertTrue(found, name)
                self.assertTrue(any(location in message for message in found), found)


class ConditionalTest(unittest.TestCase):
    def test_every_conditional_has_a_probe(self):
        pointers = if_pointers(SCHEMA)
        self.assertEqual(len(pointers), len(set(pointers)))
        self.assertEqual(sorted(pointers), sorted(CONDITIONAL_PROBES))

    def test_each_conditional_does_the_work(self):
        for pointer in if_pointers(SCHEMA):
            with self.subTest(pointer=pointer):
                self.assertIn(pointer, CONDITIONAL_PROBES, "conditional without a probe")
                document = mutated(*CONDITIONAL_PROBES[pointer])
                self.assertTrue(subset.errors(document, SCHEMA))
                self.assertEqual(subset.errors(document, without_conditional(pointer)), [])


if __name__ == "__main__":
    unittest.main()
