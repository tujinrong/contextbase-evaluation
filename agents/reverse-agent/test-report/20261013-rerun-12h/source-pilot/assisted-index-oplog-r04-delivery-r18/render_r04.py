"""Pinned frozen renderer; reads canonical MD and metadata, never original app/spec."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,sys,subprocess,time,faulthandler
HERE=Path(__file__).resolve().parent
AGENT=HERE.parents[3];REPO=HERE.parents[5];REPORT=HERE.parents[1]
RECEIPT=REPORT/'training-assisted/runtime-code-assisted-10.json'
RECEIPT_SHA='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
ASSISTED=AGENT/'.tmp/20261013-rerun-12h/training-assisted'
DOCROOT=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'
CAP_MANIFEST=ASSISTED/'snapshot/manifest.json'
CAP_SHA='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
CASES={'table-index': {'root': 'revision-table-index-r04', 'path': '基本設計書/03_テーブル仕様書.md', 'sha': 'd328d6a6f42f201b8d4026aa091b123a84ecd36fe8ae70729fd20b8dd6872eb7', 'id': 'CSHARP_ASPNET-BAS-STU-03', 'job': 'revision-table-index-r04', 'destination': 'assisted-table-index-r04-delivery-r18', 'reviewedPin': 'reviewed-table-index-r04-r11-pin.json', 'reviewedPinSha256': 'a35d6145a5f056fdca062f2e5b18a47a8405b0041c9ef029300a8455c0ba71c4'}, 'operation-log': {'root': 'revision-operation-log-r04', 'path': '基本設計書/テーブル/05_t_operation_log.md', 'sha': '7067c165e324756fb909048d2f3c6735ed3824bb6512c66155015ba6c5703b48', 'id': 'CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG', 'job': 'revision-operation-log-r04', 'destination': 'assisted-operation-log-r04-delivery-r18', 'reviewedPin': 'reviewed-operation-log-r04-r11-pin.json', 'reviewedPinSha256': '34af4227c5b28000427376f7f6c454783c712d010222d581333bdce43888d73a'}}
def safe(path):
 path=Path(os.path.abspath(path))
 for p in (path,*path.parents):
  if p.is_symlink() or (p.exists() and getattr(p.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked input/output rejected')
 return path
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
 if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
def stage(value):print(json.dumps({'stage':value,'utc':datetime.now(timezone.utc).isoformat()},ensure_ascii=False),flush=True)
def worker():
 faulthandler.enable();faulthandler.dump_traceback_later(90,repeat=True)
 parser=argparse.ArgumentParser();parser.add_argument('case',choices=CASES);parser.add_argument('--worker',action='store_true');args=parser.parse_args();case=CASES[args.case]
 if datetime.now(timezone.utc)>=datetime.fromisoformat('2026-10-13T20:15:58+00:00'):raise RuntimeError('Deadline reached')
 stage('metadata-and-full-runtime-verification')
 assert sha(RECEIPT)==RECEIPT_SHA and sha(CAP_MANIFEST)==CAP_SHA
 receipt=json.loads(RECEIPT.read_text(encoding='utf8'));frozen=safe(Path(receipt['destination']))
 assert receipt['fileCount']==126 and inventory(frozen)==receipt['files']
 source=safe(DOCROOT/case['root']/case['path']);draft=safe(ASSISTED/'jobs'/case['job']/'draft-result.json')
 before={str(p):sha(p) for p in [RECEIPT,CAP_MANIFEST,source,draft,Path(__file__)]}
 assert before[str(source)]==case['sha']
 rootpin=safe(REPORT/'training-assisted'/case['reviewedPin'])
 assert sha(rootpin)==case['reviewedPinSha256']
 approved_pin=json.loads(rootpin.read_text(encoding='utf8'))
 assert approved_pin['sha256']==case['sha'] and approved_pin['documentId']==case['id'] and approved_pin['path']==case['path']
 assert safe(approved_pin['canonicalMarkdown'])==source and safe(approved_pin['draftResult'])==draft
 assert approved_pin['independentReviewApproved'] is True and approved_pin['structureStatus']=='STRUCTURE_VALID'
 assert approved_pin['noFurtherTextRevisionPlanned'] is True and approved_pin['capsule']['manifestSha256']==CAP_SHA
 verified=safe(approved_pin['independentReview']);handoff=safe(verified.with_name('review-handoff.json'))
 assert sha(verified)==approved_pin['independentReviewSha256'] and sha(draft)==approved_pin['draftResultSha256']
 handoff_meta=json.loads(handoff.read_text(encoding='utf8'))
 assert handoff_meta['approved'] is True and handoff_meta['documentSha256']==case['sha']
 assert handoff_meta['referenceMode']=='training-assisted' and handoff_meta['snapshot']['manifestSha256']==CAP_SHA
 assert handoff_meta['reviewSha256']==sha(verified) and safe(handoff_meta['documentFile'])==source
 for pin in (rootpin,verified,handoff):before[str(pin)]=sha(pin)
 metadata=json.loads(draft.read_text(encoding='utf8'))
 assert metadata['contentSha256']==case['sha'] and metadata['path']==case['path'] and metadata['documentId']==case['id']
 assert metadata['aiAuthored'] is True and metadata['referenceMode']=='training-assisted'
 assert metadata['snapshot']['manifestSha256']==CAP_SHA
 sys.path.insert(0,str(frozen))
 from contextbase.ai.rendering import render_document
 module_pins={}
 for name,pin in receipt['renderImports'].items():
  module=sys.modules[name];expected=safe(Path(pin['path']));spec=importlib.util.find_spec(name)
  assert safe(Path(module.__file__))==expected and safe(Path(module.__spec__.origin))==expected
  assert safe(Path(spec.origin))==expected and sha(expected)==pin['sha256']
  module_pins[name]={'path':str(expected),'sha256':sha(expected)}
 destination=safe(REPORT/'render'/case['destination']);assert not destination.exists()
 stage('trusted-render-start')
 result=render_document(source,destination,asset_root=DOCROOT/case['root'],document_path=case['path'],
  mermaid_package=Path(os.environ['CONTEXTBASE_MERMAID_PACKAGE']),
  chromium_executable=Path(os.environ['CONTEXTBASE_CHROMIUM_EXE']))
 stage('trusted-render-completed-input-after-check')
 assert inventory(frozen)==receipt['files'] and all(sha(Path(p))==value for p,value in before.items())
 for name,pin in module_pins.items():assert sha(Path(pin['path']))==pin['sha256']
 canonical=destination/(source.stem+'.html');canonical.write_bytes((destination/'document.html').read_bytes())
 result.update({'documentId':case['id'],'canonicalDocumentPath':case['path'],'canonicalHtmlFilename':canonical.name,
  'canonicalHtmlSha256':sha(canonical),'sourceSnapshotManifestSha256':CAP_SHA,'draftResultSha256':sha(draft),
  'referenceMode':'training-assisted','rendererRuntimeReceipt':str(RECEIPT),'rendererRuntimeReceiptSha256':RECEIPT_SHA,
  'rendererRuntimeFileCount':126,'rendererRuntimeLabel':'r18','frozenRenderImports':module_pins,
  'inputBeforeAfterUnchanged':True,'inputPins':before,'originalApplicationExecuted':False,
  'visualFidelityVerified':False,'formalRubricEvaluated':False,'stateProjectionIncluded':False,
  'createdAt':datetime.now(timezone.utc).isoformat()})
 (destination/'render-pins.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'destination':str(destination),'structure':result['structure']['status'],
  'display':result['display']['status'],'diagrams':len(result['diagrams']),'layouts':len(result['layouts']),
  'errors':[{'id':item['id'],'error':item.get('error')} for item in result['diagrams'] if item['status']!='PASS'],
  'renderPinsSha256':sha(destination/'render-pins.json')},ensure_ascii=False),flush=True)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('case',choices=CASES);parser.add_argument('--worker',action='store_true');args=parser.parse_args()
 if args.worker:return worker()
 deadline=datetime.fromisoformat('2026-10-13T20:15:58+00:00')
 remaining=(deadline-datetime.now(timezone.utc)).total_seconds()
 if remaining<=0:raise RuntimeError('Deadline reached')
 timeout=min(240,remaining);started=time.monotonic()
 out=HERE/('screen-r18-'+args.case+'-worker.json');assert not out.exists()
 process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),args.case,'--worker'])
 stage('owned-worker-'+str(process.pid));status='UNKNOWN';code=None
 try:code=process.wait(timeout=timeout);status='COMPLETE' if code==0 else 'FAILED'
 except subprocess.TimeoutExpired:
  status='TIMED_OUT'
  subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20)
  process.wait(timeout=15)
 out.write_text(json.dumps({'status':status,'ownedWorkerPid':process.pid,'exitCode':code,'elapsedSeconds':round(time.monotonic()-started,3),'timeoutSeconds':timeout,'applicationExecuted':False},indent=2)+'\n',encoding='utf8')
 return 0 if status=='COMPLETE' else 1
if __name__=='__main__':sys.exit(main() or 0)
