package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"
	"unsafe"

	ebusgateway "github.com/Project-Helianthus/helianthus-ebusgateway"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/portalconfig"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semanticoperations/semoptest"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semgraph"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semhub"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semselect"
	"github.com/Project-Helianthus/helianthus-ebusgateway/portal"
	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/infrastructure"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/thermal"
)

// The restart recorder is harness-only. It drives the pin's own composition
// twice over one allocator store directory: the pin's pairing declaration of
// two sources on one thermal asset, the pin's resource allocator on a file
// store, the pin's operator-link seam and the pin's operator-record
// configuration provider that homes a site. It reads each lifecycle through
// the hub's own cut, inspection and presentation. Nothing the run allocates
// (source epoch, binding, batch, snapshot or cut identifier) and no clock,
// lease or digest of a capture is written, so two recordings are the same
// bytes.

const (
	rsFormat = "helianthus-oracle-restart/1"

	rsHome       semreg.AssetID    = "asset:qv02:configuration-home"
	rsSite       semreg.ResourceID = "resource:qv02:site-1"
	rsConnection semreg.ResourceID = "resource:qv02:connection-1"

	rsAsset       semreg.AssetID  = "asset:qv02:thermal-pair"
	rsOwnerSource semreg.SourceID = "source:qv02:thermal-owner"
	rsPeerSource  semreg.SourceID = "source:qv02:thermal-peer"
	rsOwnerDriver                 = "qv02_thermal_owner"
	rsPeerDriver                  = "qv02_thermal_peer"
	rsUnitKind                    = semreg.DefinitionID("resource.heat_generator")
	rsUnitSlot                    = "generator-1"
	rsFactID                      = semreg.DefinitionID("thermal.measurement.heat_generator_flow_temperature")
	rsDimension                   = semreg.DefinitionID("thermal.dimension.heat_generator")
	rsStateFile                   = "runtime_state.json"
)

// rsDocument is the operator-record section of the configuration home: the
// site, its grid connection and the site-contains-connection relation.
const rsDocument = `{
  "format": "helianthus.portal-config.operator-records/v1",
  "revision": "0",
  "records": [
    {"form": "anchor", "home": "asset:qv02:configuration-home", "resource_id": "resource:qv02:site-1", "kind": "resource.site", "slot": "site-1"},
    {"form": "anchor", "home": "asset:qv02:configuration-home", "resource_id": "resource:qv02:connection-1", "kind": "resource.grid_connection", "slot": "connection-1"},
    {"form": "relation", "home": "asset:qv02:configuration-home",
     "definition": {"pack": {"id": "helianthus.pack.infrastructure", "version": "1.0.0"}, "id": "infrastructure.relation.site_grid_connection", "version": "1.0.0"},
     "from": "resource:qv02:site-1", "to": "resource:qv02:connection-1", "basis_class": "configuration"}
  ]
}`

var rsThermalPack = thermal.New().Pack()

func rsHash(parts ...string) string {
	sum := sha256.Sum256([]byte("qv02restart\x00" + strings.Join(parts, "\x00")))
	return hex.EncodeToString(sum[:])
}

func rsEvidence(owner semreg.DefinitionID, kind semreg.DefinitionID, label string) semreg.EvidenceRef {
	return semreg.EvidenceRef{Owner: owner, Kind: kind, Digest: semreg.Digest("sha256:" + rsHash("evidence", string(owner), string(kind), label)), Contract: semreg.ContractKernelV1, Access: semreg.EvidenceAccessAuthorized, Redaction: semreg.RedactionMetadataOnly}
}

func rsPackEvidence(kind semreg.DefinitionID, label string) semreg.EvidenceRef {
	return rsEvidence(semreg.DefinitionID(rsThermalPack.ID), kind, label)
}

func rsEvidenceText(ref semreg.EvidenceRef) string {
	return string(ref.Owner) + "/" + string(ref.Kind) + "/" + string(ref.Digest)
}

func rsKelvin(centi int64) semreg.Value {
	return semreg.Value{Kind: semreg.ValueQuantity, Quantity: &semreg.Quantity{Number: semreg.Decimal{Coefficient: strconv.FormatInt(centi, 10), Exponent10: -2}, Unit: "unit.kelvin"}}
}

func rsUnitAnchor(path string) semgraph.Anchor {
	return semgraph.Anchor{Class: semreg.AnchorEquipment, Basis: semreg.AnchorOperatorSlot, Source: semgraph.SourceOperatorLabel, Slot: rsUnitSlot, Evidence: []semreg.EvidenceRef{rsPackEvidence("qv02.anchor", path)}}
}

func rsPairing() semanticPairing {
	budget := semanticCapacityBudget{SourceDescriptors: 16, Bindings: 64, IdentityLinks: 64}
	return semanticPairing{
		Owner:       semhub.AssetSpec{AssetID: rsAsset, SourceID: rsOwnerSource, Driver: rsOwnerDriver, Validators: []semreg.PackValidator{thermal.New()}, Graph: true},
		OwnerBudget: budget,
		Contributors: []semanticPairingContributor{{
			Source: rsPeerSource, Driver: rsPeerDriver, Validators: []semreg.PackValidator{thermal.New()}, Budget: budget,
		}},
	}
}

