"""AST-only full prepare path with synthetic metadata and generic text fixtures."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,copy,json,hashlib
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[4]
HELPER=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/review_table_index_fidelity_v1.py'
EXPECTED='4979e0b711cee17d79ecad4ebee99fc995b53238c2534377a53d3cd6398f56ae'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert digest(HELPER)==EXPECTED
 tree=ast.parse(HELPER.read_text(encoding='utf8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
 out=HERE/'index-fidelity-v1-independent';out.mkdir(exist_ok=False);base=out/'synthetic';base.mkdir()
 snap=base/'snapshot';source=base/'original';output=base/'drafts';jobs=base/'jobs';runtime=base/'runtime';report=base/'report'
 for p in [snap,source,output,jobs,runtime,report,jobs/'review']:p.mkdir(parents=True,exist_ok=True)
 reference=snap/'reference.md';reference.write_text('SYNTHETIC REFERENCE\n',encoding='utf8');original=source/'original.md';original.write_text('SYNTHETIC REFERENCE\n',encoding='utf8')
 doc=output/'synthetic.md';doc.write_text('# SYNTHETIC\n',encoding='utf8')
 pin=report/'pin.json';draft=jobs/'draft.json';review=jobs/'review/review-verified.json';handoff=review.with_name('review-handoff.json');plan=jobs/'plan-verified.json';planhandoff=plan.with_name('plan-handoff.json');contract=base/'contract.json';rt=report/'runtime.json';statehelper=base/'run_state_projection_v6.py';selfpath=base/'wrapper.py'
 cap={'manifestSha256':'b'*64};parent='a'*64;rootpin='c'*64;refsha='d'*64;helpersha='e'*64;planSHA='f'*64
 files={f'f{i:03d}.py':'0'*64 for i in range(124)}
 records={pin:{'documentId':'SYNTHETIC','sha256':parent,'capsule':cap,'independentReviewApproved':True,'canonicalMarkdown':str(doc),'draftResult':str(draft),'independentReview':str(review),'draftResultSha256':'1'*64,'independentReviewSha256':'2'*64},
  draft:{'contentSha256':parent,'snapshot':cap,'referenceMode':'training-assisted'},review:{'documentId':'SYNTHETIC','approved':True,'unresolved':[],'findings':[]},
  handoff:{'documentSha256':parent,'reviewSha256':'2'*64,'snapshot':cap,'documentFile':str(doc),'approved':True,'referenceMode':'training-assisted'},
  planhandoff:{'planSha256':planSHA,'snapshot':cap},rt:{'destination':str(runtime),'fileCount':124,'files':files,'imports':{}},
  plan:{'documents':[{'id':'SYNTHETIC','path':'synthetic.md','kind':'table-index'}]}}
 hashes={snap/'manifest.json':'b'*64,contract:'3'*64,plan:planSHA,rt:'4'*64,pin:rootpin,statehelper:helpersha,reference:refsha,original:refsha,doc:parent,draft:'1'*64,review:'2'*64,handoff:'5'*64,planhandoff:'6'*64,selfpath:'7'*64}
 manifest={'mode':'training-assisted','trainingReferenceAuthorizedByUser':True,'referenceSpecificationIncluded':True,'sourceRoot':str(source),'files':[],'referenceFiles':[{'path':'reference.md','sha256':refsha,'originalPath':str(original),'lines':91}]}
 results=[]
 def probe(name,change=None,expected=True):
  local=copy.deepcopy(records);h=dict(hashes);m=copy.deepcopy(manifest);counts={'provider':0,'originalApplication':0};inv=copy.deepcopy(files)
  if change:change(local,h,m,inv)
  def safe(p):return Path(p)
  def under(p,root,file=False):
   p=Path(p)
   if not p.is_relative_to(root):raise ValueError('synthetic scope violation')
   return p
  def state_assert(meta):
   if h[snap/'manifest.json']!='b'*64 or h[rt]!='4'*64 or any(h[Path(p)]!=s for p,s in meta['pinnedFiles'].items()) or inv!=meta['runtimeInventory']['files']:raise ValueError('synthetic drift')
  capsule=SimpleNamespace(safe_path=safe,verify=lambda _:copy.deepcopy(m),verification_state=lambda _:copy.deepcopy(cap))
  state=SimpleNamespace(SNAPSHOT=snap,MANIFEST_SHA='b'*64,CONTRACT=contract,CONTRACT_SHA='3'*64,PLAN=plan,PLAN_SHA=planSHA,RUNTIME_RECORD=rt,RUNTIME_RECORD_SHA='4'*64,RUNTIME_DIRECTORY=runtime,SOURCE_ROOT=source,OUTPUT=output,BASE=base,REPORT=report,MODE='training-assisted',capsule=capsule,__file__=str(statehelper),under=under,runtime_inventory=lambda _:copy.deepcopy(inv),runtime_module_pins=lambda *_:{'synthetic':'exact'},assert_unchanged=state_assert,validate_document=lambda *_a,**_k:[],workflow=SimpleNamespace(select_document=lambda *_:local[plan]['documents'][0]))
  env={'state':state,'Path':Path,'sha':lambda p:h[Path(p)],'load':lambda p:copy.deepcopy(local[Path(p)]),'DOCUMENT_ID':'SYNTHETIC','PARENT_SHA':parent,'PIN':pin,'PIN_SHA':rootpin,'REFERENCE':'reference.md','REFERENCE_SHA':refsha,'HELPER_SHA':helpersha,'SCOPE':'original-design-all-sections-source-fidelity','__file__':str(selfpath)}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HELPER),'exec'),env)
  accepted=True
  try:env['prepare']()
  except (ValueError,KeyError,StopIteration):accepted=False
  results.append({'name':name,'expectedAccepted':expected,'actualAccepted':accepted,'matchesExpected':accepted==expected,'providerCalls':0})
  return accepted
 assert probe('normal synthetic exact binding')
 for path in [snap/'manifest.json',contract,plan,rt,pin,statehelper,doc,draft,review,reference,original]:
  assert not probe('fixed SHA drift '+path.name,lambda r,h,m,i,p=path:h.update({p:'9'*64}),False)
 for field in ['mode','trainingReferenceAuthorizedByUser','referenceSpecificationIncluded','sourceRoot']:
  assert not probe('manifest '+field+' drift',lambda r,h,m,i,f=field:m.update({f:False if f.endswith('Included') or f.endswith('ByUser') else 'wrong'}),False)
 for field in ['documentId','sha256','capsule','independentReviewApproved']:
  assert not probe('root pin '+field+' drift',lambda r,h,m,i,f=field:r[pin].update({f:False if f=='independentReviewApproved' else 'wrong'}),False)
 for field in ['documentSha256','reviewSha256','snapshot','documentFile']:
  assert not probe('old handoff '+field+' drift',lambda r,h,m,i,f=field:r[handoff].update({f:'wrong'}),False)
 for field in ['approved','referenceMode']:
  assert probe('old handoff unchecked '+field,lambda r,h,m,i,f=field:r[handoff].update({f:False if f=='approved' else 'source-only'}),False)
 for field in ['planSha256','snapshot']:
  assert probe('plan handoff unchecked '+field,lambda r,h,m,i,f=field:r[planhandoff].update({f:'wrong'}),False)
 assert not probe('full124 inventory missing',lambda r,h,m,i:i.pop('f000.py'),False)
 mainfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');calls=[n for n in ast.walk(mainfn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_bound_job']
 assert len(calls)==1 and calls[0].args[1].right.value=='independent-review'
 assert digest(HELPER)==EXPECTED
 report={'schema':'independent-code-only-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(HELPER),'helperSha256':EXPECTED,'status':'REQUIRES_FRESH_GUARD_FIX','syntheticCases':results,'caseCount':len(results),'acceptedNegativeCases':[r for r in results if not r['matchesExpected']],'actualProductionMaterialRead':False,'providerCalls':0,'helperImportedOrMainExecuted':False,'findings':[{'severity':'major','location':'prepare: paths list / plan-handoff.json','message':'Plan handoff bytes are pinned but its planSha256 and capsule snapshot are not checked; wrong values pass synthetic full prepare.','fix':'Load the handoff and require exact PLAN_SHA and capsule_state before accepting pins.'},{'severity':'major','location':'prepare: reviewed handoff condition','message':'An unapproved or wrong-mode review handoff passes synthetic full prepare although other parent/review hashes are bound.','fix':'Require handoff.approved is True and handoff.referenceMode equals MODE.'}],'astChecks':{'onlyOneIndependentReviewProviderCall':True,'noCanonicalWrite':True},'limits':['This is code-only technical delta review, not original-design or specification content review.','No complete race-free or inert execution guarantee is established.']}
 p=out/'review.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':str(p),'sha256':digest(p),'cases':len(results),'acceptedNegative':len(report['acceptedNegativeCases'])},ensure_ascii=False))
if __name__=='__main__':main()
