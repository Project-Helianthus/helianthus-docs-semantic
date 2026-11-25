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

const projectionSource = "matter/projection.go"
const projectionTests = "matter/projection_test.go"

func ledgerDigest(requested []projection.RequestedItem, dispositions []projection.ProjectionDisposition) string {
	raw, err := json.Marshal([]any{requested, dispositions})
	if err != nil {
		panic(err)
	}
	return fmt.Sprintf("sha256:%x", sha256.Sum256(raw))
}

func quantityValue(coefficient string, exponent int32, unit string) semreg.Value {
	return semreg.Value{Kind: semreg.ValueQuantity, Quantity: &semreg.Quantity{Number: semreg.Decimal{Coefficient: coefficient, Exponent10: exponent}, Unit: semreg.DefinitionID(unit)}}
}

func projectionCase(t *testing.T, name, stimulus string, input, output fields) {
	t.Helper()
	oracleCase(t, "projection", name, projectionSource, projectionTests, stimulus, input, output)
}

func TestOracleMatterProjection(t *testing.T) {
	recordProjectionLedger(t)
	recordProjectionConversion(t)
	recordProjectionEligibility(t)
	recordProjectionEndToEnd(t)
	recordProjectionRejections(t)
	recordProjectionContributors(t)
	recordProjectionMappedKey(t)
}

func recordProjectionLedger(t *testing.T) {
	manifest := Manifest()
	requested, dispositions := Ledger()
	projectionCase(t, "manifest-and-ledger", "TestManifestAndLedgerCoverPinnedMetadataExactlyOnce",
		obj(kv{"calls", []string{"Manifest()", "Ledger()"}}),
		obj(kv{"manifest", manifest}, kv{"requested", requested}, kv{"dispositions", dispositions},
			kv{"constants", obj(kv{"contract", Contract}, kv{"target_id", TargetID}, kv{"target_version", TargetVersion}, kv{"mapping_revision", MappingRevision},
				kv{"matter_model_commit", MatterModelCommit}, kv{"matter_spec_commit", MatterSpecCommit}, kv{"docs_semantic_commit", DocsSemanticCommit},
				kv{"docs_semantic_contract_path", DocsSemanticContractPath}, kv{"docs_semantic_contract_sha256", DocsSemanticContractSHA256})}))

	firstRequested, firstDispositions := Ledger()
	secondRequested, secondDispositions := Ledger()
	operationRows, actionable := 0, 0
	for _, disposition := range firstDispositions {
		if disposition.Kind == projection.ItemOperation {
			operationRows++
			if len(disposition.SourceKeys) != 0 || disposition.Outcome != projection.ProjectionUnknown {
				actionable++
			}
		}
	}
	projectionCase(t, "ledger-is-deterministic", "TestLedgerIsDeterministicAndDoesNotExposeOperations",
		obj(kv{"calls", []string{"Ledger()", "Ledger()"}}),
		obj(kv{"requested_equal", reflect.DeepEqual(firstRequested, secondRequested)}, kv{"dispositions_equal", reflect.DeepEqual(firstDispositions, secondDispositions)},
			kv{"ledger_digest", ledgerDigest(firstRequested, firstDispositions)}, kv{"requested_count", len(firstRequested)}, kv{"operation_rows", operationRows}, kv{"actionable_operation_rows", actionable}))
}

