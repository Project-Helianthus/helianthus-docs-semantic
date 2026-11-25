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
    assert set(document["build"]) - {"overlay"} == {"source", "label", "build_command", "invocation"}
    assert set(document["build"].get("overlay", {"module": 0, "changed_files": 0, "added_files": 0})) == {"module", "changed_files", "added_files"}
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


def test_send_path_rows_record_the_active_transport_escape_mode_apart_from_the_receive_flag():
    rows = {row["scenario"]: row for row in bt01_case("adaptermux/send-path/write-normalization.json")["output"]["decisions"]}
    # (upstream receive flag, caller-visible escape mode of the active transport)
    assert {name: (row["upstream_reads_logical"], row["active_transport_bytes_are_unescaped"]) for name, row in rows.items()} == {
        "enh-logical-both-ways": (True, True),
        "ens-logical-both-ways": (True, True),
        "raw-receive-side": (False, False),
        "send-side-not-raw-symbol": (True, False),
    }
    for row in rows.values():
        assert row["active_reads_are_logical"] == row["upstream_reads_logical"]


@pytest.mark.parametrize("mode,count", [("off", 100), ("shadow", 50), ("enforce", 25)])
def test_idle_classifier_cases_feed_the_pinned_consecutive_bytes(mode, count):
    document = bt01_case(f"adaptermux/v8classifier/observe-idle-{mode}.json")
    assert document["input"]["bytes"] == bytes(range(count)).hex()
    assert document["input"]["qualifiers"]["count"] == count
    assert len(document["output"]["decisions"][0]["drop"]) == count
    assert document["output"]["counters"]["observed_bytes_total"] == (0 if mode == "off" else count)
    assert document["output"]["counters"]["enforce_drops_applied_total"] == 0
    if mode == "enforce":
        # the idle byte 01 is forwarded, not dropped
        assert "01" in document["output"]["symbols_written"]


def test_b524_state_default_input_carries_the_request_and_observation_of_each_decision():
    document = bt01_case("engine/observe-first-family-policy/b524-state-default-requires-active-state-read.json")
    operands = {item["name"]: item for item in document["input"]["qualifiers"]["cases"]}
    rows = {row["name"]: row for row in document["output"]["decisions"]}
    assert list(operands) == list(rows)
    config, active = operands["config-descriptor"], operands["active-state-read"]
    # Same request and same observation state; the descriptor's semantic class decides the admission.
    assert config["request"] == active["request"] and config["observation"]["state"] == active["observation"]["state"] == "active"
    assert (config["observation"]["descriptor"]["semantic_class"], active["observation"]["descriptor"]["semantic_class"]) == ("config", "state")
    assert rows["config-descriptor"]["policy"]["direct_apply_policy"] == "never"
    assert rows["active-state-read"]["policy"]["direct_apply_policy"] == "state_default"
    assert operands["catalog-miss"]["observation"]["has_descriptor"] is False
    assert operands["write"]["request"]["secondary"] == "24" and operands["write"]["request"]["source"] == "10"
    assert document["input"]["bytes"] == "".join(item["request"]["data"] for item in operands.values())


def test_b509_descriptor_cases_publish_the_descriptor_each_decision_was_made_for():
    document = bt01_case("engine/observe-first-family-policy/b509-descriptor-admission.json")
    operands = {item["name"]: item for item in document["input"]["qualifiers"]["descriptors"]}
    assert list(operands) == [row["name"] for row in document["output"]["decisions"]]
    request_key = document["input"]["qualifiers"]["request_key"]
    # The matching and the mismatched key differ only in the published descriptor key.
    assert operands["state-default-admitted"]["descriptor"]["key"] == request_key
    assert operands["key-mismatch-refused"]["descriptor"]["key"] != request_key
    assert operands["class-policy-mismatch-refused"]["descriptor"]["semantic_class"] == "config"
    assert operands["never-refused"]["descriptor"]["direct_apply_policy"] == "never"
    assert operands["unknown-policy-refused"]["descriptor"]["direct_apply_policy"] == "unknown"


def test_the_runtime_observer_case_publishes_its_descriptor_and_release_time():
    document = bt01_case("engine/deduplicator/b524-runtime-observer-fallback.json")
    observer = document["input"]["state"]["watch_observer"]
    assert (observer["state"], observer["has_descriptor"]) == ("active", True)
    assert observer["descriptor"]["semantic_class"] == "state" and observer["descriptor"]["direct_apply_policy"] == "state_default"
    assert observer["descriptor"]["key"] == observer["canonical"] == document["input"]["qualifiers"]["canonical"]
    assert document["input"]["clock"]["release_offset_ns"] > document["input"]["clock"]["passive_offset_ns"]


@pytest.mark.parametrize("name", ["allocator", "launcher", "clock", "wrong-abi", "zero-build", "layout-order", "lease-ttl", "kill-grace", "empty-gc"])
def test_a_new_config_case_publishes_the_configuration_it_submitted(name):
    document = bt01_case(f"localworkerhost/new-config-{name}.json")
    config = document["input"]["state"]["config"]
    assert document["input"]["qualifiers"]["mutation"] == name
    expected = {
        "allocator": ("has_allocator", False), "launcher": ("has_launcher", False), "clock": ("has_clock", False),
        "wrong-abi": ("self", None), "zero-build": ("self", None), "layout-order": ("descriptors", [{"role": 2, "size": 4096}, {"role": 1, "size": 152}]),
        "lease-ttl": ("lease_ttl_ns", config["lease_interval_ns"]), "kill-grace": ("kill_grace_ns", 0), "empty-gc": ("runtime_gc", ""),
    }[name]
    if name == "wrong-abi":
        assert config["self"]["abi"] != 1
    elif name == "zero-build":
        assert config["self"]["build_hex"] == "00" * 32
    else:
        assert config[expected[0]] == expected[1]


