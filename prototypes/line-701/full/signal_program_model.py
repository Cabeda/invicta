"""Bind an inferred signal-programme variant to its unchanged timetable."""
import json
from pathlib import Path

from prepare import digest, write_json
from native_input_cache import intern_network


def derive_model(source, destination, writer, version, limitation):
    source, destination = Path(source), Path(destination)
    model = json.loads((source / 'model.json').read_text())
    if model.get('signal_program_override') or isinstance(model.get('signal_programs'), dict):
        raise ValueError('Combining programme corrections needs an explicit reviewed writer')
    if (digest(source / 'baseline.net.xml') != model['network_sha256']
            or digest(source / 'routes.json') != model['reference_sha256']):
        raise ValueError('Source model identity changed')
    destination.mkdir(parents=True, exist_ok=False)
    network = destination / 'baseline.net.xml'
    network.write_bytes((source / 'baseline.net.xml').read_bytes())
    intern_network(network)
    report = writer(network, destination / 'signal-programs.add.xml')
    reference = json.loads((source / 'routes.json').read_text())
    reference['signal_programs_sha256'] = digest(destination / 'signal-programs.add.xml')
    write_json(destination / 'routes.json', reference)
    model.update(model_version=version, reference_sha256=digest(destination / 'routes.json'),
        signal_program_override={'file': 'signal-programs.add.xml', 'sha256': reference['signal_programs_sha256'],
                         'source_model_sha256': digest(source / 'model.json'), **report})
    model['limitations'] += [limitation]
    write_json(destination / 'model.json', model)
    return model
