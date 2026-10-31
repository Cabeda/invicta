# 701 traffic stress: what passes and what still prevents a proposal

Study started 30 October and continued on 31 October 2026. This is an uncalibrated native SUMO investigation, not an approved street design or a prediction of STCP performance.

**We have reproduced traffic-related delays and found a small signal-priority candidate for empty buses. We have not found a qualifying proposal for passenger-carrying service under the combined workload.** Several apparent queues also contain network-model defects. Those must be resolved before attributing their effects to missing bus lanes.

The [accepted scope](../product/traffic-stress-search-2026-10-30.md) preserves both complete directions, 127 scheduled services and all 714 designated timing checks from the frozen 28 October operator reference. A timing check evaluates a departure at an origin/intermediate timing point or an arrival at the destination. Completing a service alone does not mean it was punctual. We report exact seconds separately from the agreed operational allowance: no early departures, no missing checks, and at most 60 seconds late.

## What the traffic ramp means

The busy synthetic catalogue contains 41,599 ordinary vehicle requests in seed 17. Stable hashed subsets retain each selected request's mode, origin/destination positions and departure: 397 requests at 1%, 4,107 at 10%, then the larger subsets. These are fractions of a synthetic workload, **not estimates of the percentage of real Porto traffic**. The regional network includes through traffic, local residents, taxis, motorcycles, bicycles and other ordinary traffic. Demand remains in the denominator when it cannot enter or finish.

Separate passenger tests use 6,172 passenger requests and 3,042 pedestrian walking requests, shared across compared policies. The passenger rate is a flat synthetic 0.05 per minute per eligible stop; walking requests use 0.02 per minute per selected crossing pair. This does not establish actual stop patronage or night demand. Native boarding, alighting, finite capacity and request stops remain active. Default boarding is 1.8 seconds per passenger. No timetable, bus speed, acceleration, driver randomness or passenger list was adjusted to manufacture a pass.

## Results that matter

All figures below use the operational allowance; the archive retains strict results too. “Late checks” can include several checks on the same service. The ordinary-traffic column counts requests that did not finish, including those unable to start.

| Model and test | Buses completed | Late checks / 714 | Ordinary requests unfinished | Collisions | Interpretation |
|---|---:|---:|---:|---:|---|
| V9: 397 traffic requests, no passengers/walkers | 127 | 0 | 0 | 0 | Small traffic control passes |
| V9: 4,107 traffic requests, no passengers/walkers | 127 | 3 | 17 | 0 | Reproduced traffic-related lateness |
| V9: same 4,107 requests, bounded priority across 22 changed controllers | 127 | 0 | 13 | 0 | Bus timing passes; ordinary demand remains unfinished |
| V9: same requests, priority restricted to two controllers | 127 | 0 | 23 | 0 | Small tested bus-priority package; fails the broader acceptance goal |
| V11: no traffic/passengers/walkers, seeds 17, 29 and 41 | 127 each | 0 each | 0 | 0 | Empty prerequisite passes; exact-second misses remain |
| V11: 4,107 traffic requests, no passengers/walkers | 127 | 0 | 14 | 0 | No street intervention; model change alters the result, regional defect remains |
| V11: passengers and walkers, no ordinary traffic | 127 | 25 | 0 | 0 | Passenger service exposes a separate timing problem |
| V11: passengers, walkers and 4,107 traffic requests | 127 | 20 | 18 | 0 | Combined control does not meet the goal |
| V11: same combined requests, priority at two controllers | 127 | 23 | 28 | 0 | Reject: worse punctuality and more unfinished ordinary demand |

In the combined V11 control, all buses start within the allowance and 116 of 127 reach their destination within it. All 6,172 passenger requests and all 3,042 walking requests complete. The 20 late checks occur at Marquês inbound (7), Bolhão (6), Codiceira outbound (5), Ermesinde inbound (1) and Areosa Mercado outbound (1). This is simulation evidence, not observed delay hotspots.

The two-controller package does not transfer to combined demand: destination punctuality falls to 113 of 127, late checks increase to 23 and unfinished ordinary requests increase from 18 to 28. It is rejected. The result is why an empty-bus demonstration cannot be sold as a passenger-service solution.

The full 41,599-request stress test also retains passengers and walkers. It uses fixed paths for discovery and stops after its declared 120-second native computation budget, at simulation time 39,142 (10:52:22). Only 10 buses have finished by that cutoff, and four collision records exist. It cannot establish a full-day outcome: much scheduled service and demand lies beyond the observation window. It is not compared as a completed daily policy result.

## What the model diagnosis changed

The traffic ramp revealed ordinary vehicles waiting around Areosa for approximately 19 hours. Inspecting the saved final state without advancing time found blocked vehicles even with a green indication ahead. This is not credible evidence of normal congestion.

A native reduction with 51 roads reproduces a smaller mechanism: two cars and a bicycle strand the second car inside an internal lane. Remove any actor and the others complete. The existing fixed phase cycle clears them; changing the jam threshold or detector length does not. Setting the inferred Areosa detector gap to zero clears the three-actor case across 21 arrival offsets while preserving every original phase definition. The native regression runs in less than a second.

