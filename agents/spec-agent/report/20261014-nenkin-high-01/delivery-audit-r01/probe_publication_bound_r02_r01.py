"""Independent pure metadata / virtual-file probes. No real source or output I/O."""
import ast,copy,hashlib,json,os,re,stat,sys
from datetime import datetime,timezone
from pathlib import Path,PureWindowsPath
from types import SimpleNamespace
sys.dont_write_bytecode=True
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
SOURCE=D/'publication_bound_r02.py'
EXPECTED='fb59aa3097f8284d08276cdf334b001c1d205781507b8863a2feb3fb63709a61'
def sha(raw):return hashlib.sha256(raw).hexdigest()
raw=SOURCE.read_bytes();assert sha(raw)==EXPECTED
text=raw.decode('utf-8');tree=ast.parse(text)
allowed=[]
for node in tree.body:
    if isinstance(node,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef)):allowed.append(node)
ns={'__name__':'functions_only_publication_probe','__file__':str(SOURCE)}
exec(compile(ast.Module(body=allowed,type_ignores=[]),str(SOURCE),'exec'),ns)
original_safe=ns['safe']
original_publish=ns['publish']
actual_io_attempts=[]
def metadata_safe(value):
    p=Path(value)
    assert p.is_absolute(),'synthetic descriptor must remain absolute'
    assert not any(ord(c)<32 or ord(c)==127 for c in str(p)) and all(':' not in x for x in p.parts[1:])
    return p
ns['safe']=metadata_safe
tests=[];findings=[]
def case(name,fn):
    fn();tests.append({'name':name,'pass':True})
def reject(fn):
    try:fn()
    except (ValueError,TypeError,KeyError,AssertionError,AttributeError) as exc:return type(exc).__name__,str(exc)
    raise AssertionError('Expected rejection')

W,R,T,I=(ns[k] for k in ('WORK','REPORT','TARGET','INPUT'))
P='7'*64;CAP='3'*64;FILE='1'*64
def descriptor(path):return {'path':str(path),'sha256':FILE}
layout={'MD':'md','HTML':'html','PDF':'PDF','XLSX':'Excel'}
cp='Synthetic/01.md'
selected=[]
for kind,ext in ns['EXT'].items():
    if kind=='ASSET':continue
    selected.append({'kind':kind,'target':(Path(layout[kind])/Path(cp).with_suffix(ext)).as_posix(),
                     'source':descriptor(W/'delivery/generated'/kind/Path(cp).with_suffix(ext))})
selected.append({'kind':'ASSET','target':'md/Synthetic/01/assets/d.png','source':descriptor(W/'delivery/generated/assets/d.png')})
base_plan={'schema':'spec-agent-publication-plan/1','outputRoot':str(T),'referenceMode':'source-only',
           'sourceSnapshotManifestSha256':CAP,'complete':True,'agentIdentity':'SYNTHETIC-ONLY',
           'layout':layout,'documents':[{'documentId':'TOY-001','canonicalDocumentPath':cp,'complete':True,'reviewed':True,'generated':True,'files':selected}],
           'index':{'target':'index.md','reviewed':True,'source':descriptor(W/'delivery/generated/index.md')},
           'protectedInventories':[
               {'role':'original-input','root':str(I),'count':345,'inventory':descriptor(R/'independent-audit/SYNTHETIC-input-inventory.json')},
               {'role':'source-capsule','root':str(W/'capsule/sealed'),'count':179,'sourceSnapshotManifestSha256':CAP,'inventory':descriptor(R/'independent-audit/SYNTHETIC-cap-inventory.json')},
           ],'transactionRoot':str(W/'publication/SYNTHETIC-transaction-r01')}
base_grant={'schema':'spec-agent-publication-grant/1','planSha256':P,'allowStage':True,'allowPublication':True,
            'sourceSnapshotManifestSha256':CAP,'complete':True,'sourceReviewed':True,'textCoverageReviewed':True,
            'actualNativeReviewed':True,'reviewedIndexReady':True,'approvedDocumentIds':['TOY-001'],
            'oldOutputBaselineSha256':ns['BASELINE_SHA'],'mechanism':'JOURNALED_TWO_RENAMES','acknowledgeTransientOutputAbsence':True}
