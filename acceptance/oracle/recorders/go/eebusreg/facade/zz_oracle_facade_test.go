package eebusfacade

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	spineapi "github.com/Project-Helianthus/helianthus-spine-go/api"
	spinemodel "github.com/Project-Helianthus/helianthus-spine-go/model"
)

// TestOracleFacade records the files of internal/eebusfacade that have an
// offline fixture in the tests of the pin: facade.go, runtime_snapshot_marshal.go,
// runtime_observation_reducer.go and output_node.go. The stimuli are the pin's
// own tests; no expectation is derived here.
func TestOracleFacade(t *testing.T) {
	t.Run("static-evidence", oracleRecordStaticEvidence)
	t.Run("snapshot-marshal", oracleRecordSnapshotMarshal)
	t.Run("observation-reducer", oracleRecordObservationReducer)
	t.Run("output-node", oracleRecordOutputNode)
}

type oracleCase struct {
	Format    string       `json:"format"`
	Component string       `json:"component"`
	Source    string       `json:"source"`
	Stimulus  string       `json:"stimulus"`
	Input     oracleInput  `json:"input"`
	Output    oracleOutput `json:"output"`
}

type oracleInput struct {
	Bytes      string         `json:"bytes"`
	Qualifiers map[string]any `json:"qualifiers"`
	Clock      map[string]any `json:"clock"`
	State      map[string]any `json:"state"`
}

type oracleOutput struct {
	SymbolsWritten []any          `json:"symbols_written"`
	Decisions      []any          `json:"decisions"`
	Cache          map[string]any `json:"cache"`
	Observations   []any          `json:"observations"`
	Counters       map[string]any `json:"counters"`
}

