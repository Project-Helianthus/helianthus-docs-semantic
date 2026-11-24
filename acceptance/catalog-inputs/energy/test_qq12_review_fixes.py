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


def test_joule_prices_are_active_energy_only():
    fields = {row["id"]: row for row in _rows("pe12-fields.tsv")}
    basis = fields["energy.tariff.unit_basis"]
    assert "apparent_energy" in basis["symbols"]
    assert "energy" in basis["symbols"].split(", ")
    prices = {
        "energy.price.current": "CommodityPrice.TariffUnit",
        "energy.price.forecast_price": "CommodityPrice.TariffUnit",
        "energy.tariff.component_price": "CommodityTariff.TariffUnit",
    }
    for element, tariff_unit in prices.items():
        row = fields[element]
        assert row["unit"] == "unit.currency_per_joule"
        assert "restricted to" in row["source"]
        assert f"{tariff_unit} KWh" in row["source"]
        assert "KVAh unmapped" in row["source"]
        assert "KVAh" not in row["matter_1_6_1"]
        assert row["review"] == "bound not in specification"
    incentive = fields["energy.incentive.incentive_value"]
    assert incentive["unit"] == "unit.currency_per_joule"
    assert incentive["matter_1_6_1"] == ""
    assert "TariffUnit" not in incentive["source"]


def test_battery_fault_sets_keep_unspecified():
    fields = {row["id"]: row for row in _rows("pe08-fields.tsv")}
    events = {row["event"]: row for row in _rows("pe08-events.tsv")}
    faults = fields["storage.status.faults"]
    charge = fields["storage.status.charge_faults"]
    assert faults["symbols"].split(", ")[0] == "unspecified"
    assert "over_temperature" in faults["symbols"].split(", ")
    assert "under_temperature" in faults["symbols"].split(", ")
    assert "BatFaultEnum Unspecified" in faults["source"]
    assert "empty list" in faults["review"]
    assert faults["matter_1_6_1"] == "PowerSource.ActiveBatFaults"
    assert charge["symbols"].split(", ")[0] == "unspecified"
    assert "safety_timeout" in charge["symbols"].split(", ")
    assert "ambient_too_hot" in charge["symbols"].split(", ")
    assert "BatChargeFaultEnum Unspecified" in charge["source"]
    assert "empty list" in charge["review"]
    assert charge["matter_1_6_1"] == "PowerSource.ActiveBatChargeFaults"
    fault_event = events["storage.event.fault_change"]
    charge_event = events["storage.event.charge_fault_change"]
    assert fault_event["trigger_fact"] == "storage.status.faults"
    assert fault_event["condition"] == "changed"
    assert "BatFaultEnum Unspecified" in fault_event["source"]
    assert "Unspecified" in fault_event["review"]
    assert charge_event["trigger_fact"] == "storage.status.charge_faults"
    assert charge_event["condition"] == "changed"
    assert "BatChargeFaultEnum Unspecified" in charge_event["source"]
    assert "Unspecified" in charge_event["review"]


def test_inverter_fault_and_derating_leave_power_source_status_unmapped():
    rows = {row["element"]: row for row in _rows("pe03-elements-on-main.tsv")}
    for element, reason in (
        ("pv.status.derating", "derating"),
        ("pv.status.fault", "fault"),
    ):
        row = rows[element]
        assert row["matter_1_6_1"] == ""
        assert "PowerSource.Status" not in row["source"]
        assert "matter.unmapped.v1" in row["source"]
        assert "MOI-021" in row["eebus"] and "MOI-026" in row["eebus"]
        assert "MOI-021" in row["source"] and "MOI-026" in row["source"]
        assert reason in row["review"]
        assert "matter association removed" in row["review"]
    operating = rows["pv.status.operating"]
    assert operating["matter_1_6_1"] == "PowerSource.Status"
    assert "Matter 1.6.1 PowerSource.Status" in operating["source"]
    assert "MOI-021" in operating["eebus"] and "MOI-026" in operating["eebus"]


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


