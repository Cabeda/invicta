"""Resumable, line-scoped investigation steps with verified reuse and a journal."""
import argparse
import datetime as dt
import fcntl
import functools
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

from investigation_loop import build_casebook
from native_case import run_case
from native_runner import atomic_json
from trial_evidence import sha256
from case_view import export_case_view, NoRecordedPositions
from trial_evidence import load_trial


def _apply_profile(state, profile):
    state.setdefault('profiles', {})[profile['context']] = profile
    unresolved = [p for p in state['profiles'].values() if p.get('next_case')]
    priority = {'native_collision':0, 'ordinary_model_stall':1, 'added_bus_delay':2}
    if unresolved:
        selected = min(unresolved, key=lambda p:priority.get(p['next_case']['kind'], 3))
        state['next_case'] = {**selected['next_case'], 'source_trial':selected['trial'],
                              'workload_context_sha256':selected['context']}
    else:
        state['next_case'] = {'kind':'qualification_review', 'cause':'unclassified',
            'next_action':'Review access and the declared paired scenario/seed matrix; one passing case is insufficient.'}


def _load_session(workspace):
    state = json.loads((workspace / 'session.json').read_text())
    journal = workspace / 'events.jsonl'
    events = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    if [row['sequence'] for row in events] != list(range(1, len(events) + 1)):
        raise ValueError('Study journal has a missing or duplicate sequence; retain it for recovery')
    if state['events'] > len(events) or state['runs'] != events[:state['events']]:
        raise ValueError('Session state differs from its durable journal')
    if state['events'] < len(events):
        state.update(events=len(events), runs=events)
        for event in events:
            if event.get('profile'):
                _apply_profile(state, event['profile'])
        atomic_json(workspace / 'session.json', state)
    return state


def _serialized(operation):
    @functools.wraps(operation)
    def locked(workspace, *args, **kwargs):
        workspace = Path(workspace)
        with (workspace / 'session.lock').open('a') as stream:
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError('Another process is advancing this line session') from error
            _load_session(workspace)
            return operation(workspace, *args, **kwargs)
    return locked


def start_session(workspace, source, *, line_id, trial_id=None, deadline=None):
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=False)
    report = build_casebook(source, workspace / 'initial-casebook', trial_id=trial_id, line_id=line_id)
    state = {'schema': 'invicta.study-session.v1', 'line_id': str(line_id),
        'source': report['source'], 'deadline': deadline, 'runs': [], 'events': 0,
        'next_case': report['next_case'], 'qualified': False}
    _apply_profile(state, {'context':report['workload_context_sha256'], 'trial':report['source']['trial'],
        'next_case':report['next_case'] if report['next_case']['kind'] != 'qualification_review' else None})
    atomic_json(workspace / 'session.json', state)
    return state


def _verified_case(folder, expected_metadata):
    if sha256((folder / 'case.json').read_bytes()) != expected_metadata:
        raise ValueError('Cached native case metadata changed; do not reuse it')
    result = json.loads((folder / 'case.json').read_text())
    for name, signature in {**result['input_hashes'], **result['output_hashes']}.items():
        if Path(name).name != name or sha256((folder / name).read_bytes()) != signature:
            raise ValueError('Cached native case changed; do not reuse it')
    return result


def _append_event(workspace, state, event):
    with (workspace / 'events.jsonl').open('a') as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    state['events'] += 1
    state['runs'].append(event)
    atomic_json(workspace / 'session.json', state)


