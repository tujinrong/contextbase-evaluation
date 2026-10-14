"""Wait for the owned original batch, then retry only rejected jobs in a fresh capsule."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import subprocess
import sys
import time
import grader

deadline = '2026-10-13T20:15:58Z'
source = grader.HERE/'batches/source-m-class-r04-r6'
destination = grader.HERE/'batches/source-m-class-r04-r6-retry01'
seal, _ = grader.check_capsule(source)
if destination.exists():
    raise ValueError('Fresh retry required')
print(json.dumps({'status':'WAITING_FOR_ORIGINAL_JOBS','jobs':len(seal['jobs']),
    'source':str(source),'destination':str(destination)}),flush=True)
while grader.remaining(deadline) > 0:
    states = []
    for job in seal['jobs']:
        path = source/'jobs'/job['shardId']/'result.json'
        try:
            states.append(grader.load(path).get('status'))
        except (FileNotFoundError,json.JSONDecodeError):
            states.append(None)
    if all(status and status != 'RUNNING' for status in states):
        break
    time.sleep(min(15,max(0,grader.remaining(deadline))))
else:
    raise TimeoutError('Deadline expired while original jobs were running')

commands = [
    ['retry_batch.py','--source',str(source),'--destination',str(destination),'--deadline',deadline],
    ['grader.py','run','--batch',str(destination),'--deadline',deadline,'--workers','1'],
    ['normalize_defects.py','--batch',str(destination),'--deadline',deadline,'--output',str(destination/'defect-normalization.json')],
    ['grader.py','aggregate','--batch',str(destination),'--normalization',str(destination/'defect-normalization.json'),'--output',str(destination/'score.json')],
]
for script,*arguments in commands:
    if grader.remaining(deadline) <= 0:
        raise TimeoutError('Deadline expired before next retry phase')
    subprocess.run([sys.executable,'-X','utf8',str(grader.HERE/script),*arguments],cwd=grader.HERE,
        check=True,timeout=grader.remaining(deadline),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
