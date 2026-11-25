package eebusservicebridge

import (
	"crypto/x509"
	"encoding/json"
	"net"
	"net/netip"
	"os"
	"path/filepath"
	"testing"
	"time"

	eebusapi "github.com/Project-Helianthus/helianthus-eebus-go/api"
	shipcert "github.com/Project-Helianthus/helianthus-ship-go/cert"
	spinemodel "github.com/Project-Helianthus/helianthus-spine-go/model"
)

// TestOracleServiceBridge records internal/eebusservicebridge/service.go. The
// stimuli are the pin's own tests (TestScopedServiceShutdownJoinsMonitorWithoutFalseTerminal
// and TestIssue58ServiceOptionsInstallAttemptGateAlongsideListenerPolicy); no
// expectation is derived here. The loopback endpoint is chosen by the host and
// is not part of any output.
func TestOracleServiceBridge(t *testing.T) {
	decisions := []any{}

	{
		certificate, err := shipcert.CreateCertificate("", "Helianthus", "RO", "scoped-monitor-test")
		if err != nil {
			t.Fatal(err)
		}
		leaf, err := x509.ParseCertificate(certificate.Certificate[0])
		if err != nil {
			t.Fatal(err)
		}
		localSKI, err := shipcert.SkiFromCertificate(leaf)
		if err != nil {
			t.Fatal(err)
		}
		probe, err := net.ListenTCP("tcp4", &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 0})
		if err != nil {
			t.Fatal(err)
		}
		endpoint := probe.Addr().(*net.TCPAddr).AddrPort()
		if err := probe.Close(); err != nil {
			t.Fatal(err)
		}
		configuration, err := eebusapi.NewConfiguration(
			"Project-Helianthus", "Helianthus", "eebusreg", localSKI,
			spinemodel.DeviceTypeTypeEnergyManagementSystem,
			[]spinemodel.EntityTypeType{spinemodel.EntityTypeTypeCEM},
			int(endpoint.Port()), certificate, time.Second,
		)
		if err != nil {
			t.Fatal(err)
		}
		service := NewServiceWithOptions(configuration, nil, ServiceOptions{
			ListenerPolicy: &ListenerPolicy{ListenAddress: endpoint, DiscoveryEnabled: false},
		})
		record := map[string]any{"scenario": "scoped-service-shutdown-joins-monitor", "service_constructed": service != nil}
		if service != nil {
			record["setup_error"] = oracleErr(service.Setup())
			record["start_with_policy_error"] = oracleErr(service.StartWithPolicy())
			time.Sleep(110 * time.Millisecond)
			service.Shutdown()
			monitorDone := false
			select {
			case <-service.monitorDone:
				monitorDone = true
			default:
			}
			listenerTerminal := false
			select {
			case <-service.ListenerTerminal():
				listenerTerminal = true
			default:
			}
			record["monitor_terminated_when_shutdown_returned"] = monitorDone
			record["listener_terminal_error_emitted"] = listenerTerminal
			rebound, rebindErr := net.ListenTCP("tcp4", net.TCPAddrFromAddrPort(netip.AddrPortFrom(endpoint.Addr(), endpoint.Port())))
			record["rebind_error"] = oracleErr(rebindErr)
			if rebindErr == nil {
				_ = rebound.Close()
			}
		}
		decisions = append(decisions, record)
	}

	{
		certificate, localSKI, endpoint := issue58ServiceFixture(t)
		configuration, err := eebusapi.NewConfiguration(
			"Project-Helianthus", "Helianthus", "eebusreg", localSKI,
			spinemodel.DeviceTypeTypeEnergyManagementSystem,
			[]spinemodel.EntityTypeType{spinemodel.EntityTypeTypeCEM},
			endpoint.Port, certificate, time.Second,
		)
		if err != nil {
			t.Fatal(err)
		}
		bridge := &issue58AttemptBridge{}
		service := NewServiceWithOptions(configuration, nil, ServiceOptions{
			ListenerPolicy:        &ListenerPolicy{ListenAddress: endpoint.AddrPort(), DiscoveryEnabled: false},
			OutgoingAttemptBridge: &OutgoingAttemptBridgeConfiguration{Gate: bridge, Sink: bridge},
		})
		record := map[string]any{"scenario": "options-install-attempt-gate-alongside-listener-policy", "service_constructed": service != nil}
		if service != nil {
			record["setup_error"] = oracleErr(service.Setup())
			service.Shutdown()
			record["listener_terminal_channel_present"] = service.ListenerTerminal() != nil
		}
		decisions = append(decisions, record)
	}

	document := map[string]any{
		"format":    "helianthus-oracle-qv06-case/1",
		"component": "internal/eebusservicebridge/service.go (NewServiceWithOptions, Service.StartWithPolicy, Service.Shutdown, Service.ListenerTerminal)",
		"source":    "internal/eebusservicebridge/service.go",
		"stimulus":  "internal/eebusservicebridge/service_test.go TestScopedServiceShutdownJoinsMonitorWithoutFalseTerminal (first iteration); internal/eebusservicebridge/issue58_predial_gate_red_test.go TestIssue58ServiceOptionsInstallAttemptGateAlongsideListenerPolicy",
		"input": map[string]any{
			"bytes": "",
			"qualifiers": map[string]any{
				"vendor_code": "Project-Helianthus", "brand": "Helianthus", "model": "eebusreg", "device_type": "EnergyManagementSystem",
				"entity_types": []any{"CEM"}, "heartbeat_timeout_ns": int64(time.Second), "discovery_enabled": false,
				"endpoint": "a loopback IPv4 endpoint with a free port chosen by the host; the port is not part of any output",
				"monitor_wait_ms": 110,
			},
			"clock": map[string]any{}, "state": map[string]any{},
		},
		"output": map[string]any{
			"symbols_written": []any{}, "decisions": decisions, "cache": map[string]any{}, "observations": []any{}, "counters": map[string]any{},
		},
	}
	oracleWriteDocument(t, "service-go", "scoped-service-and-attempt-gate", document)
}

func oracleErr(err error) any {
	if err == nil {
		return nil
	}
	return map[string]any{"text": err.Error()}
}

func oracleWriteDocument(t *testing.T, group, name string, document map[string]any) {
	t.Helper()
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	data, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(directory, group, name+".json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(data, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
