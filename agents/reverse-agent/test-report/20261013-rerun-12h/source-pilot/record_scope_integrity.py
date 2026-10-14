"""Read and pin the source-only originals/capsule/frozen tool runtime; no app execution."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from contextbase.ai import capsule

parser=argparse.ArgumentParser()
parser.add_argument('--runtime-receipt',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
repo=Path(__file__).resolve().parent.parents[4]
snapshot=repo/'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot'
sha=lambda data:hashlib.sha256(data).hexdigest()
manifest_path=capsule.safe_path(snapshot/'manifest.json')
manifest_bytes=manifest_path.read_bytes()
if sha(manifest_bytes)!='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b':
    raise ValueError('fixed source-only capsule manifest differs')
manifest=capsule.verify(snapshot)
state=capsule.verification_state(snapshot)
if state['manifestSha256']!=sha(manifest_bytes) or state['mode']!='source-only':
    raise ValueError('collected source-only capsule state differs')
source_root=capsule.safe_path(Path(manifest['sourceRoot']))
expected_root=repo/'test-project1/srcs/CSharp_ASPNET'
if source_root!=capsule.safe_path(expected_root):
    raise ValueError('original source root differs')
original=[]
for entry in manifest['files']:
    path=capsule.safe_path(source_root/entry['path'])
    digest=sha(path.read_bytes())
    if digest!=entry['sha256']:
        raise ValueError('original source bytes differ from sealed baseline')
    original.append({'path':str(path),'sha256':digest})
receipt_bytes=args.runtime_receipt.read_bytes()
freeze=json.loads(receipt_bytes)
runtime=capsule.safe_path(Path(freeze['destination']))
inventory={p.relative_to(runtime).as_posix():sha(capsule.safe_path(p).read_bytes()) for p in runtime.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() not in {'.pyc','.pyo'}}
if inventory!=freeze['files']:
    raise ValueError('frozen tool runtime bytes differ from receipt')
value={'classification':'SOURCE_ONLY_SCOPE_INTEGRITY_CHECK_NOT_SPECIFICATION_APPROVAL',
       'createdAt':datetime.now(timezone.utc).isoformat(),'snapshot':str(snapshot),'snapshotState':state,
       'originalSourceCount':len(original),'originalSources':original,'originalSourcesMatchSealedBaseline':True,
       'runtimeReceiptFile':str(args.runtime_receipt.resolve()),'runtimeReceiptSha256':sha(receipt_bytes),
       'runtimeRoot':str(runtime),'runtimeFileCount':len(inventory),'runtimeAllHashesMatchReceipt':True,
       'actualCapsuleImport':str(Path(capsule.__file__).resolve()),'originalAppDatabaseBuildOrTestExecutionPerformed':False,
       'manuscriptBytesModified':False,'originalSpecificationOrEvaluationMaterialsRead':False}
if manifest_path.read_bytes()!=manifest_bytes or args.runtime_receipt.read_bytes()!=receipt_bytes:
    raise ValueError('integrity inputs changed during recording')
with args.output.open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'file':str(args.output.resolve()),'originalSourceCount':len(original),'runtimeFileCount':len(inventory)},ensure_ascii=False))
