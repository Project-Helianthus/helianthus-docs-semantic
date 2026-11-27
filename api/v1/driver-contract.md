---
status: "proposed contract text; the pre-dispatch architecture review, the Go types in the SemReg driver package and the runtime adoption are pending."
---

# Driver contract v1

This page is the stable interface every host programs against. It states how a
driver is composed into any host, how it publishes devices, values, relations,
sources and operations into SemReg, how identities stay stable, how several
sources of one element resolve, how a consumer that is also a driver reads
SemReg, and how a driver declares its diagnostic namespace for MCP and GraphQL.
A second host, such as an energy dispatcher or a building manager, needs nothing
from the gateway.

Each rule is followed by its source in square brackets: OPERATOR item numbers,
RULES rule numbers, decision and ruling identifiers, the approved design
contract it freezes, or a public file written as `repository:path`. The page
copies no specification text. Restricted specification text is cited by title,
version, and requirement identifier or scenario number only (OPERATOR item 34).

The numbered and named labels (OPERATOR items, RULES rules, decision and ruling
identifiers, design contracts) point at project decision records that are not
published in this repository. This page does not republish them: each rule
is the normative statement, and a label is a pointer for the project
owner, not public evidence. Until a public source index exists, a reader treats
a rule whose only support is such a label as a project decision, not as a fact
verified against a public source. Public source files are named as
`repository:path`.

The vectors that make each rule checkable are in
[`acceptance/contracts/`](../../acceptance/contracts/check_expected_outcomes.py).
Each vector has an `id` and a canonical `expected` outcome; the checker compares
the complete outcome for exact equality against its own independently written
expectation.

## 1. Scope and placement

- SemReg is the stable interface. It names no vendor and no register. [items 1,
  6; rule 2]
- A driver (`*reg`) holds all protocol knowledge and maps to SemReg in both
  directions as table rows. What a row cannot express is a compiled driver
  `RowHook`, declared next to its row. [items 1, 2; rule 4]
- A transport holds vendor-neutral bus mechanics. A driver uses the transport
  libraries. [item 7; rule 3]
- A host picks the drivers, passes configuration and serves the surfaces. The
  gateway exposes only hooks for mandatory protocol elements, for example eeBUS
  pairing, through which drivers extend it, and a driver extends the portal and
  MCP with its own elements. [items 1, 2]
- Imports point down only: host to driver to SemReg and transport. [rule 3]

## 2. Composition

- A driver exposes a public constructor. A host composes any subset of drivers
  with SemReg and receives every device, value, relation and method of those
  drivers. [items 4, 5; design contract 4]
- An instance plan carries an immutable configured `InstanceKey`, never a display
  name. Several instances of one driver kind run side by side and nothing is
  global to the process. [item 12]
- Transport claims are optional: a driver may have zero transports, and one that
  has a transport declares it. An existing transport claim may carry
  `LinkNodeSlot string`, the claiming driver's immutable configured slot for the
  link equipment it publishes itself. Empty selects the normal configured-link
  key construction. The durable `NodeKey` is formed in the actual installation,
  driver and instance scope from the configured parent plus the slot anchor. The
  field identifies equipment, not a session; it changes neither transport
  ownership nor exclusive-claim conflict matching. The same family then
  publishes on the reserved key, so there is no separate placeholder for that
  link. [SR93]
- Ordinary factory configuration is one record. The host owns dispatch to the
  chosen factory; the factory owns strict decoding of its two independent,
  owned byte operands. [approved runtime design 1]

  ```go
  type Config struct {
      Instance  string
      Enabled   bool
      Transport json.RawMessage
      Options   json.RawMessage
      SecretRef string
  }
  ```

  `Instance` carries the exact configured `InstanceKey` value and `Enabled` its
  configured flag. `SecretRef` carries the selected instance's optional
  `secret_ref` string unchanged; an omitted reference is empty. Neither the host
  nor generic planning resolves a secret or treats a neighbouring instance's
  reference as shared authority.
- A factory's descriptor declares the driver kinds the factory plans. The host
  knows the owner of a configured instance from these declarations alone and
  never calls a planning step, with a placeholder or otherwise, to find it. Two
  factories of one host must not declare the same kind. The host passes a
  configured instance, with its `SecretRef`, only to the factory that declares
  the instance's kind. An instance whose kind no factory declares is reported
  unmatched, receives no factory call and no reference, and the other instances
  start.
- `InstancePlan` carries `RetryPolicy`, the neutral record below. Normalization
  applies the preserved donor values and invents no other default.
  [helianthus-gateway:internal/drivermanager/manager.go]

  ```go
  type RetryPolicy struct {
      Budget       int
      InitialDelay time.Duration
      MaxDelay     time.Duration
      JitterRatio  float64
      Persistent   PersistentRetry
  }

  type PersistentRetry struct {
      Enabled      bool
      InitialDelay time.Duration
      MaxDelay     time.Duration
  }
  ```

  A negative `Budget` becomes 0. An `InitialDelay` of zero or less becomes one
  second. A `MaxDelay` below `InitialDelay` becomes `InitialDelay`. A
  `JitterRatio` of 0 becomes 0.2, a negative one becomes 0, and one above 0.5
  becomes 0.5. When `Persistent.Enabled`, its delays are normalized with the same
  initial and maximum rules; when it is not enabled they are left as given.
- One installation clock feeds the ordinary lifecycle and the managed publisher
  through the runtime configuration, with the wall sample and the recovery
  continuity kept as distinct operands. The runtime's installation calendar
  service supplies the session's `Calendar() Calendar` port when a native
  acquisition uses civil dates. `Calendar.BeginAcquisition() CalendarAcquisition`
  returns an immutable acquisition: `Reference() CalendarReference` exposes the
  one observed `time.Time` and the exact civil year, month and day, with the
  previous-year and previous-month operations, and `Check(Calendar) error` keeps
  the same-calendar generation and civil-day guard. The runtime owns calendar
  selection and drives it from the same clock. A driver uses it for native
  date-dependent queries only, never as a freshness or retention clock or as an
  identity. [approved runtime design; item 6]
