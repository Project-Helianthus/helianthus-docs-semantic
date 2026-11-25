package matter

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"reflect"
	"testing"

	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/projection"
)

const model161Source = "matter/model161.go"
const model161Tests = "matter/model161_test.go"

func model161Case(t *testing.T, name, stimulus string, input, output fields) {
	t.Helper()
	oracleCase(t, "model161", name, model161Source, model161Tests, stimulus, input, output)
}

func TestOracleMatterModel161(t *testing.T) {
	recordModel161Target(t)
	recordModel161Agreement(t)
	recordModel161Canonical(t)
	recordModel161Joins(t)
	recordModel161Qualification(t)
	recordModel161Controls(t)
	recordModel161Accounting(t)
}

func recordProject161(t *testing.T, name, stimulus string, f matterFixture, variant string) {
	t.Helper()
	got, err := Project161(f.snapshot, f.evaluation)
	zero := reflect.DeepEqual(got, Result161{})
	output := obj(kv{"result_is_zero", zero})
	if !zero {
		output = append(output, kv{"result", got})
	}
	model161Case(t, name, stimulus, oracleSealedInput(f.snapshot, f.evaluation, kv{"call", "Project161"}, kv{"variant", variant}), oracleOutput(output, err))
}

func recordCanonical161(t *testing.T, name, stimulus string, r Result161, variant string) {
	t.Helper()
	raw, err := CanonicalJSON161(r)
	reportErr := r.Report.Validate()
	model161Case(t, name, stimulus, obj(kv{"call", "CanonicalJSON161"}, kv{"variant", variant}, kv{"result", r}),
		oracleOutput(obj(kv{"report_validate", oracleError(reportErr)}, kv{"canonical", oracleBytes(raw)}), err))
}

func positive161(t *testing.T, f matterFixture) Result161 {
	t.Helper()
	got, err := Project161(f.snapshot, f.evaluation)
	if err != nil {
		t.Fatal(err)
	}
	return got
}

func recordModel161Target(t *testing.T) {
	f := aa03Fixture(t)
	before, _ := json.Marshal([]any{f.snapshot, f.evaluation})
	got := positive161(t, f)
	again := positive161(t, f)
	a, aErr := CanonicalJSON161(got)
	b, bErr := CanonicalJSON161(again)
	after, _ := json.Marshal([]any{f.snapshot, f.evaluation})
	legacy, legacyErr := Project(f.snapshot, f.evaluation)
	positives := 0
	for _, row := range got.Report.Dispositions {
		if row.Kind == projection.ItemFact && row.ItemID == "evse.ac.current" {
			positives++
		}
	}
	detached := positive161(t, f)
	detached.Document.Attributes[0].Value.Milliampere = "0"
	redo := positive161(t, f)
	model161Case(t, "target-and-full-ledger", "TestAA03TargetAndFullLedger",
		oracleSealedInput(f.snapshot, f.evaluation, kv{"call", "Project161"}),
		obj(kv{"result", got}, kv{"canonical", oracleBytes(a)}, kv{"canonical_error", oracleError(aErr)},
			kv{"second_canonical_equal", bytes.Equal(a, b)}, kv{"second_canonical_error", oracleError(bErr)},
			kv{"inputs_unchanged", bytes.Equal(before, after)}, kv{"positive_current_rows", positives},
			kv{"result_is_detached", redo.Document.Attributes[0].Value.Milliampere == got.Document.Attributes[0].Value.Milliampere},
			kv{"manifest_161", Manifest161()}, kv{"legacy_project", obj(kv{"target_version", legacy.Document.TargetVersion}, kv{"report_target_version", legacy.Report.Manifest.TargetVersion}, kv{"error", oracleError(legacyErr)})},
			kv{"constants", obj(kv{"target_version_161", TargetVersion161}, kv{"mapping_revision_161", MappingRevision161}, kv{"docs_semantic_contract_path_161", DocsSemanticContractPath161}, kv{"docs_semantic_contract_sha256_161", DocsSemanticContractSHA256161}, kv{"model", model161()})}))
}

