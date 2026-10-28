// THROWAWAY fluid passenger/berth model. Scheduled references are inputs, not observations.
export const defaults={trip_id:'701_0_2|327|D1|T2|N2',delay_seconds:300,delay_stop:'origin',
 passengers_per_minute:.25,capacity:70,base_dwell:10,boarding_seconds:1.8,alighting_seconds:1,
 alight_fraction:.15,reference_dwell:20,recovery_per_leg:3,control:'schedule',headway_fraction:.5,target_lateness:0};

export function simulateService(facts,settings={}){
 const o={...defaults,...settings},stops=facts.stoplist,points=new Set(facts.timing_points.map(s=>s.stop_id));
 for(const key of ['delay_seconds','passengers_per_minute','capacity','base_dwell','boarding_seconds','alighting_seconds','alight_fraction','reference_dwell','recovery_per_leg','headway_fraction','target_lateness'])if(!Number.isFinite(o[key])||o[key]<0)throw Error('Invalid service assumption: '+key);
 if(o.alight_fraction>1||o.capacity<=0||o.headway_fraction>1||!['none','schedule','headway'].includes(o.control)||!facts.trips.some(t=>t.trip_id===o.trip_id))throw Error('Invalid service scenario');
 if(o.target_lateness!==0)throw Error('This pilot uses the requested strict zero-lateness goal');
 if(o.delay_stop!=='origin'&&!Number.isFinite(facts.trips.find(t=>t.trip_id===o.trip_id).stops[o.delay_stop]))throw Error('Selected journey does not serve the delay stop');
 const schedules=stops.map(s=>facts.trips.map(t=>t.stops[s.stop_id]).filter(Number.isFinite).sort((a,b)=>a-b));
 const resources=stops.map((s,i)=>({queue:0,updated:schedules[i][0],end:schedules[i].at(-1),berth:0,last_departure:null,last_scheduled:null,departures:[],max_queue:0,boarded:0,generated:0}));
 const trips=facts.trips.map(t=>({...t,calls:[],onboard:0,served:stops.map((s,i)=>({i,time:t.stops[s.stop_id]})).filter(s=>Number.isFinite(s.time)),shock_applied:false}));
 const events=[];let impossible_budgets=0;
 const shock=(trip,call)=>{
  if(trip.trip_id!==o.trip_id||trip.shock_applied||!o.delay_seconds)return 0;
  if(o.delay_stop==='origin'||stops[call.i].stop_id===o.delay_stop){trip.shock_applied=true;return o.delay_seconds}
  return 0;
 };
 for(const trip of trips){const call=trip.served[0];events.push({trip,k:0,arrival:call.time+shock(trip,call)})}
 while(events.length){
  events.sort((a,b)=>a.arrival-b.arrival||a.trip.trip_id.localeCompare(b.trip.trip_id));
  const {trip,k,arrival}=events.shift(),call=trip.served[k],sid=stops[call.i].stop_id,r=resources[call.i];
  const service_start=Math.max(arrival,r.berth),demandUntil=Math.min(service_start,r.end);
  const generated=call.i===stops.length-1?0:Math.max(0,demandUntil-r.updated)/60*o.passengers_per_minute;
  r.queue+=generated;r.generated+=generated;r.updated=Math.max(r.updated,demandUntil);r.max_queue=Math.max(r.max_queue,r.queue);
  const final=k===trip.served.length-1,alighted=final?trip.onboard:trip.onboard*o.alight_fraction;
  trip.onboard-=alighted;
  const boarded=final?0:Math.min(r.queue,Math.max(0,o.capacity-trip.onboard));
  r.queue-=boarded;r.boarded+=boarded;trip.onboard+=boarded;
  const dwell=o.base_dwell+boarded*o.boarding_seconds+alighted*o.alighting_seconds;
  let departure=service_start+dwell;
  if(points.has(sid)&&o.control!=='none')departure=Math.max(departure,call.time);
  const plannedGap=r.last_scheduled===null?null:Math.abs(call.time-r.last_scheduled);
  if(points.has(sid)&&o.control==='headway'&&r.last_departure!==null&&plannedGap!==null)departure=Math.max(departure,r.last_departure+plannedGap*o.headway_fraction);
  const headway=r.last_departure===null?null:departure-r.last_departure;
  const record={stop_id:sid,index:call.i,scheduled:call.time,approach_arrival:arrival,arrival:service_start,departure,lateness:service_start-call.time,
   berth_wait:service_start-arrival,dwell,hold:departure-service_start-dwell,boarded,alighted,load:trip.onboard,
   queue_left:r.queue,headway,scheduled_headway:plannedGap,timing_point:points.has(sid)};
  trip.calls.push(record);r.departures.push({trip_id:trip.trip_id,...record});r.last_departure=departure;r.last_scheduled=call.time;r.berth=departure;
  if(!final){const next=trip.served[k+1],gap=next.time-call.time;
   const a=stops[call.i],b=stops[next.i],lat=(a.stop_lat+b.stop_lat)*Math.PI/360;
   const metres=Math.hypot((b.stop_lon-a.stop_lon)*111320*Math.cos(lat),(b.stop_lat-a.stop_lat)*111320);
   const budget=gap-o.reference_dwell-o.recovery_per_leg,floor=Math.max(5,metres/13.89);
   if(budget<floor)impossible_budgets++;
   const running=Math.max(floor,budget);
   events.push({trip,k:k+1,arrival:departure+running+shock(trip,next)})
  }
 }
 // Demand ends at the final published call. Early last departures cannot erase later passengers.
 for(let i=0;i<resources.length;i++){
  const r=resources[i];if(i===stops.length-1)continue;
  const remaining=Math.max(0,r.end-r.updated)/60*o.passengers_per_minute;
  r.queue+=remaining;r.generated+=remaining;r.max_queue=Math.max(r.max_queue,r.queue);
 }
 const calls=trips.flatMap(t=>t.calls),timing=calls.filter(c=>c.timing_point),gaps=[];
 for(let i=0;i<resources.length;i++)for(let j=1;j<resources[i].departures.length;j++){
  const a=resources[i].departures[j-1],b=resources[i].departures[j];
  // Use the scheduled-time separation of the actual adjacent pair, even after overtaking.
  const planned=Number.isFinite(b.scheduled_headway)?b.scheduled_headway:null;
  if(planned>0&&b.headway<planned*.5)gaps.push({stop_id:stops[i].stop_id,first:a.trip_id,second:b.trip_id,seconds:b.headway,planned_seconds:planned});
 }
 const passengers=resources.slice(0,-1); // no boarding demand at the final terminus
 const generated=passengers.reduce((n,r)=>n+r.generated,0),boarded=passengers.reduce((n,r)=>n+r.boarded,0),remaining=passengers.reduce((n,r)=>n+r.queue,0);
 const denied=calls.filter(c=>c.queue_left>1e-7).length;
 return {settings:o,trips:trips.map(({served,onboard,...t})=>t),stops:resources.map((r,i)=>({stop_id:stops[i].stop_id,queue_left:r.queue,max_queue:r.max_queue,generated:r.generated,boarded:r.boarded})),
  summary:{trips:trips.length,calls:calls.length,timing_calls:timing.length,late_timing_calls:timing.filter(c=>c.lateness>o.target_lateness+.001).length,
   max_lateness:Math.max(0,...timing.map(c=>c.lateness)),early_timing_departures:timing.filter(c=>c.departure<c.scheduled-.001).length,
   short_gap_events:gaps.length,short_gap_trip_pairs:new Set(gaps.map(g=>g.first+'|'+g.second)).size,
   passenger_arrivals:generated,boardings:boarded,passengers_left:remaining,capacity_denied_calls:denied,passenger_balance_error:generated-boarded-remaining,
   max_load:Math.max(0,...calls.map(c=>c.load)),max_queue:Math.max(0,...resources.map(r=>r.max_queue)),runtime_budget_floor_events:impossible_budgets,
   target_met:timing.every(c=>c.lateness<=o.target_lateness+.001&&c.departure>=c.scheduled-.001)&&gaps.length===0&&denied===0&&remaining<.01},gaps,
  limits:'Assumed fluid arrivals, alighting, dwell, capacity, single berth and timetable-derived running budgets. No measured AVL calibration, roads outside Porto, other routes, outbound trips or vehicle rotations. Not a guarantee of real punctuality.'};
}

export function compareService(facts,settings={}){
 const scenario=simulateService(facts,settings),reference=simulateService(facts,{...settings,delay_seconds:0});
 const lookup=new Map(reference.trips.map(t=>[t.trip_id,t]));let changed=0,secondaryLate=0;
 for(const trip of scenario.trips){if(trip.trip_id===scenario.settings.trip_id)continue;const base=lookup.get(trip.trip_id);
  if(trip.calls.some((c,i)=>c.timing_point&&Math.abs(c.lateness-base.calls[i].lateness)>1))changed++;
  if(trip.calls.some((c,i)=>c.timing_point&&c.lateness-base.calls[i].lateness>1))secondaryLate++;
 }
 return {reference,scenario,other_trips_changed:changed,other_trips_later:secondaryLate};
}
