# Traffic-stress implementation review

Compared the working changes with `0477ef816970b443c783d4cbe14adf207c443424`. Independent Standards and Spec reviews used fresh contexts. The accepted scope is [traffic stress and a minimum-change proposal](../product/traffic-stress-search-2026-10-30.md); the scientific findings are in the [results report](../research/701-traffic-stress-results-2026-10-30.md).

## Standards

Three actionable findings were resolved:

- Prefix replay omitted the new controller subset, extension limit and green minimum. A shared configuration mapping now reaches both native execution paths; the regression checks native prefix equivalence and exact option propagation.
- The archive initially verified operational metrics only. It now recalculates strict and operational metrics from raw native outputs; a tampered strict score is rejected before `study.json` is published.
- A standalone signals-off diagnostic omitted its compressed first-deadline snapshot from the output index. Archival preserves it separately against its recorded, hash-bound monitor digest without editing the original result. A historical-omission regression verifies the bytes.

The earlier incomplete-attempt JSON-only omission and premature manifest publication were also corrected during review. Partial XML, traces and code are retained, and verification precedes promotion of the pending manifest. The final reviewer verified the snapshot, original result identity, report figures and quoted timetable times against the frozen archive. No blocking Standards findings remain.

## Spec

No outstanding implementation findings. Nested demand, exact paired inputs, bounded priority, explicit stop assumptions and partial-scope labelling match the accepted slice. The reviewer explicitly distinguished implementation acceptance from goal achievement: the combined passenger-and-traffic experiment still fails, and there is no qualifying minimum-change proposal.

## Validation

`npm run check` passed: syntax/type checks, 53 JavaScript tests, nine native replay tests, 87 full-study tests and public asset parity. The subsequently completed frozen-study acceptance check is included in the separately passing 13-test traffic suite. The Areosa native regression covers the original failure, removal of each actor, unchanged phases and 21 corrected arrival offsets. All 31 archived timing evaluations were recalculated successfully; four failed attempts remain separate.

The two-controller package was rejected on combined demand: 20 → 23 late operational checks and 18 → 28 unfinished ordinary requests. The public replay was not replaced and no field benefit is claimed.

Final review: Standards 0 outstanding (3 resolved); Spec 0 outstanding. Scientific goal: not achieved.
