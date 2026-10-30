"""Reproducible native trials for the complete 701 timetable.

This is a new, explicitly uncalibrated study. No result replaces the published
native replay. Every failed working/checkpoint remains in the search ledger.
"""
from pathlib import Path
import argparse
import collections
import json
import random
import time
import xml.etree.ElementTree as ET

import sumo
import sumolib
from prepare import DATA, digest, write_json
from experiment import ALLOWED, CLASSES, BEGIN, demand, route
from priority_demand import migrate_requests
from timetable import assess_trial, acceptance_criteria
from model_audit import require_readiness, ModelNotReadyError
from native_runner import freeze_implementation, run_native
from scenario_audit import audit_scenario


class ExistingTrialError(FileExistsError):
    """An existing trial must never be overwritten, including a failed one."""


def make_inputs(model, folder, config):
    reference = json.loads((model / 'routes.json').read_text())
    net = sumolib.net.readNet(str(model / 'baseline.net.xml'), maxcache=0)
    baseline = net
    root = ET.parse(model / 'baseline.net.xml')
    changes = []
    if config.get('lanes'):
        # Use the access-screened v1 selection, then validate its OD connectivity
        # again on this network. No new access screen is inferred from v1.
        selected = {c['edge'] for c in json.loads((DATA / 'access-screen.json').read_text())['changes']}
        for edge in root.getroot().findall('edge'):
            if edge.get('id') not in selected:
                continue
            lanes = net.getEdge(edge.get('id')).getLanes()
            if any(l.allows('bus') and not l.allows('passenger') for l in lanes):
                continue
            lane = next((l for l in lanes if l.allows('bus') and l.allows('passenger')), None)
            if lane:
                element = next(l for l in edge.findall('lane') if l.get('id') == lane.getID())
                element.attrib.pop('disallow', None)
                element.set('allow', ' '.join(c for c in ALLOWED.split()
                    if c != 'pedestrian' or lane.allows('pedestrian')))
                changes.append({'edge': edge.get('id'), 'lane': lane.getID(), 'metres': lane.getLength()})
    root.write(folder / 'network.net.xml', encoding='utf-8', xml_declaration=True)
    net = sumolib.net.readNet(str(folder / 'network.net.xml'), maxcache=0)
    buses = [t for d in reference['directions'].values() for t in d['trips']]
    last = max(t['depart'] for t in buses)
    od = json.loads((DATA / 'od-pools.json').read_text())['pools']
    requests = [] if config['traffic'] == 'none' else demand(config['traffic'], config['seed'], od, last)
    requests, endpoint_mapping = migrate_requests(baseline, requests)
    write_json(folder / 'endpoint-mapping.json', endpoint_mapping)
    retained = set()
    for a, b, kind in dict.fromkeys((r['from'], r['to'], r['kind']) for r in requests):
        if route(net, a, b, kind)[0]:
            continue
        path, _ = route(baseline, a, b, kind)
        retained.update(path)
    if retained and changes:
        original = {l.get('id'): l.attrib for e in ET.parse(model / 'baseline.net.xml').getroot().findall('edge') for l in e.findall('lane')}
        for edge in root.getroot().findall('edge'):
            if edge.get('id') in retained:
                for lane in edge.findall('lane'):
                    ident = lane.get('id')
                    lane.attrib.clear(); lane.attrib.update(original[ident])
        changes = [c for c in changes if c['edge'] not in retained]
        root.write(folder / 'network.net.xml', encoding='utf-8', xml_declaration=True)
        net = sumolib.net.readNet(str(folder / 'network.net.xml'), maxcache=0)
    for a, b, kind in dict.fromkeys((r['from'], r['to'], r['kind']) for r in requests):
        if not route(net, a, b, kind)[0]:
            raise ValueError(f'Priority policy disconnects an OD request: {a} -> {b} ({kind})')
    routes, additional = ET.Element('routes'), ET.Element('additional')
    for group, kind in list(CLASSES.items()) + [('bus', 'bus')]:
        attributes = dict(id=group, vClass=kind, sigma='.5', speedFactor='1', speedDev='0')
        if group == 'bus':
            attributes.update(length=str(config.get('bus_length', 12)), accel='1.2', decel='4.5', maxSpeed=str(50 / 3.6),
                personCapacity=str(config.get('capacity', 70)), boardingDuration=str(config.get('boarding', 1.8)),
                loadingDuration='1')
        if group == 'bicycle':
            attributes['maxSpeed'] = '5.5'
        ET.SubElement(routes, 'vType', attributes)
    events, unroutable = [], []
    for request in requests:
        try:
            path, _ = route(net, request['from'], request['to'], request['kind'])
        except KeyError:
            path = None
        if not path:
            unroutable.append(request['id'])
            continue
        element = ET.Element('vehicle', id=request['id'], type=request['group'],
            depart=str(request['depart']), departLane='best', departSpeed='max',
            departPos=str(request['depart_pos']), arrivalPos=str(request['arrival_pos']))
        ET.SubElement(element, 'route', edges=' '.join(path))
        if config.get('rerouting'):
            ET.SubElement(element, 'param', key='has.rerouting.device', value='true')
        events.append(element)
    for direction in reference['directions'].values():
        for stop in direction['stops']:
            ET.SubElement(additional, 'busStop', id=stop['native_stop_id'], lane=stop['lane'],
                startPos=str(max(0, stop['pos'] - 15)), endPos=str(stop['pos']),
                friendlyPos='true', name=stop['stop_name'])
    shock = min((t for t in buses if t['direction'] == '1' and t['depart'] >= 17*3600),
                key=lambda t:t['depart'])['id'] if config['traffic'] == 'late' else None
    for bus in buses:
        first = bus['stops'][0]
        delay = 180 if bus['id'] == shock and not config.get('standby') else 0
        vehicle = ET.Element('vehicle', id=bus['id'], type='bus', line='701_' + bus['direction'],
            depart=str(bus['depart'] - 30 + delay), departLane=first['lane'].rsplit('_', 1)[1],
            departPos=str(max(0, first['pos'] - .1)), departSpeed='0')
        ET.SubElement(vehicle, 'route', edges=' '.join(bus['path']))
        for index, stop in enumerate(bus['stops']):
            timing = stop['designated_timing_point'] or index in [0, len(bus['stops']) - 1]
            attributes = dict(busStop=stop['native_stop_id'], duration=str(config['dwell']),
                              arrival=str(stop['scheduled']), extension='120')
            if timing:
                attributes['until'] = str(stop['scheduled'])
            elif config.get('request_stops'):
                attributes['onDemand'] = 'true'
            if timing and config.get('holding_bays'):
                attributes['parking'] = 'true'
            ET.SubElement(vehicle, 'stop', attributes)
        events.append(vehicle)
    # Synthetic passengers are identical across policies: native waiting, boarding,
    # alighting and finite capacity. OD requests are never deleted by optimisation.
    rng = random.Random(config['seed'] + 701)
    passengers = 0
    for direction in reference['directions'].values():
        for index, stop in enumerate(direction['stops'][:-1]):
            departures = [t['stops'][0]['scheduled'] if index == 0 else
                next((s['scheduled'] for s in t['stops'] if s['stop_id'] == stop['stop_id']), None)
                for t in direction['trips']]
            departures = [t for t in departures if t is not None]
            if not departures:
                continue
            current = max(BEGIN, min(departures) - 25)
            while config.get('passengers_per_minute', 0) > 0:
                current += rng.expovariate(config['passengers_per_minute'] / 60)
                if current > max(departures) - 60:
                    break
                destination = rng.choice(direction['stops'][index + 1:])
                # Short workings must not strand a passenger at a wrong terminus.
                eligible = [t['id'] for t in direction['trips']
                    if any(s['stop_id'] == stop['stop_id'] for s in t['stops'])
                    and any(s['stop_id'] == destination['stop_id'] for s in t['stops'])]
                person = ET.Element('person', id=f'passenger_{passengers}', depart=str(current),
                    departPos=str(max(0, stop['pos'] - 3)))
                ET.SubElement(person, 'ride', **{'from': stop['edge'], 'busStop': destination['native_stop_id'],
                    'lines': ' '.join(eligible)})
                events.append(person)
                passengers += 1
    # Exercise mapped crossings with explicit synthetic walking requests. Use
    # ordinary sidewalk edges on opposite sides; SUMO chooses the walking path.
    # These requests are not pedestrian counts and not all paths are guaranteed
    # to use the nearby crossing. Keep them separately identifiable in output.
    pedestrian_requests = 0
    pedestrian_pairs = []
    if config.get('crossing_persons_per_minute', 0) > 0:
        connections = root.getroot().findall('connection')
        incoming, outgoing = collections.defaultdict(list), collections.defaultdict(list)
        for connection in connections:
            incoming[connection.get('to')].append(connection.get('from'))
            outgoing[connection.get('from')].append(connection.get('to'))
        route_edges = {e for d in reference['directions'].values() for e in d['path']}
        for crossing in root.getroot().findall('edge'):
            if crossing.get('function') != 'crossing' or not route_edges.intersection(crossing.get('crossingEdges', '').split()):
                continue
            ident = crossing.get('id')
            before = [e for w in incoming[ident] for e in incoming[w] if not e.startswith(':')]
            after = [e for w in outgoing[ident] for e in outgoing[w] if not e.startswith(':')]
            if not before or not after:
                continue
            pedestrian_pairs.append({'crossing': ident, 'from': before[0], 'to': after[0]})
        rng = random.Random(config['seed'] + 1402)
        for pair in pedestrian_pairs:
            current = BEGIN
            while True:
                current += rng.expovariate(config['crossing_persons_per_minute'] / 60)
                if current > last:
                    break
                person = ET.Element('person', id=f'walking_{pedestrian_requests}',
                                    depart=str(current), departPos='-1')
                ET.SubElement(person, 'walk', **{'from': pair['from'], 'to': pair['to'], 'arrivalPos': '1'})
                events.append(person)
                pedestrian_requests += 1
    write_json(folder / 'crossing-requests.json', {'pairs': pedestrian_pairs, 'requests': pedestrian_requests})
    for element in sorted(events, key=lambda e: float(e.get('depart'))):
        routes.append(element)
    ET.ElementTree(routes).write(folder / 'routes.rou.xml', encoding='utf-8', xml_declaration=True)
    ET.ElementTree(additional).write(folder / 'additional.add.xml', encoding='utf-8', xml_declaration=True)
    audit = audit_scenario(folder, reference, requests, passengers, pedestrian_requests, baseline, net)
    write_json(folder / 'compiled-audit.json', audit)
    return reference, buses, requests, passengers, unroutable, changes, shock, pedestrian_requests


