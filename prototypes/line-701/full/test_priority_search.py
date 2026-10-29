"""Public acceptance seam: account for every scheduled working and checkpoint."""
import unittest
from pathlib import Path
import tempfile
import json
import gzip
import sumolib
from prepare import map_direction, PILOT
from priority_search import assess_trial, run_trial, ExistingTrialError
from priority_ledger import verify_ledger


class PrioritySearchTests(unittest.TestCase):
    def test_crossing_fragments_do_not_force_alfena_onto_a_side_street(self):
        root = Path(__file__).parent
        archive = root / 'priority-evidence/v3-moderate-baseline-mapped-s17/network.net.xml.gz'
        facts = json.loads((PILOT / 'data/official-extension/full-line-service-facts.json').read_text())
        shape = json.loads((PILOT / 'data/official/inbound_shape.json').read_text())['coordinates']
        with tempfile.TemporaryDirectory() as temporary:
            network = Path(temporary) / 'network.net.xml'
            network.write_bytes(gzip.decompress(archive.read_bytes()))
            direction = map_direction(sumolib.net.readNet(str(network), withInternal=True, maxcache=0), facts, shape)
        stop = next(s for s in direction['stops'] if s['stop_id'] == 'ALF')
        # The official shape and stop are on São Vicente. The crossing import
        # split this road into short edges; Rua Coroa is an erroneous detour.
        self.assertEqual(stop['street'], 'Rua de São Vicente')
        self.assertLess(stop['snap_distance'], 15)
        self.assertTrue('169771420' not in direction['path'], 'Unexpected Rua da Várzea spur')

    def test_failed_native_trial_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            trial = output / 'failed'
            trial.mkdir()
            (trial / 'error.json').write_text('original failure')
            with self.assertRaises(ExistingTrialError):
                run_trial(output / 'unused-model', output, {'id': 'failed', 'traffic': 'none'})
            self.assertEqual((trial / 'error.json').read_text(), 'original failure')

    def test_archive_cannot_replace_the_original_execution_output_binding(self):
        root = Path(__file__).parent
        ledger = json.loads((root / 'priority-search.json').read_text())
        trial = next(t for t in ledger['trials'] if t.get('output_hashes'))
        trial['output_hashes']['trips.xml'] = '0'*64
        ledger['trials'] = [trial]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'priority-evidence').symlink_to((root / 'priority-evidence').resolve(), target_is_directory=True)
            (directory / 'ledger.json').write_text(json.dumps(ledger))
            with self.assertRaisesRegex(ValueError, 'original execution binding'):
                verify_ledger(directory / 'ledger.json')
    def test_missing_trip_cannot_disappear_from_the_goal(self):
        scheduled = [{'id': 'a', 'stops': [
            {'native_stop_id': 'origin', 'scheduled': 100, 'designated_timing_point': True},
            {'native_stop_id': 'destination', 'scheduled': 200, 'designated_timing_point': True}]},
            {'id': 'b', 'stops': [
            {'native_stop_id': 'origin', 'scheduled': 300, 'designated_timing_point': True},
            {'native_stop_id': 'destination', 'scheduled': 400, 'designated_timing_point': True}]}]
        calls = [{'id': 'a', 'busStop': 'origin', 'started': '90', 'ended': '100'},
                 {'id': 'a', 'busStop': 'destination', 'started': '190', 'ended': '200'}]
        result = assess_trial(scheduled, calls, {'a'})
        self.assertEqual(result['on_time_starts'], 1)
        self.assertEqual(result['on_time_finishes'], 1)
        self.assertEqual(result['missing_checkpoints'], 2)
        self.assertEqual(result['planned'], 2)
        self.assertFalse(result['passes'])

    def test_early_intermediate_departure_fails_even_with_punctual_endpoints(self):
        scheduled = [{'id': 'a', 'stops': [
            {'native_stop_id': 'origin', 'scheduled': 100, 'designated_timing_point': True},
            {'native_stop_id': 'checkpoint', 'scheduled': 150, 'designated_timing_point': True},
            {'native_stop_id': 'destination', 'scheduled': 200, 'designated_timing_point': True}]}]
        calls = [{'id': 'a', 'busStop': 'origin', 'started': '90', 'ended': '100'},
                 {'id': 'a', 'busStop': 'checkpoint', 'started': '140', 'ended': '149'},
                 {'id': 'a', 'busStop': 'destination', 'started': '190', 'ended': '200'}]
        result = assess_trial(scheduled, calls, {'a'})
        self.assertEqual(result['early_departures'], 1)
        self.assertFalse(result['passes'])

    def test_duplicate_native_calls_are_rejected(self):
        call = {'id': 'a', 'busStop': 'origin', 'started': '90', 'ended': '100'}
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            assess_trial([], [call, call], set())

    def test_unfinished_trip_retains_its_observed_punctual_start(self):
        schedule = [{'id': 'a', 'stops': [
            {'native_stop_id': 'origin', 'scheduled': 100, 'designated_timing_point': True},
            {'native_stop_id': 'destination', 'scheduled': 200, 'designated_timing_point': True}]}]
        result = assess_trial(schedule, [{'id': 'a', 'busStop': 'origin', 'started': '90', 'ended': '100'}], set())
        self.assertEqual(result['on_time_starts'], 1)
        self.assertEqual(result['missing_checkpoints'], 1)
        self.assertFalse(result['passes'])

    def test_published_search_keeps_native_failures_and_all_127_workings(self):
        ledger = verify_ledger(Path(__file__).parent / 'priority-search.json')
        baseline = next(t for t in ledger['trials'] if t['id'] == 'v3-fixed20-s17')
        self.assertEqual(baseline['metrics']['on_time_starts'], 126)
        self.assertEqual(baseline['metrics']['on_time_finishes'], 32)
        self.assertEqual(baseline['metrics']['late_checkpoints'], 320)
        self.assertTrue(all(t['metrics']['planned'] == 127 and t['metrics']['checkpoints'] == 714
                            for t in ledger['trials']))
        self.assertIsNone(ledger['winner'])

    def test_matched_traffic_pair_retains_every_request_and_pedestrian_access(self):
        ledger = verify_ledger(Path(__file__).parent / 'priority-search.json')
        pair = [next(t for t in ledger['trials'] if t['id'] == ident) for ident in
                ['v3-moderate-baseline-mapped-s17', 'v3-moderate-priority-mapped-s17']]
        for trial in pair:
            self.assertEqual(trial['vehicle_requests'], 26035)
            self.assertEqual(trial['unroutable_requests'], 0)
            self.assertFalse(trial['eligible_for_comparison'])
            self.assertIn('Alfena', trial['invalid_reasons'][0])
        self.assertEqual(pair[0]['demand_mapping']['mapped_requests_sha256'],
                         pair[1]['demand_mapping']['mapped_requests_sha256'])
        invalid = next(t for t in ledger['trials'] if t['id'] == 'priority-package-moderate-s17')
        self.assertFalse(invalid['eligible_for_comparison'])
        self.assertEqual(len(invalid['invalid_reasons']), 2)


if __name__ == '__main__':
    unittest.main()
