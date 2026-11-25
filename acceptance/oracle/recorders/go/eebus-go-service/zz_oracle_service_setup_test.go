package service

import (
	"crypto/tls"
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-eebus-go/api"
	shipapi "github.com/Project-Helianthus/helianthus-ship-go/api"
	"github.com/Project-Helianthus/helianthus-ship-go/cert"
	spinemodel "github.com/Project-Helianthus/helianthus-spine-go/model"
)

func oracleHubFactory(hub shipapi.HubInterface, calls *int) func(
	shipapi.HubReaderInterface, shipapi.MdnsInterface, int, tls.Certificate, *shipapi.ServiceDetails,
) shipapi.HubInterface {
	return func(shipapi.HubReaderInterface, shipapi.MdnsInterface, int, tls.Certificate, *shipapi.ServiceDetails) shipapi.HubInterface {
		*calls++
		return hub
	}
}

// oracleRecordSetup records service.go Setup: the device address of the SPINE
// device and the failures before a hub is built (Test_Setup, Test_Setup_IANA,
// Test_Setup_Error_DeviceName).
func oracleRecordSetup(t *testing.T) {
	configurations := []struct {
		name, vendor, brand, model, serial string
	}{
		{"vendor-not-numeric", "vendor", "brand", "model", "serial"},
		{"vendor-numeric-iana", "12345", "brand", "model", "serial"},
		{
			"device-address-longer-than-256",
			"1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
			"brand",
			"modelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodelmodel",
			"serialserialserialserialserialserialserialserialserialserialserialserialserialserialserialserialserial",
		},
	}
	steps := []any{}
	for _, item := range configurations {
		configuration, err := api.NewConfiguration(item.vendor, item.brand, item.model, item.serial,
			spinemodel.DeviceTypeTypeEnergyManagementSystem, []spinemodel.EntityTypeType{spinemodel.EntityTypeTypeCEM},
			4729, tls.Certificate{}, 4*time.Second)
		if err != nil {
			t.Fatal(err)
		}
		sut := NewService(configuration, &pairingCandidateVisibilityReader{})
		factoryCalls := 0
		sut.connectionsHubFactory = oracleHubFactory(&pairingRegistrationHubSpy{}, &factoryCalls)
		withoutCertificate := sut.Setup()
		oracleStep(&steps, "Setup/without-certificate", map[string]any{
			"configuration": item.name, "error": oracleErr(withoutCertificate), "lifecycle": oracleState(sut), "factory_calls": factoryCalls,
		})
		certificate, err := cert.CreateCertificate("unit", "org", "de", "cn")
		if err != nil {
			t.Fatal(err)
		}
		configuration.SetCertificate(certificate)
		withCertificate := sut.Setup()
		record := map[string]any{
			"configuration": item.name, "error": oracleErr(withCertificate), "lifecycle": oracleState(sut), "factory_calls": factoryCalls,
		}
		if withCertificate == nil {
			record["spine_device_address"] = string(*sut.LocalDevice().Address())
			record["spine_entity_count"] = len(sut.LocalDevice().Entities())
			record["local_service_ski_length"] = len(sut.LocalService().SKI())
			record["local_service_ship_id"] = sut.LocalService().ShipID()
			record["local_service_device_type"] = sut.LocalService().DeviceType()
			record["hub_published"] = sut.connectionsHub != nil
			record["auto_accept"] = sut.IsAutoAcceptEnabled()
			record["configuration_identifier"] = sut.Configuration().Identifier()
		}
		oracleStep(&steps, "Setup/with-certificate", record)
	}
	factoryOnly := &Service{}
	oracleStep(&steps, "Setup/missing-factory", map[string]any{"error": oracleErr(factoryOnly.Setup())})
	oracleWrite(t, "service-go", "setup-device-address-and-failures", oracleCase{
		Component: "service/service.go (Service.Setup, NewService)",
		Source:    "service/service.go",
		Stimulus:  "service/service_test.go Test_Setup, Test_Setup_IANA, Test_Setup_Error_DeviceName; service/listener_policy_test.go TestLegacySetupChecksMissingFactoryBeforeConfiguration",
		Input: oracleInput{Qualifiers: map[string]any{
			"configurations": []any{"vendor,brand,model,serial", "12345,brand,model,serial", "100-char vendor, brand, 100-char model, 102-char serial"},
			"port":           4729, "heartbeat_timeout_ns": int64(4 * time.Second),
			"certificate": "generated per run by the pin's certificate helper; only its presence is an input",
		}},
		Output: oracleOutput{Decisions: steps},
	})
}

