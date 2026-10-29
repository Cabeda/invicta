import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateStudy} from './study-reliability.mjs';
const trip={id:'a',trip_id:'a',direction:'1',completed:true,stops:[{stop_id:'s',scheduled:10,arrival:0,departure:10},{stop_id:'e',scheduled:20,arrival:20,departure:20}]};
test('publication evaluates repeated native seeds separately before combining identical scheduled IDs',()=>{
 const raw={meta:{cases:['busy'],seeds:[17,42]},route_reference:{directions:{'1':{trips:[trip]}}},geometry:[{id:'road',shape:[[0,0],[10,0]]}],access:{changes:[{edge:'road'}]},runs:[]};
 for(const seed of raw.meta.seeds)for(const variant of ['baseline','restricted'])raw.runs.push({case:'busy',seed,variant,buses:[trip],inputs:{demand:'same'},groups:{bus:{planned:1,unserved:0}}});
 const result=evaluateStudy(raw),metrics=result.directions['1'].busy.restricted;
 assert.equal(metrics.planned,2);assert.equal(metrics.bothOnTime,2);assert.equal(metrics.runs,2);assert.equal(metrics.scheduledTripsPerRun,1);assert.equal(result.decision.winner,'baseline');
});
