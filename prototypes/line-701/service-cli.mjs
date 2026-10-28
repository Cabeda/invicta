import fs from 'node:fs';
import {compareService} from './service-model.mjs';
const args=process.argv.slice(2),value=k=>args[args.indexOf(k)+1];
const facts=JSON.parse(fs.readFileSync(new URL('./data/official-extension/full-line-service-facts.json',import.meta.url),'utf8'));
const settings=args.includes('--config')?JSON.parse(fs.readFileSync(value('--config'),'utf8')):{};
const result=compareService(facts,settings);
if(args.includes('--output'))fs.writeFileSync(value('--output'),JSON.stringify(result,null,2));
console.log(JSON.stringify({reference:result.reference.summary,scenario:result.scenario.summary,other_trips_changed:result.other_trips_changed,other_trips_later:result.other_trips_later},null,2));
