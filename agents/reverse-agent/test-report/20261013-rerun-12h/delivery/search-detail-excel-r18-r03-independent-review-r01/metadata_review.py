import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
OWN=Path(__file__).resolve().parent
DEL=OWN.parent
INV=DEL/'excel-bitmap-search-detail-r18-r03-widthonly-tiles/inventory.json'
INV_SHA='c753a6159c9785214eab41ec7356a6ce933cc453b53d8b5d66a0232625a0e7ec'
XLSX_SHA='47cd77ca1ecf27b57cb31dd6b250beea158acc42df8a0149a35c2eedbf2d544e'
PREP=DEL/'search-detail-width-r03-preparation.json'
PREP_SHA='e75c0b6dc975810358e392ee76f59ddc3806bc435cd55070ac39386e7278e9f8'
ID='CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001'
REPO=Path(r'D:\開発\contextbase-evaluation')
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def norm(path):
 p=Path(path);return str((p if p.is_absolute() else REPO/p).resolve())
def check():
 assert sha(INV)==INV_SHA
 inventory=read(INV);d=inventory['documents'][0];captures=d['captures']
 assert d['documentId']==ID and d['xlsxSha256']==XLSX_SHA
 assert d['originalPreviewCount']==47 and len(captures)==89
 assert sha(PREP)==PREP_SHA
 prep=read(PREP)
 pins={norm(INV):INV_SHA,norm(PREP):PREP_SHA}
 def add(path,h):
  p=norm(path)
  if p in pins:assert pins[p]==h,'conflicting pin: '+p
  pins[p]=h
 for p,h in inventory['sourceBindings'].items():add(p,h)
 for p,h in prep['sourcePins'].items():add(p,h)
 for v in prep['files'].values():add(v['path'],v['sha256'])
 originals=set()
 for c in captures:
  assert c['scale']==1 and c['pixelsEqualToOriginalRegion'] is True
  add(c['path'],c['sha256']);add(c['originalPath'],c['originalSha256'])
  originals.add(c['originalPath'])
 assert len(originals)==47
 delta=DEL/'search-detail-xlsx-r18-r03-widthonly-xml-delta.json'
 assert sha(delta).startswith('1778e312')
 add(delta,sha(delta))
 bindingPath=DEL/'binding-assisted-screens-r18-r01.json'
 binding=read(bindingPath);add(bindingPath,sha(bindingPath))
 bd=next(v for v in binding['documents'] if v['documentId']==ID)
 assert bd['markdownSha256']==d['markdownSha256']
 add(bd['markdown'],bd['markdownSha256'])
 rd=Path(bd['renderDirectory'])
 add(rd/'render-pins.json',bd['renderPinsSha256']);add(rd/'manifest.json',bd['renderManifestSha256'])
 rp=read(rd/'render-pins.json')
 assert rp['rendererRuntimeLabel']=='r18' and rp['rendererRuntimeFileCount']==126
 runtimePath=Path(rp['rendererRuntimeReceipt'])
 add(runtimePath,rp['rendererRuntimeReceiptSha256'])
 runtime=read(runtimePath)
 assert runtime['fileCount']==126 and len(runtime['files'])==126
 for rel,h in runtime['files'].items():add(Path(runtime['destination'])/rel,h)
 for p,h in rp['inputPins'].items():add(p,h)
 holdPath=DEL/'search-detail-excel-bitmap-r18-r02-actual-native-review.json'
 hold=read(holdPath)
 holdSHA='869a7d0cb0e049a7ca0b3c97a6e00055fb1a836772527c8c6b98d552dcb5838f'
 add(holdPath,holdSHA)
 assert hold['status']=='HOLD_ACTUAL_EXCEL_INTERNAL_IDENTIFIER_WRAP'
 planPath=DEL/'search-detail-xlsx-r18-r03-widthonly-excel-bitmap-plan.json'
 plan=read(planPath)
 manifestPath=Path(plan['manifest'])
 add(manifestPath,plan['manifestSha256'])
 manifest=read(manifestPath)
 assert manifest['bindingSha256']==sha(bindingPath) and manifest['modelSha256']==prep['files']['candidateModel']['sha256']
 resultPath=DEL/'excel-bitmap-search-detail-r18-r03-widthonly/result.json'
 result=read(resultPath)
 assert result['readOnly'] and result['macrosDisabled'] and result['updateLinks']==0 and not result['saved']
 assert not result['cellsOrFormatsChanged'] and not result['pageSetupChanged']
 assert result['beforeSha256']==result['afterSha256']==XLSX_SHA
 expected={(v['sheet'],v['cell']):v['value'] for v in plan['cells']}
 actual={(v['sheet'],v['cell']):v for v in result['cells']}
 assert len(expected)==len(actual)==1242 and expected.keys()==actual.keys()
 blankCount=literalCount=0
 for key,v in expected.items():
  a=actual[key]
  if v in ('',None):
   blankCount+=1;assert a['value2'] in ('',None) and a['text'] in ('',None),'blank mismatch'
  else:
   literalCount+=1;assert a['value2']==v and a['text']==v,'literal mismatch'
 assert literalCount==1240 and blankCount==2
 for p,h in pins.items():assert sha(p)==h,'SHA mismatch: '+p
 for c in captures:
  r=c['sourceRectangle']
  with Image.open(c['originalPath']) as orig,Image.open(c['path']) as tile:
   assert list(orig.size)==c['wholeOriginalSize']
   crop=orig.convert('RGBA').crop((r['x'],r['y'],r['x']+r['width'],r['y']+r['height']))
   actualTile=tile.convert('RGBA')
   assert crop.size==actualTile.size and crop.tobytes()==actualTile.tobytes(),'RGBA mismatch'
 return d,captures,pins,{'binding':norm(bindingPath),'bindingSha256':sha(bindingPath),'markdown':norm(bd['markdown']),'markdownSha256':bd['markdownSha256'],'renderPins':norm(rd/'render-pins.json'),'renderPinsSha256':bd['renderPinsSha256'],'renderManifest':norm(rd/'manifest.json'),'renderManifestSha256':bd['renderManifestSha256'],'runtimeReceipt':norm(runtimePath),'runtimeReceiptSha256':rp['rendererRuntimeReceiptSha256'],'frozenRuntime':runtime['destination'],'frozenRuntimeFiles':126,'rendererImports':runtime.get('renderImports'),'widthDelta':norm(delta),'widthDeltaSha256':sha(delta),'manifest':norm(manifestPath),'manifestSha256':sha(manifestPath),'historicalActualHold':norm(holdPath),'historicalActualHoldSha256':holdSHA,'historicalActualHoldStatus':hold['status']},{'coordinatesChecked':1242,'nonemptyValue2Exact':1240,'nonemptyTextExact':1240,'blankCoordinates':2,'blankEquivalence':True,'mismatches':0,'cellLiteralsPrinted':False,'source':'Fresh owned COM result cells versus pinned expected plan cells; no new COM execution.'}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',required=True,choices=['before','after']);a=parser.parse_args()
 target=OWN/('metadata-'+a.phase+'.json');assert not target.exists(),'immutable receipt'
 d,c,p,b,l=check()
 receipt={'schema':'independent-search-detail-excel-bitmap-metadata-hash/1','createdUtc':datetime.now(timezone.utc).isoformat(),'phase':a.phase,'status':'PASS_PINS_LITERAL_BLANK_AND_EXACT_RGBA','inventory':str(INV),'inventorySha256':INV_SHA,'documentId':d['documentId'],'canonicalDocumentPath':d['canonicalDocumentPath'],'xlsx':d['xlsx'],'xlsxSha256':XLSX_SHA,'markdownSha256':d['markdownSha256'],'originalCount':47,'tileCount':89,'exactRgbaComparisons':89,'checkedFiles':len(p),'pins':p,'captures':c,'bindings':b,'literalComparison':l,'sourceMarkdownBodyRead':False,'businessSourceRead':False,'semanticAssessment':False,'formalScoring':False,'wholeApproval':False,'adoption':False,'publication':False,'applicationExecuted':False}
 if a.phase=='after':
  before=read(OWN/'metadata-before.json')
  assert before['pins']==p and before['captures']==c and before['bindings']==b and before['literalComparison']==l
 target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 compact={k:v for k,v in receipt.items() if k not in ['pins','captures']}
 compact['receiptSha256']=sha(target)
 print(json.dumps(compact,ensure_ascii=False,separators=(',',':')))
if __name__=='__main__':main()

