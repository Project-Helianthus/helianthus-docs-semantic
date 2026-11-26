---
status: "candidate sealed-manifest tool; receipts stay empty until destination acceptance, and a deletion list requires the approved row and whole-session comparisons"
---

# Sealed move manifests

`acceptance/tools/manifest/main.py` publishes the manifest for one queue row and checks it.
`generate`, `receipt` and `deletion` write under `acceptance/manifests/`.
`check` and `compare` do not write manifests, sealed lists or expectations, and neither command regenerates an expected output.

The manifest records the donor commit, one sealed path list per repository, the moved symbols and the assertions that transfer with them, the pattern signature of each mapping row, the destination of each symbol and transferred assertion, the independent expectations, the approved expected-difference vectors, and the receipts.
Receipts are empty at generation.
A candidate manifest is published before destination acceptance.
Final merged receipts are published before any donor deletion.

`acceptance/oracle/check.py --replay` re-runs a reference pin and compares the reference vectors.
It does not run a destination commit and it is not `compare`.
See [the oracle](../../oracle/README.md).

## Commands

Generate from a JSON input:

```
python3 acceptance/tools/manifest/main.py generate --input <spec.json> --donor <donor-checkout>
```

Generate a move that has no mapping row from flags.
The flag form takes no exemplar, no new file, no shared file and no historical specimen unless `--specimen <test-name>` is repeated.
`<donor-sha>` is the full donor commit.
The donor checkout must contain that commit; its HEAD may be a later commit.

```
python3 acceptance/tools/manifest/main.py generate \
  --row BT01-sample \
  --donor-repository gateway \
  --donor-sha <donor-sha> \
  --donor <donor-checkout> \
  --move semantic_read_scheduler.go=ebusgo:engine/semantic_read_scheduler.go \
  --move shadow_cache.go=ebusgo:engine/shadow_cache.go \
  --move passive_bus_tap.go=ebusgo:engine/passive_bus_tap.go \
  --move active_passive_deduplicator.go=ebusgo:engine/active_passive_deduplicator.go \
  --move passive_transaction_reconstructor.go=ebusgo:engine/passive_transaction_reconstructor.go \
  --move passive_reconstructor_f19c_helpers.go=ebusgo:engine/passive_reconstructor_f19c_helpers.go
```

`--move` is `<donor-path>=<destination-repository>:<destination-path>` and may be repeated.

```
python3 acceptance/tools/manifest/main.py check --manifest acceptance/manifests/<row>.json --donor <donor-checkout>
python3 acceptance/tools/manifest/main.py compare --manifest acceptance/manifests/<row>.json --destination <destination-checkout>
python3 acceptance/tools/manifest/main.py receipt --manifest acceptance/manifests/<row>.json --input <result.json> --repository-checkout <repository>=<checkout>
python3 acceptance/tools/manifest/main.py deletion --input <deletion.json> --gateway <gateway-checkout>
```

`check` reads the donor checkout and the immutable objects named by the manifest.
It does not read a destination checkout and it cannot see a destination regression.
`compare` is the command that executes the destination.
`--repository-checkout` may be repeated, once per destination repository in the result.

A failing `generate`, `receipt` or `deletion` writes nothing.
Failure lines are unique and sorted.
`check` prints `check: ok` on success.
`compare` prints a result for each bound case, transferred assertion and whole-test comparison, then `compare: ok` on success.
A move whose `patterns` list is empty still runs each transferred assertion at its recorded destination test.
When the manifest declares transferred assertions and none of them ran, `compare` fails with `not-executed move=<row>` and does not print `compare: ok`.

## Whole-test comparisons

A donor test that stays and exercises moved behaviour can be bound to its destination test without treating the donor file or test as moved. A test already listed as a moved symbol can also opt into whole-test comparison, using its recorded destination name (including a rename).

In the generator input, `test_comparisons` entries have `file` and `name` for the donor test, and `repository`, `path` and `test` for the destination. The donor identity must match a `test` under `stays` or a moved test symbol. The destination path must be sealed for that repository, and a moved test's destination must agree with its symbol mapping. `generate` writes each binding under `destinations` with `kind: "test"`; it does not change the closure classification. For a bound retained test it also records `moved_uses` under `stays`: the moved symbols reached by that test. `check` recomputes those uses from the donor. `compare` has no donor checkout, so it checks that the recorded uses are nonempty and refer to symbols in the move before it runs the destination test.

