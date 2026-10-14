"""Fresh pure metadata tests; old r01 HOLD and its probe are preserved."""
import ast,hashlib,json
from pathlib import Path
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
old=A/'probe_delivery_binding_metadata_r01.py';before=hashlib.sha256(old.read_bytes()).hexdigest();text=old.read_text(encoding='utf-8')
for a,b in (
 ('build_delivery_binding_r01.py','build_delivery_binding_r02.py'),
 ('9086ce5c0d0a1f187568352bc59004bcc840bb4f87c542c9a38b7c3d966547c2','866269fd244073bae610eed8fd0683e2d5b1cd4073f9fcbeb8f8f3928d039c5b'),
 ('binding-r01-independent-metadata-probes-r01.json','binding-r02-independent-metadata-probes-r01.json'),
 ("'status':'HOLD_PURE_METADATA_SHA_ID_MODULE_CONTRACT'","'status':'CODE_AND_PURE_METADATA_PASS_ACTUAL_BINDING_PENDING'"),
):assert a in text;text=text.replace(a,b)
anchor="model_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='metadata_model')"
add='''def descriptor_shape(record):
    require(isinstance(record,dict) and set(record)=={'path','sha256'},'exact descriptor')
    require(isinstance(record['path'],str) and isinstance(record['sha256'],str) and re.fullmatch('[0-9a-f]{64}',record['sha256']) is not None,'strict descriptor pin')
    return safe(record['path'])
ns.update(re=re,descriptor_shape=descriptor_shape)
for name in ('digest','approved_ids'):
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),'exec'),ns)
'''
assert text.count(anchor)==1;text=text.replace(anchor,add+'\n'+anchor)
anchor="records=[{'pins':pins,'manifest':manifest}];tests=[];findings=[]"
addition='''doc.update(draftResultSha256='d'*64,analysisHandoffSha256='e'*64)
pins['collectorDocument']=copy.deepcopy(doc)
runtime_root=W/'runtime-code/SYNTHETIC'
collection['runtimeProvenance']={'receiptSha256':'9'*64,'runtimeRoot':str(runtime_root),'runtimeFileCount':2,'runtimeFiles':{'contextbase/ai/rendering.py':'b'*64,'synthetic/__init__.py':'c'*64},'loadedImports':{},'criticalModules':{}}
grant.update(runtimeReceiptSha256='9'*64,permittedRuntimeRoot=str(runtime_root))
pins.update(collection=selection['collection']['path'],renderer=str(runtime_root/'contextbase/ai/rendering.py'),originalRendererManifestSha256='f'*64)
manifest['originalRendererManifestSha256']='f'*64
'''
assert text.count(anchor)==1;text=text.replace(anchor,addition+'\n'+anchor)
oldblock="s,c,g,r=inputs();mutate(s,c,g,r);ns['metadata_model'](s,c,g,r)\n        findings.append({'id':name,'observedBy':'pure metadata synthetic counterexample','finding':finding})"
newblock="s,c,g,r=inputs();mutate(s,c,g,r);reject(lambda:ns['metadata_model'](s,c,g,r))"
assert text.count(oldblock)==1;text=text.replace(oldblock,newblock)
anchor="functions={n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef)}"
extra='''negative('missing-runtime-root-grant',lambda s,c,g,r:g.pop('permittedRuntimeRoot'))
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
'''
assert text.count(anchor)==1;text=text.replace(anchor,extra+'\n'+anchor)
text=text.replace("'actualCollectionRead':False", "'oldHoldReceipt':{'path':str(A/'binding-r01-independent-metadata-probes-r01.json'),'sha256':sha((A/'binding-r01-independent-metadata-probes-r01.json').read_bytes())},'oldFindingsAddressedInPureMetadataScope':True,'actualCollectionRead':False")
ast.parse(text);target=A/'probe_delivery_binding_metadata_r02.py'
with target.open('x',encoding='utf-8') as h:h.write(text)
assert hashlib.sha256(old.read_bytes()).hexdigest()==before
print(json.dumps({'freshProbe':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'oldProbeUnchanged':True},ensure_ascii=False))
