"""THROWAWAY native 701 route/segment experiments with explicit access screens."""
from pathlib import Path
import argparse, collections, concurrent.futures, functools, hashlib, importlib.util, json, math, random, statistics, subprocess
import xml.etree.ElementTree as ET
import sumo, sumolib
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; RUNS=ROOT/'runs';RUNS.mkdir(exist_ok=True)
LEGACY=ROOT.parent/'costa-cabral'
ALLOWED='bus taxi bicycle motorcycle custom1 emergency authority pedestrian'
DEMAND={
 'moderate':{'through':600,'background':900,'crossing':180,'resident':120,'taxi':70,'motorcycle':100,'bicycle':45},
 'busy':{'through':1200,'background':1350,'crossing':260,'resident':120,'taxi':90,'motorcycle':140,'bicycle':60},
 'late':{'through':1200,'background':1350,'crossing':260,'resident':120,'taxi':90,'motorcycle':140,'bicycle':60}}
CLASSES={'through':'passenger','background':'passenger','crossing':'passenger','resident':'custom1','taxi':'taxi','motorcycle':'motorcycle','bicycle':'bicycle'}
def write_xml(root,path):ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def run(cmd,log):
 p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True);log.write_text(p.stdout+'\n'+p.stderr)
 if p.returncode:raise RuntimeError(log.read_text()[-1800:])
@functools.lru_cache(None)
def path(net,a,b,kind='passenger'):
 p,c=net.getFastestPath(net.getEdge(a),net.getEdge(b),vClass=kind)
 return ([e.getID() for e in p],c) if p else (None,None)

def network(base,route,selected,name):
 patch=ET.Element('edges');changes=[]
 for eid in dict.fromkeys(e for segment in route['segments'] if segment['id'] in selected for e in segment['edges']):
  if eid in route.get('policy_excluded_edges',[]):continue
  edge=base.getEdge(eid);lanes=edge.getLanes()
  # Existing exclusive bus lanes already provide priority; do not take another lane.
  if any(l.allows('bus') and not l.allows('passenger') for l in lanes):continue
  lane=next((l for l in lanes if l.allows('bus') and l.allows('passenger')),None)
  if lane is None:continue
  e=ET.SubElement(patch,'edge',{'id':eid});ET.SubElement(e,'lane',{'index':str(lane.getIndex()),'allow':ALLOWED})
  changes.append({'edge':eid,'lane':lane.getID(),'street':edge.getName(),'general_lanes_retained':sum(l.allows('passenger') for l in lanes if l.getID()!=lane.getID())})
 target=DATA/f'{name}.net.xml';definition=DATA/f'{name}.edg.xml';write_xml(patch,definition)
 # Permission-only policies must not silently regenerate junctions, signals or geometry.
 # A no-change leg is byte-identical to the baseline, providing a neutral control.
 if not changes:target.write_bytes((DATA/'baseline.net.xml').read_bytes())
 else:
  xml=ET.parse(DATA/'baseline.net.xml');lookup={l.get('id'):l for l in xml.getroot().iter('lane')}
  for change in changes:
   lane=lookup[change['lane']];lane.attrib.pop('disallow',None);lane.set('allow',ALLOWED)
  xml.write(target,encoding='utf-8',xml_declaration=True)
 return sumolib.net.readNet(str(target),maxcache=0),changes

def access_pairs(base,route):
 pairs=set()
 for eid in route['path']:
  edge=base.getEdge(eid)
  for node in [edge.getFromNode(),edge.getToNode()]:
   incoming=[e for e in node.getIncoming() if e.allows('passenger')]
   outgoing=[e for e in node.getOutgoing() if e.allows('passenger')]
   for a in incoming:
    for b in outgoing:
     if a.getID()==b.getID():continue
     # No direct car access to an intentionally restricted address is treated as proof
     # that all vehicle flow must remain. Screen connector movements between side roads.
     if a.getID() in route['path'] or b.getID() in route['path']:continue
     p,c=path(base,a.getID(),b.getID())
     if p:pairs.add((a.getID(),b.getID()))
 # Add the same generated ordinary-traffic OD sample used by the earlier experiment.
 old=json.loads((DATA/'od-pools.json').read_text())
 for group in ['through','background','crossing']:
  for a,b in old[group]:
   if path(base,a,b)[0]:pairs.add((a,b))
 return sorted(pairs)

