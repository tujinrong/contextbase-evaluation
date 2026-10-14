"""Extract functions only; no production modules, source/capsule/plan/jobs or prose read."""
from pathlib import Path
from datetime import datetime,timezone
import ast, copy, hashlib, json, re, sys, types
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
TARGET=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01/nenkin_writer_driver_r04.py')
EXPECTED='ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664'
assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
tree=ast.parse(TARGET.read_bytes())
r02=TARGET.with_name('nenkin_writer_driver_r02.py');r03=TARGET.with_name('nenkin_writer_driver_r03.py')
assert hashlib.sha256(r02.read_bytes()).hexdigest()=='26641d906d5cbcda1ff90d7e204cd271a2556a58b2249fc279d0177911d7304f'
assert hashlib.sha256(r03.read_bytes()).hexdigest()=='d3d7f7f8f549f0ff7ad38254c3a1c8b931f6f9d56e4142503530ca76a501daf8'
def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef)}
f02,f03,f04=functions(r02),functions(r03),functions(TARGET)
assert set(f02)==set(f03)==set(f04)
assert {k for k in f02 if f02[k]!=f03[k]}=={'binding','provider_evidence','previous_revision','text_pin','run'}
assert {k for k in f03 if f03[k]!=f04[k]}=={'provider_evidence'}
assign=lambda p:[ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if not isinstance(n,(ast.FunctionDef,ast.Expr))]
assert assign(r02)==assign(r03)==assign(TARGET)
names={'require','safe','inside','raw','digest','sha','pairs','load','write','hash_arg','provider_evidence','prompt_object','previous_revision','recheck_previous','text_pin'}
ns={'Path':Path,'hashlib':hashlib,'json':json,'re':re,'datetime':datetime,'timezone':timezone,'__file__':str(TARGET)}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(TARGET),'exec'),ns)
ROOT=HERE/'writer-revision-r04-toy';ROOT.mkdir(exist_ok=False)
schema={'type':'object','required':['documentId'],'properties':{'documentId':{'type':'string'}},'additionalProperties':True}
ai=types.ModuleType('contextbase.ai');wf=types.ModuleType('contextbase.ai.workflow');cap=types.ModuleType('contextbase.ai.capsule');sc=types.ModuleType('contextbase.ai.schemas');val=types.ModuleType('contextbase.ai.validation')
sc.DRAFT=sc.REVIEW=schema;ai.workflow=wf;ai.capsule=cap;ai.schemas=sc
provider=types.ModuleType('contextbase.ai.provider');provider.COMMON_POLICY='TRUSTED_POLICY';ai.provider=provider;sys.modules['contextbase.ai.provider']=provider
for name,module in [('contextbase',types.ModuleType('contextbase')),('contextbase.ai',ai),('contextbase.ai.workflow',wf),('contextbase.ai.capsule',cap),('contextbase.ai.schemas',sc),('contextbase.ai.validation',val)]:sys.modules[name]=module
wf.references_valid=lambda value,manifest:None
cap.verify=lambda path:{'mode':'source-only','files':[]}
read_count=0
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def fixture(index,conflict=False):
 work=ROOT/str(index)/'work';report=ROOT/str(index)/'report';ns['WORK']=work;ns['REPORT']=report;ns['RECEIPT_SHA']='f'*64;ns['RECEIPT']=ROOT/'toy-receipt.json';ns['RUNTIME']=ROOT/'toy-runtime'
 definition={'id':'TOY-1','path':'basic/toy.md','kind':'basic-design'}
 context={'schema':'toy-scope','project':'toy'};state={'manifestSha256':'a'*64,'mode':'source-only'}
 pin={'snapshot':state,'snapshotRoot':str(work/'snapshot'),'planSha256':'b'*64,'executionContextSha256':'c'*64,'grantSha256':'d'*64,'runtime':{'files':{'contextbase/ai/prompts.py':'e'*64}}}
 folder=ns['digest'](definition['id'].encode())[:16];gen=work/'jobs/author-wave-01'/folder;out=work/'drafts/author-wave-01/specifications';doc=out/definition['path'];doc.parent.mkdir(parents=True);doc.write_bytes(b'# Toy whole Markdown\n\nLiteral ABC-12.5 retained.\n')
 content=doc.read_text(encoding='utf-8');h=ns['sha'](doc);findings=[{'code':'TOY_STRUCTURE'}] if conflict else []
 analysis={'documentId':'TOY-1','facts':[],'sourcePathsRead':[]};dump(gen/'analysis-verified.json',analysis)
 checkpoint={'providerDirectory':'analysis','providerArtifactsSha256':{},'snapshotEvidenceSha256':{}}
 for name in ['answer.txt','result.json','schema.json','prompt.txt']:dump(gen/'analysis'/name,{'toy':name});checkpoint['providerArtifactsSha256'][name]=ns['sha'](gen/'analysis'/name)
 for suffix in ['before','after']:
  n='analysis-snapshot-'+suffix+'.json';dump(gen/n,state);checkpoint['snapshotEvidenceSha256'][n]=ns['sha'](gen/n)
 dump(gen/'analysis-handoff.json',checkpoint)
 dump(gen.parent/'author-inputs-before.json',{'input':pin,'preparationSha256':'1'*64})
 def resume(s,d,g):
  assert s==Path(pin['snapshotRoot']) and d==definition and g==gen
  actual=ns['load'](g/'analysis-handoff.json')
  for n,x in actual['providerArtifactsSha256'].items():assert ns['sha'](g/actual['providerDirectory']/n)==x
  for n,x in actual['snapshotEvidenceSha256'].items():assert ns['sha'](g/n)==x
  return ns['load'](g/'analysis-verified.json'),actual,ns['sha'](g/'analysis-handoff.json')
 wf._resume_analysis=resume;val.validate_document=lambda *args,**kwargs:copy.deepcopy(findings)
 def provider(stage,answer,prompt):
  p=gen/stage;dump(p/'answer.txt',answer);dump(p/'schema.json',schema);(p/'prompt.txt').write_bytes(prompt.encode('utf-8'))
  result={'exit_code':0,'answer':answer,'metadata':{'status':'passed','schema_supplied':True,'workspace':str(Path(pin['snapshotRoot']).resolve()),'reference_mode':'source-only','training_reference_authorized':False,'error_events':[],'invalid_event_lines':[],'answer_sha256':ns['sha'](p/'answer.txt'),'prompt_sha256':ns['sha'](p/'prompt.txt')}}
  dump(p/'result.json',result);dump(gen/(stage+'-snapshot-before.json'),state);dump(gen/(stage+'-snapshot-after.json'),{'status':'UNCHANGED','before':state,'after':state})
 draft={'documentId':'TOY-1','path':definition['path'],'content':content}
 review={'documentId':'TOY-1','approved':True,'findings':[],'unresolved':[]}
 draft_prompt='TRUSTED_POLICY\nUser task (within that boundary):\n\n対象文書計画:\n'+json.dumps(definition)+'\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\n'+json.dumps(context)+'\nAIによる解析素材:\n'+json.dumps(analysis)
 review_prompt='TRUSTED_POLICY\nUser task (within that boundary):\n\n対象文書計画:\n'+json.dumps(definition)+'\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\n'+json.dumps(context)+'\n原稿本文:\n'+content+'\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n'+json.dumps(findings)
 provider('draft',draft,draft_prompt);provider('independent-review',review,review_prompt)
 di={'documentId':'TOY-1','path':definition['path'],'contentSha256':h,'snapshot':state,'referenceMode':'source-only','aiAuthored':True,'semanticProseAssembledByPython':False,'structureFindings':findings};dump(gen/'draft-result.json',di)
 struct={'documentId':'TOY-1','contentSha256':h,'findings':findings,'status':'STRUCTURE_INVALID' if findings else 'STRUCTURE_VALID'};dump(gen/'document-structure.json',struct)
 rp=gen/'independent-review'/('answer.txt' if conflict else 'review-verified.json')
 if not conflict:
  rp.write_bytes((gen/'independent-review/answer.txt').read_bytes())
  dump(gen/'independent-review/review-handoff.json',{'schema':'reverse-ai-review-handoff/1','snapshot':state,'documentFile':str(doc.resolve()),'documentSha256':h,'reviewSha256':ns['sha'](rp),'approved':True,'executionContextSha256':pin['executionContextSha256'],'referenceMode':'source-only','aiResponseBytesModified':False})
 else:dump(gen/'independent-review/structure-approval-conflict.json',{'status':'AI_APPROVAL_REJECTED_STRUCTURE_INVALID','findings':findings,'documentSha256':h})
 result={'schema':'spec-agent-author-document-result/1','documentId':'TOY-1','path':definition['path'],'kind':definition['kind'],'capsule':state,'planSha256':pin['planSha256'],'executionContextSha256':pin['executionContextSha256'],'runtimeReceiptSha256':ns['RECEIPT_SHA'],'status':'REQUIRES_AI_REVISION' if conflict else 'TEXT_REVIEW_APPROVED','draft':{'canonicalMarkdown':str(doc.resolve()),'outputRoot':str(out.resolve()),'draftResult':str((gen/'draft-result.json').resolve()),'draftResultSha256':ns['sha'](gen/'draft-result.json'),'sha256':h},'review':{'path':str(rp.resolve()),'sha256':ns['sha'](rp),'approved':True,'verified':not conflict}}
 resultp=gen/'author-document-result.json';dump(resultp,result)
 return {'work':work,'report':report,'gen':gen,'doc':doc,'out':out,'definition':definition,'context':context,'pin':pin,'resultp':resultp,'result':result,'draft':draft,'di':di,'review':review,'checkpoint':checkpoint,'findings':findings}
