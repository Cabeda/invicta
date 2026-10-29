// SUMO owns movement. Both renderers consume this verified, shared trajectory model.
export async function readAsset(name, assetBase = './inspection-assets/', expectedHash) {
  const response = await fetch(new URL(`${assetBase}${name}.json.gz`, import.meta.url));
  if (!response.ok) throw new Error(`Missing inspection asset: ${name}`);
  const bytes = await response.arrayBuffer();
  if (expectedHash) {
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v => v.toString(16).padStart(2, '0')).join('');
    if (hash !== expectedHash) throw Error('Replay asset hash does not match the prepared manifest: ' + name);
  }
  return new Response(new Response(bytes).body.pipeThrough(new DecompressionStream('gzip'))).json();
}

export function decodeFrames(replay) {
  if (replay.encoding === 'vehicle-deltas-v1') {
    const active = new Map(); let order = [];
    replay.frames = replay.frames.map(frame => {
      for (const id of frame.removed || []) if (!active.delete(id)) throw Error('Invalid removed vehicle');
      for (const row of frame.vehicles) active.set(row[0], row);
      order = frame.order || order;
      if (order.length !== active.size || new Set(order).size !== order.length || order.some(id => !active.has(id))) throw Error('Invalid native vehicle order');
      return {t:frame.t, vehicles:order.map(id => active.get(id))};
    });
  } else if (replay.encoding && replay.encoding !== 'frames-v1') throw Error('Unsupported capture encoding');
  return replay;
}

export function createTrajectoryModel(source) {
  const distances = source.lanes.map(lane => {
    const cumulative = [0];
    for (let i = 1; i < lane.shape.length; i++) cumulative.push(cumulative.at(-1) + Math.hypot(lane.shape[i][0]-lane.shape[i-1][0], lane.shape[i][1]-lane.shape[i-1][1]));
    return cumulative;
  });
  function atLane(index, position) {
    const lane = source.lanes[index], cumulative = distances[index];
    if (!lane || !lane.length || cumulative.length < 2) return null;
    const d = Math.max(0, Math.min(cumulative.at(-1), position*cumulative.at(-1)/lane.length));
    let i = 1;
    while (i < cumulative.length-1 && cumulative[i] < d) i++;
    const a = lane.shape[i-1], b = lane.shape[i], f = (d-cumulative[i-1])/(cumulative[i]-cumulative[i-1] || 1);
    return [a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f, (Math.atan2(b[0]-a[0],b[1]-a[1])*180/Math.PI+360)%360];
  }
  function positions(replay, time) {
    if (!replay?.frames.length || time < replay.start || time > replay.end) return [];
    const i = Math.max(0, Math.min(replay.frames.length-1, Math.floor((time-replay.start)/(replay.step || 1))));
    const a = replay.frames[i], b = replay.frames[Math.min(i+1,replay.frames.length-1)];
    const f = Math.max(0,Math.min(1,(time-a.t)/(b.t-a.t || replay.step || 1))), next = new Map(b.vehicles.map(v => [v[0],v]));
    return a.vehicles.map(row => {
      const n = next.get(row[0]) || row, onLane = row[5] === n[5] ? atLane(row[5],row[6]+(n[6]-row[6])*f) : null;
      return {index:row[0],id:replay.vehicles[row[0]].id,group:replay.vehicles[row[0]].group,
        x:onLane ? onLane[0] : row[1]+(n[1]-row[1])*f, y:onLane ? onLane[1] : row[2]+(n[2]-row[2])*f,
        angle:onLane ? onLane[2] : row[3]+(((n[3]-row[3]+540)%360)-180)*f,speed:row[4],lane:row[5]};
    });
  }
  return {atLane,positions};
}

export function visibleReplays(cache,state) {
  const policies=state.view==='compare'?['restricted','baseline']:[state.view];
  return policies.map(policy=>cache.get(state.case+'-'+policy)).filter(Boolean);
}

export function busChoices(source,cache,state) {
  const buses=new Map();
  for(const replay of visibleReplays(cache,state))for(const v of replay.vehicles)if(v.group==='bus'&&(source.bus_info[v.id]?.direction==null||String(source.bus_info[v.id].direction)===String(state.direction)))buses.set(v.id,v);
  return [...buses.values()];
}

export function locateBus(cache,positions,state,id) {
  const available=visibleReplays(cache,state).filter(replay=>replay.vehicles.some(v=>v.id===id));
  for(const replay of available){const row=positions(replay,state.time).find(v=>v.id===id);if(row)return {row,time:state.time,policy:replay.policy}}
  for(const replay of available){const index=replay.vehicles.findIndex(v=>v.id===id),frame=replay.frames.find(f=>f.vehicles.some(v=>v[0]===index));if(frame)return {row:positions(replay,frame.t).find(v=>v.id===id),time:frame.t,policy:replay.policy}}
  return null;
}

export async function createNativeReplay({data,assetBase = './inspection-assets/'}) {
  const response = await fetch(new URL(assetBase+'manifest.json',import.meta.url));
  if (!response.ok) throw Error('Missing prepared replay manifest');
  const manifest = await response.json();
  if (data.replay_manifest && data.replay_manifest.id !== manifest.id) throw Error('Replay manifest does not match proposal data');
  if(data.replay_manifest&&JSON.stringify(data.replay_manifest.scope)!==JSON.stringify(manifest.scope))throw Error('Replay coverage does not match proposal data');
  const source = await readAsset('scene',assetBase,manifest.scene.sha256);
  if (source.capture_signature !== manifest.capture_signature || source.study_id !== manifest.study_id) throw Error('Scene does not match replay scope');
  const trajectory = createTrajectoryModel(source), cache = new Map(), pending = new Map();
  let requestedCase = '';
  async function loadCase(current) {
    requestedCase = current;
    if (!pending.has(current)) pending.set(current,(async()=>{
      const pair = await Promise.all(['baseline','restricted'].map(async policy => {
        const key = `${current}-${policy}`;
        if (cache.has(key)) return [key,cache.get(key)];
        const clip = manifest.clips.find(c => c.case === current && c.policy === policy);
        if (!clip) throw Error('No prepared capture for '+key);
        const replay = await readAsset(key,assetBase,clip.sha256);
        if (replay.capture_signature !== source.capture_signature || replay.study_id !== source.study_id || replay.case !== current || replay.policy !== policy || replay.start !== clip.start || replay.end !== clip.end || replay.step !== clip.step || replay.seed !== clip.seed || replay.simulation_begin !== clip.simulation_begin || JSON.stringify(replay.input_hashes) !== JSON.stringify(clip.input_hashes) || JSON.stringify(replay.scope) !== JSON.stringify(manifest.scope)) throw Error('Capture does not match scene, policy or time window');
        if ((replay.encoding || 'frames-v1') !== (clip.encoding || 'frames-v1')) throw Error('Capture encoding does not match manifest');
        return [key,decodeFrames(replay)];
      }));
      if (requestedCase === current) {
        cache.clear(); for (const [key,replay] of pair) cache.set(key,replay);
      }
    })());
    try {await pending.get(current)} finally {pending.delete(current)}
  }
  return {manifest,source,cache,...trajectory,loadCase};
}
