# Huawei LUNA2000 storage mapping gate v1

This gate states what `helianthus.pack.storage@1.1.0`, the generic Storage
family that the Growatt storage mapping also uses, will take from Huawei
LUNA2000 observations once a battery profile is admitted, and it publishes
nothing before then. It adds no pack and no vendor-specific semantic family, and
it makes no stability promise before Helianthus 1.0. It is neither a device
support claim nor a live qualification. Its machine-readable companion is
[the mapping vectors](huawei-luna2000-storage-v1.json); the vectors are
synthetic and are not observations from hardware.

No battery fact is admitted today, so every item below is withheld with an
explicit reason and loss. The sibling gates are
[the SUN2000 PV gate](huawei-sun2000-pv-v1.md), which maps the admitted inverter
facts, and [the gateway-meter gate](huawei-gateway-meter-infrastructure-v1.md).

## Evidence basis

| Source | Reference | Role |
| --- | --- | --- |
| Native monitoring contract | `helianthus-docs-modbus` issue 242, pull request 253: `protocols/huawei/monitoring-readonly-v1.md` and `protocols/huawei/read-pacing-v1.md` | Owns the battery rule, the planned site and plant groups, and every grade. |
| Registry dispositions | `helianthus-modbusreg` issue 348, pull request 357 | The LUNA2000 disposition stays `NO_ADMISSIBLE_PROFILE` and records the three battery groups as present but not admitted. |
| Program | `helianthus-modbusreg` issues 199 and 201 | The Huawei read-only program this gate belongs to. |
| Multi-endpoint contract | `helianthus-docs-ebus` issue 746, pull request 748 | Asset and source keying per endpoint instance. Its text was not final when this gate was written. |

No revision, digest or pinned link is cited. Grades are those of the monitoring
contract, kept separate from admission, qualification and support: Proven needs a
live reading checked independently, Hypothesis is a document statement or a
plausible unchecked reading, and Unknown is unsettled. A rule of this gate that
goes beyond the contract is a Hypothesis.

## Decision: the generic Storage family

The operator decision on the storage publication family is to publish Huawei
battery facts into the generic Storage family and to create no new family. This
gate therefore keys every prospective fact to a `storage.*` definition of
`helianthus.pack.storage@1.1.0`. Those facts are read only through the shared
semantic snapshot. The Growatt-specific single-asset storage projection and its
machine-to-machine root are not reused or cloned.

## Admission state

The registry's LUNA2000 disposition is `NO_ADMISSIBLE_PROFILE`; whether or not
the parent inverter is identified, no battery profile is selected, and the
decoder key count is zero (Proven as a statement of the registry). The battery
groups answered with data on the SUN2000 MAP0 series only (Proven), and their
meanings, gains and signs are Unknown. On the M3 and M1 series the single reads
at the battery offsets answered one zero word (Proven), and the rule that a
battery offset answers zero at an inverter without a battery is a Hypothesis.
No battery offset is in any read plan.

The gate accepts the registry outcomes `INSUFFICIENT_EVIDENCE`,
`NO_ADMISSIBLE_PROFILE` and `AMBIGUOUS`. A selected battery profile fails closed
with `gate_revision_required`: the registry cannot admit a profile before this
gate is revised. All five registry flags (`catalog_registered`,
`automatic_runtime_admission`, `live_qualified`, `support_claim`,
`write_authority`) stay false, and `outbound_allowed=false` grants no operation.

Before any row below may be mapped, a revision of this gate must show that:

1. a battery profile for the exact family is admitted with a consulted edition;
2. type, word order, gain, unit and sign of each consumed word are stated;
3. a sign is graded before any power is published;
4. the aggregation basis is recorded as provenance;
5. the storage asset granularity is settled;
6. executable vectors for that profile are added.

## Identity and keying

The asset identifier and the source identifier are gateway-configured,
non-secret and distinct, and a binding identifier is derived by the gateway over
the asset, the source and the profile only. None may be derived from a serial
number, an ESN, the vendor, the model, firmware or any version text, a routed
unit alone, or an endpoint address; a missing or invalid identity fails closed.
The storage asset granularity is Unknown: the batteries are registers of the
inverter units and not units of their own (Proven), and the multi-endpoint
contract of `helianthus-docs-ebus` issue 746 (pull request 748, open) is not
final. Nothing is keyed today because nothing is published.

## Withheld items

Each native item has exactly one disposition, `withheld`. The reason shown for a
battery group read is the one that applies when no read is supplied; a supplied
read selects the zero-word, exception or no-profile reason, and a planned group
cannot be supplied at all because it was never read. Absent optional groups are
unknown, never zero.

