package main

import (
	"context"
	"net"
	"testing"
	"time"

	ebusgateway "github.com/Project-Helianthus/helianthus-ebusgateway"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/modbusadapter"
	sunspectest "github.com/Project-Helianthus/helianthus-ebusgateway/internal/modbusadapter/testfixture"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semgraph"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semhub"
	modbus "github.com/Project-Helianthus/helianthus-modbus"
	"github.com/Project-Helianthus/helianthus-modbusreg/huawei"
	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/evse"
)

// Every family is driven by the pin's own publisher from the offline fixtures
// the pin's own tests use; the recorder reads the hub afterwards.

func TestOracleGraphInfrastructure(t *testing.T) {
	f, _ := newIGTFixture(t)
	doc := ogRead(t, f.hub, "infrastructure", "TestInfrastructureGraphPublishesTheMeterRoleAsAConfiguredMeasuresInstance: the site publisher's own batches, before the operator-record section is accepted",
		"The synthetic infrastructure publisher is the only graph-enforced publisher of the infrastructure pack at the pin: a site, its grid connection and one meter, with the gate's four facts.")
	ogOut(t, "infrastructure.json", doc)
}

func TestOracleGraphSite(t *testing.T) {
	f, _ := newIGTFixture(t)
	f.replace(t, oraDecode(t, igtDocument), "published:", "published:")
	doc := ogRead(t, f.hub, "site", "TestInfrastructureGraphPublishesTheMeterRoleAsAConfiguredMeasuresInstance: the operator-record section accepted by the Portal configuration runtime",
		"The site is the configured installation root of the infrastructure asset: the configuration provider publishes the site-contains-grid-connection and the grid-connection-measures-meter instances into the asset that homes their starting ends.")
	ogOut(t, "site.json", doc)
}

func TestOracleGraphPVLogger(t *testing.T) {
	hub := newTestSemanticHub(t)
	huaweiRelationsFixture(t, hub, "smartlogger", "alpha")
	huaweiRelationsFixture(t, hub, "sdongle", "beta")
	doc := ogRead(t, hub, "pv-logger", "TestHuaweiPVRelationsPublishGateInstances: the logger replay of one logger and one dongle on one hub, each child an asset of the logger PV class",
		"Each admitted inverter child is one asset with the gate's system-to-inverter and inverter-to-input instances; each logger is one generic equipment asset.")
	ogOut(t, "pv-logger.json", doc)
}

func TestOracleGraphPVSunSpec(t *testing.T) {
	hub, err := semhub.New(semhub.Options{})
	if err != nil {
		t.Fatal(err)
	}
	class, err := modbusadapter.NewSemanticPVClass(hub, semanticFamilyGraph(semanticFamilyPV))
	if err != nil {
		t.Fatal(err)
	}
	words := sunspectest.ObservedFroniusFloatControlsWords()
	sunspectest.SetFloat(words, 20, 1_234.5)
	sunspectest.SetFloat(words, 22, 50)
	listener, _, err := sunspectest.ServeSunSpecChain(words)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = listener.Close() })
	config, err := mapModbusRuntimeConfig(ebusgateway.ModbusTCPConfig{Enabled: true, Endpoint: "tcp://" + listener.Addr().String(), DialTimeout: time.Second})
	if err != nil {
		t.Fatal(err)
	}
	now := time.Date(2026, 9, 20, 10, 0, 0, 0, time.UTC)
	config.Clock = func() time.Time { return now }
	config.SemanticPV = class
	adapter, err := modbusadapter.Start(context.Background(), config, (&net.Dialer{}).DialContext, func(config modbus.TCPEndpointConfig) (modbusadapter.Endpoint, error) {
		return modbus.NewTCPEndpoint(config)
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = adapter.Close() })
	producer, err := modbusadapter.NewSunSpecProducer(adapter, modbusadapter.SunSpecProducerConfig{UnitID: 1, AuthorizationScope: "test:public-05-readonly", ReadTimeout: time.Second})
	if err != nil {
		t.Fatal(err)
	}
	initial, err := producer.Qualify(context.Background(), modbusadapter.SunSpecPollIdentity{PollGeneration: 501, DeadlineIdentity: 601})
	if err != nil || initial.Outcome != modbusadapter.SunSpecQualificationGO {
		t.Fatalf("initial qualification=%+v err=%v", initial, err)
	}
	now = now.Add(31 * time.Second)
	sunspectest.SetFloat(words, 20, 4_321.5)
	refresh, err := producer.Refresh(context.Background(), modbusadapter.SunSpecPollIdentity{PollGeneration: 502, DeadlineIdentity: 602})
	if err != nil || refresh.Outcome != modbusadapter.SunSpecQualificationGO {
		t.Fatalf("refresh=%+v err=%v", refresh, err)
	}
	doc := ogRead(t, hub, "pv-sunspec", "TestPUBLIC05SunSpecSemRegSurvivesGatewayProvidersAndPortal: one SunSpec inverter served by the pin's virtual server over a loopback socket, qualified and refreshed by the production producer",
		"A single-device SunSpec chain publishes the inverter, its phases and the PV system as the PV class's one graph-enforced asset.")
	ogOut(t, "pv-sunspec.json", doc)
}

