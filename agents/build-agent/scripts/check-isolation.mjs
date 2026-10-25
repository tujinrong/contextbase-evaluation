import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {layout,writeLatest,writeJson} from './output-layout.mjs';
import {sourceFiles} from './source-files.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');const base=path.join(root,'test-project1/srcs');
const profiles=['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access'];
const runId=process.argv[2];if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(runId??''))throw new Error('Fresh run ID required.');
const outputLayout=layout(root,'test-project1');const prefix=path.join(outputLayout.tests,'isolation');
const findings=[],checks=[],files=[];
const slash=p=>p.split(path.sep).join('/');const within=(p,base)=>p===base||p.startsWith(base+path.sep);
for(const profile of profiles){const directory=path.join(base,profile);if(!fs.existsSync(path.join(directory,'spec/README.md')))findings.push({profile,code:'MISSING_OWN_SPEC'});for(const p of sourceFiles(directory))files.push({p,profile});}
for(const {p,profile} of files){const own=path.join(base,profile),file=slash(path.relative(root,p));
 if(!/\.(csproj|vbproj|slnx|md|py|mjs|ps1|sql|rpgle|sqlrpgle|cob|cpy|c|h|ts|vue|json)$/i.test(p))continue;
 const text=fs.readFileSync(p,'utf8');
 if(/\.(csproj|vbproj|slnx)$/i.test(p))for(const m of text.matchAll(/<(ProjectReference|Compile|Content|None|Project)\b[^>]*?(?:Include|Path)="([^"*;]+)"/g)){if(m[2].includes('$('))continue;const dest=path.resolve(path.dirname(p),m[2].replaceAll('\\','/'));if(!within(dest,own))findings.push({file,code:'PROJECT_REFERENCE_OUTSIDE',reference:m[2]});else if(!fs.existsSync(dest)&&m[1]==='ProjectReference')findings.push({file,code:'PROJECT_REFERENCE_MISSING',reference:m[2]});checks.push({file,kind:'project-reference',reference:m[2]});}
 if(file.endsWith('.md'))for(const m of text.matchAll(/!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g)){if(/^[a-z][a-z\d+.-]*:/i.test(m[1])||m[1].startsWith('#'))continue;const dest=path.resolve(path.dirname(p),decodeURIComponent(m[1].split('#')[0]));if(!within(dest,own))findings.push({file,code:'DOCUMENT_REFERENCE_OUTSIDE',reference:m[1]});else if(!fs.existsSync(dest))findings.push({file,code:'DOCUMENT_REFERENCE_MISSING',reference:m[1]});checks.push({file,kind:'document-reference',reference:m[1]});}
 // Scope-check tooling intentionally names prohibited paths in its tests; those are not dependencies.
 if(!/[/\\](?:tests|Tests)[/\\]|(?:static_check|test_host)\./.test(file))for(const other of profiles.filter(x=>x!==profile)){const name=other.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const re=new RegExp('(?:\\.\\.[/\\\\]|srcs[/\\\\])'+name+'[/\\\\]','g');if(re.test(text))findings.push({file,code:'CROSS_PROFILE_PATH',other});}
 if(!/[/\\](?:tests|Tests)[/\\]|(?:static_check|test_host)\./.test(file)&&/(?:\.\.\/|srcs\/)(?:Shared|Database|_tools)\//.test(text))findings.push({file,code:'SHARED_RESOURCE_PATH'});
}
const result={runId,recordedAt:new Date().toISOString(),status:findings.length?'FAILED':'PASSED',profiles,files:files.length,references:checks.length,findings,scope:['local project and source links','specification link closure','shared/cross-profile path absence','no symlinks'],notChecked:['external runtime/toolchain availability','dynamic paths beyond the static checks']};
fs.mkdirSync(path.dirname(prefix),{recursive:true});writeJson(prefix+'.json',result,outputLayout.scratch);writeLatest(prefix+'.md',`# 独立配置検査 ${runId}\n\n${result.status}。7方式、${files.length}ファイル、${checks.length}参照。\n\n`+findings.map(f=>`- ${f.file??f.profile}: ${f.code} ${f.reference??f.other??''}`).join('\n')+'\n\nローカル参照・ProjectReference・独立specの閉鎖・共有元不使用を検査。外部処理系や動的経路全体の保証ではない。\n',outputLayout.scratch);console.log(JSON.stringify(result));process.exitCode=findings.length?1:0;
