from pathlib import Path
import copy,tempfile,unittest
from publication import digest,native_inputs,validate_publication

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'data').mkdir();(self.root/'inspection-assets').mkdir()
        (self.root/'data/routes.json').write_text('reference');(self.root/'inspection-assets/scene.json.gz').write_bytes(b'scene')
        self.raw={'meta':{'cases':['busy'],'seeds':[42]},'runs':[]}
        self.manifest={'scope':{'direction':'both','directions':{'0':{},'1':{}}},'capture_signature':'scene-id','scene':{'file':'scene.json.gz','sha256':digest(self.root/'inspection-assets/scene.json.gz'),'network_sha256':{}},'clips':[]}
        for policy in ['baseline','restricted']:
            folder=self.root/f'runs/busy-{policy}-42';folder.mkdir(parents=True)
            (folder/'routes.rou.xml').write_text('routes');(folder/'additional.add.xml').write_text('stops');(self.root/f'data/{policy}.net.xml').write_text(policy)
            inputs=native_inputs(self.root,'busy',policy,42);network=inputs[f'data/{policy}.net.xml']
            self.raw['runs'].append({'case':'busy','variant':policy,'seed':42,'native_inputs':inputs,'replay_trajectory_sha256':'native-trajectory','inputs':{'network':network,'reference':digest(self.root/'data/routes.json'),'demand':'same-requested-journeys','begin':18000,'end':99300}})
            self.manifest['scene']['network_sha256'][policy]=network
            path=self.root/f'inspection-assets/busy-{policy}.json.gz';path.write_bytes(policy.encode())
            self.manifest['clips'].append({'case':'busy','policy':policy,'seed':42,'input_hashes':inputs,'simulation_begin':18000,'start':60600,'end':66000,'capture_signature':'scene-id','file':path.name,'sha256':digest(path),'execution':{'kind':'same_full_day_execution','trajectory_sha256':'native-trajectory'}})
    def tearDown(self):self.temp.cleanup()
    def test_matching_generation_and_non_default_seed(self):self.assertTrue(validate_publication(self.root,self.raw,self.manifest))
    def test_replay_from_a_different_seed_is_rejected(self):
        self.manifest['clips'][0]['seed']=17
        with self.assertRaisesRegex(ValueError,'matching numeric'):validate_publication(self.root,self.raw,self.manifest)
    def test_stale_numeric_input_binding_is_rejected(self):
        (self.root/'runs/busy-baseline-42/routes.rou.xml').write_text('new demand')
        with self.assertRaisesRegex(ValueError,'binding'):validate_publication(self.root,self.raw,self.manifest)
    def test_incomplete_replay_is_rejected(self):
        self.manifest['clips'].pop()
        with self.assertRaisesRegex(ValueError,'matrix'):validate_publication(self.root,self.raw,self.manifest)
    def test_same_inputs_but_different_execution_is_rejected(self):
        self.manifest['clips'][0]['execution']['trajectory_sha256']='another-execution'
        with self.assertRaisesRegex(ValueError,'same full-day execution'):validate_publication(self.root,self.raw,self.manifest)
    def test_changed_requested_demand_is_rejected(self):
        self.raw['runs'][1]['inputs']['demand']='fewer-journeys'
        with self.assertRaisesRegex(ValueError,'requested demand differ'):validate_publication(self.root,self.raw,self.manifest)
    def test_frozen_publication_keeps_binding_when_large_inputs_are_archived(self):
        for run in self.raw['runs']:
            for name in run['native_inputs']:(self.root/name).unlink()
        self.assertTrue(validate_publication(self.root,self.raw,self.manifest))

if __name__=='__main__':unittest.main()
