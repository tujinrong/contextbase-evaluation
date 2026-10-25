"""Lock/check only this project's fully expanded specification inputs."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib,json,sys,re,datetime,os
from output_paths import write_json
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT.parent.parent/'spec'/ROOT.name
manifest=ROOT/'build/input-manifest.json'
def records():
 result=[]
 if not SPEC.is_dir():raise SystemExit(f'Canonical specification root missing: {SPEC}')
 for p in sorted(SPEC.rglob('*')):
  if not p.is_file():continue
  data=p.read_bytes();meta=None
  if p.suffix=='.md':
   m=re.search(r'<!-- spec-meta: (.*?) -->',data.decode('utf-8'))
   if m:meta=json.loads(m.group(1))
  result.append({'path':Path(os.path.relpath(p, ROOT)).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'documentId':meta.get('documentId') if meta else None,'version':meta.get('version') if meta else None})
 return result
current=records()
if len(sys.argv)>1 and sys.argv[1]=='lock':
 write_json(manifest,{'project':'COBOL','version':next(x['version'] for x in current if x['path'].endswith('/README.md')),'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':current})
else:
 expected=json.loads(manifest.read_text(encoding='utf-8'))['inputs']
 if current!=expected:raise SystemExit('Specification input drift; review and fix the input lock before generation/build.')
print(f'COBOL local input lock: {len(current)} files verified.')