func oracleWrite(t *testing.T, group, name string, document oracleCase) {
	t.Helper()
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	document.Format = "helianthus-oracle-qv06-case/1"
	if document.Input.Qualifiers == nil {
		document.Input.Qualifiers = map[string]any{}
	}
	if document.Input.Clock == nil {
		document.Input.Clock = map[string]any{}
	}
	if document.Input.State == nil {
		document.Input.State = map[string]any{}
	}
	if document.Output.SymbolsWritten == nil {
		document.Output.SymbolsWritten = []any{}
	}
	if document.Output.Decisions == nil {
		document.Output.Decisions = []any{}
	}
	if document.Output.Cache == nil {
		document.Output.Cache = map[string]any{}
	}
	if document.Output.Observations == nil {
		document.Output.Observations = []any{}
	}
	if document.Output.Counters == nil {
		document.Output.Counters = map[string]any{}
	}
	data, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(directory, group, name+".json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(data, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

func oracleErr(err error) any {
	if err == nil {
		return nil
	}
	return map[string]any{"text": err.Error()}
}

func oracleStep(steps *[]any, call string, fields map[string]any) {
	record := map[string]any{"call": call}
	for key, value := range fields {
		record[key] = value
	}
	*steps = append(*steps, record)
}

func oracleJSON(t *testing.T, value any) json.RawMessage {
	t.Helper()
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	return data
}

func oracleRecordStaticEvidence(t *testing.T) {
	evidence := StaticEvidence()
	surface := ExpectedControlSurface()
	mutated := StaticEvidence()
	mutated.API.RequiredServiceReaders[0] = "mutated"
	mutated.API.ExcludedRuntimeOrMutators[0] = "mutated"
	next := StaticEvidence()
	callbacks := []any{}
	for _, signature := range serviceReaderCallbackSignatures() {
		callbacks = append(callbacks, map[string]any{"name": signature.Name, "inputs": signature.Inputs})
	}
	oracleWrite(t, "facade-go", "static-evidence-and-control-surface", oracleCase{
		Component: "internal/eebusfacade/facade.go (StaticEvidence, ExpectedControlSurface, serviceReaderCallbackSignatures, serviceReaderShapeMatches)",
		Source:    "internal/eebusfacade/facade.go",
		Stimulus:  "internal/eebusfacade/facade_test.go TestStaticEvidencePinsEEBusGoAPI, TestStaticEvidenceReturnsIndependentSlices, TestExpectedControlSurfaceIsStableAndSorted, TestRuntimeAndMutationMethodsAreExcludedFromApprovedReaders, TestServiceReaderShapeMatchesExpectedCallbacks",
		Input:     oracleInput{Qualifiers: map[string]any{"calls": []any{"StaticEvidence", "ExpectedControlSurface", "serviceReaderCallbackSignatures", "serviceReaderShapeMatches"}}},
		Output: oracleOutput{
			Observations: []any{
				map[string]any{"call": "StaticEvidence", "evidence": json.RawMessage(oracleJSON(t, evidence))},
				map[string]any{"call": "ExpectedControlSurface", "surface": json.RawMessage(oracleJSON(t, surface))},
				map[string]any{"call": "serviceReaderCallbackSignatures", "signatures": callbacks},
				map[string]any{"call": "serviceReaderShapeMatches", "result": serviceReaderShapeMatches()},
			},
			Decisions: []any{
				map[string]any{"call": "StaticEvidence/independent-slices", "required_service_readers_aliased": next.API.RequiredServiceReaders[0] == "mutated", "excluded_methods_aliased": next.API.ExcludedRuntimeOrMutators[0] == "mutated"},
			},
		},
	})
}

func oracleRecordSnapshotMarshal(t *testing.T) {
	steps := []any{}
	graph := snapshotMarshalFixtureGraph()
	zoned := snapshotMarshalFixtureTime.In(time.FixedZone("fixture", 3600))
	withIdentity, err := marshalRuntimeSnapshotWithIdentity(snapshotMarshalRuntimeID(), snapshotMarshalLocalSKI(), graph, zoned)
	record := map[string]any{"error": oracleErr(err), "bytes_utf8": string(withIdentity)}
	again, againErr := marshalRuntimeSnapshot(snapshotMarshalFixtureGraph(), snapshotMarshalFixtureTime)
	record["first_remote_identity_error"] = oracleErr(againErr)
	record["first_remote_identity_bytes_equal"] = string(again) == string(withIdentity)
	oracleStep(&steps, "marshalRuntimeSnapshotWithIdentity/synthetic-graph", record)

	base := func(remote string, mutate func(*runtimeGraphObservation)) runtimeGraphObservation {
		observation := runtimeGraphObservation{RuntimeID: snapshotMarshalRuntimeID(), LocalSKI: snapshotMarshalLocalSKI(), RemoteSKI: remote, Since: snapshotMarshalFixtureTime}
		mutate(&observation)
		return observation
	}
	visible := func(observation *runtimeGraphObservation) { observation.Visible = true }
	connected := func(observation *runtimeGraphObservation) {
		observation.SessionID, observation.SessionState = "session:a:1", "connected"
	}
	session := func(state string) func(*runtimeGraphObservation) {
		return func(observation *runtimeGraphObservation) {
			observation.SessionID, observation.SessionState, observation.Visible = "session:x:1", state, true
		}
	}
	trust := func(reason string) func(*runtimeGraphObservation) {
		return func(observation *runtimeGraphObservation) {
			connected(observation)
			observation.TrustDegradation = reason
		}
	}
	a, b := snapshotMarshalRemoteA(), snapshotMarshalRemoteB()
	statuses := []struct {
		name  string
		graph []runtimeGraphObservation
	}{
		{"nothing visible", []runtimeGraphObservation{base(a, func(*runtimeGraphObservation) {})}},
		{"visible only", []runtimeGraphObservation{base(a, visible)}},
		{"connected", []runtimeGraphObservation{base(a, connected)}},
		{"disconnected", []runtimeGraphObservation{base(a, session("disconnected"))}},
		{"session degraded", []runtimeGraphObservation{base(a, session("degraded"))}},
		{"connected wins over disconnected", []runtimeGraphObservation{base(a, session("disconnected")), base(b, connected)}},
		{"certificate unavailable", []runtimeGraphObservation{base(a, trust("certificate-unavailable"))}},
		{"denied trust after certificate", []runtimeGraphObservation{base(a, trust("certificate-unavailable")), base(b, trust("denied-trust"))}},
		{"certificate after denied trust", []runtimeGraphObservation{base(a, trust("denied-trust")), base(b, trust("certificate-unavailable"))}},
	}
	for _, item := range statuses {
		payload, err := marshalRuntimeSnapshotWithIdentity(snapshotMarshalRuntimeID(), snapshotMarshalLocalSKI(), item.graph, snapshotMarshalFixtureTime)
		record := map[string]any{"graph": item.name, "error": oracleErr(err)}
		if err == nil {
			var decoded runtimeSnapshotPayload
			if err := json.Unmarshal(payload, &decoded); err != nil {
				t.Fatal(err)
			}
			record["status_state"] = decoded.Status.State
			if decoded.Status.Degradation != nil {
				record["degradation_reason"] = decoded.Status.Degradation.Reason
				record["degradation_since_equals_capture_time"] = decoded.Status.Degradation.Since.Equal(snapshotMarshalFixtureTime)
			}
		}
		oracleStep(&steps, "marshalRuntimeSnapshotWithIdentity/status-derivation", record)
	}
	_, emptyErr := marshalRuntimeSnapshot(nil, snapshotMarshalFixtureTime)
	_, blankErr := marshalRuntimeSnapshotWithIdentity(" ", snapshotMarshalLocalSKI(), nil, snapshotMarshalFixtureTime)
	emptyPayload, emptyIdentityErr := marshalRuntimeSnapshotWithIdentity(snapshotMarshalRuntimeID(), snapshotMarshalLocalSKI(), nil, snapshotMarshalFixtureTime)
	arrays := map[string]any{}
	for _, field := range []string{`"pairing":[]`, `"services":[]`, `"sessions":[]`, `"devices":[]`, `"entities":[]`, `"features":[]`, `"use_cases":[]`, `"opaque":[]`} {
		arrays[field] = strings.Contains(string(emptyPayload), field)
	}
	oracleStep(&steps, "marshalRuntimeSnapshot/identity", map[string]any{
		"empty_graph_without_identity_error": oracleErr(emptyErr), "blank_runtime_identity_error": oracleErr(blankErr),
		"empty_graph_with_identity_error": oracleErr(emptyIdentityErr), "empty_graph_contains": arrays,
	})
	for _, item := range []struct {
		name   string
		device runtimeDeviceObservation
	}{
		{"missing ski", runtimeDeviceObservation{Address: "d1", Type: "HeatPump"}},
		{"missing address", runtimeDeviceObservation{SKI: snapshotMarshalRemoteA(), Type: "HeatPump"}},
		{"missing type", runtimeDeviceObservation{SKI: snapshotMarshalRemoteA(), Address: "d1"}},
	} {
		payload, entities, features, useCases := marshalRuntimeDevice(item.device)
		oracleStep(&steps, "marshalRuntimeDevice/incomplete", map[string]any{
			"device": item.name, "address": payload.Address, "entities_nil": entities == nil, "features_nil": features == nil, "use_cases_nil": useCases == nil,
		})
	}
	source := snapshotMarshalFixtureGraph()[0].Devices[0]
	source.SKI = snapshotMarshalRemoteA()
	payload, entities, features, useCases := marshalRuntimeDevice(source)
	source.Metadata["label"] = "changed"
	*source.Description = "changed"
	source.UseCases[0].Scenarios[0] = "changed"
	opaque := (*payload.Opaque)[0].Value.(map[string]any)
	number, isFloat := opaque["n"].(float64)
	oracleStep(&steps, "marshalRuntimeDevice/complete", map[string]any{
		"payload": json.RawMessage(oracleJSON(t, payload)), "entity_count": len(entities), "feature_count": len(features), "use_case_count": len(useCases),
		"ship_id_nil": payload.SHIPID == nil, "metadata_label_after_source_change": (*payload.Metadata)["label"], "description_after_source_change": *payload.Description,
		"scenario_after_source_change": useCases[0].Scenarios[0], "opaque_number_is_float64": isFloat, "opaque_number": number,
		"runtimeOptionalString/empty_is_nil": runtimeOptionalString("") == nil, "runtimeOptionalString/x": *runtimeOptionalString("x"),
	})
	oracleWrite(t, "runtime-snapshot-marshal-go", "marshal-synthetic-graph-status-and-device", oracleCase{
		Component: "internal/eebusfacade/runtime_snapshot_marshal.go (marshalRuntimeSnapshot, marshalRuntimeSnapshotWithIdentity, marshalRuntimeDevice, runtimeOptionalString)",
		Source:    "internal/eebusfacade/runtime_snapshot_marshal.go",
		Stimulus:  "internal/eebusfacade/runtime_snapshot_marshal_test.go (every test)",
		Input: oracleInput{
			Qualifiers: map[string]any{
				"graph": "snapshotMarshalFixtureGraph of the pin: two remotes (40-character repeated-digit identities), one device with one entity of each kind",
				"local_ski": snapshotMarshalLocalSKI(), "remote_a": snapshotMarshalRemoteA(), "remote_b": snapshotMarshalRemoteB(), "time_zone_offset_seconds": 3600,
			},
			Clock: map[string]any{"capture_time_utc": snapshotMarshalFixtureTime.Format(time.RFC3339)},
		},
		Output: oracleOutput{Decisions: steps},
	})
}

func oracleRecordObservationReducer(t *testing.T) {
	steps := []any{}
	source := runtimeGraphObservation{
		RuntimeID: " runtime:" + observationReducerLocalSKI() + " ", LocalSKI: " " + observationReducerLocalSKI(),
		RemoteSKI: observationReducerRemote("a") + " ", SessionID: " session:a:1 ", SessionState: " connected ",
		PairingState: " paired ", TrustDegradation: " denied-trust ", ShipID: " ship-a ", ServiceName: " Name ",
		ServiceIdentifier: " id ", ServiceBrand: " Brand ", ServiceType: " Type ", ServiceModel: " Model ",
		Since:      observationReducerFixtureTime.In(time.FixedZone("fixture", 7200)),
		ServiceIDs: []string{" service:b ", "service:a", "service:b"},
		Devices: []runtimeDeviceObservation{
			{ID: "device:b", Address: "d2", Type: "Generic"},
			{
				ID: " device:a ", SKI: " ski ", SHIPID: " ship ", Address: " d1 ", Type: " HeatPump ",
				UseCaseIDs: []string{"usecase:b", " usecase:a "},
				UseCases: []runtimeUseCaseObservation{
					{ID: "usecase:b", Name: "B", Scenarios: []string{" 2 ", "1"}},
					{ID: " usecase:a ", ContextAddress: " c ", Name: " A ", Actor: " actor "},
				},
				Entities: []runtimeEntityObservation{
					{ID: "entity:b", Features: []runtimeFeatureObservation{{ID: "feature:b", Role: "server"}, {ID: " feature:a ", Role: " client "}}},
					{ID: " entity:a ", DeviceAddress: " d1 ", EntityAddress: " [1] ", Type: " Appliance "},
				},
			},
			{ID: "device:a", Metadata: map[string]string{"label": "L"}},
		},
	}
	reducer := newRuntimeObservationReducer()
	replaceErr := reducer.Replace(source)
	oracleStep(&steps, "Replace+Snapshot/normalizes-observation", map[string]any{"error": oracleErr(replaceErr), "snapshot": json.RawMessage(oracleJSON(t, reducer.Snapshot()))})

	device := func(mutate func(*runtimeDeviceObservation)) func(*runtimeGraphObservation) {
		return func(observation *runtimeGraphObservation) {
			value := runtimeDeviceObservation{ID: "device:a"}
			mutate(&value)
			observation.Devices = []runtimeDeviceObservation{value}
		}
	}
	rejections := []struct {
		name   string
		mutate func(*runtimeGraphObservation)
	}{
		{"runtime id", func(observation *runtimeGraphObservation) { observation.RuntimeID = " " }},
		{"local ski", func(observation *runtimeGraphObservation) { observation.LocalSKI = "" }},
		{"remote ski", func(observation *runtimeGraphObservation) { observation.RemoteSKI = "" }},
		{"local ski format", func(observation *runtimeGraphObservation) { observation.LocalSKI = strings.Repeat("z", 40) }},
		{"remote ski format", func(observation *runtimeGraphObservation) { observation.RemoteSKI = strings.Repeat("a", 39) }},
		{"session state", func(observation *runtimeGraphObservation) { observation.SessionID, observation.SessionState = "s", "paused" }},
		{"session without id", func(observation *runtimeGraphObservation) { observation.SessionState = "connected" }},
		{"id without session", func(observation *runtimeGraphObservation) { observation.SessionID = "s" }},
		{"pairing state", func(observation *runtimeGraphObservation) { observation.PairingState = "pending" }},
		{"trust degradation", func(observation *runtimeGraphObservation) { observation.TrustDegradation = "expired" }},
		{"zero since", func(observation *runtimeGraphObservation) { observation.Since = time.Time{} }},
		{"blank service id", func(observation *runtimeGraphObservation) { observation.ServiceIDs = []string{" "} }},
		{"device id", device(func(value *runtimeDeviceObservation) { value.ID = " " })},
		{"blank use case id", device(func(value *runtimeDeviceObservation) { value.UseCaseIDs = []string{""} })},
		{"use case identity", device(func(value *runtimeDeviceObservation) { value.UseCases = []runtimeUseCaseObservation{{}} })},
		{"entity identity", device(func(value *runtimeDeviceObservation) { value.Entities = []runtimeEntityObservation{{}} })},
		{"opaque value", device(func(value *runtimeDeviceObservation) { value.Opaque = []runtimeOpaquePayload{{Value: func() {}}} })},
		{"feature identity", device(func(value *runtimeDeviceObservation) {
			value.Entities = []runtimeEntityObservation{{ID: "entity:a", Features: []runtimeFeatureObservation{{}}}}
		})},
		{"conflicting feature roles", device(func(value *runtimeDeviceObservation) {
			value.Entities = []runtimeEntityObservation{{ID: "entity:a", Features: []runtimeFeatureObservation{{ID: "feature:a", Role: "client"}, {ID: "feature:a", Role: "server"}}}}
		})},
	}
	for _, item := range rejections {
		reducer := newRuntimeObservationReducer()
		seedErr := reducer.Replace(observationReducerFixture(observationReducerRemote("a")))
		invalid := observationReducerFixture(observationReducerRemote("a"))
		invalid.ServiceIDs = []string{"service:changed"}
		item.mutate(&invalid)
		err := reducer.Replace(invalid)
		snapshot := reducer.Snapshot()
		oracleStep(&steps, "Replace/rejects-invalid-observation", map[string]any{
			"mutation": item.name, "seed_error": oracleErr(seedErr), "error": oracleErr(err),
			"last_known_good_retained": len(snapshot) == 1 && len(snapshot[0].ServiceIDs) == 0 && len(snapshot[0].Devices) == 0, "snapshot_size": len(snapshot),
		})
	}
	{
		reducer := newRuntimeObservationReducer()
		seedErr := reducer.Replace(observationReducerFixture(observationReducerRemote("b")))
		changedRuntime := observationReducerFixture(observationReducerRemote("a"))
		changedRuntime.RuntimeID = "runtime:other"
		runtimeErr := reducer.Replace(changedRuntime)
		changedLocal := observationReducerFixture(observationReducerRemote("a"))
		changedLocal.LocalSKI = observationReducerRemote("2")
		localErr := reducer.Replace(changedLocal)
		sameErr := reducer.Replace(observationReducerFixture(observationReducerRemote("a")))
		remotes := []any{}
		for _, item := range reducer.Snapshot() {
			remotes = append(remotes, item.RemoteSKI)
		}
		oracleStep(&steps, "Replace/pins-runtime-and-local-identity", map[string]any{
			"seed_error": oracleErr(seedErr), "changed_runtime_error": oracleErr(runtimeErr), "changed_local_error": oracleErr(localErr), "same_identities_error": oracleErr(sameErr),
			"snapshot_remote_order": remotes,
		})
	}
	{
		sourceObservation := observationReducerFixture(observationReducerRemote("a"))
		sourceObservation.ServiceIDs = []string{"service:a"}
		sourceObservation.Devices = []runtimeDeviceObservation{{
			ID: "device:a", Description: observationReducerString("D"), Metadata: map[string]string{"label": "L"},
			Opaque:     []runtimeOpaquePayload{{Path: "/p", Source: "s", Value: map[string]any{"k": "v"}}},
			UseCaseIDs: []string{"usecase:a"},
			UseCases:   []runtimeUseCaseObservation{{ID: "usecase:a", Scenarios: []string{"1"}, Version: observationReducerString("1")}},
			Entities: []runtimeEntityObservation{{ID: "entity:a", Description: observationReducerString("E"),
				Features: []runtimeFeatureObservation{{ID: "feature:a", Description: observationReducerString("F")}}}},
		}}
		reducer := newRuntimeObservationReducer()
		replaceErr := reducer.Replace(sourceObservation)
		*sourceObservation.Devices[0].Description = "source changed"
		sourceObservation.Devices[0].Metadata["label"] = "source changed"
		first := reducer.Snapshot()
		deviceValue := &first[0].Devices[0]
		first[0].ServiceIDs[0] = "changed"
		*deviceValue.Description = "changed"
		deviceValue.Metadata["label"] = "changed"
		deviceValue.Opaque[0].Value.(map[string]any)["k"] = "changed"
		deviceValue.UseCaseIDs[0] = "changed"
		deviceValue.UseCases[0].Scenarios[0] = "changed"
		*deviceValue.UseCases[0].Version = "changed"
		*deviceValue.Entities[0].Description = "changed"
		*deviceValue.Entities[0].Features[0].Description = "changed"
		second := reducer.Snapshot()[0]
		again := second.Devices[0]
		oracleStep(&steps, "Snapshot/is-detached", map[string]any{
			"replace_error": oracleErr(replaceErr), "service_id": second.ServiceIDs[0], "description": *again.Description, "metadata_label": again.Metadata["label"],
			"opaque_value": again.Opaque[0].Value.(map[string]any)["k"], "use_case_id": again.UseCaseIDs[0], "scenario": again.UseCases[0].Scenarios[0],
			"use_case_version": *again.UseCases[0].Version, "entity_description": *again.Entities[0].Description, "feature_description": *again.Entities[0].Features[0].Description,
		})
	}
	{
		left := []runtimeDeviceObservation{{
			ID: "device:a", Type: "Old", Metadata: map[string]string{"left": "1", "shared": "left"},
			Opaque:     []runtimeOpaquePayload{{Path: "/p", Source: "s", Value: "v"}},
			UseCaseIDs: []string{"usecase:a"},
			UseCases:   []runtimeUseCaseObservation{{ID: "usecase:a", Name: "A", Scenarios: []string{"2"}}},
			Entities: []runtimeEntityObservation{{ID: "entity:a", Type: "Old", Features: []runtimeFeatureObservation{{ID: "feature:a", Role: "server"}}}},
		}}
		right := []runtimeDeviceObservation{
			{
				ID: "device:a", Type: "New", Metadata: map[string]string{"shared": "right"},
				Opaque: []runtimeOpaquePayload{
					{Path: "/p", Source: "s", Value: "v"}, {Path: "/q", Source: "s", Value: "v"}, {Path: "/p", Source: "t", Value: "v"}, {Path: "/p", Source: "s", Value: "w"},
				},
				UseCaseIDs: []string{"usecase:b"},
				UseCases:   []runtimeUseCaseObservation{{ID: "usecase:a", Scenarios: []string{"1", " "}}},
				Entities: []runtimeEntityObservation{{ID: "entity:a", Type: "New", Features: []runtimeFeatureObservation{{ID: "feature:a", Type: "Measurement"}}}},
			},
			{ID: "device:b"},
		}
		merged, mergeErr := mergeRuntimeDeviceCollections(left, right)
		exact, exactErr := exactRuntimeDeviceCollection(right)
		opaque := []any{}
		if len(merged) > 0 {
			for _, value := range merged[0].Opaque {
				encoded, _ := json.Marshal(value.Value)
				opaque = append(opaque, value.Path+"|"+value.Source+"|"+string(encoded))
			}
		}
		record := map[string]any{"merge_error": oracleErr(mergeErr), "merged": json.RawMessage(oracleJSON(t, merged)), "merged_opaque_order": opaque, "exact_error": oracleErr(exactErr), "exact_device_count": len(exact)}
		if len(exact) > 0 {
			record["exact_first_device_opaque_count"] = len(exact[0].Opaque)
		}
		oracleStep(&steps, "mergeRuntimeDeviceCollections", record)
	}
	oracleWrite(t, "runtime-observation-reducer-go", "replace-snapshot-and-merge", oracleCase{
		Component: "internal/eebusfacade/runtime_observation_reducer.go (newRuntimeObservationReducer, Replace, Snapshot, mergeRuntimeDeviceCollections, exactRuntimeDeviceCollection)",
		Source:    "internal/eebusfacade/runtime_observation_reducer.go",
		Stimulus:  "internal/eebusfacade/runtime_observation_reducer_test.go TestRuntimeObservationReducerNormalizesObservation, TestRuntimeObservationReducerRejectsInvalidObservations, TestRuntimeObservationReducerPinsRuntimeAndLocalIdentity, TestRuntimeObservationReducerSnapshotIsDetached, TestRuntimeObservationReducerMergesDeviceCollections",
		Input: oracleInput{
			Qualifiers: map[string]any{"local_ski": observationReducerLocalSKI(), "remote_digits": []any{"a", "b"}},
			Clock:      map[string]any{"since_utc": observationReducerFixtureTime.Format(time.RFC3339)},
		},
		Output: oracleOutput{Decisions: steps},
	})
}

func oracleRecordOutputNode(t *testing.T) {
	steps := []any{}
	run := func(name string, scenario func(t *testing.T) map[string]any) {
		t.Run(name, func(t *testing.T) {
			oracleStep(&steps, name, scenario(t))
		})
	}
	run("counts-follow-the-service", func(t *testing.T) map[string]any {
		service, concrete := newOutputNodeRuntime(t)
		node := &OutputNode{service: concrete, byLetter: map[string]spineapi.EntityLocalInterface{}}
		unready := map[string]any{"advertisements": node.AdvertisementCount(), "services": node.ServiceCount(), "device_type": node.DeviceType()}
		setupErr := service.Setup()
		return map[string]any{
			"unready": unready, "setup_error": oracleErr(setupErr),
			"ready":                  map[string]any{"advertisements": node.AdvertisementCount(), "services": node.ServiceCount(), "device_type": node.DeviceType()},
			"has_cem_entity":         outputNodeHasEntity(concrete, spinemodel.EntityTypeTypeCEM),
			"has_inverter_entity":    outputNodeHasEntity(concrete, spinemodel.EntityTypeTypeInverter),
		}
	})
	run("uses-the-runtime-service", func(t *testing.T) map[string]any {
		service, concrete := newOutputNodeRuntime(t)
		_, beforeErr := OpenOutputNode()
		setupErr := service.Setup()
		node, openErr := OpenOutputNode()
		record := map[string]any{"open_before_prepare_error": oracleErr(beforeErr), "setup_error": oracleErr(setupErr), "open_after_prepare_error": oracleErr(openErr)}
		if node == nil {
			return record
		}
		record["node_is_runtime_service"] = node.service == concrete
		record["AddEntity_inverter_error"] = oracleErr(node.AddEntity("Inverter", "na", ""))
		record["AddEntity_pv_string_error"] = oracleErr(node.AddEntity("PV String", "nb", "na"))
		record["AddServerFeature_error"] = oracleErr(node.AddServerFeature("na", "measurement"))
		record["service_has_inverter"] = outputNodeHasEntity(concrete, spinemodel.EntityTypeTypeInverter)
		record["service_has_pv_string"] = outputNodeHasEntity(concrete, spinemodel.EntityTypeTypePVString)
		record["NestedUnder_nb_na"] = node.NestedUnder("nb", "na")
		record["ObservedServerFeatures"] = node.ObservedServerFeatures("na")
		record["EntityTypes"] = node.EntityTypes()
		record["counts"] = map[string]any{"advertisements": node.AdvertisementCount(), "services": node.ServiceCount(), "device_type": node.DeviceType()}
		releaseOutputService(service)
		_, afterErr := OpenOutputNode()
		record["open_after_release_error"] = oracleErr(afterErr)
		return record
	})
	run("failed-attach-leaves-no-feature", func(t *testing.T) map[string]any {
		service, _ := newOutputNodeRuntime(t)
		setupErr := service.Setup()
		node, openErr := OpenOutputNode()
		if openErr != nil {
			t.Fatal(openErr)
		}
		addErr := node.AddEntity("Inverter", "na", "")
		original := attachOutputServerFeature
		attachOutputServerFeature = func(spineapi.EntityLocalInterface, spinemodel.FeatureTypeType) error { return errOutputNode }
		failedErr := node.AddServerFeature("na", "measurement")
		failedObserved := node.ObservedServerFeatures("na")
		failedListed := node.ServerFeatures("na")
		attachOutputServerFeature = original
		laterErr := node.AddServerFeature("na", "measurement")
		laterListed := node.ServerFeatures("na")
		repeatErr := node.AddServerFeature("na", "measurement")
		return map[string]any{
			"setup_error": oracleErr(setupErr), "AddEntity_error": oracleErr(addErr), "failed_attach_error": oracleErr(failedErr), "observed_after_failed_attach": nonNil(failedObserved),
			"listed_after_failed_attach": nonNil(failedListed), "later_attach_error": oracleErr(laterErr), "listed_after_later_attach": laterListed,
			"repeat_attach_error": oracleErr(repeatErr), "observed_after_repeat": node.ObservedServerFeatures("na"),
		}
	})
	run("adds-all-features-or-none", func(t *testing.T) map[string]any {
		service, _ := newOutputNodeRuntime(t)
		setupErr := service.Setup()
		node, openErr := OpenOutputNode()
		if openErr != nil {
			t.Fatal(openErr)
		}
		addErr := node.AddEntity("EVSE", "na", "")
		_, missingEntityErr := node.AddServerFeatures("nb", []string{"measurement"})
		original := attachOutputServerFeature
		RejectOutputServerFeatureForTest(t, "electrical connection")
		rejected, rejectedErr := node.AddServerFeatures("na", []string{"measurement", "electrical connection"})
		afterRejected := node.ObservedServerFeatures("na")
		unknown, unknownErr := node.AddServerFeatures("na", []string{"device diagnosis", "unknown"})
		afterUnknown := node.ObservedServerFeatures("na")
		attachOutputServerFeature = original
		_, firstErr := node.AddServerFeatures("na", []string{"measurement", "electrical connection"})
		_, secondErr := node.AddServerFeatures("na", []string{"measurement", "load control"})
		return map[string]any{
			"setup_error": oracleErr(setupErr), "AddEntity_error": oracleErr(addErr), "batch_on_missing_entity_error": oracleErr(missingEntityErr),
			"rejected_feature": rejected, "rejected_error": oracleErr(rejectedErr), "observed_after_rejected_batch": nonNil(afterRejected),
			"unknown_feature": unknown, "unknown_error": oracleErr(unknownErr), "observed_after_unknown_batch": nonNil(afterUnknown),
			"accepted_batch_errors": []any{oracleErr(firstErr), oracleErr(secondErr)}, "ServerFeatures": node.ServerFeatures("na"), "observed_count": len(node.ObservedServerFeatures("na")),
		}
	})
	run("entity-address-follows-the-letter", func(t *testing.T) map[string]any {
		addresses := func(order []string) map[string]any {
			service, _ := newOutputNodeRuntime(t)
			if err := service.Setup(); err != nil {
				t.Fatal(err)
			}
			node, err := OpenOutputNode()
			if err != nil {
				t.Fatal(err)
			}
			for _, letter := range order {
				if err := node.AddEntity("Inverter", letter, ""); err != nil {
					t.Fatal(err)
				}
			}
			childErr := node.AddEntity("PV String", "c", "b")
			found := map[string]any{"pv_string_error": oracleErr(childErr)}
			for _, letter := range []string{"a", "b", "c"} {
				found[letter] = fmt.Sprint(node.byLetter[letter].Address().Entity)
			}
			return found
		}
		first := addresses([]string{"a", "b"})
		second := addresses([]string{"b", "a"})
		number, ok := letterEntityNumber("abcdefg")
		return map[string]any{
			"apply_order_a_b": first, "apply_order_b_a": second, "orders_equal": reflect.DeepEqual(first, second), "overlong_letter_number": number, "overlong_letter_accepted": ok,
		}
	})
	oracleWrite(t, "output-node-go", "output-node-on-the-runtime-service", oracleCase{
		Component: "internal/eebusfacade/output_node.go (OutputNode, OpenOutputNode, adoptOutputService, releaseOutputService, AddEntity, AddServerFeature, AddServerFeatures, letterEntityNumber)",
		Source:    "internal/eebusfacade/output_node.go",
		Stimulus:  "internal/eebusfacade/output_node_test.go TestOutputNodeCountsFollowTheService, TestOutputNodeUsesRuntimeService, TestOutputNodeFailedAttachLeavesNoFeature, TestOutputNodeAddsAllFeaturesOrNone, TestOutputNodeEntityAddressFollowsLetter",
		Input: oracleInput{Qualifiers: map[string]any{
			"service": "newOutputNodeRuntime of the pin: a generated certificate, interface fixture-interface, port 4711; Setup only, nothing listens or announces",
			"letters": []any{"na", "nb", "a", "b", "c"}, "features": []any{"measurement", "electrical connection", "device diagnosis", "load control", "unknown"},
		}},
		Output: oracleOutput{Decisions: steps},
	})
}

func nonNil(values []string) []string {
	if values == nil {
		return []string{}
	}
	return values
}
