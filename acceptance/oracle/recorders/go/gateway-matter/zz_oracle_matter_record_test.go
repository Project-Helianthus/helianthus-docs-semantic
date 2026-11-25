package matter

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"testing"

	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
)

const (
	oracleInputFormat  = "helianthus-oracle-qv08-input/1"
	oracleOutputFormat = "helianthus-oracle-qv08-output/1"
)

type kv struct {
	K string
	V any
}

// fields is an ordered JSON object. Its members keep the order in which they are listed.
type fields []kv

func obj(items ...kv) fields { return items }

func (o fields) MarshalJSON() ([]byte, error) {
	var out bytes.Buffer
	out.WriteString("{")
	for i, item := range o {
		key, err := json.Marshal(item.K)
		if err != nil {
			return nil, err
		}
		if i > 0 {
			out.WriteString(",")
		}
		out.Write(key)
		out.WriteString(":")
		out.Write(oracleValue(item.V))
	}
	out.WriteString("}")
	return out.Bytes(), nil
}

func oracleValue(value any) []byte {
	var out bytes.Buffer
	encoder := json.NewEncoder(&out)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		panic(err)
	}
	return bytes.TrimRight(out.Bytes(), "\n")
}

var oracleSlug = regexp.MustCompile(`[^a-z0-9]+`)

func oracleName(parts ...string) string {
	return strings.Trim(oracleSlug.ReplaceAllString(strings.ToLower(strings.Join(parts, "-")), "-"), "-")
}

// oracleEncode writes one member per line; the members of a nested ordered object also take a line each.
func oracleEncode(items fields, nested bool) []byte {
	var out bytes.Buffer
	out.WriteString("{\n")
	for i, item := range items {
		key, err := json.Marshal(item.K)
		if err != nil {
			panic(err)
		}
		out.Write(key)
		out.WriteString(": ")
		if body, ok := item.V.(fields); ok && nested {
			out.Write(bytes.TrimRight(oracleEncode(body, false), "\n"))
		} else {
			out.Write(oracleValue(item.V))
		}
		if i < len(items)-1 {
			out.WriteString(",")
		}
		out.WriteString("\n")
	}
	out.WriteString("}\n")
	return out.Bytes()
}

// oracleCase writes one case directory with its input file and its output file.
func oracleCase(t *testing.T, group, name, component, source, stimulus string, input, output fields) {
	t.Helper()
	root := os.Getenv("ORACLE_OUT")
	if root == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	directory := filepath.Join(root, group, name)
	if err := os.MkdirAll(directory, 0o755); err != nil {
		t.Fatal(err)
	}
	write := func(file, format, key string, body fields) {
		items := fields{{"format", format}, {"case", group + "/" + name}, {"component", component}, {"source", source}, {"stimulus", stimulus}, {key, body}}
		if err := os.WriteFile(filepath.Join(directory, file), oracleEncode(items, true), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	write("input.json", oracleInputFormat, "input", input)
	write("output.json", oracleOutputFormat, "output", output)
}

// oracleError records an error as the pin reports it: its text and its SemReg identifier.
func oracleError(err error) fields {
	if err == nil {
		return fields{{"error", nil}, {"error_id", nil}}
	}
	return fields{{"error", err.Error()}, {"error_id", string(semreg.ErrorIdentifier(err))}}
}

func oracleOutput(head fields, err error) fields { return append(append(fields{}, head...), oracleError(err)...) }

func oracleSealedInput(snapshot semreg.Snapshot, evaluation semreg.EvaluationView, extra ...kv) fields {
	return append(fields{{"snapshot", snapshot}, {"evaluation", evaluation}}, extra...)
}

func oracleKeys[V any](m map[string]V) []string {
	keys := make([]string, 0, len(m))
	for key := range m {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

// oracleBytes records the bytes a function returned by length and sha256: null when it returned none.
func oracleBytes(raw []byte) any {
	if raw == nil {
		return nil
	}
	return fields{{"length", len(raw)}, {"sha256", fmt.Sprintf("%x", sha256.Sum256(raw))}}
}
