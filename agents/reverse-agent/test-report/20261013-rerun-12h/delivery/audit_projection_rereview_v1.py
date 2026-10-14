"""Code-only AST extraction, synthetic metadata, never import/run the provider helper."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,copy,json,hashlib
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[4]
HELPER=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/rerun_projection_review_v1.py'
EXPECTED='1235842ca4d0e7f3dec12b69b9835b0bbf71353298aaa0bf0599421a240ef263'
STATE='dea405e860904d3cff89a1de675a5c8b0270d24bad76f9005c90518f140ca78f'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert digest(HELPER)==EXPECTED
 tree=ast.parse(HELPER.read_text(encoding='utf8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bind_existing_projection')
 base=Path('D:/synthetic/own');job=base/'state-projections/old';parent={'sha256':'a'*64,'path':'synthetic.md'};item={'id':'SYNTHETIC'};caps={'manifestSha256':'b'*64}
 old={'parent':parent,'capsule':caps,'documentId':item['id'],'mode':'training-assisted','helperSha256':STATE,'runtimeRecordSha256':'c'*64}
 doc={'states':[{'requiresCanonicalRevision':False,'html':'<p>literal</p>'}]};review={'documentId':item['id'],'parentDocumentSha256':parent['sha256'],'projectionSha256':'d'*64,'approved':False}
 required=['input-pins.json','projection-verified.json','projection-review-verified.json','input-after.json','projection-result.json']+['projection/'+x for x in ['prompt.txt','schema.json','events.jsonl','result.json','stderr.log']]
 original={job/'input-pins.json':old,job/'projection-verified.json':doc,job/'projection-review-verified.json':review,job/'input-after.json':{'status':'UNCHANGED','pins':copy.deepcopy(old)}}
 hashes={job/'input-pins.json':'e'*64,job/'projection-verified.json':'d'*64,job/'projection-review-verified.json':'f'*64}
 results=[]
 def run(name,change=None,expected=True):
  records=copy.deepcopy(original);existing={job/x for x in required};localhash=dict(hashes);metadata={'capsule':copy.deepcopy(caps),'pinnedFiles':{}}
  args=SimpleNamespace(projection_job=job,previous_input_sha256='e'*64,projection_sha256='d'*64,previous_review_sha256='f'*64)
  if change:change(records,existing,localhash,args)
  counts={'validation':0,'provider':0}
  def under(p,root,file=False):
   if not p.is_relative_to(root) or (file and p not in existing):raise ValueError('outside/missing synthetic path')
   return p
  def validation(a,*_):
   counts['validation']+=1
   if not isinstance(a.get('states'),list):raise ValueError('invalid state schema')
  state=SimpleNamespace(BASE=base,MODE='training-assisted',RUNTIME_RECORD_SHA='c'*64,under=under,validate_projection=validation)
  env={'state':state,'safe_sha':lambda p:localhash.get(p,'0'*64),'load':lambda p:copy.deepcopy(records[p]),'STATE_HELPER_SHA':STATE}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HELPER),'exec'),env)
  accepted=True
  try:
   answer,p=env['bind_existing_projection'](args,parent,item,{},metadata)
   assert p==job/'projection-verified.json' and answer==doc and len(metadata['pinnedFiles'])==10
  except (ValueError,KeyError,AssertionError):accepted=False
  assert accepted==expected,(name,accepted,expected)
  results.append({'name':name,'expectedAccepted':expected,'actualAccepted':accepted,'providerCalls':0})
 run('normal exact binding')
 for field in ['parent','capsule','documentId','mode','helperSha256','runtimeRecordSha256']:
  def change(r,e,h,a,f=field):r[job/'input-pins.json'][f]='wrong'
  run('old '+field+' drift',change,False)
 run('completion not unchanged',lambda r,e,h,a:r[job/'input-after.json'].update(status='CHANGED'),False)
 run('completion pins differ',lambda r,e,h,a:r[job/'input-after.json']['pins'].update(mode='wrong'),False)
 for field in ['documentId','parentDocumentSha256','projectionSha256','approved']:
  run('old rejected review '+field+' drift',lambda r,e,h,a,f=field:r[job/'projection-review-verified.json'].update({f:True if f=='approved' else 'wrong'}),False)
 for p in ['input-pins.json','projection-verified.json','projection-review-verified.json']:
  run('exact SHA '+p+' drift',lambda r,e,h,a,p=p:h.update({job/p:'0'*64}),False)
 run('canonical revision needed',lambda r,e,h,a:r[job/'projection-verified.json']['states'][0].update(requiresCanonicalRevision=True),False)
 run('invalid state schema',lambda r,e,h,a:r[job/'projection-verified.json'].update(states=None),False)
 for p in required:
  run('raw artifact missing '+p,lambda r,e,h,a,p=p:e.remove(job/p),False)
 run('projection path escapes',lambda r,e,h,a:setattr(a,'projection_job',Path('D:/synthetic/other/job')),False)
 mainfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 bound=[n for n in ast.walk(mainfn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_bound_job']
 assert len(bound)==1 and isinstance(bound[0].args[1],ast.BinOp) and bound[0].args[1].right.value=='independent-review'
 asserts=[n for n in ast.walk(mainfn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='assert_unchanged'];assert len(asserts)==3
 text=HELPER.read_text(encoding='utf8');assert 'state.validate_projection(answer' in text and 'state.input_pins(args)' in text and 'state.gates.validate_canonical_location' in text
 assert 'f.write(value[\'html\'])' in text and 'nativeSizeStateImagesVerified\':False' in text and 'strictRendererSanitizerRequired\':True' in text
 assert digest(HELPER)==EXPECTED
 out=HERE/'state-rereview-independent-v1';out.mkdir(exist_ok=False)
 report={'schema':'independent-code-only-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(HELPER),'helperSha256':EXPECTED,'reusedStateHelperSha256':STATE,'status':'PASS_CODE_ONLY_SYNTHETIC_DELTA','syntheticProbes':results,'count':len(results),'astChecks':{'oneIndependentReviewProviderCall':True,'beforeAfterPinsAndFinally':True,'canonicalPositionValidation':True,'verbatimHtmlExportOnlyAfterApproval':True,'strictRenderAndNativeRemainPending':True},'productionMetadataRead':False,'actualProviderCalls':0,'helperImportedOrMainExecuted':False,'originalInputsModified':False,'limits':['No actual projection/native HTML or provider execution was reviewed.','Path/link and loaded-module guards are reused from the independently inspected v6 helper.','Complete in-memory or race-free execution is not established.']}
 path=out/'review.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':str(path),'sha256':digest(path),'probes':len(results)},ensure_ascii=False))
if __name__=='__main__':main()
