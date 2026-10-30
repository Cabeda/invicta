"""Audit a model, diagnose one execution, reproduce a prefix or inspect a saved state."""
import argparse
import json
from pathlib import Path

from model_audit import audit_model
from prefix_reproduction import reproduce_prefix
from run_diagnostics import diagnose_trial
from snapshot_inspection import inspect_snapshot


def summary(report):
    schema = report['schema']
    if schema == 'invicta.model-audit.v1':
        lines = [f"Model: {report['status']} · {report['scheduled_trips']} scheduled trips",
                 'Findings: ' + (', '.join(report['blockers']) or 'none'), report['next_step']]
    elif schema == 'invicta.run-diagnosis.v1':
        coverage, metrics = report['coverage'], report['metrics']
        lines = [f"Execution: {report['source']['trial']} · {coverage['kind']}",
                 f"Completed: {metrics['completed']}/{coverage['scheduled_trips']} · "
                 f"missing checks: {metrics['missing_checkpoints']}/{coverage['timing_checks']}"]
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
    for name in ['audit', 'diagnose', 'reproduce', 'inspect']:
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
        if name == 'inspect':
            command.add_argument('--snapshot', default='final-state.xml')
            command.add_argument('--limit', type=int, default=8)
    args = parser.parse_args(argv)
    try:
        if args.operation == 'audit':
            report = audit_model(args.model, args.source, args.trial, bus_length=args.bus_length)
        elif args.operation == 'diagnose':
            report = diagnose_trial(args.source, args.trial, args.model, args.trip)
        elif args.operation == 'inspect':
            report = inspect_snapshot(args.source, args.trial, args.model, args.snapshot, args.trip, args.limit)
        else:
            report = reproduce_prefix(args.source, args.output_dir, args.trial, args.model,
                                      args.trip, args.stop, args.bus_sigma)
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
