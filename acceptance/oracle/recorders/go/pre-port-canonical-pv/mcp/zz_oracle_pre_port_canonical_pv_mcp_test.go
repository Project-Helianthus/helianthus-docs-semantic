package mcp

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestOraclePrePortCanonicalPVEnvelope records the canonical PV v1 envelope of the pin's golden test and checks it against the pin's golden file.
func TestOraclePrePortCanonicalPVEnvelope(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	data := canonicalPVData(modbusV1CanonicalPVFixture(), "2026-08-17T15:00:00Z")
	text := mustJSON(newModbusV1Envelope(data, nil, true, "RETAINED_CANONICAL_OBSERVATION", "2026-08-17T15:00:00Z"))
	golden, err := os.ReadFile(filepath.Join("testdata", "modbus_v1_canonical_pv.golden.json"))
	if err != nil {
		t.Fatal(err)
	}
	digest := sha256.Sum256(golden)
	var envelope any
	if err := json.Unmarshal([]byte(text), &envelope); err != nil {
		t.Fatal(err)
	}
	document := map[string]any{
		"format":                 "helianthus-oracle-pre-port-canonical-pv-mcp-envelope/1",
		"description":            "the retained canonical PV v1 envelope that canonicalPVData and newModbusV1Envelope build for the snapshot of the pin's golden test, with the clock values of that test",
		"golden_path":            "mcp/testdata/modbus_v1_canonical_pv.golden.json",
		"golden_sha256":          hex.EncodeToString(digest[:]),
		"envelope_equals_golden": text == strings.TrimSpace(string(golden)),
		"envelope":               envelope,
	}
	encoded, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, "mcp-canonical-pv-envelope.json"), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