// rsPath is one publishing source of the paired asset.
type rsPath struct {
	source semreg.SourceID
	driver string
	family string
	centi  int64
	handle *semhub.Handle
}

type rsRun struct {
	t          *testing.T
	hub        *semhub.Hub
	records    *portal.ConfigOperatorRecords
	allocator  *semanticResourceAllocator
	unit       semreg.ResourceID
	anchorKey  semgraph.AnchorKey
	heldAtOpen bool
	owner      *rsPath
	peer       *rsPath
	ticks      int64
}

func (r *rsRun) now() (semreg.TimePoint, semreg.MonotonicPoint) {
	r.ticks++
	return semoptest.TimePoint(time.Now()), semreg.MonotonicPoint{ClockEpochID: "clock:qv02", Nanoseconds: semreg.Uint64(strconv.FormatInt(r.ticks*1_000_000, 10))}
}

func (p *rsPath) generation() semreg.Uint64 {
	return semreg.Uint64(strconv.FormatUint(p.handle.Generation(), 10))
}

func (p *rsPath) binding(t *testing.T) semreg.NativeBindingID {
	t.Helper()
	binding, err := semhub.NativeBindingID(p.family, rsAsset, p.source, "qv02.profile.v1", p.handle.Epoch(), p.handle.Generation())
	if err != nil {
		t.Fatal(err)
	}
	return binding
}

func (p *rsPath) native() semreg.EvidenceRef {
	return rsPackEvidence("qv02.native", p.family)
}

// publish runs one transaction of the path on the paired asset.
func (r *rsRun) publish(p *rsPath, edit func(*semhub.Tx, *semreg.PublicationBatch)) {
	t := r.t
	t.Helper()
	tx, err := r.hub.Begin(p.handle, rsAsset)
	if err != nil {
		t.Fatalf("%s begin: %v", p.family, err)
	}
	defer tx.Abort()
	inc := tx.Incarnation()
	current, exists := tx.Current()
	expected := semreg.Uint64("0")
	if exists {
		expected = current.Revisions.Semantic
	}
	wall, mono := r.now()
	generation, sequence, epoch, source := p.generation(), tx.NextSequence(), inc.Epoch, inc.Source
	batch := semreg.PublicationBatch{Contract: semreg.ContractKernelV1, BatchID: semreg.BatchID("batch:qv02:" + rsHash("batch", string(inc.Asset), string(source), string(epoch), string(generation), string(sequence))[:32]), AssetID: inc.Asset,
		SourceID: source, SourceEpochID: epoch, DriverGeneration: generation, Sequence: sequence, ExpectedSemanticRevision: expected, ObservedAt: wall,
		SourceUpserts: []semreg.SourceDescriptor{}, SourceRetirements: tx.SourceRetirements(), BindingUpserts: []semreg.NativeBinding{}, IdentityLinkUpserts: []semreg.IdentityLink{},
		ResourceUpserts: []semreg.Resource{}, FactUpserts: []semreg.FactCandidate{}, FactWithdrawals: []semreg.CandidateID{}, ServiceUpserts: []semreg.ServiceInstance{}, ServiceWithdrawals: []semreg.ServiceInstanceID{},
		CapabilityUpserts: []semreg.CapabilityInstance{}, CapabilityWithdrawals: []semreg.CapabilityInstanceID{}, GenerationFences: []semreg.GenerationFence{}}
	edit(tx, &batch)
	if batch.BatchDigest, err = batch.ComputedDigest(); err != nil {
		t.Fatal(err)
	}
	if err := batch.Validate(); err != nil {
		t.Fatalf("%s batch is not a valid record: %v", p.family, err)
	}
	if _, _, err := tx.Apply(batch, mono); err != nil {
		t.Fatalf("%s apply: %v", p.family, err)
	}
	outcome, err := tx.Commit(nil)
	if err != nil || outcome != semhub.Accepted {
		t.Fatalf("%s commit outcome=%v err=%v", p.family, outcome, err)
	}
}

