---
status: "Strategy note for VirtualBus and Matter southbound against the merged SemReg driver contract. It records contract support and the gaps. It implements neither product."
---

# VirtualBus and Matter southbound

Module pin: `github.com/Project-Helianthus/helianthus-semreg` `v0.0.0-20261124100158-93b56d48797e`. Owning contract: [driver-contract.md](../../api/v1/driver-contract.md). Probe record: [probes/README.md](../probes/README.md).

## VirtualBus

Section 2 allows a driver with zero transports. Section 7 admits virtual nodes with durable keys, typed links, and an origin whose evidence stays on the publishing path. The same local id on two bridges is the pair `(BridgeID, ID)`.

The merged module supports that surface as records and `Validate` methods: `InstancePlan` with an empty transport list, `NodeKey` with a configured slot anchor, `LinkClaim`, `Origin`, and `NodeRef`. The [virtual probe](../probes/virtual/virtual.go) is a transport-free driver that forms those records. The [remote probe](../probes/remote/remote.go) copies `NodeRef` and origin evidence.

Concrete gaps:

- No `VirtualBus` type or constructor is exported.
- No path-node or legacy resource allocator is exported. Rows `I-ALLOC-LEGACY-SLOT`, `I-ALLOC-LEGACY-KEY`, `I-ALLOC-PATH-SLOT`, `I-ALLOC-PATH-KEY`, `I-ALLOC-INJECTIVE`, `I-ALLOC-VARY` and `I-ALLOC-DOMAIN` in [identity.json](../contracts/identity.json) stay with that file.
- No runtime overlay retains a typed link whose endpoints are both foreign. Section 4 cites SS05 item 5 for separate publisher claims. The overlay clause of `C-NO-TRANSPORT` in [consumers.json](../contracts/consumers.json) stays there.
- `Formula.Validate` does not walk cycles (`C-CYCLE`). Nothing resolves a foreign `InputRef` at an exact revision (`C-CROSS-ASSET`). Nothing rejects a reflected origin (`C-LOOP`).

## Matter southbound

Section 7 gives an output `StartOutput(context.Context, SemanticInput, ScopedOperations)`. The output reads SemReg through that input and acts through scoped invocation. Section 11 says the Matter driver derives target attributes from catalogued elements and does not add those attributes as catalog elements. `InvokeCallBound` is the call-bound entry, distinct from `Invoke`.

The merged module exports `SemanticOutput`, `SemanticInput`, `ScopedOperations`, `OperationRequest`, `OperationResult` and `CompoundStep.Validate`. The [output probe](../probes/output/output.go) captures a cut and calls `Invoke`. A zero `Timeout` stays on `Invoke`.

Concrete gaps:

- No Matter cluster encoder, attestation material or summary-exclusion type is in the driver package. The contract names an existing summary exclusion interface; the merged module has no type of that name.
- No operation router enforces a finite deadline (`C-INVOKE-FINITE`) or refuses serialization and replay of `InvokeCallBound` (`C-INVOKE-CALLBOUND`).
- No `RegisterExecutor` implementation exists. Section 7 cites SS08 item 5. Row `C-EXECUTOR-REGISTER` stays in [consumers.json](../contracts/consumers.json).
- No session implementation wires `RetrieveLens` or `SumMembers`. Rows `C-LENS-SUM`, `C-LENS-PARTIAL` and `C-LENS-OUTSIDE` stay there.
- Development attestation and certification claims in section 11 are product statements. This note does not make them.
