"""Pure timetable evaluation shared by native execution and investigation."""


def observation_window(scheduled, metrics, completed, cutoff):
    """Describe what was due by an exclusive cutoff without truncating trip semantics."""
    checks = [stop for trip in scheduled for index, stop in enumerate(trip['stops'])
              if index in [0, len(trip['stops']) - 1] or stop['designated_timing_point']]
    due = sum(stop['scheduled'] < cutoff for stop in checks)
    failures = [failure for failure in metrics['failures'] if failure['scheduled'] < cutoff]
    early_future = [failure for failure in metrics['failures'] if failure['early']
                    and failure['scheduled'] >= cutoff and failure['departure'] < cutoff]
    return {'cutoff_exclusive': cutoff, 'planned_trips': len(scheduled), 'reference_checks': len(checks),
            'due_checks': due, 'future_checks': len(checks) - due,
            'missing_due_checks': sum(failure['missing'] for failure in failures),
            'late_observed_checks': sum(failure['late'] for failure in failures),
            'early_observed_checks': sum(failure['early'] for failure in failures) + len(early_future),
            'on_time_due_checks': due - len(failures), 'completed_observed_trips': len(completed),
            'unfinished_due_trip_ids': [trip['id'] for trip in scheduled
                                        if trip['stops'][-1]['scheduled'] < cutoff and trip['id'] not in completed],
            'active_reference_trip_ids': [trip['id'] for trip in scheduled if trip['stops'][0]['scheduled'] < cutoff
                                           <= trip['stops'][-1]['scheduled'] and trip['id'] not in completed],
            'future_trip_ids': [trip['id'] for trip in scheduled if trip['stops'][0]['scheduled'] >= cutoff]}

def assess_trial(scheduled, calls, completed):
    """Strict zero-tolerance timetable test, including missing scheduled trips."""
    indexed = {(c['id'], c['busStop']): c for c in calls}
    if len(indexed) != len(calls):
        raise ValueError('Duplicate native stop calls')
    failures = []
    result = dict(planned=len(scheduled), completed=len(completed), on_time_starts=0,
                  on_time_finishes=0, checkpoints=0, missing_checkpoints=0,
                  late_checkpoints=0, early_departures=0, passes=True)
    for trip in scheduled:
        for index, stop in enumerate(trip['stops']):
            if index not in [0, len(trip['stops']) - 1] and not stop['designated_timing_point']:
                continue
            result['checkpoints'] += 1
            call = indexed.get((trip['id'], stop['native_stop_id']), {})
            arrival, departure = float(call.get('started', -1)), float(call.get('ended', -1))
            terminal = index == len(trip['stops']) - 1
            missing = arrival < 0 or (not terminal and departure < 0)
            late = not missing and (arrival if terminal else departure) > stop['scheduled']
            early = not missing and not terminal and departure < stop['scheduled']
            result['missing_checkpoints'] += missing
            result['late_checkpoints'] += late
            result['early_departures'] += early
            okay = not (missing or late or early)
            if index == 0:
                result['on_time_starts'] += okay
            if terminal:
                result['on_time_finishes'] += okay
            if not okay:
                failures.append({'trip': trip['id'], 'stop': stop['native_stop_id'],
                    'scheduled': stop['scheduled'], 'arrival': arrival if arrival >= 0 else None,
                    'departure': departure if departure >= 0 else None,
                    'missing': missing, 'late': late, 'early': early})
    result['passes'] = bool(scheduled) and not failures and result['completed'] == result['planned']
    result['failures'] = failures
    return result