// first adds the source, its binding and the identity link of a path's first
// batch; resource is the unit the link names, or nil for a link that names
// none.
func (r *rsRun) first(p *rsPath, batch *semreg.PublicationBatch, resource *semreg.ResourceID) {
	binding := p.binding(r.t)
	wall, _ := r.now()
	batch.SourceUpserts = []semreg.SourceDescriptor{{SourceID: p.source, SourceEpochID: batch.SourceEpochID, ProtocolID: "qv02_protocol", ProfileID: "qv02.profile.v1", ProfileVersion: "1", RegistryEvidence: rsPackEvidence("qv02.registry", p.family), StartedAt: wall, State: semreg.SourceCurrent, Revision: "1"}}
	batch.BindingUpserts = []semreg.NativeBinding{{BindingID: binding, AssetID: rsAsset, SourceID: p.source, SourceEpochID: batch.SourceEpochID, DriverGeneration: p.generation(), NativeResource: p.native(), State: semreg.BindingCurrent, Revision: "1"}}
	link := semreg.IdentityLink{AssetID: rsAsset, BindingID: binding, State: semreg.LinkQualified, Basis: []semreg.EvidenceRef{rsPackEvidence("qv02.observation", p.family)}, Revision: "1"}
	if resource != nil {
		named := *resource
		link.Resource = &named
	}
	batch.IdentityLinkUpserts = []semreg.IdentityLink{link}
}

// candidate is the path's flow-temperature candidate about the unit.
func (r *rsRun) candidate(p *rsPath, tx *semhub.Tx) semreg.FactCandidate {
	subject := string(r.unit)
	inc := tx.Incarnation()
	binding := p.binding(r.t)
	epoch, source, generation := inc.Epoch, inc.Source, p.generation()
	wall, mono := r.now()
	evidence := rsPackEvidence("qv02.measurement", p.family)
	id := semreg.CandidateID("candidate:qv02:" + rsHash("candidate", p.family, subject)[:32])
	revision := semreg.Uint64("1")
	if current, exists := tx.Current(); exists {
		for _, envelope := range current.Facts {
			for _, held := range envelope.Candidates {
				if held.CandidateID == id {
					next, _ := strconv.ParseUint(string(held.Revision), 10, 64)
					revision = semreg.Uint64(strconv.FormatUint(next+1, 10))
				}
			}
		}
	}
	value := rsKelvin(p.centi)
	return semreg.FactCandidate{CandidateID: id,
		Key:             semreg.FactKey{PackID: rsThermalPack.ID, PackVersion: rsThermalPack.Version, FactID: rsFactID, Dimensions: []semreg.Dimension{{ID: rsDimension, Value: semreg.Value{Kind: semreg.ValueText, Text: &subject}}}},
		Value:           &value,
		Quality:         semreg.Quality{Assertion: semreg.AssertionObserved, Qualification: semreg.QualificationQualified, Promotion: semreg.PromotionPromoted, Validity: semreg.ValidityGood, Availability: semreg.AvailabilityAvailable, Freshness: semreg.FreshnessFresh, Reasons: []semreg.DefinitionID{}},
		Times:           semreg.Times{ReceivedAt: wall, ReceiptMonotonic: mono, EvaluatedAt: wall, EvaluateMonotonic: mono},
		FreshnessPolicy: semreg.FreshnessPolicy{PolicyID: "policy:qv02", Version: "1.0.0", FreshForNS: "3600000000000", RetainForNS: "7200000000000", MaxWallUncertaintyNS: "0"},
		BindingID:       &binding, SourceEpochID: &epoch, DriverGeneration: &generation,
		Origin:   semreg.OriginRef{OriginID: semreg.OriginID("origin:qv02:" + rsHash("origin", string(id))[:32]), Kind: semreg.OriginNativeObservation, SourceID: &source, SourceEpochID: &epoch, BindingID: &binding, Evidence: []semreg.EvidenceRef{evidence}},
		Evidence: []semreg.EvidenceRef{evidence}, Revision: revision}
}

// rsStart composes one process over the allocator store directory dir.
func rsStart(t *testing.T, dir string) *rsRun {
	t.Helper()
	hub, err := semhub.New(semhub.Options{})
	if err != nil {
		t.Fatal(err)
	}
	declaring, err := newOperatorRecordPublisher(hub, operatorRecordOptions{})
	if err != nil {
		t.Fatal(err)
	}
	if err := declaring.DeclareHome(rsHome, infrastructure.New()); err != nil {
		t.Fatalf("declare the configuration home: %v", err)
	}
	runtime := opr27Runtime(t)
	records := runtime.callbacks(ebusgateway.Config{}, &gatewayRuntimeControl{hub: hub}).OperatorRecords
	allocator, err := composeSemanticResourceAllocator(hub, filepath.Join(dir, rsStateFile))
	if err != nil {
		t.Fatalf("compose the allocator: %v", err)
	}
	if err := composeDeclaredPairings(hub, []semanticPairing{rsPairing()}); err != nil {
		t.Fatalf("declare the pairing: %v", err)
	}
	return &rsRun{t: t, hub: hub, records: records, allocator: allocator,
		owner: &rsPath{source: rsOwnerSource, driver: rsOwnerDriver, family: "qv02_owner", centi: 32315},
		peer:  &rsPath{source: rsPeerSource, driver: rsPeerDriver, family: "qv02_peer", centi: 32265}}
}

