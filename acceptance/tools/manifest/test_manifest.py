"""CLI tests for the sealed-manifest tool.

Fixtures are synthetic. Revisions and digests are computed at runtime.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOL = Path(__file__).resolve().parent
TESTDATA = TOOL / "testdata"
PRODUCT_MANIFESTS = ROOT / "acceptance" / "manifests"
FN = "TestProxyENSObserverReplayHarness_CombinedArtifactFixtureRoutesBlameToStreamShape"
SURFACES = (
    "local-file",
    "stdin",
    "json",
    "text",
    "monitor-association",
    "error-stdout",
    "error-stderr",
    "status",
)
GG11_DIR = "scripts/fixtures/transport-gate/matter-feed-gateway-sources"
INPUTS = {"raw": "020001000300", "qualifiers": "header", "clock": "t0", "state": "idle"}
EXEMPLARS = {
    "measurement_rows.go": "driver/examples/peer/measurement_rows.go",
    "opev_rows.go": "driver/examples/peer/opev_rows.go",
    "cevc_series_rows.go": "driver/examples/peer/cevc_series_rows.go",
    "cevc_tariff_rows.go": "driver/examples/peer/cevc_tariff_rows.go",
    "growatt_pcs_rows.go": "driver/examples/can/growatt_pcs_rows.go",
    "legacy_rows.go": "driver/examples/modbus/legacy_rows.go",
    "scalar_rows.go": "driver/examples/ebus/scalar_rows.go",
    "identity_rows.go": "driver/examples/ebus/identity_rows.go",
    "write_rows.go": "driver/examples/ebus/write_rows.go",
    "diagnostic_rows.go": "driver/examples/ebus/diagnostic_rows.go",
}
MEAS = {
    "driver_instance": "drv",
    "remote_device": "remote-1",
    "entity": "ent-1",
    "feature_type": "Measurement",
    "function": "measurementListData",
    "measurementId": "326",
    "scopeType": "instant",
    "unit": "V",
    "valueType": "voltage",
}
OPEV = {
    "driver_instance": "drv",
    "remote_device": "remote-1",
    "entity": "ent-1",
    "feature_type": "LoadControl",
    "function": "loadControlLimitListData",
    "description_key": "limitId",
    "phase": "a",
}
OPEV_EXTRA = {
    "limit_id": "limit-1",
    "inverse_limit_id": "limit-1",
    "instance": "ent-1",
    "readback_instance": "ent-1",
}
SERIES = {
    "driver_instance": "drv",
    "remote_device": "remote-1",
    "entity": "ent-1",
    "feature_type": "TimeSeries",
    "function": "timeSeriesListData",
    "description_key": "seriesId",
    "series": "series-1",
    "slot": "slot-1",
}
SERIES_EXTRA = {"readback_slot": "slot-1", "readback_series": "series-1"}
TARIFF = {
    "driver_instance": "drv",
    "remote_device": "remote-1",
    "entity": "ent-1",
    "feature_type": "IncentiveTable",
    "function": "incentiveTableData",
    "description_key": "tariffId",
    "tariff": "tariff-1",
}
TARIFF_EXTRA = {"readback_tariff": "tariff-1"}
CAN = {
    "identifier": "18ff50",
    "format": "extended",
    "raw_dlc": "8",
    "effective_dlc": "8",
    "route": "selected",
    "direction": "receive",
    "endian": "little",
    "slice": "B0-B1",
}
MODBUS = {
    "command": "FBE0",
    "direction": "receive",
    "length": "11",
    "offset": "0",
    "count": "11",
}
SCALAR = {
    "command": "020001000300",
    "direction": "read",
    "opcode": "02",
    "group": "00",
    "instance": "01",
    "register": "00",
}
IDENTITY = {"command": "000600", "direction": "read", "request": "000600", "reply": "identity"}
WRITE = {"command": "write", "direction": "write", "register": "01", "appended": "value-bytes"}
DIAG = {
    "target": "dhw",
    "direction": "read",
    "family": "history",
    "selector": "indexed",
    "body_length": "8",
    "history": "indexed",
}
KEYS = (
    "row",
    "donor",
    "paths",
    "symbols",
    "assertions",
    "stays",
    "patterns",
    "destinations",
    "expectations",
    "expected_differences",
    "receipts",
)


def load_signature(filename: str) -> dict:
    text = (TESTDATA / "exemplar" / filename).read_text(encoding="utf-8")
    payload = text.split("QQ06ROW", 1)[1].strip()
    return json.loads(payload)["signature"]


def fill(signature: dict, values: dict, extra: dict | None = None) -> dict:
    missing = [field for field in signature["selector_fields"] if field not in values]
    if missing:
        raise AssertionError("missing selector values: " + ",".join(missing))
    operands = {field: values[field] for field in signature["selector_fields"]}
    if extra:
        operands.update(extra)
    return operands


def plant(root: Path, name: str, text: str) -> None:
    """Write a sidecar where the destination test binary runs.

    ``go test`` runs the binary with the package directory as its working
    directory, so a file at the module root is not visible to the test.
    """
    (root / "dest" / name).write_text(text, encoding="utf-8")


def selector_map(signature: dict, values: dict, drop: tuple[str, ...] = ()) -> dict:
    return {
        field: values[field]
        for field in signature["selector_fields"]
        if field not in drop and field in values
    }


def tool_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GOTOOLCHAIN"] = "local"
    env["GOWORK"] = "off"
    env["GOFLAGS"] = "-mod=mod"
    env["GOCACHE"] = str(ROOT / ".tmp" / "gocache")
    env["GOPROXY"] = "off"
    env["GOSUMDB"] = "off"
    env["GO111MODULE"] = "on"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=manifest@example.com",
            "-c",
            "user.name=Manifest Fixture",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.autocrlf=false",
            *args,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"git {args}\n{completed.stdout}\n{completed.stderr}")
    return completed


def git_out(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.strip()


def copy_tool(root: Path) -> Path:
    target = root / "acceptance" / "tools" / "manifest"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("main.py", "manifestlib.py", "closure.py", "gitstore.py", "patterns.py"):
        shutil.copy(TOOL / name, target / name)
    (root / "acceptance" / "manifests").mkdir(parents=True, exist_ok=True)
    return target / "main.py"


def product_strays() -> list[Path]:
    if not PRODUCT_MANIFESTS.is_dir():
        return []
    return [path for path in PRODUCT_MANIFESTS.iterdir() if path.name != ".gitkeep"]


def detail(completed: subprocess.CompletedProcess[str]) -> str:
    return f"exit={completed.returncode}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.dest = root.parent / "dest"
        self.main = copy_tool(root)
        self.sha = ""
        self.merged = ""
        self.integrated = ""
        self.sig: dict[str, dict] = {}
        self._copies = 0

    def build(self) -> None:
        shutil.copytree(TESTDATA / "donor", self.root / "closure")
        for name, rel in EXEMPLARS.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(TESTDATA / "exemplar" / name, target)
            self.sig[name] = load_signature(name)
        gateway = {
            "cmd/gateway/capture.go": "package gateway\n\nfunc Capture() int { return 1 }\n",
            "cmd/gateway/lock.go": "package gateway\n\nfunc Lock() int { return 1 }\n",
            "cmd/gateway/stub.go": "package gateway\n\nfunc Stub() int { return 1 }\n",
            "cmd/gateway/leaf_promotion_live_source.go": "package gateway\n\nfunc Leaf() int { return 1 }\n",
            "cmd/gateway/drivers.go": "package gateway\n\nfunc Drivers() int { return 1 }\n",
            "cmd/gateway/managed_sidecar_composition.go": "package gateway\n\nfunc Sidecar() int { return 1 }\n",
            "cmd/gateway/matter_feed.go": "package gateway\n\nfunc MatterFeed() int { return 1 }\n",
            "cmd/gateway/matter_old.go": "package gateway\n\nfunc MatterOld() int { return 1 }\n",
            "matter/composer.go": "package matter\n\nfunc Composer() int { return 1 }\n",
            "internal/eebusoutput/binding.go": "package eebusoutput\n\nfunc Relay() int { return 1 }\n",
            "internal/promotion/registry.go": "package promotion\n\nfunc Registry() int { return 1 }\n",
            "cmd/growatt-can-classify/main.go": "package main\n\nfunc Classify() int { return 1 }\n",
            "internal/growattcanclassify/classify.go": "package growattcanclassify\n\nfunc Classify() int { return 1 }\n",
        }
        for rel, text in gateway.items():
            self.write(rel, text)
        ledger = "\n".join([
            "cmd/growatt-can-classify/main.go\tclassifier\toffline\tGG07",
            "internal/growattcanclassify/classify.go\tclassifier\toffline\tGG07",
            "cmd/gateway/capture.go\tcapture\tr2-002\tGG10",
            "cmd/gateway/lock.go\tlock\tr2-002\tGG10",
            "cmd/gateway/stub.go\tstub\tr2-057\tGG10",
            "cmd/gateway/leaf_promotion_live_source.go\tlive\tshared\tGG10",
            "internal/eebusoutput/binding.go\trelay\tunused\tGG10",
            "internal/promotion/registry.go\tregistry\tshared\tGG10",
            "closure/closed/moved.go\tmove\tsample\tGG13",
            "closure/closed/moved.go\tmove\tsample\tGG08",
            "# synthetic ledger",
        ]) + "\n"
        self.write("tools/boundary/ledger.tsv", ledger)
        self.write_vectors()
        git(self.root, "init", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "fixture")
        self.sha = git_out(self.root, "rev-parse", "HEAD")
        shutil.copytree(TESTDATA / "destination", self.dest)
        for rel in (
            "engine/moved.go",
            "engine/split.go",
            "engine/capture.go",
            "engine/lock.go",
            "engine/stub.go",
            "engine/leaf_promotion_live_source.go",
            "engine/binding.go",
            "engine/registry.go",
            "cmd/growatt-can-classify/main.go",
            "internal/growattcanclassify/classify.go",
        ):
            path = self.dest / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("package destfile\n\nfunc Marker() int { return 1 }\n", encoding="utf-8")
        git(self.dest, "init", "-b", "main")
        git(self.dest, "add", "-A")
        git(self.dest, "commit", "-m", "merged")
        self.merged = git_out(self.dest, "rev-parse", "HEAD")
        (self.dest / "REV.txt").write_text("integrated\n", encoding="utf-8")
        git(self.dest, "add", "-A")
        git(self.dest, "commit", "-m", "integrated")
        self.integrated = git_out(self.dest, "rev-parse", "HEAD")

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_json(self, rel: str, body: dict) -> None:
        self.write(rel, json.dumps(body, indent=2, sort_keys=True) + "\n")

    def write_vectors(self) -> None:
        meas = self.sig["measurement_rows.go"]
        opev = self.sig["opev_rows.go"]
        series = self.sig["cevc_series_rows.go"]
        tariff = self.sig["cevc_tariff_rows.go"]
        can = self.sig["growatt_pcs_rows.go"]
        modbus = self.sig["legacy_rows.go"]
        scalar = self.sig["scalar_rows.go"]
        diag = self.sig["diagnostic_rows.go"]
        identity = self.sig["identity_rows.go"]
        write = self.sig["write_rows.go"]
        shared = selector_map(meas, MEAS, drop=("valueType",))
        self.write_json("vec/meas.json", {"fields": {"reading": "230"}, "inputs": {}, "selectors": selector_map(meas, MEAS)})
        self.write_json("vec/meas-current.json", {
            "fields": {"reading": "5"},
            "inputs": {},
            "selectors": selector_map(meas, {**MEAS, "valueType": "current"}),
        })
        self.write_json("vec/m326.json", {"fields": {"reading": "230"}, "inputs": {}, "selectors": shared})
        self.write_json("vec/opev.json", {"fields": {"applied": "1"}, "inputs": {}, "selectors": selector_map(opev, OPEV)})
        self.write_json("vec/opev-no-phase.json", {
            "fields": {"applied": "1"},
            "inputs": {},
            "selectors": selector_map(opev, OPEV, drop=("phase",)),
        })
        self.write_json("vec/series.json", {"fields": {"deleted": "slot"}, "inputs": {}, "selectors": selector_map(series, SERIES)})
        self.write_json("vec/tariff.json", {"fields": {"deleted": "tariff"}, "inputs": {}, "selectors": selector_map(tariff, TARIFF)})
        self.write_json("vec/can.json", {"fields": {"frame": "extended", "route": "selected"}, "inputs": {}, "selectors": selector_map(can, CAN)})
        can_211 = {**CAN, "identifier": "211"}
        can_212 = {**CAN, "identifier": "212"}
        self.write_json("vec/cmd211.json", {"fields": {"witness": "211"}, "inputs": {}, "selectors": selector_map(can, can_211)})
        self.write_json("vec/cmd212.json", {"fields": {"witness": "212"}, "inputs": {}, "selectors": selector_map(can, can_212)})
        self.write_json("vec/pcs-output.json", {"fields": {"frame": "extended", "route": "selected"}, "status": 0})
        self.write_json("vec/modbus.json", {"fields": {"register": "holding", "value": "1"}, "inputs": {}, "selectors": selector_map(modbus, MODBUS)})
        self.write_json("vec/scalar.json", {"fields": {"completion": "no-completion"}, "inputs": {}, "selectors": selector_map(scalar, SCALAR)})
        self.write_json("vec/scalar-kept.json", {"fields": {"completion": "done"}, "inputs": {}, "selectors": selector_map(scalar, SCALAR)})
        self.write_json("vec/b503.json", {"fields": {"native_outcome": "response", "transport_stamp": "epoch-1"}, "status": 0})
        self.write_json("vec/diag.json", {"fields": {"kept": "1"}, "inputs": {}, "selectors": selector_map(diag, DIAG)})
        self.write_json("vec/native.json", {"average_c": "25.0"})
        self.write_json("vec/binding.json", {"key": "temperature", "subject": "average", "value": "298.15"})
        self.write_json("vec/template.json", {
            "origin": "recorded",
            "quality": "good",
            "source": "caller",
            "timing": "t0",
            "provenance": "pinned",
        })
        self.write_json("vec/identity.json", {"fields": {"reply": "identity"}, "inputs": {}, "selectors": selector_map(identity, IDENTITY)})
        self.write_json("vec/write.json", {"fields": {"appended": "value-bytes"}, "inputs": {}, "selectors": selector_map(write, WRITE)})
        self.write_json("vec/north.json", {"fields": {"kept": "1"}, "inputs": {}, "selectors": selector_map(meas, MEAS)})
        self.write_json("vec/diff-north.json", {
            "approval": "approved-transition",
            "case": "north",
            "field": "northbound",
            "new": "present",
            "old": None,
            "old_present": False,
            "source": "gg10-lead",
        })
        self.write_json("vec/diff-status.json", {
            "approval": "approved-status",
            "case": "*",
            "field": "execution_status",
            "new": "1",
            "old": "0",
            "old_present": True,
            "source": "status-approval",
        })

    def run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.main), *args],
            cwd=str(self.root),
            env=tool_env(),
            text=True,
            capture_output=True,
        )

    def generate(self, spec: dict) -> subprocess.CompletedProcess[str]:
        path = self.root / "specs" / f"{spec['row']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(spec), encoding="utf-8")
        return self.run("generate", "--input", str(path), "--donor", str(self.root))

    def manifest_path(self, row: str) -> Path:
        return self.root / "acceptance" / "manifests" / f"{row}.json"

    def manifest(self, row: str) -> dict:
        return json.loads(self.manifest_path(row).read_text(encoding="utf-8"))

    def check(self, row: str, donor: Path | None = None, manifest: Path | None = None) -> subprocess.CompletedProcess[str]:
        path = manifest or self.manifest_path(row)
        return self.run("check", "--manifest", str(path), "--donor", str(donor or self.root))

    def compare(self, row: str, destination: Path, manifest: Path | None = None) -> subprocess.CompletedProcess[str]:
        path = manifest or self.manifest_path(row)
        return self.run("compare", "--manifest", str(path), "--destination", str(destination))

    def base(self, row: str, **kwargs: object) -> dict:
        spec = {
            "row": row,
            "donor_repository": "gateway",
            "donor_sha": self.sha,
            "moves": [],
            "new_files": [],
            "shared": [],
            "specimens": [],
            "assertions": [],
            "mapping_rows": [],
            "expectations": [],
            "expected_differences": [],
        }
        spec.update(kwargs)
        return spec

    def ref(self, role: str, path: str) -> dict:
        return {"role": role, "repository": "docs-semantic", "revision": self.sha, "path": path}

    def move(self, path: str, dest: str, repository: str = "ebusgo") -> dict:
        return {"path": path, "destination_repository": repository, "destination_path": dest}

    def bound(self, row: str, assertion: str, test: str, selectors: dict | None = None) -> dict:
        item = {
            "row": row,
            "assertion": assertion,
            "destination": {"repository": "ebusgo", "path": "dest/echo_test.go", "test": test},
        }
        if selectors:
            item["selectors"] = selectors
        return item

    def pattern(
        self,
        row: str,
        kind: str,
        cases: list[str],
        assertion: str,
        signature: dict,
        exemplar: str,
        operands: dict,
        old_symbol: str = "",
        bom: str = "",
        revision: str | None = None,
    ) -> dict:
        return {
            "row": row,
            "kind": kind,
            "cases": cases,
            "assertion": assertion,
            "old_symbol": old_symbol,
            "bom_entry": bom,
            "signature": signature,
            "exemplar": {
                "repository": "eebusreg",
                "path": exemplar,
                "revision": revision or self.sha,
            },
            "candidate": {"form": "inline", "operands": operands},
        }

    def expectation(
        self,
        case: str,
        kind: str,
        rows: list[dict],
        selectors: dict,
        references: list[dict],
        inputs: dict | None = None,
    ) -> dict:
        return {
            "case": case,
            "kind": kind,
            "rows": rows,
            "selectors": selectors,
            "inputs": dict(inputs or INPUTS),
            "references": references,
        }

    def difference(self, path: str) -> dict:
        body = json.loads((self.root / path).read_text(encoding="utf-8"))
        body.update({"repository": "docs-semantic", "revision": self.sha, "path": path})
        return body

    def private_dest(self) -> Path:
        self._copies += 1
        path = self.root.parent / f"dest-{self._copies}"
        shutil.copytree(self.dest, path)
        return path

    def result(
        self,
        repository: str,
        kind: str,
        commit: str,
        output: str = "same",
        old_status: int = 0,
        new_status: int = 0,
        differences: list | None = None,
        compared: list | None = None,
    ) -> dict:
        return {
            "repository": repository,
            "kind": kind,
            "commit": commit,
            "tested_donor_sha": self.sha,
            "tested_destination_commit": commit,
            "old_status": old_status,
            "new_status": new_status,
            "old_output": output if kind != "row" else output,
            "new_output": output,
            "differences": differences or [],
            "compared": compared or [],
            "case": "*",
        }

    def receipt(self, row: str, body: dict, checkout: Path, repository: str) -> subprocess.CompletedProcess[str]:
        path = self.root / "specs" / f"receipt-{row}-{kind_slug(body)}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body), encoding="utf-8")
        return self.run(
            "receipt",
            "--manifest",
            str(self.manifest_path(row)),
            "--input",
            str(path),
            "--repository-checkout",
            f"{repository}={checkout}",
        )

    def deletion(self, body: dict, gateway: Path | None = None) -> subprocess.CompletedProcess[str]:
        path = self.root / "specs" / f"deletion-{body['row']}.json"
        path.write_text(json.dumps(body), encoding="utf-8")
        return self.run("deletion", "--input", str(path), "--gateway", str(gateway or self.root))


def kind_slug(body: dict) -> str:
    return f"{body['kind']}-{body['commit'][:12]}"


class ManifestCLITest(unittest.TestCase):
    repo: Repo

    @classmethod
    def setUpClass(cls) -> None:
        (ROOT / ".tmp" / "gocache").mkdir(parents=True, exist_ok=True)
        (ROOT / ".tmp" / "manifest-tests").mkdir(parents=True, exist_ok=True)
        parent = Path(tempfile.mkdtemp(prefix="qq06-", dir=str(ROOT / ".tmp" / "manifest-tests")))
        cls.repo = Repo(parent / "donor")
        cls.repo.build()

    def tearDown(self) -> None:
        strays = product_strays()
        for path in strays:
            dest = ROOT / ".tmp" / "stray-manifests"
            dest.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest / path.name))
        self.assertEqual(strays, [], msg="product manifest directory changed")

    def assert_ok(self, completed: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(completed.returncode, 0, detail(completed))

    def assert_fail(self, completed: subprocess.CompletedProcess[str], *needles: str) -> None:
        self.assertNotEqual(completed.returncode, 0, detail(completed))
        for needle in needles:
            self.assertIn(needle, completed.stdout, detail(completed))

    def assert_absent(self, row: str) -> None:
        self.assertFalse(self.repo.manifest_path(row).exists(), row)
        self.assertEqual(list((self.repo.root / "acceptance" / "manifests").glob(f"{row}.*")), [])

    def test_closed_set_is_byte_identical_and_check_writes_nothing(self) -> None:
        spec = self.repo.base(
            "closed-sample",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            shared=[{"repository": "gateway", "path": "closure/closed/shared.go"}],
            new_files=[{"repository": "ebusgo", "path": "engine/extra.go"}],
        )
        first = self.repo.generate(spec)
        second = self.repo.generate(spec)
        self.assert_ok(first)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stdout, self.repo.manifest_path("closed-sample").read_text(encoding="utf-8"))
        manifest = self.repo.manifest("closed-sample")
        self.assertEqual(list(manifest), list(KEYS))
        self.assertEqual(manifest["patterns"], [])
        self.assertEqual(manifest["receipts"], [])
        self.assertEqual(manifest["donor"]["sha"], self.repo.sha)
        self.assertIn("Moved", {item["name"] for item in manifest["symbols"]})
        donor = next(item for item in manifest["paths"] if item["repository"] == "gateway")
        dest = next(item for item in manifest["paths"] if item["repository"] == "ebusgo")
        self.assertEqual(donor["paths"], ["closure/closed/moved.go", "closure/closed/shared.go"])
        self.assertEqual(dest["paths"], ["engine/extra.go", "engine/moved.go"])
        for entry in manifest["paths"]:
            payload = ("".join(path + "\n" for path in entry["paths"])).encode()
            self.assertNotIn(b"\r", payload)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), entry["sha256"])
            self.assertEqual(entry["donor_sha"], self.repo.sha)
            sibling = self.repo.root / "acceptance" / "manifests" / f"closed-sample.{entry['repository']}.lst"
            self.assertEqual(sibling.read_bytes(), payload)
        before = self.repo.manifest_path("closed-sample").read_bytes()
        self.assert_ok(self.repo.check("closed-sample"))
        self.assertEqual(self.repo.manifest_path("closed-sample").read_bytes(), before)
        self.assert_ok(self.repo.compare("closed-sample", self.repo.dest))
        self.assertEqual(self.repo.manifest_path("closed-sample").read_bytes(), before)
        clone = self.repo.root.parent / "closed-clone"
        git(self.repo.root.parent, "clone", "--depth", "1", "--no-local", str(self.repo.root), str(clone))
        git(clone, "commit", "--allow-empty", "-m", "later")
        cloned_lists = clone / "acceptance" / "manifests"
        cloned_lists.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.repo.manifest_path("closed-sample"), cloned_lists / "closed-sample.json")
        for entry in manifest["paths"]:
            name = f"closed-sample.{entry['repository']}.lst"
            shutil.copy(self.repo.root / "acceptance" / "manifests" / name, cloned_lists / name)
        completed = subprocess.run(
            [sys.executable, str(clone / "acceptance" / "tools" / "manifest" / "main.py"), "check", "--manifest", str(clone / "acceptance" / "manifests" / "closed-sample.json"), "--donor", str(clone)],
            env=tool_env(),
            text=True,
            capture_output=True,
        )
        self.assert_fail(completed, "donor-sha")

    def test_helper_outside_the_set_names_the_helper(self) -> None:
        spec = self.repo.base("outside-sample", moves=[self.repo.move("closure/outside/moved.go", "engine/outside.go")])
        self.assert_fail(self.repo.generate(spec), "outside-set: Helper")
        self.assert_absent("outside-sample")

    def test_absent_donor_path_writes_nothing(self) -> None:
        spec = self.repo.base("absent-sample", moves=[self.repo.move("closure/missing.go", "engine/missing.go")])
        self.assert_fail(self.repo.generate(spec), "absent: closure/missing.go")
        self.assert_absent("absent-sample")

    def test_mixed_host_keeps_the_whole_test_without_a_destination(self) -> None:
        spec = self.repo.base("mixed-sample", moves=[self.repo.move("closure/mixed/moved.go", "engine/mixed.go")])
        self.assert_ok(self.repo.generate(spec))
        manifest = self.repo.manifest("mixed-sample")
        self.assertEqual(manifest["assertions"], [])
        self.assertEqual(
            [(item["kind"], item["name"]) for item in manifest["stays"]],
            [("test", "TestHostComposition")],
        )
        self.assert_ok(self.repo.check("mixed-sample"))

    def test_split_mixed_function_accounts_every_assertion(self) -> None:
        assertions = [
            {
                "function": FN,
                "name": "transaction-event",
                "destination_repository": "ebusgo",
                "destination_path": "dest/echo_test.go",
                "test": "TestEcho",
            },
            {
                "function": FN,
                "name": "observed-symbol",
                "destination_repository": "ebusgo",
                "destination_path": "dest/echo_test.go",
                "test": "TestEcho",
            },
        ]
        spec = self.repo.base(
            "split-sample",
            moves=[self.repo.move("closure/split/moved.go", "engine/split.go")],
            assertions=assertions,
        )
        self.assert_ok(self.repo.generate(spec))
        manifest = self.repo.manifest("split-sample")
        transferred = {(item["function"], item["name"], tuple(item["helpers"])) for item in manifest["assertions"]}
        self.assertIn((FN, "transaction-event", ("CountTransactionEvents",)), transferred)
        self.assertIn((FN, "observed-symbol", ("ObservedSymbolCount",)), transferred)
        self.assertFalse(any(item["name"] == "completedTransactions" for item in manifest["assertions"]))
        self.assertEqual(
            [(item["kind"], item["function"], item["name"]) for item in manifest["stays"]],
            [("assertion", FN, "completedTransactions")],
        )
        self.assertTrue(any(item["kind"] == "assertion" and item["test"] == "TestEcho" for item in manifest["destinations"]))
        self.assert_ok(self.repo.check("split-sample"))
        missing = self.repo.base(
            "split-missing",
            moves=[self.repo.move("closure/split/moved.go", "engine/split.go")],
            assertions=[assertions[1]],
        )
        self.assert_fail(
            self.repo.generate(missing),
            f"unaccounted-assertion function={FN} assertion=transaction-event",
        )
        self.assert_absent("split-missing")
        omitted = self.repo.base("split-omitted", moves=[self.repo.move("closure/split/moved.go", "engine/split.go")])
        omitted_run = self.repo.generate(omitted)
        self.assert_fail(
            omitted_run,
            f"unaccounted-assertion function={FN} assertion=transaction-event",
            f"unaccounted-assertion function={FN} assertion=observed-symbol",
        )
        self.assert_absent("split-omitted")
        hosted = json.loads(self.repo.manifest_path("split-sample").read_text(encoding="utf-8"))
        hosted["assertions"] = []
        hosted["destinations"] = [item for item in hosted["destinations"] if item.get("kind") != "assertion"]
        hosted_path = self.repo.root / "acceptance" / "manifests" / "split-hosted.json"
        hosted_path.write_text(json.dumps(hosted), encoding="utf-8")
        self.assert_fail(
            self.repo.check("split-sample", manifest=hosted_path),
            f"unaccounted-assertion function={FN} assertion=transaction-event",
            f"unaccounted-assertion function={FN} assertion=observed-symbol",
        )

    def test_left_behind_test_and_historical_specimen(self) -> None:
        move = [self.repo.move("closure/left/moved.go", "engine/left.go")]
        self.assert_fail(
            self.repo.generate(self.repo.base("left-sample", moves=move)),
            "left-behind: TestOnlyMoved",
        )
        self.assert_absent("left-sample")
        self.assert_ok(self.repo.generate(self.repo.base("specimen-sample", moves=move, specimens=["TestOnlyMoved"])))
        manifest = self.repo.manifest("specimen-sample")
        self.assertEqual([(item["kind"], item["name"]) for item in manifest["stays"]], [("specimen", "TestOnlyMoved")])
        self.assertFalse(any(item.get("kind") == "assertion" for item in manifest["destinations"]))

    def test_spine_shapes_and_inline_operand_edits(self) -> None:
        opev_sig = self.repo.sig["opev_rows.go"]
        meas_sig = self.repo.sig["measurement_rows.go"]
        opev_ops = fill(opev_sig, OPEV, OPEV_EXTRA)
        meas_ops = fill(meas_sig, MEAS)
        inbound = self.repo.base(
            "batch-inbound",
            mapping_rows=[self.repo.pattern(
                "eebus-inbound", "specification", ["in-case"], "in-assert", meas_sig,
                EXEMPLARS["measurement_rows.go"], meas_ops,
            )],
            expectations=[self.repo.expectation(
                "in-case", "specification",
                [self.repo.bound("eebus-inbound", "in-assert", "TestEcho")],
                selector_map(meas_sig, MEAS),
                [self.repo.ref("specification", "vec/meas.json")],
            )],
        )
        self.assert_ok(self.repo.generate(inbound))
        self.assert_ok(self.repo.check("batch-inbound"))
        opev = self.repo.base(
            "batch-opev",
            mapping_rows=[self.repo.pattern(
                "opev-cmd", "specification", ["opev-case"], "opev-assert", opev_sig,
                EXEMPLARS["opev_rows.go"], opev_ops,
            )],
            expectations=[self.repo.expectation(
                "opev-case", "specification",
                [self.repo.bound("opev-cmd", "opev-assert", "TestEcho")],
                selector_map(opev_sig, OPEV),
                [self.repo.ref("specification", "vec/opev.json")],
            )],
        )
        first = self.repo.generate(opev)
        second = self.repo.generate(opev)
        self.assert_ok(first)
        self.assertEqual(first.stdout, second.stdout)
        self.assert_ok(self.repo.check("batch-opev"))
        unknown = self.repo.pattern(
            "unknown-row", "specification", ["opev-case"], "opev-assert",
            {"family": "spine", "inverse": "unsigned", "selector_fields": ["entity"]},
            EXEMPLARS["opev_rows.go"], {"entity": "ent-1"},
        )
        self.assert_fail(
            self.repo.generate(self.repo.base(
                "batch-unknown",
                mapping_rows=[unknown],
                expectations=opev["expectations"],
            )),
            "signature-mismatch row: unknown-row",
        )
        self.assert_absent("batch-unknown")
        other_limit = dict(opev_ops)
        other_limit["inverse_limit_id"] = "limit-2"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-other-limit",
            mapping_rows=[self.repo.pattern(
                "opev-cmd", "specification", ["opev-case"], "opev-assert", opev_sig,
                EXEMPLARS["opev_rows.go"], other_limit,
            )],
            expectations=opev["expectations"],
        )), "inverse-limit row: opev-cmd")
        other_readback = dict(opev_ops)
        other_readback["readback_instance"] = "ent-2"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-other-readback",
            mapping_rows=[self.repo.pattern(
                "opev-cmd", "specification", ["opev-case"], "opev-assert", opev_sig,
                EXEMPLARS["opev_rows.go"], other_readback,
            )],
            expectations=opev["expectations"],
        )), "readback-instance row: opev-cmd")
        renamed = dict(meas_ops)
        renamed["feature_type"] = "LoadControl"
        renamed["function"] = "loadControlLimitListData"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-renamed",
            mapping_rows=[self.repo.pattern(
                "meas-as-load", "specification", ["in-case"], "in-assert", meas_sig,
                EXEMPLARS["opev_rows.go"], renamed,
            )],
            expectations=[self.repo.expectation(
                "in-case", "specification",
                [self.repo.bound("meas-as-load", "in-assert", "TestEcho")],
                {field: renamed[field] for field in meas_sig["selector_fields"]},
                [self.repo.ref("specification", "vec/meas.json")],
            )],
        )), "signature-mismatch row: meas-as-load")
        dropped = json.loads(json.dumps(opev_sig))
        dropped["selector_fields"] = [field for field in dropped["selector_fields"] if field != "description_key"]
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-drop-key",
            mapping_rows=[self.repo.pattern(
                "opev-cmd", "specification", ["opev-case"], "opev-assert", dropped,
                EXEMPLARS["opev_rows.go"], {key: value for key, value in opev_ops.items() if key != "description_key"},
            )],
            expectations=opev["expectations"],
        )), "signature-mismatch row: opev-cmd")
        no_entity = json.loads(json.dumps(opev_sig))
        no_entity["selector_fields"] = [field for field in no_entity["selector_fields"] if field != "entity"]
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-no-entity",
            mapping_rows=[self.repo.pattern(
                "opev-cmd", "specification", ["opev-case"], "opev-assert", no_entity,
                EXEMPLARS["opev_rows.go"], {key: value for key, value in opev_ops.items() if key != "entity"},
            )],
            expectations=opev["expectations"],
        )), "signature-mismatch row: opev-cmd")
        other_inverse = json.loads(json.dumps(opev_sig))
        other_inverse["inverse"] = "other-pattern"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-other-inverse",
            mapping_rows=[self.repo.pattern(
                "opev-cmd", "specification", ["opev-case"], "opev-assert", other_inverse,
                EXEMPLARS["opev_rows.go"], opev_ops,
            )],
            expectations=opev["expectations"],
        )), "signature-mismatch row: opev-cmd")
        no_phase = self.repo.base(
            "batch-no-phase",
            mapping_rows=[self.repo.pattern(
                "opev-cmd", "specification", ["bare-case"], "opev-assert", opev_sig,
                EXEMPLARS["opev_rows.go"], opev_ops,
            )],
            expectations=[self.repo.expectation(
                "bare-case", "specification",
                [self.repo.bound("opev-cmd", "opev-assert", "TestEcho")],
                selector_map(opev_sig, OPEV, drop=("phase",)),
                [self.repo.ref("specification", "vec/opev-no-phase.json")],
            )],
        )
        self.assert_fail(self.repo.generate(no_phase), "selector-mismatch row: opev-cmd", "field: phase")
        no_value = json.loads(json.dumps(meas_sig))
        no_value["selector_fields"] = [field for field in no_value["selector_fields"] if field != "valueType"]
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-no-valuetype",
            mapping_rows=[self.repo.pattern(
                "326-current", "specification", ["in-case"], "current-assert", no_value,
                EXEMPLARS["measurement_rows.go"], meas_ops,
            )],
            expectations=[self.repo.expectation(
                "in-case", "specification",
                [self.repo.bound("326-current", "current-assert", "TestCurrent")],
                selector_map(meas_sig, MEAS, drop=("valueType",)),
                [self.repo.ref("specification", "vec/m326.json")],
            )],
        )), "signature-mismatch row: 326-current")
        phase_path = self.repo.root / "acceptance" / "manifests" / "opev-phase.json"
        entity_path = self.repo.root / "acceptance" / "manifests" / "opev-entity.json"
        shutil.copy(self.repo.manifest_path("batch-opev"), phase_path)
        shutil.copy(self.repo.manifest_path("batch-opev"), entity_path)
        phase = json.loads(phase_path.read_text(encoding="utf-8"))
        phase["patterns"][0]["candidate"]["operands"]["phase"] = "b"
        phase_path.write_text(json.dumps(phase), encoding="utf-8")
        self.assertEqual(phase["patterns"][0]["exemplar"]["path"], EXEMPLARS["opev_rows.go"])
        self.assertEqual(phase["expectations"][0]["selectors"]["phase"], "a")
        self.assert_fail(self.repo.check("batch-opev", manifest=phase_path), "selector-mismatch row: opev-cmd", "field: phase")
        entity = json.loads(entity_path.read_text(encoding="utf-8"))
        entity["patterns"][0]["candidate"]["operands"]["entity"] = "ent-9"
        entity_path.write_text(json.dumps(entity), encoding="utf-8")
        self.assert_fail(self.repo.check("batch-opev", manifest=entity_path), "selector-mismatch row: opev-cmd", "field: entity")

    def test_cevc_shapes(self) -> None:
        series_sig = self.repo.sig["cevc_series_rows.go"]
        tariff_sig = self.repo.sig["cevc_tariff_rows.go"]
        series_ops = fill(series_sig, SERIES, SERIES_EXTRA)
        tariff_ops = fill(tariff_sig, TARIFF, TARIFF_EXTRA)
        spec = self.repo.base(
            "batch-cevc",
            mapping_rows=[
                self.repo.pattern(
                    "cevc-series", "specification", ["series-case"], "series-assert", series_sig,
                    EXEMPLARS["cevc_series_rows.go"], series_ops,
                ),
                self.repo.pattern(
                    "cevc-tariff", "specification", ["tariff-case"], "tariff-assert", tariff_sig,
                    EXEMPLARS["cevc_tariff_rows.go"], tariff_ops,
                ),
            ],
            expectations=[
                self.repo.expectation(
                    "series-case", "specification",
                    [self.repo.bound("cevc-series", "series-assert", "TestEcho")],
                    selector_map(series_sig, SERIES),
                    [self.repo.ref("specification", "vec/series.json")],
                ),
                self.repo.expectation(
                    "tariff-case", "specification",
                    [self.repo.bound("cevc-tariff", "tariff-assert", "TestEcho")],
                    selector_map(tariff_sig, TARIFF),
                    [self.repo.ref("specification", "vec/tariff.json")],
                ),
            ],
        )
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.check("batch-cevc"))
        dropped = json.loads(json.dumps(series_sig))
        dropped["selector_fields"] = [field for field in dropped["selector_fields"] if field != "slot"]
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-drop-slot",
            mapping_rows=[self.repo.pattern(
                "cevc-series", "specification", ["series-case"], "series-assert", dropped,
                EXEMPLARS["cevc_series_rows.go"],
                {key: value for key, value in series_ops.items() if key != "slot"},
            )],
            expectations=[spec["expectations"][0]],
        )), "signature-mismatch row: cevc-series")
        swapped = json.loads(json.dumps(series_sig))
        swapped["inverse"] = "same-tariff"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-swap-inverse",
            mapping_rows=[self.repo.pattern(
                "cevc-series", "specification", ["series-case"], "series-assert", swapped,
                EXEMPLARS["cevc_series_rows.go"], series_ops,
            )],
            expectations=[spec["expectations"][0]],
        )), "signature-mismatch row: cevc-series")
        bad_series = dict(series_ops)
        bad_series["readback_series"] = "series-2"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-bad-series",
            mapping_rows=[self.repo.pattern(
                "cevc-series", "specification", ["series-case"], "series-assert", series_sig,
                EXEMPLARS["cevc_series_rows.go"], bad_series,
            )],
            expectations=[spec["expectations"][0]],
        )), "readback-series row: cevc-series")
        bad_tariff = dict(tariff_ops)
        bad_tariff["readback_tariff"] = "tariff-2"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-bad-tariff",
            mapping_rows=[self.repo.pattern(
                "cevc-tariff", "specification", ["tariff-case"], "tariff-assert", tariff_sig,
                EXEMPLARS["cevc_tariff_rows.go"], bad_tariff,
            )],
            expectations=[spec["expectations"][1]],
        )), "readback-tariff row: cevc-tariff")

    def test_326_case_binding_and_per_assertion_compare(self) -> None:
        meas_sig = self.repo.sig["measurement_rows.go"]
        voltage_ops = fill(meas_sig, MEAS)
        current_values = {**MEAS, "valueType": "current"}
        current_ops = fill(meas_sig, current_values)
        separate = self.repo.base(
            "batch-326-separate",
            mapping_rows=[
                self.repo.pattern("326-voltage", "specification", ["voltage-case"], "voltage-assert", meas_sig, EXEMPLARS["measurement_rows.go"], voltage_ops),
                self.repo.pattern("326-current", "specification", ["current-case"], "current-assert", meas_sig, EXEMPLARS["measurement_rows.go"], current_ops),
            ],
            expectations=[
                self.repo.expectation(
                    "voltage-case", "specification",
                    [self.repo.bound("326-voltage", "voltage-assert", "TestVoltage")],
                    selector_map(meas_sig, MEAS),
                    [self.repo.ref("specification", "vec/meas.json")],
                ),
                self.repo.expectation(
                    "current-case", "specification",
                    [self.repo.bound("326-current", "current-assert", "TestCurrent")],
                    selector_map(meas_sig, current_values),
                    [self.repo.ref("specification", "vec/meas-current.json")],
                ),
            ],
        )
        self.assert_ok(self.repo.generate(separate))
        removed = self.repo.root / "acceptance" / "manifests" / "326-removed.json"
        shutil.copy(self.repo.manifest_path("batch-326-separate"), removed)
        body = json.loads(removed.read_text(encoding="utf-8"))
        for pattern in body["patterns"]:
            if pattern["row"] == "326-current":
                pattern["cases"] = []
        removed.write_text(json.dumps(body), encoding="utf-8")
        self.assert_fail(self.repo.check("batch-326-separate", manifest=removed), "row: 326-current")
        self.assert_fail(self.repo.compare("batch-326-separate", self.repo.dest, manifest=removed), "row: 326-current")
        stolen = self.repo.root / "acceptance" / "manifests" / "326-stolen.json"
        shutil.copy(self.repo.manifest_path("batch-326-separate"), stolen)
        body = json.loads(stolen.read_text(encoding="utf-8"))
        for pattern in body["patterns"]:
            if pattern["row"] == "326-current":
                pattern["cases"] = ["voltage-case"]
        stolen.write_text(json.dumps(body), encoding="utf-8")
        self.assert_fail(self.repo.check("batch-326-separate", manifest=stolen), "row: 326-current")
        self.assert_fail(self.repo.compare("batch-326-separate", self.repo.dest, manifest=stolen), "row: 326-current")
        shared_selectors = selector_map(meas_sig, MEAS, drop=("valueType",))
        shared = self.repo.base(
            "batch-326-shared",
            mapping_rows=[
                self.repo.pattern("326-voltage", "specification", ["m326"], "voltage-assert", meas_sig, EXEMPLARS["measurement_rows.go"], voltage_ops),
                self.repo.pattern("326-current", "specification", ["m326"], "current-assert", meas_sig, EXEMPLARS["measurement_rows.go"], current_ops),
            ],
            expectations=[self.repo.expectation(
                "m326", "specification",
                [
                    self.repo.bound("326-voltage", "voltage-assert", "TestVoltage", {"valueType": "voltage"}),
                    self.repo.bound("326-current", "current-assert", "TestCurrent", {"valueType": "current"}),
                ],
                shared_selectors,
                [self.repo.ref("specification", "vec/m326.json")],
            )],
        )
        self.assert_ok(self.repo.generate(shared))
        self.assert_ok(self.repo.check("batch-326-shared"))
        compared = self.repo.compare("batch-326-shared", self.repo.dest)
        self.assert_ok(compared)
        self.assertIn("assertion=voltage-assert", compared.stdout)
        self.assertIn("test=TestVoltage", compared.stdout)
        self.assertIn("assertion=current-assert", compared.stdout)
        self.assertIn("test=TestCurrent", compared.stdout)
        self.assertIn("result=pass", compared.stdout)
        mutated = self.repo.private_dest()
        plant(mutated, "mutate-second", "1\n")
        self.assert_ok(self.repo.check("batch-326-shared"))
        failed = self.repo.compare("batch-326-shared", mutated)
        self.assert_fail(failed, "assertion=current-assert", "field=reading", "expected=230", "observed=other")
        self.assertIn("assertion=voltage-assert", failed.stdout)
        self.assertTrue(any("assertion=voltage-assert" in line and line.endswith("result=pass") for line in failed.stdout.splitlines()), detail(failed))
        package = subprocess.run(["go", "test", "./dest"], cwd=str(mutated), env=tool_env(), text=True, capture_output=True)
        self.assertNotEqual(package.returncode, 0, package.stdout + package.stderr)
        absent = self.repo.private_dest()
        echo = absent / "dest" / "echo_test.go"
        echo.write_text(echo.read_text(encoding="utf-8").replace("func TestCurrent(t *testing.T) { report(t, true) }\n", "", 1), encoding="utf-8")
        quiet = tool_env()
        quiet["MANIFEST_PINNED_FIELDS"] = "{}"
        package_ok = subprocess.run(["go", "test", "./dest"], cwd=str(absent), env=quiet, text=True, capture_output=True)
        self.assertEqual(package_ok.returncode, 0, package_ok.stdout + package_ok.stderr)
        missing = self.repo.compare("batch-326-shared", absent)
        self.assert_fail(missing, "not-executed case=m326 row=326-current assertion=current-assert test=TestCurrent")
        self.assertTrue(any("assertion=voltage-assert" in line and "result=pass" in line for line in missing.stdout.splitlines()), detail(missing))

    def test_protocol_shapes_do_not_substitute(self) -> None:
        can_sig = self.repo.sig["growatt_pcs_rows.go"]
        modbus_sig = self.repo.sig["legacy_rows.go"]
        scalar_sig = self.repo.sig["scalar_rows.go"]
        identity_sig = self.repo.sig["identity_rows.go"]
        write_sig = self.repo.sig["write_rows.go"]
        pcs = self.repo.base(
            "batch-pcs-shape",
            mapping_rows=[self.repo.pattern(
                "pcs-shape", "specification", ["pcs-shape-case"], "pcs-shape-assert", can_sig,
                EXEMPLARS["growatt_pcs_rows.go"], fill(can_sig, CAN),
            )],
            expectations=[self.repo.expectation(
                "pcs-shape-case", "specification",
                [self.repo.bound("pcs-shape", "pcs-shape-assert", "TestPCS")],
                selector_map(can_sig, CAN),
                [self.repo.ref("specification", "vec/can.json")],
            )],
        )
        self.assert_ok(self.repo.generate(pcs))
        self.assert_ok(self.repo.check("batch-pcs-shape"))
        wrong_direction = dict(CAN)
        wrong_direction["direction"] = "transmit"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-can-direction",
            mapping_rows=[self.repo.pattern(
                "pcs-shape", "specification", ["pcs-shape-case"], "pcs-shape-assert", can_sig,
                EXEMPLARS["growatt_pcs_rows.go"], fill(can_sig, wrong_direction),
            )],
            expectations=pcs["expectations"],
        )), "selector-mismatch row: pcs-shape", "field: direction")
        big_endian = dict(CAN)
        big_endian["endian"] = "big"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-can-endian",
            mapping_rows=[self.repo.pattern(
                "pcs-shape", "specification", ["pcs-shape-case"], "pcs-shape-assert", can_sig,
                EXEMPLARS["growatt_pcs_rows.go"], fill(can_sig, big_endian),
            )],
            expectations=pcs["expectations"],
        )), "selector-mismatch row: pcs-shape", "field: endian")
        legacy = self.repo.base(
            "batch-modbus",
            mapping_rows=[self.repo.pattern(
                "legacy-row", "specification", ["legacy-case"], "legacy-assert", modbus_sig,
                EXEMPLARS["legacy_rows.go"], fill(modbus_sig, MODBUS),
            )],
            expectations=[self.repo.expectation(
                "legacy-case", "specification",
                [self.repo.bound("legacy-row", "legacy-assert", "TestEcho")],
                selector_map(modbus_sig, MODBUS),
                [self.repo.ref("specification", "vec/modbus.json")],
            )],
        )
        self.assert_ok(self.repo.generate(legacy))
        wrong_length = dict(MODBUS)
        wrong_length["length"] = "13"
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-modbus-length",
            mapping_rows=[self.repo.pattern(
                "legacy-row", "specification", ["legacy-case"], "legacy-assert", modbus_sig,
                EXEMPLARS["legacy_rows.go"], fill(modbus_sig, wrong_length),
            )],
            expectations=legacy["expectations"],
        )), "selector-mismatch row: legacy-row", "field: length")
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-scalar-as-identity",
            mapping_rows=[self.repo.pattern(
                "scalar-row", "specification", ["legacy-case"], "legacy-assert", scalar_sig,
                EXEMPLARS["identity_rows.go"], fill(scalar_sig, SCALAR),
            )],
            expectations=[self.repo.expectation(
                "legacy-case", "specification",
                [self.repo.bound("scalar-row", "legacy-assert", "TestEcho")],
                selector_map(scalar_sig, SCALAR),
                [self.repo.ref("specification", "vec/scalar.json")],
            )],
        )), "signature-mismatch row: scalar-row")
        self.assert_ok(self.repo.generate(self.repo.base(
            "batch-identity",
            mapping_rows=[self.repo.pattern(
                "identity-row", "specification", ["id-case"], "id-assert", identity_sig,
                EXEMPLARS["identity_rows.go"], fill(identity_sig, IDENTITY),
            )],
            expectations=[self.repo.expectation(
                "id-case", "specification",
                [self.repo.bound("identity-row", "id-assert", "TestEcho")],
                selector_map(identity_sig, IDENTITY),
                [self.repo.ref("specification", "vec/identity.json")],
            )],
        )))
        self.assert_fail(self.repo.generate(self.repo.base(
            "batch-write-as-scalar",
            mapping_rows=[self.repo.pattern(
                "write-row", "specification", ["id-case"], "id-assert", write_sig,
                EXEMPLARS["scalar_rows.go"], fill(write_sig, WRITE),
            )],
            expectations=[self.repo.expectation(
                "id-case", "specification",
                [self.repo.bound("write-row", "id-assert", "TestEcho")],
                selector_map(write_sig, WRITE),
                [self.repo.ref("specification", "vec/write.json")],
            )],
        )), "signature-mismatch row: write-row")

    def test_binding_release_11(self) -> None:
        meas_sig = self.repo.sig["measurement_rows.go"]
        references = [
            self.repo.ref("donor-native", "vec/native.json"),
            self.repo.ref("new-binding", "vec/binding.json"),
            self.repo.ref("caller-template", "vec/template.json"),
        ]
        spec = self.repo.base(
            "batch-bind",
            mapping_rows=[self.repo.pattern(
                "bind-313", "binding", ["bind-case"], "bind-assert", meas_sig,
                EXEMPLARS["measurement_rows.go"], fill(meas_sig, MEAS),
            )],
            expectations=[self.repo.expectation(
                "bind-case", "binding",
                [self.repo.bound("bind-313", "bind-assert", "TestBinding")],
                selector_map(meas_sig, MEAS),
                references,
            )],
        )
        first = self.repo.generate(spec)
        second = self.repo.generate(spec)
        self.assert_ok(first)
        self.assertEqual(first.stdout, second.stdout)
        manifest = self.repo.manifest("batch-bind")
        roles = [item["role"] for item in manifest["expectations"][0]["references"]]
        self.assertEqual(roles, ["donor-native", "new-binding", "caller-template"])
        binding = next(item["projection"] for item in manifest["expectations"][0]["references"] if item["role"] == "new-binding")
        self.assertEqual(binding["value"], "298.15")
        self.assertFalse(any(key in binding for key in ("origin", "quality", "source", "timing", "provenance")))
        self.assert_ok(self.repo.check("batch-bind"))
        compared = self.repo.compare("batch-bind", self.repo.dest)
        self.assert_ok(compared)
        self.assertIn("field=binding.value expected=298.15 observed=298.15", compared.stdout)
        self.assertIn("field=native.average_c expected=25.0 observed=25.0", compared.stdout)
        native = self.repo.private_dest()
        plant(native, "mutate-observed", "native.average_c=0\n")
        self.assert_ok(self.repo.check("batch-bind"))
        self.assert_fail(self.repo.compare("batch-bind", native), "field=native.average_c", "expected=25.0", "observed=0", "assertion=bind-assert")
        wrong_binding = self.repo.private_dest()
        plant(wrong_binding, "mutate-observed", "binding.value=300\n")
        self.assert_fail(self.repo.compare("batch-bind", wrong_binding), "field=binding.value", "expected=298.15", "observed=300")
        meta = self.repo.private_dest()
        plant(meta, "mutate-origin", "other-origin\n")
        meta_run = self.repo.compare("batch-bind", meta)
        self.assert_fail(meta_run, "field=template.origin", "expected=recorded", "observed=other-origin")
        self.assertIn("observed=298.15", meta_run.stdout)
        skipped = self.repo.private_dest()
        plant(skipped, "skip-binding", "1\n")
        self.assert_ok(self.repo.check("batch-bind"))
        self.assert_fail(self.repo.compare("batch-bind", skipped), "unexecuted-binding assertion=bind-assert")
        incomplete = json.loads(json.dumps(spec))
        incomplete["row"] = "batch-bind-missing"
        incomplete["expectations"][0]["references"] = references[:2]
        self.assert_fail(self.repo.generate(incomplete), "binding-operand: caller-template")
        self.assert_absent("batch-bind-missing")
        unbound = json.loads(json.dumps(spec))
        unbound["row"] = "batch-bind-unbound"
        unbound["expectations"][0]["rows"][0]["assertion"] = "other-assert"
        self.assert_fail(self.repo.generate(unbound), "row: bind-313")
        self.assert_absent("batch-bind-unbound")

    def test_bb02_pcs_and_command_witnesses(self) -> None:
        modbus_sig = self.repo.sig["legacy_rows.go"]
        can_sig = self.repo.sig["growatt_pcs_rows.go"]
        diag_sig = self.repo.sig["diagnostic_rows.go"]
        bb02 = self.repo.base(
            "batch-bb02",
            mapping_rows=[self.repo.pattern(
                "bb02-register", "specification", ["bb02-case"], "bb02-assert", modbus_sig,
                EXEMPLARS["legacy_rows.go"], fill(modbus_sig, MODBUS),
            )],
            expectations=[self.repo.expectation(
                "bb02-case", "specification",
                [self.repo.bound("bb02-register", "bb02-assert", "TestBB02")],
                selector_map(modbus_sig, MODBUS),
                [self.repo.ref("specification", "vec/modbus.json")],
            )],
        )
        self.assert_ok(self.repo.generate(bb02))
        manifest = self.repo.manifest("batch-bb02")
        self.assertEqual(manifest["patterns"][0]["old_symbol"], "")
        self.assertEqual(manifest["patterns"][0]["bom_entry"], "")
        self.assertNotIn("donor-output", [item["role"] for item in manifest["expectations"][0]["references"]])
        self.assertEqual(manifest["symbols"], [])
        before = (self.repo.root / "vec" / "modbus.json").read_text(encoding="utf-8")
        (self.repo.root / "vec" / "modbus.json").write_text('{"fields":{"value":"9"}}\n', encoding="utf-8")
        self.assert_ok(self.repo.check("batch-bb02"))
        compared = self.repo.compare("batch-bb02", self.repo.dest)
        self.assert_ok(compared)
        self.assertIn("field=value expected=1 observed=1", compared.stdout)
        (self.repo.root / "vec" / "modbus.json").write_text(before, encoding="utf-8")
        tampered = self.repo.root / "acceptance" / "manifests" / "bb02-tampered.json"
        shutil.copy(self.repo.manifest_path("batch-bb02"), tampered)
        body = json.loads(tampered.read_text(encoding="utf-8"))
        body["expectations"][0]["references"][0]["projection"]["fields"]["value"] = "9"
        tampered.write_text(json.dumps(body), encoding="utf-8")
        self.assert_fail(self.repo.check("batch-bb02", manifest=tampered), "mutated:")
        self.assert_fail(self.repo.compare("batch-bb02", self.repo.dest, manifest=tampered), "mutated:")
        wrong = self.repo.private_dest()
        plant(wrong, "mutate-observed", "value=2\n")
        self.assert_ok(self.repo.check("batch-bb02"))
        self.assert_fail(self.repo.compare("batch-bb02", wrong), "field=value", "expected=1", "observed=2", "assertion=bb02-assert")
        can_211 = {**CAN, "identifier": "211"}
        can_212 = {**CAN, "identifier": "212"}
        mixed = self.repo.base(
            "batch-can",
            mapping_rows=[
                self.repo.pattern(
                    "pcs-row", "donor-backed", ["pcs-case"], "pcs-assert", can_sig,
                    EXEMPLARS["growatt_pcs_rows.go"], fill(can_sig, CAN),
                    old_symbol="ReadPCS", bom="pcs-frame",
                ),
                self.repo.pattern(
                    "v108-211", "specification", ["cmd-211"], "assert-211", can_sig,
                    EXEMPLARS["growatt_pcs_rows.go"], fill(can_sig, can_211),
                ),
                self.repo.pattern(
                    "v108-212", "specification", ["cmd-212"], "assert-212", can_sig,
                    EXEMPLARS["growatt_pcs_rows.go"], fill(can_sig, can_212),
                ),
            ],
            expectations=[
                self.repo.expectation(
                    "pcs-case", "donor-backed",
                    [self.repo.bound("pcs-row", "pcs-assert", "TestPCS")],
                    selector_map(can_sig, CAN),
                    [self.repo.ref("donor-output", "vec/pcs-output.json")],
                ),
                self.repo.expectation(
                    "cmd-211", "specification",
                    [self.repo.bound("v108-211", "assert-211", "TestCmd211")],
                    selector_map(can_sig, can_211),
                    [self.repo.ref("specification", "vec/cmd211.json")],
                ),
                self.repo.expectation(
                    "cmd-212", "specification",
                    [self.repo.bound("v108-212", "assert-212", "TestCmd212")],
                    selector_map(can_sig, can_212),
                    [self.repo.ref("specification", "vec/cmd212.json")],
                ),
            ],
        )
        self.assert_ok(self.repo.generate(mixed))
        for pattern in self.repo.manifest("batch-can")["patterns"]:
            if pattern["row"] != "pcs-row":
                self.assertEqual(pattern["old_symbol"], "")
                self.assertEqual(pattern["bom_entry"], "")
        self.assert_ok(self.repo.check("batch-can"))
        ran = self.repo.compare("batch-can", self.repo.dest)
        self.assert_ok(ran)
        self.assertIn("assertion=pcs-assert", ran.stdout)
        self.assertIn("assertion=assert-211", ran.stdout)
        self.assertIn("assertion=assert-212", ran.stdout)
        lost = json.loads(json.dumps(mixed))
        lost["row"] = "batch-can-lost"
        lost["expectations"][0]["references"] = []
        self.assert_fail(self.repo.generate(lost), "donor-output: pcs-row")
        self.assert_absent("batch-can-lost")
        stripped = self.repo.root / "acceptance" / "manifests" / "can-stripped.json"
        shutil.copy(self.repo.manifest_path("batch-can"), stripped)
        body = json.loads(stripped.read_text(encoding="utf-8"))
        for expectation in body["expectations"]:
            if expectation["case"] == "pcs-case":
                expectation["references"] = []
        stripped.write_text(json.dumps(body), encoding="utf-8")
        self.assert_fail(self.repo.check("batch-can", manifest=stripped), "donor-output: pcs-row")
        b503 = self.repo.base(
            "batch-b503",
            mapping_rows=[self.repo.pattern(
                "b503-row", "donor-backed", ["b503-case"], "b503-assert", diag_sig,
                EXEMPLARS["diagnostic_rows.go"], fill(diag_sig, DIAG),
                old_symbol="ReadDiagnostic", bom="b503-history",
            )],
            expectations=[self.repo.expectation(
                "b503-case", "donor-backed",
                [self.repo.bound("b503-row", "b503-assert", "TestB503")],
                selector_map(diag_sig, DIAG),
                [self.repo.ref("donor-output", "vec/b503.json")],
            )],
        )
        self.assert_ok(self.repo.generate(b503))
        b503_run = self.repo.compare("batch-b503", self.repo.dest)
        self.assert_ok(b503_run)
        self.assertIn("field=native_outcome expected=response observed=response", b503_run.stdout)
        self.assertIn("field=transport_stamp expected=epoch-1 observed=epoch-1", b503_run.stdout)

    def test_history_input_and_shared_test_function(self) -> None:
        scalar_sig = self.repo.sig["scalar_rows.go"]
        wrong_inputs = {"raw": "wrong-target", "qualifiers": "history", "clock": "t0", "state": "indexed"}
        kept_inputs = {"raw": "kept-target", "qualifiers": "history", "clock": "t1", "state": "indexed"}
        spec = self.repo.base(
            "batch-history",
            mapping_rows=[self.repo.pattern(
                "history-row", "specification", ["wrong-target", "kept-case"], "hist-assert", scalar_sig,
                EXEMPLARS["scalar_rows.go"], fill(scalar_sig, SCALAR),
            )],
            expectations=[
                self.repo.expectation(
                    "wrong-target", "specification",
                    [self.repo.bound("history-row", "hist-assert", "TestHistory")],
                    selector_map(scalar_sig, SCALAR),
                    [self.repo.ref("specification", "vec/scalar.json")],
                    wrong_inputs,
                ),
                self.repo.expectation(
                    "kept-case", "specification",
                    [self.repo.bound("history-row", "hist-assert", "TestHistory")],
                    selector_map(scalar_sig, SCALAR),
                    [self.repo.ref("specification", "vec/scalar-kept.json")],
                    kept_inputs,
                ),
            ],
        )
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.compare("batch-history", self.repo.dest))
        dropped = self.repo.private_dest()
        plant(dropped, "drop-case", "wrong-target\n")
        go = subprocess.run(
            ["go", "test", "-count=1", "-run", "^TestHistory$", "./dest"],
            cwd=str(dropped),
            env={**tool_env(), "MANIFEST_CASE": "wrong-target"},
            text=True,
            capture_output=True,
        )
        self.assertEqual(go.returncode, 0, go.stdout + go.stderr)
        self.assert_fail(
            self.repo.compare("batch-history", dropped),
            "not-executed case=wrong-target row=history-row assertion=hist-assert test=TestHistory",
        )
        self.assertTrue(any("case=kept-case" in line and "result=pass" in line for line in self.repo.compare("batch-history", self.repo.dest).stdout.splitlines()))
        stuck_manifest = self.repo.root / "acceptance" / "manifests" / "history-stuck.json"
        shutil.copy(self.repo.manifest_path("batch-history"), stuck_manifest)
        body = json.loads(stuck_manifest.read_text(encoding="utf-8"))
        for expectation in body["expectations"]:
            if expectation["case"] == "wrong-target":
                expectation["inputs"]["raw"] = "no-response"
        stuck_manifest.write_text(json.dumps(body), encoding="utf-8")
        stuck = self.repo.private_dest()
        plant(stuck, "stick-raw", "wrong-target\n")
        self.assert_ok(self.repo.check("batch-history", manifest=stuck_manifest))
        stuck_run = self.repo.compare("batch-history", stuck, manifest=stuck_manifest)
        self.assert_fail(stuck_run, "input-mismatch", "case=wrong-target", "field=raw", "expected=no-response", "observed=wrong-target")
        self.assertIn("field=completion expected=no-completion observed=no-completion", stuck_run.stdout)

    def test_approved_absence_and_extra_field(self) -> None:
        meas_sig = self.repo.sig["measurement_rows.go"]
        spec = self.repo.base(
            "batch-north",
            mapping_rows=[self.repo.pattern(
                "north-row", "specification", ["north"], "north-assert", meas_sig,
                EXEMPLARS["measurement_rows.go"], fill(meas_sig, MEAS),
            )],
            expectations=[self.repo.expectation(
                "north", "specification",
                [self.repo.bound("north-row", "north-assert", "TestEcho")],
                selector_map(meas_sig, MEAS),
                [self.repo.ref("specification", "vec/north.json")],
            )],
            expected_differences=[self.repo.difference("vec/diff-north.json")],
        )
        self.assert_ok(self.repo.generate(spec))
        approved = self.repo.private_dest()
        plant(approved, "approved-new", "northbound=present\n")
        self.assert_ok(self.repo.compare("batch-north", approved))
        extra = self.repo.private_dest()
        plant(extra, "approved-new", "northbound=present\n")
        plant(extra, "extra-field", "extra a b\n")
        self.assert_fail(self.repo.compare("batch-north", extra), "unapproved-difference: extra")

    def test_receipts_and_gg13_deletion(self) -> None:
        spec = self.repo.base("receipt-move", moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")])
        self.assert_ok(self.repo.generate(spec))
        original = self.repo.manifest_path("receipt-move").read_bytes()
        wrong_donor = self.repo.result("ebusgo", "row", self.repo.merged)
        wrong_donor["tested_donor_sha"] = "different-donor"
        self.assert_fail(self.repo.receipt("receipt-move", wrong_donor, self.repo.dest, "ebusgo"), "donor-sha")
        self.assertEqual(self.repo.manifest_path("receipt-move").read_bytes(), original)
        wrong_commit = self.repo.result("ebusgo", "row", self.repo.integrated)
        wrong_commit["tested_destination_commit"] = self.repo.merged
        self.assert_fail(self.repo.receipt("receipt-move", wrong_commit, self.repo.dest, "ebusgo"), "destination-commit")
        self.assertEqual(self.repo.manifest_path("receipt-move").read_bytes(), original)
        unequal = self.repo.result("ebusgo", "row", self.repo.merged)
        unequal["new_output"] = "different"
        self.assert_fail(self.repo.receipt("receipt-move", unequal, self.repo.dest, "ebusgo"), "unapproved-difference: output")
        status = self.repo.result("ebusgo", "row", self.repo.merged, old_status=0, new_status=1)
        self.assert_fail(self.repo.receipt("receipt-move", status, self.repo.dest, "ebusgo"), "unapproved-difference: execution_status")
        self.assertEqual(self.repo.manifest_path("receipt-move").read_bytes(), original)
        self.assert_ok(self.repo.receipt("receipt-move", self.repo.result("ebusgo", "row", self.repo.merged), self.repo.dest, "ebusgo"))
        stored = self.repo.manifest("receipt-move")["receipts"]
        self.assertEqual(stored[0]["outcome"], "equal")
        self.assertEqual(stored[0]["old_status"], 0)
        self.assertEqual(stored[0]["new_status"], 0)
        self.assertEqual(stored[0]["destination_commit"], self.repo.merged)
        self.assert_fail(
            self.repo.receipt("receipt-move", self.repo.result("ebusgo", "whole-session", self.repo.merged), self.repo.dest, "ebusgo"),
            "destination-commit",
        )
        deletion = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(self.repo.manifest_path("receipt-move"))],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        self.assert_fail(self.repo.deletion(deletion), "missing-receipt: closure/closed/moved.go")
        self.assertFalse((self.repo.root / "acceptance" / "manifests" / "GG13.lst").exists())
        bad = json.loads(self.repo.manifest_path("receipt-move").read_text(encoding="utf-8"))
        bad["receipts"].append({
            "repository": "ebusgo",
            "kind": "whole-session",
            "donor_sha": self.repo.sha,
            "destination_commit": self.repo.integrated,
            "old_status": 0,
            "new_status": 1,
            "old_output": "same",
            "new_output": "same",
            "differences": [],
            "compared": [],
            "outcome": "equal",
        })
        bad_path = self.repo.root / "acceptance" / "manifests" / "receipt-bad.json"
        bad_path.write_text(json.dumps(bad), encoding="utf-8")
        gg08 = dict(deletion)
        gg08["row"] = "GG08"
        gg08["manifests"] = [str(bad_path)]
        self.assert_fail(self.repo.deletion(gg08), "missing-receipt: closure/closed/moved.go")
        self.assertFalse((self.repo.root / "acceptance" / "manifests" / "GG08.lst").exists())
        self.assert_ok(self.repo.receipt(
            "receipt-move",
            self.repo.result("ebusgo", "whole-session", self.repo.integrated),
            self.repo.dest,
            "ebusgo",
        ))
        self.assert_ok(self.repo.deletion(deletion))
        listed = (self.repo.root / "acceptance" / "manifests" / "GG13.lst").read_bytes()
        self.assertIn(b"closure/closed/moved.go\n", listed)
        self.assertNotIn(b"*", listed)
        recorded = json.loads((self.repo.root / "acceptance" / "manifests" / "GG13.json").read_text(encoding="utf-8"))
        self.assertEqual(recorded["sha256"], hashlib.sha256(listed).hexdigest())
        self.assertEqual(recorded["donor_sha"], self.repo.sha)
        wildcard = self.repo.base(
            "batch-wildcard",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[{
                "case": "north",
                "field": "northbound",
                "old_present": False,
                "old": "*",
                "new": "present",
                "source": "gg10-lead",
                "approval": "approved-transition",
                "repository": "docs-semantic",
                "revision": self.repo.sha,
                "path": "vec/diff-north.json",
            }],
        )
        self.assert_fail(self.repo.generate(wildcard), "wildcard-difference")
        self.assert_absent("batch-wildcard")
        missing_approval = self.repo.base(
            "batch-no-approval",
            expected_differences=[{
                "case": "north",
                "field": "northbound",
                "old_present": False,
                "new": "present",
                "repository": "docs-semantic",
                "revision": self.repo.sha,
                "path": "vec/diff-north.json",
            }],
        )
        self.assert_fail(self.repo.generate(missing_approval), "missing-approval")
        status_spec = self.repo.base(
            "status-move",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[self.repo.difference("vec/diff-status.json")],
        )
        self.assert_ok(self.repo.generate(status_spec))
        extra = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            differences=[
                {"case": "*", "field": "execution_status", "old_present": True, "old": "0", "new": "1"},
                {"case": "*", "field": "extra", "old_present": True, "old": "a", "new": "b"},
            ],
        )
        self.assert_fail(self.repo.receipt("status-move", extra, self.repo.dest, "ebusgo"), "unapproved-difference: extra")
        approved = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            differences=[{"case": "*", "field": "execution_status", "old_present": True, "old": "0", "new": "1"}],
        )
        self.assert_ok(self.repo.receipt("status-move", approved, self.repo.dest, "ebusgo"))
        self.assertEqual(self.repo.manifest("status-move")["receipts"][0]["outcome"], "approved-difference")
        self.assertEqual(self.repo.manifest("status-move")["receipts"][0]["old_status"], 0)
        self.assertEqual(self.repo.manifest("status-move")["receipts"][0]["new_status"], 1)

    def test_gg07_needs_the_standalone_classifier_receipt(self) -> None:
        classifier = self.repo.base(
            "gg07-classifier",
            moves=[self.repo.move("cmd/growatt-can-classify/main.go", "cmd/growatt-can-classify/main.go", "canbusreg")],
        )
        internal = self.repo.base(
            "gg07-internal",
            moves=[self.repo.move("internal/growattcanclassify/classify.go", "internal/growattcanclassify/classify.go", "canbusreg")],
        )
        self.assert_ok(self.repo.generate(classifier))
        self.assert_ok(self.repo.generate(internal))
        for row in ("gg07-classifier", "gg07-internal"):
            self.assert_ok(self.repo.receipt(row, self.repo.result("canbusreg", "row", self.repo.merged), self.repo.dest, "canbusreg"))
            self.assert_ok(self.repo.receipt(row, self.repo.result("canbusreg", "whole-session", self.repo.integrated), self.repo.dest, "canbusreg"))
        body = {
            "row": "GG07",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(self.repo.manifest_path("gg07-classifier")), str(self.repo.manifest_path("gg07-internal"))],
            "grants": [
                {"kind": "owned", "path": "cmd/gateway/drivers.go"},
                {"kind": "owned", "path": "cmd/gateway/managed_sidecar_composition.go"},
            ],
            "reserves": [],
            "live_inputs": [],
        }
        self.assert_fail(self.repo.deletion(body), "missing-receipt: standalone-classifier")
        self.assertFalse((self.repo.root / "acceptance" / "manifests" / "GG07.lst").exists())
        standalone = self.repo.result("canbusreg", "standalone-classifier", self.repo.integrated, compared=list(SURFACES))
        self.assert_ok(self.repo.receipt("gg07-classifier", standalone, self.repo.dest, "canbusreg"))
        self.assert_ok(self.repo.deletion(body))
        text = (self.repo.root / "acceptance" / "manifests" / "GG07.lst").read_text(encoding="utf-8")
        self.assertIn("cmd/gateway/drivers.go\n", text)
        self.assertIn("cmd/gateway/managed_sidecar_composition.go\n", text)
        self.assertIn("cmd/growatt-can-classify/main.go\n", text)
        self.assertIn("internal/growattcanclassify/classify.go\n", text)
        self.assertNotIn("cmd/gateway/capture.go", text)
        self.assertNotIn("*", text)
        self.assertEqual(text.splitlines(), sorted(text.splitlines()))

    def test_gg10_retirement_evidence(self) -> None:
        groups = {
            "gg10-gateway": [
                self.repo.move("cmd/gateway/capture.go", "engine/capture.go"),
                self.repo.move("cmd/gateway/lock.go", "engine/lock.go"),
                self.repo.move("cmd/gateway/stub.go", "engine/stub.go"),
                self.repo.move("cmd/gateway/leaf_promotion_live_source.go", "engine/leaf_promotion_live_source.go"),
            ],
            "gg10-relay": [self.repo.move("internal/eebusoutput/binding.go", "engine/binding.go")],
            "gg10-registry": [self.repo.move("internal/promotion/registry.go", "engine/registry.go")],
        }
        for row, moves in groups.items():
            self.assert_ok(self.repo.generate(self.repo.base(row, moves=moves)))
            self.assert_ok(self.repo.receipt(row, self.repo.result("ebusgo", "row", self.repo.merged), self.repo.dest, "ebusgo"))
            self.assert_ok(self.repo.receipt(row, self.repo.result("ebusgo", "whole-session", self.repo.integrated), self.repo.dest, "ebusgo"))
        evidence = {
            "r2_002": True,
            "r2_057": True,
            "qq08_offline_validator": {"revision": self.repo.sha, "result": "pass"},
            "pinned_offline_capture_comparison": {"revision": self.repo.sha, "result": "equal"},
            "caller_inventory": {"revision": self.repo.sha, "result": "inventoried"},
            "live_inputs": [{"id": "live-1", "disposition": "retire", "closure": "capture-only", "source_revision": self.repo.sha}],
            "relay": {"production_callers": "absent", "testm40_outcome": "pass", "revision": self.repo.sha},
            "shared_paths": [
                {"path": "cmd/gateway/leaf_promotion_live_source.go", "ordinary_receipts": True, "offline_retirement": True},
                {"path": "internal/promotion/registry.go", "ordinary_receipts": True, "offline_retirement": True},
            ],
        }
        body = {
            "row": "GG10",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(self.repo.manifest_path(row)) for row in groups],
            "grants": [],
            "reserves": [],
            "live_inputs": ["live-1", "live-2"],
            "retirement_evidence": evidence,
        }
        self.assert_fail(self.repo.deletion(body), "uncovered-live-input: live-2")
        self.assertFalse((self.repo.root / "acceptance" / "manifests" / "GG10.lst").exists())
        missing = json.loads(json.dumps(body))
        missing["live_inputs"] = ["live-1"]
        missing["retirement_evidence"]["r2_002"] = False
        self.assert_fail(self.repo.deletion(missing), "missing-retirement-evidence")
        self.assertFalse((self.repo.root / "acceptance" / "manifests" / "GG10.lst").exists())
        uncovered = json.loads(json.dumps(body))
        uncovered["live_inputs"] = ["live-1"]
        uncovered["retirement_evidence"]["shared_paths"] = []
        self.assert_fail(self.repo.deletion(uncovered), "missing-retirement-evidence: cmd/gateway/leaf_promotion_live_source.go")
        sealed = json.loads(json.dumps(body))
        sealed["live_inputs"] = ["live-1"]
        self.assert_ok(self.repo.deletion(sealed))
        text = (self.repo.root / "acceptance" / "manifests" / "GG10.lst").read_text(encoding="utf-8")
        for path in (
            "cmd/gateway/capture.go",
            "cmd/gateway/lock.go",
            "cmd/gateway/stub.go",
            "cmd/gateway/leaf_promotion_live_source.go",
            "internal/eebusoutput/binding.go",
            "internal/promotion/registry.go",
        ):
            self.assertIn(path + "\n", text)
        self.assertEqual(text.splitlines(), sorted(set(text.splitlines())))

    def test_gg11_reserves_five_fixture_paths(self) -> None:
        reserves = [f"{GG11_DIR}/feed-{name}.json" for name in ("a", "b", "c", "d", "e")]
        body = {
            "row": "GG11",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [],
            "grants": [
                {"kind": "owned", "path": "matter/"},
                {"kind": "owned", "path": "cmd/gateway/matter_*.go"},
                {"kind": "shared", "path": GG11_DIR},
            ],
            "reserves": reserves[:4],
            "live_inputs": [],
        }
        self.assert_fail(self.repo.deletion(body), "gg11-fixtures")
        self.assertFalse((self.repo.root / "acceptance" / "manifests" / "GG11.lst").exists())
        body["reserves"] = reserves
        self.assert_ok(self.repo.deletion(body))
        text = (self.repo.root / "acceptance" / "manifests" / "GG11.lst").read_text(encoding="utf-8")
        for path in reserves:
            self.assertIn(path + "\n", text)
        self.assertIn("matter/composer.go\n", text)
        self.assertIn("cmd/gateway/matter_feed.go\n", text)
        self.assertIn("cmd/gateway/matter_old.go\n", text)
        self.assertNotIn("*", text)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(text.splitlines(), sorted(text.splitlines()))

    def test_ledger_absent(self) -> None:
        empty = self.repo.root.parent / "empty-gateway"
        empty.mkdir()
        (empty / "README").write_text("synthetic\n", encoding="utf-8")
        git(empty, "init", "-b", "main")
        git(empty, "add", "-A")
        git(empty, "commit", "-m", "empty")
        sha = git_out(empty, "rev-parse", "HEAD")
        completed = self.repo.deletion({
            "row": "GG13",
            "donor_sha": sha,
            "ledger_commit": sha,
            "manifests": [],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }, gateway=empty)
        self.assert_fail(completed, "ledger-absent: tools/boundary")

    def test_stale_exemplar_path_does_not_borrow_another_path(self) -> None:
        side = self.repo.root.parent / "exemplar-side"
        side.mkdir()
        git(side, "init", "-b", "main")
        original = (TESTDATA / "exemplar" / "measurement_rows.go").read_text(encoding="utf-8")
        good = side / "driver" / "examples" / "peer" / "measurement_rows.go"
        good.parent.mkdir(parents=True)
        good.write_text(original, encoding="utf-8")
        git(side, "add", "-A")
        git(side, "commit", "-m", "good")
        git(side, "branch", "good")
        good.write_text(original.replace('"inverse":"none"', '"inverse":"stale"'), encoding="utf-8")
        other = side / "driver" / "examples" / "peer" / "other_rows.go"
        other.write_text(original, encoding="utf-8")
        git(side, "add", "-A")
        git(side, "commit", "-m", "stale")
        git(side, "branch", "stale")
        good_sha = git_out(side, "rev-parse", "refs/heads/good")
        stale_sha = git_out(side, "rev-parse", "refs/heads/stale")
        git(self.repo.root, "fetch", str(side), "refs/heads/good:refs/exemplar/good", "refs/heads/stale:refs/exemplar/stale")
        self.assertEqual(git_out(self.repo.root, "rev-parse", "HEAD"), self.repo.sha)
        meas_sig = self.repo.sig["measurement_rows.go"]
        spec = self.repo.base(
            "batch-stale",
            mapping_rows=[self.repo.pattern(
                "meas-row", "specification", ["in-case"], "in-assert", meas_sig,
                "driver/examples/peer/measurement_rows.go", fill(meas_sig, MEAS), revision=good_sha,
            )],
            expectations=[self.repo.expectation(
                "in-case", "specification",
                [self.repo.bound("meas-row", "in-assert", "TestEcho")],
                selector_map(meas_sig, MEAS),
                [self.repo.ref("specification", "vec/meas.json")],
            )],
        )
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.check("batch-stale"))
        edited = self.repo.root / "acceptance" / "manifests" / "stale-edited.json"
        shutil.copy(self.repo.manifest_path("batch-stale"), edited)
        body = json.loads(edited.read_text(encoding="utf-8"))
        body["patterns"][0]["exemplar"]["revision"] = stale_sha
        edited.write_text(json.dumps(body), encoding="utf-8")
        other_blob = git_out(self.repo.root, "show", f"{stale_sha}:driver/examples/peer/other_rows.go")
        self.assertIn('"inverse":"none"', other_blob)
        self.assert_fail(self.repo.check("batch-stale", manifest=edited), "signature-mismatch row: meas-row")
        bare = self.repo.root.parent / "donor-bare"
        git(self.repo.root.parent, "clone", "--depth", "1", "--no-local", str(self.repo.root), str(bare))
        probe = git(bare, "cat-file", "-e", f"{good_sha}^{{commit}}", check=False)
        self.assertNotEqual(probe.returncode, 0, probe.stderr)
        listed = bare / "acceptance" / "manifests"
        listed.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.repo.manifest_path("batch-stale"), listed / "batch-stale.json")
        for path in (self.repo.root / "acceptance" / "manifests").glob("batch-stale.*"):
            if path.suffix == ".json":
                continue
            shutil.copy(path, listed / path.name)
        completed = subprocess.run(
            [sys.executable, str(bare / "acceptance" / "tools" / "manifest" / "main.py"), "check", "--manifest", str(bare / "acceptance" / "manifests" / "batch-stale.json"), "--donor", str(bare)],
            env=tool_env(),
            text=True,
            capture_output=True,
        )
        self.assert_fail(completed, "unavailable:", "driver/examples/peer/measurement_rows.go")

    def test_shallow_reference_exemplar_and_candidate(self) -> None:
        parent = git_out(ROOT, "rev-parse", "HEAD~1")
        blob = git(ROOT, "cat-file", "-e", f"{parent}:acceptance/oracle/references.json", check=False)
        self.assertEqual(blob.returncode, 0, "pinned oracle file is not in the parent commit")
        shallow = self.repo.root.parent / "shallow-tool"
        git(self.repo.root.parent, "clone", "--depth", "1", "--no-local", str(ROOT), str(shallow))
        copy_tool(shallow)
        absent = git(shallow, "cat-file", "-e", f"{parent}^{{commit}}", check=False)
        self.assertNotEqual(absent.returncode, 0)
        head = git_out(shallow, "rev-parse", "HEAD")
        spec = {
            "row": "shallow-ref",
            "donor_repository": "docs-semantic",
            "donor_sha": head,
            "moves": [],
            "new_files": [],
            "shared": [],
            "specimens": [],
            "assertions": [],
            "mapping_rows": [],
            "expectations": [{
                "case": "oracle-case",
                "kind": "specification",
                "rows": [],
                "selectors": {},
                "inputs": INPUTS,
                "references": [{
                    "role": "specification",
                    "repository": "docs-semantic",
                    "revision": parent,
                    "path": "acceptance/oracle/references.json",
                }],
            }],
            "expected_differences": [],
        }
        main = shallow / "acceptance" / "tools" / "manifest" / "main.py"
        spec_path = shallow / "specs" / "shallow-ref.json"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        missing = subprocess.run(
            [sys.executable, str(main), "generate", "--input", str(spec_path), "--donor", str(shallow)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_fail(missing, "unavailable:")
        self.assertFalse((shallow / "acceptance" / "manifests" / "shallow-ref.json").exists())
        git(shallow, "fetch", "--deepen", "1")
        present = git(shallow, "cat-file", "-e", f"{parent}^{{commit}}", check=False)
        self.assertEqual(present.returncode, 0, present.stderr)
        generated = subprocess.run(
            [sys.executable, str(main), "generate", "--input", str(spec_path), "--donor", str(shallow)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_ok(generated)
        checked = subprocess.run(
            [sys.executable, str(main), "check", "--manifest", str(shallow / "acceptance" / "manifests" / "shallow-ref.json"), "--donor", str(shallow)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_ok(checked)
        compared = subprocess.run(
            [sys.executable, str(main), "compare", "--manifest", str(shallow / "acceptance" / "manifests" / "shallow-ref.json"), "--destination", str(self.repo.dest)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_ok(compared)
        withheld = self.repo.root.parent / "shallow-withheld"
        git(self.repo.root.parent, "clone", "--depth", "1", "--no-local", str(ROOT), str(withheld))
        copy_tool(withheld)
        for path in (shallow / "acceptance" / "manifests").glob("shallow-ref.*"):
            shutil.copy(path, withheld / "acceptance" / "manifests" / path.name)
        withheld_main = withheld / "acceptance" / "tools" / "manifest" / "main.py"
        for command in ("check", "compare"):
            args = [sys.executable, str(withheld_main), command, "--manifest", str(withheld / "acceptance" / "manifests" / "shallow-ref.json")]
            if command == "check":
                args.extend(["--donor", str(withheld)])
            else:
                args.extend(["--destination", str(self.repo.dest)])
            completed = subprocess.run(args, env=tool_env(), text=True, capture_output=True)
            self.assert_fail(completed, "unavailable:")
            self.assertNotIn("check: ok", completed.stdout)
            self.assertNotIn("compare: ok", completed.stdout)
        opev_sig = self.repo.sig["opev_rows.go"]
        side = self.repo.root.parent / "candidate-side"
        side.mkdir()
        git(side, "init", "-b", "main")
        candidate = {
            "rows": {
                "phase-row": {
                    "signature": opev_sig,
                    "operands": fill(opev_sig, OPEV, OPEV_EXTRA),
                }
            }
        }
        (side / "candidate.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        exemplar_copy = side / EXEMPLARS["opev_rows.go"]
        exemplar_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(TESTDATA / "exemplar" / "opev_rows.go", exemplar_copy)
        git(side, "add", "-A")
        git(side, "commit", "-m", "phase-a")
        git(side, "branch", "good")
        bad_ops = fill(opev_sig, OPEV, OPEV_EXTRA)
        bad_ops["phase"] = "b"
        candidate["rows"]["phase-row"]["operands"] = bad_ops
        (side / "candidate.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        git(side, "add", "-A")
        git(side, "commit", "-m", "phase-b")
        git(side, "branch", "phaseb")
        good_sha = git_out(side, "rev-parse", "refs/heads/good")
        bad_sha = git_out(side, "rev-parse", "refs/heads/phaseb")
        self.assertNotEqual(good_sha, head)
        git(shallow, "fetch", str(side), "refs/heads/good:refs/candidate/good", "refs/heads/phaseb:refs/candidate/phaseb")
        git(self.repo.root, "fetch", str(side), "refs/heads/good:refs/exemplar/opev-good")
        self.assertEqual(git_out(self.repo.root, "rev-parse", "HEAD"), self.repo.sha)
        self.assertEqual(git_out(shallow, "rev-parse", "HEAD"), head)
        exemplar_side = self.repo.root.parent / "exemplar-remote"
        git(self.repo.root.parent, "clone", "--depth", "1", "--no-local", str(self.repo.root), str(exemplar_side))
        git(self.repo.root, "fetch", str(exemplar_side), "refs/heads/main:refs/remote/exemplar")
        pattern_spec = {
            "row": "batch-candidate",
            "donor_repository": "gateway",
            "donor_sha": self.repo.sha,
            "moves": [],
            "new_files": [],
            "shared": [],
            "specimens": [],
            "assertions": [],
            "mapping_rows": [{
                "row": "opev-cmd",
                "kind": "specification",
                "cases": ["opev-case"],
                "assertion": "opev-assert",
                "old_symbol": "",
                "bom_entry": "",
                "signature": opev_sig,
                "exemplar": {
                    "repository": "eebusreg",
                    "path": EXEMPLARS["opev_rows.go"],
                    "revision": good_sha,
                },
                "candidate": {
                    "form": "reference",
                    "repository": "eebusreg",
                    "revision": good_sha,
                    "path": "candidate.json",
                    "row_key": "phase-row",
                },
            }],
            "expectations": [{
                "case": "opev-case",
                "kind": "specification",
                "rows": [{"row": "opev-cmd", "assertion": "opev-assert", "destination": {"repository": "ebusgo", "path": "dest/echo_test.go", "test": "TestEcho"}}],
                "selectors": selector_map(opev_sig, OPEV),
                "inputs": INPUTS,
                "references": [{
                    "role": "specification",
                    "repository": "docs-semantic",
                    "revision": head,
                    "path": "acceptance/oracle/references.json",
                }],
            }],
            "expected_differences": [],
        }
        pattern_path = shallow / "specs" / "batch-candidate.json"
        pattern_path.write_text(json.dumps(pattern_spec), encoding="utf-8")
        made = subprocess.run(
            [sys.executable, str(main), "generate", "--input", str(pattern_path), "--donor", str(self.repo.root)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_ok(made)
        checked = subprocess.run(
            [sys.executable, str(main), "check", "--manifest", str(shallow / "acceptance" / "manifests" / "batch-candidate.json"), "--donor", str(self.repo.root)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_ok(checked)
        donor_bare = self.repo.root.parent / "donor-no-exemplar"
        git(self.repo.root.parent, "clone", "--depth", "1", "--no-local", str(exemplar_side), str(donor_bare))
        no_exemplar = subprocess.run(
            [sys.executable, str(main), "check", "--manifest", str(shallow / "acceptance" / "manifests" / "batch-candidate.json"), "--donor", str(donor_bare)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_fail(no_exemplar, "unavailable:", EXEMPLARS["opev_rows.go"])
        mismatched = shallow / "acceptance" / "manifests" / "candidate-mismatch.json"
        shutil.copy(shallow / "acceptance" / "manifests" / "batch-candidate.json", mismatched)
        mismatch_body = json.loads(mismatched.read_text(encoding="utf-8"))
        mismatch_body["patterns"][0]["signature"] = {"family": "spine", "inverse": "other-pattern", "selector_fields": ["phase"]}
        mismatched.write_text(json.dumps(mismatch_body), encoding="utf-8")
        mismatch_run = subprocess.run(
            [sys.executable, str(main), "check", "--manifest", str(mismatched), "--donor", str(self.repo.root)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_fail(mismatch_run, "signature-mismatch row: opev-cmd")
        only_oracle = self.repo.root.parent / "shallow-no-candidate"
        git(self.repo.root.parent, "clone", "--depth", "1", "--no-local", str(ROOT), str(only_oracle))
        copy_tool(only_oracle)
        for path in (shallow / "acceptance" / "manifests").glob("batch-candidate.*"):
            shutil.copy(path, only_oracle / "acceptance" / "manifests" / path.name)
        only_main = only_oracle / "acceptance" / "tools" / "manifest" / "main.py"
        withheld_candidate = subprocess.run(
            [sys.executable, str(only_main), "check", "--manifest", str(only_oracle / "acceptance" / "manifests" / "batch-candidate.json"), "--donor", str(self.repo.root)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_fail(withheld_candidate, "candidate-reference: eebusreg candidate.json phase-row")
        bad_blob = subprocess.check_output(["git", "-C", str(side), "show", f"{bad_sha}:candidate.json"])
        wrong_phase = json.loads((shallow / "acceptance" / "manifests" / "batch-candidate.json").read_text(encoding="utf-8"))
        wrong_phase["patterns"][0]["candidate"]["revision"] = bad_sha
        wrong_phase["patterns"][0]["candidate"]["operands"] = bad_ops
        reference = wrong_phase["patterns"][0]["candidate"]["reference"]
        reference["revision"] = bad_sha
        reference["blob_sha256"] = hashlib.sha256(bad_blob).hexdigest()
        reference["projection"] = json.loads(bad_blob.decode())
        phase_path = shallow / "acceptance" / "manifests" / "candidate-phase.json"
        phase_path.write_text(json.dumps(wrong_phase), encoding="utf-8")
        phase_run = subprocess.run(
            [sys.executable, str(main), "check", "--manifest", str(phase_path), "--donor", str(self.repo.root)],
            env=tool_env(), text=True, capture_output=True,
        )
        self.assert_fail(phase_run, "selector-mismatch row: opev-cmd", "field: phase")


if __name__ == "__main__":
    unittest.main()
