"""Independent metadata-helper code-only audit. Synthetic filesystem objects, no CLI."""
import ast,hashlib,json,os
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
ROOT=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent')
P=ROOT/'.tmp/20261014-nenkin-high-01/delivery/connect_print_metadata_v2_62_r01.py'
O=ROOT/'report/20261014-nenkin-high-01/delivery-audit-r01'
expected='6ee87012a2697aea4e8db8b1e5722f761a9470703e5af5adbbeb73b3ff26f307'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)==expected
tree=ast.parse(P.read_text(encoding='utf-8'));fns={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
calls=[]
class FakeNode:
    def __init__(self,name,attrs=0):self.name=name;self.attrs=attrs
    def absolute(self):return self
    def resolve(self):return self
    def is_relative_to(self,root):return True
    def is_symlink(self):calls.append(('is_symlink',self.name));return False
    def lstat(self):calls.append(('lstat',self.name));return SimpleNamespace(st_file_attributes=self.attrs)
    def exists(self):return True
    def is_file(self):return True
    @property
    def parents(self):return [fake_root]
    def __eq__(self,other):return isinstance(other,FakeNode) and self.name==other.name
    def __str__(self):return self.name
fake_root=FakeNode('synthetic-own-root')
inside_link=FakeNode('synthetic-inward-reparse-child',0x400)
def require(ok,message):
    if not ok:raise ValueError(message)
env={'Path':lambda value:inside_link,'RUN_DELIVERY':fake_root,'os':os,'require':require}
exec(compile(ast.Module(body=[fns['safe_run_path']],type_ignores=[]),str(P),'exec'),env)
returned=env['safe_run_path']('synthetic-only',exists=True)
assert returned is inside_link and not any(c[0]=='lstat' for c in calls)
env2={'require':require}
exec(compile(ast.Module(body=[fns['sheet_settings']],type_ignores=[]),str(P),'exec'),env2)
other_list_rejected=False
try:env2['sheet_settings']({'ordinal':0,'name':'synthetic-general-list','kind':'list','columns':3,'headerRow':1,'lastRow':4})
except ValueError:other_list_rejected=True
assert other_list_rejected
assert sha(P)==expected
record={'schema':'spec-agent-print-metadata-independent-code-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'CODE_ONLY_SYNTHETIC_METADATA_GATES','helper':str(P),'helperSha256':expected,'status':'HOLD_PATH_REPARSE_GATE','findings':[{'severity':'repair-before-actual-apply','code':'WINDOWS_INWARD_REPARSE_NOT_REJECTED','function':'safe_run_path','evidence':{'fakeNodeIsSymlink':False,'fakeNodeFileAttributes':'0x400','fakeResolveStaysWithinOwnRoot':True,'currentGateReturnedInput':True,'lstatCalls':0},'requestedRepair':'fresh helper version must reject all linked/reparse input/output/parent paths with lstat bit 0x400; preserve r01 evidence'},{'severity':'contract-gap','code':'OTHER_LIST_COLUMNS','evidence':'model preserves declared non-item LIST columns; current print helper accepts list columns=10 only','currentHandling':'HOLD_OTHER_LIST; do not force source values into new ten columns or silently reinterpret GRID'}],'positives':['Public Expat namespace-aware byte spans and quote-aware opening-tag changes.','Per-splice exact inverse restoration and preserved raw nonprinting segments.','Nonselected ZIP payload and local compressed records retained; central offsets are recorded changes.','Selected/nonselected worksheet physical-member alias denied.','Selected definedName scope limited to print area/titles and local ordinal.','Classic UTF8 stored/deflate ZIP, PI/DTD/entity/external/macro/unsafe parts denied.','Fresh separate CLI output and exact source/plan/author-receipt byte pins; source never saved.'],'authorSelfProbes':{'path':str(O/'print-metadata-synthetic-r03/result.json'),'sha256':sha(O/'print-metadata-synthetic-r03/result.json'),'count':34,'independentlyRerun':False},'codeFileUnchanged':True,'actualWindowsJunctionCreated':False,'actualXlsxReadOrModified':False,'artifactToolExecuted':False,'providerExecuted':False,'mainExecuted':False,'markerExecuted':False,'productionInputRead':False,'wholeApproval':False,'limitations':['Caller authorship and actual header/last-row/column extent still require independent binding.','This is a structural synthetic reparse probe, not a Windows live junction test.','No complete race-free or in-memory execution proof is claimed.']}
target=O/'print-metadata-independent-code-review-r01.json'
with target.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(target),'sha256':sha(target),'status':record['status']},ensure_ascii=False))
