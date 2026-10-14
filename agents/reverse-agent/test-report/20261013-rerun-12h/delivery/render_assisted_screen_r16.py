"""Pinned frozen renderer; reads canonical MD and metadata, never original app/spec."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,sys
HERE=Path(__file__).resolve().parent
AGENT=HERE.parents[2];REPO=HERE.parents[4];REPORT=HERE.parent
RECEIPT=REPORT/'training-assisted/runtime-code-assisted-08.json'
RECEIPT_SHA='e899df4800147e4ecb1cf29d5bde52999ac07f074b6b71d34fa7a48e5d9645aa'
ASSISTED=AGENT/'.tmp/20261013-rerun-12h/training-assisted'
DOCROOT=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'
CAP_MANIFEST=ASSISTED/'snapshot/manifest.json'
CAP_SHA='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
CASES={
 'registration-basic':{'root':'revision-registration-basic-r05','path':'基本設計書/02_学生登録画面.md',
  'sha':'ef8fc585211f4e3b9c06859e7aeb89933b80f49187a13bb6e2bbe8cd09b586ee',
  'id':'CSHARP_ASPNET-BAS-STU-02','job':'revision-registration-basic-r05',
  'destination':'assisted-registration-basic-r06-delivery-r16'},
 'search-detail':{'root':'revision-pending-r02-4a8437c580b548ac','path':'詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',
  'sha':'9a49fb5a1d22094db7c57fdaf751807dd2f69c12367973ea839bc5ff9b037696',
  'id':'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001','job':'revision-pending-r02-4a8437c580b548ac',
  'destination':'assisted-search-detail-r03-delivery-r16'}}
def safe(path):
 path=Path(os.path.abspath(path))
 for p in (path,*path.parents):
  if p.is_symlink() or (p.exists() and getattr(p.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked input/output rejected')
 return path
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
 if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
def stage(value):print(json.dumps({'stage':value,'utc':datetime.now(timezone.utc).isoformat()},ensure_ascii=False),flush=True)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('case',choices=CASES);args=parser.parse_args();case=CASES[args.case]
 if datetime.now(timezone.utc)>=datetime.fromisoformat('2026-10-13T20:15:58+00:00'):raise RuntimeError('Deadline reached')
 stage('metadata-and-full-runtime-verification')
 assert sha(RECEIPT)==RECEIPT_SHA and sha(CAP_MANIFEST)==CAP_SHA
 receipt=json.loads(RECEIPT.read_text(encoding='utf8'));frozen=safe(Path(receipt['destination']))
 assert receipt['fileCount']==126 and inventory(frozen)==receipt['files']
 source=safe(DOCROOT/case['root']/case['path']);draft=safe(ASSISTED/'jobs'/case['job']/'draft-result.json')
 before={str(p):sha(p) for p in [RECEIPT,CAP_MANIFEST,source,draft,Path(__file__)]}
 assert before[str(source)]==case['sha']
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
  'rendererRuntimeFileCount':126,'rendererRuntimeLabel':'r16','frozenRenderImports':module_pins,
  'inputBeforeAfterUnchanged':True,'inputPins':before,'originalApplicationExecuted':False,
  'visualFidelityVerified':False,'formalRubricEvaluated':False,'stateProjectionIncluded':False,
  'createdAt':datetime.now(timezone.utc).isoformat()})
 (destination/'render-pins.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'destination':str(destination),'structure':result['structure']['status'],
  'display':result['display']['status'],'diagrams':len(result['diagrams']),'layouts':len(result['layouts']),
  'errors':[{'id':item['id'],'error':item.get('error')} for item in result['diagrams'] if item['status']!='PASS'],
  'renderPinsSha256':sha(destination/'render-pins.json')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
