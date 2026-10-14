"""Pure schema fixtures only; never import/execute producers or read actual documents."""
import ast,copy,hashlib,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
W=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
R=A.parent;SOURCE=W/'delivery/build_delivery_binding_r02.py'
EXPECTED='866269fd244073bae610eed8fd0683e2d5b1cd4073f9fcbeb8f8f3928d039c5b'
def sha(raw):return hashlib.sha256(raw).hexdigest()
raw=SOURCE.read_bytes();assert sha(raw)==EXPECTED;text=raw.decode('utf-8');tree=ast.parse(text)
def require(ok,message):
    if not ok:raise ValueError('HOLD: '+message)
def safe(value):
    p=Path(value);require(p.is_absolute(),'synthetic absolute path');return p
def relative(value):
    require(isinstance(value,str) and value and '\\' not in value and ':' not in value and not value.startswith('/'),'canonical relative')
    require(all(x not in {'','.','..'} for x in value.split('/')),'relative traversal')
    return Path(value)
ns={'WORK':W,'REPORT':R,'Path':Path,'safe':safe,'relative':relative,'require':require}
for n in tree.body:
    if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in {'COLLECTOR','COLLECTOR_SHA','RENDERER','RENDERER_SHA'} for t in n.targets):exec(compile(ast.Module(body=[n],type_ignores=[]),str(SOURCE),'exec'),ns)
def descriptor_shape(record):
    require(isinstance(record,dict) and set(record)=={'path','sha256'},'exact descriptor')
    require(isinstance(record['path'],str) and isinstance(record['sha256'],str) and re.fullmatch('[0-9a-f]{64}',record['sha256']) is not None,'strict descriptor pin')
    return safe(record['path'])
ns.update(re=re,descriptor_shape=descriptor_shape)
for name in ('digest','approved_ids'):
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),'exec'),ns)

model_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='metadata_model')
exec(compile(ast.Module(body=[model_node],type_ignores=[]),str(SOURCE),'exec'),ns)
producer_pins={str(ns['COLLECTOR']):ns['COLLECTOR_SHA'],str(ns['RENDERER']):ns['RENDERER_SHA']}
assert all(sha(Path(p).read_bytes())==h for p,h in producer_pins.items())
CAP='1'*64;COLLECTION='2'*64;SEL='3'*64;MD='4'*64;PINS='5'*64;MANIFEST='6'*64;HTML='a'*64
root=W/'collections/SYNTHETIC';renderroot=W/'renders/SYNTHETIC';docpath='Synthetic/01.md'
doc={'documentId':'TOY-001','kind':'synthetic-specification','path':docpath,'sha256':MD,
     'canonicalMarkdown':str(root/docpath),'sourcePinSha256':'7'*64,'independentReviewSha256':'8'*64,
     'independentReviewApproved':True,'structureStatus':'STRUCTURE_VALID','reportOnly':False}
other={**doc,'documentId':'TOY-REPORT','kind':'analysis-report','path':'analysis-report.md','canonicalMarkdown':str(root/'analysis-report.md'),'reportOnly':True}
collection={'schema':'spec-agent-text-reviewed-collection/1','status':'TEXT_REVIEWED_CANDIDATE_DISPLAY_AND_QUALIFICATION_PENDING',
            'inputBeforeAfterUnchanged':True,'bodyTransformationPerformed':False,'semanticProseAssembledByPython':False,
            'outputRoot':str(root),'capsule':{'mode':'source-only','manifestSha256':CAP},'documents':[doc,other],
            'documentCount':2,'specificationCount':1,'reportOnlyCount':1,'completePlan':True,
            'runtimeProvenance':{'runtimeFiles':{'contextbase/ai/rendering.py':'b'*64}}}
selection={'schema':'spec-agent-delivery-binding-selection/1','_selectionSha256':SEL,
           'collection':{'path':str(R/'independent-audit/SYNTHETIC-collection.json'),'sha256':COLLECTION},
           'permittedRenderRoot':str(renderroot),'documents':[{'documentId':'TOY-001','renderDirectory':str(renderroot/'TOY-001'),'renderPinsSha256':PINS,'renderManifestSha256':MANIFEST}]}
