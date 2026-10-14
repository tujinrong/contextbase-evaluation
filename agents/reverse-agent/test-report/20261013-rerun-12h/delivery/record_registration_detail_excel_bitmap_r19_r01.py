"""Record completed actual-pixel review without changing any candidate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
P=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ip=P/'excel-bitmap-registration-detail-r19-r01-tiles/inventory.json'
assert sha(ip)=='79f5f26f83ebbbfdb6729a3d907ed2287c4a832bda0cbb0ca7de936475fd63fe'
inv=json.loads(ip.read_text(encoding='utf8'));d=inv['documents'][0]
assert d['originalPreviewCount']==60 and len(d['captures'])==114
bp=P/'binding-assisted-registration-detail-r19-r01.json'
assert sha(bp)=='4da2b4855945a1f14b33d0defa9a4820b47d59807a01693a4c6e79828724714d'
e=json.loads(bp.read_text(encoding='utf8'))['documents'][0]
pins=dict(inv['sourceBindings']);pins[str(ip)]=sha(ip);pins[str(bp)]=sha(bp)
pins[e['markdown']]=e['markdownSha256']
for name,key in [('render-pins.json','renderPinsSha256'),('manifest.json','renderManifestSha256')]:
    pins[str(Path(e['renderDirectory'])/name)]=e[key]
rp=P/'excel-bitmap-registration-detail-r19-r01/result.json'
r=json.loads(rp.read_text(encoding='utf8'));plan=json.loads(Path(r['plan']).read_text(encoding='utf8'))
assert r['workbookBytesUnchanged'] and r['planBytesUnchanged'] and r['readOnly']
assert not r['saved'] and not r['pageSetupChanged'] and not r['cellsOrFormatsChanged']
assert len(r['cells'])==len(plan['cells'])==1323
for expected,actual in zip(plan['cells'],r['cells']):
    assert (expected['sheet'],expected['cell'])==(actual['sheet'],actual['cell'])
    assert actual['value2']==expected['value'] or (expected['value']=='' and actual['value2'] is None)
    if expected['value']!='': assert actual['value2Type']=='System.String'
views=[]
for n,c in enumerate(d['captures']):
    assert c['scale']==1 and c['pixelsEqualToOriginalRegion']
    pins[c['path']]=c['sha256'];pins[c['originalPath']]=c['originalSha256']
    views.append({**c,'captureIndexZeroBased':n,'actuallyReviewed':True,'actuallyViewedBy':'delivery_tools','view':'original pixels'})
assert all(sha(k)==v for k,v in pins.items())
c=d['captures'][35]
finding={'sheet':'イベント仕様','cell':'U200','token':'EV-REG-001','visibleRows':['EV-','REG-001'],
    'finding':'An actual Excel paragraph wraps the event identifier at its authored hyphen. All literal characters remain present, but the whole identifier does not occupy one visible line.',
    'captureIndexZeroBased':35,'companionCaptureIndexZeroBased':36,'path':c['path'],'sha256':c['sha256'],'range':c['range']}
out=P/'registration-detail-excel-bitmap-r19-r01-actual-native-review.json';assert not out.exists()
record={'schema':'reverse-agent-owned-excel-actual-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'OWNED_READ_ONLY_EXCEL_BITMAP_GEOMETRY_ONLY','referenceMode':'training-assisted',
    'documentId':e['documentId'],'canonicalDocumentPath':e['canonicalDocumentPath'],'markdownSha256':e['markdownSha256'],
    'xlsx':d['xlsx'],'xlsxSha256':d['xlsxSha256'],'inventory':str(ip),'inventorySha256':sha(ip),
    'actualOriginalPreviews':60,'actualOriginalTiles':114,'actuallyViewedZeroBasedIndices':list(range(114)),
    'views':views,'status':'HOLD_WHOLE_EVENT_IDENTIFIER_HYPHEN_WRAP','blocking':[finding],
    'literalDisplay':'PASS_EXACT_STRING_VALUES_INCLUDING_LEADING_ZEROS','internalAsciiNumericWrap':'PASS',
    'notes':['All 60 ranges, 114 exact-RGBA tiles, all columns and 21 original graph / 3 static layout images were actually viewed at original scale.',
    'Artifact-native input and 02 internal wraps are resolved in actual Excel; the earlier partial Artifact HOLD is preserved.',
    'Other source citation line ranges and paths may naturally wrap at authored hyphens or slashes; no missing, hidden or cropped literal values were observed.',
    'Graphs continue across consecutive copied ranges; original flow / ER text and connector regions remain visible across these ranges.',
    'CopyPicture temporarily wrote the clipboard. Prior clipboard content was neither read nor output; only owned copied sequence content was read.',
    'Static derived workbook display only. ASP.NET application and business operations were not executed.'],
    'exactNonemptyStrings':sum(x['value']!='' for x in plan['cells']),'blankEquivalence':sum(x['value']=='' for x in plan['cells']),
    'excelVersion':r['excelVersion'],'excelBuild':r['excelBuild'],'ownedReadOnly':True,'saved':False,
    'pageSetupChanged':False,'cellsOrFormatsChanged':False,'allPinnedBytesUnchanged':True,'afterHashes':pins,
    'historicalInventoryModified':False,'historicalArtifactHoldModified':False,'businessContentAuthored':False,
    'semanticApproval':False,'formalQualityApproval':False,'stateProjectionIncluded':False,'wholeDocumentApproval':False,
    'published':False,'originalApplicationExecuted':False}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTiles':114,'cells':len(r['cells'])},ensure_ascii=False))
