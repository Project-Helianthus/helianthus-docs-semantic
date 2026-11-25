//go:build linux

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"golang.org/x/sys/unix"
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

const oracleObserveSource = "cmd/gateway/tesla_observe_flow_linux.go"

func oracleTermiosRecord(termios *syscall.Termios) map[string]any {
	return map[string]any{
		"iflag": uint64(termios.Iflag), "oflag": uint64(termios.Oflag), "cflag": uint64(termios.Cflag), "lflag": uint64(termios.Lflag),
		"vmin": int(termios.Cc[syscall.VMIN]), "vtime": int(termios.Cc[syscall.VTIME]),
	}
}

func oracleErrText(err error) any {
	if err == nil {
		return nil
	}
	return err.Error()
}

// TestOracleTeslaObserve records the opener of the pin's Linux build: the
// scripted terminal-operation cases of the pin's own tests and, on a real
// pseudo terminal, the two end-to-end tests. It runs only on a Linux host.
func TestOracleTeslaObserve(t *testing.T) {
	oracleRecordObserveInitial(t)
	oracleRecordObserveOrder(t)
	oracleRecordObservePTYFlowControl(t)
	oracleRecordObservePTYFlush(t)
}

func oracleRecordObserveInitial(t *testing.T) {
	t.Helper()
	inherited := syscall.Termios{
		Iflag: syscall.IXON | syscall.IXOFF | syscall.IXANY,
		Lflag: syscall.ECHO | syscall.ICANON,
		Cflag: syscall.CS7 | syscall.PARENB,
	}
	before := oracleTermiosRecord(&inherited)
	var calls []any
	var requested map[string]any
	updates := 0
	ops := teslaSerialOps{
		termios: func(_ int, request uintptr, termios *syscall.Termios) error {
			switch request {
			case syscall.TCGETS:
				calls = append(calls, "TCGETS")
				*termios = inherited
			case syscall.TCSETS:
				calls = append(calls, "TCSETS")
				updates++
				requested = oracleTermiosRecord(termios)
				inherited = *termios
			default:
				calls = append(calls, map[string]any{"unexpected_request": uint64(request)})
			}
			return nil
		},
		flush: func(int) error { calls = append(calls, "flush"); return nil },
	}
	err := configureTeslaObserveSerial(0, ops)
	oracleWrite(t, "linux-initial-termios", oracleCase{
		Component: "tesla-observe-serial-opener-linux",
		Source:    oracleObserveSource,
		Stimulus:  "TestTeslaObserveInitialTermiosDisablesAutomaticTransmission",
		Input:     oracleInput{Qualifiers: map[string]any{"descriptor": 0, "inherited_termios": before}},
		Output: oracleOutput{
			Decisions: []any{map[string]any{"error": oracleErrText(err), "calls": calls, "requested_termios": requested}},
			Counters:  map[string]any{"termios_updates": updates},
		},
	})
}

