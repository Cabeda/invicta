# Combatentes: reproduce first, then correct internal signal mapping

**The repeated internal stop is a native model fault, not just excess viewer markers.** A lone bus reproduces it without any other traffic. An explicit boundary-control correction removes that stop in both directions. Final V9 full-day bus-only runs pass the chosen 60-second project criterion in all three seeds, with no changes outside Combatentes; exact-second compliance and model promotion remain unresolved.

## Mapping and cause

OSM supplies road and crossing nodes. The import guesses signals, joins nearby controllers and generates an actuated programme. It does not read surveyed Porto timing plans or map individual physical lamp heads. The [source audit](701-combatentes-signal-mapping-2026-10-30.md) records the seven mapped signalised crossing nodes and separate municipal equipment points. Purple source diamonds are crossings, not poles; viewer layer switches change annotations, not bus behaviour.

At Combatentes, five represented TLS junctions share one controller. A sixth central node, `299610705`, remains a priority junction outside that controller's membership. Ten controlled movements are approached from roads wholly inside the six-node physical review footprint. Eleven control entries from outside. Inbound the source bus encounters controller links 1, 7 and 17 in succession, over short connecting fragments. Grouping their controller did not make entry permission imply internal clearance.

The local source fixture retains 59 normal roads, the six junctions' native request matrices, all 24 phases and the original bus type. At the first red-capable regression run, the corrected-case assertion failed on the actual symptom:

```text
d1: 41.0 != 0 : Bus stopped again inside the already-admitted junction
d0: 110.0 != 0 : Bus stopped again inside the already-admitted junction
```

This is post-admission waiting, measured until the whole 12 m bus clears. It does not count legitimate waiting before the entry light. The command is now a permanent native regression:

```sh
.venv/bin/python -m unittest discover -s prototypes/line-701/full -p test_signal_mapping.py -v
```

## Chosen correction and alternatives

`signal_mapping.py` validates a source-bound recipe and writes supported plain `uncontrolled="true"` connection patches for the ten internal movements. External entry indices and the phase table remain. Native yielding/conflict logic is recomputed by netconvert. No bus speed, acceleration, randomness, timetable, demand or physical OSM feature was changed to obtain the local pass. SUMO documents this connection attribute in its [plain XML contract](https://sumo.dlr.de/docs/Networks/PlainXML.html#explicitly_setting_which_edge_lane_is_connected_to_which).

The corrected lone bus has **zero post-entry waiting in either direction**, versus 41/110 seconds. Opposing buses at five offsets clear without trapping each other. All **408** bus-movement-pair cases complete without recorded collisions. All 17 retained bus paths and eight walkers also start and finish together at three offsets, without recorded collisions. The imported pedestrian lane/connection graph and normal vehicle connection permissions are retained locally. These finite cases are regression evidence, not exhaustive safety validation.

Rejected alternatives:

- Signals off clears the buses but removes the control we are trying to model; it remains an optimistic diagnostic only.
- `--tls.uncontrolled-within true` alone retains the fault because the central priority node is outside the joined controller.
- Joining all six physical nodes clears the buses but removes an existing compiled walking connection. It is rejected.
- Always-permissive internal programme columns clear the buses but alter actuation; the explicit connection patch is clearer.

Two now-unused internal-only stages remain in the generated programme, producing no-detector warnings. The listed external phases are preserved; actual actuated transitions and off-state yielding are not asserted identical. The residual programme still needs field timing evidence. The correction does not prove the location of Cabeda's two reported physical signals.

## Full-day no-traffic result

The frozen reference is unchanged: **127 trips, both directions, 6,024 stop calls and 714 designated checks**. Final V9 runs at seeds 17, 29 and 41 complete every trip, with no missing checks, early departures or recorded collisions. There is no ordinary traffic, passenger boarding, pedestrian demand or dwell in these controls. Early arrivals at designated timing points wait for the scheduled departure; ordinary request stops can be skipped when unused.

| Seed | Source checks late by >60 s | Corrected checks late by >60 s | Source exact-second late checks | Corrected exact-second late checks |
|---|---:|---:|---:|---:|
| 17 | 6 | 0 | 20 | 1 |
| 29 | 3 | 0 | 17 | 3 |
| 41 | 2 | 0 | 14 | 2 |

Remaining strict misses: the first inbound service departs Ermesinde at 05:33:18/19/20 against 05:33:00; seed 29 also reaches Bolhão at 06:46:36 against 06:46:00 and departs Marquês at 23:16:09 against 23:16:00; seed 41 reaches Bolhão at 06:46:36. The worst remaining deviation is **36 seconds**. The 60-second threshold is the user's explicit operational project criterion, not an STCP contractual punctuality definition.

## Containing regional conversion changes

Applying another netconvert pass to the final regional model changed unrelated internal junctions, so that approach was rejected. The opt-in correction instead runs during the existing second import pass. A matched no-correction build retains the internal controls and produces **the exact same network bytes as V6**, and all 6,024 native stop events match the frozen source at each seed.

V7's minimal patch caused netconvert to regenerate several unrelated connections at nodes `cluster_292257944_292302552_4495041701_4495041703`, `cluster_292257945_292257951` and adjacent `292257954`. V8 pinned connections from a fresh control rebuild, but that control already differed from the original baseline. Neither version is the selected correction. No scheduled 701 route visits those nodes, which explains why their bus-only controls were still useful, but they could not establish regional access equivalence.

V9 instead loads the exact archived V6 network and reference, plus a frozen native import proven compatible by the byte-identical no-correction reconstruction. It validates the actual import input separately, pins **every existing normal-road connection from the frozen baseline**, and applies only the ten internal control changes through supported netconvert input. It does not repeatedly rebuild the first import and assume its output is identical. The source OSM archive remains hash-checked. A fresh import attempt that drifted was rejected; the record does not establish why the converter outputs differed.

The final full-network scope check passes against the original `4ccaa3…706fe` baseline: **zero changes outside Combatentes**, unchanged normal movement permissions, unchanged explicit pedestrian graph, all eleven external entry controls retained, and the complete phase table retained. Internal conflict lanes are regenerated by SUMO. This check uses exact attributes; the 2-decimal speed normalization is confined to the reduced-fixture fingerprint. Regressions reject unrelated junction changes, a changed import-stage programme and accidental deletion of external controls.

`model_audit.py` retains a `signal_mapping_scope_review` blocker for corrections that have not passed that regional check. V9 clears this particular blocker through its bound scope audit. The existing stop-footprint review flags remain, so it is still an unpromoted model correction. The public inspector deliberately continues to show the original failing recording rather than relabelling it as a corrected result. Ordinary-traffic and passenger comparisons must use fresh matched runs after the remaining geometry review.

## Evidence

The [twelve-run ledger](701-combatentes-controls-2026-10-30/controls.json) preserves three V6 controls and three runs each for V7, V8 and final V9: model/reference hashes, exact commands, implementation witnesses, all requested service, native outputs and per-check failures. [Recomputed evaluations](701-combatentes-controls-2026-10-30/evaluations.json) use the frozen events. Compressed objects have both compressed and decoded hashes. The [local fixture and recipe](../../prototypes/line-701/full/diagnostics/combatentes-junction/README.md) provide the fast regression.

This fixes the demonstrated extra internal stop in the model and makes the empty-service operational prerequisite pass. It does not yet establish feasibility with current traffic, complete pedestrian crossing coverage, actual signal synchronisation, physical head counts, vehicle blocks or field reliability.
