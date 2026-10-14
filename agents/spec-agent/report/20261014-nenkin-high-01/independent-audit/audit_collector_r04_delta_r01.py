"""Fresh isolated r04 delta controls; preserve the forty-case receipt."""
from pathlib import Path
import ast,json,hashlib,sys
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
prior=HERE/'audit_collector_r04.py';tree=ast.parse(prior.read_bytes())
setup=[]
for node in tree.body:
 if isinstance(node,ast.Try):break
 setup.append(node)
ns={'__file__':str(prior)}
exec(compile(ast.Module(body=setup,type_ignores=[]),str(prior),'exec'),ns)
one=ns['one'];load=ns['load'];save=ns['save'];sha=ns['sha'];schemas=ns['schemas'];core=ns['core'];policy=ns['policy']
def repin_preparation(f):
 save(f['preparation'],f['prepared']);v=f['planHandoffValue'];v['scopePreparationSha256']=sha(f['preparation']);save(f['planHandoff'],v);f['args']['plan_review_handoff_sha256']=sha(f['planHandoff'])
 before=load(f['planBefore']);before['preparationSha256']=sha(f['preparation']);save(f['planBefore'],before)
 after=load(f['planAfter']);after['preparationSha256']=sha(f['preparation']);save(f['planAfter'],after)
def provider_metadata(f,role,key,value):
 directory=f['planReview'].parent if role=='plan' else f['docs'][0]['draftFile'].parent/'draft'
 p=directory/'result.json';data=load(p);data['metadata'][key]=value;save(p,data)
def new_generation(f,change=None,extra='',definition=None):
 d=f['docs'][0];directory=d['draftFile'].parent/'draft';answer=load(directory/'answer.txt')
 if change:change(answer)
 analysis=ns['copy'].deepcopy(f['checkpoints'][d['draft']['analysisJob']][0])
 prompt=policy+'\nUser task (within that boundary):\n'+'\n対象文書計画:\n'+json.dumps(d['definition'] if definition is None else definition)+'\nAIによる解析素材:\n'+json.dumps(analysis)+extra
 f['makeProvider'](directory,answer,schemas.DRAFT,prompt)
try:
 one('delta full raw/provenance positive',expected='accept')
 one('delta complete partial staging positive',expected='accept',partial=True)
 one('typed major approved rejected',lambda f:(f['assessment'].update(findings=[{'id':'F-1','severity':'major','documentIds':['TOY-001'],'subjectIds':[],'location':'plan','defect':'toy major','repairDirection':'toy repair','basis':'plan-structure','references':[]}]),ns['repin_plan_review'](f)))
 one('typed blocking unresolved approved rejected',lambda f:(f['assessment'].update(blockingUnresolved=[{'id':'U-1','question':'toy unresolved','documentIds':[],'subjectIds':[],'basis':'plan-structure','references':[]}]),ns['repin_plan_review'](f)))
 one('nonempty incomplete coverage rejected',lambda f:(f['assessment']['documentCoverage'].pop(),ns['repin_plan_review'](f)))
 one('scope prepared job changed but SHA coherent',lambda f:(f['prepared'].update(job=str(f['run']/'jobs/other-job')),repin_preparation(f)))
 def wrong_prompt_name(f):
  p=f['preparation'].parent/'other-prompt.txt';p.write_bytes(f['preparedPrompt'].read_bytes());f['prepared'].update(promptFile=str(p),promptSha256=sha(p));repin_preparation(f)
 one('prepared prompt wrong filename coherent SHA',wrong_prompt_name)
 one('actual plan scope prompt changed with successful raw4',lambda f:f['makeProvider'](f['planReview'].parent,f['assessment'],core.PLAN_REVIEW,policy+'\nUser task (within that boundary):\n'+'different toy scope\n'))
 one('plan successful-after guard failed status',lambda f:(save(f['planAfter'],dict(load(f['planAfter']),status='REVIEW_NOT_VERIFIED'))))
 one('plan provider status failure',lambda f:provider_metadata(f,'plan','status','failed'))
 one('plan provider wrong workspace',lambda f:provider_metadata(f,'plan','workspace',str(f['root']/'outside-capsule')))
 one('plan provider schema absent claim',lambda f:provider_metadata(f,'plan','schema_supplied',False))
 one('plan provider training mode claim',lambda f:provider_metadata(f,'plan','reference_mode','training-assisted'))
 one('plan provider error events',lambda f:provider_metadata(f,'plan','error_events',['toy']))
 one('plan provider unchanged evidence fails',lambda f:save(f['planReview'].parent.parent/(f['planReview'].parent.name+'-snapshot-after.json'),{'status':'INPUT_CHANGED'}))
 one('draft content differs despite valid raw metadata',lambda f:new_generation(f,lambda answer:answer.update(content='different toy canonical body\n')))
 one('draft definition differs despite valid raw metadata',lambda f:new_generation(f,definition=dict(f['docs'][0]['definition'],responsibilities=['different toy'])) )
 one('draft analysis trailing non-whitespace',lambda f:new_generation(f,extra='\nUNTRUSTED_TRAILING_DATA'))
 def changed_analysis(f):
  aj=f['docs'][0]['draft']['analysisJob'];a,c,h=f['checkpoints'][aj];a=ns['copy'].deepcopy(a);a['coverageNotes']=['different same-doc analysis'];f['checkpoints'][aj]=(a,c,h)
 one('same document alternate analysis fails exact prompt binding',changed_analysis)
 one('document review visual claim forbidden',lambda f:(f['docs'][0]['handoff'].update(visualFidelityVerified=True),ns['repin_doc'](f)))
 one('document review formal claim forbidden',lambda f:(f['docs'][0]['handoff'].update(formallyEvaluatedByOriginalRubric=True),ns['repin_doc'](f)))
 def source_drift(f):
  def change(*args):f['docs'][0]['document'].write_bytes(b'late drift')
  ns['last_guard']=change
  # The guard is captured in the main namespace; obtain it via the current_pin closure owner.
  original=f['wf']._resume_analysis
  def resumed(*args):
   value=original(*args);f['docs'][0]['document'].write_bytes(b'late drift');return value
  f['wf']._resume_analysis=resumed
 one('source drift after validated raw fails copy-stage pin',source_drift)
finally:
 sys.argv=ns['argv']
 for n,v in ns['saved'].items():
  if v is None:sys.modules.pop(n,None)
  else:sys.modules[n]=v
cases=ns['CASE'];bad=[c for c in cases if not c['expectedMatched']]
report={'schema':'spec-agent-independent-collector-delta-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(ns['SOURCE']),'helperSha256':ns['SOURCE_SHA'],'status':'PASS_CODE_AND_SYNTHETIC' if not bad else 'HOLD_DEFENSE_GAPS','caseCount':len(cases),'expectedMatched':len(cases)-len(bad),'cases':cases,'counterexamples':bad,'productionCollectionOrTopLevelExecuted':False,'actualBusinessPlanCanonicalSourceExpectedRead':False,'providerOrTargetApplicationDatabaseExecuted':False,'schemaAndPlanValidate':'Actual frozen declarations and _validate AST are used in the toy namespace.','limitations':['Source-analysis resume and structural document validator are stubs only; native and semantic quality are not assessed.','No actual junction or input program is executed in this supplementary run.','Old r01/r04 code and reports remain unchanged.']}
out=HERE/'collector-code-review-r04-delta-r01.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'cases':len(cases),'expectedMatched':report['expectedMatched'],'sha256':sha(out)}))
