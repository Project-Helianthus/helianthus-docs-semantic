"""Pins the QQ12 review fixes for subject, quantity, limit-curve input, and unconfirmed vendors."""

import csv
from pathlib import Path

ENERGY = Path(__file__).resolve().parent

AGGREGATES = {
    "pv.dc.aggregate_current": "pv.string.current",
    "pv.dc.aggregate_power": "pv.string.power",
    "pv.dc.aggregate_voltage": "pv.string.voltage",
}
STRING_MPS = {
    "pv.string.power": "MPS-011",
    "pv.string.current": "MPS-021",
    "pv.string.voltage": "MPS-031",
}
QUANTITIES = {
    "pv.moi.ac_yield_total": "unit.joule",
    "pv.moi.ac_yield_day": "unit.joule",
    "pv.moi.ac_yield_day_historical": "unit.joule",
    "pv.moi.ac_yield_month": "unit.joule",
    "pv.moi.ac_yield_month_historical": "unit.joule",
    "pv.moi.ac_yield_year": "unit.joule",
    "pv.moi.ac_yield_year_historical": "unit.joule",
    "pv.vapd.ac_yield_total": "unit.joule",
    "pv.vapd.ac_power_total": "unit.watt",
    "infrastructure.mpc.ac_power": "unit.watt",
}
UNCONFIRMED_RESEARCH = {
    "pe08-two-vendor-research.tsv": {
        "insulation and internal resistance of a battery",
        "per-cell voltage, balancing state, average and spread of cell voltages",
        "battery charge and discharge current and voltage limits",
        "permission to charge the battery from the grid",
        "minimum reserve state of charge of a battery system",
    },
    "pe03-two-vendor-research.tsv": {
        "state and temperature of a DC input (MPPT)",
        "configured maximum active, apparent and reactive power of an inverter",
        "detailed inverter operating states",
        "irradiance and module temperature of a PV array",
    },
    "pe10-two-vendor-research.tsv": {
        "reactive energy per quadrant",
    },
}


def _rows(name):
    with (ENERGY / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_string_mps_evidence_stays_off_inverter_aggregates():
    main = {row["element"]: row for row in _rows("pe03-elements-on-main.tsv")}
    fields = {row["id"]: row for row in _rows("pe03-fields.tsv")}
    for element, string_id in AGGREGATES.items():
        row = main[element]
        assert row["eebus"] == ""
        assert "eebus.unmapped.v1" in row["source"]
        assert "MPS-0" not in row["eebus"] + row["source"]
        assert string_id in row["review"]
    for element, clause in STRING_MPS.items():
        assert clause in fields[element]["eebus"]
        assert fields[element]["subject_dimension"] == "pv.dimension.string"
    coverage = [
        row
        for row in _rows("qq12-coverage.tsv")
        if row["use_case"] == "mps" and row["element"] in {"MPS-011", "MPS-021", "MPS-031"}
    ]
    assert {row["element_id"] for row in coverage} == set(STRING_MPS)


def test_inverter_yields_and_named_powers_keep_quantity_units():
    fields = {row["id"]: row for row in _rows("qq12-fields.tsv")}
    for element, unit in QUANTITIES.items():
        row = fields[element]
        assert row["value_kind"] == "quantity"
        assert row["unit"] == unit
        assert row["value_kind"] != "text"
        assert "unknown" in row["source"] or "absent scale 0" in row["source"]
        assert row["review"] == "bound not in specification"


def test_limit_curve_write_accepts_maximum_power():
    rows = _rows("pe07-operations.tsv")
    row = next(row for row in rows if row["operation"] == "energy.operation.modify_series_slot")
    signature = row["argument"] + " " + row["parameters"]
    assert "energy.series.slot_power_maximum" in signature
    assert "energy.series.slot_power_nominal" in signature
    assert "energy.series.slot_power_maximum" in row["effect_rule"]
    assert "limit-curve" in row["effect_rule"]
    assert "forecast" in row["effect_rule"]


def test_session_start_does_not_use_session_duration():
    fields = {row["id"]: row for row in _rows("pe06-fields.tsv")}
    start = fields["evse.session.start"]
    duration = fields["evse.session.duration"]
    assert start["value_kind"] == "time"
    assert start["matter_1_6_1"] == ""
    assert "SessionDuration" not in start["matter_1_6_1"]
    assert "SessionDuration" not in start["source"]
    assert "matter.unmapped.v1" in start["source"]
    assert start["eebus"] == "EVCS-sc1"
    assert start["admission"] == "eebus"
    assert "evse.session.duration" in start["review"]
    assert duration["matter_1_6_1"] == "EnergyEvse.SessionDuration"
    assert duration["unit"] == "unit.second"
    assert "EnergyEvse.SessionDuration" in duration["source"]


def test_charge_direction_leaves_bat_charge_state_unmapped():
    row = next(item for item in _rows("pe08-fields.tsv") if item["id"] == "storage.status.charge_direction")
    assert row["matter_1_6_1"] == ""
    assert "BatChargeState" not in row["matter_1_6_1"]
    assert "matter.unmapped.v1" in row["source"]
    assert "eebus.unmapped.v1" in row["source"]
    assert row["symbols"] == "charging, discharging, idle, starting"
    assert "IsNotCharging" in row["review"]
    assert "IsAtFullCharge" in row["review"]
    assert "Unknown" in row["review"]
    assert "matter.unmapped.v1" not in row["review"]


def test_metered_quantity_joule_is_active_energy_only():
    fields = {row["id"]: row for row in _rows("pe12-fields.tsv")}
    quantity = fields["energy.metering.quantity"]
    basis = fields["energy.tariff.unit_basis"]
    assert quantity["unit"] == "unit.joule"
    assert quantity["matter_1_6_1"] == "CommodityMetering.MeteredQuantity"
    assert "TariffUnit KWh" in quantity["source"]
    assert "KVAh unmapped" in quantity["source"]
    assert "restricted to" in quantity["source"]
    assert quantity["review"] == "bound not in specification"
    assert "apparent_energy" in basis["symbols"]
    assert "energy" in basis["symbols"].split(", ")
    assert "CommodityMetering.TariffUnit" in basis["matter_1_6_1"]


def test_unconfirmed_vendor_research_stays_unconfirmed():
    for name, concepts in UNCONFIRMED_RESEARCH.items():
        rows = {row["concept"]: row for row in _rows(name)}
        for concept in concepts:
            row = rows[concept]
            assert row["verification_level"] == "second vendor unconfirmed"
            assert row["review"] == "second vendor unconfirmed"
            assert row["correspondence"].startswith("unconfirmed correspondence")
            assert not row["correspondence"].startswith("same role")
    temperatures = next(
        row
        for row in _rows("pe03-two-vendor-research.tsv")
        if row["concept"] == "inverter temperatures by sensor position"
    )
    assert temperatures["verification_level"] == "specification"