grant={'schema':'spec-agent-delivery-binding-grant/1','allowBinding':True,'selectionSha256':SEL,'collectionSha256':COLLECTION,
       'sourceSnapshotManifestSha256':CAP,'approvedDocumentIds':['TOY-001']}
checks={'sourceSha256':MD,'originalModified':False,'structure':{'status':'PASS','findings':[]},
        'display':{'status':'PASS','blockedRequests':[],'errors':[]},'safety':{'removed':[],'inputJavaScriptEnabled':False}}
pins={**copy.deepcopy(checks),'schema':'spec-agent-render-pins/1','documentId':'TOY-001','canonicalDocumentPath':docpath,
      'collectorDocument':copy.deepcopy(doc),'collectionSha256':COLLECTION,'source':str(root/docpath),
      'helper':str(ns['RENDERER']),'helperSha256':ns['RENDERER_SHA'],'sourceSnapshotManifestSha256':CAP,'referenceMode':'source-only',
      'renderManifestSha256':MANIFEST,'canonicalHtmlFilename':'01.html','canonicalHtmlSha256':HTML,
      'renderer':str(W/'SYNTHETIC-runtime/contextbase/ai/rendering.py'),'rendererSha256':'b'*64}
manifest={**copy.deepcopy(checks),'canonicalHtmlCopyIsByteIdentical':True,'canonicalHtmlFilename':'01.html',
          'artifacts':[{'path':'document.html','sha256':HTML,'bytes':1},{'path':'01.html','sha256':HTML,'bytes':1},{'path':'layout-001.png','sha256':'c'*64,'bytes':1}]}
doc.update(draftResultSha256='d'*64,analysisHandoffSha256='e'*64)
pins['collectorDocument']=copy.deepcopy(doc)
runtime_root=W/'runtime-code/SYNTHETIC'
collection['runtimeProvenance']={'receiptSha256':'9'*64,'runtimeRoot':str(runtime_root),'runtimeFileCount':2,'runtimeFiles':{'contextbase/ai/rendering.py':'b'*64,'synthetic/__init__.py':'c'*64},'loadedImports':{},'criticalModules':{}}
grant.update(runtimeReceiptSha256='9'*64,permittedRuntimeRoot=str(runtime_root))
pins.update(collection=selection['collection']['path'],renderer=str(runtime_root/'contextbase/ai/rendering.py'),originalRendererManifestSha256='f'*64)
manifest['originalRendererManifestSha256']='f'*64

records=[{'pins':pins,'manifest':manifest}];tests=[];findings=[]
def inputs():return tuple(copy.deepcopy(x) for x in (selection,collection,grant,records))
def case(name,fn):fn();tests.append({'name':name,'pass':True})
def reject(fn):
    try:fn()
    except (ValueError,TypeError,KeyError,AttributeError):return
    raise AssertionError('Expected pure metadata rejection')
def positive():
    result=ns['metadata_model'](*inputs())
    assert len(result['documents'])==1 and result['documents'][0]['documentId']=='TOY-001'
    assert result['sourceSnapshotManifestSha256']==CAP and result['referenceMode']=='source-only'
    assert result['bindingApprovalScope']=='METADATA_CONNECTION_ONLY' and result['published'] is False
    assert result['documents'][0]['visualApproval']=='NOT_GRANTED_BY_BINDING' and result['documents'][0]['formalPercentage'] is None
case('dynamic-sourcecap-approved-subset-excludes-unselected-report-and-no-native-approval',positive)
def negative(name,mutate):
    def fn():
        s,c,g,r=inputs();mutate(s,c,g,r);reject(lambda:ns['metadata_model'](s,c,g,r))
    case(name,fn)
