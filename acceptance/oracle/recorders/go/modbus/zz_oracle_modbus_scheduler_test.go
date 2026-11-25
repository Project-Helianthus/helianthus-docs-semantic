package modbus

import (
	"fmt"
	"math"
	"testing"
)

const oracleSchedulerEndpoint = "tcp://scheduler-endpoint.invalid:502"

type oracleRig struct {
	t         *testing.T
	scheduler *EndpointScheduler
	groups    map[uint64]*CoalescedRead
	last      uint64
}

func oracleLimitsMap(limits SchedulerLimits) map[string]any {
	return map[string]any{
		"max_active_admission_keys":          limits.MaxActiveAdmissionKeys,
		"protected_slots_per_key":            limits.ProtectedSlotsPerKey,
		"shared_burst_slots":                 limits.SharedBurstSlots,
		"total_queued":                       limits.TotalQueued,
		"max_queued_per_key":                 limits.MaxQueuedPerKey,
		"max_queued_per_authorization_scope": limits.MaxQueuedPerAuthorizationScope,
		"max_coalesced_dependents_per_key":   limits.MaxCoalescedDependentsPerKey,
		"max_retry_attempts":                 limits.MaxRetryAttempts,
		"max_in_flight_requests":             limits.MaxInFlightRequests,
	}
}

func oracleLimitsFrom(values map[string]any) SchedulerLimits {
	return SchedulerLimits{
		MaxActiveAdmissionKeys:         int(oracleInt(values["max_active_admission_keys"])),
		ProtectedSlotsPerKey:           int(oracleInt(values["protected_slots_per_key"])),
		SharedBurstSlots:               int(oracleInt(values["shared_burst_slots"])),
		TotalQueued:                    int(oracleInt(values["total_queued"])),
		MaxQueuedPerKey:                int(oracleInt(values["max_queued_per_key"])),
		MaxQueuedPerAuthorizationScope: int(oracleInt(values["max_queued_per_authorization_scope"])),
		MaxCoalescedDependentsPerKey:   int(oracleInt(values["max_coalesced_dependents_per_key"])),
		MaxRetryAttempts:               int(oracleInt(values["max_retry_attempts"])),
		MaxInFlightRequests:            int(oracleInt(values["max_in_flight_requests"])),
	}
}

var oracleTestLimits = SchedulerLimits{
	MaxActiveAdmissionKeys:         3,
	ProtectedSlotsPerKey:           2,
	SharedBurstSlots:               2,
	TotalQueued:                    8,
	MaxQueuedPerKey:                4,
	MaxQueuedPerAuthorizationScope: 8,
	MaxCoalescedDependentsPerKey:   4,
	MaxRetryAttempts:               2,
	MaxInFlightRequests:            4,
}

func opEnqueue(id uint64, scope string, unit byte, deadline int64) map[string]any {
	return map[string]any{"op": "enqueue", "request_id": id, "scope": scope, "unit": int(unit), "deadline_offset": deadline}
}

func opAdmit(id uint64, scope string, unit byte, deadline int64, weight int) map[string]any {
	return map[string]any{"op": "admit_weighted", "request_id": id, "scope": scope, "unit": int(unit), "deadline_offset": deadline, "weight": weight}
}

func opDispatch(now int64) map[string]any { return map[string]any{"op": "dispatch", "now": now} }

func opID(name string, id uint64) map[string]any {
	return map[string]any{"op": name, "request_id": id}
}

func opKey(name string, scope string, unit byte) map[string]any {
	return map[string]any{"op": name, "scope": scope, "unit": int(unit)}
}

func opAccounting(scope string, unit byte, queued int, dependents int) map[string]any {
	return map[string]any{"op": "set_key_accounting", "scope": scope, "unit": int(unit), "queued": queued, "dependents": dependents}
}

func opNew(limits SchedulerLimits) map[string]any {
	return map[string]any{"op": "new_scheduler", "limits": oracleLimitsMap(limits)}
}

func oracleIntent(view uint64, offset uint16, quantity uint16, identity uint64, unit int) map[string]any {
	return map[string]any{"logical_view_id": view, "offset": int(offset), "quantity": int(quantity), "deadline_identity": identity, "unit_after_build": unit}
}

func opCoalesce(id uint64, scope string, unit byte, deadline int64, intents ...map[string]any) map[string]any {
	list := make([]any, 0, len(intents))
	for _, intent := range intents {
		list = append(list, intent)
	}
	return map[string]any{"op": "schedule_coalesced", "request_id": id, "scope": scope, "unit": int(unit), "deadline_offset": deadline, "endpoint": oracleSchedulerEndpoint, "transport": "tcp", "transport_generation": 7, "intent_unit": 1, "intent_scope": "site-a", "poll_generation": 11, "function": "read_holding_registers", "intents": list}
}

