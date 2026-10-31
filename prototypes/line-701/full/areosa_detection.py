"""Correct inferred Areosa detection while retaining every signal phase.

This does not claim a municipal detector location or traffic-light plan.
"""
import copy
import xml.etree.ElementTree as ET

CONTROLLER = 'joinedS_1838444495_1838445085_cluster_10121898407_1103464865_112613628_112613629_#12more'


def write_program(network, destination):
    root = ET.parse(network).getroot()
    original = root.find(f"tlLogic[@id='{CONTROLLER}']")
    if original is None or original.get('type') != 'actuated':
        raise ValueError('Expected the inspected inferred Areosa actuated programme')
    lanes = {lane.get('id'): lane for edge in root.findall('edge') for lane in edge.findall('lane')}
    if any(float(lanes[f'1304910030_{i}'].get('length')) != .2 for i in range(3)):
        raise ValueError('Areosa short-road geometry differs; inspect detection again')
    if any(param.get('key') == 'detector-gap' for param in original.findall('param')):
        raise ValueError('Existing detector placement needs a separate review')
    corrected = copy.deepcopy(original)
    corrected.set('programID', 'invicta.areosa-detection.v1')
    ET.SubElement(corrected, 'param', key='detector-gap', value='0')
    additional = ET.Element('additional')
    additional.append(corrected)
    ET.ElementTree(additional).write(destination, encoding='utf-8', xml_declaration=True)
    return {'role': 'inferred_model_correction', 'controller': CONTROLLER,
            'change': 'detector-gap=0', 'phases_unchanged': True, 'field_validated': False}