// oracleRecordPairingRegistration records SetPairingRegistration,
// AllowWaitingForTrust and the registration order seen by the hub.
func oracleRecordPairingRegistration(t *testing.T) {
	newService := func() *Service {
		configuration, err := api.NewConfiguration("vendor", "brand", "model", "serial",
			spinemodel.DeviceTypeTypeEnergyManagementSystem, []spinemodel.EntityTypeType{spinemodel.EntityTypeTypeCEM},
			4729, tls.Certificate{}, 4*time.Second)
		if err != nil {
			t.Fatal(err)
		}
		certificate, err := cert.CreateCertificate("unit", "org", "de", "cn")
		if err != nil {
			t.Fatal(err)
		}
		configuration.SetCertificate(certificate)
		return NewService(configuration, &pairingCandidateVisibilityReader{})
	}
	steps := []any{}

	{
		sut := newService()
		hub := &pairingRegistrationHubSpy{}
		calls := 0
		sut.connectionsHubFactory = oracleHubFactory(hub, &calls)
		err := sut.Setup()
		oracleStep(&steps, "Setup/default-registration", map[string]any{
			"error": oracleErr(err), "hub_values": hub.Values(), "allow_waiting_for_trust": sut.AllowWaitingForTrust("remote"),
			"auto_accept": sut.IsAutoAcceptEnabled(),
		})
	}
	{
		sut := newService()
		hub := &pairingRegistrationHubSpy{}
		calls := 0
		sut.connectionsHubFactory = oracleHubFactory(hub, &calls)
		before := sut.SetPairingRegistration(true)
		err := sut.Setup()
		oracleStep(&steps, "SetPairingRegistration-before-Setup/true", map[string]any{
			"registration_error": oracleErr(before), "setup_error": oracleErr(err), "hub_values": hub.Values(),
		})
	}
	{
		sut := newService()
		hub := &pairingRegistrationHubSpy{}
		sut.connectionsHub = hub
		sut.localService = shipapi.NewServiceDetails("local-ski")
		first := sut.SetPairingRegistration(true)
		afterFirst := hub.Values()
		second := sut.SetPairingRegistration(false)
		oracleStep(&steps, "SetPairingRegistration/advertises-without-auto-accept", map[string]any{
			"errors": []any{oracleErr(first), oracleErr(second)}, "hub_values_after_first": afterFirst, "hub_values": hub.Values(), "auto_accept": sut.IsAutoAcceptEnabled(),
		})
	}
	{
		sut := newService()
		hub := &pairingRegistrationHubSpy{err: errors.New("announce failed")}
		sut.connectionsHub = hub
		err := sut.SetPairingRegistration(true)
		oracleStep(&steps, "SetPairingRegistration/hub-error", map[string]any{
			"error": oracleErr(err), "hub_values": hub.Values(), "error_is_hub_error": errors.Is(err, hub.err),
		})
	}
	{
		sut := newService()
		calls := 0
		sut.connectionsHubFactory = oracleHubFactory(&oracleBareHub{}, &calls)
		oracleStep(&steps, "Setup/hub-without-registration-capability", map[string]any{
			"error": oracleErr(sut.Setup()), "lifecycle": oracleState(sut), "hub_published": sut.connectionsHub != nil,
		})
	}
	{
		sut := newService()
		hub := &pairingRegistrationHubSpy{}
		calls := 0
		sut.connectionsHubFactory = oracleHubFactory(hub, &calls)
		_ = sut.SetPairingRegistration(true)
		entered := make(chan struct{})
		release := make(chan struct{})
		hub.entered = entered
		hub.release = release
		setupDone := make(chan error, 1)
		go func() { setupDone <- sut.Setup() }()
		select {
		case <-entered:
		case <-time.After(2 * time.Second):
			t.Fatal("setup did not reach pairing registration")
		}
		updateDone := make(chan error, 1)
		go func() { updateDone <- sut.SetPairingRegistration(false) }()
		close(release)
		setupErr := <-setupDone
		updateErr := <-updateDone
		oracleStep(&steps, "SetPairingRegistration/change-during-Setup", map[string]any{
			"setup_error": oracleErr(setupErr), "update_error": oracleErr(updateErr), "hub_values": hub.Values(),
		})
	}
	oracleWrite(t, "service-go", "pairing-registration", oracleCase{
		Component: "service/service.go (Service.SetPairingRegistration, Service.AllowWaitingForTrust, Setup registration)",
		Source:    "service/service.go",
		Stimulus:  "service/service_test.go Test_DefaultPairingRegistrationExposesPendingWithoutAutomaticTrust, Test_ManualPairingAvailabilityBeforeSetupIsApplied, Test_ManualPairingAvailabilityAdvertisesWithoutAutoAccept, Test_ManualPairingRegistrationErrorIsReturned, Test_SetupRejectsHubWithoutPairingRegistration, Test_ManualPairingChangeDuringSetupIsNotLost",
		Input:     oracleInput{Qualifiers: map[string]any{"configuration": "vendor,brand,model,serial", "port": 4729}},
		Output:    oracleOutput{Decisions: steps},
	})
}