func oracleRecordObserveOrder(t *testing.T) {
	t.Helper()
	flushFailure := errors.New("synthetic flush failure")
	setFailure := errors.New("synthetic update failure")
	cases := []struct {
		name     string
		readBack func(*syscall.Termios)
		setErr   error
		flushErr error
	}{
		{name: "applied"},
		{name: "update-fails", setErr: setFailure},
		{name: "echo-remains", readBack: func(x *syscall.Termios) { x.Lflag |= syscall.ECHO }},
		{name: "input-flow-control-remains", readBack: func(x *syscall.Termios) { x.Iflag |= syscall.IXOFF }},
		{name: "baud-coerced", readBack: func(x *syscall.Termios) { x.Cflag = x.Cflag&^syscall.B115200 | syscall.B9600 }},
		{name: "character-size-coerced", readBack: func(x *syscall.Termios) { x.Cflag = x.Cflag&^syscall.CSIZE | syscall.CS7 }},
		{name: "parity-enabled", readBack: func(x *syscall.Termios) { x.Cflag |= syscall.PARENB }},
		{name: "odd-parity-enabled", readBack: func(x *syscall.Termios) { x.Cflag |= syscall.PARODD }},
		{name: "two-stop-bits", readBack: func(x *syscall.Termios) { x.Cflag |= syscall.CSTOPB }},
		{name: "receiver-disabled", readBack: func(x *syscall.Termios) { x.Cflag &^= syscall.CREAD }},
		{name: "local-mode-disabled", readBack: func(x *syscall.Termios) { x.Cflag &^= syscall.CLOCAL }},
		{name: "hardware-flow-control-enabled", readBack: func(x *syscall.Termios) { x.Cflag |= unix.CRTSCTS }},
		{name: "canonical-mode-enabled", readBack: func(x *syscall.Termios) { x.Lflag |= syscall.ICANON }},
		{name: "signals-enabled", readBack: func(x *syscall.Termios) { x.Lflag |= syscall.ISIG }},
		{name: "output-processing-enabled", readBack: func(x *syscall.Termios) { x.Oflag |= syscall.OPOST }},
		{name: "input-translation-enabled", readBack: func(x *syscall.Termios) { x.Iflag |= syscall.ICRNL }},
		{name: "minimum-read-coerced", readBack: func(x *syscall.Termios) { x.Cc[syscall.VMIN] = 0 }},
		{name: "read-timeout-coerced", readBack: func(x *syscall.Termios) { x.Cc[syscall.VTIME] = 1 }},
		{name: "flush-fails", flushErr: flushFailure},
	}
	for _, tc := range cases {
		var calls []any
		gets := 0
		var requested syscall.Termios
		var readBack map[string]any
		ops := teslaSerialOps{
			termios: func(_ int, request uintptr, termios *syscall.Termios) error {
				switch request {
				case syscall.TCGETS:
					calls = append(calls, "TCGETS")
					gets++
					*termios = syscall.Termios{Iflag: syscall.IXOFF, Lflag: syscall.ECHO}
					if gets == 2 {
						*termios = requested
						if tc.readBack != nil {
							tc.readBack(termios)
						}
						readBack = oracleTermiosRecord(termios)
					}
				case syscall.TCSETS:
					calls = append(calls, "TCSETS")
					requested = *termios
					return tc.setErr
				default:
					calls = append(calls, map[string]any{"unexpected_request": uint64(request)})
				}
				return nil
			},
			flush: func(int) error {
				calls = append(calls, "flush")
				return tc.flushErr
			},
		}
		err := configureTeslaObserveSerial(0, ops)
		oracleWrite(t, "linux-configuration-"+tc.name, oracleCase{
			Component: "tesla-observe-serial-opener-linux",
			Source:    oracleObserveSource,
			Stimulus:  "TestTeslaObserveConfigurationOrderAndFlushFailures/" + tc.name,
			Input: oracleInput{Qualifiers: map[string]any{
				"descriptor": 0, "case": tc.name, "update_error": oracleErrText(tc.setErr), "flush_error": oracleErrText(tc.flushErr),
				"first_read_termios":     map[string]any{"iflag": uint64(syscall.IXOFF), "lflag": uint64(syscall.ECHO)},
				"read_back_is_requested": "the second read returns the requested settings after the named change",
			}},
			Output: oracleOutput{Decisions: []any{map[string]any{
				"error": oracleErrText(err), "is_update_error": tc.setErr != nil && errors.Is(err, tc.setErr), "is_flush_error": tc.flushErr != nil && errors.Is(err, tc.flushErr),
				"calls": calls, "requested_termios": oracleTermiosRecord(&requested), "read_back_termios": readBack,
			}}},
		})
	}
}

