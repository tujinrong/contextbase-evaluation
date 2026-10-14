"""Bounded owner for the existing immutable render_pinned script, source-only."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[4];REPORT=HERE.parent
SOURCE=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-detail-07/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md'
BASE=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only'
RECEIPT=BASE/'jobs/search-detail-07/draft-result.json';CAP=BASE/'snapshot'
CORE=REPO/'agents/reverse-agent/src/contextbase/ai/rendering.py';HELPER=REPORT/'scripts/render_pinned.py'
DEST=REPORT/'render/search-detail-r04'
PINS={SOURCE:'85cddae02cf89e6e92d84ecc7709a118f298ca114bf104115f1be8ae47d62b82',RECEIPT:'90f26375d506807806f030d4b0cd5b4391f3491eccbf04b9dc8694e0a20f16fc',
 CAP/'manifest.json':'2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b',CORE:'0c87df73032d812a3e646ff2846c5daa6b3053472a52dc2b1f78d0c13d41f902',HELPER:'a975d8181a8a601236b5d8b08165a0a1ad80b674461aa855eeae6873dd326c82'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert all(sha(p)==v for p,v in PINS.items()) and not DEST.exists()
 receipt=json.loads(RECEIPT.read_text(encoding='utf-8'));assert receipt['referenceMode']=='source-only' and receipt['snapshot']['manifestSha256']==PINS[CAP/'manifest.json']
 stdout=HERE/'source-detail07-render-stage.log';stderr=HERE/'source-detail07-render-stderr.log'
 assert not stdout.exists() and not stderr.exists()
 env=dict(os.environ);env['CONTEXTBASE_MERMAID_PACKAGE']=str(REPO/'agents/reverse-agent/.tmp/render-tools/node_modules/mermaid');env['CONTEXTBASE_CHROMIUM_EXE']='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
 command=[sys.executable,'-X','faulthandler',str(HELPER),'--draft-result',str(RECEIPT),'--document',str(SOURCE),'--snapshot',str(CAP),'--destination',str(DEST)]
 started=time.monotonic();status='UNKNOWN';code=None
 with stdout.open('xb') as out,stderr.open('xb') as err:
  process=subprocess.Popen(command,stdout=out,stderr=err,env=env)
  print(json.dumps({'stage':'owned-source-render-started','pid':process.pid,'timeoutSeconds':240,'utc':datetime.now(timezone.utc).isoformat()}),flush=True)
  try:code=process.wait(timeout=240);status='COMPLETE' if code==0 else 'FAILED'
  except subprocess.TimeoutExpired:
   status='TIMED_OUT';subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True);process.wait(timeout=15)
 after={str(p):sha(p) for p in PINS};unchanged=all(after[str(p)]==v for p,v in PINS.items())
 record={'status':status,'ownedWorkerPid':process.pid,'elapsedSeconds':round(time.monotonic()-started,3),'exitCode':code,'pinnedInputHashes':{str(p):v for p,v in PINS.items()},'inputHashesAfter':after,'allInputsUnchanged':unchanged,'destination':str(DEST),'referenceMode':'source-only','originalApplicationExecuted':False,'formalRubricEvaluated':False,'visualFidelityVerified':False}
 if status=='COMPLETE':
  pins=DEST/'render-pins.json';meta=json.loads(pins.read_text(encoding='utf-8'));assert meta['sourceSha256']==PINS[SOURCE] and meta['sourceSnapshotManifestSha256']==PINS[CAP/'manifest.json'] and meta['referenceMode']=='source-only'
  record.update({'renderPinsSha256':sha(pins),'canonicalHtmlSha256':meta['canonicalHtmlSha256'],'structure':meta['structure']['status'],'display':meta['display']['status'],'diagrams':len(meta['diagrams']),'layouts':len(meta['layouts'])})
 path=HERE/'source-detail07-render-worker.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,ensure_ascii=False),flush=True)
 return 0 if status=='COMPLETE' and unchanged else 1
if __name__=='__main__':sys.exit(main())
