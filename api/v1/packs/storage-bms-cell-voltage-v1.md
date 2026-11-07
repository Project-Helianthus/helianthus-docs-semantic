# Candidate Storage individual-cell voltage and coverage v1

Status: **candidate**, proposed additive Storage **1.2.0** extension to
[accepted Storage1.1.0](storage-bms-v1.md). This is not an accepted typed runtime
input, definition index, qualified mapping, operation, or publication authority.
Nothing is stable before 1.0. Acceptance by the typed owner in
`helianthus-semreg` is a later prerequisite; this change makes no semreg change.

## Scope and evidence

The [finite contract table](storage-bms-cell-voltage-contract.json) declares the
schema, grades and bounds. The [synthetic vectors](storage-bms-cell-voltage-vectors.json)
are document examples checked by the focused Python test, not a runtime API.
Only the Growatt low-voltage BMS CAN family is illustrated. All examples have
`physical_qualified=false`. Proven and Hypothesis are candidate protocol grades;
Unknown meanings remain uninterpreted raw evidence. None is physical qualification.

Native facts are subordinate to these public native documentation contracts:

- [LINK protocol — Cell and sensor counts; Cell voltages, temperatures and balancing](https://github.com/Project-Helianthus/helianthus-docs-canbus/blob/main/protocols/growatt/growatt-low-voltage-bms-can-link-protocol-v1.md)
- [PCS protocol — Data validity and consumer obligations](https://github.com/Project-Helianthus/helianthus-docs-canbus/blob/main/protocols/growatt/growatt-low-voltage-bms-can-pcs-protocol-v1.md)

The supplied native facts grade 1810–1813 as Proven: each carries four LE16 mV
values, covering cells 1..16 in order, **only under its own selected measurement
gate**. These labels alone do not establish a route, direction, IDE, selector or
physical identity. The exact selector details are Unknown here; the fixture's
`selected_measurement` and per-channel `measurement_gate` are synthetic gate
assertions, never a native decoder. `unsupported-own-block-gate` withholds one
block while preserving the other three blocks and all raw bytes.
1830 has four LE16 fine-temperature codes, `code / 8 - 40` C, with FFFF invalid.
Reuse `storage.temperature.cell` and accepted topology meanings. No temperature
field, new sensor location meaning, or voltage invalid sentinel is introduced.

## Candidate shape

`storage.measurement.cell_voltage` is an optional `quantity` in `unit.volt`.
Its exact FactKey dimensions retain system, battery, pack, module, cell and
interface separately; none may be inferred from a channel, slot or model name.
The module and cell must match explicit topology. The per-module coverage record
uses the same context without the cell dimension. The table's `schema` declares
required channel, native lineage, accepted-value and result fields and types;
these describe finite examples, not an executable or stable API.

Volts use canonical kernel Decimal `{coefficient, exponent10}` with no floats:
3300 mV / 1000 = 3.3 V = `{"coefficient":"33","exponent10":-1}`.
0 mV is valid zero, `{"coefficient":"0","exponent10":0}`, when independently
valid; it is never absence. The semantic lower bound is zero and the upper bound
is explicitly null (unbounded). LE16 representability is a native encoding
constraint, not a universal semantic maximum. A later selected native gate may
supply narrower limits; no unstated sentinel or voltage plausibility gate is
invented. Absent, invalid, unsupported, stale, conflict and unavailable remain
separate states with retained raw evidence and no current interpreted value.

Every accepted value retains exact raw payload, interface, IDE, DLC/raw DLC,
endpoint, group, slot, source epoch, driver generation, sequence, monotonic time,
field age and grade, plus its complete dimensions. Synthetic endpoint/group/slot
labels assert no native topology or real address. The current context includes
exact source epoch and driver generation; any identity or generation mismatch
withholds that channel. Old evidence remains explicitly retained/non-actionable,
never silently relabelled as current. A rejected field cannot erase an independent
valid sibling or permitted partial last-known-good state.

## Coverage and time

The per-module tuple is
`(configured_count, addressable_slots, received_indices, valid_indices, vector_span)`.
Configured count is optional evidence: null means unknown, zero is invalid, and
positive counts are not universally bounded at 16. This particular layout has
slots 1..16. A count greater than 16 preserves partial values but cannot establish
complete coverage. Count is not capacity. Indices are sorted unique integers;
received includes invalid/stale channels while valid includes only independently
admitted channels within configured scope (when known). Extra received indices
are retained even when outside configured scope.

`vector_span` is null for no received channels; otherwise it records minimum and
maximum channel monotonic time and their exact difference, in one source epoch.
A context change prevents assembling old and new channels into a complete vector.
For mixed epochs/generations the raw span is diagnostic only, not a comparable
current vector. Complete requires a known positive count within slot capacity,
explicit topology, exact identity/generation, every configured index received
and valid, and an explicit bounded span policy. This never means physically
qualified or operationally fresh. There is no universal freshness threshold here:
the finite examples use an invented policy in the table. Each channel retains
its own age; missing or stale blocks cannot be refreshed by another channel or
the most recent unrelated frame. Blocks are not atomic. Span policy failure
withholds complete-vector interpretation while preserving individual values.

The required independent Hypothesis counterexamples are:

| Hypothesis | Named negative vector | Withheld interpretation |
| --- | --- | --- |
| H-pcs | pcs-extrema | Individual values/vector from extrema |
| H-count | missing-count, count-zero, count-seventeen | Complete coverage (paired with counts 1 and 16) |
| H-slots | slot-capacity-missing, capacity-is-not-count | Capacity as coverage/count |
| H-received | received-invalid | Received as valid |
| H-valid | valid-partial, missing-block | Partial valid set as complete |
| H-age | age-after-boundary, stale-block, other-channel-refresh | Stale channel/current complete vector |
| H-span | span-after-boundary | Atomic complete vector despite individually valid channels |
| H-sensor | no-sensor-association | Channel number as physical sensor location |
| H-topology | no-explicit-topology, no-physical-association | Slot/group/LINK-address as physical membership |

Each gate counterexample retains its paired positive payload. Numeric policy
boundaries have distinct at/after cases; cell scope includes 0/1 and 16/17.
Wrong dimensions vary system, battery, pack, module, cell and interface separately;
epoch, driver generation and native interface changes have separate cases.
These reject aliases while keeping valid siblings. Zero versus unavailable uses
the same zero payload; the latter withholds that field and keeps its raw evidence.

## Admission, migration and loss

This extension supplies candidate evidence only. Typed publication still requires
accepted typed contracts, exact semantic revision, source epoch, current driver
generation and qualified active capability. Unknown, stale, conflict, unsupported
and unqualified evidence fail closed; grades cannot promote themselves. Conflict
retains alternatives and lineage without choosing a convenient source. Balance
enable never becomes measured current or interlock-clear. PCS extrema cannot fill
missing individual indices. No system, battery or pack aggregate is fabricated.

Compatibility is proposed additive minor only if the typed owner accepts the
field, dimensions, optionality, coverage and migration rules without redefining
existing meanings. Accepted Storage1.1.0, its definition index, temperature,
topology, operation shapes and validators remain unchanged. Existing consumers
may omit the candidate with explicit loss. Future MCP and GraphQL projections
must expose equivalent optional values, coverage, lineage, lifecycle and losses;
this ticket changes neither interface and claims no implemented parity support.
Missing coverage must never become zero/full/fresh. Precision/range, topology,
partial coverage, span, stale, conflict, unavailable, unsupported selector,
identity/generation and qualification losses remain explicit.

Falsifiers include native evidence contradicting the selected block layout or
extrema limitation, proved physical associations, a different supported slot
capacity, or a typed-owner incompatibility finding. Resolve these in the native
owner and a revised candidate before acceptance; do not silently reinterpret
accepted values. Native invalid-voltage sentinels, selector specifics, freshness
thresholds, physical locations and topology remain unresolved.

This change is receive-only: it never transmits, acknowledges, probes or configures
anything on a bus. Offline synthetic checks do not establish transport, runtime,
physical qualification or operational semantics.
