"""Preserve every native asset in PDF view, including non-inline small layouts."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent;O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'pdf_projection_r02.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='660e8f5731d14c5415d43b4ebf3a750e81bcbc6df5082778403d7af56375fbe1'
text=raw.decode().replace('\r\n','\n')
text=text.replace('def native_tiles(pictures):','def native_tiles(pictures,inline_hashes=()):',1)
text=text.replace("        if source.width<=CONTENT_WIDTH_PX and source.height<=CONTENT_HEIGHT_PX:continue","        if picture['sha256'] in inline_hashes and source.width<=CONTENT_WIDTH_PX and source.height<=CONTENT_HEIGHT_PX:continue",1)
old="    annex,tiles=native_tiles(pictures)"
new="""    required=Counter(p['sha256'] for p in pictures if p.get('kind')=='diagram')
    actual=Counter(parser.imageHashes)
    require(all(actual[value]>=count for value,count in required.items()),'canonical inline diagram multiplicity mismatch')
    annex,tiles=native_tiles(pictures,parser.imageHashes)"""
assert text.count(old)==1;text=text.replace(old,new)
old="'nativeTiles':[{k:v for k,v in r.items() if k!='bytes'} for r in tiles]}"
new="'nativeTiles':[{k:v for k,v in r.items() if k!='bytes'} for r in tiles],'nativeAssetIdsRetained':[p['id'] for p in pictures],'canonicalInlineNativeImageCount':len(parser.imageHashes),'allNativeAssetsEitherInlineOrAnnexed':True}"
assert text.count(old)==1;text=text.replace(old,new)
ast.parse(text);out=D/'pdf_projection_r03.py'
with out.open('xb') as h:h.write(text.encode())
assert p.read_bytes()==raw
driver=D/'export_pdf_bound_r03.py';draw=driver.read_bytes();assert hashlib.sha256(draw).hexdigest()=='88540ccd8cc70cf81ea5d7dd6c52a0ec871254e5feaa59141f531af0dd4f35f6'
dt=draw.decode().replace('\r\n','\n').replace('from pdf_projection_r02 import','from pdf_projection_r03 import',1)
dt=dt.replace('stdout=subprocess.PIPE,env=env)','stdout=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name==\'nt\' else 0)',1)
ast.parse(dt);dout=D/'export_pdf_bound_r04.py'
with dout.open('xb') as h:h.write(dt.encode())
assert driver.read_bytes()==draw
result={'scope':'FULL_NATIVE_ASSET_PDF_VIEW_PREPARATION','projection':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'driver':{'path':str(dout),'sha256':hashlib.sha256(dout.read_bytes()).hexdigest()},'changes':['small non-inline native layouts get pixel-only annex','canonical inline graph multiplicity checked','hidden owned worker console flag'],'actualPdfCreated':0,'browserStarted':0,'status':'PENDING_INDEPENDENT_SYNTHETIC_DELTA','oldCandidatesPreserved':True}
record=O/'pdf-projection-r03-driver-r04-preparation.json'
with record.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'projectionSha256':result['projection']['sha256'],'driverSha256':result['driver']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
