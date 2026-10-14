"""Mechanical helper preparation only; no document/body generation."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(p,data):
 assert not p.exists(),str(p)
 p.write_text(data,encoding='utf8')
base=(H/'record_registration_pdf_native_qa_r18_r01.py').read_text(encoding='utf8')
manifest=H/'pdf-assisted-code-design-r19-r01/delivery-manifest.json'
text=base.replace("'pdf-assisted-screens-r18-r01'","'pdf-assisted-code-design-r19-r01'").replace("'registration-pdf-r18-r01-actual-native-review.json'","'code-design-pdf-r19-r01-actual-native-review.json'")
text=text.replace('e9cf4a92d25aad8b07a23939c4627bcdef929bcdea2d375f8dbb455fefc7f7fc',sha(manifest)).replace('CSHARP_ASPNET-BAS-STU-02','CSHARP_ASPNET-BAS-STU-04').replace('d83202e77f68350875ceece7382d9b53c4f4c3e62fdd383e6c0ec6c1213c3540','6bf9190ff103a3f2cfd50b14e3e48c4a73cb48d1553fd5df087a81e7a8e7c700')
text=re.sub(r'\b92\b','48',text).replace('range(1,93)','range(1,49)')
start=text.index("    'notes':[");end=text.index("    'literalCoverageEvidence'",start)
text=text[:start]+"    'notes':[\n      {'pages':[2,3], 'finding':'Seed table and procedure continue across pages; repeated headers and complete visible rows remain legible.'},\n      {'pages':list(range(1,49)), 'finding':'Diagram/raw-Mermaid blocks use separate pages and substantial whitespace to preserve original image and text scale.'}\n    ],\n"+text[end:]
fresh(H/'record_code_design_pdf_native_qa_r19_r01.py',text)

base=(H/'render_assisted_code_r19.py').read_text(encoding='utf8')
case="""CASES={'registration-detail':{'root':'revision-registration-detail-r05','path':'詳細仕様書/CSharp_ASPNET/02_学生登録画面.md',
 'sha':'ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd',
 'id':'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002','job':'revision-registration-detail-r05',
 'destination':'assisted-registration-detail-r01-delivery-r19'}}
PIN=REPORT/'training-assisted/reviewed-registration-detail-r05-r11-pin.json'
PIN_SHA='016746beaab58be3a3ab2406b662c63c0df9cb4824cc929b87e701c6fc975bcb'
"""
a=base.index('CASES={');b=base.index('\ndef safe',a);text=base[:a]+case+base[b:]
text=text.replace("before={str(p):sha(p) for p in [RECEIPT,CAP_MANIFEST,source,draft,Path(__file__)]}","assert sha(PIN)==PIN_SHA\n pin=json.loads(PIN.read_text(encoding='utf8'))\n assert pin['sha256']==case['sha'] and pin['documentId']==case['id'] and pin['independentReviewApproved'] is True\n assert pin['capsule']['manifestSha256']==CAP_SHA and pin['capsule']['mode']=='training-assisted'\n approved=safe(Path(pin['independentReview']))\n assert sha(approved)==pin['independentReviewSha256'] and sha(draft)==pin['draftResultSha256']\n before={str(p):sha(p) for p in [RECEIPT,CAP_MANIFEST,PIN,approved,source,draft,Path(__file__)]}")
fresh(H/'render_assisted_registration_detail_r19_r01.py',text)

p=H/'model-assisted-screens-r18-r02.json'
assert sha(p)=='08bc77b7d6a2005f9f39f27d663f5a9373bafa615618f677383f3959d459fa2a'
m=json.loads(p.read_text(encoding='utf8'))
d=next(d for d in m['documents'] if d['documentId']=='CSHARP_ASPNET-BAS-STU-02')
s=next(s for s in d['sheets'] if s['name']=='学生登録_項目')
print(json.dumps({'model':str(p),'sha256':sha(p),'sheet':s['name'],'widths':s.get('columnWidths'),'columns':s['columns'],'J41':[o for o in s['operations'] if o['range'].startswith('J41:')],'sheets':len(d['sheets'])},ensure_ascii=False))
