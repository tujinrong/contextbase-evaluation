"""Mechanical evidence binder for actual actor views; no document authoring."""
import argparse, hashlib, json, os
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image
import numpy as np

ROOT=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\training-assisted\search-basic-r07-display')
INV=ROOT/'html-columns-r02-native-tiles-r01/inventory.json'
RESULT=ROOT/'html-columns-r02/result.json'

def safe(p):
    p=Path(os.path.abspath(p))
    for a in (p,*p.parents):
        assert not a.is_symlink()
        assert not (a.exists() and getattr(a.lstat(),'st_file_attributes',0)&0x400)
    return p
def sha(p): return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def read(p): return json.loads(safe(p).read_text(encoding='utf-8'))
def pin(pins,p,expected=None):
    p=str(safe(p)); actual=sha(p)
    assert expected is None or actual==expected,(p,actual,expected)
    assert p not in pins or pins[p]==actual
    pins[p]=actual
def inventory(root):
    root=safe(root);out={}
    def visit(d):
        for p in sorted(safe(d).iterdir()):
            p=safe(p)
            if p.name=='__pycache__' or p.suffix in ('.pyc','.pyo'):continue
            if p.is_dir():visit(p)
            elif p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
            else:raise ValueError('Unexpected frozen entry')
    visit(root);return out
