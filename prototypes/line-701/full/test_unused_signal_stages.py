"""Native clearance/movement checks for removing two unserved model stages."""
import itertools
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import gzip
import xml.etree.ElementTree as ET

import sumo
from signal_mapping import write_boundary_controls
from unused_signal_stages import write_program, CONTROLLER
from test_signal_mapping import run_conflicts, FIXTURE


class UnusedStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='invicta-stage-cleanup-')
        cls.root = Path(cls.temporary.name)
        source = cls.root / 'source.net.xml'
        source.write_bytes(gzip.decompress((FIXTURE / 'split.net.xml.gz').read_bytes()))
        patch = cls.root / 'patch.xml'
        write_boundary_controls(source, json.loads((FIXTURE / 'boundary-controls.json').read_text()), patch)
        cls.network = cls.root / 'network.xml'
        subprocess.run([str(Path(sumo.SUMO_HOME) / 'bin/netconvert'), '--sumo-net-file', str(source),
            '--connection-files', str(patch), '--output-file', str(cls.network)], check=True, capture_output=True)
        cls.program = cls.root / 'program.add.xml'
        cls.report = write_program(cls.network, cls.program)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_only_unserved_green_yellow_stages_are_removed(self):
        before = next(x for x in ET.parse(self.network).getroot().findall('tlLogic') if x.get('id') == CONTROLLER)
        after = ET.parse(self.program).getroot().find('tlLogic')
        self.assertEqual(len(before.findall('phase')), 24)
        self.assertEqual(len(after.findall('phase')), 20)
        self.assertEqual(self.report['removed_phase_indices'], [6, 7, 12, 13])
        self.assertEqual([x.attrib for i, x in enumerate(before) if i not in [6, 7, 12, 13]],
                         [x.attrib for x in after])
        self.assertEqual([x.attrib for x in before if set(x.get('state')) == {'r'}],
                         [x.attrib for x in after if set(x.get('state')) == {'r'}])

    def test_retained_movements_and_walkers_clear_with_the_loaded_programme(self):
        paths = json.loads((FIXTURE / 'movements.json').read_text())
        for (i, left), (j, right) in itertools.combinations(enumerate(paths), 2):
            with self.subTest(left=i, right=j):
                self.assertEqual(run_conflicts(self.network, self.root / f'pair-{i}-{j}',
                    [left, right], additional=self.program), 0)
        self.assertEqual(run_conflicts(self.network, self.root / 'mixed', paths,
                                      walkers=True, additional=self.program), 0)