def test_mode_rows_keep_uint8_identity_and_tag_metadata():
    evse = {row["id"]: row for row in _rows("pe06-fields.tsv")}
    esa = {row["id"]: row for row in _rows("pe07-fields.tsv")}
    closed = {
        "evse.mode": {"manual", "time_of_use", "solar_charging", "v2x"},
        "energy.esa.mode": {
            "no_optimization",
            "device_optimization",
            "local_optimization",
            "grid_optimization",
        },
    }
    for row in (evse["evse.mode"], esa["energy.esa.mode"]):
        assert row["value_kind"] == "quantity"
        assert row["unit"] == "unit.one"
        assert row["direction"] == "not_applicable"
        assert row["symbols"] == ""
        assert row["minimum"] == "" and row["maximum"] == ""
        assert "uint8" in row["source"]
        assert "ModeTag" in row["source"]
        assert row["matter_1_6_1"].endswith("CurrentMode")
        assert "bound not in specification" in row["review"]
        assert closed[row["id"]].isdisjoint(set(filter(None, row["symbols"].split(", "))))
    for row, shared in (
        (evse["evse.mode_supported"], "Manual"),
        (esa["energy.esa.mode_supported"], "NoOptimization"),
    ):
        assert row["value_kind"] == "text"
        assert row["symbols"] == ""
        assert "SupportedModes.Mode" in row["source"]
        assert "uint8" in row["source"]
        assert "ModeTag" in row["source"]
        assert "Auto" in row["source"]
        assert shared in row["source"]
        assert "manufacturer" in row["source"]
        assert "not the identifier" in row["source"]
        assert "not the mode value" in row["review"]
    for name, operation, argument in (
        ("pe06-operations.tsv", "evse.operation.set_evse_mode", "evse.mode"),
        ("pe07-operations.tsv", "energy.operation.set_esa_mode", "energy.esa.mode"),
    ):
        row = next(item for item in _rows(name) if item["operation"] == operation)
        assert row["argument"] == argument
        assert row["matter_1_6_1"].endswith("ChangeToMode.NewMode")
        assert "uint8" in row["effect_rule"]
        assert "ModeTag" in row["effect_rule"]
        assert "NewMode" in row["note"]
        assert "uint8" in row["source"]
        assert "ModeTag" in row["note"]


def test_price_description_uses_the_struct_payload():
    row = {item["id"]: item for item in _rows("pe12-fields.tsv")}["energy.price.current_description"]
    assert row["value_kind"] == "text"
    assert "GetDetailedPriceRequest" not in row["matter_1_6_1"]
    assert "GetDetailedPriceRequest" not in row["source"]
    assert "CommodityPrice.CurrentPrice" in row["matter_1_6_1"]
    assert "GetDetailedPriceResponse.CurrentPrice" in row["matter_1_6_1"]
    assert "CommodityPriceStruct.Description" in row["source"]
    assert "CommodityPrice.CurrentPrice" in row["source"]
    assert "GetDetailedPriceResponse.CurrentPrice" in row["source"]
    assert "GetDetailedPriceRequest" not in row["review"]
    assert "CommodityPriceStruct.Description" in row["review"]


def test_tariff_randomization_offsets_stay_signed_and_unbounded():
    fields = {row["id"]: row for row in _rows("pe12-fields.tsv")}
    default = fields["energy.tariff.randomization_offset"]
    entry = fields["energy.tariff.day_entry_randomization_offset"]
    for row in (default, entry):
        assert row["value_kind"] == "quantity"
        assert row["unit"] == "unit.second"
        assert row["direction"] == "signed"
        assert row["direction"] != "non_negative"
        assert row["minimum"] == "" and row["maximum"] == ""
        assert row["review"] == "bound not in specification"
        assert "int16" in row["source"]
        assert "no nonnegative constraint" in row["source"]
        assert "bound not in specification" in row["source"]
    assert "DefaultRandomizationOffset" in default["matter_1_6_1"]
    assert "DefaultRandomizationOffset" in default["source"]
    assert "DayEntryStruct.RandomizationOffset" in entry["source"]
    assert "CommodityTariff.DayEntries" in entry["matter_1_6_1"]


