package sa

import "testing"

func TestF(t *testing.T) {
	if Moved() != 1 {
		t.Fatalf("assertion=sa")
	}
}
