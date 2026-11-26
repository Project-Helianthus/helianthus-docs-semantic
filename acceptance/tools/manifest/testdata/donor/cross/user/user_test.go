package user

import (
	"testing"

	"example.test/closure/cross/far"
)

func TestFar(t *testing.T) {
	if far.Move() != 1 {
		t.Fatalf("assertion=far-moved")
	}
}