def positive():
    files,tx=ns['validate'](copy.deepcopy(base_plan),copy.deepcopy(base_grant),P)
    assert len(files)==6 and tx==Path(base_plan['transactionRoot'])
case('nonempty-rootapproved-fourformats-asset-index-role345cap179-metadata',positive)
def negative(name,mutate):
    def fn():
        p,g=copy.deepcopy(base_plan),copy.deepcopy(base_grant);mutate(p,g)
        reject(lambda:ns['validate'](p,g,P))
    case(name,fn)
for key in ('schema','outputRoot','referenceMode','sourceSnapshotManifestSha256','complete','documents','layout','index','protectedInventories','transactionRoot'):
    negative('missing-plan-'+key,lambda p,g,key=key:p.pop(key))
for key in ('schema','planSha256','allowStage','sourceSnapshotManifestSha256','complete','sourceReviewed','textCoverageReviewed','actualNativeReviewed','reviewedIndexReady','approvedDocumentIds','oldOutputBaselineSha256'):
    negative('missing-grant-'+key,lambda p,g,key=key:g.pop(key))
negative('empty-documents',lambda p,g:p.update(documents=[]))
negative('unreviewed-document',lambda p,g:p['documents'][0].update(reviewed=False))
negative('unfinished-document',lambda p,g:p['documents'][0].update(complete=False))
negative('not-generated-document',lambda p,g:p['documents'][0].update(generated=False))
negative('analysis-report-document-category',lambda p,g:p['documents'][0].update(category='analysis-report'))
negative('wrong-plan-output-exact',lambda p,g:p.update(outputRoot=str(W/'output')))
negative('wrong-plan-grant-SHA',lambda p,g:g.update(planSha256='8'*64))
negative('wrong-rootapproved-ID',lambda p,g:g.update(approvedDocumentIds=['TOY-OTHER']))
negative('duplicate-rootapproved-ID',lambda p,g:g.update(approvedDocumentIds=['TOY-001','TOY-001']))
negative('empty-documentID',lambda p,g:p['documents'][0].update(documentId=''))
negative('nonstring-documentID',lambda p,g:p['documents'][0].update(documentId=1))
negative('empty-artifact-list',lambda p,g:p['documents'][0].update(files=[]))
negative('missing-PDF-format',lambda p,g:p['documents'][0].update(files=[f for f in p['documents'][0]['files'] if f['kind']!='PDF']))
negative('wrong-artifact-format',lambda p,g:p['documents'][0]['files'][0].update(kind='DOCX'))
negative('wrong-target-suffix',lambda p,g:p['documents'][0]['files'][0].update(target='md/Synthetic/01.pdf'))
negative('wrong-canonical-stem',lambda p,g:p['documents'][0]['files'][0].update(target='md/Synthetic/OTHER.md'))
negative('canonical-colon',lambda p,g:p['documents'][0].update(canonicalDocumentPath='Synthetic/x:ads.md'))
negative('target-colon',lambda p,g:p['documents'][0]['files'][0].update(target='md/Synthetic/x:ads.md'))
negative('canonical-traversal',lambda p,g:p['documents'][0].update(canonicalDocumentPath='../01.md'))
negative('canonical-Windows-device',lambda p,g:p['documents'][0].update(canonicalDocumentPath='Synthetic/CON.md'))
negative('report-MD-source',lambda p,g:p['documents'][0]['files'][0].update(source=descriptor(R/'delivered/01.md')))
negative('analysis-MD-source',lambda p,g:p['documents'][0]['files'][0].update(source=descriptor(W/'analysis/01.md')))
negative('QA-source-upper-case',lambda p,g:p['documents'][0]['files'][0].update(source=descriptor(W/'QA/01.md')))
negative('raw-answer-index-source',lambda p,g:p['index'].update(source=descriptor(W/'answers/index.md')))
negative('analysis-index-source',lambda p,g:p['index'].update(source=descriptor(W/'analysis/index.md')))
negative('REPORT-index-source',lambda p,g:p['index'].update(source=descriptor(R/'approved/index.md')))
negative('protected-cap-artifact-source',lambda p,g:p['documents'][0]['files'][0].update(source=descriptor(W/'capsule/sealed/01.md')))
negative('protected-cap-index-source',lambda p,g:p['index'].update(source=descriptor(W/'capsule/sealed/index.md')))
negative('old-OUTPUT-source',lambda p,g:p['documents'][0]['files'][0].update(source=descriptor(T/'md/01.md')))
negative('duplicate-artifact-target',lambda p,g:p['documents'][0]['files'].append(copy.deepcopy(p['documents'][0]['files'][-1])))
negative('asset-casefold-target-collision',lambda p,g:p['documents'][0]['files'].append({**copy.deepcopy(p['documents'][0]['files'][-1]),'target':'MD/SYNTHETIC/01/ASSETS/D.PNG'}))
negative('artifact-source-SHA-missing',lambda p,g:p['documents'][0]['files'][0]['source'].pop('sha256'))
negative('artifact-source-SHA-uppercase',lambda p,g:p['documents'][0]['files'][0]['source'].update(sha256='A'*64))
negative('artifact-source-SHA-short',lambda p,g:p['documents'][0]['files'][0]['source'].update(sha256='1'*63))
negative('artifact-source-extra-field',lambda p,g:p['documents'][0]['files'][0]['source'].update(unapproved=True))
negative('index-source-SHA-missing',lambda p,g:p['index']['source'].pop('sha256'))
negative('wrong-protected-roles',lambda p,g:p['protectedInventories'][1].update(role='other'))
negative('wrong-original-input-count',lambda p,g:p['protectedInventories'][0].update(count=344))
negative('wrong-cap-count',lambda p,g:p['protectedInventories'][1].update(count=178))
negative('wrong-original-input-root',lambda p,g:p['protectedInventories'][0].update(root=str(W/'input')))
negative('outside-cap-root',lambda p,g:p['protectedInventories'][1].update(root=str(R/'capsule')))
negative('wrong-cap-SHA-binding',lambda p,g:p['protectedInventories'][1].update(sourceSnapshotManifestSha256='4'*64))
negative('protected-inventory-SHA-missing',lambda p,g:p['protectedInventories'][0]['inventory'].pop('sha256'))
negative('transaction-not-publication',lambda p,g:p.update(transactionRoot=str(W/'other/transaction')))
negative('transaction-outside-owned',lambda p,g:p.update(transactionRoot=str(T/'transaction')))
negative('transaction-protected-overlap',lambda p,g:p['protectedInventories'][1].update(root=str(W/'publication')))
negative('old906-baseline-grant-mismatch',lambda p,g:g.update(oldOutputBaselineSha256='9'*64))
for value in ('../x.md','/x.md','C:/x.md','a\\b.md','a//b.md','a/./b.md','a:stream.md','a\x00.md','a/file.','a/file ','a/NUL.txt'):
    case('relative-reject-'+repr(value),lambda value=value:reject(lambda:ns['relative'](value)))