func recordModel161Agreement(t *testing.T) {
	cases := map[string]func(*Result161){
		"document contract":    func(r *Result161) { r.Document.Contract = "other.contract/v1" },
		"document target":      func(r *Result161) { r.Document.TargetID = "other.target" },
		"document version":     func(r *Result161) { r.Document.TargetVersion = TargetVersion },
		"document mapping":     func(r *Result161) { r.Document.MappingRevision = "2" },
		"sensor revision":      func(r *Result161) { r.Document.Model.ElectricalSensorRevision = 2 },
		"topology revision":    func(r *Result161) { r.Document.Model.PowerTopologyRevision = 2 },
		"measurement revision": func(r *Result161) { r.Document.Model.ElectricalPowerMeasurementRevision = 4 },
		"manifest target":      func(r *Result161) { r.Report.Manifest.TargetID = "other.target" },
		"manifest version":     func(r *Result161) { r.Report.Manifest.TargetVersion = TargetVersion },
		"manifest mapping":     func(r *Result161) { r.Report.Manifest.MappingRevision = "2" },
		"manifest kernel":      func(r *Result161) { r.Report.Manifest.KernelVersion = "other.kernel/v1" },
		"device":               func(r *Result161) { r.Document.Attributes[0].Element.DeviceType++ },
		"cluster":              func(r *Result161) { r.Document.Attributes[0].Element.Cluster++ },
		"kind":                 func(r *Result161) { r.Document.Attributes[0].Element.Kind = "command" },
		"attribute":            func(r *Result161) { r.Document.Attributes[0].Element.ElementID++ },
	}
	for i := 0; i < 5; i++ {
		i := i
		cases[fmt.Sprintf("pack id %d", i)] = func(r *Result161) { r.Report.Manifest.PackVersions[i].ID = "other.pack" }
		cases[fmt.Sprintf("pack version %d", i)] = func(r *Result161) { r.Report.Manifest.PackVersions[i].Version = "9.0.0" }
	}
	recordCanonical161(t, "agreement-control-unchanged", "TestAA03TargetAgreement (control)", positive161(t, aa03Fixture(t)), "unchanged")
	for _, name := range oracleKeys(cases) {
		r := positive161(t, aa03Fixture(t))
		cases[name](&r)
		recordCanonical161(t, oracleName("agreement", name), "TestAA03TargetAgreement/"+name, r, name)
	}
}

func recordModel161Canonical(t *testing.T) {
	for _, item := range []struct{ name, value string }{
		{"not-a-number", "not-a-number"}, {"empty", ""}, {"fraction", "1.5"}, {"exponent", "1e3"}, {"leading-space", " 1"}, {"plus-sign", "+1"},
		{"leading-zero", "01"}, {"negative-zero", "-0"}, {"above-maximum", "4611686018427387905"}, {"below-minimum", "-4611686018427387905"},
	} {
		r := positive161(t, aa03Fixture(t))
		r.Document.Attributes[0].Value.Milliampere = item.value
		recordCanonical161(t, "value-invalid-"+item.name, "TestAA03CanonicalValueAndReportAgreement/invalid value "+item.value, r, "milliamperes "+fmt.Sprintf("%q", item.value))
	}
	for _, value := range []string{"-4611686018427387904", "4611686018427387904", "0", "-1"} {
		r := positive161(t, aa03Fixture(t))
		r.Document.Attributes[0].Value.Milliampere = value
		recordCanonical161(t, oracleName("value-valid", map[string]string{"-4611686018427387904": "minimum", "4611686018427387904": "maximum", "0": "zero", "-1": "minus-one"}[value]), "TestAA03CanonicalValueAndReportAgreement/valid value "+value, r, "milliamperes "+value)
	}
	stimulus := "TestAA03CanonicalValueAndReportAgreement/"

	r := positive161(t, aa03Fixture(t))
	r.Document.Attributes = []TargetAttribute{}
	recordCanonical161(t, "report-transformed-row-without-attribute", stimulus+"transformed row without attribute", r, "attributes emptied")

	positive := positive161(t, aa03Fixture(t))
	empty := newMatterFixture(t, []semreg.FactCandidate{})
	r, err := Project161(empty.snapshot, empty.evaluation)
	if err != nil {
		t.Fatal(err)
	}
	r.Document.Attributes = positive.Document.Attributes
	recordCanonical161(t, "report-attribute-without-transformed-row", stimulus+"attribute without transformed row", r, "attributes taken from the positive projection")

	r = positive161(t, aa03Fixture(t))
	for i := range r.Report.Dispositions {
		row := &r.Report.Dispositions[i]
		if row.Kind != projection.ItemFact || row.ItemID == "evse.ac.current" || row.Outcome != projection.ProjectionUnknown {
			continue
		}
		for _, cur := range r.Report.Dispositions {
			if cur.ItemID == "evse.ac.current" {
				row.SourceKeys = cur.SourceKeys
			}
		}
		row.Outcome, row.Loss, row.Reason = projection.ProjectionExact, []projection.LossDetail{}, nil
		break
	}
	recordCanonical161(t, "report-unmapped-row-claimed-exact", stimulus+"unmapped row claimed exact", r, "first unmapped fact row made exact")

	for _, keepAttribute := range []bool{false, true} {
		r = positive161(t, aa03Fixture(t))
		for i := range r.Report.Dispositions {
			row := &r.Report.Dispositions[i]
			if row.Kind == projection.ItemFact && row.ItemID == "evse.ac.current" {
				row.Outcome, row.Loss, row.Reason = projection.ProjectionExact, []projection.LossDetail{}, nil
			}
		}
		name := "exact row without attribute"
		if keepAttribute {
			name = "exact row with attribute"
		} else {
			r.Document.Attributes = []TargetAttribute{}
		}
		recordCanonical161(t, oracleName("report", name), stimulus+name, r, name)
	}
}

