package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	graphqlgo "github.com/graphql-go/graphql"

	"github.com/Project-Helianthus/helianthus-ebusgateway/graphql"
	"github.com/Project-Helianthus/helianthus-ebusgateway/mcp"
	"github.com/Project-Helianthus/helianthus-ebusreg/registry"
	"github.com/Project-Helianthus/helianthus-ebusreg/router"
)

// The harness drives the pin's own mapping functions on synthetic native
// views and records what they publish: the GraphQL result of a full-selection
// query of the plane, the MCP adapter value and the MCP tool output, and the
// semantic cache bytes. It edits no algorithm of the pin.

const qv07Format = "helianthus-oracle-qv07-case/1"

var qv07Clock = time.Date(2030, time.April, 10, 8, 0, 0, 0, time.UTC)

type qv07Input struct {
	Bytes      string         `json:"bytes"`
	Qualifiers map[string]any `json:"qualifiers"`
	Clock      map[string]any `json:"clock"`
	State      map[string]any `json:"state"`
}

type qv07Output struct {
	Decisions    []any          `json:"decisions"`
	GraphQL      map[string]any `json:"graphql"`
	MCP          map[string]any `json:"mcp"`
	Cache        map[string]any `json:"cache"`
	Observations []any          `json:"observations"`
}

type qv07Case struct {
	Format    string     `json:"format"`
	Component string     `json:"component"`
	Source    []string   `json:"source"`
	Stimulus  string     `json:"stimulus"`
	Input     qv07Input  `json:"input"`
	Output    qv07Output `json:"output"`
}

func qv07F(v float64) *float64 { return &v }
func qv07I(v int) *int         { return &v }
func qv07B(v bool) *bool       { return &v }
func qv07S(v string) *string   { return &v }
func qv07U8(v uint8) *uint8    { return &v }
func qv07U16(v uint16) *uint16 { return &v }
func qv07U32(v uint32) *uint32 { return &v }

type qv07Invoker struct{}

func (qv07Invoker) Invoke(context.Context, router.Plane, string, map[string]any) (any, error) {
	return nil, fmt.Errorf("the harness performs no native acquisition")
}

type qv07Plane struct {
	graphql []string
	tools   []string
	adapter func(a mcpSemanticProviderAdapter) map[string]any
}

var qv07Planes = map[string]qv07Plane{
	"zones":    {[]string{"zones"}, []string{"ebus_v1_semantic_zones_get"}, func(a mcpSemanticProviderAdapter) map[string]any { return map[string]any{"zones": a.Zones()} }},
	"dhw":      {[]string{"dhw"}, []string{"ebus_v1_semantic_dhw_get"}, func(a mcpSemanticProviderAdapter) map[string]any { return map[string]any{"dhw": a.DHW()} }},
	"circuits": {[]string{"circuits"}, []string{"ebus_v1_semantic_circuits_get"}, func(a mcpSemanticProviderAdapter) map[string]any { return map[string]any{"circuits": a.Circuits()} }},
	"radio": {[]string{"radio_devices"}, []string{"ebus_v1_semantic_radio_devices_get"}, func(a mcpSemanticProviderAdapter) map[string]any {
		return map[string]any{"radio_devices": a.RadioDevices()}
	}},
	"boiler": {[]string{"boiler_status"}, []string{"ebus_v1_semantic_boiler_status_get"}, func(a mcpSemanticProviderAdapter) map[string]any {
		return map[string]any{"boiler_status": a.BoilerStatus()}
	}},
	"system": {[]string{"system"}, []string{"ebus_v1_semantic_system_get"}, func(a mcpSemanticProviderAdapter) map[string]any { return map[string]any{"system": a.System()} }},
	"fm5": {[]string{"fm5_semantic_mode", "fm5_interpretation"}, []string{"ebus_v1_semantic_fm5_mode_get", "ebus_v1_semantic_fm5_interpretation_get"}, func(a mcpSemanticProviderAdapter) map[string]any {
		return map[string]any{"fm5_mode": a.FM5SemanticMode(), "fm5_interpretation": a.FM5Interpretation()}
	}},
	"solar":     {[]string{"solar"}, []string{"ebus_v1_semantic_solar_get"}, func(a mcpSemanticProviderAdapter) map[string]any { return map[string]any{"solar": a.Solar()} }},
	"cylinders": {[]string{"cylinders"}, []string{"ebus_v1_semantic_cylinders_get"}, func(a mcpSemanticProviderAdapter) map[string]any { return map[string]any{"cylinders": a.Cylinders()} }},
	"energy": {[]string{"energy_totals"}, []string{"ebus_v1_semantic_energy_totals_get"}, func(a mcpSemanticProviderAdapter) map[string]any {
		return map[string]any{"energy_totals": a.EnergyTotals()}
	}},
	"schedules": {[]string{"schedules"}, []string{"ebus_v1_semantic_schedules_get"}, func(a mcpSemanticProviderAdapter) map[string]any { return map[string]any{"schedules": a.Schedules()} }},
	"adapter": {[]string{"adapter_hardware_info"}, []string{"ebus_v1_semantic_adapter_info_get"}, func(a mcpSemanticProviderAdapter) map[string]any {
		return map[string]any{"adapter_hardware_info": a.AdapterHardwareInfo()}
	}},
	"capability": {[]string{"vaillant_regulator_capability"}, nil, nil},
}

