// Canvas plan view of the same verified SUMO scene and frames used by 3D.
import {busChoices,locateBus,visibleReplays} from './native-replay.mjs';
export async function createInspection2D({data,getState,label,changed,replayModel:model}) {
  const {source,manifest,cache,positions} = model, panels = {}, backgrounds = new Map();
  const paths = points => {const path = new Path2D();points.forEach((p,i)=>i?path.lineTo(...p):path.moveTo(...p));return path};
  const lanes = source.lanes.filter(l=>!l.internal).map(l=>({...l,path:paths(l.shape),bounds:[Math.min(...l.shape.map(p=>p[0])),Math.min(...l.shape.map(p=>p[1])),Math.max(...l.shape.map(p=>p[0])),Math.max(...l.shape.map(p=>p[1]))]}));
  const buildings = source.buildings.features.map(b=>({path:paths([...b.shape,b.shape[0]]),bounds:[Math.min(...b.shape.map(p=>p[0])),Math.min(...b.shape.map(p=>p[1])),Math.max(...b.shape.map(p=>p[0])),Math.max(...b.shape.map(p=>p[1]))]}));
  const junctions = Object.fromEntries(Object.entries(source.junctions).map(([key,polygons])=>[key,polygons.map(p=>paths([...p,p[0]]))]));
  const laneIndices = new Map(source.lanes.map((l,i)=>[l.id,i]));
  const stops = source.stops.map(s=>({...s,point:model.atLane(laneIndices.get(s.lane),s.pos)})).filter(s=>s.point);
  let center = [0,0], span = 600, cameraKey = '', loadedCase = '', loading = true, active = false, generation = 0, drag;
  let visible = {}, selected = {}, sample = {};
  const cameraBox = () => (data.direction_cameras?.[String(getState().direction)] || data.cameras)[getState().camera];
  function invalidate() {backgrounds.clear()}
  function reset() {const b=cameraBox();center=[(b[0]+b[2])/2,(b[1]+b[3])/2];span=Math.max(b[2]-b[0],b[3]-b[1],120)*1.15;invalidate();draw()}
  function size(panel) {
    const rect=panel.host.getBoundingClientRect(),ratio=Math.min(devicePixelRatio||1,2);
    if (!rect.width || !rect.height) return null;
    const w=Math.round(rect.width*ratio),h=Math.round(rect.height*ratio);
    if(panel.canvas.width!==w||panel.canvas.height!==h){panel.canvas.width=w;panel.canvas.height=h;backgrounds.delete(panel.policy)}
    const scale=Math.min(rect.width,rect.height)/span;
    return {width:rect.width,height:rect.height,ratio,scale,bounds:[center[0]-rect.width/scale/2,center[1]-rect.height/scale/2,center[0]+rect.width/scale/2,center[1]+rect.height/scale/2]};
  }
  const intersects=(a,b)=>a[0]<=b[2]&&a[2]>=b[0]&&a[1]<=b[3]&&a[3]>=b[1];
  function worldTransform(x,s) {x.setTransform(s.ratio*s.scale,0,0,-s.ratio*s.scale,s.ratio*(s.width/2-center[0]*s.scale),s.ratio*(s.height/2+center[1]*s.scale))}
  function point(p,s) {return [(p[0]-center[0])*s.scale+s.width/2,(center[1]-p[1])*s.scale+s.height/2]}
  function background(panel,s) {
    if(backgrounds.has(panel.policy))return backgrounds.get(panel.policy);
    const canvas=document.createElement('canvas');canvas.width=panel.canvas.width;canvas.height=panel.canvas.height;
    const x=canvas.getContext('2d');x.fillStyle='#eef1e8';x.fillRect(0,0,canvas.width,canvas.height);worldTransform(x,s);
    if(getState().buildings){x.fillStyle='#d9d5c8';for(const b of buildings)if(intersects(b.bounds,s.bounds))x.fill(b.path)}
    x.fillStyle='#b2bab5';for(const path of junctions[panel.policy])x.fill(path);
    x.lineCap='round';x.lineJoin='round';
    for(const l of lanes){if(l.policy!==panel.policy||!intersects(l.bounds,s.bounds))continue;x.strokeStyle=l.corridor&&l.bus_priority?'#a9d8bf':l.corridor?'#9eaaa4':'#c2c8c2';x.lineWidth=Math.max(l.width,1.1/s.scale);x.stroke(l.path)}
    x.setTransform(s.ratio,0,0,s.ratio,0,0);x.textBaseline='middle';x.font='11px system-ui';
    for(const stop of stops){if(stop.policy!==panel.policy||(/^d\d_/.test(stop.id)&&!stop.id.startsWith('d'+getState().direction+'_')))continue;const [px,py]=point(stop.point,s);if(px<0||px>s.width||py<0||py>s.height)continue;x.beginPath();x.arc(px,py,3,0,Math.PI*2);x.fillStyle='#fff';x.fill();x.strokeStyle='#276481';x.lineWidth=1.5;x.stroke();if(s.scale>.6){x.lineWidth=3;x.strokeStyle='#fff';x.strokeText(stop.name,px+6,py-7);x.fillStyle='#254b58';x.fillText(stop.name,px+6,py-7)}}
    backgrounds.set(panel.policy,canvas);return canvas;
  }
  function draw() {
    if(!active||loading)return;
    const state=getState();if(loadedCase!==state.case)return;
    visible={};selected={};sample={};
    for(const panel of Object.values(panels)){
      if(state.view!=='compare'&&state.view!==panel.policy)continue;
      const s=size(panel),replay=cache.get(state.case+'-'+panel.policy);if(!s||!replay)continue;
      const x=panel.canvas.getContext('2d');x.setTransform(1,0,0,1,0,0);x.drawImage(background(panel,s),0,0);x.setTransform(s.ratio,0,0,s.ratio,0,0);
      const rows=positions(replay,state.time).sort((a,b)=>(a.group==='bus')-(b.group==='bus'));let count=0,stopped=0;
      for(const row of rows){const [px,py]=point([row.x,row.y],s);if(px<-30||py<-30||px>s.width+30||py>s.height+30)continue;
        count++;if(row.speed<.5)stopped++;
        const dim=source.vehicle_dimensions.types[row.group]||source.vehicle_dimensions.types.background,isBus=row.group==='bus';
        const length=Math.max(dim.length*s.scale,isBus?10:3.5),width=Math.max(dim.width*s.scale,isBus?4:2),angle=row.angle*Math.PI/180;
        x.save();x.translate(px,py);x.rotate(angle);x.fillStyle=data.colors[row.group]||'#85918a';x.fillRect(-width/2,0,width,length);
        if(row.speed<.5){x.strokeStyle='#b64032';x.lineWidth=1.2;x.strokeRect(-width/2,0,width,length)}
        if(isBus){x.fillStyle='#e5fff1';x.fillRect(-width/2+.6,1,Math.max(1,width-1.2),Math.min(2,length/4))}x.restore();
        if(row.id===state.follow){x.beginPath();x.arc(px,py,Math.max(length/2,8)+3,0,Math.PI*2);x.strokeStyle='#d6991c';x.lineWidth=2;x.stroke();selected[panel.policy]={id:row.id,speed_kmh:Math.round(row.speed*3.6)};x.font='bold 11px system-ui';x.fillStyle='#163d30';x.fillText(String(data.meta.route)+' · '+Math.round(row.speed*3.6)+' km/h',px+10,py-12)}
        if(!sample[panel.policy]||(sample[panel.policy].speed<.5&&row.speed>=.5))sample[panel.policy]={id:row.id,x:row.x,y:row.y,speed:row.speed};
      }
      visible[panel.policy]=count;document.getElementById(panel.policy+'Counter').textContent=count+' '+label('visible')+' · '+stopped+' '+label('stopped');
      const base=10**Math.floor(Math.log10(90/s.scale)),scaleMetres=[base,base*2,base*5].filter(n=>n*s.scale<=100).at(-1)||base,bar=scaleMetres*s.scale;
      x.fillStyle='#ffffffdf';x.fillRect(10,s.height-39,Math.max(bar+20,85),29);x.strokeStyle='#244c3c';x.lineWidth=2;x.beginPath();x.moveTo(20,s.height-19);x.lineTo(20+bar,s.height-19);x.stroke();x.font='11px system-ui';x.fillStyle='#244c3c';x.fillText(scaleMetres+' m',20,s.height-26);
      x.fillStyle='#244c3c';x.font='bold 12px system-ui';x.fillText('N ↑',s.width-38,23);
    }
    document.getElementById('threeState').textContent=Object.entries(selected).map(([policy,bus])=>label(policy)+': '+bus.id+' · '+bus.speed_kmh+' km/h').join(' · ');
  }
  for(const policy of ['baseline','restricted']){
    const host=document.getElementById(policy+'2D'),canvas=document.createElement('canvas');canvas.tabIndex=0;canvas.setAttribute('aria-label',label('twoCanvas'));host.append(canvas);const panel={host,canvas,policy};panels[policy]=panel;
    canvas.addEventListener('pointerdown',e=>{canvas.focus({preventScroll:true});drag={id:e.pointerId,x:e.clientX,y:e.clientY,center:[...center]};canvas.setPointerCapture(e.pointerId)});
    canvas.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;const s=size(panel);if(!s)return;center=[drag.center[0]-(e.clientX-drag.x)/s.scale,drag.center[1]+(e.clientY-drag.y)/s.scale];invalidate();draw()});
    const end=()=>{if(drag){drag=null;changed()}};canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',end);
    canvas.addEventListener('wheel',e=>{if(!active)return;e.preventDefault();const s=size(panel),rect=canvas.getBoundingClientRect(),dx=e.clientX-rect.left-s.width/2,dy=e.clientY-rect.top-s.height/2,old=span;span=Math.max(40,Math.min(24000,span*Math.exp(Math.max(-1,Math.min(1,e.deltaY*.0015)))));const nextScale=s.scale*old/span;center=[center[0]+dx/s.scale-dx/nextScale,center[1]-dy/s.scale+dy/nextScale];invalidate();draw();changed()},{passive:false});
    canvas.addEventListener('keydown',e=>{if(!active)return;const steps={ArrowUp:[0,1],ArrowDown:[0,-1],ArrowLeft:[-1,0],ArrowRight:[1,0]},step=steps[e.key];if(step){e.preventDefault();center=[center[0]+step[0]*span*.12,center[1]+step[1]*span*.12];invalidate();draw();changed()}});
  }
  function selectBus(id) {
    const state=getState();state.follow=id;const found=locateBus(cache,positions,state,id);
    if(found?.row){state.time=found.time;center=[found.row.x,found.row.y];span=Math.min(span,500);invalidate()}
    changed();draw();
  }
  function busOptions() {
    const state=getState(),select=document.getElementById('followBus'),buses=busChoices(source,cache,state);
    const ids=new Set(buses.map(b=>b.id));if(!ids.has(state.follow))state.follow=visibleReplays(cache,state).flatMap(r=>positions(r,state.time)).find(v=>ids.has(v.id))?.id||buses[0]?.id||'';
    select.replaceChildren(...buses.map(v=>new Option(source.bus_info[v.id]?.label||v.id,v.id)));select.value=state.follow;
  }
  return {
    async update(){active=getState().dimension==='2d';if(!active)return;const state=getState(),key=state.direction+'|'+state.camera+'|'+state.buildings;if(key!==cameraKey){const moved=cameraKey.split('|').slice(0,2).join('|')!==key.split('|').slice(0,2).join('|');cameraKey=key;if(moved)reset();else invalidate()}
      loading=true;const token=++generation;document.getElementById('threeState').textContent=label('threeLoading');try{await model.loadCase(state.case);if(token!==generation||getState().case!==state.case)return;loadedCase=state.case;loading=false;busOptions();draw()}catch(error){if(token===generation){loading=true;throw error}}
    },
    draw,reset,selectBus,zoom(factor){span=Math.max(40,Math.min(24000,span*factor));invalidate();draw();changed()},canvas:policy=>panels[policy].canvas,
    pose:()=>({center:[...center],span}),
    restore(pose){if(!pose||!Array.isArray(pose.center)||pose.center.length!==2||![...pose.center,pose.span].every(Number.isFinite)||pose.span<40||pose.span>24000)return;center=[...pose.center];span=pose.span;invalidate();draw()},
    debug:()=>({loaded:!loading,case:loadedCase,study:manifest.study_id,manifest:manifest.id,dimension:'2d',time:getState().time,center:[...center],span,visible:{...visible},selected:{...selected},sample:structuredClone(sample)})
  };
}
