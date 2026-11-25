package service

import (
	"fmt"
	"net"
	"net/netip"
	"strconv"
	"sync"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-eebus-go/api"
	shipapi "github.com/Project-Helianthus/helianthus-ship-go/api"
	shipmodel "github.com/Project-Helianthus/helianthus-ship-go/model"
	spinemocks "github.com/Project-Helianthus/helianthus-spine-go/mocks"
	"github.com/stretchr/testify/mock"
)

type oracleHubReader struct {
	mux   sync.Mutex
	calls []any
}

func (reader *oracleHubReader) note(call string, fields map[string]any) {
	reader.mux.Lock()
	defer reader.mux.Unlock()
	record := map[string]any{"call": call}
	for key, value := range fields {
		record[key] = value
	}
	reader.calls = append(reader.calls, record)
}

func (reader *oracleHubReader) RemoteSKIConnected(service api.ServiceInterface, ski string) {
	reader.note("RemoteSKIConnected", map[string]any{"ski": ski, "service_present": service != nil})
}

func (reader *oracleHubReader) RemoteSKIDisconnected(service api.ServiceInterface, ski string) {
	reader.note("RemoteSKIDisconnected", map[string]any{"ski": ski, "service_present": service != nil})
}

func (reader *oracleHubReader) VisibleRemoteServicesUpdated(service api.ServiceInterface, entries []shipapi.RemoteService) {
	skis := []any{}
	for _, entry := range entries {
		skis = append(skis, entry.Ski)
	}
	reader.note("VisibleRemoteServicesUpdated", map[string]any{"skis": skis, "service_present": service != nil})
}

func (reader *oracleHubReader) ServiceShipIDUpdate(ski string, shipID string) {
	reader.note("ServiceShipIDUpdate", map[string]any{"ski": ski, "ship_id": shipID})
}

func (reader *oracleHubReader) ServicePairingDetailUpdate(ski string, detail *shipapi.ConnectionStateDetail) {
	fields := map[string]any{"ski": ski, "detail_present": detail != nil}
	if detail != nil {
		fields["state"] = int(detail.State())
	}
	reader.note("ServicePairingDetailUpdate", fields)
}

type oracleHubWriter struct{}

func (oracleHubWriter) WriteShipMessageWithPayload([]byte) {}

// oracleRecordHubReaderForwarding records the callbacks the service forwards
// to its handler or its local SPINE device.
func oracleRecordHubReaderForwarding(t *testing.T) {
	reader := &oracleHubReader{}
	sut := &Service{serviceHandler: reader, isPairingPossible: true}
	localDevice := spinemocks.NewDeviceLocalInterface(t)
	sut.spineLocalDevice = localDevice
	ski := "test"
	sut.VisibleRemoteServicesUpdated([]shipapi.RemoteService{{Ski: ski}})
	sut.RemoteSKIConnected(ski)
	localDevice.EXPECT().RemoveRemoteDeviceConnection(ski).Return().Once()
	sut.RemoteSKIDisconnected(ski)
	sut.ServiceShipIDUpdate(ski, "shipid")
	detail := shipapi.NewConnectionStateDetail(shipapi.ConnectionStateReceivedPairingRequest, nil)
	sut.ServicePairingDetailUpdate(ski, detail)
	localDevice.EXPECT().SetupRemoteDevice(ski, mock.Anything).Return(nil).Once()
	reader2 := sut.SetupRemoteDevice(ski, oracleHubWriter{})
	allowOpen := sut.AllowWaitingForTrust(ski)
	sut.isPairingPossible = false
	allowClosed := sut.AllowWaitingForTrust(ski)
	localDevice.AssertExpectations(t)

	oracleWrite(t, "service-hub-go", "reader-callbacks-forwarded", oracleCase{
		Component: "service/service_hub.go (RemoteSKIConnected, RemoteSKIDisconnected, SetupRemoteDevice, VisibleRemoteServicesUpdated, ServiceShipIDUpdate, ServicePairingDetailUpdate, AllowWaitingForTrust)",
		Source:    "service/service_hub.go",
		Stimulus:  "service/service_test.go Test_EEBUSHandler, Test_ConnectionsHub (SetupRemoteDevice)",
		Input: oracleInput{Qualifiers: map[string]any{
			"ski": ski, "ship_id": "shipid", "pairing_state": "ConnectionStateReceivedPairingRequest", "pairing_possible_before": true, "pairing_possible_after": false,
		}},
		Output: oracleOutput{
			Observations: reader.calls,
			Decisions: []any{
				map[string]any{"call": "SetupRemoteDevice", "returned_reader_is_nil": reader2 == nil, "local_device_expectations_met": true},
				map[string]any{"call": "AllowWaitingForTrust/pairing-possible", "result": allowOpen},
				map[string]any{"call": "AllowWaitingForTrust/pairing-closed", "result": allowClosed},
			},
		},
	})
}

