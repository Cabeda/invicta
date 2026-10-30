"""Native regression for the observed Alfena two-car junction deadlock.

This fixture diagnoses imported geometry, not full-line or field reliability.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

import libsumo as simulation
import sumo

FIXTURE = Path(__file__).parent / 'diagnostics/alfena-junction'
ACTORS = {'crossing_14_109', 'crossing_14_33'}
BRIDGES = {'1569557889', '-1569557889'}


def junction_movements(network, junctions):
    """Compose movements through the short median roads, retaining lane identity."""
    root = ET.parse(network).getroot()
    roads = {row.get('id'): row for row in root.findall('edge') if not row.get('function')}
    links = {}
    for row in root.findall('connection'):
        if row.get('from') in roads and row.get('to') in roads:
            links.setdefault((row.get('from'), row.get('fromLane')), []).append(
                (row.get('to'), row.get('toLane')))
    movements = set()
    for ident, road in roads.items():
        if road.get('to') not in junctions or ident in BRIDGES:
            continue
        for lane in road.findall('lane'):
            if lane.get('allow') == 'pedestrian':
                continue
            start = (ident, lane.get('index'))
            pending, visited = list(links.get(start, [])), set()
            while pending:
                target = pending.pop()
                if target in visited:
                    continue
                visited.add(target)
                if target[0] in BRIDGES:
                    pending.extend(links.get(target, []))
                else:
                    movements.add((start, target))
    return movements


def run_pair(network, folder, offset=0, actors=ACTORS):
    """Run the actual native movement; assert requested actors were inserted."""
    edges = {edge.get('id') for edge in ET.parse(network).getroot().findall('edge')}
    routes = ET.parse(FIXTURE / 'pair.rou.xml')
    root = routes.getroot()
    events = []
    for vehicle in list(root.findall('vehicle')):
        root.remove(vehicle)
        if vehicle.get('id') not in actors:
            continue
        vehicle.set('depart', str(20 + (offset if vehicle.get('id') == 'crossing_14_33' else 0)))
        route = vehicle.find('route')
        original = route.get('edges').split()
        missing = set(original) - edges
        if not missing.issubset(BRIDGES):
            raise ValueError('The diagnostic changed a road outside the compound junction')
        path = [edge for edge in original if edge in edges]
        if (path[0], path[-1]) != (original[0], original[-1]):
            raise ValueError('The diagnostic changed an actor origin or destination')
        route.set('edges', ' '.join(path))
        events.append(vehicle)
    root.extend(sorted(events, key=lambda row: float(row.get('depart'))))
    folder.mkdir()
    route_file = folder / 'routes.rou.xml'
    routes.write(route_file, encoding='utf-8', xml_declaration=True)
    command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(network),
        '--route-files', str(route_file), '--begin', '0', '--end', '180', '--seed', '17',
        '--time-to-teleport', '-1', '--no-warnings', 'true', '--no-step-log', 'true',
        '--duration-log.disable', 'true', '--xml-validation', 'never',
        '--collision-output', str(folder / 'collisions.xml')]
    departed, arrived, last = set(), set(), {}
    simulation.start(command)
    try:
        while simulation.simulation.getTime() < 180 and simulation.simulation.getMinExpectedNumber() > 0:
            simulation.simulationStep()
            departed.update(simulation.simulation.getDepartedIDList())
            arrived.update(simulation.simulation.getArrivedIDList())
        last = {ident: {'waiting': simulation.vehicle.getWaitingTime(ident),
                       'position': list(simulation.vehicle.getPosition(ident))}
                for ident in simulation.vehicle.getIDList()}
        end = simulation.simulation.getTime()
    finally:
        simulation.close()
    if departed != actors:
        raise AssertionError('Native input omitted or added an actor')
    return {'departed': sorted(departed), 'arrived': sorted(arrived), 'unfinished': last, 'end': end,
            'collisions': len(ET.parse(folder / 'collisions.xml').getroot())}


class JunctionGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='invicta-alfena-')
        cls.root = Path(cls.temporary.name)
        cls.joined = cls.root / 'joined.net.xml'
        cls.roundtrip = cls.root / 'roundtrip.net.xml'
        subprocess.run([str(Path(sumo.SUMO_HOME) / 'bin/netconvert'),
            '--sumo-net-file', str(FIXTURE / 'split.net.xml'),
            '--output-file', str(cls.roundtrip)], check=True, capture_output=True)
        subprocess.run([str(Path(sumo.SUMO_HOME) / 'bin/netconvert'),
            '--sumo-net-file', str(FIXTURE / 'split.net.xml'),
            '--node-files', str(FIXTURE / 'join.nod.xml'),
            '--output-file', str(cls.joined)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_original_pair_reproduces_queue_at_recorded_positions(self):
        expected = {'crossing_14_109': [6683.74, 7684.445],
                    'crossing_14_33': [6686.812087912088, 7684.81]}
        for offset in [-7, 0, 4]:
            with self.subTest(offset=offset):
                result = run_pair(FIXTURE / 'split.net.xml', self.root / f'original-{offset}', offset)
                self.assertEqual(result['arrived'], [])
                self.assertEqual(set(result['unfinished']), ACTORS)
                for ident, data in result['unfinished'].items():
                    self.assertGreater(data['waiting'], 120)
                    for actual, recorded in zip(data['position'], expected[ident]):
                        self.assertAlmostEqual(actual, recorded, delta=.01)
                self.assertEqual(result['collisions'], 0)

    def test_each_actor_completes_alone_on_original_geometry(self):
        for ident in sorted(ACTORS):
            with self.subTest(actor=ident):
                result = run_pair(FIXTURE / 'split.net.xml', self.root / ident, actors={ident})
                self.assertEqual(result['arrived'], [ident])
                self.assertEqual(result['unfinished'], {})

    def test_join_preserves_all_eight_external_vehicle_movements(self):
        before = junction_movements(FIXTURE / 'split.net.xml', {'14297876949', '14297876959'})
        self.assertEqual(len(before), 8)
        self.assertEqual(junction_movements(self.joined, {'alfena_compound'}), before)

    def test_reprocessing_without_the_join_does_not_clear_the_pair(self):
        for offset in [0, 4]:
            with self.subTest(offset=offset):
                result = run_pair(self.roundtrip, self.root / f'roundtrip-{offset}', offset)
                self.assertEqual(result['arrived'], [])
                self.assertEqual(set(result['unfinished']), ACTORS)

    def test_compound_junction_clears_both_actors_across_departure_offsets(self):
        for offset in range(-10, 11):
            with self.subTest(offset=offset):
                result = run_pair(self.joined, self.root / f'joined-{offset}', offset)
                self.assertEqual(result['arrived'], sorted(ACTORS))
                self.assertEqual(result['unfinished'], {})
                self.assertEqual(result['collisions'], 0)


if __name__ == '__main__':
    unittest.main()
