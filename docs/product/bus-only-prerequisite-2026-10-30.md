# Bus-only timetable prerequisite

User steering: test the complete official 701 timetable without ordinary traffic before comparing traffic and proposed street changes. The user selected an explicit operational tolerance reported beside the strict result. The initial project target is **no early checkpoint departures and at most 60 seconds of lateness**, inclusive. This is not an STCP contractual indicator.

- Retain the frozen 2026-10-28 operator reference: both directions, all 127 scheduled services including short workings, and all 714 origin/designated/terminal checks. Do not change times, remove services, raise speeds or tune driver parameters to obtain a pass.
- Keep the strict zero-second evaluation unchanged. Store operational results and their criteria separately. Use departure at origins and intermediate designated timing points, arrival at terminals; early terminal arrival is permitted. Missing calls and unfinished services fail both tests.
- A no-traffic control retains the imported signal plans. A separate signals-off control is an explicitly optimistic travel-time bound, never sufficient to authorize traffic or proposal comparisons.
- Bootstrap only empty, passenger-free controls with zero boarding dwell, no walking demand, request stops and declared checkpoint holding bays. They establish an optimistic model prerequisite, not passenger-service feasibility. Signal plans and holding footprints remain unvalidated assumptions.
- Audit the same frozen native events at the explicitly selected target. Recompute rather than trusting a stored pass flag. Include the criteria in the audit identity; a 60-second pass cannot authorize a strict test. Do not rewrite historical execution results.
- Keep expensive traffic/proposal comparisons blocked when the matching existing-signals control fails or geometry review remains unresolved. Record positive and negative controls, complete source/input/output identities and collision checks.
- Apply the previously diagnosed Alfena node join only in a separate unpromoted model candidate, shared by both controls. Preserve the previous study and public replay.

The review boundaries are native evidence loading, complete-trip evaluation, and the readiness gate. Browser data/replays are unchanged by this slice.
