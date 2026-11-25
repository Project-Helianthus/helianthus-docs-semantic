package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

type oracleCanInput struct {
	Format    string         `json:"format"`
	Case      string         `json:"case"`
	Partition string         `json:"partition"`
	Component string         `json:"component"`
	Source    oracleCanFiles `json:"source"`
	Stimulus  string         `json:"stimulus"`
	Operands  map[string]any `json:"operands"`
}

type oracleCanFiles struct {
	Files   any `json:"files"`
	Overlay any `json:"overlay"`
}

type oracleCanExpected struct {
	Format    string         `json:"format"`
	Case      string         `json:"case"`
	Partition string         `json:"partition"`
	Calls     []any          `json:"calls"`
	Result    map[string]any `json:"result"`
}

func oracleCanEnvironment(t *testing.T, name string) any {
	t.Helper()
	raw := os.Getenv(name)
	if raw == "" {
		t.Fatalf("%s is not set", name)
	}
	var value any
	if err := json.Unmarshal([]byte(raw), &value); err != nil {
		t.Fatalf("%s: %v", name, err)
	}
	return value
}

func oracleCanWrite(t *testing.T, name, partition, component, stimulus string, operands map[string]any, calls []any, result map[string]any) {
	t.Helper()
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	if calls == nil {
		calls = []any{}
	}
	input := oracleCanInput{
		Format:    "helianthus-oracle-qv05-input/1",
		Case:      name,
		Partition: partition,
		Component: component,
		Source:    oracleCanFiles{Files: oracleCanEnvironment(t, "ORACLE_CAN_SOURCES_"+partition), Overlay: oracleCanEnvironment(t, "ORACLE_CAN_OVERLAY_"+partition)},
		Stimulus:  stimulus,
		Operands:  operands,
	}
	expected := oracleCanExpected{Format: "helianthus-oracle-qv05-expected/1", Case: name, Partition: partition, Calls: calls, Result: result}
	for file, document := range map[string]any{"input.json": input, "expected.json": expected} {
		data, err := json.MarshalIndent(document, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(directory, name, file)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, append(data, '\n'), 0o644); err != nil {
			t.Fatal(err)
		}
	}
}

func oracleCanError(err error) any {
	if err == nil {
		return nil
	}
	return err.Error()
}
