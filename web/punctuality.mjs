/** @typedef {{stop_id:string,scheduled:number,arrival:number|null,departure:number|null}} StopCall */
/** @typedef {{id:string,trip_id:string,direction:string,completed:boolean,stops:StopCall[]}} ScheduledTrip */
/** @typedef {{planned:number,starts:{onTime:number,late:number,early:number,missing:number},finishes:{onTime:number,late:number,missing:number},bothOnTime:number,completed:number,passes:boolean,toleranceSeconds:number}} Reliability */
/** @param {unknown} value @returns {value is number} */
const observed=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0;

/** Evaluate each scheduled departure, retaining missing trips in the denominator.
 * @param {ScheduledTrip[]} trips @param {number} toleranceSeconds @param {ScheduledTrip[]} expectedTrips @returns {Reliability} */
export function evaluatePunctuality(trips,toleranceSeconds=0,expectedTrips=trips) {
  if(!Number.isFinite(toleranceSeconds)||toleranceSeconds<0)throw Error('Invalid punctuality tolerance');
  const expectedIds=new Set(expectedTrips.map(t=>t.id)),actual=new Map(trips.map(t=>[t.id,t]));
  if(expectedIds.size!==expectedTrips.length||actual.size!==trips.length||trips.some(t=>!expectedIds.has(t.id)))throw Error('Unexpected or duplicate scheduled trip');
  const result={planned:expectedTrips.length,starts:{onTime:0,late:0,early:0,missing:0},finishes:{onTime:0,late:0,missing:0},bothOnTime:0,completed:0,passes:false,toleranceSeconds};
  for(const expected of expectedTrips){
    const trip=actual.get(expected.id);
    if(!trip){result.starts.missing++;result.finishes.missing++;continue}
    const first=trip.stops[0],last=trip.stops.at(-1);
    if(!first||!last||!Number.isFinite(first.scheduled)||!Number.isFinite(last.scheduled))throw Error('A scheduled trip must retain its own origin and destination');
    const start=!observed(first.departure)?'missing':first.departure<first.scheduled?'early':first.departure>first.scheduled+toleranceSeconds?'late':'onTime';
    const finish=!observed(last.arrival)?'missing':last.arrival>last.scheduled+toleranceSeconds?'late':'onTime';
    result.starts[start]++;result.finishes[finish]++;if(trip.completed)result.completed++;
    if(start==='onTime'&&finish==='onTime'&&trip.completed)result.bothOnTime++;
  }
  result.passes=result.planned>0&&result.bothOnTime===result.planned;
  return result;
}

/** Rank only fully evaluated feasible packages; a tested winner is not a global optimum.
 * @param {{id:string,changedLaneMetres:number|null,changeCount:number,cases:{id:string,metrics:Reliability,demandComparable:boolean,extraUnserved:number}[]}[]} packages
 * @param {string[]} requiredCases */
export function minimumChangeProposal(packages,requiredCases) {
  if(!requiredCases.length||new Set(requiredCases).size!==requiredCases.length)throw Error('Required cases must be explicit and unique');
  const assessed=packages.map(plan=>{
    const missing=requiredCases.filter(id=>!plan.cases.some(c=>c.id===id));
    const reasons=[...(missing.length?['missing_cases']:[]),...(!plan.cases.length||plan.cases.some(c=>!c.metrics.passes)?['punctuality_goal_not_met']:[]),...(plan.cases.some(c=>!c.demandComparable)?['different_demand']:[]),...(plan.cases.some(c=>!Number.isFinite(c.extraUnserved))?['unknown_access_effect']:[]),...(plan.cases.some(c=>c.extraUnserved>0)?['access_worse']:[]),...(plan.changedLaneMetres===null||!Number.isFinite(plan.changedLaneMetres)||plan.changedLaneMetres<0?['unknown_change_cost']:[])];
    return {...plan,eligible:!reasons.length,reasons};
  });
  const eligible=assessed.filter(p=>p.eligible).sort((a,b)=>(a.changedLaneMetres??Infinity)-(b.changedLaneMetres??Infinity)||a.changeCount-b.changeCount||a.id.localeCompare(b.id));
  return {status:eligible.length?'qualified_among_tested':'no_qualifying_proposal',winner:eligible[0]?.id??null,globalOptimumProven:false,assessed};
}