func (rig *oracleRig) state() []int {
	snapshot := rig.scheduler.resourceSnapshot()
	return []int{snapshot.queuedRequests, snapshot.inFlightRequests, snapshot.activeAdmissionKeys, snapshot.coalescedDependents, rig.scheduler.OrderMetadataSize()}
}

func (rig *oracleRig) request(op map[string]any) ScheduledRequest {
	return ScheduledRequest{
		RequestID:      uint64(oracleInt(op["request_id"])),
		Key:            AdmissionKey{AuthorizationScope: op["scope"].(string), UnitID: byte(oracleInt(op["unit"]))},
		DeadlineOffset: oracleInt(op["deadline_offset"]),
	}
}

func oracleRequestRecord(request ScheduledRequest) map[string]any {
	return map[string]any{"request_id": request.RequestID, "scope": request.Key.AuthorizationScope, "unit": int(request.Key.UnitID), "deadline_offset": request.DeadlineOffset}
}

func (rig *oracleRig) intents(op map[string]any) []ReadIntent {
	rig.t.Helper()
	var intents []ReadIntent
	for _, item := range op["intents"].([]any) {
		spec := item.(map[string]any)
		request, err := NewReadRegistersRequest(FunctionReadHoldingRegisters, uint16(oracleInt(spec["offset"])), uint16(oracleInt(spec["quantity"])))
		if err != nil {
			rig.t.Fatal(err)
		}
		intent, err := NewReadIntent(ReadIntentSpec{
			LogicalViewID:       uint64(oracleInt(spec["logical_view_id"])),
			Endpoint:            op["endpoint"].(string),
			Transport:           TransportTCP,
			TransportGeneration: uint64(oracleInt(op["transport_generation"])),
			UnitID:              byte(oracleInt(op["intent_unit"])),
			AuthorizationScope:  op["intent_scope"].(string),
			PollGeneration:      uint64(oracleInt(op["poll_generation"])),
			DeadlineIdentity:    uint64(oracleInt(spec["deadline_identity"])),
			Request:             request,
		})
		if err != nil {
			rig.t.Fatal(err)
		}
		if unit := byte(oracleInt(spec["unit_after_build"])); unit != 0 {
			intent.spec.UnitID = unit
		}
		intents = append(intents, intent)
	}
	return intents
}

func oracleStates(states map[uint64]DependentTerminalState) map[string]any {
	out := map[string]any{}
	for view, state := range states {
		out[fmt.Sprint(view)] = string(state)
	}
	return out
}

