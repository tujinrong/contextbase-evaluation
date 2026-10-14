from pathlib import Path
import json,hashlib,copy,zipfile,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
def safe(p):
 p=Path(p).absolute()
 for a in [p,*p.parents]:
  if a.exists() and (a.is_symlink() or getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
 return p.resolve()
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_text(encoding='utf-8-sig'))
pins=dict(load(R/'format-inventory-before.json')['immutablePins'])
assert all(sha(p)==h for p,h in pins.items())
ivp=R/'excel-bitmap-oplog-columnE12-tiles-r02/inventory.json';iv=load(ivp);doc=iv['documents'][0]
rp=R/'excel-bitmap-oplog-columnE12-r02/result.json';result=load(rp)
pp=R/'excel-bitmap-plan-oplog-columnE12-r02.json';plan=load(pp)
mp=R/'model-oplog-columnE12-r02.json';model=load(mp);oldmodel=load(R/'model-r01.json')
old=next(d for d in oldmodel['documents'] if d['documentId']==doc['documentId']);new=model['documents'][0]
assert len(model['documents'])==1 and new['documentId']=='CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG'
assert new['markdownSha256']==doc['markdownSha256']=='7067c165e324756fb909048d2f3c6735ed3824bb6512c66155015ba6c5703b48'
assert sha(new['markdown'])==new['markdownSha256']
restored=copy.deepcopy(new);assert restored['sheets'][0]['columnWidths'][4]==12
assert old['sheets'][0]['columnWidths'][4]==8;restored['sheets'][0]['columnWidths'][4]=8;assert restored==old
assert result['readOnly'] is True and result['saved'] is False and result['pageSetupChanged'] is False and result['cellsOrFormatsChanged'] is False and result['originalApplicationExecuted'] is False
assert result['macrosDisabled'] is True and result['updateLinks']==0 and result['workbookBytesUnchanged'] is True and result['planBytesUnchanged'] is True and result['baselineExcelProcessIds']==[]
assert sha(result['workbook'])==result['beforeSha256']==result['afterSha256']==plan['workbookSha256']=='03421eba02119d55c7e59f1d89546058aaf7aeb26badb23b95a8c5532a11c0f5'
assert sha(pp)==result['planSha256']=='0306f0ec86b8e65c33224ed099b9b02d72bcd5a6bd58db0fa8a4917019547c38'
assert len(result['cells'])==len(plan['cells'])==213
assert all((a['sheet'],a['cell'])==(b['sheet'],b['cell']) and (a['value2']==b['value'] or (b['value']=='' and a['value2'] is None)) for a,b in zip(result['cells'],plan['cells']))
assert sum(b['value']!='' for b in plan['cells'])==183
assert sum(b['value']=='' and a['value2'] is None for a,b in zip(result['cells'],plan['cells']))==30
assert len(result['sheets'])==len(plan['previews'])==6
assert all((a['sheet'],a['range'])==(b['sheet'],b['range']) for a,b in zip(result['sheets'],plan['previews']))
for p in [ivp,rp,pp,mp,R/'columnE12-model-delta-r02.json',R/'columnE12-xml-delta-inspection-r02.json',R/'excel-bitmap-native-review-r02.json']:
 pins[str(p)]=sha(p)
assert sha(ivp)=='84d0001b06d0d693c78c77f1fe757cd21c94507806c1dc1fdc3513e4b389b52c'
entries=doc['captures'];assert len(entries)==6;groups={}
for i,e in enumerate(entries):
 assert e['originalPreviewIndex']==i and e['pixelsEqualToOriginalRegion'] is True and e['scale']==1
 assert sha(e['path'])==e['sha256'] and sha(e['originalPath'])==e['originalSha256']
 rect=e['sourceRectangle'];box=(rect['x'],rect['y'],rect['x']+rect['width'],rect['y']+rect['height'])
 with Image.open(safe(e['originalPath'])) as original,Image.open(safe(e['path'])) as tile:
  assert list(original.size)==e['wholeOriginalSize'] and tile.size==(rect['width'],rect['height'])
  assert original.convert('RGBA').crop(box).tobytes()==tile.convert('RGBA').tobytes()
 groups.setdefault(e['originalPath'],(e['wholeOriginalSize'],[]))[1].append(box)
 pins[e['path']]=e['sha256'];pins[e['originalPath']]=e['originalSha256']
for size,boxes in groups.values():
 mask=Image.new('L',tuple(size),0);draw=ImageDraw.Draw(mask)
 for x0,y0,x1,y1 in boxes:
  assert 0<=x0<x1<=size[0] and 0<=y0<y1<=size[1];draw.rectangle((x0,y0,x1-1,y1-1),fill=255)
 assert mask.getextrema()==(255,255)
assert len(groups)==6
negativeA=Image.new('RGBA',(1,1),(255,255,255,255));negativeB=Image.new('RGBA',(1,1),(0,0,0,255));assert negativeA.tobytes()!=negativeB.tobytes()
oldxlsx=R/'xlsx-r01/Excel/基本設計書/テーブル/05_t_operation_log.xlsx';newxlsx=Path(result['workbook'])
relationshipMap=[];tableNameMap=[];widthChanges=0
with zipfile.ZipFile(safe(oldxlsx)) as a,zipfile.ZipFile(safe(newxlsx)) as b:
 assert set(a.namelist())==set(b.namelist())
 for n in a.namelist():
  aa=a.read(n);bb=b.read(n)
  if n.endswith('.rels'):
   ar=ET.fromstring(aa);br=ET.fromstring(bb)
   assert len(ar)==len(br)
   for x,y in zip(ar,br):
    assert {k:v for k,v in x.attrib.items() if k!='Id'}=={k:v for k,v in y.attrib.items() if k!='Id'}
    relationshipMap.append({'part':n,'oldId':x.get('Id'),'newId':y.get('Id'),'target':y.get('Target'),'type':y.get('Type')})