case('unique-JSON-duplicate-reject',lambda:reject(lambda:ns['unique_json'](b'{"x":1,"x":2}')))
case('unique-JSON-NaN-reject',lambda:reject(lambda:ns['unique_json'](b'{"x":NaN}')))

# The real safe() function runs against a public-path-shaped virtual filesystem.
# lstat/resolve are mocked; no actual target or input path is inspected.
class FakePath(PureWindowsPath):
    reparse=set();symlink=set();redirected=set()
    def lstat(self):
        return SimpleNamespace(st_mode=stat.S_IFLNK if str(self) in self.symlink else stat.S_IFDIR,
                               st_file_attributes=0x400 if str(self) in self.reparse else 0)
    def resolve(self,strict=False):
        return FakePath(r'D:\SYNTHETIC\redirected') if str(self) in self.redirected else self
safe_ns={'Path':FakePath,'require':ns['require'],'stat':stat}
exec(compile(ast.Module(body=[next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='safe')],type_ignores=[]),str(SOURCE),'exec'),safe_ns)
virtual=FakePath(r'D:\SYNTHETIC\owned\file.md')
case('safe-public-path-normal-positive',lambda:assert_path(safe_ns['safe'](virtual),virtual)) if False else None
def safe_positive():assert safe_ns['safe'](virtual)==virtual
case('safe-public-path-normal-positive',safe_positive)
for kind,which in (('reparse','child'),('reparse','ancestor'),('symlink','child'),('symlink','ancestor'),('redirected','child')):
    def run(kind=kind,which=which):
        target=virtual if which=='child' else virtual.parent
        getattr(FakePath,kind).add(str(target))
        try:reject(lambda:safe_ns['safe'](virtual))
        finally:getattr(FakePath,kind).clear()
    case('safe-reject-'+kind+'-'+which,run)