type oracleBareHub struct{ shipapi.HubInterface }

// oracleRecordLifecycle records the lifecycle of Start and Shutdown on the
// legacy path and the forwarding of reader callbacks to the legacy handler.
func oracleRecordLifecycle(t *testing.T) {
	steps := []any{}
	{
		handler := &legacyServiceReaderRecorder{}
		sut := legacyNewServiceConstructor(newOutgoingAttemptTestConfiguration(t), handler)
		hub := &outgoingAttemptGateAwareHub{}
		calls := 0
		sut.connectionsHubFactory = oracleHubFactory(hub, &calls)
		setupErr := sut.Setup()
		detail := &shipapi.ConnectionStateDetail{}
		sut.RemoteSKIConnected("legacy-ski")
		sut.ServicePairingDetailUpdate("legacy-ski", detail)
		sut.Start()
		sut.Shutdown()
		oracleStep(&steps, "legacy-path", map[string]any{
			"setup_error": oracleErr(setupErr), "gate_installs": hub.setGateCalls, "handler_connected_calls": handler.connectedCalls,
			"handler_connected_ski": handler.connectedSKI, "handler_service_is_sut": handler.connectedService == api.ServiceInterface(sut),
			"handler_pairing_calls": handler.pairingCalls, "handler_pairing_detail_same": handler.pairingDetail == detail,
			"hub_start_calls": hub.startCalls, "hub_shutdown_calls": hub.shutdownCalls, "lifecycle": oracleState(sut),
		})
	}
	{
		sut := legacyNewServiceConstructor(newOutgoingAttemptTestConfiguration(t), &legacyServiceReaderRecorder{})
		hub := &hubRuntimeRecorder{}
		calls := 0
		sut.connectionsHubFactory = oracleHubFactory(hub, &calls)
		order := []any{}
		note := func(call string, err error) {
			record := map[string]any{"call": call, "lifecycle": oracleState(sut), "hub_start_calls": hub.startCalls, "hub_shutdown_calls": hub.shutdownCalls}
			if err != nil {
				record["error"] = oracleErr(err)
			}
			order = append(order, record)
		}
		note("Setup", sut.Setup())
		sut.Shutdown()
		note("Shutdown", nil)
		sut.Start()
		note("Start", nil)
		note("Setup", sut.Setup())
		sut.Start()
		note("Start", nil)
		sut.Shutdown()
		note("Shutdown", nil)
		oracleStep(&steps, "shutdown-before-start-is-terminal", map[string]any{"sequence": order})
	}
	{
		sut := newOutgoingAttemptBridgeService(newOutgoingAttemptTestConfiguration(t), &legacyServiceReaderRecorder{}, &outgoingAttemptGateStub{}, &outgoingAttemptSinkRecorder{})
		failedHub := &outgoingAttemptGateAwareHub{setGateErr: errors.New("first install fails")}
		successfulHub := &outgoingAttemptGateAwareHub{}
		factoryCalls := 0
		sut.connectionsHubFactory = func(shipapi.HubReaderInterface, shipapi.MdnsInterface, int, tls.Certificate, *shipapi.ServiceDetails) shipapi.HubInterface {
			factoryCalls++
			if factoryCalls == 1 {
				return failedHub
			}
			return successfulHub
		}
		order := []any{}
		note := func(call string, err error) {
			record := map[string]any{
				"call": call, "lifecycle": oracleState(sut), "factory_calls": factoryCalls,
				"failed_hub_start_calls": failedHub.startCalls, "failed_hub_shutdown_calls": failedHub.shutdownCalls,
				"hub_start_calls": successfulHub.startCalls, "hub_shutdown_calls": successfulHub.shutdownCalls,
				"hub_published": sut.connectionsHub != nil, "local_service_published": sut.localService != nil, "local_device_published": sut.spineLocalDevice != nil,
			}
			if err != nil {
				record["error"] = oracleErr(err)
			}
			order = append(order, record)
		}
		sut.Start()
		sut.Shutdown()
		note("Start+Shutdown-before-Setup", nil)
		note("Setup/first-install-fails", sut.Setup())
		sut.Start()
		sut.Start()
		sut.Shutdown()
		sut.Shutdown()
		note("Start,Start,Shutdown,Shutdown-after-failed-Setup", nil)
		note("Setup/retry", sut.Setup())
		sut.Start()
		sut.Start()
		sut.Shutdown()
		sut.Shutdown()
		note("Start,Start,Shutdown,Shutdown", nil)
		oracleStep(&steps, "setup-retry-after-failure", map[string]any{"sequence": order})
	}
	oracleWrite(t, "service-go", "lifecycle-start-shutdown", oracleCase{
		Component: "service/service.go (Service.Start, Service.Shutdown, lifecycle states)",
		Source:    "service/service.go",
		Stimulus:  "service/outgoing_attempt_bridge_test.go TestNewServiceLegacyPathRemainsSourceAndRuntimeCompatible, TestServiceLifecycleShutdownBeforeStartIsTerminal, TestOutgoingAttemptBridgeSetupRetryIsDeterministicAndLifecycleIsIdempotent",
		Input:     oracleInput{Qualifiers: map[string]any{"configuration": "vendor,brand,model,serial", "port": 4729}},
		Output:    oracleOutput{Decisions: steps},
	})
}

