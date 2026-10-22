"""Bind completed human-visible AI inspection to exact artifact bytes."""
import datetime, hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=read(W/'view-model.json'); n=read(W/'workbook-native-check.json'); p=read(W/'pdf-html-check.json'); b=read(W/'workbook-build.json'); r=read(W/'pdf-render-receipt.json'); h=read(W/'jobs/review-03/review-handoff.json')
assert sha(m['markdown'])==m['markdownSha256']==h['documentSha256']==p['markdownSha256'] and h['approved']
assert sha(W/'jobs/review-03/review-verified.json')==h['reviewSha256']
assert sha(n['path'])==n['sha256'] and n['unchangedExceptPrintMetadata']
assert b['workbookSha256']==n['artifactToolSourceSha256']
assert sha(p['pdf'])==p['pdfSha256']==r['pdfSha256'] and sha(p['html'])==p['htmlSha256']
assert len(b['previews'])==32 and r['pageCount']==36
for x in b['previews']: assert sha(x['path'])==x['sha256']
pages=[]
for i in range(1,37):
 f=W/'pdf-pages-v6'/f'page-{i:02}.png'; pages.append({'page':i,'path':str(f),'sha256':sha(f),'status':'PASS'})
canonical=Path(m['canonicalDocumentPath'])
v={'schema':'scr014-visual-review/1','status':'PASS','inspectedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'markdownSha256':m['markdownSha256'],'reviewer':'root AI visual inspection','pdf':{'sha256':p['pdfSha256'],'dpi':96,'pages':pages,'checks':['no clipped text or image content','table readability and column boundaries','diagram labels and edges','headings accompany figures']},'workbook':{'sha256':n['sha256'],'artifactToolRenderedSha256':b['workbookSha256'],'printMetadataOnlyBridgeVerified':True,'tiles':[dict(x,status='PASS') for x in b['previews']],'checks':['cover 14 merged frames','NORMAL 62-column geometry','LIST 10 columns with title row 1 and header row 2','cell wrapping and sufficient row height','image positions and readable diagram labels']},'sourceImagesInspected':15,'limitations':['Workbook visualization uses Artifact Tool; Microsoft Excel application rendering and physical printing were not executed.','PDF pages inspected at 96 dpi; source diagrams also inspected separately.','Application and DB runtime, formal original-rubric scoring were not executed.'],'deliveredHashes':{'md/'+canonical.as_posix():m['markdownSha256'],'html/'+canonical.with_suffix('.html').as_posix():p['htmlSha256'],'PDF/'+canonical.with_suffix('.pdf').as_posix():p['pdfSha256'],'Excel/'+canonical.with_suffix('.xlsx').as_posix():n['sha256']}}
with (W/'visual-review.json').open('x',encoding='utf8') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':v['status'],'pdfPages':len(pages),'workbookTiles':len(b['previews']),'markdownSha256':m['markdownSha256']}))
