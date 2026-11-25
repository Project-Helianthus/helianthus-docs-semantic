---
status: "Draft oracle of the behaviour that existed before the 0.7 port to SemReg; vectors are historical and never edited by later rows"
---

# Oracle of current and pre-port behaviour

This directory and `acceptance/vectors/` record the old behaviour of Helianthus once, as files any later row can replay.
A row that moves code proves "no output changes" by replaying these vectors against the old build; an expectation is
never regenerated from new code. The vectors are the historical oracle: later rows read them and never edit or
regenerate them.

Nothing here is a test, golden or page of a donor repository. The donors are only read at their pins.

## References

`references.json` names three references. Each entry holds the identifier, the repository slug at the pin, the name after the
renames, and the full commit.

| Reference | Meaning |
| --- | --- |
| `current` | the frozen gateway pin, the thirteen other repository pins and the add-on 0.6.58 |
| `released` | the add-on 0.6.58 and the gateway commit that its `helianthus/bom.json` names |
| `pre-port` | the last 0.6 release of the gateway and of the add-on, and the parent of the PV cutover for the canonical PV v1 contract |

## Bill of materials (`bom/`)

`bom/<reference>-<entry>.json`, one file per Go module of each reference: the output of `go list -m -json all` at the pin,
reduced to module path, version, the `go.sum` hash (`sum`) and the `go.mod` hash (`go_mod_sum`), plus the `go` directive of
the main module. For each add-on entry the file is the add-on's own `helianthus/bom.json`, byte for byte, or a note that the
file is absent at that pin.

## Binaries (`binaries.json`, `binaries/`)

Each entry records the reference, the Dockerfile that fixes the build form, the exact command, toolchain, target and
environment, the resolved source revision and the delivered file with its SHA-256. Two build forms exist and are not mixed:

- add-on 0.6.58: `go build -trimpath -buildvcs=true -tags nomatter -ldflags ... ./cmd/gateway` in a clone of the commit;
- add-on at the last 0.6 release: `go install <module>/cmd/gateway@<version>`, with neither `-trimpath` nor tags.

A frozen gateway pin that is not the one an add-on ships is built with the form of the add-on of its reference, with its own
commit supplied as the version, and says so in its entry. The binaries are labelled gateway CLI binaries; the replay
executables of the sessions are separate and are never these files. The target is linux/amd64.

## Vector kinds

`acceptance/vectors/index.json` has one entry per vector file except itself: `path`, `sha256`, `origin` (`recorded-current`,
`recorded-released`, `recorded-pre-port`, `specification`, `synthetic`), `reference`, `role`, `recorder`, and for the SS02
cases `case` and `kind` (`native` or `new-binding`). `role` is `expected-output` for an output that a recorder or a session
replay emits and `input` for a file that no recorder emits: a session input and a hand-authored specification vector.

| Path | Content | Origin |
| --- | --- | --- |
| `current/gateway-goldens.json` | path, sha256, checking test and exit status at the pin of every golden of the frozen gateway | recorded-current |
| `current/graph/` | one cut per family (`<family>.json`) and one file per negative class (`negative-<class>.json`), read through the one hub of the frozen gateway | recorded-current |
| `current/restart/` | `cut-first.json` and `cut-second.json`: the two lifecycles of one composition over one allocator store directory | recorded-current |
| `current/gateway/cmd-gateway/ss02/` | native records of the Vaillant hot-water mappers and of the gateway Growatt CAN receive path | recorded-current |
| `current/canbusreg/canbusreg/ss02/` | native records of the registry Growatt CAN classifier | recorded-current |
| `current/modbusreg/sunspec/ss02/` | native records of the SunSpec decoder and monitoring capability on the Model 103 W and W_SF operands, with each fact's number, enum number and symbol, or bits and bit symbols | recorded-current |
| `current/gateway/adaptermux/` | case files of the multiplexer: `transition/` (every fixture and input of the state transition table), `arbitration/` (bid selection at the SYN boundary), `send-symbols/` (escape pairs of the gateway write path), `v8classifier/` (classifier modes, event sequences and admin events), `pacer/` (output cadence, echo samples, grace and deadlines) and `ptytest/` (the pseudo-terminal pair and the serial multiplexer open, absent device and reopen) | recorded-current |
| `current/gateway/localworkerhost/` | case files of the local worker supervisor: argv plan, child environment, child and configuration validation, report encoding and the lifecycle; `supervisor/` holds report fences, leases, restart, failed launch, stop escalation, unexpected exit, duplicate child and allocator mismatch | recorded-current |
| `current/gateway/engine/` | case files of the six engines (`scheduler/`, `shadow-cache/`, `passive-tap/`, `deduplicator/`, `reconstructor/` with the F19c helpers) and of the closure that moves with them (`watch-catalog/`, `observe-first-flags/`, `observe-first-family-policy/`) | recorded-current |
| `current/modbus/modbus/` | case files of the Modbus library's pacing code: `scheduler/` (limit validation, admission, fair order, retry, coalesced dependents, cursor removal and churn, exact deadline release), `backoff/` (the reconnect backoff) and `rtu-session/` (the RTU exchange owner) | recorded-current |
| `current/gateway/modbusadapter/` | case files of the gateway's read-only session: method set and admission, deadline classification, pacing completion, a cancelled pacing wait and the per-transaction timeout | recorded-current |
| `current/gateway/cmd-gateway/tesla-observe/` | case files of the passive serial opener of the build that is not Linux: the stub returns no source and the error sentence "receive-only serial observation requires Linux" | recorded-current |
| `current/gateway/cmd-gateway/vaillant-typed/` | case files of the typed outputs of the Vaillant publication owner and of the semantic cache: `zone/`, `dhw/`, `circuits/`, `boiler/`, `system/`, `fm5/`, `solar/`, `energy/`, `schedules/` and `cache/` are committed; `radio/` and `adapter-hardware/` carry bus-transmitted identifiers and are digest-only | recorded-current |
| `current/gateway/matter/` | case directories of the Matter target projection: `projection/` (`projection.go`: the requested-item and disposition table, the exact milliampere conversion, eligibility, the end to end projection, rejections, several contributors and the mapped key) and `model161/` (`model161.go`: the 1.6.1 projection and its canonical output checks); each case is a directory with `input.json` and `output.json` | recorded-current |
| `current/gateway/matter-feedv1/` | case directories of the binding feed: `server/` (lifecycle and admission, detachment and strict rejection, concurrent capture), `client/` (public wire contract, typed resync), `schema/` (closed objects and wire members), `corpus/` (valid and invalid wire values against the published schema) and `embedded-generation/` | recorded-current |
| `current/gateway/matter-libraryhost/` | case directories of the library host lifecycle: `lifecycle/`, `unavailable/`, `rows/`, `port-failure/`, `factory/`, `stamp/`, `restart/`, `token/`, `start/`, `stop/`, `close/`, `cancel/`, `generation/`, `project/` and `imports/` | recorded-current |
| `current/semreg/semreg-v1-graph/` | the catalog bytes embedded in the SemReg enforcement source and their sha256 | recorded-current |
| `current/sessions/<family>/<case>/session.json` | the published input of a whole session | synthetic |
| `current/sessions/<family>/<case>/output.json` | the frozen output of that session on the old process | recorded-current |
| `pre-port/gateway/` | GraphQL introspection (lists in name order) and MCP tool list of the pre-port gateway | recorded-pre-port |
| `pre-port/gateway/typed/` | typed semantic GraphQL queries (`graphql-typed-queries.json`), GraphQL mutations (`graphql-typed-mutations.json`) and semantic MCP tools (`mcp-typed-tools.json`) of the pre-port gateway | recorded-pre-port |
| `pre-port/gateway/canonical-pv/` | the canonical PV v1 mapper and its SemReg shadow (`canonical-pv-mapper.json`), the retained MCP envelope (`mcp-canonical-pv-envelope.json`) and the dedicated M2M contract (`m2m-canonical-pv-contract.json`) at the parent of the PV cutover | recorded-pre-port |
| `pre-port/losses.json` | pre-port GraphQL fields the current introspection does not publish (a derived comparison), each with the pre-port vector that shows a value | recorded-pre-port |
| `spec/` | independent protocol bytes for generic Modbus writes | specification |
| `specification/` | SI and specification expectations of the SS02 cases, kept apart from the recorded vectors | specification |

