"""Entire bidirectional 701 adapter; full-day results with a peak replay window."""
from pathlib import Path
import json,sys,sumolib
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from native_replay import ReplayStudy,prepare
from replay_scope import edges
LEGACY=ROOT.parents[1]/'costa-cabral'

def study(cases=None,seed=None):
    reference=json.loads((ROOT/'data/routes.json').read_text())
    net=sumolib.net.readNet(str(ROOT/'data/baseline.net.xml'),maxcache=0)
    route_edges=list(dict.fromkeys(e for route in reference['directions'].values() for e in route['path']));capture_edges,scene_edges=edges(net,reference)
    buses=[dict(trip,line='701',label=f"701 · {trip['depart']//3600:02}:{trip['depart']%3600//60:02} · {trip['stops'][0]['stop_id']} → {trip['stops'][-1]['stop_id']}") for route in reference['directions'].values() for trip in route['trips']]
    end=max(stop['scheduled'] for bus in buses for stop in bus['stops'])+7200
    points=[p for route in reference['directions'].values() for p in route['shape']]
    origin=[(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in [0,1]]
    inputs={'buses':buses,'route_edge_ids':route_edges,'replay_edge_ids':capture_edges,'scene_edge_ids':scene_edges,'scene_origin':origin}
    path=ROOT/'replay-inputs.json';path.write_text(json.dumps(inputs,ensure_ascii=False,separators=(',',':'))+'\n')
    if (ROOT/'results.json').exists():
        result=json.loads((ROOT/'results.json').read_text())
        cases=cases or result['meta']['cases'];seed=seed if seed is not None else result['meta']['seeds'][0]
        if seed not in result['meta']['seeds']:raise ValueError('Replay seed has no numeric native run')
        for row in result['geometry']:
            edge=net.getEdge(row['id']);row['bus_priority']=any(l.allows('bus') and not l.allows('passenger') for l in edge.getLanes())
        result['replay_edge_ids']=scene_edges;result['meta']['visual_buffer_metres']=150;(ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    scopes={d:{'direction':d,'from':route['start'],'to':route['end']} for d,route in reference['directions'].items()}
    return ReplayStudy(root=ROOT,id='line-701-full',results_file=path,begin=18000,start=60600,end=66000,seed=17 if seed is None else seed,cases=tuple(cases or ['moderate','busy','late']),
        dimensions_file=LEGACY/'data/vehicle-dimensions-3d.json',limit_scene_edges=True,frame_step=5,workers=1,trajectory_root=ROOT/'runs',compact_frames=True,
        scope={'route':'701','direction':'both','directions':scopes,'reference_date':reference['reference_date'],
               'service_day_begin':18000,'service_day_end':end,
               'description':'Entire 701 both directions; independent scheduled workings, regional synthetic traffic','visual_buffer_metres':150,'vehicle_coverage':'Native route roads and roads meeting their junctions; wider regional totals are numeric only'})
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--cases');parser.add_argument('--seed',type=int);args=parser.parse_args();prepare(study(args.cases.split(',') if args.cases else None,args.seed))