func (rig *oracleRig) apply(op map[string]any) map[string]any {
	rig.t.Helper()
	result := map[string]any{"op": op["op"]}
	switch op["op"] {
	case "new_scheduler":
		scheduler, err := newEndpointScheduler(oracleLimitsFrom(op["limits"].(map[string]any)))
		result["error"] = oracleErr(err)
		if err == nil {
			rig.scheduler = scheduler
			rig.groups = map[uint64]*CoalescedRead{}
		}
		return result
	case "enqueue":
		result["error"] = oracleErr(rig.scheduler.Enqueue(rig.request(op)))
	case "admit_weighted":
		rig.scheduler.mu.Lock()
		err := rig.scheduler.enqueueLocked(rig.request(op), nil, int(oracleInt(op["weight"])))
		rig.scheduler.mu.Unlock()
		result["error"] = oracleErr(err)
	case "dispatch":
		request, ok := rig.scheduler.Dispatch(oracleInt(op["now"]))
		result["dispatched"] = ok
		if ok {
			rig.last = request.RequestID
			result["request"] = oracleRequestRecord(request)
		}
	case "complete":
		result["error"] = oracleErr(rig.scheduler.Complete(uint64(oracleInt(op["request_id"]))))
	case "complete_last_dispatch":
		result["request_id"] = rig.last
		result["error"] = oracleErr(rig.scheduler.Complete(rig.last))
	case "retry":
		result["error"] = oracleErr(rig.scheduler.Retry(uint64(oracleInt(op["request_id"]))))
	case "cancel_queued":
		result["cancelled"] = rig.scheduler.CancelQueued(uint64(oracleInt(op["request_id"])))
	case "attach_dependent":
		result["error"] = oracleErr(rig.scheduler.attachDependent(AdmissionKey{AuthorizationScope: op["scope"].(string), UnitID: byte(oracleInt(op["unit"]))}))
	case "detach_dependent":
		result["error"] = oracleErr(rig.scheduler.detachDependent(AdmissionKey{AuthorizationScope: op["scope"].(string), UnitID: byte(oracleInt(op["unit"]))}))
	case "set_key_accounting":
		key := AdmissionKey{AuthorizationScope: op["scope"].(string), UnitID: byte(oracleInt(op["unit"]))}
		rig.scheduler.mu.Lock()
		state := rig.scheduler.keys[key]
		state.queued = int(oracleInt(op["queued"]))
		state.dependents = int(oracleInt(op["dependents"]))
		rig.scheduler.mu.Unlock()
	case "schedule_coalesced":
		group, err := rig.scheduler.ScheduleCoalesced(rig.request(op), rig.intents(op))
		result["error"] = oracleErr(err)
		result["group_returned"] = group != nil
		if group != nil {
			rig.groups[uint64(oracleInt(op["request_id"]))] = group
		}
	case "coalesced_group":
		got, ok := rig.scheduler.CoalescedGroup(uint64(oracleInt(op["request_id"])))
		result["found"] = ok
		result["same_group"] = ok && got == rig.groups[uint64(oracleInt(op["request_id"]))]
	case "require_coalesced_dispatch":
		result["error"] = oracleErr(rig.scheduler.RequireCoalescedDispatch(rig.groups[uint64(oracleInt(op["request_id"]))]))
	case "retry_coalesced":
		result["error"] = oracleErr(rig.scheduler.RetryCoalesced(rig.groups[uint64(oracleInt(op["request_id"]))]))
	case "finish_coalesced":
		result["error"] = oracleErr(rig.scheduler.FinishCoalesced(rig.groups[uint64(oracleInt(op["request_id"]))]))
	case "group_fail_transport":
		result["error"] = oracleErr(rig.groups[uint64(oracleInt(op["request_id"]))].FailTransport())
	case "group_cancel":
		_, err := rig.groups[uint64(oracleInt(op["request_id"]))].Cancel(uint64(oracleInt(op["logical_view_id"])))
		result["error"] = oracleErr(err)
	case "group_states":
		result["states"] = oracleStates(rig.groups[uint64(oracleInt(op["request_id"]))].DependentStates())
	case "internals":
		scheduler := rig.scheduler
		scheduler.mu.Lock()
		result["entries"] = len(scheduler.entries)
		result["coalesced"] = len(scheduler.coalesced)
		result["keys"] = len(scheduler.keys)
		result["scope_order"] = len(scheduler.scopeOrder)
		result["unit_order"] = len(scheduler.unitOrder)
		result["unit_cursor"] = len(scheduler.unitCursor)
		result["scope_cursor"] = scheduler.scopeCursor
		result["in_flight"] = scheduler.inFlight
		scheduler.mu.Unlock()
	case "key_queued":
		key := AdmissionKey{AuthorizationScope: op["scope"].(string), UnitID: byte(oracleInt(op["unit"]))}
		rig.scheduler.mu.Lock()
		state := rig.scheduler.keys[key]
		result["live"] = state != nil
		if state != nil {
			result["queued"] = state.queued
		}
		rig.scheduler.mu.Unlock()
	default:
		rig.t.Fatalf("unknown operation %v", op["op"])
	}
	result["state"] = rig.state()
	return result
}

func oracleRunScript(t *testing.T, limits SchedulerLimits, script []map[string]any) (*oracleRig, []any) {
	t.Helper()
	scheduler, err := newEndpointScheduler(limits)
	if err != nil {
		t.Fatal(err)
	}
	rig := &oracleRig{t: t, scheduler: scheduler, groups: map[uint64]*CoalescedRead{}}
	results := make([]any, 0, len(script))
	for _, op := range script {
		results = append(results, rig.apply(op))
	}
	return rig, results
}

func oracleSchedulerCase(t *testing.T, name string, stimulus string, limits SchedulerLimits, script []map[string]any) {
	t.Helper()
	rig, results := oracleRunScript(t, limits, script)
	ops := make([]any, 0, len(script))
	for _, op := range script {
		ops = append(ops, op)
	}
	oracleWrite(t, "scheduler", name, oracleCase{
		Component: "modbus-tcp-scheduler",
		Source:    "tcp_scheduler.go",
		Stimulus:  stimulus,
		Input: oracleInput{
			Qualifiers: map[string]any{"limits": oracleLimitsMap(limits), "state_vector": []string{"queued_requests", "in_flight_requests", "active_admission_keys", "coalesced_dependents", "order_metadata_size"}},
			Clock:      map[string]any{"unit": "scheduler offset", "note": "the scheduler has no clock of its own; every dispatch carries its offset"},
			State:      map[string]any{"script": ops},
		},
		Output: oracleOutput{
			Decisions: results,
			Counters:  map[string]any{"final_state": rig.state()},
		},
	})
}

