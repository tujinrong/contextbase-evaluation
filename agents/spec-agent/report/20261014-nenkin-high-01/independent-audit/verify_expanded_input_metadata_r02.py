"""Read-only independently verify expanded input, byte hashes, and infrastructure provenance."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, importlib, importlib.util, json, sys
sys.dont_write_bytecode = True
REPO = Path(r'D:/開発/contextbase-evaluation')
RUN = REPO/'agents/spec-agent/.tmp/20261014-nenkin-high-01'
REPORT = REPO/'agents/spec-agent/report/20261014-nenkin-high-01'
HERE = Path(__file__).resolve().parent
INPUT = REPO/'agents/reverse-agent/input'
OUTPUT = REPO/'agents/reverse-agent/output'
CAP = RUN/'snapshot-input-02'
CAP_SHA = 'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445'
OLD_CAP_SHA = '92c339cb7040019312d0ec01669d22c44e4cc73fa373d5278c3f6f04c0c09631'
CONTEXT = RUN/'execution-context-input-02.json'
CONTEXT_SHA = '8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605'
FEEDBACK = RUN/'plan-input-expansion-context-r01.json'
FEEDBACK_SHA = 'e087eac587641bb374f107208f143209151b576c4b617729eee7fb97bd8fd810'
RECEIPT = REPO/'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/runtime-code-source-13.json'
RECEIPT_SHA = '5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79'
EXTRAS = {'nenkin/README.md', 'nenkin/.classpath', 'nenkin/.project', 'nenkin/.gitignore'}
def safe(p):
 p = Path(p).absolute()
 for a in (p, *p.parents):
  if a.is_symlink() or a.exists() and getattr(a.lstat(),'st_file_attributes',0)&0x400:
   raise ValueError('Linked path refused before read: '+str(a))
 return p.resolve()
def raw(p): return safe(p).read_bytes()
def sha(p): return hashlib.sha256(raw(p)).hexdigest()
def pairs(items):
 d = {}
 for k,v in items:
  assert k not in d, 'Duplicate JSON member'
  d[k]=v
 return d
def load(p): return json.loads(raw(p).decode('utf-8-sig'),object_pairs_hook=pairs)
def inventory(root, cache=False):
 root=safe(root);result={}
 def descend(d):
  for p in sorted(safe(d).iterdir()):
   p=safe(p)
   if cache and ('__pycache__' in p.parts or p.suffix=='.pyc'): continue
   if p.is_dir(): descend(p)
   elif p.is_file(): result[p.relative_to(root).as_posix()]=sha(p)
   else: raise ValueError('Unsupported entry')
 descend(root)
 return result
def ast_functions(p):
 return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw(p)).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert sha(RECEIPT)==RECEIPT_SHA
receipt=load(RECEIPT);runtime=safe(receipt['destination'])
runtime_before=inventory(runtime,True)
assert len(runtime_before)==128 and runtime_before==receipt['files'] and len(receipt['imports'])==13
protected_file=REPORT/'protected-inputs-before.json';protected_sha=sha(protected_file)
protected={e['path']:e['sha256'] for e in load(protected_file)['files']}
assert len(protected)==345 and inventory(INPUT)==protected
oldcap=RUN/'snapshot';assert sha(oldcap/'manifest.json')==OLD_CAP_SHA
assert sha(CAP/'manifest.json')==CAP_SHA and sha(CONTEXT)==CONTEXT_SHA and sha(FEEDBACK)==FEEDBACK_SHA
manifest=load(CAP/'manifest.json');oldmanifest=load(oldcap/'manifest.json')
oldentries={e['path']:e for e in oldmanifest['files']};newentries={e['path']:e for e in manifest['files']}
assert len(oldentries)==len(oldmanifest['files'])==175
assert len(newentries)==len(manifest['files'])==179 and set(newentries)-set(oldentries)==EXTRAS
assert not set(oldentries)-set(newentries)
assert all(newentries[p]==e for p,e in oldentries.items())
assert manifest['mode']=='source-only' and manifest['projectId']=='nenkin' and manifest['referenceFiles']==[]
assert manifest['referenceSpecificationIncluded'] is False and manifest['sourceBytesModified'] is False
assert manifest['semanticAnalysisPerformedByPython'] is False
assert manifest['priorSourceCapsuleManifestSha256']==OLD_CAP_SHA
sys.path.insert(0,str(runtime))
loaded={}
def module_pin(name,expected):
 expected=safe(expected);found=importlib.util.find_spec(name)
 assert found and safe(found.origin)==expected
 module=importlib.import_module(name)
 assert safe(module.__file__)==safe(module.__spec__.origin)==expected
 assert sha(expected)==runtime_before[expected.relative_to(runtime).as_posix()]
 return {'path':str(expected),'sha256':sha(expected)}
for name,p in receipt['imports'].items(): loaded[name]=module_pin(name,p)
critical={name:module_pin(name,runtime/(name.replace('.','/')+'.py')) for name in (
 'contextbase.ai.capsule','contextbase.ai.workflow','contextbase.ai.provider','contextbase.ai.prompts',
 'contextbase.ai.schemas','contextbase.ai.validation','contextbase.ai.plan_review')}
capsule=importlib.import_module('contextbase.ai.capsule')
assert capsule.verify(oldcap)==oldmanifest and capsule.verify(CAP)==manifest
state=capsule.verification_state(CAP)
assert state['manifestSha256']==CAP_SHA and state['mode']=='source-only'
extra_pins=[]
for p,e in newentries.items():
 assert p.split('/')[0] in {'nenkin','n2framework'} and p in protected
 assert sha(CAP/'sources'/p)==protected[p]==e['sha256']
 if p in oldentries:
  assert raw(CAP/'sources'/p)==raw(oldcap/'sources'/p)
  assert raw(CAP/('indexed/'+p+'.txt'))==raw(oldcap/('indexed/'+p+'.txt'))
 else:
  b=raw(INPUT/p);text,encoding=capsule.decode(b);lines=text.splitlines(keepends=True)
  indexed=''.join(f'{i:06d} | {line}' for i,line in enumerate(lines,1)).encode('utf-8')
  assert raw(CAP/'sources'/p)==b and e['bytes']==len(b) and e['encoding']==encoding and e['lines']==len(lines)
  assert e['indexed']=='indexed/'+p+'.txt' and raw(CAP/('indexed/'+p+'.txt'))==indexed
  extra_pins.append({'path':p,'sha256':e['sha256'],'bytes':len(b),'lineCount':len(lines),'indexedSha256':sha(CAP/('indexed/'+p+'.txt'))})
context=load(CONTEXT)
assert context['sourceSnapshotManifestSha256']==CAP_SHA and context['sourceOnly'] is True
assert context['agentRole']=='AG-SPEC' and context['projectId']=='nenkin'
assert context['primaryDocumentationSourcePaths']==['nenkin/README.md']
assert set(context['primaryProjectConfigurationSourcePaths'])==EXTRAS-{'nenkin/README.md'}
assert context['externalReferencedMaterialReadAuthorized'] is False
assert context['originalSpecificationsAuthorized'] is False and context['evaluationExpectationsAuthorized'] is False
assert context['originalProgramsAndDatabaseExecutionAuthorized'] is False
feedback=load(FEEDBACK)
assert feedback['executionContext']==context and set(feedback['additionalSourcePaths'])==EXTRAS
assert feedback['businessFactsOrCorrectionsAssembledByPython'] is False
assert feedback['previousPlanSha256']=='f6f63186086b33a76cb26f448b7e9052dc16bc5f47236bcdb477254de2646048'
assert hashlib.sha256(raw(RUN/'jobs/plan-02/plan-verified.json')).hexdigest()==feedback['previousPlanSha256']
# Do not inspect old plan semantic prose: only ensure exact decoded AI object linkage.
assert feedback['previousAiPlan']==load(RUN/'jobs/plan-02/plan-verified.json')
packer1=RUN/'prepare_input_expansion_r01.py';packer2=RUN/'prepare_input_expansion_r02.py'
assert sha(packer1)=='aefac3c4d9e2fe525f9b4adc2fc458da8f11bc1770d516fb86d95d1e98d7b585'
assert sha(packer2)=='280907105057ed72927168f28a1e33eeea366bfc5c545fc605b6af51900c0f23'
p1,p2=ast_functions(packer1),ast_functions(packer2)
assert set(p1)==set(p2) and all(p1[k]==p2[k] for k in p1 if k!='main')
wrapper1=RUN/'review_plan_with_scope_r01.py';wrapper2=RUN/'review_plan_with_scope_r02.py'
assert sha(wrapper1)=='6cb4ca230efe445912a1ca6daa28148edfa764d3bd300d2cb0fae91c247ea2e5'
assert sha(wrapper2)=='52fb03f78b07ab9136881ece1ed76ac29a35ade053c77af9f8596d4300e0d98e'
assert ast_functions(wrapper1)==ast_functions(wrapper2)
def top_assigns(p):
 return {tuple(ast.unparse(t) for t in n.targets):ast.dump(n.value,include_attributes=False) for n in ast.parse(raw(p)).body if isinstance(n,ast.Assign)}
w1,w2=top_assigns(wrapper1),top_assigns(wrapper2)
changed=[k for k in w1 if w1[k]!=w2[k]]
assert set(w1)==set(w2) and set(changed)=={('SNAPSHOT',),('SNAPSHOT_SHA',),('CONTEXT',),('CONTEXT_SHA',)}
output_baseline=load(HERE/'output-inventory-publish-baseline-r01.json')
output_before=inventory(OUTPUT)
assert len(output_before)==906 and output_before==output_baseline['files']
assert inventory(INPUT)==protected and sha(protected_file)==protected_sha
assert inventory(runtime,True)==runtime_before and sha(RECEIPT)==RECEIPT_SHA
assert inventory(OUTPUT)==output_before
assert sha(CONTEXT)==CONTEXT_SHA and sha(FEEDBACK)==FEEDBACK_SHA
assert sha(CAP/'manifest.json')==CAP_SHA and capsule.verify(CAP)==manifest and capsule.verification_state(CAP)==state
assert sha(oldcap/'manifest.json')==OLD_CAP_SHA and capsule.verify(oldcap)==oldmanifest
result={'schema':'spec-agent-independent-expanded-input-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'status':'PASS_METADATA_AND_CODE_DELTA','snapshot':str(CAP),'manifestSha256':CAP_SHA,'protectedInputCount':345,
 'priorSourceCount':175,'expandedSourceCount':179,'priorSourcesAndIndexedBytesExact':True,'additionalFiles':extra_pins,
 'expandedSubsetMatchesProtectedOriginals':True,'originalInputFullBeforeAfterExact':True,'oldCapsuleBeforeAfterExact':True,
 'contextSha256':CONTEXT_SHA,'feedbackSha256':FEEDBACK_SHA,'runtimeReceiptSha256':RECEIPT_SHA,
 'runtimeFullFiles':128,'runtimeImports':loaded,'criticalModules':critical,'outputFileCount':906,
 'oldOutputCurrentInventoryMatchesPublishBaseline':True,'oldOutputAuditBeforeAfterExact':True,
 'packerR02FinalRecheckAdded':True,'scopedWrapperR02Sha256':sha(wrapper2),'wrapperAllFunctionAstsUnchanged':True,
 'wrapperChangedConstants':['SNAPSHOT','SNAPSHOT_SHA','CONTEXT','CONTEXT_SHA'],
 'targetApplicationDatabaseScriptsExecuted':False,'providerExecuted':False,'oldOutputBusinessBodyRead':False,
 'expectedOrRubricRead':False,'formalScore':None,'published':False,
 'limitations':['Hash/index verification does not prove source semantic coverage or dependency reachability.',
 'Project README/config declarations are observed input text, not runtime behavior.',
 'Old plan-review02 belongs to the prior seal and is not transferred to the expanded scope.',
 'Trusted frozen infrastructure was imported for verification; no target application or script was imported/executed.']}
target=HERE/'expanded-input-review-r02.json'
with safe(target).open('x',encoding='utf-8',newline='\n') as f: json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'report':str(target),'sha256':sha(target),'sourceCount':179,'protectedInputCount':345,'runtimeFiles':128,'imports':13,'critical':7,'outputFiles':906}))
