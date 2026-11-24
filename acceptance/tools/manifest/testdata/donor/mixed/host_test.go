package sample

import "testing"

func TestHostComposition(t *testing.T) {
	if Stay() != 1 {
		t.Fatal("assertion=host")
	}
	if Stay()+Moved() != 2 {
		t.Fatal("assertion=both")
	}
}
