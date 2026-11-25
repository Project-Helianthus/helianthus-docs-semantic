package libraryhost

import (
	"context"
	"errors"
	"fmt"
	"reflect"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-ebusgateway/matter"
)

const hostSource = "matter/libraryhost/host.go"
const hostTests = "matter/libraryhost/host_test.go"

func statusOf(h *Host) fields {
	s := h.Status()
	return fields{{"state", s.State}, {"reason", s.Reason}, {"class", s.Class}, {"epoch", s.Epoch}, {"owned_work", s.OwnedWork}, {"resources", s.Resources}, {"stale_rejected", s.StaleRejected}}
}

func countsOf(r *aa17Rig) fields {
	captures, qualifies, classCalls, news, closes := r.counts()
	r.mu.Lock()
	tokens := r.tokens
	r.mu.Unlock()
	return fields{{"captures", captures}, {"qualifies", qualifies}, {"class_calls", classCalls}, {"news", news}, {"closes", closes}, {"tokens", tokens}}
}

// outcomeOf records an error the way the host reports it: its text and which sentinel it matches.
func outcomeOf(err error) fields {
	if err == nil {
		return fields{{"error", nil}}
	}
	var unavailable *UnavailableError
	reason := any(nil)
	if errors.As(err, &unavailable) {
		reason = unavailable.Reason
	}
	return fields{{"error", err.Error()}, {"unavailable_reason", reason}, {"is_unavailable", errors.Is(err, ErrUnavailable)}, {"is_quiesce", errors.Is(err, ErrQuiesce)},
		{"is_quarantined", errors.Is(err, ErrQuarantined)}, {"is_stale_callback", errors.Is(err, ErrStaleCallback)}, {"is_generation_changed", errors.Is(err, ErrGenerationChanged)},
		{"is_snapshot_unavailable", errors.Is(err, ErrSnapshotUnavailable)}, {"is_context_canceled", errors.Is(err, context.Canceled)}, {"is_deadline_exceeded", errors.Is(err, context.DeadlineExceeded)}}
}

type trace struct {
	steps []fields
}

func (tr *trace) add(name string, items ...kv) {
	tr.steps = append(tr.steps, append(fields{{"step", name}}, items...))
}

func (tr *trace) call(name string, err error, host *Host, rig *aa17Rig) {
	items := fields{{"outcome", outcomeOf(err)}}
	if host != nil {
		items = append(items, kv{"status", statusOf(host)})
	}
	if rig != nil {
		items = append(items, kv{"counts", countsOf(rig)})
	}
	tr.add(name, items...)
}

type hostCase struct {
	t         *testing.T
	group     string
	name      string
	stimulus  string
	rig       fields
	configure fields
	script    []string
	tr        trace
}

func newHostCase(t *testing.T, group, name, stimulus string, script ...string) *hostCase {
	return &hostCase{t: t, group: group, name: name, stimulus: stimulus, script: script, rig: fields{},
		configure: fields{{"enabled", true}, {"selection", aa17Selection}, {"generations", aa17Generations}, {"binding_class", ClassSyntheticFixture},
			{"tokens", "token-1, token-2, ... from the rig's counter unless the variant says otherwise"}, {"cleanup_budget", "default"}}}
}

func (c *hostCase) variant(items ...kv) *hostCase {
	c.rig = append(c.rig, items...)
	return c
}

func (c *hostCase) emit() {
	c.t.Helper()
	oracleCase(c.t, c.group, c.name, hostSource, hostTests, c.stimulus,
		obj(kv{"configuration", c.configure}, kv{"rig_variant", c.rig}, kv{"script", c.script}), obj(kv{"observations", c.tr.steps}))
}

func TestOracleLibraryHost(t *testing.T) {
	recordDisabled(t)
	recordMissingPorts(t)
	recordRows(t)
	recordBoundRequest(t)
	recordPortFailures(t)
	recordFactoryFailure(t)
	recordStamp(t)
	recordRestart(t)
	recordToken(t)
	recordDuplicateStart(t)
	recordStop(t)
	recordCloseFailure(t)
	recordThreeCycles(t)
	recordProject(t)
	recordImports(t)
	recordCancellation(t)
	recordStopFencing(t)
}

func recordDisabled(t *testing.T) {
	c := newHostCase(t, "lifecycle", "disabled-allocates-nothing", "TestAA17ZeroConfigAndDisabledAllocateNothing",
		"Config{} has Enabled false", "disabled host: Start, Restart, Stop", "positive control with Enabled true: Start, Stop")
	c.configure = fields{{"zero_config_enabled", (Config{}).Enabled}, {"enabled", false}, {"selection", aa17Selection}, {"generations", aa17Generations}, {"binding_class", ClassSyntheticFixture}}
	rig := aa17NewRig()
	cfg := rig.config()
	cfg.Enabled = false
	host := New(cfg)
	ctx := context.Background()
	c.tr.call("Start", host.Start(ctx), host, rig)
	c.tr.call("Restart", host.Restart(ctx), host, rig)
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	control := aa17NewRig()
	enabled := New(control.config())
	c.tr.call("positive control Start (Enabled true)", enabled.Start(ctx), enabled, control)
	c.tr.call("positive control Stop", enabled.Stop(ctx), enabled, control)
	c.emit()
}

