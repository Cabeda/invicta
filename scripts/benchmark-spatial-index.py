"""Compare bounded regional road searches with and without SUMO's spatial index."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import warnings

import sumolib


def fingerprint(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def benchmark(network, reference, direction, count):
    points = json.loads(reference.read_text())['directions'][direction]['shape'][20:20 + count]
    if len(points) != count:
        raise ValueError('Reference does not contain enough sample points')
    net = sumolib.net.readNet(str(network), withInternal=True, maxcache=0)

    def query(point):
        return sorted(edge.getID() for edge, _ in net.getNeighboringEdges(
            *point, 55, includeJunctions=False))

    # This isolated process deliberately exercises the optional-library fallback.
    # Production regional matching requires the index instead.
    sentinel = object()
    previous = sys.modules.get('rtree', sentinel)
    sys.modules['rtree'] = None
    try:
        started = time.perf_counter()
        with warnings.catch_warnings(record=True) as emitted:
            brute = [query(point) for point in points]
        brute_seconds = time.perf_counter() - started
    finally:
        if previous is sentinel:
            del sys.modules['rtree']
        else:
            sys.modules['rtree'] = previous

    started = time.perf_counter()
    query(points[0])
    build_seconds = time.perf_counter() - started
    started = time.perf_counter()
    indexed = [query(point) for point in points]
    indexed_seconds = time.perf_counter() - started
    if indexed != brute:
        raise ValueError('Indexed and brute-force searches disagree')
    return {
        'network_sha256': fingerprint(network), 'reference_sha256': fingerprint(reference),
        'sumolib_version': importlib.metadata.version('sumolib'),
        'rtree_version': importlib.metadata.version('rtree'),
        'direction': direction, 'shape_start_index': 20, 'queries': count,
        'edges': len(net.getEdges(withInternal=True)),
        'brute_force_s': round(brute_seconds, 4),
        'index_build_and_first_query_s': round(build_seconds, 4),
        'indexed_queries_s': round(indexed_seconds, 4), 'same_results': True,
        'fallback_warning': str(emitted[0].message) if emitted else None,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--direction', default='1')
    parser.add_argument('--queries', type=int, default=10, choices=range(1, 51))
    args = parser.parse_args()
    print(json.dumps(benchmark(args.network, args.reference, args.direction, args.queries)))
