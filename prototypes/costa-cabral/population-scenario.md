# Porto: people, access and the transition

**Conditional population what-if. Not a calibrated metropolitan traffic forecast.**

The question is whether an initial disruption can be followed by lower average person-trip time if alternatives improve and enough people change mode. This model can show gains, losses or no feasible improvement; it does not predict adoption.

## Sourced context and assumed inputs

- INE 2025: 1,861,727 AMP residents; 273,476 in Porto municipality. These are residents, not vehicles or daily trips.
- Selected mode reference: AMP · all person trips · IMob 2017. AMP residents aged 6–84, all destinations; excludes visitors living outside AMP. Bus includes school/employer transport.
- Population-based trip volume uses an assumed combined eligible-and-mobile share of all residents. The 2.72 rate belongs to mobile people aged 6–84 in IMob 2017. Combining it with 2025 population is a scenario, not an observed 2025/2026 daily total.
- Every journey time, access penalty, purpose/residency allocation, service-capacity margin and congestion response below is an explicit assumption. No census table supplies these joint person/OD/purpose/mode records.
- Additional outside-AMP visitor trips are a user input, initially zero because no total was established. Zero is not evidence that no such visits occur.

## Three stages, with the same requested affected trips

| Stage | Mean minutes per affected person-trip | Unserved requests/day |
|---|---:|---:|
| Before | 31.96 | 0 in this accounting reference |
| Immediate, no switching | 34.21 | 0.00 |
| If 25% of car person-trips switch | 31.49 | 0.00 |

Represented regional requests/day: 3544728.21. Affected requests/day: 35447.28. Trips outside the assumed affected share retain their baseline time.

Average change: -0.46 minutes per affected person-trip; -273.88 person-hours/day. Regional mean change: -0.00 minutes.

The first capacity-feasible crossing below the baseline average is 19% switching in a one-percentage-point scan. This is not an observed elasticity, predicted adoption level or calendar date.

The selected scenario needs +144.27% bus passenger-trip capacity above initial demand; +150% is assumed available. This is a boarding-capacity ceiling, not a costed fleet/timetable plan.

## Who gains and who loses

| Cohort | Person-trip requests | Before min | After if served min | Change min | Unserved |
|---|---:|---:|---:|---:|---:|
| Residents who keep driving | 6290.12 | 35.00 | 34.01 | -0.99 | 0.00 |
| Non-residents: work/study, keep driving | 4672.66 | 35.00 | 36.01 | 1.01 | 0.00 |
| Non-residents: shopping, keep driving | 2336.33 | 35.00 | 36.01 | 1.01 | 0.00 |
| Non-residents: leisure/outings, keep driving | 2336.33 | 35.00 | 36.01 | 1.01 | 0.00 |
| Non-residents: other, keep driving | 2336.33 | 35.00 | 36.01 | 1.01 | 0.00 |
| Existing bus users | 2906.68 | 45.00 | 39.89 | -5.11 | 0.00 |
| People switching car to bus | 4193.41 | 35.00 | 39.89 | 4.89 | 0.00 |
| People switching car to bicycle | 1198.12 | 35.00 | 22.00 | -13.00 | 0.00 |
| People switching car to walking | 599.06 | 35.00 | 15.00 | -20.00 | 0.00 |
| Existing metro users | 708.95 | 30.00 | 30.00 | 0.00 | 0.00 |
| Existing train users | 283.58 | 45.00 | 45.00 | 0.00 | 0.00 |
| Existing cyclists | 141.79 | 22.00 | 22.00 | 0.00 | 0.00 |
| Existing walking trips | 6557.75 | 15.00 | 15.00 | 0.00 | 0.00 |
| Motorcycle/moped users | 460.81 | 28.00 | 28.00 | 0.00 | 0.00 |
| Other modes | 425.37 | 35.00 | 35.00 | 0.00 | 0.00 |

Worker/student, shopper and leisure rows refer to non-residents who keep driving. Purpose weights are scenario assumptions, not PMUS observations for car drivers. PMUS purpose marginals exclude return-home trips and cannot establish a joint purpose-by-mode table. More detailed trip chains and access requirements are still needed.

