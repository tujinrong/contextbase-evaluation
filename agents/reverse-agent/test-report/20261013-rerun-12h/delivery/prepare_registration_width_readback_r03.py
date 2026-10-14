"""Read-only semantic XML comparison and full-range bitmap plan."""
from pathlib import Path
import hashlib,json,zipfile,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
oldp=H/'xlsx-assisted-screens-r18-r02/delivery-manifest.json';newp=H/'xlsx-assisted-registration-r18-r03-widthonly/delivery-manifest.json'
oldm=json.loads(oldp.read_text(encoding='utf8'));newm=json.loads(newp.read_text(encoding='utf8'));old=next(d for d in oldm['documents'] if d['documentId']=='CSHARP_ASPNET-BAS-STU-02');new=newm['documents'][0]
assert new['writtenCells']==old['writtenCells'] and new['requestedPrintAreas']==old['requestedPrintAreas']
assert [(p['sheet'],p['range']) for p in new['previews']]==[(p['sheet'],p['range']) for p in old['previews']]
assert new['independentCellVerification']=='PASS' and sha(Path(new['xlsx']))==new['xlsxSha256'] and sha(Path(old['xlsx']))==old['xlsxSha256']
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def members(p):
 with zipfile.ZipFile(p) as z:return {n:z.read(n) for n in z.namelist()}
a=members(old['xlsx']);b=members(new['xlsx']);assert set(a)==set(b)
changes=[]
for name in sorted(a):
 if a[name]==b[name]:continue
 if name.endswith(('.xml','.rels')):
  x=E.fromstring(a[name]);y=E.fromstring(b[name])
  if name=='xl/worksheets/sheet3.xml':
   xc=x.find(S+'cols');yc=y.find(S+'cols');assert xc is not None and yc is not None
   oldwidths=[dict(c.attrib) for c in xc];newwidths=[dict(c.attrib) for c in yc]
   x.remove(xc);y.remove(yc)
   assert E.tostring(x)==E.tostring(y),'Non-width worksheet change'
   changes.append({'part':name,'scope':'COLUMN_WIDTH_ONLY','beforeColumns':oldwidths,'afterColumns':newwidths})
  elif name.startswith('docProps/'):
   changes.append({'part':name,'scope':'EXPORT_DOCUMENT_PROPERTIES'})
  else:
   assert E.tostring(x)==E.tostring(y),'Other semantic XML changed: '+name
   changes.append({'part':name,'scope':'XML_SERIALIZATION_ONLY'})
 else:raise AssertionError('Binary content changed: '+name)
assert any(c['scope']=='COLUMN_WIDTH_ONLY' for c in changes)
plan={'workbook':new['xlsx'],'workbookSha256':new['xlsxSha256'],'manifest':str(newp),'sheets':new['readbackChecks']['sheetCount'] and [r['sheet'] for r in new['requestedPrintAreas']],
 'cells':[{'sheet':c['sheet'],'cell':c['cell'],'value':c['value']} for c in new['writtenCells']],
 'previews':[{'sheet':p['sheet'],'range':p['range']} for p in new['previews']],
 'documentId':new['documentId'],'canonicalDocumentPath':new['canonicalDocumentPath'],'markdownSha256':new['markdownSha256']}
pp=H/'registration-xlsx-r18-r03-widthonly-excel-bitmap-plan.json';assert not pp.exists();pp.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rp=H/'registration-xlsx-r18-r03-widthonly-xml-delta.json';assert not rp.exists();rp.write_text(json.dumps({'scope':'COLUMN_WIDTH_ONLY_DERIVED_XLSX_READBACK','sourceXlsx':old['xlsx'],'sourceXlsxSha256':old['xlsxSha256'],'candidateXlsx':new['xlsx'],'candidateXlsxSha256':new['xlsxSha256'],'changes':changes,'allWrittenCellsRowsImagesBordersOrderUnchanged':True,'formulaCount':0,'previewRangeOrderUnchanged':True,'plan':str(pp),'planSha256':sha(pp),'actualFullRangeReview':'PENDING','oldHoldsPreserved':True,'published':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'xlsxSha256':new['xlsxSha256'],'plan':str(pp),'planSha256':sha(pp),'delta':str(rp),'deltaSha256':sha(rp),'changedParts':changes},ensure_ascii=False))
