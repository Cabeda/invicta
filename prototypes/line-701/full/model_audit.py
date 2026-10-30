"""Model fitness and the prerequisites for an expensive native service-day run."""
import json
import math
from pathlib import Path

import sumolib

from run_diagnostics import diagnose_trial, execution_coverage
from trial_evidence import sha256, load_trial
from timetable import acceptance_criteria


class ModelNotReadyError(ValueError):
    def __init__(self, report):
        self.report = report
        super().__init__('Full run blocked: ' + ', '.join(report['blockers']))


def is_empty_diagnostic(config):
    existing_signals = (config.get('diagnostic_control') == 'existing_signals'
                        and not config.get('diagnostic_all_green'))
    # Historical diagnostic_all_green means signals switched OFF, not all green.
    control = existing_signals or (config.get('diagnostic_all_green') is True
                                  and config.get('diagnostic_control') in [None, 'signals_off'])
    return (config.get('traffic') == 'none' and control
            and config.get('dwell') == 0 and config.get('passengers_per_minute', 0) == 0
            and config.get('crossing_persons_per_minute', 0) == 0
            and config.get('request_stops') is True and config.get('holding_bays') is True
            and not config.get('lanes') and not config.get('signal_priority'))


def audit_model(model, diagnostic_source=None, diagnostic_trial=None, *, bus_length=12,
                lateness_tolerance_seconds=None):
    if not math.isfinite(bus_length) or bus_length <= 0:
        raise ValueError('Audit bus length must be positive and finite')
    folder = Path(model)
    paths = {name: folder / name for name in ['baseline.net.xml', 'routes.json', 'model.json']}
    fingerprints = {name: sha256(path.read_bytes()) for name, path in paths.items()}
    reference = json.loads(paths['routes.json'].read_bytes())
    description = json.loads(paths['model.json'].read_bytes())
    findings = []

    def issue(code, detail, severity='blocker', **context):
        findings.append({'code': code, 'detail': detail, 'severity': severity, **context})

    if description.get('signal_mapping_correction', {}).get('requires_regional_scope_review',
            bool(description.get('signal_mapping_correction'))):
        issue('signal_mapping_scope_review',
              'The local signal correction passes its bus-only tests, but regional conversion/access changes remain unreviewed.')

    network_hash = fingerprints['baseline.net.xml']
    if description.get('network_sha256') != network_hash or reference.get('network_sha256') != network_hash:
        issue('network_binding', 'Network bytes disagree with model/reference identity.')
    if description.get('reference_sha256') != fingerprints['routes.json']:
        issue('reference_binding', 'Route reference bytes disagree with model identity.')
    directions = reference.get('directions', {})
    if set(directions) != {'0', '1'}:
        issue('direction_coverage', 'This full-line study requires both independent directions.')
    trips = [trip for direction in directions.values() for trip in direction['trips']]
    if len(trips) != reference.get('trip_count') or len({t['id'] for t in trips}) != len(trips):
        issue('trip_coverage', 'Declared workings and unique scheduled trips disagree.')
    if sum(len(t['stops']) for t in trips) != reference.get('served_calls'):
        issue('call_coverage', 'Declared served calls disagree with the complete schedule.')
    geometry = {}
    if not findings:
        net = sumolib.net.readNet(str(paths['baseline.net.xml']), withInternal=True, maxcache=0)
        for key, direction in directions.items():
            path = direction['path']
            if not path or any(not net.hasEdge(edge) for edge in path):
                issue('missing_route_edge', 'The bus path references an absent road.', direction=key)
                continue
            edges = [net.getEdge(edge) for edge in path]
            if any(edge.getFunction() for edge in edges) or len(path) != len(set(path)):
                issue('invalid_vehicle_path', 'Vehicle paths must retain ordered, unique normal edges.', direction=key)
            parts = []
            for index, edge in enumerate(edges):
                parts.append(edge)
                if not edge.allows('bus'):
                    issue('bus_permission', 'A route edge forbids buses.', direction=key, edge=edge.getID())
                if index + 1 < len(edges):
                    connections = edge.getAllowedOutgoing('bus').get(edges[index + 1], [])
                    internal, _ = net.getInternalPath(connections, fastest=False)
                    if not connections or internal is None:
                        issue('bus_connection', 'No permitted bus connector joins consecutive roads.',
                              direction=key, edge=edge.getID(), to_edge=edges[index + 1].getID())
                    parts.extend(internal or [])
            snaps = []
            for stop in direction['stops']:
                try:
                    lane = net.getLane(stop['lane'])
                    correct = path[stop['path_index']] == stop['edge'] == lane.getEdge().getID()
                except (KeyError, IndexError):
                    correct = False
                if not correct:
                    issue('stop_lane', 'Stop lane does not match its ordered road.', stop=stop['native_stop_id'])
                    continue
                if not lane.allows('bus') or not (bus_length <= min(15, stop['pos']) and stop['pos'] <= lane.getLength()):
                    issue('stop_footprint', 'The study bus does not fit this stop footprint.', stop=stop['native_stop_id'])
                offset = min(stop['pos'], lane.getLength())
                point = sumolib.geomhelper.positionAtShapeOffset(lane.getShape(), offset)
                distance = math.dist(point, stop['point'])
                snaps.append(distance)
                if distance > 25:
                    issue('stop_match_review', 'Stop is over 25 m from the source coordinate; inspect the street match.',
                          'review', stop=stop['native_stop_id'], distance_metres=round(distance, 3))
            samples = []
            for edge in parts:
                shape = edge.getShape()
                length = sum(math.dist(a, b) for a, b in zip(shape, shape[1:]))
                count = max(1, math.ceil(length / 10))
                for index in range(count + 1):
                    point = sumolib.geomhelper.positionAtShapeOffset(shape, length * index / count)
                    _, distance = sumolib.geomhelper.polygonOffsetAndDistanceToPoint(point, direction['shape'])
                    samples.append(distance)
            bound = max(samples, default=0) + 5
            if bound > 50:
                issue('route_match_review', 'Sampled native path departs from the operator shape; inspect geometry.',
                      'review', direction=key, continuous_screen_bound_metres=round(bound, 3))
            geometry[key] = {'stops': len(direction['stops']), 'trips': len(direction['trips']),
                             'max_stop_distance_metres': round(max(snaps, default=0), 3),
                             'route_screen_bound_metres': round(bound, 3)}
            for trip in direction['trips']:
                stops = trip['stops']
                if (not stops or trip['direction'] != key or
                        any(b['scheduled'] < a['scheduled'] for a, b in zip(stops, stops[1:]))):
                    issue('trip_schedule', 'Working has an invalid direction or schedule order.', trip=trip['id'])
                    continue
                a, b = stops[0], stops[-1]
                if trip['path'] != path[a['path_index']:b['path_index'] + 1]:
                    issue('working_pattern', 'Short/full working does not retain its own route endpoints.', trip=trip['id'])
                canonical = {stop['native_stop_id']: stop for stop in direction['stops']}
                indices = [stop['path_index'] for stop in stops]
                if (indices != sorted(indices) or any(stop['native_stop_id'] not in canonical or
                        any(stop.get(field) != canonical[stop['native_stop_id']].get(field)
                            for field in ['lane', 'edge', 'pos', 'path_index']) for stop in stops)):
                    issue('working_stops', 'Served calls disagree with the ordered canonical stop geometry.', trip=trip['id'])
    diagnosis = None
    if diagnostic_source is None:
        issue('missing_readiness_evidence', 'Run or select a frozen empty diagnostic for this model.')
    else:
        evidence = load_trial(diagnostic_source, diagnostic_trial, folder)
        if (evidence.identity['network_sha256'] != network_hash or
                evidence.identity['reference_sha256'] != fingerprints['routes.json']):
            issue('diagnostic_model_mismatch', 'Diagnostic belongs to another network or route reference.')
        elif not is_empty_diagnostic(evidence.result['config']):
            issue('diagnostic_profile', 'Readiness requires the declared empty diagnostic, not a traffic or sensitivity case.')
        elif evidence.result['config'].get('bus_length', 12) != bus_length:
            issue('diagnostic_vehicle', 'Diagnostic uses a different bus length; its readiness cannot be reused.')
        elif not execution_coverage(evidence)['full_service_day']:
            issue('diagnostic_scope', 'A bounded diagnostic cannot establish full-service readiness.')
        else:
            diagnosis = diagnose_trial(diagnostic_source, diagnostic_trial, folder,
                                       lateness_tolerance_seconds=lateness_tolerance_seconds)
            if evidence.result['config'].get('diagnostic_control') != 'existing_signals':
                issue('diagnostic_signals_disabled',
                      'A signals-off pass is an optimistic bound; retain existing signals in the bus-only prerequisite.')
            if not diagnosis['operational_compliance']:
                issue('unresolved_empty_diagnostic', 'The optimistic diagnostic misses a checkpoint; diagnose before traffic-only packages.')
    blockers = sorted({finding['code'] for finding in findings})
    identity = {**fingerprints, 'audit_version': 2,
                'bus_length_metres': bus_length,
                'acceptance_criteria': diagnosis['acceptance_criteria'] if diagnosis else acceptance_criteria(
                    0 if lateness_tolerance_seconds is None else lateness_tolerance_seconds),
                'implementation_sha256': sha256(Path(__file__).read_bytes()),
                'diagnostic_execution_sha256': diagnosis['source']['execution_sha256'] if diagnosis else None}
    return {'schema': 'invicta.model-audit.v1', 'id': sha256(json.dumps(identity, sort_keys=True).encode()),
            'source': identity, 'status': 'blocked' if blockers else 'ready_for_full_run',
            'blockers': blockers, 'findings': findings, 'geometry': geometry,
            'scheduled_trips': len(trips), 'directions': sorted(directions),
            'diagnosis': diagnosis, 'field_validated': False,
            'assumptions': description.get('limitations', []),
            'next_step': 'Resolve findings or reproduce the first missed checkpoint before another full traffic run.' if blockers
                         else 'Test the stated hypothesis with complete demand and retain every scheduled trip.'}


