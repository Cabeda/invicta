# 701 follow-up: what the small probes establish

The unchanged target remains all 127 scheduled trips, both directions, exact departures at designated checks and terminal arrivals no later than scheduled. **No passenger-service proposal has met that target.** These are bounded diagnostic experiments, separate from the 34 frozen full-service executions and the older animated replay.

## The first Codiceira–Ermesinde interval

The reference remains 05:25 → 05:33. Each probe keeps the original warmup, bus routes, complete timetable reference and requested physical demand. Empty probes have no ordinary traffic or passengers. Each new stop probe changes one aspect of its identified parent; the zero-dawdling parent remains an unvalidated sensitivity.

| Profile | Ermesinde arrival / departure | Strict target | What it establishes |
|---|---|---|---|
| Original empty control | 05:33:18 / 05:33:19 | Fail | Previously reproduced, unchanged control. |
| Zero dawdling, original request-stop entries | 05:33:04 / 05:33:05 | Fail | Previously recorded sensitivity; not calibrated driving. |
| Zero dawdling; omit 20 unused request-stop entries before Ermesinde | 05:32:54 / 05:33:00 | Pass at this checkpoint only | Request-stop handling contributes to the residual. The bus can hold until its departure reference in this optimistic model. |
| Original driver setting; omit the same 20 entries | 05:33:13 / 05:33:14 | Fail | Removing those entries alone does not solve the original diagnostic. A fixed seed does not guarantee unchanged random-number consumption after changing a stop plan. |
| Zero dawdling; two checkpoint stops changed from parking to in-lane | 05:33:04 / 05:33:05 | Fail | Off-road checkpoint holding does not explain the residual in this empty case. |

The pass above is **not** a proposal to remove passenger stops or to assume perfect drivers. Removing unused native stop entries can affect lane guidance and slowing as well as stop handling. One-second traces can miss short road fragments, so different sampled-lane sets do not by themselves prove a different driven route. The original bus routes remain byte-equivalent in their edge lists. These probes cannot establish feasible passenger boarding or a surveyed stop layout. SUMO documents request-stop skipping and the distinction between a zero-duration physical stop and a waypoint. [SUMO stop semantics](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#stops-and-waypoints).

## Queue mechanisms and restoration limits

At the proposed-layout queue head `background_14_176`, paired 60-second snapshot analogues travelled **0 m in both branches**, whether one or three consecutive keep-clear checks were disabled. Those local changes did not release that vehicle in these tests. Its examined continuation lanes permit passenger vehicles; the inspected best-lane data retains a valid continuation. This is insufficient evidence to blame a specific reserved lane, propose removing a restriction or identify how the queue began. The physical cause remains unclassified.

The baseline snapshot exposed a separate reproducibility issue. The frozen final trip output reports 1,982.80 m travelled. Reloading the preceding snapshot starts at the same 1,982.80 m, but one unchanged native step reaches 1,983.8537 m; it does not match the archived final distance within the output's 0.01 m precision. The longer unchanged snapshot analogue also moved. **These saved states are useful for inspection, but are not verified continuations of the original execution.** Initial vehicle-state fingerprints match between each probe's control and variant; that is weaker than matching the original continuation. Python controller memory is not resumed. [Documented SUMO state limitations](https://sumo.dlr.de/docs/Simulation/SaveAndLoad.html).

Disabling keep-clear checks is a model-mechanism sensitivity, not a street design. The paired cases recorded zero collisions, which does not establish safety. The existing `inspect` command still executes zero steps; `probe-state` explicitly advances a bounded diagnostic analogue.

## Replay from the original warmup

An unchanged proposed-layout replay was limited to 180 native computation seconds. It reached **08:00:47**, observed 13 completed scheduled buses and matched **all 855 completed bus calls** against the archived full run through that cutoff. Input XML bytes match the original execution. No unexpected 300-second bus wait was captured before the budget ended. The known afternoon queue remains unexplained by this morning window. Future scheduled trips are outside the observation window, not evidence of cancelled service.

That first attempt terminated with a budget exception. Its original failure and partial outputs are retained unchanged; a separately labelled post-run audit verifies inputs and completed calls. The runner now closes a diagnostic budget stop normally, records its actual cutoff and preserves an evaluable `reproduction.json`. A native regression checks that a budget-limited run cannot pass its unobserved target or claim equivalence from zero compared calls. The long replay was not repeated merely to exercise this metadata fix.

Short diagnostics now separate the complete research goal from their observed window. At the first-interval cutoff, two timing checks are due and 712 remain in the future; neither probe has an observed missing check. The original-driver stop probe has one observed late check. Derived `diagnosis.json` reports make this distinction without changing the frozen execution metadata. Future trip deadlines are no longer listed as observed unfinished service. Paired state probes also preserve their branch reports when their budget ends, including a valid zero-step case.

## Report the right target

The signed public contract defines departure indicators with their own windows and a completed-trip denominator. They differ from this project's stronger exact-second test. The [definition audit](701-punctuality-definition-2026-10-30.md) identifies the precise events, source pages and limits. Neither those windows nor minute-valued API timestamps justify changing all 714 checkpoints or hiding the 42 unfinished candidate trips. Public explanatory text and exports now make the distinction explicit; no contractual-compliance percentage is invented.

## Next decision

Keep the current package rejected. The next traffic remedy needs an onset trace from the original warmup or a smaller boundary-validated reproducer of the afternoon queue. Native saved-state analogues cannot supply that proof. Review request-stop handling against observed driving/boarding before accepting a new vehicle profile; retain the flagged stop-coordinate reviews. Once those model questions have evidence-backed dispositions, compare conditional priority and holding, then verify complete service and passenger/access impacts before ranking smaller interventions.

The [evidence manifest](701-followup-2026-10-30/manifest.json) binds seven new cases, frozen implementation witnesses and shared original input archives. Snapshot variants are represented by small exact XML replacements with a checked resulting-network hash, avoiding duplicate regional maps. Commands are in the [native README](../../prototypes/line-701/full/README.md#investigate-before-another-priority-search-run); scope is recorded in the [follow-up specification](../product/diagnostic-followup-2026-10-30.md).
