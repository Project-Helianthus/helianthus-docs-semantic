"""Offline publication checks for the eeBUS SPINE 1.3.0 target."""

import copy
import csv
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'api/v1/targets/eebus-spine-1.3.0-v1.json'
CATALOG = ROOT / 'api/v1/element-catalog-v1.json'
KINDS = ['fact', 'capability', 'operation', 'service', 'relation', 'event']
FORBIDDEN = (
    'flexibleStartForWhiteGoods',
    'monitoringAndControlOfSmartGridReadyConditions',
)
SPINE_FEATURES = frozenset({
    'ActuatorLevel', 'Bill', 'DeviceClassification', 'DeviceConfiguration',
    'DeviceDiagnosis', 'DirectControl', 'ElectricalConnection', 'HVAC',
    'Identification', 'IncentiveTable', 'LoadControl', 'Measurement',
    'Messaging', 'NodeManagement', 'OperatingConstraints', 'PowerSequences',
    'Sensing', 'Setpoint', 'SmartEnergyManagementPs', 'SupplyCondition',
    'TariffInformation', 'TaskManagement', 'TimeInformation', 'TimeSeries',
    'TimeSeriesConstraints', 'TimeTable',
})
VERSION = r'\d+\.\d+\.\d+(?: RC\d+|b)?'
SCENARIO = re.compile(
    r'^[A-Z]{2,12}-(?:sc\d+[a-z]?|\d{2,4}[a-z]?(?:/\d+)?)$')
SCENARIO_FIND = re.compile(
    r'[A-Z]{2,12}-(?:sc\d+[a-z]?|\d{2,4}[a-z]?(?:/\d+)?)')
HVAC_TOKEN = re.compile(
    r'^HVAC-(?:TEMP|SF):([A-Z]{2,12}-sc\d+)(-constraints)?$')
BRACKET = re.compile(
    rf'^(.+?) V({VERSION}) \[([A-Z0-9][A-Za-z0-9/-]*)\]')
HVAC_SOURCE = re.compile(
    rf'^(.+?) ({VERSION}) scenario (\d+), ([^,]+), '
    r'([A-Za-z]+)\.([A-Za-z0-9_.]+)'
    r'(?: \(([A-Z]{2,12}-\d+)\))?')
USE_CASE_PATH = re.compile(rf'^(.+?) V({VERSION}) (.+)$')
CLAUSE = re.compile(r'§(\d+(?:\.\d+)*)')
SCOPE = {
    'projection_items': KINDS,
    'derived_from': 'api/v1/element-catalog-v1.json',
    'not_requested':
        'core-owned elements, dimensions, effect rules and presentations',
}
LOSS_CITED = (
    'the citation records the fact-table cells and does not emit a SPINE '
    'datagram or allocate an entity')
LOSS_UNKNOWN = (
    'no SPINE feature, function, entity, scenario or datagram is created')


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
    return {
        'pack': ref['owner']['pack'],
        'id': ref['id'],
        'version': ref['version'],
    }


def identity(ref):
    return ref['pack']['id'], ref['pack']['version'], ref['id'], ref['version']


def items():
    selected = [
        (element, element['element_kind'])
        for element in load(CATALOG)['elements']
        if element['ref']['owner']['kind'] == 'pack'
        and element['element_kind'] in KINDS
    ]
    return sorted(selected, key=lambda pair: identity(pack_ref(pair[0]['ref'])))


def packs():
    found = {}
    for element, _kind in items():
        ref = pack_ref(element['ref'])
        found[ref['pack']['id'].removeprefix('helianthus.pack.')] = (
            ref['pack']['version'])
    return found


def _row_identity(row):
    for key in ('id', 'element', 'operation', 'event', 'relation'):
        value = (row.get(key) or '').strip()
        if value:
            return value
    return None


def _remember(found, ident, cell, source):
    previous = found.get(ident)
    if previous is None:
        found[ident] = {'cell': cell, 'source': source}
        return
    require(previous['cell'] == cell, 'conflicting eeBUS cell')
    require(previous['source'] == source, 'conflicting eeBUS source')