def require_readiness(model, config):
    criteria = acceptance_criteria(config.get('operational_lateness_seconds', 0))
    if is_empty_diagnostic(config):
        return {'status': 'diagnostic_only', 'acceptance_criteria': criteria, 'field_validated': False}
    if config.get('diagnostic_all_green') or config.get('diagnostic_control'):
        raise ModelNotReadyError({'status': 'blocked', 'blockers': ['invalid_empty_diagnostic_profile']})
    readiness = config.get('readiness')
    if not isinstance(readiness, dict) or not readiness.get('source'):
        raise ModelNotReadyError({'status': 'blocked', 'blockers': ['missing_readiness_evidence']})
    hypothesis = config.get('hypothesis')
    if not isinstance(hypothesis, dict) or any(not isinstance(hypothesis.get(key), str) or not hypothesis[key].strip()
                                              for key in ['change', 'prediction', 'evidence']):
        raise ModelNotReadyError({'status': 'blocked', 'blockers': ['missing_testable_hypothesis']})
    report = audit_model(model, readiness['source'], readiness.get('trial'), bus_length=config.get('bus_length', 12),
                         lateness_tolerance_seconds=criteria['lateness_tolerance_seconds'])
    if report['status'] != 'ready_for_full_run':
        raise ModelNotReadyError(report)
    return report
