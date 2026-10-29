import {evaluatePunctuality,minimumChangeProposal} from './punctuality.mjs';

function combine(metrics) {
  const result={planned:0,starts:{onTime:0,late:0,early:0,missing:0},finishes:{onTime:0,late:0,missing:0},bothOnTime:0,completed:0,passes:metrics.length>0&&metrics.every(m=>m.passes),toleranceSeconds:0,runs:metrics.length,scheduledTripsPerRun:metrics[0]?.planned??0};
  for(const m of metrics){result.planned+=m.planned;result.bothOnTime+=m.bothOnTime;result.completed+=m.completed;for(const key of Object.keys(result.starts))result.starts[key]+=m.starts[key];for(const key of Object.keys(result.finishes))result.finishes[key]+=m.finishes[key]}
  return result;
}

/** Evaluate native runs independently, then aggregate repeated scheduled trips by seed. */
export function evaluateStudy(raw) {
  const directions={},expectedTrips=Object.values(raw.route_reference.directions).flatMap((r)=>r.trips),expected=new Set(expectedTrips.map(t=>t.id));
  const required=raw.meta.cases.flatMap(c=>raw.meta.seeds.map(s=>c+'|'+s)),seen=new Set();
  const lengths=new Map(raw.geometry.map(e=>[e.id,e.shape.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-e.shape[i][0],p[1]-e.shape[i][1]),0)]));
  const changes=raw.access.changes,metres=changes.every(c=>lengths.has(c.edge))?Math.round(changes.reduce((n,c)=>n+lengths.get(c.edge),0)):null;
  for(const run of raw.runs){
    const key=run.case+'|'+run.variant+'|'+run.seed;if(seen.has(key))throw Error('Duplicate native case/policy/seed');seen.add(key);
    if(run.buses.length!==expected.size||new Set(run.buses.map(b=>b.id)).size!==expected.size||run.buses.some(b=>!expected.has(b.id)))throw Error('Native run does not retain every scheduled trip');
  }
  for(const [direction,route]of Object.entries(raw.route_reference.directions)){
    directions[direction]={};
    for(const scenario of raw.meta.cases){directions[direction][scenario]={};for(const policy of ['baseline','restricted']){
      const runs=raw.runs.filter(r=>r.case===scenario&&r.variant===policy);
      directions[direction][scenario][policy]=combine(runs.map(r=>evaluatePunctuality(r.buses.filter(b=>b.direction===direction),0,route.trips)));
    }}
  }
  const packages=['baseline','restricted'].map(id=>({id,changedLaneMetres:id==='baseline'?0:metres,changeCount:id==='baseline'?0:changes.length,cases:raw.runs.filter(r=>r.variant===id).map(run=>{
    const base=raw.runs.find(r=>r.variant==='baseline'&&r.case===run.case&&r.seed===run.seed),groups=Object.keys(run.groups);
    const comparable=!!base&&run.inputs.demand===base.inputs.demand&&groups.length===Object.keys(base.groups).length&&groups.every(g=>run.groups[g].planned===base.groups[g]?.planned);
    return {id:run.case+'|'+run.seed,metrics:evaluatePunctuality(run.buses,0,expectedTrips),demandComparable:comparable,extraUnserved:comparable?groups.reduce((sum,g)=>sum+Math.max(0,run.groups[g].unserved-base.groups[g].unserved),0):NaN};
  })}));
  return {directions,decision:minimumChangeProposal(packages,required)};
}
