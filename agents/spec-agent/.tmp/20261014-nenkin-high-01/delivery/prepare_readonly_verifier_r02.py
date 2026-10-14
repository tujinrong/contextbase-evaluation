"""Reject nonfinite width metadata; preserve unqualified r01 candidate."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent
O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'verify_xlsx_v2_62_r01.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='888ec69cb905ae56a4d82666f5137c8e2549d250571b7daafdf2920986836f2d'
text=raw.decode('utf-8').replace('\r\n','\n').replace('import hashlib, io, json, posixpath, re, zipfile','import hashlib, io, json, math, posixpath, re, zipfile')
old="if len(candidates)!=1 or abs(float(candidates[0].get('width','nan'))-3)>0.0001:"
new="if len(candidates)!=1 or not math.isfinite(float(candidates[0].get('width','nan'))) or abs(float(candidates[0].get('width','nan'))-3)>0.0001:"
assert text.count(old)==1;text=text.replace(old,new)
old_loop="    for _,_,sheet in sheets:\n        # Workbook sheet visibility is checked in its original binding element below.\n        pass\n"
assert text.count(old_loop)==1;text=text.replace(old_loop,'')
ast.parse(text);out=D/'verify_xlsx_v2_62_r02.py'
with out.open('xb') as h:h.write(text.encode())
assert p.read_bytes()==raw
receipt={'scope':'READONLY_VERIFIER_FINITE_WIDTH_PREPARATION','sourceSha256':hashlib.sha256(raw).hexdigest(),'candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'actualAuthoring':0,'actualXlsxReads':0,'status':'PREPARED_NOT_YET_SYNTHETICALLY_REVIEWED','reason':'A NaN width must not pass a numerical difference check.'}
record=O/'readonly-verifier-preparation-r02.json'
with record.open('x',encoding='utf-8') as h:json.dump(receipt,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(out),'sha256':receipt['candidate']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
