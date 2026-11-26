package alpha

import "testing"

func TestStoreBehaviour(t *testing.T) {
	if cloneRecord(Record{}).Name != "" {
		t.Fatalf("assertion=clone-name")
	}
	if kept("x") != "x" {
		t.Fatalf("assertion=kept-value")
	}
}
