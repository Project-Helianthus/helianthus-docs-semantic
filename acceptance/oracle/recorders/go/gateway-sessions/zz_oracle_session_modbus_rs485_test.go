//go:build oracle_rtu_overlay

package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"testing"
	"time"

	ebusgateway "github.com/Project-Helianthus/helianthus-ebusgateway"
	"github.com/Project-Helianthus/helianthus-ebusgateway/mcp"
	modbus "github.com/Project-Helianthus/helianthus-modbus"
)

type oracleRTUExchange struct {
	Name        string `json:"name"`
	RequestHex  string `json:"request_hex"`
	ResponseHex string `json:"response_hex"`
}

type oracleRS485Step struct {
	Name           string `json:"name"`
	Kind           string `json:"kind"`
	PatchResponses []struct {
		Exchange    int    `json:"exchange"`
		ResponseHex string `json:"response_hex"`
	} `json:"patch_responses"`
	CurrentAtOffsetMS int64 `json:"current_at_offset_ms"`
}

type oracleRS485Input struct {
	Config      ebusgateway.GrowattBMSRS485Config `json:"config"`
	ReceiptWall struct {
		AnchorUnix int64 `json:"anchor_unix"`
		StepNS     int64 `json:"step_ns"`
	} `json:"receipt_wall"`
	ByteOffsetUS int64               `json:"byte_offset_us"`
	TailOffsetUS int64               `json:"tail_offset_us"`
	Exchanges    []oracleRTUExchange `json:"exchanges"`
	Steps        []oracleRS485Step   `json:"steps"`
}

// oracleRTUStream is the scripted RTUByteStream that stands in for the physical serial operand of the production endpoint. It
// matches every written request frame against the next scripted exchange and answers with the exact frozen response frame; it
// creates no receipt of its own.
type oracleRTUStream struct {
	mu       sync.Mutex
	script   []oracleRTUExchange
	next     int
	pending  []byte
	offset   time.Duration
	byteStep time.Duration
	tailStep time.Duration
	writes   []map[string]any
	opened   []map[string]any
}

func (s *oracleRTUStream) WriteRTU(_ context.Context, frame []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	record := map[string]any{"index": len(s.writes), "request_adu_hex": hex.EncodeToString(frame)}
	if s.next >= len(s.script) {
		record["matched"] = false
		s.writes = append(s.writes, record)
		return 0, fmt.Errorf("scripted stream: no exchange is scripted for request %x", frame)
	}
	exchange := s.script[s.next]
	s.next++
	record["scripted_exchange"] = exchange.Name
	if hex.EncodeToString(frame) != exchange.RequestHex {
		record["matched"] = false
		s.writes = append(s.writes, record)
		return 0, fmt.Errorf("scripted stream: request %x does not match the scripted request of %s", frame, exchange.Name)
	}
	record["matched"] = true
	s.writes = append(s.writes, record)
	response, err := hex.DecodeString(exchange.ResponseHex)
	if err != nil {
		return 0, err
	}
	s.pending = response
	return len(frame), nil
}

func (s *oracleRTUStream) ReadRTUByte(ctx context.Context) (byte, time.Duration, error) {
	s.mu.Lock()
	if len(s.pending) > 0 {
		value := s.pending[0]
		s.pending = s.pending[1:]
		s.offset += s.byteStep
		offset := s.offset
		s.mu.Unlock()
		return value, offset, nil
	}
	s.mu.Unlock()
	<-ctx.Done()
	s.mu.Lock()
	defer s.mu.Unlock()
	s.offset += s.tailStep
	return 0, s.offset, ctx.Err()
}

func (s *oracleRTUStream) Close() error { return nil }

func (s *oracleRTUStream) RTUOffset() time.Duration {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.offset
}

