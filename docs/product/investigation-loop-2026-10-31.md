# A repeatable investigation loop for bus lines

Cabeda authorised about two hours of autonomous work to make simulation, bottleneck analysis and targeted fixes cheap and repeatable. The first line is 701; the workflow must accept future line references without copying 701-specific stop names or directories into its analysis.

## Public interface and acceptance

Extend the already agreed evaluation and replay/export interfaces. Native traffic remains SUMO's responsibility. The loop consumes the verified `TrialEvidence` interface and retains the complete timetable and demand. Each line/session gets an independent workspace and a resumable journal.

1. **Triage without rerunning physics.** Recalculate strict and operational outcomes. Identify intervals that add delay, distinguish inherited lateness and recovery, and retain origins, destinations and missing events. Report recorded stop service, scheduled holding windows, boarding/alighting and sampled non-stop waits without claiming these observations establish a physical cause. Ordinary vehicles stalled for hours are model-quality cases even when bus timing passes. Partial and optimistic diagnostic executions cannot qualify.
2. **Package one problem.** A dossier identifies its exact model, reference, run, direction, trip, stop interval and time window, plus relevant trace observations and geometry. The selected replay must use that same identity; a late destination is not automatically the bottleneck. Diagnostic continuations and coarse sampled traces are labelled separately from matched one-second recordings.
3. **Reproduce cheaply before changing a model.** Minimise the specific failure to a native case, retain the original red-capable assertion and actor-removal controls, then record 3–5 falsifiable hypotheses. Local success requires testing the original broader case before model promotion. A previously passing tiny case is insufficient when the regional failure persists.
4. **Test one change and retain the comparison.** Register the hypothesis, the changed parameter or source patch, its implementation identity, expected effect and regression command. Reuse exact paired physical inputs for controller-only changes. Retain rejected attempts and computation-limited executions. No silent timetable/speed/randomness changes or removed requests.
5. **Promote through gates.** Empty model → passengers/walkers → traffic ramp → paired full-day matrix in both directions and multiple seeds. Require every scheduled service and timing check, no early departures, the explicit 60-second operational criterion alongside strict results, no collisions or concealed unserved demand, and reviewed access constraints. Compare minimal interventions only among qualifying packages; a model correction is never a street benefit.

## Efficiency and autonomy

Reuse hash-verified results, keep fast native cases separate from expensive full-day qualification, bound each computation, and deduplicate immutable network bytes. Journals retain the next action, failure reasons, evidence locations and consumed computation time so an interrupted session resumes. Do not repeatedly rerun an unchanged failed hypothesis. The agent performs the analysis and patches; the executable workflow supplies deterministic evidence and gates, not unsupported automatic causal conclusions.

During the authorised session, proceed without routine questions. Preserve public-data-only assumptions and report missing observations rather than inventing calibration. At the session boundary, report verified progress and unresolved conditions. Push reviewed changes to main; deploy visual changes only with their exact source recording and clear coverage.

## First cases

The regional Areosa blockage remains unresolved despite a passing three-actor detector regression. Strengthen that reproducer to catch the remaining pattern before another correction. Separately analyse passenger-only added delay between timing points, particularly Ermesinde–Codiceira and the inbound approach to Marquês. Do not use the older public bus-only replay as visual evidence for the current passenger-and-traffic case.
