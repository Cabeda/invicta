# 701 investigation: an Alfena split-junction blocking mechanism

**A two-car native reproduction now explains a persistent blocking mechanism at the Alfena queue head. A compound-junction model correction clears that local failure. No full-line compliant proposal has been established.** The frozen V5 regional runs, reference, demand and public animation remain unchanged.

## What was captured from the original run

The unchanged proposed-layout replay starts at the original warmup, retains all XML inputs and controller settings, and stops at the first unexpected 300-second bus wait. It reached **15:19:33**, after 585.12 native computation seconds within its explicit 900-second cap. All **3,074 completed native bus calls** before that cutoff match the archived original run, with no differences. It observed 63 completed scheduled services; future deadlines remain separate from missing service.

The stopped service is **`d1_bus_36`, Codiceira 15:07 → Bolhão**, before Senhora da Paz. Its actual running context exposes the ordinary vehicles `crossing_14_109` and `crossing_14_33`, the bicycle and the following traffic as conflicting/queued actors. Both cars' consecutive waiting counters extend back to **14:53:27**. That time is derived from counters, not a captured first-entry manoeuvre. The bicycle stops later, around 14:54:45, and this bus around 15:14:33.

This captures propagation into a bus and gives an earlier mechanism to reproduce. Completed-call equality does not claim trajectory equivalence for every actor. A saved-state continuation is still not a verified substitute for the original run.

## How the mechanism was reduced

An unchanged 30-second snapshot analogue leaves both leading buses stationary. Removing one crossing car (`crossing_14_33`) moves the outbound bus 140.33 m and the inspected ordinary queue head 283.40 m. Removing the bicycle does not release that queue. These are diagnostic actor-removal probes, not physical traffic proposals or demand-preserving comparisons.

The decisive case starts **fresh**, with only the two crossing cars, original vehicle type and local route suffixes. Both requested actors are inserted. They become stuck at the same junction positions as the archived queue; either car completes when run alone. No inherited snapshot, passengers, bus, bicycle or regional traffic is needed for this smaller failure.

The pair uses two imported priority junctions, **`14297876949` and `14297876959`**, where Rua de São Vicente meets Rua Nossa Senhora da Paz. Their centres are about 6.64 m apart. After intersection geometry, each connecting normal road has only **0.20 m of available lane length**. The two movements can enter the separately represented intersections and then remain mutually blocked. The frozen OSM source represents the two carriageways and median connection as separate nodes/ways.

The reduced 13-road fixture retains the original two junctions' complete attributes and right-of-way request matrices. It reproduces the waiting positions within 1 cm. Removing surrounding roads changes exact arrival timing; the reduced case is not asserted to reproduce the full network's offset thresholds.

## What the correction changes

The candidate plain-XML patch joins those two imported nodes into **one compound priority junction**, using netconvert. It retains **all eight external vehicle movements**, the two requested actors, their types and physical road endpoints. The now-internal median roads disappear from the explicit route lists. No bus lane, traffic signal, turn ban, faster boarding profile or keep-clear override is added.

SUMO's own OSM-import guidance describes how separately mapped carriageways can produce multiple nodes for one intersection, and says explicit joins may be needed where automatic heuristics do not suffice. This supports testing the correction; it is not a street survey or a statement about real Portuguese signal control. [SUMO OSM junction guidance](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html#junctions), [supported plain-XML joins](https://sumo.dlr.de/docs/Networks/PlainXML.html#joining-nodes).

| Diagnostic | Split geometry | Compound-junction candidate |
|---|---|---|
| Reduced network, 21 relative departures from −10 to +10 seconds | Both actors finish in 8 cases; the pair remains blocked in 13 | Both finish in all 21 cases |
| Reduced network after unmodified netconvert reprocessing | Both finish in 9 of the same 21 cases | Reprocessing alone does not remove the failure |
| Full regional network geometry, two-car case at offsets −7, 0 and +4 | Both remain blocked at the 180-second cutoff | Both finish by seconds 35, 42 and 46 respectively |
| Full regional network after unmodified reprocessing, offset 0 | Both remain blocked | Rules out reprocessing alone as the explanation for that comparison |
| Each actor alone on the original reduced geometry | Each finishes | Both actors are load-bearing for the reduced failure |

Zero collision records were produced in these cases. This is a native diagnostic result, not a field safety validation. The full regional *network* comparison still requests only two cars; it does not represent the full regional *demand*.

An earlier full-network offset sweep completed 20 of its 21 planned cases before its 120-second sweep budget ended: 12 blocked and eight completed. The +10-second case was not executed. Its original exception and outputs are retained, with a separately labelled post-run audit. The complete 21-case figures in the table come from the small retained fixture, not that partial sweep.

## Regression and provenance

The native regression first failed with an identity node patch: the cars remained stuck where completion was required. Applying the explicit join made the test pass. Five tests now cover the original failure, each actor alone, unmodified reprocessing, preserved external movements and the 21-offset joined case. The suite runs in under one second in the local pinned environment. It exercises native SUMO rather than a mock of the junction logic.

```sh
.venv/bin/python -m unittest discover -s prototypes/line-701/full -p test_junction_geometry.py -v
```

The [small fixture and candidate patch](../../prototypes/line-701/full/diagnostics/alfena-junction/README.md) and [evidence manifest](701-queue-onset-2026-10-30/manifest.json) retain source identities, hashes, native outputs, implementation witnesses and exact correction recipes. Regional inputs are referenced from the existing verified archive; they are not replaced by a new success label.

## What remains before a proposal can qualify

This identifies a **sufficient, reproducible blocking mechanism consistent with the original Alfena queue**, and tests a candidate correction. It does not establish that this is the only source of delay or capture the exact two-car entry sequence in the original run.

The patch has not been promoted into the regional baseline. That requires regenerating the model, checking every affected route, stop and physical demand position, and applying the same accepted correction to baseline and proposal before comparison. The current audit still contains the empty-case 19-second miss and three stop-match review flags. No force flag or gate bypass was introduced.

The baseline Costa Cabral queues, the remaining Pires de Lima–Combatentes delays, conditional signal priority, finite vehicle circulation and whole-line robustness still need investigation or implementation. The next regional comparison must preserve all 127 scheduled services and all physical requests. A local two-car pass cannot qualify the 714 strict checks, passenger outcomes, access impacts or real STCP punctuality.
