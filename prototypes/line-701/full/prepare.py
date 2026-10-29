"""Freeze an expanded OSM import and map both complete official 701 directions."""
from pathlib import Path
import argparse, bisect, gzip, hashlib, json, math, shutil, subprocess
import xml.etree.ElementTree as ET
import sumo, sumolib
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';DATA.mkdir(exist_ok=True)
PILOT=ROOT.parent;LEGACY=PILOT.parent/'costa-cabral'
def digest(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def network(source):
    archive=DATA/'network.osm.xml.gz';manifest_file=DATA/'network-manifest.json';raw=DATA/'raw';raw.mkdir(exist_ok=True)
    if source:
        metadata=json.loads((source/'manifest.json').read_text());validation=json.loads((source/'validation.json').read_text())
        if not metadata['coverage_complete']:raise RuntimeError('Incomplete street acquisition')
        items={};sources=[]
        for tile in metadata['tiles']:
            name=tile.get('file') or tile.get('filename');path=source/name
            if digest(path)!=tile['sha256']:raise RuntimeError('Street source hash mismatch: '+str(path))
            for element in ET.parse(path).getroot():
                if element.tag in ['node','way','relation']:
                    key=element.tag,element.get('id');old=items.get(key)
                    if old is None or int(element.get('version','0'))>int(old.get('version','0')):items[key]=element
            sources.append({**tile,'file':name})
        merged=ET.Element('osm',version='0.6',generator='Invicta complete701 source merge')
        for kind in ['node','way','relation']:
            merged.extend(el for (tag,_),el in items.items() if tag==kind)
        with gzip.GzipFile(filename=str(archive),mode='wb',mtime=0) as f:f.write(ET.tostring(merged,encoding='utf-8',xml_declaration=True))
        write_json(manifest_file,{'source':'Official OpenStreetMap map API','licence':'ODbL © OpenStreetMap contributors','requested_bounds':metadata['requested_bounds'],'inputs':sources,'validation':validation,'archive_sha256':digest(archive)})
    manifest=json.loads(manifest_file.read_text());osm=raw/'osm-tile-0.xml'
    if digest(archive)!=manifest['archive_sha256']:raise RuntimeError('Frozen street archive hash mismatch')
    if not osm.exists() or hashlib.sha256(osm.read_bytes()).hexdigest()!=hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest():osm.write_bytes(gzip.decompress(archive.read_bytes()))
    target=DATA/'baseline.net.xml';key=digest(archive);overlay_file=DATA/'route-import-overlays.json';overlay_hash=digest(overlay_file)
    if target.exists() and manifest.get('import_source_sha256')==key and manifest.get('network_sha256')==digest(target) and manifest.get('route_overlay_sha256')==overlay_hash:return
    loc=ET.parse(LEGACY/'data/baseline.net.xml').getroot().find('location');offset=loc.get('netOffset').split(',')
    cmd=[str(Path(sumo.SUMO_HOME)/'bin/netconvert'),'--osm-files',str(osm),'--output-file',str(target),'--proj',loc.get('projParameter'),'--offset.disable-normalization','true','--offset.x',offset[0],'--offset.y',offset[1],
        '--keep-edges.in-geo-boundary',','.join(map(str,manifest['requested_bounds'])),'--geometry.remove','--ramps.guess','--junctions.join','--tls.guess-signals','--tls.discard-simple','--tls.join','--tls.default-type','actuated','--no-turnarounds','--output.street-names','true','--output.original-names','true','--osm.bike-access','true','--keep-edges.by-vclass','passenger,bus,taxi,bicycle,motorcycle']
    print('Importing complete regional street network…',flush=True);run=subprocess.run(cmd,capture_output=True,text=True);(DATA/'network-import.log').write_text(run.stdout+'\n'+run.stderr)
    if run.returncode:raise RuntimeError(run.stderr[-3000:])
    net=sumolib.net.readNet(str(target),maxcache=0);connections=ET.Element('connections');overlay=json.loads(overlay_file.read_text())
    for connection in overlay['connections']:
        a=next(l for l in net.getEdge(connection['from']).getLanes() if l.allows('bus'));b=next(l for l in net.getEdge(connection['to']).getLanes() if l.allows('bus'))
        ET.SubElement(connections,'connection',**{k:connection[k] for k in ['from','to','allow']},fromLane=str(a.getIndex()),toLane=str(b.getIndex()))
    conn_file=DATA/'raw/route-overlays.con.xml';ET.ElementTree(connections).write(conn_file,encoding='utf-8',xml_declaration=True)
    adjusted=DATA/'raw/adjusted.net.xml';run=subprocess.run([str(Path(sumo.SUMO_HOME)/'bin/netconvert'),'--sumo-net-file',str(target),'--connection-files',str(conn_file),'--output-file',str(adjusted)],capture_output=True,text=True)
    (DATA/'overlay-import.log').write_text(run.stdout+'\n'+run.stderr)
    if run.returncode:raise RuntimeError(run.stderr[-3000:])
    shutil.copy2(adjusted,target)
    manifest.update(network_sha256=digest(target),import_source_sha256=key,route_overlay_sha256=overlay_hash,route_overlay=overlay,projection=dict(ET.parse(target).getroot().find('location').attrib));write_json(manifest_file,manifest)

def map_direction(net,facts,coordinates):
    points=[list(net.convertLonLat2XY(p['lng'],p['lat'])) for p in sorted(coordinates,key=lambda p:p['sequence'])];lengths=[0]
    for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+math.dist(a,b))
    def point_at(progress):
        progress=min(max(0,progress),lengths[-1]);i=min(len(points)-2,max(0,bisect.bisect_right(lengths,progress)-1));a,b=points[i:i+2];span=lengths[i+1]-lengths[i];t=(progress-lengths[i])/span if span else 0
        return [a[k]+t*(b[k]-a[k]) for k in [0,1]]
    def heading_at(progress):
        a,b=point_at(progress-30),point_at(progress+30)
        return tuple(b[k]-a[k] for k in [0,1])
    def project(point):
        best=None
        for i,(a,b) in enumerate(zip(points,points[1:])):
            dx,dy=b[0]-a[0],b[1]-a[1];squared=dx*dx+dy*dy;t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/squared)) if squared else 0
            distance=math.dist(point,[a[0]+t*dx,a[1]+t*dy]);candidate=(distance,lengths[i]+t*math.sqrt(squared),i,(dx,dy))
            if best is None or distance<best[0]:best=candidate
        return best
    stops=[];direction=str(facts['direction_id'])
    for source in facts['stoplist']:
        point=list(net.convertLonLat2XY(source['stop_lon'],source['stop_lat']));p=project(point)
        stops.append({**source,'native_stop_id':f"d{direction}_{source['stop_id']}",'point':point,'shape_progress':p[1],'shape_distance':p[0]})
    if any(b['shape_progress']<=a['shape_progress'] for a,b in zip(stops,stops[1:])):raise RuntimeError('Official shape order mismatch')
    def snap(point,heading,is_stop=False):
        candidates=[];norm=math.hypot(*heading)
        # Regional matching requires the index, rather than a silent network scan.
        for edge,_ in net.getNeighboringEdges(*point,55,includeJunctions=False,allowFallback=False):
            # Crossings can split the correct road into 12–16 m fragments.
            # Keep enough room for the study's 12 m bus rather than forcing
            # a nominal 15 m stop onto a nearby, unrelated street.
            if edge.getFunction() or not edge.allows('bus') or edge.getLength()<(12.2 if is_stop else .05) or any(t in edge.getType() for t in ['motorway','trunk']):continue
            off,distance=sumolib.geomhelper.polygonOffsetAndDistanceToPoint(point,edge.getShape())
            if is_stop:
                off=min(max(12,off),edge.getLength()-.2);mapped=sumolib.geomhelper.positionAtShapeOffset(edge.getShape(),off);distance=math.dist(point,mapped)
                if distance>55:continue
            shape=edge.getShape();dx,dy=shape[-1][0]-shape[0][0],shape[-1][1]-shape[0][1];den=math.hypot(dx,dy)*norm;cosine=(dx*heading[0]+dy*heading[1])/den if den else -1
            if cosine<.05:continue
            candidates.append((distance+35*(1-cosine),distance,edge,off))
        if not candidates:raise RuntimeError(f'No native bus edge direction{direction} at {point}')
        return sorted(candidates,key=lambda c:c[0])[:6]
    anchors=[];last=-1e9;start,end=stops[0]['shape_progress'],stops[-1]['shape_progress']
    for i,p in enumerate(points):
        if start<lengths[i]<end and lengths[i]-last>22:
            heading=heading_at(lengths[i])
            if math.hypot(*heading):anchors.append((lengths[i],p,heading,None));last=lengths[i]
    anchors.extend((s['shape_progress'],s['point'],heading_at(s['shape_progress']),s) for s in stops);anchors.sort(key=lambda a:a[0])
    cache={};layers=[]
    def connect(a,b):
        ea,eb=a[2],b[2]
        if ea.getID()==eb.getID():return ([ea],max(0,b[3]-a[3])) if b[3]>=a[3]-5 else (None,math.inf)
        key=(ea.getID(),eb.getID())
        if key not in cache:cache[key]=net.getShortestPath(ea,eb,vClass='bus')
        path,distance=cache[key]
        return (path,max(0,distance-a[3]-(eb.getLength()-b[3]))) if path else (None,math.inf)
    for i,(progress,point,heading,stop) in enumerate(anchors):
        states=[]
        for candidate in snap(point,heading,stop is not None):
            if not layers:states.append((candidate[0]*2,None,[candidate[2]],candidate));continue
            best=None
            for j,previous in enumerate(layers[-1]):
                path,distance=connect(previous[3],candidate)
                if not path:continue
                expected=progress-anchors[i-1][0];score=previous[0]+candidate[0]*2+abs(distance-expected)*4+max(0,distance-expected-80)*12
                if best is None or score<best[0]:best=(score,j,path,candidate)
            if best:states.append(best)
        if not states:raise RuntimeError(f'No connected route match direction{direction} progress{progress}')
        layers.append(states)
    chosen=[None]*len(layers);j=min(range(len(layers[-1])),key=lambda i:layers[-1][i][0])
    for i in range(len(layers)-1,-1,-1):chosen[i]=layers[i][j];j=chosen[i][1]
    path=[];audit=[]
    for anchor,state in zip(anchors,chosen):
        _,point,_,stop=anchor;_,distance,edge,off=state[3]
        if not path:path=[edge.getID()]
        elif path[-1]!=edge.getID():path.extend(e.getID() for e in state[2][1:])
        if stop:
            lane=next(l for l in edge.getLanes() if l.allows('bus'));stop.update(edge=edge.getID(),lane=lane.getID(),pos=min(max(1,off),edge.getLength()-.2),path_index=len(path)-1,snap_distance=distance,street=edge.getName())
        audit.append({'progress':anchor[0],'edge':edge.getID(),'distance':distance})
    for a,b in zip(stops,stops[1:]):
        if a['path_index']==b['path_index'] and a['pos']>=b['pos']:raise RuntimeError('Mapped stop order reverses on a native lane')
    trips=[]
    for i,source in enumerate(facts['trips']):
        served=[{**s,'scheduled':source['stops'][s['stop_id']]} for s in stops if source['stops'][s['stop_id']] is not None]
        first,last=served[0],served[-1]
        trips.append({'id':f'd{direction}_bus_{i}','trip_id':source['trip_id'],'direction':direction,'depart':first['scheduled'],'stops':served,'path':path[first['path_index']:last['path_index']+1]})
    result={'direction':direction,'start':stops[0]['stop_id'],'end':stops[-1]['stop_id'],'stops':stops,'path':path,'shape':points,'shape_lengths':lengths,'trips':trips,'mapping_audit':audit,'shape_metres':lengths[-1]}
    print('Mapped direction',direction,len(stops),'stops',len(path),'edges',len(trips),'workings; max snap',round(max(s['snap_distance'] for s in stops),1),'m',flush=True)
    return result