def screen(base,candidate,pairs):
 losses=[];detours=[]
 for a,b in pairs:
  p,c=path(base,a,b);q,d=path(candidate,a,b)
  if not q:losses.append({'from':a,'to':b,'from_street':base.getEdge(a).getName(),'to_street':base.getEdge(b).getName()})
  else:detours.append(d-c)
 return {'tested_pairs':len(pairs),'newly_unroutable':len(losses),'examples':losses[:12],
         'mean_static_detour_seconds':statistics.mean(detours) if detours else None,
         'max_static_detour_seconds':max(detours) if detours else None,
         'status':'Structural generated-OD screen only; not actual access demand, driveway survey or legal requirement.'}

def prepare_pools(net,route):
 """Keep valid frozen OD samples and add generated demand around the extension."""
 old=json.loads((LEGACY/'data/od-pools.json').read_text());pools={}
 for group in ['through','background','resident','crossing']:
  kind='custom1' if group=='resident' else 'passenger'
  pools[group]=[p for p in old[group] if all(net.hasEdge(e) for e in p) and path(net,*p,kind)[0]]
 marque=next(s for s in route['stops'] if s['stop_id']=='MPL4');south_route=set(route['path'][marque['path_index']:])
 south=[e for e in net.getEdges() if e.allows('passenger') and e.getLength()>35 and e.getShape()[0][1]<marque['point'][1]+80
        and min(math.dist(e.getShape()[0],s['point']) for s in route['stops'][12:])<650]
 rng=random.Random(701);new={'through':[],'background':[],'resident':[],'crossing':[]}
 for _ in range(1800):
  if len(south)<2:break
  a,b=rng.sample(south,2);p,c=path(net,a.getID(),b.getID())
  if not p or c<15:continue
  pair=[a.getID(),b.getID()]
  if len(new['background'])<60 and pair not in new['background']:new['background'].append(pair)
  if any(e in south_route for e in p) and len(new['through'])<60 and pair not in new['through']:new['through'].append(pair)
  if len(new['background'])>=60 and len(new['through'])>=60:break
 for eid in route['path'][marque['path_index']:]:
  edge=net.getEdge(eid)
  for node in [edge.getFromNode(),edge.getToNode()]:
   for a in node.getIncoming():
    for b in node.getOutgoing():
     if a.getID() in route['path'] or b.getID() in route['path'] or not a.allows('passenger') or not b.allows('passenger'):continue
     p,c=path(net,a.getID(),b.getID())
     pair=[a.getID(),b.getID()]
     if p and c<90 and pair not in new['crossing']:new['crossing'].append(pair)
  for a in rng.sample(south,min(8,len(south))):
   pair=[a.getID(),eid]
   if path(net,*pair,'custom1')[0] and len(new['resident'])<60 and pair not in new['resident']:new['resident'].append(pair)
 for group in pools:
  pools[group]=list({tuple(p):p for p in pools[group]+new[group]}.values())
  if not pools[group]:raise RuntimeError('No generated OD pool for '+group)
 (DATA/'od-pools.json').write_text(json.dumps(pools,ensure_ascii=False,indent=2))
 (DATA/'demand-scope.json').write_text(json.dumps({'source':'Synthetic OD samples; valid legacy pairs plus generated pairs around Marquês–Bolhão, not measured demand.',
        'pool_sizes':{k:len(v) for k,v in pools.items()},'new_southern_pairs':{k:len(v) for k,v in new.items()}},indent=2))

def traffic(case,seed):
 pool=json.loads((DATA/'od-pools.json').read_text());rng=random.Random(seed);people=[]
 for group,count in DEMAND[case].items():
  candidates=pool['through'] if group in ['taxi','motorcycle','bicycle'] else pool[group]
  for i in range(count):
   a,b=rng.choice(candidates);people.append({'id':f'{group}_{i}','group':group,'kind':CLASSES[group],'from':a,'to':b,'depart':rng.uniform(0,3600)})
 return people

