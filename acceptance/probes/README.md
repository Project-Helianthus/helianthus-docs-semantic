---
status: "Independent probes of the merged SemReg driver contract. They compile against that module and assert only behavior its exported API implements."
---

# SemReg contract probes

These probes consume `github.com/Project-Helianthus/helianthus-semreg` `v0.0.0-20261124100158-93b56d48797e`, package `semreg/v1/driver`, from `acceptance/go.mod`. The module line has no `replace`. No probe imports a gateway package. `GOWORK=off` keeps the acceptance module off any local workspace.

The merged driver package exports records, `Validate` methods and the host, session, input and output interfaces. It exports no session constructor, retry normalizer, transport planner, remote factory, operation router or resource allocator. Where a later row needs one of those, this page names the missing operation and the owning acceptance row. The probe does not assert that row.

Build and test from `acceptance/`:

```sh
GOWORK=off go build ./probes/...
GOWORK=off go vet ./probes/...
GOWORK=off go test -count=1 ./probes/...
```

## Host

`probes/host` composes two factories. It returns the first handled `EarlyDispatcher` result and does not plan when that happens. A factory that does not implement `EarlyDispatcher` is not called for early dispatch. `Plan` receives that instance's `Config`, including its own `SecretRef`. Returned plans are validated and started, each with the session the caller opens. `driver.Descriptor.Validate` accepts a claimed composition with module and version, accepts `not_composed` with neither, and rejects a missing module, a missing version, a `not_composed` row that carries a module, and `tested_on_hardware` without a hardware-test evidence entry.

| Asserted | Owning row |
| --- | --- |
| Per-instance `SecretRef` handoff, and the plan JSON omits it | `K-CONFIG-HANDOFF` |
| Handled exit and handled error return before planning | `K-EARLY-HANDLED-EXIT`, `K-EARLY-HANDLED-ERROR` |
| An unrecognized command continues into planning | `K-EARLY-NOT-HANDLED` |
| A factory without the interface is not called | `K-EARLY-NONPARTICIPATING` |
| Claimed and `not_composed` family evidence | `K-COMPOSE-CLAIMED`, `K-COMPOSE-NOT-COMPOSED` |
| Missing module, missing version, `not_composed` carrying a module | `K-COMPOSE-MISSING-MODULE`, `K-COMPOSE-MISSING-VERSION`, `K-COMPOSE-NOT-COMPOSED-CARRIES` |
| `tested_on_hardware` needs a hardware-test record | `K-VERIFICATION-HARDWARE` |

`RetryPolicy` has no normalize function in the module. Rows `K-RETRY-ZERO`, `K-RETRY-BUDGET-NEGATIVE`, `K-RETRY-INITIAL-NONPOSITIVE`, `K-RETRY-MAX-BELOW-INITIAL`, `K-RETRY-JITTER-ZERO`, `K-RETRY-JITTER-NEGATIVE`, `K-RETRY-JITTER-ABOVE`, `K-RETRY-JITTER-KEPT`, `K-RETRY-PERSISTENT-ENABLED`, `K-RETRY-PERSISTENT-MAX-BELOW` and `K-RETRY-PERSISTENT-DISABLED` stay unasserted. `Calendar.BeginAcquisition` has no implementation, so `K-CALENDAR-GUARD` stays unasserted. The SemReg driver test names SS04 as the planner that rejects colliding transport claims; this module exports no such planner. `K-LINK-NODE-SLOT` stays unasserted: `TransportClaim.LinkNodeSlot` validates, and nothing here builds the durable key from that slot.

## Virtual

`probes/virtual` is a driver with zero transports. `Plan` rejects a transport operand, decodes its options operand strictly, and returns one `InstancePlan` with an empty transport list. `Construct` forms a `NodeKey` from the configured installation, driver kind, instance key and slot anchor, an `Origin` of kind `declared` with its evidence, and a `LinkClaim` whose endpoints use probe-literal resource ids. `Start` requires `Session.SemanticInput` and `Session.Publisher` and opens no bus.

`OriginDerived` validates and is a different kind from `OriginMeasured`. No presenter in this module shows a value, so the presentation half of `C-DERIVED` stays unasserted.

Unasserted, with the missing operation:

| Missing operation | Owning row |
| --- | --- |
| Path-node and legacy resource allocation | `I-ALLOC-LEGACY-SLOT`, `I-ALLOC-LEGACY-KEY`, `I-ALLOC-PATH-SLOT`, `I-ALLOC-PATH-KEY`, `I-ALLOC-INJECTIVE`, `I-ALLOC-VARY`, `I-ALLOC-DOMAIN` |
| Runtime overlay that retains a foreign-to-foreign link. The contract cites SS05 item 5. `publication_relations.go` does not export that overlay | `C-NO-TRANSPORT` overlay clause |
| Formula cycle walk. `Formula.Validate` checks the algorithm and that an input exists | `C-CYCLE` |
| Resolver of a foreign `InputRef` at an exact revision | `C-CROSS-ASSET` |
| Rejection of a reflected origin or loop | `C-LOOP` |

## Remote

`probes/remote` copies a validated `NodeRef` and a copy of its `Origin` evidence into a local record. Two bridges with one local id compare unequal. `NodeRef` has the fields `Bridge` and `ID`. `Changes.Validate` rejects a resync that also carries commits.

The module exports no remote factory. Authentication, one-cut paging, and the runtime that turns an expired resume position into a resync are absent. `C-REMOTE`, `C-COLLIDE`, `C-REMOTE-CUT`, `C-REMOTE-RESYNC`, `C-RESUME-ABA`, `C-ROUNDTRIP` and `C-NATIVE-RESUME` stay unasserted as runtime behavior. The pair and provenance copy is what this probe tests. GraphQL serialization is not in the module (`C-ROUNDTRIP`). Nothing returns `revision_conflict` from `Resume` (`C-NATIVE-RESUME`).

## Output

`probes/output` implements `SemanticOutput`. `StartOutput` calls `SemanticInput.Capture` with an empty `Filter`, validates the cut, and calls `ScopedOperations.Invoke` with the caller's `OperationRequest`. A zero `Timeout` still uses `Invoke`. `CompoundStep.Validate` rejects delivery, acknowledgement or readback on a step that was not attempted.

The test supplies the two interfaces. The module exports no `Session` that implements them, no operation router, and no summary-exclusion type. The output probe builds no `v1.Snapshot`, because a valid snapshot is a kernel document this gate does not assemble.

| Missing operation | Owning row |
| --- | --- |
| Router for `Invoke` deadline rules | `C-INVOKE-FINITE` |
| Router that refuses to serialize or replay `InvokeCallBound` | `C-INVOKE-CALLBOUND` |
| Production of `CompoundExecution` | `C-COMPOUND-PARTIAL` |
| `RegisterExecutor` lifetime. The contract cites SS08 item 5 | `C-EXECUTOR-REGISTER` |
| Donor snapshot left unchanged by a consumer. No valid snapshot is built here | `C-DONOR` |
| Session wiring of `RetrieveLens` and `SumMembers` | `C-LENS-SUM`, `C-LENS-PARTIAL`, `C-LENS-OUTSIDE` |

`graph.RetrieveLens` and `graph.SumMembers` exist on `semreg/v1/graph`. This gate does not call them through a driver session.

VirtualBus and Matter southbound are recorded in [strategy-receipt.md](../freeze/strategy-receipt.md).
