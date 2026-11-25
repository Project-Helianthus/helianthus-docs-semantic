package feedv1

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"
)

const (
	feedSourceServer = "matter/feedv1/server.go"
	feedSourceClient = "matter/feedv1/client.go"
	feedSourceSchema = "matter/feedv1/contract.go"
	feedSchemaPath   = "docs/schemas/matter-binding-feed-v1.schema.json"
	feedGoldenPath   = "cmd/gateway/testdata/characterization/consumers/matter_feed.json"
)

// The intent deadline of the pin's tests is the wall clock plus one minute. The recorder fixes it so the input is a value.
var (
	deadlineFuture = time.Date(2100, 1, 1, 0, 0, 0, 0, time.UTC)
	deadlinePast   = time.Date(2000, 1, 1, 0, 0, 0, 0, time.UTC)
)

func fixedIntent(snapshot Snapshot) Intent {
	intent := validIntent(snapshot)
	intent.Deadline = deadlineFuture
	return intent
}

func fileDigest(t *testing.T, path string) fields {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return fields{{"length", len(raw)}, {"sha256", fmt.Sprintf("%x", sha256.Sum256(raw))}}
}

// goldenReference names the item 5 golden of the matter feed by the entry that lists it. The golden bytes are not copied.
func goldenReference(t *testing.T) fields {
	t.Helper()
	return fields{
		{"index_entry", "current/gateway-goldens.json"},
		{"path", feedGoldenPath},
		{"sha256", fileDigest(t, "../../"+feedGoldenPath)[1].V},
		{"relation", "the gateway-level capture of this snapshot wire contract, checked by its own test; it is not an output of this case and is not copied"},
	}
}

type step struct {
	Name   string
	Method string
	Path   string
	Body   any
	State  string
}

func execute(t *testing.T, server http.Handler, fake *fakeProvider, steps []step, states map[string]Snapshot) []fields {
	t.Helper()
	var out []fields
	for _, item := range steps {
		if item.State != "" {
			fake.mu.Lock()
			fake.snapshot = states[item.State]
			fake.mu.Unlock()
		}
		response := request(t, server, item.Method, item.Path, item.Body)
		fake.mu.Lock()
		captures, invokes := fake.captures, fake.invokes
		fake.mu.Unlock()
		out = append(out, fields{{"step", item.Name}, {"status", response.Code}, {"content_type", response.Header().Get("Content-Type")}, {"body", rawBody(response.Body.Bytes())}, {"captures", captures}, {"invokes", invokes}})
	}
	return out
}

func rawBody(body []byte) any {
	if json.Valid(body) {
		return json.RawMessage(bytes.Clone(body))
	}
	return string(body)
}

func describeSteps(steps []step) []fields {
	var out []fields
	for _, item := range steps {
		entry := fields{{"step", item.Name}, {"method", item.Method}, {"path", item.Path}}
		if item.State != "" {
			entry = append(entry, kv{"provider_state_before", item.State})
		}
		if item.Body != nil {
			entry = append(entry, kv{"body", item.Body})
		}
		out = append(out, entry)
	}
	return out
}

func TestOracleFeedV1(t *testing.T) {
	recordLifecycle(t)
	recordDetachment(t)
	recordConcurrentCapture(t)
	recordClientWire(t)
	recordClientResync(t)
	recordSchemaMembers(t)
	recordCorpus(t)
	recordGeneration(t)
}

