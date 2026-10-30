"""Observe a frozen failing run without altering its demand, network or controller.

This supplementary replay never promotes a proposal or replaces its numeric run.
"""
import argparse,gzip,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'prototypes/line-701/full'))
import libsumo as sim
from trial_evidence import load_trial
from prefix_reproduction import set_option
OUT=Path(__file__).parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,default=ROOT/'docs/research/701-bus-only-controls-2026-10-30/controls.json')
parser.add_argument('--trial',default='v6-bus-only-existing-signals-60-s17')
args=parser.parse_args()
evidence=load_trial(args.source,args.trial if args.source.is_file() else None)
for name in ['network.net.xml','routes.rou.xml','additional.add.xml']:evidence.payload(name)
ref=evidence.reference['directions']['1'];start=next(s for s in ref['stops'] if s['stop_id']=='PLIM2')['path_index']
route=set(ref['path'][start:]);net=ET.fromstring(evidence.payload('network.net.xml'))
shape=lambda v:[[float(n) for n in p.split(',')[:2]] for p in v.split()]
points=[p for e in net.findall('edge') if e.get('id') in route for l in e.findall('lane') for p in shape(l.get('shape'))]
bounds=[min(p[0] for p in points)-130,min(p[1] for p in points)-130,max(p[0] for p in points)+130,max(p[1] for p in points)+130]
def inside(p):return bounds[0]<=p[0]<=bounds[2] and bounds[1]<=p[1]<=bounds[3]
lanes=[];by_lane={}
for e in net.findall('edge'):
 for l in e.findall('lane'):
  pts=shape(l.get('shape'))
  if not any(inside(p) for p in pts):continue
  row={'id':l.get('id'),'road':e.get('id'),'shape':pts,'width':float(l.get('width',3.2)),'name':e.get('name',''),'route':e.get('id') in route,'kind':e.get('function','road'),'pedestrian':l.get('allow')=='pedestrian'}
  lanes.append(row);by_lane[l.get('id')]=row
signals=[]
for c in net.findall('connection'):
 if not c.get('tl'):continue
 lane=by_lane.get(c.get('from')+'_'+c.get('fromLane'))
 if lane:signals.append({'tls':c.get('tl'),'index':int(c.get('linkIndex')),'point':lane['shape'][-1],'lane':lane['id']})
signals=list({(s['tls'],s['index']):s for s in signals}.values());tls=sorted({s['tls'] for s in signals})
features=[]  # No inherited scene may silently supply another model's footprint.
stops=[s for s in ref['stops'] if s['path_index']>=start]
windows=[{'id':'morning','trip':'d1_bus_1','label':'05:45 Codiceira → Bolhão','start':21900,'end':23040}, {'id':'evening','trip':'d1_bus_55','label':'19:45 Codiceira → Bolhão','start':73200,'end':74040}]
command=list(evidence.result['command']);run=OUT/'native';run.mkdir(exist_ok=False)
for flag,name in [('--net-file','network.net.xml'),('--route-files','routes.rou.xml'),('--additional-files','additional.add.xml')]:
 (run/name).write_bytes(evidence.payload(name));set_option(command,flag,run/name)
for flag,name in [('--tripinfo-output','trips.xml'),('--stop-output','stops.xml'),('--collision-output','collisions.xml'),('--save-state.files','final-state.xml')]:set_option(command,flag,run/name)
frames={w['id']:[] for w in windows};sim.start(command)
try:
 while sim.simulation.getTime()<float(command[command.index('--end')+1]):
  sim.simulationStep();now=int(sim.simulation.getTime());window=next((w for w in windows if w['start']<=now<=w['end']),None)
  if not window:continue
  ids=sim.vehicle.getIDList();vehicles=[]
  for ident in ids:
   point=sim.vehicle.getPosition(ident)
   if inside(point):vehicles.append([ident,round(point[0],3),round(point[1],3),round(sim.vehicle.getAngle(ident),2),round(sim.vehicle.getSpeed(ident),3)])
  focus=None
  if window['trip'] in ids:
   ident=window['trip'];focus={'lane':sim.vehicle.getLaneID(ident),'speed':sim.vehicle.getSpeed(ident),'wait':sim.vehicle.getWaitingTime(ident),'stopped':sim.vehicle.isStopped(ident),'next_signals':[list(v) for v in sim.vehicle.getNextTLS(ident)[:2]]}
  frames[window['id']].append({'time':now,'vehicles':vehicles,'signals':{t:sim.trafficlight.getRedYellowGreenState(t) for t in tls},'focus':focus})
finally:sim.close()
actual=[dict(c.attrib) for c in ET.parse(run/'stops.xml').getroot()];expected=evidence.calls()
if actual!=expected:raise ValueError('Observation replay changed native stop events; do not publish')
for name in ['network.net.xml','routes.rou.xml','additional.add.xml']:
 if (run/name).read_bytes()!=evidence.payload(name):raise ValueError('Input changed during capture')
trips=[dict(t.attrib) for t in ET.parse(run/'trips.xml').getroot() if t.tag=='tripinfo'];completed=sum(float(t.get('arrival',-1))>=0 for t in trips)
assert completed==127
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'role':'focused_observation_replay','qualified':False,'source':evidence.verified_identity(),'command':command,'native_stop_events_equal':True,'compared_stop_events':len(actual),'completed_scheduled_services':completed,'output_hashes':{n:sha(run/n) for n in ['stops.xml','trips.xml','collisions.xml','final-state.xml']},'capture_implementation_sha256':sha(Path(__file__)),'limits':['Bus-only diagnostic; no ordinary traffic or passengers.','Signal plans generated by SUMO, not surveyed municipal timing plans.','Buildings use frozen OSM footprints with mixed observed/estimated heights.','Playback samples actual native positions once per second; no future traffic forecast.']}
calls={(c['id'],c['busStop']):c for c in actual}
timing={w['trip']:[{'stop':stop['stop_name'],'scheduled':stop['scheduled'],'arrival':float(calls[w['trip'],stop['native_stop_id']]['started']),'departure':float(calls[w['trip'],stop['native_stop_id']]['ended']),'terminal':i==len(trip['stops'])-1} for trip in ref['trips'] if trip['id']==w['trip'] for i,stop in enumerate(trip['stops']) if i in [0,len(trip['stops'])-1] or stop['designated_timing_point']] for w in windows}
data={'bounds':bounds,'lanes':lanes,'signals':signals,'buildings':features,'stops':stops,'timing':timing,'windows':[{**w,'frames':frames[w['id']]} for w in windows],'manifest':manifest}
(OUT/'replay.json.gz').write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode(),mtime=0));(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'capture-index.json').write_text(json.dumps({'schema':'invicta.focused-replay.v1','replay_sha256':sha(OUT/'replay.json.gz'),'manifest_sha256':sha(OUT/'manifest.json')},indent=2)+'\n')
print(json.dumps({'frames':{k:len(v) for k,v in frames.items()},'lanes':len(lanes),'buildings':len(features),'matched_stop_events':len(actual),'services':completed}))