negative('wrong-selection-schema',lambda s,c,g,r:s.update(schema='wrong'))
negative('missing-root-grant',lambda s,c,g,r:g.update(allowBinding=False))
negative('wrong-selection-SHA-grant',lambda s,c,g,r:g.update(selectionSha256='f'*64))
negative('wrong-collection-schema',lambda s,c,g,r:c.update(schema='wrong'))
negative('collection-transformed',lambda s,c,g,r:c.update(bodyTransformationPerformed=True))
negative('semantic-Python-assembly',lambda s,c,g,r:c.update(semanticProseAssembledByPython=True))
negative('source-input-not-unchanged',lambda s,c,g,r:c.update(inputBeforeAfterUnchanged=False))
negative('wrong-capsule-mode',lambda s,c,g,r:c['capsule'].update(mode='reference-assisted'))
negative('wrong-capsule-grant-SHA',lambda s,c,g,r:g.update(sourceSnapshotManifestSha256='f'*64))
negative('wrong-collection-grant-SHA',lambda s,c,g,r:g.update(collectionSha256='f'*64))
negative('collection-root-outside-owned-namespace',lambda s,c,g,r:c.update(outputRoot=str(W/'outside')))
negative('render-root-outside-owned-namespace',lambda s,c,g,r:s.update(permittedRenderRoot=str(W/'outside')))
negative('empty-selected-documents',lambda s,c,g,r:s.update(documents=[]))
negative('missing-selected-ID',lambda s,c,g,r:s['documents'][0].pop('documentId'))
negative('nonstring-selected-ID',lambda s,c,g,r:s['documents'][0].update(documentId=1))
negative('duplicate-selected-ID',lambda s,c,g,r:s['documents'].append(copy.deepcopy(s['documents'][0])))
negative('duplicate-collected-ID',lambda s,c,g,r:c['documents'].append(copy.deepcopy(c['documents'][0])))
negative('wrong-root-approved-set',lambda s,c,g,r:g.update(approvedDocumentIds=['OTHER']))
negative('wrong-selected-record-count',lambda s,c,g,r:r.clear())
negative('report-only-selected',lambda s,c,g,r:c['documents'][0].update(reportOnly=True))
negative('analysis-report-selected-kind',lambda s,c,g,r:c['documents'][0].update(kind='analysis-report'))
negative('review-not-approved',lambda s,c,g,r:c['documents'][0].update(independentReviewApproved=False))
negative('structure-not-valid',lambda s,c,g,r:c['documents'][0].update(structureStatus='INVALID'))
negative('canonical-path-colon',lambda s,c,g,r:c['documents'][0].update(path='Synthetic/x:ads.md'))
negative('canonical-MD-root-path-mismatch',lambda s,c,g,r:c['documents'][0].update(canonicalMarkdown=str(root/'OTHER.md')))
negative('render-directory-outside-explicit-root',lambda s,c,g,r:s['documents'][0].update(renderDirectory=str(W/'renders/OTHER')))
negative('wrong-renderpins-schema',lambda s,c,g,r:r[0]['pins'].update(schema='wrong'))
negative('wrong-renderpins-doc-ID',lambda s,c,g,r:r[0]['pins'].update(documentId='OTHER'))
negative('wrong-renderpins-canonical-path',lambda s,c,g,r:r[0]['pins'].update(canonicalDocumentPath='OTHER.md'))
negative('wrong-collector-document-exact-object',lambda s,c,g,r:r[0]['pins']['collectorDocument'].update(extra='changed'))
negative('wrong-render-source-doc-path',lambda s,c,g,r:r[0]['pins'].update(source=str(root/'OTHER.md')))
negative('wrong-render-helper-path',lambda s,c,g,r:r[0]['pins'].update(helper=str(W/'OTHER.py')))
negative('wrong-render-helper-SHA',lambda s,c,g,r:r[0]['pins'].update(helperSha256='f'*64))
negative('wrong-render-sourcecap-SHA',lambda s,c,g,r:r[0]['pins'].update(sourceSnapshotManifestSha256='f'*64))
negative('wrong-render-reference-mode',lambda s,c,g,r:r[0]['pins'].update(referenceMode='reference-assisted'))
negative('wrong-enriched-manifest-SHA',lambda s,c,g,r:r[0]['pins'].update(renderManifestSha256='f'*64))
negative('canonical-copy-not-identical',lambda s,c,g,r:r[0]['manifest'].update(canonicalHtmlCopyIsByteIdentical=False))
negative('wrong-canonical-HTML-stem',lambda s,c,g,r:r[0]['pins'].update(canonicalHtmlFilename='OTHER.html'))
for kind in ('pins','manifest'):
    negative(kind+'-source-SHA-drift',lambda s,c,g,r,kind=kind:r[0][kind].update(sourceSha256='f'*64))
    negative(kind+'-source-original-modified',lambda s,c,g,r,kind=kind:r[0][kind].update(originalModified=True))
    negative(kind+'-structure-HOLD',lambda s,c,g,r,kind=kind:r[0][kind]['structure'].update(status='HOLD'))
    negative(kind+'-structure-findings',lambda s,c,g,r,kind=kind:r[0][kind]['structure'].update(findings=['synthetic']))
    negative(kind+'-display-HOLD',lambda s,c,g,r,kind=kind:r[0][kind]['display'].update(status='HOLD'))
    negative(kind+'-display-network',lambda s,c,g,r,kind=kind:r[0][kind]['display'].update(blockedRequests=['synthetic']))
    negative(kind+'-display-errors',lambda s,c,g,r,kind=kind:r[0][kind]['display'].update(errors=['synthetic']))
    negative(kind+'-safety-removed',lambda s,c,g,r,kind=kind:r[0][kind]['safety'].update(removed=['synthetic']))
    negative(kind+'-input-JS-active',lambda s,c,g,r,kind=kind:r[0][kind]['safety'].update(inputJavaScriptEnabled=True))

