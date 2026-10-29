// Run the real isolation checker in disposable project-scoped repositories.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const scratch=path.resolve(here,'../.tmp/isolation-tests');
fs.mkdirSync(scratch,{recursive:true});
const fixture=fs.mkdtempSync(path.join(scratch,'fixture-'));
const tools=path.join(fixture,'agents/builds/build-agent/scripts');
fs.mkdirSync(tools,{recursive:true});
for(const name of ['check-isolation.mjs','output-layout.mjs','source-files.mjs','input-scope.mjs','project-scope.mjs'])fs.copyFileSync(path.join(here,name),path.join(tools,name));
const write=(file,text)=>{fs.mkdirSync(path.dirname(path.join(fixture,file)),{recursive:true});fs.writeFileSync(path.join(fixture,file),text);};
write('sample-project2/spec/README.md','|方式ID|specRoot|sourceRoot|\n|---|---|---|\n|Access|sample-project2/spec/Access/|sample-project2/srcs/Access/|\n|Future_Method|sample-project2/spec/Future_Method/|sample-project2/srcs/Future_Method/|\n');
for(const profile of ['Access','Future_Method']){
 write(`sample-project2/spec/${profile}/README.md`,'# Independent specification\n');
 write(`sample-project2/srcs/${profile}/README.md`,`[Own specification](../../spec/${profile}/README.md)\n`);
}
write('sample-project1/spec/poison.md','not a valid input');
let checks=0;
function run(expected,profile){
 const result=spawnSync(process.execPath,[path.join(tools,'check-isolation.mjs'),'current','--project','sample-project2',...(profile?['--profile',profile]:[])],{encoding:'utf8'});
 assert.equal(result.status,expected,result.stderr+result.stdout);checks++;
 return result.stdout.trim()?JSON.parse(result.stdout):null;
}
try{
 assert.deepEqual(run(0).profiles,['Access','Future_Method']);
 assert.equal(fs.existsSync(path.join(fixture,'sample-project1/build')),false);
 write('sample-project2/srcs/Future_Method/leak.md','[Outside](../../../sample-project1/spec/poison.md)');
 assert.equal(run(1).findings[0].code,'DOCUMENT_REFERENCE_OUTSIDE');
 assert.deepEqual(run(0,'Access').profiles,['Access']);
 run(1,'NotRegistered');
 assert.equal(fs.existsSync(path.join(fixture,'sample-project2/srcs/NotRegistered')),false);
 write('sample-project2/srcs/Access/src/modules/leak.bas','Attribute VB_Name = "Leak"\n\' srcs/Future_Method/database/schema.sql\n');
 assert.ok(run(1,'Access').findings.some(f=>f.code==='CROSS_PROFILE_PATH'));
 fs.unlinkSync(path.join(fixture,'sample-project2/srcs/Access/src/modules/leak.bas'));
 write('sample-project2/spec/Access/README.md','[Generated source](../../srcs/Access/README.md)');
 assert.ok(run(1,'Access').findings.some(f=>f.code==='SPECIFICATION_REFERENCE_OUTSIDE'));
 write('sample-project2/spec/Access/README.md','# Independent specification\n');
 assert.equal(run(0,'Access').status,'PASSED');
 fs.renameSync(path.join(fixture,'sample-project2/srcs/Access'),path.join(fixture,'sample-project2/srcs/held'));
 const missing=run(1,'Access');assert.equal(missing.status,'FAILED');assert.ok(missing.findings.some(f=>f.code==='INSPECTION_FAILED'));
 console.log(JSON.stringify({status:'PASSED',checks,scope:'registered method selection, independent project scope, VBA paths, dependency closure and stale success invalidation in disposable fixtures',formalScore:null}));
}finally{
 // Delete only the verified, newly-created fixture inside this tool's scratch.
 assert.equal(path.dirname(fixture),scratch);assert.ok(path.basename(fixture).startsWith('fixture-'));
 fs.rmSync(fixture,{recursive:true});
}
