"""Exact RGBA bytes, avoiding alpha-only getbbox semantics in the earlier exploratory check."""
from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
from PIL import Image,ImageChops

PARENT=Path(__file__).resolve().parent.parent
rows=[]
for version in ('r01','r02','r03'):
 root=PARENT/('table-css-prototype-'+version)
 for width in (1440,800):
  a=root/f'baseline-{width}/embedded.png';b=root/f'candidate-{width}/embedded.png'
  with Image.open(a) as ia,Image.open(b) as ib:
   ra=ia.convert('RGBA');rb=ib.convert('RGBA')
   row={'version':version,'viewport':width,'baseline':str(a),'candidate':str(b),
     'baselinePngSha256':hashlib.sha256(a.read_bytes()).hexdigest(),
     'candidatePngSha256':hashlib.sha256(b.read_bytes()).hexdigest(),
     'sameSize':ra.size==rb.size,'sameExactRgbaPixels':ra.tobytes()==rb.tobytes(),
     'pixelSha256':hashlib.sha256(ra.tobytes()).hexdigest(),'size':ra.size}
   if not(row['sameSize'] and row['sameExactRgbaPixels']):raise ValueError('Embedded layout pixels changed')
   rows.append(row)
red=Image.new('RGBA',(1,1),(255,0,0,255));blue=Image.new('RGBA',(1,1),(0,0,255,255))
negative={'differentOpaqueRgbRejectedByExactBytes':red.tobytes()!=blue.tobytes(),
          'previousRgbaGetbboxWouldMissRgbDifference':ImageChops.difference(red,blue).getbbox() is None}
if not negative['differentOpaqueRgbRejectedByExactBytes']:raise ValueError('Exact pixel negative failed')
result={'schema':'embedded-exact-pixel-recheck/1','createdAt':datetime.now(timezone.utc).isoformat(),
 'scope':'SYNTHETIC_EMBEDDED_LAYOUT_PIXEL_ONLY','allPass':True,'comparisons':rows,'negative':negative,
 'oldResultsPreserved':True,'applicationExecuted':False,'mainCodeModified':False,
 'correction':'Earlier RGBA difference getbbox checked alpha by default; exact RGBA-byte equality is now independently confirmed.'}
out=Path(__file__).resolve().parent/'embedded-exact-pixel-recheck-r01.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'result':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'allPass':True,'cases':len(rows)},ensure_ascii=False))
