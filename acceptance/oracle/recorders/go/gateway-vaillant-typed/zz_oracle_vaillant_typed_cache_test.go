package main

import (
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-ebusgateway/graphql"
)

const qv07CachePath = "semantic-cache.json"

// qv07InTempDir runs fn in an empty scratch directory so that the cache path
// is the fixed relative name above and no host path enters a record.
func qv07InTempDir(t *testing.T, fn func()) {
	t.Helper()
	previous, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(t.TempDir()); err != nil {
		t.Fatal(err)
	}
	defer func() {
		if err := os.Chdir(previous); err != nil {
			t.Fatal(err)
		}
	}()
	fn()
}

type qv07Logs struct{ lines []any }

func (l *qv07Logs) printf(format string, args ...any) {
	l.lines = append(l.lines, fmt.Sprintf(format, args...))
}

func qv07Store(logs *qv07Logs) *semanticCacheStore {
	store := newSemanticCacheStore(qv07CachePath, logs.printf)
	store.now = func() time.Time { return qv07Clock }
	return store
}

func qv07ReadCache(t *testing.T) string {
	t.Helper()
	data, err := os.ReadFile(qv07CachePath)
	if err != nil {
		t.Fatal(err)
	}
	return string(data)
}

func qv07Hydration(t *testing.T, hydration vaillantCacheHydration) any {
	return qv07Native(t, map[string]any{"zones": hydration.zones, "dhw": hydration.dhw, "persisted_at": hydration.persistedAt, "boiler": hydration.boiler})
}

func qv07CacheSnapshot() semanticCacheSnapshot {
	boiler := qv07BoilerSnapshot()
	return semanticCacheSnapshot{
		Zones: []graphql.Zone{
			{
				ID: "zone-2", Name: "Upstairs",
				State: graphql.ZoneState{CurrentTempC: qv07F(20.5), CurrentHumidityPct: qv07F(44), HvacAction: "idle", SpecialFunction: "none", HeatingDemandPct: qv07F(10), ValvePositionPct: qv07F(50)},
				Config: graphql.ZoneConfig{
					OperatingMode: "auto", Preset: "schedule", TargetTempC: qv07F(21), AllowedModes: []string{"manual", "auto"}, CircuitType: "underfloor",
					AssociatedCircuit: qv07I(1), RoomTemperatureZoneMapping: qv07I(2), QuickVeto: true, QuickVetoSetpointC: qv07F(23), QuickVetoDurationH: qv07F(2),
					QuickVetoExpiry: "2030-04-10T10:00", HolidayStartDate: "2030-12-20", HolidayEndDate: "2030-12-27", HolidaySetpointC: qv07F(15), HolidayStartTime: "08:00", HolidayEndTime: "18:30",
				},
			},
			{ID: "zone-1", Name: "Downstairs", State: graphql.ZoneState{CurrentTempC: qv07F(22)}, Config: graphql.ZoneConfig{OperatingMode: "manual", TargetTempC: qv07F(23)}},
		},
		DHW: &graphql.DhwStatus{
			State:  graphql.DhwState{CurrentTempC: qv07F(48.5), SpecialFunction: "load", HeatingDemandPct: qv07F(100)},
			Config: graphql.DhwConfig{OperatingMode: "auto", Preset: "schedule", TargetTempC: qv07F(55), HolidayStartDate: "2030-12-20", HolidayEndDate: "2030-12-27"},
		},
		Boiler: boilerStatusFromSnapshot(boiler),
	}
}