func recordLifecycle(t *testing.T) {
	states := map[string]Snapshot{
		"current-with-operation": validSnapshot(t, ResourceCurrent, true),
		"withdrawn":              validSnapshot(t, ResourceWithdrawn, false),
		"unavailable":            validSnapshot(t, ResourceUnavailable, false),
	}
	fake := &fakeProvider{snapshot: states["current-with-operation"]}
	server, err := New(fake, Options{InstanceID: "feed-a", ReplayLimit: 1})
	if err != nil {
		t.Fatal(err)
	}
	intent := fixedIntent(states["current-with-operation"])
	steps := []step{
		{"first snapshot", http.MethodGet, "/v1/snapshot", nil, ""},
		{"second snapshot with no change", http.MethodGet, "/v1/snapshot", nil, ""},
		{"changes from cursor 1 with no change", http.MethodGet, "/v1/changes?cursor=feed-a:1", nil, ""},
		{"changes from cursor 1 after withdrawal", http.MethodGet, "/v1/changes?cursor=feed-a:1", nil, "withdrawn"},
		{"changes from cursor 2 after unavailable", http.MethodGet, "/v1/changes?cursor=feed-a:2", nil, "unavailable"},
		{"changes from cursor 1 after replay exhaustion", http.MethodGet, "/v1/changes?cursor=feed-a:1", nil, ""},
	}
	out := execute(t, server, fake, steps, states)
	restarted, err := New(fake, Options{InstanceID: "feed-b", ReplayLimit: 2})
	if err != nil {
		t.Fatal(err)
	}
	restartSteps := []step{{"restarted server, cursor of the first instance", http.MethodGet, "/v1/changes?cursor=feed-a:2", nil, ""}}
	out = append(out, execute(t, restarted, fake, restartSteps, states)...)
	invokeSteps := []step{
		{"invoke without principal", http.MethodPost, "/v1/invoke", intent, "current-with-operation"},
		{"invoke", http.MethodPost, "/v1/invoke", intent, ""},
	}
	out = append(out, execute(t, server, fake, invokeSteps, states)...)
	fake.mu.Lock()
	fake.reject = true
	fake.mu.Unlock()
	rejectSteps := []step{{"invoke with the provider rejecting", http.MethodPost, "/v1/invoke", intent, ""}}
	out = append(out, execute(t, server, fake, rejectSteps, states)...)
	all := append(append(append(append([]step{}, steps...), restartSteps...), invokeSteps...), rejectSteps...)
	oracleCase(t, "server", "lifecycle-and-admission", feedSourceServer, "matter/feedv1/server_test.go", "TestStandaloneConsumerLifecycleAndAdmission",
		obj(kv{"server", obj(kv{"instance_id", "feed-a"}, kv{"replay_limit", 1})}, kv{"restarted_server", obj(kv{"instance_id", "feed-b"}, kv{"replay_limit", 2})},
			kv{"provider_snapshots", states}, kv{"intent", intent}, kv{"intent_deadline_note", "fixed by the recorder; the pin's test uses the wall clock plus one minute"},
			kv{"provider_rejects_from", "invoke with the provider rejecting"}, kv{"steps", describeSteps(all)}),
		obj(kv{"responses", out}, kv{"golden", goldenReference(t)}))
}

func recordDetachment(t *testing.T) {
	snapshot := validSnapshot(t, ResourceCurrent, true)
	fake := &fakeProvider{snapshot: snapshot}
	server, err := New(fake, Options{InstanceID: "feed-c", ReplayLimit: 2})
	if err != nil {
		t.Fatal(err)
	}
	intent := fixedIntent(snapshot)
	expired := intent
	expired.Deadline = deadlinePast
	tooLong := intent
	tooLong.IdempotencyKey = strings.Repeat("a", 257)
	injection := map[string]any{"asset_id": "asset:test", "route": "native"}
	steps := []step{
		{"route injection", http.MethodPost, "/v1/invoke", injection, ""},
		{"expired deadline", http.MethodPost, "/v1/invoke", expired, ""},
		{"idempotency key of 257 characters", http.MethodPost, "/v1/invoke", tooLong, ""},
		{"valid intent", http.MethodPost, "/v1/invoke", intent, ""},
	}
	out := execute(t, server, fake, steps, nil)
	mutated := intent
	mutated.Arguments = append([]byte(nil), intent.Arguments...)
	mutated.Arguments[2] = 'X'
	fake.mu.Lock()
	stored := append([]byte(nil), fake.last.Intent.Arguments...)
	fake.mu.Unlock()
	oracleCase(t, "server", "detachment-and-strict-rejection", feedSourceServer, "matter/feedv1/server_test.go", "TestInputDetachmentAndStrictRejectionHaveNoInvoke",
		obj(kv{"server", obj(kv{"instance_id", "feed-c"}, kv{"replay_limit", 2})}, kv{"provider_snapshot", snapshot}, kv{"intent", intent}, kv{"expired_deadline", deadlinePast},
			kv{"intent_deadline_note", "fixed by the recorder; the pin's test uses the wall clock plus or minus its offset"}, kv{"steps", describeSteps(steps)},
			kv{"after_valid_intent", "the first argument byte after the opening brace and quote is replaced by X in the caller's copy"}),
		obj(kv{"responses", out}, kv{"provider_arguments_after_caller_mutation", string(stored)}, kv{"provider_arguments_contain_X", bytes.Contains(stored, []byte("X"))},
			kv{"caller_arguments_after_mutation", string(mutated.Arguments)},
			kv{"captured_operation_claim_unchanged", fake.snapshot.Operations[0].Claim == validSnapshot(t, ResourceCurrent, true).Operations[0].Claim}))
}

