// AG-BUILD: record current generated files after checking the frozen input hashes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {execFileSync,spawnSync} from 'node:child_process';
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
const excluded=new Set(['bin','obj','node_modules','dist','build','__pycache__','.vs','.git']);
const files=[];
function walk(directory) {
  const info=fs.lstatSync(directory);if(!info.isDirectory()||info.isSymbolicLink()) throw new Error('Regular output directory required.');
  for(const entry of fs.readdirSync(directory,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name,'en'))) {
    const target=path.join(directory,entry.name);
    if(entry.isSymbolicLink()) throw new Error(`Symlink output refused: ${target}`);
    if(entry.isDirectory()) {if(!excluded.has(entry.name)) walk(target);continue;}
    if(/\.(accdb|laccdb|accde|o|so|dll|exe|pdb|pyc|pyo)$/i.test(entry.name)||entry.name==='.env'||entry.name==='appsettings.Local.json') continue;
    if(!entry.isFile()) throw new Error(`Non-regular output refused: ${target}`);
    const data=fs.readFileSync(target);files.push({file:path.relative(root,target).split(path.sep).join('/'),bytes:data.length,sha256:hash(data)});
  }
}
walk(path.join(root,'agents/build-agent'));walk(path.join(root,project,'srcs'));
const changed=execFileSync('git',['diff','--name-only','-z','--','agents/build-agent',project],{cwd:root}).toString('utf8').split('\0').filter(Boolean);
const documentChanges=[];
const documents=new Set([...changed,...files.map(f=>f.file)].filter(file=>file.endsWith('.md')));
for(const file of [...documents].sort()) {
  const previous=spawnSync('git',['show',`${input.inputCommit}:${file}`],{cwd:root,encoding:null,stdio:['ignore','pipe','ignore']});
  const before=previous.status===0?previous.stdout:null;
  const after=fs.existsSync(path.join(root,file))?fs.readFileSync(path.join(root,file)):null;
  if(before&&after&&hash(before)===hash(after))continue;
  const version=data=>data?JSON.parse(data.toString('utf8').match(/<!-- spec-meta: (.*?) -->/)?.[1]??'{}').version??null:null;
  documentChanges.push({file,status:!before?'created':!after?'archived-or-removed':'modified',beforeVersion:version(before),afterVersion:version(after),beforeSha256:before?hash(before):null,afterSha256:after?hash(after):null});
}
const artifacts=[];const access=path.join(root,project,'srcs/Access/StudentManagement.accdb');if(fs.existsSync(access)){const data=fs.readFileSync(access);artifacts.push({file:relativeArtifact(access),bytes:data.length,sha256:hash(data),kind:'standalone-access-database'});}
function relativeArtifact(target){return path.relative(root,target).split(path.sep).join('/');}
const packagesPath=path.join(report,`${runId}-source-packages.json`);
if(fs.existsSync(packagesPath)){
 const packages=JSON.parse(fs.readFileSync(packagesPath,'utf8'));
 if(packages.runId!==runId||!packages.sourceOnly||packages.packages.length!==7)throw new Error('Matching seven source-only packages required.');
 for(const pack of packages.packages){
  for(const entry of pack.entries){const original=path.join(root,project,'srcs',pack.profile,entry.file);if(hash(fs.readFileSync(original))!==entry.sourceSha256)throw new Error(`Source changed after packaging: ${pack.profile}/${entry.file}`);}
  const data=fs.readFileSync(path.join(root,pack.file));if(hash(data)!==pack.sha256)throw new Error(`Package hash changed: ${pack.file}`);
  artifacts.push({file:pack.file,bytes:data.length,sha256:hash(data),kind:'independent-source-only-archive',profile:pack.profile});
 }
}
const delivery=[];
for(const file of [`${project}/test-report/README.md`,`${project}/agent-input/README.md`,`${project}/report/${runId}-generation.md`,`${project}/report/${runId}-routing-notes.md`,`${project}/report/${runId}-source-packages.json`]){
 const target=path.join(root,file);if(fs.existsSync(target)){const data=fs.readFileSync(target);delivery.push({file,bytes:data.length,sha256:hash(data)});}
}
const result={projectId:project,runId,inputCommit:input.inputCommit,recordedAt:new Date().toISOString(),outputVersion:runId,inputManifest:`${runId}-inputs.json`,structureReport:`${runId}-structure.json`,sourceOnly:true,excluded:['bin/obj/node_modules/dist/build/__pycache__/.vs','compiled binaries including Python bytecode','local secrets/configuration'],artifacts,delivery,documentChanges,files};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({projectId:project,runId,files:files.length,documentChanges:documentChanges.length,inputHashesVerified:true,output:path.relative(root,output).split(path.sep).join('/')}));