func recordMissingPorts(t *testing.T) {
	for _, tc := range []struct {
		name   string
		mutate func(*Config)
	}{
		{"factory", func(c *Config) { c.Factory = nil }},
		{"qualifier", func(c *Config) { c.Qualifier = nil }},
		{"snapshots", func(c *Config) { c.Snapshots = nil }},
		{"tag", func(c *Config) { c.Selection.Tag = "" }},
		{"target", func(c *Config) { c.Selection.Target = "" }},
		{"profile", func(c *Config) { c.Selection.Profile = "" }},
		{"evidence", func(c *Config) { c.Selection.Evidence = "" }},
	} {
		c := newHostCase(t, "unavailable", "missing-"+tc.name, "TestAA17MissingPortsAndSelectionStayUnavailable/"+tc.name, "Start with the named port or selection member empty")
		c.variant(kv{"empty_member", tc.name})
		rig := aa17NewRig()
		cfg := rig.config()
		tc.mutate(&cfg)
		host := New(cfg)
		c.tr.call("Start", host.Start(context.Background()), host, rig)
		c.emit()
	}
}

func recordRows(t *testing.T) {
	onEach := func(kind RowKind, change func(*Row)) func([]Row) []Row {
		return func(rows []Row) []Row {
			for i := range rows {
				if rows[i].Kind == kind {
					change(&rows[i])
				}
			}
			return rows
		}
	}
	type rowCase struct {
		name   string
		mutate func([]Row) []Row
		note   string
	}
	cases := []rowCase{
		{"no-rows", func([]Row) []Row { return nil }, "the qualifier returns no rows"},
		{"duplicate-row", func(rows []Row) []Row { return append(rows, rows[0]) }, "the first row is returned twice"},
		{"extra-row", func(rows []Row) []Row {
			extra := rows[0]
			extra.Kind = "extra"
			return append(rows, extra)
		}, "a sixth row of kind extra is added"},
	}
	for _, kind := range requiredRows {
		kind := kind
		cases = append(cases,
			rowCase{"missing-" + string(kind), func(rows []Row) []Row {
				kept := rows[:0]
				for _, row := range rows {
					if row.Kind != kind {
						kept = append(kept, row)
					}
				}
				return kept
			}, "the row of kind " + string(kind) + " is removed"},
			rowCase{"failed-" + string(kind), onEach(kind, func(r *Row) { r.Verdict = VerdictFail }), "its verdict is fail"},
			rowCase{"unknown-" + string(kind), onEach(kind, func(r *Row) { r.Verdict = VerdictUnknown }), "its verdict is unknown"},
			rowCase{"zero-verdict-" + string(kind), onEach(kind, func(r *Row) { r.Verdict = "" }), "its verdict is the zero value"},
			rowCase{"selected-tag-" + string(kind), onEach(kind, func(r *Row) { r.Selection.Tag = "other" }), "its selection tag is other"},
			rowCase{"selected-target-" + string(kind), onEach(kind, func(r *Row) { r.Selection.Target = "other" }), "its selection target is other"},
			rowCase{"selected-profile-" + string(kind), onEach(kind, func(r *Row) { r.Selection.Profile = "other" }), "its selection profile is other"},
			rowCase{"selected-evidence-" + string(kind), onEach(kind, func(r *Row) { r.Selection.Evidence = "other" }), "its selection evidence is other"},
			rowCase{"source-generation-" + string(kind), onEach(kind, func(r *Row) { r.Generations.Source++ }), "its source generation is one higher"},
			rowCase{"binding-generation-" + string(kind), onEach(kind, func(r *Row) { r.Generations.Binding++ }), "its binding generation is one higher"},
			rowCase{"driver-generation-" + string(kind), onEach(kind, func(r *Row) { r.Generations.NativeDriver++ }), "its native driver generation is one higher"},
			rowCase{"token-" + string(kind), onEach(kind, func(r *Row) { r.Token += "-old" }), "its token has the suffix -old"},
			rowCase{"origin-" + string(kind), onEach(kind, func(r *Row) { r.Origin = ClassProduction }), "its origin is production"},
		)
	}
	for _, tc := range cases {
		c := newHostCase(t, "rows", tc.name, "TestAA17EveryRowAndIdentityMustPassBeforeLaunch/"+tc.name, "Start with the qualifier returning the five passing rows, changed as the variant says")
		c.variant(kv{"row_variant", tc.name}, kv{"description", tc.note})
		rig := aa17NewRig()
		rig.mutateRows = tc.mutate
		host := New(rig.config())
		c.tr.call("Start", host.Start(context.Background()), host, rig)
		c.tr.add("released", kv{"owned_work", host.Status().OwnedWork}, kv{"resources", host.Status().Resources})
		c.emit()
	}
}

func recordBoundRequest(t *testing.T) {
	c := newHostCase(t, "lifecycle", "rows-bound-to-the-exact-request", "TestAA17RowsAreBoundToTheExactRequest", "Start", "read the qualifier's requests and the session stamp", "Stop")
	rig := aa17NewRig()
	host := New(rig.config())
	ctx := context.Background()
	c.tr.call("Start", host.Start(ctx), host, rig)
	rig.mu.Lock()
	requests := append([]Request(nil), rig.requests...)
	rig.mu.Unlock()
	c.tr.add("qualifier requests", kv{"requests", requests}, kv{"stamp", rig.session(0).Stamp()})
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.emit()
}

