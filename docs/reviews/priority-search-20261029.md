# Priority-search review

Fixed review point: `ce1dfee247a0ba9e78e413e4ef9dc4bfce9091fa`, as agreed for the production review. This iteration's original commit was `d02f09c`, with `51e409f` as its immediate base. Two independent reviewers examined standards and specification; corrections were checked again before publication.

## Standards

The reviewer identified two documented-standard breaches:

- **Recorded output hashes were not checked before publication.** Changed passenger output could be frozen under an earlier execution identity if bus metrics happened to match. The exporter now checks every recorded completion hash before recomputing or archiving results. Verification checks archived bytes against both the archive digest and the original execution binding. Older runs without completion hashes are marked `first_archive_only`.
- **Failed trial folders could be reused.** Inputs and failed output could be overwritten and stale controller events retained. Every existing folder is now rejected. Exclusive directory creation also handles a concurrent creator; error recording belongs to the process that created the folder. A failed-folder acceptance test protects the original error record.

The reviewer also noted possible duplicated HTML/Markdown row logic. A shared presentation selection now supplies both outputs, and scheduled-trip counts come from the registered study rather than a hard-coded 701 count.

Both provenance corrections passed the follow-up review. The concurrent-directory edge identified during follow-up was also corrected.

## Spec

The reviewer identified two model defects:

- **Bus-lane conversion also granted pedestrian access.** The inherited permission list added pedestrian access to 88 carriageway lanes, including 25 without a separate sidewalk. Conversion now preserves each lane's original pedestrian permission. The corrected candidate changes zero pedestrian permissions.
- **Old topology IDs excluded traffic requests.** The pedestrian import split roads and removed 66 older edge IDs. This left 8,581 of 26,035 requests unroutable. Requests now retain their physical origin/destination positions across imports and policies; every mapped OD pair must be connected before simulation starts. The new pair has all 26,035 vehicle definitions, identical mapping bytes, 960 endpoint/class mappings, maximum displacement 29.372 m, and no reversed same-edge trips. The corrected candidate reserves 87 lanes and retains general access where required by the connectivity test.

The old comparison is explicitly invalidated and excluded from presentation and proposal decisions. Its raw results remain in the audit history with both defects stated. Physical endpoint mappings are archived with the new native evidence.

**Unmet user objective:** no timetable-compliant proposal has been established. The report states this rather than promoting a favourable subset or retiming the published service. The complete busy/late multi-seed qualification matrix and field calibration remain required. The reviewers found the distinction between official asset locations and assumed controller timings clear; no unrelated scope expansion was identified.

Four original material findings were corrected. The minimum-change, all-trips-on-time objective remains open.

The completed mapped runs were then regraded from their unchanged native outputs. A further acceptance test caught an observation-count defect: an unfinished vehicle had incorrectly made all of its earlier observed calls count as missing. Grading schema 2 preserves those observed starts/arrivals while still rejecting the unfinished trip. Original execution metrics remain archived. The general web evaluator also now rejects a missed designated intermediate checkpoint even when origin and terminal times pass; a frozen-schedule acceptance test covers missing, early and late intermediate departures. The specification reviewer checked the final checkpoint gate and native workload/pedestrian-permission verification and found no further correctness blockers.

## Follow-up: route matching and public-only calibration

A fresh primary-source audit confirmed two import-matching defects. The stop-edge length filter moved Alfena to Rua Coroa; after that correction, the non-stop anchor filter still forced a Várzea spur. The integration regression uses `withInternal=True`, matching the actual preparation caller. Both known spurs are removed in version 5 without changing any published timetable seconds. The model's network and route-reference hashes jointly identify an execution, and superseded imports remain archived but excluded from current comparisons.

The independent Standards follow-up found zero documented-standard breaches. Its optional concern about scattered version handling was resolved with one model catalog. The Spec follow-up found no new implementation blocker: 63 inbound and 64 outbound workings remain, the corrected Alfena path follows the official corridor, and paired traffic cases retain the same OD workload and routing algorithm. It identified the continuing requirement gaps: no timetable-compliant proposal and no surveyed whole-line controller/stop model. Version 5 still has maximum stop snaps of 26.96 m inbound and 46.796 m outbound; correcting two spurs does not establish field validation.

The user confirmed public data only. The source audit found no validated public 701 passenger profile or full trip-timing history; live predictions, stale broker positions, an independent collector's unmatched records and dated speed-sign inventories are not substituted for calibration. The corrected full-day executions retain native end states for diagnosis, separate from the published animation. Final native/archive, site-parity and browser checks remain publication gates.

The final archive contains 34 complete executions. Both new mapped-traffic runs retain all 26,035 ordinary requests, identical passenger/walking plans and pedestrian permissions, with zero unroutable requests. The current package fails: 62 on-time terminal arrivals, 85 completed trips, 73 unserved ordinary requests and 15,595 served passengers, versus 3, 119, 40 and 20,738 in its baseline. No winner is declared. All 85 checks passed: 53 JavaScript, 28 Python and four browser acceptance tests, including exclusion of superseded models from the exported current comparison. Public source parity, line registration, replay hashes and all 57 deployment-asset hashes passed verification.
