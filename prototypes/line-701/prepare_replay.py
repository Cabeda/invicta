"""Reuse the prototype's native 3D capture format for the route-first pilot."""
from pathlib import Path
import gzip, hashlib, importlib.util, json, shutil
ROOT=Path(__file__).resolve().parent;LEGACY=ROOT.parent/'costa-cabral'
if __name__=='__main__':
    for name in ['vehicle-dimensions-3d.json']:
        shutil.copy2(LEGACY/'data'/name,ROOT/'data'/name)
    # Rebuild footprints from the extended frozen OSM, including the Bolhão area.
    frozen=ROOT/'data/buildings-3d.json.gz'
    if frozen.exists():frozen.unlink()
    spec=importlib.util.spec_from_file_location('route_replay',LEGACY/'prepare_3d.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=ROOT;module.OUT=ROOT/'inspection-assets';module.OUT.mkdir(exist_ok=True)
    module.START=600;module.END=2400
    data=module.scene()
    original=LEGACY/'data/buildings-3d.json.gz'
    old=json.loads(gzip.decompress(original.read_bytes()))
    features={b['id']:b for b in old['features']}
    features.update({b['id']:b for b in data['buildings']['features']})
    data['buildings'].update(features=list(features.values()),
        source='Frozen OSM footprints from the original district plus new southern map tiles; shared projection and offset, not a survey',
        inherited_snapshot_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
    with gzip.GzipFile(filename=str(frozen),mode='wb',mtime=0) as f:f.write(json.dumps(data['buildings'],ensure_ascii=False,separators=(',',':')).encode())
    module.save('scene.json.gz',data)
    print('Merged buildings:',len(features),flush=True)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        jobs=[executor.submit(module.capture,case,policy,data) for case in ['moderate','busy','late'] for policy in ['baseline','restricted']]
        for job in jobs:job.result()
