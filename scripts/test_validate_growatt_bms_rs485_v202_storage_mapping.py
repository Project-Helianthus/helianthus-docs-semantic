#!/usr/bin/env python3
"""Focused mutation controls for every Issue #25 mapping acceptance dimension."""
import copy
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('m',ROOT/'scripts/validate_growatt_bms_rs485_v202_storage_mapping.py')
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
def reject(name,path,value,error):
 d=copy.deepcopy(m.load()); m.mutate(d,{'path':path,'value':value})
 try: m.validate_contract(d)
 except ValueError as e:
  if error not in str(e): raise AssertionError(e)
 else: raise AssertionError(name+' accepted')
 print(name+': REJECTED')
ONE,ZERO={'coefficient':'1','exponent10':0},{'coefficient':'0','exponent10':0}
# (native unit, canonical SI unit) -> exact factor and offset; the SI value is native x factor + offset.
CONVERSIONS={('%','unit.ratio'):{'factor':{'coefficient':'1','exponent10':-2},'offset':ZERO},('V','unit.volt'):{'factor':ONE,'offset':ZERO},('A','unit.ampere'):{'factor':ONE,'offset':ZERO},('degC','unit.kelvin'):{'factor':ONE,'offset':{'coefficient':'27315','exponent10':-2}},('Ah','unit.ampere_hour'):{'factor':ONE,'offset':ZERO}}
# Rule index by target, so that a mutation names the rule it varies.
RULE={rule['target']:index for index,rule in enumerate(m.load()['field_rules'])}
def fraction_of(number):
    return Fraction(int(number['coefficient'])) * Fraction(10) ** number['exponent10']


def kernel(value):
    """Exact kernel Decimal of a terminating Fraction, computed independently of the validator."""
    exponent = 0
    while value.denominator != 1:
        value *= 10
        exponent -= 1
    coefficient = value.numerator
    if coefficient == 0:
        return dict(ZERO)
    while coefficient % 10 == 0:
        coefficient //= 10
        exponent += 1
    return {'coefficient': str(coefficient), 'exponent10': exponent}


def reject_change(name, change, error):
    document = copy.deepcopy(m.load())
    change(document)
    try:
        m.validate_contract(document)
    except ValueError as e:
        if error not in str(e):
            raise AssertionError(name + ': ' + str(e)) from e
    else:
        raise AssertionError(name + ' accepted')
    print(name + ': REJECTED')


def check_rule_conversions(contract):
    """Each quantity rule names its pack field's SI unit and the exact conversion of its unit pair, with a unit loss exactly when that is not the identity."""
    if m.UNIT_CONVERSION != CONVERSIONS or hasattr(m, 'UNIT_SHIFT'):
        raise AssertionError('conversion table differs from the unit rule')
    fields = m.pack_fields()
    for rule in contract['field_rules']:
        if 'unit' not in rule:
            continue
        if rule['unit'] != fields[rule['target']]['unit'] or rule['conversion'] != CONVERSIONS[(rule['native_unit'], rule['unit'])]:
            raise AssertionError(rule['target'] + ' does not state its SI conversion')
        identity = rule['conversion'] == {'factor': ONE, 'offset': ZERO}
        if identity == ('unit' in [loss['kind'] for loss in rule['disposition']['loss']]):
            raise AssertionError(rule['target'] + ' unit loss')
    units = {rule['target']: rule['unit'] for rule in contract['field_rules'] if 'unit' in rule}
    if units['storage.state.soc'] != 'unit.ratio' or units['storage.temperature.pack'] != 'unit.kelvin':
        raise AssertionError('state of charge and temperature are not in SI units')
    if {units['storage.capacity.charge'], units['storage.capacity.discharge']} != {'unit.ampere_hour'}:
        raise AssertionError('both capacities stay in ampere-hours')


def check_published_values(contract):
    """The published value is the native value through the exact factor and offset, computed here with fractions."""
    typed = contract['scenarios'][0]['observation']['typed']
    outputs = [scenario['expect']['output'] for scenario in contract['scenarios'] if 'output' in scenario.get('expect', {})]
    for fact in [fact for output in outputs for fact in output['facts']]:
        rule = contract['field_rules'][RULE[fact['key']['fact_id']]]
        if 'unit' not in rule:
            continue
        native = Fraction(str(typed[rule['source']]))
        expected = kernel(native * fraction_of(rule['conversion']['factor']) + fraction_of(rule['conversion']['offset']))
        if fact['value']['quantity'] != {'number': expected, 'unit': rule['unit']}:
            raise AssertionError(rule['target'] + ' published value')
    if kernel(Fraction(75, 100)) != {'coefficient': '75', 'exponent10': -2} or kernel(Fraction(25) + Fraction(27315, 100)) != {'coefficient': '29815', 'exponent10': -2}:
        raise AssertionError('worked values')


def check_si_conversions():
    contract = m.load()
    check_rule_conversions(contract)
    check_published_values(contract)
    print('si-conversions-and-published-values: PASS')


