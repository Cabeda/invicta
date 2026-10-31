"""Freeze native stress trials, including failed attempts, without promoting them."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare import write_json
from trial_evidence import load_trial


def archive_study(work, destination, models, *, local_cases=None):
    work, destination = Path(work), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    objects = destination / 'objects'
    objects.mkdir()

    def freeze(path):
        raw = path.read_bytes()
        signature = hashlib.sha256(raw).hexdigest()
        target = objects / (signature + '.gz')
        if not target.exists():
            target.write_bytes(gzip.compress(raw, compresslevel=6, mtime=0))
        return {'file': str(target.relative_to(destination)), 'sha256': signature,
                'gzip_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'bytes': len(raw)}

    ledger = {'schema': 'invicta.traffic-stress.v1', 'role': 'uncalibrated_native_investigation',
              'qualified': False, 'field_validated': False, 'models': {}, 'trials': [],
              'incomplete_attempts': [], 'freezer': freeze(Path(__file__))}
    identities = {}
    for ident, folder in models.items():
        folder = Path(folder)
        metadata = json.loads((folder / 'model.json').read_text())
        names = ['baseline.net.xml', 'routes.json', 'model.json']
        if (folder / 'signal-programs.add.xml').exists():
            names.append('signal-programs.add.xml')
        if (folder / 'geometry-recipe.json').exists():
            names.append('geometry-recipe.json')
            reference = json.loads((folder / 'routes.json').read_text())
            if reference.get('geometry_correction_sha256') != hashlib.sha256((folder / 'geometry-recipe.json').read_bytes()).hexdigest():
                raise ValueError('Geometry recipe does not bind its model reference')
        evidence = {name: freeze(folder / name) for name in names}
        key = (metadata['network_sha256'], metadata['reference_sha256'])
        if key in identities or evidence['baseline.net.xml']['sha256'] != key[0] or evidence['routes.json']['sha256'] != key[1]:
            raise ValueError('Ambiguous or changed archive model')
        identities[key] = ident
        ledger['models'][ident] = {'network_sha256': key[0], 'reference_sha256': key[1], 'evidence': evidence}
    for folder in sorted((work / 'trials').iterdir()):
        if not folder.is_dir():
            continue
        if not (folder / 'result.json').exists():
            files = [p for p in folder.iterdir() if p.is_file()]
            ledger['incomplete_attempts'].append({'id': folder.name, 'status': 'no_complete_result',
                                                   'evidence': {p.name: freeze(p) for p in files}})
            continue
        source = load_trial(folder)
        result = source.result
        names = list(dict.fromkeys([*result['input_hashes'], *result['output_hashes'], 'result.json']))
        for name in names:
            if name != 'result.json':
                source.payload(name)
        supplementary = {}
        monitor = json.loads(source.payload('monitor.json')) if source.available('monitor.json') else {}
        for snapshot in result.get('diagnostics', {}).get('snapshots', []):
            name = snapshot['file']
            if name in names:
                continue
            if Path(name).name != name or snapshot not in monitor.get('snapshots', []):
                raise ValueError('Supplementary snapshot lacks its recorded monitor binding')
            descriptor = freeze(folder / name)
            if descriptor['sha256'] != snapshot['sha256']:
                raise ValueError('Supplementary native snapshot changed')
            supplementary[name] = descriptor
        model_id = identities[(result['network_model'], result['reference_sha256'])]
        ledger['trials'].append({**result, 'id': folder.name, 'model_id': model_id,
                                'evidence': {name: freeze(folder / name) for name in names},
                                'supplementary_snapshot_evidence': supplementary})
    ledger['supplementary'] = {p.name: freeze(p) for p in sorted(work.iterdir())
                               if p.is_file() and p.suffix in ['.json', '.log', '.py']}
    ledger['local_cases'] = {}
    for ident, folder in (local_cases or {}).items():
        folder = Path(folder)
        metadata = folder / 'case.json' if (folder / 'case.json').exists() else folder / 'error.json'
        case = json.loads(metadata.read_text())
        if case.get('qualified') is not False:
            raise ValueError('A local reproduction cannot qualify a complete proposal')
        bindings = {**case.get('input_hashes', {}), **case.get('output_hashes', {})}
        for name, signature in bindings.items():
            if Path(name).name != name or hashlib.sha256((folder / name).read_bytes()).hexdigest() != signature:
                raise ValueError('Changed local native evidence')
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix not in ['.html', '.mjs']]
        ledger['local_cases'][ident] = {'status':'failed_native' if metadata.name == 'error.json' else 'recorded',
            'qualified':False, 'evidence':{p.name:freeze(p) for p in files}}
    manifest = destination / 'study.pending.json'
    write_json(manifest, ledger)
    # The frozen public interface must produce the same counts from raw outputs.
    from timetable import assess_trial
    for row in ledger['trials']:
        source = load_trial(manifest, row['id'])
        strict = assess_trial(source.buses, source.calls(), source.completed())
        actual = assess_trial(source.buses, source.calls(), source.completed(),
                              lateness_tolerance_seconds=row['acceptance_criteria']['lateness_tolerance_seconds'])
        if strict != row['metrics'] or actual != row['operational_metrics']:
            raise ValueError('Archived timing evaluation differs from native outputs')
    final = destination / 'study.json'
    manifest.replace(final)
    return final


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--model', action='append', required=True, help='ID=MODEL_FOLDER')
    args = parser.parse_args()
    print(archive_study(args.work, args.destination, dict(item.split('=', 1) for item in args.model)))
