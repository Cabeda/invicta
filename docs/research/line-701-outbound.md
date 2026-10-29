# Line 701: outbound official timetable and geometry snapshot

The frozen bundle in [`data/official-outbound/`](../../prototypes/line-701/data/official-outbound/) contains **58 public official JSON responses**, retrieved **29 October 2026, 10:24:56–10:24:58 UTC**. [`metadata.json`](../../prototypes/line-701/data/official-outbound/metadata.json) records every URL, HTTP status, retrieval interval, byte count and SHA-256. All stored hashes were verified before compiling the facts.

## Date and geometry have separate provenance

For **28 October 2026**, the date-resolved services API selects `UTIL ESCOLAR:FLUXO 3 20261027`. The route timetable for **direction 0** contains **64 unique trips**. Its nested `service_days` flags remain false/null; use the explicit date selection rather than interpreting those flags as no service. [Date-resolved services](https://stcp.pt/api/route/701/services?date=2026-10-28), [outbound route timetable](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=0).

The outbound direction list has **54 ordered stops**, from **Bolhão BLRB3** to **Codiceira COD4**, and six designated timing points: **BLRB3, MPL2, ARSM1, AM1, ERM4 and COD4**. Its bytes match the direction list frozen on 28 October. The freshly retrieved direction shape has **506 ordered coordinates**. [Official stop list](https://stcp.pt/api/route/701/stops/direction?direction_id=0), [official shape](https://stcp.pt/api/route/701/shape?direction_id=0).

**The shape is a 29 October retrieval, not verified historical geometry for 28 October.** The inspected official frontend requests shape with `direction_id`, while date selection is a separate service request; no historical shape-selection parameter was verified. The response exposes no shape ID or per-trip branch ID. The compiled facts preserve this distinction in `geometry_provenance`. Do not use the timetable's date resolution to assert the shape's historical validity. [Preserved official frontend](../../prototypes/line-701/data/official/route_js.js), [shape response](../../prototypes/line-701/data/official-outbound/outbound_shape.json).

## Working patterns and intermediate references

The complete per-stop schedules support three contiguous working patterns:

| Trips | First stop | Last stop | Served stops | Unserved cells per trip |
|---:|---|---|---:|---:|
| 41 | BLRB3 | COD4 | 54 | 0 |
| 22 | BLRB3 | ERM4 | 34 | 20 |
| 1 | ARSM1 | COD4 | 38 | 16 |

The route timing-point sequences are respectively `1,5,17,27,34,54`; `1,5,17,27,34,null`; and `null,null,1,11,18,38`. The early working is `701_0_1|327|D1|T7|N2`, with its first reference at **ARSM1 05:37**. All first non-null timing anchors have trip-specific sequence 1. Stops 1–16 each have **63** references, stops 17–34 each have **64**, and stops 35–54 each have **42**. The per-stop headsign counts agree with these ranges, including no Ermesinde-headsign references after ERM4. This supports ERM4 as the short workings' last served stop; it is not inferred solely from their headsign. [Route timetable](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=0), [BLRB3 references](https://stcp.pt/api/stops/BLRB3/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=0), [ARSM1 references](https://stcp.pt/api/stops/ARSM1/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=0), [ERM4 references](https://stcp.pt/api/stops/ERM4/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=0), [next-stop 1BVE3 references](https://stcp.pt/api/stops/1BVE3/schedule?route_id=701&service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=0).

Per-stop responses omit trip IDs. The adapter checks all **six direct timing-point tables** against their per-stop responses. At each of **48 non-timing stops**, it constructs the complete arrival-to-trip bipartite graph allowed by the adjacent timing-point windows. A complete matching exists. Removing each matched edge individually lowers maximum matching size by one, proving that every association is forced under the documented one-occurrence-per-trip and timing-window assumptions. This proof does not assume trip order or use headsigns to force a match. All served trip references strictly increase. The detailed proof and every source hash are retained in [`full-line-service-facts.json`](../../prototypes/line-701/data/official-outbound/full-line-service-facts.json).

The result is **3,000 published references**: **360 direct timing-point cells** and **2,640 uniquely derived intermediate cells**. There are **456 unserved null cells** and **zero unresolved associations**. Nulls remain explicit. References run from **05:37 to 25:35**; hours beyond 24 belong to the following calendar day of the same service. These are scheduled references, not observed passages. All fetched arrival and departure references are equal; that does not establish actual zero dwell. Only six stops are designated timing points, and the intermediate interpolation method remains undocumented. [Frozen raw timetables and source metadata](../../prototypes/line-701/data/official-outbound/metadata.json).

## Adapter contract and reproduction

[`fetch_outbound.py`](../../prototypes/line-701/fetch_outbound.py) uses the Python standard library and read-only official HTTPS GETs. It freezes the selected services, direction stop list, direction shape, route schedule and all per-stop schedules. Rebuild derived facts without network access:

```sh
python3 prototypes/line-701/fetch_outbound.py --compile-only
```

Fetch a fresh bundle and compile it:

```sh
python3 prototypes/line-701/fetch_outbound.py --date 2026-10-28
```

The default output folder is `prototypes/line-701/data/official-outbound/`; `--output` can select another folder. `--fetch-only` freezes inputs without compiling. Compilation rejects source hash mismatches, incomplete bundles, incompatible served ranges and non-increasing joined references. A nonunique intermediate association is retained as null with `unresolved_association`; it is never silently assigned to one trip.

The compiled JSON retains the existing `invicta.line701.full_line_service_facts.v1` core fields: `reference_date`, `active_service_id`, `direction_id`, `stoplist`, `timing_points`, `trip_patterns` and `trips[].stops`. It adds ordered `shape` coordinate objects, `geometry_provenance`, per-trip `departures`, `stop_time_status` and `terminalstatus`. `trip_stop_sequences` identifies the working's physical stop order. Status values are `published_timing_point`, `derived_unique_matching`, `unserved_working` and `unresolved_association`. `sources` provides the exact raw filenames, URLs and hashes; `matching_proof` records the validation results.

No outbound native SUMO replay, real vehicle passages, road calibration, passenger demand, vehicle rotations or layover evidence is supplied by this bundle. The existing inbound native Porto replay remains a separate prepared asset.
