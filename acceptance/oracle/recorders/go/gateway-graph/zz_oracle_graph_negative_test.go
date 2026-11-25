package main

import (
	"bytes"
	"context"
	"errors"
	"strconv"
	"strings"
	"testing"
	"time"

	ebusgateway "github.com/Project-Helianthus/helianthus-ebusgateway"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/portalconfig"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semanticoperations"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semanticoperations/semoptest"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semgraph"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semhub"
	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/operation"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/evse"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/infrastructure"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/pv"
)

// ogUnchanged states whether the asset's canonical snapshot bytes are the ones
// taken before an attempt.
func ogUnchanged(before, after []byte) string {
	if bytes.Equal(before, after) {
		return "the asset's snapshot bytes are unchanged"
	}
	return "the asset's snapshot bytes changed"
}

func ogAwaitStates(t *testing.T, f *oraFixture, saved portalconfig.OperatorRecordSet) []string {
	t.Helper()
	deadline := time.Now().Add(5 * time.Second)
	for {
		states := opr27States(t, f.records, saved)
		waiting := false
		for _, state := range states {
			waiting = waiting || strings.HasPrefix(state, "waiting:")
		}
		if !waiting || time.Now().After(deadline) {
			return states
		}
		time.Sleep(5 * time.Millisecond)
	}
}

// ogDeclared is newOraFixture with the graph enforcement of the declared
// assets chosen by the caller; a first publication that the kernel refuses is
// returned instead of ending the recording.
func ogDeclared(t *testing.T, pack func() semreg.PackValidator, paths []*oraPath, graphEnforced bool) (*oraFixture, []error) {
	t.Helper()
	hub, err := semhub.New(semhub.Options{})
	if err != nil {
		t.Fatal(err)
	}
	f := &oraFixture{hub: hub, start: time.Now()}
	declaring, err := newOperatorRecordPublisher(hub, operatorRecordOptions{})
	if err != nil {
		t.Fatal(err)
	}
	for _, path := range paths {
		if _, err := hub.Declare(semhub.AssetSpec{AssetID: path.asset, SourceID: path.source, Driver: path.driver, Validators: []semreg.PackValidator{pack()}, Graph: graphEnforced,
			Contributors: []semhub.ContributorSpec{declaring.Contributor(pack())}}); err != nil {
			t.Fatalf("declare %s: %v", path.asset, err)
		}
	}
	refused := []error{}
	for _, path := range paths {
		if path.handle, err = hub.AdmitSource(semhub.Admission{Source: path.source, Driver: path.driver}); err != nil {
			t.Fatal(err)
		}
		refused = append(refused, f.publish(t, path, nil))
	}
	return f, refused
}

func ogRelationInstance(definition semreg.DefinitionRef, from, to semreg.ResourceID, f *oraFixture, p *oraPath) semreg.RelationInstance {
	source, epoch, binding := p.source, p.handle.Epoch(), semreg.NativeBindingID("")
	if len(f.inspect2(p).Snapshot.Bindings) != 0 {
		binding = f.inspect2(p).Snapshot.Bindings[0].BindingID
	}
	evidence := oraEvidence("oratest.observation", string(from)+"/"+string(to))
	return semreg.RelationInstance{Definition: definition, From: from, To: to, State: semreg.LinkQualified, BasisClass: semreg.RelationNativeObservation, Basis: []semreg.EvidenceRef{evidence},
		Origin:   semreg.OriginRef{OriginID: semreg.OriginID("origin:ora:" + oraHash("relation", string(from), string(to))[:24]), Kind: semreg.OriginNativeObservation, SourceID: &source, SourceEpochID: &epoch, BindingID: &binding, Evidence: []semreg.EvidenceRef{evidence}},
		Revision: "1"}
}

func (f *oraFixture) inspect2(p *oraPath) semhub.InspectView {
	view, err := f.hub.Inspect(p.asset)
	if err != nil || !view.Present {
		return semhub.InspectView{}
	}
	return view
}

