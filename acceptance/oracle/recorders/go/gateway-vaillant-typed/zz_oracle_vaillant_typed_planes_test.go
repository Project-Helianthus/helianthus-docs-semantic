package main

import (
	"errors"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-ebusgateway/mcp"
	"github.com/Project-Helianthus/helianthus-ebusgo/transport"
)

func oracleRadio(t *testing.T) {
	// Radio devices carry the identifiers the bus transmits (device model,
	// firmware and hardware identifier), so these cases are indexed by digest.
	devices := []*vaillantRadioDeviceSnapshot{
		{
			Group: 0x09, Instance: 0x00, SlotMode: "paired", DeviceConnected: qv07B(true), DeviceClassAddress: qv07U8(0x15), DeviceModel: "SYN-RC-1",
			FirmwareVersion: qv07S("1.2.3"), HardwareIdentifier: qv07U16(0x1234), RemoteControlAddress: qv07U8(0x10), DevicePaired: qv07B(true),
			ReceptionStrength: qv07U8(4), ZoneAssignment: qv07U8(1), RoomTemperatureC: qv07F(21.25), RoomHumidityPct: qv07F(47),
		},
		nil,
		{Group: 0x0A, Instance: 0x01, SlotMode: "free", DeviceConnected: qv07B(false), DeviceModel: "SYN-RC-2"},
	}
	{
		env := newQV07Env(t)
		state := map[string]any{"radio_devices": qv07Native(t, devices)}
		env.decide("publish_radio_devices_live", map[string]any{"published": env.owner.publishRadioDeviceViews(devices, semanticSnapshotSourceLive)})
		env.finish("radio/radio-devices-identifiers-live", []string{qv07ViewsFile, qv07ProviderFile}, "synthetic native radio devices over radioDeviceFromSnapshot", state, map[string]any{"source": "live", "identifier_bearing": true}, "radio")
	}
	{
		env := newQV07Env(t)
		state := map[string]any{"radio_devices": qv07Native(t, devices)}
		env.decide("publish_radio_devices_live", map[string]any{"published": env.owner.publishRadioDeviceViews(devices, semanticSnapshotSourceLive)})
		env.decide("publish_empty_radio_devices_cache", map[string]any{"published": env.owner.publishRadioDeviceViews(nil, semanticSnapshotSourceCache), "devices_published": len(env.provider.RadioDevices())})
		env.decide("publish_empty_radio_devices_live", map[string]any{"published": env.owner.publishRadioDeviceViews(nil, semanticSnapshotSourceLive), "devices_published": len(env.provider.RadioDevices())})
		env.finish("radio/radio-devices-empty-cache-keeps-published", []string{qv07ViewsFile}, "synthetic native radio devices over publishRadioDeviceViews", state, map[string]any{"sources": []any{"live", "cache", "live"}, "identifier_bearing": true}, "radio")
	}
}

func qv07FM5ViewState(view vaillantFM5View) map[string]any {
	return map[string]any{"verdict": view.verdict, "solar": view.solar, "cylinders": view.cylinders}
}

