"""Pure metadata guard strengthening; no stage/swap functions are invoked."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent;O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'publication_bound_r01.py';raw=p.read_bytes();text=raw.decode().replace('\r\n','\n')
needle="    require(Path(value).as_posix()==value,'relative spelling changed');return Path(value)"
replacement="    require(not any(part.split('.')[0].casefold() in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]} for part in value.split('/')),'Windows reserved device segment')\n"+needle
assert text.count(needle)==1;text=text.replace(needle,replacement)
helper="""
def descriptor_shape(record):
    require(isinstance(record,dict) and set(record)=={'path','sha256'},'exact file descriptor required')
    require(isinstance(record.get('path'),str),'descriptor text path')
    require(isinstance(record.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',record['sha256']) is not None,'64lower SHA pin required')
    return safe(record['path'])

"""
text=text.replace('\ndef validate(',helper+'\ndef validate(',1)
needle="    files=[];ids=set();targets=set()"
replacement="""    approved=grant.get('approvedDocumentIds')
    require(isinstance(approved,list) and approved and all(isinstance(i,str) and i for i in approved) and len(approved)==len(set(approved)),'root-approved exact document set required')
    protected_roots=[safe(v['root']) for v in plan.get('protectedInventories',[])]
    files=[];ids=set();targets=set()"""
assert text.count(needle)==1;text=text.replace(needle,replacement)
needle="        cp=relative(doc['canonicalDocumentPath']);require(cp.suffix=='.md','canonical MD suffix');require(doc.get('documentId') not in ids,'duplicate document ID');ids.add(doc['documentId'])"
replacement="        require(isinstance(doc.get('documentId'),str) and doc['documentId'],'explicit document ID required')\n"+needle+"\n        require(doc.get('category')!='analysis-report','report-only document is not a published specification')"
assert text.count(needle)==1;text=text.replace(needle,replacement)
text=text.replace("source=safe(item['source']['path']);require(within(source,(WORK,REPORT)),'artifact outside this new run')","source=descriptor_shape(item['source']);require(within(source,(WORK,REPORT)),'artifact outside this new run')\n            require(not any(source.is_relative_to(root) for root in protected_roots),'protected original/capsule source cannot be a generated artifact')",1)
needle="    index=plan.get('index');"
assert text.count(needle)==1;text=text.replace(needle,"    require(ids==set(approved),'published documents differ from root-approved exact set')\n"+needle,1)
needle="    require(safe(index['source']['path']).is_relative_to(WORK),'root index source must be new WORK');require(safe(index['source']['path']).suffix=='.md','root index Markdown required')"
replacement="""    index_source=descriptor_shape(index['source'])
    require(index_source.is_relative_to(WORK),'root index source must be new WORK');require(index_source.suffix=='.md','root index Markdown required')
    require(not any(p.casefold() in DENIED for p in index_source.relative_to(WORK).parts[:-1]),'root index must not be a raw answer/report/analysis file')
    require(not any(index_source.is_relative_to(root) for root in protected_roots),'root index cannot come from protected source')"""
assert text.count(needle)==1;text=text.replace(needle,replacement)
needle="        root=safe(item['root'])\n        if item['role']=='original-input'"
assert text.count(needle)==1;text=text.replace(needle,"        descriptor_shape(item['inventory'])\n"+needle,1)
ast.parse(text);out=D/'publication_bound_r02.py'
with out.open('xb') as h:h.write(text.encode())
assert p.read_bytes()==raw
record={'scope':'PUBLICATION_METADATA_GUARD_PREPARATION_ONLY','source':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()},'candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'changes':['descriptor exact fields/SHA before staging','source-capsule/original-input cannot be selected artifacts','report-only category and index-answer/report path exclusion','dynamic root-approved document ID set, no61 hardcode','Windows device segment refusal'],'actualStage':0,'actualSwap':0,'actualOutputReads':0,'actualSourceReads':0,'status':'PENDING_INDEPENDENT_PROBES'}
report=O/'publication-r02-preparation.json'
with report.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'candidate':str(out),'sha256':record['candidate']['sha256'],'receiptSha256':hashlib.sha256(report.read_bytes()).hexdigest()}))
