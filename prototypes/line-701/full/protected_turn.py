"""An explicit, unvalidated Areosa signal-design experiment.

The compound-junction importer puts a permissive turn's waiting car in the
opposing bus path. The local regression reproduces the collision. This writer
separates that turn; it does not claim to reconstruct the municipal programme.
"""
import copy
import xml.etree.ElementTree as ET


def write_program(network, destination):
    root = ET.parse(network).getroot()
    controller = 'areosa_compound'
    connection = next((c for c in root.findall('connection')
        if c.get('from') == '743539878#7' and c.get('to') == '743461566#2'
        and c.get('fromLane') == '1' and c.get('toLane') == '1'), None)
    if connection is None or connection.get('tl') != controller or connection.get('linkIndex') != '3':
        raise ValueError('Protected-turn experiment requires the reviewed Areosa movement')
    original = root.find(f"tlLogic[@id='{controller}']")
    expected = ['rrrrrGGGGrrrrrrrrGGGGrrr', 'rrrrryyyyrrrrrrrryyyyrrr',
        'rrrrrrrrrGGrrrrrrrrrrGGG', 'rrrrrrrrryyrrrrrrrrrryyy', 'r' * 24,
        'GGGggrrrrrrggGGGgrrrrrrr', 'yyyyyrrrrrryyyyyyrrrrrrr', 'r' * 24]
    if original is None or [p.get('state') for p in original.findall('phase')] != expected:
        raise ValueError('Areosa generated phases differ; review before applying a signal experiment')
    if any(p.get(key) for p in original.findall('phase') for key in ['next', 'earlyTarget', 'finalTarget']):
        raise ValueError('Only the reviewed sequential programme is supported')
    corrected = copy.deepcopy(original)
    corrected.set('programID', 'invicta.areosa.protected-turn.v1')
    for phase in corrected.findall('phase'):
        state = list(phase.get('state'))
        state[3] = 'r'
        phase.set('state', ''.join(state))
    for duration, state in [(13, 'rrrG' + 'r' * 20), (3, 'rrry' + 'r' * 20), (8, 'r' * 24)]:
        attributes = {'duration': str(duration), 'state': state}
        if 'G' in state:
            attributes.update(minDur='13', maxDur='30')
        ET.SubElement(corrected, 'phase', attributes)
    additional = ET.Element('additional')
    additional.append(corrected)
    ET.ElementTree(additional).write(destination, encoding='utf-8', xml_declaration=True)
    return {'role': 'inferred_signal_design_experiment', 'controller': controller,
        'protected_link': 3, 'source_phases': 8, 'candidate_phases': 11,
        'other_movement_states_unchanged': True, 'original_clearances_retained': True,
        'new_turn_minimum_green_seconds': 13, 'new_turn_maximum_green_seconds': 30,
        'new_turn_yellow_seconds': 3, 'new_turn_all_red_seconds': 8,
        'field_validated': False}
