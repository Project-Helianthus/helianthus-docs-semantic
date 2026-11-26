package da

import "testing"

func TestBehaviour(t *testing.T) {
	if MoveA() != 1 {
		t.Fatalf("assertion=same")
	}
	if KeepA() != 2 {
		t.Fatalf("assertion=keep")
	}
}