func oracleRoundRobinScript(scopes []string, units byte, prefix []uint64, cancel []uint64, readd int) []map[string]any {
	var script []map[string]any
	var keys []AdmissionKey
	for _, scope := range scopes {
		for unit := byte(1); unit <= units; unit++ {
			key := AdmissionKey{AuthorizationScope: scope, UnitID: unit}
			id := uint64(11 + 2*len(keys))
			keys = append(keys, key)
			script = append(script, opEnqueue(id, scope, unit, 1000+int64(id)), opEnqueue(id+1, scope, unit, 1000+int64(id+1)))
		}
	}
	for range prefix {
		script = append(script, opDispatch(10))
		script = append(script, map[string]any{"op": "complete_last_dispatch"})
	}
	for _, id := range cancel {
		script = append(script, opID("cancel_queued", id))
	}
	if readd >= 0 {
		for _, id := range []uint64{27, 28} {
			script = append(script, opEnqueue(id, keys[readd].AuthorizationScope, keys[readd].UnitID, 1000+int64(id)))
		}
	}
	return script
}

func oracleRecordScheduler(t *testing.T) {
	t.Helper()
	oracleRecordSchedulerLimits(t)
	oracleRecordSchedulerAdmission(t)
	oracleRecordSchedulerOrder(t)
	oracleRecordSchedulerCoalesced(t)
	oracleRecordSchedulerCursors(t)
	oracleRecordSchedulerDeadlineRelease(t)
}

func oracleRecordSchedulerLimits(t *testing.T) {
	t.Helper()
	valid := SchedulerLimits{
		MaxActiveAdmissionKeys:         2,
		ProtectedSlotsPerKey:           2,
		SharedBurstSlots:               1,
		TotalQueued:                    5,
		MaxQueuedPerKey:                3,
		MaxQueuedPerAuthorizationScope: 5,
		MaxCoalescedDependentsPerKey:   2,
		MaxRetryAttempts:               2,
		MaxInFlightRequests:            2,
	}
	cases := []struct {
		name   string
		change func(*SchedulerLimits)
	}{
		{"valid", func(*SchedulerLimits) {}},
		{"zero", func(l *SchedulerLimits) { l.MaxActiveAdmissionKeys = 0 }},
		{"negative", func(l *SchedulerLimits) { l.SharedBurstSlots = -1 }},
		{"multiplication-overflow", func(l *SchedulerLimits) {
			l.MaxActiveAdmissionKeys = math.MaxInt
			l.ProtectedSlotsPerKey = 2
			l.TotalQueued = math.MaxInt
		}},
		{"protected-capacity-absent", func(l *SchedulerLimits) { l.TotalQueued = 4 }},
		{"per-key-below-protected", func(l *SchedulerLimits) { l.MaxQueuedPerKey = 1 }},
		{"per-key-above-total", func(l *SchedulerLimits) { l.MaxQueuedPerKey = 6 }},
		{"scope-below-protected", func(l *SchedulerLimits) { l.MaxQueuedPerAuthorizationScope = 1 }},
		{"dependent-below-protected", func(l *SchedulerLimits) { l.MaxCoalescedDependentsPerKey = 1 }},
		{"scope-cannot-protect-all-keys", func(l *SchedulerLimits) { l.MaxQueuedPerAuthorizationScope = 3 }},
		{"retry-attempts-zero", func(l *SchedulerLimits) { l.MaxRetryAttempts = 0 }},
		{"in-flight-zero", func(l *SchedulerLimits) { l.MaxInFlightRequests = 0 }},
	}
	for _, tc := range cases {
		limits := valid
		tc.change(&limits)
		scheduler, err := newEndpointScheduler(limits)
		oracleWrite(t, "scheduler", "limits-"+tc.name, oracleCase{
			Component: "modbus-tcp-scheduler",
			Source:    "tcp_scheduler.go",
			Stimulus:  "TestSchedulerRejectsInvalidOverflowingAndInconsistentLimits/" + tc.name,
			Input: oracleInput{
				Qualifiers: map[string]any{"mutation": tc.name, "limits": oracleLimitsMap(limits)},
			},
			Output: oracleOutput{
				Decisions: []any{map[string]any{"error": oracleErr(err), "scheduler_returned": scheduler != nil}},
			},
		})
	}
}

