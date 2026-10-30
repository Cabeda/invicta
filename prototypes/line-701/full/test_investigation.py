"""Acceptance at the native evidence loading and timetable evaluation seams."""
import unittest
from pathlib import Path
import tempfile
import json
import subprocess
import io
import gzip
import hashlib
import shutil
from contextlib import redirect_stdout
import sumo
import sumolib

from run_diagnostics import diagnose_trial
from priority_search import run_trial, ModelNotReadyError
from model_audit import audit_model
from trial_evidence import read_archive
from prepare import digest, write_json
from prefix_reproduction import reproduce_prefix
from snapshot_inspection import inspect_snapshot
from investigate import main

ROOT = Path(__file__).parent


def native_fixture(root, budget=100):
    model = root / 'model'
    model.mkdir()
    (model / 'nodes.xml').write_text('<nodes><node id="a" x="0" y="0"/><node id="b" x="300" y="0"/></nodes>')
    (model / 'edges.xml').write_text('<edges><edge id="east" from="a" to="b" speed="13.88888888888889"/>'
                                   '<edge id="west" from="b" to="a" speed="13.88888888888889"/></edges>')
    subprocess.run([str(Path(sumo.SUMO_HOME) / 'bin/netconvert'),
                    '--node-files', str(model / 'nodes.xml'), '--edge-files', str(model / 'edges.xml'),
                    '--no-turnarounds', 'true', '--output-file', str(model / 'baseline.net.xml')],
                   check=True, capture_output=True)
    net = sumolib.net.readNet(str(model / 'baseline.net.xml'))
    directions = {}
    for direction, road in [('1', 'east'), ('0', 'west')]:
        edge = net.getEdge(road)
        stops = [{'native_stop_id': f'd{direction}_{name}', 'stop_id': name, 'stop_name': name,
                  'lane': road + '_0', 'edge': road, 'pos': position, 'path_index': 0,
                  'point': sumolib.geomhelper.positionAtShapeOffset(edge.getShape(), position),
                  'designated_timing_point': True, 'scheduled': scheduled}
                 for name, position, scheduled in [('A', 15, 18100), ('B', 280, 18100 + budget)]]
        directions[direction] = {'path': [road], 'shape': edge.getShape(), 'stops': stops,
                                 'trips': [{'id': f'd{direction}_bus_0', 'direction': direction,
                                            'depart': 18100, 'stops': stops, 'path': [road]}]}
    write_json(model / 'routes.json', {'directions': directions, 'trip_count': 2, 'served_calls': 4,
                                      'network_sha256': digest(model / 'baseline.net.xml')})
    write_json(model / 'model.json', {'network_sha256': digest(model / 'baseline.net.xml'),
                                     'reference_sha256': digest(model / 'routes.json'),
                                     'limitations': ['Synthetic test fixture; not field data.']})
    return model


def empty_config(ident='fixture-empty'):
    return {**json.loads((ROOT / 'priority-configs/v5-empty-diagnostic-s17.json').read_text()), 'id': ident}


