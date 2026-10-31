"""Build reusable problem cases from verified native runs before another trial.

The interface is line-independent; the native runner remains a separate adapter.
Recorded timing and waits describe symptoms, never automatic physical causes.
"""
import argparse
import collections
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from run_diagnostics import explain
from trial_evidence import load_trial, sha256


def _time(call, key):
    value = float(call.get(key, -1)) if call else -1
    return value if value >= 0 else None


def _stop(stop):
    return {key: stop[key] for key in ['native_stop_id', 'stop_name', 'scheduled', 'point'] if key in stop}


def workload_context(evidence):
    """Keep empty, passenger and traffic prerequisites as independent cases.

    Policy/controller settings and geometry identities may vary inside a
    comparison. The timetable, declared operating assumptions and physical
    demand catalogue must remain the same before a later result supersedes it.
    """
    config = evidence.result['config']
    settings = {key: config.get(key, default) for key, default in {
        'traffic':'none', 'seed':17, 'dwell':0, 'passengers_per_minute':0,
        'crossing_persons_per_minute':0, 'demand_fraction':1, 'request_stops':False,
        'holding_bays':False, 'boarding':1.8, 'capacity':70, 'bus_length':12,
        'operational_lateness_seconds':0, 'diagnostic_all_green':False}.items()}
    timetable = [(bus['id'], bus['direction'], [(stop['native_stop_id'], stop['scheduled'],
                 stop['designated_timing_point']) for stop in bus['stops']]) for bus in evidence.buses]
    routes = ET.fromstring(evidence.payload('routes.rou.xml'))
    people = [ET.tostring(person, encoding='unicode') for person in routes.findall('person')]
    workload = (sha256(evidence.payload('traffic-workload.json')) if evidence.available('traffic-workload.json')
                else evidence.verified_identity()['execution_sha256'])
    return sha256(json.dumps({'settings':settings, 'timetable':timetable, 'people':people,
                              'traffic_workload':workload}, sort_keys=True).encode())


