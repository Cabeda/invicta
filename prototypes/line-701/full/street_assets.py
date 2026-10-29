"""Freeze CCZero Porto location evidence near either official 701 shape."""
from pathlib import Path
import argparse
import json
import math
from pyproj import Transformer
from prepare import PILOT, digest, write_json


def ingest(cache, output):
    manifest = json.loads((cache / 'source-manifest.json').read_text())
    sources = {s['filename']: s for s in manifest['sources'] if s.get('status') == 200}
    inbound = json.loads((PILOT / 'data/official/inbound_shape.json').read_text())['coordinates']
    outbound = json.loads((PILOT / 'data/official-outbound/full-line-service-facts.json').read_text())['shape']
    transformer = Transformer.from_crs(4326, 3763, always_xy=True)
    shapes = {d: [transformer.transform(p['lng'], p['lat'])
                  for p in sorted(points, key=lambda p:p['sequence'])]
              for d, points in [('1', inbound), ('0', outbound)]}

    def distance(point, line):
        best = math.inf
        for a, b in zip(line, line[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            denominator = dx*dx + dy*dy
            t = max(0, min(1, ((point[0]-a[0])*dx + (point[1]-a[1])*dy) / denominator)) if denominator else 0
            best = min(best, math.dist(point, (a[0] + t*dx, a[1] + t*dy)))
        return round(best, 2)

    features, source_list = [], []
    for name, kind in [('porto-semaforos.geojson', 'signal_equipment'),
                       ('porto-led-crossings.geojson', 'led_crossing')]:
        source = sources[name]
        if digest(cache / name) != source['sha256']:
            raise ValueError('Street inventory source hash mismatch')
        source_list.append({**source, 'licence': 'CCZero', 'publisher': 'Câmara Municipal do Porto'})
        for feature in json.loads((cache / name).read_text())['features']:
            point = transformer.transform(*feature['geometry']['coordinates'])
            distances = {d: distance(point, shape) for d, shape in shapes.items()}
            if min(distances.values()) > 40:
                continue
            properties = {**feature['properties'], 'kind': kind,
                'source_file': name, 'distance_to_direction_metres': distances,
                'directions': [d for d, value in distances.items() if value <= 40],
                'signal_timing': 'unknown', 'controller_mapping': 'unverified'}
            features.append({'type': 'Feature', 'id': kind + ':' + str(properties['objectid']),
                             'geometry': feature['geometry'], 'properties': properties})
    value = {'type': 'FeatureCollection', 'features': features, 'sources': source_list,
        'licence': 'CCZero', 'screen_distance_metres': 40,
        'note': 'Location evidence only. Signal equipment points are not controllers; LED crossings are a subset, not a complete crossing inventory. Signal phases and timings remain unknown.'}
    write_json(output, value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = ingest(args.cache, args.output)
    print('Frozen Porto street asset locations:', len(result['features']))
