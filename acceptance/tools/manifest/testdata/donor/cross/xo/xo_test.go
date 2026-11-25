package xo_test

import (
	"testing"

	"example.test/closure/cross/xo"
)

func kept() int { return 2 }

func TestOwn(t *testing.T) {
	if xo.Move()+kept() != 3 {
		t.Fatalf("assertion=own-mixed")
	}
}

func TestOwnSplit(t *testing.T) {
	if xo.Move() != 1 {
		t.Fatalf("assertion=own-moved")
	}
	if kept() != 2 {
		t.Fatalf("assertion=own-kept")
	}
}