func recordProjectionConversion(t *testing.T) {
	convert := func(name, stimulus string, value semreg.Value) {
		got, err := amperesToMilliampere(value)
		projectionCase(t, name, stimulus, obj(kv{"call", "amperesToMilliampere"}, kv{"value", value}), oracleOutput(obj(kv{"milliamperes", got}), err))
	}
	stimulus := "TestEVSEActiveCurrentUsesPinnedNumericTargetAndExactConversion"
	convert("conversion-32-exp-minus-1", stimulus, quantityValue("32", -1, "unit.ampere"))
	convert("conversion-boundary-minimum", stimulus, quantityValue("-4611686018427387904", -3, "unit.ampere"))
	convert("conversion-boundary-maximum", stimulus, quantityValue("4611686018427387904", -3, "unit.ampere"))
	projectionCase(t, "numeric-target-element", stimulus, obj(kv{"read", "evseActiveCurrent"}), obj(kv{"element", evseActiveCurrent}))
	failClosed := "TestEVSECurrentFailsClosedOnWrongUnitOrPrecision"
	convert("conversion-wrong-unit", failClosed, quantityValue("1", 0, "unit.volt"))
	convert("conversion-lossy-precision", failClosed, quantityValue("1", -4, "unit.ampere"))
	convert("conversion-above-maximum", failClosed, quantityValue("4611686018427387905", -3, "unit.ampere"))
	convert("conversion-below-minimum", failClosed, quantityValue("-4611686018427387905", -3, "unit.ampere"))
}

func recordProjectionEligibility(t *testing.T) {
	mapped := matterCandidate("candidate:matter:mapped", "l1", "32", -1)
	unmapped := matterCandidate("candidate:matter:unmapped", "l1", "32", -1)
	unmapped.Key.FactID = "evse.ac.voltage"
	snapshot := semreg.Snapshot{Facts: []semreg.FactEnvelope{{Key: mapped.Key, Candidates: []semreg.FactCandidate{mapped}}, {Key: unmapped.Key, Candidates: []semreg.FactCandidate{unmapped}}}}
	for _, item := range []struct {
		name string
		fact semreg.EvaluatedFact
	}{
		{"stale", semreg.EvaluatedFact{Freshness: semreg.FreshnessStale, EffectiveAvailability: semreg.AvailabilityAvailable}},
		{"unavailable", semreg.EvaluatedFact{Freshness: semreg.FreshnessFresh, EffectiveAvailability: semreg.AvailabilityUnavailable}},
	} {
		for _, target := range []struct {
			name string
			id   semreg.CandidateID
		}{{"mapped-key", mapped.CandidateID}, {"unmapped-key", unmapped.CandidateID}} {
			fact := item.fact
			fact.CandidateID = target.id
			view := semreg.EvaluationView{Facts: []semreg.EvaluatedFact{fact}}
			err := eligibleMappedEvaluation(snapshot, view)
			projectionCase(t, oracleName("eligibility", item.name, target.name), "TestEvaluationEligibilityFailsClosedForStaleAndUnavailable",
				obj(kv{"call", "eligibleMappedEvaluation"}, kv{"snapshot", snapshot}, kv{"evaluation", view}), oracleOutput(nil, err))
		}
	}

	result := Result{Document: Document{Contract: Contract, TargetID: TargetID, TargetVersion: TargetVersion, MappingRevision: MappingRevision, Attributes: []TargetAttribute{}}}
	raw, err := CanonicalJSON(result)
	projectionCase(t, "canonical-json-without-report", "TestCanonicalJSONIsDeterministicForEquivalentResult",
		obj(kv{"call", "CanonicalJSON"}, kv{"result", result}), oracleOutput(obj(kv{"canonical", oracleBytes(raw)}), err))
}