| Native item | Source | Grade | Reason | Loss kind |
| --- | --- | --- | --- | --- |
| `battery_group_37000_30` | registry_disposition | Unknown | `storage.reason.battery_group_not_read` | provenance |
| `battery_single_read_37000_1` | registry_disposition | Proven | `storage.reason.battery_group_not_read` | provenance |
| `battery_group_37066_4` | registry_disposition | Unknown | `storage.reason.battery_group_not_read` | provenance |
| `battery_group_47000_1` | registry_disposition | Unknown | `storage.reason.battery_group_not_read` | provenance |
| `site_battery_soc` | monitoring_contract_planned | Hypothesis | `storage.reason.planned_group_not_observed` | provenance |
| `site_battery_power` | monitoring_contract_planned | Hypothesis | `storage.reason.planned_group_not_observed` | provenance |
| `plant_battery_power` | monitoring_contract_planned | Hypothesis | `storage.reason.planned_group_not_observed` | provenance |
| `site_battery_energy_charged_total` | monitoring_contract_planned | Hypothesis | `storage.reason.planned_group_not_observed` | provenance |
| `site_battery_energy_discharged_total` | monitoring_contract_planned | Hypothesis | `storage.reason.planned_group_not_observed` | provenance |
| `site_battery_energy_charged_day` | monitoring_contract_planned | Hypothesis | `storage.reason.period_counter_time_domain_not_represented` | time |
| `site_battery_energy_discharged_day` | monitoring_contract_planned | Hypothesis | `storage.reason.period_counter_time_domain_not_represented` | time |
| `site_rated_storage_capacity` | monitoring_contract_planned | Hypothesis | `storage.reason.no_energy_capacity_fact_in_pack` | capability |

The grade is that of the native item. The battery single read at the first
battery offset answered a zero word (Proven), and its meaning is not a value.
The planned groups are site values of the EMMA, a plant value of the S-Dongle
and a candidate presence word; the monitoring contract names them from consulted
editions and does not send them until an operator-approved observation records
their answer and the contract is revised. Whether the gateways answer is
Unknown.

Three runtime reasons and the primary reason complete the set:
`storage.reason.zero_word_is_not_a_battery_value` (a zero word is never a state
of charge, power or energy of zero, and presence is never decided from it),
`storage.reason.battery_group_exception_no_negation` (an exception negates
nothing else), `storage.reason.battery_group_not_read`, and
`storage.reason.no_admitted_battery_profile`, which is the reason of each of the
five requested items.

## Prospective intake

These rows are not in force. They record only where a fact will land if the
preconditions above are met, so that a later profile does not need a new family.
Each target, dimension and unit is checked against the Storage pack's contract
tables.

| Storage fact | Dimension | Native candidate | Native form | Sign or counter rule | Grade |
| --- | --- | --- | --- | --- | --- |
| `storage.status.operating` | `storage.dimension.pack` | `battery_group_37000_30` | none decoded | empty table, observed states only | Unknown |
| `storage.state.soc` | `storage.dimension.pack` | `site_battery_soc` | U16, %, gain 100 | none | Hypothesis |
| `storage.pack.power` | `storage.dimension.pack` | `site_battery_power` | I32, kW, gain 1000 | `unknown_no_value_without_a_graded_sign` | Hypothesis |
| `storage.pack.power` | `storage.dimension.pack` | `plant_battery_power` | I32, kW, gain 1000 | `positive_while_charging_negative_while_discharging` | Hypothesis |
| `storage.energy.charged` | `storage.dimension.pack` | `site_battery_energy_charged_total` | U64, kWh, gain 100 | `reset_wrap_and_continuity_never_inferred` | Hypothesis |
| `storage.energy.discharged` | `storage.dimension.pack` | `site_battery_energy_discharged_total` | U64, kWh, gain 100 | `reset_wrap_and_continuity_never_inferred` | Hypothesis |

Rules for the intake, each a Hypothesis of this gate unless stated:

1. **Operating symbol.** The observed states of a battery state word are the only
   symbols that may be mapped, and none was observed with a known meaning, so the
   symbol table is empty and every code is Unknown and withheld.
2. **Pack power and sign.** The Storage pack does not normalize the sign of pack
   power, so a mapping keeps the native sign reference as provenance (a reversible
   `provenance` loss) and converts kilowatt at gain 1000 to watt by an exponent
   shift of three with a `unit` loss. The S-Dongle plant power states positive
   while charging; the monitoring contract grades that a Hypothesis. The EMMA
   site power states no sign (Unknown), so no value is published from it until a
   sign is graded. The two sign references are never mixed.
3. **Energy charged and discharged.** The total counters map to the pack's
   kilowatt-hour counters as read, with a `policy` loss: reset, rollover and
   continuity are Unknown and never inferred, and no energy is derived or summed.