`compare` runs each exact named Go test in its recorded file and reports its own invocation status. An absent, skipped or failing test does not pass. These runs check the whole test's own assertions; they do not substitute for transferred-assertion diagnostics or independent vector comparisons.

## Symbol-level moves

A whole-file move (`moves`) takes whole donor files from one directory and one package.
A symbol-level move states the symbols instead.
It may span donor packages, the rest of each donor file stays in the donor, and a symbol may be renamed at the destination.
`moves` and `symbol_moves` are not given together; `generate` fails with `moves-and-symbol-moves`.
A whole-file input behaves as before and writes the same bytes.

The input adds two lists:

```
"symbol_moves": [
  {
    "package": "<donor directory>",
    "path": "<donor file in that directory>",
    "symbol": "<name, or Type.Method>",
    "destination_repository": "<repository>",
    "destination_path": "<destination file>",
    "destination_symbol": "<name at the destination, optional>"
  }
],
"stay_symbols": [
  { "package": "<donor directory>", "path": "<donor file>", "symbol": "<name, or Type.Method>" }
]
```

`package` is the donor directory.
`destination_symbol` defaults to `symbol`, so a rename is the only case that sets it. A rename that is only white space fails with `invalid-destination-symbol`, since `check` reads it as no name.
`specimens` names a donor test as a bare test name, or as `{ "name": "<test>", "file": "<donor test file>" }` (the flag form takes the bare name). A bare name stands for the one test of that name; when two donor tests carry it (two packages, or a package and its external test package) the input fails with `ambiguous-specimen: <name>` and one entry per test, with its file, is required. `check` reads the recorded `file` of each specimen, so a specimen never stands for a second test of the same name.

A symbol is a top-level function, type, var or const name, or a method written `Type.Method`.
Which symbol an identifier refers to, and which package it belongs to, comes from Go's own name resolution and not from a reading of the syntax: `closure.py` runs the helper program in `gotypes/` (`resolve.go` and `flow.go`, standard library only, started as `go run`), which type-checks the donor at the commit with `go/types` and prints JSON, and `closure.py` classifies what the helper reports.
The helper reports, for every package-level declaration of the donor directories the input names and of the directories that hold tests of them, the declared symbols it uses: types, functions, methods with their receivers, variables and constants, including uses through method expressions, composite literals (nested and elided ones too), type switch cases, generic instantiations, qualified names, dot imports and imports written as a raw string or with a name.
A field label, a parameter, a receiver, a local binding, a type parameter, a label and a package name are never symbols.
A method call or method expression is a use of `Type.Method` whatever the receiver value is (a parameter, a local, a composite literal or a call result), and a promoted method is a use of the method of the type that declares it; a method of an interface is a use of the interface type.
A constant specification written without a type and an initializer repeats the preceding one and uses what that one uses.
The resolver type-checks the Linux/amd64 build without cgo. A Go file that build excludes in a donor directory the move names, or in a directory with tests that reach the move, is accounted for in the first other build that includes it: the fewest custom tags its constraint names first, and for each choice of tags the Linux platform on other architectures, then other operating systems (`ignore` is never a tag that is set). It is type-checked there with its package, and its declarations and tests are classified as those of the Linux build are. A file that no build includes, that imports `C`, whose package clause differs from the package it belongs to, or whose package does not type-check in its build is reported as `unsupported-build-file` and fails the move.
An external test package is checked against the package under test with its internal test files, and a donor package that imports the package under test is checked against that same variant, as the toolchain builds a test binary.
The standard library is read from the toolchain's source, for the platform of the build being checked. The packages of the donor's pinned dependencies are type-checked from the module versions the donor's `go.mod` requires (after its `replace` directives), read from the Go module cache (`GOMODCACHE`, else `go env GOMODCACHE`), without their test files and function bodies. A dependency whose module directory is not in the cache is represented by an empty package, and a selector in a moved declaration whose receiver cannot be resolved because of it is reported as `unresolved-selector`, not as an `outside-set` use of a same-named donor method. Declaring such a method as staying does not resolve the receiver. A checked package whose imports all resolve and that still does not type-check fails with a `type-error: <directory>: <message>` line. A checked Go file that does not parse fails with a `parse-error:` line.
The Go toolchain is required for a symbol-level `generate` and `check`. When `go` is not found or the helper fails, the tool fails with a `go-resolver:` line and writes nothing; it does not read the Go source in another way. The whole-file input does not use the helper and its closure is unchanged.

