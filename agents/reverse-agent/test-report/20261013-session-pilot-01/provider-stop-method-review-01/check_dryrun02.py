"""Metadata/hash-only comparison of actual no-stop dryruns; no CIM or process calls."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd().resolve(); report=Path(__file__).resolve().parent
helper=root/'agents/reverse-agent/.tmp/20261013-session-pilot-01/capture_owned_cycle.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(root).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
before=pin(helper); records=[]; inputs=[helper]
for number in ('01','02'):
    dry=root/f'agents/reverse-agent/test-report/20261013-session-pilot-01/owned-capture-dryrun-{number}'
    result=json.loads((dry/'result.json').read_text(encoding='utf-8'))
    actions=json.loads((dry/'process-actions.json').read_text(encoding='utf-8'))
    assert result['stopRequested'] is False and actions['stopRequested'] is False
    assert result['completedScore'] is None and result['completeInferenceClaimed'] is False
    assert result['beforeFiles']==result['afterFiles']==33 and result['captureErrors']==0
    assert len(actions['roots'])==2 and all(r['state']=='EXACT_OWNER_MATCH' for r in actions['roots'])
    assert all(p['action']=='OBSERVED_NO_STOP' for p in actions['processes'])
    stable=0; verified=0
    for stage in ('before','after'):
        inventory=dry/('inventory-'+stage+'.json'); rows=json.loads(inventory.read_text(encoding='utf-8'));inputs.append(inventory)
        for row in rows:
            target=dry/stage/row['path']; assert sha(target)==row['copiedSha256']; verified+=1
            if row['stableDuringCopy']:
                assert row['sourceSha256Before']==row['copiedSha256']==row['sourceSha256After']; stable+=1
    if number=='02':
        assert result['processOperationState']==actions['state']=='OBSERVED_PROCESS_RESPONSE'
        assert (dry/'process-stdout.txt').is_file() and (dry/'process-stderr.txt').is_file()
        request=json.loads((dry/'process-request.json').read_text(encoding='utf-8'));assert request['stop'] is False
    inputs.extend([dry/'result.json',dry/'process-actions.json',dry/'scope.json'])
    records.append({'dryrun':number,'owners':2,'observedNoStopProcesses':len(actions['processes']),'beforeFiles':33,'afterFiles':33,'copiedFileHashesVerified':verified,'stableTripleHashesVerified':stable,'completedScore':None,'state':result.get('processOperationState','LEGACY_NO_EXPLICIT_PROCESS_STATE')})
after=pin(helper); assert before==after
(report/'dryrun-comparison.json').write_text(json.dumps({'schema':'independent-owned-capture-dryrun-comparison/1','capturedAt':datetime.now(timezone.utc).isoformat(),'currentHelperBefore':before,'currentHelperAfter':after,'helperUnchanged':True,'dryruns':records,'pins':[pin(p) for p in inputs],'liveCimOrStopCalled':False,'evaluatorExpectedContentsRead':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'dryruns':2,'copiedFilesVerified':sum(r['copiedFileHashesVerified'] for r in records),'helperUnchanged':True}))
