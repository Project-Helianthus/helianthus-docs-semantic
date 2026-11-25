package xi_test

import "testing"

func F() int { return 2 }

func TestExternal(t *testing.T) {
	if F() != 2 {
		t.Fatalf("assertion=ext-f")
	}
}
