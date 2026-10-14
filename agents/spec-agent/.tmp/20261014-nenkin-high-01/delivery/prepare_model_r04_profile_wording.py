"""Mechanical generic profile metadata correction. No document/provider/authoring."""
import ast
import hashlib
import json
from pathlib import Path

D=Path(__file__).parent
O=Path(r"D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01")
source=D/"delivery_model_v2_62_r03.py"
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=="53e181a09ffed3869f21b6b51e1eb9a2ab115fe723919a7b71c9dee1d755d9e1"
text=raw.decode("utf-8")
old_comment="# User-selected V2 format profile. No change to Markdown/source content."
new_comment="# V2 preservation interpretation: 62 is inherited from the reference format, not a literal human numeric selection."
assert text.count(old_comment)==1
text=text.replace(old_comment,new_comment)
old_profile="'listHeaderRow':1,'literalStrings':True}"
new_profile="'listHeaderRow':1,'literalStrings':True,'selectionBasis':'INTERPRETATION_OF_REQUEST_TO_PRESERVE_EXISTING_V2_FORMAT','userExplicitlySpecified62':False,'referencePins':{'reverse-agent/AGENTS.md':'abe30d75507861a8aab24ed32bba1f572d7690a8d0ac71cda693263ff03e41a7','docsite/v2/reference_format.json':'fe6c22d0cfd3b06063541aa5fb4afa270f349a23a9ed931cfe5c948289bce3ee'}}"
assert text.count(old_profile)==1
text=text.replace(old_profile,new_profile)
a,b=ast.parse(raw),ast.parse(text)
fa={n.name:ast.dump(n,include_attributes=False) for n in a.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
fb={n.name:ast.dump(n,include_attributes=False) for n in b.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert fa==fb
reverse=text.replace(new_profile,old_profile).replace(new_comment,old_comment)
assert reverse.encode("utf-8")==raw
out=D/"delivery_model_v2_62_r04.py"
with out.open("xb") as h:h.write(text.encode("utf-8"))
assert source.read_bytes()==raw
receipt={"scope":"PROFILE_WORDING_AND_METADATA_ONLY","source":{"path":str(source),"sha256":hashlib.sha256(raw).hexdigest()},
 "candidate":{"path":str(out),"sha256":hashlib.sha256(out.read_bytes()).hexdigest()},
 "allFunctionAndClassAstUnchanged":True,"inverseRestoresSourceBytes":True,"userExplicitlySpecified62":False,
 "actualAuthoring":0,"inputBusinessReads":0,"providers":0,"modelParserExecuted":False,
 "limitations":["Historical r01/r02/r03 profile records remain unchanged.","Complete business text coverage and actual workbook appearance require later document-specific verification."]}
record=O/"model-r04-profile-wording-proof.json"
with record.open("x",encoding="utf-8") as h:json.dump(receipt,h,ensure_ascii=False,indent=2);h.write("\n")
print(json.dumps({"model":str(out),"sha256":receipt["candidate"]["sha256"],"receipt":str(record),"receiptSha256":hashlib.sha256(record.read_bytes()).hexdigest()}))
