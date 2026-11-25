package eebusruntime

import (
	"context"
	"encoding/json"
	"errors"
	"net/netip"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-eebusreg/eebusraw"
)

func oracleRecordRuntimeShape(t *testing.T) {
	runtimeType := reflect.TypeOf((*Runtime)(nil)).Elem()
	methods := []any{}
	for index := 0; index < runtimeType.NumMethod(); index++ {
		method := runtimeType.Method(index)
		methods = append(methods, map[string]any{"name": method.Name, "signature": method.Type.String()})
	}
	fields := func(value any) []any {
		out := []any{}
		typ := reflect.TypeOf(value)
		for index := 0; index < typ.NumField(); index++ {
			field := typ.Field(index)
			out = append(out, map[string]any{"name": field.Name, "type": field.Type.String(), "tag": string(field.Tag), "anonymous": field.Anonymous, "exported": field.PkgPath == ""})
		}
		return out
	}
	policyType := reflect.TypeOf(PairingPolicy(""))
	oracleWrite(t, "runtime-go", "public-shape", oracleCase{
		Component: "runtime.go (Runtime, Config, Remote, PairingPolicy, ErrRuntimeDisabled, ErrRuntimeShutdown)",
		Source:    "runtime.go",
		Stimulus:  "runtime_contract_test.go TestRuntimePublicLifecycleContractIsExact, TestRuntimeConfigurationUsesOnlyPlainTypes; runtime_configuration_contract_test.go TestRuntimeConfigurationPublicShapeIsExact",
		Input:     oracleInput{Qualifiers: map[string]any{"types": []any{"Runtime", "Config", "Remote", "PairingPolicy"}}},
		Output: oracleOutput{
			Observations: []any{
				map[string]any{"type": "Runtime", "kind": runtimeType.Kind().String(), "method_count": runtimeType.NumMethod(), "methods": methods},
				map[string]any{"type": "Config", "fields": fields(Config{})},
				map[string]any{"type": "Remote", "fields": fields(Remote{})},
				map[string]any{"type": "PairingPolicy", "kind": policyType.Kind().String(), "name": policyType.Name(), "package_path_present": policyType.PkgPath() != "", "closed_value": string(PairingPolicyClosed)},
				map[string]any{"error": "ErrRuntimeDisabled", "text": ErrRuntimeDisabled.Error()},
				map[string]any{"error": "ErrRuntimeShutdown", "text": ErrRuntimeShutdown.Error()},
			},
		},
	})
}

func oracleDisabledSequence(instance Runtime) []any {
	steps := []any{}
	oracleStep(&steps, "Start", map[string]any{"error": oracleErr(instance.Start(context.Background()))})
	_, snapshotErr := instance.Snapshot()
	oracleStep(&steps, "Snapshot", map[string]any{"error": oracleErr(snapshotErr), "is_ErrRuntimeDisabled": errors.Is(snapshotErr, ErrRuntimeDisabled)})
	_, pairingErr := instance.PairingState()
	oracleStep(&steps, "PairingState", map[string]any{"error": oracleErr(pairingErr), "is_ErrRuntimeDisabled": errors.Is(pairingErr, ErrRuntimeDisabled)})
	oracleStep(&steps, "Shutdown", map[string]any{"error": oracleErr(instance.Shutdown())})
	oracleStep(&steps, "Shutdown/repeated", map[string]any{"error": oracleErr(instance.Shutdown())})
	startErr := instance.Start(context.Background())
	oracleStep(&steps, "Start/after-terminal-shutdown", map[string]any{"error": oracleErr(startErr), "is_ErrRuntimeShutdown": errors.Is(startErr, ErrRuntimeShutdown)})
	return steps
}

