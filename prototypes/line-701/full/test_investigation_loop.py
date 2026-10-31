"""The study loop observes the same public evidence interface as its caller."""
import json
from pathlib import Path
import tempfile
import unittest

from investigation_loop import build_casebook

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'docs/research/701-traffic-stress-2026-10-30/study.json'


class InvestigationLoopTests(unittest.TestCase):
    def test_archive_retains_verified_local_failures_and_rejects_changed_frames(self):
        from archive_traffic_study import archive_study
        from native_case import run_case
        from test_investigation import native_fixture
        from trial_evidence import read_archive
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            work = root / 'work'
            (work / 'trials').mkdir(parents=True)
            case = root / 'local'
            run_case(fixture / 'source.net.xml', fixture / 'regional-five.rou.xml', case)
            manifest = archive_study(work, root / 'archive', {'fixture':model}, local_cases={'stranded':case})
            row = json.loads(manifest.read_text())['local_cases']['stranded']
            self.assertFalse(row['qualified'])
            self.assertEqual(read_archive(manifest.parent, row['evidence']['frames.json.gz']),
                             (case / 'frames.json.gz').read_bytes())
            (case / 'frames.json.gz').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Changed local native evidence'):
                archive_study(work, root / 'rejected', {'fixture':model}, local_cases={'stranded':case})

    def test_budget_stop_without_frames_is_journaled_without_a_visual_claim(self):
        from study_session import start_session, run_local_step, session_status
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / 'session'
            start_session(work, SOURCE, line_id='701', trial_id='v11-traffic-and-people-010-baseline-s17')
            proposal = {'id':'bounded-local', 'network':str(fixture / 'source.net.xml'),
                'routes':str(fixture / 'regional-five.rou.xml'), 'wall_seconds':1e-9,
                'hypothesis':{'change':'Explicit exhausted computation budget', 'prediction':'No physics step fits',
                              'evidence':'Positive budget shorter than native initialisation'}}
            event = run_local_step(work, proposal)
            self.assertEqual(event['stop_reason'], 'native_wall_budget')
            self.assertFalse(event['local_case_clears'])
            self.assertIsNone(event['view'])
            self.assertEqual(event['view_status'], 'no_recorded_actor_positions')
            self.assertEqual(session_status(work)['events'], 1)

    def test_local_reproducer_rejects_unaccounted_transportable_flows(self):
        from native_case import run_case
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            routes = Path(temporary) / 'hidden.rou.xml'
            routes.write_text('<routes><vehicle id="v" depart="0"><route edges="unused"/></vehicle>'
                              '<personFlow id="unaccounted" begin="0" end="100" period="1"/></routes>')
            with self.assertRaisesRegex(ValueError, 'no implicit demand'):
                run_case(fixture / 'source.net.xml', routes, Path(temporary) / 'case')

    def test_topology_contraction_preserves_short_working_canonical_stop_indices(self):
        from route_topology import contract_reference
        import copy
        stop = {'native_stop_id':'D', 'edge':'D', 'lane':'D_0', 'path_index':3,
                'scheduled':100, 'point':[10,20]}
        reference = {'network_sha256':'old', 'directions':{'inbound':{
            'path':['A','B','C','D','E'], 'stops':[stop],
            'trips':[{'id':'short', 'path':['D','E'], 'stops':[copy.deepcopy(stop)]}]}}}
        original = copy.deepcopy(reference)
        updated = contract_reference(reference, {'B'}, network_sha256='new')
        self.assertEqual(reference, original)
        direction = updated['directions']['inbound']
        self.assertEqual(direction['path'], ['A','C','D','E'])
        self.assertEqual(direction['stops'][0]['path_index'], 2)
        self.assertEqual(direction['trips'][0]['stops'][0]['path_index'], 2)
        self.assertEqual(direction['trips'][0]['path'], ['D','E'])
        self.assertEqual(direction['trips'][0]['stops'][0]['scheduled'], 100)
        with self.assertRaisesRegex(ValueError, 'served stop'):
            contract_reference(reference, {'D'}, network_sha256='invalid')

    def test_junction_scope_rejects_external_and_local_permission_drift(self):
        from junction_scope import audit_scope
        from areosa_compound import JOIN, FRINGE, CONTROLLERS
        import xml.etree.ElementTree as ET
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction/compound-collision.net.xml'
        scope = {'nodes':JOIN | FRINGE | {'areosa_compound'}, 'controllers':CONTROLLERS}
        self.assertTrue(audit_scope(fixture, fixture, **scope)['passes'])
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'candidate.xml'
            tree = ET.parse(fixture)
            local = tree.getroot().find("edge[@id='743539878#7']/lane[@index='1']")
            local.set('allow', 'bus')
            tree.write(target)
            result = audit_scope(fixture, target, **scope)
            self.assertFalse(result['passes'])
            self.assertIn('743539878#7', result['changed_normal_lane_semantics'])
            tree = ET.parse(fixture)
            remote = next(e for e in tree.getroot().findall('edge')
                          if not e.get('function') and e.get('from') not in scope['nodes']
                          and e.get('to') not in scope['nodes'])
            remote.find('lane').set('speed', '30')
            tree.write(target)
            result = audit_scope(fixture, target, **scope)
            self.assertFalse(result['passes'])
            self.assertTrue(result['outside_scope_changes'])

    def test_casebook_prioritises_native_collisions_over_punctuality(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = build_casebook(SOURCE, Path(temporary) / 'casebook',
                trial_id='ramp-busy-030-baseline-s17', line_id='701')
            self.assertEqual(len(report['collision_events']), 1)
            self.assertEqual(report['next_case']['kind'], 'native_collision')
            self.assertFalse(report['qualified'])

    def test_full_trial_step_reuses_native_work_and_regrades_all_actors(self):
        from study_session import start_session, run_service_step, session_status
        from test_investigation import native_fixture, empty_config
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = native_fixture(root)
            work = root / 'session'
            start_session(work, SOURCE, line_id='future-line-profile', trial_id='v11-traffic-and-people-010-baseline-s17')
            config = {**empty_config('full-day'), 'diagnostic_all_green': False,
                'diagnostic_control': 'existing_signals', 'operational_lateness_seconds': 60}
            proposal = {'id': 'service-control', 'model': str(model), 'config': config,
                'hypothesis': {'change': 'Unchanged empty reference', 'prediction': 'Both synthetic services comply',
                               'evidence': 'Native bidirectional fixture with a feasible timetable'}}
            first = run_service_step(work, proposal)
            self.assertFalse(first['reused'])
            self.assertTrue(first['study_case_passes'])
            self.assertEqual(first['requested_vehicles'], 2)
            self.assertEqual(first['completed_vehicles'], 2)
            self.assertTrue(first['gates']['full_reference_day'])
            self.assertFalse(first['qualified'])
            # An empty prerequisite cannot erase the unresolved combined
            # passenger/traffic case with which this session started.
            self.assertEqual(session_status(work)['next_case']['kind'], 'ordinary_model_stall')
            second = run_service_step(work, {**proposal, 'id': 'identical-control'})
            self.assertTrue(second['reused'])
            self.assertEqual(first['trial'], second['trial'])
            self.assertEqual(session_status(work)['native_executions'], 1)
            # Simulate interruption after the journal fsync and before state
            # promotion. Recovery must not repeat native physics.
            state_path = work / 'session.json'
            stale = json.loads(state_path.read_text())
            stale.update(events=1, runs=stale['runs'][:1])
            state_path.write_text(json.dumps(stale))
            self.assertEqual(session_status(work)['events'], 2)
            self.assertEqual(session_status(work)['native_executions'], 1)
            casebook = json.loads((work / first['casebook'] / 'casebook.json').read_text())
            self.assertEqual(casebook['coverage']['scheduled_trips'], 2)
            result = work / first['trial'] / 'result.json'
            result.write_text(result.read_text() + ' ')
            with self.assertRaisesRegex(ValueError, 'metadata changed'):
                run_service_step(work, {**proposal, 'id': 'changed-evidence'})

    def test_local_case_rejects_unsorted_departures_before_native_loading(self):
        from native_case import run_case
        import xml.etree.ElementTree as ET
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            tree = ET.parse(fixture / 'regional-five.rou.xml')
            vehicles = tree.getroot().findall('vehicle')
            vehicles[-1].set('depart', '0')
            tree.write(folder / 'unsorted.rou.xml')
            with self.assertRaisesRegex(ValueError, 'sorted by departure'):
                run_case(fixture / 'source.net.xml', folder / 'unsorted.rou.xml', folder / 'case')
            self.assertFalse((folder / 'case').exists())

    def test_session_journals_failed_native_steps_and_can_continue(self):
        from study_session import start_session, run_local_step, session_status
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / 'session'
            start_session(work, SOURCE, line_id='701', trial_id='v11-traffic-and-people-010-baseline-s17')
            broken = Path(temporary) / 'broken.rou.xml'
            broken.write_text('<routes><vehicle id="broken" depart="0"><route edges="absent"/></vehicle></routes>')
            proposal = {'id': 'bad-route', 'network': str(fixture / 'source.net.xml'), 'routes': str(broken),
                'hypothesis': {'change': 'Invalid route control', 'prediction': 'Native start rejects this route',
                               'evidence': 'Road id absent from the supplied network'}}
            with self.assertRaises(Exception):
                run_local_step(work, proposal)
            state = session_status(work)
            self.assertEqual(state['events'], 1)
            self.assertEqual(state['runs'][0]['status'], 'failed')
            self.assertFalse(state['runs'][0]['qualified'])
            self.assertTrue((work / 'cases/bad-route/error.json').exists())
            proposal.update(id='valid-control', routes=str(fixture / 'regional-five.rou.xml'))
            event = run_local_step(work, proposal)
            self.assertEqual(event['status'], 'recorded')
            self.assertEqual(session_status(work)['events'], 2)

    def test_protected_turn_catches_the_new_compound_junction_collision(self):
        from native_case import run_case
        from protected_turn import write_program
        import xml.etree.ElementTree as ET
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            network = fixture / 'compound-collision.net.xml'
            routes = ET.parse(fixture / 'collision-pair.rou.xml')
            vehicles = routes.getroot().findall('vehicle')
            red = run_case(network, fixture / 'collision-pair.rou.xml', out / 'red', end_seconds=600)
            self.assertEqual(len(red['departed']), 2)
            self.assertGreater(red['collision_records'], 0)
            for removed in vehicles:
                control = ET.parse(fixture / 'collision-pair.rou.xml')
                control.getroot().remove(next(v for v in control.getroot().findall('vehicle') if v.get('id') == removed.get('id')))
                control.write(out / 'control.rou.xml')
                single = run_case(network, out / 'control.rou.xml', out / ('without-' + removed.get('id')), end_seconds=600)
                self.assertTrue(single['all_requested_completed'])
                self.assertEqual(single['collision_records'], 0)
            report = write_program(network, out / 'protected.add.xml')
            self.assertEqual(report['protected_link'], 3)
            self.assertFalse(report['field_validated'])
            for offset in range(-20, 21):
                routes = ET.parse(fixture / 'collision-pair.rou.xml')
                root = routes.getroot()
                root.find("vehicle[@id='d0_bus_7']").set('depart', str(40 + offset))
                root[:] = list(root.findall('vType')) + sorted(root.findall('vehicle'), key=lambda v:float(v.get('depart')))
                routes.write(out / 'offset.rou.xml')
                green = run_case(network, out / 'offset.rou.xml', out / f'offset-{offset}',
                                 additional=out / 'protected.add.xml', end_seconds=600)
                self.assertTrue(green['all_requested_completed'])
                self.assertEqual(green['collision_records'], 0)

    def test_session_reuses_verified_unchanged_cases_and_keeps_failures(self):
        from study_session import start_session, run_local_step, session_status
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / 'line-session'
            start_session(work, SOURCE, line_id='701', trial_id='v11-traffic-and-people-010-baseline-s17')
            proposal = {'id': 'regional-five', 'network': str(fixture / 'source.net.xml'),
                        'routes': str(fixture / 'regional-five.rou.xml'), 'end_seconds': 900,
                        'hypothesis': {'change': 'Unchanged local control', 'prediction': 'Resident remains stranded',
                                       'evidence': 'Reduced actors from the regional queue'}}
            first = run_local_step(work, proposal)
            second = run_local_step(work, proposal)
            self.assertFalse(first['reused'])
            self.assertTrue(second['reused'])
            self.assertEqual(first['case'], second['case'])
            self.assertFalse(first['qualified'])
            status = session_status(work)
            self.assertEqual(status['line_id'], '701')
            self.assertEqual(status['native_executions'], 1)
            self.assertEqual(status['reused_executions'], 1)
            self.assertTrue((work / first['case'] / 'frames.json.gz').exists())
            metadata = work / first['case'] / 'case.json'
            corrupted = json.loads(metadata.read_text())
            corrupted['all_requested_completed'] = True
            metadata.write_text(json.dumps(corrupted))
            with self.assertRaisesRegex(ValueError, 'case metadata changed'):
                run_local_step(work, proposal)
    def test_local_case_records_the_regional_failure_and_requested_actors(self):
        from native_case import run_case
        from case_view import export_case_view
        fixture = Path(__file__).parent / 'diagnostics/areosa-junction'
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'native-case'
            report = run_case(fixture / 'source.net.xml', fixture / 'regional-five.rou.xml', folder,
                              end_seconds=900)
            self.assertFalse(report['all_requested_completed'])
            self.assertEqual(len(report['requested_actors']), 5)
            self.assertEqual(set(report['departed']), set(report['requested_actors']))
            self.assertIn('resident_7_7', {v['id'] for v in report['unfinished']})
            self.assertEqual(report['collision_records'], 0)
            self.assertFalse(report['qualified'])
            self.assertEqual(json.loads((folder / 'case.json').read_text()), report)
            view = export_case_view(folder)
            import hashlib
            self.assertEqual(view['source_case_sha256'], hashlib.sha256((folder / 'case.json').read_bytes()).hexdigest())
            self.assertFalse(view['qualified'])
            self.assertEqual(view['requested_actors'], report['requested_actors'])
            self.assertTrue((folder / 'index.html').exists())
            self.assertTrue((folder / 'scene.json').exists())
    def test_saved_ordinary_actor_is_inspectable_without_advancing_the_run(self):
        from snapshot_inspection import inspect_snapshot
        report = inspect_snapshot(SOURCE, trial_id='v11-traffic-and-people-010-baseline-s17',
                                  actor_id='resident_7_7')
        self.assertEqual(report['simulation_steps'], 0)
        self.assertEqual(report['active_bus_count'], 0)
        self.assertEqual(report['requested_actor'], 'resident_7_7')
        vehicle = report['contexts'][0]['vehicles'][0]
        self.assertEqual(vehicle['lane'], '1304910030_1')
        self.assertGreater(vehicle['waiting_seconds'], 72000)
        self.assertEqual(len(vehicle['point']), 2)
        self.assertTrue(vehicle['best_lanes'])
        self.assertGreater(vehicle['length_metres'], 0)

    def test_dossier_separates_added_delay_from_the_late_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'casebook'
            report = build_casebook(SOURCE, output, trial_id='v11-traffic-and-people-010-baseline-s17',
                                    line_id='701')
            self.assertEqual(report['line_id'], '701')
            self.assertFalse(report['qualified'])
            self.assertEqual(report['coverage']['scheduled_trips'], 127)
            self.assertEqual(report['operational_metrics']['late_checkpoints'], 20)
            leg = next(x for x in report['intervals'] if x['trip'] == 'd0_bus_59'
                       and x['to_stop']['native_stop_id'] == 'd0_COD4')
            self.assertEqual(leg['from_stop']['native_stop_id'], 'd0_ERM4')
            self.assertEqual(leg['scheduled_seconds'], 720)
            self.assertGreater(leg['added_delay_seconds'], 60)
            self.assertEqual(leg['inherited_delay_seconds'], 0)
            self.assertGreater(leg['recorded_stop_seconds'], 0)
            self.assertGreater(leg['boarded_passengers'], 0)
            self.assertEqual(leg['cause'], 'unclassified')
            self.assertEqual(json.loads((output / 'casebook.json').read_text()), report)
            self.assertTrue((output / 'README.md').exists())
            with self.assertRaises(FileExistsError):
                build_casebook(SOURCE, output, trial_id='v11-traffic-and-people-010-baseline-s17', line_id='701')

    def test_ordinary_stalls_and_trace_waits_are_model_cases_not_proven_causes(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = build_casebook(SOURCE, Path(temporary) / 'casebook',
                trial_id='v11-traffic-and-people-010-baseline-s17', line_id='future-line-profile')
            self.assertEqual(report['line_id'], 'future-line-profile')
            self.assertGreaterEqual(len(report['ordinary_stalls']), 9)
            self.assertTrue(all(x['recorded_waiting_seconds'] > 3600 for x in report['ordinary_stalls']))
            self.assertEqual(report['next_case']['kind'], 'ordinary_model_stall')
            late = next(x for x in report['intervals'] if x['trip'] == 'd1_bus_62'
                        and x['to_stop']['native_stop_id'] == 'd1_MPL4')
            self.assertTrue(late['trace_observations'])
            self.assertTrue(all(x['trip'] == late['trip'] for x in late['trace_observations']))
            self.assertTrue(all(late['native_begin'] <= x['time'] <= late['native_end']
                                for x in late['trace_observations']))
            self.assertNotEqual(report['next_case']['cause'], 'traffic_congestion')


if __name__ == '__main__':
    unittest.main()
