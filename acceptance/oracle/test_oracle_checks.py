"""Checks of the oracle checker itself: the SunSpec native records and the rebuild comparison of an untrimmed build.

Run: python3 -m pytest acceptance/oracle/test_oracle_checks.py -q -p no:cacheprovider
"""

import json
import shutil
import struct
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check  # noqa: E402

SUNSPEC = HERE.parent / "vectors" / "current" / "modbusreg" / "sunspec" / "ss02"
DELIVERED = HERE / "binaries" / "pre-port-gateway-linux-amd64"


@pytest.mark.parametrize("name", ["sunspec-103-w-1500-sf0", "sunspec-103-w-1234-sf-minus1", "sunspec-103-w-minus50-sf1"])
def test_admitted_sunspec_records_carry_state_and_event_values(name):
    document = json.loads((SUNSPEC / f"{name}.native.json").read_text(encoding="utf-8"))
    facts = {fact["field_id"]: fact for fact in document["output"]["facts"]}
    state = facts["inverter.operating_state"]
    assert (state["kind"], state["enum_number"], state["enum_symbol"]) == ("enum", 4, "MPPT")
    for field in ("inverter.events.1", "inverter.events.2"):
        assert (facts[field]["kind"], facts[field]["bits"], facts[field]["bit_symbols"]) == ("bitfield", 0, [])
    assert facts["inverter.ac.power.active"]["kind"] == "number"


def sections(data):
    shoff = struct.unpack_from("<Q", data, 0x28)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 0x3A)
    raw = [struct.unpack_from("<IIQQQQ", data, shoff + index * shentsize) for index in range(shnum)]
    base = raw[shstrndx][4]
    return {data[base + name:data.index(b"\0", base + name)].decode(): (offset, size) for name, _kind, _flags, _addr, offset, size in raw}


def mutated(data, section, delta=1, at=0):
    offset, _size = sections(data)[section]
    changed = bytearray(data)
    changed[offset + at] = (changed[offset + at] + delta) % 256
    return bytes(changed)


@pytest.fixture(scope="module")
def delivered():
    return DELIVERED.read_bytes()


def test_the_same_binary_has_no_difference(delivered):
    assert check.untrimmed_differences(delivered, delivered) == []


def test_host_dependent_paths_are_set_aside(delivered):
    other_host = mutated(mutated(mutated(delivered, ".rodata", at=5), ".gopclntab", at=9), ".debug_line", at=3)
    symtab_offset, _ = sections(delivered)[".symtab"]
    names = sections(delivered)[".strtab"]
    strtab = delivered[names[0]:names[0] + names[1]]
    goroot = strtab.index(b"runtime.defaultGOROOT.str\0")
    table = delivered[symtab_offset:symtab_offset + sections(delivered)[".symtab"][1]]
    for position in range(0, len(table), 24):
        if struct.unpack_from("<I", table, position)[0] == goroot:
            size_at = symtab_offset + position + 16
            break
    else:
        pytest.fail("the symbol of the Go root path is not in the symbol table")
    changed = bytearray(other_host)
    struct.pack_into("<Q", changed, size_at, struct.unpack_from("<Q", changed, size_at)[0] + 7)
    assert check.untrimmed_differences(delivered, bytes(changed)) == []


@pytest.mark.parametrize("section,expected", [(".strtab", "path-free section .strtab differs"), (".typelink", "path-free section .typelink differs")])
def test_a_change_in_a_path_free_section_is_a_difference(delivered, section, expected):
    assert expected in check.untrimmed_differences(delivered, mutated(delivered, section, at=3))


def test_a_changed_module_hash_is_a_difference(delivered):
    start, _size = sections(delivered)[".go.buildinfo"]
    marker = delivered.index(b"\th1:", delivered.index(b"dep\t", start)) + 4
    changed = bytearray(delivered)
    changed[marker] = ord("A") if changed[marker] != ord("A") else ord("B")
    assert "module graph, hashes or build settings differ" in check.untrimmed_differences(delivered, bytes(changed))


def test_a_changed_symbol_size_is_a_difference(delivered):
    offset, _ = sections(delivered)[".symtab"]
    changed = bytearray(delivered)
    position = offset + 24 * 40 + 16
    struct.pack_into("<Q", changed, position, struct.unpack_from("<Q", changed, position)[0] + 1)
    assert "symbol table differs" in check.untrimmed_differences(delivered, bytes(changed))


def build_tree(root, rebuilt_bytes, toolchain):
    entry = next(item for item in json.loads((HERE / "binaries.json").read_text(encoding="utf-8"))["binaries"] if item["id"] == "pre-port-gateway")
    oracle = root / "oracle"
    (oracle / "binaries").mkdir(parents=True)
    (oracle / "bom").mkdir()
    shutil.copyfile(DELIVERED, oracle / entry["file"])
    (oracle / "binaries.json").write_text(json.dumps({"binaries": [entry]}), encoding="utf-8")
    actual = root / "actual"
    (actual / "binaries").mkdir(parents=True)
    (actual / "binaries" / Path(entry["file"]).name).write_bytes(rebuilt_bytes)
    rebuilt_entry = dict(entry, sha256="0" * 64, size=len(rebuilt_bytes), toolchain=toolchain)
    (actual / "binaries.json").write_text(json.dumps({"binaries": [rebuilt_entry]}), encoding="utf-8")
    return oracle, actual


def test_compare_build_accepts_an_untrimmed_rebuild_on_another_host(delivered, tmp_path, monkeypatch):
    other_host = mutated(mutated(delivered, ".rodata", at=5), ".gopclntab", at=9)
    oracle, actual = build_tree(tmp_path, other_host, "go version go1.26.2 linux/amd64")
    monkeypatch.setattr(check, "HERE", oracle)
    assert check.compare_build("pre-port", actual) == []


def test_compare_build_rejects_an_untrimmed_rebuild_of_other_content(delivered, tmp_path, monkeypatch):
    oracle, actual = build_tree(tmp_path, mutated(delivered, ".strtab", at=3), "go version go1.26.2 linux/amd64")
    monkeypatch.setattr(check, "HERE", oracle)
    errors = check.compare_build("pre-port", actual)
    assert len(errors) == 1 and "path-free section .strtab differs" in errors[0]
