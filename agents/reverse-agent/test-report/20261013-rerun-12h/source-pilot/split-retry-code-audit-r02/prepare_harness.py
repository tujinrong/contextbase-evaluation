from pathlib import Path
HERE=Path(__file__).absolute().parent
old=(HERE.parent/'split-retry-code-audit-r01/audit.py').read_text(encoding='utf8')
text=old.replace("retry_split_failed_batch_r01.py","retry_split_failed_batch_r02.py")
text=text.replace("def run(name,expect,mutate=None,post=None,limit=20,patch=None):",'''def closure_for(source,tag):
    seal=grader.load(source/'batch.json')
    records=[]
    for job in seal['jobs']:
        p=source/'jobs'/job['shardId']/'result.json'
        result=grader.load(p) if p.exists() else {}
        records.append({'shardId':job['shardId'],'status':result.get('status'), 'sha256':sha(p) if p.exists() else 'missing'})
    path=grader.HERE/'checkpoints'/str(tag+'.json')
    put(path,{'schema':'root-owned-closed-grader-batch/1','sourceBatch':str(source),'sourceBatchManifestSha256':sha(source/'batch.json'),'controllerExited':True,'controllerExitCode':1,'controllerSessionId':123,'terminalResults':records})
    return path
def run(name,expect,mutate=None,post=None,limit=20,patch=None,closure_mut=None):''')
text=text.replace("before=ns['inventory'](source)","closure=closure_for(source,name);receipt_sha=sha(closure)\n    if closure_mut:\n        value=grader.load(closure);closure_mut(value);put(closure,value);receipt_sha=sha(closure)\n    before=ns['inventory'](source)")
text=text.replace("if patch:patch(source,dest)","if patch:patch(source,dest)")
text=text.replace("ns['prepare_split'](source,dest,limit)","ns['prepare_split'](source,dest,limit,closure,receipt_sha)")
begin=text.index("run('real-exclusive-positive-bug'")
end=text.index("def positive",begin)
text=text[:begin]+text[end:]
text=text.replace("run('corrected-toy-positive'","run('real-exclusive-positive'")
text=text.replace("source,dest=fixture('controller-active');put(source/'active-controller.json',{'controllerExited':False})", "source,dest=fixture('controller-active');closure=closure_for(source,'controller-active');c=grader.load(closure);c['controllerExited']=False;put(closure,c)")
text=text.replace("ns['prepare_split'](source,dest,20)","ns['prepare_split'](source,dest,20,closure,sha(closure))")
anchor="report={'scope'"
insert='''
for key,bad in [('schema','wrong'),('sourceBatch','wrong'),('sourceBatchManifestSha256','wrong'),('controllerExitCode',0),('controllerExitCode',True),('controllerSessionId',False),('controllerSessionId',0)]:
    run('closure-'+key+'-'+str(bad),'reject',closure_mut=lambda c,k=key,b=bad:c.update({k:b}))
run('closure-missing-job','reject',closure_mut=lambda c:c['terminalResults'].pop())
run('closure-extra-job','reject',closure_mut=lambda c:c['terminalResults'].append({'shardId':'EXTRA','status':'TIMEOUT','sha256':'toy'}))
run('closure-duplicate-job','reject',closure_mut=lambda c:c['terminalResults'].append(copy.deepcopy(c['terminalResults'][0])))
run('closure-result-sha-drift','reject',closure_mut=lambda c:c['terminalResults'][0].update(sha256='wrong'))
run('closure-result-status-drift','reject',closure_mut=lambda c:c['terminalResults'][0].update(status='TIMEOUT'))
report={'scope' '''
text=text.replace(anchor,insert)
text=text.replace("'r01PositiveFailure':'exclusive manifest save after byte-copy','diagnosticToyOnlyManifestOverwrite':True,", "'r01PositiveFailureFixedByFreshManifestCreation':True,'diagnosticToyOnlyManifestOverwrite':False,")
text=text.replace("graderValidateAnswerScope", "graderValidateAnswerScope")
(HERE/'audit.py').write_text(text,encoding='utf8')
