"""Fresh publication seal/recovery probes using an entirely in-memory filesystem."""
import ast,copy,hashlib,json,os,sys
from pathlib import Path,PureWindowsPath
from types import SimpleNamespace
from datetime import datetime,timezone
sys.dont_write_bytecode=True
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
OLD_PROBE=A/'probe_publication_bound_r02_r01.py'
forbidden_real_access=[]
FORBIDDEN=(Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\output'),Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\input'),Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\capsule'))
for _method in ('exists','stat','lstat','resolve','open','read_bytes','read_text','rename','replace','mkdir','unlink','rmdir','iterdir','glob','rglob'):
    _original=getattr(Path,_method)
    def _guarded(self,*args,_method=_method,_original=_original,**kwargs):
        p=Path(self)
        if any(p==root or p.is_relative_to(root) for root in FORBIDDEN):
            forbidden_real_access.append({'operation':_method,'path':str(p)})
            raise AssertionError('Actual protected-path I/O refused in virtual probe')
        return _original(self,*args,**kwargs)
    setattr(Path,_method,_guarded)

old_probe=OLD_PROBE.read_text(encoding='utf-8')
prelude=old_probe[:old_probe.index('# Source-only stage-seal inspection')]
prelude=prelude.replace('publication_bound_r02.py','publication_bound_r03.py').replace('fb59aa3097f8284d08276cdf334b001c1d205781507b8863a2feb3fb63709a61','8be4c01b30a73eade999d78a039ba46911167882140f37c028c051716fc7fa6f')
ns_outer={'__name__':'fresh_independent_functions_and_virtual_FS'}
exec(compile(prelude,str(OLD_PROBE)+'-fresh-r03-functions-only','exec'),ns_outer)
ns=ns_outer['ns'];case=ns_outer['case'];tests=ns_outer['tests'];reject=ns_outer['reject']
source=ns_outer['SOURCE'];expected_sha=ns_outer['EXPECTED'];base_plan=ns_outer['base_plan'];base_grant=ns_outer['base_grant'];P=ns_outer['P']
files=ns_outer['files'];stage=ns_outer['stage'];W=ns_outer['W'];R=ns_outer['R'];T=ns_outer['T'];FILE=ns_outer['FILE']
tree=ns_outer['tree'];text=ns_outer['text'];dep_pins=ns_outer['dep_pins'];dependency_receipt=ns_outer['dependency_receipt']
def sha(raw):return hashlib.sha256(raw).hexdigest()
old_source=D/'publication_bound_r02.py';old_bytes=old_source.read_bytes()
assert sha(old_bytes)=='fb59aa3097f8284d08276cdf334b001c1d205781507b8863a2feb3fb63709a61'
old_tree=ast.parse(old_bytes.decode('utf-8'))
old_functions={n.name:ast.dump(n,include_attributes=False) for n in old_tree.body if isinstance(n,ast.FunctionDef)}
new_functions={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
changed=[k for k in old_functions if old_functions[k]!=new_functions[k]]
assert changed==['publish'] and set(new_functions)==set(old_functions)
case('r02-to-r03-only-publish-function-AST-delta',lambda:None)

class VirtualFailure(Exception):pass
class MemContext:
    def __init__(self):
        self.old={f'SYNTHETIC/old-{i:03}.md':'0'*64 for i in range(906)}
        self.expected={f['target']:f['source']['sha256'] for f in files};self.expected['manifest.json']='2'*64
        self.transaction=PureWindowsPath(base_plan['transactionRoot']);self.stage=self.transaction/'stage'
        self.backup=self.transaction/'backup';self.quarantine=self.transaction/'failed-new';self.target=PureWindowsPath(T)
        self.dirs={self.stage:{'id':(1,2),'files':dict(self.expected)},self.target:{'id':(1,1),'files':dict(self.old)}}
        self.data={};self.events=[];self.renames=[];self.pin_calls=[];self.compares=[];self.caps_checks=0
        self.fail_event=None;self.persistent_journal_failure=False;self.journal_failed=False
        self.fail_second_rename=False;self.fail_post_new=False;self.drift_source=None
        self.receipt={'schema':'spec-agent-staged-bundle/1','planSha256':P,'stageRoot':str(self.stage),
                      'directoryIdentity':[1,2],'files':dict(self.expected),'linkIssues':0,
                      'status':'STAGED_BYTES_VERIFIED_NOT_PUBLISHED','actualPublication':False}
        self.grant=copy.deepcopy(base_grant);self.seal()
    def seal(self):
        path=self.transaction/'stage-receipt.json';self.data[path]=json.dumps(self.receipt).encode()
        self.grant.update(stageReceipt={'path':str(path),'sha256':sha(self.data[path])},stageManifestSha256='2'*64)
    def compare(self,path,values):
        path=PureWindowsPath(path);self.compares.append((str(path),dict(values)))
        ns['require'](path in self.dirs and self.dirs[path]['files']==values,'virtual raw-byte inventory mismatch')
    def identity(self,path):return self.dirs[PureWindowsPath(path)]['id']
    def pinned(self,record,roots=(W,R)):
        p=ns['descriptor_shape'](record);ns['require'](ns['within'](p,roots),'virtual descriptor roots')
        key=PureWindowsPath(p);self.pin_calls.append(str(key))
        if key in self.data:observed=sha(self.data[key])
        else:observed='f'*64 if str(key)==self.drift_source else FILE
        ns['require'](record['sha256']==observed,'virtual pinned bytes mismatch')
        return MemPath(key)
    def protected(self,plan):
        self.caps_checks+=1
        if self.fail_post_new and self.target in self.dirs and self.dirs[self.target]['id']==(1,2):raise VirtualFailure('simulated post-new protected-pin failure')
        return [{'role':'original-input','fileCount':345},{'role':'source-capsule','fileCount':179}]
    def writer(self,path,mode):
        key=PureWindowsPath(path)
        if mode=='x':
            if key in self.data:raise FileExistsError('virtual lock exists')
            self.data[key]=b''
        return MemWriter(self,key)

class MemPath(PureWindowsPath):
    context=None
    def read_bytes(self):return self.context.data[PureWindowsPath(self)]
    def exists(self):return PureWindowsPath(self) in self.context.dirs or PureWindowsPath(self) in self.context.data
    def open(self,mode='r',**kwargs):return self.context.writer(self,mode)
    def rename(self,destination):
        c=self.context;old,new=PureWindowsPath(self),PureWindowsPath(destination)
        if c.fail_second_rename and old==c.stage:raise VirtualFailure('simulated second rename failure')
        ns['require'](old in c.dirs and new not in c.dirs,'virtual rename source/target conflict')
        c.dirs[new]=c.dirs.pop(old);c.renames.append((str(old),str(new)));return MemPath(new)

class MemWriter:
    def __init__(self,context,key):self.context=context;self.key=key
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def write(self,text):
        c=self.context
        if self.key.name=='swap-journal.jsonl':
            event=json.loads(text)['event']
            if event==c.fail_event or (c.journal_failed and c.persistent_journal_failure):
                c.journal_failed=True;raise VirtualFailure('simulated journal append failure '+event)
            c.events.append(event)
        c.data[self.key]=c.data.get(self.key,b'')+text.encode();return len(text)
    def flush(self):pass
    def fileno(self):return 31337

pub_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='publish')
def run(context,plan=None,grant=None):
    MemPath.context=context
    env=dict(ns)
    exec(compile(ast.Module(body=[pub_node],type_ignores=[]),str(source),'exec'),env)
    env.update(TARGET=MemPath(T),WORK=MemPath(W),REPORT=MemPath(R),validate=lambda p,g,h:(files,MemPath(base_plan['transactionRoot'])),safe=lambda p:MemPath(p),
               owned=lambda p:MemPath(p),pinned=context.pinned,identity=context.identity,compare=context.compare,
               protected_checks=context.protected,load_baseline=lambda:{'files':context.old},
               os=SimpleNamespace(fsync=lambda fd:None,getpid=lambda:12345))
    return env['publish'](copy.deepcopy(base_plan) if plan is None else plan,
                          context.grant if grant is None else grant,P)

