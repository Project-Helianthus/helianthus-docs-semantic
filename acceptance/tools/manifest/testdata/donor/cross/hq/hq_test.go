package hq

import "testing"

func TestViaHelper(t *testing.T) {
	if wrap() != 1 {
		t.Fatalf("assertion=via-helper")
	}
}