func TestOracleGraphNegativeDuplicateIdentity(t *testing.T) {
	scenarios := []ogScenario{}

	first := &oraPath{asset: "asset:dup-a", source: "source:dup-a", driver: "driver-dup-a", kind: "resource.meter", class: semreg.AnchorEquipment, resource: "resource:dup:meter", slot: "meter-1"}
	second := &oraPath{asset: "asset:dup-b", source: "source:dup-b", driver: "driver-dup-b", kind: "resource.meter", class: semreg.AnchorEquipment, resource: "resource:dup:meter", slot: "meter-1"}
	f, refused := ogDeclared(t, infrastructure.New, []*oraPath{first, second}, true)
	scenarios = append(scenarios, ogScenario{Case: "one resource identifier homed in two assets", Fixture: "oraFixture: two synthetic drivers whose first batches each carry the same resource identifier",
		Outcomes: []ogOutcome{ogAnswer("first driver's first batch", "publish resource:dup:meter in asset:dup-a", refused[0]), ogAnswer("second driver's first batch", "publish resource:dup:meter in asset:dup-b", refused[1])},
		State:    ogState(t, f.hub, "dup-resource")})

	hub, err := semhub.New(semhub.Options{})
	if err != nil {
		t.Fatal(err)
	}
	if err := composeDeclaredPairings(hub, []semanticPairing{pairingDeclaration()}); err != nil {
		t.Fatal(err)
	}
	_, claim := hub.Declare(semhub.AssetSpec{AssetID: pairingAsset, SourceID: "source:pairtest:third", Driver: pairingThirdDriver, Validators: []semreg.PackValidator{pv.New()}, Graph: true})
	var collision *semhub.CollisionError
	outcomes := []ogOutcome{ogAnswer("second claimant of the paired asset", "declare the asset of the pairing under another driver", claim)}
	outcomes[0].Detail = append(outcomes[0].Detail, "the refusal is a collision error: "+boolText(errors.As(claim, &collision)))
	third, err := hub.AdmitSource(semhub.Admission{Source: "source:pairtest:third", Driver: pairingThirdDriver})
	if err != nil {
		t.Fatal(err)
	}
	tx, begin := hub.Begin(third, pairingAsset)
	if tx != nil {
		tx.Abort()
	}
	outcomes = append(outcomes, ogAnswer("undeclared source on the paired asset", "begin a transaction on the paired asset", begin))
	scenarios = append(scenarios, ogScenario{Case: "a second claimant of one declared asset", Fixture: "TestSemanticMultiSourceAcceptanceUndeclaredClaimantsStayFatal and TestSemanticMultiSourceAcceptanceOneUnitThroughTwoPaths: the declared pairing", Outcomes: outcomes})

	growatt, tesla := growattProductionConfig(), teslaRetainedConfig()
	tesla.AssetID = growatt.AssetID
	_, preflight := preflightSemanticHub(ebusgateway.Config{ModbusTCPConfig: ebusgateway.ModbusTCPConfig{GrowattBMSRS485: growatt, TeslaGen3HSC: tesla}})
	scenarios = append(scenarios, ogScenario{Case: "one configured asset identifier in two families", Fixture: "preflightSemanticHub: the storage and the EVSE configuration name one asset identifier",
		Outcomes: []ogOutcome{ogAnswer("startup preflight", "declare the storage and the EVSE asset under one identifier", preflight)}})

	ogOut(t, "negative-duplicate-identity.json", ogNegative("duplicate identity", "The pin refuses a second claimant of one asset at declaration; a resource identifier that two assets each carry is not refused at publication, and the cut reports it as a duplicate identity finding and excludes the members.", scenarios...))
}

func boolText(value bool) string {
	if value {
		return "yes"
	}
	return "no"
}