A recorded vector carries the input it was recorded from and every output the code produced. A specification vector cites
document, version and clause or register and never the text. A vector that carries an identifier the eBUS bus transmits is
not committed; its recorder is, and its index entry keeps the frozen digest (`digest_only`). The `radio/` and
`adapter-hardware/` cases of `current/gateway/cmd-gateway/vaillant-typed/` are such vectors.

## Family graph files

`current/graph/` holds one file per family and one per negative class, recorded at the gateway pin through the one publication
hub (`internal/semhub/`, `Hub.CaptureCut`) and the family table `cmd/gateway/semantic_family_graph.go`. The recorder is the
harness-only `recorders/go/gateway-graph/zz_oracle_graph_*_test.go`; `record.sh` copies it into a scratch unpack of the gateway
pin and runs `TestOracleGraph` there, driving each publisher of the pin from the offline fixtures the pin's own tests use and
editing none of them. A file holds no clock, no digest of a run and no identifier a run allocates (source epoch, binding,
candidate, snapshot or cut identifier), so two recordings are the same bytes.

A family file has the format `helianthus-oracle-graph/1`, kind `family`:

- `name`, `source`, `fixture` (the pin's test whose fixture drives the publisher), `publication` (`graph` when an asset of the family
  is graph-enforced, `ungraphed` when the family publishes assets that are declared without enforcement and so holds no graph
  member, `empty` when the pin composes no publisher of the family) and `statement`.
- `family_table`: each row of the pin's family table and the value of its graph switch.
- `catalog_digest`, `assets` (the hub's graph state: asset, driver and enforcement), and `cut` (completeness, members, the
  members the cut excluded for a duplicate identity and the declared assets it does not include, each with its reason).
