"""Seal terminal metadata after root observed owned controller70151 exit1."""
from datetime import datetime, timezone
import grader
batch=grader.HERE/'batches/assisted-code-design-r04-r6-retry01'
seal,capsule=grader.check_capsule(batch)
terminal=[]
for job in seal['jobs']:
    path=batch/'jobs'/job['shardId']/'result.json'
    item=grader.load(path)
    if item.get('status') not in {'PASSED','TIMEOUT','CLI_FAILED','VALIDATION_OR_PROVIDER_FAILED'}:
        raise ValueError('All results must already be terminal')
    terminal.append({'shardId':job['shardId'],'status':item['status'],'sha256':grader.digest(path)})
if len(terminal)!=10 or sum(item['status']=='PASSED' for item in terminal)!=9:
    raise ValueError('Observed ten-job closure differs')
result={'schema':'root-owned-closed-grader-batch/1','observedAt':datetime.now(timezone.utc).isoformat(),
    'sourceBatch':str(batch),'sourceBatchManifestSha256':grader.digest(batch/'batch.json'),
    'controllerSessionId':70151,'controllerExited':True,'controllerExitCode':1,
    'closureEvidence':'Root write_stdin returned terminal exit_code1 for owned controller70151.',
    'terminalResults':terminal,'originalBatchModified':False}
target=grader.HERE/'checkpoints/code-design-retry01-closed-r01.json'
grader.save(target,result)
print(grader.digest(target))
