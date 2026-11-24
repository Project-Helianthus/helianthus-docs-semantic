package mcp

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/Project-Helianthus/helianthus-ebusreg/registry"
)

// TestOraclePrePortToolList records the tools/list answer of the pre-port MCP server.
func TestOraclePrePortToolList(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	server, err := NewServer(&testRegistry{entries: make(map[byte]registry.DeviceEntry)}, &testInvoker{})
	if err != nil {
		t.Fatal(err)
	}
	list, rpcErr := server.handleToolsList()
	if rpcErr != nil {
		t.Fatalf("tools/list: %v", rpcErr)
	}
	encoded, err := json.MarshalIndent(list, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, "mcp-tools-list.json"), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
