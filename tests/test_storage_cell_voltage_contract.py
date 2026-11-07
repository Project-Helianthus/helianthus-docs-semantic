"""Finite candidate document agreement; no runtime implementation or bus access."""
import copy
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / 'api/v1/packs'


def load(name):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate key: ' + key)
            result[key] = value
        return result
    return json.loads((PACKS / name).read_text(), object_pairs_hook=unique,
                      parse_float=lambda _: (_ for _ in ()).throw(ValueError('float')))


def decimal_mv(mv):
    value = Decimal(mv) / Decimal(1000)
    if not value:
        return {'coefficient': '0', 'exponent10': 0}
    sign, digits, exponent = value.normalize().as_tuple()
    return {'coefficient': ('-' if sign else '') + ''.join(map(str, digits)),
            'exponent10': exponent}


def document_example(f, table):
    """Evaluate only the declared finite example predicates, never publish facts."""
    context = f['context']
    capacity = table['coverage']['addressable_slots']
    count = f['configured_count']
    values = []
    losses = []
    for channel in f['channels']:
        n = channel['native']
        index = channel['index']
        reasons = []
        if f['source_kind'] != 'individual' or not f['selected_measurement'] or not channel['measurement_gate']:
            reasons.append('unsupported_selector')
        if not f['topology_explicit'] or not channel['associated']:
            reasons.append('topology')
        if f['requires_sensor_location'] and not channel['sensor_location_proven']:
            reasons.append('topology')
        if index not in capacity or index not in f['addressable_slots']:
            reasons.append('topology')
        if type(count) is int and count > 0 and index > count:
            reasons.append('partial_coverage')
        expected_dimensions = {key: context[key] for key in table['field']['dimensions']
                               if key != 'cell'}
        expected_dimensions['cell'] = index
        if channel['dimensions'] != expected_dimensions:
            reasons.append('identity_or_generation')
        if any(n[key] != context[key] for key in
               ('interface', 'source_epoch', 'driver_generation')):
            reasons.append('identity_or_generation')
        if channel['state'] != 'valid':
            reasons.append(channel['state'])
        if n['field_age_ms'] > table['policy']['max_age_ms']:
            reasons.append('stale')
        blocks = table['native_facts'][0]['blocks']
        selected = next((b for b in blocks if b['selector'] == channel['block']), None)
        if selected is None or index not in selected['cells'] or channel['word'] != (index - 1) % 4:
            reasons.append('unsupported_selector')
        if n['grade'] not in ('Proven', 'Hypothesis'):
            reasons.append('unqualified')
        if not reasons:
            values.append({'index': index, 'value': decimal_mv(channel['mv']),
                           'dimensions': copy.deepcopy(channel['dimensions']),
                           'native': copy.deepcopy(n)})
        losses.extend(reasons)
    received = sorted({c['index'] for c in f['channels'] if c['index'] in capacity})
    valid = sorted(v['index'] for v in values)
    times = [c['native']['monotonic_ms'] for c in f['channels']]
    span = ({'minimum': min(times), 'maximum': max(times),
             'width': max(times) - min(times)} if times else None)
    complete = (type(count) is int and 1 <= count <= len(capacity)
                and set(range(1, count + 1)) <= set(valid)
                and span is not None and span['width'] <= table['policy']['max_span_ms'])
    if not complete:
        losses.append('partial_coverage')
    if span and span['width'] > table['policy']['max_span_ms']:
        losses.append('time_span')
    return {'values': values, 'coverage': {'configured_count': count,
            'addressable_slots': f['addressable_slots'], 'received_indices': received,
            'valid_indices': valid, 'vector_span': span}, 'complete': complete,
            'retained_raw': copy.deepcopy(f['channels']),
            'last_known_good': copy.deepcopy(f['last_known_good']),
            'withheld_indices': [c['index'] for c in f['channels'] if c['index'] not in valid],
            'losses': sorted(set(losses))}


