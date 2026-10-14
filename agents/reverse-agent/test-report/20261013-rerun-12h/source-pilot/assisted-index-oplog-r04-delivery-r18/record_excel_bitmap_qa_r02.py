from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def safe(p):
 p=Path(p).absolute()
 for a in [p,*p.parents]:
  if a.exists() and (a.is_symlink() or getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
 return p.resolve()
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_text(encoding='utf-8-sig'))
before=load(R/'format-inventory-before.json');pins=dict(before['immutablePins'])
assert all(sha(p)==d for p,d in pins.items())
records=[];viewed=0
for name in ['index','oplog']:
 invpath=R/f'excel-bitmap-{name}-tiles-r01/inventory.json';resultpath=R/f'excel-bitmap-{name}-r01/result.json';planpath=R/f'excel-bitmap-plan-{name}.json';iv=load(invpath);result=load(resultpath);plan=load(planpath)
 assert result['readOnly'] is True and result['saved'] is False and result['pageSetupChanged'] is False and result['cellsOrFormatsChanged'] is False and result['originalApplicationExecuted'] is False
 assert result['macrosDisabled'] is True and result['updateLinks']==0 and result['workbookBytesUnchanged'] is True and result['planBytesUnchanged'] is True
 assert sha(result['workbook'])==result['beforeSha256']==result['afterSha256']==plan['workbookSha256'];assert sha(planpath)==result['planSha256']
 assert len(result['cells'])==len(plan['cells']) and all((a['sheet'],a['cell'])==(b['sheet'],b['cell']) and (a['value2']==b['value'] or (b['value']=='' and a['value2'] is None)) for a,b in zip(result['cells'],plan['cells']))
 assert len(result['sheets'])==len(plan['previews']) and all((a['sheet'],a['range'])==(b['sheet'],b['range']) for a,b in zip(result['sheets'],plan['previews']))
 pins[str(invpath)]=sha(invpath);pins[str(resultpath)]=sha(resultpath);pins[str(planpath)]=sha(planpath)
 entries=iv['documents'][0]['captures'];groups={}
 for i,e in enumerate(entries):
  assert e['pixelsEqualToOriginalRegion'] is True and e['scale']==1
  assert sha(e['path'])==e['sha256'] and sha(e['originalPath'])==e['originalSha256'];rect=e['sourceRectangle'];box=(rect['x'],rect['y'],rect['x']+rect['width'],rect['y']+rect['height'])
  with Image.open(safe(e['originalPath'])) as original,Image.open(safe(e['path'])) as tile:
   assert list(original.size)==e['wholeOriginalSize'] and tile.size==(rect['width'],rect['height']);assert original.convert('RGBA').crop(box).tobytes()==tile.convert('RGBA').tobytes()
  groups.setdefault(e['originalPath'],(e['wholeOriginalSize'],[]))[1].append(box)
  pins[e['path']]=e['sha256'];pins[e['originalPath']]=e['originalSha256'];viewed+=1
 for size,boxes in groups.values():
  mask=Image.new('L',tuple(size),0);draw=ImageDraw.Draw(mask)
  for x0,y0,x1,y1 in boxes:
   assert 0<=x0<x1<=size[0] and 0<=y0<y1<=size[1];draw.rectangle((x0,y0,x1-1,y1-1),fill=255)
  assert mask.getextrema()==(255,255)
 records.append({'documentId':iv['documents'][0]['documentId'],'workbook':result['workbook'],'workbookSha256':result['beforeSha256'],'markdownSha256':iv['documents'][0]['markdownSha256'],'result':str(resultpath),'resultSha256':sha(resultpath),'plan':str(planpath),'planSha256':sha(planpath),'tileInventory':str(invpath),'tileInventorySha256':sha(invpath),'actualPreviewCount':len(result['sheets']),'actualTileCount':len(entries),'Value2LiteralCount':len(result['cells']),'allNonblankValue2LiteralsExact':True,'blankValue2EmptyEquivalenceCount':sum(b['value']=='' and a['value2'] is None for a,b in zip(result['cells'],plan['cells'])),'allRgbaBytesExact':True,'allPreviewPixelsCovered':True,'ownedExcelQuitComplete':True,'captures':[dict(e,actuallyViewed=True,actuallyViewedBy='/root/source_pilot',actualViewMethod='tools.view_image detail original',captureIndexZeroBased=i) for i,e in enumerate(entries)],'geometryStatus':'PASS_READONLY_EXCEL_GEOMETRY_ONLY' if name=='index' else 'HOLD_READONLY_EXCEL_HEADER_GEOMETRY'})
assert viewed==85 and sum(d['actualPreviewCount'] for d in records)==46 and sum(d['Value2LiteralCount'] for d in records)==996
crop=R/'excel-bitmap-oplog-header-inspection-r01.png';assert crop.exists();pins[str(crop)]=sha(crop)
assert all(sha(p)==d for p,d in pins.items())
report={'schema':'readonly-excel-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':'training-assisted derived delivery','reviewer':'/root/source_pilot','referenceMode':'training-assisted','status':'HOLD_READONLY_EXCEL_HEADER_GEOMETRY','actuallyViewedTiles':85,'actuallyViewedRanges':46,'actualViewMethod':'Personally viewed all 85 exact lossless tiles with tools.view_image detail original in this agent turn. Header detail additionally inspected as one lossless crop, not counted as an extra complete image.','documents':records,'findings':[{'documentId':records[1]['documentId'],'sheet':'t_operation_log','cell':'E54','literal':'NOT NULL','previewIndexOneBased':4,'range':'A42:I57','globalTileIndexOneBased':83,'description':'Header NOT/NULL wraps to two lines; lower NULL is partly hidden by the header border and AutoFilter button.','severity':'DISPLAY_HOLD','crop':str(crop),'cropSha256':sha(crop),'cropSourceTile':records[1]['captures'][3]['path'],'cropSourceRectangle':{'x':325,'y':820,'width':150,'height':70}}],'resolvedOnThisSurface':[{'documentId':records[0]['documentId'],'items':['class_id/category_id whole identifiers','05_t_operation_log.md filename','supplement attribution before following heading']},{'documentId':records[1]['documentId'],'items':['Saved','writeStarted','Unknown whole identifiers']}],'allInputBeforeAfterPinsUnchanged':True,'beforeAfterPins':pins,'artifactPreviewOldHoldPreserved':True,'sourceOnlyBaseline':'CLOSED','canonicalContentAuthoredOrModified':False,'applicationExecuted':False,'workbookSavedOrModified':False,'formalQualityApproval':False,'adoptionApproval':False,'published':False,'limitations':['Value2 exact for 966 nonblank cells. Thirty expected empty-string cells return None; explicitly treated as blank equivalence, not raw type equality.','Geometry inspection of actual static Excel bitmap surface only; no source/ref/rubric/score/body authoring or business-semantic review.','Wide row ranges and figures continue over adjacent bitmap ranges; lossless tiles and labelled ranges preserve all captured pixels.','ReadOnly Excel uses owned CopyPicture and temporary clipboard write; no previous clipboard content read.','This report does not claim PDF or Artifact surface approval and does not replace old HOLD evidence.']}
out=R/'excel-bitmap-native-review-r02.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':report['status'],'ranges':46,'tiles':85,'literals':996,'sha256':sha(out)}))