def fact_records():
    found = {}
    root = ROOT / 'acceptance' / 'catalog-inputs'
    for path in sorted(root.rglob('*.tsv')):
        with path.open(newline='', encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle, delimiter='\t'))
        if not rows:
            continue
        columns = [key for key in rows[0] if key.lower() in ('eebus', 'matter_eebus')]
        if not columns:
            continue
        column = columns[0]
        for row in rows:
            ident = _row_identity(row)
            if ident is None:
                continue
            _remember(
                found, ident, (row.get(column) or '').strip(),
                (row.get('source') or '').strip())
    return found


def _fresh():
    return {
        'scenarios': [],
        'use_cases': [],
        'spine': [],
        'entity_types': [],
        'scopes': [],
        'clauses': [],
        'spine_named': False,
    }


def _append_unique(values, value):
    if value and value not in values:
        values.append(value)


def _add_scenario(partial, token):
    if SCENARIO.match(token):
        _append_unique(partial['scenarios'], token)


def _add_entity(partial, name):
    _append_unique(partial['entity_types'], name)


def _add_scope(partial, name):
    _append_unique(partial['scopes'], name)


def _spine_entry(partial, feature):
    if feature == 'measurement':
        feature = 'Measurement'
    if feature not in SPINE_FEATURES:
        return None
    for entry in partial['spine']:
        if entry['feature'] == feature:
            return entry
    entry = {'feature': feature, 'functions': [], 'keys': []}
    partial['spine'].append(entry)
    return entry


def _add_functions(entry, functions):
    for function in functions:
        if not function:
            continue
        longer = [
            existing for existing in entry['functions']
            if existing == function or existing.startswith(function + '.')
            or function.startswith(existing + '.')
        ]
        if not longer:
            entry['functions'].append(function)
            continue
        entry['functions'] = [
            function if existing in longer and len(function) > len(existing)
            else existing
            for existing in entry['functions']
        ]


def _add_key(entry, key):
    if key not in entry['keys']:
        entry['keys'].append(key)


def _add_spine(partial, feature, functions=None, keys=None, parameter=None):
    entry = _spine_entry(partial, feature)
    if entry is None:
        return
    _add_functions(entry, functions or [])
    for key in keys or []:
        _add_key(entry, key)
    if parameter and 'parameter' not in entry:
        entry['parameter'] = parameter


def _add_use_case(partial, name, revision, scenarios):
    if not name or 'vendor' in name.lower() or name.startswith('Matter'):
        return
    for entry in partial['use_cases']:
        if entry['name'] == name and entry['revision'] == revision:
            for token in scenarios:
                _append_unique(entry['scenarios'], token)
                _add_scenario(partial, token)
            return
    partial['use_cases'].append({
        'name': name,
        'revision': revision,
        'scenarios': list(scenarios),
    })
    for token in scenarios:
        _add_scenario(partial, token)


def _mark_spine_document(partial, segment):
    if 'SPINE 1.3.0' in segment or 'EEBUS SPINE V1.3.0' in segment:
        partial['spine_named'] = True
        for clause in CLAUSE.findall(segment):
            _append_unique(partial['clauses'], clause)


def parse_spine_token(token, partial):
    body = token[len('SPINE:'):]
    if body.startswith('entity.'):
        _add_entity(partial, body.split('.', 1)[1])
        return
    if body.startswith('scope.'):
        _add_scope(partial, body.split('.', 1)[1])
        return
    if body.startswith('measurement.'):
        _add_spine(partial, 'Measurement', keys=[{
            'name': 'measurementType',
            'value': body.split('.', 1)[1],
        }])
        return
    feature, _, rest = body.partition('.')
    functions = [rest] if rest else []
    _add_spine(partial, feature, functions=functions)
    for found in SCENARIO_FIND.findall(rest):
        _add_scenario(partial, found)