func recordPortFailures(t *testing.T) {
	failure := errors.New("synthetic port failure")
	for _, tc := range []struct {
		name   string
		mutate func(*aa17Rig)
		note   string
	}{
		{"snapshot", func(r *aa17Rig) { r.captureErr = failure }, "the snapshot port fails"},
		{"source-generation-zero", func(r *aa17Rig) { r.generations.Source = 0 }, "the captured source generation is zero"},
		{"binding-generation-zero", func(r *aa17Rig) { r.generations.Binding = 0 }, "the captured binding generation is zero"},
		{"driver-generation-zero", func(r *aa17Rig) { r.generations.NativeDriver = 0 }, "the captured native driver generation is zero"},
		{"qualifier", func(r *aa17Rig) { r.rowsErr = failure }, "the qualifier fails"},
		{"token-error", func(r *aa17Rig) { r.tokenOverride = func() (string, error) { return "", failure } }, "the token source fails"},
		{"token-empty", func(r *aa17Rig) { r.tokenOverride = func() (string, error) { return "", nil } }, "the token source returns an empty token"},
		{"unknown-class", func(r *aa17Rig) { r.class = "other" }, "the factory class is other"},
		{"fixture-evidence-production-binding", func(r *aa17Rig) {
			r.class = ClassProduction
			r.mutateRows = func(rows []Row) []Row {
				for i := range rows {
					rows[i].Origin = ClassSyntheticFixture
				}
				return rows
			}
		}, "a production factory with rows of origin synthetic-fixture"},
		{"production-evidence-fixture-binding", func(r *aa17Rig) {
			r.mutateRows = func(rows []Row) []Row {
				for i := range rows {
					rows[i].Origin = ClassProduction
				}
				return rows
			}
		}, "a synthetic-fixture factory with rows of origin production"},
	} {
		c := newHostCase(t, "port-failure", tc.name, "TestAA17PortFailuresAndClassBoundaryStayUnavailable/"+tc.name, "Start")
		c.variant(kv{"port_variant", tc.name}, kv{"description", tc.note}, kv{"failure_text", failure.Error()})
		rig := aa17NewRig()
		tc.mutate(rig)
		host := New(rig.config())
		c.tr.call("Start", host.Start(context.Background()), host, rig)
		c.emit()
	}
	c := newHostCase(t, "port-failure", "cancelled-before-launch", "TestAA17PortFailuresAndClassBoundaryStayUnavailable/cancelled-before-launch", "Start with a context that the first snapshot capture cancels")
	rig := aa17NewRig()
	ctx, cancel := context.WithCancel(context.Background())
	rig.captureHook = func(context.Context) error { cancel(); return nil }
	host := New(rig.config())
	c.tr.call("Start", host.Start(ctx), host, rig)
	c.emit()
}

func recordFactoryFailure(t *testing.T) {
	for _, tc := range []struct {
		name   string
		mutate func(*aa17Rig)
	}{
		{"error", func(r *aa17Rig) { r.newErr = errors.New("synthetic factory failure") }},
		{"nil-binding", func(r *aa17Rig) { r.newNil = true }},
	} {
		c := newHostCase(t, "factory", "failure-"+tc.name, "TestAA17FactoryFailureDrainsItsTasks/"+tc.name, "the factory starts one owned task that waits for cancellation, then fails", "Start", "start a task on the old session")
		c.variant(kv{"factory_failure", tc.name})
		rig := aa17NewRig()
		tc.mutate(rig)
		joined := make(chan struct{})
		var taskErr error
		rig.onNew = func(session *Session) {
			taskErr = session.Go(func(ctx context.Context) {
				<-ctx.Done()
				close(joined)
			})
		}
		host := New(rig.config())
		c.tr.call("Start", host.Start(context.Background()), host, rig)
		select {
		case <-joined:
			c.tr.add("factory task", kv{"joined", true}, kv{"owned_by_the_factory", outcomeOf(taskErr)})
		default:
			c.tr.add("factory task", kv{"joined", false}, kv{"owned_by_the_factory", outcomeOf(taskErr)})
		}
		ran := false
		late := rig.session(0).Go(func(context.Context) { ran = true })
		c.tr.add("late task on the old session", kv{"outcome", outcomeOf(late)}, kv{"task_ran", ran})
		c.emit()
	}
}

func recordStamp(t *testing.T) {
	c := newHostCase(t, "stamp", "every-field-independently", "TestAA17CallbackStampVariesEveryFieldIndependently", "Start", "Deliver with the exact stamp", "Deliver with each stamp field changed in turn", "Stop")
	rig := aa17NewRig()
	host := New(rig.config())
	ctx := context.Background()
	c.tr.call("Start", host.Start(ctx), host, rig)
	session := rig.session(0)
	exact := session.Stamp()
	ran := 0
	callback := func(context.Context) error { ran++; return nil }
	c.tr.add("Deliver with the exact stamp", kv{"stamp", exact}, kv{"outcome", outcomeOf(session.Deliver(exact, callback))}, kv{"callback_runs", ran}, kv{"status", statusOf(host)})
	for _, tc := range []struct {
		name   string
		change func(*Stamp)
	}{
		{"tag", func(s *Stamp) { s.Selection.Tag = "other" }},
		{"target", func(s *Stamp) { s.Selection.Target = "other" }},
		{"profile", func(s *Stamp) { s.Selection.Profile = "other" }},
		{"evidence", func(s *Stamp) { s.Selection.Evidence = "other" }},
		{"source", func(s *Stamp) { s.Generations.Source++ }},
		{"binding", func(s *Stamp) { s.Generations.Binding++ }},
		{"driver", func(s *Stamp) { s.Generations.NativeDriver++ }},
		{"epoch", func(s *Stamp) { s.Epoch++ }},
		{"token", func(s *Stamp) { s.Token += "-old" }},
	} {
		stamp := exact
		tc.change(&stamp)
		err := session.Deliver(stamp, callback)
		c.tr.add("Deliver with the "+tc.name+" changed", kv{"stamp", stamp}, kv{"outcome", outcomeOf(err)}, kv{"callback_runs", ran}, kv{"status", statusOf(host)})
	}
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.emit()
}

