# Line 701: Codiceira COD3 source and stop-footprint review

Reviewed 31 October 2026. Scope: frozen public sources and SUMO implementation semantics. This note makes no field-safety, calibration, timetable-compliance or operating-policy claim. The source review did not change the prepared regional model or waive its audit. Subsequent controlled native tests are recorded below; they do not qualify a full-line proposal.

## Findings

1. **Outbound COD3 is OSM platform `6143667230`, not inbound COD platform `6143667229` or terminal COD4 platform `6143667226`.** The frozen STCP stop list identifies COD3 as stop 52, **LGO DA CODICEIRA**, at **41.244541, -8.519753**, in direction 0, Bolhão → Codiceira. Frozen OSM node `6143667230` version 6 explicitly identifies `COD3`; it is about **7.75 m** from the operator coordinate in the native network projection. [Frozen official stop list](../../prototypes/line-701/data/official-outbound/outbound_stops.json), [official API](https://stcp.pt/api/route/701/stops/direction?direction_id=0), [OSM node version 6](https://www.openstreetmap.org/api/0.6/node/6143667230/6).
2. **V17 has a definite stale-position error independently of the conservative whole-fragment berth rule.** COD3 retains `pos=16.23830495946768` on lane `1124001684_0`; that lane shrank from **29.67 m** in V15 to **10.84 m** in V17. Thus `pos > lane.length`, by approximately **5.40 m**. Even an engine that supports vehicles spanning lane boundaries cannot make that unchanged lane coordinate valid. [V15 reference](701-investigation-loop-2026-10-31/study.json), [V17 reference](701-investigation-loop-2026-10-31/study.json), [V17 network](701-investigation-loop-2026-10-31/study.json).
3. **The project’s complete-12-m-bus-on-one-normal-fragment check is stricter than SUMO’s engine requirement.** SUMO supports vehicle occupation across predecessor lanes and microscopic stops on internal lanes. This is a reason to investigate a continuous, source-correct footprint, **not** a reason to waive geometry or conflict checks. [SUMO 1.28 `MSVehicle::computeFurtherLanes`](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/MSVehicle.cpp#L5519-L5558), [SUMO 1.28 `MSBaseVehicle::addStop`](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/MSBaseVehicle.cpp#L1387-L1582).
4. **The selected native route itself warrants review before choosing a new berth.** The frozen outbound OSM relation and official shape support the direct movement from Rua 1º de Maio toward Rua Nossa Senhora do Amparo. The current native path instead makes a small loop through Largo Codiceira. The direct permitted connection already exists in V17, so this is a bounded route-and-stop regression candidate, not evidence for changing a street. Details below.

## Frozen stop and road evidence

The official outbound sequence ends **ALXH1 (51) → COD3 (52) → VGM5 (53) → COD4 (54)**. The stop list was retrieved on **29 October 2026 at 10:24:56 UTC**; the shape was retrieved at 10:24:57 UTC. The shape API is direction-resolved, with no verified historical-date parameter. These are frozen published locations and geometry, not observed bus passages or surveyed front-of-bus positions. [Source metadata](../../prototypes/line-701/data/official-outbound/metadata.json), [official shape API](https://stcp.pt/api/route/701/shape?direction_id=0), [frozen shape](../../prototypes/line-701/data/official-outbound/outbound_shape.json).

Frozen OSM `6143667230` v6, timestamp **2024-05-30T15:51:42Z**, has coordinates **41.2445069, -8.5198337** and tags `ref=COD3`, `gtfs:stop_code=COD3`, `gtfs:stop_id=COD3`, `name=Largo da Codiceira`, `operator=STCP`, `public_transport=platform`, `highway=bus_stop`, `bus=yes`, `shelter=no`. It is a roadside platform node, not a 12 m polygon or longitudinal berth survey. The nearby `6143667229` has `ref=COD`, a different coordinate and `shelter=yes`. [Frozen OSM extract](../../prototypes/line-701/full/data/network.osm.xml.gz), [COD3 v6](https://www.openstreetmap.org/api/0.6/node/6143667230/6), [COD v6](https://www.openstreetmap.org/api/0.6/node/6143667229/6).

Frozen outbound relation **10107392 v64** explicitly has `gtfs:direction_id=0`, `gtfs:route_id=701`, `from=Bolhão`, `to=Codiceira`; COD3’s platform member is `6143667230`. Its road-member sequence near the stop is **102890697 → 1124001683 → 151268557**. It does **not** include the current native loop roads `1124001684 → 1124001681 → 1124001708`. Way `102890697` is Rua 1º de Maio / EN 105; way `1124001683` is Rua Nossa Senhora do Amparo / EM 606, with node order ending at `1199874817`. Outbound traversal from that shared node therefore runs **against** the OSM node order of `1124001683`, consistent with native negative-prefixed edges. The relation’s member roles do not independently encode traversal direction; this direction conclusion follows from ordered road connectivity. [OSM relation version 64](https://www.openstreetmap.org/api/0.6/relation/10107392/64), [way 102890697 v21](https://www.openstreetmap.org/api/0.6/way/102890697/21), [way 1124001683 v3](https://www.openstreetmap.org/api/0.6/way/1124001683/3).

The official projected shape approaches through approximately `(7844.46,10146.04)`, `(7858.61,10163.88)`, `(7871.15,10168.39)`, reaches COD3 `(7877.61,10166.31)`, and proceeds east via `(7877.84,10170.65)` and `(7926.98,10178.80)`. This is consistent with that direct turn, rather than following the selected normal-edge loop north through Largo Codiceira. This agreement is geometric evidence for testing the direct route; it does not establish exact boarding-door location. [Frozen projected V17 reference](701-investigation-loop-2026-10-31/study.json), [unprojected official shape](../../prototypes/line-701/data/official-outbound/outbound_shape.json).

## What the current blocker means

`model_audit.py:100` groups lane permission, `12 <= min(15, stop.pos)`, and `stop.pos <= lane.length` under the single `stop_footprint` code. V17’s audit reports that blocker for `d0_COD3`. This conflates two distinct questions:

- **Position validity:** is the stated front-position coordinate inside its selected lane? Here, **no**: 16.2383 > 10.84.
- **Continuous footprint validity:** at a source-supported stopping front position, where are the bus’s preceding 12 m, and what junction/conflict areas do they occupy? This remains unresolved.

The audit’s current berth proxy prevents the complete bus from extending upstream of its selected normal edge; the extra 15 m term corresponds to the generated stop-area length. That is a conservative project rule, not a general SUMO restriction. Keep the current gate blocked until a replacement can validate the real geometry and conflicts with at least equivalent evidence. [Audit implementation](../../prototypes/line-701/full/model_audit.py), [V17 audit](701-investigation-loop-2026-10-31/study.json), [stop XML generation](../../prototypes/line-701/full/experiment.py).

## Primary SUMO semantics

- A SUMO `busStop` is an interval on **one named lane**. Vehicle front position normally aims for `endPos`; `startPos` allows an earlier blocked stop to count as reached. A stop-area definition does not itself describe the complete bus footprint. [Official public-transport documentation](https://sumo.dlr.de/docs/Simulation/Public_Transport.html#bus_stops), [official stop-position documentation](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#startpos_and_endpos).
- In **SUMO 1.28.0**, `MSStoppingPlace::fits` accepts the default downstream position, or a position with at least half the vehicle length inside the interval. This does not enforce a complete bus inside a single stop interval. [Version-pinned source, lines 170–175](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/MSStoppingPlace.cpp#L170-L175).
- `MSBaseVehicle::addStop` rejects negative `startPos` or `endPos` beyond the lane. Its short-stopping-place message uses **half** the vehicle length and exempts a stop occupying its whole lane. It explicitly associates an internal-lane stop with the preceding normal route edge and checks its next normal edge; internal stops are rejected in **mesoscopic** simulation. [Version-pinned source, lines 1410–1474 and 1564–1582](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/MSBaseVehicle.cpp#L1410-L1474).
- `MSVehicle::computeFurtherLanes` walks backwards through route-compatible normal and logical predecessor lanes while the rear still extends upstream, and marks partial occupation. This establishes engine support for a vehicle spanning lane boundaries, including internal lanes. It does not establish that stopping across any particular conflict is acceptable. [Version-pinned source, lines 5519–5558](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/MSVehicle.cpp#L5519-L5558).
- `friendlyPos` repairs numerical range errors; it does not reproject an official coordinate or preserve the old world position after junction trimming. The bus-stop builder calls `checkStopPos` with `POSITION_EPS` as the minimum interval. That helper clamps oversized `endPos` to lane length and adjusts `startPos` into range. This is distinct from a different single-position helper that uses `lane.length - 0.1`. [SUMO 1.28 bus-stop builder, lines 462–484](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/netload/NLTriggerBuilder.cpp#L462-L484), [official `checkStopPos` source, lines 327–359](https://sumo.dlr.de/doxygen/d8/dd2/_s_u_m_o_route_handler_8cpp_source.html#l00327).

The last helper source is the official Doxygen snapshot generated **7 September 2026**, rather than a verified 1.28 tag: fetching its version-pinned raw page failed. The installed-runtime check below independently confirms the relevant clamping result. Other source links above were inspected at tag `v1_28_0`.

### Installed-runtime zero-step check

A disposable additional file was loaded against the unchanged V17 network using `.venv` libsumo. `getVersion()` returned **`(22, 'SUMO 1.28.0')`** and `simulation.getTime()` returned **0.0**; no simulation step ran.

| Requested stop | Requested interval | Returned interval | What it establishes |
|---|---:|---:|---|
| `1124001684_0`, `friendlyPos=true` | 1.2383049595 … 16.2383049595 | **1.2383049595 … 10.84** | The production-style setting silently changes the stale endpoint. |
| `:codiceira_compound_20_0`, `friendlyPos=false` | 21.206 … 36.206 | **21.206 … 36.206** | An internal-lane busStop loads on this installed microscopic runtime. |

This was an isolated loading check, not a vehicle-stop, dwell, passenger or conflict regression. Existing network signal-detector warnings were emitted. No new permanent fixture was saved. The production stop generator currently writes `friendlyPos=true`; therefore a successful native load alone cannot detect this stale-position defect. [Generator](../../prototypes/line-701/full/experiment.py).

## Source-supported next test

**First inspect the direct-route alternative and reproject the two public stop references onto the ordered normal-plus-internal lane path. Do not select a position simply because a 12 m inequality passes.** V17 already permits buses from `102890697#5` directly to `-1124001683#1` through `:codiceira_compound_20_0` (40.59 m). On the present loop, the corresponding connector is `:codiceira_compound_21_0` (43.37 m). [Frozen V17 network](701-investigation-loop-2026-10-31/study.json).

The exact local **current** normal-edge sequence is `102890697#4 → 102890697#5 → 1124001684 → 1124001681 → 1124001708 → -151268557#10 → -151268557#9 → -151268557#7`. The source-supported **test alternative** is `102890697#4 → 102890697#5 → -1124001683#1 → -1124001683#0 → -151268557#10 → -151268557#9 → -151268557#7`. The negative `1124001683` fragments are the outbound traversal of that OSM road. Their connecting internal edges are `:10278911802_1` (3.03 m) and `:10278911804_7` (17.65 m). **Do not omit `-151268557#10`: it is required between `-1124001683#0` and `-151268557#9`.** These connections and bus permissions were checked read-only in V17. [Frozen network](701-investigation-loop-2026-10-31/study.json), [current ordered route](701-investigation-loop-2026-10-31/study.json).

Read-only lane projections, using the native network coordinate conversion and lane shapes:

| Public reference | Candidate lane | Closest lane offset | Lateral distance |
|---|---|---:|---:|
| OSM COD3 platform | direct connector `:codiceira_compound_20_0` | 36.206 m | **2.033 m** |
| STCP COD3 coordinate | direct normal `-1124001683#0_0` | approximately 1.024 m | **1.845 m** |
| OSM COD3 platform | current-loop connector `:codiceira_compound_21_0` | approximately 34.324 m | **7.664 m** |
| STCP COD3 coordinate | current-loop connector `:codiceira_compound_21_0` | approximately 41.042 m | **11.461 m** |

Offsets are computed by polyline projection and scaled from geometric shape length to declared simulation lane length. Distances are point-to-lane-shape distances; they differ from the stored route adapter’s centreline `snap_distance=13.0011 m`. Neither a roadside platform node nor the operator point specifies where the bus’s **front** must stop. The two source locations and any explicit front/door offset need a documented interpretation before a production stop is chosen. [Frozen OSM](../../prototypes/line-701/full/data/network.osm.xml.gz), [frozen STCP stop list](../../prototypes/line-701/data/official-outbound/outbound_stops.json), [V17 network](701-investigation-loop-2026-10-31/study.json), [SUMO distance/geometry distinction](https://sumo.dlr.de/docs/Simulation/Distances.html).

A bounded follow-up should:

1. Compare the direct route with the frozen official shape and outbound relation; preserve the explicit source distinction if they disagree. Verify permitted normal-edge connections and the internal path.
2. Bind a source-supported stop front position to the selected lane/path, with strict numerical range checks and no `friendlyPos` correction during validation. If the result is internal, account for the project’s current normal-edge-only stop representation rather than disguising it as a normal-edge offset.
3. Trace the preceding **continuous 12 m** of bus footprint over its connected lanes. Inspect junction conflict regions, occupied predecessor links, road-side consistency and passenger access. Keep the existing conservative audit blocker until those obligations are implemented and independently checked.
4. Run a small native bus approach → dwell → departure test, then both-direction meeting/offset cases with that actual stop active. Record stop front, rear/path footprint, stop output, passage, conflicts, collisions, teleports and completion. Loading alone is insufficient.
5. Only after the local regression and model audit pass, rerun the affected empty diagnostic and regional service tests with fresh identity bindings. This note supplies no result for those unperformed tests.

## Input fingerprints

All hashes were recomputed from local bytes during this review.

| Input | SHA-256 |
|---|---|
| Frozen official outbound stops | `0948247456a354c170d75e7c64f4af4a032f368ce0311adc7643a1c30df5078e` |
| Frozen official outbound shape | `6df71488885a9ae66b4caf30e4f2fd3949f2e16b01a6ee49e7e0dc36aa6da014` |
| Frozen merged OSM `.gz` | `b1fac2ec60f8183a5669326c33f8746a1bc93858e96bfd5258ec257f2fa7c726` |
| V15 network | `e53c32aeac787e051a105da37dd25a30f1379864fa11f80d44cf16f6b522ad59` |
| V15 routes | `ac67241b3bcf3bdd430495242d0f5284a8aa0d03b827e7612c4bb92b616e0d34` |
| V17 network | `0749e1790d3d21d6b8328610410450bae6be4e929f4e8a64fcfae8edd32a4194` |
| V17 routes | `da2b3d44ad97514b671d8dd1f4d833912abc07d009651a7a90ee6fa8502dd9d0` |
| V17 final audit JSON | `b48d7b1e8ba2a33475e8f89d800c27d022fac313cac6a7cb717851f2316aa7fd` |

Model links point to the enduring native archive, which contains V15/V17 descriptors and audit supplements. Use the [verified archive restoration instructions](../product/investigation-loop-operator.md#restore-prepared-models-from-the-archive), choosing the corresponding model key. Model fingerprints identify exactly which candidate was examined.


## Subsequent controlled native tests

The proposed local follow-up was run after the source review, using unchanged 12-metre bus parameters and an opposing inbound bus. No full regional reference was altered.

| Prepared network and route | Relative arrival offsets (s) | Requests completed per case | Collision records | Stationary occupancy |
|---|---|---|---|---|
| V17 direct route, strict internal stop | −10, −6, 0, 6, 10 | 2/2 | 0 | 20 one-second frames |
| V15 unchanged junction geometry, direct route | −6, 0, 6 | 2/2 | 0 | 20 one-second frames |

The V17 stop uses `:codiceira_compound_20_0`, interval 21.206…36.206, with `friendlyPos=false`. An initial route omitting `-151268557#10` was rejected by native routing and remains in the [direct-stop archive](701-codiceira-direct-route-2026-10-31/study.json). The corrected case is also a permanent native regression in `test_investigation_loop.py` with input fixtures under `diagnostics/codiceira-stop`. Beyond the archived stationary-frame evidence, the regression now asserts an actual native `source_COD3` stop-service record on that internal lane lasting at least 20 seconds. The recorder hash-binds `stops.xml`; signal/queue waiting alone cannot satisfy this assertion.

The V15 route-only probe retains the existing tiny normal fragments and uses stop lane `-1124001683#1_0`, interval 0…4.8698484344, with `friendlyPos=false`. The OSM platform projection is approximately 3.026 m laterally from that lane. Its use as a **front-position anchor** is an explicit diagnostic assumption: the platform node does not specify the boarding door or stopping front. A separate zero-step loading control emits SUMO's **short-stop warning**. The three simulations completed, but this warning and the unresolved continuous footprint/access checks prevent promotion to production stop geometry. All evidence is retained in the [route-only archive](701-codiceira-route-only-2026-10-31/study.json), including `zero-step-warnings.log`.

These results prioritize source-backed route matching before a junction rebuild. They do not isolate a field benefit, validate passenger access, resolve every meeting offset, or establish timetable compliance. The full-model gate remains blocked until the source-correct route/stop adapter and explicit continuous-footprint/conflict checks pass. Native-case recording now preserves warnings with output hashes, preventing future diagnostics from hiding this distinction.
