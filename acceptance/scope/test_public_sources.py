"""Scope cells cite a public source, not a private audit or plan locator."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_scope

SCOPE = Path(__file__).resolve().parent


def _rows(name):
    with (SCOPE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_private_locator_is_rejected():
    private = {
        "slice": "e-eebus",
        "key": "CEVC-sc1",
        "sources": "E/comparison.json CEVC-sc1; OPERATOR item 3",
    }
    assert check_scope.check_public_cells([private], "denominator")
    bare = {
        "slice": "f-modbus-can",
        "key": "huawei-dongle-logger/emma-power-30354-soc-30368",
        "uncertainty": "E/comparison linking ActivePower to the SOC word was not followed.",
    }
    assert check_scope.check_public_cells([bare], "denominator")
    audit = {
        "slice": "b-energy",
        "key": "MB-010",
        "uncertainty": "Audit 03 names FR03. Audit bundle is Brink 40xx.",
    }
    assert check_scope.check_public_cells([audit], "denominator")
    public = {
        "slice": "e-eebus",
        "key": "CEVC-sc1",
        "sources": "EVCharging 1.0.1; OPERATOR item 3",
    }
    assert check_scope.check_public_cells([public], "denominator") == []


def test_published_tables_cite_public_sources():
    for name in ("denominator.tsv", "second-vendor-unconfirmed.tsv"):
        assert check_scope.check_public_cells(_rows(name), name) == []


def test_cevc_sources_keep_the_specification():
    row = next(row for row in _rows("denominator.tsv") if row["slice"] == "e-eebus" and row["key"] == "CEVC-sc1")
    assert "comparison.json" not in row["sources"]
    assert "EVCharging 1.0.1" in row["sources"]
    assert "OPERATOR item 3" in row["sources"]
    assert row["qualification"] == "qualified"
    assert row["reason"] == "declared_by_specification"


def test_plan_association_is_not_a_source():
    row = next(row for row in _rows("denominator.tsv") if row["slice"] == "b-energy" and row["key"] == "MB-060")
    assert "→" not in row["sources"]
    assert "PB42" not in row["sources"]
    assert "modbusreg@" in row["sources"]


def test_notes_only_row_records_no_public_source():
    row = next(row for row in _rows("denominator.tsv") if row["key"] == "eebus.remote.opev_oscev")
    assert row["sources"] == "no public source"
    assert row["qualification"] != "qualified"
