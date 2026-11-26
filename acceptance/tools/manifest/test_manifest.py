"""CLI tests for the sealed-manifest tool.

Fixtures are synthetic. Revisions and digests are computed at runtime.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch


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
    shutil.copytree(TOOL / "gotypes", target / "gotypes", dirs_exist_ok=True)
    (root / "acceptance" / "manifests").mkdir(parents=True, exist_ok=True)
    return target / "main.py"


def product_strays() -> list[Path]:
    if not PRODUCT_MANIFESTS.is_dir():
        return []
    tracked = git(ROOT, "ls-files", "-z", "--", "acceptance/manifests").stdout.split("\0")
    expected = {Path(path).name for path in tracked if path}
    return sorted(path for path in PRODUCT_MANIFESTS.iterdir() if path.name not in expected)


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
        self.write("go.mod", "module example.test\n")
        self.write("root.go", "package root\n\nfunc RootHelper() int { return 1 }\n\nfunc RootOther() int { return 2 }\n")
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
        self.write_json("vec/diff-north-any.json", {
            "approval": "approved-transition",
            "case": "*",
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
        self.write_json("vec/diff-status-case-a.json", {
            "approval": "approved-status",
            "case": "case-A",
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

    def symbol(
        self,
        package: str,
        path: str,
        symbol: str,
        dest: str,
        renamed: str | None = None,
        repository: str = "ebusgo",
    ) -> dict:
        item = {
            "package": package,
            "path": path,
            "symbol": symbol,
            "destination_repository": repository,
            "destination_path": dest,
        }
        if renamed:
            item["destination_symbol"] = renamed
        return item

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


class PublishedManifestDirectoryTest(unittest.TestCase):
    def test_published_manifests_are_expected_but_strays_are_not(self) -> None:
        published = sorted(PRODUCT_MANIFESTS.glob("EE01.*"))
        self.assertEqual({path.suffix for path in published}, {".json", ".lst"})
        self.assertEqual(product_strays(), [])
        parent = Path(tempfile.mkdtemp(prefix="product-guard-", dir=ROOT / ".tmp"))
        for path in published:
            shutil.copy(path, parent / path.name)
        unexpected = parent / "unexpected.json"
        unexpected.write_text("{}\n", encoding="utf-8")
        with patch(__name__ + ".PRODUCT_MANIFESTS", parent):
            self.assertEqual(product_strays(), [unexpected])
            with self.assertRaises(AssertionError):
                ManifestCLITest().tearDown()
        self.assertTrue(unexpected.is_file())
        for path in published:
            self.assertEqual((parent / path.name).read_bytes(), path.read_bytes())


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
        self.assertEqual(strays, [], msg="unexpected files in the product manifest directory")

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

    def test_compares_a_retained_test_and_a_moved_test_under_its_new_name(self) -> None:
        row = "whole-test-comparison"
        package = "closure/mixed"
        donor_file = f"{package}/host_test.go"
        retained = {
            "name": "TestHostComposition", "file": donor_file,
            "repository": "ebusgo", "path": "dest/retained_test.go", "test": "TestRetained",
        }
        moved = {
            "name": "TestOnlyMoved", "file": "closure/left/left_test.go",
            "repository": "ebusgo", "path": "dest/transferred_test.go", "test": "TestRenamed",
        }
        spec = self.repo.base(row, symbol_moves=[
            self.repo.symbol(package, f"{package}/moved.go", "Moved", "engine/moved.go"),
            self.repo.symbol("closure/left", "closure/left/moved.go", "Moved", "engine/left.go"),
            self.repo.symbol("closure/left", moved["file"], moved["name"], moved["path"], renamed=moved["test"]),
        ], new_files=[
            {"repository": retained["repository"], "path": retained["path"]},
            {"repository": "other-repository", "path": moved["path"]},
        ], test_comparisons=[retained, moved])
        self.assert_ok(self.repo.generate(spec))
        manifest = self.repo.manifest(row)
        self.assertIn({"kind": "test", "name": retained["name"], "file": donor_file,
                       "function": retained["name"]}, manifest["stays"])
        self.assertEqual([entry for entry in manifest["destinations"] if entry["kind"] == "test"],
                         [{"kind": "test", **entry} for entry in (retained, moved)])
        self.assert_ok(self.repo.check(row))

        dest = self.repo.private_dest()
        passing = 'package dest\nimport "testing"\nfunc %s(t *testing.T) {}\n'
        for entry in (retained, moved):
            plant(dest, Path(entry["path"]).name, passing % entry["test"])
        compared = self.repo.compare(row, dest)
        self.assert_ok(compared)
        for entry in (retained, moved):
            self.assertIn(f"test={entry['test']} invocation-status=0 result=pass", compared.stdout)

        plant(dest, "retained_test.go", passing.replace("{}", '{ t.Fatal("regression") }') % retained["test"])
        failed = self.repo.compare(row, dest)
        self.assert_fail(failed, "test=TestRetained invocation-status=1 result=fail",
                         "test=TestRenamed invocation-status=0 result=pass")
        plant(dest, "retained_test.go", passing.replace("{}", '{ t.Skip("not exercised") }') % retained["test"])
        self.assert_fail(self.repo.compare(row, dest), "not-executed", "test=TestRetained")
        # A same-named test elsewhere in the same package cannot stand in for the bound file.
        plant(dest, "retained_test.go", passing % "TestOther")
        plant(dest, "other_test.go", passing % retained["test"])
        self.assert_fail(self.repo.compare(row, dest), "not-executed", "test=TestRetained")
        plant(dest, "retained_test.go", "//go:build ignore\n\n" + passing % retained["test"])
        self.assert_fail(self.repo.compare(row, dest), "not-executed", "test=TestRetained")

        for field, (value, problem) in {
            "file": (donor_file, "unaccounted"),
            "name": ("TestUnbound", "unaccounted"),
            "repository": ("other-repository", "mismatched"),
            "path": (retained["path"], "mismatched"),
            "test": ("TestOther", "mismatched"),
        }.items():
            with self.subTest(field=field):
                changed = self.repo.manifest(row)
                entry = next(item for item in changed["destinations"] if item.get("test") == moved["test"])
                entry[field] = value
                changed_path = self.repo.manifest_path(row).with_name("changed-comparison.json")
                changed_path.write_text(json.dumps(changed), encoding="utf-8")
                self.assert_fail(self.repo.check(row, manifest=changed_path), f"{problem}-test-comparison")
                self.assert_fail(self.repo.compare(row, dest, manifest=changed_path), f"{problem}-test-comparison")

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

    def test_compare_runs_split_assertions_without_mapping_rows(self) -> None:
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
            "split-compare",
            moves=[self.repo.move("closure/split/moved.go", "engine/split.go")],
            assertions=assertions,
        )
        self.assert_ok(self.repo.generate(spec))
        manifest = self.repo.manifest("split-compare")
        self.assertEqual(manifest["patterns"], [])
        self.assertEqual(
            sorted(item["name"] for item in manifest["assertions"]),
            ["observed-symbol", "transaction-event"],
        )
        compared = self.repo.compare("split-compare", self.repo.dest)
        self.assert_ok(compared)
        outcomes = [line for line in compared.stdout.splitlines() if line.startswith("outcome ")]
        self.assertEqual(len(outcomes), 2, detail(compared))
        for name in ("transaction-event", "observed-symbol"):
            self.assertTrue(
                any(
                    f"assertion={name}" in line and "test=TestEcho" in line and line.endswith("result=pass")
                    for line in outcomes
                ),
                detail(compared),
            )
        self.assertIn("compare: ok", compared.stdout)
        failed_dest = self.repo.private_dest()
        plant(failed_dest, "fail-assertion", "observed-symbol\n")
        failed = self.repo.compare("split-compare", failed_dest)
        self.assert_fail(failed, "assertion=observed-symbol", "test=TestEcho", "result=fail")
        self.assertNotIn("compare: ok", failed.stdout)
        self.assertTrue(
            any(
                "assertion=transaction-event" in line and "test=TestEcho" in line and line.endswith("result=pass")
                for line in failed.stdout.splitlines()
            ),
            detail(failed),
        )
        absent = self.repo.private_dest()
        echo = absent / "dest" / "echo_test.go"
        echo.write_text(
            echo.read_text(encoding="utf-8").replace(
                "func TestEcho(t *testing.T)    { report(t, false) }\n",
                "",
                1,
            ),
            encoding="utf-8",
        )
        missing = self.repo.compare("split-compare", absent)
        self.assert_fail(
            missing,
            "not-executed move=split-compare",
            "not-executed assertion=transaction-event",
            "not-executed assertion=observed-symbol",
        )
        self.assertNotIn("compare: ok", missing.stdout)

    ALPHA = "closure/symbols/alpha"
    BETA = "closure/symbols/beta"

    def alpha_moves(self) -> list[dict]:
        core = f"{self.ALPHA}/core.go"
        return [
            self.repo.symbol(self.ALPHA, core, "Record", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "Store", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "Store.Put", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "Store.Get", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "cloneRecord", "engine/records.go", renamed="CloneRecord"),
        ]

    def beta_moves(self) -> list[dict]:
        record = f"{self.BETA}/record.go"
        return [
            self.repo.symbol(self.BETA, record, "Record", "engine/mcp.go", renamed="MCPRecord"),
            self.repo.symbol(self.BETA, record, "NewRecord", "engine/mcp.go", renamed="NewMCPRecord"),
            self.repo.symbol(self.BETA, record, "Record.Label", "engine/mcp.go"),
        ]

    def symbol_spec(self, row: str, moves: list[dict], **kwargs: object) -> dict:
        return self.repo.base(row, symbol_moves=moves, **kwargs)

    def clone_assertions(self) -> list[dict]:
        return [{
            "function": "TestStoreBehaviour",
            "name": "clone-name",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]

    def test_symbol_moves_span_two_donor_packages(self) -> None:
        moves = self.alpha_moves() + self.beta_moves()
        spec = self.symbol_spec("symbols-two-packages", moves, assertions=self.clone_assertions())
        first = self.repo.generate(spec)
        second = self.repo.generate(spec)
        self.assert_ok(first)
        self.assertEqual(first.stdout, second.stdout)
        manifest = self.repo.manifest("symbols-two-packages")
        self.assertEqual(list(manifest), list(KEYS))
        self.assertEqual(
            [(item["package"], item["file"], item["name"]) for item in manifest["symbols"]],
            [
                (self.ALPHA, f"{self.ALPHA}/core.go", "Record"),
                (self.ALPHA, f"{self.ALPHA}/core.go", "Store"),
                (self.ALPHA, f"{self.ALPHA}/core.go", "Store.Get"),
                (self.ALPHA, f"{self.ALPHA}/core.go", "Store.Put"),
                (self.ALPHA, f"{self.ALPHA}/core.go", "cloneRecord"),
                (self.BETA, f"{self.BETA}/record.go", "NewRecord"),
                (self.BETA, f"{self.BETA}/record.go", "Record"),
                (self.BETA, f"{self.BETA}/record.go", "Record.Label"),
            ],
        )
        donor = next(item for item in manifest["paths"] if item["repository"] == "gateway")
        dest = next(item for item in manifest["paths"] if item["repository"] == "ebusgo")
        self.assertEqual(donor["paths"], [f"{self.ALPHA}/core.go", f"{self.BETA}/record.go"])
        self.assertEqual(dest["paths"], ["engine/mcp.go", "engine/records.go"])
        self.assertEqual([item["kind"] for item in manifest["stays"]], ["assertion"])
        self.assert_ok(self.repo.check("symbols-two-packages"))
        self.assert_ok(self.repo.compare("symbols-two-packages", self.repo.dest))

    def test_declared_names_only_are_counted(self) -> None:
        spec = self.symbol_spec("symbols-names", self.alpha_moves(), assertions=self.clone_assertions())
        completed = self.repo.generate(spec)
        self.assert_ok(completed)
        self.assertNotIn("outside-set", completed.stdout)
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("symbols-names")["symbols"]}
        self.assertEqual(
            uses,
            {
                "Record": [],
                "Store": ["Record"],
                "Store.Get": ["Record", "Store"],
                "Store.Put": ["Record", "Store", "cloneRecord"],
                "cloneRecord": ["Record"],
            },
        )
        whole = self.repo.base(
            "symbols-whole-file",
            moves=[self.repo.move(f"{self.ALPHA}/core.go", "engine/core.go")],
        )
        self.assert_fail(self.repo.generate(whole), "outside-set: ")
        self.assert_absent("symbols-whole-file")

    def test_a_sibling_that_stays_must_be_declared(self) -> None:
        core = f"{self.ALPHA}/core.go"
        moves = [
            self.repo.symbol(self.ALPHA, core, "Record", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "describe", "engine/records.go"),
        ]
        undeclared = self.repo.generate(self.symbol_spec("symbols-undeclared", moves))
        self.assert_fail(undeclared)
        self.assertEqual(undeclared.stdout, "outside-set: kept\n")
        self.assert_absent("symbols-undeclared")
        stays = [{"package": self.ALPHA, "path": f"{self.ALPHA}/stay.go", "symbol": "kept"}]
        declared = self.repo.generate(self.symbol_spec("symbols-declared", moves, stay_symbols=stays))
        self.assert_ok(declared)
        manifest = self.repo.manifest("symbols-declared")
        self.assertEqual(
            [item for item in manifest["stays"] if item["kind"] == "symbol"],
            [{"kind": "symbol", "name": "kept", "file": f"{self.ALPHA}/stay.go", "package": self.ALPHA}],
        )
        self.assertEqual(
            {item["name"]: item["uses"] for item in manifest["symbols"]},
            {"Record": [], "describe": ["Record"]},
        )
        self.assert_ok(self.repo.check("symbols-declared"))
        stripped = json.loads(self.repo.manifest_path("symbols-declared").read_text(encoding="utf-8"))
        stripped["stays"] = []
        path = self.repo.root / "acceptance" / "manifests" / "symbols-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("symbols-declared", manifest=path), "outside-set: kept")

    def test_methods_of_a_moved_type_are_siblings(self) -> None:
        core = f"{self.ALPHA}/core.go"
        moves = [
            self.repo.symbol(self.ALPHA, core, "Record", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "Store", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "Store.Put", "engine/records.go"),
            self.repo.symbol(self.ALPHA, core, "cloneRecord", "engine/records.go"),
        ]
        self.assertEqual(
            self.repo.generate(self.symbol_spec("symbols-methods", moves, assertions=self.clone_assertions())).stdout,
            "outside-set: Store.Get\n",
        )
        stays = [{"package": self.ALPHA, "path": core, "symbol": "Store.Get"}]
        self.assert_ok(self.repo.generate(self.symbol_spec("symbols-methods", moves, stay_symbols=stays, assertions=self.clone_assertions())))
        self.assert_ok(self.repo.check("symbols-methods"))

    def test_renamed_symbol_is_recorded_with_both_names(self) -> None:
        moves = self.alpha_moves() + self.beta_moves()
        self.assert_ok(self.repo.generate(self.symbol_spec("symbols-renames", moves, assertions=self.clone_assertions())))
        destinations = {
            (item["package"], item["name"]): item
            for item in self.repo.manifest("symbols-renames")["destinations"]
            if item["kind"] == "symbol"
        }
        self.assertEqual(destinations[(self.ALPHA, "cloneRecord")]["destination_name"], "CloneRecord")
        self.assertEqual(destinations[(self.BETA, "Record")]["destination_name"], "MCPRecord")
        self.assertEqual(destinations[(self.ALPHA, "Record")]["destination_name"], "Record")
        self.assertEqual(destinations[(self.BETA, "Record")]["path"], "engine/mcp.go")
        self.assertEqual(destinations[(self.ALPHA, "Record")]["path"], "engine/records.go")
        self.assertEqual(destinations[(self.BETA, "Record")]["repository"], "ebusgo")
        broken = json.loads(self.repo.manifest_path("symbols-renames").read_text(encoding="utf-8"))
        broken["destinations"] = [
            item for item in broken["destinations"]
            if not (item["kind"] == "symbol" and item["name"] == "cloneRecord")
        ]
        path = self.repo.root / "acceptance" / "manifests" / "symbols-renames-broken.json"
        path.write_text(json.dumps(broken), encoding="utf-8")
        self.assert_fail(
            self.repo.check("symbols-renames", manifest=path),
            f"missing-destination symbol={self.ALPHA}:cloneRecord",
        )

    def test_symbol_move_input_is_checked_against_the_donor(self) -> None:
        core = f"{self.ALPHA}/core.go"
        missing = [self.repo.symbol(self.ALPHA, core, "nothing", "engine/x.go")]
        self.assert_fail(
            self.repo.generate(self.symbol_spec("symbols-missing", missing)),
            f"absent-symbol: {core} nothing",
        )
        elsewhere = [self.repo.symbol(self.BETA, core, "Record", "engine/x.go")]
        self.assert_fail(
            self.repo.generate(self.symbol_spec("symbols-elsewhere", elsewhere)),
            f"package-mismatch: {core}",
        )
        both = [self.repo.symbol(self.ALPHA, core, "Record", "engine/x.go")]
        stays = [{"package": self.ALPHA, "path": core, "symbol": "Record"}]
        self.assert_fail(
            self.repo.generate(self.symbol_spec("symbols-both", both, stay_symbols=stays)),
            f"moved-and-stays: {core} Record",
        )
        mixed = self.repo.base(
            "symbols-mixed",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            symbol_moves=both,
        )
        self.assert_fail(self.repo.generate(mixed), "moves-and-symbol-moves")
        for row in ("symbols-missing", "symbols-elsewhere", "symbols-both", "symbols-mixed"):
            self.assert_absent(row)

    def test_symbol_level_assertions_are_executed_by_compare(self) -> None:
        spec = self.symbol_spec("symbols-compare", self.alpha_moves(), assertions=self.clone_assertions())
        self.assert_ok(self.repo.generate(spec))
        manifest = self.repo.manifest("symbols-compare")
        self.assertEqual(
            [(item["function"], item["name"], item["helpers"]) for item in manifest["assertions"]],
            [("TestStoreBehaviour", "clone-name", ["cloneRecord"])],
        )
        self.assertEqual(
            [(item["kind"], item["function"], item["name"]) for item in manifest["stays"]],
            [("assertion", "TestStoreBehaviour", "kept-value")],
        )
        self.assert_ok(self.repo.check("symbols-compare"))
        compared = self.repo.compare("symbols-compare", self.repo.dest)
        self.assert_ok(compared)
        self.assertTrue(
            any(
                "assertion=clone-name" in line and "test=TestEcho" in line and line.endswith("result=pass")
                for line in compared.stdout.splitlines()
            ),
            detail(compared),
        )
        absent = self.repo.private_dest()
        echo = absent / "dest" / "echo_test.go"
        echo.write_text(
            echo.read_text(encoding="utf-8").replace(
                "func TestEcho(t *testing.T)    { report(t, false) }\n",
                "",
                1,
            ),
            encoding="utf-8",
        )
        missing = self.repo.compare("symbols-compare", absent)
        self.assert_fail(missing, "not-executed move=symbols-compare", "not-executed assertion=clone-name")
        self.assertNotIn("compare: ok", missing.stdout)
        unaccounted = self.symbol_spec("symbols-unaccounted", self.alpha_moves())
        self.assert_fail(
            self.repo.generate(unaccounted),
            "unaccounted-assertion function=TestStoreBehaviour assertion=clone-name",
        )
        self.assert_absent("symbols-unaccounted")

    PA = "closure/cross/pa"
    PB = "closure/cross/pb"
    SIG = "closure/cross/sig"
    LOC = "closure/cross/loc"
    DA = "closure/cross/da"
    DB = "closure/cross/db"

    def test_names_qualified_by_another_donor_package_are_closed(self) -> None:
        move = self.repo.symbol(self.PA, f"{self.PA}/a.go", "Move", "engine/cross.go")
        helper = self.repo.symbol(self.PB, f"{self.PB}/b.go", "Helper", "engine/cross.go")
        other = {"package": self.PB, "path": f"{self.PB}/b.go", "symbol": "Other"}
        undeclared = self.repo.generate(self.symbol_spec("cross-open", [move], stay_symbols=[other]))
        self.assert_fail(undeclared)
        self.assertEqual(undeclared.stdout, f"outside-set: {self.PB}.Helper\n")
        self.assert_absent("cross-open")
        self.assert_ok(self.repo.generate(self.symbol_spec("cross-moved", [move, helper])))
        self.assert_ok(self.repo.check("cross-moved"))
        staying = {"package": self.PB, "path": f"{self.PB}/b.go", "symbol": "Helper"}
        self.assert_ok(self.repo.generate(self.symbol_spec("cross-stays", [move], stay_symbols=[staying, other])))
        self.assert_ok(self.repo.check("cross-stays"))
        stripped = json.loads(self.repo.manifest_path("cross-stays").read_text(encoding="utf-8"))
        stripped["stays"] = [item for item in stripped["stays"] if item["name"] != "Helper"]
        path = self.repo.root / "acceptance" / "manifests" / "cross-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("cross-stays", manifest=path), f"outside-set: {self.PB}.Helper")

    def test_binding_names_are_not_uses_but_signature_types_are(self) -> None:
        sig = f"{self.SIG}/sig.go"
        move = self.repo.symbol(self.SIG, sig, "Move", "engine/sig.go")
        opened = self.repo.generate(self.symbol_spec("sig-open", [move]))
        self.assert_fail(opened)
        self.assertEqual(opened.stdout, "outside-set: T\n")
        self.assert_absent("sig-open")
        both = [move, self.repo.symbol(self.SIG, sig, "T", "engine/sig.go")]
        self.assert_ok(self.repo.generate(self.symbol_spec("sig-closed", both)))
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("sig-closed")["symbols"]}
        self.assertEqual(uses, {"Move": ["T"], "T": []})
        reader = [self.repo.symbol(self.SIG, sig, "Reader", "engine/sig.go")]
        completed = self.repo.generate(self.symbol_spec("sig-reader", reader))
        self.assert_ok(completed)
        self.assertNotIn("outside-set", completed.stdout)

    def test_a_local_name_does_not_keep_a_donor_assertion(self) -> None:
        move = self.repo.symbol(self.LOC, f"{self.LOC}/loc.go", "Move", "engine/loc.go")
        bare = self.repo.generate(self.symbol_spec("local-bare", [move]))
        self.assert_fail(bare, "unaccounted-assertion function=TestLocal assertion=local-name")
        self.assert_absent("local-bare")
        given = [{
            "function": "TestLocal",
            "name": "local-name",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]
        self.assert_ok(self.repo.generate(self.symbol_spec("local-given", [move], assertions=given)))
        manifest = self.repo.manifest("local-given")
        self.assertEqual(
            [(item["function"], item["name"], item["helpers"]) for item in manifest["assertions"]],
            [("TestLocal", "local-name", ["Move"])],
        )
        self.assertEqual(
            [(item["kind"], item["name"]) for item in manifest["stays"]],
            [("assertion", "stay-value")],
        )

    SCOPE = "closure/cross/scope"
    EXT = "closure/cross/ext"
    EX = "closure/cross/ex"

    def scope_move(self, symbol: str) -> dict:
        return self.repo.symbol(self.SCOPE, f"{self.SCOPE}/scope.go", symbol, "engine/scope.go")

    def test_a_binding_counts_only_where_it_is_in_scope(self) -> None:
        # The select case binds `pending` for its own clause only: the default
        # clause reads the package variable.
        selected = self.repo.generate(self.symbol_spec("scope-select", [self.scope_move("SelectMove")]))
        self.assert_fail(selected)
        self.assertEqual(selected.stdout, "outside-set: pending\n")
        self.assert_absent("scope-select")
        # An if initializer binds `value` in every else branch as well.
        branched = self.repo.generate(self.symbol_spec("scope-else", [self.scope_move("ElseMove")]))
        self.assert_ok(branched)
        self.assertNotIn("outside-set", branched.stdout)
        self.assert_ok(self.repo.check("scope-else"))

    def test_a_struct_alias_masks_its_literal_keys(self) -> None:
        moves = [self.scope_move(name) for name in ("AliasMove", "view", "base")]
        aliased = self.repo.generate(self.symbol_spec("scope-alias", moves))
        self.assert_ok(aliased)
        self.assertNotIn("outside-set", aliased.stdout)
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("scope-alias")["symbols"]}
        self.assertEqual(uses, {"AliasMove": ["view"], "base": [], "view": ["base"]})
        self.assert_ok(self.repo.check("scope-alias"))

    def test_the_last_symbol_of_a_donor_package_still_closes(self) -> None:
        move = self.repo.symbol(self.PA, f"{self.PA}/a.go", "Move", "engine/cross.go")
        helper = self.repo.symbol(self.PB, f"{self.PB}/b.go", "Helper", "engine/cross.go")
        alone = self.repo.generate(self.symbol_spec("last-alone", [move]))
        self.assert_fail(alone)
        self.assertEqual(alone.stdout, f"outside-set: {self.PB}.Helper\n")
        self.assert_absent("last-alone")
        self.assert_ok(self.repo.generate(self.symbol_spec("last-both", [move, helper])))
        self.assert_ok(self.repo.check("last-both"))
        stripped = json.loads(self.repo.manifest_path("last-both").read_text(encoding="utf-8"))
        stripped["symbols"] = [item for item in stripped["symbols"] if item["name"] != "Helper"]
        path = self.repo.root / "acceptance" / "manifests" / "last-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(
            self.repo.check("last-both", manifest=path), f"unmatched-destination symbol={self.PB}:Helper",
        )
        stripped["destinations"] = [
            item for item in stripped["destinations"] if item.get("name") != "Helper"
        ]
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("last-both", manifest=path), f"outside-set: {self.PB}.Helper")

    def test_a_donor_test_that_uses_a_moved_symbol_through_an_import_is_accounted(self) -> None:
        moves = [
            self.repo.symbol(self.EX, f"{self.EX}/ex.go", "Move", "engine/cross.go"),
        ]
        keep = [{"package": self.EXT, "path": f"{self.EXT}/ext.go", "symbol": "Keep"}]
        bare = self.repo.generate(self.symbol_spec("import-bare", moves, stay_symbols=keep))
        self.assert_fail(
            bare,
            "left-behind: TestViaImport",
            "unaccounted-assertion function=TestMixedImport assertion=mixed-moved",
        )
        self.assertNotIn("assertion=mixed-kept", bare.stdout)
        self.assert_absent("import-bare")
        given = [{
            "function": "TestMixedImport",
            "name": "mixed-moved",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]
        done = self.repo.generate(self.symbol_spec(
            "import-given", moves, stay_symbols=keep, assertions=given, specimens=["TestViaImport"],
        ))
        self.assert_ok(done)
        manifest = self.repo.manifest("import-given")
        self.assertEqual(
            [(item["function"], item["name"]) for item in manifest["assertions"]],
            [("TestMixedImport", "mixed-moved")],
        )
        self.assertIn(("specimen", "TestViaImport"), [(item["kind"], item["name"]) for item in manifest["stays"]])
        self.assert_ok(self.repo.check("import-given"))

    LANG = "closure/cross/lang"
    XT = "closure/cross/xt"
    FAR = "closure/cross/far"
    RT = "closure/cross/rt"

    def lang_move(self, symbol: str) -> dict:
        return self.repo.symbol(self.LANG, f"{self.LANG}/lang.go", symbol, "engine/lang.go")

    def lang_stay(self, symbol: str) -> dict:
        return {"package": self.LANG, "path": f"{self.LANG}/lang.go", "symbol": symbol}

    def test_an_array_bound_is_a_use_but_a_type_parameter_is_not(self) -> None:
        open_bound = self.repo.generate(self.symbol_spec("lang-array", [self.lang_move("Array")]))
        self.assert_fail(open_bound)
        self.assertEqual(open_bound.stdout, "outside-set: Bound\n")
        self.assert_absent("lang-array")
        closed = self.repo.generate(
            self.symbol_spec("lang-array-stays", [self.lang_move("Array")], stay_symbols=[self.lang_stay("Bound")])
        )
        self.assert_ok(closed)
        self.assert_ok(self.repo.check("lang-array-stays"))
        generic = self.repo.generate(self.symbol_spec("lang-generic", [self.lang_move("Generic")]))
        self.assert_ok(generic)
        self.assertNotIn("outside-set", generic.stdout)

    def test_a_range_binding_covers_the_loop_body(self) -> None:
        completed = self.repo.generate(self.symbol_spec("lang-range", [self.lang_move("Range")]))
        self.assert_ok(completed)
        self.assertNotIn("outside-set", completed.stdout)
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("lang-range")["symbols"]}
        self.assertEqual(uses, {"Range": []})
        self.assert_ok(self.repo.check("lang-range"))

    def test_a_qualified_dependency_is_recorded_with_its_package(self) -> None:
        move = self.repo.symbol(self.PA, f"{self.PA}/a.go", "Move", "engine/cross.go")
        helper = self.repo.symbol(self.PB, f"{self.PB}/b.go", "Helper", "engine/cross.go")
        self.assert_ok(self.repo.generate(self.symbol_spec("qual-both", [move, helper])))
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("qual-both")["symbols"]}
        self.assertEqual(uses, {"Move": [f"{self.PB}.Helper"], "Helper": []})
        self.assert_ok(self.repo.check("qual-both"))
        stripped = json.loads(self.repo.manifest_path("qual-both").read_text(encoding="utf-8"))
        for item in stripped["symbols"]:
            if item["name"] == "Move":
                item["uses"] = []
        path = self.repo.root / "acceptance" / "manifests" / "qual-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("qual-both", manifest=path), "symbol-set")

    def test_a_helper_in_the_module_root_must_be_accounted(self) -> None:
        move = self.repo.symbol(self.RT, f"{self.RT}/rt.go", "Move", "engine/rt.go")
        open_root = self.repo.generate(self.symbol_spec("root-open", [move]))
        self.assert_fail(open_root)
        self.assertEqual(open_root.stdout, "outside-set: ..RootHelper\n")
        self.assert_absent("root-open")
        staying = {"package": ".", "path": "root.go", "symbol": "RootHelper"}
        self.assert_ok(self.repo.generate(self.symbol_spec("root-stays", [move], stay_symbols=[staying])))
        self.assert_ok(self.repo.check("root-stays"))

    def test_a_call_of_a_donor_method_is_a_dependency_but_a_field_is_not(self) -> None:
        call = self.lang_move("Call")
        holder = self.lang_stay("Holder")
        open_method = self.repo.generate(self.symbol_spec("method-open", [call], stay_symbols=[holder]))
        self.assert_fail(open_method)
        self.assertEqual(open_method.stdout, "outside-set: Holder.Helper\n")
        self.assert_absent("method-open")
        declared = self.repo.generate(
            self.symbol_spec("method-stays", [call], stay_symbols=[holder, self.lang_stay("Holder.Helper")])
        )
        self.assert_ok(declared)
        self.assert_ok(self.repo.check("method-stays"))
        moved = self.repo.generate(
            self.symbol_spec("method-moved", [call, self.lang_move("Holder.Helper")], stay_symbols=[holder])
        )
        self.assert_ok(moved)
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("method-moved")["symbols"]}
        self.assertEqual(uses["Call"], ["Holder.Helper"])
        field = self.repo.generate(
            self.symbol_spec("method-field", [self.lang_move("Field")], stay_symbols=[self.lang_stay("Plain")])
        )
        self.assert_ok(field)
        self.assertNotIn("outside-set", field.stdout)

    FIX = "closure/cross/fix"
    KEYED = "closure/cross/keyed"
    METH = "closure/cross/meth"
    XO = "closure/cross/xo"

    def fix_move(self, symbol: str) -> dict:
        return self.repo.symbol(self.FIX, f"{self.FIX}/fix.go", symbol, "engine/fix.go")

    def fix_stay(self, symbol: str, package: str | None = None) -> dict:
        package = package or self.FIX
        file = "fix.go" if package == self.FIX else "keyed.go"
        return {"package": package, "path": f"{package}/{file}", "symbol": symbol}

    def test_a_donor_test_that_calls_a_moved_method_is_accounted(self) -> None:
        move = self.repo.symbol(self.METH, f"{self.METH}/meth.go", "Record.Value", "engine/meth.go")
        keep = [{"package": self.METH, "path": f"{self.METH}/meth.go", "symbol": "Record"}]
        bare = self.repo.generate(self.symbol_spec("meth-bare", [move], stay_symbols=keep))
        self.assert_fail(bare, "unaccounted-assertion function=TestRecordValue assertion=record-value")
        self.assert_absent("meth-bare")
        given = [{
            "function": "TestRecordValue",
            "name": "record-value",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]
        self.assert_ok(self.repo.generate(self.symbol_spec("meth-given", [move], stay_symbols=keep, assertions=given)))
        manifest = self.repo.manifest("meth-given")
        self.assertEqual(
            [(item["function"], item["name"]) for item in manifest["assertions"]],
            [("TestRecordValue", "record-value")],
        )
        self.assert_ok(self.repo.check("meth-given"))
        stripped = json.loads(self.repo.manifest_path("meth-given").read_text(encoding="utf-8"))
        stripped["assertions"] = []
        stripped["destinations"] = [item for item in stripped["destinations"] if item["kind"] != "assertion"]
        path = self.repo.root / "acceptance" / "manifests" / "meth-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(
            self.repo.check("meth-given", manifest=path),
            "unaccounted-assertion function=TestRecordValue assertion=record-value",
        )

    def test_a_nested_binding_does_not_hide_the_method_in_scope_at_the_call(self) -> None:
        types = [self.fix_stay("R"), self.fix_stay("S")]
        outer = self.repo.generate(self.symbol_spec("nest-outer", [self.fix_move("Nested")], stay_symbols=types))
        self.assert_fail(outer)
        self.assertEqual(outer.stdout, "outside-set: R.Read\n")
        self.assert_absent("nest-outer")
        declared = types + [self.fix_stay("R.Read")]
        self.assert_ok(self.repo.generate(self.symbol_spec("nest-outer-stays", [self.fix_move("Nested")], stay_symbols=declared)))
        self.assert_ok(self.repo.check("nest-outer-stays"))
        inner = self.repo.generate(self.symbol_spec("nest-inner", [self.fix_move("Inner")], stay_symbols=types))
        self.assert_fail(inner)
        self.assertEqual(inner.stdout, "outside-set: S.Read\n")
        self.assert_absent("nest-inner")

    def test_a_grouped_constant_uses_what_the_preceding_specification_uses(self) -> None:
        open_group = self.repo.generate(self.symbol_spec("const-open", [self.fix_move("Moved")]))
        self.assert_fail(open_group)
        self.assertEqual(open_group.stdout, "outside-set: Kept\n")
        self.assert_absent("const-open")
        closed = self.repo.generate(
            self.symbol_spec("const-stays", [self.fix_move("Moved")], stay_symbols=[self.fix_stay("Kept")])
        )
        self.assert_ok(closed)
        self.assert_ok(self.repo.check("const-stays"))
        stripped = json.loads(self.repo.manifest_path("const-stays").read_text(encoding="utf-8"))
        stripped["stays"] = []
        path = self.repo.root / "acceptance" / "manifests" / "const-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("const-stays", manifest=path), "outside-set: Kept")

    def test_literal_keys_are_fields_only_for_struct_types(self) -> None:
        local = self.repo.generate(self.symbol_spec("keys-local", [self.fix_move("LocalKeys")]))
        self.assert_ok(local)
        self.assertNotIn("outside-set", local.stdout)
        types = [self.fix_stay("M", self.KEYED), self.fix_stay("S", self.KEYED)]
        mapped = self.repo.generate(self.symbol_spec("keys-map", [self.fix_move("MapKeys")], stay_symbols=types))
        self.assert_fail(mapped)
        self.assertEqual(mapped.stdout, "outside-set: Kept\n")
        self.assert_absent("keys-map")
        declared = self.repo.generate(
            self.symbol_spec("keys-map-stays", [self.fix_move("MapKeys")], stay_symbols=types + [self.fix_stay("Kept")])
        )
        self.assert_ok(declared)
        structured = self.repo.generate(self.symbol_spec("keys-struct", [self.fix_move("StructKeys")], stay_symbols=types))
        self.assert_ok(structured)
        self.assertNotIn("outside-set", structured.stdout)

    MB = "closure/cross/mb"
    MU = "closure/cross/mu"
    MD = "closure/cross/md"
    MC = "closure/cross/mc"
    MG = "closure/cross/mg"
    MT = "closure/cross/mt"

    def at(self, package: str, symbol: str) -> dict:
        return {"package": package, "path": f"{package}/{package.rsplit('/', 1)[-1]}.go", "symbol": symbol}

    def move_at(self, package: str, symbol: str) -> dict:
        return self.repo.symbol(package, f"{package}/{package.rsplit('/', 1)[-1]}.go", symbol, "engine/m.go")

    def test_a_method_of_a_type_of_another_donor_package_is_a_dependency(self) -> None:
        use = self.move_at(self.MU, "Use")
        box = self.at(self.MB, "Box")
        open_method = self.repo.generate(self.symbol_spec("mq-open", [use], stay_symbols=[box]))
        self.assert_fail(open_method)
        self.assertEqual(open_method.stdout, f"outside-set: {self.MB}.Box.Required\n")
        self.assert_absent("mq-open")
        expr = self.repo.generate(self.symbol_spec("mq-expr", [self.move_at(self.MU, "Expr")], stay_symbols=[box]))
        self.assert_fail(expr)
        self.assertEqual(expr.stdout, f"outside-set: {self.MB}.Box.Required\n")
        stays = [box, self.at(self.MB, "Box.Required")]
        self.assert_ok(self.repo.generate(self.symbol_spec("mq-stays", [use], stay_symbols=stays)))
        self.assert_ok(self.repo.check("mq-stays"))
        moved = self.repo.generate(self.symbol_spec(
            "mq-moved", [use, self.move_at(self.MB, "Box"), self.move_at(self.MB, "Box.Required")],
        ))
        self.assert_ok(moved)
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("mq-moved")["symbols"]}
        self.assertEqual(uses["Use"], [f"{self.MB}.Box", f"{self.MB}.Box.Required"])

    def test_a_redeclaring_short_assignment_keeps_the_receiver_type(self) -> None:
        local = self.at(self.MU, "Local")
        for name in ("Redeclare", "Shadow"):
            row = f"mr-{name.lower()}"
            open_method = self.repo.generate(self.symbol_spec(row, [self.move_at(self.MU, name)], stay_symbols=[local]))
            self.assert_fail(open_method)
            self.assertEqual(open_method.stdout, "outside-set: Local.Need\n")
            self.assert_absent(row)
            declared = self.repo.generate(self.symbol_spec(
                f"{row}-stays", [self.move_at(self.MU, name)], stay_symbols=[local, self.at(self.MU, "Local.Need")],
            ))
            self.assert_ok(declared)

    def test_a_dot_import_of_a_donor_package_is_a_dependency(self) -> None:
        dot = self.move_at(self.MD, "Dot")
        open_name = self.repo.generate(self.symbol_spec("md-open", [dot]))
        self.assert_fail(open_name)
        self.assertEqual(open_name.stdout, f"outside-set: {self.MB}.Required\n")
        self.assert_absent("md-open")
        self.assert_ok(self.repo.generate(self.symbol_spec(
            "md-stays", [dot], stay_symbols=[self.at(self.MB, "Required")],
        )))
        self.assert_ok(self.repo.check("md-stays"))
        moved = self.repo.generate(self.symbol_spec("md-moved", [dot, self.move_at(self.MB, "Required")]))
        self.assert_ok(moved)
        uses = {item["name"]: item["uses"] for item in self.repo.manifest("md-moved")["symbols"]}
        self.assertEqual(uses["Dot"], [f"{self.MB}.Required"])
        typed = self.repo.generate(self.symbol_spec(
            "md-type", [self.move_at(self.MD, "DotType")], stay_symbols=[self.at(self.MB, "Box")],
        ))
        self.assert_fail(typed)
        self.assertEqual(typed.stdout, f"outside-set: {self.MB}.Box.Required\n")

    def test_an_import_in_a_comment_is_not_an_import(self) -> None:
        completed = self.repo.generate(self.symbol_spec("mc-comment", [self.move_at(self.MC, "Print")]))
        self.assert_ok(completed)
        self.assertNotIn("outside-set", completed.stdout)
        self.assertEqual(self.repo.manifest("mc-comment")["symbols"][0]["uses"], [])
        self.assert_ok(self.repo.check("mc-comment"))

    def test_receiver_type_parameters_and_elided_pointer_elements_are_not_symbols(self) -> None:
        generic = self.repo.generate(self.symbol_spec(
            "mg-generic", [self.move_at(self.MG, "Box"), self.move_at(self.MG, "Box.Pass")],
        ))
        self.assert_ok(generic)
        self.assertNotIn("outside-set", generic.stdout)
        literal = self.repo.generate(self.symbol_spec(
            "mg-literal", [self.move_at(self.MG, "Lits")], stay_symbols=[self.at(self.MG, "R")],
        ))
        self.assert_ok(literal)
        self.assertNotIn("outside-set", literal.stdout)
        self.assert_ok(self.repo.check("mg-literal"))

    def test_two_donor_assertions_with_one_identity_are_not_bound_to_one_entry(self) -> None:
        move = self.move_at(self.MT, "Move")
        given = [{
            "function": "TestX",
            "name": "same",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]
        completed = self.repo.generate(self.symbol_spec("mt-same", [move], assertions=given))
        self.assert_fail(completed, f"ambiguous-assertion function=TestX assertion=same package={self.MT}")
        self.assert_absent("mt-same")

    def test_an_external_test_keeps_the_staying_symbols_of_its_own_package(self) -> None:
        move = self.repo.symbol(self.XO, f"{self.XO}/xo.go", "Move", "engine/xo.go")
        bare = self.repo.generate(self.symbol_spec("own-bare", [move]))
        self.assert_fail(bare, "unaccounted-assertion function=TestOwnSplit assertion=own-moved")
        self.assertNotIn("left-behind", bare.stdout)
        self.assertNotIn("TestOwn ", bare.stdout)
        self.assertNotIn("assertion=own-kept", bare.stdout)
        self.assert_absent("own-bare")
        given = [{
            "function": "TestOwnSplit",
            "name": "own-moved",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]
        self.assert_ok(self.repo.generate(self.symbol_spec("own-given", [move], assertions=given)))
        stays = [(item["kind"], item["name"]) for item in self.repo.manifest("own-given")["stays"]]
        self.assertIn(("test", "TestOwn"), stays)
        self.assertIn(("assertion", "own-kept"), stays)
        self.assert_ok(self.repo.check("own-given"))

    def test_an_external_test_package_of_a_moved_directory_is_accounted(self) -> None:
        move = self.repo.symbol(self.XT, f"{self.XT}/xt.go", "Move", "engine/xt.go")
        bare = self.repo.generate(self.symbol_spec("ext-bare", [move]))
        self.assert_fail(bare, "unaccounted-assertion function=TestExternal assertion=external-moved")
        self.assertNotIn("assertion=external-kept", bare.stdout)
        self.assert_absent("ext-bare")
        given = [{
            "function": "TestExternal",
            "name": "external-moved",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]
        self.assert_ok(self.repo.generate(self.symbol_spec("ext-given", [move], assertions=given)))
        manifest = self.repo.manifest("ext-given")
        self.assertEqual(
            [(item["function"], item["name"]) for item in manifest["assertions"]],
            [("TestExternal", "external-moved")],
        )
        self.assertEqual(
            [(item["kind"], item["name"]) for item in manifest["stays"]],
            [("assertion", "external-kept")],
        )
        self.assert_ok(self.repo.check("ext-given"))

    def test_a_test_of_a_directory_the_input_does_not_name_is_accounted(self) -> None:
        move = self.repo.symbol(self.FAR, f"{self.FAR}/far.go", "Move", "engine/far.go")
        bare = self.repo.generate(self.symbol_spec("far-bare", [move]))
        self.assert_fail(bare, "left-behind: TestFar")
        self.assert_absent("far-bare")
        kept = self.repo.generate(self.symbol_spec("far-kept", [move], specimens=["TestFar"]))
        self.assert_ok(kept)
        self.assertEqual(
            [(item["kind"], item["name"]) for item in self.repo.manifest("far-kept")["stays"]],
            [("specimen", "TestFar")],
        )
        self.assert_ok(self.repo.check("far-kept"))

    HOLD = "closure/cross/hold"
    AL = "closure/cross/al"
    QB = "closure/cross/qb"
    BX = "closure/cross/bx"
    DP = "closure/cross/dp"
    IC = "closure/cross/ic"
    IG = "closure/cross/ig"
    IH = "closure/cross/ih"

    def test_a_method_does_not_hide_a_package_function_of_its_own_name(self) -> None:
        move = self.move_at(self.HOLD, "Box.Hold")
        box = self.at(self.HOLD, "Box")
        bare = self.repo.generate(self.symbol_spec("hold-bare", [move], stay_symbols=[box]))
        self.assert_fail(bare)
        self.assertEqual(bare.stdout, "outside-set: Hold\n")
        self.assert_absent("hold-bare")
        declared = self.repo.generate(
            self.symbol_spec("hold-declared", [move], stay_symbols=[box, self.at(self.HOLD, "Hold")])
        )
        self.assert_ok(declared)
        self.assert_ok(self.repo.check("hold-declared"))
        stripped = json.loads(self.repo.manifest_path("hold-declared").read_text(encoding="utf-8"))
        stripped["stays"] = [item for item in stripped["stays"] if item["name"] != "Hold"]
        path = self.repo.root / "acceptance" / "manifests" / "hold-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("hold-declared", manifest=path), "outside-set: Hold")

    def test_a_field_key_of_an_alias_of_a_qualified_struct_is_not_a_use(self) -> None:
        move = self.move_at(self.AL, "Build")
        completed = self.repo.generate(
            self.symbol_spec("alias-keyed", [move], stay_symbols=[self.at(self.AL, "Alias")])
        )
        self.assert_ok(completed)
        self.assertNotIn("outside-set", completed.stdout)
        self.assertEqual(
            {item["name"]: item["uses"] for item in self.repo.manifest("alias-keyed")["symbols"]},
            {"Build": []},
        )
        self.assert_ok(self.repo.check("alias-keyed"))

    def test_a_donor_test_of_another_package_that_calls_a_moved_method_is_accounted(self) -> None:
        move = self.move_at(self.BX, "Box.Count")
        keep = [self.at(self.BX, "Box")]
        bare = self.repo.generate(self.symbol_spec("bx-bare", [move], stay_symbols=keep))
        self.assert_fail(bare, "unaccounted-assertion function=TestCount assertion=count")
        self.assert_absent("bx-bare")
        given = [{
            "function": "TestCount",
            "name": "count",
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]
        self.assert_ok(self.repo.generate(self.symbol_spec("bx-given", [move], stay_symbols=keep, assertions=given)))
        self.assertEqual(
            [(item["function"], item["name"]) for item in self.repo.manifest("bx-given")["assertions"]],
            [("TestCount", "count")],
        )
        self.assert_ok(self.repo.check("bx-given"))

    def test_a_donor_test_that_dot_imports_a_moved_function_is_accounted(self) -> None:
        move = self.move_at(self.DP, "Move")
        bare = self.repo.generate(self.symbol_spec("dot-bare", [move]))
        self.assert_fail(bare, "left-behind: TestDot")
        self.assert_absent("dot-bare")
        kept = self.repo.generate(self.symbol_spec("dot-kept", [move], specimens=["TestDot"]))
        self.assert_ok(kept)
        self.assertEqual(
            [(item["kind"], item["name"]) for item in self.repo.manifest("dot-kept")["stays"]],
            [("specimen", "TestDot")],
        )
        self.assert_ok(self.repo.check("dot-kept"))

    def test_equal_import_spellings_give_the_same_closure(self) -> None:
        for package, label in ((self.IG, "inline"), (self.IH, "semicolon")):
            move = self.move_at(package, "Move")
            bare = self.repo.generate(self.symbol_spec(f"imp-{label}-bare", [move]))
            self.assert_fail(bare)
            self.assertEqual(bare.stdout, f"outside-set: {self.IC}.Count\n", label)
            self.assert_absent(f"imp-{label}-bare")
            both = self.repo.generate(
                self.symbol_spec(f"imp-{label}", [move, self.move_at(self.IC, "Count")])
            )
            self.assert_ok(both)
            self.assertEqual(
                {item["name"]: item["uses"] for item in self.repo.manifest(f"imp-{label}")["symbols"]},
                {"Move": [f"{self.IC}.Count"], "Count": []},
                label,
            )
            self.assert_ok(self.repo.check(f"imp-{label}"))

    def test_check_binds_an_assertion_to_its_donor_file_and_one_destination(self) -> None:
        spec = self.symbol_spec("bind-two", self.alpha_moves() + self.beta_moves(), assertions=self.clone_assertions())
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.check("bind-two"))
        original = json.loads(self.repo.manifest_path("bind-two").read_text(encoding="utf-8"))
        path = self.repo.root / "acceptance" / "manifests" / "bind-two-mutated.json"
        twice = json.loads(json.dumps(original))
        extra = next(item for item in twice["destinations"] if item["kind"] == "assertion")
        twice["destinations"].append({**extra, "test": "TestOther"})
        path.write_text(json.dumps(twice), encoding="utf-8")
        self.assert_fail(
            self.repo.check("bind-two", manifest=path),
            "ambiguous-destination function=TestStoreBehaviour assertion=clone-name",
        )
        moved_file = json.loads(json.dumps(original))
        for item in moved_file["assertions"]:
            item["file"] = f"{self.ALPHA}/gone_test.go"
        path.write_text(json.dumps(moved_file), encoding="utf-8")
        self.assert_fail(self.repo.check("bind-two", manifest=path), "assertions")

    def test_check_needs_the_donor_seal_to_cover_every_moved_file(self) -> None:
        spec = self.symbol_spec("seal-donor", self.alpha_moves(), assertions=self.clone_assertions())
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.check("seal-donor"))
        stripped = json.loads(self.repo.manifest_path("seal-donor").read_text(encoding="utf-8"))
        stripped["paths"] = [item for item in stripped["paths"] if item["repository"] != "gateway"]
        path = self.repo.root / "acceptance" / "manifests" / "seal-donor-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("seal-donor", manifest=path), "unsealed-donor: gateway")
        shrunk = json.loads(self.repo.manifest_path("seal-donor").read_text(encoding="utf-8"))
        for item in shrunk["paths"]:
            if item["repository"] == "gateway":
                item["paths"] = []
                item["sha256"] = hashlib.sha256(b"").hexdigest()
        (self.repo.root / "acceptance" / "manifests" / "seal-donor.gateway.lst").write_bytes(b"")
        path.write_text(json.dumps(shrunk), encoding="utf-8")
        self.assert_fail(self.repo.check("seal-donor", manifest=path), f"unsealed-source: gateway:{self.ALPHA}/core.go")

    def test_check_rejects_a_symbol_destination_outside_the_sealed_list(self) -> None:
        spec = self.symbol_spec("seal-symbol", self.alpha_moves(), assertions=self.clone_assertions())
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.check("seal-symbol"))
        moved = json.loads(self.repo.manifest_path("seal-symbol").read_text(encoding="utf-8"))
        for entry in moved["destinations"]:
            if entry.get("name") == "cloneRecord":
                entry["path"] = "unsealed/other.go"
        path = self.repo.root / "acceptance" / "manifests" / "seal-symbol-moved.json"
        path.write_text(json.dumps(moved), encoding="utf-8")
        self.assert_fail(
            self.repo.check("seal-symbol", manifest=path), "unsealed-destination: ebusgo:unsealed/other.go",
        )

    def test_same_named_assertions_of_two_packages_stay_distinct(self) -> None:
        moves = [
            self.repo.symbol(self.DA, f"{self.DA}/da.go", "MoveA", "engine/dup.go"),
            self.repo.symbol(self.DB, f"{self.DB}/db.go", "MoveB", "engine/dup.go"),
        ]

        def given(package: str, test: str) -> dict:
            return {
                "function": "TestBehaviour",
                "name": "same",
                "package": package,
                "destination_repository": "ebusgo",
                "destination_path": "dest/echo_test.go",
                "test": test,
            }

        bare = dict(given(self.DA, "TestEcho"))
        del bare["package"]
        ambiguous = self.repo.generate(self.symbol_spec("dup-bare", moves, assertions=[bare]))
        self.assert_fail(
            ambiguous,
            f"ambiguous-assertion function=TestBehaviour assertion=same package={self.DA}",
            f"ambiguous-assertion function=TestBehaviour assertion=same package={self.DB}",
        )
        self.assert_absent("dup-bare")
        spec = self.symbol_spec(
            "dup-two", moves, assertions=[given(self.DA, "TestEcho"), given(self.DB, "TestHistory")],
        )
        self.assert_ok(self.repo.generate(spec))
        manifest = self.repo.manifest("dup-two")
        self.assertEqual(
            [(item["package"], item["test"]) for item in manifest["destinations"] if item["kind"] == "assertion"],
            [(self.DA, "TestEcho"), (self.DB, "TestHistory")],
        )
        self.assert_ok(self.repo.check("dup-two"))
        compared = self.repo.compare("dup-two", self.repo.dest)
        self.assert_ok(compared)
        outcomes = [line for line in compared.stdout.splitlines() if line.startswith("outcome ")]
        self.assertEqual(
            sorted(line.split("test=")[1].split()[0] for line in outcomes), ["TestEcho", "TestHistory"],
        )
        absent = self.repo.private_dest()
        echo = absent / "dest" / "echo_test.go"
        echo.write_text(
            echo.read_text(encoding="utf-8").replace(
                "func TestHistory(t *testing.T) { report(t, false) }\n", "", 1,
            ),
            encoding="utf-8",
        )
        missing = self.repo.compare("dup-two", absent)
        self.assert_fail(missing, "not-executed assertion=same function=TestBehaviour test=TestHistory")
        self.assertNotIn("compare: ok", missing.stdout)

    def test_check_rejects_a_symbol_manifest_without_its_symbols(self) -> None:
        spec = self.symbol_spec("strip-symbols", self.alpha_moves(), assertions=self.clone_assertions())
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.check("strip-symbols"))
        stripped = json.loads(self.repo.manifest_path("strip-symbols").read_text(encoding="utf-8"))
        stripped["symbols"] = []
        path = self.repo.root / "acceptance" / "manifests" / "strip-symbols-empty.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("strip-symbols", manifest=path), "symbol-set")

    def test_deletion_refuses_a_file_that_was_only_partly_moved(self) -> None:
        self.assert_ok(self.repo.generate(
            self.symbol_spec("part-move", self.alpha_moves(), assertions=self.clone_assertions())
        ))
        dest = self.repo.private_dest()
        (dest / "engine").mkdir(exist_ok=True)
        (dest / "engine" / "records.go").write_text("package engine\n", encoding="utf-8")
        git(dest, "add", "-A")
        git(dest, "commit", "-m", "records")
        merged = git_out(dest, "rev-parse", "HEAD")
        (dest / "REV.txt").write_text("integrated again\n", encoding="utf-8")
        git(dest, "add", "-A")
        git(dest, "commit", "-m", "integrated again")
        integrated = git_out(dest, "rev-parse", "HEAD")
        self.assert_ok(self.repo.receipt("part-move", self.repo.result("ebusgo", "row", merged), dest, "ebusgo"))
        self.assert_ok(self.repo.receipt(
            "part-move", self.repo.result("ebusgo", "whole-session", integrated), dest, "ebusgo",
        ))
        clone = self.repo.root.parent / "donor-partial"
        git(self.repo.root.parent, "clone", str(self.repo.root), str(clone))
        ledger = clone / "tools" / "boundary" / "ledger.tsv"
        ledger.write_text(f"{self.ALPHA}/core.go\tmove\tsample\tGG13\n", encoding="utf-8")
        git(clone, "add", "-A")
        git(clone, "commit", "-m", "ledger names the partly moved file")
        body = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": git_out(clone, "rev-parse", "HEAD"),
            "manifests": [str(self.repo.manifest_path("part-move"))],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        snapshot = self._gg13_snapshot()
        refused = self.repo.deletion(body, gateway=clone)
        written = self._gg13_snapshot()
        self._restore_gg13(snapshot)
        self.assert_fail(refused, f"partial-move: {self.ALPHA}/core.go")
        self.assertEqual(written, snapshot)
        # A manifest cut down to its symbol-level records is no whole-file coverage.
        truncated = json.loads(self.repo.manifest_path("part-move").read_text(encoding="utf-8"))
        truncated["symbols"] = []
        cut = self.repo.root / "acceptance" / "manifests" / "part-move-cut.json"
        cut.write_text(json.dumps(truncated), encoding="utf-8")
        body["manifests"] = [str(cut)]
        snapshot = self._gg13_snapshot()
        refused = self.repo.deletion(body, gateway=clone)
        written = self._gg13_snapshot()
        self._restore_gg13(snapshot)
        self.assert_fail(refused, f"partial-move: {self.ALPHA}/core.go")
        self.assertEqual(written, snapshot)

    def test_deletion_refuses_a_shared_file_the_symbol_move_did_not_move(self) -> None:
        shared = [{"repository": "gateway", "path": "closure/closed/moved.go"}]
        self.assert_ok(self.repo.generate(self.symbol_spec(
            "shared-move", self.alpha_moves(), assertions=self.clone_assertions(), shared=shared,
        )))
        dest = self.repo.private_dest()
        (dest / "engine").mkdir(exist_ok=True)
        (dest / "engine" / "records.go").write_text("package engine\n", encoding="utf-8")
        git(dest, "add", "-A")
        git(dest, "commit", "-m", "records")
        merged = git_out(dest, "rev-parse", "HEAD")
        (dest / "REV.txt").write_text("integrated again\n", encoding="utf-8")
        git(dest, "add", "-A")
        git(dest, "commit", "-m", "integrated again")
        integrated = git_out(dest, "rev-parse", "HEAD")
        self.assert_ok(self.repo.receipt("shared-move", self.repo.result("ebusgo", "row", merged), dest, "ebusgo"))
        self.assert_ok(self.repo.receipt(
            "shared-move", self.repo.result("ebusgo", "whole-session", integrated), dest, "ebusgo",
        ))
        clone = self.repo.root.parent / "donor-shared"
        git(self.repo.root.parent, "clone", str(self.repo.root), str(clone))
        ledger = clone / "tools" / "boundary" / "ledger.tsv"
        ledger.write_text("closure/closed/moved.go\tmove\tsample\tGG13\n", encoding="utf-8")
        git(clone, "add", "-A")
        git(clone, "commit", "-m", "ledger names the shared file")
        body = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": git_out(clone, "rev-parse", "HEAD"),
            "manifests": [str(self.repo.manifest_path("shared-move"))],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        snapshot = self._gg13_snapshot()
        refused = self.repo.deletion(body, gateway=clone)
        written = self._gg13_snapshot()
        self._restore_gg13(snapshot)
        self.assert_fail(refused, "partial-move: closure/closed/moved.go")
        self.assertEqual(written, snapshot)

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
        shared_path = self.repo.manifest_path("batch-326-shared")
        shared_bytes = shared_path.read_bytes()
        current = "missing-destination case=m326 row=326-current assertion=current-assert"
        voltage = "missing-destination case=m326 row=326-voltage assertion=voltage-assert"

        def write_variant(name: str, mutate) -> Path:
            body = json.loads(shared_bytes)
            mutate(body)
            path = self.repo.root / "acceptance" / "manifests" / name
            path.write_text(json.dumps(body), encoding="utf-8")
            return path

        def drop_cases(body: dict) -> None:
            body["destinations"] = [item for item in body["destinations"] if item.get("kind") != "case"]

        dropped = write_variant("326-no-case-dest.json", drop_cases)
        self.assert_fail(self.repo.check("batch-326-shared", manifest=dropped), voltage, current)
        self.assertEqual(shared_path.read_bytes(), shared_bytes)

        def blank(field: str):
            def mutate(body: dict) -> None:
                for item in body["destinations"]:
                    if item.get("kind") == "case" and item.get("assertion") == "current-assert":
                        item[field] = ""
            return mutate

        for field in ("test", "repository", "path"):
            variant = write_variant(f"326-blank-{field}.json", blank(field))
            completed = self.repo.check("batch-326-shared", manifest=variant)
            self.assert_fail(completed, current)
            self.assertNotIn(voltage, completed.stdout)
        self.assertEqual(shared_path.read_bytes(), shared_bytes)

        def duplicate(body: dict) -> None:
            extra = [
                dict(item)
                for item in body["destinations"]
                if item.get("kind") == "case" and item.get("assertion") == "current-assert"
            ]
            body["destinations"].extend(extra)

        ambiguous = write_variant("326-ambiguous-dest.json", duplicate)
        self.assert_fail(
            self.repo.check("batch-326-shared", manifest=ambiguous),
            "ambiguous-destination case=m326 row=326-current assertion=current-assert",
        )
        self.assert_ok(self.repo.check("batch-326-shared"))
        self.assertEqual(shared_path.read_bytes(), shared_bytes)

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

    def test_approved_vectors_must_account_for_output_changes(self) -> None:
        spec = self.repo.base(
            "accounted-output",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[
                self.repo.difference("vec/diff-status.json"),
                self.repo.difference("vec/diff-north.json"),
            ],
        )
        self.assert_ok(self.repo.generate(spec))
        manifest_path = self.repo.manifest_path("accounted-output")
        original = manifest_path.read_bytes()
        status = {
            "case": "*",
            "field": "execution_status",
            "old_present": True,
            "old": "0",
            "new": "1",
        }
        northbound = {
            "case": "north",
            "field": "northbound",
            "old_present": False,
            "old": None,
            "new": "present",
        }
        unrelated = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            output="correct",
            differences=[status],
        )
        unrelated["new_output"] = "unrelated-output"
        self.assert_fail(
            self.repo.receipt("accounted-output", unrelated, self.repo.dest, "ebusgo"),
            "unapproved-difference: output",
        )
        self.assertEqual(manifest_path.read_bytes(), original)
        decoy = self.repo.result(
            "ebusgo", "row", self.repo.merged,
            output="correct",
            differences=[northbound],
        )
        decoy["new_output"] = "unrelated-output"
        self.assert_fail(
            self.repo.receipt("accounted-output", decoy, self.repo.dest, "ebusgo"),
            "unapproved-difference: output",
        )
        self.assertEqual(manifest_path.read_bytes(), original)
        hidden = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            output="kept=1",
            differences=[status],
        )
        hidden["old_output"] = "kept=1"
        hidden["new_output"] = "kept=1\nnorthbound=present"
        self.assert_fail(
            self.repo.receipt("accounted-output", hidden, self.repo.dest, "ebusgo"),
            "unapproved-difference: northbound",
        )
        self.assertEqual(manifest_path.read_bytes(), original)

        def entry(kind: str, commit: str, old_output: str, new_output: str, differences: list) -> dict:
            return {
                "repository": "ebusgo",
                "kind": kind,
                "donor_sha": self.repo.sha,
                "destination_commit": commit,
                "old_status": 0,
                "new_status": 1,
                "old_output": old_output,
                "new_output": new_output,
                "differences": differences,
                "compared": [],
                "outcome": "approved-difference",
            }

        planted_path = self.repo.root / "acceptance" / "manifests" / "accounted-planted.json"
        planted = json.loads(original)
        planted["receipts"] = [
            entry("row", self.repo.merged, "correct", "unrelated-output", [status]),
            entry("whole-session", self.repo.integrated, "correct", "unrelated-output", [status]),
        ]
        planted_path.write_text(json.dumps(planted), encoding="utf-8")
        deletion = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(planted_path)],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        list_path = self.repo.root / "acceptance" / "manifests" / "GG13.lst"
        record_path = self.repo.root / "acceptance" / "manifests" / "GG13.json"
        before_list = list_path.read_bytes() if list_path.exists() else None
        before_record = record_path.read_bytes() if record_path.exists() else None
        self.assert_fail(self.repo.deletion(deletion), "missing-receipt: closure/closed/moved.go")
        after_list = list_path.read_bytes() if list_path.exists() else None
        after_record = record_path.read_bytes() if record_path.exists() else None
        self.assertEqual(after_list, before_list)
        self.assertEqual(after_record, before_record)

        accounted = self.repo.result(
            "ebusgo", "row", self.repo.merged,
            output="kept=1",
            differences=[northbound],
        )
        accounted["case"] = "north"
        accounted["old_output"] = "kept=1"
        accounted["new_output"] = "kept=1\nnorthbound=present"
        self.assert_ok(self.repo.receipt("accounted-output", accounted, self.repo.dest, "ebusgo"))
        stored = self.repo.manifest("accounted-output")["receipts"][0]
        self.assertEqual(stored["outcome"], "approved-difference")
        self.assertEqual(stored["new_output"], "kept=1\nnorthbound=present")
        extra = self.repo.result(
            "ebusgo", "whole-session", self.repo.integrated,
            output="kept=1",
            differences=[northbound],
        )
        extra["case"] = "north"
        extra["old_output"] = "kept=1"
        extra["new_output"] = "kept=1\nnorthbound=present\nextra=1"
        before_extra = manifest_path.read_bytes()
        self.assert_fail(
            self.repo.receipt("accounted-output", extra, self.repo.dest, "ebusgo"),
            "unapproved-difference: extra",
        )
        self.assertEqual(manifest_path.read_bytes(), before_extra)
        session = self.repo.result(
            "ebusgo", "whole-session", self.repo.integrated,
            output="kept=1",
            differences=[northbound],
        )
        session["case"] = "north"
        session["old_output"] = "kept=1"
        session["new_output"] = "kept=1\nnorthbound=present"
        self.assert_ok(self.repo.receipt("accounted-output", session, self.repo.dest, "ebusgo"))
        deletion["manifests"] = [str(manifest_path)]
        self.assert_ok(self.repo.deletion(deletion))
        self.assertIn(b"closure/closed/moved.go\n", list_path.read_bytes())
        if before_list is None:
            list_path.unlink()
        else:
            list_path.write_bytes(before_list)
        if before_record is None:
            record_path.unlink()
        else:
            record_path.write_bytes(before_record)

    def test_each_destination_repository_needs_its_own_receipts(self) -> None:
        spec = self.repo.base(
            "two-dest",
            moves=[
                self.repo.move("closure/closed/moved.go", "engine/moved.go", "ebusgo"),
                self.repo.move("closure/closed/shared.go", "engine/capture.go", "modbusreg"),
            ],
        )
        self.assert_ok(self.repo.generate(spec))
        manifest_path = self.repo.manifest_path("two-dest")
        original = manifest_path.read_bytes()
        self.assert_fail(
            self.repo.receipt(
                "two-dest",
                self.repo.result("canbusreg", "row", self.repo.merged),
                self.repo.dest,
                "canbusreg",
            ),
            "not-destination: canbusreg",
        )
        self.assertEqual(manifest_path.read_bytes(), original)
        self.assert_ok(self.repo.receipt(
            "two-dest", self.repo.result("ebusgo", "row", self.repo.merged), self.repo.dest, "ebusgo",
        ))
        self.assert_ok(self.repo.receipt(
            "two-dest",
            self.repo.result("modbusreg", "whole-session", self.repo.integrated),
            self.repo.dest,
            "modbusreg",
        ))
        stored = {(item["repository"], item["kind"]) for item in self.repo.manifest("two-dest")["receipts"]}
        self.assertEqual(stored, {("ebusgo", "row"), ("modbusreg", "whole-session")})
        deletion = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(manifest_path)],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        list_path = self.repo.root / "acceptance" / "manifests" / "GG13.lst"
        record_path = self.repo.root / "acceptance" / "manifests" / "GG13.json"
        before_list = list_path.read_bytes() if list_path.exists() else None
        before_record = record_path.read_bytes() if record_path.exists() else None
        self.assert_fail(self.repo.deletion(deletion), "missing-receipt: closure/closed/moved.go")
        after_list = list_path.read_bytes() if list_path.exists() else None
        after_record = record_path.read_bytes() if record_path.exists() else None
        self.assertEqual(after_list, before_list)
        self.assertEqual(after_record, before_record)
        self.assert_ok(self.repo.receipt(
            "two-dest",
            self.repo.result("ebusgo", "whole-session", self.repo.integrated),
            self.repo.dest,
            "ebusgo",
        ))
        self.assert_ok(self.repo.receipt(
            "two-dest", self.repo.result("modbusreg", "row", self.repo.merged), self.repo.dest, "modbusreg",
        ))
        self.assert_ok(self.repo.deletion(deletion))
        listed = list_path.read_bytes()
        self.assertIn(b"closure/closed/moved.go\n", listed)
        self.assertNotIn(b"*", listed)
        if before_list is None:
            list_path.unlink()
        else:
            list_path.write_bytes(before_list)
        if before_record is None:
            record_path.unlink()
        else:
            record_path.write_bytes(before_record)

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

    def test_standalone_receipt_must_name_the_classifier_destination(self) -> None:
        # The standalone proof is accepted only on a manifest that covers the
        # classifier, and only when its repository and destination commit are a
        # pair already recorded for that classifier destination.
        classifier = self.repo.base(
            "qf01-classifier",
            moves=[self.repo.move("cmd/growatt-can-classify/main.go", "cmd/growatt-can-classify/main.go", "canbusreg")],
            new_files=[{"repository": "ebusgo", "path": "engine/note.go"}],
        )
        internal = self.repo.base(
            "qf01-internal",
            moves=[self.repo.move("internal/growattcanclassify/classify.go", "internal/growattcanclassify/classify.go", "canbusreg")],
        )
        unrelated = self.repo.base(
            "qf01-unrelated",
            moves=[self.repo.move("cmd/gateway/stub.go", "engine/stub.go", "ebusgo")],
            new_files=[{"repository": "canbusreg", "path": "notes/decoy.go"}],
        )
        self.assert_ok(self.repo.generate(classifier))
        self.assert_ok(self.repo.generate(internal))
        self.assert_ok(self.repo.generate(unrelated))
        for row in ("qf01-classifier", "qf01-internal"):
            self.assert_ok(self.repo.receipt(row, self.repo.result("canbusreg", "row", self.repo.merged), self.repo.dest, "canbusreg"))
            self.assert_ok(self.repo.receipt(row, self.repo.result("canbusreg", "whole-session", self.repo.integrated), self.repo.dest, "canbusreg"))
        self.assert_ok(self.repo.receipt("qf01-classifier", self.repo.result("ebusgo", "row", self.repo.merged), self.repo.dest, "ebusgo"))
        self.assert_ok(self.repo.receipt(
            "qf01-classifier",
            self.repo.result("ebusgo", "whole-session", self.repo.integrated),
            self.repo.dest,
            "ebusgo",
        ))
        self.assert_ok(self.repo.receipt("qf01-unrelated", self.repo.result("ebusgo", "row", self.repo.merged), self.repo.dest, "ebusgo"))
        self.assert_ok(self.repo.receipt(
            "qf01-unrelated",
            self.repo.result("ebusgo", "whole-session", self.repo.integrated),
            self.repo.dest,
            "ebusgo",
        ))
        standalone = self.repo.result(
            "ebusgo", "standalone-classifier", self.repo.integrated, compared=list(SURFACES),
        )
        self.assert_ok(self.repo.receipt("qf01-unrelated", standalone, self.repo.dest, "ebusgo"))
        body = {
            "row": "GG07",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [
                str(self.repo.manifest_path("qf01-classifier")),
                str(self.repo.manifest_path("qf01-internal")),
                str(self.repo.manifest_path("qf01-unrelated")),
            ],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        list_path = self.repo.root / "acceptance" / "manifests" / "GG07.lst"
        record_path = self.repo.root / "acceptance" / "manifests" / "GG07.json"
        before_list = list_path.read_bytes() if list_path.exists() else None
        before_record = record_path.read_bytes() if record_path.exists() else None

        def unchanged() -> None:
            after_list = list_path.read_bytes() if list_path.exists() else None
            after_record = record_path.read_bytes() if record_path.exists() else None
            self.assertEqual(after_list, before_list)
            self.assertEqual(after_record, before_record)

        try:
            self.assert_fail(self.repo.deletion(body), "missing-receipt: standalone-classifier")
            unchanged()
            self.assert_ok(self.repo.receipt(
                "qf01-classifier",
                self.repo.result("ebusgo", "standalone-classifier", self.repo.integrated, compared=list(SURFACES)),
                self.repo.dest,
                "ebusgo",
            ))
            self.assert_fail(self.repo.deletion(body), "missing-receipt: standalone-classifier")
            unchanged()
            other_dest = self.repo.private_dest()
            (other_dest / "REV-other.txt").write_text("other\n", encoding="utf-8")
            git(other_dest, "add", "-A")
            git(other_dest, "commit", "-m", "other")
            other = git_out(other_dest, "rev-parse", "HEAD")
            self.assertNotEqual(other, self.repo.merged)
            self.assertNotEqual(other, self.repo.integrated)
            self.assert_ok(self.repo.receipt(
                "qf01-classifier",
                self.repo.result("canbusreg", "standalone-classifier", other, compared=list(SURFACES)),
                other_dest,
                "canbusreg",
            ))
            self.assert_fail(self.repo.deletion(body), "missing-receipt: standalone-classifier")
            unchanged()
            self.assert_ok(self.repo.receipt(
                "qf01-unrelated",
                self.repo.result("canbusreg", "standalone-classifier", self.repo.integrated, compared=list(SURFACES)),
                self.repo.dest,
                "canbusreg",
            ))
            self.assert_fail(self.repo.deletion(body), "missing-receipt: standalone-classifier")
            unchanged()
            self.assert_ok(self.repo.receipt(
                "qf01-classifier",
                self.repo.result("canbusreg", "standalone-classifier", self.repo.integrated, compared=list(SURFACES)),
                self.repo.dest,
                "canbusreg",
            ))
            self.assert_ok(self.repo.deletion(body))
            text = list_path.read_text(encoding="utf-8")
            self.assertEqual(
                text,
                "cmd/growatt-can-classify/main.go\ninternal/growattcanclassify/classify.go\n",
            )
            self.assertNotIn("*", text)
            self.assertNotIn("cmd/gateway/stub.go", text)
            self.assertNotIn("engine/note.go", text)
        finally:
            if before_list is None:
                list_path.unlink(missing_ok=True)
            else:
                list_path.write_bytes(before_list)
            if before_record is None:
                record_path.unlink(missing_ok=True)
            else:
                record_path.write_bytes(before_record)

    def test_unsupported_mapping_kind_fails_generation_and_validation(self) -> None:
        meas_sig = self.repo.sig["measurement_rows.go"]
        meas_ops = fill(meas_sig, MEAS)
        selectors = selector_map(meas_sig, MEAS)
        typo = self.repo.base(
            "batch-misspelled-kind",
            mapping_rows=[self.repo.pattern(
                "meas-typo", "specfication", ["in-case"], "in-assert", meas_sig,
                EXEMPLARS["measurement_rows.go"], meas_ops,
            )],
            expectations=[self.repo.expectation(
                "in-case", "specification",
                [self.repo.bound("meas-typo", "in-assert", "TestEcho")],
                selectors,
                [],
            )],
        )
        self.assert_fail(self.repo.generate(typo), "unsupported-kind: specfication")
        self.assert_absent("batch-misspelled-kind")
        held = self.repo.base(
            "batch-kind-hold",
            mapping_rows=[self.repo.pattern(
                "meas-held", "specification", ["in-case"], "in-assert", meas_sig,
                EXEMPLARS["measurement_rows.go"], meas_ops,
            )],
            expectations=[self.repo.expectation(
                "in-case", "specification",
                [self.repo.bound("meas-held", "in-assert", "TestEcho")],
                selectors,
                [self.repo.ref("specification", "vec/meas.json")],
            )],
        )
        self.assert_ok(self.repo.generate(held))
        path = self.repo.manifest_path("batch-kind-hold")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["patterns"][0]["kind"], "specification")
        manifest["patterns"][0]["kind"] = "specfication"
        manifest["expectations"][0]["references"] = []
        path.write_text(json.dumps(manifest), encoding="utf-8")
        mutated = path.read_bytes()
        self.assert_fail(self.repo.check("batch-kind-hold"), "unsupported-kind: specfication")
        compared = self.repo.compare("batch-kind-hold", self.repo.dest)
        self.assert_fail(compared, "unsupported-kind: specfication")
        self.assertNotIn("compare: ok", compared.stdout)
        self.assertEqual(path.read_bytes(), mutated)

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

    def _gg13_snapshot(self) -> tuple[bytes | None, bytes | None]:
        directory = self.repo.root / "acceptance" / "manifests"
        listed = directory / "GG13.lst"
        recorded = directory / "GG13.json"
        return (
            listed.read_bytes() if listed.exists() else None,
            recorded.read_bytes() if recorded.exists() else None,
        )

    def _restore_gg13(self, snapshot: tuple[bytes | None, bytes | None]) -> None:
        directory = self.repo.root / "acceptance" / "manifests"
        for name, payload in (("GG13.lst", snapshot[0]), ("GG13.json", snapshot[1])):
            path = directory / name
            if payload is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(payload)

    def test_deletion_binds_the_requested_donor(self) -> None:
        spec = self.repo.base(
            "donor-bind",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
        )
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.receipt(
            "donor-bind", self.repo.result("ebusgo", "row", self.repo.merged), self.repo.dest, "ebusgo",
        ))
        self.assert_ok(self.repo.receipt(
            "donor-bind",
            self.repo.result("ebusgo", "whole-session", self.repo.integrated),
            self.repo.dest,
            "ebusgo",
        ))
        manifest_path = self.repo.manifest_path("donor-bind")
        clone = self.repo.root.parent / "donor-moved"
        git(self.repo.root.parent, "clone", str(self.repo.root), str(clone))
        moved = clone / "closure" / "closed" / "moved.go"
        moved.write_text("package sample\n\nfunc Moved() int { return 2 }\n", encoding="utf-8")
        git(clone, "add", "-A")
        git(clone, "commit", "-m", "donor file changed")
        new_sha = git_out(clone, "rev-parse", "HEAD")
        self.assertNotEqual(new_sha, self.repo.sha)
        base = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(manifest_path)],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        snapshot = self._gg13_snapshot()
        changed = dict(base)
        changed["donor_sha"] = new_sha
        changed["ledger_commit"] = new_sha
        self.assert_fail(
            self.repo.deletion(changed, gateway=clone),
            "missing-receipt: closure/closed/moved.go",
        )
        self.assertEqual(self._gg13_snapshot(), snapshot)
        other_repository = dict(base)
        other_repository["donor_repository"] = "elsewhere"
        self.assert_fail(
            self.repo.deletion(other_repository),
            "missing-receipt: closure/closed/moved.go",
        )
        self.assertEqual(self._gg13_snapshot(), snapshot)
        edited = json.loads(manifest_path.read_text(encoding="utf-8"))
        edited["donor"]["repository"] = "elsewhere"
        edited_path = self.repo.root / "acceptance" / "manifests" / "donor-bind-elsewhere.json"
        edited_path.write_text(json.dumps(edited), encoding="utf-8")
        renamed = dict(base)
        renamed["manifests"] = [str(edited_path)]
        self.assert_fail(
            self.repo.deletion(renamed),
            "missing-receipt: closure/closed/moved.go",
        )
        self.assertEqual(self._gg13_snapshot(), snapshot)
        self.assert_ok(self.repo.deletion(base))
        recorded = json.loads((self.repo.root / "acceptance" / "manifests" / "GG13.json").read_text(encoding="utf-8"))
        self.assertEqual(recorded["donor_sha"], self.repo.sha)
        self.assertIn(b"closure/closed/moved.go\n", (self.repo.root / "acceptance" / "manifests" / "GG13.lst").read_bytes())
        self._restore_gg13(snapshot)

    def test_approved_vector_must_match_its_reference(self) -> None:
        spec = self.repo.base(
            "status-recheck",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[self.repo.difference("vec/diff-status.json")],
        )
        self.assert_ok(self.repo.generate(spec))
        path = self.repo.manifest_path("status-recheck")
        original = path.read_bytes()
        body = json.loads(original)
        self.assertEqual(body["expected_differences"][0]["new"], "1")
        self.assertEqual(body["expected_differences"][0]["reference"]["projection"]["new"], "1")
        body["expected_differences"][0]["new"] = "2"
        path.write_text(json.dumps(body), encoding="utf-8")
        try:
            self.assert_fail(self.repo.check("status-recheck"), "mutated: docs-semantic:vec/diff-status.json")
            widened = self.repo.result(
                "ebusgo", "row", self.repo.merged, old_status=0, new_status=2,
                differences=[{
                    "case": "*",
                    "field": "execution_status",
                    "old_present": True,
                    "old": "0",
                    "new": "2",
                }],
            )
            before = path.read_bytes()
            self.assert_fail(
                self.repo.receipt("status-recheck", widened, self.repo.dest, "ebusgo"),
                "mutated: docs-semantic:vec/diff-status.json",
            )
            self.assertEqual(path.read_bytes(), before)
            compared = self.repo.compare("status-recheck", self.repo.dest)
            self.assert_fail(compared, "mutated: docs-semantic:vec/diff-status.json")
            self.assertNotIn("compare: ok", compared.stdout)
        finally:
            path.write_bytes(original)
        approved = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            differences=[{
                "case": "*",
                "field": "execution_status",
                "old_present": True,
                "old": "0",
                "new": "1",
            }],
        )
        self.assert_ok(self.repo.receipt("status-recheck", approved, self.repo.dest, "ebusgo"))
        self.assertEqual(self.repo.manifest("status-recheck")["receipts"][0]["new_status"], 1)

    def test_repeated_output_fields_stay_visible(self) -> None:
        spec = self.repo.base(
            "repeat-fields",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[self.repo.difference("vec/diff-status.json")],
        )
        self.assert_ok(self.repo.generate(spec))
        path = self.repo.manifest_path("repeat-fields")
        original = path.read_bytes()
        status = {
            "case": "*",
            "field": "execution_status",
            "old_present": True,
            "old": "0",
            "new": "1",
        }
        hidden = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1, differences=[status],
        )
        hidden["old_output"] = "reading=230\nreading=230\nexecution_status=0\n"
        hidden["new_output"] = "reading=999\nreading=230\nexecution_status=1\n"
        self.assert_fail(
            self.repo.receipt("repeat-fields", hidden, self.repo.dest, "ebusgo"),
            "unapproved-difference: reading",
        )
        self.assertEqual(path.read_bytes(), original)
        snapshot = self._gg13_snapshot()
        planted = json.loads(original)

        def stored(kind: str, commit: str) -> dict:
            return {
                "repository": "ebusgo",
                "kind": kind,
                "donor_sha": self.repo.sha,
                "destination_commit": commit,
                "old_status": 0,
                "new_status": 1,
                "old_output": hidden["old_output"],
                "new_output": hidden["new_output"],
                "differences": [status],
                "compared": [],
                "outcome": "approved-difference",
            }

        planted["receipts"] = [
            stored("row", self.repo.merged),
            stored("whole-session", self.repo.integrated),
        ]
        planted_path = self.repo.root / "acceptance" / "manifests" / "repeat-planted.json"
        planted_path.write_text(json.dumps(planted), encoding="utf-8")
        deletion = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(planted_path)],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        self.assert_fail(self.repo.deletion(deletion), "missing-receipt: closure/closed/moved.go")
        self.assertEqual(self._gg13_snapshot(), snapshot)
        clean = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1, differences=[status],
        )
        clean["old_output"] = "reading=230\nreading=230\nexecution_status=0\n"
        clean["new_output"] = "reading=230\nreading=230\nexecution_status=1\n"
        self.assert_ok(self.repo.receipt("repeat-fields", clean, self.repo.dest, "ebusgo"))
        self.assertEqual(self.repo.manifest("repeat-fields")["receipts"][0]["outcome"], "approved-difference")

    def test_status_approval_stays_inside_its_case(self) -> None:
        status_difference = {
            "case": "case-A",
            "field": "execution_status",
            "old_present": True,
            "old": "0",
            "new": "1",
        }
        spec = self.repo.base(
            "status-scope",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[self.repo.difference("vec/diff-status-case-a.json")],
        )
        self.assert_ok(self.repo.generate(spec))
        path = self.repo.manifest_path("status-scope")
        original = path.read_bytes()
        crossed = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            differences=[status_difference],
        )
        crossed["case"] = "case-B"
        self.assert_fail(
            self.repo.receipt("status-scope", crossed, self.repo.dest, "ebusgo"),
            "unapproved-difference: execution_status",
        )
        self.assertEqual(path.read_bytes(), original)
        same = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            differences=[status_difference],
        )
        same["case"] = "case-A"
        self.assert_ok(self.repo.receipt("status-scope", same, self.repo.dest, "ebusgo"))
        self.assertEqual(self.repo.manifest("status-scope")["receipts"][0]["case"], "case-A")
        path.write_bytes(original)
        wildcard = self.repo.base(
            "status-wildcard-scope",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[self.repo.difference("vec/diff-status.json")],
        )
        self.assert_ok(self.repo.generate(wildcard))
        global_result = self.repo.result(
            "ebusgo", "row", self.repo.merged, old_status=0, new_status=1,
            differences=[{"case": "*", "field": "execution_status", "old_present": True, "old": "0", "new": "1"}],
        )
        global_result["case"] = "case-B"
        self.assert_ok(self.repo.receipt("status-wildcard-scope", global_result, self.repo.dest, "ebusgo"))
        self.assertEqual(self.repo.manifest("status-wildcard-scope")["receipts"][0]["case"], "case-B")
        planted = json.loads(original)
        planted["receipts"] = []
        for kind, commit in (("row", self.repo.merged), ("whole-session", self.repo.integrated)):
            planted["receipts"].append({
                "repository": "ebusgo",
                "kind": kind,
                "case": "case-B",
                "donor_sha": self.repo.sha,
                "destination_commit": commit,
                "old_status": 0,
                "new_status": 1,
                "old_output": "same",
                "new_output": "same",
                "differences": [status_difference],
                "compared": [],
                "outcome": "approved-difference",
            })
        planted_path = self.repo.root / "acceptance" / "manifests" / "status-scope-planted.json"
        planted_path.write_text(json.dumps(planted), encoding="utf-8")
        deletion = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(planted_path)],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        snapshot = self._gg13_snapshot()
        self.assert_fail(self.repo.deletion(deletion), "missing-receipt: closure/closed/moved.go")
        self.assertEqual(self._gg13_snapshot(), snapshot)

    def test_output_approval_stays_inside_its_case(self) -> None:
        northbound = {
            "case": "north",
            "field": "northbound",
            "old_present": False,
            "old": None,
            "new": "present",
        }
        spec = self.repo.base(
            "output-scope",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[self.repo.difference("vec/diff-north.json")],
        )
        self.assert_ok(self.repo.generate(spec))
        path = self.repo.manifest_path("output-scope")
        original = path.read_bytes()
        crossed = self.repo.result(
            "ebusgo", "row", self.repo.merged,
            output="kept=1",
            differences=[northbound],
        )
        crossed["case"] = "south"
        crossed["old_output"] = "kept=1"
        crossed["new_output"] = "kept=1\nnorthbound=present"
        self.assert_fail(
            self.repo.receipt("output-scope", crossed, self.repo.dest, "ebusgo"),
            "unapproved-difference: northbound",
        )
        self.assertEqual(path.read_bytes(), original)
        planted = json.loads(original)
        planted["receipts"] = []
        for kind, commit in (("row", self.repo.merged), ("whole-session", self.repo.integrated)):
            planted["receipts"].append({
                "repository": "ebusgo",
                "kind": kind,
                "case": "south",
                "donor_sha": self.repo.sha,
                "destination_commit": commit,
                "old_status": 0,
                "new_status": 0,
                "old_output": "kept=1",
                "new_output": "kept=1\nnorthbound=present",
                "differences": [northbound],
                "compared": [],
                "outcome": "approved-difference",
            })
        planted_path = self.repo.root / "acceptance" / "manifests" / "output-scope-planted.json"
        planted_path.write_text(json.dumps(planted), encoding="utf-8")
        deletion = {
            "row": "GG13",
            "donor_sha": self.repo.sha,
            "ledger_commit": self.repo.sha,
            "manifests": [str(planted_path)],
            "grants": [],
            "reserves": [],
            "live_inputs": [],
        }
        snapshot = self._gg13_snapshot()
        self.assert_fail(self.repo.deletion(deletion), "missing-receipt: closure/closed/moved.go")
        self.assertEqual(self._gg13_snapshot(), snapshot)
        same = self.repo.result(
            "ebusgo", "row", self.repo.merged,
            output="kept=1",
            differences=[northbound],
        )
        same["case"] = "north"
        same["old_output"] = "kept=1"
        same["new_output"] = "kept=1\nnorthbound=present"
        self.assert_ok(self.repo.receipt("output-scope", same, self.repo.dest, "ebusgo"))
        self.assertEqual(self.repo.manifest("output-scope")["receipts"][0]["case"], "north")
        wildcard = self.repo.base(
            "output-wildcard-scope",
            moves=[self.repo.move("closure/closed/moved.go", "engine/moved.go")],
            expected_differences=[self.repo.difference("vec/diff-north-any.json")],
        )
        self.assert_ok(self.repo.generate(wildcard))
        global_result = self.repo.result(
            "ebusgo", "row", self.repo.merged,
            output="kept=1",
            differences=[{
                "case": "*",
                "field": "northbound",
                "old_present": False,
                "old": None,
                "new": "present",
            }],
        )
        global_result["case"] = "south"
        global_result["old_output"] = "kept=1"
        global_result["new_output"] = "kept=1\nnorthbound=present"
        self.assert_ok(self.repo.receipt("output-wildcard-scope", global_result, self.repo.dest, "ebusgo"))
        self.assertEqual(self.repo.manifest("output-wildcard-scope")["receipts"][0]["case"], "south")

    def test_conflicting_reference_pins_are_rejected(self) -> None:
        meas_sig = self.repo.sig["measurement_rows.go"]
        selectors = selector_map(meas_sig, MEAS)
        agree = self.repo.base(
            "pin-agree",
            mapping_rows=[self.repo.pattern(
                "pin-row", "donor-backed", ["pin-case"], "pin-assert", meas_sig,
                EXEMPLARS["measurement_rows.go"], fill(meas_sig, MEAS),
                old_symbol="ReadMeas", bom="meas-reading",
            )],
            expectations=[self.repo.expectation(
                "pin-case", "donor-backed",
                [self.repo.bound("pin-row", "pin-assert", "TestEcho")],
                selectors,
                [
                    self.repo.ref("donor-output", "vec/meas.json"),
                    self.repo.ref("specification", "vec/meas.json"),
                ],
            )],
        )
        self.assert_ok(self.repo.generate(agree))
        self.assert_ok(self.repo.check("pin-agree"))
        agreed = self.repo.compare("pin-agree", self.repo.dest)
        self.assert_ok(agreed)
        self.assertIn("field=reading expected=230 observed=230", agreed.stdout)
        side = self.repo.root.parent / "pin-side"
        side.mkdir()
        git(side, "init", "-b", "main")
        payload = {"fields": {"reading": "231"}, "inputs": {}, "selectors": selectors}
        vector = side / "vec" / "reading-231.json"
        vector.parent.mkdir(parents=True)
        vector.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        git(side, "add", "-A")
        git(side, "commit", "-m", "reading pin")
        pin_sha = git_out(side, "rev-parse", "HEAD")
        git(self.repo.root, "fetch", str(side), "refs/heads/main:refs/pins/reading-231")
        conflict = self.repo.base(
            "pin-conflict",
            mapping_rows=[self.repo.pattern(
                "pin-row", "donor-backed", ["pin-case"], "pin-assert", meas_sig,
                EXEMPLARS["measurement_rows.go"], fill(meas_sig, MEAS),
                old_symbol="ReadMeas", bom="meas-reading",
            )],
            expectations=[self.repo.expectation(
                "pin-case", "donor-backed",
                [self.repo.bound("pin-row", "pin-assert", "TestEcho")],
                selectors,
                [
                    self.repo.ref("donor-output", "vec/meas.json"),
                    {
                        "role": "specification",
                        "repository": "docs-semantic",
                        "revision": pin_sha,
                        "path": "vec/reading-231.json",
                    },
                ],
            )],
        )
        self.assert_fail(self.repo.generate(conflict), "conflicting-pin: pin-case", "field: reading")
        self.assert_absent("pin-conflict")
        blob = subprocess.check_output(
            ["git", "-C", str(self.repo.root), "show", f"{pin_sha}:vec/reading-231.json"]
        )
        data = json.loads(blob)
        edited = self.repo.manifest("pin-agree")
        edited["expectations"][0]["references"].append({
            "role": "specification",
            "repository": "docs-semantic",
            "revision": pin_sha,
            "path": "vec/reading-231.json",
            "blob_sha256": hashlib.sha256(blob).hexdigest(),
            "projection": {
                "fields": data.get("fields", {}),
                "inputs": data.get("inputs", {}),
                "selectors": data.get("selectors", {}),
            },
        })
        edited_path = self.repo.root / "acceptance" / "manifests" / "pin-conflict.json"
        edited_path.write_text(json.dumps(edited), encoding="utf-8")
        self.assert_fail(
            self.repo.check("pin-agree", manifest=edited_path),
            "conflicting-pin: pin-case",
            "field: reading",
        )
        compared = self.repo.compare("pin-agree", self.repo.dest, manifest=edited_path)
        self.assert_fail(compared, "conflicting-pin: pin-case", "field: reading")
        self.assertNotIn("expected=231", compared.stdout)
        self.assertNotIn("compare: ok", compared.stdout)

    def test_absence_approval_cannot_replace_a_pinned_baseline(self) -> None:
        meas_sig = self.repo.sig["measurement_rows.go"]
        selectors = selector_map(meas_sig, MEAS)
        vector = {
            "approval": "approved-transition",
            "case": "reading-case",
            "field": "reading",
            "new": "999",
            "old": None,
            "old_present": False,
            "source": "contradictory-approval",
        }
        side = self.repo.root.parent / "absence-side"
        side.mkdir()
        git(side, "init", "-b", "main")
        payload = side / "vec" / "diff-reading-absent.json"
        payload.parent.mkdir(parents=True)
        payload.write_text(json.dumps(vector, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        git(side, "add", "-A")
        git(side, "commit", "-m", "absence pin")
        pin_sha = git_out(side, "rev-parse", "HEAD")
        git(self.repo.root, "fetch", str(side), "refs/heads/main:refs/pins/reading-absent")
        rows = [self.repo.pattern(
            "reading-row", "donor-backed", ["reading-case"], "reading-assert", meas_sig,
            EXEMPLARS["measurement_rows.go"], fill(meas_sig, MEAS),
            old_symbol="ReadMeas", bom="meas-reading",
        )]
        expectations = [self.repo.expectation(
            "reading-case", "donor-backed",
            [self.repo.bound("reading-row", "reading-assert", "TestEcho")],
            selectors,
            [self.repo.ref("donor-output", "vec/meas.json")],
        )]
        contradictory = self.repo.base(
            "absence-contradiction",
            mapping_rows=rows,
            expectations=expectations,
            expected_differences=[{
                **vector,
                "repository": "docs-semantic",
                "revision": pin_sha,
                "path": "vec/diff-reading-absent.json",
            }],
        )
        self.assert_fail(
            self.repo.generate(contradictory),
            "contradictory-absence: reading-case",
            "field: reading",
        )
        self.assert_absent("absence-contradiction")
        baseline = self.repo.base(
            "absence-baseline",
            mapping_rows=rows,
            expectations=expectations,
        )
        self.assert_ok(self.repo.generate(baseline))
        agreed = self.repo.compare("absence-baseline", self.repo.dest)
        self.assert_ok(agreed)
        self.assertIn("field=reading expected=230 observed=230", agreed.stdout)
        blob = subprocess.check_output(
            ["git", "-C", str(self.repo.root), "show", f"{pin_sha}:vec/diff-reading-absent.json"]
        )
        edited = self.repo.manifest("absence-baseline")
        edited["expected_differences"] = [{
            **vector,
            "reference": {
                "role": "expected-difference",
                "repository": "docs-semantic",
                "revision": pin_sha,
                "path": "vec/diff-reading-absent.json",
                "blob_sha256": hashlib.sha256(blob).hexdigest(),
                "projection": json.loads(blob),
            },
        }]
        edited_path = self.repo.root / "acceptance" / "manifests" / "absence-planted.json"
        edited_path.write_text(json.dumps(edited), encoding="utf-8")
        before = self.repo.manifest_path("absence-baseline").read_bytes()
        planted_bytes = edited_path.read_bytes()
        self.assert_fail(
            self.repo.check("absence-baseline", manifest=edited_path),
            "contradictory-absence: reading-case",
            "field: reading",
        )
        planted = self.repo.private_dest()
        plant(planted, "approved-new", "reading=999\n")
        compared = self.repo.compare("absence-baseline", planted, manifest=edited_path)
        self.assert_fail(compared, "contradictory-absence: reading-case", "field: reading")
        self.assertNotIn("compare: ok", compared.stdout)
        self.assertNotIn("expected=absent observed=999", compared.stdout)
        self.assertNotIn("result=pass", compared.stdout)
        self.assertEqual(self.repo.manifest_path("absence-baseline").read_bytes(), before)
        self.assertEqual(edited_path.read_bytes(), planted_bytes)

    IB = "closure/cross/ib"
    IK = "closure/cross/ik"
    CLAUSE = "closure/cross/clause"
    PM = "closure/cross/pm"
    GQ = "closure/cross/gq"
    GR = "closure/cross/gr"
    FLOW = "closure/cross/flow"

    def test_a_raw_string_import_path_is_the_same_dependency(self) -> None:
        for package, label in ((self.IB, "raw-single"), (self.IK, "raw-group")):
            move = self.move_at(package, "Move")
            bare = self.repo.generate(self.symbol_spec(f"imp-{label}-bare", [move]))
            self.assert_fail(bare)
            self.assertEqual(bare.stdout, f"outside-set: {self.IC}.Count\n", label)
            self.assert_absent(f"imp-{label}-bare")
            both = self.repo.generate(
                self.symbol_spec(f"imp-{label}", [move, self.move_at(self.IC, "Count")])
            )
            self.assert_ok(both)
            self.assertEqual(
                {item["name"]: item["uses"] for item in self.repo.manifest(f"imp-{label}")["symbols"]},
                {"Move": [f"{self.IC}.Count"], "Count": []},
                label,
            )
            self.assert_ok(self.repo.check(f"imp-{label}"))

    def test_a_binding_of_one_select_clause_does_not_hide_the_sibling_clause(self) -> None:
        for name in ("Pick", "PickVar"):
            bare = self.repo.generate(self.symbol_spec(f"clause-{name}", [self.move_at(self.CLAUSE, name)]))
            self.assert_fail(bare)
            self.assertEqual(bare.stdout, "outside-set: Key\n", name)
            self.assert_absent(f"clause-{name}")
            declared = self.repo.generate(self.symbol_spec(
                f"clause-{name}-kept", [self.move_at(self.CLAUSE, name)],
                stay_symbols=[self.at(self.CLAUSE, "Key")],
            ))
            self.assert_ok(declared)
            self.assert_ok(self.repo.check(f"clause-{name}-kept"))

    def test_a_pointer_receiver_method_expression_is_a_dependency(self) -> None:
        move = self.move_at(self.PM, "Move")
        keep = self.at(self.PM, "T")
        open_method = self.repo.generate(self.symbol_spec("pm-open", [move], stay_symbols=[keep]))
        self.assert_fail(open_method)
        self.assertEqual(open_method.stdout, "outside-set: T.Method\n")
        self.assert_absent("pm-open")
        declared = self.repo.generate(
            self.symbol_spec("pm-kept", [move], stay_symbols=[keep, self.at(self.PM, "T.Method")])
        )
        self.assert_ok(declared)
        self.assert_ok(self.repo.check("pm-kept"))

    def test_a_field_key_of_a_qualified_generic_literal_is_not_a_use(self) -> None:
        move = self.move_at(self.GQ, "Move")
        closed = self.repo.generate(
            self.symbol_spec("gq-kept", [move], stay_symbols=[self.at(self.GR, "Record")])
        )
        self.assert_ok(closed)
        self.assert_ok(self.repo.check("gq-kept"))

    def test_an_assertion_of_a_value_assigned_from_a_moved_call_needs_a_destination(self) -> None:
        move = self.move_at(self.FLOW, "Moved")
        keep = [self.at(self.FLOW, "Host")]
        bare = self.repo.generate(self.symbol_spec("flow-bare", [move], stay_symbols=keep))
        self.assert_fail(
            bare,
            "unaccounted-assertion function=TestFlowAssigned assertion=assigned",
            "unaccounted-assertion function=TestFlowDeclared assertion=declared",
        )
        self.assertNotIn("assertion=host", bare.stdout)
        self.assertNotIn("TestFlowHost", bare.stdout)
        self.assert_absent("flow-bare")
        given = [
            {
                "function": function,
                "name": name,
                "destination_repository": "ebusgo",
                "destination_path": "dest/echo_test.go",
                "test": "TestEcho",
            }
            for function, name in (("TestFlowAssigned", "assigned"), ("TestFlowDeclared", "declared"))
        ]
        self.assert_ok(self.repo.generate(self.symbol_spec("flow-given", [move], stay_symbols=keep, assertions=given)))
        manifest = self.repo.manifest("flow-given")
        self.assertEqual(
            sorted((item["function"], item["name"]) for item in manifest["assertions"]),
            [("TestFlowAssigned", "assigned"), ("TestFlowDeclared", "declared")],
        )
        self.assert_ok(self.repo.check("flow-given"))

    def test_check_refuses_a_destination_entry_that_disagrees_with_the_assertion_record(self) -> None:
        spec = self.symbol_spec("agree-two", self.alpha_moves() + self.beta_moves(), assertions=self.clone_assertions())
        self.assert_ok(self.repo.generate(spec))
        self.assert_ok(self.repo.check("agree-two"))
        original = json.loads(self.repo.manifest_path("agree-two").read_text(encoding="utf-8"))
        path = self.repo.root / "acceptance" / "manifests" / "agree-two-mutated.json"
        for change in ({"test": "TestOther"}, {"path": "dest/unlisted_test.go"}, {"repository": "other"}):
            mutated = json.loads(json.dumps(original))
            entry = next(item for item in mutated["destinations"] if item["kind"] == "assertion")
            entry.update(change)
            path.write_text(json.dumps(mutated), encoding="utf-8")
            self.assert_fail(self.repo.check("agree-two", manifest=path), "assertions")


    def test_an_assertion_is_classified_from_the_binding_it_reads(self) -> None:
        move = self.move_at("closure/cross/shadow", "Moved")
        keep = [self.at("closure/cross/shadow", "Host"), self.at("closure/cross/shadow", "Other")]
        bare = self.repo.generate(self.symbol_spec("shadow-bare", [move], stay_symbols=keep))
        self.assert_fail(
            bare,
            "unaccounted-assertion function=TestShadowed assertion=outer",
            "unaccounted-assertion function=TestShadowedHeader assertion=after-header",
        )
        self.assertNotIn("assertion=host", bare.stdout)
        self.assertNotIn("assertion=header", bare.stdout)
        self.assert_absent("shadow-bare")
        given = [
            {
                "function": function,
                "name": name,
                "destination_repository": "ebusgo",
                "destination_path": "dest/echo_test.go",
                "test": "TestEcho",
            }
            for function, name in (("TestShadowed", "outer"), ("TestShadowedHeader", "after-header"))
        ]
        self.assert_ok(self.repo.generate(self.symbol_spec("shadow-given", [move], stay_symbols=keep, assertions=given)))
        self.assertEqual(
            sorted((item["function"], item["name"]) for item in self.repo.manifest("shadow-given")["assertions"]),
            [("TestShadowed", "outer"), ("TestShadowedHeader", "after-header")],
        )
        self.assert_ok(self.repo.check("shadow-given"))

    def test_a_raw_string_import_of_a_donor_test_is_accounted_like_a_quoted_one(self) -> None:
        move = self.move_at("closure/cross/rq", "Move")
        bare = self.repo.generate(self.symbol_spec("raw-test-bare", [move]))
        self.assert_fail(bare, "left-behind: TestQuoted", "left-behind: TestRaw")
        self.assert_absent("raw-test-bare")
        kept = self.repo.generate(
            self.symbol_spec("raw-test-kept", [move], specimens=["TestQuoted", "TestRaw"])
        )
        self.assert_ok(kept)
        self.assertEqual(
            sorted((item["kind"], item["name"]) for item in self.repo.manifest("raw-test-kept")["stays"]),
            [("specimen", "TestQuoted"), ("specimen", "TestRaw")],
        )
        self.assert_ok(self.repo.check("raw-test-kept"))

    def test_an_instantiated_receiver_expression_is_a_method_dependency(self) -> None:
        gm = "closure/cross/gm"
        for symbol, method in (("Move", "Method"), ("Plain", "Value")):
            open_method = self.repo.generate(
                self.symbol_spec(f"gm-{symbol}", [self.move_at(gm, symbol)], stay_symbols=[self.at(gm, "T")])
            )
            self.assert_fail(open_method)
            self.assertEqual(open_method.stdout, f"outside-set: T.{method}\n", symbol)
            self.assert_absent(f"gm-{symbol}")
            declared = self.repo.generate(self.symbol_spec(
                f"gm-{symbol}-kept", [self.move_at(gm, symbol)],
                stay_symbols=[self.at(gm, "T"), self.at(gm, f"T.{method}")],
            ))
            self.assert_ok(declared)
            self.assert_ok(self.repo.check(f"gm-{symbol}-kept"))

    def test_a_field_key_of_a_local_alias_of_a_qualified_struct_is_not_a_use(self) -> None:
        move = self.move_at("closure/cross/lq", "Move")
        closed = self.repo.generate(
            self.symbol_spec("lq-kept", [move], stay_symbols=[self.at("closure/cross/qb", "Box")])
        )
        self.assert_ok(closed)
        self.assertNotIn("outside-set", closed.stdout)
        self.assertEqual(
            {item["name"]: item["uses"] for item in self.repo.manifest("lq-kept")["symbols"]},
            {"Move": []},
        )
        self.assert_ok(self.repo.check("lq-kept"))

    def test_siblings_of_one_declaration_do_not_share_their_initializers(self) -> None:
        sib = "closure/cross/sib"
        first = self.repo.generate(self.symbol_spec("sib-a", [self.move_at(sib, "A")]))
        self.assert_ok(first)
        self.assertEqual(
            {item["name"]: item["uses"] for item in self.repo.manifest("sib-a")["symbols"]},
            {"A": []},
        )
        self.assert_ok(self.repo.check("sib-a"))
        second = self.repo.generate(self.symbol_spec("sib-b", [self.move_at(sib, "B")]))
        self.assert_fail(second)
        self.assertEqual(second.stdout, "outside-set: Helper\n")
        self.assert_absent("sib-b")
        shared = self.repo.generate(self.symbol_spec("sib-c", [self.move_at(sib, "C")]))
        self.assert_fail(shared)
        self.assertEqual(shared.stdout, "outside-set: pair\n")
        self.assert_absent("sib-c")

    TS = "closure/cross/ts"
    NL = "closure/cross/nl"
    QT = "closure/cross/qt"
    QM = "closure/cross/qm"
    HP = "closure/cross/hp"
    HQ = "closure/cross/hq"
    RB = "closure/cross/rb"
    UM = "closure/cross/um"
    GX = "closure/cross/gx"

    def given(self, function: str, name: str) -> list[dict]:
        return [{
            "function": function,
            "name": name,
            "destination_repository": "ebusgo",
            "destination_path": "dest/echo_test.go",
            "test": "TestEcho",
        }]

    def test_a_type_switch_case_type_is_a_dependency_but_its_binding_is_not(self) -> None:
        move = self.move_at(self.TS, "Move")
        opened = self.repo.generate(self.symbol_spec("ts-open", [move]))
        self.assert_fail(opened)
        self.assertEqual(opened.stdout, "outside-set: Item\n")
        self.assert_absent("ts-open")
        closed = self.repo.generate(self.symbol_spec("ts-stays", [move], stay_symbols=[self.at(self.TS, "Item")]))
        self.assert_ok(closed)
        self.assert_ok(self.repo.check("ts-stays"))

    def test_nested_literals_tell_map_keys_from_field_labels_at_each_level(self) -> None:
        item = [self.at(self.NL, "Item")]
        keyed = self.repo.generate(self.symbol_spec("nl-map", [self.move_at(self.NL, "Maps")], stay_symbols=item))
        self.assert_fail(keyed)
        self.assertEqual(keyed.stdout, "outside-set: K\n")
        self.assert_absent("nl-map")
        declared = self.repo.generate(
            self.symbol_spec("nl-map-stays", [self.move_at(self.NL, "Maps")], stay_symbols=item + [self.at(self.NL, "K")])
        )
        self.assert_ok(declared)
        labelled = self.repo.generate(self.symbol_spec("nl-field", [self.move_at(self.NL, "Fields")], stay_symbols=item))
        self.assert_ok(labelled)
        self.assertNotIn("outside-set", labelled.stdout)
        self.assert_ok(self.repo.check("nl-field"))

    def test_a_method_of_a_qualified_composite_literal_is_a_dependency(self) -> None:
        move = self.move_at(self.QM, "Move")
        only_type = self.repo.generate(
            self.symbol_spec("qm-type", [move], stay_symbols=[self.at(self.QT, "T")])
        )
        self.assert_fail(only_type)
        self.assertEqual(only_type.stdout, f"outside-set: {self.QT}.T.M\n")
        self.assert_absent("qm-type")
        both = self.repo.generate(self.symbol_spec(
            "qm-both", [move], stay_symbols=[self.at(self.QT, "T"), self.at(self.QT, "T.M")],
        ))
        self.assert_ok(both)
        self.assert_ok(self.repo.check("qm-both"))

    def test_method_expressions_of_generic_and_pointer_receivers_and_a_raw_string_import(self) -> None:
        move = self.move_at(self.GX, "Exprs")
        box = self.at(self.GX, "Box")
        opened = self.repo.generate(self.symbol_spec("gx-open", [move], stay_symbols=[box]))
        self.assert_fail(opened)
        self.assertEqual(
            opened.stdout,
            "outside-set: Box.Get\noutside-set: Box.Put\n"
            f"outside-set: {self.QT}.T\noutside-set: {self.QT}.T.M\n",
        )
        self.assert_absent("gx-open")
        stays = [
            box, self.at(self.GX, "Box.Get"), self.at(self.GX, "Box.Put"),
            self.at(self.QT, "T"), self.at(self.QT, "T.M"),
        ]
        self.assert_ok(self.repo.generate(self.symbol_spec("gx-stays", [move], stay_symbols=stays)))
        self.assert_ok(self.repo.check("gx-stays"))

    def test_a_donor_test_that_reaches_a_moved_symbol_through_a_helper_is_accounted(self) -> None:
        # The helper owns the import; the test file does not import the package.
        move = self.move_at(self.HP, "Moved")
        self.assert_ok(self.repo.generate(self.symbol_spec("helper-via", [move])))
        manifest = self.repo.manifest("helper-via")
        accounted = [
            (item["kind"], item["name"]) for item in manifest["stays"]
        ] + [("assertion", item["name"]) for item in manifest["assertions"]]
        self.assertIn(("test", "TestViaHelper"), accounted)
        self.assert_ok(self.repo.check("helper-via"))
        stripped = json.loads(self.repo.manifest_path("helper-via").read_text(encoding="utf-8"))
        stripped["stays"] = [item for item in stripped["stays"] if item["name"] != "TestViaHelper"]
        path = self.repo.root / "acceptance" / "manifests" / "helper-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("helper-via", manifest=path), "stays")

    def test_an_assignment_on_a_returning_branch_does_not_change_what_a_check_exercises(self) -> None:
        move = self.move_at(self.RB, "Moved")
        keep = [self.at(self.RB, "Stay")]
        bare = self.repo.generate(self.symbol_spec("branch-bare", [move], stay_symbols=keep))
        self.assert_fail(bare, "unaccounted-assertion function=TestBranch assertion=moved-result")
        self.assertNotIn("short-stay", bare.stdout)
        self.assert_absent("branch-bare")
        done = self.repo.generate(self.symbol_spec(
            "branch-given", [move], stay_symbols=keep, assertions=self.given("TestBranch", "moved-result"),
        ))
        self.assert_ok(done)
        manifest = self.repo.manifest("branch-given")
        self.assertEqual([item["name"] for item in manifest["assertions"]], ["moved-result"])
        self.assertEqual(
            [(item["kind"], item["name"]) for item in manifest["stays"] if item["kind"] != "symbol"],
            [("assertion", "short-stay")],
        )
        self.assert_ok(self.repo.check("branch-given"))

    def test_a_staying_dependency_in_a_package_the_input_does_not_name_keeps_a_test_mixed(self) -> None:
        move = self.move_at(self.UM, "Moved")
        bare = self.repo.generate(self.symbol_spec("unlisted-bare", [move]))
        self.assert_fail(bare, "unaccounted-assertion function=TestSeparate assertion=moved")
        self.assertNotIn("left-behind", bare.stdout)
        self.assert_absent("unlisted-bare")
        done = self.repo.generate(self.symbol_spec(
            "unlisted-given", [move], assertions=self.given("TestSeparate", "moved"),
        ))
        self.assert_ok(done)
        manifest = self.repo.manifest("unlisted-given")
        self.assertEqual([item["name"] for item in manifest["assertions"]], ["moved"])
        self.assertEqual([(item["kind"], item["name"]) for item in manifest["stays"]], [("assertion", "retained")])
        self.assert_ok(self.repo.check("unlisted-given"))

    def test_an_incomplete_symbol_destination_is_refused_before_anything_is_written(self) -> None:
        core = f"{self.ALPHA}/core.go"
        for label, repository, destination in (
            ("repository", "", "engine/records.go"),
            ("path", "ebusgo", ""),
        ):
            row = f"incomplete-{label}"
            move = self.repo.symbol(self.ALPHA, core, "Record", destination, repository=repository)
            self.assert_fail(
                self.repo.generate(self.symbol_spec(row, [move])),
                f"missing-destination symbol={self.ALPHA}:Record",
            )
            self.assert_absent(row)

    def test_conflicting_destinations_for_one_assertion_fail_in_either_order(self) -> None:
        moves = self.alpha_moves() + self.beta_moves()
        first, = self.clone_assertions()
        second = dict(first, test="TestOther")
        for label, given in (("forward", [first, second]), ("reverse", [second, first])):
            row = f"conflict-{label}"
            failed = self.repo.generate(self.symbol_spec(row, moves, assertions=given))
            self.assert_fail(failed, "conflicting-assertion function=TestStoreBehaviour assertion=clone-name")
            self.assert_absent(row)
        same = self.repo.generate(self.symbol_spec("conflict-same", moves, assertions=[first, dict(first)]))
        self.assert_ok(same)

    UE = "closure/cross/ue"
    AR = "closure/cross/ar"
    TM = "closure/cross/tm"
    TT = "closure/cross/tt"
    XI = "closure/cross/xi"
    SA = "closure/cross/sa"
    SB = "closure/cross/sb"
    FB = "closure/cross/fb"

    def test_an_unavailable_receiver_type_is_not_resolved_by_a_stay_declaration(self) -> None:
        move = self.move_at(self.UE, "Move")
        keep = self.at(self.UE, "T")
        for row, stays in (("ue-open", [keep]), ("ue-kept", [keep, self.at(self.UE, "T.M")])):
            blocked = self.repo.generate(self.symbol_spec(row, [move], stay_symbols=stays))
            self.assert_fail(blocked)
            self.assertEqual(blocked.stdout, f"unresolved-selector: {self.UE}/ue.go Move.M\n")
            self.assert_absent(row)

    def test_a_method_written_on_an_alias_is_a_sibling_of_the_moved_type(self) -> None:
        move = self.move_at(self.AR, "T")
        bare = self.repo.generate(self.symbol_spec("alias-open", [move]))
        self.assert_fail(bare)
        self.assertEqual(bare.stdout, "outside-set: T.M\n")
        self.assert_absent("alias-open")
        declared = self.repo.generate(
            self.symbol_spec("alias-kept", [move], stay_symbols=[self.at(self.AR, "T.M")])
        )
        self.assert_ok(declared)
        self.assert_ok(self.repo.check("alias-kept"))
        both = self.repo.generate(self.symbol_spec(
            "alias-moved", [move, self.move_at(self.AR, "T.M"), self.move_at(self.AR, "Alias")],
        ))
        self.assert_ok(both)
        self.assert_ok(self.repo.check("alias-moved"))

    def test_a_donor_test_that_reaches_a_moved_method_through_a_bridge_is_accounted(self) -> None:
        moves = [self.move_at(self.TM, "Recv"), self.move_at(self.TM, "Recv.M")]
        self.assert_ok(self.repo.generate(self.symbol_spec("bridge", moves)))
        manifest = self.repo.manifest("bridge")
        self.assertIn(("test", "TestBridged"), [(item["kind"], item["name"]) for item in manifest["stays"]])
        self.assert_ok(self.repo.check("bridge"))
        stripped = json.loads(self.repo.manifest_path("bridge").read_text(encoding="utf-8"))
        stripped["stays"] = [item for item in stripped["stays"] if item["name"] != "TestBridged"]
        path = self.repo.root / "acceptance" / "manifests" / "bridge-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("bridge", manifest=path), "stays")

    def test_an_external_test_package_symbol_keeps_its_package_in_the_closure(self) -> None:
        external = self.repo.symbol(self.XI, f"{self.XI}/xi_test.go", "F", "engine/m.go")
        bare = self.repo.generate(self.symbol_spec("xi-bare", [external]))
        self.assert_fail(bare)
        self.assertEqual(bare.stdout, "left-behind: TestExternal\n")
        self.assert_absent("xi-bare")
        kept = self.repo.generate(self.symbol_spec("xi-kept", [external], specimens=["TestExternal"]))
        self.assert_ok(kept)
        self.assert_ok(self.repo.check("xi-kept"))
        # The package F is another symbol: moving it leaves the external test alone.
        internal = self.move_at(self.XI, "F")
        self.assert_ok(self.repo.generate(self.symbol_spec("xi-base", [internal])))
        self.assertEqual(self.repo.manifest("xi-base")["stays"], [])
        self.assert_ok(self.repo.check("xi-base"))

    def test_a_test_that_stops_at_a_fatal_branch_gives_a_later_check_no_value_from_it(self) -> None:
        move = self.move_at(self.FB, "Moved")
        keep = [self.at(self.FB, "Stay")]
        bare = self.repo.generate(self.symbol_spec("fatal-bare", [move], stay_symbols=keep))
        self.assert_fail(bare, "unaccounted-assertion function=TestFatalBranch assertion=moved-result")
        self.assert_absent("fatal-bare")
        done = self.repo.generate(self.symbol_spec(
            "fatal-given", [move], stay_symbols=keep, assertions=self.given("TestFatalBranch", "moved-result"),
        ))
        self.assert_ok(done)
        self.assertEqual([item["name"] for item in self.repo.manifest("fatal-given")["assertions"]], ["moved-result"])
        self.assert_ok(self.repo.check("fatal-given"))

    def test_a_specimen_exempts_only_the_test_it_names(self) -> None:
        moves = [self.move_at(self.SA, "Moved"), self.move_at(self.SB, "Moved")]
        sa_test = {"name": "TestF", "file": f"{self.SA}/sa_test.go"}
        sb_test = {"name": "TestF", "file": f"{self.SB}/sb_test.go"}
        bare = self.repo.generate(self.symbol_spec("spec-bare", moves, specimens=["TestF"]))
        self.assert_fail(bare)
        self.assertEqual(bare.stdout, "ambiguous-specimen: TestF\n")
        self.assert_absent("spec-bare")
        one = self.repo.generate(self.symbol_spec("spec-one", moves, specimens=[sa_test]))
        self.assert_fail(one)
        self.assertEqual(one.stdout, "left-behind: TestF\n")
        self.assert_absent("spec-one")
        both = self.repo.generate(self.symbol_spec("spec-both", moves, specimens=[sa_test, sb_test]))
        self.assert_ok(both)
        self.assertEqual(
            sorted((item["file"], item["name"]) for item in self.repo.manifest("spec-both")["stays"] if item["kind"] == "specimen"),
            [(sa_test["file"], "TestF"), (sb_test["file"], "TestF")],
        )
        self.assert_ok(self.repo.check("spec-both"))
        stripped = json.loads(self.repo.manifest_path("spec-both").read_text(encoding="utf-8"))
        stripped["stays"] = [
            item for item in stripped["stays"]
            if not (item["kind"] == "specimen" and item["file"] == sb_test["file"])
        ]
        path = self.repo.root / "acceptance" / "manifests" / "spec-stripped.json"
        path.write_text(json.dumps(stripped), encoding="utf-8")
        self.assert_fail(self.repo.check("spec-both", manifest=path), "left-behind: TestF")

    def test_a_rename_that_check_would_read_as_no_name_is_refused_before_anything_is_written(self) -> None:
        core = f"{self.ALPHA}/core.go"
        for label, name in (("blank", " "), ("tab", "\t")):
            row = f"rename-{label}"
            move = self.repo.symbol(self.ALPHA, core, "Record", "engine/records.go", renamed=name)
            self.assert_fail(
                self.repo.generate(self.symbol_spec(row, [move])),
                f"invalid-destination-symbol symbol={self.ALPHA}:Record",
            )
            self.assert_absent(row)

    def test_pointer_write_requires_the_moved_assertion_but_keeps_the_host_check(self) -> None:
        directory = "closure/cross/ptr"
        move = self.move_at(directory, "Moved")
        bare = self.repo.generate(self.symbol_spec("ptr-bare", [move]))
        self.assert_fail(bare)
        names = ["indirect-value", "moved-value"]
        messages = [f"unaccounted-assertion function=TestPointerWrite assertion={name}" for name in names]
        self.assertEqual(sorted(bare.stdout.splitlines()), messages)
        self.assert_absent("ptr-bare")
        row = "ptr-given"
        self.assert_ok(self.repo.generate(self.symbol_spec(
            row, [move], assertions=[given for name in names for given in self.given("TestPointerWrite", name)],
        )))
        manifest = self.repo.manifest(row)
        self.assertEqual(sorted(entry["name"] for entry in manifest["assertions"]), names)
        self.assertEqual([entry["name"] for entry in manifest["stays"]], ["host-value"])
        self.assert_ok(self.repo.check(row))
        manifest["assertions"] = []
        manifest["destinations"] = [entry for entry in manifest["destinations"] if entry["kind"] != "assertion"]
        self.repo.write_json(f"acceptance/manifests/{row}.json", manifest)
        checked = self.repo.check(row)
        self.assert_fail(checked)
        self.assertEqual(sorted(checked.stdout.splitlines()), messages)

    def test_duplicate_moved_checks_in_one_function_cannot_share_one_binding(self) -> None:
        directory = "closure/cross/dup"
        spec = self.symbol_spec(
            "duplicated-check", [self.move_at(directory, "Moved"), self.move_at(self.DA, "MoveA")],
            assertions=[dict(self.given("TestBehaviour", "same")[0], package=pkg) for pkg in (directory, self.DA)]
            + self.given("TestOther", "same") + self.given("TestOther", "negative"),
        )
        blocked = self.repo.generate(spec)
        self.assert_fail(blocked)
        self.assertEqual(blocked.stdout.splitlines(), [
            f"ambiguous-assertion function=TestBehaviour assertion=same package={directory}",
        ])
        self.assert_absent("duplicated-check")

    def test_excluded_build_file_in_a_donor_test_is_reported(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="build-test-", dir=self.repo.root.parent)) / "donor"
        repo = Repo(root)
        repo.write("go.mod", "module example.test\n")
        repo.write("p/p.go", "package p\nfunc Moved() int { return 1 }\n")
        repo.write("other/unrelated_windows_test.go", "package other\n")
        git(root, "init", "-b", "main")
        git(root, "add", "-A")
        git(root, "commit", "-m", "fixture")
        repo.sha = git_out(root, "rev-parse", "HEAD")
        spec = repo.base("portable-test", symbol_moves=[repo.symbol("p", "p/p.go", "Moved", "out/ported.go")])
        self.assert_ok(repo.generate(spec))
        row = spec["row"]
        path = "q/portable_windows_test.go"
        repo.write(path, '''package q_test
import ("testing"; "example.test/p")
func TestPortable(t *testing.T) { if p.Moved() != 1 { t.Fatal("mismatch") } }
''')
        repo.write("p/tagged_test.go", "//go:build custom\n\npackage p\n")
        git(root, "add", "p/tagged_test.go", path)
        git(root, "commit", "-m", "build-constrained tests")
        repo.sha = git_out(root, "rev-parse", "HEAD")
        expected = ["unsupported-build-file: p/tagged_test.go", f"unsupported-build-file: {path}"]
        blocked = repo.generate({**spec, "row": "portable-blocked", "donor_sha": repo.sha})
        self.assert_fail(blocked)
        self.assertEqual(blocked.stdout.splitlines(), expected)
        self.assertFalse(list(repo.manifest_path(row).parent.glob("portable-blocked.*")))
        manifest = repo.manifest(row)
        manifest["donor"]["sha"] = repo.sha
        for entry in manifest["paths"]:
            entry["donor_sha"] = repo.sha
        repo.write_json(f"acceptance/manifests/{row}.json", manifest)
        checked = repo.check(row)
        self.assert_fail(checked)
        self.assertEqual(checked.stdout.splitlines(), expected)

    def test_unknown_receiver_does_not_guess_a_donor_method(self) -> None:
        directory = "closure/cross/opaque"
        blocked = self.repo.generate(self.symbol_spec("opaque-receiver", [self.move_at(directory, "External")]))
        self.assert_fail(blocked)
        self.assertEqual(blocked.stdout.splitlines(), [
            f"unresolved-selector: {directory}/opaque.go External.Read",
            f"unresolved-selector: {directory}/opaque.go External.Write",
        ])
        self.assert_absent("opaque-receiver")
        resolved = self.repo.generate(self.symbol_spec(
            "resolved-receiver", [self.move_at(directory, "Resolved")], stay_symbols=[self.at(directory, "Local")],
        ))
        self.assertEqual(resolved.stdout.splitlines(), ["outside-set: Local.Read"])


class DeclaredSymbolUsesTest(unittest.TestCase):
    """Uses are counted for declared package-level names only."""

    SOURCE = """package p

