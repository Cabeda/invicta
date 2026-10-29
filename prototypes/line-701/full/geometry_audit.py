"""Repeatable source-shape geometry audit, including internal bus connectors."""
from pathlib import Path
import collections,datetime,hashlib,json,math,sumolib
ROOT=Path(__file__).resolve().parent

def digest(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()

def audit():
 P=ROOT/'data';raw=(P/'routes.json').read_bytes();f=json.loads(raw);net=sumolib.net.readNet(str(P/'baseline.net.xml'),withInternal=True,maxcache=0)
 report={'schema':'invicta.full701.route-geometry-audit.v1','routes_sha256':hashlib.sha256(raw).hexdigest(),'network_sha256':digest(P/'baseline.net.xml'),'directions':{}}
 for d,r in f['directions'].items():
  edges=[net.getEdge(e) for e in r['path']];normal=sum(e.getLength() for e in edges);internal=0;missing=[];ints=[]
  for a,b in zip(edges,edges[1:]):
   conns=a.getAllowedOutgoing('bus').get(b,[]);ip,cost=net.getInternalPath(conns,fastest=False)
   if ip is None:missing.append((a.getID(),b.getID()));cost=0
   internal+=cost;ints.append(cost)
  rows=[]
  for a,b in zip(r['stops'],r['stops'][1:]):
   ia,ib=a['path_index'],b['path_index'];std=sum(e.getLength() for e in edges[ia:ib+1])-a['pos']-(edges[ib].getLength()-b['pos']);il=sum(ints[ia:ib]);official=b['shape_progress']-a['shape_progress'];rows.append({'from':a['stop_id'],'to':b['stop_id'],'official_m':round(official,2),'normal_m':round(std,2),'internal_m':round(il,2),'combined_m':round(std+il,2),'difference_m':round(std+il-official,2),'ratio':round((std+il)/official,3),'edge_count':ib-ia+1})
  report['directions'][d]={'edge_count':len(edges),'official_m':r['shape_metres'],'normal_m':normal,'internal_m':internal,'combined_m':normal+internal,'combined_stop_to_stop_m':normal+internal-r['stops'][0]['pos']-(edges[-1].getLength()-r['stops'][-1]['pos']),'missing_bus_connections':missing,'internal_edge_ids_in_vehicle_path':[e.getID() for e in edges if e.getFunction()],'repeated_normal_edges':[(e,n) for e,n in collections.Counter(r['path']).items() if n>1],'intervals':rows,'max_anchor_snaps':sorted(r['mapping_audit'],key=lambda a:a['distance'],reverse=True)[:10],'key_stops':[{k:s[k] for k in ['stop_id','edge','lane','pos','snap_distance','street']} for s in r['stops'] if s['stop_id'] in ['ACO1','AA1','SBR1','ALXH2']]}
 out={'method':'Native normal and shortest permitted internal connector shapes sampled at <=10m; distances to the official polyline; continuous bound sample maximum +5m. Geometric screen, not a field survey.','directions':{}}
 for d,r in f['directions'].items():
  edges=[net.getEdge(e) for e in r['path']];native=[];samples=[]
  for i,e in enumerate(edges):
   parts=[e]
   if i+1<len(edges):
    ip,_=net.getInternalPath(e.getAllowedOutgoing('bus').get(edges[i+1],[]),fastest=False);parts+=ip or []
   for part in parts:
    shape=part.getShape();length=sum(math.dist(a,b) for a,b in zip(shape,shape[1:]));n=max(1,math.ceil(length/10))
    for k in range(n+1):
     point=sumolib.geomhelper.positionAtShapeOffset(shape,length*k/n);_,distance=sumolib.geomhelper.polygonOffsetAndDistanceToPoint(point,r['shape']);samples.append({'distance_m':distance,'edge':part.getID(),'xy':point})
    native.extend(shape)
  worst=max(samples,key=lambda x:x['distance_m']);reverse=[]
  for point,progress in zip(r['shape'],r['shape_lengths']):
   _,distance=sumolib.geomhelper.polygonOffsetAndDistanceToPoint(point,native);reverse.append({'distance_m':distance,'progress_m':progress})
  out['directions'][d]={'native_sample_count':len(samples),'max_native_to_official_m':worst['distance_m'],'max_native_to_official_edge':worst['edge'],'max_native_to_official_xy':worst['xy'],'samples_over_20m':sum(x['distance_m']>20 for x in samples),'samples_over_30m':sum(x['distance_m']>30 for x in samples),'max_official_vertex_to_native':max(reverse,key=lambda x:x['distance_m'])}
 for direction,result in out['directions'].items():
  result['conservative_continuous_lateral_bound_m']=result['max_native_to_official_m']+5
  report['directions'][direction]['lateral']=result
 a=net.getEdge('966302094#2');report['connector']={cls:[e.getID() for e in a.getAllowedOutgoing(cls)] for cls in ['bus','passenger','taxi','motorcycle','bicycle','custom1','emergency']}
 report.update(audited_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reference_date=f['reference_date'],working_count=f['trip_count'],served_call_count=f['served_calls'],reference_network_hash_match=f['network_sha256']==report['network_sha256'],mapper_source_sha256=digest(ROOT/'prepare.py'),bus_only_overlay=json.loads((P/'route-import-overlays.json').read_text()),audit_method=out['method'],limits=['Geometry screen, not a street survey.','Internal connection minima and sampled lateral distances are geometric estimates.','A source-supported bus-only exception still needs operator/legal validation.'])
 sources=[ROOT.parent/'data/official-extension/full-line-service-facts.json',ROOT.parent/'data/official-outbound/full-line-service-facts.json',ROOT.parent/'data/official/inbound_shape.json',ROOT.parent/'data/official-outbound/outbound_shape.json']
 report['source_reference_hashes']={str(p.relative_to(ROOT.parents[2])):digest(p) for p in sources}
 passed=report['reference_network_hash_match'] and '-477791560#1' in report['connector']['bus'] and '-477791560#1' not in report['connector']['passenger']
 for row in report['directions'].values():
  passed=passed and not row['missing_bus_connections'] and not row['internal_edge_ids_in_vehicle_path'] and not row['repeated_normal_edges'] and .9<row['combined_m']/row['official_m']<1.1 and row['lateral']['conservative_continuous_lateral_bound_m']<50
 report['status']='geometry_audit_passed' if passed else 'geometry_audit_failed'
 (P/'route-geometry-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if not passed:raise RuntimeError('Full route geometry audit failed; inspect data/route-geometry-audit.json')
 print('Both direction geometry audits passed',flush=True)
 return report

if __name__=='__main__':audit()
