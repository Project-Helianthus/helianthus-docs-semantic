package host

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	v1 "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/catalog"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"
)

func composedFamily() catalog.Family {
	return catalog.Family{
		FamilyID: "probe-meter", Name: "Probe meter", NativeOwner: "Project-Helianthus/helianthus-docs-semantic",
		SemanticPack: "helianthus.pack.infrastructure@1.0.0", State: v1.QualificationQualified,
		Composition: catalog.CompositionComposed, Reason: catalog.ReasonDeclaredBySpecification,
		Evidence: []catalog.Evidence{{
			Owner: "Project-Helianthus/helianthus-docs-semantic", Kind: catalog.EvidenceKindSpecification,
			Locator: "api/v1/driver-contract.md", Statement: "the driver contract is the composition surface this probe consumes",
		}},
		CompositionVerified: true, Verification: catalog.VerificationNotTestedOnHardware,
		Module: "github.com/Project-Helianthus/helianthus-docs-semantic/acceptance/probes/host", Version: "v0.0.0",
	}
}

func idleFamily() catalog.Family {
	return catalog.Family{
		FamilyID: "probe-idle", Name: "Probe idle", NativeOwner: "Project-Helianthus/helianthus-docs-semantic",
		State: v1.QualificationUnknown, Composition: catalog.CompositionNotComposed, Reason: catalog.ReasonNoProducer,
		Evidence: []catalog.Evidence{{
			Owner: "Project-Helianthus/helianthus-docs-semantic", Kind: "note",
			Locator: "acceptance/probes/README.md", Statement: "this probe family claims no composition",
		}},
		Verification: catalog.VerificationNotTestedOnHardware,
	}
}

type probeFactory struct {
	families []catalog.Family
	seen     driver.Config
	planned  int
}

func (f *probeFactory) Descriptor() driver.Descriptor {
	return driver.Descriptor{Families: f.families}
}

func (f *probeFactory) Plan(c driver.Config) ([]driver.InstancePlan, error) {
	f.seen = c
	f.planned++
	if !c.Enabled {
		return nil, nil
	}
	return []driver.InstancePlan{{Driver: driver.DriverKind("driver." + c.Instance), Instance: driver.InstanceKey(c.Instance)}}, nil
}

func (f *probeFactory) Construct(_ context.Context, p driver.InstancePlan) (driver.Instance, error) {
	if err := p.Validate(); err != nil {
		return nil, err
	}
	return &probeInstance{plan: p}, nil
}

type earlyFactory struct {
	probeFactory
	args  []string
	calls int
}

func (f *earlyFactory) DispatchEarly(_ context.Context, args []string) (bool, int, error) {
	f.calls++
	f.args = append([]string(nil), args...)
	if len(args) > 0 && args[0] == "child" {
		return true, 3, nil
	}
	if len(args) > 0 && args[0] == "fail" {
		return true, 1, errors.New("child failed")
	}
	return false, 0, nil
}

type probeInstance struct {
	plan    driver.InstancePlan
	session driver.Session
}

func (i *probeInstance) Start(_ context.Context, s driver.Session) error {
	i.session = s
	return nil
}

func (i *probeInstance) FenceWithdrawal() {}

func (i *probeInstance) Stop(context.Context) driver.CloseReport {
	return driver.CloseReport{Confirmed: true}
}

type markedSession struct{ mark string }

func (markedSession) Native() driver.NativeRegistry             { return nil }
func (markedSession) SemanticInput() driver.SemanticInput       { return nil }
func (markedSession) ScopedOperations() driver.ScopedOperations { return nil }
func (markedSession) Calendar() driver.Calendar                 { return nil }
func (markedSession) Publisher() driver.Publisher               { return nil }
func (markedSession) RegisterExecutor(driver.SettingRoute, driver.Executor) (func(), error) {
	return nil, errors.New("the merged module exports no executor registry")
}

type opener struct{ marks []string }

func (o *opener) Open(p driver.InstancePlan) (driver.Session, error) {
	o.marks = append(o.marks, string(p.Instance))
	return markedSession{mark: string(p.Instance)}, nil
}

