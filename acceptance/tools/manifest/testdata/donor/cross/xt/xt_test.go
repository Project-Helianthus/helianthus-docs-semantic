package xt_test

import (
	"testing"

	"example.test/closure/cross/xt"
)

func TestExternal(t *testing.T) {
	if xt.Move() != 1 {
		t.Fatalf("assertion=external-moved")
	}
	if xt.Keep() != 2 {
		t.Fatalf("assertion=external-kept")
	}
}
