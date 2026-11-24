#!/usr/bin/env python3
"""Check the public scope denominator against its draft and promotion rules."""

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

COLUMNS = [
    "package", "slice", "key", "family", "data_type", "spec_basis", "operations",
    "vendors", "second_vendor", "promotion", "verification", "delivered_by",
    "uncertainty", "sources", "qualification", "reason",
]
DRAFT_COLUMNS = [
    "part", "key", "family", "data_type", "spec_basis", "operations",
    "vendors_in_local_corpus", "second_vendor", "promotion", "row_or_ticket",
    "uncertainty", "sources",
]
OP_ORDER = ["read", "write", "event", "series", "command"]
QUEUE_ID = re.compile(r"\b([A-Z]{2}\d{2})\b")
LEAF_PATHS = [
    "/dhw/operating_mode",
    "/dhw/operation_mode_changeable",
    "/dhw/overrun_active",
    "/dhw/target_temperature_c",
    "/dhw/temperature_c",
    "/system/gateway_brand",
    "/system/gateway_vendor",
    "/system/outside_air_temperature_c",
    "/zones/zone_1/name",
    "/zones/zone_1/operating_mode",
    "/zones/zone_1/operation_mode_changeable",
    "/zones/zone_1/room_temperature_c",
    "/zones/zone_1/target_temperature_c",
    "/zones/zone_2/name",
    "/zones/zone_2/operating_mode",
    "/zones/zone_2/operation_mode_changeable",
    "/zones/zone_2/room_temperature_c",
    "/zones/zone_2/target_temperature_c",
]
OUTBACK = {
    ("A", "outback-axs"),
    ("b-energy", "MB-056"),
    ("C", "outback.axs.write-control"),
    ("f-modbus-can", "outback-axs/models-64110-64111"),
}
GRID = {
    ("b-energy", "MB-048"),
    ("b-energy", "MB-055"),
    ("b-energy", "MB-088"),
    ("C", "sunspec.grid-code-settings"),
    ("f-modbus-can", "sunspec/model-125-145"),
    ("f-modbus-can", "sunspec/model-703"),
    ("f-modbus-can", "sunspec/model-707-709"),
}
F_GRID = {
    "sunspec/model-125-145": set(range(125, 146)),
    "sunspec/model-703": {703},
    "sunspec/model-707-709": {707, 708, 709},
}
DRIVER_NAMED = {
    ("e-eebus", "SPINE-UC:monitoringAndControlOfSmartGridReadyConditions"),
    ("A", "brink-ebus-ventilation"),
    ("f-ebus-controller-1", "ebus-vaillant-controller/B524/OP02/GG00/RR00F0"),
}
PROMOTE_NAMED = {
    ("b-eebus", "can.operating_state"),
    ("b-eebus", "eebus.inbound.dhw.mode_changeable"),
    ("b-eebus", "eebus.inbound.zone.mode_changeable"),
    ("b-eebus", "eebus.inbound.gateway_brand"),
    ("b-eebus", "eebus.inbound.gateway_vendor"),
    ("b-energy", "MB-063-day"),
    ("e-eebus", "SPINE:HVAC.overrun"),
    ("e-eebus", "SPINE:DeviceDiagnosis.serviceNeeded"),
}
PROMOTIONS = {"promote", "driver namespace + release report", "out of 0.7 (item 30)"}
QUALIFICATIONS = {"qualified", "candidate", "unknown", "specification_conflict"}
DELIVERED = {
    ("C", "pv.operation.set_active_power_limit"): "ND02,MM06,BT02,SS08,RR05,MM05,MM08",
    ("C", "storage.operation.set_charge_limit"): "ND02,MM06,SS08,QQ12,QQ14",
    ("C", "storage.operation.set_discharge_limit"): "ND02,MM06,QQ12,QQ14",
}
SUPERSEDED = re.compile(
    r"NO_SEND|raw-only quarantine|documentary-only|documentary only|control-observability|"
    r"creates no operation|create no operation|create no write|creates no write|"
    r"not declared as writes|no write method|no write permission",
    re.I,
)
GREE_BAD = re.compile(
    r"receive-only|receive only|no command encoder|no transmit path|"
    r"commands are disabled|documentation only|writes are disabled",
    re.I,
)
PAIR = re.compile(r"(\d+)/([A-Za-z0-9_.]+)=(R|RW|W|unknown)\b")
SHA_PATH = re.compile(r"docs-(modbus|canbus)@([0-9a-f]{40}):(\S+)")
SPEC_EVIDENCE = re.compile(
    r"@[0-9a-f]{12,40}:|SPINE 1\.3\.0|SHIP 1\.0\.1|SunSpec|Protocol II v1\.24|"
    r"OPERATOR item \d+|Monitoring of |Configuration of |Control of |Visualization of |Limitation of |"
    r"Matter 1\.6\.1|EV Charging|Overload Protection|MOB-|MOI-|CDT-|CRHT-|CDSF-|CRHSF-|VHAN-|COB-|LPP-|LPC-"
)


def leakage_re():
    volume = "/" + "Vol" + "umes/"
    users = "/" + "Us" + "ers/"
    home = "/" + "ho" + "me/"
    parts = [
        re.escape(volume),
        re.escape(users),
        re.escape(home),
        "scratch" + "pad",
        "NOTES" + r"\.md",
        "QUEUE" + r"\.tsv",
        "OPERATOR" + r"\.md:",
        "tickets" + r"\.json",
    ]
    # The filename token is case-sensitive. A lowercase catalog word is not that file.
    exact = "(?-i:" + "CROSS" + "WALK" + ")"
    return re.compile("(?:%s)|%s" % ("|".join(parts), exact), re.I)


