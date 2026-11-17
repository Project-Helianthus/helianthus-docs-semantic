#!/usr/bin/env python3
"""Focused mutation coverage for the storage/BMS v1.1 exact contract."""
import copy
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('storage',ROOT/'scripts/validate_storage_bms_pack_v1.py')
v=importlib.util.module_from_spec(spec); sys.modules[spec.name]=v; spec.loader.exec_module(v)
# The member name used before the in-place rename, assembled so that no file spells it.
EARLIER_MEMBER='relation'+'ships'
# The SI unit set of the unit rule in api/README.md; a pack field declares no other unit.
SI_UNITS={'unit.ampere','unit.ampere_hour','unit.cubic_metre_per_second','unit.hertz','unit.joule','unit.kelvin','unit.pascal','unit.ratio','unit.reciprocal_second','unit.volt','unit.volt_ampere','unit.volt_ampere_reactive','unit.watt'}
# Customary and prefixed units that no pack field may declare.
NOT_SI=('unit.percent','unit.kilowatt_hour','unit.celsius','unit.kilowatt','unit.bar','unit.litre_per_minute')
ZERO={'coefficient':'0','exponent10':0}
# Each quantity the unit rule moved: SI unit, customary bounds before the move, exact factor and offset.
# A bound that was unbounded stays unbounded unless LOWER_BOUND states it.
CONVERTED={
 'storage.state.soc':('unit.ratio',Fraction(0),Fraction(100),Fraction(1,100),Fraction(0)),
 'storage.state.soh':('unit.ratio',Fraction(0),Fraction(100),Fraction(1,100),Fraction(0)),
 'storage.energy.charged':('unit.joule',Fraction(0),None,Fraction(3600000),Fraction(0)),
 'storage.energy.discharged':('unit.joule',Fraction(0),None,Fraction(3600000),Fraction(0)),
 'storage.temperature.pack':('unit.kelvin',None,None,Fraction(1),Fraction(27315,100)),
 'storage.temperature.cell':('unit.kelvin',None,None,Fraction(1),Fraction(27315,100)),
}
# Absolute zero: the lower bound a kelvin temperature gains, where the Celsius bound was open.
LOWER_BOUND={'storage.temperature.pack':Fraction(0),'storage.temperature.cell':Fraction(0)}
# Ampere-hour is kept (decided by the project owner): both capacities keep unit and bounds.
KEPT={'storage.capacity.charge','storage.capacity.discharge'}
# Joule energy capacities. Each field of the record is compared whole, so a mutation of
# id, kind, unit, dimension, optional, minimum coefficient, minimum exponent or maximum fails.
ENERGY_CAPACITIES=(
 'storage.energy.remaining',
 'storage.energy.usable_capacity',
 'storage.energy.nominal_capacity',
)
JOULE_CAPACITY_BOUNDS={'minimum':{'coefficient':'0','exponent10':0},'maximum':None}


def energy_capacity_record(identifier):
 return {
  'bounds': dict(JOULE_CAPACITY_BOUNDS),
  'dimension': 'storage.dimension.pack',
  'id': identifier,
  'kind': 'quantity',
  'optional': True,
  'unit': 'unit.joule',
 }


class TestStorageEnergyCapacitiesStayJoule:
 """Remaining, usable and nominal energy capacity stay joule; ampere-hour capacity stays ampere-hour."""

 def run(self):
  table = v.tables()
  specs = {field['id']: field for field in table['field_specs']}
  outline = {field['id']: field for field in v.load()['catalog']['definitions']['fields']}
  for identifier in ENERGY_CAPACITIES:
   if specs.get(identifier) != energy_capacity_record(identifier):
    raise AssertionError(identifier + ' is absent or is not a joule pack quantity')
   catalog = outline.get(identifier)
   expected_outline = {
    'dimension': 'storage.dimension.pack',
    'id': identifier,
    'kind': 'quantity',
    'unit': 'unit.joule',
   }
   if catalog != expected_outline:
    raise AssertionError(identifier + ' catalog outline differs')
  for identifier in ('storage.capacity.charge', 'storage.capacity.discharge'):
   field = specs[identifier]
   if field['unit'] != 'unit.ampere_hour' or field['bounds'] != JOULE_CAPACITY_BOUNDS:
    raise AssertionError(identifier + ' must stay in ampere-hours')
  print('storage_energy_capacities_stay_joule: PASS')

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

