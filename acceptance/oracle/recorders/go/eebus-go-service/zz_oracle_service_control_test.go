package service

import (
	"errors"
	"net"
	"net/netip"
	"strings"
	"syscall"
	"testing"

	shipapi "github.com/Project-Helianthus/helianthus-ship-go/api"
)

func oracleReservation(first byte) shipapi.PairingCandidateReservation {
	var token [32]byte
	token[0] = first
	return shipapi.NewPairingCandidateReservation(token)
}

// oracleRecordListenerPolicy records StartWithPolicy on a scripted hub and on
// the production hub bound to the loopback address of this host.
func oracleRecordListenerPolicy(t *testing.T) {
	steps := []any{}
	{
		terminalErr := errors.New("SHIP listener lifecycle is terminal")
		hub := &listenerPolicyLifecycleHub{}
		sut := serviceWithReadyListenerPolicyHub(hub)
		first := sut.StartWithPolicy()
		hub.setStartError(terminalErr)
		second := sut.StartWithPolicy()
		afterSecond := oracleState(sut)
		sut.Shutdown()
		oracleStep(&steps, "StartWithPolicy/asynchronous-hub-terminal-state", map[string]any{
			"first_error": oracleErr(first), "second_error": oracleErr(second), "second_error_is_hub_error": errors.Is(second, terminalErr),
			"lifecycle_after_second": afterSecond, "lifecycle_after_shutdown": oracleState(sut), "hub_shutdown_calls": hub.shutdownCount(),
		})
	}
	{
		hub := &listenerPolicyLifecycleHub{startEntered: make(chan struct{}), startRelease: make(chan struct{})}
		sut := serviceWithReadyListenerPolicyHub(hub)
		startResult := make(chan error, 1)
		go func() { startResult <- sut.StartWithPolicy() }()
		<-hub.startEntered
		shutdownDone := make(chan struct{})
		go func() {
			sut.Shutdown()
			close(shutdownDone)
		}()
		<-shutdownDone
		close(hub.startRelease)
		err := <-startResult
		oracleStep(&steps, "StartWithPolicy/racing-Shutdown", map[string]any{
			"error": oracleErr(err), "error_mentions_terminal": err != nil && strings.Contains(strings.ToLower(err.Error()), "terminal"),
			"lifecycle": oracleState(sut), "hub_shutdown_calls": hub.shutdownCount(),
		})
	}
	{
		endpoint := listenerPolicyAvailableEndpoint(t, netip.AddrFrom4([4]byte{127, 0, 0, 1}))
		sut := newListenerPolicyService(t, endpoint, false)
		setupErr := sut.Setup()
		startErr := startScopedService(t, sut)
		dialErr := oracleDial(endpoint)
		listenerPolicyConcurrentShutdown(t, sut, 8)
		rebindErr := oracleRebind(endpoint)
		oracleStep(&steps, "StartWithPolicy/production-hub-loopback", map[string]any{
			"discovery_enabled": false, "setup_error": oracleErr(setupErr), "start_error": oracleErr(startErr), "dial_error": oracleErr(dialErr),
			"rebind_after_shutdown_error": oracleErr(rebindErr), "lifecycle_after_shutdown": oracleState(sut),
		})
	}
	{
		held := listenerPolicyListen(t, netip.AddrPortFrom(netip.AddrFrom4([4]byte{127, 0, 0, 1}), 0))
		endpoint := held.Addr().(*net.TCPAddr).AddrPort()
		sut := newListenerPolicyService(t, endpoint, false)
		setupErr := sut.Setup()
		startErr := startScopedService(t, sut)
		_ = held.Close()
		retryErr := startScopedService(t, sut)
		sut.Start()
		listenerPolicyConcurrentShutdown(t, sut, 2)
		oracleStep(&steps, "StartWithPolicy/bind-failure-terminalizes-retries", map[string]any{
			"setup_error": oracleErr(setupErr), "start_error_is_address_in_use": errors.Is(startErr, syscall.EADDRINUSE),
			"retry_error_mentions_terminal": retryErr != nil && strings.Contains(strings.ToLower(retryErr.Error()), "terminal"),
			"lifecycle_after_shutdown":      oracleState(sut),
		})
	}
	for _, discovery := range []bool{false, true} {
		for _, pairing := range []bool{false, true} {
			endpoint := listenerPolicyAvailableEndpoint(t, netip.AddrFrom4([4]byte{127, 0, 0, 1}))
			configuration := newListenerPolicyConfiguration(t, endpoint.Port())
			configuration.SetInterfaces([]string{listenerPolicyMissingInterface})
			policy := ListenerPolicy{ListenAddress: endpoint, DiscoveryEnabled: discovery}
			sut := NewServiceWithOptions(configuration, &legacyServiceReaderRecorder{}, ServiceOptions{ListenerPolicy: &policy})
			registerErr := sut.SetPairingRegistration(pairing)
			setupErr := sut.Setup()
			startErr := startScopedService(t, sut)
			record := map[string]any{
				"discovery_enabled": discovery, "pairing_possible": pairing, "registration_error": oracleErr(registerErr), "setup_error": oracleErr(setupErr),
				"start_error_names_interface": startErr != nil && strings.Contains(startErr.Error(), listenerPolicyMissingInterface),
				"start_error_is_nil":          startErr == nil,
			}
			if startErr == nil {
				record["dial_error"] = oracleErr(oracleDial(endpoint))
			} else {
				retryErr := startScopedService(t, sut)
				record["retry_error_mentions_terminal"] = retryErr != nil && strings.Contains(strings.ToLower(retryErr.Error()), "terminal")
			}
			sut.Start()
			listenerPolicyConcurrentShutdown(t, sut, 2)
			record["rebind_after_shutdown_error"] = oracleErr(oracleRebind(endpoint))
			record["lifecycle_after_shutdown"] = oracleState(sut)
			oracleStep(&steps, "StartWithPolicy/discovery-policy", record)
		}
	}
	{
		endpoint := listenerPolicyAvailableEndpoint(t, netip.AddrFrom4([4]byte{127, 0, 0, 1}))
		configurationPort := endpoint.Port() - 1
		policy := ListenerPolicy{ListenAddress: endpoint, DiscoveryEnabled: false}
		sut := NewServiceWithOptions(newListenerPolicyConfiguration(t, configurationPort), &legacyServiceReaderRecorder{}, ServiceOptions{ListenerPolicy: &policy})
		err := sut.Setup()
		sut.Start()
		sut.Shutdown()
		sut.Shutdown()
		oracleStep(&steps, "Setup/listener-policy-port-mismatch", map[string]any{
			"error_is_nil": err == nil, "error_mentions_port": err != nil && strings.Contains(strings.ToLower(err.Error()), "port"),
			"hub_published": sut.connectionsHub != nil, "local_service_published": sut.localService != nil, "local_device_published": sut.spineLocalDevice != nil,
			"lifecycle": oracleState(sut),
		})
	}
	oracleWrite(t, "service-go", "listener-policy-start", oracleCase{
		Component: "service/service.go (Service.StartWithPolicy, ListenerPolicy, Setup with a listener policy)",
		Source:    "service/service.go",
		Stimulus:  "service/listener_policy_test.go TestScopedStartObservesAsynchronousHubTerminalState, TestScopedStartRacingShutdownReturnsTerminalAndCleansOnce, TestScopedStartBindsExactLoopbackAndReleasesIdempotently (IPv4 endpoint), TestScopedBindFailurePropagatesAndTerminalizesRetries, TestDiscoveryPolicyIsIndependentFromPairingAndListenerStartup, TestScopedSetupRejectsPortMismatchWithoutReconstructingPolicy",
		Input: oracleInput{Qualifiers: map[string]any{
			"endpoint": "a loopback IPv4 endpoint with a free port chosen by the host; the port is not part of any output",
			"missing_interface": listenerPolicyMissingInterface,
		}},
		Output: oracleOutput{Decisions: steps},
	})
}