A moved symbol may use a moved symbol, or a symbol that `stay_symbols` declares.
Any other declared symbol it uses fails the move as one `outside-set: <name>` line, sorted and unique across the whole input. A symbol of the package is written `<name>` or `<Type>.<Method>`, a symbol of another donor directory is written `<directory>.<name>` (the module root is `.`), whether or not any entry of the input names that directory. A moved symbol of another directory is recorded in `uses` as `<directory>.<name>`.
A symbol declared in an external test package `package p_test` is a symbol of that package, apart from a symbol of the same name in the directory's package, and the tests that use it are accounted against it (both cannot be listed in one input: `duplicate-symbol`).
The methods of a moved type are its siblings: each one is moved or declared staying, otherwise `outside-set: <Type>.<Method>` names it.
`generate` also fails, and writes nothing, for:

| Line | Cause |
| --- | --- |
| `absent: <path>` | The file is not in the donor commit |
| `absent-symbol: <path> <symbol>` | The file does not declare that symbol |
| `package-mismatch: <path>` | The file is not in the directory named by `package`, or files of one directory carry another package clause |
| `duplicate-symbol: <path> <symbol>` | The same symbol is listed twice as moved, or twice as staying |
| `moved-and-stays: <path> <symbol>` | The same symbol is both moved and staying |
| `ambiguous-assertion function=<f> assertion=<a> package=<p>` | Two donor packages hold a moved-only assertion of that function and name and the input names it without `package`, or one donor directory holds two, even if both checks are in the same function and file |
| `unsupported-build-file: <path>` | A relevant Go file is excluded from the resolver's build and from every other build it tries, or its package does not check in that build |
| `unresolved-selector: <path> <symbol>.<selector>` | A moved declaration uses a selector that cannot be resolved to a receiver member |
| `conflicting-assertion function=<f> assertion=<a>` | The input gives one donor assertion (function, name and package) two entries with different destinations; no entry order is right, so nothing is written |
| `invalid-destination-symbol symbol=<package>:<symbol>` | A `destination_symbol` that is only white space |
| `ambiguous-specimen: <name>` | A specimen given as a bare name that two donor tests carry |
| `invalid-specimen: <entry>` | A specimen that is neither a test name nor an entry with a name (and, optionally, a file) |
| `missing-destination symbol=<package>:<symbol>` | A symbol move names no destination repository or no destination path; `check` rejects such a move, so `generate` refuses it first |
| `go-resolver: <reason>` | The Go toolchain is missing or the helper failed |
| `type-error: <directory>: <message>` | A donor package whose imports all resolve does not type-check |
| `parse-error: <message>` | A Go file of a checked donor package does not parse |

Donor tests are accounted as for a whole-file move, per donor package: a test that uses only moved symbols is `left-behind` unless it is a specimen, and a mixed test needs its moved-only assertions in `assertions` with a destination.
What a test uses is what the helper reports for it: the declared symbols its body names, and for each of its checks (the `if` statements of the body that call `Error`, `Errorf`, `Fatal`, `Fatalf`, `Fail` or `FailNow`) the symbols the check names and the symbols of the statements that give the locals it reads their values, where those statements can reach the check. The reach is read from the control flow of the test: an assignment on a branch that returns or ends the test before the check (`panic`, `t.Fatal`, `t.Fatalf`, `t.FailNow`, `t.Skip`, `t.Skipf`, `t.SkipNow`, `os.Exit`, `runtime.Goexit`), or that a later assignment replaces, does not change what the check exercises. A declared type of a variable is not a value it was given, so `var r T` brings in nothing.
A direct write through a local pointer to a known local variable counts as a definition of that variable. Copies and reassignments of such pointers follow the same control flow as other local definitions.
A test that reaches a donor symbol through a helper that its package declares in a test file uses that symbol, even when the import is in another file than the test, and the helper itself is a symbol that stays, so a test of that kind is mixed and is accounted (`stays` or `assertions`).
Every donor symbol that is not moved stays: one the input declares, one of a donor directory the input does not name, and one a test package declares for itself, so a test with a moved and a staying check is mixed whether or not the staying symbol is named in the input.
Tests are read for the directories the input names (the package, its internal test files and its external test package `package p_test`) and for every other donor directory with a test file or package files that import a directory of the move directly or through other donor packages (a value of a moved type can only come through such a chain, so a test that calls its method need not import the package); `package` on an assertion is the directory of the test file.
An `assertions` entry may carry `package` (the donor directory); it is required when two packages hold an assertion of the same function and name. The manifest then records `package` on that assertion and on its destination, and `compare` runs and tracks each separately.
A moved test function is a moved symbol and is not accounted again.

