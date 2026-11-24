#!/usr/bin/env python3
"""Record gateway-goldens.json (item 5): path and sha256 of every pinned reference output, its checking test and the exit status at the pin."""

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

TREES = [
    "graphql/testdata/query_schema_introspection.golden.json",
    "graphql/testdata/register_derived_names.json",
    "docs/mcp-tool-inventory.md",
    "mcp/testdata/*.golden.json",
    "mcp/testdata/runtime_control_tools.json",
    "mcp/testdata/runtime_control_outputs.json",
    "mcp/testdata/runtime_control_characterization.json",
    "mcp/testdata/characterization/**",
    "mcp/testdata/semantic_snapshot.json",
    "mcp/testdata/runtime_control_recovery_contract.json",
    "mcp/testdata/issue1026_evse_decimal_0.canonical.json",
    "mcp/testdata/issue1026_evse_decimal_10.canonical.json",
    "mcp/testdata/issue1026_evse_decimal_18.canonical.json",
    "mcp/testdata/issue1026_evse_decimal_20.canonical.json",
    "mcp/testdata/issue1026_evse_decimal_30.canonical.json",
    "mcp/testdata/issue1026_evse_decimal_100.canonical.json",
    "mcp/ebusstandard/testdata/*.golden.json",
    "internal/matrix/testdata/full88-dryrun.golden",
    "internal/matrix/testdata/passive-dryrun.golden",
    "cmd/gateway/testdata/characterization/**",
    "cmd/gateway/testdata/vaillant_publication/**",
    "internal/modbusadapter/testdata/characterization/**",
    "m2mgraphql/testdata/semantic_pv_current.golden.json",
    "internal/semhub/testdata/scripted_event_stream.golden.json",
    "internal/coexistence/testdata/canonical/positive/report.json",
    "internal/coexistence/testdata/canonical/positive/evidence.json",
    "internal/coexistence/testdata/canonical/positive/live-public-status.json",
    "internal/candidatefacts/testdata/canonical/positive/graph.json",
    "internal/candidatefacts/testdata/canonical/positive/replay-result.json",
    "internal/candidatefacts/testdata/canonical/positive/source-terminal-graph.json",
    "internal/candidatefacts/testdata/canonical/positive/source-terminal-replay-result.json",
    "internal/candidatefacts/testdata/canonical/source/source-terminal-replay-result.json",
    "internal/candidatefacts/testdata/canonical/source/replay-result.json",
    "internal/candidatefacts/testdata/canonical/source/m625-source-replay.json",
    "internal/candidatefacts/testdata/canonical/source/m625-bundle.json",
    "internal/syncevidence/testdata/canonical/positive/replay-result.json",
    "internal/promotionlock/testdata/canonical/positive/result.json",
    "internal/promotionlock/testdata/canonical/positive/captured-runtime-zero-profile.json",
    "portal/catalogv1/testdata/**",
    "portal/contributionv1/testdata/**",
    "cmd/gateway/testdata/issue469_graphql_daemon_status.golden.json",
    "cmd/gateway/testdata/issue469_runtime_status.golden.json",
    "cmd/gateway/testdata/watch_summary_direct_apply_policy.golden.json",
    "cmd/gateway/testdata/huawei/**",
    "cmd/gateway/testdata/growatt_project_conformance.json",
    "docs/metrics-inventory.json",
]


def go(package, *tests):
    return [{"kind": "go-test", "package": package, "run": "|".join(tests)}]


def gw(*tests):
    return go("cmd/gateway", *tests)


def m(*tests):
    return go("mcp", *tests)


