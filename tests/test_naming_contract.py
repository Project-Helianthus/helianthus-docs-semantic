import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('naming_contract', ROOT / 'scripts/check_naming_contract.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def data():
    return json.loads((ROOT / 'architecture/naming-contract.json').read_text())

def test_contract():
    assert module.validate(data())

@pytest.mark.parametrize('field,value', [('source', 'semreg/v1/packs/pv/definitions.go'), ('kind', 'go_identifier'), ('historical_name', 'wrong'), ('canonical_name', 'wrong'), ('status', 'provisional'), ('question', 'unexpected')])
def test_proof_identity_mutations_rejected(field, value):
    item = data()
    row = next(r for r in item['rows'] if r['status'] == 'proven_rename')
    row[field] = value
    with pytest.raises(ValueError):
        module.validate(item)

def test_provisional_question_required():
    item = data()
    next(r for r in item['rows'] if r['status'] == 'provisional')['question'] = ''
    with pytest.raises(ValueError):
        module.validate(item)

def test_duplicate_identity_rejected():
    item = data()
    item['rows'].append(copy.deepcopy(item['rows'][0]))
    with pytest.raises(ValueError):
        module.validate(item)
