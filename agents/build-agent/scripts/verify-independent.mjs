// Explicit orchestration writes results to project/test-report; every build runs in its own package.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const runId=process.argv[2],profiles=process.argv.slice(3);const valid=['CSharp_ASPNET','Vue_CSharpAPI','CSharp_WPF','VB.NET_WinForms'];
if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(runId??'')||!profiles.length||profiles.some(p=>!valid.includes(p))||new Set(profiles).size!==profiles.length)throw new Error('Unique run ID and selected independent profiles required.');
const report=path.join(root,'test-project1/test-report'),prefix=path.join(report,runId+'-independent');fs.mkdirSync(report,{recursive:true});
for(const ext of ['.json','.raw.log'])if(fs.existsSync(prefix+ext))throw new Error('Fresh report required.');
const results=[],inputs=[];let raw='';
function command(profile,tool,args,relative='.'){
 const cwd=path.join(root,'test-project1/srcs',profile,relative),start=new Date().toISOString();
 const result=spawnSync(tool,args,{cwd,encoding:'utf8',timeout:180000,shell:tool==='npm.cmd',env:{...process.env,PYTHONUTF8:'1'}});
 const output=(result.stdout??'')+(result.stderr??'');const status=result.status!==0?'FAILED':/^SKIP /m.test(output)||/"status"\s*:\s*"SKIP"/.test(output)?'SKIPPED':'PASSED';
 results.push({profile,cwd:path.relative(root,cwd).split(path.sep).join('/'),tool,arguments:args,startedAt:start,exitCode:result.status,status,error:result.error?.message??null,summary:output.split(/\r?\n/).filter(s=>/PASS|SKIP|passed|assertions|警告|エラー|succeeded|error|vulnerabilities/i.test(s)).join(' | ')});
 raw+=`[${profile}] ${tool} ${args.join(' ')}\n${output}\n`;console.log(JSON.stringify(results.at(-1)));
}
function snapshot(dir,profile){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){if(['bin','obj','build','dist','node_modules','.vs','__pycache__','spec','test-report'].includes(entry.name))continue;const p=path.join(dir,entry.name);if(entry.isSymbolicLink())throw new Error('Symlink refused');if(entry.isDirectory())snapshot(p,profile);else if(entry.isFile()&&!/\.(accdb|laccdb|dll|exe|pdb|pyc)$/i.test(entry.name)){const data=fs.readFileSync(p);inputs.push({profile,file:path.relative(root,p).split(path.sep).join('/'),sha256:crypto.createHash('sha256').update(data).digest('hex')});}}}
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
fs.writeFileSync(prefix+'.raw.log',raw,{flag:'wx'});fs.writeFileSync(prefix+'.json',JSON.stringify({runId,recordedAt:new Date().toISOString(),status:results.some(r=>r.status==='FAILED')?'FAILED':'PASSED-WITH-SKIPS',profiles,scope:'independent folder builds and tests; SQL tests require explicit fixture',inputs,results,notExecuted:['SQL Server actual integration when skipped','production identity integration','visible desktop acceptance','reverse generation/scoring']},null,2)+'\n',{flag:'wx'});
process.exitCode=results.some(r=>r.status==='FAILED')?1:0;
