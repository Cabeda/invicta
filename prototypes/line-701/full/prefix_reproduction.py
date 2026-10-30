"""Bounded, source-preserving native reproduction; never a full-day qualification."""
import json
from pathlib import Path
import math
import time
import xml.etree.ElementTree as ET

import sumo

from native_runner import freeze_implementation, run_native, atomic_json, require_native_version
from timetable import assess_trial
from trial_evidence import load_trial, sha256
from run_diagnostics import explain


def set_option(command, name, value):
    if name in command:
        command[command.index(name) + 1] = str(value)
    else:
        command.extend([name, str(value)])


def reproduce_prefix(source, output, trial_id=None, model=None, trip_id=None, stop_id=None, bus_sigma=None, probe=None,
                     until_blockage=False, wall_budget_seconds=None):
    started = time.monotonic()
    evidence = load_trial(source, trial_id, model)
    if stop_id is not None and trip_id is None:
        raise ValueError('Selecting a checkpoint also requires its target trip')
    diagnosis = explain(evidence, trip_id)
    if until_blockage:
        if probe is not None or bus_sigma is not None or trip_id is not None or stop_id is not None:
            raise ValueError('Original-input blockage replay cannot change assumptions or select a timetable target')
        trip_id, stop_id = evidence.buses[0]['id'], evidence.buses[0]['stops'][-1]['native_stop_id']
    if trip_id is None or stop_id is None:
        first = diagnosis['first_failure']
        if first is None:
            raise ValueError('A passing run requires an explicit target trip and checkpoint')
        trip_id, stop_id = first['trip'], first['stop']
    trip = next((trip for trip in evidence.buses if trip['id'] == trip_id), None)
    if trip is None:
        raise ValueError('Target trip is absent from its frozen reference')
    targets = [(index, stop) for index, stop in enumerate(trip['stops']) if stop['native_stop_id'] == stop_id]
    if len(targets) != 1:
        raise ValueError('Select one checkpoint in the target trip')
    index, target = targets[0]
    if index not in [0, len(trip['stops']) - 1] and not target['designated_timing_point']:
        raise ValueError('Reproduction target must be a designated timetable checkpoint')
    command = list(evidence.result['command'])
    begin = float(command[command.index('--begin') + 1])
    end = (min(float(command[command.index('--end') + 1]), begin + 43200) if until_blockage
           else target['scheduled'] + 120)
    if not until_blockage and not 0 < end - begin <= 3600:
        raise ValueError('Target exceeds the one-hour prefix budget; inspect the saved state instead')
    if bus_sigma is not None and not 0 <= bus_sigma <= 1:
        raise ValueError('Dawdling sensitivity must be between zero and one')
    if probe not in [None, 'omit_empty_request_stops', 'in_lane_checkpoints']:
        raise ValueError('Unknown native stop-semantics probe')
    if probe is not None and bus_sigma is not None:
        raise ValueError('Change one diagnostic variable at a time')
    ceiling = 180 if until_blockage else 120
    wall_budget = ceiling if wall_budget_seconds is None else wall_budget_seconds
    if not math.isfinite(wall_budget) or not 0 < wall_budget <= ceiling:
        raise ValueError(f'Native wall budget must be positive and at most {ceiling} seconds')
    raw = {name: evidence.payload(name) for name in ['network.net.xml', 'routes.rou.xml', 'additional.add.xml']}
    if probe is not None:
        xml = ET.fromstring(raw['routes.rou.xml'])
        if (evidence.result['config'].get('traffic') != 'none' or xml.findall('person') or
                any(vehicle.get('type') != 'bus' for vehicle in xml.findall('vehicle'))):
            raise ValueError('Stop-semantics probes require an empty, passenger-free diagnostic')
    require_native_version(evidence)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    try:
        for name, payload in raw.items():
            (output / name).write_bytes(payload)
        (output / 'reference.json').write_bytes(evidence.reference_bytes)
        changed, sensitivity = [], None
        if bus_sigma is not None:
            xml = ET.parse(output / 'routes.rou.xml')
            buses = [element for element in xml.getroot().findall('vType') if element.get('vClass') == 'bus']
            if len(buses) != 1:
                raise ValueError('A dawdling sensitivity requires one explicit native bus type')
            before = float(buses[0].get('sigma', '.5'))
            buses[0].set('sigma', str(bus_sigma))
            xml.write(output / 'routes.rou.xml', encoding='utf-8', xml_declaration=True)
            changed.append('routes.rou.xml')
            sensitivity = {'parameter': 'bus.sigma', 'before': before, 'after': bus_sigma,
                           'role': 'uncertain_assumption', 'physical_intervention': False}
        if probe is not None:
            xml = ET.parse(output / 'routes.rou.xml')
            vehicle = next(row for row in xml.getroot().findall('vehicle') if row.get('id') == trip_id)
            affected = []
            prefix_stops = {stop['native_stop_id'] for stop in trip['stops'][:index + 1]}
            for stop in list(vehicle.findall('stop')):
                if stop.get('busStop') not in prefix_stops:
                    continue
                if probe == 'omit_empty_request_stops' and stop.get('onDemand') == 'true':
                    affected.append(stop.get('busStop'))
                    vehicle.remove(stop)
                elif probe == 'in_lane_checkpoints' and stop.get('parking') == 'true':
                    affected.append(stop.get('busStop'))
                    stop.set('parking', 'false')
            if not affected:
                raise ValueError('The selected semantics probe affects no stops')
            xml.write(output / 'routes.rou.xml', encoding='utf-8', xml_declaration=True)
            changed.append('routes.rou.xml')
            sensitivity = {'parameter': probe, 'role': 'model_semantics', 'physical_intervention': False,
                           'focus_trip': trip_id, 'affected_stops': affected,
                           'parent_role': evidence.result.get('role', 'full_service_execution')}
        implementations = freeze_implementation(output)
        input_hashes = {name: sha256((output / name).read_bytes()) for name in list(raw) + ['reference.json']}
        input_hashes.update(implementations)
        command[0] = str(Path(sumo.SUMO_HOME) / 'bin/sumo')
        for flag, name in [('--net-file', 'network.net.xml'), ('--route-files', 'routes.rou.xml'),
                           ('--additional-files', 'additional.add.xml'), ('--tripinfo-output', 'trips.xml'),
                           ('--stop-output', 'stops.xml'), ('--collision-output', 'collisions.xml'),
                           ('--save-state.files', 'final-state.xml')]:
            set_option(command, flag, output / name)
        set_option(command, '--end', end)
        set_option(command, '--save-state.times', end - 1)
        set_option(command, '--save-state.rng', 'true')
        set_option(command, '--save-state.transportables', 'true')
        preparation_seconds = time.monotonic() - started
        options = ({'early_green': evidence.result['config'].get('early_green', False),
                    'shorten_served_pedestrian_green': evidence.result['config'].get('shorten_served_pedestrian_green', False)}
                   if evidence.result['config'].get('signal_priority') else None)
        execution = run_native(command, evidence.buses, output, options,
                               {'sample_seconds': 60 if until_blockage else 1,
                                'focus_trip': None if until_blockage else trip_id,
                                'max_wall_seconds': wall_budget,
                                'stop_on_first_blockage': until_blockage})
        end = execution['diagnostics']['simulation_time']
        evaluation_started = time.monotonic()
        calls = [dict(row.attrib) for row in ET.parse(output / 'stops.xml').getroot()]
        original = {(row['id'], row['busStop']): row for row in evidence.calls() if 0 <= float(row['ended']) < end}
        actual = {(row['id'], row['busStop']): row for row in calls if 0 <= float(row['ended']) < end}
        differences = [list(key) for key in sorted(set(original) | set(actual)) if original.get(key) != actual.get(key)]
        completed = {row.get('id') for row in ET.parse(output / 'trips.xml').getroot()
                     if row.tag == 'tripinfo' and float(row.get('arrival', -1)) >= 0}
        metrics = assess_trial(evidence.buses, calls, completed & {bus['id'] for bus in evidence.buses})
        call = next((row for row in calls if (row['id'], row['busStop']) == (trip_id, stop_id)), None)
        target_passes = call is not None and not any(f['trip'] == trip_id and f['stop'] == stop_id for f in metrics['failures'])
        for name, expected in input_hashes.items():
            if sha256((output / name).read_bytes()) != expected:
                raise ValueError('Reproduction input changed during execution')
        names = ['stops.xml', 'trips.xml', 'collisions.xml', 'priority-events.json', 'final-state.xml',
                 'monitor.json', 'trace.jsonl', 'progress.json'] + [s['file'] for s in execution['diagnostics']['snapshots']]
        output_hashes = {name: sha256((output / name).read_bytes()) for name in names if (output / name).exists()}
        result = {'schema': 'invicta.prefix-reproduction.v1',
            'role': ('original_input_blockage_reproduction' if until_blockage else
                     'model_semantics_sensitivity' if probe else
                     'uncertain_assumption_sensitivity' if sensitivity else 'recorded_prefix_reproduction'),
            'config': {**evidence.result['config'], 'id': output.name},
            'network_model': evidence.result['network_model'],
            'reference_sha256': evidence.identity['reference_sha256'],
            'parent': evidence.verified_identity(), 'command': command, 'input_hashes': input_hashes,
            'output_hashes': output_hashes, 'runtime': execution['runtime'],
            'execution_scope': {'kind': 'diagnostic_onset' if until_blockage else 'diagnostic_prefix', 'begin': begin, 'end': end,
                                'full_service_day': False, 'all_input_entities_preserved': True},
            'target': execution['diagnostics']['first_prolonged_wait'] if until_blockage else
                      {'trip': trip_id, 'stop': stop_id, 'scheduled': target['scheduled'],
                       'event': 'arrival' if index == len(trip['stops']) - 1 else 'departure',
                       'call': call, 'passes': target_passes},
            'changed_inputs': changed, 'sensitivity': sensitivity,
            'prefix_equivalence': {'matched': not differences if sensitivity is None and original else None,
                                   'basis': 'Complete native bus calls before the prefix end; no trajectory equivalence claimed.',
                                   'compared_calls': len(original), 'differences': differences[:10]},
            'metrics': metrics, 'diagnostics': execution['diagnostics'],
            'native_wall_budget_seconds': wall_budget,
            'phase_timings': {'input_preparation_seconds': preparation_seconds,
                              'native_execution_seconds': execution['elapsed_seconds'],
                              'evaluation_seconds': time.monotonic() - evaluation_started},
            'full_service_compliance': False, 'field_validated': False, 'qualified': False,
            'limitations': ['A prefix is diagnostic evidence, not a complete-service qualification.',
                           'Dawdling is an uncertain vehicle-behaviour assumption, not a proposed street change.',
                           'Empty stop-semantics probes cannot establish feasible passenger service or stop layout.']}
        atomic_json(output / 'reproduction.json', result)
        return result
    except Exception as error:
        atomic_json(output / 'error.json', {'status': 'failed', 'reason': str(error)})
        raise
