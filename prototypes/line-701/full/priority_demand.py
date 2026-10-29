"""Migrate physical OD endpoints across imports without losing traffic requests."""
import hashlib
import json
import math

import sumolib
from prepare import DATA, digest
from experiment import route


def migrate_requests(baseline, requests):
    if not requests:
        return requests, {'requests': 0, 'mappings': []}
    old = sumolib.net.readNet(str(DATA / 'baseline.net.xml'), maxcache=0)
    mappings = {}

    def match(ident, kind, end):
        key = ident, kind, end
        if key in mappings:
            return mappings[key]
        edge = old.getEdge(ident)
        offset = max(0, edge.getLength() - 5) if end else min(5, edge.getLength())
        point = sumolib.geomhelper.positionAtShapeOffset(edge.getShape(), offset)
        ahead = sumolib.geomhelper.positionAtShapeOffset(edge.getShape(), min(edge.getLength(), offset + 3))
        behind = sumolib.geomhelper.positionAtShapeOffset(edge.getShape(), max(0, offset - 3))
        heading = ahead[0] - behind[0], ahead[1] - behind[1]
        candidates = []
        for candidate, _ in baseline.getNeighboringEdges(*point, 55, includeJunctions=False):
            if candidate.getFunction() or not candidate.allows(kind):
                continue
            shape = candidate.getShape()
            dx, dy = shape[-1][0] - shape[0][0], shape[-1][1] - shape[0][1]
            denominator = math.hypot(dx, dy) * math.hypot(*heading)
            cosine = (dx*heading[0] + dy*heading[1])/denominator if denominator else 1
            if cosine < .25:
                continue
            position, distance = sumolib.geomhelper.polygonOffsetAndDistanceToPoint(point, shape)
            same_way = candidate.getID().split('#')[0] == ident.split('#')[0]
            score = distance + 25*(1-cosine) + (0 if same_way else 75)
            candidates.append((score, candidate.getID(), position, distance))
        if not candidates:
            raise ValueError('No physical OD match: ' + str(key))
        _, new_id, position, distance = min(candidates)
        result = {'old_edge': ident, 'kind': kind, 'destination': end, 'edge': new_id,
            'position': round(max(.1, min(baseline.getEdge(new_id).getLength() - .1, position)), 3),
            'source_point': list(point), 'distance_metres': round(distance, 3)}
        mappings[key] = result
        return result

    migrated = []
    for request in requests:
        a, b = match(request['from'], request['kind'], False), match(request['to'], request['kind'], True)
        migrated.append({**request, 'source_from': request['from'], 'source_to': request['to'],
            'from': a['edge'], 'to': b['edge'], 'depart_pos': a['position'], 'arrival_pos': b['position']})
    # No missing endpoint is silently discarded. A disconnected mapped pair is
    # an input defect to resolve before starting the native experiment.
    for a, b, kind in dict.fromkeys((r['from'], r['to'], r['kind']) for r in migrated):
        if not route(baseline, a, b, kind)[0]:
            raise ValueError(f'Mapped OD is disconnected: {a} -> {b} ({kind})')
    return migrated, {'requests': len(requests), 'source_network_sha256': digest(DATA / 'baseline.net.xml'),
        'source_requests_sha256': hashlib.sha256(json.dumps(requests, sort_keys=True).encode()).hexdigest(),
        'mapped_requests_sha256': hashlib.sha256(json.dumps(migrated, sort_keys=True).encode()).hexdigest(),
        'mappings': list(mappings.values()),
        'meaning': 'Same generated physical OD endpoints across policies; original edge start+5m/end-5m projected onto the new topology. Not observed trip locations.'}
