// Contract tests use an isolated fixture; output histories are never required.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(here,'../.tmp/preflight-tests');fs.mkdirSync(base,{recursive:true});
const fixture=fs.mkdtempSync(path.join(base,'work-'));const root=path.join(fixture,'repo');let passed=0;
const files=['AGENTS.md','agents/README.md','agents/spec-agent/AGENT.md','agents/build-agent/AGENT.md','agents/build-agent/PROMPT.md','agents/build-agent/README.md','agents/reverse-agent/AGENT.md','docs/リポジトリ構成.md','docs/開発規約.md','docs/仕様書作成ルール.md','docs/評価規約.md','docs/MD構造・Excel変換規約.md','docs/テーブル仕様書記述規約.md','docs/テストデータ整備規約.md','agents/build-agent/docs/Access生成チェック.md','test-project1/README.md','test-project1/プロジェクト情報.md','test-project1/docs/開発規約.md'];
function write(file,text){const target=path.join(root,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,text);}
function doc(file,id){return `<!-- spec-meta: ${JSON.stringify({schema:'spec-md/1.0',documentId:id,version:'1.0',path:file,sheets:[{heading:'定義',kind:'LIST',sheet:'01_定義',key:['ID']}]})} -->\n# fixture\n\n## 定義\n\n| ID | 内容 |\n| --- | --- |\n| A | fixture |\n`;}
function exec(script,id,expected,profile,inspectOnly=false){const r=spawnSync(process.execPath,[path.join(root,'agents/build-agent/scripts',script),'--project','test-project1','--run-id',id,...(profile?['--profile',profile]:[]),...(inspectOnly?['--inspect-only','true']:[])],{encoding:'utf8'});if(r.status!==expected)throw new Error(`${script}: expected ${expected}, got ${r.status}: ${r.stderr}${r.stdout}`);passed++;return r;}
const generation=profile=>path.join(root,'test-project1',...(profile?['srcs',profile]:[]),'build/generation');
const read=(name,profile)=>JSON.parse(fs.readFileSync(path.join(generation(profile),name),'utf8'));
function assert(ok,text){if(!ok)throw new Error(text);passed++;}
function snapshot(directory=root){return fs.readdirSync(directory,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name)).flatMap(entry=>{const target=path.join(directory,entry.name),file=path.relative(root,target);return entry.isDirectory()?[{file,directory:true},...snapshot(target)]:[{file,data:fs.readFileSync(target).toString('base64')}];});}
try{
 files.forEach((f,i)=>write(f,doc(f,f==='agents/build-agent/AGENT.md'?'AG-BUILD':`FIX-${i}`)));
 write('test-project1/spec/README.md',doc('test-project1/spec/README.md','ROUTING'));
 for(const profile of ['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access']){const file=`test-project1/spec/${profile}/README.md`;write(file,doc(file,`SPEC-${profile}`));write(`test-project1/srcs/${profile}/README.md`,`[own specification](../../spec/${profile}/README.md)\n`);}
 for(const script of ['preflight.mjs','manifest.mjs','input-scope.mjs','output-layout.mjs','source-files.mjs','check-isolation.mjs','isolate-specs.mjs','finalize-isolation-docs.mjs','document-dotnet-projects.mjs'])write('agents/build-agent/scripts/'+script,fs.readFileSync(path.join(here,script),'utf8'));
 write('test-project1/spec-eval/poison.md','Must never be input');
 write('test-project1/spec/CSharp_ASPNET/spec-analysis/poison.md','Reverse-generated analysis must never be an original input');
 write('test-project1/spec/CSharp_ASPNET/spec-eval/poison.md','Evaluation input must never be read, even under canonical root');
 write('test-project1/srcs/CSharp_ASPNET/spec/poison.md','Legacy location must never be input or output');
 exec('preflight.mjs','current',0);
 assert(!read('inputs.json').files.some(f=>f.file.includes('spec-eval')||f.file.includes('spec-analysis')||f.file.includes('/srcs/')),'Evaluation/analysis/source/legacy input leaked');
 assert(read('inputs.json').files.filter(f=>/^test-project1\/spec\/[^/]+\/README.md$/.test(f.file)).length===7,'Aggregate did not inspect all independent packages');
 const dataRule='docs/テストデータ整備規約.md',accessRule='agents/build-agent/docs/Access生成チェック.md';
 assert(read('inputs.json').files.some(f=>f.file===dataRule)&&read('inputs.json').files.some(f=>f.file===accessRule),'Aggregate omitted common data or Access quality rules');
 const accessOriginal=fs.readFileSync(path.join(root,accessRule));
 write(accessRule,'Invalid Access-only quality document');
 const otherInspection=JSON.parse(exec('preflight.mjs','other-rule-isolation',0,'CSharp_ASPNET',true).stdout);
 assert(otherInspection.inputs.files.some(f=>f.file===dataRule)&&!otherInspection.inputs.files.some(f=>f.file===accessRule),'Non-Access scope did not freeze common data alone');
 const accessInspection=JSON.parse(exec('preflight.mjs','access-rule-invalid',2,'Access',true).stdout);
 assert(accessInspection.structure.findings.some(f=>f.file===accessRule&&f.code==='META_JSON'),'Access did not validate its required quality rule');
 write(accessRule,accessOriginal);
 write('test-project1/build/generation/outputs.json','obsolete success');
 exec('preflight.mjs','current',0);
 assert(!fs.existsSync(path.join(generation(),'outputs.json')),'Old output manifest remained current');
 assert(fs.readdirSync(generation()).sort().join(',')==='inputs.json,structure.json,structure.md','Generation history accumulated');
 const file='test-project1/spec/Access/unit.md';const valid=doc(file,'UNIT');
 for(const [value,code] of [[valid+'| A | duplicate |\n','TABLE_KEY'],[valid.replace('## 定義','## 別の章'),'CHAPTER_MAPPING'],[valid.replace('| A | fixture |','| A | [missing](missing.md) |'),'LINK_MISSING']]){write(file,value);exec('preflight.mjs','current',2);assert(read('structure.json').findings.some(f=>f.code===code),code+' not detected');}
 write(file,valid);
 const profile='CSharp_ASPNET',isolated=`test-project1/spec/${profile}/unit.md`;
 write(isolated,doc(isolated,'ISOLATED'));write('test-project1/spec/COBOL/poison.md','Must not inspect another profile');
 exec('preflight.mjs','scoped',0,profile);
 assert(!read('inputs.json',profile).files.some(f=>f.file.includes('/COBOL/')),'Peer input leaked');
 assert(read('inputs.json',profile).files.some(f=>f.file===dataRule)&&!read('inputs.json',profile).files.some(f=>f.file===accessRule),'Scoped input rule selection changed');
 write(`test-project1/srcs/${profile}/.tmp/secret.json`,'never an output');write(`test-project1/srcs/${profile}/sample.cs`,'// fixture');write(`test-project1/srcs/${profile}/build/app/final.txt`,'final fixture result');
 write(`test-project1/srcs/${profile}/build/source.zip`,'old unvalidated archive');
 exec('manifest.mjs','scoped',0,profile);
 const result=read('outputs.json',profile);
 assert(!result.files.some(f=>/\/(?:\.tmp|spec)\//.test(f.file)),'Scratch/legacy specification leaked into manifest');
 assert(result.artifacts.some(f=>f.file.endsWith('/build/app/final.txt')),'Final artifact missing');
 assert(!result.artifacts.some(f=>f.file.endsWith('/source.zip')),'Unvalidated source archive became current');
 const dataOriginal=fs.readFileSync(path.join(root,dataRule));
 write(dataRule,dataOriginal.toString('utf8').replace('| A | fixture |','| A | changed data contract |'));exec('manifest.mjs','scoped',1,profile);write(dataRule,dataOriginal);
 exec('preflight.mjs','access-rules',0,'Access');
 assert(read('inputs.json','Access').files.some(f=>f.file===accessRule)&&read('inputs.json','Access').files.some(f=>f.file===dataRule),'Access input omitted required quality or data contract');
 exec('manifest.mjs','access-rules',0,'Access');
 write(accessRule,accessOriginal.toString('utf8').replace('| A | fixture |','| A | changed Access quality contract |'));
 exec('manifest.mjs','access-rules',1,'Access');exec('manifest.mjs','scoped',0,profile);write(accessRule,accessOriginal);
 exec('manifest.mjs','scoped',0,profile);
 assert(fs.readdirSync(generation(profile)).filter(f=>f.endsWith('outputs.json')).length===1,'Manifest history accumulated');
 const frozen=fs.readFileSync(path.join(generation(profile),'inputs.json')),structure=fs.readFileSync(path.join(generation(profile),'structure.json'));
 let before=JSON.stringify(snapshot());const inspection=JSON.parse(exec('preflight.mjs','inspection',0,profile,true).stdout);
 assert(inspection.inspectionOnly&&inspection.inputs.inspectionOnly&&inspection.structure.inspectionOnly,'Inspection provenance missing');
 assert(JSON.stringify(snapshot())===before,'Read-only inspection changed files or directories');
 write(`test-project1/srcs/${profile}/build/generation/inputs.json`,JSON.stringify(inspection.inputs));write(`test-project1/srcs/${profile}/build/generation/structure.json`,JSON.stringify(inspection.structure));exec('manifest.mjs','inspection',1,profile);
 write(`test-project1/srcs/${profile}/build/generation/inputs.json`,frozen);write(`test-project1/srcs/${profile}/build/generation/structure.json`,structure);
 const forged=JSON.parse(frozen);forged.files.push({file:'test-project1/spec-eval/poison.md',sha256:'irrelevant'});write(`test-project1/srcs/${profile}/build/generation/inputs.json`,JSON.stringify(forged));exec('manifest.mjs','scoped',1,profile);write(`test-project1/srcs/${profile}/build/generation/inputs.json`,frozen);
 const added=`test-project1/spec/${profile}/added.md`;write(added,doc(added,'ADDED'));exec('manifest.mjs','scoped',1,profile);fs.unlinkSync(path.join(root,added));
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |','| A | changed input |'));exec('manifest.mjs','scoped',1,profile);
 exec('preflight.mjs','new-current',0,profile);exec('manifest.mjs','scoped',1,profile);
 assert(!fs.existsSync(path.join(root,`test-project1/srcs/${profile}/build/source.zip`)),'Previous source archive remained published after new preflight');
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |','| A | [shared](../COBOL/README.md) |'));
 exec('preflight.mjs','new-current',2,profile);assert(read('structure.json',profile).findings.some(f=>f.code==='LINK_ISOLATION'),'Cross-profile reference not rejected');exec('manifest.mjs','new-current',1,profile);
 for(const href of ['../../spec-eval/poison.md',`../../srcs/${profile}/README.md`]){write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |',`| A | [outside](${href}) |`));before=JSON.stringify(snapshot());const failed=JSON.parse(exec('preflight.mjs','scope-failure',2,profile,true).stdout);assert(failed.structure.findings.some(f=>f.code==='LINK_ISOLATION'),'Independent package closure not enforced');assert(JSON.stringify(snapshot())===before,'Failed inspection changed files');}
 write(isolated,doc(isolated,'ISOLATED'));
 const detail=`test-project1/spec/${profile}/詳細仕様書/01_学生検索画面.md`;write(detail,doc(detail,'DETAIL').replace('## 定義','## 定義\n\n### EV-SRC-001'));const event=JSON.parse(exec('preflight.mjs','event-failure',2,profile,true).stdout);assert(event.structure.findings.filter(f=>f.code==='EVENT_SECTIONS').length===6,'Relocated events were not inspected');fs.unlinkSync(path.join(root,detail));
 const spec=path.join(root,`test-project1/spec/${profile}`),moved=path.join(root,'test-project1/.tmp/spec-held');fs.mkdirSync(path.dirname(moved),{recursive:true});fs.renameSync(spec,moved);exec('preflight.mjs','missing-new-root',1,profile,true);assert(!fs.existsSync(spec),'Legacy fallback recreated canonical spec root');fs.renameSync(moved,spec);
 for(const script of ['isolate-specs.mjs','finalize-isolation-docs.mjs','document-dotnet-projects.mjs']){before=JSON.stringify(snapshot());const retired=spawnSync(process.execPath,[path.join(root,'agents/build-agent/scripts',script)],{encoding:'utf8'});assert(retired.status===1&&retired.stderr.includes('Retired migration'),'Historical writer was not refused');assert(JSON.stringify(snapshot())===before,'Historical writer changed files');}
 function isolation(expected){const r=spawnSync(process.execPath,[path.join(root,'agents/build-agent/scripts/check-isolation.mjs'),'fixture-isolation'],{encoding:'utf8'});assert(r.status===expected,`Isolation expected ${expected}: ${r.stderr}${r.stdout}`);}
 isolation(0);const ownReadme=`test-project1/spec/${profile}/README.md`,ownOriginal=fs.readFileSync(path.join(root,ownReadme));write(ownReadme,`[source](../../srcs/${profile}/README.md)\n`);isolation(1);const isolatedResult=JSON.parse(fs.readFileSync(path.join(root,'test-project1/build/test-results/isolation.json'),'utf8'));assert(isolatedResult.findings.some(f=>f.code==='SPECIFICATION_REFERENCE_OUTSIDE'),'Specification dependency on generated source was not rejected');write(ownReadme,ownOriginal);
 console.log(`PASS ${passed} assertions: canonical specification roots, independent closure, common data and scoped Access quality rule freezing, read-only inspection, frozen-set checks, retired writers, latest replacement and source-only inventory; fixture only.`);
}finally{
 const resolved=path.resolve(fixture);if(!resolved.startsWith(base+path.sep))throw new Error('Cleanup target outside fixture area');fs.rmSync(resolved,{recursive:true,force:true});
}