def accepted_gap(name,mutate,finding):
    def fn():
        s,c,g,r=inputs();mutate(s,c,g,r);reject(lambda:ns['metadata_model'](s,c,g,r))
    case('observe-'+name,fn)
def malformed_cap(s,c,g,r):c['capsule']['manifestSha256']='not-a-sha';g['sourceSnapshotManifestSha256']='not-a-sha';r[0]['pins']['sourceSnapshotManifestSha256']='not-a-sha'
accepted_gap('MALFORMED_DYNAMIC_SOURCECAP_SHA_ACCEPTED',malformed_cap,'Dynamic sourcecap equality is checked, but the shared value is not constrained to a SHA256 string.')
accepted_gap('DUPLICATE_ROOTAPPROVED_IDS_ACCEPTED',lambda s,c,g,r:g.update(approvedDocumentIds=['TOY-001','TOY-001']),'Root approved IDs are compared as sets; duplicates in the grant disappear.')
accepted_gap('RENDERER_MODULE_PIN_NOT_BOUND',lambda s,c,g,r:r[0]['pins'].update(renderer=str(W/'OTHER.py'),rendererSha256='f'*64),'Renderer helper is pinned, but actual module path/hash fields are not connected to runtime provenance by this pure bridge.')
accepted_gap('MALFORMED_SELECTED_RENDERPINS_SHA_ACCEPTED',lambda s,c,g,r:s['documents'][0].update(renderPinsSha256='not-a-sha'),'Selected renderPins SHA is carried to binding without a pure format check; build pinned() later rejects it.')