func recordConcurrentCapture(t *testing.T) {
	fake := &fakeProvider{snapshot: validSnapshot(t, ResourceCurrent, false)}
	server, err := New(fake, Options{InstanceID: "feed-race", ReplayLimit: 2})
	if err != nil {
		t.Fatal(err)
	}
	var group sync.WaitGroup
	statuses := make([]int, 32)
	bodies := make([][]byte, 32)
	for i := 0; i < 32; i++ {
		group.Add(1)
		go func(i int) {
			defer group.Done()
			got := request(t, server, http.MethodGet, "/v1/snapshot", nil)
			statuses[i], bodies[i] = got.Code, got.Body.Bytes()
		}(i)
	}
	group.Wait()
	identical := true
	for _, body := range bodies {
		identical = identical && bytes.Equal(body, bodies[0])
	}
	counts := map[int]int{}
	for _, status := range statuses {
		counts[status]++
	}
	changes := request(t, server, http.MethodGet, "/v1/changes?cursor=feed-race:1", nil)
	oracleCase(t, "server", "concurrent-capture-keeps-one-cursor", feedSourceServer, "matter/feedv1/server_test.go", "TestConcurrentCaptureKeepsOneCursor",
		obj(kv{"server", obj(kv{"instance_id", "feed-race"}, kv{"replay_limit", 2})}, kv{"provider_snapshot", fake.snapshot},
			kv{"steps", []fields{{{"step", "32 concurrent snapshot requests"}, {"method", http.MethodGet}, {"path", "/v1/snapshot"}}, {{"step", "changes from cursor 1"}, {"method", http.MethodGet}, {"path", "/v1/changes?cursor=feed-race:1"}}}}),
		obj(kv{"snapshot_status_counts", counts}, kv{"snapshot_bodies_identical", identical}, kv{"snapshot_body", rawBody(bodies[0])},
			kv{"changes", obj(kv{"status", changes.Code}, kv{"content_type", changes.Header().Get("Content-Type")}, kv{"body", rawBody(changes.Body.Bytes())})},
			kv{"golden", goldenReference(t)}))
}

func recordClientWire(t *testing.T) {
	fake := &fakeProvider{snapshot: validSnapshot(t, ResourceCurrent, false)}
	server, err := New(fake, Options{InstanceID: "feed-client", ReplayLimit: 2})
	if err != nil {
		t.Fatal(err)
	}
	httpServer := httptest.NewServer(server)
	defer httpServer.Close()
	client := Client{BaseURL: httpServer.URL, HTTPClient: httpServer.Client()}
	first, firstErr := client.Snapshot(context.Background())
	changes, changesErr := client.Changes(context.Background(), first.Cursor)
	oracleCase(t, "client", "public-wire-contract", feedSourceClient, "matter/feedv1/server_test.go", "TestStandaloneClientUsesOnlyPublicWireContract",
		obj(kv{"server", obj(kv{"instance_id", "feed-client"}, kv{"replay_limit", 2}, kv{"listener", "loopback HTTP listener, address not recorded"})}, kv{"provider_snapshot", fake.snapshot},
			kv{"calls", []string{"Client.Snapshot()", "Client.Changes(cursor of the snapshot)"}}),
		obj(kv{"snapshot", obj(kv{"response", first}, kv{"error", oracleError(firstErr)})}, kv{"changes", obj(kv{"response", changes}, kv{"error", oracleError(changesErr)})}, kv{"golden", goldenReference(t)}))
}

