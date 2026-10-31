"""Remove generated stages whose green/yellow columns control no movements.

Keep every served green combination and every original all-red clearance.
This is an explicit inferred-model correction, not a municipal timing plan.
"""
import copy
import xml.etree.ElementTree as ET

CONTROLLER = 'joinedS_12514310100_12514324965_12514324966_3897692280_#1more'


def write_program(network, destination):
    root = ET.parse(network).getroot()
    active = {int(row.get('linkIndex')) for row in root.findall('connection')
              if row.get('tl') == CONTROLLER}
    original = next(row for row in root.findall('tlLogic') if row.get('id') == CONTROLLER)
    phases = original.findall('phase')
    if any(row.get('next') or row.get('earlyTarget') or row.get('finalTarget') for row in phases):
        raise ValueError('Stage cleanup requires the inspected sequential generated programme')
    removed = set()
    for index, phase in enumerate(phases):
        state = phase.get('state')
        if not any(colour in 'Gg' for colour in state) or any(state[i] in 'Gg' for i in active):
            continue
        following = phases[(index + 1) % len(phases)]
        if any(following.get('state')[i] != 'r' for i in active):
            raise ValueError('An unused green is followed by a served transition; review explicitly')
        if not any(c in 'yY' for c in following.get('state')):
            raise ValueError('Expected an unused yellow after the unused green')
        removed.update([index, index + 1])
    if removed != {6, 7, 12, 13} or len(active) != 11:
        raise ValueError('Programme differs from the inspected two unused Combatentes stages')
    additional = ET.Element('additional')
    corrected = copy.deepcopy(original)
    corrected.set('programID', 'invicta.mapping-cleanup.v1')
    for index, phase in enumerate(list(corrected.findall('phase'))):
        if index in removed:
            corrected.remove(phase)
    additional.append(corrected)
    ET.ElementTree(additional).write(destination, encoding='utf-8', xml_declaration=True)
    return {'role': 'inferred_model_correction', 'controller': CONTROLLER,
        'removed_phase_indices': sorted(removed), 'old_phases': len(phases),
        'new_phases': len(corrected.findall('phase')),
        'all_red_phases_retained': True, 'served_green_states_unchanged': True,
        'field_validated': False}
