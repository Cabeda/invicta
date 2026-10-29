import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
test('a new visitor sees the purpose and line explanation before the simulation tools',async({page})=>{
 await page.goto('/?lang=en');await page.waitForFunction(()=>!!window.reviewedProposal701);
 await expect(page.locator('#pageTitle')).toBeInViewport();expect(await page.evaluate(()=>scrollY)).toBeLessThan(50);
 await expect(page.locator('#proposalStory')).toContainText('Give buses priority');
});
test('public story, 2D/3D simulation, sharing, drafts and 2D video retain one proposal',async({page,context})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/?lineId=701&lang=en&case=moderate&view=compare#replay');
 await page.waitForFunction(()=>window.inspection2D701?.debug().loaded);
 await expect(page.locator('#pageTitle')).toHaveText('A bus you can plan your day around.');
 await expect(page.locator('#proposalStory')).toContainText('Every departure on time. Every arrival within the schedule.');
 await expect(page.locator('#punctualityProof')).not.toHaveAttribute('open');
 const before=Number(await page.locator('#timeline').inputValue());await page.locator('#playBtn').click();
 await expect.poll(async()=>Number(await page.locator('#timeline').inputValue())).toBeGreaterThan(before);await page.locator('#playBtn').click();
 const time=await page.locator('#timeline').inputValue();
 await page.locator('#view3d').click();await page.waitForFunction(()=>window.inspection701?.debug().loaded);
 expect(await page.locator('#timeline').inputValue()).toBe(time);await page.locator('#view2d').click();await page.waitForFunction(()=>window.reviewedProposal701.selection.dimension==='2d'&&window.inspection2D701.debug().loaded);
 await page.locator('#viewDirection').selectOption('0');await page.waitForFunction(()=>window.reviewedProposal701.focus.direction==='0'&&window.inspection2D701.debug().loaded);
 await page.locator('#zoom2dIn').click();await page.locator('#shareBtn').click();const shared=page.url(),pose=await page.evaluate(()=>window.inspection2D701.pose());
 const reopened=await context.newPage();await reopened.goto(shared);await reopened.waitForFunction(()=>window.inspection2D701?.debug().loaded);
 expect(await reopened.evaluate(()=>window.reviewedProposal701.focus.direction)).toBe('0');expect(await reopened.evaluate(()=>window.inspection2D701.pose())).toEqual(pose);await reopened.close();
 await page.locator('#variant').selectOption('all_priority');await expect(page.locator('#replayArea')).toBeHidden();await expect(page.locator('#view3d')).toBeDisabled();await expect(page.locator('#proposalStory')).toContainText('has not been simulated');
 await page.locator('#variant').selectOption('restricted');await page.waitForFunction(()=>window.inspection2D701.debug().loaded);await expect(page.locator('#recordBtn')).toBeEnabled();
 const downloads=[];page.on('download',d=>downloads.push(d));await page.locator('#recordBtn').click();await expect(page.locator('#recordBtn')).toHaveText('Finish recording');await page.waitForTimeout(700);await page.locator('#recordBtn').click();
 await expect.poll(()=>downloads.length).toBe(2);
 const video=downloads.find(d=>d.suggestedFilename().endsWith('.webm')),json=downloads.find(d=>d.suggestedFilename().endsWith('.json'));
 const movie=await readFile(await video.path()),sidecar=JSON.parse(await readFile(await json.path(),'utf8'));
 expect(movie.subarray(0,4).toString('hex')).toBe('1a45dfa3');expect(movie.length).toBeGreaterThan(1000);expect(sidecar.review.selection.dimension).toBe('2d');expect(sidecar.recording.end).toBeGreaterThan(sidecar.recording.start);expect(video.suggestedFilename()).toContain(sidecar.review.id);
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(390);expect(errors).toEqual([]);
});

test('an unpublished second-line fixture uses its own descriptions and report exports',async({page})=>{
 const site='prototypes/costa-cabral/proposal/',catalog=JSON.parse(await readFile(site+'lines.json','utf8')),data=JSON.parse(await readFile(site+'701-data.json','utf8')),reference=JSON.parse(await readFile(site+'701-line-explorer.json','utf8'));
 const line={...catalog.lines[0],id:'702',name:{en:'702 · Test registration',pt:'702 · Registo de teste'},description:{en:'An unpublished test line',pt:'Uma linha de teste não publicada'},data:'702-data.json',reference:'702-reference.json',report:'702-report.md',sourceUrl:'https://example.test/702',capabilities:{serviceModel:false},assets:{experiments:'702-experiments.json',sources:'702-sources.json'},caseLabels:{moderate:{en:'702 demand case',pt:'Caso de procura 702'}}};
 catalog.lines.push(line);data.full_traffic_summary.trip_count=2;data.meta={...data.meta,route:'702',dwell_seconds:12};data.reference_id='test702';data.replay_manifest.scope.route='702';
 for(const direction of Object.keys(data.native_directions)){const d=data.native_directions[direction];d.meta={...d.meta,route:'702',dwell_seconds:12};d.route.morning=d.route.morning.slice(0,1);reference.directions[direction].trips=reference.directions[direction].trips.slice(0,1)}
 data.route.morning=data.route.morning.slice(0,1);data.replay_manifest.clips.forEach(c=>{c.start=36000;c.end=36600;c.step=2});reference.route='702';
 await page.route('**/lines.json',route=>route.fulfill({json:catalog}));await page.route('**/702-data.json',route=>route.fulfill({json:data}));await page.route('**/702-reference.json',route=>route.fulfill({json:reference}));
 await page.goto('/?lineId=702&lang=en&case=moderate&variant=all_priority');await page.waitForFunction(()=>window.reviewedProposal701?.native.line==='702');
 await expect(page.locator('#analysis')).toContainText('2 scheduled departures');await expect(page.locator('#replay')).toContainText('10:00–10:10');await expect(page.locator('#replay')).toContainText('2 seconds');
 await expect(page.locator('#case')).toContainText('702 demand case');await expect(page.locator('[data-t="nativeExport"]')).toHaveAttribute('href','702-experiments.json');await expect(page.locator('[data-t="sourceExport"]')).toHaveAttribute('href','702-sources.json');
 await expect(page.locator('#proposalStory')).toContainText('has not been simulated');
 const downloadEvent=page.waitForEvent('download');await page.locator('#reportBtn').click();const report=await downloadEvent,text=await readFile(await report.path(),'utf8');expect(report.suggestedFilename()).toMatch(/^702-/);expect(text).toContain('# 702');expect(text).toContain('https://example.test/702');expect(text).toContain('Phased implementation');expect(text).toContain('Run a reversible pilot');expect(text).toContain('Costs: not yet estimated');
});
