"""Freeze completed text/provider bytes for review preparation while rendering waits."""
from pathlib import Path
import hashlib,json,shutil,sys
from datetime import datetime,timezone
ROOT=Path(r'D:\開発\contextbase-evaluation').resolve();REPORT=Path(__file__).resolve().parent
stem=sys.argv[1]
jobname,docid={'student-search':('488af9821732c8f6','SM-DET-STUDENT-SEARCH'),'student-editor':('eebb51fa1eb2da8f','SM-DET-STUDENT-EDITOR')}[stem]
assert datetime.now(timezone.utc)<datetime.fromisoformat('2026-10-13T03:20:58+00:00')
JOB=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-06'/jobname
DOC=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-06/spec/detail'/(stem+'.md')
TARGET=REPORT/'frozen-text'/stem
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
d=read(JOB/'draft-result.json');r=read(JOB/'draft/result.json');a=read(JOB/'draft/answer.txt')
assert r['exit_code']==0 and r['metadata']['status']=='passed' and r['answer']==a
assert r['metadata']['answer_sha256']==sha(JOB/'draft/answer.txt')
assert r['metadata']['prompt_sha256']==sha(JOB/'draft/prompt.txt')
assert a['documentId']==d['documentId']==docid
assert a['path']==d['path']=='spec/detail/'+stem+'.md'
assert d['aiAuthored'] is True and d['semanticProseAssembledByPython'] is False
assert sha(DOC)==d['contentSha256']==hashlib.sha256(a['content'].encode('utf-8')).hexdigest()
TARGET.mkdir(parents=True,exist_ok=False)
pins=[]
for source,name in [(DOC,stem+'.md'),(JOB/'draft-result.json','draft-result.json'),(JOB/'draft/result.json','provider-result.json'),(JOB/'draft/answer.txt','provider-answer.txt')]:
    before=sha(source);target=TARGET/name
    with source.open('rb') as incoming,target.open('xb') as outgoing:shutil.copyfileobj(incoming,outgoing)
    copied=sha(target);after=sha(source);assert before==copied==after
    pins.append({'sourcePath':source.relative_to(ROOT).as_posix(),'frozenPath':target.relative_to(ROOT).as_posix(),'sha256':copied,'sourceBefore':before,'sourceAfter':after,'bytes':target.stat().st_size})
record={'schema':'reverse-completed-md-text-input-freeze/1','round':6,'capturedAt':datetime.now(timezone.utc).isoformat(),'documentId':docid,'publishedMdSha256':sha(DOC),'pins':pins,'publishedMdEqualsProviderAuthoredContent':True,'sourceUnchangedDuringCopy':True,'imagesActuallyViewed':0,'visualApproval':None,'semanticApproval':None,'renderCompleted':None,'semanticProseRewritten':False,'aiOrRenderStarted':False}
with (REPORT/(stem+'-text-frozen-inputs.json')).open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'stem':stem,'sha256':sha(DOC),'lines':len(DOC.read_text(encoding='utf-8').splitlines()),'frozenFiles':len(pins),'images':0,'approval':None}))
