"""Line 701 study adapter for shared scene, footprint and capture preparation."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_replay import ReplayStudy, prepare

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT.parent / 'costa-cabral'

def study():
    return ReplayStudy(root=ROOT, id='line-701', start=600, end=2400,
        cases=('moderate', 'busy', 'late'),
        scope={'route':'701','direction':'1','from':'ARS3','to':'0BLRB',
               'description':'Porto inbound streets','reference_date':'2026-10-28'},
        inherited_buildings=(LEGACY / 'data/buildings-3d.json.gz',),
        dimensions_file=LEGACY / 'data/vehicle-dimensions-3d.json')

if __name__ == '__main__':
    prepare(study())
