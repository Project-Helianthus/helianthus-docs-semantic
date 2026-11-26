package meth

import "testing"

func TestRecordValue(t *testing.T) {
	var r Record
	if r.Value() != 0 {
		t.Fatalf("assertion=record-value")
	}
}
