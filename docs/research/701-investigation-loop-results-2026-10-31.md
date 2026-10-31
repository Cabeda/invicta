# 701: repeatable investigation and current timetable result

The combined workload still does **not** meet the timetable target. The useful improvement is a source-bound loop that finds where delay is created, reproduces model defects cheaply, retains rejected changes and returns to full-service tests. No street proposal is qualified and no minimum infrastructure package can yet be claimed.

The frozen official reference is 28 October 2026: 127 scheduled services in both directions, 6,024 served calls and 714 designated timing checks. The project operational criterion is no early departures and at most 60 seconds late; the strict exact-second result is retained separately. This is not an STCP contractual acceptance standard. Ordinary traffic, passenger arrivals, walking demand and signal programmes remain uncalibrated assumptions.

## Verified results

| Native case | Services complete | Late checks >60 s | Strict late checks | Ordinary requests unserved | Passenger requests served | Walking requests served | Collision records |
|---|---:|---:|---:|---:|---:|---:|---:|
| V13 compound Areosa, traffic only | 127/127 | 0 | 15 | 0/4,107 | 0/0 | 0/0 | 17 |
| V14 protected Areosa turn, traffic only | 127/127 | 0 | 10 | 0/4,107 | 0/0 | 0/0 | 0 |
| V14 combined passenger/traffic control | 127/127 | 21 | 49 | 0/4,107 | 6,172/6,172 | 3,042/3,042 | 0 |
| V15 all-door assumption + bounded bus signal priority, combined | 127/127 | 10 | 28 | 0/4,107 | 6,172/6,172 | 3,042/3,042 | 1 |

In the combined V14 control, all 127 services leave their origins within the operational criterion and 115 finish within it. The 21 late checks include intermediate and terminal events; they are not 21 separate unfinished bus journeys. All vehicle and person requests finish, but the timetable goal remains unmet.

“10% busy” selects a stable nested fraction of the synthetic regional demand catalogue. It is **not** a measured percentage of actual Porto congestion. The faster all-door/prepaid boarding assumption is 0.6 seconds per boarding passenger versus the control's 1.8 seconds. It remains an optimistic operating scenario, not measured STCP performance. No passengers are deleted. The V15 collision is between two buses near Largo da Codiceira; a different passenger-only V15 case records a pedestrian collision near S. Gemil. Both are retained and disqualifying.

V14 empty-network controls on seeds 17, 29 and 41 complete all services with zero operational late checks, no early departures and no collisions. Strict late checks are 5, 4 and 5. Traffic-bearing V14 qualification is still single-seed evidence; this is not a robust field prediction.

Machine-readable counts and exact source identities: [summary](701-investigation-loop-2026-10-31/summary.json), [native archive](701-investigation-loop-2026-10-31/study.json). The archive retains 21 full native trials and 254 recorded or failed local native cases. Rejected readiness attempts, probes and logs are supplementary evidence. The numeric rows are regraded from frozen native stop and trip outputs during archiving.

## Areosa: a stronger regression changed the diagnosis

The earlier three-actor detector case passed, but the regional ordinary queue remained. Zero-step inspection found a resident vehicle on the 0.20-metre road `1304910030`, needing a lane change into its only continuing lane. The short storage and other actors prevented it. A nine-actor regional reduction was reduced to five load-bearing actors; removing any one clears the resident. The detector-gap-only correction still leaves two of those five unfinished.

A supported compound-junction rebuild contracts only the interior 3.92-metre and 0.20-metre normal roads. It starts from the compatible frozen native import and preserves all other normal movements. The scope audit finds no changes outside the explicitly reviewed junction/fringe and no changed normal-lane permissions or speeds. The tracked builder reproduces the exact V13 network hash. Inferred local signal programmes are regenerated too, so this result cannot be attributed to geometry alone.

That first rebuild clears the queue but creates 17 regional collision records. A two-actor car/bus case reproduces the conflict on the unchanged full network. The smaller regression also reproduces it for 20 of 41 controlled arrival offsets; either single actor completes. Reprocessing a reduced network changes some other internal movements, so its whole focus is **not** claimed identical to the regional network. The three collision-path lane shapes/lengths match, and the full-network pair independently reproduces the failure.

Changing width assumptions, waiting positions or all-red duration did not remove the reduced conflict. Separating the permissive turn into an explicitly protected phase clears all 41 local offsets and the five-/nine-actor queue cases. The V14 full traffic day then clears every request with no collision records. This is an inferred signal-design/model experiment, not a municipal timing plan or an established street benefit.