func TestOracleGraphNegativeFalseJoin(t *testing.T) {
	scenarios := []ogScenario{}

	direct := &oraPath{asset: "asset:ora-direct", source: "source:ora-direct", driver: "driver-ora-direct", kind: "resource.meter", class: semreg.AnchorEquipment, resource: "resource:ora:direct-meter", slot: "meter-1"}
	relayed := &oraPath{asset: "asset:ora-relayed", source: "source:ora-relayed", driver: "driver-ora-relayed", kind: "resource.meter", class: semreg.AnchorEquipment, resource: "resource:ora:relayed-meter", slot: "port-3"}
	f := newOraFixture(t, infrastructure.New, []*oraPath{direct, relayed})
	before := map[semreg.AssetID][]byte{direct.asset: f.inspect(t, direct.asset).Canonical, relayed.asset: f.inspect(t, relayed.asset).Canonical}
	join := oraDecode(t, `{"format": "helianthus.portal-config.operator-records/v1", "revision": "0", "records": [
    {"form": "pairing", "kind": "resource.meter", "slot": "meter-main", "views": [
      {"home": "asset:ora-direct", "resource_id": "resource:ora:direct-meter"},
      {"home": "asset:ora-relayed", "resource_id": "resource:ora:relayed-meter"}
    ]}]}`)
	saved, err := f.records.Replace(context.Background(), join)
	if err != nil {
		t.Fatal(err)
	}
	states := ogAwaitStates(t, f, saved)
	outcome := ogOutcome{Case: "pairing of two different native anchors", Attempt: "declare one operator pairing of resource:ora:direct-meter (slot meter-1) and resource:ora:relayed-meter (slot port-3)", Answer: "record status " + strings.Join(states, ",")}
	for _, path := range []*oraPath{direct, relayed} {
		outcome.Detail = append(outcome.Detail, string(path.asset)+": "+ogUnchanged(before[path.asset], f.inspect(t, path.asset).Canonical))
	}
	scenarios = append(scenarios, ogScenario{Case: "operator pairing over native evidence", Fixture: "TestOperatorRecordAcceptanceRefusesAJoinOfDifferentNativeAnchors", Outcomes: []ogOutcome{outcome}, State: ogState(t, f.hub, "false-join-pairing")})

	hub := newTestSemanticHub(t)
	second := growattProductionConfig()
	second.AssetID, second.SourceID, second.SourceEpoch, second.UnitID = "asset:growatt-bms-b", "growatt-bms-b", "source-epoch-b", 8
	for _, config := range []ebusgateway.GrowattBMSRS485Config{growattProductionConfig(), second} {
		runtime := startGrowattRuntimeWithFakeOn(t, config, &growattEndpointFake{words: growattBMSProductionWords(), failAt: -1, mismatch: -1, generation: 1}, hub)
		if _, err := runtime.GrowattStorageSemanticCurrent(context.Background()); err != nil {
			t.Fatal(err)
		}
	}
	resources, err := semanticResourceAllocatorFor(hub)
	if err != nil {
		t.Fatal(err)
	}
	slot := growattStoragePackSlot("asset:growatt-bms-a")
	evidence := growattStorageDigestEvidence("operator.storage.pack_label", slot)
	anchor := semgraph.Anchor{Class: semreg.AnchorEquipment, Basis: semreg.AnchorOperatorSlot, Source: semgraph.SourceOperatorLabel, Slot: slot, Evidence: []semreg.EvidenceRef{evidence}}
	_, _, claim := resources.resolve(growattStoragePackKind, anchor, "asset:growatt-bms-b")
	answer := ogAnswer("second storage claims the first pack", "resolve the first storage's pack anchor for asset:growatt-bms-b", claim)
	answer.Identifier = "second_home"
	answer.Detail = append(answer.Detail, "the refusal is the allocator's second-home error: "+boolText(errors.Is(claim, semgraph.ErrSecondHome)))
	scenarios = append(scenarios, ogScenario{Case: "two storage labels never join", Fixture: "TestGrowattStorageGraphTwoLabelsAreTwoPacksAndNeverJoin", Outcomes: []ogOutcome{answer}, State: ogState(t, hub, "false-join-storage")})

	ogOut(t, "negative-false-join.json", ogNegative("false join", "The pin refuses to join two native anchors that differ, and refuses a second home for one resource; the refused join leaves both snapshots byte-identical and the cut holds no same-unit finding.", scenarios...))
}