def _functions_in_piece(piece):
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*', piece):
        return [piece], None
    functions = []
    leading = re.match(r'([A-Za-z_][A-Za-z0-9_.-]*)', piece)
    if leading:
        functions.append(leading.group(1).strip('-.'))
    for extra in re.findall(
            r'[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)+', piece):
        if extra not in functions:
            functions.append(extra)
    placeholder = re.search(r'(<[A-Za-z0-9]+>\.[A-Za-z0-9_.]+)', piece)
    return functions, placeholder.group(1) if placeholder else None


def parse_spine_text(text, partial, parameter=None):
    parts = re.split(r'\s+(?:and|plus)\s+', text)
    feature = parts[0].split('.', 1)[0]
    functions = []
    for index, part in enumerate(parts):
        if index == 0 and '.' in part:
            rest = part.split('.', 1)[1]
        elif index == 0:
            rest = ''
        else:
            rest = part
        for piece in rest.split(','):
            piece = piece.strip()
            if not piece:
                continue
            extracted, extra_parameter = _functions_in_piece(piece)
            functions.extend(extracted)
            if extra_parameter and not parameter:
                parameter = extra_parameter
            for found in SCENARIO_FIND.findall(piece):
                _add_scenario(partial, found)
    _add_spine(partial, feature, functions=functions, parameter=parameter)


def _hvac_tokens(cell):
    tokens = [token.strip() for token in cell.split(',') if token.strip()]
    if tokens and all(HVAC_TOKEN.match(token) for token in tokens):
        return tokens
    return None


def parse_cell(cell, partial):
    hvac = _hvac_tokens(cell)
    if hvac is not None:
        for token in hvac:
            _add_scenario(partial, HVAC_TOKEN.match(token).group(1))
        return
    if '; parameter ' in cell or ' and ' in cell or ' plus ' in cell:
        text, _, parameter = cell.partition('; parameter ')
        parse_spine_text(text, partial, parameter or None)
        return
    tokens = [token.strip() for token in cell.split(',') if token.strip()]
    if len(tokens) == 1 and tokens[0].split('.', 1)[0] in SPINE_FEATURES:
        parse_spine_text(tokens[0], partial)
        return
    for token in tokens:
        if SCENARIO.match(token) or HVAC_TOKEN.match(token):
            matched = HVAC_TOKEN.match(token)
            _add_scenario(partial, matched.group(1) if matched else token)
        elif token.startswith('SPINE:'):
            parse_spine_token(token, partial)


def _keys_from_prose(segment):
    keys = []
    measured = re.search(r'measurementType ([A-Za-z0-9_]+)', segment)
    if measured:
        keys.append({'name': 'measurementType', 'value': measured.group(1)})
    overrun = re.search(r'overrunType(?: ([A-Za-z0-9_]+))?', segment)
    if overrun and 'overrunType' in segment:
        key = {'name': 'overrunType'}
        if overrun.group(1):
            key['value'] = overrun.group(1)
        keys.append(key)
    element = re.search(r'element ([A-Za-z0-9_]+)', segment)
    if element and element.group(1) not in ('overrunType', 'overrunStatus'):
        keys.append({'name': element.group(1)})
    return keys


def _functions_from_prose(segment):
    pair = re.search(
        r'functions ([A-Za-z0-9_.]+) and ([A-Za-z0-9_.]+)', segment)
    if pair:
        return [pair.group(1), pair.group(2)]
    single = re.search(r'function ([A-Za-z0-9_.]+)', segment)
    if single:
        return [single.group(1)]
    return []


def _header_feature(segment):
    if re.search(r'\bfeature\b', segment):
        return None
    for feature in sorted(SPINE_FEATURES, key=len, reverse=True):
        matched = re.search(
            rf'(?:^|\s){feature}(?:\.([A-Za-z0-9_.]+))?(?=\s|$)', segment)
        if matched:
            return feature, matched.group(1)
    return None


