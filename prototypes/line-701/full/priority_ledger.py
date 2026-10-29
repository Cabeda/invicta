"""Publish a complete failed/successful native trial ledger with frozen outputs."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import xml.etree.ElementTree as ET
from prepare import DATA, digest, write_json
from priority_search import assess_trial


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
        references[ident] = json.loads(payload(model['evidence']['routes.json']))
        payload(model['evidence']['model.json'])
    for trial in ledger['trials']:
        ref = references[trial['model_id']]
        buses = [t for d in ref['directions'].values() for t in d['trips']]
        files = {name: payload(item) for name, item in trial['evidence'].items()}
        rows = ET.fromstring(files['trips.xml'])
        completed = {t.get('id') for t in rows if t.tag == 'tripinfo' and float(t.get('arrival', -1)) >= 0}
        measured = assess_trial(buses, [c.attrib for c in ET.fromstring(files['stops.xml'])],
                                completed & {t['id'] for t in buses})
        if measured != trial['metrics']:
            raise ValueError('Stale public timetable result: ' + trial['id'])
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
    for folder in [cache / 'model', cache / 'model-v3']:
        model = json.loads((folder / 'model.json').read_text())
        ident = 'street-detail-v3' if folder.name == 'model-v3' else 'street-detail-v2-superseded'
        models[model['network_sha256']] = (ident, folder, model)
    trials = []
    evidence = destination / 'priority-evidence'
    evidence.mkdir(exist_ok=True)
    configs = destination / 'priority-configs'
    configs.mkdir(exist_ok=True)

    def freeze(folder, ident):
        files = {}
        target = evidence / ident
        target.mkdir(exist_ok=True)
        for name in ['stops.xml', 'trips.xml', 'collisions.xml', 'priority-events.json']:
            source = folder / name
            if not source.exists():
                continue
            payload = gzip.compress(source.read_bytes(), mtime=0)
            path = target / (name + '.gz')
            path.write_bytes(payload)
            files[name] = {'file': str(path.relative_to(destination)),
                'sha256': digest(source), 'gzip_sha256': digest(path)}
        return files

    for path in sorted((cache / 'trials').glob('*/result.json')):
        result = json.loads(path.read_text())
        ident, model_folder, model = models[result['network_model']]
        reference = json.loads((model_folder / 'routes.json').read_text())
        if digest(model_folder / 'routes.json') != result['reference_sha256']:
            raise ValueError('Changed trial reference')
        for name, fingerprint in result['input_hashes'].items():
            if digest(path.parent / name) != fingerprint:
                raise ValueError('Changed native trial input: ' + str(path.parent / name))
        buses = [t for d in reference['directions'].values() for t in d['trips']]
        trip_rows = list(ET.parse(path.parent / 'trips.xml').getroot())
        completed = {t.get('id') for t in trip_rows if t.tag == 'tripinfo' and float(t.get('arrival', -1)) >= 0}
        metrics = assess_trial(buses, [c.attrib for c in ET.parse(path.parent / 'stops.xml').getroot()], completed & {t['id'] for t in buses})
        if metrics != result['metrics']:
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
        en, pt = labels.get(config['id'], (config['id'], config['id']))
        trials.append({**result, 'id': config['id'], 'model_id': ident,
            'label': {'en': en, 'pt': pt},
            'traffic': config['traffic'], 'seed': config['seed'], 'metrics': metrics,
            'arrived_passengers': arrived('passenger_'), 'arrived_walkers': arrived('walking_'),
            'diagnostic_only': bool(config.get('diagnostic_all_green')) or
                config.get('passengers_per_minute', 0) == 0,
            'superseded_model': ident.endswith('superseded'),
            'evidence': freeze(path.parent, config['id'])})
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
    for ident, folder, model in models.values():
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
