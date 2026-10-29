import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createProposal} from './proposal.mjs';
import {citizenStory,urbanistReport} from './proposal-views.mjs';
import {createLineExplorer} from './line-explorer.mjs';
const site=new URL('../costa-cabral/proposal/',import.meta.url);
const html=readFileSync(new URL('index.html',site),'utf8');
const bundle=JSON.parse(html.match(/<script type="application\/json" id="line-data">([\s\S]*?)<\/script>/)[1]);
const data=createProposal(bundle).dataFor({line:{direction:'1'}});
const defaultCase=Object.hasOwn(data.cases,'busy')?'busy':Object.keys(data.cases)[0];
const reference=JSON.parse(readFileSync(new URL('701-line-explorer.json',site),'utf8'));
const setup=(source=data)=>{const model=createProposal(source),selection=model.restore('https://example.test/?lang=en#route'),line=createLineExplorer(reference,selection.line);return {model,selection,line}};

test('one shared proposal restores section, interval, evidence, settings and pose',()=>{
 const {model,selection,line}=setup();line.select({from:'ARS3',to:'0BLRB',detail:true});
 const input={...selection,line:line.settings(),selectedLeg:'leg_09',service:{capacity:80},pose:{position:[1,2,3],target:[2,3,4],yaw:.2,pitch:-.1},audience:'urbanist'};
 const reviewed=model.review(input,{line:line.view()}),url=model.shareURL(reviewed,'https://example.test/?old=ignored');
 const restored=model.restore(url),reopened=model.review(restored,{line:createLineExplorer(reference,restored.line).view()});
 assert.equal(reopened.id,reviewed.id);assert.equal(restored.selectedLeg,'leg_09');assert.deepEqual(restored.pose,input.pose);assert.deepEqual(restored.line,line.settings());assert.equal(restored.observation,selection.observation);
 assert.ok(url.hash.startsWith('#proposal='));assert.equal(url.searchParams.has('old'),false);
});
test('drafts retain their policy and cannot inherit the candidate replay',()=>{
 const {model,selection,line}=setup();const value=model.review({...selection,variant:'draft',priority:['leg_01','leg_08']},{line:line.view()});
 assert.equal(value.selection.variant,'draft');assert.deepEqual(value.native.priority,['leg_01','leg_08']);assert.equal(value.replay.eligible,false);assert.equal(value.replay.reason,'unprepared_policy');assert.equal(value.native.alternative,null);
});
test('source version changes withhold the old proposal results',()=>{
 const {model,selection,line}=setup();const value=model.review({...selection,reference:'old-source-reference'},{line:line.view()});
 assert.equal(value.reference.valid,false);assert.equal(value.native.available,false);assert.equal(value.native.baseline,null);assert.equal(value.replay.reason,'reference_changed');
 assert.equal(model.restore(model.shareURL(value,'https://example.test/')).reference,'old-source-reference');
});
test('selected uploaded arrivals are portable and never become GPS evidence',()=>{
 const {model,selection,line}=setup(),trip=Object.values(data.observations.timetables)[0],stop=data.route.stops[0];
 const at=new Date(Date.parse(data.study_midnight)+(trip.stops[stop.stop_id]+45)*1000).toISOString();
 const imported=model.importArrivals([{trip_id:trip.trip_id,stop_id:stop.stop_id,observed_arrival:at}]);assert.equal(imported.accepted,1);
 const reviewed=model.review({...selection,observation:imported.trips[0].trip_id},{line:line.view()});assert.equal(reviewed.evidence.kind,'uploaded_arrivals');
 const url=model.shareURL(reviewed,'https://example.test/');assert.equal(url.searchParams.has('upload'),false);
 const fresh=createProposal(data),restored=fresh.restore(url),reopened=fresh.review(restored,{line:line.view()});
 assert.equal(reopened.evidence.kind,'uploaded_arrivals');assert.equal(reopened.evidence.passages[0].lateness_low,45);assert.equal(reopened.evidence.trip_id,reviewed.evidence.trip_id);
 assert.match(urbanistReport(reopened),/User-supplied arrivals, not independently verified/);
});
test('arrival imports reject unknown, duplicate and wrong-date records',()=>{
 const {model}=setup(),trip=Object.values(data.observations.timetables)[0],stop=data.route.stops[0];
 const at=new Date(Date.parse(data.study_midnight)+trip.stops[stop.stop_id]*1000).toISOString(),row={trip_id:trip.trip_id,stop_id:stop.stop_id,at};
 const result=model.importArrivals([row,row,{...row,stop_id:'unknown'},{...row,at:'2026-10-27T12:00:00Z'}]);assert.equal(result.accepted,1);assert.equal(result.rejected,3);
});
test('reports derive findings from structured evidence, not rendered text',()=>{
 const {model,selection,line}=setup(),value=model.review({...selection,observedFinding:'FAKE DOM FINDING'},{line:line.view()});
 const text=urbanistReport(value);assert.equal(text.includes('FAKE DOM FINDING'),false);assert.equal('observedFinding' in value.serial.selection,false);assert.ok(text.includes(value.evidence.trip_id));
});
test('incomplete/unserved comparisons cannot generate a citizen gain claim',()=>{
 const source=structuredClone(data);source.cases[defaultCase].restricted.groups.through.unserved+=1;
 const {model,selection,line}=setup(source),value=model.review({...selection,case:defaultCase},{line:line.view()});
 assert.equal(value.native.can_claim_gain,false);assert.equal(citizenStory(value).metrics.change_minutes,null);assert.match(citizenStory(value).summary,/incomplete journeys or unserved demand/);
});
test('a mismatched capture signature or direction cannot offer a substitute replay',()=>{
 const bad=structuredClone(data);bad.replay_manifest.clips[0].capture_signature='wrong';const {model,selection,line}=setup(bad);
 const value=model.review({...selection,case:bad.replay_manifest.clips[0].case},{line:line.view()});assert.equal(value.replay.reason,'unmatched_capture');
 const other=model.review(selection,{line:line.select({direction:'0'})});assert.equal(other.native.available,false);assert.equal(other.replay.reason,'outside_coverage');assert.equal(other.evidence.kind,'outside_coverage');
});
test('malformed legacy and versioned URL values fall back without crashing',()=>{
 const {model}=setup();for(const url of ['https://example.test/?case=constructor&service=broken','https://example.test/#proposal=%','https://example.test/#proposal=null'])assert.equal(model.restore(url).case,defaultCase);
});
test('missing native arrivals remain missing in the urbanist report',()=>{
 const source=structuredClone(data),trip=source.route.morning[0].id;source.cases[defaultCase].restricted.trips[trip].stops[0].lateness.mean=null;
 const {model,selection,line}=setup(source),value=model.review(selection,{line:line.view()}),report=urbanistReport(value);
 const row=report.split('\n').find(s=>s.startsWith('| '+source.route.stops[0].stop_id+' '));assert.ok(row.endsWith('| — |'),row);
});

