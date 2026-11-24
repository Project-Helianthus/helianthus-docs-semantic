package main

import (
	"context"
	"encoding/hex"
	"testing"
	"time"
)

type oracleCANFrame struct {
	ID       uint32
	Length   byte
	Len8DLC  byte
	Data     []byte
	Extended bool
}

func oracleCANRecord(frame oracleCANFrame) growattBMSCANRecord {
	identifier := frame.ID
	if frame.Extended {
		identifier |= growattBMSCANExtendedFlag
	}
	return growattBMSCANRecord{Interface: growattBMSCANTestInterface, Raw: growattBMSCANTestRecord(identifier, frame.Length, frame.Len8DLC, frame.Data...)}
}

func oracleCANFrameJSON(frame oracleCANFrame) map[string]any {
	return map[string]any{"identifier": frame.ID, "extended": frame.Extended, "payload_length": frame.Length, "len8_dlc": frame.Len8DLC, "data_hex": hex.EncodeToString(frame.Data)}
}

func oracleStd(id uint32, data ...byte) oracleCANFrame {
	return oracleCANFrame{ID: id, Length: byte(len(data)), Data: data}
}

// TestOracleSS02GrowattCAN runs the pinned gateway receive path on the 311, 312 and 313 frames.
func TestOracleSS02GrowattCAN(t *testing.T) {
	limits := oracleStd(0x311, 0x02, 0x38, 0x00, 0xfa, 0x01, 0xf4, 0x00, 0x43)
	status := func(count, cells byte) oracleCANFrame {
		return oracleStd(0x312, 0x00, 0x80, 0x00, 0x00, count, 0xaa, 0xbb, cells)
	}
	measures := func(soc byte) oracleCANFrame { return oracleStd(0x313, 0x14, 0x00, 0xff, 0xf6, 0x01, 0x2c, soc, 0xff) }
	cases := []struct {
		ID, Note string
		Frames   []oracleCANFrame
	}{
		{"tuple-card", "complete 311/312/313 tuple; 313 current bytes 0xfff6 is -10 deciamperes", []oracleCANFrame{limits, status(2, 16), measures(0x50)}},
		{"312-count4-eq-1-byte7-eq-255", "312 with count byte 4 equal to 1 and byte 7 equal to 255", []oracleCANFrame{limits, status(1, 255), measures(0x50)}},
		{"312-count-0", "boundary: count byte 4 equal to 0", []oracleCANFrame{limits, status(0, 16), measures(0x50)}},
		{"312-count-254-cells-254", "boundary: count 254 and cell count 254", []oracleCANFrame{limits, status(254, 254), measures(0x50)}},
		{"312-count-255-cells-16", "boundary: count byte 4 equal to 255", []oracleCANFrame{limits, status(255, 16), measures(0x50)}},
		{"312-cells-0", "boundary: cell count byte 7 equal to 0", []oracleCANFrame{limits, status(2, 0), measures(0x50)}},
		{"313-soc-100", "boundary: SOC 100", []oracleCANFrame{limits, status(2, 16), measures(100)}},
		{"313-soc-101", "boundary: SOC 101 is above the listed range", []oracleCANFrame{limits, status(2, 16), measures(101)}},
		{"313-soc-sentinel-ff", "sentinel: SOC 0xff", []oracleCANFrame{limits, status(2, 16), measures(0xff)}},
		{"311-short-7-bytes", "short frame: 311 with seven payload bytes", []oracleCANFrame{oracleStd(0x311, 0x02, 0x38, 0x00, 0xfa, 0x01, 0xf4, 0x00), status(2, 16), measures(0x50)}},
		{"neighbour-314", "neighbouring identifier 0x314 between complete tuples", []oracleCANFrame{limits, status(2, 16), oracleStd(0x314, 1, 2, 3, 4, 5, 6, 7, 8), measures(0x50)}},
		{"neighbour-310", "neighbouring identifier 0x310 (not listed)", []oracleCANFrame{limits, status(2, 16), oracleStd(0x310, 1, 2, 3, 4, 5, 6, 7, 8), measures(0x50)}},
		{"312-extended-identifier", "extended identifier with the 312 value", []oracleCANFrame{limits, {ID: 0x312, Length: 8, Extended: true, Data: []byte{0, 0x80, 0, 0, 2, 0xaa, 0xbb, 16}}, measures(0x50)}},
	}
	var out []any
	for _, test := range cases {
		clock := &growattBMSCANTestClock{}
		driver := newGrowattBMSCANTestDriver(clock)
		var steps []any
		for index, frame := range test.Frames {
			clock.Set(time.Duration(index+1) * time.Millisecond)
			observation, decodeErr := decodeGrowattBMSCANRecord(oracleCANRecord(frame).Raw)
			step := map[string]any{"frame": oracleCANFrameJSON(frame)}
			if decodeErr != nil {
				step["decode_error"] = decodeErr.Error()
			} else {
				step["listed"] = growattBMSCANListed(observation.Identifier)
				step["valid"] = growattBMSCANValid(observation)
				step["dlc"], step["raw_dlc"] = observation.DLC, observation.RawDLC
			}
			step["observe_continues"] = driver.observe(oracleCANRecord(frame))
			steps = append(steps, step)
		}
		snapshot, err := driver.GrowattBMSV104Snapshot(context.Background())
		result := map[string]any{"diagnostics": oracleJSON(driver.Diagnostics())}
		if err != nil {
			result["snapshot_error"] = err.Error()
		} else {
			result["snapshot"] = oracleJSON(snapshot)
		}
		out = append(out, map[string]any{"case": test.ID, "note": test.Note, "steps": steps, "result": result})
	}
	for _, entry := range out {
		record := entry.(map[string]any)
		record["path"] = "gateway receive path: decodeGrowattBMSCANRecord, growattBMSCANValid, observe, GrowattBMSV104Snapshot"
		oracleWrite(t, "growatt-bms-can-"+record["case"].(string)+".gateway.native.json", record)
	}
}
