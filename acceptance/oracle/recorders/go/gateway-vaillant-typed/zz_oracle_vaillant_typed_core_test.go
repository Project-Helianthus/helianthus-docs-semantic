package main

import (
	"testing"

	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/vaillant/systemconfig"
	"github.com/Project-Helianthus/helianthus-ebusreg/vaillant/productids"
)

// TestOracleVaillantTyped records the typed GraphQL and MCP outputs of the
// Vaillant publication owner and the semantic cache of the pin.
func TestOracleVaillantTyped(t *testing.T) {
	oracleZones(t)
	oracleDhw(t)
	oracleCircuits(t)
	oracleManagingDevice(t)
	oracleBoiler(t)
	oracleSystem(t)
	oracleRadio(t)
	oracleFM5(t)
	oracleEnergy(t)
	oracleSchedules(t)
	oracleScheduleWrites(t)
	oracleAdapter(t)
	oracleCache(t)
}

func qv07ZoneViewState(views []vaillantZoneView) []any {
	out := make([]any, 0, len(views))
	for _, view := range views {
		out = append(out, map[string]any{
			"instance":                  int(view.instance),
			"snapshot":                  view.snapshot,
			"radio_room_temp_c":         view.radioRoomTempC,
			"radio_room_humidity_pct":   view.radioRoomHumidityPct,
			"inferred_room_mapping_raw": view.inferredRoomMappingRaw,
		})
	}
	return out
}

