import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeFrames,createTrajectoryModel,busChoices,locateBus} from '../costa-cabral/native-replay.mjs';
const source={lanes:[{length:20,shape:[[0,0],[10,0],[10,10]]}]};
const trajectory=createTrajectoryModel(source);
const vehicle={id:'bus1',group:'bus'};
test('native delta decoding preserves stationary vehicles, removals, reappearance and exact order',()=>{
 const a=[0,0,0,90,0,0,0],b=[1,3,0,90,1,0,3],c=[0,5,0,90,2,0,5];
 const frames=[{t:0,vehicles:[a,b],order:[1,0]},{t:5,vehicles:[c]},{t:10,vehicles:[],removed:[1],order:[0]},{t:15,vehicles:[b],order:[1,0]}];
 assert.deepEqual(decodeFrames({encoding:'vehicle-deltas-v1',frames}).frames.map(f=>f.vehicles),[[b,a],[b,c],[c],[b,c]]);
});
test('corrupt delta membership and unsupported encodings fail rather than invent traffic',()=>{
 assert.throws(()=>decodeFrames({encoding:'vehicle-deltas-v1',frames:[{t:0,vehicles:[],removed:[9]}]}),/removed/);
 assert.throws(()=>decodeFrames({encoding:'vehicle-deltas-v1',frames:[{t:0,vehicles:[[0,1]],order:[0,0]}]}),/order/);
 assert.throws(()=>decodeFrames({encoding:'future',frames:[]}),/Unsupported/);
});
test('both renderers follow native lane distance around corners at the five-second sample interval',()=>{
 const replay={start:100,end:105,step:5,vehicles:[vehicle],frames:[{t:100,vehicles:[[0,8,0,90,1,0,8]]},{t:105,vehicles:[[0,10,4,0,1,0,14]]}]};
 const row=trajectory.positions(replay,102.5)[0];assert.equal(row.x,10);assert.equal(row.y,1);assert.equal(row.angle,0);assert.equal(row.id,'bus1');
 assert.deepEqual(trajectory.positions(replay,99),[]);assert.deepEqual(trajectory.positions(replay,106),[]);
});
test('lane changes interpolate native coordinates and take the shortest heading rotation',()=>{
 const replay={start:0,end:5,step:5,vehicles:[vehicle],frames:[{t:0,vehicles:[[0,0,0,350,0,0,0]]},{t:5,vehicles:[[0,10,4,10,0,1,0]]}]};
 const row=trajectory.positions(replay,2.5)[0];assert.equal(row.x,5);assert.equal(row.y,2);assert.equal(row.angle,360);
});

test('bus selection uses the visible policy and includes baseline-only buses in comparison',()=>{
 const row=(id,x)=>[id,x,0,90,0,0,x],baseline={policy:'baseline',start:0,end:5,step:5,vehicles:[vehicle,{id:'baseline-only',group:'bus'}],frames:[{t:0,vehicles:[row(0,2),row(1,4)]},{t:5,vehicles:[row(0,3),row(1,5)]}]};
 const restricted={policy:'restricted',start:0,end:5,step:5,vehicles:[vehicle,{id:'proposal-only',group:'bus'}],frames:[{t:0,vehicles:[row(0,8),row(1,9)]},{t:5,vehicles:[row(0,9),row(1,10)]}]};
 const cache=new Map([['busy-baseline',baseline],['busy-restricted',restricted]]),info={bus_info:{}},state={case:'busy',time:0,direction:'1',view:'baseline'};
 assert.deepEqual(busChoices(info,cache,state).map(v=>v.id),['bus1','baseline-only']);assert.equal(locateBus(cache,trajectory.positions,state,'bus1').row.x,2);
 state.view='restricted';assert.equal(locateBus(cache,trajectory.positions,state,'bus1').row.x,8);assert.equal(locateBus(cache,trajectory.positions,state,'baseline-only'),null);
 state.view='compare';assert.deepEqual(new Set(busChoices(info,cache,state).map(v=>v.id)),new Set(['bus1','baseline-only','proposal-only']));assert.equal(locateBus(cache,trajectory.positions,state,'baseline-only').policy,'baseline');
});
