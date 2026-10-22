"""Layout contact sheets for local visual inspection, without changing artifacts."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
W=Path(__file__).resolve().parent;out=W/'contact';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
collections={'pdf':[{'path':str(p),'label':p.stem,'sha256':sha(p)} for p in sorted((W/'pdf-pages-final').glob('*.png'))], 'xlsx':[dict(x,label=x['sheet']+' '+x['range']) for x in json.loads((W/'workbook-build.json').read_bytes())['previews']]}
result={}
for kind,items in collections.items():
 result[kind]=[]
 for group in range(0,len(items),4):
  selected=items[group:group+4];canvas=Image.new('RGB',(1500,1800),'#dddddd');draw=ImageDraw.Draw(canvas)
  for j,item in enumerate(selected):
   im=Image.open(item['path']).convert('RGB');im.thumbnail((740,860));x=(j%2)*750+(750-im.width)//2;y=(j//2)*900+30
   canvas.paste(im,(x,y));draw.text(((j%2)*750+12,(j//2)*900+10),f'{group+j+1}: '+item['label'],fill='black')
  target=out/f'{kind}-{group//4+1:02}.png';canvas.save(target);result[kind].append({'path':str(target),'sha256':sha(target),'members':selected})
(W/'contact-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:len(v) for k,v in result.items()}))
