#!/usr/bin/env python3
"""Validate the exact storage/BMS v1 machine contract and catalog."""
from __future__ import annotations
import copy, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; VECTORS=ROOT/'api/v1/packs/storage-bms-acceptance-vectors.json'; TABLES=ROOT/'api/v1/packs/storage-bms-contract-tables.json'; DOCUMENT=ROOT/'api/v1/packs/storage-bms-v1.md'
PACK={'id':'helianthus.pack.storage','version':'1.0.0'}
DOMAINS={'thermal_hvac':('helianthus.pack.thermal','accepted'),'pv_inverter':('helianthus.pack.pv','exact_head_review'),'storage_bms':('helianthus.pack.storage','accepted'),'evse':('helianthus.pack.evse','follow_on'),'infrastructure':('helianthus.pack.infrastructure','follow_on')}
PINS={'semantic_docs':'346cda9b675a03a7d1a8c886a3467eab84ce8fb2','semreg_projection':'cc9b324225e945598128eeabe977e7fa0af6dc93','can_docs':'665a5f22f78c349b5e3063bda158af250a3f44b6','canbusreg':'8c827ea26ffbad8b50aba2c6ae89028622ba4343','rs485_docs':'c9d37b7f7cd5ebc6c4125565648a7deb094aaa7a','modbusreg':'f1e593995576fdfbbc64fd879b47abff8bd2cc0e','eebus_ledger':'81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1','matter_draft':'29b4768a513cf566011ab8cd60df1bc495204953'}
LOSS={'native_enum_bitfield','precision_range','cell_module_topology','signed_direction','aggregation_reference','counter_reset_wrap','unavailable_fields','conflicting_sources','vendor_extensions','unsupported_operations'}
LIFECYCLE={'source_epoch','driver_generation','semantic_revision','capability_qualification','activation','generation_fencing','partial_updates','stale_unknown_evidence','last_known_good_retention'}
# The digest covers every object, value, list order, and extra key in the canonical table.
TABLE_SHA256='be63e9f6d90f98da3df113fe914a9b791a6974fd4e87a17f22cccf6f147a7811'
OUTCOMES=['rejected','failed_no_contact','acknowledged_unverified','applied','no_effect','conflict','indeterminate']

def load(): return json.loads(VECTORS.read_text())
def tables(): return json.loads(TABLES.read_text())
def exact(actual, expected, name):
 if actual!=expected: raise ValueError(name)