// oracleRecordBridgeValidation records the optional outgoing-attempt bridge
// checks of Setup.
func oracleRecordBridgeValidation(t *testing.T) {
	steps := []any{}
	validGate := &outgoingAttemptGateStub{}
	validSink := &outgoingAttemptSinkRecorder{}
	var typedNilGate *outgoingAttemptGateStub
	var typedNilSink *outgoingAttemptSinkRecorder
	dependencies := []struct {
		name string
		gate shipapi.OutgoingAttemptGate
		sink shipapi.OutgoingAttemptHubReaderInterface
	}{
		{"nil gate", nil, validSink},
		{"typed nil gate", typedNilGate, validSink},
		{"nil sink", validGate, nil},
		{"typed nil sink", validGate, typedNilSink},
	}
	for _, item := range dependencies {
		sut := newOutgoingAttemptBridgeService(newOutgoingAttemptTestConfiguration(t), &legacyServiceReaderRecorder{}, item.gate, item.sink)
		hub := &outgoingAttemptGateAwareHub{}
		factoryCalls := 0
		sut.connectionsHubFactory = oracleHubFactory(hub, &factoryCalls)
		err := sut.Setup()
		sut.Start()
		sut.Shutdown()
		oracleStep(&steps, "Setup/bridge-dependencies", map[string]any{
			"dependencies": item.name, "error": oracleErr(err), "factory_calls": factoryCalls, "lifecycle": oracleState(sut),
			"hub_published": sut.connectionsHub != nil, "hub_start_calls": hub.startCalls, "hub_shutdown_calls": hub.shutdownCalls,
		})
	}
	setterFailure := errors.New("gate installation failed")
	hubs := []struct {
		name   string
		newHub func() shipapi.HubInterface
	}{
		{"nil hub", func() shipapi.HubInterface { return nil }},
		{"typed nil hub", func() shipapi.HubInterface { var typedNil *outgoingAttemptGateAwareHub; return typedNil }},
		{"missing gate setter", func() shipapi.HubInterface { return &hubRuntimeRecorder{} }},
		{"gate setter failure", func() shipapi.HubInterface { return &outgoingAttemptGateAwareHub{setGateErr: setterFailure} }},
	}
	for _, item := range hubs {
		sut := newOutgoingAttemptBridgeService(newOutgoingAttemptTestConfiguration(t), &legacyServiceReaderRecorder{}, &outgoingAttemptGateStub{}, &outgoingAttemptSinkRecorder{})
		factoryCalls := 0
		var candidate shipapi.HubInterface
		sut.connectionsHubFactory = func(shipapi.HubReaderInterface, shipapi.MdnsInterface, int, tls.Certificate, *shipapi.ServiceDetails) shipapi.HubInterface {
			factoryCalls++
			candidate = item.newHub()
			return candidate
		}
		err := sut.Setup()
		record := map[string]any{
			"hub": item.name, "error": oracleErr(err), "factory_calls": factoryCalls, "lifecycle": oracleState(sut),
			"hub_published": sut.connectionsHub != nil, "local_service_published": sut.localService != nil, "local_device_published": sut.spineLocalDevice != nil,
		}
		if recorder := runtimeRecorderFor(candidate); recorder != nil {
			record["hub_start_calls"] = recorder.startCalls
			record["hub_shutdown_calls"] = recorder.shutdownCalls
		}
		oracleStep(&steps, "Setup/bridge-hub", record)
	}
	{
		gate := &outgoingAttemptGateStub{}
		sut := newOutgoingAttemptBridgeService(newOutgoingAttemptTestConfiguration(t), &legacyServiceReaderRecorder{}, gate, &outgoingAttemptSinkRecorder{})
		hub := &outgoingAttemptGateAwareHub{}
		var hubReader shipapi.HubReaderInterface
		publishedAtInstall := false
		hub.onSetGate = func(installed shipapi.OutgoingAttemptGate) {
			publishedAtInstall = sut.connectionsHub != nil || sut.localService != nil || sut.spineLocalDevice != nil
		}
		sut.connectionsHubFactory = func(reader shipapi.HubReaderInterface, _ shipapi.MdnsInterface, _ int, _ tls.Certificate, _ *shipapi.ServiceDetails) shipapi.HubInterface {
			hubReader = reader
			return hub
		}
		err := sut.Setup()
		oracleStep(&steps, "Setup/installs-exact-gate-before-publication", map[string]any{
			"error": oracleErr(err), "gate_installs": hub.setGateCalls, "gate_is_configured_gate": hub.gate == shipapi.OutgoingAttemptGate(gate),
			"published_when_gate_installed": publishedAtInstall, "hub_reader_is_service": hubReader == shipapi.HubReaderInterface(sut),
			"hub_published": sut.connectionsHub == shipapi.HubInterface(hub), "hub_start_calls": hub.startCalls,
		})
	}
	{
		sut := newOutgoingAttemptBridgeService(newOutgoingAttemptTestConfiguration(t), &legacyServiceReaderRecorder{}, &outgoingAttemptGateStub{}, &outgoingAttemptSinkRecorder{})
		err := sut.Setup()
		oracleStep(&steps, "Setup/bridge-default-factory", map[string]any{
			"error": oracleErr(err), "hub_type": fmt.Sprintf("%T", sut.connectionsHub), "lifecycle": oracleState(sut),
		})
	}
	{
		sut := newOutgoingAttemptBridgeService(newOutgoingAttemptOversizedConfiguration(t), &legacyServiceReaderRecorder{}, &outgoingAttemptGateStub{}, &outgoingAttemptSinkRecorder{})
		factoryCalls := 0
		sut.connectionsHubFactory = oracleHubFactory(&outgoingAttemptGateAwareHub{}, &factoryCalls)
		err := sut.Setup()
		oracleStep(&steps, "Setup/bridge-oversized-device-address", map[string]any{
			"error_prefix": strings.SplitN(fmt.Sprint(err), ":", 2)[0], "factory_calls": factoryCalls, "hub_published": sut.connectionsHub != nil,
			"local_service_published": sut.localService != nil, "local_device_published": sut.spineLocalDevice != nil,
		})
	}
	oracleWrite(t, "service-go", "outgoing-attempt-bridge-setup", oracleCase{
		Component: "service/service.go (NewServiceWithOutgoingAttemptBridge, NewServiceWithOptions, Setup bridge checks)",
		Source:    "service/service.go",
		Stimulus:  "service/outgoing_attempt_bridge_test.go TestOutgoingAttemptBridgeSetupRejectsNilAndTypedNilDependencies, TestOutgoingAttemptBridgeSetupRejectsUninstallableHubsTransactionally, TestOutgoingAttemptBridgeSetupInstallsExactGateBeforePublication, TestOutgoingAttemptBridgeDefaultFactoryPublishesProductionHub, TestOutgoingAttemptBridgeSetupFailureDoesNotPublishLocalCandidates",
		Input:     oracleInput{Qualifiers: map[string]any{"configuration": "vendor,brand,model,serial", "oversized": "model x50, serial x20"}},
		Output:    oracleOutput{Decisions: steps},
	})
}
