import test from 'node:test';
import assert from 'node:assert/strict';
import {publicProposal,proposalPageHTML} from './proposal-page.mjs';
const line={id:'702',name:{en:'702 · Example',pt:'702 · Exemplo'},description:{en:'An example route',pt:'Um percurso de exemplo'}};
const metrics={planned:2,starts:{onTime:2},finishes:{onTime:1,missing:1},bothOnTime:1,passes:false};
const proposal={reference:{valid:true},focus:{direction:'1'},native:{available:true,case:'busy',baseline:{punctuality:metrics},alternative:{punctuality:metrics},applied_priority_edges:[],decision:{winner:null}}};
test('public explanation leads with an explicit goal and explains punctuality rather than completion',()=>{
 const story=publicProposal(proposal,line,'en');assert.equal(story.lineName,'702 · Example');assert.equal(story.evidence.arrivalsAfter,'1 / 2');assert.match(story.status,/No tested plan/);
 const html=proposalPageHTML(proposal,line,'en');assert.match(html,/Finishing a trip does not mean it was on time/);assert.match(html,/missing and count as failures/);assert.equal(html.includes('unserved vehicle requests'),false);assert.match(html,/none of|None of/);
});
test('a passing selected case cannot be described as validated for all scenarios',()=>{
 const value=structuredClone(proposal);value.native.alternative.punctuality.passes=true;assert.match(publicProposal(value,line,'en').status,/Other required cases and field validation/);
});
