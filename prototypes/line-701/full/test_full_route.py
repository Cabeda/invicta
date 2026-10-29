"""Validate the real frozen route contract, independently of traffic outcomes."""
from pathlib import Path
import hashlib,json,unittest
ROOT=Path(__file__).resolve().parent

class FullRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ref=json.loads((ROOT/'data/routes.json').read_text())
    def test_complete_service_with_short_and_overnight_workings(self):
        routes=self.ref['directions'];self.assertEqual(set(routes),{'0','1'})
        self.assertEqual([len(routes[d]['stops']) for d in ['1','0']],[56,54])
        self.assertEqual([len(routes[d]['trips']) for d in ['1','0']],[63,64])
        trips=[t for r in routes.values() for t in r['trips']]
        self.assertEqual(len({t['id'] for t in trips}),127);self.assertEqual(sum(len(t['stops']) for t in trips),6024)
        self.assertTrue(any(t['depart']>=86400 for t in trips));self.assertTrue(any(len(t['stops'])<54 for t in trips))
    def test_stops_and_working_endpoints_remain_on_ordered_direction_path(self):
        for direction,r in self.ref['directions'].items():
            self.assertFalse(any(e.startswith(':') for e in r['path']))
            self.assertEqual(len(r['path']),len(set(r['path'])))
            for stop in r['stops']:
                self.assertGreaterEqual(stop['pos'],15);self.assertLessEqual(stop['snap_distance'],25)
                self.assertEqual(r['path'][stop['path_index']],stop['edge'])
                self.assertTrue(stop['native_stop_id'].startswith('d'+direction+'_'))
            for trip in r['trips']:
                a,b=trip['stops'][0],trip['stops'][-1]
                self.assertEqual(trip['path'],r['path'][a['path_index']:b['path_index']+1])
                self.assertTrue(all(b['scheduled']>a['scheduled'] for a,b in zip(trip['stops'],trip['stops'][1:])))
    def test_geometry_audit_is_bound_to_the_current_route(self):
        audit=json.loads((ROOT/'data/route-geometry-audit.json').read_text())
        self.assertEqual(audit['status'],'geometry_audit_passed')
        self.assertEqual(audit['routes_sha256'],hashlib.sha256((ROOT/'data/routes.json').read_bytes()).hexdigest())
        self.assertEqual(audit['network_sha256'],self.ref['network_sha256'])

if __name__=='__main__':unittest.main()
