#!/usr/bin/env python3
"""Execute and validate the Growatt BMS RS-485 v2.02 storage mapping gate."""
import copy
import json
import math
import re
from datetime import datetime
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
 path=m['path'].replace('native.request_adu','observation.slices.0.request_adu_hex').replace('native.words','observation.slices.0.words').replace('native.revision','observation.revision').replace('native.unit_id','observation.slices.0.unit_id').replace('native.slices','observation.slices').replace('native.typed','observation.typed')
 if 'source' in value and path=='identity.source_id': path='source.source_id'
 c=value
 for p in path.split('.')[:-1]: c=c[int(p)] if isinstance(c,list) else c[p]
 p=path.split('.')[-1]; c[int(p) if isinstance(c,list) else p]=m['value']
def fail(code): raise ValueError(code)
def project(c):
 n,i,src,l,q=c['observation'],c['identity'],c['source'],c['lifecycle'],c['qualification']
 if n.get('revision')!=REV or len(n.get('slices',[]))!=4: fail('revision_or_unit_or_slice_invalid')
 for actual,required in zip(n['slices'],SLICES):
  if {k:actual.get(k) for k in ('function','offset','quantity')}!=required or not isinstance(actual.get('unit_id'),int) or not 1<=actual['unit_id']<=247 or actual.get('transport_generation')!=l.get('transport_generation'): fail('revision_or_unit_or_slice_invalid')
  if not actual.get('request_id') or not re.fullmatch(r'[0-9A-Fa-f]+',str(actual.get('request_adu_hex',''))) or not re.fullmatch(r'[0-9A-Fa-f]+',str(actual.get('response_adu_hex',''))) or len(actual.get('words',[]))!=actual['quantity']: fail('native_evidence_missing')
 if not isinstance(i.get('asset_id'),str) or not isinstance(src.get('source_id'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@-]*',i['asset_id']) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@-]*',src['source_id']) or i['asset_id']==src['source_id']: fail('identity_missing_or_invalid')
 if any(not l.get(k) for k in LIFE) or any(not isinstance(l[k],int) or isinstance(l[k],bool) or l[k]<1 for k in ('observation_revision','clock_epoch','source_epoch','driver_generation','transport_generation')) or not re.fullmatch(r'[1-9][0-9]*ns',str(l['receipt_monotonic'])): fail('lifecycle_missing')
 try: datetime.fromisoformat(l['receipt_wall'].replace('Z','+00:00'))
 except (AttributeError,ValueError): fail('lifecycle_missing')
 if q!={'physical_qualified':False,'mapping_qualified':True,'outbound_allowed':False}: fail('mapping_unqualified')
 if c.get('request_operation'): fail('unsupported_or_withheld')
 t=n['typed']; state={'standby':'storage.status.operating.standby','charging':'storage.status.operating.active','discharging':'storage.status.operating.active'}.get(t['operating_state'])
 # A valid observation with soft-starting withholds only operating state. The
 # other independent typed fields continue through the same receipt.
 if state is None and t['operating_state']!='soft_starting': fail('unsupported_or_withheld')
 if not all(isinstance(t[k],(int,float)) and not isinstance(t[k],bool) and math.isfinite(t[k]) for k in ('soc_percent','pack_voltage_volts','pack_current_amps','temperature_celsius','cumulative_charge_amp_hours','cumulative_discharge_amp_hours')) or not 0<=t['soc_percent']<=100 or t['pack_voltage_volts']<0 or t['cumulative_charge_amp_hours']<0 or t['cumulative_discharge_amp_hours']<0: fail('native_evidence_missing')
 requested=[{'kind':'fact','item_id':x} for x in ['storage.capacity.charge','storage.capacity.discharge','storage.pack.current','storage.pack.voltage','storage.state.soc','storage.status.operating','storage.temperature.pack']]
 values={'storage.capacity.charge':t['cumulative_charge_amp_hours'],'storage.capacity.discharge':t['cumulative_discharge_amp_hours'],'storage.pack.current':t['pack_current_amps'],'storage.pack.voltage':t['pack_voltage_volts'],'storage.state.soc':t['soc_percent'],'storage.temperature.pack':t['temperature_celsius']}
 units={'storage.capacity.charge':'unit.ampere_hour','storage.capacity.discharge':'unit.ampere_hour','storage.pack.current':'unit.ampere','storage.pack.voltage':'unit.volt','storage.state.soc':'unit.percent','storage.temperature.pack':'unit.celsius'}
 dispositions=[]
 for item in requested:
  key=item['item_id']; outcome='exact'; loss=[]; reason=None
  if key=='storage.status.operating':
   outcome='withheld' if state is None else 'transformed'; reason='storage.reason.soft_starting_not_representable' if state is None else None; loss=[] if state is None else [{'kind':'symbol','source_items':['native.growatt.bms.rs485.v202.operating_state'],'description':'charging and discharging collapse to active; soft_starting is withheld','reversible':False}]
  elif key=='storage.pack.current': outcome='transformed'; loss=[{'kind':'provenance','source_items':['native.growatt.bms.rs485.v202.pack_current'],'description':'native current sign reference is retained as provenance','reversible':True}]
  elif key.startswith('storage.capacity.'): outcome='transformed'; loss=[{'kind':'policy','source_items':['native.growatt.bms.rs485.v202.'+('cumulative_charge_capacity' if key.endswith('charge') else 'cumulative_discharge_capacity')],'description':'counter continuity/reset/wrap remains native evidence','reversible':False}]
  dispositions.append({'kind':'fact','item_id':key,'source_key':{'asset_id':i['asset_id'],'source_id':src['source_id'],'dimension':'storage.dimension.pack'},'outcome':outcome,'value':state if key=='storage.status.operating' and state else values.get(key),'unit':units.get(key),'loss':loss,'reason':reason})
 return {'requested':requested,'dispositions':dispositions,'withheld':[],'operations':[]}
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
   output=project(c)
   if output['requested']!=d['projection']['requested_items'] or len(output['dispositions'])!=7 or output['operations']!=[]: fail('positive projection')
  else:
   try: project(c)
   except ValueError as e:
    if str(e)!=scenario['expect']['error']: raise
   else:
    if scenario['id']=='negative-soft-starting-withheld':
     output=project(c)
     if output['dispositions'][5]['outcome']!='withheld' or output['dispositions'][5]['reason']!='storage.reason.soft_starting_not_representable': fail('soft-starting partial')
    else: fail(scenario['id']+' accepted')
def main():
 d=load(); document(d)
 for token in ('gateway-configured', 'physical qualification', 'ampere-hours', 'one atomic SemReg cutover', 'outbound_allowed=false'):
  if token not in DOC.read_text(): fail('document boundary')
 print('Growatt BMS RS-485 v2.02 storage mapping: PASS; 1 positive and 11 negative native-to-SemReg scenarios')
if __name__=='__main__': main()
