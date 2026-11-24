package canbusreg

import (
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func oracleJSON(value any) any {
	encoded, err := json.Marshal(value)
	if err != nil {
		return map[string]string{"marshal_error": err.Error()}
	}
	var decoded any
	_ = json.Unmarshal(encoded, &decoded)
	return decoded
}

// TestOracleSS02GrowattV104 runs the pinned registry classifier on the 311, 312 and 313 frames.
func TestOracleSS02GrowattV104(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	limits := []byte{0x02, 0x38, 0x00, 0xfa, 0x01, 0xf4, 0x00, 0x43}
	status := func(count, cells byte) []byte { return []byte{0x00, 0x80, 0x00, 0x00, count, 0xaa, 0xbb, cells} }
	measures := func(soc byte) []byte { return []byte{0x14, 0x00, 0xff, 0xf6, 0x01, 0x2c, soc, 0xff} }
	type frame struct {
		id   uint32
		data []byte
		ext  bool
	}
	cases := []struct {
		id, note string
		frames   []frame
	}{
		{"tuple-card", "complete 311/312/313 tuple", []frame{{0x311, limits, false}, {0x312, status(2, 16), false}, {0x313, measures(0x50), false}}},
		{"312-count4-eq-1-byte7-eq-255", "312 with count byte 4 equal to 1 and byte 7 equal to 255", []frame{{0x311, limits, false}, {0x312, status(1, 255), false}, {0x313, measures(0x50), false}}},
		{"312-count-0", "boundary: count byte 4 equal to 0", []frame{{0x311, limits, false}, {0x312, status(0, 16), false}, {0x313, measures(0x50), false}}},
		{"312-count-254-cells-254", "boundary: count 254 and cell count 254", []frame{{0x311, limits, false}, {0x312, status(254, 254), false}, {0x313, measures(0x50), false}}},
		{"312-count-255-cells-16", "boundary: count byte 4 equal to 255", []frame{{0x311, limits, false}, {0x312, status(255, 16), false}, {0x313, measures(0x50), false}}},
		{"312-cells-0", "boundary: cell count byte 7 equal to 0", []frame{{0x311, limits, false}, {0x312, status(2, 0), false}, {0x313, measures(0x50), false}}},
		{"313-soc-100", "boundary: SOC 100", []frame{{0x311, limits, false}, {0x312, status(2, 16), false}, {0x313, measures(100), false}}},
		{"313-soc-101", "boundary: SOC 101 is above the listed range", []frame{{0x311, limits, false}, {0x312, status(2, 16), false}, {0x313, measures(101), false}}},
		{"313-soc-sentinel-ff", "sentinel: SOC 0xff", []frame{{0x311, limits, false}, {0x312, status(2, 16), false}, {0x313, measures(0xff), false}}},
		{"311-short-7-bytes", "short frame: 311 with seven payload bytes", []frame{{0x311, limits[:7], false}, {0x312, status(2, 16), false}, {0x313, measures(0x50), false}}},
		{"neighbour-314", "neighbouring identifier 0x314 between complete tuples", []frame{{0x311, limits, false}, {0x312, status(2, 16), false}, {0x314, []byte{1, 2, 3, 4, 5, 6, 7, 8}, false}, {0x313, measures(0x50), false}}},
		{"neighbour-310", "neighbouring identifier 0x310 (not listed)", []frame{{0x311, limits, false}, {0x312, status(2, 16), false}, {0x310, []byte{1, 2, 3, 4, 5, 6, 7, 8}, false}, {0x313, measures(0x50), false}}},
		{"312-extended-identifier", "extended identifier with the 312 value", []frame{{0x311, limits, false}, {0x312, status(2, 16), true}, {0x313, measures(0x50), false}}},
	}
	var out []any
	for _, test := range cases {
		profile := GrowattLowVoltageBMSV104()
		identity := growattInterface(t, "can7", 7)
		var steps []any
		var last Classification
		for index, f := range test.frames {
			var evidence Evidence
			if f.ext {
				evidence = growattExtendedEvidence(t, identity, uint64(index+1), f.id, f.data)
			} else {
				evidence = growattEvidence(t, identity, uint64(index+1), f.id, f.data)
			}
			last = profile.Classify(evidence)
			steps = append(steps, map[string]any{
				"frame":    map[string]any{"identifier": f.id, "extended": f.ext, "data_hex": hex.EncodeToString(f.data)},
				"listed":   growattV104ListedFrame(evidence.Frame),
				"valid":    growattV104Valid(evidence.Frame),
				"geometry": growattV104Geometry(evidence.Frame),
				"profile":  string(last.Profile),
			})
		}
		out = append(out, map[string]any{"case": test.id, "note": test.note, "steps": steps, "result": map[string]any{"profile": string(last.Profile), "projection": oracleJSON(last.Projection)}})
	}
	for _, entry := range out {
		record := entry.(map[string]any)
		record["path"] = "canbusreg GrowattLowVoltageBMSV104 Classify and growattV104Valid"
		encoded, err := json.MarshalIndent(record, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(directory, "growatt-bms-can-"+record["case"].(string)+".canbusreg.native.json"), append(encoded, '\n'), 0o644); err != nil {
			t.Fatal(err)
		}
	}
}
