# Complete 701 traffic study

This is an actual native SUMO traffic simulation of both complete directions in one regional road network. It includes 56 inbound stops, 54 outbound stops, all 127 scheduled workings and 6,024 served timetable calls. Short workings keep their actual origins and destinations; 960 unserved timetable cells remain absent. It uses the frozen 28 October 2026 school-weekday timetable, not a live service feed.

## Investigate before another priority-search run

The supplementary street-detail search now has an audit gate and one code-first investigation interface. Install `requirements-simulation.txt` from the repository root. These commands read frozen evidence; only `reproduce` advances native traffic, in a bounded prefix:

```sh
.venv/bin/python prototypes/line-701/full/investigate.py diagnose \
  --source prototypes/line-701/full/priority-search.json --trial v5-empty-diagnostic-s17
.venv/bin/python prototypes/line-701/full/investigate.py inspect \
  --source prototypes/line-701/full/priority-search.json \
  --trial v5-moderate-priority-mapped-s17 --limit 5
.venv/bin/python prototypes/line-701/full/investigate.py reproduce \
  --source prototypes/line-701/full/priority-search.json --trial v5-empty-diagnostic-s17 \
  --output-dir .cache/701-investigation/new-control
.venv/bin/python prototypes/line-701/full/investigate.py audit \
  --model .cache/701-optimisation/model-v5 \
  --source prototypes/line-701/full/priority-search.json --trial v5-empty-diagnostic-s17
```

`audit` requires the prepared model folder, returns exit code 2 when blocked, and identifies the specific findings. `diagnose` and `inspect` return success when evidence inspection succeeds, even if the transport goal fails. Use `--format json` or `--format markdown`; `--report new-path.json` saves a new report. `inspect --snapshot first-deadline-state.xml.gz` reads a new run's first-failure state. A selected `--stop` requires its `--trip`.

The current model remains blocked: three stop placements exceed the project's 25 m review trigger, and the empty control misses Ermesinde by 19 seconds. The unchanged prefix reproduces all 25 completed calls; the explicit `reproduce --bus-sigma 0` sensitivity reduces that miss to five seconds and still fails. This changes an uncertain vehicle-behaviour assumption, not the proposed streets. Prefixes preserve the original complete demand and warmup, are capped at one simulated hour and a 120-second native wall budget checked after each step, and cannot qualify a full-day proposal. Later failures can be inspected from saved states; resume equivalence has not been established.

New `priority_search.py` configurations require `readiness: {"source": "...", "trial": "..."}` and `hypothesis: {"change": "...", "prediction": "...", "evidence": "..."}`. A matching complete-service empty diagnostic supplies readiness only after its checks pass. The existing explicit empty profile can run to bootstrap this process; there is no force flag. New native executions retain source copies, first-failure states, bounded traces, progress and phase timings. The gate applies to this supplementary search; the earlier `run.sh` replay pipeline below retains its separate publication checks.

## Run and reproduce

From the repository root, using the pinned environment in `prototypes/costa-cabral/requirements.txt`:

```sh
./prototypes/line-701/full/run.sh --cases moderate,busy,late --seeds 17
# Repeated seeds, when desired:
./prototypes/line-701/full/run.sh --cases moderate,busy,late --seeds 17,42,73
```

The pipeline imports the frozen OSM archive, maps and audits both official shapes, screens the combined priority policy, runs a bus-only geometry control, runs the full-day case/policy/seed matrix, prepares native replay assets and rebuilds the static website. Results are cached only while native inputs match. To change a native model assumption, use a fresh run directory rather than editing a completed result.

`prepare.py --osm-source /absolute/path/to/source-folder` can replace the frozen OSM source with an acquired, hash-checked map-API bundle. Normal reproduction uses the retained `data/network.osm.xml.gz` and checks its recorded hash. The 31 original map-API responses, URLs, retrieval times and validation counts are described in `data/network-manifest.json`. The raw expanded network is regenerated locally.

Replay preparation chooses the first numeric seed by default. `prepare_replay.py --seed 42` chooses another seed present in the numeric matrix. Publishing rejects missing case/policy clips, mismatched seeds, changed available input files or a replay from a different execution. Frozen public results retain the same input hashes when large local run folders are archived; running a new experiment reconstructs the native inputs. The full runner currently accepts `--cases` and `--seeds`; arbitrary policy exports remain drafts requiring an explicit native implementation.

## What is simulated

Each case runs from 05:00 to 27:35, including service after midnight and a two-hour clearance period. The ordinary-traffic requests cover neighborhoods around the entire line. Both bus directions interact with residents, ordinary traffic, taxis, bicycles and motorcycles on the same network. Baseline and priority receive the same requested vehicle journeys for each case and seed.

- Moderate and busy are explicit synthetic hourly demand profiles, not measured Porto metropolitan travel counts.
- Late uses busy demand and adds three minutes to one inbound working after 17:00.
- Every scheduled working has a separate prepositioned native bus. Vehicle blocks, driver duties, turnarounds and interactions with other bus lines are unavailable and are not invented.
- Stops use fixed 20-second dwell, with holding at designated timing points. The separate inbound passenger/berth model is not silently applied to native traffic.
- Lane permissions change in the prepared policy; imported geometry and signal programs match across baseline and priority. Generated OD connectivity is screened, but driveways, loading, emergency access and legal adequacy still need local review.

The bus-only control must complete all 127 workings and all 6,024 served calls before traffic results are published. This establishes traversable routes and stops under the model; it does not establish that its dwell assumptions fit every published timetable.

## Geometry assumptions and corrections

The baseline imports OSM one-way rules, lane counts, turn restrictions and guessed signals. It does not assume two opposing lanes throughout Costa Cabral. No street survey has validated the import.

`data/route-import-overlays.json` records one bus-only straight-turn exception near Asprela/Costa Cabral. The imported generic right-turn restriction conflicts with both the official outbound 701 shape and frozen OSM bus-route relation 10107392. The exception is present in both baseline and priority; ordinary traffic retains its imported restriction. This resolves the source conflict for modelling and still needs operator/street confirmation.

Map matching uses a broader local shape heading around curb spurs, checks bus permissions and usable stop length, and scores physical path distance including internal junction connectors. Earlier diagnostic mappings with outbound residential detours and an inbound extra roundabout lap are excluded from the published traffic matrix.

## Numeric results and animation

`results.json` retains every requested, completed, unstarted and unfinished journey, per-stop bus arrivals/departures, timing-point failures and collision records. A lower mean among completed trips cannot establish a benefit for everyone when other requests do not finish. The generated [report](../REPORT.md) includes the actual run matrix and limitations.

The full-day runs also save their own native vehicle positions. The public 3D replay uses **16:50–18:20 at five-second native samples**, with visual interpolation; traffic physics remains at the original one-second step. Vehicles are shown on route roads and roads meeting their junctions. The scene includes a wider 150m context; numerical totals cover the full regional experiment. This bounds the downloadable animation while preserving the complete line in both directions.

The manifest records scene and compressed capture hashes, input network/routes/additional hashes, seed, time window and the full-day trajectory identity. Browser loading checks those sources. No second traffic execution supplies a substitute animation for the published numbers.

Native results do not yet predict mode shift. A long-term shift to buses, cycling or walking is a separate demand assumption to test, not a consequence inferred from this fixed-demand experiment. Calibrating that transition needs full-line AVL, passenger loads, observed OD and modal travel data.