A lower overall average does not mean every person benefits. People switching to a bus can also have a longer journey under some assumptions. The model imposes a switching fraction; a validated mode-choice model would need fares, service reliability, access, transfers, parking, income/constraints and observed behaviour.

## The equations are intentionally visible

- Affected requests = regional requests × affected share.
- Population demand = population × combined eligible/mobile fraction × trips per mobile person. The alternative is the historical 3.4 million-trip benchmark.
- Mode shares are normalized for arithmetic; original rounded source values remain in the facts file.
- Remaining car pressure = 1 − switching fraction × assumed car-removal effectiveness.
- Car time = baseline car time − baseline congestion minutes + congestion minutes × remaining pressure^exponent + group access penalty.
- Bus time = baseline bus time − assumed service saving + boarding penalty × additional bus demand / baseline bus demand.
- Bus capacity = baseline bus demand × (1 + assumed spare/added capacity). Excess requests remain unserved. Existing and new bus requests share that shortage proportionally.
- Average = sum of person-trip time divided by person-trip requests. It is withheld if requests remain unserved. Weighting vehicles equally would misrepresent buses.

This algebra is a transparent sensitivity model, not a physical traffic assignment or behavioural equilibrium. It does not derive regional congestion from the Costa Cabral road network. Road pressure, occupancy and additional bus flows need calibrated assignment for a forecast.

## Implementation and measurement sequence

1. Audit baseline lanes, junctions and signals. Collect all-purpose OD, bus AVL/loads, local access and turning counts on matched days, including non-residents and mobility constraints.
2. Define destinations and access: homes, work/study, shops, walks/leisure, care and deliveries. Model access on foot, by bicycle, bus/taxi and parking/drop-off approaches; do not equate every need with a private-car exemption.
3. Test a reversible package and the immediate/no-switch case. Protect essential access, accessible stops, loading and surrounding streets; keep unserved journeys visible.
4. Provide the additional usable capacity/frequency and reliability needed before relying on adoption. Cost the required operations, stops, enforcement and works using dated quantities/rates.
5. Observe route/mode changes, rerun calibrated scenarios and compare independent days. Extend measures only when punctuality and access requirements are met. Avoid claiming a fixed number of years from an assumed adoption slider.

## Source limits

2025 population combined with historical mobility references only as an explicit scenario; not observed 2025/2026 demand.
PMUS 2035 commuting targets conflict between narrative and Table 49. They are not all-purpose observed shares and neither is used as a promised endpoint. The PMUS nonresident survey focuses on workers/students and is not guaranteed to represent every shopper, leisure visitor or tourist.

The native SUMO corridor report is separate: imported OSM baseline is retained; lane reduction is proposal-only. General vehicle-group data do not identify real residence or trip purpose. Earlier normalized-baseline bus-gain figures are superseded by the corrected comparison.

## Parameters

```json
{
  "population": 1861727,
  "mobileShare": 70,
  "tripsPerMobile": 2.72,
  "demandBasis": "population",
  "affectedShare": 1,
  "externalTrips": 0,
  "preset": "amp2017",
  "nonresidentShare": 65,
  "workShare": 40,
  "shoppingShare": 20,
  "leisureShare": 20,
  "shift": 25,
  "toBus": 70,
  "toBicycle": 20,
  "removalEffect": 90,
  "residentDetour": 3,
  "visitorDetour": 5,
  "congestionMinutes": 10,
  "exponent": 2,
  "busGain": 8,
  "boardingPenalty": 2,
  "capacityGrowth": 150,
  "carOccupancy": 1.5,
  "times": {
    "car": 35,
    "bus": 45,
    "metro": 30,
    "train": 45,
    "bicycle": 22,
    "walk": 15,
    "motorcycle": 28,
    "other": 35
  }
}
```

## Primary sources

- [INE population JSON, reference 2025](https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=0012918&lang=PT)
- [IMob 2017 original report](https://www.amt-autoridade.pt/media/1829/inquerito_mobilidade_funcionalidade_territorio_aml_amp_2017_ine.pdf#page=37)
- [PMUS all-trip mode chart, printed p91 / PDF p102](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=102)
- [PMUS purposes, excluding home returns, printed p89 / PDF p100](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=100)
- [Official PMUS document page](https://mobilidade.cm-porto.pt/destaque/pmus-discussao-publica)
