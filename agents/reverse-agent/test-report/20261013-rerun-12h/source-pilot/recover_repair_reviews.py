"""Watch successful existing AI drafts and run their fresh reviews; append event artifacts."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from contextbase.ai import capsule, validation

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, type=Path)
parser.add_argument('--progress', required=True, type=Path)
parser.add_argument('--deadline', required=True)
args = parser.parse_args()
config_bytes = args.config.read_bytes()
config = json.loads(config_bytes.decode('utf-8'))
report = Path(__file__).resolve().parent
snapshot = Path(config['snapshot'])
runtime_receipt = Path(config['runtimeReceipt'])
receipt_before = runtime_receipt.read_bytes()
freeze = json.loads(receipt_before)
runtime = Path(freeze['destination'])
def inventory():
    return {p.relative_to(runtime).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in runtime.rglob('*') if p.is_file() and '__pycache__' not in p.parts
            and p.suffix.lower() not in {'.pyc', '.pyo'}}
if inventory() != freeze['files'] or runtime not in Path(validation.__file__).resolve().parents:
    raise ValueError('recovery must retain the exact complete frozen runtime')
if capsule.verification_state(snapshot)['manifestSha256'] != config['snapshotManifestSha256']:
    raise ValueError('recovery requires the fixed source-only snapshot')
for entry in config['entries']:
    if Path(entry['reviewJob']).exists():
        raise FileExistsError('recovery review requires a fresh job')
args.progress.mkdir(parents=True, exist_ok=False)
capsule.write_json(args.progress / 'recovery-input.json', {
    'classification': 'EXCLUSIVE_PROGRESS_NOTIFICATION_FAILURE_RECOVERY',
    'oldQueueScriptSha256': hashlib.sha256((report / 'run_repair_queue.py').read_bytes()).hexdigest(),
    'configSha256': hashlib.sha256(config_bytes).hexdigest(),
    'reason': 'Original notification writes STARTED and DRAFT_SAVED to one exclusive path. Writer succeeds; post-writer notification raises before review.',
    'originalWriterOrDraftOrContextModified': False, 'duplicateWriterExecuted': False,
    'runtimeReceiptSha256': hashlib.sha256(receipt_before).hexdigest(), 'adopted': False,
})
def emit(entry, event, **fields):
    value = {'observedAt': datetime.now(timezone.utc).isoformat(), 'documentId': entry['documentId'],
             'event': event, 'job': entry['job'], 'output': entry['output'], **fields}
    name = hashlib.sha256(entry['documentId'].encode()).hexdigest()[:16] + '-' + event + '.json'
    capsule.write_json(args.progress / name, value)
    print(json.dumps(value, ensure_ascii=False), flush=True)

def review(entry, digest, document):
    name = Path(entry['job']).name
    command = [sys.executable, '-X', 'utf8', str(report / 'run_ai_stage.py'),
               '--receipt', str(report / f'{name}-review-recovery-run.json'),
               '--log', str(report / f'{name}-review-recovery-cli.log'), '--snapshot', str(snapshot), '--',
               'review', '--snapshot', str(snapshot), '--plan', config['plan'],
               '--document-id', entry['documentId'], '--job', entry['reviewJob'], '--document', str(document),
               '--timeout', '3000', '--deadline', args.deadline]
    completed = subprocess.run(command, stdin=subprocess.DEVNULL)
    if completed.returncode:
        emit(entry, 'FAILED_REVIEW', exitCode=completed.returncode)
        return
    handoff_file = Path(entry['reviewJob']) / 'review-handoff.json'
    handoff = json.loads(handoff_file.read_text(encoding='utf-8'))
    if handoff['documentSha256'] != digest or hashlib.sha256(document.read_bytes()).hexdigest() != digest:
        raise ValueError('recovery review does not bind the exact immutable AI draft')
    emit(entry, 'REVIEW_COMPLETED', documentFile=str(document), documentSha256=digest,
         reviewHandoffFile=str(handoff_file), approved=handoff['approved'], reviewScope=handoff['reviewScope'])

deadline = datetime.fromisoformat(args.deadline.replace('Z', '+00:00'))
pending = {entry['documentId']: entry for entry in config['entries']}
futures = []
with ThreadPoolExecutor(max_workers=2) as pool:
    while pending and datetime.now(timezone.utc) < deadline:
        for ident, entry in list(pending.items()):
            result_file = Path(entry['job']) / 'draft-result.json'
            if not result_file.exists():
                continue
            result = json.loads(result_file.read_text(encoding='utf-8'))
            document = Path(entry['output']) / entry['canonicalPath']
            digest = hashlib.sha256(document.read_bytes()).hexdigest()
            if digest != result['contentSha256'] or result['documentId'] != ident:
                raise ValueError('saved result differs from the existing AI manuscript')
            emit(entry, 'DRAFT_SAVED', documentFile=str(document), documentSha256=digest,
                 draftResultFile=str(result_file), analysisFacts=result['analysisFacts'],
                 structureFindings=result['structureFindings'],
                 currentStructureFindings=validation.validate_document(
                     document.read_text(encoding='utf-8'), entry['canonicalPath'], expected_document_id=ident))
            futures.append(pool.submit(review, entry, digest, document))
            del pending[ident]
        if pending:
            time.sleep(10)
    for future in futures:
        future.result()
if args.config.read_bytes() != config_bytes or runtime_receipt.read_bytes() != receipt_before or inventory() != freeze['files']:
    raise ValueError('recovery metadata or complete runtime drifted')
print(json.dumps({'event': 'RECOVERY_REVIEW_QUEUE_COMPLETED', 'unstartedDocuments': list(pending), 'adopted': False}), flush=True)
