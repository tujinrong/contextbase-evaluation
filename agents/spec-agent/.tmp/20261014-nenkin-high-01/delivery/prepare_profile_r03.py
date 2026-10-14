"""Update generic format policy only; no workbook or business text."""
import hashlib
import json
from pathlib import Path
D=Path(__file__).parent
O=Path(r"D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01")
p=D/'format-profile-v2-62-r02.json';raw=p.read_bytes();profile=json.loads(raw)
assert profile['userExplicitlySpecified62'] is False
assert profile['tableException']['singleSheet'] is True
del profile['tableException']['singleSheet']
profile['tableException'].update(singleDeclaredContentSheet=True,formatterCoverAdditional=True,declaredContentColumns=9)
profile['preamble']={'normalFirst':'original route unchanged','listFirst':'literal original preamble in collision-safe normal62 sheet before declared chapters','table':'original preamble in declared TABLE9 content sheet; additional formatter cover'}
profile['printMetadataStatus']='CODE_AND_SYNTHETIC_SCOPE_ONLY_PASS; actual author receipt, workbook layout and print legibility pending'
profile['mechanicalModelCandidate']={'file':'delivery_model_v2_62_r05.py','sha256':'3db974859d83fa9d1987b94b310400b27d158ea5b8a851f99c3b297b76d1b6c9'}
assert profile['itemList']['columns']==10 and profile['generalList']['itemListOnly10'] is True
out=D/'format-profile-v2-62-r03.json'
with out.open('x',encoding='utf-8') as h:json.dump(profile,h,ensure_ascii=False,indent=2);h.write('\n')
assert p.read_bytes()==raw
record=O/'profile-r03-interpretation-and-preamble-proof.json'
result={'scope':'GENERIC_FORMAT_POLICY_ONLY','source':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()},'candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'userExplicitlySpecified62':False,'oldProfileUnchanged':True,'actualAuthoring':0,'businessReads':0}
with record.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'profile':str(out),'sha256':result['candidate']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