func oracleDial(endpoint netip.AddrPort) error {
	connection, err := net.DialTimeout("tcp", endpoint.String(), 1e9)
	if err != nil {
		return err
	}
	return connection.Close()
}

func oracleRebind(endpoint netip.AddrPort) error {
	listener, err := net.ListenTCP("tcp4", net.TCPAddrFromAddrPort(endpoint))
	if err != nil {
		return err
	}
	return listener.Close()
}

// oracleRecordCandidateControl records the pairing candidate calls the service
// forwards to the SHIP hub and the lifecycle states that refuse them.
func oracleRecordCandidateControl(t *testing.T) {
	steps := []any{}
	ref, ski := pairingCandidateFacadeTestRef, pairingCandidateFacadeTestSKI
	terminal := []lifecycleState{lifecycleStopping, lifecycleStopped, lifecycleTerminal}
	{
		hub := &pairingCandidateHubSpy{}
		sut := &Service{connectionsHub: hub}
		err := sut.QueuePairingCandidate(ref, ski)
		oracleStep(&steps, "QueuePairingCandidate", map[string]any{"error": oracleErr(err), "hub_calls": oracleCalls(hub.pairingCandidateCalls())})
	}
	{
		wantErr := errors.New("candidate rejected")
		hub := &pairingCandidateHubSpy{err: wantErr}
		sut := &Service{connectionsHub: hub}
		err := sut.QueuePairingCandidate(ref, ski)
		oracleStep(&steps, "QueuePairingCandidate/hub-error", map[string]any{"error": oracleErr(err), "error_is_hub_error": errors.Is(err, wantErr), "hub_calls": oracleCalls(hub.pairingCandidateCalls())})
	}
	{
		sut := &Service{connectionsHub: &hubRuntimeRecorder{}}
		oracleStep(&steps, "QueuePairingCandidate/hub-without-capability", map[string]any{"error": oracleErr(sut.QueuePairingCandidate(ref, ski))})
	}
	for _, state := range terminal {
		hub := &pairingCandidateHubSpy{}
		sut := &Service{connectionsHub: hub, lifecycle: state}
		err := sut.QueuePairingCandidate(ref, ski)
		oracleStep(&steps, "QueuePairingCandidate/terminal-lifecycle", map[string]any{
			"lifecycle": oracleLifecycleName(state), "error": oracleErr(err), "error_is_terminal": errors.Is(err, errPairingCandidateServiceTerminal), "hub_calls": oracleCalls(hub.pairingCandidateCalls()),
		})
	}
	{
		hub := &pairingCandidateHubSpy{shutdownEntered: make(chan struct{}), shutdownRelease: make(chan struct{})}
		sut := &Service{connectionsHub: hub, lifecycle: lifecycleRunning}
		done := make(chan struct{})
		go func() { sut.Shutdown(); close(done) }()
		<-hub.shutdownEntered
		err := sut.QueuePairingCandidate(ref, ski)
		observed := oracleState(sut)
		close(hub.shutdownRelease)
		<-done
		oracleStep(&steps, "QueuePairingCandidate/shutdown-in-progress", map[string]any{
			"lifecycle_observed": observed, "error": oracleErr(err), "error_is_terminal": errors.Is(err, errPairingCandidateServiceTerminal), "hub_calls": oracleCalls(hub.pairingCandidateCalls()),
		})
	}
	{
		want := oracleReservation(0x5a)
		hub := &pairingCandidateControllerHubSpy{reservation: want}
		sut := &Service{connectionsHub: hub}
		got, selectErr := sut.SelectPairingCandidate(ref, ski)
		connectErr := sut.ConnectPairingCandidate(got)
		selectCalls, connectCalls := hub.snapshots()
		matches := []any{}
		for _, call := range connectCalls {
			matches = append(matches, call.Matches(want))
		}
		oracleStep(&steps, "SelectPairingCandidate+ConnectPairingCandidate", map[string]any{
			"select_error": oracleErr(selectErr), "connect_error": oracleErr(connectErr), "reservation_matches": got.Matches(want),
			"select_calls": oracleCalls(selectCalls), "connect_calls_match_reservation": matches,
		})
	}
	{
		wantErr := errors.New("candidate rejected")
		selectHub := &pairingCandidateControllerHubSpy{selectErr: wantErr}
		_, selectErr := (&Service{connectionsHub: selectHub}).SelectPairingCandidate(ref, ski)
		connectHub := &pairingCandidateControllerHubSpy{connectErr: wantErr}
		connectErr := (&Service{connectionsHub: connectHub}).ConnectPairingCandidate(oracleReservation(0x7b))
		oracleStep(&steps, "SelectPairingCandidate+ConnectPairingCandidate/hub-errors", map[string]any{
			"select_error_is_hub_error": errors.Is(selectErr, wantErr), "connect_error_is_hub_error": errors.Is(connectErr, wantErr),
		})
		sut := &Service{connectionsHub: &hubRuntimeRecorder{}}
		_, unsupportedSelect := sut.SelectPairingCandidate(ref, ski)
		unsupportedConnect := sut.ConnectPairingCandidate(oracleReservation(0x7b))
		oracleStep(&steps, "SelectPairingCandidate+ConnectPairingCandidate/hub-without-capability", map[string]any{
			"select_error": oracleErr(unsupportedSelect), "connect_error": oracleErr(unsupportedConnect),
		})
	}
	for _, state := range terminal {
		hub := &pairingCandidateControllerHubSpy{}
		sut := &Service{connectionsHub: hub, lifecycle: state}
		_, selectErr := sut.SelectPairingCandidate(ref, ski)
		connectErr := sut.ConnectPairingCandidate(oracleReservation(0x7b))
		selectCalls, connectCalls := hub.snapshots()
		oracleStep(&steps, "SelectPairingCandidate+ConnectPairingCandidate/terminal-lifecycle", map[string]any{
			"lifecycle": oracleLifecycleName(state), "select_error_is_terminal": errors.Is(selectErr, errPairingCandidateServiceTerminal),
			"connect_error_is_terminal": errors.Is(connectErr, errPairingCandidateServiceTerminal), "select_calls": len(selectCalls), "connect_calls": len(connectCalls),
		})
	}
	{
		hub := &pairingCandidateControllerHubSpy{shutdownEntered: make(chan struct{}), shutdownRelease: make(chan struct{})}
		sut := &Service{connectionsHub: hub, lifecycle: lifecycleRunning}
		done := make(chan struct{})
		go func() { sut.Shutdown(); close(done) }()
		<-hub.shutdownEntered
		_, selectErr := sut.SelectPairingCandidate(ref, ski)
		connectErr := sut.ConnectPairingCandidate(oracleReservation(0x4c))
		selectCalls, connectCalls := hub.snapshots()
		close(hub.shutdownRelease)
		<-done
		oracleStep(&steps, "SelectPairingCandidate+ConnectPairingCandidate/shutdown-in-progress", map[string]any{
			"select_error_is_terminal": errors.Is(selectErr, errPairingCandidateServiceTerminal), "connect_error_is_terminal": errors.Is(connectErr, errPairingCandidateServiceTerminal),
			"select_calls": len(selectCalls), "connect_calls": len(connectCalls),
		})
	}
	{
		want := oracleReservation(0x32)
		provider := &pairingCandidatePINProviderSpy{}
		hub := &pairingCandidatePINControllerHubSpy{}
		sut := &Service{connectionsHub: hub}
		err := sut.ConnectPairingCandidateWithPIN(want, provider)
		connects := hub.snapshotPINConnects()
		record := map[string]any{"error": oracleErr(err), "hub_connects": len(connects), "provider_consumed_calls": provider.callCount()}
		if len(connects) == 1 {
			record["reservation_matches"] = connects[0].reservation.Matches(want)
			record["provider_is_supplied_provider"] = connects[0].provider == shipapi.TransientPINProvider(provider)
		}
		oracleStep(&steps, "ConnectPairingCandidateWithPIN", record)
	}
	{
		provider := &pairingCandidatePINProviderSpy{}
		reservation := oracleReservation(0x66)
		for _, state := range terminal {
			hub := &pairingCandidatePINControllerHubSpy{}
			sut := &Service{connectionsHub: hub, lifecycle: state}
			err := sut.ConnectPairingCandidateWithPIN(reservation, provider)
			oracleStep(&steps, "ConnectPairingCandidateWithPIN/terminal-lifecycle", map[string]any{
				"lifecycle": oracleLifecycleName(state), "error_is_terminal": errors.Is(err, errPairingCandidateServiceTerminal), "hub_connects": len(hub.snapshotPINConnects()),
			})
		}
		oracleStep(&steps, "ConnectPairingCandidateWithPIN/hub-without-capability", map[string]any{
			"error": oracleErr((&Service{connectionsHub: &hubRuntimeRecorder{}}).ConnectPairingCandidateWithPIN(reservation, provider)),
		})
		var typedNilHub *pairingCandidatePINControllerHubSpy
		oracleStep(&steps, "ConnectPairingCandidateWithPIN/typed-nil-hub", map[string]any{
			"error": oracleErr((&Service{connectionsHub: typedNilHub}).ConnectPairingCandidateWithPIN(reservation, provider)),
		})
		hub := &pairingCandidatePINControllerHubSpy{}
		var typedNilProvider *pairingCandidatePINProviderSpy
		err := (&Service{connectionsHub: hub}).ConnectPairingCandidateWithPIN(reservation, typedNilProvider)
		oracleStep(&steps, "ConnectPairingCandidateWithPIN/typed-nil-provider", map[string]any{
			"error": oracleErr(err), "error_is_provider_invalid": errors.Is(err, shipapi.ErrPINProviderInvalid), "hub_connects": len(hub.snapshotPINConnects()),
		})
	}
	oracleWrite(t, "service-go", "pairing-candidate-control", oracleCase{
		Component: "service/service.go (QueuePairingCandidate, SelectPairingCandidate, ConnectPairingCandidate, ConnectPairingCandidateWithPIN)",
		Source:    "service/service.go",
		Stimulus:  "service/pairing_candidate_red_test.go (every forwarding, failure and terminal-lifecycle test)",
		Input: oracleInput{Qualifiers: map[string]any{
			"candidate_ref": ref, "expected_ski": ski, "reservation_first_bytes": []any{"0x5a", "0x7b", "0x4c", "0x32", "0x66"},
		}},
		Output: oracleOutput{Decisions: steps},
	})
}

