---
status: "proposed contract text; the SemReg origin kind, the drivers that publish from a record and the Matter endpoint statement are pending."
---

# Certification references v1

This page defines the record form, the source category and the publication rule
of a value that a certificate states about the measurement accuracy of a device.
Such a value is a statement about the device under certified conditions. It is
not a reading from the device, and it is never mixed with a value that a device
publishes.

Contract identifier: `helianthus.semreg.certification-references/v1`. The shape
of a document is [certification-references-v1.schema.json](certification-references-v1.schema.json),
the acceptance vectors are
[certification-references-vectors-v1.json](certification-references-vectors-v1.json),
and `scripts/validate_certification_references_v1.py` checks both.

Evidence basis: the [kernel](kernel.md) origin and quality records, the
[driver contract](driver-contract.md) sections 5, 7 and 10, the
[family catalog](family-catalog-v1.md) evidence references, and the catalog
facts and dimensions named below. The operator decision of 2026-11-26 is a
project decision record that is not published in this repository; the rules
below are its normative statement.

Compatibility effect: new contract. The kernel origin list gains `declared` and
the family-catalog evidence kinds gain `certification`, both in place
([in-place change record](../README.md#in-place-change-record)); no existing
value changes its meaning and no version is raised. The member `statement` is
an edit in place of this same contract: the contract identifier is unchanged
and no version is raised.

## Source category

- `certification` is the one source category of this contract. A device that
  publishes a value from its own data publishes it as device data, and that value
  is never recorded here. [operator decision 2026-11-26]
- Only the registry of the certificate issuer or the official documentation of
  the vendor counts as a source. The record states the address of that registry
  or document in `url`; the validator does not check what the address names.
- A certificate that does not name the device is no reference for it. The gap
  stays named (see [Categories](#categories)).
- Nothing is invented: there is no default number, no specification-default
  accuracy value, and no catalog element that holds a declaration without a
  source.

## Document

| Member | Type | Rule |
| --- | --- | --- |
| `contract` | string | Exactly `helianthus.semreg.certification-references/v1`. |
| `entries` | array | At least one entry. |

No other member is allowed at any object level, and a repeated member name in
any object is rejected.

## Entry

An entry has one of three categories, stated by its `category` member:
`reference`, `gap` or `unavailable`. Its members are closed per category; a
member that the table does not list for the category is rejected.

| Member | Type | `reference` | `gap` | `unavailable` |
| --- | --- | --- | --- | --- |
| `source` | string | required, exactly `certification` | required | required |
| `category` | string | required | required | required |
| `driver` | string | required | required | required |
| `vendor` | string | required | required | required |
| `flavor` | string | required | required | required |
| `model` | string | required | required | required |
| `firmware` | object | required | required | required |
| `issuer` | string | required | required | required |
| `certificate_number` | string | required | not allowed | not allowed |
| `issue_date` | string | required | not allowed | not allowed |
| `stated_value` | object | required | not allowed | not allowed |
| `url` | string | required | required | required |
| `retrieved_on` | string | required | required | required |
| `refusal` | string | not allowed | not allowed | required |

- `driver` is the identifier of the driver that holds the record. `flavor` is the
  driver's own flavor or profile identifier. `vendor` and `model` are the names
  the certificate or the vendor document uses for the device. Every text member
  is a non-empty string.
- `issuer` is the certificate issuer. For a `gap` or an `unavailable` entry it
  is the issuer whose registry was consulted.
- `certificate_number` is the number the certificate carries, as written.
- `issue_date` and `retrieved_on` are calendar dates in the form `YYYY-MM-DD`.
  `issue_date` is the issue date of the certificate; `retrieved_on` is the date
  the registry or document was read.
- `url` is an `https` address of the issuer's registry or the vendor's official
  documentation.
- `stated_value` is the exact value the certificate states; see
  [Stated value](#stated-value).
- `refusal` is the text with which the source refused automated access.

## Categories

- `reference`: a certificate names the device and states a value. It carries
  every member of the `reference` column.
- `gap`: no certificate names the device. The entry records that the gap exists
  and where it was looked for. A `gap` entry that carries a stated value is
  rejected.
- `unavailable`: the registry refused automated access, so the content is not
  known. The entry carries the refusal text, and one without refusal text is
  rejected. An `unavailable` entry that carries a stated value is rejected.
- A certificate that names the device and states no firmware release is a
  `reference` whose `firmware` is `not_stated`.
- A file that holds two entries of different categories for one `driver`,
  `vendor`, `flavor`, `model` and `firmware` is rejected. Two entries of one
  category for one such identity are allowed, for example two certificates for
  one device.

## Firmware

`firmware` is an object whose `form` member is one of:

| `form` | Other members | Meaning |
| --- | --- | --- |
| `not_stated` | none | The source states no firmware release. The record applies to the model with the firmware recorded as not stated. |
| `release` | `release` | The release the source states. Firmware is a floor, not a ceiling: the record covers that release and every later release, and no earlier release. |
| `range` | `from`, `to`, `upper_bound_stated_by` | The releases the source states, `from` and `to` included. `upper_bound_stated_by` is `certificate` or `vendor_document`: the upper bound is recorded only when one of them states it. |

A release is dot-separated non-negative integers. Two releases are compared
component by component as integers, a missing component counting as zero. A
range whose `from` is above its `to`, a range without `upper_bound_stated_by`,
and a release of another form are rejected.

Coverage of a release by a firmware record is `covered`, `not_covered`, or
`not_stated` when the form is `not_stated`; a record with a stated firmware never
covers an earlier release than its floor.

## Stated value

`stated_value` carries only the members the certificate states. No member is
`null` or defaulted, and a member the certificate does not state is absent.
`measurement_type` names the measurement the statement applies to and is always
present, as a symbol of the dimension `pv.dimension.measurement_type` or
`infrastructure.dimension.measurement_type`; the validator checks only its
token form. At least one of the other members is present.

| Member | Type | Value |
| --- | --- | --- |
| `measurement_type` | string | Token `^[a-z][a-z0-9_]*$`. |
| `measured` | boolean | Whether the certificate states the value as measured. |
| `ratio_maximum` | decimal | The maximum accuracy as a ratio of the reading. |
| `measured_minimum` | decimal | The minimum of the measured range. |
| `measured_maximum` | decimal | The maximum of the measured range. |
| `range_minimum` | decimal | The minimum of one accuracy range. |
| `range_maximum` | decimal | The maximum of one accuracy range. |
| `statement` | string | Non-empty: the certificate's words for the accuracy, as written, for example a class designation with the standard it names. |

A decimal is the canonical decimal of [serialization](serialization.md#canonical-decimal-and-quantity):
a `coefficient` string and an integer `exponent10`, written in the SI unit of the
fact it feeds (`unit.ratio`, `unit.watt` or `unit.ampere`). A figure that the
certificate states in percent is written as the exact ratio, with no rounding.
A member whose measurement type has no fact in the table below holds a value
that feeds nothing until the catalog has one. A certificate that states the
accuracy only as a class designation is a reference: `stated_value` holds
`measurement_type` and `statement` and no other member. Nothing converts that
class into a number.

## Which accuracy values a record can feed

| Member | PV inverter facts | Electrical infrastructure facts |
| --- | --- | --- |
| `measured` | `pv.accuracy.measured` | `infrastructure.accuracy.measured` |
| `ratio_maximum` | `pv.accuracy.ratio_maximum` | `infrastructure.accuracy.ratio_maximum` |
| `measured_minimum` | `pv.accuracy.measured_minimum_active_current`, `pv.accuracy.measured_minimum_active_power` | none |
| `measured_maximum` | `pv.accuracy.measured_maximum_active_current`, `pv.accuracy.measured_maximum_active_power` | none |
| `range_minimum` | `pv.accuracy.range_minimum_active_current`, `pv.accuracy.range_minimum_active_power` | none |
| `range_maximum` | `pv.accuracy.range_maximum_active_current`, `pv.accuracy.range_maximum_active_power` | none |
| `statement` | none | none |

A statement feeds no fact. Nothing converts a class designation into a number.

The facts are qualified by `pv.dimension.measurement_type` or
`infrastructure.dimension.measurement_type`; the `measurement_type` member selects
the qualifier value. The `active_current` facts take `unit.ampere` and the
`active_power` facts `unit.watt`.

A certification reference does not by itself close the values that have no
source: Power Topology `FeatureMap`, Electrical Power Measurement `FeatureMap`,
`PowerMode`, `NumberOfMeasurementTypes`, `MinMeasuredValue`, `MaxMeasuredValue`,
`RangeMin` and `RangeMax`. The record form has a member for the last four
(`measured_minimum`, `measured_maximum`, `range_minimum`, `range_maximum`), and a
record carries one of them only when the certificate states it. The record form
has no member for the other four, so they stay named gaps. The `Measured` member
of the Accuracy structure is published only when a record states `measured`, and
otherwise stays a named gap.

## Publication by a driver

- A driver publishes a certification value with origin kind `declared` and
  certification evidence: the origin carries 1 through 32 unique evidence
  references, at least one of the kind `certification`. The value is a
  statement about the device under certified conditions, not a reading, and it is
  never presented as measured.
- The source of a certification value has a lower priority than every device
  source of the same element, and no lower source substitutes for a higher one
  ([driver contract](driver-contract.md) section 5).
- A certification value is never published beside a device value for the same
  fact key: a driver declares no certification source for a fact key for which it
  declares a device source.
- An entry in the `gap` or `unavailable` category publishes no value. A release
  that a `release` or `range` firmware does not cover publishes no value from
  that record. A record with firmware `not_stated` applies to the model, and its
  value is published with the firmware recorded as not stated.
- On a Matter endpoint, the statement of origin is carried by the Fixed Label
  cluster of the endpoint: one entry per measurement type whose accuracy comes
  from certification, with `Label` the name of the measurement type in the Matter
  model and `Value` the text `certification`. The entry is absent for a
  measurement type whose accuracy the device publishes itself.

## Failure reasons

The validator reports the first failure of a document with one stable reason,
the zero-based `entry` index, and the `member` when one is named. The entry
checks run in the order of this table, after a missing or invalid `category`;
the schema check follows the entry checks, and the category conflict is checked
last.

| Reason | Rejected when |
| --- | --- |
| `source_not_certification` | `source` is present and is not `certification`. |
| `stated_value_not_allowed` | A `gap` or `unavailable` entry carries `stated_value`. |
| `unknown_member` | A member outside the closed set of the category is present, including a member that names a device-published value. |
| `refusal_missing` | An `unavailable` entry has no refusal text or an empty one. |
| `missing_member` | A member the category requires is absent, or `category` is absent. |
| `invalid_value` | A text member is not a non-empty string, a date is not a calendar date, `url` is not an `https` address, or `category` is not one of the three. |
| `firmware_invalid` | `firmware` has an unknown form, an unexpected member, a release of another form, or a range whose `from` is above its `to`. |
| `firmware_upper_bound_unstated` | A range has no `upper_bound_stated_by`, or one that is not `certificate` or `vendor_document`. |
| `stated_value_invalid` | `stated_value` has a member outside the table, no member besides `measurement_type`, a `null` member, a `statement` that is empty or not a string, or a decimal that is not canonical. |
| `schema` | The document does not conform to the schema in a way the reasons above do not name. |
| `category_conflict` | Two entries of different categories share `driver`, `vendor`, `flavor`, `model` and `firmware`. |

## Unresolved questions

- `Quality.Assertion` of a candidate with origin kind `declared` is unresolved.
  The [kernel](kernel.md) requires a `Derivation` for an inferred value and
  forbids one for an observed value; a declared origin carries no derivation,
  and the repository names no assertion kind for a statement of a certificate.
  This page sets none.
- The kernel `EvidenceRef` kind is a `DefinitionID`, which requires a separator,
  while the family-catalog vocabulary word is `certification`. The repository
  states no mapping between the two, and this page defines none.
- Two `reference` entries for one device that state different values for one
  fact key: the repository states no choice between them, and this page defines
  none.
- A firmware release that is not dot-separated integers has no order here, so
  such a release cannot be written as `release` or `range`.
- The record form has no member for the Power Topology `FeatureMap`, the
  Electrical Power Measurement `FeatureMap`, `PowerMode` and
  `NumberOfMeasurementTypes`; no source states their form for a certificate.

## Falsifiers

- A certification value published without origin kind `declared`, or beside a
  device value for the same fact key, falsifies the publication rule.
- An entry that carries a member naming a device-published value, or a source
  other than `certification`, and is accepted falsifies the source category.
- A `gap` or `unavailable` entry that carries a stated value, and is accepted,
  falsifies the category rules.
- A firmware range with an upper bound that no certificate or vendor document
  states, and is accepted, falsifies the firmware rule.
- A release earlier than the floor of a `release` record reported as covered, or
  a later release reported as not covered, falsifies the coverage rule.
- A `statement` published as an accuracy fact, or a class designation converted
  into a number, falsifies the rule that a statement feeds no fact.
