import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {layout,writeLatest,writeJson} from './output-layout.mjs';
import {sourceFiles} from './source-files.mjs';
import {specificationRoot} from './input-scope.mjs';
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
try{
for(const profile of profiles){
 const directory=path.join(base,profile),spec=specificationRoot(root,project,profile);
 if(!fs.existsSync(path.join(spec,'README.md')))findings.push({profile,code:'MISSING_OWN_SPEC'});
 for(const p of sourceFiles(directory,{excludeSpec:true}))files.push({p,profile,kind:'source'});
 if(fs.existsSync(spec))for(const p of sourceFiles(spec))files.push({p,profile,kind:'specification'});
}
for(const {p,profile,kind} of files){const own=path.join(base,profile),spec=specificationRoot(root,project,profile),file=slash(path.relative(root,p));
 if(!/\.(csproj|vbproj|slnx|md|py|mjs|cjs|js|ps1|sql|rpgle|sqlrpgle|cob|cpy|c|h|ts|vue|json|bas|cls|frm|txt|html|css)$/i.test(p))continue;
 const text=fs.readFileSync(p,'utf8');
 if(/\.(csproj|vbproj|slnx)$/i.test(p))for(const m of text.matchAll(/<(ProjectReference|Compile|Content|None|Project)\b[^>]*?(?:Include|Path)="([^"*;]+)"/g)){if(m[2].includes('$('))continue;const dest=path.resolve(path.dirname(p),m[2].replaceAll('\\','/'));if(!within(dest,own))findings.push({file,code:'PROJECT_REFERENCE_OUTSIDE',reference:m[2]});else if(!fs.existsSync(dest)&&m[1]==='ProjectReference')findings.push({file,code:'PROJECT_REFERENCE_MISSING',reference:m[2]});checks.push({file,kind:'project-reference',reference:m[2]});}
 if(file.endsWith('.md'))for(const m of text.matchAll(/!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g)){if(/^[a-z][a-z\d+.-]*:/i.test(m[1])||m[1].startsWith('#'))continue;const dest=path.resolve(path.dirname(p),decodeURIComponent(m[1].split('#')[0]));const allowed=kind==='specification'?within(dest,spec):within(dest,own)||within(dest,spec);if(!allowed)findings.push({file,code:kind==='specification'?'SPECIFICATION_REFERENCE_OUTSIDE':'DOCUMENT_REFERENCE_OUTSIDE',reference:m[1]});else if(!fs.existsSync(dest))findings.push({file,code:'DOCUMENT_REFERENCE_MISSING',reference:m[1]});checks.push({file,kind:'document-reference',reference:m[1]});}
 // Scope-check tooling intentionally names prohibited paths in its tests; those are not dependencies.
 if(!/[/\\](?:tests|Tests)[/\\]|(?:static_check|test_host)\./.test(file))for(const other of registered.filter(x=>x!==profile)){const name=other.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const re=new RegExp('(?:\\.\\.[/\\\\]|(?:srcs|spec)[/\\\\])'+name+'[/\\\\]','g');if(re.test(text))findings.push({file,code:'CROSS_PROFILE_PATH',other});}
 if(!/[/\\](?:tests|Tests)[/\\]|(?:static_check|test_host)\./.test(file)&&/(?:\.\.\/|srcs\/)(?:Shared|Database|_tools)\//.test(text))findings.push({file,code:'SHARED_RESOURCE_PATH'});
}
}catch(error){findings.push({code:'INSPECTION_FAILED',detail:error.message});}
const result={projectId:project,profileId:selected??null,runId,recordedAt:new Date().toISOString(),status:findings.length?'FAILED':'PASSED',profiles,files:files.length,references:checks.length,findings,scope:['local project and source links','specification link closure','shared/cross-profile path absence','no symlinks'],notChecked:['external runtime/toolchain availability','dynamic paths beyond the static checks'],formalScore:null};
writeJson(prefix+'.json',result,outputLayout.scratch);writeLatest(prefix+'.md',`# 独立配置検査 ${runId}\n\n${result.status}。${project}、${profiles.length}方式、${files.length}ファイル、${checks.length}参照。\n\n`+findings.map(f=>`- ${f.file??f.profile??project}: ${f.code} ${f.reference??f.other??f.detail??''}`).join('\n')+'\n\nローカル参照・ProjectReference・独立specの閉鎖・共有元不使用を検査。外部処理系や動的経路全体の保証ではない。\n',outputLayout.scratch);console.log(JSON.stringify(result));process.exitCode=findings.length?1:0;
