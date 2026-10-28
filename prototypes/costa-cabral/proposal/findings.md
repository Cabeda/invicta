# Costa Cabral prototype: experiment findings

Question: does a two-direction corridor restriction preserve local access and junction crossings, and how does it behave under assumed demand?

**Throwaway, uncalibrated experiment. These are simulator outcomes, not a forecast or observed Porto performance.**

## Goal and local needs

Primary goal: help buses meet their published schedules while catering to residents, shoppers, businesses and everyday services. Assess early departures as well as late arrivals; practical local access is an explicit requirement.

The current final-stop arrival check (no more than three minutes late) is illustrative. It does not assess early departures or whole-route punctuality. Shopper, visitor and service access are not yet represented; the resident permit remains a local-origin/destination proxy. Faster completed bus trips alone do not establish success.

## Inputs and decisions

- SUMO 1.28.0; street map and source hashes in `data/manifest.json`.
- Access: bus, taxi, bicycle, motorcycle, synthetic local resident permit; ordinary cars can directly cross junctions. No longitudinal short-link exception.
- Local permits are assigned to origins/destinations on corridor edges; actual residents are not identified.
- Existing mapped directions and bus contraflow preserved; eight directed stretches normalized to one lane per direction for the two-lane premise.
- 21 of 21 requested GTFS trips mapped; service date 2 September 2026 (holiday weekday), not a current feed.
- Traffic OD, mode counts, 20-second dwell and generated signals are assumptions. No observed passenger loads or current calibration.
- Same synthetic requested trips in each paired policy run. All no-route and unfinished journeys counted. Teleporting disabled.

## Sensitivity results

Means across three seeds; min–max is not a confidence interval. Travel-time means concern completed trips only.

| Case | Policy | Bus corridor min | Bus entry queue min | Final-stop ≤3min late % | Not served / all groups | No permitted route |
|---|---|---:|---:|---:|---:|---:|
| moderate | baseline | 13.24 | 6.32 | 61.9 | 243.3 | 0.7 |
| moderate | restricted | 9.85 | 0.01 | 100.0 | 74.0 | 74.0 |
| busy | baseline | 11.53 | 3.37 | 68.3 | 699.7 | 1.3 |
| busy | restricted | 9.88 | 0.00 | 100.0 | 121.3 | 121.3 |
| residents | baseline | 13.49 | 3.54 | 66.7 | 368.0 | 0.7 |
| residents | restricted | 10.05 | 0.00 | 98.4 | 74.0 | 74.0 |

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
