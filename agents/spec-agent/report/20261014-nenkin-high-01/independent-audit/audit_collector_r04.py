"""AST extracted collector functions and toy metadata only; no production main."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,copy,hashlib,json,sys,tempfile,types,io,contextlib
from jsonschema import ValidationError
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'.tmp/20261014-nenkin-high-01/collect_reviewed_r04.py'
RAW=SOURCE.read_bytes();SOURCE_SHA=hashlib.sha256(RAW).hexdigest()
assert SOURCE_SHA=='eb6cd4965e1685a9c2c0e845f3cc15b808608c6012e43ad08c34500f89e0d993'
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
FROZEN=Path(r'D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/runtime-code/source-13/src/contextbase/ai')
schema_ns={};exec(compile(ast.parse((FROZEN/'schemas.py').read_bytes()),'trusted-schema-definitions','exec'),schema_ns)
coretree=ast.parse((FROZEN/'plan_review.py').read_bytes());core_ns={}
core_nodes=[n for n in coretree.body if isinstance(n,ast.Assign) or (isinstance(n,ast.FunctionDef) and n.name in {'_object','_array','_unique','_validate'})]
exec(compile(ast.Module(body=core_nodes,type_ignores=[]),'trusted-plan-review-schema-and-validator','exec'),core_ns)
policytree=ast.parse((FROZEN/'provider.py').read_bytes());policy=next(n.value.value for n in policytree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMMON_POLICY' for t in n.targets))
schemas=types.SimpleNamespace(DRAFT=schema_ns['DRAFT'],REVIEW=schema_ns['REVIEW'])
core=types.SimpleNamespace(PLAN_REVIEW=core_ns['PLAN_REVIEW'],_validate=core_ns['_validate'])
provider=types.SimpleNamespace(COMMON_POLICY=policy)
saved={n:sys.modules.get(n) for n in ('contextbase','contextbase.ai','contextbase.ai.validation')}
argv=sys.argv[:]
def one(name,change=None,expected='reject',partial=False):
 with tempfile.TemporaryDirectory(prefix='collector-toy-',dir=HERE) as td:
  root=Path(td);run=root/'run';report=root/'report';(run/'jobs').mkdir(parents=True);report.mkdir()
  helper=root/'guard.py';helper.write_bytes(b'# toy pinned code\n')
  receipt=root/'receipt.json';receipt.write_text('{}');runtime=root/'runtime';runtime.mkdir()
  state={'manifestSha256':'a'*64,'capsuleSchema':'reverse-ai-source-capsule/2','mode':'source-only'}
  snapshot=run/'snapshot';snapshot.mkdir();runtime_pin={'runtime':'toy'}
  planpath=run/'jobs/plan-02/plan-verified.json';ph=planpath.parent/'plan-handoff.json'
  defs=[{'id':'TOY-001','path':'detail/toy.md','title':'toy','kind':'detailed-specification','sourcePaths':[],'responsibilities':['toy scope']},{'id':'TOY-REPORT','path':'analysis/toy.md','title':'report','kind':'analysis-report','sourcePaths':[],'responsibilities':['toy report']}]
  plan={'systemSummary':'toy','documents':defs,'unresolved':[]};save(planpath,plan);save(ph,{'snapshot':state,'origin':'toy'})
  planrev=run/'jobs/independent-plan-review-02/plan-review-verified.json';prh=planrev.parent/'plan-review-handoff.json';prraw=planrev.parent/'answer.txt'
  assessment={'schema':'reverse-ai-plan-review/1','referenceMode':'source-only','approved':True,'sourcePathsRead':[],'subjects':[],'documentCoverage':[{'documentId':d['id'],'path':d['path'],'subjectIds':[],'status':'covered','basis':'plan-structure','rationale':'toy','references':[]} for d in defs],'reachability':[],'findings':[],'blockingUnresolved':[],'scopeLimits':[]}
  save(planrev,assessment);prraw.write_bytes(planrev.read_bytes())
  selection=report/'selection.json';items=[];docdata=[];checkpoints={}
  for i,d in enumerate(defs):
   document=run/f'drafts/{i}'/d['path'];document.parent.mkdir(parents=True);document.write_bytes(b'toy AI prose, not production\n')
   dr=run/f'jobs/document-{i}/draft-result.json';rv=run/f'jobs/review-{i}/review-verified.json';rh=rv.parent/'review-handoff.json'
   aj=run/f'jobs/analysis-{i}';aj.mkdir();analysis={'documentId':d['id'],'facts':[],'sourcePathsRead':[],'unresolved':[],'coverageNotes':[]};save(aj/'analysis-verified.json',analysis)
   for f in ('answer.txt','result.json','schema.json','prompt.txt'):(aj/'analysis').mkdir(exist_ok=True);(aj/'analysis'/f).write_text('{}')
   for f in ('analysis-snapshot-before.json','analysis-snapshot-after.json'):(aj/f).write_text('{}')
   checkpoint={'analysisSha256':sha(aj/'analysis-verified.json'),'referenceMode':'source-only','providerDirectory':'analysis','providerArtifactsSha256':{f:sha(aj/'analysis'/f) for f in ('answer.txt','result.json','schema.json','prompt.txt')},'snapshotEvidenceSha256':{f:sha(aj/f) for f in ('analysis-snapshot-before.json','analysis-snapshot-after.json')}}
   save(aj/'analysis-handoff.json',checkpoint);checkpoints[str(aj)]=(analysis,checkpoint,sha(aj/'analysis-handoff.json'))
   draft={'documentId':d['id'],'path':d['path'],'snapshot':state,'referenceMode':'source-only','contentSha256':sha(document),'analysisJob':str(aj),'aiAuthored':True,'semanticProseAssembledByPython':False}
   review={'documentId':d['id'],'approved':True,'unresolved':[],'findings':[]};save(dr,draft);save(rv,review);save(rv.parent/'answer.txt',review)
   handoff={'schema':'reverse-ai-review-handoff/1','snapshot':state,'referenceMode':'source-only','documentSha256':sha(document),'documentFile':str(document),'reviewSha256':sha(rv),'approved':True,'reviewScope':'text-source-and-structure','visualFidelityVerified':False,'formallyEvaluatedByOriginalRubric':False};save(rh,handoff)
   rp={'record':str(receipt),'recordSha256':sha(receipt),'directory':str(runtime)}
   dp=report/f'pin-{i}.json';docpin={'documentId':d['id'],'path':d['path'],'kind':d['kind'],'capsule':state,'structureStatus':'STRUCTURE_VALID','independentReviewApproved':True,'noFurtherTextRevisionPlanned':True,'canonicalMarkdown':str(document),'sha256':sha(document),'draftResult':str(dr),'draftResultSha256':sha(dr),'independentReview':str(rv),'independentReviewSha256':sha(rv),'generationRuntime':rp,'reviewRuntime':rp,'structureRuntime':rp,'basisCounts':{'observed-source':0}}
   save(dp,docpin);items.append({'documentId':d['id'],'pin':str(dp),'pinSha256':sha(dp)});docdata.append({'definition':d,'document':document,'draftFile':dr,'draft':draft,'reviewFile':rv,'review':review,'handoffFile':rh,'handoff':handoff,'pinFile':dp,'pin':docpin})
  save(selection,{'documents':items})
  phv={'schema':'reverse-ai-plan-review-handoff/1','approved':True,'reviewSha256':sha(planrev),'snapshot':state,'planSha256':sha(planpath),'planHandoffSha256':sha(ph),'referenceMode':'source-only','aiResponseBytesModified':False,'originalAiResponse':'answer.txt'};save(prh,phv)
  fixed={'snapshot':state};recheck_calls=[];structure_errors=[]
  guard=types.SimpleNamespace(bootstrap=lambda:copy.deepcopy(runtime_pin),allowed_plan=lambda p:safe(p),current_pin=lambda *args:(fixed,None,plan,{'files':[]},planpath.read_bytes()),recheck=lambda *args:recheck_calls.append(True),SNAPSHOT=snapshot,RECEIPT=receipt,RECEIPT_SHA=sha(receipt),RUNTIME=runtime)
  wf=types.SimpleNamespace(references_valid=lambda *args:None,select_document=lambda p,i:next(d for d in defs if d['id']==i),_resume_analysis=lambda s,d,a:checkpoints[str(a)],relative_path=lambda p:Path(p),_materials=lambda m:{'manifest.json':{'original':'manifest.json','kind':'inventory'}})
  cap=types.SimpleNamespace(_load_json=load,reference_mode=lambda m:'source-only')
  core_ns['workflow']=wf;core_ns['capsule']=cap
  ai=types.ModuleType('contextbase.ai');ai.workflow=wf;ai.capsule=cap;ai.plan_review=core;ai.schemas=schemas;ai.provider=provider;pkg=types.ModuleType('contextbase');pkg.ai=ai
  valid=types.ModuleType('contextbase.ai.validation');valid.validate_document=lambda *args,**kwargs:list(structure_errors)
  sys.modules.update({'contextbase':pkg,'contextbase.ai':ai,'contextbase.ai.validation':valid})
  ns={'Path':Path,'datetime':datetime,'timezone':timezone,'argparse':argparse,'hashlib':hashlib,'json':json,'sys':sys,'RUN':run,'REPORT':report,'HELPER':helper,'HELPER_SHA':sha(helper),'guard':guard,'safe':safe,'sha':sha,'load':load,'__file__':str(SOURCE)}
  exec(compile(ast.Module(body=DEFS,type_ignores=[]),str(SOURCE),'exec'),ns)
  args={'selection':str(selection),'selection_sha256':sha(selection),'plan':str(planpath),'plan_sha256':sha(planpath),'plan_handoff_sha256':sha(ph),'plan_review':str(planrev),'plan_review_sha256':sha(planrev),'plan_review_handoff_sha256':sha(prh),'output':str(run/'collections/candidate'),'report':str(report/'collection.json')}
  prepdir=report/'independent-plan-review'/planrev.parent.name;prepdir.mkdir(parents=True)
  prepared_prompt=prepdir/'prepared-prompt.txt';prepared_prompt.write_bytes(b'toy full fixed scope and plan context\n')
  preparation=prepdir/'preparation.json';prepared={'input':fixed,'runtime':runtime_pin,'providerStarted':False,'helperSha256':sha(helper),'helper':str(helper),'job':str(planrev.parent),'promptFile':str(prepared_prompt),'promptSha256':sha(prepared_prompt)};save(preparation,prepared)
  phv['scopePreparationSha256']=sha(preparation);save(prh,phv);args['plan_review_handoff_sha256']=sha(prh)
  planbefore=planrev.parent.parent/(planrev.parent.name+'-plan-review-before.json');planafter=planrev.parent.parent/(planrev.parent.name+'-plan-review-after.json')
  save(planbefore,{'input':fixed,'runtime':runtime_pin,'preparationSha256':sha(preparation)})
  save(planafter,{'status':'UNCHANGED_AND_REVIEW_VALIDATED','input':fixed,'runtime':runtime_pin,'preparationSha256':sha(preparation)})
  def make_provider(directory,answer,schema,prompt):
   directory.mkdir(parents=True,exist_ok=True);save(directory/'answer.txt',answer);save(directory/'schema.json',schema);(directory/'prompt.txt').write_bytes(prompt.encode('utf8'))
   metadata={'status':'passed','schema_supplied':True,'workspace':str(snapshot),'reference_mode':'source-only','training_reference_authorized':False,'error_events':[],'invalid_event_lines':[],'answer_sha256':sha(directory/'answer.txt'),'prompt_sha256':sha(directory/'prompt.txt')}
   save(directory/'result.json',{'exit_code':0,'metadata':metadata,'answer':answer})
   save(directory.parent/(directory.name+'-snapshot-before.json'),state);save(directory.parent/(directory.name+'-snapshot-after.json'),{'status':'UNCHANGED','before':state,'after':state})
  make_provider(planrev.parent,assessment,core.PLAN_REVIEW,policy+'\nUser task (within that boundary):\n'+prepared_prompt.read_text())
  # Exact raw bytes equal the verified original plan review.
  planrev.write_bytes(prraw.read_bytes());phv['reviewSha256']=sha(planrev);save(prh,phv);args['plan_review_sha256']=sha(planrev);args['plan_review_handoff_sha256']=sha(prh)
  for d in docdata:
   reviewdir=d['reviewFile'].parent;make_provider(reviewdir,d['review'],schemas.REVIEW,'toy review prompt\n')
   generated={'documentId':d['definition']['id'],'path':d['definition']['path'],'content':d['document'].read_text(),'factCorrections':[],'unresolved':[]}
   aj=Path(d['draft']['analysisJob']);analysis=checkpoints[str(aj)][0]
   prompt=policy+'\nUser task (within that boundary):\n'+'\n対象文書計画:\n'+json.dumps(d['definition'])+'\nAIによる解析素材:\n'+json.dumps(analysis)
   make_provider(d['draftFile'].parent/'draft',generated,schemas.DRAFT,prompt)
  f={'root':root,'run':run,'report':report,'args':args,'defs':defs,'items':items,'selection':selection,'planReview':planrev,'planReviewRaw':prraw,'planHandoff':prh,'assessment':assessment,'planHandoffValue':phv,'docs':docdata,'structureErrors':structure_errors,'checkpoints':checkpoints,'wf':wf,'preparation':preparation,'prepared':prepared,'preparedPrompt':prepared_prompt,'planBefore':planbefore,'planAfter':planafter,'makeProvider':make_provider}
  if partial:items.pop();save(selection,{'documents':items});args['selection_sha256']=sha(selection)
  if change:change(f)
  sys.argv=['toy-collector']+[t for k,v in args.items() for t in ('--'+k.replace('_','-'),str(v))]+(['--partial'] if partial else [])
  observed='accept';error=None
  try:
   with contextlib.redirect_stdout(io.StringIO()):ns['main']()
  except (ValueError,FileExistsError,KeyError,StopIteration,ValidationError,FileNotFoundError) as e:observed='reject';error=type(e).__name__+': '+str(e)
  match=observed==expected
  CASE.append({'name':name,'expected':expected,'observed':observed,'expectedMatched':match,'errorType':error})
  if expected=='accept' and observed!='accept':raise AssertionError(name+' positive control failed: '+str(error))
  if name=='full staging positive':
   result=load(args['report']);assert result['documentCount']==2 and result['reportOnlyCount']==1 and result['specificationCount']==1 and result['published'] is False
   assert all(Path(d['canonicalMarkdown']).read_bytes()==Path(d['sourceReviewedMarkdown']).read_bytes() for d in result['documents'])
  if name=='partial stays staging':assert load(args['report'])['completePlan'] is False and load(args['report'])['published'] is False

def repin_doc(f,index=0):
 d=f['docs'][index];save(d['draftFile'],d['draft']);save(d['reviewFile'],d['review']);d['handoff']['reviewSha256']=sha(d['reviewFile']);save(d['handoffFile'],d['handoff']);d['pin']['draftResultSha256']=sha(d['draftFile']);d['pin']['independentReviewSha256']=sha(d['reviewFile']);save(d['pinFile'],d['pin']);f['items'][index]['pinSha256']=sha(d['pinFile']);save(f['selection'],{'documents':f['items']});f['args']['selection_sha256']=sha(f['selection'])
def repin_plan_review(f):
 f['makeProvider'](f['planReview'].parent,f['assessment'],core.PLAN_REVIEW,policy+'\nUser task (within that boundary):\n'+f['preparedPrompt'].read_text());f['planReview'].write_bytes(f['planReviewRaw'].read_bytes());f['planHandoffValue']['reviewSha256']=sha(f['planReview']);save(f['planHandoff'],f['planHandoffValue']);f['args']['plan_review_sha256']=sha(f['planReview']);f['args']['plan_review_handoff_sha256']=sha(f['planHandoff'])
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
 one('GAP original generation response absent',lambda f:(f['docs'][0]['draftFile'].parent/'draft/answer.txt').unlink())
 one('GAP plan review final success evidence absent',lambda f:f['planAfter'].unlink())
 one('GAP wrong document review scope',lambda f:(f['docs'][0]['handoff'].update(reviewScope='made-up'),repin_doc(f)))
 one('GAP wrong document review schema',lambda f:(f['docs'][0]['review'].update(extraUnknownProperty=True),repin_doc(f),f['makeProvider'](f['docs'][0]['reviewFile'].parent,f['docs'][0]['review'],schemas.REVIEW,'toy review prompt\n')))
finally:
 sys.argv=argv
 for n,v in saved.items():
  if v is None:sys.modules.pop(n,None)
  else:sys.modules[n]=v
assert SOURCE.read_bytes()==RAW
gaps=[c for c in CASE if not c['expectedMatched']]
report={'schema':'spec-agent-independent-collector-code-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(SOURCE),'helperSha256':SOURCE_SHA,'status':'PASS_CODE_AND_SYNTHETIC' if not gaps else 'HOLD_DEFENSE_GAPS','cases':CASE,'expectedMatched':sum(c['expectedMatched'] for c in CASE),'counterexamples':gaps,'caseCount':len(CASE),'productionTopLevelOrCollectionExecuted':False,'actualSourceOrCanonicalOrPlanOrReviewOrExpectedBodyRead':False,'actualProviderOrApplicationOrDatabaseExecuted':False,'oldOutputModified':False,'partialSelectionScope':'WORK collections staging only; published false, no final qualification. Report-only documents are copied into staging but flagged for exclusion from later final specification publication.','priorR01Clarification':'The r01 report had eight accepted negatives, not nine as written in one limitations sentence. Its unknown-review-key case had an independent handoff/raw binding mismatch; r04 aligns all those pins to isolate schema rejection. Old report and code are preserved.','limitations':['Extracted production function main was executed in a toy namespace with an audited-guard stub and analysis-resume stub. Production main, actual capsule and raw responses were not run/read.','Real frozen schema declarations and plan review _validate were extracted into the toy namespace; document structural and analysis-resume validators remain stubs. This audit is not source-content or native-display QA.','No actual junction is exercised in this report; initial_safe/inside and scoped-helper guards were code-reviewed.']}
out=HERE/'collector-code-review-r04.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'cases':len(CASE),'expectedMatched':report['expectedMatched'],'acceptedNegative':len(gaps),'report':str(out),'sha256':sha(out)}))
