package mcp

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-ebusreg/registry"
)

var oracleMCPFixedTime = time.Date(2026, time.March, 12, 18, 30, 0, 0, time.UTC)

// oracleMCPFill gives every field of the value a deterministic synthetic value; a counter makes each number distinct.
func oracleMCPFill(value reflect.Value, name string, counter *int) {
	switch value.Kind() {
	case reflect.Ptr:
		if value.IsNil() {
			value.Set(reflect.New(value.Type().Elem()))
		}
		oracleMCPFill(value.Elem(), name, counter)
	case reflect.Struct:
		for index := 0; index < value.NumField(); index++ {
			if value.Type().Field(index).IsExported() {
				oracleMCPFill(value.Field(index), value.Type().Field(index).Name, counter)
			}
		}
	case reflect.Slice:
		count := 1
		if value.Type().Elem().Kind() == reflect.Float64 || value.Type().Elem().Kind() == reflect.Int || name == "YearlyMeta" || name == "MonthlyMeta" {
			count = 2
		}
		slice := reflect.MakeSlice(value.Type(), count, count)
		for index := 0; index < count; index++ {
			oracleMCPFill(slice.Index(index), name, counter)
		}
		value.Set(slice)
	case reflect.String:
		switch {
		case value.Type().Name() == "Fm5SemanticMode":
			value.SetString("INTERPRETED")
		case name == "Role":
			value.SetString("FUNCTION_MODULE")
		case name == "FreshnessState":
			value.SetString("fresh")
		case name == "Provenance":
			value.SetString("register")
		case name == "LastIdentityQuery" || name == "LastTelemetryQuery":
			value.SetString(oracleMCPFixedTime.Format(time.RFC3339))
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

func oracleMCPComplete() testSemanticProvider {
	counter := 0
	fill := func(target any) { oracleMCPFill(reflect.ValueOf(target).Elem(), "", &counter) }
	provider := testSemanticProvider{fm5Mode: Fm5SemanticModeInterpreted}
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
	provider.adapterInfo = &AdapterHardwareInfo{}
	fill(provider.adapterInfo)
	return provider
}

type oracleMCPRecord struct {
	Name      string         `json:"name"`
	Fixture   string         `json:"fixture"`
	Tool      string         `json:"tool"`
	Arguments map[string]any `json:"arguments"`
	IsError   bool           `json:"is_error"`
	Envelope  any            `json:"envelope"`
}

// oracleMCPCall performs one tools/call. The envelope's data_timestamp is the host wall clock and is dropped; every other field is kept.
func oracleMCPCall(t *testing.T, server *Server, name, fixture, tool string, arguments map[string]any) oracleMCPRecord {
	t.Helper()
	params, _ := json.Marshal(map[string]any{"name": tool, "arguments": arguments})
	response := doRPC(t, server.Handler(), rpcRequest{JSONRPC: "2.0", ID: 1, Method: "tools/call", Params: json.RawMessage(params)})
	record := oracleMCPRecord{Name: name, Fixture: fixture, Tool: tool, Arguments: arguments}
	if response.Error != nil {
		record.Envelope = map[string]any{"rpc_error": response.Error}
		return record
	}
	result, _ := response.Result.(map[string]any)
	record.IsError, _ = result["isError"].(bool)
	content, _ := result["content"].([]any)
	if len(content) != 1 {
		t.Fatalf("content = %#v", result["content"])
	}
	text, _ := content[0].(map[string]any)["text"].(string)
	var envelope map[string]any
	if err := json.Unmarshal([]byte(text), &envelope); err != nil {
		t.Fatalf("envelope is not JSON: %s", text)
	}
	if meta, ok := envelope["meta"].(map[string]any); ok {
		delete(meta, "data_timestamp")
	}
	record.Envelope = envelope
	return record
}

func oracleMCPServer(t *testing.T, provider SemanticProvider) *Server {
	t.Helper()
	server, err := NewServer(&testRegistry{entries: make(map[byte]registry.DeviceEntry)}, &testInvoker{})
	if err != nil {
		t.Fatal(err)
	}
	if provider != nil {
		server.SetSemanticProvider(provider)
	}
	return server
}

var oracleMCPGetTools = []string{
	"ebus.v1.semantic.zones.get", "ebus.v1.semantic.circuits.get", "ebus.v1.semantic.radio_devices.get", "ebus.v1.semantic.fm5_mode.get",
	"ebus.v1.semantic.solar.get", "ebus.v1.semantic.cylinders.get", "ebus.v1.semantic.dhw.get", "ebus.v1.semantic.energy_totals.get",
	"ebus.v1.semantic.boiler_status.get", "ebus.v1.semantic.system.get", "ebus.v1.semantic.schedules.get", "ebus.v1.semantic.adapter_info.get",
}

var oracleMCPPlanes = []any{"zones", "dhw", "energy_totals", "boiler_status", "system", "circuits", "radio_devices", "fm5_mode", "solar", "cylinders", "schedules", "adapter_info"}

type oracleMCPConfigWriter struct {
	calls []map[string]string
}

func (writer *oracleMCPConfigWriter) SetSystemConfig(_ context.Context, field string, value string) ConfigSetResult {
	writer.calls = append(writer.calls, map[string]string{"writer": "system", "field": field, "value": value})
	return ConfigSetResult{Success: true}
}

func (writer *oracleMCPConfigWriter) SetBoilerConfig(_ context.Context, field string, value string) ConfigSetResult {
	writer.calls = append(writer.calls, map[string]string{"writer": "boiler", "field": field, "value": value})
	return ConfigSetResult{Success: true}
}

type oracleMCPScheduleWriter struct {
	result *TimeProgramWriteResult
	calls  []map[string]any
}

func (writer *oracleMCPScheduleWriter) SetZoneTimeProgram(_ context.Context, zone int, weekday int, slots []TimeProgramSlot) (*TimeProgramWriteResult, error) {
	writer.calls = append(writer.calls, map[string]any{"writer": "zone", "zone": zone, "weekday": weekday, "slots": slots})
	return writer.result, nil
}

func (writer *oracleMCPScheduleWriter) SetDhwTimeProgram(_ context.Context, weekday int, slots []TimeProgramSlot) (*TimeProgramWriteResult, error) {
	writer.calls = append(writer.calls, map[string]any{"writer": "dhw", "weekday": weekday, "slots": slots})
	return writer.result, nil
}

// TestOraclePrePortTypedMCP records the semantic MCP tools of mcp/server.go.
func TestOraclePrePortTypedMCP(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	var complete, pin, writes []oracleMCPRecord

	completeServer := oracleMCPServer(t, oracleMCPComplete())
	for _, tool := range oracleMCPGetTools {
		complete = append(complete, oracleMCPCall(t, completeServer, tool, "complete-synthetic", tool, map[string]any{}))
	}
	complete = append(complete, oracleMCPCall(t, completeServer, "ebus.v1.semantic.snapshot.get", "complete-synthetic; runtime_status is not selected because it reports the host process", "ebus.v1.semantic.snapshot.get", map[string]any{"planes": oracleMCPPlanes}))

	noProvider := oracleMCPServer(t, nil)
	for _, tool := range oracleMCPGetTools {
		pin = append(pin, oracleMCPCall(t, noProvider, tool+"/no-provider", "server without a semantic provider", tool, map[string]any{}))
	}

	pinServer := oracleMCPServer(t, testSemanticProvider{
		zones: []Zone{
			{ID: "zone-b", Name: "Bedroom", Config: ZoneConfig{OperatingMode: "AUTO", Preset: "COMFORT"}},
			{ID: "zone-a", Name: "Living", Config: ZoneConfig{OperatingMode: "AUTO", Preset: "COMFORT"}},
		},
		circuits: []CircuitStatus{
			{Index: 1, CircuitType: "fixed_value", ManagingDevice: ManagingDevice{Role: "UNKNOWN"}},
			{Index: 0, CircuitType: "heating", ManagingDevice: ManagingDevice{Role: "FUNCTION_MODULE", DeviceID: stringPtr("VR_71"), Address: intPtr(0x26)}},
		},
		radio: []RadioDevice{
			{Group: 0x0A, Instance: 1, DeviceModel: "VR92"},
			{Group: 0x09, Instance: 1, DeviceModel: "VRC720"},
		},
		fm5Mode: Fm5SemanticModeInterpreted,
		solar:   &SolarStatus{CollectorTemperatureC: floatPtr(72.5), PumpActive: boolPtr(true)},
		cylinders: []CylinderStatus{
			{Index: 0, TemperatureC: floatPtr(48.0)},
			{Index: 1, TemperatureC: floatPtr(46.0)},
		},
		dhw: &DhwStatus{Config: DhwConfig{OperatingMode: "AUTO", Preset: "ECO"}},
		energy: &EnergyTotals{Gas: EnergyChannel{
			DHW:     EnergySeries{Today: 1.25, Yearly: []float64{10, 20}, TodayMeta: EnergyPointMeta{FreshnessState: "fresh", Provenance: "register", Stale: false}},
			Climate: EnergySeries{Today: 2.5, Yearly: []float64{30, 40}, TodayMeta: EnergyPointMeta{FreshnessState: "stale", Provenance: "broadcast", Stale: true}},
		}},
		system: &SystemStatus{
			State:      &SystemState{SystemOff: boolPtr(false), SystemWaterPressure: floatPtr(1.5), OutdoorTemperature: floatPtr(6.0), SystemFlowTemperature: floatPtr(32.0)},
			Config:     &SystemConfig{MaxRoomHumidity: intPtr(70)},
			Properties: &SystemProperties{SystemScheme: intPtr(8), ModuleConfigurationVR71: intPtr(2)},
		},
	})
	for _, tool := range oracleMCPGetTools {
		if tool == "ebus.v1.semantic.boiler_status.get" || tool == "ebus.v1.semantic.schedules.get" || tool == "ebus.v1.semantic.adapter_info.get" {
			continue
		}
		pin = append(pin, oracleMCPCall(t, pinServer, tool+"/semantic-snapshots", "the provider of the pin's TestServer_ToolsCallSemanticSnapshots", tool, map[string]any{}))
	}

	flow, returned, pump, heating := 52.5, 47.0, true, 2
	boilerServer := oracleMCPServer(t, testSemanticProvider{boiler: &BoilerStatus{
		State:       &BoilerState{FlowTemperatureC: &flow, ReturnTemperatureC: &returned, CentralHeatingPumpActive: &pump},
		Diagnostics: &BoilerDiagnostics{HeatingStatusRaw: &heating},
	}})
	pin = append(pin, oracleMCPCall(t, boilerServer, "ebus.v1.semantic.boiler_status.get/boiler-fixture", "the boiler status of the pin's MCP boiler case", "ebus.v1.semantic.boiler_status.get", map[string]any{}))

	adapterServer := oracleMCPServer(t, testSemanticProvider{adapterInfo: &AdapterHardwareInfo{
		FirmwareVersion: "1.2.3", HardwareID: "deadbeef", HardwareConfig: "c0ffee", JumperFlags: []string{"JP1", "JP2"},
		TemperatureC: floatPtr(24.5), SupplyVoltageMV: intPtr(2500), BusVoltageMaxDV: intPtr(150), BusVoltageMinDV: intPtr(130),
		ResetCause: stringPtr("power_on"), ResetCauseCode: bytePtr(0x04), RestartCount: bytePtr(0x07), WiFiRSSIDBm: intPtr(-62),
		LastIdentityQuery: stringPtr("2026-03-12T13:00:00Z"), LastTelemetryQuery: stringPtr("2026-03-12T13:01:00Z"),
		VersionResponseLen: 8, InfoSupported: true,
	}})
	pin = append(pin, oracleMCPCall(t, adapterServer, "ebus.v1.semantic.adapter_info.get/adapter-fixture", "the adapter hardware info of the pin's TestServer_SnapshotConsistencyAdapterInfo", "ebus.v1.semantic.adapter_info.get", map[string]any{}))

	emptyZones := oracleMCPServer(t, testSemanticProvider{zones: []Zone{}, zonesPublished: true})
	pin = append(pin, oracleMCPCall(t, emptyZones, "ebus.v1.semantic.zones.get/empty-published", "the pin's empty zones case", "ebus.v1.semantic.zones.get", map[string]any{}))
	emptyCircuits := oracleMCPServer(t, testSemanticProvider{circuits: []CircuitStatus{}, circuitsPublished: true})
	pin = append(pin, oracleMCPCall(t, emptyCircuits, "ebus.v1.semantic.circuits.get/empty-published", "the pin's empty circuits case", "ebus.v1.semantic.circuits.get", map[string]any{}))

	writerServer := oracleMCPServer(t, nil)
	scheduleWriter := &oracleMCPScheduleWriter{
		result: &TimeProgramWriteResult{Success: true, SlotResults: []TimeProgramSlotResult{{SlotIndex: 0, Accepted: true, ErrorCode: 0, ErrorDesc: "accepted"}}},
	}
	configWriter := &oracleMCPConfigWriter{}
	noWriter := oracleMCPServer(t, nil)
	writes = append(writes, oracleMCPCall(t, noWriter, "ebus.v1.semantic.schedules.set_zone_time_program/no-writer", "the pin's TestScheduleWriteNoWriter", "ebus.v1.semantic.schedules.set_zone_time_program", map[string]any{"zone": 0, "weekday": 0, "slots": []any{}}))
	writes = append(writes, oracleMCPCall(t, noWriter, "ebus.v1.semantic.system.set_config/no-writer", "server without a config writer", "ebus.v1.semantic.system.set_config", map[string]any{"field": "maxRoomHumidity", "value": "70"}))
	writerServer.SetScheduleWriter(scheduleWriter)
	writerServer.SetConfigWriter(configWriter)
	writes = append(writes, oracleMCPCall(t, writerServer, "ebus.v1.semantic.schedules.set_zone_time_program/success", "the pin's TestScheduleWriteZoneSuccess", "ebus.v1.semantic.schedules.set_zone_time_program", map[string]any{
		"zone": 1, "weekday": 3, "slots": []any{map[string]any{"start_hour": 6, "start_minute": 0, "end_hour": 22, "end_minute": 0, "temperature_c": 21.5}},
	}))
	writes = append(writes, oracleMCPCall(t, writerServer, "ebus.v1.semantic.schedules.set_dhw_time_program/success", "the pin's TestScheduleWriteDhwSuccess", "ebus.v1.semantic.schedules.set_dhw_time_program", map[string]any{
		"weekday": 5, "slots": []any{map[string]any{"start_hour": 5, "start_minute": 30, "end_hour": 23, "end_minute": 0}},
	}))
	writes = append(writes, oracleMCPCall(t, writerServer, "ebus.v1.semantic.schedules.set_zone_time_program/missing-temperature", "the pin's TestScheduleWriteZoneMissingTemp", "ebus.v1.semantic.schedules.set_zone_time_program", map[string]any{
		"zone": 1, "weekday": 3, "slots": []any{map[string]any{"start_hour": 6, "start_minute": 0, "end_hour": 22, "end_minute": 0}},
	}))
	writes = append(writes, oracleMCPCall(t, writerServer, "ebus.v1.semantic.system.set_config/success", "a config writer that accepts", "ebus.v1.semantic.system.set_config", map[string]any{"field": "maxRoomHumidity", "value": "70"}))
	writes = append(writes, oracleMCPCall(t, writerServer, "ebus.v1.semantic.boiler_status.set_config/success", "a config writer that accepts", "ebus.v1.semantic.boiler_status.set_config", map[string]any{"field": "flowsetHcMaxC", "value": "55"}))
	writes = append(writes, oracleMCPCall(t, writerServer, "ebus.v1.semantic.system.set_config/field-missing", "a call without a field", "ebus.v1.semantic.system.set_config", map[string]any{"value": "70"}))

	document := map[string]any{
		"format":                "helianthus-oracle-pre-port-typed-mcp/1",
		"description":           "semantic tools of the pre-port MCP server; the envelope's data_timestamp is the host wall clock and is not recorded",
		"complete":              complete,
		"pin_cases":             pin,
		"write_cases":           writes,
		"config_writer_calls":   configWriter.calls,
		"schedule_writer_calls": scheduleWriter.calls,
	}
	encoded, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, "mcp-typed-tools.json"), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
