"""Offline publication checks; no SDK or production converter is exercised."""

import copy
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'api/v1/targets/matter-1.6.1-v1.json'
METADATA = ROOT / 'api/v1/pack-metadata-v1.json'
HISTORICAL = ROOT / 'api/v1/targets/matter-1.7-ballot-0.9-v1.json'
PACKS = {'evse': '1.0.0', 'infrastructure': '1.0.0', 'pv': '1.0.0',
         'storage': '1.1.0', 'thermal': '1.0.0'}
GUARDS = ['stale', 'unavailable', 'unqualified', 'conflicted', 'invalid',
          'revision_mismatch', 'nonrepresentable_value',
          'multiple_or_ambiguous_source_keys']
MODELS = [
    {'name': 'Electrical Sensor', 'device_type_id': 1296, 'revision': 1,
     'path': 'device/electrical_sensor_gen.go'},
    {'name': 'Power Topology', 'cluster_id': 156, 'revision': 1,
     'path': 'cluster/spec/powertopology/definition_gen.go'},
    {'name': 'Electrical Power Measurement', 'cluster_id': 144, 'revision': 3,
     'attribute_id': 5, 'attribute_name': 'ActiveCurrent',
     'path': 'cluster/spec/electricalpowermeasurement/definition_gen.go'},
]
VALUE = {
    'from_unit': 'unit.ampere', 'to_unit': 'amperage-mA',
    'conversion': {'algorithm': 'exact_multiply', 'factor': 1000,
                   'require_integral_result': True},
    'representation': {'kind': 'signed_integer', 'minimum': -(2**62),
                       'maximum': 2**62, 'nullable': True},
    'emission': {'value_must_be_non_null': True, 'eligible_source_keys': 1,
                 'required_dimension': 'evse.dimension.phase'},
    'on_nonrepresentable': 'whole_document_no_payload',
}
POSITIVE_REF = {'pack': {'id': 'helianthus.pack.evse', 'version': '1.0.0'},
                'id': 'evse.ac.current', 'version': '1.0.0'}


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def require(condition, label):
    if not condition:
        raise ValueError(label)


def positive(document):
    return next(row for row in document['rows'] if row['ref'] == POSITIVE_REF)


def items():
    result = []
    for pack in load(METADATA)['packs']:
        for group, kind in [('fields', 'fact'), ('capabilities', 'capability'),
                            ('operations', 'operation')]:
            result.extend((item, kind) for item in pack[group])
    return sorted(result, key=lambda pair: identity(pair[0]['ref']))


def identity(ref):
    return ref['pack']['id'], ref['pack']['version'], ref['id'], ref['version']


def check_model(d):
    require(d['contract'] == 'helianthus.gateway.matter-projection/v1', 'contract')
    require(d['status'] == 'adoption_projection_contract_pre_1_0', 'status')
    require(d['mapping_revision'] == 1, 'mapping revision')
    require(d['target'] == {'name': 'matter.data-model', 'version': '1.6.1'}, 'target')
    require(d['pins'] == {'packs': PACKS}, 'pack versions; no historical pins')
    require(d['model_source'] == {
        'repository': 'SukramJ/go-fabric', 'tag': 'v0.13.12',
        'report_title': 'go-fabric suitability for the Helianthus Matter binding',
        'inspection_grade': 'Proven',
        'inspection_basis': 'supplied graded report; upstream source not independently replayed here',
        'execution_grade': 'Unknown', 'standards_equivalence': 'Unknown',
        'models': MODELS}, 'graded model source')


def check_roster(d):
    expected = [(item['ref'], kind) for item, kind in items()]
    require([(r['ref'], r['kind']) for r in d['rows']] == expected, 'exact roster')
    require(Counter(r['kind'] for r in d['rows']) ==
            {'fact': 88, 'capability': 32, 'operation': 7}, 'roster counts')
    require(d['scope'] == {'projection_items': ['fact', 'capability', 'operation'],
                           'excluded': 'service'}, 'scope')


def check_dispositions(d):
    require([r['ref'] for r in d['rows'] if r['disposition'] != 'unknown'] ==
            [POSITIVE_REF], 'single positive')
    for row in d['rows']:
        if row['ref'] == POSITIVE_REF:
            require(row['kind'] == 'fact' and row['disposition'] == 'transformed'
                    and row['reason'] == 'matter.phase_endpoint_identity_loss.v1',
                    'positive identity')
        else:
            require(row['disposition'] == 'unknown' and
                    row['reason'] == 'matter.unmapped.v1' and
                    'target' not in row, 'unknown has no target or inferred mapping')


