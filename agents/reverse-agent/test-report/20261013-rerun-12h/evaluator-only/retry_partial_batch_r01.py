"""Prepare one closed max-jobs=2 phase of a twenty-job batch without rewriting answers."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import grader

GRADER_SHA256 = '83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7'
STARTED_JOB_LIMIT = 2
TOTAL_JOB_COUNT = 20
TERMINAL_STATUSES = {'PASSED', 'TIMEOUT', 'CLI_FAILED', 'VALIDATION_OR_PROVIDER_FAILED', 'DEADLINE_EXPIRED'}


def _safe(path, root):
    return grader.safe(Path(path), Path(root))


def _digest(path, root):
    return hashlib.sha256(_safe(path, root).read_bytes()).hexdigest()


def _load(path, root):
    return json.loads(_safe(path, root).read_text(encoding='utf-8-sig'))


def _save(path, root, value):
    path = _safe(path, root)
    _safe(path.parent, root).mkdir(parents=True, exist_ok=True)
    with _safe(path, root).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def _inventory(root):
    root = _safe(root, root)
    files, directories, pending = {}, [], [root]
    while pending:
        current = _safe(pending.pop(), root)
        directories.append(current.relative_to(root).as_posix())
        for raw in current.iterdir():
            path = _safe(raw, root)
            relative = path.relative_to(root).as_posix()
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                files[relative] = _digest(path, root)
            else:
                raise ValueError('Nonregular batch evidence is forbidden: ' + relative)
    return {'files': files, 'directories': sorted(directories)}


def _verify_grader():
    expected = _safe(grader.HERE / 'grader.py', grader.HERE)
    spec = getattr(grader, '__spec__', None)
    if (_safe(Path(grader.__file__), grader.HERE) != expected or spec is None or
            spec.origin is None or _safe(Path(spec.origin), grader.HERE) != expected or
            _digest(expected, grader.HERE) != GRADER_SHA256):
        raise ValueError('The original exact grader implementation is required')


def _controller(receipt_path, receipt_sha256, source, batch_sha256):
    receipt_path = _safe(receipt_path, grader.HERE / 'checkpoints')
    if not isinstance(receipt_sha256, str) or not re.fullmatch('[0-9a-f]{64}', receipt_sha256):
        raise ValueError('An explicit exact completion receipt SHA256 is required')
    if _digest(receipt_path, grader.HERE / 'checkpoints') != receipt_sha256:
        raise ValueError('Completion receipt bytes differ from the root pin')
    receipt = _load(receipt_path, grader.HERE / 'checkpoints')
    if (receipt.get('schema') != 'partial-controller-terminal-receipt/1' or
            receipt.get('controllerExited') is not True or
            type(receipt.get('controllerExitCode')) is not int or receipt['controllerExitCode'] != 1 or
            type(receipt.get('startedJobLimit')) is not int or receipt['startedJobLimit'] != STARTED_JOB_LIMIT or
            receipt.get('otherJobDirectoriesAbsent') is not True or
            type(receipt.get('unstartedJobs')) is not int or
            receipt['unstartedJobs'] != TOTAL_JOB_COUNT - STARTED_JOB_LIMIT or
            receipt.get('sourceBatchManifestSha256') != batch_sha256 or
            _safe(Path(receipt.get('sourceBatch', '')), grader.HERE / 'batches') != source or
            not isinstance(receipt.get('terminalJobs'), list) or
            len(receipt['terminalJobs']) != STARTED_JOB_LIMIT):
        raise ValueError('A matching closed partial controller receipt is required')
    if _digest(receipt_path, grader.HERE / 'checkpoints') != receipt_sha256:
        raise ValueError('Completion receipt changed while reading')
    return receipt


def _check_capsule(batch):
    # Call the unchanged grader only after every current descendant has passed
    # the same parent/link policy. Its own evidence/answer checks remain authoritative.
    _inventory(batch)
    seal, capsule = grader.check_capsule(batch)
    if seal != _load(batch / 'batch.json', batch) or _safe(capsule, batch) != _safe(batch / 'capsule', batch):
        raise ValueError('The grader returned a different batch or capsule')
    return seal, _safe(capsule, batch)


def copy_checked(source, destination, source_root, destination_root, expected_sha256):
    source = _safe(source, source_root)
    destination = _safe(destination, destination_root)
    if _digest(source, source_root) != expected_sha256:
        raise ValueError('Source evidence changed before byte copy')
    data = _safe(source, source_root).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('Source evidence changed during byte copy')
    _safe(destination.parent, destination_root).mkdir(parents=True, exist_ok=True)
    with _safe(destination, destination_root).open('xb') as stream:
        stream.write(data)
    if (_digest(source, source_root) != expected_sha256 or
            _digest(destination, destination_root) != expected_sha256):
        raise ValueError('Immutable retry byte copy drift')
    return expected_sha256


def prepare_partial_retry(source, destination, completion_receipt, completion_sha256):
    _verify_grader()
    source = _safe(source, grader.HERE / 'batches')
    destination = _safe(destination, grader.HERE / 'batches')
    completion_receipt = _safe(completion_receipt, grader.HERE / 'checkpoints')
    if (source == destination or source in destination.parents or destination in source.parents):
        raise ValueError('Source and fresh destination roots must be disjoint')
    if not source.is_dir() or destination.exists():
        raise ValueError('An existing source and completely fresh destination are required')
    original = _inventory(source)
    batch_sha256 = _digest(source / 'batch.json', source)
    receipt = _controller(completion_receipt, completion_sha256, source, batch_sha256)
    seal, capsule = _check_capsule(source)
    if seal.get('graderSha256') != GRADER_SHA256:
        raise ValueError('The batch is not bound to the original grader')
    jobs = seal.get('jobs')
    if not isinstance(jobs, list) or len(jobs) != TOTAL_JOB_COUNT:
        raise ValueError('This helper requires the exact twenty-job batch')
    identifiers, request_paths = [], []
    for job in jobs:
        identifier = job.get('shardId')
        relative = job.get('requestPath')
        if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,255}', identifier):
            raise ValueError('Job IDs must be unique plain path components')
        if (not isinstance(relative, str) or '\\' in relative or PurePosixPath(relative).is_absolute() or
                '..' in PurePosixPath(relative).parts or not relative):
            raise ValueError('Request paths must stay in the same sealed capsule')
        if not _safe(capsule / relative, capsule).is_file():
            raise ValueError('Every original request must exist')
        identifiers.append(identifier)
        request_paths.append(relative)
    if len(set(identifiers)) != TOTAL_JOB_COUNT or len(set(request_paths)) != TOTAL_JOB_COUNT:
        raise ValueError('Duplicate original job/request identity is forbidden')
    first = jobs[:STARTED_JOB_LIMIT]
    if [item.get('shardId') for item in receipt['terminalJobs']] != identifiers[:STARTED_JOB_LIMIT]:
        raise ValueError('The receipt must bind the exact first two original jobs in order')
    jobs_root = _safe(source / 'jobs', source)
    if not jobs_root.is_dir():
        raise ValueError('The closed phase must contain its two started job directories')
    for raw in jobs_root.iterdir():
        path = _safe(raw, source)
        if path.name not in identifiers[:STARTED_JOB_LIMIT] or not path.is_dir():
            raise ValueError('Only the exact first two closed job directories may exist')
    for identifier in identifiers[STARTED_JOB_LIMIT:]:
        if _safe(jobs_root / identifier, source).exists():
            raise ValueError('An unstarted job directory exists')
    reused, retried = [], []
    for job, terminal in zip(first, receipt['terminalJobs']):
        target = _safe(jobs_root / job['shardId'], source)
        result_path = _safe(target / 'result.json', source)
        if not target.is_dir() or not result_path.is_file():
            raise ValueError('Every started job requires a complete terminal result')
        digest = _digest(result_path, source)
        if digest != terminal.get('resultSha256'):
            raise ValueError('Terminal result differs from the closed root receipt')
        result = _load(result_path, source)
        status = result.get('status')
        if (status not in TERMINAL_STATUSES or status != terminal.get('status') or
                result.get('shardId') != job['shardId'] or result.get('documentId') != job['documentId']):
            raise ValueError('A matching terminal job result is required')
        record = {'shardId': job['shardId'], 'previousStatus': status, 'previousResultSha256': digest}
        if status == 'PASSED':
            answer = _safe(target / 'answer.txt', source)
            if _digest(answer, source) != result.get('answerSha256'):
                raise ValueError('Accepted answer drift before reuse')
            grader.validate_answer(_load(answer, source), _load(capsule / job['requestPath'], capsule), capsule)
            record['answerSha256'] = result['answerSha256']
            reused.append(record)
        else:
            record['rawCopiedToRetry'] = False
            retried.append(record)
    unstarted = [{'shardId': job['shardId'], 'previousStatus': 'UNSTARTED', 'rawCopiedToRetry': False}
                 for job in jobs[STARTED_JOB_LIMIT:]]
    if _inventory(source) != original:
        raise ValueError('Original files or directory membership changed during validation')
    _controller(completion_receipt, completion_sha256, source, batch_sha256)
    _verify_grader()
    copied = {}
    expected = {name: original['files'][name] for name in ('batch.json', 'answer-schema.json', 'canonical-pin.json')}
    for name, digest in original['files'].items():
        if name.startswith('capsule/') or any(name.startswith('jobs/' + job['shardId'] + '/') for job in reused):
            expected[name] = digest
    _safe(destination, grader.HERE / 'batches').mkdir(parents=True, exist_ok=False)
    for relative, digest in expected.items():
        copied[relative] = copy_checked(source / relative, destination / relative, source, destination, digest)
    receipt_copy = 'partial-controller-terminal-receipt.json'
    copied[receipt_copy] = copy_checked(completion_receipt, destination / receipt_copy,
                                      grader.HERE / 'checkpoints', destination, completion_sha256)
    for job in [*retried, *unstarted]:
        if _safe(destination / 'jobs' / job['shardId'], destination).exists():
            raise ValueError('Failed or unstarted raw was copied to the fresh destination')
    if _inventory(destination)['files'] != copied:
        raise ValueError('Fresh retry contains extra/missing files or altered bytes')
    _check_capsule(source)
    _check_capsule(destination)
    if _inventory(source) != original:
        raise ValueError('Original files or directory membership changed during copying')
    if _inventory(destination)['files'] != copied:
        raise ValueError('Fresh retry changed during final capsule validation')
    _controller(completion_receipt, completion_sha256, source, batch_sha256)
    _verify_grader()
    _save(destination / 'retry-provenance.json', destination, {
        'schema': 'independent-evaluation-immutable-partial-retry/1',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'sourceBatch': str(source),
        'sourceBatchManifestSha256': batch_sha256, 'completionReceipt': str(completion_receipt),
        'completionReceiptSha256': completion_sha256, 'controllerExited': True, 'controllerExitCode': 1,
        'startedJobLimit': STARTED_JOB_LIMIT, 'totalJobCount': TOTAL_JOB_COUNT,
        'allStartedJobsTerminal': True, 'reusedAcceptedJobs': reused, 'retryJobs': retried,
        'unstartedJobs': unstarted, 'copiedFileHashes': copied, 'originalInventory': original,
        'originalBeforeAfterUnchanged': True, 'originalBatchModified': False,
        'answerContentRewritten': False, 'rubricOrCanonicalChanged': False,
        'unstartedAnswersOrResultsFabricated': False, 'providerExecutedByPreparation': False,
        'qualityScore': None, 'formallyComplete': False})
    return {'reused': len(reused), 'retryJobs': len(retried), 'unstarted': len(unstarted),
            'completionReceiptSha256': completion_sha256, 'sourceBatchManifestSha256': batch_sha256}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--completion-receipt', type=Path, required=True)
    parser.add_argument('--completion-sha256', required=True)
    parser.add_argument('--deadline', required=True)
    args = parser.parse_args()
    run_manifest = _load(grader.HERE.parent / 'run-manifest.json', grader.HERE.parent)
    requested = datetime.fromisoformat(args.deadline.replace('Z', '+00:00'))
    authorized = datetime.fromisoformat(run_manifest['deadline'].replace('Z', '+00:00'))
    if grader.remaining(args.deadline) <= 0 or requested > authorized:
        raise ValueError('Partial retry must stay within the original user deadline')
    print(json.dumps(prepare_partial_retry(args.source, args.destination,
                                          args.completion_receipt, args.completion_sha256)))


if __name__ == '__main__':
    main()