// oracleRecordHubOutgoingAttemptForwarding records the outgoing attempt
// callbacks forwarded to the sink of the bridge configuration.
func oracleRecordHubOutgoingAttemptForwarding(t *testing.T) {
	legacy := &legacyServiceReaderRecorder{}
	sink := &outgoingAttemptSinkRecorder{}
	sut := newOutgoingAttemptBridgeService(newOutgoingAttemptTestConfiguration(t), legacy, &outgoingAttemptGateStub{}, sink)
	metadata := shipapi.OutgoingAttemptMetadata{AttemptID: "attempt-73\x00opaque", Scope: "remote-scope/value", ControlEpoch: ^uint64(0) - 41}
	second := shipapi.OutgoingAttemptMetadata{AttemptID: "attempt-74/distinct", Scope: "second-scope\x00opaque", ControlEpoch: 0}
	state := shipmodel.ShipState{State: shipmodel.SmeStateError}
	remote := "remote-ski\x00exact"
	sut.OutgoingAttemptConnectionClosed(remote, false, metadata)
	sut.OutgoingAttemptConnectionClosed("second-remote-ski", true, second)
	sut.OutgoingAttemptHandshakeStateUpdate(remote, state, metadata)
	encode := func(value shipapi.OutgoingAttemptMetadata) map[string]any {
		return map[string]any{"attempt_id": value.AttemptID, "scope": value.Scope, "control_epoch": strconv.FormatUint(value.ControlEpoch, 10)}
	}
	observations := []any{}
	for _, event := range sink.closed {
		observations = append(observations, map[string]any{"call": "OutgoingAttemptConnectionClosed", "remote_ski": event.remoteSKI, "complete": event.complete, "metadata": encode(event.metadata)})
	}
	for _, event := range sink.handshake {
		observations = append(observations, map[string]any{"call": "OutgoingAttemptHandshakeStateUpdate", "remote_ski": event.remoteSKI, "state": fmt.Sprint(event.state.State), "state_value": int(event.state.State), "metadata": encode(event.metadata)})
	}
	oracleWrite(t, "service-hub-go", "outgoing-attempt-callbacks-forwarded", oracleCase{
		Component: "service/service_hub.go (OutgoingAttemptConnectionClosed, OutgoingAttemptHandshakeStateUpdate)",
		Source:    "service/service_hub.go",
		Stimulus:  "service/outgoing_attempt_bridge_test.go TestOutgoingAttemptBridgeProductionHubReaderRouteForwardsExactCallbacks",
		Input: oracleInput{Qualifiers: map[string]any{
			"calls": []any{
				map[string]any{"call": "OutgoingAttemptConnectionClosed", "remote_ski": remote, "complete": false, "metadata": encode(metadata)},
				map[string]any{"call": "OutgoingAttemptConnectionClosed", "remote_ski": "second-remote-ski", "complete": true, "metadata": encode(second)},
				map[string]any{"call": "OutgoingAttemptHandshakeStateUpdate", "remote_ski": remote, "state": "SmeStateError", "metadata": encode(metadata)},
			},
		}},
		Output: oracleOutput{
			Observations: observations,
			Decisions: []any{
				map[string]any{"call": "legacy-handler-notified", "connected": legacy.connectedCalls, "disconnected": legacy.disconnected, "pairing": legacy.pairingCalls},
			},
		},
	})
}

