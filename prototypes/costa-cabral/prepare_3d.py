"""Costa Cabral study adapter for the shared native replay preparation module."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_replay import ReplayStudy, prepare

ROOT = Path(__file__).resolve().parent

def study():
    return ReplayStudy(root=ROOT, id='costa-cabral', start=720, end=1440,
        cases=('moderate', 'busy', 'residents'),
        scope={'route':None,'direction':None,'from':None,'to':None,
               'description':'Costa Cabral street study','reference_date':'2026-10-28'})

if __name__ == '__main__':
    prepare(study())
