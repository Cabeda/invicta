"""Map the current official 701 inbound section, not a street-name selection."""
from pathlib import Path
import csv, datetime, gzip, hashlib, json, math, xml.etree.ElementTree as ET
import sumolib
ROOT = Path(__file__).resolve().parent
LEGACY = ROOT.parent/'costa-cabral'
DATA = ROOT/'data'

def seconds(text):
    h,m,s = map(int,text.split(':')); return h*3600+m*60+s
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare():
    facts = json.loads((DATA/'source-facts.json').read_text())
    net = sumolib.net.readNet(str(DATA/'baseline.net.xml'), maxcache=0)
    raw_shape = json.loads((DATA/'official/inbound_shape.json').read_text())['coordinates']
    points = [net.convertLonLat2XY(p['lng'],p['lat']) for p in sorted(raw_shape,key=lambda p:p['sequence'])]
    lengths=[0]
    for a,b in zip(points,points[1:]): lengths.append(lengths[-1]+math.dist(a,b))
    def project(point):
        best=None
        for i,(a,b) in enumerate(zip(points,points[1:])):
            dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
            f=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/den)) if den else 0
            x,y=a[0]+f*dx,a[1]+f*dy;distance=math.dist(point,(x,y))
            if best is None or distance<best[0]:best=(distance,lengths[i]+f*math.sqrt(den),i,(dx,dy))
        return best
    source_stops=facts['segment']['stops']
    stops=[]
    for stop in source_stops:
        x,y=net.convertLonLat2XY(stop['stop_lon'],stop['stop_lat']);pr=project((x,y))
        stops.append({**stop,'point':[x,y],'shape_progress':pr[1],'shape_distance':pr[0]})
    if any(b['shape_progress']<=a['shape_progress'] for a,b in zip(stops,stops[1:])):raise RuntimeError('Official shape/stop order does not agree')
    municipality=facts.get('municipality',{})
    entry_point=net.convertLonLat2XY(*municipality['entry_lonlat']) if municipality.get('entry_lonlat') else stops[0]['point']
    entry={'point':list(entry_point),'shape_progress':project(entry_point)[1],'is_boundary':True}
    start,end=entry['shape_progress'],stops[-1]['shape_progress']
    buses=[e for e in net.getEdges() if e.allows('bus') and e.getLength()>18 and not any(t in e.getType() for t in ['motorway','trunk'])]
    def snap(point, heading):
        candidates=[]
        norm=math.hypot(*heading)
        for edge in buses:
            off,dist=sumolib.geomhelper.polygonOffsetAndDistanceToPoint(point,edge.getShape())
            if dist>45:continue
            shape=edge.getShape();dx,dy=shape[-1][0]-shape[0][0],shape[-1][1]-shape[0][1]
            cosine=(dx*heading[0]+dy*heading[1])/(math.hypot(dx,dy)*norm) if norm and math.hypot(dx,dy) else -1
            if cosine<.1:continue
            candidates.append((dist+35*(1-cosine),dist,edge,off))
        if not candidates:raise RuntimeError(f'No bus edge for official route point {point}')
        return sorted(candidates,key=lambda x:x[0])[:5]
    anchors=[]
    # Shape vertices impose the actual route's turns between stops.
    last=-1e9
    for i,p in enumerate(points):
        if start<lengths[i]<end and lengths[i]-last>18:
            heading=(points[i+1][0]-p[0],points[i+1][1]-p[1]) if i+1<len(points) else project(p)[3]
            anchors.append((lengths[i],p,heading,None));last=lengths[i]
    for stop in [entry]+stops:anchors.append((stop['shape_progress'],stop['point'],project(stop['point'])[3],stop))
    anchors.sort(key=lambda x:x[0]);path=[];stop_indexes=[];audit=[]
    layers=[];route_cache={}
    def connection(a,b):
        ea,eb=a[2],b[2]
        if ea.getID()==eb.getID():
            return ([ea],max(0,b[3]-a[3])) if b[3]>=a[3]-12 else (None,math.inf)
        key=(ea.getID(),eb.getID())
        if key not in route_cache:
            part,_=net.getFastestPath(ea,eb,vClass='bus');route_cache[key]=part
        part=route_cache[key]
        if not part:return None,math.inf
        return part,max(0,sum(e.getLength() for e in part)-a[3]-(eb.getLength()-b[3]))
    for i,(progress,point,heading,stop) in enumerate(anchors):
        candidates=snap(point,heading);states=[]
        for candidate in candidates:
            emission=candidate[0]*2
            if not layers:states.append((emission,None,[candidate[2]],candidate));continue
            best=None
            for j,previous in enumerate(layers[-1]):
                part,length=connection(previous[3],candidate)
                if not part:continue
                expected=progress-anchors[i-1][0]
                penalty=abs(length-expected)*4 + max(0,length-expected-80)*12
                score=previous[0]+emission+penalty
                if best is None or score<best[0]:best=(score,j,part,candidate)
            if best:states.append(best)
        if not states:raise RuntimeError('No connected shape match')
        layers.append(states)
    selected=[None]*len(layers);choice=min(range(len(layers[-1])),key=lambda j:layers[-1][j][0])
    for i in range(len(layers)-1,-1,-1):
        selected[i]=layers[i][choice];choice=selected[i][1]
    for anchor,state in zip(anchors,selected):
        progress,point,heading,stop=anchor
        _,distance,edge,offset=state[3]
        if not path:path=[edge.getID()]
        elif path[-1]!=edge.getID():path.extend(e.getID() for e in state[2][1:])
        if stop:
            lane=next(l for l in edge.getLanes() if l.allows('bus'))
            stop.update({'edge':edge.getID(),'lane':lane.getID(),'pos':min(max(.1 if stop.get('is_boundary') else 15,offset),edge.getLength()-1),
                         'snap_distance':round(distance,2),'street':edge.getName(),'path_index':len(path)-1})
            if not stop.get('is_boundary'):stop_indexes.append(len(path)-1)
        audit.append({'shape_progress':progress,'edge':edge.getID(),'distance':distance})
    if len(stop_indexes)!=len(source_stops):raise RuntimeError('Incomplete mapped stop sequence')
    segments=[]
    for i,(a,b) in enumerate(zip(stops,stops[1:])):
        edges=path[a['path_index']:b['path_index']+1]
        # An edge shared by neighbouring stop intervals is assigned to the first.
        owned=[e for e in edges if not any(e in s['edges'] for s in segments)]
        if i==0 and a['edge'] not in owned:owned.insert(0,a['edge'])
        segments.append({'id':f'leg_{i+1:02}','index':i,'from':a['stop_id'],'to':b['stop_id'],
                         'from_name':a['stop_name'],'to_name':b['stop_name'], 'edges':owned,
                         'route_edges':edges,'shape_metres':round(b['shape_progress']-a['shape_progress'],1),
                         'streets':list(dict.fromkeys(net.getEdge(e).getName() for e in edges)),
                         'car_edges':sum(net.getEdge(e).allows('passenger') for e in owned),
                         'already_priority':sum(any(l.allows('bus') and not l.allows('passenger') for l in net.getEdge(e).getLanes()) for e in owned),
                         'multi_lane_edges':sum(len(net.getEdge(e).getLanes())>1 for e in owned)})
    route_shape=[list(points[i]) for i in range(len(points)) if start<=lengths[i]<=end]
    route_shape.insert(0,entry['point']);route_shape.append(stops[-1]['point'])
    approach_edges=path[:stops[0]['path_index']+1]
    approach_distance=sum(net.getEdge(e).getLength() for e in approach_edges)-entry['pos']-(net.getEdge(stops[0]['edge']).getLength()-stops[0]['pos'])
    approach_lead=max(1,math.ceil(max(0,approach_distance)/min(13.89,net.getEdge(entry['edge']).getSpeed())+3))
    morning=[]
    for i,trip in enumerate(facts['schedule']['morning']):
        calls={c['stop_id']:c for c in trip['stop_times']}
        morning.append({'id':f'bus_{i}','trip_id':trip['trip_id'],'line':'701',
                        'stops':[{**s,'sid':s['stop_id'],'name':s['stop_name'],'scheduled':seconds(calls[s['stop_id']]['arrival_time'])-28800,
                                  'scheduled_text':calls[s['stop_id']]['arrival_time']} for s in stops],
                        'depart':seconds(calls[stops[0]['stop_id']]['arrival_time'])-28800-approach_lead,'path':path})
    result={'route':'701','direction':1,'destination':'Bolhão','study_date':facts['service_date'],
            'start':stops[0]['stop_id'],'end':stops[-1]['stop_id'],'stops':stops,'segments':segments,'path':path,'shape':route_shape,
            'label':'Areosa → Bolhão','municipality':municipality,'boundary_entry':entry,'approach_lead_seconds':approach_lead,
            'approach_metres':round(approach_distance,2),'policy_excluded_edges':[entry['edge']],
            'full_shape':points,'shape_lengths':lengths,'shape_start':start,'shape_end':end,
            'morning':morning,'source_facts':facts,'network_sha256':digest(DATA/'baseline.net.xml'),
            'mapping_audit':audit,'mapping_note':'Shape-constrained bus route through current official stop sequence; mapped geometry is not field-validated.'}
    (DATA/'route.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print('701 inbound:',len(stops),'stops,',len(path),'network edges,',round(end-start),'m,',len(morning),'morning trips',flush=True)
    for stop in stops:print(stop['stop_id'],stop['stop_name'],stop['street'],stop['edge'],'snap',stop['snap_distance'],'m',flush=True)
    print('Streets:',list(dict.fromkeys(net.getEdge(e).getName() for e in path)),flush=True)
    return result

if __name__=='__main__':prepare()
