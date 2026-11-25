package modbusadapter

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	modbus "github.com/Project-Helianthus/helianthus-modbus"
	"github.com/Project-Helianthus/helianthus-modbusreg/huawei"
)

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
	document.Format = "helianthus-oracle-qv04-case/1"
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
	path := filepath.Join(directory, name+".json")
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

// TestOracleModbusAdapterReadOnlySession records the read-only session of the
// pin. The stimuli are the pin's own tests in readonly_session_test.go.
func TestOracleModbusAdapterReadOnlySession(t *testing.T) {
	oracleRecordMethodSetAndAdmission(t)
	oracleRecordDeadlineClassification(t)
	oracleRecordPacingAfterLateResponses(t)
	oracleRecordCanceledPacingWait(t)
	oracleRecordSessionTimeout(t)
}

const oracleSessionSource = "internal/modbusadapter/readonly_session.go"

func oracleRecordMethodSetAndAdmission(t *testing.T) {
	t.Helper()
	typ := reflect.TypeOf((*ReadOnlySession)(nil))
	var methods []any
	for i := 0; i < typ.NumMethod(); i++ {
		methods = append(methods, typ.Method(i).Name)
	}
	endpoint := &fakeEndpoint{}
	adapter := &Adapter{endpoint: endpoint}
	session, err := NewReadOnlySession(adapter)
	if err != nil {
		t.Fatal(err)
	}
	var steps, decisions []any
	for _, spec := range []struct {
		function modbus.FunctionCode
		quantity uint16
	}{{modbus.FunctionReadInputRegisters, 1}, {modbus.FunctionReadHoldingRegisters, 124}} {
		request, err := modbus.NewReadRegistersRequest(spec.function, 0, spec.quantity)
		if err != nil {
			t.Fatal(err)
		}
		_, readErr := session.ReadHolding(context.Background(), 1, request)
		steps = append(steps, map[string]any{"step": "read_holding", "unit": 1, "function": int(spec.function), "offset": 0, "quantity": int(spec.quantity)})
		decisions = append(decisions, map[string]any{"step": "read_holding", "function": int(spec.function), "quantity": int(spec.quantity), "error": oracleErr(readErr)})
	}
	_, identErr := session.ReadDeviceIdentification(context.Background(), 1, huawei.IdentificationRequest{ReadDeviceIDCode: 4})
	steps = append(steps, map[string]any{"step": "read_device_identification", "unit": 1, "read_device_id_code": 4})
	decisions = append(decisions, map[string]any{"step": "read_device_identification", "error": oracleErr(identErr)})
	enqueuedBeforeClose := endpoint.enqueueCalls
	closeErr := session.Close()
	steps = append(steps, map[string]any{"step": "close"})
	decisions = append(decisions, map[string]any{"step": "close", "error": oracleErr(closeErr)})
	request, _ := modbus.NewReadRegistersRequest(modbus.FunctionReadHoldingRegisters, 0, 1)
	_, closedErr := session.ReadHolding(context.Background(), 1, request)
	steps = append(steps, map[string]any{"step": "read_holding_after_close", "unit": 1, "function": int(modbus.FunctionReadHoldingRegisters), "offset": 0, "quantity": 1})
	decisions = append(decisions, map[string]any{"step": "read_holding_after_close", "error": oracleErr(closedErr)})
	oracleWrite(t, "method-set-and-admission", oracleCase{
		Component: "modbusadapter-readonly-session",
		Source:    oracleSessionSource,
		Stimulus:  "TestH10ReadOnlySessionMethodSetAndAdmission",
		Input: oracleInput{
			Qualifiers: map[string]any{"adapter": "an adapter holding a recording endpoint, no pacing configured, connection generation zero"},
			State:      map[string]any{"steps": steps},
		},
		Output: oracleOutput{
			Decisions: decisions,
			Cache:     map[string]any{"exported_methods": methods},
			Counters:  map[string]any{"endpoint_enqueue_calls_before_close": enqueuedBeforeClose, "endpoint_enqueue_calls_at_end": endpoint.enqueueCalls, "endpoint_close_calls": endpoint.closeCalls},
		},
	})
}

func oracleRecordDeadlineClassification(t *testing.T) {
	t.Helper()
	classified := sessionReadError(os.ErrDeadlineExceeded)
	oracleWrite(t, "deadline-classification", oracleCase{
		Component: "modbusadapter-readonly-session",
		Source:    oracleSessionSource,
		Stimulus:  "TestH10SessionDeadlineClassification",
		Input:     oracleInput{Qualifiers: map[string]any{"error": os.ErrDeadlineExceeded.Error(), "error_kind": "the operating system's deadline-exceeded sentinel"}},
		Output: oracleOutput{Decisions: []any{map[string]any{
			"error":                        oracleErr(classified),
			"is_context_deadline_exceeded": errors.Is(classified, context.DeadlineExceeded),
			"is_os_deadline_exceeded":      errors.Is(classified, os.ErrDeadlineExceeded),
		}}},
	})
}

