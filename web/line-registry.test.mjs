import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {validateRegistry,selectLine,loadLine} from './line-registry.mjs';
const line=id=>({id,operator:'STCP',name:{pt:id,en:id},description:{pt:'Percurso',en:'Route'},data:id+'.json',reference:id+'-reference.json',report:id+'-report.md',sourceUrl:'https://stcp.pt/pt/linhas/'+id,capabilities:{serviceModel:false}});
const registry=()=>({schema:'invicta.lines.v1',defaultLine:'701',lines:[line('701'),line('702')]});
test('another line uses the same registration and selection interface without a new page',()=>{
 const catalog=validateRegistry(registry());assert.equal(selectLine(catalog,'https://example.test/?lineId=702').id,'702');
 assert.equal(selectLine(catalog,'https://example.test/').id,'701');assert.throws(()=>selectLine(catalog,'https://example.test/?lineId=999'),/Unknown line/);
});
test('invalid identities, duplicate lines and asset paths fail registration',()=>{
 const duplicate=registry();duplicate.lines[1]=line('701');assert.throws(()=>validateRegistry(duplicate),/duplicate/);
 for(const path of ['../secret','https://example.test/data.json','/data.json']){const value=registry();value.lines[0].data=path;assert.throws(()=>validateRegistry(value),/relative paths/)}
});
test('line loading verifies selected data and native coverage through real HTTP responses',async()=>{
 const server=createServer((req,res)=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(req.url==='/lines.json'?registry():req.url==='/702-reference.json'?{route:'702'}:{meta:{route:'702'},replay_manifest:{scope:{route:'702'}}}))});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{const {port}=server.address(),result=await loadLine(`http://127.0.0.1:${port}/?lineId=702`);assert.equal(result.line.id,'702');assert.equal(result.data.meta.route,'702')}finally{await new Promise(resolve=>server.close(resolve))}
});