@pytest.mark.parametrize("mode", ["off", "shadow", "enforce"])
def test_the_classifier_fault_cascade_feeds_the_pinned_continuation_and_recovery(mode):
    document = bt01_case(f"adaptermux/v8classifier/sequence-protocol-fault-cascade-{mode}.json")
    # Header, the NN fault byte, the five continuation bytes 00..04, then a reset and a plain byte.
    assert document["input"]["bytes"] == "10b516ff" + "0001020304" + "55"
    events = [step["event"] for step in document["input"]["state"]["events"]]
    assert events[-2:] == ["reset", "byte"]
    states = [step["fsm_state"] for step in document["output"]["decisions"]]
    if mode != "off":
        assert states[-3:] == ["ABORTED", "IDLE", "IDLE"]
        assert document["output"]["counters"]["fsm_protocol_fault_total"] == 6


def test_arbitration_rows_name_the_request_that_won_apart_from_its_session_and_initiator():
    document = bt01_case("adaptermux/arbitration/selection-ownerfalse-idletrue.json")
    rows = document["output"]["decisions"]
    # Two queued bids that look equal (same session and initiator) are told apart by request identity.
    equal_looking = [row for row in rows if row.startswith("ext=[s1:10,s1:10] gw=false mask=3 ")]
    assert equal_looking and all("win_id=" in row and "pend_ext_id=[" in row for row in rows)
    winners = {row.split("win_id=")[1].split(" ")[0] for row in rows if row.startswith("ext=[s1:10,s1:10] ")}
    assert {"x0", "x1"} <= winners
    # A selection of the second equal-looking bid is a different row from selecting the first.
    second = [row for row in rows if row.startswith("ext=[s1:10,s1:10] gw=false mask=2 ")]
    assert second and "win_id=x1" in second[0] and "pend_ext_id=[x0]" in second[0]


def test_the_reconnect_case_leaves_out_the_timing_dependent_read_timeouts_and_says_so():
    document = bt01_case("engine/passive-tap/reconnect.json")
    assert document["input"]["qualifiers"]["observations_exclude"] == ["read_timeout"]
    assert document["input"]["clock"]["read_timeout_ns"] < document["input"]["clock"]["absence_threshold_ns"]
    assert "read_timeout" not in [event["kind"] for event in document["output"]["observations"]]


def test_a_scheduler_cache_hit_returns_a_value_and_writes_no_symbol():
    document = bt01_case("engine/scheduler/watch-read-served-from-passive-shadow.json")
    assert document["output"]["symbols_written"] == []
    decision = document["output"]["decisions"][0]
    assert decision["returned_value"] == "ab" and decision["served_from_passive_shadow"] is True
    assert document["output"]["counters"]["fetch_calls"] == 0


@pytest.mark.parametrize("name", ["passive-first-then-active", "active-first-then-delayed-passive", "passive-fingerprint-shared-watch-key", "degraded-skips-active-suppression"])
def test_a_deduplicator_case_publishes_the_emitted_observation_with_its_timestamp(name):
    document = bt01_case(f"engine/deduplicator/{name}.json")
    event = document["output"]["decisions"][0]["event"]
    assert event["kind"] == document["output"]["decisions"][0]["event_kind"] == "transaction"
    assert event["observed_at"].endswith("Z") and event["observed_at"] != "0001-01-01T00:00:00Z"
    assert event["request"]["primary"] == "b5" and event["has_request"] and event["has_response"]


@pytest.mark.parametrize("name", ["coalesce", "cache-within-max-age", "refresh-after-max-age"])
def test_a_scheduler_get_case_reports_returned_values_apart_from_bus_writes(name):
    document = bt01_case(f"engine/scheduler/{name}.json")
    # The scheduler's Get only returns values from an injected fetch; it writes no symbol to a bus.
    assert document["output"]["symbols_written"] == []
    decision = document["output"]["decisions"][0]
    assert len(decision["returned_values"]) == len(decision["errors"]) == 2
    expected = {"coalesce": ["0102", "0102"], "cache-within-max-age": ["aa", "aa"], "refresh-after-max-age": ["01", "02"]}[name]
    assert decision["returned_values"] == expected


def test_the_shadow_eviction_case_publishes_the_activations_budgets_and_ordered_write_times():
    document = bt01_case("engine/shadow-cache/evict-oldest.json")
    state, qualifiers = document["input"]["state"], document["input"]["qualifiers"]
    assert (state["capacity"], state["pinned_capacity"], state["write_confirm_pinned_cap"]) == (2, 2, 1)
    activations = {item["source"]: item["keys"] for item in state["activations"]}
    assert activations["poller"] == [qualifiers["pinned"]]
    assert activations["tooling"] == state["catalog_keys"] == [qualifiers["pinned"], qualifiers["older"], qualifiers["newer"]]
    writes = state["writes"]
    assert [item["order"] for item in writes] == [1, 2, 3]
    assert [item["role"] for item in writes] == ["pinned", "older", "newer"]
    assert [item["observed_offset_ns"] for item in writes] == [0, 1000000000, 2000000000]
    assert "".join(item["value"] for item in writes) == document["input"]["bytes"]
    # Only the entry that no activation pins down for the poller and is oldest is evicted.
    assert [document["output"]["cache"][role]["present"] for role in ("pinned", "older", "newer")] == [True, False, True]


def test_the_b524_read_write_case_publishes_the_policy_operands_of_each_call():
    document = bt01_case("engine/observe-first-family-policy/b524-read-write.json")
    calls = document["input"]["state"]["calls"]
    decisions = document["output"]["decisions"]
    assert [call["order"] for call in calls] == [1, 2, 3, 4] and len(decisions) == len(calls)
    assert [call["response_class"] for call in calls] == ["value_bearing", "header_only", "header_only", "header_only"]
    assert [call["request"]["secondary"] for call in calls] == ["24"] * 4
    assert [call["request"]["data"][2:4] for call in calls] == ["00", "01", "01", "01"]
    assert calls[0]["flags"] == {"constructor": "DefaultObserveFirstFeatureFlags"}
    # The runtime policy each write is made under comes from its input, not from the expected decision.
    assert [call["flags"]["external_write_policy"] for call in calls[1:]] == ["invalidate_only", "record_only", "record_and_invalidate"]
    assert [row["effective_external_write_policy"] for row in decisions[1:]] == [call["flags"]["external_write_policy"] for call in calls[1:]]
    assert all(call["observation"]["state"] == "active" and call["observation"]["semantic_class"] == "state" for call in calls)