func oracleRecordPacingAfterLateResponses(t *testing.T) {
	t.Helper()
	endpoint := &h10LateEndpoint{delay: 80 * time.Millisecond}
	adapter := &Adapter{endpoint: endpoint, config: Config{Pacing: &Pacing{Gap: time.Second}}}
	session, err := NewReadOnlySession(adapter)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := modbus.NewReadRegistersRequest(modbus.FunctionReadHoldingRegisters, 0, 1)
	_, readErr := session.ReadHolding(context.Background(), 1, request)
	since := time.Since(adapter.completedAt)
	oracleWrite(t, "pacing-completes-after-late-responses", oracleCase{
		Component: "modbusadapter-readonly-session",
		Source:    oracleSessionSource,
		Stimulus:  "TestH10ReadHoldingPacingCompletesAfterLateResponses",
		Input: oracleInput{
			Qualifiers: map[string]any{"pacing_gap_ns": int64(time.Second), "pacing_settle_ns": 0, "unit": 1, "function": int(modbus.FunctionReadHoldingRegisters), "offset": 0, "quantity": 1},
			Clock:      map[string]any{"unit": "wall clock", "note": "the endpoint's second read sleeps for the delay below, then fails; the completion time is read straight after the call returns"},
			State: map[string]any{
				"endpoint":                         "first read returns an empty batch, the second sleeps and then returns an error whose text is h10 stop",
				"second_read_delay_ns":             int64(80 * time.Millisecond),
				"completion_bound_after_return_ns": int64(40 * time.Millisecond),
			},
		},
		Output: oracleOutput{
			Decisions: []any{map[string]any{"step": "read_holding", "error": oracleErr(readErr)}},
			Counters: map[string]any{
				"endpoint_reads": endpoint.reads,
				"completion_stamped_within_bound_of_the_read_end": since <= 40*time.Millisecond,
			},
		},
	})
}

func oracleRecordCanceledPacingWait(t *testing.T) {
	t.Helper()
	endpoint := &fakeEndpoint{}
	previous := time.Now()
	adapter := &Adapter{endpoint: endpoint, config: Config{Pacing: &Pacing{Gap: time.Second}}, completedAt: previous}
	session, err := NewReadOnlySession(adapter)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := modbus.NewReadRegistersRequest(modbus.FunctionReadHoldingRegisters, 0, 1)
	var decisions []any
	for i := 0; i < 3; i++ {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
		_, readErr := session.ReadHolding(ctx, 1, request)
		cancel()
		decisions = append(decisions, map[string]any{"attempt": i, "error": oracleErr(readErr), "is_deadline_exceeded": errors.Is(readErr, context.DeadlineExceeded)})
	}
	oracleWrite(t, "canceled-pacing-wait-keeps-completion", oracleCase{
		Component: "modbusadapter-readonly-session",
		Source:    oracleSessionSource,
		Stimulus:  "TestH10ReadHoldingCanceledPacingWaitKeepsCompletion",
		Input: oracleInput{
			Qualifiers: map[string]any{"pacing_gap_ns": int64(time.Second), "attempts": 3, "caller_deadline_ns": int64(10 * time.Millisecond), "unit": 1, "function": int(modbus.FunctionReadHoldingRegisters), "offset": 0, "quantity": 1},
			Clock:      map[string]any{"unit": "wall clock", "note": "the adapter's previous completion time is the moment the case starts, so each attempt waits out its own caller deadline inside the pacing gap"},
		},
		Output: oracleOutput{
			Decisions: decisions,
			Counters:  map[string]any{"endpoint_enqueue_calls": endpoint.enqueueCalls, "completion_time_unchanged": adapter.completedAt.Equal(previous)},
		},
	})
}

func oracleRecordSessionTimeout(t *testing.T) {
	t.Helper()
	cases := []struct{ remaining, min, max time.Duration }{
		{5 * time.Second, 4 * time.Second, 5*time.Second - sessionDeadlineMargin},
		{2 * time.Second, time.Second, 2*time.Second - sessionDeadlineMargin},
		{300 * time.Millisecond, 100 * time.Millisecond, 150 * time.Millisecond},
	}
	var steps, decisions []any
	steps = append(steps, map[string]any{"step": "no_caller_deadline"})
	decisions = append(decisions, map[string]any{"step": "no_caller_deadline", "timeout_ns": int64(sessionTimeout(context.Background()))})
	for _, tc := range cases {
		ctx, cancel := context.WithTimeout(context.Background(), tc.remaining)
		got := sessionTimeout(ctx)
		cancel()
		steps = append(steps, map[string]any{"step": "caller_deadline", "remaining_ns": int64(tc.remaining), "accepted_min_ns": int64(tc.min), "accepted_max_ns": int64(tc.max)})
		decisions = append(decisions, map[string]any{"step": "caller_deadline", "remaining_ns": int64(tc.remaining), "timeout_within_accepted_range": got >= tc.min && got <= tc.max, "timeout_strictly_inside_deadline": got < tc.remaining})
	}
	expired, cancel := context.WithDeadline(context.Background(), time.Now().Add(-time.Second))
	defer cancel()
	steps = append(steps, map[string]any{"step": "expired_caller_deadline", "expired_by_ns": int64(time.Second)})
	decisions = append(decisions, map[string]any{"step": "expired_caller_deadline", "timeout_ns": int64(sessionTimeout(expired))})
	oracleWrite(t, "session-timeout-inside-caller-deadline", oracleCase{
		Component: "modbusadapter-readonly-session",
		Source:    oracleSessionSource,
		Stimulus:  "TestH10SessionTimeoutStaysInsideCallerDeadline",
		Input: oracleInput{
			Qualifiers: map[string]any{"deadline_margin_ns": int64(sessionDeadlineMargin)},
			Clock:      map[string]any{"unit": "wall clock", "note": "the remaining time is measured when the function is called; only the pin test's own range checks are recorded for deadlines that remain"},
			State:      map[string]any{"steps": steps},
		},
		Output: oracleOutput{Decisions: decisions},
	})
}