func recordModel161Joins(t *testing.T) {
	cases := map[string]func(*semreg.EvaluationView){
		"snapshot": func(v *semreg.EvaluationView) {
			v.SnapshotID = semreg.SnapshotID(fmt.Sprintf("sha256:%x", sha256.Sum256([]byte("other snapshot"))))
		},
		"semantic revision":     func(v *semreg.EvaluationView) { v.Revisions.Semantic = "2" },
		"identity revision":     func(v *semreg.EvaluationView) { v.Revisions.Identity = "2" },
		"facts revision":        func(v *semreg.EvaluationView) { v.Revisions.Facts = "2" },
		"services revision":     func(v *semreg.EvaluationView) { v.Revisions.Services = "2" },
		"capabilities revision": func(v *semreg.EvaluationView) { v.Revisions.Capabilities = "2" },
		"candidate identity":    func(v *semreg.EvaluationView) { v.Facts[0].CandidateID = "candidate:other" },
		"candidate revision":    func(v *semreg.EvaluationView) { v.Facts[0].CandidateRevision = "2" },
		"candidate omission":    func(v *semreg.EvaluationView) { v.Facts = []semreg.EvaluatedFact{} },
		"freshness":             func(v *semreg.EvaluationView) { v.Facts[0].Freshness = semreg.FreshnessStale },
		"availability":          func(v *semreg.EvaluationView) { v.Facts[0].EffectiveAvailability = semreg.AvailabilityUnavailable },
	}
	for _, name := range oracleKeys(cases) {
		f := aa03Fixture(t)
		cases[name](&f.evaluation)
		sealEvaluation(t, &f.evaluation)
		recordProject161(t, oracleName("evaluation-join", name), "TestAA03EvaluationJoins/"+name, f, name)
	}

	sources := map[string]func(*semreg.FactCandidate){
		"binding":             func(c *semreg.FactCandidate) { v := semreg.NativeBindingID("binding:other"); c.BindingID = &v },
		"source epoch":        func(c *semreg.FactCandidate) { v := semreg.SourceEpochID("epoch:other"); c.SourceEpochID = &v },
		"driver generation":   func(c *semreg.FactCandidate) { v := semreg.Uint64("2"); c.DriverGeneration = &v },
		"origin source":       func(c *semreg.FactCandidate) { v := semreg.SourceID("source:other"); c.Origin.SourceID = &v },
		"origin binding":      func(c *semreg.FactCandidate) { v := semreg.NativeBindingID("binding:other"); c.Origin.BindingID = &v },
		"origin epoch":        func(c *semreg.FactCandidate) { v := semreg.SourceEpochID("epoch:other"); c.Origin.SourceEpochID = &v },
		"key pack id":         func(c *semreg.FactCandidate) { c.Key.PackID = "other.pack" },
		"key pack version":    func(c *semreg.FactCandidate) { c.Key.PackVersion = "9.0.0" },
		"key fact":            func(c *semreg.FactCandidate) { c.Key.FactID = "evse.ac.active_power" },
		"key dimension id":    func(c *semreg.FactCandidate) { c.Key.Dimensions[0].ID = "evse.dimension.connector" },
		"key dimension value": func(c *semreg.FactCandidate) { v := "l2"; c.Key.Dimensions[0].Value.Text = &v },
		"key dimension kind": func(c *semreg.FactCandidate) {
			v := true
			c.Key.Dimensions[0].Value = semreg.Value{Kind: semreg.ValueBoolean, Boolean: &v}
		},
	}
	for _, name := range oracleKeys(sources) {
		f := aa03Fixture(t)
		sources[name](&f.snapshot.Facts[0].Candidates[0])
		aa03Reseal(t, &f)
		recordProject161(t, oracleName("source-join", name), "TestAA03SourceJoins/"+name, f, name)
	}
}

