# Combatentes signal mapping correction

Cabeda observed a bus crossing one light and stopping immediately again inside the Combatentes junction, where he reports only one vehicle control in reality. First explain the OSM-to-SUMO mapping, reproduce the extra stop in a native regression, then correct the conversion. Do not substitute hidden annotation markers for a physics change.

Acceptance for this slice:

- Keep a reduced, source-bound native network that reproduces the extra stop in each direction with a lone bus, without traffic or passengers. Keep the source failure as a permanent test.
- Apply an explicit, opt-in supported netconvert patch to the inspected junction. Keep external entry control and its generated phase table; remove repeated controls on roads wholly inside the reviewed junction footprint. Include the central priority node, which is outside SUMO's joined TLS membership.
- Bind the recipe to the frozen OSM and inspected topology/programme. A changed source must fail rather than silently reuse the patch. The frozen final network and the earlier import stage have separate fingerprints.
- Preserve vehicle movement permissions and pedestrian connectivity. Check opposing buses, every retained bus-movement pair and mixed bus/walking traffic with native collision checking; assert that every requested actor actually starts and finishes.
- Apply the correction in the existing conversion pass, then compare the resulting full model with the frozen control. Do not introduce an uncontrolled conversion pass that changes unrelated junctions.
- Retain all 127 scheduled trips, both directions, all 6,024 served calls and all 714 designated checks. Rerun the signal-enabled, traffic-free prerequisite at seeds 17, 29 and 41. Keep strict and 60-second project criteria separate, with no early departure permitted. Report any remaining failure honestly.

This is an inferred-model correction, not a real traffic-light programme or a proposed street intervention. OSM source nodes do not establish physical lamp-head count or actual phases. The two reported vehicle signals have not been assigned to surveyed stop lines. Walking connectivity checks do not establish complete crossing coverage or pedestrian signal clearance. No upstream OSM edit, bus-physics tuning, timetable relaxation, baseline promotion or field reliability claim is part of this slice.
