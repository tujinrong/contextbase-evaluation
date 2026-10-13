"""Print allowed raw source lines and preserve exact read boundaries, no execution."""
from pathlib import Path
import json,hashlib,sys
from datetime import datetime,timezone
ROOT=Path(r'D:\開発\contextbase-evaluation').resolve()
CAP=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
REPORT=Path(__file__).resolve().parent
name=sys.argv[1]
records=[]
for arg in sys.argv[2:]:
    rel,start,end=arg.rsplit(':',2);start=int(start);end=int(end)
    p=(CAP/rel).resolve()
    assert p.is_relative_to(CAP/'sources')
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    lines=p.read_text(encoding='utf-8-sig').splitlines()
    assert 1<=start<=end<=len(lines)
    print(rel)
    for i in range(start,end+1):print(f'{i}: {lines[i-1]}')
    after=hashlib.sha256(p.read_bytes()).hexdigest();assert before==after
    records.append({'path':rel,'startLine':start,'endLine':end,'sha256':before,'beforeAfterMatch':True})
with (REPORT/name).open('x',encoding='utf-8',newline='\n') as f:
    json.dump({'schema':'reverse-independent-raw-source-read-boundaries/1','readAt':datetime.now(timezone.utc).isoformat(),'round':6,'phase':'SOURCE_PREPARATION','references':records,'sourceProgramExecuted':False,'generatedDocumentAssessed':False},f,ensure_ascii=False,indent=2);f.write('\n')
