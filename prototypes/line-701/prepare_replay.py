"""Reuse the prototype's native 3D capture format for the route-first pilot."""
from pathlib import Path
import importlib.util, shutil
ROOT=Path(__file__).resolve().parent;LEGACY=ROOT.parent/'costa-cabral'
if __name__=='__main__':
    for name in ['buildings-3d.json.gz','vehicle-dimensions-3d.json']:
        shutil.copy2(LEGACY/'data'/name,ROOT/'data'/name)
    spec=importlib.util.spec_from_file_location('route_replay',LEGACY/'prepare_3d.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=ROOT;module.OUT=ROOT/'inspection-assets';module.OUT.mkdir(exist_ok=True)
    module.START=600;module.END=2400
    data=module.scene()
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        jobs=[executor.submit(module.capture,case,policy,data) for case in ['moderate','busy','late'] for policy in ['baseline','restricted']]
        for job in jobs:job.result()
