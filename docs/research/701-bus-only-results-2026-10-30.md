# 701 without ordinary traffic: free-flow pass, signal-enabled failures

**The existing-layout baseline displayed by the demo includes synthetic traffic. The new bus-only tests show that the timetable is attainable within the project's 60-second target when signals are off, but not consistently with the generated signal plans enabled. Traffic and street-proposal comparisons remain blocked.** Neither test uses observed Porto traffic or surveyed municipal timing plans.

## The test and the acceptance rule

The complete frozen operator reference is dated 2026-10-28: **127 scheduled services, both directions, 6,024 served calls and 714 timing checks**. A service is one scheduled departure running to its specified destination; short workings remain included. Each service is still an independent simulated bus, without observed vehicle blocks.

Cabeda selected an explicit operational tolerance beside the exact-second result. The initial project target is **no early departures and no more than 60 seconds late**, inclusive, at every origin and designated timing point; terminal arrival is measured instead of terminal departure and may be early. Missing checks and incomplete services fail. This is a project criterion, not a claim of compliance with an STCP contract. The exact-second test remains intact.

All six controls use the same candidate network, official times, route/stop mapping and bus parameters, including `sigma=0.5`, 12 m length, acceleration 1.2 m/s² and maximum speed 50 km/h. There are **no ordinary vehicles, passengers, boarding dwell or requested pedestrian crossings**, and unused request stops are skipped by native SUMO. Timing points hold early buses to schedule using the existing declared parking/holding assumption. Thus this is an optimistic prerequisite, not a realistic passenger-service scenario.

The candidate model applies the [previously isolated Alfena compound-junction correction](701-queue-onset-results-2026-10-30.md). Every service ID, operator trip ID, stop ID and scheduled time was checked against V5: all are unchanged. This correction has not been promoted to the published baseline, and no public replay was regenerated. Full-day controls use SUMO 1.28.0, disable teleporting, warn on collisions and enable junction collision checks.

## Results

| Control | Seed | Services completed | Exact-second late checks | Checks more than 60 s late | Operational pass |
|---|---:|---:|---:|---:|---|
| Signals off, optimistic bound | 17 | 127/127 | 1 | 0 | Yes |
| Signals off, optimistic bound | 29 | 127/127 | 1 | 0 | Yes |
| Signals off, optimistic bound | 41 | 127/127 | 1 | 0 | Yes |
| Imported signals enabled | 17 | 127/127 | 20 | 6 | No |
| Imported signals enabled | 29 | 127/127 | 17 | 3 | No |
| Imported signals enabled | 41 | 127/127 | 14 | 2 | No |

Each row evaluates all 714 checks. Every row has **zero missing timing checks, zero early departures and zero recorded collisions**. Zero collision records do not establish street safety. The three seeds are diagnostic repetitions, not a robust forecast or validated operating distribution.

The sole strict miss with signals off is `d1_bus_0`, Codiceira 05:25 → Ermesinde Estação 05:33: departure is 05:33:16, **16 seconds late**, in all three seeds. No schedule, speed or driving parameter was changed to remove that miss. The historical configuration name `diagnostic_all_green` invokes `--tls.all-off true`: signals are switched **off**, with applicable priority rules retained. It does not make all traffic movements green.

## Which signal-enabled services fail the 60-second target?

Seed 17 has these six failures; seeds 29 and 41 retain the early service failures and have fewer later misses.

| Service toward Bolhão | Timing point | Scheduled | Observed | Lateness |
|---|---|---|---|---:|
| Codiceira 05:45 (`d1_bus_1`) | Marquês, departure | 06:17:00 | 06:18:01 | 61 s |
| Same service | Bolhão, arrival | 06:20:00 | 06:21:22 | 82 s |
| Codiceira 19:45 (`d1_bus_55`) | Marquês, departure | 20:28:00 | 20:30:18 | 138 s |
| Same service | Bolhão, arrival | 20:32:00 | 20:33:04 | 64 s |
| Codiceira 21:10 (`d1_bus_58`) | Marquês, departure | 21:46:00 | 21:47:37 | 97 s |
| Codiceira 24:10 (`d1_bus_62`) | Marquês, departure | 24:46:00 | 24:47:05 | 65 s |

Times above 24:00 preserve the operator service-day convention; 24:10 is 00:10 the following calendar day. Outbound toward Codiceira has no checks beyond the 60-second allowance in these three empty controls. This does not establish outbound performance with passengers or traffic.

For seed 29, the 05:45 service is 61 s late at Marquês and 81 s at Bolhão; the 19:45 service is 132 s late at Marquês. Seed 41 retains only the 05:45 service's 61 s/81 s misses.

## What the trace establishes

The seed-17 19:45 service leaves Areosa Mercado at 20:18:00 on schedule. Its next designated timing point is Marquês at 20:28:00. The recorded trace shows repeated stops through the generated joined controller `joinedS_12514310100_12514324965_12514324966_3897692280_#1more`, around Costa Cabral/Combatentes. This controller combines 21 vehicle signal links into eight green stages, with retained yellow/all-red stages; these are generated assumptions, not the actual municipal programme.