def seal_reject(name,mutate):
    def fn():
        c=MemContext();mutate(c)
        reject(lambda:run(c))
        assert not c.renames and c.dirs[c.target]['files']==c.old
    case(name,fn)
seal_reject('publish-HOLD-missing-root-stage-receipt',lambda c:c.grant.pop('stageReceipt'))
seal_reject('publish-HOLD-wrong-root-stage-receipt-SHA',lambda c:c.grant['stageReceipt'].update(sha256='f'*64))
seal_reject('publish-HOLD-wrong-exact-stage-receipt-path',lambda c:(c.data.update({c.transaction/'other.json':c.data[c.transaction/'stage-receipt.json']}),c.grant['stageReceipt'].update(path=str(c.transaction/'other.json'))))
seal_reject('publish-HOLD-missing-root-manifest-SHA',lambda c:c.grant.pop('stageManifestSha256'))
seal_reject('publish-HOLD-malformed-root-manifest-SHA',lambda c:c.grant.update(stageManifestSha256='UPPER'))
def unapproved_map(c):c.receipt['files']={'UNAPPROVED.txt':'f'*64};c.seal()
seal_reject('publish-HOLD-unapproved-receipt-map-even-with-matching-receipt-pin',unapproved_map)
def manifest_mismatch(c):c.receipt['files']['manifest.json']='f'*64;c.seal()
seal_reject('publish-HOLD-receipt-manifest-root-SHA-mismatch',manifest_mismatch)
def wrong_stage_root(c):c.receipt['stageRoot']=str(c.transaction/'other-stage');c.seal()
seal_reject('publish-HOLD-wrong-stage-root-identity',wrong_stage_root)
def wrong_dir_id(c):c.receipt['directoryIdentity']=[1,999];c.seal()
seal_reject('publish-HOLD-wrong-stage-directory-ID',wrong_dir_id)
seal_reject('publish-HOLD-generated-source-drift-before-any-rename',lambda c:setattr(c,'drift_source',files[0]['source']['path']))
seal_reject('publish-HOLD-unacknowledged-nonatomic-pair',lambda c:c.grant.update(acknowledgeTransientOutputAbsence=False))
seal_reject('publish-HOLD-wrong-publication-mechanism',lambda c:c.grant.update(mechanism='ATOMIC_PAIR'))
seal_reject('publish-HOLD-final-publication-not-granted',lambda c:c.grant.update(allowPublication=False))
def stage_drift(c):c.dirs[c.stage]['files']['extra.txt']='f'*64
seal_reject('publish-HOLD-stage-raw-inventory-drift',stage_drift)

