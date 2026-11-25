"""Checks of the oracle checker itself: the SunSpec native records and the rebuild comparison of an untrimmed build.

Run: python3 -m pytest acceptance/oracle/test_oracle_checks.py -q -p no:cacheprovider
"""

import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check  # noqa: E402
import replay_session  # noqa: E402

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
    other_host = mutated(mutated(delivered, ".gopclntab", at=9), ".debug_line", at=3)
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
    other_host = mutated(mutated(delivered, ".gopclntab", at=9), ".debug_line", at=3)
    oracle, actual = build_tree(tmp_path, other_host, "go version go1.26.2 linux/amd64")
    monkeypatch.setattr(check, "HERE", oracle)
    assert check.compare_build("pre-port", actual) == []


def test_compare_build_rejects_an_untrimmed_rebuild_of_other_content(delivered, tmp_path, monkeypatch):
    oracle, actual = build_tree(tmp_path, mutated(delivered, ".strtab", at=3), "go version go1.26.2 linux/amd64")
    monkeypatch.setattr(check, "HERE", oracle)
    errors = check.compare_build("pre-port", actual)
    assert len(errors) == 1 and "path-free section .strtab differs" in errors[0]


@pytest.mark.parametrize("section", [".text", ".rodata", ".noptrdata", ".data"])
@pytest.mark.parametrize("delta", [1, -32])
def test_a_change_in_code_or_data_is_a_difference(delivered, section, delta):
    assert f"code or data section {section} differs" in check.untrimmed_differences(delivered, mutated(delivered, section, delta=delta, at=100))


def test_compare_build_rejects_an_untrimmed_rebuild_with_other_code(delivered, tmp_path, monkeypatch):
    oracle, actual = build_tree(tmp_path, mutated(delivered, ".text", at=100), "go version go1.26.2 linux/amd64")
    monkeypatch.setattr(check, "HERE", oracle)
    errors = check.compare_build("pre-port", actual)
    assert len(errors) == 1 and "code or data section .text differs" in errors[0]


def trimmed_tree(root, toolchain, **changes):
    entry = next(item for item in json.loads((HERE / "binaries.json").read_text(encoding="utf-8"))["binaries"] if item["id"] == "current-gateway")
    delivered_file = HERE / entry["file"]
    oracle = root / "oracle"
    (oracle / "binaries").mkdir(parents=True)
    (oracle / "bom").mkdir()
    shutil.copyfile(delivered_file, oracle / entry["file"])
    (oracle / "binaries.json").write_text(json.dumps({"binaries": [entry]}), encoding="utf-8")
    actual = root / "actual"
    (actual / "binaries").mkdir(parents=True)
    shutil.copyfile(delivered_file, actual / entry["file"])
    (actual / "binaries.json").write_text(json.dumps({"binaries": [dict(entry, toolchain=toolchain, **changes)]}), encoding="utf-8")
    return oracle, actual


def test_compare_build_accepts_a_byte_identical_trimmed_rebuild_on_another_host_platform(tmp_path, monkeypatch):
    oracle, actual = trimmed_tree(tmp_path, "go version go1.26.2 linux/amd64")
    monkeypatch.setattr(check, "HERE", oracle)
    assert check.compare_build("current", actual) == []


@pytest.mark.parametrize("toolchain,changes", [
    ("go version go1.26.3 linux/amd64", {}),
    ("go version go1.26.2 linux/amd64", {"note": "other"}),
    ("go version go1.26.2 linux/amd64", {"size": 1}),
])
def test_compare_build_still_rejects_a_trimmed_rebuild_with_other_version_or_metadata(tmp_path, monkeypatch, toolchain, changes):
    oracle, actual = trimmed_tree(tmp_path, toolchain, **changes)
    monkeypatch.setattr(check, "HERE", oracle)
    errors = check.compare_build("current", actual)
    assert len(errors) == 1 and "rebuilt manifest entry differs" in errors[0]


PROGRAM = """package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Println("hello", os.Args)
}
"""