**That local success does not fix the regional Areosa problem.** The full V11 reruns still leave vehicles trapped there. V11 is an unpromoted diagnostic variant, not a corrected representation of the real junction. Remaining hypotheses include short split-road storage and lane-change connectivity around the 3.92 m and 0.20 m fragments. A broader source-bound native regression is needed before changing the regional geometry or claiming a street intervention is necessary.

SUMO generates inferred signal programmes; those are not municipal timing plans. Its documentation explains [generated programmes and actuated detector behaviour](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html). Changing visibility in the inspection viewer never changes these native controls.

Three stop offsets also remain explicit model approximations: Codiceira, Largo da Codiceira and Brás Oleiro. The review files bind the exact operator stop, corroborating OSM platform, short route fragment, retained berth, network and reference hashes. They permit synthetic stress work only and do not establish a surveyed bus berth.

## Why lanes alone are not yet a defensible answer

Passenger-only runs are late without cars. A separate signals-off diagnostic keeps the same passenger and walking requests: all 127 buses and all people finish, but seven checks remain late and one pedestrian collision is recorded. This is neither a proposed signal policy nor a proof that the real timetable is impossible. It shows that removing signal delay alone does not remove all lateness under these assumptions.

For example, the 21:55 outbound service (d0_bus_59) leaves Ermesinde Forum on its reference time of 22:23 in that diagnostic. It reaches Codiceira at 22:37:42 against 22:35:00. Along that section it boards and alights passengers at closely spaced stops. This directs the next feasibility audit toward running time, stop service and the shape of late-evening passenger demand, before blaming downstream car queues or changing the timetable.

Faster-boarding sensitivities were labelled explicitly. On V9 without cars, 0.6 seconds per passenger reduced 23 late checks to eight; bounded priority did not remove the remaining eight. The more optimistic 0.5-second variant had eleven late checks and a collision. Instantaneous boarding still had three late checks and is only a diagnostic bound. Historical capacity guidance distinguishes boarding channels and fare arrangements; these rates are not measurements of STCP operations. See the [TRB capacity manual, Part B](https://www.trb.org/publications/tcrp/tcrp_webdoc_6-b.pdf) and [NACTO boarding guidance](https://nacto.org/publication/transit-street-design-guide/transit-system-strategies/network-strategies/fares-boarding/).

Removing two generated, unused Combatentes stages (V10) retained every served green and all-red clearance but did not produce a qualifying passenger result. Experimental phase resequencing also failed to improve the passenger results; that active implementation was removed, and its native witnesses remain archived. More complicated control was not treated as progress merely because it ran.

## How this search is now faster and more reliable

Controller comparisons reuse hash-verified physical inputs. Only declared controller options may differ; changing a seed, demand, boarding or lane policy is rejected. Identical native network files share storage while keeping their original paths and exact bytes. This recovered space after several native attempts failed because the disk filled; those attempts remain recorded as storage failures, not traffic outcomes.

Fixed routing is a separate discovery assumption. At 397 requests, native execution was about 12 seconds with fixed paths versus 189 seconds with dynamic rerouting. Acceptance comparisons must use the same routing policy. Frozen controller code is executed from each trial folder; trial and prefix-replay option mapping is shared, preventing a subset policy from silently replaying on every signal.

The evidence archive verifies input/output hashes and recalculates both strict and operational results before publishing its final manifest. Failed attempts preserve partial XML, traces, snapshots and implementation witnesses. A snapshot omitted from a historical output index is preserved separately against its recorded monitor digest, without rewriting the original execution result.

The [frozen manifest](701-traffic-stress-2026-10-30/study.json) contains 31 recorded runs: 29 full-day executions, one budget-limited stress diagnostic and one explicitly non-qualifying signals-off diagnostic. Four failed attempts are retained separately. The [compact result table](701-traffic-stress-2026-10-30/summary.json) binds its source manifest by SHA-256. There are 519 deduplicated evidence objects, about 115 MB compressed. All 31 recorded timing evaluations were recalculated from their archived native stop and trip outputs.

Inspect the combined control through the existing public command:

```sh
.venv/bin/python prototypes/line-701/full/investigate.py diagnose \
  --source docs/research/701-traffic-stress-2026-10-30/study.json \
  --trial v11-traffic-and-people-010-baseline-s17 --format summary
```

## Decision

No proposal is qualified and no global minimum is claimed. The two-controller empty-bus result is a candidate worth retaining, not a recommendation to install equipment. The immediate next steps are to reproduce the remaining regional Areosa blockage, audit passenger-service feasibility between timing points, then repeat baseline and candidate on identical combined demand across seeds. Only after that should the search add targeted lane/access restrictions, compare total person travel time and phase a street pilot. The current public 2D/3D recording remains its original identified execution; these diagnostic runs have not been substituted into it.
