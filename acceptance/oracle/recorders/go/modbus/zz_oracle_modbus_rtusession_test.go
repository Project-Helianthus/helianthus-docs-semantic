package modbus

import (
	"context"
	"io"
	"sync"
	"testing"
	"time"
)

type oracleRTUStream struct {
	inner    RTUByteStream
	fake     *rtuSessionFakeStream
	mu       sync.Mutex
	frames   []any
	reads    []any
	scripted bool
}

func (stream *oracleRTUStream) ReadRTUByte(ctx context.Context) (byte, time.Duration, error) {
	scripted := stream.fake != nil && len(stream.fake.actions) != 0
	value, offset, err := stream.inner.ReadRTUByte(ctx)
	if scripted {
		stream.mu.Lock()
		stream.reads = append(stream.reads, map[string]any{"byte": int(value), "offset_ns": oracleNS(offset), "error": oracleErr(err)})
		stream.mu.Unlock()
	}
	return value, offset, err
}

func (stream *oracleRTUStream) WriteRTU(ctx context.Context, frame []byte) (int, error) {
	written, err := stream.inner.WriteRTU(ctx, frame)
	stream.mu.Lock()
	stream.frames = append(stream.frames, map[string]any{"frame": oracleHex(frame), "written": written, "error": oracleErr(err)})
	stream.mu.Unlock()
	return written, err
}

func (stream *oracleRTUStream) RTUOffset() time.Duration { return stream.inner.RTUOffset() }

func oracleRTUTimingRecord(timing RTUTiming) map[string]any {
	return map[string]any{
		"baud": 115200, "data_bits": 8, "parity": "even", "stop_bits": 1,
		"configured_max_response_latency_ns": oracleNS(20 * time.Millisecond),
		"configured_max_quiescence_ns":       oracleNS(100 * time.Millisecond),
		"character_time_ns":                  oracleNS(timing.CharacterTime()),
		"inter_character_ns":                 oracleNS(timing.InterCharacter()),
		"inter_frame_ns":                     oracleNS(timing.InterFrame()),
		"max_response_latency_ns":            oracleNS(timing.MaxResponseLatency()),
		"max_quiescence_ns":                  oracleNS(timing.MaxQuiescence()),
	}
}

func oracleActions(actions []rtuSessionAction) []any {
	out := make([]any, 0, len(actions))
	for _, action := range actions {
		record := map[string]any{"byte": int(action.value), "offset_ns": oracleNS(action.offset), "error": nil}
		if action.err != nil {
			record["error"] = action.err.Error()
		}
		out = append(out, record)
	}
	return out
}

func oracleResponses(responses []RTUPrivateFunctionResponseADU) []any {
	out := make([]any, 0, len(responses))
	for _, response := range responses {
		out = append(out, map[string]any{"adu": oracleHex(response.Bytes()), "payload": oracleHex(response.Payload())})
	}
	return out
}

type oracleRTUScenario struct {
	name      string
	stimulus  string
	stream    RTUByteStream
	fake      *rtuSessionFakeStream
	config    RTUSessionConfig
	script    []rtuSessionAction
	streamSet map[string]any
	steps     []any
	decisions []any
	session   *RTUSession
	request   PrivateFunctionRequest
	timing    RTUTiming
	t         *testing.T
	recorder  *oracleRTUStream
}

func newOracleRTUScenario(t *testing.T, name string, stimulus string, fake *rtuSessionFakeStream, streamSet map[string]any) *oracleRTUScenario {
	t.Helper()
	scenario := &oracleRTUScenario{t: t, name: name, stimulus: stimulus, fake: fake, streamSet: streamSet, timing: rtuTestTiming(t, 115200)}
	if fake != nil {
		scenario.script = append([]rtuSessionAction(nil), fake.actions...)
		scenario.recorder = &oracleRTUStream{inner: fake, fake: fake}
		scenario.stream = scenario.recorder
	}
	return scenario
}

func (scenario *oracleRTUScenario) open(maxFrames uint8, enabled bool, step string) {
	scenario.t.Helper()
	config := RTUSessionConfig{Stream: scenario.stream, Timing: scenario.timing, Enabled: enabled, MaxResponseFrames: maxFrames}
	session, err := NewRTUSession(config)
	scenario.steps = append(scenario.steps, map[string]any{"step": step, "enabled": enabled, "max_response_frames": int(maxFrames)})
	scenario.decisions = append(scenario.decisions, map[string]any{"step": step, "error": oracleErr(err), "session_returned": session != nil})
	if err == nil {
		scenario.session = session
	}
}

