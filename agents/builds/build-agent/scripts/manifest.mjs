// AG-BUILD: record current generated files after checking the frozen input hashes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {execFileSync,spawnSync} from 'node:child_process';
import {layout, writeJson} from './output-layout.mjs';
import {assertRegular, collectInputFiles} from './input-scope.mjs';
import {selectedProfiles, validProfile} from './project-scope.mjs';
import {uiPolicyForProfile,requireCurrentUIResult} from './ui-conformance.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const args=process.argv.slice(2);let project,runId,profile;
if(args.length%2)throw new Error('Every option requires a value.');
for(let i=0;i<args.length;i+=2) {
  if(args[i]==='--project'&&!project) project=args[i+1];
  else if(args[i]==='--run-id'&&!runId) runId=args[i+1];
  else if(args[i]==='--profile'&&!profile) profile=args[i+1];
  else throw new Error('Usage: manifest.mjs --project sample-projectN --run-id <preflight-id> [--profile <profile-id>]');
}
if(!/^(?:sample|test)-project[1-9]\d*$/.test(project??'')||!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(runId??'')||(profile!==undefined&&!validProfile(profile))) throw new Error('Explicit safe project/run-id and supported profile required.');
const methods=selectedProfiles(root,project,profile);
const outputLayout=layout(root,project,profile);
const report=outputLayout.generation;
const output=path.join(report,'outputs.json');
const input=JSON.parse(fs.readFileSync(path.join(report,'inputs.json'),'utf8'));
const structure=JSON.parse(fs.readFileSync(path.join(report,'structure.json'),'utf8'));
const generationStateFile=path.join(report,'regeneration.json');
const generationState=fs.existsSync(generationStateFile)?JSON.parse(fs.readFileSync(generationStateFile,'utf8')):null;
if(generationState&&(generationState.runId!==runId||generationState.profileId!==profile))throw new Error('Generation status must describe the current profile/run.');
if(input.projectId!==project||input.runId!==runId||input.profileId!==profile||structure.runId!==runId||structure.profileId!==profile||structure.status!=='structure-check-passed') throw new Error('Matching successful preflight and profile scope required.');
if(input.inspectionOnly!==false||structure.inspectionOnly!==false||input.specificationLayout!=='project/spec/profile')throw new Error('Current publishing preflight required; inspection-only and legacy layouts are not generation authorization.');
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const currentInputs=collectInputFiles(root,project,profile).map(file=>path.relative(root,file).split(path.sep).join('/')).sort();
if(!Array.isArray(input.files)||JSON.stringify(input.files.map(record=>record.file).sort())!==JSON.stringify(currentInputs))throw new Error('Input file set changed or is outside the selected specification scope.');
for(const record of input.files) {
  const target=path.join(root,record.file);assertRegular(target);
  if(hash(fs.readFileSync(target))!==record.sha256) throw new Error(`Input changed after preflight: ${record.file}`);
}
// This is an independent UI gate, not an inference from structural preflight PASS.
let uiConformance;
try {
 uiConformance=methods.map(method=>{
  const policy=uiPolicyForProfile({root,project,profile:method,requireDeclaration:input.files.some(record=>record.file==='docs/UI適合検査.md'),frozenInputs:input});
  if(!policy.required)return {profileId:method,...policy};
  return {profileId:method,required:true,status:'PASS',record:requireCurrentUIResult({root,project,profile:method,runId})};
 });
} catch(error) {
 if(fs.existsSync(output)){assertRegular(output);fs.unlinkSync(output);}
 throw error;
}
const excluded=new Set(['.tmp','bin','obj','node_modules','dist','build','__pycache__','.vs','.git','spec','spec-eval','spec-analysis','test-report','test-evidence']);
const files=[];
function walk(directory) {
  const info=fs.lstatSync(directory);if(!info.isDirectory()||info.isSymbolicLink()) throw new Error('Regular output directory required.');
  for(const entry of fs.readdirSync(directory,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name,'en'))) {
    const target=path.join(directory,entry.name);
    if(excluded.has(entry.name))continue;
    if(entry.isSymbolicLink()) throw new Error(`Symlink output refused: ${target}`);
    if(entry.isDirectory()) {if(!excluded.has(entry.name)) walk(target);continue;}
    if(/\.(accdb|laccdb|accde|o|so|dll|exe|pdb|pyc|pyo)$/i.test(entry.name)||entry.name==='.env'||entry.name==='appsettings.Local.json') continue;
    if(!entry.isFile()) throw new Error(`Non-regular output refused: ${target}`);
    const data=fs.readFileSync(target);files.push({file:path.relative(root,target).split(path.sep).join('/'),bytes:data.length,sha256:hash(data)});
  }
}
const outputRoots=['agents/builds/build-agent/scripts',...methods.map(method=>`${project}/srcs/${method}`)];
for(const directory of outputRoots)walk(path.join(root,directory));
const changed=execFileSync('git',['diff','--name-only','-z','--',...(profile?outputRoots:['agents/builds/build-agent',project])],{cwd:root}).toString('utf8').split('\0').filter(Boolean);
const documentChanges=[];
const documents=new Set([...changed,...files.map(f=>f.file)].filter(file=>file.endsWith('.md')&&!file.split('/').includes('spec-eval')));
for(const file of [...documents].sort()) {
  const previous=spawnSync('git',['show',`${input.inputCommit}:${file}`],{cwd:root,encoding:null,stdio:['ignore','pipe','ignore']});
  const before=previous.status===0?previous.stdout:null;
  const after=fs.existsSync(path.join(root,file))?fs.readFileSync(path.join(root,file)):null;
  if(before&&after&&hash(before)===hash(after))continue;
  const version=data=>data?JSON.parse(data.toString('utf8').match(/<!-- spec-meta: (.*?) -->/)?.[1]??'{}').version??null:null;
  documentChanges.push({file,status:!before?'created':!after?'archived-or-removed':'modified',beforeVersion:version(before),afterVersion:version(after),beforeSha256:before?hash(before):null,afterSha256:after?hash(after):null});
}
const artifacts=[];
if(methods.includes('Access')){
 const accessBuild=path.join(root,project,'srcs/Access/build');
 const accessFiles=fs.existsSync(accessBuild)?fs.readdirSync(accessBuild).filter(name=>/\.accdb$/i.test(name)):[];
 if(accessFiles.length>1)throw new Error('Access delivery requires exactly one final ACCDB, without assuming its product name.');
 for(const name of accessFiles){const access=path.join(accessBuild,name);assertRegular(access);const data=fs.readFileSync(access);artifacts.push({file:relativeArtifact(access),bytes:data.length,sha256:hash(data),kind:'standalone-access-database'});}
}
function relativeArtifact(target){return path.relative(root,target).split(path.sep).join('/');}
const packagesPath=path.join(report,'source-packages.json');
if(fs.existsSync(packagesPath)){
 const packages=JSON.parse(fs.readFileSync(packagesPath,'utf8'));
 if(packages.projectId!==project||packages.runId!==runId||!packages.sourceOnly||!Array.isArray(packages.packages))throw new Error('Matching project/source-only packages required.');
 const packageMethods=packages.packages.map(pack=>pack.profile);
 if(packageMethods.length!==methods.length||new Set(packageMethods).size!==methods.length||methods.some(method=>!packageMethods.includes(method)))throw new Error('Exactly the registered selected source-only package set required.');
 const selectedPackages=profile?packages.packages.filter(pack=>pack.profile===profile):packages.packages;
 if(profile&&selectedPackages.length!==1)throw new Error('Exactly one source-only package for the selected profile required.');
 for(const pack of selectedPackages){
  if(pack.file!==`${project}/srcs/${pack.profile}/build/source.zip`||!Array.isArray(pack.entries)||!pack.entries.length)throw new Error('Package outside current selected delivery path.');
  for(const entry of pack.entries){if(typeof entry.file!=='string'||entry.file.includes('\\')||entry.file.includes(':')||entry.file.startsWith('/')||entry.file.split('/').some(part=>!part||part==='.'||part==='..'))throw new Error('Unsafe source package entry.');const original=path.join(root,project,'srcs',pack.profile,entry.file);assertRegular(original);if(hash(fs.readFileSync(original))!==entry.sourceSha256)throw new Error(`Source changed after packaging: ${pack.profile}/${entry.file}`);}
  assertRegular(path.join(root,pack.file));const data=fs.readFileSync(path.join(root,pack.file));if(hash(data)!==pack.sha256)throw new Error(`Package hash changed: ${pack.file}`);
  artifacts.push({file:pack.file,bytes:data.length,sha256:hash(data),kind:'independent-source-only-archive',profile:pack.profile});
 }
}
const delivery=[];
const generationFiles=[];
for(const entry of fs.readdirSync(report,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name,'en'))) {
 if(entry.name==='outputs.json')continue;
 if(!entry.isFile()||entry.isSymbolicLink())throw new Error(`Only fixed regular generation records may be published: ${entry.name}`);
 generationFiles.push(relativeArtifact(path.join(report,entry.name)));
}
for(const file of [`${project}/test-report/README.md`,`${project}/agent-input/README.md`,...generationFiles]){
 const target=path.join(root,file);if(fs.existsSync(target)){const data=fs.readFileSync(target);delivery.push({file,bytes:data.length,sha256:hash(data)});}
}
// Final app/test files are delivered separately from the source-only inventory.
function finalFiles(directory) {
 if(!fs.existsSync(directory))return;
 const info=fs.lstatSync(directory);if(!info.isDirectory()||info.isSymbolicLink())throw new Error('Regular final directory required.');
 for(const entry of fs.readdirSync(directory,{withFileTypes:true})){
  // A source archive is current only after its package record/run/source hashes passed.
  if(['.tmp','generation','source.zip'].includes(entry.name))continue;
  const target=path.join(directory,entry.name);
  if(entry.isSymbolicLink())throw new Error(`Linked final artifact refused: ${target}`);
  if(entry.isDirectory()){finalFiles(target);continue;}
  if(!entry.isFile()||entry.name==='.env'||entry.name==='appsettings.Local.json'||/\.laccdb$/i.test(entry.name))continue;
  const file=relativeArtifact(target);if(artifacts.some(a=>a.file===file))continue;
  const data=fs.readFileSync(target);artifacts.push({file,bytes:data.length,sha256:hash(data),kind:'current-build-result'});
 }
}
for(const method of methods)finalFiles(path.join(root,project,'srcs',method,'build'));
const result={projectId:project,...(profile?{profileId:profile}:{}),runId,inputCommit:input.inputCommit,recordedAt:new Date().toISOString(),outputVersion:runId,inputManifest:'inputs.json',structureReport:'structure.json',generationStatus:generationState?.status??'NOT_RECORDED',uiConformance,sourceOnly:true,historyPolicy:'git-only; fixed latest build paths',excluded:['.tmp/bin/obj/node_modules/dist/build/__pycache__/.vs in source inventory','spec-eval','local secrets/configuration',...(profile?['other profiles','build-agent files outside scripts']:[])],artifacts,delivery,documentChanges,files};
writeJson(output,result,outputLayout.scratch);
console.log(JSON.stringify({projectId:project,...(profile?{profileId:profile}:{}),runId,files:files.length,documentChanges:documentChanges.length,inputHashesVerified:true,output:path.relative(root,output).split(path.sep).join('/')}));
