# Line 701: full-line exploration and prepared inbound models

## Whole-line reference

The explorer shows each direction independently: 56 stops / 63 trips towards Bolhão; 54 stops / 64 trips towards Codiceira or Ermesinde. A continuous focus range and selected trip are retained for each direction in shared links. Short workings retain their unserved stops; no missing departure is invented.

Timetables refer to 28 October 2026, Europe/Lisbon. Inbound geometry was retrieved on 28 October; outbound geometry was retrieved on 29 October, and its historical applicability to 28 October is not established. The two shapes are independent official references, not one reversed polyline.

Full-line geography and timetables do not extend native traffic simulation. SUMO and 3D remain inbound Areosa–Bolhão; the separate whole-line delay/queue model remains inbound only. Selecting outbound hides these inbound results. The background map needs internet; route geometry and timetable data are exported with the site.

Source bundles: `701-extension/metadata.json`, `701-official/metadata.json`, `701-outbound/metadata.json`; combined explorer reference: `701-line-explorer.json`. Outbound: 3,000 uniquely resolved published references, 456 unserved cells and no unresolved matching. See `docs/research/line-701-outbound.md` in the repository for the derivation.

## Prepared Porto street model

Study date: 2026-10-28. 16 Porto stops, 4.545km inside the CAOP2025 municipality. Areosa ARS3 is the first stop inside Porto; the municipal entry is about 60m before it. Bolhão 0BLRB is the final stop.

## What is known

Current STCP shape, ordered stops and scheduled seconds are frozen with URLs, timestamps and hashes. MPL4 and 0BLRB are designated timing points in Porto. Other calls are intermediate published references. DGT CAOP2025 locates the municipal entry; these are cartographic source positions, not a survey.

Native vehicles start at the mapped municipal entry using an assumed 6s lead before the Areosa reference. There is no official boundary timetable. Reported entry lateness remains measured at Areosa, so it also includes the modeled approach delay. The boundary-crossing edge is excluded from new permission policies to avoid extending restrictions into another municipality.

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
| leg_13 | MPL4 → DCAS2 | 5 | retain general traffic |
| leg_14 | DCAS2 → FTNH2 | 2 | retain general traffic |
| leg_15 | FTNH2 → 0BLRB | 0 | priority / existing priority |

## Simulated Porto street performance

Native SUMO; extended frozen-OSM district, synthetic OD samples including new Marquês–Bolhão demand, fixed 20-second dwell, unverified signals, three seeds and five target 701 trips only. These new outputs supersede the shorter-network results; changed demand/network scope prevents treating differences from the earlier batch as policy gains. The late-entry case adds 180 seconds before municipal entry. Final lateness minus Areosa lateness measures added delay after the first published checkpoint, including intentional timing-point holds. MPL4 and 0BLRB departures wait for their published times. Every unserved request remains visible.

| Case | Variant | Completed 701 journeys / planned | Mean final lateness sec (completed only) | Mean unserved all vehicles |
|---|---|---:|---:|---:|
| moderate | baseline | 15/15 | -41.3 | 0.0 |
| moderate | restricted | 15/15 | -52.2 | 0.0 |
| moderate | all_priority | 15/15 | -60.9 | 41.7 |
| busy | baseline | 15/15 | -49.9 | 1.0 |
| busy | restricted | 12/15 | -63.8 | 31.7 |
| busy | all_priority | 15/15 | -30.8 | 68.0 |
| busy | leg_01 | 15/15 | -26.3 | 1.0 |
| busy | leg_02 | 15/15 | -48.5 | 1.0 |
| busy | leg_03 | 15/15 | -38.4 | 1.0 |
| busy | leg_04 | 15/15 | -41.7 | 1.0 |
| busy | leg_05 | 15/15 | -48.8 | 1.0 |
| busy | leg_06 | 15/15 | -48.8 | 1.0 |
| busy | leg_07 | 15/15 | -55.5 | 1.0 |
| busy | leg_08 | 15/15 | -49.9 | 1.0 |
| busy | leg_09 | 15/15 | -40.0 | 1.0 |
| busy | leg_10 | 15/15 | -49.9 | 1.0 |
| busy | leg_11 | 15/15 | -46.6 | 1.0 |
| busy | leg_12 | 15/15 | -53.2 | 1.0 |
| busy | leg_13 | 15/15 | -55.3 | 60.3 |
| busy | leg_14 | 15/15 | -30.3 | 18.0 |
| busy | leg_15 | 15/15 | -39.2 | 1.0 |
| late | baseline | 15/15 | 111.4 | 1.0 |
| late | restricted | 15/15 | 141.9 | 1.0 |
| late | all_priority | 15/15 | 120.0 | 68.0 |

### Native punctuality and spacing checks

These counts cover the five requested native journeys across three seeds. Missing timing-point calls cannot pass the strict check. Arrival-spacing events compare the actual consecutive pair with half its published-time separation; the count is withheld when bus journeys are incomplete. A native timetable pass does not establish sufficient passenger capacity or practical access.

