//go:build !linux

package main

import (
	"go/parser"
	"go/token"
	"strconv"
	"testing"
)

func oracleCanImports(t *testing.T, file string) []string {
	t.Helper()
	parsed, err := parser.ParseFile(token.NewFileSet(), file, nil, parser.ImportsOnly)
	if err != nil {
		t.Fatal(err)
	}
	imports := []string{}
	for _, item := range parsed.Imports {
		path, err := strconv.Unquote(item.Path.Value)
		if err != nil {
			t.Fatal(err)
		}
		imports = append(imports, path)
	}
	return imports
}

func oracleCanResult(receiver any, err error, imports []string) map[string]any {
	return map[string]any{
		"receiver_returned":   receiver != nil,
		"error":               oracleCanError(err),
		"pinned_file_imports": imports,
		"socket_actions":      0,
		"socket_action_basis": "the pinned !linux file imports only the listed packages and holds no operating-system call",
	}
}

// TestOracleCanReceive runs the pinned !linux openers of the BMS and project
// receivers on a host that is not Linux.
func TestOracleCanReceive(t *testing.T) {
	names := []any{"synthetic0", ""}
	{
		imports := oracleCanImports(t, "growatt_project_socketcan_unsupported.go")
		attempts := []any{}
		for _, name := range names {
			receiver, err := openGrowattProjectSocket(name.(string))
			attempts = append(attempts, map[string]any{"name": name, "outcome": oracleCanResult(receiver, err, imports)})
		}
		oracleCanWrite(t, "nonlinux-project-unsupported", "nonlinux", "growatt-project-socketcan-opener-non-linux",
			"openGrowattProjectSocket is called with each configured name; the pinned test files of this opener are build-tagged linux, so the pin has no stimulus for it",
			map[string]any{"function": "openGrowattProjectSocket", "names": names}, nil, map[string]any{"attempts": attempts})
	}
	{
		imports := oracleCanImports(t, "growatt_bms_can_socketcan_unsupported.go")
		attempts := []any{}
		for _, name := range names {
			receiver, err := openGrowattBMSCANSocket(name.(string))
			attempts = append(attempts, map[string]any{
				"name":                 name,
				"outcome":              oracleCanResult(receiver, err, imports),
				"is_config_error":      err == errGrowattBMSCANConfig,
				"is_unsupported_error": err == errGrowattBMSCANUnsupported,
			})
		}
		oracleCanWrite(t, "nonlinux-bms-unsupported", "nonlinux", "growatt-bms-can-socketcan-opener-non-linux",
			"openGrowattBMSCANSocket is called with each configured name; the pin has no test of the !linux opener",
			map[string]any{"function": "openGrowattBMSCANSocket", "names": names}, nil, map[string]any{"attempts": attempts})
	}
}
