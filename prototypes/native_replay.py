"""Prepare matched native scenes and captures for concrete study adapters.

SUMO remains the movement authority. This module owns footprint assembly,
compatibility checks, cache invalidation and publication as one operation.
"""
from dataclasses import dataclass
from pathlib import Path
import concurrent.futures, datetime, gzip, hashlib, json, math, subprocess
import xml.etree.ElementTree as ET
import numpy as np
from pyproj import Transformer
import sumo

@dataclass(frozen=True)
class ReplayStudy:
    root: Path
    id: str
    start: int
    end: int
    cases: tuple
    scope: dict
    inherited_buildings: tuple = ()
    dimensions_file: Path | None = None
    results_file: Path | None = None
    seed: int = 17
    begin: int = 0
    limit_scene_edges: bool = False
    frame_step: int = 1
    trajectory_root: Path | None = None
    compact_frames: bool = False
    workers: int = 3
    policies: tuple = ('baseline', 'restricted')

    def __post_init__(self):
        if self.begin>self.start or self.start < 0 or self.end <= self.start or not self.cases or self.frame_step<1 or (self.end-self.start)%self.frame_step:
            raise ValueError('A replay study needs cases and a positive ordered time window')

    @property
    def output(self): return self.root / 'inspection-assets'
    @property
    def dimensions(self): return self.dimensions_file or self.root / 'data/vehicle-dimensions-3d.json'


