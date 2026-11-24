package promotion

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

const replayRoot = "../../testdata/promotion/replay"

var leafInputs = []string{"manifest.json", "pre.json", "post.json"}

var testListPackages = []string{
	"./internal/candidatefacts",
	"./internal/candidatefacts/cmd/rawfirst",
	"./internal/coexistence",
	"./internal/coexistence/cmd/msp08harness",
	"./internal/promotioncapture",
	"./internal/promotioncapture/cmd/leafpromotionartifacts",
	"./internal/promotionlock",
	"./internal/syncevidence",
}

type commandRun struct {
	exitStatus int
	stdout     []byte
	stderr     []byte
}

func TestReplayRawfirst(t *testing.T) {
	root := moduleRoot(t)
	binary := buildCommand(t, root, "./internal/candidatefacts/cmd/rawfirst")
	assertReplay(t, produceRawfirst(t, root, binary))
}

func TestReplayMsp08harness(t *testing.T) {
	root := moduleRoot(t)
	binary := buildCommand(t, root, "./internal/coexistence/cmd/msp08harness")
	assertReplay(t, produceMsp08harness(t, root, binary))
}

func TestReplayLeafpromotionartifacts(t *testing.T) {
	root := moduleRoot(t)
	binary := buildCommand(t, root, "./internal/promotioncapture/cmd/leafpromotionartifacts")
	assertReplay(t, produceLeafpromotionartifacts(t, root, binary))
}

func TestReplayTestList(t *testing.T) {
	root := moduleRoot(t)
	got := listTestNames(t, root)
	want, err := os.ReadFile(filepath.Join(replayRoot, "test-list.txt"))
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, want) {
		t.Fatalf("test list differs from replay/test-list.txt\n got: %q\nwant: %q", got, want)
	}
}

func moduleRoot(t *testing.T) string {
	t.Helper()
	root, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	return root
}

func buildCommand(t *testing.T, root, pkg string) string {
	t.Helper()
	output := filepath.Join(t.TempDir(), filepath.Base(pkg))
	command := exec.Command("go", "build", "-o", output, pkg)
	command.Dir = root
	if combined, err := command.CombinedOutput(); err != nil {
		t.Fatalf("go build %s: %v\n%s", pkg, err, combined)
	}
	return output
}

func listTestNames(t *testing.T, root string) []byte {
	t.Helper()
	args := append([]string{"test", "-list", ".*"}, testListPackages...)
	command := exec.Command("go", args...)
	command.Dir = root
	var stdout, stderr bytes.Buffer
	command.Stdout = &stdout
	command.Stderr = &stderr
	if err := command.Run(); err != nil {
		t.Fatalf("go test -list: %v\n%s", err, stderr.Bytes())
	}
	var names bytes.Buffer
	for _, line := range strings.SplitAfter(stdout.String(), "\n") {
		if line == "" || strings.HasPrefix(line, "ok ") || strings.HasPrefix(line, "? ") {
			continue
		}
		names.WriteString(line)
	}
	return names.Bytes()
}

func runCommand(t *testing.T, root, binary string, args ...string) commandRun {
	t.Helper()
	command := exec.Command(binary, args...)
	command.Dir = root
	var stdout, stderr bytes.Buffer
	command.Stdout = &stdout
	command.Stderr = &stderr
	err := command.Run()
	exitStatus := 0
	if err != nil {
		var exitError *exec.ExitError
		if !errors.As(err, &exitError) {
			t.Fatalf("run %s %v: %v", binary, args, err)
		}
		exitStatus = exitError.ExitCode()
	}
	return commandRun{exitStatus: exitStatus, stdout: stdout.Bytes(), stderr: stderr.Bytes()}
}

func recordRun(records map[string][]byte, prefix string, run commandRun) {
	records[prefix+"exit-status.txt"] = []byte(fmt.Sprintf("%d\n", run.exitStatus))
	records[prefix+"stdout.txt"] = run.stdout
	records[prefix+"stderr.txt"] = run.stderr
}

