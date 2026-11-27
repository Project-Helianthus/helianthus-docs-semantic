#!/usr/bin/env python3
"""Validate certification-references documents and their acceptance vectors.

``python3 scripts/validate_certification_references_v1.py [VECTORS]`` loads the
vectors file (default ``api/v1/certification-references-vectors-v1.json``) with
repeated object keys refused. Every vector holds a ``document`` and the outcome
``expected`` of the contract in ``api/v1/certification-references-v1.md``: the
validator recomputes the outcome and compares the whole outcome for equality.
A vector may also state ``coverage`` checks, each the coverage of one release by
one entry. The validator then checks the statements that the kernel, the family
catalog and the driver contract make about certification references.

Exit status 0 with a PASS line when every vector and statement holds, 1 otherwise.
"""
import datetime
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

import json_schema_subset_v1 as subset

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "api/v1/certification-references-vectors-v1.json"
SCHEMA = ROOT / "api/v1/certification-references-v1.schema.json"
CONTRACT = "helianthus.semreg.certification-references/v1"
VECTORS_CONTRACT = "helianthus.semreg.certification-references-vectors/v1"
SOURCE = "certification"

COMMON = ("source", "category", "driver", "vendor", "flavor", "model", "firmware")
LOCATION = ("issuer", "url", "retrieved_on")
CATEGORY_MEMBERS = {
    "reference": COMMON + ("issuer", "certificate_number", "issue_date", "stated_value", "url", "retrieved_on"),
    "gap": COMMON + LOCATION,
    "unavailable": COMMON + LOCATION + ("refusal",),
}
TEXT_MEMBERS = ("driver", "vendor", "flavor", "model", "issuer", "certificate_number")
DATE_MEMBERS = ("issue_date", "retrieved_on")
IDENTITY = ("driver", "vendor", "flavor", "model", "firmware")
STATED_MEMBERS = (
    "measurement_type", "measured", "ratio_maximum", "measured_minimum",
    "measured_maximum", "range_minimum", "range_maximum", "statement",
)
DECIMAL_MEMBERS = ("ratio_maximum", "measured_minimum", "measured_maximum", "range_minimum", "range_maximum")
UPPER_BOUND_SOURCES = ("certificate", "vendor_document")
FIRMWARE_FORMS = {
    "not_stated": (),
    "release": ("release",),
    "range": ("from", "to", "upper_bound_stated_by"),
}
REASONS = (
    "schema", "source_not_certification", "unknown_member", "missing_member",
    "stated_value_not_allowed", "refusal_missing", "invalid_value", "firmware_invalid",
    "firmware_upper_bound_unstated", "stated_value_invalid", "category_conflict",
)
COVERAGE = ("covered", "not_covered", "not_stated")
RELEASE = re.compile(r"[0-9]+(\.[0-9]+)*")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
COEFFICIENT = re.compile(r"0|-?[1-9]([0-9]*[1-9])?")


class Finding(NamedTuple):
    """One rejection: the stable reason, the entry index and the member, when any."""

    reason: str
    entry: "int | None" = None
    member: "str | None" = None


def release_key(release):
    """Return the numeric components of a release, the order of its comparison."""
    return tuple(int(part) for part in release.split("."))


def compare_releases(left, right):
    """Compare two releases component by component, a missing component being zero."""
    a, b = release_key(left), release_key(right)
    size = max(len(a), len(b))
    a, b = a + (0,) * (size - len(a)), b + (0,) * (size - len(b))
    return (a > b) - (a < b)


def coverage(firmware, release):
    """Return covered, not_covered or not_stated for a release against a firmware record."""
    form = firmware["form"]
    if form == "not_stated":
        return "not_stated"
    floor = firmware["release"] if form == "release" else firmware["from"]
    if compare_releases(release, floor) < 0:
        return "not_covered"
    if form == "range" and compare_releases(release, firmware["to"]) > 0:
        return "not_covered"
    return "covered"


def first_member(entry, names, test):
    """Return the first name of the entry for which the test holds."""
    return next((name for name in names if name in entry and test(entry[name])), None)


def is_text(value):
    return isinstance(value, str) and bool(value)


