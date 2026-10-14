"""Seal own completed native observations and metadata-only fresh delivery binding."""
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;REPORT=HERE.parents[1];REPO=HERE.parents[5]
def safe(p):
 p=Path(os.path.abspath(p))
 for a in (p,*p.parents):
  if a.is_symlink() or (a.exists() and getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path rejected')
 return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_bytes())
cap='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
runtime_receipt=REPORT/'training-assisted/runtime-code-assisted-10.json'
assert sha(runtime_receipt)=='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
freeze=load(runtime_receipt);runtime=safe(freeze['destination'])
actual={p.relative_to(runtime).as_posix():sha(p) for p in runtime.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
assert actual==freeze['files'] and len(actual)==126
groups={'indexGraphs':'table-index-graphs-native','indexDocument':'table-index-document-native','oplogDocument':'operation-log-document-native'}
expected_counts={'indexGraphs':22,'indexDocument':35,'oplogDocument':4}
reviews={};all_view_log=[];all_pins={str(runtime_receipt):sha(runtime_receipt)}
for name,directory in groups.items():
 invp=HERE/directory/'inventory.json';inv=load(invp);records=inv['captures'];assert len(records)==expected_counts[name]
 all_pins[str(invp)]=sha(invp)
 originals={}
 for i,c in enumerate(records,1):
  p,original=safe(c['path']),safe(c['originalPath']);assert sha(p)==c['sha256'] and sha(original)==c['originalSha256']
  all_pins[str(p)]=c['sha256'];all_pins[str(original)]=c['originalSha256']
  image=Image.open(original).convert('RGBA');tile=Image.open(p).convert('RGBA');r=c['sourceRectangle']
  box=(r['x'],r['y'],r['x']+r['width'],r['y']+r['height'])
  assert c['scale']==1 and tile.size==(r['width'],r['height']) and tile.tobytes()==image.crop(box).tobytes()
  if str(original) not in originals:originals[str(original)]=[image,[]]
  originals[str(original)][1].append(box)
  all_view_log.append({'group':name,'viewIndex':i,'path':str(p),'sha256':c['sha256'],'sourceRectangle':r,
    'actuallyViewedBy':'/root/source_pilot','viewMethod':'tools.view_image(detail=original) then image(detail=original)','scale':1,'actualViewCompleted':True})
 for original,(image,rects) in originals.items():
  mask=Image.new('L',image.size,0);draw=ImageDraw.Draw(mask)
  for x0,y0,x1,y1 in rects:draw.rectangle((x0,y0,x1-1,y1-1),fill=255)
  assert mask.histogram()[255]==image.width*image.height
 reviews[name]={'inventory':str(invp),'inventorySha256':sha(invp),'originalImageCount':len(originals),'actualOwnNativeTileViews':len(records),
   'allOriginalPixelsCovered':True,'exactRGBARecheckedAfterViews':True}
 for p,d in inv.get('pins',{}).items():assert sha(Path(p))==d;all_pins[p]=d
assert len(all_view_log)==61
binding_docs=[];documents=[]
cases=[('table-index','reviewed-table-index-r04-r11-pin.json','a35d6145a5f056fdca062f2e5b18a47a8405b0041c9ef029300a8455c0ba71c4'),
       ('operation-log','reviewed-operation-log-r04-r11-pin.json','34af4227c5b28000427376f7f6c454783c712d010222d581333bdce43888d73a')]
for name,pinname,pinsha in cases:
 rp=REPORT/'training-assisted'/pinname;assert sha(rp)==pinsha;root=load(rp)
 render=REPORT/'render'/('assisted-'+name+'-r04-delivery-r18');pp=render/'render-pins.json';pins=load(pp)
 assert pins['sourceSha256']==root['sha256'] and pins['referenceMode']=='training-assisted'
 assert pins['rendererRuntimeReceiptSha256']==sha(runtime_receipt) and pins['structure']['status']==pins['display']['status']=='PASS'
 assert not pins['safety']['removed'] and not pins['safety']['inputJavaScriptEnabled']
 for path,digest in pins['inputPins'].items():assert sha(Path(path))==digest;all_pins[path]=digest
 md=safe(root['canonicalMarkdown']);draft=safe(root['draftResult']);review=safe(root['independentReview']);handoff=review.with_name('review-handoff.json');h=load(handoff)
 assert sha(md)==root['sha256'] and sha(draft)==root['draftResultSha256'] and sha(review)==root['independentReviewSha256']
 assert root['independentReviewApproved'] is True and root['noFurtherTextRevisionPlanned'] is True
 assert h['approved'] is True and h['documentSha256']==root['sha256'] and h['reviewSha256']==sha(review) and h['snapshot']['manifestSha256']==cap
 assert safe(h['documentFile'])==md and h['referenceMode']=='training-assisted'
 for p in [rp,pp,render/'manifest.json',md,draft,review,handoff]:all_pins[str(p)]=sha(p)
 document={'documentId':root['documentId'],'canonicalDocumentPath':root['path'],'markdown':str(md),'markdownSha256':root['sha256'],
  'renderDirectory':str(render),'renderPinsSha256':sha(pp),'renderManifestSha256':sha(render/'manifest.json'),'draftResult':str(draft),
  'draftResultSha256':sha(draft),'rootReviewedPin':str(rp),'rootReviewedPinSha256':pinsha,
  'separateApprovedReview':{'handoff':str(handoff),'handoffSha256':sha(handoff),'review':str(review),'reviewSha256':sha(review),'approved':True,'scope':'text-source-and-structure'},
  'stateProjectionIncluded':False}
 binding_docs.append(document)
 documents.append({'documentId':root['documentId'],'markdownSha256':root['sha256'],'renderPinsSha256':sha(pp),
  'status':'PASS_NATIVE_GEOMETRY_ONLY','blockingFindings':[],'nativeGeometryApproved':True,
  'actualOwnNativeTileViews':57 if name=='table-index' else 4,
  'notes':['Narrow Japanese logical-name/header columns wrap vertically while remaining fully visible and readable.',
           'Some ordinary plaintext hyphenated control labels wrap at legal hyphen boundaries; this was distinguished from token-internal anywhere wrapping.',
           'Document capture tile boundaries split large diagrams; complete adjacent captures and the separate original diagram review preserve the visible continuation.'] if name=='table-index' else ['Nine-column definitions have narrow Japanese headings/logical names; all nine columns and complete ASCII physical names remain visible.']})
review_out=HERE/'native-review.json'
assert not review_out.exists()
review_out.write_text(json.dumps({'schema':'own-assisted-native-geometry-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'subject':'training-assisted delivery','status':'PASS_NATIVE_GEOMETRY_ONLY','documents':documents,'groups':reviews,'actualOwnNativeTileViews':61,
 'actualViewLog':all_view_log,'immutablePins':all_pins,'allPinsRecheckedAfterActualView':True,'runtimeFullMembership126Verified':True,
 'runtimeRenderImportsVerifiedInRenderWrapper':2,'sourceSnapshotManifestSha256':cap,'sourceOnlyBaseline':'CLOSED',
 'canonicalMarkdownOriginalImagesChanged':0,'providerOriginalAppDatabaseRuns':0,'semanticApproval':False,'formalApproval':False,'adoptionApproval':False,
 'originalReferenceRubricExpectedGradingAnswerRead':False},ensure_ascii=False,indent=2),encoding='utf-8')
for d in binding_docs:d.update(nativeGeometryReview=str(review_out),nativeGeometryReviewSha256=sha(review_out))
binding=HERE/'binding.json';assert not binding.exists()
binding.write_text(json.dumps({'schema':'reverse-agent-delivery-binding/1','referenceMode':'training-assisted',
 'permittedMarkdownRoot':str(REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'),
 'permittedRenderRoot':str(REPORT/'render'),'sourceSnapshotManifestSha256':cap,'formalQualityGatePassed':False,
 'wholeQualityApproved':False,'published':False,'documents':binding_docs},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'nativeReview':str(review_out),'nativeReviewSha256':sha(review_out),'binding':str(binding),'bindingSha256':sha(binding),'actualOwnViews':61},ensure_ascii=False))