func recordProjectionEndToEnd(t *testing.T) {
	fixture := newMatterFixture(t, []semreg.FactCandidate{matterCandidate("candidate:matter:l1", "l1", "32", -1)})
	beforeSnapshot, _ := json.Marshal(fixture.snapshot)
	beforeEvaluation, _ := json.Marshal(fixture.evaluation)
	first, err := Project(fixture.snapshot, fixture.evaluation)
	if err != nil {
		t.Fatal(err)
	}
	firstJSON, firstErr := CanonicalJSON(first)
	second, err := Project(fixture.snapshot, fixture.evaluation)
	if err != nil {
		t.Fatal(err)
	}
	secondJSON, secondErr := CanonicalJSON(second)
	afterSnapshot, _ := json.Marshal(fixture.snapshot)
	afterEvaluation, _ := json.Marshal(fixture.evaluation)
	transformed := 0
	for _, disposition := range first.Report.Dispositions {
		if disposition.ItemID == "evse.ac.current" && disposition.Kind == projection.ItemFact {
			transformed++
		}
	}
	projectionCase(t, "project-evse-current-end-to-end", "TestProjectEVSECurrentEndToEndAndContractPin",
		obj(kv{"call", "Project"}, kv{"snapshot", fixture.snapshot}, kv{"evaluation", fixture.evaluation}),
		obj(kv{"result", first}, kv{"canonical", oracleBytes(firstJSON)}, kv{"canonical_error", oracleError(firstErr)},
			kv{"second_canonical_json_equal", bytes.Equal(firstJSON, secondJSON)}, kv{"second_canonical_error", oracleError(secondErr)},
			kv{"inputs_unchanged", bytes.Equal(beforeSnapshot, afterSnapshot) && bytes.Equal(beforeEvaluation, afterEvaluation)},
			kv{"manifest_equal", reflect.DeepEqual(first.Report.Manifest, Manifest())}, kv{"transformed_current_rows", transformed}))
}

func recordProjectionRejections(t *testing.T) {
	stimulus := "TestProjectRejectsEvaluationCorrespondenceDrift"
	for _, tc := range []struct {
		name   string
		mutate func(*semreg.EvaluationView)
	}{
		{"candidate revision", func(v *semreg.EvaluationView) { v.Facts[0].CandidateRevision = "2" }},
		{"dangling candidate", func(v *semreg.EvaluationView) { v.Facts[0].CandidateID = "candidate:matter:dangling" }},
		{"omitted candidate", func(v *semreg.EvaluationView) { v.Facts = []semreg.EvaluatedFact{} }},
	} {
		fixture := newMatterFixture(t, []semreg.FactCandidate{matterCandidate("candidate:matter:l1", "l1", "32", -1)})
		tc.mutate(&fixture.evaluation)
		sealEvaluation(t, &fixture.evaluation)
		recordProject(t, oracleName("correspondence", tc.name), stimulus+"/"+tc.name, fixture, tc.name)
	}

	for _, tc := range []struct {
		name          string
		mutateQuality func(*semreg.Quality)
		mutateView    func(*semreg.EvaluationView)
	}{
		{name: "unqualified", mutateQuality: func(q *semreg.Quality) {
			q.Qualification, q.Promotion = semreg.QualificationCandidate, semreg.PromotionUnpromoted
		}},
		{name: "unpromoted", mutateQuality: func(q *semreg.Quality) { q.Promotion = semreg.PromotionUnpromoted }},
		{name: "invalid", mutateQuality: func(q *semreg.Quality) { q.Validity, q.Promotion = semreg.ValidityBad, semreg.PromotionUnpromoted }},
		{name: "stale", mutateView: func(v *semreg.EvaluationView) { v.Facts[0].Freshness = semreg.FreshnessStale }},
		{name: "unavailable", mutateView: func(v *semreg.EvaluationView) { v.Facts[0].EffectiveAvailability = semreg.AvailabilityUnavailable }},
	} {
		fixture := newMatterFixture(t, []semreg.FactCandidate{matterCandidate("candidate:matter:l1", "l1", "32", -1)})
		if tc.mutateQuality != nil {
			tc.mutateQuality(&fixture.snapshot.Facts[0].Candidates[0].Quality)
			sealSnapshot(t, &fixture.snapshot)
			fixture.evaluation = evaluateMatterSnapshot(t, fixture.snapshot)
		}
		if tc.mutateView != nil {
			tc.mutateView(&fixture.evaluation)
			sealEvaluation(t, &fixture.evaluation)
		}
		recordProject(t, oracleName("ineligible", tc.name), "TestProjectRejectsIneligibleQualityAndEvaluation/"+tc.name, fixture, tc.name)
	}

	stimulus = "TestProjectRejectsWrongDimensionUnitBoundsConflictAndAmbiguity"
	one := func() matterFixture {
		return newMatterFixture(t, []semreg.FactCandidate{matterCandidate("candidate:matter:l1", "l1", "32", -1)})
	}
	f := one()
	f.snapshot.Facts[0].Key.Dimensions[0].ID = "evse.dimension.connector"
	f.snapshot.Facts[0].Candidates[0].Key = f.snapshot.Facts[0].Key
	sealSnapshot(t, &f.snapshot)
	f.evaluation = evaluateMatterSnapshot(t, f.snapshot)
	recordProject(t, "reject-wrong-phase-dimension", stimulus+"/wrong phase dimension", f, "wrong phase dimension")
	f = one()
	f.snapshot.Facts[0].Candidates[0].Value.Quantity.Unit = "unit.volt"
	sealSnapshot(t, &f.snapshot)
	f.evaluation = evaluateMatterSnapshot(t, f.snapshot)
	recordProject(t, "reject-wrong-unit", stimulus+"/wrong unit", f, "wrong unit")
	f = one()
	f.snapshot.Facts[0].Candidates[0].Value.Quantity.Number = semreg.Decimal{Coefficient: "1001"}
	sealSnapshot(t, &f.snapshot)
	f.evaluation = evaluateMatterSnapshot(t, f.snapshot)
	recordProject(t, "reject-outside-evse-source-bounds", stimulus+"/outside EVSE source bounds", f, "outside EVSE source bounds")
	f = newMatterFixture(t, []semreg.FactCandidate{matterCandidate("candidate:matter:a", "l1", "32", -1), matterCandidate("candidate:matter:b", "l1", "33", -1)})
	recordProject(t, "reject-conflict", stimulus+"/conflict", f, "conflict")
	f = newMatterFixture(t, []semreg.FactCandidate{matterCandidate("candidate:matter:l1", "l1", "32", -1), matterCandidate("candidate:matter:l2", "l2", "33", -1)})
	recordProject(t, "reject-multiple-phase-keys", stimulus+"/multiple phase keys", f, "multiple phase keys")
}