func TestHostComposesTwoDrivers(t *testing.T) {
	meter := &probeFactory{families: []catalog.Family{composedFamily()}}
	idle := &probeFactory{families: []catalog.Family{idleFamily()}}
	drivers := []Bound{
		{Factory: meter, Config: driver.Config{Instance: "meter", Enabled: true, Transport: json.RawMessage(`{"endpoint":"meter"}`), Options: json.RawMessage(`{"mode":"read"}`), SecretRef: "secret.meter"}},
		{Factory: idle, Config: driver.Config{Instance: "idle", Enabled: true, Options: json.RawMessage(`{}`)}},
	}
	if err := Families(drivers).Validate(); err != nil {
		t.Fatalf("families: %v", err)
	}
	got := Families(drivers)
	if len(got.Families) != 2 || got.Families[0].FamilyID != "probe-meter" || got.Families[1].FamilyID != "probe-idle" {
		t.Fatalf("families = %+v", got.Families)
	}
	sessions := &opener{}
	result, err := Compose(context.Background(), drivers, sessions, nil)
	if err != nil {
		t.Fatal(err)
	}
	if result.Handled || len(result.Started) != 2 {
		t.Fatalf("result = %+v", result)
	}
	if meter.seen.SecretRef != "secret.meter" || idle.seen.SecretRef != "" {
		t.Fatalf("secret handoff meter=%q idle=%q", meter.seen.SecretRef, idle.seen.SecretRef)
	}
	if meter.seen.SecretRef == idle.seen.SecretRef {
		t.Fatal("the two instances share one secret reference")
	}
	encoded, err := json.Marshal(result.Started)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(encoded), "secret.meter") {
		t.Fatalf("a plan carries the secret reference: %s", encoded)
	}
	if string(meter.seen.Transport) != `{"endpoint":"meter"}` || string(meter.seen.Options) != `{"mode":"read"}` {
		t.Fatalf("factory operands = %s %s", meter.seen.Transport, meter.seen.Options)
	}
	if string(idle.seen.Transport) != "" || string(idle.seen.Options) != `{}` {
		t.Fatalf("second factory saw %s %s", idle.seen.Transport, idle.seen.Options)
	}
	seen := map[driver.InstanceKey]driver.Session{}
	for _, running := range result.Started {
		if err := running.Plan.Validate(); err != nil {
			t.Fatalf("plan: %v", err)
		}
		inst := running.Instance.(*probeInstance)
		if inst.session == nil {
			t.Fatalf("instance %s started without a session", running.Plan.Instance)
		}
		if seen[running.Plan.Instance] != nil {
			t.Fatalf("duplicate instance %s", running.Plan.Instance)
		}
		seen[running.Plan.Instance] = inst.session
	}
	if seen["meter"] == seen["idle"] {
		t.Fatal("both instances received one session")
	}
	if _, plain := any(meter).(driver.EarlyDispatcher); plain {
		t.Fatal("a factory without early dispatch implements it")
	}
}

func TestDisabledInstanceIsNotConstructed(t *testing.T) {
	factory := &probeFactory{}
	result, err := Compose(context.Background(), []Bound{{
		Factory: factory, Config: driver.Config{Instance: "meter", Enabled: false, SecretRef: "secret.meter"},
	}}, &opener{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if factory.planned != 1 || factory.seen.Enabled || len(result.Started) != 0 {
		t.Fatalf("planned=%d enabled=%v started=%d", factory.planned, factory.seen.Enabled, len(result.Started))
	}
}

func TestEarlyDispatchReturnsBeforePlanning(t *testing.T) {
	early := &earlyFactory{probeFactory: probeFactory{families: []catalog.Family{idleFamily()}}}
	plain := &probeFactory{families: []catalog.Family{composedFamily()}}
	drivers := []Bound{
		{Factory: early, Config: driver.Config{Instance: "early", Enabled: true}},
		{Factory: plain, Config: driver.Config{Instance: "plain", Enabled: true}},
	}
	ctx := context.Background()
	handled, err := Compose(ctx, drivers, &opener{}, []string{"child", "--flag"})
	if err != nil || !handled.Handled || handled.ExitCode != 3 || len(handled.Started) != 0 || early.planned != 0 || plain.planned != 0 {
		t.Fatalf("handled exit: %+v %v planned=%d,%d", handled, err, early.planned, plain.planned)
	}
	failed, err := Compose(ctx, drivers, &opener{}, []string{"fail"})
	if err == nil || !failed.Handled || failed.ExitCode != 1 || early.planned != 0 {
		t.Fatalf("handled error: %+v %v", failed, err)
	}
	early.planned, plain.planned = 0, 0
	continued, err := Compose(ctx, drivers, &opener{}, []string{"serve"})
	if err != nil || continued.Handled || len(continued.Started) != 2 || early.calls == 0 || plain.planned != 1 {
		t.Fatalf("continue: %+v %v calls=%d planned=%d", continued, err, early.calls, plain.planned)
	}
}

func TestCompositionEvidenceRules(t *testing.T) {
	if err := (driver.Descriptor{Families: []catalog.Family{composedFamily(), idleFamily()}}).Validate(); err != nil {
		t.Fatal(err)
	}
	missingModule := composedFamily()
	missingModule.Module = ""
	if err := (driver.Descriptor{Families: []catalog.Family{missingModule}}).Validate(); err == nil {
		t.Fatal("accepted a claimed composition without a module")
	}
	missingVersion := composedFamily()
	missingVersion.Version = ""
	if err := (driver.Descriptor{Families: []catalog.Family{missingVersion}}).Validate(); err == nil {
		t.Fatal("accepted a claimed composition without a version")
	}
	carries := idleFamily()
	carries.Module = "synthetic.module"
	if err := (driver.Descriptor{Families: []catalog.Family{carries}}).Validate(); err == nil {
		t.Fatal("accepted not_composed carrying a module")
	}
	hardware := composedFamily()
	hardware.Verification = catalog.VerificationTestedOnHardware
	if err := (driver.Descriptor{Families: []catalog.Family{hardware}}).Validate(); err == nil {
		t.Fatal("accepted tested_on_hardware without a hardware test record")
	}
}
