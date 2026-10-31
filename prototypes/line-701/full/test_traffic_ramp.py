"""Acceptance for nested demand and evidence-bound model review."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import sumolib
from traffic_workload import select_traffic
from model_review import stop_reviews

ROOT = Path(__file__).parent


class TrafficWorkloadTests(unittest.TestCase):
    def test_ramp_is_nested_and_preserves_physical_request_identity(self):
        source = [{'id': 'car' + str(i), 'from': 'a', 'to': 'b', 'depart': i / 3, 'kind': 'passenger'}
                  for i in range(1000)]
        original = copy.deepcopy(source)
        previous = set()
        for fraction in [0, .01, .05, .1, .25, .5, 1]:
            selected, report = select_traffic(source, fraction)
            self.assertLessEqual(previous, {r['id'] for r in selected})
            self.assertEqual(report['selected_requests'], len(selected))
            self.assertEqual(select_traffic(source, fraction), (selected, report))
            for row in selected:
                self.assertIn(row, source)
            previous = {r['id'] for r in selected}
        self.assertEqual(source, original)
        self.assertEqual(select_traffic(source, 0)[0], [])
        self.assertEqual(select_traffic(source, 1)[0], source)

    def test_invalid_levels_or_duplicate_requests_are_rejected(self):
        for value in [-1, 1.1, True, float('nan'), float('inf'), '0.1']:
            with self.assertRaises(ValueError):
                select_traffic([], value)
        with self.assertRaises(ValueError):
            select_traffic([{'id': 'a'}, {'id': 'a'}])

    def test_identical_networks_share_storage_without_changing_their_bytes(self):
        import os
        from native_input_cache import intern_network
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a, b, c = [root / name for name in ['a.xml', 'b.xml', 'c.xml']]
            a.write_bytes(b'same native network')
            b.write_bytes(a.read_bytes())
            c.write_bytes(b'different native network')
            self.assertEqual(intern_network(a, root / 'pool'), intern_network(b, root / 'pool'))
            self.assertTrue(os.path.samefile(a, b))
            self.assertEqual(b.read_bytes(), b'same native network')
            intern_network(c, root / 'pool')
            self.assertFalse(os.path.samefile(a, c))

    def test_unsupported_hard_links_keep_an_unchanged_native_input(self):
        import errno
        from unittest.mock import patch
        from native_input_cache import intern_network
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            network = root / 'network.xml'
            network.write_bytes(b'unchanged native input')
            with patch('native_input_cache.os.link', side_effect=OSError(errno.EXDEV, 'different volumes')):
                self.assertEqual(len(intern_network(network, root / 'pool')), 64)
            self.assertEqual(network.read_bytes(), b'unchanged native input')


class PairedWorkloadTests(unittest.TestCase):
    def test_archive_preserves_a_snapshot_missing_from_historical_output_index(self):
        from test_investigation import native_fixture, empty_config
        from priority_search import run_trial
        from archive_traffic_study import archive_study
        from trial_evidence import read_archive
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root, budget=1)
            work = root / 'work'
            config = empty_config('snapshot-source')
            result = run_trial(model, work / 'trials', config)
            snapshot = result['diagnostics']['snapshots'][0]
            # Reproduce the historical indexing omission, keeping the recorded
            # monitor binding and the exact immutable snapshot intact.
            del result['output_hashes'][snapshot['file']]
            folder = work / 'trials/snapshot-source'
            (folder / 'result.json').write_text(json.dumps(result))
            manifest = archive_study(work, root / 'archive', {'fixture': model})
            row = json.loads(manifest.read_text())['trials'][0]
            evidence = row['supplementary_snapshot_evidence'][snapshot['file']]
            self.assertEqual(read_archive(manifest.parent, evidence), (folder / snapshot['file']).read_bytes())

    def test_archive_is_self_contained_and_regrades_native_counts(self):
        from test_investigation import native_fixture, empty_config
        from priority_search import run_trial
        from archive_traffic_study import archive_study
        from trial_evidence import load_trial, read_archive
        from timetable import assess_trial
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            work = root / 'work'
            config = empty_config('archived')
            original = run_trial(model, work / 'trials', config)
            failed = work / 'trials/failed-storage-attempt'
            failed.mkdir()
            (failed / 'partial.xml').write_bytes(b'<incomplete-native-output>')
            (failed / 'implementation-controller.py').write_bytes(b'# frozen failed attempt\n')
            manifest = archive_study(work, root / 'archive', {'fixture': model})
            source = load_trial(manifest, config['id'])
            actual = assess_trial(source.buses, source.calls(), source.completed())
            self.assertEqual(actual, original['operational_metrics'])
            self.assertEqual(source.payload('routes.rou.xml'),
                             (work / 'trials/archived/routes.rou.xml').read_bytes())
            incomplete = json.loads(manifest.read_text())['incomplete_attempts'][0]
            self.assertEqual(incomplete['status'], 'no_complete_result')
            self.assertEqual(read_archive(manifest.parent, incomplete['evidence']['partial.xml']),
                             b'<incomplete-native-output>')
            self.assertEqual(read_archive(manifest.parent, incomplete['evidence']['implementation-controller.py']),
                             b'# frozen failed attempt\n')
            corrupted = copy.deepcopy(original)
            corrupted['metrics']['late_checkpoints'] = 999
            (work / 'trials/archived/result.json').write_text(json.dumps(corrupted))
            rejected = root / 'rejected-archive'
            with self.assertRaisesRegex(ValueError, 'timing evaluation differs'):
                archive_study(work, rejected, {'fixture': model})
            self.assertFalse((rejected / 'study.json').exists())

    def test_prefix_replay_preserves_subset_and_controller_bounds(self):
        from unittest.mock import patch
        from test_investigation import native_fixture, empty_config
        from priority_search import run_trial
        from prefix_reproduction import reproduce_prefix
        from native_runner import run_native
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            config = {**empty_config('subset-source'), 'diagnostic_control': None,
                      'diagnostic_all_green': False, 'signal_priority': True,
                      'extension_limit': 0, 'priority_tls': [], 'priority_min_green': 10}
            control = {**empty_config('control'), 'diagnostic_all_green': False,
                       'diagnostic_control': 'existing_signals'}
            run_trial(model, root, control)
            config.update(readiness={'source': str(root / 'control')},
                          hypothesis={'change': 'No selected controllers', 'prediction': 'Preserve timings',
                                      'evidence': 'Same native physical input'})
            run_trial(model, root, config)
            with patch('prefix_reproduction.run_native', wraps=run_native) as native:
                replay = reproduce_prefix(root / 'subset-source', root / 'replay',
                                          trip_id='d1_bus_0', stop_id='d1_B')
            self.assertEqual(native.call_args.args[3]['extension_limit'], 0)
            self.assertEqual(native.call_args.args[3]['tls_filter'], [])
            self.assertEqual(native.call_args.args[3]['minimum_conflicting_green'], 10)
            self.assertTrue(replay['prefix_equivalence']['matched'])

    def test_signal_comparison_reuses_exact_inputs_but_rejects_changed_demand(self):
        from test_investigation import native_fixture, empty_config
        from priority_search import run_trial
        from paired_workload import reuse_workload, INPUTS
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            config = empty_config('paired-source')
            run_trial(model, root, config)
            candidate = {**config, 'id': 'candidate', 'signal_priority': True,
                         'paired_workload': str(root / config['id'])}
            folder = root / 'copied'
            folder.mkdir()
            _, buses, ordinary, *_ = reuse_workload(model, folder, candidate)
            self.assertEqual(len(buses), 2)
            self.assertEqual(ordinary, [])
            for name in INPUTS:
                self.assertEqual((folder / name).read_bytes(), (root / config['id'] / name).read_bytes())
            with self.assertRaisesRegex(ValueError, 'physical/acceptance setting: seed'):
                reuse_workload(model, folder, {**candidate, 'seed': config['seed'] + 1})

    def test_budget_stopped_native_run_cannot_establish_full_day_readiness(self):
        from test_investigation import native_fixture, empty_config
        from priority_search import run_trial
        from model_audit import audit_model
        from run_diagnostics import diagnose_trial
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            config = {**empty_config('budget-control'), 'diagnostic_budget_seconds': .000001}
            result = run_trial(model, root, config)
            self.assertEqual(result['execution_scope']['kind'], 'bounded_diagnostic')
            self.assertFalse(diagnose_trial(root / config['id'])['coverage']['full_service_day'])
            self.assertIn('diagnostic_scope', audit_model(model, root / config['id'])['blockers'])


class StopReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The archive is a public interface, rather than a dependency on .cache.
        from trial_evidence import read_archive
        cls.temporary = tempfile.TemporaryDirectory(prefix='invicta-stop-review-')
        cls.folder = Path(cls.temporary.name)
        archive = ROOT.parents[2] / 'docs/research/701-combatentes-controls-2026-10-30'
        ledger = json.loads((archive / 'controls.json').read_text())
        evidence = ledger['models']['v9-frozen']['evidence']
        cls.model = json.loads(read_archive(archive, evidence['model.json']))
        cls.reference = json.loads(read_archive(archive, evidence['routes.json']))
        network = cls.folder / 'network.xml'
        network.write_bytes(read_archive(archive, evidence['baseline.net.xml']))
        cls.net = sumolib.net.readNet(str(network), withInternal=True, maxcache=0)
        cls.path = ROOT / 'reviews/v9-stop-placement.json'

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_only_the_three_source_bound_approximations_are_accepted(self):
        rows, signature = stop_reviews(self.path, self.model, self.reference, self.net)
        self.assertEqual(set(rows), {'d1_COD', 'd0_BRO1', 'd0_COD4'})
        self.assertEqual(len(signature), 64)
        self.assertEqual(stop_reviews(None, self.model, self.reference, self.net), ({}, None))

    def test_changed_model_cannot_inherit_review(self):
        with self.assertRaisesRegex(ValueError, 'does not bind this model'):
            stop_reviews(self.path, {**self.model, 'network_sha256': '0' * 64}, self.reference, self.net)

    def test_nearby_different_platform_cannot_justify_the_stop(self):
        value = json.loads(self.path.read_text())
        value['stops'][0]['osm_platform'] = '6143667230'  # COD3 is not COD.
        path = self.folder / 'wrong-platform.json'
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'identity does not match'):
            stop_reviews(path, self.model, self.reference, self.net)


class FrozenTrafficStudyTests(unittest.TestCase):
    def test_combined_failure_and_partial_scopes_survive_public_evaluation(self):
        from run_diagnostics import diagnose_trial
        source = ROOT.parents[2] / 'docs/research/701-traffic-stress-2026-10-30/study.json'
        ledger = json.loads(source.read_text())
        self.assertFalse(ledger['qualified'])
        self.assertEqual(len(ledger['trials']), 31)
        self.assertEqual(len(ledger['incomplete_attempts']), 4)
        for ident, late in [('v11-traffic-and-people-010-baseline-s17', 20),
                            ('v11-traffic-and-people-target-two-s17', 23)]:
            report = diagnose_trial(source, ident)
            self.assertTrue(report['coverage']['full_service_day'])
            self.assertEqual(report['metrics']['completed'], 127)
            self.assertEqual(report['coverage']['timing_checks'], 714)
            self.assertEqual(report['operational_metrics']['late_checkpoints'], late)
            self.assertFalse(report['operational_compliance'])
        for ident in ['v11-busy-100-diagnostic-s17', 'v11-people-signals-off-bound-s17']:
            report = diagnose_trial(source, ident)
            self.assertFalse(report['coverage']['full_service_day'])
            self.assertFalse(report['operational_compliance'])


if __name__ == '__main__':
    unittest.main()