func (scenario *oracleRTUScenario) exchange(ctx context.Context, step string, unit byte, request PrivateFunctionRequest, policy PrivateFunctionResponsePolicy) {
	scenario.t.Helper()
	scenario.request = request
	adu, aduErr := EncodeRTUPrivateFunctionADU(unit, request)
	responses, err := scenario.session.Exchange(ctx, unit, request, policy)
	scenario.steps = append(scenario.steps, map[string]any{
		"step": step, "unit": int(unit), "request_adu": oracleHex(adu), "request_adu_error": oracleErr(aduErr),
		"policy_max_attempts": int(policy.MaxAttempts()), "policy_replay_safe": policy.ReplaySafe(),
	})
	scenario.decisions = append(scenario.decisions, map[string]any{"step": step, "responses": oracleResponses(responses), "error": oracleErr(err)})
}

func (scenario *oracleRTUScenario) recover(step string) {
	scenario.t.Helper()
	err := scenario.session.Recover(context.Background())
	scenario.steps = append(scenario.steps, map[string]any{"step": step})
	scenario.decisions = append(scenario.decisions, map[string]any{"step": step, "error": oracleErr(err)})
}

func (scenario *oracleRTUScenario) write(offsetStable bool, writes int) {
	scenario.t.Helper()
	counters := map[string]any{"stream_write_calls": writes}
	if offsetStable && scenario.fake != nil {
		counters["final_stream_offset_ns"] = oracleNS(scenario.fake.RTUOffset())
	}
	var observations []any
	var symbols []any
	if scenario.recorder != nil {
		scenario.recorder.mu.Lock()
		symbols = append(symbols, scenario.recorder.frames...)
		observations = append(observations, scenario.recorder.reads...)
		scenario.recorder.mu.Unlock()
	}
	oracleWrite(scenario.t, "rtu-session", scenario.name, oracleCase{
		Component: "modbus-rtu-session",
		Source:    "rtu_session.go",
		Stimulus:  scenario.stimulus,
		Input: oracleInput{
			Qualifiers: map[string]any{"timing": oracleRTUTimingRecord(scenario.timing), "stream": scenario.streamSet},
			Clock:      map[string]any{"unit": "stream offset", "note": "byte receipt offsets are scripted by the stream; context timeouts use the wall clock"},
			State:      map[string]any{"scripted_reads": oracleActions(scenario.script), "steps": scenario.steps},
		},
		Output: oracleOutput{SymbolsWritten: symbols, Decisions: scenario.decisions, Observations: observations, Counters: counters},
	})
}