@pytest.mark.parametrize("name,channels", [
    ("passive-first-then-active", ["passive", "active"]),
    ("active-first-then-delayed-passive", ["active", "passive"]),
])
def test_a_deduplicator_match_case_publishes_both_submitted_events_with_their_frame_boundaries(name, channels):
    document = bt01_case(f"engine/deduplicator/{name}.json")
    submissions = document["input"]["state"]["submissions"]
    assert [item["channel"] for item in submissions] == channels
    fingerprint = document["output"]["decisions"][0]["fingerprint"]
    for item in submissions:
        assert item["has_request"] and item["has_response"] and item["frame_type"] == "initiator_target"
        assert (item["request"]["source"], item["request"]["target"], item["request"]["primary"], item["request"]["secondary"]) == ("31", "08", "b5", "09")
        # The fingerprint is built from the header fields and data of both frames, which the input now carries.
        request = item["request"]
        assert fingerprint["request"].startswith(request["source"] + request["target"] + request["primary"] + request["secondary"])
        assert request["data"] in fingerprint["request"] and item["response"]["data"] in fingerprint["response"]
        assert (item["response"]["source"], item["response"]["target"]) == ("08", "31")
    assert document["input"]["bytes"] == submissions[0]["request"]["data"] + submissions[0]["response"]["data"]
    assert document["input"]["state"]["submissions"][0]["request"] == submissions[1]["request"]


@pytest.mark.parametrize("name", ["passive-fingerprint-shared-watch-key", "degraded-skips-active-suppression", "discontinuity-flushes-pending", "critical-subscriber-overflow"])
def test_every_other_deduplicator_case_publishes_the_events_it_submitted(name):
    submissions = bt01_case(f"engine/deduplicator/{name}.json")["input"]["state"]["submissions"]
    assert submissions and all({"channel", "kind", "frame_type", "request"} <= set(item) for item in submissions)


def test_the_in_order_lease_case_publishes_the_starting_state_and_the_timed_call_sequence():
    document = bt01_case("localworkerhost/supervisor/lease-in-order.json")
    state, clock = document["input"]["state"], document["input"]["clock"]
    assert state["start"]["state"] == "ready" and state["start"]["ready_report"]["kind"] == 1
    schedule = state["schedule"]
    assert [step["call"] for step in schedule] == ["clock.Advance", "Observe", "Tick"] * 3
    # Each renewal comes after 900 ms, well past the 100 ms configured interval and inside the 1 s lease.
    advances = [step["advance_ns"] for step in schedule if step["call"] == "clock.Advance"]
    assert advances == [900000000] * 3 and clock["lease_interval_ns"] == 100000000 and advances[0] < clock["lease_ttl_ns"]
    reports = [step["report"] for step in schedule if step["call"] == "Observe"]
    assert [report["sequence"] for report in reports] == [1, 2, 3] and all(report["kind"] == 2 and report["tx_active"] is False for report in reports)
    assert [row["advance_ns"] for row in document["output"]["decisions"]] == advances


@pytest.mark.parametrize("name", ["b524-runtime-observer-fallback", "passive-fingerprint-shared-watch-key", "degraded-skips-active-suppression", "discontinuity-flushes-pending", "critical-subscriber-overflow"])
def test_a_deduplicator_case_that_forces_health_publishes_its_starting_state(name):
    state = bt01_case(f"engine/deduplicator/{name}.json")["input"]["state"]
    assert state["initial_health"].startswith("healthy: constructed degraded, then forced healthy")


def test_the_runtime_observer_fallback_case_publishes_the_active_and_passive_events_in_order():
    state = bt01_case("engine/deduplicator/b524-runtime-observer-fallback.json")["input"]["state"]
    active, passive = state["submissions"]
    assert (active["channel"], active["kind"], active["outcome"], active["submitted_offset_ns"]) == ("active", "attempt_complete", "success", 0)
    assert (passive["channel"], passive["observed_offset_ns"]) == ("passive", 100000000)
    assert active["request"]["source"] == "31" and passive["request"]["source"] == "10"
    assert active["response"]["data"] == passive["response"]["data"] == "4201031c0022"


def test_the_b516_policy_case_publishes_the_response_class_scope_and_observation_it_was_decided_for():
    document = bt01_case("engine/observe-first-family-policy/b516-energy-merge.json")
    call, = document["input"]["state"]["calls"]
    assert (call["scope"], call["response_class"], call["observation"]["state"], call["flags"]["constructor"]) == ("passive", "value_bearing", "catalog_miss", "DefaultObserveFirstFeatureFlags")
    assert (call["request"]["source"], call["request"]["target"], call["request"]["primary"], call["request"]["secondary"]) == ("15", "fe", "b5", "16")
    assert call["request"]["data"] == document["input"]["bytes"]


def test_the_f19c_case_publishes_the_target_operands_it_validated():
    document = bt01_case("engine/reconstructor/f19c-initiator-and-target.json")
    state = document["input"]["state"]
    assert state["target_operands"] == "08aaa9fe10" and state["initiator_operands"] == document["input"]["bytes"]
    assert [row["byte"] for row in document["output"]["observations"]] == [state["target_operands"][i:i + 2] for i in range(0, 10, 2)]


def test_the_widened_ttl_case_publishes_the_descriptor_it_was_checked_against():
    descriptor = bt01_case("engine/watch-catalog/widened-ttl.json")["input"]["state"]["descriptor"]
    assert (descriptor["semantic_class"], descriptor["freshness_profile"], descriptor["freshness_ttl_ns"]) == ("state", "state_slow", 121000000000)
    assert {"key", "decoder_id", "correlation_policy", "direct_apply_policy"} <= set(descriptor)