func oracleRecordSchedulerAdmission(t *testing.T) {
	t.Helper()
	oracleSchedulerCase(t, "admission-arithmetic-fails-closed", "TestSchedulerAdmissionArithmeticFailsClosed", oracleTestLimits, []map[string]any{
		opEnqueue(1, "a", 1, 100),
		opAccounting("a", 1, math.MaxInt, 1),
		opEnqueue(2, "a", 1, 100),
		opAccounting("a", 1, oracleTestLimits.MaxQueuedPerKey+1, 0),
		opEnqueue(3, "a", 1, 100),
	})
	spare := SchedulerLimits{MaxActiveAdmissionKeys: 2, ProtectedSlotsPerKey: 2, SharedBurstSlots: 1, TotalQueued: 5, MaxQueuedPerKey: 3, MaxQueuedPerAuthorizationScope: 5, MaxCoalescedDependentsPerKey: 2, MaxRetryAttempts: 2, MaxInFlightRequests: 2}
	oracleSchedulerCase(t, "capacity-kept-for-inactive-keys", "TestSchedulerPreservesCapacityForInactiveAdmissionKeys", spare, []map[string]any{
		opEnqueue(1, "a", 1, 100), opEnqueue(2, "a", 1, 100), opEnqueue(3, "a", 1, 100),
		opEnqueue(4, "a", 1, 100),
		opEnqueue(5, "b", 2, 100), opEnqueue(6, "b", 2, 100),
		opEnqueue(7, "c", 3, 100),
	})
	deficit := SchedulerLimits{MaxActiveAdmissionKeys: 2, ProtectedSlotsPerKey: 2, SharedBurstSlots: 1, TotalQueued: 5, MaxQueuedPerKey: 5, MaxQueuedPerAuthorizationScope: 5, MaxCoalescedDependentsPerKey: 2, MaxRetryAttempts: 1, MaxInFlightRequests: 2}
	oracleSchedulerCase(t, "protected-deficit-for-active-keys", "TestSchedulerPreservesProtectedDeficitForActiveKeys", deficit, []map[string]any{
		opEnqueue(1, "a", 1, 100), opEnqueue(2, "a", 1, 100), opEnqueue(3, "a", 1, 100),
		opEnqueue(4, "b", 2, 100),
		opEnqueue(5, "a", 1, 100),
		opEnqueue(6, "b", 2, 100),
	})
	single := SchedulerLimits{MaxActiveAdmissionKeys: 1, ProtectedSlotsPerKey: 1, SharedBurstSlots: 1, TotalQueued: 2, MaxQueuedPerKey: 2, MaxQueuedPerAuthorizationScope: 2, MaxCoalescedDependentsPerKey: 2, MaxRetryAttempts: 2, MaxInFlightRequests: 1}
	oracleSchedulerCase(t, "key-active-until-queue-inflight-and-dependents-empty", "TestAdmissionKeyStaysActiveUntilQueueInflightAndDependentsEmpty", single, []map[string]any{
		opEnqueue(1, "a", 1, 100),
		opKey("attach_dependent", "a", 1),
		opDispatch(0),
		opEnqueue(2, "b", 2, 100),
		opID("complete", 1),
		opEnqueue(2, "b", 2, 100),
		opKey("detach_dependent", "a", 1),
		opEnqueue(2, "b", 2, 100),
	})
	oracleSchedulerCase(t, "retry-limit-fails-and-releases-request", "TestSchedulerRetryLimitFailsAndReleasesRequest", oracleTestLimits, []map[string]any{
		opEnqueue(1, "a", 1, 100),
		opDispatch(0), opID("retry", 1),
		opDispatch(0), opID("retry", 1),
		opDispatch(0), opID("retry", 1),
		opEnqueue(2, "b", 2, 100),
	})
	oracleSchedulerCase(t, "retry-admission-failure-releases-in-flight-slot", "TestSchedulerRetryAdmissionFailureReleasesInFlightSlot", single, []map[string]any{
		opEnqueue(1, "a", 1, 100), opEnqueue(2, "a", 1, 100),
		opDispatch(0),
		opEnqueue(3, "a", 1, 100),
		opID("retry", 1),
		opDispatch(0),
	})
	oracleSchedulerCase(t, "in-flight-bound", "TestSchedulerBoundsInflightRequests", oracleTestLimits, []map[string]any{
		opEnqueue(1, "a", 1, 100), opEnqueue(2, "a", 1, 100), opEnqueue(3, "a", 1, 100), opEnqueue(4, "a", 1, 100),
		opDispatch(0), opDispatch(0), opDispatch(0), opDispatch(0),
		opEnqueue(5, "a", 1, 100),
		opDispatch(0),
		opID("complete", 1),
		opDispatch(0),
	})
}

