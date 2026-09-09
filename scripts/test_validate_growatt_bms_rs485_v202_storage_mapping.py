#!/usr/bin/env python3
"""Focused mutation controls for the Growatt BMS RS-485 v2.02 mapping gate."""
import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('growatt_mapping', ROOT / 'scripts/validate_growatt_bms_rs485_v202_storage_mapping.py')
v = importlib.util.module_from_spec(spec); sys.modules[spec.name] = v; spec.loader.exec_module(v)

def rejects(name, mutation, expected):
    data = v.load(); data.pop('vectors')
    v.mutate(data, mutation)
    try: v.validate(data)
    except ValueError as error:
        if expected not in str(error): raise AssertionError(error)
    else: raise AssertionError(name + ' accepted')
    print(name + ': REJECTED')

def main():
    cases = [('source_revision',{'path':'pins.native_source','value':'0'*40},'pins'),('gateway_tree',{'path':'pins.gateway_tree','value':'0'*40},'pins'),('unit_zero',{'path':'native_contract.unit.allowed','value':'0..247'},'unit'),('identity_claim',{'path':'identity.asset','value':'unit_id'},'identity'),('lifecycle_promotion',{'path':'lifecycle.qualification','value':'qualified'},'lifecycle'),('ah_to_kwh',{'path':'fields.5.unit','value':'unit.kilowatt_hour'},'field mapping'),('loss_removed',{'path':'fields.3.loss.0','value':'none'},'field mapping'),('operation_grant',{'path':'projection.operations','value':'allowed'},'projection'),('consumer_fallback',{'path':'consumer_cutover.required_removals.1','value':'fallback_allowed'},'consumer cutover')]
    for case in cases: rejects(*case)
    print('baseline: PASS; 9 focused mutations rejected')
if __name__ == '__main__': main()
