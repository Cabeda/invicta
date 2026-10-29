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