# Link parsing uses synthetic code-string documents in a virtual reader.
# Imported parser code is the already approved pinned analysis dependencies only.
dependency_receipt=R/'delivery-audit-r01/analysis-dependencies-r01.json'
dep_record=json.loads(dependency_receipt.read_text(encoding='utf-8'))
DEP=Path(dep_record['pythonPath']);dep_pins={p:h for value in dep_record['modules'].values() for p,h in value['nonCacheFiles'].items()}
assert all(sha(Path(p).read_bytes())==h for p,h in dep_pins.items())
assert str(DEP) not in sys.path
sys.path.insert(0,str(DEP))
files,_=ns['validate'](copy.deepcopy(base_plan),copy.deepcopy(base_grant),P)
stage=Path(base_plan['transactionRoot'])/'stage'
virtual_bodies={f['target']:'' for f in files if f['kind'] in {'MD','INDEX','HTML'}}
def virtual_reader(path):
    relative=Path(path).relative_to(stage).as_posix()
    assert relative in virtual_bodies
    return SimpleNamespace(read_text=lambda **kwargs:virtual_bodies[relative])
def link_case(name,bodies,expect_issues):
    def fn():
        virtual_bodies.update({p:'' for p in virtual_bodies});virtual_bodies.update(bodies)
        old_safe=ns['safe'];ns['safe']=virtual_reader
        try:result=ns['linkcheck'](stage,files)
        finally:ns['safe']=old_safe
        assert bool(result['issues'])==expect_issues,result
        assert result['bodyRewritten'] is False and result['networkRequested'] is False
    case(name,fn)
link_case('explicit-complete-index-MD-HTML-asset-links-good',{
    'index.md':'[MD](md/Synthetic/01.md) [PDF](PDF/Synthetic/01.pdf)',
    'md/Synthetic/01.md':'[PDF](../../PDF/Synthetic/01.pdf) ![image](01/assets/d.png)',
    'html/Synthetic/01.html':'<img src="../../md/Synthetic/01/assets/d.png">',
},False)
link_case('link-HOLD-excluded-report',{'index.md':'[bad](report/unselected.md)'},True)
link_case('link-HOLD-unselected-local-asset',{'md/Synthetic/01.md':'![bad](01/assets/unselected.png)'},True)
link_case('link-HOLD-traversal-out-of-explicit-bundle',{'index.md':'[bad](../escape.md)'},True)
link_case('link-HOLD-percentencoded-excluded-input',{'index.md':'[bad](%2E%2E/input/source.md)'},True)
link_case('link-HOLD-protocolrelative',{'index.md':'[bad](//invalid.example/file.md)'},True)
link_case('link-HOLD-file-protocol',{'index.md':'<a href="file:///C:/outside.md">bad</a>'},True)
link_case('link-HOLD-fragment-no-anchor-proof',{'index.md':'[bad](md/Synthetic/01.md#missing)'},True)
link_case('link-HOLD-inlineHTML-excluded-link',{'md/Synthetic/01.md':'<a href="../../analysis/report.md">bad</a>'},True)
link_case('link-HTTPS-source-reference-no-network-request',{'index.md':'[reference](https://invalid.example/reference)'},False)