func recordRestart(t *testing.T) {
	c := newHostCase(t, "restart", "rejects-every-old-route", "TestAA17RestartRejectsEveryOldRoute", "Start", "Restart", "old session and fresh session: Deliver with each stamp pair, Go, Project", "Stop")
	rig := aa17NewRig()
	aa17InstallProjection(t, rig)
	host := New(rig.config())
	ctx := context.Background()
	c.tr.call("Start", host.Start(ctx), host, rig)
	old := rig.session(0)
	oldStamp := old.Stamp()
	c.tr.call("Restart", host.Restart(ctx), host, rig)
	fresh := rig.session(1)
	freshStamp := fresh.Stamp()
	c.tr.add("stamps", kv{"old", oldStamp}, kv{"fresh", freshStamp})
	ran := 0
	callback := func(context.Context) error { ran++; return nil }
	for _, tc := range []struct {
		name    string
		session *Session
		stamp   Stamp
	}{
		{"old-session-old-stamp", old, oldStamp},
		{"old-session-new-stamp", old, freshStamp},
		{"new-session-old-stamp", fresh, oldStamp},
	} {
		c.tr.add("Deliver "+tc.name, kv{"outcome", outcomeOf(tc.session.Deliver(tc.stamp, callback))}, kv{"callback_runs", ran})
	}
	c.tr.add("old session Go", kv{"outcome", outcomeOf(old.Go(func(context.Context) { ran++ }))}, kv{"callback_runs", ran})
	_, projectErr := old.Project(ctx)
	c.tr.add("old session Project", kv{"outcome", outcomeOf(projectErr)}, kv{"callback_runs", ran})
	c.tr.add("fresh session Deliver with the fresh stamp", kv{"outcome", outcomeOf(fresh.Deliver(freshStamp, callback))}, kv{"callback_runs", ran})
	result, freshErr := fresh.Project(ctx)
	c.tr.add("fresh session Project", kv{"outcome", outcomeOf(freshErr)}, kv{"result_attributes", result.Document.Attributes})
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.emit()

	d := newHostCase(t, "restart", "disabled-host-stays-disabled", "TestAA17RestartOfDisabledHostStaysDisabled", "Restart on a disabled host")
	disabled := aa17NewRig()
	cfg := disabled.config()
	cfg.Enabled = false
	h := New(cfg)
	d.tr.call("Restart", h.Restart(context.Background()), h, disabled)
	d.emit()
}

func recordToken(t *testing.T) {
	c := newHostCase(t, "token", "reused-after-stop", "TestAA17ReusedTokenIsRefused", "token source always returns same", "Start", "Stop", "Start")
	c.variant(kv{"token_source", "always returns same"})
	rig := aa17NewRig()
	rig.tokenOverride = func() (string, error) { return "same", nil }
	host := New(rig.config())
	ctx := context.Background()
	c.tr.call("Start", host.Start(ctx), host, rig)
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.tr.call("Start again", host.Start(ctx), host, rig)
	c.emit()

	d := newHostCase(t, "token", "replay-across-lifecycles", "TestAA17TokenReplayAcrossLifecyclesIsRefused", "token sequence A, B, A", "Start, Stop twice", "Start")
	d.variant(kv{"token_source", "returns A, then B, then A"})
	replay := aa17NewRig()
	sequence := []string{"A", "B", "A"}
	replay.tokenOverride = func() (string, error) {
		token := sequence[0]
		sequence = sequence[1:]
		return token, nil
	}
	h := New(replay.config())
	for i := 0; i < 2; i++ {
		d.tr.call(fmt.Sprintf("Start %d", i+1), h.Start(ctx), h, replay)
		d.tr.call(fmt.Sprintf("Stop %d", i+1), h.Stop(ctx), h, replay)
	}
	d.tr.call("Start 3", h.Start(ctx), h, replay)
	d.emit()
}

func recordDuplicateStart(t *testing.T) {
	c := newHostCase(t, "start", "duplicate-concurrent-starts", "TestAA17DuplicateStartCannotAllocateASecondBinding", "eight concurrent Start calls", "Stop", "Stop again")
	rig := aa17NewRig()
	host := New(rig.config())
	ctx := context.Background()
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- host.Start(ctx)
		}()
	}
	wg.Wait()
	close(errs)
	failed := 0
	for err := range errs {
		if err != nil {
			failed++
		}
	}
	c.tr.add("eight Start calls", kv{"calls_with_an_error", failed}, kv{"status", statusOf(host)}, kv{"counts", countsOf(rig)})
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.tr.call("Stop again", host.Stop(ctx), host, rig)
	c.emit()
}