func recordClientResync(t *testing.T) {
	states := map[string]Snapshot{
		"current":     validSnapshot(t, ResourceCurrent, false),
		"withdrawn":   validSnapshot(t, ResourceWithdrawn, false),
		"unavailable": validSnapshot(t, ResourceUnavailable, false),
	}
	fake := &fakeProvider{snapshot: states["current"]}
	server, err := New(fake, Options{InstanceID: "feed-resync", ReplayLimit: 1})
	if err != nil {
		t.Fatal(err)
	}
	httpServer := httptest.NewServer(server)
	defer httpServer.Close()
	client := Client{BaseURL: httpServer.URL, HTTPClient: httpServer.Client()}
	var observed []fields
	record := func(name string, response any, err error) {
		observed = append(observed, fields{{"call", name}, {"response", response}, {"error", oracleError(err)}})
	}
	foreign, err := client.Changes(context.Background(), Cursor{Instance: "other-process", Sequence: 1})
	record("Changes(other-process:1)", foreign, err)
	ahead, err := client.Changes(context.Background(), Cursor{Instance: "feed-resync", Sequence: 99})
	record("Changes(feed-resync:99)", ahead, err)
	first, err := client.Snapshot(context.Background())
	record("Snapshot()", first, err)
	set := func(name string) {
		fake.mu.Lock()
		fake.snapshot = states[name]
		fake.mu.Unlock()
	}
	set("withdrawn")
	second, err := client.Snapshot(context.Background())
	record("Snapshot() after the provider withdrew the resource", second, err)
	set("unavailable")
	third, err := client.Snapshot(context.Background())
	record("Snapshot() after the provider made the resource unavailable", third, err)
	expired, err := client.Changes(context.Background(), first.Cursor)
	record("Changes(cursor of the first snapshot)", expired, err)
	resynced, err := client.Snapshot(context.Background())
	record("Snapshot() after the resync", resynced, err)
	oracleCase(t, "client", "typed-resync-foreign-ahead-expired", feedSourceClient, "matter/feedv1/server_test.go", "TestStandaloneClientReturnsTypedResyncForForeignAheadAndExpiredCursors",
		obj(kv{"server", obj(kv{"instance_id", "feed-resync"}, kv{"replay_limit", 1}, kv{"listener", "loopback HTTP listener, address not recorded"})}, kv{"provider_snapshots", states},
			kv{"calls", []string{"Changes(other-process:1)", "Changes(feed-resync:99)", "Snapshot()", "provider state withdrawn", "Snapshot()", "provider state unavailable", "Snapshot()", "Changes(cursor of the first snapshot)", "Snapshot()"}}),
		obj(kv{"observations", observed}))
}

func schemaFile(t *testing.T) (map[string]any, fields) {
	t.Helper()
	raw, err := os.ReadFile("../../" + feedSchemaPath)
	if err != nil {
		t.Fatal(err)
	}
	var schema map[string]any
	if err := json.Unmarshal(raw, &schema); err != nil {
		t.Fatal(err)
	}
	return schema, fields{{"path", feedSchemaPath}, {"length", len(raw)}, {"sha256", fmt.Sprintf("%x", sha256.Sum256(raw))}}
}

func mapOf(value any) map[string]any {
	result, _ := value.(map[string]any)
	return result
}

func recordSchemaMembers(t *testing.T) {
	schema, reference := schemaFile(t)
	definitions := mapOf(schema["$defs"])
	members := []string{"cursor", "target", "fence", "resource", "operationClaim", "operation", "snapshot", "snapshotResponse", "changesResponse", "intent", "execution"}
	var objects []fields
	for _, name := range members {
		definition := mapOf(definitions[name])
		properties := mapOf(definition["properties"])
		objects = append(objects, fields{{"definition", name}, {"additional_properties", definition["additionalProperties"]}, {"properties", oracleKeys(properties)}})
	}
	intentProperties := mapOf(mapOf(definitions["intent"])["properties"])
	forbidden := fields{}
	for _, name := range []string{"principal", "route", "native_route", "endpoint"} {
		_, present := intentProperties[name]
		forbidden = append(forbidden, kv{name, present})
	}
	oracleCase(t, "schema", "closed-objects-and-wire-members", feedSourceSchema, "matter/feedv1/schema_test.go", "TestSchemaKeepsPublicObjectsClosedAndMatchesWireMembers",
		obj(kv{"schema_file", reference}, kv{"definitions_inspected", members}, kv{"intent_members_probed", []string{"principal", "route", "native_route", "endpoint"}}),
		obj(kv{"definitions", oracleKeys(definitions)}, kv{"objects", objects}, kv{"intent_forbidden_member_present", forbidden}))
}

