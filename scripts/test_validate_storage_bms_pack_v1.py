#!/usr/bin/env python3
"""Focused mutation coverage for the storage/BMS v1.1 exact contract."""
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

def reject_table(table,error):
 try: v.validate(v.load()['catalog'],table)
 except ValueError as value:
  if error not in str(value): raise AssertionError(value)
 else: raise AssertionError('table mutation accepted')

def catalog_case(name,change,error):
 data=copy.deepcopy(v.load()); change(data['catalog']); reject_catalog(data,error); print(name+': REJECTED')

def table_case(name,change,error):
 table=copy.deepcopy(v.tables()); change(table); reject_table(table,error); print(name+': REJECTED')

def main():
 data=v.load(); table=v.tables(); v.document(data,table); v.validate(data['catalog'],table)
 catalog_cases=[
  ('wrong_pack',lambda c:c['pack'].update(id='helianthus.pack.pv'),'PackRef'),
  ('wrong_pack_version',lambda c:c['pack'].update(version='1.0.0'),'PackRef'),
  ('missing_domain',lambda c:c['domain_catalog'].pop(),'five-domain'),
  ('missing_field',lambda c:c['definitions']['fields'].pop(),'field catalog'),
  ('interlock_symbol_drift',lambda c:c['definitions']['fields'][19]['symbols'].reverse(),'field catalog'),
  ('unit_swap',lambda c:c['definitions']['fields'][0].update(unit='unit.volt'),'field catalog'),
  ('dimension_swap',lambda c:c['definitions']['fields'][0].update(dimension='storage.dimension.cell'),'field catalog'),
  ('can_live',lambda c:c['candidate_mappings'][0].update(physical_qualified=True),'mapping'),
  ('rs485_control',lambda c:c['candidate_mappings'][1].update(control_route=True),'mapping'),
  ('counter_reset_wrap_weakened',lambda c:c['counter_policy'].update(decrease='infer'),'counter'),
  ('loss_of_qualified_current',lambda c:c['publication_withdrawal_policy']['admission'].remove('qualified_active_capability'),'publication lifecycle'),
  ('supersession_weakened',lambda c:c['supersession'].update(operation_use='implemented'),'supersession'),
  ('fail_closed_state_removed',lambda c:c['interlock_fail_closed_states'].pop(),'fail-closed states'),
 ]
 for case in catalog_cases: catalog_case(*case)
 table_cases=[
  ('wrong_count',lambda t:t['capabilities'].pop(),'exact counts'),
  ('missing_optionality',lambda t:t['field_specs'][0].pop('optional'),'field optionality'),
  ('bound_drift',lambda t:t['field_specs'][0]['bounds'].update(maximum={'coefficient':'99','exponent10':0}),'exact contract tables'),
  ('quantity_unit_retyped',lambda t:t['field_specs'][0].update(unit='unit.volt'),'exact contract tables'),
  ('quantity_dimension_crosswire',lambda t:t['field_specs'][0].update(dimension='storage.dimension.cell'),'exact contract tables'),
  ('duplicate_field_id',lambda t:t['field_specs'][1].update(id='storage.state.soc'),'duplicate field'),
  ('interlock_field_drift',lambda t:t['field_specs'][19].update(dimension='storage.dimension.pack'),'interlock field'),
  ('interlock_symbol_drift',lambda t:t['field_specs'][19]['symbols'].reverse(),'interlock field'),
  ('service_dimension_crosswire',lambda t:t['services'][2].update(dimension='storage.dimension.cell'),'exact contract tables'),
  ('relationship_endpoint_crosswire',lambda t:t['relationships'][0].update(target='storage.service.pack'),'exact contract tables'),
  ('relationship_cardinality_drift',lambda t:t['relationships'][0].update(cardinality='one_to_one'),'exact contract tables'),
  ('interface_capability_field_drift',lambda t:t['capabilities'][2]['field_ids'].reverse(),'qualified-current interface capability'),
  ('interface_capability_binding_drift',lambda t:t['capabilities'][2].update(binding='unqualified'),'qualified-current interface capability'),
  ('portal_capability_drift',lambda t:t['portal_contributions'][2].update(capability=None),'Portal interface contribution'),
  ('portal_field_drift',lambda t:t['portal_contributions'][2]['fields'].pop(),'Portal interface contribution'),
  ('operation_input_crosswire',lambda t:t['operations'][0].update(input='storage.limit.discharge_power'),'exact contract tables'),
  ('operation_authority_weakened',lambda t:t['operations'][0]['preconditions'].remove('authority_admitted'),'exact contract tables'),
  ('old_interlock_control',lambda t:t['operations'][0]['preconditions'].__setitem__(4,'interlock_admitted'),'canonical interlock predicate'),
  ('missing_canonical_predicate',lambda t:t['operations'][0].pop('canonical_interlock_predicate'),'canonical interlock predicate'),
  ('duplicate_canonical_predicate',lambda t:t['operations'][0].update(canonical_interlock_predicates=[copy.deepcopy(v.INTERLOCK_PREDICATE),copy.deepcopy(v.INTERLOCK_PREDICATE)]),'duplicate canonical interlock predicate'),
  ('unrelated_predicate_fact',lambda t:t['operations'][0]['canonical_interlock_predicate']['definition'].update(id='storage.status.alarm'),'canonical interlock predicate'),
  ('predicate_pack_drift',lambda t:t['operations'][0]['canonical_interlock_predicate']['definition']['pack'].update(id='helianthus.pack.pv'),'canonical interlock predicate'),
  ('predicate_version_drift',lambda t:t['operations'][0]['canonical_interlock_predicate']['definition'].update(version='1.0.0'),'canonical interlock predicate'),
  ('predicate_dimension_drift',lambda t:t['operations'][0]['canonical_interlock_predicate'].update(fact_key_dimensions=['storage.dimension.pack']),'canonical interlock predicate'),
  ('predicate_operator_drift',lambda t:t['operations'][0]['canonical_interlock_predicate'].update(operator='not_equal'),'canonical interlock predicate'),
  ('predicate_value_drift',lambda t:t['operations'][0]['canonical_interlock_predicate']['expected_value']['symbol'].update(token='active'),'canonical interlock predicate'),
  ('predicate_unknown_symbol',lambda t:t['operations'][0]['canonical_interlock_predicate']['expected_value']['symbol'].update(known=False),'canonical interlock predicate'),
  ('effect_dimension_drift',lambda t:t['effects'][0].update(fact_key_dimensions=['storage.dimension.pack']),'same-interface equal predicate'),
  ('effect_comparator_drift',lambda t:t['effects'][0].update(comparator='greater_than'),'same-interface equal predicate'),
  ('operation_terminal_drift',lambda t:t['operations'][0]['terminal_outcomes'].pop(),'kernel outcomes/no-blind-retry'),
  ('blind_retry',lambda t:t['operations'][0].update(retry='allowed'),'kernel outcomes/no-blind-retry'),
  ('supersession_drift',lambda t:t['supersession'].update(operation_use='implemented'),'supersession'),
  ('fail_closed_state_removed',lambda t:t['interlock_fail_closed_states'].pop(),'fail-closed states'),
  ('definition_ref_wrong_owner',lambda t:t['definition_index']['fields'][0]['pack'].update(id='helianthus.pack.pv'),'DefinitionRef owner/version'),
  ('definition_ref_missing_version',lambda t:t['definition_index']['services'][0].pop('version'),'DefinitionRef owner/version'),
  ('definition_index_out_of_order',lambda t:t['definition_index']['fields'].__setitem__(slice(0,2),list(reversed(t['definition_index']['fields'][:2]))),'noncanonical DefinitionIndex order'),
  ('decimal_malformed_coefficient',lambda t:t['field_specs'][0]['bounds']['minimum'].update(coefficient='00'),'bounds must use canonical kernel Decimal'),
  ('decimal_zero_exponent',lambda t:t['field_specs'][0]['bounds']['minimum'].update(exponent10=1),'bounds must use canonical kernel Decimal'),
  ('decimal_trailing_zero',lambda t:t['field_specs'][0]['bounds']['maximum'].update(coefficient='10',exponent10=1),'bounds must use canonical kernel Decimal'),
  ('decimal_reversed_bounds',lambda t:t['field_specs'][0].update(bounds={'minimum':{'coefficient':'1','exponent10':2},'maximum':{'coefficient':'0','exponent10':0}}),'reversed bounds'),
 ]
 for case in table_cases: table_case(*case)
 print('baseline: PASS; 13 catalog and 40 table mutations rejected')

if __name__=='__main__': main()
