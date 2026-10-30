# Focused visual inspection and timetable holding

User request: show the failing section from Combatentes through Marquês to Bolhão, so he can inspect possible model errors. Follow-up: verify whether early buses can wait at stops and leave on schedule, without ordinary traffic and with traffic lights enabled. Consider an uneven timetable as a hypothesis, while keeping the current timetable fixed first.

- Export a separate diagnostic replay of the actual failing existing-signals control, not the older traffic-heavy public animation or the rejected geometry candidate.
- Preserve all source native inputs, bus parameters, seed, warmup and complete scheduled service. Observe positions/signal states once per second; verify exact stop-event equality before publication. Keep completion and source identities explicit.
- Show the prepared inbound Combatentes–Marquês–Bolhão area, with the early and evening failing services selectable. 2D/3D share the same native frame. Provide playback, scrubbing, landmarks, orbit/pan/zoom and optional bus following.
- Show actual observed waiting/speed/next-link states without claiming causality from a downstream green. Signal marker positions are schematic; imported timing plans and holding footprints are unvalidated. No passenger or ordinary-traffic feasibility claim.
- Separate native arrival and departure at designated timing points. Show early-arrival holding and late departure; grade the final destination by arrival. Do not invent holding at every interpolated intermediate passage time or alter the timetable to fit the result.
- Publish through the existing static-site build, verify asset integrity and retain bilingual UI. Keep the main proposal/reliability decision unchanged. This is inspection evidence, not a qualifying transport proposal.

## Follow-up: the pictured extra signals

Cabeda reports eight displayed signals where the pictured Costa Cabral stretch has two vehicle signals, and asks how official-source data was mapped into SUMO. Audit the actual chain: municipal equipment points, OSM crossing/signal tags, inferred node joins/programmes, route stop controls and viewer markers. Distinguish head/pole count from movement count. Do not silently delete native controls or relabel a display change as improved punctuality. Keep the user observation as an unresolved mapping constraint until the two physical signals can be assigned to approaches. Provide separate, clearly labelled municipal-inventory and model-movement layers, preserving their provenance and uncertainty.