// oracleRecordHubLegacyCandidateVisibility records the endpoint-redacted
// candidate callback: ordering, cloning and the readers that receive nothing.
func oracleRecordHubLegacyCandidateVisibility(t *testing.T) {
	steps := []any{}
	input := []shipapi.PairingCandidateRef{
		{CandidateRef: "candidate-b", Name: "zeta", SKI: "ski-z"},
		{CandidateRef: "candidate-b", Name: "alpha", SKI: "ski-a"},
		{CandidateRef: "candidate-a", Name: "zeta", SKI: "ski-z", Identifier: "identifier-b"},
		{CandidateRef: "candidate-a", Name: "zeta", SKI: "ski-z", Identifier: "identifier-a", Brand: "brand-b"},
		{CandidateRef: "candidate-a", Name: "zeta", SKI: "ski-z", Identifier: "identifier-a", Brand: "brand-a", Type: "type-b"},
		{CandidateRef: "candidate-a", Name: "alpha", SKI: "ski-z"},
	}
	{
		reader := &pairingCandidateVisibilityReader{}
		sut := &Service{serviceHandler: reader}
		sut.VisiblePairingCandidatesUpdated(input)
		forwarded := oracleRefs(reader.candidates)
		input[1].Name = "mutated-input"
		readerAliasesInput := reader.candidates[0].Name != "alpha"
		reader.candidates[0].Name = "mutated-reader"
		inputAliasesReader := input[1].Name != "mutated-input"
		oracleStep(&steps, "VisiblePairingCandidatesUpdated/ordering-and-cloning", map[string]any{
			"forwarded": forwarded, "reader_aliases_input": readerAliasesInput, "input_aliases_reader": inputAliasesReader,
		})
	}
	{
		candidates := []shipapi.PairingCandidateRef{{CandidateRef: "candidate-a", SKI: "ski-a"}}
		(&Service{}).VisiblePairingCandidatesUpdated(candidates)
		unsupported := &Service{serviceHandler: &legacyPairingCandidateVisibilityReader{}}
		unsupported.VisiblePairingCandidatesUpdated(candidates)
		var typedNil *pairingCandidateVisibilityReader
		(&Service{serviceHandler: typedNil}).VisiblePairingCandidatesUpdated(candidates)
		oracleStep(&steps, "VisiblePairingCandidatesUpdated/absent-unsupported-typed-nil-readers", map[string]any{"panicked": false})
	}
	{
		reader := &pairingCandidateVisibilityReader{}
		sut := &Service{serviceHandler: reader}
		sut.VisiblePairingCandidatesUpdated([]shipapi.PairingCandidateRef{{CandidateRef: "candidate-a", SKI: "ski-a"}})
		sut.VisiblePairingCandidatesUpdated(nil)
		oracleStep(&steps, "VisiblePairingCandidatesUpdated/empty-clears", map[string]any{"candidates_after": oracleRefs(reader.candidates)})
	}
	for _, state := range []lifecycleState{lifecycleReady, lifecycleStarting, lifecycleRunning, lifecycleStopping, lifecycleStopped, lifecycleTerminal} {
		reader := &pairingCandidateVisibilityReader{}
		sut := &Service{serviceHandler: reader, lifecycle: state}
		sut.VisiblePairingCandidatesUpdated([]shipapi.PairingCandidateRef{{CandidateRef: "candidate-a", SKI: "ski-a"}})
		oracleStep(&steps, "VisiblePairingCandidatesUpdated/lifecycle", map[string]any{"lifecycle": oracleLifecycleName(state), "forwarded": len(reader.candidates)})
	}
	{
		reader := &concurrentPairingCandidateVisibilityReader{}
		sut := &Service{serviceHandler: reader}
		const callbacks = 32
		start := make(chan struct{})
		var wait sync.WaitGroup
		for index := 0; index < callbacks; index++ {
			wait.Add(1)
			go func(index int) {
				defer wait.Done()
				<-start
				sut.VisiblePairingCandidatesUpdated([]shipapi.PairingCandidateRef{{CandidateRef: "candidate", Name: string(rune('a' + index%26))}})
			}(index)
		}
		close(start)
		wait.Wait()
		snapshots := reader.snapshot()
		complete := true
		for _, candidates := range snapshots {
			if len(candidates) != 1 || candidates[0].CandidateRef != "candidate" {
				complete = false
			}
		}
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("latest"))
		after := reader.snapshot()
		oracleStep(&steps, "VisiblePairingCandidatesUpdated/concurrent-reports", map[string]any{
			"callbacks_sent": callbacks, "delivered_between_one_and_sent": len(snapshots) >= 1 && len(snapshots) <= callbacks, "every_delivery_complete": complete,
			"final_label": candidateVisibilityLabel(after[len(after)-1]),
		})
	}
	{
		reader := &reentrantPairingCandidateVisibilityReader{}
		sut := &Service{serviceHandler: reader}
		done := make(chan struct{})
		go func() {
			sut.VisiblePairingCandidatesUpdated([]shipapi.PairingCandidateRef{{CandidateRef: "outer", Name: "outer"}})
			close(done)
		}()
		select {
		case <-done:
		case <-time.After(time.Second):
			t.Fatal("reentrant candidate callback blocked")
		}
		labels := []any{}
		for _, snapshot := range reader.snapshots {
			labels = append(labels, candidateVisibilityLabel(snapshot))
		}
		reader.snapshots[1][0].Name = "mutated-inner"
		oracleStep(&steps, "VisiblePairingCandidatesUpdated/reentrant-report", map[string]any{
			"delivery_order": labels, "snapshots_alias": reader.snapshots[0][0].Name != "outer",
		})
	}
	oracleWrite(t, "service-hub-go", "legacy-candidate-visibility", oracleCase{
		Component: "service/service_hub.go (VisiblePairingCandidatesUpdated, cloneAndSortPairingCandidateRefs, pairingCandidateRefLess)",
		Source:    "service/service_hub.go",
		Stimulus:  "service/pairing_candidate_visibility_red_test.go (every test of the legacy callback)",
		Input:     oracleInput{Qualifiers: map[string]any{"candidates_in_input_order": oracleRefs(input)}},
		Output:    oracleOutput{Decisions: steps},
	})
}

