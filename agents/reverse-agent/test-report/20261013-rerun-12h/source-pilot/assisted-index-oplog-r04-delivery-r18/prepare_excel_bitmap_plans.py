"""Mechanically copy fixed metadata literals/ranges; canonical hash-only."""
import json,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
H=Path(__file__).absolute().parent
def safe(p):
 p=Path(os.path.abspath(p))
 for a in [p,*p.parents]:
  if a.is_symlink() or (a.exists() and getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path before read')
 return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_bytes())
manifest=H/'xlsx-r01/delivery-manifest.json';binding=H/'binding.json'
assert sha(binding)=='f35938dea33a2abec797c06ecee0039cb031193a1e616f7647918a841ccbe366'
docs=load(manifest)['documents'];bound={d['documentId']:d for d in load(binding)['documents']}
delivery=H.parents[1]/'delivery';ps=delivery/'excel_bitmap_readonly_r02.ps1';worker=delivery/'run_excel_bitmap_readonly_r02.py'
assert sha(ps)=='1a792f0ff92f803df0d749117b57f85c0892ea8d7a690a51fca88f234f0d815d'
pins={str(p):sha(p) for p in [manifest,binding,ps,worker]};plans=[]
for d in docs:
 b=bound[d['documentId']];assert d['markdownSha256']==b['markdownSha256'];assert sha(d['xlsx'])==d['xlsxSha256'];assert sha(b['markdown'])==b['markdownSha256']
 pins[d['xlsx']]=d['xlsxSha256'];pins[b['markdown']]=b['markdownSha256']
 cells=d['writtenCells']; previews=[{k:p[k] for k in ['sheet','range']} for p in d['previews']]
 sheets=list(dict.fromkeys(c['sheet'] for c in cells))
 p=H/('excel-bitmap-plan-index.json' if d['documentId']=='CSHARP_ASPNET-BAS-STU-03' else 'excel-bitmap-plan-oplog.json')
 assert not p.exists()
 data={'workbook':d['xlsx'],'workbookSha256':d['xlsxSha256'],'manifest':str(manifest),'manifestSha256':sha(manifest),'sheets':sheets,'cells':cells,'previews':previews,'documentId':d['documentId'],'markdownSha256':d['markdownSha256'],'canonicalDocumentPath':b['canonicalDocumentPath']}
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 plans.append({'plan':str(p),'planSha256':sha(p),'documentId':d['documentId'],'literalCount':len(cells),'previewCount':len(previews),'workbook':d['xlsx'],'workbookSha256':d['xlsxSha256']})
for p,v in pins.items():assert sha(p)==v
out=H/'excel-bitmap-plan-provenance.json';assert not out.exists();out.write_text(json.dumps({'createdUtc':datetime.now(timezone.utc).isoformat(),'plans':plans,'immutablePins':pins,'cellsAndRangeOrderCopiedExactly':True,'canonicalHashOnly':True,'semanticApproval':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'plans':plans,'provenanceSha256':sha(out)}))
