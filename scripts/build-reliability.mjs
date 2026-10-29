import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {evaluatePunctuality,minimumChangeProposal} from '../web/punctuality.mjs';
const [input,output]=process.argv.slice(2);
if(!input||!output)throw Error('Usage: node scripts/build-reliability.mjs INPUT OUTPUT');
const bytes=await readFile(input),raw=JSON.parse(bytes),directions={};
const expected=new Set(Object.values(raw.route_reference.directions).flatMap(r=>r.trips.map(t=>t.id)));
const required=raw.meta.cases.flatMap(c=>raw.meta.seeds.map(s=>c+'|'+s));
const length=new Map(raw.geometry.map(e=>[e.id,e.shape.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-e.shape[i][0],p[1]-e.shape[i][1]),0)]));
const changes=raw.access.changes,changedLaneMetres=changes.every(c=>length.has(c.edge))?Math.round(changes.reduce((n,c)=>n+length.get(c.edge),0)):null;
for(const run of raw.runs){
 if(run.buses.length!==expected.size||new Set(run.buses.map(b=>b.id)).size!==expected.size||run.buses.some(b=>!expected.has(b.id)))throw Error('Native run does not retain every scheduled trip');
 for(const direction of Object.keys(raw.route_reference.directions)){
  directions[direction]??={};directions[direction][run.case]??={};
  const all=raw.runs.filter(r=>r.case===run.case&&r.variant===run.variant).flatMap(r=>r.buses.filter(b=>b.direction===direction));
  directions[direction][run.case][run.variant]=evaluatePunctuality(all);
 }
}
const packages=['baseline','restricted'].map(id=>({id,changedLaneMetres:id==='baseline'?0:changedLaneMetres,changeCount:id==='baseline'?0:changes.length,cases:raw.runs.filter(r=>r.variant===id).map(run=>{
 const baseline=raw.runs.find(r=>r.variant==='baseline'&&r.case===run.case&&r.seed===run.seed);
 return {id:run.case+'|'+run.seed,metrics:evaluatePunctuality(run.buses),demandComparable:!!baseline&&run.inputs.demand===baseline.inputs.demand,extraUnserved:baseline?Object.keys(run.groups).reduce((sum,g)=>sum+Math.max(0,run.groups[g].unserved-baseline.groups[g].unserved),0):Infinity};
})}));
const value={schema:'invicta.reliability.v1',line:String(raw.meta.route),serviceDate:raw.meta.service_date,sourceSha256:createHash('sha256').update(bytes).digest('hex'),goal:{lateToleranceSeconds:0,earlyDeparturesAllowed:false,allScheduledTripsRequired:true},directions,decision:minimumChangeProposal(packages,required),validation:{trafficCalibrated:false,signalsVerified:false,fleetBlocksAvailable:false},changeMeasure:'Approximate directed lane length in mapped SUMO geometry; not a financial estimate.'};
await writeFile(output,JSON.stringify(value,null,2)+'\n');
console.log('Published endpoint punctuality and minimum-change decision:',value.decision.status);
