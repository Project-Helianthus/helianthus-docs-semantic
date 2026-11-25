package modbus

import (
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// TestOracleModbus records the pacing code of the pin: the endpoint scheduler,
// the reconnect backoff and the RTU session. The stimuli are the pin's own
// tests; no expectation is derived here.
func TestOracleModbus(t *testing.T) {
	oracleRecordScheduler(t)
	oracleRecordBackoff(t)
	oracleRecordRTUSession(t)
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
	document.Format = "helianthus-oracle-qv04-case/1"
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
	record := map[string]any{"text": err.Error()}
	var protocol *ProtocolError
	if errors.As(err, &protocol) {
		record["kind"] = string(protocol.Kind)
		record["field"] = protocol.Field
		record["offset"] = protocol.Offset
		record["requested_function"] = int(protocol.RequestedFunction)
		record["received_function"] = int(protocol.ReceivedFunction)
		record["exception_code"] = int(protocol.ExceptionCode)
	}
	return record
}

func oracleHex(data []byte) string { return hex.EncodeToString(data) }

func oracleNS(value time.Duration) int64 { return int64(value) }

func oracleInt(value any) int64 {
	switch typed := value.(type) {
	case int:
		return int64(typed)
	case int64:
		return typed
	case uint64:
		return int64(typed)
	case uint8:
		return int64(typed)
	case uint16:
		return int64(typed)
	}
	panic("oracle: not an integer")
}
