"""Cheap workload checks on compiled native inputs, before vehicle execution."""
import json
import xml.etree.ElementTree as ET

from trial_evidence import sha256


def audit_scenario(folder, reference, requests, passenger_requests, walking_requests, baseline=None, compiled=None):
    routes = ET.parse(folder / 'routes.rou.xml').getroot()
    buses = {trip['id']: trip for direction in reference['directions'].values() for trip in direction['trips']}
    vehicles = routes.findall('vehicle')
    actual = {vehicle.get('id'): vehicle for vehicle in vehicles}
    expected = buses.keys() | {request['id'] for request in requests}
    if len(actual) != len(vehicles) or set(actual) != expected:
        raise ValueError('Compiled workload drops, duplicates or adds a scheduled bus or ordinary request')
    for ident, bus in buses.items():
        vehicle = actual[ident]
        if (vehicle.get('type') != 'bus' or vehicle.find('route').get('edges').split() != bus['path'] or
                [(stop.get('busStop'), float(stop.get('arrival'))) for stop in vehicle.findall('stop')] !=
                [(stop['native_stop_id'], stop['scheduled']) for stop in bus['stops']]):
            raise ValueError('Compiled scheduled bus path or served timetable was changed')
    for request in requests:
        vehicle = actual[request['id']]
        edges = vehicle.find('route').get('edges').split()
        if (vehicle.get('type') != request['group'] or not edges or
                (edges[0], edges[-1]) != (request['from'], request['to']) or
                any(float(vehicle.get(attribute)) != request[field] for attribute, field in
                    [('depart', 'depart'), ('departPos', 'depart_pos'), ('arrivalPos', 'arrival_pos')])):
            raise ValueError('Compiled ordinary request changes a physical endpoint, departure or vehicle type')
    people = routes.findall('person')
    ids = [person.get('id') for person in people]
    if (len(ids) != len(set(ids)) or len(ids) != passenger_requests + walking_requests or
            sum(ident.startswith('passenger_') for ident in ids) != passenger_requests or
            sum(ident.startswith('walking_') for ident in ids) != walking_requests):
        raise ValueError('Compiled passenger or walking workload was dropped or duplicated')
    permission_signature = None
    if baseline is not None and compiled is not None:
        permissions = []
        for edge in baseline.getEdges():
            for lane in edge.getLanes():
                allowed = lane.allows('pedestrian')
                if compiled.getLane(lane.getID()).allows('pedestrian') != allowed:
                    raise ValueError('Compiled proposal changes pedestrian permissions')
                permissions.append((lane.getID(), allowed))
        permission_signature = sha256(json.dumps(sorted(permissions)).encode())
    return {'schema': 'invicta.scenario-audit.v1', 'scheduled_trips': len(buses),
            'ordinary_requests': len(requests), 'passenger_requests': passenger_requests,
            'walking_requests': walking_requests, 'pedestrian_permissions_sha256': permission_signature,
            'physical_requests_sha256': sha256(json.dumps(requests, sort_keys=True).encode()),
            'status': 'ready_for_execution', 'field_validated': False}