func oracleFM5(t *testing.T) {
	solar := &vaillantSolarSnapshot{
		CollectorTemperatureC: qv07F(68.5), ReturnTemperatureC: qv07F(41.25), PumpActive: qv07B(true), CurrentYield: qv07F(3.75),
		PumpHours: qv07U32(2200), SolarEnabled: qv07B(true), FunctionMode: qv07B(false),
	}
	cylinders := map[byte]*vaillantCylinderSnapshot{
		2: {Instance: 2, TemperatureC: qv07F(55), MaxSetpointC: qv07F(75), ChargeHysteresis: qv07F(5), ChargeOffset: qv07F(8)},
		0: {Instance: 0, TemperatureC: qv07F(48.5), MaxSetpointC: qv07F(70)},
		1: {Instance: 1, MaxSetpointC: qv07F(60)},
	}
	interpreted := vaillantFM5Interpretation{Mode: vaillantFM5ModeInterpreted, EvidenceRevision: "synthetic-rev-1"}
	{
		env := newQV07Env(t)
		view := vaillantFM5View{verdict: interpreted, solar: solar, cylinders: cylinders}
		state := map[string]any{"fm5_view": qv07Native(t, qv07FM5ViewState(view))}
		env.owner.publishFM5View(view, semanticSnapshotSourceLive)
		env.decide("publish_fm5_live", map[string]any{"gpio_only": env.owner.fm5PublishedAsGPIOOnly()})
		env.finish("fm5/fm5-interpreted-with-solar-and-cylinders", []string{qv07FM5File, qv07ProviderFile}, "synthetic native FM5 view over publishFM5View", state, map[string]any{"source": "live"}, "fm5", "solar", "cylinders")
	}
	{
		env := newQV07Env(t)
		view := vaillantFM5View{verdict: interpreted, solar: solar, cylinders: cylinders}
		state := map[string]any{"fm5_view": qv07Native(t, qv07FM5ViewState(view))}
		env.owner.publishFM5View(view, semanticSnapshotSourceCache)
		env.decide("publish_fm5_cache", map[string]any{"gpio_only": env.owner.fm5PublishedAsGPIOOnly()})
		env.finish("fm5/fm5-interpreted-published-from-cache-source", []string{qv07FM5File}, "synthetic native FM5 view over publishFM5View", state, map[string]any{"source": "cache"}, "fm5", "solar", "cylinders")
	}
	{
		env := newQV07Env(t)
		view := vaillantFM5View{verdict: vaillantFM5Interpretation{Mode: vaillantFM5ModeGPIOOnly, DegradedReason: vaillantFM5DegradedConfigurationNotInterpretable, EvidenceRevision: "synthetic-rev-2"}, solar: solar, cylinders: cylinders}
		state := map[string]any{"fm5_view": qv07Native(t, qv07FM5ViewState(view))}
		env.owner.publishFM5View(view, semanticSnapshotSourceLive)
		env.decide("publish_fm5_live", map[string]any{"gpio_only": env.owner.fm5PublishedAsGPIOOnly(), "structural_withdrawal": isFM5StructuralWithdrawal(view.verdict)})
		env.finish("fm5/fm5-gpio-only-structural-withdrawal", []string{qv07FM5File}, "synthetic native FM5 view over publishFM5View", state, map[string]any{"source": "live"}, "fm5", "solar", "cylinders")
	}
	{
		env := newQV07Env(t)
		view := vaillantFM5View{verdict: vaillantFM5Interpretation{Mode: vaillantFM5ModeAbsent, EvidenceRevision: "synthetic-rev-3"}}
		state := map[string]any{"fm5_view": qv07Native(t, qv07FM5ViewState(view))}
		env.owner.publishFM5View(view, semanticSnapshotSourceLive)
		env.decide("publish_fm5_live", map[string]any{"gpio_only": env.owner.fm5PublishedAsGPIOOnly()})
		env.finish("fm5/fm5-absent-without-solar-and-cylinders", []string{qv07FM5File}, "synthetic native FM5 view over publishFM5View", state, map[string]any{"source": "live"}, "fm5", "solar", "cylinders")
	}
	{
		env := newQV07Env(t)
		degraded := vaillantFM5Interpretation{Mode: vaillantFM5ModeInterpreted, DegradedReason: vaillantFM5DegradedEvidenceStale, EvidenceRevision: "synthetic-rev-4"}
		outside := vaillantFM5Interpretation{Mode: vaillantFM5Mode("OUTSIDE_NATIVE_SET"), EvidenceRevision: "synthetic-rev-5"}
		views := []vaillantFM5View{{verdict: degraded, solar: solar}, {verdict: outside, solar: solar}}
		state := map[string]any{"fm5_views": []any{qv07Native(t, qv07FM5ViewState(views[0])), qv07Native(t, qv07FM5ViewState(views[1]))}}
		env.owner.publishFM5View(views[0], semanticSnapshotSourceLive)
		env.decide("publish_fm5_degraded_live", map[string]any{"mapped": qv07Native(t, publishedFM5Interpretation(views[0].verdict))})
		env.owner.publishFM5View(views[1], semanticSnapshotSourceLive)
		env.decide("publish_fm5_outside_native_set_live", map[string]any{"mapped": qv07Native(t, publishedFM5Interpretation(views[1].verdict))})
		env.finish("fm5/fm5-verdict-outside-native-set-keeps-previous", []string{qv07FM5File}, "synthetic native FM5 view over publishFM5View", state, map[string]any{"sources": []any{"live", "live"}}, "fm5", "solar", "cylinders")
	}
	{
		env := newQV07Env(t)
		env.owner.publishStartupPlaneDefaults()
		env.decide("publish_startup_plane_defaults", map[string]any{})
		env.finish("solar/startup-plane-defaults-empty", []string{qv07OwnerFile}, "publishStartupPlaneDefaults on an empty provider", map[string]any{}, nil, "circuits", "solar", "cylinders")
	}
}

