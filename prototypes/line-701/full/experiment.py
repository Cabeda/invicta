"""Run the complete bidirectional 701 service day in native SUMO, not a timetable proxy."""
from pathlib import Path
import argparse, collections, concurrent.futures, functools, hashlib, json, math, random, statistics, subprocess, time
import xml.etree.ElementTree as ET
import sumo,sumolib
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';RUNS=ROOT/'runs';RUNS.mkdir(exist_ok=True)
ALLOWED='bus taxi bicycle motorcycle custom1 emergency authority pedestrian'
CLASSES={'through':'passenger','background':'passenger','crossing':'passenger','resident':'custom1','taxi':'taxi','motorcycle':'motorcycle','bicycle':'bicycle'}
HOURLY={'moderate':{'through':600,'background':900,'crossing':180,'resident':120,'taxi':70,'motorcycle':100,'bicycle':45},'busy':{'through':1200,'background':1350,'crossing':260,'resident':120,'taxi':90,'motorcycle':140,'bicycle':60}}
BEGIN=18000;ORIGIN_LEAD=30;DWELL=20

def digest(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def write_xml(path,value):ET.ElementTree(value).write(path,encoding='utf-8',xml_declaration=True)
@functools.lru_cache(None)
def route(net,a,b,kind='passenger'):
    edges,cost=net.getFastestPath(net.getEdge(a),net.getEdge(b),vClass=kind)
    return ([e.getID() for e in edges],cost) if edges else (None,None)

def pools(net,directions):
    target=DATA/'od-pools.json';fingerprint=digest(DATA/'baseline.net.xml')
    if target.exists():
        value=json.loads(target.read_text())
        if value.get('network_sha256')==fingerprint:return value['pools']
    route_edges=set(e for d in directions.values() for e in d['path']);near={}
    for d in directions.values():
        for stop in d['stops']:
            for edge,_ in net.getNeighboringEdges(*stop['point'],650,includeJunctions=False):
                if edge.allows('passenger') and edge.getLength()>30:near[edge.getID()]=edge
    candidates=list(near);rng=random.Random(701);result={'through':[],'background':[],'resident':[],'crossing':[]}
    for _ in range(3000):
        a,b=rng.sample(candidates,2);path,cost=route(net,a,b)
        if not path or cost<30:continue
        pair=[a,b]
        if len(result['background'])<100:result['background'].append(pair)
        if any(e in route_edges for e in path) and len(result['through'])<80:result['through'].append(pair)
        if len(result['resident'])<80 and route(net,a,b,'custom1')[0]:result['resident'].append(pair)
        if min(map(len,[result['background'],result['resident']]))>=80 and len(result['through'])>=80:break
    for eid in route_edges:
        edge=net.getEdge(eid)
        for node in [edge.getFromNode(),edge.getToNode()]:
            for a in node.getIncoming():
                for b in node.getOutgoing():
                    if a.getID() in route_edges or b.getID() in route_edges or not a.allows('passenger') or not b.allows('passenger') or a==b:continue
                    path,cost=route(net,a.getID(),b.getID())
                    if path and cost<180 and len(result['crossing'])<120:result['crossing'].append([a.getID(),b.getID()])
    for key,values in result.items():
        result[key]=list(dict.fromkeys(map(tuple,values)))
        if not result[key]:raise RuntimeError('Empty full-network demand pool '+key)
    write_json(target,{'network_sha256':fingerprint,'source':'Generated regional OD pairs near all110 stops; not observed trip purposes, population or traffic counts','pools':result});print('Full-route OD pools',{k:len(v) for k,v in result.items()},flush=True);return result

def policy(base,directions,od):
    xml=ET.parse(DATA/'baseline.net.xml');lanes={l.get('id'):l for l in xml.getroot().iter('lane')};changes={}
    for eid in dict.fromkeys(e for d in directions.values() for e in d['path']):
        edge=base.getEdge(eid)
        if any(l.allows('bus') and not l.allows('passenger') for l in edge.getLanes()):continue
        lane=next((l for l in edge.getLanes() if l.allows('bus') and l.allows('passenger')),None)
        if lane is not None:changes[eid]={'edge':eid,'lane':lane.getID(),'street':edge.getName(),'general_lanes_retained':sum(l.allows('passenger') for l in edge.getLanes() if l!=lane)}
    original={ident:dict(l.attrib) for ident,l in lanes.items()};target=DATA/'restricted.net.xml';pairs=list(dict.fromkeys(tuple(p) for k in ['through','background','crossing'] for p in od[k]));kept=[]
    def make():
        for ident,lane in lanes.items():lane.attrib.clear();lane.attrib.update(original[ident])
        for change in changes.values():lane=lanes[change['lane']];lane.attrib.pop('disallow',None);lane.set('allow',ALLOWED)
        write_xml(target,xml.getroot());return sumolib.net.readNet(str(target),maxcache=0)
    candidate=make()
    for a,b in pairs:
        if route(candidate,a,b)[0]:continue
        baseline_path,_=route(base,a,b)
        for eid in baseline_path:
            if eid in changes:kept.append(changes.pop(eid))
    candidate=make();losses=[];detours=[]
    for a,b in pairs:
        before,before_cost=route(base,a,b);after,after_cost=route(candidate,a,b)
        if not after:losses.append([a,b])
        else:detours.append(after_cost-before_cost)
    if losses:raise RuntimeError('Combined full-route candidate disconnects screened OD pairs')
    screen={'tested_pairs':len(pairs),'newly_unroutable':len(losses),'mean_static_detour_seconds':statistics.mean(detours) if detours else None,'max_static_detour_seconds':max(detours) if detours else None,'changes':list(changes.values()),'general_traffic_retained':kept,'status':'Generated regional OD connectivity screen; not a driveway/loading/legal-access survey.'}
    write_json(DATA/'access-screen.json',screen);print('Combined bidirectional policy:',len(changes),'priority edges;',len(kept),'general edges retained',flush=True);return candidate,screen

def demand(case,seed,od,last_origin):
    rng=random.Random(seed);values=[];counts=HOURLY['busy' if case=='late' else case]
    for hour in range(BEGIN//3600,math.ceil(last_origin/3600)):
        weight=1 if hour in [7,8,16,17,18] else .65 if 9<=hour<=20 else .35
        start=max(BEGIN,hour*3600);end=min(last_origin,(hour+1)*3600)
        if end<=start:continue
        for group,rate in counts.items():
            pool=od['through' if group in ['taxi','motorcycle','bicycle'] else group]
            for i in range(round(rate*weight*(end-start)/3600)):
                a,b=rng.choice(pool);values.append({'id':f'{group}_{hour}_{i}','group':group,'kind':CLASSES[group],'from':a,'to':b,'depart':rng.uniform(start,end)})
    return values

def simulate(net,reference,people,case,variant,seed,end_time):
    start_clock=time.monotonic();folder=RUNS/f'{case}-{variant}-{seed}';folder.mkdir(exist_ok=True)
    inputs={'network':digest(DATA/f'{variant}.net.xml'),'reference':digest(DATA/'routes.json'),'demand':hashlib.sha256(json.dumps(people,sort_keys=True).encode()).hexdigest(),'case':case,'seed':seed,'begin':BEGIN,'end':end_time,'origin_lead':ORIGIN_LEAD,'dwell':DWELL,'schema':1}
    output=folder/'result.json'
    if output.exists():
        old=json.loads(output.read_text())
        if old.get('inputs')==inputs:
            from publication import native_inputs
            if old.get('native_inputs')==native_inputs(ROOT,case,variant,seed):
                print('Cached',case,variant,seed,flush=True);return old
            raise RuntimeError('Cached native run has missing or changed input binding; rerun in a fresh run folder')
    routes=ET.Element('routes');add=ET.Element('additional');events=[];unroutable=[]
    for group,kind in list(CLASSES.items())+[('bus','bus')]:
        attrs={'id':group,'vClass':kind,'sigma':'.5','speedDev':'.1'}
        if group=='resident':attrs['guiShape']='passenger'
        if group=='bicycle':attrs['maxSpeed']='5.5'
        if group=='bus':attrs.update(length='12',accel='1.2',decel='4.5',maxSpeed='13.89')
        ET.SubElement(routes,'vType',attrs)
    for person in people:
        path,_=route(net,person['from'],person['to'],person['kind'])
        if not path:unroutable.append(person['id']);continue
        vehicle=ET.Element('vehicle',id=person['id'],type=person['group'],depart=f"{person['depart']:.2f}",departLane='best',departSpeed='max');ET.SubElement(vehicle,'route',edges=' '.join(path));events.append(vehicle)
    buses=[t for d in reference['directions'].values() for t in d['trips']]
    shock=min((t for t in buses if t['direction']=='1' and t['depart']>=17*3600),key=lambda t:t['depart'])['id'] if case=='late' else None
    for direction in reference['directions'].values():
        for stop in direction['stops']:ET.SubElement(add,'busStop',id=stop['native_stop_id'],lane=stop['lane'],startPos=str(max(0,stop['pos']-15)),endPos=str(stop['pos']),name=stop['stop_name'],friendlyPos='true')
    for bus in buses:
        first=bus['stops'][0];delay=180 if bus['id']==shock else 0
        vehicle=ET.Element('vehicle',id=bus['id'],type='bus',line='701',depart=str(bus['depart']-ORIGIN_LEAD+delay),departLane=first['lane'].rsplit('_',1)[1],departPos=str(max(0,first['pos']-.1)),departSpeed='0')
        ET.SubElement(vehicle,'route',edges=' '.join(bus['path']))
        for stop in bus['stops']:
            attrs={'busStop':stop['native_stop_id'],'duration':str(DWELL),'arrival':str(stop['scheduled'])}
            if stop['designated_timing_point']:attrs['until']=str(stop['scheduled'])
            ET.SubElement(vehicle,'stop',attrs)
        events.append(vehicle)
    for event in sorted(events,key=lambda v:float(v.get('depart'))):routes.append(event)
    write_xml(folder/'routes.rou.xml',routes);write_xml(folder/'additional.add.xml',add)
    from publication import native_inputs
    bound_inputs=native_inputs(ROOT,case,variant,seed)
    from replay_scope import selection
    selection(net,reference,folder/'replay-edges.txt',DATA/f'{variant}.net.xml')
    cmd=[str(Path(sumo.SUMO_HOME)/'bin/sumo'),'--net-file',str(DATA/f'{variant}.net.xml'),'--route-files',str(folder/'routes.rou.xml'),'--additional-files',str(folder/'additional.add.xml'),'--begin',str(BEGIN),'--end',str(end_time),'--seed',str(seed),'--tripinfo-output',str(folder/'trips.xml'),'--tripinfo-output.write-unfinished','true','--tripinfo-output.write-undeparted','true','--stop-output',str(folder/'stops.xml'),'--stop-output.write-unfinished','true','--collision-output',str(folder/'collisions.xml'),'--time-to-teleport','-1','--no-step-log','true','--duration-log.disable','true','--xml-validation','never']
    if case!='bus_only_validation':cmd+=['--fcd-output',str(folder/'trajectory.xml.gz'),'--device.fcd.begin','60600','--device.fcd.period','5','--fcd-output.filter-edges.input-file',str(folder/'replay-edges.txt'),'--fcd-output.attributes','id,x,y,angle,speed,type,lane,pos','--fcd-output.skip-empty','false']
    print('Running full day',case,variant,seed,len(buses),'buses',len(people),'other requests',flush=True);process=subprocess.run(cmd,capture_output=True,text=True);(folder/'sumo.log').write_text(process.stdout+'\n'+process.stderr)
    if process.returncode:raise RuntimeError(process.stderr[-4000:])
    if case!='bus_only_validation':write_json(folder/'replay-trajectory.json',{'input_hashes':bound_inputs,'seed':seed,'simulation_begin':BEGIN,'start':60600,'end':66000,'step':5,'trajectory_sha256':digest(folder/'trajectory.xml.gz'),'selection_sha256':digest(folder/'replay-edges.txt'),'source':'Same full-day native execution as the numeric result'})
    calls=collections.defaultdict(dict)
    for event in ET.parse(folder/'stops.xml').getroot():calls[event.get('id')][event.get('busStop')]=event.attrib
    trip_rows={t.get('id'):t.attrib for t in ET.parse(folder/'trips.xml').getroot()};bus_results=[]
    for bus in buses:
        values=[]
        for stop in bus['stops']:
            call=calls[bus['id']].get(stop['native_stop_id']);arrival=float(call.get('started','-1')) if call else -1;departure=float(call.get('ended','-1')) if call else -1
            values.append({'stop_id':stop['stop_id'],'scheduled':stop['scheduled'],'arrival':arrival if arrival>=0 else None,'departure':departure if departure>=0 else None,'lateness':arrival-stop['scheduled'] if arrival>=0 else None,'dwell_and_hold':departure-arrival if arrival>=0 and departure>=0 else None})
        trip=trip_rows.get(bus['id'],{});complete=float(trip.get('arrival','-1'))>=0;entry=values[0]['lateness'];final=values[-1]['lateness']
        bus_results.append({'id':bus['id'],'trip_id':bus['trip_id'],'direction':bus['direction'],'stops':values,'completed':complete,'entry_lateness':entry,'final_lateness':final,'section_generated_delay':final-entry if final is not None and entry is not None else None,'section_seconds':values[-1]['arrival']-values[0]['arrival'] if final is not None and entry is not None else None})
    groups={}
    for group in list(CLASSES)+['bus']:
        rows=[row for row in trip_rows.values() if row.get('vType')==group];done=[r for r in rows if float(r.get('arrival','-1'))>=0];planned=len(buses) if group=='bus' else sum(p['group']==group for p in people)
        groups[group]={'planned':planned,'completed':len(done),'unserved':planned-len(done),'mean_duration':statistics.mean(float(r['duration']) for r in done) if done else None,'mean_depart_delay':statistics.mean(float(r['departDelay']) for r in done) if done else None}
    if native_inputs(ROOT,case,variant,seed)!=bound_inputs:raise RuntimeError('Native inputs changed during simulation')
    result={'case':case,'variant':variant,'seed':seed,'buses':bus_results,'groups':groups,'unroutable':len(unroutable),'collision_records':len(list(ET.parse(folder/'collisions.xml').getroot())),'inputs':inputs,'native_inputs':bound_inputs,'elapsed_seconds':time.monotonic()-start_clock,'shock_vehicle':shock,'native':True}
    if case!='bus_only_validation':result['replay_trajectory_sha256']=digest(folder/'trajectory.xml.gz')
    write_json(output,result);print('Finished',case,variant,seed,groups['bus']['completed'],'/',len(buses),'bus journeys;',round(result['elapsed_seconds'],1),'s',flush=True);return result

def run(cases,seeds):
    reference=json.loads((DATA/'routes.json').read_text());base=sumolib.net.readNet(str(DATA/'baseline.net.xml'),maxcache=0);od=pools(base,reference['directions']);candidate,screen=policy(base,reference['directions'],od)
    buses=[t for d in reference['directions'].values() for t in d['trips']];last_origin=max(t['depart'] for t in buses);end_time=max(s['scheduled'] for t in buses for s in t['stops'])+7200
    control=simulate(base,reference,[],'bus_only_validation','baseline',17,end_time)
    served=sum(c['arrival'] is not None for b in control['buses'] for c in b['stops'])
    if control['groups']['bus']['completed']!=reference['trip_count'] or served!=reference['served_calls']:raise RuntimeError('Full-route geometry control failed; traffic comparison is not published')
    timing_ids={d:{s['stop_id'] for s in r['stops'] if s['designated_timing_point']} for d,r in reference['directions'].items()}
    timed=[c for b in control['buses'] for c in b['stops'] if c['stop_id'] in timing_ids[b['direction']]]
    control_timing={'planned_calls':len(timed),'late_arrivals':sum(c['lateness'] is not None and c['lateness']>0 for c in timed),'missing_arrivals':sum(c['arrival'] is None for c in timed)}
    write_json(DATA/'geometry-validation.json',{'native':True,'working_count':reference['trip_count'],'completed_workings':control['groups']['bus']['completed'],'served_calls':served,'planned_served_calls':reference['served_calls'],'ordinary_traffic_requests':0,'inputs':control['inputs'],'timing_points':control_timing})
    requested={(case,seed):demand(case,seed,od,last_origin) for case in cases for seed in seeds}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        jobs=[executor.submit(simulate,net,reference,requested[case,seed],case,variant,seed,end_time) for case in cases for seed in seeds for variant,net in [('baseline',base),('restricted',candidate)]]
        results=[j.result() for j in jobs]
    return compile_results(reference,results,screen,base,cases,seeds)

def compile_results(reference,results,screen,base,cases,seeds):
    """Compile completed native runs without launching or changing an experiment."""
    buses=[t for d in reference['directions'].values() for t in d['trips']]
    end_time=max(s['scheduled'] for t in buses for s in t['stops'])+7200
    geometry=[{'id':e.getID(),'name':e.getName(),'shape':[list(p) for p in e.getShape()],'lanes':len(e.getLanes())} for e in base.getEdges()]
    all_route_edges=list(dict.fromkeys(e for d in reference['directions'].values() for e in d['path']))
    replay_edges=set(all_route_edges)
    for d in reference['directions'].values():
        for stop in d['stops']:replay_edges.update(e.getID() for e,_ in base.getNeighboringEdges(*stop['point'],350,includeJunctions=False))
    value={'route_reference':reference,'runs':results,'access':screen,'geometry':geometry,'buses':[dict(t,line='701') for t in buses],'route_edge_ids':all_route_edges,'replay_edge_ids':sorted(replay_edges),
      'meta':{'route':'701','directions':['1','0'],'service_date':reference['reference_date'],'begin':BEGIN,'end':end_time,'time_origin_seconds':0,'cases':cases,'seeds':seeds,'dwell_seconds':DWELL,'origin_lead_seconds':ORIGIN_LEAD,'sumo_version':subprocess.run([str(Path(sumo.SUMO_HOME)/'bin/sumo'),'--version'],capture_output=True,text=True).stdout.splitlines()[0],
       'traffic':'Synthetic regional OD requests with explicit hourly weights; not measured counts or calibrated population travel.','hourly_reference_rates':HOURLY,'hourly_weights':{'peak_7_8_16_17_18':1,'day_9_to_20':.65,'other':.35},'other_bus_routes_included':False,'vehicle_blocks':'Unavailable; each scheduled working is a separate native bus, no invented vehicle rotation.'}}
    write_json(ROOT/'results.json',value);print('Full bidirectional traffic results:',ROOT/'results.json',len(results),'native runs',flush=True);return value
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--cases',default='moderate,busy,late');parser.add_argument('--seeds',default='17');args=parser.parse_args();run(args.cases.split(','),[int(s) for s in args.seeds.split(',')])
