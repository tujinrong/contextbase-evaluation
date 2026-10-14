"""Document-local HTML/assets metadata only; no actual document or filesystem actor."""
import ast,copy,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
old_probe=A/'probe_publication_bound_r02_r01.py';old_raw=old_probe.read_bytes()
prelude=old_raw.decode('utf-8').split('# Source-only stage-seal inspection')[0]
prelude=prelude.replace('publication_bound_r02.py','publication_bound_r04.py').replace('fb59aa3097f8284d08276cdf334b001c1d205781507b8863a2feb3fb63709a61','fd64394ef596f20558ea8e25c06f426c12c39ed0e5bec5468c9ef77b7f4ef4b9')
anchor='def positive():'
injected='''base_plan['htmlLayout']='PER_DOCUMENT_DIRECTORY'
base_plan['documents'][0]['files'][1]['target']='html/Synthetic/01/01.html'
base_plan['documents'][0]['files'][-1]['assetForFormat']='MD'
base_plan['documents'][0]['files'].append({'kind':'ASSET','assetForFormat':'HTML','target':'html/Synthetic/01/d.png','source':descriptor(W/'delivery/generated/html-assets/d.png')})
'''
assert prelude.count(anchor)==1;prelude=prelude.replace(anchor,injected+'\n'+anchor)
prelude=prelude.replace('assert len(files)==6','assert len(files)==7')
prelude=prelude.replace("'html/Synthetic/01.html':'<img src=\"../../md/Synthetic/01/assets/d.png\">'","'html/Synthetic/01/01.html':'<img src=\"d.png\">'")
env={'__name__':'functions_only_publication_r04_layout'}
exec(compile(prelude,str(old_probe)+'-fresh-layout-r04','exec'),env)
ns=env['ns'];case=env['case'];reject=env['reject'];tests=env['tests'];base_plan=env['base_plan'];base_grant=env['base_grant'];P=env['P'];W=env['W'];SOURCE=env['SOURCE'];EXPECTED=env['EXPECTED']
def sha(raw):return hashlib.sha256(raw).hexdigest()
old=D/'publication_bound_r03.py';old_bytes=old.read_bytes();assert sha(old_bytes)=='8be4c01b30a73eade999d78a039ba46911167882140f37c028c051716fc7fa6f'
old_ast=ast.parse(old_bytes.decode('utf-8'));new_ast=ast.parse(SOURCE.read_text(encoding='utf-8'))
old_functions={n.name:ast.dump(n,include_attributes=False) for n in old_ast.body if isinstance(n,ast.FunctionDef)}
new_functions={n.name:ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,ast.FunctionDef)}
changed=[name for name in old_functions if old_functions[name]!=new_functions[name]]
assert changed==['validate']
case('r03-to-r04-only-validate-AST-changed-publish-recovery-bytecode-unchanged',lambda:None)

two_plan=copy.deepcopy(base_plan);two_grant=copy.deepcopy(base_grant);docs=[]
for ordinal,section in enumerate(('Alpha','Beta'),1):
    cp=Path(section)/'shared.md';selected=[]
    for kind,ext in (('MD','.md'),('HTML','.html'),('PDF','.pdf'),('XLSX','.xlsx')):
        target=Path(two_plan['layout'][kind])/(cp.with_suffix('')/(cp.stem+'.html') if kind=='HTML' else cp.with_suffix(ext))
        selected.append({'kind':kind,'target':target.as_posix(),'source':{'path':str(W/'delivery/generated'/kind/cp.with_suffix(ext)),'sha256':sha((section+kind).encode())}})
    for name in ('layout-001.png','diagram-001.png'):
        selected.append({'kind':'ASSET','assetForFormat':'HTML','target':(Path('html')/cp.with_suffix('')/name).as_posix(),
                         'source':{'path':str(W/'delivery/generated/native'/section/name),'sha256':sha((section+name).encode())}})
    selected.append({'kind':'ASSET','assetForFormat':'MD','target':(Path('md')/cp.with_suffix('')/'assets/diagram-001.png').as_posix(),
                     'source':{'path':str(W/'delivery/generated/native'/section/'diagram-001.png'),'sha256':sha((section+'diagram-001.png').encode())}})
    docs.append({'documentId':'TOY-'+section,'canonicalDocumentPath':cp.as_posix(),'complete':True,'reviewed':True,'generated':True,'files':selected})