def test_the_circuit_breaker_case_publishes_the_call_schedule_and_the_fetch_behaviour():
    document = bt01_case("engine/scheduler/circuit-open-and-suppress.json")
    gets = document["input"]["state"]["gets"]
    assert [item["order"] for item in gets] == [1, 2, 3, 4, 5]
    # The clock moves by the cooldown before the fourth call, not before the third.
    assert [item["clock_offset_ns"] for item in gets] == [0, 0, 0, 15000000000, 15000000000]
    assert all(item["key"] == "k" and item["max_age_ns"] == 0 for item in gets)
    assert "read failed" in document["input"]["qualifiers"]["fetch_returns"]
    assert len(document["output"]["decisions"]) == len(gets)


def test_the_restart_case_publishes_each_stale_operation_with_the_generation_it_submits():
    document = bt01_case("localworkerhost/supervisor/restart-advances-every-epoch.json")
    operations = document["input"]["state"]["operations"]
    assert [item["order"] for item in operations] == list(range(1, len(operations) + 1))
    assert [item["call"] for item in operations] == ["PublishPlan", "Enqueue", "Restart", "Observe", "Observe"] + ["PublishPlan"] * 3 + ["Enqueue"] * 3 + ["PublishPlan", "PublishPlan", "Enqueue", "Drain"]
    before = document["input"]["state"]["generation_before"]
    after = document["output"]["decisions"][0]["status_after_restart"]["generation"]
    assert operations[3]["report"]["generation"] == before and operations[4]["report"]["generation"] == after
    # Each stale operation differs from the current generation in exactly one field, and each field once per call kind.
    def differing(item, keys):
        return [key for key in keys if item[key] != after[key]]
    assert [differing(item, ("worker", "stream", "registration")) for item in operations[5:8]] == [["worker"], ["stream"], ["registration"]]
    assert [differing(item, ("worker", "stream", "token")) for item in operations[8:11]] == [["worker"], ["stream"], ["token"]]
    assert [item["call"] for item in operations[11:14]] == ["PublishPlan", "PublishPlan", "Enqueue"]
    assert operations[11] == {**operations[12], "order": 12} and differing(operations[11], ("worker", "stream", "registration")) == []
    assert [row["name"] for row in document["output"]["decisions"][0]["stale"]] == ["old worker", "old stream", "old registration", "old worker", "old stream", "old token"]


MATTER_DIRECTORIES = {
    "projection.go": "current/gateway/matter/projection",
    "model161.go": "current/gateway/matter/model161",
    "feedv1": "current/gateway/matter-feedv1",
    "libraryhost": "current/gateway/matter-libraryhost",
}
MATTER_GOLDEN = "cmd/gateway/testdata/characterization/consumers/matter_feed.json"
VECTORS = HERE.parent / "vectors"


def matter_cases(directory):
    root = VECTORS / directory
    return sorted(path for path in root.glob("*/*") if path.is_dir()) if directory.endswith(("matter-feedv1", "matter-libraryhost")) else sorted(path for path in root.glob("*") if path.is_dir())


def case_stimuli(directory):
    return {json.loads((case / "input.json").read_text(encoding="utf-8"))["stimulus"].split("/")[0].split(" ")[0] for case in matter_cases(directory)}


def test_every_matter_case_has_an_input_file_and_an_output_file_that_name_the_same_case():
    seen = 0
    for directory in MATTER_DIRECTORIES.values():
        for case in matter_cases(directory):
            documents = {name: json.loads((case / name).read_text(encoding="utf-8")) for name in ("input.json", "output.json")}
            assert {path.name for path in case.iterdir()} == {"input.json", "output.json"}, case
            assert documents["input.json"]["format"] == "helianthus-oracle-qv08-input/1" and "input" in documents["input.json"]
            assert documents["output.json"]["format"] == "helianthus-oracle-qv08-output/1" and "output" in documents["output.json"]
            for key in ("case", "component", "source", "stimulus"):
                assert documents["input.json"][key] == documents["output.json"][key], (case, key)
            assert documents["input.json"]["case"].endswith(case.name)
            seen += 1
    assert seen > 0


def test_the_matter_cases_are_indexed_as_recorded_outputs_of_the_current_reference():
    entries = {entry["path"]: entry for entry in check.load_index()}
    for directory in MATTER_DIRECTORIES.values():
        for case in matter_cases(directory):
            for name in ("input.json", "output.json"):
                entry = entries[(case / name).relative_to(VECTORS).as_posix()]
                assert (entry["origin"], entry["reference"], entry["role"]) == ("recorded-current", "current", "expected-output")
                assert "--entry gateway" in entry["recorder"] and "--sources gateway-" in entry["recorder"]


# The tests of the pin that have offline inputs; each is the stimulus of at least one case.
PROJECTION_TESTS = {
    "TestManifestAndLedgerCoverPinnedMetadataExactlyOnce", "TestLedgerIsDeterministicAndDoesNotExposeOperations",
    "TestEVSEActiveCurrentUsesPinnedNumericTargetAndExactConversion", "TestEVSECurrentFailsClosedOnWrongUnitOrPrecision",
    "TestEvaluationEligibilityFailsClosedForStaleAndUnavailable", "TestCanonicalJSONIsDeterministicForEquivalentResult",
    "TestProjectEVSECurrentEndToEndAndContractPin", "TestProjectRejectsEvaluationCorrespondenceDrift",
    "TestProjectRejectsIneligibleQualityAndEvaluation", "TestProjectRejectsWrongDimensionUnitBoundsConflictAndAmbiguity",
    "TestProjectEligibilityReadsOnlyMappedKeysWithSeveralContributors", "TestMappedKeyNamesPackVersionAndFact",
}
MODEL161_TESTS = {
    "TestAA03TargetAndFullLedger", "TestAA03TargetAgreement", "TestAA03CanonicalValueAndReportAgreement", "TestAA03EvaluationJoins",
    "TestAA03SourceJoins", "TestAA03QualificationAndPrecision", "TestAA03EmptyAndPhaseControls", "TestAA03ReportAccountingAndCurrentMetadata",
    "TestAA03CurrentRowSourceDimensions", "TestAA03EmptyProjectionCurrentRowMustBeLedgerRow",
}
FEEDV1_TESTS = {
    "TestStandaloneConsumerLifecycleAndAdmission", "TestInputDetachmentAndStrictRejectionHaveNoInvoke", "TestConcurrentCaptureKeepsOneCursor",
    "TestStandaloneClientUsesOnlyPublicWireContract", "TestStandaloneClientReturnsTypedResyncForForeignAheadAndExpiredCursors",
    "TestSchemaKeepsPublicObjectsClosedAndMatchesWireMembers", "TestSchemaCorpusMatchesFeedWireValues", "TestSchemaEmbeddedPortalGeneration",
}


