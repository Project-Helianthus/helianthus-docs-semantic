package graphql

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-ebusgateway/mcp"
	"github.com/Project-Helianthus/helianthus-ebusgo/types"
	"github.com/Project-Helianthus/helianthus-ebusreg/registry"
)

// oracleTypedProvider serves fixed values through the pre-port SemanticProvider interface.
type oracleTypedProvider struct {
	zones     []Zone
	dhw       *DhwStatus
	circuits  []CircuitStatus
	radio     []RadioDevice
	fm5       Fm5SemanticMode
	solar     *SolarStatus
	cylinders []CylinderStatus
	energy    *EnergyTotals
	boiler    *BoilerStatus
	system    *SystemStatus
	schedules *ScheduleStatus
	adapter   *AdapterHardwareInfo
}

func (p oracleTypedProvider) Zones() []Zone                             { return p.zones }
func (p oracleTypedProvider) DHW() *DhwStatus                           { return p.dhw }
func (p oracleTypedProvider) Circuits() []CircuitStatus                 { return p.circuits }
func (p oracleTypedProvider) RadioDevices() []RadioDevice               { return p.radio }
func (p oracleTypedProvider) FM5SemanticMode() Fm5SemanticMode          { return p.fm5 }
func (p oracleTypedProvider) Solar() *SolarStatus                       { return p.solar }
func (p oracleTypedProvider) Cylinders() []CylinderStatus               { return p.cylinders }
func (p oracleTypedProvider) EnergyTotals() *EnergyTotals               { return p.energy }
func (p oracleTypedProvider) BoilerStatus() *BoilerStatus               { return p.boiler }
func (p oracleTypedProvider) System() *SystemStatus                     { return p.system }
func (p oracleTypedProvider) Schedules() *ScheduleStatus                { return p.schedules }
func (p oracleTypedProvider) AdapterHardwareInfo() *AdapterHardwareInfo { return p.adapter }

var oracleTypedFixedTime = time.Date(2026, time.March, 12, 18, 30, 0, 0, time.UTC)

// oracleTypedFill gives every field of the value a deterministic synthetic value; a counter makes each number distinct.
func oracleTypedFill(value reflect.Value, name string, counter *int) {
	switch value.Kind() {
	case reflect.Ptr:
		if value.IsNil() {
			value.Set(reflect.New(value.Type().Elem()))
		}
		oracleTypedFill(value.Elem(), name, counter)
	case reflect.Struct:
		if value.Type() == reflect.TypeOf(time.Time{}) {
			value.Set(reflect.ValueOf(oracleTypedFixedTime))
			return
		}
		for index := 0; index < value.NumField(); index++ {
			if value.Type().Field(index).IsExported() {
				oracleTypedFill(value.Field(index), value.Type().Field(index).Name, counter)
			}
		}
	case reflect.Slice:
		count := 1
		if value.Type().Elem().Kind() == reflect.Float64 || value.Type().Elem().Kind() == reflect.Int {
			count = 2
		}
		if value.Type().Elem().Kind() == reflect.Struct && (name == "YearlyMeta" || name == "MonthlyMeta") {
			count = 2
		}
		slice := reflect.MakeSlice(value.Type(), count, count)
		for index := 0; index < count; index++ {
			oracleTypedFill(slice.Index(index), name, counter)
		}
		value.Set(slice)
	case reflect.String:
		switch value.Type().Name() {
		case "ManagingDeviceRole":
			value.SetString("FUNCTION_MODULE")
		case "Fm5SemanticMode":
			value.SetString("INTERPRETED")
		case "EnergyFreshnessState":
			value.SetString("fresh")
		case "EnergyProvenance":
			value.SetString("register")
		default:
			value.SetString("synthetic-" + name)
		}
	case reflect.Float64:
		*counter++
		value.SetFloat(float64(10+*counter) + 0.5)
	case reflect.Int, reflect.Int64:
		*counter++
		value.SetInt(int64(100 + *counter))
	case reflect.Uint8:
		*counter++
		value.SetUint(uint64(1 + *counter%200))
	case reflect.Bool:
		value.SetBool(true)
	}
}

