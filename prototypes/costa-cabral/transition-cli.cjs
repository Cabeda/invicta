// Code-first counterpart of the browser population calculator; no dependencies.
const fs = require('node:fs');
const path = require('node:path');
require('./transition-model.js');
const args = process.argv.slice(2);
const root = __dirname;
const arg = (key, fallback) => args.includes(key) ? args[args.indexOf(key) + 1] : fallback;
const facts = JSON.parse(fs.readFileSync(path.join(root, 'data/transition-facts.json')));
const source = arg('--input', null);
const input = source ? JSON.parse(fs.readFileSync(source)) : {};
const parameters = { ...TravelTransition.defaults, ...(input.parameters || input), times: { ...TravelTransition.defaults.times, ...(input.parameters || input).times } };
const model = TravelTransition.compare(parameters, facts);
if (model.error) throw new Error('Mode destination and purpose allocations must each total at most 100%');
const out = path.resolve(arg('--output', path.join(root, 'population-scenario')));
const { immediate: a, future: b } = model;
const n = x => x === null ? 'unavailable' : x.toFixed(2);
const names = { residentDrivers: 'Residents who keep driving', workDrivers: 'Non-residents: work/study, keep driving', shoppingDrivers: 'Non-residents: shopping, keep driving', leisureDrivers: 'Non-residents: leisure/outings, keep driving', otherDrivers: 'Non-residents: other, keep driving', existingBus: 'Existing bus users', switchBus: 'People switching car to bus', switchBicycle: 'People switching car to bicycle', switchWalk: 'People switching car to walking', metro: 'Existing metro users', train: 'Existing train users', bicycle: 'Existing cyclists', walk: 'Existing walking trips', motorcycle: 'Motorcycle/moped users', other: 'Other modes' };
fs.writeFileSync(out + '.json', JSON.stringify({ conditional: true, parameters, results: model, sourceFacts: facts }, null, 2));
const csv = [['stage', 'cohort', 'requests', 'served', 'unserved', 'before_minutes', 'after_if_served_minutes', 'delta_minutes']];
for (const stage of ['immediate', 'future']) for (const r of model[stage].rows) csv.push([stage, r.key, r.count, r.served, r.unserved, r.before, r.after, r.delta]);
fs.writeFileSync(out + '.csv', csv.map(r => r.join(',')).join('\n') + '\n');
const lines = ['# Porto: people, access and the transition', '', '**Conditional population what-if. Not a calibrated metropolitan traffic forecast.**', '',
  'The question is whether an initial disruption can be followed by lower average person-trip time if alternatives improve and enough people change mode. This model can show gains, losses or no feasible improvement; it does not predict adoption.', '',
  '## Sourced context and assumed inputs', '',
  `- INE ${facts.population.annual_population.reference_year}: ${facts.population.annual_population.metropolitan_population.toLocaleString('en-GB')} AMP residents; ${facts.population.annual_population.porto_municipality_population.toLocaleString('en-GB')} in Porto municipality. These are residents, not vehicles or daily trips.`,
  `- Selected mode reference: ${b.preset.label.en}. ${b.preset.scope.en}`,
  '- Population-based trip volume uses an assumed combined eligible-and-mobile share of all residents. The 2.72 rate belongs to mobile people aged 6–84 in IMob 2017. Combining it with 2025 population is a scenario, not an observed 2025/2026 daily total.',
  '- Every journey time, access penalty, purpose/residency allocation, service-capacity margin and congestion response below is an explicit assumption. No census table supplies these joint person/OD/purpose/mode records.',
  '- Additional outside-AMP visitor trips are a user input, initially zero because no total was established. Zero is not evidence that no such visits occur.', '',
  '## Three stages, with the same requested affected trips', '',
  '| Stage | Mean minutes per affected person-trip | Unserved requests/day |', '|---|---:|---:|',
  `| Before | ${n(b.beforeMean)} | 0 in this accounting reference |`,
  `| Immediate, no switching | ${n(a.mean)} | ${n(a.unserved)} |`,
  `| If ${parameters.shift}% of car person-trips switch | ${n(b.mean)} | ${n(b.unserved)} |`, '',
  `Represented regional requests/day: ${n(b.totalDaily)}. Affected requests/day: ${n(b.requests)}. Trips outside the assumed affected share retain their baseline time.`, '',
  b.allServed ? `Average change: ${n(b.meanDelta)} minutes per affected person-trip; ${n(b.personHoursDelta)} person-hours/day. Regional mean change: ${n(b.metroMeanDelta)} minutes.` : 'The full-request mean is withheld because bus demand exceeds the supplied capacity. The served-trip mean is conditional and cannot rank the proposal for the whole population.', '',
  model.breakEven === null ? 'No feasible break-even found up to 60% switching under these assumptions.' : `The first capacity-feasible crossing below the baseline average is ${model.breakEven}% switching in a one-percentage-point scan. This is not an observed elasticity, predicted adoption level or calendar date.`, '',
  `The selected scenario needs +${n(b.requiredCapacityGrowth)}% bus passenger-trip capacity above initial demand; +${parameters.capacityGrowth}% is assumed available. This is a boarding-capacity ceiling, not a costed fleet/timetable plan.`, '',
  '## Who gains and who loses', '', '| Cohort | Person-trip requests | Before min | After if served min | Change min | Unserved |', '|---|---:|---:|---:|---:|---:|'];
