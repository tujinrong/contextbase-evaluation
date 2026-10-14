"""Exact RGBA crops of immutable Artifact or owned read-only Excel previews."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json
from PIL import Image

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path)
    p.add_argument('--model', type=Path)
    p.add_argument('--excel-result', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    assert bool(a.manifest) != bool(a.excel_result)
    assert not a.output.exists()
    pins={str(Path(__file__).resolve()):sha(__file__)}
    if a.manifest:
        assert a.model
        m=json.loads(a.manifest.read_text(encoding='utf8'))
        model=json.loads(a.model.read_text(encoding='utf8'))
        assert len(m['documents'])==len(model['documents'])
        pins.update({str(a.manifest):sha(a.manifest),str(a.model):sha(a.model),model['binding']:sha(model['binding'])})
        documents=m['documents']; scope='ARTIFACT_NATIVE_PREVIEW'
    else:
        r=json.loads(a.excel_result.read_text(encoding='utf8'))
        assert r['status']=='STATIC_EXCEL_BITMAP_EXPORTED_VISUAL_REVIEW_PENDING'
        assert r['readOnly'] and r['macrosDisabled'] and r['updateLinks']==0 and not r['visible']
        assert r['workbookBytesUnchanged'] and r['planBytesUnchanged'] and not r['saved']
        assert not r['pageSetupChanged'] and not r['cellsOrFormatsChanged'] and not r['originalApplicationExecuted']
        plan=json.loads(Path(r['plan']).read_text(encoding='utf8'))
        assert sha(r['plan'])==r['planSha256'] and sha(r['workbook'])==r['beforeSha256']==r['afterSha256']
        assert len(plan['previews'])==len(r['sheets'])
        previews=[]
        for expected,actual in zip(plan['previews'],r['sheets']):
            assert expected['sheet']==actual['sheet'] and expected['range']==actual['range']
            assert actual['clipboardOnlyOwnContentRead'] and not actual['cellOrFormatChanges']
            assert actual['clipboardSequenceBefore']!=actual['clipboardOwnSequence']
            previews.append({'path':actual['png'],'sha256':actual['pngSha256'],'sheet':actual['sheet'],'range':actual['range']})
        pins.update({str(a.excel_result):sha(a.excel_result),r['plan']:r['planSha256'],r['workbook']:r['beforeSha256']})
        documents=[{'documentId':plan.get('documentId','READ_ONLY_EXCEL'),'canonicalDocumentPath':plan.get('canonicalDocumentPath'),
                    'markdownSha256':plan.get('markdownSha256'),'xlsx':r['workbook'],'xlsxSha256':r['beforeSha256'],'previews':previews}]
        scope='OWNED_READ_ONLY_EXCEL_BITMAP_PREVIEW'
    for d in documents:
        assert sha(d['xlsx'])==d['xlsxSha256'];pins[d['xlsx']]=d['xlsxSha256']
        for v in d['previews']:
            assert sha(v['path'])==v['sha256'];pins[v['path']]=v['sha256']
    a.output.mkdir();result=[]
    for d in documents:
        target=a.output/d['documentId'];target.mkdir();captures=[]
        for ordinal,v in enumerate(d['previews']):
            with Image.open(v['path']) as original:
                original.load()
                rectangles=[]
                for y in range(0,original.height,1700):
                    for x in range(0,original.width,1700):
                        bounds=(x,y,min(x+1800,original.width),min(y+1800,original.height))
                        crop=original.crop(bounds);dest=target/f'preview-{ordinal+1:03}-{x:04}-{y:04}.png';crop.save(dest)
                        with Image.open(dest) as saved:
                            assert saved.size==crop.size and saved.convert('RGBA').tobytes()==crop.convert('RGBA').tobytes()
                        rectangles.append(bounds)
                        captures.append({'originalPreviewIndex':ordinal,'sheet':v['sheet'],'range':v['range'],'originalPath':v['path'],
                          'originalSha256':v['sha256'],'path':str(dest),'sha256':sha(dest),'sourceRectangle':{'x':x,'y':y,'width':bounds[2]-x,'height':bounds[3]-y},
                          'wholeOriginalSize':list(original.size),'scale':1,'pixelsEqualToOriginalRegion':True,'actuallyReviewed':False})
                for y in range(original.height):
                    intervals=sorted((x0,x1) for x0,y0,x1,y1 in rectangles if y0<=y<y1)
                    cursor=0
                    for left,right in intervals:
                        assert left<=cursor;cursor=max(cursor,right)
                    assert cursor==original.width
        result.append({k:d.get(k) for k in ['documentId','canonicalDocumentPath','markdownSha256','xlsx','xlsxSha256']}|
          {'originalPreviewCount':len(d['previews']),'captures':captures,'nativeApproval':False})
    assert all(sha(path)==value for path,value in pins.items())
    report={'schema':'derived-native-review-tile-inventory/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':scope,
      'pixelComparator':'exact RGBA bytes','coverage':'all original pixels, original scale, up to 100px overlap',
      'sourceBindings':pins,'documents':result,'formalApproval':False,'published':False,'applicationExecuted':False}
    dest=a.output/'inventory.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'inventory':str(dest),'sha256':sha(dest),'documents':[(d['documentId'],d['originalPreviewCount'],len(d['captures'])) for d in result]}))

if __name__=='__main__':run()
