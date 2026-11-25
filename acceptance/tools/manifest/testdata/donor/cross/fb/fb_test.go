package fb

import "testing"

func TestFatalBranch(t *testing.T) {
	got := Moved()
	if testing.Short() {
		got = Stay()
		t.FailNow()
	}
	if got != 1 {
		t.Fatalf("assertion=moved-result")
	}
}
