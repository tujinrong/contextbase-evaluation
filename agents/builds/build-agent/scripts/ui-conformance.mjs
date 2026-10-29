// Compare independently authored UI expectations with observations of the final product.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {selectedProfiles} from './project-scope.mjs';
import {collectInputFiles} from './input-scope.mjs';
import {writeJson} from './output-layout.mjs';

export const UI_SCHEMA_VERSION = 1;
export const UI_VALIDATOR_VERSION = '1.0';
const kinds = new Set(['font', 'dimensions', 'appearance', 'render', 'interaction']);
const methods = {
  font: new Set(['native-property', 'computed-style']),
  dimensions: new Set(['native-property', 'computed-style', 'layout-measurement']),
  appearance: new Set(['native-property', 'computed-style', 'render-review']),
  render: new Set(['render-review', 'layout-measurement']),
  interaction: new Set(['keyboard-operation']),
};
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const isHash = value => typeof value === 'string' && /^[a-fA-F0-9]{64}$/.test(value);
const identifier = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value);
const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);

function regular(target, directory = false) {
  const info = fs.lstatSync(target);
  if (info.isSymbolicLink() || fs.realpathSync(target).toLowerCase() !== path.resolve(target).toLowerCase() ||
      (directory ? !info.isDirectory() : !info.isFile())) throw new Error('Regular path required: ' + target);
  return info;
}
function local(base, relative) {
  if (typeof relative !== 'string' || !relative || relative.includes('\\') || relative.includes(':') ||
      relative.startsWith('/') || relative.split('/').some(part => !part || part === '.' || part === '..')) throw new Error('Safe POSIX relative path required.');
  const target = path.resolve(base, ...relative.split('/'));
  if (!target.startsWith(path.resolve(base) + path.sep)) throw new Error('Path escapes its scope.');
  return target;
}
const read = target => JSON.parse(fs.readFileSync(target,'utf8').replace(/^\uFEFF/,''));
const fileRecord = (root,target) => ({file:path.relative(root,target).split(path.sep).join('/'),sha256:sha(fs.readFileSync(target))});

// Directory digest binds CSS/assets as well as the entry assembly. No timestamps enter it.
export function hashArtifact(target) {
  const info = fs.lstatSync(target);
  if (info.isDirectory()) {
    const entries = [];
    function walk(directory) {
      regular(directory,true);
      for (const entry of fs.readdirSync(directory,{withFileTypes:true}).sort((a,b)=>a.name < b.name ? -1 : a.name > b.name ? 1 : 0)) {
        const child=path.join(directory,entry.name);
        if (entry.isSymbolicLink()) throw new Error('Linked artifact refused.');
        if (entry.isDirectory()) walk(child);
        else {regular(child); const data=fs.readFileSync(child); entries.push({file:path.relative(target,child).split(path.sep).join('/'),bytes:data.length,sha256:sha(data)});}
      }
    }
    walk(target);
    if (!entries.length) throw new Error('Empty artifact directory refused.');
    entries.sort((a,b)=>a.file < b.file ? -1 : a.file > b.file ? 1 : 0);
    return {sha256:sha(Buffer.from(JSON.stringify(entries))),kind:'directory',files:entries.length};
  }
  regular(target);
  return {sha256:sha(fs.readFileSync(target)),kind:'file',files:1};
}

export function uiPolicyForProfile({root,project,profile,requireDeclaration=false,frozenInputs}) {
  const owner=path.join(root,project,'srcs',profile), metadata=path.join(owner,'profile.json');
  const hasContract=fs.existsSync(path.join(owner,'tests/ui-contract.json'));
  const hasObservations=fs.existsSync(path.join(owner,'build/test-results/ui-observations.json'));
  let policy;
  if(fs.existsSync(metadata)) {regular(metadata);policy=read(metadata).uiConformance;}
  if(policy===undefined) {
    if(requireDeclaration || hasContract || hasObservations) throw new Error('Explicit profile.uiConformance declaration required: '+profile);
    return {required:null,status:'LEGACY_NOT_DECLARED'};
  }
  if(!isObject(policy) || typeof policy.required!=='boolean') throw new Error('Invalid profile.uiConformance declaration: '+profile);
  if(policy.required) {
    if(policy.contract!=='tests/ui-contract.json') throw new Error('The mandatory UI contract must use tests/ui-contract.json.');
    return {required:true,contract:policy.contract};
  }
  if(typeof policy.reason!=='string' || !policy.reason.trim() || hasContract || hasObservations ||
     !Array.isArray(policy.sourceFiles) || !policy.sourceFiles.length || !Array.isArray(frozenInputs?.files)) throw new Error('Non-UI exemption requires a reason, frozen specification sources, and no contradictory UI contract/observations.');
  for(const file of policy.sourceFiles) {
    const source=frozenInputs.files.find(entry=>entry.file===file);
    if(!file.startsWith(`${project}/spec/${profile}/`) || !source) throw new Error('Non-UI exemption source is outside the frozen method specification.');
    const target=local(root,file);regular(target);
    if(sha(fs.readFileSync(target))!==source.sha256?.toLowerCase()) throw new Error('Non-UI exemption source changed.');
  }
  return {required:false,status:'NOT_APPLICABLE',reason:policy.reason,sourceFiles:policy.sourceFiles};
}

