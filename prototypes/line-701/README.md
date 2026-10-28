# 701: Areosa → Marquês, one direction first

**Question:** can we locate where the 701 loses time, compare bus priority by stop interval, and identify car connections that need to remain? This is a throwaway, runnable investigation, not a calibrated forecast or approved design.

Open the [bilingual pilot](../costa-cabral/proposal/index.html) over HTTP, or serve it with:

```sh
python3 -m http.server 8765 --directory prototypes/costa-cabral
# http://127.0.0.1:8765/proposal/index.html?lang=pt#route
```

The website contains the official route, five scheduled morning journeys, simulated arrival profiles, twelve interval controls, car connectivity results, GPS passage evidence, CSV arrival import, 3D and WebM recording. Its policy JSON is controlled through code; new checkbox combinations require a native rerun. The earlier street experiment and regional population calculator remain in `proposal/legacy.html`.

## Current route and timetable

Frozen official STCP APIs for **28 October 2026**, inbound `direction_id=1`, towards Bolhão; service `UTIL ESCOLAR:FLUXO 3 20261027`. The section contains **13 stops** and approximately **3.14 km** of official shape:

`ARS3 → AA2 → ACO2 → STJ3 → BRRS2 → CF2 → LW2 → SVT4 → PLIM2 → COMB4 → LIMA2 → MPL7 → MPL4`.

The current route turns from Costa Cabral into **Rua da Alegria, Rua da Constituição and Praça do Marquês**. COMB4 is already on Alegria. Both Marquês stops matter: MPL7 was restored in October; the frozen September municipal feed is not the route authority for this date. Only MPL4 is a designated timing point inside this section. Intermediate published seconds are reference times, not instructions to hold a bus or an agreed punctuality standard.

The 08:00–09:00 Areosa references are 08:12:50, 08:23:50, 08:34:50, 08:45:50 and 08:57:43. Four run to MPL4 in a published 13m10s; the fifth in 11m17s. Per-stop APIs omit trip IDs: all 63 unique stop calls are associated by sorted rank against unique MPL4 trip anchors, with exact anchor and monotonicity checks. This is a derived association.

See [primary-source research](../../docs/research/line-701-data-and-direction.md), `data/source-facts.json`, and the raw response bundle `data/official/metadata.json` for URLs, dates and hashes. `prepare_route.py` uses the official ordered shape and bus-permitted network connectivity to match 42 native edges, with stop snap distances below 10m. It does not select roads just by their names. Segment policies use whole native edges; a shared boundary edge belongs to the earlier interval. Exact stop boundaries and street design require field review.

## What the observation sample establishes

A bounded, 15-minute public Porto Digital collection captured 48 unique accepted timestamped 701 positions across 59 polls. Duplicates are removed; current trip IDs, Lisbon study date, observation age, shape distance and progress are checked. Raw positions are in `data/observations/positions.ndjson`; reproducible passage windows are in `data/observations-summary.json`.

One evening journey has ten stop passage windows. Between **PLIM2 (Pires de Lima) and COMB4 (Combatentes)** its deviation from the published reference grew by **137–258 seconds**, approximately **2.3–4.3 minutes**. These are brackets from consecutive GPS positions straddling a stop, not door-open arrival measurements. One trip cannot establish a recurring bottleneck or its cause. That journey has no Areosa passage, so its inherited delay and full-section added observed delay cannot be separated. The evening sample does not calibrate morning demand.

The CSV importer accepts `trip_id,stop_id,observed_arrival`, with an ISO timestamp including timezone, matching current trip IDs, study date and stops. A later upload for the same trip replaces its previous uploaded records. Uploaded arrivals remain in browser memory and are labelled user supplied, without independent verification. They are never presented as captured GPS evidence. Predicted arrival/delay fields are not used as measured passages.

## Native experiments and car access

The baseline is byte-identical to the earlier unmodified frozen OSM import. **Lane counts, geometry, connections and signal programs stay identical across all new variants.** A policy changes lane permissions only. Existing bus-only lanes remain; new priority reserves one eligible lane and retains other general lanes where present. Only the selected inbound edges change. A no-change interval produces exactly identical native outcomes to the baseline in all three seeds.

