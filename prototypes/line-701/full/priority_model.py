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
from signal_mapping import (write_boundary_controls, verify_correction_scope,
                            verify_import_source, load_frozen_control, load_frozen_import,
                            inherited_junction_correction)


def cap_urban_speed(xml):
    """Apply the existing unsurveyed study cap after native conversion."""
    corrections = []
    for edge in xml.getroot().findall('edge'):
        if any(t in edge.get('type', '') for t in ['motorway', 'trunk']):
            continue
        for lane in edge.findall('lane'):
            before = float(lane.get('speed'))
            if before > 50 / 3.6:
                lane.set('speed', str(50 / 3.6))
                corrections.append({'lane': lane.get('id'), 'before': before, 'after': 50 / 3.6})
    return corrections


def prepare_priority_model(destination, junction_corrections=None, signal_corrections=None):
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
    imported = destination / 'imported.net.xml' if signal_corrections is not None else network
    command = [str(Path(sumo.SUMO_HOME) / 'bin/netconvert'),
        '--osm-files', str(raw), '--output-file', str(imported),
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
    if signal_corrections is not None:
        recipe_file = destination / 'signal-corrections.json'
        recipe_file.write_bytes(Path(signal_corrections).read_bytes())
        recipe = json.loads(recipe_file.read_text())
        if recipe['osm_sha256'] != digest(archive):
            raise ValueError('Signal correction refers to another OSM source')
        correction = inherited_junction_correction(recipe, correction)
        load_frozen_import(recipe, imported)
        (destination / 'import.log').write_text(
            'Materialized the hash-verified compatible frozen native import; no fresh OSM conversion executed.\n')
    else:
        process = subprocess.run(command, capture_output=True, text=True)
        (destination / 'import.log').write_text(process.stdout + '\n' + process.stderr)
        if process.returncode:
            raise RuntimeError(process.stderr[-4000:])

    # The same explicit route-continuity overlay as v1. This is not a new
    # intervention, and is shared by every baseline/candidate in this study.
    net = sumolib.net.readNet(str(imported), maxcache=0)
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
    overlay_command = [command[0], '--sumo-net-file', str(imported),
        '--connection-files', str(overlay), '--output-file', str(adjusted)]
    signal_correction = None
    if signal_corrections is not None:
        control = destination / 'control.net.xml'
        verify_import_source(imported, recipe)
        control_identity = load_frozen_control(recipe, control)
        write_json(destination / 'control-source.json', control_identity)
        signal_patch = destination / 'signal-corrections.con.xml'
        signal_correction = write_boundary_controls(control, recipe, signal_patch)
        corrected = destination / 'signal-adjusted.net.xml'
        correction_command = [command[0], '--sumo-net-file', str(imported),
            '--connection-files', str(signal_patch), '--output-file', str(corrected)]
        overlay_command = correction_command
        process = subprocess.run(correction_command, capture_output=True, text=True)
        (destination / 'signal-corrections.log').write_text(process.stdout + '\n' + process.stderr)
        if process.returncode:
            raise RuntimeError(process.stderr[-4000:])
        xml = ET.parse(corrected)
        corrections = cap_urban_speed(xml)
        xml.write(network, encoding='utf-8', xml_declaration=True)
        scope = verify_correction_scope(control, network, recipe)
        write_json(destination / 'signal-scope-audit.json', scope)
        signal_correction.update(recipe_sha256=digest(recipe_file), patch_sha256=digest(signal_patch),
            source_control_network_sha256=digest(control), scope_audit_sha256=digest(destination / 'signal-scope-audit.json'),
            imported_network_sha256=digest(imported), control_source_sha256=digest(destination / 'control-source.json'),
            requires_regional_scope_review=False, command=correction_command)
    else:
        process = subprocess.run(overlay_command, capture_output=True, text=True)
        (destination / 'overlay.log').write_text(process.stdout + '\n' + process.stderr)
        if process.returncode:
            raise RuntimeError(process.stderr[-4000:])
        xml = ET.parse(adjusted)
        corrections = cap_urban_speed(xml)
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
    report = {'schema': 1, 'model_version': 9 if signal_correction else 6 if correction else 5, 'shape_mapping_minimum_metres': .05,
        'stop_mapping_minimum_metres': 12.2,
        'stop_mapping_footprint_metres': 12,
        'osm_sha256': digest(archive), 'network_sha256': digest(network),
        'reference_sha256': digest(destination / 'routes.json'),
        'command': command if signal_corrections is None else None,
        'import_mode': 'frozen_compiled_source' if signal_corrections is not None else 'osm_conversion',
        'overlay_command': overlay_command, 'adapted_overlays': adapted_overlays,
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
    if signal_correction is not None:
        report['signal_mapping_correction'] = signal_correction
        report['limitations'] += [
            'Combatentes internal controls removed by an opt-in mapping correction; external phases remain inferred.',
            'Unused internal-only stages remain in the generated programme; no municipal timing plan is available.',
            'Pedestrian connectivity is retained; crossing coverage and signal clearance remain unsurveyed.']
    write_json(destination / 'model.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--junction-corrections', type=Path)
    parser.add_argument('--signal-corrections', type=Path)
    args = parser.parse_args()
    print(json.dumps({k:v for k,v in prepare_priority_model(args.output, args.junction_corrections, args.signal_corrections).items()
                      if k not in ['speed_corrections', 'command', 'overlay_command']}, indent=2))