DIAGNOSTIC_STATUS = (
    "storage.status.alarm",
    "storage.status.operating",
    "storage.status.protection",
    "storage.status.warning",
)
ENERGY_FIELDS = {
    "pe10-fields.tsv": {
        "infrastructure.energy.reactive_import": (
            "CumulativeEnergyImported",
            "ReactiveEnergy",
            "feat.REAE",
            "energy-mVARh",
            "unit.volt_ampere_reactive_second",
        ),
        "infrastructure.energy.reactive_export": (
            "CumulativeEnergyExported",
            "ReactiveEnergy",
            "feat.REAE",
            "energy-mVARh",
            "unit.volt_ampere_reactive_second",
        ),
        "infrastructure.energy.apparent_import": (
            "CumulativeEnergyImported",
            "ApparentEnergy",
            "feat.APPE",
            "energy-mVAh",
            "unit.volt_ampere_second",
        ),
        "infrastructure.energy.apparent_export": (
            "CumulativeEnergyExported",
            "ApparentEnergy",
            "feat.APPE",
            "energy-mVAh",
            "unit.volt_ampere_second",
        ),
    },
    "pe03-fields.tsv": {
        "pv.energy.reactive_imported": (
            "CumulativeEnergyImported",
            "ReactiveEnergy",
            "feat.REAE",
            "energy-mVARh",
            "unit.volt_ampere_reactive_second",
        ),
        "pv.energy.reactive_exported": (
            "CumulativeEnergyExported",
            "ReactiveEnergy",
            "feat.REAE",
            "energy-mVARh",
            "unit.volt_ampere_reactive_second",
        ),
        "pv.energy.apparent_imported": (
            "CumulativeEnergyImported",
            "ApparentEnergy",
            "feat.APPE",
            "energy-mVAh",
            "unit.volt_ampere_second",
        ),
        "pv.energy.apparent_exported": (
            "CumulativeEnergyExported",
            "ApparentEnergy",
            "feat.APPE",
            "energy-mVAh",
            "unit.volt_ampere_second",
        ),
    },
}


def test_battery_diagnostics_leave_bat_charge_state_unmapped():
    rows = {row["element"]: row for row in _rows("pe08-elements-on-main.tsv")}
    for element in DIAGNOSTIC_STATUS:
        row = rows[element]
        assert row["matter_1_6_1"] == ""
        assert "BatChargeState" not in row["matter_1_6_1"]
        assert "BatChargeState" not in row["source"]
        assert "matter.unmapped.v1" in row["source"]
        assert row["eebus"] == "MOB-025"
        assert "MOB-025" in row["source"]
        assert "Monitoring of Battery V1.0.0 [MOB-025]" in row["source"]
        assert row["verification_level"] == "specification"
        assert "IsCharging" in row["review"]
        assert "IsAtFullCharge" in row["review"]
        assert "IsNotCharging" in row["review"]
        assert "Unknown" in row["review"]
        assert "matter.unmapped.v1" not in row["review"]


def test_reactive_and_apparent_energy_cite_value_fields():
    for name, expected in ENERGY_FIELDS.items():
        rows = {row["id"]: row for row in _rows(name)}
        seen = set()
        for element, (attribute, field, feature, native, unit) in expected.items():
            row = rows[element]
            matter = f"ElectricalEnergyMeasurement.{attribute}.{field}"
            assert row["matter_1_6_1"] == matter
            assert "feat.REAE" not in row["matter_1_6_1"]
            assert "feat.APPE" not in row["matter_1_6_1"]
            assert row["unit"] == unit
            assert row["eebus"] == ""
            assert "eebus.unmapped.v1" in row["source"]
            assert matter in row["source"]
            assert f"availability {feature}" in row["source"]
            assert native in row["source"]
            assert unit in row["source"]
            assert "3.6" in row["source"]
            assert row["minimum"] == "" and row["maximum"] == ""
            assert row["review"] == "bound not in specification"
            seen.add(row["matter_1_6_1"])
        assert len(seen) == 4


