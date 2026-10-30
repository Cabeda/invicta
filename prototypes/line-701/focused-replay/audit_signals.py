"""Trace the Combatentes controller to source observations without editing physics."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'prototypes/line-701/full'))
from trial_evidence import load_trial
OUT=Path(__file__).parent
CONTROL='joinedS_12514310100_12514324965_12514324966_3897692280_#1more'
source=load_trial(ROOT/'docs/research/701-bus-only-controls-2026-10-30/controls.json','v6-bus-only-existing-signals-60-s17')
net=ET.fromstring(source.payload('network.net.xml'))
edges={e.get('id'):e for e in net.findall('edge')}
nodes={n.get('id'):n for n in net.findall('junction')}
connections=[c for c in net.findall('connection') if c.get('tl')==CONTROL]
controlled_nodes={edges[c.get('from')].get('to') for c in connections}
original_ids=set()
for ident in controlled_nodes:
    originals=next((p.get('value') for p in nodes[ident].findall('param') if p.get('key')=='origId'),ident)
    original_ids.update(originals.split())
raw=ROOT/'prototypes/line-701/full/data/network.osm.xml.gz'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
network_manifest=json.loads((raw.parent/'network-manifest.json').read_text())
assert sha(raw)==network_manifest['archive_sha256']
location=net.find('location').attrib
transform=Transformer.from_crs('EPSG:4326',location['projParameter'],always_xy=True)
offset=[float(v) for v in location['netOffset'].split(',')]
def project(lon,lat):
    x,y=transform.transform(lon,lat)
    return [x+offset[0],y+offset[1]]
observations=[]
with gzip.open(raw,'rb') as stream:
    for _,node in ET.iterparse(stream,events=['end']):
        if node.tag=='node' and node.get('id') in original_ids:
            tags={t.get('k'):t.get('v') for t in node.findall('tag')}
            observations.append({'osm_node':node.get('id'),'lon':float(node.get('lon')),'lat':float(node.get('lat')),
                                 'point':project(float(node.get('lon')),float(node.get('lat'))),'tags':tags})
        if node.tag in ['node','way','relation']:node.clear()
asset_path=ROOT/'prototypes/line-701/data/porto-street-assets.geojson'
assets=json.loads(asset_path.read_text())
equipment=[]
for feature in assets['features']:
    props=feature['properties']
    if props.get('kind')!='signal_equipment':continue
    lon,lat=feature['geometry']['coordinates']
    point=project(lon,lat)
    if ((point[0]-1318)**2+(point[1]-1380)**2)**.5<=75:
        equipment.append({'objectid':props['objectid'],'installation':props['numero_instalacao'],
                          'equipment':props['equipamento'],'lon':lon,'lat':lat,'point':point,
                          'head_type':'unknown','movement_assignment':'unverified','timing':'unknown'})
logic=next(t for t in net.findall('tlLogic') if t.get('id')==CONTROL)
phases=[dict(p.attrib) for p in logic.findall('phase')]
movements=[]
for connection in connections:
    edge=edges[connection.get('from')]
    lane=next(l for l in edge.findall('lane') if l.get('index')==connection.get('fromLane'))
    index=int(connection.get('linkIndex'))
    movements.append({'link_index':index,'junction':edge.get('to'),'from_road':edge.get('id'),
                      'from_lane':lane.get('id'),'to_road':connection.get('to'),'street':edge.get('name'),
                      'movement':connection.get('dir'),'point':[float(v) for v in lane.get('shape').split()[-1].split(',')],
                      'incoming_lane_length_metres':float(lane.get('length')),
                      'green_phase_indices':[i for i,p in enumerate(phases) if p['state'][index] in 'Gg']})
serial={}
for direction,reference in source.reference['directions'].items():
    pairs=set(zip(reference['path'],reference['path'][1:]))
    serial[direction]=sorted([m for m in movements if (m['from_road'],m['to_road']) in pairs],
                             key=lambda m:reference['path'].index(m['from_road']))
report={'schema':'invicta.signal-mapping-audit.v1','role':'source_to_model_audit_not_a_corrected_controller',
        'network_sha256':source.identity['network_sha256'],'source_execution_sha256':source.identity['execution_sha256'],
        'source_chain':{'osm_archive_sha256':sha(raw),'osm_role':'Community map observations via public OSM API; not a Porto municipal signal plan',
                        'municipal_review_layer_sha256':sha(asset_path),'municipal_sources':assets['sources'],
                        'municipal_layer_route_screen_metres':assets['screen_distance_metres'],
                        'municipal_local_selection_radius_metres':75,
                        'municipal_role':'Equipment-location review layer; not consumed by priority_model.py to generate signal control',
                        'coordinate_rule':'GeoJSON longitude/latitude transformed by the native projection and netOffset','native_projection':location},
        'official_equipment_within_75_metres':equipment,'osm_nodes_under_joined_controller':observations,
        'controller':{'id':CONTROL,'type':logic.get('type'),'offset_seconds':float(logic.get('offset')),
                      'represented_junctions':sorted(controlled_nodes),'movement_links':len(movements),
                      'incoming_lanes':len({m['from_lane'] for m in movements}),'green_stages':sum(any(c in 'Gg' for c in p['state']) for p in phases),
                      'phase_count':len(phases),'nominal_phase_duration_sum_seconds':sum(float(p['duration']) for p in phases),
                      'actual_cycle_duration':'Variable under generated actuation, not a measured 288-second cycle',
                      'synchronisation':'One generated joined programme; real phase groups, offsets and adjacent coordination unverified',
                      'phases':phases,'movements':sorted(movements,key=lambda m:m['link_index'])},
        'scheduled_route_links_under_controller':serial,
        'user_observation':{'scope':'Pictured Costa Cabral stretch','displayed_markers':8,'expected_vehicle_lights':2,
                            'status':'User-reported physical count; not yet assigned to source equipment objects or native approach stop lines'},
        'conclusion':'The viewer displayed logical movement links as coloured markers. Neither the official inventory nor OSM tags establishes one-to-one vehicle signal-head mapping. Inbound meets three controlled road transitions under this joined programme; serial control requires review before punctuality attribution.',
        'field_validated':False,'native_inputs_changed':False,'implementation_sha256':sha(Path(__file__))}
path=OUT/'signal-audit.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'signal-audit-index.json').write_text(json.dumps({'schema':'invicta.signal-audit-index.v1','sha256':sha(path),'network_sha256':report['network_sha256']},indent=2)+'\n')
print(json.dumps({'municipal_equipment':len(equipment),'installations':sorted({e['installation'] for e in equipment}),
                  'osm_signalised_crossings':sum(o['tags'].get('crossing')=='traffic_signals' for o in observations),
                  'model_movement_links':len(movements),'native_inputs_changed':False,'inbound_link_indices':[m['link_index'] for m in serial['1']]}))