func oracleTypedComplete() oracleTypedProvider {
	counter := 0
	provider := oracleTypedProvider{fm5: Fm5SemanticModeInterpreted}
	fill := func(target any) { oracleTypedFill(reflect.ValueOf(target).Elem(), "", &counter) }
	var zone Zone
	fill(&zone)
	provider.zones = []Zone{zone}
	provider.dhw = &DhwStatus{}
	fill(provider.dhw)
	var circuit CircuitStatus
	fill(&circuit)
	provider.circuits = []CircuitStatus{circuit}
	var radio RadioDevice
	fill(&radio)
	provider.radio = []RadioDevice{radio}
	provider.solar = &SolarStatus{}
	fill(provider.solar)
	var cylinder CylinderStatus
	fill(&cylinder)
	provider.cylinders = []CylinderStatus{cylinder}
	provider.energy = &EnergyTotals{}
	fill(provider.energy)
	provider.boiler = &BoilerStatus{}
	fill(provider.boiler)
	flow := 52.5
	provider.boiler.State.FlowTemperatureC = &flow
	provider.system = &SystemStatus{}
	fill(provider.system)
	provider.schedules = &ScheduleStatus{}
	fill(provider.schedules)
	provider.adapter = &AdapterHardwareInfo{}
	fill(provider.adapter)
	return provider
}

func oracleTypedPost(t *testing.T, handler http.Handler, query string) any {
	t.Helper()
	body, _ := json.Marshal(map[string]any{"query": query})
	request := httptest.NewRequest(http.MethodPost, "/graphql", bytes.NewReader(body))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, request)
	var document any
	if err := json.Unmarshal(recorder.Body.Bytes(), &document); err != nil {
		t.Fatalf("response is not JSON: %s", recorder.Body.String())
	}
	return document
}

type oracleTypedType struct {
	Name   string `json:"name"`
	Kind   string `json:"kind"`
	Fields []struct {
		Name string `json:"name"`
		Args []struct {
			Name string `json:"name"`
		} `json:"args"`
		Type oracleTypedRef `json:"type"`
	} `json:"fields"`
}

type oracleTypedRef struct {
	Kind   string          `json:"kind"`
	Name   string          `json:"name"`
	OfType *oracleTypedRef `json:"ofType"`
}

func (reference oracleTypedRef) named() (string, string) {
	current := reference
	for current.OfType != nil {
		current = *current.OfType
	}
	return current.Name, current.Kind
}

const oracleTypedIntrospection = `query { __schema { queryType { name } types { kind name fields { name args { name } type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } } }`

func oracleTypedSchema(t *testing.T, handler http.Handler) map[string]oracleTypedType {
	t.Helper()
	document := oracleTypedPost(t, handler, oracleTypedIntrospection)
	encoded, _ := json.Marshal(document)
	var parsed struct {
		Data struct {
			Schema struct {
				Types []oracleTypedType `json:"types"`
			} `json:"__schema"`
		} `json:"data"`
	}
	if err := json.Unmarshal(encoded, &parsed); err != nil {
		t.Fatal(err)
	}
	out := make(map[string]oracleTypedType)
	for _, entry := range parsed.Data.Schema.Types {
		out[entry.Name] = entry
	}
	return out
}

// oracleTypedSelection lists every argument-free field of a type, nested objects included, in schema field order sorted by name.
func oracleTypedSelection(schema map[string]oracleTypedType, name string) string {
	entry := schema[name]
	fields := append(entry.Fields[:0:0], entry.Fields...)
	sort.SliceStable(fields, func(i, j int) bool { return fields[i].Name < fields[j].Name })
	parts := make([]string, 0, len(fields))
	for _, field := range fields {
		if len(field.Args) > 0 {
			continue
		}
		typeName, kind := field.Type.named()
		if kind == "OBJECT" {
			parts = append(parts, field.Name+" { "+oracleTypedSelection(schema, typeName)+" }")
		} else {
			parts = append(parts, field.Name)
		}
	}
	return strings.Join(parts, " ")
}

