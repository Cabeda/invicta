// Build-time restoration only: the deployed website has no GitHub dependency.
import {readFile,writeFile,mkdir,rename,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function stageDeploymentAssets({root=process.cwd(),commit=process.env.INVICTA_ASSET_COMMIT||process.env.VERCEL_GIT_COMMIT_SHA,fetchAsset=fetch}={}){
 const manifest=JSON.parse(await readFile(path.join(root,'deployment-assets.json'),'utf8'));
 if(manifest.schema!=='invicta.deployment-assets.v1'||manifest.repository!=='Cabeda/invicta'||manifest.output_directory!=='prototypes/costa-cabral/proposal')throw Error('Unsupported public asset manifest');
 const output=path.resolve(root,manifest.output_directory),seen=new Set();let restored=0;
 for(const entry of manifest.files){const target=path.resolve(root,entry.repository_path);if(!target.startsWith(output+path.sep)||seen.has(target)||!/^[a-f0-9]{64}$/.test(entry.sha256)||!Number.isSafeInteger(entry.bytes)||entry.bytes<1)throw Error('Invalid public asset entry');seen.add(target)}
 const pending=[...manifest.files];
 async function worker(){while(pending.length){const entry=pending.shift(),target=path.resolve(root,entry.repository_path);let local=false;try{local=(await stat(target)).size===entry.bytes&&sha(await readFile(target))===entry.sha256}catch(error){if(error.code!=='ENOENT')throw error}if(local)continue;
  if(!/^[a-f0-9]{40}$/.test(commit||''))throw Error('A pushed Git commit is required in INVICTA_ASSET_COMMIT');
  const url='https://raw.githubusercontent.com/'+manifest.repository+'/'+commit+'/'+entry.repository_path.split('/').map(encodeURIComponent).join('/');let bytes;
  for(let attempt=0;attempt<3;attempt++){try{const response=await fetchAsset(url,{signal:AbortSignal.timeout(120000)});if(!response.ok)throw Error('Public asset HTTP '+response.status);bytes=Buffer.from(await response.arrayBuffer());break}catch(error){if(attempt===2)throw error;await new Promise(resolve=>setTimeout(resolve,500*(attempt+1)))}}
  if(bytes.length!==entry.bytes||sha(bytes)!==entry.sha256)throw Error('Public asset bytes do not match manifest: '+entry.repository_path);
  await mkdir(path.dirname(target),{recursive:true});await writeFile(target+'.verified-part',bytes);await rename(target+'.verified-part',target);restored++;
 }}
 await Promise.all(Array.from({length:3},()=>worker()));return {restored,verified:manifest.files.length};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){const result=await stageDeploymentAssets();console.log('Public assets verified:',result.verified,'restored:',result.restored);}
