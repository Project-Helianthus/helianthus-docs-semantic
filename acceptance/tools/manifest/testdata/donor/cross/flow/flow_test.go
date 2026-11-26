package flow

import "testing"

func TestFlowAssigned(t *testing.T) {
	got := Moved()
	if got != 1 {
		t.Fatalf("assertion=assigned")
	}
	if Host != 1 {
		t.Fatalf("assertion=host")
	}
}

func TestFlowDeclared(t *testing.T) {
	var got int
	got = Moved()
	if got != 1 {
		t.Fatalf("assertion=declared")
	}
	if Host != 1 {
		t.Fatalf("assertion=host")
	}
}

func TestFlowHost(t *testing.T) {
	got := Moved()
	if got != Host {
		t.Fatalf("assertion=with-host")
	}
}