The manifest keeps the same keys and order.
Only these records differ:

| Key | Symbol-level record |
| --- | --- |
| `symbols` | `name`, `file`, `uses`, `package`. Sorted by package, file and name. A name may repeat in two packages. |
| `stays` | The declared staying symbols are `kind` `symbol`, with `name`, `file` and `package`, next to the test and specimen records |
| `destinations` | A symbol is `kind` `symbol`, with `name`, `package`, `repository`, `path` and `destination_name`. `destination_name` is the donor name when nothing was renamed |
| `paths` | The donor list holds each file that has a moved symbol, so a file that only gives part of itself is listed whole |

`check` recomputes the closure from the donor, the moved symbols and the declared staying symbols of the manifest, and fails on a changed symbol set (including a manifest whose `symbols` were removed while symbol destinations or declared staying symbols remain: `symbol-set`), a changed `uses`, a removed staying declaration (`outside-set`), a symbol without exactly one destination (`missing-destination symbol=<package>:<name>`), a symbol destination with no recorded symbol (`unmatched-destination symbol=<package>:<name>`), a symbol destination that is not in the sealed list of its repository (`unsealed-destination: <repository>:<path>`), a donor repository without a sealed list (`unsealed-donor: <repository>`) or a moved donor file that the sealed list of the donor does not hold (`unsealed-source: <repository>:<path>`).
`compare` is unchanged: it executes the transferred assertions and the bound cases, and fails with `not-executed` when they did not run.
`deletion` never counts a symbol-level manifest as covering a donor file, whether the file is partly moved or only listed as shared: a finding of the debt list for such a file is answered `partial-move: <path>` and no list is written, unless a whole-file manifest covers it. A manifest whose `symbols` were removed but that keeps symbol destinations or declared staying symbols is still a symbol-level manifest.

## Manifest

`<row>.json` keeps this key order:

| Key | Contents |
| --- | --- |
| `row` | Queue row id |
| `donor` | `repository` and full `sha` |
| `paths` | One entry per repository: `repository`, sorted literal `paths`, `sha256` of that sealed list, and `donor_sha` |
| `symbols` | Moved symbol, its file at the donor commit, and the moved symbols it uses |
| `assertions` | Transferred assertion: `name`, `file`, holding `function`, and `helpers` |
| `stays` | Mixed host assertions and historical specimens. No destination |
| `patterns` | Empty when the set has no mapping row |
| `destinations` | Destination repository, path and, for an assertion or a case, the existing Go test name |
| `expectations` | Pinned case, row bindings, inputs, selectors and references |
| `expected_differences` | Empty, or exact approved difference vectors |
| `receipts` | Empty at generation |

A pattern entry holds `row`, `kind` (`donor-backed`, `specification` or `binding`), `old_symbol`, `bom_entry`, `cases`, `assertion`, `signature`, `candidate` and `exemplar`.
Any other kind is rejected. The error names that kind. `generate` writes no manifest, and `check` and `compare` fail the manifest.
`exemplar` is `repository`, `path` and the full `revision` of the row that matched.
A donor-backed row names the old symbol and the BOM entry.
A specification-only row, including a register acquisition and a command witness, has an empty old symbol, an empty BOM entry and no donor output.
A binding row names three references and no donor output: donor native fields, the new-binding expectation (`key`, `subject`, `value`) and the caller template.

`candidate.form` is `inline` or `reference`.
Inline operands are stored on the manifest.
A reference is `repository`, full `revision`, `path` and `row_key`, plus the object recorded from the tool checkout.
The reference document is a JSON object whose `rows` map selects that key.
Its operands are the row's concrete operands, not a copy of the exemplar.

An expectation holds `case`, `kind`, `rows`, `inputs`, `selectors` and `references`.
Each row binding is `row` and `assertion`.
When one case exercises several rows, the binding may also carry the `selectors` that belong to that row alone (for example `valueType` when two rows share one `measurementId`).
`inputs` holds `raw`, `qualifiers`, `clock` and `state`.
A reference holds `role`, `repository`, full `revision`, `path`, `blob_sha256` and `projection`.
Roles are `donor-native`, `new-binding`, `caller-template`, `donor-output`, `specification`, `expected-difference` and `candidate`.

