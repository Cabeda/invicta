# Costa Cabral prototype: experiment findings

Question: does a two-direction corridor restriction preserve local access and junction crossings, and how does it behave under assumed demand?

**Throwaway, uncalibrated experiment. These are simulator outcomes, not a forecast or observed Porto performance.**

## Goal and local needs

Primary goal: help buses meet their published schedules while catering to residents, shoppers, businesses and everyday services. Assess early departures as well as late arrivals; practical local access is an explicit requirement.

The current final-stop arrival check (no more than three minutes late) is illustrative. It does not assess early departures or whole-route punctuality. Shopper, visitor and service access are not yet represented; the resident permit remains a local-origin/destination proxy. Faster completed bus trips alone do not establish success.

## Corrected baseline

Earlier results standardized the baseline as well as the proposal. Those headline gains are superseded. The current comparison preserves imported baseline lanes and applies the lane reduction only to the proposal; bus routes are recomputed against each network while retaining the same scheduled stops. This is an imported-map baseline, not a verified as-built inventory.

## Inputs and decisions

- SUMO 1.28.0; street map and source hashes in `data/manifest.json`.
- Access: bus, taxi, bicycle, motorcycle, synthetic local resident permit; ordinary cars can directly cross junctions. No longitudinal short-link exception.
- Local permits are assigned to origins/destinations on corridor edges; actual residents are not identified.
- Baseline preserves the unmodified frozen-OSM SUMO import. Only the proposal reduces eight multi-lane directed stretches to one lane per mapped direction. Imported lane counts and bus contraflow need a field audit.
- 21 of 21 requested GTFS trips mapped; service date 2 September 2026 (holiday weekday), not a current feed.
- Traffic OD, mode counts, 20-second dwell and generated signals are assumptions. No observed passenger loads or current calibration.
- Same synthetic requested trips in each paired policy run. All no-route and unfinished journeys counted. Teleporting disabled.

## Sensitivity results

Means across three seeds; min–max is not a confidence interval. Travel-time means concern completed trips only.

| Case | Policy | Bus corridor min | Bus entry queue min | Final-stop ≤3min late % | Not served / all groups | No permitted route |
|---|---|---:|---:|---:|---:|---:|
| moderate | baseline | 9.86 | 0.00 | 100.0 | 0.3 | 0.3 |
| moderate | restricted | 9.85 | 0.00 | 100.0 | 73.7 | 73.7 |
| busy | baseline | 10.08 | 0.02 | 98.4 | 45.7 | 1.7 |
| busy | restricted | 9.91 | 0.00 | 100.0 | 167.7 | 146.3 |
| residents | baseline | 9.83 | 0.00 | 100.0 | 0.7 | 0.7 |
| residents | restricted | 9.88 | 0.01 | 98.4 | 74.0 | 74.0 |

## Effects on every simulated vehicle group

Completed-trip driving means exclude insertion delay and are conditional on completion. Purpose and actual residence are unknown for ordinary traffic. Do not relabel through/background cars as observed workers or shoppers.

| Case | Group | Driving min: baseline → proposal | Unserved requests: baseline → proposal |
|---|---|---:|---:|
| moderate | through | 7.19 → 6.44 | 0.0 → 59.7 |
| moderate | background | 5.35 → 5.42 | 0.0 → 13.7 |
| moderate | crossing | 0.54 → 0.49 | 0.0 → 0.0 |
| moderate | resident | 3.86 → 3.91 | 0.0 → 0.0 |
| moderate | taxi | 7.12 → 7.56 | 0.0 → 0.0 |
| moderate | motorcycle | 7.39 → 7.70 | 0.0 → 0.0 |
| moderate | bicycle | 13.23 → 13.39 | 0.3 → 0.3 |
| moderate | bus | 9.86 → 9.85 | 0.0 → 0.0 |
| busy | through | 9.31 → 7.94 | 27.3 → 128.0 |
| busy | background | 5.66 → 5.77 | 10.7 → 30.0 |
| busy | crossing | 0.69 → 0.52 | 0.0 → 0.0 |
| busy | resident | 4.65 → 4.19 | 0.0 → 0.7 |
| busy | taxi | 9.29 → 7.96 | 1.7 → 2.0 |
| busy | motorcycle | 9.30 → 8.22 | 3.3 → 3.0 |
| busy | bicycle | 14.49 → 13.50 | 2.7 → 4.0 |
| busy | bus | 10.08 → 9.91 | 0.0 → 0.0 |
| residents | through | 7.23 → 6.48 | 0.0 → 59.7 |
| residents | background | 5.39 → 5.42 | 0.0 → 13.7 |
| residents | crossing | 0.57 → 0.49 | 0.0 → 0.0 |
| residents | resident | 4.03 → 4.14 | 0.0 → 0.0 |
| residents | taxi | 7.32 → 7.98 | 0.0 → 0.0 |
| residents | motorcycle | 7.06 → 7.55 | 0.0 → 0.0 |
| residents | bicycle | 13.19 → 13.58 | 0.7 → 0.7 |
| residents | bus | 9.83 → 9.88 | 0.0 → 0.0 |

## Population and transition scenarios

See `population-scenario.md` and the People & transition section of the bilingual proposal for conditional, sourced population accounting. It includes non-resident worker/student, shopper and leisure cohorts under explicit allocation assumptions. It is separate from the corridor SUMO simulation: no full metropolitan OD or mode-choice model has been calibrated. A lower mean need not benefit every cohort, and unmet bus demand prevents an all-request comparison.

## Verdict

The rule is representable and runnable: permitted local trips remain distinct from ordinary through traffic, direct crossings remain routable, and diverted/unserved demand is exposed. This is enough to inspect the policy logic. It does not establish that the restriction should be deployed.

A comparison with unmet demand cannot be read as an equal-served-demand welfare estimate. Some trips have no permitted path within the clipped district, and some baseline trips remain queued. A larger diversion boundary, audited geometry/signals, matched traffic and AVL observations, and resident eligibility data are needed before interpreting benefits as real.

## Potential phases and cost evidence

1. Obtain matching observations, audit the two-lane premise and validate the baseline.
2. Define resident permits, deliveries/essential access and crossing rules; audit diversion roads and crossing capacity.
3. Design a reversible trial: signs, enforcement points, loading alternatives, permit administration and monitoring.
4. Monitor actual bus reliability, resident access and displacement; update the model before permanent changes.

No euro estimate or implementation duration is supported yet. A costed scheme needs dated quantities and rates for surveys/design, signage/markings, enforcement/permits, stop/access works, monitoring and recurring operations.

## Reproduce

Open `costa-cabral.prototype.html` directly for the frozen offline demo, or run `./prototypes/costa-cabral/prototype.sh` from the repository. Captured on branch `prototype/costa-cabral-access`; no production decision is validated.

## Limitations

Guessed signal timings and junction geometry; no field calibration; synthetic OD and compliance; no induced demand/mode choice, pedestrians, freight, parking search or safety appraisal. Buses begin at their first mapped corridor stop, with insertion queues instead of measured upstream lateness. Final-stop completion threshold is illustrative, not an STCP standard. Retain import/SUMO logs in `runs/` for diagnosis.
