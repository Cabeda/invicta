# Investigation loop review

Base: `edf83bb3319af2cc8b2ad20cef41265168f7f830`. Initial candidate: `1ac6535`. Standards and Spec were reviewed independently in fresh agent contexts; fixes were rechecked independently. Generated vendor copies and compressed evidence were not read wholesale; native archive verification and source-level invariants were checked through the public interfaces.

## Standards

Three P2 findings:

1. Partial service runs could replace established complete failure profiles.
2. Additional XML could introduce future vehicle demand outside the requested-actor denominator.
3. Failure bookkeeping omitted native computation time and counted preflight rejection as native execution.

All addressed. Only full-reference analyses promote workload profiles. Local additional XML is validated before allocation. Native witnesses distinguish initialization attempts, successful startup and measured time; preflight rejection is separate. A subsequent classification edge—successful startup followed by a pre-first-step controller error—was fixed with an explicit startup notification and a native unknown-TLS regression. Final recheck: no remaining blocking Standards findings.

## Spec

Three P2 findings:

1. A native run finishing before a reporting error was not journaled and could not resume under the same experiment identity.
2. Operational scoring inherited arbitrary source tolerances instead of enforcing the agreed 60 seconds.
3. Failed native computation time disappeared from session totals.

All addressed. Native completion is journaled before postprocessing; hash-verified physics can be reused after an analysis failure. Casebooks use pending directories and source-bound receipts. The loop explicitly computes 60 seconds beside strict scoring and rejects a relaxed service target. Failed native attempts retain their measured cost. Final recheck ran the focused native suite and found no remaining blocking Spec findings.

## Validation

The initial full check passed 53 JavaScript tests, nine shared replay tests and 103 native/Python tests. Review fixes add real native regressions for additional future demand, analysis failure/reuse, partial profile retention, legacy 3,600-second scoring, preflight/native accounting and pre-step setup failure. The focused suite has 19 passing tests. All 13 browser acceptance tests pass, including same-frame 2D/3D, restored source/language/frame, source mismatch rejection and Retina canvas sizing. The final full check passes 53 JavaScript tests, nine replay tests and 107 native/Python tests. Deployment is verified separately.

These checks establish software/evidence behaviour. They do not qualify the current traffic proposal or provide field calibration.
