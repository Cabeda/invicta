# Line 701: full inbound Porto extent to Bolhão

Verified on **28 October 2026**, using public official STCP APIs retrieved at **19:45–19:53 UTC** and DGT boundary sources retrieved at **19:45–19:48 UTC**. This extends the existing Areosa→Marquês schedule pilot. The service date remains **Wednesday 28 October 2026**, direction **1 / Bolhão / VOLTA**, service `UTIL ESCOLAR:FLUXO 3 20261027`. The fresh stops, 548-point shape and 63-trip route timetable are byte-identical to the earlier snapshot. [Date-resolved service](https://stcp.pt/api/route/701/services?date=2026-10-28), [official stops](https://stcp.pt/api/route/701/stops/direction?direction_id=1), [shape](https://stcp.pt/api/route/701/shape?direction_id=1), [route timetable](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1).

## Confirmed endpoint and additional stops

The terminus is **Bolhão `0BLRB`**, direction stop sequence **56**, at **41.151940, −8.607110**. The initial character of its code is the digit **zero**. There are **16 stops from ARS3 through 0BLRB**. The three additions after the old endpoint MPL4 are:

| Sequence | Code | Stop | Latitude | Longitude | Official timing point |
|---|---|---|---|---|---|
| 54 | DCAS2 | Doze Casas | 41.158198 | −8.604619 | No |
| 55 | FTNH2 | Fontinha | 41.155645 | −8.604726 | No |
| 56 | 0BLRB | Bolhão | 41.151940 | −8.607110 | Yes |

These are stop records from the current direction API, not identification by name. **MPL4 and 0BLRB are the only designated timing points among the 16 stops.** The full direction designates COD4, ERM3, AM2, ARSM2, MPL4 and 0BLRB. Its route timetable explicitly marks these as `timepoint: 1`. [Stops and timing-point IDs](https://stcp.pt/api/route/701/stops/direction?direction_id=1), [route timetable](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1).

## Porto begins before Areosa, with no earlier Porto stop

An intersection against **DGT's CAOP2025 Municípios**, municipality **Porto / DTMN 1312**, confirms that **ARS3 is strictly inside Porto**, approximately **56.37 m** from the municipal boundary. Its preceding stop **ARSM2 / Areosa (Mercado)** is in **Gondomar**, approximately **135.56 m** outside Porto. Testing all 56 direction stop positions found no earlier stop inside Porto; all 16 positions ARS3→0BLRB are inside. This is a calculated overlay of STCP coordinates and the official polygon, not an on-street survey. [DGT Porto municipal feature](https://ogcapi.dgterritorio.gov.pt/collections/municipios/items/1312?f=json), [three municipalities around Areosa](https://ogcapi.dgterritorio.gov.pt/collections/municipios/items?f=json&bbox=-8.585,41.178,-8.579,41.186&limit=20), [DGT CAOP dataset](https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-tematica/caop).

The **entire inbound shape crosses Porto's boundary exactly once**, at **longitude −8.5832957540, latitude 41.1811205245**, between official shape sequences **407 and 408**. ARS3 is sequence **409**. Thus, to include the entire route inside Porto, retain the **59.66 m approach before ARS3**, rather than starting only at the Areosa stop. The clipped route continues to Bolhão without leaving Porto.

Distances calculated in **EPSG:3763 / ETRS89 Portugal TM06** are:

| Measure | Metres |
|---|---:|
| Full direction shape chainage at Porto entry | 11,652.654161 |
| Full direction shape chainage at ARS3 | 11,712.310728 |
| Porto boundary→ARS3 along shape | 59.656567 |
| ARS3→0BLRB along shape | 4,485.508398 |
| Entire Porto portion, boundary→0BLRB | 4,545.164965 |
| Full direction shape | 16,197.819126 |

The raw OGC API GeoJSON uses **CRS84, longitude then latitude**; the collection documents storage CRS EPSG:3763. Distances above come from projection before measurement, not degree distances. Boundary classification uses the unbuffered polygon. Published STCP and CAOP positions are cartographic references; their numeric precision does not establish surveyed road-edge precision. [DGT collection metadata](https://ogcapi.dgterritorio.gov.pt/collections?f=json).

**No official schedule time exists at the municipal boundary.** A simulation may set a boundary entry lead relative to the first ARS3 reference, but must label that lead as an assumption. Retain ARS3 as the first published schedule reference used for entry punctuality.

## Complete morning scheduled reference

The same five trips selected by **08:00 inclusive ≤ ARS3 scheduled arrival < 09:00** remain selected. All times below are **Europe/Lisbon**. These are operator-published scheduled references, not measured stop passages. Only the two marked rows are designated timing points. [ARS3 schedule](https://stcp.pt/api/stops/ARS3/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1), [DCAS2 schedule](https://stcp.pt/api/stops/DCAS2/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1), [FTNH2 schedule](https://stcp.pt/api/stops/FTNH2/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1), [0BLRB schedule](https://stcp.pt/api/stops/0BLRB/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1).

| Sequence | Stop | Code | A | B | C | D | E |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 41 | Areosa | ARS3 | 08:12:50 | 08:23:50 | 08:34:50 | 08:45:50 | 08:57:43 |
| 42 | Alto da Areosa | AA2 | 08:13:46 | 08:24:46 | 08:35:46 | 08:46:46 | 08:58:31 |
| 43 | António Coelho | ACO2 | 08:14:40 | 08:25:40 | 08:36:40 | 08:47:40 | 08:59:17 |
| 44 | S.ta Justa | STJ3 | 08:15:54 | 08:26:54 | 08:37:54 | 08:48:54 | 09:00:21 |
| 45 | Barrocas | BRRS2 | 08:17:13 | 08:28:13 | 08:39:13 | 08:50:13 | 09:01:28 |
| 46 | Conde Ferreira | CF2 | 08:18:17 | 08:29:17 | 08:40:17 | 08:51:17 | 09:02:23 |
| 47 | Luis Woodhouse | LW2 | 08:19:27 | 08:30:27 | 08:41:27 | 08:52:27 | 09:03:23 |
| 48 | Silva Tapada | SVT4 | 08:20:03 | 08:31:03 | 08:42:03 | 08:53:03 | 09:03:54 |
| 49 | Pires de Lima | PLIM2 | 08:21:34 | 08:32:34 | 08:43:34 | 08:54:34 | 09:05:12 |
| 50 | Combatentes | COMB4 | 08:22:23 | 08:33:23 | 08:44:23 | 08:55:23 | 09:05:54 |
| 51 | Lima | LIMA2 | 08:23:52 | 08:34:52 | 08:45:52 | 08:56:52 | 09:07:11 |
| 52 | Marquês | MPL7 | 08:25:15 | 08:36:15 | 08:47:15 | 08:58:15 | 09:08:21 |
| 53 | Marquês (timing point) | MPL4 | 08:26:00 | 08:37:00 | 08:48:00 | 08:59:00 | 09:09:00 |
| 54 | Doze Casas | DCAS2 | 08:27:45 | 08:38:45 | 08:49:45 | 09:00:24 | 09:10:24 |
| 55 | Fontinha | FTNH2 | 08:28:49 | 08:39:49 | 08:50:49 | 09:01:15 | 09:11:15 |
| 56 | Bolhão (timing point) | 0BLRB | 08:31:00 | 08:42:00 | 08:53:00 | 09:03:00 | 09:13:00 |

| Column | Full route trip ID | ARS3→MPL4 | MPL4→0BLRB | ARS3→0BLRB |
|---|---|---|---|---|
| A | `701_0_2\|327\|D1\|T2\|N2` | 13m10s | 5m00s | 18m10s |
| B | `701_0_2\|327\|D1\|T6\|N4` | 13m10s | 5m00s | 18m10s |
| C | `701_0_2\|327\|D1\|T9\|N4` | 13m10s | 5m00s | 18m10s |
| D | `701_0_2\|327\|D1\|T7\|N5` | 13m10s | 4m00s | 17m10s |
| E | `701_0_2\|327\|D1\|T4\|N4` | 11m17s | 4m00s | 15m17s |

The per-stop API omits `trip_id`, so the associations above are **derived**. The extension verifies more than a plausible sorted join:

1. Each of the 17 fetched stop timetables, including upstream ARSM2, contains exactly **63 unique times**; the route has 63 unique trip IDs.
2. ARSM2, MPL4 and final 0BLRB each have 63 unique route times in the same trip order. Every per-stop anchor time equals the corresponding route-trip time exactly.
3. For each of the 14 intermediate stops, construct a graph allowing an arrival to match a trip only when it falls between that trip's adjacent known timing points: ARSM2→MPL4 upstream, MPL4→0BLRB downstream. The chronological rank join is a valid complete assignment of all 63 arrivals to all 63 trips.
4. Independently remove each of the 63 rank-assignment edges and recompute maximum matching. **Every removal reduces the maximum matching size to 62**, at every intermediate stop. Therefore no alternative complete assignment exists under the one-arrival-per-trip and timing-point-window constraints. This proves the join's uniqueness without a trip-order assumption.
5. Every joined trip's 17 stop times strictly increase, and the five morning IDs equal the old pilot's IDs.

Some upstream arrivals individually fit two timing-point windows; the complete one-to-one matching resolves them. DCAS2 and FTNH2 each have only one candidate trip even before global matching. The proof establishes a coherent unique schedule association, not independently exposed intermediate trip IDs, observed vehicle order, actual dwell, or punctuality. All fetched arrival and departure references are identical at each stop; do not interpret that equality as measured zero dwell. The inspected API does not document its intermediate-time interpolation algorithm.

## Preserve the ordered shape and the correct date

The official shape has **548 points**; ARS3→Bolhão uses shape sequences **409–548 inclusive**. Important stop-to-shape matches are MPL7 **499**, MPL4 **505**, DCAS2 **518**, FTNH2 **526**, final 0BLRB **548**. The shape continues south and bends west/east between MPL4 and DCAS2, and turns west then south after Fontinha. Preserve these ordered turns when mapping to the native road graph; straight stop-to-stop links would omit them. The raw shape has no exposed `shape_id`, per-trip branch ID or street names. [Official shape](https://stcp.pt/api/route/701/shape?direction_id=1).

The notified inbound route remains **Rua de Costa Cabral→Rua da Alegria→Rua da Constituição→Praça do Marquês**, with MPL7 restored from 15 October. These notices and the shape jointly constrain the Marquês approach. [Costa Cabral notice](https://stcp.pt/pt/viajar/alteracoes-de-servico/varias-linhas-alteracao-percurso-alt-sentido-transito-r-costa-cabral-porto), [MPL7 restoration](https://stcp.pt/pt/viajar/alteracoes-de-servico/normalizacao-de-paragem-obras-r-constituicao-porto-1).

A new Santa Catarina works notice applies **29 October 23:00→30 October 07:00**, routing the inbound bus through Latino Coelho, Alegria and Escola Normal. **It does not apply to the 28 October morning experiment.** The notice is saved to make that temporal distinction explicit. [Official future diversion](https://stcp.pt/pt/viajar/alteracoes-de-servico/alteracao-de-percurso-obras-r-santa-catarina-porto-1).

## Full-line scheduled service layer

The whole inbound line can be represented as a **scheduled service layer** while native road/traffic context remains the 4.545 km Porto portion. The complete verified timetable is [`full-line-service-facts.json`](../../prototypes/line-701/data/official-extension/full-line-service-facts.json). It includes all **56 direction stops**, **six timing points**, **63 trips**, and each trip's 56-key stop-time mapping in integer seconds after local service-day midnight. [Complete stop list](https://stcp.pt/api/route/701/stops/direction?direction_id=1), [six-point route timetable](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1).

The current route timetable provides stronger origin evidence than the earlier pilot documented. It identifies **39 trips beginning at Codiceira COD4**, whose route timing-point stop sequences are `1,22,28,40,53,56`, and **24 trips beginning at Ermesinde (Estação) ERM3**, whose sequences are `null,1,7,19,32,35` for COD4, ERM3, AM2, ARSM2, MPL4 and 0BLRB. The short workings have explicitly null COD4 arrival/departure/sequence, then ERM3 at **trip-specific stop_sequence=1**. All 21 early-stop APIs contain 39 unique arrivals, and all 35 stops from ERM3 onward contain 63. Their counts, first sequence and exact suffix sequences agree. **Do not create Codiceira departures for the 24 Ermesinde workings.** [Route timetable](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1), [COD4 stop timetable](https://stcp.pt/api/stops/COD4/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1), [ERM3 stop timetable](https://stcp.pt/api/stops/ERM3/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1).

| Service pattern | Trips | First stop | Last stop | Served stops per trip | Missing/unserved cells |
|---|---:|---|---|---:|---:|
| Full working | 39 | COD4 | 0BLRB | 56 | 0 |
| Short working | 24 | ERM3 | 0BLRB | 35 | 21 per trip |

All **50 non-timing stops** were joined using the adjacent timing-point graph proof described above, restricting the COD4→ERM3 interval to the 39 full workings. Every join has a unique complete matching; removing any rank edge reduces maximum matching by one. The six direct route timing-point tables equal their corresponding per-stop APIs. All served per-trip times strictly increase. The result contains **3,024 published reference times** and **504 nulls** exactly corresponding to the unserved 21 upstream stops on 24 short workings; there are **zero ambiguous cells**. The JSON retains trip IDs, origin evidence, patterns, trip-specific stop sequences, per-stop status and matching checks.

This permits scenario logic that propagates scheduled departure and delay state from the true origin across the full line and into/out of Porto. It does **not** verify bus blocks, which vehicle performs the next trip, layover/recovery time, observed upstream congestion, minimum feasible headway, tailgating or queue spillback. Those dynamics require explicit model assumptions or additional evidence. Extending schedule propagation across the line must not be described as calibrated microscopic traffic simulation outside the native road network.

## Frozen source bundle and limits

The bundle is [`prototypes/line-701/data/official-extension/`](../../prototypes/line-701/data/official-extension/). [`metadata.json`](../../prototypes/line-701/data/official-extension/metadata.json) records the full source URL, UTC retrieval interval, HTTP status, size and SHA-256 for **69 raw responses**, all verified against their stored bytes. This includes the date-resolved service, fresh complete direction stops/shape/route timetable, 56 per-stop timetables, official DGT polygon/collection/query schema and dated route notices.

[`extension-facts.json`](../../prototypes/line-701/data/official-extension/extension-facts.json) contains the 16 stops, designated timing points, five-trip full reference matrix, raw-source URLs, all 56 stop boundary classifications, geometry chainage and the complete uniqueness checks. [`joined_stop_times.json`](../../prototypes/line-701/data/official-extension/joined_stop_times.json) preserves the full 63-trip × 17-stop derived timetable. [`porto_route_clip.geojson`](../../prototypes/line-701/data/official-extension/porto_route_clip.geojson) is the derived municipal clip with its boundary entry point. DGT publishes CAOP as open data under **CC BY 4.0**; attribute **Direção-Geral do Território — CAOP2025**. [DGT open-data terms](https://www.dgterritorio.gov.pt/dados-abertos).

Still unverified: actual morning vehicle passages/traffic, stop dwell, current intermediate-time interpolation method, on-street positional accuracy, and final street/turn matching in the imported native network. The source does establish the current direction, terminal stop, date-selected timetable and the full municipal extent.