func oracleCache(t *testing.T) {
	// Save at the pin's clock, then Load the bytes back and seed a fresh
	// provider the way the poller start does.
	qv07InTempDir(t, func() {
		logs := &qv07Logs{}
		snapshot := qv07CacheSnapshot()
		store := qv07Store(logs)
		saveErr := store.Save(snapshot)
		bytes := qv07ReadCache(t)
		loadStore := qv07Store(logs)
		loaded, ok := loadStore.Load()
		seeded := graphql.NewLiveSemanticProvider()
		hydration, hydrated := preloadSemanticCache(seeded, loadStore)

		env := &qv07Env{t: t, provider: seeded}
		env.decide("save", map[string]any{"error": fmt.Sprint(saveErr)})
		env.decide("load", map[string]any{"ok": ok})
		env.decide("preload_semantic_cache", map[string]any{"hydrated": hydrated})
		gql, mcpRecord := qv07Capture(t, seeded, "zones", "dhw", "boiler")
		qv07Write(t, "cache/cache-save-load-seed-at-pin-clock", qv07Case{
			Component: "cmd/gateway semantic cache",
			Source:    []string{qv07CacheFile, qv07CachePubFile, qv07ProviderFile},
			Stimulus:  "synthetic cache snapshot saved and loaded, following " + qv07CacheTest + " TestSemanticCacheStoreLoad_HitLogsMarker",
			Input:     qv07Input{Bytes: "", Qualifiers: map[string]any{"cache_path": qv07CachePath}, Clock: map[string]any{"store_now": qv07Clock.Format("2006-01-02T15:04:05Z07:00")}, State: map[string]any{"snapshot": qv07Native(t, snapshot)}},
			Output: qv07Output{
				Decisions: env.decisions, GraphQL: gql, MCP: mcpRecord,
				Cache:        map[string]any{"saved_bytes": bytes, "loaded_snapshot": qv07Native(t, loaded), "hydration": qv07Hydration(t, hydration)},
				Observations: logs.lines,
			},
		})
	})

	// Save sorts the zones by ordinal and the allowed modes by name.
	qv07InTempDir(t, func() {
		logs := &qv07Logs{}
		snapshot := semanticCacheSnapshot{Zones: []graphql.Zone{
			{ID: "zone-10", Name: "Zone 10", Config: graphql.ZoneConfig{AllowedModes: []string{"heat", "off"}}},
			{ID: "zone-2", Name: "Zone 2", Config: graphql.ZoneConfig{AllowedModes: []string{"off", "heat"}}},
			{ID: "zone-1", Name: "Zone 1", Config: graphql.ZoneConfig{AllowedModes: []string{"heat", "auto"}}},
			{ID: "other", Name: "Other"},
		}}
		store := qv07Store(logs)
		saveErr := store.Save(snapshot)
		bytes := qv07ReadCache(t)
		loaded, ok := qv07Store(logs).Load()
		env := &qv07Env{t: t}
		env.decide("save", map[string]any{"error": fmt.Sprint(saveErr)})
		env.decide("load", map[string]any{"ok": ok})
		qv07Write(t, "cache/cache-save-sorts-zones-and-allowed-modes", qv07Case{
			Component: "cmd/gateway semantic cache",
			Source:    []string{qv07CacheFile},
			Stimulus:  "synthetic cache snapshot, following " + qv07CacheTest + " TestSemanticCacheStoreSave_SortsZonesAndAllowedModes",
			Input:     qv07Input{Qualifiers: map[string]any{"cache_path": qv07CachePath}, Clock: map[string]any{"store_now": qv07Clock.Format("2006-01-02T15:04:05Z07:00")}, State: map[string]any{"snapshot": qv07Native(t, snapshot)}},
			Output:    qv07Output{Decisions: env.decisions, Cache: map[string]any{"saved_bytes": bytes, "loaded_snapshot": qv07Native(t, loaded)}, Observations: logs.lines},
		})
	})

	// Load of files the pin discards or rejects, and of a missing file.
	{
		type load struct {
			name  string
			bytes *string
		}
		text := func(s string) *string { return &s }
		loads := []load{
			{"miss", nil},
			{"invalid_json", text("{not-json")},
			{"unknown_schema_version", text(`{"schema_version":99,"zones":[]}`)},
			{"schema_version_absent", text(`{"zones":[{"id":"zone-2","name":"Zone 2"},{"id":"zone-1","name":"Zone 1","allowed_modes":["heat","auto"]}],"dhw":{"operating_mode":"auto","preset":"schedule"}}`)},
			{"schema_version_1", text(`{"schema_version":1,"zones":[{"id":"zone-1","name":"Zone 1"}]}`)},
			{"schema_version_2", text(`{"schema_version":2,"metadata":{},"zones":[{"id":"zone-1","name":"Zone 1"}]}`)},
			{"schema_version_3_wrong_member_type", text(`{"schema_version":3,"zones":"not-a-list"}`)},
			{"schema_version_3_minimal", text(`{"schema_version":3,"metadata":{"persisted_at":"2030-04-10T08:00:00Z"}}`)},
			{"schema_version_3_boiler_flow_and_pumps_withheld", text(`{"schema_version":3,"metadata":{"persisted_at":"2030-04-10T08:00:00Z"},"boiler":{"flow_temperature_c":50.5,"return_temperature_c":40.25,"central_heating_pump_active":true,"dhw_temperature_c":47,"dhw_target_temperature_c":50,"dhw_operating_mode":"auto","heating_status_raw":4,"dhw_status_raw":1}}`)},
		}
		recorded := []any{}
		inputs := []any{}
		for _, item := range loads {
			qv07InTempDir(t, func() {
				logs := &qv07Logs{}
				input := map[string]any{"name": item.name, "file_present": item.bytes != nil}
				if item.bytes != nil {
					input["bytes"] = *item.bytes
					if err := os.WriteFile(qv07CachePath, []byte(*item.bytes), 0o644); err != nil {
						t.Fatal(err)
					}
				}
				inputs = append(inputs, input)
				snapshot, ok := qv07Store(logs).Load()
				hydration := cacheHydrationFromSnapshot(snapshot)
				recorded = append(recorded, map[string]any{"name": item.name, "ok": ok, "snapshot": qv07Native(t, snapshot), "hydration": qv07Hydration(t, hydration), "logs": logs.lines})
			})
		}
		qv07Write(t, "cache/cache-load-discards-rejects-and-withholds", qv07Case{
			Component: "cmd/gateway semantic cache",
			Source:    []string{qv07CacheFile, qv07CachePubFile},
			Stimulus:  "synthetic cache files, following " + qv07CacheTest + " TestSemanticCacheStoreLoad_MissLogsMarker, TestSemanticCacheStoreLoad_InvalidJSONLogsMarker, TestSemanticCacheStoreLoad_UnknownSchemaVersionLogsInvalid, TestSemanticCacheStoreLoad_DiscardsV1, TestSemanticCacheStoreLoad_DiscardsV2",
			Input:     qv07Input{Qualifiers: map[string]any{"cache_path": qv07CachePath}, State: map[string]any{"loads": inputs}},
			Output:    qv07Output{Cache: map[string]any{"loads": recorded}},
		})
	}

	// The publication owner persists the published planes with the retained
	// native zone values laid over them.
	qv07InTempDir(t, func() {
		logs := &qv07Logs{}
		store := qv07Store(logs)
		provider := graphql.NewLiveSemanticProvider()
		owner := newVaillantSemanticPublication(provider, nil, store)
		views := []vaillantZoneView{
			{instance: 0, snapshot: &vaillantZoneSnapshot{Instance: 0, Present: true, Name: "Living", OperatingMode: "auto", AllowedModes: []string{"auto", "off"}, TargetTempC: qv07F(21), CurrentTempC: qv07F(19), HumidityPct: qv07F(40)}},
			{instance: 1, snapshot: &vaillantZoneSnapshot{Instance: 1, Present: true, Name: "Bedroom", OperatingMode: "off", CurrentTempC: qv07F(17)}},
		}
		overlays := map[byte]vaillantZoneCacheOverlay{
			0: {currentTempC: qv07F(20.25), humidityPct: qv07F(45), roomMappingRaw: qv07U16(1), associatedCircuitRaw: qv07U16(0)},
		}
		dhwView := vaillantDhwView{snapshot: &vaillantDhwSnapshot{CurrentTempC: qv07F(48.5), OperatingMode: "auto", TargetTempC: qv07F(55)}}
		boilerSnapshot := qv07BoilerSnapshot()
		env := &qv07Env{t: t, provider: provider, owner: owner}
		env.decide("publish_zone_views_live", map[string]any{"published": owner.publishZoneViews(views, semanticSnapshotSourceLive)})
		env.decide("publish_dhw_live", map[string]any{"published": owner.publishDhwView(dhwView, semanticSnapshotSourceLive)})
		env.decide("publish_boiler_live", map[string]any{"published": owner.publishBoilerStatusView(boilerSnapshot, semanticSnapshotSourceLive)})
		env.decide("persists_cache", map[string]any{"value": owner.persistsCache()})
		owner.persistCache(overlays)
		bytes := qv07ReadCache(t)
		loaded, ok := qv07Store(logs).Load()
		env.decide("load", map[string]any{"ok": ok})
		overlayState := map[string]any{}
		for instance, overlay := range overlays {
			overlayState[fmt.Sprint(instance)] = qv07Native(t, map[string]any{"current_temp_c": overlay.currentTempC, "humidity_pct": overlay.humidityPct, "room_mapping_raw": overlay.roomMappingRaw, "associated_circuit_raw": overlay.associatedCircuitRaw})
		}
		gql, mcpRecord := qv07Capture(t, provider, "zones", "dhw", "boiler")
		qv07Write(t, "cache/cache-persist-published-planes-with-zone-overlay", qv07Case{
			Component: "cmd/gateway semantic cache",
			Source:    []string{qv07CachePubFile, qv07CacheFile},
			Stimulus:  "cmd/gateway/vaillant_semantic_publication_cache.go persistCache over published planes",
			Input: qv07Input{Qualifiers: map[string]any{"cache_path": qv07CachePath, "source": "live"}, Clock: map[string]any{"store_now": qv07Clock.Format("2006-01-02T15:04:05Z07:00")}, State: map[string]any{
				"zone_views": qv07Native(t, qv07ZoneViewState(views)), "dhw_view": qv07Native(t, qv07DhwViewState(dhwView)),
				"boiler_snapshot": qv07Native(t, boilerSnapshot), "overlays": overlayState,
			}},
			Output: qv07Output{Decisions: env.decisions, GraphQL: gql, MCP: mcpRecord, Cache: map[string]any{"saved_bytes": bytes, "loaded_snapshot": qv07Native(t, loaded)}, Observations: logs.lines},
		})
	})
}
