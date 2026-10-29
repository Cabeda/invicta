# Proposal, line exploration and native replay

This implementation follows the three boundaries recommended in the 29 October architecture review. The browser consumes precomputed native results; SUMO remains the vehicle movement authority.

## Application and line registry

`web/line-registry.mjs` validates registrations, selects the requested line and checks its data/reference/native identity. `web/lines.json` supplies the catalog; data loads separately from the small HTML shell. `web/proposal-page.mjs` owns the public explanation and phased delivery story. The current 701 native adapter remains under its historical path; adding a line follows `docs/product/add-a-line.md`.

`web/punctuality.mjs` evaluates departures and destination arrivals, retaining the complete expected schedule and failing missing/early/late events. The minimum-change decision first requires every declared traffic case and seed to pass punctuality and access constraints, then minimizes approximate changed lane length. It distinguishes a qualifying tested package from a global optimum. The current published search has no qualifying package.

`scripts/build-reliability.mjs` applies the same domain evaluator to frozen native runs. The generated per-direction punctuality summaries are included in the canonical proposal data, so the public view and detailed evidence use the same results.

## Line exploration

`prototypes/line-701/line-explorer.mjs` owns official direction identity, ordered geometry and stops, independent selected trips, continuous focus sections and coverage decisions. `createLineExplorer(reference, state)` is usable without a DOM. The mounted view receives an existing model and reports explicit change types so a detail-panel toggle cannot silently select a different simulated journey.

The full official map and timetable reference remain independent of native coverage. The current full native study covers both complete directions; the earlier Porto study retains its narrower declared coverage.

## Proposal

`prototypes/line-701/proposal.mjs` owns the selection, versioned source reference, prepared policy masks for both directions, evidence, service settings, camera/replay state and eligibility. Its public operations are `restore`, `review`, `shareURL`, `dataFor`, `importArrivals` and `observations`. Rendering code collects controls into this model; reports and recording metadata do not reconstruct meaning from rendered text.

`proposal-views.mjs` adapts one reviewed snapshot to a plain-language citizen story and a detailed Markdown report. Both expose completion and unfinished demand. A faster mean among completed journeys cannot produce an overall-benefit claim while requested journeys remain unfinished. The independent passenger/berth service model retains its own assumptions and inbound coverage.

Shared links contain the canonical `invicta.proposal.v1` selection in the URL fragment. Importing a proposal or recording sidecar restores the same selection. A source-version mismatch suppresses current native claims and evidence interpretation while preserving the original raw uploaded arrivals, including rows whose trip IDs no longer exist. Imported arrivals remain user-supplied evidence.

The renderer never substitutes a prepared policy for a draft. A recording freezes one reviewed snapshot and locks incompatible controls. Its WebM and JSON sidecar share the same proposal ID and include actual capture sources, camera pose, time window and selected focus. Finalizing one recording prevents a new session from mixing its buffers.

## Native replay preparation

`prototypes/native_replay.py` owns scene construction, inherited-footprint projection checks, source-based cache invalidation, capture/scene compatibility and publication of `invicta.native-replay.v1`. `ReplayStudy` is its explicit adapter input and `prepare(study)` is the public operation.

Concrete adapters are `costa-cabral/prepare_3d.py`, `line-701/prepare_replay.py` and `line-701/full/prepare_replay.py`. They provide scope, source paths, time window, seed and sampling. They do not monkey-patch a previously imported study's globals. Cache compatibility includes native network/routes/additional hashes, seed, simulation start, frame sampling, lane references, capture edges and declared scope.

Full-day captures are extracted from the numerical run’s own native FCD. Recorded edge-selection bytes and coverage are checked before extraction or cache reuse; widening the visual vehicle scope requires an execution that recorded those roads. The full native publisher additionally validates the complete numeric case/policy/seed matrix and binds each clip to the exact numeric run's input hashes. It rejects an old seed-17 clip beside seed-42-only numbers, partial capture matrices and changed source files. Browser loading verifies compressed bytes against the manifest before rendering. Full-line assets use `line-701-full-assets/`; the earlier Porto assets retain `line-701-assets/`, so an existing viewer cannot fetch a different study through the same path. Full-line frames use lossless vehicle deltas, round-tripped against every original native row before saving. The scene supplies one shared coordinate origin, so a camera pose saved after switching direction reopens in the same frame.

## Verification

The supplementary street-detail search is independent of the published native replay. `full/priority_model.py` builds a separate OSM pedestrian/speed/route model; `priority_search.py` executes explicit trial configurations, retains every scheduled working and grades all designated checkpoints; `signal_priority.py` logs bounded interventions without skipping clearance phases. `priority_ledger.py` freezes native outputs and verifies every published timetable count against them. Failed controller attempts and superseded imports remain visible. These exploratory rows cannot qualify a production proposal or inherit an existing animation.

The line registry optionally registers `streetAssets`, `prioritySearch` and `priorityReport`. `priority-panel.mjs` verifies supplementary JSON hashes against the proposal's source identity before displaying or exporting it. Porto equipment locations are a review layer, not live signal states or surveyed controller assignments. The public bundle is namespaced under `701-priority/`, so another line can register its own ledger independently.

`priority_demand.py` preserves generated physical OD positions when a new import splits road edges. Both policies receive identical endpoint mappings; no missing edge ID is silently discarded. A policy is checked for connectivity again on the new topology, retaining ordinary access when necessary. Lane restrictions preserve original pedestrian permission. Invalidated historical comparisons remain in the ledger with explicit reasons and are excluded from both HTML and Markdown presentation.

`native-replay.mjs` owns browser-side asset verification, lossless decoding, lane interpolation and policy-specific bus selection. The Canvas2D and Three.js renderers receive the same model. A plan-view viewport is serialized separately from the 3D pose; switching dimensions preserves the native time and scenario. Both renderers can supply the recording canvas.

- `node --test prototypes/line-701/line-explorer.test.mjs prototypes/line-701/proposal.test.mjs`: direction/focus identity, source-version gates, draft policy/replay behavior, share/import, uploaded evidence and public-claim eligibility.
- `.venv/bin/python -m unittest discover -s prototypes -p test_native_replay.py`: preparation through its public interface, matched captures, footprint invalidation, projection/lane rejection and two-second sampling.
- `.venv/bin/python -m unittest discover -s prototypes/line-701/full -p 'test_*.py'`: native publication contracts and full-route preparation invariants.
- Actual native full-day runs and a separate bus-only geometry control establish execution coverage, rather than a website assertion that a map is simulated.