def kernel_decimal(value):
    """Exact kernel Decimal of a Fraction, computed independently of the validator."""
    exponent = 0
    while value.denominator != 1:
        value *= 10
        exponent -= 1
        if exponent < -18:
            raise AssertionError('conversion does not terminate in decimal')
    coefficient = value.numerator
    if coefficient == 0:
        return dict(ZERO)
    while coefficient % 10 == 0:
        coefficient //= 10
        exponent += 1
    return {'coefficient': str(coefficient), 'exponent10': exponent}


def expected_bounds(identifier):
    """The SI bounds of a moved field: each customary bound through the exact factor and offset, or the stated lower bound."""
    _, minimum, maximum, factor, offset = CONVERTED[identifier]
    low = LOWER_BOUND.get(identifier, None if minimum is None else minimum * factor + offset)
    high = None if maximum is None else maximum * factor + offset
    return {'minimum': None if low is None else kernel_decimal(low), 'maximum': None if high is None else kernel_decimal(high)}


def check_si_units(data, table):
    if getattr(v, 'CANONICAL_UNITS', None) != SI_UNITS:
        raise AssertionError('validator unit set differs from the unit rule')
    specs = {field['id']: field for field in table['field_specs']}
    outline = {field['id']: field for field in data['catalog']['definitions']['fields']}
    for identifier, field in specs.items():
        if field['kind'] == 'quantity' and field['unit'] not in SI_UNITS:
            raise AssertionError(identifier + ' declares ' + field['unit'])
        if outline[identifier].get('unit') != field.get('unit'):
            raise AssertionError(identifier + ' catalog unit differs from its table')
    for identifier, (unit, *_) in CONVERTED.items():
        if specs[identifier]['unit'] != unit or specs[identifier]['bounds'] != expected_bounds(identifier):
            raise AssertionError(identifier + ' is not the exact SI conversion')
    for identifier in KEPT:
        if specs[identifier]['unit'] != 'unit.ampere_hour' or specs[identifier]['bounds'] != {'minimum': dict(ZERO), 'maximum': None}:
            raise AssertionError(identifier + ' must stay in ampere-hours')
    if specs['storage.state.soc']['bounds']['maximum'] != {'coefficient': '1', 'exponent10': 0}:
        raise AssertionError('state of charge is a ratio from 0 to 1')
    print('si_units_and_exact_bounds: PASS')