def parse_spine_prose(segment, partial):
    if not (segment.startswith('SPINE') or segment.startswith('EEBUS SPINE')):
        return False
    _mark_spine_document(partial, segment)
    feature = re.search(r'feature ([A-Za-z]+)', segment)
    entity = re.search(r'entity type ([A-Za-z0-9]+)', segment)
    if entity:
        _add_entity(partial, entity.group(1))
    scope = re.search(r'ScopeTypeEnumType ([A-Za-z0-9_]+)', segment)
    if scope:
        _add_scope(partial, scope.group(1))
    functions = _functions_from_prose(segment)
    header = _header_feature(segment)
    if header and header[1]:
        functions = functions + [header[1]]
    chosen = feature.group(1) if feature else (header[0] if header else None)
    if chosen:
        _add_spine(
            partial, chosen, functions=functions, keys=_keys_from_prose(segment))
    return True


def parse_clause_continuation(segment, partial):
    if not segment.startswith('§'):
        return False
    for clause in CLAUSE.findall(segment):
        _append_unique(partial['clauses'], clause)
    path = re.search(r'([a-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)', segment)
    if path and len(partial['spine']) == 1:
        _add_functions(partial['spine'][0], [path.group(1)])
    return True


def parse_use_case(segment, partial):
    bracket = BRACKET.match(segment)
    if bracket:
        _add_use_case(
            partial, bracket.group(1).strip(), bracket.group(2),
            [bracket.group(3)])
        return True
    hvac = HVAC_SOURCE.match(segment)
    if hvac:
        _add_use_case(
            partial, hvac.group(1).strip(), hvac.group(2),
            [token for token in (hvac.group(7),) if token])
        _add_entity(partial, hvac.group(4).strip())
        _add_spine(
            partial, hvac.group(5), functions=[hvac.group(6)])
        return True
    path = USE_CASE_PATH.match(segment)
    if path is None:
        return False
    _add_use_case(partial, path.group(1).strip(), path.group(2), [])
    rest = path.group(3).strip()
    if rest.split('.', 1)[0] in SPINE_FEATURES:
        parameter = None
        text = rest
        if '; parameter ' in rest:
            text, _, parameter = rest.partition('; parameter ')
        parse_spine_text(text, partial, parameter or None)
    return True


def _ignored_segment(segment):
    lowered = segment.lower()
    if lowered.startswith('matter') or lowered.startswith('vendor'):
        return True
    if lowered.startswith('bound not') or lowered.startswith('source not found'):
        return True
    if lowered.startswith('native unit') or lowered.startswith('number *'):
        return True
    if lowered.startswith('absent scale') or lowered.startswith('unit.'):
        return True
    if 'conversion undeclared' in lowered or 'scale not declared' in lowered:
        return True
    if segment.endswith('J per Wh') or SCENARIO.match(segment):
        return True
    return segment.startswith('SPINE:')


def _attach_loose_scenarios(partial):
    if len(partial['use_cases']) != 1:
        return
    entry = partial['use_cases'][0]
    for token in partial['scenarios']:
        _append_unique(entry['scenarios'], token)


def parse_source(source, partial):
    for segment in source.split(';'):
        segment = segment.strip()
        if not segment or _ignored_segment(segment):
            if segment.startswith('SPINE:'):
                parse_spine_token(segment, partial)
            continue
        if parse_clause_continuation(segment, partial):
            continue
        if parse_spine_prose(segment, partial):
            continue
        if parse_use_case(segment, partial):
            continue
        for found in SCENARIO_FIND.findall(segment):
            _add_scenario(partial, found)
    _attach_loose_scenarios(partial)


def unit_conversion(source):
    if re.search(r'conversion undeclared|scale not declared', source):
        return None
    found = re.search(
        r'native unit ([^;]+); number \* 10\^scale; absent scale (\d+); '
        r'(unit\.[a-z0-9_]+)',
        source)
    if found is None:
        return None
    conversion = {
        'native_unit': found.group(1),
        'canonical_unit': found.group(3),
        'scale_when_absent': int(found.group(2)),
        'algorithm': 'number_times_ten_to_scale',
    }
    factor = re.search(r'(\d+) J per Wh', source)
    if factor and conversion['canonical_unit'] == 'unit.joule':
        conversion['factor'] = int(factor.group(1))
        conversion['factor_from_unit'] = 'Wh'
    return conversion


