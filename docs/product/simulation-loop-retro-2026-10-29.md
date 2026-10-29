# Retrospective: make the simulation loop produce a feasible proposal

Reviewed the current session and repository at `c03bfd82e0f6d16eaff24a660f2eca4690945fb0`. The objective remains the published 701 timetable, with complete service and workable passenger and local access. This review recommends changes to the investigation workflow; it does not establish a compliant transport proposal.

## What the evidence says

| Evidence | Implication |
|---|---|
| 34 archived executions; 30 now superseded; six include ordinary traffic | Much of the work investigated model versions rather than narrowing a proposal on one accepted model. Superseded experiments remain useful audit history, but cannot qualify the current proposal. |
| Current empty diagnostic: 22.91 s of execution, one checkpoint 19 s late | A cheap test still exposes an unresolved model/timetable fit issue. It is an optimistic diagnostic, not a certified physical lower bound. |
| Current full-traffic runs: 1,210.62 and 1,258.59 s | Expensive runs need prerequisites and a specific hypothesis. The runner currently accepts either configuration directly. |
| Current package: 85 completed trips versus baseline 119 | The next useful result is an explanation of the unfinished trips that selects a controlled next experiment. |
| Existing checks: 53 JavaScript, 28 Python and four browser tests | Guardrails exist and run in CI. The missing checks concern model readiness and experiment decisions, rather than another general lint policy. |

Durable evidence: [trial ledger](../../prototypes/line-701/full/priority-search.json), [native runner](../../prototypes/line-701/full/priority_search.py), [archive verifier](../../prototypes/line-701/full/priority_ledger.py), [check command](../../scripts/check.mjs), [CI](../../.github/workflows/check.yml). Runtime totals come from original execution metadata. Local file timestamps suggest most full-run time is in native execution, but phase timings are not recorded; no engine speedup is assumed here.

## Recommendations, in priority order

### P0 — Put model readiness and diagnosis before expensive experiments

`run_trial` builds inputs and starts the full service day without consulting a model audit or an earlier diagnostic. I ran expensive cases while the empty diagnostic remained unresolved. Two wrong route matches were discovered late, invalidating comparisons across successive imports.

Introduce a **ModelAudit module** that checks both directions, served trip patterns, stop footprints, route deviation from the operator shape, speeds, lane connections and physical OD preservation. Move cheap workload/permission checks currently performed by archive verification into scenario compilation as well. Classify inputs as frozen evidence, uncertain assumptions or proposed interventions. Demand and vehicle physics must not become convenient optimisation variables.

An unresolved empty-case failure should lead to a targeted diagnosis before more traffic-only packages. It must not automatically declare the real timetable impossible. Public-data gaps should become explicit sensitivity cases; modelled feasibility and field validation are separate outcomes.

**Completion:** the experiment planner explains why a full run is justified, or returns the specific model issue and a small reproducible case.

### P0 — Produce explanations at the first failure

The runner grades after the whole day. State capture was only added recently, at the end; progress and controller logs provide little help while a bus becomes stuck. The session needed several temporary inspection scripts to follow leaders and signals.

Introduce a **Diagnostics module** shared by passive runs and signal-priority runs. Capture bounded traces when a bus first misses a checkpoint or remains unexpectedly blocked: position, intended movement, leader chain, junction conflicts, signal phase, boarding, occupancy and scheduled holding. Separate delay inherited from upstream from delay added in the current interval. Return “unclassified” when the evidence does not establish a cause.

Record preparation, routing, native execution, evaluation and publication times separately. A code-first `inspect`/`diagnose` interface should show the worst few failures and their source identities without dumping one-line XML or large JSON documents.

