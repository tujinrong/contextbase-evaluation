"""Read-only package comparison canonicalizes export-generated relationship IDs."""
from pathlib import Path
import hashlib,json,posixpath,zipfile,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
oldp=H/'xlsx-assisted-screens-r18-r02/delivery-manifest.json';newp=H/'xlsx-assisted-registration-r18-r03-widthonly/delivery-manifest.json'
oldm=json.loads(oldp.read_text(encoding='utf8'));newm=json.loads(newp.read_text(encoding='utf8'));old=next(d for d in oldm['documents'] if d['documentId']=='CSHARP_ASPNET-BAS-STU-02');new=newm['documents'][0]
assert new['writtenCells']==old['writtenCells'] and new['requestedPrintAreas']==old['requestedPrintAreas']
assert [(p['sheet'],p['range']) for p in new['previews']]==[(p['sheet'],p['range']) for p in old['previews']]
assert new['independentCellVerification']=='PASS' and sha(Path(new['xlsx']))==new['xlsxSha256'] and sha(Path(old['xlsx']))==old['xlsxSha256']
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}';R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
def members(p):
 with zipfile.ZipFile(p) as z:return {n:z.read(n) for n in z.namelist()}
a=members(old['xlsx']);b=members(new['xlsx']);assert set(a)==set(b)
maps={};relationship_records=[]
for name in sorted(a):
 if not name.endswith('.rels'):continue
 x=E.fromstring(a[name]);y=E.fromstring(b[name])
 key=lambda n:tuple(sorted((k,v) for k,v in n.attrib.items() if k!='Id'))
 xa={key(n):n.attrib['Id'] for n in x};ya={key(n):n.attrib['Id'] for n in y}
 assert len(xa)==len(list(x)) and len(ya)==len(list(y)) and xa.keys()==ya.keys(),'Relationship target/type change'
 mapping={ya[k]:xa[k] for k in xa};maps[name]=mapping
 relationship_records.append({'part':name,'targetsAndTypesUnchanged':True,'exportIdMapping':mapping})
def relpart(name):return posixpath.join(posixpath.dirname(name),'_rels',posixpath.basename(name)+'.rels')
changes=[]
for name in sorted(a):
 if a[name]==b[name]:continue
 if not name.endswith(('.xml','.rels')):raise AssertionError('Binary content changed: '+name)
 x=E.fromstring(a[name]);y=E.fromstring(b[name])
 mapping=maps.get(name if name.endswith('.rels') else relpart(name),{})
 for n in y.iter():
  for k,v in list(n.attrib.items()):
   if (name.endswith('.rels') and k=='Id') or (k.startswith(R) and k.rsplit('}',1)[-1] in {'id','embed','link'}):
    assert v in mapping,'Unmapped relationship reference';n.set(k,mapping[v])
 if name=='xl/worksheets/sheet3.xml':
  xc=x.find(S+'cols');yc=y.find(S+'cols');assert xc is not None and yc is not None
  xo=[dict(c.attrib) for c in xc];yo=[dict(c.attrib) for c in yc];assert len(xo)==len(yo)
  differences=[]
  for i,(v,w) in enumerate(zip(xo,yo)):
   if v==w:continue
   assert v['min']==w['min']=='10' and v['max']==w['max']=='10'
   without=lambda d:{k:z for k,z in d.items() if k!='width'}
   assert without(v)==without(w) and float(w['width'])-float(v['width'])==16
   differences.append({'column':'J','before':v,'after':w})
  assert len(differences)==1
  x.remove(xc);y.remove(yc);assert E.tostring(x)==E.tostring(y),'Non-width worksheet change'
  changes.append({'part':name,'scope':'COLUMN_WIDTH_ONLY','differences':differences})
 else:
  assert E.tostring(x)==E.tostring(y),'Other semantic XML changed: '+name
  changes.append({'part':name,'scope':'ONLY_EXPORT_RELATIONSHIP_IDS_OR_XML_SERIALIZATION'})
assert any(c['scope']=='COLUMN_WIDTH_ONLY' for c in changes)
plan={'workbook':new['xlsx'],'workbookSha256':new['xlsxSha256'],'manifest':str(newp),'sheets':[r['sheet'] for r in new['requestedPrintAreas']],
 'cells':[{'sheet':c['sheet'],'cell':c['cell'],'value':c['value']} for c in new['writtenCells']],
 'previews':[{'sheet':p['sheet'],'range':p['range']} for p in new['previews']],
 'documentId':new['documentId'],'canonicalDocumentPath':new['canonicalDocumentPath'],'markdownSha256':new['markdownSha256']}
pp=H/'registration-xlsx-r18-r03-widthonly-excel-bitmap-plan.json';assert not pp.exists();pp.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rp=H/'registration-xlsx-r18-r03-widthonly-xml-delta.json';assert not rp.exists();rp.write_text(json.dumps({'scope':'COLUMN_WIDTH_ONLY_DERIVED_XLSX_READBACK','sourceXlsx':old['xlsx'],'sourceXlsxSha256':old['xlsxSha256'],'candidateXlsx':new['xlsx'],'candidateXlsxSha256':new['xlsxSha256'],'changes':changes,'relationshipComparison':relationship_records,'allWrittenCellsRowsImagesBordersOrderUnchanged':True,'formulaCount':0,'previewRangeOrderUnchanged':True,'plan':str(pp),'planSha256':sha(pp),'actualFullRangeReview':'PENDING','oldHoldsPreserved':True,'published':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'xlsxSha256':new['xlsxSha256'],'plan':str(pp),'planSha256':sha(pp),'delta':str(rp),'deltaSha256':sha(rp),'changedPartCount':len(changes)},ensure_ascii=False))