def simulate(net,route,case,variant,seed,people):
 folder=RUNS/f'{case}-{variant}-{seed}';folder.mkdir(exist_ok=True)
 routes=ET.Element('routes');add=ET.Element('additional');events=[];missing=[]
 for tid,kind in list(CLASSES.items())+[('bus','bus')]:
  attrs={'id':tid,'vClass':kind,'sigma':'0.5','speedDev':'0.1'}
  if tid=='resident':attrs['guiShape']='passenger'
  if tid=='bicycle':attrs['maxSpeed']='5.5'
  if tid=='bus':attrs.update({'length':'12','accel':'1.2','maxSpeed':'13.89'})
  ET.SubElement(routes,'vType',attrs)
 for person in people:
  edges,_=path(net,person['from'],person['to'],person['kind'])
  if not edges:missing.append(person['id']);continue
  v=ET.Element('vehicle',{'id':person['id'],'type':person['group'],'depart':f"{person['depart']:.2f}",'departLane':'best','departSpeed':'max'})
  ET.SubElement(v,'route',{'edges':' '.join(edges)});events.append(v)
 for stop in route['stops']:
  ET.SubElement(add,'busStop',{'id':stop['stop_id'],'lane':stop['lane'],'startPos':str(max(0,stop['pos']-15)),'endPos':str(stop['pos']),'name':stop['stop_name'],'friendlyPos':'true'})
 for bus in route['morning']:
  first=route.get('boundary_entry',bus['stops'][0]);launch_delay=180 if case=='late' else 0
  v=ET.Element('vehicle',{'id':bus['id'],'type':'bus','line':'701','depart':str(bus['depart']+launch_delay),
                        'departLane':first['lane'].rsplit('_',1)[1],'departPos':str(max(0,first['pos']-.1)),'departSpeed':'0'})
  ET.SubElement(v,'route',{'edges':' '.join(route['path'])})
  for stop in bus['stops']:
   attrs={'busStop':stop['stop_id'],'duration':'20','arrival':str(stop['scheduled'])}
   # Published non-timepoint seconds are references, not holding instructions.
   if stop['designated_timing_point']:attrs['until']=str(stop['scheduled'])
   ET.SubElement(v,'stop',attrs)
  events.append(v)
 for event in sorted(events,key=lambda e:float(e.get('depart'))):routes.append(event)
 ET.SubElement(add,'edgeData',{'id':'traffic','file':str(folder/'edges.xml'),'begin':'0','end':'5400','excludeEmpty':'true'})
 write_xml(routes,folder/'routes.rou.xml');write_xml(add,folder/'additional.add.xml')
 run([Path(sumo.SUMO_HOME)/'bin/sumo','--net-file',DATA/f'{variant}.net.xml','--route-files',folder/'routes.rou.xml','--additional-files',folder/'additional.add.xml','--begin','0','--end','5400','--seed',seed,'--tripinfo-output',folder/'trips.xml','--tripinfo-output.write-unfinished','true','--tripinfo-output.write-undeparted','true','--stop-output',folder/'stops.xml','--stop-output.write-unfinished','true','--collision-output',folder/'collisions.xml','--time-to-teleport','-1','--no-step-log','true','--duration-log.disable','true','--xml-validation','never'],folder/'sumo.log')
 calls=collections.defaultdict(dict)
 for stop in ET.parse(folder/'stops.xml').getroot():calls[stop.get('id')][stop.get('busStop')]=dict(stop.attrib)
 buses=[]
 for bus in route['morning']:
  observed=[]
  for stop in bus['stops']:
   call=calls[bus['id']].get(stop['stop_id'])
   if call and float(call.get('started','-1'))>=0:
    arrival=float(call['started']);departure=float(call.get('ended','-1'))
    observed.append({'stop_id':stop['stop_id'],'arrival':arrival,'departure':departure,'scheduled':stop['scheduled'],
                     'lateness':arrival-stop['scheduled'],'dwell_and_hold':departure-arrival if departure>=0 else None})
   else:observed.append({'stop_id':stop['stop_id'],'arrival':None,'departure':None,'scheduled':stop['scheduled'],'lateness':None})
  entry=observed[0]['lateness'];final=observed[-1]['lateness'];complete=final is not None
  buses.append({'id':bus['id'],'trip_id':bus['trip_id'],'stops':observed,'completed':complete,'entry_lateness':entry,'final_lateness':final,
                'section_generated_delay':final-entry if complete and entry is not None else None,
                'section_seconds':observed[-1]['arrival']-observed[0]['arrival'] if complete and observed[0]['arrival'] is not None else None})
 trips=list(ET.parse(folder/'trips.xml').getroot());groups={}
 for group in list(CLASSES)+['bus']:
  rows=[t for t in trips if t.get('vType')==group];done=[t for t in rows if float(t.get('arrival','-1'))>=0]
  planned=len(route['morning']) if group=='bus' else DEMAND[case][group]
  groups[group]={'planned':planned,'completed':len(done),'unserved':planned-len(done),
                 'mean_duration':statistics.mean(float(t.get('duration')) for t in done) if done else None,
                 'mean_depart_delay':statistics.mean(float(t.get('departDelay')) for t in done) if done else None}
 record={'case':case,'variant':variant,'seed':seed,'buses':buses,'groups':groups,'unroutable':len(missing),
         'collision_records':len(list(ET.parse(folder/'collisions.xml').getroot()))}
 (folder/'result.json').write_text(json.dumps(record,ensure_ascii=False))
 completed_lateness=[b['final_lateness'] for b in buses if b['completed']]
 print(case,variant,seed,'final late',round(statistics.mean(completed_lateness)) if completed_lateness else 'none completed','unserved',sum(g['unserved'] for g in groups.values()),flush=True)
 return record

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--scenario',type=Path);parser.add_argument('--quick',action='store_true');args=parser.parse_args()
 route=json.loads((DATA/'route.json').read_text())
 base=sumolib.net.readNet(str(DATA/'baseline.net.xml'),maxcache=0)
 prepare_pools(base,route)
 pairs=access_pairs(base,route)
 networks={'baseline':base};screens={};changes={};all_ids=[s['id'] for s in route['segments']]
 for segment in route['segments']:
  key=segment['id'];net,change=network(base,route,[key],key);networks[key]=net;changes[key]=change;screens[key]=screen(base,net,pairs)
 safe=[key for key in all_ids if screens[key]['newly_unroutable']==0]
 # Check the combined package as well: individual safety does not imply combined safety.
 while True:
  candidate,change=network(base,route,safe,'restricted');combined=screen(base,candidate,pairs)
  if not safe or combined['newly_unroutable']==0:break
  # Drop the leg whose removal resolves most package losses; this is a generated-OD heuristic.
  trials=[]
  for key in safe:
   test,_=network(base,route,[k for k in safe if k!=key],f'trial_{key}');trials.append((screen(base,test,pairs)['newly_unroutable'],key))
  safe.remove(min(trials)[1])
 networks['restricted']=candidate;changes['restricted']=change;screens['restricted']=combined
 networks['all_priority'],changes['all_priority']=network(base,route,all_ids,'all_priority');screens['all_priority']=screen(base,networks['all_priority'],pairs)
 if args.scenario:
  config=json.loads(args.scenario.read_text());selected=config.get('priority_segments',[])
  for field,expected in {'route':'701','direction_id':1,'start_stop':route['start'],'end_stop':route['end']}.items():
   if field in config and config[field]!=expected:raise RuntimeError(f'Policy {field} does not match this pilot')
  if any(k not in all_ids for k in selected):raise RuntimeError('Unknown route segment')
  networks['custom'],changes['custom']=network(base,route,selected,'custom');screens['custom']=screen(base,networks['custom'],pairs)
 (DATA/'access-screen.json').write_text(json.dumps({'pairs':pairs,'segments':screens,'candidate_priority_segments':safe,'changes':changes,**({'custom_priority_segments':selected} if args.scenario else {})},ensure_ascii=False,indent=2))
 cases=['moderate'] if args.quick else list(DEMAND);seeds=[17] if args.quick else [17,42,73]
 tasks=[]
 for case in cases:
  variants=['baseline','restricted','all_priority']
  if case=='busy':variants+=all_ids
  if args.scenario:variants+=['custom']
  for seed in seeds:
   people=traffic(case,seed)
   tasks += [(networks[v],route,case,v,seed,people) for v in variants]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:results=list(executor.map(lambda task:simulate(*task),tasks))
 geometry=[{'id':e.getID(),'name':e.getName(),'corridor':e.getID() in route['path'],'length':e.getLength(),'lanes':len(e.getLanes()),
            'car':e.allows('passenger'),'shape':e.getShape()} for e in base.getEdges()]
 nodes={base.getEdge(e).getFromNode().getID() for e in route['path']}|{base.getEdge(e).getToNode().getID() for e in route['path']}
 replay_edges={e.getID() for e in base.getEdges() if e.getFromNode().getID() in nodes or e.getToNode().getID() in nodes}
 output={'route':route,'runs':results,'access':json.loads((DATA/'access-screen.json').read_text()),'geometry':geometry,
         'buses':route['morning'],'route_edge_ids':route['path'],'replay_edge_ids':sorted(replay_edges),
         'meta':{'cases':DEMAND,'seeds':seeds,'service_date':route['study_date'],'route':'701','direction':1,'entry_delay_seconds':{'moderate':0,'busy':0,'late':180},
                 'dwell_seconds':20,'other_bus_routes_included':False,'traffic':'Synthetic; no observed traffic calibration',
                 'approach_lead_seconds':route.get('approach_lead_seconds',0),
                 'holding':'Designated MPL4 and 0BLRB timing points only; intermediate published seconds are not holding instructions'}}
 (ROOT/('quick-results.json' if args.quick else 'results.json')).write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')))
 print('Saved',len(results),'native runs; access-preserving candidate priority legs:',safe,flush=True)

if __name__=='__main__':main()