func (r *rsRun) awaitAdmitted() {
	deadline := time.Now().Add(5 * time.Second)
	for !r.hub.Admitted(rsAsset) {
		if time.Now().After(deadline) {
			r.t.Fatal("the paired asset did not settle")
		}
		time.Sleep(time.Millisecond)
	}
}

// publishAll is the sequence both lifecycles run: both paths resolve the unit
// under one operator slot, the owner publishes the unit and its candidate, the
// contributor publishes its binding with an identity link that names no
// resource, the operator declares the contributor's link, the contributor
// publishes again with the link and its candidate, and the configuration
// provider accepts the site section.
func (r *rsRun) publishAll() {
	t := r.t
	ownerAnchor, peerAnchor := rsUnitAnchor(rsOwnerDriver), rsUnitAnchor(rsPeerDriver)
	key, err := ownerAnchor.Key(rsUnitKind)
	if err != nil {
		t.Fatal(err)
	}
	r.anchorKey = key
	_, held, err := r.allocator.store.Lookup(key)
	if err != nil {
		t.Fatal(err)
	}
	r.heldAtOpen = held
	unit, anchor, err := r.allocator.resolve(rsUnitKind, ownerAnchor, rsAsset)
	if err != nil {
		t.Fatalf("resolve the unit through the owner's path: %v", err)
	}
	peerUnit, _, err := r.allocator.resolve(rsUnitKind, peerAnchor, rsAsset)
	if err != nil || peerUnit != unit {
		t.Fatalf("the contributor's path resolved %q (%v), want %q", peerUnit, err, unit)
	}
	r.unit = unit
	resource := semreg.Resource{ResourceID: unit, Kind: rsUnitKind, Anchor: anchor, State: semreg.ResourceCurrent,
		Origin:   semreg.OriginRef{OriginID: "origin:qv02:operator", Kind: semreg.OriginOperator, Evidence: []semreg.EvidenceRef{rsPackEvidence("qv02.operator", "unit")}},
		Revision: "1"}

	var err2 error
	if r.owner.handle, err2 = r.hub.AdmitSource(semhub.Admission{Source: rsOwnerSource, Driver: rsOwnerDriver}); err2 != nil {
		t.Fatal(err2)
	}
	if r.peer.handle, err2 = r.hub.AdmitSource(semhub.Admission{Source: rsPeerSource, Driver: rsPeerDriver}); err2 != nil {
		t.Fatal(err2)
	}
	r.publish(r.owner, func(tx *semhub.Tx, batch *semreg.PublicationBatch) {
		r.first(r.owner, batch, &unit)
		batch.ResourceUpserts = []semreg.Resource{resource}
		batch.FactUpserts = []semreg.FactCandidate{r.candidate(r.owner, tx)}
	})
	r.publish(r.peer, func(_ *semhub.Tx, batch *semreg.PublicationBatch) {
		r.first(r.peer, batch, nil)
	})
	declaration := rsEvidence(semhub.OperatorEvidenceOwner, "qv02.operator.declaration", "peer-link")
	if err := r.hub.SetOperatorLinks(rsAsset, rsPeerSource, []semhub.OperatorLink{{Native: r.peer.native(), Resource: unit, Basis: []semreg.EvidenceRef{declaration}}}); err != nil {
		t.Fatalf("declare the operator link: %v", err)
	}
	r.publish(r.peer, func(tx *semhub.Tx, batch *semreg.PublicationBatch) {
		batch.IdentityLinkUpserts = tx.OperatorLinks(nil)
		if len(batch.IdentityLinkUpserts) != 1 {
			t.Fatalf("operator links of the contributor's second batch=%+v, want the declared one", batch.IdentityLinkUpserts)
		}
		batch.FactUpserts = []semreg.FactCandidate{r.candidate(r.peer, tx)}
	})
	set, err := portalconfig.DecodeOperatorRecords([]byte(rsDocument))
	if err != nil {
		t.Fatal(err)
	}
	if err := portalconfig.ValidateOperatorRecords(set); err != nil {
		t.Fatal(err)
	}
	saved, err := r.records.Replace(context.Background(), set)
	if err != nil {
		t.Fatalf("replace the operator-record section: %v", err)
	}
	opr27Await(t, r.records, saved, []string{"published:", "published:", "published:"})
	r.awaitAdmitted()
}

// stop retires the source epoch of each path, as a stopped driver does.
func (r *rsRun) stop() {
	for _, p := range []*rsPath{r.owner, r.peer} {
		wall, mono := r.now()
		if _, err := r.hub.RetireEpoch(semhub.RetireRequest{Source: p.source, Epoch: p.handle.Epoch(), Reason: "lifecycle.source_stopped",
			Evidence: []semreg.EvidenceRef{rsPackEvidence("qv02.stop", p.family)}, ObservedAt: wall, Monotonic: mono}); err != nil {
			r.t.Fatalf("stop %s: %v", p.source, err)
		}
		if info, ok := r.hub.Source(p.source); !ok || info.Live {
			r.t.Fatalf("source %s still live after it stopped: %+v", p.source, info)
		}
	}
}

