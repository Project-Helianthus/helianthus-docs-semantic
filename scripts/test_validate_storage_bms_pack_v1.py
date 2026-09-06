#!/usr/bin/env python3
"""Focused mutation coverage for the storage/BMS exact contract."""
import copy
import importlib.util
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('storage',ROOT/'scripts/validate_storage_bms_pack_v1.py')
v=importlib.util.module_from_spec(spec); sys.modules[spec.name]=v; spec.loader.exec_module(v)

def reject_catalog(data,error):
 try: v.document(data)
 except ValueError as value:
  if error not in str(value): raise AssertionError(value)
 else: raise AssertionError('catalog mutation accepted')

def reject_table(table,error='exact contract tables'):
 try: v.validate(v.load()['catalog'],table)
 except ValueError as value:
  if error!='exact contract tables' and error not in str(value): raise AssertionError(value)
 else: raise AssertionError('table mutation accepted')

def run_catalog(name,change,error):
 data=copy.deepcopy(v.load()); change(data['catalog']); reject_catalog(data,error); print(name+': REJECTED')

def run_table(name,change,error='exact contract tables'):
 table=copy.deepcopy(v.tables()); change(table); reject_table(table,error); print(name+': REJECTED')

def main():
 data=v.load(); table=v.tables(); v.document(data,table); v.validate(data['catalog'],table)
 catalog_cases=[
  ('wrong_pack',lambda c:c['pack'].update(id='helianthus.pack.pv'),'PackRef'),
  ('missing_domain',lambda c:c['domain_catalog'].pop(),'five-domain'),
  ('missing_field',lambda c:c['definitions']['fields'].pop(),'field catalog'),
  ('unit_swap',lambda c:c['definitions']['fields'][0].update(unit='unit.volt'),'field catalog'),
  ('dimension_swap',lambda c:c['definitions']['fields'][0].update(dimension='storage.dimension.cell'),'field catalog'),
  ('duplicate_symbol',lambda c:c['definitions']['fields'][15].update(symbols=['x','x']),'field catalog'),
  ('can_live',lambda c:c['candidate_mappings'][0].update(physical_qualified=True),'mapping'),
  ('rs485_control',lambda c:c['candidate_mappings'][1].update(control_route=True),'mapping'),
  ('wrong_owner',lambda c:c['candidate_mappings'][0].update(native_owner='helianthus-semreg'),'mapping'),
  ('extra_mapping',lambda c:c['candidate_mappings'].append({}),'mapping'),
  ('missing_loss',lambda c:c['candidate_mappings'][0].pop('loss'),'mapping'),
  ('counter_reset_wrap_weakened',lambda c:c['counter_policy'].update(decrease='infer'),'counter'),
 ]
 for name,change,error in catalog_cases: run_catalog(name,change,error)
 table_cases=[
  ('missing_optionality',lambda t:t['field_specs'][0].pop('optional')),
  ('bound_drift',lambda t:t['field_specs'][0]['bounds'].update(maximum={'coefficient':'99','exponent10':0})),
  ('quantity_unit_retyped',lambda t:t['field_specs'][0].update(unit='unit.volt')),
  ('quantity_dimension_crosswire',lambda t:t['field_specs'][0].update(dimension='storage.dimension.cell')),
  ('duplicate_field_id',lambda t:t['field_specs'][1].update(id='storage.state.soc')),
  ('symbol_set_drift',lambda t:t['field_specs'][15]['symbols'].append('storage.status.operating.fault')),
  ('service_dimension_crosswire',lambda t:t['services'][2].update(dimension='storage.dimension.cell')),
  ('relationship_endpoint_crosswire',lambda t:t['relationships'][0].update(target='storage.service.pack')),
  ('relationship_cardinality_drift',lambda t:t['relationships'][0].update(cardinality='one_to_one')),
  ('capability_service_crosswire',lambda t:t['capabilities'][0].update(service='storage.service.cell')),
  ('capability_field_crosswire',lambda t:t['capabilities'][0]['field_ids'].reverse()),
  ('capability_operation_crosswire',lambda t:t['capabilities'][2].update(operation='storage.operation.set_discharge_limit')),
  ('operation_input_crosswire',lambda t:t['operations'][0].update(input='storage.limit.discharge_power')),
  ('operation_authority_weakened',lambda t:t['operations'][0]['preconditions'].remove('authority_admitted')),
  ('operation_dispatch_drift',lambda t:t['operations'][0].update(dispatch='generic_enable')),
  ('operation_ack_drift',lambda t:t['operations'][0].update(acknowledgement='ack')),
  ('operation_readback_crosswire',lambda t:t['operations'][0].update(readback='stale_effect')),
  ('operation_terminal_drift',lambda t:t['operations'][0]['terminal_outcomes'].pop()),
  ('operation_effect_crosswire',lambda t:t['operations'][0].update(effect='storage.effect.set_discharge_limit')),
  ('effect_field_crosswire',lambda t:t['effects'][0].update(field='storage.limit.discharge_power')),
  ('effect_comparator_drift',lambda t:t['effects'][0].update(comparator='greater_than')),
  ('portal_service_crosswire',lambda t:t['portal_contributions'][0].update(service='storage.service.cell')),
  ('portal_capability_crosswire',lambda t:t['portal_contributions'][0].update(capability='storage.capability.read.cell')),
  ('portal_field_crosswire',lambda t:t['portal_contributions'][0]['fields'].reverse()),
  ('portal_operation_crosswire',lambda t:t['portal_contributions'][3].update(operation='storage.operation.set_discharge_limit')),
  ('portal_admission_drift',lambda t:t['portal_contributions'][3].update(admission='any_generation')),
  ('extra_normative_row',lambda t:t['effects'].append({})),
  ('definition_ref_wrong_owner',lambda t:t['definition_index']['fields'][0]['pack'].update(id='helianthus.pack.pv'),'DefinitionRef owner/version'),
  ('definition_ref_missing_version',lambda t:t['definition_index']['services'][0].pop('version'),'DefinitionRef owner/version'),
  ('decimal_malformed_coefficient',lambda t:t['field_specs'][0]['bounds']['minimum'].update(coefficient='00'),'bounds must use canonical kernel Decimal'),
  ('decimal_zero_exponent',lambda t:t['field_specs'][0]['bounds']['minimum'].update(exponent10=1),'bounds must use canonical kernel Decimal'),
  ('decimal_trailing_zero',lambda t:t['field_specs'][0]['bounds']['maximum'].update(coefficient='10',exponent10=1),'bounds must use canonical kernel Decimal'),
  ('decimal_reversed_bounds',lambda t:t['field_specs'][0].update(bounds={'minimum':{'coefficient':'1','exponent10':2},'maximum':{'coefficient':'0','exponent10':0}}),'reversed bounds'),
  ('missing_acknowledged_unverified',lambda t:t['operations'][0]['terminal_outcomes'].remove('acknowledged_unverified'),'kernel outcomes/no-blind-retry'),
  ('blind_retry',lambda t:t['operations'][0].update(retry='allowed'),'kernel outcomes/no-blind-retry'),
  ('definition_index_fields_out_of_order',lambda t:t['definition_index']['fields'].__setitem__(slice(0,2),list(reversed(t['definition_index']['fields'][:2]))),'noncanonical DefinitionIndex order'),
  ('definition_index_services_out_of_order',lambda t:t['definition_index']['services'].__setitem__(slice(0,2),list(reversed(t['definition_index']['services'][:2]))),'noncanonical DefinitionIndex order'),
  ('definition_index_capabilities_out_of_order',lambda t:t['definition_index']['capabilities'].__setitem__(slice(0,2),list(reversed(t['definition_index']['capabilities'][:2]))),'noncanonical DefinitionIndex order'),
 ]
 for case in table_cases: run_table(*case)
 print('baseline: PASS; 12 catalog and 38 table mutations rejected')

if __name__=='__main__': main()
