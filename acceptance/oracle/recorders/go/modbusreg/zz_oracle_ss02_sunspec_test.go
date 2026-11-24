package sunspec

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func oracleSunSpecDecision(decision CapabilityDecision) map[string]any {
	facts := []any{}
	for _, fact := range decision.Facts() {
		value := fact.Value()
		entry := map[string]any{"field_id": fact.FieldID(), "unit": fact.Unit(), "kind": string(value.Kind())}
		if number, isNumber := value.Number(); isNumber {
			entry["number"] = number
		}
		if enumNumber, symbol, isEnum := value.Enum(); isEnum {
			entry["enum_number"] = enumNumber
			entry["enum_symbol"] = symbol
		}
		if bits, symbols, isBitfield := value.Bitfield(); isBitfield {
			if symbols == nil {
				symbols = []string{}
			}
			entry["bits"] = bits
			entry["bit_symbols"] = symbols
		}
		facts = append(facts, entry)
	}
	return map[string]any{"admitted": decision.Admitted(), "reason": string(decision.Reason()), "profile": decision.ProfileID(), "facts": facts}
}

// TestOracleSS02SunSpec records the native decoder and the monitoring capability on the Model 103 W and W_SF operands.
func TestOracleSS02SunSpec(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	registry := mustStandardSunSpecRegistry(t)
	type operand struct {
		id, note string
		w, sf    uint16
	}
	operands := []operand{
		{"sunspec-103-w-1500-sf0", "W 1500 with SF 0", 1500, 0},
		{"sunspec-103-w-1234-sf-minus1", "W 1234 with SF -1", 1234, 0xFFFF},
		{"sunspec-103-w-minus50-sf1", "W -50 with SF 1", 0xFFCE, 1},
		{"sunspec-103-w-sentinel-8000", "raw W 0x8000", 0x8000, 0},
		{"sunspec-103-sf-plus11", "scale-factor word +11", 1500, 11},
		{"sunspec-103-sf-minus11", "scale-factor word -11", 1500, 0xFFF5},
	}
	write := func(name string, document map[string]any) {
		encoded, err := json.MarshalIndent(document, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(directory, name+".native.json"), append(encoded, '\n'), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	for _, test := range operands {
		snapshot := capabilitySnapshot(t, registry, 103, map[string][]uint16{"W": {test.w}, "W_SF": {test.sf}})
		write(test.id, map[string]any{
			"case": test.id, "note": test.note, "path": "modbusreg sunspec EvaluateThreePhaseMonitoring on a Common model followed by Model 103 (length 50)",
			"input": map[string]any{"common": map[string]string{"manufacturer": "Maker", "model": "Model", "firmware": "1.0"}, "model": 103, "length": 50, "W_word_14": test.w, "W_SF_word_15": test.sf, "other_points": "pinned integer inverter fixture"},
			"output": oracleSunSpecDecision(registry.EvaluateThreePhaseMonitoring(snapshot)),
		})
	}
	only101 := snapshotFromOccurrences(commonOccurrence(t, registry, "Maker", "Model", "1.0", 1), inverterOccurrence(t, registry, 101, nil, 2))
	write("sunspec-common-then-101", map[string]any{"case": "sunspec-common-then-101", "note": "a valid common model followed only by Model 101", "path": "modbusreg sunspec EvaluateThreePhaseMonitoring",
		"input": map[string]any{"models": []int{1, 101}}, "output": oracleSunSpecDecision(registry.EvaluateThreePhaseMonitoring(only101))})
	short := snapshotFromOccurrences(commonOccurrence(t, registry, "Maker", "Model", "1.0", 1), admittedOccurrence(103, 30, make([]uint16, 32), 2))
	write("sunspec-103-short-inconsistent-length", map[string]any{"case": "sunspec-103-short-inconsistent-length", "note": "a Model 103 occurrence declaring length 30 instead of 50", "path": "modbusreg sunspec EvaluateThreePhaseMonitoring",
		"input": map[string]any{"models": []int{1, 103}, "model_103_length": 30}, "output": oracleSunSpecDecision(registry.EvaluateThreePhaseMonitoring(short))})
}