func oracleCalls(calls []pairingCandidateCall) []any {
	out := []any{}
	for _, call := range calls {
		out = append(out, map[string]any{"candidate_ref": call.ref, "expected_ski": call.ski})
	}
	return out
}

// oracleRecordTrustedRemoteRetry records RetryTrustedRemote.
func oracleRecordTrustedRemoteRetry(t *testing.T) {
	steps := []any{}
	{
		hub := &trustedRemoteRetryHubSpy{}
		err := (&Service{connectionsHub: hub}).RetryTrustedRemote(trustedRemoteRetryTestSKI)
		oracleStep(&steps, "RetryTrustedRemote", map[string]any{"error": oracleErr(err), "hub_calls": hub.snapshot()})
	}
	{
		wantErr := errors.New("retry rejected")
		hub := &trustedRemoteRetryHubSpy{err: wantErr}
		err := (&Service{connectionsHub: hub}).RetryTrustedRemote(trustedRemoteRetryTestSKI)
		oracleStep(&steps, "RetryTrustedRemote/hub-error", map[string]any{"error_is_hub_error": errors.Is(err, wantErr), "hub_calls": hub.snapshot()})
	}
	for _, item := range []struct {
		name string
		hub  shipapi.HubInterface
	}{{"missing hub", nil}, {"unsupported hub", &hubRuntimeRecorder{}}, {"typed nil retry hub", (*trustedRemoteRetryHubSpy)(nil)}} {
		err := (&Service{connectionsHub: item.hub}).RetryTrustedRemote(trustedRemoteRetryTestSKI)
		oracleStep(&steps, "RetryTrustedRemote/fails-closed", map[string]any{"hub": item.name, "error": oracleErr(err)})
	}
	for _, state := range []lifecycleState{lifecycleStopping, lifecycleStopped, lifecycleTerminal} {
		hub := &trustedRemoteRetryHubSpy{}
		err := (&Service{connectionsHub: hub, lifecycle: state}).RetryTrustedRemote(trustedRemoteRetryTestSKI)
		oracleStep(&steps, "RetryTrustedRemote/terminal-lifecycle", map[string]any{
			"lifecycle": oracleLifecycleName(state), "error_is_terminal": errors.Is(err, errTrustedRemoteRetryServiceTerminal), "hub_calls": hub.snapshot(),
		})
	}
	{
		hub := &trustedRemoteRetryHubSpy{shutdownEntered: make(chan struct{}), shutdownRelease: make(chan struct{})}
		sut := &Service{connectionsHub: hub, lifecycle: lifecycleRunning}
		done := make(chan struct{})
		go func() { sut.Shutdown(); close(done) }()
		<-hub.shutdownEntered
		err := sut.RetryTrustedRemote(trustedRemoteRetryTestSKI)
		calls := hub.snapshot()
		close(hub.shutdownRelease)
		<-done
		oracleStep(&steps, "RetryTrustedRemote/shutdown-in-progress", map[string]any{"error_is_terminal": errors.Is(err, errTrustedRemoteRetryServiceTerminal), "hub_calls": calls})
	}
	oracleWrite(t, "service-go", "trusted-remote-retry", oracleCase{
		Component: "service/service.go (Service.RetryTrustedRemote)",
		Source:    "service/service.go",
		Stimulus:  "service/trusted_remote_retry_red_test.go (every forwarding, failure and terminal-lifecycle test)",
		Input:     oracleInput{Qualifiers: map[string]any{"expected_ski": trustedRemoteRetryTestSKI}},
		Output:    oracleOutput{Decisions: steps},
	})
}
