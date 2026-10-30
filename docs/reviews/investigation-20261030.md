# Investigation slice review

User release baseline: `ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa`. Full comparison: `git diff ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa...effc164bb271dd24a666a75d03be9e931afad2e8`. Previously reviewed history was retained as context; this review focused on the new `eb9d0a0..effc164` slice and its correction below.

Spec: [accepted investigation slice](../product/investigation-slice-2026-10-30.md). Standards: [architecture](../ARCHITECTURE.md), [production specification](../product/production-spec.md), plus the code-review skill's judgment-based smell baseline. No repository coding-standards, contributing or RTK file was found. Independent reviewers covered each axis.

## Standards

One P2 finding: prefix reproduction passed every completed native vehicle into the bus evaluator. A traffic-bearing prefix could report completed cars as completed buses, conflicting with the complete-service accounting requirement. The full runner and evidence loader already filtered scheduled bus IDs. No additional material standard violations or smell findings were identified.

Correction: intersect completed IDs with the frozen scheduled buses. A native fixture with two buses and one completed car failed with `3 != 2` before the fix, then passed and agreed with the diagnosis loader. The archived empty prefixes contain no ordinary cars and are unaffected. The Standards reviewer confirmed resolution.

## Spec

One P2 finding: the same prefix completion count violated the requirement to retain the complete scheduled-bus denominator. The remaining reviewed boundaries bind network/reference identities, prevent prefix promotion, inspect states without a simulation step and explicitly defer the broader search/promotion work.

The regression above verifies the correction through public native execution and diagnosis boundaries. The Spec reviewer confirmed resolution.

Standards: one finding, zero outstanding. Spec: one finding, zero outstanding. Each axis's original highest-severity finding was the P2 prefix completion count.

## Validation

`npm run check` passed: 53 JavaScript tests, nine native replay tests and 31 full-study Python tests, plus type checking and source/replay/deployment verification. All four browser acceptance tests passed. After the correction, the affected investigation file passed all 13 tests, including the new native traffic-prefix regression. The final suite contains 98 tests; the entire suite was not repeated after this isolated Python correction.

Actual evidence checks also completed: current model audit, unchanged first-Ermesinde prefix, explicit zero-dawdling sensitivity and read-only baseline/candidate final-state inspection. No new full-day traffic execution or compliant proposal is claimed.
