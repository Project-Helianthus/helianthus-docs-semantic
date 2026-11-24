"""BatCapacity stays a gap when the only catalog facts are lifetime counters."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTE = ROOT / "acceptance" / "target-research" / "storage-pv-power.md"
INDEX = ROOT / "acceptance" / "target-research" / "README.md"


def _row(text: str, prefix: str) -> str:
    matches = [line for line in text.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, prefix
    return matches[0]


def _section(text: str, start: str, end: str) -> str:
    body = text.split(start, 1)[1].split(end, 1)[0]
    return body


def test_batcapacity_grade_records_lifetime_counter_loss():
    row = _row(NOTE.read_text(encoding="utf-8"), "| BatCapacity | attribute |")
    assert "`storage.capacity.charge` candidate" in row
    assert "`storage.capacity.discharge` candidate" in row
    assert "partial" not in row
    assert "pack_terminals_lifetime_counter" in row
    assert "cumulative" in row
    assert "Fixed" in row
    assert "no derivation" in row


def test_batcapacity_is_on_the_source_gap_list():
    note = NOTE.read_text(encoding="utf-8")
    gaps = _section(
        note,
        "## 4. Mandatory elements without a source",
        "## 5. Catalog elements",
    )
    assert _row(gaps, "| BatCapacity |")
    excluded = [
        sentence
        for line in gaps.splitlines()
        for sentence in line.split(". ")
        if "are not in this list" in sentence
    ]
    assert excluded
    assert all("BatCapacity" not in sentence for sentence in excluded)

    index = INDEX.read_text(encoding="utf-8")
    battery = _row(index, "**BatteryStorage**")
    added = [sentence for sentence in battery.split(". ") if "gap list adds" in sentence]
    assert len(added) == 1
    assert "BatCapacity" in added[0]
    excluded = [
        sentence
        for sentence in battery.split(". ")
        if "are not in the gap list" in sentence
    ]
    assert len(excluded) == 1
    assert "BatCapacity" not in excluded[0]
    gap_table = _section(
        index,
        "## Mandatory elements without a source",
        "## Catalog elements",
    )
    assert "| BatCapacity `" in gap_table or "| BatCapacity`" in gap_table
    composition = _row(index, "| Battery Storage ")
    assert "BatCapacity" in composition.split("|")[-2]
    assert (
        "`storage.capacity.charge` and `storage.capacity.discharge` candidate"
        in composition
    )
    assert (
        "`storage.capacity.charge` and `storage.capacity.discharge` partial"
        not in composition
    )
    grades = [
        line
        for line in index.splitlines()
        if line.startswith("| `storage.capacity.charge`, `storage.capacity.discharge` | ")
        and "| BatCapacity `0x0018`" in line
    ]
    assert len(grades) == 1
    grade = grades[0]
    assert "| candidate |" in grade
    assert "partial" not in grade
    assert "lifetime" in grade or "cumulative" in grade
