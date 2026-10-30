"""Paired, bounded mechanism probes from a snapshot; never service verification."""
import gzip
import json
import math
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import sumo

from native_runner import atomic_json, context, freeze_implementation, require_native_version
from trial_evidence import load_trial, sha256


def probe_snapshot(source, output, vehicle, *, trial_id=None, model=None, snapshot='final-state.xml', seconds=60,
                   connections=1, wall_budget_seconds=120):
    if not isinstance(seconds, int) or not 1 <= seconds <= 300:
        raise ValueError('State mechanism probes must be bounded to 1–300 simulated seconds')
    if not isinstance(connections, int) or not 1 <= connections <= 5:
        raise ValueError('State mechanism probes must be bounded to 1–5 route connections')
    if not math.isfinite(wall_budget_seconds) or not 0 < wall_budget_seconds <= 120:
        raise ValueError('State mechanism probes must be bounded to at most 120 native seconds per branch')
    evidence = load_trial(source, trial_id, model)
    require_native_version(evidence)
    names = ['network.net.xml', 'routes.rou.xml', 'additional.add.xml', snapshot]
    raw = {name: evidence.payload(name) for name in names}
    state = ET.fromstring(gzip.decompress(raw[snapshot]) if raw[snapshot].startswith(b'\x1f\x8b') else raw[snapshot])
    begin = float(state.get('time'))
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=False)
    try:
        for name, payload in raw.items():
            (folder / name).write_bytes(payload)
        implementation = freeze_implementation(folder)
        import libsumo as native
        runs, change = {}, None
        for variant in ['control', 'variant']:
            run = folder / variant
            run.mkdir()
            network = folder / ('variant.net.xml' if variant == 'variant' else 'network.net.xml')
            command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'),
                '--net-file', str(network), '--route-files', str(folder / 'routes.rou.xml'),
                '--additional-files', str(folder / 'additional.add.xml'), '--load-state', str(folder / snapshot),
                '--begin', str(begin), '--end', str(begin + seconds), '--seed', str(evidence.result['config'].get('seed', 17)),
                '--time-to-teleport', '-1', '--time-to-teleport.ride', '-1',
                '--no-warnings', 'true', '--no-step-log', 'true', '--duration-log.disable', 'true',
                '--xml-validation', 'never', '--collision-output', str(run / 'collisions.xml')]
            started = time.monotonic()
            native.start(command)
            try:
                if vehicle not in native.vehicle.getIDList():
                    raise ValueError('Probe vehicle is absent from the saved state')
                if native.simulation.getTime() != begin:
                    raise ValueError('Probe did not restore the recorded native time')
                start_distance = native.vehicle.getDistance(vehicle)
                before = context(native, vehicle)
                initial = sha256(json.dumps([(ident, native.vehicle.getLaneID(ident),
                    native.vehicle.getLanePosition(ident), native.vehicle.getSpeed(ident),
                    native.vehicle.getWaitingTime(ident), native.vehicle.getRoute(ident))
                    for ident in sorted(native.vehicle.getIDList())]).encode())
                rows = []
                stop_reason = 'simulation_window'
                if variant == 'control':
                    lane = native.vehicle.getLaneID(vehicle)
                    links = native.vehicle.getNextLinks(vehicle)
                    if lane.startswith(':') or not links:
                        raise ValueError('The mechanism probe requires a normal lane and its next route connection')
                    xml = ET.fromstring(raw['network.net.xml'])
                    affected = []
                    for link in links[:connections]:
                        target = link[0]
                        edge, index = lane.rsplit('_', 1)
                        to_edge, to_index = target.rsplit('_', 1)
                        matches = [connection for connection in xml.findall('connection')
                                   if (connection.get('from'), connection.get('fromLane'), connection.get('to'),
                                       connection.get('toLane')) == (edge, index, to_edge, to_index)]
                        if len(matches) != 1 or matches[0].get('keepClear', 'true') == 'false':
                            raise ValueError('Select currently enabled normal-lane keep-clear connections')
                        affected.append({'from': edge, 'from_lane': index, 'to': to_edge, 'to_lane': to_index,
                                         'before': matches[0].get('keepClear', 'true'), 'after': 'false'})
                        matches[0].set('keepClear', 'false')
                        lane = target
                    change = {'parameter': 'connection.keepClear', 'affected_connections': affected,
                              'requested_connections': connections, 'physical_intervention': False}
                    ET.ElementTree(xml).write(folder / 'variant.net.xml', encoding='utf-8', xml_declaration=True)
                for _ in range(seconds):
                    if time.monotonic() - started > wall_budget_seconds:
                        stop_reason = 'native_wall_budget'
                        break
                    native.simulationStep()
                    now = native.simulation.getTime()
                    if vehicle in native.vehicle.getIDList():
                        rows.append({'time': now, 'distance_metres': native.vehicle.getDistance(vehicle) - start_distance,
                                     'vehicles': context(native, vehicle)})
                    else:
                        rows.append({'time': now, 'vehicle_exited': True,
                                     'arrived': vehicle in native.simulation.getArrivedIDList()})
                        stop_reason = 'vehicle_exited'
                        break
                after = native.simulation.getTime()
            finally:
                native.close()
            atomic_json(run / 'trace.json', rows)
            collisions = len(ET.parse(run / 'collisions.xml').getroot())
            runs[variant] = {'command': command, 'before': before, 'begin': begin, 'end': after,
                             'initial_distance_metres': start_distance,
                             'initial_vehicle_state_sha256': initial,
                             'simulation_steps': len(rows), 'stop_reason': stop_reason,
                             'last': rows[-1] if rows else {'time': begin, 'distance_metres': 0, 'vehicles': before},
                             'collision_records': collisions,
                             'elapsed_seconds': time.monotonic() - started,
                             'trace_sha256': sha256((run / 'trace.json').read_bytes())}
        if any(sha256((folder / name).read_bytes()) != sha256(payload) for name, payload in raw.items()):
            raise ValueError('State probe input changed during execution')
        if runs['control']['initial_vehicle_state_sha256'] != runs['variant']['initial_vehicle_state_sha256']:
            raise ValueError('Paired probes restored different initial vehicle states')
        result = {'schema': 'invicta.state-probe.v1', 'role': 'snapshot_mechanism_probe',
                  'source': evidence.verified_identity(), 'snapshot': snapshot, 'vehicle': vehicle,
                  'changed_parameter': change, 'control': runs['control'], 'variant': runs['variant'],
                  'input_hashes': {name: sha256(payload) for name, payload in raw.items()},
                  'variant_network_sha256': sha256((folder / 'variant.net.xml').read_bytes()),
                  'native_wall_budget_seconds_per_branch': wall_budget_seconds,
                  'implementation_hashes': implementation, 'controller_state_restored': False,
                  'original_continuation_verified': False,
                  'full_service_compliance': False, 'field_validated': False, 'qualified': False,
                  'limitations': ['Only native signal state is loaded; Python controller memory is not resumed.',
                                 'Disabling keep-clear heuristics diagnoses a model mechanism; it is not a street proposal.',
                                 'Paired snapshot probes do not establish the initiating cause or full-run resume equivalence.']}
        atomic_json(folder / 'state-probe.json', result)
        return result
    except Exception as error:
        atomic_json(folder / 'error.json', {'status': 'failed', 'reason': str(error)})
        raise
