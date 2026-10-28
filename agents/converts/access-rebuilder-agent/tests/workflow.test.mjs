import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {safePath,loadRequest,hash,writeJson,begin,complete} from '../src/workflow.mjs';

const agent=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
function fixture(projectId='sample-project1') {
  const root=fs.mkdtempSync(path.join(fs.mkdirSync(path.join(agent,'.tmp/tests'),{recursive:true}) ?? path.join(agent,'.tmp/tests'),'workflow-'));
  const sourceFile=`${projectId}/srcs/Access/build/input.accdb`;
  const source=path.join(root,sourceFile); fs.mkdirSync(path.dirname(source),{recursive:true}); fs.writeFileSync(source,'inert test bytes');
  const rules=path.join(root,'agents/converts/access-rebuilder-agent/docs/変換ルール.md'); fs.mkdirSync(path.dirname(rules),{recursive:true});fs.writeFileSync(rules,'rules');
  const profile={schema:'access-rebuilder-request/0.1',projectId,phase:'implementation',approval:{implementation:'authorized',evidence:'unit fixture',accessExtraction:true,codeGeneration:true,databaseExecution:false},training:{maxIterations:2},source:{file:sourceFile,sha256:hash(source)},target:{profileId:'Access-To-CSharp_ASPNET',sourceRoot:`${projectId}/srcs/Access-To-CSharp_ASPNET`,specRoot:`${projectId}/spec/Access-To-CSharp_ASPNET`}};
  writeJson(path.join(root,'profile.json'),profile);
  return {root,profile};
}
test('unsafe parent and absolute paths are rejected',()=>{ assert.throws(()=>safePath(agent,'../source'));assert.throws(()=>safePath(agent,'C:/Windows')); });
test('sample and legacy project IDs preserve path and request boundaries',()=>{
  for(const projectId of ['sample-project1','test-project1']) {
    const {root,profile}=fixture(projectId);
    assert.equal(loadRequest(root,'profile.json').profile.projectId,projectId);
    for(const invalid of ['../sample-project1','sample-project1/other','sample-project1\\other','D:/sample-project1']) {
      writeJson(path.join(root,'profile.json'),{...profile,projectId:invalid});
      assert.throws(()=>loadRequest(root,'profile.json'),/Unsupported request\/project/);
    }
  }
});
test('grouped CLI finds its repository and default profile outside the working directory',()=>{
  const {root,profile}=fixture();
  const checkout=path.join(root,'agents/converts/access-rebuilder-agent');
  for(const relative of ['scripts/rebuild.mjs','src/workflow.mjs']) {
    const destination=path.join(checkout,relative);
    fs.mkdirSync(path.dirname(destination),{recursive:true});
    fs.copyFileSync(path.join(agent,relative),destination);
  }
  writeJson(path.join(checkout,'profiles/sample-project1.json'),profile);
  const result=spawnSync(process.execPath,[path.join(checkout,'scripts/rebuild.mjs'),'status'],{cwd:path.dirname(root),encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  assert.deepEqual(JSON.parse(result.stdout),{iterations:[],maxIterations:2});
  assert.equal(fs.existsSync(path.join(root,profile.target.sourceRoot)),false);
});
test('changed input and missing authorization are rejected',()=>{
  const {root,profile}=fixture(); profile.approval.evidence=null;writeJson(path.join(root,'profile.json'),profile);assert.throws(()=>loadRequest(root,'profile.json'),/authorized/);
  profile.approval.evidence='fixture';writeJson(path.join(root,'profile.json'),profile);fs.appendFileSync(path.join(root,profile.source.file),'changed');assert.throws(()=>loadRequest(root,'profile.json'),/hash changed/);
});
test('third training iteration cannot begin and nested begin is rejected',()=>{
  const {root,profile}=fixture();const context=loadRequest(root,'profile.json');
  for(let iteration=1;iteration<=2;iteration++) { begin(context);assert.throws(()=>begin(context),/already running/);const relative=`${profile.target.sourceRoot}/build/test-results/current.json`;writeJson(path.join(root,relative),{sourceHash:profile.source.sha256,iteration,checks:[],findings:[]});complete(context,relative); }
  assert.throws(()=>begin(context),/limit reached/);
});
test('mismatched results and unselected DB execution are rejected',()=>{
  const {root,profile}=fixture();const context=loadRequest(root,'profile.json');begin(context);const relative=`${profile.target.sourceRoot}/build/test-results/current.json`;writeJson(path.join(root,relative),{sourceHash:'wrong',iteration:1,checks:[],findings:[]});assert.throws(()=>complete(context,relative),/does not match/);
  profile.approval.databaseExecution=true;writeJson(path.join(root,'profile.json'),profile);assert.throws(()=>loadRequest(root,'profile.json'),/dedicated connection/);
});
