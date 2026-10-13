"""Read only manifest-authorized design ranges; separate from source observations."""
from pathlib import Path
import json,hashlib,sys
from datetime import datetime,timezone
ROOT=Path(r'D:\開発\contextbase-evaluation').resolve()
CAP=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
REPORT=Path(__file__).resolve().parent
manifest=json.loads((CAP/'manifest.json').read_text(encoding='utf-8-sig'))
assert manifest['trainingReferenceAuthorizedByUser'] is True
allowed={x['path']:x for x in manifest['referenceFiles']}
assert len(allowed)==11
records=[]
for arg in sys.argv[2:]:
    rel,start,end=arg.rsplit(':',2);start=int(start);end=int(end)
    assert rel in allowed and allowed[rel]['basis']=='user-authorized-training-reference'
    p=(CAP/rel).resolve();assert p.is_relative_to(CAP/'reference-designs')
    before=hashlib.sha256(p.read_bytes()).hexdigest();assert before==allowed[rel]['sha256']
    lines=p.read_text(encoding='utf-8-sig').splitlines();assert 1<=start<=end<=len(lines)
    print(rel)
    for i in range(start,end+1):print(f'{i}: {lines[i-1]}')
    after=hashlib.sha256(p.read_bytes()).hexdigest();assert before==after
    records.append({'path':rel,'startLine':start,'endLine':end,'sha256':before,'beforeAfterMatch':True,'basis':'user-authorized-training-reference'})
with (REPORT/sys.argv[1]).open('x',encoding='utf-8',newline='\n') as f:
    json.dump({'schema':'reverse-independent-authorized-design-read-boundaries/1','readAt':datetime.now(timezone.utc).isoformat(),'round':6,'phase':'REFERENCE_INTENT_PREPARATION','scope':'Design intention only; distinct from observed current source behavior; new generated document comparison not yet performed','references':records,'linkedOrUnlistedMaterialsRead':False,'formalGradingExpectationsRead':False},f,ensure_ascii=False,indent=2);f.write('\n')