func oracleTypedRootQuery(schema map[string]oracleTypedType, root string) string {
	for _, field := range schema["Query"].Fields {
		if field.Name != root {
			continue
		}
		typeName, kind := field.Type.named()
		if kind == "OBJECT" {
			return "query { " + root + " { " + oracleTypedSelection(schema, typeName) + " } }"
		}
		return "query { " + root + " }"
	}
	return ""
}

var oracleTypedRoots = []string{
	"zones", "dhw", "circuits", "radioDevices", "fm5SemanticMode", "solar", "cylinders", "energyTotals", "boilerStatus", "system", "schedules", "adapterHardwareInfo",
	"radio_devices", "fm5_semantic_mode", "energy_totals", "boiler_status", "adapter_hardware_info",
}

type oracleTypedRecord struct {
	Name     string `json:"name"`
	Fixture  string `json:"fixture"`
	Query    string `json:"query"`
	Response any    `json:"response"`
}

func oracleTypedHandler(t *testing.T, provider SemanticProvider) http.Handler {
	t.Helper()
	builder := NewBuilder(mockRegistry{}, nil)
	if provider != nil {
		builder.SetSemanticProvider(provider)
	}
	handler, err := NewHandler(builder)
	if err != nil {
		t.Fatal(err)
	}
	return handler
}

func oracleTypedWrite(t *testing.T, directory, name string, document any) {
	t.Helper()
	encoded, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, name), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

