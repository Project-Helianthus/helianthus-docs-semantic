#!/usr/bin/env python3
"""Check bounded SemReg naming correspondence and contract references."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = {
    'thermal.measurement.humidity_relative': 'thermal.measurement.humidity',
    'thermal.setpoint.temperature': 'thermal.setpoint.temperature_setpoint',
    'thermal.setpoint.dhw_temperature': 'thermal.setpoint.dhw_temperature_setpoint',
}

def validate(data):
    rows = data['rows']
    expected_counts = dict(zip(('pv', 'storage', 'evse', 'thermal', 'infrastructure'), (61, 63, 52, 61, 57)))
    counts = Counter(r['source'].split('/')[3] for r in rows)
    if counts != expected_counts or any(r['kind'] not in ('definition_literal', 'go_identifier') for r in rows):
        raise ValueError('inventory coverage or kind differs')
    keys = [(r['source'], r['kind'], r['historical_name']) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate inventory identity')
    if {r['historical_name']: r['canonical_name'] for r in rows if r['status'] == 'proven_rename'} != MAP:
        raise ValueError('supported map differs')
    for row in rows:
        if row['status'] == 'proven_rename':
            if row['question'] is not None or row['kind'] != 'definition_literal' or row['source'] != 'semreg/v1/packs/thermal/definitions.go':
                raise ValueError('invalid proof row')
        elif row['status'] != 'provisional' or not row['question'] or row['canonical_name'] != row['historical_name']:
            raise ValueError('unresolved row changed or lacks question')
    if set(data['consumer_correspondence']) != set(MAP):
        raise ValueError('missing consumer correspondence')
    for old, new in MAP.items():
        if old == new:
            raise ValueError('invalid rename')
    return True

if __name__ == '__main__':
    validate(json.loads((ROOT / 'architecture/naming-contract.json').read_text()))
    print('naming contract valid')