func recordModel161Qualification(t *testing.T) {
	cases := map[string]func(*semreg.FactCandidate){
		"assertion":     func(c *semreg.FactCandidate) { c.Quality.Assertion = semreg.AssertionInferred },
		"qualification": func(c *semreg.FactCandidate) { c.Quality.Qualification = semreg.QualificationCandidate },
		"promotion":     func(c *semreg.FactCandidate) { c.Quality.Promotion = semreg.PromotionUnpromoted },
		"validity":      func(c *semreg.FactCandidate) { c.Quality.Validity = semreg.ValidityBad },
		"availability":  func(c *semreg.FactCandidate) { c.Quality.Availability = semreg.AvailabilityUnavailable },
		"freshness":     func(c *semreg.FactCandidate) { c.Quality.Freshness = semreg.FreshnessStale },
		"remainder": func(c *semreg.FactCandidate) {
			c.Value.Quantity.Number = semreg.Decimal{Coefficient: "1", Exponent10: -4}
		},
		"unit":          func(c *semreg.FactCandidate) { c.Value.Quantity.Unit = "unit.volt" },
		"source bounds": func(c *semreg.FactCandidate) { c.Value.Quantity.Number = semreg.Decimal{Coefficient: "1001"} },
	}
	for _, name := range oracleKeys(cases) {
		f := aa03Fixture(t)
		cases[name](&f.snapshot.Facts[0].Candidates[0])
		aa03Reseal(t, &f)
		recordProject161(t, oracleName("qualification", name), "TestAA03QualificationAndPrecision/"+name, f, name)
	}
	for _, phase := range []string{"l1", "l2"} {
		f := newMatterFixture(t, []semreg.FactCandidate{aa03Candidate("l1"), matterCandidate("candidate:synthetic:second", phase, "33", -1)})
		recordProject161(t, "qualification-ambiguous-"+phase, "TestAA03QualificationAndPrecision/ambiguous "+phase, f, "second candidate on phase "+phase)
	}
}

func recordModel161Controls(t *testing.T) {
	empty := newMatterFixture(t, []semreg.FactCandidate{})
	got, err := Project161(empty.snapshot, empty.evaluation)
	if err != nil {
		t.Fatal(err)
	}
	a, aErr := CanonicalJSON161(got)
	again, err := Project161(empty.snapshot, empty.evaluation)
	if err != nil {
		t.Fatal(err)
	}
	b, bErr := CanonicalJSON161(again)
	requested, dispositions := Ledger()
	model161Case(t, "empty-snapshot", "TestAA03EmptyAndPhaseControls/empty", oracleSealedInput(empty.snapshot, empty.evaluation, kv{"call", "Project161"}),
		obj(kv{"result", got}, kv{"attributes_non_nil_and_empty", got.Document.Attributes != nil && len(got.Document.Attributes) == 0},
			kv{"requested_equals_ledger", reflect.DeepEqual(got.Report.Requested, requested)}, kv{"dispositions_equal_ledger", reflect.DeepEqual(got.Report.Dispositions, dispositions)},
			kv{"canonical", oracleBytes(a)}, kv{"canonical_error", oracleError(aErr)}, kv{"second_canonical_equal", bytes.Equal(a, b)}, kv{"second_canonical_error", oracleError(bErr)}))
	for _, phase := range []string{"l2", "l3"} {
		f := newMatterFixture(t, []semreg.FactCandidate{aa03Candidate(phase)})
		r := positive161(t, f)
		kept := true
		for _, row := range r.Report.Dispositions {
			if row.ItemID == "evse.ac.current" && !reflect.DeepEqual(row.SourceKeys, []semreg.FactKey{f.snapshot.Facts[0].Key}) {
				kept = false
			}
		}
		model161Case(t, "phase-control-"+phase, "TestAA03EmptyAndPhaseControls/"+phase, oracleSealedInput(f.snapshot, f.evaluation, kv{"call", "Project161"}),
			obj(kv{"result", r}, kv{"phase_source_key_kept", kept}))
	}
}

