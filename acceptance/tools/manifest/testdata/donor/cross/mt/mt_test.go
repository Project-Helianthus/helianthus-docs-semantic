package mt

import "testing"

func TestX(t *testing.T) {
	if Move() != 1 {
		t.Fatalf("assertion=same")
	}
	if Keep() != 2 {
		t.Fatalf("assertion=kept")
	}
}