// TestOracleSessionModbusRS485 runs the pinned Growatt RS-485 storage runtime through its production RTU endpoint.
func TestOracleSessionModbusRS485(t *testing.T) {
	session := oracleLoadSession(t)
	var input oracleRS485Input
	if err := json.Unmarshal(session.Input, &input); err != nil {
		t.Fatal(err)
	}
	classes := oracleNormalize()
	stream := &oracleRTUStream{script: append([]oracleRTUExchange(nil), input.Exchanges...), byteStep: time.Duration(input.ByteOffsetUS) * time.Microsecond, tailStep: time.Duration(input.TailOffsetUS) * time.Microsecond}
	var receiptCalls int64
	modbus.OracleRTUStream = func(config modbus.RTUSerialConfig) (modbus.OracleRTUStreamCloser, error) {
		stream.opened = append(stream.opened, map[string]any{"baud": config.Baud, "data_bits": config.DataBits, "parity": fmt.Sprint(config.Parity), "stop_bits": config.StopBits})
		return stream, nil
	}
	modbus.OracleReceiptWall = func() time.Time {
		wall := time.Unix(input.ReceiptWall.AnchorUnix, receiptCalls*input.ReceiptWall.StepNS).UTC()
		receiptCalls++
		return wall
	}
	t.Cleanup(func() { modbus.OracleRTUStream, modbus.OracleReceiptWall = nil, nil })

	hub := newTestSemanticHub(t)
	runtime, err := startGrowattBMSRS485Runtime(input.Config, hub)
	if err != nil {
		t.Fatal(err)
	}
	classes.Outcomes = append(classes.Outcomes, map[string]any{"step": "runtime-start", "source_epoch": input.Config.SourceEpoch, "configured_driver_generation": input.Config.DriverGeneration, "unit": input.Config.UnitID, "serial_open": oracleJSON(stream.opened)})
	asset := input.Config.AssetID
	anchor := time.Unix(input.ReceiptWall.AnchorUnix, 0).UTC()
	ctx := context.Background()
	written := 0
	collect := func(step string) {
		stream.mu.Lock()
		writes := append([]map[string]any(nil), stream.writes[written:]...)
		written = len(stream.writes)
		stream.mu.Unlock()
		for _, write := range writes {
			write["step"] = step
			classes.Sends = append(classes.Sends, write)
		}
		if evidence, ok := runtime.LastObservationEvidence(); ok {
			classes.Acquisitions = append(classes.Acquisitions, map[string]any{"step": step, "observation_evidence": oracleJSON(evidence)})
		}
	}
	for _, step := range input.Steps {
		stream.mu.Lock()
		for _, patch := range step.PatchResponses {
			stream.script[patch.Exchange].ResponseHex = patch.ResponseHex
		}
		stream.mu.Unlock()
		switch step.Kind {
		case "publish":
			value, err := runtime.GrowattStorageSemanticCurrent(ctx)
			record := map[string]any{"step": step.Name}
			if err != nil {
				record["error"] = err.Error()
				classes.Outcomes = append(classes.Outcomes, record)
				collect(step.Name)
				continue
			}
			public := characterizationJSON(t, value)
			canonical, snapshot := characterizationCanonical(t, public)
			sum := sha256.Sum256(canonical)
			classes.Publications = append(classes.Publications, map[string]any{"step": step.Name, "view": oracleJSON(value), "canonical_sha256": hex.EncodeToString(sum[:]), "identity": string(characterizationIdentity(t, snapshot))})
			classes.Outcomes = append(classes.Outcomes, map[string]any{"step": step.Name, "published": true})
			collect(step.Name)
		case "retained-current":
			retained, ok := runtime.storage.Current(asset)
			var decoded any
			if ok {
				_ = json.Unmarshal(retained, &decoded)
			}
			classes.PublicOutputs = append(classes.PublicOutputs, map[string]any{"step": step.Name, "read": "storage.Current", "available": ok, "view": decoded})
		case "current-at":
			at, ok := runtime.storage.CurrentAt(asset, anchor.Add(time.Duration(step.CurrentAtOffsetMS)*time.Millisecond))
			classes.PublicOutputs = append(classes.PublicOutputs, map[string]any{"step": step.Name, "read": "storage.CurrentAt", "available": ok, "view": oracleJSON(at)})
		case "mcp-call":
			server, err := mcp.NewServer(emptyMCPRegistry{}, nil)
			if err != nil {
				t.Fatal(err)
			}
			mcp.RegisterModbusV1Tools(server, newGatewayModbusMCPProviderWithGrowatt(nil, runtime))
			status, body := oracleMCPCall(server.Handler(), mcp.SemanticV1GrowattStorageCurrentGetTool)
			classes.PublicOutputs = append(classes.PublicOutputs, map[string]any{"step": step.Name, "read": "mcp tools/call " + mcp.SemanticV1GrowattStorageCurrentGetTool, "status": status, "body": body})
			collect(step.Name)
		default:
			t.Fatalf("unknown step kind %q", step.Kind)
		}
	}
	stream.mu.Lock()
	unused := len(stream.script) - stream.next
	stream.mu.Unlock()
	classes.Outcomes = append(classes.Outcomes, map[string]any{"step": "end", "unconsumed_scripted_exchanges": unused, "request_frames_written": len(stream.writes)})
	oracleWriteClasses(t, classes)
}