def run_trial(model, output, config):
    if config['traffic'] not in ['none', 'moderate', 'busy', 'late']:
        raise ValueError('Unknown requested traffic case')
    folder = output / config['id']
    if folder.resolve().parent != output.resolve():
        raise ValueError('Trial id must name one directory')
    if folder.exists():
        raise ExistingTrialError('Use a fresh trial id; every trial folder is immutable')
    readiness = require_readiness(model, config)
    try:
        folder.mkdir(parents=True)
    except FileExistsError as error:
        raise ExistingTrialError('A concurrent process already created this trial') from error
    try:
        return _execute_trial(model, folder, config, readiness)
    except Exception as error:
        write_json(folder / 'error.json', {'config': config, 'status': 'failed', 'reason': str(error)})
        raise


def _execute_trial(model, folder, config, readiness):
    started = time.monotonic()
    implementations = freeze_implementation(folder)
    (folder / 'reference.json').write_bytes((model / 'routes.json').read_bytes())
    (folder / 'model.json').write_bytes((model / 'model.json').read_bytes())
    source_hashes = {name: digest(model / name) for name in ['baseline.net.xml', 'routes.json', 'model.json']}
    if source_hashes['baseline.net.xml'] != json.loads((model / 'model.json').read_text())['network_sha256']:
        raise ValueError('Model network bytes changed')
    reference, buses, requests, passengers, unroutable, changes, shock, pedestrian_requests = make_inputs(model, folder, config)
    native_hashes = {name: digest(folder / name) for name in ['network.net.xml', 'routes.rou.xml', 'additional.add.xml', 'endpoint-mapping.json', 'crossing-requests.json', 'compiled-audit.json']}
    native_hashes.update(implementations)
    native_hashes['reference.json'] = digest(folder / 'reference.json')
    native_hashes['model.json'] = digest(folder / 'model.json')
    preparation_seconds = time.monotonic() - started
    end = max(s['scheduled'] for t in buses for s in t['stops']) + 7200
    command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(folder / 'network.net.xml'),
        '--route-files', str(folder / 'routes.rou.xml'), '--additional-files', str(folder / 'additional.add.xml'),
        '--begin', str(BEGIN), '--end', str(end), '--seed', str(config['seed']),
        '--tripinfo-output', str(folder / 'trips.xml'), '--tripinfo-output.write-unfinished', 'true',
        '--tripinfo-output.write-undeparted', 'true', '--stop-output', str(folder / 'stops.xml'),
        '--stop-output.write-unfinished', 'true', '--collision-output', str(folder / 'collisions.xml'),
        '--time-to-teleport', '-1', '--time-to-teleport.ride', '-1', '--no-step-log', 'true',
        '--collision.action', 'warn', '--collision.check-junctions', 'true',
        '--duration-log.disable', 'true', '--xml-validation', 'never', '--device.rerouting.period', '60',
        '--routing-algorithm', config.get('routing_algorithm', 'dijkstra'),
        '--save-state.times', str(end - 1), '--save-state.files', str(folder / 'final-state.xml'),
        '--save-state.rng', 'true', '--save-state.transportables', 'true']
    if config.get('diagnostic_all_green'):
        command += ['--tls.all-off', 'true']
    options = ({'early_green': config.get('early_green', False),
                'shorten_served_pedestrian_green': config.get('shorten_served_pedestrian_green', False)}
               if config.get('signal_priority') else None)
    execution = run_native(command, buses, folder, options)
    priority = execution['priority']
    evaluation_started = time.monotonic()
    trips = list(ET.parse(folder / 'trips.xml').getroot())
    completed = {t.get('id') for t in trips if t.tag == 'tripinfo' and float(t.get('arrival', -1)) >= 0}
    calls = [c.attrib for c in ET.parse(folder / 'stops.xml').getroot()]
    completed_buses = completed & {b['id'] for b in buses}
    metrics = assess_trial(buses, calls, completed_buses)
    criteria = acceptance_criteria(config.get('operational_lateness_seconds', 0))
    operational = assess_trial(buses, calls, completed_buses,
                                lateness_tolerance_seconds=criteria['lateness_tolerance_seconds'])
    person_results = [p for p in trips if p.tag == 'personinfo' and p.get('id').startswith('passenger_')]
    arrived_people = sum(len(p) > 0 and all(float(stage.get('arrival', -1)) >= 0
                         for stage in p) for p in person_results)
    served_vehicles = len(completed - {b['id'] for b in buses})
    collisions = len(list(ET.parse(folder / 'collisions.xml').getroot()))
    evaluation_seconds = time.monotonic() - evaluation_started
    verification_started = time.monotonic()
    if any(digest(model / name) != value for name, value in source_hashes.items()) or any(
            digest(folder / name) != value for name, value in native_hashes.items()):
        raise ValueError('Simulation inputs changed during execution')
    outputs = ['trips.xml', 'stops.xml', 'collisions.xml', 'priority-events.json', 'final-state.xml',
               'monitor.json', 'trace.jsonl', 'progress.json'] + [s['file'] for s in execution['diagnostics']['snapshots']]
    output_hashes = {name: digest(folder / name) for name in outputs if (folder / name).exists()}
    result = {'config': config, 'metrics': metrics, 'grading_schema': 2, 'native': True,
        'acceptance_criteria': criteria, 'operational_metrics': operational,
        'readiness': readiness,
        'scenario_audit': json.loads((folder / 'compiled-audit.json').read_text()),
        'diagnostics': execution['diagnostics'], 'runtime': execution['runtime'],
        'phase_timings': {'input_preparation_seconds': preparation_seconds,
                          'native_execution_seconds': execution['elapsed_seconds'],
                          'evaluation_seconds': evaluation_seconds,
                          'output_verification_seconds': time.monotonic() - verification_started},
        'network_model': json.loads((model / 'model.json').read_text())['network_sha256'],
        'input_hashes': native_hashes,
        'output_hashes': output_hashes,
        'demand_mapping_sha256': digest(folder / 'endpoint-mapping.json'),
        'reference_sha256': digest(model / 'routes.json'), 'command': command,
        'passenger_requests': passengers, 'arrived_passengers': arrived_people,
        'walking_requests': pedestrian_requests,
        'arrived_walkers': sum(p.tag == 'personinfo' and p.get('id').startswith('walking_')
                              and len(p) > 0 and all(float(stage.get('arrival', -1)) >= 0 for stage in p)
                              for p in trips),
        'vehicle_requests': len(requests), 'completed_ordinary_vehicles': served_vehicles,
        'unroutable_requests': len(unroutable), 'unserved_vehicle_requests': len(requests) - served_vehicles,
        'collision_records': collisions, 'lane_changes': changes, 'signal_priority': priority,
        'shock_vehicle': shock, 'standby_resources': 1 if shock and config.get('standby') else 0,
        'elapsed_seconds': round(time.monotonic() - started, 2),
        'qualified': False,
        'qualification_note': 'Exploratory model: pedestrian demand, stop positions, signal plans, passenger demand and vehicle blocks require validation.'}
    write_json(folder / 'result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k in ['config', 'elapsed_seconds', 'passenger_requests', 'arrived_passengers', 'vehicle_requests', 'unserved_vehicle_requests', 'collision_records']}, ensure_ascii=False), flush=True)
    print(json.dumps({k: v for k, v in metrics.items() if k != 'failures'}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    run_trial(args.model.resolve(), args.output.resolve(), config)
