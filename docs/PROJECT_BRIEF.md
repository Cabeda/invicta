# Invicta: agreed project focus

Clarified by the user on 28 October 2026.

**Primary goal: help buses meet their published schedules while catering to the everyday needs of local residents, shoppers, businesses and services.**

The user further clarified that effects on **all travellers** matter, including non-residents travelling for work/study, shopping, leisure/walks and other needs. Explain immediate effects separately from conditional longer-term mode shifts. Show person-trip-weighted mean time, bus punctuality, who remains worse off, and all unserved requests. A lower average does not establish a gain for every individual.

**Current pilot unit:** line **701 towards Bolhão**. Detailed native street simulation now covers the whole Porto municipal extent, about 60m before **Areosa ARS3 → Bolhão 0BLRB**, including both Marquês stops, Doze Casas and Fontinha. The whole-line operational layer separately covers all 56 stops and 63 inbound workings, including the shorter Ermesinde workings. Identify where general car flow should remain through connectivity and real access needs; a blanket restriction is not assumed.

**Reliability goal:** evaluate the whole service and cascading effects, not only mean time on Costa Cabral. Track lateness at all designated timing points, early departures, consecutive-bus headways, passenger queues and boarding capacity. A delayed bus can collect more passengers and slow further while the next bus catches up. Test the same demand without the injected delay, and retain failures. The strict zero-lateness model target follows the user's goal; it is not an operator-agreed tolerance or a guarantee of actual operation. Vehicle rotations, reverse-direction service and road conditions outside Porto need matched evidence before such a guarantee could be claimed.

## How alternatives should be assessed

- Measure arrivals against the timetable at relevant stops, and departures that occur too early. Also show reliability, headway regularity and upstream lateness so corridor effects are not confused with delays arriving from elsewhere. Agree acceptable early/late tolerances with the operator before using them to rank real proposals.
- Treat practical local access as an explicit requirement: reaching homes and shops, accessible boarding and walking routes, legitimate visits and care, deliveries/loading, servicing and emergency access. Record access by mode and destination, including available parking/drop-off approaches where relevant, rather than treating every local need as an exemption for a private car.
- Keep requested journeys and unmet demand visible. A scenario cannot appear successful merely because difficult journeys have disappeared from the calculation. Report effects on neighbouring streets and affected groups.
- Compare feasible alternatives on bus punctuality and local access first; then explain passenger time, cost, operational complexity and implementation phases. If no alternative meets both requirements, show the conflict and the evidence needed rather than hiding it in one weighted score.
- Test bus priority by stop interval and as a combined package. Preserve the existing imported geometry and lane counts in the baseline; keep restrictions separate from changes to signals or street design. Also consider supporting measures such as signal priority, stop operation and loading arrangements when the evidence justifies them.
- Use sourced population and mode-share inputs with their geography, year and denominator intact. Population is not daily trips; person-trip shares are not fleet percentages. The 2025 INE metropolitan population, 2017 IMob references and PMUS survey profiles can inform explicit scenarios, but are not a matched present-day OD demand set.
- Test the chicken-and-egg hypothesis rather than building it into the conclusion. Alternatives must be usable and attractive, and their capacity must accommodate the assumed shift. Show the no-switch case and adverse/no-break-even cases; do not assign a future adoption date without a validated model.

## What the current prototype establishes

The [route-first 701 pilot](../prototypes/line-701/README.md) has 16 current official Porto stops through Bolhão, five morning native journeys, three-seed package/interval comparisons, a generated-OD connectivity screen and timestamped GPS passage windows. MPL4 and 0BLRB are designated timing points in Porto; other published seconds are intermediate references. A separate assumed whole-line service model covers 3,024 published calls, passenger/dwell feedback, capacity and berth/headway controls. Native results distinguish entry lateness from added delay and retain all unserved requests. No calibrated real-world benefit is established. Other bus lines are not yet included.

The candidate retains general flow in the first two intervals and Marquês→Doze Casas→Fontinha because some generated connector pairs become unreachable. It still has operational failures: 12/15 completed bus stop sequences in the busy case, and worse arrival deviation in the late-entry case. A connectivity pass is not proof of capacity or workable access. One evening trajectory flags Pires de Lima→Combatentes for repeated observation; it does not establish a recurring cause. Missing endpoint coverage prevents claiming observed full-section punctuality.

The earlier street access/routing rule remains runnable in the archived study. It retains buses, synthetic local resident permits, taxis, bicycles and motorcycles; ordinary cars may directly cross junctions. The shopper/service-access policy has not been defined or simulated, and this clarification does not silently grant additional vehicle exemptions.

The earlier street study used an **illustrative final-modelled-stop arrival no more than three minutes late**, with unfinished bus trips counted as failures. It is not an agreed operator standard, an early-departure check or a validated assessment of whole-route punctuality. The traffic, signals, dwell and local permits remain assumptions. Faster completed bus trips alone do not demonstrate that the primary goal has been achieved.

The baseline has been corrected: it preserves the unmodified frozen-OSM SUMO import, with the one-lane-per-mapped-direction adjustment only in the proposal. This is still an unvalidated import. Earlier results using a standardized baseline are superseded; the corrected moderate-demand bus means are about 9.86 → 9.85 minutes, with higher unserved demand in the proposal.

The [population transition calculator](../prototypes/costa-cabral/TRANSITION.md) is a separate, transparent what-if model with sourced population/mode references and assumed travel times, access penalties, capacity and adoption. It does not simulate 1.86 million individual residents on the clipped corridor network.

See [report input and scorecard priorities](research/costa-cabral-report-variables.md), [3D inspection options](research/3d-street-inspection.md), and [current experiment limitations](../prototypes/costa-cabral/FINDINGS.md).