func schemaVerdict(root map[string]any, value any) fields {
	err := validateFeedSchema(root, value)
	if err == nil {
		return fields{{"accepted", true}, {"error", nil}}
	}
	return fields{{"accepted", false}, {"error", err.Error()}}
}

func recordCorpus(t *testing.T) {
	schema, reference := schemaFile(t)
	snapshot := validSnapshot(t, ResourceCurrent, true)
	intent := fixedIntent(snapshot)
	execution := Execution{Contract: Contract, ACK: "ACKNOWLEDGED", Readback: json.RawMessage(`{"value":1}`), Outcome: json.RawMessage(`{"state":"completed"}`)}
	cursor := Cursor{Instance: "feed-schema", Sequence: 1}
	withdrawn := validSnapshot(t, ResourceWithdrawn, false)
	withdrawn.Resources[0].LastFence = &Fence{
		SnapshotID: snapshot.Resources[0].SnapshotID, Revisions: snapshot.Resources[0].Revisions, BindingID: snapshot.Resources[0].BindingID,
		SourceEpoch: snapshot.Resources[0].SourceEpoch, DriverGeneration: snapshot.Resources[0].DriverGeneration,
	}
	if err := withdrawn.Validate(); err != nil {
		t.Fatal(err)
	}
	quarantined := validSnapshot(t, ResourceQuarantined, false)
	unavailable := validSnapshot(t, ResourceUnavailable, false)
	valid := map[string]any{
		"snapshot":    SnapshotResponse{Contract: Contract, Cursor: cursor, Snapshot: snapshot},
		"changes":     ChangesResponse{Contract: Contract, Cursor: cursor, Changes: []SnapshotResponse{{Contract: Contract, Cursor: cursor, Snapshot: snapshot}}},
		"resync":      ChangesResponse{Contract: Contract, Cursor: cursor, ResyncRequired: true, Changes: []SnapshotResponse{}},
		"withdrawn":   SnapshotResponse{Contract: Contract, Cursor: cursor, Snapshot: withdrawn},
		"quarantined": SnapshotResponse{Contract: Contract, Cursor: cursor, Snapshot: quarantined},
		"unavailable": SnapshotResponse{Contract: Contract, Cursor: cursor, Snapshot: unavailable},
		"intent":      intent,
		"execution":   execution,
		"error":       map[string]any{"contract": Contract, "error": "invalid_intent"},
	}
	for _, name := range oracleKeys(valid) {
		wire := wireValue(t, valid[name])
		oracleCase(t, "corpus", "valid-"+oracleName(name), feedSourceSchema, "matter/feedv1/schema_corpus_test.go", "TestSchemaCorpusMatchesFeedWireValues/"+name,
			obj(kv{"schema_file", reference}, kv{"wire_value", wire}, kv{"intent_deadline_note", "the intent deadline is fixed by the recorder"}), obj(kv{"validation", schemaVerdict(schema, wire)}))
	}
	response := httptest.NewRecorder()
	WriteUnavailable(response)
	var budget map[string]any
	if err := json.Unmarshal(response.Body.Bytes(), &budget); err != nil {
		t.Fatal(err)
	}
	oracleCase(t, "corpus", "valid-budget-refusal", feedSourceServer, "matter/feedv1/schema_corpus_test.go", "TestSchemaCorpusMatchesFeedWireValues/budget_refusal",
		obj(kv{"schema_file", reference}, kv{"call", "WriteUnavailable(response recorder)"}),
		obj(kv{"status", response.Code}, kv{"content_type", response.Header().Get("Content-Type")}, kv{"body", rawBody(response.Body.Bytes())}, kv{"validation", schemaVerdict(schema, wireValue(t, budget))}))

	invalid := map[string]func(map[string]any){
		"unknown_member":   func(value map[string]any) { value["route"] = "must-not-cross-the-boundary" },
		"wrong_constant":   func(value map[string]any) { value["contract"] = "other/v1" },
		"missing_required": func(value map[string]any) { delete(value["cursor"].(map[string]any), "instance") },
		"malformed_report": func(value map[string]any) {
			delete(value["snapshot"].(map[string]any)["resources"].([]any)[0].(map[string]any)["projected"].(map[string]any)["report"].(map[string]any), "snapshot_id")
		},
		"malformed_action": func(value map[string]any) {
			value["snapshot"].(map[string]any)["operations"].([]any)[0].(map[string]any)["action"].(map[string]any)["discoverable"] = "true"
		},
		"malformed_causal": func(value map[string]any) {
			value["causal"].(map[string]any)["origin"].(map[string]any)["kind"] = "native_route"
		},
		"malformed_revision": func(value map[string]any) {
			value["snapshot"].(map[string]any)["resources"].([]any)[0].(map[string]any)["revisions"].(map[string]any)["semantic"] = float64(1)
		},
		"current_missing_projected": func(value map[string]any) {
			delete(value["snapshot"].(map[string]any)["resources"].([]any)[0].(map[string]any), "projected")
		},
		"current_zero_revisions": func(value map[string]any) {
			revisions := value["snapshot"].(map[string]any)["resources"].([]any)[0].(map[string]any)["revisions"].(map[string]any)
			for key := range revisions {
				revisions[key] = ""
			}
		},
		"noncurrent_retains_projected": func(value map[string]any) {
			value["snapshot"].(map[string]any)["resources"].([]any)[0].(map[string]any)["projected"] = wireValue(t, snapshot).(map[string]any)["resources"].([]any)[0].(map[string]any)["projected"]
		},
		"noncurrent_retains_current_fence": func(value map[string]any) {
			resource := value["snapshot"].(map[string]any)["resources"].([]any)[0].(map[string]any)
			current := wireValue(t, snapshot).(map[string]any)["resources"].([]any)[0].(map[string]any)
			resource["snapshot_id"] = current["snapshot_id"]
			resource["revisions"] = current["revisions"]
			resource["binding_id"] = current["binding_id"]
			resource["source_epoch"] = current["source_epoch"]
			resource["driver_generation"] = current["driver_generation"]
		},
	}
	for _, name := range oracleKeys(invalid) {
		var value map[string]any
		base := "snapshot"
		if name == "malformed_causal" {
			value, base = wireValue(t, intent).(map[string]any), "intent"
		} else if strings.HasPrefix(name, "noncurrent_") {
			value, base = wireValue(t, valid["withdrawn"]).(map[string]any), "withdrawn"
		} else {
			value = wireValue(t, valid["snapshot"]).(map[string]any)
		}
		invalid[name](value)
		oracleCase(t, "corpus", "invalid-"+oracleName(name), feedSourceSchema, "matter/feedv1/schema_corpus_test.go", "TestSchemaCorpusMatchesFeedWireValues/"+name,
			obj(kv{"schema_file", reference}, kv{"base_wire_value", base}, kv{"mutation", name}, kv{"wire_value", value}), obj(kv{"validation", schemaVerdict(schema, value)}))
	}
}

