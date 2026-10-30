"""Explicit, opt-in corrections to inferred OSM-to-SUMO signal mapping."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
from trial_evidence import load_trial, read_archive


def _canonical(element, round_speeds=True):
    attributes = dict(element.attrib)
    # netconvert serializes lane speeds to 2 dp when extracting a fixture.
    if round_speeds and element.tag == 'lane' and 'speed' in attributes:
        attributes['speed'] = f"{float(attributes['speed']):.2f}"
    return {'attributes': attributes, 'children': [_canonical(child, round_speeds) for child in element]}


def topology_fingerprint(root, recipe):
    """Bind the correction to the inspected roads, conflicts and programme."""
    nodes = set(recipe['junctions'])
    roads = {row.get('id'): row for row in root.findall('edge') if not row.get('function')}
    incident = {ident for ident, row in roads.items()
                if row.get('from') in nodes or row.get('to') in nodes}
    data = {'junctions': [_canonical(row) for row in root.findall('junction') if row.get('id') in nodes],
        'roads': [_canonical(roads[ident]) for ident in sorted(incident)],
        'programs': [_canonical(row) for row in root.findall('tlLogic')
                     if row.get('id') == recipe['controller']],
        'connections': [_canonical(row) for row in root.findall('connection')
                        if row.get('from') in incident]}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def verify_import_source(network, recipe):
    if topology_fingerprint(ET.parse(network).getroot(), recipe) != recipe['import_topology_sha256']:
        raise ValueError('Import-stage signal topology/programme differs from the inspected source')


def load_frozen_control(recipe, destination):
    """Use the recorded baseline, rather than a fresh set of converter guesses."""
    source = recipe['control_source']
    root = Path(__file__).resolve().parents[3]
    ledger = (root / source['ledger']).resolve()
    if not ledger.is_relative_to(root):
        raise ValueError('Control source must be a repository evidence ledger')
    evidence = load_trial(ledger, source['trial'])
    payload = evidence.payload('network.net.xml')
    identity = evidence.verified_identity()
    if (hashlib.sha256(payload).hexdigest() != source['network_sha256']
            or identity['reference_sha256'] != source['reference_sha256']):
        raise ValueError('Frozen signal-control identity changed')
    Path(destination).write_bytes(payload)
    return identity


def load_frozen_import(recipe, destination):
    root = Path(__file__).resolve().parents[3]
    Path(destination).write_bytes(read_archive(root, recipe['import_source']))
    verify_import_source(destination, recipe)


def inherited_junction_correction(recipe, supplied=None):
    expected = recipe['junction_corrections_sha256']
    if supplied is not None and supplied['sha256'] != expected:
        raise ValueError('Junction correction conflicts with the frozen import; rebuild and review the source model')
    return {'source': 'frozen_import', 'sha256': expected,
            'role': 'inherited_model_geometry_correction', 'field_validated': False}


def write_boundary_controls(network, recipe, destination):
    """Write a supported netconvert patch; keep the source network immutable."""
    if recipe.get('schema') != 1 or recipe.get('field_validated') is not False:
        raise ValueError('Expected an explicit, unvalidated model correction recipe')
    root = ET.parse(network).getroot()
    fingerprint = topology_fingerprint(root, recipe)
    if fingerprint != recipe['topology_sha256']:
        raise ValueError('Signal mapping topology/programme differs from the inspected source')
    nodes = set(recipe['junctions'])
    roads = {row.get('id'): row for row in root.findall('edge') if not row.get('function')}
    patch, internal, external = ET.Element('connections'), [], []
    internal_keys = set()
    for connection in root.findall('connection'):
        if connection.get('tl') != recipe['controller']:
            continue
        road = roads.get(connection.get('from'))
        if road is None or road.get('to') not in nodes:
            raise ValueError('Correction would change a control outside the inspected junction')
        item = {key: connection.get(key) for key in ['from', 'to', 'fromLane', 'toLane', 'linkIndex']}
        if road.get('from') in nodes:
            internal.append(item)
            internal_keys.add(tuple(item[key] for key in ['from', 'to', 'fromLane', 'toLane']))
        else:
            external.append(item)
    if (len(internal), len(external)) != (recipe['expected_internal_controls'], recipe['expected_external_controls']):
        raise ValueError('Correction does not match the inspected internal/external control counts')
    # Changing TLS membership makes netconvert recompute connection guesses at
    # unrelated nodes too. Pin the existing normal-road movements explicitly.
    for connection in root.findall('connection'):
        if connection.get('from') not in roads or connection.get('to') not in roads:
            continue
        attributes = {key: connection.get(key) for key in
                      ['from', 'to', 'fromLane', 'toLane', 'allow', 'disallow']
                      if connection.get(key) is not None}
        key = tuple(attributes[name] for name in ['from', 'to', 'fromLane', 'toLane'])
        if key in internal_keys:
            attributes['uncontrolled'] = 'true'
        ET.SubElement(patch, 'connection', **attributes)
    ET.ElementTree(patch).write(destination, encoding='utf-8', xml_declaration=True)
    return {'recipe': recipe['id'], 'role': recipe['role'], 'field_validated': False,
            'internal_controls': internal, 'external_controls': external,
            'topology_sha256': fingerprint, 'requires_regional_scope_review': True}


def verify_correction_scope(source, corrected, recipe):
    """Reject any compiler drift outside the reviewed junction footprint."""
    before, after = ET.parse(source).getroot(), ET.parse(corrected).getroot()
    nodes = set(recipe['junctions'])
    roads = {row.get('id'): row for row in before.findall('edge') if not row.get('function')}

    def internal(ident):
        return any(ident.startswith(':' + node + '_') for node in nodes)

    def key(row):
        if row.tag == 'connection':
            return tuple(row.get(name) for name in ['from', 'to', 'fromLane', 'toLane'])
        return row.get('id')

    old_controls = {key(row): row for row in before.findall('connection')
                    if row.get('tl') == recipe['controller']}
    new_connections = {key(row): row for row in after.findall('connection')}
    expected_retained = set()
    for ident, row in old_controls.items():
        updated = new_connections.get(ident)
        road = roads.get(row.get('from'))
        if road is None:
            raise ValueError('Expected normal-road signal controls in the reviewed footprint')
        if road.get('from') in nodes:
            if updated is None or updated.get('tl') is not None or updated.get('linkIndex') is not None:
                raise ValueError('Control correction did not remove an intended internal control')
        else:
            expected_retained.add(ident)
            if updated is None or {k: v for k, v in updated.attrib.items() if k != 'state'} != {
                    k: v for k, v in row.attrib.items() if k != 'state'}:
                raise ValueError('Control correction changed external entry control')
    retained = {key(row) for row in after.findall('connection') if row.get('tl') == recipe['controller']}
    if retained != expected_retained or len(retained) != recipe['expected_external_controls']:
        raise ValueError('Control correction changed external entry control count')
    if len(old_controls) - len(retained) != recipe['expected_internal_controls']:
        raise ValueError('Control correction removed an unexpected number of internal controls')

    def permitted(row):
        if row.tag == 'edge':
            return internal(row.get('id'))
        if row.tag == 'junction':
            return row.get('id') in nodes or internal(row.get('id'))
        if row.tag == 'connection':
            road = roads.get(row.get('from'))
            return internal(row.get('from')) or road is not None and road.get('to') in nodes
        return False

    changes = []
    if before.attrib != after.attrib:
        raise ValueError('Control correction changed global network attributes')
    def pedestrian_graph(root):
        lanes = {row.get('id'): _canonical(row, False) for row in root.iter('lane')
                 if 'pedestrian' in row.get('allow', '').split()}
        links = {key(row) for row in root.findall('connection')
                 if row.get('from') + '_' + row.get('fromLane') in lanes
                 and row.get('to') + '_' + row.get('toLane') in lanes}
        return lanes, links
    if pedestrian_graph(before) != pedestrian_graph(after):
        raise ValueError('Control correction changed the explicit pedestrian graph')
    for tag in sorted({row.tag for row in before} | {row.tag for row in after}):
        if tag not in ['edge', 'junction', 'connection']:
            if [_canonical(row, False) for row in before if row.tag == tag] != [
                    _canonical(row, False) for row in after if row.tag == tag]:
                raise ValueError(f'Control correction changed protected network elements: {tag}')
            continue
        old = {key(row): row for row in before if row.tag == tag}
        new = {key(row): row for row in after if row.tag == tag}
        for ident in sorted(old.keys() | new.keys(), key=str):
            a, b = old.get(ident), new.get(ident)
            if a is not None and b is not None and _canonical(a, False) == _canonical(b, False):
                continue
            if any(not permitted(row) for row in [a, b] if row is not None):
                raise ValueError(f'Control correction changed {tag} outside its scope: {ident}')
            # A control correction may rebuild internal conflict lanes, but may
            # not add/remove normal movements or change their access permissions.
            if tag == 'connection' and (ident[0] in roads or ident[1] in roads):
                if ident[0] in roads and ident[1] in roads:
                    if a is None or b is None or any(a.get(name) != b.get(name)
                            for name in ['allow', 'disallow']):
                        raise ValueError('Control correction changed normal movement access')
            changes.append({'kind': tag, 'id': ident, 'change':
                            'added' if a is None else 'removed' if b is None else 'updated'})
    return {'status': 'passed', 'outside_scope_changes': 0, 'explicit_pedestrian_graph_equal': True,
            'changes': changes,
            'source_network_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
            'corrected_network_sha256': hashlib.sha256(Path(corrected).read_bytes()).hexdigest()}
