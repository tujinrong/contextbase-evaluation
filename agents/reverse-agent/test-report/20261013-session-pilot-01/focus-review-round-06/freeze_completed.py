"""Exclusive byte freeze of one completed Round6 document, never runs a job."""
from pathlib import Path
import hashlib,json,shutil,sys
from datetime import datetime,timezone
ROOT=Path(r'D:\開発\contextbase-evaluation').resolve()
REPORT=Path(__file__).resolve().parent
JOBS=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-06'
STEMS={'student-search':('488af9821732c8f6','SM-DET-STUDENT-SEARCH'),'student-editor':('eebb51fa1eb2da8f','SM-DET-STUDENT-EDITOR')}
stem=sys.argv[1]
jobname,docid=STEMS[stem]
JOB=JOBS/jobname;RENDER=JOBS/'render'/stem
DOC=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-06/spec/detail'/(stem+'.md')
RREPORT=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-round-06'/(stem+'-render.json')
TARGET=REPORT/'frozen'/stem
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def confined(base,rel):
    p=(base/rel).resolve()
    assert p.is_relative_to(base.resolve())
    return p
deadline=datetime.fromisoformat('2026-10-13T03:20:58+00:00')
assert datetime.now(timezone.utc)<deadline,'No new freeze/review after deadline'
m=read(RENDER/'manifest.json');d=read(JOB/'draft-result.json')
r=read(JOB/'draft/result.json');a=read(JOB/'draft/answer.txt')
assert r['exit_code']==0 and r['answer']==a
assert r['metadata']['status']=='passed'  # Provider schema completion only.
assert r['metadata']['answer_sha256']==sha(JOB/'draft/answer.txt')
assert r['metadata']['prompt_sha256']==sha(JOB/'draft/prompt.txt')
assert r['metadata']['reference_mode']=='training-assisted'
assert a['documentId']==d['documentId']==docid
assert a['path']==d['path']=='spec/detail/'+stem+'.md'
assert d['aiAuthored'] is True and d['semanticProseAssembledByPython'] is False
content_sha=hashlib.sha256(a['content'].encode('utf-8')).hexdigest()
assert sha(DOC)==content_sha==m['sourceSha256']==d['contentSha256']
assert Path(m['source']).resolve()==DOC and m['originalModified'] is False
assert read(RREPORT)['sourceSha256']==content_sha
assert m['display']['documentCapture']['complete'] is True
for k in ('diagrams','layouts'):
    for item in m[k]:
        assert sha(RENDER/(item['id']+'.png'))==item['png']['sha256']
        if k=='diagrams':assert sha(RENDER/(item['id']+'.mmd'))==item['sourceSha256']
for item in m['display']['documentCapture']['pages']:
    assert sha(confined(RENDER,item['path']))==item['png']['sha256']
artifact_field='files' if 'files' in m else 'artifacts'
artifacts=[(DOC,stem+'.md'),(JOB/'draft-result.json','draft-result.json'),(RENDER/'manifest.json','manifest.json'),(RREPORT,'render-report.json'),(JOB/'draft/answer.txt','provider-answer.txt'),(JOB/'draft/result.json','provider-result.json')]
for item in m[artifact_field]:
    p=confined(RENDER,item['path']);assert sha(p)==item['sha256']
    artifacts.append((p,item['path']))
assert len({name for _,name in artifacts})==len(artifacts)
assert {p.name for p in RENDER.glob('*.png')}=={Path(name).name for _,name in artifacts if name.endswith('.png')}
TARGET.mkdir(parents=True,exist_ok=False)
pins=[]
for source,name in artifacts:
    before=sha(source);target=confined(TARGET,name);target.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as incoming,target.open('xb') as outgoing:shutil.copyfileobj(incoming,outgoing)
    copied=sha(target);after=sha(source);assert before==copied==after
    pins.append({'sourcePath':source.relative_to(ROOT).as_posix(),'frozenPath':target.relative_to(ROOT).as_posix(),'sha256':copied,'sourceBefore':before,'sourceAfter':after,'bytes':target.stat().st_size})
image_count=sum(p['frozenPath'].endswith('.png') for p in pins)
record={'schema':'reverse-completed-md-native-input-freeze/1','capturedAt':datetime.now(timezone.utc).isoformat(),'documentId':docid,'round':6,'publishedMdSha256':content_sha,'completedMdBoundToProviderAnswerDraftAndCanonicalManifest':True,'imagesFrozen':image_count,'sourceUnchangedDuringCopy':True,'pins':pins,'approved':None,'imagesActuallyViewed':0,'aiOrRenderingStarted':False,'semanticProseRewritten':False,'structure':m['structure']['status'],'display':m['display']['status']}
with (REPORT/(stem+'-frozen-inputs.json')).open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'stem':stem,'frozenFiles':len(pins),'frozenImages':image_count,'sha256':content_sha,'structure':m['structure']['status'],'display':m['display']['status'],'approval':None}))
