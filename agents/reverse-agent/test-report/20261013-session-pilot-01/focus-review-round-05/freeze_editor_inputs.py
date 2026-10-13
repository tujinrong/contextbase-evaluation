"""Freeze only completed published MD/render artifacts, without generating/rewriting prose."""
import hashlib,json,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path.cwd().resolve();REPORT=Path(__file__).resolve().parent
JOBS=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-05'
JOB=JOBS/'eebb51fa1eb2da8f';RENDER=JOBS/'render/student-editor'
DOC=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05/spec/detail/student-editor.md'
TARGET=REPORT/'frozen/student-editor'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
m=read(RENDER/'manifest.json');d=read(JOB/'draft-result.json')
assert sha(DOC)==m['sourceSha256']==d['contentSha256']=='5cec039f58141cbac0318ca8b937336fcc9234179b066f72a77083b71e6d81a7'
assert Path(m['source']).resolve()==DOC and m['originalModified'] is False
assert m['structure']['status']==m['display']['status']=='PASS'
assert len(m['diagrams'])==22 and len(m['layouts'])==3
artifacts=[(DOC,'student-editor.md'),(JOB/'draft-result.json','draft-result.json'),(RENDER/'manifest.json','manifest.json'),(RENDER/'document.html','document.html')]
for k in ('layouts','diagrams'):
    for i in m[k]:
        p=RENDER/(i['id']+'.png');assert sha(p)==i['png']['sha256'];artifacts.append((p,p.name))
        if k=='diagrams':
            p=RENDER/(i['id']+'.mmd');assert sha(p)==i['sourceSha256'];artifacts.append((p,p.name))
for i in m['display']['documentCapture']['pages']:
    p=RENDER/i['path'];assert sha(p)==i['png']['sha256'];artifacts.append((p,p.name))
TARGET.mkdir(parents=True,exist_ok=False)
pins=[]
for source,name in artifacts:
    before=sha(source);target=TARGET/name
    with source.open('rb') as incoming,target.open('xb') as outgoing:shutil.copyfileobj(incoming,outgoing)
    copied=sha(target);after=sha(source);assert before==copied==after
    pins.append({'sourcePath':source.relative_to(ROOT).as_posix(),'frozenPath':target.relative_to(ROOT).as_posix(),'sha256':copied,'sourceBefore':before,'sourceAfter':after,'bytes':target.stat().st_size})
(REPORT/'student-editor-frozen-inputs.json').write_text(json.dumps({'schema':'reverse-completed-md-native-input-freeze/1','capturedAt':datetime.now(timezone.utc).isoformat(),'documentId':'SM-DET-STUDENT-EDITOR','round':5,'completedMdBoundToDraftAndCanonicalManifest':True,'imagesFrozen':39,'sourceUnchangedDuringCopy':True,'pins':pins,'searchFreezeIsSeparate':True,'editorApproved':None,'aiOrRenderingStarted':False,'semanticProseRewritten':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'frozenFiles':len(pins),'frozenImages':39,'sourceUnchanged':True}))

