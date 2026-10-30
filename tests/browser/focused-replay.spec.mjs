import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

test('focused replay preserves native time across 2D/3D and displays timetable holding',async({page})=>{
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/701-inspection/');
 await expect(page.locator('#proof')).toContainText('6,024');
 await expect(page.locator('#time')).toHaveText('20:25:30');
 await expect(page.locator('#wait')).toHaveText('8 s');
 await expect(page.locator('#lights')).toContainText('Green');
 await expect(page.locator('#layerNote')).toContainText('model movements, not physical');
 const recorded=await page.evaluate(()=>window.focusedReplay.data.windows.find(w=>w.id==='evening').frames[window.focusedReplay.index]);
 await page.locator('#signalLayer').selectOption('equipment');
 await expect(page.locator('#layerNote')).toContainText('timings unknown');
 await expect(page.locator('#auditCounts')).toContainText('installation 121');
 expect(await page.evaluate(()=>window.focusedReplay.audit.controller.movement_links)).toBe(21);
 expect(await page.evaluate(()=>window.focusedReplay.data.windows.find(w=>w.id==='evening').frames[window.focusedReplay.index])).toEqual(recorded);
 await page.locator('#signalLayer').selectOption('all');
 await expect(page.locator('#layerNote')).toContainText('not physical');
 await page.locator('#signalLayer').selectOption('osm');
 await expect(page.locator('#layerNote')).toContainText('OSM signalised-crossing');
 await expect(page.locator('#osmLinks a')).toHaveCount(7);
 await page.locator('#signalLayer').selectOption('next');
 await expect(page.locator('#schedule')).toContainText('20:12:29');
 await expect(page.locator('#schedule')).toContainText('20:18:00');
 const before=await page.evaluate(()=>window.focusedReplay.data.windows.find(w=>w.id==='evening').frames[window.focusedReplay.index]);
 await page.getByRole('button',{name:'2D',exact:true}).click();
 expect(await page.evaluate(()=>window.focusedReplay.dimension)).toBe('2d');
 await expect(page.locator('#time')).toHaveText('20:25:30');
 await page.getByRole('button',{name:'3D',exact:true}).click();
 const after=await page.evaluate(()=>window.focusedReplay.data.windows.find(w=>w.id==='evening').frames[window.focusedReplay.index]);
 expect(after).toEqual(before);
 await page.locator('#scrub').fill('350');
 await expect(page.locator('#time')).toHaveText('20:25:50');
 await expect(page.locator('#wait')).toHaveText('28 s');
 await page.locator('#journey').selectOption('morning');
 await expect(page.locator('#time')).toHaveText('06:18:00');
 await page.locator('#lang').selectOption('pt');
 await expect(page.locator('#scheduleTitle')).toHaveText('Chegar cedo, sair à hora certa');
 await expect(page.locator('#title')).toContainText('Inspecionar');
 await page.getByRole('button',{name:'Reproduzir',exact:true}).click();
 await expect.poll(async()=>page.locator('#time').textContent()).not.toBe('06:18:00');
 await page.getByRole('button',{name:'Pausar',exact:true}).click();
 expect(errors).toEqual([]);
});

test('focused replay rejects altered capture bytes',async({page})=>{
 await page.route('**/replay.json.gz',async route=>{const response=await route.fetch();const bytes=await response.body();bytes[11]^=1;await route.fulfill({response,body:bytes});});
 await page.goto('/701-inspection/');
 await expect(page.locator('#load')).toContainText('Unable to load the verified replay');
 expect(await page.evaluate(()=>window.focusedReplay)).toBeUndefined();
});

test('a validly hashed signal audit cannot describe another network',async({page})=>{
 const audit=JSON.parse(await readFile('prototypes/line-701/focused-replay/signal-audit.json','utf8'));
 audit.network_sha256='0'.repeat(64);const body=JSON.stringify(audit);
 await page.route('**/signal-audit.json',route=>route.fulfill({contentType:'application/json',body}));
 await page.route('**/signal-audit-index.json',route=>route.fulfill({contentType:'application/json',body:JSON.stringify({sha256:createHash('sha256').update(body).digest('hex'),network_sha256:audit.network_sha256})}));
 await page.goto('/701-inspection/');
 await expect(page.locator('#load')).toContainText('Unable to load the verified replay');
 expect(await page.evaluate(()=>window.focusedReplay)).toBeUndefined();
});

test('2D inspection remains usable without WebGL',async({page})=>{
 await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return String(kind).includes('webgl')?null:original.call(this,kind,...args);};});
 await page.goto('/701-inspection/');
 await expect(page.locator('#b3')).toBeDisabled();
 await expect(page.locator('#proof')).toContainText('6,024');
 expect(await page.evaluate(()=>window.focusedReplay.dimension)).toBe('2d');
 await page.locator('#scrub').fill('350');
 await expect(page.locator('#wait')).toHaveText('28 s');
});

test('phone layout keeps the inspection within the viewport',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/701-inspection/');
 await expect(page.locator('#proof')).toContainText('6,024');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByRole('button',{name:'2D',exact:true}).click();
 await expect(page.locator('#time')).toHaveText('20:25:30');
});

test('OSM source links keep keyboard focus while playback advances',async({page})=>{
 await page.goto('/701-inspection/?signals=osm&dimension=2d');
 await expect(page.locator('#proof')).toContainText('6,024');
 await page.locator('#osmSourceTitle').click();
 await page.getByRole('button',{name:'Play',exact:true}).click();
 const link=page.locator('#osmLinks a').first();
 await link.focus();
 const frame=await page.evaluate(()=>window.focusedReplay.index);
 await expect.poll(()=>page.evaluate(()=>window.focusedReplay.index)).toBeGreaterThan(frame);
 expect(await link.evaluate(el=>document.activeElement===el)).toBe(true);
});
