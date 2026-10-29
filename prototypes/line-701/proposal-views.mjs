// Citizen and urbanist adapters consume the same reviewed snapshot.
const minutes=value=>Number.isFinite(value)?value/60:null;
const number=(value,lang,digits=1)=>Number.isFinite(value)?value.toLocaleString(lang==='pt'?'pt-PT':'en-GB',{maximumFractionDigits:digits}):'—';
const reasons={
 en:{reference_changed:'The source data has changed since this proposal was shared. Results are withheld until you choose to use the current sources.',outside_coverage:'This selection has no prepared traffic replay. Official route and timetable data remain available.',unprepared_policy:'This policy has no matching prepared replay. Your proposal is preserved; neither view will replace it with another policy.',different_demand:'The requested demand differs between these scenarios; this is not a matched comparison.',unmatched_capture:'The scene, policy or capture window could not be matched. No substitute replay is shown.'},
 pt:{reference_changed:'Os dados de origem mudaram desde a partilha desta proposta. Os resultados ficam indisponíveis até escolher usar as fontes atuais.',outside_coverage:'Esta seleção não tem um replay de tráfego preparado. O percurso e horário oficiais continuam disponíveis.',unprepared_policy:'Esta política não tem um replay preparado correspondente. A proposta é preservada; nenhuma das vistas a substitui por outra política.',different_demand:'A procura solicitada difere entre os cenários; não é uma comparação equivalente.',unmatched_capture:'Não foi possível confirmar a correspondência do cenário, política ou período de captura. Não é mostrado outro replay.'}
};
export function citizenStory(proposal,lang='en') {
 const pt=lang==='pt',f=proposal.focus,n=proposal.native;
 const warning=proposal.replay.reason?reasons[lang][proposal.replay.reason]:null;
 return {id:proposal.id,title:`${n.line||"701"} · ${f.from_name || f.from || ''} → ${f.to_name || f.to || ''}`,
  stamp:pt?'Proposta exploratória · simulação com tráfego sintético':'Exploratory proposal · synthetic traffic simulation',
  coverage:pt?`Replay: ${proposal.replay.scope.from || '—'} → ${proposal.replay.scope.to || '—'} · sentido ${proposal.replay.scope.direction || '—'} · semente ${proposal.replay.seed || '—'}`:`Replay: ${proposal.replay.scope.from || '—'} → ${proposal.replay.scope.to || '—'} · direction ${proposal.replay.scope.direction || '—'} · seed ${proposal.replay.seed || '—'}`,
  summary:!n.available?(pt?'Consulte o percurso e o horário desta secção. Não há resultados de tráfego correspondentes para esta seleção.':'Review the route and timetable for this section. Matching traffic results are not available for this selection.'):
   !n.can_claim_gain?(pt?'Há viagens incompletas ou procura não servida nesta comparação. Um autocarro mais rápido, por si só, não demonstra uma melhoria para todos.':'This comparison has incomplete journeys or unserved demand. A faster completed bus alone does not demonstrate an improvement for everyone.'):
   (pt?'Compare a pontualidade e o acesso com a mesma procura solicitada. Os valores são simulados, não atrasos medidos.':'Compare punctuality and access under the same requested demand. Values are simulated, not measured delays.'),
  replayEligible:proposal.replay.eligible,warning,
  metrics:n.available?{completed_before:`${n.baseline.completed}/${n.baseline.planned}`,completed:`${n.alternative.completed}/${n.alternative.planned}`,unserved_before:Object.values(n.baseline.groups).reduce((sum,g)=>sum+g.unserved,0),unserved:Object.values(n.alternative.groups).reduce((sum,g)=>sum+g.unserved,0),change_minutes:n.can_claim_gain?(n.baseline.final_lateness.mean-n.alternative.final_lateness.mean)/60:null}:null};
}

export function observationFinding(evidence,lang='en') {
 const pt=lang==='pt',f=evidence.finding;
 const source=evidence.kind==='uploaded_arrivals'?(pt?'Chegadas fornecidas pelo utilizador, sem verificação independente.':'User-supplied arrivals, not independently verified.'):
  evidence.kind==='gps_passage_windows'?(pt?'Janelas de passagem inferidas de GPS; não são eventos de abertura de portas.':'GPS-derived passage windows; not door-open arrival events.'):(pt?'Sem observações correspondentes.':'No matching observations.');
 const scope=evidence.focus?(pt?`Secção selecionada: ${evidence.focus.from} → ${evidence.focus.to} · ${evidence.focus.captured_stops} paragens captadas. `:`Selected section: ${evidence.focus.from} → ${evidence.focus.to} · ${evidence.focus.captured_stops} captured stops. `):'';
 return scope+(f?`${f.from} → ${f.to}: +${number(f.low/60,lang)} … +${number(f.high/60,lang)} min. `:(pt?'Não foi identificado um aumento positivo inequívoco entre paragens adjacentes nesta secção. ':'No unambiguous positive increase was identified between adjacent stops in this section. '))+source;
}

