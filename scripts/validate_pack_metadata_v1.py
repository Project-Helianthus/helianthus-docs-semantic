#!/usr/bin/env python3
"""Validate the immutable v1 view exported from accepted pack contracts."""
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "api/v1/pack-metadata-v1.json"
SOURCES = ("api/v1/packs/thermal-hvac-acceptance-vectors.json", "api/v1/packs/pv-inverter-acceptance-vectors.json", "api/v1/packs/storage-bms-acceptance-vectors.json", "api/v1/packs/evse-acceptance-vectors.json", "api/v1/packs/infrastructure-acceptance-vectors.json")
STORAGE_TABLES = ROOT / "api/v1/packs/storage-bms-contract-tables.json"

def pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError("duplicate JSON key")
        result[key] = value
    return result
def load(path): return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
def ref(pack, identifier): return {"pack": pack, "id": identifier, "version": pack["version"]}
def key(value): return (value["pack"]["id"], value["pack"]["version"], value["id"], value["version"])

def source_metadata(path):
    catalog = load(ROOT / path)["catalog"]; pack = catalog["pack"]; definitions = catalog.get("definitions", {})
    if pack["id"] == "helianthus.pack.storage":
        tables = load(STORAGE_TABLES)
        fields, services, capabilities, operations = tables["field_specs"], tables["services"], tables["capabilities"], tables["operations"]
    else:
        fields, services, capabilities, operations = definitions["fields"], definitions["services"], definitions["capabilities"], definitions["operations"]
    capability_by_id = {item["id"]: item for item in capabilities}
    fields = [{"ref": ref(pack, item["id"]), "canonical_unit": ref(pack, item["unit"]) if item.get("unit") else None, "dimension": ref(pack, item["dimension"])} for item in fields]
    services = [{"ref": ref(pack, item["id"]), "fact_key_dimension": ref(pack, item.get("fact_key_dimension", item.get("dimension")))} for item in services]
    capabilities = [{"ref": ref(pack, item["id"]), "service": ref(pack, item["service"])} for item in capability_by_id.values()]
    operations_out = []
    for item in operations:
        argument = item.get("arguments", [item.get("input")])[0]; effect = item.get("effect_rule", item.get("effect"))
        operations_out.append({"ref": ref(pack, item["id"]), "capability": ref(pack, item["capability"]), "service": ref(pack, capability_by_id[item["capability"]]["service"]), "argument": ref(pack, argument), "effect": ref(pack, effect)})
    units = sorted({item["canonical_unit"]["id"] for item in fields if item["canonical_unit"]})
    known = [item["ref"] for item in fields + services + capabilities + operations_out] + [item["effect"] for item in operations_out] + [ref(pack, unit) for unit in units]
    return {"pack": pack, "source": path, "units": [ref(pack, unit) for unit in units], "definitions": sorted(known, key=key), "fields": sorted(fields, key=lambda item: key(item["ref"])), "services": sorted(services, key=lambda item: key(item["ref"])), "capabilities": sorted(capabilities, key=lambda item: key(item["ref"])), "operations": sorted(operations_out, key=lambda item: key(item["ref"]))}
def expected(): return sorted((source_metadata(path) for path in SOURCES), key=lambda item: (item["pack"]["id"], item["pack"]["version"]))
def ordered(items, selector):
    values = [selector(item) for item in items]
    if values != sorted(values): raise ValueError("noncanonical order")
    if len(values) != len(set(values)): raise ValueError("duplicate or ambiguous metadata")

def validate(document):
    if document.get("contract") != "helianthus.semantic.pack-metadata/v1" or document.get("status") != "accepted": raise ValueError("contract identity")
    packs = document.get("packs")
    if packs != expected(): raise ValueError("metadata differs from accepted pack sources")
    ordered(packs, lambda item: (item["pack"]["id"], item["pack"]["version"]))
    for pack in packs:
        pack_ref = pack["pack"]
        for group in ("units", "definitions"):
            ordered(pack[group], key)
            if any(item["pack"] != pack_ref or item["version"] != pack_ref["version"] for item in pack[group]): raise ValueError("cross-pack or wrong-version definition")
        known = {key(item) for item in pack["definitions"]}
        for item in pack["fields"]:
            if key(item["ref"]) not in known or item["canonical_unit"] and key(item["canonical_unit"]) not in known: raise ValueError("missing field or unit definition")
        services = {key(item["ref"]): item for item in pack["services"]}; capabilities = {key(item["ref"]): item for item in pack["capabilities"]}
        for item in pack["capabilities"]:
            if key(item["service"]) not in services: raise ValueError("missing service ownership")
        for item in pack["operations"]:
            if key(item["capability"]) not in capabilities or item["service"] != capabilities[key(item["capability"])]["service"]: raise ValueError("malformed operation shape")
            if any(key(item[name]) not in known for name in ("ref", "argument", "effect")): raise ValueError("missing operation definition")

class Registry:
    """Reference query model for vectors; every public collection is copied."""
    def __init__(self, packs): self._packs = copy.deepcopy(packs)
    def packs(self): return copy.deepcopy([item["pack"] for item in self._packs])
    def has_definition(self, definition): return any(definition in item["definitions"] for item in self._packs)
    def canonical_unit(self, field): return next((copy.deepcopy(item["canonical_unit"]) for pack in self._packs for item in pack["fields"] if item["ref"] == field), None)
    def service_owns_capability(self, service, capability): return any(item["ref"] == capability and item["service"] == service for pack in self._packs for item in pack["capabilities"])
    def field_matches(self, field, service, capability):
        for pack in self._packs:
            fields = {item["ref"]["id"]: item for item in pack["fields"]}; services = {item["ref"]["id"]: item for item in pack["services"]}
            if self.service_owns_capability(service, capability) and field["pack"] == pack["pack"] and service["pack"] == pack["pack"] and capability["pack"] == pack["pack"]:
                return fields.get(field["id"], {}).get("dimension") == services.get(service["id"], {}).get("fact_key_dimension")
        return False
    def operation_matches(self, operation, capability, service, argument, effect):
        return any(item == {"ref": operation, "capability": capability, "service": service, "argument": argument, "effect": effect} for pack in self._packs for item in pack["operations"])
def main():
    document = load(FIXTURE); validate(document); registry = Registry(document["packs"])
    for pack in document["packs"]:
        assert registry.packs() and all(registry.has_definition(item) for item in pack["definitions"])
        for field in pack["fields"]: assert registry.canonical_unit(field["ref"]) == field["canonical_unit"]
        for capability in pack["capabilities"]: assert registry.service_owns_capability(capability["service"], capability["ref"])
        for operation in pack["operations"]: assert registry.operation_matches(operation["ref"], operation["capability"], operation["service"], operation["argument"], operation["effect"])
    print("pack metadata v1: PASS")
if __name__ == "__main__": main()
