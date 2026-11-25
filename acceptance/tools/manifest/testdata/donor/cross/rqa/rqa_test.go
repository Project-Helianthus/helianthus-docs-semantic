package rqa

import (
	"testing"

	"example.test/closure/cross/rq"
)

func TestQuoted(t *testing.T) {
	if rq.Move() != 1 {
		t.Fatalf("assertion=quoted")
	}
}
