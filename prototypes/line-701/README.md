# Line 701: Porto streets and whole-line reliability

**Question:** can the 701 meet its schedule throughout its inbound service without bunching, while keeping everyday access and passenger capacity workable? This is a throwaway investigation with two explicitly different layers.

- **Native Porto streets:** the entire mapped municipal extent, beginning about 60m before Areosa ARS3 and ending at Bolhão 0BLRB. Sixteen stops, 15 stop intervals, approximately 4.545km on the official shape.
- **Whole-line service:** all 56 stops and 63 inbound workings; 39 start at Codiceira, 24 at Ermesinde. A timetable/passenger/berth model tests delay propagation, dwell, capacity and headways. Road traffic outside Porto, the opposite direction, other lines and shared vehicle rotations are not simulated.

[Live demo](https://invicta-dusky.vercel.app) · [Detailed report](REPORT.md) · [Primary-source extent and timetable research](../../docs/research/line-701-porto-extent.md)

## Open locally

```sh
python3 -m http.server 8765 --directory prototypes/costa-cabral/proposal
# http://127.0.0.1:8765/?lang=pt
```

The bilingual website has the official map, five morning native journeys, stop profiles, fifteen interval policies, visible unserved demand, a whole-line delay/bunching explorer, CSV arrival import, 3D bus following, WebM recording and JSON/Markdown exports. The earlier street study and metropolitan what-if calculator remain in `legacy.html`.

## Verified reference, not a traffic forecast

The frozen date is **28 October 2026**, service `UTIL ESCOLAR:FLUXO 3 20261027`, direction 1 towards Bolhão. The full Porto stop sequence is:

`ARS3 → AA2 → ACO2 → STJ3 → BRRS2 → CF2 → LW2 → SVT4 → PLIM2 → COMB4 → LIMA2 → MPL7 → MPL4 → DCAS2 → FTNH2 → 0BLRB`.

After the two Marquês stops, the bus continues through Doze Casas, Fontinha and the Bolhão terminus. The actual source shape includes a loop via Bonjardim/João de Oliveira Ramos and then Santa Catarina, Gonçalo Cristóvão, Carvalheiras and Bolhão. Match the ordered shape rather than drawing a straight extension. A diversion published for 29–30 October is outside this dated pilot.

DGT CAOP2025 establishes that ARS3 is the first stop inside Porto. The route crosses the boundary 59.66m before it, at 41.1811205245,−8.5832957540. The official municipal clip is 4,545.16m measured in EPSG:3763. Native map-matched positions use the SUMO projection and can differ from cartographic distances. Stop/lane geometry still needs field validation.

The five Areosa references are 08:12:50,08:23:50,08:34:50,08:45:50,08:57:43; Bolhão references are 08:31,08:42,08:53,09:03,09:13. **MPL4 and 0BLRB are the two designated timing points inside Porto.** The whole inbound line has six designated timing points. Other stop seconds are published intermediate references, not exact observed passages or operator-agreed punctuality tolerances.

The per-stop API omits trip IDs. The full service dataset has 3,024 published references with derived trip IDs, uniquely matched against route timing-point anchors; the 504 nulls are only the 24 short workings' 21 unserved upstream stops. No Codiceira departures are invented for Ermesinde workings. All 69 newly frozen raw responses have hashes and retrieval times in `data/official-extension/metadata.json`.

## Native Porto experiment

`prepare_network.py` combines the original frozen OSM district with two additional southern tiles. It preserves the coordinate projection/offset and leaves the legacy study untouched. Every new policy shares the extended imported geometry, lane counts, connections and signals; it changes lane permissions only. The network is an unvalidated OSM import. Earlier 13-stop results are superseded; network/demand scope changed, so differences from that earlier batch are not policy gains.

`prepare_route.py` maps all 16 stops and the municipal approach onto 64 directed native edges. Boundary entry has no official scheduled time. Vehicles launch with an explicitly assumed 6-second lead before the Areosa reference; entry lateness is measured at Areosa and therefore also includes approach delay. The boundary-crossing edge is excluded from new permission policies. Interval policies affect whole native edges, with shared edges owned by the earlier interval.

New synthetic OD pairs cover the southern extension as well as valid earlier pairs. They are not actual residents' or shoppers' demand. The connectivity screen identifies newly unreachable pairs and static detours, including the combined policy. It cannot establish practical/legal access adequacy or operational capacity. A connectivity-screened candidate can still gridlock; all requested and unfinished journeys remain visible.

The full batch has **72 SUMO runs**: three seeds for three demand/entry cases and three packages, plus 15 isolated interval tests in the busy case. Only five target 701 buses are included. Dwell is fixed at 20s and signal programs are unverified. MPL4/0BLRB departures hold until their reference times. The late-entry case adds 180s before municipal entry.

The new candidate retains general flow in the first two intervals and in Marquês→Doze Casas→Fontinha where the generated connectivity screen finds losses. It is not an optimized or recommended design. In the busy case it completes 12/15 bus stop sequences, versus 15/15 for the baseline; in one seed it leaves 93 total vehicle requests unserved. Under assumed late entry its mean final deviation can also be worse than the baseline. The report and top-level counters preserve these failures. An individual interval's bus benefit is withheld when buses fail or a vehicle group has extra unserved demand.

## Whole-line bunching and cascade model

The service layer is a separate conditional model with all 63 workings and their actual scheduled patterns. It is not a full-road simulation outside Porto and is not automatically calibrated by the local SUMO results. Passenger demand, running-time recovery, capacity and dwell are assumptions exposed in the interface and JSON.

It processes arrivals chronologically, including overtaking, shared single-berth queues, fluid passenger arrivals, alighting, capacity limits and boarding dwell. A delayed bus can collect more passengers and slow further; a following bus can collect fewer and catch up. A no-injected-delay reference keeps the same passenger demand and other settings. The display counts changed other trips, actual adjacent departure pairs whose gap is below half their published-time separation, capacity-denied calls and residual waiting passengers.

Punctuality uses **boarding-berth access**, including a queue for the berth, rather than approach arrival. The strict project goal requires zero late arrivals at every designated timing point, no early departures there, no short-gap events, no capacity-denied boarding calls and no residual passenger queues. This is a test of an assumed model; real zero tardiness is not established. A headway hold can itself create delay, and bus benefits must not be manufactured by reducing requested demand. Times beyond 24:00 refer to the following calendar day of the same service.

```sh
node prototypes/line-701/service-cli.mjs
node prototypes/line-701/service-cli.mjs --config /absolute/path/701-service-scenario.json --output /absolute/path/result.json
```

The website exports both settings and full results. Needed evidence includes full-line AVL/door-open history, passenger loads and boarding rates, actual running/recovery/turnaround times, vehicle blocks and interactions with other routes. Fleet rotations and the reverse direction are particularly important before claiming that delays cannot cascade into later trips.

## GPS evidence and uploads

The existing bounded evening sample has 48 unique accepted positions across 59 polls. It yields 11 GPS-derived passage windows, including 10 on one journey. PLIM2→COMB4 is an investigative lead: deviation from the published reference grows by 137–258s on that single evening trip. These are nominal map-matched passage brackets, not door-open events. The sample does not cover that journey's Areosa/Bolhão endpoints and cannot calibrate morning demand or prove a recurring cause.

Raw positions remain in `data/observations/positions.ndjson`. Timestamp age, duplicates, current trip IDs, Lisbon observation date and shape progress are checked. CSV uploads match current service IDs and study stops, remain in browser memory, and are labelled user supplied. A later upload for the same trip replaces its earlier uploaded evidence. The dated observation importer covers the 28October evening sample; extending observation collection to overnight workings requires an explicit service-date association rather than reusing a calendar-date check.

## Rebuild, share and inspect

```sh
./prototypes/line-701/pilot.sh
./prototypes/line-701/pilot.sh --scenario /absolute/path/701-policy.json
```

The script reuses the project's pinned SUMO environment, compiles the frozen scope, imports the extended network, reruns experiments and regenerates the static site. Quick experiment output is separate in `quick-results.json`. No live collection runs by default. A changed service date requires updated official inputs.

Six native baseline/candidate clips cover 08:10–08:40 at one-second resolution; full metrics use all five morning journeys and the full simulation. The replay shows route/adjacent-junction traffic. Building footprints combine the frozen northern district with new southern OSM tiles; heights are source values where available and otherwise estimates. The model is flat and does not validate road safety, terrain, kerbs or pedestrian access.

`build_site.py` writes the entry page and report, keeps the legacy study, and creates `invicta-line-701-site.zip`. Extract and serve the complete folder over HTTP(S). Updates use the existing direct Vercel CLI workflow in [deployment notes](../../docs/DEPLOYMENT.md).

## Verification

All 72 native runs completed with zero collision records; incomplete journeys are retained. Geometry, connections and signals match across variants after removing only lane permission attributes. `leg_08` remains an unchanged-permission neutral control. The service model preserves 3,024 calls, all 63 origin patterns, fixed demand between reference/shock cases, passenger accounting and capacity bounds. An exact no-demand/no-dwell timetable control passes; overload cannot claim the goal is met. Review prompted corrections for berth-access lateness, overtaken bus gap detection and boarding-denial accounting.
