package rqb

import (
	"testing"

	`example.test/closure/cross/rq`
)

func TestRaw(t *testing.T) {
	if rq.Move() != 1 {
		t.Fatalf("assertion=raw")
	}
}