SUMO snapshots can speed diagnosis, but [its documented state limitations](https://sumo.dlr.de/docs/Simulation/SaveAndLoad.html) include unsaved vehicle-model state and platform-dependent random state. Our Python controller also has its own memory. Reuse states across identical, verified prefixes only after equivalence checks; changed networks or earlier policies require new executions. Local diagnostic windows never substitute for final full-day verification.

**Completion:** one command reproduces and explains the first relevant failure without another full-day run.

### P0 — Unify the objective, experiment results and promotion path

There are two decision paths. `web/punctuality.mjs` and `web/study-reliability.mjs` assess the older published study. The newer Python search has another evaluator and reaches the page through an optional research panel. Its ledger intentionally forces `qualified:false` and `winner:null`, and rejects a qualified result. That protects against unsupported field claims, but there is no route for a future simulation-compliant candidate to enter the main proposal workflow. All 34 existing runs also fail their actual timetable checks; the guard is not the cause of those failures.

Create one versioned **Goal/Evaluation module** consumed by the runner, optimiser, report and browser. Prefer the existing JavaScript domain evaluator as the authority, with a small JSON command interface for Python native adapters. Expand its result to retain every checkpoint failure and relevant passenger/access constraints. Preserve observed calls and all missing demand.

Expose three independent decisions: compliance in the declared simulation; robustness across required cases; readiness for field claims. Model vehicle circulation, turnaround and reserve resources explicitly before claiming origin resilience: the current native study inserts independent scheduled workings. Minimal-change ranking should account for controllers, stop works and fleet/driver resources as well as lane length.

**Completion:** a passing synthetic fixture can become a clearly labelled simulation-feasible candidate; a failed fixture remains rejected everywhere. Neither can masquerade as field validation.

### P1 — Add a search coordinator, rather than manually accumulating packages

The current CLI executes one JSON configuration. Lane permissions, boarding, request stops, signal priority and holding are often changed together. There is no orchestrator selecting the next intervention from a diagnosed failure, or testing whether an individual change is necessary.

Define a finite intervention catalog with locations, resources and effect assumptions. Test controlled changes on the same accepted model and physical demand. Use fast discovery cases to shortlist; then run the complete required demand/seed matrix. Once feasible, remove changes and reverify to identify which are necessary in the tested set. Keep the search heuristic distinct from acceptance: a less-bad failed package is not a winner or a proven global optimum.

**Completion:** each trial records the hypothesis, single change or declared interaction, baseline pairing and next decision. Search stops on budget, a model blocker or a verified candidate.

### P1 — Separate reusable execution from evaluation and presentation

Immutable trial folders and source/output hashes are strengths. However, human trial IDs do not provide automatic reuse by content. `build_site.py` also includes report prose in the proposal's `reference_id`, while new numerical results and the existing replay belong to different studies.

Use separate identities for model preparation, physical demand, native execution, evaluation and presentation. Native identity includes controller implementation/version and capture settings. Changing a goal reevaluates frozen events; changing report text updates presentation. Neither requires new vehicle physics. Reuse a matching completed execution through a run registry, while preserving the original archive.

Publish one **ProposalBundle** joining the selected intervention plan, evaluation, evidence maturity and matching replay coverage. The website can display an exploratory or rejected bundle, but its status must derive from data, and footage must retain its actual source identity.

**Completion:** prose edits preserve numerical compatibility; repeated identical experiments reuse evidence; a new candidate enters the same public workflow without another research-only path.

### P2 — Extract the reusable study interface after the first end-to-end slice works

The browser line registry already supports another line. The native runner still imports 701-specific `DATA`, OD pools and access screens, emits `701_` identifiers and exports a ledger fixed to line 701. UI extensibility is ahead of simulation extensibility.

Pass an explicit **StudySpec** containing line identity, frozen references, model, demand, goals and intervention catalog into the modules above. Keep acquisition as line-specific adapters. Retain current URLs and archives during extraction. A broad directory rewrite should follow a working 701 investigation path rather than delay it.

Keep the existing release checks. Split fast contract checks from full archive verification, verify an immutable archive once per evidence/evaluator identity, and preserve the full evidence check as a release gate. The current test file independently verifies the full ledger twice.

## Concrete environment correction applied

The existing [prototype requirements](../../prototypes/costa-cabral/requirements.txt) already pin `rtree==1.4.1`, but CI installed a separate list without it. SUMO's nearby-road search silently falls back to scanning the network when that optional import is absent.

A [recorded local comparison](spatial-index-benchmark-2026-10-29.json) used the 175,415-edge version-5 network: ten searches took 5.8337 s without the index versus 0.0023 s with an already built index; building the index and first query cost 4.6765 s. Both returned the same edges. This measures spatial queries, not a full traffic simulation, and does not imply a comparable speedup of the 21-minute native run.

CI now installs [one simulation environment](../../requirements-simulation.txt), which reuses the existing pins and adds the controller runtime. A native-index smoke check catches missing compiled support. Regional route/OD matching now fails immediately instead of silently using brute force. The existing actual-network route regression verifies the indexed path.

Reproduce the bounded measurement with [the benchmark tool](../../scripts/benchmark-spatial-index.py):

```sh
.venv/bin/python scripts/benchmark-spatial-index.py \
  --network .cache/701-optimisation/model-v5/baseline.net.xml \
  --reference .cache/701-optimisation/model-v5/routes.json
```

## Next implementation slice

Build **model audit → first-failure diagnosis → one controlled intervention → full-day verification → one proposal bundle**, using the first Codiceira–Ermesinde interval and the unfinished-trip queues as concrete cases. Extend the pre-agreed loading, evaluation and browser/export test seams. The outcome should be a reproducible explanation and a targeted next experiment, with a path to a simulation-feasible proposal.