class InvestigationTests(unittest.TestCase):
    def test_traffic_prefix_counts_only_completed_scheduled_buses(self):
        import xml.etree.ElementTree as ET
        from prefix_reproduction import set_option
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            base = run_trial(model, root, empty_config())
            source = root / 'with-car'
            source.mkdir()
            names = ['network.net.xml', 'routes.rou.xml', 'additional.add.xml', 'reference.json']
            for name in names:
                shutil.copy2(root / 'fixture-empty' / name, source / name)
            xml = ET.parse(source / 'routes.rou.xml')
            car = ET.SubElement(xml.getroot(), 'vehicle', id='car', type='resident', depart='18100')
            ET.SubElement(car, 'route', edges='east')
            xml.write(source / 'routes.rou.xml')
            command = list(base['command'])
            for flag, name in [('--net-file', 'network.net.xml'), ('--route-files', 'routes.rou.xml'),
                               ('--additional-files', 'additional.add.xml'), ('--tripinfo-output', 'trips.xml'),
                               ('--stop-output', 'stops.xml'), ('--collision-output', 'collisions.xml'),
                               ('--save-state.files', 'final-state.xml')]:
                set_option(command, flag, source / name)
            subprocess.run(command, check=True, capture_output=True)
            write_json(source / 'result.json', {**base, 'config': {'id': 'with-car', 'traffic': 'moderate'},
                'command': command, 'input_hashes': {name: digest(source / name) for name in names},
                'output_hashes': {name: digest(source / name) for name in ['stops.xml', 'trips.xml', 'collisions.xml']}})
            prefix = reproduce_prefix(source, root / 'traffic-control', trip_id='d1_bus_0', stop_id='d1_B')
            self.assertEqual(prefix['metrics']['completed'], 2)
            self.assertEqual(prefix['metrics']['completed'], diagnose_trial(root / 'traffic-control')['metrics']['completed'])

    def test_published_prefix_evidence_retains_original_bindings_and_full_day_rejection(self):
        folder = ROOT.parents[2] / 'docs/research/701-investigation-2026-10-30'
        manifest = json.loads((folder / 'manifest.json').read_text())
        for execution in manifest['executions'].values():
            raw = {}
            for name, item in execution['files'].items():
                path = (folder / item['file']).resolve()
                self.assertTrue(path.is_relative_to(ROOT.parents[2].resolve()))
                compressed = path.read_bytes()
                self.assertEqual(hashlib.sha256(compressed).hexdigest(), item['gzip_sha256'])
                raw[name] = gzip.decompress(compressed)
                self.assertEqual(hashlib.sha256(raw[name]).hexdigest(), item['sha256'])
            result = json.loads(raw['reproduction.json'])
            for name, expected in {**result['input_hashes'], **result['output_hashes']}.items():
                self.assertEqual(hashlib.sha256(raw[name]).hexdigest(), expected)
            self.assertFalse(result['full_service_compliance'])
            self.assertEqual(result['metrics']['planned'], 127)
            self.assertEqual(result['metrics']['checkpoints'], 714)
            if execution['role'] == 'recorded_prefix_reproduction':
                self.assertTrue(result['prefix_equivalence']['matched'])
                self.assertEqual(result['prefix_equivalence']['compared_calls'], 25)
            else:
                self.assertEqual(float(result['target']['call']['ended']) - result['target']['scheduled'], 5)

    def test_compiled_inputs_reject_a_dropped_bus_or_altered_physical_endpoint(self):
        import xml.etree.ElementTree as ET
        from scenario_audit import audit_scenario
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            run_trial(model, root, empty_config())
            folder = root / 'fixture-empty'
            reference = json.loads((model / 'routes.json').read_text())
            xml = ET.parse(folder / 'routes.rou.xml')
            car = ET.SubElement(xml.getroot(), 'vehicle', id='car', type='resident', depart='18100',
                                departPos='5', arrivalPos='290')
            ET.SubElement(car, 'route', edges='east')
            xml.write(folder / 'routes.rou.xml')
            request = {'id': 'car', 'group': 'resident', 'from': 'east', 'to': 'east',
                       'depart': 18100, 'depart_pos': 5, 'arrival_pos': 290}
            report = audit_scenario(folder, reference, [request], 0, 0)
            self.assertEqual(report['ordinary_requests'], 1)
            with self.assertRaisesRegex(ValueError, 'endpoint'):
                audit_scenario(folder, reference, [{**request, 'arrival_pos': 280}], 0, 0)
            xml.getroot().remove(xml.getroot().find('vehicle'))
            xml.write(folder / 'routes.rou.xml')
            with self.assertRaisesRegex(ValueError, 'scheduled bus'):
                audit_scenario(folder, reference, [request], 0, 0)

    def test_cli_diagnoses_archived_evidence_without_starting_native_traffic(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'diagnosis.json'
            with redirect_stdout(io.StringIO()) as stdout:
                status = main(['diagnose', '--source', str(ROOT / 'priority-search.json'),
                               '--trial', 'v5-empty-diagnostic-s17', '--report', str(output)])
            self.assertEqual(status, 0)
            self.assertIn('19.0 s added', stdout.getvalue())
            self.assertLess(len(stdout.getvalue()), 1000)
            self.assertEqual(json.loads(output.read_text())['coverage']['scheduled_trips'], 127)

    def test_snapshot_inspection_preserves_time_and_rejects_changed_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, budget=1)
            source = root / 'fixture-empty'
            result = run_trial(model, root, empty_config())
            report = inspect_snapshot(source, model=model, snapshot='first-deadline-state.xml.gz')
            self.assertEqual(report['simulation_steps'], 0)
            self.assertEqual(report['time'], 18102)
            self.assertEqual(report['active_bus_count'], 2)
            self.assertEqual(report['cause'], 'unclassified')
            self.assertEqual(digest(source / 'routes.rou.xml'), result['input_hashes']['routes.rou.xml'])
            with (source / 'routes.rou.xml').open('a') as output:
                output.write('\n')
            with self.assertRaisesRegex(ValueError, 'differs from execution binding'):
                inspect_snapshot(source, model=model)

    def test_observed_native_path_matches_passive_cli_bus_calls(self):
        from prefix_reproduction import set_option
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            result = run_trial(model, root, empty_config())
            command = list(result['command'])
            for flag, name in [('--tripinfo-output', 'cli-trips.xml'), ('--stop-output', 'cli-stops.xml'),
                               ('--collision-output', 'cli-collisions.xml'), ('--save-state.files', 'cli-state.xml')]:
                set_option(command, flag, root / name)
            subprocess.run(command, check=True, capture_output=True)
            actual = [row.attrib for row in ET.parse(root / 'fixture-empty/stops.xml').getroot()]
            cli = [row.attrib for row in ET.parse(root / 'cli-stops.xml').getroot()]
            self.assertEqual(actual, cli)

    def test_readiness_cannot_reuse_a_different_vehicle_or_disable_signals_in_traffic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            run_trial(model, root, empty_config())
            report = audit_model(model, root / 'fixture-empty', bus_length=13)
            self.assertIn('diagnostic_vehicle', report['blockers'])
            with self.assertRaises(ModelNotReadyError) as error:
                run_trial(model, root, {**empty_config('bad-profile'), 'traffic': 'moderate'})
            self.assertIn('invalid_empty_diagnostic_profile', error.exception.report['blockers'])

    def test_reproduction_preserves_inputs_and_cannot_be_promoted_to_a_full_day(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            source = run_trial(model, root, empty_config())
            before = digest(root / 'fixture-empty/routes.rou.xml')
            control = reproduce_prefix(root / 'fixture-empty', root / 'control', model=model,
                                       trip_id='d1_bus_0', stop_id='d1_B')
            self.assertTrue(control['prefix_equivalence']['matched'])
            self.assertTrue(control['target']['passes'])
            self.assertFalse(control['full_service_compliance'])
            report = audit_model(model, root / 'control')
            self.assertIn('diagnostic_scope', report['blockers'])
            sensitivity = reproduce_prefix(root / 'fixture-empty', root / 'sensitivity', model=model,
                                           trip_id='d1_bus_0', stop_id='d1_B', bus_sigma=0)
            self.assertEqual(sensitivity['changed_inputs'], ['routes.rou.xml'])
            self.assertEqual(sensitivity['role'], 'uncertain_assumption_sensitivity')
            self.assertEqual(before, digest(root / 'fixture-empty/routes.rou.xml'))
            self.assertFalse(sensitivity['full_service_compliance'])

    def test_native_execution_captures_the_first_missed_checkpoint_and_phase_timings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, budget=1)
            result = run_trial(model, root, empty_config())
            self.assertFalse(result['metrics']['passes'])
            self.assertGreater(result['phase_timings']['native_execution_seconds'], 0)
            monitor = result['diagnostics']
            self.assertEqual(monitor['first_deadline_pending']['time'], 18102)
            self.assertIn('first-deadline-state.xml.gz', result['output_hashes'])
            self.assertIn('trace.jsonl', result['output_hashes'])
            report = diagnose_trial(root / 'fixture-empty', model=model)
            self.assertIsNotNone(report['first_failure']['trace_observation'])

    def test_passing_native_control_has_a_readiness_path_without_claiming_field_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            result = run_trial(model, root, empty_config())
            self.assertTrue(result['metrics']['passes'])
            report = audit_model(model, root / 'fixture-empty')
            self.assertEqual(report['status'], 'ready_for_full_run')
            self.assertFalse(report['blockers'])
            self.assertFalse(report['field_validated'])
            config = {**empty_config('gated-run'), 'diagnostic_all_green': False,
                      'readiness': {'source': str(root / 'fixture-empty')},
                      'hypothesis': {'change': 'Keep ordinary signal behavior in the synthetic fixture.',
                                     'prediction': 'Both scheduled workings still pass.',
                                     'evidence': 'The bound empty fixture passes all four checks.'}}
            gated = run_trial(model, root, config)
            self.assertEqual(gated['readiness']['status'], 'ready_for_full_run')
            self.assertTrue(gated['metrics']['passes'])
            self.assertEqual(gated['scenario_audit']['scheduled_trips'], 2)

    def test_current_model_is_blocked_by_its_bound_empty_diagnostic(self):
        ledger = json.loads((ROOT / 'priority-search.json').read_text())
        descriptor = ledger['models']['street-detail-v5']
        trial = next(t for t in ledger['trials'] if t['id'] == 'v5-moderate-baseline-mapped-s17')
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary)
            for name in ['model.json', 'routes.json']:
                (model / name).write_bytes(read_archive(ROOT, descriptor['evidence'][name]))
            (model / 'baseline.net.xml').write_bytes(read_archive(ROOT, trial['evidence']['network.net.xml']))
            report = audit_model(model, ROOT / 'priority-search.json', 'v5-empty-diagnostic-s17')
        self.assertEqual(report['status'], 'blocked')
        self.assertIn('unresolved_empty_diagnostic', report['blockers'])
        self.assertEqual(report['scheduled_trips'], 127)
        self.assertEqual(report['diagnosis']['first_failure']['interval']['added_delay_seconds'], 19)
        self.assertFalse(report['field_validated'])

    def test_full_run_without_readiness_is_rejected_before_creating_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ModelNotReadyError) as error:
                run_trial(root / 'unprepared-model', root, {'id': 'expensive', 'traffic': 'moderate'})
            self.assertEqual(error.exception.report['status'], 'blocked')
            self.assertIn('missing_readiness_evidence', error.exception.report['blockers'])
            self.assertFalse((root / 'expensive').exists())

    def test_first_checkpoint_diagnosis_retains_the_complete_frozen_service(self):
        report = diagnose_trial(ROOT / 'priority-search.json', 'v5-empty-diagnostic-s17')
        self.assertEqual(report['coverage']['scheduled_trips'], 127)
        self.assertEqual(report['coverage']['timing_checks'], 714)
        self.assertFalse(report['simulation_compliance'])
        first = report['first_failure']
        self.assertEqual((first['trip'], first['stop']), ('d1_bus_0', 'd1_ERM3'))
        self.assertEqual(first['interval']['from_stop'], 'd1_COD4')
        self.assertEqual(first['interval']['scheduled_seconds'], 480)
        self.assertEqual(first['interval']['observed_seconds'], 499)
        self.assertEqual(first['interval']['inherited_delay_seconds'], 0)
        self.assertEqual(first['interval']['added_delay_seconds'], 19)
        self.assertEqual(first['cause'], 'unclassified')
        self.assertFalse(report['field_validated'])


if __name__ == '__main__':
    unittest.main()
