import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {safePath,loadRequest,hash,writeJson,begin,complete} from '../src/workflow.mjs';

const agent=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
function fixture() {
  const root=fs.mkdtempSync(path.join(fs.mkdirSync(path.join(agent,'.tmp/tests'),{recursive:true}) ?? path.join(agent,'.tmp/tests'),'workflow-'));
  const source=path.join(root,'test-project1/srcs/Access/build/input.accdb'); fs.mkdirSync(path.dirname(source),{recursive:true}); fs.writeFileSync(source,'inert test bytes');
  const rules=path.join(root,'agents/access-rebuilder-agent/docs/変換ルール.md'); fs.mkdirSync(path.dirname(rules),{recursive:true});fs.writeFileSync(rules,'rules');
  const profile={schema:'access-rebuilder-request/0.1',projectId:'test-project1',phase:'implementation',approval:{implementation:'authorized',evidence:'unit fixture',accessExtraction:true,codeGeneration:true,databaseExecution:false},training:{maxIterations:2},source:{file:'test-project1/srcs/Access/build/input.accdb',sha256:hash(source)},target:{profileId:'Access-CSharp_ASPNET',sourceRoot:'test-project1/srcs/Access-CSharp_ASPNET',specRoot:'test-project1/spec/Access-CSharp_ASPNET'}};
  writeJson(path.join(root,'profile.json'),profile);
  return {root,profile};
}
test('unsafe parent and absolute paths are rejected',()=>{ assert.throws(()=>safePath(agent,'../source'));assert.throws(()=>safePath(agent,'C:/Windows')); });
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
