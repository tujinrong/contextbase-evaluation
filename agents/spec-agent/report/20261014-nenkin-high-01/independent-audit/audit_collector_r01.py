"""AST extracted collector functions and toy metadata only; no production main."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,copy,hashlib,json,sys,tempfile,types
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'.tmp/20261014-nenkin-high-01/collect_reviewed_r01.py'
RAW=SOURCE.read_bytes();SOURCE_SHA=hashlib.sha256(RAW).hexdigest()
assert SOURCE_SHA=='ed717bbbeee6ab7c0ecb9b4f838ba985534254f4ca9b6bee6057864853b980fd'
TREE=ast.parse(RAW);DEFS=[n for n in TREE.body if isinstance(n,ast.FunctionDef)]
CASE=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(p):
 p=Path(p).absolute()
 for q in (p,*p.parents):
  if q.is_symlink() or (q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Toy linked path rejected')
 return p.resolve()
def load(p):return json.loads(safe(p).read_text(encoding='utf-8'))
def save(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v),encoding='utf8')
saved={n:sys.modules.get(n) for n in ('contextbase','contextbase.ai','contextbase.ai.validation')}
argv=sys.argv[:]
def one(name,change=None,expected='reject',partial=False):
 with tempfile.TemporaryDirectory(prefix='collector-toy-',dir=HERE) as td:
  root=Path(td);run=root/'run';report=root/'report';(run/'jobs').mkdir(parents=True);report.mkdir()
  helper=root/'guard.py';helper.write_bytes(b'# toy pinned code\n')
  receipt=root/'receipt.json';receipt.write_text('{}');runtime=root/'runtime';runtime.mkdir()
  state={'manifestSha256':'a'*64,'capsuleSchema':'reverse-ai-source-capsule/2','mode':'source-only'}
  planpath=run/'jobs/plan-02/plan-verified.json';ph=planpath.parent/'plan-handoff.json'
  defs=[{'id':'TOY-001','path':'detail/toy.md','title':'toy','kind':'detailed-specification','sourcePaths':[],'responsibilities':['toy scope']},{'id':'TOY-REPORT','path':'analysis/toy.md','title':'report','kind':'analysis-report','sourcePaths':[],'responsibilities':['toy report']}]
  plan={'documents':defs};save(planpath,plan);save(ph,{'snapshot':state,'origin':'toy'})
  planrev=run/'jobs/independent-plan-review-02/plan-review-verified.json';prh=planrev.parent/'plan-review-handoff.json';prraw=planrev.parent/'answer.txt'
  assessment={'schema':'reverse-ai-plan-review/1','referenceMode':'source-only','approved':True,'sourcePathsRead':[],'subjects':[],'documentCoverage':[{'documentId':d['id'],'path':d['path'],'subjectIds':[],'status':'covered','basis':'plan-structure','rationale':'toy','references':[]} for d in defs],'reachability':[],'findings':[],'blockingUnresolved':[],'scopeLimits':[]}
  save(planrev,assessment);prraw.write_bytes(planrev.read_bytes())
  selection=report/'selection.json';items=[];docdata=[];checkpoints={}
  for i,d in enumerate(defs):
   document=run/f'drafts/{i}'/d['path'];document.parent.mkdir(parents=True);document.write_bytes(b'toy AI prose, not production\n')
   dr=run/f'jobs/document-{i}/draft-result.json';rv=run/f'jobs/review-{i}/review-verified.json';rh=rv.parent/'review-handoff.json'
   aj=run/f'jobs/analysis-{i}';aj.mkdir();analysis={'documentId':d['id'],'facts':[],'sourcePathsRead':[]};save(aj/'analysis-verified.json',analysis)
   for f in ('answer.txt','result.json','schema.json','prompt.txt'):(aj/'analysis').mkdir(exist_ok=True);(aj/'analysis'/f).write_text('{}')
   for f in ('analysis-snapshot-before.json','analysis-snapshot-after.json'):(aj/f).write_text('{}')
   checkpoint={'analysisSha256':sha(aj/'analysis-verified.json'),'referenceMode':'source-only','providerDirectory':'analysis','providerArtifactsSha256':{f:sha(aj/'analysis'/f) for f in ('answer.txt','result.json','schema.json','prompt.txt')},'snapshotEvidenceSha256':{f:sha(aj/f) for f in ('analysis-snapshot-before.json','analysis-snapshot-after.json')}}
   save(aj/'analysis-handoff.json',checkpoint);checkpoints[str(aj)]=(analysis,checkpoint,sha(aj/'analysis-handoff.json'))
   draft={'documentId':d['id'],'path':d['path'],'snapshot':state,'referenceMode':'source-only','contentSha256':sha(document),'analysisJob':str(aj),'aiAuthored':True,'semanticProseAssembledByPython':False}
   review={'documentId':d['id'],'approved':True,'unresolved':[],'findings':[],'sourcePathsRead':[]};save(dr,draft);save(rv,review);save(rv.parent/'answer.txt',review)
   handoff={'schema':'reverse-ai-review-handoff/1','snapshot':state,'referenceMode':'source-only','documentSha256':sha(document),'documentFile':str(document),'reviewSha256':sha(rv),'approved':True,'reviewScope':'text-source-and-structure'};save(rh,handoff)
   rp={'record':str(receipt),'recordSha256':sha(receipt),'directory':str(runtime)}
   dp=report/f'pin-{i}.json';docpin={'documentId':d['id'],'path':d['path'],'kind':d['kind'],'capsule':state,'structureStatus':'STRUCTURE_VALID','independentReviewApproved':True,'noFurtherTextRevisionPlanned':True,'canonicalMarkdown':str(document),'sha256':sha(document),'draftResult':str(dr),'draftResultSha256':sha(dr),'independentReview':str(rv),'independentReviewSha256':sha(rv),'generationRuntime':rp,'reviewRuntime':rp,'structureRuntime':rp,'basisCounts':{'observed-source':0}}
   save(dp,docpin);items.append({'documentId':d['id'],'pin':str(dp),'pinSha256':sha(dp)});docdata.append({'definition':d,'document':document,'draftFile':dr,'draft':draft,'reviewFile':rv,'review':review,'handoffFile':rh,'handoff':handoff,'pinFile':dp,'pin':docpin})
  save(selection,{'documents':items})
  phv={'schema':'reverse-ai-plan-review-handoff/1','approved':True,'reviewSha256':sha(planrev),'snapshot':state,'planSha256':sha(planpath),'planHandoffSha256':sha(ph),'referenceMode':'source-only','aiResponseBytesModified':False,'originalAiResponse':'answer.txt'};save(prh,phv)
  fixed={'snapshot':state};runtime_pin={'runtime':'toy'};recheck_calls=[];structure_errors=[]
  guard=types.SimpleNamespace(bootstrap=lambda:copy.deepcopy(runtime_pin),allowed_plan=lambda p:safe(p),current_pin=lambda *args:(fixed,None,plan,{'files':[]},planpath.read_bytes()),recheck=lambda *args:recheck_calls.append(True),SNAPSHOT=run/'snapshot',RECEIPT=receipt,RECEIPT_SHA=sha(receipt),RUNTIME=runtime)
  wf=types.SimpleNamespace(references_valid=lambda *args:None,select_document=lambda p,i:next(d for d in defs if d['id']==i),_resume_analysis=lambda s,d,a:checkpoints[str(a)],relative_path=lambda p:Path(p))
  cap=types.SimpleNamespace(_load_json=load)
  ai=types.ModuleType('contextbase.ai');ai.workflow=wf;ai.capsule=cap;pkg=types.ModuleType('contextbase');pkg.ai=ai
  valid=types.ModuleType('contextbase.ai.validation');valid.validate_document=lambda *args,**kwargs:list(structure_errors)
  sys.modules.update({'contextbase':pkg,'contextbase.ai':ai,'contextbase.ai.validation':valid})
  ns={'Path':Path,'datetime':datetime,'timezone':timezone,'argparse':argparse,'hashlib':hashlib,'json':json,'sys':sys,'RUN':run,'REPORT':report,'HELPER':helper,'HELPER_SHA':sha(helper),'guard':guard,'safe':safe,'sha':sha,'load':load,'__file__':str(SOURCE)}
  exec(compile(ast.Module(body=DEFS,type_ignores=[]),str(SOURCE),'exec'),ns)
  args={'selection':str(selection),'selection_sha256':sha(selection),'plan':str(planpath),'plan_sha256':sha(planpath),'plan_handoff_sha256':sha(ph),'plan_review':str(planrev),'plan_review_sha256':sha(planrev),'plan_review_handoff_sha256':sha(prh),'output':str(run/'collections/candidate'),'report':str(report/'collection.json')}
  f={'root':root,'run':run,'report':report,'args':args,'defs':defs,'items':items,'selection':selection,'planReview':planrev,'planReviewRaw':prraw,'planHandoff':prh,'assessment':assessment,'planHandoffValue':phv,'docs':docdata,'structureErrors':structure_errors,'checkpoints':checkpoints,'wf':wf}
  if partial:items.pop();save(selection,{'documents':items});args['selection_sha256']=sha(selection)
  if change:change(f)
  sys.argv=['toy-collector']+[t for k,v in args.items() for t in ('--'+k.replace('_','-'),str(v))]+(['--partial'] if partial else [])
  observed='accept';error=None
  try:ns['main']()
  except (ValueError,FileExistsError,KeyError,StopIteration) as e:observed='reject';error=type(e).__name__
  match=observed==expected
  CASE.append({'name':name,'expected':expected,'observed':observed,'expectedMatched':match,'errorType':error})
  if name=='full staging positive':
   result=load(args['report']);assert result['documentCount']==2 and result['reportOnlyCount']==1 and result['specificationCount']==1 and result['published'] is False
   assert all(Path(d['canonicalMarkdown']).read_bytes()==Path(d['sourceReviewedMarkdown']).read_bytes() for d in result['documents'])
  if name=='partial stays staging':assert load(args['report'])['completePlan'] is False and load(args['report'])['published'] is False

def repin_doc(f,index=0):
 d=f['docs'][index];save(d['draftFile'],d['draft']);save(d['reviewFile'],d['review']);save(d['handoffFile'],d['handoff']);d['pin']['draftResultSha256']=sha(d['draftFile']);d['pin']['independentReviewSha256']=sha(d['reviewFile']);save(d['pinFile'],d['pin']);f['items'][index]['pinSha256']=sha(d['pinFile']);save(f['selection'],{'documents':f['items']});f['args']['selection_sha256']=sha(f['selection'])
def repin_plan_review(f):
 save(f['planReview'],f['assessment']);f['planReviewRaw'].write_bytes(f['planReview'].read_bytes());f['planHandoffValue']['reviewSha256']=sha(f['planReview']);save(f['planHandoff'],f['planHandoffValue']);f['args']['plan_review_sha256']=sha(f['planReview']);f['args']['plan_review_handoff_sha256']=sha(f['planHandoff'])
try:
 one('full staging positive',expected='accept')
 one('partial stays staging',expected='accept',partial=True)
 one('full selection missing planned document',lambda f:(f['items'].pop(),save(f['selection'],{'documents':f['items']}),f['args'].update(selection_sha256=sha(f['selection']))))
 one('duplicate selection ID',lambda f:(f['items'].append(copy.deepcopy(f['items'][0])),save(f['selection'],{'documents':f['items']}),f['args'].update(selection_sha256=sha(f['selection']))))
 one('unknown selection ID',lambda f:(f['items'][0].update(documentId='UNKNOWN'),save(f['selection'],{'documents':f['items']}),f['args'].update(selection_sha256=sha(f['selection']))))
 one('output outside collections',lambda f:f['args'].update(output=str(f['root']/'outside')))
 one('selection outside REPORT',lambda f:f['args'].update(selection=str(f['root']/'outside.json')))
 one('existing output rejected',lambda f:Path(f['args']['output']).mkdir(parents=True))
 one('existing report rejected',lambda f:Path(f['args']['report']).write_text('{}'))
 one('selection SHA drift',lambda f:f['args'].update(selection_sha256='0'*64))
 one('plan review SHA drift',lambda f:f['args'].update(plan_review_sha256='0'*64))
 one('plan review handoff SHA drift',lambda f:f['args'].update(plan_review_handoff_sha256='0'*64))
 one('original plan review answer drift',lambda f:f['planReviewRaw'].write_text('{}'))
 one('plan review not approved',lambda f:(f['assessment'].update(approved=False),repin_plan_review(f)))
 one('plan review wrong snapshot',lambda f:(f['planHandoffValue'].update(snapshot={'mode':'other'}),repin_plan_review(f)))
 one('plan review wrong source mode',lambda f:(f['planHandoffValue'].update(referenceMode='training-assisted'),repin_plan_review(f)))
 one('plan review original answer filename',lambda f:(f['planHandoffValue'].update(originalAiResponse='../answer.txt'),repin_plan_review(f)))
 for key,value in [('independentReviewApproved',False),('noFurtherTextRevisionPlanned',False),('structureStatus','STRUCTURE_INVALID'),('kind','wrong'),('capsule',{'mode':'other'})]:
  one('pin rejects '+key,lambda f,k=key,v=value:(f['docs'][0]['pin'].update({k:v}),repin_doc(f)))
 one('canonical byte drift',lambda f:f['docs'][0]['document'].write_bytes(b'changed'))
 one('draft wrong document ID',lambda f:(f['docs'][0]['draft'].update(documentId='OTHER'),repin_doc(f)))
 one('draft wrong reference mode',lambda f:(f['docs'][0]['draft'].update(referenceMode='training-assisted'),repin_doc(f)))
 one('review major finding rejected',lambda f:(f['docs'][0]['review'].update(findings=[{'severity':'major','references':[]}]),repin_doc(f)))
 one('review unresolved rejected',lambda f:(f['docs'][0]['review'].update(unresolved=['toy']),repin_doc(f)))
 one('raw document review drift',lambda f:(f['docs'][0]['reviewFile'].parent/'answer.txt').write_text('{}'))
 one('current structural failure',lambda f:f['structureErrors'].append({'code':'TOY_ERROR'}))
 one('stage runtime receipt mismatch',lambda f:(f['docs'][0]['pin']['generationRuntime'].update(recordSha256='0'*64),repin_doc(f)))
 one('analysis artifact byte drift',lambda f:(Path(f['docs'][0]['draft']['analysisJob'])/'analysis/answer.txt').write_text('drift'))
 # Intended refusals; accepted cases are explicit defense gaps, never synthetic PASS.
 one('GAP plan review major approved',lambda f:(f['assessment'].update(findings=[{'id':'toy','severity':'major','references':[]}]),repin_plan_review(f)))
 one('GAP plan review blocking unresolved approved',lambda f:(f['assessment'].update(blockingUnresolved=[{'id':'toy'}]),repin_plan_review(f)))
 one('GAP plan review missing document coverage',lambda f:(f['assessment'].update(documentCoverage=[]),repin_plan_review(f)))
 one('GAP draft aiAuthored false',lambda f:(f['docs'][0]['draft'].update(aiAuthored=False),repin_doc(f)))
 one('GAP draft Python semantic assembly true',lambda f:(f['docs'][0]['draft'].update(semanticProseAssembledByPython=True),repin_doc(f)))
 one('GAP original generation response absent')
 one('GAP plan review final success evidence absent')
 one('GAP wrong document review scope',lambda f:(f['docs'][0]['handoff'].update(reviewScope='made-up'),repin_doc(f)))
 one('GAP wrong document review schema',lambda f:(f['docs'][0]['review'].update(extraUnknownProperty=True),repin_doc(f)))
finally:
 sys.argv=argv
 for n,v in saved.items():
  if v is None:sys.modules.pop(n,None)
  else:sys.modules[n]=v
assert SOURCE.read_bytes()==RAW
gaps=[c for c in CASE if not c['expectedMatched']]
report={'schema':'spec-agent-independent-collector-code-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(SOURCE),'helperSha256':SOURCE_SHA,'status':'HOLD_DEFENSE_GAPS','cases':CASE,'expectedMatched':sum(c['expectedMatched'] for c in CASE),'counterexamples':gaps,'caseCount':len(CASE),'productionTopLevelOrCollectionExecuted':False,'actualSourceOrCanonicalOrPlanOrReviewOrExpectedBodyRead':False,'actualProviderOrApplicationOrDatabaseExecuted':False,'oldOutputModified':False,'partialSelectionScope':'WORK collections staging only; published false, no final qualification. Report-only documents are copied into staging but flagged for exclusion from later final specification publication.','limitations':['Extracted production function main was executed in a toy namespace with an audited-guard stub and analysis-resume stub. Production main, actual capsule and raw responses were not run/read.','Core document structural/schema/analysis validators are stubbed only to isolate collection provenance. This audit is not source-content or native-display QA.','Nine accepted negative cases are defense gaps, not passing tests.','No actual junction is exercised in this report; initial_safe/inside and scoped-helper guards were code-reviewed.']}
out=HERE/'collector-code-review-r01.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'cases':len(CASE),'expectedMatched':report['expectedMatched'],'acceptedNegative':len(gaps),'report':str(out),'sha256':sha(out)}))
