# Native bus-only evidence

`controls.json` is a self-contained diagnostic ledger, deliberately separate from the published proposal search. Its six `trials` are complete empty service-day executions on one candidate network: three seeds with imported signals enabled, paired with three signals-off bounds. `evaluations.json` recomputes both strict and 60-second project results from those frozen events. `readiness-audit.json` records the blocked signal-enabled prerequisite.

Each descriptor identifies a gzip object under `objects/` by compressed SHA-256, decoded SHA-256 and decoded byte length. Objects are deduplicated across models, executions and implementation witnesses. Use `trial_evidence.read_archive(root, descriptor)` to verify and decompress one object, or `load_trial(controls_json, trial_id)` for a lazy execution view. Its `payload(name)` also checks the original execution's input/output binding.

The model includes only the candidate Alfena node join, not a new street proposal. The default published model, public animation and timetable remain unchanged. Original commands contain the local paths used at execution; path relocation must preserve file contents, seed and all behavioural flags. The original implementation sources and pinned dependency requirements are retained with each execution. `evaluation_sources` records the current evaluator/audit implementation used for the supplementary reports.

`reduction_attempt` is separate: a one-bus control loses the recorded late outcome, and an empty-request-stop probe on that passing reduction cannot establish a remedy. It must never be counted as another complete-service pass. Both traces, commands, route inputs and native outputs are retained; their unchanged network/additional inputs are those of `source_trial`.

See [the results and limits](../701-bus-only-results-2026-10-30.md) and [acceptance scope](../../product/bus-only-prerequisite-2026-10-30.md).