`new-binding` has `key`, `subject` and `value` and no template fields.
`caller-template` has `origin`, `quality`, `source`, `timing` and `provenance`.
`donor-native` preserves the donor fields and does not invent a binding.
`donor-output` has `fields` and may have `status`.
`specification` has `fields`, `inputs` and `selectors` and must not carry `status`, `donor_output` or `donor_symbol`.

An approved difference has `case`, `field`, `old_present`, `old`, `new`, `source`, `approval` and its reference.
`old` or `new` of `*` is rejected.
`old_present: false` is a frozen old absence with the approved new value.
An absence whose field is already pinned by a reference for that case is rejected and does not replace that pin.
The same case and field, the same source and approval, and the same old and new values must be in the referenced object.

## Destination test identity

`destinations` records, for each moved symbol, each transferred assertion and each pinned case, the destination `repository`, `path` and the existing behavior-named Go test.
The test name is the Go function already present in that destination file.
A retained `stays` entry has no destination.
`check` requires one destination of kind `case` for each bound case.
That entry must name `repository`, `path` and `test`.
A missing or ambiguous entry fails and names the case, the row and the assertion.

`compare` resolves every case binding and every transferred assertion through that entry and runs that one test by its exact name, once per assertion, including when `patterns` is empty:

```
go test -count=1 -v -run ^<TestName>$ <package>
```

`<package>` is the directory of the destination path, or `.` when the path is at the repository root.
Two assertions that share a file and a package are two invocations.
A package status is not an assertion result.
An invocation that does not run the named test fails, including when the package exits 0 because the function is absent.

The invocation receives `MANIFEST_CASE`, `MANIFEST_ROW`, `MANIFEST_ASSERTION`, `MANIFEST_RAW`, `MANIFEST_QUALIFIERS`, `MANIFEST_CLOCK`, `MANIFEST_STATE`, `MANIFEST_ORIGIN`, `MANIFEST_QUALITY`, `MANIFEST_SOURCE`, `MANIFEST_TIMING`, `MANIFEST_PROVENANCE` and `MANIFEST_PINNED_FIELDS`.
Pinned field values are the manifest's expectations, not values regenerated from the test.
Two references that pin different values for one field are rejected. An approved vector does not replace either pin, and an absence approval does not replace a field a reference for that case already pins.
The test prints its own identity, the inputs it actually used, the template metadata it actually attached, and one line per compared field:

```
MANIFEST_RESULT case=<case> row=<row> assertion=<assertion>
MANIFEST_INPUT raw=<raw> qualifiers=<qualifiers> clock=<clock> state=<state>
MANIFEST_META origin=<origin> quality=<quality> source=<source> timing=<timing> provenance=<provenance>
MANIFEST_FIELD field=<field> expected=<expected> observed=<observed>
```

Tokens do not contain spaces.
`compare` prints `outcome assertion=<assertion> test=<test> invocation-status=<status> case=<case> row=<row> result=pass` or `result=fail`, then the field lines it captured.
A native field is the pinned donor value against the observed value.
`binding.key`, `binding.subject` and `binding.value` are the independent new-binding expectation (the value is the exact decimal, such as `298.15`).
`template.origin`, `template.quality`, `template.source`, `template.timing` and `template.provenance` are the caller template supplied to that invocation.
Native equality does not pass a binding case whose binding operand was not executed.
A wrong input fails even when the output field still matches.
A missing field line, a missing test, or an observed value that is not the pin and not the approved new value fails and names the case, the assertion and the field.

## Pattern signature

A signature is the selector geometry plus the inverse pattern.
Concrete feature, function and description values are operands.
They do not make a new signature.
The signature matches an exemplar only when it equals the signature of a row in the exemplar file the manifest names.
Another path at the same revision does not stand in.
A stale, missing or different signature fails and names the row.

Selector fields are the service's typed address and the request or reply shape: eBUS command, operation, group, instance, register and direction; Modbus function, table, block or model occurrence, word offset and count, or the legacy command, direction, decoded length and byte offset and count with no inverse; CAN identifier, format, raw and effective DLC, route, direction, byte order and slice; SPINE driver instance, remote device, entity, feature type, function and the description keys that pick one data entry.
Measurement also carries `valueType`.
The remote LoadControl command adds the phase join, the same-keyed disable and the same-instance readback.
TimeSeries delete uses the same-slot readback.
IncentiveTable uses the same-tariff readback.
Those inverses are not interchangeable.

