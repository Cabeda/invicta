"""THROWAWAY Costa Cabral SUMO experiment. Synthetic demand; not a forecast."""
from pathlib import Path
import argparse, csv, io, json, math, random, statistics, subprocess, collections, datetime, hashlib, xml.etree.ElementTree as ET, zipfile, functools
from concurrent.futures import ThreadPoolExecutor
import sumolib, sumo

ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; RUNS=ROOT/'runs'; RUNS.mkdir(exist_ok=True)
CORRIDOR='Rua de Costa Cabral'; CLASSES={'through':'passenger','background':'passenger','crossing':'passenger','resident':'custom1','taxi':'taxi','motorcycle':'motorcycle','bicycle':'bicycle'}
CASES={'moderate':{'through':600,'background':900,'crossing':180,'resident':120,'taxi':70,'motorcycle':100,'bicycle':45},'busy':{'through':1200,'background':1350,'crossing':260,'resident':120,'taxi':90,'motorcycle':140,'bicycle':60},'residents':{'through':600,'background':900,'crossing':180,'resident':480,'taxi':70,'motorcycle':100,'bicycle':45}}
BEGIN=8*3600; DEMAND_END=3600; END=5400

def write_xml(root,path):ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def call(cmd,log):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True);log.write_text(r.stdout+'\n'+r.stderr)
 if r.returncode:raise RuntimeError(log.read_text()[-3500:])

def networks():
 base=DATA/'baseline.net.xml';n=sumolib.net.readNet(str(base),maxcache=0);cor={e.getID() for e in n.getEdges() if e.getName()==CORRIDOR}
 changes=ET.Element('edges')
 for eid in sorted(cor):ET.SubElement(changes,'edge',{'id':eid,'allow':'bus taxi bicycle motorcycle custom1 pedestrian'})
 patch=DATA/'restricted.edg.xml';write_xml(changes,patch)
 alt=DATA/'restricted.net.xml'
 call([Path(sumo.SUMO_HOME)/'bin/netconvert','--sumo-net-file',base,'--edge-files',patch,'--output-file',alt,'--no-turnarounds'],DATA/'restriction-import.log')
 return n,sumolib.net.readNet(str(alt),maxcache=0),cor

@functools.lru_cache(maxsize=None)
def route(n,a,b,vc):
 p,c=n.getFastestPath(n.getEdge(a),n.getEdge(b),vClass=vc)
 return [e.getID() for e in p] if p else None

def pools(n,cor):
 rng=random.Random(20261028);car=[e for e in n.getEdges() if e.allows('passenger') and e.getLength()>35 and e.getName()!=CORRIDOR and not any(x in e.getType() for x in ['motorway','trunk'])]
 local=[e for e in n.getEdges() if e.getID() in cor and e.allows('passenger') and e.getLength()>35]
 out={'through':[],'background':[],'resident':[],'crossing':[]}
 for k in range(2500):
  a,b=rng.sample(car,2)
  if math.dist(a.getShape()[0],b.getShape()[-1])<700:continue
  p=route(n,a.getID(),b.getID(),'passenger')
  if not p:continue
  length=sum(n.getEdge(x).getLength() for x in p)
  if not 800<length<5000:continue
  along=sum(n.getEdge(x).getLength() for x in p if x in cor)
  group='through' if along>500 else 'background'
  if len(out[group])<60:out[group].append((a.getID(),b.getID()))
  if len(out['through'])>=60 and len(out['background'])>=60:break
 for _ in range(250):
  a,b=rng.choice(local),rng.choice(car)
  if rng.random()<.5:a,b=b,a
  p=route(n,a.getID(),b.getID(),'custom1')
  if p and 300<sum(n.getEdge(x).getLength() for x in p)<4000:out['resident'].append((a.getID(),b.getID()))
  if len(out['resident'])>=60:break
 nodes={n.getEdge(e).getFromNode() for e in cor}|{n.getEdge(e).getToNode() for e in cor}
 for node in sorted(nodes,key=lambda x:x.getID()):
  ins=[e for e in node.getIncoming() if e.getID() not in cor and e.allows('passenger') and e.getLength()>10]
  outs=[e for e in node.getOutgoing() if e.getID() not in cor and e.allows('passenger') and e.getLength()>10]
  for a in ins:
   for b in outs:
    va=(a.getShape()[-1][0]-a.getShape()[0][0],a.getShape()[-1][1]-a.getShape()[0][1]);vb=(b.getShape()[-1][0]-b.getShape()[0][0],b.getShape()[-1][1]-b.getShape()[0][1]);den=math.hypot(*va)*math.hypot(*vb)
    if den and (va[0]*vb[0]+va[1]*vb[1])/den>.5:
     p=route(n,a.getID(),b.getID(),'passenger')
     if p and len(p)==2:out['crossing'].append((a.getID(),b.getID()))
 print('OD candidate pools:',{k:len(v) for k,v in out.items()},flush=True)
 if any(not v for v in out.values()):raise RuntimeError('A required demand pool is empty')
 return out

