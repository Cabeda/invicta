// Presentation shell around the pure, conditional person-trip accounting model.
window.createTransitionPanel = function ({ facts, language, download, corridor }) {
  const host = document.getElementById('people');
  let p = { ...TravelTransition.defaults, times: { ...TravelTransition.defaults.times }, population: facts.population.annual_population.metropolitan_population };
  let renderedLanguage = '', last;
  const C = {
    en: {
      eyebrow: 'PEOPLE, ACCESS AND THE TRANSITION', title: 'Who gains, who loses, and what changes over time?',
      loop: 'Hypothesis to test: better alternatives → people can switch → fewer car journeys → congestion can fall. Capacity and practical access determine whether this happens.', modeChange: 'Person-trip request shares: before → conditional scenario', intro: 'Compare the immediate change with a possible shift towards buses, bikes and walking. Keep every requested person-trip visible, including people who continue driving.',
      warning: 'Conditional what-if calculator. Population and reference travel shares are sourced; journey times, adoption, access penalties and capacity are assumptions. These controls update accounting, not the SUMO replay, and do not predict that people will switch.',
      population: 'Metropolitan population', populationInput: 'Scenario population', mobileShare: 'Share of all residents travelling that day (%) — assumed', tripsPerMobile: 'Trips per travelling person — IMob 2017 reference',
      demandBasis: 'Demand basis', populationBasis: 'Population × travelling share × trip rate', historicBasis: 'Historic IMob 2017 benchmark: about 3.4 million trips/day',
      affectedShare: 'Share of regional trips affected (%) — assumed', externalTrips: 'Additional trips by visitors living outside AMP/day — unknown, input assumption',
      preset: 'Reference travel mix', shift: 'Car person-trips switching mode (%) — assumed', capacityGrowth: 'Spare + added bus passenger-trip capacity (% of baseline demand) — assumed',
      busGain: 'Bus door-to-door saving from combined measures (min) — assumed', visitorDetour: 'Extra time for non-resident drivers (min) — assumed',
      assumptions: 'Change the assumptions', allocation: 'Where do switching car trips go?', toBus: 'To bus (%)', toBicycle: 'To bicycle (%)', toWalk: 'Remainder goes to walking',
      removalEffect: 'Shifts that actually remove a car journey (%)', carOccupancy: 'People per removed car — assumed',
      access: 'Residents, workers, shoppers and leisure visitors', nonresidentShare: 'Non-resident share among car trips that remain (%) — assumed', residentDetour: 'Extra time for resident drivers (min) — assumed',
      workShare: 'Work/study share of remaining non-resident car trips (%) — assumed', shoppingShare: 'Shopping share (%) — assumed', leisureShare: 'Leisure / going for a walk share (%) — assumed',
      times: 'Baseline door-to-door minutes — all assumed', feedback: 'Congestion and boarding response — assumed', congestionMinutes: 'Car minutes attributed to congestion', exponent: 'Response exponent (0 means no congestion relief)', boardingPenalty: 'Extra bus minutes per 100% passenger growth',
      inputNote: 'The population-based total uses a combined eligible-and-travelling fraction of the whole population. The 2.72 rate applies to mobile people aged 6–84 in 2017, not every resident. Outside-AMP visitor trips are not in that survey; zero here means not added, not that none exist.',
      before: 'Before the change', immediate: 'Immediately: nobody switches yet', future: 'If the selected share switches', minuteUnit: 'min per affected person-trip',
      noMean: 'Full-population mean unavailable', servedOnly: 'Served trips only', unserved: 'Unserved bus person-trips/day',
      threshold: 'First feasible break-even in this model', noThreshold: 'No feasible break-even up to 60% switching with these assumptions.',
      thresholdText: 'of car person-trips must switch before the average falls below the baseline. This is a scenario threshold, not a prediction or a calendar date.',
      driverNote: 'Non-resident drivers who keep driving', metroDelta: 'Mean change across all represented regional trips', hoursDelta: 'Total person-hours/day change',
      scopeNote: 'Unaffected trips keep their baseline time. These are weighted representative requests, not individual residents or a metropolitan road-network simulation. Population scales requests and hours; it does not by itself determine network congestion.',
      trips: 'Affected person-trips/day', regionalTrips: 'Represented regional person-trips/day', vehicles: 'Estimated car journeys removed/day', capacityNeeded: 'Required bus passenger-trip capacity above baseline demand',
      chart: 'Average time as more car trips change mode', chartHelp: 'Grey: baseline. Green: all requests served. Orange: served-trip mean with unmet bus demand, excluded from the break-even test. The horizontal axis is assumed adoption, not time.',
      table: 'Keep the people behind the average visible', who: 'Who', count: 'Person-trip requests', beforeColumn: 'Before (min)', afterColumn: 'After, if served (min)', delta: 'Change/person (min)', missing: 'Unserved',
      cohortNote: 'Resident means the chosen study-area resident, not automatically a Porto census resident. Residency and purpose allocations are explicit assumptions. The mode profile does not identify real individuals. PMUS purpose marginals exclude return-home trips and are not a joint purpose × mode table. Work, shopping and leisure rows here refer to non-residents who keep driving.',
      cohortWarning: 'An improved overall average can coexist with longer journeys for some people. More bus demand needs usable capacity, reliable service and accessible stops; a mode-shift percentage does not supply those things. The daily capacity ceiling does not validate capacity on each route or at peak times.',
      sourceTitle: 'What is observed, and what is assumed?', sourceModes: 'Printed reference percentages', normalization: 'Rounded source values are preserved here and normalized only for calculation.',
      sourceNote: 'INE population: 2025 estimate, updated June 2026. IMob travel reference: 2017, residents aged 6–84. PMUS profiles: survey reference, with scope/sample limitations. These are person-trip shares, not vehicle-fleet percentages.',
      conflict: 'PMUS 2035 targets differ between the narrative and Table 49. They concern commuting, not all trips, so neither is used as an observed baseline or a promised outcome.',
      report: 'Download explanation (.md)', json: 'Export scenario + sources (.json)', csv: 'Export people affected (.csv)', reset: 'Reset illustrative assumptions',
      native: 'What the corridor simulation currently says', nativeNote: 'Imported OSM baseline retained; one-lane-per-mapped-direction premise applied only to the proposal. Imported layouts, demand and signals still require validation. The table covers simulated vehicle groups; residence/purpose of ordinary traffic is unknown.',
      nativeGroup: 'Simulated group', nativeTime: 'Completed-trip driving min: baseline → proposal', nativeUnserved: 'Unserved requests: baseline → proposal', nativeCase: 'Follows the demand case selected in the replay above.',
      labels: { car: 'Car', bus: 'Bus', metro: 'Metro', train: 'Train', bicycle: 'Bicycle', walk: 'Walking', motorcycle: 'Motorcycle / moped', other: 'Other', residentDrivers: 'Residents who keep driving', workDrivers: 'Non-residents: work / study, keep driving', shoppingDrivers: 'Non-residents: shopping, keep driving', leisureDrivers: 'Non-residents: leisure / walks, keep driving', otherDrivers: 'Non-residents: other, keep driving', existingBus: 'Existing bus users', switchBus: 'People switching car → bus', switchBicycle: 'People switching car → bicycle', switchWalk: 'People switching car → walking', through: 'Through cars — purpose/residence unknown', background: 'Other cars — purpose/residence unknown', crossing: 'Junction-crossing cars', resident: 'Synthetic resident-permit cars', taxi: 'Taxis' },
      invalid: 'Destination shares and purpose shares must each total no more than 100%.'
    },
    pt: {
      eyebrow: 'PESSOAS, ACESSO E TRANSIÇÃO', title: 'Quem ganha, quem perde e o que muda com o tempo?',
      loop: 'Hipótese a testar: melhores alternativas → as pessoas podem mudar → menos viagens de carro → o congestionamento pode diminuir. Capacidade e acesso prático determinam se isto acontece.', modeChange: 'Repartição dos pedidos de viagem de pessoas: antes → cenário condicional', intro: 'Compare a alteração imediata com uma possível mudança para autocarro, bicicleta e deslocações a pé. Mantenha visíveis todos os pedidos de viagem, incluindo quem continua de automóvel.',
      warning: 'Calculadora condicional de cenários. População e repartições de referência têm fontes; tempos, adesão, penalizações de acesso e capacidade são hipóteses. Estes controlos atualizam os cálculos, não o replay SUMO, e não preveem que as pessoas mudem de modo.',
      population: 'População metropolitana', populationInput: 'População no cenário', mobileShare: 'Percentagem de todos os residentes que viaja nesse dia (%) — hipótese', tripsPerMobile: 'Viagens por pessoa móvel — referência IMob 2017',
      demandBasis: 'Base da procura', populationBasis: 'População × percentagem móvel × viagens por pessoa', historicBasis: 'Referência histórica IMob 2017: cerca de 3,4 milhões de viagens/dia',
      affectedShare: 'Percentagem das viagens regionais afetada (%) — hipótese', externalTrips: 'Viagens adicionais de visitantes de fora da AMP/dia — desconhecido, hipótese',
      preset: 'Repartição modal de referência', shift: 'Viagens de pessoas em automóvel que mudam de modo (%) — hipótese', capacityGrowth: 'Capacidade de viagens em autocarro disponível + adicional (% da procura inicial) — hipótese',
      busGain: 'Poupança porta a porta no autocarro com medidas combinadas (min) — hipótese', visitorDetour: 'Tempo adicional para condutores não residentes (min) — hipótese',
      assumptions: 'Alterar as hipóteses', allocation: 'Para onde mudam as viagens de automóvel?', toBus: 'Para autocarro (%)', toBicycle: 'Para bicicleta (%)', toWalk: 'A restante percentagem passa a andar a pé',
      removalEffect: 'Mudanças que retiram realmente uma viagem de automóvel (%)', carOccupancy: 'Pessoas por automóvel retirado — hipótese',
      access: 'Moradores, trabalhadores, clientes e visitantes', nonresidentShare: 'Não residentes nas viagens que continuam de carro (%) — hipótese', residentDetour: 'Tempo adicional para condutores residentes (min) — hipótese',
      workShare: 'Trabalho/estudo nas viagens de não residentes que continuam de carro (%) — hipótese', shoppingShare: 'Compras (%) — hipótese', leisureShare: 'Lazer / passeios (%) — hipótese',
      times: 'Minutos porta a porta na referência — todas hipóteses', feedback: 'Resposta do congestionamento e embarque — hipóteses', congestionMinutes: 'Minutos de automóvel atribuídos a congestionamento', exponent: 'Expoente de resposta (0 significa ausência de alívio)', boardingPenalty: 'Minutos adicionais no autocarro por 100% de aumento de passageiros',
      inputNote: 'A procura baseada na população usa uma fração conjunta de pessoas elegíveis e móveis sobre toda a população. A taxa 2,72 refere-se a pessoas móveis de 6–84 anos em 2017, não a cada residente. Visitantes de fora da AMP não estão nesse inquérito; zero aqui significa não acrescentados, não que não existam.',
      before: 'Antes da alteração', immediate: 'Imediatamente: ainda ninguém muda', future: 'Se a percentagem escolhida mudar', minuteUnit: 'min por viagem de pessoa afetada',
      noMean: 'Média de toda a procura indisponível', servedOnly: 'Apenas viagens servidas', unserved: 'Viagens de autocarro não servidas/dia',
      threshold: 'Primeiro ponto de equilíbrio viável neste modelo', noThreshold: 'Sem ponto de equilíbrio viável até 60% de mudança com estas hipóteses.',
      thresholdText: 'das viagens de pessoas em automóvel têm de mudar para a média ficar abaixo da referência. É um limiar do cenário, não uma previsão nem uma data.',
      driverNote: 'Não residentes que continuam de automóvel', metroDelta: 'Variação média em todas as viagens regionais representadas', hoursDelta: 'Variação de horas-pessoa/dia',
      scopeNote: 'As viagens não afetadas mantêm o tempo de referência. São pedidos representativos ponderados, não residentes individuais nem uma simulação da rede rodoviária metropolitana. A população escala pedidos e horas; por si só não determina congestionamento na rede.',
      trips: 'Viagens de pessoas afetadas/dia', regionalTrips: 'Viagens regionais de pessoas representadas/dia', vehicles: 'Viagens de automóvel retiradas/dia — estimativa', capacityNeeded: 'Capacidade de viagens em autocarro necessária acima da procura inicial',
      chart: 'Tempo médio à medida que mais viagens mudam de modo', chartHelp: 'Cinzento: referência. Verde: toda a procura servida. Laranja: média apenas das viagens servidas, com procura de autocarro por servir, excluída do equilíbrio. O eixo horizontal é adesão assumida, não tempo.',
      table: 'Manter visíveis as pessoas por trás da média', who: 'Quem', count: 'Pedidos de viagem de pessoas', beforeColumn: 'Antes (min)', afterColumn: 'Depois, se servido (min)', delta: 'Variação/pessoa (min)', missing: 'Não servidas',
      cohortNote: 'Morador refere-se à área de estudo escolhida, não automaticamente ao residente censitário do Porto. Residência e finalidade são repartições assumidas. O perfil modal não identifica pessoas reais. As finalidades do PMUS excluem regressos a casa e não são uma tabela conjunta finalidade × modo. As linhas de trabalho, compras e lazer referem-se a não residentes que continuam de carro.',
      cohortWarning: 'A média global pode melhorar e algumas pessoas continuar com viagens mais longas. Mais passageiros exigem capacidade utilizável, serviço fiável e paragens acessíveis; uma percentagem de mudança não fornece essas condições. O teto diário não valida a capacidade por linha ou nas horas de ponta.',
      sourceTitle: 'O que é observado e o que é assumido?', sourceModes: 'Percentagens de referência publicadas', normalization: 'Os valores arredondados da fonte são preservados aqui e normalizados apenas no cálculo.',
      sourceNote: 'População INE: estimativa de 2025, atualizada em junho de 2026. IMob: 2017, residentes com 6–84 anos. Perfis PMUS: referência do inquérito, com limitações de amostra e âmbito. São quotas de viagens de pessoas, não percentagens da frota.',
      conflict: 'As metas PMUS de 2035 diferem entre o texto e o Quadro 49. Referem-se a deslocações pendulares, não a todas as viagens; nenhuma é usada como referência observada ou resultado garantido.',
      report: 'Descarregar explicação (.md)', json: 'Exportar cenário + fontes (.json)', csv: 'Exportar pessoas afetadas (.csv)', reset: 'Repor hipóteses ilustrativas',
      native: 'O que diz atualmente a simulação do corredor', nativeNote: 'Referência OSM importada preservada; hipótese de uma via por sentido mapeado apenas na proposta. Geometria, procura e sinais importados precisam de validação. A tabela representa grupos de veículos; residência/finalidade do tráfego comum é desconhecida.',
      nativeGroup: 'Grupo simulado', nativeTime: 'Minutos de condução, viagens concluídas: referência → proposta', nativeUnserved: 'Pedidos não servidos: referência → proposta', nativeCase: 'Segue a hipótese de procura escolhida no replay acima.',
      labels: { car: 'Automóvel', bus: 'Autocarro', metro: 'Metro', train: 'Comboio', bicycle: 'Bicicleta', walk: 'A pé', motorcycle: 'Motociclo / ciclomotor', other: 'Outros', residentDrivers: 'Moradores que continuam de automóvel', workDrivers: 'Não residentes: trabalho / estudo, continuam de carro', shoppingDrivers: 'Não residentes: compras, continuam de carro', leisureDrivers: 'Não residentes: lazer / passeios, continuam de carro', otherDrivers: 'Não residentes: outros motivos, continuam de carro', existingBus: 'Utilizadores atuais de autocarro', switchBus: 'Pessoas que mudam de carro → autocarro', switchBicycle: 'Pessoas que mudam de carro → bicicleta', switchWalk: 'Pessoas que mudam de carro → a pé', through: 'Automóveis de atravessamento — finalidade/residência desconhecida', background: 'Outros automóveis — finalidade/residência desconhecida', crossing: 'Automóveis em cruzamentos', resident: 'Automóveis com autorização sintética de morador', taxi: 'Táxis' },
      invalid: 'As repartições por destino modal e por finalidade não podem exceder 100% cada.'
    }
  };
  const esc = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmt = (n, d = 1) => Number.isFinite(n) ? new Intl.NumberFormat(language() === 'pt' ? 'pt-PT' : 'en-GB', { maximumFractionDigits: d, minimumFractionDigits: d }).format(n) : '—';
  const signed = n => (n > 0 ? '+' : '') + fmt(n);
  const input = (key, min, max, step = 1, type = 'number') => `<label>${esc(C[language()][key])}<input data-transition-input="${key}" type="${type}" min="${min}" max="${max}" step="${step}" value="${p[key]}">${type === 'range' ? `<output data-transition-output="${key}">${p[key]}</output>` : ''}</label>`;
  function build() {
    const t = C[language()], pop = facts.population.annual_population;
    host.innerHTML = `<div class="section-head"><div><div class="eyebrow">${t.eyebrow}</div><h2>${t.title}</h2><p class="muted">${t.intro}</p></div></div>
      <p class="transition-warning">${t.warning}</p><p class="transition-loop">${t.loop}</p><div class="transition-source"><strong>${t.population}: ${fmt(pop.metropolitan_population, 0)}</strong> · INE ${pop.reference_year} · Porto ${fmt(pop.porto_municipality_population, 0)}<br><span class="fine">${t.sourceNote}</span></div>
      <div class="transition-inputs"><label>${t.preset}<select id="transitionPreset">${Object.entries(facts.presets).map(([key, v]) => `<option value="${key}" ${p.preset === key ? 'selected' : ''}>${esc(v.label[language()])}</option>`).join('')}</select></label>
      <label>${t.demandBasis}<select id="transitionBasis"><option value="population" ${p.demandBasis === 'population' ? 'selected' : ''}>${t.populationBasis}</option><option value="historic" ${p.demandBasis === 'historic' ? 'selected' : ''}>${t.historicBasis}</option></select></label>
      ${input('affectedShare', .01, 100, .01)}${input('shift', 0, 60, 1, 'range')}${input('busGain', 0, 25, .5, 'range')}${input('visitorDetour', 0, 30, .5, 'range')}${input('capacityGrowth', 0, 500, 5, 'range')}</div>
      <details class="transition-details"><summary>${t.assumptions}</summary><div class="transition-inputs">${input('population', 1, 5000000)}${input('mobileShare', 1, 100)}${input('tripsPerMobile', .1, 10, .01)}${input('externalTrips', 0, 1000000)}<p class="fine transition-span">${t.inputNote}</p></div>
      <h3>${t.allocation}</h3><div class="transition-inputs">${input('toBus', 0, 100)}${input('toBicycle', 0, 100)}${input('removalEffect', 0, 100)}${input('carOccupancy', 1, 5, .1)}<p class="fine">${t.toWalk}</p></div>
      <h3>${t.access}</h3><div class="transition-inputs">${input('nonresidentShare', 0, 100)}${input('residentDetour', 0, 30, .5)}${input('workShare', 0, 100)}${input('shoppingShare', 0, 100)}${input('leisureShare', 0, 100)}</div>
      <h3>${t.times}</h3><div class="transition-inputs">${TravelTransition.modes.map(mode => `<label>${t.labels[mode]}<input data-transition-time="${mode}" type="number" min="1" max="240" step="1" value="${p.times[mode]}"></label>`).join('')}</div>
      <h3>${t.feedback}</h3><div class="transition-inputs">${input('congestionMinutes', 0, 90, .5)}${input('exponent', 0, 4, .1)}${input('boardingPenalty', 0, 20, .5)}</div></details>
      <div id="transitionResults"></div><div class="actions"><button id="transitionReport">${t.report}</button><button id="transitionJSON">${t.json}</button><button id="transitionCSV">${t.csv}</button><button id="transitionReset">${t.reset}</button></div>`;
    const update = () => {
      for (const e of host.querySelectorAll('[data-transition-input]')) p[e.dataset.transitionInput] = Math.max(Number(e.min), Math.min(Number(e.max), Number(e.value) || Number(e.min)));
      for (const e of host.querySelectorAll('[data-transition-time]')) p.times[e.dataset.transitionTime] = Math.max(1, Math.min(240, Number(e.value) || 1));
      p.preset = document.getElementById('transitionPreset').value; p.demandBasis = document.getElementById('transitionBasis').value;
      results();
    };
    for (const e of host.querySelectorAll('input,select')) e.addEventListener('input', update);
    document.getElementById('transitionReset').onclick = () => { p = { ...TravelTransition.defaults, times: { ...TravelTransition.defaults.times }, population: pop.metropolitan_population }; renderedLanguage = ''; render(); };
    document.getElementById('transitionJSON').onclick = () => download('porto-population-scenario.json', new Blob([JSON.stringify({ schema: 1, conditional: true, parameters: p, sources: facts, results: last }, null, 2)], { type: 'application/json' }));
    document.getElementById('transitionCSV').onclick = () => {
      const rows = [['stage', 'cohort', 'person_trip_requests', 'served', 'unserved', 'before_minutes', 'after_if_served_minutes', 'delta_minutes']];
      for (const stage of ['immediate', 'future']) for (const r of last[stage].rows) rows.push([stage, r.key, r.count, r.served, r.unserved, r.before, r.after, r.delta]);
      download('porto-person-trip-impacts.csv', new Blob([rows.map(r => r.join(',')).join('\n')], { type: 'text/csv' }));
    };
    document.getElementById('transitionReport').onclick = () => download('porto-transition-explanation.md', new Blob([report()], { type: 'text/markdown' }));
  }
  function chart(model, t) {
    const width = 850, height = 245, pad = 43;
    const vals = model.curve.flatMap(r => [r.before, r.servedMean]);
    const lo = Math.floor(Math.min(...vals) - 1), hi = Math.ceil(Math.max(...vals) + 1);
    const x = s => pad + s / 60 * (width - pad * 2), y = n => height - pad - (n - lo) / (hi - lo || 1) * (height - pad * 2);
    let segments = '', previous;
    for (const r of model.curve) {
      if (previous) segments += `<line x1="${x(previous.shift)}" y1="${y(previous.servedMean)}" x2="${x(r.shift)}" y2="${y(r.servedMean)}" stroke="${r.mean === null || previous.mean === null ? '#b28139' : '#177455'}" stroke-width="3" ${r.mean === null ? 'stroke-dasharray="4 4"' : ''}/>`;
      previous = r;
    }
    const current = model.future;
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(t.chart)}"><line x1="${pad}" x2="${width - pad}" y1="${y(current.beforeMean)}" y2="${y(current.beforeMean)}" stroke="#8b9690" stroke-width="2" stroke-dasharray="6 4"/>${[lo, (lo + hi) / 2, hi].map(v => `<text x="4" y="${y(v) + 4}" font-size="12" fill="#607166">${fmt(v)}m</text>`).join('')}${segments}<circle cx="${x(p.shift)}" cy="${y(current.servedMean)}" r="6" fill="${current.allServed ? '#177455' : '#b28139'}"/>${[0, 10, 20, 30, 40, 50, 60].map(v => `<text x="${x(v)}" y="${height - 12}" text-anchor="middle" font-size="12" fill="#607166">${v}%</text>`).join('')}</svg>`;
  }
  function results() {
    const t = C[language()]; last = TravelTransition.compare(p, facts);
    for (const e of host.querySelectorAll('[data-transition-output]')) e.textContent = fmt(p[e.dataset.transitionOutput], Number.isInteger(p[e.dataset.transitionOutput]) ? 0 : 1);
    for(const id of ['transitionReport','transitionJSON','transitionCSV'])document.getElementById(id).disabled=!!last.error;if (last.error) { document.getElementById('transitionResults').textContent = t.invalid; return; }
    const a = last.immediate, b = last.future, driver = b.rows.find(r => r.key === 'workDrivers');
    const story=language()==='pt'?`Com estas hipóteses, a alteração imediata varia a média em ${signed(a.meanDelta)} min. Se ${fmt(p.shift,0)}% das viagens em automóvel mudarem, ${b.allServed?`a variação será ${signed(b.meanDelta)} min; quem não reside na área e continua de carro terá ${signed(driver.delta)} min.`:`ficam ${fmt(b.unserved,0)} pedidos de autocarro por servir; não há comparação da média de toda a procura.`}`:`Under these assumptions, the immediate mean changes by ${signed(a.meanDelta)} min. If ${fmt(p.shift,0)}% of car person-trips switch, ${b.allServed?`the mean changes by ${signed(b.meanDelta)} min; non-residents who keep driving have ${signed(driver.delta)} min.`:`${fmt(b.unserved,0)} bus requests remain unserved; the mean for all requests cannot be compared.`}`;
    const box = (name, value, note, warn = false) => `<div class="card metric ${warn ? 'warning' : ''}"><div class="fine">${name}</div><strong>${value}</strong><div class="comparison">${note}</div></div>`;
    const html = `<div class="transition-stages">${box(t.before, fmt(b.beforeMean), t.minuteUnit)}${box(t.immediate, fmt(a.mean), `${t.minuteUnit} · ${signed(a.meanDelta)}`, a.meanDelta > 0)}${box(t.future, b.allServed ? fmt(b.mean) : '—', b.allServed ? `${t.minuteUnit} · ${signed(b.meanDelta)}` : `${t.noMean}; ${t.servedOnly}: ${fmt(b.servedMean)} min`, !b.allServed)}</div>
      <details class="transition-details"><summary>${t.modeChange}</summary><div class="transition-table"><table><thead><tr><th>${t.who}</th><th>${t.before}</th><th>${t.future}</th></tr></thead><tbody>${TravelTransition.modes.map(k=>`<tr><td>${t.labels[k]}</td><td>${fmt(b.baseCounts[k]/b.requests*100)}%</td><td>${fmt(b.counts[k]/b.requests*100)}%</td></tr>`).join('')}</tbody></table></div></details><div class="transition-summary"><p class="transition-story">${story}</p><p><b>${t.trips}:</b> ${fmt(b.requests, 0)} · <b>${t.regionalTrips}:</b> ${fmt(b.totalDaily, 0)}</p><p><b>${t.threshold}:</b> ${last.breakEven === null ? t.noThreshold : `${last.breakEven}% ${t.thresholdText}`}</p>
      <p><b>${t.driverNote}:</b> <span class="${driver.delta > 0 ? 'transition-loss' : 'transition-gain'}">${signed(driver.delta)} min</span> · <b>${t.unserved}:</b> ${fmt(b.unserved, 0)}</p>
      <p><b>${t.capacityNeeded}:</b> +${fmt(b.requiredCapacityGrowth)}% · <b>${t.vehicles}:</b> ${fmt(b.estimatedCarsRemoved, 0)}</p><p><b>${t.metroDelta}:</b> ${b.metroMeanDelta === null ? '—' : `${signed(b.metroMeanDelta)} min`} · <b>${t.hoursDelta}:</b> ${b.personHoursDelta === null ? '—' : signed(b.personHoursDelta)}</p><p class="fine">${t.scopeNote}</p></div>
      <div class="card"><h3>${t.chart}</h3>${chart(last, t)}<p class="fine">${t.chartHelp}</p></div>
      <div class="card transition-cohorts"><h3>${t.table}</h3><div class="transition-table"><table><thead><tr>${[t.who, t.count, t.beforeColumn, t.afterColumn, t.delta, t.missing].map(x => `<th>${x}</th>`).join('')}</tr></thead><tbody>${b.rows.filter(r => r.count > .00001).map(r => `<tr><td>${t.labels[r.key]}</td><td>${fmt(r.count, 0)}</td><td>${fmt(r.before)}</td><td>${fmt(r.after)}</td><td class="${r.delta > 0 ? 'transition-loss' : 'transition-gain'}">${signed(r.delta)}</td><td>${fmt(r.unserved, 0)}</td></tr>`).join('')}</tbody></table></div><p class="fine">${t.cohortNote}</p><p>${t.cohortWarning}</p></div>
      <details class="transition-details"><summary>${t.sourceTitle}</summary><p>${esc(b.preset.scope[language()])}</p><p>${t.sourceModes}: ${TravelTransition.modes.map(k => `${t.labels[k]} ${b.preset.unreportedModes?.includes(k)?(language()==='pt'?'não separado na fonte':'not separated in source'):fmt(b.preset.shares[k] || 0)+'%'}`).join(' · ')}</p><p class="fine">${t.normalization}</p><p>${t.conflict}</p><p><a href="${esc(facts.population.annual_population.source_url)}" target="_blank" rel="noreferrer">INE ${facts.population.annual_population.reference_year}</a> · <a href="${esc(b.preset.source)}" target="_blank" rel="noreferrer">${esc(b.preset.label[language()])}</a> · <a href="pmus-mode-shares.md">PMUS: ${language() === 'pt' ? 'fontes e limites' : 'sources and scope'}</a> · <a href="amp-population-demand.md">AMP: ${language() === 'pt' ? 'população e procura' : 'population and demand'}</a></p></details>
      <div class="card"><h3>${t.native}</h3><p class="fine">${t.nativeNote} ${t.nativeCase}</p>${nativeTable(t)}</div>`;
    document.getElementById('transitionResults').innerHTML = html;
  }
  function nativeTable(t) {
    const groups = corridor(); if (!groups) return '';
    return `<div class="transition-table"><table><thead><tr><th>${t.nativeGroup}</th><th>${t.nativeTime}</th><th>${t.nativeUnserved}</th></tr></thead><tbody>${Object.keys(groups.baseline).map(k => {
      const a = groups.baseline[k], b = groups.restricted[k];
      return `<tr><td>${t.labels[k] || esc(k)}</td><td>${fmt(a.minutes)} → ${fmt(b.minutes)}</td><td>${fmt(a.unserved)} → ${fmt(b.unserved)}</td></tr>`;
    }).join('')}</tbody></table></div>`;
  }
  function report() {
    const t = C[language()], b = last.future, a = last.immediate;
    const lines = [`# ${t.title}`, '', t.warning, '', `- INE 2025 AMP: ${facts.population.annual_population.metropolitan_population}`, `- ${b.preset.label[language()]}`, `- ${t.regionalTrips}: ${fmt(b.totalDaily, 0)}`, `- ${t.trips}: ${fmt(b.requests, 0)}`, '', `| ${t.before} | ${t.immediate} | ${t.future} |`, '|---|---|---|', `| ${fmt(b.beforeMean)} min | ${fmt(a.mean)} min | ${b.allServed ? fmt(b.mean) + ' min' : t.noMean} |`, '', `${t.threshold}: ${last.breakEven === null ? t.noThreshold : last.breakEven + '% ' + t.thresholdText}`, '', `${t.unserved}: ${fmt(b.unserved, 0)}`, '', `| ${t.who} | ${t.count} | ${t.beforeColumn} | ${t.afterColumn} | ${t.delta} | ${t.missing} |`, '|---|---:|---:|---:|---:|---:|'];
    for (const r of b.rows) lines.push(`| ${t.labels[r.key]} | ${fmt(r.count, 0)} | ${fmt(r.before)} | ${fmt(r.after)} | ${signed(r.delta)} | ${fmt(r.unserved, 0)} |`);
    lines.push('', t.cohortNote, '', t.cohortWarning, '', t.inputNote, '', t.scopeNote, '', '## Parameters / Parâmetros', '', '```json', JSON.stringify(p, null, 2), '```', '', '## Sources / Fontes', '', `- [INE 2025](${facts.population.annual_population.source_url})`, `- [${b.preset.label[language()]}](${b.preset.source})`, '- [PMUS documents](https://mobilidade.cm-porto.pt/destaque/pmus-discussao-publica)', '', t.conflict, '', 'No calibrated adoption or metropolitan OD model. A feasible alternative must also meet bus punctuality, access and implementation requirements.');
    return lines.join('\n');
  }
  function render() {
    if (renderedLanguage !== language()) { renderedLanguage = language(); build(); }
    results();
  }
  render();
  return { render, report, parameters: () => p, results: () => last };
};
