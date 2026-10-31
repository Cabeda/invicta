"""Export a small 2D/3D view of one verified local native reproduction."""
import json
import gzip
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from trial_evidence import sha256


class NoRecordedPositions(ValueError):
    """A retained budget-limited case has no actor positions to show."""


def export_case_view(folder, *, title='Inspect the native problem case'):
    folder = Path(folder)
    raw = (folder / 'case.json').read_bytes()
    case = json.loads(raw)
    if (case.get('schema') != 'invicta.native-case.v1' or case.get('qualified') is not False
            or case.get('role') != 'local_reproduction_not_service_qualification'):
        raise ValueError('Only an explicitly non-qualifying native case can use this viewer')
    for name, signature in {**case['input_hashes'], **case['output_hashes']}.items():
        if Path(name).name != name or sha256((folder / name).read_bytes()) != signature:
            raise ValueError('Case view source differs from its native execution')
    recording = json.loads(gzip.decompress((folder / 'frames.json.gz').read_bytes()))
    observations = [v for frame in recording['frames'] for v in frame['vehicles']]
    points = [v[1:3] for v in observations]
    if not points:
        raise NoRecordedPositions('Native case has no recorded actor positions')
    bounds = [min(p[0] for p in points) - 120, min(p[1] for p in points) - 120,
              max(p[0] for p in points) + 120, max(p[1] for p in points) + 120]
    root = ET.fromstring((folder / 'network.net.xml').read_bytes())
    lanes = []
    for edge in root.findall('edge'):
        for lane in edge.findall('lane'):
            shape = [[float(x) for x in p.split(',')[:2]] for p in lane.get('shape').split()]
            if not shape:
                continue
            if (max(p[0] for p in shape) < bounds[0] or min(p[0] for p in shape) > bounds[2]
                    or max(p[1] for p in shape) < bounds[1] or min(p[1] for p in shape) > bounds[3]):
                continue
            lanes.append({'id': lane.get('id'), 'shape': shape, 'width': float(lane.get('width', 3.2)),
                          'pedestrian': lane.get('allow') == 'pedestrian'})
    centre = [(min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in range(2)]
    scene = {'centre': centre, 'lanes': lanes, 'view_bounds':bounds,
        'geometry_scope':'lanes intersecting the actor recording bounds plus 120 metres',
        'source_network_sha256': case['input_hashes']['network.net.xml']}
    (folder / 'scene.json').write_text(json.dumps(scene, separators=(',', ':')) + '\n')
    repo = Path(__file__).resolve().parents[3]
    template = repo / 'prototypes/line-701/case-view'
    for name in ['index.html', 'viewer.mjs']:
        shutil.copy2(template / name, folder / name)
    vendor = repo / 'prototypes/costa-cabral/proposal/vendor'
    (folder / 'vendor').mkdir(exist_ok=True)
    for name in ['three.module.js', 'three.core.js', 'OrbitControls.js', 'THREE-LICENSE.txt']:
        shutil.copy2(vendor / name, folder / 'vendor' / name)
    manifest = {'schema': 'invicta.case-view.v1', 'title': title, 'qualified': False,
        'source_case_sha256': sha256(raw), 'requested_actors': case['requested_actors'],
        'scene_sha256': sha256((folder / 'scene.json').read_bytes()),
        'frames_sha256': case['output_hashes']['frames.json.gz'],
        'view_implementation_sha256': sha256((folder / 'viewer.mjs').read_bytes())}
    if observations:
        focus = max(observations, key=lambda v: v[5])
        manifest.update(focus_actor=focus[0], focus_point=focus[1:3])
    collisions = [dict(row.attrib) for row in ET.parse(folder / 'collisions.xml').getroot()]
    manifest['collision_events'] = collisions
    if collisions:
        event = collisions[0]
        moment = float(event['time'])
        index = min(range(len(recording['frames'])), key=lambda i:abs(recording['frames'][i]['time'] - moment))
        manifest.update(focus_actor=event['collider'], focus_frame=max(0, index - 2),
                        focus_point=[float(x) for x in event['colliderFront'].split(',')])
    (folder / 'view-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest
