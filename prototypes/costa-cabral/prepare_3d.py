"""THROWAWAY: freeze mapped context and native one-second SUMO replays for 3D."""
from pathlib import Path
import concurrent.futures, datetime, gzip, hashlib, json, math, subprocess
import xml.etree.ElementTree as ET
import numpy as np
from pyproj import Transformer
import sumo

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'inspection-assets'
OUT.mkdir(exist_ok=True)
START, END = 720, 1440

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value):
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    with gzip.GzipFile(filename=str(OUT / name), mode='wb', mtime=0) as f: f.write(raw)
    print(name, len(raw), 'uncompressed bytes', flush=True)
def shape(text): return [[round(float(v), 2) for v in p.split(',')[:2]] for p in text.split()]

def scene():
    result = json.loads((ROOT / 'results.json').read_text())
    net = ET.parse(ROOT / 'data/baseline.net.xml').getroot()
    lanes, junctions, hashes = [], {}, {}
    for policy in ['baseline', 'restricted']:
        file = ROOT / 'data' / f'{policy}.net.xml'
        policy_net = ET.parse(file).getroot()
        hashes[policy] = digest(file)
        for edge in policy_net.findall('edge'):
            for lane in edge.findall('lane'):
                allow, disallow = lane.get('allow', '').split(), lane.get('disallow', '').split()
                def permits(kind):
                    return (not allow or kind in allow or 'all' in allow) and kind not in disallow and 'all' not in disallow
                lanes.append({'id': policy + '|' + lane.get('id'), 'local_id': lane.get('id'), 'policy': policy,
                              'edge': edge.get('id'), 'shape': shape(lane.get('shape')),
                              'length': float(lane.get('length')), 'width': float(lane.get('width', 3.2)),
                              'internal': edge.get('function') == 'internal',
                              'bus_priority': permits('bus') and not permits('passenger'),
                              'corridor': edge.get('id') in result['route_edge_ids'] if 'route_edge_ids' in result else edge.get('name') == 'Rua de Costa Cabral'})
        junctions[policy] = [shape(j.get('shape')) for j in policy_net.findall('junction') if j.get('shape')]
    frozen = ROOT / 'data/buildings-3d.json.gz'
    if frozen.exists():
        buildings = json.loads(gzip.decompress(frozen.read_bytes()))
    else:
        nodes, ways, inputs = {}, {}, []
        tiles = sorted((ROOT / 'data/raw').glob('osm-tile-*.xml'))
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
        buildings = {'source': 'OpenStreetMap building ways in original 28 October 2026 map tiles; not a survey',
                     'licence': 'ODbL, © OpenStreetMap contributors', 'inputs': inputs, 'features': footprints,
                     'height_rule': 'OSM height when valid; otherwise levels × 3.2m; otherwise illustrative 9m. No terrain.'}
        with gzip.GzipFile(filename=str(frozen), mode='wb', mtime=0) as f:
            f.write(json.dumps(buildings, ensure_ascii=False, separators=(',', ':')).encode())
    stops = []
    for policy in ['baseline', 'restricted']:
        add = ET.parse(ROOT / 'runs' / f'moderate-{policy}-17/additional.add.xml').getroot()
        for stop in add.findall('busStop'):
            stops.append({'id': stop.get('id'), 'name': stop.get('name'), 'policy': policy,
                          'lane': policy + '|' + stop.get('lane'), 'pos': float(stop.get('endPos'))})
    value = {'lanes': lanes, 'junctions': junctions, 'buildings': buildings, 'stops': stops,
             'vehicle_dimensions': json.loads((ROOT / 'data/vehicle-dimensions-3d.json').read_text()),
             'lane_ids': [l['id'] for l in lanes], 'network_sha256': hashes, 'scene_schema': 2,
             'projection': dict(net.find('location').attrib),
             'bus_info': {b['id']: {'line': b['line'], 'trip': b['trip_id']} for b in result['buses']},
             'capture_edges': result.get('replay_edge_ids'),
             'show_lane_permissions': 'route_edge_ids' in result,
             'notes': 'Flat model. Lane widths/junctions are imported or generated, not surveyed. Building heights mostly estimated.'}
    save('scene.json.gz', value)
    print('Buildings:', len(buildings['features']), 'OSM heights:', sum(b['height_source'] == 'osm_height' for b in buildings['features']), flush=True)
    return value

def capture(case, policy, scene_data):
    key = f'{case}-{policy}'
    folder = ROOT / 'runs/inspection' / key
    folder.mkdir(parents=True, exist_ok=True)
    inputs = [ROOT / 'data' / f'{policy}.net.xml', ROOT / 'runs' / f'{key}-17/routes.rou.xml', ROOT / 'runs' / f'{key}-17/additional.add.xml']
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    target = OUT / f'{key}.json.gz'
    if target.exists():
        cached = json.loads(gzip.decompress(target.read_bytes()))
        if cached['input_hashes'] == hashes and cached.get('step') == 1 and cached.get('scene_schema') == 2: return
    add = ET.parse(inputs[2])
    for element in list(add.getroot()):
        if element.tag == 'edgeData': add.getroot().remove(element)
    add.write(folder / 'stops.add.xml', encoding='utf-8', xml_declaration=True)
    fcd = folder / 'trajectory.xml.gz'
    cmd = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'), '--net-file', str(inputs[0]), '--route-files', str(inputs[1]), '--additional-files', str(folder / 'stops.add.xml'), '--begin', '0', '--end', str(END + 1), '--seed', '17', '--time-to-teleport', '-1', '--no-step-log', 'true', '--duration-log.disable', 'true', '--xml-validation', 'never', '--fcd-output', str(fcd), '--device.fcd.begin', str(START), '--device.fcd.period', '1', '--fcd-output.attributes', 'id,x,y,angle,speed,type,lane,pos', '--stop-output', str(folder / 'stops.xml')]
    run = subprocess.run(cmd, capture_output=True, text=True)
    (folder / 'capture.log').write_text(run.stdout + '\n' + run.stderr)
    if run.returncode: raise RuntimeError(run.stderr[-1500:])
    vehicles, ids, frames = [], {}, []
    lane_index = {ident: i for i, ident in enumerate(scene_data['lane_ids'])}
    with gzip.open(fcd, 'rb') as f:
        for _, el in ET.iterparse(f, events=['end']):
            if el.tag != 'timestep': continue
            t = float(el.get('time'))
            if START <= t <= END:
                rows = []
                for v in el:
                    idx = lane_index.get(policy + '|' + v.get('lane'), -1)
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
    save(f'{key}.json.gz', {'case': case, 'policy': policy, 'seed': 17, 'start': START, 'end': END, 'step': 1, 'scene_schema': 2,
                           'frames': frames, 'vehicles': vehicles, 'input_hashes': hashes,
                           'source': 'Native SUMO one-second FCD; front bumper coordinates; same original simulation step and inputs',
                           'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat()})

if __name__ == '__main__':
    data = scene()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        jobs = [executor.submit(capture, case, policy, data) for case in ['moderate', 'busy', 'residents'] for policy in ['baseline', 'restricted']]
        for job in jobs: job.result()