class CandidateCellVoltage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = load('storage-bms-cell-voltage-contract.json')
        cls.data = load('storage-bms-cell-voltage-vectors.json')
        cls.rows = {row['id']: row for row in cls.data['vectors']}
        cls.doc = (PACKS / 'storage-bms-cell-voltage-v1.md').read_text()

    def test_candidate_shape_and_accepted_separation(self):
        t = self.table
        self.assertEqual(t['status'], 'candidate')
        self.assertEqual(t['proposed_pack_version'], '1.2.0')
        self.assertEqual(t['accepted_pack_version'], '1.1.0')
        self.assertFalse(t['typed_runtime_input'])
        self.assertFalse(t['physical_qualified'])
        self.assertTrue(t['receive_only'])
        self.assertEqual(t['field'], {
            'id': 'storage.measurement.cell_voltage', 'kind': 'quantity',
            'unit': 'unit.volt', 'optional': True,
            'dimensions': ['system', 'battery', 'pack', 'module', 'cell', 'interface'],
            'bounds': {'minimum': {'coefficient': '0', 'exponent10': 0}, 'maximum': None},
            'conversion': 'Decimal(mV) / Decimal(1000)'})
        self.assertEqual(t['coverage']['tuple'], ['configured_count', 'addressable_slots',
                         'received_indices', 'valid_indices', 'vector_span'])
        self.assertEqual(t['coverage']['addressable_slots'], list(range(1, 17)))
        accepted = load('storage-bms-contract-tables.json')
        self.assertEqual(accepted['definition_index']['pack']['version'], '1.1.0')
        self.assertNotIn(t['field']['id'], [f['id'] for f in accepted['field_specs']])
        self.assertIn('storage.temperature.cell', [f['id'] for f in accepted['field_specs']])
        for text in ['1.2.0', 'candidate', t['field']['id'], 'receive-only',
                     'physical_qualified=false', 'GraphQL', 'MCP', 'unbounded']:
            self.assertIn(text, self.doc)

    def test_explicit_schema_and_raw_word_agreement(self):
        self.assertEqual(len(self.rows), len(self.data['vectors']))
        self.assertGreaterEqual(len(self.rows), 40)
        self.assertEqual(self.data['contract'], self.table['contract'])
        self.assertFalse(self.data['physical_qualified'])
        for row in self.rows.values():
            with self.subTest(vector=row['id']):
                f = row['input']
                self.assertFalse(f['physical_qualified'])
                self.assertTrue(f['channels'])
                self.assertIs(type(f['selected_measurement']), bool)
                for c in f['channels']:
                    self.assertEqual(set(c), set(self.table['schema']['channel_required']))
                    n = c['native']
                    self.assertIs(type(c['measurement_gate']), bool)
                    self.assertEqual(set(n), set(self.table['schema']['native_required']))
                    self.assertEqual(set(c['dimensions']), set(self.table['field']['dimensions']))
                    self.assertRegex(n['payload'], r'^[0-9a-f]{16}$')
                    self.assertIs(type(n['ide']), bool)
                    for key in ['dlc', 'raw_dlc', 'slot', 'driver_generation', 'sequence',
                                'monotonic_ms', 'field_age_ms']:
                        self.assertIs(type(n[key]), int)
                        self.assertGreaterEqual(n[key], 0)
                    self.assertIn(n['grade'], ['Proven', 'Hypothesis', 'Unknown'])
                    self.assertIn(c['state'], self.table['schema']['states'])
                    raw = bytes.fromhex(n['payload'])
                    self.assertEqual(int.from_bytes(raw[2*c['word']:2*c['word']+2], 'little'), c['mv'])
                    self.assertGreaterEqual(c['mv'], 0)

    def test_all_declared_examples(self):
        for name, row in self.rows.items():
            with self.subTest(vector=name):
                f = copy.deepcopy(row['input'])
                before = copy.deepcopy(f)
                result = document_example(f, self.table)
                expected = row['expected']
                self.assertEqual(result['coverage']['received_indices'], expected['received_indices'])
                self.assertEqual(result['coverage']['valid_indices'], expected['valid_indices'])
                self.assertEqual(result['coverage']['vector_span'], expected['vector_span'])
                self.assertEqual(result['complete'], expected['complete'])
                self.assertEqual({str(v['index']): v['value'] for v in result['values']}, expected['values'])
                self.assertEqual(result['retained_raw'], before['channels'])
                self.assertEqual(result['last_known_good'], before['last_known_good'])
                self.assertEqual(f, before)
                self.assertEqual(set(result), set(self.table['schema']['result_required']))
                self.assertEqual(set(result['coverage']), set(self.table['schema']['coverage_required']))
                for v in result['values']:
                    self.assertEqual(set(v), set(self.table['schema']['accepted_value_required']))
                    original = next(c for c in f['channels'] if c['index'] == v['index'])
                    self.assertEqual(v['native'], original['native'])
                    self.assertEqual(v['dimensions'], original['dimensions'])
                    self.assertRegex(v['value']['coefficient'], r'^(0|-?[1-9][0-9]*)$')
                    self.assertFalse(v['value']['coefficient'] != '0' and v['value']['coefficient'].endswith('0'))

    def test_hypotheses_have_independent_fixed_payload_counterexamples(self):
        negative = {'H-pcs': 'pcs-extrema', 'H-count': 'missing-count',
                    'H-slots': 'slot-capacity-missing', 'H-received': 'received-invalid',
                    'H-valid': 'valid-partial', 'H-age': 'other-channel-refresh',
                    'H-span': 'span-after-boundary', 'H-sensor': 'no-sensor-association',
                    'H-topology': 'no-explicit-topology'}
        self.assertEqual({h['id'] for h in self.table['hypotheses']}, set(negative))
        base = self.rows['valid-4']['input']
        for hypothesis, name in negative.items():
            with self.subTest(hypothesis=hypothesis):
                self.assertIn(name, self.doc)
                row = self.rows[name]
                self.assertEqual(row['hypothesis'], hypothesis)
                self.assertFalse(row['expected']['complete'])
                for c in row['input']['channels']:
                    self.assertEqual(c['native']['payload'], base['channels'][c['index']-1]['native']['payload'])
                result = document_example(row['input'], self.table)
                self.assertTrue(result['losses'])
                self.assertEqual(result['retained_raw'], row['input']['channels'])

    def test_all_gate_pairs_retain_payload(self):
        for name, row in self.rows.items():
            if name.startswith('valid-') or name == 'zero-voltage':
                continue
            base = self.rows['zero-voltage' if name == 'zero-unavailable' else
                             'valid-16' if name in ('count-seventeen', 'missing-block', 'stale-block', 'unsupported-own-block-gate')
                             else 'valid-4']['input']
            with self.subTest(vector=name):
                for c in row['input']['channels']:
                    # Word position, rather than intentionally invalid semantic index,
                    # identifies the unchanged raw block in scope counterexamples.
                    original = next(b for b in base['channels']
                                    if b['word'] == c['word'])
                    self.assertEqual(c['native']['payload'], original['native']['payload'])

    def test_identity_fields_and_sibling_preservation(self):
        # Each dimension catches dropping that dimension from identity comparison.
        # Epoch/generation catch omission of their fence; native interface catches aliasing.
        names = ['wrong-' + key for key in self.table['field']['dimensions']]
        names += ['changed-source_epoch', 'changed-driver_generation', 'native-interface-change']
        for name in names:
            with self.subTest(field=name):
                result = document_example(self.rows[name]['input'], self.table)
                self.assertEqual(result['coverage']['valid_indices'], [2, 3, 4])
                self.assertIn('identity_or_generation', result['losses'])
                self.assertFalse(result['complete'])
                self.assertEqual(result['last_known_good']['state'], 'retained_non_actionable')

    def test_numeric_boundary_pairs_and_zero(self):
        for name in ['valid-1', 'valid-4', 'valid-16', 'span-at-boundary', 'zero-voltage']:
            self.assertTrue(self.rows[name]['expected']['complete'], name)
        for name in ['missing-count', 'count-zero', 'count-seventeen', 'span-after-boundary',
                     'cell-index-0', 'cell-index-17', 'zero-unavailable']:
            self.assertFalse(self.rows[name]['expected']['complete'], name)
        self.assertIn(1, self.rows['age-at-boundary']['expected']['valid_indices'])
        self.assertNotIn(1, self.rows['age-after-boundary']['expected']['valid_indices'])
        self.assertEqual(self.rows['zero-voltage']['expected']['values']['1'],
                         {'coefficient': '0', 'exponent10': 0})
        self.assertNotIn('1', self.rows['zero-unavailable']['expected']['values'])
        self.assertEqual(self.rows['zero-voltage']['input']['channels'][0]['native']['payload'],
                         self.rows['zero-unavailable']['input']['channels'][0]['native']['payload'])
        self.assertEqual(self.rows['span-after-boundary']['expected']['valid_indices'], [1, 2, 3, 4])

    def test_selected_gate_is_per_block(self):
        result = document_example(self.rows['unsupported-own-block-gate']['input'], self.table)
        self.assertEqual(result['coverage']['received_indices'], list(range(1, 17)))
        self.assertEqual(result['coverage']['valid_indices'], list(range(1, 13)))
        self.assertFalse(result['complete'])
        self.assertIn('unsupported_selector', result['losses'])

    def test_native_facts_and_references(self):
        self.assertEqual(self.table['native_facts'][0]['blocks'], [
            {'selector': str(1810+i), 'cells': list(range(4*i+1, 4*i+5))} for i in range(4)])
        self.assertEqual(self.table['native_facts'][1]['selector'], '1830')
        self.assertIn('FFFF invalid', self.table['native_facts'][1]['encoding'])
        self.assertEqual(len(self.table['references']), 2)
        for reference in self.table['references']:
            repository, path = reference['page'].split('/', 1)
            self.assertIn(repository + '/blob/main/' + path, self.doc)
            for section in reference['sections']:
                self.assertIn(section, self.doc)
        self.assertNotRegex(self.doc, r'\b[0-9a-f]{40,64}\b')


if __name__ == '__main__':
    unittest.main()
