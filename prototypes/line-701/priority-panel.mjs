const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function presentation(data) {
  const rows=data.trials.filter(t=>!t.diagnostic_only&&t.eligible_for_comparison);
  return {rows, planned:[...new Set(rows.map(t=>t.metrics.planned))].join(' / ')};
}

export async function loadEvidenceJSON(url, expectedSha256) {
  const response=await fetch(url);
  if(!response.ok)throw Error('Evidence unavailable: '+url);
  const bytes=await response.arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
  if(!expectedSha256||hash!==expectedSha256)throw Error('Evidence source version mismatch: '+url);
  return JSON.parse(new TextDecoder().decode(bytes));
}

/** A separate research ledger: these runs never inherit the published replay. */
export function prioritySearchHTML(data, lang, reportUrl) {
  const pt = lang === 'pt', choose = (en, portuguese) => pt ? portuguese : en;
  const {rows,planned}=presentation(data);
  const unfinished=rows.some(t=>t.traffic!=='none'&&t.metrics.completed<t.metrics.planned)?choose('Some trips do not finish within the simulated service-day window.','Há viagens que não chegam ao fim dentro do período simulado.'):'';
  return `<div class="eyebrow">${choose('THE NEXT DESIGN ITERATION','A PRÓXIMA ITERAÇÃO')}</div>
    <h2>${choose('A reliable bus needs more than a clear lane.','Um autocarro pontual precisa de mais do que uma via livre.')}</h2>
    <p>${choose('We are testing junction priority, faster boarding and better dispatch. The target stays the same: every scheduled departure and every published timing point, in both directions.','Testamos prioridade nos cruzamentos, embarque mais rápido e melhor gestão das partidas. A meta mantém-se: cumprir todas as partidas e pontos de horário, nos dois sentidos.')}</p>
    <p class="notice">${choose('No tested package meets every checkpoint yet. These new street-detail experiments are separate from the animation above; traffic, passenger loads and signal timings remain assumptions.','Ainda nenhum pacote testado cumpre todos os pontos de horário. Estes novos testes de detalhe urbano são distintos da animação acima; o tráfego, a procura de passageiros e os tempos semafóricos continuam a ser pressupostos.')} ${unfinished}</p>
    <div class="split"><div><h3>${choose('Priority without removing pedestrian time','Prioridade sem retirar tempo aos peões')}</h3><p>${choose('Test up to 10 seconds of green extension and earlier release for buses, retaining phase order, pedestrian greens, amber and all-red phases. These are assumed programs for testing, not approved controller plans.','Testar prolongamentos de verde até 10 segundos e abertura antecipada para o autocarro, mantendo a ordem das fases, os verdes pedonais, o amarelo e o vermelho integral. São programas assumidos para testes, não planos aprovados.')}</p></div><div><h3>${choose('Make the stop and the service work together','Fazer a paragem e o serviço funcionar em conjunto')}</h3><p>${choose('Compare request stops and faster boarding with finite bus capacity. Holding space and standby buses need explicit space, vehicles and staffing; they are not free fixes.','Comparar paragens a pedido e embarque mais rápido, com capacidade limitada dos autocarros. Espaço para regular horários e autocarros de reserva exigem espaço, veículos e pessoal; não são soluções gratuitas.')}</p></div></div>
    <details><summary>${choose('Inspect every test and the remaining obstacles','Consultar todos os testes e os obstáculos por resolver')}</summary>
    <p>${choose('Our strict research target requires exact departures at designated checks and terminal arrivals no later than scheduled, for every planned trip. It is stricter than the operator’s contractual indicators. The iteration report explains their different measured events, time windows and completed-trip denominators.','A nossa meta de investigação exige partidas à hora exata nos pontos definidos e chegadas ao terminal sem atraso, em todas as viagens previstas. É mais exigente do que os indicadores contratuais do operador. O relatório explica os diferentes momentos medidos, as tolerâncias e as viagens completas contabilizadas.')}</p>
    <p>${choose(`Each row covers all ${planned} scheduled trips for one day and one random seed. Bus-only rows include passengers and walking requests only when shown in the data. Superseded imports and invalid traffic comparisons remain in the ledger and are excluded here.`,`Cada linha cobre as ${planned} viagens previstas de um dia e uma semente aleatória. As linhas sem automóveis incluem passageiros e pedidos pedonais apenas quando indicados nos dados. Importações anteriores e comparações inválidas ficam no registo e são excluídas desta tabela.`)}</p>
    <div class="table-wrap"><table><thead><tr><th>${choose('Test / model','Teste / modelo')}</th><th>${choose('On-time starts','Partidas pontuais')}</th><th>${choose('On-time terminal arrivals','Chegadas pontuais ao terminal')}</th><th>${choose('Reached the endpoint, including late','Chegaram ao fim, incluindo atrasos')}</th><th>${choose('Failed timing points','Pontos de horário falhados')}</th><th>${choose('Unserved car/other vehicle requests','Pedidos de automóveis/outros veículos não servidos')}</th></tr></thead><tbody>${rows.map(t => `<tr><td>${escape(t.label?.[lang] || t.id)}<br><span class="fine">${escape(t.model_id)} · ${escape(t.traffic)} · seed ${t.seed}</span></td><td>${t.metrics.on_time_starts}/${t.metrics.planned}</td><td>${t.metrics.on_time_finishes}/${t.metrics.planned}</td><td>${t.metrics.completed}/${t.metrics.planned}</td><td>${t.metrics.late_checkpoints + t.metrics.missing_checkpoints + t.metrics.early_departures}/${t.metrics.checkpoints}</td><td>${t.unserved_vehicle_requests}/${t.vehicle_requests}</td></tr>`).join('')}</tbody></table></div>
    <p>${choose('The next validation needs current controller plans, surveyed stop locations and speed signs, passenger counts, and actual bus rotations. This ledger includes failed and optimistic diagnostic runs; diagnostics cannot qualify a proposal.','A próxima validação precisa de planos semafóricos atuais, levantamento das paragens e sinais de velocidade, contagens de passageiros e rotações reais dos autocarros. O registo inclui testes falhados e diagnósticos otimistas; os diagnósticos não podem qualificar uma proposta.')}</p>
    <p><a href="${escape(reportUrl)}">${choose('Read the iteration report','Ler o relatório de iterações')}</a></p></details>
    <p class="fine">${choose('Map option: CMP signals & crossings shows municipal location evidence. Equipment points are not controllers; LED crossings are a small subset. Timings are unknown.','Opção do mapa: semáforos e passadeiras CMP mostra localizações do inventário municipal. Os pontos de equipamento não são controladores; as passadeiras LED são um pequeno subconjunto. Os tempos são desconhecidos.')}</p>`;
}

