// Run the real isolation checker in disposable project-scoped repositories.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
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
const guardedFiles=new Set(),guardedDirectories=new Set();
function run(expected,profile,{guarded=false}={}){
 const guard=path.join(fixture,'guard-reference-reads.mjs');
 if(guarded)write('guard-reference-reads.mjs',`import fs from 'node:fs';import path from 'node:path';\nconst normalize=p=>path.resolve(String(p)).toLowerCase();const files=new Set(${JSON.stringify([...guardedFiles])}.map(normalize));const directories=new Set(${JSON.stringify([...guardedDirectories])}.map(normalize));const read=fs.readFileSync,walk=fs.readdirSync;fs.readFileSync=function(p,...args){if(typeof p!=='number'&&files.has(normalize(p)))throw new Error('Existence-only or excluded content read: '+p);return read.call(this,p,...args);};fs.readdirSync=function(p,...args){if(directories.has(normalize(p)))throw new Error('Existence-only directory traversed: '+p);return walk.call(this,p,...args);};\n`);
 const result=spawnSync(process.execPath,[...(guarded?['--import',pathToFileURL(guard).href]:[]),path.join(tools,'check-isolation.mjs'),'current','--project','sample-project2',...(profile?['--profile',profile]:[])],{encoding:'utf8'});
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
 // The exact preflight navigation exceptions are existence checks, not content inputs.
 const ownSpec='sample-project2/spec/Access/README.md';
 const href=file=>path.relative(path.dirname(path.join(fixture,ownSpec)),path.join(fixture,file)).split(path.sep).map(encodeURIComponent).join('/')||'.';
 const common=['AGENTS.md','agents/README.md','docs/UIパターン規約.md','docs/WinForms画面品質規約.md','docs/Access画面品質規約.md'];
 const design=['requirement','basic-design','detail-design'].flatMap(agent=>{
  const name=agent==='requirement'?'要件定義':agent==='basic-design'?'基本設計':'詳細設計',base=`agents/designs/${agent}-agent`;
  return ['AGENT.md','PROMPT.md','README.md',`rules/${name}書作成ルール.md`,`workflows/${name}.md`].map(leaf=>`${base}/${leaf}`);
 });
 const directories=['requirement','basic-design','detail-design'].flatMap(agent=>['rules','workflows'].map(name=>`agents/designs/${agent}-agent/${name}`));
 const reports=['basic-design','detail-design'].map(stage=>`sample-project2/srcs/Access/build/spec-generation/${stage}/report.md`);
 for(const file of [...common,...design,...reports]){write(file,'Existence only. Never read this body.');guardedFiles.add(path.join(fixture,file));}
 for(const dir of directories){fs.mkdirSync(path.join(fixture,dir),{recursive:true});guardedDirectories.add(path.join(fixture,dir));}
 guardedFiles.add(path.join(fixture,'sample-project1/spec/poison.md'));
 guardedFiles.add(path.join(fixture,'sample-project2/spec/Future_Method/README.md'));
 guardedFiles.add(path.join(fixture,'sample-project2/srcs/Future_Method/README.md'));
 for(const prefix of ['sample-project2/spec/Access','sample-project2/srcs/Access'])for(const branch of ['.TMP','SPEC-EVAL','SPEC-ANALYSIS','BUILD','.GIT']){
  const file=`${prefix}/${branch}/poison.md`;write(file,'Excluded tree body must not be read');guardedFiles.add(path.join(fixture,file));
 }
 const accepted=[...common,...design,...directories,...reports];
 write(ownSpec,accepted.map(file=>`[guide](${href(file)})`).join('\n'));
 const guides=run(0,'Access',{guarded:true});
 assert.equal(guides.referenceChecks.filter(c=>c.referenceClass?.endsWith('-existence')).length,accepted.length);
 assert.ok(guides.referenceChecks.every(c=>c.kind!=='document-reference'||c.contentReadByReferenceCheck===false&&c.inputPromoted===false));
 assert.equal(fs.existsSync(path.join(fixture,'sample-project1/build')),false);
 const rejected=[
  'sample-project2/spec/Future_Method/README.md','sample-project1/spec/poison.md',
  'sample-project2/spec-eval/poison.md','sample-project2/spec-analysis/poison.md',
  'sample-project2/srcs/Access/README.md','sample-project2/srcs/Future_Method/README.md',
  'docs/WEB画面品質規約.md','docs/unlisted.md','agents/designs/basic-design-agent/build/report.md',
  'agents/designs/basic-design-agent/rules/arbitrary.md','agents/designs/basic-design-agent',
  'references/web-ui-standard/README.md','sample-project2/srcs/Access/build/spec-generation/requirement/report.md',
 ];
 for(const file of rejected){
  if(file!=='agents/designs/basic-design-agent'&&!fs.existsSync(path.join(fixture,file)))write(file,'Rejected reference body');
  if(!file.startsWith('sample-project2/srcs/Access/'))guardedFiles.add(path.join(fixture,file));
  write(ownSpec,`[bad](${href(file)})`);
  assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='SPECIFICATION_REFERENCE_OUTSIDE'),file);
 }
 for(const branch of ['.tmp','spec-eval','spec-analysis','build','.git','.TMP','SPEC-EVAL','BUILD']){
  const file=`sample-project2/spec/Access/${branch}/poison.md`;write(file,'Excluded reference body');guardedFiles.add(path.join(fixture,file));
  write(ownSpec,`[bad](${href(file)})`);
  assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='SPECIFICATION_REFERENCE_OUTSIDE'),file);
 }
 write(ownSpec,'[bad](%ZZ)');assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='DOCUMENT_REFERENCE_ENCODING'));
 write(ownSpec,`[bad](${href('sample-project1/spec/poison.md').replaceAll('..','%2e%2e')})`);
 assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='SPECIFICATION_REFERENCE_OUTSIDE'));
 // Missing and nonregular approved targets must fail without reading bodies.
 const approved='docs/Access画面品質規約.md',approvedPath=path.join(fixture,approved);
 write(ownSpec,`[guide](${href(approved)})`);fs.unlinkSync(approvedPath);
 assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='DOCUMENT_REFERENCE_MISSING'));
 fs.mkdirSync(approvedPath);assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='DOCUMENT_REFERENCE_NONREGULAR'));fs.rmdirSync(approvedPath);
 // A junction at an approved file name and a redirected approved parent both fail.
 const held=path.join(fixture,'held-guides');fs.mkdirSync(held);fs.writeFileSync(path.join(held,'Access画面品質規約.md'),'Redirected content');
 fs.symlinkSync(held,approvedPath,'junction');assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='DOCUMENT_REFERENCE_NONREGULAR'));fs.unlinkSync(approvedPath);write(approved,'Existence only');
 const ruleDir=path.join(fixture,'agents/designs/basic-design-agent/rules'),heldRules=path.join(fixture,'held-rules');
 fs.renameSync(ruleDir,heldRules);fs.symlinkSync(heldRules,ruleDir,'junction');
 write(ownSpec,`[guide](${href('agents/designs/basic-design-agent/rules/基本設計書作成ルール.md')})`);
 assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='DOCUMENT_REFERENCE_NONREGULAR'));
 fs.unlinkSync(ruleDir);fs.renameSync(heldRules,ruleDir);
 // Accepted declaration-derived family rules for new registered profiles stay exact.
 write('sample-project2/spec/Future_Method/規約/UIパターン.json',JSON.stringify({schemaVersion:1,family:'TEXT',renderer:'TERMINAL'}));
 write('docs/Text画面品質規約.md','Existence-only adopted TEXT rule');
 guardedFiles.delete(path.join(fixture,'sample-project2/spec/Future_Method/README.md'));
 guardedFiles.delete(path.join(fixture,'sample-project2/srcs/Future_Method/README.md'));
 guardedFiles.add(path.join(fixture,'docs/Text画面品質規約.md'));
 write('sample-project2/spec/Future_Method/README.md',`[rule](${path.relative(path.join(fixture,'sample-project2/spec/Future_Method'),path.join(fixture,'docs/Text画面品質規約.md')).split(path.sep).join('/')})`);
 fs.unlinkSync(path.join(fixture,'sample-project2/srcs/Future_Method/leak.md'));
 assert.equal(run(0,'Future_Method',{guarded:true}).status,'PASSED');
 // Source-document evaluation references remain forbidden too.
 write(ownSpec,'# Independent specification\n');
 write('sample-project2/srcs/Access/README.md','[bad](SPEC-EVAL/poison.md)');
 assert.ok(run(1,'Access',{guarded:true}).findings.some(f=>f.code==='DOCUMENT_REFERENCE_OUTSIDE'));
 write('sample-project2/srcs/Access/README.md','[Own specification](../../spec/Access/README.md)');
 assert.equal(run(0,'Access',{guarded:true}).status,'PASSED');
 fs.renameSync(path.join(fixture,'sample-project2/srcs/Access'),path.join(fixture,'sample-project2/srcs/held'));
 const missing=run(1,'Access');assert.equal(missing.status,'FAILED');assert.ok(missing.findings.some(f=>f.code==='INSPECTION_FAILED'));
 console.log(JSON.stringify({status:'PASSED',checks,existenceOnlyTargets:accepted.length,scope:'registered method selection; exact common/design/report existence only with read/traversal guards; excluded/cross-project/cross-profile/encoded escapes; missing/nonregular/junction targets; declaration-derived family; stale success invalidation',formalScore:null}));
}finally{
 // Delete only the verified, newly-created fixture inside this tool's scratch.
 assert.equal(path.dirname(fixture),scratch);assert.ok(path.basename(fixture).startsWith('fixture-'));
 fs.rmSync(fixture,{recursive:true});
}