PUBLIC_CELL_SKIP = {
    "package", "slice", "key", "operations", "promotion",
    "verification", "qualification", "delivered_by",
}


def private_locator_re():
    """Private audit files, plan ids and local notes. Public citations stay."""
    plan = r"(?:PA|PB|PC|PD|PE|PF|PG)\d{2}"
    parts = [
        r"E/comparison\b",
        r"(?<![\w./-])comparison\.md",
        r"\bcomparison index\b",
        r"Chapter index:\s*audit\b",
        r"\bidentifier harvest\b",
        r"\bdirectory listing\b",
        r"\bNOTES\b",
        r"\bPrivate VRF research\b",
        r"ship-spine",
        r"\blocal files\b",
        r"\baudit\s+(?:0?3|A\b|package\b|cell\b|index\b|bundle\b|key\b|text\b|controllable\b)",
        r"(?i:\bAudit\s+(?:bundle|letter|says|binds|semreg)\b)",
        r"(?i:\bAudit\s+text\s+says\b)",
        r"(?i:\bAudit\s+row\s+says\b)",
        r"(?i:\baudit\s+0\d\b)",
        r"(?i:\baudit ticket\b)",
        r"(?i:\bthe audit\b)",
        r"LEAD-MAP",
        r"\bRECONCILE\b",
        r"\bQUEUE\b",
        r"\bis not in or\b",
        r"\bCW\d{2}\b",
        r"\bAudit\s+E\b",
        r"\bPE\s+rows\b",
        r"\bnew_home\b",
        r"05-matter\.md",
        r"COMMANDMENTS\.md",
        r"proposals\.md",
        r"\bB-eebus(?:-remote)?\b",
        r"(?:→|->)",
        r"(?<!\d/)" + plan + r"\b",
        r"\bGT-(?:E)?\d+\b",
        r"\bzip PDF\b",
        r"control/drafts/",
        r"Helianthus Project/",
        r"chapter headings:\d",
        r"Matter index lines \d",
        r"eeBUS index lines \d",
    ]
    return re.compile("|".join(parts))


def check_public_cells(rows, label):
    pattern = private_locator_re()
    errors = []
    for row in rows:
        for column, value in row.items():
            if column in PUBLIC_CELL_SKIP:
                continue
            if pattern.search(value):
                errors.append(
                    label + " " + row.get("slice", "") + " " + row.get("key", "")
                    + " " + column + " cites a private locator"
                )
    return errors


def delivered_by(cell):
    if not cell or cell.strip().lower() in {"none", ""}:
        return "none"
    found = []
    for chunk in cell.split(";"):
        if "→" not in chunk and "->" not in chunk:
            continue
        rhs = re.split(r"→|->", chunk, maxsplit=1)[1]
        for match in QUEUE_ID.findall(rhs):
            if match not in found:
                found.append(match)
    return ",".join(found) if found else "none"


def load_tsv(path, columns):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    errors = []
    if not lines:
        return [], ["empty " + Path(path).name]
    for index, line in enumerate(lines, 1):
        if line.endswith(" ") or line.endswith("\t"):
            errors.append(f"{Path(path).name}:{index} trailing whitespace")
        if len(line.split("\t")) != len(columns):
            errors.append(f"{Path(path).name}:{index} expected {len(columns)} columns")
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != columns:
            errors.append(Path(path).name + " header mismatch")
            return [], errors
        return list(reader), errors


def ops_set(value):
    if value == "unknown":
        return set()
    return set(value.split(",")) if value else set()


def union_from_pairs(pairs):
    found = set()
    stated = False
    for _model, _point, access in pairs:
        if access == "R":
            found.add("read")
            stated = True
        elif access == "RW":
            found.update(("read", "write"))
            stated = True
        elif access == "W":
            found.add("write")
            stated = True
    if not stated:
        return "unknown"
    return ",".join(op for op in OP_ORDER if op in found)