two_plan['documents']=docs;two_grant['approvedDocumentIds']=[d['documentId'] for d in docs]
def two_positive():
    files,_=ns['validate'](copy.deepcopy(two_plan),copy.deepcopy(two_grant),P)
    assert len(files)==15 and len({f['target'].casefold() for f in files})==15
    for name in ('layout-001.png','diagram-001.png'):
        selected=[f for f in files if f.get('assetForFormat')=='HTML' and Path(f['target']).name==name]
        assert len(selected)==2 and len({f['source']['sha256'] for f in selected})==2
        assert {f['target'] for f in selected}=={'html/Alpha/shared/'+name,'html/Beta/shared/'+name}
    for section in ('Alpha','Beta'):
        assert {f['target'] for f in files if f['kind'] in {'MD','PDF','XLSX'} and f.get('documentId')=='TOY-'+section}=={'md/'+section+'/shared.md','PDF/'+section+'/shared.pdf','Excel/'+section+'/shared.xlsx'}
case('same-canonical-stem-two-documents-same-image-filenames-distinct-SHAs-safe-local-targets',two_positive)
def layout_negative(name,mutate):
    def fn():
        p,g=copy.deepcopy(two_plan),copy.deepcopy(two_grant);mutate(p,g);reject(lambda:ns['validate'](p,g,P))
    case(name,fn)
layout_negative('layout-HOLD-missing-per-document-directory-policy',lambda p,g:p.pop('htmlLayout'))
layout_negative('layout-HOLD-flat-policy',lambda p,g:p.update(htmlLayout='FLAT'))
layout_negative('layout-HOLD-flat-HTML-destination',lambda p,g:p['documents'][0]['files'][1].update(target='html/Alpha/shared.html'))
layout_negative('layout-HOLD-cross-document-HTML-asset',lambda p,g:p['documents'][0]['files'][4].update(target='html/Beta/shared/layout-001.png'))
layout_negative('layout-HOLD-flat-global-asset',lambda p,g:p['documents'][0]['files'][4].update(target='html/layout-001.png'))
layout_negative('layout-HOLD-renamed-native-image',lambda p,g:p['documents'][0]['files'][4].update(target='html/Alpha/shared/renamed.png'))
layout_negative('layout-HOLD-nested-HTML-assets-changes-relative-link',lambda p,g:p['documents'][0]['files'][4].update(target='html/Alpha/shared/assets/layout-001.png'))
layout_negative('layout-HOLD-MD-asset-missing-assets-directory',lambda p,g:p['documents'][0]['files'][-1].update(target='md/Alpha/shared/diagram-001.png'))
layout_negative('layout-HOLD-missing-format-association',lambda p,g:p['documents'][0]['files'][4].pop('assetForFormat'))
layout_negative('layout-HOLD-PDF-asset-format-association',lambda p,g:p['documents'][0]['files'][4].update(assetForFormat='PDF'))
layout_negative('layout-HOLD-MD-hierarchy-changed',lambda p,g:p['documents'][0]['files'][0].update(target='md/Alpha/shared/shared.md'))
layout_negative('layout-HOLD-PDF-hierarchy-changed',lambda p,g:p['documents'][0]['files'][2].update(target='PDF/Alpha/shared/shared.pdf'))
layout_negative('layout-HOLD-XLSX-hierarchy-changed',lambda p,g:p['documents'][0]['files'][3].update(target='Excel/Alpha/shared/shared.xlsx'))
layout_negative('layout-HOLD-casefold-local-asset-collision',lambda p,g:p['documents'][0]['files'].append({**copy.deepcopy(p['documents'][0]['files'][4]),'target':'HTML/ALPHA/SHARED/layout-001.png'}))