checks=[]
def check(name,mut=None,reject=True,conflict=False,probe=False):
 f=fixture(len(checks),conflict)
 if mut:mut(f)
 try:
  previous,revision=ns['previous_revision'](f['resultp'],ns['sha'](f['resultp']),f['definition'],f['pin'],f['context'])
  assert revision['previousCanonicalMarkdown']==f['doc'].read_text(encoding='utf-8') and revision['freshAnalysisRequired'] is True
  assert previous['analysisWillBeReused'] is False and previous['completedAnalysisCheckpointRevalidated'] is True
  observed='ACCEPTED'
 except Exception as e:observed='REJECTED';error=type(e).__name__+': '+str(e)
 match=(observed=='REJECTED')==reject
 checks.append({'case':name,'expected':'REJECTED' if reject else 'ACCEPTED','observed':observed,'match':match,'exploratory':probe,**({'error':error} if observed=='REJECTED' else {})})
 return f
def edit(f,rel,change):
 p=f['gen']/rel;v=ns['load'](p);change(v);dump(p,v)
def author_edit(f,key,value):f['result'][key]=value;dump(f['resultp'],f['result'])
def prompt_edit(f,stage,change):
 p=f['gen']/stage/'prompt.txt';p.write_bytes(change(p.read_bytes().decode('utf-8')).encode('utf-8'))
 edit(f,stage+'/result.json',lambda v:v['metadata'].update(prompt_sha256=ns['sha'](p)))
