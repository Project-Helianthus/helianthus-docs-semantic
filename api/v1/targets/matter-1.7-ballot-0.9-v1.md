# Matter 1.7 ballot 0.9 projection contract v1

`helianthus.gateway.matter-projection/v1` is a versioned projection contract
for the pinned `matter.data-model` target. Its machine-readable ledger is
[matter-1.7-ballot-0.9-v1.json](matter-1.7-ballot-0.9-v1.json), validated from
the accepted immutable pack metadata by
`scripts/validate_matter_17_projection_v1.py`.

The target version is
`1.7-draft-ballot-0.9+29b4768a513cf566011ab8cd60df1bc495204953`. The ledger
pins the `connectedhomeip` branch `dm-0.9-1.7` and commit
`29b4768a513cf566011ab8cd60df1bc495204953`; `data_model/1.7` source SHA
`214e40c9d51cfe89050eae68ca5b76238fcfa332`; tag `0.9-1.7-winter2027`; and
scraper `alchemy v1.7.10+dirty`. It also pins SemReg `089ed6ae9004`, docs base
`2b3ca78`, and the five accepted pack versions.

Every accepted field, capability, and operation receives exactly one kernel-v1
row: 88 `fact`, 32 `capability`, and 7 `operation` rows. Rows are canonically
sorted by `(pack id, pack version, definition id, definition version)`; kind
does not create a second ordering group. Each row carries its typed kernel
request, exact revision binding, and structured loss accounting.

One narrow read-only transformed observation projects `evse.ac.current` to the
exact numeric tuple device type `0x0510`, cluster `0x0090`, attribute `0x0005`.
It multiplies amperes by 1000 only when the result is integral and representable
as a non-null signed `amperage-mA` in the inclusive range
`-4611686018427387904..4611686018427387904`; the target attribute itself is
nullable. The positive emission requires exactly one eligible FactKey/candidate
with the pack-validated runtime phase dimension. A missing, multiple, or
ambiguous phase key, a non-integral or out-of-range conversion, produces no
target payload. The same whole-document no-payload rule applies to stale,
unavailable, unqualified, conflicted, invalid, and revision-mismatched input.
Its FactKey binds the exact pack ID/version, fact ID, and canonical runtime
dimensions, and the projection binds the exact input snapshot and revision
vector.

All remaining rows are kernel-v1 `unknown`, each with a reason and structured
loss. They permit no target lookup, inferred fallback, operation, or control.
The public-source evidence fixture records the pinned XML paths and Git blob
identities used for the one tuple without copying standard prose. This contract
makes no Matter runtime, conformance, qualification, consumer-binding, or
physical-device claim.

Run `python3 scripts/validate_matter_17_projection_v1.py`,
`python3 scripts/test_validate_matter_17_projection_v1.py`, and
`./scripts/check_docs.sh`. These local checks verify only ledger coverage and
pin structure.
