// Line identity, independent direction focus and evidence coverage share one seam.
const finite = value => typeof value === 'number' && Number.isFinite(value);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clock = value => finite(value) ? `${String(Math.floor(value / 3600)).padStart(2, '0')}:${String(Math.floor(value / 60) % 60).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}` : '—';

// Fit every stop to the ordered shape together. Independent nearest points can
// jump to the wrong pass through a junction or loop and reverse the focus.
function locateStops(stops, shape) {
  const cos = Math.cos(stops.reduce((sum, s) => sum + s.stop_lat, 0) / stops.length * Math.PI / 180);
  const xy = ([lon, lat]) => [lon * 111320 * cos, lat * 111320];
  const points = shape.map(xy), lengths = [0];
  for (let i = 1; i < points.length; i++) lengths.push(lengths.at(-1) + Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
  const candidates = stops.map(stop => {
    const p = xy([stop.stop_lon, stop.stop_lat]);
    return points.slice(0, -1).map((a, j) => {
      const b = points[j + 1], dx = b[0] - a[0], dy = b[1] - a[1], squared = dx * dx + dy * dy;
      const t = squared ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / squared)) : 0;
      return {progress: lengths[j] + t * Math.sqrt(squared), cost: (p[0] - a[0] - t * dx) ** 2 + (p[1] - a[1] - t * dy) ** 2,
        point: shape[j].map((v, k) => v + t * (shape[j + 1][k] - v)), edge: j};
    });
  });
  let previous = candidates[0].map(c => c.cost);
  const parents = [];
  for (let i = 1; i < stops.length; i++) {
    const current = [], parent = []; let best = Infinity, bestIndex = -1;
    for (let j = 0; j < previous.length; j++) {
      if (j && previous[j - 1] < best) { best = previous[j - 1]; bestIndex = j - 1; }
      let cost = best, index = bestIndex;
      if (candidates[i - 1][j].progress <= candidates[i][j].progress && previous[j] < cost) { cost = previous[j]; index = j; }
      current[j] = cost + candidates[i][j].cost; parent[j] = index;
    }
    previous = current; parents.push(parent);
  }
  let j = previous.indexOf(Math.min(...previous)); const matches = [];
  for (let i = stops.length - 1; i >= 0; i--) { matches[i] = candidates[i][j]; if (i) j = parents[i - 1][j]; }
  return {matches, lengths};
}