# Source-only stage-seal inspection uses virtual bytes, and stops before baseline
# or transaction mutation. These are NOT real copy/rename/backup tests.
class ProbeStop(Exception):pass
class MemoryPath(PureWindowsPath):
    data={}
    def read_bytes(self):return self.data[str(self)]
    def rename(self,*args):actual_io_attempts.append('rename');raise AssertionError('No rename permitted')
receipt_path=MemoryPath(base_plan['transactionRoot'])/'stage-receipt.json'
unapproved={'UNAPPROVED.txt':'f'*64}
MemoryPath.data[str(receipt_path)]=json.dumps({'planSha256':P,'status':'STAGED_BYTES_VERIFIED_NOT_PUBLISHED',
                                              'stageRoot':str(stage),'directoryIdentity':[5,6],'files':unapproved}).encode()
observed_compare=[]
publish_ns=dict(ns)
publish_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='publish')
exec(compile(ast.Module(body=[publish_node],type_ignores=[]),str(SOURCE),'exec'),publish_ns)
publish_ns.update(validate=lambda p,g,h:(files,MemoryPath(base_plan['transactionRoot'])),safe=lambda p:MemoryPath(p),
                  identity=lambda p:(5,6),compare=lambda p,x:observed_compare.append((str(p),x)),
                  load_baseline=lambda:(_ for _ in ()).throw(ProbeStop('Stopped before actual baseline or mutation')))
def unsealed_stage():
    try:publish_ns['publish'](copy.deepcopy(base_plan),copy.deepcopy(base_grant),P)
    except ProbeStop:pass
    else:raise AssertionError('Expected stop-before-mutation')
    assert observed_compare==[(str(stage),unapproved)] and not actual_io_attempts
    findings.append({'id':'UNPINNED_STAGE_RECEIPT_SEAL','severity':'HOLD_BEFORE_PUBLICATION',
                     'sourceLines':[212,214],'observedBy':'functions-only virtual reader and stop-before-baseline/mutation',
                     'actual':'A stage receipt with the valid planSHA/status/dirID but an unapproved files map is used as comparison authority before any binding to plan file pins.',
                     'fixtureUnapprovedTarget':'UNAPPROVED.txt','actualStageCreated':False,'actualRenameExecuted':False})
case('observe-unsealed-stage-receipt-acceptance-before-mutation',unsealed_stage)