Exemplar files are either a JSON object with a `rows` map, a JSON object with a `signature`, or Go source with one `QQ06ROW` JSON object per line:

```
// QQ06ROW {"id":"<row>","signature":{"family":"spine","inverse":"none","selector_fields":["entity"]}}
```

`generate` reads the exemplar commit from the donor checkout.
`check` reads that same `revision:path` from the donor checkout.

## Sealed lists

`acceptance/manifests/<row>.<repository>.lst` is one repository.
One literal repository-relative path per line, sorted, no glob, LF line ends.
The donor list is the moved files plus the shared files granted in the donor repository.
Each destination list is the destination path of each move into that repository, the new files, and the shared files granted there.
The `sha256` of those exact bytes is stored with the repository and the donor commit.
`check` requires the sibling list to match.

## Receipts

`<result.json>` carries `repository`, `kind` (`row`, `whole-session` or `standalone-classifier`), `case`, `commit`, `tested_donor_sha`, `tested_destination_commit`, `old_status`, `new_status`, `old_output`, `new_output`, `differences` and `compared`.
An omitted `case` is `*`.
`tested_donor_sha` must be the manifest donor.
`tested_destination_commit` must equal `commit`.
A whole-session result filed at the destination commit already recorded for that repository's row receipt is rejected.
Neither result certifies the other's revision.
Every destination path of that repository must exist at `commit`.
A result for a repository that is not a destination of the manifest is rejected.

`differences` entries are `case`, `field`, `old_present`, `old` and `new`.
Only an exact approved vector is accepted.
`check`, `compare`, `receipt` and `deletion` read each approved vector from its pinned reference.
A top-level case, field, presence, old value, new value, source or approval that differs from that reference is rejected.
A status change with equal output bytes is an unapproved difference unless an approved `execution_status` vector names it.
That vector covers only its own case.
The case `*` covers every case.
A vector for one case does not cover another.
Output fields are whole lines of the form `field=value`.
Each occurrence of a repeated field is compared on its own, so a later copy does not replace an earlier one.
Every added, removed or changed field must be named by an approved vector that covers the result case, with that field's old presence, old value and new value, and every other output line must be identical.
An approved `execution_status` vector does not account for any other output change.
An extra field is an unapproved difference.
The stored receipt keeps `case`, `old_status`, `new_status`, both outputs, the differences, `donor_sha`, `destination_commit` and `outcome` (`equal` or `approved-difference`).

The row comparison is filed at the batch's merged commit.
The whole-session comparison is filed at its own integrated commit, which may be later.
A classifier manifest, one whose paths include `cmd/growatt-can-classify/` or `internal/growattcanclassify/`, also takes a `standalone-classifier` result whose `compared` list names `local-file`, `stdin`, `json`, `text`, `monitor-association`, `error-stdout`, `error-stderr` and `status`.

## Deletion lists

`deletion` accepts `GG07`, `GG08`, `GG09`, `GG10`, `GG11` and `GG13`.
`<deletion.json>` carries `row`, `donor_sha`, `ledger_commit`, `manifests`, `grants`, `reserves`, `live_inputs` and `retirement_evidence`.
The ledger is the TSV files under `tools/boundary/` at `ledger_commit`, one finding per line: `path`, `kind`, `item`, `owner`, separated by tabs.
A missing `tools/boundary/` tree stops the command.
The list is written only when every kept finding is covered by a manifest whose donor repository is gateway, or `donor_repository` when the input names one, and whose donor SHA is the requested `donor_sha`.
That manifest's every destination repository has its own row receipt and its own whole-session receipt, each naming the manifest donor and its own destination commit, and each exact equality or the precise approved difference.
GG07 classifier paths also require a standalone receipt on a manifest whose donor paths include `cmd/growatt-can-classify/` or `internal/growattcanclassify/`.
That receipt must name the classifier destination repository and a destination commit already recorded for that repository by its row or whole-session receipt.
A standalone receipt on another manifest, or one that names another repository or another commit, does not cover those paths.
A missing proof writes no list.

