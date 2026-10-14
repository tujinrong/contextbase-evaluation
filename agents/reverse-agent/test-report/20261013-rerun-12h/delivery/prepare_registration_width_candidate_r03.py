"""Column geometry projection; every source operation/table/image remains unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'model-assisted-screens-r18-r02.json';oldsha='08bc77b7d6a2005f9f39f27d663f5a9373bafa615618f677383f3959d459fa2a'
assert sha(p)==oldsha
m=json.loads(p.read_text(encoding='utf8'));old=next(d for d in m['documents'] if d['documentId']=='CSHARP_ASPNET-BAS-STU-02')
d=copy.deepcopy(old);s=next(s for s in d['sheets'] if s['name']=='学生登録_項目');assert s['columnWidths'][9]==44;s['columnWidths'][9]=60
restored=copy.deepcopy(d);next(s for s in restored['sheets'] if s['name']=='学生登録_項目')['columnWidths'][9]=44
assert restored==old
m['documents']=[d];out=H/'model-assisted-registration-r18-r03-widthonly.json';assert not out.exists()
out.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
record=H/'registration-columnwidth-probe-r01-excel/result.json'
r=json.loads(record.read_text(encoding='utf8'));assert r['status']=='STATIC_EXCEL_BITMAP_EXPORTED_VISUAL_REVIEW_PENDING' and r['workbookBytesUnchanged'] is True
assets={str(p):oldsha,str(record):sha(record)}
views=[]
for width,item in zip([44,60,80,100],r['sheets']):
 assert item['sheet']=='Width'+str(width)
 assets[item['png']]=item['pngSha256'];views.append({'width':width,'path':item['png'],'sha256':item['pngSha256'],'actuallyViewedBy':'delivery_tools','view':'original pixels','wholeIdentifier':width!=44})
assert all(sha(Path(p))==h for p,h in assets.items())
report={'schema':'reverse-agent-column-geometry-projection/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'ONE_UNCHANGED_LITERAL_COLUMN_WIDTH_ONLY_PROBE','sourceModel':str(p),'sourceModelSha256':oldsha,
 'candidateModel':str(out),'candidateModelSha256':sha(out),'documentId':d['documentId'],'markdownSha256':d['markdownSha256'],
 'change':{'sheet':'学生登録_項目','column':'J','before':44,'after':60},'restoringOnlyThisWidthExactlyEqualsOriginalDocumentModel':True,
 'allValuesImagesRowsStylesOrderUnchanged':True,'actualExcelViews':views,'beforeAfterPins':assets,
 'clipboardTemporaryWriteSideEffect':True,'workbookSavedByExcel':False,'cellFormattingChangedByExcel':False,
 'existingArtifactAndExcelHoldsPreserved':True,'fullCandidateNativeReview':'PENDING','wholeApproval':False,'published':False,'businessContentAuthored':False}
rp=H/'registration-columnwidth-probe-r01-actual-review.json';assert not rp.exists();rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':str(out),'sha256':sha(out),'probeRecord':str(rp),'probeSha256':sha(rp)}))
