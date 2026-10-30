# Focused inspection and signal-source review

Accepted full review baseline: `ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa`; earlier history was reviewed separately. Fresh-context Standards and Spec agents reviewed `40b6cd4...a6da7e4`, followed by `a6da7e4...a278c17`. Standards also reviewed the playback-focus fix in `a278c17...7311ffa`.

Scope: [focused inspection](../product/focused-inspection-2026-10-30.md). Standards: glossary, architecture, production specification and code-review skill smell baseline.

## Standards

No documented-standard breaches or material Fowler smells. The standalone diagnostic follows the existing static publication contract and keeps source data, controller assumptions, replay observations and field validation distinct.

A functional review concern identified source links recreated on every playback render, losing keyboard focus. A browser regression reproduced the failure before the fix. Source anchors are now created once; playback preserves them and language changes update labels in place. The reviewer confirmed the correction.

## Spec

No material requirement gaps. One minor stale building-provenance sentence was found in the initial capture metadata. Revision 2 corrects it and preserves revision 1 with a defect/supersession record. The reviewer independently confirmed that every sampled frame, geometry/timing row, native stop-event row and tripinfo row is unchanged between revisions, and that active artifacts match the R2 implementation and hashes.

Independent checks verified both focused Python tests, every controller phase and movement against the frozen native network, and all 16 municipal equipment coordinates/installation IDs against the review layer. The source layer uses the seven frozen OSM signalised-crossing nodes with direct links. These are not presented as physical head counts. Equipment remains an optional neutral comparison layer. The two real vehicle signals reported by Cabeda remain an unresolved mapping constraint; no native controller correction is claimed.

## Validation

`npm run check` passed 53 JavaScript tests, nine native replay tests and 51 full-study Python tests, plus type checking and public source/replay/deployment-asset verification. Two new focused native-evidence tests passed separately. Six browser acceptance checks passed: shared 2D/3D state and holding table; altered-byte rejection; wrong-network audit rejection despite a valid hash; 2D fallback without WebGL; phone layout; and source-link keyboard focus during playback. **121 unique tests pass across these checks.**

Active recording R2 matches all **6,024 source stop events and 127 tripinfo rows**. It records positions and traffic-light states once per second in two inspection windows, while preserving the complete source service day. A native observation rerun does not change signal programmes, ordinary traffic demand or model assumptions.

The static publisher exports only seven inspection assets. Raw inputs/outputs remain outside the served site; native evidence is retained in the repository. The canonical proposal and its qualification status remain unchanged. Runtime loading verifies the recording and signal-audit bytes and binds the audit to the captured network.

Standards: **0 outstanding findings**. Spec: **0 outstanding findings**. Physical signal-head mapping, real phase timings and transport feasibility remain unresolved. Deployment and remote CI are verified separately.
