"""Pure timetable evaluation shared by native execution and investigation."""

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