def test_ratio_write_stays_unqualified_without_a_writable_clause():
    row = next(
        item
        for item in _rows("pe03-operations.tsv")
        if item["operation"] == "pv.operation.set_active_power_limit_ratio"
    )
    assert row["argument"] == "pv.limit.active_power_ratio"
    assert row["eebus"] == ""
    assert row["admission"] == ""
    assert row["matter_1_6_1"] == ""
    assert row["verification_level"] == "source not found"
    assert row["verification_level"] != "specification"
    assert "eebus.unmapped.v1" in row["source"]
    assert "matter.unmapped.v1" in row["source"]
    assert "MGCP-011" not in row["eebus"]
    assert "LPP-011" not in row["eebus"]
    assert row["review"].startswith("source not found:")
    assert "writable ratio" in row["review"]
    assert "read,event" in row["review"]
    assert "set_production_limit" in row["review"]
    limit = next(
        item
        for item in _rows("pe03-elements-on-main.tsv")
        if item["element"] == "pv.limit.active_power_ratio"
    )
    assert "MGCP-011" in limit["eebus"]
    watt = next(
        item
        for item in _rows("pe07-operations.tsv")
        if item["operation"] == "energy.operation.set_production_limit"
    )
    assert watt["eebus"] == "LPP-011"
    assert watt["verification_level"] == "specification"


MEASUREMENT_TYPE_SYMBOLS = (
    "unspecified",
    "voltage",
    "active_current",
    "reactive_current",
    "apparent_current",
    "active_power",
    "reactive_power",
    "apparent_power",
    "rms_voltage",
    "rms_current",
    "rms_power",
    "frequency",
    "power_factor",
    "neutral_current",
    "electrical_energy",
    "reactive_energy",
    "apparent_energy",
)
MEASUREMENT_TYPE_MEMBERS = (
    "Unspecified",
    "Voltage",
    "ActiveCurrent",
    "ReactiveCurrent",
    "ApparentCurrent",
    "ActivePower",
    "ReactivePower",
    "ApparentPower",
    "RmsVoltage",
    "RmsCurrent",
    "RmsPower",
    "Frequency",
    "PowerFactor",
    "NeutralCurrent",
    "ElectricalEnergy",
    "ReactiveEnergy",
    "ApparentEnergy",
)
PERCENT_MAX = (
    "ElectricalPowerMeasurement.Accuracy.AccuracyRanges.PercentMax, "
    "ElectricalEnergyMeasurement.Accuracy.AccuracyRanges.PercentMax"
)


def _symbols(attributes):
    marker = "symbols "
    text = attributes.split(marker, 1)[1]
    return tuple(part.strip() for part in text.split(","))


def test_active_power_limit_withholds_power_adjust_request():
    rows = {row["element"]: row for row in _rows("pe03-elements-on-main.tsv")}
    operation = rows["pv.operation.set_active_power_limit"]
    limit = rows["pv.limit.active_power"]
    for row in (operation, limit):
        assert row["matter_1_6_1"] == ""
        assert "PowerAdjustRequest" not in row["matter_1_6_1"]
        assert "PowerAdjustRequest" not in row["source"]
        assert "matter.unmapped.v1" in row["source"]
        assert row["eebus"] == "LPP-011"
        assert "LPP-011" in row["source"]
        assert "Limitation of Power Production V1.0.0 [LPP-011]" in row["source"]
        assert row["verification_level"] == "specification"
        assert "PowerAdjustRequest" in row["review"]
        assert "Duration" in row["review"]
        assert "Cause" in row["review"]
        assert "energy.operation.adjust_power" in row["review"]
        assert "matter association removed" in row["review"]
    assert "pv.limit.active_power" in operation["review"]
    assert "temporary adjustment" in operation["review"]
    adjust = next(
        item
        for item in _rows("pe07-operations.tsv")
        if item["operation"] == "energy.operation.adjust_power"
    )
    signature = adjust["argument"] + " " + adjust["parameters"]
    assert adjust["argument"] == "energy.esa.requested_power"
    assert "energy.esa.requested_duration" in signature
    assert "energy.esa.request_cause" in signature
    assert "PowerAdjustRequest" in adjust["matter_1_6_1"]