[Native regression inputs and provenance](../../prototypes/line-701/full/diagnostics/areosa-junction/) and the public `/701-investigation/` gallery show the blocked case, initial compound case, introduced collision and protected-turn experiment. Each 2D/3D view uses its own verified native recording, not a reused older regional animation.

## Codiceira: local success rejected by the complete model

The V15 combined collision is reduced to two 12-metre buses on the original regional network. The observed approach lane matters: an initial drive-through reduction did not reproduce the failure. With a matching lane assignment, the pair collides; either single-bus control clears. This distinction is retained in the probe logs rather than silently replacing the initial negative test.

Increasing the minor-road time gap from 1 to 2 or 3 seconds, disabling junction advance, and removing minor-link dawdling did not eliminate that pair collision. Those are explicitly uncertain driver-parameter sensitivities, never calibration or a street proposal. Joining two adjacent priority junctions and contracting two 0.20-metre normal roads clears 31 controlled offsets with unchanged driver parameters.

The complete audit rejects that candidate: the changed boundary leaves only **10.84 metres** on the road containing the outbound Largo da Codiceira stop, too short for the 12-metre study bus. An initial reference update also exposed a short-working canonical-index bug. `route_topology.contract_reference` now preserves those indices without changing the timetable; after that correction the berth finding remains. V16/V17 are retained as rejected diagnostics. No passenger/traffic qualification is run through this blocker.

Next action: inspect the official/OSM platform and direction, rematch a physically valid berth with source evidence, and review the junction boundary before another regional trial. Do not move the stop merely to make an audit pass. Inferred 1.60-metre lanes near Areosa are another source/import review item; the frozen OSM ways lack an explicit width. That does not by itself establish that OSM should be edited.

## Delay created versus delay inherited

The passenger-only all-door V15 case leaves six operational late checks: fresh delay on several Areosa–Marquês intervals and on the 05:45 Codiceira–Ermesinde service, plus an inherited Bolhão miss. The destination where a bus is late is not automatically the defect location.

An original-input one-second prefix replay of the early Codiceira–Ermesinde case matches all 114 complete bus calls before its cutoff. Its native execution takes about six seconds on this machine. The trace shows short signal waits and stopping/braking overhead, not a single large queue. Skipped on-demand passage records are excluded from stationary stop-service time in the new casebook. Missing passenger/signal observations prevent treating this deficit as proof that the published timetable is wrong.

## Reusable workflow and evidence boundaries

Use the [operator guide](../product/investigation-loop-operator.md). `study_session.py` exposes line-scoped initialization, cheap local steps, full-service steps and status. It verifies reuse, journals failures, recovers interrupted state promotion and refuses concurrent writers. A passing empty control cannot erase an unresolved combined-demand profile. A real complete 701 control was executed through this interface and the second invocation reused the result: one native execution, one verified reuse.

The local recorder keeps requested, departed, completed, undeparted and uncompleted actors explicit. Collisions do not teleport actors away. Native budget stops remain partial evidence; a run with no recorded positions cannot produce a visual claim. Local tests take hundredths of a second on the reduced network; using the full regional network adds several seconds of initialization. Full-day executions here take roughly 10–404 native seconds. These are observed development timings, not performance guarantees.

The public viewer preserves frame, selected actor, dimension, language and source identity in shared links. Both renderers show the same trajectory. A changed capture or different source execution is rejected. Browser tests and visual review caught and fixed Retina canvas clipping. The older `/701-inspection/` bus-only replay remains labelled as its historical control and links to the current local cases.

Another line can use the same triage, session, native-case and export interfaces. It still needs an adapter for its actual road network, official service, demand, stop matching and readiness review. The current full-day demand/preparation adapter is still specific to 701; the new workflow does not claim automatic calibrated ingestion for arbitrary lines.

Minimality is considered only after a package passes the declared complete scenario/seed and access gates. No package does so yet. Costs and implementation phases would be premature as a recommended scheme; retain candidate quantities and resource assumptions for later comparison.

## Primary technical references

SUMO documents internal waiting positions and their role in yielding movements in [Road networks](https://sumo.dlr.de/docs/Networks/SUMO_Road_Networks.html) and supported `contPos` changes in [PlainXML](https://sumo.dlr.de/docs/Networks/PlainXML.html). The [netconvert options](https://sumo.dlr.de/docs/netconvert.html) distinguish assumed internal-junction vehicle width from surveyed lane width. [Vehicle junction parameters](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html) and [Safety](https://sumo.dlr.de/docs/Simulation/Safety.html) describe minor-gap, advance and dawdling controls. These sources explain the tested mechanisms; they do not validate Porto signal plans or prove causality for a recorded failure.
