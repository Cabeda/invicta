// One reviewed proposal is the seam used by links, reports and recordings.
const own = (object, key) => Object.hasOwn(object || {}, key);
const clone = value => structuredClone(value);
const finite = value => typeof value === 'number' && Number.isFinite(value);
const decode = value => { try { return decodeURIComponent(value); } catch { return ''; } };
const json = (value, fallback = null) => { try { return JSON.parse(value); } catch { return fallback; } };
const pick = (value, choices, fallback) => choices.includes(value) ? value : fallback;
const displayId = value => { let hash = 2166136261; for (const char of JSON.stringify(value)) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619); return (hash >>> 0).toString(36); };

export function createProposal(data) {
  if(data.native_directions)return multiDirectionProposal(data);
  const imports = new Map(), rawUploads = new Map(), legs = data.route.segments.map(s => s.id);
  const serviceStart=Date.parse(data.study_midnight),serviceEnd=serviceStart+(Math.max(86400,...Object.values(data.observations.timetables).flatMap(t=>Object.values(t.stops)).filter(finite))+7200)*1000;
  const cases = Object.keys(data.cases), tripIds = data.route.morning.map(t => t.id);
  const mask = variant => variant === 'baseline' ? [] : variant === 'restricted' ? data.access.candidate_priority_segments : variant === 'all_priority' ? legs : variant === 'custom' ? data.access.custom_priority_segments : legs.includes(variant) ? [variant] : null;
  const samePolicy = (a, b) => Array.isArray(a) && Array.isArray(b) && [...a].sort().join('|') === [...b].sort().join('|');
  const validPriority = values => [...new Set((Array.isArray(values) ? values : []).filter(id => legs.includes(id)))];
  function normalize(input = {}) {
    const selection = {};
    selection.lang = pick(input.lang, ['pt', 'en'], 'pt');
    selection.case = pick(input.case, cases, cases.includes('busy')?'busy':cases[0]);
    selection.variant = pick(input.variant, ['baseline', 'restricted', 'all_priority', 'custom', 'draft', ...legs], 'restricted');
    if (legs.includes(selection.variant)&&cases.includes('busy')) selection.case = 'busy';
    selection.priority = validPriority(input.priority ?? mask(selection.variant));
    if (!samePolicy(selection.priority, mask(selection.variant))) selection.variant = 'draft';
    if(data.access.policy_masks){
      const direction=String(data.route.direction??data.meta.direction),masks=data.access.policy_masks;
      selection.policy_by_direction=clone(input.policy_by_direction||masks[selection.variant]||masks.baseline);
      for(const id of Object.keys(masks.baseline)){const allowed=masks.all_priority[id];selection.policy_by_direction[id]=[...new Set((selection.policy_by_direction[id]||[]).filter(leg=>allowed.includes(leg)))]}
      selection.policy_by_direction[direction]=[...selection.priority];
      if(!masks[selection.variant]||!Object.keys(masks.baseline).every(id=>samePolicy(selection.policy_by_direction[id],masks[selection.variant][id])))selection.variant='draft';
    }
    selection.trip = pick(input.trip, tripIds, tripIds[0]);
    selection.selectedLeg = pick(input.selectedLeg, legs, legs[0]);
    selection.camera = pick(input.camera, Object.keys(data.cameras), 'combatentes');
    selection.dimension = input.dimension === '3d' ? '3d' : '2d';
    selection.perspective = pick(input.perspective, ['orbit', 'street', 'follow'], 'orbit');
    selection.view = pick(input.view, ['compare', 'baseline', 'restricted'], 'restricted');
    const clip=data.replay_manifest?.clips?.[0],start=clip?.start??600,end=clip?.end??2400;
    selection.time = finite(input.time) ? Math.max(start, Math.min(end, input.time)) : Math.round((start+end)/2);
    selection.speed = pick(input.speed, [1, 5, 10, 20], 5);
    selection.cameraSpeed = pick(input.cameraSpeed, [1, 3, 10], 3);
    selection.buildings = input.buildings !== false;
    selection.follow = typeof input.follow === 'string' ? input.follow.slice(0, 100) : '';
    selection.pose = input.pose && ['position', 'target'].every(k => Array.isArray(input.pose[k]) && input.pose[k].length === 3) && [...input.pose.position, ...input.pose.target, input.pose.yaw, input.pose.pitch].every(n => finite(n) && Math.abs(n) <= 1e6) ? clone(input.pose) : null;
    selection.reference = typeof input.reference === 'string' ? input.reference : data.reference_id;
    selection.line = input.line && typeof input.line === 'object' ? clone(input.line) : {direction: '1'};
    selection.service = input.service && typeof input.service === 'object' ? clone(input.service) : null;
    selection.audience = pick(input.audience, ['citizen', 'urbanist'], 'citizen');
    selection.anchor = pick(input.anchor, ['route', 'replay', 'service', 'access', 'observations', 'native-route'], 'route');
    selection.observation = typeof input.observation === 'string' ? input.observation : data.observations.trips.filter(t => t.passages.length).sort((a,b) => b.passages.length-a.passages.length)[0]?.trip_id;
    selection.analysis_open = input.analysis_open === true || ['service','access','observations','native-route'].includes(selection.anchor);
    selection.playing = false;
    return selection;
  }

  function restore(url) {
    const parsed = new URL(url), q = parsed.searchParams;
    const payload = parsed.hash.startsWith('#proposal=') ? json(decode(parsed.hash.slice(10)), {}) : null;
    let input;
    if (payload?.schema === 'invicta.proposal.v1') {
      input = payload.selection || {};
      if (payload.upload && typeof payload.upload.trip_id==='string' && Array.isArray(payload.upload.arrivals)) {
        const id='upload:'+payload.upload.trip_id;rawUploads.set(id,clone(payload.upload));input={...input,observation:id};
        if(!input.reference || input.reference===data.reference_id)importArrivals(payload.upload.arrivals,payload.upload.trip_id);
      }
    } else {
      input = {lang:q.get('lang'),case:q.get('case'),variant:q.get('variant'),trip:q.get('trip'),camera:q.get('camera'),dimension:q.get('dimension'),perspective:q.get('perspective'),view:q.get('view'),
        time:q.has('t') ? Number(q.get('t')) : undefined,speed:Number(q.get('speed')),cameraSpeed:Number(q.get('cameraSpeed')),buildings:q.get('buildings')!=='0',follow:q.get('follow'),
        pose:json(q.get('pose')),service:json(q.get('service')),line:json(q.get('line')) || {direction:q.get('direction') || '1'},
        selectedLeg:q.get('leg'),observation:q.get('observation'),anchor:parsed.hash.slice(1),audience:['#service','#access','#observations'].includes(parsed.hash)?'urbanist':'citizen'};
      if (q.has('priority')) input.priority = q.get('priority').split(',');
    }
    return normalize(input);
  }

  function importArrivals(rows, fixedTrip = null) {
    if (typeof rows === 'string') {
      const lines = rows.trim().split(/\r?\n/), headers = lines.shift().split(',').map(s => s.trim());
      rows = lines.map(line => Object.fromEntries(line.split(',').map((s,i) => [headers[i], s.trim()])));
    }
    const grouped = new Map(), seen = new Set(); let accepted = 0, rejected = 0;
    for (const row of rows) {
      const tripId = fixedTrip || row.trip_id, timetable = own(data.observations.timetables, tripId) && data.observations.timetables[tripId];
      const at = row.observed_arrival || row.at, time = Date.parse(at), stop = data.route.stops.find(s => s.stop_id === row.stop_id);
      const expected=serviceStart+(timetable?.stops?.[row.stop_id]??NaN)*1000;
      if (!timetable || !stop || !finite(timetable.stops[row.stop_id]) || !finite(time) || !/(Z|[+-]\d\d:\d\d)$/.test(at || '') || time<serviceStart || time>serviceEnd || Math.abs(time-expected)>21600000 || seen.has(tripId+'|'+row.stop_id)) { rejected++; continue; }
      seen.add(tripId+'|'+row.stop_id);
      if (!grouped.has(tripId)) grouped.set(tripId,{trip_id:'upload:'+tripId,base_trip_id:tripId,passages:[],samples:0});
      const lateness = (time-Date.parse(data.study_midnight))/1000-timetable.stops[row.stop_id], iso = new Date(time).toISOString();
      grouped.get(tripId).passages.push({stop_id:row.stop_id,lateness_low:lateness,lateness_high:lateness,from:iso,to:iso,kind:'user-supplied arrival, not independently verified'}); accepted++;
    }
    for (const trip of grouped.values()){imports.set(trip.trip_id,trip);rawUploads.set(trip.trip_id,{trip_id:trip.base_trip_id,arrivals:trip.passages.map(p=>({stop_id:p.stop_id,at:p.from}))})}
    return {accepted,rejected,trips:clone([...grouped.values()])};
  }

  function observations() { return [...data.observations.trips, ...imports.values()].filter(t => t.passages.length).map(clone); }
  function evidence(id,focusStops=data.route.stops) {
    const uploaded = imports.get(id), trip = uploaded || data.observations.trips.find(t => t.trip_id === id);
    if (!trip) return {kind:rawUploads.has(id)?'unresolved_uploaded_arrivals':'missing',trip_id:id || null,raw_upload:clone(rawUploads.get(id)||null),passages:[],finding:null};
    let finding = null;
    const selected=new Set(focusStops.map(s=>s.stop_id));
    for (let i=0;i<data.route.stops.length-1;i++) {
      if(!selected.has(data.route.stops[i].stop_id)||!selected.has(data.route.stops[i+1].stop_id))continue;
      const a=trip.passages.find(p=>p.stop_id===data.route.stops[i].stop_id),b=trip.passages.find(p=>p.stop_id===data.route.stops[i+1].stop_id);
      if (!a || !b) continue;
      const low=b.lateness_low-a.lateness_high,high=b.lateness_high-a.lateness_low;
      if (low>0 && (!finding || low>finding.low)) finding={from:a.stop_id,to:b.stop_id,low,high};
    }
    return {...clone(trip),kind:uploaded?'uploaded_arrivals':'gps_passage_windows',finding,focus:{from:focusStops[0]?.stop_id,to:focusStops.at(-1)?.stop_id,captured_stops:trip.passages.filter(p=>selected.has(p.stop_id)).length}};
  }

  function review(input, context = {}) {
    const selection=normalize(input), referenceValid=selection.reference===data.reference_id;
    const line=context.line, direction=String(line?.direction ?? selection.line.direction ?? '1');
    const nativeDirection=String(data.route.direction??data.meta.direction??'1'),inbound=direction===nativeDirection,operationalDirection=direction==='1', coverage=line?.coverage || (inbound?'partial':'none');
    const baseline=own(data.cases,selection.case) ? data.cases[selection.case].baseline : null;
    const alternative=own(data.cases[selection.case],selection.variant) && samePolicy(selection.priority,mask(selection.variant)) ? data.cases[selection.case][selection.variant] : null;
    const nativeAvailable=referenceValid && inbound && !!alternative;
    const demandComparable=!!alternative && Object.keys(baseline.groups).every(key=>alternative.groups[key]?.planned===baseline.groups[key].planned) && Object.keys(alternative.groups).length===Object.keys(baseline.groups).length;
    const allServed=!!alternative && Object.values(baseline.groups).every(g=>g.unserved===0) && Object.values(alternative.groups).every(g=>g.unserved===0);
    const complete=!!alternative && alternative.completed===alternative.planned && baseline.completed===baseline.planned;
    const noExtraUnserved=!!alternative && Object.keys(baseline.groups).every(key=>alternative.groups[key]?.unserved<=baseline.groups[key].unserved);
    const selectedEvidence=evidence(selection.observation,line?.stops), manifest=data.replay_manifest;
    const policies=selection.variant==='baseline'?['baseline']:['baseline','restricted'];
    const clips=(manifest?.clips || []).filter(c=>c.case===selection.case && policies.includes(c.policy));
    let replayReason=null;
    if (!referenceValid) replayReason='reference_changed';
    else if (!inbound || coverage==='none') replayReason='outside_coverage';
    else if (!nativeAvailable || !['baseline','restricted'].includes(selection.variant)) replayReason='unprepared_policy';
    else if (!demandComparable) replayReason='different_demand';
    else if (!manifest || manifest.scope.route!=='701' || !(String(manifest.scope.direction)===nativeDirection || own(manifest.scope.directions,nativeDirection)) || (manifest.scope.directions?.[nativeDirection]||manifest.scope).from!==data.route.start || (manifest.scope.directions?.[nativeDirection]||manifest.scope).to!==data.route.end || clips.length!==policies.length || clips.some(c=>c.capture_signature!==manifest.capture_signature || selection.time<c.start || selection.time>c.end)) replayReason='unmatched_capture';
    if (selection.variant==='baseline') selection.view='baseline';
    const service=context.service && referenceValid && operationalDirection ? clone(context.service) : null;
    selection.service=service?.settings || selection.service;
    const serial={schema:'invicta.proposal.v1',selection:clone(selection)};
    if(rawUploads.has(selection.observation))serial.upload=clone(rawUploads.get(selection.observation));
    const snapshot={id:`701-${displayId(serial)}`,selection,serial,
      reference:{expected:selection.reference,actual:data.reference_id,valid:referenceValid,date:data.route.study_date,sources:clone(data.source_summary || {})},
      focus:line ? {direction,from:line.stops[0].stop_id,to:line.stops.at(-1).stop_id,from_name:line.stops[0].stop_name,to_name:line.stops.at(-1).stop_name,stops:line.stops.length,metres:line.metres,scheduled_seconds:line.seconds,trip:line.trip?.trip_id,coverage} : {direction,coverage},
      native:{available:nativeAvailable,case:selection.case,variant:selection.variant,trip:clone(data.route.morning.find(t=>t.id===selection.trip)),priority:selection.priority,selected_leg:selection.selectedLeg,
        scope:{direction:nativeDirection,simulated_directions:data.meta.directions||[nativeDirection],from:data.route.start,to:data.route.end,stops:clone(data.route.stops)},policy_by_direction:selection.policy_by_direction||null,applied_priority_edges:selection.variant==='restricted'?clone(data.access.applied_edges||[]):[],baseline:referenceValid && inbound?clone(baseline):null,alternative:nativeAvailable?clone(alternative):null,
        demand_comparable:demandComparable,complete,no_extra_unserved:noExtraUnserved,can_claim_gain:nativeAvailable && demandComparable && complete && noExtraUnserved && allServed},
      evidence:!referenceValid?{kind:'reference_changed',trip_id:selectedEvidence.trip_id,passages:[],finding:null}:inbound?selectedEvidence:{kind:'outside_coverage',trip_id:null,passages:[],finding:null},
      service,replay:{eligible:!replayReason,reason:replayReason,study_id:manifest?.study_id,assets:data.replay_assets||'./line-701-assets/',scope:clone(manifest?.scope.directions?.[nativeDirection] ? {...manifest.scope.directions[nativeDirection],direction:nativeDirection,route:'701',both_directions_in_simulation:true} : manifest?.scope || {}),follow:selection.follow,follow_trip_id:data.route.morning.find(t=>t.id===selection.follow)?.trip_id||null,scene_sha256:manifest?.scene.sha256,capture_signature:manifest?.capture_signature,clips:clone(clips),seed:clips[0]?.seed,window:clips.length?[Math.max(...clips.map(c=>c.start)),Math.min(...clips.map(c=>c.end))]:null}};
    return snapshot;
  }

  function shareURL(snapshot, base) {
    const url=new URL(base);url.search=new URLSearchParams({lang:snapshot.selection.lang,direction:snapshot.focus.direction}).toString();
    // Fragment payloads keep portable uploaded evidence out of request URLs and logs.
    url.hash='proposal='+encodeURIComponent(JSON.stringify(snapshot.serial));return url;
  }
  return {restore,review,shareURL,importArrivals,observations,dataFor:()=>data};
}

