---
status: "scope denominator for packages A to F; each row records its specification, operations and promotion."
---

# Scope denominator for 0.7

This directory is the public scope table for audit packages A to F.

Package A is the meaning of qualified and the family catalog. Package B is the wiring of existing feeds. Package C is semantic operations. Package D is the graph read side, lenses and relations. Package E is the catalog extension to the Matter and eeBUS union. Package F is driver breadth.

SemReg promotes Matter HVAC, Energy and Hydraulics, all of eeBUS as one corpus, and a row whose public document from a second major vendor provides the same data. A row that stays unconfirmed stays native in its driver namespace (MCP, GraphQL, Prometheus) and is listed in the release report. Home Assistant receives only what SemReg promotes. Support is declared from the specification. Units in SemReg are SI. An eeBUS leaf is promoted without waiting for an eBUS twin.

The four OutBack rows are out of 0.7 and scheduled for 0.8 (OPERATOR item 30). Graph lenses and relations are SemReg structure and are promoted.

A named exception wins over the second-vendor cell. An `in corpus` row is promoted only when the cited clause supplies the same role, subject, period where it applies, sign or direction, and quantity or value meaning. A confirmed second vendor promotes the row when the cited document supplies that same data. An unconfirmed row stays in the driver namespace. Uncertainty is recorded on the row.

## Columns

`package` is A to F. `slice` is the draft part name, or `cross-protocol` for the eighteen manifest leaves. `key` is the draft key or the leaf semantic path. `family` is the family name. `data_type` is the declared data. `spec_basis` is the specification or public document the row is declared from. `operations` is a comma-separated set drawn from `read`, `write`, `event`, `series` and `command`, or `unknown`. `vendors` names the first vendor. `second_vendor` records corpus membership, a confirmed second vendor, an unconfirmed result, or that a second vendor is not applicable. `promotion` is `promote`, `driver namespace + release report`, or `out of 0.7 (item 30)`. `verification` is `tested_on_hardware` or `not_tested_on_hardware` and does not change promotion or operations. `delivered_by` lists the queue rows taken from the right-hand side of each draft association, or `none`. `uncertainty` records the open point. `sources` cites a public repository revision and path, a specification by title, version and clause, or an operator item. `qualification` is `qualified`, `candidate`, `unknown` or `specification_conflict`. `reason` names why.

## Rows by promotion

| promotion | rows |
| --- | --- |
| promote | 2102 |
| driver namespace + release report | 465 |
| out of 0.7 (item 30) | 4 |

## Rows by package and promotion

| package | promotion | rows |
| --- | --- | --- |
| A | promote | 22 |
| A | driver namespace + release report | 2 |
| A | out of 0.7 (item 30) | 1 |
| B | promote | 227 |
| B | driver namespace + release report | 60 |
| B | out of 0.7 (item 30) | 1 |
| C | promote | 10 |
| C | driver namespace + release report | 4 |
| C | out of 0.7 (item 30) | 1 |
| D | promote | 54 |
| E | promote | 1237 |
| E | driver namespace + release report | 3 |
| F | promote | 552 |
| F | driver namespace + release report | 396 |
| F | out of 0.7 (item 30) | 1 |