# Unmodified HTML bodies use local filenames, not rewritten URL strings.
files,_=ns['validate'](copy.deepcopy(two_plan),copy.deepcopy(two_grant),P)
stage=Path(two_plan['transactionRoot'])/'stage'
bodies={f['target']:'' for f in files if f['kind'] in {'MD','HTML','INDEX'}}
for section in ('Alpha','Beta'):
    bodies['html/'+section+'/shared/shared.html']='<html><body><img src="layout-001.png"><img src="diagram-001.png"></body></html>'
    bodies['md/'+section+'/shared.md']='![diagram](shared/assets/diagram-001.png)'
bodies['index.md']='[A](html/Alpha/shared/shared.html) [B](html/Beta/shared/shared.html)'
def new_link_positive():
    original=ns['safe']
    def reader(path):
        name=Path(path).relative_to(stage).as_posix();assert name in bodies
        return type('SyntheticReader',(),{'read_text':lambda self,**kwargs:bodies[name]})()
    ns['safe']=reader
    try:result=ns['linkcheck'](stage,files)
    finally:ns['safe']=original
    assert result['checkedLinks']==8 and not result['issues'] and result['bodyRewritten'] is False and result['networkRequested'] is False
case('same-unrewritten-local-HTML-image-links-and-MD-assets-available-in-each-document',new_link_positive)
assert sha(SOURCE.read_bytes())==EXPECTED and sha(old.read_bytes())=='8be4c01b30a73eade999d78a039ba46911167882140f37c028c051716fc7fa6f'
prior=A/'publication-r03-independent-delta-probes-r02.json';assert sha(prior.read_bytes())=='a57c1e22684eed67ca6ee472c118f0a20f9b5843c7c4f6e13a1e5887d7872229'
assert all(sha(Path(p).read_bytes())==h for p,h in env['dep_pins'].items())
record={'schema':'spec-agent-publication-layout-independent-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'CODE_PURE_METADATA_AND_IN_MEMORY_SYNTHETIC_LINK_TEXT_ONLY','status':'CODE_AND_SYNTHETIC_PASS_ACTUAL_PUBLICATION_PENDING',
 'source':{'path':str(SOURCE),'sha256':EXPECTED},'previousR03SourceSha256':'8be4c01b30a73eade999d78a039ba46911167882140f37c028c051716fc7fa6f',
 'r03IndependentVirtualReceipt':{'path':str(prior),'sha256':'a57c1e22684eed67ca6ee472c118f0a20f9b5843c7c4f6e13a1e5887d7872229','unchanged':True},
 'changedFunctionsOnly':changed,'unchangedOtherFunctionCount':len(new_functions)-1,'tests':tests,'syntheticCases':len(tests),
 'sameImageFilenameDistinctSourcePinsAcrossDocumentsAccepted':True,'flatOrCrossDocumentAssetOrRenameRejected':True,
 'MDPDFXLSXOriginalStemHierarchyPreserved':True,'linkBodiesSyntheticOnly':True,'bodyRewritePerformed':False,
 'actualOutputRead':False,'actualOutputBodyRead':False,'actualOutputHashRead':False,'actualSourceOrCapsuleRead':False,
 'actualStageCreated':False,'actualCopyExecuted':False,'actualRenameExecuted':False,'actualBackupExecuted':False,
 'producerExecuted':False,'providerExecuted':False,'nativeAuthorExecuted':False,'markerExecuted':False,
 'semanticApproval':False,'formalQualityAssessed':False,'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,
 'allSourceAndPreviousReceiptsUnchanged':True,'reviewer':'/root/delivery_tools/registration_pdf_qa',
 'limits':['No actual HTML/Markdown/image was read; link strings and source hashes are synthetic.',
           'No actual copy, checksum, filesystem path gate, Windows rename, journal, or rollback was exercised for r04.',
           'Publish/recovery function AST is unchanged from r03; prior virtual tests remain evidence for that code only, not an actual operation.',
           'This metadata/layout audit does not qualify source content, native legibility, complete production outputs, or publication.']}
p=A/'publication-r04-layout-independent-probes-r01.json'
with p.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p.read_bytes()),'syntheticCases':len(tests),'changedFunctions':changed},ensure_ascii=False))
