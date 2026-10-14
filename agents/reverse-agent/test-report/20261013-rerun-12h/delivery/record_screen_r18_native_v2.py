"""Record explicit actual-view indices with exact RGBA and all-pixel coverage."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
from PIL import Image

HERE=Path(__file__).resolve().parent;REPORT=HERE.parent
RECEIPT=REPORT/'training-assisted/runtime-code-assisted-10.json'
RECEIPT_SHA='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
CASES={'registration-basic':('assisted-registration-basic-r07-delivery-r18','d989620e9bcd27d3059a1b8de9aa8bfd79e7ab68d0974e9d2ac04d8719e2a03e',46),
       'code-design':('assisted-code-design-r01-delivery-r18','5fa8b8184b88c3066cf4bc1233a73a350845953ccc2970b0ff9cce82a5a7dbf3',28),
       'search-detail':('assisted-search-detail-r04-delivery-r18','dd466812fcd18679da84b001b9d4c8ee584bb3b9323e82a34e5940285c184287',26)}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*')
    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('case',choices=CASES)
    parser.add_argument('--actually-viewed',type=Path,required=True);parser.add_argument('--findings',type=Path);args=parser.parse_args()
    findings=json.loads(args.findings.read_text(encoding='utf-8-sig')) if args.findings else []
    name,pins_sha,count=CASES[args.case]
    viewed=json.loads(args.actually_viewed.read_text(encoding='utf-8-sig'))
    assert viewed==list(range(count)), 'Every explicit actual-view index is required'
    assert sha(RECEIPT)==RECEIPT_SHA
    receipt=json.loads(RECEIPT.read_text(encoding='utf8'));frozen=Path(receipt['destination'])
    assert inventory(frozen)==receipt['files'] and receipt['fileCount']==126
    render=REPORT/'render'/name;pin_path=render/'render-pins.json'
    assert sha(pin_path)==pins_sha
    pins=json.loads(pin_path.read_text(encoding='utf8'))
    assert pins['rendererRuntimeReceiptSha256']==RECEIPT_SHA and pins['rendererRuntimeLabel']=='r18'
    assert pins['structure']['status']==pins['display']['status']=='PASS'
    assert pins['display']['blockedRequests']==[] and pins['safety']['removed']==[]
    assert all(sha(path)==value for path,value in pins['inputPins'].items())
    assert sha(render/pins['canonicalHtmlFilename'])==pins['canonicalHtmlSha256']
    inventory_path=REPORT/'visual-review'/(name+'-tiles')/'inventory.json'
    inv=json.loads(inventory_path.read_text(encoding='utf8'))
    assert inv['renderPinsSha256']==pins_sha and len(inv['captures'])==count
    assert inv['pixelComparator']=='exact RGBA byte equality; opaque color differences are rejected'
    seen=[];groups={}
    for index,record in enumerate(inv['captures']):
        assert sha(record['path'])==record['sha256'] and sha(record['originalPath'])==record['originalSha256']
        rect=record['sourceRectangle'];box=(rect['x'],rect['y'],rect['x']+rect['width'],rect['y']+rect['height'])
        with Image.open(record['originalPath']) as original,Image.open(record['path']) as tile:
            expected=original.crop(box).convert('RGBA')
            assert expected.size==tile.size and expected.tobytes()==tile.convert('RGBA').tobytes()
            assert list(original.size)==record['wholeOriginalSize'] and record['scale']==1
        groups.setdefault(record['imageId'],[]).append(record)
        seen.append(dict(record,actuallyReviewed=True,actualViewIndex=index,
                         viewMethod='view_image original detail',geometryFindings=[f for f in findings if f['imageId']==record['imageId']]))
    for image_id,records in groups.items():
        coverage=Image.new('1',tuple(records[0]['wholeOriginalSize']),0)
        for record in records:
            rect=record['sourceRectangle']
            coverage.paste(1,(rect['x'],rect['y'],rect['x']+rect['width'],rect['y']+rect['height']))
        assert coverage.getextrema()==(1,1),image_id
    report={'schema':'screen-native-review/2','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'FAIL_NATIVE_GEOMETRY' if findings else 'PASS_NATIVE_GEOMETRY_ONLY','documentId':pins['documentId'],'documentSha256':pins['sourceSha256'],
        'canonicalDocumentPath':pins['canonicalDocumentPath'],'canonicalHtmlSha256':pins['canonicalHtmlSha256'],
        'renderPins':str(pin_path),'renderPinsSha256':pins_sha,'rendererRuntimeReceipt':str(RECEIPT),
        'rendererRuntimeReceiptSha256':RECEIPT_SHA,'frozenRuntimeAll126FilesUnchanged':True,
        'inputBeforeAfterPinsUnchanged':True,'tileInventory':str(inventory_path),'tileInventorySha256':sha(inventory_path),
        'actuallyViewedIndexRecord':str(args.actually_viewed),'actuallyViewedIndexRecordSha256':sha(args.actually_viewed),
        'actuallyViewedTileCount':count,'actuallyViewedImageCount':len(groups),
        'diagramCount':len(pins['diagrams']),'layoutCount':len(pins['layouts']),
        'exactRgbaComparisonAndCompletePixelCoverage':True,'captures':seen,'findings':findings,
        'checked':['whole identifiers/numbers','visible labels and connectors','opaque label backgrounds',
                   'crop continuity and full pixel coverage','static layout fields and bounds'],
        'referenceMode':'training-assisted','sourceSnapshotManifestSha256':pins['sourceSnapshotManifestSha256'],
        'scope':{'canonicalMarkdownEdited':False,'businessSourceOrOriginalSpecificationRead':False,
                 'applicationExecuted':False,'formalRubricEvaluated':False,'stateProjectionIncluded':False,
                 'wholeQualityApproved':False,'published':False},
        'pdfReadability':'NOT_ASSESSED','xlsxVisualFidelity':'NOT_ASSESSED',
        'limits':['Current canonical-native pixels only; full PDF and XLSX review remain separate gates.',
                  'Approved state projections are kept in separate parent-owned records.',
                  'Static controls are illustrative, not application execution evidence.']}
    out=HERE/(name+'-native-qa.json');assert not out.exists()
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'path':str(out),'sha256':sha(out),'tiles':count,'images':len(groups)},ensure_ascii=False))

if __name__=='__main__':main()