4. **Aggregation.** The site and plant values are aggregates over an undetermined
   number of packs, while the pack's fact dimension is the pack. A revision must
   either key them to one battery asset with the aggregation basis kept as
   provenance, or keep them withheld. The pack never infers membership, a cell
   count or an arithmetic aggregate (Unknown).
5. **Decimal form.** Quantities use the kernel coefficient and exponent pair.
   There is no binary floating point, and the validator rejects a float literal.

## Capacity

Capacity in energy units is withheld. The Storage pack carries ampere-hour
counters only (`storage.capacity.charge` and `storage.capacity.discharge`, which
are cumulative throughput and not a rated capacity), and the planned rated
storage capacity is in kilowatt-hours. A rating in energy units needs a separate
SemReg and pack revision. It is never converted from ampere-hours or voltage, and
never derived from state of charge or from an energy counter; the vector
`STG-NEG-008-ampere-hour-to-kilowatt-hour` pins that the conversion is refused.
The ampere-hour counters are not mapped either, because no Huawei ampere-hour
quantity is evidenced.

## Control-adjacent items

The charge and discharge power limits, the interlock, working modes, schedules,
remote dispatch and every write are withheld or unsupported. `storage.limit.charge_power`,
`storage.limit.discharge_power`, `storage.status.interlock`,
`storage.operation.set_charge_limit` and `storage.operation.set_discharge_limit`
are never requested by this gate. No authority, acknowledgement, readback, retry
or route exists, and a request for one is rejected with `unsupported_or_withheld`.

## Lifecycle

A case carries the observation identifier and revision, the receipt on a wall and
a monotonic axis, the clock epoch, the source epoch, the driver generation, the
connection generation, the registry outcome and any battery reads. The first
error of this order is reported: gate revision required, native evidence
invalid, identity missing or invalid, lifecycle missing, mapping unqualified,
unsupported or withheld. A battery value that existed would keep its original age
when a read failed; no such value exists today. Withdrawal is explicit and
generation-fenced.

## Acceptance vectors

| Vector | What it proves |
| --- | --- |
| `STG-POS-001-no-battery-read` | No battery offset is in any read plan, so every item is withheld and nothing is zero. |
| `STG-POS-002-zero-words-without-battery` | Zero words at the battery offsets of an inverter without a battery publish no state of charge, power or energy. |
| `STG-POS-003-battery-group-answers-with-data` | A group that answers with data still publishes nothing, because no profile gives its words a meaning. |
| `STG-POS-004-battery-read-exception` | An exception or a failed read withholds the battery item and negates nothing else. |
| `STG-POS-005-selection-insufficient-evidence` | Every allowed registry outcome withholds the same items. |
| `STG-NEG-001-battery-profile-selected` | A battery profile selected before this gate is revised fails closed. |
| `STG-NEG-002-planned-group-fed-as-evidence` | A planned group that was never read cannot be supplied as evidence. |
| `STG-NEG-003-word-count-mismatch` | A read must carry exactly its quantity of words. |
| `STG-NEG-004-asset-missing` | A blank asset identifier fails closed. |
| `STG-NEG-005-lifecycle-missing` | The source epoch is required. |
| `STG-NEG-006-live-qualified` | A live qualification requires a revision of this gate. |
| `STG-NEG-007-charge-limit-operation` | The gate has no limit, interlock, route or authority. |
| `STG-NEG-008-ampere-hour-to-kilowatt-hour` | Capacity is never converted to energy units. |
| `STG-NEG-009-limit-item-requested` | A control-adjacent item is not requestable. |
| `STG-NEG-010-error-precedence` | The first error of the precedence list is reported. |

## Unresolved and falsifiers

| Question | Falsifier | Grade |
| --- | --- | --- |
| What do the battery words mean, and what are their gains and signs? | A consulted edition that covers the family, or an independent check of the layout. | Unknown |
| Which word, if any, states battery presence? | The candidate presence word checked against a site with and without a battery. | Unknown |
| Do the planned site and plant groups answer? | An operator-approved observation. | Unknown |
| What is the sign of the EMMA site battery power? | A reading at charge and at discharge with an independent check. | Unknown |
| Is the storage asset one per inverter child or one per site? | The final multi-endpoint contract. | Hypothesis |

## Later consumer cutover

Consumers read these facts only through the shared semantic snapshot. This gate
publishes no consumer binding. Any implementation must bind consumers in one
atomic cutover, must not reuse the single-asset Growatt projection, and must keep
`outbound_allowed=false`.

## Validation

Run `python3 scripts/validate_huawei_luna2000_storage_mapping.py`,
`python3 scripts/test_validate_huawei_luna2000_storage_mapping.py` (also collected
by `python3 -m pytest`), and `./scripts/check_docs.sh`, which runs both. The validator executes every vector, checks each
prospective target against the Storage pack tables, checks that every native item
has exactly one disposition, and compares the tables of this page with the
contract.
