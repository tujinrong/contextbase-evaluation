"""Fresh pure validation guards; source/output HTML literals remain insertion-only."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent;O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'pdf_projection_r01.py';raw=p.read_bytes();text=raw.decode().replace('\r\n','\n')
text=text.replace('import base64,hashlib,io,math,re','import base64,hashlib,io,math,re\nfrom collections import Counter',1)
old="    missing=[v for v in expected if normalize(v) not in normalize(extracted)]\n    return {'expectedCount':len(expected),'missing':missing,'missingCount':len(missing),'normalization':'WHITESPACE_ONLY','visualQualified':False}\n"
new="""    normalized=normalize(extracted);counts=Counter(normalize(v) for v in expected)
    missing=[v for v in expected if normalize(v) not in normalized]
    multiplicity=[{'normalizedLiteral':v,'expectedMinimum':count,'observedNonoverlappingOccurrences':normalized.count(v)} for v,count in counts.items() if normalized.count(v)<count]
    return {'expectedCount':len(expected),'missing':missing,'missingCount':len(missing),'multiplicityFailures':multiplicity,'normalization':'WHITESPACE_ONLY','visualQualified':False}

def canonical_text_order(extracted,strings):
    normalized=''.join(extracted.split());cursor=0;missing=[]
    for ordinal,value in enumerate(strings):
        value=''.join(value.split())
        if not value:continue
        found=normalized.find(value,cursor)
        if found<0:missing.append({'canonicalDomOrdinal':ordinal,'literal':value})
        else:cursor=found+len(value)
    return {'orderedStringsChecked':len(strings),'orderFailures':missing,'visualQualified':False,'limitation':'Normalized text sequence is a conservative extraction check; it does not prove visual cell alignment.'}
"""
assert text.count(old)==1;text=text.replace(old,new)
ast.parse(text);out=D/'pdf_projection_r02.py'
with out.open('xb') as h:h.write(text.encode())
assert p.read_bytes()==raw
driver=D/'export_pdf_bound_r02.py';draw=driver.read_bytes();dt=draw.decode().replace('\r\n','\n')
dt=dt.replace('from pdf_projection_r01 import project_html,text_coverage,GEOMETRY_JS,CONTENT_WIDTH_PX','from pdf_projection_r02 import project_html,text_coverage,canonical_text_order,GEOMETRY_JS,CONTENT_WIDTH_PX',1)
dt=dt.replace("coverage.update(canonicalDomStrings=len(canonical_strings),missingCanonicalStrings=missing,canonicalDomIncludesRawMermaidCode=True)","coverage.update(canonicalDomStrings=len(canonical_strings),missingCanonicalStrings=missing,canonicalDomIncludesRawMermaidCode=True,canonicalTextOrder=canonical_text_order(extracted,canonical_strings))",1)
dt=dt.replace("require(not coverage['missing'] and not missing,'PDF incomplete literal text')","require(not coverage['missing'] and not coverage['multiplicityFailures'] and not missing and not coverage['canonicalTextOrder']['orderFailures'],'PDF incomplete or reordered literal text')",1)
ast.parse(dt);dout=D/'export_pdf_bound_r03.py'
with dout.open('xb') as h:h.write(dt.encode())
assert driver.read_bytes()==draw
receipt={'scope':'PURE_LITERAL_TEXT_VALIDATION_PREPARATION','projection':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'driver':{'path':str(dout),'sha256':hashlib.sha256(dout.read_bytes()).hexdigest()},'sourceProjectionSha256':hashlib.sha256(raw).hexdigest(),'sourceDriverSha256':hashlib.sha256(draw).hexdigest(),'sourceTextOrHtmlModified':False,'newAssertions':['minimum duplicate occurrence checks','monotonic canonical DOM text extraction order, including raw Mermaid code'],'actualPdfCreated':0,'actualWriterOrBrowserStarted':0,'status':'PENDING_INDEPENDENT_SYNTHETIC_CHECKS','limitation':'Conservative ordered extraction can HOLD a visually reordered CSS layout. It must not be silently weakened or treated as formal quality.'}
record=O/'pdf-projection-r02-driver-r03-preparation.json'
with record.open('x',encoding='utf-8') as h:json.dump(receipt,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'projectionSha256':receipt['projection']['sha256'],'driverSha256':receipt['driver']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
