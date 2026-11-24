package main

import (
	"bytes"
	"context"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"sync/atomic"
	"testing"

	ebusgateway "github.com/Project-Helianthus/helianthus-ebusgateway"
	"github.com/Project-Helianthus/helianthus-ebusgateway/graphql"
	"github.com/Project-Helianthus/helianthus-ebusgateway/mcp"
	ebuserrors "github.com/Project-Helianthus/helianthus-ebusgo/errors"
	"github.com/Project-Helianthus/helianthus-ebusgo/protocol"
	"github.com/Project-Helianthus/helianthus-ebusgo/transport"
)

type oracleWire struct {
	inner  transport.RawTransport
	log    func(payload []byte)
	mu     sync.Mutex
	buffer []byte
	logged bool
}

func (w *oracleWire) ReadByte() (byte, error) { return w.inner.ReadByte() }

// Write reassembles the symbols the bus writes one at a time into the telegram of one exchange and logs it once complete.
func (w *oracleWire) Write(payload []byte) (int, error) {
	w.mu.Lock()
	for _, b := range payload {
		if b == protocol.SymbolSyn {
			w.buffer, w.logged = w.buffer[:0], false
			continue
		}
		w.buffer = append(w.buffer, b)
	}
	if !w.logged {
		if _, _, ok := oracleTelegram(w.buffer); ok {
			w.log(append([]byte(nil), w.buffer...))
			w.logged = true
		}
	}
	w.mu.Unlock()
	return w.inner.Write(payload)
}
func (w *oracleWire) Close() error { return w.inner.Close() }

// oracleTelegram decodes one initiator telegram QQ ZZ PB SB NN DATA CRC as the virtual site reads it.
func oracleTelegram(raw []byte) (map[string]any, byte, bool) {
	var plain []byte
	escaped := false
	for _, b := range raw {
		if escaped {
			escaped = false
			if b == 0x00 {
				plain = append(plain, protocol.SymbolEscape)
			} else {
				plain = append(plain, protocol.SymbolSyn)
			}
			continue
		}
		if b == protocol.SymbolEscape {
			escaped = true
			continue
		}
		if b == protocol.SymbolSyn {
			continue
		}
		plain = append(plain, b)
	}
	if len(plain) < 6 || len(plain) < 5+int(plain[4])+1 {
		return nil, 0, false
	}
	data := plain[5 : 5+int(plain[4])]
	return map[string]any{"source": plain[0], "target": plain[1], "primary": plain[2], "secondary": plain[3], "data_hex": hex.EncodeToString(data)}, plain[4], true
}

func oracleWriteFrame(primary, secondary byte, data []byte) bool {
	switch {
	case primary == vaillantExtRegisterPrimary && secondary == vaillantExtRegisterSecondary:
		return len(data) >= 2 && data[1] == vaillantB524OpWrite
	case primary == vaillantB509Primary && secondary == vaillantB509Secondary:
		return len(data) >= 1 && data[0] == vaillantB509OpcodeWrite
	case primary == vaillantB555Primary && secondary == vaillantB555Secondary:
		return len(data) >= 1 && data[0] == b555OpcodeTimerWrite
	}
	return false
}

type oracleStepLog struct {
	mu      sync.Mutex
	current atomic.Value
	frames  []map[string]any
}

func (l *oracleStepLog) add(entry map[string]any) {
	step, _ := l.current.Load().(string)
	entry["step"] = step
	l.mu.Lock()
	l.frames = append(l.frames, entry)
	l.mu.Unlock()
}

