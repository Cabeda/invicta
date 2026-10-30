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


def native_fixture(root, budget=100, request_stop=False, connected=False):
    model = root / 'model'
    model.mkdir()
    (model / 'nodes.xml').write_text('<nodes><node id="a" x="0" y="0"/><node id="b" x="300" y="0"/>'
                                   + ('<node id="c" x="600" y="0"/>' if connected else '') + '</nodes>')
    edges = ('<edge id="east" from="a" to="b" speed="13.88888888888889"/>'
             + ('<edge id="east2" from="b" to="c" speed="13.88888888888889"/>'
                '<edge id="west" from="c" to="b" speed="13.88888888888889"/>'
                '<edge id="west2" from="b" to="a" speed="13.88888888888889"/>' if connected else
                '<edge id="west" from="b" to="a" speed="13.88888888888889"/>'))
    (model / 'edges.xml').write_text('<edges>' + edges + '</edges>')
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
        if request_stop:
            stops.insert(1, {**stops[0], 'native_stop_id': f'd{direction}_MID', 'stop_id': 'MID',
                             'stop_name': 'MID', 'pos': 150, 'scheduled': 18100 + budget // 2,
                             'point': sumolib.geomhelper.positionAtShapeOffset(edge.getShape(), 150),
                             'designated_timing_point': False})
        path, shape = [road], edge.getShape()
        if connected:
            path.append(road + '2')
            last = net.getEdge(road + '2')
            shape += last.getShape()
            stops[-1].update(lane=road + '2_0', edge=road + '2', path_index=1,
                             point=sumolib.geomhelper.positionAtShapeOffset(last.getShape(), 280))
        directions[direction] = {'path': path, 'shape': shape, 'stops': stops,
                                 'trips': [{'id': f'd{direction}_bus_0', 'direction': direction,
                                            'depart': 18100, 'stops': stops, 'path': path}]}
    write_json(model / 'routes.json', {'directions': directions, 'trip_count': 2, 'served_calls': 6 if request_stop else 4,
                                      'network_sha256': digest(model / 'baseline.net.xml')})
    write_json(model / 'model.json', {'network_sha256': digest(model / 'baseline.net.xml'),
                                     'reference_sha256': digest(model / 'routes.json'),
                                     'limitations': ['Synthetic test fixture; not field data.']})
    return model


def empty_config(ident='fixture-empty'):
    return {**json.loads((ROOT / 'priority-configs/v5-empty-diagnostic-s17.json').read_text()), 'id': ident}


