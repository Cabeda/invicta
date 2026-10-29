# Invicta production application

This specification follows the 29 October request and supersedes the prototype page hierarchy. The release baseline is `ce1dfee`.

## Public purpose

Help people assess a proposal for reliable buses and workable everyday access. Lead with the desired outcome, explain the proposed street changes, let people inspect the same traffic simulation in 2D or 3D, then disclose the evidence and implementation conditions.

The goal is every scheduled trip departing its own origin at the published time and reaching its own destination no later than its published arrival. A trip is one scheduled departure in one direction, including short services. Completed journeys alone are not punctual journeys. Missing arrivals fail the goal and remain in its denominator. Early departures fail it. The initial late tolerance is zero seconds, made explicit rather than hidden.

## Product hierarchy

1. Purpose: a dependable bus, access to homes and businesses, fewer changes where possible.
2. Line: choose a registered line and direction; explain its geography and daily service.
3. Proposal: what changes, where general access stays, the minimum-change objective and the current evidence status.
4. Experience: synchronized 2D/3D native replays, baseline/proposal comparison and playback controls.
5. Proof: departure and terminal-arrival punctuality, unfinished trips, regional access impacts, timetable and sources. Technical counters are explained and disclosed here.
6. Delivery: survey and calibration, targeted tests, a reversible pilot and measured expansion. Costs and commitments need evidence; unknown amounts remain unknown.

The current synthetic study does not demonstrate a policy that makes every trip punctual. Presenting that failure clearly is necessary. Persuasive language concerns the benefit sought and the testing process, rather than an unsupported promise of success.

## Extensibility

A validated line registry owns identity, localized descriptions, data and reference URLs, native coverage and optional analysis capabilities. Selecting an unknown line produces an explicit error. Adding a line must not require a new page or another copy of the traffic renderer. Native study adapters supply the data contract and maintain their own provenance.

The shared replay engine owns verified assets, decoding, frame interpolation and policy-specific bus selection. Canvas2D and Three.js render the same trajectories. Links preserve line, direction, section, policy, time, language, 2D viewport and 3D pose. Neither renderer substitutes a capture for an unprepared policy.

## Minimum-change decisions

Evaluate the complete scheduled service and required demand cases before ranking changes. First require punctual departures and terminal arrivals, complete service, matching requested demand and no additional unserved demand. Then minimize changed lane length, with change count as a tie-breaker. A winner among tested packages is not a proven global optimum. Missing tests or costs cannot become zero-cost evidence. If no tested package meets the constraints, say that no qualifying proposal has been found and identify the unmet criteria.

## Release requirements

One documented check command covers module syntax/type checks, domain tests, native publication tests and static asset contracts. CI runs the same checks on pushes and pull requests. Public site data loads through the registry rather than a large JSON document embedded in HTML. Generated output matches source, source/capture hashes remain auditable, and unsupported coverage fails clearly. Validate both views, direction switching, draft rejection, mobile layout, shared state and video sidecars before deployment.

Production software readiness and transport-model validation are separate: the latter still requires observed counts, full-line arrival/departure data, operator fleet blocks and verified street access/signals.
