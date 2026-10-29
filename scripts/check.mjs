import {readdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
function run(command,args){const result=spawnSync(command,args,{stdio:'inherit'});if(result.error)throw result.error;if(result.status!==0)process.exit(result.status??1)}
for(const folder of ['web','scripts','prototypes/line-701','prototypes/costa-cabral'])for(const name of await readdir(folder))if(/\.(mjs|js)$/.test(name))run(process.execPath,['--check',folder+'/'+name]);
run('npm',['run','typecheck']);
run('npm',['test']);
run(process.env.INVICTA_PYTHON||(existsSync('.venv/bin/python')?'.venv/bin/python':'python3'),['-m','unittest','discover','-s','prototypes','-p','test_native_replay.py']);
run(process.env.INVICTA_PYTHON||(existsSync('.venv/bin/python')?'.venv/bin/python':'python3'),['-m','unittest','discover','-s','prototypes/line-701/full','-p','test_*.py']);
run(process.execPath,['scripts/verify-site.mjs']);
