# Diagnostic follow-up review

User release baseline: `ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa`. Full comparison: `git diff ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa...734d38db211aa2d6cca30559453e59e74a8d95f2`. Previously reviewed history was context; independent reviewers focused on `732b8e0..734d38d`, then reviewed the working-tree corrections and final evidence additions.

Spec: [diagnostic follow-up](../product/diagnostic-followup-2026-10-30.md). Standards: [architecture](../ARCHITECTURE.md), [production specification](../product/production-spec.md), glossary and the code-review skill's judgment-based smell baseline. No separate coding-standards, contributing or RTK file was found.

## Standards

Two P2 findings:

- State-probe timeouts discarded buffered observations before writing the trace and report. Budget stops now close normally with actual cutoff, stop reason and partial or zero-step evidence.
- Partial diagnostic metrics presented future checkpoints as missing service. Whole-reference goal metrics remain intact, while an explicit observation view separates due checks, future deadlines and observed failures. The CLI uses that view and future trips are not listed as overdue unfinished service.

The Standards reviewer confirmed both corrections, the bounded explicit onset-budget extension, and the hashes/bindings of the added diagnoses. No material baseline smell was identified. Final evidence review independently checked the 62 completed buses and 3,025 matching bus calls, observation counters, exact input bindings, reduced-case offsets and collision output.

## Spec

The Spec reviewer identified the same two P2 gaps against the requirement to preserve evaluable partial executions and distinguish future service. Both are resolved. Native regressions cover budget stops in both commands, the due/future split, a real all-red fixture's early blockage capture, and the unchanged reference and qualification boundaries.

The explicit onset budget defaults to 180 native seconds, permits at most 900 and retains the 12-hour simulated cap; normal checkpoint prefixes and state branches retain their 120-second caps. Onset replay cannot modify physical inputs. The reviewer found no further material scope/correctness issue. Final added evidence clearly labels reduced demand/boundaries and does not claim original continuation, service qualification or safety validation.

Standards: two findings, zero outstanding. Spec: two findings, zero outstanding. Each axis's original highest severity was P2.

## Validation

`npm run check` passed syntax/type checks, 53 JavaScript tests, nine native replay tests and 40 full-study Python tests, plus source/replay/deployment verification. All four browser acceptance tests passed. The affected investigation file subsequently passed all 21 tests, including the final evidence checks; the explicit 901-second rejection was also checked separately. This is 106 tests in total. No additional full-day traffic execution was performed.

Actual native evidence includes stop-semantics probes, paired state analogues, a one-step original-tail mismatch, unchanged-input replays through 08:00:47 and 15:10:02, four reduced two-vehicle cases and a three-second stack sample. The research target remains unmet. Remote CI status is reported at release time separately from these local results.
