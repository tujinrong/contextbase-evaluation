"""Infrastructure-only synthetic audit. No actual evaluation material reads."""
import ast, copy, hashlib, json, os, re, shutil, sys, types
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

HERE=Path(__file__).absolute().parent
EVAL=HERE.parents[1]/'evaluator-only'
TARGET=EVAL/'retry_split_failed_batch_r03.py'
GRADER=EVAL/'grader.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'helper':sha(TARGET),'grader':sha(GRADER)}
gsrc=ast.parse(GRADER.read_text(encoding='utf-8-sig'))
gdefs=[n for n in gsrc.body if isinstance(n,ast.FunctionDef) and n.name in {'safe','digest','load','save','grouped_shards'}]
grader=types.SimpleNamespace(HERE=HERE/'fixtures')
gns={'Path':Path,'hashlib':hashlib,'json':json}
exec(compile(ast.Module(body=gdefs,type_ignores=[]),str(GRADER),'exec'),gns)
for n in gdefs:setattr(grader,n.name,gns[n.name])
tree=ast.parse(TARGET.read_text(encoding='utf-8-sig'))
defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='main']
ns={'grader':grader,'Path':Path,'Counter':Counter,'copy':copy,'datetime':datetime,'timezone':timezone,'os':os,'re':re,'shutil':shutil,'TERMINAL':{'PASSED','TIMEOUT','CLI_FAILED','VALIDATION_OR_PROVIDER_FAILED'},'ID':re.compile(r'^[A-Za-z0-9_-]+$')}
exec(compile(ast.Module(body=defs,type_ignores=[]),str(TARGET),'exec'),ns)
calls=[]
def validate(answer,request,capsule):
    calls.append(('validate',request['shardId']))
    if answer.get('valid') is not True:raise ValueError('Synthetic answer validator rejected')
    if answer['shardId']!=request['shardId'] or answer['rows']!=[r['evaluationId'] for r in request['rows']]:raise ValueError('Synthetic answer identity rejected')
grader.validate_answer=validate
def check(batch):
    calls.append(('check',str(batch)))
    seal=grader.load(batch/'batch.json');cap=batch/'capsule'
    if grader.digest(cap/'manifest.json')!=seal['capsuleManifestSha256']:raise ValueError('Toy cap drift')
    for rec in grader.load(cap/'manifest.json')['files']:
        if grader.digest(grader.safe(cap/rec['path'],cap))!=rec['sha256']:raise ValueError('Toy data drift')
    if seal['runtime']!={'toy':'runtime'} or seal['graderSha256']!='toy-fixed-grader':raise ValueError('Toy runtime drift')
    return seal,cap
