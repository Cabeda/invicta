# Combatentes: signal observations, inferred control and duplicated markers

**Follow-up:** the [native regression and correction](701-combatentes-native-fix-2026-10-30.md) now demonstrate the extra internal stop and remove it in an opt-in model, while preserving external entry controls. This document retains the original source/mapping audit; its unresolved field-head and timing questions still apply.

**The coloured circles in the inspection are SUMO movement-state markers, not an inventory of physical signal heads. The underlying controller is inferred from OpenStreetMap; it was not generated from official Porto timing plans.** Cabeda reports that the pictured Costa Cabral stretch should have two vehicle signals, while the view showed eight markers. That observation is retained as a constraint to validate; the two physical heads have not yet been assigned to particular native lanes or municipal equipment IDs.

## Source chain

| Layer | What the frozen sources establish | What they do not establish |
|---|---|---|
| Porto municipal equipment review layer | 16 `SEM` equipment records in the route-filtered review layer within 75 m of the inspected controller centre; all carry installation string `121`. Source downloaded on 29 October 2026, published as CCZero. | Vehicle versus pedestrian head, facing direction, controlled lane/turn, stop-line assignment, phase plan or offsets. These records were **not inputs** to `priority_model.py`'s signal generation. |
| OpenStreetMap source | Among the original nodes represented by this joined controller, seven have `highway=crossing` and `crossing=traffic_signals`; three others have no such tags. | Seven car signal heads, seven independent controllers, real phase timings or a correct stopping position for each vehicle direction. The acquisition manifest's wording “Official OpenStreetMap map API” refers to OSM's API, not municipal approval of the map. |
| Native SUMO controller | Five represented junctions grouped into one actuated programme; **21 movement links on 14 incoming lanes**. Eight green stages, each followed by 3 s yellow and 2 s all-red. | Physical signal-head count or verified real-world synchronisation. |
| Initial viewer | One coloured marker per `(controller, linkIndex)`, placed at a native lane end. Several links share the same lane and exact displayed position. | The number/location of physical traffic-light poles. This display could overstate the physical hardware. |

[Municipal dataset](https://dadosabertos.cm-porto.pt/dataset/sistema-de-gestao-de-trafego-semaforos). The extracted [machine-readable audit](../../prototypes/line-701/focused-replay/signal-audit.json) retains official record IDs, original coordinates, transformed coordinates, OSM tags, hashes, native movement links, phase membership and route transitions.

The source OSM archive hash is checked before extraction. Municipal longitude/latitude coordinates are projected using the native network projection and `netOffset`; this is explicit because the catalogue's CRS declaration and the downloaded coordinate ranges were previously found inconsistent. The review layer was already filtered to 40 m of either line direction; this local extract is not a complete 75 m hardware inventory. The inventory is location evidence, not a controller plan.

## How “synchronisation” was generated

The import uses `--tls.guess-signals`, `--tls.discard-simple`, `--tls.join` and `--tls.default-type actuated`. SUMO interprets nearby mapped signals and crossing structures, groups nodes and constructs a joint programme. This is **internal consistency within an inferred programme**, not alignment with the real installation's clock or surveyed neighbouring signal offsets.

The inspected programme has 24 phases and an offset of zero. Its listed nominal phase durations sum to **288 seconds**. Actual duration varies under actuation: 288 seconds is not a measured or fixed field cycle. No municipal phase grouping, real detector assignments or real offsets were supplied.

SUMO's documentation specifically warns that separately mapped junction nodes can produce poor throughput or deadlocks on short intermediate roads, and that automatically generated programmes can differ from reality. It recommends inspecting joins and joint controllers rather than assuming that imported signal locations imply correct control. [OSM traffic-light interpretation](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html#traffic_lights), [generated programmes](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#automatically_generated_tls-programs).

## What may affect the bus physically

This is not solely a display issue. The declared inbound route encounters three controlled transitions under the same joined programme, in order:

1. Link **1**: `-1172588827#2 → -1172588827#0`, at OSM crossing node `12514324965` on Costa Cabral.
2. Link **7**: `-1083211594 → -675897037#1`, at the separately represented junction `3897692280`, an untagged road node in the source.
3. Link **17**: `-675897037#1 → -27292882#9`, at the joined Alegria/Combatentes representation.

Some intervening normal road fragments have only 0.20–2.74 m usable lane length. Three programmed control transitions in this compact area require explicit review against actual entry stop lines, pedestrian crossings and internal conflict clearance. The frozen output establishes where the model stops the bus; it does not prove those stops exist on the real road.

The previously tested blanket physical junction join still failed the timetable and changed road-fragment identities. It remains rejected. Likewise, the `--tls.uncontrolled-within` option is not an automatic fix: SUMO explicitly notes collision risk. No such override or signal deletion has been applied. [Netconvert TLS options](https://sumo.dlr.de/docs/netconvert.html#tls_building).

## Inspection changes and next mapping decision

The inspector now separates:

- **Next bus links:** the selected bus's next logical movement states; the default. These coloured symbols are explicitly not physical signal heads.
- **All model movements:** the complete diagnostic overlay, for inspecting inferred control.
- **OSM source crossings:** the original seven signalised-crossing nodes in the audited controller, with links to review current OSM objects; these are not a physical signal-head count.
- **Combatentes equipment inventory:** neutral markers for the municipal equipment points, with unknown head type/timing; no invented red/green state.
- **No signal markers:** geometry/vehicle inspection alone.

These presentation changes do not alter the native run, remove control points or improve its punctuality scores. The audited controller and every recorded failure remain available.

Before changing physics, locate the two vehicle signals reported in the screenshot, distinguish them from pedestrian heads, map each controlled entry approach once, and identify which internal movements should clear under the same permission. Then test an explicitly documented controller/mapping candidate with pedestrian clearance and native collision checks. Until that mapping is resolved, signal-enabled lateness remains an **inferred-model diagnostic**, not evidence that Porto's actual timetable is infeasible or that the real junction requires more signals.

## Use OSM as the canonical map, with fixes at the right boundary

OSM is a suitable canonical source for roads, lanes where mapped, crossings, turn restrictions and signal-related geographic features. STCP remains the source for its timetable; signal phase programmes and detector/coordination assumptions remain separate model inputs. Municipal equipment can stay a comparison layer without independently creating extra simulated controllers.

There are three different correction paths:

1. A verified real-world feature is missing or wrong in OSM: prepare a source-backed OSM correction, retaining original IDs/history and evidence. Import a new frozen map version after that correction.
2. OSM accurately describes the street, but conversion duplicates control or creates inappropriate internal stops: correct the SUMO import/overlay and test it locally. Do not change accurate OSM geometry to accommodate a simulator limitation.
3. Timing or coordination is absent: record an explicit model assumption or obtain controller observations. A map edit cannot manufacture a real timing programme.

OSM's own signal documentation says its traffic-signal mapping is an abstraction of regulated ways/junctions, not a count of individual devices. It supports optional facing-direction tags and distinguishes signalised-crossing nodes from separately mapped signal devices. Therefore OSM-only sourcing would not make a naive one-node/one-head conversion valid. [OSM traffic-signal modelling](https://wiki.openstreetmap.org/wiki/Tag:highway%3Dtraffic_signals).

OSM also asks contributors to map verifiable ground conditions and avoid distorting correct data for a particular renderer/router. For this case, first trace the seven crossing nodes through the importer and validate the two reported vehicle stop controls. No upstream OSM edit has been made. [OSM good practice](https://wiki.openstreetmap.org/wiki/Good_practice#Don't_map_for_the_renderer).
