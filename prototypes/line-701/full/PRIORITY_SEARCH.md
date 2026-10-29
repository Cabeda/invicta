# Getting every 701 trip onto its timetable

No tested package meets every published checkpoint yet. The target is unchanged: all 127 scheduled trips in both directions, including short workings and service after midnight. Departures at origins and designated intermediate timing points must match the published second; terminal arrivals must be no later than published. Missing trips fail. Intermediate reference times are not promoted into exact timing points.

The new experiments are separate from the site's existing animated replay. They do not establish present-day STCP punctuality or a field-validated design. The frozen timetable refers to 28 October 2026. The [complete trial ledger](priority-search.json) includes successful executions, failed timetable checks, superseded imports, optimistic diagnostics and one corrected controller API failure. Native bus calls and trip outputs are available as gzip files through each trial's `evidence` entries. No failed trip is removed from a denominator.

## What the iterations have established

### Correct the route before attributing delay to street policy

A fresh check of STCP's date-resolved API confirms the frozen first Codiceira 05:25 → Ermesinde 05:33 interval. The archived municipal GTFS feed expires in September and cannot replace the current operator reference. The newer 29 October service retains these first checkpoint times; this study still uses the complete 28 October service.

Two native matching filters were producing side-street loops absent from the operator's official shape. At Alfena, a 16 m minimum excluded the correct 13.86 m São Vicente road fragment and placed the stop 49.5 m away on Rua Coroa. After correcting that, a 0.5 m minimum for non-stop shape anchors still excluded 0.2 m straight-road fragments and forced a spur onto Rua da Várzea. The matcher now accepts a 12 m study-bus footprint on stop edges and positive short fragments for shape anchors. Both defects have a regression check using the actual imported junction geometry. Actual stop footprints remain unsurveyed.