func oracleRecordRuntimeDisabled(t *testing.T) {
	sandbox := t.TempDir()
	t.Setenv("HOME", sandbox)
	t.Setenv("XDG_CONFIG_HOME", filepath.Join(sandbox, "config"))
	t.Setenv("XDG_DATA_HOME", filepath.Join(sandbox, "data"))
	t.Setenv("XDG_STATE_HOME", filepath.Join(sandbox, "state"))

	var acquisitions atomic.Int32
	factory := runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
		acquisitions.Add(1)
		return newFakeRuntimeBackend(), nil
	})
	steps := []any{}
	internal, err := newRuntime(Config{}, factory)
	oracleStep(&steps, "newRuntime/zero-config", map[string]any{"error": oracleErr(err), "runtime_returned": internal != nil})
	for _, item := range oracleDisabledSequence(internal) {
		steps = append(steps, item)
	}
	public, err := New(Config{})
	oracleStep(&steps, "New/zero-config", map[string]any{"error": oracleErr(err), "runtime_returned": public != nil})
	for _, item := range oracleDisabledSequence(public) {
		steps = append(steps, item)
	}
	entries, _ := os.ReadDir(sandbox)
	oracleStep(&steps, "filesystem", map[string]any{"entries_created_in_sandbox": len(entries), "backend_acquisitions": acquisitions.Load()})

	mixed := []struct {
		name   string
		config Config
	}{
		{"state root", Config{StateRoot: filepath.Join(sandbox, "runtime-state")}},
		{"interface", Config{Interface: "en0"}},
		{"listen address", Config{ListenAddress: oracleV4(192, 0, 2, 10, 4711)}},
		{"discovery", Config{DiscoveryEnabled: true}},
		{"remotes", Config{Remotes: []Remote{{SKI: strings.Repeat("a", 40)}}}},
		{"pairing policy", Config{PairingPolicy: PairingPolicyClosed}},
	}
	for _, item := range mixed {
		var mixedAcquisitions atomic.Int32
		internal, internalErr := newRuntime(item.config, runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
			mixedAcquisitions.Add(1)
			return newFakeRuntimeBackend(), nil
		}))
		public, publicErr := New(item.config)
		oracleStep(&steps, "disabled-with-field-set", map[string]any{
			"field_set": item.name, "newRuntime_error": oracleErr(internalErr, sandbox), "newRuntime_runtime_returned": internal != nil,
			"New_error": oracleErr(publicErr, sandbox), "New_runtime_returned": public != nil, "backend_acquisitions": mixedAcquisitions.Load(),
		})
	}
	oracleWrite(t, "runtime-go", "disabled-runtime-is-inert", oracleCase{
		Component: "runtime.go (New, newRuntime and the disabled runtime)",
		Source:    "runtime.go",
		Stimulus:  "runtime_contract_test.go TestRuntimeDisabledDefaultRemainsInert; runtime_configuration_contract_test.go TestRuntimeConfigurationDisabledModeIsStrictlyInert; runtime_lifecycle_test.go TestRuntimeDisabledNeverAcquiresBackend",
		Input: oracleInput{
			Qualifiers: map[string]any{
				"config": oracleConfig(Config{}), "environment": "HOME and the XDG directories point at an empty sandbox",
				"mixed_configs": []any{"state root", "interface", "listen address", "discovery", "remotes", "pairing policy"},
			},
		},
		Output: oracleOutput{Decisions: steps},
	})
}

func oracleInvalidMutations() []struct {
	name   string
	mutate func(*Config)
} {
	return []struct {
		name   string
		mutate func(*Config)
	}{
		{"missing state root", func(config *Config) { config.StateRoot = "" }},
		{"relative state root", func(config *Config) { config.StateRoot = "relative/state" }},
		{"filesystem root", func(config *Config) { config.StateRoot = string(filepath.Separator) }},
		{"missing interface", func(config *Config) { config.Interface = "" }},
		{"whitespace interface", func(config *Config) { config.Interface = "  " }},
		{"star interface", func(config *Config) { config.Interface = "*" }},
		{"ipv4 wildcard interface", func(config *Config) { config.Interface = oracleWildcardInterface() }},
		{"ipv6 wildcard interface", func(config *Config) { config.Interface = "::" }},
		{"bracketed ipv6 wildcard interface", func(config *Config) { config.Interface = "[::]" }},
		{"zero endpoint", func(config *Config) { config.ListenAddress = netip.AddrPort{} }},
		{"invalid address", func(config *Config) { config.ListenAddress = netip.AddrPortFrom(netip.Addr{}, 4711) }},
		{"zero port", func(config *Config) { config.ListenAddress = oracleV4(192, 0, 2, 10, 0) }},
		{"unspecified ipv4", func(config *Config) { config.ListenAddress = oracleV4(0, 0, 0, 0, 4711) }},
		{"unspecified ipv6", func(config *Config) { config.ListenAddress = netip.MustParseAddrPort("[::]:4711") }},
		{"ipv4 multicast", func(config *Config) { config.ListenAddress = oracleV4(224, 0, 0, 1, 4711) }},
		{"ipv6 multicast", func(config *Config) { config.ListenAddress = netip.MustParseAddrPort("[ff02::1]:4711") }},
		{"ipv4 zero network", func(config *Config) { config.ListenAddress = oracleV4(0, 1, 2, 3, 4711) }},
		{"limited broadcast", func(config *Config) { config.ListenAddress = oracleV4(255, 255, 255, 255, 4711) }},
		{"ipv4 mapped ipv6", func(config *Config) { config.ListenAddress = netip.AddrPortFrom(netip.AddrFrom16([16]byte{10: 0xff, 11: 0xff, 12: 192, 13: 0, 14: 2, 15: 10}), 4711) }},
		{"missing pairing policy", func(config *Config) { config.PairingPolicy = "" }},
		{"open pairing policy", func(config *Config) { config.PairingPolicy = PairingPolicy("open") }},
		{"noncanonical closed policy", func(config *Config) { config.PairingPolicy = PairingPolicy(" closed ") }},
	}
}