function multiDirectionProposal(root){
 const datasets=Object.fromEntries(Object.entries(root.native_directions).map(([direction,value])=>[direction,{...root,...value,native_directions:undefined}]));
 const models=Object.fromEntries(Object.entries(datasets).map(([direction,value])=>[direction,createProposal(value)]));
 const direction=(selection={},context={})=>{const id=String(context.line?.direction??selection.line?.direction??'1');return Object.hasOwn(models,id)?id:'1'};
 function restore(url){
  const parsed=new URL(url),payload=parsed.hash.startsWith('#proposal=')?json(decode(parsed.hash.slice(10)),{}):null;
  const line=payload?.selection?.line || json(parsed.searchParams.get('line')) || {direction:parsed.searchParams.get('direction')||'1'};
  return models[direction({line})].restore(url);
 }
 function importArrivals(rows,fixedTrip=null){
  if(typeof rows==='string'){const lines=rows.trim().split(/\r?\n/),headers=lines.shift().split(',').map(s=>s.trim());rows=lines.map(line=>Object.fromEntries(line.split(',').map((s,i)=>[headers[i],s.trim()])))}
  const grouped={};let rejected=0;const trips=[];let accepted=0;
  for(const row of rows){const id=Object.keys(datasets).find(d=>Object.hasOwn(datasets[d].observations.timetables,fixedTrip||row.trip_id));if(!id){rejected++;continue}(grouped[id]??=[]).push(row)}
  for(const [id,values]of Object.entries(grouped)){const result=models[id].importArrivals(values,fixedTrip);accepted+=result.accepted;rejected+=result.rejected;trips.push(...result.trips.map(t=>({...t,direction:id})))}
  return {accepted,rejected,trips};
 }
 return {restore,importArrivals,dataFor:selection=>datasets[direction(selection)],review:(selection,context)=>models[direction(selection,context)].review(selection,context),
  observations:id=>models[Object.hasOwn(models,String(id))?String(id):'1'].observations(),shareURL:(snapshot,base)=>models[snapshot.focus.direction].shareURL(snapshot,base)};
}
