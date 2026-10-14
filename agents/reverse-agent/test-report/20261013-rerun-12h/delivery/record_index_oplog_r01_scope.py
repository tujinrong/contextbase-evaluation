"""Record actually viewed native failure and experimental scope, without rewriting evidence."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 inventory_path=ROOT/'native-assisted-table-index-r01/inventory.json';native=read(inventory_path)
 records=[]
 for item in native['captures']:
  assert digest(item['path'])==item['sha256'] and digest(item['originalPath'])==item['originalSha256']
  records.append({**item,'actuallyReviewed':True,'review':'FAIL' if item['imageId'] in {'diagram-005','diagram-008','diagram-011'} else 'NO_LATIN_IDENTIFIER_SPLIT_OBSERVED','scope':'original-size pixel geometry only'})
 write(ROOT/'index-oplog-r01-native-failure.json',{'schema':'reverse-agent-native-readability-failure/1','createdUtc':datetime.now(timezone.utc).isoformat(),'inventory':str(inventory_path),'inventorySha256':digest(inventory_path),'referenceMode':'training-assisted','sourceMarkdownSha256':native['documentSha256'],'rendererRevision':'frozen-assisted06-r14','all19Diagram27TilesActuallyViewed':True,'images':records,'status':'FAIL','findings':[{'image':'diagram-005','token':'ArgumentException','actualRows':['ArgumentExceptio','n']},{'image':'diagram-008','token':'ArgumentException','actualRows':['ArgumentExcept','ion']},{'image':'diagram-011','token':'ArgumentException','actualRows':['ArgumentEx','ception']}],'otherObservedJapaneseContinuations':['diagram-003 未確認','diagram-004 不一致','diagram-007 不一致','diagram-011 不一致'],'originalMarkdownModified':False,'published':False,'formalQualityGatePassed':False})
 probe_path=ROOT/'mermaid-edge-width-probe-r01/probe.json';probe=read(probe_path);viewed=[]
 selected={('synthetic','baseline'),('synthetic','edgeFont12'),('synthetic','derivedExplicitBreaks'),('own-index005','baseline'),('own-index005','width640'),('own-index005','edgeFont12'),('own-index005','derivedExplicitBreaks')}
 for item in probe['results']:
  assert digest(item['png'])==item['pngSha256'] and digest(item['svg'])==item['svgSha256']
  if (item['case'],item['variant']) in selected:viewed.append({'case':item['case'],'variant':item['variant'],'png':item['png'],'pngSha256':item['pngSha256'],'actuallyViewed':True,'geometryVerdict':'IDENTIFIERS_INTACT_NO_OVERLAP_OBSERVED' if item['variant']=='derivedExplicitBreaks' else 'IDENTIFIER_MID_WRAP_REPRODUCED'})
 write(ROOT/'mermaid-edge-width-probe-r01/actually-viewed.json',{'schema':'trusted-mermaid-native-probe-review/1','probe':str(probe_path),'probeSha256':digest(probe_path),'totalCases':12,'actuallyViewedCount':len(viewed),'images':viewed,'remaining5Cases':'mechanical config/rows/signatures inspected; image pixels not viewed','publicConfigOnlyRemedyFound':False,'fixtureOnlyDerivedBreakReadable':True,'productionFormatterImplemented':False,'mainOrDependencyDirectoryEdited':False,'published':False})
 files=['binding-assisted-index-oplog-r01.json','model-assisted-index-oplog-r01.json','html-assisted-index-oplog-r01/qa.json','pdf-assisted-index-oplog-r01/delivery-manifest.json','xlsx-assisted-index-oplog-r01/delivery-manifest.json','index-oplog-r01-native-failure.json']
 pdf=read(ROOT/files[3]);xlsx=read(ROOT/files[4]);html=read(ROOT/files[2])
 write(ROOT/'index-oplog-r01-partial-status.json',{'schema':'reverse-agent-delivery-partial-status/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'INDEX_NATIVE_FAIL_REMEDY_INVESTIGATION','referenceMode':'training-assisted','frozenRendererRevision':'assisted06-r14','formalQualityGatePassed':False,'published':False,'originalMarkdownOrReferenceEdited':False,'specOrSpecEvalRead':False,'mainRendererReadOrEdited':False,'artifactToolAuthoringMarkerReexecuted':False,'inputsUnchanged':html['allInputsUnchanged'],'frozenRuntime124Unchanged':html['frozenRuntime124FilesUnchanged'],'artifacts':[{'path':str(ROOT/n),'sha256':digest(ROOT/n)} for n in files],'mechanical':['PDF immutable canonical HTML and visible source strings PASS','XLSX literal cells/no formulas/sheet order/embedded PNG hashes/print areas/strict borders PASS'],'currentActualImageScope':{'indexOriginalDiagramTiles':27,'htmlDocumentCrops':0,'pdfPages':0,'xlsxPreviews':0},'generatedPendingImageScope':{'htmlCrops':sum(len(d['crops']) for d in html['documents']),'pdfPages':sum(len(d['pageImages']) for d in pdf['documents']),'xlsxPreviews':sum(len(d['previews']) for d in xlsx['documents'])},'pending':['Index152PDFpages inspection paused by root because original diagrams already fail','Operation-log native full HTML/PDF/XLSX QA remains pending','Generic edge layout fix must use fresh renderer and fresh candidates; old failures preserved']})
 print(json.dumps({'partialStatus':str(ROOT/'index-oplog-r01-partial-status.json'),'sha256':digest(ROOT/'index-oplog-r01-partial-status.json')},ensure_ascii=False))
if __name__=='__main__':main()