def blob(checkout, sha, rel):
    if not checkout:
        return None
    spec = sha + ":" + rel
    probe = subprocess.run(
        ["git", "-C", checkout, "cat-file", "-e", spec],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        return None
    shown = subprocess.run(
        ["git", "-C", checkout, "show", spec],
        capture_output=True,
        text=True,
    )
    if shown.returncode != 0:
        return None
    return shown.stdout


def parse_model_points(text):
    parts = re.split(r"(?m)^## Model (\d+)\s*$", text)
    found = {}
    index = 1
    while index + 1 < len(parts):
        model = int(parts[index])
        body = parts[index + 1]
        index += 2
        if re.search(r"catalog defines none|defines no points|no points", body, re.I):
            found[model] = []
            continue
        found[model] = table_points(body)
    return found


def table_points(body):
    points = []
    header = None
    for line in body.splitlines():
        if not line.startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header is None:
            header = [cell.lower() for cell in cells]
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        try:
            point_at = next(i for i, name in enumerate(header) if name.startswith("point"))
            access_at = next(i for i, name in enumerate(header) if "access" in name)
        except StopIteration:
            continue
        if point_at >= len(cells) or access_at >= len(cells):
            continue
        access = cells[access_at].upper()
        if access not in {"R", "RW", "W"}:
            access = "unknown"
        points.append((cells[point_at], access))
    return points


def citation(row, suffix):
    blob_text = row["sources"] + " " + row["spec_basis"]
    for repo, sha, path in SHA_PATH.findall(blob_text):
        if path.startswith(suffix) or path.split(";")[0] == suffix:
            return repo, sha, suffix
    return None


def pending_page(row):
    text = (row["spec_basis"] + " " + row["uncertainty"]).lower()
    return "pending" in text


def has_all(text, phrases):
    return all(phrase in text for phrase in phrases)


def affirmative(text, pattern):
    for sentence in re.split(r"(?<=\.)\s+", text):
        if pattern.search(sentence) and not re.search(r"\b(does not|do not|not say)\b", sentence, re.I):
            return sentence
    return ""


def expected_promotion(row, draft):
    key = (row["slice"], row["key"])
    if key in OUTBACK:
        return "out of 0.7 (item 30)"
    if row["package"] == "D":
        return "promote"
    if key in GRID or key in DRIVER_NAMED:
        return "driver namespace + release report"
    if key in PROMOTE_NAMED:
        return "promote"
    second = row["second_vendor"]
    if second.startswith("not applicable"):
        return draft["promotion"].strip() if draft else row["promotion"]
    if second.startswith("unconfirmed"):
        return "driver namespace + release report"
    if second.startswith("confirmed:"):
        return "promote"
    if second.startswith("in corpus (Matter)") or second.startswith("in corpus (eeBUS)"):
        blob_text = row["uncertainty"] + " " + row["data_type"]
        if (
            "does not supply this row's same semantic proposition" in blob_text
            or "are different data" in blob_text
        ):
            return "driver namespace + release report"
        return "promote"
    if draft:
        return draft["promotion"].strip()
    return row["promotion"]


def check_rows(rows, draft_rows, readme, scope_dir, docs_modbus, docs_canbus):
    errors = []
    pending = []
    by_key = {(row["slice"], row["key"]): row for row in rows}
    draft_by = {(row["part"], row["key"]): row for row in draft_rows}
    if len(by_key) != len(rows):
        errors.append("duplicate package slice key")
    draft_pairs = set(draft_by)
    leaf_pairs = {("cross-protocol", path) for path in LEAF_PATHS}
    product_pairs = {(row["slice"], row["key"]) for row in rows}
    expected_pairs = draft_pairs | leaf_pairs
    if product_pairs != expected_pairs:
        missing = sorted(expected_pairs - product_pairs)[:8]
        extra = sorted(product_pairs - expected_pairs)[:8]
        errors.append("membership mismatch missing " + str(missing) + " extra " + str(extra))
    for path in LEAF_PATHS:
        row = by_key.get(("cross-protocol", path))
        if row is None:
            errors.append("missing manifest leaf " + path)
            continue
        if row["package"] != "B" or "read" not in ops_set(row["operations"]):
            errors.append(path + " must be package B and include read")
        if row["operations"] == "unknown":
            errors.append(path + " operations unknown")

    unconfirmed = []
    seen = set()
    for row in rows:
        key = (row["slice"], row["key"])
        seen.add(key)
        if row["promotion"] not in PROMOTIONS:
            errors.append(f"{key} promotion {row['promotion']}")
        if row["qualification"] not in QUALIFICATIONS or not row["reason"]:
            errors.append(f"{key} qualification or reason")
        if row["verification"] not in {"tested_on_hardware", "not_tested_on_hardware"}:
            errors.append(f"{key} verification")
        if row["verification"] == "tested_on_hardware" and not re.search(r"@[0-9a-f]{12,40}:", row["sources"]):
            errors.append(f"{key} hardware record is not cited")
        if row["operations"] != "unknown":
            parts = row["operations"].split(",")
            ordered = [op for op in OP_ORDER if op in parts]
            if parts != ordered or len(parts) != len(set(parts)):
                errors.append(f"{key} operations {row['operations']}")
        draft = draft_by.get(key)
        if draft and row["delivered_by"] != delivered_by(draft["row_or_ticket"]):
            errors.append(f"{key} delivered_by {row['delivered_by']}")
        if key in DELIVERED and row["delivered_by"] != DELIVERED[key]:
            errors.append(f"{key} delivered_by lost a named queue id")
        if not draft and row["delivered_by"] != "none":
            errors.append(f"{key} leaf delivered_by")
        if expected_promotion(row, draft) != row["promotion"]:
            errors.append(f"{key} promotion {row['promotion']} disagrees with the rule")
        if row["qualification"] == "qualified":
            if row["reason"] != "declared_by_specification":
                errors.append(f"{key} qualified reason")
            if row["sources"].strip() == "no public source" or not SPEC_EVIDENCE.search(row["sources"]):
                errors.append(f"{key} qualified without specification evidence")
        if row["package"] == "D" and draft and draft["promotion"].strip() != "promote":
            if row["second_vendor"] != "not applicable (SemReg structure)":
                errors.append(f"{key} SemReg structure second vendor")
        if row["promotion"] == "driver namespace + release report":
            unconfirmed.append(row)
        if key in OUTBACK:
            if "outback" not in row["key"] and "outback" not in row["family"].lower():
                errors.append(f"{key} is not an OutBack row")
            if "0.8" not in row["uncertainty"]:
                errors.append(f"{key} does not schedule 0.8")
    check_named(by_key, errors, pending, docs_modbus, docs_canbus)
    subset_path = scope_dir / "second-vendor-unconfirmed.tsv"
    subset, subset_errors = load_tsv(subset_path, COLUMNS)
    errors.extend(subset_errors)
    if [row["slice"] + row["key"] + row["promotion"] for row in subset] != [
        row["slice"] + row["key"] + row["promotion"] for row in unconfirmed
    ]:
        if len(subset) == len(unconfirmed):
            errors.append("unconfirmed subset rows differ")
        else:
            errors.append(f"unconfirmed subset {len(subset)} != {len(unconfirmed)}")
    errors.extend(check_readme(readme, rows))
    errors.extend(check_leakage(scope_dir))
    errors.extend(check_public_cells(rows, "denominator"))
    errors.extend(check_public_cells(subset, "unconfirmed"))
    return errors, pending


def check_named(by_key, errors, pending, docs_modbus, docs_canbus):
    def row(slice_name, key):
        found = by_key.get((slice_name, key))
        if found is None:
            errors.append("missing " + slice_name + " " + key)
        return found

    def blob_of(*rows):
        return " ".join(
            " ".join(item[name] for name in ("data_type", "spec_basis", "uncertainty", "operations", "sources"))
            for item in rows if item
        )

    zone = row("b-eebus", "eebus.inbound.zone.mode_changeable")
    z1 = row("cross-protocol", "/zones/zone_1/operation_mode_changeable")
    z2 = row("cross-protocol", "/zones/zone_2/operation_mode_changeable")
    if zone and z1 and z2:
        for item in (zone, z1, z2):
            if not (
                item["promotion"] == "promote"
                and item["second_vendor"] == "in corpus (eeBUS)"
                and item["operations"] == "read"
                and "isOperationModeIdChangeable" in item["spec_basis"]
            ):
                errors.append(item["key"] + " changeable flag disposition")
        if zone["promotion"] == "driver namespace + release report":
            errors.append("zone changeable flag is in the unconfirmed disposition")

    inbound = row("A", "eebus-inbound")
    if inbound:
        text = inbound["data_type"] + inbound["spec_basis"] + inbound["uncertainty"]
        if inbound["qualification"] != "qualified" or inbound["reason"] != "declared_by_specification":
            errors.append("eebus-inbound qualification")
        for phrase in ("state unknown", "exact revisions unresolved", "unknown_pending_normative_source"):
            if phrase in text:
                errors.append("eebus-inbound keeps " + phrase)
        for title in (
            "HVAC Temperature use cases 1.0.0",
            "HVAC System Function use cases 1.0.0",
            "Monitoring of Inverter 1.0.0",
            "Monitoring of Battery 1.0.0",
            "SPINE 1.3.0",
            "SHIP 1.0.1",
        ):
            if title not in inbound["sources"]:
                errors.append("eebus-inbound sources miss " + title)

    for slice_name, key in list(by_key):
        item = by_key[(slice_name, key)]
        zone_row = key.startswith("eebus.inbound.zone") or key.startswith("/zones/")
        if not zone_row:
            continue
        text = item["uncertainty"]
        if "first pairs fill" in text:
            errors.append(key + " fills zone slots from the first pairs")
        for phrase in (
            "device-address",
            "malformed",
            "unequal",
            "unresolved",
            "no unconditional zone fill",
        ):
            if phrase not in text:
                errors.append(key + " pairing omits " + phrase)

    gree_family = ("gree-vrf-can", "gree vrf can")
    for item in by_key.values():
        gree = (
            item["family"].lower() in gree_family
            or item["key"].startswith("gree.vrf.")
            or item["key"].startswith("gree-vrf-can/")
            or item["key"] == "canbus.gree-vrf.command"
        )
        if not gree:
            continue
        text = item["data_type"] + " " + item["spec_basis"] + " " + item["uncertainty"]
        if "semantic_mapping_unknown" in text:
            errors.append(item["key"] + " keeps semantic_mapping_unknown")
        bad = affirmative(text, GREE_BAD)
        if bad:
            errors.append(item["key"] + " keeps a disabled-command sentence")
    issue60 = row("f-modbus-can", "gree-vrf-can/issue-60-maps")
    if issue60 and "label_only" not in issue60["data_type"]:
        errors.append("issue-60-maps lost label_only")
    gree_a = row("A", "gree-vrf-can")
    if gree_a and gree_a["operations"] != "read,command":
        errors.append("gree-vrf-can operations")
    command = row("C", "canbus.gree-vrf.command")
    if command and command["operations"] != "command":
        errors.append("gree command operations")
    check_gree_pages(gree_a, by_key, errors, pending, docs_canbus)

    for key, models in F_GRID.items():
        item = row("f-modbus-can", key)
        if item:
            check_grid_row(item, models, errors, pending, docs_modbus, require_unknown=True)
    for key, models in {"MB-048": {707, 708, 709}, "MB-055": set(range(125, 146))}.items():
        item = row("b-energy", key)
        if item:
            check_grid_row(item, models, errors, pending, docs_modbus, require_unknown=False)
    sunspec = row("C", "sunspec.grid-code-settings")
    if sunspec:
        if "command" not in ops_set(sunspec["operations"]):
            errors.append("sunspec.grid-code-settings lost command")
        check_grid_row(
            sunspec,
            set(range(125, 146)) | {707, 708, 709},
            errors,
            pending,
            docs_modbus,
            require_unknown=False,
            keep_command=True,
        )
    huawei = row("b-energy", "MB-088")
    if huawei:
        if "ma-v200.control.frequency_power_42040=RW" not in huawei["spec_basis"]:
            errors.append("MB-088 omitted ma-v200.control.frequency_power_42040=RW")
        if not {"read", "write"} <= ops_set(huawei["operations"]):
            errors.append("MB-088 omitted the documented RW operation")
        check_huawei_grid(huawei, errors, pending, docs_modbus)

    spine = row("e-eebus", "SPINE-UC:monitoringAndControlOfSmartGridReadyConditions")
    overrun = row("e-eebus", "SPINE:HVAC.overrun")
    if spine:
        if spine["operations"] != "unknown":
            errors.append("SPINE-UC operations")
        if not has_all(spine["spec_basis"], ("sgReadyCondition1", "sgReadyCondition3", "sgReadyCondition4")):
            errors.append("SPINE-UC lost XSD literals")
        if "thermal.overrun.sg_ready_condition_1" in spine["data_type"]:
            errors.append("SPINE-UC still carries the overrun elements")
        if spine["qualification"] != "unknown" or "not available" not in spine["reason"]:
            errors.append("SPINE-UC qualification")
    if overrun:
        if overrun["operations"] != "read,write":
            errors.append("HVAC.overrun operations")
        if "isOverrunStatusChangeable" not in overrun["spec_basis"]:
            errors.append("HVAC.overrun changeable status")
        if not has_all(overrun["data_type"], (
            "thermal.overrun.sg_ready_condition_1",
            "thermal.overrun.sg_ready_condition_3",
            "thermal.overrun.sg_ready_condition_4",
        )):
            errors.append("HVAC.overrun lost sg-ready elements")

    needed = row("e-eebus", "SPINE:DeviceDiagnosis.serviceNeeded")
    if needed:
        if needed["operations"] != "read":
            errors.append("serviceNeeded operations")
        text = needed["spec_basis"] + needed["uncertainty"] + needed["data_type"]
        if "DeviceDiagnosisOperatingStateEnumType" not in text or "thermal.event.maintenance_due" not in needed["uncertainty"]:
            errors.append("serviceNeeded state evidence")
        if "absent from" in text and "xsd" in text.lower():
            errors.append("serviceNeeded keeps the absent-identifier sentence")

    check_bindings(by_key, errors)
    check_vendor_rows(by_key, errors, pending, docs_modbus, docs_canbus)


def check_bindings(by_key, errors):
    pairs = [
        ("b-eebus", "eebus.inbound.dhw.setpoint", "cross-protocol", "/dhw/target_temperature_c", ("DHWCircuit", "CDT-001", "Setpoint.setpointListData"), ("CRHT-001",)),
        ("b-eebus", "eebus.inbound.zone.setpoint", "cross-protocol", "/zones/zone_1/target_temperature_c", ("HVACRoom", "CRHT-001", "Setpoint.setpointListData"), ("CDT-001",)),
    ]
    for left_slice, left_key, right_slice, right_key, need, forbid in pairs:
        left = by_key.get((left_slice, left_key))
        right = by_key.get((right_slice, right_key))
        sibling = by_key.get(("cross-protocol", "/zones/zone_2/target_temperature_c")) if "zone_1" in right_key else right
        for item in (left, right, sibling):
            if item is None:
                errors.append("missing binding " + left_key)
                continue
            text = item["spec_basis"] + item["uncertainty"]
            if item["operations"] != "read,write" or not has_all(text, need) or any(phrase in text for phrase in forbid):
                errors.append(item["key"] + " setpoint binding")
    dhw_mode = by_key.get(("b-eebus", "eebus.inbound.dhw.mode"))
    dhw_leaf = by_key.get(("cross-protocol", "/dhw/operating_mode"))
    for item in (dhw_mode, dhw_leaf):
        if item is None:
            errors.append("missing dhw mode")
            continue
        text = item["spec_basis"]
        if item["operations"] != "read,write" or not has_all(text, ("DHWCircuit", "CDSF-001", "isOperationModeIdChangeable=true")):
            errors.append(item["key"] + " dhw mode binding")
        if "CRHSF-001" in text:
            errors.append(item["key"] + " borrowed the room source")
    for key in ("eebus.inbound.zone.mode",):
        item = by_key.get(("b-eebus", key))
        if item is None or not mode_condition(item, ""):
            errors.append("zone mode condition")
    for path, label in (("/zones/zone_1/operating_mode", "zone 1"), ("/zones/zone_2/operating_mode", "zone 2")):
        item = by_key.get(("cross-protocol", path))
        other = "zone 2" if label == "zone 1" else "zone 1"
        if item is None or not mode_condition(item, label) or ("this " + other) in (item["spec_basis"] + item["uncertainty"]):
            errors.append(path + " room condition")
    overrun = by_key.get(("b-eebus", "eebus.inbound.dhw.one_time_charge"))
    leaf = by_key.get(("cross-protocol", "/dhw/overrun_active"))
    for item in (overrun, leaf):
        if item is None:
            errors.append("missing overrun")
            continue
        text = item["spec_basis"]
        if item["operations"] != "read,write" or not has_all(text, (
            "isOverrunActive", "hvacSystemFunctionListData", "hvacOverrunListData", "overrunStatus", "CDSF-002", "CDSF-003",
        )):
            errors.append(item["key"] + " overrun bindings")
    name = by_key.get(("b-eebus", "eebus.inbound.zone.name"))
    if name is None or name["operations"] != "read" or not has_all(name["spec_basis"], ("userLabel", "VHAN-002")):
        errors.append("zone name read")
    for path in ("/zones/zone_1/name", "/zones/zone_2/name"):
        item = by_key.get(("cross-protocol", path))
        if item is None or "STABLE_ZONE_PSEUDONYM" not in item["spec_basis"] or item["operations"] != "read":
            errors.append(path + " public transform")


def mode_condition(item, label):
    text = item["spec_basis"] + item["uncertainty"]
    if item["operations"] != "read,write":
        return False
    if not has_all(text, ("HVACRoom", "CRHSF-001", "explicitly true", "False", "Absent")):
        return False
    if label and ("this " + label) not in text and ("This leaf is " + label) not in text:
        return False
    return True


def check_grid_row(item, models, errors, pending, checkout, require_unknown, keep_command=False):
    for field in ("data_type", "spec_basis", "uncertainty", "operations"):
        if SUPERSEDED.search(item[field]):
            errors.append(item["key"] + " keeps a superseded grid statement in " + field)
    pairs = PAIR.findall(item["spec_basis"])
    if not pairs:
        if require_unknown and item["operations"] != "unknown":
            errors.append(item["key"] + " recorded an operation without stated point access")
        if keep_command and item["operations"] != "command":
            errors.append(item["key"] + " invented a point operation or lost command")
        pending.append(item["key"] + " point access")
        return
    derived = union_from_pairs(pairs)
    actual = item["operations"]
    if keep_command:
        if "command" not in ops_set(actual):
            errors.append(item["key"] + " lost command")
        actual = ",".join(op for op in OP_ORDER if op in ops_set(actual) - {"command"}) or "unknown"
    if actual != derived:
        errors.append(item["key"] + " operations do not match its point pairs")
    cited = citation(item, "protocols/sunspec/grid-code-settings-v1.md")
    if pending_page(item) or cited is None:
        pending.append(item["key"] + " ND02 grid page")
        return
    body = blob(checkout, cited[1], cited[2])
    if body is None:
        pending.append(item["key"] + " ND02 grid blob")
        return
    parsed = parse_model_points(body)
    expected = []
    for model in sorted(models):
        if model not in parsed:
            errors.append(item["key"] + " missing model section " + str(model))
            continue
        for point, access in parsed[model]:
            expected.append((str(model), point, access))
    if sorted(pairs) != sorted(expected):
        errors.append(item["key"] + " point access pairs differ from the cited sections")


def check_huawei_grid(item, errors, pending, checkout):
    for field in ("data_type", "spec_basis", "uncertainty", "operations"):
        if SUPERSEDED.search(item[field]):
            errors.append("MB-088 keeps a superseded grid statement")
    cited = citation(item, "protocols/huawei/grid-code-settings-v1.md")
    if pending_page(item) or cited is None:
        pending.append("MB-088 Huawei grid page")
        return
    body = blob(checkout, cited[1], cited[2])
    if body is None:
        pending.append("MB-088 Huawei grid blob")
        return
    if "ma-v200.control.frequency_power_42040" not in body:
        errors.append("MB-088 cited page has no frequency-power point")
    if "ma-v200.control.frequency_power_42040=RW" not in item["spec_basis"]:
        errors.append("MB-088 dropped the frequency-power tuple")


def check_gree_pages(gree_a, by_key, errors, pending, checkout):
    pages = (
        "protocols/gree/gree-vrf-can-register-model.md",
        "protocols/gree/gree-vrf-can-dictionary.md",
    )
    if gree_a is None:
        return
    cited = [citation(gree_a, page) for page in pages]
    if gree_a["qualification"] == "qualified" and not all(cited):
        errors.append("gree-vrf-can qualified without both ND03 pages")
    if not all(cited) or pending_page(gree_a):
        pending.append("gree-vrf-can ND03 pages")
        return
    bodies = []
    for page, found in zip(pages, cited):
        body = blob(checkout, found[1], page)
        if body is None:
            pending.append("gree-vrf-can ND03 blob " + page)
            return
        bodies.append(body)
    for body in bodies:
        if "gree-vrf-can" not in body or "qualified" not in body or "specification evidence" not in body:
            errors.append("gree page does not state the qualification")
        if "every statement in the pages is an unverified candidate claim" in body:
            errors.append("gree page keeps the unverified-candidate sentence")
    if gree_a["qualification"] != "qualified" or gree_a["reason"] != "declared_by_specification":
        errors.append("gree-vrf-can is not qualified from the cited pages")
    for item in by_key.values():
        if item["qualification"] != "qualified":
            continue
        if item["family"].lower() not in {"gree-vrf-can", "gree vrf can"} and not item["key"].startswith("gree"):
            continue
        if not all(citation(item, page) for page in pages):
            errors.append(item["key"] + " qualified gree row lacks the ND03 pages")


def check_vendor_rows(by_key, errors, pending, docs_modbus, docs_canbus):
    operating = by_key.get(("b-eebus", "can.operating_state"))
    if operating:
        if operating["second_vendor"] != "in corpus (eeBUS)" or operating["promotion"] != "promote":
            errors.append("can.operating_state promotion")
        if "Huawei" in operating["vendors"] or operating["second_vendor"].startswith("confirmed:"):
            errors.append("can.operating_state treated Huawei as confirmation")
        text = operating["spec_basis"] + operating["uncertainty"]
        if not has_all(text, ("MOB-025", "Table 39", "0x311", "soft-starting", "none decoded")):
            errors.append("can.operating_state evidence")
        if "no equivalence" not in operating["uncertainty"].lower():
            errors.append("can.operating_state guessed a symbol equivalence")

    feed = by_key.get(("C", "matter.binding.feed.invoke"))
    if feed:
        if "empty production operation collection" not in feed["data_type"] or "Invoke" not in feed["data_type"]:
            errors.append("matter feed lost the historical receipt")
        if not has_all(feed["spec_basis"], ("scoped registered executor", "UNSUPPORTED_COMMAND", "unadmitted mapped route")):
            errors.append("matter feed lost the managed disposition")

    mb097 = by_key.get(("b-energy", "MB-097"))
    if mb097:
        text = mb097["uncertainty"] + mb097["spec_basis"]
        if "withholds soft_starting" in text or "withheld" in text:
            errors.append("MB-097 keeps the withhold claim")
        if not has_all(text, ("coarse active", "coarse standby", "no coarse candidate", "starting", "Standby has no direction", "unresolved")):
            errors.append("MB-097 coarse or direction evidence")
        if "CAN equivalence is confirmed" in text or "same symbols as" in text:
            errors.append("MB-097 assumed CAN equivalence")

    day = by_key.get(("b-energy", "MB-063-day"))
    if day:
        text = day["data_type"] + day["spec_basis"]
        if day["promotion"] != "promote" or not has_all(text, ("per-inverter", "current-day", "U32", "gain 100", "kWh", "MOI-042a", "Wh")):
            errors.append("MB-063-day representations")
        if any(phrase in text for phrase in ("lifetime", "monthly", "opposite direction")):
            errors.append("MB-063-day changed period or direction")

    brink = by_key.get(("A", "brink-ebus-ventilation"))
    if brink:
        text = brink["second_vendor"] + brink["uncertainty"]
        if brink["promotion"] != "driver namespace + release report":
            errors.append("brink family-grain promotion")
        if not has_all(text, ("ventilation_fan_speed_setpoint", "89 sensor", "125")):
            errors.append("brink member disposition")

    priority = by_key.get(("f-ebus-controller-1", "ebus-vaillant-controller/B524/OP02/GG00/RR00F0"))
    if priority:
        if priority["promotion"] == "promote" or "different data" not in priority["uncertainty"]:
            errors.append("Vaillant priority code was promoted")
        if "in corpus (eeBUS)" not in priority["second_vendor"] or "unconfirmed" not in priority["second_vendor"]:
            errors.append("Vaillant priority second vendor")

    protocol = by_key.get(("A", "growatt-protocol-ii"))
    if protocol:
        text = protocol["data_type"] + protocol["spec_basis"] + protocol["uncertainty"]
        if "configured eligible" not in text or "no automatic match" not in text:
            errors.append("protocol II outcomes")
        if affirmative(text, re.compile(r"FC04 is outside|FC04 outside", re.I)):
            errors.append("protocol II says FC04 is outside the profile")
        if "no_admissible_profile" in text and "automatic matching only" not in text:
            errors.append("protocol II unconditional profile reason")
        compare_when_ready(protocol, "protocols/growatt/protocol-ii-readonly-v1.md", docs_modbus, "protocol II page", errors, pending, lambda body: "FC04" in body)

    for key in ("growatt-modbus/protocol-ii-fc04-0-58", "growatt-modbus/protocol-ii-fc04-59-249"):
        item = by_key.get(("f-modbus-can", key))
        if item is None:
            errors.append("missing " + key)
            continue
        text = item["spec_basis"] + item["uncertainty"]
        if "read" not in ops_set(item["operations"]) or "typed" not in text or "word 93" not in text:
            errors.append(key + " typed reads")
        if key.endswith("59-249") and not has_all(text, ("Word 113", "Word 125", "raw word")):
            errors.append(key + " raw dispositions")
        if "creates no typed telemetry" in text:
            errors.append(key + " keeps the unconditional decoder claim")

    version = by_key.get(("f-modbus-can", "growatt-can/v105-v107-v108"))
    if version:
        text = version["data_type"] + version["spec_basis"] + version["uncertainty"]
        if version["operations"] != "read,command" or "candidate only" in text.lower():
            errors.append("V1.08 operations or candidate claim")
        if "No complete V1.05 or V1.07" not in text:
            errors.append("V1.08 claims a complete earlier layout")
        compare_when_ready(version, "protocols/growatt/low-voltage-bms-can-v108.md", docs_canbus, "V1.08 page", errors, pending, lambda body: "0x211" in body and "0x212" in body)

    v104 = by_key.get(("A", "growatt-bms-can-v104"))
    if v104:
        if "offline_replay_only" in v104["data_type"] or "command" not in ops_set(v104["operations"]):
            errors.append("V1.04 family disposition")
        if not has_all(v104["spec_basis"], ("0x301", "passive")):
            errors.append("V1.04 command and passive decoder")
        compare_when_ready(v104, "protocols/growatt/low-voltage-bms-can-v104.md", docs_canbus, "V1.04 page", errors, pending, lambda body: "0x301" in body and "receive-only" not in body.lower())

    frame = by_key.get(("f-modbus-can", "growatt-can/v104-0x301"))
    if frame and (frame["operations"] == "unknown" or "passive" not in frame["spec_basis"].lower() or "0x301" not in frame["data_type"]):
        errors.append("v104 0x301 donor description")
    reports = by_key.get(("f-modbus-can", "growatt-can/v104-0x311-0x313"))
    if reports and reports["operations"] != "read":
        errors.append("0x311-0x313 is not report-only")
    host = by_key.get(("b-eebus", "can.host_command"))
    if host:
        text = host["uncertainty"] + host["spec_basis"]
        if "command" not in ops_set(host["operations"]) or "0x301" not in text:
            errors.append("host command 0x301")
        if affirmative(text, re.compile(r"receive-only|does not transmit|command is not recorded|outbound_allowed is false", re.I)):
            errors.append("host command denial")
    pcs = by_key.get(("A", "growatt-bms-can-pcs"))
    link = by_key.get(("A", "growatt-bms-can-link"))
    if pcs and ("0x211" not in pcs["spec_basis"] or not {"read", "event", "command"} <= ops_set(pcs["operations"])):
        errors.append("PCS 0x211")
    if pcs and affirmative(pcs["spec_basis"] + pcs["uncertainty"], re.compile(r"receive-only|no transmission", re.I)):
        errors.append("PCS receive-only claim")
    if link and ("188A" not in link["spec_basis"] or not {"read", "write", "event"} <= ops_set(link["operations"])):
        errors.append("LINK command")
    if link and affirmative(link["spec_basis"] + link["uncertainty"], re.compile(r"receive-only|no transmit condition", re.I)):
        errors.append("LINK receive-only claim")
    for key in ("huawei-gateway-meter", "huawei-luna2000"):
        item = by_key.get(("A", key))
        if item is None:
            continue
        text = item["spec_basis"] + item["uncertainty"] + item["data_type"]
        if "write_authority" in text or "grants no writes" in text or "stays false" in text or "writes default denied" in text:
            errors.append(key + " blanket write denial")
    for key, phrase in {
        "MB-025": "WMaxLimPct",
        "MB-026": "Model 123",
        "MB-027": "OutPFSet",
        "MB-028": "Model 123",
        "MB-029-soc": "ChaState",
        "MB-029-other": "InBatV",
        "MB-030-nominal": "ratings",
        "MB-030-mode": "StorCtl_Mod",
    }.items():
        item = by_key.get(("b-energy", key))
        if item is None or phrase not in item["spec_basis"]:
            errors.append(key + " control evidence")
            continue
        if re.search(r"read-only(?!-)|eeBUS-only", item["uncertainty"]):
            errors.append(key + " restored a read-only claim")
        if key in {"MB-025", "MB-030-mode"} and "write" not in ops_set(item["operations"]):
            errors.append(key + " lost the documented write")
    for key in (
        "pv.operation.set_active_power_limit",
        "storage.operation.set_charge_limit",
        "storage.operation.set_discharge_limit",
    ):
        item = by_key.get(("C", key))
        if item is None:
            errors.append("missing " + key)
            continue
        text = item["spec_basis"] + item["uncertainty"] + item["sources"]
        if "MM06" not in text or "NoExecutors" in text or "no native write" in text:
            errors.append(key + " native write evidence")
    opaque = by_key.get(("b-eebus", "gree.vrf.opaque_state"))
    if opaque and (opaque["operations"] != "read" or "opaque" not in opaque["spec_basis"].lower()):
        errors.append("opaque state was decoded")
    for key in ("sunspec-storage", "sunspec/model-123", "sunspec/model-124"):
        item = by_key.get(("A", key)) or by_key.get(("f-modbus-can", key))
        if item is None:
            errors.append("missing " + key)
            continue
        if "write" not in ops_set(item["operations"]) or "controls-v1.md" not in item["spec_basis"]:
            errors.append(key + " control write")
        if re.search(r"read-only(?!-)|not requests", item["uncertainty"] + item["data_type"]):
            errors.append(key + " observed-only claim")


def compare_when_ready(item, suffix, checkout, label, errors, pending, predicate):
    if pending_page(item) or citation(item, suffix) is None:
        pending.append(label)
        return
    found = citation(item, suffix)
    body = blob(checkout, found[1], suffix)
    if body is None:
        pending.append(label + " blob")
        return
    if not predicate(body):
        errors.append(item["key"] + " disagrees with " + label)


def check_readme(text, rows):
    errors = []
    lines = text.splitlines()
    if not lines or lines[0] != "---" or not lines[1].startswith('status: "'):
        errors.append("readme front matter")
    counts = {}
    both = {}
    for row in rows:
        counts[row["promotion"]] = counts.get(row["promotion"], 0) + 1
        both[(row["package"], row["promotion"])] = both.get((row["package"], row["promotion"]), 0) + 1
    prom_rows = []
    package_rows = []
    mode = ""
    for line in lines:
        if line == "## Rows by promotion":
            mode = "prom"
            continue
        if line == "## Rows by package and promotion":
            mode = "both"
            continue
        match = re.fullmatch(r"\| ([^|]+) \| (\d+) \|", line.strip())
        if mode == "prom" and match and match.group(1) != "promotion":
            prom_rows.append((match.group(1).strip(), int(match.group(2))))
        match = re.fullmatch(r"\| ([A-F]) \| ([^|]+) \| (\d+) \|", line.strip())
        if mode == "both" and match:
            package_rows.append((match.group(1), match.group(2).strip(), int(match.group(3))))
    expected_prom = [(name, counts[name]) for name in ("promote", "driver namespace + release report", "out of 0.7 (item 30)") if counts.get(name)]
    expected_both = [
        (package, name, both[(package, name)])
        for package in "ABCDEF"
        for name in ("promote", "driver namespace + release report", "out of 0.7 (item 30)")
        if both.get((package, name))
    ]
    if prom_rows != expected_prom or package_rows != expected_both:
        errors.append("readme counts differ from denominator.tsv")
    return errors


def check_leakage(scope_dir):
    pattern = leakage_re()
    errors = []
    root = scope_dir.parents[1]
    paths = []
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
    if listed.returncode == 0:
        paths.extend(root / item.decode() for item in listed.stdout.split(b"\0") if item)
    paths.extend(path for path in scope_dir.rglob("*") if path.is_file())
    seen = set()
    for path in paths:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(text):
            errors.append("local path marker in " + path.relative_to(root).as_posix())
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("draft")
    parser.add_argument("--docs-modbus")
    parser.add_argument("--docs-canbus")
    args = parser.parse_args()
    scope_dir = Path(__file__).resolve().parent
    draft_rows, draft_errors = load_tsv(args.draft, DRAFT_COLUMNS)
    rows, row_errors = load_tsv(scope_dir / "denominator.tsv", COLUMNS)
    readme = (scope_dir / "README.md").read_text(encoding="utf-8")
    errors = draft_errors + row_errors
    pending = []
    if not draft_errors and not row_errors:
        found, pending = check_rows(rows, draft_rows, readme, scope_dir, args.docs_modbus, args.docs_canbus)
        errors.extend(found)
    for item in pending:
        print("PENDING " + item)
    if errors:
        print("\n".join(errors))
        return 1
    print("scope check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