func oracleRecordObservePTYFlowControl(t *testing.T) {
	t.Helper()
	pty := newTeslaTestPTY(t)
	pty.inherit(t)
	updates, flushes := 0, 0
	var permitted []any
	ops := teslaSerialOps{
		termios: func(fd int, request uintptr, settings *syscall.Termios) error {
			if request == syscall.TCSETS {
				updates++
				permitted = append(permitted, map[string]any{
					"automatic_transmission_permitted":   settings.Iflag&(syscall.IXON|syscall.IXOFF|syscall.IXANY) != 0 || settings.Lflag&syscall.ECHO != 0,
					"format_is_115200_8n1_receive_local": settings.Cflag == syscall.B115200|syscall.CS8|syscall.CREAD|syscall.CLOCAL,
				})
			}
			return teslaTermios(fd, request, settings)
		},
		flush: func(fd int) error {
			flushes++
			return teslaFlushQueues(fd)
		},
	}
	err := configureTeslaObserveSerial(pty.deviceFD, ops)
	var got syscall.Termios
	readErr := teslaTermios(pty.deviceFD, syscall.TCGETS, &got)
	oracleWrite(t, "linux-pty-disables-inherited-flow-control", oracleCase{
		Component: "tesla-observe-serial-opener-linux",
		Source:    oracleObserveSource,
		Stimulus:  "TestTeslaObserveDisablesInheritedSoftwareFlowControl",
		Input:     oracleInput{Qualifiers: map[string]any{"terminal": "a pseudo terminal whose device side inherited software flow control and echo", "inherited_flags": "IXON, IXOFF, IXANY, ECHO, canonical mode off"}},
		Output: oracleOutput{
			Decisions: []any{map[string]any{
				"error": oracleErrText(err), "read_back_error": oracleErrText(readErr), "updates": permitted,
				"automatic_transmission_still_enabled": got.Iflag&(syscall.IXON|syscall.IXOFF|syscall.IXANY) != 0 || got.Lflag&syscall.ECHO != 0,
			}},
			Counters: map[string]any{"termios_updates": updates, "flushes": flushes},
		},
	})
}

func oracleRecordObservePTYFlush(t *testing.T) {
	t.Helper()
	pty := newTeslaTestPTY(t)
	pty.inherit(t)
	stale := bytes.Repeat([]byte{0x42}, 64)
	if _, err := pty.control.Write(stale); err != nil {
		t.Fatal(err)
	}
	echo := pty.echoed(t, len(stale), 2*time.Second)
	pty.waitQueuedInput(t, len(stale))
	stream, err := openTeslaObserveSerial(pty.path)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = stream.Close() }()
	queuedAfter := pty.queuedInput(t)
	quiet, quietCancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer quietCancel()
	staleValue, staleErr := stream.ReceiveByte(quiet)
	fresh := bytes.Repeat([]byte{0x43}, 8192)
	if _, err := pty.control.Write(fresh); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	received, mismatches := 0, 0
	var receiveErr error
	for range fresh {
		value, err := stream.ReceiveByte(ctx)
		if err != nil {
			receiveErr = err
			break
		}
		received++
		if value != 0x43 {
			mismatches++
		}
	}
	afterEcho := pty.echoed(t, 1, 50*time.Millisecond)
	canceled, stop := context.WithCancel(context.Background())
	stop()
	_, canceledErr := stream.ReceiveByte(canceled)
	oracleWrite(t, "linux-pty-flushes-traffic-before-configuration", oracleCase{
		Component: "tesla-observe-serial-opener-linux",
		Source:    oracleObserveSource,
		Stimulus:  "TestTeslaObserveFlushesTrafficReceivedBeforeConfiguration",
		Input: oracleInput{
			Bytes:      "42",
			Qualifiers: map[string]any{"terminal": "a pseudo terminal whose device side inherited software flow control and echo", "stale_bytes": len(stale), "stale_byte": 0x42, "fresh_bytes": len(fresh), "fresh_byte": 0x43, "quiet_receive_bound_ns": int64(100 * time.Millisecond), "fresh_receive_bound_ns": int64(5 * time.Second)},
		},
		Output: oracleOutput{
			Decisions: []any{map[string]any{
				"stale_bytes_echoed_before_configuration": len(echo), "stale_bytes_queued_before_open": len(stale),
				"queued_after_open": queuedAfter, "stale_receive_error": oracleErrText(staleErr), "stale_receive_error_is_deadline": errors.Is(staleErr, context.DeadlineExceeded), "stale_receive_value": int(staleValue),
				"fresh_bytes_received": received, "fresh_bytes_mismatched": mismatches, "fresh_receive_error": oracleErrText(receiveErr),
				"bytes_echoed_after_configuration": len(afterEcho),
				"canceled_receive_error":           oracleErrText(canceledErr), "canceled_receive_is_canceled": errors.Is(canceledErr, context.Canceled),
			}},
		},
	})
}