def _public_spine(partial):
    if not partial['spine_named']:
        return None
    document = {'name': 'SPINE', 'revision': '1.3.0'}
    if partial['clauses']:
        document['clauses'] = sorted(partial['clauses'])
    return document


def _clean_spine(entry):
    cleaned = {'feature': entry['feature']}
    if entry['functions']:
        cleaned['functions'] = sorted(entry['functions'])
    if entry['keys']:
        cleaned['keys'] = sorted(
            entry['keys'], key=lambda key: (key['name'], key.get('value', '')))
    if entry.get('parameter'):
        cleaned['parameter'] = entry['parameter']
    return cleaned


def _clean_use_case(entry):
    cleaned = {'name': entry['name'], 'revision': entry['revision']}
    if entry['scenarios']:
        cleaned['scenarios'] = sorted(entry['scenarios'])
    return cleaned


def finish(partial, conversion):
    target = {}
    document = _public_spine(partial)
    if document:
        target['document'] = document
    if partial['use_cases']:
        target['use_cases'] = sorted(
            (_clean_use_case(entry) for entry in partial['use_cases']),
            key=lambda entry: (entry['name'], entry['revision']))
    if partial['scenarios']:
        target['scenarios'] = sorted(partial['scenarios'])
    if partial['spine']:
        target['spine'] = sorted(
            (_clean_spine(entry) for entry in partial['spine']),
            key=lambda entry: entry['feature'])
    if partial['entity_types']:
        target['entity_types'] = sorted(partial['entity_types'])
    if partial['scopes']:
        target['scopes'] = sorted(partial['scopes'])
    if conversion:
        target['unit_conversion'] = conversion
    if not target:
        return None
    target['equivalence'] = 'Hypothesis'
    return target


def cite(cell, source):
    if not (cell or '').strip():
        return None
    partial = _fresh()
    parse_cell(cell.strip(), partial)
    parse_source(source or '', partial)
    return finish(partial, unit_conversion(source or ''))


def fact_keys(element):
    ref = pack_ref(element['ref'])
    subject = element['attributes']['subject']
    dimension = pack_ref(subject.get('dimension') or subject['qualifier_dimension'])
    return [{
        'pack_id': ref['pack']['id'],
        'pack_version': ref['pack']['version'],
        'fact_id': ref['id'],
        'dimensions': {
            'mode': 'exact_runtime_fact_key',
            'definition': dimension,
        },
    }]


def loss(item_id, cited_row):
    return [{
        'kind': 'policy',
        'source_items': [item_id],
        'description': LOSS_CITED if cited_row else LOSS_UNKNOWN,
        'reversible': False,
    }]


def source_binding(element, kind):
    ref = pack_ref(element['ref'])
    requested = None
    if kind not in ('service', 'event'):
        requested = {
            'kind': kind,
            'item_id': ref['id'],
            'item_version': ref['version'],
        }
    return {
        'kernel_contract': 'helianthus.semantic.kernel/v1',
        'requested': requested,
        'revision_binding': {
            'snapshot_id': 'exact_input_snapshot',
            'revisions': 'exact_input_revisions',
        },
        'fact_keys': fact_keys(element) if kind == 'fact' else [],
    }


def relation_member(element):
    attributes = element['attributes']
    member = {'core_type': attributes['core_type']}
    if 'medium' in attributes:
        member['medium'] = attributes['medium']
    return member