func oracleRecordSchedulerOrder(t *testing.T) {
	t.Helper()
	oracleSchedulerCase(t, "scope-then-unit-round-robin-fifo", "TestSchedulerIsScopeThenUnitRoundRobinAndFIFOWithinKey", oracleTestLimits, []map[string]any{
		opEnqueue(1, "a", 1, 100), opEnqueue(2, "a", 1, 100), opEnqueue(3, "a", 2, 100),
		opEnqueue(4, "a", 2, 100), opEnqueue(5, "b", 1, 100), opEnqueue(6, "b", 1, 100),
		opDispatch(0), opID("complete", 1),
		opDispatch(0), opID("complete", 5),
		opDispatch(0), opID("complete", 3),
		opDispatch(0), opID("complete", 6),
		opDispatch(0), opID("complete", 2),
		opDispatch(0), opID("complete", 4),
	})
	oracleSchedulerCase(t, "unit-zero-and-unit-one-keys-distinct", "TestSchedulerKeepsTCPUnitZeroAndUnitOneAdmissionKeysDistinct", oracleTestLimits, []map[string]any{
		opEnqueue(1, "site", 0, 100), opEnqueue(2, "site", 1, 100),
		opDispatch(0), opDispatch(0),
	})
	oracleSchedulerCase(t, "expiry-cancellation-retry-at-tail", "TestSchedulerSkipsExpirySupportsCancellationAndRetriesAtTail", oracleTestLimits, []map[string]any{
		opEnqueue(1, "a", 1, 5), opEnqueue(2, "a", 1, 100), opEnqueue(3, "a", 1, 100),
		opID("cancel_queued", 3),
		opDispatch(5),
		opEnqueue(4, "a", 1, 100),
		opID("retry", 2),
		opDispatch(5),
		opID("complete", 4),
		opDispatch(5),
	})
	removal := func(removedScope string, removedUnit byte, peerScope string) []map[string]any {
		script := []map[string]any{
			opEnqueue(1, "a", 1, 100), opEnqueue(2, "a", 1, 100),
		}
		if peerScope == "b" {
			script = append(script, opEnqueue(3, "b", 1, 100))
		} else {
			script = append(script, opEnqueue(3, "a", 2, 100))
		}
		script = append(script, opDispatch(0), opID("complete", 1))
		for id := uint64(4); id < 68; id++ {
			script = append(script, opEnqueue(id, removedScope, removedUnit, 100), opID("cancel_queued", id))
		}
		script = append(script, opDispatch(0))
		return script
	}
	oracleSchedulerCase(t, "scope-removal-keeps-next-peer", "TestSchedulerScopeRemovalPreservesNextRoundRobinPeer", oracleTestLimits, removal("c", 1, "b"))
	oracleSchedulerCase(t, "unit-removal-keeps-next-peer", "TestSchedulerUnitRemovalPreservesNextRoundRobinPeer", oracleTestLimits, removal("a", 3, "a"))
	pruning := SchedulerLimits{MaxActiveAdmissionKeys: 1, ProtectedSlotsPerKey: 1, SharedBurstSlots: 1, TotalQueued: 2, MaxQueuedPerKey: 2, MaxQueuedPerAuthorizationScope: 2, MaxCoalescedDependentsPerKey: 1, MaxRetryAttempts: 1, MaxInFlightRequests: 1}
	var script []map[string]any
	for id := uint64(1); id <= 100; id++ {
		script = append(script, opEnqueue(id, string(rune('a'+id)), 1, 100), opDispatch(0), opID("complete", id))
	}
	oracleSchedulerCase(t, "historical-scope-and-unit-metadata-pruned", "TestSchedulerPrunesHistoricalScopeAndUnitMetadata", pruning, script)
}