Grants are `{ "kind": "shared" or "owned", "path": "<path>" }`.
A directory or a glob is replaced by the literal files it matches at the ledger commit.
An empty granted directory uses `reserves`, each path under that directory.
`@paths/<row>.lst` is not listed.
GG11's empty `scripts/fixtures/transport-gate/matter-feed-gateway-sources/` needs exactly five reserve paths under it.

GG10's `retirement_evidence` records `r2_002`, `r2_057`, `qq08_offline_validator`, `pinned_offline_capture_comparison` and `caller_inventory` (`revision` and `result`), plus `live_inputs` (`id`, `disposition`, `closure`, `source_revision`).
Every id in the top-level `live_inputs` must be covered.
`internal/eebusoutput/binding.go` needs `relay.testm40_outcome`, `relay.production_callers` of `absent` and `relay.revision`.
`cmd/gateway/leaf_promotion_live_source.go` and `internal/promotion/registry.go` need `shared_paths` entries with `ordinary_receipts` and `offline_retirement`.
A missing disposition, an uncovered live input or missing retirement evidence names that path or input and writes no list.

The list is `acceptance/manifests/<row>.lst`.
`<row>.json` records `repository` `gateway`, `donor_sha` and `sha256`.

## Acquisition

At the start of a workflow, resolve the published docs-semantic `refs/heads/main` and read the tool, the manifests and the sealed lists only from that commit:

```
git ls-remote https://github.com/Project-Helianthus/helianthus-docs-semantic.git refs/heads/main
git clone https://github.com/Project-Helianthus/helianthus-docs-semantic.git tool
git -C tool fetch --depth 1 origin <full-sha>
git -C tool checkout --detach <full-sha>
```

Select the manifest by its `row` and by coverage of the change in the sealed destination paths.
Donor paths stay distinct from destination paths.
An incomplete record or a signature that does not match fails that check.
No matching manifest selects the existing full CI and does not count as an additive preflight success.
A selected failing check stays a failure.

Resolve `donor.repository` through the public names below, fetch that repository and detach the recorded donor commit.
For each pattern, fetch the exemplar repository at the recorded full revision into the donor checkout's object store.
`check` then reads `git show <full-revision>:<path>` there.
For each expectation reference, each expected-difference reference and each non-inline candidate reference, fetch that repository at its recorded full revision into the tool checkout's object store.
`check` and `compare` read those objects with `git show` and do not read the worktree file.
A shallow checkout at the manifest commit does not drop a pinned revision once this fetch has stored it.
Inline candidate operands need no fetch.
The candidate commit and the oracle commit may differ.
No destination checkout stands in for a missing object.
Preflight does not fetch and does not publish.
Its inputs are the manifest path and the donor checkout.
`main.py` is `../tools/manifest/main.py` relative to `acceptance/manifests/`.
Later acceptance reuses the recorded source commit.

Public names, as recorded by [references.json](../../oracle/references.json) (`name_after_nn00`, and the gateway slug `helianthus-ebusgateway`):

| Id or slug | Public repository |
| --- | --- |
| `gateway`, `helianthus-ebusgateway` | `helianthus-gateway` |
| `semreg` | `helianthus-semreg` |
| `ebusreg` | `helianthus-ebusreg` |
| `ebusgo` | `helianthus-ebusgo` |
| `modbusreg` | `helianthus-modbusreg` |
| `modbus` | `helianthus-modbus` |
| `canbusreg` | `helianthus-canbusreg` |
| `canbus` | `helianthus-canbus` |
| `eebusreg` | `helianthus-eebusreg` |
| `eebus-go` | `helianthus-eebus-go` |
| `matterreg`, `helianthus-matter-binding` | `helianthus-matterreg` |
| `ha-integration` | `helianthus-ha-integration` |
| `vrc-explorer`, `helianthus-vrc-explorer` | `helianthus-vrc-explorer` |
| `docs-semantic` | `helianthus-docs-semantic` |
| `addon`, `helianthus-ha-addon` | `helianthus-ha-addon` |

The fetch URL is `https://github.com/Project-Helianthus/<public-name>.git`.

```
git clone https://github.com/Project-Helianthus/<public-name>.git donor
git -C donor fetch --depth 1 origin <donor-sha>
git -C donor checkout --detach <donor-sha>
git -C donor fetch --depth 1 https://github.com/Project-Helianthus/<exemplar-public-name>.git <full-revision>
git -C tool fetch --depth 1 https://github.com/Project-Helianthus/<reference-public-name>.git <full-revision>
```
