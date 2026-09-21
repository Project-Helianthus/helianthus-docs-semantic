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

Every accepted field, capability, and operation receives exactly one row: 88
fields, 32 capabilities, and 7 operations. Services are not projection items.
One narrow read-only candidate projects `evse.ac.current` to the exact numeric
tuple device type `0x0510`, cluster `0x0090`, attribute `0x0005`, transforming
amperes to milliamperes by 1000. Endpoint and phase identity, precision,
lifecycle, range, nullability, and target behavior remain explicit loss.

All remaining rows are `unknown_fail_closed`, each with a reason and loss. They
permit no target lookup, inferred fallback, operation, or control. This contract
copies no draft text and makes no Matter runtime, conformance, qualification,
consumer-binding, or physical-device claim.

Run `python3 scripts/validate_matter_17_projection_v1.py`,
`python3 scripts/test_validate_matter_17_projection_v1.py`, and
`./scripts/check_docs.sh`. These local checks verify only ledger coverage and
pin structure.