func oracleZones(t *testing.T) {
	// Native zone views as the pin's own test builds them from a poller: the
	// zone without values of its own takes the radio room state and the
	// inferred room mapping.
	{
		env := newQV07Env(t)
		connected := true
		poller := &vaillantSemanticPoller{
			radioDevices: map[radioDeviceKey]*vaillantRadioDeviceSnapshot{
				{Group: remoteThermostats.group, Instance: 0x02}: {
					Group: remoteThermostats.group, Instance: 0x02, DeviceConnected: &connected,
					ZoneAssignment: qv07U8(2), RoomTemperatureC: qv07F(20.5), RoomHumidityPct: qv07F(44.0),
				},
			},
			zones: map[byte]*vaillantZoneSnapshot{
				0x01: {Instance: 0x01, Present: true, Name: "Upstairs", AllowedModes: []string{"auto"}},
				0x00: {Instance: 0x00, Present: true, CurrentTempC: qv07F(22.0), HumidityPct: qv07F(51.0), ConfigurationRoomTemperatureZoneMappingRaw: qv07U16(0)},
			},
		}
		poller.mu.Lock()
		views := poller.zoneViewsLocked()
		poller.mu.Unlock()
		pollerRadio := []any{}
		for key, device := range poller.radioDevices {
			pollerRadio = append(pollerRadio, map[string]any{"group": key.Group, "instance": key.Instance, "device": device})
		}
		state := map[string]any{
			"poller":     qv07Native(t, map[string]any{"radio_devices": pollerRadio, "zones": poller.zones}),
			"zone_views": qv07Native(t, qv07ZoneViewState(views)),
		}
		env.decide("publish_zone_views_live", map[string]any{"published": env.owner.publishZoneViews(views, semanticSnapshotSourceLive)})
		env.finish("zone/zone-views-radio-fallback", []string{qv07ViewsFile, qv07ProviderFile}, qv07ViewsTest+" TestVaillantZoneViewsDeriveRadioStateOnlyForMissingZoneValues", state, map[string]any{"source": "live"}, "zones")
	}

	// A zone with every native field: quick veto, holiday, raw decodings.
	{
		env := newQV07Env(t)
		views := []vaillantZoneView{
			{instance: 0, snapshot: &vaillantZoneSnapshot{
				Instance: 0, Present: true, Name: "Living", OperatingMode: "auto", Preset: "quickveto", HvacAction: "heating",
				AllowedModes: []string{"off", "auto", "manual"}, CurrentTempC: qv07F(21.5), TargetTempC: qv07F(22), HumidityPct: qv07F(48),
				StateSpecialFunction:                       "quick_veto",
				ConfigurationRoomTemperatureZoneMappingRaw: qv07U16(1),
				ConfigurationAssociatedCircuitRaw:          qv07U16(0),
				ConfigurationCircuitTypeRaw:                qv07U16(1),
				StateValveStatusRaw:                        qv07U16(32768),
				QuickVetoTempC:                             qv07F(23.5), QuickVetoDurationH: qv07F(3), QuickVetoEndTime: "18:30", QuickVetoEndDate: "2030-04-10",
				HolidayStartDate: "2030-12-20", HolidayEndDate: "2030-12-27", HolidaySetpointC: qv07F(15), HolidayStartTime: "08:00", HolidayEndTime: "18:30",
			}},
			{instance: 1, snapshot: &vaillantZoneSnapshot{
				Instance: 1, Present: true, Name: "  ", OperatingMode: "off", Preset: "schedule",
				ConfigurationRoomTemperatureZoneMappingRaw: qv07U16(3), ConfigurationCircuitTypeRaw: qv07U16(2), StateValveStatusRaw: qv07U16(0),
				QuickVetoEndTime: "09:00", QuickVetoEndDate: "2030-04-11",
			}},
			{instance: 2, snapshot: nil},
		}
		state := map[string]any{"zone_views": qv07Native(t, qv07ZoneViewState(views))}
		env.decide("publish_zone_views_live", map[string]any{"published": env.owner.publishZoneViews(views, semanticSnapshotSourceLive)})
		env.finish("zone/zone-views-quick-veto-holiday-and-defaults", []string{qv07ViewsFile, qv07ProviderFile}, "synthetic native zone views over zoneFromView", state, map[string]any{"source": "live"}, "zones")
	}

	// An empty cache publication never replaces published zones; an empty
	// live publication does.
	{
		env := newQV07Env(t)
		one := []vaillantZoneView{{instance: 0, snapshot: &vaillantZoneSnapshot{Instance: 0, Present: true, Name: "Kept", CurrentTempC: qv07F(19)}}}
		cached := []vaillantZoneView{{instance: 1, snapshot: &vaillantZoneSnapshot{Instance: 1, Present: true, Name: "Cached"}}}
		state := map[string]any{"steps": []any{
			map[string]any{"source": "live", "zone_views": qv07Native(t, qv07ZoneViewState(one))},
			map[string]any{"source": "cache", "zone_views": qv07Native(t, qv07ZoneViewState(nil))},
			map[string]any{"source": "cache", "zone_views": qv07Native(t, qv07ZoneViewState(cached))},
			map[string]any{"source": "live", "zone_views": qv07Native(t, qv07ZoneViewState(nil))},
		}}
		env.decide("publish_zone_views_live", map[string]any{"published": env.owner.publishZoneViews(one, semanticSnapshotSourceLive)})
		env.decide("publish_empty_zone_views_cache", map[string]any{"published": env.owner.publishZoneViews(nil, semanticSnapshotSourceCache), "zones_published": len(env.provider.Zones())})
		env.decide("publish_zone_views_cache_replacement", map[string]any{"published": env.owner.publishZoneViews(cached, semanticSnapshotSourceCache), "zones_published": len(env.provider.Zones())})
		env.decide("publish_empty_zone_views_live", map[string]any{"published": env.owner.publishZoneViews(nil, semanticSnapshotSourceLive), "zones_published": len(env.provider.Zones())})
		env.finish("zone/zone-views-empty-cache-keeps-published", []string{qv07ViewsFile}, "synthetic native zone views over publishZoneViews", state, map[string]any{"sources": []any{"live", "cache", "cache", "live"}}, "zones")
	}
}

func qv07DhwViewState(view vaillantDhwView) map[string]any {
	return map[string]any{"snapshot": view.snapshot, "expired": view.expired}
}