func oracleEnergy(t *testing.T) {
	{
		env := newQV07Env(t)
		ref := qv07Clock
		env.decide("energy_reference_time", map[string]any{"value": env.owner.energyReferenceTime().Format("2006-01-02T15:04:05Z07:00")})
		env.decide("apply_lifetime_gas_hot_water", map[string]any{"accepted": env.owner.applyLifetimeEnergy("gas", "hot_water", 321)})
		env.decide("apply_window_electricity_climate_month_current", map[string]any{"accepted": env.owner.applyWindowEnergy("electricity", "climate", "month", "current", ref.AddDate(0, -1, 10), 45)})
		state := map[string]any{"applied": []any{
			map[string]any{"kind": "lifetime", "channel": "gas", "usage": "hot_water", "kwh": 321},
			map[string]any{"kind": "window", "channel": "electricity", "usage": "climate", "period": "month", "label": "current", "ref": ref.AddDate(0, -1, 10).Format("2006-01-02T15:04:05Z07:00"), "kwh": 45},
		}}
		env.finish("energy/energy-owner-lifetime-and-window-keys", []string{qv07OwnerFile, qv07ProviderFile}, "synthetic energy values over the owner's lifetime and window keys, following the provider-value key test of cmd/gateway/vaillant_semantic_publication_views_test.go", state, map[string]any{"provider_clock": qv07Clock.Format("2006-01-02T15:04:05Z07:00")}, "energy")
	}
	{
		env := newQV07Env(t)
		const failedQuery = 6
		reads := 0
		queries := []any{}
		acquireEnergy(env.owner, func(q b524EnergyQuery, ref time.Time) (uint32, bool) {
			reads++
			ok := reads-1 != failedQuery
			queries = append(queries, map[string]any{"channel": q.channel, "usage": q.usage, "period": q.period, "label": q.yearKind, "reply": 1000 + reads, "answered": ok, "ref": ref.Format("2006-01-02T15:04:05Z07:00")})
			return uint32(1000 + reads), ok
		})
		env.decide("acquire_energy", map[string]any{"reads": reads})
		env.finish("energy/energy-acquisition-every-query", []string{qv07OwnerFile, qv07ProviderFile}, "inputs of the energy acquisition test of cmd/gateway/vaillant_semantic_publication_views_test.go, applied to the owner's energy keys", map[string]any{"queries": queries}, map[string]any{"provider_clock": qv07Clock.Format("2006-01-02T15:04:05Z07:00"), "failed_query_index": failedQuery}, "energy")
	}
}

func qv07ScheduleNative() []vaillantScheduleProgram {
	return []vaillantScheduleProgram{
		{
			Zone: 2, HC: "heating",
			Config:    &vaillantScheduleConfig{MaxSlots: 3, TimeResolution: 10, MinDuration: 20, HasTemperature: true, TempSlots: 4, MinTempC: qv07F(11), MaxTempC: qv07F(29)},
			SlotsUsed: []int{1, 2, 0, 0, 0, 0, 3},
			Days: []vaillantScheduleDay{
				{Weekday: "Monday", Slots: []vaillantScheduleTimerSlot{{StartHour: 5, StartMinute: 30, EndHour: 21, EndMinute: 45, TemperatureC: qv07F(21.5), TemperatureRaw: qv07I(215)}}},
				{Weekday: "Tuesday"},
			},
		},
		{Zone: 255, HC: "dhw"},
	}
}