export function createLineExplorer(data, initial = {}) {
  if (typeof initial === 'string') { try { initial = JSON.parse(initial); } catch { initial = {}; } }
  if (!initial || typeof initial !== 'object') initial = {};
  const directions = Object.fromEntries(Object.entries(data.directions).map(([id, raw]) => {
    if (raw.stops.length < 2 || raw.shape.length < 2) throw Error(`Incomplete direction ${id}`);
    return [id, {...raw, ...locateStops(raw.stops, raw.shape)}];
  }));
  const state = {direction: Object.hasOwn(directions, String(initial.direction)) ? String(initial.direction) : (Object.hasOwn(directions,'1')?'1':Object.keys(directions)[0]), focus: {}, trips: {}, detail: initial.detail === true, zoom: initial.zoom === true};
  if (!Object.hasOwn(directions, state.direction)) state.direction = Object.keys(directions)[0];
  for (const [id, dir] of Object.entries(directions)) {
    const saved = initial.focus?.[id], start = dir.stops.findIndex(s => s.stop_id === saved?.[0]), end = dir.stops.findIndex(s => s.stop_id === saved?.[1]);
    state.focus[id] = start >= 0 && end > start ? [saved[0], saved[1]] : [dir.stops[0].stop_id, dir.stops.at(-1).stop_id];
    state.trips[id] = dir.trips.some(t => t.trip_id === initial.trips?.[id]) ? initial.trips[id] : null;
  }
  const settings = () => structuredClone(state);
  function view() {
    const dir = directions[state.direction], [from, to] = state.focus[state.direction];
    const start = dir.stops.findIndex(s => s.stop_id === from), end = dir.stops.findIndex(s => s.stop_id === to), stops = dir.stops.slice(start, end + 1);
    const firstTime = trip => stops.map(s => trip.stops[s.stop_id]).find(finite);
    const trips = dir.trips.filter(t => stops.some(s => finite(t.stops[s.stop_id]))).sort((a, b) => firstTime(a) - firstTime(b));
    const through = trips.filter(t => stops.every(s => finite(t.stops[s.stop_id])));
    let trip = trips.find(t => t.trip_id === state.trips[state.direction]);
    if (!trip) { trip = through[0] || trips[0]; state.trips[state.direction] = trip?.trip_id ?? null; }
    const a = dir.matches[start], b = dir.matches[end];
    const focusShape = [a.point, ...dir.shape.filter((_, i) => dir.lengths[i] > a.progress && dir.lengths[i] < b.progress), b.point];
    const native = data.native.directions?.[state.direction] || data.native, nativeDir = Object.hasOwn(data.native.directions||{},state.direction) || state.direction === String(native.direction), ns = dir.stops.findIndex(s => s.stop_id === native.from), ne = dir.stops.findIndex(s => s.stop_id === native.to);
    const coverage = !nativeDir || ns < 0 || ne < 0 || end <= ns || start >= ne ? 'none' : start >= ns && end <= ne ? 'full' : 'partial';
    const seconds = trip && finite(trip.stops[from]) && finite(trip.stops[to]) ? trip.stops[to] - trip.stops[from] : null;
    return {direction: state.direction, dir, start, end, stops, trips, through, trip, focusShape, metres: b.progress - a.progress, seconds, coverage,
      operational: state.direction === String(data.operational_direction), nativeShape: nativeDir && ns >= 0 && ne > ns ? [dir.matches[ns].point, ...dir.shape.filter((_, i) => dir.lengths[i] > dir.matches[ns].progress && dir.lengths[i] < dir.matches[ne].progress), dir.matches[ne].point] : []};
  }
  function select(change) {
    if (Object.hasOwn(directions, String(change.direction))) state.direction = String(change.direction);
    const dir = directions[state.direction], current = state.focus[state.direction];
    let start = dir.stops.findIndex(s => s.stop_id === current[0]), end = dir.stops.findIndex(s => s.stop_id === current[1]);
    if (change.whole) { start = 0; end = dir.stops.length - 1; }
    if (change.from && dir.stops.some(s => s.stop_id === change.from)) {
      start = Math.min(dir.stops.length - 2, dir.stops.findIndex(s => s.stop_id === change.from)); end = Math.max(end, start + 1);
    }
    if (change.to && dir.stops.some(s => s.stop_id === change.to)) {
      end = Math.max(1, dir.stops.findIndex(s => s.stop_id === change.to)); start = Math.min(start, end - 1);
    }
    state.focus[state.direction] = [dir.stops[start].stop_id, dir.stops[end].stop_id];
    if (dir.trips.some(t => t.trip_id === change.trip)) state.trips[state.direction] = change.trip;
    if (typeof change.detail === 'boolean') state.detail = change.detail;
    if (typeof change.zoom === 'boolean') state.zoom = change.zoom;
    return view();
  }
  function summaryText(lang = 'en') {
    const v = view(), pt = lang === 'pt', native=data.native.directions?.[v.direction]||data.native;
    return [`# ${data.route} · ${v.dir.origin} → ${v.dir.destination}`, '', `${pt ? 'Secção em análise' : 'Focus section'}: ${v.stops[0].stop_name} (${v.stops[0].stop_id}) → ${v.stops.at(-1).stop_name} (${v.stops.at(-1).stop_id})`,
      `${pt ? 'Horário de referência' : 'Timetable reference'}: ${v.dir.reference_date} · Europe/Lisbon`, `${pt ? 'Paragens / distância aproximada' : 'Stops / approximate distance'}: ${v.stops.length} / ${(v.metres / 1000).toFixed(2)} km`,
      `${pt ? 'Viagens com referência em todas as paragens selecionadas' : 'Trips with references at every selected stop'}: ${v.through.length} / ${v.dir.trips.length}`,
      `${pt ? 'Viagem selecionada' : 'Selected trip'}: ${v.trip?.trip_id ?? '—'}`, `${pt ? 'Tempo previsto entre extremos' : 'Scheduled endpoint duration'}: ${finite(v.seconds) ? (v.seconds / 60).toFixed(1) + ' min' : '—'}`, '',
      `3D / SUMO: ${v.coverage} ${pt ? 'sobreposição' : 'overlap'}; ${native.from} → ${native.to}, ${pt ? 'sentido' : 'direction'} ${native.direction||v.direction}, ${data.native.window}. ${pt ? 'Tráfego sintético; não é atraso medido.' : 'Synthetic traffic; not measured delay.'}`,
      `Geometry: ${v.dir.geometry_note[lang] || v.dir.geometry_note.en}`, '', `| ${pt ? 'Paragem' : 'Stop'} | ${pt ? 'Hora publicada' : 'Published time'} | ${pt ? 'Tipo' : 'Type'} |`, '|---|---|---|',
      ...v.stops.map(s => `| ${s.stop_id} ${s.stop_name} | ${clock(v.trip?.stops[s.stop_id])} | ${s.designated_timing_point ? (pt ? 'Ponto de horário' : 'Timing point') : (pt ? 'Referência intermédia' : 'Intermediate reference')} |`), '',
      pt ? 'As referências em falta permanecem em falta. Um tempo previsto não é um tempo de viagem observado ou simulado.' : 'Missing published references remain missing. A scheduled duration is not an observed or simulated travel time.', '', `Source: ${data.source_url||"https://stcp.pt/pt/linhas/"+data.route}`, `Raw bundle: ${v.dir.bundle}/metadata.json`, ''].join('\n');
  }
  return {select, view, settings, summaryText};
}

