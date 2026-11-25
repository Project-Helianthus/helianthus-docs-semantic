package shadow

import "testing"

func TestShadowed(t *testing.T) {
	got := Moved()
	{
		got := Other()
		_ = got
	}
	if got != 1 {
		t.Fatalf("assertion=outer")
	}
	if Host != 1 {
		t.Fatalf("assertion=host")
	}
}

func TestShadowedHeader(t *testing.T) {
	got := Moved()
	if got := Other(); got != 2 {
		t.Fatalf("assertion=header")
	}
	if got != 1 {
		t.Fatalf("assertion=after-header")
	}
	if Host != 1 {
		t.Fatalf("assertion=host")
	}
}
