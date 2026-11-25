package main

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semhub"
	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/graph"
)

// The graph recorder is harness-only. It reads one hub that the pin's own
// publishers filled from the pin's own offline fixtures and writes the cut as
// a family document. It holds no clock, no digest and no identifier that the
// run allocates (source epoch, binding, candidate, snapshot or cut identifier),
// so two recordings of one family are the same bytes.

const oracleGraphFormat = "helianthus-oracle-graph/1"

type ogFamilyTable struct {
	Family string `json:"family"`
	Listed bool   `json:"listed"`
	Graph  bool   `json:"graph"`
}

type ogAsset struct {
	Asset       semreg.AssetID `json:"asset"`
	Driver      string         `json:"driver"`
	Enforcement string         `json:"enforcement"`
}

type ogNotIncluded struct {
	Asset  semreg.AssetID `json:"asset"`
	Reason string         `json:"reason"`
}

type ogCut struct {
	Completeness string          `json:"completeness"`
	Members      []string        `json:"members"`
	Excluded     []string        `json:"excluded"`
	NotIncluded  []ogNotIncluded `json:"not_included"`
}

type ogResource struct {
	Resource semreg.ResourceID   `json:"resource"`
	Kind     semreg.DefinitionID `json:"kind,omitempty"`
	Asset    semreg.AssetID      `json:"asset"`
	State    string              `json:"state"`
	Anchor   string              `json:"anchor"`
	Origin   string              `json:"origin"`
	Planes   []graph.PlaneID     `json:"planes"`
}

type ogRelation struct {
	Asset      semreg.AssetID       `json:"asset"`
	Definition semreg.DefinitionRef `json:"definition"`
	From       semreg.ResourceID    `json:"from"`
	To         semreg.ResourceID    `json:"to"`
	State      string               `json:"state"`
	Coherence  string               `json:"coherence"`
	Basis      string               `json:"basis_class"`
	Planes     []graph.PlaneID      `json:"planes"`
}

type ogFact struct {
	Asset      semreg.AssetID      `json:"asset"`
	Fact       semreg.DefinitionID `json:"fact"`
	Dimensions []string            `json:"dimensions"`
	Candidates int                 `json:"candidates"`
	Planes     []graph.PlaneID     `json:"planes"`
}

type ogDocument struct {
	Format        string          `json:"format,omitempty"`
	Kind          string          `json:"kind,omitempty"`
	Name          string          `json:"name"`
	Source        string          `json:"source,omitempty"`
	Fixture       string          `json:"fixture,omitempty"`
	Publication   string          `json:"publication,omitempty"`
	Statement     string          `json:"statement,omitempty"`
	FamilyTable   []ogFamilyTable `json:"family_table,omitempty"`
	CatalogDigest string          `json:"catalog_digest,omitempty"`
	Assets        []ogAsset       `json:"assets"`
	Cut           ogCut           `json:"cut"`
	Resources     []ogResource    `json:"resources"`
	Relations     []ogRelation    `json:"relations"`
	Facts         []ogFact        `json:"facts"`
	Findings      []string        `json:"findings"`
	Declared      []string        `json:"declared_relation_definitions,omitempty"`
	Retrieval     *ogRetrievalDoc `json:"retrieval,omitempty"`
	Evidence      []string        `json:"evidence,omitempty"`
}

// ogOutcome is one attempt a negative class makes and what the pin answers.
type ogOutcome struct {
	Case       string   `json:"case"`
	Attempt    string   `json:"attempt"`
	Answer     string   `json:"answer"`
	Identifier string   `json:"error_identifier,omitempty"`
	Detail     []string `json:"detail,omitempty"`
}