func TestOracleGraphNegativeMissingMembership(t *testing.T) {
	scenarios := []ogScenario{}

	path := &oraPath{asset: "asset:ungraphed-site", source: "source:ungraphed-site", driver: "driver-ungraphed-site", kind: "resource.grid_connection", class: semreg.AnchorFunction, resource: "resource:ungraphed:connection-1", slot: "connection-1"}
	f, refused := ogDeclared(t, infrastructure.New, []*oraPath{path}, false)
	scenarios = append(scenarios, ogScenario{Case: "a graph member in an asset declared without enforcement", Fixture: "oraFixture variant: the declaration asks for no graph enforcement",
		Outcomes: []ogOutcome{ogAnswer("first batch", "publish a resource record in an asset whose kernel was built without the element catalog", refused[0])},
		State:    ogState(t, f.hub, "membership-ungraphed")})

	g, site := newIGTFixture(t)
	before := g.inspect(t, igtAsset).Canonical
	unlisted := igtDefinition("infrastructure.relation.unlisted")
	err := g.publish(t, site, func(_ *semhub.Tx, batch *semreg.PublicationBatch) {
		batch.RelationUpserts = []semreg.RelationInstance{ogRelationInstance(unlisted, igtSite, igtConnection, g, site)}
	})
	answer := ogAnswer("relation definition outside the catalog", "publish an instance of infrastructure.relation.unlisted from the site to the grid connection", err)
	answer.Detail = append(answer.Detail, ogUnchanged(before, g.inspect(t, igtAsset).Canonical))
	scenarios = append(scenarios, ogScenario{Case: "a relation definition that is not a catalog member", Fixture: "the infrastructure site publisher of TestInfrastructureGraphPublishesTheMeterRoleAsAConfiguredMeasuresInstance", Outcomes: []ogOutcome{answer}, State: ogState(t, g.hub, "membership-catalog")})

	ogOut(t, "negative-missing-membership.json", ogNegative("missing membership", "The pin refuses a graph member that the asset's kernel has no catalog entry for: a record in an asset declared without enforcement, and a relation definition the catalog does not list.", scenarios...))
}

