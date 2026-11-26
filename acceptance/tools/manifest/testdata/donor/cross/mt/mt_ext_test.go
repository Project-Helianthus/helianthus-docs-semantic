package mt_test

import (
	"testing"

	"example.test/closure/cross/mt"
)

func TestX(t *testing.T) {
	if mt.Move() != 1 {
		t.Fatalf("assertion=same")
	}
	if mt.Keep() != 2 {
		t.Fatalf("assertion=kept")
	}
}