func oracleSchedules(t *testing.T) {
	{
		env := newQV07Env(t)
		native := qv07ScheduleNative()
		state := map[string]any{"programs": qv07Native(t, native)}
		env.owner.publishSchedulePrograms(native)
		env.decide("publish_schedule_programs", map[string]any{})
		env.finish("schedules/schedules-programs-every-field", []string{qv07SchedFile, qv07ProviderFile}, qv07SchedTest+" TestVaillantPublicationOwnerMapsNativeSchedulePrograms", state, nil, "schedules")
	}
	{
		env := newQV07Env(t)
		days := func() []vaillantScheduleDay {
			return []vaillantScheduleDay{{Weekday: "Monday"}, {Weekday: "Tuesday"}, {Weekday: "Wednesday"}}
		}
		programs := []vaillantScheduleProgram{
			{Zone: 1, HC: "heating", SlotsUsed: []int{0, 0, 0}, Days: days()},
			{Zone: 0, HC: "cooling", SlotsUsed: []int{0, 0, 0}, Days: days()},
			{Zone: 0, HC: "heating", SlotsUsed: []int{0, 0, 0}, Days: days()},
		}
		written := vaillantScheduleTimerSlot{StartHour: 6, StartMinute: 15, EndHour: 22, EndMinute: 50, TemperatureC: qv07F(19.5), TemperatureRaw: qv07I(195)}
		state := map[string]any{"programs": qv07Native(t, programs), "days": []any{
			map[string]any{"zone": 0, "hc": "heating", "weekday": 0, "day": "before programs", "slots_used": []int{1}},
			map[string]any{"zone": 0, "hc": "heating", "weekday": 2, "day": qv07Native(t, vaillantScheduleDay{Weekday: "Wednesday", Slots: []vaillantScheduleTimerSlot{written}}), "slots_used": []int{0, 0, 1}},
			map[string]any{"zone": 0, "hc": "heating", "weekday": 0, "day": qv07Native(t, vaillantScheduleDay{Weekday: "Monday"}), "slots_used": nil},
			map[string]any{"zone": 0, "hc": "heating", "weekday": 5, "day": qv07Native(t, vaillantScheduleDay{Weekday: "Saturday"}), "slots_used": []int{4}},
		}}
		env.owner.publishScheduleDay(0, "heating", 0, vaillantScheduleDay{Weekday: "Monday"}, []int{1})
		env.decide("publish_schedule_day_without_schedules", map[string]any{"schedules_published": env.provider.Schedules() != nil})
		env.owner.publishSchedulePrograms(programs)
		env.owner.publishScheduleDay(0, "heating", 2, vaillantScheduleDay{Weekday: "Wednesday", Slots: []vaillantScheduleTimerSlot{written}}, []int{0, 0, 1})
		env.decide("publish_schedule_day_matching_program", map[string]any{})
		env.owner.publishScheduleDay(0, "heating", 0, vaillantScheduleDay{Weekday: "Monday"}, nil)
		env.decide("publish_schedule_day_unread_slot_count", map[string]any{})
		env.owner.publishScheduleDay(0, "heating", 5, vaillantScheduleDay{Weekday: "Saturday"}, []int{4})
		env.decide("publish_schedule_day_out_of_range_weekday", map[string]any{})
		env.finish("schedules/schedules-day-replacement-by-zone-and-hc", []string{qv07SchedFile, qv07ProviderFile}, qv07SchedTest+" TestVaillantPublicationOwnerPublishesScheduleDayForMatchingProgram", state, nil, "schedules")
	}
	{
		env := newQV07Env(t)
		beforeGraphQL, beforeMCP := qv07Capture(t, env.provider, "schedules")
		env.decide("capture_before_startup_schedule_placeholder", map[string]any{"graphql": beforeGraphQL, "mcp": beforeMCP})
		env.owner.publishStartupSchedulePlaceholder()
		placeholderGraphQL, placeholderMCP := qv07Capture(t, env.provider, "schedules")
		env.decide("publish_startup_schedule_placeholder", map[string]any{"graphql": placeholderGraphQL, "mcp": placeholderMCP})
		env.owner.publishSchedulePrograms(nil)
		env.decide("publish_schedule_programs_nil", map[string]any{})
		env.finish("schedules/schedules-startup-placeholder-and-nil-programs", []string{qv07OwnerFile, qv07SchedFile}, "publishStartupSchedulePlaceholder and publishSchedulePrograms with no programs", map[string]any{}, nil, "schedules")
	}
}

// oracleScheduleWrites records the two schedule mappings of the writer
// adapters: the MCP slots of a time-program request to native slots, and the
// native write result to its MCP form.
func oracleScheduleWrites(t *testing.T) {
	slots := [][]mcp.TimeProgramSlot{
		nil,
		{},
		{
			{StartHour: 6, StartMinute: 15, EndHour: 8, EndMinute: 0, TemperatureC: qv07F(21.5)},
			{StartHour: 17, StartMinute: 30, EndHour: 24, EndMinute: 0},
		},
	}
	mapped := []any{}
	for _, in := range slots {
		mapped = append(mapped, map[string]any{"mcp_slots": qv07Native(t, in), "native_slots": qv07Native(t, timeProgramSlotsFromMCP(in))})
	}
	failure := errors.New("synthetic write failure")
	results := []struct {
		name   string
		result *vaillantTimeProgramWriteResult
		err    error
	}{
		{"nil_result_nil_error", nil, nil},
		{"nil_result_with_error", nil, failure},
		{"success_without_slot_results", &vaillantTimeProgramWriteResult{Success: true}, nil},
		{"slot_results_with_rejection", &vaillantTimeProgramWriteResult{Success: false, Error: "slot rejected", SlotResults: []vaillantTimeProgramSlotResult{
			{SlotIndex: 0, Accepted: true, ErrorCode: 0},
			{SlotIndex: 1, Accepted: false, ErrorCode: 3, ErrorDesc: "synthetic description"},
		}}, failure},
	}
	outcomes := []any{}
	state := []any{}
	for _, item := range results {
		got, err := mcpTimeProgramWriteResult(item.result, item.err)
		state = append(state, map[string]any{"name": item.name, "native_result": qv07Native(t, item.result), "error": errText(item.err)})
		outcomes = append(outcomes, map[string]any{"name": item.name, "mcp_result": qv07Native(t, got), "error": errText(err)})
	}
	qv07Write(t, "schedules/schedule-write-mappings", qv07Case{
		Component: "cmd/gateway vaillant typed publication",
		Source:    []string{qv07SchedFile},
		Stimulus:  "synthetic MCP slots and native write results over timeProgramSlotsFromMCP and mcpTimeProgramWriteResult",
		Input:     qv07Input{State: map[string]any{"slot_requests": qv07Native(t, slots), "write_results": state}},
		Output:    qv07Output{Decisions: mapped, MCP: map[string]any{"write_results": outcomes}},
	})
}

