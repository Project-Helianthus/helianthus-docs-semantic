package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// oracleWrite stores one recorded document; the test is inert unless the recorder names an output directory.
func oracleWrite(t *testing.T, name string, document any) {
	t.Helper()
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	encoded, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, name), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}

func oracleJSON(value any) any {
	encoded, err := json.Marshal(value)
	if err != nil {
		return map[string]string{"marshal_error": err.Error()}
	}
	var decoded any
	_ = json.Unmarshal(encoded, &decoded)
	return decoded
}

// TestOracleSS02VaillantDHW runs the pinned detached DHW mappers on the cases of the SS02 vector set.
func TestOracleSS02VaillantDHW(t *testing.T) {
	type setpointCase struct {
		ID      string
		Note    string
		Mutate  func(*thermalDhwObservation, *thermalDhwBinding)
		Celsius int
	}
	setpoint := []setpointCase{
		{"0004-value-50", "native 50 C requested target on the matching B5/24 tuple, controller direction and presentation", func(*thermalDhwObservation, *thermalDhwBinding) {}, 50},
		{"0004-boundary-35", "lower qualified native bound", func(*thermalDhwObservation, *thermalDhwBinding) {}, 35},
		{"0004-boundary-70", "upper qualified native bound", func(*thermalDhwObservation, *thermalDhwBinding) {}, 70},
		{"0004-below-bound-34", "one degree below the qualified native domain", func(*thermalDhwObservation, *thermalDhwBinding) {}, 34},
		{"0004-above-bound-71", "one degree above the qualified native domain", func(*thermalDhwObservation, *thermalDhwBinding) {}, 71},
		{"0004-neighbouring-register-0005", "same tuple with the neighbouring register 0005 (measured temperature) as selector", func(o *thermalDhwObservation, b *thermalDhwBinding) {
			o.Identity.Selector.Register, b.Identity.Selector.Register = 5, 5
		}, 50},
		{"0004-neighbouring-sb-23", "version miss: the secondary byte differs", func(o *thermalDhwObservation, b *thermalDhwBinding) {
			o.Identity.Selector.SB, b.Identity.Selector.SB = 0x23, 0x23
		}, 50},
		{"0004-neighbouring-group-02", "neighbouring group", func(o *thermalDhwObservation, b *thermalDhwBinding) {
			o.Identity.Selector.Group, b.Identity.Selector.Group = 2, 2
		}, 50},
		{"0004-short-empty-raw-reply", "short frame: no raw reply bytes", func(o *thermalDhwObservation, _ *thermalDhwBinding) { o.RawReply = nil }, 50},
		{"0004-sentinel-no-value", "sentinel: the decoded value is absent", func(o *thermalDhwObservation, _ *thermalDhwBinding) { o.Value = nil }, 50},
		{"0004-mirror-presentation", "controller mirror presentation", func(o *thermalDhwObservation, _ *thermalDhwBinding) { o.Presentation = "controller_mirror" }, 50},
		{"0004-boiler-direct-presentation", "boiler direct presentation is native context only", func(o *thermalDhwObservation, _ *thermalDhwBinding) { o.Presentation = "boiler_direct" }, 50},
	}
	var cases []any
	for _, test := range setpoint {
		observation, binding, evaluation := thermalDhwTestFixture("synthetic", test.Celsius)
		test.Mutate(&observation, &binding)
		cases = append(cases, map[string]any{
			"case": test.ID, "note": test.Note,
			"input": map[string]any{"observations": oracleJSON([]thermalDhwObservation{observation}), "bindings": oracleJSON([]thermalDhwBinding{binding}), "evaluation": oracleJSON(evaluation)},
			"output": oracleJSON(mapThermalDhwSetpoints([]thermalDhwObservation{observation}, []thermalDhwBinding{binding}, evaluation)),
		})
	}
	for _, entry := range cases {
		record := entry.(map[string]any)
		record["mapper"], record["selector"] = "mapThermalDhwSetpoints", "B5/24 opcode 02 group 01 instance 00 register 0004"
		oracleWrite(t, "vaillant-dhw-"+record["case"].(string)+".native.json", record)
	}

	type measuredCase struct {
		ID, Note string
		Mutate   func(*dhwMeasuredRequest)
	}
	measured := []measuredCase{
		{"0005-measured-temperature", "native measured temperature 45 C (f32 little endian 0x42340000) with qualified presence", func(*dhwMeasuredRequest) {}},
		{"0005-neighbouring-register-0004", "neighbouring register 0004 as the measurement identity", func(r *dhwMeasuredRequest) { r.Identity.Selector.Register = 4 }},
		{"0005-short-measurement-reply", "short frame: the measurement value is two bytes", func(r *dhwMeasuredRequest) {
			r.Measurement.Attempt.Value = []byte{0, 0}
		}},
		{"0005-presence-zero", "presence value zero", func(r *dhwMeasuredRequest) { r.Presence.Attempt.Value = []byte{0, 0} }},
		{"0005-sentinel-nan", "sentinel: float32 not-a-number", func(r *dhwMeasuredRequest) { r.Measurement.Attempt.Value = []byte{0, 0, 0xc0, 0x7f} }},
		{"0005-version-miss-sb-23", "version miss: the secondary byte differs", func(r *dhwMeasuredRequest) { r.Identity.Selector.SB = 0x23 }},
	}
	var measuredCases []any
	for _, test := range measured {
		request := i32Input()
		test.Mutate(&request)
		measuredCases = append(measuredCases, map[string]any{"case": test.ID, "note": test.Note, "input": oracleJSON(request), "output": oracleJSON(mapDHWMeasuredTemperature(request))})
	}
	for _, entry := range measuredCases {
		record := entry.(map[string]any)
		record["mapper"], record["selector"] = "mapDHWMeasuredTemperature", "B5/24 opcode 02 group 01 instance 00 register 0005"
		oracleWrite(t, "vaillant-dhw-"+record["case"].(string)+".native.json", record)
	}
}