func oracleRecordRuntimeConfigValidation(t *testing.T) {
	sandbox := t.TempDir()
	stateRoot := filepath.Join(sandbox, "runtime-state")
	valid := validCleanupRuntimeConfig(stateRoot, false, nil)

	rejections := []any{}
	for _, item := range oracleInvalidMutations() {
		config := valid
		item.mutate(&config)
		var acquisitions atomic.Int32
		factory := runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
			acquisitions.Add(1)
			return newFakeRuntimeBackend(), nil
		})
		internal, internalErr := newRuntime(config, factory)
		public, publicErr := New(config)
		_, statErr := os.Lstat(stateRoot)
		rejections = append(rejections, map[string]any{
			"mutation": item.name, "config": oracleConfig(config),
			"newRuntime_error": oracleErr(internalErr, sandbox), "newRuntime_runtime_returned": internal != nil,
			"New_error": oracleErr(publicErr, sandbox), "New_runtime_returned": public != nil,
			"backend_acquisitions": acquisitions.Load(), "state_root_touched": statErr == nil,
		})
	}
	legacy := validRuntimeConfig(stateRoot)
	legacyMutations := []struct {
		name   string
		mutate func(*Config)
	}{
		{"missing state root", func(config *Config) { config.StateRoot = "" }},
		{"missing interface", func(config *Config) { config.Interface = "" }},
		{"missing listen address", func(config *Config) { config.ListenAddress = netip.AddrPort{} }},
		{"missing pairing policy", func(config *Config) { config.PairingPolicy = "" }},
		{"missing remote ski", func(config *Config) { config.Remotes[0].SKI = "" }},
		{"duplicate remote", func(config *Config) { config.Remotes = append(config.Remotes, config.Remotes[0]) }},
	}
	for _, item := range legacyMutations {
		config := legacy
		config.Remotes = append([]Remote(nil), legacy.Remotes...)
		item.mutate(&config)
		public, err := New(config)
		_, statErr := os.Lstat(stateRoot)
		rejections = append(rejections, map[string]any{
			"mutation": "fixture B: " + item.name, "config": oracleConfig(config),
			"New_error": oracleErr(err, sandbox), "New_runtime_returned": public != nil, "state_root_touched": statErr == nil,
		})
	}
	oracleWrite(t, "runtime-go", "enabled-config-rejections", oracleCase{
		Component: "runtime.go (New, newRuntime, normalizeRuntimeConfig, validateRuntimeListenAddress, normalizeRuntimeRemote)",
		Source:    "runtime.go",
		Stimulus:  "runtime_configuration_contract_test.go TestRuntimeConfigurationEnabledValidationIsPureAndExact; runtime_contract_test.go TestRuntimeEnabledNewValidatesWithoutIO",
		Input: oracleInput{Qualifiers: map[string]any{
			"base_config_A": oracleConfig(valid), "base_config_B": oracleConfig(legacy),
			"state_root_note": "a fresh path under an empty sandbox; the sandbox path is replaced by <sandbox> in error texts",
		}},
		Output: oracleOutput{Decisions: rejections},
	})

	accepted := []any{}
	for _, endpoint := range []netip.AddrPort{oracleV4(192, 0, 2, 10, 4711), netip.MustParseAddrPort("[2001:db8::10]:4711")} {
		for _, discovery := range []bool{false, true} {
			config := validCleanupRuntimeConfig(stateRoot, discovery, nil)
			config.ListenAddress = endpoint
			var acquisitions atomic.Int32
			internal, err := newRuntime(config, runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
				acquisitions.Add(1)
				return newFakeRuntimeBackend(), nil
			}))
			record := map[string]any{"config": oracleConfig(config), "newRuntime_error": oracleErr(err, sandbox), "acquisitions_after_construction": acquisitions.Load()}
			if err == nil {
				record["shutdown_error"] = oracleErr(internal.Shutdown(), sandbox)
			}
			public, err := New(config)
			record["New_error"] = oracleErr(err, sandbox)
			if err == nil {
				record["New_shutdown_error"] = oracleErr(public.Shutdown(), sandbox)
			}
			_, statErr := os.Lstat(stateRoot)
			record["state_root_touched"] = statErr == nil
			accepted = append(accepted, record)
		}
	}
	{
		instance, err := New(legacy)
		record := map[string]any{"config": oracleConfig(legacy), "New_error": oracleErr(err, sandbox)}
		if err == nil {
			record["Shutdown_before_Start_error"] = oracleErr(instance.Shutdown(), sandbox)
		}
		_, statErr := os.Lstat(stateRoot)
		record["state_root_touched"] = statErr == nil
		accepted = append(accepted, record)
	}
	oracleWrite(t, "runtime-go", "enabled-config-accepted-without-io", oracleCase{
		Component: "runtime.go (New, newRuntime with a valid enabled configuration)",
		Source:    "runtime.go",
		Stimulus:  "runtime_configuration_contract_test.go TestRuntimeConfigurationEnabledValidationIsPureAndExact (valid endpoints); runtime_contract_test.go TestRuntimeEnabledNewValidatesWithoutIO",
		Input:     oracleInput{Qualifiers: map[string]any{"endpoints": []any{oracleEndpoint(oracleV4(192, 0, 2, 10, 4711)), oracleEndpoint(netip.MustParseAddrPort("[2001:db8::10]:4711"))}, "discovery": []any{false, true}}},
		Output:    oracleOutput{Decisions: accepted},
	})
}

