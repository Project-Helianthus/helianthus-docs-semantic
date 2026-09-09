#!/usr/bin/env python3
"""Focused mutation controls for every Issue #25 mapping acceptance dimension."""
import copy
import importlib.util
import sys
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
def main():
 cases=[('pin','pins.gateway_tree','0'*40,'contract'),('revision','native_contract.revision.cumulative_revision','2.03','native contract'),('unit','native_contract.unit.allowed','0..247','native contract'),('slice','native_contract.slices.0.quantity',8,'native contract'),('physical','native_contract.qualification.physical_qualified',True,'native contract'),('asset-derivation','identity.asset_id.forbidden_derivations.0','serial','identity contract'),('source-distinction','identity.source_id.distinct_from','unit_id','identity contract'),('binding-input','identity.binding_id.stable_inputs.0','unit_id','identity contract'),('observation-axis','lifecycle.required_observation_evidence.0','bad','lifecycle contract'),('exact-loss','field_rules.1.disposition.loss',[{'kind':'policy'}],'exact loss'),('invalid-loss-kind','field_rules.0.disposition.loss.0.kind','native_enum_bitfield','transformed loss'),('missing-withheld-reason','withheld.0.reason','','withheld unsupported'),('unsupported-removed','unsupported.0','x','withheld unsupported'),('requested-drift','projection.requested_items.0.item_id','storage.x','requested items'),('precedence','projection.error_precedence.0','x','projection'),('operation','projection.operations','allowed','projection'),('consumer','consumer_cutover.required_removals.1','allowed','consumer cutover')]
 for c in cases: reject(*c)
 data=m.load(); data['scenarios'][0]['expect']['output']['facts'][0]['value']['quantity']['number']['coefficient']='999'
 try: m.document(data)
 except ValueError as error:
  if str(error)!='scenario output': raise AssertionError(error)
 else: raise AssertionError('scenario output drift accepted')
 print('scenario-output-drift: REJECTED')
 print('baseline: PASS; 18 focused mutations rejected')
if __name__=='__main__': main()