func TestOracleGraphStorage(t *testing.T) {
	hub := newTestSemanticHub(t)
	runtime := startGrowattRuntimeWithFakeOn(t, growattProductionConfig(), &growattEndpointFake{words: growattBMSProductionWords(), failAt: -1, mismatch: -1, generation: 1}, hub)
	if _, err := runtime.GrowattStorageSemanticCurrent(context.Background()); err != nil {
		t.Fatal(err)
	}
	doc := ogRead(t, hub, "storage", "TestGrowattStorageGraphPublishesThePackAsAnAllocatedResource: the production storage runtime over the pin's scripted endpoint",
		"The configured battery storage asset publishes one battery pack as an allocated resource; the gate states no relation.")
	ogOut(t, "storage.json", doc)
}

func TestOracleGraphEVSE(t *testing.T) {
	hub := newTestSemanticHub(t)
	config := teslaRetainedConfig()
	owner, err := startTeslaHSCRetainedOwner(config, hub)
	if err != nil {
		t.Fatal(err)
	}
	if err := owner.IngestPersistent(context.Background(), teslaPersistentOutcome(t, 1, 16)); err != nil {
		t.Fatal(err)
	}
	doc := ogRead(t, hub, "evse", "TestTeslaHSCRetainedOwnerSuccessorFirstPublicationIsAcceptedOnTheRetainedKernel: the retained owner's first publication",
		"The EVSE family is switched off in the family table, so its asset is declared not enforced and the cut reports it ungraphed.")
	ogOut(t, "evse.json", doc)
}

func TestOracleGraphThermal(t *testing.T) {
	publisher, _, _ := m15Fixture(t)
	if publisher.scalar(publisher.binding.Identity.Target) == nil {
		t.Fatalf("thermal fixture did not publish: %v", publisher.lastError)
	}
	doc := ogRead(t, publisher.hub, "thermal", "TestM15QualifiedFlowOnly: the boiler publisher's first qualified flow temperature",
		"The thermal family is switched off in the family table: its asset is declared not enforced, holds no resource, and the cut reports it ungraphed.")
	ogOut(t, "thermal.json", doc)
}

func TestOracleGraphPaired(t *testing.T) {
	hub, err := semhub.New(semhub.Options{})
	if err != nil {
		t.Fatal(err)
	}
	if err := composeDeclaredPairings(hub, []semanticPairing{pairingDeclaration()}); err != nil {
		t.Fatal(err)
	}
	allocator, err := semgraph.NewAllocator(semgraph.NewMemoryStore())
	if err != nil {
		t.Fatal(err)
	}
	unit, anchor, err := allocator.Resolve(pairingResourceKind, pairingUnitAnchor(pairingOwnerDriver))
	if err != nil {
		t.Fatal(err)
	}
	resource := semreg.Resource{ResourceID: unit, Kind: pairingResourceKind, Anchor: anchor, State: semreg.ResourceCurrent, Origin: semreg.OriginRef{OriginID: "origin:pairtest:operator", Kind: semreg.OriginOperator, Evidence: []semreg.EvidenceRef{pairingEvidence("pairtest.operator", "pairing")}}, Revision: "1"}
	owner, err := hub.AdmitSource(semhub.Admission{Source: pairingOwnerSource, Driver: pairingOwnerDriver})
	if err != nil {
		t.Fatal(err)
	}
	peer, err := hub.AdmitSource(semhub.Admission{Source: pairingPeerSource, Driver: pairingPeerDriver})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := pairingPublish(t, hub, owner, pairingOwnerDriver, 1, 1500, unit, resource); err != nil {
		t.Fatal(err)
	}
	if _, err := pairingPublish(t, hub, peer, pairingPeerDriver, 2, 1490, unit); err != nil {
		t.Fatal(err)
	}
	doc := ogRead(t, hub, "paired", "TestSemanticMultiSourceAcceptanceOneUnitThroughTwoPaths: one unit observed by an owner family and a contributor family through the declared pairing",
		"The declared pair is one graph-enforced asset with one resource, one binding and one identity link per path, and one fact key with two candidates.")
	ogOut(t, "paired.json", doc)
}