func oracleDhw(t *testing.T) {
	{
		env := newQV07Env(t)
		views := []vaillantDhwView{
			{snapshot: &vaillantDhwSnapshot{CurrentTempC: qv07F(48.5), OperatingMode: "auto"}},
			{},
			{expired: true},
		}
		state := map[string]any{"dhw_views": []any{qv07Native(t, qv07DhwViewState(views[0])), qv07Native(t, qv07DhwViewState(views[1])), qv07Native(t, qv07DhwViewState(views[2]))}}
		env.decide("publish_dhw_live", map[string]any{"published": env.owner.publishDhwView(views[0], semanticSnapshotSourceLive)})
		env.decide("publish_dhw_cache_without_snapshot", map[string]any{"published": env.owner.publishDhwView(views[1], semanticSnapshotSourceCache), "dhw_published": env.provider.DHW() != nil})
		env.decide("publish_dhw_cache_expired", map[string]any{"published": env.owner.publishDhwView(views[2], semanticSnapshotSourceCache), "dhw_published": env.provider.DHW() != nil})
		env.finish("dhw/dhw-live-then-expired-withdrawal", []string{qv07ViewsFile, qv07OwnerFile, qv07ProviderFile}, qv07ViewsTest+" TestVaillantPublicationOwnerPublishesCircuitAndDhwViews", state, map[string]any{"sources": []any{"live", "cache", "cache"}}, "dhw")
	}
	{
		env := newQV07Env(t)
		view := vaillantDhwView{snapshot: &vaillantDhwSnapshot{
			OperatingMode: "manual", Preset: "holiday", CurrentTempC: qv07F(52.25), TargetTempC: qv07F(55),
			StateSpecialFunction: "load", HolidayStartDate: "2030-12-20", HolidayEndDate: "2030-12-27",
		}}
		state := map[string]any{"dhw_view": qv07Native(t, qv07DhwViewState(view))}
		env.decide("publish_dhw_live", map[string]any{"published": env.owner.publishDhwView(view, semanticSnapshotSourceLive)})
		env.finish("dhw/dhw-all-fields-holiday", []string{qv07ViewsFile, qv07ProviderFile}, "synthetic native hot water view over dhwStatusFromSnapshot", state, map[string]any{"source": "live"}, "dhw")
	}
}

func qv07CircuitsViewState(view vaillantCircuitsView) map[string]any {
	return map[string]any{"circuits": view.circuits, "managed_by_function_module": view.managedByFunctionModule}
}

func oracleCircuits(t *testing.T) {
	{
		env := newQV07Env(t)
		circuitType := uint16(1)
		view := vaillantCircuitsView{
			circuits: []*vaillantCircuitSnapshot{
				{Instance: 0, Active: true, CircuitTypeRaw: &circuitType},
				{
					Instance: 1, Active: true, CircuitTypeRaw: qv07U16(2), CoolingEnabledRaw: qv07U16(1), FlowSetpointC: qv07F(35), FlowTemperatureC: qv07F(33.5),
					HeatingCurve: qv07F(1.2), FlowTempMaxC: qv07F(60), FlowTempMinC: qv07F(20), SummerLimitC: qv07F(18), RoomTempControlRaw: qv07U16(1),
					CircuitStateRaw: qv07U16(2), SpecialFunctionMode: qv07U8(3), PumpStatusRaw: qv07U16(1), CalcFlowTempC: qv07F(34), MixerPositionPct: qv07F(40),
					HumidityPct: qv07F(51), DewPointC: qv07F(11.5), PumpHoursRaw: qv07U32(1200), PumpStartsRaw: qv07U32(87),
				},
				nil,
			},
			managedByFunctionModule: true,
		}
		state := map[string]any{"circuits_views": []any{qv07Native(t, qv07CircuitsViewState(view)), qv07Native(t, qv07CircuitsViewState(vaillantCircuitsView{}))}}
		env.decide("publish_circuits_empty_live", map[string]any{"published": env.owner.publishCircuitsView(vaillantCircuitsView{}, semanticSnapshotSourceLive)})
		env.decide("publish_circuits_live", map[string]any{"published": env.owner.publishCircuitsView(view, semanticSnapshotSourceLive)})
		env.decide("publish_circuits_empty_cache", map[string]any{"published": env.owner.publishCircuitsView(vaillantCircuitsView{}, semanticSnapshotSourceCache), "circuits_published": len(env.provider.Circuits())})
		env.finish("circuits/circuits-function-module-managed", []string{qv07ViewsFile, qv07OwnerFile, qv07ProviderFile}, "synthetic native circuit views over publishCircuitsView, following "+qv07ViewsTest+" TestVaillantPublicationOwnerPublishesCircuitAndDhwViews", state, map[string]any{"sources": []any{"live", "live", "cache"}}, "circuits")
	}
	{
		env := newQV07Env(t)
		view := vaillantCircuitsView{circuits: []*vaillantCircuitSnapshot{
			{Instance: 2, Active: true, CircuitTypeRaw: qv07U16(99), PumpStatusRaw: qv07U16(0), CircuitStateRaw: qv07U16(0), RoomTempControlRaw: qv07U16(0), CoolingEnabledRaw: qv07U16(0)},
		}}
		state := map[string]any{"circuits_view": qv07Native(t, qv07CircuitsViewState(view))}
		env.decide("publish_circuits_live", map[string]any{"published": env.owner.publishCircuitsView(view, semanticSnapshotSourceLive)})
		env.finish("circuits/circuits-unmanaged-unknown-raw-values", []string{qv07ViewsFile, qv07OwnerFile}, "synthetic native circuit view over circuitStatusFromSnapshot", state, map[string]any{"source": "live"}, "circuits")
	}
}

