//go:build linux || darwin

package adaptermux

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/adaptermux/ptytest"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/adaptermux/v8classifier"
	"github.com/Project-Helianthus/helianthus-ebusgo/transport"
	"golang.org/x/sys/unix"
)

// TestOracleAdapterMux records the pin's multiplexer, classifier and
// pseudo-terminal cases. The stimuli are the pin's own fixtures.
func TestOracleAdapterMux(t *testing.T) {
	oracleRecordTransitions(t)
	oracleRecordClassifier(t)
	oracleRecordPty(t)
}

func oracleRecordTransitions(t *testing.T) {
	t.Helper()
	for _, row := range transitionRows {
		row := row
		fixture := transitionFixtures[row.fixture]
		apply := transitionInputs[row.input]
		h := newTransitionHarness(t, fixture.mode)
		fixture.build(h)
		h.discardEffects()
		before := h.state()
		apply(h)
		after := h.state()
		effects := append([]string(nil), h.effects()...)
		h.stop()
		symbols, observations, classes := oracleClassifyEffects(effects)
		oracleWrite(t, "transition/"+row.fixture+"--"+row.input+".json", oracleCase{
			Component: "adaptermux",
			Source:    "internal/adaptermux/mux.go",
			Stimulus:  "TestMuxTransitionCharacterization/" + row.fixture + "/" + row.input,
			Input: oracleInput{
				Bytes:      oracleTransitionBytes(row.input),
				Qualifiers: map[string]any{"fixture": row.fixture, "input": row.input, "upstream": oracleUpstream(fixture.mode)},
				Clock:      map[string]any{"timers": "held", "deadline": "fires only when the input is start_deadline"},
				State:      oracleTransitionState(before),
			},
			Output: oracleOutput{
				SymbolsWritten: symbols,
				Decisions:      []any{map[string]any{"state": oracleTransitionState(after), "effects": effects, "effect_classes": classes}},
				Observations:   observations,
			},
		})
	}
}

// oracleClassifyEffects splits the harness effect log with the pin's own effect
// classifier. Only the payload of an adapter write is a symbol written;
// consumer-facing passive, active and session entries are observations; adapter
// start requests, results and errors stay in the effect list and its classes.
func oracleClassifyEffects(effects []string) (written, observations, classes []any) {
	written, observations, classes = []any{}, []any{}, []any{}
	for _, effect := range effects {
		kind, err := muxModelEffectKind(effect)
		if err != nil {
			classes = append(classes, "unclassified")
			continue
		}
		classes = append(classes, kind.String())
		switch kind {
		case muxModelEffectAdapterWrite:
			written = append(written, strings.ToLower(strings.ReplaceAll(strings.TrimPrefix(effect, "adapter: Write "), " ", "")))
		case muxModelEffectPassiveSymbol, muxModelEffectPassiveReset, muxModelEffectPassiveLifecycle, muxModelEffectActiveByte,
			muxModelEffectSessionReceived, muxModelEffectSessionStarted, muxModelEffectSessionFailed, muxModelEffectSessionReset,
			muxModelEffectSessionError, muxModelEffectSessionInfo:
			observations = append(observations, effect)
		}
	}
	return written, observations, classes
}

func oracleUpstream(mode transitionUpstreamMode) string {
	switch mode {
	case transitionUpstreamAsync:
		return "async"
	case transitionUpstreamBlocking:
		return "blocking"
	case transitionUpstreamRawView:
		return "raw_view"
	default:
		return "unknown"
	}
}

func oracleTransitionBytes(input string) string {
	switch input {
	case "wire_syn", "stream_wire_syn":
		return "aa"
	case "received_symbol":
		return "52"
	case "received_initiator_symbol", "failed", "started_other_source":
		return "10"
	case "raw_escape_lead":
		return "a9"
	case "bid":
		return "71"
	default:
		return ""
	}
}

func oracleTransitionState(state transitionState) map[string]any {
	return map[string]any{
		"owner":             state.owner,
		"gateway_txn":       state.gatewayTxn,
		"start":             state.start,
		"start_response":    state.startResponse,
		"start_blocking":    state.startBlocking,
		"blocking_call":     state.blockingCall,
		"absorb":            state.absorb,
		"regrant_fence":     state.regrantFence,
		"retired_selection": state.retiredSelection,
		"recovery":          state.recovery,
		"resync_owed":       state.resyncOwed,
		"phase":             state.phase,
		"local_losers":      state.localLosers,
		"bids":              state.bids,
	}
}