func oracleRecordSchedulerCoalesced(t *testing.T) {
	t.Helper()
	capacity := SchedulerLimits{MaxActiveAdmissionKeys: 2, ProtectedSlotsPerKey: 1, SharedBurstSlots: 2, TotalQueued: 4, MaxQueuedPerKey: 4, MaxQueuedPerAuthorizationScope: 4, MaxCoalescedDependentsPerKey: 4, MaxRetryAttempts: 1, MaxInFlightRequests: 1}
	four := []map[string]any{oracleIntent(1, 10, 4, 13, 0), oracleIntent(2, 11, 4, 13, 0), oracleIntent(3, 12, 4, 13, 0), oracleIntent(4, 13, 4, 13, 0)}
	oracleSchedulerCase(t, "coalesced-dependents-bypass-protected-capacity", "TestCoalescedDependentsConsumeTotalAndScopeAdmission/four-dependents", capacity, []map[string]any{
		opCoalesce(100, "site-a", 1, 50, four...),
	})
	oracleSchedulerCase(t, "coalesced-dependents-consume-total-and-scope", "TestCoalescedDependentsConsumeTotalAndScopeAdmission/second-group", capacity, []map[string]any{
		opCoalesce(100, "site-a", 1, 50, four[:3]...),
		opCoalesce(101, "site-a", 2, 50, oracleIntent(5, 20, 2, 13, 2), oracleIntent(6, 21, 2, 13, 2)),
	})
	one := oracleIntent(11, 10, 4, math.MaxUint64, 0)
	oracleSchedulerCase(t, "coalesced-requires-explicit-finite-deadline", "TestScheduleCoalescedRequiresExplicitFiniteDeadlineOffset", oracleTestLimits, []map[string]any{
		opCoalesce(100, "site-a", 1, 0, one),
		opNew(oracleTestLimits),
		opCoalesce(100, "site-a", 1, -1, one),
		opNew(oracleTestLimits),
		opCoalesce(100, "site-a", 1, 50, one),
		opDispatch(49),
		opID("require_coalesced_dispatch", 100),
	})
	lifecycle := []map[string]any{
		opCoalesce(100, "site-a", 1, 50, oracleIntent(11, 10, 4, 13, 0), oracleIntent(12, 11, 4, 13, 0)),
		opEnqueue(200, "site-b", 2, 50),
		opID("require_coalesced_dispatch", 100),
		opDispatch(0),
		opID("coalesced_group", 100),
		opID("require_coalesced_dispatch", 100),
		opDispatch(0),
		opID("retry_coalesced", 100),
		opID("require_coalesced_dispatch", 100),
		opDispatch(0),
		opID("complete", 200),
		opDispatch(0),
		opID("group_fail_transport", 100),
		opID("finish_coalesced", 100),
	}
	oracleSchedulerCase(t, "coalesced-physical-read-dispatch-lifecycle", "TestCoalescedPhysicalReadUsesSchedulerDispatchLifecycle", capacity, lifecycle)
	oracleSchedulerCase(t, "coalesced-final-cancellation-releases-token", "TestFinalQueuedCoalescedCancellationReleasesDispatchToken", oracleTestLimits, []map[string]any{
		opCoalesce(100, "site-a", 1, 50, oracleIntent(11, 10, 4, 13, 0), oracleIntent(12, 11, 4, 13, 0)),
		{"op": "group_cancel", "request_id": uint64(100), "logical_view_id": uint64(11)},
		{"op": "group_cancel", "request_id": uint64(100), "logical_view_id": uint64(12)},
		opID("finish_coalesced", 100),
		opID("group_states", 100),
		opDispatch(0),
	})
	oracleSchedulerCase(t, "coalesced-physical-read-expires-without-write", "TestCoalescedPhysicalReadExpiresWithoutTransportWrite", oracleTestLimits, []map[string]any{
		opCoalesce(100, "site-a", 1, 10, oracleIntent(11, 10, 4, math.MaxUint64, 0), oracleIntent(12, 11, 4, math.MaxUint64, 0)),
		opDispatch(10),
		opID("group_states", 100),
		opID("coalesced_group", 100),
	})
}

func oracleRecordSchedulerCursors(t *testing.T) {
	t.Helper()
	limits := SchedulerLimits{MaxActiveAdmissionKeys: 3, ProtectedSlotsPerKey: 1, SharedBurstSlots: 5, TotalQueued: 8, MaxQueuedPerKey: 2, MaxQueuedPerAuthorizationScope: 8, MaxCoalescedDependentsPerKey: 1, MaxRetryAttempts: 1, MaxInFlightRequests: 1}
	removal := []struct {
		name   string
		scopes []string
		units  byte
		prefix int
		cancel []uint64
		readd  int
		drain  int
	}{
		{"unit-before-cursor", []string{"a"}, 3, 2, []uint64{12}, -1, 3},
		{"unit-at-cursor", []string{"a"}, 3, 1, []uint64{13, 14}, -1, 3},
		{"unit-after-cursor", []string{"a"}, 3, 1, []uint64{15, 16}, -1, 3},
		{"last-scope-at-cursor-readded", []string{"a", "b", "c"}, 1, 2, []uint64{15, 16}, 2, 4},
		{"last-unit-at-cursor-readded", []string{"a"}, 2, 1, []uint64{13, 14}, 1, 3},
	}
	for _, tc := range removal {
		script := oracleRoundRobinScript(tc.scopes, tc.units, make([]uint64, tc.prefix), tc.cancel, tc.readd)
		for range tc.drain {
			script = append(script, opDispatch(10), map[string]any{"op": "complete_last_dispatch"})
		}
		script = append(script, opDispatch(10), map[string]any{"op": "internals"})
		oracleSchedulerCase(t, "cursor-removal-"+tc.name, "TestS21SchedulerCursorRemovalOrder/"+tc.name, limits, script)
	}
	churn := SchedulerLimits{MaxActiveAdmissionKeys: 12, ProtectedSlotsPerKey: 1, SharedBurstSlots: 52, TotalQueued: 64, MaxQueuedPerKey: 8, MaxQueuedPerAuthorizationScope: 64, MaxCoalescedDependentsPerKey: 8, MaxRetryAttempts: 2, MaxInFlightRequests: 16}
	cases := []struct {
		name     string
		prefix   []int
		cancel   []uint64
		complete uint64
		readd    []int
		drain    int
	}{
		{"scope-before-cursor-completion", []int{11}, []uint64{12, 21, 22}, 11, []int{0, 1}, 12},
		{"scope-at-cursor-cancellation", []int{11}, []uint64{31, 32, 41, 42}, 0, []int{2, 3}, 11},
		{"scope-after-cursor-cancellation", []int{11}, []uint64{51, 52, 61, 62}, 0, []int{5, 4}, 11},
		{"unit-before-cursor-completion", []int{11}, []uint64{12}, 11, []int{0}, 12},
		{"unit-at-cursor-cancellation", nil, []uint64{11, 12}, 0, []int{0}, 12},
		{"unit-after-cursor-cancellation", nil, []uint64{21, 22}, 0, []int{1}, 12},
	}
	for _, tc := range cases {
		var script []map[string]any
		for cycle, scopes := range [][3]string{{"a", "b", "c"}, {"d", "e", "f"}} {
			base := uint64(cycle * 100)
			var keys []AdmissionKey
			for _, scope := range scopes {
				for unit := byte(1); unit <= 2; unit++ {
					keys = append(keys, AdmissionKey{AuthorizationScope: scope, UnitID: unit})
				}
			}
			for index, key := range keys {
				for _, id := range []uint64{uint64(index*10 + 11), uint64(index*10 + 12)} {
					script = append(script, opEnqueue(base+id, key.AuthorizationScope, key.UnitID, 1000+int64(id)))
				}
			}
			script = append(script, map[string]any{"op": "internals"})
			for _, id := range tc.prefix {
				script = append(script, opDispatch(10))
				if uint64(id) != tc.complete {
					script = append(script, map[string]any{"op": "complete_last_dispatch"})
				}
			}
			for _, id := range tc.cancel {
				script = append(script, opID("cancel_queued", base+id))
			}
			if tc.complete != 0 {
				script = append(script, opID("complete", base+tc.complete))
			}
			for index, keyIndex := range tc.readd {
				for _, id := range []uint64{uint64(71 + index*10), uint64(72 + index*10)} {
					script = append(script, opEnqueue(base+id, keys[keyIndex].AuthorizationScope, keys[keyIndex].UnitID, 1000+int64(id)))
				}
			}
			for range tc.drain {
				script = append(script, opDispatch(10), map[string]any{"op": "complete_last_dispatch"})
			}
			script = append(script, opDispatch(10), map[string]any{"op": "internals"})
		}
		oracleSchedulerCase(t, "cursor-churn-"+tc.name, "TestS21SchedulerCursorChurn/"+tc.name, churn, script)
	}
}

