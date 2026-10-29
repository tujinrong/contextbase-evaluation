// Synthetic regressions only: these fixture PASS results never accept an application.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {validateUIConformance,hashArtifact,uiPolicyForProfile,requireCurrentUIResult} from './ui-conformance.mjs';
import {fixedInputFiles,collectInputFiles} from './input-scope.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(here,'../.tmp/ui-conformance-tests');fs.mkdirSync(base,{recursive:true});
const workspace=fs.mkdtempSync(path.join(base,'work-')), root=path.join(workspace,'repo');
const project='sample-project1',profile='Access',runId='ui-fixture',owner=`${project}/srcs/${profile}`;
const spec=`${project}/spec/${profile}/規約/UI生成条件.md`;
const contractFile=`${owner}/tests/ui-contract.json`, observationFile=`${owner}/build/test-results/ui-observations.json`;
const inputsFile=`${owner}/build/generation/inputs.json`,resultFile=`${owner}/build/test-results/ui-conformance.json`;
const accessQualitySource='docs/Access画面品質規約.md';
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const hash=file=>sha(fs.readFileSync(path.join(root,file)));
const write=(file,value)=>{const target=path.join(root,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,typeof value==='string'?value:JSON.stringify(value,null,2)+'\n');};
const read=file=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
let assertions=0;
function assert(ok,detail){if(!ok)throw new Error(detail);assertions++;}
function doc(file,id){return `<!-- spec-meta: ${JSON.stringify({schema:'spec-md/1.0',documentId:id,version:'1.0',path:file,sheets:[{heading:'定義',kind:'GRID',sheet:'01_定義'}]})} -->\n# Synthetic UI fixture\n\n## 定義\n\nThis fixture declares synthetic UI expectations, not a real product.\n`;}
const options={root,project,profile,runId};
function refreshContractHash(){const actual=read(observationFile);actual.contractSha256=hash(contractFile);write(observationFile,actual);}
function setup(){
 for(const file of fixedInputFiles(project,profile))write(file,doc(file,'FIX-'+sha(file).slice(0,12)));
 write(`${project}/spec/README.md`,'| 方式ID | specRoot | sourceRoot |\n| --- | --- | --- |\n| Access | sample-project1/spec/Access/ | sample-project1/srcs/Access/ |\n');
 write(`${project}/spec/${profile}/規約/開発規約.md`,doc(`${project}/spec/${profile}/規約/開発規約.md`,'FIX-DEV'));
 write(spec,doc(spec,'FIX-UI'));
 write(`${owner}/profile.json`,{projectId:project,methodId:profile,uiConformance:{required:true,contract:'tests/ui-contract.json'}});
 write(`${owner}/build/app/product.bin`,'synthetic product bytes');
 write(`${owner}/build/app/site.css`,'synthetic style v1');
 write(`${owner}/build/test-results/ui/screen.txt`,'synthetic independent render measurement evidence');
 write(`${owner}/build/test-results/ui/operations.txt`,'synthetic independent operation and data reload evidence; no application was run');
 write(`${owner}/tests/observe.py`,'# Synthetic observer source, never executed\n');
 write(`${owner}/tools/measure-helper.py`,'# Synthetic measurement helper, never executed\n');
 const files=collectInputFiles(root,project,profile).map(target=>{
  const data=fs.readFileSync(target),metadata=JSON.parse(data.toString().match(/<!-- spec-meta: (.*?) -->/)?.[1]??'null');
  return {file:path.relative(root,target).split(path.sep).join('/'),sha256:sha(data),bytes:data.length,...(metadata?{documentId:metadata.documentId,version:metadata.version}:{})};
 });
 const frozen={projectId:project,profileId:profile,runId,inputCommit:'fixture',inspectionOnly:false,specificationLayout:'project/spec/profile',files};
 write(inputsFile,frozen);
 write(`${owner}/build/generation/structure.json`,{projectId:project,profileId:profile,runId,inspectionOnly:false,status:'structure-check-passed'});
 const components=[{id:'F01',kind:'Form',textCapable:false},{id:'F01/Tab',kind:'Tab',textCapable:true},{id:'F01/Label',kind:'Label',textCapable:true}];
 const rule=(id,kind,target,properties)=>({id,kind,target,mandatory:true,sourceFiles:[spec],properties});
 const eq=value=>({op:'eq',value});
 const contract={schemaVersion:1,projectId:project,profileId:profile,contractId:'SYNTHETIC-UI',version:'1.0',artifact:{file:'build/app'},
  sources:[{file:spec,documentId:'FIX-UI',version:'1.0',sha256:hash(spec)}],components,
  rules:[rule('TAB-FONT','font','F01/Tab',{fontFamily:eq('Yu Gothic UI'),fontSize:eq(11),fontUnit:eq('pt')}),
   rule('LABEL-FONT','font','F01/Label',{fontFamily:eq('Yu Gothic UI'),fontSize:eq(11),fontUnit:eq('pt')}),
   rule('WIDTH','dimensions','F01',{width:{op:'range',value:[459,461]},unit:eq('px')}),
   rule('CLASSIC','appearance','F01',{useTheme:eq(false),gradient:eq(0)}),
   rule('RENDER','render','F01',{readable:eq(true),horizontalOverflow:eq(false)}),
   rule('KEYBOARD','interaction','F01',{keyboardAccessible:eq(true),statePreserved:eq(true)}),
   rule('IDENTITY','render','F01',{targetIdentifiable:eq(true)}),
   rule('CONTENT','render','F01',{fullTextReachable:eq(true)}),
   rule('SELECTION','interaction','F01',{detailMatchesSelection:eq(true)}),
   rule('SAVE-CANCEL','interaction','F01',{unappliedValuesProtected:eq(true),discardedValuesAbsentOnReload:eq(true)}),
   rule('NAVIGATION','interaction','F01',{dirtyExitProtected:eq(true),saveFailureKeepsInput:eq(true)}),
   rule('STATES','render','F01',{statesDistinguishable:eq(true)}),
   rule('VIEWPORT-SIZE','dimensions','F01',{width:eq(1366),height:eq(768),unit:eq('px')}),
   rule('VIEWPORT-RENDER','render','F01',{primaryActionsReachable:eq(true)})],
  accessScreenChecks:[{target:'F01',screenType:'MASTER_DETAIL',checks:{
   identity:{applicable:true,ruleIds:['IDENTITY']},layout:{applicable:true,ruleIds:['WIDTH']},
   content:{applicable:true,ruleIds:['CONTENT']},selection:{applicable:true,ruleIds:['SELECTION']},
   saveCancel:{applicable:true,ruleIds:['SAVE-CANCEL']},navigation:{applicable:true,ruleIds:['NAVIGATION']},
   keyboard:{applicable:true,ruleIds:['KEYBOARD']},states:{applicable:true,ruleIds:['STATES']},
   viewport:{applicable:true,ruleIds:['VIEWPORT-SIZE','VIEWPORT-RENDER']}}}]};
 write(contractFile,contract);
 // Observed values are deliberately independent fixture constants, not copied from expected property values.
 const actual={schemaVersion:1,projectId:project,profileId:profile,runId,contractSha256:hash(contractFile),frozenInputManifestSha256:hash(inputsFile),
  validatorSha256:sha(fs.readFileSync(path.join(here,'ui-conformance.mjs'))),artifact:{file:'build/app',sha256:hashArtifact(path.join(root,owner,'build/app')).sha256},
  measurementSources:[{file:'tests/observe.py',sha256:hash(`${owner}/tests/observe.py`)},{file:'tools/measure-helper.py',sha256:hash(`${owner}/tools/measure-helper.py`)}],
  environment:{platform:'Synthetic Windows',renderer:'Synthetic native renderer',dpi:96,scale:1,viewport:{width:1366,height:768,unit:'px'}},
  components:[{id:'F01',kind:'Form',textCapable:false},{id:'F01/Tab',kind:'Tab',textCapable:true},{id:'F01/Label',kind:'Label',textCapable:true}],
  observations:[{ruleId:'TAB-FONT',target:'F01/Tab',method:'native-property',properties:{fontFamily:'Yu Gothic UI',fontSize:11,fontUnit:'pt'}},
   {ruleId:'LABEL-FONT',target:'F01/Label',method:'native-property',properties:{fontFamily:'Yu Gothic UI',fontSize:11,fontUnit:'pt'}},
   {ruleId:'WIDTH',target:'F01',method:'layout-measurement',properties:{width:460,unit:'px'}},
   {ruleId:'CLASSIC',target:'F01',method:'native-property',properties:{useTheme:false,gradient:0}},
   {ruleId:'RENDER',target:'F01',method:'render-review',properties:{readable:true,horizontalOverflow:false},evidence:[{file:'build/test-results/ui/screen.txt',sha256:hash(`${owner}/build/test-results/ui/screen.txt`)}]},
   {ruleId:'KEYBOARD',target:'F01',method:'keyboard-operation',properties:{keyboardAccessible:true,statePreserved:true}},
   {ruleId:'IDENTITY',target:'F01',method:'render-review',properties:{targetIdentifiable:true}},
   {ruleId:'CONTENT',target:'F01',method:'render-review',properties:{fullTextReachable:true}},
   {ruleId:'SELECTION',target:'F01',method:'keyboard-operation',properties:{detailMatchesSelection:true}},
   {ruleId:'SAVE-CANCEL',target:'F01',method:'keyboard-operation',properties:{unappliedValuesProtected:true,discardedValuesAbsentOnReload:true}},
   {ruleId:'NAVIGATION',target:'F01',method:'keyboard-operation',properties:{dirtyExitProtected:true,saveFailureKeepsInput:true}},
   {ruleId:'STATES',target:'F01',method:'render-review',properties:{statesDistinguishable:true}},
   {ruleId:'VIEWPORT-SIZE',target:'F01',method:'layout-measurement',properties:{width:1366,height:768,unit:'px'}},
   {ruleId:'VIEWPORT-RENDER',target:'F01',method:'render-review',properties:{primaryActionsReachable:true}}]};
 for(const observed of actual.observations) {
  if(['render-review','keyboard-operation'].includes(observed.method) && !observed.evidence) {
   const file=observed.method==='keyboard-operation'?'build/test-results/ui/operations.txt':'build/test-results/ui/screen.txt';
   observed.evidence=[{file,sha256:hash(`${owner}/${file}`)}];
  }
 }
 write(observationFile,actual);
}
function fails(name,change,code){setup();change();const result=validateUIConformance(options);assert(result.status==='FAIL',name+' was accepted');assert(result.findings.some(item=>item.code===code),name+' had wrong finding: '+JSON.stringify(result.findings));}
function mutateObservation(change){const value=read(observationFile);change(value);write(observationFile,value);}
function mutateContract(change){const value=read(contractFile);change(value);write(contractFile,value);refreshContractHash();}
function cli(script,expected){const output=spawnSync(process.execPath,[path.join(root,'agents/builds/build-agent/scripts',script),'--project',project,'--profile',profile,'--run-id',runId],{cwd:root,encoding:'utf8'});assert(output.status===expected,script+' expected '+expected+' got '+output.status+': '+output.stderr+output.stdout);}
function peerFixture(){
 setup();
 const peer='CSharp_ASPNET',peerOwner=`${project}/srcs/${peer}`,peerSpec=`${project}/spec/${peer}/規約/UI生成条件.md`;
 write(`${project}/spec/README.md`,'| 方式ID | specRoot | sourceRoot |\n| --- | --- | --- |\n| Access | sample-project1/spec/Access/ | sample-project1/srcs/Access/ |\n| CSharp_ASPNET | sample-project1/spec/CSharp_ASPNET/ | sample-project1/srcs/CSharp_ASPNET/ |\n');
 write(`${project}/spec/${peer}/規約/開発規約.md`,doc(`${project}/spec/${peer}/規約/開発規約.md`,'FIX-PEER-DEV'));
 write(peerSpec,doc(peerSpec,'FIX-PEER-UI'));
 write(`${peerOwner}/profile.json`,{uiConformance:{required:true,contract:'tests/ui-contract.json'}});
 for(const file of ['build/app/product.bin','build/app/site.css','build/test-results/ui/screen.txt','build/test-results/ui/operations.txt','tests/observe.py','tools/measure-helper.py']) write(`${peerOwner}/${file}`,fs.readFileSync(path.join(root,owner,file),'utf8'));
 const files=collectInputFiles(root,project,peer).map(target=>{
  const data=fs.readFileSync(target),metadata=JSON.parse(data.toString().match(/<!-- spec-meta: (.*?) -->/)?.[1]??'null');
  return {file:path.relative(root,target).split(path.sep).join('/'),sha256:sha(data),bytes:data.length,...(metadata?{documentId:metadata.documentId,version:metadata.version}:{})};
 });
 write(`${peerOwner}/build/generation/inputs.json`,{...read(inputsFile),profileId:peer,files});
 const contract=read(contractFile);contract.profileId=peer;delete contract.accessScreenChecks;
 contract.sources=[{file:peerSpec,documentId:'FIX-PEER-UI',version:'1.0',sha256:hash(peerSpec)}];
 for(const rule of contract.rules) rule.sourceFiles=[peerSpec];
 write(`${peerOwner}/tests/ui-contract.json`,contract);
 const actual=read(observationFile);actual.profileId=peer;actual.contractSha256=hash(`${peerOwner}/tests/ui-contract.json`);
 actual.frozenInputManifestSha256=hash(`${peerOwner}/build/generation/inputs.json`);
 for(const observed of actual.observations) if(observed.method==='keyboard-operation') delete observed.evidence;
 write(`${peerOwner}/build/test-results/ui-observations.json`,actual);
 return {root,project,profile:peer,runId};
}
try {
 setup();assert(validateUIConformance(options).status==='PASS','Valid native fixture failed');
 assert(read(inputsFile).files.some(file=>file.file===accessQualitySource),'Access fixture must freeze the Access screen quality rule.');
 assert(validateUIConformance(options).accessScreenChecksRequired===true,'Current Access quality coverage was not enabled.');
 const digest=hashArtifact(path.join(root,owner,'build/app')).sha256;fs.utimesSync(path.join(root,owner,'build/app/site.css'),new Date(0),new Date(0));assert(hashArtifact(path.join(root,owner,'build/app')).sha256===digest,'Timestamp changed product directory hash');
 fails('Tab font fell back to 9pt',()=>mutateObservation(value=>value.observations[0].properties.fontSize=9),'PROPERTY_MISMATCH');
 fails('Attached label font unobserved',()=>mutateObservation(value=>delete value.observations[1].properties.fontFamily),'PROPERTY_MISSING');
 fails('Missing Tab font rule',()=>mutateContract(value=>value.rules=value.rules.filter(rule=>rule.id!=='TAB-FONT')),'COMPONENT_FONT_UNCOVERED');
 fails('Office theme returned',()=>mutateObservation(value=>value.observations[3].properties.useTheme=true),'PROPERTY_MISMATCH');
 fails('All appearance rules omitted',()=>{mutateContract(value=>value.rules=value.rules.filter(rule=>rule.kind!=='appearance'));mutateObservation(value=>value.observations=value.observations.filter(item=>item.ruleId!=='CLASSIC'));},'REQUIRED_KIND_MISSING');
 fails('Width overwritten by later style',()=>mutateObservation(value=>value.observations[2].properties.width=520),'PROPERTY_MISMATCH');
 fails('Narrow DOM horizontal overflow',()=>mutateObservation(value=>value.observations[4].properties.horizontalOverflow=true),'PROPERTY_MISMATCH');
 fails('Unreadable rendering',()=>mutateObservation(value=>value.observations[4].properties.readable=false),'PROPERTY_MISMATCH');
 fails('Keyboard regression',()=>mutateObservation(value=>value.observations[5].properties.keyboardAccessible=false),'PROPERTY_MISMATCH');
 fails('Unobserved mandatory rule',()=>mutateObservation(value=>value.observations.pop()),'OBSERVATION_MISSING');
 fails('Unknown rule',()=>mutateObservation(value=>value.observations.push({ruleId:'UNKNOWN',target:'F01',properties:{}})),'RULE_UNKNOWN');
 fails('Unknown rule kind',()=>mutateContract(value=>value.rules[0].kind='guess-font'),'RULE_KIND_UNKNOWN');
 fails('Duplicate observation',()=>mutateObservation(value=>value.observations.push(value.observations[0])),'OBSERVATION_DUPLICATE');
 fails('Unspecified real component',()=>mutateObservation(value=>value.components.push({id:'F01/Surprise',kind:'Label',textCapable:true})),'COMPONENT_UNSPECIFIED');
 fails('Missing real component',()=>mutateObservation(value=>value.components.pop()),'COMPONENT_MISSING');
 fails('Property outside expected contract',()=>mutateObservation(value=>value.observations[0].properties.unexpected=11),'PROPERTY_UNSPECIFIED');
 fails('Missing expected property value',()=>mutateContract(value=>delete value.rules[0].properties.fontSize.value),'EXPECTED_INVALID');
 fails('Empty expected property set',()=>mutateContract(value=>value.rules[2].properties={}),'EXPECTED_MISSING');
 fails('Optional rule cannot hide mismatch',()=>mutateContract(value=>value.rules[0].mandatory=false),'RULE_NOT_MANDATORY');
 fails('Old final product',()=>write(`${owner}/build/app/product.bin`,'new synthetic product'),'ARTIFACT_HASH');
 fails('Only published CSS changed',()=>write(`${owner}/build/app/site.css`,'synthetic style v2'),'ARTIFACT_HASH');
 fails('Added published asset',()=>write(`${owner}/build/app/new.css`,'new style'),'ARTIFACT_HASH');
 fs.unlinkSync(path.join(root,owner,'build/app/new.css'));
 fails('Old validator',()=>mutateObservation(value=>value.validatorSha256='a'.repeat(64)),'VALIDATOR_HASH');
 fails('Measurement source array missing',()=>mutateObservation(value=>delete value.measurementSources),'MEASUREMENT_SOURCES_MISSING');
 fails('Measurement source edited after observation',()=>write(`${owner}/tests/observe.py`,'# Changed collector after observation\n'),'MEASUREMENT_SOURCE_HASH');
 fails('Measurement helper edited after observation',()=>write(`${owner}/tools/measure-helper.py`,'# Changed helper after observation\n'),'MEASUREMENT_SOURCE_HASH');
 fails('Duplicate measurement source',()=>mutateObservation(value=>value.measurementSources.push(value.measurementSources[0])),'MEASUREMENT_SOURCE_DUPLICATE');
 fails('Escaping measurement source',()=>mutateObservation(value=>value.measurementSources[0].file='tests/../../other.py'),'MEASUREMENT_SOURCE_SCOPE');
 fails('Expected contract cannot be measurement source',()=>mutateObservation(value=>value.measurementSources[0]={file:'tests/ui-contract.json',sha256:hash(contractFile)}),'MEASUREMENT_SOURCE_SCOPE');
 fails('Observation cannot cite itself as measurement source',()=>mutateObservation(value=>value.measurementSources[0]={file:'build/test-results/ui-observations.json',sha256:hash(observationFile)}),'MEASUREMENT_SOURCE_SCOPE');
 fails('Measurement source absent',()=>fs.unlinkSync(path.join(root,owner,'tools/measure-helper.py')),'MEASUREMENT_SOURCE_SCOPE');
 fails('Old input manifest',()=>mutateObservation(value=>value.frozenInputManifestSha256='b'.repeat(64)),'INPUT_MANIFEST_HASH');
 fails('Old contract',()=>mutateObservation(value=>value.contractSha256='c'.repeat(64)),'CONTRACT_HASH');
 fails('Old source version',()=>mutateContract(value=>value.sources[0].version='0.9'),'SOURCE_PROVENANCE');
 fails('Expected source deleted',()=>write(spec,'changed source'),'FROZEN_INPUT_DRIFT');
 fails('Wrong source attribution',()=>mutateContract(value=>value.rules[0].sourceFiles=[]),'RULE_SOURCE_MISSING');
 fails('Unknown source scope',()=>mutateContract(value=>value.sources[0].file='sample-project1/spec/CSharp_ASPNET/UI.md'),'SOURCE_SCOPE');
 fails('DPI unobserved',()=>mutateObservation(value=>value.environment.dpi=null),'ENVIRONMENT');
 fails('Model values used as font observation',()=>mutateObservation(value=>value.observations[0].method='keyboard-operation'),'MEASUREMENT_METHOD');
 fails('Render evidence omitted',()=>mutateObservation(value=>value.observations[4].evidence=[]),'RENDER_EVIDENCE_MISSING');
 fails('Render evidence changed',()=>write(`${owner}/build/test-results/ui/screen.txt`,'changed independent evidence'),'EVIDENCE_HASH');
 fails('Evidence escaped final evidence folder',()=>mutateObservation(value=>value.observations[4].evidence[0].file='../outside.txt'),'EVIDENCE_SCOPE');
 fails('Contract deleted',()=>fs.unlinkSync(path.join(root,contractFile)),'VALIDATION_ERROR');
 fails('Access screen coverage missing',()=>mutateContract(value=>delete value.accessScreenChecks),'ACCESS_SCREEN_CHECKS_MISSING');
 fails('Access screen coverage empty',()=>mutateContract(value=>value.accessScreenChecks=[]),'ACCESS_SCREEN_CHECKS_MISSING');
 fails('Missing check category',()=>mutateContract(value=>delete value.accessScreenChecks[0].checks.content),'ACCESS_CHECK_CATEGORIES');
 fails('Unknown check category',()=>mutateContract(value=>value.accessScreenChecks[0].checks.contents={applicable:true,ruleIds:['CONTENT']}),'ACCESS_CHECK_CATEGORIES');
 fails('Unknown screen target',()=>mutateContract(value=>value.accessScreenChecks[0].target='F99'),'ACCESS_SCREEN_TARGET');
 fails('Repeated screen target',()=>mutateContract(value=>value.accessScreenChecks.push(value.accessScreenChecks[0])),'ACCESS_SCREEN_DUPLICATE');
 fails('Unknown screen type',()=>mutateContract(value=>value.accessScreenChecks[0].screenType='EDIT'),'ACCESS_SCREEN_TYPE');
 fails('Custom screen purpose missing',()=>mutateContract(value=>value.accessScreenChecks[0].screenType='CUSTOM'),'ACCESS_SCREEN_PURPOSE');
 fails('Undocumented exclusion',()=>mutateContract(value=>{value.accessScreenChecks[0].screenType='AUTH';value.accessScreenChecks[0].checks.selection={applicable:false,ruleIds:[]};}),'ACCESS_CHECK_EXCLUSION');
 fails('Excluded check retains rules',()=>mutateContract(value=>{value.accessScreenChecks[0].screenType='AUTH';value.accessScreenChecks[0].checks.selection={applicable:false,reason:'No row selection',ruleIds:['SELECTION']};}),'ACCESS_CHECK_EXCLUSION');
 fails('Always required check excluded',()=>mutateContract(value=>value.accessScreenChecks[0].checks.identity={applicable:false,reason:'Hidden identity',ruleIds:[]}),'ACCESS_CHECK_REQUIRED');
 fails('Master detail selection excluded',()=>mutateContract(value=>value.accessScreenChecks[0].checks.selection={applicable:false,reason:'Skipped selection',ruleIds:[]}),'ACCESS_CHECK_REQUIRED');
 fails('Search selection excluded',()=>mutateContract(value=>{value.accessScreenChecks[0].screenType='SEARCH_LIST';value.accessScreenChecks[0].checks.selection={applicable:false,reason:'Skipped selection',ruleIds:[]};}),'ACCESS_CHECK_REQUIRED');
 for(const screenType of ['EDIT_FORM','MASTER_DETAIL','WIZARD','SETTINGS']) fails(screenType+' save/cancel excluded',()=>mutateContract(value=>{value.accessScreenChecks[0].screenType=screenType;value.accessScreenChecks[0].checks.saveCancel={applicable:false,reason:'Skipped persistence',ruleIds:[]};}),'ACCESS_CHECK_REQUIRED');
 fails('Applicable check has no rules',()=>mutateContract(value=>value.accessScreenChecks[0].checks.content.ruleIds=[]),'ACCESS_CHECK_RULES_MISSING');
 fails('Absent check rule',()=>mutateContract(value=>value.accessScreenChecks[0].checks.identity.ruleIds=['NO-SUCH-RULE']),'ACCESS_CHECK_RULE_REFERENCE');
 fails('Repeated check rule',()=>mutateContract(value=>value.accessScreenChecks[0].checks.identity.ruleIds=['IDENTITY','IDENTITY']),'ACCESS_CHECK_RULE_REFERENCE');
 fails('Nonmandatory check rule',()=>mutateContract(value=>value.rules.find(rule=>rule.id==='IDENTITY').mandatory=false),'ACCESS_CHECK_RULE_REFERENCE');
 fails('Render used for layout',()=>mutateContract(value=>value.accessScreenChecks[0].checks.layout.ruleIds=['RENDER']),'ACCESS_CHECK_KIND');
 fails('Viewport render without dimensions',()=>mutateContract(value=>value.accessScreenChecks[0].checks.viewport.ruleIds=['VIEWPORT-RENDER']),'ACCESS_CHECK_KIND');
 fails('Viewport dimensions without render',()=>mutateContract(value=>value.accessScreenChecks[0].checks.viewport.ruleIds=['VIEWPORT-SIZE']),'ACCESS_CHECK_KIND');
 fails('Universal render rule reused for categories',()=>mutateContract(value=>value.accessScreenChecks[0].checks.content.ruleIds=['IDENTITY']),'ACCESS_CHECK_RULE_REUSE');
 fails('Universal interaction rule reused for categories',()=>mutateContract(value=>value.accessScreenChecks[0].checks.navigation.ruleIds=['KEYBOARD']),'ACCESS_CHECK_RULE_REUSE');
 fails('Unregistered Tab page',()=>{
  mutateContract(value=>{value.components.push({id:'F01/Page2',kind:'tAbPaGe',textCapable:false});value.rules.push({id:'PAGE-RENDER',kind:'render',target:'F01/Page2',mandatory:true,sourceFiles:[spec],properties:{readable:{op:'eq',value:true}}});});
  mutateObservation(value=>{value.components.push({id:'F01/Page2',kind:'tAbPaGe',textCapable:false});value.observations.push({ruleId:'PAGE-RENDER',target:'F01/Page2',method:'render-review',properties:{readable:true},evidence:[{file:'build/test-results/ui/screen.txt',sha256:hash(`${owner}/build/test-results/ui/screen.txt`)}]});});
 },'ACCESS_SCREEN_UNCOVERED');
 fails('Interaction evidence omitted',()=>mutateObservation(value=>delete value.observations.find(item=>item.ruleId==='SAVE-CANCEL').evidence),'INTERACTION_EVIDENCE_MISSING');
 fails('Interaction evidence changed',()=>write(`${owner}/build/test-results/ui/operations.txt`,'changed operation evidence'),'EVIDENCE_HASH');
 setup();mutateContract(value=>{value.accessScreenChecks[0].screenType='AUTH';for(const key of ['selection','saveCancel'])value.accessScreenChecks[0].checks[key]={applicable:false,reason:'Authentication has no row selection or business-record edits.',ruleIds:[]};});
 assert(validateUIConformance(options).status==='PASS','Justified optional AUTH exclusions failed.');
 setup();mutateContract(value=>{value.accessScreenChecks[0].screenType='CUSTOM';value.accessScreenChecks[0].purpose='Synthetic purpose-specific screen';});
 assert(validateUIConformance(options).status==='PASS','Custom type with a purpose failed.');
 setup();mutateContract(value=>{value.components.push({id:'F01/Page2',kind:'Page',textCapable:false});value.rules.push({id:'PAGE-WIDTH',kind:'dimensions',target:'F01/Page2',mandatory:true,sourceFiles:[spec],properties:{width:{op:'eq',value:460}}});value.accessScreenChecks.push({...value.accessScreenChecks[0],target:'F01/Page2'});});
 mutateObservation(value=>{value.components.push({id:'F01/Page2',kind:'Page',textCapable:false});value.observations.push({ruleId:'PAGE-WIDTH',target:'F01/Page2',method:'native-property',properties:{width:460}});});
 assert(validateUIConformance(options).status==='PASS','Same-category common checks across surfaces were rejected.');
 setup();const legacyInputs=read(inputsFile);legacyInputs.files=legacyInputs.files.filter(file=>file.file!==accessQualitySource);write(inputsFile,legacyInputs);
 mutateContract(value=>delete value.accessScreenChecks);mutateObservation(value=>{value.frozenInputManifestSha256=hash(inputsFile);for(const item of value.observations)if(item.method==='keyboard-operation')delete item.evidence;});
 const legacyResult=validateUIConformance(options);
 assert(legacyResult.accessScreenChecksRequired===false&&!legacyResult.findings.some(item=>item.code.startsWith('ACCESS_')||item.code==='INTERACTION_EVIDENCE_MISSING'),'Access checks were imposed on an old input contract.');
 assert(legacyResult.findings.some(item=>item.code==='FROZEN_INPUT_SET'),'Old frozen input set bypassed the current required input set.');
 const peerResult=validateUIConformance(peerFixture());
 assert(peerResult.status==='PASS'&&peerResult.accessScreenChecksRequired===false,'Access-specific screen checks or interaction evidence affected another profile: '+JSON.stringify(peerResult.findings));
 setup();write(resultFile,validateUIConformance(options));assert(requireCurrentUIResult(options).file.endsWith('/ui-conformance.json'),'Current saved gate not accepted');
 mutateObservation(value=>value.observations[2].properties.width=461);let refused=false;try{requireCurrentUIResult(options);}catch{refused=true;}assert(refused,'Changed observations reused old saved gate');
 setup();const policyOptions={root,project,profile,requireDeclaration:true,frozenInputs:read(inputsFile)};
 assert(uiPolicyForProfile(policyOptions).required===true,'Mandatory UI declaration not recognized');
 write(`${owner}/profile.json`,{});refused=false;try{uiPolicyForProfile(policyOptions);}catch{refused=true;}assert(refused,'Missing declaration skipped current gate');
 write(`${owner}/profile.json`,{uiConformance:{required:false}});refused=false;try{uiPolicyForProfile(policyOptions);}catch{refused=true;}assert(refused,'required:false without reason bypassed current gate');
 fs.unlinkSync(path.join(root,contractFile));fs.unlinkSync(path.join(root,observationFile));
 write(`${owner}/profile.json`,{uiConformance:{required:false,reason:'Synthetic CLI has no UI'}});refused=false;try{uiPolicyForProfile(policyOptions);}catch{refused=true;}assert(refused,'Non-UI reason without frozen provenance bypassed gate');
 write(`${owner}/profile.json`,{uiConformance:{required:false,reason:'Synthetic CLI has no UI',sourceFiles:[spec]}});assert(uiPolicyForProfile(policyOptions).status==='NOT_APPLICABLE','Valid non-UI exemption rejected');
 setup();for(const name of ['manifest.mjs','ui-conformance.mjs','input-scope.mjs','output-layout.mjs','project-scope.mjs'])write('agents/builds/build-agent/scripts/'+name,fs.readFileSync(path.join(here,name),'utf8'));
 assert(spawnSync('git',['init',root],{encoding:'utf8'}).status===0,'Fixture git init failed');
 cli('ui-conformance.mjs',0);cli('manifest.mjs',0);
 const outputFile=`${owner}/build/generation/outputs.json`;
 assert(read(outputFile).uiConformance[0].status==='PASS','Manifest did not bind the current UI gate');
 write(`${owner}/build/app/site.css`,'late CSS change');cli('manifest.mjs',1);assert(!fs.existsSync(path.join(root,outputFile)),'UI gate failure left an old output manifest published');
 setup();cli('ui-conformance.mjs',0);cli('manifest.mjs',0);write(`${owner}/tests/observe.py`,'# Later collector change, artifact is unchanged\n');cli('manifest.mjs',1);assert(!fs.existsSync(path.join(root,outputFile)),'Changed measurement source retained a current output manifest');
 setup();cli('ui-conformance.mjs',0);fs.unlinkSync(path.join(root,contractFile));cli('manifest.mjs',1);
 setup();cli('ui-conformance.mjs',0);fs.unlinkSync(path.join(root,resultFile));cli('manifest.mjs',1);
 setup();cli('ui-conformance.mjs',0);write(`${owner}/profile.json`,{});cli('manifest.mjs',1);
 console.log(`PASS ${assertions} assertions: independent UI contracts, Access screen/category coverage and operation evidence, native Tab/theme/font regressions, DOM widths/overflow, full artifact hashes, provenance, legacy/non-Access isolation, declared non-UI exceptions and mandatory manifest refusal; synthetic fixture only.`);
} finally {
 if(!path.resolve(workspace).startsWith(base+path.sep))throw new Error('Fixture cleanup outside owned .tmp refused.');
 fs.rmSync(workspace,{recursive:true,force:true});
}
