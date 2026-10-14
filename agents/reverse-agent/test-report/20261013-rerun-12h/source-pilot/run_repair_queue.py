"""Run authorized fresh AI document/review pairs from metadata-only queue entries."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading

from contextbase.ai import capsule, validation


parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, type=Path)
parser.add_argument('--progress', required=True, type=Path)
parser.add_argument('--workers', type=int, default=2)
parser.add_argument('--deadline', required=True)
args = parser.parse_args()
config_bytes = args.config.read_bytes()
config = json.loads(config_bytes.decode('utf-8'))
report = Path(__file__).resolve().parent
snapshot = Path(config['snapshot'])
plan = Path(config['plan'])
runtime_receipt = Path(config['runtimeReceipt'])
runtime = json.loads(runtime_receipt.read_text(encoding='utf-8'))
runtime_root = Path(runtime['destination'])
inventory = {p.relative_to(runtime_root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in runtime_root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.suffix.lower() not in {'.pyc', '.pyo'}}
if inventory != runtime['files'] or runtime_root not in Path(validation.__file__).resolve().parents:
    raise ValueError('queue must use its complete pinned frozen runtime')
manifest = capsule.verify(snapshot)
if capsule.verification_state(snapshot)['manifestSha256'] != config['snapshotManifestSha256'] or manifest['mode'] != 'source-only':
    raise ValueError('repair queue is restricted to the exact sealed source-only capsule')
planned = {d['id']: d for d in json.loads(plan.read_text(encoding='utf-8'))['documents']}
for entry in config['entries']:
    if planned[entry['documentId']]['path'] != entry['canonicalPath']:
        raise ValueError('repair entry must retain the existing canonical filename')
    if Path(entry['job']).exists() or Path(entry['output']).exists() or Path(entry['reviewJob']).exists():
        raise FileExistsError('repair entry requires fresh job and output roots')
args.progress.mkdir(parents=True, exist_ok=False)
lock = threading.Lock()


def emit(entry, event, **fields):
    value = {'observedAt': datetime.now(timezone.utc).isoformat(), 'documentId': entry['documentId'],
             'event': event, 'job': entry['job'], 'output': entry['output'], **fields}
    name = hashlib.sha256(entry['documentId'].encode()).hexdigest()[:16] + '.json'
    with lock:
        capsule.write_json(args.progress / name, value)
        print(json.dumps(value, ensure_ascii=False), flush=True)


def stage(entry, phase, cli):
    name = Path(entry['job']).name
    command = [sys.executable, '-X', 'utf8', str(report / 'run_ai_stage.py'),
               '--receipt', str(report / f'{name}-{phase}-run.json'),
               '--log', str(report / f'{name}-{phase}-cli.log'), '--snapshot', str(snapshot), '--', *cli]
    completed = subprocess.run(command, stdin=subprocess.DEVNULL)
    if completed.returncode:
        emit(entry, 'FAILED_STAGE', phase=phase, exitCode=completed.returncode)
        return False
    return True


def run(entry):
    emit(entry, 'STARTED', analysisCheckpointReused=entry['analysisJob'])
    base = ['--snapshot', str(snapshot), '--plan', str(plan), '--document-id', entry['documentId'],
            '--timeout', '3000', '--deadline', args.deadline]
    if not stage(entry, 'document', ['document', *base, '--job', entry['job'], '--output', entry['output'],
                                   '--analysis-job', entry['analysisJob'], '--revision-context', entry['revisionContext']]):
        return
    result_file = Path(entry['job']) / 'draft-result.json'
    result = json.loads(result_file.read_text(encoding='utf-8'))
    document = Path(entry['output']) / entry['canonicalPath']
    digest = hashlib.sha256(document.read_bytes()).hexdigest()
    if digest != result['contentSha256']:
        raise ValueError('AI manuscript differs from its saved draft result')
    emit(entry, 'DRAFT_SAVED', documentFile=str(document), documentSha256=digest,
         draftResultFile=str(result_file), structureFindings=result['structureFindings'],
         analysisFacts=result['analysisFacts'], analysisExecutedInThisJob=result['analysisExecutedInThisJob'])
    if not stage(entry, 'review', ['review', *base, '--job', entry['reviewJob'], '--document', str(document)]):
        return
    handoff_file = Path(entry['reviewJob']) / 'review-handoff.json'
    handoff = json.loads(handoff_file.read_text(encoding='utf-8'))
    if handoff['documentSha256'] != digest:
        raise ValueError('independent review did not bind the exact AI manuscript')
    emit(entry, 'REVIEW_COMPLETED', documentFile=str(document), documentSha256=digest,
         reviewHandoffFile=str(handoff_file), approved=handoff['approved'], reviewScope=handoff['reviewScope'])


with ThreadPoolExecutor(max_workers=args.workers) as pool:
    futures = [pool.submit(run, entry) for entry in config['entries']]
    for future in futures:
        future.result()
if args.config.read_bytes() != config_bytes:
    raise ValueError('repair queue metadata changed during execution')
print(json.dumps({'event': 'QUEUE_COMPLETED', 'entries': len(config['entries']), 'adopted': False,
                  'configSha256': hashlib.sha256(config_bytes).hexdigest()}, ensure_ascii=False), flush=True)