def build_casebook(source, output, *, trial_id=None, model=None, line_id):
    evidence = load_trial(source, trial_id, model)
    diagnosis = explain(evidence, lateness_tolerance_seconds=60)
    calls = {(c['id'], c['busStop']): c for c in evidence.calls()}
    failures = {(f['trip'], f['stop']) for f in diagnosis['operational_metrics']['failures']}
    intervals = []
    for trip in evidence.buses:
        points = [i for i, stop in enumerate(trip['stops'])
                  if i in [0, len(trip['stops']) - 1] or stop['designated_timing_point']]
        for begin, end in zip(points, points[1:]):
            start, finish = trip['stops'][begin], trip['stops'][end]
            departure = _time(calls.get((trip['id'], start['native_stop_id'])), 'ended')
            terminal = end == len(trip['stops']) - 1
            reached = _time(calls.get((trip['id'], finish['native_stop_id'])), 'started' if terminal else 'ended')
            budget = finish['scheduled'] - start['scheduled']
            elapsed = reached - departure if reached is not None and departure is not None else None
            stop_seconds, holding_windows, boarded, alighted, skipped = 0, 0, 0, 0, 0
            if elapsed is not None:
                for index in range(begin + 1, end + 1):
                    if terminal and index == end:
                        continue  # Destination arrival excludes its later unloading/holding.
                    stop = trip['stops'][index]
                    call = calls.get((trip['id'], stop['native_stop_id']))
                    if call and 'skippedOnDemand' in call.get('state', ''):
                        skipped += 1
                        continue  # SUMO emits passage rows even without a stop.
                    arrived, left = _time(call, 'started'), _time(call, 'ended')
                    if arrived is None or left is None:
                        continue
                    stop_seconds += max(0, min(left, reached) - max(arrived, departure))
                    if index in points:
                        holding_windows += max(0, min(left, reached, stop['scheduled']) - max(arrived, departure))
                    boarded += int(call.get('loadedPersons', 0))
                    alighted += int(call.get('unloadedPersons', 0))
            intervals.append({'trip': trip['id'], 'direction': trip['direction'],
                'from_stop': _stop(start), 'to_stop': _stop(finish), 'terminal_arrival': terminal,
                'scheduled_seconds': budget, 'observed_seconds': elapsed,
                'native_begin': departure, 'native_end': reached,
                'inherited_delay_seconds': max(0, departure - start['scheduled']) if departure is not None else None,
                'added_delay_seconds': elapsed - budget if elapsed is not None else None,
                'end_deviation_seconds': reached - finish['scheduled'] if reached is not None else None,
                'recorded_stop_seconds': stop_seconds, 'scheduled_hold_window_seconds': holding_windows,
                'non_stop_seconds': elapsed - stop_seconds if elapsed is not None else None,
                'boarded_passengers': boarded, 'alighted_passengers': alighted,
                'skipped_request_stops':skipped,
                'operational_failure': (trip['id'], finish['native_stop_id']) in failures,
                'cause': 'unclassified'})
    intervals.sort(key=lambda row: (not row['operational_failure'],
        -(row['added_delay_seconds'] if row['added_delay_seconds'] is not None else float('inf')),
        row['trip'], row['to_stop']['native_stop_id']))
    watched = collections.defaultdict(list)
    for row in intervals:
        row['trace_observations'] = []
        if row['operational_failure'] and row['native_begin'] is not None and row['native_end'] is not None:
            watched[row['trip']].append(row)
    if evidence.available('trace.jsonl'):
        for line in evidence.payload('trace.jsonl').decode().splitlines():
            event = json.loads(line)
            vehicle = event.get('vehicle', {})
            if vehicle.get('waiting_seconds', 0) < 10 or vehicle.get('stop_state', 0):
                continue
            for row in watched.get(vehicle.get('id'), []):
                if row['native_begin'] <= event['time'] <= row['native_end']:
                    row['trace_observations'].append({'trip': row['trip'], 'time': event['time'],
                        **{key: vehicle.get(key) for key in ['lane', 'position_metres', 'waiting_seconds',
                            'speed_mps', 'leader', 'next_signals', 'signals', 'passengers']},
                        'cause': 'unclassified'})
        for rows in watched.values():
            for row in rows:
                row['trace_observations'] = sorted(row['trace_observations'],
                    key=lambda sample: -sample['waiting_seconds'])[:32]
    buses = {bus['id'] for bus in evidence.buses}
    ordinary_stalls = []
    for vehicle in ET.fromstring(evidence.payload('trips.xml')):
        if (vehicle.tag == 'tripinfo' and vehicle.get('id') not in buses
                and float(vehicle.get('arrival', -1)) < 0
                and float(vehicle.get('depart', -1)) >= 0
                and float(vehicle.get('waitingTime', 0)) > 3600):
            ordinary_stalls.append({'actor': vehicle.get('id'),
                'recorded_waiting_seconds': float(vehicle.get('waitingTime')),
                'time_loss_seconds': float(vehicle.get('timeLoss', 0)),
                'cause': 'unclassified'})
    ordinary_stalls.sort(key=lambda row: -row['recorded_waiting_seconds'])
    collisions = ([dict(row.attrib) for row in ET.fromstring(evidence.payload('collisions.xml'))]
                  if evidence.available('collisions.xml') else [])
    if collisions:
        next_case = {'kind': 'native_collision', 'event': collisions[0], 'cause': 'unclassified',
            'next_action': 'Reject model promotion; reduce the recorded collision to a native actor/movement regression.'}
    elif ordinary_stalls:
        next_case = {'kind': 'ordinary_model_stall', **ordinary_stalls[0],
            'next_action': 'Inspect the hash-bound saved state, minimise the native blockage and retain an actor-removal control.'}
    elif watched:
        row = next(row for row in intervals if row['operational_failure'])
        next_case = {'kind': 'added_bus_delay', 'trip': row['trip'],
            'from_stop': row['from_stop'], 'to_stop': row['to_stop'], 'cause': 'unclassified',
            'next_action': 'Inspect this interval and its sampled waits; build a short native reproduction before a policy change.'}
    elif diagnosis['operational_metrics']['failures']:
        next_case = {'kind':'timetable_event', 'failure':diagnosis['operational_metrics']['failures'][0],
            'cause':'unclassified',
            'next_action':'Inspect the missing or origin timing event; do not substitute a later destination as its cause.'}
    else:
        next_case = {'kind': 'qualification_review', 'cause': 'unclassified',
            'next_action': 'Check remaining origin/missing events, coverage, demand, access and seed matrix before ranking proposals.'}
    report = {'schema': 'invicta.investigation-casebook.v1', 'line_id': str(line_id),
        'analysis_implementation_sha256': sha256(Path(__file__).read_bytes()),
        'workload_context_sha256':workload_context(evidence),
        'source': evidence.verified_identity(), 'coverage': diagnosis['coverage'],
        'acceptance_criteria': diagnosis['acceptance_criteria'], 'strict_metrics': diagnosis['metrics'],
        'operational_metrics': diagnosis['operational_metrics'], 'intervals': intervals,
        'ordinary_stalls': ordinary_stalls, 'collision_events': collisions, 'next_case': next_case,
        'qualified': False, 'field_validated': False,
        'limitations': ['Stop durations include boarding, alighting and scheduled holding; those can overlap.',
            'Skipped on-demand passage rows are excluded from recorded stop duration.',
            'Scheduled hold windows are not independently measured pure holding time.',
            'Non-stop elapsed time includes movement, signals and queues; it is not free-flow running time.',
            'A late timing point is not automatically the place where delay was created.',
            'Consecutive waiting samples overlap; do not add their counters as total delay.',
            'A prolonged unfinished ordinary request needs investigation; it does not prove a particular junction defect.',
            'This casebook diagnoses one recorded execution; it cannot qualify a proposal.']}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'casebook.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    lines = [f'# Line {line_id}: bottleneck casebook', '',
        f"Source: {report['source']['trial']}. Field validated: false. Proposal qualified: false.", '',
        f"Operational late checks: {report['operational_metrics']['late_checkpoints']}; "
        f"missing: {report['operational_metrics']['missing_checkpoints']}.", '',
        f"Next case: {next_case['kind']}. {next_case['next_action']}", '',
        '| Trip | Interval | Inherited delay (s) | Added delay (s) | Stop time (s) |',
        '|---|---|---:|---:|---:|']
    for row in intervals:
        if row['operational_failure']:
            lines.append(f"| {row['trip']} | {row['from_stop']['stop_name']} → {row['to_stop']['stop_name']} | "
                f"{row['inherited_delay_seconds']} | {row['added_delay_seconds']} | {row['recorded_stop_seconds']} |")
    lines += ['', *report['limitations']]
    (output / 'README.md').write_text('\n'.join(lines) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--trial')
    parser.add_argument('--model', type=Path)
    parser.add_argument('--line', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build_casebook(args.source, args.output, trial_id=args.trial, model=args.model, line_id=args.line)
    print(json.dumps({'line': result['line_id'], 'intervals': len(result['intervals']),
                      'late_checks': result['operational_metrics']['late_checkpoints'],
                      'output': str(args.output)}, ensure_ascii=False))
