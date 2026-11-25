package modbusadapter

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"io"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"

	pv "github.com/Project-Helianthus/helianthus-ebusreg/pv"
	modbus "github.com/Project-Helianthus/helianthus-modbus"
)

const oraclePVEndpoint = "127.0.0.1:20502"

// oraclePVServe serves the pin's qualified inverter words on the fixed loopback endpoint of the recorded identities.
func oraclePVServe(t *testing.T, words []uint16) {
	t.Helper()
	listener, err := net.Listen("tcp4", oraclePVEndpoint)
	if err != nil {
		t.Fatalf("Listen: %v", err)
	}
	t.Cleanup(func() { _ = listener.Close() })
	go func() {
		connection, err := listener.Accept()
		if err != nil {
			return
		}
		defer func() { _ = connection.Close() }()
		for {
			header := make([]byte, 7)
			if _, err := io.ReadFull(connection, header); err != nil {
				return
			}
			length := int(binary.BigEndian.Uint16(header[4:6]))
			body := make([]byte, length-1)
			if _, err := io.ReadFull(connection, body); err != nil || len(body) != 5 {
				return
			}
			request := sunSpecReadRequest{
				UnitID: header[6], Function: modbus.FunctionCode(body[0]),
				Offset: binary.BigEndian.Uint16(body[1:3]), WordCount: binary.BigEndian.Uint16(body[3:5]),
			}
			start := int(request.Offset) - 40000
			end := start + int(request.WordCount)
			if start < 0 || end > len(words) {
				return
			}
			response := make([]byte, 9+2*int(request.WordCount))
			copy(response[:2], header[:2])
			binary.BigEndian.PutUint16(response[4:6], uint16(3+2*int(request.WordCount)))
			response[6], response[7], response[8] = request.UnitID, byte(request.Function), byte(2*request.WordCount)
			for index, word := range words[start:end] {
				binary.BigEndian.PutUint16(response[9+2*index:], word)
			}
			if _, err := connection.Write(response); err != nil {
				return
			}
		}
	}()
}

// oraclePVWithoutWords drops the register payloads of the observation: they carry the device identity strings of the Common
// model, which the oracle keeps at the level of the device family. The digest of the whole encoded observation is recorded instead.
func oraclePVWithoutWords(value any) {
	switch typed := value.(type) {
	case map[string]any:
		for _, key := range []string{"raw_words", "words", "wire_response_bytes"} {
			delete(typed, key)
		}
		for _, child := range typed {
			oraclePVWithoutWords(child)
		}
	case []any:
		for _, child := range typed {
			oraclePVWithoutWords(child)
		}
	}
}

type oraclePVCounterReader struct{ next byte }

func (reader *oraclePVCounterReader) Read(buffer []byte) (int, error) {
	for index := range buffer {
		reader.next++
		buffer[index] = reader.next
	}
	return len(buffer), nil
}

// TestOraclePrePortCanonicalPVMapper records canonical_pv.go and canonical_pv_semreg_shadow.go on the qualified inverter observation
// of the pin's mapper test. The mapper and the shadow run on a fixed evaluation instant, a fixed production time and a fixed entropy
// stream; the adapter's clocks are the host's and are not used.
func TestOraclePrePortCanonicalPVMapper(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	oraclePVServe(t, observedFroniusFloatControlsWords())
	adapter, err := Start(context.Background(), integrationConfig(t, "tcp://"+oraclePVEndpoint), realDialer, realFactory)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = adapter.Close() }()
	producer, err := NewSunSpecProducer(adapter, SunSpecProducerConfig{UnitID: 1, AuthorizationScope: "test:canonical-pv", ReadTimeout: time.Second})
	if err != nil {
		t.Fatal(err)
	}
	qualified, err := producer.Qualify(context.Background(), SunSpecPollIdentity{PollGeneration: 71, DeadlineIdentity: 81})
	if err != nil || qualified.Outcome != SunSpecQualificationGO {
		t.Fatalf("qualification=%#v err=%v", qualified, err)
	}
	observation, _, ok := adapter.SunSpecQualificationObservation(qualified.CapabilityID, qualified.SampleID)
	if !ok {
		t.Fatal("qualified observation was not retained")
	}
	encoded, err := json.Marshal(observation)
	if err != nil {
		t.Fatal(err)
	}

	var visible any
	if err := json.Unmarshal(encoded, &visible); err != nil {
		t.Fatal(err)
	}
	oraclePVWithoutWords(visible)
	digest := sha256.Sum256(encoded)

	const evaluated = pv.MonotonicNanos(100)
	producedAt := time.Date(2026, time.August, 17, 15, 0, 0, 0, time.UTC)
	mapper, err := NewCanonicalPVMapper()
	if err != nil {
		t.Fatal(err)
	}
	legacy, err := mapper.Map(observation, encoded, evaluated)
	if err != nil {
		t.Fatal(err)
	}
	withheld := 0
	for _, projection := range legacy.ProjectionReport {
		if projection.Outcome == pv.ProjectionWithheld {
			withheld++
		}
	}

	shadow, err := newCanonicalPVSemRegShadowWithReader(&oraclePVCounterReader{})
	if err != nil {
		t.Fatal(err)
	}
	defer shadow.close()
	record, err := shadow.apply(observation, encoded, legacy, producedAt, evaluated)
	if err != nil {
		t.Fatal(err)
	}
	witness, err := record.detachedSnapshot()
	if err != nil {
		t.Fatal(err)
	}

	document := map[string]any{
		"format":      "helianthus-oracle-pre-port-canonical-pv-mapper/1",
		"description": "the canonical PV v1 snapshot and the SemReg shadow of the qualified inverter observation that the pin's mapper test serves (register payloads left out, its digest kept); evaluation instant, production time and shadow entropy are fixed by the recorder",
		"fixed": map[string]any{
			"evaluated_monotonic_ns": int64(evaluated),
			"produced_at":            producedAt.Format(time.RFC3339),
			"endpoint":               "tcp://" + oraclePVEndpoint,
			"poll_generation":        71,
			"deadline_identity":      81,
		},
		"observation":                visible,
		"observation_encoded_sha256": hex.EncodeToString(digest[:]),
		"accounting":                 map[string]any{"facts": len(legacy.Facts), "requested_outputs": len(legacy.RequestedOutputs), "projection_report": len(legacy.ProjectionReport), "withheld": withheld},
		"legacy":                     legacy,
		"shadow": map[string]any{
			"snapshot":   witness.Snapshot,
			"canonical":  string(bytes.TrimSpace(witness.Canonical)),
			"evaluation": witness.Evaluation,
			"projection": witness.Projection,
		},
	}
	out, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, "canonical-pv-mapper.json"), append(out, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
