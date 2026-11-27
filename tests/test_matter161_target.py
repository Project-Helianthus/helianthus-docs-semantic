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
KINDS = ['fact', 'capability', 'operation', 'service', 'relation', 'event']
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
    'conversion': {'algorithm': 'exact_multiply', 'factor': 1000, 'offset': 0,
                   'rounding': 'exact', 'require_integral_result': True},
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


def cited_number(mapping, key):
    item = mapping.get(key)
    return (key in mapping and isinstance(item, (int, float)) and
            not isinstance(item, bool))


def cites_conversion(row):
    # A transformed row names one device type, one cluster, one element, and
    # one conversion that cites factor, offset, rounding and representation bounds.
    target = row.get('target')
    if not isinstance(target, dict):
        return False
    value = target.get('value')
    if not isinstance(value, dict):
        return False
    conversion = value.get('conversion')
    representation = value.get('representation')
    if not isinstance(conversion, dict) or not isinstance(representation, dict):
        return False
    rounding = conversion.get('rounding')
    return (cited_number(target, 'device_type_id') and
            cited_number(target, 'cluster_id') and
            cited_number(target, 'attribute_id') and
            cited_number(conversion, 'factor') and
            cited_number(conversion, 'offset') and
            isinstance(rounding, str) and rounding != '' and
            cited_number(representation, 'minimum') and
            cited_number(representation, 'maximum'))


def check_dispositions(d):
    positives = [r['ref'] for r in d['rows']
                 if r['disposition'] in ('exact', 'transformed')]
    require(POSITIVE_REF in positives, 'evse.ac.current remains transformed')
    for row, (element, kind) in zip(d['rows'], items()):
        if row['disposition'] in ('exact', 'transformed'):
            require(kind in ('fact', 'capability', 'operation', 'event'),
                    'service and relation are not transformed')
            require(cites_conversion(row),
                    'transformed row cites device type, cluster, element, factor, offset, rounding and bounds')
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
        if kind not in ('service', 'event'):
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


PILOT_UNSOURCED = [
    ('Power Topology', 156, 'FeatureMap', 65532),
    ('Electrical Power Measurement', 144, 'FeatureMap', 65532),
    ('Electrical Power Measurement', 144, 'PowerMode', 0),
    ('Electrical Power Measurement', 144, 'NumberOfMeasurementTypes', 1),
    ('Electrical Power Measurement', 144, 'Accuracy.MinMeasuredValue', 2),
    ('Electrical Power Measurement', 144, 'Accuracy.MaxMeasuredValue', 2),
    ('Electrical Power Measurement', 144, 'Accuracy.AccuracyRanges.RangeMin', 2),
    ('Electrical Power Measurement', 144, 'Accuracy.AccuracyRanges.RangeMax', 2),
    ('Electrical Power Measurement', 144, 'Accuracy.MeasurementType', 2),
    ('Electrical Power Measurement', 144, 'Accuracy.Measured', 2),
    ('Electrical Power Measurement', 144, 'ActivePower', 8),
]


def check_pilot(d):
    pilot = d['electrical_sensor_pilot']
    require(set(pilot) == {'device_type_id', 'declared_values', 'unsourced'}, 'pilot members')
    require(pilot['device_type_id'] == 1296, 'pilot device type')
    require(pilot['declared_values'] == [], 'no declared value without a recorded sentence')
    entries = pilot['unsourced']
    require([(e['cluster'], e['cluster_id'], e['attribute'], e['attribute_id'])
             for e in entries] == PILOT_UNSOURCED, 'unsourced values')
    for entry in entries:
        require(set(entry) == {'cluster', 'cluster_id', 'attribute', 'attribute_id',
                               'status', 'reason'}, 'unsourced entry members')
        require(entry['status'] == 'unsourced', 'unsourced status')
        require(isinstance(entry['reason'], str) and entry['reason'] != '', 'reason')
    for row in d['rows']:
        require('declared' not in row.get('target', {}) and 'field' not in row.get('target', {}),
                'no row uses the field or declared member yet')


