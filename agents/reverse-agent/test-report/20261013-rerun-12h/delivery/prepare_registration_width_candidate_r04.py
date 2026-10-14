"""Prepare a J-column-only projection and records for actual completed views."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'model-assisted-screens-r18-r02.json';assert sha(p)=='08bc77b7d6a2005f9f39f27d663f5a9373bafa615618f677383f3959d459fa2a'
m=json.loads(p.read_text(encoding='utf8'));old=next(d for d in m['documents'] if d['documentId']=='CSHARP_ASPNET-BAS-STU-02');d=copy.deepcopy(old)
s=next(s for s in d['sheets'] if s['name']=='学生登録_項目');assert s['columnWidths'][9]==44;s['columnWidths'][9]=160
restored=copy.deepcopy(d);next(s for s in restored['sheets'] if s['name']=='学生登録_項目')['columnWidths'][9]=44;assert restored==old
m['documents']=[d];out=H/'model-assisted-registration-r18-r04-widthonly.json';assert not out.exists();out.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rp=H/'registration-columnwidth-probe-r02-excel/result.json';r=json.loads(rp.read_text(encoding='utf8'));assert r['workbookBytesUnchanged'] and not r['saved'] and not r['cellsOrFormatsChanged']
assert len(r['sheets'])==20 and len(r['cells'])==20
pins={str(p):sha(p),str(rp):sha(rp),r['workbook']:r['beforeSha256'],r['plan']:r['planSha256']};views=[]
for i,item in enumerate(r['sheets']):
 pins[item['png']]=item['pngSha256'];views.append({**item,'actuallyViewedBy':'delivery_tools','view':'original pixels','captureIndexZeroBased':i})
assert all(sha(path)==value for path,value in pins.items())
report={'schema':'reverse-agent-column-geometry-projection/2','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'UNCHANGED_LITERAL_MULTI_CELL_COLUMN_WIDTH_ONLY_PROBE','sourceModel':str(p),'sourceModelSha256':sha(p),'candidateModel':str(out),'candidateModelSha256':sha(out),'documentId':d['documentId'],'markdownSha256':d['markdownSha256'],'change':{'sheet':'学生登録_項目','column':'J','before':44,'after':160},'restoringOnlyThisWidthExactlyEqualsOriginalDocumentModel':True,'allValuesImagesRowsStylesOrderUnchanged':True,'actualExcelViews':views,'findings':[{'width':60,'cell':'J47','token':'EV-REG-006','status':'HOLD_IDENTIFIER_WRAP'},{'width':100,'cell':'J44','token':'16-16','status':'HOLD_HYPHENATED_CITATION_WRAP'},{'width':160,'cells':['J41','J44','J45','J46','J47'],'status':'PASS_FOCAL_GEOMETRY_ONLY'},{'width':255,'cells':['J41','J44','J45','J46','J47'],'status':'PASS_FOCAL_GEOMETRY_ONLY'}],'selectedWidthReason':'160 is the smallest tested width preserving all five focal identifiers and citation ranges on complete visible rows.','beforeAfterPins':pins,'clipboardTemporaryWriteSideEffect':True,'workbookSavedByExcel':False,'fullCandidateNativeReview':'PENDING','oldHoldsPreserved':True,'wholeApproval':False,'published':False,'businessContentAuthored':False}
record=H/'registration-columnwidth-probe-r02-actual-review.json';assert not record.exists();record.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
template=H/'prepare_registration_width_readback_r03_v3.py';dest=H/'prepare_registration_width_readback_r04.py';assert not dest.exists()
code=template.read_text(encoding='utf8');assert code.count("float(w['width'])-float(v['width'])==16")==1
code=code.replace('r18-r03-widthonly','r18-r04-widthonly').replace("float(w['width'])-float(v['width'])==16","float(w['width'])-float(v['width'])==116")
dest.write_text(code,encoding='utf8')
print(json.dumps({'model':str(out),'sha256':sha(out),'probeReview':str(record),'probeReviewSha256':sha(record),'readbackHelper':str(dest),'readbackHelperSha256':sha(dest)},ensure_ascii=False))