mapping={e['oldId']:e['newId'] for e in relationshipMap}
with zipfile.ZipFile(safe(oldxlsx)) as a,zipfile.ZipFile(safe(newxlsx)) as b:
 for n in a.namelist():
  x=ET.fromstring(a.read(n));y=ET.fromstring(b.read(n))
  for el in x.iter():
   if el.tag.rsplit('}',1)[-1]=='Relationship':el.set('Id',mapping[el.get('Id')])
   for k in list(el.attrib):
    if k=='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id':el.set(k,mapping[el.get(k)])
   if n=='xl/worksheets/sheet1.xml' and el.tag.rsplit('}',1)[-1]=='col' and el.get('min')=='5' and el.get('max')=='5':
    assert el.get('width')=='8';el.set('width','12');widthChanges+=1
   if n=='xl/tables/table1.xml' and el.tag.rsplit('}',1)[-1]=='table':
    assert el.get('name')==el.get('displayName')=='Rows1_0_0';assert y.get('name')==y.get('displayName')=='Rows0_0_0'
    tableNameMap.append({'old':'Rows1_0_0','new':'Rows0_0_0','reason':'Exporter document ordinal changed from selected second document to sole document.'});el.set('name','Rows0_0_0');el.set('displayName','Rows0_0_0')
  assert ET.tostring(x)==ET.tostring(y),n
  assert not any(el.tag.rsplit('}',1)[-1]=='f' for el in y.iter())
assert widthChanges==1 and len(tableNameMap)==1
pins[str(newxlsx)]=sha(newxlsx);assert all(sha(p)==h for p,h in pins.items())
report={'schema':'readonly-excel-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':'training-assisted derived delivery','reviewer':'/root/source_pilot','referenceMode':'training-assisted','status':'PASS_READONLY_EXCEL_GEOMETRY_ONLY','sourceOnlyBaseline':'CLOSED','documentId':doc['documentId'],'canonicalDocumentPath':new['canonicalDocumentPath'],'markdownSha256':new['markdownSha256'],'sourceSnapshotManifestSha256':model['sourceSnapshotManifestSha256'],'workbook':str(newxlsx),'workbookSha256':sha(newxlsx),'model':str(mp),'modelSha256':sha(mp),'plan':str(pp),'planSha256':sha(pp),'result':str(rp),'resultSha256':sha(rp),'tileInventory':str(ivp),'tileInventorySha256':sha(ivp),'actuallyViewedRanges':6,'actuallyViewedTiles':6,'actualViewMethod':'Personally viewed all six exact lossless images with tools.view_image detail original in this agent turn. No old view count is reused.','captures':[dict(e,actuallyViewed=True,actuallyViewedBy='/root/source_pilot',actualViewMethod='tools.view_image detail original',captureIndexZeroBased=i) for i,e in enumerate(entries)],'findings':[],'resolvedPriorFinding':{'sheet':'t_operation_log','cell':'E54','literal':'NOT NULL','previewIndexOneBased':4,'description':'The header is now displayed on one line with all letters visible above the lower border and clear of the AutoFilter button.','oldHoldReport':str(R/'excel-bitmap-native-review-r02.json'),'oldHoldReportSha256':sha(R/'excel-bitmap-native-review-r02.json')},'allSelectedModelDataExceptOneColumnWidthExact':True,'widthChange':{'sheet':'t_operation_log','column':'E','old':8,'new':12},'xmlLogicalDelta':{'onlyDisplayedFormattingDelta':'column E width 8 to 12','relationshipIdentifiers':relationshipMap,'generatedTableNameChange':tableNameMap,'allOtherXmlStructureTextAndAttributesExact':True,'allFormulaElementsAbsent':True},'Value2LiteralCount':213,'nonblankValue2Count':183,'allNonblankValue2LiteralsExact':True,'blankValue2EmptyEquivalenceCount':30,'allRgbaBytesExact':True,'opaqueDifferentColorNegativeRejected':True,'allPreviewPixelsCovered':True,'ownedExcelQuitComplete':True,'allInputBeforeAfterPinsUnchanged':True,'beforeAfterPins':pins,'oldHoldAndArtifactsPreserved':True,'canonicalContentAuthoredOrModified':False,'applicationExecuted':False,'workbookSavedOrModified':False,'formalQualityApproval':False,'adoptionApproval':False,'published':False,'limitations':['Static ReadOnly Excel bitmap geometry only. No business/source/reference/rubric/score evaluation.','Thirty expected empty-string cells return None, explicitly treated as blank equivalence rather than raw type equality.','Generated relationship IDs and the technical table name changed with fresh single-document export; targets, table structure, cell order and formulas absence are verified.','This record does not approve the old Artifact preview surface, PDF, or formal adoption.']}
out=R/'excel-bitmap-oplog-columnE12-native-review-r02.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'ranges':6,'tiles':6,'nonblankLiterals':183,'blankEquivalent':30,'sha256':sha(out),'resultSha256':sha(rp)}))