def prepare(source=None):
    network(source);net=sumolib.net.readNet(str(DATA/'baseline.net.xml'),withInternal=True,maxcache=0)
    inbound=json.loads((PILOT/'data/official-extension/full-line-service-facts.json').read_text());outbound=json.loads((PILOT/'data/official-outbound/full-line-service-facts.json').read_text())
    inbound_shape=json.loads((PILOT/'data/official/inbound_shape.json').read_text())['coordinates']
    directions={'1':map_direction(net,inbound,inbound_shape),'0':map_direction(net,outbound,outbound['shape'])}
    value={'reference_date':inbound['reference_date'],'directions':directions,'network_sha256':digest(DATA/'baseline.net.xml'),'projection':dict(ET.parse(DATA/'baseline.net.xml').getroot().find('location').attrib),'served_calls':sum(len(t['stops']) for d in directions.values() for t in d['trips']),'trip_count':sum(len(d['trips']) for d in directions.values()),'time_origin_seconds':0,'limits':['Independent scheduled workings; physical bus blocks and turnarounds are unavailable.','OSM import and stop mapping are not a field survey.','Frozen 28 October timetable, geometry and regional OSM retrieved on their recorded source dates.']}
    write_json(DATA/'routes.json',value);return value
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--osm-source',type=Path);args=parser.parse_args();prepare(args.osm_source)