func qv07BoilerSnapshot() *vaillantBoilerSnapshot {
	return &vaillantBoilerSnapshot{
		FlowTemperatureC: qv07F(54.5), ReturnTemperatureC: qv07F(41), CentralHeatingPumpActive: qv07B(true), WaterPressureBar: qv07F(1.6),
		ExternalPumpActive: qv07B(false), CirculationPumpActive: qv07B(true), GasValveActive: qv07B(true), FlameActive: qv07B(true),
		DiverterValvePositionPct: qv07F(100), FanSpeedRpm: qv07I(3120), TargetFanSpeedRpm: qv07I(3200), IonisationVoltageUa: qv07F(5.5),
		DhwWaterFlowLpm: qv07F(7.25), DhwDemandActive: qv07B(false), HeatingSwitchActive: qv07B(true), StorageLoadPumpPct: qv07F(65),
		ModulationPct: qv07F(35), PrimaryCircuitFlowLpm: qv07F(12.5), FlowTempDesiredC: qv07F(55), DhwTempDesiredC: qv07F(50), StateNumber: qv07I(8),
		DhwTemperatureC: qv07F(48), DhwTargetTemperatureC: qv07F(50), DhwOperatingMode: qv07I(2), FlowsetHcMaxC: qv07F(75), FlowsetHwcMaxC: qv07F(80),
		PartloadHcKW: qv07F(12), PartloadHwcKW: qv07F(24), HeatingStatusRaw: qv07I(4), DhwStatusRaw: qv07I(1), CentralHeatingHours: qv07F(4321.5),
		DhwHours: qv07F(987.25), CentralHeatingStarts: qv07I(12345), DhwStarts: qv07I(6789), PumpHours: qv07F(5000), FanHours: qv07F(4800),
		DeactivationsIFC: qv07I(3), DeactivationsTemplimiter: qv07I(1), InstallerMenuCode: qv07I(17), PhoneNumber: qv07S("0123"), HoursTillService: qv07I(2400),
	}
}