func recordGeneration(t *testing.T) {
	schema, reference := schemaFile(t)
	for _, tc := range []struct {
		name  string
		value any
	}{
		{"zero", "0"}, {"current", "7"}, {"beyond-browser-integer", "9007199254740993"}, {"uint64-max", "18446744073709551615"},
		{"numeric", float64(7)}, {"empty", ""}, {"negative", "-1"}, {"leading-zero", "07"}, {"fraction", "1.5"}, {"exponent", "1e3"}, {"text", "generation"},
	} {
		snapshot := validSnapshot(t, ResourceCurrent, true)
		value := wireValue(t, SnapshotResponse{Contract: Contract, Cursor: Cursor{Instance: "schema", Sequence: 1}, Snapshot: snapshot}).(map[string]any)
		source := value["snapshot"].(map[string]any)["operations"].([]any)[0].(map[string]any)["action"].(map[string]any)["source"].(map[string]any)
		source["driver_generation"] = tc.value
		oracleCase(t, "embedded-generation", tc.name, feedSourceSchema, "matter/feedv1/schema_corpus_test.go", "TestSchemaEmbeddedPortalGeneration/"+tc.name,
			obj(kv{"schema_file", reference}, kv{"base", "snapshot response with one admitted operation"}, kv{"operation_action_source_driver_generation", tc.value}, kv{"wire_value", value}),
			obj(kv{"validation", schemaVerdict(schema, value)}))
	}
}

var _ = reflect.DeepEqual
