package ext

import (
	"testing"

	"example.test/closure/cross/ex"
)

func TestViaImport(t *testing.T) {
	if ex.Move() != 1 {
		t.Fatalf("assertion=via-import")
	}
}

func TestMixedImport(t *testing.T) {
	if ex.Move() != 1 {
		t.Fatalf("assertion=mixed-moved")
	}
	if Keep() != 1 {
		t.Fatalf("assertion=mixed-kept")
	}
}
