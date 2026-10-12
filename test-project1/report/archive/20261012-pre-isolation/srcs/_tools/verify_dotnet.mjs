// Local compiler / isolated contract tests only. Never applies DDL or starts a business DB.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const runId=process.argv[2];if(!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(runId??'')) throw new Error('Pass a unique report run-id.');
const reportName=process.argv[3]??'test-report';
if(!['report','test-report'].includes(reportName)) throw new Error('Report directory must be report or test-report.');
const report=path.join(root,'test-project1',reportName);
fs.mkdirSync(report,{recursive:true});
const json=path.join(report,`${runId}-verification.json`),log=path.join(report,`${runId}-verification.log`);
if(fs.existsSync(json)||fs.existsSync(log)) throw new Error('Verification report already exists.');
const base='test-project1/srcs/';
const commands=[
 ['build',base+'Shared/StudentMaintenance/StudentMaintenance.csproj'],
 ['build',base+'VB.NET_WinForms/StudentManagement.WinForms.vbproj'],
 ['build',base+'CSharp_WPF/StudentManagement.Wpf.csproj'],
 ['build',base+'CSharp_ASPNET/StudentManagement.Web.csproj'],
 ['build',base+'Vue_CSharpAPI/backend/StudentManagement.Api.csproj'],
 ['run','--project',base+'Shared/StudentManagement.Core.Tests/StudentManagement.Core.Tests.csproj'],
 ['run','--project',base+'VB.NET_WinForms/Tests/NativeSmoke.csproj'],
 ['run','--project',base+'CSharp_ASPNET/tests/WebContracts.csproj']
];
const results=[];let output='';
for(const command of commands) {
 const args=[...command,'-c','Release',...(command[0]==='build'?['--nologo']:[])];
 const start=new Date().toISOString();const result=spawnSync('dotnet',args,{cwd:root,encoding:'utf8',timeout:180000});
 const details=(result.stdout??'')+(result.stderr??'');output+=`$ dotnet ${args.join(' ')}\n${details}\n`;
 results.push({tool:'dotnet',arguments:args,startedAt:start,exitCode:result.status,error:result.error?.message??null});
 console.log(JSON.stringify({command:args.join(' '),exitCode:result.status,summary:details.split(/\r?\n/).filter(line=>/PASS|passed|assertions|エラー|警告|succeeded|error/i.test(line)).join(' | ')}));
}
fs.writeFileSync(log,output,{flag:'wx'});
fs.writeFileSync(json,JSON.stringify({runId,recordedAt:new Date().toISOString(),scope:['.NET compilation','isolated core boundaries','native view-model smoke without windows','HTTPS web contracts with fake DB'],notExecuted:['SQL Server DDL/DML','real student data','DB concurrency','Windows UI acceptance','reverse generation/scoring'],results},null,2)+'\n',{flag:'wx'});
process.exitCode=results.every(result=>result.exitCode===0)?0:1;
