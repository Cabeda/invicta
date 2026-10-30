# Focused 701 delay inspection

This separate inspection records the **original failing bus-only control with imported signals enabled**, seed 17, on the unpromoted Alfena-corrected candidate. It does not reuse the public traffic-heavy animation or the rejected Combatentes geometry candidate.

The two windows follow `d1_bus_1` (Codiceira 05:45) and `d1_bus_55` (Codiceira 19:45) through the Combatentes–Marquês–Bolhão area. Vehicle positions and all selected signal-link states are sampled from libsumo once per second. The complete source network, all 127 services, timetable, bus parameters, seed, simulation warmup and end are preserved. Only output destinations are relocated. **All 6,024 native stop events match the frozen source exactly**; all 127 services complete. This is source-matched diagnostic observation, not transport qualification.

`capture.py` loads the self-contained frozen control ledger by default and verifies/materializes its native inputs. Native outputs go under ignored `native/`. Use a fresh native output directory for recapture; prior outputs must be retained elsewhere before rerunning. The captured implementation hash, source identity, command and output hashes are in `manifest.json`. `capture-index.json` binds that manifest and the compressed recording. The browser verifies recording bytes before decoding them; publication checks verify both files.

```sh
.venv/bin/python prototypes/line-701/focused-replay/capture.py
npm run build
python3 -m http.server 8776 --bind 127.0.0.1 --directory prototypes/costa-cabral/proposal
```

Open `/701-inspection/` on that server. The publisher copies only HTML, JavaScript, the compressed capture and its two manifests; it never publishes raw simulation inputs/outputs or runs SUMO in the browser. The existing vendor module supplies Three.js. 2D and 3D use the same selected frame; devices without WebGL retain 2D. Select the morning/evening service, scrub, play at 1–30×, jump between landmarks, pan/orbit/zoom or follow the selected orange bus. Other buses are blue. Language can switch between English and Portuguese.

The default is the evening bus at **20:25:30**, stationary inside Combatentes while its next downstream signal is green. This does not prove every internal movement is permitted. Signal symbols are schematic link-state markers at lane ends, not surveyed pole positions. Streets and crossing geometry come from the source native network. Buildings are deliberately omitted.

## Arrival and departure are separate

The table shows the selected service's designated timing points from source-matched native events. An early arrival can wait; an early departure cannot pass. The final destination is assessed by arrival. Ordinary intermediate request stops are not turned into extra holding points merely because the reference includes a passage time.

For the evening service, Areosa arrival is 20:12:29 and departure is 20:18:00: **5 minutes 31 seconds waiting for its scheduled departure**. Marquês arrival is 20:30:17 and departure 20:30:18, against 20:28:00. Bolhão arrival is 20:33:04 against 20:32:00.

Across the entire seed-17 control there are 587 departure checks (127 origins and 460 intermediate timing points), plus 127 terminal-arrival checks. **Zero departures are early**; 571 are exactly on time and 16 are late under the strict test. At 444 intermediate checks, an early arrival waits and departs exactly on time. Holding uses the source model's assumed parking bays; physical space and effects on other road users are unvalidated. No ordinary traffic, passenger boarding or actual nighttime signal programme is represented.

A poorly distributed timetable is a valid hypothesis, but these generated signal plans cannot establish that the official timetable is wrong. Keep the official times fixed while diagnosing the signal/junction model, then compare any timetable-revision hypothesis separately.

## Signal source mapping

`audit_signals.py` traces the selected native controller to its original OSM node tags, the route-filtered official Porto equipment layer and every generated movement link/phase. It writes `signal-audit.json` and its byte/network binding. Run it separately from capture; it never edits signal control or vehicle trajectories.

The viewer initially drew every movement link as a coloured circle, which could look like extra physical traffic lights. It now defaults to the selected bus's next logical links, and explicitly distinguishes the full movement-debug overlay from neutral municipal equipment locations. Neither view is a verified physical signal-head assignment. The user-reported two vehicle signals on the pictured Costa Cabral stretch remain a mapping constraint to validate.

The local review-layer extract has 16 equipment records sharing installation string `121`; unknown head types, movement assignments and timings remain unknown. Seven source OSM nodes are tagged signalised crossings. SUMO builds five represented junctions into one actuated controller with 21 movement links on 14 incoming lanes. The inbound route passes links 1, 7 and 17 in order. The programme's 24 nominal phase durations sum to 288 seconds, but actual cycle length is variable and not field-observed. The official equipment locations did not generate the signal programme.

See the [mapping investigation](../../../docs/research/701-combatentes-signal-mapping-2026-10-30.md). The new layers change only presentation; the recorded native inputs, phases, delays and original failed result remain unchanged.

The source layer can show the seven original OSM signalised-crossing nodes, with links to review each current OSM object. `?signals=osm&dimension=2d` opens that comparison directly. Frozen snapshot tags and current upstream OSM edits remain distinct: a verified correction needs a new extract/hash, reimport and native control; old results are not rewritten.

Active capture revision 2 corrects an inaccurate building-provenance sentence from revision 1. Both revisions are retained under `docs/research/701-focused-replay-2026-10-30*`. All sampled positions, signal states, geometry and timing rows are exactly equal across revisions; both native observations match every source stop event and tripinfo row. The active revision correctly states that no buildings are included.
