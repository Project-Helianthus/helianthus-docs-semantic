#!/usr/bin/env python3
"""Record every output of one reference into a vectors tree and an oracle tree (items 3 to 9).

The same function serves the initial recording (trees under acceptance/) and a replay (trees under .tmp/)."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bom  # noqa: E402
import binaries  # noqa: E402
import common  # noqa: E402
import goldens  # noqa: E402
import gorun  # noqa: E402
import losses  # noqa: E402
import semreg_catalog  # noqa: E402

ORACLE = Path(__file__).resolve().parent.parent


def case_of(name):
    """Index case id of a native SS02 record file name."""
    stem = name.split(".")[0]
    if stem == "vaillant-dhw-0004-value-50":
        return "vaillant-dhw-0004"
    if stem == "vaillant-dhw-0005-measured-temperature":
        return "vaillant-dhw-0005"
    if stem.startswith("vaillant-dhw-"):
        return stem
    if stem == "growatt-bms-can-tuple-card":
        return "can-311-312-313"
    return stem.replace("growatt-bms-can-", "can-")


BT01 = (
    ("internal/adaptermux", "gateway-adaptermux", "TestOracleAdapterMux", "current/gateway/adaptermux"),
    ("internal/localworkerhost", "gateway-localworkerhost", "TestOracleLocalWorkerHost", "current/gateway/localworkerhost"),
    (".", "gateway-engine", "TestOracleEngine", "current/gateway/engine"),
)


def record_bt01(vectors, work):
    """Run the three BT01 recorders at the gateway pin and write their case files; return the index entries."""
    vectors, work = Path(vectors), Path(work)
    entries = []
    for package, sources, test, directory in BT01:
        out = work / sources
        gorun.run("current", "gateway", package, sources, test, out)
        for produced in sorted(p for p in out.rglob("*.json")):
            relative = f"{directory}/{produced.relative_to(out).as_posix()}"
            common.write(vectors / relative, produced.read_bytes())
            entries.append({"path": relative, "origin": "recorded-current", "reference": "current", "role": "expected-output",
                            "recorder": f"recorders/gorun.py --entry gateway --package {package} --sources {sources} --test {test}"})
    return entries


def record(reference, vectors, oracle, sessions):
    """Return the index entries (path relative to the vectors tree) of every vector output written."""
    vectors, oracle = Path(vectors), Path(oracle)
    entries = []

    def emit(relative, recorder, origin, case=None, kind=None):
        entry = {"path": relative, "origin": origin, "reference": reference, "role": "expected-output", "recorder": recorder}
        if case:
            entry["case"] = case
        if kind:
            entry["kind"] = kind
        entries.append(entry)

    bom.record(reference, oracle / "bom")
    if reference in ("current", "released", "pre-port"):
        binaries.record(oracle / "binaries", oracle / "binaries.json", only={s["id"] for s in binaries.SPECS if s["reference"] == reference})

    with tempfile.TemporaryDirectory(dir=str(common.scratch_root())) as work:
        work = Path(work)
        if reference == "current":
            goldens.record(vectors / "current/gateway-goldens.json")
            emit("current/gateway-goldens.json", "recorders/goldens.py", "recorded-current")
            semreg_catalog.record(vectors / "current/semreg/semreg-v1-graph/embedded-element-catalog.json")
            emit("current/semreg/semreg-v1-graph/embedded-element-catalog.json", "recorders/semreg_catalog.py", "recorded-current")
            for entry_id, package, sources, test, directory, impl in (
                ("gateway", "cmd/gateway", "gateway", "TestOracleSS02", "current/gateway/cmd-gateway/ss02", "gateway"),
                ("canbusreg", ".", "canbusreg", "TestOracleSS02GrowattV104", "current/canbusreg/canbusreg/ss02", "canbusreg"),
                ("modbusreg", "sunspec", "modbusreg", "TestOracleSS02SunSpec", "current/modbusreg/sunspec/ss02", "modbusreg"),
            ):
                out = work / impl
                gorun.run("current", entry_id, package, sources, test, out)
                for produced in sorted(out.glob("*.json")):
                    relative = f"{directory}/{produced.name}"
                    common.write(vectors / relative, produced.read_bytes())
                    emit(relative, f"recorders/gorun.py --entry {entry_id} --sources {sources} --test {test}", "recorded-current", case_of(produced.name), "native")
            entries.extend(record_bt01(vectors, work))
            if sessions:
                for session in sorted((vectors / "current/sessions").rglob("session.json")):
                    output = session.with_name("output.json")
                    provenance = oracle / "provenance" / ("-".join(session.parent.relative_to(vectors / "current/sessions").parts) + ".json")
                    subprocess.run([sys.executable, "-I", str(ORACLE / "replay_session.py"), "--reference", "current", "--session", str(session), "--output", str(output), "--provenance", str(provenance)], check=True)
                    emit(output.relative_to(vectors).as_posix(), "replay_session.py --reference current", "recorded-current")
        if reference == "pre-port":
            out = work / "pre-port"
            gorun.run("pre-port", "gateway", "graphql", "pre-port-graphql", "TestOraclePrePortSchema", out)
            gorun.run("pre-port", "gateway", "mcp", "pre-port-mcp", "TestOraclePrePortToolList", out)
            for name in ("graphql-schema-introspection.json", "mcp-tools-list.json"):
                common.write(vectors / "pre-port/gateway" / name, (out / name).read_bytes())
                emit(f"pre-port/gateway/{name}", "recorders/gorun.py --reference pre-port", "recorded-pre-port")
            losses.record(vectors / "pre-port/gateway/graphql-schema-introspection.json", vectors / "pre-port/losses.json")
            emit("pre-port/losses.json", "recorders/losses.py", "recorded-pre-port")
    return entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--vectors", required=True)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--no-sessions", action="store_true")
    parser.add_argument("--entries")
    args = parser.parse_args()
    entries = record(args.reference, args.vectors, args.oracle, not args.no_sessions)
    if args.entries:
        Path(args.entries).write_text(json.dumps(entries, indent=2) + "\n")


if __name__ == "__main__":
    main()
