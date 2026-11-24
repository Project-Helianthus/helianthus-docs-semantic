"""Offline publication checks; no SDK or production converter is exercised."""

import copy
import json
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'api/v1/targets/matter-1.6.1-v1.json'
CATALOG = ROOT / 'api/v1/element-catalog-v1.json'
HISTORICAL = ROOT / 'api/v1/targets/matter-1.7-ballot-0.9-v1.json'
KINDS = ['fact', 'capability', 'operation', 'service', 'relation']
GUARDS = ['stale', 'unavailable', 'conflicted', 'invalid',
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
POSITIVE_REASON = 'matter.phase_association_by_relation.v1'
HISTORICAL_POSITIVE_REASON = 'matter.phase_endpoint_identity_loss.v1'
UNMAPPED = ('unknown', 'matter.unmapped.v1', 'policy',
            'no target lookup, inferred fallback, authority, intent, route, or operation is created')
SERVICE = ('unsupported', 'matter.service_not_requested_item.v1', 'identity',
           'a service is not a kernel-v1 requested item; its subject has no allocated endpoint in this target and no endpoint correspondence is inferred')
TOPOLOGY = ('withheld', 'matter.power_topology_endpoint_unallocated.v1', 'identity',
            'the association needs allocated endpoints on the power topology construct; this target allocates none, so no association is emitted and no endpoint correspondence is inferred')
NOT_ADOPTED = ('unknown', 'matter.relation_construct_not_adopted.v1', 'identity',
               'the target construct for this relation type is outside the adopted model identities; no association is emitted and no endpoint composition is inferred')
TOPOLOGY_CONSTRUCT = {'cluster_id': 156, 'equivalence': 'Hypothesis'}
SCOPE = {'projection_items': KINDS,
         'derived_from': 'api/v1/element-catalog-v1.json',
         'not_requested': 'core-owned elements, dimensions, effect rules and presentations'}


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


def pack_ref(ref):
    # Catalog refs carry an owner; roster refs keep the pack-index shape.
    return {'pack': ref['owner']['pack'], 'id': ref['id'], 'version': ref['version']}


def identity(ref):
    return ref['pack']['id'], ref['pack']['version'], ref['id'], ref['version']


def items():
    result = [(element, element['element_kind'])
              for element in load(CATALOG)['elements']
              if element['ref']['owner']['kind'] == 'pack'
              and element['element_kind'] in KINDS]
    return sorted(result, key=lambda pair: identity(pack_ref(pair[0]['ref'])))


def packs():
    return {ref['pack']['id'].removeprefix('helianthus.pack.'): ref['pack']['version']
            for ref in (pack_ref(element['ref']) for element, _ in items())}


def positive(document):
    return next(row for row in document['rows'] if row['ref'] == POSITIVE_REF)


def phase_relation():
    # The catalog relation whose far endpoint is the positive row's phase key.
    matches = [element for element, kind in items() if kind == 'relation'
               and element['ref']['owner']['pack'] == POSITIVE_REF['pack']
               and element['attributes']['endpoint_dimensions']['to']['id']
               == VALUE['emission']['required_dimension']]
    require(len(matches) == 1, 'one phase association relation')
    return pack_ref(matches[0]['ref'])


def rule(element, kind):
    if kind == 'service':
        return SERVICE
    if kind == 'relation':
        attributes = element['attributes']
        electrical = (attributes['core_type'] == 'measures' or
                      (attributes['core_type'] == 'supplies' and
                       attributes.get('medium') == 'electrical'))
        return TOPOLOGY if electrical else NOT_ADOPTED
    return UNMAPPED


def check_model(d):
    require(d['contract'] == 'helianthus.gateway.matter-projection/v1', 'contract')
    require(d['status'] == 'adoption_projection_contract_pre_1_0', 'status')
    require(d['mapping_revision'] == 1, 'mapping revision')
    require(d['target'] == {'name': 'matter.data-model', 'version': '1.6.1'}, 'target')
    require(d['pins'] == {'packs': packs()}, 'catalog pack versions; no historical pins')
    require(d['model_source'] == {
        'repository': 'SukramJ/go-fabric', 'tag': 'v0.13.12',
        'report_title': 'go-fabric suitability for the Helianthus Matter binding',
        'inspection_grade': 'Proven',
        'inspection_basis': 'supplied graded report; upstream source not independently replayed here',
        'execution_grade': 'Unknown', 'standards_equivalence': 'Unknown',
        'models': MODELS}, 'graded model source')


def check_roster(d):
    expected = [(pack_ref(element['ref']), kind) for element, kind in items()]
    require([(r['ref'], r['kind']) for r in d['rows']] == expected, 'exact roster')
    require(d['scope'] == SCOPE, 'scope')


def check_dispositions(d):
    require([r['ref'] for r in d['rows']
             if r['disposition'] in ('exact', 'transformed')] ==
            [POSITIVE_REF], 'single positive')
    for row, (element, kind) in zip(d['rows'], items()):
        if row['ref'] == POSITIVE_REF:
            require(row['kind'] == 'fact' and row['disposition'] == 'transformed'
                    and row['reason'] == POSITIVE_REASON, 'positive identity')
            continue
        outcome, reason = rule(element, kind)[:2]
        require(row['disposition'] == outcome and row['reason'] == reason and
                'target' not in row, 'no target payload or inferred mapping')
        construct = TOPOLOGY_CONSTRUCT if outcome == 'withheld' else None
        require(row.get('target_construct') == construct, 'target construct')


def check_relations(d):
    for row, (element, kind) in zip(d['rows'], items()):
        if kind != 'relation':
            require('relation' not in row, 'relation attributes only on relations')
            continue
        attributes = element['attributes']
        expected = {'core_type': attributes['core_type']}
        if 'medium' in attributes:
            expected['medium'] = attributes['medium']
        require(row['relation'] == expected, 'relation type from catalog')


def fact_keys(element):
    ref = pack_ref(element['ref'])
    subject = element['attributes']['subject']
    dimension = pack_ref(subject.get('dimension') or subject['qualifier_dimension'])
    return [{'pack_id': ref['pack']['id'], 'pack_version': ref['pack']['version'],
             'fact_id': ref['id'],
             'dimensions': {'mode': 'exact_runtime_fact_key',
                            'definition': dimension}}]


def check_source(d):
    for row, (element, kind) in zip(d['rows'], items()):
        ref = pack_ref(element['ref'])
        requested = None
        if kind != 'service':
            requested = {'kind': kind, 'item_id': ref['id'],
                         'item_version': ref['version']}
        require(row['source'] == {
            'kernel_contract': 'helianthus.semantic.kernel/v1',
            'requested': requested,
            'revision_binding': {'snapshot_id': 'exact_input_snapshot',
                                 'revisions': 'exact_input_revisions'},
            'fact_keys': fact_keys(element) if kind == 'fact' else []},
            'exact source binding')


def check_target(d):
    target = positive(d)['target']
    require({k: v for k, v in target.items() if k != 'value'} ==
            {'device_type_id': 1296, 'cluster_id': 144, 'attribute_id': 5}, 'tuple')


def check_phase(d):
    row = positive(d)
    require(row['target']['value']['emission'] == VALUE['emission'],
            'one non-null phase-qualified source')
    cited = phase_relation()
    require(row['relations'] == [cited], 'phase association cites its relation')
    require(sum(1 for r in d['rows'] if r['ref'] == cited and
                r['kind'] == 'relation') == 1, 'cited relation has its own row')
    require(all('relations' not in r for r in d['rows'] if r is not row),
            'only the positive row cites a relation')


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
    for row, (element, kind) in zip(d['rows'], items()):
        item = row['ref']['id']
        if row['ref'] == POSITIVE_REF:
            expected = [
                {'kind': 'unit', 'source_items': ['evse.ac.current'],
                 'description': 'amperes are represented as integral milliamperes only when exact and representable',
                 'reversible': False}]
        else:
            loss_kind, description = rule(element, kind)[2:]
            expected = [{'kind': loss_kind, 'source_items': [item],
                         'description': description, 'reversible': False}]
        require(row['loss'] == expected, 'explicit irreversible loss')


CHECKS = [check_model, check_roster, check_dispositions, check_relations,
          check_source, check_target, check_phase, check_conversion,
          check_guards, check_loss]


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

    def index(self, ref=POSITIVE_REF, kind=None):
        return next(i for i, r in enumerate(self.document['rows'])
                    if r['ref'] == ref and (kind is None or r['kind'] == kind))

    def first(self, kind, outcome=None):
        return next(i for i, r in enumerate(self.document['rows'])
                    if r['kind'] == kind and
                    (outcome is None or r['disposition'] == outcome))

    def test_baseline_independent_checks(self):
        for checker in CHECKS:
            with self.subTest(check=checker.__name__):
                checker(self.document)

    def test_roster_covers_every_requested_catalog_kind(self):
        # Every kind is present, so no kind can be dropped by a derived roster.
        self.assertEqual({r['kind'] for r in self.document['rows']}, set(KINDS))
        self.assertEqual(len(self.document['rows']), len(items()))

    def test_historical_accounting_preserved(self):
        historical = load(HISTORICAL)
        self.assertEqual(self.document['historical_input'], HISTORICAL.name)
        kept = [r for r in self.document['rows']
                if r['kind'] in ('fact', 'capability', 'operation')]
        historical_ids = {json.dumps(row['ref'], sort_keys=True) for row in historical['rows']}
        matched = [row for row in kept if json.dumps(row['ref'], sort_keys=True) in historical_ids]
        extra = [row for row in kept if json.dumps(row['ref'], sort_keys=True) not in historical_ids]
        self.assertEqual(len(matched), len(historical['rows']))
        for old, new in zip(historical['rows'], matched):
            expected = copy.deepcopy(new)
            if expected['ref'] == POSITIVE_REF:
                # The phase association now cites its relation definition.
                del expected['relations']
                expected['reason'] = HISTORICAL_POSITIVE_REASON
            self.assertEqual(old, expected)
        pilot = {'pv.accuracy.measured', 'pv.accuracy.ratio_maximum',
                 'infrastructure.accuracy.measured', 'infrastructure.accuracy.ratio_maximum',
                 'storage.limit.charge_current', 'storage.limit.discharge_current'}
        room = {
            'thermal.capability.read.room',
            'thermal.room.capability_set_occupied_cooling',
            'thermal.room.capability_set_occupied_heating',
            'thermal.room.capability_set_temperature',
            'thermal.room.capability_set_zone_cooling_mode',
            'thermal.room.capability_set_zone_mode',
            'thermal.room.limit_absolute_maximum_cooling_setpoint',
            'thermal.room.limit_absolute_maximum_heating_setpoint',
            'thermal.room.limit_absolute_minimum_cooling_setpoint',
            'thermal.room.limit_absolute_minimum_heating_setpoint',
            'thermal.room.limit_maximum_cooling_setpoint',
            'thermal.room.limit_maximum_heating_setpoint',
            'thermal.room.limit_minimum_cooling_setpoint',
            'thermal.room.limit_minimum_heating_setpoint',
            'thermal.room.limit_setpoint_step',
            'thermal.room.measurement_air_temperature',
            'thermal.room.mode_zone',
            'thermal.room.mode_zone_cooling',
            'thermal.room.operation_set_occupied_cooling',
            'thermal.room.operation_set_occupied_heating',
            'thermal.room.operation_set_temperature',
            'thermal.room.operation_set_zone_cooling_mode',
            'thermal.room.operation_set_zone_mode',
            'thermal.room.setpoint_occupied_cooling',
            'thermal.room.setpoint_occupied_heating',
            'thermal.room.setpoint_temperature_setpoint',
        }
        new_facts = {
            "infrastructure.ac.apparent_current",
            "infrastructure.ac.harmonic_current",
            "infrastructure.ac.harmonic_phase",
            "infrastructure.ac.neutral_current",
            "infrastructure.ac.phase_power_factor",
            "infrastructure.ac.reactive_current",
            "infrastructure.energy.apparent_export",
            "infrastructure.energy.apparent_import",
            "infrastructure.energy.phase_export",
            "infrastructure.energy.phase_import",
            "infrastructure.energy.reactive_export",
            "infrastructure.energy.reactive_import",
            "infrastructure.limit.pv_curtailment_factor",
            "infrastructure.load.active_power",
            "infrastructure.load.energy_consumed",
            "infrastructure.load.energy_produced",
            "infrastructure.load.phase_active_power",
            "infrastructure.meter.apparent_power_threshold",
            "infrastructure.meter.kind",
            "infrastructure.meter.point_of_delivery",
            "infrastructure.meter.power_threshold",
            "infrastructure.meter.power_threshold_source",
            "infrastructure.meter.protocol_version",
            "infrastructure.mgcp.ac_current",
            "infrastructure.mgcp.actor",
            "infrastructure.mgcp.committed_power_plan",
            "infrastructure.mgcp.per",
            "infrastructure.mgcp.slots",
            "infrastructure.mgcp.use_case_name",
            "infrastructure.mgcp.use_case_version",
            "infrastructure.mgcp.value_range_min",
            "infrastructure.mgcp.value_source",
            "infrastructure.mpc.ac_power",
            "infrastructure.mpc.ac_voltage",
            "infrastructure.mpc.actor",
            "infrastructure.mpc.one",
            "infrastructure.mpc.per",
            "infrastructure.mpc.slots",
            "infrastructure.mpc.use_case_name",
            "infrastructure.mpc.use_case_version",
            "infrastructure.mpc.value_range_min",
            "infrastructure.mpc.value_state",
            "infrastructure.status.supply_condition",
            "pv.ac.phase_energy_exported",
            "pv.ac.phase_energy_imported",
            "pv.ac.phase_power_factor",
            "pv.configuration.grid_code",
            "pv.dc.aggregate_energy",
            "pv.energy.apparent_exported",
            "pv.energy.apparent_imported",
            "pv.energy.consumed",
            "pv.energy.reactive_exported",
            "pv.energy.reactive_imported",
            "pv.energy.yield_history",
            "pv.moi.ac_yield_day",
            "pv.moi.ac_yield_day_historical",
            "pv.moi.ac_yield_month",
            "pv.moi.ac_yield_month_historical",
            "pv.moi.ac_yield_total",
            "pv.moi.ac_yield_year",
            "pv.moi.ac_yield_year_historical",
            "pv.moi.actor",
            "pv.moi.device_code",
            "pv.moi.device_name",
            "pv.moi.ec1",
            "pv.moi.hardware_revision",
            "pv.moi.manufacturer_label",
            "pv.moi.moi_016b",
            "pv.moi.moi_018",
            "pv.moi.moi_022",
            "pv.moi.serial_number",
            "pv.moi.software_revision",
            "pv.moi.timestamp",
            "pv.moi.use_case_name",
            "pv.moi.use_case_version",
            "pv.moi.vendor_code",
            "pv.moi.vendor_name",
            "pv.mps.actor",
            "pv.mps.ec1",
            "pv.mps.use_case_name",
            "pv.mps.use_case_version",
            "pv.nameplate.apparent_consumption_nominal_maximum",
            "pv.nameplate.apparent_production_nominal_maximum",
            "pv.nameplate.consumption_nominal_maximum",
            "pv.nameplate.peak_power",
            "pv.nameplate.production_nominal_maximum",
            "pv.status.battery_availability",
            "pv.status.failure_states",
            "pv.status.functional_states",
            "pv.status.grid_connection",
            "pv.status.string_availability",
            "pv.string.azimuth",
            "pv.string.current",
            "pv.string.insulation_resistance",
            "pv.string.power",
            "pv.string.temperature",
            "pv.string.tilt",
            "pv.string.voltage",
            "pv.system.active_power",
            "pv.vapd.ac_power_total",
            "pv.vapd.ac_yield_total",
            "pv.vapd.actor",
            "pv.vapd.ec1",
            "pv.vapd.use_case_name",
            "pv.vapd.use_case_version",
            "pv.vapd.vapd_004",
        }
        storage_rows = {
            "storage.capability.set_ac_charge_power_limit",
            "storage.capability.set_ac_discharge_power_limit",
            "storage.capability.set_ac_power",
            "storage.capability.set_control_mode",
            "storage.capability.set_dc_charge_power_limit",
            "storage.capability.set_dc_discharge_power_limit",
            "storage.capability.set_dc_power",
            "storage.capability.set_default_ac_power",
            "storage.capability.set_default_dc_power",
            "storage.capability.set_default_pcc_power",
            "storage.capability.set_failsafe_ac_power",
            "storage.capability.set_failsafe_dc_power",
            "storage.capability.set_failsafe_duration_minimum",
            "storage.capability.set_failsafe_pcc_power",
            "storage.capability.set_pcc_power",
            "storage.capacity.full_charge",
            "storage.capacity.remaining",
            "storage.cob.actor",
            "storage.cob.ec1",
            "storage.cob.heartbeat_counter",
            "storage.cob.heartbeat_timeout",
            "storage.cob.heartbeat_timestamp",
            "storage.cob.use_case_name",
            "storage.cob.use_case_version",
            "storage.configuration.battery_type",
            "storage.configuration.control_mode",
            "storage.configuration.default_ac_power",
            "storage.configuration.default_dc_power",
            "storage.configuration.default_pcc_power",
            "storage.configuration.failsafe_ac_power",
            "storage.configuration.failsafe_dc_power",
            "storage.configuration.failsafe_duration_minimum",
            "storage.configuration.failsafe_pcc_power",
            "storage.configuration.maximum_cycles_per_day",
            "storage.interface.ac_power",
            "storage.limit.ac_charge_power",
            "storage.limit.ac_discharge_power",
            "storage.limit.dc_charge_power",
            "storage.limit.dc_discharge_power",
            "storage.mob.actor",
            "storage.mob.device_code",
            "storage.mob.device_name",
            "storage.mob.ec1",
            "storage.mob.hardware_revision",
            "storage.mob.manufacturer_label",
            "storage.mob.moi_016b",
            "storage.mob.moi_018",
            "storage.mob.moi_022",
            "storage.mob.serial_number",
            "storage.mob.software_revision",
            "storage.mob.timestamp",
            "storage.mob.use_case_name",
            "storage.mob.use_case_version",
            "storage.mob.vendor_code",
            "storage.mob.vendor_name",
            "storage.nameplate.ac_charge_power_maximum",
            "storage.nameplate.ac_charge_power_nominal_maximum",
            "storage.nameplate.ac_charge_power_nominal_minimum",
            "storage.nameplate.ac_discharge_power_maximum",
            "storage.nameplate.ac_discharge_power_nominal_maximum",
            "storage.nameplate.ac_discharge_power_nominal_minimum",
            "storage.nameplate.dc_charge_power_maximum",
            "storage.nameplate.dc_discharge_power_maximum",
            "storage.nameplate.time_to_ac_charge_power_maximum",
            "storage.nameplate.time_to_ac_discharge_power_maximum",
            "storage.operation.set_ac_charge_power_limit",
            "storage.operation.set_ac_discharge_power_limit",
            "storage.operation.set_ac_power",
            "storage.operation.set_control_mode",
            "storage.operation.set_dc_charge_power_limit",
            "storage.operation.set_dc_discharge_power_limit",
            "storage.operation.set_dc_power",
            "storage.operation.set_default_ac_power",
            "storage.operation.set_default_dc_power",
            "storage.operation.set_default_pcc_power",
            "storage.operation.set_failsafe_ac_power",
            "storage.operation.set_failsafe_dc_power",
            "storage.operation.set_failsafe_duration_minimum",
            "storage.operation.set_failsafe_pcc_power",
            "storage.operation.set_pcc_power",
            "storage.setpoint.ac_power",
            "storage.setpoint.active",
            "storage.setpoint.dc_power",
            "storage.setpoint.duration",
            "storage.setpoint.pcc_power",
            "storage.state.cycle_count",
            "storage.status.charge_direction",
            "storage.status.charge_faults",
            "storage.status.charge_level",
            "storage.status.faults",
            "storage.status.replacement_needed",
            "storage.status.state",
            "storage.system.ac_power",
            "storage.system.energy_charged",
            "storage.system.energy_discharged",
            "storage.system.state_of_charge",
            "storage.vabd.actor",
            "storage.vabd.ec1",
            "storage.vabd.use_case_name",
            "storage.vabd.use_case_version",
            "storage.vabd.vabd_005",
        }
        self.assertEqual({row['ref']['id'] for row in extra}, pilot | room | new_facts | storage_rows)
        for row in extra:
            self.assertEqual(row['disposition'], 'unknown')
            self.assertEqual(row['reason'], 'matter.unmapped.v1')
            self.assertNotIn('target', row)
        self.assertEqual(self.document['ownership'], historical['ownership'])
        self.assertEqual(self.document['non_claims'], historical['non_claims'])

    def test_model_version_and_revision_mutants(self):
        cases = [(('target', 'version'), '1.7')]
        cases += [(('model_source', 'models', i, 'revision'), revision)
                  for i, revision in enumerate([2, 2, 4])]
        cases += [(('pins', 'packs', 'storage'), '1.0.0')]
        for path, value in cases:
            with self.subTest(axis=path):
                self.reject(check_model, path, value)

    def test_second_positive_mutant(self):
        self.reject(check_dispositions, ('rows', 0, 'disposition'), 'transformed')
        for kind in ('service', 'relation'):
            with self.subTest(kind=kind):
                self.reject(check_dispositions,
                            ('rows', self.first(kind), 'disposition'), 'exact')

    def test_missing_requested_item_each_pack_and_kind_mutants(self):
        for pack in packs():
            for kind in KINDS:
                rows = copy.deepcopy(self.document['rows'])
                found = [i for i, r in enumerate(rows) if r['kind'] == kind and
                         r['ref']['pack']['id'] == 'helianthus.pack.' + pack]
                if not found:
                    continue
                del rows[found[0]]
                with self.subTest(pack=pack, kind=kind):
                    self.reject(check_roster, ('rows',), rows)

    def test_row_identity_axes_mutants(self):
        # Valid sibling components, one axis changed, every other field valid.
        cases = {
            self.index(): [(('ref', 'pack', 'id'), 'helianthus.pack.pv'),
                           (('ref', 'pack', 'version'), '1.1.0'),
                           (('kind',), 'capability'),
                           (('ref', 'id'), 'evse.ac.voltage'),
                           (('ref', 'version'), '1.1.0')],
            self.first('service'): [(('ref', 'pack', 'id'), 'helianthus.pack.pv'),
                                    (('ref', 'pack', 'version'), '1.1.0'),
                                    (('kind',), 'relation'),
                                    (('ref', 'id'), 'evse.service.evse'),
                                    (('ref', 'version'), '1.1.0')],
            self.first('relation'): [(('ref', 'pack', 'id'), 'helianthus.pack.pv'),
                                     (('ref', 'pack', 'version'), '1.1.0'),
                                     (('kind',), 'service'),
                                     (('ref', 'id'), 'evse.relation.evse_meter'),
                                     (('ref', 'version'), '1.1.0')]}
        for i, axes in cases.items():
            for path, value in axes:
                with self.subTest(row=i, axis=path):
                    self.reject(check_roster, ('rows', i) + path, value)

    def test_scope_mutants(self):
        self.reject(check_roster, ('scope', 'projection_items'), KINDS[:3])
        self.reject(check_roster, ('scope', 'derived_from'),
                    'api/v1/pack-metadata-v1.json')

    def test_fact_identity_and_dimension_axes_mutants(self):
        prefix = ('rows', self.index(), 'source', 'fact_keys', 0)
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
        for i in (self.index(), self.first('relation')):
            prefix = ('rows', i, 'source')
            cases = [(('requested', 'kind'), 'capability'),
                     (('requested', 'item_id'), 'evse.ac.voltage'),
                     (('requested', 'item_version'), '1.1.0'),
                     (('revision_binding', 'snapshot_id'), 'other_input_snapshot'),
                     (('revision_binding', 'revisions'), 'other_input_revisions')]
            for path, value in cases:
                with self.subTest(row=i, axis=path):
                    self.reject(check_source, prefix + path, value)

    def test_service_is_never_a_requested_item_mutant(self):
        i = self.first('service')
        row = self.document['rows'][i]
        self.reject(check_source, ('rows', i, 'source', 'requested'),
                    {'kind': 'service', 'item_id': row['ref']['id'],
                     'item_version': row['ref']['version']})

    def test_relation_type_mutants(self):
        withheld = self.first('relation', 'withheld')
        self.reject(check_relations, ('rows', withheld, 'relation', 'core_type'),
                    'contains')
        supplies = next(i for i, r in enumerate(self.document['rows'])
                        if r.get('relation', {}).get('core_type') == 'supplies')
        self.reject(check_relations, ('rows', supplies, 'relation', 'medium'),
                    'refrigerant')

    def test_relation_and_service_outcome_mutants(self):
        cases = [(self.first('relation', 'withheld'), 'disposition', 'unknown'),
                 (self.first('relation', 'withheld'), 'reason', NOT_ADOPTED[1]),
                 (self.first('relation', 'unknown'), 'disposition', 'withheld'),
                 (self.first('relation', 'unknown'), 'reason', TOPOLOGY[1]),
                 (self.first('service'), 'disposition', 'unknown'),
                 (self.first('service'), 'reason', UNMAPPED[1])]
        for i, field, value in cases:
            with self.subTest(row=i, field=field):
                self.reject(check_dispositions, ('rows', i, field), value)

    def test_target_construct_mutants(self):
        prefix = ('rows', self.first('relation', 'withheld'), 'target_construct')
        self.reject(check_dispositions, prefix + ('cluster_id',), 144)
        self.reject(check_dispositions, prefix + ('equivalence',), 'Proven')
        self.reject(check_dispositions,
                    ('rows', self.first('relation', 'unknown'), 'target_construct'),
                    TOPOLOGY_CONSTRUCT)

    def test_target_identity_axes_mutants(self):
        # Valid sibling device, cluster and attribute identifiers, not sentinels.
        prefix = ('rows', self.index(), 'target')
        for axis, value in [('device_type_id', 14), ('cluster_id', 156),
                            ('attribute_id', 4)]:
            with self.subTest(axis=axis):
                self.reject(check_target, prefix + (axis,), value)

    def test_phase_restriction_mutants(self):
        prefix = ('rows', self.index(), 'target', 'value', 'emission')
        for axis, value in [('required_dimension', 'evse.dimension.evse'),
                            ('eligible_source_keys', 2),
                            ('value_must_be_non_null', False)]:
            with self.subTest(axis=axis):
                self.reject(check_phase, prefix + (axis,), value)
        self.reject(check_phase, prefix, {})

    def test_phase_association_citation_mutants(self):
        # Each axis of the cited relation identity is varied with a valid sibling.
        prefix = ('rows', self.index(), 'relations', 0)
        cases = [(('pack', 'id'), 'helianthus.pack.infrastructure'),
                 (('pack', 'version'), '1.1.0'),
                 (('id',), 'evse.relation.connector_session'),
                 (('version',), '1.1.0')]
        for path, value in cases:
            with self.subTest(axis=path):
                self.reject(check_phase, prefix + path, value)
        self.reject(check_phase, ('rows', self.index(), 'relations'), [])
        cited = self.index(phase_relation(), 'relation')
        rows = [r for k, r in enumerate(self.document['rows']) if k != cited]
        self.reject(check_phase, ('rows',), rows)
        self.reject(check_phase, ('rows', 0, 'relations'), [phase_relation()])

    def test_fractional_rounding_range_and_refusal_mutants(self):
        prefix = ('rows', self.index(), 'target', 'value')
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
        i = self.index()
        self.reject(check_loss, ('rows', i, 'loss'), [])
        self.reject(check_loss, ('rows', i, 'loss', 0, 'reversible'), True)
        self.reject(check_loss, ('rows', 0, 'loss'), [])
        for kind in ('service', 'relation'):
            with self.subTest(kind=kind):
                self.reject(check_loss, ('rows', self.first(kind), 'loss'), [])
                self.reject(check_loss,
                            ('rows', self.first(kind), 'loss', 0, 'reversible'), True)

    def test_phase_identity_loss_is_not_reinstated_mutant(self):
        i = self.index()
        loss = copy.deepcopy(self.document['rows'][i]['loss'])
        loss.append({'kind': 'identity', 'source_items': ['evse.ac.current'],
                     'description': 'phase identity and endpoint association are lost',
                     'reversible': False})
        self.reject(check_loss, ('rows', i, 'loss'), loss)

    def test_every_other_item_stays_unpromoted_mutants(self):
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


class Matter161ProjectionPageTests(unittest.TestCase):
    PAGE = ROOT / 'api/v1/targets/matter-1.6.1-v1.md'

    def setUp(self):
        self.text = self.PAGE.read_text()

    def test_chemistry_pair_stays_out_and_pilot_facts_are_unknown(self):
        for ident in ['storage.attribute.chemistry', 'storage.configuration.battery_type']:
            with self.subTest(ident=ident):
                self.assertIn(ident, self.text)
        self.assertIn('are not added', self.text)
        for ident in ['storage.limit.charge_current', 'storage.limit.discharge_current',
                      'pv.accuracy.measured', 'pv.accuracy.ratio_maximum',
                      'infrastructure.accuracy.measured', 'infrastructure.accuracy.ratio_maximum',
                      'pv.dimension.measurement_type', 'infrastructure.dimension.measurement_type']:
            with self.subTest(ident=ident):
                self.assertIn(ident, self.text)
        self.assertIn('PV inverter', self.text)
        self.assertIn('have no roster row', self.text)
        self.assertIn('matter.unmapped.v1', self.text)
        self.assertIn('no struct is published', self.text)
        self.assertIn('does not deliver', self.text)
        self.assertIn('withheld', self.text)

    def test_no_false_unresolved_subject_schema_cause(self):
        self.assertNotIn('unresolved subject', self.text)
        self.assertNotIn('qualifier dimension only', self.text)

    def test_internal_table_names_are_not_cited_as_source(self):
        self.assertNotIn('PE03', self.text)
        self.assertNotIn('PE10', self.text)
        self.assertIn('unverified', self.text)


if __name__ == '__main__':
    unittest.main()
