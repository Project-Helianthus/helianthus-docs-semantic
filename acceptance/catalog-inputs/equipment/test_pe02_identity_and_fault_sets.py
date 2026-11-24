"""Product identifiers, version forms, manufacturing dates, and fault sets stay representable."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLEAR = (
    "source enum Unspecified converts to unspecified; "
    "unspecified is a source enum member; "
    "empty source list converts to the symbol set no_fault; "
    "no_fault is not a source enum member; "
    "no_fault is absent from a non-empty source list"
)
DATE_TEXT = "Matter string length 8 to 16 retained as text"
VERSIONS = {
    "equipment.identification.software_revision": {
        "value_kind": "text",
        "matter": {
            "BasicInformation.SoftwareVersionString",
            "BridgedDeviceBasicInformation.SoftwareVersionString",
        },
        "review": "display string distinct from equipment.identification.software_version",
        "crosswalk": {
            "BasicInformation.SoftwareVersionString",
            "BridgedDeviceBasicInformation.SoftwareVersionString",
        },
    },
    "equipment.identification.software_version": {
        "value_kind": "quantity",
        "unit": "unit.one",
        "minimum": "0",
        "maximum": "4294967295",
        "direction": "not_applicable",
        "encoding": "encoding range: uint32",
        "matter": {
            "BasicInformation.SoftwareVersion",
            "BridgedDeviceBasicInformation.SoftwareVersion",
        },
        "review": "numeric identifier distinct from equipment.identification.software_revision",
        "crosswalk": {
            "BasicInformation.SoftwareVersion",
            "BridgedDeviceBasicInformation.SoftwareVersion",
        },
    },
    "equipment.identification.hardware_revision": {
        "value_kind": "text",
        "matter": {
            "BasicInformation.HardwareVersionString",
            "BridgedDeviceBasicInformation.HardwareVersionString",
        },
        "review": "display string distinct from equipment.identification.hardware_version",
        "crosswalk": {
            "BasicInformation.HardwareVersionString",
            "BridgedDeviceBasicInformation.HardwareVersionString",
        },
    },
    "equipment.identification.hardware_version": {
        "value_kind": "quantity",
        "unit": "unit.one",
        "minimum": "0",
        "maximum": "65535",
        "direction": "not_applicable",
        "encoding": "encoding range: uint16",
        "matter": {
            "BasicInformation.HardwareVersion",
            "BridgedDeviceBasicInformation.HardwareVersion",
        },
        "review": "numeric identifier distinct from equipment.identification.hardware_revision",
        "crosswalk": {
            "BasicInformation.HardwareVersion",
            "BridgedDeviceBasicInformation.HardwareVersion",
        },
    },
}
FAULTS = {
    "equipment.power.wired_faults": {
        "unspecified",
        "over_voltage",
        "under_voltage",
        "no_fault",
    },
    "equipment.power.battery_faults": {
        "unspecified",
        "over_temperature",
        "under_temperature",
        "no_fault",
    },
    "equipment.power.battery_charge_faults": {
        "unspecified",
        "ambient_too_hot",
        "ambient_too_cold",
        "battery_too_hot",
        "battery_too_cold",
        "battery_absent",
        "battery_over_voltage",
        "battery_under_voltage",
        "charger_over_voltage",
        "charger_under_voltage",
        "safety_timeout",
        "no_fault",
    },
}
FAULT_EVENTS = {
    "equipment.event.wired_fault_change": "equipment.power.wired_faults",
    "equipment.event.battery_fault_change": "equipment.power.battery_faults",
    "equipment.event.battery_charge_fault_change": "equipment.power.battery_charge_faults",
}
FAULT_ATTRIBUTES = {
    "PowerSource.ActiveWiredFaults": "equipment.power.wired_faults",
    "PowerSource.ActiveBatFaults": "equipment.power.battery_faults",
    "PowerSource.ActiveBatChargeFaults": "equipment.power.battery_charge_faults",
}


def _rows(name):
    with (ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _by_id(name, key):
    return {row[key]: row for row in _rows(name)}


def _symbols(cell):
    return {token.strip() for token in (cell or "").split(",") if token.strip()}


def test_product_id_and_part_number_are_separate_facts():
    fields = _by_id("pe02-fields.tsv", "id")
    product = fields["equipment.identification.product_code"]
    part = fields["equipment.identification.part_number"]
    assert product["subject_dimension"] == "equipment.dimension.unit"
    assert part["subject_dimension"] == product["subject_dimension"]
    assert not (product.get("qualifiers") or "").strip()
    assert not (part.get("qualifiers") or "").strip()
    assert "PartNumber" not in product["matter_1_6_1"]
    assert "ProductId" not in part["matter_1_6_1"]
    assert "BasicInformation.PartNumber" in part["matter_1_6_1"]
    assert "BridgedDeviceBasicInformation.PartNumber" in part["matter_1_6_1"]
    assert part["value_kind"] == "text"
    assert part["review"] == "distinct from equipment.identification.product_code"

    carried = {}
    for row in _rows("union-crosswalk.tsv"):
        if row["element"] in {
            "BasicInformation.ProductId",
            "BridgedDeviceBasicInformation.ProductId",
            "BasicInformation.PartNumber",
            "BridgedDeviceBasicInformation.PartNumber",
        }:
            carried[row["element"]] = row
    assert carried["BasicInformation.ProductId"]["element_id"] == product["id"]
    assert carried["BridgedDeviceBasicInformation.ProductId"]["element_id"] == product["id"]
    assert carried["BasicInformation.PartNumber"]["element_id"] == part["id"]
    assert carried["BridgedDeviceBasicInformation.PartNumber"]["element_id"] == part["id"]
    for row in carried.values():
        assert row["status"] == "carried"
    assert len({row["element_id"] for row in carried.values()}) == 2

    for service in ("equipment.capability.read.unit", "equipment.portal.read.unit"):
        listed = _by_id("pe02-services.tsv", "id")[service]["attributes"]
        assert "equipment.identification.part_number" in listed.split(", ")


def _matter_tokens(cell):
    return {token.strip() for token in (cell or "").split(",") if token.strip()}


def test_numeric_version_identifiers_are_separate_from_display_strings():
    fields = _by_id("pe02-fields.tsv", "id")
    crosswalk = {
        row["element"]: row
        for row in _rows("union-crosswalk.tsv")
        if row["element"] in {element for spec in VERSIONS.values() for element in spec["crosswalk"]}
    }
    assert set(crosswalk) == {element for spec in VERSIONS.values() for element in spec["crosswalk"]}
    for fact_id, spec in VERSIONS.items():
        field = fields[fact_id]
        assert field["value_kind"] == spec["value_kind"]
        assert field["subject_dimension"] == "equipment.dimension.unit"
        assert not (field.get("qualifiers") or "").strip()
        assert _matter_tokens(field["matter_1_6_1"]) == spec["matter"]
        assert field["review"] == spec["review"]
        assert field["admission"] == "matter_baseline"
        if spec["value_kind"] == "quantity":
            assert field["unit"] == spec["unit"]
            assert field["minimum"] == spec["minimum"]
            assert field["maximum"] == spec["maximum"]
            assert field["direction"] == spec["direction"]
            assert field["source"].startswith(spec["encoding"])
            assert not (field.get("eebus") or "").strip()
        else:
            assert not (field.get("unit") or "").strip()
            assert "VersionString" in field["matter_1_6_1"]
            assert field["eebus"]
        for element in spec["crosswalk"]:
            row = crosswalk[element]
            assert row["element_id"] == fact_id
            assert row["status"] == "carried"
            assert row["review"] == spec["review"]
            assert not (row.get("reason") or "").strip()
    assert (
        fields["equipment.identification.software_version"]["id"]
        != fields["equipment.identification.software_revision"]["id"]
    )
    assert (
        fields["equipment.identification.hardware_version"]["id"]
        != fields["equipment.identification.hardware_revision"]["id"]
    )
    for service in ("equipment.capability.read.unit", "equipment.portal.read.unit"):
        listed = set(_by_id("pe02-services.tsv", "id")[service]["attributes"].split(", "))
        assert "equipment.identification.software_version" in listed
        assert "equipment.identification.hardware_version" in listed
        assert "equipment.identification.software_revision" in listed
        assert "equipment.identification.hardware_revision" in listed


def test_manufacturing_date_is_retained_as_text():
    field = _by_id("pe02-fields.tsv", "id")["equipment.identification.manufacturing_date"]
    assert field["value_kind"] == "text"
    assert field["review"] == DATE_TEXT
    seen = []
    for row in _rows("union-crosswalk.tsv"):
        if row["element"].endswith(".ManufacturingDate") and ".ev." not in row["element"]:
            seen.append(row)
    assert {row["element"] for row in seen} == {
        "BasicInformation.ManufacturingDate",
        "BridgedDeviceBasicInformation.ManufacturingDate",
    }
    for row in seen:
        assert row["element_id"] == field["id"]
        assert row["status"] == "carried"
        assert row["review"] == DATE_TEXT


def test_fault_sets_encode_an_empty_clear_state():
    fields = _by_id("pe02-fields.tsv", "id")
    for fact_id, symbols in FAULTS.items():
        field = fields[fact_id]
        assert field["value_kind"] == "symbols"
        assert _symbols(field["symbols"]) == symbols
        assert field["review"] == CLEAR
        assert "unspecified" in symbols
        assert "no_fault" in symbols
        assert "source enum Unspecified converts to unspecified" in field["review"]
        assert "no_fault is absent from a non-empty source list" in field["review"]

    events = _by_id("pe02-events.tsv", "event")
    for event_id, fact_id in FAULT_EVENTS.items():
        event = events[event_id]
        assert event["origin"] == "emitted"
        assert fact_id in event["payload"].split(", ")
        assert event["review"] == CLEAR

    attributes = {
        row["element"]: row
        for row in _rows("union-crosswalk.tsv")
        if row["element"] in FAULT_ATTRIBUTES
    }
    assert set(attributes) == set(FAULT_ATTRIBUTES)
    for element, fact_id in FAULT_ATTRIBUTES.items():
        row = attributes[element]
        assert row["element_id"] == fact_id
        assert row["status"] == "carried"
        assert row["review"] == CLEAR
