import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createLineExplorer} from './line-explorer.mjs';

const data = JSON.parse(readFileSync(new URL('../costa-cabral/proposal/701-line-explorer.json', import.meta.url)));
// The narrower prepared-study fixture tests geographic scope independently of any newer full-line study.
data.native={direction:'1',from:'ARS3',to:'0BLRB',window:'08:10–08:40'};

test('full geography and timetable retain each direction, including Ermesinde', () => {
  const explorer = createLineExplorer(data);
  assert.equal(explorer.view().stops.length, 56);
  assert.equal(explorer.view().dir.shape.length, 548);
  assert.equal(explorer.view().through.length, 39);
  assert.ok(explorer.view().stops.some(s => s.stop_id === 'ERM3'));
  const outbound = explorer.select({direction: '0'});
  assert.equal(outbound.stops.length, 54);
  assert.equal(outbound.dir.shape.length, 506);
  assert.equal(outbound.stops[0].stop_id, 'BLRB3');
  assert.equal(outbound.through.length, 41);
  assert.equal(outbound.coverage, 'none');
  assert.equal(outbound.operational, false);
});

test('direction switching preserves independent contiguous sections and trips', () => {
  const explorer = createLineExplorer(data);
  const inbound = explorer.select({from: 'ERM3', to: 'ARS3'});
  assert.equal(inbound.through.length, 63);
  assert.equal(inbound.coverage, 'none');
  explorer.select({direction: '0', from: 'ARS2', to: 'ERM4'});
  const outbound = explorer.view();
  assert.equal(outbound.through.length, 63);
  const restored = explorer.select({direction: '1'});
  assert.deepEqual(restored.stops.map(s => s.stop_id), inbound.stops.map(s => s.stop_id));
  assert.equal(restored.trip.trip_id, inbound.trip.trip_id);
  assert.deepEqual(explorer.select({direction: '0'}).stops, outbound.stops);
});

test('short workings keep unserved stops missing rather than inventing journey times', () => {
  const explorer = createLineExplorer(data);
  const short = data.directions['1'].trips.find(t => t.originstatus.origin_stop_id === 'ERM3');
  const selected = explorer.select({trip: short.trip_id});
  assert.equal(selected.trip.stops.COD4, null);
  assert.equal(selected.seconds, null);
  assert.ok(Number.isFinite(selected.trip.stops.ERM3));
  const outboundShort = data.directions['0'].trips.find(t => t.terminalstatus.terminal_stop_id === 'ERM4');
  explorer.select({direction: '0', trip: outboundShort.trip_id});
  assert.equal(explorer.view().trip.stops.COD4, null);
  assert.equal(explorer.view().seconds, null);
});

test('native replay coverage is independent of showing a whole-line map', () => {
  const explorer = createLineExplorer(data);
  assert.equal(explorer.view().coverage, 'partial');
  assert.equal(explorer.select({from: 'ARS3', to: '0BLRB'}).coverage, 'full');
  assert.equal(explorer.select({from: 'MPL7', to: 'MPL4'}).coverage, 'full');
  assert.equal(explorer.select({direction: '0', from: 'BLRB3', to: 'ARS2'}).coverage, 'none');
});

test('shared selection restores both directions, selected trip and reading mode', () => {
  const explorer = createLineExplorer(data);
  explorer.select({from: 'ERM3', to: 'ARS3'});
  explorer.select({direction: '0', from: 'ARSM1', to: 'ERM4', detail: true, zoom: true});
  const trip = explorer.view().trips.at(-1).trip_id;
  explorer.select({trip});
  const reopened = createLineExplorer(data, JSON.stringify(explorer.settings()));
  assert.deepEqual(reopened.settings(), explorer.settings());
  assert.equal(reopened.view().trip.trip_id, trip);
  assert.equal(reopened.select({direction: '1'}).stops[0].stop_id, 'ERM3');
});

test('invalid shared state falls back to valid direction-specific ranges', () => {
  for (const input of ['invalid JSON', 'null', {direction: '__proto__'}, {direction: 'constructor'}, {direction: '99', focus: {'1': ['0BLRB', 'COD4']}, trips: {'1': 'unknown'}}]) {
    const explorer = createLineExplorer(data, input), view = explorer.view();
    assert.equal(view.direction, '1');
    assert.equal(view.start, 0);
    assert.equal(view.end, 55);
    assert.ok(view.trip);
    assert.equal(explorer.select({direction: 'constructor'}).direction, '1');
  }
});

test('ordered shape matching preserves loops and a plausible Porto section length', () => {
  const explorer = createLineExplorer(data);
  for (const direction of ['1', '0']) {
    const view = explorer.select({direction});
    assert.ok(view.dir.matches.every((p, i, all) => i === 0 || p.progress >= all[i - 1].progress));
    assert.ok(view.dir.matches.every(p => Math.sqrt(p.cost) < 150), 'Official stops should remain near their own ordered route');
  }
  const porto = explorer.select({direction: '1', from: 'ARS3', to: '0BLRB'});
  assert.ok(porto.metres > 4000 && porto.metres < 5000);
  assert.match(explorer.summaryText(), /ARS3/);
  assert.match(explorer.summaryText(), /Synthetic traffic; not measured delay/);
});
