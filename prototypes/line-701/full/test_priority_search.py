"""Public acceptance seam: account for every scheduled working and checkpoint."""
import unittest
from pathlib import Path
from priority_search import assess_trial
from priority_ledger import verify_ledger


class PrioritySearchTests(unittest.TestCase):
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

    def test_published_search_keeps_native_failures_and_all_127_workings(self):
        ledger = verify_ledger(Path(__file__).parent / 'priority-search.json')
        baseline = next(t for t in ledger['trials'] if t['id'] == 'v3-fixed20-s17')
        self.assertEqual(baseline['metrics']['on_time_starts'], 126)
        self.assertEqual(baseline['metrics']['on_time_finishes'], 32)
        self.assertEqual(baseline['metrics']['late_checkpoints'], 320)
        self.assertTrue(all(t['metrics']['planned'] == 127 and t['metrics']['checkpoints'] == 714
                            for t in ledger['trials']))
        self.assertIsNone(ledger['winner'])


if __name__ == '__main__':
    unittest.main()