// oracleRecordHubCandidateVisibilityDispatch records the serialized, coalescing
// and terminal behaviour of the candidate visibility dispatcher.
func oracleRecordHubCandidateVisibilityDispatch(t *testing.T) {
	steps := []any{}
	newHub := func(released bool) *candidateVisibilityShutdownHub {
		hub := &candidateVisibilityShutdownHub{entered: make(chan struct{}), release: make(chan struct{}), done: make(chan struct{})}
		if released {
			close(hub.release)
		}
		return hub
	}
	{
		hub := newHub(false)
		reader := &serializedCandidateVisibilityReader{firstEntered: make(chan struct{}), firstRelease: make(chan struct{}), hubShutdownDone: hub.done}
		sut := &Service{serviceHandler: reader, connectionsHub: hub, lifecycle: lifecycleRunning}
		firstDone := make(chan struct{})
		go func() { sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("first")); close(firstDone) }()
		<-reader.firstEntered
		shutdownDone := make(chan struct{})
		go func() { sut.Shutdown(); close(shutdownDone) }()
		<-hub.entered
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("during-shutdown"))
		close(hub.release)
		shutdownReturned := false
		select {
		case <-shutdownDone:
			shutdownReturned = true
		case <-time.After(time.Second):
		}
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("after-shutdown-return"))
		close(reader.firstRelease)
		<-firstDone
		labels, maxActive, emptyAfterHub := reader.state()
		oracleStep(&steps, "shutdown-racing-an-in-flight-callback", map[string]any{
			"shutdown_returned_while_callback_in_flight": shutdownReturned, "callback_order": labels, "max_concurrent_callbacks": maxActive, "terminal_empty_after_hub_shutdown": emptyAfterHub,
		})
	}
	{
		hub := newHub(true)
		reader := &serializedCandidateVisibilityReader{hubShutdownDone: hub.done, shutdownOn: "shutdown"}
		sut := &Service{serviceHandler: reader, connectionsHub: hub, lifecycle: lifecycleRunning}
		reportDone := make(chan struct{})
		go func() { sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("shutdown")); close(reportDone) }()
		returned := false
		select {
		case <-reportDone:
			returned = true
		case <-time.After(time.Second):
		}
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("after"))
		labels, maxActive, emptyAfterHub := reader.state()
		oracleStep(&steps, "callback-reenters-shutdown", map[string]any{
			"report_returned": returned, "callback_order": labels, "max_concurrent_callbacks": maxActive, "terminal_empty_after_hub_shutdown": emptyAfterHub,
		})
	}
	{
		hub := newHub(true)
		reader := &serializedCandidateVisibilityReader{hubShutdownDone: hub.done}
		sut := &Service{serviceHandler: reader, connectionsHub: hub, lifecycle: lifecycleRunning}
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("before"))
		sut.Shutdown()
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("after"))
		sut.Shutdown()
		labels, maxActive, emptyAfterHub := reader.state()
		oracleStep(&steps, "terminal-empty-once-last", map[string]any{
			"callback_order": labels, "max_concurrent_callbacks": maxActive, "terminal_empty_after_hub_shutdown": emptyAfterHub, "lifecycle": oracleState(sut),
		})
	}
	{
		hub := newHub(true)
		reader := &serializedCandidateVisibilityReader{firstEntered: make(chan struct{}), firstRelease: make(chan struct{}), hubShutdownDone: hub.done}
		sut := &Service{serviceHandler: reader, connectionsHub: hub, lifecycle: lifecycleRunning}
		firstDone := make(chan struct{})
		go func() { sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("first")); close(firstDone) }()
		<-reader.firstEntered
		for index := 0; index < 1024; index++ {
			sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("stale"))
		}
		latest := candidateVisibilitySnapshot("latest")
		sut.VisiblePairingCandidatesUpdated(latest)
		latest[0].Name = "mutated-input"
		normalBefore, totalBefore, labelsBefore := pendingCandidateVisibilityState(sut)
		sut.Shutdown()
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("after-shutdown"))
		normalAfter, totalAfter, labelsAfter := pendingCandidateVisibilityState(sut)
		close(reader.firstRelease)
		<-firstDone
		labels, maxActive, emptyAfterHub := reader.state()
		oracleStep(&steps, "flood-coalesces-latest-pending", map[string]any{
			"reports_while_first_callback_blocked": 1025, "pending_before_terminal": map[string]any{"normal": normalBefore, "total": totalBefore, "labels": labelsBefore},
			"pending_with_terminal": map[string]any{"normal": normalAfter, "total": totalAfter, "labels": labelsAfter},
			"callback_order":        labels, "max_concurrent_callbacks": maxActive, "terminal_empty_after_hub_shutdown": emptyAfterHub,
		})
	}
	{
		reader := &serializedCandidateVisibilityReader{reenter: true}
		sut := &Service{serviceHandler: reader}
		sut.VisiblePairingCandidatesUpdated(candidateVisibilitySnapshot("outer"))
		labels, maxActive, _ := reader.state()
		oracleStep(&steps, "reentrant-report-queues-without-nesting", map[string]any{"callback_order": labels, "max_concurrent_callbacks": maxActive})
	}
	oracleWrite(t, "service-hub-go", "candidate-visibility-dispatch", oracleCase{
		Component: "service/service_hub.go (dispatchPairingCandidateVisibility, closePairingCandidateVisibilityAdmissions, emitTerminalPairingCandidateVisibility, drainPairingCandidateVisibility)",
		Source:    "service/service_hub.go",
		Stimulus:  "service/pairing_candidate_visibility_dispatch_test.go (every test)",
		Input:     oracleInput{Qualifiers: map[string]any{"labels": []any{"first", "during-shutdown", "after-shutdown-return", "shutdown", "after", "before", "stale", "latest", "after-shutdown", "outer", "inner"}, "flood_reports": 1024}},
		Output:    oracleOutput{Decisions: steps},
	})
}