func oracleRecordSchedulerDeadlineRelease(t *testing.T) {
	t.Helper()
	limits := SchedulerLimits{MaxActiveAdmissionKeys: 2, ProtectedSlotsPerKey: 1, SharedBurstSlots: 1, TotalQueued: 3, MaxQueuedPerKey: 2, MaxQueuedPerAuthorizationScope: 3, MaxCoalescedDependentsPerKey: 1, MaxRetryAttempts: 1, MaxInFlightRequests: 2}
	peers := []struct {
		name  string
		scope string
		unit  byte
	}{{"scope-only", "beta", 1}, {"unit-only", "alpha", 2}, {"scope-and-unit", "beta", 2}}
	for _, peer := range peers {
		for _, offset := range []struct {
			name string
			now  int64
		}{{"before-deadline", 9}, {"at-deadline", 10}} {
			script := []map[string]any{
				opAdmit(1, "alpha", 1, 10, 2),
				opAdmit(2, peer.scope, peer.unit, 20, 1),
				opKey("key_queued", "alpha", 1),
				opKey("key_queued", peer.scope, peer.unit),
				{"op": "internals"},
				opEnqueue(3, peer.scope, peer.unit, 20),
				opDispatch(offset.now),
				opKey("key_queued", "alpha", 1),
				{"op": "internals"},
				opID("complete", 1),
				opKey("key_queued", "alpha", 1),
				{"op": "internals"},
				opAdmit(1, "gamma", 3, 20, 2),
				opKey("key_queued", "gamma", 3),
				{"op": "internals"},
			}
			if offset.now == 9 {
				script = append(script, opEnqueue(3, peer.scope, peer.unit, 20), opDispatch(offset.now))
			}
			script = append(script,
				opAdmit(3, peer.scope, peer.unit, 20, 2),
				opEnqueue(3, peer.scope, peer.unit, 20),
				opID("complete", 2),
				opDispatch(offset.now), map[string]any{"op": "complete_last_dispatch"},
				opDispatch(offset.now), map[string]any{"op": "complete_last_dispatch"},
				opDispatch(offset.now),
				map[string]any{"op": "internals"},
			)
			oracleSchedulerCase(t, "deadline-equality-"+peer.name+"-"+offset.name, "TestSchedulerDeadlineEqualityReleasesQueuedWeight/"+peer.name+"/"+offset.name, limits, script)
		}
	}
}
