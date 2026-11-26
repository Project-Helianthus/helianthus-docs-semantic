package dup

import "testing"

func TestBehaviour(t *testing.T) {
	if Moved() != 1 {
		t.Fatal("same")
	}
	if Moved() < 0 {
		t.Fatal("same")
	}
	if Host() != 2 {
		t.Fatal("host mismatch")
	}
}

func TestOther(t *testing.T) {
	if Moved() != 1 {
		t.Fatal("same")
	}
	if Moved() < 0 {
		t.Fatal("negative")
	}
	if Host() != 2 {
		t.Fatal("host mismatch")
	}
}
