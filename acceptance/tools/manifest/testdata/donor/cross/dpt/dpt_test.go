package dpt

import (
	"testing"

	. "example.test/closure/cross/dp"
)

func TestDot(t *testing.T) {
	if Move() != 1 {
		t.Fatalf("assertion=dot")
	}
}