func TestOracleGraphNegativeStaleOrDanglingRelation(t *testing.T) {
	scenarios := []ogScenario{}

	f, site := newIGTFixture(t)
	f.replace(t, oraDecode(t, igtDocument), "published:", "published:")
	meter, ok := oprResourceIn(f.inspect(t, igtAsset).Snapshot, igtMeter)
	if !ok {
		t.Fatal("the fixture holds no meter")
	}
	meter.State = semreg.ResourceWithdrawn
	meter.Revision = "2"
	before := f.inspect(t, igtAsset).Canonical
	err := f.publish(t, site, func(_ *semhub.Tx, batch *semreg.PublicationBatch) {
		batch.ResourceUpserts = []semreg.Resource{meter}
	})
	answer := ogAnswer("driver batch", "withdraw resource:igt:meter-1, which a service and the grid connection's measures relation name", err)
	answer.Detail = append(answer.Detail, ogUnchanged(before, f.inspect(t, igtAsset).Canonical))
	scenarios = append(scenarios, ogScenario{Case: "a resource that a service and a relation name is withdrawn", Fixture: "the infrastructure site publisher with its operator-record section accepted",
		Outcomes: []ogOutcome{answer}, State: ogState(t, f.hub, "withdrawn-far-end")})

	g := newOraFixture(t, infrastructure.New, []*oraPath{oraSitePath(), ogFarMeterPath()})
	unpublished := oraDecode(t, `{"format": "helianthus.portal-config.operator-records/v1", "revision": "0", "records": [
    {"form": "relation", "home": "asset:ora-site",
     "definition": {"pack": {"id": "helianthus.pack.infrastructure", "version": "1.0.0"}, "id": "infrastructure.relation.grid_connection_meter", "version": "1.0.0"},
     "from": "resource:ora:connection-1", "to": "resource:ora:not-published", "basis_class": "configuration"}]}`)
	saved, err := g.records.Replace(context.Background(), unpublished)
	if err != nil {
		t.Fatal(err)
	}
	states := ogAwaitStates(t, g, saved)
	scenarios = append(scenarios, ogScenario{Case: "a configured relation to a resource nobody has published", Fixture: "oraFixture: a site driver and a meter driver, the operator-record section naming an unpublished far end",
		Outcomes: []ogOutcome{{Case: "operator-record section", Attempt: "declare a measures relation from resource:ora:connection-1 to resource:ora:not-published", Answer: "record status " + strings.Join(states, ",")}},
		State:    ogState(t, g.hub, "relation-unpublished-far-end")})

	home := oraSitePath()
	far := ogFarMeterPath()
	h := newOraFixture(t, infrastructure.New, []*oraPath{home, far})
	farRelation := oraDecode(t, `{"format": "helianthus.portal-config.operator-records/v1", "revision": "0", "records": [
    {"form": "relation", "home": "asset:ora-site",
     "definition": {"pack": {"id": "helianthus.pack.infrastructure", "version": "1.0.0"}, "id": "infrastructure.relation.grid_connection_meter", "version": "1.0.0"},
     "from": "resource:ora:connection-1", "to": "resource:ora:far-meter", "basis_class": "configuration"}]}`)
	savedFar, err := h.records.Replace(context.Background(), farRelation)
	if err != nil {
		t.Fatal(err)
	}
	published := ogAwaitStates(t, h, savedFar)
	stateBefore := ogState(t, h.hub, "relation-far-end-in-the-cut")
	h.stop(t, far)
	scenarios = append(scenarios, ogScenario{Case: "the far end belongs to another asset whose source stops", Fixture: "oraFixture: a site driver and a meter driver, the relation configured while both publish, then the meter driver stops",
		Outcomes: []ogOutcome{{Case: "operator-record section", Attempt: "declare a measures relation from resource:ora:connection-1 to resource:ora:far-meter, then stop the meter driver", Answer: "record status " + strings.Join(published, ",")}},
		State:    ogState(t, h.hub, "relation-far-end-source-stopped")})
	scenarios[len(scenarios)-1].Outcomes = append(scenarios[len(scenarios)-1].Outcomes, ogOutcome{Case: "cut before the stop", Attempt: "read the cut while both assets publish", Answer: "relations " + strconv.Itoa(len(stateBefore.Relations)) + ", members " + strconv.Itoa(len(stateBefore.Cut.Members))})

	ogOut(t, "negative-stale-or-dangling-relation.json", ogNegative("stale or dangling relation", "The pin judges each relation instance of the cut as coherent, stale, dangling, outside the cut, excluded or conflicting; a batch that withdraws a resource that is still named, and a configured relation whose far end nobody has published, are answered as recorded.", scenarios...))
}

func ogFarMeterPath() *oraPath {
	return &oraPath{asset: "asset:ora-meter-source", source: "source:ora-meter-source", driver: "driver-ora-meter-source", kind: "resource.meter", class: semreg.AnchorEquipment, resource: "resource:ora:far-meter", slot: "meter-9"}
}

