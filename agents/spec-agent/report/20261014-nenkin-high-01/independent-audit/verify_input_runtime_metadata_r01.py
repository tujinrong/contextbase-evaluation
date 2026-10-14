"""Read-only byte hashes and trusted infrastructure imports; no target execution."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,sys,importlib
sys.dont_write_bytecode=True
REPO=Path(r'D:/開発/contextbase-evaluation')
RUN=REPO/'agents/spec-agent/.tmp/20261014-nenkin-high-01'
REPORT=REPO/'agents/spec-agent/report/20261014-nenkin-high-01'
HERE=Path(__file__).resolve().parent
INPUT=REPO/'agents/reverse-agent/input';OUTPUT=REPO/'agents/reverse-agent/output'
RECEIPT=REPO/'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/runtime-code-source-13.json'
CAPSHA='92c339cb7040019312d0ec01669d22c44e4cc73fa373d5278c3f6f04c0c09631'
RECSHA='5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79'
def safe(p):
 p=Path(p).absolute()
 for a in [p,*p.parents]:
  if a.exists() and (a.is_symlink() or getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path refused before read: '+str(a))
 return p.resolve()
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_text(encoding='utf-8-sig'))
def inventory(root,exclude_cache=False):
 root=safe(root);files={}
 if not root.exists():return files
 def descend(d):
  d=safe(d)
  for p in sorted(d.iterdir()):
   p=safe(p)
   if exclude_cache and ('__pycache__' in p.parts or p.suffix=='.pyc'):continue
   if p.is_dir():descend(p)
   elif p.is_file():files[p.relative_to(root).as_posix()]=sha(p)
   else:raise ValueError('Unsupported entry')
 descend(root);return files
assert sha(RECEIPT)==RECSHA
receipt=load(RECEIPT);runtime=safe(receipt['destination'])
before_runtime=inventory(runtime,True);assert before_runtime==receipt['files'] and len(before_runtime)==128
cap=RUN/'snapshot';capmanifest=cap/'manifest.json';assert sha(capmanifest)==CAPSHA
manifest=load(capmanifest);assert manifest['projectId']=='nenkin' and manifest['mode']=='source-only'
assert manifest['referenceFiles']==[] and manifest['referenceSpecificationIncluded'] is False
assert manifest['sourceBytesModified'] is False and manifest['semanticAnalysisPerformedByPython'] is False
baselinep=REPORT/'protected-inputs-before.json';baseline=load(baselinep)
protected={e['path']:e['sha256'] for e in baseline['files']};assert len(protected)==345
before_input=inventory(INPUT);assert before_input==protected
subset={e['path']:e['sha256'] for e in manifest['files']};assert len(subset)==175 and len(subset)==len(manifest['files'])
assert all(protected[p]==h for p,h in subset.items())
assert {p for p in subset if p.split('/')[0] not in {'nenkin','n2framework'}}==set()
assert all(sha(cap/'sources'/p)==h for p,h in subset.items())
assert all(not p.lower().startswith(('spec/','spec-eval/')) and '/spec-eval/' not in p.lower() for p in subset)
sys.path.insert(0,str(runtime))
loaded={}
for name,expected in receipt['imports'].items():
 module=importlib.import_module(name);path=safe(module.__file__)
 assert path==safe(expected) and path.is_relative_to(runtime)
 rel=path.relative_to(runtime).as_posix();assert sha(path)==before_runtime[rel]
 loaded[name]={'path':str(path),'sha256':sha(path)}
assert len(loaded)==13
capsule=importlib.import_module('contextbase.ai.capsule');cp=safe(capsule.__file__)
assert cp==runtime/'contextbase/ai/capsule.py' and sha(cp)==before_runtime['contextbase/ai/capsule.py']
state=capsule.verification_state(cap)
assert state['manifestSha256']==CAPSHA and state['mode']=='source-only'
critical=['contextbase.ai.workflow','contextbase.ai.provider','contextbase.ai.prompts','contextbase.ai.schemas','contextbase.ai.validation','contextbase.ai.capsule']
critical_loaded={}
for name in critical:
 module=importlib.import_module(name);path=safe(module.__file__)
 rel=path.relative_to(runtime).as_posix();assert sha(path)==before_runtime[rel]
 critical_loaded[name]={'path':str(path),'sha256':sha(path)}
output_before=inventory(OUTPUT)
output_baseline={'schema':'spec-agent-output-change-baseline/1','createdUtc':datetime.now(timezone.utc).isoformat(),'outputRoot':str(OUTPUT),'exists':OUTPUT.exists(),'fileCount':len(output_before),'files':output_before,'scope':'Current raw-byte SHA inventory for future publish-time drift detection. Not a historical before/after proof of prepare_run execution.','oldOutputBodyReadByReviewer':False,'oldOutputProvidedToAiAuthor':False}
outbase=HERE/'output-inventory-publish-baseline-r01.json';assert not outbase.exists()
outbase.write_text(json.dumps(output_baseline,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert inventory(INPUT)==before_input==protected
assert inventory(runtime,True)==before_runtime==receipt['files']
assert inventory(OUTPUT)==output_before
assert sha(RECEIPT)==RECSHA and sha(capmanifest)==CAPSHA
capsule.verify(cap);afterstate=capsule.verification_state(cap);assert afterstate==state
registry=REPO/'agents/reverse-agent/ContextBase/identities.json';registrysha=sha(registry)
context=load(RUN/'execution-context.json');assert context['identityRegistrySha256']==registrysha
assert context['agentRole']=='AG-SPEC' and context['projectId']=='nenkin' and context['sourceOnly'] is True
assert context['originalSpecificationsAuthorized'] is False and context['evaluationExpectationsAuthorized'] is False
assert context['originalProgramsAndDatabaseExecutionAuthorized'] is False
result={'schema':'spec-agent-independent-input-runtime-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'PASS_METADATA_ONLY','projectId':'nenkin','agentRole':'AG-SPEC','snapshot':str(cap),'sourceSnapshotManifestSha256':CAPSHA,'referenceMode':'source-only','protectedInputCount':345,'sourceSubsetCount':175,'inputFullMembershipAndBytesMatchOriginalBefore':True,'snapshotSubsetMatchesProtectedOriginals':True,'snapshotSourceFilesAllMatchOriginalHashes':True,'snapshotVerifyBeforeAfterSame':True,'runtimeReceipt':str(RECEIPT),'runtimeReceiptSha256':RECSHA,'runtimeRoot':str(runtime),'runtimeFileCount':128,'runtimeFullInventoryBeforeAfterExact':True,'runtimeImports':loaded,'criticalLoadedModules':critical_loaded,'loadedImportCount':13,'criticalModuleCount':6,'identityRegistrySafePathAndShaCurrentMatch':True,'outputBaseline':str(outbase),'outputBaselineSha256':sha(outbase),'outputCurrentFileCount':len(output_before),'outputBeforeAfterDuringThisAuditExact':True,'sourceApplicationDatabaseOrScriptsExecuted':False,'providerExecuted':False,'productionPlanExecutedByReviewer':False,'canonicalOrExistingSpecificationBodyRead':False,'expectedOrTargetSpecEvalRead':False,'oldAspNetBusinessOrScoreTransferred':False,'limitations':['Raw source/output/runtime bytes were read only for SHA computation; no target program or script was executed.','Output inventory starts now; it is not retroactive proof that the earlier prepare_run left output bytes unchanged.','Trusted frozen infrastructure modules were imported solely for exact provenance and capsule verification. Imported module count is separate from target application execution.','Full source coverage and framework dependency reachability remain pending independent plan review.']}
out=HERE/'input-runtime-review-r01.json';assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['status'],'protected':345,'subset':175,'runtimeFiles':128,'imports':13,'critical':6,'outputFiles':len(output_before),'report':str(out),'sha256':sha(out),'outputBaselineSha256':sha(outbase)}))
