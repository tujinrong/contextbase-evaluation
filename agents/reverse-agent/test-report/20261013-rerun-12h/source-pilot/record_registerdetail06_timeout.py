"""Preserve provider timeout evidence and unchanged source-only baseline, without a new AI job."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from contextbase.ai import capsule

REPO=Path(r'D:\開発\contextbase-evaluation')
R=REPO/'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot'
S=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only'
JOB=S/'jobs/remaining-register-detail-06'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
state=capsule.verification_state(S/'snapshot')
if state['manifestSha256']!='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b':raise ValueError('Cap drift')
runtime=json.loads((R/'runtime-code-source-09.json').read_text(encoding='utf-8'))
runtime_root=capsule.safe_path(Path(runtime['destination']))
inventory={p.relative_to(runtime_root).as_posix():sha(capsule.safe_path(p).read_bytes()) for p in runtime_root.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts}
if inventory!=runtime['files']:raise ValueError('Frozen writer runtime drift')
provider=json.loads((JOB/'draft/result.json').read_text(encoding='utf-8'))
run=json.loads((R/'remaining-register-detail-06-document-run.json').read_text(encoding='utf-8'))
if provider['metadata']['status']!='timeout' or provider['answer'] is not None or run['exitCode']!=1:raise ValueError('Unexpected terminal state')
files=[]
for path in sorted(JOB.rglob('*')):
 if path.is_file():
  raw=capsule.safe_path(path).read_bytes();files.append({'path':str(path),'sha256':sha(raw),'bytes':len(raw)})
for name in ('remaining-register-detail-06-document-run.json','remaining-register-detail-06-document-cli.log',
             'registerdetail06-timeout-provider-actions.json','remaining-register-detail-06-revision-context.json',
             'register-detail06-local-scope.json'):
 p=R/name;raw=capsule.safe_path(p).read_bytes();files.append({'path':str(p),'sha256':sha(raw),'bytes':len(raw)})
previous=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/remaining-register-detail-05/詳細仕様書/CSharp_ASPNET/02_学生登録画面.md'
previous_sha=sha(capsule.safe_path(previous).read_bytes())
if previous_sha!='6f7c8ac8724bdd1a2925a982651ca48a1b9d59b398a310ee28623cb93065ce6b':raise ValueError('Prior baseline draft drift')
stderr=(JOB/'draft/stderr.log').read_text(encoding='utf-8')
errors=[line for line in stderr.splitlines() if 'responses_retry' in line]
result={'schema':'source-only-provider-timeout-preservation/1','createdAt':datetime.now(timezone.utc).isoformat(),
 'job':str(JOB),'snapshot':state,'runtimeRoot':str(runtime_root),'runtimeFileCount':len(inventory),
 'runtimeReceiptSha256':sha((R/'runtime-code-source-09.json').read_bytes()),
 'status':'FAILED_PROVIDER_TIMEOUT_NO_NEW_CANONICAL','providerSeconds':provider['metadata']['seconds'],
 'runnerSeconds':run['seconds'],'startedAt':run['startedAt'],'endedAt':run['endedAt'],
 'timeoutSeconds':3000,'providerAnswerExists':(JOB/'draft/answer.txt').exists(),
 'newDraftResultExists':(JOB/'draft-result.json').exists(),'usageReported':False,
 'retryMessagesFromProviderStderr':errors,'filesPreserved':files,
 'snapshotUnchanged':run['snapshotUnchanged'],'allowedOriginalSourceUnchanged':run['allowedOriginalSourceUnchanged'],
 'frozenRuntimeUnchangedFullInventory':True,
 'previousSavedCandidate':{'path':str(previous),'sha256':previous_sha,'reviewStatus':'REVISION_REQUIRED','adopted':False},
 'followupWriterStarted':False,'newSourceStateProviderStarted':False,
 'priority':'USER_95_PERCENT_STOP_SCOPE_SOURCE_BASELINE_PRESERVATION',
 'watcherCleanup':[{'sessionId':65449,'role':'owned read-only detail stage watcher','signal':'Ctrl+C','exitCode':1},
                   {'sessionId':51050,'role':'owned read-only stale basic original-review watcher','signal':'Ctrl+C','exitCode':1}],
 'watcherCleanupReason':'Provider/writer terminal and fresh basic review terminal; stale watcher targets cannot produce a draft. No provider was interrupted.',
 'applicationRuntimeExecuted':False,'semanticContentHandModified':False,'overallPassClaimed':False}
out=R/'registerdetail06-timeout-preservation-r01.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'preservedFiles':len(files),'runtimeFiles':len(inventory),'newWriterStarted':False},ensure_ascii=False))
