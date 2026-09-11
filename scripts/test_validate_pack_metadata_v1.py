#!/usr/bin/env python3
"""Negative and query-isolation controls for pack metadata v1."""
import copy, importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pack_metadata", ROOT / "scripts" / "validate_pack_metadata_v1.py")
module = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = module; SPEC.loader.exec_module(module)
def rejects(document):
    try: module.validate(document)
    except ValueError as error:
        if "metadata differs" not in str(error): raise AssertionError(error)
    else: raise AssertionError("mutation accepted")
def main():
    baseline = module.load(module.FIXTURE); module.validate(baseline); registry = module.Registry(baseline["packs"])
    packs = registry.packs(); packs[0]["id"] = "mutated"; assert registry.packs()[0]["id"] != "mutated"
    field = baseline["packs"][0]["fields"][0]; unit = registry.canonical_unit(field["ref"])
    if unit: unit["id"] = "mutated"; assert registry.canonical_unit(field["ref"])["id"] != "mutated"
    for pack in baseline["packs"]:
        services = {item["ref"]["id"]: item for item in pack["services"]}
        for capability in pack["capabilities"]:
            service = services[capability["service"]["id"]]
            matching = next((item for item in pack["fields"] if item["dimension"] == service["fact_key_dimension"]), None)
            if matching:
                assert registry.field_matches(matching["ref"], service["ref"], capability["ref"])
                wrong = copy.deepcopy(capability["ref"]); wrong["version"] = "0.0.0"
                assert not registry.field_matches(matching["ref"], service["ref"], wrong)
        for operation in pack["operations"]:
            assert registry.operation_matches(operation["ref"], operation["capability"], operation["service"], operation["argument"], operation["effect"])
            wrong = copy.deepcopy(operation["effect"]); wrong["id"] += ".wrong"
            assert not registry.operation_matches(operation["ref"], operation["capability"], operation["service"], operation["argument"], wrong)
    unknown = copy.deepcopy(baseline["packs"][0]["definitions"][0]); unknown["version"] = "0.0.0"
    assert not registry.has_definition(unknown) and registry.canonical_unit(unknown) is None
    for name, mutate in (
        ("wrong_version", lambda d: d["packs"][0]["definitions"][0].update(version="9.0.0")),
        ("wrong_unit", lambda d: d["packs"][0]["fields"][0]["canonical_unit"].update(id="unit.missing")),
        ("cross_pack", lambda d: d["packs"][0]["capabilities"][0]["service"].update(pack=d["packs"][1]["pack"])),
        ("duplicate", lambda d: d["packs"][0]["definitions"].append(copy.deepcopy(d["packs"][0]["definitions"][0]))),
        ("operation_shape", lambda d: d["packs"][0]["operations"] and d["packs"][0]["operations"][0].update(argument=d["packs"][0]["fields"][0]["ref"])),
        ("order", lambda d: d["packs"].reverse()),
    ):
        candidate = copy.deepcopy(baseline); mutate(candidate); rejects(candidate); print(f"{name}: REJECTED")
    print("deep_copy_queries: PASS")
if __name__ == "__main__": main()
