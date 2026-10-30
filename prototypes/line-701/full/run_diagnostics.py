"""Explain recorded timetable failures without rerunning vehicle physics."""
from timetable import assess_trial
from trial_evidence import load_trial


def execution_coverage(evidence):
    command = evidence.result.get('command', [])
    begin = float(command[command.index('--begin') + 1]) if '--begin' in command else None
    end = float(command[command.index('--end') + 1]) if '--end' in command else None
    buses = evidence.buses
    explicit = evidence.result.get('execution_scope', {}).get('kind', 'full_service_day')
    if explicit != 'full_service_day':
        begin = evidence.result.get('execution_scope', {}).get('begin', begin)
        end = evidence.result.get('execution_scope', {}).get('end', end)
    full = (explicit == 'full_service_day' and begin is not None and end is not None
            and begin <= min(bus['depart'] for bus in buses) - 30
            and end >= max(stop['scheduled'] for bus in buses for stop in bus['stops']))
    return {'kind': explicit, 'begin': begin, 'end': end, 'full_service_day': full}


def explain(evidence, trip_id=None):
    scheduled, calls = evidence.buses, evidence.calls()
    completed = evidence.completed()
    metrics = assess_trial(scheduled, calls, completed)
    indexed = {(call['id'], call['busStop']): call for call in calls}
    trips = {trip['id']: trip for trip in scheduled}
    if trip_id is not None and trip_id not in trips:
        raise ValueError('Trip is absent from the frozen reference')
    coverage = execution_coverage(evidence)
    failures = sorted((failure for failure in metrics['failures']
                       if (trip_id is None or failure['trip'] == trip_id)
                       and (coverage['end'] is None or failure['scheduled'] < coverage['end'])),
                      key=lambda failure: (failure['scheduled'], failure['trip'], failure['stop']))
    first = None
    if failures:
        first = {**failures[0], 'cause': 'unclassified', 'interval': None, 'trace_observation': None}
        if evidence.available('monitor.json'):
            import json
            monitor = json.loads(evidence.payload('monitor.json'))
            observed = monitor.get('first_deadline_pending')
            if observed and (observed['trip'], observed['stop']) == (first['trip'], first['stop']):
                first['trace_observation'] = observed
        trip = trips[first['trip']]
        stop_index = next(i for i, stop in enumerate(trip['stops']) if stop['native_stop_id'] == first['stop'])
        previous = [stop for i, stop in enumerate(trip['stops'][:stop_index])
                    if i == 0 or stop['designated_timing_point']]
        if previous:
            start, end = previous[-1], trip['stops'][stop_index]
            call = indexed.get((trip['id'], start['native_stop_id']), {})
            departure = float(call.get('ended', -1))
            observed_end = first['arrival'] if stop_index == len(trip['stops']) - 1 else first['departure']
            budget = end['scheduled'] - start['scheduled']
            observed = observed_end - departure if observed_end is not None and departure >= 0 else None
            first['interval'] = {'from_stop': start['native_stop_id'], 'to_stop': end['native_stop_id'],
                'scheduled_seconds': budget, 'observed_seconds': observed,
                'inherited_delay_seconds': max(0, departure - start['scheduled']) if departure >= 0 else None,
                'added_delay_seconds': observed - budget if observed is not None else None}
    unfinished = [trip['id'] for trip in scheduled if trip['id'] not in completed]
    return {'schema': 'invicta.run-diagnosis.v1', 'source': evidence.verified_identity(),
        'coverage': {'scheduled_trips': len(scheduled), 'timing_checks': metrics['checkpoints'],
                     'directions': sorted(evidence.reference['directions']), **coverage},
        'metrics': {key: value for key, value in metrics.items() if key != 'failures'},
        'simulation_compliance': metrics['passes'] and coverage['full_service_day'], 'field_validated': False,
        'first_failure': first, 'unfinished_trips': unfinished,
        'next_step': ('Inspect the first failed interval and its native trace before changing a traffic package.'
                      if first else 'Verify the declared traffic/seed matrix and passenger/access constraints.'),
        'limitations': ['Recorded stop calls establish timing, not the physical cause of a delay.',
                       'Unclassified failures require a native trace or targeted reproduction.',
                       'Simulation compliance does not establish field validation.']}


def diagnose_trial(source, trial_id=None, model=None, trip_id=None):
    return explain(load_trial(source, trial_id, model), trip_id)