- Factory-owned early dispatch is an optional interface. The driver performs the
  exact command recognition and owns any child command; the host calls the
  selected factories that implement it before configuration parsing, returns the
  handled exit code or error, and holds no protocol argument switch. A factory
  that does not implement it is not called. [approved runtime design]

  ```go
  type EarlyDispatcher interface {
      DispatchEarly(context.Context, []string) (handled bool, exitCode int, err error)
  }
  ```
- Each driver declares its families and their composition evidence when it
  registers through this contract, in any host. SemReg stores no vendor family
  row and no gateway composition record. The family evidence is `module` and
  `version`, omitted when empty; a claimed composition requires both and
  `composition_verified=true`, and `not_composed` carries neither and has
  `composition_verified=false`. This is the evidence of the driver's own
  registration, not a gateway token. The vocabulary is that of the
  [family catalog contract](family-catalog-v1.md#composition). [design 3.4;
  PA03; PA21; R3-028; R3-087]
- The family list is every family the registered drivers declare, with no fixed
  count. A consumer's pinned list names the required families; a missing
  required family is rejected, a valid additional family that a linked driver
  declares is admitted, and an unknown member of a Family object is rejected.
  `not_composed` and `no_producer` record the current state with its reason and
  leave what exists available. [rules 6, 14; F4-108; F4-215]
- The session passed to `Instance.Start` carries `Native()`, `SemanticInput()`,
  `ScopedOperations()`, `Calendar()` and the session's own transactional
  publisher. [sections 7 and 9]

## 3. Qualification

- `qualified` means the native owner declares the mapping from the protocol
  specification, or from the public documentation it pins, and the binding is
  current at runtime: current source, epoch, binding and generation, and the
  identity link of the participant actually present. [PA01; rule 12; D14]
- A hardware test is a verification level recorded beside the state, with a
  reference to a public record: `tested_on_hardware` or
  `not_tested_on_hardware`. It never raises or lowers qualification, promotion or
  an operation. No row is held below `qualified` for lack of a hardware test, and
  a family once held at "seen on one device" is qualified from its declaration.
  `tested_on_hardware` needs a public hardware test record in a project
  repository. Every declared profile is exposed with its level. [rule 12; D5;
  R2-072]
- A family whose specification facts declare its mapping gets no candidate or
  experimental state. `gree-vrf-can` is qualified from its specification facts,
  with the mapping declared and commands included; a fact the source does not
  give stays unknown for that element only, and its verification level is
  recorded beside it and conditions nothing. [R2-053; item 55; D1; F4-023]
- `candidate` means decoded, with no pinned source stating the semantic mapping;
  the missing fact is named and the reason is `semantic_mapping_unknown`.
  `unknown` means no source is pinned or the value is not decoded. Two public
  sources in conflict are both recorded with the reason
  `specification_conflict`. `unsupported` means the specification says the
  capability is absent; `rejected` is a runtime rejection with a reason. [rule
  14; PA01]
- A `qualified` record has the reason `declared_by_specification` and an
  evidence entry of kind `specification`, and tests reject drift from it. A
  reference to the specification or public document is enough activation
  evidence. A model string, an address or a similar concept alone declares
  nothing. [PA01; F4-021]
- Qualify, admit, accept and promote stay distinct. Qualify is this
  declared-by-specification binding. Admission applies an explicit gate.
  Acceptance is relative to a named contract. Promotion exposes a stable
  consumer contract. [PA01; rule 7]
- A field is published under its own declared type and meaning wherever the
  native documentation states its source. A categorical or boolean observation,
  for example a diagnosis state, needs no physical unit and does not go
  native-only for lacking one. [F4-028; F4-029]
- A refrigerant pressure is published wherever the native documentation states
  its pressure reference, meaning and unit; compressor speed wherever it states
  the mechanical meaning and the unit. Their poll starts when a heat pump is
  identified. A pressure whose reference, meaning or unit, or a speed whose
  mechanical meaning or unit, no public page states (a relative pressure with a
  stated reference but no documented unit included) stays native with the
  missing fact named and has no typed value or SI conversion. Any other field is
  published under the documented type and meaning rule with only the operands
  its type requires; a declared condensing temperature with documented meaning
  and unit is typed. [item 30; F4-028; rule 21]
- A value, bit or word the documentation does not define stays native and named,
  never guessed, zeroed or defaulted, and everything the documentation defines is
  decoded and published. [rule 14]
- The eeBUS normative sources are the specification files in the operator's
  eeBUS folder, each recorded by title and revision, and `eebus-inbound` is
  declared `qualified` with `declared_by_specification` from them. Flexible Load
  / Smart Heater DHW, and Monitoring and Control of Smart Grid Ready Conditions,
  exist only as drafts and are not available; nothing is built from assumptions
  about them, and no other eeBUS specification is assumed. [item 55; F4-021]
- Qualification records the declaration and its runtime binding. It does not
  gate observation visibility or operation admission: unqualified, unavailable
  and unknown observations retain their actual state. Every key the device
  declares writable, and every in-scope setting the specification itself
  declares writable (for example a SunSpec storage setting with a SemReg
  counterpart and no device-reported write bit), has its operation, and the
  level never gates it. Where SemReg has the element, the write is the semantic
  operation. A writable point with no SemReg counterpart (for example a SunSpec
  grid-code register) invents no semantic element and is exposed as a registered
  driver method in the driver's namespace, callable through MCP and GraphQL.
  [item 48; item 53; RESOLVE D3; SR36]