- `resources` (kind, home asset, state, anchor, origin and the planes the cut gives each), `relations` (each instance with its
  state, coherence, basis class and planes), `facts` (each fact key held by a member, its candidate count and its planes), `findings` and, in the relation files,
  `declared_relation_definitions` (the pack's relation definitions in the embedded catalog).
- `retrieval`: the sites traversal and the seeded lenses. The semantic registry the gateway resolves at the pin has no cut
  traversal function, no lens retrieval function and an embedded catalog that seeds no lens; the recorder checks the first two
  against the module source the gateway resolves, so `sites_traversal` is `not_available`, `seeded_lenses` is empty, and the
  installation roots are the cut's current resources of the installation-root kind. A later pin that adds the retrieval
  functions makes the recorder stop instead of recording a traversal it does not run.

| File | Publisher at the pin | Fixture |
| --- | --- | --- |
| `pv-logger.json` | the logger PV class, one asset per admitted inverter child and one per logger | the logger replay of one logger and one dongle |
| `pv-sunspec.json` | the SunSpec PV class | one inverter served by the pin's virtual server over a loopback socket |
| `storage.json` | the configured battery storage asset | the production runtime over the pin's scripted endpoint |
| `evse.json` | the retained EVSE owner; the family is off in the table | its first persistent outcome |
| `infrastructure.json` | the synthetic site publisher, the infrastructure pack's only graph-enforced publisher | its own batches |
| `site.json` | the same publisher with the operator-record section accepted | the configured site, grid connection and meter role |
| `pv-relations.json` | the logger PV class's relation instances after the native owner withholds one child; the pack's declared relation definitions | the logger replay with one child withheld |
| `storage-relations.json` | the storage gate: no relation instance, no absence; the pack's declared relation definitions | the production runtime over the pin's scripted endpoint |
| `evse-relations.json` | the operator-record path of the EVSE pack: a configured meter measures the charging driver's EVSE; the pack's declared relation definitions | a synthetic charging driver with graph enforcement and the accepted operator-record section |
| `thermal.json` | the boiler publisher; the family is off in the table | its first qualified flow temperature |
| `paired.json` | one unit observed by an owner family and a contributor family through the declared pairing | the pairing acceptance fixture |
| `meter.json`, `vrf.json`, `gateway-topology.json` | none: the pin has no such publisher | empty hub |
| `eebus-inbound.json`, `can-storage.json` | none: the pin's file does not name the publication hub (the file says so) | empty hub |

The empty files are read through the same cut as every other family: no asset, no member, no resource, no relation.

## Restart files

`current/restart/cut-first.json` and `current/restart/cut-second.json` record two lifecycles of one composition of the frozen
gateway over one allocator store directory. The recorder is the harness-only
`recorders/go/gateway-restart/zz_oracle_restart_test.go`; `record.sh` copies it into a scratch unpack of the gateway pin and runs
`TestOracleRestart` there, driving the pin's pairing composition, resource allocator on its file store, operator-link seam and
operator-record configuration provider, and editing none of them.

Each lifecycle declares a paired asset of the thermal pack with an owner source and a contributor source, and the configuration
home that holds a site, its grid connection and the site-contains-connection relation. Both sources resolve the one unit under one
operator slot. The owner publishes the unit and its flow temperature; the contributor's first batch carries an identity link that
names no resource; the operator then declares that link; the contributor's next batch carries it with its own flow temperature;
the configuration provider accepts the site section. The first lifecycle is captured and stopped (each source's epoch retired);
the second opens a new hub on the same allocator store directory, republishes in the same order and is captured again. A file
holds no clock, lease, cut digest, source epoch, binding, batch or snapshot identifier, so two recordings are the same bytes.

A cut has the format `helianthus-oracle-restart/1`, kind `cut`:

- `compared`: the members the two lifecycles are compared on, sorted: `node_ids`, `nodes` (resource, home asset, kind, state,
  anchor, origin), `link_keys` (relation definition, endpoints, type, home asset, state, coherence), `aliases` (each anchor key the
  allocator store holds for a resource, with its class, basis, slot, supersession state and home), `source_links` (each source's
  identity link: its native evidence, the resource it names, state, revision, whether it is an operator declaration, and its
  basis) and `consumer_value_keys` (each fact key with its dimensions and candidate count).
- `late_link`: the operator identity link declared after the first batch, as it is published. It is also a row of `source_links`.
- `source_values` and `presentation`: each source's candidate of the fact, its value and quality, and the pin's presentation of
  the key. The pin holds no numeric priority per source; the priority is the owner-first presentation policy
  (`policy:gateway-owner-first`), so each value says whether it is the one presented and `presentation` names the policy, the
  owner and the selected source and value.
- `recovery_export`: what the recovery seam returns for the shared asset, exactly as the pin returns it, from four calls. The
  pin's composition creates its hub with no recovery hooks, so `ExportRecoveryChecked` answers that recovery is not enabled and
  `ExportRecovery` the zero record. A hub with a contributor list cannot be declared with the hooks enabled, so the same two
  calls are repeated after the hooks are enabled on the declared hub through the hub's own field, as the pin's package test seam
  does; `ExportRecoveryChecked` then fails with `ErrRecoveryMultiSource` and the zero record. Export and restore of an asset with
  several sources are the repair of SS05 and SS06; the result is recorded as the pin's behaviour, and no per-source share is
  asserted.
- `lifecycle`, `cut` (completeness, members, findings), `not_compared` and `not_recorded`.

`check.py --restart` verifies that both files are indexed as recorded-current expected output of the `current` reference with
their sha256, then compares `compared` member by member. Clocks, leases, cut digests, `late_link`, `source_values`,
`presentation`, `cut`, `lifecycle` and `recovery_export` are not part of the comparison. When the lifecycles match it prints
`OK` and exits 0. When a member differs it prints each difference as an item 15 defect (the identity differs between the two
lifecycles of the pin, owned by SS05 and SS06, a 0.7 bug); the command exits 0 only if `index.json` marks that member in the
`defect` object of both cuts (`item`, `owner` and `members`, added when the cuts are first recorded), so the committed bytes stay
the pin's, and exits nonzero for a difference the index does not mark or a mark the cuts do not show. `check.py --replay current`
rebuilds both cuts under `.tmp/`, compares their bytes with the committed ones, and runs the same comparison on the rebuilt cuts.

A negative file has kind `negative`, a `class` and `scenarios`, each with the fixture, the outcomes the pin gives (accepted, or
refused with the kernel's stable identifier and its text, and whether the asset's snapshot bytes are unchanged) and, where it
is meaningful, the `state` of the cut after the scenario. The six classes are `duplicate-identity`, `false-join`,
`missing-membership`, `stale-or-dangling-relation`, `identity-drift` and `unauthorized-control`. A result that is not the
refusal its scenario title suggests is recorded as the pin gave it: two assets that each carry one resource identifier are both
accepted and the cut reports a duplicate identity finding and excludes them; a withdrawal of a resource that a service names is
refused as `dangling_reference`; a configured relation to an unpublished far end is published and the cut judges it dangling.

## Engine, adaptermux and local worker case files

Each case file of `current/gateway/adaptermux/`, `current/gateway/localworkerhost/` and `current/gateway/engine/` has the
format `helianthus-oracle-bt01-case/1`: `component`, `source` (the donor file), `stimulus` (the pin's own test that supplies
the input), `input` (`bytes`, `qualifiers`, `clock`, `state`) and `output` (`symbols_written`, `decisions`, `cache`,
`observations`, `counters`). The recorders are the harness-only `zz_oracle_*_test.go` files under
`recorders/go/gateway-adaptermux/`, `recorders/go/gateway-localworkerhost/` and `recorders/go/gateway-engine/`; `record.sh`
copies them into a scratch unpack of the gateway pin, runs `TestOracleAdapterMux`, `TestOracleLocalWorkerHost` and
`TestOracleEngine` there and writes the case files. The `recorder` of each of these entries is a complete command: run from the
repository root as `python3 acceptance/oracle/<recorder>`, with `ORACLE_DONOR_ROOT` set (see Commands), it writes the whole
group under `.tmp/oracle-record/<sources>/`, and the vector named by the entry is at that directory plus the entry path
without its `current/gateway/<group>/` prefix. A case that varies a field of its input records every field it varies.
A reconstructor case records the symbols as the pin's feeder passes them (`qualifiers.fed_symbols`, with the feeder, the escape
flags and the tap events that follow the stream), the symbol spacing and start (`clock`), the configured watchdog and the
local-address snapshotter (`state`). A local-worker report case records the encoded report bytes or the exact bytes given to the
decoder (`bytes`). A transition case records in `input.bytes` the byte its input hands to the handler, including the source byte of a STARTED event. A `send-path/` case drives the mux send path and lists the symbols the upstream received. A `ptytest/pair-roundtrip.json` case runs the pin's serial-path fixtures on both serial ports. A local-worker validation case records the plan, the child identity, the observed descriptors and the environment it was given (`input.state`), and an argv case records the vector given to the parser (`input.state.args`). A reconstructor observation records its five timing markers and its ACK correlation. In an adaptermux transition case `symbols_written` lists only the payloads of adapter writes; the other
effects are in `decisions` with their class and in `observations`. In a classifier case `symbols_written` lists the symbols
that the classifier does not drop.

Donor files with no offline fixture at the pin have no vector. `watch_efficiency.go` declares types and no function and has
no test file: only `SemanticReadExecutionStats` is recorded, through the scheduler's watch read cases. The reconstructor's
pending-probe SYN scan-timeout path has no caller in the pin's tests. The Linux-only pseudo-terminal files
(`ptytest_linux.go`, `serial_exclusive_linux_test.go`) are not executed on a Darwin host, and the one pin test that is skipped
at the pin (`TestPassiveBusTap_WrappedResetAndDecodeFaultsStillSurface`) is not recorded.

## Modbus pacing, read-only session and passive-open case files

The case files of `current/modbus/modbus/`, `current/gateway/modbusadapter/` and `current/gateway/cmd-gateway/tesla-observe/`
have the format `helianthus-oracle-qv04-case/1`, with the members of the BT01 case format: `component`, `source` (the donor file
under test), `stimulus` (the pin's test that supplies the input, or a statement that the pin has none), `input` (`bytes`,
`qualifiers`, `clock`, `state`) and `output` (`symbols_written`, `decisions`, `cache`, `observations`, `counters`). The recorders
are the harness-only `zz_oracle_*_test.go` files under `recorders/go/modbus/`, `recorders/go/gateway-modbusadapter/` and
`recorders/go/gateway-tesla-observe/`; `record.sh` copies them into a scratch unpack of the pin, runs `TestOracleModbus`,
`TestOracleModbusAdapterReadOnlySession` and `TestOracleTeslaObserve` there and writes the case files.

The pacing code (`tcp_scheduler.go`, `rtu_session.go`) is recorded at the `modbus` entry of `references.json`; that tree has no
`session/` directory and none is recorded. The read-only session is recorded at the gateway pin, which resolves the Modbus library to its own
pseudo-version (see `bom/current-gateway.json`); that revision is not the pacing pin.

- `scheduler/` and `backoff/` come from `tcp_scheduler_test.go`, `scheduler_cursor_churn_test.go` and
  `scheduler_exact_deadline_release_test.go`. A scheduler case has its `limits` in `input.qualifiers` and its operations as
  `input.state.script`, executed in order against one scheduler; `output.decisions` has one record per operation, in the same
  order, with its error (`text`, and for a protocol error `kind`, `field`, `offset`), the dispatched request where there is one
  and `state`, the vector `[queued requests, in-flight requests, active admission keys, coalesced dependents, order
  metadata size]` after the operation. The operations are `enqueue`, `admit_weighted` (weighted admission, as the exact-deadline
  test drives it), `dispatch` (with the scheduler offset `now`), `complete`, `complete_last_dispatch`, `retry`, `cancel_queued`,
  `attach_dependent`, `detach_dependent`, `set_key_accounting` (sets one key's queued and dependent counters, as the
  arithmetic test does), `new_scheduler`, `schedule_coalesced` (with its intents), `coalesced_group`,
  `require_coalesced_dispatch`, `retry_coalesced`, `finish_coalesced`, `group_fail_transport`, `group_cancel`, `group_states`,
  `key_queued` and `internals` (the sizes of the scheduler's tables). The scheduler has no clock; every dispatch carries its
  offset. The endpoint of a coalescing intent is an opaque identity that the scheduler only compares; the cases use a synthetic
  host name for it. A backoff case records its configuration and jitter sequence and the delay or error of every call; the
  backoff has no clock either.
- `rtu-session/` comes from `rtu_session_test.go`. The input records the timing (`baud`, framing, the configured and derived
  intervals), the scripted reads of the stream (`state.scripted_reads`: byte, receipt offset and error) and the steps (the
  request ADU, the unit and the response policy). The output has the frames the stream received (`symbols_written`, with the
  written count and error), the scripted reads the session consumed (`observations`), one decision per step with the
  retained response ADUs or the error, and the write count. Context timeouts of the session use the wall clock; only values
  that the scripted stream fixes are recorded, so a stream that has no script left has no recorded offset or read count.
- `gateway/modbusadapter/` comes from `readonly_session_test.go`. The pacing and timeout tests measure wall time; the case
  records the test's own range or bound check as a boolean beside the bound it uses, never the measured time.
- `tesla-observe/` holds the non-Linux records: the opener of `tesla_observe_flow_other.go` called directly with three
  synthetic paths, taken from the command's port table, and reached through the preparation run (exit code 1 and the
  sentence on the error stream). The pin has no test of this file, so the stimuli are the opener's own argument. Each record
  has `source_is_nil`: no source is returned.

Evidence gap. The Linux opener `tesla_observe_flow_linux.go` and its pin test file need a Linux kernel and a pseudo terminal
under `/dev/pts`; the recording host here is not Linux and has no Linux machine, so no record of the Linux opener is
published. The recorder `recorders/go/gateway-tesla-observe/zz_oracle_tesla_observe_linux_test.go` (build tag `linux`) is
written against the pin's test helpers and compiles for linux/amd64, but it has not been executed and no vector is derived from
it. The `!linux` records are produced by a replay on a host that is not Linux; a replay on Linux compiles the other file.

## CAN receive case files

`current/transport/can-receive/<case>/{input,expected}.json` hold the six cases that the CAN receive rows replay. Each case has
the formats `helianthus-oracle-qv05-input/1` (`case`, `partition`, `component`, `source`, `stimulus`, `operands`) and
`helianthus-oracle-qv05-expected/1` (`case`, `partition`, `calls`, `result`). `source.files` names the pinned file under test with
the sha256 of its bytes at the pin and `source.overlay` lists the scratch substitutions of the run (empty on a host that is not
Linux). `calls` is the ordered list of the operating-system operands the opener made, with their arguments; `result` is what
the opener returned. Both files of a case are recorder output, so the index gives each the origin `recorded-current`, the role
`expected-output`, the case id (the directory name) and its `platform` partition.

| Case | Partition | Pinned file | What it records |
| --- | --- | --- | --- |
| `linux-bms-receive` | `linux` | `growatt_bms_can_socketcan_linux.go` | lookup, socket, classic-mode option, bind, poll, read, close in order; the identity and the raw record |
| `linux-bms-identity-mismatch` | `linux` | same | a different name, index zero and a negative index: the identity sentence and no socket or bind |
| `linux-bms-missing-interface` | `linux` | same | a failed lookup: the wrapped error and no socket or bind |
| `linux-project-reopen-clock` | `linux` | `growatt_project_socketcan_linux.go` | the open, receive, close, reopen, receive and snapshot sequence of `TestCX18ReopenKeepsOneClock` on one scripted clock |
| `nonlinux-project-unsupported` | `nonlinux` | `growatt_project_socketcan_unsupported.go` | the unsupported sentence for a valid and an empty name |
| `nonlinux-bms-unsupported` | `nonlinux` | `growatt_bms_can_socketcan_unsupported.go` | the configuration sentence for an empty name and the unsupported sentence for a valid name |

The four Linux cases need a Linux host and the two unsupported cases a host that is not Linux; neither is a cross-compile
receipt. The BMS opener calls the operating system directly (`net.InterfaceByName`, `unix.Socket`, `unix.SetsockoptInt`,
`unix.Bind`, `unix.Poll`, `unix.Read`, `unix.Close`), so on Linux the recorder runs a scratch copy in which each call is replaced
by a recorder function with the same signature (the table `OVERLAYS` in `recorders/can_receive.py`; the counts of the replaced
text are checked, and the replaced text is written into `source.overlay`). The project opener already takes its operating-system
calls as an argument; the recorder passes its own scripted calls and replaces only its one clock reading,
`time.Since(growattProjectClockOrigin)`, so that the receipts and the snapshot read a scripted clock from the one origin. The
unsupported cases call the pinned `!linux` openers unchanged; `result` records the imports of the pinned file (only `errors`),
which is the evidence that the branch holds no socket call. The pinned test files of these openers are build-tagged for Linux,
so no pin test supplies a stimulus for the unsupported branch.

The recorder is `recorders/can_receive.py` with the harness-only files of `recorders/go/gateway-can-receive/`. It compiles the
test binary on the host, runs it, and writes a receipt beside the cases: the platform, the Go target and the host it ran on, the
toolchain, the command, the compile and run statuses, the revision of this repository the recorder ran from, the pinned sources and their digests, the overlay, the pinned files that
the compile selected (`go list`), the digest of the test executable, the digest of the recorder sources and the digest of the
whole `index.json` entry list. The gateway resolves the CAN library to its own pseudo-version (see `bom/current-gateway.json`), not
to the pin of the `canbus` entry. That pin has no `receiver/` and no `periodic/` directory, so there is no periodic-publication
donor at it.

The cases are frozen once, on one host of each platform, with `recorders/can_receive.py freeze --actual <tree>`; a frozen
case is never replaced. After both partitions are frozen and indexed, each runner runs `check.py --record-can-native current` from
the same revision of this repository, and the two trees are collected on the replay host (see Commands).

## Matter projection, feed and library-host case files

The three directories `current/gateway/matter/`, `current/gateway/matter-feedv1/` and `current/gateway/matter-libraryhost/`
hold one directory per offline case of the gateway pin's `matter/projection.go`, `matter/model161.go`, `matter/feedv1/` and
`matter/libraryhost/`: `<directory>/<group>/<case>/input.json` and `<directory>/<group>/<case>/output.json`. The layout is
the same in the three directories.

- `input.json` holds the inputs. Its members are `format` (`helianthus-oracle-qv08-input/1`), `case` (`<group>/<case>`),
  `component` (the donor file under test), `source` (the donor test file that supplies the stimulus), `stimulus` (the pin's
  test, with its subtest where it has one) and `input`.
- `output.json` holds every output the code produced for that input. Its members are `format`
  (`helianthus-oracle-qv08-output/1`), the same `case`, `component`, `source` and `stimulus`, and `output`.

Both files are emitted by the recorder, so both are `expected-output` entries of `index.json`; `check.py --replay current`
compares both byte for byte, which also freezes the input. A replay of a case reads `input.json`, drives the code and
compares what it produced with `output.json`.

In `matter/`, an input holds the call (`call`), the SemReg snapshot and evaluation view or the result under test, and a
`variant` that names what the case changed from the pin's positive fixture; the changed value is in the input, never only its
name. An output holds `result` (the projection), `canonical` for a canonical byte string (`length` and `sha256` of the bytes
the function returned, `null` when it returned none) and `error` and `error_id` (the error text and the SemReg identifier, both
`null` on success). `result_is_zero` is true when the function returned its zero value with an error. A case that depends on
the roster pin of `model161_test.go` has no record (see below).

In `matter-feedv1/`, a `server/` or `client/` case lists its HTTP `steps` (method, path, body, and the provider state set
before the step), the provider snapshots, and the server options. The output lists per step the status, content type, JSON
body, the provider's capture and invoke counts. The intent deadline of the pin's tests is the wall clock plus one minute;
the recorder fixes it at a calendar date in 2100 (and in 2000 for the expired intent), so the input is a value. The client
cases run through a loopback listener whose address is not recorded. A `schema/`, `corpus/` or `embedded-generation/` case
names the schema file of the pin (`docs/schemas/matter-binding-feed-v1.schema.json`, by length and sha256, not copied) and
records the wire value and the validator's verdict (`accepted`, `error`). The three cases that capture the provider's snapshot through
the feed (`server/lifecycle-and-admission`, `server/concurrent-capture-keeps-one-cursor`, `client/public-wire-contract`) carry a
`golden` member in their output that names the item 5 golden `cmd/gateway/testdata/characterization/consumers/matter_feed.json` by its entry in
`current/gateway-goldens.json` (path and sha256); the golden is the gateway-level capture of the same snapshot wire contract
and is not copied.

In `matter-libraryhost/`, an input holds the `configuration` (selection, generations, binding class, cleanup budget), the
`rig_variant` (the named change of the pin's port rig), and the `script` of calls the case makes. The pin has no JSON tags on
these types, so values carry the Go field names. An output holds `observations`: per call the error text and which sentinel
it matches (`is_unavailable`, `is_quiesce`, `is_quarantined`, `is_stale_callback`, `is_generation_changed`,
`is_snapshot_unavailable`, `is_context_canceled`, `is_deadline_exceeded`), the host `status` (state, reason, class, epoch,
owned work, resources, stale callbacks rejected) and the rig `counts` (captures, qualifications, class calls, constructions,
closes, tokens). The cases that start goroutines record only values the pin's synchronisation fixes.

Evidence gaps. The two tests of `model161_test.go` that read the adopted 1.6.1 roster (`TestAA03RosterPin` and
`TestAA03RosterPinRejectsDrift`) skip at the pin unless a docs-semantic checkout that holds the roster with the pinned digest
is staged, and no revision of this repository holds bytes with that digest; they have no offline input and no record. The
functions that no test of the three packages drives (the client `Invoke`, the server's method and not-found refusals, the
`Digest` function) have no case. `TestAA17PackageImportsNoSDKTransportOrVendorDecoding` reads the pin's `host.go`; its record
holds the imports it reports.

## Vaillant typed-output case files

The case files of `current/gateway/cmd-gateway/vaillant-typed/` have the format `helianthus-oracle-qv07-case/1`: `component`,
`source` (the donor files under test), `stimulus` (the pin's test that supplies the input, or a statement that the case is a
synthetic native view over a named mapping function), `input` (`bytes`, `qualifiers`, `clock`, `state`) and `output`
(`decisions`, `graphql`, `mcp`, `cache`, `observations`). The recorder is the harness-only
`recorders/go/gateway-vaillant-typed/zz_oracle_vaillant_typed_*_test.go`; `record.sh` copies it into a scratch unpack of the
gateway pin and runs `TestOracleVaillantTyped` there. It calls the pin's own publication owner
(`vaillant_semantic_publication_views.go`, `vaillant_semantic_publication.go`, `vaillant_semantic_publication_fm5.go`,
`vaillant_semantic_publication_schedules.go`, `vaillant_semantic_publication_cache.go`), the field mappings of
`semantic_provider.go` and `semantic_cache.go` Load and Save, and edits none of them.

- `input.state` holds the native view (zone, hot-water, circuit, system and FM5 views, boiler and radio snapshots, native
  schedule programs, the native adapter hardware value, the cache snapshot or the cache file bytes) as the pin's own
  structures marshal it; `input.clock` holds the clock the case sets: the provider's energy clock and the cache store's clock
  (`2030-04-10T08:00:00Z`, the date the pin's own tests use). `input.qualifiers.source` says whether the view reaches the owner
  as a live or a cache publication, and in a sequence lists one source per step.
- `output.decisions` has one record per step with what the pin returns: whether a publication happened, and what remained
  published after it.
- `output.graphql` has, for each root field of the plane, the query that selects every field of its type (in name order) and the
  `data` and `errors` of the executed result against the pin's query schema over the published provider. `output.mcp.adapter`
  is the value of the pin's MCP semantic provider adapter for the plane and `output.mcp.tools` the `data`, `error` and the
  `contract`, `consistency` and `data_hash` members of `meta` of the MCP tool output of the plane, called through the pin's MCP
  server; its `data_timestamp` is the wall clock of the call and is not recorded.
- `output.cache` has, for a cache case, the bytes the pin's `Save` wrote at the case's clock (`saved_bytes`), what `Load`
  returned (`loaded_snapshot`), the native hydration value (`hydration`) and, in the seed case, the GraphQL and MCP records of a
  fresh provider after the pin's `preloadSemanticCache`; `output.observations` has the log lines the store wrote. The cache path
  is the relative name `semantic-cache.json` in an empty scratch directory, so no host path enters a record.

`circuits/circuit-managing-device-derivation` and `schedules/schedule-write-mappings` record pure mappings that publish nothing: the
first the managing device derived for every pairing of the system scheme, the function module configuration and the FM5 mode
(`output.decisions`), the second the MCP slots of a time-program request as native slots (`output.decisions`) and the native write
results as their MCP form (`output.mcp.write_results`).

`current/gateway/cmd-gateway/vaillant-typed/radio/` and `.../adapter-hardware/` hold the cases whose record carries the device
model, firmware and hardware identifier of a radio device or the hardware identity of the adapter. They are not committed: the
index entry of each has `digest_only` and the sha256 of the pin's output, and `check.py --replay current` rebuilds the file from
the pin and compares its digest.

## eeBUS service, API and consumer case files

The case files of `current/eebus-go/service/`, `current/eebus-go/api/`, `current/eebusreg/eebusreg/`,
`current/eebusreg/eebusfacade/` and `current/eebusreg/eebusservicebridge/` have the format `helianthus-oracle-qv06-case/1`, with the
members of the Modbus case format: `component` (the donor file under test and the functions it holds), `source` (the donor
file), `stimulus` (the pin's test or tests that supply the input), `input` (`bytes`, `qualifiers`, `clock`, `state`) and `output`
(`symbols_written`, `decisions`, `cache`, `observations`, `counters`). Each step of a sequence is one record of
`output.decisions` or `output.observations` with the call, the error text or the error identity the call returned, and what
the code left published or forwarded. The recorders are the harness-only `zz_oracle_*_test.go` files under
`recorders/go/eebus-go-service/`, `recorders/go/eebus-go-api/` and `recorders/go/eebusreg/{root,facade,bridge}/`; `record.sh`
copies each into the package directory of a scratch unpack of its pin and runs `TestOracleEEBusGoService`,
`TestOracleAPIConfiguration`, `TestOracleEEBusRoot`, `TestOracleFacade` and `TestOracleServiceBridge` there. They use the helper
types and fixtures of the pin's own test files, which compile in the same package, and edit none of the pin's files. A step
that depends on a certificate generated at run time, a port chosen by the host or a temporary directory records only the
facts that do not (a boolean, a length, an error identity, an error text with the directory replaced by `<sandbox>`); an
address is written as bytes and a port, never as a dotted quad.

The files are named after the donor file they record, under a group directory with the suffix `-go`:

| Pin | Donor file | Group | Stimulus |
| --- | --- | --- | --- |
| `eebus-go` | `service/service.go` | `service/service-go/` | `service_test.go`, `outgoing_attempt_bridge_test.go`, `listener_policy_test.go`, `pairing_candidate_red_test.go`, `trusted_remote_retry_red_test.go` |
| `eebus-go` | `service/service_hub.go` | `service/service-hub-go/` | `service_test.go`, `outgoing_attempt_bridge_test.go`, `pairing_candidate_visibility_red_test.go`, `pairing_candidate_visibility_dispatch_test.go` |
| `eebus-go` | `service/native_discovery_snapshot_test.go` | `service/native-discovery-snapshot/` | the four tests of that file, driven through `service_hub.go` |
| `eebus-go` | `api/configuration.go` | `api/configuration-go/` | `configuration_test.go` |
| `eebusreg` | `runtime.go` | `eebusreg/runtime-go/` | `runtime_contract_test.go`, `runtime_configuration_contract_test.go`, `runtime_lifecycle_test.go` |
| `eebusreg` | `output_binding.go` | `eebusreg/output-binding-go/` | `output_binding_test.go` |
| `eebusreg` | `internal/eebusfacade/facade.go` | `eebusfacade/facade-go/` | `facade_test.go` |
| `eebusreg` | `internal/eebusfacade/runtime_snapshot_marshal.go` | `eebusfacade/runtime-snapshot-marshal-go/` | `runtime_snapshot_marshal_test.go` |
| `eebusreg` | `internal/eebusfacade/runtime_observation_reducer.go` | `eebusfacade/runtime-observation-reducer-go/` | `runtime_observation_reducer_test.go` |
| `eebusreg` | `internal/eebusfacade/output_node.go` | `eebusfacade/output-node-go/` | `output_node_test.go` |
| `eebusreg` | `internal/eebusservicebridge/service.go` | `eebusservicebridge/service-go/` | `service_test.go`, `issue58_predial_gate_red_test.go` |

The `eebusreg` pin builds against the module version `v0.7.1-helianthus.21` of the eebus-go module, and that version has the
same `service/` and `api/` trees as the eebus-go pin, so the service bridge and the output node run the pinned eebus-go service
code. `service/service.go` also holds two tests that bind a loopback port (the listener policy cases): their records hold the
outcome (started, reachable, rebindable after shutdown, the address-in-use identity of a held port) and never the port.

Evidence gaps.

- `session/` and `discovery/` do not exist at the eebus-go pin: its tree has `api/`, `service/` and the packages of the
  eebus-go library, so there is no session or discovery vector and none is invented. The four sessions of
  `current/sessions/eebus/` stay the whole-session evidence.
- The tests of the `api/` package at the pin are one file, `configuration_test.go`. `api/api.go`, `features.go`,
  `featuresclient.go`, `featuresserver.go` and `usecases.go` declare interfaces and a few plain types, `errors.go` declares
  error values and `types.go` declares one string type; no test of the package drives any of them and no other test of the
  pin names them as an input, so they have no record. The interface method sets that `service/` implements are exercised only
  through the service records.
- The facade holds many more source files than the four that have a record. The files with a record are the ones whose pin tests
  need only the pin's own fixtures and no filesystem capability, certificate store, operator-admin session or SHIP/SPINE
  connection: `facade.go`, `runtime_snapshot_marshal.go`, `runtime_observation_reducer.go` and `output_node.go`. The remaining
  files (the first-trust, raw feature, raw mutation, remote subscription, operator admin, protected identity and runtime SHIP
  handler files) have tests in the pin that do run offline, and no record in this set; they are listed in the report as the
  facade files that still have no vector, and none is invented for them.
- Some facade tests of the pin (the `TestMSP05P*` protected-identity tests and `TestAcquireRuntime*`) read a filesystem
  capability of the host and fail with `filesystem_capability_unavailable` when the scratch directory lacks ACL inspection; their
  outcome depends on the host, so no record depends on them.

## Whole sessions

`replay_session.py --reference current --session <session.json> --output <output.json>` starts the frozen old production
path in a separate replay process: it verifies the pinned fixtures that the session names, compiles a replay executable
from the exact pinned source plus the harness-only entry files under `recorders/go/gateway-sessions/`, runs it and writes
`acquisitions`, `sends`, `publications`, `withdrawals`, `outcomes` and `public_outputs` with the portable build record
(source revision, label, build command, invocation). The toolchain with its operating system and architecture and the digest
of the replay executable depend on the host that ran the replay: they are written to a separate provenance file
(`--provenance`, default `<output>.provenance.json`; `provenance/<session>.json` for the frozen sessions) and are never part
of the output that `check.py` compares, so the same six output classes compare equal on any host. The replay executable is
not the shipped gateway CLI binary. No live hardware is used.

Published sessions: `modbus/*` (seven, below), `vaillant/poller-full-site` and `vaillant/poller-cache-hydrated-partial-reads` (the production poller on
the pinned virtual site and simulated clock), `eebus/inbound-observation-and-withdrawal` (remote observations, a profile
drift and a runtime state change) and `eebus/outbound-peer-request` (one peer request relayed through the pinned output
binding, which serves no eeBUS feature; the donor outcome is recorded as it is). The frames of one step of the Vaillant
sessions are recorded in canonical order because the production poller issues the reads of a step concurrently.

### Modbus sessions (`sessions/modbus/`)

Seven further sessions run the pinned Modbus paths whole. Each directory holds `session.json` (role `input`) and
`output.json` (role `expected-output`), indexed with `case` `modbus/<name>` and `source_entry` `gateway` (the gateway pin of
`references.json`). The harness is `recorders/go/gateway-sessions/zz_oracle_session_modbus_test.go`, with
`zz_oracle_session_modbus_rs485_test.go` for the RS-485 case (build tag `oracle_rtu_overlay`).

| Session | Pinned production path that runs | Stimuli |
| --- | --- | --- |
| `sunspec-first-incarnation` | the production SunSpec driver, producer and qualifier that `newGatewaySunSpecInstanceLiveSmokeWorker` assembles, run on the worker core with a scripted wait between cycles: `Poll` runs `Qualify` then `Refresh` on one `Adapter` over a real loopback connection, then the registered public reads (adapter getters, the MCP provider, the Portal route over the machine GraphQL runtime), then the scope fence | the register words of the frozen SunSpec chain fixture, one changed float word, the clock of `TestPVCharacterizationFirstIncarnationLegacyIdentityAndCanonicalSnapshots` |
| `sunspec-generation-replacement` | the same, over a same-epoch driver generation replacement and a later epoch replacement, each admitted after the fence of the previous scope | the words and the receipt schedule of `TestPVCharacterizationGenerationAndEpochReplacement` |
| `rs485-storage-first-incarnation` | `startGrowattBMSRS485Runtime` through `OpenRTUProductionEndpoint`, three publications and the scheduled MCP call | four FC03 windows of unit 7 per acquisition, scripted request and response frames |
| `gen3-managed-first-incarnation` | the retained Gen3 owner: completed exchanges accepted after receipt, the semantic reads, the MCP tool call, the machine GraphQL read | the exchanges and clocks of `TestTeslaCharacterizationOwnerFirstIncarnationLegacyIdentityAndPublicBytes` |
| `gen3-managed-generation-replacement` | the same owner, its generation fence, the successor registered on the retained kernel, and the repeated public reads against the successor | the exchanges of `TestTeslaHSCRetainedOwnerSuccessorFirstPublicationIsAcceptedOnTheRetainedKernel` |
| `dongle-tcp`, `logger-tcp` | the production Huawei provider over a real loopback connection, its PV publication on the hub, and the GraphQL and MCP snapshot reads | the per-endpoint `sdongle_replay.json` and `smartlogger_replay.json` register inputs; `logger-tcp` adds a lost child identity, an incomplete listing and a restoration |

How the classes are filled. SunSpec: `sends` are the FC03 requests the frozen virtual server recorded, `acquisitions` the words
returned for each, `outcomes` the qualification result of every poll and the decision lines of the worker, `publications` the
view after each poll, `withdrawals` the fence of each scope, `public_outputs` the registered reads. RS-485: `sends` are the
request frames the production endpoint wrote, `acquisitions` the observation evidence it retained (request and response frames,
transport generation, receipt instants), `publications` the three semantic publications. Gen3: the retained owner opens no
endpoint, so `acquisitions` and `sends` are empty; `outcomes` carry the exchanges it accepted and the native values it holds.
Huawei: `sends` are the request PDUs the provider wrote, `acquisitions` the response PDUs the fixture answered (an empty
response is a timeout), `outcomes` the provider cycles with their per-child evidence, withheld reasons and exchange attempts,
`publications` the published assets, `withdrawals` the assets that left, `public_outputs` the snapshot reads.

Gen3 cross-link. Each Gen3 `session.json` carries `raw_active_transport_arm`: the separate raw active-transport sequence the
consumer drives at its own active Open path. It is stimulus only. The pinned owner transmits nothing, so none of its frames is a
donor transmission, and a coincident configured-current value from that arm grants no equivalence of wire, receipts, identity or
time. The output records the digest of the block, so a changed arm changes the output. Unknown in that block, and listed there as
such: the response terminal frames of the ordinary reads (the pinned test builds them with an unexported helper) and the declared
t28 read window (neither the pinned fixtures nor the public page state one).

Harness seams, each harness-only and none an edit of production code:

- The SunSpec sessions compose the steps of `startModbusInstanceRuntimeWithPublication` (the production configuration mapping,
  the PV class of the hub, the publication scope, `modbusadapter.Start`) and add the injected clock that
  `TestPUBLIC05SunSpecSemRegSurvivesGatewayProvidersAndPortal` also injects, because that function takes no clock and would stamp
  every publication with the host's wall clock. The frozen helper `ServeSunSpecChain` binds an ephemeral port that enters the PV
  source identity, so the harness serves the same words with the same request recorder on the fixed loopback port that
  `endpoint_port` names.
- The RS-485 session runs `startGrowattBMSRS485Runtime` and its real `OpenRTUProductionEndpoint` in a replay executable built
  with a scratch copy of the module version the gateway `go.mod` pins (`recorders/go/overlays/helianthus-modbus-rtu/`). The copy
  is byte-identical except two operands of `rtu_production.go`: the `OpenRTUSerial` call returns the scripted stream, and the
  receipt wall-clock sample returns the clock of the session. The digest of the file before and after the change, and of the
  added hook file, are part of the `build` record of the output.
- The Huawei sessions draw the random incarnation identity of the hub from a fixed seed named in the session (`crypto/rand` is
  replaced only while the hub is constructed). The pinned Huawei publication reads the host wall clock once, for the start
  instant of its source, and covers that instant in the digests of the snapshot; those values are recorded as
  `host-clock-dependent` and every other field is recorded as the pin produced it.
- The SunSpec sessions bind the fixed loopback port of `endpoint_port`, because the endpoint string is part of the recorded
  identities. Two replays of a SunSpec session on one host at the same time, or a host process that holds the port, make the
  replay fail with a bind error; run them one after another.
- A pinned fixture that a session names and the pin lacks makes `replay_session.py` exit with status 3 and name the missing
  operand; `check.py --replay` then reports that session as incomplete.

## Pre-port typed queries, MCP tools and canonical PV v1

Recorded at the last 0.6 release of the gateway (`pre-port` entry `gateway`) by the harness-only sources under
`recorders/go/pre-port-typed/{graphql,mcp}/`, which are copied next to the pinned tests and use their helpers (the
registry, provider, invoker, schedule-writer and mutation-schema helpers); nothing in the pin is edited.

- `graphql-typed-queries.json`: `complete` holds, for each typed root query (`zones`, `dhw`, `circuits`, `radioDevices`,
  `fm5SemanticMode`, `solar`, `cylinders`, `energyTotals`, `boilerStatus`, `system`, `schedules`, `adapterHardwareInfo`, and
  the snake-case root aliases) the query text, which selects every argument-free field the introspection lists, and the
  answer for a provider in which every field of `semantic.go` holds a synthetic value (counter-derived, deterministic; the
  fixed instant of the time fields is in the recorder). `pin_cases` holds the answers on the fixtures the pin's own tests
  use: the default provider (empty, `null` and `ABSENT` answers), the zone of `zones_dhw`, the managing device of the circuit
  case, the removed `vr71CircuitStartIndex` field, the energy no-data and with-values cases (the host-clock observation
  time and age are not selected), the schedule program, and the boiler status of the pin's MCP boiler case (flow 52.5,
  return 47.0, pump on, heating status 2), which is the only boiler fixture of the pin.
- `graphql-typed-mutations.json`: every mutation of `mutations.go` that a test of the pin drives, with the request, the
  answer, and the calls the invoker or writer received (register parameters in hexadecimal): circuit, system and boiler
  config, zone and DHW time programs, the validation, read-back, missing-controller, missing-method and source-admission
  failures, and the direct `ApplyConfigMutation` call. `setZoneConfig` has no test in the pin; its one case runs on the
  controller fixture of the circuit case and is marked as a harness fixture.
- `mcp-typed-tools.json`: `tools/call` of each semantic tool (`zones`, `circuits`, `radio_devices`, `fm5_mode`, `solar`,
  `cylinders`, `dhw`, `energy_totals`, `boiler_status`, `system`, `schedules`, `adapter_info`, `snapshot.get`) on the
  complete synthetic provider (`complete`), on a server without provider, on the providers of the pin's semantic snapshot
  cases (`pin_cases`), and the five write tools (schedule and config writers, `write_cases`) with the calls the writers
  received. The envelope's `data_timestamp` is the host wall clock and is not recorded; `runtime_status` is not selected in
  `snapshot.get` because it reports the host process.
- `losses.json` keeps its 69 entries and `pre_port_vector` (the introspection entry). Each entry gains
  `pre_port_value_vector` (a pointer into the typed GraphQL vector with the value shown), `pre_port_mcp_value_vector` (the
  semantic MCP tool answer), and, where a fixture of the pin's own tests sets the field, `pre_port_pin_fixture_vector` and
  `pre_port_mcp_pin_fixture_vector`. `BoilerState.flowTemperatureC` shows 52.5 in all four: the value of the pin's MCP
  boiler fixture. The values of the other fields come from the complete synthetic provider because no test of the pin sets
  them; they show what the pre-port resolver publishes when the provider holds a value, not a field observation.

Recorded at the parent of the PV cutover (`pre-port` entry `gateway-canonical-pv`) by
`recorders/go/pre-port-canonical-pv/{modbusadapter,mcp,m2mgraphql}/`:

- `canonical-pv-mapper.json`: `CanonicalPVMapper.Map` and the SemReg shadow (`canonical_pv_semreg_shadow.go`) on the qualified
  inverter observation the pin's mapper test serves on a loopback endpoint, at the fixed endpoint of the recorded identities
  (`tcp://127.0.0.1:20502`), a fixed evaluation instant (100 ns), a fixed production time and a fixed entropy stream, the
  adapter's host clocks not being used. The register payloads of the observation are not recorded (they carry the device
  identity strings of the Common model); the sha256 of the whole encoded observation is. Two replays on one host at the same
  time, or a host process that holds that port, fail with a bind error.
- `mcp-canonical-pv-envelope.json`: the retained canonical envelope of the pin's golden test, the sha256 of
  `mcp/testdata/modbus_v1_canonical_pv.golden.json` and the check that the two are equal.
- `m2m-canonical-pv-contract.json`: `m2mgraphql/testdata/contract.json` with its sha256, and the answers of the pin's handler:
  the served snapshot, the asset not allowed, the asset without snapshot, the `GET`, the generic route and the subscription.

Pre-port surfaces that no test of the pin drives: the GraphQL `boilerStatus` and `adapterHardwareInfo` roots (and their
snake-case aliases), the `setZoneConfig` mutation, and the typed values of 67 of the 69 lost fields (all but
`BoilerState.flowTemperatureC` and `DhwConfig.operatingMode`); the vectors record them on the harness fixtures stated above.
No test of the pin drives the MCP `schedules` tool with a populated provider; the `adapter_info` fixture is the one of the pin's snapshot consistency case.

## Commands

Environment: `ORACLE_DONOR_ROOT` is the directory that holds one clone per `slug_at_pin`; `GOMODCACHE` holds the public module
sources. No network is used. Module versions the cache lacks are served to the Go tool from a scratch proxy built from the
extracted cache or the donor clones, and `go.sum` verifies them.

- `acceptance/oracle/record.sh <reference>` unpacks each pin under `.tmp/`, places the recorder sources, runs them and writes
  the vectors. With `--replay` every actual output goes under `.tmp/oracle-replay/<reference>/` and never into
  `acceptance/vectors/`.
- `python3 acceptance/oracle/check.py --index` verifies every vector payload against `index.json` and every file-backed
  index entry against its file.
- `python3 acceptance/oracle/check.py --replay <reference>` verifies the sha256 of every input entry, re-records the
  reference, runs every indexed session, and compares every `expected-output` entry byte for byte with the committed file or,
  for a digest-only entry, with the frozen digest. A missing, changed or extra actual output exits nonzero. For each binary
  it requires the delivered file and an independent rebuild to have the recorded SHA-256. The `go install` form has no
  `-trimpath`, so its executable embeds the Go root and module cache paths of the host that built it. When the rebuild
  differs from the delivered file, the comparison sets only those paths aside: it requires the same toolchain version,
  module graph with hashes and build settings, section list, symbol table (names, kinds and sizes, except the size of the
  string that holds the Go root path), byte-identical path-free sections and the same bytes in `.text`, `.rodata`,
  `.noptrdata` and `.data`, where only the shift of the layout (the Go root string changes length) is set aside: a word
  that holds an address may differ by exactly the distance its target symbol moved, and the Go root string and the
  variable that points at it are not compared.
- `python3 -m pytest acceptance/oracle/test_oracle_checks.py` checks the SunSpec native records and that rebuild comparison.
- `python3 acceptance/oracle/check.py --record-can-native current` checks the six cases in `index.json` (origin, reference, role,
  case id and platform of each file, and its sha256) and the gateway pin, runs the cases of the native platform of the host
  (the four Linux cases on Linux, the two unsupported cases on any other host) and writes the actual tree only under
  `.tmp/oracle-can-actual/current/linux/` or `.tmp/oracle-can-actual/current/nonlinux/`; the recorder's own unpack and build
  scratch is under the scratch root of `record.sh`. It then compares the tree with the frozen expectation. A run whose Go target is
  not the host's own is refused. `record.sh` does not run these cases: the replay of `current` takes both trees from the
  collected directories. `check.py --replay current` fails when either tree is absent, holds a receipt of another platform,
  revision, recorder, index or pin, whose pinned source digests differ from the pin, carries no host and target metadata, was not run natively, has a failed status, or lacks, adds or changes a case.
- `python3 acceptance/oracle/check.py --restart` compares the two lifecycles of `current/restart/` (see the restart files).

## Sources

Only public fixtures and synthetic inputs are committed. A private capture appears only as its sha256 digest. The charger
vendor's corpus is not a source. Sources are read for facts only.