def canonical_digest(value): return hashlib.sha256(json.dumps(value,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def decimal(value):
 if not isinstance(value,dict) or set(value)!={'coefficient','exponent10'} or not isinstance(value['coefficient'],str) or not re.fullmatch(r'0|-?[1-9][0-9]*',value['coefficient']) or type(value['exponent10']) is not int or not -18<=value['exponent10']<=18 or (value['coefficient']=='0' and value['exponent10']!=0) or (value['coefficient']!='0' and value['coefficient'].endswith('0')): raise ValueError('bounds must use canonical kernel Decimal')
 return int(value['coefficient'])*10**value['exponent10']

def validate_tables(table):
 fields=table['field_specs']
 index=table.get('definition_index',{}); expected={'fields':[x.get('id') for x in fields],'services':[x.get('id') for x in table['services']],'capabilities':[x.get('id') for x in table['capabilities']],'operations':[x.get('id') for x in table['operations']],'effect_rules':[x.get('id') for x in table['effects']]}
 if index.get('pack')!=PACK: raise ValueError('DefinitionIndex PackRef')
 for category,ids in expected.items():
  refs=index.get(category)
  if not all(isinstance(identifier,str) for identifier in ids): raise ValueError('DefinitionRef owner/version')
  ordered=sorted(ids)
  if not isinstance(refs,list) or [ref.get('id') for ref in refs]!=ordered: raise ValueError('noncanonical DefinitionIndex order')
  if any(ref!={'pack':PACK,'id':identifier,'version':'1.0.0'} for ref,identifier in zip(refs,ordered)): raise ValueError('DefinitionRef owner/version')
 if len({field.get('id') for field in fields})!=len(fields): raise ValueError('duplicate field')
 for field in fields:
  if field.get('optional') is not True: raise ValueError('field optionality')
  if field.get('kind')=='quantity':
   if set(field)!={'id','kind','unit','dimension','optional','bounds'} or not isinstance(field.get('bounds'),dict) or set(field['bounds'])!={'minimum','maximum'}: raise ValueError('field bounds')
   low,high=field['bounds']['minimum'],field['bounds']['maximum']
   if low is not None: low=decimal(low)
   if high is not None: high=decimal(high)
   if low is not None and high is not None and low>high: raise ValueError('reversed bounds')
  elif field.get('kind')=='symbol':
   if set(field)!={'id','kind','dimension','optional','symbols'} or not isinstance(field.get('symbols'),list) or field['symbols']!=sorted(set(field['symbols'])): raise ValueError('field symbols')
  else: raise ValueError('field kind')
 for operation in table['operations']:
  if operation.get('terminal_outcomes')!=OUTCOMES or operation.get('retry')!='forbidden_after_possible_side_effect_or_indeterminate': raise ValueError('kernel outcomes/no-blind-retry')
 if canonical_digest(table)!=TABLE_SHA256: raise ValueError('exact contract tables')

def validate(catalog,table=None):
 table=tables() if table is None else table; validate_tables(table)
 if catalog.get('pack')!=PACK or catalog.get('kernel_contract')!='helianthus.semantic.kernel/v1': raise ValueError('PackRef')
 exact({x.get('id'):(x.get('pack'),x.get('state')) for x in catalog.get('domain_catalog',[])},DOMAINS,'five-domain catalog')
 exact({x.get('id'):x.get('revision') for x in catalog.get('inputs',[])},PINS,'pins')
 if set(catalog.get('lifecycle_axes',[]))!=LIFECYCLE or set(catalog.get('loss_dispositions',[]))!=LOSS: raise ValueError('lifecycle/loss')
 if catalog.get('counter_policy')!={'decrease':'never_infer_reset_or_wrap','continuity':'native_reset_or_wrap_evidence_required'}: raise ValueError('counter')
 d=catalog.get('definitions',{}); fields=d.get('fields',[])
 outline=[{key:field[key] for key in ('id','kind','unit','dimension','symbols') if key in field} for field in table['field_specs']]
 exact(fields,outline,'field catalog')
 exact(d.get('dimensions'),['system','battery','pack','module','cell','string','interface'],'dimensions')
 exact(d.get('relationships'),[entry['id'].removeprefix('storage.relationship.') for entry in table['relationships']],'relationships')
 exact(d.get('operations'),[entry['id'].removeprefix('storage.operation.') for entry in table['operations']],'operations')
 exact(d.get('portal'),{'read':'all_fields_exactly_once','operation':'current_admission_only'},'Portal')
 expected=[
  {'id':'storage.mapping.growatt.can.v104','native_owner':'helianthus-docs-canbus','source_refs':['can_docs','canbusreg'],'state':'candidate','qualification':'synthetic_offline_selected_interface_only','physical_qualified':False,'control_route':False,'loss':'unknown'},
  {'id':'storage.mapping.growatt.rs485.1xsxxp','native_owner':'helianthus-docs-modbus','source_refs':['rs485_docs','modbusreg'],'state':'candidate','qualification':'observation_fixture_no_runtime_or_command','physical_qualified':False,'control_route':False,'loss':'unknown'},
  {'id':'storage.mapping.eebus','native_owner':'helianthus-docs-eebus','source_refs':['eebus_ledger'],'state':'unknown_pending_std_01','qualification':'unresolved','loss':'unknown'}]
 exact(catalog.get('candidate_mappings'),expected,'mapping boundary')

def mutate(target,mutation):
 cursor=target; path=mutation['path'].split('.')
 for segment in path[:-1]: cursor=cursor[int(segment)] if isinstance(cursor,list) else cursor[segment]
 cursor[int(path[-1]) if isinstance(cursor,list) else path[-1]]=mutation['value']

def document(data,table=None):
 if data.get('contract')!='helianthus.semantic.pack.storage.acceptance/v1' or data.get('pack_contract')!='helianthus.pack.storage/v1': raise ValueError('contract')
 table=tables() if table is None else table; validate(data['catalog'],table)
 for vector in data['vectors']:
  catalog=copy.deepcopy(data['catalog'])
  for mutation in vector.get('input',{}).get('mutations',[]): mutate(catalog,mutation)
  if vector['polarity']=='positive': validate(catalog,table)
  else:
   try: validate(catalog,table)
   except ValueError as error:
    if vector['expect']['error'] not in str(error): raise
   else: raise ValueError(vector['id']+' accepted')

def main():
 data=load(); document(data)
 for token in ('state of charge','physical_qualified=false','No generic contactor','unknown_pending_std_01','unbounded maximum'):
  if token not in DOCUMENT.read_text(): raise ValueError('document boundary')
 print('storage/BMS pack v1: PASS')
if __name__=='__main__': main()
