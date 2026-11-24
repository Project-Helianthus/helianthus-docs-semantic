package imports_test

import (
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

func TestProbesImportSemRegAndNoGateway(t *testing.T) {
	modRoot := filepath.Clean(filepath.Join("..", ".."))
	probeRoot := filepath.Clean("..")
	mod, err := os.ReadFile(filepath.Join(modRoot, "go.mod"))
	if err != nil {
		t.Fatal(err)
	}
	text := string(mod)
	if strings.Contains(text, "replace ") || strings.Contains(text, "\nreplace") {
		t.Fatalf("go.mod contains a replace directive:\n%s", text)
	}
	if !strings.Contains(text, "github.com/Project-Helianthus/helianthus-semreg ") {
		t.Fatalf("go.mod does not require semreg:\n%s", text)
	}
	if strings.Contains(text, "gateway") {
		t.Fatalf("go.mod names a gateway module:\n%s", text)
	}
	var goFiles int
	err = filepath.WalkDir(probeRoot, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || !strings.HasSuffix(path, ".go") {
			return nil
		}
		goFiles++
		file, err := parser.ParseFile(token.NewFileSet(), path, nil, parser.ImportsOnly)
		if err != nil {
			return err
		}
		for _, spec := range file.Imports {
			imported, err := strconv.Unquote(spec.Path.Value)
			if err != nil {
				t.Fatal(err)
			}
			if strings.Contains(imported, "gateway") {
				t.Errorf("%s imports %s", path, imported)
			}
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if goFiles == 0 {
		t.Fatal("no Go files under acceptance/probes")
	}
}