for (const r of b.rows) lines.push(`| ${names[r.key]} | ${n(r.count)} | ${n(r.before)} | ${n(r.after)} | ${n(r.delta)} | ${n(r.unserved)} |`);
lines.push('', 'Worker/student, shopper and leisure rows refer to non-residents who keep driving. Purpose weights are scenario assumptions, not PMUS observations for car drivers. PMUS purpose marginals exclude return-home trips and cannot establish a joint purpose-by-mode table. More detailed trip chains and access requirements are still needed.', '',
  'A lower overall average does not mean every person benefits. People switching to a bus can also have a longer journey under some assumptions. The model imposes a switching fraction; a validated mode-choice model would need fares, service reliability, access, transfers, parking, income/constraints and observed behaviour.', '',
  '## The equations are intentionally visible', '',
  '- Affected requests = regional requests × affected share.',
  '- Population demand = population × combined eligible/mobile fraction × trips per mobile person. The alternative is the historical 3.4 million-trip benchmark.',
  '- Mode shares are normalized for arithmetic; original rounded source values remain in the facts file.',
  '- Remaining car pressure = 1 − switching fraction × assumed car-removal effectiveness.',
  '- Car time = baseline car time − baseline congestion minutes + congestion minutes × remaining pressure^exponent + group access penalty.',
  '- Bus time = baseline bus time − assumed service saving + boarding penalty × additional bus demand / baseline bus demand.',
  '- Bus capacity = baseline bus demand × (1 + assumed spare/added capacity). Excess requests remain unserved. Existing and new bus requests share that shortage proportionally.',
  '- Average = sum of person-trip time divided by person-trip requests. It is withheld if requests remain unserved. Weighting vehicles equally would misrepresent buses.', '',
  'This algebra is a transparent sensitivity model, not a physical traffic assignment or behavioural equilibrium. It does not derive regional congestion from the Costa Cabral road network. Road pressure, occupancy and additional bus flows need calibrated assignment for a forecast.', '',
  '## Implementation and measurement sequence', '',
  '1. Audit baseline lanes, junctions and signals. Collect all-purpose OD, bus AVL/loads, local access and turning counts on matched days, including non-residents and mobility constraints.',
  '2. Define destinations and access: homes, work/study, shops, walks/leisure, care and deliveries. Model access on foot, by bicycle, bus/taxi and parking/drop-off approaches; do not equate every need with a private-car exemption.',
  '3. Test a reversible package and the immediate/no-switch case. Protect essential access, accessible stops, loading and surrounding streets; keep unserved journeys visible.',
  '4. Provide the additional usable capacity/frequency and reliability needed before relying on adoption. Cost the required operations, stops, enforcement and works using dated quantities/rates.',
  '5. Observe route/mode changes, rerun calibrated scenarios and compare independent days. Extend measures only when punctuality and access requirements are met. Avoid claiming a fixed number of years from an assumed adoption slider.', '',
  '## Source limits', '', facts.cross_year_warning,
  'PMUS 2035 commuting targets conflict between narrative and Table 49. They are not all-purpose observed shares and neither is used as a promised endpoint. The PMUS nonresident survey focuses on workers/students and is not guaranteed to represent every shopper, leisure visitor or tourist.', '',
  'The native SUMO corridor report is separate: imported OSM baseline is retained; lane reduction is proposal-only. General vehicle-group data do not identify real residence or trip purpose. Earlier normalized-baseline bus-gain figures are superseded by the corrected comparison.', '',
  '## Parameters', '', '```json', JSON.stringify(parameters, null, 2), '```', '', '## Primary sources', '',
  `- [INE population JSON, reference ${facts.population.annual_population.reference_year}](${facts.population.annual_population.source_url})`,
  `- [IMob 2017 original report](${facts.pmus.amp_imob2017.source_url}#page=37)`,
  `- [PMUS all-trip mode chart, printed p91 / PDF p102](${facts.pmus.pmus_all_trip_modes.source_url}#page=102)`,
  `- [PMUS purposes, excluding home returns, printed p89 / PDF p100](${facts.pmus.pmus_trip_purposes.source_url}#page=100)`,
  '- [Official PMUS document page](https://mobilidade.cm-porto.pt/destaque/pmus-discussao-publica)', '');
fs.writeFileSync(out + '.md', lines.join('\n'));
console.log(JSON.stringify({ files: [out + '.json', out + '.csv', out + '.md'], before: b.beforeMean, immediate: a.mean, conditionalFuture: b.mean, breakEven: model.breakEven, unserved: b.unserved }));
