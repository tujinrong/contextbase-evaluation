"""Functions-only synthetic reparse/provenance probe; no collection/provider/material read."""
import ast,hashlib,json,copy
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
R=Path(__file__).parent;P=R.parents[4]/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/collect_reviewed_v2.py'
EXPECTED='c63b5bd6bb7fd5222b157113a43bfbe7750a47df433311187ae22e1372b7ead6'
raw=P.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED;tree=ast.parse(raw.decode('utf8'))
reads=[];safe_calls=[]
class Linked:
 parts=('synthetic','module.py');suffix='.py'
 def resolve(self):return self
 def relative_to(self,root):return Path('module.py')
 def is_file(self):return True
 def read_bytes(self):reads.append('linked-read');return b'synthetic-same-bytes'
 def __str__(self):return 'C:/synthetic/runtime/module.py'
def safe(path):safe_calls.append(str(path));raise ValueError('synthetic reparse refused')
ns={'hashlib':hashlib,'Path':Path,'capsule':SimpleNamespace(safe_path=safe)}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'sha','pin','runtime_inventory'}]
exec(compile(ast.Module(body=copy.deepcopy(nodes),type_ignores=[]),'<functions-only-synthetic>','exec'),ns)
linked=Linked();expected=hashlib.sha256(b'synthetic-same-bytes').hexdigest();pins={}
ns['pin'](linked,pins,expected)
assert reads==['linked-read'] and safe_calls==[]
reads.clear();inventory=ns['runtime_inventory'](SimpleNamespace(rglob=lambda _: [linked]))
assert inventory=={'module.py':expected} and reads==['linked-read'] and safe_calls==[]
report={'schema':'reverse-agent-independent-collection-boundary-finding/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'CHANGES_REQUIRED_PATH_READ_BOUNDARY',
 'helper':str(P),'helperSha256':EXPECTED,'providerCalls':0,'wholeHelperExecuted':False,'productionDataRead':False,'syntheticFunctionsOnly':True,
 'findings':[{'function':'pin','line':next(n.lineno for n in nodes if n.name=='pin'),'reproduction':'Synthetic linked file with matching bytes is resolved and read without capsule.safe_path. safe_path spy0, file read1.','repair':'Check nonresolved original path with capsule.safe_path before resolve/read, and recheck on each final hash.'},
 {'function':'runtime_inventory','line':next(n.lineno for n in nodes if n.name=='runtime_inventory'),'reproduction':'Synthetic linked runtime module with expected bytes yields the expected complete inventory; safe_path spy0, linked read1.','repair':'Use capsule.safe_path(directory) and capsule.safe_path(each file) before every read, including after-copy inventory and assert_unchanged.'}],
 'limits':['This isolates two read-boundary gaps; the full eleven-document metadata/copy workflow has not been audited or executed.',
 'Adding assisted06 receipt to a fresh version alone does not address these existing guards.']}
out=R/'collection-v2-independent-path-findings.json'
with out.open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
assert hashlib.sha256(P.read_bytes()).hexdigest()==EXPECTED
print(json.dumps({'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'linkedAcceptancesReproduced':2,'providerCalls':0},ensure_ascii=False))