function expectationValid(value) {
  if (!isObject(value) || !Object.hasOwn(value,'value') || value.value === null || value.value === undefined) return false;
  if (value.op === 'eq') return ['string','number','boolean'].includes(typeof value.value) && (typeof value.value!=='number' || Number.isFinite(value.value));
  if (value.op === 'min' || value.op === 'max') return Number.isFinite(value.value);
  if (value.op === 'range') return Array.isArray(value.value) && value.value.length===2 && value.value.every(Number.isFinite) && value.value[0]<=value.value[1];
  if (value.op === 'oneOf') return Array.isArray(value.value) && value.value.length>0 && value.value.every(item=>item!==null && ['string','number','boolean'].includes(typeof item));
  return false;
}
function compare(expected, actual) {
  if (actual === null || actual === undefined) return false;
  if (expected.op === 'eq') return actual === expected.value;
  if (expected.op === 'oneOf') return expected.value.some(value=>value===actual);
  if (!Number.isFinite(actual)) return false;
  if (expected.op === 'min') return actual>=expected.value;
  if (expected.op === 'max') return actual<=expected.value;
  if (expected.op === 'range') return actual>=expected.value[0] && actual<=expected.value[1];
  return false;
}

export function validateUIConformance({root,project,profile,runId}) {
  const findings=[], checks=[];
  const add=(code,detail)=>findings.push({code,detail});
  const result={schemaVersion:UI_SCHEMA_VERSION,validatorVersion:UI_VALIDATOR_VERSION,projectId:project,profileId:profile,runId,
    recordedAt:new Date().toISOString(),status:'FAIL',findings,checks,formalScore:null,
    scope:'Expected UI contract versus observations of the current final artifact; not formal or production acceptance'};
  try {
    if (!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(runId ?? '')) throw new Error('Safe current run ID required.');
    selectedProfiles(root,project,profile);
    if (!profile) throw new Error('Exactly one profile is required.');
    const owner=local(root,`${project}/srcs/${profile}`), specPrefix=`${project}/spec/${profile}/`;
    const contractPath=local(owner,'tests/ui-contract.json'), observationPath=local(owner,'build/test-results/ui-observations.json');
    const inputPath=local(owner,'build/generation/inputs.json');
    for(const target of [contractPath,observationPath,inputPath]) regular(target);
    const contract=read(contractPath), observations=read(observationPath), inputs=read(inputPath);
    result.contract=fileRecord(root,contractPath);result.observations=fileRecord(root,observationPath);result.frozenInputs=fileRecord(root,inputPath);
    result.validator=fileRecord(root,fileURLToPath(import.meta.url));
    if(observations.validatorSha256?.toLowerCase()!==result.validator.sha256) add('VALIDATOR_HASH','Observations were collected against another validator version.');
    // Bind the actual measurement implementation, not just the comparison tool.
    const measurementSources=[], measurementNames=new Set();
    if(!Array.isArray(observations.measurementSources) || !observations.measurementSources.length) add('MEASUREMENT_SOURCES_MISSING','A nonempty measurement source file/sha256 array is required.');
    else for(const source of observations.measurementSources) {
      if(!isObject(source) || typeof source.file!=='string' || !isHash(source.sha256)) {add('MEASUREMENT_SOURCE_SHAPE','Measurement source requires file and SHA-256.');continue;}
      const parts=source.file.split('/'), extension=path.posix.extname(source.file).toLowerCase();
      const sourceExtensions=new Set(['.py','.ps1','.bas','.cls','.mjs','.cjs','.js','.ts','.tsx','.jsx','.cs','.vb','.fs','.java','.go','.rb','.sh','.c','.cc','.cpp','.h','.hpp','.sql','.cbl','.cob','.cpy','.rpgle','.clle']);
      if(!['tests','tools','src','database'].includes(parts[0]) || parts.some(part=>['.tmp','build','node_modules','.git','spec','spec-eval','spec-analysis'].includes(part)) || !sourceExtensions.has(extension)) {
        add('MEASUREMENT_SOURCE_SCOPE',source.file+' must be owned measurement/test code, not metadata, evidence or output.');continue;
      }
      const normalized=source.file.toLowerCase();
      if(measurementNames.has(normalized)) add('MEASUREMENT_SOURCE_DUPLICATE',source.file);
      measurementNames.add(normalized);
      try {
        const target=local(owner,source.file);regular(target);
        const current=sha(fs.readFileSync(target));
        if(current!==source.sha256.toLowerCase()) add('MEASUREMENT_SOURCE_HASH',source.file+' changed after observation.');
        measurementSources.push({file:source.file,sha256:current});
      } catch(error) {add('MEASUREMENT_SOURCE_SCOPE',source.file+': '+error.message);}
    }
    result.measurementSources=measurementSources.sort((a,b)=>a.file < b.file ? -1 : a.file > b.file ? 1 : 0);
    if (contract.schemaVersion!==UI_SCHEMA_VERSION || observations.schemaVersion!==UI_SCHEMA_VERSION) add('SCHEMA_VERSION','UI contract and observations must use schemaVersion 1.');
    for(const [name,value] of [['contract',contract],['observations',observations],['frozen inputs',inputs]]) {
      if(value.projectId!==project || value.profileId!==profile) add('SCOPE',name+' belongs to another project/profile.');
    }
    if(inputs.runId!==runId || inputs.inspectionOnly!==false || inputs.specificationLayout!=='project/spec/profile') add('FROZEN_INPUT_SCOPE','Publishing inputs for this current run are required.');
    if(observations.runId!==undefined && observations.runId!==runId) add('OBSERVATION_RUN','Observations belong to another run.');
    if(!identifier(contract.contractId) || typeof contract.version!=='string' || !contract.version.trim()) add('CONTRACT_ID','Contract ID and version are required.');
    if(observations.contractSha256?.toLowerCase()!==result.contract.sha256) add('CONTRACT_HASH','Observations do not reference the exact independently authored contract.');
    if(observations.frozenInputManifestSha256?.toLowerCase()!==result.frozenInputs.sha256) add('INPUT_MANIFEST_HASH','Observations do not reference the exact current frozen input manifest.');
    if(!Array.isArray(inputs.files) || !inputs.files.length) throw new Error('Nonempty frozen inputs required.');
    const currentInputs=collectInputFiles(root,project,profile).map(target=>path.relative(root,target).split(path.sep).join('/')).sort();
    if(!same(inputs.files.map(entry=>entry.file).sort(),currentInputs)) add('FROZEN_INPUT_SET','Current required input files differ from the frozen set.');
    const frozen=new Map();
    for(const entry of inputs.files) {
      if(frozen.has(entry.file)) add('INPUT_DUPLICATE',entry.file);
      frozen.set(entry.file,entry);
      const target=local(root,entry.file);regular(target);
      if(!isHash(entry.sha256) || sha(fs.readFileSync(target))!==entry.sha256.toLowerCase()) add('FROZEN_INPUT_DRIFT',entry.file);
    }
    if(!Array.isArray(contract.sources) || !contract.sources.length) throw new Error('Contract source provenance is required.');
    const sourceFiles=new Set();
    for(const source of contract.sources) {
      if(!isObject(source) || typeof source.file!=='string') {add('SOURCE_PROVENANCE','Invalid source entry.');continue;}
      if(sourceFiles.has(source.file)) add('SOURCE_DUPLICATE',source.file);
      sourceFiles.add(source.file);
      const entry=frozen.get(source.file);
      if(!source.file.startsWith(specPrefix)) add('SOURCE_SCOPE','UI expectations must cite their own method specification: '+source.file);
      if(!entry || !isHash(source.sha256) || source.sha256.toLowerCase()!==entry.sha256?.toLowerCase() ||
         typeof source.documentId!=='string' || !source.documentId || typeof source.version!=='string' || !source.version ||
         source.documentId!==entry.documentId || source.version!==entry.version) add('SOURCE_PROVENANCE',source.file+' version/document ID/hash disagrees with frozen inputs.');
      const sourceText=fs.readFileSync(local(root,source.file),'utf8').replace(/^\uFEFF/,'');
      const sourceMetadata=JSON.parse(sourceText.match(/<!-- spec-meta: (.*?) -->/)?.[1]??'null');
      if(!sourceMetadata || sourceMetadata.documentId!==source.documentId || sourceMetadata.version!==source.version) add('SOURCE_METADATA',source.file+' actual document metadata differs from provenance.');
    }
    if(!isObject(contract.artifact) || !contract.artifact.file?.startsWith('build/') ||
       contract.artifact.file.startsWith('build/generation/') || contract.artifact.file.startsWith('build/test-results/')) throw new Error('Final product artifact under owned build/ is required.');
    const artifactPath=local(owner,contract.artifact.file), artifactHash=hashArtifact(artifactPath);
    result.artifact={file:contract.artifact.file,...artifactHash};
    if(observations.artifact?.file!==contract.artifact.file || observations.artifact?.sha256?.toLowerCase()!==artifactHash.sha256) add('ARTIFACT_HASH','Observations are stale or describe another final artifact.');
    const environment=observations.environment;
    if(!isObject(environment) || typeof environment.platform!=='string' || !environment.platform || typeof environment.renderer!=='string' || !environment.renderer ||
       !Number.isFinite(environment.scale) || environment.scale<=0 || !Number.isFinite(environment.dpi) || environment.dpi<=0 ||
       !isObject(environment.viewport) || !Number.isFinite(environment.viewport.width) || environment.viewport.width<=0 ||
       !Number.isFinite(environment.viewport.height) || environment.viewport.height<=0 || typeof environment.viewport.unit!=='string' || !environment.viewport.unit) add('ENVIRONMENT','Actual renderer, platform, DPI, scale and viewport are required.');
    result.environment=environment;
    if(!Array.isArray(contract.components) || !contract.components.length || !Array.isArray(observations.components)) throw new Error('Expected and independently observed component inventories are required.');
    const components=new Map(), actualComponents=new Map();
    for(const [label,list,target] of [['expected',contract.components,components],['observed',observations.components,actualComponents]]) {
      for(const component of list) {
        if(!isObject(component) || !identifier(component.id) || typeof component.kind!=='string' || !component.kind || typeof component.textCapable!=='boolean') {add('COMPONENT_SHAPE',label+' component must have id/kind/textCapable.');continue;}
        if(target.has(component.id)) add('COMPONENT_DUPLICATE',label+': '+component.id);
        target.set(component.id,component);
      }
    }
    for(const [id,component] of components) {
      const actual=actualComponents.get(id);
      if(!actual) add('COMPONENT_MISSING',id);
      else if(actual.kind!==component.kind || actual.textCapable!==component.textCapable) add('COMPONENT_MISMATCH',id);
    }
    for(const id of actualComponents.keys()) if(!components.has(id)) add('COMPONENT_UNSPECIFIED',id);
    if(!Array.isArray(contract.rules) || !contract.rules.length || !Array.isArray(observations.observations)) throw new Error('Expected rules and observed rule results are required.');
    const rules=new Map(), actualRules=new Map(), presentKinds=new Set();
    for(const rule of contract.rules) {
      if(!isObject(rule) || !identifier(rule.id)) {add('RULE_SHAPE','A stable rule ID is required.');continue;}
      if(rules.has(rule.id)) add('RULE_DUPLICATE',rule.id);
      rules.set(rule.id,rule);
      if(!kinds.has(rule.kind)) add('RULE_KIND_UNKNOWN',rule.id);
      if(rule.mandatory!==true) add('RULE_NOT_MANDATORY',rule.id+' must explicitly be mandatory.');
      if(!components.has(rule.target)) add('RULE_TARGET_UNKNOWN',rule.id);
      if(!Array.isArray(rule.sourceFiles) || !rule.sourceFiles.length || rule.sourceFiles.some(file=>!sourceFiles.has(file))) add('RULE_SOURCE_MISSING',rule.id);
      if(!isObject(rule.properties) || !Object.keys(rule.properties).length) {add('EXPECTED_MISSING',rule.id);continue;}
      for(const [property,value] of Object.entries(rule.properties)) if(!/^[A-Za-z][A-Za-z0-9_]{0,79}$/.test(property) || !expectationValid(value)) add('EXPECTED_INVALID',rule.id+'/'+property);
      if(rule.kind==='font' && ['fontFamily','fontSize','fontUnit'].some(property=>!Object.hasOwn(rule.properties,property))) add('FONT_EXPECTED_MISSING',rule.id);
      presentKinds.add(rule.kind);
    }
    for(const kind of ['font','dimensions','appearance','render','interaction']) if(!presentKinds.has(kind)) add('REQUIRED_KIND_MISSING',kind);
    for(const [id,component] of components) {
      const componentRules=[...rules.values()].filter(rule=>rule.target===id && rule.mandatory===true);
      if(!componentRules.length) add('COMPONENT_UNCOVERED',id);
      if(component.textCapable && !componentRules.some(rule=>rule.kind==='font')) add('COMPONENT_FONT_UNCOVERED',id);
    }
    for(const observed of observations.observations) {
      if(!isObject(observed) || !identifier(observed.ruleId)) {add('OBSERVATION_SHAPE','A stable ruleId is required.');continue;}
      if(actualRules.has(observed.ruleId)) add('OBSERVATION_DUPLICATE',observed.ruleId);
      actualRules.set(observed.ruleId,observed);
      if(!rules.has(observed.ruleId)) add('RULE_UNKNOWN',observed.ruleId);
    }
    for(const [id,rule] of rules) {
      const observed=actualRules.get(id);
      if(!observed) {add('OBSERVATION_MISSING',id);continue;}
      if(observed.target!==rule.target) add('OBSERVATION_TARGET',id);
      if(!methods[rule.kind]?.has(observed.method)) add('MEASUREMENT_METHOD',id);
      if(!isObject(observed.properties)) {add('PROPERTIES_MISSING',id);continue;}
      const expectedProperties=isObject(rule.properties)?Object.keys(rule.properties):[];
      for(const property of Object.keys(observed.properties)) if(!expectedProperties.includes(property)) add('PROPERTY_UNSPECIFIED',id+'/'+property);
      for(const property of expectedProperties) {
        const passed=expectationValid(rule.properties[property]) && compare(rule.properties[property],observed.properties[property]);
        checks.push({ruleId:id,target:rule.target,property,expected:rule.properties[property],actual:observed.properties[property]??null,passed});
        if(!passed) add(Object.hasOwn(observed.properties,property)?'PROPERTY_MISMATCH':'PROPERTY_MISSING',id+'/'+property);
      }
      if(observed.evidence!==undefined && !Array.isArray(observed.evidence)) {add('EVIDENCE_SHAPE',id);continue;}
      if(rule.kind==='render' && !observed.evidence?.length) add('RENDER_EVIDENCE_MISSING',id);
      for(const item of observed.evidence??[]) {
        if(!isObject(item) || !item.file?.startsWith('build/test-results/') || item.file==='build/test-results/ui-observations.json' || item.file==='build/test-results/ui-conformance.json') {add('EVIDENCE_SCOPE',id);continue;}
        const target=local(owner,item.file);regular(target);
        if(!isHash(item.sha256) || sha(fs.readFileSync(target))!==item.sha256.toLowerCase()) add('EVIDENCE_HASH',id+'/'+item.file);
      }
    }
    result.contractId=contract.contractId;result.contractVersion=contract.version;
    result.components=components.size;result.rules=rules.size;result.comparedProperties=checks.length;
  } catch(error) {add('VALIDATION_ERROR',error.message);}
  result.status=findings.length?'FAIL':'PASS';
  return result;
}