// The document of one lifecycle.

type rsNode struct {
	Resource semreg.ResourceID `json:"resource"`
	Asset    semreg.AssetID    `json:"asset"`
	Kind     string            `json:"kind"`
	State    string            `json:"state"`
	Anchor   string            `json:"anchor"`
	Origin   string            `json:"origin"`
}

type rsLinkKey struct {
	Definition string            `json:"definition"`
	From       semreg.ResourceID `json:"from"`
	To         semreg.ResourceID `json:"to"`
	Type       string            `json:"type"`
	Asset      semreg.AssetID    `json:"asset"`
	State      string            `json:"state"`
	Coherence  string            `json:"coherence"`
}

type rsAlias struct {
	Resource   semreg.ResourceID `json:"resource"`
	KeyKind    string            `json:"key_kind"`
	KeyDigest  string            `json:"key_digest"`
	KeyParent  string            `json:"key_parent"`
	KeySlot    string            `json:"key_slot"`
	Class      string            `json:"class"`
	Basis      string            `json:"basis"`
	Slot       string            `json:"slot"`
	Superseded bool              `json:"superseded"`
	Home       semreg.AssetID    `json:"home"`
}

type rsSourceLink struct {
	Asset    semreg.AssetID  `json:"asset"`
	Source   semreg.SourceID `json:"source"`
	Native   string          `json:"native"`
	Resource string          `json:"resource"`
	State    string          `json:"state"`
	Revision string          `json:"revision"`
	Operator bool            `json:"operator_declaration"`
	Basis    []string        `json:"basis"`
}

type rsValueKey struct {
	Asset      semreg.AssetID `json:"asset"`
	Fact       string         `json:"fact"`
	Dimensions []string       `json:"dimensions"`
	Candidates int            `json:"candidates"`
}

type rsCompared struct {
	NodeIDs           []semreg.ResourceID `json:"node_ids"`
	Nodes             []rsNode            `json:"nodes"`
	LinkKeys          []rsLinkKey         `json:"link_keys"`
	Aliases           []rsAlias           `json:"aliases"`
	SourceLinks       []rsSourceLink      `json:"source_links"`
	ConsumerValueKeys []rsValueKey        `json:"consumer_value_keys"`
}

type rsSourceValue struct {
	Fact       string          `json:"fact"`
	Dimensions []string        `json:"dimensions"`
	Source     semreg.SourceID `json:"source"`
	Role       string          `json:"role"`
	Value      string          `json:"value"`
	Quality    string          `json:"quality"`
	Presented  bool            `json:"presented"`
}

type rsPresentation struct {
	Policy         string          `json:"policy"`
	PolicyVersion  string          `json:"policy_version"`
	Owner          semreg.SourceID `json:"owner"`
	Fact           string          `json:"fact"`
	Dimensions     []string        `json:"dimensions"`
	SelectedSource semreg.SourceID `json:"selected_source"`
	SelectedValue  string          `json:"selected_value"`
}

type rsCutInfo struct {
	Completeness string   `json:"completeness"`
	Members      []string `json:"members"`
	Excluded     []string `json:"excluded"`
	Findings     []string `json:"findings"`
}

type rsExportCall struct {
	Call               string `json:"call"`
	Recovery           string `json:"recovery_hooks"`
	Version            int    `json:"version"`
	Assets             int    `json:"assets"`
	Epochs             int    `json:"epochs"`
	Regimes            int    `json:"regimes"`
	Unfixed            int    `json:"unfixed"`
	Drivers            int    `json:"drivers"`
	Error              string `json:"error"`
	IsErrRestore       bool   `json:"error_is_ErrRestore"`
	IsRecoveryMultiSrc bool   `json:"error_is_ErrRecoveryMultiSource"`
}

type rsLifecycleInfo struct {
	Name            string `json:"name"`
	AllocatorStore  string `json:"allocator_store"`
	UnitAnchorHeld  bool   `json:"unit_anchor_held_when_the_lifecycle_opened"`
	StoppedAfterCut bool   `json:"stopped_after_the_cut"`
}

type rsDocumentOut struct {
	Format       string           `json:"format"`
	Kind         string           `json:"kind"`
	Case         string           `json:"case"`
	Lifecycle    rsLifecycleInfo  `json:"lifecycle"`
	Source       string           `json:"source"`
	Fixture      string           `json:"fixture"`
	Statement    string           `json:"statement"`
	Compared     rsCompared       `json:"compared"`
	LateLink     []rsSourceLink   `json:"late_link"`
	SourceValues []rsSourceValue  `json:"source_values"`
	Presentation []rsPresentation `json:"presentation"`
	Cut          rsCutInfo        `json:"cut"`
	Export       []rsExportCall   `json:"recovery_export"`
	NotCompared  []string         `json:"not_compared"`
	NotRecorded  []string         `json:"not_recorded"`
}