def test_measurement_type_qualifiers_keep_distinct_enum_members():
    expected = {
        "pe03-qualifier-dimensions.tsv": "pv.dimension.measurement_type",
        "pe10-qualifier-dimensions.tsv": "infrastructure.dimension.measurement_type",
    }
    for name, element in expected.items():
        row = next(item for item in _rows(name) if item["id"] == element)
        assert _symbols(row["attributes"]) == MEASUREMENT_TYPE_SYMBOLS
        assert len(set(MEASUREMENT_TYPE_SYMBOLS)) == len(MEASUREMENT_TYPE_SYMBOLS)
        for member in MEASUREMENT_TYPE_MEMBERS:
            assert member in row["source"]
        assert "MeasurementTypeEnum" in row["matter_eebus"]
        assert "ElectricalPowerMeasurement.MeasurementTypeEnum" in row["matter_eebus"]
        assert "ElectricalEnergyMeasurement.MeasurementTypeEnum" in row["matter_eebus"]
        assert "RmsVoltage" in row["note"]
        assert "NeutralCurrent" in row["note"]
        assert "Unspecified" in row["note"]
        assert row["verification_level"] == "specification"


def test_accuracy_ratio_is_a_restricted_percent_max_projection():
    rows = {
        "pe03-fields.tsv": "pv.accuracy.ratio_maximum",
        "pe10-fields.tsv": "infrastructure.accuracy.ratio_maximum",
    }
    for name, element in rows.items():
        row = next(item for item in _rows(name) if item["id"] == element)
        assert row["matter_1_6_1"] == PERCENT_MAX
        assert row["matter_1_6_1"] != (
            "ElectricalPowerMeasurement.Accuracy, ElectricalEnergyMeasurement.Accuracy"
        )
        assert "PercentMax" in row["source"]
        assert "one AccuracyRanges entry" in row["source"]
        assert "multiple ranges are unsupported" in row["source"]
        assert "FixedMax" in row["source"]
        assert "the Accuracy structure is not this scalar" in row["source"]
        assert "no range qualifier" in row["source"]
        assert "percent100ths / 10000" in row["source"]
        assert "eebus.unmapped.v1" in row["source"]
        assert row["eebus"] == ""
        assert row["minimum"] == "" and row["maximum"] == ""
        assert row["review"] == "bound not in specification"
        assert row["unit"] == "unit.ratio"
        assert "measurement_type" in row["qualifiers"]


def test_calendar_yields_withhold_periodic_energy_until_period_matches():
    rows = {row["element"]: row for row in _rows("pe03-elements-on-main.tsv")}
    boundaries = {
        "pv.energy.yield_day": "day",
        "pv.energy.yield_month": "month",
        "pv.energy.yield_year": "year",
    }
    for element, boundary in boundaries.items():
        row = rows[element]
        assert row["matter_1_6_1"] == ""
        assert row["eebus"] == ""
        assert "PeriodicEnergyExported" not in row["matter_1_6_1"]
        assert "PeriodicEnergyExported" not in row["source"]
        assert "matter.unmapped.v1" in row["source"]
        assert "eebus.unmapped.v1" in row["source"]
        assert "PeriodicEnergyExported" in row["review"]
        assert "StartTimestamp" in row["review"]
        assert "EndTimestamp" in row["review"]
        assert "StartSystime" in row["review"]
        assert "EndSystime" in row["review"]
        assert boundary in row["review"]
        assert "matter association removed" in row["review"]
        assert "MOI-042a" in row["review"]
        assert "pv.dimension.inverter" in row["review"]
        assert row["verification_level"] == "specification"


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


def test_allocated_current_withholds_enable_charging():
    rows = {row["element"]: row for row in _rows("pe06-elements-on-main.tsv")}
    row = rows["evse.operation.set_allocated_current"]
    assert row["matter_1_6_1"] == ""
    assert "EnableCharging" not in row["matter_1_6_1"]
    assert "EnableCharging" not in row["source"]
    assert "matter.unmapped.v1" in row["source"]
    assert row["eebus"] == "OPEV-sc1"
    assert "OPEV-sc1" in row["source"]
    assert row["verification_level"] == "specification"
    for name in ("ChargingEnabledUntil", "MinimumChargeCurrent", "MaximumChargeCurrent"):
        assert name in row["review"]
    assert "evse.limit.allocated_current" in row["review"]
    assert "matter association removed" in row["review"]
    assert "evse.operation.set_supply" in row["review"]
    supply = next(
        item
        for item in _rows("pe06-operations.tsv")
        if item["operation"] == "evse.operation.set_supply"
    )
    assert "EnableCharging" in supply["matter_1_6_1"]
    signature = supply["argument"] + " " + supply["parameters"]
    assert "evse.limit.charging_enabled_until" in signature
    assert "evse.limit.minimum_charge_current" in signature