func oracleRecordRTUSession(t *testing.T) {
	t.Helper()
	privateRequest := func(code byte, payload []byte) PrivateFunctionRequest {
		return newSessionPrivateFunctionRequest(t, code, payload)
	}
	{
		fake := &rtuSessionFakeStream{}
		scenario := newOracleRTUScenario(t, "single-flight-and-recover", "TestRTUSessionIsSingleFlightAndDisabledUntilExplicitlyEnabled", fake, map[string]any{"script": "empty", "write_result": "full"})
		scenario.open(0, true, "open")
		request := privateRequest(0x64, []byte{0})
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		scenario.exchange(ctx, "exchange_with_one_second_context", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		cancel()
		writesAfterFirst := fake.writes
		fake.writeN = 0
		fake.writeErr = nil
		scenario.recover("recover")
		scenario.exchange(context.Background(), "exchange_after_recovery", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.decisions = append(scenario.decisions, map[string]any{"step": "writes", "after_first_exchange": writesAfterFirst, "after_recovery": fake.writes})
		scenario.write(false, fake.writes)
	}
	{
		fake := newRTUSessionFakeStream()
		fake.writeResults = []rtuSessionWriteResult{{err: io.ErrClosedPipe}, {}}
		scenario := newOracleRTUScenario(t, "retries-only-proven-zero-byte-replay-safe-write", "TestRTUSessionRetriesOnlyProvenZeroByteReplaySafeWrite", fake, map[string]any{"script": "empty", "write_results": []any{map[string]any{"written": 0, "error": io.ErrClosedPipe.Error()}, map[string]any{"written": "full", "error": nil}}})
		scenario.open(0, true, "open")
		policy, err := NewPrivateFunctionResponsePolicy(2, true)
		if err != nil {
			t.Fatal(err)
		}
		scenario.exchange(context.Background(), "exchange_two_attempts_replay_safe", 0x10, privateRequest(0x66, nil), policy)
		scenario.write(false, fake.writes)
	}
	{
		stream := &blockingRTUSessionStream{writeStarted: make(chan struct{}), release: make(chan struct{})}
		session, err := NewRTUSession(RTUSessionConfig{Stream: &oracleRTUStream{inner: stream}, Timing: rtuTestTiming(t, 115200), Enabled: true})
		if err != nil {
			t.Fatal(err)
		}
		recorder := session.stream.(*oracleRTUStream)
		request := privateRequest(0x64, nil)
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		finished := make(chan error, 2)
		go func() {
			_, err := session.Exchange(ctx, 0x10, request, DefaultPrivateFunctionResponsePolicy())
			finished <- err
		}()
		<-stream.writeStarted
		go func() {
			_, err := session.Exchange(ctx, 0x10, request, DefaultPrivateFunctionResponsePolicy())
			finished <- err
		}()
		time.Sleep(5 * time.Millisecond)
		concurrent := stream.WriteCount()
		close(stream.release)
		firstErr := <-finished
		secondErr := <-finished
		cancel()
		adu, _ := EncodeRTUPrivateFunctionADU(0x10, request)
		recorder.mu.Lock()
		frames := append([]any(nil), recorder.frames...)
		recorder.mu.Unlock()
		oracleWrite(t, "rtu-session", "serializes-concurrent-exchanges", oracleCase{
			Component: "modbus-rtu-session",
			Source:    "rtu_session.go",
			Stimulus:  "TestRTUSessionSerializesConcurrentExchanges",
			Input: oracleInput{
				Qualifiers: map[string]any{"timing": oracleRTUTimingRecord(rtuTestTiming(t, 115200)), "stream": map[string]any{"kind": "blocking", "write_blocks_until": "released by the caller", "reads": "block until the context ends"}},
				Clock:      map[string]any{"unit": "stream offset", "note": "the blocking stream reports a constant offset of two milliseconds; the second exchange starts five milliseconds of wall time after the first write began"},
				State: map[string]any{"steps": []any{
					map[string]any{"step": "first_exchange", "unit": 0x10, "request_adu": oracleHex(adu), "context_timeout_ns": oracleNS(time.Second)},
					map[string]any{"step": "second_exchange_after_first_write_started", "unit": 0x10, "request_adu": oracleHex(adu), "context_timeout_ns": oracleNS(time.Second)},
					map[string]any{"step": "release_the_blocked_write_after_five_milliseconds"},
				}},
			},
			Output: oracleOutput{
				SymbolsWritten: frames,
				Decisions: []any{
					map[string]any{"step": "first_exchange", "error": oracleErr(firstErr)},
					map[string]any{"step": "second_exchange", "error": oracleErr(secondErr)},
				},
				Counters: map[string]any{"write_calls_while_second_waited": concurrent, "write_calls_at_end": stream.WriteCount()},
			},
		})
	}
	{
		request := privateRequest(0x64, []byte{0})
		code := request.FunctionCode()
		fake := newRTUSessionFakeStream(
			rtuSessionBytes(makePrivateFunctionRTUFrame(t, 0x10, code, []byte{0}), 0),
			rtuSessionGap(3*time.Millisecond),
			rtuSessionBytes(makePrivateFunctionRTUFrame(t, 0x10, code, []byte{1, 2}), 4*time.Millisecond),
			rtuSessionGap(7*time.Millisecond),
		)
		scenario := newOracleRTUScenario(t, "retains-multiple-opaque-frames-until-response-bound", "TestRTUSessionRetainsMultipleOpaqueFramesUntilResponseBound", fake, map[string]any{"script": "two response frames with a gap after each", "write_result": "full"})
		scenario.open(0, true, "open")
		scenario.exchange(context.Background(), "exchange", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.write(false, fake.writes)
	}
	{
		request := privateRequest(0x64, []byte{0})
		code := request.FunctionCode()
		fake := newRTUSessionFakeStream(
			rtuSessionBytes(makePrivateFunctionRTUFrame(t, 0x10, code, []byte{0}), 0),
			rtuSessionGap(3*time.Millisecond),
			rtuSessionBytes(makePrivateFunctionRTUFrame(t, 0x10, code, []byte{1}), 4*time.Millisecond),
			rtuSessionGap(7*time.Millisecond),
		)
		scenario := newOracleRTUScenario(t, "response-frame-overflow-quarantines", "TestRTUSessionQuarantinesResponseFrameOverflow", fake, map[string]any{"script": "two response frames with a gap after each", "write_result": "full"})
		scenario.open(1, true, "open_max_one_response_frame")
		scenario.exchange(context.Background(), "exchange", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.exchange(context.Background(), "exchange_successor", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.write(false, fake.writes)
	}
	{
		fake := newRTUSessionFakeStream()
		scenario := newOracleRTUScenario(t, "rejects-disabled-and-local-failures-without-write", "TestRTUSessionRejectsDisabledAndLocalFailuresWithoutWrite", fake, map[string]any{"script": "empty", "write_result": "full"})
		scenario.open(0, false, "open_disabled")
		scenario.open(0, true, "open_enabled")
		scenario.exchange(context.Background(), "exchange_invalid_local_request", 0, PrivateFunctionRequest{}, DefaultPrivateFunctionResponsePolicy())
		scenario.write(true, fake.writes)
	}
	{
		fake := newRTUSessionFakeStream()
		fake.writeN = 1
		fake.writeErr = io.ErrUnexpectedEOF
		scenario := newOracleRTUScenario(t, "partial-write-quarantines-successor", "TestRTUSessionPartialWriteQuarantinesSuccessor", fake, map[string]any{"script": "empty", "write_result": map[string]any{"written": 1, "error": io.ErrUnexpectedEOF.Error()}})
		scenario.open(0, true, "open")
		request := privateRequest(0x65, nil)
		scenario.exchange(context.Background(), "exchange_partial_write", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.exchange(context.Background(), "exchange_successor", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.write(true, fake.writes)
	}
	{
		fake := newRTUSessionFakeStream(rtuSessionGap(0))
		fake.writeN = 1
		fake.writeErr = io.ErrUnexpectedEOF
		scenario := newOracleRTUScenario(t, "recovery-requires-monotonic-quiet-proof", "TestRTUSessionRecoveryRequiresMonotonicQuietProof", fake, map[string]any{"script": "one gap at offset zero", "write_result": map[string]any{"written": 1, "error": io.ErrUnexpectedEOF.Error()}})
		scenario.open(0, true, "open")
		request := privateRequest(0x65, nil)
		scenario.exchange(context.Background(), "exchange_partial_write", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.recover("recover_without_proof")
		fake.writeN = 0
		fake.writeErr = nil
		scenario.exchange(context.Background(), "exchange_successor_after_failed_recovery", 0x10, request, DefaultPrivateFunctionResponsePolicy())
		scenario.write(true, fake.writes)
	}
	for _, tc := range []struct {
		name     string
		stimulus string
		first    func(RTUTiming) time.Duration
		second   func(RTUTiming) time.Duration
	}{
		{"recovery-waits-response-horizon-before-quiet-proof", "TestRTUSessionRecoveryWaitsResponseHorizonBeforeQuietProof",
			func(timing RTUTiming) time.Duration { return timing.InterFrame() + 1 },
			func(timing RTUTiming) time.Duration { return timing.MaxResponseLatency() + timing.InterFrame() + 1 }},
		{"recovery-requires-quiet-proof-after-response-horizon", "TestRTUSessionRecoveryRequiresQuietProofAfterResponseHorizon",
			func(timing RTUTiming) time.Duration { return timing.MaxResponseLatency() },
			func(timing RTUTiming) time.Duration { return timing.MaxResponseLatency() + timing.InterFrame() + 1 }},
	} {
		timing := rtuTestTiming(t, 115200)
		fake := newRTUSessionFakeStream(rtuSessionGap(tc.first(timing)), rtuSessionGap(tc.second(timing)))
		fake.writeN = 1
		fake.writeErr = io.ErrUnexpectedEOF
		scenario := newOracleRTUScenario(t, tc.name, tc.stimulus, fake, map[string]any{"script": "two gaps", "write_result": map[string]any{"written": 1, "error": io.ErrUnexpectedEOF.Error()}})
		scenario.open(0, true, "open")
		scenario.exchange(context.Background(), "exchange_partial_write", 0x10, privateRequest(0x65, nil), DefaultPrivateFunctionResponsePolicy())
		scenario.recover("recover")
		scenario.decisions = append(scenario.decisions, map[string]any{
			"step": "offset_after_recovery", "offset_ns": oracleNS(fake.RTUOffset()),
			"at_least_response_latency_plus_inter_frame": fake.RTUOffset() >= timing.MaxResponseLatency()+timing.InterFrame(),
		})
		scenario.write(true, fake.writes)
	}
}
