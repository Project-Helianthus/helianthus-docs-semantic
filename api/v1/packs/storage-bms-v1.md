# Storage and BMS capability pack v1

`helianthus.pack.storage/v1` has exact PackRef `{id: "helianthus.pack.storage", version: "1.0.0"}` and is the accepted software-0.7 typed input over `helianthus.semantic.kernel/v1`. Its machine-significant catalog is [storage-bms-acceptance-vectors.json](storage-bms-acceptance-vectors.json).

The companion [exact contract tables](storage-bms-contract-tables.json) fix each
field's kind, unit, dimension, optionality and bounded/unbounded shape; service,
relationship, capability, operation, effect, and Portal tuples are fixed there
as well. They require admission, interlock, authority, exact route and current
generation before operation dispatch, then separate acknowledgement, readback,
terminal outcome, and applied effect confirmation.

The table's `definition_index` is a complete kernel `DefinitionRef` index for
fields, services, capabilities, operations, and effect rules. Every reference
names `helianthus.pack.storage` version `1.0.0`; no owner or version is inferred
from a DefinitionID. Quantity bounds use kernel `Decimal` objects
`{coefficient, exponent10}`, never string or floating-point comparisons.

Each canonical field record declares optionality. State of charge and health are
bounded from 0 through 100 percent. Energy, capacity, pack voltage, cell-voltage
extrema, and admitted charge/discharge limits have a minimum of 0 and an explicit
unbounded maximum. Pack current/power and pack/cell temperatures retain explicit
unbounded minimum and maximum because their native reference or sign is not
normalized by this contract. Symbol records carry their complete accepted set.

Limit operations use the complete kernel outcomes: `rejected`,
`failed_no_contact`, `acknowledged_unverified`, `applied`, `no_effect`,
`conflict`, and `indeterminate`. ACK without confirming current-generation
readback is `acknowledged_unverified`; unknown delivery is `indeterminate`.
Blind retry or route fallback is forbidden after a possible side effect or an
indeterminate outcome.

The catalog defines state of charge/health, pack voltage/current/power, charged and discharged energy/capacity, pack/cell temperature, cell voltage extrema, alarms/protection/warnings, operating state, and charge/discharge limits. Canonical units are percent, volt, ampere, watt, kilowatt-hour, ampere-hour, and celsius. Missing data is unavailable evidence, never zero. Raw native bitfields and validity remain native evidence whenever a symbol is lossy.

System, battery, pack, module, cell, string, and inverter/charger interface remain separate FactKey dimensions and relationship records. Aggregate fields retain native aggregation/reference/sign evidence; this pack never infers membership, a cell count, sign, or arithmetic aggregate.

Publication requires exact source epoch, current driver generation, exact semantic revision, and qualified active capability. Partial publication changes supplied valid fields only and preserves permitted last-known-good data. Withdrawal is explicit and generation-fenced; stale/unknown evidence cannot promote or authorize. Counter decrease never proves reset/wrap; native evidence is required.

The only operation shapes are `storage.operation.set_charge_limit` and `storage.operation.set_discharge_limit`. An exact qualified native route, capability, generation, authority, and interlock are required before dispatch. ACK, readback, and terminal outcome remain separate; `applied` needs exact current-generation readback. No generic contactor, enable/disable, balancing, firmware, reset, or raw native write is published.

Projection loss covers native enum/bitfield, precision/range, cell/module topology, signed direction, aggregation/reference, counter reset/wrap, unavailable fields, conflicts, extensions, and unsupported operations. Portal consumes promoted read facts and current admitted operations; it cannot define truth, routes, authority, or lifecycle.

Inputs are semantic docs `346cda9b675a03a7d1a8c886a3467eab84ce8fb2`, semreg projection `cc9b324225e945598128eeabe977e7fa0af6dc93`, CAN docs/registry `665a5f22f78c349b5e3063bda158af250a3f44b6` / `8c827ea26ffbad8b50aba2c6ae89028622ba4343`, RS-485 docs/registry `c9d37b7f7cd5ebc6c4125565648a7deb094aaa7a` / `f1e593995576fdfbbc64fd879b47abff8bd2cc0e`, eeBUS ledger `81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1`, and Matter draft `29b4768a513cf566011ab8cd60df1bc495204953`.

Growatt CAN V1.04 is a selected-interface synthetic offline candidate with `physical_qualified=false`, no control route, and V1.05/high-voltage/other families unsupported. Growatt 1xSxxP RS-485 is an observation/fixture candidate with no command tuple, discovery, runtime admission, or real I/O. eeBUS remains `unknown_pending_std_01`; Matter is not conformance. No mapping is normative or operable.

The five-domain catalog has thermal/HVAC and storage/BMS accepted, PV/inverter in exact-HEAD review, and EVSE/infrastructure follow-ons. This is typed 0.7 documentation only: no IR/codegen, runtime, driver, gateway, consumer, deployment, or live behavior. Run `python3 scripts/validate_storage_bms_pack_v1.py`, `python3 scripts/test_validate_storage_bms_pack_v1.py`, and `./scripts/check_docs.sh`.
