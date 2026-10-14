"""Diagnose rejected quotations without modifying or accepting AI answers."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

report=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(report/'evaluator-only'))
import grader
assert grader.digest(report/'evaluator-only/grader.py')=='83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7'
batch=report/'evaluator-only/batches/assisted-search-basic-r04-r6'
cap=batch/'capsule'
manifest=grader.load(cap/'manifest.json')
registered={v['path'] for v in manifest['files']}
records=[]
for job in sorted((batch/'jobs').iterdir()):
    result_file=job/'result.json'
    if not result_file.is_file():
        continue
    result=grader.load(result_file)
    answer=job/'answer.txt'
    if result.get('error')!='Invalid generated evidence' or not answer.is_file():
        continue
    raw=grader.load(answer)
    invalid=[]
    for row in raw['rows']:
        evidence=row['generatedEvidence']
        if grader.evidence_valid(evidence,cap,'generated/',registered):
            continue
        reasons=[]
        for item in evidence:
            path=item['path']
            record={'path':path,'registered':path in registered,'correctPrefix':path.startswith('generated/')}
            if path in registered and path.startswith('generated/'):
                source=grader.safe(cap/path,cap/'generated')
                lines=source.read_text(encoding='utf-8-sig').splitlines()
                start,end=item['startLine'],item['endLine']
                bounded=1<=start<=end<=len(lines)
                record.update(startLine=start,endLine=end,totalLines=len(lines),rangeValid=bounded,
                    nonemptyQuote=bool(item['quote']),
                    exactQuotationInRange=bounded and bool(item['quote']) and item['quote'] in '\n'.join(lines[start-1:end]),
                    sourceSha256=grader.digest(source))
            reasons.append(record)
        invalid.append({'evaluationId':row['evaluationId'],'invalidEvidence':reasons})
    records.append({'shardId':job.name,'resultSha256':grader.digest(result_file),
        'rawAnswerSha256':grader.digest(answer),'invalidRows':invalid,'adopted':False})
out=report/'evaluator-only/rejected-evidence-diagnostic-r01.json'
if out.exists():
    raise ValueError('Fresh diagnostic required')
value={'schema':'rejected-grading-evidence-diagnostic/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'graderSha256':grader.digest(report/'evaluator-only/grader.py'),'records':records,
    'rawAnswersEdited':False,'rejectedAnswersAdopted':False,'expectationsChanged':False,'scoreAssigned':False}
out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'shards':len(records),'invalidRows':sum(len(r['invalidRows']) for r in records),
    'report':str(out),'records':records},ensure_ascii=False))