export function requireCurrentUIResult(options) {
  const current=validateUIConformance(options);
  if(current.status!=='PASS') throw new Error('UI conformance failed: '+current.findings.map(item=>item.code+': '+item.detail).join('; '));
  const owner=path.join(options.root,options.project,'srcs',options.profile);
  const target=path.join(owner,'build/test-results/ui-conformance.json');regular(target);
  const previous=read(target);
  for(const key of ['schemaVersion','validatorVersion','projectId','profileId','runId','status','contract','observations','frozenInputs','validator','artifact','measurementSources']) {
    if(!same(previous[key],current[key])) throw new Error('UI conformance result is missing or stale: '+key);
  }
  return fileRecord(options.root,target);
}

if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const args=process.argv.slice(2), options={root:path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..')};
  if(args.length%2) throw new Error('Every option requires a value.');
  for(let i=0;i<args.length;i+=2) {
    const names={'--project':'project','--profile':'profile','--run-id':'runId'};
    if(!names[args[i]] || options[names[args[i]]]) throw new Error('Usage: ui-conformance.mjs --project <project> --profile <profile> --run-id <run>');
    options[names[args[i]]]=args[i+1];
  }
  selectedProfiles(options.root,options.project,options.profile);
  if(!options.profile) throw new Error('Exactly one profile required.');
  const result=validateUIConformance(options);
  const owner=path.join(options.root,options.project,'srcs',options.profile);
  writeJson(path.join(owner,'build/test-results/ui-conformance.json'),result,path.join(owner,'.tmp/ui-conformance'));
  console.log(JSON.stringify({status:result.status,comparedProperties:result.comparedProperties??0,findings:result.findings}));
  process.exitCode=result.status==='PASS'?0:1;
}
