"""Fix HTMLParser public callback bookkeeping name collision, preserving old code."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent;O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'pdf_projection_r03.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='1f97920494cade5b41f6047607c495662b3dc965368529b4040ef69ba60b66d5'
text=raw.decode().replace('\r\n','\n');assert text.count('def offset(self):')==1 and text.count('self.offset()')==2
text=text.replace('def offset(self):','def source_offset(self):').replace('self.offset()','self.source_offset()');ast.parse(text)
out=D/'pdf_projection_r04.py'
with out.open('xb') as h:h.write(text.encode())
assert p.read_bytes()==raw
d=D/'export_pdf_bound_r04.py';dr=d.read_bytes();assert hashlib.sha256(dr).hexdigest()=='91d10a2ffaf523febaa2e3acb5be125a2d0682339aa173dfebbf1d20a0fa7642'
dt=dr.decode().replace('\r\n','\n').replace('from pdf_projection_r03 import','from pdf_projection_r04 import',1);ast.parse(dt);dout=D/'export_pdf_bound_r05.py'
with dout.open('xb') as h:h.write(dt.encode())
assert d.read_bytes()==dr
result={'scope':'HTMLPARSER_CALLBACK_NAME_REPAIR_ONLY','projection':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'driver':{'path':str(dout),'sha256':hashlib.sha256(dout.read_bytes()).hexdigest()},'observedPriorFailure':'HTMLParser.offset is an integer; helper method collision caused TypeError at valid outer head close.','oldCandidatesPreserved':True,'actualPdfCreated':0,'actualBrowserStarted':0,'status':'PENDING_INDEPENDENT_SYNTHETIC_RERUN'}
record=O/'pdf-projection-r04-driver-r05-preparation.json'
with record.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'projectionSha256':result['projection']['sha256'],'driverSha256':result['driver']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
