package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"testing"
)

// oracleSession is the published session input the replay runner hands to the harness.
type oracleSession struct {
	Session  string          `json:"session"`
	Scenario string          `json:"scenario"`
	Input    json.RawMessage `json:"input"`
}

func oracleLoadSession(t *testing.T) oracleSession {
	t.Helper()
	path := os.Getenv("ORACLE_SESSION")
	if path == "" {
		t.Skip("ORACLE_SESSION is not set")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var session oracleSession
	if err := json.Unmarshal(raw, &session); err != nil {
		t.Fatal(err)
	}
	return session
}

// oracleClasses is the six-class record of one whole session.
type oracleClasses struct {
	Acquisitions  []any `json:"acquisitions"`
	Sends         []any `json:"sends"`
	Publications  []any `json:"publications"`
	Withdrawals   []any `json:"withdrawals"`
	Outcomes      []any `json:"outcomes"`
	PublicOutputs []any `json:"public_outputs"`
}

func oracleNormalize() *oracleClasses {
	return &oracleClasses{Acquisitions: []any{}, Sends: []any{}, Publications: []any{}, Withdrawals: []any{}, Outcomes: []any{}, PublicOutputs: []any{}}
}

func oracleWriteClasses(t *testing.T, classes *oracleClasses) {
	t.Helper()
	encoded, err := json.MarshalIndent(classes, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(os.Getenv("ORACLE_OUT"), "classes.json"), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

// oracleLeaves flattens a decoded JSON value into path to non-null leaf.
func oracleLeaves(prefix string, value any, out map[string]string) {
	switch typed := value.(type) {
	case nil:
	case map[string]any:
		for key, child := range typed {
			oracleLeaves(prefix+"/"+key, child, out)
		}
	case []any:
		for index, child := range typed {
			oracleLeaves(prefix+"/"+oracleItoa(index), child, out)
		}
	default:
		encoded, _ := json.Marshal(typed)
		out[prefix] = string(encoded)
	}
}

func oracleItoa(value int) string {
	encoded, _ := json.Marshal(value)
	return string(encoded)
}

// oracleWithdrawn lists the paths that held a value before and hold none now.
func oracleWithdrawn(before, after map[string]string) []string {
	var paths []string
	for path := range before {
		if _, kept := after[path]; !kept {
			paths = append(paths, path)
		}
	}
	sort.Strings(paths)
	return paths
}

func oracleJSON(value any) any {
	encoded, err := json.Marshal(value)
	if err != nil {
		return map[string]string{"marshal_error": err.Error()}
	}
	var decoded any
	_ = json.Unmarshal(encoded, &decoded)
	return decoded
}
