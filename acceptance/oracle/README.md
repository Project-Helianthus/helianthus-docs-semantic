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
| `current/gateway/cmd-gateway/ss02/` | native records of the Vaillant hot-water mappers and of the gateway Growatt CAN receive path | recorded-current |
| `current/canbusreg/canbusreg/ss02/` | native records of the registry Growatt CAN classifier | recorded-current |
| `current/modbusreg/sunspec/ss02/` | native records of the SunSpec decoder and monitoring capability on the Model 103 W and W_SF operands, with each fact's number, enum number and symbol, or bits and bit symbols | recorded-current |
| `current/gateway/adaptermux/` | case files of the multiplexer: `transition/` (every fixture and input of the state transition table), `arbitration/` (bid selection at the SYN boundary), `send-symbols/` (escape pairs of the gateway write path), `v8classifier/` (classifier modes, event sequences and admin events), `pacer/` (output cadence, echo samples, grace and deadlines) and `ptytest/` (the pseudo-terminal pair and the serial multiplexer open, absent device and reopen) | recorded-current |
| `current/gateway/localworkerhost/` | case files of the local worker supervisor: argv plan, child environment, child and configuration validation, report encoding and the lifecycle; `supervisor/` holds report fences, leases, restart, failed launch, stop escalation, unexpected exit, duplicate child and allocator mismatch | recorded-current |
| `current/gateway/engine/` | case files of the six engines (`scheduler/`, `shadow-cache/`, `passive-tap/`, `deduplicator/`, `reconstructor/` with the F19c helpers) and of the closure that moves with them (`watch-catalog/`, `observe-first-flags/`, `observe-first-family-policy/`) | recorded-current |
| `current/gateway/matter/` | case directories of the Matter target projection: `projection/` (`projection.go`: the ledger, the exact milliampere conversion, eligibility, the end to end projection, rejections, several contributors and the mapped key) and `model161/` (`model161.go`: the 1.6.1 projection and its canonical output checks); each case is a directory with `input.json` and `output.json` | recorded-current |
| `current/gateway/matter-feedv1/` | case directories of the binding feed: `server/` (lifecycle and admission, detachment and strict rejection, concurrent capture), `client/` (public wire contract, typed resync), `schema/` (closed objects and wire members), `corpus/` (valid and invalid wire values against the published schema) and `embedded-generation/` | recorded-current |
| `current/gateway/matter-libraryhost/` | case directories of the library host lifecycle: `lifecycle/`, `unavailable/`, `rows/`, `port-failure/`, `factory/`, `stamp/`, `restart/`, `token/`, `start/`, `stop/`, `close/`, `cancel/`, `generation/`, `project/` and `imports/` | recorded-current |
| `current/semreg/semreg-v1-graph/` | the catalog bytes embedded in the SemReg enforcement source and their sha256 | recorded-current |
| `current/sessions/<family>/<case>/session.json` | the published input of a whole session | synthetic |
| `current/sessions/<family>/<case>/output.json` | the frozen output of that session on the old process | recorded-current |
| `pre-port/gateway/` | GraphQL introspection (lists in name order) and MCP tool list of the pre-port gateway | recorded-pre-port |
| `pre-port/losses.json` | pre-port GraphQL fields the current introspection does not publish (a derived comparison) | recorded-pre-port |
| `spec/` | independent protocol bytes for generic Modbus writes | specification |
| `specification/` | SI and specification expectations of the SS02 cases, kept apart from the recorded vectors | specification |

A recorded vector carries the input it was recorded from and every output the code produced. A specification vector cites
document, version and clause or register and never the text. A vector that carries an identifier the eBUS bus transmits is
not committed; its recorder is, and its index entry keeps the frozen digest (`digest_only`). No such vector exists in this
revision.

## Engine, adaptermux and local worker case files

Each case file of `current/gateway/adaptermux/`, `current/gateway/localworkerhost/` and `current/gateway/engine/` has the
format `helianthus-oracle-bt01-case/1`: `component`, `source` (the donor file), `stimulus` (the pin's own test that supplies
the input), `input` (`bytes`, `qualifiers`, `clock`, `state`) and `output` (`symbols_written`, `decisions`, `cache`,
`observations`, `counters`). The recorders are the harness-only `zz_oracle_*_test.go` files under
`recorders/go/gateway-adaptermux/`, `recorders/go/gateway-localworkerhost/` and `recorders/go/gateway-engine/`; `record.sh`
copies them into a scratch unpack of the gateway pin, runs `TestOracleAdapterMux`, `TestOracleLocalWorkerHost` and
`TestOracleEngine` there and writes the case files. A case that varies a field of its input records every field it varies.
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

Published sessions: `vaillant/poller-full-site` and `vaillant/poller-cache-hydrated-partial-reads` (the production poller on
the pinned virtual site and simulated clock), `eebus/inbound-observation-and-withdrawal` (remote observations, a profile
drift and a runtime state change) and `eebus/outbound-peer-request` (one peer request relayed through the pinned output
binding, which serves no eeBUS feature; the donor outcome is recorded as it is). The frames of one step of the Vaillant
sessions are recorded in canonical order because the production poller issues the reads of a step concurrently.

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
- `python3 acceptance/oracle/check.py --restart` compares the two lifecycles of `current/restart/` when they are recorded.

## Sources

Only public fixtures and synthetic inputs are committed. A private capture appears only as its sha256 digest. The charger
vendor's corpus is not a source. Sources are read for facts only.