def digest(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()
def digest_value(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save_file(path, value):
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and gzip.decompress(path.read_bytes()) == raw: return
    with gzip.GzipFile(filename=str(path), mode='wb', mtime=0) as f: f.write(raw)
    print(path.name, len(raw), 'uncompressed bytes', flush=True)

def expand_capture(value):
    if value.get('encoding','frames-v1')=='frames-v1':return value
    if value['encoding']!='vehicle-deltas-v1':raise ValueError('Unsupported native replay encoding')
    active={};order=[];frames=[]
    for frame in value['frames']:
        for ident in frame.get('removed',[]):
            if ident not in active:raise ValueError('Removed native vehicle was not present')
            del active[ident]
        for row in frame['vehicles']:active[row[0]]=row
        order=frame.get('order',order)
        if len(order)!=len(active) or len(set(order))!=len(order) or any(ident not in active for ident in order):raise ValueError('Native replay order does not match active vehicles')
        frames.append({'t':frame['t'],'vehicles':[active[ident] for ident in order]})
    return {**value,'frames':frames,'encoding':'frames-v1'}

def compact_capture(value):
    value=expand_capture(value);previous={};previous_order=[];frames=[]
    for frame in value['frames']:
        current={row[0]:row for row in frame['vehicles']};order=list(current)
        if len(current)!=len(frame['vehicles']):raise ValueError('Duplicate native vehicle in a frame')
        packed={'t':frame['t'],'vehicles':[row for ident,row in current.items() if previous.get(ident)!=row]}
        removed=[ident for ident in previous if ident not in current]
        if removed:packed['removed']=removed
        if order!=previous_order:packed['order']=order
        frames.append(packed);previous=current;previous_order=order
    return {**value,'frames':frames,'encoding':'vehicle-deltas-v1'}

def save_capture(study,path,value):
    packed=compact_capture(value) if study.compact_frames else value
    if study.compact_frames and expand_capture(packed)['frames']!=value['frames']:raise ValueError('Native replay packing changed a frame')
    save_file(path,packed)

def validate_capture(study, value, scene_data):
    if value.get('scope', study.scope) != study.scope: raise ValueError('Replay scope does not match study')
    if value.get('capture_signature', scene_data['capture_signature']) != scene_data['capture_signature']: raise ValueError('Replay does not match scene')
    frames=value.get('frames',[])
    if len(frames) != (study.end-study.start)//study.frame_step+1: raise ValueError('Replay has incomplete time coverage')
    lane_count=len(scene_data['lane_ids']);vehicle_count=len(value.get('vehicles',[]))
    for i,frame in enumerate(frames):
        if frame['t'] != study.start+i*study.frame_step: raise ValueError('Replay frame times must be contiguous native samples at the declared step')
        for row in frame['vehicles']:
            if len(row)!=7 or type(row[0]) is not int or type(row[5]) is not int or not 0<=row[0]<vehicle_count or not 0<=row[5]<lane_count or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in row):
                raise ValueError('Replay has invalid vehicle or lane references')
            if scene_data['lanes'][row[5]]['policy'] != value['policy']: raise ValueError('Replay references another policy lane')

def clip_descriptor(study,value):
    peak={}
    for frame in value['frames']:
        counts={}
        for row in frame['vehicles']:
            group=value['vehicles'][row[0]]['group'];counts[group]=counts.get(group,0)+1
        for group,count in counts.items():peak[group]=max(peak.get(group,0),count)
    name=f"{value['case']}-{value['policy']}.json.gz"
    result={key:value[key] for key in ['case','policy','seed','start','end','step','simulation_begin','capture_signature','input_hashes','captured_at']}
    result.update(file=name,sha256=digest(study.output/name),frames=len(value['frames']),vehicles=len(value['vehicles']),peak_by_group=peak)
    result['encoding']='vehicle-deltas-v1' if study.compact_frames else 'frames-v1'
    if value.get('execution'):result['execution']=value['execution']
    return result

def shape(text): return [[round(float(v), 2) for v in p.split(',')[:2]] for p in text.split()]

def scene(study):
    result = json.loads((study.results_file or study.root / 'results.json').read_text())
    net = ET.parse(study.root / 'data/baseline.net.xml').getroot()
    lanes, junctions, hashes = [], {}, {}
    display_edges = set(result.get('scene_edge_ids') or result.get('replay_edge_ids') or [])
    capture_edges=set(result.get('replay_edge_ids') or [])
    capture_lane_ids=[] if result.get('scene_edge_ids') else None
    for policy in study.policies:
        file = study.root / 'data' / f'{policy}.net.xml'
        policy_net = ET.parse(file).getroot()
        hashes[policy] = digest(file)
        selected_nodes = {e.get(key) for e in policy_net.findall('edge') if e.get('id') in display_edges for key in ['from','to']}
        internal_lanes = {ident for node in policy_net.findall('junction') if node.get('id') in selected_nodes for ident in node.get('intLanes','').split()}
        capture_nodes={e.get(key) for e in policy_net.findall('edge') if e.get('id') in capture_edges for key in ['from','to']}
        capture_internal={ident for node in policy_net.findall('junction') if node.get('id') in capture_nodes for ident in node.get('intLanes','').split()}
        for edge in policy_net.findall('edge'):
            for lane in edge.findall('lane'):
                if study.limit_scene_edges and display_edges and edge.get('id') not in display_edges and lane.get('id') not in internal_lanes: continue
                if capture_lane_ids is not None and (edge.get('id') in capture_edges or lane.get('id') in capture_internal):capture_lane_ids.append(policy+'|'+lane.get('id'))
                allow, disallow = lane.get('allow', '').split(), lane.get('disallow', '').split()
                def permits(kind):
                    return (not allow or kind in allow or 'all' in allow) and kind not in disallow and 'all' not in disallow
                lanes.append({'id': policy + '|' + lane.get('id'), 'local_id': lane.get('id'), 'policy': policy,
                              'edge': edge.get('id'), 'shape': shape(lane.get('shape')),
                              'length': float(lane.get('length')), 'width': float(lane.get('width', 3.2)),
                              'internal': edge.get('function') == 'internal',
                              'bus_priority': permits('bus') and not permits('passenger'),
                              'corridor': edge.get('id') in result['route_edge_ids'] if 'route_edge_ids' in result else edge.get('name') == 'Rua de Costa Cabral'})
        junctions[policy] = [shape(j.get('shape')) for j in policy_net.findall('junction') if j.get('shape') and (not study.limit_scene_edges or j.get('id') in selected_nodes)]
    frozen = study.root / 'data/buildings-3d.json.gz'
    building_inputs = [*sorted((study.root / 'data/raw').glob('osm-tile-*.xml')), *study.inherited_buildings]
    building_key = digest_value({'inputs': {str(p): digest(p) for p in building_inputs}, 'projection': dict(net.find('location').attrib), 'networks': hashes, 'rule': 2})
    cached_buildings = json.loads(gzip.decompress(frozen.read_bytes())) if frozen.exists() else {}
    if cached_buildings.get('cache_key') == building_key:
        buildings = cached_buildings
    else:
        nodes, ways, inputs = {}, {}, []
        tiles = sorted((study.root / 'data/raw').glob('osm-tile-*.xml'))
        if not tiles: raise RuntimeError('Frozen buildings or original OSM tiles required')
        for tile in tiles:
            inputs.append({'file': tile.name, 'sha256': digest(tile)})
            osm = ET.parse(tile).getroot()
            for node in osm.findall('node'): nodes[node.get('id')] = (float(node.get('lon')), float(node.get('lat')))
            for way in osm.findall('way'):
                tags = {t.get('k'): t.get('v') for t in way.findall('tag')}
                if 'building' in tags and tags['building'] != 'no':
                    ways[way.get('id')] = ([n.get('ref') for n in way.findall('nd')], tags)
        loc = net.find('location')
        transform = Transformer.from_crs('EPSG:4326', loc.get('projParameter'), always_xy=True)
        offset = list(map(float, loc.get('netOffset').split(',')))
        corridor = np.array([p for lane in lanes if lane['corridor'] for p in lane['shape']])
        def number(s):
            try: return float(str(s).replace(' m', '').replace(',', '.'))
            except (ValueError, TypeError): return None
        footprints = []
        for ident, (refs, tags) in ways.items():
            if len(refs) < 4 or refs[0] != refs[-1] or any(r not in nodes for r in refs): continue
            points = []
            for ref in refs[:-1]:
                x, y = transform.transform(*nodes[ref]); points.append([round(x + offset[0], 2), round(y + offset[1], 2)])
            centre = np.mean(points, axis=0)
            if np.min(np.sum((corridor - centre) ** 2, axis=1)) > 260 ** 2: continue
            height, levels = number(tags.get('height')), number(tags.get('building:levels'))
            source = 'osm_height' if height and 2 < height < 120 else 'levels_estimate' if levels and 0 < levels < 35 else 'illustrative'
            height = height if source == 'osm_height' else levels * 3.2 if source == 'levels_estimate' else 9
            footprints.append({'id': ident, 'shape': points, 'height': round(height, 1), 'height_source': source, 'name': tags.get('name', '')})
        buildings = {'source': 'Frozen OpenStreetMap building ways; input hashes retained; not a survey',
                     'licence': 'ODbL, © OpenStreetMap contributors', 'inputs': inputs, 'features': footprints,
                     'height_rule': 'OSM height when valid; otherwise levels × 3.2m; otherwise illustrative 9m. No terrain.'}
        projection = {key: net.find('location').get(key) for key in ['netOffset', 'projParameter']}
        inherited = {}
        for snapshot in study.inherited_buildings:
            saved = json.loads(gzip.decompress(snapshot.read_bytes()))
            if saved.get('projection') != projection: raise ValueError('Inherited footprints do not match the study projection and offset')
            inherited.update({feature['id']: feature for feature in saved['features']})
        inherited.update({feature['id']: feature for feature in buildings['features']})
        buildings.update(features=list(inherited.values()), projection=projection, cache_key=building_key, inherited_inputs={str(p): digest(p) for p in study.inherited_buildings})
        save_file(frozen, buildings)
    stops = []
    for policy in study.policies:
        add = ET.parse(study.root / 'runs' / f'{study.cases[0]}-{policy}-{study.seed}/additional.add.xml').getroot()
        for stop in add.findall('busStop'):
            stops.append({'id': stop.get('id'), 'name': stop.get('name'), 'policy': policy,
                          'lane': policy + '|' + stop.get('lane'), 'pos': float(stop.get('endPos'))})
    value = {'lanes': lanes, 'junctions': junctions, 'buildings': buildings, 'stops': stops,
             'vehicle_dimensions': json.loads(study.dimensions.read_text()),
             'lane_ids': [l['id'] for l in lanes], 'network_sha256': hashes, 'scene_schema': 2,
             'projection': dict(net.find('location').attrib),
             'origin':result.get('scene_origin'),
             'bus_info': {b['id']: {'line': b['line'], 'trip': b['trip_id'], 'direction': b.get('direction'), 'label':b.get('label')} for b in result['buses']},
             'capture_edges': result.get('replay_edge_ids'),
             'capture_lane_ids':capture_lane_ids,
             'show_lane_permissions': 'route_edge_ids' in result,
             'notes': 'Flat model. Lane widths/junctions are imported or generated, not surveyed. Building heights mostly estimated.'}
    value.update(study_id=study.id, scope=study.scope)
    signature_keys=['scene_schema', 'lane_ids', 'network_sha256', 'capture_edges', 'scope', 'study_id']
    if capture_lane_ids is not None:signature_keys.append('capture_lane_ids')
    value['capture_signature'] = digest_value({key: value.get(key) for key in signature_keys})
    save_file(study.output / 'scene.json.gz', value)
    print('Buildings:', len(buildings['features']), 'OSM heights:', sum(b['height_source'] == 'osm_height' for b in buildings['features']), flush=True)
    return value

def capture(study, case, policy, scene_data, run_native=subprocess.run):
    key = f'{case}-{policy}'
    folder = study.root / 'runs/inspection' / key
    folder.mkdir(parents=True, exist_ok=True)
    inputs = [study.root / 'data' / f'{policy}.net.xml', study.root / 'runs' / f'{key}-{study.seed}/routes.rou.xml', study.root / 'runs' / f'{key}-{study.seed}/additional.add.xml']
    hashes = {str(p.relative_to(study.root)): digest(p) for p in inputs}
    source_metadata=None
    if study.trajectory_root:
        source_folder=study.trajectory_root/f'{key}-{study.seed}'
        source_metadata=json.loads((source_folder/'replay-trajectory.json').read_text())
        selection=source_folder/'replay-edges.txt'
        if digest(selection)!=source_metadata['selection_sha256']:raise ValueError('Full-day recorded edge selection bytes changed')
        recorded={line.removeprefix('edge:') for line in selection.read_text().splitlines() if line.startswith('edge:')}
        requested_lanes=set(scene_data.get('capture_lane_ids') or [])
        requested={lane['edge'] for lane in scene_data['lanes'] if lane['policy']==policy and (lane['id'] in requested_lanes if requested_lanes else not scene_data.get('capture_edges') or lane['edge'] in scene_data['capture_edges'])}
        if not requested<=recorded:raise ValueError('Full-day positions do not cover the requested replay edges; a new native execution is required')
    target = study.output / f'{key}.json.gz'
    cached = expand_capture(json.loads(gzip.decompress(target.read_bytes()))) if target.exists() else None
    compatible = cached is not None and cached.get('input_hashes') == hashes and cached.get('step') == study.frame_step and cached.get('scene_schema') == 2 and cached.get('start') == study.start and cached.get('end') == study.end and cached.get('capture_edges') == scene_data.get('capture_edges') and cached.get('seed') == study.seed and cached.get('simulation_begin',0) == study.begin and cached.get('case') == case and cached.get('policy') == policy
    if study.trajectory_root and compatible:
        compatible=cached.get('execution',{}).get('trajectory_sha256')==source_metadata['trajectory_sha256'] and cached.get('execution',{}).get('selection_sha256')==source_metadata['selection_sha256']
    if compatible and cached.get('capture_signature') not in (None, scene_data['capture_signature']):
        compatible = False
    if compatible:
        validate_capture(study, cached, scene_data)
        metadata={'study_id':study.id,'scope':study.scope,'capture_signature':scene_data['capture_signature'],'replay_schema':4 if study.compact_frames else 3,'simulation_begin':study.begin}
        cached.update(metadata);save_capture(study,target,cached)
        return clip_descriptor(study,cached)
    add = ET.parse(inputs[2])
    for element in list(add.getroot()):
        if element.tag == 'edgeData': add.getroot().remove(element)
    add.write(folder / 'stops.add.xml', encoding='utf-8', xml_declaration=True)
    fcd = folder / 'trajectory.xml.gz'
    cmd = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(inputs[0]), '--route-files', str(inputs[1]), '--additional-files', str(folder / 'stops.add.xml'), '--begin', str(study.begin), '--end', str(study.end + 1), '--seed', str(study.seed), '--time-to-teleport', '-1', '--no-step-log', 'true', '--duration-log.disable', 'true', '--xml-validation', 'never', '--fcd-output', str(fcd), '--device.fcd.begin', str(study.start), '--device.fcd.period', str(study.frame_step), '--fcd-output.attributes', 'id,x,y,angle,speed,type,lane,pos', '--stop-output', str(folder / 'stops.xml')]
    execution=None
    if study.trajectory_root:
        metadata=source_metadata
        expected={'input_hashes':hashes,'seed':study.seed,'simulation_begin':study.begin,'start':study.start,'end':study.end,'step':study.frame_step}
        if any(metadata.get(k)!=v for k,v in expected.items()):raise ValueError('Full-day trajectory does not match replay inputs and window')
        fcd=source_folder/'trajectory.xml.gz'
        if digest(fcd)!=metadata['trajectory_sha256']:raise ValueError('Full-day trajectory bytes changed')
        execution={'kind':'same_full_day_execution','trajectory_sha256':metadata['trajectory_sha256'],'selection_sha256':metadata['selection_sha256']}
    else:
        run = run_native(cmd, capture_output=True, text=True)
        (folder / 'capture.log').write_text(run.stdout + '\n' + run.stderr)
        if run.returncode: raise RuntimeError(run.stderr[-1500:])
    vehicles, ids, frames = [], {}, []
    lane_index = {ident: i for i, ident in enumerate(scene_data['lane_ids'])}
    capture_lanes=set(scene_data.get('capture_lane_ids') or [])
    with gzip.open(fcd, 'rb') as f:
        for _, el in ET.iterparse(f, events=['end']):
            if el.tag != 'timestep': continue
            t = float(el.get('time'))
            if t>study.end:break
            if study.start <= t <= study.end:
                rows = []
                for v in el:
                    idx = lane_index.get(policy + '|' + v.get('lane'), -1)
                    if idx < 0: continue
                    if capture_lanes and policy+'|'+v.get('lane') not in capture_lanes:continue
                    if scene_data.get('capture_edges') and idx >= 0:
                        lane = scene_data['lanes'][idx]
                        if not lane['internal'] and lane['edge'] not in scene_data['capture_edges']: continue
                    ident = v.get('id')
                    if ident not in ids:
                        ids[ident] = len(vehicles)
                        vehicles.append({'id': ident, 'group': v.get('type')})
                    rows.append([ids[ident], round(float(v.get('x')), 2), round(float(v.get('y')), 2),
                                 round(float(v.get('angle')), 2), round(float(v.get('speed')), 2),
                                 lane_index.get(policy + '|' + v.get('lane'), -1), round(float(v.get('pos')), 2)])
                frames.append({'t': t, 'vehicles': rows})
            el.clear()
    value = {'case': case, 'policy': policy, 'seed': study.seed, 'start': study.start, 'end': study.end, 'step': study.frame_step, 'scene_schema': 2,
                           'frames': frames, 'vehicles': vehicles, 'input_hashes': hashes,'capture_edges':scene_data.get('capture_edges'),
                           'source': f'Native SUMO {study.frame_step}-second FCD sampling; front bumper coordinates; original simulation step and inputs retained',
                           'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           'study_id':study.id,'scope':study.scope,'capture_signature':scene_data['capture_signature'],'replay_schema':4 if study.compact_frames else 3,'simulation_begin':study.begin}
    if execution:value['execution']=execution
    validate_capture(study, value, scene_data)
    save_capture(study,target,value)
    return clip_descriptor(study,value)


def prepare(study, run_native=subprocess.run):
    """Publish a compatible scene, all captures and a reproducible manifest."""
    study.output.mkdir(parents=True,exist_ok=True)
    scene_data=scene(study)
    with concurrent.futures.ThreadPoolExecutor(max_workers=study.workers) as executor:
        jobs=[executor.submit(capture,study,case,policy,scene_data,run_native) for case in study.cases for policy in study.policies]
        values=[job.result() for job in jobs]
    manifest={'schema':'invicta.native-replay.v1','study_id':study.id,'scope':study.scope,
              'source_kind':'native_simulation','traffic':'synthetic; not observed or calibrated traffic',
              'capture_signature':scene_data['capture_signature'],
              'scene':{'file':'scene.json.gz','sha256':digest(study.output/'scene.json.gz'),'network_sha256':scene_data['network_sha256']},
              'clips':[]}
    manifest['clips']=values
    manifest['id']=digest_value(manifest)
    target=study.output/'manifest.json'
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Prepared',study.id,len(values),'matched captures',flush=True)
    return manifest
