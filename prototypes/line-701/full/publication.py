"""Reject publication unless numeric runs and native replay use the same inputs."""
from pathlib import Path
import hashlib

def digest(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()

def native_inputs(root,case,policy,seed):
    paths=[root/f'data/{policy}.net.xml',root/f'runs/{case}-{policy}-{seed}/routes.rou.xml',root/f'runs/{case}-{policy}-{seed}/additional.add.xml']
    return {str(path.relative_to(root)):digest(path) for path in paths}

def validate_publication(root,raw,manifest):
    expected={(case,policy,seed) for case in raw['meta']['cases'] for policy in ['baseline','restricted'] for seed in raw['meta']['seeds']}
    runs={(r['case'],r['variant'],r['seed']):r for r in raw['runs']}
    if len(runs)!=len(raw['runs']) or set(runs)!=expected:raise ValueError('Incomplete or duplicate native numeric matrix')
    reference_hash=digest(root/'data/routes.json')
    for key,run in runs.items():
        case,policy,seed=key;inputs=run.get('native_inputs',{})
        expected_names={f'data/{policy}.net.xml',f'runs/{case}-{policy}-{seed}/routes.rou.xml',f'runs/{case}-{policy}-{seed}/additional.add.xml'}
        if set(inputs)!=expected_names or any(not isinstance(value,str) or len(value)!=64 for value in inputs.values()) or any((root/name).exists() and digest(root/name)!=value for name,value in inputs.items()) or run['inputs']['reference']!=reference_hash or run['inputs']['network']!=inputs.get(f'data/{policy}.net.xml'):
            raise ValueError('Numeric native run input binding is missing or stale')
    for case in raw['meta']['cases']:
        for seed in raw['meta']['seeds']:
            a=runs[case,'baseline',seed]['inputs'];b=runs[case,'restricted',seed]['inputs']
            if a['demand']!=b['demand']:raise ValueError('Baseline and priority requested demand differ')
    clips=manifest['clips'];pairs={(c['case'],c['policy']) for c in clips}
    if len(pairs)!=len(clips) or pairs!={(c,p) for c in raw['meta']['cases'] for p in ['baseline','restricted']}:
        raise ValueError('Incomplete or duplicate replay matrix')
    if manifest['scope'].get('direction')!='both' or set(manifest['scope'].get('directions',{}))!={'0','1'}:raise ValueError('Full replay must cover both directions')
    assets=root/'inspection-assets'
    if digest(assets/manifest['scene']['file'])!=manifest['scene']['sha256']:raise ValueError('Scene bytes do not match manifest')
    for clip in clips:
        key=(clip['case'],clip['policy'],clip['seed']);run=runs.get(key)
        if run is None or clip['input_hashes']!=run['native_inputs']:raise ValueError('Replay has no matching numeric native run')
        if clip.get('execution',{}).get('kind')!='same_full_day_execution' or clip['execution'].get('trajectory_sha256')!=run.get('replay_trajectory_sha256'):
            raise ValueError('Replay did not come from the same full-day execution')
        if clip['simulation_begin']!=run['inputs']['begin'] or not run['inputs']['begin']<=clip['start']<clip['end']<=run['inputs']['end']:
            raise ValueError('Replay window does not belong to numeric run')
        if manifest['scene']['network_sha256'][clip['policy']]!=run['inputs']['network'] or clip['capture_signature']!=manifest['capture_signature']:
            raise ValueError('Replay scene does not belong to numeric run')
        if digest(assets/clip['file'])!=clip['sha256']:raise ValueError('Replay bytes do not match manifest')
    return True
