"""Split only rejected closed jobs into smaller requests; retain accepted raw bytes."""
from __future__ import annotations
import argparse, copy, os, re, shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import grader

TERMINAL={'PASSED','TIMEOUT','CLI_FAILED','VALIDATION_OR_PROVIDER_FAILED'}
ID=re.compile(r'^[A-Za-z0-9_-]+$')

def safe_path(path, root):
    checked=grader.safe(path,root)
    if path.is_symlink() or path.is_junction(): raise ValueError('Linked material refused before reading')
    return checked

def inventory(root):
    root=safe_path(root,grader.HERE/'batches')
    result={}
    for current,directories,names in os.walk(root,followlinks=False):
        current=Path(current)
        safe_path(current,root)
        for name in directories:
            safe_path(current/name,root)
        for name in names:
            path=safe_path(current/name,root)
            result[path.relative_to(root).as_posix()]=grader.digest(path)
    return result

def read(path,root):
    return grader.load(safe_path(path,root))

def copy_checked(path,target,source_root,target_root):
    path=safe_path(path,source_root)
    safe_path(target,target_root)
    digest=grader.digest(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,target)
    if grader.digest(path)!=digest or grader.digest(target)!=digest:
        raise ValueError('Byte copy drift')
    return digest

def prepare_split(source,destination,maximum_rows):
    if isinstance(maximum_rows,bool) or maximum_rows not in (10,20,40):
        raise ValueError('A reviewed smaller grouping limit is required')
    source=safe_path(source,grader.HERE/'batches')
    destination=safe_path(destination,grader.HERE/'batches')
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError('Fresh independent batch directory required')
    before=inventory(source)
    seal,capsule=grader.check_capsule(source)
    original_manifest=read(capsule/'manifest.json',source)
    jobs,states,original_ids=[],[],[]
    known=set()
    for job in seal['jobs']:
        identifier=job['shardId']
        if not isinstance(identifier,str) or not ID.fullmatch(identifier) or identifier in known:
            raise ValueError('Plain unique shard IDs required')
        known.add(identifier)
        if job['requestPath']!='requests/'+identifier+'.json':
            raise ValueError('Exact manifest request path required')
        request=read(capsule/job['requestPath'],source)
        row_ids=[row['evaluationId'] for row in request['rows']]
        if (request['shardId']!=identifier or request['documentId']!=job['documentId'] or
            row_ids!=job['evaluationIds'] or not row_ids or len(row_ids)!=len(set(row_ids)) or
            type(request['requireSafetyReview']) is not bool):
            raise ValueError('Sealed request identity or row set differs')
        original_ids.extend(row_ids)
        result_path=source/'jobs'/identifier/'result.json'
        if not result_path.is_file(): raise ValueError('All original jobs must be terminal')
        result=read(result_path,source)
        if (result.get('status') not in TERMINAL or result.get('shardId')!=identifier or
            result.get('documentId')!=job['documentId']):
            raise ValueError('A closed known job result is required')
        if result['status']=='PASSED':
            answer_path=safe_path(source/'jobs'/identifier/'answer.txt',source)
            if grader.digest(answer_path)!=result['answerSha256']:
                raise ValueError('Accepted raw answer drift')
            grader.validate_answer(read(answer_path,source),request,capsule)
            jobs.append(copy.deepcopy(job))
        else:
            for index,rows in enumerate(grader.grouped_shards(request['rows'],maximum_rows),1):
                part_id=identifier+'-P'+str(index).zfill(3)
                if part_id in known: raise ValueError('Split ID collides')
                known.add(part_id)
                part=copy.deepcopy(request)
                part.update(shardId=part_id,rows=copy.deepcopy(rows),
                            requireSafetyReview=request['requireSafetyReview'] and index==1)
                relative='requests/'+part_id+'.json'
                jobs.append({'shardId':part_id,'documentId':job['documentId'],'requestPath':relative,
                             'evaluationIds':[r['evaluationId'] for r in rows]})
                states.append({'request':part,'requestPath':relative,'parentShardId':identifier,
                               'parentResultSha256':grader.digest(result_path),'previousStatus':result['status']})
    if not states: raise ValueError('No failed job requires smaller requests')
    new_ids=[identifier for job in jobs for identifier in job['evaluationIds']]
    if len(original_ids)!=len(set(original_ids)) or Counter(new_ids)!=Counter(original_ids):
        raise ValueError('Every original evaluation row must occur exactly once')
    if inventory(source)!=before: raise ValueError('Source changed during preflight')
    destination.mkdir(parents=True)
    copied={}
    for name in ('answer-schema.json','canonical-pin.json'):
        copied[name]=copy_checked(source/name,destination/name,source,destination)
    for relative in sorted(before):
        if relative.startswith('capsule/'):
            copied[relative]=copy_checked(source/relative,destination/relative,source,destination)
    reused=[]
    for job in seal['jobs']:
        identifier=job['shardId']
        result=read(source/'jobs'/identifier/'result.json',source)
        if result['status']!='PASSED': continue
        prefix='jobs/'+identifier+'/'
        for relative in sorted(before):
            if relative.startswith(prefix):
                copied[relative]=copy_checked(source/relative,destination/relative,source,destination)
        reused.append({'shardId':identifier,'answerSha256':result['answerSha256']})
    manifest=copy.deepcopy(original_manifest)
    for item in states:
        path=destination/'capsule'/item['requestPath']
        if path.exists(): raise ValueError('Fresh split request path required')
        grader.save(path,item['request'])
        manifest['files'].append({'path':item['requestPath'],'sha256':grader.digest(path),'role':'rubric-shard'})
    grader.save(destination/'capsule/manifest.json',manifest)
    new_seal=copy.deepcopy(seal)
    new_seal.update(createdAt=datetime.now(timezone.utc).isoformat(),jobs=jobs,
                    capsuleManifestSha256=grader.digest(destination/'capsule/manifest.json'))
    grader.save(destination/'batch.json',new_seal)
    grader.check_capsule(destination)
    if inventory(source)!=before: raise ValueError('Original batch bytes changed')
    if any(grader.digest(destination/relative)!=digest for relative,digest in copied.items()
           if relative!='capsule/manifest.json'):
        raise ValueError('Copied material or accepted raw bytes changed')
    provenance={'schema':'independent-evaluation-smaller-immutable-retry/1',
        'sourceBatch':str(source),'sourceBatchManifestSha256':before['batch.json'],
        'originalInventory':before,'maximumRowsPerFailedRequest':maximum_rows,
        'reusedAcceptedJobs':reused,'splitFailedJobs':[{k:v for k,v in item.items() if k!='request'} for item in states],
        'newBatchManifestSha256':grader.digest(destination/'batch.json'),
        'rowSetPreservedExactlyOnce':True,'originalBatchModified':False,'answerContentRewritten':False,
        'rubricOrCanonicalChanged':False,'copiedFileHashes':copied,
        'capsuleChange':'Append smaller failed-job requests and update only the manifest; all original records and data remain unchanged.'}
    grader.save(destination/'split-retry-provenance.json',provenance)
    return {'reused':len(reused),'smallerRetryJobs':len(states),'rowsPreserved':len(original_ids)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--maximum-rows',type=int,choices=(10,20,40),required=True)
    parser.add_argument('--deadline',required=True)
    args=parser.parse_args()
    user_deadline=grader.load(grader.HERE.parent/'run-manifest.json')['deadline']
    if grader.remaining(args.deadline)<=0 or datetime.fromisoformat(args.deadline.replace('Z','+00:00')) > \
       datetime.fromisoformat(user_deadline.replace('Z','+00:00')):
        raise ValueError('Retry must remain inside the user deadline')
    import json
    print(json.dumps(prepare_split(args.source,args.destination,args.maximum_rows)))

if __name__=='__main__': main()