func recordStop(t *testing.T) {
	ctx := context.Background()
	c := newHostCase(t, "stop", "fences-drains-then-releases", "TestAA17StopFencesDrainsThenReleases", "Start", "Deliver a callback that blocks", "Stop in another goroutine", "Deliver during Stop", "release the callback")
	rig := aa17NewRig()
	host := New(rig.config())
	c.tr.call("Start", host.Start(ctx), host, rig)
	session := rig.session(0)
	stamp := session.Stamp()
	entered, finish := make(chan struct{}), make(chan struct{})
	deliverDone := make(chan error, 1)
	go func() {
		deliverDone <- session.Deliver(stamp, func(context.Context) error {
			close(entered)
			<-finish
			return nil
		})
	}()
	<-entered
	stopDone := make(chan error, 1)
	go func() { stopDone <- host.Stop(ctx) }()
	aa17WaitState(host, StateStopping)
	admitted := false
	late := session.Deliver(stamp, func(context.Context) error { admitted = true; return nil })
	c.tr.add("Deliver while Stop drains", kv{"outcome", outcomeOf(late)}, kv{"callback_ran", admitted}, kv{"status", statusOf(host)}, kv{"counts", countsOf(rig)})
	returned := false
	select {
	case <-stopDone:
		returned = true
	default:
	}
	c.tr.add("Stop before the callback finished", kv{"returned", returned})
	close(finish)
	c.tr.add("blocked callback result", kv{"outcome", outcomeOf(<-deliverDone)})
	c.tr.add("Stop result", kv{"outcome", outcomeOf(<-stopDone)}, kv{"status", statusOf(host)}, kv{"counts", countsOf(rig)})
	c.emit()

	d := newHostCase(t, "stop", "unquiesced-task-quarantines", "TestAA17UnquiescedTaskQuarantinesAndBlocksRestart", "Start", "Go a task that waits for a release", "Stop with a budget cancelled once Stop holds the operation lock", "Start", "Restart with a budget cancelled while stopping", "Deliver", "release the task", "Stop", "Start")
	rigQ := aa17NewRig()
	hostQ := New(rigQ.config())
	d.tr.call("Start", hostQ.Start(ctx), hostQ, rigQ)
	sessionQ := rigQ.session(0)
	stampQ := sessionQ.Stamp()
	release, joined := make(chan struct{}), make(chan struct{})
	goErr := sessionQ.Go(func(context.Context) {
		<-release
		close(joined)
	})
	d.tr.add("Go task", kv{"outcome", outcomeOf(goErr)})
	stopCtx, stopCancel := context.WithCancel(ctx)
	stopDoneQ := make(chan error, 1)
	go func() { stopDoneQ <- hostQ.Stop(stopCtx) }()
	deadline := time.Now().Add(10 * time.Second)
	for len(hostQ.ops) == 0 {
		if time.Now().After(deadline) {
			t.Fatal("first stop did not take the operation lock within 10s")
		}
		runtime.Gosched()
	}
	stopCancel()
	d.tr.call("Stop with a cancelled budget", <-stopDoneQ, hostQ, rigQ)
	d.tr.call("Start while quarantined", hostQ.Start(ctx), hostQ, rigQ)
	blocked, restartCancel := context.WithCancel(ctx)
	restartDone := make(chan error, 1)
	go func() { restartDone <- hostQ.Restart(blocked) }()
	aa17WaitState(hostQ, StateStopping)
	restartCancel()
	d.tr.call("Restart with a cancelled budget", <-restartDone, hostQ, rigQ)
	ranQ := false
	d.tr.add("Deliver on the quarantined generation", kv{"outcome", outcomeOf(sessionQ.Deliver(stampQ, func(context.Context) error { ranQ = true; return nil }))}, kv{"callback_ran", ranQ})
	close(release)
	<-joined
	d.tr.call("Stop after the task finished", hostQ.Stop(ctx), hostQ, rigQ)
	d.tr.call("Start after quiesce", hostQ.Start(ctx), hostQ, rigQ)
	d.tr.add("stamps", kv{"first", stampQ}, kv{"second", rigQ.session(1).Stamp()})
	d.tr.call("final Stop", hostQ.Stop(ctx), hostQ, rigQ)
	d.emit()
}

func recordCloseFailure(t *testing.T) {
	ctx := context.Background()
	c := newHostCase(t, "close", "error-then-retry", "TestAA17CloseFailureAndHangStayQuarantined/error-then-retry", "Close returns a synthetic failure", "Start", "Stop", "Close succeeds", "Stop")
	failure := errors.New("synthetic close failure")
	c.variant(kv{"close_failure_text", failure.Error()})
	rig := aa17NewRig()
	rig.closeErr = failure
	host := New(rig.config())
	c.tr.call("Start", host.Start(ctx), host, rig)
	err := host.Stop(ctx)
	c.tr.add("Stop with the failing Close", kv{"outcome", outcomeOf(err)}, kv{"is_close_failure", errors.Is(err, failure)}, kv{"status", statusOf(host)})
	rig.mu.Lock()
	rig.closeErr = nil
	rig.mu.Unlock()
	c.tr.call("Stop after Close succeeds", host.Stop(ctx), host, rig)
	c.emit()

	d := newHostCase(t, "close", "hang-bounded-and-not-reinvoked", "TestAA17CloseFailureAndHangStayQuarantined/hang-is-bounded-and-not-reinvoked", "Close blocks until released", "Start", "Stop with a budget cancelled once Close was called", "release Close", "Stop")
	hung := aa17NewRig()
	unblock := make(chan struct{})
	hung.closeHook = func(context.Context) error { <-unblock; return nil }
	h := New(hung.config())
	d.tr.call("Start", h.Start(ctx), h, hung)
	budget, cancel := context.WithCancel(ctx)
	stopDone := make(chan error, 1)
	go func() { stopDone <- h.Stop(budget) }()
	for {
		if _, _, _, _, closes := hung.counts(); closes == 1 {
			break
		}
		runtime.Gosched()
	}
	cancel()
	d.tr.call("Stop with the cancelled budget", <-stopDone, h, hung)
	close(unblock)
	d.tr.call("Stop after Close was released", h.Stop(ctx), h, hung)
	d.emit()
}

func recordThreeCycles(t *testing.T) {
	c := newHostCase(t, "lifecycle", "three-cycles-leave-nothing-owned", "TestAA17ThreeCyclesLeaveNothingOwned", "three cycles of Start, Project, Stop with an owned task", "an unavailable host: three cycles of Start and Stop with no rows")
	rig := aa17NewRig()
	aa17InstallProjection(t, rig)
	joined := 0
	var mu sync.Mutex
	rig.onNew = func(session *Session) {
		_ = session.Go(func(ctx context.Context) {
			<-ctx.Done()
			mu.Lock()
			joined++
			mu.Unlock()
		})
	}
	host := New(rig.config())
	ctx := context.Background()
	tokens := map[string]struct{}{}
	for cycle := 1; cycle <= 3; cycle++ {
		c.tr.call(fmt.Sprintf("cycle %d Start", cycle), host.Start(ctx), host, rig)
		session := rig.session(cycle - 1)
		result, err := session.Project(ctx)
		c.tr.add(fmt.Sprintf("cycle %d Project", cycle), kv{"outcome", outcomeOf(err)}, kv{"attributes", result.Document.Attributes}, kv{"status", statusOf(host)}, kv{"stamp", session.Stamp()})
		tokens[session.Stamp().Token] = struct{}{}
		c.tr.call(fmt.Sprintf("cycle %d Stop", cycle), host.Stop(ctx), host, rig)
		mu.Lock()
		c.tr.add(fmt.Sprintf("cycle %d joined tasks", cycle), kv{"joined", joined})
		mu.Unlock()
	}
	c.tr.add("distinct tokens", kv{"count", len(tokens)})
	absent := aa17NewRig()
	absent.mutateRows = func([]Row) []Row { return nil }
	unavailable := New(absent.config())
	for cycle := 1; cycle <= 3; cycle++ {
		c.tr.call(fmt.Sprintf("unavailable cycle %d Start", cycle), unavailable.Start(ctx), unavailable, absent)
		c.tr.call(fmt.Sprintf("unavailable cycle %d Stop", cycle), unavailable.Stop(ctx), unavailable, absent)
	}
	c.emit()
}

