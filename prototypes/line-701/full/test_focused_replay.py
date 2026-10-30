"""The focused visual recording must preserve its failing native source."""
import gzip
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from trial_evidence import load_trial, read_archive

ROOT=Path(__file__).resolve().parents[3]

class FocusedReplayTests(unittest.TestCase):
    def test_capture_matches_native_calls_and_retains_real_holding(self):
        folder=ROOT/'prototypes/line-701/focused-replay'
        evidence_root=ROOT/'docs/research/701-focused-replay-2026-10-30'
        archive=json.loads((evidence_root/'evidence.json').read_text())
        source=load_trial(ROOT/'docs/research/701-bus-only-controls-2026-10-30/controls.json',
                          'v6-bus-only-existing-signals-60-s17')
        outputs={name:read_archive(evidence_root,desc) for name,desc in archive['evidence'].items()}
        self.assertEqual([v.attrib for v in ET.fromstring(outputs['stops.xml'])],source.calls())
        self.assertEqual([v.attrib for v in ET.fromstring(outputs['trips.xml']) if v.tag=='tripinfo'],
                         [v.attrib for v in ET.fromstring(source.payload('trips.xml')) if v.tag=='tripinfo'])
        manifest=json.loads(outputs['manifest.json'])
        self.assertEqual(manifest['compared_stop_events'],6024)
        self.assertEqual(manifest['completed_scheduled_services'],127)
        self.assertEqual(hashlib.sha256(outputs['capture.py']).hexdigest(),manifest['capture_implementation_sha256'])
        self.assertEqual(outputs['capture.py'],(folder/'capture.py').read_bytes())
        for name,fingerprint in manifest['output_hashes'].items():
            self.assertEqual(hashlib.sha256(outputs[name]).hexdigest(),fingerprint)
        index=json.loads((folder/'capture-index.json').read_text())
        self.assertEqual(hashlib.sha256((folder/'replay.json.gz').read_bytes()).hexdigest(),index['replay_sha256'])
        self.assertEqual(hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),index['manifest_sha256'])
        data=json.loads(gzip.decompress((folder/'replay.json.gz').read_bytes()))
        self.assertFalse(data['manifest']['qualified'])
        evening=next(w for w in data['windows'] if w['id']=='evening')
        self.assertEqual([f['time'] for f in evening['frames']],list(range(73200,74041)))
        frame=next(f for f in evening['frames'] if f['time']==73530)
        self.assertEqual(frame['focus']['wait'],8)
        self.assertEqual(frame['focus']['next_signals'][0][3],'G')
        areosa=next(p for p in data['timing']['d1_bus_55'] if p['stop']=='AREOSA (MERCADO)')
        self.assertEqual(areosa['arrival'],72749)
        self.assertEqual(areosa['departure'],areosa['scheduled'])
        self.assertEqual(areosa['departure']-areosa['arrival'],331)
        for rows in data['timing'].values():
            self.assertTrue(all(p['terminal'] or p['departure']>=p['scheduled'] for p in rows))

    def test_signal_sources_are_not_presented_as_a_physical_head_mapping(self):
        folder=ROOT/'prototypes/line-701/focused-replay'
        audit=json.loads((folder/'signal-audit.json').read_text())
        index=json.loads((folder/'signal-audit-index.json').read_text())
        capture=json.loads((folder/'manifest.json').read_text())
        self.assertEqual(hashlib.sha256((folder/'signal-audit.json').read_bytes()).hexdigest(),index['sha256'])
        self.assertEqual(audit['network_sha256'],capture['source']['network_sha256'])
        self.assertEqual(audit['implementation_sha256'],hashlib.sha256((folder/'audit_signals.py').read_bytes()).hexdigest())
        self.assertFalse(audit['field_validated'])
        self.assertFalse(audit['native_inputs_changed'])
        self.assertEqual(len(audit['official_equipment_within_75_metres']),16)
        self.assertEqual({p['installation'] for p in audit['official_equipment_within_75_metres']},{'121'})
        self.assertTrue(all(p['head_type']=='unknown' and p['movement_assignment']=='unverified'
                            for p in audit['official_equipment_within_75_metres']))
        self.assertEqual(sum(p['tags'].get('crossing')=='traffic_signals'
                             for p in audit['osm_nodes_under_joined_controller']),7)
        self.assertEqual(audit['controller']['movement_links'],21)
        self.assertEqual(audit['controller']['incoming_lanes'],14)
        self.assertEqual(len(audit['controller']['represented_junctions']),5)
        self.assertEqual([m['link_index'] for m in audit['scheduled_route_links_under_controller']['1']],[1,7,17])
        self.assertEqual(audit['user_observation']['expected_vehicle_lights'],2)

if __name__=='__main__': unittest.main()