func oracleRecordClassifier(t *testing.T) {
	t.Helper()
	now := time.Unix(0, 0).UTC()
	for _, mode := range []v8classifier.Mode{v8classifier.ModeOff, v8classifier.ModeShadow, v8classifier.ModeEnforce} {
		classifier := v8classifier.New(mode)
		drops := make([]bool, 0, 4)
		for _, value := range []byte{0x00, 0x10, 0x31, 0x52} {
			drops = append(drops, classifier.Observe(transport.StreamEvent{Kind: transport.StreamEventByte, Byte: value}, now))
		}
		oracleWrite(t, "v8classifier/observe-idle-"+mode.String()+".json", oracleCase{
			Component: "v8classifier",
			Source:    "internal/adaptermux/v8classifier/classifier.go",
			Stimulus:  "TestClassifier_Observe/" + mode.String(),
			Input: oracleInput{
				Bytes:      "00103152",
				Qualifiers: map[string]any{"mode": mode.String(), "kind": "byte"},
				Clock:      map[string]any{"at": now.Format(time.RFC3339Nano)},
				State:      map[string]any{"fsm": "idle"},
			},
			Output: oracleOutput{
				Decisions: []any{map[string]any{"drop": drops}},
				Counters:  oracleClassifierCounters(classifier),
			},
		})
	}
	for _, mode := range []v8classifier.Mode{v8classifier.ModeOff, v8classifier.ModeShadow, v8classifier.ModeEnforce} {
		at := time.Unix(42, 0).UTC()
		if mode == v8classifier.ModeEnforce {
			at = time.Unix(7, 0).UTC()
		}
		classifier := v8classifier.New(mode)
		classifier.Observe(transport.StreamEvent{Kind: transport.StreamEventStarted, Data: 0x71}, at)
		drop := classifier.Observe(transport.StreamEvent{Kind: transport.StreamEventByte, Byte: 0xAA}, at)
		events, dropped := classifier.DrainAdminEvents()
		recorded := make([]any, 0, len(events))
		for _, event := range events {
			recorded = append(recorded, map[string]any{
				"kind": event.Kind.String(), "byte": hex.EncodeToString([]byte{event.Byte}),
				"was_escaped": event.WasEscaped, "at": event.At.UTC().Format(time.RFC3339Nano),
				"fsm_state": fmt.Sprint(event.FSMState),
			})
		}
		oracleWrite(t, "v8classifier/aa-injection-"+mode.String()+".json", oracleCase{
			Component: "v8classifier",
			Source:    "internal/adaptermux/v8classifier/classifier.go",
			Stimulus:  "TestClassifier_DropAaInjection/" + mode.String(),
			Input: oracleInput{
				Bytes:      "aa",
				Qualifiers: map[string]any{"mode": mode.String(), "started": "71"},
				Clock:      map[string]any{"at": at.Format(time.RFC3339Nano)},
				State:      map[string]any{"after_started": true},
			},
			Output: oracleOutput{
				SymbolsWritten: oracleForwarded("aa", drop),
				Decisions:      []any{map[string]any{"drop": drop, "admin_events": recorded, "admin_dropped": dropped}},
				Observations:   recorded,
				Counters:       oracleClassifierCounters(classifier),
			},
		})
	}
}

// oracleForwarded lists the symbol the classifier lets through: a symbol that
// Observe drops is not forwarded and is not listed as written.
func oracleForwarded(symbol string, drop bool) []any {
	if drop {
		return []any{}
	}
	return []any{symbol}
}

func oracleClassifierCounters(classifier *v8classifier.Classifier) map[string]any {
	return map[string]any{
		"observed_bytes_total":        classifier.ObservedBytesTotal(),
		"fsm_drop_aa_injection_total": classifier.FsmDropAaInjectionTotal(),
		"shadow_would_have_dropped":   classifier.ShadowWouldHaveDroppedTotal(),
		"enforce_drops_applied_total": classifier.EnforceDropsAppliedTotal(),
		"observed_admin_events_total": classifier.ObservedAdminEventsTotal(),
	}
}

