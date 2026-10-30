import {readFile,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {validateRegistry} from '../web/line-registry.mjs';
import {evaluateStudy} from '../web/study-reliability.mjs';
const site='prototypes/costa-cabral/proposal';
for(const name of ['index.html','viewer.mjs','replay.json.gz','manifest.json','capture-index.json','signal-audit.json','signal-audit-index.json']){
 if(!(await readFile('prototypes/line-701/focused-replay/'+name)).equals(await readFile(site+'/701-inspection/'+name)))throw Error('Focused replay source differs: '+name);
}
const focused=JSON.parse(await readFile(site+'/701-inspection/capture-index.json','utf8'));
for(const [file,key]of [['replay.json.gz','replay_sha256'],['manifest.json','manifest_sha256']])if(createHash('sha256').update(await readFile(site+'/701-inspection/'+file)).digest('hex')!==focused[key])throw Error('Focused replay hash mismatch: '+file);
const signalAudit=JSON.parse(await readFile(site+'/701-inspection/signal-audit-index.json','utf8'));
if(createHash('sha256').update(await readFile(site+'/701-inspection/signal-audit.json')).digest('hex')!==signalAudit.sha256)throw Error('Signal source audit hash mismatch');
const signalReport=JSON.parse(await readFile(site+'/701-inspection/signal-audit.json','utf8'));
const focusedCapture=JSON.parse(await readFile(site+'/701-inspection/manifest.json','utf8'));
if(signalReport.network_sha256!==signalAudit.network_sha256||signalReport.network_sha256!==focusedCapture.source.network_sha256)throw Error('Signal audit differs from captured native network');
const pairs=[['prototypes/line-701/pilot.template.html','index.html'],['prototypes/line-701/pilot.js','line-701.js'],...['proposal.mjs','proposal-views.mjs','line-explorer.mjs','line-explorer.css','inspection-2d.mjs'].map(n=>['prototypes/line-701/'+n,n]),...['inspection-3d.js','native-replay.mjs'].map(n=>['prototypes/costa-cabral/'+n,n]),...['line-registry.mjs','proposal-page.mjs','punctuality.mjs','study-labels.mjs','lines.json'].map(n=>['web/'+n,n])];
for(const [source,name]of pairs)if(!(await readFile(source)).equals(await readFile(site+'/'+name)))throw Error('Generated public source differs: '+name);
for(const [source,target]of [['prototypes/line-701/priority-panel.mjs','priority-panel.mjs'],['prototypes/line-701/data/porto-street-assets.geojson','701-street-assets.geojson'],['prototypes/line-701/full/priority-search.json','701-priority/priority-search.json'],['prototypes/line-701/full/PRIORITY_SEARCH.md','701-priority/PRIORITY_SEARCH.md']])if(!(await readFile(source)).equals(await readFile(site+'/'+target)))throw Error('Generated priority evidence differs: '+target);
const search=JSON.parse(await readFile(site+'/701-priority/priority-search.json','utf8'));
for(const item of [...Object.values(search.models).flatMap(m=>Object.values(m.evidence)),...search.trials.flatMap(t=>Object.values(t.evidence))])if(createHash('sha256').update(await readFile(site+'/701-priority/'+item.file)).digest('hex')!==item.gzip_sha256)throw Error('Priority native evidence hash mismatch: '+item.file);
const html=await readFile(site+'/index.html','utf8');if(Buffer.byteLength(html)>100_000||html.includes('id="line-data"'))throw Error('Page shell must load line data separately');
const registry=validateRegistry(JSON.parse(await readFile(site+'/lines.json','utf8')));
for(const line of registry.lines){
 const data=JSON.parse(await readFile(site+'/'+line.data,'utf8')),ref=JSON.parse(await readFile(site+'/'+line.reference,'utf8'));
 if(String(data.meta.route)!==line.id||String(ref.route)!==line.id)throw Error('Line data identity mismatch');
 await readFile(site+'/'+line.report);
 const base=site+'/'+data.replay_assets.replace(/^\.\//,''),manifest=JSON.parse(await readFile(base+'manifest.json','utf8'));
 for(const item of [{file:'scene.json.gz',sha256:manifest.scene.sha256},...manifest.clips]){const bytes=await readFile(base+item.file);if(createHash('sha256').update(bytes).digest('hex')!==item.sha256)throw Error('Native asset hash mismatch: '+item.file)}
 if(data.reliability_decision?.winner&&!data.reliability_decision.assessed.find(p=>p.id===data.reliability_decision.winner)?.eligible)throw Error('Unqualified proposal published as winner');
 if(line.assets?.experiments&&line.assets?.reliability){
  const bytes=await readFile(site+'/'+line.assets.experiments),raw=JSON.parse(bytes),stored=JSON.parse(await readFile(site+'/'+line.assets.reliability,'utf8')),computed=evaluateStudy(raw);
  if(createHash('sha256').update(bytes).digest('hex')!==stored.sourceSha256||JSON.stringify(computed.directions)!==JSON.stringify(stored.directions)||JSON.stringify(computed.decision)!==JSON.stringify(stored.decision)||JSON.stringify(computed.decision)!==JSON.stringify(data.reliability_decision))throw Error('Published punctuality or decision is stale against native evidence');
  for(const [direction,cases]of Object.entries(computed.directions))for(const [scenario,policies]of Object.entries(cases))for(const [policy,metrics]of Object.entries(policies))if(JSON.stringify(metrics)!==JSON.stringify(data.native_directions[direction].cases[scenario][policy].punctuality))throw Error('Page punctuality is stale against its native evidence');
 }
}
const deployment=JSON.parse(await readFile('deployment-assets.json','utf8'));
for(const file of deployment.files){const bytes=await readFile(file.repository_path);if(bytes.length!==file.bytes||createHash('sha256').update(bytes).digest('hex')!==file.sha256)throw Error('Prepare deployment manifest again: '+file.repository_path)}
console.log('Public source parity, line registry, replay hashes and deployment assets verified.');