export async function mountPriorityPanel({host, url, reportUrl, getLang, expectedSha256}) {
  if (!url) { host.hidden = true; return null; }
  const data = await loadEvidenceJSON(url, expectedSha256);
  function renderLanguage() { host.innerHTML = prioritySearchHTML(data, getLang(), reportUrl); }
  renderLanguage();
  return {renderLanguage, markdown(lang) {
    const pt=lang==='pt', {rows,planned}=presentation(data);
    return '\n\n## '+(pt?'Pesquisa complementar de prioridade · distinta do replay selecionado':'Supplementary priority search · separate from the selected replay')+'\n\n'+
      (pt?`Ainda nenhum pacote cumpre todos os pontos de horário. Procura e programas semafóricos são pressupostos. Cada linha cobre ${planned} viagens e uma semente; comparações inválidas e importações anteriores são excluídas.`:`No package meets every timetable checkpoint yet. Demand and signal programs are assumed. Each row covers ${planned} trips and one seed; invalid comparisons and superseded imports are excluded.`)+
      '\n\n'+(pt?'A meta de investigação exige partidas exatas e chegadas ao terminal sem atraso em todas as viagens previstas. É mais exigente do que os indicadores contratuais do operador; não calculamos aqui conformidade contratual.':'The research target requires exact departures and no-later-than terminal arrivals for every scheduled trip. It is stricter than the operator’s contractual indicators; contractual compliance is not calculated here.')+
      '\n\n| '+(pt?'Teste / rede | Partidas pontuais | Chegadas pontuais | Pontos falhados | Passageiros servidos':'Test / network | On-time starts | On-time terminal arrivals | Failed checkpoints | Passengers served')+' |\n|---|---:|---:|---:|---:|\n'+
      rows.map(t=>`| ${t.label?.[lang]||t.id} · ${t.model_id} · ${t.traffic} | ${t.metrics.on_time_starts}/${t.metrics.planned} | ${t.metrics.on_time_finishes}/${t.metrics.planned} | ${t.metrics.late_checkpoints+t.metrics.missing_checkpoints+t.metrics.early_departures}/${t.metrics.checkpoints} | ${t.arrived_passengers}/${t.passenger_requests} |`).join('\n')+
      '\n\n'+(pt?'As localizações municipais não fornecem fases/tempos. São necessários planos semafóricos, levantamento de paragens e sinalização, contagens de passageiros e rotações reais.':'Municipal locations do not supply phases/timings. Current signal plans, stop/sign surveys, passenger counts and actual bus rotations are still required.')+
      '\n\nSHA-256: '+expectedSha256+'\n\n['+(pt?'Relatório completo das iterações':'Full iteration report')+']('+new URL(reportUrl,location.href).href+')\n';
  }};
}