func rsDimensions(key semreg.FactKey) []string {
	out := []string{}
	for _, dimension := range key.Dimensions {
		text := ""
		if dimension.Value.Text != nil {
			text = *dimension.Value.Text
		} else {
			encoded, _ := json.Marshal(dimension.Value)
			text = string(encoded)
		}
		out = append(out, string(dimension.ID)+"="+text)
	}
	return out
}

func rsAnchorText(anchor semreg.ResourceAnchor) string {
	text := string(anchor.Class) + "/" + string(anchor.Basis)
	if anchor.Slot != nil {
		text += "/slot:" + *anchor.Slot
	}
	if anchor.Parent != nil {
		text += "/parent:" + string(*anchor.Parent)
	}
	return text
}

func rsValueText(value *semreg.Value) string {
	if value == nil {
		return ""
	}
	if value.Quantity != nil {
		return value.Quantity.Number.Coefficient + "e" + strconv.Itoa(int(value.Quantity.Number.Exponent10)) + " " + string(value.Quantity.Unit)
	}
	encoded, _ := json.Marshal(value)
	return string(encoded)
}

func rsQualityText(q semreg.Quality) string {
	return strings.Join([]string{string(q.Assertion), string(q.Qualification), string(q.Promotion), string(q.Validity), string(q.Availability), string(q.Freshness)}, "/")
}

func rsOperatorBasis(basis []semreg.EvidenceRef) bool {
	for _, ref := range basis {
		if ref.Owner == semhub.OperatorEvidenceOwner {
			return true
		}
	}
	return false
}