func oracleRecordRuntimeRemotes(t *testing.T) {
	stateRoot := filepath.Join(t.TempDir(), "runtime-state")
	valid := validCleanupRuntimeConfig(stateRoot, true, nil)
	steps := []any{}
	invalid := []struct {
		name    string
		remotes []Remote
	}{
		{"missing SKI", []Remote{{}}},
		{"short SKI", []Remote{{SKI: strings.Repeat("a", 39)}}},
		{"non hexadecimal SKI", []Remote{{SKI: strings.Repeat("z", 40)}}},
		{"normalized duplicate", []Remote{{SKI: " AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA "}, {SKI: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}},
	}
	for _, item := range invalid {
		config := valid
		config.Remotes = item.remotes
		var acquisitions atomic.Int32
		internal, internalErr := newRuntime(config, runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
			acquisitions.Add(1)
			return newFakeRuntimeBackend(), nil
		}))
		public, publicErr := New(config)
		oracleStep(&steps, "reject", map[string]any{
			"remotes": item.name, "newRuntime_error": oracleErr(internalErr), "newRuntime_runtime_returned": internal != nil,
			"New_error": oracleErr(publicErr), "New_runtime_returned": public != nil, "backend_acquisitions": acquisitions.Load(),
		})
	}

	input := []Remote{{SKI: " AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA "}, {SKI: "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"}}
	config := validCleanupRuntimeConfig(stateRoot, true, input)
	firstAttempt := errors.New("fixture first acquisition failed")
	backend := newFakeRuntimeBackend()
	received := make(chan Config, 2)
	var attempts atomic.Int32
	instance, err := newRuntime(config, runtimeBackendFactory(func(_ context.Context, got Config) (runtimeBackend, error) {
		captured := got
		captured.Remotes = append([]Remote(nil), got.Remotes...)
		received <- captured
		if attempts.Add(1) == 1 {
			got.Remotes[0].SKI = strings.Repeat("f", 40)
			return nil, firstAttempt
		}
		return backend, nil
	}))
	if err != nil {
		t.Fatal(err)
	}
	constructionAcquisitions := attempts.Load()
	input[0].SKI = strings.Repeat("0", 40)
	config.Remotes[1].SKI = strings.Repeat("1", 40)
	firstErr := instance.Start(context.Background())
	first := <-received
	secondErr := instance.Start(context.Background())
	second := <-received
	waitRuntimeSignal(t, backend.runStarted, "v1 backend Run")
	shutdownErr := instance.Shutdown()
	oracleStep(&steps, "normalize-and-copy", map[string]any{
		"input_remotes": []any{" AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA ", "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"},
		"acquisitions_after_construction": constructionAcquisitions, "first_Start_error_is_fixture_failure": errors.Is(firstErr, firstAttempt),
		"first_backend_config": oracleConfig(first), "second_Start_error": oracleErr(secondErr), "second_backend_config": oracleConfig(second),
		"Shutdown_error": oracleErr(shutdownErr),
	})
	for _, discovery := range []bool{false, true} {
		backend := newFakeRuntimeBackend()
		captured := make(chan Config, 1)
		config := validCleanupRuntimeConfig(filepath.Join(t.TempDir(), "state"), discovery, []Remote{})
		instance, err := newRuntime(config, runtimeBackendFactory(func(_ context.Context, got Config) (runtimeBackend, error) {
			captured <- got
			return backend, nil
		}))
		record := map[string]any{"discovery_enabled": discovery, "newRuntime_error": oracleErr(err)}
		if err == nil {
			record["Start_error"] = oracleErr(instance.Start(context.Background()))
			got := <-captured
			record["backend_remote_count"] = len(got.Remotes)
			record["backend_discovery_enabled"] = got.DiscoveryEnabled
			waitRuntimeSignal(t, backend.runStarted, "empty-allowlist backend Run")
			record["Shutdown_error"] = oracleErr(instance.Shutdown())
		}
		oracleStep(&steps, "empty-remotes", record)
	}
	oracleWrite(t, "runtime-go", "remotes-normalized-rejected-and-copied", oracleCase{
		Component: "runtime.go (normalizeRuntimeRemote, cloneRuntimeConfig, Start backend configuration)",
		Source:    "runtime.go",
		Stimulus:  "runtime_configuration_contract_test.go TestRuntimeConfigurationRemotesNormalizeRejectAndRemainDefensivelyCopied",
		Input:     oracleInput{Qualifiers: map[string]any{"base_config": oracleConfig(valid), "invalid_remotes": []any{"missing SKI", "short SKI", "non hexadecimal SKI", "normalized duplicate"}}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordRuntimeLifecycle(t *testing.T) {
	steps := []any{}
	{
		backend := newFakeRuntimeBackend()
		var acquisitions atomic.Int32
		var wrongConfig atomic.Bool
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), runtimeBackendFactory(func(_ context.Context, config Config) (runtimeBackend, error) {
			acquisitions.Add(1)
			if config.Interface != "test-interface" || len(config.Remotes) != 1 {
				wrongConfig.Store(true)
			}
			return backend, nil
		}))
		if err != nil {
			t.Fatal(err)
		}
		cancelled, cancel := context.WithCancel(context.Background())
		cancel()
		canceledErr := instance.Start(cancelled)
		afterCanceled := acquisitions.Load()
		startErrors := callRuntimeConcurrently(t, 32, "concurrent Start", func() error { return instance.Start(context.Background()) })
		startFailures := 0
		for err := range startErrors {
			if err != nil {
				startFailures++
			}
		}
		waitRuntimeSignal(t, backend.runStarted, "backend Run")
		first := lifecycleRuntimeSnapshot(t, "session-before-reconnect")
		backend.publish(t, first)
		(*first.Pairing[0].Opaque)[0].Path = "/source-mutation"
		(*first.Services[0].Opaque)[0].Path = "/source-mutation"
		afterFirst, _ := instance.Snapshot()
		computed, _ := afterFirst.ComputeDataHash()
		second := lifecycleRuntimeSnapshot(t, "session-after-reconnect")
		backend.publish(t, second)
		afterSecond, _ := instance.Snapshot()
		terminalDraft := second.Clone()
		terminalDraft.Pairing[0].State = eebusraw.PairingStateDenied
		terminalDraft.Services[0].Paired = false
		terminalDraft.Status = RuntimeObservationV1{State: ObservedRuntimeStateV1Degraded, Degradation: &DegradationV1{Reason: DegradationReasonV1DeniedTrust, Since: terminalDraft.Meta.DataTimestamp}}
		terminalDraft.Meta.DataHash = ""
		terminalSnapshot, err := NewSnapshotV1(terminalDraft)
		if err != nil {
			t.Fatal(err)
		}
		backend.setTerminalSnapshot(terminalSnapshot)
		shutdownFailures := 0
		for err := range callRuntimeConcurrently(t, 32, "concurrent Shutdown", instance.Shutdown) {
			if err != nil {
				shutdownFailures++
			}
		}
		waitRuntimeSignal(t, backend.cancelled, "backend cancellation")
		waitRuntimeSignal(t, backend.runExited, "backend join")
		afterShutdownStart := instance.Start(context.Background())
		terminal, terminalErr := instance.Snapshot()
		oracleStep(&steps, "concurrent-start-and-shutdown", map[string]any{
			"Start_with_canceled_context_error": oracleErr(canceledErr), "is_context_canceled": errors.Is(canceledErr, context.Canceled),
			"acquisitions_after_canceled_Start": afterCanceled, "concurrent_Start_calls": 32, "concurrent_Start_failures": startFailures,
			"backend_acquisitions": acquisitions.Load(), "backend_Run_calls": backend.runCalls.Load(), "backend_received_validated_config": !wrongConfig.Load(),
			"snapshot_after_first_publication": oracleSnapshotFacts(afterFirst), "snapshot_hash_intact_after_source_mutation": computed == afterFirst.Meta.DataHash,
			"snapshot_after_reconnect": oracleSnapshotFacts(afterSecond),
			"concurrent_Shutdown_calls": 32, "concurrent_Shutdown_failures": shutdownFailures, "backend_Close_calls": backend.closeCalls.Load(),
			"Start_after_Shutdown_error": oracleErr(afterShutdownStart), "is_ErrRuntimeShutdown": errors.Is(afterShutdownStart, ErrRuntimeShutdown),
			"terminal_snapshot_error": oracleErr(terminalErr), "terminal_snapshot": oracleSnapshotFacts(terminal),
		})
	}
	{
		backend := newFakeRuntimeBackend()
		entered := make(chan struct{})
		release := make(chan struct{})
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
			close(entered)
			<-release
			return backend, nil
		}))
		if err != nil {
			t.Fatal(err)
		}
		firstResult := make(chan error, 1)
		go func() { firstResult <- instance.Start(context.Background()) }()
		waitRuntimeSignal(t, entered, "first backend acquisition")
		waiterCtx, cancelWaiter := context.WithCancel(context.Background())
		waiterResult := make(chan error, 1)
		go func() { waiterResult <- instance.Start(waiterCtx) }()
		cancelWaiter()
		waiterErr := waitRuntimeResult(t, waiterResult, "canceled Start waiter")
		firstReturnedEarly := false
		select {
		case <-firstResult:
			firstReturnedEarly = true
		default:
		}
		close(release)
		firstErr := waitRuntimeResult(t, firstResult, "first Start")
		waitRuntimeSignal(t, backend.runStarted, "backend Run")
		shutdownErr := instance.Shutdown()
		oracleStep(&steps, "concurrent-start-waiter-cancels-independently", map[string]any{
			"waiter_error": oracleErr(waiterErr), "waiter_is_context_canceled": errors.Is(waiterErr, context.Canceled), "first_Start_returned_before_acquisition_completed": firstReturnedEarly,
			"first_Start_error": oracleErr(firstErr), "Shutdown_error": oracleErr(shutdownErr),
		})
	}
	{
		var acquisitions atomic.Int32
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
			acquisitions.Add(1)
			return newFakeRuntimeBackend(), nil
		}))
		if err != nil {
			t.Fatal(err)
		}
		failures := 0
		for err := range callRuntimeConcurrently(t, 16, "pre-start Shutdown", instance.Shutdown) {
			if err != nil {
				failures++
			}
		}
		startErr := instance.Start(context.Background())
		oracleStep(&steps, "shutdown-before-start-is-terminal", map[string]any{
			"Shutdown_calls": 16, "Shutdown_failures": failures, "backend_acquisitions": acquisitions.Load(),
			"Start_after_Shutdown_error": oracleErr(startErr), "is_ErrRuntimeShutdown": errors.Is(startErr, ErrRuntimeShutdown),
		})
	}
	{
		backend := newFakeRuntimeBackend()
		denied := errors.New("fixture runtime admission denied")
		var acquisitions atomic.Int32
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) {
			if acquisitions.Add(1) == 1 {
				return nil, denied
			}
			return backend, nil
		}))
		if err != nil {
			t.Fatal(err)
		}
		firstErr := instance.Start(context.Background())
		runCallsAfterDenial := backend.runCalls.Load()
		secondErr := instance.Start(context.Background())
		waitRuntimeSignal(t, backend.runStarted, "backend Run after admission")
		oracleStep(&steps, "pretrust-denial-does-not-launch-or-latch-started", map[string]any{
			"first_Start_is_denial": errors.Is(firstErr, denied), "backend_Run_calls_after_denial": runCallsAfterDenial, "second_Start_error": oracleErr(secondErr),
			"backend_acquisitions": acquisitions.Load(), "Shutdown_error": oracleErr(instance.Shutdown()),
		})
	}
	{
		backend := newFakeRuntimeBackend()
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), runtimeBackendFactory(func(context.Context, Config) (runtimeBackend, error) { return backend, nil }))
		if err != nil {
			t.Fatal(err)
		}
		if err := instance.Start(context.Background()); err != nil {
			t.Fatal(err)
		}
		waitRuntimeSignal(t, backend.runStarted, "backend Run")
		backend.publish(t, lifecycleRuntimeSnapshot(t, "detached-session"))
		first, _ := instance.Snapshot()
		wantHash := first.Meta.DataHash
		(*first.Pairing[0].Opaque)[0].Path = "/caller-mutation"
		(*first.Services[0].Opaque)[0].Path = "/caller-mutation"
		first.Features = nil
		first.Opaque[0].Path = "/caller-mutation"
		pairing, _ := instance.PairingState()
		(*pairing[0].Opaque)[0].Path = "/pairing-mutation"
		again, _ := instance.Snapshot()
		computed, _ := again.ComputeDataHash()
		pairingAgain, _ := instance.PairingState()
		oracleStep(&steps, "snapshot-and-pairing-results-are-detached", map[string]any{
			"hash_before_caller_mutation": wantHash, "hash_after_caller_mutation": again.Meta.DataHash, "computed_hash_equals_stored_hash": computed == wantHash && again.Meta.DataHash == wantHash,
			"feature_count_after_caller_cleared_features": len(again.Features), "pairing_state_count": len(pairingAgain),
			"pairing_opaque_retained": len(pairingAgain) == 1 && pairingAgain[0].Opaque != nil && len(*pairingAgain[0].Opaque) == 1,
			"snapshot": oracleSnapshotFacts(again),
		})
		_ = instance.Shutdown()
	}
	oracleWrite(t, "runtime-go", "lifecycle-start-snapshot-shutdown", oracleCase{
		Component: "runtime.go (runtimeImplementation.Start, Shutdown, Snapshot, PairingState, publishSnapshot, freezeTerminalSnapshotLocked)",
		Source:    "runtime.go",
		Stimulus:  "runtime_lifecycle_test.go TestRuntimeConcurrentLifecycleAcquiresOnceCancelsJoinsAndClosesOnce, TestRuntimeConcurrentStartWaiterCanCancelIndependently, TestRuntimeShutdownBeforeStartIsTerminalWithoutAcquisition, TestRuntimeStartPretrustDenialDoesNotLaunchOrLatchStarted, TestRuntimeSnapshotAndPairingResultsAreDeeplyDetached",
		Input: oracleInput{
			Qualifiers: map[string]any{
				"config": oracleConfig(validRuntimeConfig("<state-root>")), "backend": "the pin's scripted runtime backend and its synthetic snapshots (session-before-reconnect, session-after-reconnect, detached-session)",
				"concurrency": map[string]any{"Start_calls": 32, "Shutdown_calls": 32, "pre_start_Shutdown_calls": 16},
			},
		},
		Output: oracleOutput{Decisions: steps},
	})
}