func recordProject(t *testing.T) {
	ctx := context.Background()
	c := newHostCase(t, "project", "uses-the-projector", "TestAA17ProjectUsesTheAA03Projector", "Start", "Project", "Project with each generation moved", "Project with a capture failure", "Project with an invalid evaluation digest", "Stop")
	rig := aa17NewRig()
	aa17InstallProjection(t, rig)
	want, wantErr := matter.Project161(rig.capture.Snapshot, rig.capture.Evaluation)
	c.tr.add("direct Project161 control", kv{"snapshot", rig.capture.Snapshot}, kv{"evaluation", rig.capture.Evaluation}, kv{"outcome", outcomeOf(wantErr)}, kv{"result", want})
	host := New(rig.config())
	c.tr.call("Start", host.Start(ctx), host, rig)
	session := rig.session(0)
	got, err := session.Project(ctx)
	c.tr.add("Project", kv{"outcome", outcomeOf(err)}, kv{"result_equals_direct_project161", reflect.DeepEqual(got, want)}, kv{"target_version", got.Document.TargetVersion})
	for _, tc := range []struct {
		name   string
		change func(*Generations)
	}{
		{"source", func(g *Generations) { g.Source++ }},
		{"binding", func(g *Generations) { g.Binding++ }},
		{"driver", func(g *Generations) { g.NativeDriver++ }},
	} {
		rig.mu.Lock()
		tc.change(&rig.generations)
		moved := rig.generations
		rig.mu.Unlock()
		_, err := session.Project(ctx)
		c.tr.add("Project with the "+tc.name+" generation moved", kv{"captured_generations", moved}, kv{"outcome", outcomeOf(err)})
		rig.mu.Lock()
		rig.generations = aa17Generations
		rig.mu.Unlock()
	}
	failure := errors.New("synthetic capture failure")
	rig.mu.Lock()
	rig.captureErr = failure
	rig.mu.Unlock()
	_, err = session.Project(ctx)
	c.tr.add("Project with a capture failure", kv{"failure_text", failure.Error()}, kv{"outcome", outcomeOf(err)}, kv{"is_capture_failure", errors.Is(err, failure)})
	rig.mu.Lock()
	rig.captureErr = nil
	rig.capture.Evaluation.EvaluationDigest = "sha256:invalid"
	rig.mu.Unlock()
	result, err := session.Project(ctx)
	c.tr.add("Project with an invalid evaluation digest", kv{"outcome", outcomeOf(err)}, kv{"result_is_zero", reflect.DeepEqual(result, matter.Result161{})})
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.emit()

	for _, tc := range []struct {
		name string
		exit func(context.Context) error
	}{
		{"capture-returns-a-value", func(context.Context) error { return nil }},
		{"capture-returns-its-cancellation", func(capture context.Context) error { return capture.Err() }},
	} {
		d := newHostCase(t, "project", "stop-withholds-in-flight-"+tc.name, "TestAA17StopCancelsAndWithholdsAnInFlightProjection/"+tc.name, "Start", "Project blocks in the snapshot port until its context ends", "Stop")
		d.variant(kv{"capture_exit", tc.name})
		r := aa17NewRig()
		aa17InstallProjection(t, r)
		h := New(r.config())
		d.tr.call("Start", h.Start(ctx), h, r)
		s := r.session(0)
		entered := make(chan struct{})
		r.mu.Lock()
		r.captureHook = func(capture context.Context) error {
			close(entered)
			<-capture.Done()
			return tc.exit(capture)
		}
		r.mu.Unlock()
		result := make(chan error, 1)
		go func() {
			_, err := s.Project(ctx)
			result <- err
		}()
		<-entered
		d.tr.call("Stop", h.Stop(ctx), h, r)
		d.tr.add("in-flight Project", kv{"outcome", outcomeOf(<-result)}, kv{"status", statusOf(h)})
		d.emit()
	}
}

func recordImports(t *testing.T) {
	c := newHostCase(t, "imports", "allowed-set", "TestAA17PackageImportsNoSDKTransportOrVendorDecoding", "parse the imports of host.go", "parse one synthetic source per control import path")
	c.configure = fields{{"source_file", "matter/libraryhost/host.go"}, {"controls", []string{"net/http", "example.invalid/go-fabric", "example.invalid/vendor/decoder"}}}
	c.tr.add("host.go imports outside the allowed set", kv{"disallowed", aa17DisallowedImports(t, nil)})
	for _, path := range []string{"net/http", "example.invalid/go-fabric", "example.invalid/vendor/decoder"} {
		source := "package libraryhost\nimport _ \"" + path + "\"\n"
		c.tr.add("control "+path, kv{"source", source}, kv{"disallowed", aa17DisallowedImports(t, source)})
	}
	c.emit()
}

