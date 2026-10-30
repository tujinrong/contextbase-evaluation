import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {layout,writeLatest,writeJson} from './output-layout.mjs';
import {sourceFiles} from './source-files.mjs';
import {assertRegular,fixedInputFiles,resolveUIFamily,specificationRoot} from './input-scope.mjs';
import {selectedProfiles,projectProfiles,validProject} from './project-scope.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const [runId,...args]=process.argv.slice(2);let project,selected;
if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(runId??'')||args.length%2)throw new Error('Usage: check-isolation.mjs <run-id> --project <project> [--profile <profile>]');
for(let i=0;i<args.length;i+=2){if(args[i]==='--project'&&!project)project=args[i+1];else if(args[i]==='--profile'&&!selected)selected=args[i+1];else throw new Error('Unknown/duplicate isolation option.');}
if(!validProject(project))throw new Error('Explicit safe project required.');
const profiles=selectedProfiles(root,project,selected),registered=projectProfiles(root,project),base=path.join(root,project,'srcs');
const outputLayout=layout(root,project,selected);const prefix=path.join(outputLayout.tests,'isolation');
const findings=[],checks=[],files=[];
const slash=p=>p.split(path.sep).join('/');const within=(p,base)=>p===base||p.startsWith(base+path.sep);
const excludedTrees=new Set(['spec-eval','spec-analysis','.tmp','build','.git']);
const guideFiles=new Set(['requirement','basic-design','detail-design'].flatMap(agent=>{
 const name=agent==='requirement'?'要件定義':agent==='basic-design'?'基本設計':'詳細設計',base=`agents/designs/${agent}-agent`;
 return ['AGENT.md','PROMPT.md','README.md',`rules/${name}書作成ルール.md`,`workflows/${name}.md`,'rules','workflows'].map(leaf=>`${base}/${leaf}`);
}));
const commonRules=new Map();
// Only names already selected by preflight, never arbitrary docs/Agent content.
// The optional family declaration is inside the selected specification package.
function commonRuleNames(profile){
 const names=new Set(fixedInputFiles(project,profile).filter(name=>name==='AGENTS.md'||/^(?:docs|agents)\//.test(name)));
 const ui=resolveUIFamily(root,project,profile);
 if(ui.family)names.add({WEB:'docs/WEB画面品質規約.md',WINFORMS:'docs/WinForms画面品質規約.md',TEXT:'docs/Text画面品質規約.md'}[ui.family]);
 if(ui.renderer==='ACCESS')for(const name of ['docs/Access画面品質規約.md','agents/builds/build-agent/docs/Access生成チェック.md'])names.add(name);
 return names;
}
function guideKind(local,profile){
 if(commonRules.get(profile).has(local))return 'common-rule-existence';
 if(guideFiles.has(local))return 'design-rule-existence';
 if(['basic-design','detail-design'].some(stage=>local===`${project}/srcs/${profile}/build/spec-generation/${stage}/report.md`))return 'design-record-existence';
 return null;
}
try{
for(const profile of profiles){
 const directory=path.join(base,profile),spec=specificationRoot(root,project,profile);
 commonRules.set(profile,commonRuleNames(profile));
 if(!fs.existsSync(path.join(spec,'README.md')))findings.push({profile,code:'MISSING_OWN_SPEC'});
 for(const p of sourceFiles(directory,{excludeSpec:true}))files.push({p,profile,kind:'source'});
 if(fs.existsSync(spec))for(const p of sourceFiles(spec))files.push({p,profile,kind:'specification'});
}
for(const {p,profile,kind} of files){const own=path.join(base,profile),spec=specificationRoot(root,project,profile),file=slash(path.relative(root,p));
 if(!/\.(csproj|vbproj|slnx|md|py|mjs|cjs|js|ps1|sql|rpgle|sqlrpgle|cob|cpy|c|h|ts|vue|json|bas|cls|frm|txt|html|css)$/i.test(p))continue;
 const text=fs.readFileSync(p,'utf8');
 if(/\.(csproj|vbproj|slnx)$/i.test(p))for(const m of text.matchAll(/<(ProjectReference|Compile|Content|None|Project)\b[^>]*?(?:Include|Path)="([^"*;]+)"/g)){if(m[2].includes('$('))continue;const dest=path.resolve(path.dirname(p),m[2].replaceAll('\\','/'));if(!within(dest,own))findings.push({file,code:'PROJECT_REFERENCE_OUTSIDE',reference:m[2]});else if(!fs.existsSync(dest)&&m[1]==='ProjectReference')findings.push({file,code:'PROJECT_REFERENCE_MISSING',reference:m[2]});checks.push({file,kind:'project-reference',reference:m[2]});}
 if(file.endsWith('.md'))for(const m of text.matchAll(/!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g)){
  const href=m[1];if(/^[a-z][a-z\d+.-]*:/i.test(href)||href.startsWith('#'))continue;
  let dest;try{dest=path.resolve(path.dirname(p),decodeURIComponent(href.split('#')[0]));}
  catch{findings.push({file,code:'DOCUMENT_REFERENCE_ENCODING',reference:href});continue;}
  const local=slash(path.relative(root,dest)),insideSpec=within(dest,spec);
  const excluded=(insideSpec&&path.relative(spec,dest).split(path.sep).some(part=>excludedTrees.has(part.toLowerCase())))||
   (within(dest,own)&&path.relative(own,dest).split(path.sep).some(part=>['spec-eval','spec-analysis','.tmp','.git'].includes(part.toLowerCase())));
  const guide=kind==='specification'&&!excluded?guideKind(local,profile):null;
  const allowed=!excluded&&(kind==='specification'?insideSpec||guide:within(dest,own)||insideSpec);
  const check={file,kind:'document-reference',reference:href,target:local,referenceClass:guide??(insideSpec?'own-specification-reference':'own-source-reference'),contentReadByReferenceCheck:false,inputPromoted:false};
  if(!allowed)findings.push({file,code:kind==='specification'?'SPECIFICATION_REFERENCE_OUTSIDE':'DOCUMENT_REFERENCE_OUTSIDE',reference:href});
  else try{
   // Existence only. realpath also rejects a linked ancestor; no body reads/hashes.
   const directory=guide==='design-rule-existence'?/\/(rules|workflows)$/.test(local):guide?false:fs.lstatSync(dest).isDirectory();
   assertRegular(dest,directory);
  }catch(error){findings.push({file,code:error.code==='ENOENT'?'DOCUMENT_REFERENCE_MISSING':'DOCUMENT_REFERENCE_NONREGULAR',reference:href});}
  checks.push(check);
 }
 // Scope-check tooling intentionally names prohibited paths in its tests; those are not dependencies.
 if(!/[/\\](?:tests|Tests)[/\\]|(?:static_check|test_host)\./.test(file))for(const other of registered.filter(x=>x!==profile)){const name=other.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const re=new RegExp('(?:\\.\\.[/\\\\]|(?:srcs|spec)[/\\\\])'+name+'[/\\\\]','g');if(re.test(text))findings.push({file,code:'CROSS_PROFILE_PATH',other});}
 if(!/[/\\](?:tests|Tests)[/\\]|(?:static_check|test_host)\./.test(file)&&/(?:\.\.\/|srcs\/)(?:Shared|Database|_tools)\//.test(text))findings.push({file,code:'SHARED_RESOURCE_PATH'});
}
}catch(error){findings.push({code:'INSPECTION_FAILED',detail:error.message});}
const result={projectId:project,profileId:selected??null,runId,recordedAt:new Date().toISOString(),status:findings.length?'FAILED':'PASSED',profiles,files:files.length,references:checks.length,referenceChecks:checks,findings,scope:['local project and source links','specification link closure with exact preflight-aligned guide existence exceptions','shared/cross-profile path absence','no symlinks or redirected reference ancestors'],notChecked:['contents/hashes of existence-only common/design guides and own design reports; no input promotion','external runtime/toolchain availability','dynamic paths beyond the static checks','product UI/rendering/runtime acceptance'],formalScore:null};
writeJson(prefix+'.json',result,outputLayout.scratch);writeLatest(prefix+'.md',`# 独立配置検査 ${runId}\n\n${result.status}。${project}、${profiles.length}方式、${files.length}ファイル、${checks.length}参照。\n\n`+findings.map(f=>`- ${f.file??f.profile??project}: ${f.code} ${f.reference??f.other??f.detail??''}`).join('\n')+'\n\nローカル参照・ProjectReference・独立specの閉鎖・共有元不使用を検査。外部処理系や動的経路全体の保証ではない。\n',outputLayout.scratch);console.log(JSON.stringify(result));process.exitCode=findings.length?1:0;
