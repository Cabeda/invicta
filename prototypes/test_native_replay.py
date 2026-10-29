"""Exercise shared preparation through the same interface as both study adapters."""
from pathlib import Path
import dataclasses, gzip, json, tempfile, unittest
from native_replay import ReplayStudy, prepare, digest, save_file,expand_capture

class NativeReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'data/raw').mkdir(parents=True);(self.root/'inspection-assets').mkdir()
        net='<net><location netOffset="0,0" projParameter="EPSG:3857"/><edge id="e" name="Rua de Costa Cabral"><lane id="e_0" index="0" length="20" shape="0,0 20,0" allow="bus passenger"/></edge></net>'
        for policy in ['baseline','restricted']:
            (self.root/f'data/{policy}.net.xml').write_text(net)
            folder=self.root/f'runs/moderate-{policy}-17';folder.mkdir(parents=True)
            (folder/'routes.rou.xml').write_text('<routes/>');(folder/'additional.add.xml').write_text('<additional><busStop id="s" lane="e_0" endPos="10"/></additional>')
        (self.root/'results.json').write_text(json.dumps({'buses':[{'id':'bus_0','line':'701','trip_id':'trip'}]}))
        (self.root/'data/vehicle-dimensions-3d.json').write_text('{"types":{}}')
        self.osm=self.root/'data/raw/osm-tile-0.xml'
        self.osm.write_text('<osm><node id="1" lon="0" lat="0"/><node id="2" lon="0.0001" lat="0"/><node id="3" lon="0.0001" lat="0.0001"/><way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="1"/><tag k="building" v="yes"/></way></osm>')
        self.study=ReplayStudy(self.root,'fixture',1,2,('moderate',),{'direction':'1','from':'a','to':'b'})
        for index,policy in enumerate(['baseline','restricted']):
            paths=[self.root/f'data/{policy}.net.xml',self.root/f'runs/moderate-{policy}-17/routes.rou.xml',self.root/f'runs/moderate-{policy}-17/additional.add.xml']
            value={'case':'moderate','policy':policy,'seed':17,'start':1,'end':2,'step':1,'scene_schema':2,'input_hashes':{str(p.relative_to(self.root)):digest(p) for p in paths},'capture_edges':None,
                'vehicles':[{'id':'bus_0','group':'bus'}],'frames':[{'t':t,'vehicles':[[0,1,1,0,1,index,1]]} for t in [1,2]],'captured_at':'frozen'}
            save_file(self.root/f'inspection-assets/moderate-{policy}.json.gz',value)
    def tearDown(self): self.temp.cleanup()
    def no_run(self,*args,**kwargs): raise AssertionError('Unexpected native rerun')
    def test_both_policy_captures_publish_matched_provenance(self):
        manifest=prepare(self.study,run_native=self.no_run)
        self.assertEqual(len(manifest['clips']),2)
        for clip in manifest['clips']:
            value=json.loads(gzip.decompress((self.root/'inspection-assets'/clip['file']).read_bytes()))
            self.assertEqual(value['capture_signature'],manifest['capture_signature']);self.assertEqual(value['captured_at'],'frozen')
            self.assertEqual(clip['sha256'],digest(self.root/'inspection-assets'/clip['file']))
    def test_footprint_inputs_invalidate_scene_without_rerunning_movement(self):
        first=prepare(self.study,run_native=self.no_run)
        self.osm.write_text(self.osm.read_text().replace('</way>','<tag k="height" v="30"/></way>'))
        second=prepare(self.study,run_native=self.no_run)
        self.assertNotEqual(first['scene']['sha256'],second['scene']['sha256'])
        self.assertEqual(first['clips'][0]['sha256'],second['clips'][0]['sha256'])
    def test_changed_capture_window_does_not_reuse_old_cache(self):
        with self.assertRaisesRegex(AssertionError,'Unexpected native rerun'):
            prepare(dataclasses.replace(self.study,end=3),run_native=self.no_run)
    def test_scene_origin_is_independent_of_viewer_direction(self):
        before=prepare(self.study,run_native=self.no_run)
        path=self.root/'results.json';value=json.loads(path.read_text());value['scene_origin']=[10,20];path.write_text(json.dumps(value))
        after=prepare(self.study,run_native=self.no_run);scene=json.loads(gzip.decompress((self.study.output/'scene.json.gz').read_bytes()))
        self.assertEqual(scene['origin'],[10,20]);self.assertNotEqual(before['scene']['sha256'],after['scene']['sha256'])
        self.assertEqual([c['sha256'] for c in before['clips']],[c['sha256'] for c in after['clips']])
    def test_two_second_samples_keep_declared_native_times(self):
        for policy in ['baseline','restricted']:
            path=self.root/f'inspection-assets/moderate-{policy}.json.gz';value=json.loads(gzip.decompress(path.read_bytes()))
            value.update(step=2,end=3);value['frames'][1]['t']=3;save_file(path,value)
        manifest=prepare(dataclasses.replace(self.study,end=3,frame_step=2),run_native=self.no_run)
        self.assertTrue(all(c['step']==2 and c['frames']==2 for c in manifest['clips']))
    def test_wrong_lane_policy_is_rejected(self):
        path=self.root/'inspection-assets/moderate-baseline.json.gz';value=json.loads(gzip.decompress(path.read_bytes()));value['frames'][0]['vehicles'][0][5]=1;save_file(path,value)
        with self.assertRaisesRegex(ValueError,'another policy lane'):prepare(self.study,run_native=self.no_run)
    def test_compact_preparation_preserves_stationary_departing_and_reappearing_vehicles(self):
        expected={}
        for index,policy in enumerate(['baseline','restricted']):
            path=self.root/f'inspection-assets/moderate-{policy}.json.gz';value=json.loads(gzip.decompress(path.read_bytes()));value['end']=3
            value['vehicles'].append({'id':'car_1','group':'through'})
            bus=[0,1,1,0,1,index,1];car=[1,2,1,0,0,index,2]
            value['frames']=[{'t':1,'vehicles':[bus,car]},{'t':2,'vehicles':[car]},{'t':3,'vehicles':[car,bus]}];expected[policy]=value['frames'];save_file(path,value)
        study=dataclasses.replace(self.study,end=3,compact_frames=True);first=prepare(study,run_native=self.no_run)
        for clip in first['clips']:
            packed=json.loads(gzip.decompress((study.output/clip['file']).read_bytes()))
            self.assertEqual(clip['encoding'],'vehicle-deltas-v1');self.assertEqual(packed['frames'][1]['vehicles'],[])
            self.assertEqual(expand_capture(packed)['frames'],expected[clip['policy']])
        second=prepare(study,run_native=self.no_run)
        self.assertEqual([c['sha256'] for c in first['clips']],[c['sha256'] for c in second['clips']])
    def test_inherited_footprints_require_matching_projection(self):
        inherited=self.root/'wrong.json.gz';save_file(inherited,{'projection':{'netOffset':'1,1','projParameter':'EPSG:3857'},'features':[]})
        with self.assertRaisesRegex(ValueError,'projection and offset'):prepare(dataclasses.replace(self.study,inherited_buildings=(inherited,)),run_native=self.no_run)
    def test_full_day_positions_are_extracted_without_a_second_execution(self):
        for policy in ['baseline','restricted']:
            target=self.root/f'inspection-assets/moderate-{policy}.json.gz';value=json.loads(gzip.decompress(target.read_bytes()));target.unlink()
            folder=self.root/f'runs/moderate-{policy}-17';trajectory=folder/'trajectory.xml.gz'
            selection=folder/'replay-edges.txt';selection.write_text('edge:e\n')
            trajectory.write_bytes(gzip.compress(('<fcd-export>'+''.join(f'<timestep time="{t}"><vehicle id="bus_0" type="bus" x="1" y="1" angle="0" speed="1" lane="e_0" pos="1"/></timestep>' for t in [0,1,2,3])+'</fcd-export>').encode()))
            (folder/'replay-trajectory.json').write_text(json.dumps({'input_hashes':value['input_hashes'],'seed':17,'simulation_begin':0,'start':1,'end':2,'step':1,'trajectory_sha256':digest(trajectory),'selection_sha256':digest(selection)}))
        manifest=prepare(dataclasses.replace(self.study,trajectory_root=self.root/'runs'),run_native=self.no_run)
        self.assertTrue(all(c['frames']==2 and c['execution']['kind']=='same_full_day_execution' for c in manifest['clips']))
        # Expanding a visual scope must never relabel positions that were filtered out.
        folder=self.root/'runs/moderate-baseline-17';selection=folder/'replay-edges.txt';selection.write_text('edge:another-edge\n')
        metadata=json.loads((folder/'replay-trajectory.json').read_text());metadata['selection_sha256']=digest(selection);(folder/'replay-trajectory.json').write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError,'do not cover'):prepare(dataclasses.replace(self.study,trajectory_root=self.root/'runs'),run_native=self.no_run)

if __name__=='__main__': unittest.main()
