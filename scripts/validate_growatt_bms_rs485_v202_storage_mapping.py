#!/usr/bin/env python3
"""Validate the exact public Growatt BMS RS-485 v2.02 storage mapping gate."""
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'api/v1/mappings/growatt-bms-rs485-v202-storage-v1.json'
DOC = ROOT / 'api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md'
PACK = {'id': 'helianthus.pack.storage', 'version': '1.1.0'}
PINS = {'docs_semantic_base':'ed33276cddb2dd86757efcf335c95936bdf4efe2','semreg':'f3f761bc67e10d6a65eba6c13cb4dc51002d6955','storage_docs':'c20fdef000fe95df95fca60c55d651a0614c4efd','storage_runtime':'6556bf4b3fffd645b6c14ebfd194d8570b7c5207','docs_modbus_lifecycle':'35151979c8561d5dc4215030899277aec36d2f9f','modbusreg':'7853d903970a4fdded35abaef01fe30f7e93be6a','native_source':'6c08d4d2acf70bea622da333f6d75e26d2d92621','gateway_main':'32244901c4c8337266cd348bdad90fb9e8eb0a61','gateway_tree':'0a850d5646d46f5782b1396d72a3d93bffa6974e','gateway_reviewed_source':'15ab7f0f4197485c83c04f8fe24000ebe058cb7a'}
FIELDS = [('operating_state','storage.status.operating','transformed',None),('soc_percent','storage.state.soc','exact','unit.percent'),('pack_voltage_volts','storage.pack.voltage','exact','unit.volt'),('pack_current_amps','storage.pack.current','exact','unit.ampere'),('temperature_celsius','storage.temperature.pack','exact','unit.celsius'),('cumulative_charge_amp_hours','storage.capacity.charge','exact','unit.ampere_hour'),('cumulative_discharge_amp_hours','storage.capacity.discharge','exact','unit.ampere_hour'),('remaining_capacity_amp_hours',None,'withheld','unit.ampere_hour'),('full_charge_capacity_amp_hours',None,'withheld','unit.ampere_hour'),('cycle_count',None,'withheld','unit.count'),('continuous_charge_seconds',None,'withheld','unit.second'),('current_cycle_charge_amp_hours',None,'withheld','unit.ampere_hour'),('average_cell_voltage_volts',None,'withheld','unit.volt'),('floating_pack_voltage_volts',None,'withheld','unit.volt'),('mcu_software_version,gauge_version,bms_company,bms_generation,pack_company,pack_generation',None,'native_provenance_only',None)]

def load(): return json.loads(PATH.read_text())
def mutate(value, mutation):
    cursor = value
    parts = mutation['path'].split('.')
    for part in parts[:-1]: cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    cursor[int(parts[-1]) if isinstance(cursor, list) else parts[-1]] = mutation['value']

def validate(value):
    if value.get('contract') != 'helianthus.semantic.mapping.growatt-bms-rs485-v202.storage/v1' or value.get('mapping_id') != 'storage.mapping.growatt.rs485.1xsxxp.v202' or value.get('pack') != PACK: raise ValueError('contract')
    if value.get('pins') != PINS: raise ValueError('pins')
    native = value.get('native_contract', {})
    if native.get('revision') != {'family':'1xSxxP ESS','file_revision':'Rev2.01','header_version':'V2.0','cumulative_revision':'2.02'}: raise ValueError('native revision')
    if native.get('unit') != {'selection':'explicit_unicast','allowed':'1..247','broadcast_zero':'no_send'} or native.get('slices') != [{'function':'FC03','offset':'0x0001','quantity':7},{'function':'FC03','offset':'0x000D','quantity':29},{'function':'FC03','offset':'0x0100','quantity':12},{'function':'FC03','offset':'0x010D','quantity':2}]: raise ValueError('unit')
    if native.get('qualification') != {'physical_qualified':False,'semantic_qualified':False,'outbound_allowed':False}: raise ValueError('qualification')
    identity = value.get('identity', {})
    if identity.get('asset') != 'no_semantic_asset_identity_emitted' or identity.get('rule') != 'all_fields_required_as_native_coherent_evidence; none_is_a_stable_asset_selector': raise ValueError('identity')
    lifecycle = value.get('lifecycle', {})
    if lifecycle.get('qualification') != 'false_blocks_semantic_promotion_and_operations' or lifecycle.get('withdrawal') != 'explicit_generation_fenced' or set(lifecycle.get('observation', [])) != {'observation_id','observation_revision','receipt_wall','receipt_monotonic','clock_epoch','source_epoch','driver_generation','transport_generation','unit_id','revision','slices','request_adu','response_adu','words'}: raise ValueError('lifecycle')
    actual = [(x.get('source'),x.get('target'),x.get('disposition'),x.get('unit')) for x in value.get('fields', [])]
    if actual != FIELDS or value['fields'][3].get('loss') != ['signed_direction'] or value['fields'][5].get('loss') != ['counter_reset_wrap'] or value['fields'][6].get('loss') != ['counter_reset_wrap']: raise ValueError('field mapping')
    if value.get('projection', {}).get('operations') != 'unsupported_no_authority' or value['projection'].get('missing_native') != 'unavailable_withheld_never_zero': raise ValueError('projection')
    cutover = value.get('consumer_cutover', {})
    if cutover.get('consumers') != ['semantic_mcp','graphql','portal','home_assistant'] or cutover.get('implementation_requirement') != 'one_atomic_cutover' or cutover.get('required_removals') != ['legacy_semantic_path','fallback','comparator','compatibility_only_path','dual_publication']: raise ValueError('consumer cutover')

def document(value):
    baseline = copy.deepcopy(value); vectors = baseline.pop('vectors', None)
    validate(baseline)
    expected = ['growatt-v202-storage-positive','growatt-v202-storage-negative-native-revision','growatt-v202-storage-negative-unit','growatt-v202-storage-negative-identity','growatt-v202-storage-negative-lifecycle','growatt-v202-storage-negative-loss','growatt-v202-storage-negative-operation','growatt-v202-storage-negative-consumer']
    if [x.get('id') for x in vectors or []] != expected: raise ValueError('vectors')
    for vector in vectors:
        candidate = copy.deepcopy(baseline)
        for mutation in vector.get('input', {}).get('mutations', []): mutate(candidate, mutation)
        if vector['polarity'] == 'positive': validate(candidate); continue
        try: validate(candidate)
        except ValueError as error:
            if vector['expect']['error'] not in str(error): raise
        else: raise ValueError(vector['id'] + ' accepted')

def main():
    document(load())
    text = DOC.read_text()
    for token in ('ampere-hours', 'Capacity is never converted to', 'outbound_allowed=false', 'one atomic SemReg cutover', 'no consumer binding'):
        if token not in text: raise ValueError('document boundary')
    print('Growatt BMS RS-485 v2.02 storage mapping: PASS; 1 positive and 7 negative vectors')
if __name__ == '__main__': main()
