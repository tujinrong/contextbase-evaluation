"""Read current ownership and completed-file presence; never execute generation.

Mutable raw files are only observed. This program neither pins nor scores them.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():ROOT=ROOT.parent
REPORT=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01'
scope=json.loads((HERE/'frozen/provenance/scope.json').read_text(encoding='utf-8-sig'))
records=list(REPORT.glob('focus-continuation-handoff-*.json'))
record=max(records,key=lambda p:int(re.search(r'-(\d+)\.json$',p.name).group(1)))
ownership=json.loads(record.read_text(encoding='utf-8-sig'))
expected_config=scope['configPath']
job_root=Path(scope['preservedRunnerPath']).parent
if not job_root.is_absolute():job_root=ROOT/job_root
now=datetime.now(timezone.utc)
deadline=datetime.fromisoformat(scope['deadline'].replace('Z','+00:00'))
status='DEADLINE_REACHED' if now>=deadline else 'WATCHING_CURRENT_ROUND'
if ownership['activeConfig']!=expected_config or ROOT/ownership['activeJobRoot']!=job_root:
    status='OWNERSHIP_CHANGED_STOP_OBSERVATION'
checks=[]
if status=='WATCHING_CURRENT_ROUND':
    config=json.loads((ROOT/expected_config).read_text(encoding='utf-8-sig'))
    for job,stem in [('488af9821732c8f6','student-search'),('eebb51fa1eb2da8f','student-editor')]:
        directory=job_root/job
        completed=[]
        for phase in ('analysis','draft'):
            files=[directory/phase/'result.json',directory/phase/'answer.txt',directory/(phase+'-snapshot-after.json')]
            files+=([directory/'analysis-verified.json',directory/'analysis-handoff.json'] if phase=='analysis' else [directory/'draft-result.json'])
            if all(p.exists() for p in files):completed.append(phase)
        published=ROOT/config['output']/'spec/detail'/(stem+'.md')
        draft=directory/'draft-result.json'
        candidate_present=draft.exists() and published.exists()
        candidate_equal=False
        if candidate_present:
            content=json.loads(draft.read_text(encoding='utf-8-sig'))
            candidate_equal=hashlib.sha256(published.read_bytes()).hexdigest()==content['contentSha256']
        checks.append({'jobId':job,'document':stem,'completedFilesPresentForPhases':completed,
            'candidateFilesPresent':candidate_present,'publishedShaEqualsDraftResult':candidate_equal})
print(json.dumps({'observedAt':now.isoformat(),'status':status,'ownershipRecord':record.name,
 'activeConfig':ownership['activeConfig'],'documents':checks,'rawCompletionProvenByPresenceAlone':False,
 'scoresAssigned':False,'candidateOrMutableRawFilesFrozen':False},ensure_ascii=False))
