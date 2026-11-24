package graphql

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sort"
	"testing"

	"github.com/Project-Helianthus/helianthus-ebusreg/registry"
)

// oraclePrePortSort puts every introspection list in name order: the schema does not specify one and the pinned library
// builds its type list from a map.
func oraclePrePortSort(value any) {
	switch typed := value.(type) {
	case map[string]any:
		for key, child := range typed {
			if list, ok := child.([]any); ok {
				switch key {
				case "types", "fields", "args", "inputFields", "enumValues", "possibleTypes", "interfaces":
					sort.SliceStable(list, func(i, j int) bool {
						left, _ := list[i].(map[string]any)["name"].(string)
						right, _ := list[j].(map[string]any)["name"].(string)
						return left < right
					})
				}
			}
			oraclePrePortSort(child)
		}
	case []any:
		for _, child := range typed {
			oraclePrePortSort(child)
		}
	}
}

const oraclePrePortIntrospection = `query Introspection {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      kind name
      fields(includeDeprecated: true) {
        name
        args { name type { ...T } defaultValue }
        type { ...T }
        isDeprecated
      }
      inputFields { name type { ...T } defaultValue }
      interfaces { name }
      enumValues(includeDeprecated: true) { name isDeprecated }
      possibleTypes { name }
    }
  }
}
fragment T on __Type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } }`

// TestOraclePrePortSchema records the schema of the pre-port GraphQL surface as one introspection document.
func TestOraclePrePortSchema(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	builder := NewBuilder(registry.NewDeviceRegistry(nil), nil)
	if err := builder.Start(context.Background()); err != nil {
		t.Fatal(err)
	}
	handler, err := NewHandler(builder)
	if err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(handler)
	defer server.Close()
	body, _ := json.Marshal(map[string]any{"query": oraclePrePortIntrospection})
	response, err := http.Post(server.URL, "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	raw, _ := io.ReadAll(response.Body)
	var document any
	if err := json.Unmarshal(raw, &document); err != nil {
		t.Fatalf("response is not JSON: %s", raw)
	}
	oraclePrePortSort(document)
	encoded, _ := json.MarshalIndent(document, "", "  ")
	if err := os.WriteFile(filepath.Join(directory, "graphql-schema-introspection.json"), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
