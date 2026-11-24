package virtual

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	v1 "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/graph"

	"github.com/Project-Helianthus/helianthus-docs-semantic/acceptance/probes/support"
)

func validOptions() json.RawMessage {
	return json.RawMessage(`{"installation":"installation.probe","slot":"slot.total"}`)
}

func TestTransportFreePlanAndDurableKey(t *testing.T) {
	var factory Factory
	if err := factory.Descriptor().Validate(); err != nil {
		t.Fatal(err)
	}
	for _, transport := range []json.RawMessage{nil, json.RawMessage("null")} {
		plans, err := factory.Plan(driver.Config{Instance: "total", Enabled: true, Transport: transport, Options: validOptions(), SecretRef: "secret.virtual"})
		if err != nil {
			t.Fatalf("transport %s: %v", transport, err)
		}
		if len(plans) != 1 || len(plans[0].Transports) != 0 || plans[0].Instance != "total" || plans[0].Driver != Kind {
			t.Fatalf("plans = %+v", plans)
		}
		if err := plans[0].Validate(); err != nil {
			t.Fatal(err)
		}
		encoded, err := json.Marshal(plans[0])
		if err != nil {
			t.Fatal(err)
		}
		if strings.Contains(string(encoded), "secret.virtual") {
			t.Fatalf("plan carries the secret: %s", encoded)
		}
	}
	disabled, err := factory.Plan(driver.Config{Instance: "total", Options: validOptions()})
	if err != nil || len(disabled) != 0 {
		t.Fatalf("disabled = %+v %v", disabled, err)
	}
	if _, err := factory.Plan(driver.Config{Instance: "total", Enabled: true, Transport: json.RawMessage(`{"bus":"x"}`), Options: validOptions()}); err == nil {
		t.Fatal("accepted a transport operand")
	}
	if _, err := factory.Plan(driver.Config{Instance: "total", Enabled: true, Options: json.RawMessage(`{"installation":"installation.probe","slot":"slot.total","bus":"x"}`)}); err == nil {
		t.Fatal("accepted an unknown options member")
	}

	plans, err := factory.Plan(driver.Config{Instance: "total", Enabled: true, Options: validOptions()})
	if err != nil {
		t.Fatal(err)
	}
	inst, err := factory.Construct(context.Background(), plans[0])
	if err != nil {
		t.Fatal(err)
	}
	got := inst.(*Instance)
	if got.Node.Installation != Installation || got.Node.Driver != Kind || got.Node.Instance != "total" || got.Node.Anchor.Slot != Slot {
		t.Fatalf("node = %+v", got.Node)
	}
	if got.Node.Anchor.Scheme != "" || got.Node.Anchor.Key != "" {
		t.Fatalf("configured anchor also carries a native anchor: %+v", got.Node.Anchor)
	}
	if got.Origin.Kind != driver.OriginDeclared || len(got.Origin.Evidence) != 1 {
		t.Fatalf("origin = %+v", got.Origin)
	}
	if got.Link.Key.From.Bridge == got.Link.Key.To.Bridge || got.Link.Key.From.ID == "" || got.Link.Key.To.ID == "" {
		t.Fatalf("link = %+v", got.Link.Key)
	}
	if err := got.Start(context.Background(), session{}); err != nil {
		t.Fatal(err)
	}
	if !got.Started() {
		t.Fatal("start did not stick")
	}
	if report := got.Stop(context.Background()); !report.Confirmed || report.Err != nil {
		t.Fatalf("stop = %+v", report)
	}
}

func TestDerivedOriginKindValidates(t *testing.T) {
	origin := support.Origin(driver.OriginDerived, "derived-total")
	if err := origin.Validate(); err != nil {
		t.Fatal(err)
	}
	if origin.Kind == driver.OriginMeasured {
		t.Fatal("derived kind equals measured")
	}
}

type session struct{}

func (session) Native() driver.NativeRegistry             { return nil }
func (session) SemanticInput() driver.SemanticInput       { return idleInput{} }
func (session) ScopedOperations() driver.ScopedOperations { return nil }
func (session) Calendar() driver.Calendar                 { return nil }
func (session) Publisher() driver.Publisher               { return idlePublisher{} }
func (session) RegisterExecutor(driver.SettingRoute, driver.Executor) (func(), error) {
	return nil, errors.New("the merged module exports no executor registry")
}

type idleInput struct{}

func (idleInput) Capture(context.Context, driver.Filter) (driver.SemanticCut, error) {
	return driver.SemanticCut{}, errors.New("the merged module exports no capture runtime")
}

func (idleInput) Resume(context.Context, driver.Cursor, driver.Filter) (driver.Changes, error) {
	return driver.Changes{}, errors.New("the merged module exports no resume runtime")
}

func (idleInput) RetrieveLens(context.Context, graph.CutRef, graph.LensRequest) (graph.LensResult, error) {
	return graph.LensResult{}, errors.New("the merged module exports no session lens runtime")
}

func (idleInput) SumMembers(context.Context, graph.CutRef, graph.LensRequest, v1.DefinitionRef, v1.ResourceID) (graph.MemberSum, error) {
	return graph.MemberSum{}, errors.New("the merged module exports no session sum runtime")
}

type idlePublisher struct{}

func (idlePublisher) Begin(context.Context) (driver.PublicationTransaction, error) {
	return nil, errors.New("the merged module exports no publication runtime")
}
