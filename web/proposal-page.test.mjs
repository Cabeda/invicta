import test from 'node:test';
import assert from 'node:assert/strict';
import {publicProposal,proposalPageHTML,deliveryMarkdown} from './proposal-page.mjs';
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
test('unprepared requested restrictions are described as a draft, not a tested baseline',()=>{
 const value=structuredClone(proposal);value.native.variant='all_priority';value.native.available=false;value.native.alternative=null;
 const html=proposalPageHTML(value,line,'en');assert.match(html,/not been simulated/);assert.equal(html.includes('The baseline is selected'),false);assert.equal(html.includes('This package was tested jointly'),false);
});
test('a prepared study cannot inherit another line’s access rules or bidirectional comparison claims',()=>{
 const value=structuredClone(proposal);value.native.variant='restricted';value.native.scope={simulated_directions:['1']};
 const html=proposalPageHTML(value,line,'en');assert.equal(html.includes('both directions'),false);assert.equal(html.includes('signals are the same'),false);assert.equal(html.includes('admitting residents'),false);
});
test('report rollout phases retain the same reversible pilot and unknown-cost conditions',()=>{
 const text=deliveryMarkdown('en');assert.match(text,/Run a reversible pilot/);assert.match(text,/Measure and adapt/);assert.match(text,/Costs: not yet estimated/);assert.equal((text.match(/^### /gm)||[]).length,4);
});