def check_source(d):
    for row, (item, kind) in zip(d['rows'], items()):
        ref = item['ref']
        keys = []
        if kind == 'fact':
            keys = [{'pack_id': ref['pack']['id'],
                     'pack_version': ref['pack']['version'], 'fact_id': ref['id'],
                     'dimensions': {'mode': 'exact_runtime_fact_key',
                                    'definition': item['dimension']}}]
        require(row['source'] == {
            'kernel_contract': 'helianthus.semantic.kernel/v1',
            'requested': {'kind': kind, 'item_id': ref['id'],
                          'item_version': ref['version']},
            'revision_binding': {'snapshot_id': 'exact_input_snapshot',
                                 'revisions': 'exact_input_revisions'},
            'fact_keys': keys}, 'exact source binding')


def check_target(d):
    target = positive(d)['target']
    require({k: v for k, v in target.items() if k != 'value'} ==
            {'device_type_id': 1296, 'cluster_id': 144, 'attribute_id': 5}, 'tuple')


def check_phase(d):
    require(positive(d)['target']['value']['emission'] == VALUE['emission'],
            'one non-null phase-qualified source')


def check_conversion(d):
    value = positive(d)['target']['value']
    require({k: v for k, v in value.items() if k != 'emission'} ==
            {k: v for k, v in VALUE.items() if k != 'emission'}, 'exact mA refusal')


def check_guards(d):
    require(d['input_guards'] == {
        'whole_document_no_payload': GUARDS,
        'rule': 'all guards and every transformed-value representability rule must pass before any target payload exists'},
        'whole-document guards')


def check_loss(d):
    for row in d['rows']:
        item = row['ref']['id']
        if row['ref'] == POSITIVE_REF:
            expected = [
                {'kind': 'unit', 'source_items': ['evse.ac.current'],
                 'description': 'amperes are represented as integral milliamperes only when exact and representable',
                 'reversible': False},
                {'kind': 'identity', 'source_items': ['evse.ac.current'],
                 'description': 'phase identity and endpoint association are irreversibly lost in the scalar target; no inverse phase or endpoint reconstruction is permitted',
                 'reversible': False}]
        else:
            expected = [{'kind': 'policy', 'source_items': [item],
                         'description': 'no target lookup, inferred fallback, authority, intent, route, or operation is created',
                         'reversible': False}]
        require(row['loss'] == expected, 'explicit irreversible loss')


CHECKS = [check_model, check_roster, check_dispositions, check_source,
          check_target, check_phase, check_conversion, check_guards, check_loss]


