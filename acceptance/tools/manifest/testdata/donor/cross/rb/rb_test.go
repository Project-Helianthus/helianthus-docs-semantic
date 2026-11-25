package rb

import "testing"

func TestBranch(t *testing.T) {
	got := Moved()
	if testing.Short() {
		if Stay() != 2 {
			t.Fatalf("assertion=short-stay")
		}
		got = Stay()
		return
	}
	if got != 1 {
		t.Fatalf("assertion=moved-result")
	}
}
