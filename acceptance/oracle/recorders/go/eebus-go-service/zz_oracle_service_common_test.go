package service

import (
	"encoding/hex"
	"encoding/json"
	"net"
	"os"
	"path/filepath"
	"testing"

	shipapi "github.com/Project-Helianthus/helianthus-ship-go/api"
)

// TestOracleEEBusGoService records service.go, service_hub.go and the native
// discovery snapshot test file of the eebus-go service package at the pin. The
// stimuli are the pin's own tests; no expectation is derived here.
func TestOracleEEBusGoService(t *testing.T) {
	oracleRecordServiceFile(t)
	oracleRecordServiceHubFile(t)
}

func oracleRecordServiceFile(t *testing.T) {
	oracleRecordSetup(t)
	oracleRecordPairingRegistration(t)
	oracleRecordLifecycle(t)
	oracleRecordBridgeValidation(t)
	oracleRecordListenerPolicy(t)
	oracleRecordCandidateControl(t)
	oracleRecordTrustedRemoteRetry(t)
}

func oracleRecordServiceHubFile(t *testing.T) {
	oracleRecordHubReaderForwarding(t)
	oracleRecordHubOutgoingAttemptForwarding(t)
	oracleRecordHubLegacyCandidateVisibility(t)
	oracleRecordHubCandidateVisibilityDispatch(t)
	oracleRecordNativeDiscoverySnapshots(t)
}

type oracleCase struct {
	Format    string       `json:"format"`
	Component string       `json:"component"`
	Source    string       `json:"source"`
	Stimulus  string       `json:"stimulus"`
	Input     oracleInput  `json:"input"`
	Output    oracleOutput `json:"output"`
}

type oracleInput struct {
	Bytes      string         `json:"bytes"`
	Qualifiers map[string]any `json:"qualifiers"`
	Clock      map[string]any `json:"clock"`
	State      map[string]any `json:"state"`
}

type oracleOutput struct {
	SymbolsWritten []any          `json:"symbols_written"`
	Decisions      []any          `json:"decisions"`
	Cache          map[string]any `json:"cache"`
	Observations   []any          `json:"observations"`
	Counters       map[string]any `json:"counters"`
}

func oracleWrite(t *testing.T, group string, name string, document oracleCase) {
	t.Helper()
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	document.Format = "helianthus-oracle-qv06-case/1"
	if document.Input.Qualifiers == nil {
		document.Input.Qualifiers = map[string]any{}
	}
	if document.Input.Clock == nil {
		document.Input.Clock = map[string]any{}
	}
	if document.Input.State == nil {
		document.Input.State = map[string]any{}
	}
	if document.Output.SymbolsWritten == nil {
		document.Output.SymbolsWritten = []any{}
	}
	if document.Output.Decisions == nil {
		document.Output.Decisions = []any{}
	}
	if document.Output.Cache == nil {
		document.Output.Cache = map[string]any{}
	}
	if document.Output.Observations == nil {
		document.Output.Observations = []any{}
	}
	if document.Output.Counters == nil {
		document.Output.Counters = map[string]any{}
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

func oracleErr(err error) any {
	if err == nil {
		return nil
	}
	return map[string]any{"text": err.Error()}
}

func oracleLifecycleName(state lifecycleState) string {
	switch state {
	case lifecycleUninitialized:
		return "uninitialized"
	case lifecycleSettingUp:
		return "setting_up"
	case lifecycleReady:
		return "ready"
	case lifecycleStarting:
		return "starting"
	case lifecycleRunning:
		return "running"
	case lifecycleStopping:
		return "stopping"
	case lifecycleStopped:
		return "stopped"
	case lifecycleTerminal:
		return "terminal"
	default:
		return "unknown"
	}
}

func oracleState(sut *Service) string {
	return oracleLifecycleName(serviceLifecycle(sut))
}

func oracleStep(steps *[]any, call string, fields map[string]any) {
	record := map[string]any{"call": call}
	for key, value := range fields {
		record[key] = value
	}
	*steps = append(*steps, record)
}

func oracleIPHex(address net.IP) any {
	if address == nil {
		return nil
	}
	return hex.EncodeToString(address.To16())
}

func oracleSnapshot(snapshot shipapi.PairingCandidateDiscoverySnapshotV1) map[string]any {
	candidates := []any{}
	for _, candidate := range snapshot.Candidates {
		addresses := []any{}
		for _, address := range candidate.Addresses {
			addresses = append(addresses, oracleIPHex(address))
		}
		scoped := []any{}
		for _, address := range candidate.ScopedAddresses {
			scoped = append(scoped, address.String())
		}
		candidates = append(candidates, map[string]any{
			"candidate_ref": candidate.CandidateRef, "name": candidate.Name, "ski": candidate.SKI,
			"identifier": candidate.Identifier, "brand": candidate.Brand, "type": candidate.Type, "model": candidate.Model,
			"path": candidate.Path, "host": candidate.Host, "port": candidate.Port, "register": candidate.Register,
			"addresses_hex": addresses, "addresses_nil": candidate.Addresses == nil,
			"scoped_addresses": scoped, "scoped_addresses_nil": candidate.ScopedAddresses == nil,
			"unscoped_link_local_observed": candidate.UnscopedLinkLocalObserved,
		})
	}
	return map[string]any{
		"observation_revision": snapshot.ObservationRevision,
		"new_entries":          snapshot.NewEntries,
		"candidates":           candidates,
		"candidates_nil":       snapshot.Candidates == nil,
	}
}

func oracleRefs(refs []shipapi.PairingCandidateRef) []any {
	out := []any{}
	for _, ref := range refs {
		out = append(out, map[string]any{
			"candidate_ref": ref.CandidateRef, "name": ref.Name, "ski": ref.SKI, "identifier": ref.Identifier,
			"brand": ref.Brand, "type": ref.Type, "model": ref.Model,
		})
	}
	return out
}