const words = {
  en: {title:'One line. Choose your direction.', intro:'See the complete line, then choose the direction and section you want to understand.', direction:'Direction', from:'From stop', to:'To stop', whole:'Entire line', focus:'Zoom to section', overview:'Whole-line overview', section:'YOUR FOCUS', stops:'stops', distance:'approx. route distance', through:'trips with references at every selected stop', day:'weekday timetable', trip:'Scheduled trip', journey:'Scheduled section time', notServed:'Not served on this trip', unresolved:'Reference unavailable', timing:'Timing point', intermediate:'Intermediate reference', scheduled:'Published time', stop:'Stop', detail:'Inspect timetable, coverage and sources', source:'Official route and timetable', tableNote:'Times are scheduled references in Lisbon time. Only designated timing points are exact schedule checkpoints; none of these times measures actual delay.', coverage:'WHAT CAN WE TEST HERE?', full:'This section lies inside the prepared traffic model.', partial:'Only part of this selection has a prepared traffic model.', none:'This section has official route and timetable data; traffic simulation and 3D are not prepared here yet.', replay:'Watch this section in the simulation', model:'A separate operational model is available for this direction, using its declared assumptions.', noModel:'No separate operational model is registered for this selection. Native traffic coverage is declared independently.', simulation:'Native traffic replay', fullRoute:'Whole direction', chosen:'Selected section', startHere:'Start here', endHere:'End here', pick:'Click a stop to set the section start or end, or use the selectors.', tripCount:'daily trips', reference:'Timetable reference', narrative:'The goal: buses that keep their schedule, with access that works for residents, workers and shoppers.', share:'Share this section', export:'Export section JSON', mapOffline:'Background map tiles need internet; the official route and stop selection remain available.', focusNote:'Direction changes preserve each direction’s section and selected trip.', towards:'Towards', scheduledOnly:'Scheduled reference · not measured travel time', shape:'Route geometry', generated:'Frozen sources', sourceNote:'Route shapes and timetables have their own retrieval dates. Showing the whole line does not imply whole-line traffic simulation.'},
  pt: {title:'Uma linha. Escolha o sentido.', intro:'Veja a linha completa, depois escolha o sentido e a secção que quer compreender.', direction:'Sentido', from:'Da paragem', to:'À paragem', whole:'Linha inteira', focus:'Aproximar à secção', overview:'Vista geral da linha', section:'A SUA SECÇÃO', stops:'paragens', distance:'distância aproximada no percurso', through:'viagens com referência em todas as paragens selecionadas', day:'horário de dia útil', trip:'Viagem prevista', journey:'Tempo previsto na secção', notServed:'Não servida nesta viagem', unresolved:'Referência indisponível', timing:'Ponto de horário', intermediate:'Referência intermédia', scheduled:'Hora publicada', stop:'Paragem', detail:'Consultar horário, cobertura e fontes', source:'Percurso e horário oficiais', tableNote:'Horas previstas no fuso de Lisboa. Apenas os pontos de horário designados são referências exatas do horário; nenhum destes valores mede atraso real.', coverage:'O QUE PODEMOS TESTAR AQUI?', full:'Esta secção está dentro do modelo de tráfego preparado.', partial:'Só uma parte desta seleção tem um modelo de tráfego preparado.', none:'Esta secção tem percurso e horário oficiais; ainda não tem simulação de tráfego nem 3D preparados.', replay:'Ver esta secção na simulação', model:'Está disponível um modelo operacional distinto neste sentido, com os pressupostos declarados.', noModel:'Não está registado um modelo operacional distinto para esta seleção. A cobertura de tráfego nativo é declarada em separado.', simulation:'Replay de tráfego nativo', fullRoute:'Percurso completo', chosen:'Secção selecionada', startHere:'Começar aqui', endHere:'Terminar aqui', pick:'Clique numa paragem para definir o início ou o fim da secção, ou use os seletores.', tripCount:'viagens por dia', reference:'Horário de referência', narrative:'O objetivo: autocarros a cumprir o horário, com acessos que funcionem para moradores, trabalhadores e clientes do comércio.', share:'Partilhar esta secção', export:'Exportar secção JSON', mapOffline:'O mapa de fundo precisa de internet; o percurso oficial e a seleção de paragens continuam disponíveis.', focusNote:'Ao mudar de sentido, a secção e a viagem selecionadas de cada sentido são preservadas.', towards:'Sentido', scheduledOnly:'Referência do horário · não é tempo medido', shape:'Geometria do percurso', generated:'Fontes guardadas', sourceNote:'Os percursos e horários têm datas de recolha próprias. Mostrar a linha completa não significa simular o tráfego em toda a linha.'}
};

