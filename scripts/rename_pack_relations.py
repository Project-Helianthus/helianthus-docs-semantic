#!/usr/bin/env python3
"""Rename the pack relation spelling in place.

The pack relation definitions are spelled ``<pack>.relation.<name>``, listed
under the member ``relations``, and the gateway-meter gate names its relation
under the member ``relation``. This one-shot tool rewrites the earlier spelling
of that word, in every case form, to ``relation`` in the files of ``FILES``:
identifiers, JSON members, Python names and prose. It then puts the entries of
the element catalog and of the seed reference list back in the canonical order
CAT-8 (owner kind, pack id, pack version, element id, element version as UTF-8
bytes).

``python3 scripts/rename_pack_relations.py --apply`` rewrites the files and
names each file it changed. ``--check`` writes nothing and exits 1 while a file
of ``FILES``, or any other repository file outside ``LICENSE`` and
``author-evidence/``, still holds the earlier spelling. Paths with a component
that starts with a dot are not repository content and are not read. The tool
uses the standard library only and keeps no alias of the earlier spelling.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The earlier word is assembled so that no file of the repository spells it.
EARLIER = "relation" + "ship"
CURRENT = "relation"
PATTERN = re.compile(EARLIER, re.IGNORECASE)

CATALOG = "api/v1/element-catalog-v1.json"
SEED_REFS = "scripts/element-catalog-seed-refs.json"

FILES = (
    "api/v1/packs/pv-inverter-acceptance-vectors.json",
    "api/v1/packs/evse-acceptance-vectors.json",
    "api/v1/packs/infrastructure-acceptance-vectors.json",
    "api/v1/packs/storage-bms-acceptance-vectors.json",
    "api/v1/packs/storage-bms-contract-tables.json",
    "api/v1/packs/storage-bms-cell-voltage-contract.json",
    "api/v1/packs/pv-inverter-v1.md",
    "api/v1/packs/evse-v1.md",
    "api/v1/packs/infrastructure-v1.md",
    "api/v1/packs/storage-bms-v1.md",
    "api/v1/packs/thermal-hvac-v1.md",
    "api/v1/mappings/huawei-sun2000-pv-v1.json",
    "api/v1/mappings/huawei-sun2000-pv-v1.md",
    "api/v1/mappings/huawei-luna2000-storage-v1.json",
    "api/v1/mappings/huawei-gateway-meter-infrastructure-v1.json",
    "api/v1/mappings/huawei-gateway-meter-infrastructure-v1.md",
    "mappings/infrastructure/gateway-runtime.md",
    "scripts/validate_pv_inverter_pack_v1.py",
    "scripts/test_validate_pv_inverter_pack_v1.py",
    "scripts/validate_evse_pack_v1.py",
    "scripts/test_validate_evse_pack_v1.py",
    "scripts/validate_infrastructure_pack_v1.py",
    "scripts/test_validate_infrastructure_pack_v1.py",
    "scripts/validate_storage_bms_pack_v1.py",
    "scripts/test_validate_storage_bms_pack_v1.py",
    "scripts/validate_huawei_sun2000_pv_mapping.py",
    "scripts/test_validate_huawei_sun2000_pv_mapping.py",
    "scripts/validate_huawei_luna2000_storage_mapping.py",
    "scripts/test_validate_huawei_luna2000_storage_mapping.py",
    "scripts/validate_huawei_gateway_meter_infrastructure_mapping.py",
    "scripts/test_validate_huawei_gateway_meter_infrastructure_mapping.py",
    "tests/test_storage_cell_voltage_contract.py",
    CATALOG,
    SEED_REFS,
    "scripts/generate_element_catalog_v1.py",
    "scripts/validate_element_catalog_v1.py",
    "scripts/test_validate_element_catalog_v1.py",
    "api/v1/graph.md",
    "api/README.md",
    "CHANGELOG.md",
)

EXEMPT = ("LICENSE", "author-evidence")


def same_case(match):
    """The current word in the case form of the matched earlier word."""
    found = match.group(0)
    if found.islower():
        return CURRENT
    if found.isupper():
        return CURRENT.upper()
    if found[0].isupper() and found[1:].islower():
        return CURRENT.capitalize()
    raise ValueError(f"mixed-case spelling {found!r} has no rule")


def rename(text):
    return PATTERN.sub(same_case, text)


def cat8_key(ref):
    owner = ref["owner"]
    pack = owner.get("pack", {"id": "", "version": ""})
    parts = (owner["kind"], pack["id"], pack["version"], ref["id"], ref["version"])
    return tuple(part.encode("utf-8") for part in parts)


def render(document):
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def canonical_order(path, text):
    """Re-sort the catalog entries or the seed references by CAT-8."""
    if path == CATALOG:
        document = json.loads(text)
        document["elements"].sort(key=lambda entry: cat8_key(entry["ref"]))
        return render(document)
    if path == SEED_REFS:
        document = json.loads(text)
        document["refs"].sort(key=cat8_key)
        return render(document)
    return text


def apply():
    changed = []
    for path in FILES:
        target = ROOT / path
        before = target.read_text(encoding="utf-8")
        after = canonical_order(path, rename(before))
        if after != before:
            target.write_text(after, encoding="utf-8")
            changed.append(path)
    for path in changed:
        print(f"renamed: {path}")
    print(f"{len(changed)} of {len(FILES)} files changed")
    return 0


def repository_files():
    for path in sorted(ROOT.rglob("*")):
        parts = path.relative_to(ROOT).parts
        if not path.is_file() or any(part.startswith(".") for part in parts) or parts[0] in EXEMPT:
            continue
        yield path


def holders():
    """Repository-relative paths that still hold the earlier spelling, with a count."""
    found = {}
    for path in [ROOT / name for name in FILES] + list(repository_files()):
        name = path.relative_to(ROOT).as_posix()
        if name in found:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        count = len(PATTERN.findall(text))
        if count:
            found[name] = count
    return found


def check():
    found = holders()
    for name, count in found.items():
        print(f"{name}: {count} occurrence(s) of the earlier spelling", file=sys.stderr)
    if found:
        print(f"FAIL: {len(found)} file(s) hold the earlier spelling", file=sys.stderr)
        return 1
    print("PASS: no file outside LICENSE and author-evidence/ holds the earlier spelling")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rename the pack relation spelling in place.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true", help="rewrite the files and re-sort the catalog")
    mode.add_argument("--check", action="store_true", help="exit 1 while the earlier spelling remains")
    args = parser.parse_args(argv)
    try:
        return apply() if args.apply else check()
    except (OSError, ValueError, KeyError) as error:
        print(f"rename pack relations: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