func recordCancellation(t *testing.T) {
	ctx := context.Background()
	for _, tc := range []struct {
		name   string
		mutate func(*Generations)
	}{
		{"source", func(g *Generations) { g.Source++ }},
		{"binding", func(g *Generations) { g.Binding++ }},
		{"native-driver", func(g *Generations) { g.NativeDriver++ }},
	} {
		c := newHostCase(t, "generation", "change-during-qualification-"+tc.name, "TestAA17GenerationChangeDuringQualificationIsFenced/"+tc.name, "Start; the qualifier moves the named generation")
		c.variant(kv{"moved_generation", tc.name})
		rig := aa17NewRig()
		rig.mutateRows = func(rows []Row) []Row {
			rig.generations = aa17Generations
			tc.mutate(&rig.generations)
			return rows
		}
		host := New(rig.config())
		c.tr.call("Start", host.Start(ctx), host, rig)
		c.emit()
	}

	c := newHostCase(t, "factory", "partial-construction-closed-and-drained", "TestAA17PartialConstructionIsClosedAndDrained", "the factory returns a binding with an error", "Start", "the factory recovers", "Start", "Stop")
	rig := aa17NewRig()
	rig.newErr = errors.New("synthetic partial construction")
	rig.newPartial = true
	host := New(rig.config())
	c.variant(kv{"factory_failure", rig.newErr.Error()})
	c.tr.call("Start", host.Start(ctx), host, rig)
	rig.newErr = nil
	rig.newPartial = false
	c.tr.call("Start after the factory recovered", host.Start(ctx), host, rig)
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.emit()

	c = newHostCase(t, "cancel", "second-capture", "TestAA17CancelOnSecondCaptureNeverConstructs", "Start with a context that the second snapshot capture cancels")
	rig = aa17NewRig()
	cctx, cancel := context.WithCancel(ctx)
	rig.captureHook = func(context.Context) error {
		rig.mu.Lock()
		second := rig.captures == 2
		rig.mu.Unlock()
		if second {
			cancel()
		}
		return nil
	}
	host = New(rig.config())
	c.tr.call("Start", host.Start(cctx), host, rig)
	cancel()
	c.emit()

	c = newHostCase(t, "cancel", "during-construction", "TestAA17CancelDuringConstructionIsNotPublishedAsRunning", "Start with a context that the factory cancels")
	rig = aa17NewRig()
	cctx, cancel = context.WithCancel(ctx)
	rig.onNew = func(*Session) { cancel() }
	host = New(rig.config())
	c.tr.call("Start", host.Start(cctx), host, rig)
	cancel()
	c.emit()

	c = newHostCase(t, "cancel", "hung-close-quarantines-within-budget", "TestAA17CancelledStartWithHungCloseQuarantinesWithinBudget", "Start with a context that the factory cancels; Close waits for its context; cleanup budget 20 ms", "Start again")
	c.configure = append(c.configure[:len(c.configure)-1], kv{"cleanup_budget", "20ms"})
	rig = aa17NewRig()
	cctx, cancel = context.WithCancel(ctx)
	rig.onNew = func(*Session) { cancel() }
	rig.closeHook = func(c context.Context) error {
		<-c.Done()
		return c.Err()
	}
	cfg := rig.config()
	cfg.CleanupBudget = 20 * time.Millisecond
	host = New(cfg)
	c.tr.call("Start", host.Start(cctx), host, rig)
	c.tr.call("Start again", host.Start(context.Background()), host, rig)
	cancel()
	c.emit()

	c = newHostCase(t, "cancel", "partial-construction-fresh-cleanup-budget", "TestAA17PartialConstructionUnderCancelledStartGetsFreshCleanupBudget", "Start with a context that the factory cancels; the factory fails with a partial binding; Close returns its context error")
	rig = aa17NewRig()
	cctx, cancel = context.WithCancel(ctx)
	rig.newErr = errors.New("synthetic partial construction")
	rig.newPartial = true
	rig.onNew = func(*Session) { cancel() }
	rig.closeHook = func(c context.Context) error { return c.Err() }
	host = New(rig.config())
	c.tr.call("Start", host.Start(cctx), host, rig)
	cancel()
	c.emit()

	c = newHostCase(t, "cancel", "partial-construction-hung-close", "TestAA17PartialConstructionWithHungCloseQuarantinesWithinBudget", "Start with a context that the factory cancels; the factory fails with a partial binding; Close waits for its context; cleanup budget 20 ms")
	c.configure = append(c.configure[:len(c.configure)-1], kv{"cleanup_budget", "20ms"})
	rig = aa17NewRig()
	cctx, cancel = context.WithCancel(ctx)
	rig.newErr = errors.New("synthetic partial construction")
	rig.newPartial = true
	rig.onNew = func(*Session) { cancel() }
	rig.closeHook = func(c context.Context) error {
		<-c.Done()
		return c.Err()
	}
	cfg = rig.config()
	cfg.CleanupBudget = 20 * time.Millisecond
	host = New(cfg)
	c.tr.call("Start", host.Start(cctx), host, rig)
	cancel()
	c.emit()
}