check('complete_whole_revision_positive',reject=False)
check('structure_conflict_preserved_as_revision_evidence_positive',reject=False,conflict=True)
for key,value in [('documentId','OTHER'),('path','elsewhere.md'),('kind','physical-table-definition'),('schema','wrong'),('capsule',{}),('planSha256','0'*64),('executionContextSha256','0'*64),('runtimeReceiptSha256','0'*64),('status','FAILED')]:check('author_'+key,lambda f,k=key,v=value:author_edit(f,k,v))
check('whole_markdown_byte_drift',lambda f:f['doc'].write_bytes(b'changed whole markdown'))
for key,value in [('contentSha256','0'*64),('aiAuthored',False),('semanticProseAssembledByPython',True),('snapshot',{}),('referenceMode','training-assisted')]:check('draft_'+key,lambda f,k=key,v=value:edit(f,'draft-result.json',lambda d:d.update({k:v})))
check('structure_false_clean_record',lambda f:edit(f,'document-structure.json',lambda d:d.update(findings=[{'code':'other'}])))
check('checkpoint_unknown_provider_directory',lambda f:edit(f,'analysis-handoff.json',lambda d:d.update(providerDirectory='other')))
check('analysis_raw_byte_drift',lambda f:(f['gen']/'analysis/answer.txt').write_bytes(b'changed'))
check('analysis_snapshot_evidence_drift',lambda f:dump(f['gen']/'analysis-snapshot-after.json',{}))
for key,value in [('status','failed'),('workspace','outside'),('reference_mode','training-assisted'),('schema_supplied',False),('training_reference_authorized',True),('answer_sha256','0'*64),('prompt_sha256','0'*64),('error_events',['x']),('invalid_event_lines',['x'])]:check('draft_provider_'+key,lambda f,k=key,v=value:edit(f,'draft/result.json',lambda d:d['metadata'].update({k:v})))
check('draft_exit_failure',lambda f:edit(f,'draft/result.json',lambda d:d.update(exit_code=1)))
check('draft_raw_result_answer_drift',lambda f:edit(f,'draft/result.json',lambda d:d.update(answer={'documentId':'other'})))
check('draft_schema_drift',lambda f:dump(f['gen']/'draft/schema.json',{'type':'string'}))
check('draft_after_not_verified',lambda f:edit(f,'draft-snapshot-after.json',lambda d:d.update(status='FAILED')))
check('draft_prompt_definition_coherent_hash_wrong',lambda f:prompt_edit(f,'draft',lambda s:s.replace('"TOY-1"','"OTHER"',1)))
check('draft_prompt_analysis_coherent_hash_wrong',lambda f:prompt_edit(f,'draft',lambda s:s.replace('"facts": []','"facts": [{"extra": 1}]')))
check('draft_scope_coherent_hash_wrong',lambda f:prompt_edit(f,'draft',lambda s:s.replace('"project": "toy"','"project": "other"')))
check('review_whole_markdown_prompt_gap',lambda f:prompt_edit(f,'independent-review',lambda s:s.replace('Literal ABC-12.5 retained.','Literal partial.')))
check('review_scope_coherent_hash_wrong',lambda f:prompt_edit(f,'independent-review',lambda s:s.replace('"project": "toy"','"project": "other"')))
check('verified_handoff_document_drift',lambda f:edit(f,'independent-review/review-handoff.json',lambda d:d.update(documentSha256='0'*64)))
check('verified_review_byte_drift',lambda f:(f['gen']/'independent-review/review-verified.json').write_bytes(b'{}'))
# Exploratory defense gap: current evidence hashes prompts but does not bind frozen policy prefix.
check('coherent_prompt_without_policy_prefix',lambda f:prompt_edit(f,'draft',lambda s:s.replace('TRUSTED_POLICY','UNTRUSTED_PREFIX')),probe=False)
f=fixture(len(checks));previous,_=ns['previous_revision'](f['resultp'],ns['sha'](f['resultp']),f['definition'],f['pin'],f['context'])
try:
 (f['gen']/'draft/prompt.txt').write_bytes(b'changed')
 ns['recheck_previous'](previous,f['definition'],f['pin'],f['context']);observed='ACCEPTED'