func oracleVaillantRun(t *testing.T, scenario string) *oracleClasses {
	t.Helper()
	log := &oracleStepLog{}
	log.current.Store("")
	seed := ""
	if scenario == "cache_hydrated_partial_reads" {
		seed = filepath.Join(vaillantPublicationDir, "semantic_cache_seed.json")
	}
	h := newOracleVaillantHarness(t, seed, log)
	step := func(name string, action func(context.Context) any) {
		log.current.Store(name)
		h.step(name, action)
	}
	poll := func(name string, refresh func(context.Context)) {
		step(name, func(ctx context.Context) any {
			h.poller.withPollLock(ctx, refresh)
			return nil
		})
	}
	pass := func(prefix string) {
		p := h.poller
		poll(prefix+"refresh_regulator_capability", p.refreshRegulatorCapability)
		poll(prefix+"refresh_discovery", p.refreshDiscovery)
		poll(prefix+"refresh_state", p.refreshState)
		poll(prefix+"refresh_config", p.refreshConfig)
		poll(prefix+"refresh_circuits", p.refreshCircuits)
		poll(prefix+"refresh_system", p.refreshSystem)
		poll(prefix+"refresh_energy", p.refreshEnergy)
		poll(prefix+"refresh_schedules", p.refreshSchedules)
		poll(prefix+"refresh_boiler_fast", p.boilerStatusTierTask(boilerStatusTierFast))
		poll(prefix+"refresh_boiler_medium", p.boilerStatusTierTask(boilerStatusTierMedium))
		poll(prefix+"refresh_boiler_slow", p.boilerStatusTierTask(boilerStatusTierSlow))
		poll(prefix+"refresh_radio_devices", p.refreshRadioDevices)
		poll(prefix+"refresh_fm5", p.refreshFM5Semantic)
	}
	switch scenario {
	case "full_site":
		poll("startup_discovery", h.poller.refreshDiscovery)
		pass("")
		temperature := 20.5
		step("write_boiler_config", func(ctx context.Context) any {
			return vaillantPublicationValue(h.graphqlWriter.SetBoilerConfig(ctx, "maximum_heating_flow_temperature_setpoint", "70"))
		})
		step("write_system_config", func(ctx context.Context) any {
			return vaillantPublicationValue(h.mcpConfigWriter.SetSystemConfig(ctx, "room_humidity_limit_maximum", "55"))
		})
		step("write_zone_time_program", func(ctx context.Context) any {
			slots := []mcp.TimeProgramSlot{{StartHour: 5, StartMinute: 30, EndHour: 21, EndMinute: 0, TemperatureC: &temperature}}
			result := vaillantPublicationWriteResult(h.mcpScheduleWriter.SetZoneTimeProgram(ctx, 0, 2, slots))
			h.awaitProgramRefresh(0, "heating", 2, slots[0])
			return result
		})
		step("write_dhw_time_program", func(ctx context.Context) any {
			slots := []mcp.TimeProgramSlot{{StartHour: 7, StartMinute: 0, EndHour: 9, EndMinute: 30}}
			result := vaillantPublicationWriteResult(h.graphqlWriter.SetDhwTimeProgram(ctx, 6, slots))
			h.awaitProgramRefresh(255, "dhw", 6, slots[0])
			return result
		})
	case "cache_hydrated_partial_reads":
		step("cache_hydrated", func(context.Context) any { return nil })
		poll("startup_discovery", h.poller.refreshDiscovery)
		pass("")
		h.site.failReads(vaillantPublicationFailingB524, vaillantPublicationFailingB509)
		poll("failing_startup_discovery", h.poller.refreshDiscovery)
		pass("failing_")
	default:
		t.Fatalf("unknown scenario %q", scenario)
	}

	classes := oracleNormalize()
	log.mu.Lock()
	frames := log.frames
	log.mu.Unlock()
	// The production poller issues the reads of one step concurrently, so the frames of a step are recorded in
	// canonical order: steps in run order, then the frame text. The multiset of a step is what the poller does.
	rank := map[string]int{}
	for index, raw := range h.steps {
		rank[raw.(map[string]any)["Step"].(string)] = index
	}
	text := func(frame map[string]any) string { encoded, _ := json.Marshal(frame); return string(encoded) }
	sort.SliceStable(frames, func(i, j int) bool {
		ri, rj := rank[frames[i]["step"].(string)], rank[frames[j]["step"].(string)]
		if ri != rj {
			return ri < rj
		}
		return text(frames[i]) < text(frames[j])
	})
	for _, frame := range frames {
		primary, _ := frame["primary"].(byte)
		secondary, _ := frame["secondary"].(byte)
		data, _ := hex.DecodeString(frame["data_hex_value"].(string))
		delete(frame, "data_hex_value")
		if oracleWriteFrame(primary, secondary, data) {
			classes.Sends = append(classes.Sends, frame)
		} else {
			classes.Acquisitions = append(classes.Acquisitions, frame)
		}
	}
	var previousProviderLeaves = map[string]map[string]string{}
	lastProvider := map[string]any{}
	for _, raw := range h.steps {
		record := raw.(map[string]any)
		name := record["Step"]
		classes.Publications = append(classes.Publications, map[string]any{"step": name, "at": record["At"], "hub": oracleJSON(record["Hub"]), "cache_saves": oracleJSON(record["CacheSaves"])})
		classes.Outcomes = append(classes.Outcomes, map[string]any{"step": name, "writer_result": oracleJSON(record["WriterResult"])})
		classes.PublicOutputs = append(classes.PublicOutputs, map[string]any{"step": name, "provider": oracleJSON(record["Provider"]), "mcp": oracleJSON(record["MCP"])})
		views, _ := oracleJSON(record["Provider"]).(map[string]any)
		for view, value := range views {
			if text, unchanged := value.(string); unchanged && text == vaillantPublicationUnchanged {
				continue
			}
			lastProvider[view] = value
			now := map[string]string{}
			oracleLeaves("", value, now)
			if before, seen := previousProviderLeaves[view]; seen {
				if gone := oracleWithdrawn(before, now); len(gone) > 0 {
					classes.Withdrawals = append(classes.Withdrawals, map[string]any{"step": name, "view": view, "paths": gone})
				}
			}
			previousProviderLeaves[view] = now
		}
	}
	sort.SliceStable(classes.Withdrawals, func(i, j int) bool {
		a, _ := json.Marshal(classes.Withdrawals[i])
		b, _ := json.Marshal(classes.Withdrawals[j])
		return rank[classes.Withdrawals[i].(map[string]any)["step"].(string)] < rank[classes.Withdrawals[j].(map[string]any)["step"].(string)] ||
			(rank[classes.Withdrawals[i].(map[string]any)["step"].(string)] == rank[classes.Withdrawals[j].(map[string]any)["step"].(string)] && string(a) < string(b))
	})
	return classes
}