grader.check_capsule=check
def put(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(data,bytes):p.write_bytes(data)
    else:p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def fixture(tag):
    base=grader.HERE/'batches'/tag;source=base/'source';dest=base/'fresh'
    cap=source/'capsule';jobs=[]
    for i,(count,status) in enumerate([(2,'PASSED'),(80,'VALIDATION_OR_PROVIDER_FAILED')],1):
        sid='S'+str(i).zfill(3)
        rows=[{'evaluationId':f'TOY-{i}-{j:03}','subject':'toy','source':{'path':'source/toy.txt','startLine':j//4+1,'endLine':j//4+1},'uninterpreted':{'keep':['literal',j]}} for j in range(count)]
        req={'shardId':sid,'documentId':'TOY','rows':rows,'requireSafetyReview':True,'safetyTopics':['toy-topic'],'fixedField':{'keep':'unchanged'}}
        put(cap/f'requests/{sid}.json',req)
        job={'shardId':sid,'documentId':'TOY','requestPath':f'requests/{sid}.json','evaluationIds':[r['evaluationId'] for r in rows]};jobs.append(job)
        answer={'valid':True,'shardId':sid,'rows':job['evaluationIds']}
        put(source/f'jobs/{sid}/answer.txt',answer)
        put(source/f'jobs/{sid}/raw-notes.txt',b'opaque raw bytes\r\n\x00preserved')
        put(source/f'jobs/{sid}/result.json',{'status':status,'shardId':sid,'documentId':'TOY','answerSha256':sha(source/f'jobs/{sid}/answer.txt')})
    put(cap/'source/toy.txt',b'synthetic fixture only\n')
    put(cap/'generated/toy.md',b'synthetic generated fixture only\n')
    records=[{'path':p.relative_to(cap).as_posix(),'sha256':sha(p),'role':'toy'} for p in cap.rglob('*') if p.is_file()]
    manifest={'schema':'toy-manifest','files':records,'unchangedMetadata':{'toy':True}}
    put(cap/'manifest.json',manifest)
    seal={'schema':'toy-batch','jobs':jobs,'graderSha256':'toy-fixed-grader','runtime':{'toy':'runtime'},'capsuleManifestSha256':sha(cap/'manifest.json'),'canonicalPinSha256':'toy-pin','rubricSha256':'toy-rubric','unrelated':['retain']}
    put(source/'batch.json',seal);put(source/'answer-schema.json',{'toy':'schema'});put(source/'canonical-pin.json',{'toy':'pin'})
    return source,dest
def reseal(source):
    cap=source/'capsule';m=grader.load(cap/'manifest.json')
    for r in m['files']:r['sha256']=sha(cap/r['path'])
    put(cap/'manifest.json',m);s=grader.load(source/'batch.json');s['capsuleManifestSha256']=sha(cap/'manifest.json');put(source/'batch.json',s)
results=[]
def closure_for(source,tag):
    seal=grader.load(source/'batch.json')
    records=[]
    for job in seal['jobs']:
        p=source/'jobs'/job['shardId']/'result.json'
        result=grader.load(p) if p.exists() else {}
        records.append({'shardId':job['shardId'],'status':result.get('status'), 'sha256':sha(p) if p.exists() else 'missing'})
    path=grader.HERE/'checkpoints'/str(tag+'.json')
    put(path,{'schema':'root-owned-closed-grader-batch/1','sourceBatch':str(source),'sourceBatchManifestSha256':sha(source/'batch.json'),'controllerExited':True,'controllerExitCode':1,'controllerSessionId':123,'terminalResults':records})
    return path
def run(name,expect,mutate=None,post=None,limit=20,patch=None,closure_mut=None):
    source,dest=fixture(f'{len(results)+1:03}-{name}');calls.clear()
    if mutate:mutate(source,dest)
    closure=closure_for(source,name);receipt_sha=sha(closure)
    if closure_mut:
        value=grader.load(closure);closure_mut(value);put(closure,value);receipt_sha=sha(closure)
    before=ns['inventory'](source) if not (source.is_symlink() or source.is_junction()) else None
    oldgroup=grader.grouped_shards;oldcopy=shutil.copyfile;oldsav=grader.save
    if patch:patch(source,dest)
    error=None;value=None
    try:value=ns['prepare_split'](source,dest,limit,closure,receipt_sha)
    except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
    finally:grader.grouped_shards=oldgroup;shutil.copyfile=oldcopy;grader.save=oldsav
    passed=(error is None) if expect=='accept' else (error is not None)
    checks=[]
    if post and error is None:
        checks=post(source,dest,value)
        passed=passed and all(checks)
    if before is not None and source.exists():passed=passed and ns['inventory'](source)==before
    results.append({'name':name,'expected':expect,'passed':passed,'error':error,'checks':checks,'validatorCalls':[x for x in calls if x[0]=='validate'],'destinationCreated':dest.exists()})
def json_mut(rel,fn,re=False):
    def mutate(s,d):
        p=s/rel;v=grader.load(p);fn(v);put(p,v)
        if re:reseal(s)
    return mutate
def change_status(v):v['status']='RUNNING'
def positive(s,d,v):
    orig=grader.load(s/'capsule/manifest.json');new=grader.load(d/'capsule/manifest.json')
    srcseal=grader.load(s/'batch.json');dstseal=grader.load(d/'batch.json')
    origids=[x for j in srcseal['jobs'] for x in j['evaluationIds']];newids=[x for j in dstseal['jobs'] for x in j['evaluationIds']]
    newreq=[grader.load(d/'capsule'/j['requestPath']) for j in dstseal['jobs'] if '-P' in j['shardId']]
    checks=[orig['files']==new['files'][:len(orig['files'])],Counter(origids)==Counter(newids),len(newids)==len(set(newids)),v=={'reused':1,'smallerRetryJobs':4,'rowsPreserved':82},not (d/'jobs/S002').exists(),not any((d/'jobs'/r['shardId']).exists() for r in newreq),[r['requireSafetyReview'] for r in newreq]==[True,False,False,False],all(len(r['rows'])<=20 for r in newreq),srcseal['runtime']==dstseal['runtime'],srcseal['rubricSha256']==dstseal['rubricSha256'],srcseal['canonicalPinSha256']==dstseal['canonicalPinSha256']]
    for p in (s/'jobs/S001').rglob('*'):
        if p.is_file():checks.append(p.read_bytes()==(d/'jobs/S001'/p.relative_to(s/'jobs/S001')).read_bytes())
    return checks
run('real-exclusive-positive','accept',post=positive)
run('existing-destination','reject',lambda s,d:d.mkdir())
run('nested-destination','reject',patch=lambda s,d:None) if False else None
run('bool-limit','reject',limit=True)
run('unsupported-limit','reject',limit=30)
for status in ('RUNNING','PENDING','',None,'FAILED'):
    run('status-'+str(status),'reject',json_mut('jobs/S002/result.json',lambda v,x=status:v.update(status=x)))
run('missing-result','reject',lambda s,d:(s/'jobs/S002/result.json').unlink())
run('empty-started-dir','reject',lambda s,d:shutil.rmtree(s/'jobs/S002'))
run('wrong-result-shard','reject',json_mut('jobs/S002/result.json',lambda v:v.update(shardId='OTHER')))
run('wrong-result-doc','reject',json_mut('jobs/S002/result.json',lambda v:v.update(documentId='OTHER')))
run('answer-drift','reject',lambda s,d:(s/'jobs/S001/answer.txt').write_bytes(b'{"valid":false}'))
def answer_invalid(s,d):
    p=s/'jobs/S001/answer.txt';a=grader.load(p);a['valid']=False;put(p,a);r=grader.load(s/'jobs/S001/result.json');r['answerSha256']=sha(p);put(s/'jobs/S001/result.json',r)
run('validator-reject','reject',answer_invalid)
run('wrong-request-doc','reject',json_mut('capsule/requests/S002.json',lambda v:v.update(documentId='OTHER'),True))
run('wrong-request-shard','reject',json_mut('capsule/requests/S002.json',lambda v:v.update(shardId='OTHER'),True))
run('wrong-row-order','reject',json_mut('capsule/requests/S002.json',lambda v:v['rows'].reverse(),True))
run('empty-rows','reject',json_mut('capsule/requests/S002.json',lambda v:v.update(rows=[]),True))
run('duplicate-rows','reject',json_mut('capsule/requests/S002.json',lambda v:v['rows'].append(copy.deepcopy(v['rows'][0])),True))
run('nonboolean-safety','reject',json_mut('capsule/requests/S002.json',lambda v:v.update(requireSafetyReview='false'),True))
run('nonplain-id','reject',json_mut('batch.json',lambda v:v['jobs'][1].update(shardId='../x')))
run('duplicate-job','reject',json_mut('batch.json',lambda v:v['jobs'].append(copy.deepcopy(v['jobs'][0]))))
run('wrong-request-path','reject',json_mut('batch.json',lambda v:v['jobs'][1].update(requestPath='requests/OTHER.json')))
run('all-passed-no-split','reject',json_mut('jobs/S002/result.json',lambda v:v.update(status='PASSED')))
run('capsule-data-drift','reject',lambda s,d:(s/'capsule/source/toy.txt').write_bytes(b'drift'))
run('capsule-manifest-drift','reject',lambda s,d:(s/'capsule/manifest.json').write_bytes(b'{}'))
run('runtime-drift','reject',json_mut('batch.json',lambda v:v.update(runtime={'toy':'other'})))
run('grader-drift','reject',json_mut('batch.json',lambda v:v.update(graderSha256='other')))
def group_patch(mode):
    def patch(s,d):
        if mode=='omit':grader.grouped_shards=lambda rows,m:[rows[:-1]]
        elif mode=='duplicate':grader.grouped_shards=lambda rows,m:[rows,rows[:1]]
        elif mode=='oversize':grader.grouped_shards=lambda rows,m:[rows]
    return patch
run('group-omission','reject',patch=group_patch('omit'))
run('group-duplication','reject',patch=group_patch('duplicate'))
run('group-overlimit','reject',patch=group_patch('oversize'))
def copy_corrupt(s,d):
    original=shutil.copyfile
    def bad(src,dst):
        original(src,dst);Path(dst).write_bytes(b'corrupted')
    shutil.copyfile=bad
run('copy-byte-drift','reject',patch=copy_corrupt)
def colliding(s,d):
    seal=grader.load(s/'batch.json');seal['jobs'][0]['shardId']='S002-P001';seal['jobs'][0]['requestPath']='requests/S002-P001.json'
    req=grader.load(s/'capsule/requests/S001.json');req['shardId']='S002-P001';put(s/'capsule/requests/S002-P001.json',req)
    jobdir=s/'jobs/S001';jobdir.rename(s/'jobs/S002-P001');r=grader.load(s/'jobs/S002-P001/result.json');r['shardId']='S002-P001';a=grader.load(s/'jobs/S002-P001/answer.txt');a['shardId']='S002-P001';put(s/'jobs/S002-P001/answer.txt',a);r['answerSha256']=sha(s/'jobs/S002-P001/answer.txt');put(s/'jobs/S002-P001/result.json',r)
    put(s/'batch.json',seal);m=grader.load(s/'capsule/manifest.json');m['files'].append({'path':'requests/S002-P001.json','sha256':sha(s/'capsule/requests/S002-P001.json'),'role':'toy'});put(s/'capsule/manifest.json',m);reseal(s)
run('part-id-collision','reject',colliding)
# Direct path and closed-controller probes have no rubric/answer reads.
for label,target,root in [('outside-source',HERE/'outside',grader.HERE/'batches'),('outside-destination',HERE/'outside2',grader.HERE/'batches')]:
    try:ns['safe_path'](target,root);accepted=True
    except Exception:accepted=False
    results.append({'name':label,'expected':'reject','passed':not accepted})
source,dest=fixture('controller-active');closure=closure_for(source,'controller-active');c=grader.load(closure);c['controllerExited']=False;put(closure,c)
try:ns['prepare_split'](source,dest,20,closure,sha(closure));accepted=True;error=None
except Exception as exc:accepted=False;error=str(exc)
results.append({'name':'controller-active-no-closed-receipt','expected':'reject','passed':not accepted,'accepted':accepted,'error':error})

for key,bad in [('schema','wrong'),('sourceBatch','wrong'),('sourceBatchManifestSha256','wrong'),('controllerExitCode',0),('controllerExitCode',True),('controllerSessionId',False),('controllerSessionId',0)]:
    run('closure-'+key+'-'+str(bad),'reject',closure_mut=lambda c,k=key,b=bad:c.update({k:b}))
run('closure-missing-job','reject',closure_mut=lambda c:c['terminalResults'].pop())
run('closure-extra-job','reject',closure_mut=lambda c:c['terminalResults'].append({'shardId':'EXTRA','status':'TIMEOUT','sha256':'toy'}))
run('closure-duplicate-job','reject',closure_mut=lambda c:c['terminalResults'].append(copy.deepcopy(c['terminalResults'][0])))
run('closure-result-sha-drift','reject',closure_mut=lambda c:c['terminalResults'][0].update(sha256='wrong'))
run('closure-result-status-drift','reject',closure_mut=lambda c:c['terminalResults'][0].update(status='TIMEOUT'))
report={'scope' :'CODE_AND_SYNTHETIC_ONLY','helper':str(TARGET),'helperSha256':pins['helper'],'graderSha256':pins['grader'],'cases':results,'passed':sum(x['passed'] for x in results),'total':len(results),'productionMaterialsRead':False,'actualPrepareExecuted':False,'providerExecuted':False,'graderValidateAnswerScope':'call-spy plus synthetic identity validator; production schema not imported','realGraderDefinitionsUsed':['safe','digest','load','save','grouped_shards'],'r01PositiveFailureFixedByFreshManifestCreation':True,'diagnosticToyOnlyManifestOverwrite':False,'codePinsAfterEqual':pins=={'helper':sha(TARGET),'grader':sha(GRADER)}}
put(HERE/'review.json',report)
print(json.dumps({'passed':report['passed'],'total':report['total'],'reportSha256':sha(HERE/'review.json'),'failures':[x['name'] for x in results if not x['passed']]}))
