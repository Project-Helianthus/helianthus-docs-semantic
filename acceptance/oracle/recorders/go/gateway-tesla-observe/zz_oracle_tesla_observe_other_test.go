//go:build !linux

package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

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

func oracleWrite(t *testing.T, name string, document oracleCase) {
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
	path := filepath.Join(directory, name+".json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(data, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

// TestOracleTeslaObserve records the opener of the pin's non-Linux build.
// The pin has no test of this file; the stimuli are the opener's own
// argument, called directly and through the command's port wiring.
func TestOracleTeslaObserve(t *testing.T) {
	const source = "cmd/gateway/tesla_observe_flow_other.go"
	for _, tc := range []struct{ name, path string }{
		{"empty-path", ""},
		{"relative-path", "synthetic-serial-port"},
		{"absolute-path", "/synthetic/serial/port"},
	} {
		stream, err := openTeslaObserveSerial(tc.path)
		text := any(nil)
		if err != nil {
			text = err.Error()
		}
		oracleWrite(t, "nonlinux-stub-"+tc.name, oracleCase{
			Component: "tesla-observe-serial-opener-non-linux",
			Source:    source,
			Stimulus:  "none at the pin; the opener is called directly with a synthetic path",
			Input:     oracleInput{Qualifiers: map[string]any{"function": "openTeslaObserveSerial", "path": tc.path}},
			Output: oracleOutput{
				Decisions: []any{map[string]any{"source_is_nil": stream == nil, "error": text}},
			},
		})
	}
	{
		var stderr bytes.Buffer
		ports := newTeslaObservePorts()
		ports.Stderr = &stderr
		stream, err := ports.OpenSerial("synthetic-serial-port")
		text := any(nil)
		if err != nil {
			text = err.Error()
		}
		oracleWrite(t, "nonlinux-stub-command-ports", oracleCase{
			Component: "tesla-observe-serial-opener-non-linux",
			Source:    source,
			Stimulus:  "none at the pin; the opener is taken from the command's own port table",
			Input:     oracleInput{Qualifiers: map[string]any{"function": "newTeslaObservePorts().OpenSerial", "path": "synthetic-serial-port"}},
			Output: oracleOutput{
				Decisions: []any{map[string]any{"source_is_nil": stream == nil, "error": text}},
			},
		})
	}
	{
		var stderr bytes.Buffer
		ports := newTeslaObservePorts()
		ports.Stderr = &stderr
		args := []string{"-prepare", "-serial-path", "synthetic-serial-port"}
		code := runTeslaObserve(args, ports)
		oracleWrite(t, "nonlinux-stub-prepare-run", oracleCase{
			Component: "tesla-observe-serial-opener-non-linux",
			Source:    source,
			Stimulus:  "none at the pin; the preparation run reaches the opener through the command's own port table",
			Input:     oracleInput{Qualifiers: map[string]any{"function": "runTeslaObserve", "args": args}},
			Output: oracleOutput{
				Decisions: []any{map[string]any{"exit_code": code, "stderr": stderr.String()}},
			},
		})
	}
}
