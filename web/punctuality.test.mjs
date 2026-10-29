import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluatePunctuality,minimumChangeProposal} from './punctuality.mjs';
const trip=(id='one',departure=100,arrival=200)=>({id,trip_id:id,direction:'1',completed:true,stops:[{stop_id:'a',scheduled:100,arrival:90,departure},{stop_id:'b',scheduled:200,arrival,departure:200}]});
test('missing scheduled departures remain in the goal denominator',()=>{
 const result=evaluatePunctuality([trip()],0,[trip(),trip('missing')]);
 assert.equal(result.planned,2);assert.equal(result.starts.missing,1);assert.equal(result.finishes.missing,1);assert.equal(result.bothOnTime,1);assert.equal(result.passes,false);
});
test('minimum-change selection rejects unknown access effects instead of treating them as zero',()=>{
 const metrics=evaluatePunctuality([trip()]),result=minimumChangeProposal([{id:'unknown',changedLaneMetres:10,changeCount:1,cases:[{id:'busy',metrics,demandComparable:true,extraUnserved:NaN}]}],['busy']);
 assert.equal(result.winner,null);assert.ok(result.assessed[0].reasons.includes('unknown_access_effect'));
});
test('a completed but late trip is a failure; short trips use their own endpoints and early departures fail',()=>{
 assert.equal(evaluatePunctuality([trip('late',100,201)]).passes,false);
 assert.equal(evaluatePunctuality([trip('early',99,190)]).passes,false);
 assert.equal(evaluatePunctuality([trip('short',100,190)]).passes,true);
 assert.equal(evaluatePunctuality([trip('late',101,201)],1).passes,true);
 assert.equal(evaluatePunctuality([]).passes,false);
 assert.throws(()=>evaluatePunctuality([trip(),trip()]),/duplicate/);
});
test('the smallest qualifying tested package wins only after every required case passes',()=>{
 const metrics=evaluatePunctuality([trip()]),cases=['moderate','busy'].map(id=>({id,metrics,demandComparable:true,extraUnserved:0}));
 const plan=(id,metres,count=1)=>({id,changedLaneMetres:metres,changeCount:count,cases});
 let result=minimumChangeProposal([plan('wide',200),plan('small',50),{...plan('untested',1),cases:cases.slice(0,1)}, {...plan('worse-access',1),cases:[{...cases[0],extraUnserved:1},cases[1]]}],['moderate','busy']);
 assert.equal(result.winner,'small');assert.equal(result.globalOptimumProven,false);assert.equal(result.assessed[2].eligible,false);assert.equal(result.assessed[3].eligible,false);
 result=minimumChangeProposal([{...plan('fails',0),cases:[{...cases[0],metrics:evaluatePunctuality([trip('late',100,201)])}]}],['moderate','busy']);
 assert.equal(result.status,'no_qualifying_proposal');assert.equal(result.winner,null);
});
