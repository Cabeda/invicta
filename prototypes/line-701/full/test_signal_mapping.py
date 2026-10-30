"""Native regression for a bus stopping twice inside Combatentes without foes."""
from pathlib import Path
import copy
import gzip
import hashlib
import itertools
import json
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

import libsumo as simulation
import sumo
import sumolib

from signal_mapping import (write_boundary_controls, verify_correction_scope, verify_import_source,
                            topology_fingerprint, inherited_junction_correction)

FIXTURE = Path(__file__).parent / 'diagnostics/combatentes-junction'
APPROACH = {'d1': '-1172588827#2', 'd0': '482331424#8'}
EXIT = {'d1': '-27292882#9', 'd0': '1172588827#1'}


def run_buses(network, folder, actors=('d1', 'd0'), offset=0):
    """Measure waiting after admission, until the entire 12 m bus clears."""
    folder.mkdir()
    source = ET.parse(FIXTURE / 'buses.rou.xml').getroot()
    root = ET.Element('routes')
    root.append(copy.deepcopy(source.find('vType')))
    vehicles, paths = [], {}
    for row in source.findall('vehicle'):
        ident = row.get('id')
        if ident not in actors:
            continue
        row.set('depart', str(20 + (offset if ident == 'd0' else 0)))
        vehicles.append(row)
        paths[ident] = row.find('route').get('edges').split()
    root.extend(sorted(vehicles, key=lambda row: float(row.get('depart'))))
    routes = folder / 'routes.xml'
    ET.ElementTree(root).write(routes, encoding='utf-8', xml_declaration=True)
    collisions = folder / 'collisions.xml'
    command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(network),
        '--route-files', str(routes), '--begin', '0', '--end', '600', '--seed', '17',
        '--no-step-log', 'true', '--duration-log.disable', 'true',
        '--xml-validation', 'never', '--no-warnings', 'true', '--time-to-teleport', '-1',
        '--collision.action', 'warn', '--collision.check-junctions', 'true',
        '--collision-output', str(collisions)]
    departed, arrived, entries, cleared, waits = set(), set(), {}, {}, {}
    simulation.start(command)
    try:
        while simulation.simulation.getTime() < 600 and simulation.simulation.getMinExpectedNumber():
            simulation.simulationStep()
            now = simulation.simulation.getTime()
            departed.update(simulation.simulation.getDepartedIDList())
            for ident in simulation.simulation.getArrivedIDList():
                arrived.add(ident)
                if ident in entries:
                    cleared.setdefault(ident, now)
            for ident in simulation.vehicle.getIDList():
                road = simulation.vehicle.getRoadID(ident)
                index = simulation.vehicle.getRouteIndex(ident)
                start = paths[ident].index(APPROACH[ident])
                end = paths[ident].index(EXIT[ident])
                # A short normal road can be crossed within one simulation step.
                if index > start or index == start and road.startswith(':'):
                    entries.setdefault(ident, now)
                if ident in entries and (index > end or road == EXIT[ident]
                        and simulation.vehicle.getLanePosition(ident) >= 12):
                    cleared.setdefault(ident, now)
                if ident in entries and ident not in cleared:
                    waits[ident] = max(waits.get(ident, 0), simulation.vehicle.getWaitingTime(ident))
    finally:
        simulation.close()
    if departed != set(actors) or arrived != set(actors) or set(entries) != set(actors) or set(cleared) != set(actors):
        raise AssertionError('Probe did not insert, admit and clear every requested bus')
    return {'post_entry_wait': waits, 'entries': entries, 'cleared': cleared,
            'collisions': len(ET.parse(collisions).getroot())}


