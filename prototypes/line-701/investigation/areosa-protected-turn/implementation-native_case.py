"""Fast, immutable native reproductions with their own one-second visual trace."""
import gzip
import json
import math
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import libsumo as native
import sumo
from prepare import digest
from native_input_cache import intern_network


def run_case(network, routes, output, *, additional=None, end_seconds=900, wall_seconds=30):
    if (not isinstance(end_seconds, int) or isinstance(end_seconds, bool) or not 1 <= end_seconds <= 3600
            or isinstance(wall_seconds, bool) or not isinstance(wall_seconds, (int, float))
            or not math.isfinite(wall_seconds) or not 0 < wall_seconds <= 120):
        raise ValueError('Local cases require 1–3600 simulated seconds and at most 120 native wall seconds')
    source = ET.parse(routes).getroot()
    actors = [row.get('id') for row in source.findall('vehicle')]
    if (not 1 <= len(actors) <= 100 or not all(actors) or len(set(actors)) != len(actors)
            or source.findall('flow') or source.findall('trip') or source.findall('person')):
        raise ValueError('A vehicle reproducer must explicitly request 1–100 unique actors; no implicit demand')
    departures = [float(row.get('depart')) for row in source.findall('vehicle')]
    if any(not math.isfinite(t) or t < 0 for t in departures) or departures != sorted(departures):
        raise ValueError('Local actors must have finite nonnegative times sorted by departure')
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=False)
    inputs = {}
    for name, path in [('network.net.xml', network), ('routes.rou.xml', routes),
                       ('additional.add.xml', additional)]:
        if path is not None:
            (folder / name).write_bytes(Path(path).read_bytes())
            inputs[name] = digest(folder / name)
    (folder / 'implementation-native_case.py').write_bytes(Path(__file__).read_bytes())
    inputs['implementation-native_case.py'] = digest(folder / 'implementation-native_case.py')
    intern_network(folder / 'network.net.xml')
    command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(folder / 'network.net.xml'),
        '--route-files', str(folder / 'routes.rou.xml'), '--begin', '0', '--end', str(end_seconds),
        '--seed', '17', '--time-to-teleport', '-1', '--no-warnings', 'true', '--no-step-log', 'true',
        '--collision.check-junctions', 'true', '--collision.action', 'warn',
        '--collision-output', str(folder / 'collisions.xml'),
        '--duration-log.disable', 'true', '--xml-validation', 'never']
    if additional is not None:
        command += ['--additional-files', str(folder / 'additional.add.xml')]
    started = time.monotonic()
    departed, arrived, frames = set(), set(), []
    loaded = False
    try:
        native.start(command)
        loaded = True
        signals = native.trafficlight.getIDList()
        actor_types = {}
        stop_reason = 'simulation_window'
        while native.simulation.getTime() < end_seconds and native.simulation.getMinExpectedNumber():
            if time.monotonic() - started > wall_seconds:
                stop_reason = 'native_wall_budget'
                break
            native.simulationStep()
            departed.update(native.simulation.getDepartedIDList())
            arrived.update(native.simulation.getArrivedIDList())
            frame = []
            for ident in native.vehicle.getIDList():
                point = native.vehicle.getPosition(ident)
                frame.append([ident, *point, native.vehicle.getAngle(ident), native.vehicle.getSpeed(ident),
                              native.vehicle.getWaitingTime(ident), native.vehicle.getLaneID(ident)])
                if ident not in actor_types:
                    actor_types[ident] = {'class': native.vehicle.getVehicleClass(ident),
                        'length': native.vehicle.getLength(ident), 'width': native.vehicle.getWidth(ident),
                        'height': native.vehicle.getHeight(ident)}
            frames.append({'time': native.simulation.getTime(), 'vehicles': frame,
                           'signals': {tls: native.trafficlight.getRedYellowGreenState(tls) for tls in signals}})
        unfinished = [{'id': ident, 'lane': native.vehicle.getLaneID(ident),
                       'wait': native.vehicle.getWaitingTime(ident), 'point': list(native.vehicle.getPosition(ident))}
                      for ident in native.vehicle.getIDList()]
        end = native.simulation.getTime()
        version = list(native.getVersion())
    except Exception as error:
        (folder / 'error.json').write_text(json.dumps({'status': 'failed', 'reason': str(error),
            'requested_actors': actors, 'input_hashes': inputs, 'command': command,
            'qualified': False}, indent=2) + '\n')
        raise
    finally:
        if loaded:
            native.close()
    if any(digest(folder / name) != value for name, value in inputs.items()):
        raise ValueError('Native case inputs changed during execution')
    if not departed.issubset(actors) or not arrived.issubset(actors):
        raise ValueError('Native case inserted an unrequested actor')
    trace = {'role': 'local_native_reproduction', 'sampling_seconds': 1, 'types': actor_types, 'frames': frames}
    (folder / 'frames.json.gz').write_bytes(gzip.compress(json.dumps(trace, separators=(',', ':')).encode(), mtime=0))
    report = {'schema': 'invicta.native-case.v1', 'role': 'local_reproduction_not_service_qualification',
        'requested_actors': actors, 'departed': sorted(departed), 'arrived': sorted(arrived), 'unfinished': unfinished,
        'undeparted': sorted(set(actors) - departed), 'uncompleted': sorted(set(actors) - arrived),
        'all_requested_completed': set(actors) == arrived, 'simulation_end': end, 'stop_reason': stop_reason,
        'collision_records': len(ET.parse(folder / 'collisions.xml').getroot()),
        'input_hashes': inputs, 'output_hashes': {name: digest(folder / name) for name in ['collisions.xml', 'frames.json.gz']},
        'native_version': version, 'command': command, 'wall_seconds': time.monotonic() - started,
        'qualified': False, 'field_validated': False}
    (folder / 'case.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report