def test_allocated_current_expiry_withholds_enable_charging():
    row = next(
        item
        for item in _rows("pe06-operations.tsv")
        if item["operation"] == "evse.operation.set_allocated_current_with_expiry"
    )
    assert row["matter_1_6_1"] == ""
    assert "EnableCharging" not in row["matter_1_6_1"]
    assert "EnableCharging" not in row["source"]
    assert "matter.unmapped.v1" in row["source"]
    assert row["eebus"] == "OPEV-sc1"
    assert "OPEV-sc1" in row["source"]
    assert "Overload Protection by EV Charging Current Curtailment V1.0.1b [OPEV-sc1]" in row["source"]
    assert row["admission"] == "eebus"
    assert row["argument"] == "evse.limit.allocated_current"
    assert row["parameters"] == "evse.limit.allocated_current_expiry"
    assert "evse.limit.minimum_charge_current" not in row["argument"] + " " + row["parameters"]
    assert row["verification_level"] == "specification"
    for name in ("ChargingEnabledUntil", "MinimumChargeCurrent", "MaximumChargeCurrent"):
        assert name in row["review"]
    assert "enables charging" in row["review"]
    assert "provisional limit" in row["review"]
    assert "matter association removed" in row["review"]
    assert "evse.operation.set_supply" in row["review"]
    supply = next(
        item
        for item in _rows("pe06-operations.tsv")
        if item["operation"] == "evse.operation.set_supply"
    )
    assert "EnableCharging" in supply["matter_1_6_1"]
    assert "evse.limit.minimum_charge_current" in supply["parameters"]


def test_grid_carbon_intensity_withholds_unknown_native_unit():
    fields = {row["id"]: row for row in _rows("pe12-fields.tsv")}
    native = {
        "energy.grid.carbon_intensity": "GridCarbonIntensity",
        "energy.grid.local_carbon_intensity": "LocalCarbonIntensity",
    }
    for element, field_name in native.items():
        row = fields[element]
        assert row["matter_1_6_1"] == ""
        assert row["eebus"] == ""
        assert row["unit"] == ""
        assert row["direction"] == ""
        assert row["minimum"] == "" and row["maximum"] == ""
        assert "kilogram_per_joule" not in row["unit"] + row["source"] + row["review"]
        assert "kg/Wh" not in row["source"] + row["review"]
        assert "ElectricalGridConditions" not in row["matter_1_6_1"]
        assert "ElectricalGridConditions" not in row["source"]
        assert "Matter 1.6.1" not in row["source"]
        assert "matter.unmapped.v1" in row["source"]
        assert "eebus.unmapped.v1" in row["source"]
        assert "int16" in row["source"]
        assert "no unit name" in row["source"]
        assert "conversion undeclared" in row["source"]
        assert "bound not in specification" in row["source"]
        assert field_name in row["review"]
        assert "int16" in row["review"]
        assert "no unit name" in row["review"]
        assert "native unit" in row["review"]
        assert "conversion" in row["review"]
        assert "matter association removed" in row["review"]
        assert row["verification_level"] == "specification"
        assert row["value_kind"] == "quantity"
    for element in ("energy.grid.carbon_level", "energy.grid.local_carbon_level", "energy.grid.start", "energy.grid.end"):
        assert "ElectricalGridConditions" in fields[element]["matter_1_6_1"]
    incentive = fields["energy.incentive.co2_intensity"]
    assert "TOUT-011" in incentive["eebus"]
    assert "SPINE:IncentiveTable" in incentive["eebus"]


def test_current_and_next_tariff_days_project_date():
    fields = {row["id"]: row for row in _rows("pe12-fields.tsv")}
    expected = {
        "energy.tariff.current_day": "CommodityTariff.CurrentDay.Date",
        "energy.tariff.next_day": "CommodityTariff.NextDay.Date",
    }
    for element, matter in expected.items():
        row = fields[element]
        assert row["value_kind"] == "time"
        assert row["matter_1_6_1"] == matter
        assert row["matter_1_6_1"] not in {
            "CommodityTariff.CurrentDay",
            "CommodityTariff.NextDay",
        }
        assert "DayStruct.Date" in row["source"]
        assert "DayType" in row["source"]
        assert "DayEntryIds" in row["source"]
        assert "not projected" in row["source"]
        assert "eebus.unmapped.v1" in row["source"]
        assert row["eebus"] == ""
        assert "DayType" in row["review"]
        assert "DayEntryIds" in row["review"]
        assert row["verification_level"] == "specification"