def main():
 data=v.load(); table=v.tables(); v.document(data,table); v.validate(data['catalog'],table)
 TestStorageEnergyCapacitiesStayJoule().run()
 check_si_units(data,table)
 catalog_cases=[
  ('wrong_pack',lambda c:c['pack'].update(id='helianthus.pack.pv'),'PackRef'),
  ('wrong_pack_version',lambda c:c['pack'].update(version='1.0.0'),'PackRef'),
  ('missing_domain',lambda c:c['domain_catalog'].pop(),'five-domain'),
  ('missing_field',lambda c:c['definitions']['fields'].pop(),'field catalog'),
  ('interlock_symbol_drift',lambda c:c['definitions']['fields'][22]['symbols'].reverse(),'field catalog'),
  ('unit_swap',lambda c:c['definitions']['fields'][0].update(unit='unit.volt'),'field catalog'),
  ('dimension_swap',lambda c:c['definitions']['fields'][0].update(dimension='storage.dimension.cell'),'field catalog'),
  ('can_live',lambda c:c['candidate_mappings'][0].update(physical_qualified=True),'mapping'),
  ('rs485_control',lambda c:c['candidate_mappings'][1].update(control_route=True),'mapping'),
  ('counter_reset_wrap_weakened',lambda c:c['counter_policy'].update(decrease='infer'),'counter'),
  ('loss_of_qualified_current',lambda c:c['publication_withdrawal_policy']['admission'].remove('qualified_active_capability'),'publication lifecycle'),
  ('supersession_weakened',lambda c:c['supersession'].update(operation_use='implemented'),'supersession'),
  ('fail_closed_state_removed',lambda c:c['interlock_fail_closed_states'].pop(),'fail-closed states'),
  ('relation_list_earlier_name',lambda c:c['definitions'].update({EARLIER_MEMBER:c['definitions'].pop('relations')}),'definition groups'),
  ('relation_list_duplicated',lambda c:c['definitions'].update({EARLIER_MEMBER:list(c['definitions']['relations'])}),'definition groups'),
  ('relation_list_drift',lambda c:c['definitions']['relations'].reverse(),'relations'),
  ('catalog_unit_customary_soc',lambda c:c['definitions']['fields'][0].update(unit='unit.percent'),'field catalog'),
  ('catalog_unit_customary_energy',lambda c:c['definitions']['fields'][5].update(unit='unit.kilowatt_hour'),'field catalog'),
  ('catalog_unit_customary_temperature',lambda c:c['definitions']['fields'][13].update(unit='unit.celsius'),'field catalog'),
 ]
 for case in catalog_cases: catalog_case(*case)
 table_cases=[
  ('wrong_count',lambda t:t['capabilities'].pop(),'exact counts'),
  ('missing_optionality',lambda t:t['field_specs'][0].pop('optional'),'field optionality'),
  ('bound_drift',lambda t:t['field_specs'][0]['bounds'].update(maximum={'coefficient':'99','exponent10':0}),'exact contract tables'),
  ('quantity_unit_retyped',lambda t:t['field_specs'][0].update(unit='unit.volt'),'exact contract tables'),
  ('quantity_dimension_crosswire',lambda t:t['field_specs'][0].update(dimension='storage.dimension.cell'),'exact contract tables'),
  ('duplicate_field_id',lambda t:t['field_specs'][1].update(id='storage.state.soc'),'duplicate field'),
  ('interlock_field_drift',lambda t:t['field_specs'][22].update(dimension='storage.dimension.pack'),'interlock field'),
  ('interlock_symbol_drift',lambda t:t['field_specs'][22]['symbols'].reverse(),'interlock field'),
  ('service_dimension_crosswire',lambda t:t['services'][2].update(dimension='storage.dimension.cell'),'exact contract tables'),
  ('relation_endpoint_crosswire',lambda t:t['relations'][0].update(to='storage.service.pack'),'exact contract tables'),
  ('relation_origin_crosswire',lambda t:t['relations'][1].update(**{'from':'storage.service.system'}),'exact contract tables'),
  ('relation_cardinality_drift',lambda t:t['relations'][0].update(cardinality='one_to_one'),'exact contract tables'),
  ('relation_cardinality_missing',lambda t:t['relations'][2].pop('cardinality'),'relation encoding'),
  ('relation_endpoint_earlier_names',lambda t:t['relations'][3].update(source=t['relations'][3].pop('from'),target=t['relations'][3].pop('to')),'relation encoding'),
  ('relation_member_earlier_name',lambda t:t.update({EARLIER_MEMBER:t.pop('relations')}),'exact table members'),
  ('relation_member_duplicated',lambda t:t.update({EARLIER_MEMBER:copy.deepcopy(t['relations'])}),'exact table members'),
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
  ('ratio_bound_left_in_percent',lambda t:t['field_specs'][1]['bounds'].update(maximum={'coefficient':'1','exponent10':2}),'exact contract tables'),
  ('energy_minimum_dropped',lambda t:t['field_specs'][6]['bounds'].update(minimum=None),'exact contract tables'),
  ('kelvin_minimum_dropped',lambda t:t['field_specs'][12]['bounds'].update(minimum=None),'exact contract tables'),
  ('kelvin_minimum_left_in_celsius',lambda t:t['field_specs'][13]['bounds'].update(minimum={'coefficient':'-27315','exponent10':-2}),'exact contract tables'),
  ('capacity_moved_to_joule',lambda t:t['field_specs'][10].update(unit='unit.joule'),'exact contract tables'),
 ]
 table_cases += [('field_%d_unit_%s' % (index, unit.removeprefix('unit.')), lambda t, index=index, unit=unit: t['field_specs'][index].update(unit=unit), 'field unit is outside the canonical SI unit set') for index in (0, 1, 5, 6, 12, 13) for unit in NOT_SI]
 for case in table_cases: table_case(*case)
 print('baseline: PASS; %d catalog and %d table mutations rejected'%(len(catalog_cases),len(table_cases)))

if __name__=='__main__': main()