func TestOracleGraphNegativeIdentityDrift(t *testing.T) {
	scenarios := []ogScenario{}

	f, site := newIGTFixture(t)
	f.replace(t, oraDecode(t, igtDocument), "published:", "published:")
	before := f.inspect(t, igtAsset).Canonical
	outcomes := []ogOutcome{}
	for _, negative := range []struct {
		name string
		fact semreg.FactCandidate
	}{
		{"power under the meter dimension", igtFact(t, f, site, igtMeterBinding(t, site), "infrastructure.power.import_active", "infrastructure.dimension.meter", igtMeter, igtQuantity("18", 2, "unit.watt"))},
		{"power whose subject is the meter", igtFact(t, f, site, igtMeterBinding(t, site), "infrastructure.power.export_active", "infrastructure.dimension.grid_connection", igtMeter, igtQuantity("1", 2, "unit.watt"))},
		{"energy under the grid connection dimension", igtFact(t, f, site, site.binding(t), "infrastructure.energy.import", "infrastructure.dimension.grid_connection", igtConnection, igtQuantity("1", 0, "unit.kilowatt_hour"))},
		{"energy whose subject is the grid connection", igtFact(t, f, site, site.binding(t), "infrastructure.energy.export", "infrastructure.dimension.meter", igtConnection, igtQuantity("1", 0, "unit.kilowatt_hour"))},
	} {
		answer := ogAnswer(negative.name, "publish the fact in one batch of the site publisher", igtPublishFacts(t, f, site, negative.fact))
		answer.Detail = append(answer.Detail, ogUnchanged(before, f.inspect(t, igtAsset).Canonical))
		outcomes = append(outcomes, answer)
	}
	scenarios = append(scenarios, ogScenario{Case: "a fact whose subject or dimension names the wrong resource", Fixture: "TestInfrastructureGraphRoleNeverChangesAFactDefinition", Outcomes: outcomes, State: ogState(t, f.hub, "identity-drift-facts")})

	g, gsite := newIGTFixture(t)
	gbefore := g.inspect(t, igtAsset).Canonical
	meter, ok := oprResourceIn(g.inspect(t, igtAsset).Snapshot, igtMeter)
	if !ok {
		t.Fatal("the fixture holds no meter")
	}
	meter.Kind = "resource.grid_connection"
	meter.Revision = "2"
	err := g.publish(t, gsite, func(_ *semhub.Tx, batch *semreg.PublicationBatch) {
		batch.ResourceUpserts = []semreg.Resource{meter}
	})
	answer := ogAnswer("resource republished under another kind", "publish resource:igt:meter-1 as a resource.grid_connection", err)
	answer.Detail = append(answer.Detail, ogUnchanged(gbefore, g.inspect(t, igtAsset).Canonical))
	scenarios = append(scenarios, ogScenario{Case: "one identifier republished as another kind", Fixture: "the infrastructure site publisher", Outcomes: []ogOutcome{answer}, State: ogState(t, g.hub, "identity-drift-kind")})

	h, hsite := newIGTFixture(t)
	hbefore := h.inspect(t, igtAsset).Canonical
	moved, ok := oprResourceIn(h.inspect(t, igtAsset).Snapshot, igtMeter)
	if !ok {
		t.Fatal("the fixture holds no meter")
	}
	other := "meter-2"
	moved.Anchor.Slot = &other
	moved.Revision = "2"
	err = h.publish(t, hsite, func(_ *semhub.Tx, batch *semreg.PublicationBatch) {
		batch.ResourceUpserts = []semreg.Resource{moved}
	})
	movedAnswer := ogAnswer("resource republished under another anchor", "publish resource:igt:meter-1 under the native slot meter-2 instead of meter-1", err)
	movedAnswer.Detail = append(movedAnswer.Detail, ogUnchanged(hbefore, h.inspect(t, igtAsset).Canonical))
	scenarios = append(scenarios, ogScenario{Case: "one identifier republished under another anchor", Fixture: "the infrastructure site publisher", Outcomes: []ogOutcome{movedAnswer}, State: ogState(t, h.hub, "identity-drift-anchor")})

	ogOut(t, "negative-identity-drift.json", ogNegative("identity drift", "The pin refuses a fact whose subject is a resource of another kind than its dimension names and a resource identifier that changes kind; each refusal leaves the asset's snapshot bytes unchanged.", scenarios...))
}