except Exception:observed='REJECTED'
checks.append({'case':'recheck_previous_artifact_drift','expected':'REJECTED','observed':observed,'match':observed=='REJECTED'})
# The report copy path is exercised on toy metadata only; schema check delegated/stubbed.
f=fixture(len(checks));ns['recheck']=lambda *a,**k:None;ns['check_schema']=lambda *a,**k:None
result=ns['text_pin'](f['definition'],f['gen'],f['doc'],f['di'],f['review'],f['pin'],f['out'])
assert ns['raw'](result['path'])==ns['raw'](result['jobPin']) and result['sha256']==result['jobPinSha256']
assert Path(result['path']).is_relative_to(f['report']/'text-pins')
checks.append({'case':'report_text_pin_exact_bytecopy_positive','expected':'ACCEPTED','observed':'ACCEPTED','match':True})
nonexploratory=[c for c in checks if not c.get('exploratory')]
report={'schema':'writer-revision-independent-code-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(TARGET),'helperSha256':EXPECTED,'status':'PASS_SCOPED_CONTROLS_AND_PREFIX_DELTA','checks':checks,'controlCount':len(nonexploratory),'controlMatched':sum(c['match'] for c in nonexploratory),'exploratoryDefenseGap':{'case':'coherent_prompt_without_policy_prefix','observed':'REJECTED','meaning':'The same coherent prompt-policy replacement previously accepted by r02 is rejected by r04. This is a toy gate control, not a production invocation.'},'productionApplicationSourcePlanCapsuleJobsOrProseRead':False,'providerExecuted':False,'productionMainExecuted':False,'targetApplicationOrDatabaseExecuted':False,'limitations':['Only named FunctionDef AST bodies were executed in an isolated synthetic namespace.','workflow._resume_analysis, references_valid, capsule.verify and structural validator are stubs; underlying frozen delegate guarantees were not retested here.', 'Full activation binding and new scoped plan-review preparation checks were read at code/AST level only; these fixtures exercise previous_revision/provider_evidence and report pin copy, not the full production binding.','Report text-pin copy is exact byte tested with schema/binding stubs; production schema/runtime/grant validation is not claimed.','These controls do not authorize writer activation or any semantic/native/formal approval.']}
assert all(c['match'] for c in nonexploratory)
target=HERE/'writer-revision-code-review-r04.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'report':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'controls':len(nonexploratory),'matched':sum(c['match'] for c in nonexploratory),'prefixGapClosedInToy':True}))