// read describes the lifecycle through the hub's own cut, inspection and
// presentation.
func (r *rsRun) read(name string, stopped bool) rsDocumentOut {
	t := r.t
	t.Helper()
	captured, err := r.hub.CaptureCut(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	cut := captured.Cut
	if len(captured.NotIncluded) != 0 {
		t.Fatalf("the cut left out %+v", captured.NotIncluded)
	}
	doc := rsDocumentOut{Format: rsFormat, Kind: "cut", Case: "restart-paired-thermal",
		Source:      "cmd/gateway/semantic_pairing_composition.go, cmd/gateway/semantic_resource_allocator.go, internal/semgraph/store_file.go, internal/semhub/operator_links.go, internal/semhub/restore.go and cmd/gateway/operator_record_publisher.go",
		Fixture:     "a synthetic paired thermal asset with an owner and a contributor source, the configuration home with its site and grid connection, and an operator identity link declared after the first batch, on one allocator store directory",
		Statement:   "The paired asset is declared through the pin's pairing composition with graph enforcement; the pin's family table keeps the thermal family itself off. The unit is resolved by the allocator on a file store under one operator slot through both sources' paths. The owner's identity link names the unit in its first batch; the contributor's first batch has a link that names none, the operator declares the link afterwards, and the contributor's next batch carries it. The pin holds no numeric priority per source: the priority of a source is the owner-first presentation policy, recorded per fact key.",
		Lifecycle:   rsLifecycleInfo{Name: name, AllocatorStore: "file store of the state file's directory, one directory for both lifecycles", UnitAnchorHeld: r.heldAtOpen, StoppedAfterCut: stopped},
		NotCompared: []string{"lifecycle", "late_link", "source_values", "presentation", "cut", "recovery_export", "not_compared", "not_recorded"},
		NotRecorded: []string{"clocks", "leases", "cut digests", "source epochs, bindings, batches and snapshot identifiers: a run allocates them, so a recording that held them would differ from the next"}}

	byBinding := map[semreg.NativeBindingID]semreg.NativeBinding{}
	snapshots := []semreg.Snapshot{}
	for _, member := range cut.Members() {
		doc.Cut.Members = append(doc.Cut.Members, string(member.AssetID))
		view, err := r.hub.Inspect(member.AssetID)
		if err != nil || !view.Present {
			t.Fatalf("inspect %s: present=%v err=%v", member.AssetID, view.Present, err)
		}
		snapshots = append(snapshots, view.Snapshot)
	}
	if doc.Cut.Members == nil {
		doc.Cut.Members = []string{}
	}
	doc.Cut.Completeness = string(cut.Completeness())
	doc.Cut.Excluded = []string{}
	for _, excluded := range cut.Excluded() {
		doc.Cut.Excluded = append(doc.Cut.Excluded, string(excluded))
	}
	doc.Cut.Findings = []string{}
	for _, finding := range cut.Findings() {
		doc.Cut.Findings = append(doc.Cut.Findings, string(finding.Kind))
	}
	doc.Compared = rsCompared{NodeIDs: []semreg.ResourceID{}, Nodes: []rsNode{}, LinkKeys: []rsLinkKey{}, Aliases: []rsAlias{}, SourceLinks: []rsSourceLink{}, ConsumerValueKeys: []rsValueKey{}}
	doc.LateLink, doc.SourceValues, doc.Presentation = []rsSourceLink{}, []rsSourceValue{}, []rsPresentation{}
	for _, snapshot := range snapshots {
		for _, binding := range snapshot.Bindings {
			byBinding[binding.BindingID] = binding
		}
	}
	for _, snapshot := range snapshots {
		for _, resource := range snapshot.Resources {
			doc.Compared.NodeIDs = append(doc.Compared.NodeIDs, resource.ResourceID)
			doc.Compared.Nodes = append(doc.Compared.Nodes, rsNode{Resource: resource.ResourceID, Asset: snapshot.AssetID, Kind: string(resource.Kind), State: string(resource.State), Anchor: rsAnchorText(resource.Anchor), Origin: string(resource.Origin.Kind)})
		}
		for _, link := range snapshot.IdentityLinks {
			binding := byBinding[link.BindingID]
			row := rsSourceLink{Asset: snapshot.AssetID, Source: binding.SourceID, Native: rsEvidenceText(binding.NativeResource), Resource: "", State: string(link.State), Revision: string(link.Revision), Operator: rsOperatorBasis(link.Basis), Basis: []string{}}
			if link.Resource != nil {
				row.Resource = string(*link.Resource)
			}
			for _, ref := range link.Basis {
				row.Basis = append(row.Basis, rsEvidenceText(ref))
			}
			doc.Compared.SourceLinks = append(doc.Compared.SourceLinks, row)
			if row.Operator {
				doc.LateLink = append(doc.LateLink, row)
			}
		}
		for _, envelope := range snapshot.Facts {
			doc.Compared.ConsumerValueKeys = append(doc.Compared.ConsumerValueKeys, rsValueKey{Asset: snapshot.AssetID, Fact: string(envelope.Key.FactID), Dimensions: rsDimensions(envelope.Key), Candidates: len(envelope.Candidates)})
		}
	}
	for _, relation := range cut.Relations() {
		held := ""
		for _, snapshot := range snapshots {
			if snapshot.AssetID != relation.AssetID {
				continue
			}
			for _, instance := range snapshot.Relations {
				if instance.Definition == relation.Definition && instance.From == relation.From && instance.To == relation.To {
					held = string(instance.BasisClass)
				}
			}
		}
		doc.Compared.LinkKeys = append(doc.Compared.LinkKeys, rsLinkKey{Definition: string(relation.Definition.ID), From: relation.From, To: relation.To, Type: held, Asset: relation.AssetID, State: string(relation.State), Coherence: string(relation.Coherence)})
	}
	for _, node := range doc.Compared.Nodes {
		entry, held, err := r.allocator.store.Lookup(r.anchorKey)
		if err != nil {
			t.Fatal(err)
		}
		if node.Resource != r.unit || !held || entry.Resource != node.Resource {
			continue
		}
		home, err := r.allocator.allocator.Home(node.Resource, node.Asset)
		if err != nil {
			t.Fatal(err)
		}
		doc.Compared.Aliases = append(doc.Compared.Aliases, rsAlias{Resource: node.Resource, KeyKind: string(r.anchorKey.Kind), KeyDigest: string(r.anchorKey.Key), KeyParent: string(r.anchorKey.Parent), KeySlot: r.anchorKey.Slot, Class: string(entry.Class), Basis: string(entry.Basis), Slot: entry.Slot, Superseded: entry.Superseded, Home: home})
	}
	sort.Slice(doc.Compared.NodeIDs, func(i, j int) bool { return doc.Compared.NodeIDs[i] < doc.Compared.NodeIDs[j] })
	sort.Slice(doc.Compared.Nodes, func(i, j int) bool { return doc.Compared.Nodes[i].Resource < doc.Compared.Nodes[j].Resource })
	sort.Slice(doc.Compared.LinkKeys, func(i, j int) bool {
		a, b := doc.Compared.LinkKeys[i], doc.Compared.LinkKeys[j]
		return a.Definition+"\x00"+string(a.From)+"\x00"+string(a.To) < b.Definition+"\x00"+string(b.From)+"\x00"+string(b.To)
	})
	sort.Slice(doc.Compared.SourceLinks, func(i, j int) bool {
		a, b := doc.Compared.SourceLinks[i], doc.Compared.SourceLinks[j]
		return string(a.Asset)+"\x00"+string(a.Source)+"\x00"+a.Native < string(b.Asset)+"\x00"+string(b.Source)+"\x00"+b.Native
	})
	sort.Slice(doc.LateLink, func(i, j int) bool { return doc.LateLink[i].Source < doc.LateLink[j].Source })
	sort.Slice(doc.Compared.ConsumerValueKeys, func(i, j int) bool {
		a, b := doc.Compared.ConsumerValueKeys[i], doc.Compared.ConsumerValueKeys[j]
		return string(a.Asset)+a.Fact+strings.Join(a.Dimensions, ",") < string(b.Asset)+b.Fact+strings.Join(b.Dimensions, ",")
	})

	// The values of each source with the owner-first presentation of the key.
	capture, err := r.hub.Capture(context.Background(), []semreg.AssetID{rsAsset}, time.Now)
	if err != nil {
		t.Fatal(err)
	}
	asset := capture.Assets[0]
	if !asset.PublicAdmitted || asset.Snapshot == nil || asset.Evaluation == nil {
		t.Fatalf("the paired asset is not admitted: %+v", asset)
	}
	for _, envelope := range asset.Snapshot.Facts {
		selection, ok, err := semselect.Present(*asset.Snapshot, *asset.Evaluation, envelope, rsOwnerSource)
		if err != nil {
			t.Fatal(err)
		}
		selected := semreg.CandidateID("")
		if ok {
			selected = selection.SelectedCandidate
		}
		presentation := rsPresentation{Policy: string(semselect.PolicyID), PolicyVersion: string(semselect.PolicyVersion), Owner: rsOwnerSource, Fact: string(envelope.Key.FactID), Dimensions: rsDimensions(envelope.Key)}
		for _, candidate := range envelope.Candidates {
			source := semreg.SourceID("")
			if candidate.Origin.SourceID != nil {
				source = *candidate.Origin.SourceID
			}
			role := "contributor"
			if source == rsOwnerSource {
				role = "owner"
			}
			row := rsSourceValue{Fact: string(envelope.Key.FactID), Dimensions: rsDimensions(envelope.Key), Source: source, Role: role, Value: rsValueText(candidate.Value), Quality: rsQualityText(candidate.Quality), Presented: candidate.CandidateID == selected}
			doc.SourceValues = append(doc.SourceValues, row)
			if row.Presented {
				presentation.SelectedSource, presentation.SelectedValue = source, row.Value
			}
		}
		doc.Presentation = append(doc.Presentation, presentation)
	}
	sort.Slice(doc.SourceValues, func(i, j int) bool { return doc.SourceValues[i].Source < doc.SourceValues[j].Source })

	doc.Export = []rsExportCall{rsExportOf(r.hub, "Hub.ExportRecoveryChecked", "not enabled: the hub is created with no recovery hooks, as the pin's composition creates it"),
		rsExportOf(r.hub, "Hub.ExportRecovery", "not enabled: the hub is created with no recovery hooks, as the pin's composition creates it")}
	rsEnableRecovery(r.hub)
	doc.Export = append(doc.Export, rsExportOf(r.hub, "Hub.ExportRecoveryChecked", "enabled after the declaration through the hub's own field, as the pin's package test seam does (a contributor list is refused at declaration while the hooks are enabled)"),
		rsExportOf(r.hub, "Hub.ExportRecovery", "enabled after the declaration through the hub's own field, as the pin's package test seam does (a contributor list is refused at declaration while the hooks are enabled)"))
	return doc
}

func rsWrite(t *testing.T, name string, document any) {
	t.Helper()
	root := os.Getenv("ORACLE_OUT")
	if root == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	data, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(root, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, name), append(data, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

// TestOracleRestart records the two lifecycles over one allocator store.
func TestOracleRestart(t *testing.T) {
	dir := t.TempDir()
	first := rsStart(t, dir)
	first.publishAll()
	firstCut := first.read("first", true)
	first.stop()

	second := rsStart(t, dir)
	second.publishAll()
	secondCut := second.read("second", false)

	rsWrite(t, "cut-first.json", firstCut)
	rsWrite(t, "cut-second.json", secondCut)
}

func rsExportOf(hub *semhub.Hub, call, hooks string) rsExportCall {
	var record semhub.RecoveryRecord
	var err error
	if call == "Hub.ExportRecovery" {
		record = hub.ExportRecovery()
	} else {
		record, err = hub.ExportRecoveryChecked()
	}
	out := rsExportCall{Call: call, Recovery: hooks, Version: record.Version, Assets: len(record.Assets), Epochs: len(record.Epochs), Regimes: len(record.Regimes), Unfixed: len(record.Unfixed), Drivers: len(record.Drivers),
		IsErrRestore: errors.Is(err, semhub.ErrRestore), IsRecoveryMultiSrc: errors.Is(err, semhub.ErrRecoveryMultiSource)}
	if err != nil {
		out.Error = err.Error()
	}
	return out
}

// rsEnableRecovery sets the hub's recovery hooks under the hub's own lock,
// exactly as the pin's package test seam enableRecovery does.
func rsEnableRecovery(hub *semhub.Hub) {
	value := reflect.ValueOf(hub).Elem()
	lock := value.FieldByName("mu")
	mutex := reflect.NewAt(lock.Type(), unsafe.Pointer(lock.UnsafeAddr())).Interface().(*sync.RWMutex)
	field := value.FieldByName("recovery")
	mutex.Lock()
	reflect.NewAt(field.Type(), unsafe.Pointer(field.UnsafeAddr())).Elem().Set(reflect.ValueOf(&semhub.RecoveryHooks{}))
	mutex.Unlock()
}