SERVER = "TestServer_ToolsCallChangedArgumentErrorsHaveStableEnvelopes"
CHECKERS = [
    ("graphql/testdata/query_schema_introspection.golden.json", go("graphql", "TestQuerySchemaMatchesIntrospectionGolden", "TestQuerySchemaIntrospectionGoldenRecordsTheDocument")),
    ("graphql/testdata/register_derived_names.json", go("graphql", "TestRegisterNamesFixtureIsConsistent", "TestGraphQLPublishesDocsEbusRegisterNames") + m("TestMCPPublishesDocsEbusRegisterNames") + go("portal", "TestPortalPublishesDocsEbusRegisterNames")),
    ("docs/mcp-tool-inventory.md", gw("TestMCPInventoryRegistrationCoverage") + m("TestMCPToolInventory", "TestNewServerKeepsPublicToolsListManifest")),
    ("mcp/testdata/bus_identification_evidence.golden.json", m("TestIdentificationEvidenceGoldenEnvelope")),
    ("mcp/testdata/bus_protocol_specimens_*.golden.json", m("TestProtocolSpecimensStableGoldens")),
    ("mcp/testdata/bus_summary_startup_reason.golden.json", m("TestBusSummaryStartupReasonGolden")),
    ("mcp/testdata/device_retained_*.golden.json", m("TestDeviceRetainedOriginGoldenEnvelopes")),
    ("mcp/testdata/device_zero_alias.golden.json", m("TestDeviceGetZeroAliasGoldenEnvelope")),
    ("mcp/testdata/growatt_protocol_ii_*.golden.json", m("TestGrowattProtocolIIV1GoldenToolsListAndCallEnvelope")),
    ("mcp/testdata/huawei_*.golden.json", m("TestH10NativeInstanceSchemaAndEnvelope")),
    ("mcp/testdata/modbus_v1_*.golden.json", []),
    ("mcp/testdata/rpc_invoke_malformed_allow_dangerous.golden.json", m("TestServer_ToolsCallInvokeV1MalformedArgumentReturnsStableEnvelope")),
    ("mcp/testdata/rpc_invoke_invalid_intent_precedes_lookup.golden.json", m("TestServer_ToolsCallInvokeV1InvalidIntentPrecedesRouteLookup")),
    ("mcp/testdata/legacy_invoke_*.golden.json", m(SERVER)),
    ("mcp/testdata/registry_*.golden.json", m(SERVER)),
    ("mcp/testdata/rpc_invoke_*.golden.json", m(SERVER)),
    ("mcp/testdata/runtime_status_regulator_capability.golden.json", m("TestRuntimeStatusRegulatorCapabilityGoldenAndFailClosed")),
    ("mcp/testdata/semantic_boiler_status_unknown.golden.json", m("TestSemanticBoilerStatusUnknownGoldenEnvelope")),
    ("mcp/testdata/semantic_circuits_state.golden.json", m("TestSemanticCircuitsStateGoldenEnvelope")),
    ("mcp/testdata/semantic_populated_planes.golden.json", m("TestSemanticPopulatedPlanesGoldenEnvelope")),
    ("mcp/testdata/semantic_snapshot_dhw_bivalence_bound.golden.json", m("TestSemanticSnapshotDHWBivalenceBoundGoldenEnvelope")),
    ("mcp/testdata/semantic_system_dhw_bivalence_bound.golden.json", m("TestSemanticSystemDHWBivalenceBoundGoldenEnvelope")),
    ("mcp/testdata/semantic_zones_dhw.golden.json", m("TestSemanticZonesAndDHWGoldenEnvelope")),
    ("mcp/testdata/vaillant_b503_errors_history_list.golden.json", m("TestVaillantB503PromotedToolsGolden")),
    ("mcp/testdata/vaillant_b503_live_monitor_session_get.golden.json", m("TestVaillantB503PromotedToolsGolden")),
    ("mcp/testdata/vaillant_b503_promoted_tools.golden.json", m("TestVaillantB503PromotedToolsGolden")),
    ("mcp/testdata/vaillant_b503_live_monitor_session_refreshing.golden.json", m("TestVaillantB503LiveMonitorSessionRefreshingGolden")),
    ("mcp/testdata/runtime_control_tools.json", m("TestRuntimeControlToolsGolden")),
    ("mcp/testdata/runtime_control_outputs.json", m("TestRuntimeControlOutputsGolden")),
    ("mcp/testdata/runtime_control_characterization.json", m("TestRuntimeControlCharacterizationMCPPayloads")),
    ("mcp/testdata/semantic_snapshot.json", m("TestM10DiscoveryGolden")),
    ("mcp/testdata/runtime_control_recovery_contract.json", m("TestRuntimeControlRecoveryMatchesTheContractFixtures")),
    ("mcp/testdata/issue1026_evse_decimal_*.canonical.json", m("TestTeslaGen3EVSESemanticCanonicalCurrentDecimals")),
    ("mcp/testdata/characterization/**", m("TestTeslaGen3EVSECharacterizationFirstIncarnationLegacyIdentityAndPublicBytes")),
    ("mcp/ebusstandard/testdata/command_get_alpha.golden.json", go("mcp/ebusstandard", "TestGolden_CommandGet")),
    ("mcp/ebusstandard/testdata/commands_list_pb03.golden.json", go("mcp/ebusstandard", "TestGolden_CommandsList")),
    ("mcp/ebusstandard/testdata/decode_alpha.golden.json", go("mcp/ebusstandard", "TestGolden_Decode")),
    ("mcp/ebusstandard/testdata/services_list.golden.json", go("mcp/ebusstandard", "TestGolden_ServicesList")),
    ("mcp/ebusstandard/testdata/forward_compat_synthetic_v1_1.golden.json", go("mcp/ebusstandard", "TestForwardCompat_UnknownEnumsParse")),
    ("mcp/ebusstandard/testdata/forward_compat_unknown_active_transport_v1_1.golden.json", go("mcp/ebusstandard", "TestForwardCompat_UnknownActiveTransport_GoldenParses", "TestForwardCompat_UnknownActiveTransport_ProducerEmits", "TestForwardCompat_UnknownActiveTransport_HashStable", "TestForwardCompat_UnknownActiveTransport_ConsumerFailsClosed")),
    ("internal/matrix/testdata/*", go("internal/matrix", "TestDryRunGoldenFull88AndPassiveUnchanged")),
    ("cmd/gateway/testdata/characterization/consumers/matter_feed.json", gw("TestMatterProfileCharacterizationFeed")),
    ("cmd/gateway/testdata/characterization/consumers/*", gw("TestCharacterizationConsumersOfAllThreeFamilies")),
    ("cmd/gateway/testdata/characterization/m2m/*", gw("TestCharacterizationM2MGraphQLOfAllThreeFamilies")),
    ("cmd/gateway/testdata/characterization/growatt_first_incarnation/*", gw("TestGrowattCharacterizationFirstIncarnationLegacyIdentityAndPublicBytes")),
    ("cmd/gateway/testdata/characterization/tesla_owner_first_incarnation/*", gw("TestTeslaCharacterizationOwnerFirstIncarnationLegacyIdentityAndPublicBytes")),
    ("cmd/gateway/testdata/characterization/tesla_successor/*", gw("TestTeslaHSCRetainedOwnerSuccessorFirstPublicationIsAcceptedOnTheRetainedKernel")),
    ("cmd/gateway/testdata/vaillant_publication/*", gw("TestVaillantPublicationGolden")),
    ("internal/modbusadapter/testdata/characterization/pv_first_incarnation/*", go("internal/modbusadapter", "TestPVCharacterizationFirstIncarnationLegacyIdentityAndCanonicalSnapshots")),
    ("internal/modbusadapter/testdata/characterization/pv_generation_replacement/*", go("internal/modbusadapter", "TestPVCharacterizationGenerationAndEpochReplacement")),
    ("m2mgraphql/testdata/semantic_pv_current.golden.json", go("m2mgraphql", "TestSemanticPVCurrentUsesOneEvaluatedProjection")),
    ("internal/semhub/testdata/scripted_event_stream.golden.json", go("internal/semhub", "TestScriptedEventStreamGolden")),
    ("internal/coexistence/testdata/canonical/positive/report.json", go("internal/coexistence", "TestMSP08ProductionHarnessConformance")),
    ("internal/coexistence/testdata/canonical/positive/evidence.json", go("internal/coexistence", "TestMSP08ProductionHarnessConformance")),
    ("internal/coexistence/testdata/canonical/positive/live-public-status.json", go("internal/coexistence", "^TestMSP08PublicStatusProjectionIsDeterministicAndMetadataClosed$")),
    ("internal/candidatefacts/testdata/canonical/positive/graph.json", go("internal/candidatefacts", "TestMSP07BuildVerifyReplayAreDeterministicAndCanonical")),
    ("internal/candidatefacts/testdata/canonical/positive/replay-result.json", go("internal/candidatefacts", "TestMSP07BuildVerifyReplayAreDeterministicAndCanonical")),
    ("internal/candidatefacts/testdata/canonical/positive/source-terminal-*.json", go("internal/candidatefacts", "TestMSP07SourceTerminalBuildVerifyReplayAreCanonical")),
    ("internal/candidatefacts/testdata/canonical/source/source-terminal-replay-result.json", go("internal/candidatefacts", "TestMSP07SourceTerminalBuildVerifyReplayAreCanonical")),
    ("internal/candidatefacts/testdata/canonical/source/replay-result.json", go("internal/coexistence", "^TestMSP08PinsExecutableV1ArtifactsAndM7Inputs$")),
    ("internal/candidatefacts/testdata/canonical/source/m625-*.json", go("internal/candidatefacts", "^TestMSP07RawFirstBuildConsumesM625PathsAndCloudObservation$")),
    ("internal/syncevidence/testdata/canonical/positive/replay-result.json", go("internal/syncevidence", "TestMSP065CanonicalFixturesPositiveReplayAndAllNegatives")),
    ("internal/promotionlock/testdata/canonical/positive/result.json", go("internal/promotionlock", "TestMSP085SyntheticConformanceRemainsCanonicalAndNonLive")),
    ("internal/promotionlock/testdata/canonical/positive/captured-runtime-zero-profile.json", go("internal/promotionlock", "^TestIssue1694DeclaredProfileCountsEighteenPromotedLeaves$")),
    ("portal/catalogv1/testdata/catalog-negative-vectors.json", []),
    ("portal/catalogv1/testdata/five-domain-catalog.json", go("portal/catalogv1", "TestCatalogSchemaClosesEveryPopulatedWireItem")),
    ("portal/contributionv1/testdata/state-matrix.json", [{"kind": "node-test", "file": "portal/web/test/portal-contribution-v1.test.mjs"}]),
    ("portal/contributionv1/testdata/invalid-manifests.json", go("portal/contributionv1", "TestInvalidManifestsFailClosed")),
    ("portal/contributionv1/testdata/five-domain-catalog.json", go("portal/contributionv1", "TestCanonicalDigestBoundsDirectManifestAndCanonicalizesUnorderedArrays", "TestCanonicalizePreservesExplicitEmptyRequiredArrays", "TestCanonicalizeSortsDefensivelyWithoutMutatingInput", "TestDecodeAcceptsSchemaValidIntegralOrderSpellings", "TestDecodeDistinguishesPresentZeroOrderFromMissingOrder")),
    ("cmd/gateway/testdata/issue469_graphql_daemon_status.golden.json", gw("TestIssue469GraphQLDaemonStatusMatchesMCPRuntimeStatus")),
    ("cmd/gateway/testdata/issue469_runtime_status.golden.json", gw("TestIssue469MCPRuntimeStatusSerializesCachedDaemonReleaseGolden")),
    ("cmd/gateway/testdata/watch_summary_direct_apply_policy.golden.json", gw("TestMCPWatchSummaryProviderAdapter_DirectApplyPolicyGoldenAndNormalizedFlagClasses")),
    ("cmd/gateway/testdata/huawei/*", gw("TestH10TCPProviderPVSnapshotParity", "TestH10MappingValuesAndWithheldFacts", "TestH10LostChildIdentityWithdrawsOnlyThatChild")),
    ("cmd/gateway/testdata/growatt_project_conformance.json", gw("TestCX22VoltageAndMemberDictionary", "TestCX22ComposedThreeFamiliesAndTwoProviderIsolation")),
    ("docs/metrics-inventory.json", [{"kind": "pytest", "file": "tests/test_metrics_inventory_docs.py", "test": "test_inventory_and_documentation"}]),
]

