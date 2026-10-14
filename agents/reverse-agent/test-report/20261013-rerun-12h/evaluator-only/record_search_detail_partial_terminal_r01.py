"""Record the root-observed terminal two-job phase; no evaluation answers are edited."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json
import grader

source=grader.safe(grader.HERE/'batches/assisted-search-detail-r02-r6',grader.HERE/'batches')
seal,capsule=grader.check_capsule(source)
started=2
if len(seal['jobs'])!=20: raise ValueError('The original twenty-job batch is required')
terminal=[]
for position,job in enumerate(seal['jobs']):
    target=grader.safe(source/'jobs'/job['shardId'],source)
    if position>=started:
        if target.exists(): raise ValueError('A supposedly unstarted job has artifacts')
        continue
    result=grader.load(grader.safe(target/'result.json',source))
    if result['status'] not in ('TIMEOUT','PASSED'): raise ValueError('The observed terminal phase differs')
    terminal.append({'shardId':job['shardId'],'status':result['status'],
        'resultSha256':grader.digest(target/'result.json')})
if [x['status'] for x in terminal]!=['TIMEOUT','PASSED']: raise ValueError('Expected terminal statuses differ')
destination=grader.safe(grader.HERE/'checkpoints/search-detail-first-phase-terminal-r01.json',grader.HERE)
if destination.exists(): raise FileExistsError('Fresh controller-completion receipt required')
record={'schema':'partial-controller-terminal-receipt/1','observedAt':datetime.now(timezone.utc).isoformat(),
    'sourceBatch':str(source),'sourceBatchManifestSha256':grader.digest(source/'batch.json'),
    'controllerExited':True,'observedRootSessionId':14055,'controllerExitCode':1,'startedJobLimit':started,
    'terminalJobs':terminal,'otherJobDirectoriesAbsent':True,'unstartedJobs':18,
    'sourceBatchChanged':False,'gradingAnswersChanged':False,'qualityScore':None,
    'observation':'Root unified-exec polling returned completed exit code 1 for the max-jobs=2 controller.'}
grader.save(destination,record)
print(json.dumps({'receipt':str(destination),'sha256':grader.digest(destination),'terminalJobs':2,'unstartedJobs':18}))
