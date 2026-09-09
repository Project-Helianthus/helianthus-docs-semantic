#!/usr/bin/env python3
"""Execute and validate the Growatt BMS RS-485 v2.02 storage mapping gate."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'api/v1/mappings/growatt-bms-rs485-v202-storage-v1.json'
DOC=ROOT/'api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md'
REV={'family':'1xSxxP ESS','file_revision':'Rev2.01','header_version':'V2.0','cumulative_revision':'2.02'}
SLICES=[{'function':'FC03','offset':'0x0001','quantity':7},{'function':'FC03','offset':'0x000D','quantity':29},{'function':'FC03','offset':'0x0100','quantity':12},{'function':'FC03','offset':'0x010D','quantity':2}]
LOSS={'unit','range','precision','time','symbol','provenance','identity','capability','operation','policy'}
LIFE={'observation_id','observation_revision','receipt_wall','receipt_monotonic','clock_epoch','source_epoch','driver_generation','transport_generation'}
UNSUPPORTED=['pack_power','state_of_health','cell_temperature_meaning','cell_voltage_extrema','pack_module_cell_string_topology','repeated_pack_identity','warning_error_company_status','extension_words','calibration_control_adjacent_fields','writable_ranges','charge_discharge_limits','interlock','authority','write_operations','acknowledgement','readback','retry','control_routes']

def load(): return json.loads(PATH.read_text())
def mutate(value,m):
 c=value
 for p in m['path'].split('.')[:-1]: c=c[int(p)] if isinstance(c,list) else c[p]
 p=m['path'].split('.')[-1]; c[int(p) if isinstance(c,list) else p]=m['value']
def fail(code): raise ValueError(code)
def project(c):
 n,i,l=c['native'],c['identity'],c['lifecycle']
 if not n.get('request_adu') or not n.get('response_adu') or not n.get('words'): fail('native_evidence_missing')
 if n.get('revision')!=REV or not isinstance(n.get('unit_id'),int) or not 1<=n['unit_id']<=247 or n.get('slices')!=SLICES: fail('revision_or_unit_or_slice_invalid')
 if not i.get('asset_id') or not i.get('source_id') or i['asset_id']==i['source_id']: fail('identity_missing_or_invalid')
 if any(not l.get(k) for k in LIFE): fail('lifecycle_missing')
 if c.get('request_operation'): fail('unsupported_or_withheld')
 t=n['typed']; state={'standby':'storage.status.operating.standby','charging':'storage.status.operating.active','discharging':'storage.status.operating.active'}.get(t['operating_state'])
 if state is None: fail('unsupported_or_withheld')
 if not all(isinstance(t[k],(int,float)) for k in ('soc_percent','pack_voltage_volts','pack_current_amps','temperature_celsius','cumulative_charge_amp_hours','cumulative_discharge_amp_hours')): fail('native_evidence_missing')
 return [['storage.capacity.charge',t['cumulative_charge_amp_hours'],'unit.ampere_hour','transformed'],['storage.capacity.discharge',t['cumulative_discharge_amp_hours'],'unit.ampere_hour','transformed'],['storage.pack.current',t['pack_current_amps'],'unit.ampere','transformed'],['storage.pack.voltage',t['pack_voltage_volts'],'unit.volt','exact'],['storage.state.soc',t['soc_percent'],'unit.percent','exact'],['storage.status.operating',state,None,'transformed'],['storage.temperature.pack',t['temperature_celsius'],'unit.celsius','exact']]
def validate_contract(d):
 if d.get('contract')!='helianthus.semantic.mapping.growatt-bms-rs485-v202.storage/v1' or d.get('pack')!={'id':'helianthus.pack.storage','version':'1.1.0'} or len(d.get('pins',{}))!=10 or d['pins'].get('gateway_tree')!='0a850d5646d46f5782b1396d72a3d93bffa6974e' or d['pins'].get('native_source')!='6c08d4d2acf70bea622da333f6d75e26d2d92621': fail('contract')
 n=d.get('native_contract',{})
 if n.get('revision')!=REV or n.get('unit')!={'selection':'explicit_unicast','allowed':'1..247','broadcast_zero':'no_send'} or n.get('slices')!=SLICES or n.get('qualification')!={'physical_qualified':False,'mapping_qualified':True,'outbound_allowed':False}: fail('native contract')
 identity=d.get('identity',{})
 for key in ('asset_id','source_id'):
  x=identity.get(key,{})
  if x.get('required') is not True or x.get('non_secret') is not True or x.get('forbidden_derivations')!=['unit_id','vendor','version','company','generation']: fail('identity contract')
 if identity.get('failure')!='missing_or_invalid_asset_or_source_identity_fails_closed' or identity.get('source_id',{}).get('distinct_from')!='asset_id': fail('identity contract')
 lifecycle=d.get('lifecycle',{})
 if set(lifecycle.get('required_observation_evidence',[]))!=LIFE|{'unit_id','revision','slices','request_adu','response_adu','words'} or lifecycle.get('qualification')!='mapping_qualified_and_physical_unqualified': fail('lifecycle contract')
 rules=d.get('field_rules',[])
 if len(rules)!=7 or d.get('projection',{}).get('requested_items')!=sorted([r['requested'] for r in rules],key=lambda x:x['item_id']): fail('requested items')
 for r in rules:
  disp=r.get('disposition',{}); loss=disp.get('loss')
  if disp.get('outcome')=='exact' and loss!=[]: fail('exact loss')
  if disp.get('outcome')=='transformed' and (not loss or any(x.get('kind') not in LOSS or not x.get('source_items') or not x.get('description') or type(x.get('reversible')) is not bool for x in loss)): fail('transformed loss')
 if len(d.get('withheld',[]))!=7 or any(not x.get('reason') for x in d['withheld']) or d.get('unsupported')!=UNSUPPORTED: fail('withheld unsupported')
 p=d.get('projection',{})
 if p.get('error_precedence')!=['native_evidence_missing','revision_or_unit_or_slice_invalid','identity_missing_or_invalid','lifecycle_missing','mapping_unqualified','unsupported_or_withheld'] or p.get('operations')!='unsupported_no_authority': fail('projection')
 if d.get('consumer_cutover',{}).get('required_removals')!=['legacy_semantic_path','fallback','comparator','compatibility_only_path','dual_publication']: fail('consumer cutover')
def document(d):
 validate_contract(d); scenarios=d.get('scenarios',[])
 if len(scenarios)!=12 or scenarios[0].get('polarity')!='positive': fail('scenario coverage')
 positive=scenarios[0]
 for scenario in scenarios:
  c=copy.deepcopy(positive)
  for m in scenario.get('mutations',[]): mutate(c,m)
  if scenario['polarity']=='positive':
   if project(c)!=scenario['expect']['facts'] or scenario['expect']['operations']!=[]: fail('positive projection')
  else:
   try: project(c)
   except ValueError as e:
    if str(e)!=scenario['expect']['error']: raise
   else: fail(scenario['id']+' accepted')
def main():
 d=load(); document(d)
 for token in ('gateway-configured', 'physical qualification', 'ampere-hours', 'one atomic SemReg cutover', 'outbound_allowed=false'):
  if token not in DOC.read_text(): fail('document boundary')
 print('Growatt BMS RS-485 v2.02 storage mapping: PASS; 1 positive and 11 negative native-to-SemReg scenarios')
if __name__=='__main__': main()
