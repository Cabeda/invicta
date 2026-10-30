"""Load one native execution, checking only the evidence actually requested."""
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_archive(root, item):
    path = (root / item['file']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Evidence path leaves its archive')
    compressed = path.read_bytes()
    if sha256(compressed) != item['gzip_sha256']:
        raise ValueError('Changed compressed native evidence')
    raw = gzip.decompress(compressed)
    if sha256(raw) != item['sha256']:
        raise ValueError('Changed native evidence')
    return raw


class TrialEvidence:
    """A reference and a lazy, verified view of its recorded native execution."""

    def __init__(self, reference_bytes, result, reader, identity):
        self.reference_bytes = reference_bytes
        self.reference = json.loads(reference_bytes)
        self.result = result
        self.identity = identity
        self._reader = reader
        self._loaded = {}

    def payload(self, name):
        if name not in self._loaded:
            raw = self._reader(name)
            binding = {**self.result.get('input_hashes', {}), **self.result.get('output_hashes', {})}
            if name not in binding:
                raise ValueError('File has no recorded native execution binding: ' + name)
            if sha256(raw) != binding[name]:
                raise ValueError('Native evidence differs from execution binding: ' + name)
            self._loaded[name] = raw
        return self._loaded[name]

    def available(self, name):
        return name in self.identity['available_files']

    @property
    def buses(self):
        return [trip for direction in self.reference['directions'].values() for trip in direction['trips']]

    def calls(self):
        return [dict(row.attrib) for row in ET.fromstring(self.payload('stops.xml'))]

    def completed(self):
        ids = {trip['id'] for trip in self.buses}
        return {row.get('id') for row in ET.fromstring(self.payload('trips.xml'))
                if row.tag == 'tripinfo' and row.get('id') in ids and float(row.get('arrival', -1)) >= 0}

    def verified_identity(self):
        return {**self.identity, 'verified_files': {name: sha256(raw) for name, raw in self._loaded.items()}}


def load_trial(source, trial_id=None, model=None):
    source = Path(source)
    if source.is_dir():
        if trial_id:
            raise ValueError('A native folder already identifies one trial')
        metadata = source / 'result.json'
        if not metadata.exists():
            metadata = source / 'reproduction.json'
        original_bytes = metadata.read_bytes()
        original = json.loads(original_bytes)
        local_reference = source / 'reference.json'
        if local_reference.exists():
            reference_bytes = local_reference.read_bytes()
            if model is not None and sha256((Path(model) / 'routes.json').read_bytes()) != sha256(reference_bytes):
                raise ValueError('Explicit model differs from the frozen trial reference')
        elif model is not None:
            reference_bytes = (Path(model) / 'routes.json').read_bytes()
        else:
            raise ValueError('This older native trial requires its explicit model folder')
        def reader(name):
            if Path(name).name != name:
                raise ValueError('Native file name must be local to its trial')
            return (source / name).read_bytes()
        identity = {'kind': 'native_folder', 'trial': original['config']['id'],
                    'available_files': [p.name for p in source.iterdir() if p.is_file()]}
    else:
        ledger = json.loads(source.read_bytes())
        matches = [trial for trial in ledger['trials'] if trial['id'] == trial_id]
        if len(matches) != 1:
            raise ValueError('Select exactly one archived trial')
        trial = matches[0]
        descriptor = ledger['models'].get(trial['model_id'])
        if descriptor is None or 'result.json' not in trial['evidence']:
            raise ValueError('Legacy trial lacks a self-contained execution/reference binding')
        original_bytes = read_archive(source.parent, trial['evidence']['result.json'])
        original = json.loads(original_bytes)
        for key in ['config', 'network_model', 'reference_sha256', 'input_hashes', 'output_hashes', 'command']:
            if original.get(key) != trial.get(key):
                raise ValueError('Archive differs from original execution binding')
        reference_bytes = read_archive(source.parent, descriptor['evidence']['routes.json'])
        if sha256(reference_bytes) != descriptor['reference_sha256']:
            raise ValueError('Changed model reference')
        def reader(name):
            if name not in trial['evidence']:
                raise ValueError('Native file not archived: ' + name)
            return read_archive(source.parent, trial['evidence'][name])
        identity = {'kind': 'archive', 'trial': trial_id, 'model': trial['model_id'],
                    'manifest_sha256': sha256(source.read_bytes()),
                    'available_files': sorted(trial['evidence'])}
    if sha256(reference_bytes) != original['reference_sha256']:
        raise ValueError('Trial belongs to a different route reference')
    identity.update(reference_sha256=sha256(reference_bytes), network_sha256=original['network_model'],
                    execution_sha256=sha256(original_bytes))
    return TrialEvidence(reference_bytes, original, reader, identity)
