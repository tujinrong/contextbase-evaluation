"""Record only the actually inspected layout overview and detailed changed views."""
import datetime,hashlib,json,re
from pathlib import Path
W=Path(__file__).resolve().parent;REV=W.parents[1];R=REV/'report'/W.name
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=read(W/'view-model.json');b=read(W/'workbook-build.json');n=read(W/'workbook-native-check.json');p=read(W/'pdf-html-check.json');contacts=read(W/'contact-manifest.json')
assert sha(m['markdown'])==m['markdownSha256']==p['markdownSha256']==read(R/'format-equivalence.json')['markdownSha256']
assert sha(n['path'])==n['sha256'] and n['artifactToolSourceSha256']==b['workbookSha256'] and n['unchangedExceptPrintMetadata']
assert sha(p['pdf'])==p['pdfSha256'] and sha(p['html'])==p['htmlSha256']
assert len(contacts['pdf'])==10 and len(contacts['xlsx'])==8 and len(b['previews'])==32
for items in contacts.values():
 for item in items:
  assert sha(item['path'])==item['sha256']
  for member in item['members']:assert sha(member['path'])==member['sha256']
assert len([x for s in contacts['pdf'] for x in s['members']])==p['pages']==37
detailPdf=[2,4,9,13,15,16,22,23]
detailXlsx=['sheet-2-002','sheet-4-001','sheet-4-004','sheet-4-006','sheet-4-013','sheet-4-015']
assert m['hierarchicalOrdinalProjection']['splitRows']==38
assert not any('根拠：' in op['value'] for s in m['sheets'] for op in s['operations'])
for s in m['sheets']:
 byrange={op['range']:op['value'] for op in s['operations']}
 for op in s['operations']:
  if re.fullmatch(r'\d+\.\d+\.',op['value']):
   row=re.search(r'\d+',op['range'])[0];assert op['range']==f'B{row}:D{row}' and byrange.get(f'E{row}:BJ{row}')
v={'schema':'scr014-format-visual-review/1','status':'PASS','scope':'visual format and readability only; not whole-document semantic approval','inspectedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'markdownSha256':m['markdownSha256'],'pdfSha256':p['pdfSha256'],'xlsxSha256':n['sha256'],'overview':contacts,'nativeSizeDetailPdf':[{'page':i,'path':str(W/'pdf-pages-final'/f'page-{i:02}.png'),'sha256':sha(W/'pdf-pages-final'/f'page-{i:02}.png')} for i in detailPdf],'nativeSizeDetailWorkbook':[{'path':str(W/'workbook-preview'/(name+'.png')),'sha256':sha(W/'workbook-preview'/(name+'.png'))} for name in detailXlsx],'checks':['24 citation paragraphs absent from deliverable prose','hierarchical parent labels and child numbers readable','38 child ordinals and descriptions share worksheet rows','no clipping or overlap in inspected format views','cover and LIST conventions preserved'],'knownSemanticIssues':1,'applicationOrDatabaseExecuted':False,'excelApplicationOrPhysicalPrintExecuted':False}
c=Path(m['canonicalDocumentPath']);v['deliveredHashes']={'md/'+c.as_posix():m['markdownSha256'],'html/'+c.with_suffix('.html').as_posix():p['htmlSha256'],'PDF/'+c.with_suffix('.pdf').as_posix():p['pdfSha256'],'Excel/'+c.with_suffix('.xlsx').as_posix():n['sha256']}
with (W/'visual-review.json').open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'PASS','pdfOverviewPages':37,'xlsxOverviewTiles':32,'detailPdfPages':len(detailPdf),'detailXlsxTiles':len(detailXlsx),'xlsxProjectedCells':n['literalCellsChecked']}))
