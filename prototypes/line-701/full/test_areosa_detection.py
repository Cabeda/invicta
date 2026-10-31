"""Native regression: an Areosa internal vehicle loses its detector request."""
import copy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import libsumo as simulation
import sumo
from areosa_detection import write_program, CONTROLLER

FIXTURE = Path(__file__).parent / 'diagnostics/areosa-junction'
ACTORS = {'background_7_1259', 'background_7_126', 'bicycle_7_10'}


def run_actors(folder, additional=None, omit=None, offset=0):
    folder.mkdir()
    routes = ET.parse(FIXTURE / 'actors.rou.xml')
    for vehicle in list(routes.getroot().findall('vehicle')):
        if vehicle.get('id') == omit:
            routes.getroot().remove(vehicle)
        elif vehicle.get('id') == 'bicycle_7_10':
            vehicle.set('depart', str(40 + offset))
    routes.write(folder / 'routes.xml')
    command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(FIXTURE / 'source.net.xml'),
        '--route-files', str(folder / 'routes.xml'), '--begin', '0', '--end', '900', '--seed', '17',
        '--time-to-teleport', '-1', '--no-warnings', 'true', '--no-step-log', 'true',
        '--collision.check-junctions', 'true', '--collision-output', str(folder / 'collisions.xml'),
        '--duration-log.disable', 'true', '--xml-validation', 'never']
    if additional:
        command += ['--additional-files', str(additional)]
    departed, arrived = set(), set()
    simulation.start(command)
    try:
        while simulation.simulation.getTime() < 900 and simulation.simulation.getMinExpectedNumber() > 0:
            simulation.simulationStep()
            departed.update(simulation.simulation.getDepartedIDList())
            arrived.update(simulation.simulation.getArrivedIDList())
        remaining = {actor: {'waiting': simulation.vehicle.getWaitingTime(actor),
                            'lane': simulation.vehicle.getLaneID(actor)}
                     for actor in simulation.vehicle.getIDList()}
    finally:
        simulation.close()
    if departed != ACTORS - {omit}:
        raise AssertionError('Native diagnostic omitted or added an actor')
    return arrived, remaining, len(ET.parse(folder / 'collisions.xml').getroot())


class AreosaDetectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='invicta-areosa-')
        self.root = Path(self.temporary.name)
        self.corrected = self.root / 'detection.add.xml'
        write_program(FIXTURE / 'source.net.xml', self.corrected)

    def tearDown(self):
        self.temporary.cleanup()

    def test_original_three_actor_case_loses_an_internal_vehicle(self):
        arrived, remaining, collisions = run_actors(self.root / 'original')
        self.assertEqual(arrived, ACTORS - {'background_7_126'})
        self.assertEqual(set(remaining), {'background_7_126'})
        self.assertEqual(remaining['background_7_126']['lane'], ':1838444495_0_2')
        self.assertGreater(remaining['background_7_126']['waiting'], 700)
        self.assertEqual(collisions, 0)

    def test_removing_any_actor_clears_original_network(self):
        for actor in sorted(ACTORS):
            with self.subTest(omit=actor):
                arrived, remaining, collisions = run_actors(self.root / actor, omit=actor)
                self.assertEqual(arrived, ACTORS - {actor})
                self.assertEqual(remaining, {})
                self.assertEqual(collisions, 0)

    def test_correction_preserves_every_phase_and_only_changes_detection(self):
        original = ET.parse(FIXTURE / 'source.net.xml').getroot().find(f"tlLogic[@id='{CONTROLLER}']")
        corrected = ET.parse(self.corrected).getroot().find('tlLogic')
        corrected = copy.deepcopy(corrected)
        corrected.set('programID', original.get('programID'))
        parameter = corrected.find("param[@key='detector-gap']")
        self.assertEqual(parameter.attrib, {'key': 'detector-gap', 'value': '0'})
        corrected.remove(parameter)
        self.assertEqual(ET.tostring(corrected).strip(), ET.tostring(original).strip())

    def test_detector_correction_clears_every_requested_actor_across_offsets(self):
        for offset in range(-10, 11):
            with self.subTest(offset=offset):
                arrived, remaining, collisions = run_actors(self.root / f'corrected-{offset}',
                                                           self.corrected, offset=offset)
                self.assertEqual(arrived, ACTORS)
                self.assertEqual(remaining, {})
                self.assertEqual(collisions, 0)


if __name__ == '__main__':
    unittest.main()
