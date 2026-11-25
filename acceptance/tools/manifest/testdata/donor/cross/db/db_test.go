package db

import "testing"

func TestBehaviour(t *testing.T) {
	if MoveB() != 1 {
		t.Fatalf("assertion=same")
	}
	if KeepB() != 2 {
		t.Fatalf("assertion=keep")
	}
}
