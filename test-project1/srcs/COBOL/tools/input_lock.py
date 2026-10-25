"""Lock/check only this project's fully expanded specification inputs."""
from pathlib import Path
import hashlib,json,sys,re,datetime,os
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
 manifest.parent.mkdir(parents=True,exist_ok=True)
 manifest.write_text(json.dumps({'project':'COBOL','version':'8.0','createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':current},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:
 expected=json.loads(manifest.read_text(encoding='utf-8'))['inputs']
 if current!=expected:raise SystemExit('Specification input drift; review and fix the input lock before generation/build.')
print(f'COBOL local input lock: {len(current)} files verified.')
