// Contract tests use an isolated fixture; output histories are never required.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(here,'../.tmp/preflight-tests');fs.mkdirSync(base,{recursive:true});
const fixture=fs.mkdtempSync(path.join(base,'work-'));const root=path.join(fixture,'repo');let passed=0;
const files=['AGENTS.md','agents/README.md','agents/spec-agent/AGENT.md','agents/build-agent/AGENT.md','agents/build-agent/PROMPT.md','agents/build-agent/README.md','agents/reverse-agent/AGENT.md','docs/リポジトリ構成.md','docs/開発規約.md','docs/仕様書作成ルール.md','docs/評価規約.md','docs/MD構造・Excel変換規約.md','docs/テーブル仕様書記述規約.md','test-project1/README.md','test-project1/プロジェクト情報.md','test-project1/docs/開発規約.md'];
function write(file,text){const target=path.join(root,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,text);}
function doc(file,id){return `<!-- spec-meta: ${JSON.stringify({schema:'spec-md/1.0',documentId:id,version:'1.0',path:file,sheets:[{heading:'定義',kind:'LIST',sheet:'01_定義',key:['ID']}]})} -->\n# fixture\n\n## 定義\n\n| ID | 内容 |\n| --- | --- |\n| A | fixture |\n`;}
function exec(script,id,expected,profile){const r=spawnSync(process.execPath,[path.join(root,'agents/build-agent/scripts',script),'--project','test-project1','--run-id',id,...(profile?['--profile',profile]:[])],{encoding:'utf8'});if(r.status!==expected)throw new Error(`${script}: expected ${expected}, got ${r.status}: ${r.stderr}${r.stdout}`);passed++;return r;}
const generation=profile=>path.join(root,'test-project1',...(profile?['srcs',profile]:[]),'build/generation');
const read=(name,profile)=>JSON.parse(fs.readFileSync(path.join(generation(profile),name),'utf8'));
function assert(ok,text){if(!ok)throw new Error(text);passed++;}
try{
 files.forEach((f,i)=>write(f,doc(f,f==='agents/build-agent/AGENT.md'?'AG-BUILD':`FIX-${i}`)));
 fs.mkdirSync(path.join(root,'test-project1/docs/開発規約'),{recursive:true});fs.mkdirSync(path.join(root,'test-project1/spec'),{recursive:true});
 for(const script of ['preflight.mjs','manifest.mjs','output-layout.mjs'])write('agents/build-agent/scripts/'+script,fs.readFileSync(path.join(here,script),'utf8'));
 write('test-project1/spec-eval/poison.md','Must never be input');
 exec('preflight.mjs','current',0);
 assert(!read('inputs.json').files.some(f=>f.file.includes('spec-eval')),'Evaluation input leaked');
 write('test-project1/build/generation/outputs.json','obsolete success');
 exec('preflight.mjs','current',0);
 assert(!fs.existsSync(path.join(generation(),'outputs.json')),'Old output manifest remained current');
 assert(fs.readdirSync(generation()).sort().join(',')==='inputs.json,structure.json,structure.md','Generation history accumulated');
 const file='test-project1/spec/unit.md';const valid=doc(file,'UNIT');
 for(const [value,code] of [[valid+'| A | duplicate |\n','TABLE_KEY'],[valid.replace('## 定義','## 別の章'),'CHAPTER_MAPPING'],[valid.replace('| A | fixture |','| A | [missing](missing.md) |'),'LINK_MISSING']]){write(file,value);exec('preflight.mjs','current',2);assert(read('structure.json').findings.some(f=>f.code===code),code+' not detected');}
 write(file,valid);
 const profile='CSharp_ASPNET',isolated=`test-project1/srcs/${profile}/spec/unit.md`;
 write(isolated,doc(isolated,'ISOLATED'));write('test-project1/srcs/COBOL/spec/poison.md','Must not inspect another profile');
 exec('preflight.mjs','scoped',0,profile);
 assert(!read('inputs.json',profile).files.some(f=>f.file.includes('/COBOL/')),'Peer input leaked');
 write(`test-project1/srcs/${profile}/.tmp/secret.json`,'never an output');write(`test-project1/srcs/${profile}/sample.cs`,'// fixture');write(`test-project1/srcs/${profile}/build/app/final.txt`,'final fixture result');
 write(`test-project1/srcs/${profile}/build/source.zip`,'old unvalidated archive');
 exec('manifest.mjs','scoped',0,profile);
 const result=read('outputs.json',profile);
 assert(!result.files.some(f=>f.file.includes('/.tmp/')),'Scratch leaked into manifest');
 assert(result.artifacts.some(f=>f.file.endsWith('/build/app/final.txt')),'Final artifact missing');
 assert(!result.artifacts.some(f=>f.file.endsWith('/source.zip')),'Unvalidated source archive became current');
 exec('manifest.mjs','scoped',0,profile);
 assert(fs.readdirSync(generation(profile)).filter(f=>f.endsWith('outputs.json')).length===1,'Manifest history accumulated');
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |','| A | changed input |'));exec('manifest.mjs','scoped',1,profile);
 exec('preflight.mjs','new-current',0,profile);exec('manifest.mjs','scoped',1,profile);
 assert(!fs.existsSync(path.join(root,`test-project1/srcs/${profile}/build/source.zip`)),'Previous source archive remained published after new preflight');
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |','| A | [shared](../../../spec/unit.md) |'));
 exec('preflight.mjs','new-current',2,profile);assert(read('structure.json',profile).findings.some(f=>f.code==='LINK_ISOLATION'),'Cross-profile reference not rejected');exec('manifest.mjs','new-current',1,profile);
 console.log(`PASS ${passed} assertions: latest replacement, stale-result invalidation, input freeze, scope exclusion, final artifacts and structural stops; fixture only.`);
}finally{
 const resolved=path.resolve(fixture);if(!resolved.startsWith(base+path.sep))throw new Error('Cleanup target outside fixture area');fs.rmSync(resolved,{recursive:true,force:true});
}
