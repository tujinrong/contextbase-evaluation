// Fresh tooling/frontend tests. LocalDB probe is read-only and never starts an instance.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const runId=process.argv[2];
if(!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(runId??'')) throw new Error('Unique run ID required.');
const directory=path.join(root,'test-project1/test-report');fs.mkdirSync(directory,{recursive:true});
const json=path.join(directory,runId+'-tools.json'),log=path.join(directory,runId+'-tools.log');
if(fs.existsSync(json)||fs.existsSync(log)) throw new Error('Reports already exist.');
const specs=[
 {tool:'node',args:['agents/build-agent/scripts/preflight-tests.mjs'],cwd:root,scope:'9 isolated preflight assertions'},
 {tool:process.env.ComSpec??'cmd.exe',args:['/d','/s','/c','npm run build'],cwd:path.join(root,'test-project1/srcs/Vue_CSharpAPI/frontend'),scope:'Vue TypeScript and production bundle'},
 {tool:process.env.ComSpec??'cmd.exe',args:['/d','/s','/c','npm audit --json'],cwd:path.join(root,'test-project1/srcs/Vue_CSharpAPI/frontend'),scope:'current locked npm dependencies'}
];
const results=[];let output='';
for(const spec of specs){
 const startedAt=new Date().toISOString();const actual=spawnSync(spec.tool,spec.args,{cwd:spec.cwd,encoding:'utf8',timeout:180000});
 output+=`$ ${spec.tool} ${spec.args.join(' ')}\n${actual.stdout??''}${actual.stderr??''}\n`;
 results.push({scope:spec.scope,tool:spec.tool,arguments:spec.args,startedAt,exitCode:actual.status,error:actual.error?.message??null});
 console.log(JSON.stringify({scope:spec.scope,exitCode:actual.status}));
}
const probes=[];
for(const args of [['versions'],['info','MSSQLLocalDB']]){
 const actual=spawnSync('sqllocaldb',args,{cwd:root,timeout:15000});
 const decode=buffer=>buffer?new TextDecoder('shift-jis').decode(buffer):'';
 const text=decode(actual.stdout)+decode(actual.stderr);
 probes.push({command:['sqllocaldb',...args],exitCode:actual.status,error:actual.error?.message??null,output:text});
 output+=`$ sqllocaldb ${args.join(' ')} (read-only capability probe)\n${text}\n`;
}
const result={runId,recordedAt:new Date().toISOString(),nodeVersion:process.version,inputManifest:'../report/'+runId+'-inputs.json',results,readOnlyEnvironmentProbes:probes,notExecuted:['SQL Server database or LocalDB startup','real browser E2E','reverse generation/scoring']};
fs.writeFileSync(log,output,{flag:'wx'});fs.writeFileSync(json,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
process.exitCode=results.every(r=>r.exitCode===0)?0:1;
