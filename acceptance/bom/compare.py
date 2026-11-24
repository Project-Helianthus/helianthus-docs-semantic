#!/usr/bin/env python3
"""Compare the handoff bill of materials of the renamed gateway and matterreg with the QQ01 pre-rename snapshot.

Writes compare.json next to this file and exits 1 when any pair is unexplained.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SNAPSHOT = {
    "gateway": ROOT / "acceptance/oracle/bom/current-gateway.json",
    "matterreg": ROOT / "acceptance/oracle/bom/current-matterreg.json",
}
HANDOFF = ROOT / "acceptance/handoff/handoff-bom.json"
OUT = HERE / "compare.json"

RENAMES = {
    "github.com/Project-Helianthus/helianthus-ebusgateway": "github.com/Project-Helianthus/helianthus-gateway",
    "github.com/Project-Helianthus/helianthus-matter-binding": "github.com/Project-Helianthus/helianthus-matterreg",
}
FABRIC = "github.com/SukramJ/go-fabric"
FABRIC_REPOSITORY = "matterreg"
CLASSES = ("same", "rename", "go-fabric re-pin", "unexplained")


def ident(m):
    if m is None:
        return None
    return {"version": m["version"], "sum": m["sum"], "go_mod_sum": m["go_mod_sum"]}


def pair(kind, repository, before_path, after_path, before, after, cls):
    return {
        "repository": repository,
        "kind": kind,
        "before_path": before_path,
        "after_path": after_path,
        "before": before,
        "after": after,
        "class": cls,
    }


def compare_repository(repository, before, after):
    pairs = []
    fabric_before = next((m["version"] for m in before["modules"] if m["path"] == FABRIC), None)
    fabric_after = next((m["version"] for m in after["modules"] if m["path"] == FABRIC), None)
    # The go-fabric re-pin exists only on matterreg and only when the requirement's release moved.
    repin = repository == FABRIC_REPOSITORY and fabric_before != fabric_after

    main_before, main_after = before["main"], after["main"]
    main_cls = "rename" if RENAMES.get(main_before["path"]) == main_after["path"] else "unexplained"
    pairs.append(pair("main", repository, main_before["path"], main_after["path"], None, None, main_cls))

    go_before, go_after = main_before["go"], main_after["go"]
    if go_before == go_after:
        go_cls = "same"
    elif repin:
        go_cls = "go-fabric re-pin"
    else:
        go_cls = "unexplained"
    pairs.append(pair("go", repository, go_before, go_after, None, None, go_cls))

    after_by_path = {m["path"]: m for m in after["modules"]}
    matched = set()
    for m in before["modules"]:
        target = RENAMES.get(m["path"], m["path"])
        a = after_by_path.get(target)
        if a is None:
            cls = "go-fabric re-pin" if repin else "unexplained"
        else:
            matched.add(target)
            if ident(m) == ident(a):
                cls = "rename" if target != m["path"] else "same"
            else:
                cls = "go-fabric re-pin" if repin else "unexplained"
        pairs.append(pair("module", repository, m["path"], target, ident(m), ident(a), cls))
    for a in after["modules"]:
        if a["path"] not in matched:
            cls = "go-fabric re-pin" if repin else "unexplained"
            pairs.append(pair("module", repository, None, a["path"], None, ident(a), cls))
    return pairs, {"before": fabric_before, "after": fabric_after}


def main():
    handoff = json.loads(HANDOFF.read_text())
    report = {"format": "helianthus-bom-compare/1", "repositories": {}, "pairs": []}
    counts = {c: 0 for c in CLASSES}
    unexplained = []
    for repository in ("gateway", "matterreg"):
        before = json.loads(SNAPSHOT[repository].read_text())
        after = handoff[repository]
        pairs, fabric = compare_repository(repository, before, after)
        report["repositories"][repository] = {"go_fabric_version": fabric}
        for p in pairs:
            counts[p["class"]] += 1
            report["pairs"].append(p)
            if p["class"] == "unexplained":
                unexplained.append(p)
    report["counts"] = counts
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for p in unexplained:
        print("unexplained:", json.dumps(p, sort_keys=True), file=sys.stderr)
    print("counts:", json.dumps(counts, sort_keys=True))
    return 1 if unexplained else 0


if __name__ == "__main__":
    sys.exit(main())
