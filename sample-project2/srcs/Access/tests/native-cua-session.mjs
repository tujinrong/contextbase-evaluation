// Native test evidence only. Each call performs one Sky input and immediately
// refreshes its state. The operator must inspect that state before the next call.
// No expected UI values or application generation definitions are stored here.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const safeName = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(value);
export function createNativeEvidenceSession({sky, sourceRoot, runId, artifact, ownerCopy, contractSha256}) {
  if (!sky || !safeName(runId)) throw new Error('An initialized Sky client and safe run id are required.');
  const owner = path.resolve(sourceRoot);
  const destination = path.join(owner, 'build/test-results/native-ui');
  fs.mkdirSync(destination, {recursive:true});
  if (fs.realpathSync(destination).toLowerCase() !== destination.toLowerCase()) throw new Error('Evidence destination is redirected.');
  const local = name => {
    if (typeof name !== 'string' || path.isAbsolute(name) || name.split(/[\\/]/).some(p => p === '..')) throw new Error('Owned relative path required.');
    const file = path.resolve(owner,name);
    if (!file.toLowerCase().startsWith(owner.toLowerCase()+path.sep)) throw new Error('Outside source root.');
    return file;
  };
  const fileRecord = file => {
    const stat=fs.lstatSync(file);
    if (!stat.isFile() || stat.isSymbolicLink() || fs.realpathSync(file).toLowerCase()!==file.toLowerCase()) throw new Error('Regular unredirected evidence file required.');
    const bytes=fs.readFileSync(file);
    return {file:path.relative(owner,file).split(path.sep).join('/'),bytes:bytes.length,sha256:digest(bytes)};
  };
  const artifactRecord=fileRecord(local(artifact.file));
  if (artifact.sha256 && artifactRecord.sha256!==artifact.sha256) throw new Error('Product changed before the UI session.');
  const copyPath=local(ownerCopy.file);
  const copyRecord=fileRecord(copyPath);
  const driverAtStart=fileRecord(local('tests/native-cua-session.mjs'));
  const log={schemaVersion:1,projectId:'sample-project2',profileId:'Access',runId,
    startedAt:new Date().toISOString(),artifact:artifactRecord,
    ownerCopy:{...copyRecord,initialCopySha256:ownerCopy.initialCopySha256??null},
    contractSha256,measurementSources:[driverAtStart],
    scope:'Native Sky observations and individual inputs; no product acceptance or unobserved behavior inferred',
    formalScore:null,steps:[],cases:[]};
  let state=null, activeCase=null;
  const requireUnchangedDriver=()=>{
    if (fileRecord(local('tests/native-cua-session.mjs')).sha256!==driverAtStart.sha256) throw new Error('Measurement driver changed; restart this UI session and recollect its evidence.');
  };
  const summary = value => value ? {window:value.window,focusedElement:value.accessibility?.focused_element??null,
    selectedElements:value.accessibility?.selected_elements??[],screenshotIds:(value.screenshots??[]).map(s=>s.id)} : null;
  const save=()=>{
    requireUnchangedDriver();
    fs.writeFileSync(path.join(destination,'operations.json'),JSON.stringify(log,null,2)+'\n');
  };
  async function observe(window,{screenshot=true,text=true}={}) {
    requireUnchangedDriver();
    state=await sky.get_window_state({window,include_screenshot:screenshot,include_text:text});
    return {summary:summary(state),tree:state.accessibility?.tree??state.accessibility?.document_text??''};
  }
  async function act(kind,parameters={}) {
    requireUnchangedDriver();
    const previous=state;
    if (!previous) throw new Error('Observe and inspect the target before acting.');
    const {window}=previous;
    const before=summary(previous);
    let args={window};
    if (kind==='click') {
      if (Number.isInteger(parameters.element_index)) {
        if (!previous.accessibility) throw new Error('A fresh accessibility tree is required.');
        args.element_index=parameters.element_index;
      } else {
        const shot=previous.screenshots?.[parameters.screenshotIndex??0];
        if (!shot || !Number.isFinite(parameters.x) || !Number.isFinite(parameters.y)) throw new Error('A fresh screenshot and observed point are required.');
        args={...args,screenshotId:shot.id,x:parameters.x,y:parameters.y};
      }
      if (parameters.click_count!==undefined) args.click_count=parameters.click_count;
    } else if (kind==='key') {
      if (typeof parameters.key!=='string' || !parameters.key) throw new Error('An explicit key is required.');
      args.key=parameters.key;
    } else if (kind==='text') {
      if (!before.focusedElement && parameters.focusConfirmedBy!=='current-screenshot') throw new Error('Observe and confirm focus before text entry.');
      if (typeof parameters.text!=='string') throw new Error('Literal text required.');
      args.text=parameters.text;
    } else if (kind==='scroll') {
      const shot=previous.screenshots?.[parameters.screenshotIndex??0];
      if (!shot || !['x','y','scrollX','scrollY'].every(k=>Number.isFinite(parameters[k]))) throw new Error('Fresh screenshot and explicit scroll coordinates/deltas required.');
      args={...args,screenshotId:shot.id,x:parameters.x,y:parameters.y,scrollX:parameters.scrollX,scrollY:parameters.scrollY};
    } else throw new Error('Supported individual inputs: click, key, text, scroll.');
    state=null;
    const step={id:log.steps.length+1,at:new Date().toISOString(),caseId:activeCase?.id??null,kind,parameters,before};
    try {
      if (kind==='click') await sky.click(args);
      else if (kind==='key') await sky.press_key(args);
      else if (kind==='text') await sky.type_text(args);
      else await sky.scroll(args);
      state=await sky.get_window_state({window,include_screenshot:true,include_text:true});
      step.after=summary(state);step.status='INPUT_AND_REFRESH_COMPLETED';
      log.steps.push(step);save();
      return {summary:step.after,tree:state.accessibility?.tree??state.accessibility?.document_text??''};
    } catch(error) {
      step.status='OUTCOME_UNKNOWN_REOBSERVE_REQUIRED';step.error=String(error?.message??error);
      log.steps.push(step);save();throw error;
    }
  }
  function beginCase({id,ruleIds=[],note=''}) {
    if (!safeName(id) || activeCase) throw new Error('A safe unique case id and no unfinished case are required.');
    if (log.cases.some(c=>c.id===id)) throw new Error('Case already recorded.');
    activeCase={id,ruleIds,note,startedAt:new Date().toISOString(),firstStep:log.steps.length+1,before:summary(state)};
    return activeCase.id;
  }
  function finishCase({actual,assessment,notes='',dataReloadEvidence=[]}) {
    if (!activeCase || !state || !['PASS','FAIL','NOT_VERIFIED'].includes(assessment)) throw new Error('An observed active case and explicit assessment are required.');
    const images=[];
    for (const [index,shot] of (state.screenshots??[]).entries()) {
      // Archival evidence of the already displayed observation, never a second
      // image emission or decoding for inspection.
      const match=/^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=\r\n]+)$/.exec(shot.url);
      if (!match) throw new Error('Expected a supported screenshot image data URL.');
      const extension=match[1]==='jpeg'?'jpg':match[1];
      const file=path.join(destination,`${activeCase.id}-${index}.${extension}`);
      fs.writeFileSync(file,Buffer.from(match[2],'base64'));
      images.push({...fileRecord(file),screenshotId:shot.id,width:shot.width,height:shot.height,originX:shot.originX,originY:shot.originY,zIndex:shot.zIndex});
    }
    const value={...activeCase,finishedAt:new Date().toISOString(),lastStep:log.steps.length,
      after:summary(state),actual,assessment,notes,dataReloadEvidence,images};
    const caseFile=path.join(destination,`${activeCase.id}.json`);
    fs.writeFileSync(caseFile,JSON.stringify(value,null,2)+'\n');
    log.cases.push({...value,evidence:fileRecord(caseFile)});activeCase=null;save();
    return {id:value.id,assessment,images:images.map(i=>i.file),evidence:path.relative(owner,caseFile).split(path.sep).join('/')};
  }
  save();
  return {observe,act,beginCase,finishCase,focus:()=>summary(state),tree:()=>state?.accessibility?.tree??'',
    currentWindow:()=>state?.window??null,report:()=>structuredClone(log)};
}
