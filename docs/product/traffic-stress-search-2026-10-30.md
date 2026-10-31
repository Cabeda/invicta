# Traffic stress and a minimum-change 701 proposal

Cabeda authorised raising traffic to reproduce delays, then searching for the smallest intervention that meets the official timetable. The reference remains the frozen 28 October operator timetable: both directions, 127 scheduled services and 714 designated timing checks. Evaluate strict seconds and the explicitly chosen operational allowance of 60 seconds; never permit early departures. Missing calls or unfinished buses fail either criterion.

## Accepted investigation scope

- Increase ordinary traffic using deterministic nested subsets of the existing synthetic busy catalogue. Preserve every selected request's ID, mode, physical endpoints and departure. The percentages are workload fractions, not measured Porto traffic or a population forecast.
- Isolate traffic, passenger boarding and pedestrian demand before combining them. Retain the denominators and unserved demand. Faster boarding requires an explicit operating assumption; instantaneous boarding and empty buses are diagnostic bounds.
- Compare signal-only policies on exact verified physical inputs. Bound green extensions to at most 10 seconds, preserve phase order and yellow/all-red intervals, and retain pedestrian green by default. A separately declared pedestrian-green shortening sensitivity retains occupied-crossing checks and a slow-walker clearance bound. It is not a surveyed safety plan.
- Search controller subsets before proposing lane restrictions. Count changed controllers and lane length, record failed alternatives, and describe any passing candidate as the smallest tested package only after checking access, unserved demand, collisions and multiple seeds. A bus-only punctuality pass cannot qualify a passenger-carrying service or establish a global minimum.
- The three previously flagged stop offsets may receive source-bound, explicit model-approximation dispositions for synthetic stress only. Bind operator/platform identity, frozen OSM, route fragment, retained berth, network and reference hashes. Do not silently move stops or call these surveyed placements.
- Reduce unexpected native stalls before treating them as street congestion. An Areosa regression must reproduce the three-actor stall, clear when any actor is removed, and test the detector correction across arrival offsets while retaining all original phase definitions. Apply model corrections equally to baseline and proposal and repeat the empty prerequisite in three seeds.
- Keep every trial immutable. Archive exact inputs, outputs, frozen implementation, failed attempts and revised model identities. Diagnostic computation limits must produce an explicit partial scope that cannot establish full-day readiness. Reusing identical inputs or sharing network storage must not change bytes or demand.

## Production boundary

These runs use uncalibrated demand, inferred signal plans, idealised holding bays and independent bus services. Vehicle blocks, actual detector positions, signal timings, demand observations and surveyed berths remain unvalidated. No experiment changes the public replay or qualifies a field proposal automatically. The delivered evidence must state whether the combined passenger-and-traffic case passes; a failed or incomplete search remains visible.