def test_a_real_rebuild_under_other_host_paths_is_accepted_and_a_changed_text_is_not(tmp_path):
    go = shutil.which("go")
    if go is None:
        pytest.skip("no Go toolchain")
    root = subprocess.run([go, "env", "GOROOT"], stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
    built = []
    # The second build runs with a Go root and a source path of other lengths: the paths of another host, no -trimpath.
    for name, goroot in (("a", root), ("b" * 30, None)):
        source = tmp_path / name / "src"
        source.mkdir(parents=True)
        (source / "main.go").write_text(PROGRAM, encoding="utf-8")
        (source / "go.mod").write_text("module oracle\n\ngo 1.21\n", encoding="utf-8")
        if goroot is None:
            link = tmp_path / name / ("go-root-" + "r" * 40)
            link.symlink_to(root)
            goroot = str(link)
        env = dict(os.environ, GOROOT=goroot, GOCACHE=str(tmp_path / name / "cache"), GOOS="linux", GOARCH="amd64", CGO_ENABLED="0", GOWORK="off", GOFLAGS="", GOTOOLCHAIN="local")
        target = tmp_path / name / "out"
        subprocess.run([go, "build", "-o", str(target), "."], cwd=source, env=env, check=True)
        built.append(target.read_bytes())
    first, second = built
    assert first != second
    assert check.untrimmed_differences(first, second) == []
    assert "code or data section .text differs" in check.untrimmed_differences(first, mutated(second, ".text", at=100))


SESSIONS = HERE.parent / "vectors" / "current" / "sessions"
CLASSES = replay_session.CLASSES


def session_documents(toolchain, executable):
    session = {"session": "eebus-outbound-peer-request", "reference": "current"}
    item = {"slug_at_pin": "helianthus-ebusgateway", "commit": "0" * 40}
    harness = {"package": "cmd/gateway", "test": "TestOracleSessionEEBus"}
    classes = {name: [name] for name in CLASSES}
    return replay_session.documents(session, b"{}", item, harness, classes, toolchain, executable)


def test_the_session_output_does_not_depend_on_the_host_that_ran_it():
    darwin, darwin_provenance = session_documents("go version go1.26.2 darwin/arm64", "1" * 64)
    linux, linux_provenance = session_documents("go version go1.26.2 linux/amd64", "2" * 64)
    assert darwin == linux
    assert set(CLASSES) <= set(darwin) and "toolchain" not in darwin["build"] and "executable_sha256" not in darwin["build"]
    assert darwin_provenance != linux_provenance
    assert linux_provenance["build"]["toolchain"] == "go version go1.26.2 linux/amd64" and linux_provenance["build"]["executable_sha256"] == "2" * 64


@pytest.mark.parametrize("output", sorted(SESSIONS.rglob("output.json")), ids=lambda path: path.parent.name)
def test_a_committed_session_output_holds_no_host_specific_build_record(output):
    document = json.loads(output.read_text(encoding="utf-8"))
    assert set(document["build"]) == {"source", "label", "build_command", "invocation"}
    assert "darwin" not in output.read_text(encoding="utf-8") and "arm64" not in output.read_text(encoding="utf-8")
    provenance = json.loads((HERE / "provenance" / ("-".join(output.parent.relative_to(SESSIONS).parts) + ".json")).read_text(encoding="utf-8"))
    assert provenance["session_sha256"] == document["session_sha256"]
    assert {"toolchain", "executable_sha256"} <= set(provenance["build"])


BT01 = HERE.parent / "vectors" / "current" / "gateway"


def bt01_case(relative):
    return json.loads((BT01 / relative).read_text(encoding="utf-8"))


def test_the_two_self_echo_cases_differ_in_their_published_input():
    echo = bt01_case("engine/reconstructor/self-echo-parse-failure.json")
    plain = bt01_case("engine/reconstructor/self-echo-without-snapshotter.json")
    assert echo["input"]["bytes"] == plain["input"]["bytes"]
    assert echo["input"] != plain["input"]
    assert echo["input"]["state"]["local_address_snapshotter"] == {"installed": True, "address": "71", "known": True}
    assert plain["input"]["state"]["local_address_snapshotter"] == {"installed": False}
    assert (echo["output"]["counters"]["abandons_by_reason"], plain["output"]["counters"]["abandons_by_reason"]) == ({"self_echo": 1}, {"corrupted_request": 1})


def test_a_reconstructor_case_publishes_the_symbols_and_events_it_was_fed():
    reset = bt01_case("engine/reconstructor/reset.json")["input"]
    assert reset["qualifiers"]["tap_events_after_stream"] == [{"kind": "reset", "offset_from_start_ns": 100000000}]
    timeout = bt01_case("engine/reconstructor/read-timeout-watchdog.json")["input"]
    assert [event["offset_from_start_ns"] for event in timeout["qualifiers"]["tap_events_after_stream"]] == [100000000, 400000000]
    assert timeout["state"]["passive_transaction_watchdog_ns"] == 250000000
    direct = bt01_case("engine/reconstructor/direct.json")["input"]
    assert direct["qualifiers"]["fed_symbols"] == "aa" + direct["bytes"] and direct["clock"]["symbol_spacing_ns"] == 10000000


def test_the_b555_selector_cases_publish_their_arguments():
    axes = bt01_case("engine/watch-catalog/b555-axes.json")
    assert len(axes["input"]["qualifiers"]["keys"]) == len(axes["output"]["decisions"]) == 7
    assert bt01_case("engine/watch-catalog/builders.json")["input"]["qualifiers"]["calls"][2]["weekday"] == "06"


def test_the_local_worker_report_cases_publish_the_bytes_the_decoder_received():
    good = bt01_case("localworkerhost/report-round-trip.json")["input"]["bytes"]
    assert len(good) == 2 * 152
    corrupt = bt01_case("localworkerhost/report-corrupt-magic.json")
    assert corrupt["input"]["bytes"] != good and corrupt["input"]["state"]["encoded_original_hex"] == good
    assert len(bt01_case("localworkerhost/report-short.json")["input"]["bytes"]) == 2 * 151


def test_a_dropped_symbol_is_not_a_written_symbol():
    enforce = bt01_case("adaptermux/v8classifier/aa-injection-enforce.json")["output"]
    assert enforce["decisions"][0]["drop"] is True and enforce["symbols_written"] == []
    assert bt01_case("adaptermux/v8classifier/aa-injection-off.json")["output"]["symbols_written"] == ["aa"]


def test_an_arbitration_error_is_not_a_written_symbol():
    mismatch = bt01_case("adaptermux/transition/start_async--started_other_source.json")["output"]
    assert mismatch["symbols_written"] == []
    assert any(effect.startswith("result ") and ", error " in effect for effect in mismatch["decisions"][0]["effects"])
    assert "muxModelEffectResultError" in mismatch["decisions"][0]["effect_classes"]
    for path in sorted((BT01 / "adaptermux" / "transition").glob("*.json")):
        written = json.loads(path.read_text(encoding="utf-8"))["output"]["symbols_written"]
        assert all(set(symbol) <= set("0123456789abcdef") for symbol in written), path.name


GATEWAY_SOURCE_FIXTURES = {"gateway_awaiting_echo", "gateway_grace", "gateway_transaction", "start_async_gateway"}


def test_a_started_transition_publishes_the_source_byte_it_was_fed():
    paths = sorted((BT01 / "adaptermux" / "transition").glob("*--started_selected_source.json"))
    assert len(paths) == 13
    for path in paths:
        fixture = path.name.split("--")[0]
        expected = "7f" if fixture in GATEWAY_SOURCE_FIXTURES else "31"
        assert json.loads(path.read_text(encoding="utf-8"))["input"]["bytes"] == expected, path.name
    assert bt01_case("adaptermux/transition/idle--started_other_source.json")["input"]["bytes"] == "10"


def test_the_send_path_record_lists_the_symbols_the_upstream_received():
    document = bt01_case("adaptermux/send-path/write-normalization.json")
    assert document["output"]["symbols_written"] == ["a900", "a901", "aa", "a9", "a900", "a9", "a9", "aa"]
    assert document["input"]["bytes"] == "a9aaaaa9a9a9a9aa"
    first = document["output"]["decisions"][0]["sends"]
    assert [(step["session"], step["data"], step["structural"], step["upstream_writes"]) for step in first] == [
        (0, "a9", False, "a900"), (0, "aa", False, "a901"), (0, "aa", True, "aa"), (7, "a9", False, "a9")]
    assert [row["scenario"] for row in document["output"]["decisions"]] == [
        "enh-logical-both-ways", "ens-logical-both-ways", "raw-receive-side", "send-side-not-raw-symbol"]


def test_a_classifier_case_lists_the_symbols_it_forwards():
    for mode in ("off", "shadow", "enforce"):
        document = bt01_case(f"adaptermux/v8classifier/observe-idle-{mode}.json")
        drops = document["output"]["decisions"][0]["drop"]
        fed = [document["input"]["bytes"][index:index + 2] for index in range(0, len(document["input"]["bytes"]), 2)]
        assert document["output"]["symbols_written"] == [symbol for symbol, drop in zip(fed, drops) if not drop], mode
        assert document["output"]["symbols_written"], mode


def test_the_serial_round_trip_runs_the_configured_serial_path_on_both_ports():
    document = bt01_case("adaptermux/ptytest/pair-roundtrip.json")
    assert "TestSerialConn_ENSFramingPassesThrough" in document["stimulus"]
    assert len(document["input"]["bytes"]) == 256 * 2 * 2 and document["output"]["counters"]["receive_symbols"] == {"poller": 256, "retry": 256}
    decision = document["output"]["decisions"][0]
    assert [row["port"] for row in decision["receive"]] == [row["port"] for row in decision["send"]] == ["poller", "retry"]
    assert all(row["matches_stimulus"] for row in decision["receive"] + decision["send"])
    assert all(row["symbols"] == bytes(range(256)).hex() for row in decision["receive"])
    assert [row["peer_read"] for row in decision["send"]] == document["output"]["symbols_written"]
    assert all(row["peer_read"] == document["input"]["qualifiers"]["send_wire"] for row in decision["send"])


def test_a_local_worker_validation_case_publishes_the_operands_it_was_given():
    gogc = bt01_case("localworkerhost/validate-inherited-gogc.json")["input"]["state"]
    assert gogc["runtime_gc"] == "off" and gogc["environment"] == {"GOGC": "50", "GOMEMLIMIT": "64MiB"}
    assert bt01_case("localworkerhost/validate-inherited-gomemlimit.json")["input"]["state"]["environment"]["GOMEMLIMIT"] == "2GiB"
    positive = bt01_case("localworkerhost/validate-positive.json")["input"]["state"]
    assert positive["environment"] == {"GOGC": "off", "GOMEMLIMIT": "64MiB"} and positive["self"]["build_hex"] == positive["plan_build_hex"]
    assert [item["fd"] for item in bt01_case("localworkerhost/validate-control-fd.json")["input"]["state"]["observed"]] == [5, 4]
    assert len(bt01_case("localworkerhost/validate-missing-descriptor.json")["input"]["state"]["observed"]) == 1
    assert bt01_case("localworkerhost/validate-plan-build.json")["input"]["state"]["plan_build_hex"] != positive["self"]["build_hex"]


def test_an_argv_case_publishes_the_vector_the_parser_received():
    for name in ("flag-alone", "trailing-gateway-flag", "missing-field", "wrong-selector", "reordered-fields", "empty-gc"):
        state = bt01_case(f"localworkerhost/argv-{name}.json")["input"]["state"]
        assert len(state["args"]) == state["argc"], name
    assert bt01_case("localworkerhost/argv-flag-alone.json")["input"]["state"]["args"] == ["--internal-ebus-local-worker"]
    assert bt01_case("localworkerhost/argv-trailing-gateway-flag.json")["input"]["state"]["args"][-1] == "-matter-library-enabled"
    assert "gc=" in bt01_case("localworkerhost/argv-empty-gc.json")["input"]["state"]["args"]


def test_a_reconstructor_transaction_publishes_its_timing_markers_and_ack_correlation():
    direct = bt01_case("engine/reconstructor/direct.json")["output"]["observations"]
    assert len(direct) == 1
    assert direct[0]["timing"] == {
        "request_start": "1970-01-01T00:00:00.01Z", "request_end": "1970-01-01T00:00:00.07Z",
        "response_start": "1970-01-01T00:00:00.09Z", "response_end": "1970-01-01T00:00:00.12Z", "terminal": "1970-01-01T00:00:00.14Z"}
    assert direct[0]["ack_correlation"] == {"byte": "00", "position": "request_ack", "complete_request": True, "correlator": "M2A"}
    for path in sorted((BT01 / "engine" / "reconstructor").glob("*.json")):
        for event in json.loads(path.read_text(encoding="utf-8"))["output"]["observations"]:
            if "kind" in event:
                assert {"timing", "ack_correlation"} <= set(event), path.name


def test_the_pinned_budget_case_publishes_the_activations_that_exceed_the_budget():
    state = bt01_case("engine/shadow-cache/pinned-budget-reject.json")["input"]["state"]
    assert state["activation_source"] == "poller"
    assert state["activated_keys"] == state["catalog_keys"] == ["b509:08:0200", "b509:08:0201", "b509:08:0202"]
    assert len(state["activated_keys"]) > state["write_confirm_pinned_cap"]


FENCE_MUTATIONS = {
    "build": lambda report: report["build"] != report["executable"],
    "abi": lambda report: report["abi"] != 1,
    "future-worker": lambda report: report["generation"]["worker"] > 1,
    "descriptor-size": lambda report: [d["size"] for d in report["descriptors"]] == [152, 8192],
    "descriptor-missing": lambda report: len(report["descriptors"]) == 1,
    "state-not-passive": lambda report: report["state"] == 2,
    "tx-active": lambda report: report["tx_active"] is True,
    "ready-sequence": lambda report: report["sequence"] == 1,
    "unknown-kind": lambda report: report["kind"] == 9,
}


@pytest.mark.parametrize("name", sorted(FENCE_MUTATIONS))
def test_a_report_fence_case_publishes_the_report_that_was_submitted(name):
    case = bt01_case(f"localworkerhost/supervisor/observe-fence-{name}.json")
    report = case["input"]["state"]["report"]
    assert set(report) >= {"kind", "state", "tx_active", "sequence", "abi", "build", "executable", "generation", "descriptors"}
    assert FENCE_MUTATIONS[name](report), (name, report)
    assert case["input"]["state"]["layout"] != report["descriptors"] or name != "descriptor-size"


def test_a_classifier_sequence_case_publishes_the_event_stream_it_replays():
    case = bt01_case("adaptermux/v8classifier/sequence-telegram-lifecycle-enforce.json")
    events = case["input"]["state"]["events"]
    assert events == [
        {"event": "started", "value": "71", "escaped": False}, {"event": "byte", "value": "10", "escaped": False},
        {"event": "reset", "value": "00", "escaped": False}, {"event": "started", "value": "10", "escaped": False}]
    assert [(step["event"], step["value"], step["escaped"]) for step in case["output"]["decisions"]] == [
        (event["event"], event["value"], event["escaped"]) for event in events]
    for path in sorted((BT01 / "adaptermux" / "v8classifier").glob("sequence-*.json")):
        replayed = json.loads(path.read_text(encoding="utf-8"))
        assert replayed["input"]["state"]["events"], path.name


def test_the_serial_round_trip_writes_what_each_peer_read():
    case = bt01_case("adaptermux/ptytest/pair-roundtrip.json")
    sent = case["output"]["decisions"][0]["send"]
    assert [item["port"] for item in sent] == ["poller", "retry"]
    assert case["output"]["symbols_written"] == [item["peer_read"] for item in sent]
    assert case["output"]["counters"] == {
        "receive_symbols": {"poller": 256, "retry": 256}, "send_frames": {"poller": 7, "retry": 7}}


GATEWAY = HERE.parent / "vectors" / "current" / "gateway"


def bt01_case(relative):
    return json.loads((GATEWAY / relative).read_text(encoding="utf-8"))


def test_adaptermux_send_path_input_lists_each_scenario_and_its_ordered_sends():
    document = bt01_case("adaptermux/send-path/write-normalization.json")
    scenarios = document["input"]["qualifiers"]["scenarios"]
    assert [item["scenario"] for item in scenarios] == [row["scenario"] for row in document["output"]["decisions"]]
    first = scenarios[0]
    assert (first["protocol"], first["upstream_reads_logical"]) == ("enh", True)
    # Two consecutive aa bytes: the input alone says which one is payload and which one is structural.
    assert [(step["session"], step["data"], step["structural"]) for step in first["sends"]] == [(0, "a9", False), (0, "aa", False), (0, "aa", True), (7, "a9", False)]
    assert scenarios[2]["upstream_reads_logical"] is False
    assert scenarios[3]["protocol"] == "plain"
    for scenario, row in zip(scenarios, document["output"]["decisions"]):
        assert [(step["session"], step["data"], step["structural"]) for step in scenario["sends"]] == [(send["session"], send["data"], send["structural"]) for send in row["sends"]]


def test_watch_catalog_key_inputs_carry_each_request():
    b509 = bt01_case("engine/watch-catalog/passive-b509-key.json")
    events = b509["input"]["state"]["events"]
    assert [item["opcode"] for item in events] == [row["opcode"] for row in b509["output"]["decisions"]] == ["0d", "29", "0e"]
    assert all(item["has_request"] and item["request"]["primary"] == "b5" and item["request"]["secondary"] == "09" and item["request"]["target"] == "08" for item in events)
    assert [item["request"]["data"] for item in events] == ["0d0200", "290200", "0e0200"]
    b524 = bt01_case("engine/watch-catalog/passive-b524-key.json")
    requests = {item["name"]: item["request"]["data"] for item in b524["input"]["state"]["events"]}
    assert requests == {"read": "060003011c00", "write": "020203011c00aa55"}


@pytest.mark.parametrize("name,responses", [
    ("b509-response-class", {"header": "290200", "value": "2902007f", "single": "7f", "empty": ""}),
    ("b524-response-class", {"header": "4201031c00", "value": "4201031c0055", "ambiguous": "4201041c0055"}),
])
def test_response_class_inputs_carry_each_response(name, responses):
    document = bt01_case(f"engine/observe-first-family-policy/{name}.json")
    operands = {item["name"]: item for item in document["input"]["state"]["responses"]}
    assert {key: item["response"]["data"] for key, item in operands.items()} == responses
    assert all(item["has_response"] and item["outcome"] == "success" and item["frame_type"] == "initiator_target" for item in operands.values())
    assert [row["name"] for row in document["output"]["decisions"]] == list(responses)
    assert document["input"]["qualifiers"]["request"]["primary"] == "b5"


def test_supervisor_readiness_inputs_distinguish_the_call_and_carry_the_report():
    deadline = bt01_case("localworkerhost/supervisor/lease-readiness-deadline.json")
    late = bt01_case("localworkerhost/supervisor/lease-late-readiness.json")
    assert deadline["input"] != late["input"]
    assert (deadline["input"]["qualifiers"]["call"], late["input"]["qualifiers"]["call"]) == ("Tick", "Observe")
    assert "report" not in deadline["input"]["state"]
    report = late["input"]["state"]["report"]
    assert (report["kind"], report["state"], report["tx_active"], report["sequence"]) == (1, 1, False, 0)
    assert report["descriptors"] and report["generation"] == {"worker": 1, "stream": 1, "registration": 1, "token": 1}


def test_passive_tap_reconnect_keeps_the_event_order():
    document = bt01_case("engine/passive-tap/reconnect.json")
    assert document["output"]["symbols_written"] == []
    assert [(event["kind"], event.get("symbol")) for event in document["output"]["observations"]] == [
        ("connected", None), ("symbol", "11"), ("disconnected", None), ("connected", None), ("symbol", "22"),
    ]


@pytest.mark.parametrize("name,entry", [
    ("stale-active-confirmed", "entry"), ("equal-timestamp-active-confirmed", "entry"), ("evict-oldest", "pinned"),
])
def test_shadow_cache_entries_keep_expiry_and_generation(name, entry):
    cache = bt01_case(f"engine/shadow-cache/{name}.json")["output"]["cache"][entry]
    for field in ("expires_at", "observed_at", "generation", "last_write_generation", "state", "confidence", "pinned"):
        assert field in cache
    assert cache["expires_at"] > cache["observed_at"]
    assert cache["generation"] >= 1