func recordModel161Accounting(t *testing.T) {
	current := func(r *Result161) *projection.ProjectionDisposition {
		for i := range r.Report.Dispositions {
			if r.Report.Dispositions[i].ItemID == "evse.ac.current" && r.Report.Dispositions[i].Kind == projection.ItemFact {
				return &r.Report.Dispositions[i]
			}
		}
		t.Fatal("current disposition missing")
		return nil
	}
	accounting := map[string]func(*Result161){
		"paired omission": func(r *Result161) {
			last := len(r.Report.Requested) - 1
			r.Report.Requested = r.Report.Requested[:last]
			r.Report.Dispositions = r.Report.Dispositions[:last]
		},
		"empty source keys": func(r *Result161) { current(r).SourceKeys = []semreg.FactKey{} },
		"no reason":         func(r *Result161) { current(r).Reason = nil },
		"reversible loss":   func(r *Result161) { current(r).Loss[0].Reversible = true },
		"wrong reason": func(r *Result161) {
			reason := semreg.DefinitionID("matter.unmapped.v1")
			current(r).Reason = &reason
		},
		"foreign source": func(r *Result161) { current(r).SourceKeys[0].FactID = "evse.ac.voltage" },
	}
	for _, name := range oracleKeys(accounting) {
		r := positive161(t, aa03Fixture(t))
		accounting[name](&r)
		recordCanonical161(t, oracleName("accounting", name), "TestAA03ReportAccountingAndCurrentMetadata/"+name, r, name)
	}
	recordCanonical161(t, "accounting-control-unchanged", "TestAA03ReportAccountingAndCurrentMetadata (control)", positive161(t, aa03Fixture(t)), "unchanged")

	phaseText, otherText := "l1", "l2"
	flag := true
	phase := semreg.Dimension{ID: "evse.dimension.phase", Value: semreg.Value{Kind: semreg.ValueText, Text: &phaseText}}
	connector := semreg.Dimension{ID: "evse.dimension.connector", Value: semreg.Value{Kind: semreg.ValueText, Text: &otherText}}
	dimensions := map[string][]semreg.Dimension{
		"other phase control": {{ID: phase.ID, Value: semreg.Value{Kind: semreg.ValueText, Text: &otherText}}},
		"wrong id":            {{ID: connector.ID, Value: phase.Value}},
		"wrong kind":          {{ID: phase.ID, Value: semreg.Value{Kind: semreg.ValueBoolean, Boolean: &flag}}},
		"missing":             {},
		"extra":               {connector, phase},
	}
	for _, name := range oracleKeys(dimensions) {
		r := positive161(t, aa03Fixture(t))
		row := current(&r)
		row.SourceKeys[0].Dimensions = dimensions[name]
		recordCanonical161(t, oracleName("current-row-dimensions", name), "TestAA03CurrentRowSourceDimensions/"+name, r, name)
	}

	emptyResult := func() Result161 {
		f := newMatterFixture(t, []semreg.FactCandidate{})
		r, err := Project161(f.snapshot, f.evaluation)
		if err != nil {
			t.Fatal(err)
		}
		return r
	}
	recordCanonical161(t, "empty-current-row-control-unchanged", "TestAA03EmptyProjectionCurrentRowMustBeLedgerRow (control)", emptyResult(), "unchanged")
	reasonAltered := semreg.DefinitionID("matter.altered.v1")
	emptyCases := map[string]func(*projection.ProjectionDisposition){
		"unsupported instead of unknown": func(d *projection.ProjectionDisposition) { d.Outcome = projection.ProjectionUnsupported },
		"unknown with altered reason":    func(d *projection.ProjectionDisposition) { d.Reason = &reasonAltered },
	}
	for _, name := range oracleKeys(emptyCases) {
		r := emptyResult()
		emptyCases[name](current(&r))
		recordCanonical161(t, oracleName("empty-current-row", name), "TestAA03EmptyProjectionCurrentRowMustBeLedgerRow/"+name, r, name)
	}
}
