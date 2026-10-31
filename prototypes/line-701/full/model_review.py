"""Evidence-bound stop-placement assumptions for synthetic stress studies."""
import gzip
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import sumolib
from prepare import DATA, digest


def stop_reviews(path, model, reference, network):
    if path is None:
        return {}, None
    document = json.loads(Path(path).read_text())
    if (document.get('schema') != 'invicta.stop-review.v1'
            or document.get('scope') != 'synthetic_stress_only'
            or document.get('field_validated') is not False
            or document.get('network_sha256') != model['network_sha256']
            or document.get('reference_sha256') != model['reference_sha256']
            or document.get('osm_sha256') != model.get('osm_sha256')
            or digest(DATA / 'network.osm.xml.gz') != document['osm_sha256']):
        raise ValueError('Stop review does not bind this model and frozen OSM source')
    rows = document.get('stops', [])
    selected = {row['stop']: row for row in rows}
    if len(selected) != len(rows):
        raise ValueError('Duplicate stop-review disposition')
    wanted = {str(row['osm_platform']) for row in rows}
    platforms = {}
    with gzip.open(DATA / 'network.osm.xml.gz') as stream:
        for _, element in ET.iterparse(stream, events=['end']):
            if element.tag == 'node':
                if element.get('id') in wanted:
                    platforms[element.get('id')] = {
                        'lon': float(element.get('lon')), 'lat': float(element.get('lat')),
                        'tags': {tag.get('k'): tag.get('v') for tag in element.findall('tag')}}
                element.clear()
            elif element.tag in ['way', 'relation']:
                element.clear()
    stops = {stop['native_stop_id']: (direction, stop)
             for direction in reference['directions'].values() for stop in direction['stops']}
    for ident, row in selected.items():
        if (ident not in stops or row.get('disposition') != 'accepted_model_approximation'
                or not row.get('reason') or not row.get('limitations')):
            raise ValueError('Stop review requires a specific supported disposition')
        direction, stop = stops[ident]
        if row.get('lane') != stop['lane'] or row.get('pos') != stop['pos']:
            raise ValueError('Reviewed stop geometry changed')
        platform = platforms.get(str(row['osm_platform']))
        if platform is None:
            raise ValueError('Reviewed OSM platform missing')
        tags = platform['tags']
        if (tags.get('public_transport') != 'platform'
                or stop['stop_id'] not in [tags.get('ref'), tags.get('gtfs:stop_id'), tags.get('gtfs:stop_code')]):
            raise ValueError('OSM platform identity does not match the operator stop')
        point = network.convertLonLat2XY(platform['lon'], platform['lat'])
        if math.dist(point, stop['point']) > 5:
            raise ValueError('OSM platform does not corroborate the operator coordinate')
        fragment = network.getEdge(row['nearby_route_fragment'])
        _, distance = sumolib.geomhelper.polygonOffsetAndDistanceToPoint(stop['point'], fragment.getShape())
        if (fragment.getID() not in direction['path'] or not fragment.allows('bus')
                or fragment.getFunction() or fragment.getLength() >= 12.2 or distance > 10
                or abs(direction['path'].index(fragment.getID()) - stop['path_index']) > 6):
            raise ValueError('Short-fragment explanation does not match the reviewed route')
        lane = network.getLane(stop['lane'])
        berth = sumolib.geomhelper.positionAtShapeOffset(lane.getShape(), stop['pos'])
        if math.dist(berth, stop['point']) > 55:
            raise ValueError('Reviewed approximation exceeds its explicit 55 m bound')
    return selected, digest(path)