def is_date(value):
    if not isinstance(value, str) or not DATE.fullmatch(value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_url(value):
    return isinstance(value, str) and re.fullmatch(r"https://[^ ]+", value) is not None


def is_decimal(value):
    if not isinstance(value, dict) or set(value) != {"coefficient", "exponent10"}:
        return False
    coefficient, exponent = value["coefficient"], value["exponent10"]
    if not isinstance(coefficient, str) or not COEFFICIENT.fullmatch(coefficient):
        return False
    if type(exponent) is not int or not -18 <= exponent <= 18:
        return False
    return coefficient != "0" or exponent == 0


def check_source(entry):
    if "source" in entry and entry["source"] != SOURCE:
        return Finding("source_not_certification", member="source")
    return None


def check_category(entry):
    if "category" not in entry:
        return Finding("missing_member", member="category")
    if entry["category"] not in tuple(CATEGORY_MEMBERS):
        return Finding("invalid_value", member="category")
    return None


def check_members(entry):
    allowed = CATEGORY_MEMBERS[entry["category"]]
    if entry["category"] != "reference" and "stated_value" in entry:
        return Finding("stated_value_not_allowed", member="stated_value")
    extra = sorted(set(entry) - set(allowed))
    if extra:
        return Finding("unknown_member", member=extra[0])
    if entry["category"] == "unavailable" and not is_text(entry.get("refusal")):
        return Finding("refusal_missing", member="refusal")
    missing = [name for name in allowed if name not in entry]
    return Finding("missing_member", member=missing[0]) if missing else None


def check_values(entry):
    bad = first_member(entry, TEXT_MEMBERS, lambda value: not is_text(value))
    bad = bad or first_member(entry, DATE_MEMBERS, lambda value: not is_date(value))
    bad = bad or first_member(entry, ("url",), lambda value: not is_url(value))
    return Finding("invalid_value", member=bad) if bad else None


def check_firmware(entry):
    firmware = entry["firmware"]
    if not isinstance(firmware, dict) or firmware.get("form") not in tuple(FIRMWARE_FORMS):
        return Finding("firmware_invalid", member="firmware")
    if firmware["form"] == "range" and firmware.get("upper_bound_stated_by") not in UPPER_BOUND_SOURCES:
        return Finding("firmware_upper_bound_unstated", member="firmware")
    if set(firmware) != {"form", *FIRMWARE_FORMS[firmware["form"]]}:
        return Finding("firmware_invalid", member="firmware")
    releases = [firmware[name] for name in ("release", "from", "to") if name in firmware]
    if not all(isinstance(item, str) and RELEASE.fullmatch(item) for item in releases):
        return Finding("firmware_invalid", member="firmware")
    if firmware["form"] == "range" and compare_releases(firmware["from"], firmware["to"]) > 0:
        return Finding("firmware_invalid", member="firmware")
    return None


def valid_stated_value(stated):
    if not isinstance(stated, dict) or not set(stated) <= set(STATED_MEMBERS):
        return False
    measurement_type = stated.get("measurement_type")
    if not isinstance(measurement_type, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", measurement_type):
        return False
    values = set(stated) - {"measurement_type"}
    if not values or ("measured" in values and type(stated["measured"]) is not bool):
        return False
    if "statement" in values and not is_text(stated["statement"]):
        return False
    return all(is_decimal(stated[name]) for name in values & set(DECIMAL_MEMBERS))


def check_stated_value(entry):
    if "stated_value" not in entry:
        return None
    if not valid_stated_value(entry["stated_value"]):
        return Finding("stated_value_invalid", member="stated_value")
    return None


ENTRY_CHECKS = (check_source, check_category, check_members, check_values, check_firmware, check_stated_value)


def check_entry(entry, index):
    """Return the first Finding of one entry, or None."""
    if not isinstance(entry, dict):
        return Finding("schema", index)
    for check in ENTRY_CHECKS:
        found = check(entry)
        if found:
            return found._replace(entry=index)
    return None


def identity(entry):
    """Return the device identity of an entry: driver, vendor, flavor, model and firmware."""
    return json.dumps([entry[name] for name in IDENTITY], sort_keys=True)


def check_categories(entries):
    """Reject two entries of different categories for one device identity."""
    seen = {}
    for index, entry in enumerate(entries):
        key = identity(entry)
        if key in seen and seen[key][0] != entry["category"]:
            return Finding("category_conflict", index)
        seen.setdefault(key, (entry["category"], index))
    return None


def check_document(document, schema):
    """Return the Finding of a document, or None when it is valid."""
    entries = document.get("entries") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        return Finding("schema")
    for index, entry in enumerate(entries):
        found = check_entry(entry, index)
        if found:
            return found
    if subset.errors(document, schema):
        return Finding("schema")
    return check_categories(entries)


def outcome(finding):
    """Return the canonical outcome of a Finding."""
    if finding is None:
        return {"accepted": True}
    result = {"accepted": False, "reason": finding.reason}
    if finding.entry is not None:
        result["entry"] = finding.entry
    if finding.member is not None:
        result["member"] = finding.member
    return result


def check_coverage(vector):
    """Return the errors of the coverage checks of one vector."""
    errors = []
    entries = vector["document"]["entries"]
    for check in vector.get("coverage", []):
        actual = coverage(entries[check["entry"]]["firmware"], check["release"])
        if actual != check["result"]:
            errors.append(f"{vector['id']}: release {check['release']} is {actual}, expected {check['result']}")
    return errors


def check_vector(vector, schema):
    """Return the errors of one vector."""
    actual = outcome(check_document(vector["document"], schema))
    if actual != vector["expected"]:
        return [f"{vector['id']}: outcome {actual} differs from expected {vector['expected']}"]
    return check_coverage(vector)


def check_vector_set(vectors, schema):
    """Check every vector and the vocabulary the vectors must cover."""
    ids = [vector["id"] for vector in vectors]
    errors = [] if len(ids) == len(set(ids)) else ["vector ids are not unique"]
    for vector in vectors:
        errors += check_vector(vector, schema)
    reasons = {vector["expected"].get("reason") for vector in vectors} - {None}
    errors += [f"reason without a vector: {reason}" for reason in REASONS if reason not in reasons]
    errors += [f"reason outside the contract: {reason}" for reason in sorted(reasons - set(REASONS))]
    seen = {check["result"] for vector in vectors for check in vector.get("coverage", [])}
    errors += [f"coverage result without a vector: {result}" for result in COVERAGE if result not in seen]
    return errors


STATEMENTS = {
    "api/v1/kernel.md": [
        "`OriginKind` is `native_observation`, `derived`, `declared`, `operator`, `automation`, or `projection`",
        "A declared origin omits native source fields and carries 1 through 32 unique evidence references",
    ],
    "api/v1/family-catalog-v1.md": ["`specification`, `hardware_test_record`, `certification`, `issue` or `pull_request`"],
    "api/v1/driver-contract.md": [
        "origin kind `declared` and certification evidence",
        "lower priority than every device source",
        "never published beside a device value for the same fact key",
    ],
}


def check_statements(root=ROOT):
    """Return the statements of the other pages that are missing."""
    errors = []
    for name, statements in STATEMENTS.items():
        flat = " ".join((root / name).read_text(encoding="utf-8").split())
        errors += [f"{name}: statement missing: {text}" for text in statements if text not in flat]
    page = root / "api/v1/certification-references-v1.md"
    flat = " ".join(page.read_text(encoding="utf-8").split())
    errors += [f"{page.name}: reason not stated: {reason}" for reason in REASONS if f"| `{reason}` |" not in flat]
    return errors


def load(path):
    return subset.load_json(path)


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) > 1:
        print("usage: validate_certification_references_v1.py [VECTORS]", file=sys.stderr)
        return 1
    try:
        document = load(Path(args[0]) if args else VECTORS)
        schema = load(SCHEMA)
        subset.check_schema(schema)
        if document.get("contract") != VECTORS_CONTRACT:
            raise ValueError("vectors contract identifier differs")
        errors = check_vector_set(document["vectors"], schema) + check_statements()
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"PASS: {len(document['vectors'])} certification reference vectors hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
