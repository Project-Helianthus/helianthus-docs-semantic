#!/usr/bin/env python3
"""Build the gateway binaries of the references the way the reference add-on Dockerfile builds them (item 4).

Two add-on build forms exist and neither is mixed into the other:
  build   add-on 0.6.58 Dockerfile: clone the commit, then
          go build -trimpath -buildvcs=true -tags nomatter -ldflags "-X main.buildVersion=.. -X main.buildID=.." ./cmd/gateway
  install add-on v0.6.32 Dockerfile: go install <module>/cmd/gateway@<version>, no -trimpath, no tags, default ldflags.
Both run with CGO_ENABLED=0 for the add-on target.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

GATEWAY_MODULE = "github.com/Project-Helianthus/helianthus-ebusgateway"
TARGET = {"goos": "linux", "goarch": "amd64"}
ADDON_BUILD_VERSION = "0.6.58"

SPECS = [
    {"id": "released-gateway", "reference": "released", "entry": "gateway", "form": "build", "dockerfile_entry": ("released", "addon")},
    {"id": "current-gateway", "reference": "current", "entry": "gateway", "form": "build", "dockerfile_entry": ("current", "addon"),
     "note": "the frozen gateway pin supplied as EBUSGATEWAY_VERSION to the build form of the add-on of this reference; it is not the gateway the add-on ships"},
    {"id": "pre-port-gateway", "reference": "pre-port", "entry": "gateway", "form": "install", "dockerfile_entry": ("pre-port", "addon"), "version": "v0.6.32"},
    {"id": "pre-port-gateway-canonical-pv", "reference": "pre-port", "entry": "gateway-canonical-pv", "form": "install", "dockerfile_entry": ("pre-port", "addon"),
     "note": "the frozen canonical PV v1 source supplied as the version of the install form of the add-on of this reference; it is not the gateway the add-on ships"},
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pseudo_version(item):
    when = subprocess.run(["git", "-C", str(common.donor_repo(item)), "log", "-1", "--format=%cd", "--date=format-local:%Y%m%d%H%M%S", item["commit"]], env=dict(os.environ, TZ="UTC"), stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
    return f"v0.0.0-{when}-{item['commit'][:12]}"


def toolchain():
    out = subprocess.run(["go", "version"], env=common.go_env({"GOTOOLCHAIN": "local"}), stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
    return out


def build_form(spec, item, out_path):
    scratch = common.scratch_root() / "build" / spec["id"]
    common.clean(scratch)
    scratch.mkdir(parents=True)
    clone = scratch / "src"
    subprocess.run(["git", "clone", "--no-checkout", "--quiet", str(common.donor_repo(item)), str(clone)], check=True)
    subprocess.run(["git", "-C", str(clone), "checkout", "--quiet", "--detach", item["commit"]], check=True)
    head = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
    if head != item["commit"]:
        sys.exit("checked-out HEAD differs from the pin")
    dirty = subprocess.run(["git", "-C", str(clone), "status", "--porcelain=v1", "--untracked-files=all"], stdout=subprocess.PIPE, text=True, check=True).stdout
    if dirty:
        sys.exit("clone is not clean")
    ldflags = f"-X main.buildVersion={ADDON_BUILD_VERSION} -X main.buildID={item['commit']}"
    env = common.go_env({"CGO_ENABLED": "0", "GOOS": TARGET["goos"], "GOARCH": TARGET["goarch"], "GOENV": "off", "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly",
                         "GOMODCACHE": os.environ.get("GOMODCACHE", "")})
    args = ["build", "-trimpath", "-buildvcs=true", "-tags", "nomatter", "-ldflags", ldflags, "-o", str(out_path), "./cmd/gateway"]
    result = common.go_run(args, clone, env)
    if result.returncode != 0:
        sys.exit(f"build failed for {spec['id']}: {result.stderr.strip()[-2000:]}")
    return {"command": "go build -trimpath -buildvcs=true -tags nomatter -ldflags \"" + ldflags + "\" -o gateway ./cmd/gateway", "build_args": {"BUILD_VERSION": ADDON_BUILD_VERSION, "EBUSGATEWAY_VERSION": item["commit"], "GATEWAY_TAGS": "nomatter"},
            "resolved_module_revision": item["commit"], "env": {"CGO_ENABLED": "0", "GOOS": TARGET["goos"], "GOARCH": TARGET["goarch"], "GOENV": "off", "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly", "GOWORK": "off"}}


def install_form(spec, item, out_path):
    version = spec.get("version") or pseudo_version(item)
    if not common.materialize(GATEWAY_MODULE, version):
        sys.exit(f"cannot serve {GATEWAY_MODULE}@{version} from the donor clone")
    scratch = common.scratch_root() / "build" / spec["id"]
    common.clean(scratch)
    bindir = scratch / "out"
    bindir.mkdir(parents=True)
    env = common.go_env({"CGO_ENABLED": "0", "GOOS": TARGET["goos"], "GOARCH": TARGET["goarch"], "GOPATH": str(bindir), "GOFLAGS": "", "GOTOOLCHAIN": "local"})
    result = common.go_run(["install", f"{GATEWAY_MODULE}/cmd/gateway@{version}"], scratch, env)
    if result.returncode != 0:
        sys.exit(f"install failed for {spec['id']}: {result.stderr.strip()[-2000:]}")
    built = sorted(bindir.rglob("gateway"))
    if not built:
        built = sorted(bindir.rglob("gateway*"))
    out_path.write_bytes(built[0].read_bytes())
    return {"command": f"go install {GATEWAY_MODULE}/cmd/gateway@{version}", "build_args": {"EBUSGATEWAY_VERSION": version},
            "resolved_module_revision": item["commit"], "resolved_module_version": version,
            "env": {"CGO_ENABLED": "0", "GOOS": TARGET["goos"], "GOARCH": TARGET["goarch"], "GOBIN": "/out (a cross-compiled go install writes to GOPATH/bin/<goos>_<goarch> instead)", "GOWORK": "off"}}


def record(output_dir, manifest_path, only=None):
    entries = []
    version = toolchain()
    for spec in SPECS:
        if only and spec["id"] not in only:
            continue
        item = common.entry(spec["reference"], spec["entry"])
        dockerfile = common.entry(*spec["dockerfile_entry"])
        name = f"{spec['id']}-{TARGET['goos']}-{TARGET['goarch']}"
        path = Path(output_dir).resolve() / name
        path.parent.mkdir(parents=True, exist_ok=True)
        details = (build_form if spec["form"] == "build" else install_form)(spec, item, path)
        entries.append({
            "id": spec["id"], "reference": spec["reference"], "entry": spec["entry"], "label": "gateway-cli-binary",
            "build_form": "go build in a clone of the pinned commit" if spec["form"] == "build" else "go install module@version",
            "dockerfile": {"repository": dockerfile["slug_at_pin"], "commit": dockerfile["commit"], "path": "helianthus/Dockerfile"},
            "source": {"repository": item["slug_at_pin"], "commit": item["commit"]},
            **details,
            "toolchain": version,
            "target": f"{TARGET['goos']}/{TARGET['goarch']}",
            "file": f"binaries/{name}", "sha256": sha256(path), "size": path.stat().st_size,
            **({"note": spec["note"]} if "note" in spec else {}),
        })
    if Path(manifest_path).exists():
        kept = {e["id"]: e for e in json.loads(Path(manifest_path).read_text(encoding="utf-8"))["binaries"]}
        kept.update({e["id"]: e for e in entries})
        order = [spec["id"] for spec in SPECS]
        entries = [kept[i] for i in order if i in kept]
    manifest = {"format": "helianthus-oracle-binaries/1", "binaries": entries}
    common.write(manifest_path, common.canonical(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, help="directory that receives the binaries")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--only", action="append")
    args = parser.parse_args()
    manifest = record(args.output_dir, args.manifest, set(args.only) if args.only else None)
    for item in manifest["binaries"]:
        print(item["id"], item["sha256"], item["size"])


if __name__ == "__main__":
    main()