// qv07Selection selects every leaf of an output type, fields in name order.
func qv07Selection(t *testing.T, output graphqlgo.Output) string {
	t.Helper()
	switch typed := output.(type) {
	case *graphqlgo.NonNull:
		return qv07Selection(t, typed.OfType)
	case *graphqlgo.List:
		return qv07Selection(t, typed.OfType)
	case *graphqlgo.Object:
		fields := typed.Fields()
		names := make([]string, 0, len(fields))
		for name := range fields {
			names = append(names, name)
		}
		sort.Strings(names)
		parts := make([]string, 0, len(names))
		for _, name := range names {
			if len(fields[name].Args) > 0 {
				continue
			}
			if sub := qv07Selection(t, fields[name].Type); sub != "" {
				parts = append(parts, name+" "+sub)
			} else {
				parts = append(parts, name)
			}
		}
		return "{ " + strings.Join(parts, " ") + " }"
	case *graphqlgo.Scalar, *graphqlgo.Enum:
		return ""
	default:
		t.Fatalf("unsupported GraphQL output type %T", output)
		return ""
	}
}

func qv07GraphQL(t *testing.T, provider *graphql.LiveSemanticProvider, roots []string) map[string]any {
	t.Helper()
	builder := graphql.NewBuilder(nil, nil)
	builder.SetSemanticProvider(provider)
	schema, err := graphql.NewQuerySchema(builder)
	if err != nil {
		t.Fatalf("query schema: %v", err)
	}
	out := map[string]any{}
	for _, root := range roots {
		field, ok := schema.QueryType().Fields()[root]
		if !ok {
			t.Fatalf("GraphQL query root %q is not in the schema", root)
		}
		query := "{ " + root
		if selection := qv07Selection(t, field.Type); selection != "" {
			query += " " + selection
		}
		query += " }"
		result := graphqlgo.Do(graphqlgo.Params{Schema: schema, RequestString: query})
		record := map[string]any{"query": query}
		if len(result.Errors) > 0 {
			errs := make([]any, 0, len(result.Errors))
			for _, e := range result.Errors {
				errs = append(errs, e.Message)
			}
			record["errors"] = errs
		}
		if data, ok := result.Data.(map[string]any); ok {
			record["data"] = data[root]
		}
		out[root] = record
	}
	return out
}

func qv07Tool(t *testing.T, server *mcp.Server, tool string) map[string]any {
	t.Helper()
	return qv07ToolWith(t, server, tool, "{}")
}

