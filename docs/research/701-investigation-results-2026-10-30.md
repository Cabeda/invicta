# 701: a reproducible first-failure investigation

The first audit/diagnosis slice is implemented. It establishes a faster investigation loop; **no timetable-compliant proposal has been found**. All current full-day results and the complete 127-workings / 714-check objective remain unchanged.

## Results

| Check | Recorded result | Decision |
|---|---|---|
| Current model audit | Three stop coordinates need review: inbound COD 26.960 m; outbound BRO1 30.652 m and COD4 46.796 m. The empty diagnostic also retains one late checkpoint. | Block another full traffic package pending diagnosis. The 25 m trigger is a project review screen, not a planning standard or proof of a wrong match. |
| First failed interval | First inbound `d1_bus_0`, Codiceira 05:25 → Ermesinde 05:33. Budget 480 s; observed 499 s; inherited delay 0 s; added delay 19 s. | Inspect this interval before attributing its failure to ordinary traffic. |
| Unchanged prefix, original 05:00 warmup → 05:35 | All 25 completed bus calls match the archived empty execution. Ermesinde departure remains 05:33:19. Native execution 8.38 s; input preparation 0.72 s; evaluation 0.18 s. | The short control reproduces the target. This is stop-call equivalence, not trajectory or resumed-state equivalence. |
| Same prefix, bus `sigma` changed from 0.5 to 0 | Ermesinde departure 05:33:05: 14 s less late, still five seconds late. Native execution 8.21 s. | Uncertain vehicle-behaviour sensitivity; still fails. It is not a physical intervention or an acceptable way to tune a model into success. |
| Final baseline state | Eight active buses, all outbound; first waiting bus `d0_bus_56` on `482331424#8_1`. | The reported unfinished service is present in native state. Physical cause remains unclassified. |
| Final candidate state | 42 active buses; bounded contexts show queues affecting both directions. | The candidate remains rejected. A signal, leader or foe is an observation, not proof of a junction defect. |

Both saved-state inspections read native time 99,299 (27:34:59) and execute **zero simulation steps**. Active buses at a snapshot and final unfinished-trip counts are separate measures; they coincide in these two cases. Context capture is bounded to 16 vehicles per selected bus. No traffic forecast, safety validation or field calibration is established.

At the first overdue second, the control bus is moving, with no reported leader or junction foe in that captured context. That observation does not explain the whole 499-second interval. The signal-off diagnostic remains an optimistic experiment, not a certified physical lower bound. Geometry, stop semantics, source timetable interpretation and unvalidated vehicle behaviour remain possible model issues. Public data has not resolved those uncertainties.

## What changed in the workflow

The native runner now refuses an expensive new search configuration without a bound ready model and a stated change, prediction and supporting evidence. An explicit empty control can bootstrap readiness. A passing synthetic native fixture demonstrates the success path; a prefix cannot supply full-service readiness. New configurations cannot disable signals while carrying ordinary traffic under the guise of an empty control.

Compiled-input checks preserve scheduled bus paths/calls, physical ordinary-vehicle endpoints/departures, passenger/walking counts and pedestrian permissions before execution. Passive and priority-controlled trials share one observed native runner. New runs retain implementation copies, package versions, first pending-deadline and prolonged-wait snapshots, bounded traces, progress and separate preparation/execution/evaluation/verification timings. A native fixture checks that observation preserves passive CLI stop calls.

The frozen current-model empty and bus-only trials now include their original native input XML through the archive. Identical input bytes reuse an existing archive descriptor. Original result metadata, physical requests and numerical outcomes are unchanged. The two prefixes write `reproduction.json` and are not added to the 34 full-service executions.

The conservative audit gate has no reviewed-disposition mechanism yet. Geometry screens and unexplained optimistic misses need evidence-backed review, not arbitrary parameter adjustment. Canonical evaluation across Python and JavaScript, conditional priority, controlled intervention search, robust multi-seed acceptance and proposal promotion remain later slices. See [the accepted scope](../product/investigation-slice-2026-10-30.md) and [the research on best practice](bus-reliability-best-practices-2026-10-30.md).

## Reproduce and inspect

Commands and exit semantics are in the [native study README](../../prototypes/line-701/full/README.md#investigate-before-another-priority-search-run). Use `investigate.py diagnose`, `reproduce` and `inspect` against `priority-search.json`, selecting one trial. Add `--bus-sigma 0` only to request the explicit uncertainty sensitivity. The preserved native input/reference remains the frozen 28 October 2026 service; this investigation does not substitute a new timetable.

Evidence: [audit](701-investigation-2026-10-30/model-audit-v5.json), [baseline state inspection](701-investigation-2026-10-30/baseline-final-inspection.json), [candidate state inspection](701-investigation-2026-10-30/candidate-final-inspection.json), [prefix archive manifest](701-investigation-2026-10-30/manifest.json), and the original [full-day ledger](../../prototypes/line-701/full/priority-search.json). The prefix manifest binds compressed outputs, input bytes and frozen implementation witnesses. Shared descriptors point to the existing original native archive. No prefix is used to claim full-service compliance or to relabel the older public animation.