def success():
    c=MemContext();result=run(c)
    assert result['status']=='PUBLISHED_BYTES_MATCHED' and result['pairAtomic'] is False
    assert c.dirs[c.target]['files']==c.expected and c.dirs[c.backup]['files']==c.old
    assert len(c.old)==906 and len(c.renames)==2 and c.events==['PREPARED','OLD_RENAMED','NEW_RENAMED','COMMITTED']
    assert all(f['source']['path'] in c.pin_calls for f in files) and c.caps_checks==2
case('virtual-positive-two-renames-keeps-exact-old906-backup-and-new7-map',success)
def recovery(name,configure,quarantined):
    def fn():
        c=MemContext();configure(c)
        try:run(c)
        except VirtualFailure as error:
            notes=getattr(error,'__notes__',[])
        else:raise AssertionError('Expected simulated primary failure')
        assert c.dirs[c.target]['files']==c.old and c.dirs[c.target]['id']==(1,1) and len(c.old)==906
        assert c.backup not in c.dirs
        if quarantined:assert c.dirs[c.quarantine]['files']==c.expected
        else:assert c.dirs[c.stage]['files']==c.expected
        if c.persistent_journal_failure:assert notes and 'do not suppress rollback' in notes[0]
    case(name,fn)
recovery('virtual-second-rename-failure-restores-old906-with-new-stage-retained',lambda c:setattr(c,'fail_second_rename',True),False)
recovery('virtual-post-new-pin-failure-quarantines-new-and-restores-old906',lambda c:setattr(c,'fail_post_new',True),True)
recovery('virtual-OLD_RENAMED-persistent-journal-failure-still-restores-old906',lambda c:(setattr(c,'fail_event','OLD_RENAMED'),setattr(c,'persistent_journal_failure',True)),False)
recovery('virtual-NEW_RENAMED-persistent-journal-failure-still-quarantines-and-restores',lambda c:(setattr(c,'fail_event','NEW_RENAMED'),setattr(c,'persistent_journal_failure',True)),True)
recovery('virtual-COMMITTED-persistent-journal-failure-conservatively-restores-old906',lambda c:(setattr(c,'fail_event','COMMITTED'),setattr(c,'persistent_journal_failure',True)),True)
functions={n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
pub=functions['publish']
source_checks={
 'root-stage-receipt-SHA-and-exact-path-before-read':"pinned(grant.get('stageReceipt'),roots=(WORK,))" in pub and "receipt_path==safe(transaction/'stage-receipt.json')" in pub,
 'expected-map-from-plan-and-root-manifest':"expected={f['target']:f['source']['sha256'] for f in files}" in pub and "receipt.get('files')==expected" in pub,
 'all-selected-generated-source-pins-before-stage-or-old-mutation':pub.index("for item in files:pinned(item['source'])")<pub.index('safe(TARGET).rename'),
 'recovery-journal-exceptions-captured-not-shortcircuited':"except BaseException as error:journal_errors.append(str(error))" in pub,
 'quarantine-before-restore-and-old906-compare':pub.index('safe(TARGET).rename(safe(quarantine))')<pub.index("safe(backup).rename(safe(TARGET));compare(TARGET,baseline['files'])"),
 'primary-failure-rethrown-with-recovery-journal-note':"primary.add_note(" in pub and 'raise' in pub,
 'no-real-source-read-in-independent-probe':True,
}
assert all(source_checks.values())
assert not forbidden_real_access
assert sha(source.read_bytes())==expected_sha and sha(old_source.read_bytes())=='fb59aa3097f8284d08276cdf334b001c1d205781507b8863a2feb3fb63709a61'
assert all(sha(Path(p).read_bytes())==h for p,h in dep_pins.items())
old_receipt=A/'publication-r02-independent-probes-r01.json'
assert sha(old_receipt.read_bytes())=='04de4edd908f37a6560d14fe762f33a762c8b1c83f191a4a7cf397c2dfc9ce4f'
record={'schema':'spec-agent-publication-independent-delta-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'CODE_SYNTHETIC_METADATA_AND_IN_MEMORY_VIRTUAL_FS_ONLY','status':'CODE_AND_SYNTHETIC_PASS_ACTUAL_PUBLICATION_PENDING',
 'source':{'path':str(source),'sha256':expected_sha},'previousSource':{'path':str(old_source),'sha256':'fb59aa3097f8284d08276cdf334b001c1d205781507b8863a2feb3fb63709a61'},
 'oldHoldReceipt':{'path':str(old_receipt),'sha256':'04de4edd908f37a6560d14fe762f33a762c8b1c83f191a4a7cf397c2dfc9ce4f','unchanged':True},
 'changedFunctionsOnly':changed,'unchangedOtherFunctionCount':len(new_functions)-1,
 'tests':tests,'syntheticCases':len(tests),'staticSourceChecks':source_checks,'staticSourceCheckCount':len(source_checks),
 'oldFindingsAddressedInThisCodeAndVirtualScope':['UNPINNED_STAGE_RECEIPT_SEAL','JOURNAL_FAILURE_CAN_PREVENT_ROLLBACK'],
 'failedPreviousHarnessMetadataReadReceipt':{'path':str(A/'publication-r03-independent-harness-failure-r01.json'),'sha256':sha((A/'publication-r03-independent-harness-failure-r01.json').read_bytes())},'actualProtectedPathAccessRefusalInstalled':True,'actualProtectedPathAccessAttempts':forbidden_real_access,'actualOutputRead':False,'actualOutputExistenceMetadataRead':False,'actualOutputBodyRead':False,'actualOutputHashRead':False,'actualSourceOrCapsuleRead':False,
 'actualStageCreated':False,'actualCopyExecuted':False,'actualRenameExecuted':False,'actualBackupExecuted':False,'actualRollbackExecuted':False,
 'virtualDirectoryRenamesSimulated':True,'virtualOldOutput906MetadataOnly':True,'virtualSourceHashDictionaryOnly':True,
 'providerExecuted':False,'authorExecuted':False,'markerExecuted':False,'semanticApproval':False,'formalQualityAssessed':False,
 'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,'allHelpersAndOldHoldBytesUnchanged':True,
 'parserDependencyReceiptSha256':sha(dependency_receipt.read_bytes()),'parserNoncachePinsBeforeAfterUnchanged':True,
 'reviewer':'/root/delivery_tools/registration_pdf_qa',
 'limits':['Virtual filesystem tests do not verify real Windows rename/share/ACL/ADS/dir-ID/durability/rollback behavior.',
           'Two-renames pair remains non-atomic; output may be temporarily absent.',
           'No race-free exclusion is claimed against noncooperating processes or changes between preflight and operations.',
           'Rollback cannot overwrite a concurrently replaced target or unowned quarantine/backup; conflicts must HOLD and preserve evidence.',
           'Source population, root approval authenticity, semantic quality, actual native review, and final AI index body were outside this probe.',
           'Current files/link checks were tested with synthetic in-memory bodies only.']}
p=A/'publication-r03-independent-delta-probes-r02.json'
with p.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p.read_bytes()),'syntheticCases':len(tests),'staticSourceChecks':len(source_checks),'changedFunctions':changed},ensure_ascii=False))