func oracleBoiler(t *testing.T) {
	{
		env := newQV07Env(t)
		snapshot := qv07BoilerSnapshot()
		state := map[string]any{"boiler_snapshot": qv07Native(t, snapshot)}
		env.decide("publish_boiler_live", map[string]any{"published": env.owner.publishBoilerStatusView(snapshot, semanticSnapshotSourceLive)})
		env.finish("boiler/boiler-status-all-fields", []string{qv07ViewsFile, qv07ProviderFile}, "synthetic native boiler snapshot over boilerStatusFromSnapshot", state, map[string]any{"source": "live"}, "boiler")
	}
	{
		env := newQV07Env(t)
		snapshot := &vaillantBoilerSnapshot{FlowTemperatureC: qv07F(54.5), WaterPressureBar: qv07F(1.6), PhoneNumber: qv07S("0123"), DhwOperatingMode: qv07I(2)}
		state := map[string]any{"boiler_snapshot": qv07Native(t, snapshot)}
		env.decide("publish_boiler_missing_snapshot", map[string]any{"published": env.owner.publishBoilerStatusView(nil, semanticSnapshotSourceLive), "status_published": env.provider.BoilerStatus() != nil})
		env.decide("publish_boiler_live", map[string]any{"published": env.owner.publishBoilerStatusView(snapshot, semanticSnapshotSourceLive)})
		env.owner.withdrawBoilerFlowTemperature()
		env.decide("withdraw_boiler_flow_temperature", map[string]any{"flow_published": env.provider.BoilerStatus().State.FlowTemperatureC != nil})
		env.finish("boiler/boiler-flow-temperature-withdrawal", []string{qv07ViewsFile, qv07ProviderFile}, qv07ViewsTest+" TestVaillantPublicationOwnerPublishesAndWithdrawsBoilerStatus", state, map[string]any{"source": "live"}, "boiler")
	}
	{
		env := newQV07Env(t)
		snapshot := &vaillantBoilerSnapshot{FlowTemperatureC: qv07F(40), ReturnTemperatureC: qv07F(35)}
		state := map[string]any{"boiler_snapshot": qv07Native(t, snapshot)}
		env.decide("publish_boiler_cache", map[string]any{"published": env.owner.publishBoilerStatusView(snapshot, semanticSnapshotSourceCache)})
		env.decide("publish_boiler_missing_snapshot_cache", map[string]any{"published": env.owner.publishBoilerStatusView(nil, semanticSnapshotSourceCache), "status_published": env.provider.BoilerStatus() != nil})
		env.finish("boiler/boiler-missing-snapshot-withdraws-published", []string{qv07ViewsFile}, "synthetic native boiler snapshots over publishBoilerStatusView, following "+qv07ViewsTest+" TestVaillantPublicationOwnerPublishesAndWithdrawsBoilerStatus", state, map[string]any{"sources": []any{"cache", "cache"}}, "boiler")
	}
}

func qv07SystemViewState(view vaillantSystemView) map[string]any {
	return map[string]any{"snapshot": view.snapshot, "dhw_bivalence_bound": view.dhwBivalenceBound}
}

func oracleSystem(t *testing.T) {
	{
		env := newQV07Env(t)
		bound := systemconfig.ConfigBound{MinC: -10, MaxC: 20, Source: "profile", Profile: "synthetic", ControllerAddress: 0x15}
		view := vaillantSystemView{snapshot: &vaillantSystemSnapshot{
			Controller: 0x15, SystemOff: qv07B(false), SystemWaterPressure: qv07F(1.8), SystemFlowTemperature: qv07F(42.5), OutdoorTemperature: qv07F(7.5),
			OutdoorTemperatureAvg24h: qv07F(6.25), MaintenanceDue: qv07B(true), HwcCylinderTemperatureTop: qv07F(51), HwcCylinderTemperatureBottom: qv07F(38),
			AdaptiveHeatingCurve: qv07B(true), AlternativePoint: qv07F(-5), HeatingCircuitBivalencePoint: qv07F(-3), DhwBivalencePoint: qv07F(-2),
			HcEmergencyTemperature: qv07F(-15), HwcMaxFlowTempDesired: qv07F(65), MaxRoomHumidity: qv07U16(70), MaintenanceDate: qv07S("2031-01-15"),
			InstallerName: qv07S("Synthetic Installer"), InstallerPhone: qv07S("0123"), InstallerMenuCode: qv07U16(17), SystemScheme: qv07U16(3), ModuleConfigurationVR71: qv07U16(2),
		}, dhwBivalenceBound: bound}
		state := map[string]any{"system_view": qv07Native(t, qv07SystemViewState(view))}
		env.decide("publish_system_live", map[string]any{"published": env.owner.publishSystemView(view, semanticSnapshotSourceLive)})
		env.finish("system/system-view-all-fields-with-bound", []string{qv07ViewsFile, qv07OwnerFile, qv07ProviderFile}, "synthetic native system view over systemStatusFromView", state, map[string]any{"source": "live"}, "system")
	}
	{
		env := newQV07Env(t)
		view := vaillantSystemView{snapshot: &vaillantSystemSnapshot{OutdoorTemperature: qv07F(7.5), SystemScheme: qv07U16(3)}, dhwBivalenceBound: systemconfig.ConfigBound{MinC: -10, MaxC: 20, Source: "profile", Profile: "synthetic", ControllerAddress: 0x15}}
		state := map[string]any{"system_views": []any{qv07Native(t, qv07SystemViewState(view)), qv07Native(t, qv07SystemViewState(vaillantSystemView{}))}}
		env.decide("publish_system_live", map[string]any{"published": env.owner.publishSystemView(view, semanticSnapshotSourceLive)})
		env.decide("publish_system_without_snapshot_cache", map[string]any{"published": env.owner.publishSystemView(vaillantSystemView{}, semanticSnapshotSourceCache), "status_published": env.provider.System() != nil})
		env.finish("system/system-view-without-snapshot-withdraws", []string{qv07ViewsFile}, "synthetic native system views over publishSystemView, following "+qv07ViewsTest+" TestVaillantPublicationOwnerPublishesSystemView", state, map[string]any{"sources": []any{"live", "cache"}}, "system")
	}
	{
		env := newQV07Env(t)
		steps := []any{}
		natives := []any{}
		for _, capability := range []struct {
			name  string
			value productids.ControllerCapability
		}{{"present", productids.ControllerPresent}, {"none", productids.ControllerNone}, {"unrecognised", productids.ControllerCapability(99)}} {
			natives = append(natives, map[string]any{"name": capability.name, "native_value": int(capability.value)})
			env.owner.publishRegulatorCapability(capability.value)
			gql, _ := qv07Capture(t, env.provider, "capability")
			steps = append(steps, map[string]any{
				"native": capability.name, "published": string(env.provider.VaillantRegulatorCapability()),
				"graphql": gql, "mcp": qv07CapabilityMCP(t, env.provider),
			})
		}
		env.decide("publish_regulator_capability", map[string]any{"mapped": steps})
		env.finish("system/regulator-capability-mapping", []string{qv07ViewsFile}, "synthetic native controller capabilities over publishRegulatorCapability, read through the pin's GraphQL root and MCP runtime status tools after each step", map[string]any{"capabilities": natives}, nil, "capability")
	}
}