def expected_row(element, kind, records):
    ref = pack_ref(element['ref'])
    record = records.get(ref['id'])
    cell = record['cell'] if record else ''
    source = record['source'] if record else ''
    target = cite(cell, source)
    row = {
        'ref': ref,
        'kind': kind,
        'disposition': 'cited' if target else 'unknown',
        'reason': 'eebus.cited.v1' if target else 'eebus.unmapped.v1',
        'loss': loss(ref['id'], target is not None),
        'source': source_binding(element, kind),
    }
    if kind == 'relation':
        row['relation'] = relation_member(element)
    if target:
        row['target'] = target
    return row


def document():
    records = fact_records()
    return {
        'contract': 'helianthus.gateway.eebus-projection/v1',
        'status': 'adoption_projection_contract_pre_1_0',
        'mapping_revision': 1,
        'target': {'name': 'eebus.spine', 'version': '1.3.0'},
        'pins': {'packs': packs()},
        'scope': SCOPE,
        'ownership': {
            'projection_contract': 'Project-Helianthus/helianthus-docs-semantic',
            'kernel_and_packs': 'Project-Helianthus/helianthus-semreg',
            'runtime_implementation': 'Project-Helianthus/helianthus-eebusreg',
        },
        'non_claims': [
            'ship_node',
            'pairing',
            'datagram_emission',
            'entity_allocation',
            'certification',
            'conformance',
            'live_device',
            'physical_result',
            'use_case_requirement_text',
        ],
        'model_source': {
            'document': 'SPINE',
            'revision': '1.3.0',
            'inspection_grade': 'Hypothesis',
            'inspection_basis': (
                'fact-table scenario, feature, function and conversion cells; '
                'requirement text is not copied'),
            'execution_grade': 'Unknown',
            'standards_equivalence': 'Unknown',
        },
        'rows': [expected_row(element, kind, records) for element, kind in items()],
    }


def check_header(candidate):
    expected = document()
    require(candidate['contract'] == expected['contract'], 'contract')
    require(candidate['status'] == expected['status'], 'status')
    require(candidate['mapping_revision'] == expected['mapping_revision'], 'mapping revision')
    require(candidate['target'] == expected['target'], 'target')
    require(candidate['pins'] == expected['pins'], 'pack pins')
    require(candidate['scope'] == expected['scope'], 'scope')
    require(candidate['ownership'] == expected['ownership'], 'ownership')
    require(candidate['non_claims'] == expected['non_claims'], 'non claims')
    require(candidate['model_source'] == expected['model_source'], 'model source')


def check_roster(candidate):
    expected = [(pack_ref(element['ref']), kind) for element, kind in items()]
    require([(row['ref'], row['kind']) for row in candidate['rows']] == expected, 'exact roster')


def check_rows(candidate):
    records = fact_records()
    expected = [expected_row(element, kind, records) for element, kind in items()]
    require(candidate['rows'] == expected, 'fact-table citation')


def check_empty_cells(candidate):
    records = fact_records()
    for row in candidate['rows']:
        record = records.get(row['ref']['id'])
        if record is not None and record['cell'] == '':
            require(row['disposition'] == 'unknown', 'empty cell disposition')
            require(row['reason'] == 'eebus.unmapped.v1', 'empty cell reason')
            require('target' not in row, 'empty cell has no target')


def check_function_names(candidate):
    for row in candidate['rows']:
        for entry in (row.get('target') or {}).get('spine') or []:
            for function in entry.get('functions') or []:
                require(
                    re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*', function) is not None,
                    'function identifier')


def check_forbidden(candidate):
    encoded = json.dumps(candidate)
    for name in FORBIDDEN:
        require(name not in encoded, 'forbidden use case')
    require('vendor A' not in encoded and 'vendor B' not in encoded, 'vendor note')


def check_registration():
    script = (ROOT / 'scripts' / 'check_docs.sh').read_text(encoding='utf-8')
    require('python3 tests/test_eebus_target.py' in script, 'check_docs runs the test')
    require(
        'api/v1/targets/eebus-spine-1.3.0-v1.json' in script,
        'check_docs requires the descriptor')


