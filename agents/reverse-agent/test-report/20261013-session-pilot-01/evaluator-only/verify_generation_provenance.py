"""Check completed raw inference/checkpoint evidence, not a driver's fresh flag.

This never executes an input program or assigns a semantic score. A provider
record/trace is execution evidence within its stated scope, not sealed-v2 or
proof that every possible host read was isolated.
"""
from pathlib import Path
from artifact_store import exclusive_json
import argparse
import hashlib
import json
import datetime

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def phase_check(directory,phase,expected_id):
    p=directory/phase
    result=read(p/'result.json');m=result['metadata'];raw=read(p/'answer.txt')
    assert m['status']=='passed' and result['exit_code']==0
    assert raw==result['answer'] and raw['documentId']==expected_id
    assert m['prompt_sha256']==sha(p/'prompt.txt')
    assert m['answer_sha256']==sha(p/'answer.txt')
    assert Path(m['job_dir']).resolve()==p.resolve()
    assert m['sandbox']=='read-only' and m['ephemeral'] is True
    assert m['reference_mode']=='training-assisted' and m['training_reference_authorized'] is True
    # Provider metadata represents these collections as lists. Accept the
    # historical count form only when it is exactly zero, never a truthy value.
    assert m['error_events'] in ([],0) and m['invalid_event_lines'] in ([],0)
    command=m['command'];assert '--ephemeral' in command and '--sandbox' in command
    assert '--model' not in command and '-m' not in command
    events=[json.loads(line) for line in (p/'events.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    threads=[event.get('thread_id') for event in events if event.get('type')=='thread.started']
    assert len(threads)==1 and threads[0]
    assert any(event.get('type')=='turn.started' for event in events)
    assert any(event.get('type')=='turn.completed' for event in events)
    assert not any(event.get('type') in ('error','turn.failed') for event in events)
    before=read(directory/(phase+'-snapshot-before.json'))
    after=read(directory/(phase+'-snapshot-after.json'))
    assert after['status']=='UNCHANGED' and before==after['before']==after['after']
    assert before['mode']=='training-assisted'
    assert before['scope']=='legacy-v1-raw-indexed-metadata-revalidated-unsealed-manifest'
    out={'phase':phase,'providerStatus':'passed','exitCode':0,'jobDirectoryMatched':True,
        'answerEqualsRawProviderResult':True,'promptSha256':sha(p/'prompt.txt'),
        'schemaSha256':sha(p/'schema.json'),'answerSha256':sha(p/'answer.txt'),
        'resultSha256':sha(p/'result.json'),'eventsSha256':sha(p/'events.jsonl'),
        'stderrSha256':sha(p/'stderr.log'),'threadId':threads[0],
        'turnStartedAndCompleted':True,'cliSha256':m['cli_sha256'],
        'modelSelection':m['model_selection'],'actualModelNameRecorded':False,
        'scope':before['scope'],'beforeAfterIdentityMatched':True,
        'driverFreshFlagUsedAsProof':False,
        'allModelToolActionsAudited':m.get('model_tool_actions_audited',False)}
    if phase=='analysis':
        assert raw==read(directory/'analysis-verified.json')
        handoff=read(directory/'analysis-handoff.json')
        assert Path(handoff['analysisJob']).resolve()==directory.resolve()
        assert handoff['analysisSha256']==sha(directory/'analysis-verified.json')
        assert handoff['document']['id']==expected_id and handoff['referenceMode']=='training-assisted'
        for name,digest in handoff['providerArtifactsSha256'].items():assert sha(p/name)==digest
        for name,digest in handoff['snapshotEvidenceSha256'].items():assert sha(directory/name)==digest
        out['verifiedAnalysisEqualsRawAnswer']=True
        out['handoffArtifactAndCheckpointHashesMatched']=True
    else:
        draft=read(directory/'draft-result.json')
        assert draft['documentId']==expected_id and draft['path']==raw['path']
        assert hashlib.sha256(raw['content'].encode('utf-8')).hexdigest()==draft['contentSha256']
        out['draftContentSha256']=draft['contentSha256']
        out['rawAiContentEqualsCompletedDraftContent']=True
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--job-root',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    jobs={'488af9821732c8f6':'SM-DET-STUDENT-SEARCH','eebb51fa1eb2da8f':'SM-DET-STUDENT-EDITOR'}
    checks=[];pending=[]
    for job,doc in jobs.items():
        directory=args.job_root/job
        for phase in ('analysis','draft'):
            required=[directory/phase/'result.json',directory/phase/'answer.txt',directory/(phase+'-snapshot-after.json')]
            if not all(p.exists() for p in required):pending.append({'jobId':job,'phase':phase});continue
            item=phase_check(directory,phase,doc);item.update(jobId=job,documentId=doc);checks.append(item)
    assert len({x['threadId'] for x in checks})==len(checks),'Duplicate trace thread IDs across current jobs/phases'
    result={'schema':'raw-inference-provenance-verification/1','classification':'EVALUATOR_ONLY','generatorMayRead':False,
        'verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobRoot':str(args.job_root),
        'checks':checks,'pending':pending,'allFourInferencePhasesComplete':len(checks)==4,
        'driverFreshFlagsUsedAsProof':False,'semanticAcceptanceInferred':False,
        'sealedV2Claimed':False,'readIsolationBeyondRecordedPolicyProved':False,
        'applicationOrDbExecutionProved':False,'scriptSha256':sha(Path(__file__))}
    assert not args.output.exists(),'Keep prior verification; select a new output name.'
    exclusive_json(args.output,result)
    print(json.dumps({'checks':len(checks),'pending':pending,'allComplete':len(checks)==4,'sha256':sha(args.output)},ensure_ascii=False))

if __name__=='__main__':main()
