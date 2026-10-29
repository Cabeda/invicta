import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {evaluateStudy} from '../web/study-reliability.mjs';
const [input,output]=process.argv.slice(2);
if(!input||!output)throw Error('Usage: node scripts/build-reliability.mjs INPUT OUTPUT');
const bytes=await readFile(input),raw=JSON.parse(bytes),evaluated=evaluateStudy(raw);
const value={schema:'invicta.reliability.v1',line:String(raw.meta.route),serviceDate:raw.meta.service_date,sourceSha256:createHash('sha256').update(bytes).digest('hex'),goal:{lateToleranceSeconds:0,earlyDeparturesAllowed:false,allScheduledTripsRequired:true},...evaluated,validation:{trafficCalibrated:false,signalsVerified:false,fleetBlocksAvailable:false},changeMeasure:'Approximate directed lane length in mapped SUMO geometry; not a financial estimate.'};
await writeFile(output,JSON.stringify(value,null,2)+'\n');
console.log('Published endpoint punctuality and minimum-change decision:',value.decision.status);