| Case | Package | Late timing-point arrivals / planned | Missing calls | Short-gap events | Strict check |
|---|---|---:|---:|---:|---|
| moderate | baseline | 9/30 | 0 | 0 | fail |
| moderate | restricted | 6/30 | 0 | 0 | fail |
| moderate | all_priority | 4/30 | 0 | 0 | fail |
| busy | baseline | 6/30 | 0 | 0 | fail |
| busy | restricted | 1/30 | 6 | unavailable | fail |
| busy | all_priority | 6/30 | 0 | 0 | fail |
| late | baseline | 29/30 | 0 | 0 | fail |
| late | restricted | 30/30 | 0 | 0 | fail |
| late | all_priority | 28/30 | 0 | 0 | fail |

## Whole-line bunching and cascade checks

A separate operational model covers all 56 stops, 63 inbound workings and 3,024 published calls: 39 start at Codiceira, 24 at Ermesinde. Unserved upstream stops on short workings stay null. All intermediate-reference associations are derived from unique timetable matchings, not raw per-stop trip IDs.

This model uses fluid passenger arrivals, capacity limits, boarding/alighting dwell, single-berth queues and timing-point/headway holding. Running budgets and recovery are assumptions. It simulates one direction with independent vehicles per trip; road traffic outside Porto, other routes, outbound service and shared vehicle rotations are absent. The strict goal is zero late timing-point arrivals, zero early timing-point departures, no gap below half the published spacing, and no passengers left behind. Meeting that goal in a what-if model is not a real-world guarantee.

Default no-shock versus injected-delay scenario:

```json
{
  "reference": {
    "trips": 63,
    "calls": 3024,
    "timing_calls": 354,
    "late_timing_calls": 158,
    "max_lateness": 1102.6526333726652,
    "early_timing_departures": 0,
    "short_gap_events": 29,
    "short_gap_trip_pairs": 3,
    "passenger_arrivals": 15539.70833333333,
    "boardings": 15491.009629818524,
    "passengers_left": 48.69870351481109,
    "capacity_denied_calls": 160,
    "passenger_balance_error": -4.32720526077901e-12,
    "max_load": 70,
    "max_queue": 14.786139264149277,
    "runtime_budget_floor_events": 536,
    "target_met": false
  },
  "scenario": {
    "trips": 63,
    "calls": 3024,
    "timing_calls": 354,
    "late_timing_calls": 163,
    "max_lateness": 1102.6526333726652,
    "early_timing_departures": 0,
    "short_gap_events": 39,
    "short_gap_trip_pairs": 4,
    "passenger_arrivals": 15539.70833333333,
    "boardings": 15491.009629818524,
    "passengers_left": 48.69870351481109,
    "capacity_denied_calls": 160,
    "passenger_balance_error": -4.32720526077901e-12,
    "max_load": 70,
    "max_queue": 14.786139264149277,
    "runtime_budget_floor_events": 536,
    "target_met": false
  },
  "other_trips_changed": 2,
  "other_trips_later": 1
}
```

Reduce neither journey counts nor passenger demand to manufacture a punctuality gain. Compare the same demand without the injected delay; secondary changes and short-gap events expose passenger–dwell feedback, while remaining queues expose capacity failures. A late bus can collect more passengers and slow further; a following bus can collect fewer and catch up. Native SUMO separately retains vehicle following and queue spillback within the Porto road network.

## Interpretation and next steps

Use the passage-window profile to identify where deviation grows, then collect repeated complete trips before attributing causes. Missing Areosa/Bolhão coverage prevents claiming full-section observed punctuality. A single evening trajectory is an investigative lead, not a causal diagnosis.

Compare the connectivity-screened package, unrestricted baseline and individual-leg tests. Individual effects must not be added together. Permission-only policies retain identical network geometry and signal programs; a no-change leg is an exact neutral control. Do not rank a policy on faster completed trips when bus or other requests remain unserved.

Obtain matched full-line AVL and door-open events, boarding/load counts, actual recovery and turnaround times, controller phases, other-line interactions and vehicle/block circulation. Audit lane directions, widths, turns and property/loading access. Calibrate both layers before optimizing for real punctuality or choosing an implementation.

## Code-first controls

`./prototypes/line-701/pilot.sh` rebuilds the route pilot. Export a draft policy JSON from the website, then pass `--scenario /absolute/path/policy.json` to the runner. The static website does not execute new SUMO simulations. The collector and observation importer preserve timestamp/source distinctions.

## Primary sources

- [Official line 701](https://stcp.pt/pt/linhas/701)
- [STCP route stops API](https://stcp.pt/api/route/701/stops/direction?direction_id=1)
- [DGT CAOP2025 Porto municipality](https://ogcapi.dgterritorio.gov.pt/collections/municipios/items/1312?f=json)
- [Porto Digital public bus broker](https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType%3D%3Dbus&limit=1000)
- Source/API/hash detail: `701-source-facts.json`. Native per-run data: `701-experiments.json`. Observation windows: `701-observations.json`.
