// Contract tests use an isolated fixture; output histories are never required.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(here,'../.tmp/preflight-tests');fs.mkdirSync(base,{recursive:true});
const fixture=fs.mkdtempSync(path.join(base,'work-'));const root=path.join(fixture,'repo');let passed=0;
const detailInputs=['agents/designs/detail-design-agent/AGENT.md','agents/designs/detail-design-agent/rules/詳細設計書作成ルール.md','agents/designs/detail-design-agent/workflows/詳細設計.md'];
const uiInputs=['docs/UIパターン規約.md','docs/WEB画面品質規約.md','docs/WinForms画面品質規約.md','docs/Text画面品質規約.md','agents/builds/build-agent/docs/UIパターン生成チェック.md'];
const files=['AGENTS.md','agents/README.md',...detailInputs,...uiInputs,'agents/builds/build-agent/AGENT.md','agents/builds/build-agent/PROMPT.md','agents/builds/build-agent/README.md','agents/reverses/reverse-agent/AGENT.md','docs/リポジトリ構成.md','docs/開発規約.md','docs/仕様書作成ルール.md','docs/評価規約.md','docs/MD構造・Excel変換規約.md','docs/テーブル仕様書記述規約.md','docs/テストデータ整備規約.md','docs/UI適合検査.md','docs/Access画面品質規約.md','agents/builds/build-agent/docs/Access生成チェック.md','sample-project1/README.md','sample-project1/プロジェクト情報.md','sample-project1/docs/開発規約.md'];
function write(file,text){const target=path.join(root,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,text);}
function doc(file,id){return `<!-- spec-meta: ${JSON.stringify({schema:'spec-md/1.0',documentId:id,version:'1.0',path:file,sheets:[{heading:'定義',kind:'LIST',sheet:'01_定義',key:['ID']}]})} -->\n# fixture\n\n## 定義\n\n| ID | 内容 |\n| --- | --- |\n| A | fixture |\n`;}
const readGuard=path.join(fixture,'read-guard.cjs');
fs.writeFileSync(readGuard,`const fs=require('node:fs'),path=require('node:path'),{fileURLToPath}=require('node:url');
const denied=new Set(JSON.parse(process.env.PREFLIGHT_FORBIDDEN_READS||'[]').map(f=>path.resolve(f).toLowerCase()));
const read=fs.readFileSync;fs.readFileSync=function(file,...args){const name=file instanceof URL?fileURLToPath(file):file;if(typeof name==='string'&&denied.has(path.resolve(name).toLowerCase()))throw new Error('Existence-only target content was read: '+name);return read.call(this,file,...args);};require('node:module').syncBuiltinESMExports();\n`);
function exec(script,id,expected,profile,inspectOnly=false,project='sample-project1',unread=[]){const r=spawnSync(process.execPath,[...(unread.length?['--require',readGuard]:[]),path.join(root,'agents/builds/build-agent/scripts',script),'--project',project,'--run-id',id,...(profile?['--profile',profile]:[]),...(inspectOnly?['--inspect-only','true']:[])],{encoding:'utf8',env:{...process.env,PREFLIGHT_FORBIDDEN_READS:JSON.stringify(unread.map(file=>path.join(root,file)))}});if(r.status!==expected)throw new Error(`${script}: expected ${expected}, got ${r.status}: ${r.stderr}${r.stdout}`);passed++;return r;}
function routing(project,methods){const file=`${project}/spec/README.md`;return `<!-- spec-meta: ${JSON.stringify({schema:'spec-md/1.0',documentId:`ROUTING-${project}`,version:'1.0',path:file,sheets:[{heading:'方式',kind:'LIST',sheet:'01_方式',key:['方式ID']}]})} -->\n# Routing fixture\n\n## 方式\n\n| 方式ID | specRoot | sourceRoot |\n| --- | --- | --- |\n${methods.map(method=>`| ${method} | ${project}/spec/${method}/ | ${project}/srcs/${method}/ |`).join('\n')}\n`;}
const generation=profile=>path.join(root,'sample-project1',...(profile?['srcs',profile]:[]),'build/generation');
const read=(name,profile)=>JSON.parse(fs.readFileSync(path.join(generation(profile),name),'utf8'));
function assert(ok,text){if(!ok)throw new Error(text);passed++;}
function snapshot(directory=root){return fs.readdirSync(directory,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name)).flatMap(entry=>{const target=path.join(directory,entry.name),file=path.relative(root,target);return entry.isSymbolicLink()?[{file,symlink:fs.readlinkSync(target)}]:entry.isDirectory()?[{file,directory:true},...snapshot(target)]:[{file,data:fs.readFileSync(target).toString('base64')}];});}
try{
 const initialized=spawnSync('git',['init',root],{encoding:'utf8'});if(initialized.status!==0)throw new Error(initialized.stderr);
 files.forEach((f,i)=>write(f,doc(f,f==='agents/builds/build-agent/AGENT.md'?'AG-BUILD':`FIX-${i}`)));
 const requirementTemplate='agents/designs/requirement-agent/AGENT.md';write(requirementTemplate,'Draft requirement Agent must not become an implementation input');
 write('sample-project1/spec/README.md',routing('sample-project1',['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access']));
 for(const profile of ['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access']){const file=`sample-project1/spec/${profile}/README.md`;write(file,doc(file,`SPEC-${profile}`));const rule=`sample-project1/spec/${profile}/規約/開発規約.md`;write(rule,doc(rule,`RULE-${profile}`));write(`sample-project1/srcs/${profile}/README.md`,`[own specification](../../spec/${profile}/README.md)\n`);}
 for(const script of ['preflight.mjs','manifest.mjs','ui-conformance.mjs','input-scope.mjs','output-layout.mjs','project-scope.mjs','source-files.mjs','check-isolation.mjs','isolate-specs.mjs','finalize-isolation-docs.mjs','document-dotnet-projects.mjs'])write('agents/builds/build-agent/scripts/'+script,fs.readFileSync(path.join(here,script),'utf8'));
 for(const method of ['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access'])write(`sample-project1/srcs/${method}/profile.json`,JSON.stringify({uiConformance:{required:false,reason:'Synthetic pipeline fixture has no product UI',sourceFiles:[`sample-project1/spec/${method}/README.md`]}}));
 write('sample-project1/spec-eval/poison.md','Must never be input');
 write('sample-project1/spec/CSharp_ASPNET/spec-analysis/poison.md','Reverse-generated analysis must never be an original input');
 write('sample-project1/spec/CSharp_ASPNET/spec-eval/poison.md','Evaluation input must never be read, even under canonical root');
 write('sample-project1/srcs/CSharp_ASPNET/spec/poison.md','Legacy location must never be input or output');
 exec('preflight.mjs','current',0);
 assert(detailInputs.every(file=>read('inputs.json').files.some(f=>f.file===file))&&!read('inputs.json').files.some(f=>f.file===requirementTemplate),'Detailed-design rules were not frozen or requirement template became an implementation input');
 assert(!read('inputs.json').files.some(f=>f.file.includes('spec-eval')||f.file.includes('spec-analysis')||f.file.includes('/srcs/')),'Evaluation/analysis/source/legacy input leaked');
 assert(read('inputs.json').files.filter(f=>/^sample-project1\/spec\/[^/]+\/README.md$/.test(f.file)).length===7,'Aggregate did not inspect all independent packages');
 assert(uiInputs.every(file=>read('inputs.json').files.some(f=>f.file===file)),'Aggregate omitted UI family or generation rules');
 const familyRules={WEB:'docs/WEB画面品質規約.md',WINFORMS:'docs/WinForms画面品質規約.md',TEXT:'docs/Text画面品質規約.md'};
 function checkFamily(inspection,family){const names=inspection.inputs.files.map(record=>record.file);assert(names.includes('docs/UIパターン規約.md')&&names.includes('agents/builds/build-agent/docs/UIパターン生成チェック.md'),'Common UI inputs missing');assert(Object.entries(familyRules).every(([key,file])=>names.includes(file)===(key===family)),'Wrong family rules selected for '+family);}
 for(const [method,family] of [['CSharp_ASPNET','WEB'],['Vue_CSharpAPI','WEB'],['CSharp_WPF','WEB'],['VB.NET_WinForms','WINFORMS'],['Access','WINFORMS'],['COBOL','TEXT'],['AS400_RPG','TEXT']]) checkFamily(JSON.parse(exec('preflight.mjs','family-scope',0,method,true).stdout),family);
 const uiRule='docs/UI適合検査.md';
 assert(read('inputs.json').files.some(f=>f.file===uiRule),'Aggregate omitted the common UI conformance rule');
 const dataRule='docs/テストデータ整備規約.md',accessRule='agents/builds/build-agent/docs/Access生成チェック.md',accessLayoutRule='docs/Access画面品質規約.md';
 assert([dataRule,accessRule,accessLayoutRule].every(file=>read('inputs.json').files.some(f=>f.file===file)),'Aggregate omitted common data or Access quality rules');
 const accessOriginal=fs.readFileSync(path.join(root,accessRule));
 write(accessRule,'Invalid Access-only quality document');
 const otherInspection=JSON.parse(exec('preflight.mjs','other-rule-isolation',0,'CSharp_ASPNET',true).stdout);
 assert(otherInspection.inputs.files.some(f=>f.file===dataRule)&&![accessRule,accessLayoutRule].some(file=>otherInspection.inputs.files.some(f=>f.file===file)),'Non-Access scope included an Access-only rule');
 const accessInspection=JSON.parse(exec('preflight.mjs','access-rule-invalid',2,'Access',true).stdout);
 assert(accessInspection.structure.findings.some(f=>f.file===accessRule&&f.code==='META_JSON'),'Access did not validate its required quality rule');
 write(accessRule,accessOriginal);
 const accessLayoutOriginal=fs.readFileSync(path.join(root,accessLayoutRule));
 write(accessLayoutRule,'Invalid Access screen quality document');
 const layoutInspection=JSON.parse(exec('preflight.mjs','access-layout-invalid',2,'Access',true).stdout);
 assert(layoutInspection.structure.findings.some(f=>f.file===accessLayoutRule&&f.code==='META_JSON'),'Access did not validate its screen quality rule');
 exec('preflight.mjs','other-layout-isolation',0,'CSharp_ASPNET',true);
 fs.unlinkSync(path.join(root,accessLayoutRule));
 exec('preflight.mjs','missing-access-layout',1,'Access',true);
 exec('preflight.mjs','other-layout-absent',0,'CSharp_ASPNET',true);
 write(accessLayoutRule,accessLayoutOriginal);
 // Each family freezes its rule, rejects its removal/change, and ignores peer policies.
 for(const [method,family,peer] of [['CSharp_WPF','WEB','VB.NET_WinForms'],['VB.NET_WinForms','WINFORMS','COBOL'],['COBOL','TEXT','CSharp_WPF']]) {
  const file=familyRules[family],original=fs.readFileSync(path.join(root,file));
  exec('preflight.mjs','family-policy',0,method);exec('manifest.mjs','family-policy',0,method);
  write(file,original.toString('utf8').replace('| A | fixture |','| A | changed family policy |'));
  exec('manifest.mjs','family-policy',1,method);assert(!fs.existsSync(path.join(generation(method),'outputs.json')),'Changed family policy retained old outputs');
  exec('preflight.mjs','peer-policy',0,peer,true);write(file,original);exec('manifest.mjs','family-policy',0,method);
  fs.unlinkSync(path.join(root,file));exec('manifest.mjs','family-policy',1,method);
  assert(!fs.existsSync(path.join(generation(method),'outputs.json')),'Deleted family policy retained old outputs');
  exec('preflight.mjs','missing-family',1,method,true);exec('preflight.mjs','peer-policy-absent',0,peer,true);write(file,original);
 }
 write('sample-project1/build/generation/outputs.json','obsolete success');
 exec('preflight.mjs','current',0);
 assert(!fs.existsSync(path.join(generation(),'outputs.json')),'Old output manifest remained current');
 assert(fs.readdirSync(generation()).sort().join(',')==='inputs.json,structure.json,structure.md','Generation history accumulated');
 const file='sample-project1/spec/Access/unit.md';const valid=doc(file,'UNIT');
 for(const [value,code] of [[valid+'| A | duplicate |\n','TABLE_KEY'],[valid.replace('## 定義','## 別の章'),'CHAPTER_MAPPING'],[valid.replace('| A | fixture |','| A | [missing](missing.md) |'),'LINK_MISSING']]){write(file,value);exec('preflight.mjs','current',2);assert(read('structure.json').findings.some(f=>f.code===code),code+' not detected');}
 write(file,valid);
 const profile='CSharp_ASPNET',isolated=`sample-project1/spec/${profile}/unit.md`;
 write(isolated,doc(isolated,'ISOLATED'));write('sample-project1/spec/COBOL/poison.md','Must not inspect another profile');
 exec('preflight.mjs','scoped',0,profile);
 assert(!read('inputs.json',profile).files.some(f=>f.file.includes('/COBOL/')),'Peer input leaked');
 assert(read('inputs.json',profile).files.some(f=>f.file===dataRule)&&![accessRule,accessLayoutRule].some(file=>read('inputs.json',profile).files.some(f=>f.file===file)),'Scoped input rule selection changed');
 write(`sample-project1/srcs/${profile}/.tmp/secret.json`,'never an output');write(`sample-project1/srcs/${profile}/sample.cs`,'// fixture');write(`sample-project1/srcs/${profile}/build/app/final.txt`,'final fixture result');
 write(`sample-project1/srcs/${profile}/build/source.zip`,'old unvalidated archive');
 exec('manifest.mjs','scoped',0,profile);
 const result=read('outputs.json',profile);
 assert(!result.files.some(f=>/\/(?:\.tmp|spec)\//.test(f.file)),'Scratch/legacy specification leaked into manifest');
 assert(result.artifacts.some(f=>f.file.endsWith('/build/app/final.txt')),'Final artifact missing');
 assert(!result.artifacts.some(f=>f.file.endsWith('/source.zip')),'Unvalidated source archive became current');
 const uiOriginal=fs.readFileSync(path.join(root,uiRule));
 write(uiRule,uiOriginal.toString('utf8').replace('| A | fixture |','| A | changed UI conformance rule |'));exec('manifest.mjs','scoped',1,profile);write(uiRule,uiOriginal);
 const dataOriginal=fs.readFileSync(path.join(root,dataRule));
 write(dataRule,dataOriginal.toString('utf8').replace('| A | fixture |','| A | changed data contract |'));exec('manifest.mjs','scoped',1,profile);write(dataRule,dataOriginal);
 exec('preflight.mjs','access-rules',0,'Access');
 assert([accessRule,accessLayoutRule,dataRule].every(file=>read('inputs.json','Access').files.some(f=>f.file===file)),'Access input omitted required quality or data contract');
 exec('manifest.mjs','access-rules',0,'Access');
 write(accessRule,accessOriginal.toString('utf8').replace('| A | fixture |','| A | changed Access quality contract |'));
 exec('manifest.mjs','access-rules',1,'Access');exec('manifest.mjs','scoped',0,profile);write(accessRule,accessOriginal);
 exec('manifest.mjs','access-rules',0,'Access');
 write(accessLayoutRule,accessLayoutOriginal.toString('utf8').replace('| A | fixture |','| A | changed Access layout contract |'));
 exec('manifest.mjs','access-rules',1,'Access');
 assert(!fs.existsSync(path.join(generation('Access'),'outputs.json')),'Changed Access layout rule retained a current output manifest');
 exec('manifest.mjs','scoped',0,profile);
 write(accessLayoutRule,accessLayoutOriginal);
 exec('manifest.mjs','access-rules',0,'Access');
 fs.unlinkSync(path.join(root,accessLayoutRule));
 exec('manifest.mjs','access-rules',1,'Access');
 assert(!fs.existsSync(path.join(generation('Access'),'outputs.json')),'Deleted Access layout rule retained a current output manifest');
 exec('manifest.mjs','scoped',0,profile);
 write(accessLayoutRule,accessLayoutOriginal);
 exec('manifest.mjs','scoped',0,profile);
 assert(fs.readdirSync(generation(profile)).filter(f=>f.endsWith('outputs.json')).length===1,'Manifest history accumulated');
 const frozen=fs.readFileSync(path.join(generation(profile),'inputs.json')),structure=fs.readFileSync(path.join(generation(profile),'structure.json'));
 let before=JSON.stringify(snapshot());const inspection=JSON.parse(exec('preflight.mjs','inspection',0,profile,true).stdout);
 assert(inspection.inspectionOnly&&inspection.inputs.inspectionOnly&&inspection.structure.inspectionOnly,'Inspection provenance missing');
 assert(JSON.stringify(snapshot())===before,'Read-only inspection changed files or directories');
 write(`sample-project1/srcs/${profile}/build/generation/inputs.json`,JSON.stringify(inspection.inputs));write(`sample-project1/srcs/${profile}/build/generation/structure.json`,JSON.stringify(inspection.structure));exec('manifest.mjs','inspection',1,profile);
 write(`sample-project1/srcs/${profile}/build/generation/inputs.json`,frozen);write(`sample-project1/srcs/${profile}/build/generation/structure.json`,structure);
 const forged=JSON.parse(frozen);forged.files.push({file:'sample-project1/spec-eval/poison.md',sha256:'irrelevant'});write(`sample-project1/srcs/${profile}/build/generation/inputs.json`,JSON.stringify(forged));exec('manifest.mjs','scoped',1,profile);write(`sample-project1/srcs/${profile}/build/generation/inputs.json`,frozen);
 const added=`sample-project1/spec/${profile}/added.md`;write(added,doc(added,'ADDED'));exec('manifest.mjs','scoped',1,profile);fs.unlinkSync(path.join(root,added));
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |','| A | changed input |'));exec('manifest.mjs','scoped',1,profile);
 exec('preflight.mjs','new-current',0,profile);exec('manifest.mjs','scoped',1,profile);
 assert(!fs.existsSync(path.join(root,`sample-project1/srcs/${profile}/build/source.zip`)),'Previous source archive remained published after new preflight');
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |','| A | [shared](../COBOL/README.md) |'));
 exec('preflight.mjs','new-current',2,profile);assert(read('structure.json',profile).findings.some(f=>f.code==='LINK_ISOLATION'),'Cross-profile reference not rejected');exec('manifest.mjs','new-current',1,profile);
 for(const href of ['../../spec-eval/poison.md',`../../srcs/${profile}/README.md`]){write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |',`| A | [outside](${href}) |`));before=JSON.stringify(snapshot());const failed=JSON.parse(exec('preflight.mjs','scope-failure',2,profile,true).stdout);assert(failed.structure.findings.some(f=>f.code==='LINK_ISOLATION'),'Independent package closure not enforced');assert(JSON.stringify(snapshot())===before,'Failed inspection changed files');}
 write(isolated,doc(isolated,'ISOLATED'));
 // Links to provenance/guide material only check existence. They do not extend
 // normative inputs, recursively parse poison text, or weaken package isolation.
 const guides={
  rule:'agents/designs/basic-design-agent/rules/基本設計書作成ルール.md',
  directory:'agents/designs/basic-design-agent/rules',
  basic:`sample-project1/srcs/${profile}/build/spec-generation/basic-design/report.md`,
  detail:`sample-project1/srcs/${profile}/build/spec-generation/detail-design/report.md`,
  raw:'references/web-ui-standard/README.md',
 };
 for(const name of [guides.rule,guides.basic,guides.detail,guides.raw])write(name,'Poison without metadata. Must not read/hash/freeze as a specification input.');
 const uiIndex='docs/UIパターン規約.md',uiIndexBefore=fs.readFileSync(path.join(root,uiIndex));
 const hrefFor=(destination,source=isolated)=>path.relative(path.dirname(path.join(root,source)),path.join(root,destination)).split(path.sep).join('/')||'.';
 const link=(destination,source=isolated)=>write(source,doc(source,source===isolated?'ISOLATED':'UI-LINK').replace('| A | fixture |',`| A | [guide](${hrefFor(destination,source)}) |`));
 link(guides.raw,uiIndex);
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |',`| A | ${[guides.rule,guides.directory,guides.basic,guides.detail,'docs/仕様書作成ルール.md'].map(name=>`[guide](${hrefFor(name)})`).join(' ')} |`));
 before=JSON.stringify(snapshot());
 const guideResult=JSON.parse(exec('preflight.mjs','guide-references',0,profile,true,'sample-project1',[guides.rule,guides.basic,guides.detail,guides.raw]).stdout);
 assert(JSON.stringify(snapshot())===before,'Guide inspection wrote or moved files');
 assert([guides.rule,guides.basic,guides.detail,guides.raw].every(file=>!guideResult.inputs.files.some(record=>record.file===file)),'Existence-only references became normative inputs');
 assert(['design-rule-existence','design-record-existence','reference-source-existence','common-rule-input'].every(kind=>guideResult.structure.referenceChecks.some(check=>check.kind===kind)),'Guide reference roles were not classified');
 assert(guideResult.structure.referenceChecks.filter(check=>/^(?:design-|reference-source)/.test(check.kind)).every(check=>check.contentReadByReferenceCheck===false&&check.frozenInput===false),'Guide references were read or frozen');
 for(const [destination,code] of [
  ['sample-project1/spec/COBOL/README.md','LINK_ISOLATION'],
  ['sample-project9/spec/Other/README.md','LINK_ISOLATION'],
  [`sample-project1/srcs/${profile}/README.md`,'LINK_ISOLATION'],
  ['sample-project1/srcs/Access/build/spec-generation/basic-design/report.md','LINK_ISOLATION'],
  ['sample-project9/srcs/CSharp_ASPNET/build/spec-generation/basic-design/report.md','LINK_ISOLATION'],
  [`sample-project1/srcs/${profile}/build/generation/inputs.json`,'LINK_ISOLATION'],
  [`sample-project1/srcs/${profile}/build/spec-generation/basic-design/history/report.md`,'LINK_ISOLATION'],
  ['sample-project1/spec-eval/poison.md','LINK_ISOLATION'],
  ['agents/designs/basic-design-agent/.tmp/poison.md','LINK_ISOLATION'],
  ['agents/designs/basic-design-agent/build/report.md','LINK_ISOLATION'],
  ['agents/designs/basic-design-agent/rules/arbitrary.md','LINK_ISOLATION'],
  ['docs/unfrozen-rule.md','LINK_ISOLATION'],
  [guides.raw,'LINK_ISOLATION'],
  [`sample-project1/spec/${profile}/spec-eval/poison.md`,'LINK_ISOLATION'],
  [`sample-project1/spec/${profile}/spec-analysis/poison.md`,'LINK_ISOLATION'],
  [`sample-project1/spec/${profile}/.tmp/poison.md`,'LINK_ISOLATION'],
  [`sample-project1/spec/${profile}/build/poison.md`,'LINK_ISOLATION'],
  [`sample-project1/spec/${profile}/.TMP/`,'LINK_ISOLATION'],
  [`sample-project1/spec/${profile}/SPEC-EVAL/`,'LINK_ISOLATION'],
 ]) {
  link(destination);const failed=JSON.parse(exec('preflight.mjs','guide-isolation-negative',2,profile,true).stdout);
  assert(failed.structure.findings.some(f=>f.code===code),'Guide exception permitted '+destination);
 }
 for(const branch of ['spec-eval','spec-analysis','.tmp','build']) {
  const name=`sample-project1/spec/${profile}/${branch}/guide-unread.md`;
  write(name,'Excluded fixture body must never become input');link(name);
  const excluded=JSON.parse(exec('preflight.mjs','excluded-subtree',2,profile,true,'sample-project1',[name]).stdout);
  assert(excluded.structure.findings.some(f=>f.code==='LINK_ISOLATION')&&!excluded.inputs.files.some(f=>f.file===name),'Selected excluded subtree was inspected');
  fs.unlinkSync(path.join(root,name));fs.symlinkSync(fixture,path.join(root,name),'junction');
  assert(JSON.parse(exec('preflight.mjs','linked-excluded-subtree',2,profile,true).stdout).structure.findings.some(f=>f.code==='LINK_ISOLATION'),'Linked excluded subtree was accepted');fs.unlinkSync(path.join(root,name));
 }
 link(`sample-project1/spec/${profile}`);
 assert(JSON.parse(exec('preflight.mjs','spec-directory-guide',0,profile,true).stdout).structure.referenceChecks.some(check=>check.kind==='specification-directory-existence'&&!check.frozenInput),'Specification directory was misclassified as an input body');
 // Case-preserving Windows directory names must also be excluded during input
 // collection, before link inspection could protect against reading their body.
 const lowerScratch=`sample-project1/spec/${profile}/.tmp`,upperScratch=`sample-project1/spec/${profile}/.TMP`,heldScratch=path.join(fixture,'held-excluded-scratch');
 fs.renameSync(path.join(root,lowerScratch),heldScratch);fs.renameSync(heldScratch,path.join(root,upperScratch));
 const upperPoison=upperScratch+'/UPPER.md';write(upperPoison,'Uppercase excluded input must not be read');write(isolated,doc(isolated,'ISOLATED'));
 const uppercaseInput=JSON.parse(exec('preflight.mjs','uppercase-excluded-input',0,profile,true,'sample-project1',[upperPoison]).stdout);
 assert(!uppercaseInput.inputs.files.some(record=>record.file.toLowerCase().includes('/.tmp/')),'Uppercase excluded directory became input');
 fs.unlinkSync(path.join(root,upperPoison));fs.renameSync(path.join(root,upperScratch),heldScratch);fs.renameSync(heldScratch,path.join(root,lowerScratch));
 // A raw source README is accepted only as a frozen common docs provenance link.
 write(isolated,doc(isolated,'ISOLATED'));link('references/web-ui-standard/pattern.md',uiIndex);
 assert(JSON.parse(exec('preflight.mjs','raw-body-denied',2,profile,true).stdout).structure.findings.some(f=>f.code==='LINK_SCOPE'),'Arbitrary raw reference was accepted');
 const routingSource='agents/README.md',routingBefore=fs.readFileSync(path.join(root,routingSource));link(guides.raw,routingSource);write(uiIndex,uiIndexBefore);
 assert(JSON.parse(exec('preflight.mjs','raw-source-denied',2,profile,true).stdout).structure.findings.some(f=>f.code==='LINK_SCOPE'),'Non-doc origin gained raw-reference exception');write(routingSource,routingBefore);
 for(const name of [guides.rule,guides.basic,guides.detail,guides.raw]) {
  const original=fs.readFileSync(path.join(root,name));fs.unlinkSync(path.join(root,name));
  if(name===guides.raw){write(isolated,doc(isolated,'ISOLATED'));link(name,uiIndex);}else{write(uiIndex,uiIndexBefore);link(name);}
  assert(JSON.parse(exec('preflight.mjs','missing-guide',2,profile,true).stdout).structure.findings.some(f=>f.code==='LINK_MISSING'),'Missing guide was not rejected: '+name);write(name,original);
 }
 write(uiIndex,uiIndexBefore);
 // Directory junctions test linked leaves and redirected parents without relying
 // on Windows file-symlink privilege. No target body is read in either case.
 for(const [name,directory] of [[guides.rule,false],[guides.basic,false],[guides.raw,false],[guides.directory,true],[path.posix.dirname(guides.detail),true]]) {
  const target=path.join(root,name),held=path.join(fixture,'held-guide');fs.renameSync(target,held);
  fs.symlinkSync(directory?held:path.dirname(held),target,'junction');
  const destination=name===guides.directory?guides.rule:name===path.posix.dirname(guides.detail)?guides.detail:name;
  if(name===guides.raw){write(isolated,doc(isolated,'ISOLATED'));link(guides.raw,uiIndex);}else{write(uiIndex,uiIndexBefore);link(destination);}
  assert(JSON.parse(exec('preflight.mjs','linked-guide',2,profile,true).stdout).structure.findings.some(f=>f.code==='LINK_NONREGULAR'),'Linked/redirected guide was accepted: '+name);
  fs.unlinkSync(target);fs.renameSync(held,target);
 }
 write(uiIndex,uiIndexBefore);write(isolated,doc(isolated,'ISOLATED'));
 // Encoded traversal cannot borrow a peer report through the own-report spelling.
 write(isolated,doc(isolated,'ISOLATED').replace('| A | fixture |',`| A | [escape](${hrefFor(guides.basic).replace('CSharp_ASPNET/','CSharp_ASPNET/%2e%2e/Access/')}) |`));
 assert(JSON.parse(exec('preflight.mjs','encoded-guide-escape',2,profile,true).stdout).structure.findings.some(f=>f.code==='LINK_ISOLATION'),'Encoded report path escape was accepted');
 write(isolated,doc(isolated,'ISOLATED'));
 const detail=`sample-project1/spec/${profile}/詳細仕様書/01_学生検索画面.md`;write(detail,doc(detail,'DETAIL').replace('## 定義','## 定義\n\n### EV-SRC-001'));const event=JSON.parse(exec('preflight.mjs','event-failure',2,profile,true).stdout);assert(event.structure.findings.filter(f=>f.code==='EVENT_SECTIONS').length===6,'Relocated events were not inspected');fs.unlinkSync(path.join(root,detail));
 const modernDetail=`sample-project1/spec/${profile}/詳細仕様書/06_機能.md`;
 write(modernDetail,doc(modernDetail,'MODERN-DETAIL').replace('## 定義','## 定義\n\n### F06-E03 取消'));
 const modernEvent=JSON.parse(exec('preflight.mjs','modern-event',2,profile,true).stdout);assert(modernEvent.structure.findings.filter(f=>f.code==='EVENT_SECTIONS').length===6,'F06 modern events were skipped');fs.unlinkSync(path.join(root,modernDetail));
 write(isolated,doc(isolated,'ISOLATED').replace('fixture |','IReadOnlyList<SearchRow> / PasswordHasher<AppUser> / `Custom<Foo>` |'));
 exec('preflight.mjs','typed-text',0,profile,true);
 write(isolated,doc(isolated,'ISOLATED').replace('fixture |','<script>alert(1)</script> |'));
 assert(JSON.parse(exec('preflight.mjs','html-rejected',2,profile,true).stdout).structure.findings.some(f=>f.code==='LIST_HTML'),'Actual HTML was accepted as a C# type');write(isolated,doc(isolated,'ISOLATED'));
 for(const file of ['sample-project2/README.md','sample-project2/プロジェクト情報.md'])write(file,doc(file,`SP2-${file}`));
 write('sample-project2/spec/README.md',routing('sample-project2',['Access','CSharp_ASPNET']));
 for(const method of ['Access','CSharp_ASPNET'])for(const leaf of ['README.md','規約/開発規約.md']){const f=`sample-project2/spec/${method}/${leaf}`;write(f,doc(f,`SP2-${method}-${leaf}`));}
 write('sample-project2/spec/COBOL/poison.md','Unregistered method must never be read');
 const sp2=JSON.parse(exec('preflight.mjs','two-method-project',0,undefined,true,'sample-project2').stdout);
 assert(sp2.inputs.files.filter(f=>/^sample-project2\/spec\/[^/]+\/README.md$/.test(f.file)).length===2&&!sp2.inputs.files.some(f=>f.file.includes('/COBOL/')),'Two-method routing expanded to old fixed profiles');
 assert(!sp2.inputs.files.some(f=>f.file==='sample-project2/docs/開発規約.md')&&sp2.inputs.files.some(f=>f.file==='sample-project2/spec/Access/規約/開発規約.md'),'Method-local rules were not used');
 exec('preflight.mjs','unregistered',1,'COBOL',true,'sample-project2');
 write('sample-project2/spec/README.md',routing('sample-project2',['Access','CSharp_ASPNET','New_GUI']));
 for(const leaf of ['README.md','規約/開発規約.md']){const f=`sample-project2/spec/New_GUI/${leaf}`;write(f,doc(f,`SP2-New-${leaf}`));}
 checkFamily(JSON.parse(exec('preflight.mjs','registered-extension',0,'New_GUI',true,'sample-project2').stdout),null);
 write('sample-project2/srcs/New_GUI/profile.json',JSON.stringify({uiFamily:'WEB',renderer:'BROWSER'}));
 checkFamily(JSON.parse(exec('preflight.mjs','source-family-ignored',0,'New_GUI',true,'sample-project2').stdout),null);
 const uiMetadata='sample-project2/spec/New_GUI/規約/UIパターン.json';
 for(const [family,renderer] of [['WEB','BROWSER'],['WEB','WPF'],['TEXT','TERMINAL'],['WINFORMS','ACCESS'],['WINFORMS','WINFORMS']]) {
  write(uiMetadata,JSON.stringify({schemaVersion:1,family,renderer}));
  const declared=JSON.parse(exec('preflight.mjs','declared-extension',0,'New_GUI',true,'sample-project2').stdout);checkFamily(declared,family);
  assert(declared.inputs.files.some(record=>record.file===uiMetadata),'Explicit UI family metadata was not frozen');
  assert([accessRule,accessLayoutRule].every(file=>declared.inputs.files.some(record=>record.file===file)===(renderer==='ACCESS')),'Access renderer policies were omitted or leaked to another renderer');
  if(renderer==='ACCESS') {
   fs.unlinkSync(path.join(root,accessLayoutRule));exec('preflight.mjs','unknown-access-policy-missing',1,'New_GUI',true,'sample-project2');
   write(uiMetadata,JSON.stringify({schemaVersion:1,family:'WEB',renderer:'BROWSER'}));exec('preflight.mjs','unknown-browser-policy-isolation',0,'New_GUI',true,'sample-project2');write(accessLayoutRule,accessLayoutOriginal);
  }
 }
 for(const value of ['{broken',JSON.stringify({schemaVersion:2,family:'WEB',renderer:'BROWSER'}),JSON.stringify({schemaVersion:1,family:'OTHER',renderer:'BROWSER'}),JSON.stringify({schemaVersion:1,family:'WEB',renderer:'TERMINAL'}),JSON.stringify({schemaVersion:1,family:'WEB',renderer:'BROWSER',render:'typo'})]) {write(uiMetadata,value);exec('preflight.mjs','invalid-ui-metadata',1,'New_GUI',true,'sample-project2');}
 fs.unlinkSync(path.join(root,uiMetadata));fs.mkdirSync(path.join(root,uiMetadata));exec('preflight.mjs','nonregular-ui-metadata',1,'New_GUI',true,'sample-project2');fs.rmdirSync(path.join(root,uiMetadata));
 fs.symlinkSync(path.dirname(path.join(root,uiMetadata)),path.join(root,uiMetadata),'junction');exec('preflight.mjs','linked-ui-metadata',1,'New_GUI',true,'sample-project2');fs.unlinkSync(path.join(root,uiMetadata));
 const knownMetadata='sample-project2/spec/Access/規約/UIパターン.json';write(knownMetadata,JSON.stringify({schemaVersion:1,family:'WEB',renderer:'BROWSER'}));exec('preflight.mjs','known-ui-conflict',1,'Access',true,'sample-project2');
 write(knownMetadata,JSON.stringify({schemaVersion:1,family:'WINFORMS',renderer:'WINFORMS'}));exec('preflight.mjs','known-renderer-conflict',1,'Access',true,'sample-project2');
 write(knownMetadata,JSON.stringify({schemaVersion:1,family:'WINFORMS',renderer:'ACCESS'}));exec('preflight.mjs','known-ui-match',0,'Access',true,'sample-project2');fs.unlinkSync(path.join(root,knownMetadata));
 write(uiMetadata,JSON.stringify({schemaVersion:1,family:'WEB',renderer:'BROWSER'}));
 write('sample-project2/srcs/New_GUI/profile.json',JSON.stringify({uiConformance:{required:false,reason:'Synthetic metadata lifecycle fixture has no product UI',sourceFiles:['sample-project2/spec/New_GUI/README.md']}}));
 exec('preflight.mjs','extension-metadata',0,'New_GUI',false,'sample-project2');exec('manifest.mjs','extension-metadata',0,'New_GUI',false,'sample-project2');
 write(uiMetadata,JSON.stringify({schemaVersion:1,family:'TEXT',renderer:'TERMINAL'}));exec('manifest.mjs','extension-metadata',1,'New_GUI',false,'sample-project2');
 assert(!fs.existsSync(path.join(root,'sample-project2/srcs/New_GUI/build/generation/outputs.json')),'Changed explicit UI metadata retained old outputs');fs.unlinkSync(path.join(root,uiMetadata));
 write('sample-project2/spec/README.md',routing('sample-project2',['Access','CSharp_ASPNET']));
 const sharedRule='docs/仕様書作成ルール.md',sharedBefore=fs.readFileSync(path.join(root,sharedRule));write(sharedRule,sharedBefore.toString('utf8')+'| B | [other project routing](../sample-project9/spec/Other/missing.md) |\n');
 exec('preflight.mjs','foreign-routing',0,'Access',true,'sample-project2');write(sharedRule,sharedBefore);
 const ownRule=path.join(root,'sample-project2/spec/Access/規約/開発規約.md'),heldRule=path.join(fixture,'held-rule.md');fs.renameSync(ownRule,heldRule);exec('preflight.mjs','missing-method-rule',1,'Access',true,'sample-project2');fs.renameSync(heldRule,ownRule);
 for(const script of ['package-source.py','verify-packages.py','output_layout.py','project_scope.py'])write('agents/builds/build-agent/scripts/'+script,fs.readFileSync(path.join(here,script),'utf8'));
 for(const method of ['Access','CSharp_ASPNET'])write(`sample-project2/srcs/${method}/README.md`,'Production source fixture; original specifications excluded.\n');
 for(const method of ['Access','CSharp_ASPNET'])write(`sample-project2/srcs/${method}/profile.json`,JSON.stringify({uiConformance:{required:false,reason:'Synthetic package fixture has no product UI',sourceFiles:[`sample-project2/spec/${method}/README.md`]}}));
 write('sample-project2/srcs/Access/Build-Access.ps1','# Self-contained production builder fixture\n');write('sample-project2/srcs/Access/build/CareerManagement.accdb','fixture bytes only; not a real database');
 write('sample-project2/srcs/CSharp_ASPNET/CareerPortal.csproj','<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>\n');
 exec('preflight.mjs','sp2-pipeline',0,undefined,false,'sample-project2');
 function pythonTool(script,extra=[]){const result=spawnSync('python',['-X','utf8',path.join(root,'agents/builds/build-agent/scripts',script),'sp2-pipeline','--project','sample-project2',...extra],{encoding:'utf8'});assert(result.status===0,`${script} fixture failed: ${result.stdout}${result.stderr}`);}
 pythonTool('package-source.py');pythonTool('verify-packages.py',['--hashes-only']);exec('manifest.mjs','sp2-pipeline',0,undefined,false,'sample-project2');
 const sp2Output=JSON.parse(fs.readFileSync(path.join(root,'sample-project2/build/generation/outputs.json'),'utf8'));
 assert(sp2Output.artifacts.filter(a=>a.kind==='independent-source-only-archive').length===2,'Manifest retained a fixed seven-package count');
 assert(sp2Output.artifacts.some(a=>a.file.endsWith('/CareerManagement.accdb')&&a.kind==='standalone-access-database'),'Manifest required an old product ACCDB filename');
 const packagePath=path.join(root,'sample-project2/build/generation/source-packages.json'),packageOriginal=fs.readFileSync(packagePath);const forgedPackages=JSON.parse(packageOriginal);forgedPackages.projectId='sample-project9';fs.writeFileSync(packagePath,JSON.stringify(forgedPackages));exec('manifest.mjs','sp2-pipeline',1,undefined,false,'sample-project2');fs.writeFileSync(packagePath,packageOriginal);
 write('sample-project2/srcs/Access/build/Unexpected.accdb','second final artifact fixture');exec('manifest.mjs','sp2-pipeline',1,undefined,false,'sample-project2');fs.unlinkSync(path.join(root,'sample-project2/srcs/Access/build/Unexpected.accdb'));
 const spec=path.join(root,`sample-project1/spec/${profile}`),moved=path.join(root,'sample-project1/.tmp/spec-held');fs.mkdirSync(path.dirname(moved),{recursive:true});fs.renameSync(spec,moved);exec('preflight.mjs','missing-new-root',1,profile,true);assert(!fs.existsSync(spec),'Legacy fallback recreated canonical spec root');fs.renameSync(moved,spec);
 for(const script of ['isolate-specs.mjs','finalize-isolation-docs.mjs','document-dotnet-projects.mjs']){before=JSON.stringify(snapshot());const retired=spawnSync(process.execPath,[path.join(root,'agents/builds/build-agent/scripts',script)],{encoding:'utf8'});assert(retired.status===1&&retired.stderr.includes('Retired migration'),'Historical writer was not refused');assert(JSON.stringify(snapshot())===before,'Historical writer changed files');}
 function isolation(expected){const r=spawnSync(process.execPath,[path.join(root,'agents/builds/build-agent/scripts/check-isolation.mjs'),'fixture-isolation','--project','sample-project1'],{encoding:'utf8'});assert(r.status===expected,`Isolation expected ${expected}: ${r.stderr}${r.stdout}`);}
 isolation(0);const ownReadme=`sample-project1/spec/${profile}/README.md`,ownOriginal=fs.readFileSync(path.join(root,ownReadme));write(ownReadme,`[source](../../srcs/${profile}/README.md)\n`);isolation(1);const isolatedResult=JSON.parse(fs.readFileSync(path.join(root,'sample-project1/build/test-results/isolation.json'),'utf8'));assert(isolatedResult.findings.some(f=>f.code==='SPECIFICATION_REFERENCE_OUTSIDE'),'Specification dependency on generated source was not rejected');write(ownReadme,ownOriginal);
 console.log(`PASS ${passed} assertions: canonical specification roots, independent closure, classified existence-only guide references with denied body reads/missing/link/escape checks, scoped WEB/WinForms/Text and Access policies, explicit extension metadata and renderer checks, read-only inspection, frozen-set checks, retired writers, latest replacement and source-only inventory; fixture only.`);
}finally{
 const resolved=path.resolve(fixture);if(!resolved.startsWith(base+path.sep))throw new Error('Cleanup target outside fixture area');fs.rmSync(resolved,{recursive:true,force:true});
}