func recordOutputs(t *testing.T, records map[string][]byte, prefix, directory string) {
	t.Helper()
	err := filepath.WalkDir(directory, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			return nil
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		relative, err := filepath.Rel(directory, path)
		if err != nil {
			return err
		}
		records[prefix+filepath.ToSlash(relative)] = raw
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

func privateDirectory(t *testing.T) string {
	t.Helper()
	// The commands open every component of -output-dir with O_NOFOLLOW, so the
	// temporary directory must be given without symlinked ancestors.
	base, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	directory := filepath.Join(base, "output")
	if err := os.Mkdir(directory, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(directory, 0o700); err != nil {
		t.Fatal(err)
	}
	return directory
}

func produceRawfirst(t *testing.T, root, binary string) map[string][]byte {
	t.Helper()
	outputDir := privateDirectory(t)
	run := runCommand(t, root, binary,
		"-source-bundle", filepath.Join(root, "internal/candidatefacts/testdata/canonical/source/bundle.json"),
		"-output-dir", outputDir)
	records := map[string][]byte{}
	recordRun(records, "rawfirst/", run)
	recordOutputs(t, records, "rawfirst/output/", outputDir)
	return records
}

func m7AndRegistryArgs(root string) []string {
	return []string{
		"--registry", filepath.Join(root, "internal/coexistence/contracts/multi-runtime-coexistence-registry-v1.json"),
		"--m7-graph", filepath.Join(root, "internal/candidatefacts/testdata/canonical/positive/graph.json"),
		"--m7-replay", filepath.Join(root, "internal/candidatefacts/testdata/canonical/positive/replay-result.json"),
		"--m7-registry", filepath.Join(root, "internal/candidatefacts/contracts/draft-candidate-fact-registry-v1.json"),
		"--m7-source-bundle", filepath.Join(root, "internal/candidatefacts/testdata/canonical/source/bundle.json"),
		"--m7-source-replay", filepath.Join(root, "internal/candidatefacts/testdata/canonical/source/replay-result.json"),
	}
}

func decodeObject(t *testing.T, raw []byte) map[string]any {
	t.Helper()
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var value map[string]any
	if err := decoder.Decode(&value); err != nil {
		t.Fatal(err)
	}
	if err := decoder.Decode(&struct{}{}); err != io.EOF {
		t.Fatal("JSON contains multiple top-level values")
	}
	return value
}

func generationArgs(t *testing.T, root, outputRoot string) []string {
	t.Helper()
	args := append([]string{"generate", "--output-root", outputRoot}, m7AndRegistryArgs(root)...)
	raw, err := os.ReadFile(filepath.Join(root, "internal/coexistence/testdata/canonical/positive/evidence.json"))
	if err != nil {
		t.Fatal(err)
	}
	evidence := decodeObject(t, raw)
	runs := evidence["runs"].([]any)
	var timestamps, subjects []any
	for _, rawRun := range runs {
		view := rawRun.(map[string]any)["protected_views"].([]any)[0].(map[string]any)
		meta := view["payload"].(map[string]any)["meta"].(map[string]any)
		timestamps = append(timestamps, meta["captured_at"])
		subjects = append(subjects, meta["auth_subject"])
	}
	runtimeOf := func(run any) any {
		return run.(map[string]any)["provenance"].(map[string]any)["runtime"]
	}
	values := []struct {
		flag, name string
		value      any
	}{
		{"--baseline-runtime", "baseline-runtime.json", runtimeOf(runs[0])},
		{"--compared-runtime", "compared-runtime.json", runtimeOf(runs[1])},
		{"--capture-clock", "capture-clock.json", evidence["capture_clock"]},
		{"--capture-timestamps", "capture-timestamps.json", timestamps},
		{"--masked-subjects", "masked-subjects.json", subjects},
	}
	inputs := t.TempDir()
	for _, item := range values {
		path := filepath.Join(inputs, item.name)
		encoded, err := json.MarshalIndent(item.value, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, append(encoded, '\n'), 0o600); err != nil {
			t.Fatal(err)
		}
		args = append(args, item.flag, path)
	}
	return args
}

func produceMsp08harness(t *testing.T, root, binary string) map[string][]byte {
	t.Helper()
	evidence := filepath.Join(root, "internal/coexistence/testdata/canonical/positive/evidence.json")
	records := map[string][]byte{}
	for _, name := range []string{"verify", "report"} {
		args := append([]string{name, "--evidence", evidence}, m7AndRegistryArgs(root)...)
		recordRun(records, "msp08harness/"+name+"/", runCommand(t, root, binary, args...))
	}
	generated := filepath.Join(t.TempDir(), "generated")
	run := runCommand(t, root, binary, generationArgs(t, root, generated)...)
	recordRun(records, "msp08harness/generate/", run)
	recordOutputs(t, records, "msp08harness/generate/output/", generated)
	return records
}

func produceLeafpromotionartifacts(t *testing.T, root, binary string) map[string][]byte {
	t.Helper()
	records := map[string][]byte{}
	inputs := t.TempDir()
	paths := map[string]string{}
	for _, name := range leafInputs {
		raw, err := os.ReadFile(filepath.Join(replayRoot, "leafpromotionartifacts", name))
		if err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(inputs, name)
		if err := os.WriteFile(path, raw, 0o600); err != nil {
			t.Fatal(err)
		}
		paths[name] = path
		records["leafpromotionartifacts/"+name] = raw
	}
	outputDir := privateDirectory(t)
	run := runCommand(t, root, binary,
		"-manifest", paths["manifest.json"], "-pre", paths["pre.json"], "-post", paths["post.json"],
		"-output-dir", outputDir)
	recordRun(records, "leafpromotionartifacts/", run)
	recordOutputs(t, records, "leafpromotionartifacts/output/", outputDir)
	return records
}

func assertReplay(t *testing.T, produced map[string][]byte) {
	t.Helper()
	prefixes := map[string]bool{}
	for name := range produced {
		prefixes[strings.SplitN(name, "/", 2)[0]] = true
	}
	var names []string
	for prefix := range prefixes {
		err := filepath.WalkDir(filepath.Join(replayRoot, prefix), func(path string, entry fs.DirEntry, walkErr error) error {
			if walkErr != nil {
				return walkErr
			}
			if entry.IsDir() {
				return nil
			}
			relative, err := filepath.Rel(replayRoot, path)
			if err != nil {
				return err
			}
			names = append(names, filepath.ToSlash(relative))
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	for name := range produced {
		names = append(names, name)
	}
	sort.Strings(names)
	for index, name := range names {
		if index > 0 && names[index-1] == name {
			continue
		}
		want, err := os.ReadFile(filepath.Join(replayRoot, filepath.FromSlash(name)))
		if err != nil {
			t.Errorf("%s: no saved old record: %v", name, err)
			continue
		}
		got, present := produced[name]
		if !present {
			t.Errorf("%s: saved old record has no counterpart in the new run", name)
			continue
		}
		if !bytes.Equal(got, want) {
			t.Errorf("%s: new run differs from the saved old record (%d bytes vs %d)", name, len(got), len(want))
		}
	}
}