@_serialized
def run_local_step(workspace, proposal):
    workspace = Path(workspace)
    state = _load_session(workspace)
    if state.get('deadline'):
        deadline = dt.datetime.fromisoformat(state['deadline'].replace('Z', '+00:00'))
        if dt.datetime.now(dt.timezone.utc) >= deadline:
            raise TimeoutError('Study session budget ended; retain state and report its unresolved cases')
    hypothesis = proposal.get('hypothesis')
    if not isinstance(hypothesis, dict) or any(not isinstance(hypothesis.get(k), str) or not hypothesis[k].strip()
                                              for k in ['change', 'prediction', 'evidence']):
        raise ValueError('Each step requires a specific change, prediction and prior evidence')
    name = proposal['id']
    if not isinstance(name, str) or not name or Path(name).name != name or name in ['.', '..']:
        raise ValueError('An experiment id must name one local directory')
    inputs = {key: sha256(Path(proposal[key]).read_bytes()) for key in ['network', 'routes']}
    if proposal.get('additional'):
        inputs['additional'] = sha256(Path(proposal['additional']).read_bytes())
    inputs.update(end_seconds=proposal.get('end_seconds', 900), wall_seconds=proposal.get('wall_seconds', 30),
                  native_case_implementation=sha256(Path(__file__).with_name('native_case.py').read_bytes()))
    import libsumo
    inputs['native_version'] = list(libsumo.getVersion())
    signature = sha256(json.dumps(inputs, sort_keys=True).encode())
    cached = next((r for r in state['runs'] if r['signature'] == signature and r.get('status') != 'failed'
                   and r.get('stop_reason') != 'native_wall_budget'), None)
    if cached:
        result = _verified_case(workspace / cached['case'], cached['case_sha256'])
        case, reused = cached['case'], True
    else:
        case = 'cases/' + name
        try:
            result = run_case(proposal['network'], proposal['routes'], workspace / case,
                additional=proposal.get('additional'), end_seconds=inputs['end_seconds'], wall_seconds=inputs['wall_seconds'])
        except Exception as error:
            _append_event(workspace, state, {'sequence': state['events'] + 1, 'id': name,
                'signature': signature, 'case': case, 'status': 'failed', 'reason': str(error),
                'reused': False, 'hypothesis': hypothesis, 'qualified': False})
            raise
        reused = False
    view_error = None
    try:
        view = export_case_view(workspace / case, title=proposal.get('title', hypothesis['change']))
    except NoRecordedPositions:
        view = None
    except Exception as error:
        view, view_error = None, error
    event = {'sequence': state['events'] + 1, 'id': name, 'signature': signature, 'case': case,
             'case_sha256': sha256((workspace / case / 'case.json').read_bytes()),
             'view': case + '/index.html' if view else None,
             'view_case_sha256': view['source_case_sha256'] if view else None,
             'view_status':'failed' if view_error else 'recorded' if view else 'no_recorded_actor_positions',
             'status': 'recorded', 'reused': reused, 'hypothesis': hypothesis, 'stop_reason': result['stop_reason'],
             'requested': len(result['requested_actors']), 'completed': len(result['arrived']),
             'collisions': result['collision_records'], 'qualified': False,
             'native_wall_seconds':0 if reused else result['wall_seconds'],
             'local_case_clears': result['all_requested_completed'] and result['collision_records'] == 0}
    # Journal first. If interrupted before state promotion, the immutable case
    # and event remain available for explicit recovery rather than being lost.
    if view_error:
        event.update(status='view_failed', reason=str(view_error))
    _append_event(workspace, state, event)
    if view_error:
        raise view_error
    return event