export function urbanistReport(proposal,lang='en',focusText='') {
 const pt=lang==='pt',n=proposal.native,story=citizenStory(proposal,lang);
 const lines=[focusText || `# ${story.title}`,'',`## ${pt?'Proposta revista':'Reviewed proposal'} ${proposal.id}`,'',
  `Reference: ${proposal.reference.date} · ${proposal.reference.actual}`,`Expected reference: ${proposal.reference.expected}`,`Direction / focus: ${proposal.focus.direction} · ${proposal.focus.from} → ${proposal.focus.to}`,
  `Policy / case: ${n.variant} / ${n.case}`,`Selected interval: ${n.selected_leg}`,`Selected observation: ${proposal.evidence.trip_id || '—'}`,'',story.summary,'',story.warning || '',
  '',`## ${pt?'Âmbito do modelo de ruas preparado':'Prepared street-model scope'}`,'',`${n.scope.from} → ${n.scope.to} · direction ${n.scope.direction}. Synthetic traffic; uncalibrated signals and dwell.`,
  `Selected focus overlap: ${proposal.focus.coverage}. Native numeric summaries span the prepared street section, not arbitrary focus endpoints.`,''];
 if(n.available){
  lines.push(`| ${pt?'Paragem':'Stop'} | ${pt?'Horário':'Schedule'} | Baseline min | ${pt?'Proposta':'Proposal'} min |`,'|---|---|---:|---:|');
  const a=n.baseline.trips[n.trip.id],b=n.alternative.trips[n.trip.id];
  n.scope.stops.forEach((s,i)=>lines.push(`| ${s.stop_id} ${s.stop_name} | ${n.trip.stops[i].scheduled_text} | ${number(minutes(a?.stops[i].lateness.mean),lang)} | ${number(minutes(b?.stops[i].lateness.mean),lang)} |`));
  lines.push('',`Completed buses: ${n.alternative.completed}/${n.alternative.planned}. Comparable requested demand: ${n.demand_comparable}. Gain claim eligible: ${n.can_claim_gain}.`,'',
   '| Group | Planned | Baseline unserved | Proposal unserved | Baseline network min | Proposal network min | Baseline entry wait min | Proposal entry wait min |','|---|---:|---:|---:|---:|---:|---:|---:|');
  for(const [key,g]of Object.entries(n.alternative.groups))lines.push(`| ${key} | ${g.planned} | ${n.baseline.groups[key].unserved} | ${g.unserved} | ${number(minutes(n.baseline.groups[key].seconds.mean),lang)} | ${number(minutes(g.seconds.mean),lang)} | ${number(minutes(n.baseline.groups[key].departure_delay?.mean),lang)} | ${number(minutes(g.departure_delay?.mean),lang)} |`);
 }
 lines.push('',`## ${pt?'Evidência selecionada':'Selected evidence'}`,'',observationFinding(proposal.evidence,lang),'',JSON.stringify(proposal.evidence,null,2),'',
  `## ${pt?'Modelo operacional distinto':'Separate operational model'}`,'',proposal.service?'Assumed whole-line inbound passenger/berth model; not observed or microscopic street traffic.':'Not available for this direction, data version or loading state.',proposal.service?JSON.stringify(proposal.service,null,2):'',
  '',`## ${pt?'Compatibilidade do replay':'Replay compatibility'}`,'',JSON.stringify(proposal.replay,null,2),'',
  `## ${pt?'Política revista':'Reviewed policy'}`,'',JSON.stringify({route:n.line||'701',direction_id:Number(n.scope.direction),priority_by_direction:n.policy_by_direction,applied_priority_edges:n.applied_priority_edges,start_stop:n.scope.from,end_stop:n.scope.to,priority_segments:n.priority},null,2),'',
  'Source: https://stcp.pt/pt/linhas/'+(n.line||'701'),'Source and capture hashes are retained in the proposal JSON and replay manifest. Uploaded observations remain user-supplied; neither GPS windows nor a replay establishes calibrated recurring delays.','');
 return lines.join('\n');
}
