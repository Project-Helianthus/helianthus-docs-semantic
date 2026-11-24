package remote

import (
	"reflect"
	"testing"

	v1 "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"

	"github.com/Project-Helianthus/helianthus-docs-semantic/acceptance/probes/support"
)

func TestPreserveKeepsBridgeIDAndProvenance(t *testing.T) {
	const localID = "resource:meter"
	left := support.Node("bridge.east", localID)
	right := support.Node("bridge.west", localID)
	provenance := support.Origin(driver.OriginMeasured, "remote-observation")
	gotLeft, err := Preserve(left, provenance)
	if err != nil {
		t.Fatal(err)
	}
	gotRight, err := Preserve(right, provenance)
	if err != nil {
		t.Fatal(err)
	}
	if gotLeft.Ref != left || gotRight.Ref != right {
		t.Fatalf("preserved %+v %+v", gotLeft.Ref, gotRight.Ref)
	}
	if gotLeft.Ref == gotRight.Ref || gotLeft.Ref.ID != gotRight.Ref.ID {
		t.Fatalf("bridge pair collapsed: %+v %+v", gotLeft.Ref, gotRight.Ref)
	}
	if gotLeft.Provenance.Kind != driver.OriginMeasured || len(gotLeft.Provenance.Evidence) != 1 {
		t.Fatalf("provenance = %+v", gotLeft.Provenance)
	}
	if gotLeft.Provenance.Evidence[0].Digest != provenance.Evidence[0].Digest {
		t.Fatalf("digest = %s", gotLeft.Provenance.Evidence[0].Digest)
	}
	provenance.Evidence[0].Digest = v1.Digest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
	if gotLeft.Provenance.Evidence[0].Digest == provenance.Evidence[0].Digest {
		t.Fatal("local provenance follows a later change of the input evidence")
	}
	fields := reflect.TypeOf(driver.NodeRef{})
	if fields.NumField() != 2 || fields.Field(0).Name != "Bridge" || fields.Field(1).Name != "ID" {
		t.Fatalf("NodeRef fields changed")
	}
}

func TestExplicitResyncCarriesNoCommits(t *testing.T) {
	cursor := driver.Cursor{Incarnation: "incarnation.probe", Position: "1"}
	if err := (driver.Changes{Cursor: cursor, Resync: true}).Validate(); err != nil {
		t.Fatal(err)
	}
	if err := (driver.Changes{Cursor: cursor, Resync: true, Commits: []driver.SemanticCut{support.Cut("cut-probe")}}).Validate(); err == nil {
		t.Fatal("accepted a resync that carries commits")
	}
}
