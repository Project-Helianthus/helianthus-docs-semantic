//go:build linux

package main

import (
	"context"
	"encoding/hex"
	"errors"
	"net"
	"testing"
	"time"

	"golang.org/x/sys/unix"
)

// The BMS opener of the pin calls the operating system directly. In the scratch
// copy that the recorder runs, each operand is replaced by the function below
// that carries the same name and signature; nothing else of the opener changes.
type oracleBMSOperands struct {
	lookup     func(string) (*net.Interface, error)
	socket     func(int, int, int) (int, error)
	setsockopt func(int, int, int, int) error
	bind       func(int, unix.Sockaddr) error
	poll       func([]unix.PollFd, int) (int, error)
	read       func(int, []byte) (int, error)
	close      func(int) error
}

var oracleBMS oracleBMSOperands

func oracleBMSLookup(name string) (*net.Interface, error) { return oracleBMS.lookup(name) }
func oracleBMSSocket(domain, kind, protocol int) (int, error) {
	return oracleBMS.socket(domain, kind, protocol)
}
func oracleBMSSetsockoptInt(fd, level, option, value int) error {
	return oracleBMS.setsockopt(fd, level, option, value)
}
func oracleBMSBind(fd int, address unix.Sockaddr) error { return oracleBMS.bind(fd, address) }
func oracleBMSPoll(fds []unix.PollFd, timeout int) (int, error) {
	return oracleBMS.poll(fds, timeout)
}
func oracleBMSRead(fd int, buffer []byte) (int, error) { return oracleBMS.read(fd, buffer) }
func oracleBMSClose(fd int) error                      { return oracleBMS.close(fd) }

// oracleProjectReadings replaces the one reading of the shared receive clock:
// the project opener computes time.Since(growattProjectClockOrigin), and the
// scratch copy hands that origin to oracleProjectSince instead.
var (
	oracleProjectReadings []time.Duration
	oracleProjectOrigins  []time.Time
)

func oracleProjectSince(origin time.Time) time.Duration {
	oracleProjectOrigins = append(oracleProjectOrigins, origin)
	return oracleProjectReadings[len(oracleProjectOrigins)-1]
}

type oracleCalls struct{ list []any }

func (c *oracleCalls) add(operation string, fields map[string]any) {
	record := map[string]any{"step": len(c.list) + 1, "operation": operation}
	for key, value := range fields {
		record[key] = value
	}
	c.list = append(c.list, record)
}

func oracleSymbol(value int, name string, symbol int) any {
	if value == symbol {
		return name
	}
	return value
}

func oracleSocketFields(domain, kind, protocol int) map[string]any {
	return map[string]any{
		"domain":   oracleSymbol(domain, "AF_CAN", unix.AF_CAN),
		"type":     oracleSymbol(kind, "SOCK_RAW|SOCK_NONBLOCK|SOCK_CLOEXEC", unix.SOCK_RAW|unix.SOCK_NONBLOCK|unix.SOCK_CLOEXEC),
		"protocol": oracleSymbol(protocol, "CAN_RAW", unix.CAN_RAW),
	}
}

// oracleSyntheticFrame is one struct can_frame record: identifier 0x311 in
// native byte order of the record layout (little endian), data length 8, three
// pad bytes and eight synthetic data bytes.
var oracleSyntheticFrame = []byte{0x11, 0x03, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08}

func oracleBMSScript(calls *oracleCalls, lookup func(string) (*net.Interface, error)) oracleBMSOperands {
	return oracleBMSOperands{
		lookup: func(name string) (*net.Interface, error) {
			calls.add("lookup", map[string]any{"name": name})
			return lookup(name)
		},
		socket: func(domain, kind, protocol int) (int, error) {
			fields := oracleSocketFields(domain, kind, protocol)
			calls.add("socket", fields)
			return 11, nil
		},
		setsockopt: func(fd, level, option, value int) error {
			calls.add("setsockopt", map[string]any{
				"fd":     fd,
				"level":  oracleSymbol(level, "SOL_CAN_RAW", unix.SOL_CAN_RAW),
				"option": oracleSymbol(option, "CAN_RAW_FD_FRAMES", unix.CAN_RAW_FD_FRAMES),
				"value":  value,
			})
			return nil
		},
		bind: func(fd int, address unix.Sockaddr) error {
			can, ok := address.(*unix.SockaddrCAN)
			if !ok {
				return errors.New("bind address is not a CAN address")
			}
			calls.add("bind", map[string]any{"fd": fd, "ifindex": can.Ifindex})
			return nil
		},
		poll: func(fds []unix.PollFd, timeout int) (int, error) {
			calls.add("poll", map[string]any{"fds": len(fds), "fd": fds[0].Fd, "events": oracleSymbol(int(fds[0].Events), "POLLIN", unix.POLLIN), "timeout_ms": timeout})
			fds[0].Revents = unix.POLLIN
			return 1, nil
		},
		read: func(fd int, buffer []byte) (int, error) {
			calls.add("read", map[string]any{"fd": fd, "buffer_length": len(buffer)})
			return copy(buffer, oracleSyntheticFrame), nil
		},
		close: func(fd int) error {
			calls.add("close", map[string]any{"fd": fd})
			return nil
		},
	}
}