test('after-midnight service arrivals keep their original service day',()=>{
 const {model}=setup();const trip=Object.values(data.observations.timetables).find(t=>Object.values(t.stops).some(n=>n>86400));const [stop_id,seconds]=Object.entries(trip.stops).find(([,n])=>n>86400);
 const at=new Date(Date.parse(data.study_midnight)+(seconds+30)*1000).toISOString();const imported=model.importArrivals([{trip_id:trip.trip_id,stop_id,at}]);
 assert.equal(imported.accepted,1);assert.equal(imported.trips[0].passages[0].lateness_low,30);
});

test('raw uploaded evidence survives a stale reference with removed trip identities',()=>{
 const {model,selection,line}=setup(),trip=Object.values(data.observations.timetables)[0],stop=data.route.stops[0];
 const at=new Date(Date.parse(data.study_midnight)+(trip.stops[stop.stop_id]+30)*1000).toISOString();
 const imported=model.importArrivals([{trip_id:trip.trip_id,stop_id:stop.stop_id,at}]);
 const original=model.review({...selection,observation:imported.trips[0].trip_id},{line:line.view()});
 const changed=structuredClone(data);changed.reference_id='new-source-version';delete changed.observations.timetables[trip.trip_id];
 const newer=createProposal(changed),restored=newer.restore(model.shareURL(original,'https://example.test/'));
 const withheld=newer.review(restored,{line:line.view()});
 assert.equal(withheld.reference.valid,false);assert.equal(withheld.evidence.kind,'reference_changed');
 assert.deepEqual(withheld.serial.upload,original.serial.upload);
 const exportedAgain=newer.review(newer.restore(newer.shareURL(withheld,'https://example.test/')),{line:line.view()});
 assert.deepEqual(exportedAgain.serial.upload,original.serial.upload);
});


test('both full native directions share one proposal and retain the opposite policy',()=>{
 const model=createProposal(bundle),selection=model.restore('https://example.test/?direction=0&case=moderate'),line=createLineExplorer(reference,selection.line);
 const reviewed=model.review(selection,{line:line.view()});
 assert.equal(reviewed.focus.direction,'0');assert.equal(String(reviewed.native.scope.direction),'0');assert.equal(reviewed.native.available,true);assert.equal(reviewed.native.alternative.planned,64);assert.equal(reviewed.replay.eligible,true);
 const restored=model.restore(model.shareURL(reviewed,'https://example.test/'));
 assert.equal(model.review(restored,{line:createLineExplorer(reference,restored.line).view()}).id,reviewed.id);
 const policy=structuredClone(selection.policy_by_direction);policy['1']=[];
 const draft=model.review({...selection,policy_by_direction:policy},{line:line.view()});
 assert.equal(draft.native.available,false);assert.equal(draft.replay.eligible,false);
});
test('only prepared cases can become the default selection',()=>{
 const source=structuredClone(data);source.cases={moderate:source.cases.moderate};const model=createProposal(source);
 assert.equal(model.restore('https://example.test/?case=busy').case,'moderate');
});

test('evidence findings follow the chosen section while raw arrivals remain portable',()=>{
 const {model,selection,line}=setup(),trip=Object.values(data.observations.timetables).find(t=>data.route.stops.every(s=>Number.isFinite(t.stops[s.stop_id]))),stops=data.route.stops;
 const result=model.importArrivals(stops.slice(0,2).map((s,i)=>({trip_id:trip.trip_id,stop_id:s.stop_id,observed_arrival:new Date(Date.parse(data.study_midnight)+(trip.stops[s.stop_id]+i*120)*1000).toISOString()})));
 assert.equal(result.accepted,2);const observation=result.trips[0].trip_id;
 let review=model.review({...selection,observation},{line:line.view()});assert.ok(review.evidence.finding);
 line.select({from:stops.at(-2).stop_id,to:stops.at(-1).stop_id});review=model.review({...selection,observation},{line:line.view()});
 assert.equal(review.evidence.finding,null);assert.equal(review.evidence.focus.captured_stops,0);assert.equal(review.evidence.passages.length,2);assert.equal(review.serial.upload.arrivals.length,2);
});
