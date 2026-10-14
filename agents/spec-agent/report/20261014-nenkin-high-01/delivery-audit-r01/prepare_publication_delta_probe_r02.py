"""Preserve failed virtual harness and add complete target mocking and I/O refusal."""
import ast,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
old=A/'probe_publication_bound_r03_delta_r01.py';raw=old.read_bytes();before=hashlib.sha256(raw).hexdigest()
record={'schema':'spec-agent-independent-probe-harness-failure/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'INDEPENDENT_SYNTHETIC_HARNESS_FAILURE','harness':str(old),'harnessSha256':before,
 'finding':'The harness left publish global TARGET as a real Path. Two TARGET.exists() calls inspected real output existence metadata before the virtual positive failed.',
 'realOutputExistenceMetadataRead':True,'realOutputExistenceMetadataReadCount':2,
 'actualOutputBodyRead':False,'actualOutputHashRead':False,'actualOutputCopied':False,'actualOutputRenamed':False,
 'actualStageCreated':False,'actualBackupExecuted':False,'actualSourceOrCapsuleRead':False,
 'helpersChanged':False,'oldRecordsChanged':False,'candidateApproval':False,'published':False,
 'repair':'Fresh harness binds TARGET/WORK/REPORT to virtual MemPath, and refuses real Path filesystem I/O under actual output/input/capsule roots.'}
rp=A/'publication-r03-independent-harness-failure-r01.json'
with rp.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
text=raw.decode('utf-8')
oldline="env.update(validate=lambda p,g,h:(files,MemPath(base_plan['transactionRoot'])),safe=lambda p:MemPath(p),"
newline="env.update(TARGET=MemPath(T),WORK=MemPath(W),REPORT=MemPath(R),validate=lambda p,g,h:(files,MemPath(base_plan['transactionRoot'])),safe=lambda p:MemPath(p),"
assert text.count(oldline)==1;text=text.replace(oldline,newline)
anchor="old_probe=OLD_PROBE.read_text(encoding='utf-8')"
guard='''forbidden_real_access=[]
FORBIDDEN=(Path(r'D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\output'),Path(r'D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\input'),Path(r'D:\\開発\\contextbase-evaluation\\agents\\spec-agent\\.tmp\\20261014-nenkin-high-01\\capsule'))
for _method in ('exists','stat','lstat','resolve','open','read_bytes','read_text','rename','replace','mkdir','unlink','rmdir','iterdir','glob','rglob'):
    _original=getattr(Path,_method)
    def _guarded(self,*args,_method=_method,_original=_original,**kwargs):
        p=Path(self)
        if any(p==root or p.is_relative_to(root) for root in FORBIDDEN):
            forbidden_real_access.append({'operation':_method,'path':str(p)})
            raise AssertionError('Actual protected-path I/O refused in virtual probe')
        return _original(self,*args,**kwargs)
    setattr(Path,_method,_guarded)
'''
assert text.count(anchor)==1;text=text.replace(anchor,guard+'\n'+anchor)
text=text.replace("p=A/'publication-r03-independent-delta-probes-r01.json'","p=A/'publication-r03-independent-delta-probes-r02.json'")
text=text.replace("'actualOutputRead':False,'actualOutputBodyRead':False", "'failedPreviousHarnessMetadataReadReceipt':{'path':str(A/'publication-r03-independent-harness-failure-r01.json'),'sha256':sha((A/'publication-r03-independent-harness-failure-r01.json').read_bytes())},'actualProtectedPathAccessRefusalInstalled':True,'actualProtectedPathAccessAttempts':forbidden_real_access,'actualOutputRead':False,'actualOutputExistenceMetadataRead':False,'actualOutputBodyRead':False")
text=text.replace("assert sha(source.read_bytes())==expected_sha", "assert not forbidden_real_access\nassert sha(source.read_bytes())==expected_sha")
ast.parse(text)
target=A/'probe_publication_bound_r03_delta_r02.py'
with target.open('x',encoding='utf-8') as h:h.write(text)
assert hashlib.sha256(old.read_bytes()).hexdigest()==before
print(json.dumps({'failureReceipt':str(rp),'failureReceiptSha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'freshHarness':str(target),'freshHarnessSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'oldHarnessPreserved':True},ensure_ascii=False))