The original empty, signals-off diagnostic missed Ermesinde by 55 s. Correcting only Alfena reduced that to 37 s; the intermediate version-4 passenger/walking control still completed all 127 trips but had 91 on-time terminal arrivals and 106 late timing checks. These are model corrections, not infrastructure benefits. All version-3 and version-4 rows are retained as superseded and excluded from the current public comparison. The detailed primary-source and matching audit is in [the route and public-data audit](https://github.com/Cabeda/invicta/blob/main/docs/research/701-first-checkpoint-audit.md).

Version 5 retains all 127 workings and 714 designated timing checks. Its optimistic empty diagnostic completes every trip and reaches all terminals on time, but misses the first Ermesinde departure by **19 seconds**. Request stops, faster boarding, bounded signal priority and idealised off-line holding with passengers and walking requests—but no ordinary vehicles—complete all 127 workings, with **93 on-time terminal arrivals and 97 late timing checks**. This still fails the target.

The two new full-traffic executions use the corrected route match, seed 17, the same 26,035 physical ordinary-vehicle requests, 30,759 synthetic passenger requests and 46,073 synthetic walking requests. Both use A* for dynamic native routing, retaining the same 60-second rerouting period; this is an execution choice shared by the pair, not a street intervention. Their OD mappings remain identical, with 960 endpoint/class mappings, a maximum displacement of 29.372 m and zero unroutable requests. The package changes 87 lane permissions and preserves all pedestrian permissions.

| Current version 5 · full traffic · seed 17 | On-time starts | On-time terminal arrivals | Finished trips | Missing timing checks | Late timing checks | Unserved ordinary requests | Served passenger requests |
|---|---:|---:|---:|---:|---:|---:|---:|
| Compulsory 20-second stops, generated signals | 126/127 | 3/127 | 119/127 | 32/714 | 388/714 | 40/26,035 | 20,738/30,759 |
| Screened lanes + request stops + faster boarding + signal priority + off-line holding | 127/127 | 62/127 | 85/127 | 114/714 | 103/714 | 73/26,035 | 15,595/30,759 |

**The current package is rejected.** More terminal arrivals are on time among the trips that finish, but 42 trips remain unfinished versus eight in its baseline, fewer passenger requests are served, and more ordinary vehicle requests remain unserved. This is not an overall improvement and cannot be ranked as the smallest successful proposal. Both cases complete all walking requests and record no collisions; that is not a safety validation.

The complete ledger now preserves **34 full-service native executions**, plus the failed controller attempt. Network/route identity and source/output hashes keep earlier models distinct. Version 5 removes the two known Alfena spurs but still has maximum stop snaps of **26.96 m inbound and 46.796 m outbound**. Actual stop footprints, controller assignments, demand and vehicle blocks remain unvalidated. No calibrated moderate/busy/late multi-seed matrix or verified winner is claimed.

### Earlier experiments retained for audit

The previous model imposed a 20-second stop on every bus at every stop, even without a passenger request. In the first Codiceira–Ermesinde interval, 20 intervening stops alone consume 400 seconds of an eight-minute allowance. An optimistic road-speed calculation on that older match adds about 359 seconds before acceleration, turns or signals. That assumption cannot meet this interval; adding a lane cannot fix it.

The new street-detail model imports **875 OSM crossings**, walking areas and **237 generated signal programs** across the regional network. Counts are regional, not all on the 701. Guessed sidewalks and generated timings remain assumptions. An unverified 50 km/h study cap applies to non-motorway/non-trunk imported lanes, retaining lower speeds; individual posted limits remain unverified. This corrects imports that gave Costa Cabral and Marquês 100 km/h defaults. The correction applies to both sides of each comparison. It is not a proposed street intervention.

The pedestrian import also split a junction previously merged by SUMO. Version 3 restored the existing bus-only route-continuity exception at the actual junction, using the unambiguous fragment of the same OSM way. Version 2 omitted it. Version 3 still had the route-matching defects described above. Differences between network versions are not policy benefits.

Within the superseded version 3, using the same 30,759 synthetic passenger requests and 46,073 walking requests, seed 17:

| Package · no ordinary traffic | On-time origin departures | On-time terminal arrivals | Late timing-point checks |
|---|---:|---:|---:|
| Compulsory 20-second stops | 126/127 | 32/127 | 320/714 |
| Request stops + faster boarding | 127/127 | 90/127 | 107/714 |
| Request stops + boarding + signal priority | 127/127 | 92/127 | 102/714 |
| Above + off-line timetable holding | 127/127 | 94/127 | 100/714 |
| Larger, 110-person buses with faster boarding | 127/127 | 91/127 | 106/714 |

These are deliberately labelled **bus-only controls**, with synthetic passenger and walking demand. They are not forecasts of benefits in existing traffic. The holding and larger-bus assumptions require space and vehicle/accessibility checks. Increasing capacity improved served passenger requests from around 22,500 to 27,102 of 30,759, but did not solve punctuality. Unserved passengers remain visible in the ledger; capacity and the offered service window both require investigation. Trip and person means cannot describe requests that never finish.

The flat passenger rate of 0.25 requests per minute per directional stop is an **unmeasured stress assumption**, not an estimate of line 701's actual ridership. STCP's [2025 annual report](https://stcp.pt/uploads/stcp-institucional/relatorio-e-contas/rc2025.pdf) gives network-wide totals of 71.2 million bus passengers and 15% occupancy; those aggregates cannot calibrate an individual line or be divided evenly between routes. Stop-by-stop demand by time of day and actual journey destinations remain necessary before drawing conclusions about fleet size or capacity.

The earlier version-2 ordinary-traffic pair is **invalidated and excluded from proposal comparisons**. Both runs left 8,581 of the 26,035 requests unroutable because they referenced 66 road-edge IDs lost when crossings split the network. The lane package also added pedestrian permission on 88 carriageway lanes. Its apparent 5-to-86 terminal-punctuality improvement cannot support a proposal. The original outputs remain in the ledger with these defects marked explicitly.

The version-3 pair corrected the ordinary-demand mapping and preserves the same physical origins and destinations across both policies. All 26,035 ordinary vehicle requests are submitted to SUMO; 960 endpoint/class mappings have a maximum displacement of 29.372 metres. Candidate connectivity is checked again after lane restrictions, with general traffic retained where needed. The candidate changes 87 lane permissions and changes **zero pedestrian permissions**. Both full service days ran from 05:00 through 27:35, with the same 127 bus workings, passenger requests and walking requests. Its bus path still had the matching defects above, so this pair is now superseded.

| Historical full-traffic experiment · superseded geometry · seed 17 | On-time starts | On-time terminal arrivals | Finished trips | Missing timing checks | Late timing checks | Unserved ordinary requests | Served passenger requests |
|---|---:|---:|---:|---:|---:|---:|---:|
| Compulsory 20-second stops, generated signals | 126/127 | 0/127 | 85/127 | 114/714 | 340/714 | 129/26,035 | 15,990/30,759 |
| Screened lanes + request stops + faster boarding + signal priority + off-line holding | 127/127 | 59/127 | 85/127 | 114/714 | 107/714 | 65/26,035 | 15,610/30,759 |

**This historical combined package was rejected.** It improved punctuality among some trips and reduced unserved ordinary requests within that model, but 42 bus workings remained unfinished in both policies and fewer passenger requests were served. Missing and late timing checks both failed the target. No early departures at designated checkpoints or collision records were recorded. These are simulated outcomes under the declared stress assumptions, not a measurement of existing STCP service or a valid estimate of the corrected route's performance.

The unfinished workings comprise 18 inbound and 24 outbound trips. Their last recorded stops cluster around Viela S. Vicente, Cabeda, Reguengo, Ermida, Soutinho and S.ra da Paz; native logs show prolonged waiting. The cause still needs a local network/control audit: persistent queues can reflect imported junction/stop geometry, generated control logic, demand assumptions or physical conflicts. It is not established as an actual street problem. Junction coordination, keeping intersections clear and boarding/holding layouts should be investigated before wider restrictions are proposed. A lane package cannot be called successful while these trips remain unfinished.

Observed starts retain their observed status even when a trip later fails to finish. Grading schema 2 corrects the earlier evaluator's conflation of unfinished trips with missing observations; unfinished trips still cannot pass the overall goal. Original execution metadata and output hashes are preserved unchanged, and all displayed counts are recomputed from native calls.

The version-3 optimistic diagnostic—no ordinary traffic, no passengers, zero dwell, signals switched off and idealised off-line holding—got all 127 terminal arrivals on time but missed the first Ermesinde departure checkpoint by 55 seconds. The two subsequent matching corrections reduced this miss to 19 seconds in version 5. **Switching signals off is not a proposal.** This is a warning about model/timetable fit, not proof that STCP's actual timetable is impossible. Remaining vehicle dynamics, stop footprints, road geometry and signage require validation.

## Beyond bus lanes

The native controller tests green extension of at most ten seconds per phase. A second option can shorten a conflicting vehicle green only after its configured minimum and at least 15 seconds. It retains the original phase order, yellow and all-red phases; it does not jump directly from a conflicting green to a bus green. The default never shortens a pedestrian green. A separate sensitivity permits shortening only after a conservative width/0.8 m/s plus five-second minimum and no detected occupancy of the controlled crossing. These rules exercise a hypothesis; they are not approved roadside controller settings or a substitute for validated conflict/clearance plans. Each action is logged.

Request stops use native passenger waiting, boarding, alighting and finite vehicle capacity. Tested door/boarding times are assumptions, not measured STCP performance. Holding outside the running lane is represented using SUMO parking stops; it is an idealised bay assumption, without surveyed bay dimensions, approach manoeuvres or land availability. It cannot be counted as a free operational change. Dynamic rerouting changes ordinary vehicles' paths without deleting requested journeys.

The injected three-minute late origin in the separate resilience case cannot be fixed after the bus has already missed its departure. A standby vehicle and driver would need to be explicitly available at that origin. The runner records that resource if enabled; this iteration has not validated the busy/late multi-seed matrix or actual vehicle blocks. No such case is silently removed or reported as passing.

## Actual open street data

Porto publishes [signal equipment locations](https://dadosabertos.cm-porto.pt/dataset/sistema-de-gestao-de-trafego-semaforos) and an [LED crossing inventory](https://dadosabertos.cm-porto.pt/dataset/sinalizacao-led-em-travessias-de-peoes), both CCZero. The site map can show **139 equipment points and two LED crossing points within 40 metres of either official shape**. These are location evidence: many signal heads may belong to one junction; LED crossings are a small subset of all crossings. They are not 139 controllers, live signal states or complete crossing geometries.

Public Maia and Valongo inventories also exist, but the inspected status/survey attributes date to 2020 and 2009 and reuse rights remain unverified. No current public phase plans, cycles, offsets, pedestrian clearances or implemented 701 priority logic were verified for the line. See the repository research note [the street-asset source audit](https://github.com/Cabeda/invicta/blob/main/docs/research/701-signals-crossings-open-data.md) for endpoints, dates, fields and acquisition limits. The raw Porto CCZero exports and hashes are retained in `data/street-assets-sources/`; source URLs are embedded in the public GeoJSON.

Valongo also exposes a dated vertical-sign inventory. Nine candidates lie within 40 m of the first Codiceira–Ermesinde section, including maximum-30/40 and zone-50 signs. The records date to 2009 and do not establish current facing direction or extent. They do not justify raising the model's cap to force a timetable pass; missing or stale speed tags still need validation.

The follow-up remains public-data-only. Current STCP vehicle and stop-ETA endpoints support bounded future collection, but predictions are not observed arrivals and sampled per-vehicle timestamps were null. The five sampled 701 records in Porto's public broker were about 13 hours old. Independent STCP Watch offers history and CSV exports, but its sampled quality/trip matching does not establish validated per-trip timing history. No public 701 boarding/alighting profile was found in this bounded audit. Existing short evening GPS passage brackets do not calibrate an entire service day. Acquisition details and source limits are recorded in [the route and public-data audit](https://github.com/Cabeda/invicta/blob/main/docs/research/701-first-checkpoint-audit.md).

## A practical path to a defensible proposal

1. **Resolve the baseline fit.** Survey the first Codiceira–Ermesinde interval and flagged stop positions. Confirm posted speeds, current turns, stop footprints and timetable meaning with STCP. Obtain actual timing/priority plans, pedestrian clearance and historical passage/boarding observations. Keep the published timetable frozen while checking it.
2. **Test the smallest reversible package.** Conditional signal priority, faster accessible boarding, enforcement of existing priority and dispatch/holding changes should be tested before reserving long stretches of road. Compare identical passenger, pedestrian and ordinary traffic requests. Check residents, shops, deliveries, crossing waits and queues on adjacent streets.
3. **Add targeted infrastructure only for remaining failures.** Queue jumps, short priority lanes, stop/holding layouts and extra vehicle capacity need designs and an access survey. A missed origin requires dispatch resilience as well as road priority. Do not rank an infeasible package as the cheapest successful solution.
4. **Qualify before scaling.** Run full days in both directions for moderate, busy and late-origin conditions and multiple seeds. Require all timetable checkpoints, no missing trips, passenger-capacity checks, no extra unserved ordinary demand and reviewed pedestrian/access constraints. Observe a reversible pilot before extending it.

Costs are not yet estimated. The cost schedule should distinguish controller/detection integration and communications, accessible stop works and land, lane/signage/enforcement work, recurring maintenance, vehicle procurement and driver hours. Each needs a quantity, responsible authority, supplier estimate, operational dependency and uncertainty range. This evidence does not justify invented euro figures or a construction sequence before controller ownership and physical space are known.

## Reproduce and inspect

Install `eclipse-sumo==1.28.0`, `libsumo==1.28.0` and the project's pinned Python dependencies. From the repository root:

```sh
.venv/bin/python prototypes/line-701/full/priority_model.py --output .cache/701-priority-new
.venv/bin/python prototypes/line-701/full/priority_search.py \
  --model .cache/701-priority-new --output .cache/701-priority-runs \
  --config prototypes/line-701/full/priority-configs/v5-moderate-priority-mapped-s17.json
.venv/bin/python -m unittest discover -s prototypes/line-701/full -p test_priority_search.py
```

Use a fresh output directory or trial ID, including after failure: native trial folders are immutable. Model identity includes both network and route-reference hashes; a rematched path cannot inherit an earlier model's identity. Older model/diagnostic rows are retained to explain the search, not to qualify a new package. Native XML outputs, compressed payloads, physical endpoint mappings and controller events have separate hashes; the acceptance check re-evaluates every stored timetable result from frozen native output and checks original completion bindings when available. Mapped-traffic pairs also archive native input files. Version-5 runs save an immutable native state at 27:34:59, including random-generator and transportable states, for investigating unfinished demand. This is diagnostic evidence, not a new animation. Earlier controls without original completion digests are marked `first_archive_only`.

SUMO primary references: [public-transport stops, schedules and passengers](https://sumo.dlr.de/docs/Simulation/Public_Transport.html), [signal programs](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html), [pedestrian crossings](https://sumo.dlr.de/docs/Simulation/Pedestrians.html). OSM data © OpenStreetMap contributors, ODbL; Porto inventories CCZero. Program timings, passenger/walking demand and intervention geometry are assumed.