def timetable(n,cor):
 with zipfile.ZipFile(DATA/'raw/gtfs.zip') as z:
  def table(name):return list(csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig')))
  active={x['service_id'] for x in table('calendar_dates.txt') if x['date']=='20260902' and x['exception_type']=='1'}
  trips={x['trip_id']:x for x in table('trips.txt') if x['service_id'] in active};stops={x['stop_id']:x for x in table('stops.txt')};calls=collections.defaultdict(list)
  edges=[n.getEdge(x) for x in sorted(cor) if n.getEdge(x).allows('bus') and n.getEdge(x).getLength()>12]
  mapped={}
  for sid,s in stops.items():
   x,y=n.convertLonLat2XY(float(s['stop_lon']),float(s['stop_lat']));candidates=[]
   for e in edges:
    off,dist=sumolib.geomhelper.polygonOffsetAndDistanceToPoint((x,y),e.getShape())
    if dist<35:candidates.append((dist,off,e.getID()))
   if candidates:mapped[sid]=candidates
  for x in table('stop_times.txt'):
   if x['trip_id'] in trips and x['stop_id'] in mapped:calls[x['trip_id']].append(x)
 def secs(s):h,m,sec=map(int,s.split(':'));return h*3600+m*60+sec
 buses=[];requested=0;skipped=[]
 for tid,cs in calls.items():
  cs.sort(key=lambda x:int(x['stop_sequence']))
  if len(cs)<5 or not BEGIN<=secs(cs[0]['arrival_time'])<BEGIN+DEMAND_END:continue
  requested+=1;locations=[]
  for i,c in enumerate(cs):
   j=i+1 if i<len(cs)-1 else i-1;s=stops[c['stop_id']];other=stops[cs[j]['stop_id']]
   v=(float(other['stop_lon'])-float(s['stop_lon']),float(other['stop_lat'])-float(s['stop_lat']))
   if j<i:v=(-v[0],-v[1])
   candidates=[]
   for dist,off,eid in mapped[c['stop_id']]:
    e=n.getEdge(eid);lon0,lat0=n.convertXY2LonLat(*e.getShape()[0]);lon1,lat1=n.convertXY2LonLat(*e.getShape()[-1]);w=(lon1-lon0,lat1-lat0);den=math.hypot(*v)*math.hypot(*w);dot=(v[0]*w[0]+v[1]*w[1])/den if den else -1
    candidates.append((dist+80*(1-dot),eid,off))
   _,eid,off=min(candidates);e=n.getEdge(eid);lane=next(l for l in e.getLanes() if l.allows('bus'));pos=min(max(9,off),e.getLength()-1)
   locations.append({'sid':c['stop_id'],'name':s['stop_name'],'edge':eid,'lane':lane.getID(),'pos':pos,'scheduled':secs(c['arrival_time'])-BEGIN,'lon':float(s['stop_lon']),'lat':float(s['stop_lat'])})
  path=[];valid=True
  for a,b in zip(locations,locations[1:]):
   p=route(n,a['edge'],b['edge'],'bus')
   if not p:valid=False;break
   if not path:path=list(p)
   else:path.extend(p[1:])
  if not valid:skipped.append(tid);continue
  buses.append({'id':'bus_'+str(len(buses)),'trip_id':tid,'line':trips[tid]['route_id'],'depart':locations[0]['scheduled'],'stops':locations,'path':path})
 print('Timetable:',requested,'requested;',len(buses),'mapped;',len(skipped),'unmapped',flush=True)
 (DATA/'timetable.json').write_text(json.dumps({'service_date':'2026-09-02','time_window':'08:00–09:00','requested':requested,'mapped':len(buses),'skipped':skipped,'buses':buses},ensure_ascii=False,indent=2))
 return buses,requested,skipped

def demand(case,seed,pool):
 rng=random.Random(seed);people=[]
 for group,count in CASES[case].items():
  pp=pool['through'] if group in ['taxi','motorcycle','bicycle'] else pool[group]
  for i in range(count):
   a,b=rng.choice(pp);people.append({'id':f'{group}_{i}','group':group,'class':CLASSES[group],'from':a,'to':b,'depart':rng.uniform(0,DEMAND_END)})
 return people

def experiment(n,cor,case,policy,seed,people,buses):
 rid=f'{case}-{policy}-{seed}';folder=RUNS/rid;folder.mkdir(exist_ok=True);routes=ET.Element('routes');add=ET.Element('additional')
 for tid,vc,attrs in [('through','passenger',{}),('background','passenger',{}),('crossing','passenger',{}),('resident','custom1',{'guiShape':'passenger'}),('taxi','taxi',{}),('motorcycle','motorcycle',{}),('bicycle','bicycle',{'maxSpeed':'5.5'}),('bus','bus',{'length':'12','accel':'1.2','maxSpeed':'13.89'})]:
  ET.SubElement(routes,'vType',{'id':tid,'vClass':vc,'sigma':'0.5','speedDev':'0.1',**attrs})
 events=[];unroutable=[];examples={};changed=0
 for person in people:
  path=route(n,person['from'],person['to'],person['class'])
  if not path:unroutable.append(person['id']);continue
  if policy=='restricted' and person['class']=='passenger' and any(e in cor for e in path):raise RuntimeError('A private through route entered the restricted corridor')
  if person['group'] not in examples:examples[person['group']]=path
  v=ET.Element('vehicle',{'id':person['id'],'type':person['group'],'depart':f"{person['depart']:.2f}",'departLane':'best','departSpeed':'max'});ET.SubElement(v,'route',{'edges':' '.join(path)});events.append(v)
 stop_ids=set()
 for bus in buses:
  v=ET.Element('vehicle',{'id':bus['id'],'type':'bus','line':bus['line'],'depart':str(bus['depart']),'departLane':'best','departSpeed':'max'});ET.SubElement(v,'route',{'edges':' '.join(bus['path'])})
  for st in bus['stops']:
   sid=st['sid']+'_'+st['edge'].replace('#','_').replace('-','m')
   if sid not in stop_ids:
    ET.SubElement(add,'busStop',{'id':sid,'lane':st['lane'],'startPos':f"{max(0,st['pos']-8):.2f}",'endPos':f"{st['pos']:.2f}",'name':st['name'],'friendlyPos':'true'});stop_ids.add(sid)
   ET.SubElement(v,'stop',{'busStop':sid,'duration':'20','arrival':str(st['scheduled']),'until':str(st['scheduled'])})
  events.append(v)
 for v in sorted(events,key=lambda x:float(x.get('depart'))):routes.append(v)
 ET.SubElement(add,'edgeData',{'id':'flows','file':str(folder/'edges.xml'),'begin':'0','end':str(END),'excludeEmpty':'true'})
 write_xml(routes,folder/'routes.rou.xml');write_xml(add,folder/'additional.add.xml')
 net=DATA/('baseline.net.xml' if policy=='baseline' else 'restricted.net.xml')
 cmd=[Path(sumo.SUMO_HOME)/'bin/sumo','--net-file',net,'--route-files',folder/'routes.rou.xml','--additional-files',folder/'additional.add.xml','--begin','0','--end',str(END),'--seed',str(seed),'--tripinfo-output',folder/'trips.xml','--tripinfo-output.write-unfinished','true','--tripinfo-output.write-undeparted','true','--stop-output',folder/'stops.xml','--stop-output.write-unfinished','true','--summary-output',folder/'summary.xml','--collision-output',folder/'collisions.xml','--time-to-teleport','-1','--no-step-log','true','--duration-log.disable','true','--xml-validation','never']
 call(cmd,folder/'sumo.log')
 infos=list(ET.parse(folder/'trips.xml').getroot());groups={}
 for g in list(CLASSES)+['bus']:
  rows=[x for x in infos if x.get('vType')==g];done=[x for x in rows if float(x.get('arrival','-1'))>=0];planned=len(buses) if g=='bus' else CASES[case][g]
  def avg(k):return statistics.mean(float(x.get(k,0)) for x in done) if done else None
  groups[g]={'planned':planned,'completed':len(done),'unserved':planned-len(done),'mean_duration':avg('duration'),'mean_depart_delay':avg('departDelay'),'mean_time_loss':avg('timeLoss'),'mean_distance':avg('routeLength')}
 bus_calls=collections.defaultdict(list)
 for st in ET.parse(folder/'stops.xml').getroot():bus_calls[st.get('id')].append(dict(st.attrib))
 lateness=[]
 for bus in buses:
  bs=bus_calls.get(bus['id'],[])
  if len(bs)>=len(bus['stops']):lateness.append(float(bs[-1].get('started','0'))-bus['stops'][-1]['scheduled'])
 groups['bus']['final_stop_completed']=len(lateness);groups['bus']['late_over_180']=sum(x>180 for x in lateness)+(len(buses)-len(lateness));groups['bus']['on_time_pct']=100*(sum(x<=180 for x in lateness))/len(buses) if buses else None;groups['bus']['mean_final_lateness']=statistics.mean(lateness) if lateness else None
 flow={}
 for interval in ET.parse(folder/'edges.xml').getroot():
  for e in interval:
   count=float(e.get('entered',0));flow[e.get('id')]={'entered':count,'speed':float(e.get('speed',0)),'timeLoss':float(e.get('timeLoss',0))}
 summary=list(ET.parse(folder/'summary.xml').getroot())[-1].attrib;collisions=len(list(ET.parse(folder/'collisions.xml').getroot()))
 result={'id':rid,'case':case,'policy':policy,'seed':seed,'groups':groups,'unroutable':len(unroutable),'collision_records':collisions,'end_summary':summary,'examples':examples,'flows':flow}
 (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False));print(rid,'bus',groups['bus']['completed'],'/',len(buses),'unserved',sum(x['unserved'] for x in groups.values()),'collisions',collisions,flush=True)
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');args=ap.parse_args()
 base,alt,cor=networks();pool=pools(base,cor);buses,requested,skipped=timetable(base,cor)
 if not buses:raise RuntimeError('No buses mapped')
 (DATA/'od-pools.json').write_text(json.dumps(pool))
 cases=['moderate'] if args.quick else list(CASES);seeds=[17] if args.quick else [17,42,73]
 tasks=[]
 for case in cases:
  for seed in seeds:
   people=demand(case,seed,pool)
   for policy,n in [('baseline',base),('restricted',alt)]:tasks.append((n,cor,case,policy,seed,people,buses))
 # Disable sumolib mutable partial-search caching; memoize only complete routes above.
 # This keeps route choices independent of worker query order. Each job owns its artifacts.
 with ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(lambda args:experiment(*args),tasks))
 geometry=[]
 for e in base.getEdges():
  if not any(e.allows(c) for c in ['passenger','bus','bicycle']):continue
  geometry.append({'id':e.getID(),'name':e.getName(),'corridor':e.getID() in cor,'length':round(e.getLength(),1),'lanes':len(e.getLanes()),'car':e.allows('passenger'),'shape':[[round(x,1),round(y,1)] for x,y in e.getShape()]})
 meta={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sumo_version':'1.28.0','service_date':'2026-09-02','traffic':'synthetic and uncalibrated','boundary':json.loads((DATA/'manifest.json').read_text())['bbox'],'cases':CASES,'seeds':seeds,'duration':DEMAND_END,'clearance':END-DEMAND_END,'gtfs_requested':requested,'gtfs_mapped':len(buses),'gtfs_skipped':skipped,'dwell_seconds':20,'lateness_threshold_seconds':180,'corridor_edges':len(cor),'normalized_carriageways':8,'resident_rule':'A synthetic permit is assigned only to trips with an origin or destination on a Costa Cabral edge. Crossing-only cars never use a Costa Cabral road edge.','signals':'Generated from OSM; not measured Porto timings.','lane_assumption':'Eight imported directed stretches normalized to one lane in each mapped direction, correcting an importer expansion of two marked lanes plus a contraflow lane. Survey required.'}
 # Municipal layers as context, never traffic observations.
 municipal={k:json.loads((DATA/'raw'/f).read_text()) for k,f in [('bus','bus_corridors.geojson'),('loading','loading.geojson')]}
 layers={}
 for key,obj in municipal.items():
  features=[]
  for f in obj['features']:
   coords=f['geometry']['coordinates'];lines=coords if f['geometry']['type']=='MultiLineString' else [coords]
   for line in lines:
    if not line or not isinstance(line[0],list):continue
    w,s,e,n=meta['boundary']
    if any(w<=p[0]<=e and s<=p[1]<=n for p in line):features.append({'shape':[[round(v,1) for v in base.convertLonLat2XY(p[0],p[1])] for p in line],'properties':f['properties']})
  layers[key]=features
 output={'meta':meta,'geometry':geometry,'municipal':layers,'buses':buses,'manifest':json.loads((DATA/'manifest.json').read_text()),'runs':results}
 (ROOT/'results.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')))
 print('Saved',ROOT/'results.json',flush=True)

if __name__=='__main__':main()