def main():
 check_si_conversions()
 soc,temperature,voltage,charge=RULE['storage.state.soc'],RULE['storage.temperature.pack'],RULE['storage.pack.voltage'],RULE['storage.capacity.charge']
 conversion_cases=[
  # Key field native unit: a native unit with no entry for the canonical unit.
  ('native-unit-soc',lambda d:d['field_rules'][soc].update(native_unit='ratio'),'unit conversion'),
  ('native-unit-temperature',lambda d:d['field_rules'][temperature].update(native_unit='K'),'unit conversion'),
  ('native-unit-capacity-energy',lambda d:d['field_rules'][charge].update(native_unit='kWh'),'unit conversion'),
  ('native-unit-missing',lambda d:d['field_rules'][voltage].pop('native_unit'),'unit conversion'),
  # Key field canonical unit: a customary unit, or an SI unit other than the pack field's.
  ('canonical-unit-percent',lambda d:d['field_rules'][soc].update(unit='unit.percent'),'unit conversion'),
  ('canonical-unit-celsius',lambda d:d['field_rules'][temperature].update(unit='unit.celsius'),'unit conversion'),
  ('canonical-unit-capacity-joule',lambda d:d['field_rules'][charge].update(unit='unit.joule'),'unit conversion'),
  ('canonical-unit-other-si',lambda d:d['field_rules'][voltage].update(unit='unit.ampere'),'unit conversion'),
  # Value field factor: coefficient and exponent each varied.
  ('factor-coefficient',lambda d:d['field_rules'][soc]['conversion'].update(factor={'coefficient':'2','exponent10':-2}),'unit conversion'),
  ('factor-exponent',lambda d:d['field_rules'][soc]['conversion'].update(factor={'coefficient':'1','exponent10':-1}),'unit conversion'),
  ('factor-identity-dropped',lambda d:d['field_rules'][voltage]['conversion'].update(factor={'coefficient':'1','exponent10':-3}),'unit conversion'),
  # Value field offset: coefficient and exponent each varied.
  ('offset-coefficient',lambda d:d['field_rules'][temperature]['conversion'].update(offset={'coefficient':'273','exponent10':0}),'unit conversion'),
  ('offset-exponent',lambda d:d['field_rules'][temperature]['conversion'].update(offset={'coefficient':'27315','exponent10':-3}),'unit conversion'),
  ('offset-on-ratio',lambda d:d['field_rules'][soc]['conversion'].update(offset={'coefficient':'27315','exponent10':-2}),'unit conversion'),
  ('conversion-missing',lambda d:d['field_rules'][charge].pop('conversion'),'unit conversion'),
  ('conversion-extra-member',lambda d:d['field_rules'][soc]['conversion'].update(rounding='half_even'),'unit conversion'),
  ('rule-extra-member',lambda d:d['field_rules'][soc].update(scale=-2),'unit conversion'),
  ('symbol-rule-with-unit',lambda d:d['field_rules'][RULE['storage.status.operating']].update(unit='unit.ratio'),'unit conversion'),
  # Loss: a conversion that is not the identity declares a unit loss, and the identity declares none.
  ('silent-ratio-conversion',lambda d:d['field_rules'][soc].update(disposition={'outcome':'exact','loss':[]}),'silent unit conversion'),
  ('silent-kelvin-conversion',lambda d:d['field_rules'][temperature]['disposition']['loss'][0].update(kind='provenance'),'silent unit conversion'),
  ('identity-with-unit-loss',lambda d:d['field_rules'][RULE['storage.pack.current']]['disposition']['loss'][0].update(kind='unit'),'silent unit conversion'),
 ]
 for c in conversion_cases:
  reject_change(*c)
 cases=[('pin','pins.gateway_tree','0'*40,'contract'),('revision','native_contract.revision.cumulative_revision','2.03','native contract'),('unit','native_contract.unit.allowed','0..247','native contract'),('slice','native_contract.slices.0.quantity',8,'native contract'),('physical','native_contract.qualification.physical_qualified',True,'native contract'),('asset-derivation','identity.asset_id.forbidden_derivations.0','serial','identity contract'),('source-distinction','identity.source_id.distinct_from','unit_id','identity contract'),('binding-input','identity.binding_id.stable_inputs.0','unit_id','identity contract'),('observation-axis','lifecycle.required_observation_evidence.0','bad','lifecycle contract'),('exact-loss','field_rules.2.disposition.loss',[{'kind':'policy'}],'exact loss'),('invalid-loss-kind','field_rules.0.disposition.loss.0.kind','native_enum_bitfield','transformed loss'),('missing-withheld-reason','withheld.0.reason','','withheld unsupported'),('unsupported-removed','unsupported.0','x','withheld unsupported'),('requested-drift','projection.requested_items.0.item_id','storage.x','requested items'),('precedence','projection.error_precedence.0','x','projection'),('operation','projection.operations','allowed','projection'),('consumer','consumer_cutover.required_removals.1','allowed','consumer cutover')]
 for c in cases: reject(*c)
 data=m.load(); data['scenarios'][0]['expect']['output']['facts'][0]['value']['quantity']['number']['coefficient']='999'
 try: m.document(data)
 except ValueError as error:
  if str(error)!='scenario output': raise AssertionError(error)
 else: raise AssertionError('scenario output drift accepted')
 print('scenario-output-drift: REJECTED')
 print('baseline: PASS; %d focused mutations rejected'%(len(cases)+1+len(conversion_cases)))
if __name__=='__main__': main()