def test_every_offline_test_of_the_matter_packages_is_the_stimulus_of_a_case():
    assert PROJECTION_TESTS <= {name for name in case_stimuli(MATTER_DIRECTORIES["projection.go"])}
    assert MODEL161_TESTS <= case_stimuli(MATTER_DIRECTORIES["model161.go"])
    assert FEEDV1_TESTS <= case_stimuli(MATTER_DIRECTORIES["feedv1"])
    libraryhost = case_stimuli(MATTER_DIRECTORIES["libraryhost"])
    assert len(libraryhost) == 33 and all(name.startswith("TestAA17") for name in libraryhost)
    roster = {"TestAA03RosterPin", "TestAA03RosterPinRejectsDrift"}
    assert not roster & case_stimuli(MATTER_DIRECTORIES["model161.go"])


def golden_reference_errors(reference, goldens):
    """The reference of a case to the item 5 golden: the entry that lists it, its path and its sha256 must be that entry's."""
    listed = {item["path"]: item for item in goldens["files"]}
    errors = []
    if reference.get("index_entry") != "current/gateway-goldens.json":
        errors.append("index_entry")
    entry = listed.get(reference.get("path"))
    if entry is None:
        errors.append("path")
    elif entry["sha256"] != reference.get("sha256"):
        errors.append("sha256")
    return errors


def feed_golden_references():
    for case in matter_cases(MATTER_DIRECTORIES["feedv1"]):
        output = json.loads((case / "output.json").read_text(encoding="utf-8"))["output"]
        if "golden" in output:
            yield case, output["golden"]


def test_a_feed_case_that_names_the_matter_feed_golden_cites_its_entry_and_does_not_copy_it():
    goldens = json.loads((VECTORS / "current" / "gateway-goldens.json").read_text(encoding="utf-8"))
    assert MATTER_GOLDEN in {item["path"] for item in goldens["files"]}
    cited = list(feed_golden_references())
    assert cited
    for case, reference in cited:
        assert reference["path"] == MATTER_GOLDEN
        assert golden_reference_errors(reference, goldens) == [], case
    assert not [path for path in VECTORS.rglob("*") if path.name == "matter_feed.json"]


@pytest.mark.parametrize("field,value,expected", [
    ("index_entry", "current/other.json", "index_entry"),
    ("path", "cmd/gateway/testdata/characterization/consumers/other.json", "path"),
    ("sha256", "0" * 64, "sha256"),
])
def test_a_golden_reference_with_another_entry_path_or_digest_is_refused(field, value, expected):
    goldens = json.loads((VECTORS / "current" / "gateway-goldens.json").read_text(encoding="utf-8"))
    case, reference = next(feed_golden_references())
    assert golden_reference_errors({**reference, field: value}, goldens) == [expected]


def matter_case_document(directory, case, name):
    return json.loads((VECTORS / directory / case / name).read_text(encoding="utf-8"))


LIBRARYHOST = MATTER_DIRECTORIES["libraryhost"]
FEEDV1 = MATTER_DIRECTORIES["feedv1"]
RECORDERS = HERE / "recorders" / "go"


def test_the_disabled_restart_input_states_the_configuration_the_host_was_built_with():
    document = matter_case_document(LIBRARYHOST, "restart/disabled-host-stays-disabled", "input.json")
    assert document["input"]["configuration"]["enabled"] is False


def test_the_projector_case_input_holds_the_snapshot_and_evaluation_its_output_was_computed_from():
    case = "project/uses-the-projector"
    variant = matter_case_document(LIBRARYHOST, case, "input.json")["input"]["rig_variant"]
    assert variant["capture_snapshot"] and variant["capture_evaluation"]
    control = matter_case_document(LIBRARYHOST, case, "output.json")["output"]["observations"][0]
    assert control["step"] == "direct Project161 control" and "snapshot" not in control and "evaluation" not in control


@pytest.mark.parametrize("case", ["project/stop-withholds-in-flight-capture-returns-a-value", "project/stop-withholds-in-flight-capture-returns-its-cancellation"])
def test_an_in_flight_projection_records_that_its_result_was_withheld_and_not_only_its_error(case):
    observations = matter_case_document(LIBRARYHOST, case, "output.json")["output"]["observations"]
    step = next(item for item in observations if item["step"] == "in-flight Project")
    assert step["outcome"]["is_stale_callback"] is True
    assert step["result_is_zero"] is True and step["result"]["document"]["target_id"] == ""


def test_the_feed_lifecycle_keeps_the_wire_byte_distinction_the_donor_checks():
    output = matter_case_document(FEEDV1, "server/lifecycle-and-admission", "output.json")["output"]
    assert output["wire_checks"] == {"second_snapshot_bytes_equal_first": True, "stable_changes_contains_empty_changes_literal": True, "withdrawal_changes_contains_WITHDRAWN": True}
    for case in ("server/lifecycle-and-admission", "server/detachment-and-strict-rejection"):
        for response in matter_case_document(FEEDV1, case, "output.json")["output"]["responses"]:
            assert response["wire_body_length"] > 0 and len(response["wire_body_sha256"]) == 64, (case, response["step"])
    snapshots = output["responses"][:2]
    assert snapshots[0]["wire_body_sha256"] == snapshots[1]["wire_body_sha256"]


