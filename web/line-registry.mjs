/** @typedef {{id:string,operator:string,name:{pt:string,en:string},description:{pt:string,en:string},data:string,reference:string,report:string,capabilities:{serviceModel:boolean},sourceUrl:string}} LineRegistration */
/** @typedef {{schema:string,defaultLine:string,lines:LineRegistration[]}} LineRegistry */

/** @param {unknown} value @returns {LineRegistry} */
export function validateRegistry(value) {
  const registry=/** @type {LineRegistry} */(value);
  if(registry?.schema!=='invicta.lines.v1'||!Array.isArray(registry.lines)||!registry.lines.length)throw Error('Invalid line registry');
  const ids=new Set();
  for(const line of registry.lines){
    if(!/^[a-zA-Z0-9_-]+$/.test(line.id)||ids.has(line.id))throw Error('Invalid or duplicate line identity');ids.add(line.id);
    for(const key of ['data','reference','report']){const path=/** @type {string} */(line[/** @type {'data'} */(key)]);if(typeof path!=='string'||!path||path.startsWith('/')||path.split('/').includes('..')||/[:?#\\]/.test(path))throw Error('Line assets must use local relative paths')}
    if(!line.name?.pt||!line.name?.en||!line.description?.pt||!line.description?.en||typeof line.capabilities?.serviceModel!=='boolean')throw Error('Line description or capabilities missing');
    if(!/^https:\/\//.test(line.sourceUrl))throw Error('Official source URL must use HTTPS');
  }
  if(!ids.has(registry.defaultLine))throw Error('Default line is not registered');
  return registry;
}

/** @param {LineRegistry} registry @param {string|URL} url @returns {LineRegistration} */
export function selectLine(registry,url) {
  const parsed=new URL(url),id=parsed.searchParams.get('lineId')||registry.defaultLine;
  const line=registry.lines.find(line=>line.id===id);if(!line)throw Error('Unknown line: '+id);
  return line;
}

export async function loadLine(url=location.href) {
  const base=new URL('./',url),response=await fetch(new URL('lines.json',base));
  if(!response.ok)throw Error('Line registry unavailable');
  const registry=validateRegistry(await response.json()),line=selectLine(registry,url);
  const results=await Promise.all([line.data,line.reference].map(async file=>{const r=await fetch(new URL(file,base));if(!r.ok)throw Error('Line asset unavailable: '+file);return r.json()}));
  const [data,reference]=results;
  if(String(data.meta?.route)!==line.id||String(reference.route)!==line.id||String(data.replay_manifest?.scope.route)!==line.id)throw Error('Registered line and native study do not match');
  return {registry,line,data,reference};
}