func TestOracleGraphPVRelations(t *testing.T) {
	hub := newTestSemanticHub(t)
	publication, cycle, unit := huaweiRelationsFixture(t, hub, "smartlogger", "alpha")
	withheld := huaweiRelationsNext(cycle, func(child *huawei.ProviderChildObservation) {
		if child.UnitID == unit {
			child.Evidence = huawei.ProviderEvidenceWithheld
			child.Reason = huawei.ProviderReasonChildTimeout
		}
	})
	if err := publication.Publish(withheld); err != nil {
		t.Fatal(err)
	}
	doc := ogRead(t, hub, "pv-relations", "TestHuaweiPVRelationsWithheldChildLeavesStructuralRecord: the logger replay with one child withheld by the native owner",
		"The logger PV class states the gate's system-to-inverter and inverter-to-input instances for each published child; the withheld child keeps its resources as withdrawn records and states no relation; the logger states no relays instance while the registry cannot name the definition.")
	doc.Declared = ogDeclaredRelations(t, "pv")
	doc.Evidence = []string{"relays instances withheld: " + publication.relaysWithheld()}
	ogOut(t, "pv-relations.json", doc)
}

func TestOracleGraphStorageRelations(t *testing.T) {
	hub := newTestSemanticHub(t)
	runtime := startGrowattRuntimeWithFakeOn(t, growattProductionConfig(), &growattEndpointFake{words: growattBMSProductionWords(), failAt: -1, mismatch: -1, generation: 1}, hub)
	if _, err := runtime.GrowattStorageSemanticCurrent(context.Background()); err != nil {
		t.Fatal(err)
	}
	doc := ogRead(t, hub, "storage-relations", "TestGrowattStorageGraphPublishesThePackAsAnAllocatedResource: the production storage runtime",
		"The storage gate states no relation instance and no absence statement: the pack declares its relation definitions and the pin publishes none.")
	doc.Declared = ogDeclaredRelations(t, "storage")
	ogOut(t, "storage-relations.json", doc)
}

func TestOracleGraphEVSERelations(t *testing.T) {
	charging := oraChargingPath()
	f := newOraFixture(t, evse.New, []*oraPath{charging}, oraChargingMeterHome)
	f.replace(t, oraDecode(t, oraChargingDocument), "published:", "published:")
	doc := ogRead(t, f.hub, "evse-relations", "TestOperatorRecordAcceptanceConfiguredMeasuresGrantsNoControl: a synthetic charging driver declared with graph enforcement and the operator-record section accepted",
		"The production EVSE asset is declared without enforcement and holds no relation (see evse); the pin's relation path for the EVSE pack is the operator record: a configured meter measures the charging driver's EVSE, a qualified coherent instance held by the driver's asset.")
	doc.Declared = ogDeclaredRelations(t, "evse")
	ogOut(t, "evse-relations.json", doc)
}

func TestOracleGraphEmptyFamilies(t *testing.T) {
	for _, item := range []struct {
		name, statement string
		files           []string
	}{
		{"meter", "The pin has no meter publisher: no declaration, no resource, no fact.", nil},
		{"eebus-inbound", "The pin reads eeBUS inbound values into the promotion capture and the registry; it publishes nothing on the semantic hub.", []string{"eebus_inbound_values.go", "eebus_promoted_semantic.go"}},
		{"can-storage", "The pin's low-voltage battery CAN runtime publishes nothing on the semantic hub.", []string{"growatt_bms_can_runtime.go"}},
		{"vrf", "The pin has no VRF family: no file, no declaration, no resource.", nil},
		{"gateway-topology", "The pin publishes no gateway topology resource on the semantic hub.", nil},
	} {
		evidence := []string{}
		for _, file := range item.files {
			evidence = append(evidence, ogSourceDoesNotUse(t, file))
		}
		doc := ogEmpty(t, item.name, "cmd/gateway/semantic_family_graph.go", evidence, item.statement)
		ogOut(t, item.name+".json", doc)
	}
}