type Name string

type Zone struct {
	Name  string `json:"name"`
	Other Sibling
	hook  func(sibling int) error
}

type Sibling struct{ ID int }

type Reader interface {
	Read(sibling int) Sibling
	Embedded
}

type Embedded interface{}

var sibling = 3
var name = "x"

const (
	KeyA = "a"
	KeyB = "b"
)

func helper(name string) int { return len(name) }

func Generic[Sibling any](items []Sibling, fn func(name Sibling) Sibling) {}

func (zone *Zone) Describe(id int) string {
	err := helper("a")
	for index, value := range []int{1} {
		_ = index + value
	}
	if found, ok := table[KeyA]; ok {
		_ = found
	}
	built := Zone{Name: "a", Other: Sibling{ID: 2}}
	keyed := map[string]int{KeyB: 1}
	apply := func(sibling int) int { return sibling }
	switch kind := any(built).(type) {
	case Zone:
		_ = kind
	}
	_, _, _ = err, keyed, apply
	return zone.Name + name
}

func Late() int {
	value := sibling
	return value
}
"""

    def uses(self) -> dict[str, set[str]]:
        sys.path.insert(0, str(TOOL))
        try:
            import closure
        finally:
            sys.path.pop(0)
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "go.mod").write_text("module example.test\n", encoding="utf-8")
            (root / "p").mkdir()
            (root / "p" / "p.go").write_text(self.SOURCE, encoding="utf-8")
            git(root, "init", "-b", "main")
            git(root, "add", "-A")
            git(root, "commit", "-m", "fixture")
            with patch.dict(os.environ, tool_env()):
                report = closure.resolve_donor(root, "HEAD", ["p"])
        package = next(item for item in report["packages"] if item["dir"] == "p")
        return {
            item["key"]: {name for directory, name in item["uses"] if directory == "p"}
            for item in package["decls"]
        }

    def test_declarations_are_top_level_names_and_methods(self) -> None:
        self.assertEqual(
            sorted(self.uses()),
            [
                "Embedded", "Generic", "KeyA", "KeyB", "Late", "Name", "Reader",
                "Sibling", "Zone", "Zone.Describe", "helper", "name", "sibling",
            ],
        )

    def test_field_parameter_receiver_and_local_names_are_not_uses(self) -> None:
        uses = self.uses()
        self.assertEqual(uses["Zone"], {"Sibling"})
        self.assertEqual(uses["Reader"], {"Sibling", "Embedded"})
        self.assertEqual(uses["helper"], set())
        self.assertEqual(uses["Generic"], set())
        self.assertEqual(
            uses["Zone.Describe"],
            {"Zone", "Sibling", "KeyA", "KeyB", "helper", "name"},
        )

    def test_a_name_is_used_outside_the_scope_that_shadows_it(self) -> None:
        self.assertEqual(self.uses()["Late"], {"sibling"})


class ResolverRequiredTest(unittest.TestCase):
    """A symbol-level closure comes from the Go helper or not at all."""

    def donor(self, root: Path) -> None:
        (root / "go.mod").write_text("module example.test\n", encoding="utf-8")
        (root / "p").mkdir()
        (root / "p" / "p.go").write_text("package p\n\nfunc Moved() int { return 1 }\n", encoding="utf-8")
        git(root, "init", "-b", "main")
        git(root, "add", "-A")
        git(root, "commit", "-m", "fixture")

    def test_a_missing_go_toolchain_fails_and_does_not_read_the_source_another_way(self) -> None:
        sys.path.insert(0, str(TOOL))
        try:
            import closure
        finally:
            sys.path.pop(0)
        move = [{"package": "p", "path": "p/p.go", "symbol": "Moved"}]
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            self.donor(root)
            with patch.object(closure.shutil, "which", return_value=None):
                facts = closure.analyze_symbols(root, git_out(root, "rev-parse", "HEAD"), move, [])
            self.assertEqual(len(facts.errors), 1)
            self.assertTrue(facts.errors[0].startswith("go-resolver: "), facts.errors)
            self.assertEqual(facts.moved, [])
            with patch.dict(os.environ, tool_env()):
                facts = closure.analyze_symbols(root, git_out(root, "rev-parse", "HEAD"), move, [])
            self.assertEqual(facts.errors, [])
            self.assertEqual([item["name"] for item in facts.moved], ["Moved"])


class CompareTimeoutPolicyTest(unittest.TestCase):
    def test_long_destination_run_is_compared(self) -> None:
        """A destination run is not cut off, and its field result is kept."""
        if str(TOOL) not in sys.path:
            sys.path.insert(0, str(TOOL))
        import manifestlib

        calls: list[tuple[list[str], bool]] = []

        def fake_run(args, **kwargs):
            argv = [str(arg) for arg in args]
            calls.append((argv, "timeout" in kwargs))
            capped = "timeout" in kwargs or any(
                arg == "-timeout" or arg.startswith("-timeout=") for arg in argv
            )
            if capped:
                raise subprocess.TimeoutExpired(cmd=args, timeout=kwargs.get("timeout") or 60)
            env = kwargs.get("env") or {}
            test_name = ""
            if "-run" in argv:
                test_name = argv[argv.index("-run") + 1].strip("^$")
            case = env.get("MANIFEST_CASE", "")
            row = env.get("MANIFEST_ROW", "")
            assertion = env.get("MANIFEST_ASSERTION", "")
            stdout = (
                f"--- PASS: {test_name}\n"
                f"MANIFEST_RESULT case={case} row={row} assertion={assertion}\n"
                f"MANIFEST_INPUT raw={env.get('MANIFEST_RAW', '')} "
                f"qualifiers={env.get('MANIFEST_QUALIFIERS', '')} "
                f"clock={env.get('MANIFEST_CLOCK', '')} "
                f"state={env.get('MANIFEST_STATE', '')}\n"
                "MANIFEST_FIELD field=reading expected=230 observed=230\n"
            )
            return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

        def fake_reload(_tool, recorded):
            projection = recorded.get("projection")
            if not isinstance(projection, dict):
                return None, "unavailable: fixture"
            return projection, None

        inputs = {"raw": "aa", "qualifiers": "q", "clock": "t0", "state": "idle"}
        manifest = {
            "row": "slow-row",
            "expectations": [{
                "case": "slow-case",
                "kind": "donor-backed",
                "inputs": inputs,
                "references": [{
                    "role": "donor-output",
                    "projection": {"fields": {"reading": "230"}},
                }],
                "rows": [],
            }],
            "expected_differences": [],
            "assertions": [],
            "destinations": [
                {
                    "kind": "assertion",
                    "name": "moved-assert",
                    "function": "TestMovedReplay",
                    "test": "TestMovedReplay",
                    "path": "session/moved_test.go",
                },
                {
                    "kind": "case",
                    "case": "slow-case",
                    "row": "slow-row",
                    "assertion": "slow-assert",
                    "test": "TestSlowReplay",
                    "path": "session/replay_test.go",
                },
            ],
            "patterns": [],
        }
        with tempfile.TemporaryDirectory(prefix="qq06-long-run-") as directory:
            path = Path(directory) / "slow.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            buffer = io.StringIO()
            with ExitStack() as stack:
                stack.enter_context(patch.object(manifestlib.subprocess, "run", fake_run))
                stack.enter_context(patch.object(manifestlib, "_reload_reference", fake_reload))
                with redirect_stdout(buffer):
                    code = manifestlib.compare(path, Path(directory))
            text = buffer.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn("compare: ok", text)
        self.assertIn("assertion=moved-assert", text)
        self.assertIn("assertion=slow-assert", text)
        self.assertIn("result=pass", text)
        self.assertIn(
            "field assertion=slow-assert field=reading expected=230 observed=230",
            text,
        )
        self.assertFalse(any(line.startswith("timeout") for line in text.splitlines()), text)
        self.assertEqual(len(calls), 2, calls)
        invoked = []
        for argv, has_timeout in calls:
            self.assertFalse(has_timeout, argv)
            self.assertFalse(
                any(arg == "-timeout" or arg.startswith("-timeout=") for arg in argv),
                argv,
            )
            invoked.append(argv[argv.index("-run") + 1])
        self.assertEqual(invoked, ["^TestMovedReplay$", "^TestSlowReplay$"])
        readme = (TOOL / "README.md").read_text(encoding="utf-8")
        self.assertIn("go test -count=1 -v -run ^<TestName>$ <package>", readme)
        self.assertNotIn("-timeout", readme)


if __name__ == "__main__":
    unittest.main()