negative('missing-runtime-root-grant',lambda s,c,g,r:g.pop('permittedRuntimeRoot'))
negative('missing-runtime-receipt-grant',lambda s,c,g,r:g.pop('runtimeReceiptSha256'))
negative('runtime-receipt-SHA-mismatch',lambda s,c,g,r:g.update(runtimeReceiptSha256='f'*64))
negative('runtime-root-grant-mismatch',lambda s,c,g,r:g.update(permittedRuntimeRoot=str(W/'runtime-code/OTHER')))
negative('runtime-root-outside-namespace',lambda s,c,g,r:(c['runtimeProvenance'].update(runtimeRoot=str(W/'OTHER')),g.update(permittedRuntimeRoot=str(W/'OTHER'))))
negative('runtime-count-not-complete',lambda s,c,g,r:c['runtimeProvenance'].update(runtimeFileCount=1))
negative('runtime-count-bool',lambda s,c,g,r:c['runtimeProvenance'].update(runtimeFileCount=True))
negative('runtime-file-SHA-not64hex',lambda s,c,g,r:c['runtimeProvenance']['runtimeFiles'].update({'contextbase/ai/rendering.py':'BAD'}))
negative('runtime-file-traversal',lambda s,c,g,r:c['runtimeProvenance'].update(runtimeFiles={'../rendering.py':'b'*64},runtimeFileCount=1))
negative('renderer-exact-path-mismatch',lambda s,c,g,r:r[0]['pins'].update(renderer=str(runtime_root/'OTHER.py')))
negative('renderer-exact-SHA-mismatch',lambda s,c,g,r:r[0]['pins'].update(rendererSha256='0'*64))
negative('collection-evidence-outside-REPORT',lambda s,c,g,r:s['collection'].update(path=str(W/'collection.json')))
negative('render-directory-equals-root',lambda s,c,g,r:s['documents'][0].update(renderDirectory=str(renderroot)))
negative('collection-evidence-pins-path-mismatch',lambda s,c,g,r:r[0]['pins'].update(collection=str(R/'OTHER.json')))
negative('missing-original-manifest-SHA',lambda s,c,g,r:r[0]['pins'].pop('originalRendererManifestSha256'))
negative('original-manifest-SHA-mismatch',lambda s,c,g,r:r[0]['manifest'].update(originalRendererManifestSha256='0'*64))
negative('missing-canonical-HTML-SHA',lambda s,c,g,r:r[0]['pins'].pop('canonicalHtmlSha256'))
negative('empty-native-artifact-metadata',lambda s,c,g,r:r[0]['manifest'].update(artifacts=[]))
negative('missing-canonical-HTML-artifact',lambda s,c,g,r:r[0]['manifest'].update(artifacts=[x for x in r[0]['manifest']['artifacts'] if x['path']!='01.html']))
negative('canonical-artifact-SHA-not-equal',lambda s,c,g,r:r[0]['manifest']['artifacts'][1].update(sha256='0'*64))
negative('artifact-SHA-malformed',lambda s,c,g,r:r[0]['manifest']['artifacts'][2].update(sha256='BAD'))
negative('artifact-nested-path-rejected',lambda s,c,g,r:r[0]['manifest']['artifacts'][2].update(path='nested/layout-001.png'))
negative('artifact-casefold-duplicate',lambda s,c,g,r:r[0]['manifest']['artifacts'].append({'path':'LAYOUT-001.PNG','sha256':'c'*64}))
for field in ('sha256','sourcePinSha256','draftResultSha256','independentReviewSha256','analysisHandoffSha256'):
    negative('selected-doc-pin-malformed-'+field,lambda s,c,g,r,field=field:c['documents'][0].update({field:'BAD'}))
def duplicated_renderdir(s,c,g,r):
    d=copy.deepcopy(c['documents'][0]);d.update(documentId='TOY-002',path='Synthetic/02.md',canonicalMarkdown=str(root/'Synthetic/02.md'))
    c['documents'].append(d);g['approvedDocumentIds'].append('TOY-002')
    row=copy.deepcopy(s['documents'][0]);row['documentId']='TOY-002';s['documents'].append(row)
    new=copy.deepcopy(r[0]);new['pins'].update(documentId='TOY-002',canonicalDocumentPath=d['path'],collectorDocument=d,source=d['canonicalMarkdown'],canonicalHtmlFilename='02.html')
    new['manifest']['canonicalHtmlFilename']='02.html';new['manifest']['artifacts'][1]['path']='02.html';r.append(new)
negative('duplicate-render-directory-across-two-valid-IDs',duplicated_renderdir)
def dynamic_capsule_positive():
    s,c,g,r=inputs();value='0'*64
    c['capsule']['manifestSha256']=value;g['sourceSnapshotManifestSha256']=value;r[0]['pins']['sourceSnapshotManifestSha256']=value
    result=ns['metadata_model'](s,c,g,r);assert result['sourceSnapshotManifestSha256']==value
