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


QV08 = (
    ("matter", "gateway-matter", "TestOracleMatter", "current/gateway/matter"),
    ("matter/feedv1", "gateway-feedv1", "TestOracleFeedV1", "current/gateway/matter-feedv1"),
    ("matter/libraryhost", "gateway-libraryhost", "TestOracleLibraryHost", "current/gateway/matter-libraryhost"),
)


QV04 = (
    (".", "modbus", "TestOracleModbus", "current/modbus/modbus", "modbus"),
    ("internal/modbusadapter", "gateway-modbusadapter", "TestOracleModbusAdapterReadOnlySession", "current/gateway/modbusadapter", "gateway"),
    ("cmd/gateway", "gateway-tesla-observe", "TestOracleTeslaObserve", "current/gateway/cmd-gateway/tesla-observe", "gateway"),
)


QV07 = (("cmd/gateway", "gateway-vaillant-typed", "TestOracleVaillantTyped", "current/gateway/cmd-gateway/vaillant-typed"),)

QV06 = (
    ("service", "eebus-go-service", "TestOracleEEBusGoService", "current/eebus-go/service", "eebus-go"),
    ("api", "eebus-go-api", "TestOracleAPIConfiguration", "current/eebus-go/api", "eebus-go"),
    (".", "eebusreg/root", "TestOracleEEBusRoot", "current/eebusreg/eebusreg", "eebusreg"),
    ("internal/eebusfacade", "eebusreg/facade", "TestOracleFacade", "current/eebusreg/eebusfacade", "eebusreg"),
    ("internal/eebusservicebridge", "eebusreg/bridge", "TestOracleServiceBridge", "current/eebusreg/eebusservicebridge", "eebusreg"),
)

PRE_PORT_TYPED = (
    ("gateway", "graphql", "pre-port-typed/graphql", "TestOraclePrePortTyped", ("graphql-typed-queries.json", "graphql-typed-mutations.json"), "pre-port/gateway/typed"),
    ("gateway", "mcp", "pre-port-typed/mcp", "TestOraclePrePortTypedMCP", ("mcp-typed-tools.json",), "pre-port/gateway/typed"),
)

PRE_PORT_CANONICAL_PV = (
    ("gateway-canonical-pv", "internal/modbusadapter", "pre-port-canonical-pv/modbusadapter", "TestOraclePrePortCanonicalPVMapper", ("canonical-pv-mapper.json",), "pre-port/gateway/canonical-pv"),
    ("gateway-canonical-pv", "mcp", "pre-port-canonical-pv/mcp", "TestOraclePrePortCanonicalPVEnvelope", ("mcp-canonical-pv-envelope.json",), "pre-port/gateway/canonical-pv"),
    ("gateway-canonical-pv", "m2mgraphql", "pre-port-canonical-pv/m2mgraphql", "TestOraclePrePortCanonicalPVContract", ("m2m-canonical-pv-contract.json",), "pre-port/gateway/canonical-pv"),
)

# Cases whose record carries an identifier the eBUS bus transmits (radio device model, firmware and hardware identifier; adapter
# hardware identity) keep only their digest in the index.
QV07_DIGEST_ONLY = ("radio/", "adapter-hardware/")


def recorder_command(package, sources, test, entry_id="gateway"):
    """The recorder command stored in an index entry; run from the repository root as python3 acceptance/oracle/<command>."""
    return (f"recorders/gorun.py --reference current --entry {entry_id} --package {package} --sources {sources} --test {test}"
            f" --output .tmp/oracle-record/{sources}")


def record_go_cases(specs, vectors, work, runnable=False):
    """Run harness-only Go recorders at the gateway pin, write their case files and return the index entries."""
    vectors, work = Path(vectors), Path(work)
    entries = []
    for package, sources, test, directory, *rest in specs:
        entry_id = rest[0] if rest else "gateway"
        out = work / sources
        gorun.run("current", entry_id, package, sources, test, out)
        for produced in sorted(p for p in out.rglob("*.json")):
            relative = f"{directory}/{produced.relative_to(out).as_posix()}"
            common.write(vectors / relative, produced.read_bytes())
            command = recorder_command(package, sources, test, entry_id) if runnable else f"recorders/gorun.py --entry gateway --package {package} --sources {sources} --test {test}"
            entries.append({"path": relative, "origin": "recorded-current", "reference": "current", "role": "expected-output", "recorder": command})
    return entries


def record_bt01(vectors, work):
    """The three BT01 recorders: multiplexer, local worker supervisor and the six engines."""
    return record_go_cases(BT01, vectors, work, runnable=True)


def record_qv04(vectors, work):
    """The BT02 recorders: the pacing code, the read-only session and the passive opener of the non-Linux build."""
    return record_go_cases(QV04, vectors, work, runnable=True)


def record_qv07(vectors, work):
    """The EE01 recorder: typed GraphQL and MCP outputs of the Vaillant publication owner and the semantic cache."""
    entries = record_go_cases(QV07, vectors, work, runnable=True)
    for entry in entries:
        if entry["path"].split("vaillant-typed/", 1)[1].startswith(QV07_DIGEST_ONLY):
            entry["digest_only"] = True
    return entries


def record_qv06(vectors, work):
    """The BT04 recorders: the eebus-go service and api packages and the eebusreg runtime, output binding, facade and service bridge."""
    return record_go_cases(QV06, vectors, work, runnable=True)


def record_qv08(vectors, work):
    """The three XX02 recorders: the Matter projection and model, the feed contract and the library host."""
    return record_go_cases(QV08, vectors, work)


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
            entries.extend(record_qv08(vectors, work))
            entries.extend(record_qv04(vectors, work))
            entries.extend(record_qv07(vectors, work))
            entries.extend(record_qv06(vectors, work))
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
            for entry_id, package, sources, test, names, directory in PRE_PORT_TYPED + PRE_PORT_CANONICAL_PV:
                produced = work / "pre-port-typed" / sources.replace("/", "-")
                gorun.run("pre-port", entry_id, package, sources, test, produced)
                for name in names:
                    common.write(vectors / directory / name, (produced / name).read_bytes())
                    emit(f"{directory}/{name}", f"recorders/gorun.py --reference pre-port --entry {entry_id} --package {package} --sources {sources} --test {test}", "recorded-pre-port")
            losses.record(vectors / "pre-port/gateway/graphql-schema-introspection.json", vectors / "pre-port/gateway/typed/graphql-typed-queries.json", vectors / "pre-port/gateway/typed/mcp-typed-tools.json", vectors / "pre-port/losses.json")
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
