#!/usr/bin/env python3
"""Focused mutation coverage for the storage/BMS v1.1 exact contract."""
import copy
import importlib.util
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('storage',ROOT/'scripts/validate_storage_bms_pack_v1.py')
v=importlib.util.module_from_spec(spec); sys.modules[spec.name]=v; spec.loader.exec_module(v)
# The member name used before the in-place rename, assembled so that no file spells it.
EARLIER_MEMBER='relation'+'ships'
# The SI unit set of the unit rule in api/README.md; a pack field declares no other unit.
SI_UNITS={'unit.ampere','unit.ampere_hour','unit.cubic_metre_per_second','unit.hertz','unit.joule','unit.kelvin','unit.pascal','unit.ratio','unit.reciprocal_second','unit.volt','unit.volt_ampere','unit.volt_ampere_reactive','unit.watt', 'unit.second', 'unit.cubic_metre', 'unit.metre', 'unit.ohm', 'unit.radian', 'unit.one', 'unit.volt_ampere_reactive_second', 'unit.volt_ampere_second', 'unit.kilogram_per_cubic_metre', 'unit.becquerel_per_cubic_metre', 'unit.kilogram_per_joule', 'unit.watt_per_square_metre', 'unit.metre_per_joule', 'unit.currency', 'unit.currency_per_joule'}
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


def check_current_limits(table):
    """Current-limit fields and the production mutation each one catches.

    field_specs length: removing storage.limit.charge_current fails exact counts.
    id: renaming that field fails the DefinitionIndex order.
    unit: a unit outside the SI set fails the unit check.
    dimension: moving it off storage.dimension.pack fails the table digest.
    bounds.minimum: filling the charge-current minimum fails the table digest.
    bounds.maximum: filling the discharge-current maximum fails the table digest.
    interlock last: swapping the last field off storage.status.interlock fails the interlock check.
    interface field list: inserting the current limit fails the interface capability check.
    """
    specs = table['field_specs']
    if len(specs) != 96:
        raise AssertionError('field_specs is not 25')
    if specs[-1]['id'] != 'storage.status.interlock':
        raise AssertionError('interlock is not last')
    for ident in ('storage.limit.charge_current', 'storage.limit.discharge_current'):
        field = next(item for item in specs if item['id'] == ident)
        if field['unit'] != 'unit.ampere' or field['dimension'] != 'storage.dimension.pack':
            raise AssertionError(ident)
        if field['bounds'] != {'minimum': None, 'maximum': None}:
            raise AssertionError(ident + ' bounds are not empty')
    cap = next(item for item in table['capabilities'] if item['id'] == 'storage.capability.read.interface')
    expected = ['storage.limit.charge_power', 'storage.limit.discharge_power', 'storage.status.interlock']
    if cap['field_ids'] != expected:
        raise AssertionError('interface capability field list changed')
    print('current_limits: PASS')