def covers(spans,end):
    at=0
    for start,stop in sorted(spans):
        assert start<=at and stop>start
        at=max(at,stop)
    assert at==end

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--child-review',type=Path,required=True);ap.add_argument('--child-sha',required=True)
    args=ap.parse_args();assert safe(args.child_review).is_relative_to(safe(ROOT))
    assert sha(INV)=='67d412bd3d50ac1eaa1c67ca5e0cdea9cf0501f2c154618204349bd5b0db0da0'
    assert sha(RESULT)=='24b2ec5c3120935e5fa8332e9aa9391763d8ce7a9ffa935754447a9b0b3129f1'
    assert sha(args.child_review)==args.child_sha
    inv=read(INV);r=read(RESULT);child=read(args.child_review)
    assert child['status']=='PASS_WITH_NOTES_ASSIGNED_FIRST16_NATIVE_GEOMETRY_ONLY'
    assert child['actualVisualCoverage']['indices']==list(range(16)) and child['actualVisualCoverage']['count']==16
    assert child['actualVisualCoverage']['detail']=='original' and child['blockingFindings']==[]
    assert child['mechanicalChecks']['all493PinnedFileSha256BeforeAfterEqual'] and child['mechanicalChecks']['all64ExactRgbaCropsRechecked']
    captures=inv['captures'];assert len(captures)==64
    # Actor 0..15 review is external and bound by exact receipt bytes.
    # Root-side delivery actor personally viewed indices 16..63 via original-detail view_image.
    ours=list(range(16,64));assert len(ours)==48
    pins=dict(r['sourceBindings'])
    for p,h in list(pins.items()):assert sha(p)==h
    for p in (INV,RESULT,args.child_review,ROOT/'native-review-r01.json',ROOT/'capture-columns-r01-failure-review.json',ROOT/'capture_search_basic_columns_r02.py',ROOT/'capture-search-basic-columns-r02-preparation.json',ROOT/'html-columns-r02/worker.json',ROOT/'html-columns-r02/stages.jsonl',ROOT/'html-columns-r02/candidate.css',Path(__file__)):
        pin(pins,p)
    pin(pins,r['projectionHtml'],r['projectionHtmlSha256'])
    assert r['bodyRawBytesEqual'] and r['bodyDomBytesEqual'] and r['bodyTextEqual']
    assert r['allTablesDeepExact'] and r['allImageElementsDeepExact'] and r['bodyElementOrderExact']
    assert r['removeInsertedElementRecoversOriginalBytes'] and r['unmarkedAndOneTwoColumnTableComputedPropertiesExact']
    assert r['javascriptEnabled'] is False and r['networkRequests']==[] and r['asciiWholeTokenWrapDiagnostics']==[]
    pages=r['documentCapture']['pages'];assert len(pages)==11
    covers([(p['y'],p['y']+p['height']) for p in pages],r['documentCapture']['height'])
    pixel_records=[]
    for page in pages:
        pin(pins,page['path'],page['sha256'])
        with Image.open(safe(page['path'])) as image:
            original=image.convert('RGBA');assert original.size==(2400,page['height'])
            selected=[(i,c) for i,c in enumerate(captures) if c['originalPath']==page['path']]
            assert selected
            ys=sorted({0,page['height'],*[y for _,c in selected for y in (c['sourceRectangle']['y'],c['sourceRectangle']['y']+c['sourceRectangle']['height'])]})
            for low,high in zip(ys,ys[1:]):
                spans=[]
                for _,c in selected:
                    rect=c['sourceRectangle'];y=rect['y']
                    if y<=low and y+rect['height']>=high:spans.append((rect['x'],rect['x']+rect['width']))
                covers(spans,2400)
            for i,c in selected:
                assert c['originalSha256']==page['sha256'];pin(pins,c['path'],c['sha256'])
                t=c['sourceRectangle'];box=(t['x'],t['y'],t['x']+t['width'],t['y']+t['height'])
                with Image.open(safe(c['path'])) as image:
                    tile=image.convert('RGBA');expected=original.crop(box)
                    assert tile.size==expected.size and np.array_equal(np.asarray(tile),np.asarray(expected))
                pixel_records.append({'index':i,'path':c['path'],'sha256':c['sha256'],'originalPath':c['originalPath'],'originalSha256':c['originalSha256'],'sourceRectangle':t,'exactRGBA':True})
    receipt=read(ROOT.parent/'runtime-code-assisted-10.json')
    assert len(receipt['files'])==126 and inventory(receipt['destination'])==receipt['files']
    assert all(sha(p)==h for p,h in pins.items())
    output={
        'schema':'reverse-agent-css-only-actual-native-review/2','createdUtc':datetime.now(timezone.utc).isoformat(),
        'documentId':r['documentId'],'markdownSha256':r['markdownSha256'],
        'scope':'DERIVED_CSS_ONLY_STATIC_GEOMETRY_ONLY','status':'PASS_WITH_NOTES_DERIVED_NATIVE_GEOMETRY_ONLY',
        'sourceHtml':r['sourceHtml'],'sourceHtmlSha256':r['sourceHtmlSha256'],
        'projectionHtml':r['projectionHtml'],'projectionHtmlSha256':r['projectionHtmlSha256'],
        'cssSha256':r['cssSha256'],'css':r['css'],'outerHtmlBoundary':r['outerHtmlBoundary'],
        'insertOnlyInverseExact':True,'bodyRawBytesEqual':True,'bodyDomBytesEqual':True,'bodyTextEqual':True,
        'allTablesDeepExact':True,'allImageElementsDeepExact':True,'bodyElementOrderExact':True,
        'unmarkedAndOneTwoColumnTableComputedPropertiesExact':True,
        'captureResult':{'path':str(RESULT),'sha256':sha(RESULT),'workerStatus':'COMPLETE','exitCode':0},
        'nativeInventory':{'path':str(INV),'sha256':sha(INV),'originalPages':11,'tiles':64,'fullDocumentWidth':2400,'fullDocumentHeight':43062},
        'actors':[{'actor':'/root/delivery_tools/registration_pdf_qa','actualIndices':list(range(16)),'receipt':str(args.child_review),'receiptSha256':args.child_sha,'scope':'first16 only'},
                  {'actor':'/root/delivery_tools','actualIndices':ours,'viewMechanism':'tools.view_image(detail=original) returned full original pixels','actualViewedTileCount':48,'scope':'indices16..63 only'}],
        'actualViewedUnion':list(range(64)),'actualViewedTileCount':64,'missingActualViews':[],
        'allPixelsCovered':True,'allTilesExactRGBA':True,'pixelEvidence':sorted(pixel_records,key=lambda x:x['index']),
        'blockingFindings':[],
        'notes':['Wide 2400px viewing projection; horizontal crops require original-size viewing or horizontal scrolling.',
                 '100px crop overlap and original page continuations were inspected; crop cuts are distinguished from internal label/identifier breaks.',
                 'Embedded layout and 27 original Mermaid PNGs remain unchanged; fresh body view does not replace state capture.',
                 'ASCII cell diagnostic reports zero multiline whole tokens; numeric-only labels rely on actual image review.',
                 'Original 1440px native HOLD and first CSS helper boundary rejection remain historical unchanged evidence.'],
        'oldHold':{'path':str(ROOT/'native-review-r01.json'),'sha256':sha(ROOT/'native-review-r01.json'),'statusPreserved':'HOLD_FULL_BODY_FIRST_COLUMN_IDENTIFIER_WRAP'},
        'firstAttemptFailure':{'path':str(ROOT/'capture-columns-r01-failure-review.json'),'sha256':sha(ROOT/'capture-columns-r01-failure-review.json'),'preserved':True},
        'frozenRuntimeReceipt':{'path':str(ROOT.parent/'runtime-code-assisted-10.json'),'sha256':sha(ROOT.parent/'runtime-code-assisted-10.json'),'fileCount':126,'nonCacheInventoryBeforeAfterExact':True},
        'beforeAfterPins':pins,'allPinnedBytesUnchanged':True,'borrowedActualCoverage':0,
        'javascriptEnabled':False,'networkRequests':[],'providerExecuted':False,'applicationExecuted':False,
        'sourceModified':False,'canonicalModified':False,'originalHtmlModified':False,'mainModified':False,'businessContentAuthored':False,
        'formalApproval':False,'semanticApproval':False,'stateApproval':False,'wholeDocumentApproval':False,'adoptionApproval':False,'published':False,
        'remaining':['Root-owned strict state normalizer/capture/native QA pending.','Formal grading/whole 11-document gate/collection/adoption not performed here.','PDF/XLSX for this r07 candidate not exported in this display-only task.']}
    target=ROOT/'css-native-review-r02.json'
    with safe(target).open('x',encoding='utf-8') as f:json.dump(output,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'path':str(target),'sha256':sha(target),'pins':len(pins),'actualTiles':64,'status':output['status']},ensure_ascii=False))

if __name__=='__main__':main()