class Matter161TargetTests(unittest.TestCase):
    def setUp(self):
        self.document = load(LEDGER)

    def reject(self, checker, path, replacement):
        # The valid positive control passes the same independent checker first.
        checker(self.document)
        candidate = copy.deepcopy(self.document)
        node = candidate
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = replacement
        # Mutate only a disposable copy of the owned production descriptor.
        with tempfile.TemporaryDirectory(prefix='matter161-') as directory:
            mutant = Path(directory) / LEDGER.name
            mutant.write_text(json.dumps(candidate))
            with self.assertRaises(ValueError):
                checker(load(mutant))

    def positive_index(self):
        return next(i for i, r in enumerate(self.document['rows'])
                    if r['ref'] == POSITIVE_REF)

    def test_baseline_independent_checks(self):
        for checker in CHECKS:
            with self.subTest(check=checker.__name__):
                checker(self.document)

    def test_historical_accounting_preserved(self):
        historical = load(HISTORICAL)
        self.assertEqual(self.document['historical_input'], HISTORICAL.name)
        for old, new in zip(historical['rows'], self.document['rows']):
            expected = copy.deepcopy(new)
            if expected['ref'] == POSITIVE_REF:
                expected['loss'] = expected['loss'][:1]
            self.assertEqual(old, expected)
        self.assertEqual(self.document['ownership'], historical['ownership'])
        self.assertEqual(self.document['non_claims'], historical['non_claims'])

    def test_model_version_and_revision_mutants(self):
        cases = [(('target', 'version'), '1.7')]
        cases += [(('model_source', 'models', i, 'revision'), revision)
                  for i, revision in enumerate([2, 2, 4])]
        for path, value in cases:
            with self.subTest(axis=path):
                self.reject(check_model, path, value)

    def test_second_positive_mutant(self):
        self.reject(check_dispositions, ('rows', 0, 'disposition'), 'transformed')

    def test_missing_requested_item_each_pack_mutants(self):
        for pack in PACKS:
            rows = copy.deepcopy(self.document['rows'])
            index = next(i for i, r in enumerate(rows)
                         if r['ref']['pack']['id'] == 'helianthus.pack.' + pack)
            del rows[index]
            with self.subTest(pack=pack):
                self.reject(check_roster, ('rows',), rows)

    def test_row_identity_axes_mutants(self):
        # Valid sibling components, one axis changed, every other field valid.
        i = self.positive_index()
        cases = [(('ref', 'pack', 'id'), 'helianthus.pack.pv'),
                 (('ref', 'pack', 'version'), '1.1.0'),
                 (('kind',), 'capability'),
                 (('ref', 'id'), 'evse.ac.voltage'),
                 (('ref', 'version'), '1.1.0')]
        for path, value in cases:
            with self.subTest(axis=path):
                self.reject(check_roster, ('rows', i) + path, value)

    def test_fact_identity_and_dimension_axes_mutants(self):
        i = self.positive_index()
        prefix = ('rows', i, 'source', 'fact_keys', 0)
        cases = [(('pack_id',), 'helianthus.pack.pv'),
                 (('pack_version',), '1.1.0'),
                 (('fact_id',), 'evse.ac.voltage'),
                 (('dimensions', 'definition', 'pack', 'id'), 'helianthus.pack.pv'),
                 (('dimensions', 'definition', 'pack', 'version'), '1.1.0'),
                 (('dimensions', 'definition', 'id'), 'evse.dimension.evse'),
                 (('dimensions', 'definition', 'version'), '1.1.0')]
        for path, value in cases:
            with self.subTest(axis=path):
                self.reject(check_source, prefix + path, value)
        self.reject(check_source, prefix + ('dimensions', 'mode'), 'inferred')

    def test_request_and_revision_axes_mutants(self):
        prefix = ('rows', self.positive_index(), 'source')
        cases = [(('requested', 'kind'), 'capability'),
                 (('requested', 'item_id'), 'evse.ac.voltage'),
                 (('requested', 'item_version'), '1.1.0'),
                 (('revision_binding', 'snapshot_id'), 'other_input_snapshot'),
                 (('revision_binding', 'revisions'), 'other_input_revisions')]
        for path, value in cases:
            with self.subTest(axis=path):
                self.reject(check_source, prefix + path, value)

    def test_target_identity_axes_mutants(self):
        # Valid sibling device, cluster and attribute identifiers, not sentinels.
        prefix = ('rows', self.positive_index(), 'target')
        for axis, value in [('device_type_id', 14), ('cluster_id', 156),
                            ('attribute_id', 4)]:
            with self.subTest(axis=axis):
                self.reject(check_target, prefix + (axis,), value)

    def test_phase_restriction_mutants(self):
        prefix = ('rows', self.positive_index(), 'target', 'value', 'emission')
        for axis, value in [('required_dimension', 'evse.dimension.evse'),
                            ('eligible_source_keys', 2),
                            ('value_must_be_non_null', False)]:
            with self.subTest(axis=axis):
                self.reject(check_phase, prefix + (axis,), value)
        self.reject(check_phase, prefix, {})

    def test_fractional_rounding_range_and_refusal_mutants(self):
        prefix = ('rows', self.positive_index(), 'target', 'value')
        cases = [(('conversion', 'algorithm'), 'round'),
                 (('conversion', 'require_integral_result'), False),
                 (('conversion', 'factor'), 1),
                 (('representation', 'minimum'), 0),
                 (('representation', 'maximum'), 2**63 - 1),
                 (('representation', 'nullable'), False),
                 (('on_nonrepresentable',), 'partial_payload')]
        for path, value in cases:
            with self.subTest(axis=path):
                self.reject(check_conversion, prefix + path, value)

    def test_whole_document_guard_mutants(self):
        for guard in GUARDS:
            with self.subTest(guard=guard):
                self.reject(check_guards, ('input_guards', 'whole_document_no_payload'),
                            [g for g in GUARDS if g != guard])

    def test_loss_erasure_mutants(self):
        i = self.positive_index()
        self.reject(check_loss, ('rows', i, 'loss'), [])
        self.reject(check_loss, ('rows', i, 'loss'), self.document['rows'][i]['loss'][:1])
        self.reject(check_loss, ('rows', i, 'loss', 1, 'reversible'), True)
        self.reject(check_loss, ('rows', 0, 'loss'), [])

    def test_every_other_item_stays_unknown_mutants(self):
        for i, row in enumerate(self.document['rows']):
            if row['ref'] == POSITIVE_REF:
                continue
            with self.subTest(item=row['ref']['id'], kind=row['kind']):
                self.reject(check_dispositions, ('rows', i, 'disposition'), 'exact')

    def test_exact_arithmetic_examples_are_spec_oracles_only(self):
        # Independent rational arithmetic illustrates the contract, not runtime code.
        check_conversion(self.document)
        for amperes, expected in [('1.234', 1234), ('-1.234', -1234), ('0', 0),
                                  ('4611686018427387.904', 2**62),
                                  ('-4611686018427387.904', -(2**62)),
                                  ('0.0001', None),
                                  ('4611686018427387.905', None),
                                  ('-4611686018427387.905', None)]:
            with self.subTest(amperes=amperes):
                exact = Fraction(amperes) * 1000
                result = (int(exact) if exact.denominator == 1 and
                          -(2**62) <= exact <= 2**62 else None)
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
