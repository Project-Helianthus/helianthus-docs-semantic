package um

import (
	"testing"

	"example.test/closure/cross/ub"
)

func TestSeparate(t *testing.T) {
	if Moved() != 1 {
		t.Fatalf("assertion=moved")
	}
	if ub.Retained() != 2 {
		t.Fatalf("assertion=retained")
	}
}
