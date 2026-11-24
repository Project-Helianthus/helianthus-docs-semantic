"""Product identifiers, manufacturing dates, and cleared fault sets stay representable."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLEAR = (
    "empty source list converts to the symbol set no_fault; "
    "no_fault is not a source enum member; "
    "no_fault is absent from a non-empty source list"
)
DATE_TEXT = "Matter string length 8 to 16 retained as text"
FAULTS = {
    "equipment.power.wired_faults": {
        "over_voltage",
        "under_voltage",
        "no_fault",
    },
    "equipment.power.battery_faults": {
        "over_temperature",
        "under_temperature",
        "no_fault",
    },
    "equipment.power.battery_charge_faults": {
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
        assert "no_fault" in symbols

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
