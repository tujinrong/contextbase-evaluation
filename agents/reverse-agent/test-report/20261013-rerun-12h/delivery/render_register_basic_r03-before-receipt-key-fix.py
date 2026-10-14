"""Hash-bound derived image QA only; never launches the original application."""
from __future__ import annotations
import argparse, faulthandler, hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
REPORT=HERE.parent
CORE=REPO/'agents/reverse-agent/src/contextbase/ai/rendering.py'
CORE_SHA='0c87df73032d812a3e646ff2846c5daa6b3053472a52dc2b1f78d0c13d41f902'
SOURCE=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts/revision-registration-basic-r03/基本設計書/02_学生登録画面.md'
SOURCE_SHA='efba87eb3db5f99a4df0afba2e607ccc9a36cf3fb2f3e3c615f63d20f3763e44'
RECEIPT=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/jobs/revision-registration-basic-r03/draft-result.json'
OUT=REPORT/'render/assisted-register-basic-r03-delivery'
CAP='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
CHROME=Path('C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe')
MERMAID=REPO/'agents/reverse-agent/.tmp/render-tools/node_modules/mermaid'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def log(stage,**kw):print(json.dumps({'stage':stage,'utc':datetime.now(timezone.utc).isoformat(),**kw},ensure_ascii=False),flush=True)
def worker():
    faulthandler.enable();faulthandler.dump_traceback_later(90,repeat=True)
    before={str(p):sha(p) for p in [SOURCE,CORE,RECEIPT]}
    assert before[str(SOURCE)]==SOURCE_SHA and before[str(CORE)]==CORE_SHA
    receipt=json.loads(RECEIPT.read_text(encoding='utf-8'))
    assert receipt['documentSha256']==SOURCE_SHA and receipt['referenceMode']=='training-assisted'
    assert receipt['sourceSnapshotManifestSha256']==CAP
    log('pins-verified',inputSha256=SOURCE_SHA,coreSha256=CORE_SHA,receiptSha256=before[str(RECEIPT)])
    from contextbase.ai.rendering import render_document
    log('renderer-imported')
    result=render_document(SOURCE,OUT,mermaid_package=MERMAID,chromium_executable=CHROME,document_path='基本設計書/02_学生登録画面.md')
    log('renderer-returned',status=result.get('displayStatus'),diagrams=len(result.get('diagrams',[])),layouts=len(result.get('layouts',[])))
    assert before=={str(p):sha(p) for p in [SOURCE,CORE,RECEIPT]}
    canonical=OUT/'02_学生登録画面.html';canonical.write_bytes((OUT/'document.html').read_bytes())
    result.update({'documentId':'CSHARP_ASPNET-BAS-STU-02','canonicalDocumentPath':'基本設計書/02_学生登録画面.md','canonicalHtmlFilename':canonical.name,
      'canonicalHtmlSha256':sha(canonical),'sourceSnapshotManifestSha256':CAP,'draftResultSha256':before[str(RECEIPT)],'referenceMode':'training-assisted',
      'rendererCodeSha256':CORE_SHA,'createdAt':datetime.now(timezone.utc).isoformat(),'originalApplicationExecuted':False,
      'visualFidelityVerified':False,'formalRubricEvaluated':False,'separateBodyReview':'IN_PROGRESS_AT_RENDER_START'})
    (OUT/'render-pins.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    log('completed',pinsSha256=sha(OUT/'render-pins.json'),inputsUnchanged=True)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:return worker()
    if OUT.exists():raise SystemExit('Fresh output required')
    stdout=HERE/'registration-basic-r03-render-stage.log';stderr=HERE/'registration-basic-r03-render-stderr.log'
    if stdout.exists() or stderr.exists():raise SystemExit('Fresh logs required')
    started=time.monotonic();status='UNKNOWN';code=None
    with stdout.open('xb') as out,stderr.open('xb') as err:
      process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],stdout=out,stderr=err)
      log('owned-worker-started',pid=process.pid,timeoutSeconds=240)
      try:code=process.wait(timeout=240);status='COMPLETE' if code==0 else 'FAILED'
      except subprocess.TimeoutExpired:
        status='TIMED_OUT';subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],check=False,capture_output=True);process.wait(timeout=15)
    record={'status':status,'exitCode':code,'ownedWorkerPid':process.pid,'elapsedSeconds':round(time.monotonic()-started,3),'originalApplicationExecuted':False,
      'sourceSha256After':sha(SOURCE),'rendererSha256After':sha(CORE),'sourceUnchanged':sha(SOURCE)==SOURCE_SHA,'rendererUnchanged':sha(CORE)==CORE_SHA,
      'stdoutPath':str(stdout),'stderrPath':str(stderr),'output':str(OUT)}
    (HERE/'registration-basic-r03-render-worker.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');log('worker-final',**record)
    return 0 if status=='COMPLETE' else 1
if __name__=='__main__':sys.exit(main() or 0)