At 20:25:30 and 20:26:00 the bus is stationary on internal lane `:3897692280_1_0`, with no reported leader or nearby junction foe, while its next downstream controlled link (17) reports green. By 20:27:30 it has accumulated 128 seconds of consecutive waiting at the same position. This is a specific target for a source-preserving junction/signal reproduction. The downstream green alone does not prove that every internal conflict the bus must clear is permissive. Stop output and these samples do not isolate the precise native rule responsible.

The paired controls establish that enabling the imported signal model produces failures even without ordinary traffic. They do **not** establish a real-world failure of Porto's traffic lights, or prove that a particular signal-priority proposal fixes it. Source signal assignments, internal junction movements, detector coverage and phase progression must be inspected before tuning a controller. The matched stop footprint at Combatentes is another candidate to distinguish with a minimal reproduction.

A fresh reduced test retaining only `d1_bus_55` loses the failure: that bus meets its six checks within 60 seconds. Removing its empty request-stop entries in that already-passing reduction also passes, and therefore does not establish a remedy. These negative reduction attempts are retained separately in the evidence ledger. Other buses can affect signal actuation and random-number consumption even when no ordinary traffic is present; the full-schedule control remains the reproducible failing case.

### A compound-junction candidate was tested and rejected

The original Combatentes representation contains several short normal connecting roads: `-1083211594`, `-1172588827#0`, `1083211594`, `1172588827#0` and `675897037#0` each have only 0.20 m available lane length; `-675897037#1` has 2.74 m. Following the earlier Alfena diagnosis, a separate candidate joined the six represented junctions in the controller area (11 original OSM nodes) into one physical junction. SUMO documents that separately mapped carriageways can require explicit joins, but this guidance does not establish that a particular join is correct. [OSM junction guidance](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html#junctions), [plain-XML joins](https://sumo.dlr.de/docs/Networks/PlainXML.html#joining-nodes).

The candidate retained the same 127 services, 6,024 scheduled calls, all stop IDs/times and bus parameters, with signals enabled and no ordinary traffic or passengers. **Seed 17 still fails:** all services finish, but ten exact-second checks and three operational checks are late. The 05:45 service's Marquês departure becomes 112 s late (previously 61 s) and its Bolhão arrival 79 s late. The service `d1_bus_61` also departs Marquês 112 s late. There are no early/missing checks or recorded collisions. Further seeds were not run for this already-failing candidate.

The reimport also changes edge-fragment identities and the native mapping of the Combatentes stop. A lane-ID comparison is retained only as an identity screen: it does not establish preservation or loss of physical turns. Complete physical-access validation remains unestablished. This candidate was **not promoted** and does not authorize traffic tests; merely joining short fragments is insufficient to reproduce the timetable. [Candidate inputs, outputs and failed-import provenance](701-bus-only-controls-2026-10-30/candidate-controls.json), [native re-evaluation](701-bus-only-controls-2026-10-30/candidate-evaluation.json).

## Repository changes and next gate

The pure evaluator accepts an explicit lateness tolerance while retaining its historical strict default. Native results and diagnoses report both scores and the project criterion. Audit identities include that criterion, and re-evaluation reads verified native events without rewriting archived results. A strict candidate cannot inherit a 60-second acceptance flag.

The bootstrap supports an empty control with the imported signals enabled. A signals-off pass is retained as an optimistic bound and now explicitly **cannot authorize** later traffic or street-proposal comparisons. The signal-enabled control must pass the selected target first. The three existing stop-match review flags also remain unresolved; no force option or blanket acceptance was added.

This separates three questions: can a bus physically follow the timetable under optimistic conditions; can the imported existing-layout model reproduce it without ordinary traffic; and can a proposed change deliver it with complete traffic/passenger demand? The first passes the operational target; the second is still failing; the third has not been rerun in this investigation.

## Evidence and reproduction

The [self-contained six-control ledger](701-bus-only-controls-2026-10-30/controls.json) retains original execution metadata, every recorded native input/output, implementation witnesses, model import logs, the correction patch and compressed-byte/raw-byte hashes. Shared objects are stored once. [Recomputed evaluations](701-bus-only-controls-2026-10-30/evaluations.json) retain both criteria. The ledger is diagnostic evidence, separate from the published proposal search.

```sh
.venv/bin/python prototypes/line-701/full/investigate.py diagnose \
  --source docs/research/701-bus-only-controls-2026-10-30/controls.json \
  --trial v6-bus-only-existing-signals-60-s17

.venv/bin/python prototypes/line-701/full/investigate.py diagnose \
  --source docs/research/701-bus-only-controls-2026-10-30/controls.json \
  --trial v6-bus-only-signals-off-60-s17 --lateness-tolerance 0
```

To reproduce execution, extract a trial's `network.net.xml`, `routes.rou.xml` and `additional.add.xml` through the hash-verifying `trial_evidence.load_trial(...).payload(name)` interface; preserve the complete `reference.json`, recorded native version, seed and command options, replacing only file paths and output destinations. Its original timetable can be regraded from `stops.xml` and `trips.xml` without executing physics again. No saved-state continuation or altered driver sensitivity is needed for these controls.
