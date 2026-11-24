package dest

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"testing"
)

func TestVoltage(t *testing.T) { report(t, false) }
func TestCurrent(t *testing.T) { report(t, true) }
func TestEcho(t *testing.T)    { report(t, false) }
func TestHistory(t *testing.T) { report(t, false) }
func TestBinding(t *testing.T) { report(t, false) }
func TestPCS(t *testing.T)     { report(t, false) }
func TestCmd211(t *testing.T)  { report(t, false) }
func TestCmd212(t *testing.T)  { report(t, false) }
func TestB503(t *testing.T)    { report(t, false) }
func TestBB02(t *testing.T)    { report(t, false) }

func fileText(name string) (string, bool) {
	text, err := os.ReadFile(name)
	if err != nil {
		return "", false
	}
	return strings.TrimSpace(string(text)), true
}

func report(t *testing.T, second bool) {
	t.Helper()
	caseID := os.Getenv("MANIFEST_CASE")
	if dropped, ok := fileText("drop-case"); ok && dropped == caseID {
		return
	}
	raw := os.Getenv("MANIFEST_RAW")
	if stuck, ok := fileText("stick-raw"); ok && caseID == "wrong-target" {
		raw = stuck
	}
	origin := os.Getenv("MANIFEST_ORIGIN")
	if changed, ok := fileText("mutate-origin"); ok {
		origin = changed
	}
	quality := os.Getenv("MANIFEST_QUALITY")
	if changed, ok := fileText("mutate-quality"); ok {
		quality = changed
	}
	provenance := os.Getenv("MANIFEST_PROVENANCE")
	if changed, ok := fileText("mutate-provenance"); ok {
		provenance = changed
	}
	fmt.Printf("MANIFEST_RESULT case=%s row=%s assertion=%s\n", caseID, os.Getenv("MANIFEST_ROW"), os.Getenv("MANIFEST_ASSERTION"))
	fmt.Printf(
		"MANIFEST_INPUT raw=%s qualifiers=%s clock=%s state=%s\n",
		raw, os.Getenv("MANIFEST_QUALIFIERS"), os.Getenv("MANIFEST_CLOCK"), os.Getenv("MANIFEST_STATE"),
	)
	fmt.Printf(
		"MANIFEST_META origin=%s quality=%s source=%s timing=%s provenance=%s\n",
		origin, quality, os.Getenv("MANIFEST_SOURCE"), os.Getenv("MANIFEST_TIMING"), provenance,
	)
	var pins map[string]string
	if err := json.Unmarshal([]byte(os.Getenv("MANIFEST_PINNED_FIELDS")), &pins); err != nil {
		t.Fatalf("pins %v", err)
	}
	_, skipBinding := fileText("skip-binding")
	approved := map[string]string{}
	if text, err := os.ReadFile("approved-new"); err == nil {
		for _, line := range strings.Split(string(text), "\n") {
			if i := strings.Index(line, "="); i > 0 {
				approved[line[:i]] = strings.TrimSpace(line[i+1:])
			}
		}
	}
	mutated := false
	override, hasOverride := fileText("mutate-observed")
	overrideName, overrideValue := "", ""
	if hasOverride {
		if i := strings.Index(override, "="); i > 0 {
			overrideName = override[:i]
			overrideValue = override[i+1:]
		}
	}
	_, mutateSecond := fileText("mutate-second")
	for name, value := range pins {
		if strings.HasPrefix(name, "template.") {
			continue
		}
		if skipBinding && strings.HasPrefix(name, "binding.") {
			continue
		}
		if replacement, ok := approved[name]; ok {
			fmt.Printf("MANIFEST_FIELD field=%s expected=absent observed=%s\n", name, replacement)
			continue
		}
		observed := value
		if second && mutateSecond && name == "reading" {
			observed = "other"
			mutated = true
		}
		if name == overrideName && overrideValue != value {
			observed = overrideValue
			mutated = true
		}
		fmt.Printf("MANIFEST_FIELD field=%s expected=%s observed=%s\n", name, value, observed)
	}
	if text, err := os.ReadFile("extra-field"); err == nil {
		parts := strings.Fields(string(text))
		if len(parts) == 3 {
			fmt.Printf("MANIFEST_FIELD field=%s expected=%s observed=%s\n", parts[0], parts[1], parts[2])
			if parts[1] != parts[2] {
				mutated = true
			}
		}
	}
	if failedName, ok := fileText("fail-assertion"); ok && failedName == os.Getenv("MANIFEST_ASSERTION") {
		t.Errorf("assertion=%s failed", failedName)
	}
	if mutated || origin != os.Getenv("MANIFEST_ORIGIN") || quality != os.Getenv("MANIFEST_QUALITY") || provenance != os.Getenv("MANIFEST_PROVENANCE") {
		t.Errorf("mutated output")
	}
}