func recordStopFencing(t *testing.T) {
	ctx := context.Background()

	c := newHostCase(t, "stop", "before-generation-install", "TestAA17StopBeforeGenerationInstallNeverConstructs", "the second snapshot capture calls Stop with an expired context", "Start", "later Start", "Stop")
	rig := aa17NewRig()
	var host *Host
	var stopErr error
	rig.captureHook = func(context.Context) error {
		rig.mu.Lock()
		second := rig.captures == 2
		rig.mu.Unlock()
		if second {
			expired, cancel := context.WithCancel(context.Background())
			cancel()
			stopErr = host.Stop(expired)
		}
		return nil
	}
	host = New(rig.config())
	c.tr.call("Start", host.Start(ctx), host, rig)
	c.tr.add("Stop issued during the second capture", kv{"outcome", outcomeOf(stopErr)})
	rig.mu.Lock()
	rig.captureHook = nil
	rig.mu.Unlock()
	c.tr.call("later Start", host.Start(ctx), host, rig)
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.emit()

	c = newHostCase(t, "stop", "fences-a-start-holding-the-operation-lock", "TestAA17StopFencesAStartHoldingTheOperationLock", "Start blocks in the first capture", "Stop with an expired context", "release the capture", "later Start", "Stop")
	rig = aa17NewRig()
	entered, release := make(chan struct{}), make(chan struct{})
	var once sync.Once
	rig.captureHook = func(context.Context) error {
		once.Do(func() { close(entered) })
		<-release
		return nil
	}
	host = New(rig.config())
	startDone := make(chan error, 1)
	go func() { startDone <- host.Start(ctx) }()
	<-entered
	expired, cancel := context.WithCancel(ctx)
	cancel()
	c.tr.call("Stop with an expired context", host.Stop(expired), host, nil)
	close(release)
	c.tr.call("blocked Start", <-startDone, host, rig)
	rig.mu.Lock()
	rig.captureHook = nil
	rig.mu.Unlock()
	c.tr.call("later Start", host.Start(ctx), host, rig)
	c.tr.call("Stop", host.Stop(ctx), host, rig)
	c.emit()

	for _, mode := range []string{"retries-close-after-an-expired-attempt", "retry-accepts-non-comparable-contexts"} {
		stimulus := "TestAA17StopRetriesCloseAfterAnExpiredAttempt"
		script := []string{"Close waits for its context on the first call and succeeds after", "Start", "Stop with a budget cancelled once Close received it", "Stop with a live budget"}
		if mode != "retries-close-after-an-expired-attempt" {
			stimulus = "TestAA17StopRetryAcceptsNonComparableContexts"
			script = []string{"Close waits for its context on the first call and succeeds after", "Start", "Stop with a context type holding a slice, cancelled once Close received it", "Stop with another such context"}
		}
		c = newHostCase(t, "stop", mode, stimulus, script...)
		rig = aa17NewRig()
		observed, returned := make(chan struct{}), make(chan struct{})
		var mu sync.Mutex
		calls := 0
		rig.closeHook = func(ctx context.Context) error {
			mu.Lock()
			calls++
			first := calls == 1
			mu.Unlock()
			if !first {
				return nil
			}
			close(observed)
			<-ctx.Done()
			defer close(returned)
			return ctx.Err()
		}
		host = New(rig.config())
		c.tr.call("Start", host.Start(ctx), host, rig)
		base, cancelBase := context.WithCancel(ctx)
		var first, second context.Context = base, ctx
		if mode != "retries-close-after-an-expired-attempt" {
			first, second = aa17SliceContext{Context: base, tag: []int{1}}, aa17SliceContext{Context: ctx, tag: []int{2}}
		}
		stopDone := make(chan error, 1)
		go func() { stopDone <- host.Stop(first) }()
		<-observed
		cancelBase()
		c.tr.call("first Stop", <-stopDone, host, rig)
		<-returned
		c.tr.call("follow-up Stop", host.Stop(second), host, rig)
		mu.Lock()
		c.tr.add("Close calls", kv{"count", calls})
		mu.Unlock()
		c.emit()
	}

	c = newHostCase(t, "stop", "expired-stop-fences-the-running-generation", "TestAA17ExpiredStopStillFencesTheRunningGeneration", "Start", "Deliver", "hold the operation lock", "Stop with an expired context", "release the lock", "Deliver", "Start", "Stop")
	rig = aa17NewRig()
	host = New(rig.config())
	c.tr.call("Start", host.Start(ctx), host, rig)
	session := rig.session(0)
	stamp := session.Stamp()
	c.tr.add("Deliver while running", kv{"outcome", outcomeOf(session.Deliver(stamp, func(context.Context) error { return nil }))})
	expired, cancel = context.WithCancel(ctx)
	cancel()
	_ = host.acquire(ctx)
	c.tr.call("Stop with an expired context while the operation lock is held", host.Stop(expired), host, rig)
	host.release()
	ran := false
	c.tr.add("Deliver after the expired Stop", kv{"outcome", outcomeOf(session.Deliver(stamp, func(context.Context) error { ran = true; return nil }))}, kv{"callback_ran", ran})
	c.tr.call("Start", host.Start(ctx), host, rig)
	c.tr.call("Stop with a live budget", host.Stop(ctx), host, rig)
	c.emit()

	c = newHostCase(t, "stop", "fencing-during-construction-is-not-overwritten", "TestAA17StopFencingDuringConstructionIsNotOverwrittenByRunning", "the factory calls Stop with an expired context", "Start")
	rig = aa17NewRig()
	expired, cancel = context.WithCancel(ctx)
	cancel()
	var inner error
	rig.onNew = func(*Session) { inner = rig.host.Stop(expired) }
	host = New(rig.config())
	rig.host = host
	c.tr.call("Start", host.Start(ctx), host, rig)
	c.tr.add("Stop issued by the factory", kv{"outcome", outcomeOf(inner)})
	c.emit()

	c = newHostCase(t, "stop", "concurrent-start-and-stop", "TestAA17ConcurrentStartAndStopShareTheFenceUnderTheLock", "Start", "eight concurrent Start and eight concurrent Stop calls", "Stop")
	rig = aa17NewRig()
	host = New(rig.config())
	c.tr.call("Start", host.Start(ctx), host, rig)
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(2)
		go func() { defer wg.Done(); _ = host.Start(ctx) }()
		go func() { defer wg.Done(); _ = host.Stop(ctx) }()
	}
	wg.Wait()
	finalErr := host.Stop(ctx)
	s := host.Status()
	c.tr.add("final Stop", kv{"outcome", outcomeOf(finalErr)}, kv{"state", s.State}, kv{"owned_work", s.OwnedWork}, kv{"resources", s.Resources})
	c.emit()
}

var _ = strings.TrimSpace