@_serialized
def run_service_step(workspace, proposal):
    """Execute or reuse a complete native trial, then recalculate its gates.

    The prepared model/runner is an adapter. Triage and accounting do not depend
    on 701 stop names. A passing study case never promotes a complete proposal.
    """
    from priority_search import run_trial
    from prepare import DATA
    import libsumo
    workspace = Path(workspace)
    state = _load_session(workspace)
    name = proposal['id']
    if not isinstance(name, str) or not name or Path(name).name != name or name in ['.', '..']:
        raise ValueError('An experiment id must name one local directory')
    hypothesis = proposal.get('hypothesis')
    if not isinstance(hypothesis, dict) or any(not isinstance(hypothesis.get(k), str) or not hypothesis[k].strip()
                                              for k in ['change', 'prediction', 'evidence']):
        raise ValueError('Each step requires a specific change, prediction and prior evidence')
    config = {**proposal['config'], 'id': name, 'hypothesis': hypothesis}
    budget = config.setdefault('diagnostic_budget_seconds', 180)
    if state.get('deadline'):
        deadline = dt.datetime.fromisoformat(state['deadline'].replace('Z', '+00:00'))
        remaining = (deadline - dt.datetime.now(dt.timezone.utc)).total_seconds()
        if remaining < budget:
            raise TimeoutError('Insufficient session time for the declared native trial budget')
    model = Path(proposal['model'])
    # Include all prepared-model files, runner modules, and the regional demand
    # adapter's external pools. An unchanged configuration alone is insufficient.
    signatures = {'model/' + p.name: sha256(p.read_bytes()) for p in model.iterdir() if p.is_file()}
    from native_runner import implementation_sources
    signatures.update({'implementation/' + p.name: sha256(p.read_bytes())
                       for p in implementation_sources()})
    for filename in ['od-pools.json', 'access-screen.json']:
        signatures['demand/' + filename] = sha256((DATA / filename).read_bytes())
    review = config.get('readiness', {}).get('geometry_review')
    if review:
        signatures['geometry_review'] = sha256(Path(review).read_bytes())
    if config.get('paired_workload'):
        paired = load_trial(config['paired_workload'])
        signatures['paired_execution'] = paired.verified_identity()['execution_sha256']
        for filename in paired.result['input_hashes']:
            paired.payload(filename)
    signature_config = {k:v for k,v in config.items() if k not in ['id', 'hypothesis']}
    signature = sha256(json.dumps({'files': signatures, 'config': signature_config,
        'native_version': list(libsumo.getVersion())}, sort_keys=True).encode())
    cached = next((r for r in state['runs'] if r.get('kind') == 'service_trial'
                   and r['signature'] == signature and r['status'] == 'recorded'
                   and r.get('full_reference_day')), None)
    trial = cached['trial'] if cached else 'trials/' + name
    if cached:
        if sha256((workspace / trial / 'result.json').read_bytes()) != cached['result_sha256']:
            raise ValueError('Cached native trial metadata changed; do not reuse it')
    else:
        try:
            run_trial(model, workspace / 'trials', config)
        except Exception as error:
            _append_event(workspace, state, {'sequence': state['events'] + 1, 'id': name,
                'kind': 'service_trial', 'signature': signature, 'trial': trial,
                'status': 'failed', 'reason': str(error), 'reused': False,
                'hypothesis': hypothesis, 'qualified': False})
            raise
    evidence = load_trial(workspace / trial)
    for filename in {**evidence.result['input_hashes'], **evidence.result['output_hashes']}:
        evidence.payload(filename)
    from run_diagnostics import explain
    diagnosis = explain(evidence)
    routes = ET.fromstring(evidence.payload('routes.rou.xml'))
    requested_vehicles = {v.get('id') for v in routes.findall('vehicle')}
    requested_people = {v.get('id') for v in routes.findall('person')}
    raw_trips = ET.fromstring(evidence.payload('trips.xml'))
    complete_vehicles = {v.get('id') for v in raw_trips if v.tag == 'tripinfo' and float(v.get('arrival', -1)) >= 0}
    complete_people = {v.get('id') for v in raw_trips if v.tag == 'personinfo' and len(v)
                       and all(float(stage.get('arrival', -1)) >= 0 for stage in v)}
    collisions = len(ET.fromstring(evidence.payload('collisions.xml')))
    gates = {'full_reference_day': diagnosis['coverage']['full_service_day'],
        'operational_timetable': diagnosis['operational_metrics']['passes'],
        'all_vehicle_requests': requested_vehicles == complete_vehicles,
        'all_people_requests': requested_people == complete_people,
        'no_collisions': collisions == 0,
        'normal_signal_control': not config.get('diagnostic_all_green', False),
        'no_unroutable_requests': evidence.result.get('unroutable_requests') == 0}
    analysis = sha256(b''.join(Path(__file__).with_name(filename).read_bytes() for filename in
        ['investigation_loop.py', 'run_diagnostics.py', 'timetable.py', 'trial_evidence.py']))
    same_analysis = cached and cached.get('analysis_sha256') == analysis
    casebook = cached['casebook'] if same_analysis else 'casebooks/' + name + '-' + analysis[:12]
    if not same_analysis:
        book = build_casebook(workspace / trial, workspace / casebook, line_id=state['line_id'])
    else:
        if sha256((workspace / casebook / 'casebook.json').read_bytes()) != cached['casebook_sha256']:
            raise ValueError('Cached casebook changed; do not reuse its analysis')
        book = json.loads((workspace / casebook / 'casebook.json').read_text())
        if book['source']['execution_sha256'] != evidence.verified_identity()['execution_sha256']:
            raise ValueError('Cached casebook belongs to a different native execution')
    event = {'sequence': state['events'] + 1, 'id': name, 'kind': 'service_trial',
        'signature': signature, 'trial': trial, 'casebook': casebook, 'status': 'recorded',
        'result_sha256': evidence.verified_identity()['execution_sha256'], 'reused': bool(cached),
        'analysis_sha256':analysis, 'casebook_sha256':sha256((workspace / casebook / 'casebook.json').read_bytes()),
        'hypothesis': hypothesis, 'requested_vehicles': len(requested_vehicles),
        'completed_vehicles': len(complete_vehicles), 'requested_people': len(requested_people),
        'completed_people': len(complete_people), 'collisions': collisions,
        'full_reference_day': gates['full_reference_day'], 'gates': gates,
        'strict_metrics': diagnosis['metrics'], 'operational_metrics': diagnosis['operational_metrics'],
        'study_case_passes': all(gates.values()), 'qualified': False, 'next_case': book['next_case'],
        'native_wall_seconds':0 if cached else evidence.result.get('phase_timings', {}).get('native_execution_seconds', 0),
        'qualification_note': 'One study case; access review, paired scenario/seed matrix and field validation remain separate.'}
    event['profile'] = {'context':book['workload_context_sha256'], 'trial':book['source']['trial'],
        'next_case':book['next_case'] if not event['study_case_passes'] else None}
    _apply_profile(state, event['profile'])
    _append_event(workspace, state, event)
    return event


@_serialized
def session_status(workspace):
    state = _load_session(Path(workspace))
    return {**state, 'native_executions': sum(not r['reused'] for r in state['runs']),
            'reused_executions': sum(r['reused'] for r in state['runs']),
            'spent_native_seconds':sum(r.get('native_wall_seconds', 0) for r in state['runs'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    init.add_argument('--source', type=Path, required=True)
    init.add_argument('--trial')
    init.add_argument('--line', required=True)
    init.add_argument('--deadline')
    step = sub.add_parser('step')
    step.add_argument('--proposal', type=Path, required=True)
    service = sub.add_parser('service')
    service.add_argument('--proposal', type=Path, required=True)
    sub.add_parser('status')
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'init':
        value = start_session(args.workspace, args.source, line_id=args.line, trial_id=args.trial, deadline=args.deadline)
    elif args.command == 'step':
        value = run_local_step(args.workspace, json.loads(args.proposal.read_text()))
    elif args.command == 'service':
        value = run_service_step(args.workspace, json.loads(args.proposal.read_text()))
    else:
        value = session_status(args.workspace)
    print(json.dumps(value, ensure_ascii=False, indent=2))
