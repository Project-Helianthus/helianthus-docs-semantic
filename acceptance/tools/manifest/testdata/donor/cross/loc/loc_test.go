package loc

import "testing"

func TestLocal(t *testing.T) {
	kept := "m"
	if Move() != kept {
		t.Fatalf("assertion=local-name")
	}
	if Stay() != 1 {
		t.Fatalf("assertion=stay-value")
	}
}
