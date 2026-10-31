"""One observed native execution path for passive and priority-controlled trials."""
import collections
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import time

from trial_evidence import sha256


def require_native_version(evidence):
    import libsumo
    recorded = re.search(rb'Eclipse SUMO[^\n]*?(\d+\.\d+\.\d+)', evidence.payload('stops.xml')[:500])
    current = re.search(r'\d+\.\d+\.\d+', libsumo.getVersion()[1])
    if recorded is None or current is None or recorded[1].decode() != current[0]:
        raise ValueError('Native version differs or is unrecorded; reproduce with the recorded environment')


def implementation_sources():
    here = Path(__file__).parent
    paths = [here / name for name in ['priority_search.py', 'priority_model.py', 'native_runner.py', 'signal_priority.py', 'signal_mapping.py',
             'model_audit.py', 'run_diagnostics.py', 'trial_evidence.py', 'timetable.py',
             'priority_demand.py', 'prepare.py', 'experiment.py', 'prefix_reproduction.py', 'scenario_audit.py',
             'state_probe.py', 'model_review.py', 'traffic_workload.py', 'paired_workload.py', 'native_input_cache.py',
             'unused_signal_stages.py', 'areosa_detection.py', 'signal_program_model.py', 'controller_options.py',
             'protected_turn.py', 'areosa_compound.py', 'junction_scope.py']]
    paths += [here.parents[2] / 'requirements-simulation.txt',
              here.parents[1] / 'costa-cabral/requirements.txt']
    return paths


def freeze_implementation(folder):
    files = {}
    for path in implementation_sources():
        payload = path.read_bytes()
        name = 'implementation-' + path.name
        (folder / name).write_bytes(payload)
        files[name] = sha256(payload)
    return files


def vehicle_observation(simulation, vehicle):
    stops = simulation.vehicle.getStops(vehicle)[:2]
    signals = simulation.vehicle.getNextTLS(vehicle)[:2]
    leader = simulation.vehicle.getLeader(vehicle, 200)
    stopped = simulation.vehicle.isStopped(vehicle)
    waiting = simulation.vehicle.getWaitingTime(vehicle)
    observation = ('scheduled_stop' if stopped else 'queue_behind_vehicle' if waiting > 0 and leader
                   else 'red_signal_ahead' if waiting > 0 and signals and signals[0][3] in 'rR' and signals[0][2] < 5
                   else 'unclassified')
    route = simulation.vehicle.getRoute(vehicle)
    index = max(0, simulation.vehicle.getRouteIndex(vehicle))
    foes = []
    keys = ['foeId', 'egoDist', 'foeDist', 'egoExitDist', 'foeExitDist', 'egoLane', 'foeLane', 'egoResponse', 'foeResponse']
    for foe in simulation.vehicle.getJunctionFoes(vehicle, 100)[:10]:
        foes.append(dict(zip(keys, foe)) if isinstance(foe, (tuple, list))
                    else {key: getattr(foe, key) for key in keys})
    return {'id': vehicle, 'lane': simulation.vehicle.getLaneID(vehicle),
        'road': simulation.vehicle.getRoadID(vehicle),
        'position_metres': simulation.vehicle.getLanePosition(vehicle),
        'speed_mps': simulation.vehicle.getSpeed(vehicle), 'waiting_seconds': waiting,
        'stop_state': simulation.vehicle.getStopState(vehicle), 'passengers': simulation.vehicle.getPersonNumber(vehicle),
        'time_loss_seconds': simulation.vehicle.getTimeLoss(vehicle), 'leader': leader,
        'next_route': list(route[index:index + 6]), 'next_signals': list(signals), 'junction_foes': foes,
        'next_links': list(simulation.vehicle.getNextLinks(vehicle)[:2]),
        'next_stops': [{'id': stop.stoppingPlaceID, 'lane': stop.lane, 'position': stop.endPos,
                        'duration': stop.duration, 'flags': stop.stopFlags} for stop in stops],
        'signals': [{'id': tls[0], 'phase': simulation.trafficlight.getPhase(tls[0]),
                     'state': simulation.trafficlight.getRedYellowGreenState(tls[0]),
                     'spent_seconds': simulation.trafficlight.getSpentDuration(tls[0]),
                     'next_switch': simulation.trafficlight.getNextSwitch(tls[0])} for tls in signals],
        'proximate_observation': observation, 'cause': 'unclassified'}


def context(simulation, vehicle, limit=16):
    active = set(simulation.vehicle.getIDList())
    pending, rows, visited = collections.deque([vehicle]), [], set()
    while pending and len(rows) < limit:
        ident = pending.popleft()
        if ident in visited or ident not in active:
            continue
        visited.add(ident)
        row = vehicle_observation(simulation, ident)
        rows.append(row)
        if row['leader']:
            pending.append(row['leader'][0])
        pending.extend(foe['foeId'] for foe in row['junction_foes'])
    return rows


def atomic_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