- SemReg promotes Matter HVAC, Energy and Hydraulics, all of eeBUS, and data a
  confirmed second major vendor also provides. An element with a Matter or eeBUS
  source is promoted on that source regardless. An element whose only basis is
  two vendors, and whose second vendor is not confirmed, stays in the driver
  namespace (MCP, GraphQL, Prometheus), is listed in the release report and is
  promoted once confirmed. Qualified alone does not promote. A candidate state
  is never by itself a promotion veto; the
  [kernel Quality rule](kernel.md#type-quality) and the separate capability and
  projection rules apply. [item 3; R2-085; R3-005; D14; SR55]

## 4. Identity

- The identity types freeze as follows. [design contract 1]
  - `NodeKey`: installation, driver kind, instance key, kind, anchor.
  - `NodeRef`: bridge, resource id.
  - `LinkKey`: type, `From`, `To`, the ordered tuple that identifies a directed
    link.
  - `LinkClaim`: key and basis.
- Each publisher's claim and its basis are retained separately under the link
  key. Two publishers attesting the same directed tuple keep two claims; one
  publisher's basis never replaces the other's, and withdrawing one publisher's
  claim leaves the other's in place. [design 3.1; SS05 item 5]
- A declaration to an absent target keeps the same `To`. When the target returns,
  the same key resolves with every publisher's retained claim and basis. Cut
  states are dangling on a complete cut, outside-cut on a partial cut, and stale
  and excluded where those apply; there is no phantom current resource. Where v1
  requires a locally homed current start, the declaration is retained in the
  publisher's runtime overlay rather than by relaxing kernel relation
  validation, so a typed link whose two endpoints are both foreign is kept and
  resolves with no resource fabricated. [design 3.1;
  helianthus-semreg:semreg/v1/publication_relations.go]
- Path-node identity is distinct from canonical equipment identity. With no
  durable anchor the node is a configured slot or unresolved. Arrival order,
  epoch, network address, credential and current value never enter an identity.
  [item 15; rule 20]
- Existing resource ids keep the allocator domain
  `helianthus.semgraph.resource/v1` and the legacy minters. The legacy id is
  `resource:` and the first 32 lowercase hexadecimal characters of SHA-256 over
  the domain bytes followed by the key members, each preceded by one `0x00`
  byte: kind, `slot`, parent, slot for a configured-slot anchor; kind, `key`,
  digest for a native anchor. [helianthus-gateway:internal/semgraph/allocator.go]
- A new path node is minted under a separate domain, the ASCII bytes
  `helianthus.semgraph.path-node/v1`. The ordered key fields are installation,
  driver kind, instance key, node kind, the anchor tag, then the anchor members:
  `slot` with the parent resource id (empty when the anchor has none) and the
  slot, or `key` with the identity digest. The digest input is the domain bytes
  followed, for each field in that order, by its UTF-8 byte length as four
  big-endian bytes and then its bytes. The id is `resource:` and the first 32
  lowercase hexadecimal characters of the SHA-256 result. The length prefix makes
  the encoding injective, and the field count is fixed by the anchor tag. The
  independent literal allocation vectors are the `I-ALLOC-` vectors of
  [`identity.json`](../../acceptance/contracts/identity.json).
- A changed serial or identifier creates a new, unbound claim. The old reference
  and its history stay; nothing is inferred as a replacement, and only a person
  rebinds. [item 16]
- An unchanged installation gives the same nodes and links on every start. The
  lifecycle test reopens durable state and compares canonical graph results; it
  does not compare cut digests, timestamps or leases. [item 15; rule 20]

## 5. Several sources of one element

- The types freeze as `Element`, `Source`, `Sample`, `SettingRoute` and
  `Resolution`. An `Element` is the canonical subject plus the whole versioned,
  dimensioned `FactKey`, so two slots of one definition on one subject are two
  elements and never contend. A `Source` has a producer, a durable path key, a
  priority, an optional step in SI and known relays. [design contract 2]
- A source declaration, its candidate and its setting route are committed
  together under the publisher's session transaction stamp, so a reader sees
  them from one commit and never a replacement candidate with a route of the
  prior generation. The runtime derives the source's owning member from that
  accepted publication and evaluates it at the selected capture. An active source
  follows its own asset's member revision; a kept stopped sample uses its prior
  owner member basis under the same evaluation context and existing lifetime.
  Source and member ownership remain distinct from the canonical subject,
  including for two joined assets with equal candidate ids and revisions. [SR56]
- The driver publishes a priority per source. SemReg returns every source as a
  link with its priority, path, resolution and availability, and takes data only
  from the highest current source. If that source is unknown or stale, the
  element shows that state and no lower source substitutes. Sources are not
  averaged. [items 21, 25]
- A stopped generation (`GenerationStopped(SourceRef)`) keeps the source and its
  last value visible as stale and it stays the highest source, so no lower
  source or mirror becomes authoritative. An explicit withdrawal of the
  declaration removes the source from current contention. An accepted
  `FactWithdrawals` for its sample, including a retained sample of a fenced
  predecessor, removes the sample from current outputs in the same commit; a
  still-declared source keeps its priority and link without borrowing a value.
- Equal declared priorities are a driver bug. A `Finding` of `Resolution.Findings`
  keeps its two ordered source references and an optional `PriorityTie *int32`.
  When present it carries the shared declared priority, including zero, with no
  sample values, steps or incomparable marker. The producers are the owners
  identified by the two source references in the returned source views. Other
  findings keep the existing sample-disagreement or incomparable payload with
  `PriorityTie` absent. Exact kernel conflicts are separate. Ties are reported
  even below the winner and before either source has a sample. Only among the
  highest sources of a tie does the most recent runtime receipt win;
  indistinguishable receipts use stable source-key order. A replayed observation
  does not refresh its receipt, and unrelated device clocks are never compared.
  [item 21]
- Disagreement is compared only between commensurate, contemporaneous samples in
  SI with both steps known. Beyond the larger step of the two sources it is
  reported as a finding with the sources, values and steps (a 0.5 °C step is
  0.5 K), and it changes no winner. Samples that are not commensurate or
  contemporaneous, for example a fresh boiler sample after a setpoint change
  against an internet mirror's pre-change sample, or an unknown step, are
  reported incomparable and never as disagreement. [item 21; rule 21; SR56]
- A value that a certificate states about a device is held as a
  [certification reference](certification-references-v1.md), a source category
  of its own and never mixed with a value the device publishes. A driver publishes
  it with origin kind `declared` and certification evidence. Its source has a
  lower priority than every device source of the same element, and it is never
  published beside a device value for the same fact key: a driver declares no
  certification source for a fact key for which it declares a device source.
  [operator decision 2026-11-26; rule 20]
- A write goes to the one owner route of the setting, checked at dispatch. It is
  never written to the latest reader and never broadcast. With no owner route, an
  ambiguous one or a withdrawn one, nothing is sent. [item 56; rule 17]

## 6. Joins

- The types freeze as `MatchClaim` (member, scheme, issuer, digest key, proof)
  and `CertifiedJoin` (A, B, survivor, statement). A driver attests only its own
  observation of a scoped, catalog-admitted identifier; for example the SKI of an
  eeBUS host seen over eBUS identifies that host, not the appliances behind it. A
  digest is comparison evidence, never the resource id. A claim is validated for
  scheme, issuer, uniqueness domain, kinds, evidence and conflicts. [design
  contract 3]
- Device-reported manufacturer and serial evidence is a separate public record,
  not a `MatchClaim` scheme. [D17; R3-104; SR43]

  ```go
  type ManufacturerSerialClaim struct {
      Member       NodeRef
      Manufacturer string
      Serial       string
      Proof        []v1.EvidenceRef
  }
  ```

  It is admitted through the consuming session's existing transactional
  publisher, with that transaction's driver, instance, epoch and generation
  ownership stamp. A driver attests only its own reported evidence. When both
  components are present, equal and unambiguous across two protocol members, they
  join deterministically and the two members resolve as one resource. Missing or
  ambiguous evidence keeps its reason and infers no identity. No catalog scheme
  id, new minted identity or second publisher is involved.
- An authenticated, revisioned operator statement naming the exact pair
  certifies a join, recorded as a `CertifiedJoin`. A driver cannot certify a join
  itself. The statement reference carries the accepted statement revision and the
  authenticated origin evidence. The installation's trusted host configuration
  supplies explicit certify, rebind or revoke through the existing identity
  owner. Both immutable member references and the named survivor come from that
  statement. A revocation names the earlier statement by its exact revision and
  the same pair and survivor, and carries its own verified disposition revision.
  Drivers and ordinary editing surfaces cannot supply authenticated origin. Host
  input and statement history stay with the existing configuration and identity
  checkpoint; no new records database or editor exists. [item 16: a changed
  serial number or identifier never implies a replacement, only a person
  rebinds; SR109]
- Only a full `CertifiedJoin` takes precedence over driver claim evidence and
  supplies the authority to rebind. Joins are computed from the validated claim
  set independent of insertion order. The representative is the certified
  survivor when that survivor is unique, otherwise the smallest canonical member
  reference, and it is a view: member references stay resolvable. Rebind and
  revocation are explicit. Mutually inconsistent operator statements leave a
  disputed join unapplied. A valid operator override takes precedence over
  contradictory driver evidence; without an applicable operator statement
  incompatible driver proofs remain unapplied with a finding. No match is made
  from a name, address, quantity, topology position or resemblance. [items 16,
  21; rules 14, 17; SR58]
- The configured binding association (an `IdentityLink` of a binding to its
  operator-selected resource) stays scoped to that binding. It changes neither
  identity membership nor routes, is no certification, and neither merges nor
  rebinds. In the eligible owner batch (its source, epoch and generation) it
  takes precedence over a competing link on that same binding, the binding
  resolves to the operator-selected resource without a new certification, and
  unrelated publisher links survive. [SR90]
- The session publication transaction offers
  `OperatorLinks([]v1.NativeBinding) []v1.IdentityLink`, using the transaction's
  source, asset, epoch and generation. The operand is its binding upserts plus
  the same owner's still-current committed bindings. Returned links are ordered
  by binding and replace only the same binding's link in that batch; a
  withdrawal travels in the same transaction. A binding whose operator link is
  already withdrawn takes no link again: re-declaring the same native reference
  while that binding remains current leaves its link withdrawn, and the next
  eligible successor binding carries the declaration. Declaration alone, another
  owner, or a batch without that carry leaves the declaration pending. An
  eligible withdrawals-only batch may carry every pending withdrawal while
  independent qualified associations stay pending. A qualified carry must match
  the whole pending set. [SR90; helianthus-gateway:internal/semgraph/operator_links.go]

## 7. Consumers that are also drivers

- A consumer driver reads SemReg through the scoped `SemanticInput` and acts
  through `ScopedOperations`, both supplied by the `Session` passed to
  `Instance.Start`: `SemanticInput() SemanticInput` and
  `ScopedOperations() ScopedOperations`, alongside the session's own publisher
  and `Native()` registry. A driver imports neither the SemReg host nor a
  concrete runtime. [item 17; SR75]
- `SemanticInput` captures a cut and resumes from a cursor, and exposes the
  typed graph operations on an already captured cut. `graph` is the public
  `semreg/v1/graph` leaf that owns the graph query and result types.

  ```go
  type SemanticInput interface {
      Capture(context.Context, Filter) (SemanticCut, error)
      Resume(context.Context, Cursor, Filter) (Changes, error)
      RetrieveLens(context.Context, CutRef, graph.LensRequest) (graph.LensResult, error)
      SumMembers(context.Context, CutRef, graph.LensRequest, v1.DefinitionRef, v1.ResourceID) (graph.MemberSum, error)
  }
  ```

  The session supplies the captured cut id, the scoped members and omissions,
  and the retained catalog and evaluation context. The caller supplies the lens,
  traversal and paging selection and the sum's member definition and scope. The
  caller cannot switch revisions, supply replacement snapshots or widen the
  captured scope. `RetrieveLens` returns its existing typed partial and frontier
  result with the in-scope members and paging it retrieved; it does not turn a
  partial cut or an omitted frontier into an early reason return. `SumMembers`
  calls the frozen graph reducer on that result and returns its exact typed
  value, or the absence reason, and the observed aggregate beside it; the
  reducer decides when an omission makes the sum unavailable. The lens result and
  the sum absence are verified separately on the same captured cut.
- The `Cursor` is an incarnation plus an ordered commit position, separate from
  the cut id. `Resume` replays every intervening commit in order, so A to B to A
  returns both transitions and not only the endpoint state. The scoped wait is
  atomic under the caller's context, so a commit between handoff and wait is not
  lost. Unavailable history returns an explicit resync; expiry of a retained cut
  is a separate error. [SR43; SR56]
- The returned scoped `SemanticCut` exposes detached `Snapshots []v1.Snapshot`
  and `SettingRoutes []SettingRoute` from the same commit, filtered to the
  session's scope, carrying the frozen snapshot capabilities, bindings and
  revisions and the committed setting-route declarations, including the route and
  capability instance selected by XX06. A consumer still uses scoped invocation
  for an independently revalidated operation. There is no second capture, route
  authority or public transport surface.
- `ScopedOperations` has two entries. Both invoke the same registered
  setting-owner router with the session's actual caller identity and scope.

  ```go
  type ScopedOperations interface {
      Invoke(context.Context, OperationRequest) (OperationResult, error)
      InvokeCallBound(context.Context, OperationRequest) (OperationResult, error)
  }
  ```

  Ordinary `Invoke` uses the existing finite request and caller deadline rules.
  `InvokeCallBound` accepts only a live, cancellable, in-process invocation
  without an absolute execution deadline; it cannot be serialized, prepared for
  later dispatch or replayed, and dropping `Timeout` cannot opt into it. [item
  67; operator conversation: «Aprob execuția legată de apel pentru comenzile
  Matter fără termen absolut (recomandat)»]
- `OperationRequest` has the closed fields `AssetID v1.AssetID`,
  `BindingID v1.NativeBindingID`, `CapabilityInstanceID
  v1.CapabilityInstanceID`, `Operation v1.DefinitionRef`, `Arguments
  []v1.TypedField`, `ExpectedSemanticRevision`, `ExpectedCapabilityRevision`,
  `ExpectedCapabilityInstanceRevision` and `ExpectedDriverGeneration` of type
  `v1.Uint64`, `ExpectedSourceEpochID v1.SourceEpochID`, `Preconditions
  []operation.Precondition` and `Timeout time.Duration`. Cut and revision
  constraints and typed canonical validation keep the donor shape; the driver
  supplies neither the effect, the route nor a causal expiry.
- `OperationResult` keeps `Status`, `KernelOutcome`, `Delivery`,
  `Acknowledgement`, `ReadbackRelation` and `Reason`, with the existing route's
  status and the operation package's evidence types. A nullable
  `CompoundExecution` contains `Partial` and the ordered `Steps`. A step contains
  its stable owner point name, `Attempted`, an optional delivery,
  acknowledgement and readback relation, and a sanitized reason. A step that was
  not attempted carries no delivery, acknowledgement or readback. No native
  coordinates, frame or unredacted transport error enter the public result. This
  is the one result shape for both invocations and their synchronously returned
  evidence. [items 66, 67; operator conversation: «Aprob comanda compusă cu
  rezultat parțial explicit (recomandat)»]
- On the setting-owner side the session exposes
  `RegisterExecutor(SettingRoute, Executor) (unregister func(), err error)`,
  where `Executor` has `Execute(context.Context, Dispatch) (Completion, error)`
  in `semreg/v1/driver`. The driver supplies its setting route and callback; the
  instance-bound session supplies the owner scope and generation. Registration
  may precede the matching route publication in the same generation so that a
  published route is usable on its first cut, but until the route is committed
  and selected by the router, registration alone cannot authorize a send. The
  scoped host adapter refuses a foreign, duplicate or retired registration under
  the existing binding and operation selector. Stopping or replacing the
  generation disables the registration, and an unregister returned for an old
  generation cannot remove its successor. [SS08 item 5]
- `Dispatch` contains the admitted `Request OperationRequest`, `Route
  operation.Route`, `Guard operation.GuardClaims`, `ExpectedEffect
  operation.ExpectedEffect`, `AdmittedAt v1.TimePoint` and `AdmittedRevision
  v1.RevisionVector`, detached from router state. The exact caller context flows
  to the executor. A call-bound invocation carries no finite-wire intent and no
  invented UTC or causal expiry. The executor supplies only `Completion`
  evidence: `Dispatch *operation.DispatchEvidence`, `Acknowledgement
  *operation.Acknowledgement`, `Readback *operation.Readback`, `ReadbackSnapshot
  *v1.Snapshot`, `Outcome operation.Outcome`, `ErrorID *v1.ErrorID`,
  `OutcomeEvidence []v1.EvidenceRef` and an optional `CompoundExecution
  *CompoundExecution`. No terminal outcome means no terminal evidence was
  supplied. The router retains ownership of the admitted intent, the exact later
  snapshot and the pack correlation. For a finite call it assembles and validates
  the strict `operation.ExecutionRecord`; for an admitted call-bound invocation
  it applies the same evidence checks without constructing a finite-wire record.
  The owner rechecks `Guard` and the active cancellation context immediately
  before the native send. An executor's own refusal before anything is
  sent (for example a precondition it reads from the device and finds unmet) is
  recorded as `failed_no_contact` with dispatch evidence `not_sent` and no
  possible side effect; `rejected` stays the admission outcome with no dispatch
  and is never produced by an executor. A readback with relation `contradicts`
  and no candidate yields `conflict`, as in the kernel page, for the recorded
  and the call-bound invocation alike. There is one registration path.
- `Session.Native() NativeRegistry` is instance- and generation-rooted.
  `NativeRegistry` provides `Node(NodeSpec) (NodeRef, error)`,
  `ReadMember(NodeRef, MemberSpec, NativeReader) error` and
  `Method(NodeRef, MethodSpec, NativeMethod) error`. `NodeSpec` carries the
  parent, kind, stable local identity, native contract and an optional semantic
  subject link. A member spec carries the stable member id, schema, units, mode,
  visibility, channel and scope, and bounds. Instance and transport setup are
  registered before device discovery. `Resume` reports the ordered changes,
  every intervening commit and endpoint recurrence included, while cursor history
  is available, independently of retained cuts. Unavailable history resyncs, and
  an unavailable pinned cut returns `revision_conflict`. [approved runtime design
  3; item 6]
- A driver opens a `driver.PublicationTransaction` through
  `Session.Publisher().Begin(ctx)`. To publish the source and candidate together
  as in section 5, it uses `DeclareSource(driver.Source) error` for the
  declaration and `StageSample(driver.Sample) error` for the sample. The
  sample names the declared source and the candidate also carried in the
  batch's `FactUpserts`; the runtime stamps the sample's receipt on admission.
  A setting route, if supplied, is staged with `DeclareSettingRoute` in the
  same transaction. [helianthus-semreg:semreg/v1/driver/session.go;
  helianthus-semreg:semreg/runtime/cut_publish.go]
- The session-backed batch preparation supplies the transaction's ownership
  stamp (driver and instance in the session, asset, source, epoch and generation
  in the batch), the next publication sequence and the expected semantic
  revision. It computes the batch digest after the batch contents are filled
  in. The handoff to the driver transaction is `Stage(v1.PublicationBatch)
  error` with that prepared batch, followed by `Commit(ctx)`; the driver does
  not call a concrete runtime's preparation method. Staging alone publishes
  nothing. [helianthus-semreg:semreg/runtime/cut_publish.go]
- The same `driver.PublicationTransaction` offers
  `StageLink(driver.LinkClaim) error`. The claim commits with the staged batch
  under the transaction's ownership stamp. Aborting the transaction or
  rejecting its commit discards the staged claim without changing committed
  claims. Claims and their bases remain separate per publisher under section 4,
  including when a target is absent. [helianthus-semreg:semreg/runtime/cut_publish.go]
- A consumer that is also a driver publishes through its own publisher. These
  types freeze with it. [design contract 4]

  ```go
  type InputRef struct {
      At        CutRef
      Subject   NodeRef
      Candidate v1.CandidateID
      Revision  v1.Uint64
  }

  type Origin struct {
      Kind     OriginKind
      Evidence []v1.EvidenceRef
  }

  type Formula struct {
      Algorithm v1.DefinitionRef
      Inputs    []InputRef
  }

  type SemanticOutput interface {
      StartOutput(context.Context, SemanticInput, ScopedOperations) error
  }
  ```

  `OriginKind` is `measured`, `declared` or `derived`. The evidence supports the
  declaration, including an operator-declared observation published without a
  derivation, and is retained on the scoped publishing path. `Site.Watch` is
  lifecycle state, never a replacement feed.
- A derived value's inputs are validated on the captured cut across assets, not
  by snapshot-local candidate lookup: each `InputRef` resolves at that exact
  `Revision` of the foreign `Subject` and `Candidate`, and a reused local
  identifier never binds to a local candidate. The snapshot-local `v1.Derivation`
  validator and its bounds stay local to that record; foreign inputs are
  validated only under the captured graph's established dependency scope and
  bounds. A derived value carries its lineage and is never presented as measured.
  A formula with a cycle is rejected, and missing, stale or withdrawn inputs
  propagate. A consumer does not mutate a donor snapshot. [design 3.4; rule 20]
- Typed links between two foreign subjects (the publisher's claim stays in the
  runtime overlay where the kernel requires a locally homed current start) and
  virtual nodes with durable keys are admitted. The same local id on two bridges
  does not collide, and reflected origins and loops are rejected. [design 3.4;
  item 15]
- A remote bridge read is implemented by the ordinary factory. It authenticates
  the remote bridge and pages one cut: every page is of that one fixed cut, so a
  bridge that advances between pages never yields a mixed-revision view. It
  resumes or explicitly resyncs, an expired or unavailable resume position being
  an explicit resync and never a silent mixed cut, and keeps the original
  `(BridgeID, ID)` and provenance under local publisher ownership.
  `_helianthus-graphql._tcp` is discovery, not identity or authority. [design
  3.4]
- An output (Matter, eeBUS) takes its semantic data from SemReg only, with the
  existing summary exclusion interface; everything is exposed by default. The two
  halves of a two-way driver may share one transport session, trust store and
  library. [items 17, 50]

## 8. Diagnostic namespaces

- The types freeze as `Namespace` (owner driver kind, key), `MemberKey`
  (namespace, instance, node, local id) and `Member` (key, schema, access mode,
  scope). A driver reserves its namespace at planning; instances are scoped
  separately. Conflicting namespace owners are rejected. There is no per-driver
  resolver, no arbitrary schema injection and no per-driver MCP server. [design
  contract 5; item 13]
- A roster read on `TreeCut` returns the namespaces declared at capture, in
  namespace-key order. For each namespace it gives the owner driver kind, the
  namespace key and every instance planned under it, in instance-key order.
  This is a read of planning declarations, not an enumeration of published
  members: a namespace with no instances and an instance that has published
  nothing are both visible. [helianthus-semreg:semreg/runtime/tree/registry.go]
- A root accessor on `TreeCut` returns the `NodeRef` of the captured tree's
  installation node, the starting node for `List`. It is not a driver
  instance or a semantic site selected from published resources. The node is
  present even before any driver publishes.
  [helianthus-semreg:semreg/runtime/tree/registry.go]
- Keep the `CutID` returned by `TreeCut.ID()` to continue in a later call. Look
  up that identifier on `Tree` to get the same captured `TreeCut` for `List`,
  `Describe` and `Read`; do not capture again. To continue a listing, pass
  the previous page's `Next` as `Page.Token` on that cut. An empty `Next` ends
  the listing. Release the capture with `Tree.Release(CutID)` or
  `TreeCut.Close()`. Looking up or releasing an unknown or released `CutID`
  returns `dangling_reference`; using another cut's page token returns
  `revision_conflict`. These are tree-capture operations, distinct from graph
  retrieval's pin and retention rules in [graph section 25, CUT-1 to CUT-3](graph.md#25-coherence-unit).
  [helianthus-semreg:semreg/runtime/tree/tree.go]
- GraphQL serves the typed `Resource`, `Relation`, `Fact`, `Source`,
  `Capability`, `Operation` and typed outcome reads over SemReg, and driver
  namespaces through the generic `TreeNode`, `Attribute` and `Method` types. MCP
  addresses the identical keys. A detached read is not turned into a bus poll or
  a remote pairing grant. [items 6, 13]
- Supported GraphQL and MCP behaviour is preserved. The historical MCP tool names
  are removed with no alias, table or dual registration, and the old eBUS-typed
  GraphQL surface is deleted after Home Assistant is re-pointed to the driver's
  namespace, with no alias. [item 30; rule 15; D16; R3-117; item 56; R3-118]

## 9. Host hooks

- The host exposes the hooks a driver needs for mandatory protocol procedures
  (eeBUS pairing, with SHIP's own trust as SHIP 1.0.1 section 12.3 and section
  13.4.4 define it) and for its portal and MCP elements. The driver implements
  them; the host serves them and holds no protocol logic. [items 1, 2; D4]

## 10. Row evaluator

- A native row needs no semantic binding. A read row instantiates a versioned
  fact key on the resolved subject with quality, time, source epoch, generation
  and evidence. An inverse row states the argument, bounds, quantization, target,
  the operation it serves and the readback that proves the effect. An accepted
  command is not an applied command. [design row evaluator; rule 4]
- A mapping a row cannot express is a compiled driver hook declared next to its
  row. `DetachedInputs` is a bounded, immutable set of payloads, qualifiers,
  receipts and instance coordinates; `DerivedValue` cites the inputs it used; no
  bus, clock, publisher or executor is passed to a hook. [rule 4]

  ```go
  type RowHook func(DetachedInputs, RowID, Direction, TypedValue) (DerivedValue, Reason)
  ```

  The verifying example is the Vaillant DHW mode and preset derivation over
  current and cached special-function inputs; polling, attempted-field merge and
  expiry stay code.
- The evaluator's acquired input carries a caller-supplied complete
  `v1.FactCandidate` metadata template and an explicit resolved subject-role map.
  It preserves the candidate id, origin id, binding id, revision, policy
  durations and version, all quality axes, source, epoch and generation, times
  and monotonic receipt, evidence and exact derivation supplied by the driver and
  runtime, and writes only the fields its matched row transforms. It invents no
  identity, clock, quality or omitted metadata, and returns the resolved subject
  beside the candidate because `FactCandidate` has no subject field. A subject
  role is validated against the supplied binding map and the referenced existing
  catalog definitions without copying a catalog. Missing required metadata or an
  unresolved role is a typed input error. Layout identifiers are validated
  against the native codec and layout descriptors the driver supplies; unknown
  codec, byte-order, word-order or bit-order identifiers fail table validation.
  No protocol-specific registry exists inside SemReg.
- Every key the device declares writable, and every in-scope setting the
  specification itself declares writable, gets its operation and its route in a
  second host where SemReg has the element, system mode included. A writable
  point with no SemReg counterpart is a registered driver method callable
  through MCP and GraphQL in the driver's namespace, with no semantic element
  invented. What the gateway wrote before the port keeps an operation. The
  setting-owner and dispatch checks stay. An operation does not wait for a
  hardware test or an evidence grade, and no default-deny or write-authority
  rule of our own applies. [items 48, 53; RESOLVE D3; SR36]
- A value's limits carry their origin: queried from the device at first
  population, in which case they apply over the specification's, else the
  specification's clause. There is no other limit. Codec checks of the wire
  representation stay. [item 54; D15]
- Nothing is sent unless an operation is called. The runtime correctness checks
  stay: the participant actually present, configured against observed topology,
  codec and range checks against queried or specified limits, freshness,
  generation fences, SHIP trust and pairing, and the privacy of published
  identities. A failed check sends nothing. A write or added traffic on a real
  installation during development or tests needs the operator's word at that
  moment; that binds agents and tests and adds no product gate. [item 56; rules
  14, 16; D11]
- Values are SI in SemReg. [rule 21]
- Disagreement findings carry the sources, SI values, steps and the incomparable
  state, compared only for commensurate, contemporaneous SI samples with both
  steps known, and preserve the exact existing `v1.Conflict` identifiers.
  Bridge-to-link relays keep the `native_observation` basis; configuration
  supplies the durable identity, and measured and declared value provenance stay
  explicit. [item 21]

## 11. Element structure for the Matter and eeBUS union

The catalog rows themselves are not part of this page; this section states the
structure they follow.

- A resource dimension names a `resource_kind` or `anchor_classes`, a non-empty
  sorted unique subset of equipment, component, function and episode. A service
  names `subject_kind` or `subject_classes` the same way. A class-level fact is
  about any current resource whose kind has one of those anchor classes, and the
  kernel checks that class. Plane membership on each such entry is diagnostic,
  energy or control. [PE01 item 2; rule 7]
- `qualifiers` are sorted unique references to dimensions of role qualifier of
  the same pack. A qualifier's value kind is a quantity `unit.one`, text, or
  symbol with its symbol list. A key carries the resource dimension and exactly
  the declared qualifiers. An unresolved fact's subject is one qualifier
  dimension. An undeclared subject class or qualifier is rejected with a reason,
  never guessed.
- A series, curve, plan, forecast, schedule, tariff table or history is a set of
  facts keyed by subject plus slot or index qualifiers; slot start and duration
  are fields of the same series; a series has no value kind of its own. [PE01
  item 3]
- An `event` kind has a service, a trigger fact of the same pack on the service's
  subject, a condition `entered`, `left` or `changed`, symbols and a payload.
  `symbols` are required for `entered` and `left`, as a subset of the trigger's
  symbols, and absent for `changed`. Payload facts are facts of the same pack,
  each on the trigger's subject or on a resource one relation of that pack away;
  a payload fact of another pack, or a relation of another pack, fails the
  contract. Planes are the trigger's. The kernel publishes an event record where
  a source emits occurrences, and otherwise events are derived from consecutive
  retained revisions of the trigger fact. [PE01 item 4; R2-051; F4-192]
- Operation attributes carry the declared list of arguments, and `parameters`
  are optional sorted unique fields of the same pack. An operation with a
  pack-declared release case (`pv.operation.set_active_power_limit` and
  `evse.operation.set_allocated_current` each have a numeric set case and a
  boolean-false release case under the same operation id and owner route) is
  judged by the selected case. The set case supplies its numeric argument.
  For operations with optional parameters, the ordinary case supplies each
  parameter at most once; an omitted optional parameter is accepted. A repeated
  or undeclared field is rejected with a reason. The release intent supplies
  exactly one argument under the existing argument field ID, with the declared
  boolean `false`. It supplies no parameter, and a request mixing set and
  release arguments is rejected. The shared `effect_rule` identifies the
  operation and judges only the set case. [PE01 item 5; F4-112; F4-113;
  SR84; SR55]
  In the element catalog, these two operations declare the alternative in
  `attributes.release` beside `argument` and `effect_rule`. Its entire shape is
  `{"argument":{"value_kind":"boolean","value":false}}`. `release` and its
  `argument` are closed objects. The boolean is a command argument, not a new
  fact or an assertion about the existing fact's value. Release clears the
  limit on the subject of the existing `argument` fact, under the same
  `capability`, `effect_rule` and single setting-owner route. It takes no set
  argument or parameter and uses no numeric fallback. The numeric set case is
  unchanged. The [kernel release intent](kernel.md#type-expectedeffect) carries
  only the effect-rule reference, not a predicate. There is no readback; at best
  the outcome is `acknowledged_unverified`. The enabled state stays Unknown.
- The pack list is open: every pack the catalog defines is admitted, with no
  fixed count, and a Family row can name every accepted pack it maps to. [F4-107]
- The units the union adds are `unit.second`, `unit.cubic_metre`, `unit.metre`,
  `unit.ohm`, `unit.radian`, `unit.one`, `unit.volt_ampere_reactive_second`,
  `unit.volt_ampere_second`, `unit.kilogram_per_cubic_metre`,
  `unit.becquerel_per_cubic_metre`, `unit.kilogram_per_joule`,
  `unit.watt_per_square_metre`, `unit.metre_per_joule`, `unit.currency` and
  `unit.currency_per_joule`, with the currency named by an ISO 4217 text fact of
  the same subject. Unseen cases are marked as working readings. [PE01 item 7]
- Target rules. Matter feature bits, PowerMode, measured-value bounds, ranges,
  energy reset and scaled pressure are derived by the Matter driver from the
  catalogued SemReg elements, their declared field bounds and the kernel
  continuity where the target needs it. The current measurement alone does not
  give Min/MaxMeasuredValue. An equal numeric cumulative-energy sample after a
  documented counter discontinuity differs from a continuous sample for
  projection and reset; the binding uses the supplied continuity evidence, not a
  fabricated threshold. The derived target attributes do not become new catalog
  elements. An atomic write of presets or schedules is one operation.
  SetpointRaiseLower is a transformation to an absolute setpoint. AC voltage,
  current and power fields are RMS. For eeBUS, the value source and value state
  map measured to observed, calculated to derived, empirical to inferred, and out
  of range to validity suspect with the bound kept. eeBUS `HVACRoom` maps to a
  room resource kind and `HeatingZone` to `resource.zone`; rooms are not folded
  into zones. [PE01 item 8; F4-066; F4-120; F4-146; F4-191]
- The identification schemes are exactly `scheme.ieee.eui48` (issuer none; 12
  upper-case hexadecimal digits, no separators) and `scheme.ieee.eui64` (issuer
  none; 16 upper-case hexadecimal digits, no separators), arm `public_registry`.
  [F4-110]
- `unqualified` does not remove the northbound Matter payload. SS01 removes
  that northbound effect. Southbound Matter input guards stay. [D26]
- Matter clusters are a design input of SemReg. The 0.7 Matter output ships with
  development attestation using the SDK's test certificates, uncertified, and
  claims no certification. [items 3, 39, 51; F4-020]

## 12. Mapping records

- A mapping toward SemReg and any vendor or protocol family id live in the driver
  as data rows. A record is declared from its specification and names its source.
  No authority field of our own decides a write or an exposure. [items 1, 2;
  PA12; R2-052; R2-083]

## 13. Wire continuity

- Existing v1 fields keep their meaning: `Selection` is presentation only,
  `Conflict` has exact-value semantics, and a binding generation is not a device
  identity. Additions are in place, with no alias, migration step or revision
  bump. The [kernel](kernel.md), [graph](graph.md) and
  [serialization](serialization.md) contracts remain the definitions of the
  records they name. [rule 15; D16]
