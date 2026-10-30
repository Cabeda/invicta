"""Build a separate street-detail experiment; never overwrite the published study.

OSM crossings are observations in the frozen map, not a complete street survey.
Sidewalk geometry and signal programs produced by netconvert remain assumptions.
"""
from pathlib import Path
import argparse
import json
import subprocess
import xml.etree.ElementTree as ET

import sumo
import sumolib
from prepare import DATA, PILOT, digest, map_direction, write_json


def prepare_priority_model(destination, junction_corrections=None):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    raw = DATA / 'raw/osm-tile-0.xml'
    manifest = json.loads((DATA / 'network-manifest.json').read_text())
    import gzip
    archive = DATA / 'network.osm.xml.gz'
    if digest(archive) != manifest['archive_sha256']:
        raise ValueError('Frozen OSM source changed')
    raw_bytes = gzip.decompress(archive.read_bytes())
    if not raw.exists() or raw.read_bytes() != raw_bytes:
        raw.write_bytes(raw_bytes)
    location = ET.parse(DATA / 'baseline.net.xml').getroot().find('location')
    offset = location.get('netOffset').split(',')
    network = destination / 'baseline.net.xml'
    command = [str(Path(sumo.SUMO_HOME) / 'bin/netconvert'),
        '--osm-files', str(raw), '--output-file', str(network),
        '--proj', location.get('projParameter'), '--offset.disable-normalization', 'true',
        '--offset.x', offset[0], '--offset.y', offset[1],
        '--keep-edges.in-geo-boundary', ','.join(map(str, manifest['requested_bounds'])),
        '--geometry.remove', '--ramps.guess', '--junctions.join',
        '--tls.guess-signals', '--tls.discard-simple', '--tls.join',
        '--tls.default-type', 'actuated', '--tls.yellow.time', '3',
        '--tls.allred.time', '2', '--no-turnarounds',
        '--output.street-names', 'true', '--output.original-names', 'true',
        '--osm.bike-access', 'true', '--osm.sidewalks', 'true',
        '--osm.crossings', 'true', '--walkingareas', 'true',
        '--sidewalks.guess', 'true',
        '--keep-edges.by-vclass', 'passenger,bus,taxi,bicycle,motorcycle,pedestrian']
    correction = None
    if junction_corrections is not None:
        source = Path(junction_corrections)
        patch = destination / 'junction-corrections.nod.xml'
        patch.write_bytes(source.read_bytes())
        command += ['--node-files', str(patch)]
        correction = {'source': str(source), 'sha256': digest(patch),
                      'role': 'model_geometry_correction', 'field_validated': False}
    process = subprocess.run(command, capture_output=True, text=True)
    (destination / 'import.log').write_text(process.stdout + '\n' + process.stderr)
    if process.returncode:
        raise RuntimeError(process.stderr[-4000:])

    # The same explicit route-continuity overlay as v1. This is not a new
    # intervention, and is shared by every baseline/candidate in this study.
    net = sumolib.net.readNet(str(network), maxcache=0)
    connections = ET.Element('connections')
    adapted_overlays = []
    for item in json.loads((DATA / 'route-import-overlays.json').read_text())['connections']:
        if net.getEdge(item['from']).getToNode() != net.getEdge(item['to']).getFromNode():
            # Pedestrian import can prevent an old junction merge. Resolve only
            # an unambiguous fragment of the same OSM way at the actual node.
            candidates = [e for e in net.getEdge(item['to']).getFromNode().getIncoming()
                if e.getID().split('#')[0] == item['from'].split('#')[0] and e.allows('bus')]
            if len(candidates) != 1:
                raise ValueError('Cannot resolve bus-only route overlay at its real junction')
            replacement = {**item, 'from': candidates[0].getID()}
            adapted_overlays.append({'original': item, 'resolved': replacement})
            item = replacement
        a = next(l for l in net.getEdge(item['from']).getLanes() if l.allows('bus'))
        b = next(l for l in net.getEdge(item['to']).getLanes() if l.allows('bus'))
        ET.SubElement(connections, 'connection', **{k: item[k] for k in ['from', 'to', 'allow']},
                      fromLane=str(a.getIndex()), toLane=str(b.getIndex()))
    overlay = destination / 'overlay.con.xml'
    ET.ElementTree(connections).write(overlay, encoding='utf-8', xml_declaration=True)
    adjusted = destination / 'adjusted.net.xml'
    overlay_command = [command[0], '--sumo-net-file', str(network),
        '--connection-files', str(overlay), '--output-file', str(adjusted)]
    process = subprocess.run(overlay_command, capture_output=True, text=True)
    (destination / 'overlay.log').write_text(process.stdout + '\n' + process.stderr)
    if process.returncode:
        raise RuntimeError(process.stderr[-4000:])
    xml = ET.parse(adjusted)
    corrections = []
    for edge in xml.getroot().findall('edge'):
        # Unverified study cap, not a claim about actual posted limits.
        if any(t in edge.get('type', '') for t in ['motorway', 'trunk']):
            continue
        for lane in edge.findall('lane'):
            before = float(lane.get('speed'))
            if before > 50 / 3.6:
                lane.set('speed', str(50 / 3.6))
                corrections.append({'lane': lane.get('id'), 'before': before, 'after': 50 / 3.6})
    xml.write(network, encoding='utf-8', xml_declaration=True)
    net = sumolib.net.readNet(str(network), withInternal=True, maxcache=0)
    inbound = json.loads((PILOT / 'data/official-extension/full-line-service-facts.json').read_text())
    outbound = json.loads((PILOT / 'data/official-outbound/full-line-service-facts.json').read_text())
    shape = json.loads((PILOT / 'data/official/inbound_shape.json').read_text())['coordinates']
    directions = {'1': map_direction(net, inbound, shape),
                  '0': map_direction(net, outbound, outbound['shape'])}
    reference = {'directions': directions, 'reference_date': inbound['reference_date'],
        'network_sha256': digest(network),
        'trip_count': sum(len(d['trips']) for d in directions.values()),
        'served_calls': sum(len(t['stops']) for d in directions.values() for t in d['trips'])}
    write_json(destination / 'routes.json', reference)
    root = xml.getroot()
    report = {'schema': 1, 'model_version': 6 if correction else 5, 'shape_mapping_minimum_metres': .05,
        'stop_mapping_minimum_metres': 12.2,
        'stop_mapping_footprint_metres': 12,
        'osm_sha256': digest(archive), 'network_sha256': digest(network),
        'reference_sha256': digest(destination / 'routes.json'),
        'command': command, 'overlay_command': overlay_command, 'adapted_overlays': adapted_overlays,
        'crossings': sum(e.get('function') == 'crossing' for e in root.findall('edge')),
        'walkingareas': sum(e.get('function') == 'walkingarea' for e in root.findall('edge')),
        'signal_programs': len(root.findall('tlLogic')), 'speed_corrections': corrections,
        'limitations': ['Urban road speed capped at 50 km/h, preserving lower imported limits; unverified signage.',
            'Crossings imported from frozen OSM; sidewalk guesses are inferred, not surveyed.',
            'Signal phases, yellow (3 s) and all-red (2 s) are generated assumptions, not municipal timing plans.',
            'Known Porto signal equipment points do not establish controlled movements.',
            'Stop matching accepts road fragments long enough for the 12 m study bus; actual stopping footprints remain unsurveyed.',
            'Independent scheduled workings; no observed vehicle blocks.']}
    if correction is not None:
        report['junction_corrections'] = correction
    write_json(destination / 'model.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--junction-corrections', type=Path)
    args = parser.parse_args()
    print(json.dumps({k:v for k,v in prepare_priority_model(args.output, args.junction_corrections).items()
                      if k not in ['speed_corrections', 'command', 'overlay_command']}, indent=2))