func oracleRecordPty(t *testing.T) {
	t.Helper()
	pair := ptytest.Open(t)
	payload := []byte{0x31, 0x15, 0x07, 0x04, 0x00}
	device, err := os.OpenFile(pair.DevicePath, os.O_RDWR, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer device.Close()
	pair.WritePeer(t, payload)
	buf := make([]byte, len(payload))
	_ = device.SetReadDeadline(time.Now().Add(2 * time.Second))
	n, err := device.Read(buf)
	if err != nil {
		t.Fatal(err)
	}
	oracleWrite(t, "ptytest/pair-roundtrip.json", oracleCase{
		Component: "ptytest",
		Source:    "internal/adaptermux/ptytest/ptytest.go",
		Stimulus:  "ptytest.Open/WritePeer",
		Input:     oracleInput{Bytes: hex.EncodeToString(payload), Qualifiers: map[string]any{"device": "synthetic-pty"}, Clock: map[string]any{}, State: map[string]any{}},
		Output:    oracleOutput{SymbolsWritten: []any{hex.EncodeToString(buf[:n])}, Decisions: []any{map[string]any{"read_matches_write": n == len(payload) && string(buf) == string(payload)}}},
	})

	for _, test := range []struct {
		protocol string
		baud     uint32
	}{{"ens", 115200}, {"enh", 9600}} {
		opened := ptytest.Open(t)
		adapter := ptytest.ServeAdapter(opened)
		mux := newSerialTestMux(test.protocol, opened.DevicePath, nil)
		if err := mux.Start(context.Background()); err != nil {
			t.Fatal(err)
		}
		adapter.WaitInit(t, serialTestGuard)
		got := opened.Baud(t)
		mux.connMu.Lock()
		_, isSerial := mux.conn.(*serialConn)
		mux.connMu.Unlock()
		_ = mux.Close()
		oracleWrite(t, "ptytest/mux-open-"+test.protocol+".json", oracleCase{
			Component: "ptytest",
			Source:    "internal/adaptermux/serial.go",
			Stimulus:  "TestMuxSerial_StartOpensDeviceAtTheProtocolSpeed/" + test.protocol,
			Input:     oracleInput{Bytes: "", Qualifiers: map[string]any{"protocol": test.protocol, "device": "synthetic-pty"}, Clock: map[string]any{}, State: map[string]any{}},
			Output: oracleOutput{
				Decisions: []any{map[string]any{"baud": got, "serial_connection": isSerial, "baud_matches_protocol": got == test.baud}},
				Counters:  map[string]any{"baud": got},
			},
		})
	}

	absent := newSerialTestMux("ens", filepath.Join(t.TempDir(), "absent"), nil)
	err = absent.Start(context.Background())
	_ = absent.Close()
	oracleWrite(t, "ptytest/mux-absent-device.json", oracleCase{
		Component: "ptytest",
		Source:    "internal/adaptermux/serial.go",
		Stimulus:  "TestMuxSerial_StartReportsAnAbsentDevice",
		Input:     oracleInput{Qualifiers: map[string]any{"protocol": "ens", "device": "absent"}, Clock: map[string]any{}, State: map[string]any{}},
		Output:    oracleOutput{Decisions: []any{map[string]any{"enoent": errors.Is(err, unix.ENOENT)}}},
	})

	link := filepath.Join(t.TempDir(), "adapter")
	first := ptytest.Open(t)
	if err := os.Symlink(first.DevicePath, link); err != nil {
		t.Fatal(err)
	}
	firstAdapter := ptytest.ServeAdapter(first)
	logs := make(serialLogLines, 256)
	mux := newSerialTestMux("ens", link, logs)
	if err := mux.Start(context.Background()); err != nil {
		t.Fatal(err)
	}
	firstAdapter.WaitInit(t, serialTestGuard)
	second := ptytest.Open(t)
	distinct := second.DevicePath != first.DevicePath
	if err := os.Remove(link); err != nil {
		t.Fatal(err)
	}
	first.Close()
	firstFailure := logs.wait(t, "no such file or directory")
	secondFailure := logs.wait(t, "no such file or directory")
	gap := secondFailure.at.Sub(firstFailure.at)
	secondAdapter := ptytest.ServeAdapter(second)
	if err := os.Symlink(second.DevicePath, link); err != nil {
		t.Fatal(err)
	}
	secondAdapter.WaitInit(t, serialTestGuard)
	reconnected := logs.wait(t, "reconnected to "+NetworkSerial+"/")
	baud := second.Baud(t)
	_ = mux.Close()
	oracleWrite(t, "ptytest/mux-reopen.json", oracleCase{
		Component: "ptytest",
		Source:    "internal/adaptermux/serial.go",
		Stimulus:  "TestMuxSerial_ReopensThePathAfterTheDeviceWentAway",
		Input:     oracleInput{Qualifiers: map[string]any{"protocol": "ens", "device": "synthetic-pty-link"}, Clock: map[string]any{"reconnect_initial": "40ms", "reconnect_max": "80ms"}, State: map[string]any{"distinct_replacement": distinct}},
		Output: oracleOutput{
			Decisions: []any{map[string]any{
				"first_failure_is_reconnect": strings.Contains(firstFailure.text, "reconnect failed"),
				"backoff_doubled":            gap >= 80*time.Millisecond,
				"reconnected":                strings.Contains(reconnected.text, "reconnected"),
				"baud":                       baud,
			}},
			Counters: map[string]any{"baud": baud},
		},
	})
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

func oracleWrite(t *testing.T, name string, document oracleCase) {
	t.Helper()
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	if document.Format == "" {
		document.Format = "helianthus-oracle-bt01-case/1"
	}
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
	encoded, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(directory, filepath.FromSlash(name))
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