export async function mountLineExplorer({host, getLang, initial, onChange, onReplay, onShare, reference, existingModel, replayStatus}) {
  let data = reference;
  if (!data) { const response = await fetch('./701-line-explorer.json'); if (!response.ok) throw Error('Full-line reference unavailable'); data = await response.json(); }
  const model = existingModel || createLineExplorer(data, initial);
  const L = globalThis.L; let map, layers, tileFailed = false;
  host.innerHTML = `<div class="explorer-heading"><div><div class="eyebrow">${escape(data.route)} / ${data.reference_date}</div><h2 data-word="title"></h2><p data-word="intro"></p></div><label><span data-word="direction"></span><select id="lineDirection"></select></label></div>
    <div class="explorer-grid"><div class="explorer-map-card"><div class="explorer-map-shell"><div id="wholeLineMap" aria-label="Whole-line map" role="region"></div><div class="line-overview"><span data-word="overview"></span><svg viewBox="0 0 160 150" role="img" aria-label="Whole line and selected section" id="lineOverview"></svg></div></div><div class="line-map-legend"><span><i class="route-color"></i><span data-word="fullRoute"></span></span><span><i class="focus-color"></i><span data-word="chosen"></span></span><span><i class="native-color"></i><span data-word="simulation"></span></span></div><p class="fine" data-word="pick"></p><p class="fine" id="tileStatus"></p></div>
    <div class="card explorer-focus"><div class="eyebrow" data-word="section"></div><h3 id="focusName"></h3><div class="focus-fields"><label><span data-word="from"></span><select id="focusFrom"></select></label><label><span data-word="to"></span><select id="focusTo"></select></label></div><div class="actions section-shortcuts"><button id="wholeLine" data-word="whole"></button><button id="metroFocus">Ermesinde ↔ Areosa</button><button id="portoFocus">Areosa ↔ Bolhão</button><button id="zoomFocus" data-word="focus"></button></div><p class="fine" data-word="focusNote"></p>
    <div class="focus-metrics" id="focusMetrics" aria-live="polite"></div><label class="trip-field"><span data-word="trip"></span><select id="lineTrip"></select></label><div id="tripDuration"></div><div class="coverage-card"><div class="eyebrow" data-word="coverage"></div><p id="focusCoverage"></p><button id="focusReplay" class="primary" data-word="replay"></button></div><p class="fine" data-word="narrative"></p><div class="actions"><button id="shareFocus" data-word="share"></button><button id="exportFocus" data-word="export"></button></div><p class="status" id="focusShareStatus" aria-live="polite"></p></div></div>
    <details id="lineEvidence"><summary data-word="detail"></summary><div class="explorer-evidence"><div><p data-word="tableNote"></p><div class="table-wrap"><table id="focusTimetable"></table></div></div><aside><h3 data-word="source"></h3><p id="lineSourceDates"></p><p id="lineGeometryDates"></p><p id="lineModelCoverage"></p><p class="fine" data-word="sourceNote"></p><div id="lineSources"></div></aside></div></details>`;
  const $ = id => host.querySelector('#' + id), text = key => (words[getLang()] || words.en)[key];
  const latlng = points => points.map(([lon, lat]) => [lat, lon]);
  if (L) {
    map = L.map($('wholeLineMap'), {scrollWheelZoom: false, minZoom: 10, maxZoom: 19});
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).on('tileerror', () => { tileFailed = true; $('tileStatus').textContent = text('mapOffline'); }).addTo(map);
    layers = L.layerGroup().addTo(map); L.control.scale({imperial: false}).addTo(map);
  }
  function notify(change = {}) { onChange?.(model.settings(), model.view(), change); }
  function update(change, fit = true) { model.select(change); render(fit); notify(change); }
  function render(fit = true) {
    const v = model.view(), config = model.settings(), t = text, pt = getLang() === 'pt';
    host.querySelectorAll('[data-word]').forEach(el => { el.textContent = t(el.dataset.word); });
    $('lineDirection').replaceChildren(...Object.entries(data.directions).sort(([a], [b]) => b.localeCompare(a)).map(([id, d]) => new Option(`${d.origin} → ${d.destination}`, id)));
    $('lineDirection').value = v.direction;
    const options = v.dir.stops.map((s, i) => [`${i + 1}. ${s.stop_name} · ${s.stop_id}`, s.stop_id]);
    $('focusFrom').replaceChildren(...options.slice(0, -1).map(x => new Option(...x)));
    $('focusTo').replaceChildren(...options.slice(1).map(x => new Option(...x)));
    $('focusFrom').value = v.stops[0].stop_id; $('focusTo').value = v.stops.at(-1).stop_id;
    $('focusName').textContent = `${v.stops[0].stop_name} → ${v.stops.at(-1).stop_name}`;
    $('focusMetrics').innerHTML = `<div><strong>${v.stops.length}</strong><span>${t('stops')}</span></div><div><strong>${(v.metres / 1000).toLocaleString(pt ? 'pt-PT' : 'en-GB', {maximumFractionDigits: 2})} km</strong><span>${t('distance')}</span></div><div><strong>${v.through.length} / ${v.dir.trips.length}</strong><span>${t('through')}</span></div>`;
    $('lineTrip').replaceChildren(...v.trips.map(trip => {
      const published = v.stops.map(s => trip.stops[s.stop_id]).filter(finite);
      return new Option(`${clock(published[0])} · ${trip.originstatus?.origin_stop_id || ''} → ${trip.terminalstatus?.terminal_stop_id || trip.headsign || v.dir.destination} · ${trip.trip_id}`, trip.trip_id);
    })); $('lineTrip').value = v.trip?.trip_id ?? '';
    $('tripDuration').innerHTML = `<strong class="section-duration">${finite(v.seconds) ? (v.seconds / 60).toLocaleString(pt ? 'pt-PT' : 'en-GB', {maximumFractionDigits: 1}) + ' min' : '—'}</strong><span class="fine">${t('journey')}<br>${t('scheduledOnly')}</span>`;
    $('focusCoverage').textContent = t(v.coverage); $('focusReplay').disabled = v.coverage === 'none' || replayStatus?.()?.eligible === false;
    $('focusTimetable').innerHTML = `<thead><tr><th>${t('stop')}</th><th>${t('scheduled')}</th><th>${pt ? 'Referência' : 'Reference'}</th></tr></thead><tbody>${v.stops.map((s, i) => {
      const value = v.trip?.stops[s.stop_id], status = v.trip?.stop_time_status?.[s.stop_id];
      const knownUnserved = status === 'unserved_working' || v.trip?.originstatus?.unserved_stop_ids?.includes(s.stop_id);
      const missing = knownUnserved ? t('notServed') : t('unresolved');
      return `<tr><td>${v.start + i + 1}. ${escape(s.stop_name)}<br><span class="fine">${escape(s.stop_id)}</span></td><td>${finite(value) ? clock(value) : missing}</td><td>${t(s.designated_timing_point ? 'timing' : 'intermediate')}</td></tr>`;
    }).join('')}</tbody>`;
    $('lineSourceDates').textContent = `${t('reference')}: ${v.dir.reference_date} · Europe/Lisbon · ${v.dir.trips.length} ${t('tripCount')}.`;
    $('lineGeometryDates').textContent = `${t('shape')}: ${v.dir.geometry_note[getLang()] || v.dir.geometry_note.en}`;
    $('lineModelCoverage').textContent = data.native.full_line ? (pt?'A simulação nativa cobre a linha completa nos dois sentidos. O modelo separado de passageiros mantém pressupostos próprios e está disponível no sentido Bolhão.':'Native traffic simulation covers the complete line in both directions. The separate passenger model retains its own assumptions and is available inbound.') : t(v.operational ? 'model' : 'noModel');
    const shortcuts=v.dir.shortcuts||{};$('metroFocus').hidden=!shortcuts.ermesinde||!shortcuts.areosa;$('portoFocus').hidden=!shortcuts.areosa;
    $('lineSources').innerHTML = `<p><a href="${escape(data.source_url||"https://stcp.pt/pt/linhas/"+data.route)}" target="_blank" rel="noreferrer">${escape(data.operator||"STCP")} / ${escape(data.route)}</a></p><p><a href="${escape(v.dir.bundle)}/metadata.json">${t('generated')} · metadata.json</a></p><p><a href="${escape(data.data_file||"701-line-explorer.json")}" download>JSON · ${t('fullRoute')}</a></p>`;
    $('lineEvidence').open = config.detail;
    $('tileStatus').textContent = tileFailed || !L ? t('mapOffline') : '';
    const all = v.dir.shape, lon = all.map(p => p[0]), lat = all.map(p => p[1]);
    const minX = Math.min(...lon), maxX = Math.max(...lon), minY = Math.min(...lat), maxY = Math.max(...lat), cos = Math.cos(minY * Math.PI / 180);
    const scale = Math.min(132 / ((maxX - minX) * cos), 118 / (maxY - minY));
    const path = points => points.map((p, i) => `${i ? 'L' : 'M'}${(14 + (p[0] - minX) * cos * scale).toFixed(1)},${(132 - (p[1] - minY) * scale).toFixed(1)}`).join(' ');
    $('lineOverview').innerHTML = `<path d="${path(all)}" fill="none" stroke="#adbdb4" stroke-width="4"/><path d="${path(v.focusShape)}" fill="none" stroke="#177455" stroke-width="4"/><path d="${path(v.nativeShape)}" fill="none" stroke="#3e7fa2" stroke-width="2" stroke-dasharray="4 3"/>`;
    if (map) {
      layers.clearLayers();
      L.polyline(latlng(all), {color: '#899e94', weight: 7, opacity: .65, interactive: false}).addTo(layers);
      L.polyline(latlng(v.focusShape), {color: '#177455', weight: 6, interactive: false}).addTo(layers);
      if (v.nativeShape.length) L.polyline(latlng(v.nativeShape), {color: '#3e7fa2', weight: 3, dashArray: '7 6', interactive: false}).addTo(layers);
      v.dir.stops.forEach((stop, i) => {
        const selected = i >= v.start && i <= v.end, endpoint = i === v.start || i === v.end;
        const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {radius: endpoint ? 7 : selected ? 4 : 3, color: selected ? '#173b31' : '#81988a', weight: endpoint ? 3 : 1, fillColor: selected ? '#fff' : '#b5c7ba', fillOpacity: 1}).addTo(layers);
        marker.bindTooltip(`${i + 1}. ${escape(stop.stop_name)} · ${escape(stop.stop_id)}`);
        marker.on('click', () => {
          const popup = document.createElement('div'), name = document.createElement('strong'), actions = document.createElement('div'); name.textContent = `${stop.stop_name} · ${stop.stop_id}`; actions.className = 'actions'; popup.append(name, actions);
          for (const [key, label, disabled] of [['from', 'startHere', i === v.dir.stops.length - 1], ['to', 'endHere', i === 0]]) {
            const button = document.createElement('button'); button.textContent = t(label); button.disabled = disabled; button.onclick = () => { map.closePopup(); update({[key]: stop.stop_id}); }; actions.append(button);
          }
          L.popup().setLatLng(marker.getLatLng()).setContent(popup).openOn(map);
        });
        if (endpoint) marker.bindTooltip(escape(stop.stop_name), {permanent: true, direction: i === v.start ? 'top' : 'bottom', className: 'focus-stop-label'});
      });
      map.invalidateSize(); if (fit) map.fitBounds(latlng(config.zoom ? v.focusShape : all), {padding: [32, 32], maxZoom: 16, animate: false});
    } else $('wholeLineMap').innerHTML = `<svg viewBox="0 0 160 150" style="width:100%;height:100%">${$('lineOverview').innerHTML}</svg>`;
  }
  $('lineDirection').onchange = e => update({direction: e.target.value});
  $('focusFrom').onchange = e => update({from: e.target.value}); $('focusTo').onchange = e => update({to: e.target.value});
  $('wholeLine').onclick = () => update({whole: true, zoom: false}); $('zoomFocus').onclick = () => update({zoom: true});
  $('lineTrip').onchange = e => update({trip: e.target.value}, false);
  $('metroFocus').onclick = () => { const d = model.view().dir; update(model.settings().direction === '1' ? {from: d.shortcuts.ermesinde, to: d.shortcuts.areosa} : {from: d.shortcuts.areosa, to: d.shortcuts.ermesinde}); };
  $('portoFocus').onclick = () => { const d = model.view().dir; update(model.settings().direction === '1' ? {from: d.shortcuts.areosa, to: d.stops.at(-1).stop_id} : {from: d.stops[0].stop_id, to: d.shortcuts.areosa}); };
  $('lineEvidence').ontoggle = e => { if (model.settings().detail !== e.target.open) { model.select({detail: e.target.open}); notify({detail:e.target.open}); } };
  $('focusReplay').onclick = () => {
    const v = model.view(); if (v.coverage === 'none') return;
    onReplay?.(model.view());
  };
  $('shareFocus').onclick = async () => { $('focusShareStatus').textContent = await onShare?.() || ''; };
  $('exportFocus').onclick = () => {
    const blob = new Blob([JSON.stringify({route: data.route, explorer: model.settings(), reference_date: data.reference_date, coverage: model.view().coverage, kind: 'review selection; not a simulated lane policy'}, null, 2)], {type: 'application/json'});
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${data.route}-section-${model.settings().direction}.json`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  };
  render(); notify({initial:true});
  return {...model,select(change){update(change,!Object.keys(change).every(key=>['trip','detail'].includes(key)));return model.view()},renderLanguage: () => render(false),refreshLayout:()=>render(true), map};
}
