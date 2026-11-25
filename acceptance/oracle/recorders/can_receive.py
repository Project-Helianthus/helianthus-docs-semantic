#!/usr/bin/env python3
"""Record the six CAN receive cases of the gateway pin on the native platform of this host (BT03).

  can_receive.py record --output DIR   run the cases of this host's partition and write DIR/receipt.json and DIR/cases/<case>/{input,expected}.json
  can_receive.py freeze --actual DIR   initial recording only: copy the cases of one actual tree into acceptance/vectors and append their index entries

The four Linux cases run on a Linux host, the two unsupported cases on a host that is not Linux. Nothing is cross-compiled: the host's own
Go target is the target. The pin's sources are unpacked into a scratch directory; on Linux two of them are copied with the operating-system
operands replaced (see OVERLAYS), the pin itself and every opener sentence stay as they are."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

RECORDERS = Path(__file__).resolve().parent
GO_SOURCES = RECORDERS / "go" / "gateway-can-receive"
VECTORS = common.ROOT / "acceptance" / "vectors"
CASES_DIRECTORY = "current/transport/can-receive"
TEST = "TestOracleCanReceive"
FILES = ("input.json", "expected.json")

PARTITIONS = {
    "linux": ("linux-bms-receive", "linux-bms-identity-mismatch", "linux-bms-missing-interface", "linux-project-reopen-clock"),
    "nonlinux": ("nonlinux-project-unsupported", "nonlinux-bms-unsupported"),
}
SOURCES = {
    "linux": ("cmd/gateway/growatt_bms_can_socketcan_linux.go", "cmd/gateway/growatt_project_socketcan_linux.go"),
    "nonlinux": ("cmd/gateway/growatt_bms_can_socketcan_unsupported.go", "cmd/gateway/growatt_project_socketcan_unsupported.go"),
}
# Scratch-only substitutions of the Linux openers: (file, pinned text, replacement, occurrences). The BMS opener calls the operating
# system directly; each call is replaced by the function of the recorder that has the same name and signature. The project opener
# already takes its operating-system calls as an argument; only its one clock reading is replaced.
OVERLAYS = {
    "cmd/gateway/growatt_bms_can_socketcan_linux.go": (
        ("net.InterfaceByName(", "oracleBMSLookup(", 1),
        ("unix.Socket(", "oracleBMSSocket(", 1),
        ("unix.SetsockoptInt(", "oracleBMSSetsockoptInt(", 1),
        ("unix.Bind(", "oracleBMSBind(", 1),
        ("unix.Poll(", "oracleBMSPoll(", 1),
        ("unix.Read(", "oracleBMSRead(", 1),
        ("unix.Close(", "oracleBMSClose(", 3),
        ('\t"net"\n', "", 1),
    ),
    "cmd/gateway/growatt_project_socketcan_linux.go": (("time.Since(growattProjectClockOrigin)", "oracleProjectSince(growattProjectClockOrigin)", 1),),
}
RECEIPT_FORMAT = "helianthus-oracle-qv05-receipt/1"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def go_value(name):
    return subprocess.run(["go", "env", name], stdout=subprocess.PIPE, text=True, check=True, env=common.go_env()).stdout.strip()


def native_platform():
    """('linux' | 'nonlinux', target) of this host. A run whose Go target is not the host's own is not native and is refused."""
    host = {name: go_value(name) for name in ("GOHOSTOS", "GOHOSTARCH", "GOOS", "GOARCH")}
    if host["GOOS"] != host["GOHOSTOS"] or host["GOARCH"] != host["GOHOSTARCH"]:
        sys.exit(f"the Go target {host['GOOS']}/{host['GOARCH']} is not the native platform {host['GOHOSTOS']}/{host['GOHOSTARCH']}: no cross-compiled receipt")
    return ("linux" if host["GOOS"] == "linux" else "nonlinux"), host


def case_entries(entries):
    return sorted((e for e in entries if e["path"].startswith(CASES_DIRECTORY + "/")), key=lambda e: e["path"])


def index_digest(entries):
    """Digest of the whole common index (every entry, ordered by path): what both runners must hold alike."""
    return sha256(json.dumps(sorted(entries, key=lambda e: e["path"]), sort_keys=True).encode("utf-8"))


