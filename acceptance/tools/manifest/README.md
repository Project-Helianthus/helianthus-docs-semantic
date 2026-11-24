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
`compare` prints one result per bound case and one result per transferred assertion, then `compare: ok`.
A move whose `patterns` list is empty still runs each transferred assertion at its recorded destination test.
When the manifest declares transferred assertions and none of them ran, `compare` fails with `not-executed move=<row>` and does not print `compare: ok`.

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
