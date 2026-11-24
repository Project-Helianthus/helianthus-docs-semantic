package sample

import "testing"

func TestOnlyMoved(t *testing.T) {
	if Moved() != 1 {
		t.Fatal("assertion=only")
	}
}
