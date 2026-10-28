# People, access and a possible mode transition

Question: can the report explain the immediate effects on all travellers and what would have to change for an initially disruptive scheme to improve average journey time?

**Implemented as an explicit conditional calculator in the bilingual proposal, under People & transition / Pessoas e transição.** It is separate from the SUMO corridor replay. The population is sourced; the response model is illustrative. No future adoption or metropolitan congestion forecast is established.

## What readers can explore

- Three stages: before, immediately after with no switching, and if a chosen share of car person-trips later switches.
- Official metropolitan population, five reference modal profiles, population-based demand or a historical trip-total benchmark, an affected-trip share and additional outside-AMP visits.
- Assumed bus service savings, non-resident/resident access penalties, switching destinations, car-removal effectiveness, occupancy, boarding effects and bus capacity.
- A break-even curve, effects on people who keep driving, weighted mean time and person-hours, plus explicit unmet bus demand.
- Non-resident worker/student, shopper and leisure/outings rows. Their counts and purpose allocations are assumptions; they are not observed joint purpose-by-mode records.
- Markdown explanation, source-rich scenario JSON and cohort CSV downloads. The native corridor table separately shows every simulated vehicle group's driving time and unserved requests.

## Sourced facts and their limits

INE's annual series, updated 22 June 2026, gives **1,861,727 AMP residents and 273,476 Porto municipality residents for reference 2025**. Census 2021 gives **1,736,228 and 231,800**, respectively. The 17 municipal 2025 totals match the metropolitan total. These are population counts, not traffic demand. [INE annual JSON](https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=0012918&lang=PT), [Census JSON](https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=0014584&lang=PT).

IMob 2017's all-purpose metropolitan person-trip reference is car 67.6%, bus 8.2%, metro 2.0%, train 0.8%, bicycle 0.4%, walking 18.5%, motorcycle/moped 1.3%, other 1.2%. Walking is derived from 18.9% active minus 0.4% bicycle. Bus includes school/employer transport. These concern AMP residents aged 6–84, all destinations; not today's fleet mix or visitors living outside AMP. The approximate 3.4 million daily trips and 2.72 trips per **mobile person** must not be applied to every current resident without a mobility/eligibility assumption. [Original INE report, PDF pp35–37](https://www.amt-autoridade.pt/media/1829/inquerito_mobilidade_funcionalidade_territorio_aml_amp_2017_ine.pdf#page=35).

PMUS provides separate all-trip reference profiles for Porto residents/non-residents on working and non-working days. Its non-resident sample is oriented to working/studying in Porto, and the diary deliberately collects only their journeys with an origin/destination in Porto. It is not assured representative of every shopper, tourist or leisure visitor. Purpose charts exclude return-home trips, and no joint purpose × mode OD table was established. The published 2035 commuting targets also conflict between text and Table 49; neither is used as a promised endpoint. [PMUS source audit](../../docs/research/pmus-mode-shares.md), [official documents](https://mobilidade.cm-porto.pt/destaque/pmus-discussao-publica).

## The illustrative default, not a forecast

The default combines 2025 population with an **assumed 70% eligible-and-mobile fraction** and the historical rate 2.72. This represents about **3.54 million person-trip requests/day**. An assumed 1% affected share gives about **35,447 affected requests**; it does not inject the whole metropolis into Costa Cabral.

With the example travel times, detours and response curve, average affected person-trip time is **31.96 → 34.21 → 31.49 minutes** before/immediately/at 25% switching. Remaining non-resident drivers still face about **+1.01 minute**. The first feasible crossing below the baseline is **19% switching**, on a one-percentage-point scan, under the chosen assumptions.

This example needs about **+144% bus passenger-trip capacity above baseline demand**, against an assumed available/spare/added margin of +150%. That does not mean +144% buses: spare places, turnover, timetable, fleet, routes and stop capacity need a real operating model. Setting the margin to zero leaves about **4,193 bus requests/day unserved** in the selected example; the calculator withholds the overall mean. It does not make those people disappear.

The model imposes the switching fraction; it does not estimate willingness or speed of adoption. Some switching travellers can have longer trips under the assumptions. Door-to-door minutes, fares, reliability, walking/transfer conditions, personal constraints and observed behaviour must underpin an actual mode-choice model. A time-weighted mean also cannot measure all accessibility, equity or wellbeing effects by itself.

## Code-first operation

`transition-model.js` is the same pure numerical module used by the website and CLI. `transition-panel.js` supplies the bilingual controls and explanation. Frozen source extracts, dates and hashes are in `data/transition-facts.json`, `data/amp-population-facts.json` and `data/pmus-facts.json`.

```sh
node prototypes/costa-cabral/transition-cli.cjs
node prototypes/costa-cabral/transition-cli.cjs --input /absolute/path/scenario.json --output /absolute/path/result
```

The input can be a parameter dictionary or an exported scenario with `parameters`. Outputs are `.md`, `.json` and `.csv`. Default outputs are `population-scenario.*`; they are included in the website export. The ready-to-host site needs no Node runtime; rebuilding the report uses Node alongside the existing Python/SUMO workflow.

The visible equations cover demand, mode transfers, car-pressure response, bus boarding/capacity and weighted time. The full equations and assumptions appear in the exported explanation. Source rounding is retained in the facts; profiles are normalized only for arithmetic.

## Baseline correction and what remains

The corridor baseline now retains the raw SUMO import of frozen OSM. Only the proposal reduces eight directed stretches from two lanes to one. Neither is an audited as-built layout. Bus routes are recomputed through the same scheduled stops for each policy.

After correction, the moderate bus mean is about **9.86 → 9.85 minutes**, and the proposal leaves more requested journeys unserved. Thus the previous large bus gains are superseded; the current experiment does not establish the expected benefit. Both native policies and all presentation/3D captures have been regenerated.

A calibrated metropolitan model needs a larger network, all-purpose OD/trip chains, age/eligibility constraints, destinations and activity timing, public-transport supply and capacity, access/parking approaches, matched traffic/AVL/load observations and validated mode/route choice. Census commuting tables cover only a subset. Shoppers and leisure visitors need their own evidence, including people living outside AMP. Simply multiplying the population by modal shares cannot supply these missing behaviours or destinations.

## Verification

- Conservation of requested person-trips and mode totals checked for all five reference profiles.
- A neutral scenario has zero change. A capacity shortage withholds the full-request mean. An adverse high-detour/no-service-gain case has no forced positive break-even.
- Corrected native baseline keeps eight two-lane directed stretches; proposal has one lane on all 75 corridor directed edges. All 18 SUMO runs completed.
- Native one-second 3D captures preserve all **232 completed bus-stop events** within the six new excerpts (38/38 moderate, 39/39 busy, 39/39 resident-demand; baseline/proposal).

This prototype answers the explanation/accounting question. It does not validate a real-world shift, a timetable improvement, a construction budget or a citywide implementation decision.