case('dynamic-sourcecap-second-valid-value-no-hardcoded-corpus',dynamic_capsule_positive)

functions={n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
build=functions['build']
source_checks={
 'producer-code-only-pins-no-producer-import':'hashfile(COLLECTOR)==COLLECTOR_SHA and hashfile(RENDERER)==RENDERER_SHA' in build and 'import collect_reviewed' not in text and 'import render_reviewed' not in text,
 'selection-grant-collection-pinned-before-read':'selection_file=pinned(' in build and "collection_file=pinned(selection['collection'])" in build,
 'render-pins-and-manifest-descriptor-pinned-before-read':"directory/'render-pins.json'" in build and "directory/'manifest.json'" in build,
 'actual-artifacts-loop-single-filename-and-pin-before-binding':"relative(name).name==name and name not in seen" in build and "hashfile(path)==artifact['sha256']" in build,
 'canonical-HTML-hash-and-byte-equality-before-binding':"hashfile(canonical)==pins['canonicalHtmlSha256']" in build and "canonical.read_bytes()==safe(directory/'document.html').read_bytes()" in build,
 'all-inputs-repin-before-and-after-binding':"input changed before binding write" in build and "input changed after binding write" in build,
 'fresh-no-input-overwrite-binding-receipt':"output!=receipt_path" in build and "output overwrites pinned input" in build,
 'visual-and-formal-not-granted-by-metadata':"'visualApproval':'NOT_GRANTED_BY_BINDING'" in functions['metadata_model'] and "'formalPercentage':None" in functions['metadata_model'],
}
assert all(source_checks.values())
assert sha(SOURCE.read_bytes())==EXPECTED and all(sha(Path(p).read_bytes())==h for p,h in producer_pins.items())
record={'schema':'spec-agent-binding-independent-metadata-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'CODE_SCHEMA_AND_PURE_SYNTHETIC_JSON_METADATA_ONLY','status':'CODE_AND_PURE_METADATA_PASS_ACTUAL_BINDING_PENDING',
 'helper':{'path':str(SOURCE),'sha256':EXPECTED},'producerCodePins':producer_pins,'producerSchemasReadOnly':True,
 'producerSchemaEvidenceLines':{'collect_reviewed_r07.py':[259,268,297,307],'render_reviewed_r04.py':[50,54,69,73,88,91,101,113]},
 'tests':tests,'syntheticCases':len(tests),'staticSourceChecks':source_checks,'staticSourceCheckCount':len(source_checks),'findings':findings,
 'allHelperAndProducerCodeBytesUnchanged':True,'helperImported':False,'metadataModelASTOnlyExecuted':True,
 'producerImported':False,'producerExecuted':False,'buildExecuted':False,'oldHoldReceipt':{'path':str(A/'binding-r01-independent-metadata-probes-r01.json'),'sha256':sha((A/'binding-r01-independent-metadata-probes-r01.json').read_bytes())},'oldFindingsAddressedInPureMetadataScope':True,'actualCollectionRead':False,'actualRenderRecordsRead':False,
 'actualMarkdownRead':False,'actualPNGRead':False,'actualHTMLRead':False,'actualSourceRead':False,'actualOldOutputRead':False,
 'actualBindingWritten':False,'providerExecuted':False,'markerExecuted':False,'nativeAuthorExecuted':False,
 'semanticApproval':False,'formalQualityAssessed':False,'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,
 'reviewer':'/root/delivery_tools/registration_pdf_qa',
 'limits':['Actual collector/render records and their documents were not inspected; code schemas and synthetic objects only.',
           'Actual MD/PNG/HTML byte coverage and filesystem gates live in build() and were source-inspected only; this pure scope does not prove them.',
           'Approved subset may differ from full collection, but this check does not infer full plan completion or native/semantic quality.']}
p=A/'binding-r02-independent-metadata-probes-r01.json'
with p.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p.read_bytes()),'syntheticCases':len(tests),'staticSourceChecks':len(source_checks),'findings':[v['id'] for v in findings]},ensure_ascii=False))