def test_the_hung_close_recorders_take_the_close_count_after_close_was_entered():
    source = (RECORDERS / "gateway-libraryhost" / "zz_oracle_libraryhost_cases_test.go").read_text(encoding="utf-8")
    assert source.count("waitForCloses(t, rig, 1)") == 2
    for case in ("cancel/hung-close-quarantines-within-budget", "cancel/partial-construction-hung-close"):
        step = matter_case_document(LIBRARYHOST, case, "output.json")["output"]["observations"][0]
        assert step["step"] == "Start" and step["counts"]["closes"] == 1


def bt01_entries():
    import run_all

    entries = check.load_index()
    groups = {}
    for package, sources, test, directory in run_all.BT01:
        groups[directory] = (package, sources, test, [e for e in entries if e["path"].startswith(directory + "/")])
    return groups


def test_every_bt01_index_command_parses_and_reaches_the_recording_step(monkeypatch):
    sys.path.insert(0, str(HERE / "recorders"))
    import gorun

    calls = []
    monkeypatch.setattr(gorun, "run", lambda *args: calls.append(args))
    for directory, (package, sources, test, entries) in bt01_entries().items():
        assert entries, directory
        for entry in entries:
            words = entry["recorder"].split()
            assert words[0] == "recorders/gorun.py"
            monkeypatch.setattr(sys, "argv", words)
            gorun.main()
            reference, entry_id, run_package, run_sources, run_test, output = calls[-1]
            assert (reference, entry_id, run_package, run_sources, run_test) == (entry["reference"], "gateway", package, sources, test), entry["path"]
            assert output == f".tmp/oracle-record/{sources}", entry["path"]


def test_the_bt01_index_commands_are_the_ones_run_all_emits():
    import run_all

    for package, sources, test, directory in run_all.BT01:
        expected = run_all.recorder_command(package, sources, test)
        for entry in bt01_entries()[directory][3]:
            assert entry["recorder"] == expected, entry["path"]


def test_the_bt01_manifest_tally_has_the_send_path_case_in_the_adaptermux_group():
    groups = bt01_entries()
    counts = {directory: len(item[3]) for directory, item in groups.items()}
    assert counts == {"current/gateway/adaptermux": 207, "current/gateway/localworkerhost": 97, "current/gateway/engine": 77}
    assert sum(counts.values()) == 381
    adaptermux = {entry["path"] for entry in groups["current/gateway/adaptermux"][3]}
    assert "current/gateway/adaptermux/send-path/write-normalization.json" in adaptermux


# CAN receive cases: the comparison of a collected actual tree with the frozen expectations of its platform partition.
import copy  # noqa: E402
import hashlib  # noqa: E402

import can_receive  # noqa: E402