// TestOraclePrePortTypedQueries records the typed semantic root queries of graphql/queries.go and graphql/semantic.go.
func TestOraclePrePortTypedQueries(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	static := oracleTypedHandler(t, nil)
	schema := oracleTypedSchema(t, static)

	var complete []oracleTypedRecord
	completeHandler := oracleTypedHandler(t, oracleTypedComplete())
	for _, root := range oracleTypedRoots {
		query := oracleTypedRootQuery(schema, root)
		if query == "" {
			t.Fatalf("root %s is not published", root)
		}
		complete = append(complete, oracleTypedRecord{Name: root, Fixture: "complete-synthetic", Query: query, Response: oracleTypedPost(t, completeHandler, query)})
	}

	var pin []oracleTypedRecord
	for _, root := range oracleTypedRoots[:12] {
		query := oracleTypedRootQuery(schema, root)
		pin = append(pin, oracleTypedRecord{Name: root + "/static-provider", Fixture: "default provider of the builder; the pin's own test expects empty, nil and ABSENT answers", Query: query, Response: oracleTypedPost(t, static, query)})
	}

	associatedCircuit := 1
	roomMapping := 2
	live := NewLiveSemanticProvider()
	live.SetZones([]Zone{{
		ID:   "zone-2",
		Name: "Etaj",
		Config: ZoneConfig{
			OperatingMode:              "heat",
			Preset:                     "manual",
			AllowedModes:               []string{"off", "auto", "heat"},
			CircuitType:                "underfloor",
			AssociatedCircuit:          &associatedCircuit,
			RoomTemperatureZoneMapping: &roomMapping,
		},
	}})
	liveHandler := oracleTypedHandler(t, live)
	zonesQuery := oracleTypedRootQuery(schema, "zones")
	pin = append(pin, oracleTypedRecord{Name: "zones/zones_dhw", Fixture: "the zone the pin's zones_dhw case publishes", Query: zonesQuery, Response: oracleTypedPost(t, liveHandler, zonesQuery)})

	deviceID := "VR_71"
	address := 0x26
	live.SetCircuits([]CircuitStatus{{
		Index:       0,
		CircuitType: "heating",
		ManagingDevice: ManagingDevice{
			Role:     ManagingDeviceRoleFunctionModule,
			DeviceID: &deviceID,
			Address:  &address,
		},
	}})
	managing := "query { circuits { index managingDevice { role deviceId address } } }"
	pin = append(pin, oracleTypedRecord{Name: "circuits/managing-device", Fixture: "the circuit the pin's managing-device case publishes", Query: managing, Response: oracleTypedPost(t, liveHandler, managing)})
	live.SetCircuits(nil)

	removed := "query { system { properties { vr71CircuitStartIndex } } }"
	pin = append(pin, oracleTypedRecord{Name: "system/removed-vr71CircuitStartIndex", Fixture: "the pin's removed-field case", Query: removed, Response: oracleTypedPost(t, liveHandler, removed)})

	energyNoData := "query { energyTotals { gas { dhw { today todayMeta { freshnessState provenance stale } yearlyMeta { freshnessState provenance stale } } } } }"
	pin = append(pin, oracleTypedRecord{Name: "energyTotals/no-data", Fixture: "the pin's energy_totals_root case", Query: energyNoData, Response: oracleTypedPost(t, liveHandler, energyNoData)})

	for _, step := range []struct {
		key EnergyMergeKey
		kwh float64
	}{
		{EnergyMergeKey{Channel: "gas", Usage: "hot_water", Period: "day"}, 3.5},
		{EnergyMergeKey{Channel: "gas", Usage: "hot_water", Period: "year", YearKind: "previous"}, 120.0},
		{EnergyMergeKey{Channel: "gas", Usage: "hot_water", Period: "year", YearKind: "current"}, 240.0},
		{EnergyMergeKey{Channel: "electricity", Usage: "heating", Period: "day"}, 1.25},
		{EnergyMergeKey{Channel: "gas", Usage: "hot_water", Period: "month", YearKind: "current"}, 15.0},
		{EnergyMergeKey{Channel: "solar", Usage: "cooling", Period: "day"}, 2.75},
	} {
		live.ApplyEnergyFromRegister(step.key, step.kwh)
	}
	energyValues := "query { energyTotals { gas { dhw { today yearly monthly todayMeta { freshnessState provenance stale } monthlyMeta { freshnessState provenance stale } } climate { today } } electric { climate { today } } solar { climate { today } } } }"
	pin = append(pin, oracleTypedRecord{Name: "energyTotals/with-values", Fixture: "the register values the pin's energy_totals_root_with_values case applies; the observation time and age are the host clock and are not selected", Query: energyValues, Response: oracleTypedPost(t, liveHandler, energyValues)})

	tempC := 22.5
	tempRaw := 225
	minTemp := 5.0
	maxTemp := 30.0
	live.SetSchedules(&ScheduleStatus{Programs: []ScheduleProgram{{
		Zone: 0,
		HC:   "heating",
		Config: &ScheduleConfig{
			MaxSlots: 12, TimeResolution: 10, MinDuration: 5, HasTemperature: true, TempSlots: 12, MinTempC: &minTemp, MaxTempC: &maxTemp,
		},
		SlotsUsed: []int{1, 0, 1, 1, 1, 1, 1},
		Days: []ScheduleDayProgram{{
			Weekday: "monday",
			Slots:   []ScheduleTimerSlot{{StartHour: 0, StartMinute: 0, EndHour: 24, EndMinute: 0, TemperatureC: &tempC, TemperatureRaw: &tempRaw}},
		}},
	}}})
	schedulesQuery := oracleTypedRootQuery(schema, "schedules")
	pin = append(pin, oracleTypedRecord{Name: "schedules/schedules_populated", Fixture: "the program the pin's schedules_populated case publishes", Query: schedulesQuery, Response: oracleTypedPost(t, liveHandler, schedulesQuery)})

	flowPin, returnPin, pumpPin, heatingPin := 52.5, 47.0, true, 2
	live.SetBoilerStatus(&BoilerStatus{
		State:       BoilerState{FlowTemperatureC: &flowPin, ReturnTemperatureC: &returnPin, CentralHeatingPumpActive: &pumpPin},
		Diagnostics: BoilerDiagnostics{HeatingStatusRaw: &heatingPin},
	})
	boilerQuery := oracleTypedRootQuery(schema, "boilerStatus")
	pin = append(pin, oracleTypedRecord{Name: "boilerStatus/mcp-boiler-fixture", Fixture: "the values the pin's MCP boiler status case publishes (flow 52.5, return 47.0, pump on, heating status 2); no GraphQL test of the pin drives boilerStatus", Query: boilerQuery, Response: oracleTypedPost(t, liveHandler, boilerQuery)})

	oracleTypedWrite(t, directory, "graphql-typed-queries.json", map[string]any{
		"format":      "helianthus-oracle-pre-port-typed-graphql/1",
		"description": "typed semantic root queries of the pre-port GraphQL surface; each query selects every argument-free field of its type",
		"complete":    complete,
		"pin_cases":   pin,
	})
}

