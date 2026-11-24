#!/usr/bin/env python3
"""Record the bill of materials of one reference: bom/<reference>-<entry>.json (item 3)."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def objects(text):
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        value, index = decoder.raw_decode(text, index)
        yield value


def go_bom(item):
    source = common.unpack(item)
    result = common.go_run(["list", "-m", "-json", "all"], source)
    if result.returncode != 0:
        sys.exit(f"go list -m -json all failed for {item['id']}: {result.stderr.strip()}")
    go_sum = {}
    for line in (common.show(item, "go.sum") or b"").decode("utf-8").splitlines():
        parts = line.split()
        if len(parts) == 3:
            go_sum[(parts[0], parts[1])] = parts[2]
    main = None
    modules = []
    for obj in objects(result.stdout):
        if obj.get("Main"):
            main = {"path": obj["Path"], "go": obj.get("GoVersion", "")}
            continue
        module = {"path": obj["Path"], "version": obj.get("Version", ""), "sum": go_sum.get((obj["Path"], obj.get("Version", "")), ""), "go_mod_sum": go_sum.get((obj["Path"], obj.get("Version", "") + "/go.mod"), "")}
        if "Replace" in obj:
            module["replace"] = {"path": obj["Replace"]["Path"], "version": obj["Replace"].get("Version", ""), "sum": go_sum.get((obj["Replace"]["Path"], obj["Replace"].get("Version", "")), "")}
        modules.append(module)
    modules.sort(key=lambda m: (m["path"], m["version"]))
    return {"format": "helianthus-oracle-bom/1", "reference": None, "entry": item["id"], "slug_at_pin": item["slug_at_pin"], "commit": item["commit"], "main": main, "modules": modules}


def record(reference, output):
    written = []
    for item in common.references()[reference]["entries"]:
        name = f"{reference}-{item['id']}.json"
        if item["id"] == "addon":
            data = common.show(item, "helianthus/bom.json")
            if data is None:
                payload = {"format": "helianthus-oracle-bom/1", "reference": reference, "entry": item["id"], "slug_at_pin": item["slug_at_pin"], "commit": item["commit"], "helianthus/bom.json": "absent at this pin"}
                common.write(output / name, common.canonical(payload))
            else:
                common.write(output / name, data)
            written.append(name)
            continue
        if common.show(item, "go.mod") is None:
            continue
        payload = go_bom(item)
        payload["reference"] = reference
        common.write(output / name, common.canonical(payload))
        written.append(name)
    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    for name in record(args.reference, Path(args.output)):
        print(name)


if __name__ == "__main__":
    main()
