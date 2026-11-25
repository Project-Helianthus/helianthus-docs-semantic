package modbus

import (
	"context"
	"errors"
	"testing"
	"time"
)

func oracleBackoffInput(config BackoffConfig, jitter []time.Duration) map[string]any {
	return map[string]any{
		"floor_ns":            oracleNS(config.Floor),
		"ceiling_ns":          oracleNS(config.Ceiling),
		"max_attempts":        config.MaxAttempts,
		"jitter_algorithm_id": config.JitterAlgorithmID,
		"jitter_version":      config.JitterVersion,
		"jitter_evidence":     config.JitterEvidence,
		"jitter_sequence_ns":  oracleDurations(jitter),
	}
}

func oracleDurations(values []time.Duration) []any {
	out := make([]any, 0, len(values))
	for _, value := range values {
		out = append(out, oracleNS(value))
	}
	return out
}

func oracleBackoffCase(t *testing.T, name string, stimulus string, config BackoffConfig, jitter []time.Duration, steps []any, decisions []any, backoff *ReconnectBackoff) {
	t.Helper()
	counters := map[string]any{}
	if backoff != nil {
		counters["jitter_algorithm_id"] = backoff.JitterAlgorithmID()
		counters["jitter_version"] = backoff.JitterVersion()
		counters["jitter_evidence"] = backoff.JitterEvidence()
		counters["emitted_jitter_ns"] = oracleDurations(backoff.EmittedJitter())
	}
	oracleWrite(t, "backoff", name, oracleCase{
		Component: "modbus-reconnect-backoff",
		Source:    "tcp_scheduler.go",
		Stimulus:  stimulus,
		Input: oracleInput{
			Qualifiers: map[string]any{"config": oracleBackoffInput(config, jitter)},
			Clock:      map[string]any{"unit": "nanoseconds", "note": "the backoff has no clock; delays are returned and the caller passes its own offsets"},
			State:      map[string]any{"steps": steps},
		},
		Output: oracleOutput{Decisions: decisions, Counters: counters},
	})
}

func oracleRecordBackoff(t *testing.T) {
	t.Helper()
	{
		jitter := []time.Duration{10, 20, 30, 40}
		config := BackoffConfig{
			Floor: 100 * time.Millisecond, Ceiling: 350 * time.Millisecond, MaxAttempts: 4,
			Jitter: &sequenceJitter{values: jitter}, JitterAlgorithmID: "sequence", JitterVersion: "v1", JitterEvidence: "schedule:test-sequence",
		}
		backoff, err := newReconnectBackoff(config)
		if err != nil {
			t.Fatal(err)
		}
		var steps, decisions []any
		next := func() {
			steps = append(steps, "next_delay")
			delay, err := backoff.NextDelay()
			decisions = append(decisions, map[string]any{"step": "next_delay", "delay_ns": oracleNS(delay), "error": oracleErr(err)})
		}
		next()
		steps = append(steps, "connected")
		backoff.Connected()
		decisions = append(decisions, map[string]any{"step": "connected"})
		next()
		next()
		steps = append(steps, "valid_correlated_response")
		backoff.ValidCorrelatedResponse()
		decisions = append(decisions, map[string]any{"step": "valid_correlated_response"})
		next()
		oracleBackoffCase(t, "bounded-injected-resets-only-on-valid-response", "TestReconnectBackoffIsBoundedInjectedAndResetsOnlyOnValidResponse", config, jitter, steps, decisions, backoff)
	}
	{
		jitter := []time.Duration{0}
		config := BackoffConfig{
			Floor: time.Second, Ceiling: time.Second, MaxAttempts: 1,
			Jitter: &sequenceJitter{values: jitter}, JitterAlgorithmID: "zero", JitterVersion: "v1", JitterEvidence: "seed:0",
		}
		backoff, err := newReconnectBackoff(config)
		if err != nil {
			t.Fatal(err)
		}
		ctx, cancel := context.WithCancel(context.Background())
		delay := blockingDelay{started: make(chan time.Duration, 1)}
		done := make(chan error, 1)
		go func() { done <- backoff.WaitUntil(ctx, delay, 0, 2*time.Second) }()
		started := <-delay.started
		cancel()
		waitErr := <-done
		_, nextErr := backoff.NextDelay()
		steps := []any{
			map[string]any{"step": "wait_until", "now_offset_ns": 0, "deadline_offset_ns": oracleNS(2 * time.Second), "then": "cancel the context once the waiter started"},
			map[string]any{"step": "next_delay"},
		}
		decisions := []any{
			map[string]any{"step": "wait_until", "waiter_started_with_ns": oracleNS(started), "error": oracleErr(waitErr), "is_context_canceled": errors.Is(waitErr, context.Canceled)},
			map[string]any{"step": "next_delay", "error": oracleErr(nextErr)},
		}
		oracleBackoffCase(t, "wait-is-cancellation-aware", "TestReconnectBackoffWaitIsCancellationAware", config, jitter, steps, decisions, backoff)
	}
	{
		var backoff *ReconnectBackoff
		source := callbackJitter{callback: func() { backoff.ValidCorrelatedResponse() }}
		config := BackoffConfig{
			Floor: time.Second, Ceiling: 2 * time.Second, MaxAttempts: 2,
			Jitter: source, JitterAlgorithmID: "callback", JitterVersion: "v1", JitterEvidence: "schedule:zero",
		}
		var err error
		backoff, err = newReconnectBackoff(config)
		if err != nil {
			t.Fatal(err)
		}
		done := make(chan struct {
			delay time.Duration
			err   error
		}, 1)
		go func() {
			delay, nextErr := backoff.NextDelay()
			done <- struct {
				delay time.Duration
				err   error
			}{delay, nextErr}
		}()
		var decisions []any
		select {
		case result := <-done:
			decisions = append(decisions, map[string]any{"step": "next_delay", "completed": true, "delay_ns": oracleNS(result.delay), "error": oracleErr(result.err)})
		case <-time.After(time.Second):
			decisions = append(decisions, map[string]any{"step": "next_delay", "completed": false})
		}
		steps := []any{map[string]any{"step": "next_delay", "jitter_callback": "calls ValidCorrelatedResponse while the delay is computed", "completion_bound_ns": oracleNS(time.Second)}}
		oracleBackoffCase(t, "state-lock-not-held-across-jitter", "TestReconnectBackoffDoesNotHoldStateLockAcrossJitter", config, []time.Duration{0}, steps, decisions, backoff)
	}
	{
		jitter := []time.Duration{0}
		config := BackoffConfig{
			Floor: time.Second, Ceiling: time.Second, MaxAttempts: 1,
			Jitter: &sequenceJitter{values: jitter}, JitterAlgorithmID: "zero", JitterVersion: "v1", JitterEvidence: "seed:0",
		}
		backoff, err := newReconnectBackoff(config)
		if err != nil {
			t.Fatal(err)
		}
		delay := blockingDelay{started: make(chan time.Duration, 1)}
		waitErr := backoff.WaitUntil(context.Background(), delay, 500*time.Millisecond, time.Second)
		started := false
		select {
		case <-delay.started:
			started = true
		default:
		}
		steps := []any{map[string]any{"step": "wait_until", "now_offset_ns": oracleNS(500 * time.Millisecond), "deadline_offset_ns": oracleNS(time.Second)}}
		decisions := []any{map[string]any{"step": "wait_until", "error": oracleErr(waitErr), "waiter_started": started}}
		oracleBackoffCase(t, "delay-past-absolute-deadline-refused", "TestReconnectBackoffRefusesDelayPastAbsoluteDeadline", config, jitter, steps, decisions, backoff)
	}
}
