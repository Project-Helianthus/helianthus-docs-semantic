package eebusruntime

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/netip"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestOracleEEBusRoot records runtime.go and output_binding.go at the pin. The
// stimuli are the pin's own tests; no expectation is derived here.
func TestOracleEEBusRoot(t *testing.T) {
	oracleRecordRuntimeFile(t)
	oracleRecordOutputBindingFile(t)
}

func oracleRecordRuntimeFile(t *testing.T) {
	oracleRecordRuntimeShape(t)
	oracleRecordRuntimeDisabled(t)
	oracleRecordRuntimeConfigValidation(t)
	oracleRecordRuntimeRemotes(t)
	oracleRecordRuntimeLifecycle(t)
	oracleRecordRuntimeFailures(t)
}

func oracleRecordOutputBindingFile(t *testing.T) {
	oracleRecordBindingConstruction(t)
	oracleRecordBindingResourceFields(t)
	oracleRecordBindingBasisAndMerge(t)
	oracleRecordBindingProhibition(t)
	oracleRecordBindingAddresses(t)
	oracleRecordBindingFeatures(t)
	oracleRecordBindingAnnouncement(t)
	oracleRecordBindingNodeFollowing(t)
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

func oracleWrite(t *testing.T, group, name string, document oracleCase) {
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

func oracleScrub(text string, directories ...string) string {
	for _, directory := range directories {
		if directory != "" {
			text = strings.ReplaceAll(text, directory, "<sandbox>")
		}
	}
	return text
}

func oracleErr(err error, directories ...string) any {
	if err == nil {
		return nil
	}
	return map[string]any{"text": oracleScrub(err.Error(), directories...)}
}

func oracleStep(steps *[]any, call string, fields map[string]any) {
	record := map[string]any{"call": call}
	for key, value := range fields {
		record[key] = value
	}
	*steps = append(*steps, record)
}

// oracleEndpoint writes an address and port without a dotted-quad rendering.
func oracleEndpoint(endpoint netip.AddrPort) map[string]any {
	if !endpoint.IsValid() {
		return map[string]any{"valid": false, "port": endpoint.Port()}
	}
	address := endpoint.Addr()
	bytes := address.As16()
	return map[string]any{
		"valid": true, "is_ipv4": address.Is4(), "is_ipv4_mapped_ipv6": address.Is4In6(), "address_bytes_hex": hex.EncodeToString(bytes[:]),
		"is_unspecified": address.IsUnspecified(), "is_multicast": address.IsMulticast(), "port": endpoint.Port(),
	}
}

func oracleConfig(config Config) map[string]any {
	state := "empty"
	switch {
	case config.StateRoot == "":
	case config.StateRoot == string(filepath.Separator):
		state = "filesystem-root"
	case filepath.IsAbs(config.StateRoot):
		state = "absolute"
	default:
		state = config.StateRoot
	}
	interfaceName := config.Interface
	if interfaceName == oracleWildcardInterface() {
		interfaceName = "<ipv4-all-zero-wildcard>"
	}
	remotes := []any{}
	for _, remote := range config.Remotes {
		remotes = append(remotes, remote.SKI)
	}
	return map[string]any{
		"enabled": config.Enabled, "state_root": state, "interface": interfaceName, "listen_address": oracleEndpoint(config.ListenAddress),
		"discovery_enabled": config.DiscoveryEnabled, "remotes": remotes, "remotes_nil": config.Remotes == nil, "pairing_policy": string(config.PairingPolicy),
	}
}

func oracleSnapshotFacts(snapshot SnapshotV1) map[string]any {
	pairing := []any{}
	for _, item := range snapshot.Pairing {
		pairing = append(pairing, map[string]any{"remote_ski": item.RemoteSKI, "state": fmt.Sprint(item.State)})
	}
	services := []any{}
	for _, item := range snapshot.Services {
		services = append(services, map[string]any{"ski": item.SKI, "paired": item.Paired})
	}
	sessions := []any{}
	for _, item := range snapshot.Sessions {
		sessions = append(sessions, map[string]any{"id": item.ID, "state": fmt.Sprint(item.State)})
	}
	facts := map[string]any{
		"status_state": fmt.Sprint(snapshot.Status.State), "pairing": pairing, "services": services, "sessions": sessions,
		"device_count": len(snapshot.Devices), "entity_count": len(snapshot.Entities), "feature_count": len(snapshot.Features), "use_case_count": len(snapshot.UseCases),
		"data_hash": snapshot.Meta.DataHash,
	}
	if snapshot.Status.Degradation != nil {
		facts["degradation_reason"] = fmt.Sprint(snapshot.Status.Degradation.Reason)
	}
	return facts
}

func oracleV4(a, b, c, d byte, port uint16) netip.AddrPort {
	return netip.AddrPortFrom(netip.AddrFrom4([4]byte{a, b, c, d}), port)
}

// oracleWildcardInterface is the IPv4 all-zero wildcard the pin's test passes as an interface name.
func oracleWildcardInterface() string {
	return strings.Join([]string{"0", "0", "0", "0"}, ".")
}