def test_day_entry_and_pattern_qualifiers_use_their_collections():
    rows = {row["id"]: row for row in _rows("pe12-qualifier-dimensions.tsv")}
    entry = rows["energy.dimension.day_entry"]
    pattern = rows["energy.dimension.day_pattern"]
    assert entry["matter_eebus"] == "CommodityTariff.DayEntries.DayEntryId"
    assert pattern["matter_eebus"] == "CommodityTariff.DayPatterns.DayPatternId"
    for row, identifier in (
        (entry, "DayEntryId"),
        (pattern, "DayPatternId"),
    ):
        assert "TariffComponents" not in row["matter_eebus"]
        assert "IncentiveTable" not in row["matter_eebus"]
        assert identifier in row["source"]
        assert "TariffComponentId" in row["source"]
        assert "eebus.unmapped.v1" in row["source"]
        assert row["verification_level"] == "specification"
        assert identifier in row["review"]
    component = rows["energy.dimension.component"]
    assert "CommodityTariff.TariffComponents" in component["matter_eebus"]
    fields = {row["id"]: row for row in _rows("pe12-fields.tsv")}
    assert fields["energy.tariff.day_entry_start"]["qualifiers"] == "energy.dimension.day_entry"
    assert "energy.dimension.day_pattern" in fields["energy.tariff.day_pattern_days"]["qualifiers"]
    assert "energy.dimension.day_entry" in fields["energy.tariff.day_pattern_entry"]["qualifiers"]


def test_harmonic_order_keeps_uint8_source_range():
    row = next(
        item
        for item in _rows("pe10-qualifier-dimensions.tsv")
        if item["id"] == "infrastructure.dimension.harmonic_order"
    )
    assert row["matter_eebus"] == "ElectricalPowerMeasurement.HarmonicMeasurement.Order"
    assert "63" not in row["note"]
    assert "min 1" in row["note"]
    assert "uint8" in row["source"]
    assert "min 1" in row["source"]
    assert "encoding range: uint8" in row["source"]
    assert "1 to 255" in row["source"]
    assert "not a specification maximum" in row["source"]
    assert "HarmonicCurrents" in row["source"]
    assert "HarmonicPhases" in row["source"]
    assert "63" in row["review"]
    assert "max 25" in row["review"]
    assert row["verification_level"] == "specification"
    fields = {item["id"]: item for item in _rows("pe10-fields.tsv")}
    for element in ("infrastructure.ac.harmonic_current", "infrastructure.ac.harmonic_phase"):
        assert fields[element]["qualifiers"] == "infrastructure.dimension.harmonic_order"


def test_reactive_import_export_leave_signed_power_mapped():
    rows = {row["element"]: row for row in _rows("pe10-elements-on-main.tsv")}
    signed = rows["infrastructure.ac.reactive_power"]
    assert signed["matter_1_6_1"] == "ElectricalPowerMeasurement.ReactivePower"
    assert signed["eebus"] == "SPINE:measurement.acPowerReactive"
    for element in ("infrastructure.power.import_reactive", "infrastructure.power.export_reactive"):
        row = rows[element]
        assert row["matter_1_6_1"] == ""
        assert row["eebus"] == ""
        assert "ReactivePower" not in row["matter_1_6_1"]
        assert "ReactivePower" not in row["source"]
        assert "acPowerReactive" not in row["eebus"]
        assert "matter.unmapped.v1" in row["source"]
        assert "eebus.unmapped.v1" in row["source"]
        assert "power-mVAR" in row["review"]
        assert "nonnegative" in row["review"]
        assert "no sign convention" in row["review"]
        assert "native-unit projection" in row["review"]
        assert "matter association removed" in row["review"]
        assert "infrastructure.ac.reactive_power" in row["review"]
        assert row["verification_level"] == "specification"