func recordProject(t *testing.T, name, stimulus string, fixture matterFixture, mutation string) {
	t.Helper()
	got, err := Project(fixture.snapshot, fixture.evaluation)
	zero := reflect.DeepEqual(got, Result{})
	output := obj(kv{"result_is_zero", zero})
	if !zero {
		output = append(output, kv{"result", got})
	}
	projectionCase(t, name, stimulus, oracleSealedInput(fixture.snapshot, fixture.evaluation, kv{"call", "Project"}, kv{"variant", mutation}), oracleOutput(output, err))
}

func recordProjectionContributors(t *testing.T) {
	owner := []semreg.FactCandidate{
		matterCandidate("candidate:matter:current", "l1", "32", -1),
		matterFactOf("candidate:matter:limit:owner", "1", "evse.limit.configured_current", "evse.dimension.evse", "evse-1", "165", "unit.ampere"),
	}
	staleVoltage := matterFactOf("candidate:matter:voltage", "2", "evse.ac.voltage", "evse.dimension.phase", "l1", "2301", "unit.volt")
	staleVoltage.FreshnessPolicy.FreshForNS = "10"
	contributor := []semreg.FactCandidate{
		matterFactOf("candidate:matter:limit:contributor", "2", "evse.limit.configured_current", "evse.dimension.evse", "evse-1", "175", "unit.ampere"),
		staleVoltage,
	}
	stimulus := "TestProjectEligibilityReadsOnlyMappedKeysWithSeveralContributors"
	fixture := matterContributorFixture(t, owner, contributor)
	conflicts, stale := 0, 0
	for _, fact := range fixture.snapshot.Facts {
		if fact.Key.FactID == "evse.limit.configured_current" {
			conflicts += len(fact.Conflicts)
		}
	}
	for _, item := range fixture.evaluation.Facts {
		if item.CandidateID == "candidate:matter:voltage" && item.Freshness != semreg.FreshnessFresh {
			stale++
		}
	}
	got, err := Project(fixture.snapshot, fixture.evaluation)
	projectionCase(t, "contributors-unmapped-conflict-and-stale", stimulus,
		oracleSealedInput(fixture.snapshot, fixture.evaluation, kv{"call", "Project"}, kv{"sources", 2}),
		oracleOutput(obj(kv{"unmapped_conflicts", conflicts}, kv{"unmapped_stale_facts", stale}, kv{"result", got}), err))

	other := matterContributorFixture(t, owner, []semreg.FactCandidate{matterOnSource(matterCandidate("candidate:matter:current:contributor", "l1", "33", -1), "2")})
	mapped := 0
	for _, fact := range other.snapshot.Facts {
		if fact.Key.FactID == "evse.ac.current" {
			mapped += len(fact.Conflicts)
		}
	}
	recordContributor(t, "contributors-conflict-on-mapped-key", stimulus+"/conflict on the mapped key", other, obj(kv{"mapped_conflicts", mapped}))

	current := matterCandidate("candidate:matter:current", "l1", "32", -1)
	current.FreshnessPolicy.FreshForNS = "10"
	staleMapped := matterContributorFixture(t, []semreg.FactCandidate{current}, contributor)
	recordContributor(t, "contributors-stale-mapped-key", stimulus+"/stale mapped key", staleMapped, nil)

	unavailable := matterContributorFixture(t, owner, contributor)
	for i := range unavailable.evaluation.Facts {
		if unavailable.evaluation.Facts[i].CandidateID == "candidate:matter:current" {
			unavailable.evaluation.Facts[i].EffectiveAvailability = semreg.AvailabilityUnavailable
		}
	}
	sealEvaluation(t, &unavailable.evaluation)
	recordContributor(t, "contributors-unavailable-mapped-key", stimulus+"/unavailable mapped key", unavailable, nil)
}

