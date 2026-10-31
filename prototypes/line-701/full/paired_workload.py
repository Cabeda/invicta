"""Reuse verified physical inputs when changing only the signal controller."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from prepare import digest, write_json
from trial_evidence import load_trial

CONTROLLER_FIELDS = {'signal_priority', 'early_green', 'shorten_served_pedestrian_green',
                     'extension_limit', 'priority_tls', 'priority_min_green'}
METADATA_FIELDS = {'id', 'hypothesis', 'readiness', 'paired_workload'}
INPUTS = ['network.net.xml', 'routes.rou.xml', 'additional.add.xml',
          'endpoint-mapping.json', 'crossing-requests.json', 'compiled-audit.json', 'traffic-workload.json']


def reuse_workload(model, folder, config):
    source = load_trial(Path(config['paired_workload']))
    original = source.result['config']
    for key in (original.keys() | config.keys()) - CONTROLLER_FIELDS - METADATA_FIELDS:
        if original.get(key) != config.get(key):
            raise ValueError('Paired workload changes a physical/acceptance setting: ' + key)
    if (config.get('lanes') or config.get('lane_edges') or source.result.get('lane_changes')
            or source.identity['network_sha256'] != digest(model / 'baseline.net.xml')
            or source.identity['reference_sha256'] != digest(model / 'routes.json')):
        raise ValueError('Controller-only reuse requires the unchanged source model and lane permissions')
    for name in INPUTS:
        (folder / name).write_bytes(source.payload(name))
    buses = source.buses
    bus_ids = {bus['id'] for bus in buses}
    vehicles = ET.parse(folder / 'routes.rou.xml').getroot().findall('vehicle')
    ordinary = [row.attrib for row in vehicles if row.get('id') not in bus_ids]
    if (len(ordinary) != source.result['vehicle_requests']
            or len(vehicles) != len(ordinary) + len(bus_ids)
            or {row.get('id') for row in vehicles if row.get('type') == 'bus'} != bus_ids):
        raise ValueError('Frozen workload does not contain every expected actor')
    write_json(folder / 'workload-source.json', {'source': source.verified_identity(),
        'copied_input_hashes': {name: digest(folder / name) for name in INPUTS},
        'meaning': 'Exact same physical inputs; signal-controller options are the only permitted changes.'})
    return (source.reference, buses, ordinary, source.result['passenger_requests'], [], [],
            source.result.get('shock_vehicle'), source.result.get('walking_requests', 0))