func ogOut(t *testing.T, name string, document any) {
	t.Helper()
	root := os.Getenv("ORACLE_OUT")
	if root == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	data, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(root, name)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(data, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

func ogTable() []ogFamilyTable {
	out := make([]ogFamilyTable, 0, len(semanticFamilyGraphTable))
	for _, entry := range semanticFamilyGraphTable {
		out = append(out, ogFamilyTable{Family: string(entry.family), Listed: true, Graph: semanticFamilyGraph(entry.family)})
	}
	return out
}

func ogPlanes(planes []graph.PlaneID) []graph.PlaneID {
	if planes == nil {
		return []graph.PlaneID{}
	}
	return planes
}

func ogDimensions(key semreg.FactKey) []string {
	out := []string{}
	for _, dimension := range key.Dimensions {
		text := ""
		switch {
		case dimension.Value.Text != nil:
			text = *dimension.Value.Text
		default:
			encoded, _ := json.Marshal(dimension.Value)
			text = string(encoded)
		}
		out = append(out, string(dimension.ID)+"="+text)
	}
	return out
}

func ogAnchorText(anchor semreg.ResourceAnchor) string {
	text := string(anchor.Class) + "/" + string(anchor.Basis)
	if anchor.Slot != nil {
		text += "/slot:" + *anchor.Slot
	}
	if anchor.Parent != nil {
		text += "/parent:" + string(*anchor.Parent)
	}
	return text
}

func ogFindingText(finding graph.CutFinding) string {
	parts := []string{string(finding.Kind)}
	for _, asset := range finding.Assets {
		parts = append(parts, "member="+string(asset))
	}
	for _, resource := range finding.Resources {
		parts = append(parts, "resource="+string(resource.AssetID)+"/"+string(resource.ResourceID))
	}
	if finding.Relation != nil {
		parts = append(parts, "relation="+string(finding.Relation.AssetID)+"/"+string(finding.Relation.Definition.ID)+"/"+string(finding.Relation.From)+"->"+string(finding.Relation.To))
	}
	if finding.Absence != nil {
		parts = append(parts, "absence="+string(finding.Absence.AssetID)+"/"+string(finding.Absence.Definition.ID)+"/"+string(finding.Absence.Resource)+"/"+string(finding.Absence.Side))
	}
	return strings.Join(parts, " ")
}

// ogRead describes the hub's cut as the family document: the sources of every
// section are the hub's own graph state, cut, snapshots and the SemReg
// retrieval over the cut.
func ogRead(t *testing.T, hub *semhub.Hub, name, fixture, statement string) ogDocument {
	t.Helper()
	state, err := hub.GraphState()
	if err != nil {
		t.Fatal(err)
	}
	captured, err := hub.CaptureCut(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	cut := captured.Cut
	doc := ogDocument{Format: oracleGraphFormat, Kind: "family", Name: name, Source: "cmd/gateway/semantic_family_graph.go and internal/semhub/graph_cut.go", Fixture: fixture, Statement: statement,
		FamilyTable: ogTable(), CatalogDigest: string(state.CatalogDigest), Assets: []ogAsset{}, Resources: []ogResource{}, Relations: []ogRelation{}, Facts: []ogFact{}, Findings: []string{}}
	doc.Publication = "empty"
	for _, asset := range state.Assets {
		if asset.Enforcement == semhub.GraphEnforced {
			doc.Publication = "graph"
		} else if doc.Publication == "empty" {
			doc.Publication = "ungraphed"
		}
		doc.Assets = append(doc.Assets, ogAsset{Asset: asset.Asset, Driver: asset.Driver, Enforcement: string(asset.Enforcement)})
	}
	doc.Cut = ogCut{Completeness: string(cut.Completeness()), Members: []string{}, Excluded: []string{}, NotIncluded: []ogNotIncluded{}}
	snapshots := make([]semreg.Snapshot, 0, len(cut.Members()))
	for _, member := range cut.Members() {
		doc.Cut.Members = append(doc.Cut.Members, string(member.AssetID))
		view, err := hub.Inspect(member.AssetID)
		if err != nil || !view.Present {
			t.Fatalf("inspect member %s: present=%v err=%v", member.AssetID, view.Present, err)
		}
		if view.Snapshot.SnapshotID != member.SnapshotID {
			t.Fatalf("member %s changed between the cut and the read", member.AssetID)
		}
		snapshots = append(snapshots, view.Snapshot)
		for _, resource := range view.Snapshot.Resources {
			doc.Resources = append(doc.Resources, ogResource{Resource: resource.ResourceID, Kind: resource.Kind, Asset: member.AssetID, State: string(resource.State), Anchor: ogAnchorText(resource.Anchor), Origin: string(resource.Origin.Kind), Planes: ogPlanes(cut.PlanesOfResource(resource.ResourceID))})
		}
		for _, envelope := range view.Snapshot.Facts {
			doc.Facts = append(doc.Facts, ogFact{Asset: member.AssetID, Fact: envelope.Key.FactID, Dimensions: ogDimensions(envelope.Key), Candidates: len(envelope.Candidates), Planes: ogPlanes(cut.PlanesOfFact(member.AssetID, envelope.Key))})
		}
	}
	for _, excluded := range cut.Excluded() {
		doc.Cut.Excluded = append(doc.Cut.Excluded, string(excluded))
	}
	for _, item := range captured.NotIncluded {
		doc.Cut.NotIncluded = append(doc.Cut.NotIncluded, ogNotIncluded{Asset: item.Asset, Reason: string(item.Reason)})
	}
	for _, relation := range cut.Relations() {
		basis := ""
		for _, snapshot := range snapshots {
			if snapshot.AssetID != relation.AssetID {
				continue
			}
			for _, held := range snapshot.Relations {
				if held.Definition == relation.Definition && held.From == relation.From && held.To == relation.To {
					basis = string(held.BasisClass)
				}
			}
		}
		doc.Relations = append(doc.Relations, ogRelation{Asset: relation.AssetID, Definition: relation.Definition, From: relation.From, To: relation.To, State: string(relation.State), Coherence: string(relation.Coherence), Basis: basis,
			Planes: ogPlanes(cut.PlanesOfRelation(semreg.RelationKey{Definition: relation.Definition, From: relation.From, To: relation.To}))})
	}
	for _, finding := range cut.Findings() {
		doc.Findings = append(doc.Findings, ogFindingText(finding))
	}
	sort.Slice(doc.Resources, func(i, j int) bool {
		if doc.Resources[i].Asset != doc.Resources[j].Asset {
			return doc.Resources[i].Asset < doc.Resources[j].Asset
		}
		return doc.Resources[i].Resource < doc.Resources[j].Resource
	})
	retrieval := ogRetrieval(t, doc.Resources)
	doc.Retrieval = &retrieval
	return doc
}

// ogEmpty is the document of a family whose publisher declares nothing on the
// hub at the pin: the hub the pin composes holds no asset of it, and the cut
// of that hub is read exactly like any other.
func ogEmpty(t *testing.T, name, source string, evidence []string, statement string) ogDocument {
	t.Helper()
	hub, err := semhub.New(semhub.Options{})
	if err != nil {
		t.Fatal(err)
	}
	doc := ogRead(t, hub, name, "no pinned fixture drives a publisher: the pin composes none", statement)
	doc.Source = source
	doc.Evidence = evidence
	return doc
}

// ogSourceDoesNotUse records, from the pin's own file, that the file names no
// publication hub.
func ogSourceDoesNotUse(t *testing.T, file string) string {
	t.Helper()
	data, err := os.ReadFile(file)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(data), "semhub") {
		return "cmd/gateway/" + file + " names the publication hub"
	}
	return "cmd/gateway/" + file + " does not name the publication hub"
}

type ogLensRow struct {
	Lens      semreg.DefinitionID   `json:"lens"`
	Planes    []graph.PlaneID       `json:"planes"`
	RootKinds []semreg.DefinitionID `json:"root_kinds"`
	Roots     []semreg.ResourceID   `json:"roots"`
}

// ogRetrievalDoc is the sites traversal and the seeded lenses at the pin. The
// semantic registry version the gateway resolves gives the cut and the plane
// membership; the traversal and lens retrieval over a cut are checked below
// against that exact module source, and the catalog it embeds lists its lenses.
type ogRetrievalDoc struct {
	TraverseFunction string              `json:"graph_traverse_function"`
	LensFunction     string              `json:"graph_lens_retrieval_function"`
	SitesEntry       string              `json:"sites_traversal"`
	SiteKind         semreg.DefinitionID `json:"installation_root_kind"`
	SiteRoots        []semreg.ResourceID `json:"installation_roots_in_the_cut"`
	SeededLenses     []ogLensRow         `json:"seeded_lenses"`
	Statement        string              `json:"statement"`
}

func ogModuleFunction(t *testing.T, directory, name string) string {
	t.Helper()
	entries, err := os.ReadDir(directory)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".go") || strings.HasSuffix(entry.Name(), "_test.go") {
			continue
		}
		data, err := os.ReadFile(filepath.Join(directory, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if strings.Contains(string(data), "\nfunc "+name+"(") {
			return "present"
		}
	}
	return "absent"
}

func ogRetrieval(t *testing.T, resources []ogResource) ogRetrievalDoc {
	t.Helper()
	output, err := exec.Command("go", "list", "-m", "-f", "{{.Version}} {{.Dir}}", "github.com/Project-Helianthus/helianthus-semreg").Output()
	if err != nil {
		t.Fatal(err)
	}
	fields := strings.Fields(string(output))
	if len(fields) != 2 {
		t.Fatalf("go list answered %q", output)
	}
	directory := filepath.Join(fields[1], "semreg", "v1", "graph")
	catalog, err := graph.Embedded()
	if err != nil {
		t.Fatal(err)
	}
	doc := ogRetrievalDoc{TraverseFunction: ogModuleFunction(t, directory, "Traverse"), LensFunction: ogModuleFunction(t, directory, "RetrieveLens"), SitesEntry: "not_available", SiteKind: "resource.site", SiteRoots: []semreg.ResourceID{}, SeededLenses: []ogLensRow{}}
	if doc.TraverseFunction == "present" {
		t.Fatal("the pin's registry has a cut traversal: the recorder must run it")
	}
	rootsOf := func(kinds ...semreg.DefinitionID) []semreg.ResourceID {
		out := []semreg.ResourceID{}
		for _, resource := range resources {
			if resource.State != string(semreg.ResourceCurrent) {
				continue
			}
			for _, kind := range kinds {
				if resource.Kind == kind {
					out = append(out, resource.Resource)
				}
			}
		}
		return out
	}
	doc.SiteRoots = rootsOf(doc.SiteKind)
	lenses := catalog.Lenses()
	sort.Slice(lenses, func(i, j int) bool { return lenses[i].ID < lenses[j].ID })
	for _, lens := range lenses {
		doc.SeededLenses = append(doc.SeededLenses, ogLensRow{Lens: lens.ID, Planes: lens.Planes, RootKinds: lens.RootKinds, Roots: rootsOf(lens.RootKinds...)})
	}
	doc.Statement = "At this pin the semantic registry the gateway resolves has no cut traversal function and no lens retrieval function, so no sites traversal and no lens retrieval is recorded; the cut, its relation coherence, findings and plane membership are the hub's own. The installation roots are the cut's current resources of the installation-root kind; every seeded lens of the embedded catalog is listed with the roots the cut has for it."
	return doc
}

// ogState is the cut of a hub after a negative scenario: the family document
// without the family table and the retrieval statement, which every family
// file already carries.
func ogState(t *testing.T, hub *semhub.Hub, name string) *ogDocument {
	t.Helper()
	doc := ogRead(t, hub, name, "", "")
	doc.FamilyTable = nil
	doc.Retrieval = nil
	doc.Fixture, doc.Statement, doc.Source, doc.Format, doc.Kind, doc.Publication, doc.CatalogDigest = "", "", "", "", "", "", ""
	return &doc
}

type ogScenario struct {
	Case     string      `json:"case"`
	Fixture  string      `json:"fixture"`
	Outcomes []ogOutcome `json:"outcomes"`
	State    *ogDocument `json:"state,omitempty"`
}

type ogNegativeDocument struct {
	Format    string       `json:"format"`
	Kind      string       `json:"kind"`
	Class     string       `json:"class"`
	Source    string       `json:"source"`
	Statement string       `json:"statement"`
	Scenarios []ogScenario `json:"scenarios"`
}

func ogNegative(class, statement string, scenarios ...ogScenario) ogNegativeDocument {
	return ogNegativeDocument{Format: oracleGraphFormat, Kind: "negative", Class: class, Source: "cmd/gateway/semantic_family_graph.go and internal/semhub", Statement: statement, Scenarios: scenarios}
}

// ogAnswer is the pin's answer to one attempt: accepted, or refused with the
// kernel's stable identifier and its text.
func ogAnswer(label, attempt string, err error) ogOutcome {
	out := ogOutcome{Case: label, Attempt: attempt, Answer: "accepted"}
	if err != nil {
		out.Answer = "refused"
		out.Identifier = string(semreg.ErrorIdentifier(err))
		out.Detail = []string{err.Error()}
	}
	return out
}

// ogDeclaredRelations lists the relation definitions the embedded catalog holds
// for one pack, whether or not the pin's publisher publishes an instance.
func ogDeclaredRelations(t *testing.T, pack string) []string {
	t.Helper()
	catalog, err := graph.Embedded()
	if err != nil {
		t.Fatal(err)
	}
	out := []string{}
	for _, element := range catalog.Elements() {
		if element.ElementKind == graph.KindRelation && strings.HasPrefix(string(element.Ref.ID), pack+".relation.") {
			out = append(out, string(element.Ref.ID))
		}
	}
	sort.Strings(out)
	return out
}
