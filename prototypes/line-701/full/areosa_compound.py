"""Rebuild the diagnosed Areosa split junction from the frozen native import.

This model experiment includes regenerated inferred phases. Scope preservation
is checked against the final V9 control; it is not a surveyed junction design.
"""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import sumo
from prepare import digest, write_json
from priority_model import cap_urban_speed
from junction_scope import audit_scope

JOIN = {'1838444495', '12085962393', 'cluster_10121898407_1103464865_112613628_112613629_#12more'}
FRINGE = {'1838445085', '4751802409', '12085962392', '12514558241', '12514558260'}
CONTROLLERS = {'joinedS_1838444495_1838445085_cluster_10121898407_1103464865_112613628_112613629_#12more',
               'areosa_compound'}


def rebuild(source, destination):
    source, destination = Path(source), Path(destination)
    expected = {'baseline.net.xml': '64eeea8de7a2c43aac704faabef47e8500b71d57054db4daa11cc86d81ccae83',
        'imported.net.xml': '9f3aa4cd76fa51511d4f5d6f45dba2961924f60a529a3918c0a3d3237603cb16'}
    if any(digest(source / name) != signature for name, signature in expected.items()):
        raise ValueError('Areosa recipe requires the reviewed V9 control and compatible frozen import')
    destination.mkdir(parents=True, exist_ok=False)
    root = ET.parse(source / 'imported.net.xml').getroot()
    roads = {e.get('id'):e for e in root.findall('edge') if not e.get('function')}
    pins = ET.parse(source / 'signal-corrections.con.xml')
    for connection in list(pins.getroot()):
        if roads[connection.get('from')].get('to') in JOIN:
            pins.getroot().remove(connection)
    pins.write(destination / 'connections.con.xml', encoding='utf-8', xml_declaration=True)
    nodes = ET.Element('nodes')
    ET.SubElement(nodes, 'join', nodes=' '.join(sorted(JOIN)), id='areosa_compound', type='traffic_light')
    ET.ElementTree(nodes).write(destination / 'join.nod.xml', encoding='utf-8', xml_declaration=True)
    command = [str(Path(sumo.SUMO_HOME) / 'bin/netconvert'), '--sumo-net-file', str(source / 'imported.net.xml'),
        '--connection-files', str(destination / 'connections.con.xml'), '--node-files', str(destination / 'join.nod.xml'),
        '--tls.allred.time', '2', '--tls.yellow.time', '3', '--tls.default-type', 'actuated',
        '--output-file', str(destination / 'converted.net.xml')]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    (destination / 'build.log').write_text(completed.stdout + completed.stderr)
    completed.check_returncode()
    network = ET.parse(destination / 'converted.net.xml')
    cap_urban_speed(network)
    network.write(destination / 'baseline.net.xml', encoding='utf-8', xml_declaration=True)
    scope = audit_scope(source / 'baseline.net.xml', destination / 'baseline.net.xml',
        nodes=JOIN | FRINGE | {'areosa_compound'}, controllers=CONTROLLERS,
        removed_roads={'1165499581#3', '1304910030'})
    write_json(destination / 'scope.json', scope)
    report = {'schema':'invicta.areosa-rebuild.v1', 'source_hashes':{
        name:digest(source / name) for name in [*expected, 'signal-corrections.con.xml']},
        'network_sha256':digest(destination / 'baseline.net.xml'), 'command':command,
        'join_nodes':sorted(JOIN), 'reviewed_fringe_nodes':sorted(FRINGE),
        'scope_sha256':digest(destination / 'scope.json'), 'scope_passes':scope['passes'],
        'implementation_sha256':digest(__file__), 'field_validated':False, 'qualified':False}
    write_json(destination / 'rebuild.json', report)
    if not scope['passes']:
        raise ValueError('Areosa native rebuild exceeded its reviewed scope; retain the rejected output')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(rebuild(args.source, args.output), indent=2))