class RunMonitor:
    def __init__(self, folder, buses, sample_seconds=30, stall_seconds=300, focus_trip=None, max_samples=20000,
                 max_wall_seconds=None, stop_on_first_blockage=False):
        if sample_seconds < 1 or stall_seconds < 1 or not 1 <= max_samples <= 20000:
            raise ValueError('Diagnostic sampling must be positive and bounded')
        self.folder, self.buses = folder, {bus['id'] for bus in buses}
        self.active, self.arrived = set(), set()
        self.sample_seconds, self.stall_seconds = sample_seconds, stall_seconds
        self.focus_trip, self.max_samples = focus_trip, max_samples
        self.max_wall_seconds, self.started = max_wall_seconds, time.monotonic()
        self.stop_on_first_blockage, self.stop_requested, self.last_time = stop_on_first_blockage, False, None
        self.stop_reason = None
        self.samples, self.first_deadline, self.first_stall, self.snapshots = 0, None, None, []
        self.deadlines = collections.defaultdict(list)
        for bus in buses:
            if focus_trip and bus['id'] != focus_trip:
                continue
            for index, stop in enumerate(bus['stops']):
                if index in [0, len(bus['stops']) - 1] or stop['designated_timing_point']:
                    self.deadlines[stop['scheduled'] + 1].append(
                        (bus['id'], stop['native_stop_id'], index == len(bus['stops']) - 1))
        self.stream = (folder / 'trace.jsonl').open('w')

    def emit(self, event):
        self.stream.write(json.dumps(event, ensure_ascii=False) + '\n')
        self.stream.flush()

    def capture(self, simulation, kind, trip, stop=None):
        now = simulation.simulation.getTime()
        name = 'first-deadline-state.xml.gz' if kind == 'checkpoint_pending' else 'first-blockage-state.xml.gz'
        simulation.simulation.saveState(str(self.folder / name))
        event = {'kind': kind, 'time': now, 'trip': trip, 'stop': stop, 'snapshot': name,
                 'vehicles': context(simulation, trip), 'cause': 'unclassified'}
        self.snapshots.append({'file': name, 'time': now, 'kind': kind,
                               'sha256': sha256((self.folder / name).read_bytes())})
        self.emit(event)
        return event

    def step(self, simulation, now):
        self.last_time = now
        if self.max_wall_seconds is not None and time.monotonic() - self.started > self.max_wall_seconds:
            self.stop_requested, self.stop_reason = True, 'native_wall_budget'
            return
        self.active.update(set(simulation.simulation.getDepartedIDList()) & self.buses)
        arrived = set(simulation.simulation.getArrivedIDList()) & self.buses
        self.arrived.update(arrived)
        self.active.difference_update(arrived)
        watched = sorted(bus for bus in self.active if not self.focus_trip or bus == self.focus_trip)
        if self.first_deadline is None:
            for trip, stop, terminal in sorted(self.deadlines.get(now, [])):
                if trip in self.arrived:
                    continue
                if trip not in self.active:
                    self.first_deadline = self.capture(simulation, 'checkpoint_pending', trip, stop)
                    break
                pending = simulation.vehicle.getStops(trip)
                if not any(item.stoppingPlaceID == stop for item in pending):
                    continue
                if terminal and pending and pending[0].stoppingPlaceID == stop and simulation.vehicle.isStopped(trip):
                    continue  # Reached its destination; subsequent holding is not a late arrival.
                self.first_deadline = self.capture(simulation, 'checkpoint_pending', trip, stop)
                break
        if self.first_stall is None:
            for bus in watched:
                if simulation.vehicle.getWaitingTime(bus) >= self.stall_seconds and not simulation.vehicle.isStopped(bus):
                    self.first_stall = self.capture(simulation, 'prolonged_wait', bus)
                    self.stop_requested = self.stop_on_first_blockage
                    if self.stop_requested:
                        self.stop_reason = 'first_blockage'
                    break
        if int(now) % self.sample_seconds == 0:
            for bus in watched:
                if self.samples >= self.max_samples:
                    break
                self.emit({'kind': 'sample', 'time': now, 'vehicle': vehicle_observation(simulation, bus)})
                self.samples += 1
        if int(now) % 60 == 0:
            atomic_json(self.folder / 'progress.json', {'simulation_time': now, 'active_buses': len(self.active),
                        'arrived_buses': len(self.arrived), 'sample_count': self.samples})

    def close(self):
        self.stream.close()
        data = {'first_deadline_pending': self.first_deadline, 'first_prolonged_wait': self.first_stall,
                'simulation_time': self.last_time, 'stopped_on_first_blockage': self.stop_reason == 'first_blockage',
                'stop_reason': self.stop_reason,
                'sample_count': self.samples, 'sample_limit': self.max_samples,
                'snapshots': self.snapshots, 'events_file': 'trace.jsonl',
                'limitations': ['A pending-deadline snapshot is checked against native stop output after execution.',
                                'Proximate observations do not establish the physical cause of delay.',
                                'Snapshots are for diagnosis; resumed-run equivalence is not established.']}
        atomic_json(self.folder / 'monitor.json', data)
        return data


def run_native(command, buses, folder, priority_options=None, monitor_options=None):
    # Execute the recorded controller, so edits made while another trial is
    # preparing cannot change that trial after its implementation was frozen.
    import importlib.util
    controller = Path(folder) / 'implementation-signal_priority.py'
    if controller.exists():
        spec = importlib.util.spec_from_file_location('invicta_frozen_signal_priority', controller)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        simulate_with_priority = module.simulate_with_priority
    else:
        from signal_priority import simulate_with_priority
    import libsumo
    monitor = RunMonitor(folder, buses, **(monitor_options or {}))
    started = time.monotonic()
    try:
        priority = simulate_with_priority(command, {bus['id'] for bus in buses}, folder,
                                         enabled=priority_options is not None, observer=monitor,
                                         **(priority_options or {}))
    finally:
        diagnostics = monitor.close()
    return {'priority': priority, 'diagnostics': diagnostics,
            'elapsed_seconds': time.monotonic() - started,
            'runtime': {'libsumo': list(libsumo.getVersion()), 'python': platform.python_version(),
                        'packages': {name: importlib.metadata.version(name) for name in
                                     ['libsumo', 'traci', 'sumolib', 'sumo-data', 'rtree']}}}
