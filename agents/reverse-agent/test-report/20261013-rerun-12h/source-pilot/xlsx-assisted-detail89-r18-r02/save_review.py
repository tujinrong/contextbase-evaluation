"""Record this agent's completed visual observations; no artifact transformation."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((HERE/'inventory-before.json').read_text(encoding='utf-8'))
after=json.loads((HERE/'inventory-after.json').read_text(encoding='utf-8'))
assert before['pins']==after['pins'] and len(before['captures'])==89
def captures(indices):
    return [{k:c[k] for k in ('viewIndex','sheet','range','path','sha256','originalPath','originalSha256','sourceRectangle','wholeOriginalSize')} for c in before['captures'] if c['viewIndex'] in indices]
findings=[
 {'id':'XLSX-GEO-01','severity':'important','sheet':'03_選択候補一覧','range':'A1:G9','cells':['F7','B8','D3','E8'],
  'observed':'Cell F7 displays the numeric value 20 as 2 then 0 on separate lines. B8 studentNo, D3 code_value, and E8 admissionDate also break inside the identifier.',
  'effect':'Atomic numeric and ASCII values are visually fragmented inside the original cell; this is not a crop-boundary effect.',
  'evidence':captures([20])},
 {'id':'XLSX-GEO-02','severity':'important','sheet':'02_項目一覧','range':'A12:J20','cells':['J12'],
  'observed':'The source line ranges 120-122 and 149-149 wrap as 120-12 / 2 and 149-14 / 9. Source type and file identifiers also wrap inside words in this explanation column.',
  'effect':'Source reference numbers and ASCII identifiers require joining separate lines while reading.',
  'evidence':captures([11,15])},
 {'id':'XLSX-GEO-03','severity':'important','sheet':'04_内部項目一覧','range':'A1:F12','cells':['B6','D7','D9','E12','F2'],
  'observed':'Atomic values break inside cells: B6 string, D7 Options, D9 NULL, E12 totalCount, and the numeric source range 9-13 in F2.',
  'effect':'The table preserves visible columns, but ordinary type/state tokens and numeric references are fragmented.',
  'evidence':captures([21])},
 {'id':'XLSX-GEO-04','severity':'important','sheet':'06_項目移送仕様','range':'A1:F13','cells':['D2','E2','D3','D4','E6','D10','E10','D13'],
  'observed':'Within-cell line wrapping splits string[], ModelState, Search, StudentNameKana, EnrollmentStatusCodes, DateOnly, Criteria, studentID and studentNo.',
  'effect':'The transfer table has all six columns, but values and identifiers are split inside complete tokens.',
  'evidence':captures([79])}
]
visual_log=[]
for c in before['captures']:
    visual_log.append({**{k:c[k] for k in ('viewIndex','sheet','range','path','sha256','sourceRectangle','originalPreviewIndex')},
                       'actuallyViewedBy':'/root/source_pilot','viewMethod':'tools.view_image(detail=original) followed by image(detail=original)',
                       'nativeScale':1,'actualViewCompleted':True})
review={'schema':'own-native-xlsx-visual-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'subject':'training-assisted delivery','scope':'SELECTED_DETAIL_NATIVE_GEOMETRY_ONLY','status':'HOLD',
 'documentId':before['documentId'],'workbook':before['workbook'],'workbookSha256':before['workbookSha256'],
 'markdownSha256':before['markdownSha256'],'sourceSnapshotManifestSha256':before['sourceSnapshotManifestSha256'],
 'beforeInventory':str(HERE/'inventory-before.json'),'beforeInventorySha256':sha(HERE/'inventory-before.json'),
 'afterInventory':str(HERE/'inventory-after.json'),'afterInventorySha256':sha(HERE/'inventory-after.json'),
 'immutablePinsCount':len(before['pins']),'beforeAfterPinsEqual':True,'originalPreviewCount':47,
 'actualOwnNativeTileViews':89,'distinctActualOwnNativeTileViews':89,'fullPixelCoverageRechecked':True,
 'all89ExactRGBARechecked':True,'opaqueRGBDifferenceNegativeRejected':True,
 'nativeGeometryApproved':False,'findings':findings,'actualViewLog':visual_log,
 'otherObservations':[
  'Text remains readable at native scale. No missing table columns, unreadably small font, or hidden values was observed.',
  'Viewed event diagrams preserve readable labels and traceable connections; no diagram label-edge overlap was observed in this selected delivery.',
  'Some diagrams cross preview row-range partitions. Adjacent row ranges continue them; this is capture partitioning and not demonstrated workbook clipping.',
  'Several LIST rows have generous blank cell height. This was not treated as missing body text.',
  'All right-hand tiles, including blank portions, were actually displayed. Wide-image tile boundaries were distinguished from within-cell wrapping.'
 ],
 'sourceOnlyBaseline':'CLOSED','originalWorkbookModelHtmlMarkdownImagesChanged':0,
 'applicationOrProviderRuns':0,'semanticApproval':False,'formalApproval':False,
 'limitations':['This review covers the renderer-produced native PNGs and selected immutable delivery bindings, not a live Microsoft Excel session.',
                'No original design, evaluation rubric, expected answers, score, or grading answer was read.',
                'This is a display geometry finding, not a semantic completeness or application behavior determination.']}
out=HERE/'review.json'
if out.exists():raise FileExistsError('Fresh report required')
out.write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':review['status'],'actualOwnNativeTileViews':89,'findings':len(findings)},ensure_ascii=False))