def run_conflicts(network, folder, paths, offset=0, walkers=False):
    """Exercise retained movements; never count omitted actors as a success."""
    folder.mkdir()
    root = ET.Element('routes')
    root.append(ET.parse(FIXTURE / 'buses.rou.xml').getroot().find('vType'))
    actors = []
    expected = {'bus' + str(index) for index in range(len(paths))}
    for index, path in enumerate(paths):
        row = ET.Element('vehicle', id='bus' + str(index), type='bus',
                         depart=str(20 + offset * index), departLane='best')
        ET.SubElement(row, 'route', edges=' '.join(path))
        actors.append(row)
    people = {'ped' + str(index) for index in range(8)} if walkers else set()
    for index in range(len(people)):
        row = ET.Element('person', id='ped' + str(index), depart=str(20 + index * 3))
        ET.SubElement(row, 'walk', **{'from': '1352537841', 'to': '1352537837#1'})
        actors.append(row)
    # SUMO requires chronological ordering across vehicles AND pedestrians.
    root.extend(sorted(actors, key=lambda row: float(row.get('depart'))))
    ET.ElementTree(root).write(folder / 'routes.xml', encoding='utf-8', xml_declaration=True)
    command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(network),
        '--route-files', str(folder / 'routes.xml'), '--begin', '0', '--end', '600', '--seed', '17',
        '--no-step-log', 'true', '--duration-log.disable', 'true', '--no-warnings', 'true',
        '--xml-validation', 'never', '--time-to-teleport', '-1',
        '--collision.action', 'warn', '--collision.check-junctions', 'true',
        '--collision-output', str(folder / 'collisions.xml')]
    departed, arrived, walking, walked = set(), set(), set(), set()
    simulation.start(command)
    try:
        while simulation.simulation.getTime() < 600 and simulation.simulation.getMinExpectedNumber():
            simulation.simulationStep()
            departed.update(simulation.simulation.getDepartedIDList())
            arrived.update(simulation.simulation.getArrivedIDList())
            walking.update(simulation.simulation.getDepartedPersonIDList())
            walked.update(simulation.simulation.getArrivedPersonIDList())
    finally:
        simulation.close()
    if departed != expected or arrived != expected or walking != people or walked != people:
        raise AssertionError('Conflict probe omitted or failed to complete a requested actor')
    return len(ET.parse(folder / 'collisions.xml').getroot())


class SignalMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='invicta-combatentes-')
        cls.root = Path(cls.temporary.name)
        cls.source = cls.root / 'source.net.xml'
        cls.source.write_bytes(gzip.decompress((FIXTURE / 'split.net.xml.gz').read_bytes()))
        cls.patch = cls.root / 'boundary.con.xml'
        cls.recipe = json.loads((FIXTURE / 'boundary-controls.json').read_text())
        cls.mapping = write_boundary_controls(cls.source, cls.recipe, cls.patch)
        cls.corrected = cls.root / 'corrected.net.xml'
        subprocess.run([str(Path(sumo.SUMO_HOME) / 'bin/netconvert'),
            '--sumo-net-file', str(cls.source), '--connection-files', str(cls.patch),
            '--output-file', str(cls.corrected)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_source_reproduces_the_reported_double_stop_with_a_lone_bus(self):
        for ident, minimum in [('d1', 40), ('d0', 100)]:
            with self.subTest(direction=ident):
                result = run_buses(self.source, self.root / ('source-' + ident), (ident,))
                self.assertGreaterEqual(result['post_entry_wait'][ident], minimum)
                self.assertEqual(result['collisions'], 0)

    def test_fixture_bytes_are_bound_to_the_frozen_native_source(self):
        provenance = json.loads((FIXTURE / 'source.json').read_text())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), provenance['fixture_sha256'])
        self.assertEqual(hashlib.sha256((FIXTURE / 'split.net.xml.gz').read_bytes()).hexdigest(), provenance['archive_sha256'])
        self.assertEqual(provenance['source']['network_sha256'],
                         '4ccaa3d85ba2e8b998a300c16a05f5e2714ec9e5289da0266125f988272706fe')

    def test_only_internal_controls_are_removed_and_external_programme_is_retained(self):
        source, corrected = ET.parse(self.source).getroot(), ET.parse(self.corrected).getroot()
        controller = self.recipe['controller']
        key = lambda row: tuple(row.get(name) for name in ['from', 'to', 'fromLane', 'toLane'])
        before = {key(row): row for row in source.findall('connection') if row.get('tl') == controller}
        after = {key(row): row for row in corrected.findall('connection') if row.get('tl') == controller}
        internal = {key(row) for row in self.mapping['internal_controls']}
        self.assertEqual(len(before), 21)
        self.assertEqual(len(internal), 10)
        self.assertEqual(set(before) - set(after), internal)
        self.assertEqual(len(after), 11)
        for ident, row in after.items():
            # netconvert recomputes off-state yielding when inner control changes.
            self.assertEqual({k: v for k, v in row.attrib.items() if k != 'state'},
                             {k: v for k, v in before[ident].attrib.items() if k != 'state'})
        original = next(row for row in source.findall('tlLogic') if row.get('id') == controller)
        updated = next(row for row in corrected.findall('tlLogic') if row.get('id') == controller)
        self.assertEqual(original.attrib, updated.attrib)
        self.assertEqual([row.attrib for row in original], [row.attrib for row in updated])

    def test_changed_source_programme_is_rejected_before_writing_a_patch(self):
        root = ET.parse(self.source)
        root.getroot().find('tlLogic/phase').set('duration', '32')
        altered = self.root / 'altered.net.xml'
        root.write(altered)
        output = self.root / 'rejected.con.xml'
        with self.assertRaisesRegex(ValueError, 'differs from the inspected source'):
            write_boundary_controls(altered, self.recipe, output)
        self.assertFalse(output.exists())

    def test_actual_import_stage_is_checked_independently_before_conversion(self):
        # Exercise the stage-input boundary with the small native fixture.
        recipe = {**self.recipe, 'import_topology_sha256': topology_fingerprint(
            ET.parse(self.source).getroot(), self.recipe)}
        verify_import_source(self.source, recipe)
        altered = ET.parse(self.source)
        altered.getroot().find('tlLogic/phase').set('duration', '32')
        path = self.root / 'changed-import-stage.net.xml'
        altered.write(path)
        with self.assertRaisesRegex(ValueError, 'Import-stage signal topology/programme differs'):
            verify_import_source(path, recipe)

    def test_frozen_import_rejects_geometry_override_and_records_inherited_patch(self):
        inherited = inherited_junction_correction(self.recipe)
        self.assertEqual(inherited['role'], 'inherited_model_geometry_correction')
        self.assertEqual(inherited['sha256'], self.recipe['junction_corrections_sha256'])
        self.assertEqual(inherited_junction_correction(self.recipe,
            {'sha256': self.recipe['junction_corrections_sha256']}), inherited)
        with self.assertRaisesRegex(ValueError, 'conflicts with the frozen import'):
            inherited_junction_correction(self.recipe, {'sha256': '0' * 64})

    def test_compiler_scope_check_retains_the_programme_and_walking_graph(self):
        report = verify_correction_scope(self.source, self.corrected, self.recipe)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['outside_scope_changes'], 0)
        self.assertTrue(report['explicit_pedestrian_graph_equal'])

    def test_compiler_drift_at_an_unrelated_junction_is_rejected(self):
        root = ET.parse(self.corrected)
        outside = next(row for row in root.getroot().findall('junction')
                       if not row.get('id').startswith(':') and row.get('id') not in self.recipe['junctions'])
        outside.set('x', str(float(outside.get('x')) + 1))
        altered = self.root / 'outside-drift.net.xml'
        root.write(altered)
        with self.assertRaisesRegex(ValueError, 'outside its scope'):
            verify_correction_scope(self.source, altered, self.recipe)

    def test_scope_guard_rejects_a_compiler_output_that_removes_external_control(self):
        root = ET.parse(self.corrected)
        for row in root.getroot().findall('connection'):
            if row.get('tl') == self.recipe['controller']:
                del row.attrib['tl']
                del row.attrib['linkIndex']
        altered = self.root / 'missing-entry-control.net.xml'
        root.write(altered)
        with self.assertRaisesRegex(ValueError, 'external entry control'):
            verify_correction_scope(self.source, altered, self.recipe)

    def test_vehicle_permissions_and_pedestrian_connections_are_preserved(self):
        def connectivity(file, vehicle_class):
            root = ET.parse(file).getroot()
            net = sumolib.net.readNet(str(file), withInternal=True)
            lanes = {lane.getID(): lane for edge in net.getEdges(withInternal=True) for lane in edge.getLanes()}
            return {(row.get('from'), row.get('fromLane'), row.get('to'), row.get('toLane'),
                     row.get('allow'), row.get('disallow')) for row in root.findall('connection')
                    if lanes[row.get('from') + '_' + row.get('fromLane')].allows(vehicle_class)
                    and lanes[row.get('to') + '_' + row.get('toLane')].allows(vehicle_class)
                    and not row.get('from').startswith(':') and not row.get('to').startswith(':')}
        for vehicle_class in ['bus', 'passenger', 'taxi', 'bicycle', 'motorcycle']:
            with self.subTest(vehicle_class=vehicle_class):
                self.assertEqual(connectivity(self.source, vehicle_class), connectivity(self.corrected, vehicle_class))
        def pedestrian_graph(file):
            root = ET.parse(file).getroot()
            lanes = {row.get('id') for row in root.iter('lane') if row.get('allow') == 'pedestrian'}
            return lanes, {(row.get('from'), row.get('fromLane'), row.get('to'), row.get('toLane'))
                           for row in root.findall('connection')
                           if row.get('from') + '_' + row.get('fromLane') in lanes
                           and row.get('to') + '_' + row.get('toLane') in lanes}
        self.assertEqual(pedestrian_graph(self.source), pedestrian_graph(self.corrected))

    def test_opposing_buses_do_not_trap_one_another_inside_the_junction(self):
        for offset in [-10, -5, 0, 5, 10]:
            with self.subTest(offset=offset):
                result = run_buses(self.corrected, self.root / ('opposing-' + str(offset)), offset=offset)
                self.assertEqual(result['collisions'], 0)
                self.assertEqual(max(result['post_entry_wait'].values()), 0)

    def test_every_pair_of_retained_bus_movements_completes_without_a_recorded_collision(self):
        movements = json.loads((FIXTURE / 'movements.json').read_text())
        self.assertEqual(len(movements), 17)
        for (i, left), (j, right) in itertools.combinations(enumerate(movements), 2):
            for offset in [-5, 0, 5]:
                with self.subTest(left=i, right=j, offset=offset):
                    self.assertEqual(run_conflicts(self.corrected, self.root / f'pair-{i}-{j}-{offset}',
                                                  [left, right], offset=offset), 0)

    def test_all_movements_and_the_walking_route_complete_together(self):
        movements = json.loads((FIXTURE / 'movements.json').read_text())
        for offset in [0, 2, 5]:
            with self.subTest(offset=offset):
                self.assertEqual(run_conflicts(self.corrected, self.root / ('mixed-' + str(offset)),
                                              movements, offset=offset, walkers=True), 0)

    def test_corrected_lone_bus_does_not_receive_another_stop_after_admission(self):
        for ident in ['d1', 'd0']:
            with self.subTest(direction=ident):
                result = run_buses(self.corrected, self.root / ('corrected-' + ident), (ident,))
                self.assertEqual(result['post_entry_wait'][ident], 0,
                    'Bus stopped again inside the already-admitted junction')
                self.assertEqual(result['collisions'], 0)


if __name__ == '__main__':
    unittest.main()