The access screen tests generated side-road connector and ordinary-traffic OD pairs. Restricting the first two intervals, **Areosa → Alto da Areosa → António Coelho**, makes some pairs unreachable. The candidate therefore retains general flow there and applies new/existing priority on later intervals; its combined screen has zero newly unreachable pairs. This is a sampled structural finding, not proof that those are the only possible policies, not actual residents' demand, and not a legal conclusion. Driveways, loading, visits, deliveries, emergency access, turn movements and walking access need a real inventory. Low detours do not establish that access is acceptable.

The full batch has **63 SUMO runs**: three seeds for three traffic/entry cases and three packages, plus all twelve individual-interval tests in the busy case. Traffic is synthetic, dwell is fixed at 20s, and imported signals are unverified. Only five target 701 buses are included; other routes and passengers are not modelled. The late-entry case adds an assumed 180 seconds before Areosa. Intermediate references do not hold buses; MPL4 departures wait for its published time.

Outputs distinguish entry lateness, final lateness and delay added inside the section. Negative deviations mean early arrivals. No operator tolerance is assumed. Completed-only in-network times and all unserved requests remain visible. In one seed, the isolated LW2 → SVT4 intervention leaves all five buses unfinished; its benefit is withheld. Do not add individual interval effects or rank a policy by the surviving journeys. This model cannot yet establish whether buses will meet actual schedules or quantify workers' and shoppers' purpose-specific impacts.

## Reproduce and control using code

```sh
./prototypes/line-701/pilot.sh
./prototypes/line-701/pilot.sh --scenario /absolute/path/701-policy.json
```

The script uses the existing SUMO/Python environment; on a fresh checkout it bootstraps through the street prototype. Frozen official source responses and raw observations are inputs. Native output folders and large network files are ignored. `--quick` belongs to the experiment runner for a smoke run only; the complete website/replay requires a full batch.

Quick runner output is written separately to `quick-results.json`, preserving the full published results.

For a fresh bounded collection, explicitly run:

```sh
.venv/bin/python prototypes/line-701/collect_positions.py --duration 900 --interval 15
.venv/bin/python prototypes/line-701/analyse_observations.py
.venv/bin/python prototypes/line-701/build_site.py
```

Collection does not run in the background by default. A different service date needs refreshed official inputs and validation; this is a frozen dated pilot.

`prepare_replay.py` captures six native baseline/candidate clips at one-second resolution, 08:10–08:40. Vehicles shown are on the route and adjacent junction links; metrics use the full runs. The shared 3D model is flat, with OSM footprints and estimated building heights. It supports street inspection and following the same bus in both policies, but does not validate kerbs, safety or accessibility.

`build_site.py` publishes the new entry point, preserves the earlier page, generates [REPORT.md](REPORT.md), and creates `invicta-line-701-site.zip` (also copied to the older compatibility ZIP path). Host the extracted folder on any static HTTP(S) server. Keep both asset folders and `vendor/` together. The browser can export a bilingual explanation and record the new 3D view as WebM; the older MP4 films are labelled as the earlier street experiment.

## Next evidence to collect

Obtain repeated, complete inbound 701 trajectories with trip IDs, door-open arrivals/departures and passenger boarding/load counts. Audit the current lane directions and widths, signal phases, bus stop layouts and the property/loading/turn access inventory. Analyse time of day, inherited delay and dwell separately. Validate this section, add other bus services and affected traveller demand, then extend to the full line and opposite direction.

## Verification

All 63 native runs completed, with failures retained in their results; all three packages have 15/15 completed stop sequences in each demand case. All runs reported zero collision records. Geometry, connections and signal programs match across variants after removing only lane permission attributes; the baseline bytes match the original import. The no-change `leg_08` control reproduces baseline buses and vehicle-group results exactly in every seed. `leg_10` also has identical outcomes, although it does change two lane permissions; this illustrates the limits of the generated traffic coverage. All 26 frozen official response hashes match the provenance manifest.

Browser checks covered PT/EN, all 13 stop rows and 12 interval controls, incomplete bus accounting, untested drafts without invented metrics, draft URL restoration, validated CSV import with user-supplied labels, and a 390px layout without page overflow. Six native clips each contain 1,801 one-second frames. Bus-follow 3D and recording were exercised; `ffprobe` confirmed the recording is VP9 WebM at 1920×1080. Every file in the static export matches the generated ZIP. No production test suite was added.

Independent review identified and prompted fixes for repeated CSV uploads and cross-date GPS attribution. A corrected upload for the same trip now replaces its earlier values. Replaying the complete GPS sample one day later rejects all 48 unique positions instead of comparing them with the frozen timetable.