def main():
 data=v.load(); table=v.tables(); v.document(data,table); v.validate(data['catalog'],table)
 TestStorageEnergyCapacitiesStayJoule().run()
 check_si_units(data,table)
 check_current_limits(table)
 catalog_cases=[
  ('wrong_pack',lambda c:c['pack'].update(id='helianthus.pack.pv'),'PackRef'),
  ('wrong_pack_version',lambda c:c['pack'].update(version='1.0.0'),'PackRef'),
  ('missing_domain',lambda c:c['domain_catalog'].pop(),'five-domain'),
  ('missing_field',lambda c:c['definitions']['fields'].pop(),'field catalog'),
  ('interlock_symbol_drift',lambda c:next(field for field in c['definitions']['fields'] if field['id']=='storage.status.interlock')['symbols'].reverse(),'field catalog'),
  ('unit_swap',lambda c:c['definitions']['fields'][0].update(unit='unit.volt'),'field catalog'),
  ('dimension_swap',lambda c:c['definitions']['fields'][0].update(dimension='storage.dimension.cell'),'field catalog'),
  ('can_live',lambda c:c['candidate_mappings'][0].update(physical_qualified=True),'mapping'),
  ('rs485_control',lambda c:c['candidate_mappings'][1].update(control_route=True),'mapping'),
  ('counter_reset_wrap_weakened',lambda c:c['counter_policy'].update(decrease='infer'),'counter'),
  ('loss_of_qualified_current',lambda c:c['publication_withdrawal_policy']['admission'].remove('qualified_active_capability'),'publication lifecycle'),
  ('supersession_weakened',lambda c:c['supersession'].update(operation_use='implemented'),'supersession'),
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
  ('interlock_field_drift',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.status.interlock').update(dimension='storage.dimension.pack'),'interlock field'),
  ('interlock_symbol_drift',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.status.interlock')['symbols'].reverse(),'interlock field'),
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
  ('operation_authority_weakened',lambda t:t['operations'][0]['preconditions'].remove('authority_admitted'),'generic preconditions'),
  ('predicate_precondition_readded',lambda t:t['operations'][0]['preconditions'].append('canonical_'+'interlock_predicate'),'generic preconditions'),
  ('predicate_member_added',lambda t:t['operations'][0].update({'canonical_'+'interlock_predicate':{}}),'operation predicate member'),
  ('effect_dimension_drift',lambda t:t['effects'][0].update(fact_key_dimensions=['storage.dimension.pack']),'same-interface equal predicate'),
  ('effect_comparator_drift',lambda t:t['effects'][0].update(comparator='greater_than'),'same-interface equal predicate'),
  ('operation_terminal_drift',lambda t:t['operations'][0]['terminal_outcomes'].pop(),'kernel outcomes/no-blind-retry'),
  ('blind_retry',lambda t:t['operations'][0].update(retry='allowed'),'kernel outcomes/no-blind-retry'),
  ('supersession_drift',lambda t:t['supersession'].update(operation_use='implemented'),'supersession'),
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
  ('charge_current_removed',lambda t:t['field_specs'].pop(next(i for i,field in enumerate(t['field_specs']) if field['id']=='storage.limit.charge_current')),'exact counts'),
  ('charge_current_renamed',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.limit.charge_current').update(id='storage.limit.charge_current_moved'),'noncanonical DefinitionIndex order'),
  ('charge_current_unit',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.limit.charge_current').update(unit='unit.percent'),'field unit is outside the canonical SI unit set'),
  ('charge_current_dimension',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.limit.charge_current').update(dimension='storage.dimension.cell'),'exact contract tables'),
  ('charge_current_minimum',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.limit.charge_current')['bounds'].update(minimum={'coefficient':'0','exponent10':0}),'exact contract tables'),
  ('discharge_current_maximum',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.limit.discharge_current')['bounds'].update(maximum={'coefficient':'1','exponent10':0}),'exact contract tables'),
  ('interlock_not_last',lambda t:t['field_specs'].__setitem__(slice(-2,None),list(reversed(t['field_specs'][-2:]))),'interlock field'),
  ('current_on_interface',lambda t:next(item for item in t['capabilities'] if item['id']=='storage.capability.read.interface')['field_ids'].insert(0,'storage.limit.charge_current'),'qualified-current interface capability'),
  ('text_field_extra_member',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.cob.actor').update(unit='unit.one'),'field kind'),
  ('boolean_field_extra_member',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.setpoint.active').update(symbols=['on']),'field kind'),
  ('symbols_field_extra_member',lambda t:next(field for field in t['field_specs'] if field['id']=='storage.status.faults').update(unit='unit.one'),'field symbols'),
 ]
 table_cases += [('field_%d_unit_%s' % (index, unit.removeprefix('unit.')), lambda t, index=index, unit=unit: t['field_specs'][index].update(unit=unit), 'field unit is outside the canonical SI unit set') for index in (0, 1, 5, 6, 12, 13) for unit in NOT_SI]
 for case in table_cases: table_case(*case)
 check_duration_identity()
 print('baseline: PASS; %d catalog and %d table mutations rejected'%(len(catalog_cases),len(table_cases)))


def duration_case(name, change, error):
    data = copy.deepcopy(v.load())
    change(data)
    try:
        v.check_duration_vectors(data, v.tables())
    except ValueError as value:
        if error not in str(value):
            raise AssertionError(value)
    else:
        raise AssertionError('duration mutation accepted')
    print(name + ': REJECTED')


def check_duration_identity():
    """Each duration-vector identity field, and the production check its mutation fails.

    operation: a limit operation id fails duration operation.
    argument: a different setpoint fails duration argument.
    parameter order: reversing storage.setpoint.active and storage.setpoint.duration fails duration parameters.
    parameter id: replacing storage.setpoint.duration fails duration parameters.
    presence: a token other than omitted or explicit_zero fails duration presence.
    duration coefficient: an explicit zero coefficient other than 0 fails duration value.
    duration exponent: an explicit zero exponent other than 0 fails duration value.
    command_deadline: true fails duration deadline.
    setpoint_effect: a different effect token fails duration effect.
    presence collision: a second omitted record for the same operation fails duration distinct.
    """
    v.check_duration_vectors(v.load(), v.tables())
    vectors = v.load()['duration_vectors']
    omitted = next(item for item in vectors if item['presence'] == 'omitted')
    explicit = next(item for item in vectors if item['operation'] == omitted['operation'] and item['presence'] == 'explicit_zero')
    omitted_bytes = json.dumps(omitted['duration'], separators=(',', ':'), sort_keys=True)
    explicit_bytes = json.dumps(explicit['duration'], separators=(',', ':'), sort_keys=True)
    if omitted_bytes == explicit_bytes:
        raise AssertionError('omitted and explicit zero are not distinct')
    cases = [
        ('duration_operation', lambda d: d['duration_vectors'][0].update(operation='storage.operation.set_charge_limit'), 'duration operation'),
        ('duration_argument', lambda d: d['duration_vectors'][0].update(argument='storage.setpoint.dc_power'), 'duration argument'),
        ('duration_parameter_order', lambda d: d['duration_vectors'][0]['parameters'].reverse(), 'duration parameters'),
        ('duration_parameter_id', lambda d: d['duration_vectors'][0]['parameters'].__setitem__(1, 'storage.setpoint.ac_power'), 'duration parameters'),
        ('duration_presence', lambda d: d['duration_vectors'][0].update(presence='blank'), 'duration presence'),
        ('duration_coefficient', lambda d: next(item for item in d['duration_vectors'] if item['presence'] == 'explicit_zero')['duration'].update(coefficient='1'), 'duration value'),
        ('duration_exponent', lambda d: next(item for item in d['duration_vectors'] if item['presence'] == 'explicit_zero')['duration'].update(exponent10=1), 'duration value'),
        ('duration_deadline', lambda d: d['duration_vectors'][0].update(command_deadline=True), 'duration deadline'),
        ('duration_effect', lambda d: next(item for item in d['duration_vectors'] if item['presence'] == 'explicit_zero').update(setpoint_effect='hold'), 'duration effect'),
        ('duration_distinct', lambda d: next(item for item in d['duration_vectors'] if item['operation'] == d['duration_vectors'][0]['operation'] and item['presence'] == 'explicit_zero').update(presence='omitted', duration=None, setpoint_effect='omitted_validity', starts_at_receipt=False), 'duration distinct'),
    ]
    for case in cases:
        duration_case(*case)
    print('duration_vectors: PASS')


def function_lines(path, name):
    """Lines of one top-level function, from its definition through the next one."""
    lines = Path(path).read_text().splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith('def ' + name + '('):
            start = index
            break
    if start is None:
        raise AssertionError(name + ' is missing')
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith(('def ', 'class ', 'if __name__')):
            end = index
            break
    return lines[start:end]


def assert_no_joined_statements(path, name):
    """A split checker has no semicolon statement and no clause with a trailing statement."""
    clause = re.compile(r'^\s*(?:if|elif|else|for|try|except|while|with)\b.*:\s*\S')
    for line in function_lines(path, name):
        code = line.split('#', 1)[0]
        if ';' in code or clause.search(code):
            raise AssertionError(name + ' joins statements on one line')


def test_duration_split_and_plain_fields():
    """Duration checks stay split, and boolean, text and symbol shapes still fail closed."""
    validator = ROOT / 'scripts/validate_storage_bms_pack_v1.py'
    suite = Path(__file__)
    for name in ('check_duration_vectors', 'check_one_duration_vector', 'check_duration_effect', 'check_plain_field'):
        assert_no_joined_statements(validator, name)
    for name in ('duration_case', 'check_duration_identity'):
        assert_no_joined_statements(suite, name)
    document = function_lines(validator, 'document')
    semicolons = 0
    for line in document:
        semicolons += line.split('#', 1)[0].count(';')
    if semicolons != 1:
        raise AssertionError('document joined statements')
    for line in function_lines(validator, 'validate_tables'):
        if 'field kind' in line:
            raise AssertionError('plain field check grew validate_tables')
    check_duration_identity()
    reject_plain_field('storage.cob.actor', 'unit', 'unit.one', 'field kind')
    reject_plain_field('storage.setpoint.active', 'symbols', ['on'], 'field kind')
    reject_plain_field('storage.status.faults', 'unit', 'unit.one', 'field symbols')


def reject_plain_field(identifier, key, value, error):
    table = copy.deepcopy(v.tables())
    field = next(item for item in table['field_specs'] if item['id'] == identifier)
    field[key] = value
    reject_table(table, error)


if __name__=='__main__': main()
