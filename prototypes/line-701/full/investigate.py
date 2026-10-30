"""Audit a model, diagnose one execution, reproduce a prefix or inspect a saved state."""
import argparse
import json
from pathlib import Path

from model_audit import audit_model
from prefix_reproduction import reproduce_prefix
from run_diagnostics import diagnose_trial
from snapshot_inspection import inspect_snapshot
from state_probe import probe_snapshot


def summary(report):
    schema = report['schema']
    if schema == 'invicta.model-audit.v1':
        lines = [f"Model: {report['status']} · {report['scheduled_trips']} scheduled trips",
                 'Findings: ' + (', '.join(report['blockers']) or 'none'), report['next_step']]
    elif schema == 'invicta.run-diagnosis.v1':
        coverage, metrics = report['coverage'], report['metrics']
        lines = [f"Execution: {report['source']['trial']} · {coverage['kind']}",
                 f"Reference: {coverage['scheduled_trips']} planned trips · {coverage['timing_checks']} timing checks"]
        observation = report.get('observation')
        if observation is not None:
            lines.append(f"Observed completions: {metrics['completed']} · checks due: {observation['due_checks']} · "
                         f"missing due: {observation['missing_due_checks']} · future checks: {observation['future_checks']}")
        first = report['first_failure']
        if first:
            lines.append(f"First failure: {first['trip']} at {first['stop']} · cause: {first['cause']}")
            interval = first['interval']
            if interval:
                lines.append(f"Interval: {interval['scheduled_seconds']} s budget; "
                             f"{interval['observed_seconds']} s observed; "
                             f"{interval['inherited_delay_seconds']} s inherited; "
                             f"{interval['added_delay_seconds']} s added")
        lines.append(report['next_step'])
    elif schema == 'invicta.snapshot-inspection.v1':
        lines = [f"Snapshot: {report['time']} s · {report['active_bus_count']} active buses · zero steps executed"]
        for row in report['contexts']:
            bus = row['vehicles'][0]
            lines.append(f"{row['trip']}: {bus['lane']} · {bus['waiting_seconds']} s waiting · "
                         f"{bus['proximate_observation']} · cause unclassified")
    elif schema == 'invicta.state-probe.v1':
        count = len(report['changed_parameter']['affected_connections'])
        lines = [f"State mechanism probe: {report['vehicle']} · {count} keep-clear connections changed"]
        for name in ['control', 'variant']:
            run = report[name]
            distance = run['last'].get('distance_metres', 'vehicle exited')
            lines.append(f"{name}: {run['simulation_steps']} steps · {distance} m · {run['collision_records']} collision records")
        lines.append('Diagnostic continuation only; Python controller state is not restored; no service qualification.')
    elif report.get('role') == 'original_input_blockage_reproduction':
        target = report['target']
        lines = ['Original-input blockage reproduction · ' +
                 (f"{target['trip']} at {target['time']} s" if target else 'no prolonged bus wait captured'),
                 f"Recorded bus-call prefix matches: {report['prefix_equivalence']['matched']}",
                 'Diagnostic onset only; full-service compliance is not established.']
    else:
        target = report['target']
        lines = [f"Reproduction: {report['role']} · {target['trip']} at {target['stop']}",
                 f"Target passes: {target['passes']} · original prefix matches: {report['prefix_equivalence']['matched']}",
                 'Diagnostic prefix only; full-service compliance is not established.']
    lines.append('Field validated: false')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    for name in ['audit', 'diagnose', 'reproduce', 'inspect', 'probe-state']:
        command = commands.add_parser(name)
        command.add_argument('--source', type=Path, required=name != 'audit', help='Trial folder or frozen ledger JSON')
        command.add_argument('--trial', help='Required when source is a ledger')
        command.add_argument('--model', type=Path, required=name == 'audit')
        command.add_argument('--format', choices=['summary', 'json', 'markdown'], default='summary')
        command.add_argument('--report', type=Path, help='Save a new JSON report without overwriting an existing file')
        if name in ['diagnose', 'reproduce', 'inspect']:
            command.add_argument('--trip')
        if name == 'audit':
            command.add_argument('--bus-length', type=float, default=12)
        if name == 'reproduce':
            command.add_argument('--output-dir', type=Path, required=True)
            command.add_argument('--stop')
            command.add_argument('--bus-sigma', type=float, help='Explicit uncertain-assumption sensitivity, 0 to 1')
            command.add_argument('--probe', choices=['omit_empty_request_stops', 'in_lane_checkpoints'],
                                 help='Empty-network stop-semantics diagnostic; never a passenger-service proposal')
            command.add_argument('--until-blockage', action='store_true',
                                 help='Replay unchanged inputs to first 300-second bus blockage; 12 h simulated / default 180 s native, max 900 s')
            command.add_argument('--wall-budget', type=float, help='Set an explicit native computation budget; preserves partial evidence')
        if name in ['inspect', 'probe-state']:
            command.add_argument('--snapshot', default='final-state.xml')
        if name == 'inspect':
            command.add_argument('--limit', type=int, default=8)
        if name == 'probe-state':
            command.add_argument('--vehicle', required=True)
            command.add_argument('--seconds', type=int, default=60)
            command.add_argument('--connections', type=int, default=1)
            command.add_argument('--wall-budget', type=float, default=120)
            command.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == 'audit':
            report = audit_model(args.model, args.source, args.trial, bus_length=args.bus_length)
        elif args.operation == 'diagnose':
            report = diagnose_trial(args.source, args.trial, args.model, args.trip)
        elif args.operation == 'inspect':
            report = inspect_snapshot(args.source, args.trial, args.model, args.snapshot, args.trip, args.limit)
        elif args.operation == 'probe-state':
            report = probe_snapshot(args.source, args.output_dir, args.vehicle, trial_id=args.trial, model=args.model,
                                    snapshot=args.snapshot, seconds=args.seconds, connections=args.connections,
                                    wall_budget_seconds=args.wall_budget)
        else:
            report = reproduce_prefix(args.source, args.output_dir, args.trial, args.model,
                                      args.trip, args.stop, args.bus_sigma, args.probe, args.until_blockage, args.wall_budget)
        if args.report:
            with args.report.open('x') as output:
                output.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    except (ValueError, OSError, TimeoutError) as error:
        parser.exit(1, f'Investigation failed: {error}\n')
    if args.format == 'json':
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.format == 'markdown':
        print('# 701 investigation\n\n' + summary(report) + '\n')
    else:
        print(summary(report))
    return 2 if args.operation == 'audit' and report['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