NO_CHECKER = {
    "mcp/testdata/modbus_v1_*.golden.json": "no test at the pin reads this file: the pinned tree names it nowhere outside its own testdata directory",
    "portal/catalogv1/testdata/catalog-negative-vectors.json": "the pin has no checker for this file (the pinned tree names it only in docs/architecture/naming-inventory.json)",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expand(source):
    found = set()
    for pattern in TREES:
        if pattern.endswith("/**"):
            base = source / pattern[:-3]
            found.update(p.relative_to(source).as_posix() for p in base.rglob("*") if p.is_file())
        elif any(c in pattern for c in "*?["):
            found.update(p.relative_to(source).as_posix() for p in source.glob(pattern) if p.is_file())
        else:
            if not (source / pattern).is_file():
                sys.exit(f"pinned file missing: {pattern}")
            found.add(pattern)
    return sorted(found)


def checkers_of(path):
    for pattern, checkers in CHECKERS:
        if fnmatch.fnmatchcase(path, pattern):
            return pattern, checkers
    sys.exit(f"no checker rule for {path}")


def verify_names(source, checker):
    if checker["kind"] != "go-test":
        return
    package = source / checker["package"]
    text = "".join(p.read_text(encoding="utf-8", errors="replace") for p in package.glob("*_test.go"))
    for name in checker["run"].split("|"):
        bare = name.strip("^$")
        if not re.search(rf"(?m)^func {re.escape(bare)}\(", text):
            sys.exit(f"checker {bare} is not a test of ./{checker['package']}/ at the pin")


def run(source, checker, cache):
    key = json.dumps(checker, sort_keys=True)
    if key in cache:
        return cache[key]
    if checker["kind"] == "go-test":
        command = ["go", "test", "-count=1", "-run", checker["run"], f"./{checker['package']}/"]
        result = common.go_run(command[1:], source, common.go_env({"GOTOOLCHAIN": "auto"}))
        status = result.returncode
        text = " ".join(command[:4]) + f" '{checker['run']}' ./{checker['package']}/"
    elif checker["kind"] == "pytest":
        command = [sys.executable, "-I", "-m", "pytest", checker["file"] + "::" + checker["test"], "-q", "-p", "no:cacheprovider"]
        status = subprocess.run(command, cwd=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
        text = f"python3 -m pytest {checker['file']}::{checker['test']} -q -p no:cacheprovider"
    else:
        command = ["node", "--test", checker["file"]]
        status = subprocess.run(command, cwd=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
        text = f"node --test {checker['file']}"
    cache[key] = (text, status)
    return cache[key]


def record(manifest_path):
    item = common.entry("current", "gateway")
    source = common.unpack(item)
    cache = {}
    entries = []
    for path in expand(source):
        pattern, checkers = checkers_of(path)
        entry = {"ref": f"{item['slug_at_pin']}@{item['commit']}:{path}", "path": path, "sha256": sha256(source / path)}
        if not checkers:
            entry["checker"] = None
            entry["note"] = NO_CHECKER[pattern]
        else:
            entry["checkers"] = []
            for checker in checkers:
                verify_names(source, checker)
                command, status = run(source, checker, cache)
                entry["checkers"].append({"command": command, "exit_status": status})
        entries.append(entry)
    manifest = {"format": "helianthus-oracle-gateway-goldens/1", "source": {"repository": item["slug_at_pin"], "commit": item["commit"]}, "files": entries}
    common.write(manifest_path, common.canonical(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    manifest = record(args.manifest)
    failing = [(e["path"], c["command"], c["exit_status"]) for e in manifest["files"] for c in e.get("checkers", []) if c["exit_status"] != 0]
    print(len(manifest["files"]), "files;", len(failing), "failing checker entries")
    for item in failing:
        print("FAIL", *item)


if __name__ == "__main__":
    main()