CHECKS = [check_model, check_roster, check_dispositions, check_relations,
          check_source, check_target, check_phase, check_conversion,
          check_guards, check_loss, check_pilot]


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
                # Offset and rounding cite the same exact milliampere conversion.
                del expected['relations']
                expected['reason'] = HISTORICAL_POSITIVE_REASON
                conversion = expected['target']['value']['conversion']
                self.assertEqual(conversion['offset'], 0)
                self.assertEqual(conversion['rounding'], 'exact')
                del conversion['offset']
                del conversion['rounding']
            self.assertEqual(old, expected)
        pilot = {'pv.accuracy.measured', 'pv.accuracy.ratio_maximum',
                 'infrastructure.accuracy.measured', 'infrastructure.accuracy.ratio_maximum',
                 'storage.limit.charge_current', 'storage.limit.discharge_current'}
        ep01_pv_accuracy = {
            'pv.accuracy.measured_minimum_active_current',
            'pv.accuracy.measured_maximum_active_current',
            'pv.accuracy.range_minimum_active_current',
            'pv.accuracy.range_maximum_active_current',
            'pv.accuracy.measured_minimum_active_power',
            'pv.accuracy.measured_maximum_active_power',
            'pv.accuracy.range_minimum_active_power',
            'pv.accuracy.range_maximum_active_power',
        }
        cr02_accuracy = {
            'infrastructure.accuracy.measured_minimum_active_current',
            'infrastructure.accuracy.measured_maximum_active_current',
            'infrastructure.accuracy.range_minimum_active_current',
            'infrastructure.accuracy.range_maximum_active_current',
            'infrastructure.accuracy.measured_minimum_active_power',
            'infrastructure.accuracy.measured_maximum_active_power',
            'infrastructure.accuracy.range_minimum_active_power',
            'infrastructure.accuracy.range_maximum_active_power',
            'evse.accuracy.measured',
            'evse.accuracy.ratio_maximum',
            'evse.accuracy.measured_minimum_active_current',
            'evse.accuracy.measured_maximum_active_current',
            'evse.accuracy.range_minimum_active_current',
            'evse.accuracy.range_maximum_active_current',
            'evse.accuracy.measured_minimum_active_power',
            'evse.accuracy.measured_maximum_active_power',
            'evse.accuracy.range_minimum_active_power',
            'evse.accuracy.range_maximum_active_power',
            'storage.accuracy.measured',
            'storage.accuracy.ratio_maximum',
            'storage.accuracy.measured_minimum_active_current',
            'storage.accuracy.measured_maximum_active_current',
            'storage.accuracy.range_minimum_active_current',
            'storage.accuracy.range_maximum_active_current',
            'storage.accuracy.measured_minimum_active_power',
            'storage.accuracy.measured_maximum_active_power',
            'storage.accuracy.range_minimum_active_power',
            'storage.accuracy.range_maximum_active_power',
        }
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
        evse_rows = {
            'evse.status.state',
            'evse.status.supply',
            'evse.status.fault_cause',
            'evse.limit.charging_enabled_until',
            'evse.limit.allocated_current_expiry',
            'evse.limit.discharging_enabled_until',
            'evse.limit.minimum_charge_current',
            'evse.limit.maximum_discharge_current',
            'evse.limit.user_maximum_charge_current',
            'evse.limit.failsafe_current',
            'evse.limit.recommended_current_phase',
            'evse.limit.vehicle_minimum_current_phase',
            'evse.limit.vehicle_maximum_current_phase',
            'evse.configuration.randomization_delay_window',
            'evse.mode',
            'evse.mode_supported',
            'evse.ac.total_active_power',
            'evse.ac.connected_phases',
            'evse.energy.lifetime_exported',
            'evse.session.identifier',
            'evse.session.start',
            'evse.session.duration',
            'evse.energy.session_discharged',
            'evse.session.rfid_token',
            'evse.session.communication_standard',
            'evse.session.asymmetric_charging',
            'evse.demand.minimum_energy',
            'evse.demand.optimal_energy',
            'evse.demand.maximum_energy',
            'evse.demand.departure_time',
            'evse.summary.energy_grid',
            'evse.summary.energy_self_produced',
            'evse.summary.self_produced_ratio',
            'evse.summary.cost',
            'evse.summary.currency',
            'evse.summary.end',
            'evse.target.schedule_count',
            'evse.target.days',
            'evse.target.time_of_day',
            'evse.target.state_of_charge',
            'evse.target.added_energy',
            'evse.target.next_start',
            'evse.target.next_target_time',
            'evse.target.next_required_energy',
            'evse.target.next_state_of_charge',
            'evse.vehicle.approximate_efficiency',
            'evse.vehicle.state_of_charge',
            'evse.vehicle.battery_capacity',
            'evse.vehicle.state_of_health',
            'evse.vehicle.travel_range',
            'evse.vehicle.identifier',
            'evse.vehicle.minimum_power',
            'evse.vehicle.maximum_power',
            'evse.vehicle.standby_power',
            'evse.vehicle.sleep',
            'evse.vehicle.connection',
            'evse.vehicle.ac_power',
            'evse.operation.set_supply',
            'evse.operation.set_allocated_current_with_expiry',
            'evse.operation.set_user_maximum_charge_current',
            'evse.operation.set_randomization_delay_window',
            'evse.operation.set_vehicle_efficiency',
            'evse.operation.set_target',
            'evse.operation.clear_targets',
            'evse.operation.set_evse_mode',
            'evse.operation.set_allocated_current_phase',
            'evse.operation.set_recommended_current_phase',
            'evse.operation.set_failsafe_current',
            'evse.capability.set_supply',
            'evse.capability.set_allocated_current_with_expiry',
            'evse.capability.set_user_maximum_charge_current',
            'evse.capability.set_randomization_delay_window',
            'evse.capability.set_vehicle_efficiency',
            'evse.capability.set_target',
            'evse.capability.clear_targets',
            'evse.capability.set_evse_mode',
            'evse.capability.set_allocated_current_phase',
            'evse.capability.set_recommended_current_phase',
            'evse.capability.set_failsafe_current',
            'evse.capability.read.vehicle',
            'evse.cevc.actor',
            'evse.cevc.brand_name',
            'evse.cevc.cevc_001',
            'evse.cevc.cevc_007',
            'evse.cevc.cevc_012',
            'evse.cevc.cevc_015',
            'evse.cevc.cevc_023',
            'evse.cevc.cevc_028',
            'evse.cevc.cevc_054',
            'evse.cevc.device_code',
            'evse.cevc.earliest_time_series_start_time',
            'evse.cevc.electrical_connection_id',
            'evse.cevc.hardware_revision',
            'evse.cevc.heartbeat_counter',
            'evse.cevc.heartbeat_timeout',
            'evse.cevc.heartbeat_timestamp',
            'evse.cevc.incentive_slot',
            'evse.cevc.incentive_slot_constraints',
            'evse.cevc.incentive_table',
            'evse.cevc.incentive_table_constraints',
            'evse.cevc.incentive_table_description',
            'evse.cevc.manufacturer_label',
            'evse.cevc.measurement_id',
            'evse.cevc.operating_state',
            'evse.cevc.permitted_value_set',
            'evse.cevc.scope_type',
            'evse.cevc.serial_number',
            'evse.cevc.slot_count_max',
            'evse.cevc.slot_count_min',
            'evse.cevc.slot_duration_min',
            'evse.cevc.slot_value_max',
            'evse.cevc.slot_value_min',
            'evse.cevc.slot_value_step_size',
            'evse.cevc.software_revision',
            'evse.cevc.tariff_constraints',
            'evse.cevc.tariff_description',
            'evse.cevc.tier',
            'evse.cevc.time_period',
            'evse.cevc.time_series_constraints_data',
            'evse.cevc.time_series_description_data',
            'evse.cevc.time_series_id',
            'evse.cevc.time_series_slot',
            'evse.cevc.time_series_type',
            'evse.cevc.time_series_writeable',
            'evse.cevc.unit',
            'evse.cevc.use_case_name',
            'evse.cevc.use_case_version',
            'evse.cevc.vendor_code',
            'evse.cevc.vendor_name',
            'evse.evcc.actor',
            'evse.evcc.brand_name',
            'evse.evcc.device_code',
            'evse.evcc.device_name',
            'evse.evcc.electrical_connection_id',
            'evse.evcc.evcc_006',
            'evse.evcc.evcc_007',
            'evse.evcc.evcc_017',
            'evse.evcc.evcc_018',
            'evse.evcc.evcc_019',
            'evse.evcc.hardware_revision',
            'evse.evcc.identification_id',
            'evse.evcc.identification_value',
            'evse.evcc.iso15118',
            'evse.evcc.key_id',
            'evse.evcc.key_name',
            'evse.evcc.manufacturer_description',
            'evse.evcc.manufacturer_label',
            'evse.evcc.measurement_id',
            'evse.evcc.one',
            'evse.evcc.operating_state',
            'evse.evcc.parameter_id',
            'evse.evcc.permitted_value_set',
            'evse.evcc.scope_type',
            'evse.evcc.serial_number',
            'evse.evcc.software_revision',
            'evse.evcc.use_case_name',
            'evse.evcc.use_case_version',
            'evse.evcc.value_type',
            'evse.evcc.vendor_code',
            'evse.evcc.vendor_name',
            'evse.evcem.ac_measured_phases',
            'evse.evcem.ac_measurement_variant',
            'evse.evcem.actor',
            'evse.evcem.brand_name',
            'evse.evcem.current',
            'evse.evcem.device_code',
            'evse.evcem.electrical_connection_id',
            'evse.evcem.hardware_revision',
            'evse.evcem.manufacturer_label',
            'evse.evcem.measurement_constraints_data',
            'evse.evcem.measurement_id',
            'evse.evcem.measurement_type',
            'evse.evcem.parameter_id',
            'evse.evcem.permitted_value_set',
            'evse.evcem.scope_type',
            'evse.evcem.serial_number',
            'evse.evcem.software_revision',
            'evse.evcem.timestamp',
            'evse.evcem.use_case_name',
            'evse.evcem.use_case_version',
            'evse.evcem.value_range_min',
            'evse.evcem.value_source',
            'evse.evcem.vendor_code',
            'evse.evcem.vendor_name',
            'evse.evcem.voltage_type',
            'evse.evcs.actor',
            'evse.evcs.bill_constraints_data',
            'evse.evcs.bill_data',
            'evse.evcs.bill_description_data',
            'evse.evcs.bill_writeable',
            'evse.evcs.brand_name',
            'evse.evcs.device_code',
            'evse.evcs.electrical_connection_id',
            'evse.evcs.evcs_009',
            'evse.evcs.hardware_revision',
            'evse.evcs.manufacturer_label',
            'evse.evcs.permitted_value_set',
            'evse.evcs.position',
            'evse.evcs.position_count_max',
            'evse.evcs.position_count_min',
            'evse.evcs.scope_type',
            'evse.evcs.serial_number',
            'evse.evcs.software_revision',
            'evse.evcs.supported_bill_type',
            'evse.evcs.total',
            'evse.evcs.use_case_name',
            'evse.evcs.use_case_version',
            'evse.evcs.vendor_code',
            'evse.evcs.vendor_name',
            'evse.evsecc.actor',
            'evse.evsecc.brand_name',
            'evse.evsecc.device_code',
            'evse.evsecc.device_name',
            'evse.evsecc.electrical_connection_id',
            'evse.evsecc.hardware_revision',
            'evse.evsecc.manufacturer_label',
            'evse.evsecc.operating_state',
            'evse.evsecc.permitted_value_set',
            'evse.evsecc.scope_type',
            'evse.evsecc.serial_number',
            'evse.evsecc.software_revision',
            'evse.evsecc.use_case_name',
            'evse.evsecc.use_case_version',
            'evse.evsecc.vendor_code',
            'evse.evsecc.vendor_name',
            'evse.evsoc.actor',
            'evse.evsoc.brand_name',
            'evse.evsoc.characteristic_context',
            'evse.evsoc.commodity_type',
            'evse.evsoc.current',
            'evse.evsoc.device_code',
            'evse.evsoc.electrical_connection_id',
            'evse.evsoc.evsoc_002',
            'evse.evsoc.hardware_revision',
            'evse.evsoc.manufacturer_label',
            'evse.evsoc.measurement_constraints_data',
            'evse.evsoc.measurement_id',
            'evse.evsoc.measurement_type',
            'evse.evsoc.permitted_value_set',
            'evse.evsoc.scope_type',
            'evse.evsoc.serial_number',
            'evse.evsoc.software_revision',
            'evse.evsoc.timestamp',
            'evse.evsoc.use_case_name',
            'evse.evsoc.use_case_version',
            'evse.evsoc.value_range_min',
            'evse.evsoc.value_source',
            'evse.evsoc.value_state',
            'evse.evsoc.vendor_code',
            'evse.evsoc.vendor_name',
            'evse.opev.actor',
            'evse.opev.brand_name',
            'evse.opev.device_code',
            'evse.opev.electrical_connection_id',
            'evse.opev.hardware_revision',
            'evse.opev.heartbeat_counter',
            'evse.opev.heartbeat_timeout',
            'evse.opev.heartbeat_timestamp',
            'evse.opev.is_limit_changeable',
            'evse.opev.last_error_code',
            'evse.opev.limit_category',
            'evse.opev.limit_type',
            'evse.opev.load_control_limit_data',
            'evse.opev.load_control_limit_description_data',
            'evse.opev.manufacturer_label',
            'evse.opev.measurement_id',
            'evse.opev.opev_004',
            'evse.opev.parameter_id',
            'evse.opev.permitted_value_set',
            'evse.opev.scale',
            'evse.opev.scope_type',
            'evse.opev.serial_number',
            'evse.opev.software_revision',
            'evse.opev.unit',
            'evse.opev.use_case_name',
            'evse.opev.use_case_version',
            'evse.opev.vendor_code',
            'evse.opev.vendor_name',
            'evse.oscev.actor',
            'evse.oscev.brand_name',
            'evse.oscev.device_code',
            'evse.oscev.electrical_connection_id',
            'evse.oscev.hardware_revision',
            'evse.oscev.heartbeat_counter',
            'evse.oscev.heartbeat_timeout',
            'evse.oscev.heartbeat_timestamp',
            'evse.oscev.is_limit_changeable',
            'evse.oscev.limit_category',
            'evse.oscev.limit_type',
            'evse.oscev.load_control_limit_data',
            'evse.oscev.load_control_limit_description_data',
            'evse.oscev.manufacturer_label',
            'evse.oscev.measurement_id',
            'evse.oscev.operating_state',
            'evse.oscev.parameter_id',
            'evse.oscev.permitted_value_set',
            'evse.oscev.scale',
            'evse.oscev.scope_type',
            'evse.oscev.serial_number',
            'evse.oscev.software_revision',
            'evse.oscev.unit',
            'evse.oscev.use_case_name',
            'evse.oscev.use_case_version',
            'evse.oscev.vendor_code',
            'evse.oscev.vendor_name',
        }
        energy_rows = {
            "energy.capability.adjust_power",
            "energy.capability.adjust_start_time",
            "energy.capability.modify_series_slot",
            "energy.capability.read.subject",
            "energy.capability.schedule_sequence",
            "energy.capability.set_consumption_failsafe",
            "energy.capability.set_consumption_limit",
            "energy.capability.set_energy_balance",
            "energy.capability.set_esa_mode",
            "energy.capability.set_esa_state",
            "energy.capability.set_low_power_sensitivity",
            "energy.capability.set_production_failsafe",
            "energy.capability.set_production_limit",
            "energy.capability.set_sequence_state",
            "energy.esa.adjustment_cause",
            "energy.esa.adjustment_end_cause",
            "energy.esa.adjustment_maximum_duration",
            "energy.esa.adjustment_maximum_power",
            "energy.esa.adjustment_minimum_duration",
            "energy.esa.adjustment_minimum_power",
            "energy.esa.can_generate",
            "energy.esa.maximum_power",
            "energy.esa.minimum_power",
            "energy.esa.mode",
            "energy.esa.mode_supported",
            "energy.esa.opt_out",
            "energy.esa.request_cause",
            "energy.esa.requested_duration",
            "energy.esa.requested_power",
            "energy.esa.state",
            "energy.esa.type",
            "energy.heartbeat.status",
            "energy.heartbeat.timeout",
            "energy.limit.consumption_active",
            "energy.limit.consumption_active_power",
            "energy.limit.consumption_duration",
            "energy.limit.consumption_failsafe_duration_minimum",
            "energy.limit.consumption_failsafe_power",
            "energy.limit.production_active",
            "energy.limit.production_active_power",
            "energy.limit.production_duration",
            "energy.limit.production_failsafe_duration_minimum",
            "energy.limit.production_failsafe_power",
            "energy.limit.state",
            "energy.manager.state",
            "energy.nameplate.consumption_contractual_maximum",
            "energy.nameplate.consumption_nominal_maximum",
            "energy.nameplate.production_contractual_maximum",
            "energy.nameplate.production_nominal_maximum",
            "energy.operation.adjust_power",
            "energy.operation.adjust_start_time",
            "energy.operation.modify_series_slot",
            "energy.operation.schedule_sequence",
            "energy.operation.set_consumption_failsafe",
            "energy.operation.set_consumption_limit",
            "energy.operation.set_energy_balance",
            "energy.operation.set_esa_mode",
            "energy.operation.set_esa_state",
            "energy.operation.set_low_power_sensitivity",
            "energy.operation.set_production_failsafe",
            "energy.operation.set_production_limit",
            "energy.operation.set_sequence_state",
            "energy.preference.balance_label",
            "energy.preference.balance_step",
            "energy.preference.current_balance",
            "energy.preference.low_power_sensitivity",
            "energy.preference.priorities",
            "energy.sequence.active_duration_maximum",
            "energy.sequence.active_duration_minimum",
            "energy.sequence.earliest_start",
            "energy.sequence.latest_end",
            "energy.sequence.pausable",
            "energy.sequence.pause_duration_maximum",
            "energy.sequence.pause_duration_minimum",
            "energy.sequence.scheduled_start",
            "energy.sequence.slot_duration",
            "energy.sequence.slot_power_expected",
            "energy.sequence.slot_power_maximum",
            "energy.sequence.slot_power_minimum",
            "energy.sequence.state",
            "energy.sequence.stoppable",
            "energy.series.constraint_maximum_slots",
            "energy.series.constraint_minimum_slot_duration",
            "energy.series.constraint_slot_value_step",
            "energy.series.earliest_start",
            "energy.series.end",
            "energy.series.identifier",
            "energy.series.latest_end",
            "energy.series.pausable",
            "energy.series.slot_adjustment_maximum_duration",
            "energy.series.slot_adjustment_maximum_power",
            "energy.series.slot_adjustment_minimum_duration",
            "energy.series.slot_adjustment_minimum_power",
            "energy.series.slot_default_duration",
            "energy.series.slot_duration",
            "energy.series.slot_elapsed",
            "energy.series.slot_energy_nominal",
            "energy.series.slot_maximum_duration",
            "energy.series.slot_maximum_pause",
            "energy.series.slot_minimum_duration",
            "energy.series.slot_minimum_pause",
            "energy.series.slot_pausable",
            "energy.series.slot_power_maximum",
            "energy.series.slot_power_minimum",
            "energy.series.slot_power_nominal",
            "energy.series.slot_remaining",
            "energy.series.slot_start",
            "energy.series.slot_state",
            "energy.series.start",
            "energy.series.update_reason",
        }
        qu08_energy = {
            "energy.capability.read.tariff",
            "energy.capability.set_direct_control_activity_state",
            "energy.capability.set_direct_control_energy",
            "energy.capability.set_direct_control_energy_mode",
            "energy.capability.set_direct_control_power",
            "energy.capability.set_local_generation_available",
            "energy.capability.write_incentive_slot",
            "energy.direct_control.activity_state",
            "energy.direct_control.energy",
            "energy.direct_control.energy_mode",
            "energy.direct_control.energy_unit",
            "energy.direct_control.is_activity_state_changeable",
            "energy.direct_control.is_energy_changeable",
            "energy.direct_control.is_energy_mode_changeable",
            "energy.direct_control.is_power_changeable",
            "energy.direct_control.positive_energy_direction",
            "energy.direct_control.power",
            "energy.direct_control.power_unit",
            "energy.direct_control.sequence_id",
            "energy.direct_control.timestamp",
            "energy.grid.carbon_intensity",
            "energy.grid.carbon_level",
            "energy.grid.end",
            "energy.grid.local_carbon_intensity",
            "energy.grid.local_carbon_level",
            "energy.grid.local_generation_available",
            "energy.grid.start",
            "energy.incentive.boundary_lower",
            "energy.incentive.boundary_upper",
            "energy.incentive.co2_intensity",
            "energy.incentive.incentive_kind",
            "energy.incentive.incentive_value",
            "energy.incentive.maximum_slots",
            "energy.incentive.maximum_tiers",
            "energy.incentive.renewable_ratio",
            "energy.incentive.slot_end",
            "energy.incentive.slot_start",
            "energy.incentive.tier_kind",
            "energy.itpcm.actor",
            "energy.itpcm.committed_power_plan",
            "energy.itpcm.itpcm_031",
            "energy.itpcm.per",
            "energy.itpcm.simple_committed_incentive_table",
            "energy.itpcm.slots",
            "energy.itpcm.use_case_name",
            "energy.itpcm.use_case_version",
            "energy.itpcm.value_range_min",
            "energy.lpc.actor",
            "energy.lpc.committed_power_plan",
            "energy.lpc.heartbeat_counter",
            "energy.lpc.heartbeat_timestamp",
            "energy.lpc.per",
            "energy.lpc.slots",
            "energy.lpc.use_case_name",
            "energy.lpc.use_case_version",
            "energy.lpc.value_range_min",
            "energy.lpp.actor",
            "energy.lpp.committed_power_plan",
            "energy.lpp.heartbeat_counter",
            "energy.lpp.heartbeat_timestamp",
            "energy.lpp.per",
            "energy.lpp.slots",
            "energy.lpp.use_case_name",
            "energy.lpp.use_case_version",
            "energy.lpp.value_range_min",
            "energy.metering.maximum_quantities",
            "energy.metering.quantity",
            "energy.metering.timestamp",
            "energy.negotiation.request_timeout",
            "energy.negotiation.simulation_concurrent",
            "energy.negotiation.simulation_cycles_maximum",
            "energy.negotiation.writeable_wait",
            "energy.ohpcf.active_duration_min",
            "energy.ohpcf.actor",
            "energy.ohpcf.alternatives",
            "energy.ohpcf.alternatives_count",
            "energy.ohpcf.committed_power_plan",
            "energy.ohpcf.default_duration",
            "energy.ohpcf.earliest_start_time",
            "energy.ohpcf.elapsed_slot_time",
            "energy.ohpcf.flexibility",
            "energy.ohpcf.is_pausable",
            "energy.ohpcf.is_stoppable",
            "energy.ohpcf.latest_end_time",
            "energy.ohpcf.pause_duration_min",
            "energy.ohpcf.per",
            "energy.ohpcf.remaining_slot_time",
            "energy.ohpcf.sequence_id",
            "energy.ohpcf.slots",
            "energy.ohpcf.supports_reselection",
            "energy.ohpcf.total_sequences_count_max",
            "energy.ohpcf.use_case_name",
            "energy.ohpcf.use_case_version",
            "energy.ohpcf.value_range_min",
            "energy.operation.set_direct_control_activity_state",
            "energy.operation.set_direct_control_energy",
            "energy.operation.set_direct_control_energy_mode",
            "energy.operation.set_direct_control_power",
            "energy.operation.set_local_generation_available",
            "energy.operation.write_incentive_slot",
            "energy.podf.actor",
            "energy.podf.committed_power_plan",
            "energy.podf.per",
            "energy.podf.slots",
            "energy.podf.use_case_name",
            "energy.podf.use_case_version",
            "energy.podf.value_range_min",
            "energy.poen.actor",
            "energy.poen.committed_power_plan",
            "energy.poen.per",
            "energy.poen.slots",
            "energy.poen.use_case_name",
            "energy.poen.use_case_version",
            "energy.poen.value_range_min",
            "energy.price.current",
            "energy.price.current_description",
            "energy.price.current_end",
            "energy.price.current_level",
            "energy.price.current_start",
            "energy.price.forecast_end",
            "energy.price.forecast_level",
            "energy.price.forecast_price",
            "energy.price.forecast_start",
            "energy.tariff.block_mode",
            "energy.tariff.calendar_period_pattern",
            "energy.tariff.calendar_period_start",
            "energy.tariff.component_apparent_power_threshold",
            "energy.tariff.component_auxiliary_load",
            "energy.tariff.component_friendly_credit",
            "energy.tariff.component_label",
            "energy.tariff.component_peak_period",
            "energy.tariff.component_power_threshold",
            "energy.tariff.component_predicted",
            "energy.tariff.component_price",
            "energy.tariff.component_price_kind",
            "energy.tariff.component_threshold",
            "energy.tariff.currency",
            "energy.tariff.current_components",
            "energy.tariff.current_day",
            "energy.tariff.current_day_entry",
            "energy.tariff.current_day_entry_date",
            "energy.tariff.day_entry_duration",
            "energy.tariff.day_entry_randomization_offset",
            "energy.tariff.day_entry_start",
            "energy.tariff.day_pattern_days",
            "energy.tariff.day_pattern_entry",
            "energy.tariff.direction",
            "energy.tariff.individual_day_date",
            "energy.tariff.individual_day_entry",
            "energy.tariff.individual_day_kind",
            "energy.tariff.label",
            "energy.tariff.next_components",
            "energy.tariff.next_day",
            "energy.tariff.next_day_entry",
            "energy.tariff.next_day_entry_date",
            "energy.tariff.period_component",
            "energy.tariff.period_entry",
            "energy.tariff.period_label",
            "energy.tariff.price_kind",
            "energy.tariff.provider",
            "energy.tariff.randomization_kind",
            "energy.tariff.randomization_offset",
            "energy.tariff.start",
            "energy.tariff.status",
            "energy.tariff.unit_basis",
            "energy.task.description",
            "energy.task.direct_control_related",
            "energy.task.elapsed_time",
            "energy.task.hvac_related",
            "energy.task.hvac_related_overrun_id",
            "energy.task.job_id",
            "energy.task.job_source",
            "energy.task.job_state",
            "energy.task.jobs_active",
            "energy.task.label",
            "energy.task.load_control_releated",
            "energy.task.load_control_releated_event_id",
            "energy.task.power_sequences_related",
            "energy.task.power_sequences_related_sequence_id",
            "energy.task.remaining_time",
            "energy.task.remote_controllable",
            "energy.task.smart_energy_management_ps_related",
            "energy.task.smart_energy_management_ps_related_sequence_id",
            "energy.task.timestamp",
            "energy.tout.actor",
            "energy.tout.committed_power_plan",
            "energy.tout.per",
            "energy.tout.slots",
            "energy.tout.use_case_name",
            "energy.tout.use_case_version",
            "energy.tout.value_range_min",
        }
        qu09_thermal = {
            "thermal.action.zone_state",
            "thermal.calibration.temperature_offset",
            "thermal.capability.read.function",
            "thermal.capability.read.sensor",
            "thermal.capability.set_active_preset",
            "thermal.capability.set_active_program",
            "thermal.capability.set_control_sequence",
            "thermal.capability.set_display_unit",
            "thermal.capability.set_emergency_heat_delta",
            "thermal.capability.set_hold",
            "thermal.capability.set_keypad_lockout",
            "thermal.capability.set_maximum_cooling_setpoint",
            "thermal.capability.set_maximum_heating_setpoint",
            "thermal.capability.set_minimum_cooling_setpoint",
            "thermal.capability.set_minimum_heating_setpoint",
            "thermal.capability.set_occupied_cooling",
            "thermal.capability.set_occupied_heating",
            "thermal.capability.set_preset",
            "thermal.capability.set_program_entry",
            "thermal.capability.set_remote_sensing",
            "thermal.capability.set_schedule_programming",
            "thermal.capability.set_suggestion",
            "thermal.capability.set_temperature_calibration",
            "thermal.capability.set_unoccupied_cooling",
            "thermal.capability.set_unoccupied_heating",
            "thermal.capability.set_zone_cooling_mode",
            "thermal.capability.set_zone_mode",
            "thermal.configuration.control_sequence",
            "thermal.configuration.display_unit",
            "thermal.configuration.emergency_heat_delta",
            "thermal.configuration.keypad_lockout",
            "thermal.configuration.remote_sensing",
            "thermal.configuration.schedule_programming",
            "thermal.demand.cooling",
            "thermal.demand.heating",
            "thermal.hold.duration",
            "thermal.hold.expiry",
            "thermal.hold.setpoint",
            "thermal.hold.state",
            "thermal.limit.absolute_maximum_cooling_setpoint",
            "thermal.limit.absolute_maximum_heating_setpoint",
            "thermal.limit.absolute_minimum_cooling_setpoint",
            "thermal.limit.absolute_minimum_heating_setpoint",
            "thermal.limit.maximum_cooling_setpoint",
            "thermal.limit.maximum_heating_setpoint",
            "thermal.limit.minimum_cooling_setpoint",
            "thermal.limit.minimum_heating_setpoint",
            "thermal.limit.minimum_setpoint_deadband",
            "thermal.limit.setpoint_step",
            "thermal.measurement.sensor_humidity",
            "thermal.measurement.sensor_temperature",
            "thermal.mode.zone_cooling",
            "thermal.operation.set_active_preset",
            "thermal.operation.set_active_program",
            "thermal.operation.set_control_sequence",
            "thermal.operation.set_display_unit",
            "thermal.operation.set_emergency_heat_delta",
            "thermal.operation.set_hold",
            "thermal.operation.set_keypad_lockout",
            "thermal.operation.set_maximum_cooling_setpoint",
            "thermal.operation.set_maximum_heating_setpoint",
            "thermal.operation.set_minimum_cooling_setpoint",
            "thermal.operation.set_minimum_heating_setpoint",
            "thermal.operation.set_occupied_cooling",
            "thermal.operation.set_occupied_heating",
            "thermal.operation.set_preset",
            "thermal.operation.set_program_entry",
            "thermal.operation.set_remote_sensing",
            "thermal.operation.set_schedule_programming",
            "thermal.operation.set_suggestion",
            "thermal.operation.set_temperature_calibration",
            "thermal.operation.set_unoccupied_cooling",
            "thermal.operation.set_unoccupied_heating",
            "thermal.operation.set_zone_cooling_mode",
            "thermal.operation.set_zone_mode",
            "thermal.preset.active_handle",
            "thermal.preset.built_in",
            "thermal.preset.cooling_setpoint",
            "thermal.preset.heating_setpoint",
            "thermal.preset.maximum_count",
            "thermal.preset.name",
            "thermal.preset.scenario",
            "thermal.preset.supported_scenarios",
            "thermal.program.active_handle",
            "thermal.program.built_in",
            "thermal.program.entry_cooling_setpoint",
            "thermal.program.entry_days",
            "thermal.program.entry_end",
            "thermal.program.entry_heating_setpoint",
            "thermal.program.entry_preset",
            "thermal.program.entry_start",
            "thermal.program.entry_state",
            "thermal.program.entry_system_mode",
            "thermal.program.maximum_count",
            "thermal.program.maximum_entries",
            "thermal.program.maximum_entries_per_day",
            "thermal.program.name",
            "thermal.program.preset",
            "thermal.program.supported_types",
            "thermal.program.system_mode",
            "thermal.setpoint.change_amount",
            "thermal.setpoint.change_source",
            "thermal.setpoint.change_time",
            "thermal.status.occupancy",
            "thermal.status.window",
            "thermal.status.zone_running_state",
            "thermal.suggestion.active",
            "thermal.suggestion.current",
            "thermal.suggestion.effective_time",
            "thermal.suggestion.expiration",
            "thermal.suggestion.maximum_count",
            "thermal.suggestion.not_following_reason",
            "thermal.suggestion.preset",
        }
        qu10_thermal = {
            "thermal.capability.enable_detector_alarm",
            "thermal.capability.reset_water_tank",
            "thermal.capability.set_detector_sensitivity",
            "thermal.capability.set_dhw_boost",
            "thermal.capability.set_dhw_mode",
            "thermal.capability.set_dhw_temperature",
            "thermal.capability.set_pump_control_mode",
            "thermal.capability.set_pump_level",
            "thermal.capability.set_pump_operation_mode",
            "thermal.capability.set_pump_running",
            "thermal.capability.set_valve_default_open_duration",
            "thermal.capability.set_valve_default_open_level",
            "thermal.capability.set_valve_level",
            "thermal.capability.set_valve_state",
            "thermal.capability.suppress_detector_alarm",
            "thermal.configuration.valve_default_open_duration",
            "thermal.configuration.valve_default_open_level",
            "thermal.configuration.valve_level_step",
            "thermal.detector.alarms_active",
            "thermal.detector.alarms_enabled",
            "thermal.detector.alarms_supported",
            "thermal.detector.alarms_suppressed",
            "thermal.detector.default_sensitivity_level",
            "thermal.detector.sensitivity_level",
            "thermal.detector.sensor_fault",
            "thermal.detector.supported_sensitivity_levels",
            "thermal.dhw.boost_duration",
            "thermal.dhw.boost_emergency",
            "thermal.dhw.boost_one_shot",
            "thermal.dhw.boost_state",
            "thermal.dhw.boost_target_ratio",
            "thermal.dhw.boost_target_reheat_ratio",
            "thermal.dhw.boost_temporary_setpoint",
            "thermal.dhw.charge_ratio",
            "thermal.dhw.estimated_heat_required",
            "thermal.dhw.heat_demand",
            "thermal.dhw.heater_types",
            "thermal.energy.pump_consumed",
            "thermal.measurement.circuit_humidity",
            "thermal.measurement.circuit_return_temperature",
            "thermal.measurement.circuit_water_pressure",
            "thermal.measurement.collector_temperature",
            "thermal.measurement.dew_point",
            "thermal.measurement.dhw_circuit_flow_temperature",
            "thermal.measurement.dhw_circuit_return_temperature",
            "thermal.measurement.dhw_flow_rate",
            "thermal.measurement.heat_generator_flow_rate",
            "thermal.measurement.pump_capacity",
            "thermal.measurement.pump_flow_rate",
            "thermal.measurement.pump_medium_temperature",
            "thermal.measurement.pump_power",
            "thermal.measurement.pump_pressure",
            "thermal.measurement.pump_running_time",
            "thermal.measurement.solar_flow_temperature",
            "thermal.measurement.solar_power",
            "thermal.measurement.solar_return_temperature",
            "thermal.measurement.store_bottom_temperature",
            "thermal.measurement.store_top_temperature",
            "thermal.measurement.system_water_pressure",
            "thermal.measurement.valve_flow_rate",
            "thermal.measurement.valve_level",
            "thermal.mode.dhw",
            "thermal.mode.dhw_supported",
            "thermal.mode.pump_control",
            "thermal.mode.pump_effective_control",
            "thermal.mode.pump_effective_operation",
            "thermal.mode.pump_operation",
            "thermal.nameplate.pump_maximum_compensated_pressure",
            "thermal.nameplate.pump_maximum_constant_flow",
            "thermal.nameplate.pump_maximum_constant_pressure",
            "thermal.nameplate.pump_maximum_constant_speed",
            "thermal.nameplate.pump_maximum_constant_temperature",
            "thermal.nameplate.pump_maximum_flow",
            "thermal.nameplate.pump_maximum_pressure",
            "thermal.nameplate.pump_maximum_speed",
            "thermal.nameplate.pump_minimum_compensated_pressure",
            "thermal.nameplate.pump_minimum_constant_flow",
            "thermal.nameplate.pump_minimum_constant_pressure",
            "thermal.nameplate.pump_minimum_constant_speed",
            "thermal.nameplate.pump_minimum_constant_temperature",
            "thermal.nameplate.store_volume",
            "thermal.operation.enable_detector_alarm",
            "thermal.operation.reset_water_tank",
            "thermal.operation.set_detector_sensitivity",
            "thermal.operation.set_dhw_boost",
            "thermal.operation.set_dhw_mode",
            "thermal.operation.set_dhw_temperature",
            "thermal.operation.set_pump_control_mode",
            "thermal.operation.set_pump_level",
            "thermal.operation.set_pump_operation_mode",
            "thermal.operation.set_pump_running",
            "thermal.operation.set_valve_default_open_duration",
            "thermal.operation.set_valve_default_open_level",
            "thermal.operation.set_valve_level",
            "thermal.operation.set_valve_state",
            "thermal.operation.suppress_detector_alarm",
            "thermal.setpoint.pump_level",
            "thermal.setpoint.valve_target_level",
            "thermal.setpoint.valve_target_state",
            "thermal.status.freeze",
            "thermal.status.leak",
            "thermal.status.pump",
            "thermal.status.pump_alarms",
            "thermal.status.pump_running",
            "thermal.status.valve_faults",
            "thermal.status.valve_state",
            "thermal.valve.auto_close_time",
            "thermal.valve.open_duration",
            "thermal.valve.remaining_duration",
            "thermal.water_tank.change_indication",
            "thermal.water_tank.condition",
            "thermal.water_tank.degradation_direction",
            "thermal.water_tank.in_place",
            "thermal.water_tank.last_changed",
            "thermal.water_tank.replacement_product_identifier",
        }
        qu11_thermal = {
            "thermal.air.level",
            "thermal.air.mass_concentration",
            "thermal.air.measurement_medium",
            "thermal.air.radon_concentration",
            "thermal.air.statistic_window",
            "thermal.air.uncertainty",
            "thermal.air.volume_fraction",
            "thermal.capability.reset_filter",
            "thermal.capability.set_circuit_fixed_flow_temperature",
            "thermal.capability.set_circuit_flow_temperature_maximum",
            "thermal.capability.set_circuit_flow_temperature_minimum",
            "thermal.capability.set_fan_airflow_direction",
            "thermal.capability.set_fan_mode",
            "thermal.capability.set_fan_rock",
            "thermal.capability.set_fan_speed",
            "thermal.capability.set_fan_step",
            "thermal.capability.set_fan_wind",
            "thermal.capability.set_filter_last_changed",
            "thermal.capability.set_heat_generator_flow_temperature",
            "thermal.capability.set_louver_position",
            "thermal.capability.set_overrun_hvac_system_off",
            "thermal.capability.set_overrun_one_day_at_home",
            "thermal.capability.set_overrun_one_day_away",
            "thermal.capability.set_overrun_one_time_dhw",
            "thermal.capability.set_overrun_one_time_ventilation",
            "thermal.capability.set_overrun_party",
            "thermal.capability.set_overrun_sg_ready_condition_1",
            "thermal.capability.set_overrun_sg_ready_condition_3",
            "thermal.capability.set_overrun_sg_ready_condition_4",
            "thermal.capability.set_overrun_valve_kick",
            "thermal.capability.set_terminal_unit_cooling",
            "thermal.capability.set_terminal_unit_heating",
            "thermal.capability.set_terminal_unit_mode",
            "thermal.capability.set_terminal_unit_power",
            "thermal.capability.set_ventilation_level",
            "thermal.capability.set_ventilation_mode",
            "thermal.configuration.ac_type",
            "thermal.configuration.compressor_type",
            "thermal.configuration.refrigerant_type",
            "thermal.energy.electrical_consumed",
            "thermal.energy.solar_yield",
            "thermal.fan.airflow_direction",
            "thermal.fan.mode",
            "thermal.fan.mode_sequence",
            "thermal.fan.rock_setting",
            "thermal.fan.rock_support",
            "thermal.fan.speed_ratio",
            "thermal.fan.speed_setting",
            "thermal.fan.speed_step",
            "thermal.fan.speed_step_maximum",
            "thermal.fan.speed_step_setting",
            "thermal.fan.wind_setting",
            "thermal.fan.wind_support",
            "thermal.filter.change_indication",
            "thermal.filter.condition",
            "thermal.filter.degradation_direction",
            "thermal.filter.in_place",
            "thermal.filter.kind",
            "thermal.filter.last_changed",
            "thermal.filter.replacement_product_identifier",
            "thermal.filter.replacement_product_kind",
            "thermal.limit.circuit_flow_temperature_maximum",
            "thermal.limit.circuit_flow_temperature_minimum",
            "thermal.measurement.air_quality",
            "thermal.measurement.coil_temperature",
            "thermal.measurement.electrical_power",
            "thermal.measurement.exhaust_air_temperature",
            "thermal.measurement.extract_air_flow",
            "thermal.measurement.extract_air_temperature",
            "thermal.measurement.louver_position",
            "thermal.measurement.outdoor_air_temperature_average",
            "thermal.measurement.outdoor_intake_air_temperature",
            "thermal.measurement.supply_air_flow",
            "thermal.measurement.supply_air_temperature",
            "thermal.measurement.terminal_unit_air_temperature",
            "thermal.measurement.terminal_unit_humidity",
            "thermal.mode.ventilation",
            "thermal.nameplate.cooling_capacity",
            "thermal.operation.reset_filter",
            "thermal.operation.set_circuit_fixed_flow_temperature",
            "thermal.operation.set_circuit_flow_temperature_maximum",
            "thermal.operation.set_circuit_flow_temperature_minimum",
            "thermal.operation.set_fan_airflow_direction",
            "thermal.operation.set_fan_mode",
            "thermal.operation.set_fan_rock",
            "thermal.operation.set_fan_speed",
            "thermal.operation.set_fan_step",
            "thermal.operation.set_fan_wind",
            "thermal.operation.set_filter_last_changed",
            "thermal.operation.set_heat_generator_flow_temperature",
            "thermal.operation.set_louver_position",
            "thermal.operation.set_overrun_hvac_system_off",
            "thermal.operation.set_overrun_one_day_at_home",
            "thermal.operation.set_overrun_one_day_away",
            "thermal.operation.set_overrun_one_time_dhw",
            "thermal.operation.set_overrun_one_time_ventilation",
            "thermal.operation.set_overrun_party",
            "thermal.operation.set_overrun_sg_ready_condition_1",
            "thermal.operation.set_overrun_sg_ready_condition_3",
            "thermal.operation.set_overrun_sg_ready_condition_4",
            "thermal.operation.set_overrun_valve_kick",
            "thermal.operation.set_terminal_unit_cooling",
            "thermal.operation.set_terminal_unit_heating",
            "thermal.operation.set_terminal_unit_mode",
            "thermal.operation.set_terminal_unit_power",
            "thermal.operation.set_ventilation_level",
            "thermal.operation.set_ventilation_mode",
            "thermal.setpoint.circuit_fixed_flow_temperature",
            "thermal.setpoint.circuit_flow_temperature",
            "thermal.setpoint.heat_generator_flow_temperature",
            "thermal.setpoint.terminal_unit_cooling",
            "thermal.setpoint.terminal_unit_heating",
            "thermal.status.terminal_unit_errors",
            "thermal.status.terminal_unit_power",
        }
        qu12_equipment = {
            "equipment.capability.read.resource",
            "equipment.capability.read.unit",
            "equipment.capability.set_label",
            "equipment.diagnosis.last_error_code",
            "equipment.diagnosis.operating_state",
            "equipment.diagnosis.operating_time",
            "equipment.diagnosis.vendor_state_code",
            "equipment.identification.brand_name",
            "equipment.identification.hardware_revision",
            "equipment.identification.hardware_version",
            "equipment.identification.manufacturing_date",
            "equipment.identification.part_number",
            "equipment.identification.power_source_kind",
            "equipment.identification.product_code",
            "equipment.identification.product_description",
            "equipment.identification.product_label",
            "equipment.identification.product_name",
            "equipment.identification.product_url",
            "equipment.identification.serial_number",
            "equipment.identification.software_revision",
            "equipment.identification.software_version",
            "equipment.identification.vendor_code",
            "equipment.identification.vendor_name",
            "equipment.label.description",
            "equipment.label.name",
            "equipment.message.kind",
            "equipment.message.text",
            "equipment.message.time",
            "equipment.operation.set_label",
            "equipment.power.battery_ansi_designation",
            "equipment.power.battery_capacity",
            "equipment.power.battery_charge_faults",
            "equipment.power.battery_charge_level",
            "equipment.power.battery_charge_ratio",
            "equipment.power.battery_charge_state",
            "equipment.power.battery_charging_current",
            "equipment.power.battery_chemistry",
            "equipment.power.battery_common_designation",
            "equipment.power.battery_faults",
            "equipment.power.battery_functional_while_charging",
            "equipment.power.battery_iec_designation",
            "equipment.power.battery_present",
            "equipment.power.battery_quantity",
            "equipment.power.battery_replaceability",
            "equipment.power.battery_replacement_description",
            "equipment.power.battery_replacement_needed",
            "equipment.power.battery_time_remaining",
            "equipment.power.battery_time_to_full",
            "equipment.power.battery_voltage",
            "equipment.power.source_description",
            "equipment.power.source_order",
            "equipment.power.source_status",
            "equipment.power.wired_current",
            "equipment.power.wired_current_type",
            "equipment.power.wired_faults",
            "equipment.power.wired_input_frequency",
            "equipment.power.wired_input_voltage",
            "equipment.power.wired_maximum_current",
            "equipment.power.wired_nominal_voltage",
            "equipment.power.wired_present",
            "equipment.status.reachable",
            "equipment.time.current",
            "equipment.time.timezone",
        }
        self.assertEqual({row['ref']['id'] for row in extra}, pilot | ep01_pv_accuracy | cr02_accuracy | room | new_facts | storage_rows | evse_rows | energy_rows | qu08_energy | qu09_thermal | qu10_thermal | qu11_thermal | qu12_equipment)
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

    def test_event_is_never_a_requested_item_mutant(self):
        # requested: installing an event request is rejected. The production
        # row keeps requested null because an event is not a kernel-v1 item.
        i = self.first('event')
        row = self.document['rows'][i]
        self.reject(check_source, ('rows', i, 'source', 'requested'),
                    {'kind': 'event', 'item_id': row['ref']['id'],
                     'item_version': row['ref']['version']})

    def test_catalog_events_stay_unmapped_without_a_target(self):
        rows = {(r['ref']['id'], r['kind']): r for r in self.document['rows']}
        seen = 0
        for element, kind in items():
            if kind != 'event':
                continue
            seen += 1
            row = rows[(element['ref']['id'], 'event')]
            self.assertEqual(row['disposition'], 'unknown')
            self.assertEqual(row['reason'], 'matter.unmapped.v1')
            self.assertNotIn('target', row)
        self.assertGreater(seen, 0)

    def test_pilot_accuracy_rows_stay_unknown_without_a_target(self):
        # Expectations are literal ids from the Matter field list: no cited
        # one-target conversion exists for a field of the Accuracy struct.
        rows = {r['ref']['id']: r for r in self.document['rows']}
        for ident in ('pv.accuracy.measured', 'pv.accuracy.ratio_maximum',
                      'infrastructure.accuracy.measured',
                      'infrastructure.accuracy.ratio_maximum',
                      'evse.ac.active_power'):
            with self.subTest(ident=ident):
                row = rows[ident]
                self.assertEqual(row['disposition'], 'unknown')
                self.assertEqual(row['reason'], 'matter.unmapped.v1')
                self.assertNotIn('target', row)
        transformed = [r['ref']['id'] for r in self.document['rows']
                       if r['disposition'] in ('exact', 'transformed')]
        self.assertEqual(transformed, ['evse.ac.current'])

    def test_pilot_unsourced_values_are_named(self):
        pilot = self.document['electrical_sensor_pilot']
        self.assertEqual(pilot['declared_values'], [])
        named = {(e['cluster_id'], e['attribute']) for e in pilot['unsourced']}
        for key in [(156, 'FeatureMap'), (144, 'FeatureMap'), (144, 'PowerMode'),
                    (144, 'NumberOfMeasurementTypes')]:
            with self.subTest(value=key):
                self.assertIn(key, named)

    def test_pilot_unsourced_entry_field_mutants(self):
        # Each field of an entry is varied alone; the production mutation it
        # catches is the same field changed in the descriptor.
        # cluster: a value moved to the other cluster; cluster_id: a wrong id;
        # attribute: a renamed value; attribute_id: a wrong id; status: a
        # value called sourced; reason: an erased reason.
        for i, _ in enumerate(PILOT_UNSOURCED):
            for field, value in [('cluster', 'Other'), ('cluster_id', 1),
                                 ('attribute', 'Other'), ('attribute_id', 9999),
                                 ('status', 'declared'), ('reason', '')]:
                with self.subTest(entry=i, field=field):
                    self.reject(check_pilot,
                                ('electrical_sensor_pilot', 'unsourced', i, field), value)

    def test_pilot_declared_value_and_dropped_entry_mutants(self):
        self.reject(check_pilot, ('electrical_sensor_pilot', 'declared_values'),
                    [{'attribute': 'PowerMode', 'value': 0}])
        self.reject(check_pilot, ('electrical_sensor_pilot', 'unsourced'),
                    self.document['electrical_sensor_pilot']['unsourced'][1:])
        self.reject(check_pilot, ('electrical_sensor_pilot', 'device_type_id'), 1295)

    def test_pv_measured_range_and_accuracy_range_rows_are_unknown(self):
        """One unknown row per added element, each with its own subtests.

        Expectations are literal ids, never read back from the catalog.
        """
        rows = {r['ref']['id']: r for r in self.document['rows']}
        expected = [
            'pv.accuracy.measured_minimum_active_current',
            'pv.accuracy.measured_maximum_active_current',
            'pv.accuracy.range_minimum_active_current',
            'pv.accuracy.range_maximum_active_current',
            'pv.accuracy.measured_minimum_active_power',
            'pv.accuracy.measured_maximum_active_power',
            'pv.accuracy.range_minimum_active_power',
            'pv.accuracy.range_maximum_active_power',
        ]
        for ident in expected:
            with self.subTest(ident=ident):
                row = rows[ident]
                self.assertEqual(row['kind'], 'fact')
                self.assertEqual(row['disposition'], 'unknown')
                self.assertEqual(row['reason'], 'matter.unmapped.v1')
                self.assertNotIn('target', row)
                self.assertEqual(row['loss'][0]['source_items'], [ident])
                self.assertEqual(row['source']['requested']['item_id'], ident)
                self.assertEqual(row['source']['fact_keys'][0]['fact_id'], ident)
        transformed = [r['ref']['id'] for r in self.document['rows']
                       if r['disposition'] in ('exact', 'transformed')]
        self.assertEqual(transformed, ['evse.ac.current'])

    CR02_PACKS = {
        'infrastructure': ('helianthus.pack.infrastructure', '1.0.0', 'infrastructure.dimension.meter'),
        'evse': ('helianthus.pack.evse', '1.0.0', 'evse.dimension.meter'),
        'storage': ('helianthus.pack.storage', '1.1.0', 'storage.dimension.pack'),
    }
    CR02_VALUE_FACTS = [
        'accuracy.measured_minimum_active_current',
        'accuracy.measured_maximum_active_current',
        'accuracy.range_minimum_active_current',
        'accuracy.range_maximum_active_current',
        'accuracy.measured_minimum_active_power',
        'accuracy.measured_maximum_active_power',
        'accuracy.range_minimum_active_power',
        'accuracy.range_maximum_active_power',
    ]
    CR02_BASE_FACTS = ['accuracy.measured', 'accuracy.ratio_maximum']

    def cr02_expected(self):
        # Literal prefixes and suffixes; the infrastructure meter already has the base facts.
        result = []
        for prefix, (pack, version, dimension) in self.CR02_PACKS.items():
            names = self.CR02_VALUE_FACTS if prefix == 'infrastructure' else self.CR02_BASE_FACTS + self.CR02_VALUE_FACTS
            result.extend((prefix + '.' + name, pack, version, dimension) for name in names)
        return result

    @staticmethod
    def cr02_row_fault(row, ident, pack, version, dimension):
        """The first fault of one added row, or None.

        Every identity field of the row is compared: ref pack id, ref pack version, ref id,
        ref version, kind, disposition, reason, the target member, the loss source item, the
        requested item id, kind and version, and the fact key pack id, pack version, fact id,
        dimension definition pack id, pack version, id and version.
        """
        ref = row['ref']
        checks = [
            (ref['pack']['id'] == pack, 'ref pack id'),
            (ref['pack']['version'] == version, 'ref pack version'),
            (ref['id'] == ident, 'ref id'),
            (ref['version'] == version, 'ref version'),
            (row['kind'] == 'fact', 'kind'),
            (row['disposition'] == 'unknown', 'disposition'),
            (row['reason'] == 'matter.unmapped.v1', 'reason'),
            ('target' not in row, 'target member'),
            (row['loss'][0]['source_items'] == [ident], 'loss source item'),
            (row['source']['requested']['item_id'] == ident, 'requested item id'),
            (row['source']['requested']['kind'] == 'fact', 'requested kind'),
            (row['source']['requested']['item_version'] == version, 'requested item version'),
            (row['source']['fact_keys'][0]['pack_id'] == pack, 'fact key pack id'),
            (row['source']['fact_keys'][0]['pack_version'] == version, 'fact key pack version'),
            (row['source']['fact_keys'][0]['fact_id'] == ident, 'fact key fact id'),
            (row['source']['fact_keys'][0]['dimensions']['definition']['pack']['id'] == pack, 'dimension pack id'),
            (row['source']['fact_keys'][0]['dimensions']['definition']['pack']['version'] == version, 'dimension pack version'),
            (row['source']['fact_keys'][0]['dimensions']['definition']['id'] == dimension, 'dimension id'),
            (row['source']['fact_keys'][0]['dimensions']['definition']['version'] == version, 'dimension version'),
        ]
        return next((label for ok, label in checks if not ok), None)

    def test_storage_evse_and_meter_accuracy_rows_are_unknown(self):
        """One unknown row per added element; expectations are literal, never read from the catalog."""
        rows = {r['ref']['id']: r for r in self.document['rows']}
        expected = self.cr02_expected()
        self.assertEqual(len(expected), 28)
        for ident, pack, version, dimension in expected:
            with self.subTest(ident=ident):
                self.assertIsNone(self.cr02_row_fault(rows[ident], ident, pack, version, dimension))
        for prefix in ('evse', 'storage'):
            with self.subTest(dimension=prefix):
                self.assertNotIn(prefix + '.dimension.measurement_type', rows)
        transformed = [r['ref']['id'] for r in self.document['rows']
                       if r['disposition'] in ('exact', 'transformed')]
        self.assertEqual(transformed, ['evse.ac.current'])

    def test_each_identity_field_of_an_accuracy_row_is_checked(self):
        """Each mutation below must be reported by cr02_row_fault.

        ref pack id, ref pack version, ref id and ref version: another value is reported.
        kind, disposition and reason: another value is reported.
        target member: adding one is reported.
        loss source item, requested item id, kind and version: another value is reported.
        fact key pack id, pack version and fact id: another value is reported.
        dimension definition pack id, pack version, id and version: another value is reported.
        """
        ident, pack, version, dimension = 'storage.accuracy.measured', 'helianthus.pack.storage', '1.1.0', 'storage.dimension.pack'
        row = next(r for r in self.document['rows'] if r['ref']['id'] == ident)
        key = ('source', 'fact_keys', 0, 'dimensions', 'definition')
        mutations = {
            'ref pack id': (('ref', 'pack', 'id'), 'helianthus.pack.evse'),
            'ref pack version': (('ref', 'pack', 'version'), '1.0.0'),
            'ref id': (('ref', 'id'), 'storage.accuracy.ratio_maximum'),
            'ref version': (('ref', 'version'), '1.0.0'),
            'kind': (('kind',), 'service'),
            'disposition': (('disposition',), 'transformed'),
            'reason': (('reason',), 'matter.service_not_requested_item.v1'),
            'target member': (('target',), {'device_type_id': 1296}),
            'loss source item': (('loss', 0, 'source_items'), ['storage.accuracy.ratio_maximum']),
            'requested item id': (('source', 'requested', 'item_id'), 'storage.accuracy.ratio_maximum'),
            'requested kind': (('source', 'requested', 'kind'), 'capability'),
            'requested item version': (('source', 'requested', 'item_version'), '1.0.0'),
            'fact key pack id': (('source', 'fact_keys', 0, 'pack_id'), 'helianthus.pack.evse'),
            'fact key pack version': (('source', 'fact_keys', 0, 'pack_version'), '1.0.0'),
            'fact key fact id': (('source', 'fact_keys', 0, 'fact_id'), 'storage.accuracy.ratio_maximum'),
            'dimension pack id': (key + ('pack', 'id'), 'helianthus.pack.evse'),
            'dimension pack version': (key + ('pack', 'version'), '1.0.0'),
            'dimension id': (key + ('id',), 'storage.dimension.cell'),
            'dimension version': (key + ('version',), '1.0.0'),
        }
        for label, (path, value) in mutations.items():
            with self.subTest(field=label):
                candidate = copy.deepcopy(row)
                cursor = candidate
                for part in path[:-1]:
                    cursor = cursor[part]
                cursor[path[-1]] = value
                self.assertEqual(self.cr02_row_fault(candidate, ident, pack, version, dimension), label)

    def test_unqualified_is_not_a_whole_document_guard(self):
        guards = self.document['input_guards']['whole_document_no_payload']
        self.assertNotIn('unqualified', guards)
        self.assertEqual(guards, GUARDS)
        self.assertEqual(self.document['model_source']['repository'], 'SukramJ/go-fabric')
        self.assertEqual(self.document['model_source']['tag'], 'v0.13.12')

    def test_a_second_cited_transformed_row_is_admitted(self):
        """A second transformed row is admitted when every citation field is present.

        Fields and the production mutation each check catches:
        - device_type_id: deleting it is rejected as an uncited device type.
        - cluster_id: deleting it is rejected as an uncited cluster.
        - attribute_id: deleting it is rejected as an uncited element.
        - conversion.factor: deleting it is rejected as an uncited factor.
        - conversion.offset: deleting it is rejected as an uncited offset.
        - conversion.rounding: deleting it is rejected as an uncited rounding.
        - representation.minimum: deleting it is rejected as an uncited lower bound.
        - representation.maximum: deleting it is rejected as an uncited upper bound.
        - evse.ac.current disposition: demoting it is rejected while the second row stays.
        """
        ref = {'pack': {'id': 'helianthus.pack.evse', 'version': '1.0.0'},
               'id': 'evse.ac.voltage', 'version': '1.0.0'}

        def cited(document):
            row = document['rows'][self.index(ref)]
            row['disposition'] = 'transformed'
            row['reason'] = 'matter.cited_conversion.v1'
            row['target'] = {
                'device_type_id': 14, 'cluster_id': 156, 'attribute_id': 4,
                'value': {
                    'conversion': {'factor': 1, 'offset': 0, 'rounding': 'exact'},
                    'representation': {'minimum': 0, 'maximum': 100},
                },
            }
            return document

        check_dispositions(cited(copy.deepcopy(self.document)))
        fields = [
            ('device_type_id', ('target', 'device_type_id')),
            ('cluster_id', ('target', 'cluster_id')),
            ('attribute_id', ('target', 'attribute_id')),
            ('factor', ('target', 'value', 'conversion', 'factor')),
            ('offset', ('target', 'value', 'conversion', 'offset')),
            ('rounding', ('target', 'value', 'conversion', 'rounding')),
            ('minimum', ('target', 'value', 'representation', 'minimum')),
            ('maximum', ('target', 'value', 'representation', 'maximum')),
        ]
        for label, path in fields:
            candidate = cited(copy.deepcopy(self.document))
            node = candidate['rows'][self.index(ref)]
            for key in path[:-1]:
                node = node[key]
            del node[path[-1]]
            with self.subTest(field=label):
                with self.assertRaises(ValueError):
                    check_dispositions(candidate)
        demoted = cited(copy.deepcopy(self.document))
        positive = demoted['rows'][self.index()]
        positive['disposition'] = 'unknown'
        positive['reason'] = 'matter.unmapped.v1'
        del positive['target']
        with self.assertRaises(ValueError):
            check_dispositions(demoted)

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
                 (('conversion', 'offset'), 1),
                 (('conversion', 'rounding'), 'round'),
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
        for ident in [
                'pv.accuracy.measured_minimum_active_current',
                'pv.accuracy.measured_maximum_active_current',
                'pv.accuracy.range_minimum_active_current',
                'pv.accuracy.range_maximum_active_current',
                'pv.accuracy.measured_minimum_active_power',
                'pv.accuracy.measured_maximum_active_power',
                'pv.accuracy.range_minimum_active_power',
                'pv.accuracy.range_maximum_active_power']:
            with self.subTest(ident=ident):
                self.assertIn(ident, self.text)
        for field in ['MinMeasuredValue', 'MaxMeasuredValue', 'RangeMin', 'RangeMax']:
            with self.subTest(field=field):
                self.assertIn(field, self.text)
        self.assertIn('PV inverter', self.text)
        self.assertIn('have no roster row', self.text)
        self.assertIn('matter.unmapped.v1', self.text)
        self.assertIn('no struct is published', self.text)
        self.assertIn('does not deliver', self.text)
        self.assertIn('withheld', self.text)

    def test_storage_evse_and_meter_accuracy_facts_are_stated(self):
        for ident in ['infrastructure.accuracy.measured_minimum_active_current',
                      'infrastructure.accuracy.range_maximum_active_power',
                      'evse.accuracy.measured', 'evse.accuracy.ratio_maximum',
                      'evse.accuracy.measured_maximum_active_current',
                      'evse.accuracy.range_minimum_active_power',
                      'storage.accuracy.measured', 'storage.accuracy.ratio_maximum',
                      'storage.accuracy.measured_minimum_active_power',
                      'storage.accuracy.range_maximum_active_current',
                      'evse.dimension.measurement_type', 'storage.dimension.measurement_type']:
            with self.subTest(ident=ident):
                self.assertIn(ident, self.text)
        self.assertIn('Fixed Label', self.text)

    def test_unsourced_values_and_shape_are_stated(self):
        for text in ['electrical_sensor_pilot', 'declared_values', '`unsourced`',
                     'Power Topology `FeatureMap`',
                     'Electrical Power Measurement `FeatureMap`', '`PowerMode`',
                     '`NumberOfMeasurementTypes`', '`MinMeasuredValue`',
                     '`MaxMeasuredValue`', '`RangeMin`', '`RangeMax`',
                     '`ActivePower`', 'ActivePower` is null for the pilot',
                     '`field`', '`declared`', 'native_convention']:
            with self.subTest(text=text):
                self.assertIn(text, self.text)

    def test_no_false_unresolved_subject_schema_cause(self):
        self.assertNotIn('unresolved subject', self.text)
        self.assertNotIn('qualifier dimension only', self.text)

    def test_internal_table_names_are_not_cited_as_source(self):
        self.assertNotIn('PE03', self.text)
        self.assertNotIn('PE10', self.text)
        self.assertIn('unverified', self.text)

    def test_page_does_not_treat_unqualified_as_a_payload_guard(self):
        self.assertNotIn('unqualified', self.text)
        self.assertNotIn('SS01', self.text)
        contract = (ROOT / 'api/v1/driver-contract.md').read_text()
        self.assertEqual(contract.count('SS01'), 1)
        self.assertIn('SS01 removes\n  that northbound effect', contract)


if __name__ == '__main__':
    unittest.main()
