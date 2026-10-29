# 701: complete bidirectional native traffic simulation

## What was actually run

Native SUMO covers both complete directions, all 127 scheduled workings and 6024 served scheduled calls: 63 towards Bolhão and 64 towards Codiceira/Ermesinde. Short workings retain their true endpoints; 960 unserved timetable cells are not invented departures.
The service reference is 2026-10-28. Runs begin 05:00 and include service after midnight through 25:35, plus clearance until 27:35. Cases: moderate, busy, late; seeds: [17]; 6 native runs.
The native buses share one regional road simulation with ordinary traffic, residents, taxis, bicycles and motorcycles. Both directions interact on the imported network. No other bus line or physical vehicle block/rotation is invented.

## How to read the comparison

Baseline and priority use the same requested demand for each case/seed. Keep unfinished and unroutable requests in the comparison. A lower mean among completed trips cannot establish an improvement for everyone if other trips never finish. Entry waiting and in-network duration are reported separately; these are not door-to-door person travel times. These are conditional simulation outcomes, not measured recurring city delays.

|Case|Policy|Seed|Inbound completed/63|Outbound completed/64|Served calls/6024|Unserved all vehicles|Late timing-point calls|Missing timing-point calls|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|moderate|baseline|17|28|23|3094|11797|80|306|
|moderate|restricted|17|63|64|6024|0|173|0|
|busy|baseline|17|10|4|1177|34922|62|531|
|busy|restricted|17|7|4|1116|35140|54|529|
|late|baseline|17|10|4|1177|34922|63|531|
|late|restricted|17|7|4|1116|35140|55|529|

## What changed in the prepared proposal

Priority reserves one mapped bus-capable lane on 105 directed edges. General traffic is retained on 321 screened route edges. Existing bus-only lanes remain. The combined policy disconnects 0 of 191 generated connector/OD test pairs.
This is a generated connectivity screen, not proof of legal access, driveways, loading capacity, emergency routes or equitable access. Lane permissions change; the same imported geometry and signal assumptions are used in both policies.

## What the animation shows

The browser replay covers the complete line in both directions during 16:50–18:20, sampled from native output every 5 seconds and interpolated visually. The underlying traffic simulation uses its original one-second step. Vehicles are shown on route roads and roads meeting their junctions; the scene includes a wider 150m context. Numeric traffic totals cover the regional experiment. The replay is extracted from the same full-day execution as its numeric run. Scene/capture/network hashes and exact windows are validated through the replay manifest.

## Evidence and limits

Synthetic regional OD requests with explicit hourly weights; not measured counts or calibrated population travel.
Unavailable; each scheduled working is a separate native bus, no invented vehicle rotation.
One bus-only straight-turn exception near Asprela/Costa Cabral resolves a conflict between imported OSM restriction 16086845 and both the official outbound shape and OSM bus-route relation 10107392. It applies equally to baseline and priority; ordinary traffic keeps the imported restriction. This is a documented modelling assumption pending street/operator confirmation.
Imported OSM one-way rules, lane counts and signals are not surveyed. Signals are guessed/unverified. Stops are snapped to native lanes with at least 15m usable stop space; the full bus-only validation must serve all 127 workings and 6024 calls. Ordinary traffic demand uses an explicit synthetic hourly profile, not metropolitan population, modal-choice calibration or observed OD counts. Dwell is fixed 20 seconds; the separate passenger/berth model retains its own assumptions. Real boarding loads, driver duties, other lines and fleet circulation remain missing.
Timetable data is frozen for 28 October 2026. Direction 0 geometry and regional OSM have their own recorded retrieval dates; historical applicability is not established by the timetable date.
The bus-only control still has 154 late timing-point arrivals out of 714 planned calls under the fixed-dwell and imported-signal assumptions. Traversable geometry does not establish a calibrated timetable model. Priority alone must not be presented as proving zero tardiness under these assumptions.

## Reproduce and inspect

`./prototypes/line-701/full/run.sh --cases moderate,busy,late --seeds 17` (use `--seeds 17,42,73` for repeated seeds).
Raw results: 701-full-experiments.json. Route mapping:701-full-routes.json. Street provenance:701-full-network-manifest.json. Replay provenance:line-701-full-assets/manifest.json. Timetable bundles:701-extension/ and 701-outbound/. [Source code and frozen input archive](https://github.com/Cabeda/invicta/tree/prototype/costa-cabral-access/prototypes/line-701/full).

## Transition interpretation

This experiment first holds requested traffic demand constant to test street priority. Longer-term shifts from cars to reliable buses, cycling or walking are a separate scenario assumption, not an uptake prediction. The metropolitan transition calculator remains available in the earlier study. Deployment phases and costs still require an access survey, operator input, signal plans and local cost evidence.
