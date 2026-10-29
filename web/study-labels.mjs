/** Study descriptions derive from the selected dataset, never another line's defaults. */
export function studyLabels(data,lang='en') {
  const pt=lang==='pt',route=String(data.meta.route),directions=Object.values(data.native_directions||{}),count=data.full_traffic_summary?.trip_count??(directions.length?directions.reduce((n,d)=>n+d.route.morning.length,0):data.route.morning?.length);
  const clip=data.replay_manifest?.clips?.[0],origin=data.meta.time_origin_seconds||0;
  const clock=seconds=>{const n=Math.round(seconds+origin);return `${String(Math.floor(n/3600)).padStart(2,'0')}:${String(Math.floor(n%3600/60)).padStart(2,'0')}`};
  const window=clip?clock(clip.start)+'–'+clock(clip.end):'—',step=clip?.step??'—',dwell=data.meta.dwell_seconds;
  return {
    analysisTitle:pt?'Análise técnica · dados e hipóteses do estudo':'Technical analysis · study data and assumptions',
    analysisScope:pt?`Este estudo inclui ${count??'—'} partidas previstas nos sentidos declarados. Os perfis de autocarro referem-se ao sentido escolhido; os totais de tráfego têm o âmbito regional indicado nas fontes.`:`This study includes ${count??'—'} scheduled departures across its declared directions. Bus profiles refer to the selected direction; traffic totals retain the regional scope declared in the sources.`,
    limits:(pt?'Resultados de simulação, distintos de horários publicados e observações. ':'Simulated results are distinct from published schedules and observations. ')+(Number.isFinite(dwell)?(pt?`Hipótese de paragem: ${dwell} segundos. `:`Stop dwell assumption: ${dwell} seconds. `):'')+(pt?'Procura, sinais, outras linhas e blocos de veículos têm a validação e cobertura declaradas nas fontes; não é demonstrada pontualidade real.':'Demand, signals, other routes and vehicle blocks retain the validation and coverage declared in the sources; real punctuality is not established.'),
    scope:route+' · '+data.route.start+' → '+data.route.end,
    routeTitle:data.route.start+' → '+data.route.end,
    profileNote:pt?'Cinzento: referência. Verde: plano selecionado. Desvio face ao horário publicado; passagens não servidas permanecem vazias. As amplitudes abrangem as execuções nativas disponíveis, não um intervalo de confiança.':'Grey: baseline. Green: selected plan. Deviation from published references; unserved calls remain empty. Ranges span available native runs, not a confidence interval.',
    replayNote:pt?`Replay nativo ${window}, com amostras a cada ${step} segundos e interpolação visual. As posições provêm da execução identificada nas fontes; as métricas diárias têm o seu âmbito próprio.`:`Native replay ${window}, sampled every ${step} seconds with visual interpolation. Positions come from the execution identified in the sources; daily metrics retain their own scope.`,
    observedNote:data.observations?.counts?.accepted>0?(pt?`Amostra de ${data.observations.counts.accepted} posições: ${data.observations.captured_from||'—'} → ${data.observations.captured_to||'—'}. Janelas de passagem GPS não são chegadas com abertura de portas nem calibram atrasos recorrentes.`:`Sample of ${data.observations.counts.accepted} positions: ${data.observations.captured_from||'—'} → ${data.observations.captured_to||'—'}. GPS passage windows are not door-open arrivals and do not calibrate recurring delays.`):(pt?'Não existe uma amostra de posições correspondente. Chegadas importadas são dados fornecidos pelo utilizador, sem verificação independente.':'No matched position sample is available. Imported arrivals are user-supplied and not independently verified.'),
    generated:pt?'Atraso acrescentado após a origem':'Delay added after journey origin',
    growthNote:pt?'Uma amostra face a referências publicadas é uma pista para investigar, não prova da causa do atraso.':'A sample relative to published references is a lead to investigate, not evidence of the cause of delay.',
    trip:pt?'Partida prevista':'Scheduled departure',
    completed:pt?'Partidas que chegaram ao destino':'Departures reaching their destination',
    entry:pt?'Atraso simulado na origem':'Simulated origin lateness',
    nativeCheck:pt?'Verificação nativa da pontualidade':'Native punctuality check'
  };
}
