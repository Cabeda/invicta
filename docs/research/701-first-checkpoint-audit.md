# 701 first checkpoint audit — 29 October 2026

## Confirmed timetable and applicability

The frozen reference is **Wednesday, 28 October 2026**. A fresh read of STCP's [date-resolved services API](https://stcp.pt/api/route/701/services?date=2026-10-28) still resolves `UTIL ESCOLAR:FLUXO 3 20261027` for that date. The response's changing list of available services and `today` field should not invalidate an otherwise identical historical timetable. The per-trip weekday booleans remain false and the date range null; the explicit date resolver supplies applicability.

The [official inbound route timetable](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1) confirms trip `701_0_2|327|D1|T8|N2`: Codiceira (`COD4`, sequence 1) **05:25:00**, Ermesinde Estação (`ERM3`, sequence 22) **05:33:00**. Both arrival and departure references are equal. Its later timing points are Alto da Maia 05:38, Areosa Mercado 05:45, Marquês 05:53 and Bolhão 05:57. This is a full Codiceira working, not one of the Ermesinde-origin short workings. There are 20 non-timing stops between its first two checkpoints. Current route/stop evidence does not show a special early-morning bypass variant.

Fresh API bytes match the previously frozen files exactly:

| Official source | SHA-256 |
|---|---|
| Route timetable, direction 1, service `…20261027` | `3e20d21e40b9d6ae81bad9f7fa31a41e75c31a466231059a67f9de09c34d1eb1` |
| [Direction stop list](https://stcp.pt/api/route/701/stops/direction?direction_id=1) | `8e97c5a48b737e37b3a5289e0794ca0761d619ed34868329fa7372da1daa029d` |
| [Direction shape](https://stcp.pt/api/route/701/shape?direction_id=1) | `a7123c79d83a9f53138ddcabc5a33bde4af06d2a48af81ed821be6af3f76b7fd` |

The archive `data/official/municipal_latest_gtfs.zip` declares `feed_start_date=20260901`, `feed_end_date=20260923`. It cannot establish applicability for 28 October. The existing current operator API reference is the appropriate frozen authority for this experiment.

A separate check of [29 October services](https://stcp.pt/api/route/701/services?date=2026-10-29) resolves the newer `UTIL ESCOLAR:FLUXO 3 20261029`, first trip `701_0_2|328|D1|T8|N2`; its first six timing-point times remain identical. This does not automatically update or validate the remaining frozen service day. Retrievals are retained locally under `.cache/701-first-checkpoint-audit/`.

## Confirmed native matching defect at Alfena

The **official shape and the version-3 native path disagree**, independently of the timetable grader. The official shape continues south along Rua de São Vicente past Alfena (`ALF`, 41.240758, -8.525564). Its successive shape points include:

- 50: 41.240890, -8.525480
- 51: 41.240758, -8.525564 (Alfena)
- 52: 41.240540, -8.525510
- 53: 41.240094, -8.525548
- 54: 41.239737, -8.525579

The version-3 `routes.json` instead assigns Alfena to **Rua Coroa**, edge `-460560653#1`, position 55.7 m, **49.5 m from the operator stop coordinate**. Its path leaves São Vicente eastward via Rua Nova de Alfena, returns through Rua Coroa, then loops west through Rua da Várzea before continuing south to Travessa da Costa. Those spur loops are absent from the operator shape in this location.

`full/prepare.py:map_direction` rejects stop candidate edges shorter than 16 m, imposes an offset of at least 15 m and then selects among six heading/distance candidates. Crossing import fragments the actual adjacent road. The appropriate southbound São Vicente edge `-215493217#2` is only **13.86 m** long and **4.27 m** from the official coordinate, so it is excluded by that length filter. Its neighbouring southbound edge `-215493217#3` is only 7.73 m long. Neither can be selected under the present stop rule.

The native topology does contain the straight southbound bus connections:

`-215493217#1 → -215493217#0 → -1103653946 → -1101562418#1`.

Thus the observed spur loops are **not necessary for bus connectivity** at this junction. The stop matching and its route-choice scoring need correction before using this import to infer how much the first interval can be improved. A model correction must apply to baseline and proposal, preserve its own source identity, and be distinguished from a proposed physical street intervention.

## What remains unproven

The known 55-second miss in the zero-demand, zero-dwell, signals-off diagnostic is a **model outcome**, not proof that STCP's published interval is unattainable. The identified matching defect is a falsifiable contributor: rematch Alfena to the actual shape corridor, eliminate these spurs, then repeat the same frozen diagnostic before changing traffic policy. This audit does not quantify how many seconds that fix saves, establish actual stop dimensions, validate all other stops, or show compliance in ordinary traffic.

The underlying OSM topology and current API geometry are still not a field survey. There is no observed vehicle trajectory in this audit to establish exact stop footprints or validate real journey times. The corrected native path must be compared to the full official shape, since a stop within 55 m is insufficient proof of a correct road match.

## Follow-up: remaining version-4 Várzea detour

Version 4 accepts 12.2 m stop edges and maps Alfena to São Vicente. Its unchanged optimistic diagnostic improves the first Ermesinde miss from 55 to 37 seconds (parent's execution result); this does not qualify a traffic proposal. A second map-matching exclusion still sends the path through Rua da Várzea.

At official shape progress **1333.0357 m**, point 52 (41.240540, -8.525510), the non-stop anchor filter excludes edges shorter than 0.5 m. Crossing/junction import has reduced the correct connecting São Vicente fragments to approximately 0.2 m:

| Candidate at point 52 | Native edge length | Point distance | Heading cosine | Local distance/heading score | Filtered? |
|---|---:|---:|---:|---:|---|
| São Vicente `-215493217#0` | 0.20 m | 6.20 m | 0.99 | 6.41 | Yes |
| São Vicente `-215493217#1` | 0.20 m | 7.37 m | 1.00 | 7.43 | Yes |
| Várzea `169771420` | 3.55 m | 6.58 m | 0.41 | 27.08 | No; selected |
| São Vicente `-1103653946` | 0.20 m | 19.09 m | 1.00 | 19.16 | Yes |

This causes a spur via `169771420 → 169771431#1 → 1101562417 → 169771424`, whereas the official shape remains on São Vicente. Allowing positive short fragments for non-stop shape anchors is the direct falsifiable correction to test; a bus does not need to stop or fit entirely on an anchor edge.

The hypothesis that the matcher ignores internal junction distances is **not supported** by this inspection. On the `withInternal=True` network, `getShortestPath` from Alfena edge `-215493217#2` to `-1101562418#0` returns a cost of **82.71 m**, while its external edge lengths sum to only 32.95 m. The internal length contribution is present. The corresponding route through the Várzea anchor is longer. Removing the tiny-fragment candidate exclusion should be tested before changing this scoring or any vehicle physics.

## Public-only calibration check — 29 October 2026

**No validated public 701 boarding/alighting/load profile or trip-by-trip actual arrival/departure history was identified in this bounded check.** This is a search result, not proof those records do not exist. The synthetic demand remains uncalibrated. No authority was contacted and no credentials or access controls were bypassed.

| Public source inspected | What it can supply | Calibration limit |
|---|---|---|
| [STCP 701 vehicles](https://stcp.pt/api/route/701/vehicles?direction_id=1) and [Marquês realtime arrivals](https://stcp.pt/api/stops/MPL4/realtime) | Current trip IDs, direction, position, speed, service date; predicted arrivals/delay estimates. STCP [announces](https://stcp.pt/pt/noticias/a-rede-stcp-em-tempo-real) its public live map and route/direction filters. | The sampled vehicle's own timestamp was null; the response has a retrieval timestamp. A predicted future ETA is not a measured stop arrival/departure. No passenger counts or historical query is established by these endpoints. |
| [Porto open bus locations catalogue](https://dadosabertos.cm-porto.pt/dataset/urban-platform-bus-location), [public NGSI feed](https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType==bus&limit=1000) | Fleet ID, trip/direction annotations, GPS, speed and `observationDateTime`; the catalogue marks reuse **CCZero**. | Latest entity states, not a verified historical archive. Five 701 entities in the 22:56 UTC sample carried 09:44:58–09:45:06 observation times, roughly 13 hours old. No occupancy/boarding/alighting field occurred among the 215 returned bus entities. |
| Porto's [2024 STCP contract-monitoring report](https://mobilidade.cm-porto.pt/files/uploads/cms/Relat%C3%B3rio%20STCP%202024.pdf), §2.2.2–2.2.3 | A pooled punctuality measure: 92.3% over 6,835 first/last-trip inspection records across twelve lines, including 701; network-wide occupancy. | No isolated 701 distribution, intermediate-stop trajectory or boarding/alighting profile. It cannot calibrate each 701 stop/time band. |
| Independent [STCP Watch 701 page](https://stcp.02wow.net/linhas/701), [quality page](https://stcp.02wow.net/qualidade), [public one-day CSV](https://stcp.02wow.net/api/export/wait-events.csv?from=2026-10-28&to=2026-10-28) | Historical rider-wait summaries by line/direction/stop and an export with scheduled/served times, wait seconds and `served_by_gps`. This is a first-party publication of an independent collector's own derived metrics, **not an official STCP performance report**. | Quality and semantics are insufficient for adoption as actual trip timing; see below. No passenger counts or reuse licence was verified. |

The independent export has **no trip ID** or observed departure column. Its wait metric concerns the next bus serving someone who arrives at the scheduled time, so it cannot be equated with the delay of that specific scheduled trip. The bounded CSV prefix contained 31 records for 701, all `served_by_gps=0`; this is a partial sample, not a complete daily count. The fresh quality page reported **26.1% matching**, below its own 80% acceptance criterion, and **222.5% daily coverage**, an unresolved denominator warning. Neither its headline averages nor the `served_arrival` field should be imported as validated bus trajectories without documenting the matching, missingness, prediction/GPS distinction and clipping rules. It is a useful lead for further audit, not a substitute for measured arrivals.

The catalogue and public website scripts advertise current location/ETA and scheduled-service endpoints; no documented historical endpoint or public passenger profile was found. Searches covered STCP, municipal open-data/monitoring sources and public line-specific performance leads. Raw probe responses and a timestamp/SHA manifest are retained under `.cache/701-first-checkpoint-audit/observations/`; they are not republished as licensed calibration data.

A public-data-only next step is to **collect a future observation series** from the official public feeds at a modest rate, retaining source observation time separately from retrieval time, rejecting stale entities, resolving trip IDs against that day's active service, recording coverage/gaps and distinguishing inferred stop passages from confirmed arrival/departure events. It needs several representative service days before validation; a single live snapshot is insufficient. Such collection still cannot supply boarding/alighting or occupancy when those fields are not published. Passenger demand must therefore stay an explicit sensitivity range until a suitable public source is found; network totals cannot make its flat synthetic profile factual.

## Posted-speed and locality-boundary check

**No current public evidence was verified that permits raising the first interval's assumed 50 km/h cap.** Missing OSM `maxspeed` tags do not establish signage, legal locality boundaries or a higher permitted bus speed. This conclusion follows a bounded public inventory/municipal-document search; it does not certify that every road is currently limited to 50 km/h.

Valongo exposes more detail than the earlier road-centreline schema: its public [vertical-sign table 13](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/13?f=pjson) has `CodigoSina`, `SINALTRANS`, `TextoSinal` and a declared `IDApoioSinal` relationship to [support-point layer 10](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/10?f=pjson). A query for C13/speed-labelled records returned **291 rows**, with 291 linked supports and no transfer-limit warning. The linked support dates range from June to November **2009**. Public access and a service name containing `2016` do not make this a current signage survey; reuse licensing remains unverified.

Screening those points within 40 m of the official inbound shape from Codiceira to Ermesinde Estação gives **nine candidates** (EPSG:3763 point-to-polyline distance). Four C13 maximum-speed records read **40, 30, 40 and 40 km/h** (support IDs 127, 5614, 4553 and 53). Other candidates include G4 zone-50 records, a blank G4 value and an H6 recommended-40 record. None of these nearby records states a speed above 50 km/h. Their support dates are 19 June or 15 July 2009; facing direction, applicability at adjacent junctions and present-day signs are not verified. H6 recommendations must not be confused with C13 mandatory maxima. Proximity alone cannot assign a sign to a bus movement or determine the extent of its effect.

The same service returned only four N1/N2 locality-entry/exit records municipality-wide. One old N1a names Alfena at approximately **41.249354, -8.512506**, north of the Codiceira origin. This small, dated inventory is insufficient to reconstruct current locality boundaries along the entire interval. The bounded Maia BaZe catalogue inspection and targeted official municipal searches did not locate a current posted-speed inventory or a corridor ordinance establishing higher limits.

Official municipal search results also contain old street-work/event plans, such as the [São Vicente temporary-signage plan](https://www.cm-valongo.pt/cmvalongo/uploads/writer_file/document/4188/plano_de_sinalizacao.pdf), which explicitly dates its works to **29 November–6 December 2021**. Search-engine publication dates must not be mistaken for the plan's effective dates. Those documents do not establish current operating speeds.

The public schemas, filtered records, linked points, source timestamps/hashes and reproducible 40 m screen are retained locally under `.cache/701-first-checkpoint-audit/speed-signs/`. No such record has been promoted into the simulation's speed limits. Correct next action: keep the cap labelled as an assumption, preserve existing lower tagged limits and require current sign/extent evidence before any baseline-speed correction. Raising a value merely to remove a diagnostic timing miss would not be an evidence-based proposal.
