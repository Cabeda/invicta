"""Bounded green extension; retain generated phase order and all clearance phases.

This controller is an experiment, not a deployable roadside safety controller.
It never sets a signal colour or skips a phase. Each green can gain at most 10s.
"""
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import libsumo as simulation


def simulate_with_priority(command, bus_ids, folder, extension_limit=10, early_green=False,
                           shorten_served_pedestrian_green=False, enabled=True, observer=None):
    events = []
    phase_state = {}
    active = set()
    simulation.start(command)
    try:
        pedestrian_links, pedestrian_lanes = {}, {}
        network = ET.parse(command[command.index('--net-file') + 1]).getroot()
        crossing_lanes = {l.get('id') for e in network.findall('edge')
                          if e.get('function') == 'crossing' for l in e.findall('lane')}
        for tls in simulation.trafficlight.getIDList() if enabled else []:
            links = simulation.trafficlight.getControlledLinks(tls)
            pedestrian_links[tls] = {i for i, alternatives in enumerate(links)
                if any(simulation.lane.getAllowed(link[0]) == ('pedestrian',)
                       for link in alternatives)}
            pedestrian_lanes[tls] = {lane for alternatives in links for link in alternatives
                                     for lane in link if lane in crossing_lanes}
        end = float(command[command.index('--end') + 1])
        while simulation.simulation.getTime() < end:
            simulation.simulationStep()
            now = simulation.simulation.getTime()
            active.update(set(simulation.simulation.getDepartedIDList()) & bus_ids)
            active.difference_update(simulation.simulation.getArrivedIDList())
            if observer is not None:
                observer.step(simulation, now)
            if not enabled:
                continue
            if int(now) % 2:
                continue
            requests, red_requests = {}, set()
            for bus in sorted(active):
                if simulation.vehicle.isStopped(bus):
                    continue
                next_tls = simulation.vehicle.getNextTLS(bus)
                if not next_tls:
                    continue
                tls, link, distance, colour = next_tls[0]
                speed = simulation.vehicle.getSpeed(bus)
                if distance > 120:
                    continue
                if colour in 'rR' and early_green:
                    red_requests.add(tls)
                    continue
                if colour not in 'Gg' or speed < 2:
                    continue
                # Only extend when the bus can plausibly clear in the extension.
                needed = now + math.ceil(distance / speed) + 2
                if needed > now + extension_limit:
                    continue
                requests[tls] = max(requests.get(tls, 0), needed)
            for tls, needed in requests.items():
                phase = simulation.trafficlight.getPhase(tls)
                spent = simulation.trafficlight.getSpentDuration(tls)
                phase_started = round(now - spent, 4)
                key = (tls, phase, phase_started)
                next_switch = simulation.trafficlight.getNextSwitch(tls)
                if key not in phase_state:
                    logic = next(p for p in simulation.trafficlight.getAllProgramLogics(tls)
                                 if p.programID == simulation.trafficlight.getProgram(tls))
                    green = logic.phases[phase]
                    # Max duration is an upper bound even for actuated programs.
                    maximum = green.maxDur if green.maxDur > 0 else green.duration
                    phase_state[key] = min(next_switch + extension_limit,
                                           phase_started + maximum + extension_limit)
                bounded_end = min(needed, phase_state[key])
                if bounded_end > next_switch:
                    simulation.trafficlight.setPhaseDuration(tls, bounded_end - now)
                    events.append({'time': now, 'tls': tls, 'phase': phase,
                        'kind': 'extend_green',
                        'phase_started': phase_started, 'before_switch': next_switch,
                        'after_switch': bounded_end, 'bound': phase_state[key]})
            for tls in sorted(red_requests - requests.keys()):
                state = simulation.trafficlight.getRedYellowGreenState(tls)
                if 'y' in state.lower() or not any(c in 'Gg' for c in state):
                    continue
                # Retain every yellow/all-red phase and the original phase
                # order. Pedestrian-green shortening is a separate sensitivity.
                has_pedestrian_green = any(state[i] in 'Gg' for i in pedestrian_links[tls])
                if has_pedestrian_green and not shorten_served_pedestrian_green:
                    continue
                phase = simulation.trafficlight.getPhase(tls)
                logic = next(p for p in simulation.trafficlight.getAllProgramLogics(tls)
                             if p.programID == simulation.trafficlight.getProgram(tls))
                minimum = max(15, logic.phases[phase].minDur)
                if has_pedestrian_green:
                    # An explicit sensitivity test: 0.8 m/s crossing speed plus
                    # five seconds startup, and no occupied controlled crossing.
                    # Surveyed clearance/conflict plans are still required.
                    if any(simulation.edge.getLastStepPersonIDs(simulation.lane.getEdgeID(lane))
                           for lane in pedestrian_lanes[tls]):
                        continue
                    minimum = max([minimum] + [simulation.lane.getLength(lane)/.8 + 5
                                               for lane in pedestrian_lanes[tls]])
                spent = simulation.trafficlight.getSpentDuration(tls)
                switch = simulation.trafficlight.getNextSwitch(tls)
                if spent >= minimum and switch > now + 1:
                    simulation.trafficlight.setPhaseDuration(tls, 1)
                    events.append({'kind': 'end_conflicting_green', 'time': now,
                        'tls': tls, 'phase': phase, 'spent': spent,
                        'minimum': minimum, 'before_switch': switch, 'after_switch': now + 1})
        simulation.close()
    except BaseException:
        simulation.close()
        raise
    (Path(folder) / 'priority-events.json').write_text(json.dumps(events, indent=2) + '\n')
    return {'extensions': sum(e['kind'] == 'extend_green' for e in events),
        'early_green_requests': sum(e['kind'] == 'end_conflicting_green' for e in events),
        'changed_signals': sorted({e['tls'] for e in events}),
        'extension_limit_seconds': extension_limit, 'phase_order_preserved': True,
        'clearance_phases_preserved': True}
