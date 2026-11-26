package tt

import (
	"testing"

	"example.test/closure/cross/tbr"
)

func TestBridged(t *testing.T) {
	if tbr.Receiver.M() != 1 {
		t.Fatalf("assertion=bridged")
	}
}
