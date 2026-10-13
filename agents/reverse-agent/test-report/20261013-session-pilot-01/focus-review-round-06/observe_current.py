"""Observe only the already-authorized Round6 files; no jobs or source execution."""
from pathlib import Path
import hashlib, json, re
from datetime import datetime, timezone
ROOT=Path(r"D:\開発\contextbase-evaluation").resolve()
BASE=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01'
JOBS=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-06'
OUTPUT=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-06/spec/detail'
EXPECTED_CONFIG='agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-06-config.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
handoffs=[(int(re.search(r'-(\d+)\.json$',p.name).group(1)),p) for p in BASE.glob('focus-continuation-handoff-*.json') if re.search(r'-(\d+)\.json$',p.name)]
_,hp=max(handoffs)
h=read(hp)
record={'schema':'reverse-current-native-input-observation/1','observedAt':datetime.now(timezone.utc).isoformat(),'handoff':hp.name,'activeConfig':h.get('activeConfig'),'configUnchanged':h.get('activeConfig')==EXPECTED_CONFIG,'deadline':h.get('deadline'),'duplicateAiOrRenderStarted':False,'documents':[]}
if record['configUnchanged']:
    for stem,jobname in [('student-search','488af9821732c8f6'),('student-editor','eebb51fa1eb2da8f')]:
        job=JOBS/jobname;md=OUTPUT/(stem+'.md');draft=job/'draft-result.json';render=JOBS/'render'/stem/'manifest.json';rr=BASE/'focus-round-06'/(stem+'-render.json')
        item={'stem':stem,'mdExists':md.is_file(),'draftResultExists':draft.is_file(),'renderManifestExists':render.is_file(),'renderReportExists':rr.is_file(),'completedCandidate':False,'approved':None}
        item['providerStages']={}
        for stage in ('analysis','draft'):
            result=job/stage/'result.json'
            if result.is_file():
                provider=read(result)
                item['providerStages'][stage]={'resultExists':True,'resultSha256':sha(result),'status':provider.get('metadata',{}).get('status'),'exitCode':provider.get('exit_code')}
            else:
                item['providerStages'][stage]={'resultExists':False,'completionVerified':None}
        if md.is_file() and draft.is_file():
            d=read(draft);item.update({'documentId':d.get('documentId'),'publishedMdSha256':sha(md),'draftContentSha256':d.get('contentSha256'),'mdMatchesDraft':sha(md)==d.get('contentSha256')})
        if render.is_file():
            m=read(render);item.update({'renderSourceSha256':m.get('sourceSha256'),'renderSource':m.get('source'),'structure':m.get('structure',{}).get('status'),'display':m.get('display',{}).get('status'),'diagrams':len(m.get('diagrams',[])),'layouts':len(m.get('layouts',[])),'textTiles':len(m.get('display',{}).get('documentCapture',{}).get('pages',[]))})
            item['completedCandidate']=bool(item.get('mdMatchesDraft') and item.get('publishedMdSha256')==m.get('sourceSha256') and m.get('display',{}).get('documentCapture',{}).get('complete') and rr.is_file())
        record['documents'].append(item)
print(json.dumps(record,ensure_ascii=False))
