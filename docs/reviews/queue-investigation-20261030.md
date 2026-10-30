# Alfena queue investigation review

Previously accepted user baseline: `ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa`. Full comparison: `git diff ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa...c6a33244cf1b00a9900c2c39eaebe31be5985dae`. Reviewed earlier history was context; independent fresh-context reviewers focused on `4b25218...c6a3324`, with the added evidence README checked subsequently by the Spec reviewer.

Spec: [queue-onset investigation](../product/queue-onset-investigation-2026-10-30.md). Standards: [architecture](../ARCHITECTURE.md), [production specification](../product/production-spec.md), glossary and the code-review skill's judgment-based smell baseline. No separate RTK, coding-standards or contributing file was found.

## Standards

No documented-rule violations or material baseline smells. The change respects the architecture's diagnostic/replay boundary and the production specification's distinction between software readiness and transport validation. Documentation labels the compound junction as an unpromoted candidate, preserves failed/partial evidence and avoids whole-line or field-success claims.

The reviewer ran all five native tests and independently verified the 365 manifest hash entries, fixture hashes and both focus junctions' original attributes/request matrices.

## Spec

No missing/partial requirements, scope creep or unsupported service-success claim. The work reduces a recorded mechanism to a fast native reproduction, preserves external movements/types/endpoints, retains the split failure and archives scope-qualified evidence.

The reviewer ran all five native tests, verified every manifest descriptor and byte count, reconstructed both exact full-network inputs from their Zstandard reference patches, independently matched all 3,074 completed calls, and checked fixture geometry/type bindings. The partial earlier sweep, state analogues, full-network two-car cases and complete local sweep remain separate. The missing first-entry manoeuvre and regional promotion are documented limits.

## Validation and release scope

`npm run check` passed 53 JavaScript tests, nine native replay tests and 45 full-study Python tests: **107 tests**, plus type checking and source/replay/deployment-asset verification. The five new native regressions run in under one second locally. Browser tests were not repeated because no browser code or assets changed.

No new full-day service execution or public animation was produced. The candidate patch has not been promoted into the regional model; the strict timetable goal remains unmet. Remote CI status is reported separately at release.

Standards: **0 findings**. Spec: **0 findings**.
