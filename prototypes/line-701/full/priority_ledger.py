"""Publish a complete failed/successful native trial ledger with frozen outputs."""
from pathlib import Path
import argparse
import gzip
import hashlib
import io
import json
import xml.etree.ElementTree as ET
from sumolib.net.lane import get_allowed
from prepare import DATA, digest, write_json
from timetable import assess_trial
from trial_evidence import read_archive

MODEL_CATALOG = {
    'model': {'id': 'street-detail-v2-superseded', 'current': False, 'defect': None},
    'model-v3': {'id': 'street-detail-v3', 'current': False,
        'defect': 'Superseded route matching: Alfena was placed on Rua Coroa instead of São Vicente; this is a model defect, not a street intervention.'},
    'model-v4': {'id': 'street-detail-v4', 'current': False,
        'defect': 'Superseded route matching: a short shape-anchor filter still forced a spur onto Rua da Várzea; this is a model defect, not a street intervention.'},
    'model-v5': {'id': 'street-detail-v5', 'current': True, 'defect': None},
}


def verify_ledger(path):
    """Re-evaluate the public timetable claim from frozen native bus calls."""
    ledger = json.loads(path.read_text())
    references = {'v1-empty-diagnostic': json.loads((DATA / 'routes.json').read_text())}
    def payload(item):
        data = (path.parent / item['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['gzip_sha256']:
            raise ValueError('Changed compressed native evidence')
        raw = gzip.decompress(data)
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Changed native evidence')
        return raw
    for ident, model in ledger['models'].items():
        reference_bytes = payload(model['evidence']['routes.json'])
        if hashlib.sha256(reference_bytes).hexdigest() != model['reference_sha256']:
            raise ValueError('Model route reference changed')
        references[ident] = json.loads(reference_bytes)
        payload(model['evidence']['model.json'])
    matched_inputs = {}
    for trial in ledger['trials']:
        ref = references[trial['model_id']]
        if trial.get('reference_sha256') and trial['reference_sha256'] != ledger['models'][trial['model_id']]['reference_sha256']:
            raise ValueError('Trial belongs to a different route reference')
        buses = [t for d in ref['directions'].values() for t in d['trips']]
        files = {name: payload(item) for name, item in trial['evidence'].items()}
        if 'result.json' in files:
            original = json.loads(files['result.json'])
            for name in ['config', 'network_model', 'reference_sha256', 'input_hashes', 'output_hashes', 'command']:
                if original.get(name) != trial.get(name):
                    raise ValueError('Archived execution metadata disagrees with original execution binding')
        for name, fingerprint in trial.get('output_hashes', {}).items():
            if name not in files or hashlib.sha256(files[name]).hexdigest() != fingerprint:
                raise ValueError('Archived output disagrees with original execution binding')
        for name, fingerprint in trial.get('input_hashes', {}).items():
            if name in files and hashlib.sha256(files[name]).hexdigest() != fingerprint:
                raise ValueError('Archived input disagrees with original execution binding')
        if trial.get('demand_mapping_sha256') and hashlib.sha256(files['endpoint-mapping.json']).hexdigest() != trial['demand_mapping_sha256']:
            raise ValueError('Archived physical demand mapping changed')
        rows = ET.fromstring(files['trips.xml'])
        completed = {t.get('id') for t in rows if t.tag == 'tripinfo' and float(t.get('arrival', -1)) >= 0}
        measured = assess_trial(buses, [c.attrib for c in ET.fromstring(files['stops.xml'])],
                                completed & {t['id'] for t in buses})
        if measured != trial['metrics']:
            raise ValueError('Stale public timetable result: ' + trial['id'])
        arrived = lambda prefix: sum(p.tag == 'personinfo' and p.get('id').startswith(prefix)
            and len(p) > 0 and all(float(stage.get('arrival', -1)) >= 0 for stage in p) for p in rows)
        if arrived('passenger_') != trial.get('arrived_passengers', 0) or arrived('walking_') != trial.get('arrived_walkers', 0):
            raise ValueError('Stale passenger or pedestrian outcome')
        ordinary_completed = len(completed - {b['id'] for b in buses})
        if trial['vehicle_requests'] - ordinary_completed != trial['unserved_vehicle_requests']:
            raise ValueError('Unserved ordinary vehicle denominator changed')
        if 'network.net.xml' in files:
            permissions = []
            for _, element in ET.iterparse(io.BytesIO(files['network.net.xml']), events=['end']):
                if element.tag == 'lane':
                    permissions.append((element.get('id'), 'pedestrian' in get_allowed(element.get('allow'), element.get('disallow'))))
                elif element.tag == 'edge':
                    element.clear()
            cars, persons = [], []
            for _, element in ET.iterparse(io.BytesIO(files['routes.rou.xml']), events=['end']):
                if element.tag == 'vehicle':
                    if element.get('type') != 'bus':
                        edges = element.find('route').get('edges').split()
                        cars.append([dict(element.attrib), edges[0], edges[-1]])
                    element.clear()
                elif element.tag == 'person':
                    persons.append([dict(element.attrib), [(c.tag, dict(c.attrib)) for c in element]])
                    element.clear()
            if len(cars) != trial['vehicle_requests'] or trial['unroutable_requests']:
                raise ValueError('Physical OD workload was dropped or disconnected')
            if len([t for t in rows if t.tag == 'tripinfo']) != len(cars) + len(buses):
                raise ValueError('Native outputs omitted requested vehicles')
            config = trial['config']
            key = (trial['network_model'], trial['reference_sha256'], trial['traffic'], trial['seed'],
                   config.get('passengers_per_minute'), config.get('crossing_persons_per_minute'))
            signatures = [hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                          for value in [cars, persons, sorted(permissions)]]
            if key in matched_inputs and signatures != matched_inputs[key]:
                raise ValueError('Paired physical demand or pedestrian permissions differ')
            matched_inputs[key] = signatures
        if 'priority-events.json' in files:
            for event in json.loads(files['priority-events.json']):
                if event.get('kind', 'extend_green') == 'extend_green' and event['after_switch'] > event['bound']:
                    raise ValueError('Signal extension exceeded its bound')
                if event.get('kind') == 'end_conflicting_green' and event['spent'] < event['minimum']:
                    raise ValueError('Signal priority violated its configured minimum')
        if trial.get('qualified'):
            raise ValueError('Unvalidated exploratory evidence cannot qualify a production proposal')
    if ledger['winner'] is not None:
        raise ValueError('Exploratory ledger cannot declare a verified winner')
    return ledger


def export_ledger(cache, destination):
    destination.mkdir(exist_ok=True, parents=True)
    models = {}
    for name, registration in MODEL_CATALOG.items():
        folder = cache / name
        model = json.loads((folder / 'model.json').read_text())
        # A stop/path rematch changes the model even when the road network is
        # byte-identical. Never let a network hash alias two route references.
        identity = (model['network_sha256'], model['reference_sha256'])
        if identity in models:
            raise ValueError('Two model registrations alias the same network and route reference')
        models[identity] = (registration, folder, model)
    trials = []
    evidence = destination / 'priority-evidence'
    evidence.mkdir(exist_ok=True)
    configs = destination / 'priority-configs'
    configs.mkdir(exist_ok=True)
    shared_inputs = {}
    previous = destination / 'priority-search.json'
    if previous.exists():
        for trial in json.loads(previous.read_text())['trials']:
            for name, item in trial.get('evidence', {}).items():
                if name in ['network.net.xml', 'routes.rou.xml', 'additional.add.xml']:
                    shared_inputs[item['sha256']] = item

    def freeze(folder, ident, archive_inputs=False):
        files = {}
        target = evidence / ident
        target.mkdir(exist_ok=True)
        names = ['stops.xml', 'trips.xml', 'collisions.xml', 'priority-events.json', 'endpoint-mapping.json', 'result.json', 'final-state.xml']
        if '-mapped-' in ident or archive_inputs:
            names += ['network.net.xml', 'routes.rou.xml', 'additional.add.xml']
        if archive_inputs:
            original = json.loads((folder / 'result.json').read_text())
            names += list(original['input_hashes']) + list(original.get('output_hashes', {}))
        for name in dict.fromkeys(names):
            source = folder / name
            if not source.exists():
                continue
            fingerprint = digest(source)
            if name in ['network.net.xml', 'routes.rou.xml', 'additional.add.xml'] and fingerprint in shared_inputs:
                item = shared_inputs[fingerprint]
                read_archive(destination, item)
                files[name] = item
                continue
            payload = gzip.compress(source.read_bytes(), mtime=0)
            path = target / (name + '.gz')
            path.write_bytes(payload)
            files[name] = {'file': str(path.relative_to(destination)),
                'sha256': fingerprint, 'gzip_sha256': digest(path)}
            if name in ['network.net.xml', 'routes.rou.xml', 'additional.add.xml']:
                shared_inputs[fingerprint] = files[name]
        return files

    for path in sorted((cache / 'trials').glob('*/result.json')):
        result = json.loads(path.read_text())
        registration, model_folder, model = models[(result['network_model'], result['reference_sha256'])]
        ident = registration['id']
        reference = json.loads((model_folder / 'routes.json').read_text())
        if digest(model_folder / 'routes.json') != result['reference_sha256']:
            raise ValueError('Changed trial reference')
        for name, fingerprint in result['input_hashes'].items():
            if digest(path.parent / name) != fingerprint:
                raise ValueError('Changed native trial input: ' + str(path.parent / name))
        for name, fingerprint in result.get('output_hashes', {}).items():
            if digest(path.parent / name) != fingerprint:
                raise ValueError('Changed native trial output: ' + str(path.parent / name))
        buses = [t for d in reference['directions'].values() for t in d['trips']]
        trip_rows = list(ET.parse(path.parent / 'trips.xml').getroot())
        completed = {t.get('id') for t in trip_rows if t.tag == 'tripinfo' and float(t.get('arrival', -1)) >= 0}
        metrics = assess_trial(buses, [c.attrib for c in ET.parse(path.parent / 'stops.xml').getroot()], completed & {t['id'] for t in buses})
        if result.get('grading_schema', 1) >= 2 and metrics != result['metrics']:
            raise ValueError('Trial metrics disagree with native output')
        # Earlier experimental parser looked for arrival on personinfo rather
        # than its child ride. Recompute all passenger totals from frozen output.
        def arrived(prefix):
            return sum(p.tag == 'personinfo' and p.get('id').startswith(prefix) and len(p) > 0
                and all(float(stage.get('arrival', -1)) >= 0 for stage in p) for p in trip_rows)
        config = result['config']
        write_json(configs / (config['id'] + '.json'), config)
        labels = {
            'v3-fixed20-s17': ('Compulsory 20-second stops', 'Paragens obrigatórias de 20 segundos'),
            'v3-request5-s17': ('Request stops + faster boarding', 'Paragens a pedido + embarque mais rápido'),
            'v3-smart-s17': ('Boarding + signal priority', 'Embarque + prioridade semafórica'),
            'v3-bays-smart-s17': ('Priority + off-line timetable holding', 'Prioridade + regulação fora da via'),
            'v3-articulated-smart-s17': ('Priority + larger buses', 'Prioridade + autocarros de maior capacidade'),
            'v3-clearance-aware-smart-r2-s17': ('Priority + crossing-clearance sensitivity', 'Prioridade + teste de tempos de travessia'),
            'baseline-moderate-s17': ('Earlier network · traffic baseline', 'Rede anterior · referência com tráfego'),
            'priority-package-moderate-s17': ('Earlier network · lanes, boarding & signal priority', 'Rede anterior · vias, embarque e prioridade semafórica')}
        labels.update({
            'v3-moderate-baseline-mapped-s17': ('Matched traffic · baseline', 'Tráfego com origens e destinos preservados · referência'),
            'v3-moderate-priority-mapped-s17': ('Matched traffic · lanes, boarding, signals & holding', 'Tráfego com origens e destinos preservados · vias, embarque, semáforos e regulação')})
        labels.update({
            'v4-bays-smart-s17': ('Intermediate rematch · boarding, signals & holding', 'Remapeamento intermédio · embarque, semáforos e regulação'),
            'v5-bays-smart-s17': ('Current route · no ordinary traffic · boarding, signals & holding', 'Traçado atual · sem tráfego automóvel · embarque, semáforos e regulação'),
            'v5-moderate-baseline-mapped-s17': ('Current route · traffic baseline', 'Traçado atual · referência com tráfego'),
            'v5-moderate-priority-mapped-s17': ('Current route · lanes, boarding, signals & holding', 'Traçado atual · vias, embarque, semáforos e regulação')})
        en, pt = labels.get(config['id'], (config['id'], config['id']))
        defects = []
        if config['id'] in ['baseline-moderate-s17', 'priority-package-moderate-s17']:
            defects.append('8,581 requests used obsolete endpoint edge IDs and were unroutable; excluded from proposal comparisons.')
        if config['id'] == 'priority-package-moderate-s17':
            defects.append('Lane conversion added pedestrian permission to 88 lanes; excluded from proposal comparisons.')
        if registration['defect']:
            defects.append(registration['defect'])
        mapping = json.loads((path.parent / 'endpoint-mapping.json').read_text()) if (path.parent / 'endpoint-mapping.json').exists() else None
        trials.append({**result, 'id': config['id'], 'model_id': ident,
            'grading_schema': 2, 'execution_grading_schema': result.get('grading_schema', 1),
            'grading_note': 'Observed calls retain their observed status even when the vehicle never exits; incomplete trips still fail the overall goal. Original execution metadata is archived unchanged.',
            'output_binding': 'recorded_at_completion' if result.get('output_hashes') else 'first_archive_only',
            'label': {'en': en, 'pt': pt},
            'invalid_reasons': defects, 'eligible_for_comparison': not defects and registration['current'],
            'demand_mapping': ({**{k:v for k,v in mapping.items() if k != 'mappings'},
                'endpoint_count': len(mapping['mappings']),
                'max_snap_metres': max((m['distance_metres'] for m in mapping['mappings']), default=0)} if mapping else None),
            'traffic': config['traffic'], 'seed': config['seed'], 'metrics': metrics,
            'arrived_passengers': arrived('passenger_'), 'arrived_walkers': arrived('walking_'),
            'diagnostic_only': bool(config.get('diagnostic_all_green')) or
                config.get('passengers_per_minute', 0) == 0,
            'superseded_model': not registration['current'],
            'evidence': freeze(path.parent, config['id'], archive_inputs=registration['current'])})
    # Retain the eight earlier bus-only controls rather than selecting favourable
    # runs. They cannot be used to qualify a traffic proposal.
    reference = json.loads((DATA / 'routes.json').read_text())
    buses = [t for d in reference['directions'].values() for t in d['trips']]
    for bound in json.loads((cache / 'bounds/summary.json').read_text()):
        folder = cache / 'bounds' / bound['id']
        rows = list(ET.parse(folder / 'trips.xml').getroot())
        done = {t.get('id') for t in rows if float(t.get('arrival', -1)) >= 0}
        metrics = assess_trial(buses, [c.attrib for c in ET.parse(folder / 'stops.xml').getroot()], done)
        trials.append({'id': bound['id'], 'model_id': 'v1-empty-diagnostic', 'traffic': 'none',
            'seed': 17, 'diagnostic_only': True, 'superseded_model': True, 'metrics': metrics,
            'config': bound, 'passenger_requests': 0, 'arrived_passengers': 0,
            'vehicle_requests': 0, 'unserved_vehicle_requests': 0,
            'evidence': freeze(folder, bound['id']), 'qualified': False})
    published_models = {}
    for registration, folder, model in models.values():
        ident = registration['id']
        target = evidence / ident
        target.mkdir(exist_ok=True)
        sources = {}
        for name in ['routes.json', 'model.json']:
            output = target / (name + '.gz')
            output.write_bytes(gzip.compress((folder / name).read_bytes(), mtime=0))
            sources[name] = {'file': str(output.relative_to(destination)),
                'sha256': digest(folder / name), 'gzip_sha256': digest(output)}
        published_models[ident] = {k:v for k,v in model.items() if k != 'speed_corrections'}
        published_models[ident].update(speed_correction_count=len(model['speed_corrections']), evidence=sources)
    value = {'schema': 'invicta.priority-search.v1', 'line': '701', 'winner': None,
        'target': 'Every origin departure and intermediate designated timing-point departure exactly on time; every terminal arrival no later than published; no missing trips. Zero tolerance.',
        'required_traffic_cases': ['moderate', 'busy', 'late'], 'required_seeds': [17, 29, 43],
        'qualification': 'No complete calibrated matrix. Diagnostic, superseded, bus-only and single-seed results cannot qualify a production proposal.',
        'models': published_models, 'trials': trials,
        'failed_attempts': [json.loads(p.read_text()) for p in sorted((cache / 'trials').glob('*/error.json'))]}
    write_json(destination / 'priority-search.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print('Frozen native trials:', len(export_ledger(args.cache, args.output)['trials']))
