import test from 'node:test';
import assert from 'node:assert/strict';
import {studyLabels} from './study-labels.mjs';
test('another registered line describes its own trips, replay window and observations',()=>{
 const data={meta:{route:'702',dwell_seconds:12,time_origin_seconds:0},route:{start:'A',end:'B'},native_directions:{'1':{route:{morning:[{},{}]}}},replay_manifest:{clips:[{start:36000,end:36600,step:2}]},observations:{counts:{accepted:0}}};
 const labels=studyLabels(data,'en');assert.match(labels.analysisScope,/2 scheduled/);assert.match(labels.replayNote,/10:00.*10:10/);assert.match(labels.replayNote,/2 seconds/);assert.match(labels.limits,/12/);assert.equal(JSON.stringify(labels).includes('701'),false);assert.equal(JSON.stringify(labels).includes('127'),false);assert.match(labels.observedNote,/No matched/);
});