type oracleMutationCall struct {
	Plane  string         `json:"plane"`
	Method string         `json:"method"`
	Params map[string]any `json:"params"`
}

func oracleMutationParams(params map[string]any) map[string]any {
	out := make(map[string]any, len(params))
	for key, value := range params {
		switch typed := value.(type) {
		case []byte:
			out[key] = fmt.Sprintf("%X", typed)
		case byte:
			out[key] = fmt.Sprintf("byte:%02X", typed)
		case uint16:
			out[key] = fmt.Sprintf("u16:%04X", typed)
		default:
			out[key] = value
		}
	}
	return out
}

// TestOraclePrePortTypedMutations records the mutation type of graphql/mutations.go on the pin's mutation fixtures.
func TestOraclePrePortTypedMutations(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	type scenario struct {
		name     string
		fixture  string
		request  string
		registry InvokeRegistry
		invoker  *mutationTestInvoker
		boiler   *mockBoilerWriter
		schedule *mockScheduleWriter
		source   func() (byte, bool)
	}
	controller := func() InvokeRegistry {
		return mutationTestRegistry{
			entries: map[byte]registry.DeviceEntry{0x15: testControllerEntryWithMethods(mutationSetExtRegisterMethod, mutationGetExtRegisterMethod)},
			order:   []byte{0x15},
		}
	}
	controllerSetOnly := func() InvokeRegistry {
		return mutationTestRegistry{
			entries: map[byte]registry.DeviceEntry{0x15: testControllerEntryWithMethods(mutationSetExtRegisterMethod)},
			order:   []byte{0x15},
		}
	}
	circuitFailure := func(name, fixture, query string) scenario {
		return scenario{name: name, fixture: fixture, request: query, registry: controller(), invoker: &mutationTestInvoker{}}
	}
	scenarios := []scenario{
		{
			name:     "setCircuitConfig/success",
			fixture:  "TestSetCircuitConfigMutation_Success",
			request:  `mutation { setCircuitConfig(index: 1, field: "heatingCurve", value: "1.5") { success error } }`,
			registry: controller(),
			invoker: &mutationTestInvoker{responses: []any{
				map[string]types.Value{},
				map[string]types.Value{"value": {Value: []byte{0x00, 0x00, 0xC0, 0x3F}, Valid: true}},
			}},
		},
		{
			name:     "setSystemConfig/success",
			fixture:  "TestSetSystemConfigMutation_Success",
			request:  `mutation { setSystemConfig(field: "adaptiveHeatingCurve", value: "true") { success error } }`,
			registry: controller(),
			invoker: &mutationTestInvoker{responses: []any{
				map[string]types.Value{},
				map[string]types.Value{"value": {Value: []byte{0x01}, Valid: true}},
			}},
		},
		{
			name:    "setBoilerConfig/delegates-to-writer",
			fixture: "TestSetBoilerConfigMutation_DelegatesToWriter",
			request: `mutation { setBoilerConfig(field: "flowsetHcMaxC", value: "55") { success error } }`,
			boiler:  &mockBoilerWriter{result: BoilerConfigMutationResult{Success: true}},
		},
		{
			name:    "setBoilerConfig/unsupported-in-reduced-profile",
			fixture: "TestSetBoilerConfigMutation_UnsupportedInReducedProfile",
			request: `mutation { setBoilerConfig(field: "flowsetHcMaxC", value: "55") { success error } }`,
			source:  func() (byte, bool) { return 0, false },
		},
		{
			name:     "setZoneTimeProgram/success",
			fixture:  "TestSetZoneTimeProgramMutation_Success",
			request:  `mutation { setZoneTimeProgram(zone: 2, weekday: 1, slots: "[{\"start_hour\":6,\"start_minute\":0,\"end_hour\":22,\"end_minute\":0,\"temperature_c\":21}]") { success error slotResults { slotIndex accepted errorCode errorDescription } } }`,
			schedule: &mockScheduleWriter{zoneResult: &mcp.TimeProgramWriteResult{Success: true, SlotResults: []mcp.TimeProgramSlotResult{{SlotIndex: 0, Accepted: true, ErrorCode: 0}}}},
		},
		{
			name:     "setDhwTimeProgram/success",
			fixture:  "TestSetDhwTimeProgramMutation_Success",
			request:  `mutation { setDhwTimeProgram(weekday: 5, slots: "[{\"start_hour\":5,\"start_minute\":30,\"end_hour\":7,\"end_minute\":0}]") { success error slotResults { slotIndex accepted errorCode errorDescription } } }`,
			schedule: &mockScheduleWriter{dhwResult: &mcp.TimeProgramWriteResult{Success: true, SlotResults: []mcp.TimeProgramSlotResult{{SlotIndex: 0, Accepted: true, ErrorCode: 0}}}},
		},
		{
			name:     "setZoneTimeProgram/invalid-json",
			fixture:  "TestSetZoneTimeProgramMutation_InvalidJSON",
			request:  `mutation { setZoneTimeProgram(zone: 1, weekday: 2, slots: "not-json") { success error slotResults { slotIndex } } }`,
			schedule: &mockScheduleWriter{},
		},
		{
			name:     "setSystemConfig/integer-like-float-string",
			fixture:  "TestSetSystemConfigMutation_IntegerLikeFloatString",
			request:  `mutation { setSystemConfig(field: "maxRoomHumidityPct", value: "55.0") { success error } }`,
			registry: controller(),
			invoker: &mutationTestInvoker{responses: []any{
				map[string]types.Value{},
				map[string]types.Value{"value": {Value: []byte{0x37, 0x00}, Valid: true}},
			}},
		},
		{
			name:     "setCircuitConfig/readback-mismatch",
			fixture:  "TestSetCircuitConfigMutation_ReadbackConfirmFailure",
			request:  `mutation { setCircuitConfig(index: 2, field: "heatingCurve", value: "1.5") { success error } }`,
			registry: controller(),
			invoker: &mutationTestInvoker{responses: []any{
				map[string]types.Value{},
				map[string]types.Value{"value": {Value: []byte{0x00, 0x00, 0x40, 0x40}, Valid: true}},
			}},
		},
		{
			name:     "setCircuitConfig/fails-closed-before-source-admission",
			fixture:  "TestSetCircuitConfigMutation_FailsClosedBeforeSourceAdmission",
			request:  `mutation { setCircuitConfig(index: 1, field: "heatingCurve", value: "1.5") { success error } }`,
			registry: controller(),
			invoker:  &mutationTestInvoker{},
			source:   func() (byte, bool) { return 0, false },
		},
		circuitFailure("setCircuitConfig/unknown-field", "TestSetCircuitConfigMutation_ValidationFailures: unknown field", `mutation { setCircuitConfig(index: 1, field: "bogus", value: "1") { success error } }`),
		circuitFailure("setCircuitConfig/float-out-of-range", "TestSetCircuitConfigMutation_ValidationFailures: float out of range", `mutation { setCircuitConfig(index: 1, field: "heatingCurve", value: "8.1") { success error } }`),
		circuitFailure("setCircuitConfig/invalid-enum", "TestSetCircuitConfigMutation_ValidationFailures: invalid enum", `mutation { setCircuitConfig(index: 1, field: "roomTempControl", value: "manual") { success error } }`),
		circuitFailure("setSystemConfig/invalid-bool", "TestSetSystemConfigMutation_FailureScenarios: invalid bool", `mutation { setSystemConfig(field: "adaptiveHeatingCurve", value: "maybe") { success error } }`),
		{
			name:     "setSystemConfig/missing-controller",
			fixture:  "TestSetSystemConfigMutation_FailureScenarios: missing controller",
			request:  `mutation { setSystemConfig(field: "adaptiveHeatingCurve", value: "true") { success error } }`,
			registry: mutationTestRegistry{},
			invoker:  &mutationTestInvoker{},
		},
		{
			name:     "setSystemConfig/missing-get-method",
			fixture:  "TestSetSystemConfigMutation_FailureScenarios: missing get method",
			request:  `mutation { setSystemConfig(field: "adaptiveHeatingCurve", value: "true") { success error } }`,
			registry: controllerSetOnly(),
			invoker:  &mutationTestInvoker{},
		},
		{
			name:     "setZoneConfig/success",
			fixture:  "harness fixture: no test of the pin drives setZoneConfig; the controller and invoker of the pin's circuit success case with the enum value of the zone operating mode",
			request:  `mutation { setZoneConfig(index: 1, field: "operatingMode", value: "auto") { success error } }`,
			registry: controller(),
			invoker: &mutationTestInvoker{responses: []any{
				map[string]types.Value{},
				map[string]types.Value{"value": {Value: []byte{0x01, 0x00}, Valid: true}},
			}},
		},
	}

	var records []map[string]any
	for _, item := range scenarios {
		var invoker Invoker
		if item.invoker != nil {
			invoker = item.invoker
		}
		var boilerWriter BoilerConfigWriter
		if item.boiler != nil {
			boilerWriter = item.boiler
		}
		var scheduleWriter ScheduleWriter
		if item.schedule != nil {
			scheduleWriter = item.schedule
		}
		built := buildMutationSchema(t, item.registry, invoker, boilerWriter, scheduleWriter)
		if item.source != nil {
			built = buildMutationSchemaWithSourceProvider(t, item.registry, invoker, boilerWriter, scheduleWriter, item.source)
		}
		data := executeMutation(t, built, item.request)
		record := map[string]any{"name": item.name, "fixture": item.fixture, "request": item.request, "response": data}
		if item.invoker != nil {
			calls := make([]oracleMutationCall, 0, len(item.invoker.calls))
			for _, call := range item.invoker.calls {
				calls = append(calls, oracleMutationCall{Plane: call.Plane, Method: call.Method, Params: oracleMutationParams(call.Params)})
			}
			record["invoker_calls"] = calls
		}
		if item.boiler != nil {
			calls := make([]map[string]string, 0)
			for _, call := range item.boiler.calls {
				calls = append(calls, map[string]string{"field": call.field, "value": call.value})
			}
			record["boiler_writer_calls"] = calls
		}
		if item.schedule != nil {
			zone := make([]map[string]any, 0)
			for _, call := range item.schedule.zoneCalls {
				zone = append(zone, map[string]any{"zone": call.zone, "weekday": call.weekday, "slots": call.slots})
			}
			dhw := make([]map[string]any, 0)
			for _, call := range item.schedule.dhwCalls {
				dhw = append(dhw, map[string]any{"weekday": call.weekday, "slots": call.slots})
			}
			record["schedule_writer_zone_calls"] = zone
			record["schedule_writer_dhw_calls"] = dhw
		}
		records = append(records, record)
	}

	direct := &mutationTestInvoker{}
	failClosed := ApplyConfigMutation(context.Background(), controller(), direct, 0, false, "heatingCurve", "1.5", circuitConfigFieldSpecs)
	records = append(records, map[string]any{
		"name": "ApplyConfigMutation/fails-closed-before-source-admission", "fixture": "TestApplyConfigMutation_FailsClosedBeforeSourceAdmission",
		"call": "ApplyConfigMutation(source 0, not admitted, heatingCurve, 1.5)", "response": map[string]any{"success": failClosed.Success, "error": failClosed.Error}, "invoker_calls": len(direct.calls),
	})

	oracleTypedWrite(t, directory, "graphql-typed-mutations.json", map[string]any{
		"format":      "helianthus-oracle-pre-port-typed-graphql-mutations/1",
		"description": "mutation answers of graphql/mutations.go on the fixtures of the pin's mutation tests; the source provider admits source 0x7F except where stated by the fixture name",
		"cases":       records,
	})
}