func qv07ToolWith(t *testing.T, server *mcp.Server, tool string, arguments string) map[string]any {
	t.Helper()
	body := fmt.Sprintf(`{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":%q,"arguments":%s}}`, tool, arguments)
	request := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(body))
	recorder := httptest.NewRecorder()
	server.Handler().ServeHTTP(recorder, request)
	var response struct {
		Result struct {
			Content []struct {
				Text string `json:"text"`
			} `json:"content"`
		} `json:"result"`
		Error any `json:"error"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &response); err != nil {
		t.Fatalf("tool %s response: %v", tool, err)
	}
	if response.Error != nil || len(response.Result.Content) != 1 {
		t.Fatalf("tool %s response = %s", tool, recorder.Body.String())
	}
	var envelope map[string]any
	if err := json.Unmarshal([]byte(response.Result.Content[0].Text), &envelope); err != nil {
		t.Fatalf("tool %s envelope: %v", tool, err)
	}
	meta, _ := envelope["meta"].(map[string]any)
	record := map[string]any{"data": envelope["data"], "error": envelope["error"]}
	if meta != nil {
		record["meta"] = map[string]any{"contract": meta["contract"], "consistency": meta["consistency"], "data_hash": meta["data_hash"]}
	}
	return record
}

// qv07Normalize turns a value into its JSON-decoded form so that every record
// is written with the same key order.
func qv07Normalize(t *testing.T, value any) any {
	t.Helper()
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	var out any
	if err := json.Unmarshal(data, &out); err != nil {
		t.Fatal(err)
	}
	return out
}

func qv07MCP(t *testing.T, provider *graphql.LiveSemanticProvider, planes []string) map[string]any {
	t.Helper()
	adapter := mcpSemanticProviderAdapter{provider: provider}
	server, err := mcp.NewServer(registry.NewDeviceRegistry(nil), qv07Invoker{})
	if err != nil {
		t.Fatal(err)
	}
	server.SetSemanticProvider(adapter)
	adapters := map[string]any{}
	tools := map[string]any{}
	for _, name := range planes {
		if name == "capability" {
			for tool, record := range qv07CapabilityMCP(t, provider) {
				tools[tool] = record
			}
			continue
		}
		plane := qv07Planes[name]
		if plane.adapter == nil {
			continue
		}
		for key, value := range plane.adapter(adapter) {
			adapters[key] = qv07Normalize(t, value)
		}
		for _, tool := range plane.tools {
			tools[tool] = qv07Tool(t, server, tool)
		}
	}
	return map[string]any{"adapter": adapters, "tools": tools}
}

// qv07CapabilityMCP records the regulator capability as the pin's MCP server
// emits it: the runtime status tool and the runtime status plane of the
// semantic snapshot tool, over the pin's runtime status provider.
func qv07CapabilityMCP(t *testing.T, provider *graphql.LiveSemanticProvider) map[string]any {
	t.Helper()
	server, err := mcp.NewServer(registry.NewDeviceRegistry(nil), qv07Invoker{})
	if err != nil {
		t.Fatal(err)
	}
	server.SetStatusProvider(newMCPRuntimeStatusProvider(provider, nil))
	return map[string]any{
		"ebus_v1_runtime_status_get":    qv07ToolWith(t, server, "ebus_v1_runtime_status_get", "{}"),
		"ebus_v1_semantic_snapshot_get": qv07ToolWith(t, server, "ebus_v1_semantic_snapshot_get", `{"planes":["runtime_status"]}`),
	}
}

// qv07Capture records the published state of the named planes.
func qv07Capture(t *testing.T, provider *graphql.LiveSemanticProvider, planes ...string) (map[string]any, map[string]any) {
	t.Helper()
	var roots []string
	for _, name := range planes {
		plane, ok := qv07Planes[name]
		if !ok {
			t.Fatalf("unknown plane %q", name)
		}
		roots = append(roots, plane.graphql...)
	}
	return qv07GraphQL(t, provider, roots), qv07MCP(t, provider, planes)
}

type qv07Env struct {
	t         *testing.T
	provider  *graphql.LiveSemanticProvider
	owner     *vaillantSemanticPublication
	decisions []any
}

func newQV07Env(t *testing.T) *qv07Env {
	t.Helper()
	provider := graphql.NewLiveSemanticProvider()
	provider.SetEnergyClock(func() time.Time { return qv07Clock })
	return &qv07Env{t: t, provider: provider, owner: newVaillantSemanticPublication(provider, nil, nil)}
}

func (e *qv07Env) decide(step string, fields map[string]any) {
	record := map[string]any{"step": step}
	for key, value := range fields {
		record[key] = value
	}
	e.decisions = append(e.decisions, record)
}

func qv07Native(t *testing.T, value any) any { return qv07Normalize(t, value) }

// finish captures the named planes and writes the case file.
func (e *qv07Env) finish(path string, source []string, stimulus string, state map[string]any, qualifiers map[string]any, planes ...string) {
	e.t.Helper()
	gql, mcpRecord := qv07Capture(e.t, e.provider, planes...)
	if qualifiers == nil {
		qualifiers = map[string]any{}
	}
	qv07Write(e.t, path, qv07Case{
		Component: "cmd/gateway vaillant typed publication",
		Source:    source,
		Stimulus:  stimulus,
		Input:     qv07Input{Qualifiers: qualifiers, Clock: map[string]any{"energy_clock": qv07Clock.Format(time.RFC3339Nano)}, State: state},
		Output:    qv07Output{Decisions: e.decisions, GraphQL: gql, MCP: mcpRecord, Cache: map[string]any{}, Observations: []any{}},
	})
}

func qv07Write(t *testing.T, path string, document qv07Case) {
	t.Helper()
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	document.Format = qv07Format
	if document.Input.State == nil {
		document.Input.State = map[string]any{}
	}
	if document.Input.Qualifiers == nil {
		document.Input.Qualifiers = map[string]any{}
	}
	if document.Input.Clock == nil {
		document.Input.Clock = map[string]any{}
	}
	if document.Output.Decisions == nil {
		document.Output.Decisions = []any{}
	}
	if document.Output.GraphQL == nil {
		document.Output.GraphQL = map[string]any{}
	}
	if document.Output.MCP == nil {
		document.Output.MCP = map[string]any{}
	}
	if document.Output.Cache == nil {
		document.Output.Cache = map[string]any{}
	}
	if document.Output.Observations == nil {
		document.Output.Observations = []any{}
	}
	var buffer bytes.Buffer
	encoder := json.NewEncoder(&buffer)
	encoder.SetIndent("", "  ")
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(document); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(directory, path+".json")
	if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(target, buffer.Bytes(), 0o644); err != nil {
		t.Fatal(err)
	}
}

const (
	qv07ViewsFile    = "cmd/gateway/vaillant_semantic_publication_views.go"
	qv07OwnerFile    = "cmd/gateway/vaillant_semantic_publication.go"
	qv07FM5File      = "cmd/gateway/vaillant_semantic_publication_fm5.go"
	qv07SchedFile    = "cmd/gateway/vaillant_semantic_publication_schedules.go"
	qv07CachePubFile = "cmd/gateway/vaillant_semantic_publication_cache.go"
	qv07ProviderFile = "cmd/gateway/semantic_provider.go"
	qv07CacheFile    = "cmd/gateway/semantic_cache.go"

	qv07ViewsTest = "cmd/gateway/vaillant_semantic_publication_views_test.go"
	qv07CacheTest = "cmd/gateway/semantic_cache_test.go"
	qv07SchedTest = "cmd/gateway/vaillant_semantic_publication_schedules_test.go"
)