def can_world(tmp_path, monkeypatch):
    """A scratch vectors tree with the six frozen cases, the entries that index them and a receipt builder for each platform."""
    vectors = tmp_path / "vectors"
    entries = []
    for platform, cases in can_receive.PARTITIONS.items():
        for case in cases:
            for name in can_receive.FILES:
                path = f"{can_receive.CASES_DIRECTORY}/{case}/{name}"
                data = json.dumps({"case": case, "file": name, "result": [1, 2]}, indent=2).encode() + b"\n"
                (vectors / path).parent.mkdir(parents=True, exist_ok=True)
                (vectors / path).write_bytes(data)
                entries.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "origin": "recorded-current", "reference": "current", "role": "expected-output",
                                "recorder": "check.py --record-can-native current", "case": case, "platform": platform})
    monkeypatch.setattr(check, "VECTORS", vectors)
    monkeypatch.setattr(can_receive, "oracle_revision", lambda: "a" * 40)
    sources = {platform: [{"path": path, "sha256": hashlib.sha256(path.encode()).hexdigest()} for path in can_receive.SOURCES[platform]] for platform in can_receive.PARTITIONS}
    monkeypatch.setattr(can_receive, "pinned_sources", lambda platform: copy.deepcopy(sources[platform]))
    pin = next(item for item in check.references()["current"]["entries"] if item["id"] == "gateway")["commit"]

    def tree(platform, root=None):
        root = root or tmp_path / f"actual-{platform}"
        for case in can_receive.PARTITIONS[platform]:
            for name in can_receive.FILES:
                target = root / "cases" / case / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((vectors / can_receive.CASES_DIRECTORY / case / name).read_bytes())
        linux = platform == "linux"
        receipt = {
            "format": can_receive.RECEIPT_FORMAT, "reference": "current", "platform": platform,
            "native": {"goos": "linux" if linux else "darwin", "goarch": "arm64", "hostos": "linux" if linux else "darwin", "hostarch": "arm64"},
            "cases": sorted(can_receive.PARTITIONS[platform]), "statuses": {"compile": 0, "run": 0}, "gateway_pin": pin, "oracle_revision": "a" * 40,
            "selected_pinned_files": sorted(Path(path).name for path in can_receive.SOURCES[platform]),
            "pinned_sources": copy.deepcopy(sources[platform]),
            "executable_sha256": "1" * 64, "recorder_sha256": can_receive.recorder_digest(), "index_sha256": can_receive.index_digest(entries),
        }
        (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        return root, receipt

    return vectors, entries, tree


def rewrite_receipt(root, change):
    document = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
    change(document)
    (root / "receipt.json").write_text(json.dumps(document), encoding="utf-8")


@pytest.mark.parametrize("platform", ["linux", "nonlinux"])
def test_a_matching_tree_passes(tmp_path, monkeypatch, platform):
    _vectors, entries, tree = can_world(tmp_path, monkeypatch)
    root, _receipt = tree(platform)
    assert check.verify_can_tree(platform, root, entries) == []


def test_an_absent_tree_fails(tmp_path, monkeypatch):
    _vectors, entries, _tree = can_world(tmp_path, monkeypatch)
    assert any("absent" in error for error in check.verify_can_tree("linux", tmp_path / "nothing", entries))


def test_a_tree_without_receipt_fails(tmp_path, monkeypatch):
    _vectors, entries, tree = can_world(tmp_path, monkeypatch)
    root, _receipt = tree("linux")
    (root / "receipt.json").rename(tmp_path / "moved.json")
    assert any("receipt.json is absent" in error for error in check.verify_can_tree("linux", root, entries))


@pytest.mark.parametrize("platform", ["linux", "nonlinux"])
def test_a_changed_case_fails(tmp_path, monkeypatch, platform):
    _vectors, entries, tree = can_world(tmp_path, monkeypatch)
    root, _receipt = tree(platform)
    case = can_receive.PARTITIONS[platform][0]
    target = root / "cases" / case / "expected.json"
    target.write_bytes(target.read_bytes().replace(b"2", b"3"))
    assert any(f"case {case}/expected.json differs" in error for error in check.verify_can_tree(platform, root, entries))


def test_a_missing_case_and_an_extra_case_and_an_extra_file_fail(tmp_path, monkeypatch):
    _vectors, entries, tree = can_world(tmp_path, monkeypatch)
    root, _receipt = tree("linux")
    shutil.move(str(root / "cases" / "linux-bms-receive"), str(tmp_path / "moved-case"))
    (root / "cases" / "nonlinux-bms-unsupported").mkdir()
    (root / "cases" / "linux-bms-identity-mismatch" / "extra.json").write_text("{}", encoding="utf-8")
    (root / "stray.json").write_text("{}", encoding="utf-8")
    errors = check.verify_can_tree("linux", root, entries)
    assert any("missing case linux-bms-receive" in error for error in errors)
    assert any("extra case nonlinux-bms-unsupported" in error for error in errors)
    assert any("linux-bms-identity-mismatch holds" in error for error in errors)
    assert any("not cases and receipt.json" in error for error in errors)


def test_a_swapped_platform_fails_in_both_directions(tmp_path, monkeypatch):
    _vectors, entries, tree = can_world(tmp_path, monkeypatch)
    linux, _receipt = tree("linux")
    nonlinux, _receipt = tree("nonlinux")
    assert any("receipt platform is 'linux'" in error for error in check.verify_can_tree("nonlinux", linux, entries))
    assert any("receipt platform is 'nonlinux'" in error for error in check.verify_can_tree("linux", nonlinux, entries))
    assert any("missing case" in error for error in check.verify_can_tree("linux", nonlinux, entries))


# Each receipt member is varied alone; the comment names the production mutation that the case catches.
RECEIPT_MUTATIONS = {
    "format": lambda d: d.update(format="other/1"),  # a receipt of another recorder revision is accepted
    "reference": lambda d: d.update(reference="released"),  # a receipt of another reference is accepted
    "platform": lambda d: d.update(platform="nonlinux"),  # the platform of a tree is not read from its receipt
    "goos is not linux on the linux tree": lambda d: d["native"].update(goos="darwin"),  # a non-Linux host stands in for the Linux partition
    "cross target": lambda d: d["native"].update(goarch="amd64"),  # a cross-compiled target is accepted as native
    "cases": lambda d: d.update(cases=d["cases"][:-1]),  # a receipt that lists fewer cases is accepted
    "compile status": lambda d: d["statuses"].update(compile=1),  # a failed compile is accepted
    "run status": lambda d: d["statuses"].update(run=1),  # a failed run is accepted
    "gateway pin": lambda d: d.update(gateway_pin="0" * 40),  # a receipt of an older pin is accepted
    "selected files": lambda d: d.update(selected_pinned_files=["growatt_bms_can_socketcan_unsupported.go"]),  # another branch of the opener is accepted
    "pinned sources": lambda d: d.update(pinned_sources=d["pinned_sources"][:1]),  # a receipt that omits a pinned source is accepted
    "recorder digest": lambda d: d.update(recorder_sha256="2" * 64),  # a receipt of another recorder revision is accepted
    "oracle revision": lambda d: d.update(oracle_revision="b" * 40),  # a receipt collected at an older revision of this repository is accepted
    "pinned source digest": lambda d: d["pinned_sources"][0].update(sha256="0" * 64),  # a receipt whose pinned source differs from the pin is accepted
    "oracle revision absent": lambda d: d.pop("oracle_revision"),  # a receipt that does not name its revision is accepted
    "native absent": lambda d: d.pop("native"),  # a receipt with no host or target metadata is accepted
    "index digest": lambda d: d.update(index_sha256="3" * 64),  # a receipt of another index revision is accepted
    "executable digest": lambda d: d.update(executable_sha256=""),  # a receipt with no executable digest is accepted
}


@pytest.mark.parametrize("name", sorted(RECEIPT_MUTATIONS))
def test_every_receipt_member_is_checked(tmp_path, monkeypatch, name):
    _vectors, entries, tree = can_world(tmp_path, monkeypatch)
    root, _receipt = tree("linux")
    rewrite_receipt(root, RECEIPT_MUTATIONS[name])
    assert check.verify_can_tree("linux", root, entries)


@pytest.mark.parametrize("change", [
    lambda d: d.pop("native"),  # both pairs of missing members compare equal
    lambda d: d.update(native={}),
    lambda d: d["native"].pop("hostos"),
    lambda d: d["native"].update(goarch="", hostarch=""),
    lambda d: d["native"].update(goos="linux", hostos="linux"),  # a Linux target stands in for the non-Linux partition
    lambda d: d["native"].update(hostos="linux"),  # a cross-compiled target
], ids=["no-native", "empty-native", "no-host", "empty-arch", "linux-target", "cross-target"])
def test_a_nonlinux_receipt_without_native_evidence_fails(tmp_path, monkeypatch, change):
    _vectors, entries, tree = can_world(tmp_path, monkeypatch)
    root, _receipt = tree("nonlinux")
    assert check.verify_can_tree("nonlinux", root, entries) == []
    rewrite_receipt(root, change)
    assert check.verify_can_tree("nonlinux", root, entries)


def test_the_index_digest_covers_the_whole_index(tmp_path, monkeypatch):
    _vectors, entries, _tree = can_world(tmp_path, monkeypatch)
    other = {"path": "current/other/vector.json", "sha256": "5" * 64, "origin": "recorded-current", "reference": "current", "role": "expected-output"}
    assert can_receive.index_digest(entries + [other]) != can_receive.index_digest(entries)


def test_the_project_reopen_recorder_serializes_the_interface_of_each_record():
    source = (HERE / "recorders" / "go" / "gateway-can-receive" / "zz_oracle_can_receive_linux_test.go").read_text(encoding="utf-8")
    assert '"record_interface": map[string]any{"name": record.Interface.Name(), "index": record.Interface.Index()}' in " ".join(source.split())


def test_the_project_reopen_input_serializes_the_raw_bytes_each_read_delivers():
    source = " ".join((HERE / "recorders" / "go" / "gateway-can-receive" / "zz_oracle_can_receive_linux_test.go").read_text(encoding="utf-8").split())
    assert '"read_bytes_hex": []any{hex.EncodeToString(stimulus), hex.EncodeToString(stimulus)}' in source
    assert "copy(buffer, stimulus)" in source and "buffer[4] = 8" not in source


INDEX_MUTATIONS = {
    "origin": lambda e: e.update(origin="synthetic"),
    "reference": lambda e: e.update(reference="released"),
    "role": lambda e: e.update(role="input"),
    "case": lambda e: e.update(case="other"),
    "platform": lambda e: e.update(platform="nonlinux" if e["platform"] == "linux" else "linux"),
    "sha256": lambda e: e.update(sha256="4" * 64),
}


@pytest.mark.parametrize("name", sorted(INDEX_MUTATIONS))
def test_every_index_member_of_a_case_is_checked(tmp_path, monkeypatch, name):
    _vectors, entries, _tree = can_world(tmp_path, monkeypatch)
    assert check.can_index_errors(entries) == []
    changed = copy.deepcopy(entries)
    INDEX_MUTATIONS[name](changed[0])
    assert check.can_index_errors(changed)


def test_a_missing_or_extra_index_entry_fails(tmp_path, monkeypatch):
    _vectors, entries, _tree = can_world(tmp_path, monkeypatch)
    assert any("not in index.json" in error for error in check.can_index_errors(entries[1:]))
    extra = entries + [dict(entries[0], path=f"{can_receive.CASES_DIRECTORY}/seventh/input.json")]
    assert any("outside the six cases" in error for error in check.can_index_errors(extra))


def refused_before_recording(monkeypatch, entries):
    monkeypatch.setattr(check, "load_index", lambda: entries)
    monkeypatch.setattr(check.can_receive, "native_platform", lambda: ("linux", {}))

    def recorder_must_not_run(*_args, **_kwargs):
        raise AssertionError("the recorder was invoked against an invalid common index")

    monkeypatch.setattr(check.subprocess, "run", recorder_must_not_run)
    return check.record_can_native("current")


def test_native_recording_refuses_a_duplicate_case_entry_before_the_recorder_runs(tmp_path, monkeypatch):
    _vectors, entries, _tree = can_world(tmp_path, monkeypatch)
    assert check.can_index_errors(entries + [dict(entries[0])]) == []  # the six-case check alone collapses a duplicate path
    errors = refused_before_recording(monkeypatch, entries + [dict(entries[0])])
    assert any("listed twice" in error for error in errors)


def test_native_recording_refuses_a_changed_non_can_payload_before_the_recorder_runs(tmp_path, monkeypatch):
    vectors, entries, _tree = can_world(tmp_path, monkeypatch)
    other = vectors / "current" / "other" / "vector.json"
    other.parent.mkdir(parents=True)
    other.write_bytes(b"{}\n")
    entry = {"path": "current/other/vector.json", "sha256": "5" * 64, "origin": "recorded-current", "reference": "current", "role": "expected-output",
             "recorder": "x"}
    errors = refused_before_recording(monkeypatch, entries + [entry])
    assert any("sha256 differs from index.json" in error for error in errors)


def test_the_index_digest_follows_every_entry_member(tmp_path, monkeypatch):
    _vectors, entries, _tree = can_world(tmp_path, monkeypatch)
    base = can_receive.index_digest(entries)
    for name, mutate in INDEX_MUTATIONS.items():
        changed = copy.deepcopy(entries)
        mutate(changed[0])
        assert can_receive.index_digest(changed) != base, name


MODBUS_SESSIONS = ("sunspec-first-incarnation", "sunspec-generation-replacement", "rs485-storage-first-incarnation", "gen3-managed-first-incarnation",
                   "gen3-managed-generation-replacement", "dongle-tcp", "logger-tcp")


@pytest.mark.parametrize("name", MODBUS_SESSIONS)
def test_a_modbus_session_is_indexed_as_input_and_expected_output_with_its_case(name):
    entries = {entry["path"]: entry for entry in check.load_index()}
    base = f"current/sessions/modbus/{name}"
    for file, role in (("session.json", "input"), ("output.json", "expected-output")):
        entry = entries[f"{base}/{file}"]
        assert (entry["role"], entry["reference"], entry["case"], entry["source_entry"]) == (role, "current", f"modbus/{name}", "gateway")
    session = json.loads((SESSIONS / "modbus" / name / "session.json").read_text(encoding="utf-8"))
    output = json.loads((SESSIONS / "modbus" / name / "output.json").read_text(encoding="utf-8"))
    assert session["scenario"] == name and output["session"] == session["session"]
    assert all(isinstance(output[group], list) for group in CLASSES)


def test_the_gen3_sessions_record_empty_acquisitions_and_sends_and_carry_the_raw_arm_as_stimulus():
    for name in ("gen3-managed-first-incarnation", "gen3-managed-generation-replacement"):
        session = json.loads((SESSIONS / "modbus" / name / "session.json").read_text(encoding="utf-8"))
        output = json.loads((SESSIONS / "modbus" / name / "output.json").read_text(encoding="utf-8"))
        assert output["acquisitions"] == [] and output["sends"] == []
        assert "none of these frames is a donor transmission" in session["input"]["raw_active_transport_arm"]["role"]


def test_the_exit_status_of_a_pin_without_a_runnable_operand_is_shared_by_the_runner_and_the_checker():
    assert check.NO_RUNNABLE_OPERAND == replay_session.NO_RUNNABLE_OPERAND == 3