// oracleRecordNativeDiscoverySnapshots records native_discovery_snapshot_test.go:
// the complete snapshot callback, absence and restart revision, terminal clear
// and the readers that receive nothing.
func oracleRecordNativeDiscoverySnapshots(t *testing.T) {
	{
		reader := &nativeDiscoveryReader{}
		sut := &Service{serviceHandler: reader}
		input := shipapi.PairingCandidateDiscoverySnapshotV1{
			ObservationRevision: 41,
			NewEntries:          true,
			Candidates: []shipapi.PairingCandidateDiscoveryObservationV1{
				{
					CandidateRef: "candidate-z", Name: "second", SKI: "ski-z", Identifier: "id-z",
					Brand: "brand-z", Type: "type-z", Model: "model-z", Path: "/ship/z", Host: "z.invalid",
					Port: 4712, Register: true, Addresses: []net.IP{net.IPv4(192, 0, 2, 41)},
					ScopedAddresses:           []netip.Addr{netip.MustParseAddr("fe80::41").WithZone("synthetic1")},
					UnscopedLinkLocalObserved: true,
				},
				{
					CandidateRef: "candidate-a", Name: "first", SKI: "ski-a", Identifier: "id-a",
					Brand: "brand-a", Type: "type-a", Model: "model-a", Path: "/ship/a", Host: "a.invalid",
					Port: 4713, Addresses: []net.IP{net.ParseIP("2001:db8::41")},
					ScopedAddresses: []netip.Addr{netip.MustParseAddr("2001:db8::41")},
				},
			},
		}
		stimulus := oracleSnapshot(input)
		sut.VisiblePairingCandidateDiscoverySnapshotUpdated(input)
		input.Candidates[1].Name = "mutated-input"
		input.Candidates[1].Addresses[0][0] ^= 0xff
		input.Candidates[1].ScopedAddresses[0] = netip.MustParseAddr("2001:db8::99")
		got := reader.snapshot()
		delivered := []any{}
		for _, snapshot := range got {
			delivered = append(delivered, oracleSnapshot(snapshot))
		}
		oracleWrite(t, "native-discovery-snapshot", "round-trips-all-fields-ordered-and-detached", oracleCase{
			Component: "service/service_hub.go (VisiblePairingCandidateDiscoverySnapshotUpdated, cloneAndSortPairingCandidateDiscoverySnapshot)",
			Source:    "service/service_hub.go",
			Stimulus:  "service/native_discovery_snapshot_test.go TestNativeDiscoverySnapshotRoundTripsAllFieldsOrderedAndDetached",
			Input:     oracleInput{Qualifiers: map[string]any{"snapshot": stimulus, "after_delivery": "the input candidate name, first address byte and first scoped address of candidate-a are mutated"}},
			Output:    oracleOutput{Observations: delivered},
		})
	}
	{
		firstReader := &nativeDiscoveryReader{}
		first := &Service{serviceHandler: firstReader}
		before := shipapi.PairingCandidateDiscoverySnapshotV1{
			ObservationRevision: 99,
			Candidates:          []shipapi.PairingCandidateDiscoveryObservationV1{{CandidateRef: "candidate-before-restart", SKI: "ski-before-restart"}},
		}
		first.VisiblePairingCandidateDiscoverySnapshotUpdated(before)
		restartedReader := &nativeDiscoveryReader{}
		restarted := &Service{serviceHandler: restartedReader}
		after := shipapi.PairingCandidateDiscoverySnapshotV1{ObservationRevision: 1, Candidates: []shipapi.PairingCandidateDiscoveryObservationV1{}}
		restarted.VisiblePairingCandidateDiscoverySnapshotUpdated(after)
		delivered := func(reader *nativeDiscoveryReader) []any {
			out := []any{}
			for _, snapshot := range reader.snapshot() {
				out = append(out, oracleSnapshot(snapshot))
			}
			return out
		}
		oracleWrite(t, "native-discovery-snapshot", "preserves-absence-and-restart-revision", oracleCase{
			Component: "service/service_hub.go (VisiblePairingCandidateDiscoverySnapshotUpdated)",
			Source:    "service/service_hub.go",
			Stimulus:  "service/native_discovery_snapshot_test.go TestNativeDiscoverySnapshotPreservesAbsenceAndRestartRevision",
			Input:     oracleInput{Qualifiers: map[string]any{"before_restart": oracleSnapshot(before), "after_restart": oracleSnapshot(after)}},
			Output: oracleOutput{Observations: []any{
				map[string]any{"reader": "before-restart", "delivered": delivered(firstReader)},
				map[string]any{"reader": "after-restart", "delivered": delivered(restartedReader)},
			}},
		})
	}
	{
		hub := &candidateVisibilityShutdownHub{entered: make(chan struct{}), release: make(chan struct{}), done: make(chan struct{})}
		close(hub.release)
		reader := &nativeDiscoveryReader{}
		sut := &Service{serviceHandler: reader, connectionsHub: hub, lifecycle: lifecycleRunning}
		beforeShutdown := shipapi.PairingCandidateDiscoverySnapshotV1{
			ObservationRevision: 7, NewEntries: true,
			Candidates: []shipapi.PairingCandidateDiscoveryObservationV1{{CandidateRef: "candidate-before-shutdown", SKI: "ski-before-shutdown"}},
		}
		afterShutdown := shipapi.PairingCandidateDiscoverySnapshotV1{
			ObservationRevision: 8,
			Candidates:          []shipapi.PairingCandidateDiscoveryObservationV1{{CandidateRef: "candidate-after-shutdown", SKI: "ski-after-shutdown"}},
		}
		sut.VisiblePairingCandidateDiscoverySnapshotUpdated(beforeShutdown)
		sut.Shutdown()
		sut.VisiblePairingCandidateDiscoverySnapshotUpdated(afterShutdown)
		sut.Shutdown()
		delivered := []any{}
		for _, snapshot := range reader.snapshot() {
			delivered = append(delivered, oracleSnapshot(snapshot))
		}
		oracleWrite(t, "native-discovery-snapshot", "shutdown-clears-once-and-suppresses-later-updates", oracleCase{
			Component: "service/service_hub.go (VisiblePairingCandidateDiscoverySnapshotUpdated, emitTerminalPairingCandidateVisibility)",
			Source:    "service/service_hub.go",
			Stimulus:  "service/native_discovery_snapshot_test.go TestNativeDiscoverySnapshotShutdownClearsOnceAndSuppressesLaterUpdates",
			Input: oracleInput{Qualifiers: map[string]any{
				"sequence": []any{"snapshot revision 7", "Shutdown", "snapshot revision 8", "Shutdown"}, "snapshot_7": oracleSnapshot(beforeShutdown), "snapshot_8": oracleSnapshot(afterShutdown),
			}},
			Output: oracleOutput{Observations: delivered, Decisions: []any{map[string]any{"lifecycle": oracleState(sut)}}},
		})
	}
	{
		snapshot := shipapi.PairingCandidateDiscoverySnapshotV1{ObservationRevision: 1}
		(&Service{}).VisiblePairingCandidateDiscoverySnapshotUpdated(snapshot)
		var typedNil *nativeDiscoveryReader
		(&Service{serviceHandler: typedNil}).VisiblePairingCandidateDiscoverySnapshotUpdated(snapshot)
		oracleWrite(t, "native-discovery-snapshot", "ignores-absent-and-typed-nil-readers", oracleCase{
			Component: "service/service_hub.go (VisiblePairingCandidateDiscoverySnapshotUpdated)",
			Source:    "service/service_hub.go",
			Stimulus:  "service/native_discovery_snapshot_test.go TestNativeDiscoverySnapshotIgnoresAbsentAndTypedNilReaders",
			Input:     oracleInput{Qualifiers: map[string]any{"snapshot": oracleSnapshot(snapshot), "handlers": []any{"none", "typed nil native reader"}}},
			Output:    oracleOutput{Decisions: []any{map[string]any{"panicked": false}}},
		})
	}
}
