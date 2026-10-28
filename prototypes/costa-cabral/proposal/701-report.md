# Line 701: Areosa → Marquês, inbound towards Bolhão

Study date: 2026-10-28. Current official route/service snapshot; 13 stops, approximately 3.14km. Ends at MPL4 after the restored MPL7 stop.

## What is known

Current STCP route shape, ordered stops and stop schedule seconds are frozen with source URLs, timestamps and hashes. Only MPL4 is a designated timing point within this section. Other stop times are published non-timepoint references. This section does not model the entire 701 line.

## Observed sample

A bounded evening collection has 48 unique accepted timestamped positions from 59 polls. Duplicate records are excluded. GPS-derived passage brackets are not door-open arrivals, and this short evening sample does not calibrate morning traffic.

Trip: 701_0_2|327|D1|T4|N14

| Stop | Scheduled-reference lateness window (min) |
|---|---:|
| STJ3 | 6.77 … 7.77 |
| BRRS2 | 6.45 … 7.38 |
| CF2 | 6.32 … 7.35 |
| LW2 | 6.18 … 7.35 |
| SVT4 | 6.75 … 7.55 |
| PLIM2 | 6.03 … 6.97 |
| COMB4 | 9.25 … 10.33 |
| LIMA2 | 7.77 … 8.85 |
| MPL7 | 8.45 … 9.43 |
| MPL4 | 8.68 … 9.63 |

Trip: 701_0_2|327|D1|T6|N11

| Stop | Scheduled-reference lateness window (min) |
|---|---:|
| ARS3 | 11.82 … 12.80 |

## Where general traffic is retained in the candidate

This is a structural screen using generated side-road connector/ordinary-traffic OD pairs, not measured local demand or a legal conclusion. Driveways, loading, emergency access, signage and pedestrian access require field review. Existing exclusive bus lanes are retained; where a new lane is reserved on a multi-lane road, other lanes remain general traffic. Opposite-direction road edges are untouched.

| Leg | Section | Newly unreachable generated OD pairs if priority is applied | Decision in candidate |
|---|---|---:|---|
| leg_01 | ARS3 → AA2 | 1 | retain general traffic |
| leg_02 | AA2 → ACO2 | 2 | retain general traffic |
| leg_03 | ACO2 → STJ3 | 0 | priority / existing priority |
| leg_04 | STJ3 → BRRS2 | 0 | priority / existing priority |
| leg_05 | BRRS2 → CF2 | 0 | priority / existing priority |
| leg_06 | CF2 → LW2 | 0 | priority / existing priority |
| leg_07 | LW2 → SVT4 | 0 | priority / existing priority |
| leg_08 | SVT4 → PLIM2 | 0 | priority / existing priority |
| leg_09 | PLIM2 → COMB4 | 0 | priority / existing priority |
| leg_10 | COMB4 → LIMA2 | 0 | priority / existing priority |
| leg_11 | LIMA2 → MPL7 | 0 | priority / existing priority |
| leg_12 | MPL7 → MPL4 | 0 | priority / existing priority |

## Simulated section performance

Native SUMO; current official timetable; synthetic traffic, fixed 20-second dwell, guessed signals, three seeds, five target 701 trips only. The late-entry case adds an assumed 180 seconds before Areosa. Additional delay in section is final lateness minus actual simulated entry lateness. Intermediate non-timepoint references are not used for holding. MPL4 departures are held to its published time. All unserved requests remain in the accounting.

| Case | Variant | Completed 701 journeys / planned | Mean final lateness sec (completed only) | Mean unserved all vehicles |
|---|---|---:|---:|---:|
| moderate | baseline | 15/15 | -109.0 | 0.3 |
| moderate | restricted | 15/15 | -90.5 | 0.3 |
| moderate | all_priority | 15/15 | -88.3 | 0.3 |
| busy | baseline | 15/15 | -41.3 | 1.7 |
| busy | restricted | 15/15 | -81.3 | 1.7 |
| busy | all_priority | 15/15 | -89.7 | 1.7 |
| busy | leg_01 | 14/15 | -73.7 | 30.0 |
| busy | leg_02 | 15/15 | -85.7 | 1.7 |
| busy | leg_03 | 15/15 | -64.6 | 1.7 |
| busy | leg_04 | 15/15 | -80.0 | 1.7 |
| busy | leg_05 | 15/15 | -65.2 | 1.7 |
| busy | leg_06 | 15/15 | -65.2 | 1.7 |
| busy | leg_07 | 10/15 | -32.3 | 256.7 |
| busy | leg_08 | 15/15 | -41.3 | 1.7 |
| busy | leg_09 | 15/15 | -88.9 | 1.7 |
| busy | leg_10 | 15/15 | -41.3 | 1.7 |
| busy | leg_11 | 15/15 | -83.5 | 1.7 |
| busy | leg_12 | 15/15 | -73.7 | 1.7 |
| late | baseline | 15/15 | 126.1 | 1.7 |
| late | restricted | 15/15 | 94.2 | 1.7 |
| late | all_priority | 15/15 | 98.9 | 1.7 |

## Interpretation and next steps

Use the actual passage-window profile to identify where deviation from the published reference grows, then collect repeated complete trips before attributing causes. Missing Areosa coverage means inherited lateness and full-section added observed delay cannot be separated for that trip. A single-trip evening increase is a lead for investigation, not proof that car traffic, signals or boarding caused it.

Compare an access-preserving package, unrestricted baseline and individual-leg tests. Individual effects must not be added together. Permission-only policies retain identical network geometry and signal programs; a no-change leg is an exact neutral control. Do not rank a policy on faster completed trips when bus or other requests remain unserved.

Map-match and audit the actual bus turns, widths, stop locations, signal phases and loading/property access; obtain a matched AVL/door-open/history dataset and target-route passenger loads. Include other bus lines in subsequent network validation. Extend to the full 701 line after this direction and section are validated.

## Code-first controls

`./prototypes/line-701/pilot.sh` rebuilds the route pilot. Export a draft policy JSON from the website, then pass `--scenario /absolute/path/policy.json` to the runner. The static website does not execute new SUMO simulations. The collector and observation importer preserve timestamp/source distinctions.

## Primary sources

- [Official line 701](https://stcp.pt/pt/linhas/701)
- [STCP route stops API](https://stcp.pt/api/route/701/stops/direction?direction_id=1)
- [Porto Digital public bus broker](https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType%3D%3Dbus&limit=1000)
- Source/API/hash detail: `701-source-facts.json`. Native per-run data: `701-experiments.json`. Observation windows: `701-observations.json`.