func oracleBMSInterface(name string, index int) func(string) (*net.Interface, error) {
	return func(string) (*net.Interface, error) { return &net.Interface{Name: name, Index: index}, nil }
}

func oracleBMSOutcome(receiver growattBMSCANReceiver, err error) map[string]any {
	return map[string]any{
		"receiver_returned": receiver != nil,
		"error":             oracleCanError(err),
		"is_config_error":   errors.Is(err, errGrowattBMSCANConfig),
		"is_identity_error": errors.Is(err, errGrowattBMSCANIdentity),
	}
}

func TestOracleCanReceive(t *testing.T) {
	const configured = "synthetic0"
	t.Run("linux-bms-receive", func(t *testing.T) {
		calls := &oracleCalls{}
		oracleBMS = oracleBMSScript(calls, oracleBMSInterface(configured, 3))
		receiver, err := openGrowattBMSCANSocket(configured)
		result := map[string]any{"open": oracleBMSOutcome(receiver, err)}
		if err != nil {
			t.Fatal(err)
		}
		identity := receiver.Identity()
		result["identity"] = map[string]any{"name": identity.Name, "index": identity.Index}
		record, err := receiver.Receive(context.Background())
		result["receive"] = map[string]any{
			"error":                     oracleCanError(err),
			"raw_hex":                   hex.EncodeToString(record.Raw),
			"interface":                 map[string]any{"name": record.Interface.Name, "index": record.Interface.Index},
			"raw_length":                len(record.Raw),
			"interface_equals_identity": record.Interface == identity,
		}
		result["close"] = map[string]any{"error": oracleCanError(receiver.Close())}
		oracleCanWrite(t, "linux-bms-receive", "linux", "growatt-bms-can-socketcan-opener-linux",
			"openGrowattBMSCANSocket, Identity, Receive and Close run in order against scripted operands of the opener",
			map[string]any{
				"configured_name": configured,
				"lookup":          map[string]any{"name": configured, "index": 3},
				"socket_fd":       11,
				"raw_hex":         hex.EncodeToString(oracleSyntheticFrame),
				"poll":            "ready for reading",
				"context":         "background, no deadline",
			}, calls.list, result)
	})
	t.Run("linux-bms-identity-mismatch", func(t *testing.T) {
		calls := &oracleCalls{}
		attempts := []any{}
		for _, scripted := range []struct {
			label string
			name  string
			index int
		}{{"different-name", "other0", 3}, {"index-zero", configured, 0}, {"index-negative", configured, -1}} {
			before := len(calls.list)
			oracleBMS = oracleBMSScript(calls, oracleBMSInterface(scripted.name, scripted.index))
			receiver, err := openGrowattBMSCANSocket(configured)
			attempts = append(attempts, map[string]any{"attempt": scripted.label, "operations": len(calls.list) - before, "outcome": oracleBMSOutcome(receiver, err)})
		}
		oracleCanWrite(t, "linux-bms-identity-mismatch", "linux", "growatt-bms-can-socketcan-opener-linux",
			"openGrowattBMSCANSocket is called three times; the scripted lookup returns a different name, index zero and a negative index",
			map[string]any{
				"configured_name": configured,
				"lookups":         []any{map[string]any{"name": "other0", "index": 3}, map[string]any{"name": configured, "index": 0}, map[string]any{"name": configured, "index": -1}},
			}, calls.list, map[string]any{"attempts": attempts})
	})
	t.Run("linux-bms-missing-interface", func(t *testing.T) {
		calls := &oracleCalls{}
		lookupFailure := errors.New("synthetic interface lookup failure")
		oracleBMS = oracleBMSScript(calls, func(string) (*net.Interface, error) { return nil, lookupFailure })
		receiver, err := openGrowattBMSCANSocket(configured)
		outcome := oracleBMSOutcome(receiver, err)
		outcome["wraps_scripted_failure"] = errors.Is(err, lookupFailure)
		oracleCanWrite(t, "linux-bms-missing-interface", "linux", "growatt-bms-can-socketcan-opener-linux",
			"openGrowattBMSCANSocket is called once; the scripted lookup fails and the configured name is never looked up in the operating system",
			map[string]any{"configured_name": configured, "lookup_error": lookupFailure.Error()}, calls.list, map[string]any{"open": outcome})
	})
	t.Run("linux-project-reopen-clock", func(t *testing.T) {
		calls := &oracleCalls{}
		readings := []time.Duration{2 * time.Millisecond, 7 * time.Millisecond, 9 * time.Millisecond}
		// The 16 raw bytes every scripted read delivers: zero but for byte 4, which is 8. The case input serializes them.
		stimulus := make([]byte, 16)
		stimulus[4] = 8
		oracleProjectReadings, oracleProjectOrigins = readings, nil
		ops := growattProjectSyscalls{
			lookup: func(name string) (*net.Interface, error) {
				calls.add("lookup", map[string]any{"name": name})
				return &net.Interface{Name: name, Index: 7}, nil
			},
			socket: func(domain, kind, protocol int) (int, error) {
				calls.add("socket", oracleSocketFields(domain, kind, protocol))
				return 9, nil
			},
			bind: func(fd int, address unix.Sockaddr) error {
				calls.add("bind", map[string]any{"fd": fd, "ifindex": address.(*unix.SockaddrCAN).Ifindex})
				return nil
			},
			poll: func(fds []unix.PollFd, timeout int) (int, error) {
				calls.add("poll", map[string]any{"fds": len(fds), "fd": fds[0].Fd, "events": oracleSymbol(int(fds[0].Events), "POLLIN", unix.POLLIN), "timeout_ms": timeout})
				fds[0].Revents = unix.POLLIN
				return 1, nil
			},
			read: func(fd int, buffer []byte) (int, error) {
				calls.add("read", map[string]any{"fd": fd, "buffer_length": len(buffer)})
				copy(buffer, stimulus)
				return len(stimulus), nil
			},
			close: func(fd int) error {
				calls.add("close", map[string]any{"fd": fd})
				return nil
			},
		}
		receive := func(label string) (growattProjectReceiver, map[string]any, growattProjectRecord) {
			receiver, err := openGrowattProjectSocketWith("can0", ops)
			if err != nil {
				t.Fatal(label, err)
			}
			record, err := receiver.Receive(context.Background())
			if err != nil {
				t.Fatal(label, err)
			}
			identity := receiver.Identity()
			return receiver, map[string]any{
				"open":             label,
				"identity":         map[string]any{"name": identity.Name(), "index": identity.Index()},
				"record_interface": map[string]any{"name": record.Interface.Name(), "index": record.Interface.Index()},
				"sequence":         record.Sequence,
				"monotonic_ns":     record.Monotonic.Nanoseconds(),
				"raw_hex":          hex.EncodeToString(record.Raw),
			}, record
		}
		first, firstReceipt, a := receive("first")
		firstClose := first.Close()
		second, secondReceipt, b := receive("second")
		snapshot := growattProjectNow()
		secondClose := second.Close()
		sameOrigin := len(oracleProjectOrigins) == len(readings)
		for _, origin := range oracleProjectOrigins {
			sameOrigin = sameOrigin && origin.Equal(growattProjectClockOrigin)
		}
		oracleCanWrite(t, "linux-project-reopen-clock", "linux", "growatt-project-socketcan-opener-linux",
			"TestCX18ReopenKeepsOneClock: two opens of the same configured receiver, a receipt on each, a close between them and a snapshot of the shared clock after the second receipt",
			map[string]any{
				"configured_name": "can0",
				"lookup":          map[string]any{"index": 7},
				"socket_fd":       9,
				"read_length":     len(stimulus),
				"read_bytes_hex":  []any{hex.EncodeToString(stimulus), hex.EncodeToString(stimulus)},
				"clock": map[string]any{
					"origin":      "growattProjectClockOrigin, one package variable shared by every receiver and by the snapshot",
					"readings_ns": []any{readings[0].Nanoseconds(), readings[1].Nanoseconds(), readings[2].Nanoseconds()},
					"order":       []any{"first receipt", "second receipt", "snapshot"},
				},
			}, calls.list, map[string]any{
				"receipts":                          []any{firstReceipt, secondReceipt},
				"snapshot_ns":                       snapshot.Nanoseconds(),
				"interval_first_to_second_ns":       (b.Monotonic - a.Monotonic).Nanoseconds(),
				"interval_second_to_snapshot_ns":    (snapshot - b.Monotonic).Nanoseconds(),
				"clock_readings_taken":              len(oracleProjectOrigins),
				"every_reading_from_the_one_origin": sameOrigin,
				"clock_restarted":                   b.Monotonic <= a.Monotonic,
				"snapshot_behind_receipt":           snapshot < b.Monotonic,
				"close_errors":                      []any{oracleCanError(firstClose), oracleCanError(secondClose)},
			})
	})
}