functions={n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
pub=functions['publish'];stager=functions['stage_bundle']
static={
    'root-stage-and-final-review-gates':all(k in functions['validate'] for k in ('sourceReviewed','textCoverageReviewed','actualNativeReviewed','reviewedIndexReady')),
    'dynamic-approved-exact-document-set':"ids==set(approved)" in functions['validate'],
    'descriptor-shape64-and-protected-source-rejection':"descriptor_shape(item['source'])" in functions['validate'] and 'source.is_relative_to(root) for root in protected_roots' in functions['validate'],
    'all-ancestor-lstat-reparse-and-symlink':"(p,*p.parents)" in functions['safe'] and '0x400' in functions['safe'] and 'S_ISLNK' in functions['safe'],
    'staging-fresh-copy-and-source-before-after-hash':"source=pinned(item['source'])" in stager and 'shutil.copyfile' in stager and "hashfile(destination)==item['source']['sha256'] and hashfile(source)==item['source']['sha256']" in stager,
    'stage-link-HOLD-no-body-rewrite':"require(not links['issues']" in stager and "'bodyRewritten':False" in functions['linkcheck'],
    'protected-and-old-output-rechecks-before-stage-completion':"protected_checks(plan);compare(TARGET,baseline['files'])" in stager,
    'samevolume-transaction-required':"transaction.drive==TARGET.drive" in functions['validate'],
    'non-atomic-pair-grant-required':'JOURNALED_TWO_RENAMES' in pub and 'acknowledgeTransientOutputAbsence' in pub,
    'durable-journal-public-fsync':'os.fsync(h.fileno())' in pub,
    'directory-ID-before-and-after-both-renames':'identity(TARGET)==old_id' in pub and 'identity(backup)==old_id' in pub and 'identity(TARGET)==new_id' in pub,
    'owned-new-quarantine-and-old906-restore':'identity(TARGET)==new_id and not quarantine.exists()' in pub and "safe(backup).rename(safe(TARGET));compare(TARGET,baseline['files'])" in pub,
    'no-delete-no-body-rewrite':'rmtree' not in text and '.unlink(' not in text and "'businessBodyRewritten':False" in pub,
    'metadata-only-main-default':"default='validate-metadata'" in functions['main'],
}
assert all(static.values()),static
findings.append({'id':'JOURNAL_FAILURE_CAN_PREVENT_ROLLBACK','severity':'HOLD_FOR_AUTOMATIC_ROLLBACK_CONTRACT',
                 'sourceLines':[226,230,231,237],'observedBy':'AST/source-only (not actual or virtual rename execution)',
                 'actual':'except first calls event(FAILED); if journal append/fsync raises again, quarantine/old restoration is skipped.',
                 'actualFailureTestExecuted':False})
assert not actual_io_attempts
assert sha(SOURCE.read_bytes())==EXPECTED
assert all(sha(Path(p).read_bytes())==h for p,h in dep_pins.items())
old_path=D/'publication_bound_r01.py';assert sha(old_path.read_bytes())=='733500a862da4bd3c0e4de40b5f9bed632f5729114d23e486720a227f029549d'
record={'schema':'spec-agent-publication-independent-functions-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'scope':'CODE_SYNTHETIC_METADATA_AND_VIRTUAL_READERS_ONLY','status':'HOLD_STAGE_SEAL_AND_JOURNAL_ROLLBACK',
        'source':{'path':str(SOURCE),'sha256':EXPECTED},'oldR01Sha256':'733500a862da4bd3c0e4de40b5f9bed632f5729114d23e486720a227f029549d',
        'allSourceHelperBytesUnchanged':True,'tests':tests,'syntheticCases':len(tests),'staticSourceChecks':static,
        'staticSourceCheckCount':len(static),'findings':findings,
        'parserDependencyReceipt':str(dependency_receipt),'parserDependencyReceiptSha256':sha(dependency_receipt.read_bytes()),
        'parserNoncachePinsBeforeAfterUnchanged':True,'parserPinCount':len(dep_pins),
        'stageBundleInvoked':False,'publishInvokedWithVirtualReaderOnlyStoppedBeforeBaseline':True,
        'actualOutputRead':False,'actualOutputBodyRead':False,'actualOutputHashRead':False,
        'actualSourceOrCapsuleRead':False,'actualStageCreated':False,'actualCopyExecuted':False,
        'actualRenameExecuted':False,'actualBackupExecuted':False,'actualRollbackExecuted':False,
        'providerExecuted':False,'authorExecuted':False,'markerExecuted':False,'semanticApproval':False,
        'formalQualityAssessed':False,'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,
        'reviewer':'/root/delivery_tools/registration_pdf_qa',
        'limits':['Root grant authenticity/source quality/completeness of final capability population was not inferred.',
                  'Filesystem path checks were probed through virtual public-path-shaped objects, not actual target paths.',
                  'All link bodies were synthetic in-memory code strings; no authored candidate index/body was read or rewritten.',
                  'No real same-volume rename, rollback, directory identity, copy, timeout, or Windows sharing behavior was exercised.',
                  'Two-renames pair remains non-atomic and preflight does not claim race-free filesystem exclusion.',
                  'Link parser coverage here is Markdown links/images and raw HTML href/src; source semantics and other CSS/resource URL syntax are outside this check.']}
p=A/'publication-r02-independent-probes-r01.json'
with p.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p.read_bytes()),'syntheticCases':len(tests),'staticSourceChecks':len(static),'findings':[x['id'] for x in findings]},ensure_ascii=False))