func TestOracleGraphNegativeUnauthorizedControl(t *testing.T) {
	scenarios := []ogScenario{}

	charging := oraChargingPath()
	f := newOraFixture(t, evse.New, []*oraPath{charging}, oraChargingMeterHome)
	f.replace(t, oraDecode(t, oraChargingDocument), "published:", "published:")
	kernel, err := semanticoperations.NewBuiltinKernel()
	if err != nil {
		t.Fatal(err)
	}
	executor := &oraExecutor{}
	lookup := &semoptest.Lookup{}
	lookup.Register(charging.controlRoute(t), oraEVSEDefinition("evse.operation.set_allocated_current"), executor)
	router := semanticoperations.NewRouter(semanticoperations.Config{Snapshots: &hubSemanticSnapshotProvider{hub: f.hub, now: time.Now}, Kernel: kernel, Intents: &oraOwner{}, Executors: lookup})
	result, err := router.Route(context.Background(), oraRequest(t, f, charging))
	if err != nil {
		t.Fatalf("route: %v", err)
	}
	scenarios = append(scenarios, ogScenario{Case: "a configured measures relation grants no control", Fixture: "TestOperatorRecordAcceptanceConfiguredMeasuresGrantsNoControl: the intent before the driver publishes a control capability",
		Outcomes: []ogOutcome{ogRouteOutcome("intent on the measured EVSE", "set the allocated current to 16 A through the router", result, len(executor.received()))}, State: ogState(t, f.hub, "control-measures-relation")})

	g, site := newIGTFixture(t)
	g.replace(t, oraDecode(t, igtDocument), "published:", "published:")
	gexecutor := &oraExecutor{}
	glookup := &semoptest.Lookup{}
	glookup.Register(operation.Route{CapabilityInstance: igtConnectionLimit, ServiceInstance: "service:igt:connection", BindingID: site.binding(t), SourceID: site.source, SourceEpochID: site.handle.Epoch(), DriverGeneration: site.generation()}, igtExportLimit, gexecutor)
	glookup.Register(operation.Route{CapabilityInstance: igtMeterCapability, ServiceInstance: igtMeterService, BindingID: igtMeterBinding(t, site), SourceID: site.source, SourceEpochID: site.handle.Epoch(), DriverGeneration: site.generation()}, igtExportLimit, gexecutor)
	grouter := semanticoperations.NewRouter(semanticoperations.Config{Snapshots: &hubSemanticSnapshotProvider{hub: g.hub, now: time.Now}, Kernel: kernel, Intents: &igtOwner{}, Executors: glookup})
	outcomes := []ogOutcome{}
	for _, item := range []struct {
		name    string
		request semanticoperations.Request
	}{
		{"the grid connection's own capability", igtRequest(t, g, site, site.binding(t), igtConnectionLimit)},
		{"the meter's capability through the role", igtRequest(t, g, site, igtMeterBinding(t, site), igtMeterCapability)},
	} {
		got, err := grouter.Route(context.Background(), item.request)
		if err != nil {
			t.Fatalf("route: %v", err)
		}
		outcomes = append(outcomes, ogRouteOutcome(item.name, "set an export limit on the grid connection through the router", got, len(gexecutor.received())))
	}
	scenarios = append(scenarios, ogScenario{Case: "the infrastructure pack defines no operation", Fixture: "TestInfrastructureGraphPackDefinesNoOperationSoAnIntentOnTheGridConnectionIsRefused", Outcomes: outcomes, State: ogState(t, g.hub, "control-no-operation")})

	ogOut(t, "negative-unauthorized-control.json", ogNegative("unauthorized control", "The pin refuses an intent that no qualified capability of the driver carries and an intent for an operation its pack does not define; the refused intent reaches no executor.", scenarios...))
}

func ogRouteOutcome(label, attempt string, result semanticoperations.Result, executed int) ogOutcome {
	out := ogOutcome{Case: label, Attempt: attempt, Answer: "status " + string(result.Status), Identifier: oraReason(result)}
	delivery := "none"
	if result.Delivery != nil {
		delivery = string(*result.Delivery)
	}
	out.Detail = []string{"delivery " + delivery, "executor dispatches " + strconv.Itoa(executed)}
	return out
}
