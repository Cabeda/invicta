"""Inspect a verified native state without advancing traffic or changing its source."""
import gzip
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

import sumo

from native_runner import context, require_native_version
from trial_evidence import load_trial


def inspect_snapshot(source, trial_id=None, model=None, snapshot='final-state.xml', trip_id=None, limit=8,
                     *, actor_id=None):
    if not 1 <= limit <= 127:
        raise ValueError('Inspect between one and 127 bus contexts')
    if actor_id is not None and trip_id is not None:
        raise ValueError('Select either one scheduled bus or one native actor')
    evidence = load_trial(source, trial_id, model)
    require_native_version(evidence)
    names = ['network.net.xml', 'routes.rou.xml', 'additional.add.xml', snapshot]
    payloads = {name: evidence.payload(name) for name in names}
    raw = payloads[snapshot]
    state = ET.fromstring(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
    when = float(state.get('time'))
    import libsumo as native
    with tempfile.TemporaryDirectory(prefix='invicta-inspect-') as temporary:
        folder = Path(temporary)
        for name, raw in payloads.items():
            (folder / name).write_bytes(raw)
        command = [str(Path(sumo.SUMO_HOME) / 'bin/sumo'),
            '--net-file', str(folder / 'network.net.xml'), '--route-files', str(folder / 'routes.rou.xml'),
            '--additional-files', str(folder / 'additional.add.xml'), '--load-state', str(folder / snapshot),
            '--begin', str(when), '--end', str(when + 1), '--time-to-teleport', '-1',
            '--no-warnings', 'true', '--no-step-log', 'true', '--duration-log.disable', 'true',
            '--xml-validation', 'never']
        native.start(command)
        try:
            before = native.simulation.getTime()
            scheduled = {trip['id'] for trip in evidence.buses}
            active = scheduled & set(native.vehicle.getIDList())
            if trip_id is not None and trip_id not in active:
                raise ValueError('Requested bus is not active in this snapshot')
            if actor_id is not None and actor_id not in native.vehicle.getIDList():
                raise ValueError('Requested actor is not active in this snapshot')
            ordered = sorted(active, key=lambda bus: (-native.vehicle.getWaitingTime(bus), bus))
            selected = [actor_id] if actor_id is not None else [trip_id] if trip_id is not None else ordered[:limit]
            rows = [{'trip': actor, 'actor_kind': 'scheduled_bus' if actor in scheduled else 'ordinary_vehicle',
                     'vehicles': context(native, actor)} for actor in selected]
            if actor_id is not None:
                for row in rows:
                    for vehicle in row['vehicles']:
                        ident = vehicle['id']
                        vehicle.update(point=list(native.vehicle.getPosition(ident)),
                            angle=native.vehicle.getAngle(ident), vehicle_class=native.vehicle.getVehicleClass(ident),
                            length_metres=native.vehicle.getLength(ident), width_metres=native.vehicle.getWidth(ident),
                            height_metres=native.vehicle.getHeight(ident), best_lanes=list(native.vehicle.getBestLanes(ident)),
                            lane_change_left=list(native.vehicle.getLaneChangeState(ident, 1)),
                            lane_change_right=list(native.vehicle.getLaneChangeState(ident, -1)))
            after = native.simulation.getTime()
            if before != when or after != before:
                raise ValueError('Inspection advanced or failed to restore the recorded native time')
        finally:
            native.close()
    return {'schema': 'invicta.snapshot-inspection.v1', 'source': evidence.verified_identity(),
            'snapshot': snapshot, 'time': when, 'active_bus_count': len(active),
            'active_buses': ordered, 'inspected_bus_count': len(set(selected) & scheduled),
            'inspected_actor_count': len(rows), 'requested_actor': actor_id, 'contexts': rows,
            'simulation_steps': 0, 'cause': 'unclassified', 'field_validated': False,
            'limitations': ['State inspection does not resume traffic or establish controller-state equivalence.',
                           'A leader, signal or junction foe is an observation, not a confirmed cause.',
                           'Active buses at this snapshot are distinct from final uncompleted-trip counts.']}
