#!/usr/bin/env python3
"""Replay one whole session on the frozen old production path.

  python3 acceptance/oracle/replay_session.py --reference current --session <session.json> --output <output.json>

The session names the pinned donor fixtures that carry its stimuli and the harness that drives them. The runner
verifies those fixtures at the pin, compiles a separately labelled replay executable from the exact pinned source
plus the harness-only entry files of this tree, runs it as its own process and writes the six output classes
(acquisitions, sends, publications, withdrawals, outcomes, public_outputs) with the portable part of the build record (source
revision, label, build command, invocation) to --output. What depends on the host that ran it (toolchain with its operating system
and architecture, digest of the replay executable) is written to a separate provenance file, --provenance, which defaults to
<output>.provenance.json, and is never part of the output that is compared.
The replay executable is not the shipped gateway CLI binary.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "recorders"))
import common  # noqa: E402

CLASSES = ["acquisitions", "sends", "publications", "withdrawals", "outcomes", "public_outputs"]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def documents(session, session_bytes, item, harness, classes, toolchain, executable_sha256):
    """The output document (six classes and the portable build record) and the host-dependent provenance of one replay."""
    reference = session["reference"]
    build = {
        "source": {"repository": item["slug_at_pin"], "commit": item["commit"]},
        "label": "replay executable built from the pinned production source plus harness-only entry files; not the shipped gateway CLI binary",
        "build_command": f"go test -c -trimpath -o replay-{session['session']}.test ./{harness['package']}/",
        "invocation": f"replay-{session['session']}.test -test.run ^{harness['test']}$ -test.count=1 (working directory ./{harness['package']}/, session input in ORACLE_SESSION)",
    }
    head = {"session": session["session"], "reference": reference, "session_sha256": sha256_bytes(session_bytes)}
    document = {"format": "helianthus-oracle-session-output/1", **head, "build": build, **{name: classes[name] for name in CLASSES}}
    provenance = {"format": "helianthus-oracle-session-provenance/1", **head, "build": dict(build, toolchain=toolchain, executable_sha256=executable_sha256)}
    return document, provenance


def replay(reference, session_path, output_path, provenance_path=None):
    session_bytes = Path(session_path).read_bytes()
    session = json.loads(session_bytes)
    if session.get("reference") != reference:
        sys.exit(f"session {session.get('session')} belongs to reference {session.get('reference')}, not {reference}")
    harness = session["harness"]
    item = common.entry(reference, harness["entry"])
    tree = common.unpack(item, common.scratch_root() / "replay" / f"{reference}-{item['id']}-{item['commit'][:12]}")
    for fixture in session.get("fixtures", []):
        actual = sha256_bytes((tree / fixture["path"]).read_bytes())
        if actual != fixture["sha256"]:
            sys.exit(f"pinned fixture {fixture['path']} has sha256 {actual}, the session names {fixture['sha256']}")
    package = tree / harness["package"]
    for stale in package.glob("zz_oracle_*"):
        stale.unlink()
    for source in sorted((HERE / "recorders" / "go" / harness["sources"]).glob("*.go")):
        shutil.copyfile(source, package / source.name)
    env = common.go_env({"GOTOOLCHAIN": "local"})
    work = Path(tempfile.mkdtemp(prefix="replay-", dir=str(common.scratch_root())))
    executable = work / f"replay-{session['session']}.test"
    build = common.go_run(["test", "-c", "-trimpath", "-o", str(executable), f"./{harness['package']}/"], tree, env)
    if build.returncode != 0:
        sys.exit(f"replay executable did not build: {build.stderr[-3000:]}")
    out_dir = work / "out"
    out_dir.mkdir()
    run_env = dict(env, ORACLE_SESSION=str(Path(session_path).resolve()), ORACLE_OUT=str(out_dir))
    command = [str(executable), "-test.run", f"^{harness['test']}$", "-test.count=1"]
    run = subprocess.run(command, cwd=package, env=run_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if run.returncode != 0:
        sys.exit(f"replay process failed ({run.returncode}): {(run.stdout + run.stderr)[-3000:]}")
    classes = json.loads((out_dir / "classes.json").read_text(encoding="utf-8"))
    for name in CLASSES:
        if name not in classes:
            sys.exit(f"replay process emitted no class {name}")
    toolchain = subprocess.run(["go", "version"], env=env, stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
    document, provenance = documents(session, session_bytes, item, harness, classes, toolchain, sha256_bytes(executable.read_bytes()))
    provenance_path = Path(provenance_path) if provenance_path else Path(str(output_path) + ".provenance.json")
    for path, content in ((Path(output_path), document), (provenance_path, provenance)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.rmtree(work)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provenance", help="where the host-dependent build record is written (default: <output>.provenance.json)")
    args = parser.parse_args()
    replay(args.reference, args.session, args.output, args.provenance)


if __name__ == "__main__":
    main()
