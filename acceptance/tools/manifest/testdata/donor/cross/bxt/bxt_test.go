package bxt

import (
	"testing"

	"example.test/closure/cross/bx"
)

func TestCount(t *testing.T) {
	var b bx.Box
	if b.Count() != 1 {
		t.Fatalf("assertion=count")
	}
}