class EebusTargetTests(unittest.TestCase):
    def setUp(self):
        self.document = load(LEDGER)

    def reject(self, checker, mutate):
        checker(self.document)
        candidate = copy.deepcopy(self.document)
        mutate(candidate)
        with tempfile.TemporaryDirectory(prefix='eebus-target-') as directory:
            mutant = Path(directory) / LEDGER.name
            mutant.write_text(json.dumps(candidate))
            with self.assertRaises(ValueError):
                checker(load(mutant))

    def test_baseline_independent_checks(self):
        check_header(self.document)
        check_roster(self.document)
        check_rows(self.document)
        check_empty_cells(self.document)
        check_function_names(self.document)
        check_forbidden(self.document)
        check_registration()

    def test_roster_covers_every_requested_catalog_kind(self):
        self.assertEqual({row['kind'] for row in self.document['rows']}, set(KINDS))
        self.assertEqual(len(self.document['rows']), len(items()))

    def test_pack_identity_fields_are_independent(self):
        def pack_id(candidate):
            candidate['rows'][0]['ref']['pack']['id'] = 'helianthus.pack.other'

        def pack_version(candidate):
            candidate['rows'][0]['ref']['pack']['version'] = '9.9.9'

        def item_id(candidate):
            candidate['rows'][0]['ref']['id'] = 'energy.fact.missing'

        def item_version(candidate):
            candidate['rows'][0]['ref']['version'] = '9.9.9'

        def kind(candidate):
            candidate['rows'][0]['kind'] = 'dimension'

        for mutate in (pack_id, pack_version, item_id, item_version, kind):
            with self.subTest(mutate=mutate.__name__):
                self.reject(check_roster, mutate)

    def test_empty_cell_cannot_gain_a_target(self):
        records = fact_records()
        index = next(
            position for position, row in enumerate(self.document['rows'])
            if row['ref']['id'] in records and records[row['ref']['id']]['cell'] == '')

        def disposition(candidate):
            candidate['rows'][index]['disposition'] = 'cited'

        def reason(candidate):
            candidate['rows'][index]['reason'] = 'eebus.cited.v1'

        def target(candidate):
            candidate['rows'][index]['target'] = {'equivalence': 'Hypothesis'}

        for mutate in (disposition, reason, target):
            with self.subTest(mutate=mutate.__name__):
                self.reject(check_empty_cells, mutate)

    def test_cited_revision_feature_and_function_are_independent(self):
        index = next(
            position for position, row in enumerate(self.document['rows'])
            if row['disposition'] == 'cited' and row['target'].get('use_cases')
            and row['target'].get('spine'))

        def revision(candidate):
            candidate['rows'][index]['target']['use_cases'][0]['revision'] = '9.9.9'

        def feature(candidate):
            candidate['rows'][index]['target']['spine'][0]['feature'] = 'MissingFeature'

        def function(candidate):
            spine = candidate['rows'][index]['target']['spine'][0]
            spine['functions'] = ['missingFunction']

        for mutate in (revision, feature, function):
            with self.subTest(mutate=mutate.__name__):
                self.reject(check_rows, mutate)

    def test_function_name_rejects_a_note(self):
        index = next(
            position for position, row in enumerate(self.document['rows'])
            if row['disposition'] == 'cited' and row['target'].get('spine'))

        def mutate(candidate):
            candidate['rows'][index]['target']['spine'][0]['functions'] = [
                'constraints shared with the current day row']

        self.reject(check_function_names, mutate)

    def test_page_cites_spine_and_rejects_the_forbidden_names(self):
        page = (ROOT / 'api/v1/targets/eebus-spine-1.3.0-v1.md').read_text(encoding='utf-8')
        self.assertIn('eebus-spine-1.3.0-v1.json', page)
        self.assertIn('eebus.unmapped.v1', page)
        self.assertIn('SPINE', page)
        self.assertIn('1.3.0', page)
        for name in FORBIDDEN:
            self.assertNotIn(name, page)


if __name__ == '__main__':
    unittest.main()
