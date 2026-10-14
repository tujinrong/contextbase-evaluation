"""Independent source state-review audit: AST nodes plus synthetic metadata only."""
from __future__ import annotations
import ast,copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from jsonschema import Draft202012Validator
HERE=Path(__file__).resolve().parent;HELPER=HERE.parent/'source-pilot/review_state_projection.py'
EXPECTED='c9d0d3afdbc3af98cebdcc2bf50c768022ba661d03f63922fb23231bbd7070a9'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(ns,nodes):exec(compile(ast.Module(body=nodes,type_ignores=[]),'<synthetic-ast-only>','exec'),ns)
def main():
 out=HERE/'state-review-helper-independent-r01';out.mkdir(exist_ok=False);assert sha(HELPER)==EXPECTED
 tree=ast.parse(HELPER.read_text(encoding='utf-8'));ifs=[n for n in tree.body if isinstance(n,ast.If)];cases=[]
 def probe(name,fn,accept):
  try:fn();actual=True;err=None
  except Exception as exc:actual=False;err=type(exc).__name__+': '+str(exc)
  cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':accept==actual,'error':err})
 def guard(fragment):return next(n for n in ifs if fragment in ast.unparse(n))
 manifest_sha='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b';docsha='a'*64;rawsha='b'*64
 capstate={'manifestSha256':manifest_sha,'mode':'source-only'}
 h={'snapshot':capstate,'reviewScope':'STATIC_PROJECTION_VS_SOURCE_RESOURCES','status':'AI_STATIC_PROJECTION_REQUIRES_INDEPENDENT_REVIEW','canonicalRevisionRequiredStates':[],'documents':[{'file':'C:/synthetic/draft.md','sha256':docsha}]}
 projection_guard=guard('complete exact-parent source-only projection')
 for kind in ['correct','wrong-mode','wrong-cap','wrong-scope','wrong-status','revision','count']:
  candidate=copy.deepcopy(h)
  if kind=='wrong-mode':candidate['snapshot']['mode']='training-assisted'
  elif kind=='wrong-cap':candidate['snapshot']['manifestSha256']='c'*64
  elif kind=='wrong-scope':candidate['reviewScope']='OTHER'
  elif kind=='wrong-status':candidate['status']='OTHER'
  elif kind=='revision':candidate['canonicalRevisionRequiredStates']=['normal']
  elif kind=='count':candidate['documents']*=2
  probe('handoff-'+kind,lambda c=candidate:run({'handoff':c,'state':capstate},[projection_guard]),kind=='correct')
 rawguard=guard('raw projection does not bind exact source and parent')
 for kind in ['correct','wrong-cap','wrong-parent']:
  candidate={'snapshotManifestSha256':manifest_sha,'boundDraftSha256s':[docsha]}
  if kind=='wrong-cap':candidate['snapshotManifestSha256']='c'*64
  elif kind=='wrong-parent':candidate['boundDraftSha256s']=['c'*64]
  probe('raw-projection-'+kind,lambda c=candidate:run({'projection':c,'manifest_sha':manifest_sha,'document_sha':docsha},[rawguard]),kind=='correct')
 docguard=guard('canonical differs from explicit parent SHA')
 for kind,caller,hashval in [('correct',docsha,docsha),('caller','c'*64,docsha),('handoff',docsha,'c'*64)]:
  candidate=copy.deepcopy(h);candidate['documents'][0]['sha256']=hashval
  probe('parent-'+kind,lambda c=candidate,x=caller:run({'document_sha':docsha,'args':SimpleNamespace(document_sha256=x),'handoff':c},[docguard]),kind=='correct')
 # Concrete gap: fixed manifest bytes check before verify, but no fixed state pin after.
 initial=guard('fixed source-only manifest differs before input collection');wrongstate={'manifestSha256':'c'*64,'mode':'source-only'}
 assignments=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'manifest','state'}]
 def fixed_cap_race():
  ns={'snapshot':Path('C:/synthetic/snapshot'),'manifest_sha':manifest_sha,
    'capsule':SimpleNamespace(material_path=lambda *a:SimpleNamespace(read_bytes=lambda:b'synthetic-initial'),sha256=lambda b:manifest_sha,
      verify=lambda p:{'mode':'source-only','referenceFiles':[],'sourceRoot':'C:/synthetic/source'},verification_state=lambda p:wrongstate)}
  run(ns,[initial,*assignments]);candidate=copy.deepcopy(h);candidate['snapshot']=wrongstate
  run({**ns,'handoff':candidate},[projection_guard]);run({'projection':{'snapshotManifestSha256':manifest_sha,'boundDraftSha256s':[docsha]},'manifest_sha':manifest_sha,'document_sha':docsha},[rawguard])
 probe('fixed-cap-verification-state-drift-reproduction',fixed_cap_race,False)
 # Full inventory byte comparison catches additions/deletions/drift, but links bypass safe_path.
 inventory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inventory')
 class File:
  parts=('synthetic','module.py');suffix='.py'
  def __init__(self,name,data,linked=False):self.name=name;self.data=data;self.linked=linked
  def relative_to(self,r):return Path(self.name)
  def is_file(self):return True
  def read_bytes(self):return self.data
 files=[File('module.py',b'original')];safe_calls=[]
 ns={'runtime':SimpleNamespace(rglob=lambda p:list(files)), 'capsule':SimpleNamespace(sha256=lambda b:hashlib.sha256(b).hexdigest(),safe_path=lambda p:safe_calls.append(p))};run(ns,[inventory])
 expected_inventory={'module.py':hashlib.sha256(b'original').hexdigest()}
 def compare(kind):
  old=list(files)
  if kind=='added':files.append(File('added.py',b'new'))
  elif kind=='deleted':files.clear()
  elif kind=='bytes':files[0]=File('module.py',b'drift')
  try:
   if ns['inventory']()!=expected_inventory:raise ValueError('Synthetic inventory drift')
  finally:files[:]=old
 for kind in ['same','added','deleted','bytes']:probe('inventory-'+kind,lambda k=kind:compare(k),kind=='same')
 def linked_inventory():
  prior=list(files);files[:]=[File('module.py',b'original',True)]
  try:ns['inventory']()
  finally:files[:]=prior
 probe('linked-runtime-file-boundary-reproduction',linked_inventory,False)
 answer_guard=guard('approved review contradicts its state verdicts/findings');revision_guard=guard('canonical revision finding requires the top-level pause flag')
 def answer(kind):
  a={'approved':True,'requiresCanonicalRevision':False,'states':[{'approved':True}]*4,'findings':[]}
  if kind=='revision':a['requiresCanonicalRevision']=True
  elif kind=='state':a['states']=[{'approved':False}]*4
  elif kind=='finding':a['findings']=[{'requiresCanonicalRevision':False}]
  elif kind=='unpropagated':a.update({'approved':False,'findings':[{'requiresCanonicalRevision':True}]})
  elif kind=='pause':a.update({'approved':False,'requiresCanonicalRevision':True,'findings':[{'requiresCanonicalRevision':True}]})
  run({'answer':a},[answer_guard,revision_guard])
 for kind in ['correct','revision','state','finding','unpropagated','pause']:probe('review-answer-'+kind,lambda k=kind:answer(k),kind in ['correct','pause'])
 schema_nodes=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'ref_schema','location_schema','state_schema','finding_schema','schema'}]
 schema_ns={'ids':['normal','empty','tooMany','viewer'],'manifest_sha':manifest_sha,'document_sha':docsha,'raw_sha':rawsha};run(schema_ns,schema_nodes)
 def transport():
  schema=schema_ns['schema'];Draft202012Validator.check_schema(schema);assert json.loads(json.dumps(schema))==schema;pending=[schema]
  while pending:
   value=pending.pop()
   if isinstance(value,dict):
    if ('enum' in value or 'const' in value) and 'type' not in value:raise ValueError('Untyped enum')
    pending.extend(value.values())
   elif isinstance(value,list):pending.extend(value)
 probe('actual-review-schema-typed-enums-serialization',transport,True)
 static={'providerTopLevelWasNotExecuted':True,'sourceOtherModeBusinessWasNotRead':True,'postVerificationFixedCapCheckMissing':True,
  'runtimeInventorySafePathPerFileMissing':not safe_calls,'actualImportProvenanceWorkflowOnly':True,
  'canonicalReviewExactBytesModeParentGuardsPresent':True,'fourStatesAndEvidenceAndStrictCanonicalRangeGatesPresent':True,
  'nativeRuntimeFormalApprovalFlagsRemainFalse':True}
 assert sha(HELPER)==EXPECTED
 findings=[{'severity':'major','issue':'Fixed cap bytes checked only before verify. Independently verify fixed verification_state manifest SHA and fixed actual manifest bytes after collection, before provider and after provider.','syntheticReproduction':'fixed-cap-verification-state-drift-reproduction'},
 {'severity':'major','issue':'inventory reads each runtime file directly without safe_path; link/reparse boundary not enforced by this enumeration.','syntheticReproduction':'linked-runtime-file-boundary-reproduction'},
 {'severity':'minor','issue':'workflow import is the only checked actual module. Freeze inventory equality alone does not establish loaded capsule/provider/prompts/validation provenance. Either bind them or limit the claimed runtime scope.'}]
 report={'schema':'source-state-review-helper-code-only-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'CHANGES_REQUIRED','helper':str(HELPER),'helperSha256':EXPECTED,'helperUnchanged':True,'cases':cases,'caseCount':len(cases),'expectedMatches':sum(c['pass'] for c in cases),'missingRejectionReproductions':sum(not c['pass'] for c in cases),'findings':findings,'staticChecks':static,'providerInvocations':0,'helperTopLevelInvocations':0,'originalSourceSpecEvalOrOtherModeBusinessRead':False,'productionInputsInspected':False,'completeInertnessProven':False,'actualTransportProviderAcceptanceVerified':False}
 path=out/'review.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(path),'sha256':sha(path),'cases':len(cases),'matches':report['expectedMatches'],'missingRejections':report['missingRejectionReproductions'],'status':'CHANGES_REQUIRED'}))
if __name__=='__main__':main()
