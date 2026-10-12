// AG-BUILD: record current generated files after checking the frozen input hashes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const args=process.argv.slice(2);let project,runId;
for(let i=0;i<args.length;i+=2) {
  if(args[i]==='--project'&&!project) project=args[i+1];
  else if(args[i]==='--run-id'&&!runId) runId=args[i+1];
  else throw new Error('Usage: manifest.mjs --project test-projectN --run-id <preflight-id>');
}
if(!/^test-project[1-9]\d*$/.test(project??'')||!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(runId??'')) throw new Error('Explicit safe project/run-id required.');
const report=path.join(root,project,'report');
const output=path.join(report,`${runId}-outputs.json`);
if(fs.existsSync(output)) throw new Error('Output manifest already exists; use a new run-id.');
const input=JSON.parse(fs.readFileSync(path.join(report,`${runId}-inputs.json`),'utf8'));
const structure=JSON.parse(fs.readFileSync(path.join(report,`${runId}-structure.json`),'utf8'));
if(input.projectId!==project||input.runId!==runId||structure.status!=='structure-check-passed') throw new Error('Matching successful preflight required.');
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
for(const record of input.files) if(hash(fs.readFileSync(path.join(root,record.file)))!==record.sha256) throw new Error(`Input changed after preflight: ${record.file}`);
const excluded=new Set(['bin','obj','node_modules','dist','build','.git']);
const files=[];
function walk(directory) {
  const info=fs.lstatSync(directory);if(!info.isDirectory()||info.isSymbolicLink()) throw new Error('Regular output directory required.');
  for(const entry of fs.readdirSync(directory,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name,'en'))) {
    const target=path.join(directory,entry.name);
    if(entry.isSymbolicLink()) throw new Error(`Symlink output refused: ${target}`);
    if(entry.isDirectory()) {if(!excluded.has(entry.name)) walk(target);continue;}
    if(/\.(accdb|laccdb|accde|o|so|dll|exe|pdb)$/i.test(entry.name)||entry.name==='.env'||entry.name==='appsettings.Local.json') continue;
    if(!entry.isFile()) throw new Error(`Non-regular output refused: ${target}`);
    const data=fs.readFileSync(target);files.push({file:path.relative(root,target).split(path.sep).join('/'),bytes:data.length,sha256:hash(data)});
  }
}
walk(path.join(root,'agents/build-agent'));walk(path.join(root,project,'srcs'));
const changed=execFileSync('git',['diff','--name-only','-z','--','agents/build-agent',project],{cwd:root}).toString('utf8').split('\0').filter(Boolean);
const documentChanges=[];
for(const file of changed.filter(file=>file.endsWith('.md'))) {
  const before=execFileSync('git',['show',`${input.inputCommit}:${file}`],{cwd:root});
  const after=fs.readFileSync(path.join(root,file));
  const version=data=>JSON.parse(data.toString('utf8').match(/<!-- spec-meta: (.*?) -->/)?.[1]??'{}').version??null;
  documentChanges.push({file,beforeVersion:version(before),afterVersion:version(after),beforeSha256:hash(before),afterSha256:hash(after)});
}
const result={projectId:project,runId,inputCommit:input.inputCommit,recordedAt:new Date().toISOString(),outputVersion:runId,inputManifest:`${runId}-inputs.json`,structureReport:`${runId}-structure.json`,sourceOnly:true,excluded:['bin/obj/node_modules/dist/build','compiled binaries','local secrets/configuration'],documentChanges,files};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({projectId:project,runId,files:files.length,documentChanges:documentChanges.length,inputHashesVerified:true,output:path.relative(root,output).split(path.sep).join('/')}));