// newOracleVaillantHarness is newVaillantPublicationHarness with the wire and the poller send hook logged.
func newOracleVaillantHarness(t *testing.T, seed string, log *oracleStepLog) *vaillantPublicationHarness {
	t.Helper()
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	site := newVaillantPublicationSite()
	wire := &oracleWire{inner: newVaillantPublicationWire(site), log: func(payload []byte) {
		if entry, length, ok := oracleTelegram(payload); ok {
			entry["via"] = "gateway-bus"
			entry["payload_length"] = length
			entry["wire_hex"] = hex.EncodeToString(payload)
			entry["data_hex_value"] = entry["data_hex"]
			log.add(entry)
		}
	}}
	gateway, err := ebusgateway.New(ctx, ebusgateway.Config{Transport: wire})
	if err != nil {
		t.Fatalf("ebusgateway.New() error = %v", err)
	}
	busCtx, stopBus := context.WithCancel(context.Background())
	busDone := make(chan struct{})
	go func() {
		defer close(busDone)
		gateway.Start(busCtx)
	}()
	t.Cleanup(func() {
		stopBus()
		<-busDone
		_ = gateway.Close()
	})
	vaillantPublicationRegisterDevices(t, gateway.Registry)
	cfg := ebusgateway.DefaultConfig()
	cfg.TransportConfig = ebusgateway.TransportConfig{Protocol: ebusgateway.TransportAdapterDirect, Network: "tcp", Address: "adapter.invalid:9999"}
	cfg.ScanSource = vaillantPublicationSource
	h := &vaillantPublicationHarness{t: t, ctx: ctx, site: site, provider: graphql.NewLiveSemanticProvider()}
	clock := site.clock
	h.provider.SetEnergyClock(clock.Now)
	var cached vaillantCacheHydration
	cacheLoaded := false
	if seed != "" {
		cached, cacheLoaded = preloadSemanticCache(h.provider, newSemanticCacheStore(seed, t.Logf))
		if !cacheLoaded {
			t.Fatalf("semantic cache seed %s did not load", seed)
		}
	}
	hub := graphql.NewBroadcastHub(nil)
	poller := newVaillantSemanticPoller(cfg, gateway, h.provider, hub, h)
	poller.nowFn = clock.Now
	poller.tasks.now = clock.Now
	poller.scheduler.SetClock(clock.Now)
	shadow := ebusgateway.NewShadowCache(ebusgateway.ShadowCacheOptions{FeatureFlags: normalizeObserveFirstFeatureFlagsForPoller(cfg), Now: clock.Now})
	poller.shadow = shadow
	poller.scheduler.SetShadowCache(shadow)
	poller.sendFrameFn = func(ctx context.Context, frame protocol.Frame) (*protocol.Frame, error) {
		reply, sendErr := site.send(ctx, frame)
		entry := map[string]any{"via": "poller-send", "source": frame.Source, "target": frame.Target, "primary": frame.Primary, "secondary": frame.Secondary, "data_hex": hex.EncodeToString(frame.Data), "data_hex_value": hex.EncodeToString(frame.Data)}
		if sendErr != nil {
			entry["error"] = sendErr.Error()
			entry["timeout"] = errors.Is(sendErr, ebuserrors.ErrTimeout)
		} else {
			entry["reply_hex"] = hex.EncodeToString(reply.Data)
		}
		log.add(entry)
		return reply, sendErr
	}
	poller.pauseFn = clock.pause
	if cacheLoaded {
		poller.hydrateFromCache(cached)
	}
	h.poller = poller
	admitted := admittedSourceProvider(func() (byte, bool) { return vaillantPublicationSource, true })
	h.graphqlWriter = admittedGraphQLSemanticWriter{boiler: poller, system: poller, schedule: poller, admitted: admitted}
	h.mcpConfigWriter = admittedMCPConfigWriter{writer: &mcpConfigWriterAdapter{poller: poller}, admitted: admitted}
	h.mcpScheduleWriter = admittedMCPScheduleWriter{writer: poller, admitted: admitted}
	view, ok := newMCPSemanticProvider(h.provider).(mcpSemanticProviderAdapter)
	if !ok {
		t.Fatal("newMCPSemanticProvider() is not the gateway's semantic adapter")
	}
	h.mcpView = view
	h.subscribe(hub)
	return h
}

// TestOracleSessionVaillantPoller runs the production poller over the virtual site and records the six classes.
func TestOracleSessionVaillantPoller(t *testing.T) {
	session := oracleLoadSession(t)
	first := oracleVaillantRun(t, session.Scenario)
	second := oracleVaillantRun(t, session.Scenario)
	a, _ := json.Marshal(first)
	b, _ := json.Marshal(second)
	if !bytes.Equal(a, b) {
		_ = os.WriteFile(filepath.Join(os.Getenv("ORACLE_OUT"), "first.json"), a, 0o644)
		_ = os.WriteFile(filepath.Join(os.Getenv("ORACLE_OUT"), "second.json"), b, 0o644)
		t.Fatalf("two runs of the session differ (%d and %d bytes)", len(a), len(b))
	}
	oracleWriteClasses(t, first)
	_ = fmt.Sprint
}
