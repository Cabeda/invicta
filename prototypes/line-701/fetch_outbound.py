"""Freeze and validate official 701 outbound schedules using public read-only GETs.

The service date selects the timetable, not historical geometry. Run with
--compile-only to verify hashes and rebuild derived facts without network access.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import concurrent.futures
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "data/official-outbound"
BASE = "https://stcp.pt"
ROUTE = "701"
DIRECTION = 0


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read(folder: Path, name: str):
    return json.loads((folder / name).read_text())


def write(folder: Path, name: str, value) -> None:
    (folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def seconds(value: str | None) -> int | None:
    if value is None:
        return None
    hours, minutes, secs = map(int, value.split(":"))
    if hours < 0 or not 0 <= minutes < 60 or not 0 <= secs < 60:
        raise ValueError(f"Invalid service-day time: {value}")
    return hours * 3600 + minutes * 60 + secs


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def maximum_matching(candidates: list[list[int]], blocked=None) -> dict[int, int]:
    """Return a maximum trip-index to arrival-index matching, optionally deleting one edge."""
    assigned = {}

    def augment(arrival, seen):
        for trip in candidates[arrival]:
            if (arrival, trip) == blocked or trip in seen:
                continue
            seen.add(trip)
            if trip not in assigned or augment(assigned[trip], seen):
                assigned[trip] = arrival
                return True
        return False

    for arrival in range(len(candidates)):
        augment(arrival, set())
    return assigned


def fetch(folder: Path, name: str, url: str) -> dict:
    started = now()
    request = urllib.request.Request(
        url, headers={"User-Agent": "Invicta-701 outbound research; public read-only GET"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read()
        metadata = {
            "file": name, "url": url, "final_url": response.url,
            "retrieved_start_utc": started, "retrieved_end_utc": now(),
            "http_status": response.status, "http_date": response.headers.get("Date"),
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
            "size_bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
        }
    json.loads(body)  # Reject an HTML error page before replacing a frozen response.
    (folder / name).write_bytes(body)
    return metadata


def fetch_bundle(folder: Path, reference_date: str, workers: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    metadata = []
    # Save progress after every successful request; compilation rejects incomplete bundles.
    def record(entry):
        metadata.append(entry)
        write(folder, "metadata.json", metadata)

    record(fetch(folder, "services.json", f"{BASE}/api/route/{ROUTE}/services?date={reference_date}"))
    services = read(folder, "services.json")
    if services.get("selected_date") != reference_date.replace("-", ""):
        raise ValueError("Service response does not select the requested reference date")
    service = services.get("active_service_id")
    if not service:
        raise ValueError("No active service for the requested reference date")
    record(fetch(folder, "outbound_stops.json", f"{BASE}/api/route/{ROUTE}/stops/direction?direction_id={DIRECTION}"))
    stops = read(folder, "outbound_stops.json")
    if not stops.get("success") or stops.get("direction_id") != DIRECTION:
        raise ValueError("Unexpected outbound stop-list response")
    route_params = urllib.parse.urlencode({"service_id": service, "direction_id": DIRECTION})
    stop_params = urllib.parse.urlencode({"route_id": ROUTE, "service_id": service, "direction_id": DIRECTION})
    jobs = [
        ("outbound_shape.json", f"{BASE}/api/route/{ROUTE}/shape?direction_id={DIRECTION}"),
        ("schedule.json", f"{BASE}/api/route/{ROUTE}/schedule?{route_params}"),
    ] + [
        (f"stop_schedule_{stop['stop_id']}.json", f"{BASE}/api/stops/{stop['stop_id']}/schedule?{stop_params}")
        for stop in stops["stops"]
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, folder, name, url): name for name, url in jobs}
        for future in concurrent.futures.as_completed(futures):
            record(future.result())
    write(folder, "metadata.json", sorted(metadata, key=lambda entry: entry["file"]))


def compile_facts(folder: Path, reference_date: str) -> dict:
    metadata = read(folder, "metadata.json")
    raw_stops = read(folder, "outbound_stops.json")
    stops = sorted(raw_stops["stops"], key=lambda stop: stop["stop_sequence"])
    stop_ids = [stop["stop_id"] for stop in stops]
    expected_files = {"services.json", "outbound_stops.json", "outbound_shape.json", "schedule.json"}
    expected_files.update(f"stop_schedule_{sid}.json" for sid in stop_ids)
    check(len(metadata) == len(expected_files), "Raw response metadata count does not match the full bundle")
    check({entry["file"] for entry in metadata} == expected_files, "Incomplete or duplicate raw response metadata")
    byfile = {entry["file"]: entry for entry in metadata}
    for entry in metadata:
        body = (folder / entry["file"]).read_bytes()
        check(entry["http_status"] == 200, f"Non-success HTTP status: {entry['file']}")
        check(len(body) == entry["size_bytes"], f"Source size mismatch: {entry['file']}")
        check(hashlib.sha256(body).hexdigest() == entry["sha256"], f"Source hash mismatch: {entry['file']}")
    services = read(folder, "services.json")
    service = services["active_service_id"]
    check(services["selected_date"] == reference_date.replace("-", ""), "Reference date differs from the frozen services response")
    check(raw_stops["direction_id"] == DIRECTION and raw_stops["route_id"] == ROUTE, "Wrong route or direction stop list")
    check(len(set(stop_ids)) == len(stops), "Repeated stop IDs require a different adapter")
    check([stop["stop_sequence"] for stop in stops] == list(range(1, len(stops) + 1)), "Direction stop order is not contiguous")
    check(all(math.isfinite(stop[key]) for stop in stops for key in ("stop_lat", "stop_lon")), "Invalid stop coordinates")
    byid = {stop["stop_id"]: stop for stop in stops}
    tpids = sorted(raw_stops["timepoint_stop_ids"], key=lambda sid: byid[sid]["stop_sequence"])
    check(tpids[0] == stop_ids[0] and tpids[-1] == stop_ids[-1], "The complete direction must have endpoint timing anchors")
    shape_response = read(folder, "outbound_shape.json")
    check(shape_response.get("success") and shape_response["direction_id"] == DIRECTION and shape_response["route_id"] == ROUTE, "Unexpected shape response")
    shape = sorted(shape_response["coordinates"], key=lambda point: point["sequence"])
    check([point["sequence"] for point in shape] == list(range(1, len(shape) + 1)), "Shape coordinates are not a complete ordered sequence")
    check(len(shape) >= 2 and all(math.isfinite(point[key]) for point in shape for key in ("lat", "lng")), "Invalid shape coordinates")

    raw_schedule = read(folder, "schedule.json")
    check(raw_schedule["direction_id"] == DIRECTION and raw_schedule["route_id"] == ROUTE and raw_schedule["service_id"] == service, "Wrong route timetable service or direction")
    check([stop["stopId"] for stop in raw_schedule["selected_stops"]] == tpids, "Route timetable timing points differ from the direction list")
    check(all(stop["timepoint"] == 1 for stop in raw_schedule["selected_stops"]), "Unexpected route timetable timing-point status")
    trips = raw_schedule["schedule"]
    check(trips and len({trip["trip_id"] for trip in trips}) == len(trips), "Trip IDs are missing or duplicated")
    routes, ranges = {}, {}
    for trip in trips:
        tid = trip["trip_id"]
        check(trip["direction_id"] == DIRECTION and trip["service_id"] == service, f"Trip service or direction mismatch: {tid}")
        check([stop["stop_id"] for stop in trip["stops"]] == tpids, f"Trip has unexpected timing points: {tid}")
        anchors = {stop["stop_id"]: stop for stop in trip["stops"]}
        routes[tid] = anchors
        active = [stop for stop in trip["stops"] if stop["arrival_time"] is not None]
        check(active and active[0]["stop_sequence"] == 1, f"Physical origin cannot be established from the first anchor: {tid}")
        for stop in trip["stops"]:
            check((stop["arrival_time"] is None) == (stop["departure_time"] is None) == (stop["stop_sequence"] is None), f"Inconsistent unserved anchor: {tid}")
        offset = byid[active[0]["stop_id"]]["stop_sequence"] - 1
        check(all(byid[stop["stop_id"]]["stop_sequence"] - stop["stop_sequence"] == offset for stop in active), f"Anchor sequences do not support a contiguous pattern: {tid}")
        first = byid[active[0]["stop_id"]]["stop_sequence"]
        last = byid[active[-1]["stop_id"]]["stop_sequence"]
        check([stop["stop_id"] for stop in active] == [sid for sid in tpids if first <= byid[sid]["stop_sequence"] <= last], f"Trip skips a timing point: {tid}")
        check(all(seconds(a["arrival_time"]) < seconds(b["arrival_time"]) for a, b in zip(active, active[1:])), f"Timing anchors do not increase: {tid}")
        ranges[tid] = (first, last)
    # A common anchor supplies a direction-wide chronological order even when endpoints vary.
    common = next(sid for sid in tpids if all(routes[trip["trip_id"]][sid]["arrival_time"] is not None for trip in trips))
    ordered_common = sorted(trips, key=lambda trip: seconds(routes[trip["trip_id"]][common]["arrival_time"]))
    common_rank = {trip["trip_id"]: index + 1 for index, trip in enumerate(ordered_common)}
    trips = sorted(trips, key=lambda trip: (seconds(next(stop["arrival_time"] for stop in trip["stops"] if stop["arrival_time"] is not None)), trip["trip_id"]))
    arrivals = {trip["trip_id"]: {sid: None for sid in stop_ids} for trip in trips}
    departures = {trip["trip_id"]: {sid: None for sid in stop_ids} for trip in trips}
    statuses = {trip["trip_id"]: {sid: "unserved_working" for sid in stop_ids} for trip in trips}
    stop_counts, anchor_proof, matching_proof, ambiguous = {}, {}, {}, []
    raw_reference_count = 0
    all_arrival_departure_equal = True

    for stop in stops:
        sid, seq = stop["stop_id"], stop["stop_sequence"]
        raw = read(folder, f"stop_schedule_{sid}.json")
        check(raw["stop_id"] == sid and raw["route_id"] == ROUTE and str(raw["direction_id"]) == str(DIRECTION) and raw["service_id"] == service, f"Wrong per-stop timetable: {sid}")
        rows = sorted((row for values in raw["schedule"].values() for row in values), key=lambda row: seconds(row["arrival_time"]))
        check(all(row["direction_id"] == DIRECTION and seconds(row["arrival_time"]) is not None and seconds(row["departure_time"]) is not None for row in rows), f"Invalid per-stop schedule occurrence: {sid}")
        check(len({row["arrival_time"] for row in rows}) == len(rows), f"Duplicate reference times need separate ambiguity handling: {sid}")
        active = [trip for trip in trips if ranges[trip["trip_id"]][0] <= seq <= ranges[trip["trip_id"]][1]]
        check(len(rows) == len(active), f"Unanchored served-stop scope at {sid}: {len(rows)} rows but {len(active)} trips between first/last anchors")
        check(Counter(row["headsign"] for row in rows) == Counter(trip["trip_headsign"] for trip in active), f"Headsigns do not support the contiguous served-stop scope: {sid}")
        stop_counts[sid] = {"published_reference_count": len(rows), "headsign_counts": dict(Counter(row["headsign"] for row in rows)), "served_range_count_matches": True}
        raw_reference_count += len(rows)
        all_arrival_departure_equal &= all(row["arrival_time"] == row["departure_time"] for row in rows)
        if sid in tpids:
            expected = sorted((seconds(routes[trip["trip_id"]][sid]["arrival_time"]), seconds(routes[trip["trip_id"]][sid]["departure_time"]), trip["trip_headsign"]) for trip in active)
            actual = [(seconds(row["arrival_time"]), seconds(row["departure_time"]), row["headsign"]) for row in rows]
            check(expected == actual, f"Route and per-stop timing anchors disagree: {sid}")
            anchor_proof[sid] = {"route_trip_count_with_time": len(active), "stop_schedule_count": len(rows), "exact_route_and_stop_schedule_agreement": True}
            for trip in active:
                tid = trip["trip_id"]
                arrivals[tid][sid] = seconds(routes[tid][sid]["arrival_time"])
                departures[tid][sid] = seconds(routes[tid][sid]["departure_time"])
                statuses[tid][sid] = "published_timing_point"
            continue
        left = max((anchor for anchor in tpids if byid[anchor]["stop_sequence"] < seq), key=lambda anchor: byid[anchor]["stop_sequence"])
        right = min((anchor for anchor in tpids if byid[anchor]["stop_sequence"] > seq), key=lambda anchor: byid[anchor]["stop_sequence"])
        check(all(routes[trip["trip_id"]][left]["arrival_time"] and routes[trip["trip_id"]][right]["arrival_time"] for trip in active), f"A served intermediate stop lacks enclosing timing anchors: {sid}")
        candidates = [[index for index, trip in enumerate(active) if seconds(routes[trip["trip_id"]][left]["arrival_time"]) <= seconds(row["arrival_time"]) <= seconds(routes[trip["trip_id"]][right]["arrival_time"])] for row in rows]
        matched = maximum_matching(candidates)
        check(len(matched) == len(rows), f"No complete timing-window assignment: {sid}")
        deleted_sizes = []
        for trip_index, row_index in sorted(matched.items()):
            tid = active[trip_index]["trip_id"]
            deleted_size = len(maximum_matching(candidates, (row_index, trip_index)))
            deleted_sizes.append(deleted_size)
            if deleted_size < len(active):
                arrivals[tid][sid] = seconds(rows[row_index]["arrival_time"])
                departures[tid][sid] = seconds(rows[row_index]["departure_time"])
                statuses[tid][sid] = "derived_unique_matching"
                check(rows[row_index]["headsign"] == active[trip_index]["trip_headsign"], f"Uniquely matched row has a different headsign: {sid} / {tid}")
            else:
                statuses[tid][sid] = "unresolved_association"
                ambiguous.append({"trip_id": tid, "stop_id": sid, "reason": "multiple_complete_timing_window_assignments"})
        matching_proof[sid] = {
            "anchor_interval": [left, right], "eligible_trip_count": len(active),
            "stop_schedule_count": len(rows), "unique_stop_schedule_times": len(rows),
            "complete_matching_size": len(matched), "matched_edges_individually_removed": len(matched),
            "maximum_matching_size_after_any_one_matched_edge_removed": max(deleted_sizes, default=0),
            "unique_perfect_matching_proved": all(size < len(active) for size in deleted_sizes),
            "arrivals_with_multiple_individual_candidate_trips": sum(len(options) > 1 for options in candidates),
            "max_individual_candidate_trips": max(map(len, candidates), default=0),
        }

    patterns = defaultdict(list)
    for trip in trips:
        tid = trip["trip_id"]
        patterns[(ranges[tid], tuple(routes[tid][sid]["stop_sequence"] for sid in tpids), trip["trip_headsign"])].append(trip)
    pattern_facts, pattern_by_trip = [], {}
    for ((first, last), sequences, headsign), members in patterns.items():
        served = stop_ids[first - 1:last]
        pattern_id = f"{served[0].lower()}_to_{served[-1].lower()}_{len(served)}"
        pattern_facts.append({"pattern_id": pattern_id, "trip_count": len(members), "origin_stop_id": served[0], "terminal_stop_id": served[-1], "headsign": headsign, "stop_count": len(served), "served_stop_ids": served, "route_timing_point_stop_sequences": dict(zip(tpids, sequences)), "scope_status": "supported_by_trip_anchor_sequences_and_all_stop_schedule_counts_and_headsigns"})
        for trip in members:
            pattern_by_trip[trip["trip_id"]] = pattern_id
    compiled_trips = []
    for trip in trips:
        tid = trip["trip_id"]
        first, last = ranges[tid]
        served = stop_ids[first - 1:last]
        known = [arrivals[tid][sid] for sid in served if arrivals[tid][sid] is not None]
        check(all(a < b for a, b in zip(known, known[1:])), f"Joined served times do not strictly increase: {tid}")
        compiled_trips.append({
            "trip_id": tid, "headsign": trip["trip_headsign"], "direction_id": DIRECTION, "service_id": service,
            "chronological_rank_at_common_timing_point_1based": common_rank[tid], "pattern_id": pattern_by_trip[tid],
            "originstatus": {"origin_stop_id": served[0], "status": "confirmed_in_current_route_timetable", "evidence": "First non-null route timing point has trip-specific stop_sequence=1; all subsequent anchor offsets match the common direction list.", "first_published_time_seconds": arrivals[tid][served[0]], "physical_first_stop_in_full_direction_sequence": first, "served_stop_count": len(served), "unserved_stop_ids": [sid for sid in stop_ids if sid not in served], "null_reason_before_origin": "Unserved before this working's origin, supported by null route timing anchors and complete per-stop schedule counts." if first > 1 else None},
            "terminalstatus": {"terminal_stop_id": served[-1], "status": "supported_by_route_anchors_and_all_stop_schedule_counts", "physical_last_stop_in_full_direction_sequence": last, "evidence": "The last served route anchor, null later anchors, trip headsign and exact per-stop reference/headsign counts agree on this contiguous working's terminal."},
            "timing_point_times": {sid: arrivals[tid][sid] for sid in tpids},
            "stops": arrivals[tid], "departures": departures[tid], "stop_time_status": statuses[tid],
            "trip_stop_sequences": {sid: byid[sid]["stop_sequence"] - first + 1 if sid in served else None for sid in stop_ids},
        })
    shape_meta = byfile["outbound_shape.json"]
    unique = not ambiguous and all(proof["unique_perfect_matching_proved"] for proof in matching_proof.values())
    try:
        source_bundle = folder.resolve().relative_to(ROOT.parents[1]).as_posix()
    except ValueError:
        source_bundle = str(folder.resolve())
    facts = {
        "schema_version": "invicta.line701.full_line_service_facts.v1", "compiled_at_utc": now(),
        "reference_day": reference_date, "reference_date": reference_date, "timezone": "Europe/Lisbon",
        "route_id": ROUTE, "direction_id": DIRECTION, "destination": "Codiceira / Ermesinde", "active_service_id": service,
        "source_role": "operator_published_scheduled_service_layer_not_observed_native_traffic",
        "time_representation": "Integer scheduled arrival seconds after local service-day midnight, retaining hours >=24. Null means unserved or unresolved; stop_time_status distinguishes them. These are published references, not observations.",
        "stoplist": [dict(stop, designated_timing_point=stop["stop_id"] in tpids) for stop in stops],
        "timing_points": [dict(byid[sid], timepoint=1) for sid in tpids],
        "shape": shape,
        "geometry_provenance": {"raw_file": "outbound_shape.json", "source_url": shape_meta["url"], "retrieved_start_utc": shape_meta["retrieved_start_utc"], "retrieved_end_utc": shape_meta["retrieved_end_utc"], "historical_reference_date_verified": False, "reference_date": reference_date, "has_exposed_shape_id_or_trip_branch_id": False, "caveat": "The shape API accepts direction_id in the inspected official frontend and exposes no verified historical date selection. This is geometry as retrieved, not proven geometry for the timetable service date."},
        "trip_patterns": pattern_facts, "trips": compiled_trips,
        "matching_proof": {
            "method": "At every non-timing stop, find a complete bipartite matching between published arrivals and trips whose adjacent timing anchors enclose each arrival. Remove each matched edge individually and recompute maximum matching. Only forced associations are exposed; ambiguous cells remain null. This does not assume chronological trip order or use headsigns to force a match.",
            "assumptions": ["Each per-stop published occurrence belongs to one route trip in this explicit service and direction.", "The route trip's anchor stop sequences support a contiguous portion of the common direction stop list; every stop's exact count and headsign multiset independently agrees with those served ranges.", "An intermediate scheduled reference lies between its adjacent route timing-point arrivals."],
            "route_trip_count": len(trips), "full_direction_stop_count": len(stops), "timing_point_count": len(tpids), "shape_point_count": len(shape),
            "stop_schedule_raw_response_count": len(stops), "common_ordering_timing_point": common,
            "all_route_anchors_match_per_stop_schedule": anchor_proof,
            "served_scope_stop_schedule_checks": stop_counts, "non_timing_stop_unique_matching": matching_proof,
            "all_non_timing_stop_assignments_unique": unique,
            "all_served_trip_stop_times_strictly_increase": unique,
            "all_fetched_arrival_departure_references_equal": all_arrival_departure_equal,
            "raw_published_reference_count": raw_reference_count,
            "published_reference_cells": sum(value is not None for trip in compiled_trips for value in trip["stops"].values()),
            "unserved_null_cells": sum(status == "unserved_working" for trip in compiled_trips for status in trip["stop_time_status"].values()),
            "unresolved_cell_count": len(ambiguous), "ambiguous_cells": ambiguous,
        },
        "limits": [
            "The timetable is date-resolved; the stop list and shape are snapshots from their recorded retrieval times. Historical shape pinning is unverified.",
            "Per-stop responses omit trip_id. Intermediate trip identity is derived only where the complete timing-window assignment is unique under the documented assumptions.",
            "Only six stops are designated timing points. Other published reference times have an undocumented interpolation method. Equal arrival/departure references are not measured zero dwell.",
            "No outbound native SUMO replay, observed vehicle passages, road calibration, passenger demand, vehicle blocks, layovers or interactions with other routes are established by this bundle.",
            "The API service_days flags are false/null despite the date-resolved service. The explicit services?date response is the date authority.",
        ],
        "sources": {"source_bundle": source_bundle, "metadata_file": "metadata.json", "raw_route_timetable": "schedule.json", "raw_full_stoplist": "outbound_stops.json", "raw_shape": "outbound_shape.json", "raw_date_resolved_services": "services.json", "per_stop_raw_filename_pattern": "stop_schedule_{stop_id}.json", "raw_response_count_in_bundle": len(metadata), "all_raw_response_sha256_verified": True, "raw_response_sha256": {name: entry["sha256"] for name, entry in sorted(byfile.items())}, "raw_response_paths": {name: f"{source_bundle}/{name}" for name in sorted(byfile)}, "urls": {name: entry["url"] for name, entry in sorted(byfile.items())}},
    }
    write(folder, "full-line-service-facts.json", facts)
    return facts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-10-28", help="Local timetable service date, YYYY-MM-DD")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=4)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--compile-only", action="store_true", help="Verify frozen bytes and compile without fetching")
    mode.add_argument("--fetch-only", action="store_true", help="Freeze responses without compiling")
    args = parser.parse_args()
    date.fromisoformat(args.date)
    if not args.compile_only:
        fetch_bundle(args.output, args.date, args.workers)
    if not args.fetch_only:
        facts = compile_facts(args.output, args.date)
        proof = facts["matching_proof"]
        print(json.dumps({key: proof[key] for key in ["route_trip_count", "full_direction_stop_count", "shape_point_count", "all_non_timing_stop_assignments_unique", "published_reference_cells", "unserved_null_cells", "unresolved_cell_count"]}, indent=2))


if __name__ == "__main__":
    main()