class InvestigationTests(unittest.TestCase):
    def test_archived_bus_only_controls_retain_both_scores_and_complete_service(self):
        source = ROOT.parents[2] / 'docs/research/701-bus-only-controls-2026-10-30/controls.json'
        ledger = json.loads(source.read_text())
        self.assertEqual(len(ledger['trials']), 6)
        for trial in ledger['trials']:
            self.assertEqual(trial['config']['traffic'], 'none')
            self.assertEqual(trial['vehicle_requests'], 0)
            self.assertEqual(trial['passenger_requests'], 0)
            report = diagnose_trial(source, trial['id'])
            self.assertEqual(report['coverage']['timing_checks'], 714)
            self.assertTrue(report['coverage']['full_service_day'])
            self.assertEqual(report['metrics']['completed'], 127)
            self.assertEqual(report['metrics'], {k: v for k, v in trial['metrics'].items() if k != 'failures'})
            self.assertEqual(report['operational_metrics'], trial['operational_metrics'])
            self.assertFalse(report['simulation_compliance'])
            self.assertEqual(report['operational_compliance'], trial['config'].get('diagnostic_all_green', False))

    def test_failed_compound_candidate_does_not_become_a_timetable_pass(self):
        source = ROOT.parents[2] / 'docs/research/701-bus-only-controls-2026-10-30/candidate-controls.json'
        ledger = json.loads(source.read_text())
        self.assertEqual(ledger['status'], 'rejected_prerequisite_still_fails')
        self.assertFalse(ledger['qualified'])
        report = diagnose_trial(source, ledger['trials'][0]['id'])
        self.assertEqual(report['metrics']['completed'], 127)
        self.assertEqual(report['metrics']['checkpoints'], 714)
        self.assertEqual(report['metrics']['late_checkpoints'], 10)
        self.assertEqual(report['operational_metrics']['late_checkpoints'], 3)
        self.assertFalse(report['operational_compliance'])
        self.assertFalse(report['simulation_compliance'])

    def test_operational_tolerance_is_reported_without_replacing_strict_or_early_failures(self):
        from timetable import assess_trial
        scheduled = [{'id': 'bus', 'stops': [
            {'native_stop_id': 'A', 'scheduled': 100, 'designated_timing_point': True},
            {'native_stop_id': 'B', 'scheduled': 200, 'designated_timing_point': True}]}]
        calls = [{'id': 'bus', 'busStop': 'A', 'started': '99', 'ended': '100'},
                 {'id': 'bus', 'busStop': 'B', 'started': '260', 'ended': '261'}]
        self.assertFalse(assess_trial(scheduled, calls, {'bus'})['passes'])
        self.assertTrue(assess_trial(scheduled, calls, {'bus'}, lateness_tolerance_seconds=60)['passes'])
        calls[1]['started'] = '261'
        self.assertFalse(assess_trial(scheduled, calls, {'bus'}, lateness_tolerance_seconds=60)['passes'])
        calls[1]['started'] = '190'
        calls[0]['ended'] = '99'
        self.assertFalse(assess_trial(scheduled, calls, {'bus'}, lateness_tolerance_seconds=60)['passes'])
        for invalid in [-1, float('nan'), float('inf'), True]:
            with self.assertRaises(ValueError):
                assess_trial(scheduled, calls, {'bus'}, lateness_tolerance_seconds=invalid)

    def test_bus_only_control_keeps_existing_signals_and_blocks_traffic_when_late(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, budget=1)
            config = {**empty_config('bus-only-existing-signals'),
                'diagnostic_all_green': False, 'diagnostic_control': 'existing_signals'}
            result = run_trial(model, root, config)
            self.assertNotIn('--tls.all-off', result['command'])
            self.assertFalse(result['metrics']['passes'])
            report = audit_model(model, root / config['id'])
            self.assertIn('unresolved_empty_diagnostic', report['blockers'])
            with self.assertRaises(ModelNotReadyError):
                run_trial(model, root, {'id': 'traffic-too-early', 'traffic': 'moderate', 'seed': 17,
                    'readiness': {'source': str(root / config['id'])},
                    'hypothesis': {'change': 'Traffic', 'prediction': 'Still late', 'evidence': 'Control'}})
            self.assertFalse((root / 'traffic-too-early').exists())

    def test_readiness_rescores_the_frozen_control_at_the_explicit_target(self):
        from model_audit import require_readiness
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, budget=1)
            config = {**empty_config(), 'operational_lateness_seconds': 60,
                      'diagnostic_all_green': False, 'diagnostic_control': 'existing_signals'}
            result = run_trial(model, root, config)
            self.assertFalse(result['metrics']['passes'])
            self.assertTrue(result['operational_metrics']['passes'])
            raw_result = (root / config['id'] / 'result.json').read_bytes()
            strict = audit_model(model, root / config['id'], lateness_tolerance_seconds=0)
            operational = audit_model(model, root / config['id'], lateness_tolerance_seconds=60)
            self.assertIn('unresolved_empty_diagnostic', strict['blockers'])
            self.assertEqual(operational['status'], 'ready_for_full_run')
            self.assertFalse(operational['diagnosis']['simulation_compliance'])
            self.assertTrue(operational['diagnosis']['operational_compliance'])
            self.assertNotEqual(strict['id'], operational['id'])
            self.assertEqual((root / config['id'] / 'result.json').read_bytes(), raw_result)
            candidate = {'traffic': 'none', 'readiness': {'source': str(root / config['id'])},
                         'hypothesis': {'change': 'Control', 'prediction': 'Complete', 'evidence': 'Fixture'}}
            with self.assertRaises(ModelNotReadyError):
                require_readiness(model, candidate)
            self.assertEqual(require_readiness(model, {**candidate, 'operational_lateness_seconds': 60})['status'],
                             'ready_for_full_run')

    def test_signals_off_pass_is_only_an_optimistic_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            run_trial(model, root, empty_config())
            report = audit_model(model, root / 'fixture-empty', lateness_tolerance_seconds=60)
            self.assertTrue(report['diagnosis']['operational_compliance'])
            self.assertIn('diagnostic_signals_disabled', report['blockers'])

    def test_native_onset_capture_stops_at_an_actual_red_signal_blockage(self):
        import xml.etree.ElementTree as ET
        from native_runner import run_native
        from prefix_reproduction import set_option
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, connected=True)
            original = run_trial(model, root, empty_config())
            folder = root / 'red-signal-control'
            folder.mkdir()
            subprocess.run([str(Path(sumo.SUMO_HOME) / 'bin/netconvert'),
                '--sumo-net-file', str(root / 'fixture-empty/network.net.xml'), '--tls.set', 'b',
                '--tls.default-type', 'static', '--output-file', str(folder / 'network.net.xml')],
                check=True, capture_output=True)
            network = ET.parse(folder / 'network.net.xml')
            phases = network.getroot().findall('tlLogic/phase')
            self.assertTrue(phases)
            for phase in phases:
                phase.set('state', 'r' * len(phase.get('state')))
            network.write(folder / 'network.net.xml')
            command = list(original['command'])
            index = command.index('--tls.all-off')
            del command[index:index + 2]
            for flag, name in [('--net-file', 'network.net.xml'), ('--tripinfo-output', 'trips.xml'),
                               ('--stop-output', 'stops.xml'), ('--collision-output', 'collisions.xml'),
                               ('--save-state.files', 'final-state.xml')]:
                set_option(command, flag, folder / name)
            set_option(command, '--end', 18500)
            reference = json.loads((model / 'routes.json').read_text())
            buses = [trip for direction in reference['directions'].values() for trip in direction['trips']]
            result = run_native(command, buses, folder, monitor_options={
                'stall_seconds': 2, 'stop_on_first_blockage': True, 'max_wall_seconds': 10})
            observed = result['diagnostics']
            self.assertEqual(observed['stop_reason'], 'first_blockage')
            self.assertIsNotNone(observed['first_prolonged_wait'])
            self.assertLess(observed['simulation_time'], 18500)
            self.assertTrue((folder / 'first-blockage-state.xml.gz').exists())

    def test_partial_diagnosis_distinguishes_future_checks_from_observed_misses(self):
        archive = ROOT.parents[2] / 'docs/research/701-followup-2026-10-30'
        manifest = json.loads((archive / 'manifest.json').read_text())
        case = manifest['cases']['original-driver-no-unused-stops']['files']
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            for name in ['reference.json', 'reproduction.json', 'stops.xml', 'trips.xml']:
                item = case[name]
                (source / name).write_bytes(gzip.decompress((archive / item['file']).read_bytes()))
            report = diagnose_trial(source)
        self.assertEqual(report['coverage']['scheduled_trips'], 127)
        self.assertEqual(report['coverage']['timing_checks'], 714)
        self.assertEqual(report['metrics']['missing_checkpoints'], 712)  # Whole-reference goal, not observed loss.
        self.assertEqual(report['observation']['due_checks'], 2)
        self.assertEqual(report['observation']['future_checks'], 712)
        self.assertEqual(report['observation']['missing_due_checks'], 0)
        self.assertEqual(report['observation']['late_observed_checks'], 1)
        self.assertFalse(report['unfinished_trips'])
        self.assertEqual(len(report['observation']['future_trip_ids']), 126)

    def test_published_followup_distinguishes_diagnostic_success_from_service_success(self):
        folder = ROOT.parents[2] / 'docs/research/701-followup-2026-10-30'
        manifest = json.loads((folder / 'manifest.json').read_text())
        verified = set()
        def payload(item):
            path = (folder / item['file']).resolve()
            self.assertTrue(path.is_relative_to(ROOT.parents[2].resolve()))
            compressed = path.read_bytes()
            self.assertEqual(hashlib.sha256(compressed).hexdigest(), item['gzip_sha256'])
            raw = gzip.decompress(compressed)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item['sha256'])
            return raw
        for case in manifest['cases'].values():
            for item in case['files'].values():
                if item['gzip_sha256'] not in verified:
                    payload(item)
                    verified.add(item['gzip_sha256'])
            if case['kind'] == 'prefix':
                result = json.loads(payload(case['files']['reproduction.json']))
                for name, expected in {**result['input_hashes'], **result['output_hashes']}.items():
                    self.assertEqual(case['files'][name]['sha256'], expected)
                self.assertFalse(result['full_service_compliance'])
                self.assertEqual(result['metrics']['planned'], 127)
                self.assertEqual(result['metrics']['checkpoints'], 714)
            if 'variant_network_delta' in case:
                delta = case['variant_network_delta']
                network = payload(case['files'][delta['source']])
                for change in delta['replacements']:
                    self.assertEqual(network.count(change['before'].encode()), 1)
                    network = network.replace(change['before'].encode(), change['after'].encode(), 1)
                self.assertEqual(hashlib.sha256(network).hexdigest(), delta['sha256'])
        cases = manifest['cases']
        def report(case, name):
            return json.loads(payload(cases[case]['files'][name]))
        passing = report('no-unused-stops-first-interval', 'reproduction.json')
        self.assertTrue(passing['target']['passes'])
        self.assertEqual(len(passing['sensitivity']['affected_stops']), 20)
        self.assertEqual(passing['sensitivity']['parent_role'], 'uncertain_assumption_sensitivity')
        original = report('original-driver-no-unused-stops', 'reproduction.json')
        self.assertEqual(float(original['target']['call']['ended']) - original['target']['scheduled'], 14)
        parked = report('in-lane-checkpoints', 'reproduction.json')
        self.assertEqual(float(parked['target']['call']['ended']) - parked['target']['scheduled'], 5)
        tail = report('baseline-one-step-tail-check', 'tail-check.json')
        self.assertFalse(tail['matches_within_native_output_precision'])
        self.assertEqual(cases['baseline-one-step-tail-check']['files']['original-trips.xml']['sha256'],
                         tail['original_trip_output_sha256'])
        onset = report('original-candidate-onset', 'failed-replay-audit.json')
        self.assertEqual(onset['observed_through_seconds'], 28847)
        self.assertEqual(onset['complete_bus_calls_compared'], 855)
        self.assertTrue(onset['bus_call_prefix_matches'])
        self.assertIsNone(onset['first_prolonged_wait'])
        later = report('original-candidate-onset-600', 'reproduction.json')
        self.assertEqual(later['execution_scope']['end'], 54602)
        self.assertEqual(later['prefix_equivalence']['compared_calls'], 3025)
        self.assertTrue(later['prefix_equivalence']['matched'])
        self.assertIsNone(later['target'])
        self.assertEqual(later['observation']['future_checks'], 353)
        self.assertEqual(later['observation']['missing_due_checks'], 1)
        reduced = report('reduced-two-vehicle-junction', 'summary.json')
        self.assertFalse(reduced['full_service_compliance'])
        self.assertEqual(len(reduced['cases']), 4)
        for case in reduced['cases']:
            self.assertEqual(case['departed'], ['major', 'minor'])
            self.assertEqual(case['completed'], ['major', 'minor'])
            self.assertEqual(case['collision_records'], 0)

    def test_computation_budget_preserves_partial_evidence_without_passing_the_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            run_trial(model, root, empty_config())
            result = reproduce_prefix(root / 'fixture-empty', root / 'limited', trip_id='d1_bus_0',
                                      stop_id='d1_B', wall_budget_seconds=.000001)
            self.assertEqual(result['diagnostics']['stop_reason'], 'native_wall_budget')
            self.assertFalse(result['target']['passes'])
            self.assertFalse(result['full_service_compliance'])
            self.assertEqual(result['prefix_equivalence']['matched'], None)
            self.assertLess(result['execution_scope']['end'], 18100)
            self.assertTrue((root / 'limited/reproduction.json').exists())
            self.assertIn('trips.xml', result['output_hashes'])

    def test_original_input_blockage_replay_cannot_qualify_even_when_fixture_service_finishes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            run_trial(model, root, empty_config())
            report = reproduce_prefix(root / 'fixture-empty', root / 'onset', until_blockage=True)
            self.assertEqual(report['role'], 'original_input_blockage_reproduction')
            self.assertEqual(report['execution_scope']['kind'], 'diagnostic_onset')
            self.assertTrue(report['prefix_equivalence']['matched'])
            self.assertFalse(report['full_service_compliance'])
            with self.assertRaisesRegex(ValueError, 'at most 900'):
                reproduce_prefix(root / 'fixture-empty', root / 'unbounded-onset', until_blockage=True,
                                 wall_budget_seconds=901)
            self.assertFalse((root / 'unbounded-onset').exists())

    def test_paired_state_probe_is_bounded_and_cannot_be_read_as_a_service_execution(self):
        from state_probe import probe_snapshot
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, budget=1, connected=True)
            original = run_trial(model, root, empty_config())
            source = root / 'fixture-empty'
            result = probe_snapshot(source, root / 'state-probe', 'd1_bus_0', seconds=2,
                                    snapshot='first-deadline-state.xml.gz')
            self.assertEqual(result['role'], 'snapshot_mechanism_probe')
            self.assertEqual(result['control']['simulation_steps'], 2)
            self.assertEqual(result['variant']['simulation_steps'], 2)
            self.assertFalse(result['full_service_compliance'])
            self.assertFalse(result['controller_state_restored'])
            self.assertFalse((root / 'state-probe/result.json').exists())
            self.assertEqual(digest(source / 'network.net.xml'), original['input_hashes']['network.net.xml'])
            with self.assertRaisesRegex(ValueError, 'bounded'):
                probe_snapshot(source, root / 'unbounded', 'd1_bus_0', seconds=301)

    def test_state_probe_budget_preserves_zero_step_branch_observations(self):
        from state_probe import probe_snapshot
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, budget=1, connected=True)
            run_trial(model, root, empty_config())
            report = probe_snapshot(root / 'fixture-empty', root / 'limited-state', 'd1_bus_0', seconds=2,
                                    snapshot='first-deadline-state.xml.gz', wall_budget_seconds=.000001)
            for branch in ['control', 'variant']:
                self.assertEqual(report[branch]['simulation_steps'], 0)
                self.assertEqual(report[branch]['stop_reason'], 'native_wall_budget')
                self.assertEqual(report[branch]['end'], report[branch]['begin'])
                self.assertTrue((root / 'limited-state' / branch / 'trace.json').exists())
            self.assertTrue((root / 'limited-state/state-probe.json').exists())
            self.assertFalse(report['full_service_compliance'])

    def test_empty_stop_semantics_probe_preserves_route_and_cannot_qualify_service(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, request_stop=True)
            run_trial(model, root, empty_config())
            source = root / 'fixture-empty'
            before = digest(source / 'routes.rou.xml')
            result = reproduce_prefix(source, root / 'skip-probe', trip_id='d1_bus_0', stop_id='d1_B',
                                      probe='omit_empty_request_stops')
            self.assertEqual(result['role'], 'model_semantics_sensitivity')
            self.assertEqual(result['sensitivity']['affected_stops'], ['d1_MID'])
            self.assertEqual(result['sensitivity']['physical_intervention'], False)
            self.assertEqual(result['metrics']['checkpoints'], 4)
            self.assertEqual(result['metrics']['planned'], 2)
            self.assertFalse(result['full_service_compliance'])
            self.assertEqual(digest(source / 'routes.rou.xml'), before)
            import xml.etree.ElementTree as ET
            native = ET.parse(root / 'skip-probe/routes.rou.xml').getroot()
            self.assertEqual(native.find("vehicle[@id='d1_bus_0']/route").get('edges'), 'east')
            self.assertEqual([s.get('busStop') for s in native.find("vehicle[@id='d1_bus_0']").findall('stop')],
                             ['d1_A', 'd1_B'])
            with self.assertRaisesRegex(ValueError, 'one diagnostic variable'):
                reproduce_prefix(source, root / 'mixed-probe', trip_id='d1_bus_0', stop_id='d1_B',
                                 probe='omit_empty_request_stops', bus_sigma=0)
            self.assertFalse((root / 'mixed-probe').exists())

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
            with self.assertRaisesRegex(ValueError, 'passenger-free'):
                reproduce_prefix(source, root / 'invalid-stop-probe', trip_id='d1_bus_0', stop_id='d1_B',
                                 probe='omit_empty_request_stops')
            self.assertFalse((root / 'invalid-stop-probe').exists())

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
            result = run_trial(model, root, {**empty_config(), 'diagnostic_all_green': False,
                                             'diagnostic_control': 'existing_signals'})
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