func oracleRecordRuntimeFailures(t *testing.T) {
	steps := []any{}
	{
		backend := newFakeRuntimeBackend()
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), func(context.Context, Config) (runtimeBackend, error) { return backend, nil })
		if err != nil {
			t.Fatal(err)
		}
		_ = instance.Start(context.Background())
		waitRuntimeSignal(t, backend.runStarted, "backend Run")
		backend.publish(t, lifecycleRuntimeSnapshot(t, "before-worker-failure"))
		runErr := errors.New("fixture backend Run failed")
		backend.fail(t, runErr)
		waitRuntimeWorkerExit(t, instance)
		_, snapshotErr := instance.Snapshot()
		startErr := instance.Start(context.Background())
		shutdownErr := instance.Shutdown()
		oracleStep(&steps, "backend-Run-error", map[string]any{
			"Snapshot_is_backend_failure": errors.Is(snapshotErr, runErr), "Start_is_backend_failure": errors.Is(startErr, runErr), "Shutdown_is_backend_failure": errors.Is(shutdownErr, runErr),
			"Snapshot_error": oracleErr(snapshotErr), "backend_Close_calls": backend.closeCalls.Load(),
		})
	}
	{
		backend := newFakeRuntimeBackend()
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), func(context.Context, Config) (runtimeBackend, error) { return backend, nil })
		if err != nil {
			t.Fatal(err)
		}
		_ = instance.Start(context.Background())
		waitRuntimeSignal(t, backend.runStarted, "backend Run")
		backend.publish(t, lifecycleRuntimeSnapshot(t, "before-invalid-publication"))
		invalid := lifecycleRuntimeSnapshot(t, "invalid-publication")
		invalid.Meta.Contract = ""
		backend.publish(t, invalid)
		waitRuntimeWorkerExit(t, instance)
		_, snapshotErr := instance.Snapshot()
		shutdownErr := instance.Shutdown()
		oracleStep(&steps, "invalid-publication", map[string]any{
			"Snapshot_error_names_publication": snapshotErr != nil && strings.Contains(snapshotErr.Error(), "publish runtime snapshot"),
			"Shutdown_error_names_publication": shutdownErr != nil && strings.Contains(shutdownErr.Error(), "publish runtime snapshot"), "backend_Close_calls": backend.closeCalls.Load(),
			"Snapshot_error": oracleErr(snapshotErr),
		})
	}
	{
		backend := &facadeRuntimeBackend{backend: malformedFacadeBackend{}}
		published := 0
		err := backend.Run(context.Background(), func(SnapshotV1) { published++ })
		oracleStep(&steps, "facadeRuntimeBackend/malformed-internal-payload", map[string]any{
			"error_names_decode": err != nil && strings.Contains(err.Error(), "decode internal runtime snapshot"), "error": oracleErr(err), "snapshots_published": published,
		})
	}
	{
		backend := newCloseReleasedRuntimeBackend()
		instance, err := newRuntime(validRuntimeConfig(t.TempDir()), func(context.Context, Config) (runtimeBackend, error) { return backend, nil })
		if err != nil {
			t.Fatal(err)
		}
		_ = instance.Start(context.Background())
		waitRuntimeSignal(t, backend.runStarted, "cancellation-ignoring backend Run")
		failures := 0
		for err := range callRuntimeConcurrently(t, 16, "cancellation-ignoring Shutdown", instance.Shutdown) {
			if err != nil {
				failures++
			}
		}
		waitRuntimeSignal(t, backend.runExited, "backend exit after Close")
		oracleStep(&steps, "shutdown-closes-backend-before-joining-cancellation-ignoring-Run", map[string]any{
			"Shutdown_calls": 16, "Shutdown_failures": failures, "backend_Close_calls": backend.closeCalls.Load(),
		})
	}
	{
		terminalDraft := lifecycleRuntimeSnapshot(t, "terminal-close-capture")
		terminalDraft.Pairing[0].State = eebusraw.PairingStateDenied
		terminalDraft.Services[0].Paired = false
		terminalDraft.Meta.DataHash = ""
		terminal, err := NewSnapshotV1(terminalDraft)
		if err != nil {
			t.Fatal(err)
		}
		payload, err := json.Marshal(terminal)
		if err != nil {
			t.Fatal(err)
		}
		inner := &closePublishingFacadeBackend{started: make(chan struct{}), payload: payload}
		backend := &facadeRuntimeBackend{backend: inner}
		ctx, cancel := context.WithCancel(context.Background())
		runResult := make(chan error, 1)
		go func() { runResult <- backend.Run(ctx, func(SnapshotV1) {}) }()
		waitRuntimeSignal(t, inner.started, "facade backend run")
		cancel()
		runErr := waitRuntimeResult(t, runResult, "facade backend cancellation")
		closeErr := backend.Close()
		captured, ok := backend.TerminalSnapshot()
		record := map[string]any{"Run_error_is_context_canceled": errors.Is(runErr, context.Canceled), "Close_error": oracleErr(closeErr), "terminal_snapshot_captured": ok}
		if ok {
			record["terminal_snapshot"] = oracleSnapshotFacts(captured)
		}
		oracleStep(&steps, "facadeRuntimeBackend/captures-close-terminal-state", record)
	}
	oracleWrite(t, "runtime-go", "backend-failure-and-terminal-capture", oracleCase{
		Component: "runtime.go (runBackend, publishSnapshot, retainWorkerErrorLocked, facadeRuntimeBackend.Run, Close, TerminalSnapshot)",
		Source:    "runtime.go",
		Stimulus:  "runtime_lifecycle_test.go TestRuntimeRunErrorStopsLiveSuccessAndIsReturnedByShutdown, TestRuntimeInvalidPublicationBecomesWorkerError, TestFacadeRuntimeBackendRejectsMalformedInternalPayload, TestRuntimeShutdownClosesBackendBeforeJoiningCancellationIgnoringRun, TestFacadeRuntimeBackendCapturesCloseTerminalState",
		Input:     oracleInput{Qualifiers: map[string]any{"config": oracleConfig(validRuntimeConfig("<state-root>")), "backend": "the pin's scripted runtime backend, malformed payload backend and close-publishing backend"}},
		Output:    oracleOutput{Decisions: steps},
	})
}

var _ = strconv.Itoa
var _ = time.Second
