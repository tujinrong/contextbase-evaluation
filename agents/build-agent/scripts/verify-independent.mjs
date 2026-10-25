// Current results replace fixed build paths; all work remains method-local.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
import {layout,writeLatest,writeJson} from './output-layout.mjs';
import {sourceFiles} from './source-files.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const runId=process.argv[2],profiles=process.argv.slice(3);const valid=['CSharp_ASPNET','Vue_CSharpAPI','CSharp_WPF','VB.NET_WinForms'];
if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(runId??'')||!profiles.length||profiles.some(p=>!valid.includes(p))||new Set(profiles).size!==profiles.length)throw new Error('Unique run ID and selected independent profiles required.');
const outputLayout=layout(root,'test-project1');const prefix=path.join(outputLayout.tests,'independent');
const results=[],inputs=[];let raw='';
function command(profile,tool,args,relative='.'){
 const cwd=path.join(root,'test-project1/srcs',profile,relative),start=new Date().toISOString();
 const result=spawnSync(tool,args,{cwd,encoding:'utf8',timeout:180000,shell:tool==='npm.cmd',env:{...process.env,PYTHONUTF8:'1'}});
 const output=(result.stdout??'')+(result.stderr??'');const status=result.status!==0?'FAILED':/^SKIP /m.test(output)||/"status"\s*:\s*"SKIP"/.test(output)?'SKIPPED':'PASSED';
 results.push({profile,cwd:path.relative(root,cwd).split(path.sep).join('/'),tool,arguments:args,startedAt:start,exitCode:result.status,status,error:result.error?.message??null,summary:output.split(/\r?\n/).filter(s=>/PASS|SKIP|passed|assertions|警告|エラー|succeeded|error|vulnerabilities/i.test(s)).join(' | ')});
 raw+=`[${profile}] ${tool} ${args.join(' ')}\n${output}\n`;console.log(JSON.stringify(results.at(-1)));
}
function snapshot(dir,profile){for(const p of sourceFiles(dir,{excludeSpec:true})){if(/\.(accdb|laccdb|dll|exe|pdb|pyc)$/i.test(p))continue;const data=fs.readFileSync(p);inputs.push({profile,file:path.relative(root,p).split(path.sep).join('/'),sha256:crypto.createHash('sha256').update(data).digest('hex')});}}
for(const profile of profiles){
 snapshot(path.join(root,'test-project1/srcs',profile),profile);
 command(profile,'dotnet',['--version']);
 command(profile,'dotnet',['build',profile==='VB.NET_WinForms'?'StudentManagement.WinForms.slnx':'StudentManagement.slnx','-c','Release','--nologo','-p:RestoreLockedMode=true']);
 const vb=profile==='VB.NET_WinForms';
 const core='tests/Core/StudentManagement.Core.Tests.csproj';
 const contract={CSharp_ASPNET:'tests/WebContracts.csproj',Vue_CSharpAPI:'tests/ApiContracts.csproj',CSharp_WPF:'tests/Smoke/NativeSmoke.csproj','VB.NET_WinForms':'Tests/StudentManagement.WinForms.Tests.vbproj'}[profile];
 if(!vb)command(profile,'dotnet',['run','--project',core,'-c','Release','--no-launch-profile']);
 command(profile,'dotnet',['run','--project',contract,'-c','Release','--no-launch-profile']);
 command(profile,'dotnet',['run','--project',vb?'database/tests/SqlServer.IntegrationTests.vbproj':'database/tests/SqlServer.IntegrationTests.csproj','-c','Release','--no-launch-profile']);
 if(profile==='Vue_CSharpAPI'){command(profile,'npm.cmd',['run','build'],'frontend');command(profile,'npm.cmd',['audit','--json'],'frontend');}
}
writeLatest(prefix+'.raw.log',raw,outputLayout.scratch);const record={runId,recordedAt:new Date().toISOString(),status:results.some(r=>r.status==='FAILED')?'FAILED':'PASSED-WITH-SKIPS',profiles,scope:'independent folder builds and tests; SQL tests require explicit fixture',inputs,results,notExecuted:['SQL Server actual integration when skipped','production identity integration','visible desktop acceptance','reverse generation/scoring']};writeJson(prefix+'.json',record,outputLayout.scratch);
for(const profile of profiles){const own=layout(root,'test-project1',profile);writeJson(path.join(own.tests,'independent.json'),{...record,profiles:[profile],inputs:inputs.filter(i=>i.profile===profile),results:results.filter(r=>r.profile===profile)},own.scratch);}
process.exitCode=results.some(r=>r.status==='FAILED')?1:0;
