// Keep the CLI upload small; the build restores these exact public Git assets.
import {readdir,stat,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const START='# BEGIN verified public deployment assets',END='# END verified public deployment assets';
export async function prepareDeployment(root=process.cwd()){
 const prefix='prototypes/costa-cabral/proposal',files=[];
 async function visit(folder){for(const entry of await readdir(folder,{withFileTypes:true})){const file=path.join(folder,entry.name);if(entry.isDirectory())await visit(file);else if(entry.isFile()&&(await stat(file)).size>1_000_000){const bytes=await readFile(file);files.push({repository_path:path.relative(root,file).split(path.sep).join('/'),bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')})}}}
 await visit(path.join(root,prefix));files.sort((a,b)=>a.repository_path.localeCompare(b.repository_path));
 const manifest={schema:'invicta.deployment-assets.v1',repository:'Cabeda/invicta',output_directory:prefix,files};
 await writeFile(path.join(root,'deployment-assets.json'),JSON.stringify(manifest,null,2)+'\n');
 const ignoreFile=path.join(root,'.vercelignore'),old=await readFile(ignoreFile,'utf8'),start=old.indexOf(START),end=old.indexOf(END);
 const before=(start>=0?old.slice(0,start):old).trimEnd(),after=start>=0&&end>=start?old.slice(end+END.length).trim():'';
 await writeFile(ignoreFile,before+'\n'+START+'\n'+files.map(f=>f.repository_path).join('\n')+'\n'+END+'\n'+(after?after+'\n':''));
 return manifest;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){const manifest=await prepareDeployment();console.log('Prepared',manifest.files.length,'verified public assets for the deployment build.');}