func recordContributor(t *testing.T, name, stimulus string, fixture matterFixture, extra fields) {
	t.Helper()
	got, err := Project(fixture.snapshot, fixture.evaluation)
	zero := reflect.DeepEqual(got, Result{})
	output := append(fields{{"result_is_zero", zero}}, extra...)
	if !zero {
		output = append(output, kv{"result", got})
	}
	projectionCase(t, name, stimulus, oracleSealedInput(fixture.snapshot, fixture.evaluation, kv{"call", "Project"}, kv{"sources", 2}), oracleOutput(output, err))
}

func recordProjectionMappedKey(t *testing.T) {
	key := matterCandidate("candidate:matter:key", "l1", "32", -1).Key
	stimulus := "TestMappedKeyNamesPackVersionAndFact"
	projectionCase(t, "mapped-key-the-mapped-current", stimulus, obj(kv{"call", "mappedKey"}, kv{"key", key}), obj(kv{"mapped", mappedKey(key)}))
	for _, name := range []string{"fact", "pack", "version"} {
		other := key
		switch name {
		case "pack":
			other.PackID = "helianthus.pack.pv"
		case "version":
			other.PackVersion = "1.1.0"
		case "fact":
			other.FactID = "evse.ac.voltage"
		}
		projectionCase(t, "mapped-key-other-"+name, stimulus+"/"+name, obj(kv{"call", "mappedKey"}, kv{"key", other}), obj(kv{"mapped", mappedKey(other)}))
	}
	phase := "l2"
	other := key
	other.Dimensions = []semreg.Dimension{{ID: "evse.dimension.phase", Value: semreg.Value{Kind: semreg.ValueText, Text: &phase}}}
	projectionCase(t, "mapped-key-another-phase", stimulus, obj(kv{"call", "mappedKey"}, kv{"key", other}), obj(kv{"mapped", mappedKey(other)}))
}
