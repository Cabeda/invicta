# Combatentes native mapping review

Incremental baseline: `976bc24a7e1b1f7d060be47441f6c40351f9e0dc`, the last reviewed/deployed commit. Fresh-context Standards and Spec agents reviewed the working change against the [accepted slice](../product/combatentes-signal-mapping-2026-10-30.md), glossary, architecture and production specification.

## Standards

No outstanding findings. A P2 guard gap was reproduced: removing external controller assignments could still pass the regional scope check. A failing regression preceded the fix; the guard now requires all ten intended internal removals and preserves all eleven external controls and the phase table.

A second P2 concerned frozen-input provenance: a supplied geometry patch could be ignored while being reported as applied. The recipe now binds the inherited geometry digest, conflicting arguments fail before import materialization, and matching or omitted geometry is explicitly recorded as inherited. The actual CLI rejection was verified in addition to the regression. The reviewer confirmed both fixes and all 14 mapping tests.

## Spec

No outstanding findings. The reviewer requested independent validation of the actual import-stage input, beyond checking the final control network. The recipe now binds the import bytes and their distinct topology/programme signature, with a rejection regression. The reviewer also confirmed the inherited-geometry fix above.

Independent review loaded the hash-verified frozen control/import, reran the selected V9 regional scope check and confirmed zero outside changes from `4ccaa3…706fe` to `64eeea…ae83`. Recomputed native stop/trip outputs confirm both directions, 127 completed trips, 6,024 calls and 714 checks at each seed. Operational misses, early departures, missing checks and collision records are all zero; strict late checks remain 1/3/2. The frozen-input model reports `import_mode: frozen_compiled_source` and `command: null`.

## Validation and limits

`npm run check` passed syntax/type checks, 53 JavaScript tests, nine native replay tests, 67 full-study Python tests and source/replay/deployment-asset parity. The added final-archive acceptance test and inherited-geometry regression passed separately; the complete mapping group was rerun with 14 passing tests. This is **131 unique passing tests** across those runs. UI code/assets did not change, so browser tests were not repeated.

Fourteen mapping tests include 408 retained bus-movement-pair cases, opposing buses at five offsets, mixed bus/walker flows, source rejection and regional-scope rejection. Every requested actor must start and finish; no omitted actor can count as a success. Full-day numerical controls use seeds 17, 29 and 41 and preserve the complete service. The twelve-run archive retains superseded models and failed import attempts.

The [final readiness audit](../research/701-combatentes-controls-2026-10-30/readiness-audit.json) retains only `stop_match_review`: three stopping positions need review. The operational no-traffic pass does not establish exact-second compliance, behaviour with ordinary traffic/passenger demand, actual municipal phase timings, complete pedestrian crossing coverage or field reliability. The original failing public recording remains unchanged; the correction is opt-in and unpromoted.

Standards: **0 outstanding findings**. Spec: **0 outstanding findings**.