// oracleManagingDevice records the managing device that the owner derives for a
// circuit from the native system snapshot and the FM5 mode: every pairing of the
// system scheme, the function module configuration and the FM5 mode.
func oracleManagingDevice(t *testing.T) {
	type pairing struct {
		scheme, module *uint16
		mode           vaillantFM5Mode
	}
	var pairings []pairing
	for _, scheme := range []*uint16{nil, qv07U16(0), qv07U16(1)} {
		for _, module := range []*uint16{nil, qv07U16(0), qv07U16(2)} {
			for _, mode := range []vaillantFM5Mode{"", vaillantFM5ModeInterpreted, vaillantFM5ModeGPIOOnly, vaillantFM5ModeAbsent} {
				pairings = append(pairings, pairing{scheme, module, mode})
			}
		}
	}
	inputs := []any{}
	results := []any{}
	for _, item := range pairings {
		system := &vaillantSystemSnapshot{SystemScheme: item.scheme, ModuleConfigurationVR71: item.module}
		inputs = append(inputs, map[string]any{"system_scheme": item.scheme, "module_configuration_vr71": item.module, "fm5_mode": string(item.mode)})
		results = append(results, qv07Native(t, map[string]any{"managed_by_function_module": circuitsManagedByFunctionModule(system, item.mode), "managing_device": deriveCircuitManagingDevice(system, item.mode)}))
	}
	inputs = append(inputs, map[string]any{"system_snapshot": nil, "fm5_mode": string(vaillantFM5ModeInterpreted)})
	results = append(results, qv07Native(t, map[string]any{"managed_by_function_module": circuitsManagedByFunctionModule(nil, vaillantFM5ModeInterpreted), "managing_device": deriveCircuitManagingDevice(nil, vaillantFM5ModeInterpreted)}))
	qv07Write(t, "circuits/circuit-managing-device-derivation", qv07Case{
		Component: "cmd/gateway vaillant typed publication",
		Source:    []string{qv07OwnerFile, "cmd/gateway/semantic_vaillant_circuits.go"},
		Stimulus:  "synthetic native system snapshots and FM5 modes over deriveCircuitManagingDevice",
		Input:     qv07Input{State: map[string]any{"pairings": inputs}},
		Output:    qv07Output{Decisions: results},
	})
}