def oracle_revision():
    """The commit of this repository that the recorder runs from; a receipt of another revision is not accepted."""
    return subprocess.run(["git", "-C", str(common.ROOT), "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True, check=True).stdout.strip()


def pinned_sources(platform):
    """Path and sha256 of the pinned source files of one platform, read from the gateway pin itself."""
    item = gateway_entry()
    files = []
    for path in SOURCES[platform]:
        pinned = common.show(item, path)
        if pinned is None:
            sys.exit(f"{path} does not exist at the gateway pin")
        files.append({"path": path, "sha256": sha256(pinned)})
    return files


def recorder_digest():
    """Digest of the recorder sources: the Go files, this script and the overlay table."""
    parts = {path.name: sha256(path.read_bytes()) for path in sorted(GO_SOURCES.glob("*.go"))}
    parts["can_receive.py"] = sha256(Path(__file__).read_bytes())
    return sha256(json.dumps(parts, sort_keys=True).encode("utf-8"))


def gateway_entry():
    return common.entry("current", "gateway")


def overlaid(item, tree, platform):
    """Apply OVERLAYS to the scratch tree; return the list that is written into input.json (the pinned digest and the overlaid digest)."""
    applied = []
    if platform != "linux":
        return applied
    for path in SOURCES["linux"]:
        pinned = common.show(item, path)
        if pinned is None:
            sys.exit(f"{path} does not exist at the gateway pin")
        text = pinned.decode("utf-8")
        substitutions = []
        for old, new, count in OVERLAYS.get(path, ()):
            if text.count(old) != count:
                sys.exit(f"{path}: expected {count} occurrence(s) of {old!r}, found {text.count(old)}")
            text = text.replace(old, new)
            substitutions.append({"pinned": old, "replacement": new, "occurrences": count})
        (tree / path).write_bytes(text.encode("utf-8"))
        applied.append({"file": path, "pinned_sha256": sha256(pinned), "substitutions": substitutions})
    return applied


def record(output):
    platform, target = native_platform()
    item = gateway_entry()
    scratch = common.scratch_root() / "rec" / f"can-receive-{platform}-{item['commit'][:12]}"
    common.clean(scratch)
    tree = common.unpack(item, scratch)
    package = tree / "cmd" / "gateway"
    for stale in package.glob("zz_oracle_*"):
        stale.unlink()
    for source in sorted(GO_SOURCES.glob("*.go")):
        shutil.copyfile(source, package / source.name)
    overlay = overlaid(item, tree, platform)
    files = pinned_sources(platform)
    output = Path(output).resolve()
    common.clean(output)
    cases = output / "cases"
    cases.mkdir(parents=True)
    executable = scratch / "can-receive.test"
    env = common.go_env({
        "ORACLE_OUT": str(cases),
        f"ORACLE_CAN_SOURCES_{platform}": json.dumps(files),
        f"ORACLE_CAN_OVERLAY_{platform}": json.dumps(overlay),
    })
    compiled = common.go_run(["test", "-c", "-o", str(executable), "./cmd/gateway/"], tree, env)
    if compiled.returncode != 0:
        sys.exit("compile of the recorder failed: " + (compiled.stdout + compiled.stderr)[-3000:])
    ran = subprocess.run([str(executable), "-test.count=1", "-test.run", f"^{TEST}$", "-test.v"], cwd=package, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if ran.returncode != 0:
        sys.exit(f"recorder {TEST} failed: " + (ran.stdout + ran.stderr)[-3000:])
    selected = common.go_run(["list", "-f", "{{join .GoFiles \" \"}}", "./cmd/gateway/"], tree, env).stdout.split()
    produced = sorted(p.name for p in cases.iterdir())
    if produced != sorted(PARTITIONS[platform]):
        sys.exit(f"the recorder produced {produced}, the {platform} partition is {sorted(PARTITIONS[platform])}")
    for case in produced:
        names = sorted(p.name for p in (cases / case).iterdir())
        if names != sorted(FILES):
            sys.exit(f"{case}: produced {names}")
    entries = json.loads((VECTORS / "index.json").read_text(encoding="utf-8"))["vectors"]
    receipt = {
        "format": RECEIPT_FORMAT,
        "reference": "current",
        "platform": platform,
        "native": {"goos": target["GOOS"], "goarch": target["GOARCH"], "hostos": target["GOHOSTOS"], "hostarch": target["GOHOSTARCH"]},
        "toolchain": subprocess.run(["go", "version"], stdout=subprocess.PIPE, text=True, check=True).stdout.strip(),
        "command": "python3 acceptance/oracle/check.py --record-can-native current",
        "cases": sorted(produced),
        "statuses": {"compile": compiled.returncode, "run": ran.returncode},
        "oracle_revision": oracle_revision(),
        "gateway_pin": item["commit"],
        "selected_pinned_files": sorted(name for name in selected if name.startswith("growatt_") and "socketcan" in name),
        "pinned_sources": files,
        "overlay": overlay,
        "executable_sha256": sha256(executable.read_bytes()),
        "recorder_sha256": recorder_digest(),
        "index_sha256": index_digest(entries),
    }
    (output / "receipt.json").write_text(common.canonical(receipt), encoding="utf-8")
    return receipt


def freeze(actual):
    """Copy the cases of one actual tree into acceptance/vectors and append their index entries after the existing ones, which keep their order. A frozen case is never replaced."""
    actual = Path(actual)
    receipt = json.loads((actual / "receipt.json").read_text(encoding="utf-8"))
    platform = receipt["platform"]
    index_path = VECTORS / "index.json"
    document = json.loads(index_path.read_text(encoding="utf-8"))
    known = {e["path"] for e in document["vectors"]}
    added = []
    for case in PARTITIONS[platform]:
        for name in FILES:
            relative = f"{CASES_DIRECTORY}/{case}/{name}"
            if relative in known or (VECTORS / relative).exists():
                sys.exit(f"{relative} is already frozen and is never replaced")
            data = (actual / "cases" / case / name).read_bytes()
            common.write(VECTORS / relative, data)
            added.append({"path": relative, "sha256": sha256(data), "origin": "recorded-current", "reference": "current", "role": "expected-output",
                          "recorder": "check.py --record-can-native current", "case": case, "platform": platform})
    document["vectors"] = document["vectors"] + sorted(added, key=lambda e: e["path"])
    index_path.write_text(common.canonical(document), encoding="utf-8")
    print(len(added), "entries appended for the", platform, "partition")


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("record").add_argument("--output", required=True)
    commands.add_parser("freeze").add_argument("--actual", required=True)
    args = parser.parse_args()
    if args.command == "record":
        record(args.output)
    else:
        freeze(args.actual)


if __name__ == "__main__":
    main()