func errText(err error) any {
	if err == nil {
		return nil
	}
	return err.Error()
}

func oracleAdapter(t *testing.T) {
	// Adapter hardware identity: firmware, checksum and hardware identifiers
	// are identifiers, so these cases are indexed by digest.
	telemetry := vaillantAdapterInfo{
		identity: &transport.AdapterVersion{
			Version: 0x1c, Features: 0x01, Checksum: 0xbeef, Jumpers: 0x2b, BootloaderVersion: 0x03, BootloaderChecksum: 0x1234,
			HasChecksum: true, HasBootloader: true, SupportsInfo: true, IsWiFi: true, IsEthernet: false, IsHighSpeed: true, IsV31: true,
		},
		hardwareID: "SYN-HW-ID", hardwareConfig: "SYN-HW-CONFIG", temperatureC: qv07F(36.5), supplyMV: qv07I(3310), busMaxDV: qv07I(205), busMinDV: qv07I(190),
		resetCause: qv07S("power_on"), resetCode: qv07U8(1), restartCount: qv07U8(7), wifiRSSI: qv07I(-61),
		lastIdentity: qv07Clock, lastTelemetry: qv07Clock.Add(30e9),
	}
	state := func(info vaillantAdapterInfo) map[string]any {
		return map[string]any{"adapter_info": map[string]any{
			"identity": info.identity, "hardware_id": info.hardwareID, "hardware_config": info.hardwareConfig, "temperature_c": info.temperatureC,
			"supply_mv": info.supplyMV, "bus_max_dv": info.busMaxDV, "bus_min_dv": info.busMinDV, "reset_cause": info.resetCause, "reset_code": info.resetCode,
			"restart_count": info.restartCount, "wifi_rssi": info.wifiRSSI, "last_identity": info.lastIdentity, "last_telemetry": info.lastTelemetry,
		}}
	}
	{
		env := newQV07Env(t)
		env.owner.publishAdapterInfo(telemetry)
		env.decide("publish_adapter_info", map[string]any{})
		env.finish("adapter-hardware/adapter-hardware-info-full-identity", []string{qv07OwnerFile, qv07ProviderFile}, "synthetic native adapter hardware value over publishAdapterInfo", map[string]any{"native": qv07Native(t, state(telemetry))}, map[string]any{"identifier_bearing": true}, "adapter")
	}
	{
		env := newQV07Env(t)
		minimal := vaillantAdapterInfo{hardwareID: "SYN-HW-ID", temperatureC: qv07F(20.5)}
		env.owner.publishAdapterInfo(minimal)
		env.decide("publish_adapter_info", map[string]any{})
		env.finish("adapter-hardware/adapter-hardware-info-without-identity", []string{qv07OwnerFile, qv07ProviderFile}, "synthetic native adapter hardware value over publishAdapterInfo", map[string]any{"native": qv07Native(t, state(minimal))}, map[string]any{"identifier_bearing": true}, "adapter")
	}
	{
		env := newQV07Env(t)
		checksumOnly := vaillantAdapterInfo{identity: &transport.AdapterVersion{Version: 0x10, Checksum: 0x00ff, HasChecksum: true, Jumpers: 0x04, IsEthernet: true}}
		env.owner.publishAdapterInfo(checksumOnly)
		env.decide("publish_adapter_info", map[string]any{})
		env.finish("adapter-hardware/adapter-hardware-info-checksum-without-bootloader", []string{qv07OwnerFile, qv07ProviderFile}, "synthetic native adapter hardware value over publishAdapterInfo", map[string]any{"native": qv07Native(t, state(checksumOnly))}, map[string]any{"identifier_bearing": true}, "adapter")
	}
}
